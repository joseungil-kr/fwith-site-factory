#!/usr/bin/env python3
"""Small static contract for the isolated noindex AstroPaper preview."""
from pathlib import Path
import os


root = Path("dist")
revision = os.environ.get("SITE_FACTORY_REVISION", "")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read(path: str) -> str:
    file = root / path
    require(file.is_file(), f"missing artifact: {path}")
    return file.read_text(encoding="utf-8")


home = read("index.html")
detail = read("posts/blog-preparation/index.html")
robots = read("robots.txt")
headers = read("_headers")
read("rss.xml")
read("sitemap-index.xml")
read("tags/index.html")
read("tags/지역/index.html")
read("tags/근조/index.html")
read("tags/축하/index.html")

require("꽃이랑" in home and "https://fwith.co.kr" in home, "brand_cta_missing")
require("꽃이랑 블로그 준비 안내" in detail, "detail_route_missing")
require('name="robots" content="noindex,nofollow"' in home, "noindex_meta_missing")
require("X-Robots-Tag: noindex, nofollow" in headers, "noindex_header_missing")
require("User-agent: *" in robots and "Disallow: /" in robots, "robots_block_missing")
if revision:
    require(f'name="site-factory-revision" content="{revision}"' in home, "revision_meta_missing")

print("static QA passed")
