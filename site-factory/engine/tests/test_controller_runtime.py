import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from controller_runtime import run_once
from controller_state import digest


class Pool:
    def __init__(self):
        self.row = {"record_id": "rec123", "priority": 14, "status": "ready",
                    "site_key": "example-flower-v2", "launch_key": "example-launch",
                    "region_key": "example-region"}

    def read(self):
        return [self.row]


class Store:
    def __init__(self):
        self.revision, self.state = 0, None

    def read(self, key):
        return self.revision, self.state

    def compare_and_swap(self, key, revision, state):
        if revision != self.revision:
            raise ValueError("state changed")
        self.revision += 1
        self.state = state
        return self.revision


class Roles:
    def __init__(self, reviewer="reviewer"):
        self.calls, self.reviewer = [], reviewer

    def prepare(self, region):
        return {"source_sha": "a" * 40,
                "publication_scope_key": "example-coverage",
                "members": [{"page_key": "p0"}]}

    def invoke(self, state):
        phase = state["phase"]
        self.calls.append(phase)
        receipt = {"release_key": state["release_key"],
                   "source_sha": state["source_sha"],
                   "membership_sha256": state["membership_sha256"]}
        if phase == "WRITING":
            receipt.update(writer_id="writer", draft_count=1)
        if phase == "REVIEWING":
            payload = {"page_key": "p0", "source_sha": state["source_sha"],
                       "membership_sha256": state["membership_sha256"],
                       "body": "real reviewed content", "revision": 1,
                       "writer_id": "writer"}
            review = {"result": "PASS", "payload_sha256": digest(payload),
                      "reviewer_id": self.reviewer,
                      "evidence_url": "https://example.test/review"}
            receipt.update(approved_count=1, independent_review=True,
                           reviewer_id=self.reviewer)
            return {"receipt": receipt, "payloads": {"p0": payload},
                    "reviews": {"p0": review}}
        if state.get("frozen_sha256"):
            receipt["frozen_sha256"] = state["frozen_sha256"]
        return {"receipt": receipt}


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.pool, self.store, self.roles = Pool(), Store(), Roles()

    def step(self):
        return run_once(self.pool, self.store, self.roles, "runner")

    def test_actual_stage_handoffs_and_resume(self):
        self.assertEqual(self.step()["status"], "initialized")
        for expected in ("BOOTSTRAP", "PLANNING", "WRITING", "REVIEWING", "FROZEN"):
            self.assertEqual(self.step()["to"], expected)
        self.assertEqual(self.roles.calls, ["BOOTSTRAP", "PLANNING", "WRITING", "REVIEWING"])
        self.assertEqual(self.store.state["writer_id"], "writer")
        self.assertEqual(self.store.state["reviewer_id"], "reviewer")
        self.assertEqual(len(self.store.state["frozen_sha256"]), 64)
        self.assertEqual(self.step()["to"], "SNAPSHOTTING")
        self.assertEqual(self.roles.calls[-1], "FROZEN")

    def test_writer_self_review_fails_closed(self):
        self.roles.reviewer = "writer"
        for _ in range(5):
            self.step()
        with self.assertRaisesRegex(ValueError, "writer cannot review"):
            self.step()
        self.assertEqual(self.store.state["phase"], "REVIEWING")

    def test_pool_identity_change_blocks_resume(self):
        self.step()
        self.pool.row["region_key"] = "other-region"
        with self.assertRaisesRegex(ValueError, "identity changed"):
            self.step()

    def test_launched_pool_row_resumes_existing_release(self):
        self.step()
        self.pool.row["status"] = "launched"
        self.assertEqual(self.step()["to"], "BOOTSTRAP")

    def test_missing_pool_contract_blocks_creation(self):
        self.pool.row["launch_key"] = ""
        with self.assertRaisesRegex(ValueError, "lacks site"):
            self.step()
        self.assertIsNone(self.store.state)


if __name__ == "__main__":
    unittest.main()
