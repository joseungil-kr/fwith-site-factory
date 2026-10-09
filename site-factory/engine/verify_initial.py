#!/usr/bin/env python3
"""Exact full initial-site HTTP/artifact verification; no deployment or approval."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import unquote, urljoin, urlsplit
from html.parser import HTMLParser
import xml.etree.ElementTree as ET

from provision_goyang import target_contract
from whole_initial import is_reviewed_initial_site, reviewed_release_binding, released_initial_keys
from verify_live import (Document, validate_html, goyang_http_fetch,
                         goyang_artifact_matches, require)


def validate_release_links(html, origin, route, routes):
    class Anchors(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag != 'a':
                return
            href = dict(attrs).get('href', '')
            parsed = urlsplit(urljoin(origin + route, href))
            # Hostnames are case-insensitive. Treat same-host links as internal
            # even across scheme/default-port spellings; redirects must not hide
            # links to a deferred route. External shop/phone anchors stay external.
            if parsed.scheme in ('http', 'https') and parsed.hostname == urlsplit(origin).hostname:
                path = unquote(parsed.path)
                require(path in routes, 'Initial internal anchor targets absent release route: ' + path)
    Anchors().feed(html)


def verify(root, site_key, origin, revision, phase, fetch):
    root = Path(root)
    require(is_reviewed_initial_site(site_key) and re.fullmatch(r'[0-9a-f]{40}', revision or ''), 'Unknown initial identity')
    binding = reviewed_release_binding(site_key)
    subset = binding.get('releaseSubset')
    target = target_contract(site_key)
    require(phase in ('preview', 'production') and origin == target['stagingUrl' if phase == 'preview' else 'siteUrl'],
            'Initial HTTP verification origin/phase mismatch')
    manifest = json.loads((root/'src/data/publish-manifest.json').read_text())
    architecture = json.loads((root/'src/data/architecture.json').read_text())
    require(manifest.get('siteKey') == architecture.get('siteKey') == site_key and manifest['pages'],
            'Initial HTTP source has no approved complete site')
    routes = {'/': (None, True)}
    for row in manifest['pages']:
        require(row.get('status') == 'approved' and row.get('approvalVerified') is True
                and re.fullmatch(r'/regions/[a-z0-9-]+/', row.get('url', ''))
                and row['url'] not in routes, 'Invalid initial frozen route')
        routes[row['url']] = (row['snapshotId'], True)
    absent = {'/site-factory-live-qa-definitely-not-found/'}
    if subset is not None:
        coverage = json.loads((root/'src/data/region-coverage.json').read_text())
        reps = {row['pageKey']: row for row in coverage['representatives']}
        released = released_initial_keys(binding, site_key, reps)
        require({row['pageKey'] for row in manifest['pages']} == released, 'Initial HTTP release subset differs')
        absent.update(reps[key]['url'] for key in subset['deferredPageKeys'])
    for hub in architecture['hubs']:
        count = sum(row['category'] == hub['category'] for row in manifest['pages'])
        require(hub.get('children') == count and hub.get('indexable') is (count >= 3)
                and hub.get('menuVisible') is (count >= 5), 'Initial hub eligibility mismatch')
        if count:
            routes[hub['url']] = (None, count >= 3)
        else:
            absent.add(hub['url'])
    expected_html = {'404.html'} | {route.lstrip('/') + 'index.html' for route in routes}
    files = [p for p in (root/'dist').rglob('*') if p.is_file()]
    require(not any(p.is_symlink() for p in (root/'dist').rglob('*')), 'Initial dist cannot contain symlinks')
    actual_html = {p.relative_to(root/'dist').as_posix() for p in files if p.suffix.lower() in ('.html', '.htm', '.xhtml')}
    require(actual_html == expected_html, 'Initial dist HTML inventory differs from frozen routes')

    def response(route):
        status, raw, headers = fetch(route)
        if status == 403:
            raise PermissionError('Initial hosted verification HTTP403; incomplete')
        require(isinstance(raw, bytes), 'Initial HTTP verifier requires original response bytes')
        return status, raw, {k.lower(): v for k, v in headers.items()}

    def headers_ok(headers):
        directives = set(re.split(r'[,\s:]+', headers.get('x-robots-tag', '').lower())) - {''}
        require(directives == {'noindex', 'nofollow', 'noarchive'} if phase == 'preview'
                else not directives.intersection({'noindex', 'nofollow', 'none'}), 'Initial response robots header mismatch')

    fingerprint = hashlib.sha256()
    for route, (snapshot, eligible) in sorted(routes.items()):
        status, raw, headers = response(route)
        require(status == 200, 'Initial route is absent or failed: ' + route)
        require(headers.get('content-type', '').split(';', 1)[0].strip() == 'text/html', 'Initial page MIME mismatch')
        html = raw.decode('utf-8')
        if subset is not None:
            validate_release_links(html, origin, route, set(routes))
        doc = validate_html(html, origin, route, revision, snapshot, phase == 'production' and eligible)
        expected = {'noindex', 'nofollow', 'noarchive'} if phase == 'preview' else {'index', 'follow'} if eligible else {'noindex', 'follow'}
        require(set(doc.metas.get('robots', '').split(',')) == expected, 'Initial exact robots meta mismatch')
        require(doc.snapshots == ([snapshot] if snapshot else []), 'Initial exact snapshot identity mismatch')
        headers_ok(headers)
        artifact = (root/'dist'/route.lstrip('/')/'index.html').read_bytes()
        require(goyang_artifact_matches(html, artifact, phase == 'production'), 'Initial hosted HTML body/schema/CTA differs from built reviewed artifact')
        fingerprint.update(raw)
    for route in sorted(absent):
        status, raw, headers = response(route)
        html = raw.decode('utf-8'); doc = Document(html)
        require(headers.get('content-type', '').split(';', 1)[0].strip() == 'text/html', 'Initial 404 MIME mismatch')
        require(status == 404 and doc.h1 == 1 and doc.metas.get('site-factory-revision') == revision
                and doc.metas.get('robots') == 'noindex,nofollow,noarchive' and not doc.canonicals
                and not doc.snapshots and 'application/ld+json' not in html
                and goyang_artifact_matches(html, (root/'dist/404.html').read_bytes(), phase == 'production'),
                'Initial unknown/empty-hub 404 artifact mismatch')
        headers_ok(headers)
    asset_count = 0
    for file in sorted(files):
        relative = file.relative_to(root/'dist').as_posix()
        if relative in expected_html or relative in ('_headers', '_redirects'):
            continue
        status, raw, headers = response('/' + relative)
        require(status == 200 and raw == file.read_bytes(), 'Initial asset/robots/sitemap/key bytes differ: ' + relative)
        headers_ok(headers)
        mime = {'.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.png':'image/png', '.webp':'image/webp',
                '.svg':'image/svg+xml', '.css':'text/css'}.get(file.suffix.lower())
        if mime:
            require(headers.get('content-type', '').split(';',1)[0].strip() == mime, 'Initial asset MIME mismatch')
        asset_count += 1
    robots = (root/'dist/robots.txt').read_text()
    expected_robots = [('user-agent','*'),('disallow','/')] if phase == 'preview' else [
        ('user-agent','*'),('allow','/'),('sitemap',origin+'/sitemap-index.xml')]
    require([(a.strip().lower(),b.strip()) for a,b in [line.split(':',1) for line in robots.splitlines() if line.strip()]] == expected_robots,
            'Initial robots artifact differs from phase')
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    index = ET.fromstring((root/'dist/sitemap-index.xml').read_bytes())
    require(index.tag == ns+'sitemapindex', 'Initial sitemap index type mismatch')
    locations = [node.text or '' for node in index.findall(ns+'sitemap/'+ns+'loc')]
    require(locations and len(locations) == len(set(locations)) and all(re.fullmatch(re.escape(origin)+r'/sitemap-[0-9]+\.xml', u) for u in locations),
            'Initial sitemap child inventory mismatch')
    urls = []
    for url in locations:
        child = ET.fromstring((root/'dist'/url[len(origin)+1:]).read_bytes())
        require(child.tag == ns+'urlset', 'Initial sitemap child type mismatch')
        urls += [unquote(node.text or '') for node in child.findall(ns+'url/'+ns+'loc')]
    require(len(urls) == len(set(urls)) and set(urls) == {origin+route for route,(_,eligible) in routes.items() if eligible},
            'Initial exact sitemap URL set mismatch')
    return {'pipelineState':'preview_verified' if phase == 'preview' else 'live_verified',
            'siteKey':site_key,'revision':revision,'origin':origin,'manifestPages':len(manifest['pages']),
            'routes':len(routes),'notFoundRoutes':len(absent),'assets':asset_count,'artifactParity':True,
            'htmlSha256':fingerprint.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True); parser.add_argument('--site-key',required=True)
    parser.add_argument('--origin',required=True); parser.add_argument('--revision',required=True)
    parser.add_argument('--phase',choices=['preview','production'],required=True)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--attempts',type=int,default=12)
    parser.add_argument('--delay',type=float,default=5)
    args = parser.parse_args()
    require(1 <= args.attempts <= 12 and 0 <= args.delay <= 30, 'Invalid bounded read-only verification retry')
    for attempt in range(args.attempts):
        try:
            result = verify(args.root,args.site_key,args.origin,args.revision,args.phase,goyang_http_fetch(args.origin))
            break
        except (AssertionError,ValueError,KeyError,TypeError,OSError,ET.ParseError) as error:
            result = {'pipelineState':'verification_blocked' if isinstance(error,PermissionError) else 'verification_failed',
                      'siteKey':args.site_key,'revision':args.revision,'reason':str(error)}
            if isinstance(error,PermissionError):
                break
            if attempt + 1 < args.attempts:
                time.sleep(args.delay)
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))
    return int(result['pipelineState'] not in ('preview_verified','live_verified'))


if __name__ == '__main__':
    raise SystemExit(main())
