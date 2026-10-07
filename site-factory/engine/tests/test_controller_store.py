import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from controller_store import GitStateStore


def git(cwd, *args):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True, encoding="utf-8",
                                   errors="replace", stderr=subprocess.DEVNULL).strip()


class GitStoreTests(unittest.TestCase):
    def test_two_controllers_cannot_commit_same_checkpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bare, first, second = root / "remote.git", root / "first", root / "second"
            git(root, "init", "--bare", str(bare))
            git(root, "clone", str(bare), str(first))
            git(first, "checkout", "-b", "site-factory-controller-state")
            (first / "README").write_text("state branch\n", encoding="utf-8")
            git(first, "add", "README")
            git(first, "-c", "user.name=test", "-c", "user.email=test@example.test",
                "commit", "-m", "Create state branch")
            git(first, "push", "origin", "site-factory-controller-state")
            git(root, "clone", str(bare), str(second))
            key = "example-flower-v2:example-dong-coverage-20261007"
            a, b = GitStateStore(first), GitStateStore(second)
            rev_a, state_a = a.read(key)
            rev_b, state_b = b.read(key)
            self.assertEqual(rev_a, rev_b)
            self.assertIsNone(state_a)
            self.assertIsNone(state_b)
            result = {"release_key": key, "phase": "READY_REGION"}
            committed = a.compare_and_swap(key, rev_a, result)
            self.assertEqual(b.read(key), (committed, result))
            with self.assertRaisesRegex(ValueError, "state changed"):
                b.compare_and_swap(key, rev_b, {**result, "phase": "BOOTSTRAP"})


if __name__ == "__main__":
    unittest.main()
