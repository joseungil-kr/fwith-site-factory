#!/usr/bin/env python3
"""One fixed SeoulSeocho static release. No registry, queue or orchestration.

Reuses the existing native Custom Domains no-override operation and the standalone
IndexNow receipt function. Source code never runs with provider credentials.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import time
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
import xml.etree.ElementTree as ET

REPOSITORY = 'joseungil-kr/fwith-site-factory'
BRANCH = 'source/seoul-seocho-production-successor-20261014'
SOURCE_ROOT = 'site-factory/seoul-seocho-flower'
HOSTNAME = 'seoul-seocho.fwith.kr'
ORIGIN = 'https://' + HOSTNAME
WORKER = 'seoul-seocho-flower-guide'
RECEIPT_ISSUE = 266
SLUGS = ['seocho-celebration-wreath', 'seocho-funeral-wreath']
DEFERRED_SLUGS = set()
REGION_ROUTES = {'/regions/' + slug + '/' for slug in SLUGS}
ARTICLE_ROUTES = REGION_ROUTES
THIN_HUB_ROUTES = {'/regions/'}
SITEMAP_ROUTES = {'/'} | ARTICLE_ROUTES
ROUTES = SITEMAP_ROUTES | THIN_HUB_ROUTES
import production_build as gate
import production_output as output


def expected_robots(route):
    if route == '/404.html':
        return {'noindex', 'nofollow', 'noarchive'}
    return {'noindex', 'follow'} if route in THIN_HUB_ROUTES else {'index', 'follow'}

DEFERRED = []
LIMIT = 20 * 1024 * 1024


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def revision():
    value = os.environ.get('REVISION', '')
    require(re.fullmatch(r'[0-9a-f]{40}', value), 'full_revision_required')
    return value


def local_path(url):
    u = urlsplit(url)
    require(u.scheme == 'https' and u.netloc == HOSTNAME and not u.query and not u.fragment, 'foreign_canonical_or_asset')
    path = unquote(u.path)
    require(path.startswith('/') and not any(x in ('.', '..') for x in path.split('/'))
            and '//' not in path and '\\' not in path and not any(ord(c) < 32 for c in path), 'unsafe_path')
    return path


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.meta, self.canon, self.links, self.assets, self.images = {}, [], [], set(), []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('name'):
            key = a['name'].lower()
            require(key not in self.meta, 'duplicate_metadata')
            self.meta[key] = a.get('content', '')
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split():
            self.canon.append(a.get('href', ''))
        if tag == 'a':
            self.links.append(a.get('href', ''))
        if tag == 'img':
            self.images.append(a)
        if tag in ('img', 'script', 'source') and a.get('src'):
            self.assets.add(a['src'])
        if tag == 'link' and any(r in a.get('rel', '').split() for r in ('stylesheet', 'icon', 'preload', 'modulepreload')) and a.get('href'):
            self.assets.add(a['href'])


def release_review():
    root = Path(__file__).resolve().parents[2]
    descriptor = json.loads(gate.read(Path(__file__).with_name('production-release-review-binding.json')))
    def evidence(path, digest):
        require(isinstance(path, str) and path.startswith('docs/direct-seoul-seocho/') and '..' not in Path(path).parts
                and not Path(path).is_absolute() and '\\' not in path, 'review_path_invalid')
        raw = gate.read(root / path)
        require(re.fullmatch('[0-9a-f]{64}', digest or '') and sha(raw) == digest, 'review_digest_mismatch')
        return json.loads(raw)
    require(descriptor.get('schemaVersion') == 1, 'review_descriptor_invalid')
    review = evidence(descriptor.get('path'), descriptor.get('sha256'))
    contract,binding,binding_sha = gate.load()
    required = dict(region='seoul-seocho', sourceCommit=contract['expectedSourceRevision'],
                    bindingSha256=binding_sha, sourceContractSha256=binding['sourceContractSha256'],
                    allRouteOutputVerified=True, nativeTestsPassed=True,
                    mobileAndDesktopPixelsVerified=True, publicHttpVerified=False)
    require(all(review.get(k) == v for k,v in required.items()), 'review_identity_or_required_checks_mismatch')
    require(review.get('verdict') == 'PASS_SEOCHO_PRODUCTION_ARTIFACT_REVIEW' and isinstance(review.get('reviewer'),str)
            and review['reviewer'].strip(), 'independent_manual_review_required')
    for field in ['buildRunId','artifactId','qaRunId']:
        require(re.fullmatch('[1-9][0-9]*',str(review.get(field,''))), 'actual_run_artifact_binding_required')
    for field in ['outputFilesSha256','releaseManifestSha256']:
        require(re.fullmatch('[0-9a-f]{64}',review.get(field,'')), 'actual_output_binding_required')
    require(re.fullmatch('[0-9a-f]{40}',review.get('buildControlSha','')), 'build_control_binding_required')
    rows=review.get('evidence',[])
    require({r.get('kind') for r in rows} >= {'all-route-output','mobile-pixels','desktop-pixels'}, 'manual_review_evidence_missing')
    for row in rows: evidence(row.get('path'),row.get('sha256'))
    return review


def artifact():
    contract,binding,binding_sha = gate.load(); review = release_review()
    require(revision() == contract['expectedSourceRevision'], 'source_revision_mismatch')
    release=Path('release'); root=release/'dist'
    require({p.name for p in release.iterdir()} in ({'dist','release.json'},{'dist','release.json','wrangler.publish.json'}), 'unexpected_release_files')
    raw=gate.read(release/'release.json'); manifest=json.loads(raw); files=gate.inventory(root)
    require(sha(raw)==review['releaseManifestSha256'], 'reviewed_manifest_digest_mismatch')
    expected=dict(schemaVersion=1,repository=REPOSITORY,sourceBranch=BRANCH,sourceRoot=SOURCE_ROOT,
                  revision=revision(),controlRevision=review['buildControlSha'],runId=str(review['buildRunId']),
                  origin=ORIGIN,worker=WORKER,indexable=True,bindingSha256=binding_sha,
                  sourceContractSha256=binding['sourceContractSha256'],files=files)
    require(manifest==expected, 'artifact_identity_or_files_mismatch')
    require(sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode())==review['outputFilesSha256'], 'reviewed_output_digest_mismatch')
    facts=output.inspect_dist(root,dict(mode='production',indexable=True,origin=ORIGIN,revision=revision()),binding['proof'])
    pages=[]; assets=set()
    for file,route in output.FILES.items():
        p=Page(gate.read(root/file).decode('utf-8'))
        if route!='/404.html':
            require('tel:1844-0644' in p.links and 'https://fwith.co.kr/' in p.links,'cta_mismatch')
            require(all(i.get('alt','').strip() for i in p.images),'image_alt_missing')
            for href in p.links:
                if href.startswith('/') or href.startswith(ORIGIN):
                    target=urlsplit(href).path
                    if not urlsplit(href).fragment and target.endswith('/'):
                        require(target in ROUTES,'broken_internal_route')
            pages.append(dict(file=file,path=route,url=ORIGIN+route,robots=sorted(expected_robots(route))))
        for asset in p.assets:
            require(asset.startswith('/') and not asset.startswith('//'),'nonlocal_page_asset')
            path=local_path(ORIGIN+asset);require(path.lstrip('/') in files,'referenced_asset_missing');assets.add(path)
    for parent in [release.resolve(),*release.resolve().parents]:
        require(not (parent/'.wrangler/deploy/config.json').exists(),'wrangler_config_redirect')
    maps=sorted('/'+name for name in files if name.endswith('.xml'))
    save('http-contract.json',dict(origin=ORIGIN,revision=revision(),pages=pages,assets=sorted(assets),
        sitemaps=maps,sitemapUrls=sorted(facts['sitemapUrls']),ownershipFile=binding['proof']['path'].lstrip('/'),files=files))
    save(release/'wrangler.publish.json',dict(name=WORKER,compatibility_date='2026-10-09',workers_dev=False,
        assets=dict(directory='./dist/',not_found_handling='404-page',html_handling='auto-trailing-slash')))
    return dict(state='reviewed_production_artifact_verified',revision=revision(),htmlFiles=5,sitemapUrls=3,
                noindexHubs=1,files=len(files),buildRunId=review['buildRunId'],artifactId=review['artifactId'],
                qaRunId=review['qaRunId'],publicHttpVerified=False)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def helpers():
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'site-factory/engine'))
    import bucheon_domain_attach as native
    from goyang_domain import single_page
    native.HOSTNAME, native.WORKER, native.ZONE_NAME = HOSTNAME, WORKER, 'fwith.kr'
    return native, single_page


def provider_transport():
    account = os.environ.get('CLOUDFLARE_ACCOUNT_ID', '')
    token = os.environ.get('CLOUDFLARE_API_TOKEN', '')
    require(re.fullmatch('[0-9a-fA-F]{32}', account) and token, 'missing_provider_configuration')
    prefix = '/accounts/' + account
    reads = {prefix, prefix + '/workers/scripts', prefix + '/workers/domains'}
    write = prefix + '/workers/scripts/' + WORKER + '/domains/records'
    opener = build_opener(NoRedirect())
    def transport(method, path, body=None):
        require((method == 'GET' and path in reads and body is None) or (method == 'PUT' and path == write
                and body == dict(override_scope=False, override_existing_origin=False, override_existing_dns_record=False,
                                 origins=[dict(hostname=HOSTNAME, zone_name='fwith.kr')])), 'provider_operation_forbidden')
        req = Request('https://api.cloudflare.com/client/v4' + path, method=method,
                      data=None if body is None else json.dumps(body).encode(),
                      headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        transport.last_http_status = None
        with opener.open(req, timeout=25) as response:
            transport.last_http_status = response.status
            raw = response.read(1024 * 1024 + 1)
        require(len(raw) <= 1024 * 1024, 'provider_response_limit')
        value = json.loads(raw)
        require(transport.last_http_status == 200 and value.get('success') is True
                and value.get('errors') in ([], None), 'provider_response_unverified')
        return value
    transport.last_http_status = None
    return account, transport


def inspect_provider(account, transport, stage):
    _, single_page = helpers()
    prefix = '/accounts/' + account
    p = transport('GET', prefix)
    require(isinstance(p.get('result'), dict) and p['result'].get('id') == account, 'account_identity_mismatch')
    scripts = single_page(transport, prefix + '/workers/scripts')
    names = [r.get('id') for r in scripts]
    require(all(isinstance(x, str) and x for x in names) and len(names) == len(set(names)), 'script_inventory_unverified')
    domains = single_page(transport, prefix + '/workers/domains')
    require(all(isinstance(r.get('hostname'), str) and r['hostname'] and isinstance(r.get('service'), str) and r['service'] for r in domains), 'domain_inventory_unverified')
    matches = [r for r in domains if r['hostname'].lower() == HOSTNAME or r['service'] == WORKER]
    bound = len(matches) == 1 and matches[0]['hostname'].lower() == HOSTNAME and matches[0]['service'] == WORKER
    require(not matches or bound, 'hostname_or_worker_collision')
    exists = WORKER in names
    require(not bound or exists, 'binding_without_worker')
    if stage == 'preflight':
        require(bound or not exists, 'unbound_existing_worker_requires_review')
    else:
        require(exists, 'deployed_worker_not_observed')
    if stage == 'readback':
        require(bound, 'exact_binding_not_observed')
    return dict(state='binding_verified' if bound else 'target_absent_verified' if not exists else 'uploaded_worker_verified',
                accountVerified=True, workerExists=exists, hostnameBindingExists=bound,
                hostname=HOSTNAME, worker=WORKER, dnsState='not_observed', mutationsPerformed=False)


def provider(mode):
    native, _ = helpers(); account, transport = provider_transport()
    result = inspect_provider(account, transport, mode)
    if mode == 'attach' and not result['hostnameBindingExists']:
        before = json.loads(Path('binding-before.json').read_text())
        require(before.get('state') == 'target_absent_verified' and before.get('hostname') == HOSTNAME
                and before.get('worker') == WORKER, 'initial_preflight_required')
        native.attach(transport, account)
        result = dict(state='attach_request_accepted', hostname=HOSTNAME, worker=WORKER,
                      mutationsPerformed=True, liveVerification='pending')
    return result


def get(path, status=200):
    req = Request(ORIGIN + quote(path, safe='/%-._~'), headers={'User-Agent': 'SeoulSeocho-Direct-Release-QA/1.0',
                  'Accept-Encoding': 'identity', 'Cache-Control': 'no-cache'})
    try:
        response = build_opener(NoRedirect()).open(req, timeout=20)
    except HTTPError as error:
        response = error
    with response:
        require(response.code == status, 'http_status_' + str(response.code))
        body = response.read(LIMIT + 1)
        require(len(body) <= LIMIT, 'http_response_limit')
        return body, response.headers


def http_once(contract):
    checked = 0; normalized = 0
    require(len(contract['pages']) == len(ROUTES) and {item['path'] for item in contract['pages']} == ROUTES,
            'http_contract_routes_mismatch')
    require(len(contract['sitemapUrls']) == len(SITEMAP_ROUTES) and
            {local_path(url) for url in contract['sitemapUrls']} == SITEMAP_ROUTES, 'http_contract_sitemap_mismatch')
    for item in contract['pages']:
        body, headers = get(item['path'])
        require(headers.get('Content-Type', '').lower().startswith('text/html'), 'html_content_type')
        p = Page(body.decode('utf-8'))
        require(p.meta.get('site-factory-revision') == revision() and p.canon == [item['url']], 'live_revision_or_canonical_mismatch')
        require(set(item['robots']) == expected_robots(item['path']) and
                set(re.split(r'\s*,\s*', p.meta.get('robots', '').lower())) == expected_robots(item['path']), 'live_meta_robots_mismatch')
        require(not re.search(r'\b(noindex|nofollow|none)\b', ','.join(headers.get_all('X-Robots-Tag', [])), re.I), 'live_header_not_indexable')
        require('tel:1844-0644' in p.links and 'https://fwith.co.kr/' in p.links, 'live_cta_mismatch')
        if sha(body) != contract['files'][item['file']]:
            body = strip_one_cf_beacon(body, contract['files'][item['file']]); normalized += 1
        require(sha(body) == contract['files'][item['file']], 'live_html_digest_mismatch')
        checked += 1
    for path in sorted('/' + name for name in contract['files'] if not name.endswith('.html') and name != '_headers'):
        body, headers = get(path)
        require(sha(body) == contract['files'][path.lstrip('/')], 'live_asset_digest_mismatch')
        if path.startswith('/images/'):
            require(headers.get('Content-Type', '').lower().startswith('image/'), 'image_content_type')
        checked += 1
    for path in [*DEFERRED, '/.direct-release-missing-' + revision() + '/']:
        body, headers = get(path, 404)
        p = Page(body.decode('utf-8'))
        require(headers.get('Content-Type','').lower().startswith('text/html') and p.meta.get('site-factory-revision') == revision() and p.canon == [] and set(re.split(r'\s*,\s*', p.meta.get('robots','').lower())) == expected_robots('/404.html'), 'live_404_metadata_mismatch')
        if sha(body) != contract['files']['404.html']:
            body = strip_one_cf_beacon(body, contract['files']['404.html']); normalized += 1
        require(sha(body) == contract['files']['404.html'], 'live_404_digest_mismatch')
        checked += 1
    return dict(state='public_release_verified', revision=revision(), regionCount=len(REGION_ROUTES), articleCount=len(ARTICLE_ROUTES), htmlRoutes=len(ROUTES),
                noindexHubs=len(THIN_HUB_ROUTES), sitemapUrls=len(SITEMAP_ROUTES),
                checkedPaths=checked, normalizedCloudflareBeacons=normalized, unknownHttpStatus=404)


def public_http():
    c = json.loads(Path('http-contract.json').read_text()); last = None
    for attempt in range(1, 13):
        try:
            return dict(http_once(c), attempts=attempt)
        except Exception as error:
            last = error
            if attempt < 12:
                time.sleep(5)
    raise last


def indexnow_site():
    c = json.loads(Path('http-contract.json').read_text())
    key = (Path('release/dist') / c['ownershipFile']).read_text().strip()
    return dict(siteKey='seoul-seocho-flower-direct', siteUrl=ORIGIN, productionEnabled=True, launchMode='live', indexnowKey=key)


def observed_indexnow_request(method, url, payload=None):
    from indexnow_finalize import request, ENDPOINT
    require((method == 'GET' and url.startswith(ORIGIN + '/') and payload is None)
            or (method == 'POST' and url == ENDPOINT), 'indexnow_observation_scope_mismatch')
    path = Path('indexnow-http-observations.json')
    previous = json.loads(path.read_text()) if path.exists() else []
    redacted_url = ORIGIN + '/[ownership-proof]' if re.fullmatch(r'/[A-Za-z0-9-]{8,128}[.]txt', urlsplit(url).path) else url
    record = dict(method=method, url=redacted_url, userAgent='SiteFactory-IndexNow/2.0', observedAt=int(time.time()))
    try:
        status, body, headers = request(method, url, payload)
        record.update(httpStatus=status, contentType=headers.get('content-type', ''),
                      xRobotsTag=headers.get('x-robots-tag', ''),
                      cfMitigated=headers.get('cf-mitigated', ''),
                      bodySha256=sha(body.encode('utf-8')))
        save(path, previous + [record])
        return status, body, headers
    except Exception as error:
        record.update(httpStatus=None, errorType=type(error).__name__)
        save(path, previous + [record])
        raise


def indexnow_probe():
    helpers()
    from indexnow_finalize import verify_public
    urls = verify_public(indexnow_site(), revision(), Path('release'),
                         lambda url: observed_indexnow_request('GET', url))
    return dict(state='indexnow_get_preflight_verified', revision=revision(),
                sitemapUrls=len(urls), mutationsPerformed=False, submissionAttempted=False)


def indexnow():
    helpers()
    from indexnow_finalize import finalize, Journal
    result = finalize(indexnow_site(), revision(), Path('release'), Journal(REPOSITORY, RECEIPT_ISSUE),
                      transport=observed_indexnow_request,
                      run_url='https://github.com/' + REPOSITORY + '/actions/runs/' + os.environ['GITHUB_RUN_ID'])
    result['searchIndexing'] = 'not_verified'
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['select','artifact','preflight','attach','readback','http','indexnow-probe','indexnow'])
    p.add_argument('--report',type=Path,required=True);args=p.parse_args()
    try:
        contract,binding,binding_sha=gate.load()
        gate.authorize(contract,binding_sha,os.environ,json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text()),'publish')
        require(revision()==contract['expectedSourceRevision'],'source_revision_mismatch')
        review=release_review()
        if args.mode=='select':
            result=dict(state='reviewed_release_selected',buildRunId=review['buildRunId'],artifactId=review['artifactId'],revision=revision())
            with open(os.environ['GITHUB_OUTPUT'],'a') as f:
                f.write('build_run_id='+str(review['buildRunId'])+'\nartifact_id='+str(review['artifactId'])+'\n')
        else:
            artifact_result=artifact()
            if args.mode=='artifact':result=artifact_result
            elif args.mode in ('preflight','attach','readback'):result=provider(args.mode)
            elif args.mode=='http':result=public_http()
            elif args.mode=='indexnow-probe':result=indexnow_probe()
            else:
                public_http()
                result=indexnow()
        save(args.report,result);print(json.dumps({k:v for k,v in result.items() if k not in ('urls','files')},sort_keys=True));return 0
    except Exception as error:
        code=str(error) if type(error) is ValueError and re.fullmatch('[a-z0-9_]+',str(error)) else type(error).__name__
        result=dict(state='blocked_or_failed',mode=args.mode,code=code);save(args.report,result);print(json.dumps(result));return 1


def strip_one_cf_beacon(body,expected_sha):
    # Latin-1 is lossless here: parser offsets remain exact byte offsets.
    text=body.decode('latin-1'); starts=[0]+[m.end() for m in re.finditer('\n',text)]
    class Beacon(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False); self.pending=None; self.spans=[]; self.markers=0
        def source_offset(self):
            line,column=self.getpos(); return starts[line-1]+column
        def handle_starttag(self,tag,attrs):
            if tag!='script': return
            values=dict(attrs); src=values.get('src') or ''; u=urlsplit(src)
            marker='data-cf-beacon' in values or u.hostname=='static.cloudflareinsights.com'
            if not marker: return
            self.markers+=1
            assert self.markers==1 and self.pending is None, 'multiple_404_beacon_markers'
            assert len(values)==len(attrs), 'duplicate_404_beacon_attributes'
            assert set(values)<={'src','defer','async','integrity','crossorigin','data-cf-beacon','type'}, 'unexpected_404_beacon_attribute'
            assert values.get('type') in (None,'','module'), 'wrong_404_beacon_type'
            assert 'data-cf-beacon' in values and u.scheme=='https' and u.netloc=='static.cloudflareinsights.com', 'wrong_404_beacon_identity'
            assert re.fullmatch(r'/beacon[.]min[.]js(?:/[A-Za-z0-9]+)?',u.path) and not u.query and not u.fragment, 'wrong_404_beacon_path'
            start=self.source_offset(); self.pending=(start,start+len(self.get_starttag_text()))
        def handle_startendtag(self,tag,attrs):
            self.handle_starttag(tag,attrs)
            assert self.pending is None, 'self_closing_404_beacon'
        def handle_endtag(self,tag):
            if tag!='script' or self.pending is None: return
            start,content_start=self.pending; end_start=self.source_offset()
            closing=re.match(r'</script\s*>',text[end_start:],re.I)
            assert closing and not text[content_start:end_start].strip(), 'nonempty_or_malformed_404_beacon'
            self.spans.append((start,end_start+closing.end())); self.pending=None
    parser=Beacon(); parser.feed(text); parser.close()
    assert parser.markers==1 and len(parser.spans)==1 and parser.pending is None, 'unverified_404_beacon'
    start,end=parser.spans[0]
    candidate=body[:start]+body[end:]
    if hashlib.sha256(candidate).hexdigest()==expected_sha: return candidate
    if body[end:end+1]==b'\n': candidate=body[:start]+body[end+1:]
    assert hashlib.sha256(candidate).hexdigest()==expected_sha, 'wrong_404_body'
    return candidate

if __name__=='__main__':raise SystemExit(main())
