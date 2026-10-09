#!/usr/bin/env python3
"""Static and real-HTTP QA for the dedicated Astro chat experiment."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
import os
import sys
import time

MODE = sys.argv[1]
ROOT = Path("site-factory/astro-chat-lab")
DIST = ROOT / "dist"
ORIGIN = os.environ.get("ASTRO_CHAT_ORIGIN", "").rstrip("/")
POST = "/posts/webchat-astro-first-post/"
TITLE = "웹채팅으로 만든 Astro 블로그 첫 게시물"
assert ORIGIN.startswith("https://astro-chat-lab-qa.") and ORIGIN.endswith(".workers.dev")

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canon = []
        self.robots = []
        self.h1 = []
        self.h2_count = 0
        self.links = []
        self.local_assets = []
        self._in_h1 = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "link" and a.get("rel") == "canonical":
            self.canon.append(a.get("href",""))
        if tag == "meta" and a.get("name", "").lower() == "robots":
            self.robots.append(a.get("content", ""))
        if tag == "h1": self._in_h1 = True
        if tag == "h2": self.h2_count += 1
        if tag == "a" and a.get("href"): self.links.append(a["href"])
        if tag in ("script", "link"):
            uri = a.get("src") if tag == "script" else a.get("href")
            if uri and urlsplit(uri).path.startswith("/_astro/"):
                self.local_assets.append(urlsplit(uri).path)
    def handle_endtag(self, tag):
        if tag == "h1": self._in_h1 = False
    def handle_data(self, data):
        if self._in_h1: self.h1.append(data)

def parse(html, expected_path):
    p = Page()
    p.feed(html)
    assert len(p.canon) == 1, "canonical count mismatch"
    assert p.canon[0].rstrip("/") == (ORIGIN+expected_path).rstrip("/"), "canonical origin/path mismatch: " + repr(p.canon)
    assert len(p.robots) == 1 and {"noindex","nofollow"}.issubset(
        {d.strip().lower() for d in p.robots[0].split(",")}
    ), "noindex meta missing"
    assert len(p.h1) > 0 and "".join(p.h1).strip(), "h1 missing"
    assert len(p.local_assets) > 0, "no local stylesheet or JS assets in page"
    return p

def check_content(home, detail):
    assert TITLE in home, "homepage does not contain the test post"
    assert TITLE in detail, "post title missing"
    for word in ("이번 실험에서 확인하는 것", "정적 블로그란?", "앞으로 글을 추가하는 방식"):
        assert word in detail, "post content missing: " + word
    hi = parse(home, "/")
    di = parse(detail, POST)
    assert len(di.h1) == 1, "post detail must have exactly one H1"
    assert di.h2_count >= 3, "post subheadings missing"
    assert any(urlsplit(link).path.rstrip("/") == POST.rstrip("/") for link in hi.links), "homepage post link missing"
    return sorted(set(hi.local_assets + di.local_assets))

if MODE == "build":
    source_posts = list((ROOT/"src/content/posts").rglob("*.md")) + list((ROOT/"src/content/posts").rglob("*.mdx"))
    assert len(source_posts) == 1 and source_posts[0].name == "webchat-astro-first-post.md"
    assert (DIST/"index.html").is_file() and (DIST/"404.html").is_file()
    assert (DIST/"posts/webchat-astro-first-post/index.html").is_file()
    home = (DIST/"index.html").read_text(encoding="utf-8")
    detail = (DIST/"posts/webchat-astro-first-post/index.html").read_text(encoding="utf-8")
    assets = check_content(home, detail)
    for asset in assets:
        assert (DIST/asset.lstrip("/")).is_file(), "local asset is missing: " + asset
    robots = (DIST/"robots.txt").read_text(encoding="utf-8")
    assert "Disallow: /" in robots and "Allow: /" not in robots, "robots.txt not closed"
    print(json.dumps({"phase":"build","result":"PASS","sourcePosts":1,"h1":1,"assets":assets,"post":POST},ensure_ascii=False))
elif MODE == "live":
    def read(path):
        req = Request(ORIGIN+path,headers={"User-Agent":"AstroChatLab-QA/1.0"})
        try:
            with urlopen(req, timeout=20) as response:
                return response.status, response.read().decode("utf-8",errors="replace")
        except HTTPError as error:
            return error.code, error.read().decode("utf-8", errors="replace")

    last = None
    for attempt in range(1, 11):
        try:
            home_status, home = read("/")
            post_status, detail = read(POST)
            missing_status, missing = read("/missing-astro-chat-lab-check-20261009/")
            if (home_status, post_status, missing_status) != (200,200,404):
                raise AssertionError("HTTP statuses: "+repr((home_status,post_status,missing_status)))
            assets = check_content(home, detail)
            asset_codes={}
            for asset in assets:
                code, _ = read(asset)
                assert code == 200, "asset missing "+asset+": "+str(code)
                asset_codes[asset] = code
            robots_status, robots = read("/robots.txt")
            assert robots_status == 200 and "Disallow: /" in robots
            print(json.dumps({"phase":"public-http","result":"PASS","origin":ORIGIN,
                "homepage":{"url":ORIGIN+"/","status":home_status},
                "post":{"url":ORIGIN+POST,"status":post_status},
                "missing":{"status":missing_status},
                "robots":{"status":robots_status,"disallow":True},
                "assets":asset_codes,"title":TITLE,"h1":1,"noindex":True},ensure_ascii=False))
            break
        except (AssertionError,URLError,TimeoutError) as e:
            last = str(e)
            if attempt == 10:
                raise SystemExit("Public QA failed after retries: "+last)
            time.sleep(8)
else:
    raise SystemExit("Usage: qa.py build|live")
