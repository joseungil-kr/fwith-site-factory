"""Git-backed compare-and-swap checkpoints for the cloud controller.

Use a dedicated state branch. Non-fast-forward push is the lease CAS: two
controllers can both calculate a new state, but only one can publish it.
GITHUB_TOKEN's normal contents:write permission is sufficient for this store.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


STATE_BRANCH = "site-factory-controller-state"


def _git(cwd, *args):
    result = subprocess.run(["git", *args], cwd=cwd, text=True, encoding="utf-8", errors="replace",
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git operation failed")
    return result.stdout.strip()


def _path(release_key):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*:[a-z0-9][a-z0-9-]*", release_key):
        raise ValueError("unsafe release key")
    return "releases/" + release_key.replace(":", "--") + ".json"


class GitStateStore:
    def __init__(self, checkout: Path, branch=STATE_BRANCH):
        self.checkout = Path(checkout)
        self.branch = branch

    def read(self, release_key):
        path = _path(release_key)
        _git(self.checkout, "fetch", "origin", self.branch)
        revision = _git(self.checkout, "rev-parse", "FETCH_HEAD")
        # Only a successful tree read can establish absence. Authentication,
        # corrupt-object and transport failures must never restart a release.
        entry = _git(self.checkout, "ls-tree", "--name-only", revision, "--", path)
        if not entry:
            return revision, None
        raw = _git(self.checkout, "show", f"{revision}:{path}")
        return revision, json.loads(raw)

    def compare_and_swap(self, release_key, expected_revision, state):
        path = _path(release_key)
        if state.get("release_key") != release_key:
            raise ValueError("state release identity mismatch")
        if not re.fullmatch(r"[0-9a-f]{40}", expected_revision):
            raise ValueError("expected state revision must be pinned")
        # The checkout must be an isolated Actions workspace. A regular push
        # rejects a competing update; never force the state branch.
        _git(self.checkout, "fetch", "origin", self.branch)
        if _git(self.checkout, "rev-parse", "FETCH_HEAD") != expected_revision:
            raise ValueError("state changed; readback and resume")
        if _git(self.checkout, "status", "--porcelain"):
            raise ValueError("state checkout has unrelated changes")
        _git(self.checkout, "checkout", "--detach", expected_revision)
        target = self.checkout / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(state, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                          encoding="utf-8")
        _git(self.checkout, "add", "--", path)
        changed = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=self.checkout).returncode
        if changed == 0:
            return expected_revision
        if changed != 1:
            raise RuntimeError("cannot inspect staged state")
        _git(self.checkout, "-c", "user.name=github-actions[bot]", "-c",
             "user.email=41898282+github-actions[bot]@users.noreply.github.com",
             "commit", "-m", "Advance Site Factory controller checkpoint")
        revision = _git(self.checkout, "rev-parse", "HEAD")
        _git(self.checkout, "push", "origin", f"HEAD:refs/heads/{self.branch}")
        return revision
