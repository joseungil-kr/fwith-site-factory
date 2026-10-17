"""One-shot, no-deploy Boseong IndexNow finalizer.

The shared engine is pinned by Git blob SHA. This control can submit only the
existing public Boseong proof and the single URL in the reviewed live sitemap.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from html.parser import HTMLParser
import re
import sys
import subprocess
from urllib.parse import urlsplit

CONTROL = Path(__file__).resolve().parent
REPO_ROOT = CONTROL.parents[1]
BINDING_PATH = CONTROL / "submission-binding.json"
OWNER = "joseungil-kr"
REPO = "joseungil-kr/fwith-site-factory"
ENDPOINT = "https://searchadvisor.naver.com/indexnow"
ORIGIN = "https://boseong.fwith.kr"
OWNER_ISSUE_TITLE = "[BOSEONG-INDEXNOW-SUBMIT] 20261017"
URL_LIST = ["https://boseong.fwith.kr/"]
PROOF_URL = "https://boseong.fwith.kr/31d1075dc9b5ec84419992fe7a70c660.txt"
ALLOWED_PUBLIC_URLS = frozenset({
    PROOF_URL,
    ORIGIN + "/",
    ORIGIN + "/robots.txt",
    ORIGIN + "/sitemap-index.xml",
    ORIGIN + "/sitemap-0.xml",
})
TRUSTED_ENV_KEYS = frozenset({
    "PATH", "HOME", "LANG", "PYTHONDONTWRITEBYTECODE",
    "GH_TOKEN", "GITHUB_REPOSITORY", "GITHUB_REF", "GITHUB_ACTOR",
    "GITHUB_TRIGGERING_ACTOR", "GITHUB_RUN_ATTEMPT", "GITHUB_EVENT_NAME",
    "GITHUB_JOB", "RUNNER_ENVIRONMENT", "GITHUB_SHA", "GITHUB_RUN_ID",
    "GITHUB_EVENT_PATH", "GITHUB_OUTPUT", "GITHUB_WORKSPACE",
    "BOSEONG_RELEASE_ROOT",
})
SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class Blocked(ValueError):
    pass


class Stop429Retry(Exception):
    """Stop the shared engine's optional 429 retry after its first POST."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise Blocked(code)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def binding():
    value = read_json(BINDING_PATH)
    require(value.get("repository") == REPO and value.get("origin") == ORIGIN,
            "fixed_boseong_binding_required")
    require(value.get("endpoint") == ENDPOINT and value.get("urlList") == URL_LIST,
            "fixed_one_url_target_required")
    require(value.get("limits") == {
        "maximumPOSTRequests": 1, "automaticRetry": False, "deploy": False,
        "cloudflareCredentials": False, "newIndexNowKey": False,
    }, "bounded_scope_changed")
    auth_path = REPO_ROOT / value["authorizationPath"]
    raw = auth_path.read_bytes()
    require(sha256(raw) == value.get("authorizationSha256"), "submission_authorization_digest_mismatch")
    auth = json.loads(raw)
    receipt_journal = {
        "repository": REPO, "issueNumber": 425,
        "expectedOwner": OWNER, "expectedTitle": "[BOSEONG-PRODUCTION-PUBLISH] 20261017",
    }
    require(value.get("receiptJournal") == receipt_journal, "fixed_receipt_journal_binding_required")
    require(value.get("cloudflareHtmlNormalizer") == {
        "path": "scripts/direct-boseong/publish.py",
        "gitBlobSha": "5536f327547d5e815da5788ba4958f91cf0a15ca",
    }, "reviewed_html_normalizer_pin_required")
    require(auth.get("recordType") == "boseong-indexnow-submission-phase-authorization"
            and auth.get("authorizedAction", {}).get("endpoint") == ENDPOINT
            and auth.get("authorizedAction", {}).get("origin") == ORIGIN
            and auth.get("authorizedAction", {}).get("urlList") == URL_LIST
            and auth.get("authorizedAction", {}).get("maximumPOSTRequests") == 1
            and auth.get("authorizedAction", {}).get("automaticRetry") is False
            and auth.get("authorizedAction", {}).get("existingPublicProofOnly") is True
            and auth.get("authorizedAction", {}).get("newKeyOrCredential") is False
            and auth.get("authorizedAction", {}).get("deploymentOrProviderMutation") is False
            and auth.get("authorizedAction", {}).get("durableJournal") == {
                "repository": REPO, "issueNumber": 425, "owner": OWNER,
                "title": "[BOSEONG-PRODUCTION-PUBLISH] 20261017",
            }, "submission_authorization_scope_mismatch")
    return value


def validate_issue_event(event: dict, env: dict):
    b = binding()
    issue = event.get("issue", {})
    require(env.get("GITHUB_REPOSITORY") == REPO
            and env.get("GITHUB_REF") == "refs/heads/main"
            and env.get("GITHUB_ACTOR") == OWNER
            and env.get("GITHUB_TRIGGERING_ACTOR") == OWNER
            and env.get("GITHUB_RUN_ATTEMPT") == "1"
            and env.get("GITHUB_EVENT_NAME") == "issues"
            and env.get("GITHUB_JOB") == "submit"
            and env.get("RUNNER_ENVIRONMENT") == "github-hosted"
            and SHA1.fullmatch(env.get("GITHUB_SHA", "")) is not None
            and re.fullmatch(r"[1-9][0-9]*", env.get("GITHUB_RUN_ID", "")) is not None,
            "exact_owner_main_first_hosted_run_required")
    require(set(env) <= TRUSTED_ENV_KEYS, "trusted_finalizer_environment_required")
    require(event.get("repository", {}).get("full_name") == REPO
            and event.get("action") == "opened"
            and issue.get("title") == b["exactTitle"]
            and issue.get("user", {}).get("login") == OWNER
            and issue.get("state") == "open"
            and not issue.get("pull_request")
            and type(issue.get("number")) is int and issue["number"] > 0,
            "exact_owner_submission_issue_required")
    try:
        body = json.loads(issue.get("body") or "")
    except Exception as exc:
        raise Blocked("submission_issue_body_invalid") from None
    expected = {
        "schemaVersion": 1,
        "action": "BOSEONG_INDEXNOW_ONE_SHOT",
        "expected_control_revision": env["GITHUB_SHA"],
        "source_revision": b["source"]["revision"],
        "publication_run_id": b["publication"]["runId"],
        "build_run_id": b["build"]["runId"],
        "artifact_id": b["build"]["artifactId"],
        "authorization_sha256": b["authorizationSha256"],
        "maximum_post_requests": 1,
    }
    require(type(body) is dict and set(body) == set(expected)
            and all(body.get(k) == v for k, v in expected.items()),
            "owner_issue_binding_mismatch")
    return issue, body


def load_cf_beacon_normalizer():
    """Compile only the exact reviewed helper AST; never import publisher control flow."""
    b = binding()
    path = REPO_ROOT / b["cloudflareHtmlNormalizer"]["path"]
    raw = path.read_bytes()
    require(git_blob_sha(raw) == b["cloudflareHtmlNormalizer"]["gitBlobSha"],
            "cloudflare_html_normalizer_changed")
    tree = ast.parse(raw.decode("utf-8"), filename=str(path))
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name == "strip_one_cf_beacon"]
    require(len(functions) == 1 and not functions[0].decorator_list,
            "single_reviewed_cf_beacon_helper_required")
    module = ast.Module(body=functions, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"HTMLParser": HTMLParser, "hashlib": hashlib, "re": re,
                 "urlsplit": urlsplit}
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["strip_one_cf_beacon"]


def read_receipt_journal_issue(repository: str, issue_number: int):
    result = subprocess.run(
        ["gh", "api", f"repos/{repository}/issues/{issue_number}"],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def verify_receipt_journal_target():
    target = binding()["receiptJournal"]
    issue = read_receipt_journal_issue(target["repository"], target["issueNumber"])
    expected_url = f"https://github.com/{target['repository']}/issues/{target['issueNumber']}"
    require(type(issue) is dict
            and issue.get("number") == target["issueNumber"]
            and issue.get("html_url") == expected_url
            and issue.get("title") == target["expectedTitle"]
            and issue.get("state") == "open"
            and issue.get("user", {}).get("login") == target["expectedOwner"],
            "fixed_receipt_journal_issue_mismatch")
    return True


def load_engine():
    b = binding()
    engine_path = REPO_ROOT / b["engine"]["path"]
    raw = engine_path.read_bytes()
    require(git_blob_sha(raw) == b["engine"]["gitBlobSha"], "shared_indexnow_engine_changed")
    sys.path.insert(0, str(engine_path.parent))
    import indexnow_finalize
    require(indexnow_finalize.ENDPOINT == ENDPOINT, "indexnow_endpoint_changed")
    return indexnow_finalize


def load_robots():
    path = REPO_ROOT / "scripts/direct-boseong/managed_robots.py"
    spec = importlib.util.spec_from_file_location("boseong_managed_robots", path)
    require(spec is not None and spec.loader is not None, "managed_robots_control_missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_release(release_root: Path):
    b = binding()
    require(release_root.is_dir() and not release_root.is_symlink(), "retained_release_missing")
    dist = release_root / "dist"
    require(dist.is_dir() and not dist.is_symlink(), "retained_dist_missing")
    require(not any(p.is_symlink() for p in release_root.rglob("*")), "symlinked_release_forbidden")
    meta_raw = (release_root / "release.json").read_bytes()
    require(sha256(meta_raw) == b["build"]["releaseManifestSha256"], "release_manifest_digest_mismatch")
    meta = json.loads(meta_raw)
    require(meta.get("repository") == REPO
            and meta.get("revision") == b["source"]["revision"]
            and meta.get("sourceBranch") == b["source"]["branch"]
            and meta.get("runId") == b["build"]["runId"]
            and meta.get("controlRevision") == b["build"]["controlRevision"]
            and meta.get("bindingSha256") == "f7c8fd6d4f94bdfe70aaf70822e871219166ed75230bff94eaf940110ec25f9d"
            and meta.get("sourceContractSha256") == b["source"]["contractSha256"]
            and meta.get("origin") == ORIGIN
            and meta.get("indexable") is True,
            "retained_release_identity_mismatch")
    files = meta.get("files")
    require(type(files) is dict, "release_file_manifest_invalid")
    for path, expected in b["releaseFiles"].items():
        raw = (dist / path).read_bytes()
        require(sha256(raw) == expected and files.get(path) == expected,
                "retained_release_file_digest_mismatch")
    proof_raw = (dist / "31d1075dc9b5ec84419992fe7a70c660.txt").read_bytes()
    require(sha256(proof_raw) == b["proof"]["sha256"], "existing_proof_digest_mismatch")
    key = proof_raw.decode("ascii").strip()
    require(re.fullmatch(r"[A-Za-z0-9-]{8,128}", key) is not None
            and (key + "\n").encode("ascii") == proof_raw,
            "existing_proof_format_mismatch")
    return dist, meta, key


class GuardedTransport:
    def __init__(self, engine, site, key):
        self.engine = engine
        self.site = site
        self.key = key
        self.get_count = 0
        self.post_count = 0
        self.observed = {}
        self.expected_payload = {
            "host": "boseong.fwith.kr",
            "key": key,
            "keyLocation": PROOF_URL,
            "urlList": URL_LIST,
        }
        self.cf_beacon_normalizer = load_cf_beacon_normalizer()
        self.home_evidence = None

    def __call__(self, method, url, payload=None):
        if method == "GET":
            require(payload is None and url in ALLOWED_PUBLIC_URLS, "public_get_outside_fixed_scope")
            self.get_count += 1
            require(self.get_count <= 40, "public_get_budget_exceeded")
            result = self.engine.request("GET", url)
            self.observed[url] = result
            if url == ORIGIN + "/":
                raw_html = result[1].encode("utf-8")
                expected = binding()["publication"]["publicHtmlSha256"]
                try:
                    normalized_html = self.cf_beacon_normalizer(raw_html, expected)
                except Exception:
                    raise Blocked("public_home_cf_beacon_not_exact_reviewed_transform") from None
                require(sha256(normalized_html) == expected, "public_home_not_exact_reviewed_output")
                self.home_evidence = {
                    "rawBodySha256": sha256(raw_html),
                    "normalizedBodySha256": sha256(normalized_html),
                    "normalizedCloudflareBeaconCount": int(raw_html != normalized_html),
                }
                require(self.home_evidence["normalizedCloudflareBeaconCount"] == 1,
                        "exactly_one_cf_beacon_normalization_required")
            return result
        if method == "POST":
            require(url == ENDPOINT and payload == self.expected_payload,
                    "indexnow_payload_outside_approved_scope")
            require(self.post_count == 0, "one_post_budget_exhausted")
            self.post_count += 1
            return self.engine.request("POST", url, payload)
        raise Blocked("unsupported_http_method")


class ReadbackJournal:
    """Shared journal adapter that confirms every write through a fresh GET."""
    def __init__(self, engine, issue_number: int, base_factory=None):
        self.engine = engine
        factory = base_factory or engine.Journal
        self.base = factory(REPO, issue_number)
        self.last_readback = None

    def records(self):
        return self.base.records()

    def write(self, record):
        self.base.write(record)
        rows = self.records()
        matches = [row for row in rows if row == record]
        require(len(matches) == 1, "journal_write_readback_mismatch")
        self.last_readback = dict(record)


def identity_fingerprint(engine, site, urls):
    origin = site["siteUrl"].rstrip("/")
    identity = {
        "siteKey": site["siteKey"], "origin": origin,
        "revision": binding()["source"]["revision"],
        "endpoint": ENDPOINT, "urlSetSha256": engine.digest(urls),
        "urlCount": len(urls),
    }
    return engine.digest({**identity, "keySha256": engine.digest(site["indexnowKey"])})


def verify_robot_composite(engine, release_root: Path, site, transport: GuardedTransport):
    urls = engine.verify_public(site, binding()["source"]["revision"], release_root,
                                lambda url: transport("GET", url))
    require(urls == URL_LIST, "live_sitemap_not_exact_single_root_url")
    robots = transport.observed.get(ORIGIN + "/robots.txt")
    require(robots is not None and robots[0] == 200, "public_robots_missing")
    source_sha = binding()["releaseFiles"]["robots.txt"]
    report = load_robots().verify(robots[1].encode("utf-8"), source_sha, ORIGIN, urls)
    load_robots().verify_headers(robots[2])
    return urls, report


def preflight(release_root: Path, event: dict, env: dict):
    b = binding()
    issue, _ = validate_issue_event(event, env)
    dist, meta, key = validate_release(release_root)
    engine = load_engine()
    site = {
        "siteKey": b["siteKey"], "siteUrl": ORIGIN,
        "productionEnabled": True, "launchMode": "live", "indexnowKey": key,
    }
    transport = GuardedTransport(engine, site, key)
    urls, robots_report = verify_robot_composite(engine, release_root, site, transport)
    return {
        "state": "public_get_preflight_verified",
        "sourceRevision": meta["revision"], "buildRunId": b["build"]["runId"],
        "buildArtifactId": b["build"]["artifactId"], "urls": urls,
        "proofSha256": b["proof"]["sha256"], "robotsVerification": robots_report,
        "GETCount": transport.get_count, "POSTCount": transport.post_count,
        "liveHtmlEvidence": getattr(transport, "home_evidence", None),
        "issue": issue["number"], "mutationsPerformed": False,
        "searchIndexing": "not_verified",
    }


def _submit_impl(release_root: Path, event: dict, env: dict, base_journal_factory=None, execution_state=None):
    b = binding()
    issue, _ = validate_issue_event(event, env)
    dist, meta, key = validate_release(release_root)
    verify_receipt_journal_target()
    engine = load_engine()
    site = {
        "siteKey": b["siteKey"], "siteUrl": ORIGIN,
        "productionEnabled": True, "launchMode": "live", "indexnowKey": key,
    }
    transport = GuardedTransport(engine, site, key)
    if execution_state is not None:
        execution_state["transport"] = transport
    urls, robots_report = verify_robot_composite(engine, release_root, site, transport)
    fingerprint = identity_fingerprint(engine, site, urls)
    journal = ReadbackJournal(engine, b["receiptJournal"]["issueNumber"], base_journal_factory)
    if execution_state is not None:
        execution_state["journal"] = journal
    previous = [row for row in journal.records() if row.get("fingerprint") == fingerprint]
    if previous:
        last = previous[-1]
        if last.get("state") in ("received", "received_key_validation_pending"):
            return {
                "state": "already_received", "receiptState": last["state"],
                "httpStatus": last.get("httpStatus"), "fingerprint": fingerprint,
                "sourceRevision": meta["revision"], "urls": urls,
                "POSTCount": 0, "GETCount": transport.get_count,
                "liveHtmlEvidence": getattr(transport, "home_evidence", None),
                "retryAllowed": False, "journalReadbackVerified": True,
                "searchIndexing": "not_verified",
            }
        raise Blocked("prior_same_fingerprint_blocks_replay")
    def no_retry_after_429(delay):
        raise Stop429Retry()
    run_url = "https://github.com/" + REPO + "/actions/runs/" + env["GITHUB_RUN_ID"]
    try:
        result = engine.finalize(
            site, b["source"]["revision"], release_root, journal,
            transport=transport, run_url=run_url, sleep=no_retry_after_429,
        )
    except Stop429Retry:
        last = journal.last_readback
        require(last and last.get("fingerprint") == fingerprint
                and last.get("state") == "rejected" and last.get("httpStatus") == 429,
                "429_receipt_readback_missing")
        return {
            "state": "rejected", "httpStatus": 429, "reason": "one_post_policy_no_retry",
            "fingerprint": fingerprint, "sourceRevision": meta["revision"], "urls": urls,
            "POSTCount": transport.post_count, "GETCount": transport.get_count,
            "liveHtmlEvidence": getattr(transport, "home_evidence", None),
            "retryAllowed": False, "journalReadbackVerified": True,
            "searchIndexing": "not_verified", "robotsVerification": robots_report,
        }
    except Exception as error:
        last = journal.last_readback
        readback = last is not None and last.get("fingerprint") == fingerprint
        reason = (str(error) if type(error) is ValueError and
                  re.fullmatch(r"[a-z0-9_]+", str(error)) else type(error).__name__)
        if last and last.get("state") == "rejected" and type(last.get("httpStatus")) is int:
            return {
                "state": "rejected", "httpStatus": last["httpStatus"], "reason": reason,
                "fingerprint": fingerprint, "sourceRevision": meta["revision"], "urls": urls,
                "POSTCount": transport.post_count, "GETCount": transport.get_count,
                "liveHtmlEvidence": getattr(transport, "home_evidence", None),
                "retryAllowed": False, "journalReadbackVerified": readback,
                "searchIndexing": "not_verified", "robotsVerification": robots_report,
            }
        return {
            "state": "blocked_or_outcome_uncertain", "reason": reason,
            "lastJournalState": last.get("state") if last else "not_readable_or_absent",
            "fingerprint": fingerprint, "sourceRevision": meta["revision"], "urls": urls,
            "POSTCount": transport.post_count, "GETCount": transport.get_count,
            "liveHtmlEvidence": getattr(transport, "home_evidence", None),
            "retryAllowed": False, "journalReadbackVerified": readback,
            "searchIndexing": "not_verified", "robotsVerification": robots_report,
        }
    require(transport.post_count == 1 and result.get("state") in
            ("received", "received_key_validation_pending"),
            "indexnow_receipt_not_accepted")
    last = journal.last_readback
    require(last and last.get("fingerprint") == fingerprint
            and last.get("state") == result.get("state")
            and last.get("httpStatus") == result.get("httpStatus"),
            "final_receipt_readback_mismatch")
    return {
        "state": result["state"], "httpStatus": result["httpStatus"],
        "fingerprint": fingerprint, "sourceRevision": meta["revision"], "urls": urls,
        "POSTCount": transport.post_count, "GETCount": transport.get_count,
        "liveHtmlEvidence": getattr(transport, "home_evidence", None),
        "retryAllowed": False, "searchIndexing": "not_verified",
        "journalReadbackVerified": True, "robotsVerification": robots_report,
        "runUrl": run_url,
    }


def submit(release_root: Path, event: dict, env: dict, base_journal_factory=None):
    """Preserve the true one-POST count if a late readback/report check fails."""
    execution_state = {}
    try:
        return _submit_impl(release_root, event, env, base_journal_factory, execution_state)
    except Exception as error:
        transport = execution_state.get("transport")
        count = transport.post_count if transport is not None else 0
        if count == 0:
            raise
        journal = execution_state.get("journal")
        try:
            last = journal.last_readback if journal is not None else None
        except Exception:
            last = None
        reason = (str(error) if type(error) is ValueError and
                  re.fullmatch(r"[a-z0-9_]+", str(error)) else type(error).__name__)
        return {
            "state": "blocked_or_outcome_uncertain", "reason": reason,
            "lastJournalState": last.get("state") if last else "not_readable_or_absent",
            "POSTCount": count, "GETCount": transport.get_count,
            "liveHtmlEvidence": getattr(transport, "home_evidence", None),
            "retryAllowed": False, "journalReadbackVerified": False,
            "searchIndexing": "not_verified",
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("authorize", "preflight", "submit"))
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        env = dict(os.environ)
        require(set(env) <= TRUSTED_ENV_KEYS, "trusted_finalizer_environment_required")
        if args.mode in ("authorize", "preflight"):
            require("GH_TOKEN" not in env, "preflight_must_be_credential_free")
        else:
            require(type(env.get("GH_TOKEN")) is str and len(env["GH_TOKEN"]) >= 20,
                    "github_journal_token_required")
        event_path = Path(env["GITHUB_EVENT_PATH"])
        event = read_json(event_path)
        issue, _ = validate_issue_event(event, env)
        release_root = Path(env.get("BOSEONG_RELEASE_ROOT", "boseong-retained/release"))
        if args.mode == "authorize":
            result = {
                "state": "owner_request_and_exact_control_authorized",
                "issue": issue["number"], "sourceRevision": binding()["source"]["revision"],
                "buildRunId": binding()["build"]["runId"],
                "buildArtifactId": binding()["build"]["artifactId"],
                "authorizationSha256": binding()["authorizationSha256"],
                "noPOST": True,
            }
            outputs = {
                "build_run_id": binding()["build"]["runId"],
                "artifact_id": binding()["build"]["artifactId"],
                "artifact_name": binding()["build"]["artifactName"],
                "artifact_digest": binding()["build"]["artifactDigest"],
            }
            if env.get("GITHUB_OUTPUT"):
                with open(env["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
                    for key, value in outputs.items():
                        f.write(key + "=" + str(value) + "\n")
        elif args.mode == "preflight":
            result = preflight(release_root, event, env)
        else:
            result = submit(release_root, event, env)
        ok = result.get("state") not in (
            "rejected", "blocked", "error", "blocked_or_outcome_uncertain")
    except Exception as error:
        safe = (str(error) if type(error) is Blocked and
                re.fullmatch(r"[a-z0-9_]+", str(error)) else type(error).__name__)
        result = {
            "state": "blocked_or_outcome_uncertain", "reason": safe,
            "POSTCount": 0, "retryAllowed": False,
            "searchIndexing": "not_verified",
        }
        ok = False
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("urls", "files")},
                     ensure_ascii=False, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
