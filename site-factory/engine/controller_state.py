"""Durable control-plane decisions for a whole-region Site Factory release.

The caller owns persistence and side effects.  This module deliberately never
publishes a snapshot or approves content: it only decides which already-proven
receipt allows the existing publisher/deployment workflows to run next.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone


PHASES = (
    "READY_REGION", "BOOTSTRAP", "PLANNING", "WRITING", "REVIEWING",
    "FROZEN", "SNAPSHOTTING", "BATCH_VERIFIED", "STAGING", "STAGING_QA",
    "PRODUCTION", "LIVE_QA", "INDEXNOW", "RECONCILED", "COMPLETE",
)
TERMINAL = {"BLOCKED_USER", "BLOCKED_TECHNICAL", "ROLLBACK_REQUIRED"}
TRANSIENT = {429, 500, 502, 503, 504}


def digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def next_ready_region(pool):
    """Choose after the highest launched priority, ignoring stale earlier rows."""
    launched = [row["priority"] for row in pool if row["status"] == "launched"]
    floor = max(launched, default=0)
    ready = sorted((row for row in pool if row["status"] == "ready" and
                    row["priority"] > floor), key=lambda row: row["priority"])
    return ready[0] if ready else None


def release_key(site_key, scope_key):
    if not site_key or not scope_key:
        raise ValueError("site and scope are required")
    return f"{site_key}:{scope_key}"


def acquire_lease(state, owner, now, ttl_seconds=900):
    """Return a new state only if no live owner exists; caller must CAS persist."""
    old = state.get("lease") or {}
    expires = old.get("expires_at")
    if expires and datetime.fromisoformat(expires) > now and old.get("owner") != owner:
        raise ValueError("release has a live controller lease")
    result = dict(state)
    result["lease"] = {"owner": owner, "expires_at": (now + timedelta(seconds=ttl_seconds)).isoformat()}
    return result


def retry_delay(attempt, status):
    if status not in TRANSIENT or attempt >= 5:
        raise ValueError("non-retryable or exhausted failure")
    return min(300, 2 ** attempt)


def require_receipt(state, phase, receipt):
    """Advance only when an exact, immutable receipt satisfies the phase gate."""
    receipts = dict(state.get("receipts", {}))
    if phase in receipts:
        if receipts[phase] != digest(receipt):
            raise ValueError("conflicting completion receipt")
        return dict(state)
    if state["phase"] != phase:
        raise ValueError("unexpected phase")
    if not isinstance(receipt, dict) or receipt.get("release_key") != state["release_key"]:
        raise ValueError("receipt release identity mismatch")
    if receipt.get("source_sha") != state["source_sha"]:
        raise ValueError("stale source SHA")
    if receipt.get("membership_sha256") != state["membership_sha256"]:
        raise ValueError("membership hash mismatch")
    if phase in ("REVIEWING", "FROZEN", "SNAPSHOTTING", "BATCH_VERIFIED", "STAGING",
                 "STAGING_QA", "PRODUCTION", "LIVE_QA", "INDEXNOW", "RECONCILED"):
        if receipt.get("frozen_sha256") != state.get("frozen_sha256") or not state.get("frozen_sha256"):
            raise ValueError("frozen hash mismatch")
    if phase == "REVIEWING" and (receipt.get("approved_count") != state["member_count"] or
                                  not receipt.get("independent_review")):
        raise ValueError("independent whole-region review incomplete")
    if phase == "WRITING" and (not receipt.get("writer_id") or
                                receipt.get("draft_count") != state["member_count"]):
        raise ValueError("whole-region writer handoff incomplete")
    if phase == "REVIEWING" and (not receipt.get("reviewer_id") or
                                  receipt.get("reviewer_id") == state.get("writer_id")):
        raise ValueError("writer cannot review own work")
    if phase == "SNAPSHOTTING" and (receipt.get("snapshot_count") != state["member_count"] or
                                    len(set(receipt.get("page_keys", []))) != state["member_count"]):
        raise ValueError("whole-region snapshot barrier incomplete")
    if phase == "STAGING_QA" and receipt.get("hosted_qa") != "passed":
        raise ValueError("staging QA failed")
    if phase == "LIVE_QA" and receipt.get("live_qa") != "passed":
        raise ValueError("live QA failed")
    if phase == "INDEXNOW" and receipt.get("indexnow_status") != 200:
        raise ValueError("IndexNow receipt missing")
    if phase in ("PRODUCTION", "LIVE_QA", "INDEXNOW") and not receipt.get("production_revision"):
        raise ValueError("production revision missing")
    result = dict(state)
    receipt_hash = digest(receipt)
    receipts[phase] = receipt_hash
    result["receipts"] = receipts
    if phase == "WRITING":
        result["writer_id"] = receipt["writer_id"]
    if phase == "REVIEWING":
        result["reviewer_id"] = receipt["reviewer_id"]
    result["phase"] = PHASES[PHASES.index(phase) + 1]
    return result


def snapshot_publish_key(state, page_key, revision):
    if page_key not in state["page_keys"] or not revision:
        raise ValueError("unregistered page or revision")
    return f"{state['site_key']}:{state['scope_key']}:{page_key}:r{revision}"


def freeze_batch(state, payloads, reviews):
    """Bind all reviewed frozen payloads before the existing Publisher sees one.

    A review must name the exact payload digest and a distinct reviewer.  The
    caller must persist the returned state with CAS before making a Queue row.
    """
    if state["phase"] != "REVIEWING":
        raise ValueError("batch is not in review")
    if set(payloads) != set(state["page_keys"]) or set(reviews) != set(state["page_keys"]):
        raise ValueError("whole-region payload/review membership incomplete")
    frozen = []
    for page_key in state["page_keys"]:
        payload, review = payloads[page_key], reviews[page_key]
        if (payload.get("page_key") != page_key or
                payload.get("source_sha") != state["source_sha"] or
                payload.get("membership_sha256") != state["membership_sha256"] or
                not payload.get("body") or not payload.get("revision") or
                not payload.get("writer_id") or payload.get("writer_id") != state.get("writer_id")):
            raise ValueError("frozen payload provenance mismatch")
        if (review.get("result") != "PASS" or
                review.get("payload_sha256") != digest(payload) or
                not review.get("reviewer_id") or
                review.get("reviewer_id") == payload.get("writer_id") or
                review.get("reviewer_id") != state.get("reviewer_id") or
                not review.get("evidence_url")):
            raise ValueError("independent exact-payload approval missing")
        frozen.append({"page_key": page_key, "payload_sha256": digest(payload),
                       "approval_sha256": digest(review)})
    result = dict(state)
    result["frozen_sha256"] = digest(frozen)
    return result


def pending_snapshots(state, published):
    """Next page only; a lost event is harmless after durable readback."""
    if state["phase"] != "SNAPSHOTTING":
        return []
    for page_key in state["page_keys"]:
        receipt = published.get(page_key)
        if not receipt:
            return [page_key]
        if receipt.get("frozen_sha256") != state["frozen_sha256"] or not receipt.get("commit_sha"):
            raise ValueError("published snapshot readback differs from frozen batch")
    return []


def new_release(region, scope_key, source_sha, members):
    keys = [row["page_key"] for row in members]
    if not keys or len(keys) != len(set(keys)):
        raise ValueError("whole-region membership must be nonempty and unique")
    site = region["site_key"]
    return {"schema": "site-factory-controller-v1", "release_key": release_key(site, scope_key),
            "site_key": site, "scope_key": scope_key, "region_priority": region["priority"],
            "phase": "READY_REGION", "source_sha": source_sha,
            "membership_sha256": digest(members), "member_count": len(members),
            "page_keys": keys, "receipts": {}, "lease": None}
