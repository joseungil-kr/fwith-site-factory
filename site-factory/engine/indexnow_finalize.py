#!/usr/bin/env python3
"""Finalize an already published revision; never deploy or configure ownership.

Only the existing, independently verified public sitemap is submitted. Journal
writes precede POSTs, so an interrupted or uncertain result cannot auto-repeat.
"""
import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import time
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
import xml.etree.ElementTree as ET

ENDPOINT = 'https://searchadvisor.naver.com/indexnow'
MARKER = 'SITE_FACTORY_INDEXNOW_V1 '
MAX_BYTES = 8 * 1024 * 1024


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()


def normalize(url, origin):
    p = urlsplit(url)
    require(p.scheme == 'https' and p.netloc == urlsplit(origin).netloc and not p.query
            and not p.fragment and not p.username and not p.password, 'foreign_or_unsafe_url')
    path = unquote(p.path)
    require(path.startswith('/') and not any(c in path for c in ('\\', '\n', '\r'))
            and '//' not in path and not any(ord(c) < 32 for c in path)
            and not any(x in ('.', '..') for x in path.split('/')), 'unsafe_url_path')
    return origin + quote(path, safe='/-._~')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def request(method, url, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(url, data=data, method=method,
        headers={'User-Agent': 'SiteFactory-IndexNow/2.0', 'Content-Type': 'application/json; charset=utf-8',
                 'Cache-Control': 'no-cache'})
    try:
        response = build_opener(NoRedirect).open(req, timeout=40)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read(MAX_BYTES + 1)
        require(len(raw) <= MAX_BYTES, 'oversized_http_response')
        headers = {}
        for name, value in response.headers.items():
            name = name.lower()
            headers[name] = headers.get(name, '') + (', ' if name in headers else '') + value
        return response.code, raw.decode('utf-8'), headers


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.meta, self.canonical, self.snapshots = {}, [], []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'data-snapshot-id' in a or 'data-page-key' in a:
            self.snapshots.append((a.get('data-page-key'), a.get('data-snapshot-id')))
        if tag == 'meta':
            name = a.get('name', '').lower()
            self.meta.setdefault(name, []).append(a.get('content', ''))
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split():
            self.canonical.append(a.get('href', ''))


def blocking(value):
    return bool({'noindex', 'none'} & set(re.split(r'[\s,:;]+', value.lower())))


def robots_allows(text, agent, url):
    """Most-specific user-agent and longest path match; Allow wins a tie."""
    groups, agents, rules = [], [], []
    for line in text.splitlines() + ['User-agent: __sentinel__']:
        line = line.split('#', 1)[0].strip()
        if ':' not in line:
            continue
        name, value = (x.strip() for x in line.split(':', 1))
        name = name.lower()
        if name == 'user-agent':
            if rules:
                groups.append((agents, rules)); agents, rules = [], []
            agents.append(value.lower())
        elif name in ('allow', 'disallow') and agents:
            rules.append((name, value))
    matches = []
    for names, group_rules in groups:
        score = max((0 if name == '*' else len(name) for name in names
                     if name == '*' or name in agent.lower()), default=-1)
        if score >= 0:
            matches.append((score, group_rules))
    score = max((item[0] for item in matches), default=-1)
    path = unquote(urlsplit(url).path)
    applicable = []
    for specificity, group_rules in matches:
        if specificity != score:
            continue
        for name, pattern in group_rules:
            if not pattern:
                continue
            pattern = unquote(pattern)
            anchored = pattern.endswith('$')
            if anchored: pattern = pattern[:-1]
            regex = '^' + re.escape(pattern).replace(r'\*', '.*') + ('$' if anchored else '')
            if re.search(regex, path):
                applicable.append((len(pattern.replace('*', '')), name == 'allow'))
    return max(applicable, default=(0, True))[1]


def sitemap_urls(origin, get):
    seen, urls = set(), set()
    def visit(url):
        url = normalize(url, origin)
        require(url not in seen and len(seen) < 100, 'duplicate_or_excess_sitemaps')
        seen.add(url)
        status, text, headers = get(url)
        require(status == 200 and not blocking(headers.get('x-robots-tag', '')), 'sitemap_not_public')
        require(len(text.encode()) <= MAX_BYTES and '<!DOCTYPE' not in text.upper()
                and '<!ENTITY' not in text.upper(), 'unsafe_sitemap_xml')
        doc = ET.fromstring(text)
        kind = doc.tag.split('}')[-1]
        require(kind in ('sitemapindex', 'urlset'), 'invalid_sitemap_root')
        rows = list(doc)
        require(rows, 'empty_sitemap')
        for row in rows:
            loc = row.find('{*}loc')
            require(loc is not None and loc.text, 'missing_sitemap_location')
            value = normalize(loc.text.strip(), origin)
            if kind == 'sitemapindex':
                visit(value)
            else:
                require(value not in urls, 'duplicate_sitemap_url')
                urls.add(value)
                require(len(urls) <= 10000, 'submission_exceeds_single_atomic_batch')
    visit(origin + '/sitemap-index.xml')
    require(origin + '/' in urls, 'sitemap_missing_home')
    return sorted(urls)


def local_get(root, origin):
    base = (Path(root) / 'dist').resolve()
    def get(url):
        path = (base / unquote(urlsplit(url).path).lstrip('/')).resolve()
        require(path.is_relative_to(base), 'unsafe_artifact_path')
        if path.is_dir():
            path = path / 'index.html'
        require(path.is_file(), 'missing_built_artifact')
        return 200, path.read_text(), {}
    return get


def validate_page(url, origin, revision, get, expected=None):
    status, html, headers = get(url)
    require(status == 200, 'page_not_http200')
    require(not blocking(headers.get('x-robots-tag', '')), 'page_header_not_indexable')
    page = Page(html)
    require(page.meta.get('site-factory-revision') == [revision], 'page_revision_mismatch')
    require(len(page.canonical) == 1 and normalize(page.canonical[0], origin) == url, 'page_canonical_mismatch')
    for name in ('robots', 'googlebot', 'bingbot', 'yeti', 'naverbot'):
        require(len(page.meta.get(name, [])) <= 1, 'duplicate_robots_metadata')
        require(not any(blocking(v) for v in page.meta.get(name, [])), 'page_meta_not_indexable')
    require(page.meta.get('robots'), 'missing_robots_metadata')
    if expected is not None:
        require(page.snapshots == expected.snapshots, 'page_snapshot_mismatch')
        for name in ('site-factory-snapshot', 'site-factory-snapshot-id', 'site-factory-snapshot-hash'):
            require(page.meta.get(name) == expected.meta.get(name), 'page_snapshot_mismatch')
    return page


def verify_public(site, revision, root, get, require_ownership=True):
    origin = site['siteUrl'].rstrip('/')
    require(site.get('productionEnabled') is True and site.get('launchMode') == 'live', 'production_gate_closed')
    require(re.fullmatch(r'[0-9a-f]{40}', revision or ''), 'full_revision_required')
    if require_ownership:
        key = site.get('indexnowKey', '')
        require(re.fullmatch(r'[A-Za-z0-9-]{8,128}', key or ''), 'ownership_key_not_configured')
        # A key is usable only on this exact host. Never copy one from another site.
        status, text, _ = get(origin + '/' + key + '.txt')
        require(status == 200 and text.strip() == key, 'ownership_file_not_verified')
    built = local_get(root, origin)
    wanted = sitemap_urls(origin, built)
    current = sitemap_urls(origin, get)
    require(current == wanted, 'live_sitemap_differs_from_exact_source')
    status, robots, headers = get(origin + '/robots.txt')
    require(status == 200 and not blocking(headers.get('x-robots-tag', '')), 'robots_not_public')
    for url in current:
        require(all(robots_allows(robots, agent, url) for agent in ('*', 'Yeti', 'bingbot', 'Googlebot', 'IndexNow')),
                'robots_disallows_sitemap_url')
        artifact = validate_page(url, origin, revision, built)
        validate_page(url, origin, revision, get, artifact)
    return current


class Journal:
    def __init__(self, repository, number):
        require(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository or ''), 'invalid_repository')
        require(isinstance(number, int) and number > 0, 'submission_journal_not_configured')
        self.path = f'repos/{repository}/issues/{number}/comments'
        self.read_path = f'repos/{repository}/issues/comments'

    def records(self):
        # gh --slurp preserves page boundaries and does not truncate older receipts.
        data = json.loads(subprocess.run(['gh', 'api', '--paginate', '--slurp', self.read_path + '?per_page=100'],
            check=True, capture_output=True, text=True).stdout)
        records = []
        for page in data:
            for comment in page:
                # Only workflow-owned journal records affect execution. A user or
                # third-party comment cannot forge an accepted/unknown submission.
                if comment.get('user', {}).get('login') != 'github-actions[bot]':
                    continue
                body = comment.get('body', '')
                if body.startswith(MARKER):
                    records.append(json.loads(body[len(MARKER):]))
        return records

    def write(self, record):
        body = MARKER + json.dumps(record, ensure_ascii=False, sort_keys=True)
        subprocess.run(['gh', 'api', '--method', 'POST', self.path, '--input', '-'],
            input=json.dumps({'body': body}), check=True, capture_output=True, text=True)


def finalize(site, revision, root, journal, transport=request, run_url='', sleep=time.sleep):
    origin = site['siteUrl'].rstrip('/')
    get = lambda url: transport('GET', url)
    urls = verify_public(site, revision, root, get)
    identity = {'siteKey': site.get('siteKey', ''), 'origin': origin, 'revision': revision,
        'endpoint': ENDPOINT, 'urlSetSha256': digest(urls), 'urlCount': len(urls)}
    fingerprint = digest({**identity, 'keySha256': digest(site['indexnowKey'])})
    previous = [r for r in journal.records() if r.get('fingerprint') == fingerprint]
    if previous:
        latest = previous[-1]
        if latest.get('state') in ('received', 'received_key_validation_pending'):
            return {**identity, 'state': 'already_received', 'receiptState': latest['state'],
                    'httpStatus': latest['httpStatus'], 'fingerprint': fingerprint,
                    'receiptRun': latest.get('runUrl'), 'urls': urls}
        require(latest.get('state') == 'rejected', 'prior_submission_outcome_uncertain')
        require(time.time() >= latest.get('retryNotBefore', 0), 'indexnow_retry_after_not_elapsed')
    record = {**identity, 'fingerprint': fingerprint, 'runUrl': run_url}
    # Re-read complete live sitemap and every public route immediately before
    # each POST (including explicit 429 retries); never submit stale selection.
    for attempt in range(1, 4):
        require(verify_public(site, revision, root, get) == urls, 'public_source_changed_before_submission')
        started = {**record, 'state': 'started', 'attempt': attempt,
                   'recordedAt': datetime.now(timezone.utc).isoformat()}
        journal.write(started)  # If this fails, do not submit anything.
        try:
            status, _, headers = transport('POST', ENDPOINT, {
                'host': urlsplit(origin).netloc, 'key': site['indexnowKey'],
                'keyLocation': origin + '/' + site['indexnowKey'] + '.txt', 'urlList': urls})
        except Exception:
            journal.write({**started, 'state': 'unknown'})
            raise ValueError('submission_outcome_uncertain') from None
        state = ('received' if status == 200 else 'received_key_validation_pending' if status == 202
                 else 'rejected' if status in (400, 403, 422, 429) else 'unknown')
        result = {**started, 'state': state, 'httpStatus': status}
        if status == 429:
            raw_delay = headers.get('retry-after', '')
            try:
                delay = int(raw_delay) if raw_delay.isdigit() else max(0, int(parsedate_to_datetime(raw_delay).timestamp() - time.time())) if raw_delay else 10 * attempt
            except (ValueError, TypeError, OverflowError):
                delay = 3600
            result['retryNotBefore'] = time.time() + max(10 * attempt, delay)
        journal.write(result)  # Missing receipt leaves started, blocking replay.
        if status in (200, 202):
            return {**result, 'urls': urls}
        if status == 429 and attempt < 3:
            # Never shorten a requested retry delay or retry a 5xx/timeout.
            delay = max(10 * attempt, delay)
            if delay > 120:
                break
            sleep(delay)
            continue
        break
    raise ValueError('indexnow_' + state + '_http_' + str(status))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--site-key', required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--receipt-issue', type=int, required=True)
    parser.add_argument('--run-url', default='')
    args = parser.parse_args()
    try:
        registry = json.loads(args.registry.read_text())
        site = dict(registry['sites'][args.site_key], siteKey=args.site_key)
        journal = Journal(site['repo'], args.receipt_issue)
        result = finalize(site, args.revision, args.root, journal, run_url=args.run_url)
        result['pipelineState'] = 'live_verified_indexnow_received'
        result['searchIndexing'] = 'not_verified'
        ok = True
    except Exception as error:
        # Exception bodies/URLs may contain ownership keys or credentials.
        safe = str(error) if type(error) is ValueError and re.fullmatch(r'[a-z0-9_]+', str(error)) else type(error).__name__
        result = {'pipelineState': 'indexnow_blocked_or_failed', 'siteKey': args.site_key,
                  'revision': args.revision, 'reason': safe, 'searchIndexing': 'not_verified'}
        ok = False
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'urls'}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
