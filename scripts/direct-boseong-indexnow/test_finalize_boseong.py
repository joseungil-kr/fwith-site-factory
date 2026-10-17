import hashlib
import importlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlsplit
from unittest.mock import patch

import finalize_boseong as control

ROOT = Path(__file__).resolve().parents[2]
RELEASE_ROOT = Path(os.environ.get("BOSEONG_RELEASE_ROOT", ROOT / "test-build" / "release"))
DIST = RELEASE_ROOT / "dist"
OWNER = control.OWNER
REPO = control.REPO
SOURCE = control.binding()["source"]["revision"]
URL_LIST = control.URL_LIST
CF_BEACON = (
    b'<script type="module" src="https://static.cloudflareinsights.com/beacon.min.js/vce701823e78c4301a35b7e07294d87301792088814092" '
    b'integrity="sha512-UKNk8GbxkABxKcXYuLkO16EleLGUkcvJWtpSNmExE0Too3ZaFAxTscNWEc1OdAv5/BikHawapSCaiD2XCmp+Bw==" '
    b'data-cf-beacon=\'{"version":"2024.11.0","token":"test-fixture","r":1,"spa":2}\' crossorigin="anonymous"></script>'
)


def make_event(env, title=None, actor=OWNER, body=None):
    b = control.binding()
    body = body or {
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
    return {
        "action": "opened",
        "repository": {"full_name": REPO},
        "issue": {
            "number": 700,
            "title": title or b["exactTitle"],
            "body": json.dumps(body),
            "state": "open",
            "user": {"login": actor},
        },
    }


def fake_env(event, gh_token=False):
    fd, name = tempfile.mkstemp(prefix="boseong-event-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(event, f)
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),
        "LANG": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "GITHUB_REPOSITORY": REPO,
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_ACTOR": OWNER,
        "GITHUB_TRIGGERING_ACTOR": OWNER,
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_EVENT_NAME": "issues",
        "GITHUB_JOB": "submit",
        "RUNNER_ENVIRONMENT": "github-hosted",
        "GITHUB_SHA": "a" * 40,
        "GITHUB_RUN_ID": "39099990001",
        "GITHUB_EVENT_PATH": name,
    }
    if gh_token:
        env["GH_TOKEN"] = "test-only-fake-token-never-used"
    return env, Path(name)


def response_for(dist, method, url, payload=None, post_status=200, post_counter=None):
    if method == "POST":
        if post_counter is not None:
            post_counter.append(payload)
        return post_status, "", {"content-type": "application/json"}
    path = urlsplit(url).path
    relative = "index.html" if path == "/" else path.lstrip("/")
    raw = (dist / relative).read_bytes()
    if method == "GET" and relative == "index.html":
        raw = raw.replace(b"</body>", CF_BEACON + b"</body>", 1)
    content_type = (
        "text/html; charset=utf-8" if relative == "index.html" else
        "text/plain; charset=utf-8" if relative == "robots.txt" or relative.endswith(".txt") else
        "application/xml; charset=utf-8" if relative.endswith(".xml") else
        "application/octet-stream"
    )
    return 200, raw.decode("utf-8"), {"content-type": content_type}


class MemoryJournal:
    records_store = []
    created_numbers = []

    def __init__(self, repository, number):
        self.repository = repository
        self.number = number
        MemoryJournal.created_numbers.append((repository, number))

    def records(self):
        return list(MemoryJournal.records_store)

    def write(self, record):
        MemoryJournal.records_store.append(dict(record))


class BoseongIndexNowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = control.load_engine()
        if not DIST.is_dir() or not (RELEASE_ROOT / "release.json").is_file():
            raise RuntimeError("validated release artifact must be supplied via BOSEONG_RELEASE_ROOT")

    def setUp(self):
        MemoryJournal.records_store = []
        MemoryJournal.created_numbers = []
        self.journal_target_patch = patch.object(control, "verify_receipt_journal_target", return_value=True)
        self.journal_target_patch.start()
        self.env, self.event_path = fake_env({})
        self.event = make_event(self.env)
        with self.event_path.open("w", encoding="utf-8") as f:
            json.dump(self.event, f)

    def tearDown(self):
        self.journal_target_patch.stop()
        self.event_path.unlink(missing_ok=True)

    def test_pins_existing_user_authorized_phase_and_accepted_build(self):
        b = control.binding()
        auth = control.read_json(ROOT / b["authorizationPath"])
        self.assertEqual(auth["authorizedAction"]["urlList"], URL_LIST)
        self.assertFalse(auth["authorizedAction"]["newKeyOrCredential"])
        self.assertFalse(auth["authorizedAction"]["deploymentOrProviderMutation"])
        self.assertEqual(b["receiptJournal"], {
            "repository": REPO, "issueNumber": 425,
            "expectedOwner": OWNER, "expectedTitle": "[BOSEONG-PRODUCTION-PUBLISH] 20261017",
        })
        self.assertEqual(b["build"]["artifactDigest"],
                         "sha256:af5732bdc751630c7f7546f597947e0e00ea7d599e830f61a63d59ad9361a1a8")
        self.assertEqual(control.validate_release(RELEASE_ROOT)[1]["revision"], SOURCE)
        old_publish = control.read_json(ROOT / "scripts/direct-boseong/production-publication.json")
        self.assertFalse(old_publish["indexNowSubmissionEnabled"])

    def test_fixed_receipt_journal_requires_readback_of_repo_owner_title_and_state(self):
        self.journal_target_patch.stop()
        target = control.binding()["receiptJournal"]
        valid = {
            "number": target["issueNumber"],
            "html_url": f"https://github.com/{REPO}/issues/{target['issueNumber']}",
            "title": target["expectedTitle"], "state": "open",
            "user": {"login": target["expectedOwner"]},
        }
        try:
            with patch.object(control, "read_receipt_journal_issue", return_value=valid) as read:
                self.assertTrue(control.verify_receipt_journal_target())
                read.assert_called_once_with(REPO, 425)
            for key, bad_value in (("title", "wrong"), ("state", "closed"), ("number", 426)):
                bad = dict(valid)
                bad[key] = bad_value
                with patch.object(control, "read_receipt_journal_issue", return_value=bad):
                    with self.assertRaises(control.Blocked):
                        control.verify_receipt_journal_target()
            bad_owner = dict(valid, user={"login": "not-the-owner"})
            with patch.object(control, "read_receipt_journal_issue", return_value=bad_owner):
                with self.assertRaises(control.Blocked):
                    control.verify_receipt_journal_target()
            bad_repo = dict(valid, html_url="https://github.com/other/repo/issues/425")
            with patch.object(control, "read_receipt_journal_issue", return_value=bad_repo):
                with self.assertRaises(control.Blocked):
                    control.verify_receipt_journal_target()
        finally:
            self.journal_target_patch.start()

    def test_get_only_preflight_checks_current_public_root_and_never_posts(self):
        original = self.engine.request
        observed = []
        raw_home_responses = []
        def fake(method, url, payload=None):
            observed.append((method, url))
            self.assertNotEqual(method, "POST")
            result = response_for(DIST, method, url, payload)
            if method == "GET" and url == control.ORIGIN + "/":
                raw_home_responses.append(result[1])
            return result
        with patch.object(self.engine, "request", side_effect=fake):
            result = control.preflight(RELEASE_ROOT, self.event, self.env)
        self.assertEqual(result["urls"], URL_LIST)
        self.assertEqual(result["state"], "public_get_preflight_verified")
        self.assertEqual(result["POSTCount"], 0)
        self.assertGreater(result["GETCount"], 0)
        evidence = result["liveHtmlEvidence"]
        self.assertEqual(evidence["rawBodySha256"], hashlib.sha256(
            (DIST / "index.html").read_bytes().replace(b"</body>", CF_BEACON + b"</body>", 1)).hexdigest())
        self.assertEqual(evidence["normalizedBodySha256"], control.binding()["publication"]["publicHtmlSha256"])
        self.assertEqual(evidence["normalizedCloudflareBeaconCount"], 1)
        expected_raw = (DIST / "index.html").read_text(encoding="utf-8").replace(
            "</body>", CF_BEACON.decode("utf-8") + "</body>", 1)
        self.assertEqual(raw_home_responses, [expected_raw])
        self.assertFalse(any(method == "POST" for method, _ in observed))

    def test_reviewed_beacon_normalizer_accepts_only_exact_single_beacon(self):
        normalize = control.load_cf_beacon_normalizer()
        body = (DIST / "index.html").read_bytes()
        expected = control.binding()["publication"]["publicHtmlSha256"]
        injected = body.replace(b"</body>", CF_BEACON + b"</body>", 1)
        self.assertEqual(normalize(injected, expected), body)
        variants = {
            "authored_change": injected.replace(b"<title>", b"<title>changed", 1),
            "duplicate_beacon": injected.replace(b"</body>", CF_BEACON + b"</body>", 1),
            "beacon_with_inline_content": injected.replace(b"</script>", b"alert(1)</script>", 1),
            "unrelated_extra_script": injected.replace(b"</body>", b"<script>extra()</script></body>", 1),
        }
        for label, variant in variants.items():
            with self.subTest(label=label), self.assertRaises(AssertionError):
                normalize(variant, expected)

    def test_changed_live_sitemap_is_blocked_before_any_post(self):
        posts = []
        def fake(method, url, payload=None):
            result = response_for(DIST, method, url, payload, post_counter=posts)
            if method == "GET" and url == control.ORIGIN + "/sitemap-0.xml":
                body = result[1].replace(
                    "</urlset>", "<url><loc>https://boseong.fwith.kr/not-reviewed/</loc></url></urlset>")
                return result[0], body, result[2]
            return result
        factory = lambda repo, issue: MemoryJournal(repo, issue)
        with patch.object(self.engine, "request", side_effect=fake):
            with self.assertRaises((control.Blocked, ValueError)):
                control.submit(RELEASE_ROOT, self.event, self.env, factory)
        self.assertEqual(posts, [])
        self.assertEqual(MemoryJournal.records_store, [])

    def test_transport_rejects_any_payload_beyond_exact_home_url(self):
        b = control.binding()
        key = (DIST / "31d1075dc9b5ec84419992fe7a70c660.txt").read_text().strip()
        site = {"siteKey": b["siteKey"], "siteUrl": control.ORIGIN,
                "productionEnabled": True, "launchMode": "live", "indexnowKey": key}
        transport = control.GuardedTransport(self.engine, site, key)
        bad = dict(host="boseong.fwith.kr", key=key, keyLocation=control.PROOF_URL,
                   urlList=[control.ORIGIN + "/", control.ORIGIN + "/not-reviewed/"])
        with self.assertRaises(control.Blocked):
            transport("POST", control.ENDPOINT, bad)
        self.assertEqual(transport.post_count, 0)

    def test_202_is_pending_not_retried_or_called_indexed(self):
        posts = []
        def fake(method, url, payload=None):
            return response_for(DIST, method, url, payload, 202, posts)
        factory = lambda repo, issue: MemoryJournal(repo, issue)
        with patch.object(self.engine, "request", side_effect=fake):
            result = control.submit(RELEASE_ROOT, self.event, self.env, factory)
        self.assertEqual(result["state"], "received_key_validation_pending")
        self.assertEqual(result["POSTCount"], 1)
        self.assertEqual(len(posts), 1)
        self.assertEqual(result["searchIndexing"], "not_verified")
        self.assertFalse(result["retryAllowed"])

    def test_valid_success_is_one_post_and_started_and_received_are_read_back(self):
        posts = []
        def fake(method, url, payload=None):
            return response_for(DIST, method, url, payload, 200, posts)
        factory = lambda repo, issue: MemoryJournal(repo, issue)
        with patch.object(self.engine, "request", side_effect=fake):
            result = control.submit(RELEASE_ROOT, self.event, self.env, factory)
        self.assertEqual(result["state"], "received")
        self.assertEqual(result["POSTCount"], 1)
        self.assertEqual(result["urls"], URL_LIST)
        self.assertTrue(result["journalReadbackVerified"])
        self.assertEqual([r["state"] for r in MemoryJournal.records_store], ["started", "received"])
        self.assertEqual(posts[0]["urlList"], URL_LIST)
        self.assertEqual(posts[0]["host"], "boseong.fwith.kr")
        self.assertEqual(posts[0]["keyLocation"], control.PROOF_URL)

    def test_explicit_429_is_not_retried_and_persisted_rejection_blocks_new_run(self):
        posts = []
        def fake(method, url, payload=None):
            status = 429 if method == "POST" else 200
            return response_for(DIST, method, url, payload, status, posts)
        factory = lambda repo, issue: MemoryJournal(repo, issue)
        with patch.object(self.engine, "request", side_effect=fake):
            result = control.submit(RELEASE_ROOT, self.event, self.env, factory)
            self.assertEqual(result["state"], "rejected")
            self.assertEqual(result["POSTCount"], 1)
            self.assertFalse(result["retryAllowed"])
            self.assertEqual([r["state"] for r in MemoryJournal.records_store], ["started", "rejected"])
            with self.assertRaises(control.Blocked):
                control.submit(RELEASE_ROOT, self.event, self.env, factory)
        self.assertEqual(len(posts), 1)

    def test_terminal_journal_readback_failure_after_post_keeps_count_one_and_blocks_replay(self):
        posts = []
        class FailTerminalReadbackJournal(MemoryJournal):
            def __init__(self, repository, number):
                super().__init__(repository, number)
                self.write_count = 0
            def write(self, record):
                super().write(record)
                self.write_count += 1
            def records(self):
                if self.write_count >= 2:
                    # Model a terminal comment whose write could not be confirmed.
                    MemoryJournal.records_store.pop()
                    raise OSError("simulated terminal journal readback failure")
                return super().records()
        factory = lambda repo, issue: FailTerminalReadbackJournal(repo, issue)
        def fake(method, url, payload=None):
            return response_for(DIST, method, url, payload, 200, posts)
        with patch.object(self.engine, "request", side_effect=fake):
            result = control.submit(RELEASE_ROOT, self.event, self.env, factory)
            self.assertEqual(result["state"], "blocked_or_outcome_uncertain")
            self.assertEqual(result["POSTCount"], 1)
            self.assertEqual(result["lastJournalState"], "started")
            self.assertFalse(result["retryAllowed"])
            second_event = json.loads(json.dumps(self.event))
            second_event["issue"]["number"] = 702
            with self.assertRaises(control.Blocked):
                control.submit(RELEASE_ROOT, second_event, self.env,
                               lambda repo, issue: MemoryJournal(repo, issue))
        self.assertEqual(len(posts), 1)
        self.assertEqual([r["state"] for r in MemoryJournal.records_store], ["started"])
        self.assertEqual(MemoryJournal.created_numbers, [(REPO, 425), (REPO, 425)])

    def test_late_exception_after_one_post_preserves_count_and_unknown_state(self):
        class FakeTransport:
            post_count = 1
            get_count = 6
        class FakeJournal:
            last_readback = {"state": "started"}
        def explode_after_post(*args):
            execution_state = args[-1]
            execution_state["transport"] = FakeTransport()
            execution_state["journal"] = FakeJournal()
            raise control.Blocked("final_receipt_readback_mismatch")
        with patch.object(control, "_submit_impl", side_effect=explode_after_post):
            result = control.submit(RELEASE_ROOT, self.event, self.env)
        self.assertEqual(result["state"], "blocked_or_outcome_uncertain")
        self.assertEqual(result["POSTCount"], 1)
        self.assertEqual(result["lastJournalState"], "started")
        self.assertFalse(result["retryAllowed"])

    def test_uncertain_post_is_durably_unknown_and_blocks_replay(self):
        post_calls = []
        def fake(method, url, payload=None):
            if method == "POST":
                post_calls.append(payload)
                raise TimeoutError("simulated transport uncertainty")
            return response_for(DIST, method, url, payload)
        factory = lambda repo, issue: MemoryJournal(repo, issue)
        with patch.object(self.engine, "request", side_effect=fake):
            result = control.submit(RELEASE_ROOT, self.event, self.env, factory)
            self.assertEqual(result["state"], "blocked_or_outcome_uncertain")
            self.assertEqual(result["POSTCount"], 1)
            self.assertEqual(result["lastJournalState"], "unknown")
            self.assertFalse(result["retryAllowed"])
            self.assertEqual([r["state"] for r in MemoryJournal.records_store], ["started", "unknown"])
            with self.assertRaises(control.Blocked):
                control.submit(RELEASE_ROOT, self.event, self.env, factory)
        self.assertEqual(len(post_calls), 1)

    def test_new_trigger_issue_reads_same_durable_journal_and_does_not_repost(self):
        posts = []
        def fake(method, url, payload=None):
            return response_for(DIST, method, url, payload, 200, posts)
        factory = lambda repo, issue: MemoryJournal(repo, issue)
        second_event = json.loads(json.dumps(self.event))
        second_event["issue"]["number"] = 701
        with patch.object(self.engine, "request", side_effect=fake):
            first = control.submit(RELEASE_ROOT, self.event, self.env, factory)
            second = control.submit(RELEASE_ROOT, second_event, self.env, factory)
        self.assertEqual(first["state"], "received")
        self.assertEqual(second["state"], "already_received")
        self.assertEqual(len(posts), 1)
        self.assertEqual(second["POSTCount"], 0)
        self.assertTrue(second["journalReadbackVerified"])
        self.assertEqual(MemoryJournal.created_numbers, [(REPO, 425), (REPO, 425)])

    def test_invalid_owner_or_changed_issue_binding_fails_before_network(self):
        bad = make_event(self.env, actor="other-user")
        with self.assertRaises(control.Blocked):
            control.validate_issue_event(bad, self.env)
        body = {
            "schemaVersion": 1, "action": "BOSEONG_INDEXNOW_ONE_SHOT",
            "expected_control_revision": self.env["GITHUB_SHA"],
            "source_revision": SOURCE, "publication_run_id": "39009688147",
            "build_run_id": "38994862258", "artifact_id": "12086568586",
            "authorization_sha256": control.binding()["authorizationSha256"],
            "maximum_post_requests": 2,
        }
        bad = make_event(self.env, body=body)
        with self.assertRaises(control.Blocked):
            control.validate_issue_event(bad, self.env)

    def test_workflow_is_serialized_issue_only_and_has_no_provider_secrets(self):
        workflow = (ROOT / ".github/workflows/boseong-indexnow-submit.yml").read_text()
        self.assertIn("types: [opened]", workflow)
        self.assertIn("boseong-direct-indexnow-submit", workflow)
        group = next(line.strip() for line in workflow.splitlines() if line.strip().startswith("group:"))
        self.assertNotIn("?", group)
        self.assertIn("&& 'boseong-direct-indexnow-submit' || format('irrelevant-{0}', github.run_id)", group)
        expression = group.split("${{", 1)[1].rsplit("}}", 1)[0]
        # Parse/evaluate the supported GitHub-expression subset in a Python AST
        # after mapping GitHub's logical tokens to their equivalent operators.
        expression = expression.replace("&&", " and ").replace("||", " or ").strip()
        def evaluate(run_id, *, eligible=True):
            from types import SimpleNamespace
            issue_title = "[BOSEONG-INDEXNOW-SUBMIT] 20261017" if eligible else "other-event"
            owner = OWNER if eligible else "another-user"
            github = SimpleNamespace(
                event_name="issues", repository=REPO, ref="refs/heads/main",
                actor=OWNER, triggering_actor=OWNER, run_id=str(run_id),
                event=SimpleNamespace(action="opened", issue=SimpleNamespace(
                    title=issue_title, user=SimpleNamespace(login=owner))),
            )
            return eval(expression, {"__builtins__": {}}, {
                "github": github,
                "format": lambda template, value: template.format(value),
            })
        self.assertEqual(evaluate("3901"), "boseong-direct-indexnow-submit")
        self.assertEqual(evaluate("3902"), "boseong-direct-indexnow-submit")
        self.assertEqual(evaluate("3901", eligible=False), "irrelevant-3901")
        self.assertNotEqual(evaluate("3901", eligible=False), evaluate("3902", eligible=False))
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertIn("run_attempt == 1", workflow)
        self.assertIn("actions: read", workflow)
        self.assertIn("issues: write", workflow)
        self.assertLess(workflow.index("actions/download-artifact@v4"),
                        workflow.index("Run bounded control tests against the verified retained artifact"))
        self.assertLess(workflow.index("Run bounded control tests against the verified retained artifact"),
                        workflow.index("GET-only live proof"))
        self.assertIn('BOSEONG_RELEASE_ROOT="$GITHUB_WORKSPACE/boseong-retained/release"', workflow)
        self.assertNotIn("CLOUDFLARE_API_TOKEN", workflow)
        self.assertNotIn("CLOUDFLARE_ACCOUNT_ID", workflow)
        self.assertNotIn("wrangler", workflow.lower())


if __name__ == "__main__":
    unittest.main()
