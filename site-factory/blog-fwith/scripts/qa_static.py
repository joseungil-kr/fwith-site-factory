#!/usr/bin/env python3
"""Small static contract for the isolated noindex AstroPaper preview."""
from pathlib import Path
import os
import re


root = Path("dist")
revision = os.environ.get("SITE_FACTORY_REVISION", "")
origin = os.environ.get("SITE_URL", "").rstrip("/")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read(path: str) -> str:
    file = root / path
    require(file.is_file(), f"missing artifact: {path}")
    return file.read_text(encoding="utf-8")


pages = sorted(root.glob("**/*.html"))
require(bool(pages), "no_html_routes")
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
require("X-Robots-Tag: noindex, nofollow" in headers, "noindex_header_missing")
require("User-agent: *" in robots and "Disallow: /" in robots, "robots_block_missing")
require(origin.startswith("https://"), "site_url_missing")
for page in pages:
    html = page.read_text(encoding="utf-8")
    relative = page.relative_to(root).as_posix()
    require('name="robots" content="noindex,nofollow"' in html, f"noindex_meta_missing:{relative}")
    require(
        f'name="site-factory-revision" content="{revision}"' in html,
        f"revision_meta_missing:{relative}",
    )
    canonical = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    require(canonical is not None and canonical.group(1).startswith(origin + "/"), f"canonical_origin_mismatch:{relative}")
    for asset in re.findall(r'(?:src|href)="(/[^"]+)"', html):
        if not (asset.startswith("/_astro/") or asset == "/favicon.svg"):
            continue
        require((root / asset.lstrip("/")).is_file(), f"asset_missing:{relative}:{asset}")

sitemap = read("sitemap-0.xml")
sitemap_origins = set(re.findall(r"<loc>(https?://[^/]+)", sitemap))
require(sitemap_origins == {origin}, "sitemap_origin_mismatch")

print("static QA passed")
