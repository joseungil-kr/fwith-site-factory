import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from controller_state import (acquire_lease, digest, freeze_batch, new_release, next_ready_region,
                              pending_snapshots, require_receipt, retry_delay,
                              snapshot_publish_key)


class ControllerStateTests(unittest.TestCase):
    def setUp(self):
        self.members = [{"page_key": f"p{i}"} for i in range(37)]
        self.state = new_release({"site_key": "example-flower-v2", "priority": 14},
                                 "example-dong-coverage-20261007", "a" * 40, self.members)
        self.state["frozen_sha256"] = "b" * 64

    def receipt(self, **extra):
        return {"release_key": self.state["release_key"], "source_sha": "a" * 40,
                "membership_sha256": self.state["membership_sha256"],
                "frozen_sha256": "b" * 64, **extra}

    def test_next_ready_skips_stale_prior_candidate(self):
        pool = [{"priority": 11, "status": "ready", "site_key": "old"},
                {"priority": 13, "status": "launched", "site_key": "done"},
                {"priority": 15, "status": "ready", "site_key": "later"},
                {"priority": 14, "status": "ready", "site_key": "next"}]
        self.assertEqual(next_ready_region(pool)["site_key"], "next")

    def test_duplicate_event_and_publish_key_are_stable(self):
        self.state["phase"] = "PLANNING"
        r = self.receipt()
        once = require_receipt(self.state, "PLANNING", r)
        self.assertEqual(require_receipt(once, "PLANNING", r), once)
        self.assertEqual(snapshot_publish_key(self.state, "p0", 1),
                         snapshot_publish_key(self.state, "p0", 1))
        with self.assertRaisesRegex(ValueError, "conflicting"):
            require_receipt(once, "PLANNING", self.receipt(other="changed"))

    def test_crash_resume_uses_readback(self):
        self.state["phase"] = "SNAPSHOTTING"
        receipts = {"p0": {"frozen_sha256": "b" * 64, "commit_sha": "c" * 40}}
        self.assertEqual(pending_snapshots(self.state, receipts), ["p1"])

    def test_stale_sha_and_frozen_mismatch_fail_closed(self):
        self.state["phase"] = "PRODUCTION"
        for r in (self.receipt(source_sha="c" * 40), self.receipt(frozen_sha256="c" * 64)):
            with self.assertRaises(ValueError):
                require_receipt(self.state, "PRODUCTION", r)

    def test_snapshot_failure_retry_is_bounded(self):
        self.assertEqual(retry_delay(1, 500), 2)
        self.assertEqual(retry_delay(4, 503), 16)
        with self.assertRaises(ValueError):
            retry_delay(5, 503)

    def test_lost_completion_event_reconciles_from_receipt(self):
        self.state["phase"] = "SNAPSHOTTING"
        receipts = {p: {"frozen_sha256": "b" * 64, "commit_sha": "c" * 40}
                    for p in self.state["page_keys"]}
        self.assertEqual(pending_snapshots(self.state, receipts), [])
        advanced = require_receipt(self.state, "SNAPSHOTTING",
                                   self.receipt(snapshot_count=37, page_keys=self.state["page_keys"]))
        self.assertEqual(advanced["phase"], "BATCH_VERIFIED")

    def test_http_429_and_5xx_backoff(self):
        self.assertEqual(retry_delay(2, 429), 4)
        with self.assertRaises(ValueError):
            retry_delay(2, 400)

    def test_36_of_37_never_crosses_barrier(self):
        self.state["phase"] = "SNAPSHOTTING"
        with self.assertRaisesRegex(ValueError, "barrier"):
            require_receipt(self.state, "SNAPSHOTTING",
                            self.receipt(snapshot_count=36, page_keys=self.state["page_keys"][:-1]))

    def test_staging_qa_failure_blocks_production(self):
        self.state["phase"] = "STAGING_QA"
        with self.assertRaisesRegex(ValueError, "staging QA"):
            require_receipt(self.state, "STAGING_QA", self.receipt(hosted_qa="failed"))

    def test_indexnow_failure_retries_without_production_rollback(self):
        self.state["phase"] = "INDEXNOW"
        self.state["receipts"]["PRODUCTION"] = digest({"production_revision": "d" * 40})
        with self.assertRaisesRegex(ValueError, "IndexNow"):
            require_receipt(self.state, "INDEXNOW",
                            self.receipt(indexnow_status=503, production_revision="d" * 40))
        self.assertEqual(self.state["phase"], "INDEXNOW")
        self.assertIn("PRODUCTION", self.state["receipts"])

    def test_indexnow_receipt_advances_once(self):
        self.state["phase"] = "INDEXNOW"
        r = self.receipt(indexnow_status=200, production_revision="d" * 40)
        once = require_receipt(self.state, "INDEXNOW", r)
        self.assertEqual(once["phase"], "RECONCILED")
        self.assertEqual(require_receipt(once, "INDEXNOW", r), once)

    def test_live_lease_rejects_other_owner_and_ttl_allows_handoff(self):
        now = datetime.now(timezone.utc)
        held = acquire_lease(self.state, "controller-1", now, 30)
        with self.assertRaisesRegex(ValueError, "live controller"):
            acquire_lease(held, "controller-2", now + timedelta(seconds=10), 30)
        handed = acquire_lease(held, "controller-2", now + timedelta(seconds=31), 30)
        self.assertEqual(handed["lease"]["owner"], "controller-2")

    def test_membership_identity_cannot_duplicate(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            new_release({"site_key": "example", "priority": 1}, "scope", "a" * 40,
                        [{"page_key": "same"}, {"page_key": "same"}])

    def test_freeze_requires_exact_member_payload_and_independent_review(self):
        self.state["phase"] = "REVIEWING"
        self.state["writer_id"] = "writer"
        self.state["reviewer_id"] = "independent-reviewer"
        payloads = {key: {"page_key": key, "source_sha": "a" * 40,
                          "membership_sha256": self.state["membership_sha256"],
                          "body": "reviewed text", "revision": 1, "writer_id": "writer"}
                    for key in self.state["page_keys"]}
        reviews = {key: {"result": "PASS", "payload_sha256": digest(payload),
                         "reviewer_id": "independent-reviewer", "evidence_url": "https://example.test/review"}
                   for key, payload in payloads.items()}
        self.assertEqual(len(freeze_batch(self.state, payloads, reviews)["frozen_sha256"]), 64)
        del reviews["p36"]
        with self.assertRaisesRegex(ValueError, "membership"):
            freeze_batch(self.state, payloads, reviews)


if __name__ == "__main__":
    unittest.main()
