#!/usr/bin/env python3
"""Manual, no-deploy six-region completion. Default is verification only.

No key creation, configuration mutation, deployment, automatic POST retry or
dependency on the Site Factory execution pipeline. Existing public keys only.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

REPO = 'joseungil-kr/fwith-site-factory'
ENDPOINT = 'https://searchadvisor.naver.com/indexnow'
MARKER = 'MANUAL_SIX_INDEXNOW_20261007 '
ALLOWED = {
 'namyangju-flower-v2': ('d02e86ed7fc39131431a0332a84002906be2f88b', 36),
 'bucheon-flower-v2': ('1f00f46ef2afad7dcc0ca814d98ec31cf7abc73e', 42),
 'suwon-flower-test': ('e6e8248c44733583d2cbe08288db655fa9bc2302', 54),
 'seongnam-flower-v2': ('06f4049c2c8e818ef7474e628031c5f901b4ecab', 35),
 'goyang-flower-v2': ('0a8b3de17a4a7badadcbc1c4f4bf0e5b2f085777', 69),
 'hwaseong-flower': ('d7d7f47ecafc9bd9e3a75511379d430cd00e8510', 65),
}

def require(ok, message):
    if not ok: raise ValueError(message)

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()

def sha(value): return hashlib.sha256(value).hexdigest()

def api(path):
    command = ['gh', 'api', path]
    return json.loads(subprocess.run(command, text=True, capture_output=True, check=True).stdout)

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None

def request(method, url, payload=None):
    req = Request(url, data=None if payload is None else canonical(payload), method=method,
        headers={'User-Agent': 'SiteFactory-LiveQA/3.0', 'Cache-Control': 'no-cache',
                 'Content-Type': 'application/json; charset=utf-8'})
    try: response = build_opener(NoRedirect).open(req, timeout=40)
    except HTTPError as error: response = error
    with response:
        # Record status even if reading the accepted response body fails.
        if method == 'POST': return response.status, '', {}
        raw = response.read(8 * 1024 * 1024 + 1)
        require(len(raw) <= 8 * 1024 * 1024, 'response_too_large')
        headers = {}
        for name, value in response.headers.items():
            key = name.lower(); headers[key] = headers.get(key, '') + (',' if key in headers else '') + value
        return response.status, raw, headers

def normalize(url, origin):
    p = urlsplit(url)
    require(p.scheme == 'https' and p.netloc == urlsplit(origin).netloc and
            not p.query and not p.fragment and not p.username and not p.password, 'unsafe_url')
    path = unquote(p.path)
    require(path.startswith('/') and '//' not in path and '\\' not in path and
            not any(ord(c) < 32 for c in path) and
            not any(x in ('.', '..') for x in path.split('/')), 'unsafe_path')
    return origin + quote(path, safe='/-._~')

def mime(value): return value.split(';', 1)[0].strip().lower()

def blocked(value): return bool(re.search(r'\b(noindex|nofollow|none)\b', value, re.I))

class Page(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.meta = {}; self.canonicals = []; self.feed(html)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta': self.meta.setdefault(a.get('name', '').lower(), []).append(a.get('content', ''))
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split(): self.canonicals.append(a.get('href'))

def validate_page(html, headers, url, site):
    page = Page(html)
    require(page.meta.get('site-factory-revision') == [site['revision']], 'revision_mismatch')
    require(len(page.canonicals) == 1 and normalize(page.canonicals[0], site['origin']) == url, 'canonical_mismatch')
    require(len(page.meta.get('robots', [])) == 1, 'robots_missing_or_duplicate')
    for name in ('robots', 'googlebot', 'bingbot', 'yeti', 'naverbot', 'indexnow'):
        require(len(page.meta.get(name, [])) <= 1 and not any(blocked(v) for v in page.meta.get(name, [])), 'robots_blocked')
    require(not blocked(headers.get('x-robots-tag', '')), 'header_blocked')

PINNED_MANAGED_BEACONS = (
 (b'https://static.cloudflareinsights.com/beacon.min.js/v31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495', '8a5cd48fb3f913d009a128498bef6fadc43d5561daec87e79f6adcd0bcc903f5'),
 (b'https://static.cloudflareinsights.com/beacon.min.js/v4bc70e2c01a94c73b74392e4234840661791215815920', '53ed6266d9ab3cb60b83bb38278a519b4b688707f7254f5ffeeeb8bcaa3a5e4c'),
)

def artifact_matches(data, row):
    """Hash-only equivalent of immutable M4's exact whole insertion matcher."""
    if isinstance(data, str): data = data.encode()
    wanted = row['expectedSha256']
    if sha(data) == wanted: return True
    closing = b'</body></html>'
    if mime(row['headers'].get('content-type', '')) != 'text/html' or not data.endswith(closing): return False
    length = row['comparison']['expectedArtifactBytes']
    if length < len(closing) or len(data) <= length: return False
    prefix_end = length - len(closing)
    insertion = data[prefix_end:-len(closing)]
    if not (insertion.endswith(b'</script>\n') and insertion.count(b'<script') == 1 and
        any(insertion.startswith(b'<script type="module" src="' + src + b'" ') and sha(insertion) == digest
            for src, digest in PINNED_MANAGED_BEACONS)): return False
    reconstructed = data[:prefix_end] + closing
    return len(reconstructed) == length and sha(reconstructed) == wanted

def checked_json(root, path, expected):
    file = (root / path).resolve()
    require(file.is_relative_to(root.resolve()) and file.is_file(), 'invalid_bound_evidence_path')
    raw = file.read_bytes(); require(sha(raw) == expected, 'bound_evidence_hash_mismatch')
    return json.loads(raw)

def attest(site, root, api_get=api):
    require(ALLOWED.get(site['siteKey']) == (site['revision'], site['urlCount']), 'outside_approved_scope')
    region = site['siteKey'].split('-')[0]
    require(site['origin'] == 'https://' + region + '.fwith.kr', 'wrong_origin')
    qa = site['qa']
    require(qa['status'] == 'passed' and qa['independentReviewer'], 'independent_public_qa_pending')
    path = (root / qa['evidencePath']).resolve()
    require(path.is_relative_to(root.resolve()) and path.is_file(), 'invalid_evidence_path')
    raw = path.read_bytes(); require(sha(raw) == qa['evidenceSha256'], 'evidence_hash_mismatch')
    evidence = json.loads(raw)
    require(evidence['status'] == 'passed' and evidence['sourceRevision'] == site['revision'] and
            evidence['origin'] == site['origin'] and evidence['siteKey'] == site['siteKey'] and
            evidence['runId'] == qa['runId'] and evidence['reviewer'] == qa['independentReviewer'] and
            evidence['author'] != evidence['reviewer'] and evidence['author'], 'evidence_identity_mismatch')
    for name in ('allPublicBytes', 'allRoutes', 'desktopPixels', 'mobilePixels', 'links', 'canonical', 'robots', 'sitemap', 'real404'):
        require(evidence['checks'].get(name) is True, 'independent_check_missing_' + name)
    require(re.fullmatch('[a-f0-9]{64}', evidence['urlSetSha256']), 'missing_reviewed_url_hash')
    original = checked_json(root, qa['rawReportPath'], qa['rawReportSha256'])
    http = checked_json(root, qa['httpReceiptsPath'], qa['httpReceiptsSha256'])
    if original.get('city') == 'suwon':
        require(original.get('passed') is True and original.get('decision') == 'passed', 'original_suwon_review_not_passed')
        original = dict(original, decision='PASS', reviewer=original['reviewerId'],
            httpBodiesHashVerified=original['coverage']['httpResponses'],
            artifactDigests={str(a['id']):a['digest'].removeprefix('sha256:') for a in original['artifacts']})
    require(original['decision'] == 'PASS' and original['sourceRevision'] == site['revision'] and
        original['runId'] == qa['runId'] and original['executionRevision'] == qa['runHeadSha'] and
        original['reviewer'] == evidence['reviewer'] and original.get('origin', site['origin']) == site['origin'] and
        original['artifactDigests'] == evidence['artifactDigests'] and
        evidence['rawReportSha256'] == qa['rawReportSha256'] and
        evidence['httpReceiptsSha256'] == qa['httpReceiptsSha256'], 'original_review_identity_mismatch')
    require(http['passed'] is True and http['phase'] == 'production' and http['sourceRevision'] == site['revision'] and
        http['origin'] == site['origin'] and int(http['runId']) == qa['runId'] and
        len(http['responses']) == original['httpBodiesHashVerified'], 'original_http_identity_mismatch')
    require(all(row['status'] == row['expectedStatus'] and row['exactFinalUrl'] and
        row['expectedSha256'] == row['comparison']['expectedArtifactSha256'] for row in http['responses']), 'invalid_original_http_receipt')
    evidence['_http'] = http
    run = api_get(f'repos/{REPO}/actions/runs/{qa["runId"]}')
    require(run['status'] == 'completed' and run['conclusion'] == 'success' and
            run['head_sha'] == qa['runHeadSha'], 'qa_run_not_verified')
    branch = api_get(f'repos/{REPO}/git/ref/heads/{site["branch"]}')
    require(branch['object']['sha'] == site['revision'], 'public_source_branch_moved')
    return evidence

def verify(site, evidence, transport=request):
    origin = site['origin']; key = site['indexnowKey']
    require(re.fullmatch('[A-Za-z0-9-]{8,128}', key), 'existing_key_missing')
    # Verify every retained artifact, including images, noindex thin hubs and real
    # 404, before any submission. Then reuse exactly those checked response bytes.
    cached = {}
    rows = evidence['_http']['responses']
    for row in rows:
        url = normalize(row['url'], origin)
        require(url not in cached, 'duplicate_reviewed_http_route')
        status, body, headers = transport('GET', url)
        require(status == row['expectedStatus'] and status not in (401, 403, 429), 'reviewed_http_status_mismatch')
        require(artifact_matches(body, row), 'reviewed_artifact_bytes_changed')
        require(headers.get('x-robots-tag', '').lower() == row['headers'].get('x-robots-tag', '').lower(), 'reviewed_robots_header_changed')
        if mime(row['headers'].get('content-type', '')) == 'text/html':
            require(mime(headers.get('content-type', '')) == 'text/html', 'page_content_type_changed')
        cached[url] = (body, headers, status)
    def get(url):
        url = normalize(url, origin)
        require(url in cached, 'url_not_in_reviewed_http_artifacts')
        body, headers, status = cached[url]
        require(status == 200, 'public_get_http_' + str(status))
        require(not blocked(headers.get('x-robots-tag', '')), 'public_header_blocked')
        return body.decode('utf-8') if isinstance(body, bytes) else body, headers
    body, _ = get(origin + '/' + key + '.txt'); require(body.strip() == key, 'existing_ownership_mismatch')
    seen = set(); urls = set()
    def visit(url):
        url = normalize(url, origin)
        require(url not in seen and len(seen) < 20, 'sitemap_cycle_or_limit'); seen.add(url)
        body, _ = get(url)
        require('<!DOCTYPE' not in body.upper() and '<!ENTITY' not in body.upper(), 'unsafe_xml')
        doc = ET.fromstring(body); kind = doc.tag.split('}')[-1]
        require(kind in ('sitemapindex', 'urlset') and len(doc), 'invalid_sitemap')
        for row in doc:
            loc = row.find('{*}loc'); require(loc is not None and loc.text, 'missing_loc')
            child = normalize(loc.text.strip(), origin)
            if kind == 'sitemapindex': visit(child)
            else:
                require(child not in urls, 'duplicate_url'); urls.add(child)
    visit(origin + '/sitemap-index.xml')
    urls = sorted(urls)
    require(len(urls) == site['urlCount'] and origin + '/' in urls, 'sitemap_count_mismatch')
    require(sha(canonical(urls)) == evidence['urlSetSha256'], 'reviewed_sitemap_changed')
    body, _ = get(origin + '/robots.txt'); robot = RobotFileParser()
    for line in body.splitlines():
        name, _, value = line.partition(':')
        require(not (name.strip().lower() in ('allow', 'disallow') and any(x in value for x in ('*', '$'))), 'unsupported_robots_pattern')
    robot.parse(body.splitlines())
    for url in urls:
        require(all(robot.can_fetch(agent, url) for agent in ('*', 'Yeti', 'Naverbot', 'bingbot', 'Googlebot', 'IndexNow')), 'robots_disallow')
        html, headers = get(url)
        require(mime(headers.get('content-type', '')) == 'text/html', 'page_content_type_changed')
        validate_page(html, headers, url, site)
    return urls

def atomic_json(path, value):
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w') as output:
        output.write(json.dumps(value, indent=2) + '\n'); output.flush(); os.fsync(output.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)

class Journal:
    """Local receipt only. Execution needs separately uploaded pre-POST intent."""
    def __init__(self, path): self.path = path
    def records(self):
        return [json.loads(self.path.read_text())] if self.path.exists() else []
    def write(self, record):
        atomic_json(self.path, record)
        require(json.loads(self.path.read_text()) == record, 'receipt_readback_failed')
        return 'workflow-artifact:' + self.path.name

def public_api(path):
    status, body, _ = request('GET', 'https://api.github.com/' + path)
    require(status == 200, 'github_read_failed')
    return json.loads(body)

def execution_guard(site, intent, api_get=public_api):
    require(os.environ.get('GITHUB_REPOSITORY') == REPO and os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'first_trusted_workflow_attempt_required')
    region = site['siteKey'].split('-')[0]
    branch = 'manual-' + region + '-indexnow-final-20261007'
    workflow = region + '-manual-indexnow-final-20261007.yml'
    require(os.environ.get('GITHUB_REF') == 'refs/heads/' + branch and os.environ.get('GITHUB_EVENT_NAME') == 'push', 'wrong_execution_trigger')
    current = str(os.environ['GITHUB_RUN_ID'])
    page = 1
    while True:
        data = api_get(f'repos/{REPO}/actions/workflows/{workflow}/runs?per_page=100&page={page}')
        rows = data['workflow_runs']
        require(len(rows) == 1 and str(rows[0]['id']) == current, 'prior_one_time_run_blocks_replay')
        run = rows[0]
        require(run.get('head_sha') == os.environ.get('GITHUB_SHA') and run.get('head_branch') == branch and
            run.get('event') == 'push' and run.get('run_attempt') == 1 and
            run.get('path') == '.github/workflows/' + workflow, 'current_run_identity_mismatch')
        if len(rows) < 100: break
        page += 1
    data = api_get(f'repos/{REPO}/actions/runs/{current}/artifacts?per_page=100')
    name = 'indexnow-intent-' + region + '-' + sha(canonical(intent))
    found = [a for a in data['artifacts'] if a['name'] == name and not a['expired']]
    require(len(found) == 1 and found[0]['size_in_bytes'] > 0, 'durable_intent_artifact_missing')

def prior_result(records, site):
    # Any prior attempt for the same public revision blocks a second POST unless
    # an accepted receipt proves it is already done. Rejection is not auto-retry.
    prior = [r for r in records if r.get('origin') == site['origin'] and
             r.get('revision', r.get('sourceRevision')) == site['revision'] and r.get('endpoint') == ENDPOINT]
    if not prior: return None
    last = prior[-1]
    require(last.get('state') in ('received', 'received_key_validation_pending'), 'prior_attempt_do_not_replay')
    require((last.get('state'), last.get('httpStatus')) in (('received', 200), ('received_key_validation_pending', 202)), 'accepted_receipt_inconsistent')
    return last

def submit(site, urls, journal, transport=request, run_url=''):
    old = prior_result(journal.records(), site)
    if old:
        require(old.get('urlCount') == len(urls) and old.get('urlSetSha256') == sha(canonical(urls)) and
            old.get('keySha256') == sha(site['indexnowKey'].encode()), 'prior_receipt_identity_mismatch')
        return {**old, 'state': 'already_received'}
    record = {'siteKey': site['siteKey'], 'origin': site['origin'], 'revision': site['revision'],
        'endpoint': ENDPOINT, 'urlCount': len(urls), 'urlSetSha256': sha(canonical(urls)),
        'keySha256': sha(site['indexnowKey'].encode()), 'runUrl': run_url}
    record['fingerprint'] = sha(canonical(record | {'runUrl': ''}))
    record['state'] = 'started'; journal.write(record) # Durable readback before POST.
    try:
        status, _, _ = transport('POST', ENDPOINT, {'host': urlsplit(site['origin']).netloc,
            'key': site['indexnowKey'], 'keyLocation': site['origin'] + '/' + site['indexnowKey'] + '.txt', 'urlList': urls})
    except Exception:
        journal.write(record | {'state': 'unknown'})
        raise ValueError('post_outcome_unknown_do_not_retry') from None
    state = 'received' if status == 200 else 'received_key_validation_pending' if status == 202 else 'unknown' if status >= 500 else 'rejected'
    result = record | {'state': state, 'httpStatus': status}
    result['receiptUrl'] = journal.write(result)
    require(status in (200, 202), 'post_not_accepted_do_not_retry')
    return result

def run_cli():
    p = argparse.ArgumentParser(); p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--site', choices=ALLOWED, required=True); p.add_argument('--report', type=Path, required=True)
    p.add_argument('--submit', action='store_true'); p.add_argument('--intent', type=Path, required=True)
    args = p.parse_args(); report = {'siteKey': args.site, 'state': 'not_submitted'}
    try:
        plan = json.loads(args.plan.read_text())
        require(plan['repository'] == REPO and plan['endpoint'] == ENDPOINT, 'wrong_plan_destination')
        matches = [s for s in plan['sites'] if s['siteKey'] == args.site]
        require(len(matches) == 1, 'duplicate_or_missing_site'); site = matches[0]
        evidence = attest(site, args.plan.parent, public_api); urls = verify(site, evidence, transport=request)
        report.update(state='verified_not_submitted', revision=site['revision'], urlCount=len(urls), urlSetSha256=sha(canonical(urls)))
        intent = {'siteKey': site['siteKey'], 'origin': site['origin'], 'revision': site['revision'],
            'endpoint': ENDPOINT, 'urls': urls, 'keySha256': sha(site['indexnowKey'].encode()),
            'qaEvidenceSha256': site['qa']['evidenceSha256'], 'runId': os.environ.get('GITHUB_RUN_ID')}
        if args.submit:
            require(args.intent.read_bytes() == (json.dumps(intent, indent=2) + '\n').encode(), 'prepared_intent_changed')
            execution_guard(site, intent)
            journal = Journal(args.report)
            if args.report.exists():
                require(json.loads(args.report.read_text()).get('state') == 'verified_not_submitted', 'local_prior_attempt_blocks_replay')
            # The command already performed a fresh full scan. Recheck exact source
            # after that scan and immediately before the sole POST.
            require(public_api(f'repos/{REPO}/git/ref/heads/{site["branch"]}')['object']['sha'] == site['revision'], 'source_changed_after_scan')
            result = submit(site, urls, journal, transport=request, run_url=f'https://github.com/{REPO}/actions/runs/{os.environ["GITHUB_RUN_ID"]}')
            report.update(result)
        else:
            with args.intent.open('x') as output:
                output.write(json.dumps(intent, indent=2) + '\n'); output.flush(); os.fsync(output.fileno())
            region = site['siteKey'].split('-')[0]
            if os.environ.get('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
                    output.write('intent_name=indexnow-intent-' + region + '-' + sha(canonical(intent)) + '\n')
        report['searchIndexing'] = 'not_verified'
    except Exception as error:
        if args.report.exists():
            saved = json.loads(args.report.read_text())
            if saved.get('state') in ('started', 'unknown', 'rejected', 'received', 'received_key_validation_pending'): report.update(saved)
        report['completionState'] = 'blocked_or_failed'
        report['reason'] = str(error) if type(error) is ValueError and re.fullmatch('[a-z0-9_]+', str(error)) else type(error).__name__
        atomic_json(args.report, report); print(json.dumps(report)); return 1
    atomic_json(args.report, report); print(json.dumps(report)); return 0

def main():
    return run_cli()

if __name__ == '__main__': raise SystemExit(main())
