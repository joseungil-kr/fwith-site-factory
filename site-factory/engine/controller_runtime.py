#!/usr/bin/env python3
"""One durable Site Factory v2 controller step.

The configured role endpoints implement the recovered Creator/Reviewer contract.
They must accept an idempotency key and return immutable readback receipts. The
Publisher endpoint is the existing frozen Queue publisher bridge; later endpoints
read receipts from the existing snapshot/deployment/IndexNow workflows.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from controller_state import (PHASES, acquire_lease, digest, freeze_batch,
                              new_release, next_ready_region, release_key,
                              require_receipt, retry_delay)
from controller_store import GitStateStore


class HttpJson:
    def __init__(self, token, timeout=30):
        if not token:
            raise ValueError("controller HTTP token is required")
        self.token, self.timeout = token, timeout

    def request(self, method, url, body=None):
        if not url.startswith("https://"):
            raise ValueError("controller endpoints must use HTTPS")
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode()
        headers = {"Authorization": "Bearer " + self.token, "Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        for attempt in range(1, 6):
            try:
                with urllib.request.urlopen(
                    urllib.request.Request(url, data=data, headers=headers, method=method),
                    timeout=self.timeout,
                ) as response:
                    return json.load(response)
            except urllib.error.HTTPError as error:
                if error.code not in (429, 500, 502, 503, 504):
                    raise
                if attempt == 5:
                    raise
                time.sleep(retry_delay(attempt, error.code))
        raise RuntimeError("unreachable retry state")


class AirtableRegionPool:
    """Read the existing Region Launch Pool; this adapter never writes pool rows."""

    def __init__(self, http, base_id, table="Region Launch Pool"):
        if not base_id or not table:
            raise ValueError("Airtable base and pool table are required")
        self.http, self.base_id, self.table = http, base_id, table

    def read(self):
        url = "https://api.airtable.com/v0/" + urllib.parse.quote(self.base_id, safe="")
        url += "/" + urllib.parse.quote(self.table, safe="")
        rows, offset = [], None
        while True:
            query = {"pageSize": 100}
            if offset:
                query["offset"] = offset
            response = self.http.request("GET", url + "?" + urllib.parse.urlencode(query))
            for record in response["records"]:
                fields = record["fields"]
                rows.append({"record_id": record["id"], "priority": fields["priority"],
                             "status": fields["status"], "site_key": fields["site_key"],
                             "launch_key": fields["launch_key"],
                             "region_key": fields["region_key"]})
            offset = response.get("offset")
            if not offset:
                return rows


class RoleEndpoints:
    def __init__(self, http, urls, writer_id, reviewer_id):
        if not writer_id or not reviewer_id or writer_id == reviewer_id:
            raise ValueError("distinct writer_id and reviewer_id are required")
        self.http, self.urls = http, urls
        self.writer_id, self.reviewer_id = writer_id, reviewer_id

    def prepare(self, region):
        """Read-only bootstrap preflight; repeated calls return identical pins."""
        if "BOOTSTRAP" not in self.urls:
            raise ValueError("missing BOOTSTRAP endpoint")
        response = self.http.request(
            "POST", self.urls["BOOTSTRAP"],
            {"phase": "PREPARE", "region": region,
             "idempotency_key": digest({"pool_record_id": region["record_id"],
                                        "launch_key": region["launch_key"]})})
        if not isinstance(response, dict):
            raise ValueError("bootstrap preflight is not an object")
        return response

    def invoke(self, state):
        phase = state["phase"]
        if phase not in self.urls:
            raise ValueError("missing endpoint for " + phase)
        actor = self.writer_id if phase == "WRITING" else self.reviewer_id if phase == "REVIEWING" else "controller"
        key = digest({"release_key": state["release_key"], "phase": phase,
                      "source_sha": state["source_sha"],
                      "membership_sha256": state["membership_sha256"],
                      "frozen_sha256": state.get("frozen_sha256")})
        response = self.http.request("POST", self.urls[phase],
                                     {"idempotency_key": key, "actor_id": actor,
                                      "phase": phase, "state": state})
        if not isinstance(response, dict):
            raise ValueError("role response is not an object")
        receipt = response.get("receipt")
        if receipt and phase in ("WRITING", "REVIEWING"):
            field = "writer_id" if phase == "WRITING" else "reviewer_id"
            if receipt.get(field) != actor:
                raise ValueError("role response actor identity mismatch")
        return response


def _validate_pool_row(row):
    if not isinstance(row.get("priority"), int) or isinstance(row["priority"], bool):
        raise ValueError("pool priority must be an integer")
    if not row.get("site_key") or not row.get("launch_key") or not row.get("region_key"):
        raise ValueError("pool row lacks site, launch, or region identity")


def run_once(pool, store, roles, owner, now=None):
    """Advance exactly one transition; all external effects are replay safe."""
    now = now or datetime.now(timezone.utc)
    rows = pool.read()
    region = None
    existing = None
    # A bootstrap may change a Pool row from ready to launched. Resume that
    # release before selecting a later region.
    for row in sorted((row for row in rows if row["status"] == "launched"),
                      key=lambda row: row["priority"]):
        _validate_pool_row(row)
        candidate_key = release_key(row["site_key"], row["launch_key"])
        candidate = store.read(candidate_key)
        if candidate[1] is not None and candidate[1]["phase"] != "COMPLETE":
            region, existing = row, candidate
            break
    if region is None:
        region = next_ready_region(rows)
    if region is None:
        return {"status": "idle"}
    _validate_pool_row(region)
    key = release_key(region["site_key"], region["launch_key"])
    revision, state = existing if existing is not None else store.read(key)
    if state is None:
        prepared = roles.prepare(region)
        if (not isinstance(prepared.get("members"), list) or
                not isinstance(prepared.get("source_sha"), str) or
                len(prepared["source_sha"]) != 40 or
                not prepared.get("publication_scope_key")):
            raise ValueError("bootstrap preflight lacks pinned membership or source")
        state = new_release(region, region["launch_key"], prepared["source_sha"],
                            prepared["members"])
        state["publication_scope_key"] = prepared["publication_scope_key"]
        state["pool_record_id"] = region["record_id"]
        state["region_key"] = region["region_key"]
        store.compare_and_swap(key, revision, state)
        return {"status": "initialized", "release_key": key}
    if (state["pool_record_id"] != region["record_id"] or
            state["region_key"] != region["region_key"] or
            state["region_priority"] != region["priority"]):
        raise ValueError("pool identity changed after release initialization")
    if state["phase"] == "COMPLETE":
        return {"status": "complete", "release_key": key}
    phase = state["phase"]
    leased = acquire_lease(state, owner, now)
    revision = store.compare_and_swap(key, revision, leased)
    if phase == "READY_REGION":
        response = {"receipt": {"release_key": key, "source_sha": state["source_sha"],
                                "membership_sha256": state["membership_sha256"],
                                "pool_record_id": region["record_id"]}}
    else:
        response = roles.invoke(leased)
    receipt = response.get("receipt")
    if receipt is None:
        return {"status": "pending", "phase": phase, "release_key": key}
    if phase == "REVIEWING":
        if not receipt.get("reviewer_id") or receipt["reviewer_id"] == leased.get("writer_id"):
            raise ValueError("writer cannot review own work")
        frozen = freeze_batch({**leased, "reviewer_id": receipt["reviewer_id"]},
                              response["payloads"], response["reviews"])
        receipt = {**receipt, "frozen_sha256": frozen["frozen_sha256"]}
        candidate = require_receipt(frozen, phase, receipt)
    else:
        candidate = require_receipt(leased, phase, receipt)
    # The response is durable only after the exact receipt has passed the gate.
    store.compare_and_swap(key, revision, candidate)
    return {"status": "advanced", "from": phase, "to": candidate["phase"],
            "release_key": key}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-checkout", type=Path, required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--max-steps", type=int, default=16)
    args = parser.parse_args(argv)
    airtable = AirtableRegionPool(HttpJson(os.environ["AIRTABLE_TOKEN"]),
                                 os.environ["AIRTABLE_BASE_ID"])
    urls = json.loads(os.environ["SITE_FACTORY_STAGE_ENDPOINTS"])
    roles = RoleEndpoints(HttpJson(os.environ["SITE_FACTORY_RUNTIME_TOKEN"]), urls,
                          os.environ["SITE_FACTORY_WRITER_ID"],
                          os.environ["SITE_FACTORY_REVIEWER_ID"])
    if not 1 <= args.max_steps <= len(PHASES) + 1:
        raise ValueError("max-steps out of bounds")
    store = GitStateStore(args.state_checkout)
    for _ in range(args.max_steps):
        result = run_once(airtable, store, roles, args.owner)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        if result["status"] != "advanced" and result["status"] != "initialized":
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
