#!/usr/bin/env python3
"""Cloud-only publish rehearsal for the actual Decap-created draft.

Temporarily publishes the Korean short-text post INSIDE the GitHub Actions
runner, verifies Astro and content-derived QA, then restores the exact draft
bytes and rebuilds. Never commits/pushes simulated content or deploys it.
"""
from pathlib import Path
import re
import subprocess
import sys

repo = Path.cwd()
root = repo / "site-factory/astro-chat-lab"
post = root / "src/content/posts/제목테스트.md"

if not post.is_file():
    print("CMS_SHORT_POST_DRYRUN=SKIP (Decap test article not present)")
    raise SystemExit(0)

original = post.read_bytes()
text = original.decode("utf-8")
if not re.search(r"(?m)^draft:\s*true\s*$", text):
    print("CMS_SHORT_POST_DRYRUN=SKIP (test article is already published)")
    raise SystemExit(0)

updated, count = re.subn(r"(?m)^draft:\s*true\s*$", "draft: false", text, count=1)
assert count == 1, "Exactly one draft flag is required"
updated, count = re.subn(
    r"(?m)^pubDatetime:\s*[^\r\n]+$",
    "pubDatetime: 2024-01-01T00:00:00+09:00",
    updated,
    count=1,
)
assert count == 1, "A publication datetime must exist"
qa = ["python3", "site-factory/astro-chat-lab/qa.py", "build"]

try:
    post.write_text(updated, encoding="utf-8")
    subprocess.run(["pnpm", "run", "build"], cwd=root, check=True)
    subprocess.run(qa, cwd=repo, check=True)
    route = root / "dist/posts/제목테스트/index.html"
    assert route.is_file(), "Published Korean slug was not generated"
    rendered = route.read_text(encoding="utf-8")
    assert "제목테스트" in rendered and "본문테스트" in rendered, (
        "Short Decap article title/body absent from rendered HTML"
    )
    print("CMS_SHORT_POST_DRYRUN=PASS: Korean slug, title, and short body built")
finally:
    post.write_bytes(original)
    assert post.read_bytes() == original, "Source draft was not restored verbatim"
    # Deployment MUST use the original draft, never the simulated publication.
    subprocess.run(["pnpm", "run", "build"], cwd=root, check=True)
    subprocess.run(qa, cwd=repo, check=True)
    assert not (root / "dist/posts/제목테스트/index.html").exists(), (
        "Simulated draft incorrectly remained in production dist"
    )
    print("CMS_SHORT_POST_RESTORED=PASS: draft excluded from deployable dist")
