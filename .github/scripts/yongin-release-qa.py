#!/usr/bin/env python3
"""Verify the manual Yongin release without changing article or snapshot source."""
import argparse
import json
import os
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

ORIGIN = 'https://yongin.fwith.kr'
HUBS = ['/funeral/', '/business/', '/school/', '/event/', '/gift/', '/order/']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_pages(site):
    frozen = json.loads((site / 'src/data/publish-manifest.json').read_text())['pages']
    manual = json.loads((site / 'src/data/manual-pages.json').read_text())['pages']
    require(len(frozen) == 31 and len(manual) == 15, 'Expected 31 frozen and 15 manual pages')
    keys, urls = set(), set()
    for collection in [frozen, manual]:
        keys.clear()
        urls.clear()
        for page in collection:
            key, url = page['pageKey'], page['url']
            require(isinstance(key, str) and key.strip() == key and key, 'Invalid pageKey')
            require(isinstance(url, str) and url.startswith('/') and not url.startswith('//') and url.endswith('/'), 'Invalid page URL')
            require(not any(c.isspace() or c in '?#\\' for c in url), 'Unsafe page URL')
            require(key not in keys and url not in urls, 'Duplicate pageKey or URL')
            keys.add(key)
            urls.add(url)
    old = {p['pageKey']: p for p in frozen}
    replacements = {p['pageKey'] for p in manual if p['pageKey'] in old}
    require(replacements == {'yongin-flower-launch-07','yongin-flower-launch-08','yongin-flower-launch-09','yongin-flower-launch-10','yongin-flower-launch-11','yongin-flower-launch-14'}, 'Expected exactly the six declared manual replacements')
    for page in manual:
        require(page.get('sourceType') == 'manual-authored' and page.get('revisionId'), 'Missing manual identity')
        if page['pageKey'] in old:
            original = old[page['pageKey']]
            require(page.get('supersedesSnapshotId') == original['snapshotId'], 'Incorrect original snapshot')
            require(page['url'] == original['url'], 'Replacement must preserve its original URL')
        else:
            require(not page.get('supersedesSnapshotId'), 'New page cannot claim an original snapshot')
    pages = [p for p in frozen if p['pageKey'] not in replacements] + manual
    require(len(pages) == 40 and len({p['url'] for p in pages}) == 40, 'Expected 40 unique effective detail URLs')
    return pages, manual


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.meta, self.canonicals, self.identities = {}, [], []
        self.title, self.h1 = [], []
        self.title_depth = self.h1_depth = self.h1_count = 0
        self.has_schema = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('name'):
            self.meta[attrs['name']] = attrs.get('content', '')
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonicals.append(attrs.get('href'))
        if tag == 'title':
            self.title_depth += 1
        if tag == 'h1':
            self.h1_depth += 1
            self.h1_count += 1
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.has_schema = True
        if 'article-shell' in attrs.get('class', '').split():
            self.identities.append({k: v for k, v in attrs.items() if k.startswith('data-')})

    def handle_endtag(self, tag):
        if tag == 'title':
            self.title_depth = max(0, self.title_depth - 1)
        if tag == 'h1':
            self.h1_depth = max(0, self.h1_depth - 1)

    def handle_data(self, data):
        if self.title_depth:
            self.title.append(data)
        if self.h1_depth:
            self.h1.append(data)

    def text(self, field):
        return ' '.join(''.join(getattr(self, field)).split())


def verify_page(html, built, path, expected_revision, indexable, entry=None):
    live, local = Page(html), Page(built)
    require(live.meta.get('site-factory-revision') == expected_revision, f'{path}: wrong live revision')
    require(local.meta.get('site-factory-revision') == expected_revision, f'{path}: wrong built revision')
    require(live.canonicals == [ORIGIN + path], f'{path}: wrong canonical')
    directives = {p.strip() for p in live.meta.get('robots', '').lower().split(',')}
    require(('index' if indexable else 'noindex') in directives, f'{path}: wrong indexing directive')
    require('none' not in directives and ('noindex' if indexable else 'index') not in directives, f'{path}: conflicting indexing directive')
    require(live.h1_count == 1 and live.text('h1') == local.text('h1') and live.text('h1'), f'{path}: H1 differs from approved build')
    require(live.text('title') == local.text('title') and live.text('title'), f'{path}: title differs from approved build')
    if entry:
        require(live.has_schema, f'{path}: structured data missing')
        require(len(live.identities) == 1, f'{path}: expected one article identity')
        identity = live.identities[0]
        if entry.get('sourceType') == 'manual-authored':
            require(identity.get('data-manual-revision') == entry['revisionId'], f'{path}: wrong manual revision')
            require('data-snapshot-id' not in identity, f'{path}: manual content must not impersonate frozen snapshot')
            original = entry.get('supersedesSnapshotId')
            require(identity.get('data-original-snapshot') == original, f'{path}: wrong original snapshot reference')
        else:
            require(identity.get('data-snapshot-id') == entry['snapshotId'], f'{path}: frozen snapshot changed')
            require('data-manual-revision' not in identity and 'data-original-snapshot' not in identity, f'{path}: frozen page claims manual identity')


def verify_http_indexing(headers, path):
    values = headers.get_all('X-Robots-Tag', []) if hasattr(headers, 'get_all') else [headers.get('X-Robots-Tag', '')]
    for value in values:
        directives = {part.strip().lower().split(':')[-1].strip() for part in value.split(',')}
        require(not directives.intersection({'noindex', 'none'}), f'{path}: restrictive X-Robots-Tag')


def get(base, path):
    request = urllib.request.Request(base + quote(path, safe='/'), headers={'User-Agent': 'Yongin-Manual-Release-QA/1.0', 'Cache-Control': 'no-cache'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            require(response.geturl() == request.full_url, f'{path}: unexpected redirect')
            return response.status, response.read().decode('utf-8'), response.headers
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode('utf-8'), error.headers


def locations(xml):
    return [unquote(element.text or '') for element in ET.fromstring(xml).iter() if element.tag.rsplit('}', 1)[-1] == 'loc']


def sitemap_urls(base):
    code, index, headers = get(base, '/sitemap-index.xml')
    verify_http_indexing(headers, '/sitemap-index.xml')
    require(code == 200, 'Sitemap index HTTP error')
    sitemap_paths = locations(index)
    require(sitemap_paths == [ORIGIN + '/sitemap-0.xml'], 'Unexpected sitemap index URLs')
    code, sitemap, headers = get(base, '/sitemap-0.xml')
    verify_http_indexing(headers, '/sitemap-0.xml')
    require(code == 200, 'Sitemap HTTP error')
    urls = locations(sitemap)
    require(len(urls) == len(set(urls)), 'Duplicate sitemap URL')
    return set(urls)


def indexnow_scope(manual, live_urls):
    candidates = {ORIGIN + '/', *(ORIGIN + p['url'] for p in manual), *(ORIGIN + '/' + p['category'] + '/' for p in manual)}
    require(len(candidates) == 20, 'Expected 15 manual detail URLs, homepage and four changed hubs')
    require(candidates <= live_urls, 'Changed IndexNow URL missing from live sitemap')
    require(all(urlparse(url).scheme == 'https' and urlparse(url).netloc == 'yongin.fwith.kr' for url in candidates), 'Invalid IndexNow host')
    return sorted(candidates)


def verify_release(site, base, revision, indexable):
    pages, manual = read_pages(site)
    paths = ['/', *HUBS, *(p['url'] for p in pages)]
    entries = {p['url']: p for p in pages}
    for path in paths:
        code, html, headers = get(base, path)
        if indexable:
            verify_http_indexing(headers, path)
        require(code == 200, f'{path}: HTTP {code}')
        built = (site / 'dist' / path.strip('/') / 'index.html').read_text()
        verify_page(html, built, path, revision, indexable, entries.get(path))
    code, robots, headers = get(base, '/robots.txt')
    require(code == 200, 'robots.txt HTTP error')
    if indexable:
        require('Allow: /' in robots and 'Disallow: /' not in robots and f'Sitemap: {ORIGIN}/sitemap-index.xml' in robots, 'Incorrect production robots.txt')
        live_urls = sitemap_urls(base)
        require(live_urls == {ORIGIN + p for p in paths}, 'Sitemap does not match all 47 canonical pages')
        key = os.environ['INDEXNOW_KEY']
        code, body, headers = get(base, '/' + key + '.txt')
        require(code == 200 and body.strip() == key, 'IndexNow key readback failed')
        indexnow_scope(manual, live_urls)
    else:
        require('Disallow: /' in robots and 'Sitemap:' not in robots, 'Incorrect staging robots.txt')
        for path in ['/sitemap-index.xml', '/sitemap-0.xml']:
            require(get(base, path)[0] == 404, f'Staging exposes {path}')
    require(get(base, '/용인꽃배달/')[0] == 404, 'Duplicate landing page is still accessible')
    return {'revision': revision, 'origin': base, 'indexable': indexable, 'detailCount': len(pages), 'frozenCount': len(pages) - len(manual), 'manualCount': len(manual), 'hubCount': len(HUBS), 'verifiedPaths': paths, 'decision': 'pass'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['production', 'staging', 'indexnow'])
    parser.add_argument('--site', type=Path, default=Path('.'))
    args = parser.parse_args()
    if args.mode == 'indexnow':
        _, manual = read_pages(args.site)
        urls = indexnow_scope(manual, sitemap_urls(ORIGIN))
        revision = os.environ['EXPECTED_REVISION']
        pages, _ = read_pages(args.site)
        entries = {p['url']: p for p in pages}
        for url in urls:
            path = urlparse(url).path
            code, html, headers = get(ORIGIN, path)
            require(code == 200, f'{path}: HTTP {code} before IndexNow')
            verify_http_indexing(headers, path)
            built = (args.site / 'dist' / path.strip('/') / 'index.html').read_text()
            verify_page(html, built, path, revision, True, entries.get(path))
        (args.site / 'indexnow-urls.json').write_text(json.dumps(urls, indent=2) + '\n')
        print(f'IndexNow selection: {len(urls)} verified changed public URLs')
        return
    indexable = args.mode == 'production'
    base = ORIGIN if indexable else os.environ['PREVIEW_URL'].rstrip('/')
    if not indexable:
        parsed = urlparse(base)
        require(parsed.scheme == 'https' and parsed.hostname and parsed.hostname.startswith('yongin-flower-v2.') and parsed.hostname.endswith('.workers.dev') and parsed.path == '' and not parsed.query and not parsed.fragment and not parsed.username and not parsed.password, 'Unexpected staging Worker URL')
    revision = os.environ['EXPECTED_REVISION']
    last = None
    for attempt in range(1, 61):
        try:
            receipt = verify_release(args.site, base, revision, indexable)
            (args.site / f'{args.mode}-live-qa.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
            print(f'YONGIN V2 {args.mode.upper()} QA PASSED: revision={revision}, pages=40, manual=15, frozen=25, hubs=6')
            return
        except Exception as error:
            last = error
            print(f'Attempt {attempt}/60: {error}', flush=True)
            if attempt < 60:
                time.sleep(5)
    raise SystemExit(f'Yongin {args.mode} verification failed: {last}')


if __name__ == '__main__':
    main()
