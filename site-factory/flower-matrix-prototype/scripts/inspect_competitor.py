#!/usr/bin/env python3
"""Capture public competitor evidence; compare only verified, comparable captures.

Body text is HTML body text, not a CSS/JavaScript visibility audit.
The JSON embeds exact response bytes as base64 so the existing CI artifact
(competitor-structure.json) retains originals without a workflow change.
"""
import argparse
import base64
import codecs
from datetime import datetime, timedelta, timezone
from email.message import Message
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

RAW = [
    "https://graduation.m-castle.co.kr/축하화환/2658.html",
    "https://order.m-castle.co.kr/축하화환/2658.html",
    "https://passion.m-castle.co.kr/축하화환/1286.html",
]
KST = timezone(timedelta(hours=9))
IGNORED = {"script", "style", "template", "noscript"}
BLOCKS = {"address", "article", "aside", "blockquote", "br", "div", "dl", "dt", "dd",
          "fieldset", "figcaption", "figure", "footer", "form", "header", "hr", "li",
          "main", "nav", "ol", "p", "section", "table", "td", "th", "tr", "ul",
          "h1", "h2", "h3", "h4", "h5", "h6"}


def norm(text):
    return re.sub(r"\s+", " ", text).strip()


def safe_url(raw):
    p = urlsplit(raw)
    if p.scheme != "https" or not p.hostname or p.username or p.password:
        raise ValueError("public_https_url_required")
    return urlunsplit((p.scheme, p.netloc, quote(p.path, safe="/%:@"), p.query, ""))


class Doc(HTMLParser):
    def __init__(self, text, final_url):
        super().__init__(convert_charrefs=True)
        self.base = final_url
        self.title_parts = []; self.meta = {}; self.canonical = []
        self.headings = []; self.links = []; self.images = []; self.body_parts = []
        self.in_body = False; self.saw_body = False; self.in_title = False
        self.ignored = 0; self.heading = None; self.anchor = None
        self.feed(text)
        self.close()
        self.title = norm("".join(self.title_parts))
        self.body_text = "\n".join(filter(None, (norm(line) for line in "".join(self.body_parts).splitlines())))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in IGNORED:
            self.ignored += 1
            return
        if self.ignored:
            return
        if tag == "body":
            self.in_body = self.saw_body = True
        if tag == "title": self.in_title = True
        if tag == "base" and a.get("href"): self.base = urljoin(self.base, a["href"])
        if tag == "meta": self.meta[a.get("name", a.get("property", "")).lower()] = a.get("content", "")
        if tag == "link" and "canonical" in a.get("rel", "").lower().split():
            self.canonical.append(urljoin(self.base, a.get("href", "")))
        if not self.in_body:
            return
        if tag in BLOCKS: self.body_parts.append("\n")
        if re.fullmatch(r"h[1-6]", tag):
            self.heading = {"level": int(tag[1]), "parts": []}
            self.headings.append(self.heading)
        if tag == "a" and a.get("href"):
            self.anchor = {"href": a["href"], "url": urljoin(self.base, a["href"]), "parts": []}
            self.links.append(self.anchor)
        if tag == "img" and a.get("src"):
            self.images.append({"src": a["src"], "url": urljoin(self.base, a["src"]), "alt": a.get("alt", "")})

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in IGNORED:
            self.ignored = max(0, self.ignored - 1)
            return
        if self.ignored:
            return
        if tag == "title": self.in_title = False
        if self.in_body and tag in BLOCKS: self.body_parts.append("\n")
        if self.heading is not None and tag == "h" + str(self.heading["level"]): self.heading = None
        if tag == "a": self.anchor = None
        if tag == "body": self.in_body = False

    def handle_data(self, data):
        if self.ignored:
            return
        if self.in_title: self.title_parts.append(data)
        if not self.in_body:
            return
        self.body_parts.append(data)
        if self.heading is not None: self.heading["parts"].append(data)
        if self.anchor is not None: self.anchor["parts"].append(data)


def decode_html(body, content_type):
    header = Message(); header["Content-Type"] = content_type
    declared = header.get_content_charset()
    meta = re.search(br"charset\s*=\s*[\"']?\s*([a-zA-Z0-9._-]+)", body[:4096], re.I)
    meta_charset = meta.group(1).decode("ascii") if meta else None
    bom = "utf-8-sig" if body.startswith(codecs.BOM_UTF8) else (
        "utf-16" if body.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)) else None)
    encoding = "utf-8"; source = "fallback"
    for candidate, candidate_source in [(bom, "bom"), (declared, "http"), (meta_charset, "meta")]:
        if candidate:
            try:
                encoding = codecs.lookup(candidate).name; source = candidate_source
                break
            except LookupError:
                continue
    try:
        text = body.decode(encoding); lossy = False
    except UnicodeDecodeError:
        text = body.decode(encoding, "replace"); lossy = True
    return text, {"encoding": encoding, "encodingSource": source,
                  "httpCharset": declared, "metaCharset": meta_charset, "decodeLossy": lossy}


def timestamps(now):
    dt = now().astimezone(timezone.utc)
    return {"collectedAtUtc": dt.isoformat().replace("+00:00", "Z"),
            "collectedAtKst": dt.astimezone(KST).isoformat()}


def capture(raw, output_dir, run_dir, index, opener, now):
    row = {"requestedUrl": raw, "captureStatus": "failed", "status": None, "finalUrl": None}
    try:
        url = safe_url(raw); row["fetchUrl"] = url
        request = Request(url, headers={"User-Agent": "SiteFactory-StructureResearch/2.0"})
        with opener(request, timeout=25) as response:
            row.update(status=response.status, finalUrl=response.geturl())
            content_type = response.headers.get("Content-Type", "")
            if response.status != 200:
                row["failureReason"] = "http_status_not_200"
                return row
            body = response.read()
        row["contentType"] = content_type
        stem = f"{index:02d}-{urlsplit(url).hostname}"
        html_path = run_dir / (stem + ".html")
        html_path.write_bytes(body)
        row["rawHtml"] = {"path": html_path.relative_to(output_dir).as_posix(),
                          "sha256": sha256(body).hexdigest(), "bytes": len(body),
                          "base64": base64.b64encode(body).decode("ascii")}
        row["captureStatus"] = "unverified"
        if content_type.split(";", 1)[0].strip().lower() not in {"text/html", "application/xhtml+xml"}:
            row["failureReason"] = "html_content_type_required"
            return row
        try:
            text, decoding = decode_html(body, content_type)
        except LookupError:
            row["failureReason"] = "unsupported_html_encoding"
            return row
        row.update(decoding)
        d = Doc(text, row["finalUrl"])
        body_bytes = d.body_text.encode("utf-8")
        body_path = run_dir / (stem + ".body.txt")
        body_path.write_bytes(body_bytes)
        headings = [{"level": h["level"], "text": norm("".join(h["parts"]))} for h in d.headings]
        links = [{"href": a["href"], "url": a["url"], "anchor": norm("".join(a["parts"]))} for a in d.links]
        row.update(title=d.title, description=d.meta.get("description"), robots=d.meta.get("robots"),
                   canonical=d.canonical, headings=headings, links=links, images=d.images,
                   headingCounts={f"h{i}": sum(h["level"] == i for h in headings) for i in range(1, 7)},
                   imageCount=len(d.images), imageHosts=sorted({urlsplit(x["url"]).hostname for x in d.images if urlsplit(x["url"]).hostname}),
                   internalLinkCount=sum(urlsplit(x["url"]).hostname == urlsplit(row["finalUrl"]).hostname for x in links),
                   bodyText={"path": body_path.relative_to(output_dir).as_posix(), "encoding": "utf-8",
                             "sha256": sha256(body_bytes).hexdigest(), "text": d.body_text},
                   visibleTextLength=len(d.body_text), visibleTextSha256=sha256(body_bytes).hexdigest(),
                   imageListSha256=sha256("\n".join(x["url"] for x in d.images).encode("utf-8")).hexdigest())
        if not d.saw_body or not d.body_text:
            row["failureReason"] = "nonempty_html_body_required"
        elif decoding["decodeLossy"]:
            row["failureReason"] = "lossy_html_decode"
        else:
            row["captureStatus"] = "success"
    except HTTPError as exc:
        row.update(status=exc.code, errorType="HTTPError", failureReason="http_error")
        if exc.fp is not None:
            exc.close()
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        row.update(errorType=type(exc).__name__, failureReason="capture_failed")
    finally:
        row.update(timestamps(now))
    return row


def compare_pair(rows):
    result = {"state": "unverified", "same2658PathAcrossSubdomains": None, "same2658Title": None,
              "same2658Description": None, "same2658VisibleText": None, "same2658Images": None}
    pair = [r for r in rows if unquote(urlsplit(r.get("fetchUrl", "")).path).endswith("/2658.html")]
    if len(pair) != 2 or any(r.get("captureStatus") != "success" for r in pair):
        result["reason"] = "two_successful_pair_captures_required"
        return result
    a, b = pair
    paths = [unquote(urlsplit(r["finalUrl"]).path) for r in pair]
    hosts = [urlsplit(r["finalUrl"]).hostname for r in pair]
    if paths[0] != paths[1] or hosts[0] == hosts[1]:
        result["reason"] = "matching_final_paths_and_distinct_hosts_required"
        return result
    result.update(state="compared", same2658PathAcrossSubdomains=True,
                  same2658VisibleText=a["bodyText"]["sha256"] == b["bodyText"]["sha256"],
                  same2658Images=a["images"] == b["images"])
    for field, key in [("title", "same2658Title"), ("description", "same2658Description")]:
        if a.get(field) and b.get(field): result[key] = a[field] == b[field]
    result["unverifiedFields"] = [f for f in ("title", "description") if not a.get(f) or not b.get(f)]
    return result


def inspect_urls(urls, output_dir=Path("."), opener=None, now=None):
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    evidence_root = output_dir / "competitor-evidence"; evidence_root.mkdir(exist_ok=True)
    now = now or (lambda: datetime.now(timezone.utc))
    stamp = now().astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-")
    run_dir = Path(tempfile.mkdtemp(prefix=stamp, dir=evidence_root))
    rows = [capture(raw, output_dir, run_dir, index, opener or urlopen, now) for index, raw in enumerate(urls, 1)]
    report = {"schemaVersion": 2, "scope": "public-source-evidence-and-structure-no-reuse-in-site-copy",
              "bodyTextExtraction": "body only; excludes script/style/template/noscript; block newlines and whitespace normalized; CSS visibility not evaluated",
              "evidencePolicy": "rawHtml.base64 is exact response bytes; bodyText.text is separate derived UTF-8 text; path fields point to companion files",
              "rows": rows, "comparison": compare_pair(rows), "similarityMetrics": None,
              "rankingCause": "unproven-hypothesis"}
    (output_dir / "competitor-structure.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    report = inspect_urls(RAW, args.output_dir)
    print(json.dumps({"rows": [{"url": r["requestedUrl"], "status": r["status"],
                                 "captureStatus": r["captureStatus"], "failureReason": r.get("failureReason")}
                                for r in report["rows"]], "comparison": report["comparison"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
