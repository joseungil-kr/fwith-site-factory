#!/usr/bin/env python3
"""One fixed Uijeongbu static release. No registry, queue or orchestration.

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
BRANCH = 'site-factory-uijeongbu-direct'
SOURCE_ROOT = 'site-factory/uijeongbu-flower'
HOSTNAME = 'uijeongbu.fwith.kr'
ORIGIN = 'https://' + HOSTNAME
WORKER = 'uijeongbu-flower-guide'
RECEIPT_ISSUE = 266
SLUGS = ['uijeongbu-dong', 'howon-dong', 'jangam-dong', 'singok-dong', 'yonghyeon-dong', 'millak-dong', 'nakyang-dong', 'jail-dong', 'geumo-dong', 'ganeung-dong', 'nogyang-dong', 'gosan-dong', 'sangok-dong']
REGION_ROUTES = {'/regions/' + slug + '/' for slug in SLUGS}
ADDED_ROUTES = set()
ARTICLE_ROUTES = REGION_ROUTES
THIN_HUB_ROUTES = set()
SITEMAP_ROUTES = {'/', '/regions/'} | ARTICLE_ROUTES
ROUTES = SITEMAP_ROUTES


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
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def revision():
    value = os.environ.get('REVISION', '')
    require(re.fullmatch(r'[0-9a-f]{40}', value), 'full_revision_required')
    return value


def inventory(root):
    require(root.is_dir() and not root.is_symlink(), 'invalid_artifact_root')
    files = {}
    for path in sorted(root.rglob('*')):
        mode = path.lstat().st_mode
        require(stat.S_ISDIR(mode) or stat.S_ISREG(mode), 'unsafe_artifact_type')
        rel = path.relative_to(root)
        require(not any(part.startswith('.') for part in rel.parts), 'hidden_artifact_path')
        require(path.name not in {'_worker.js', '_routes.json', '_redirects', 'package.json', 'package-lock.json'}
                and not path.name.startswith('wrangler.'), 'executable_artifact_forbidden')
        if path.is_file():
            files[rel.as_posix()] = sha(path.read_bytes())
    require({'index.html', 'regions/index.html', '404.html', '_headers', 'robots.txt', 'sitemap-index.xml'} <= set(files), 'required_artifact_missing')
    return files


def identity():
    require(os.environ.get('GITHUB_REPOSITORY') == REPOSITORY, 'repository_mismatch')
    return dict(schemaVersion=1, repository=REPOSITORY, sourceBranch=BRANCH, sourceRoot=SOURCE_ROOT,
                revision=revision(), controlRevision=os.environ['GITHUB_SHA'], runId=os.environ['GITHUB_RUN_ID'],
                origin=ORIGIN, worker=WORKER, indexable=True)


def package(source):
    files = inventory(source / 'dist')
    release = Path('release')
    release.mkdir()
    shutil.copytree(source / 'dist', release / 'dist')
    manifest = dict(**identity(), files=files)
    save(release / 'release.json', manifest)
    digest = sha((release / 'release.json').read_bytes())
    with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
        out.write('release_sha256=' + digest + '\n')
    return dict(state='packaged', files=len(files), revision=revision(), releaseSha256=digest)


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


def artifact():
    release = Path('release'); root = release / 'dist'
    require({p.name for p in release.iterdir()} == {'dist', 'release.json'}, 'unexpected_release_files')
    raw = (release / 'release.json').read_bytes()
    require(sha(raw) == os.environ.get('RELEASE_SHA256'), 'manifest_digest_mismatch')
    manifest = json.loads(raw)
    require(manifest == dict(**identity(), files=inventory(root)), 'artifact_identity_or_digest_mismatch')
    files = manifest['files']; pages = []; assets = set()
    expected_files = {'404.html'} | {route.lstrip('/') + 'index.html' for route in ROUTES}
    require({p for p in files if p.endswith('.html')} == expected_files, 'exact_reviewed_routes_mismatch')
    for file in sorted(expected_files):
        p = Page((root / file).read_text())
        require(p.meta.get('site-factory-revision') == revision(), 'revision_mismatch')
        require(len(p.canon) == (0 if file == '404.html' else 1), 'canonical_count')
        route = '/' if file == 'index.html' else '/' + file.removesuffix('index.html')
        robots = expected_robots('/404.html' if file == '404.html' else route)
        require(set(re.split(r'\s*,\s*', p.meta.get('robots', '').lower())) == robots, 'robots_meta_mismatch')
        if file != '404.html':
            require(local_path(p.canon[0]) == route and route in ROUTES, 'canonical_mismatch')
            require('tel:18440644' in p.links and 'https://fwith.co.kr' in p.links, 'cta_mismatch')
            require((p.images or route == '/regions/') and all(i.get('alt', '').strip() for i in p.images), 'image_alt_missing')
            for href in p.links:
                if href.startswith('/') or href.startswith(ORIGIN):
                    path = urlsplit(href).path
                    require(path not in DEFERRED, 'deferred_link_published')
                    if not urlsplit(href).fragment and path.endswith('/'):
                        require(path in ROUTES, 'broken_internal_route')
            pages.append(dict(file=file, path=route, url=p.canon[0], robots=sorted(robots)))
        for asset in p.assets:
            require(asset.startswith('/') and not asset.startswith('//'), 'nonlocal_page_asset')
            path = local_path(ORIGIN + asset)
            require(path.lstrip('/') in files, 'referenced_asset_missing')
            assets.add(path)
    robots = [x.strip() for x in (root / 'robots.txt').read_text().splitlines() if x.strip() and not x.strip().startswith('#')]
    require(robots == ['User-agent: *', 'Allow: /', 'Sitemap: ' + ORIGIN + '/sitemap-index.xml'], 'robots_not_indexable')
    require(not re.search(r'^\s*X-Robots-Tag:.*\b(noindex|nofollow|none)\b', (root / '_headers').read_text(), re.I | re.M), 'blocking_response_header')
    index = ET.fromstring((root / 'sitemap-index.xml').read_bytes())
    require(index.tag.split('}')[-1] == 'sitemapindex', 'wrong_sitemap_root')
    maps = [local_path(n.text) for n in index.iter() if n.tag.split('}')[-1] == 'loc']
    require(maps and len(maps) == len(set(maps)), 'sitemap_index_invalid')
    urls = []
    for path in maps:
        require(path.lstrip('/') in files, 'sitemap_missing')
        doc = ET.fromstring((root / path.lstrip('/')).read_bytes())
        require(doc.tag.split('}')[-1] == 'urlset', 'wrong_sitemap_kind')
        urls.extend(n.text for n in doc.iter() if n.tag.split('}')[-1] == 'loc')
    require(len(urls) == len(set(urls)) and {local_path(u) for u in urls} == SITEMAP_ROUTES, 'sitemap_exact_reviewed_urls_mismatch')
    ownership = [p for p in root.glob('*.txt') if re.fullmatch(r'[A-Za-z0-9-]{8,128}', p.stem)
                 and p.read_text().strip() == p.stem]
    require(len(ownership) == 1, 'ownership_file_missing_or_ambiguous')
    for parent in [release.resolve(), *release.resolve().parents]:
        require(not (parent / '.wrangler/deploy/config.json').exists(), 'wrangler_config_redirect')
    save('http-contract.json', dict(origin=ORIGIN, revision=revision(), pages=pages, assets=sorted(assets),
                                   sitemaps=['/sitemap-index.xml', *maps], sitemapUrls=sorted(urls), ownershipFile=ownership[0].name, files=files))
    save(release / 'wrangler.publish.json', dict(name=WORKER, compatibility_date='2026-10-09', workers_dev=False,
         assets=dict(directory='./dist/', not_found_handling='404-page', html_handling='auto-trailing-slash')))
    return dict(state='artifact_verified', revision=revision(), files=len(files), regionCount=len(REGION_ROUTES), articleCount=len(ARTICLE_ROUTES),
                htmlRoutes=len(ROUTES), noindexHubs=len(THIN_HUB_ROUTES), sitemapUrls=len(urls))


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
        require(not matches and not exists, 'initial_target_must_be_absent')
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
    req = Request(ORIGIN + quote(path, safe='/%-._~'), headers={'User-Agent': 'Uijeongbu-Direct-Release-QA/1.0',
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
        require('tel:18440644' in p.links and 'https://fwith.co.kr' in p.links, 'live_cta_mismatch')
        if sha(body) != contract['files'][item['file']]:
            body = strip_one_cf_beacon(body, contract['files'][item['file']]); normalized += 1
        require(sha(body) == contract['files'][item['file']], 'live_html_digest_mismatch')
        checked += 1
    for path in ['/robots.txt', '/' + contract['ownershipFile'], *contract['sitemaps'], *contract['assets']]:
        body, headers = get(path)
        require(sha(body) == contract['files'][path.lstrip('/')], 'live_asset_digest_mismatch')
        if path.startswith('/images/'):
            require(headers.get('Content-Type', '').lower().startswith('image/'), 'image_content_type')
        checked += 1
    for path in [*DEFERRED, '/.direct-release-missing-' + revision() + '/']:
        body, headers = get(path, 404)
        p = Page(body.decode('utf-8'))
        require(p.meta.get('site-factory-revision') == revision() and 'noindex' in p.meta.get('robots', ''), 'live_404_metadata_mismatch')
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


def indexnow():
    helpers()
    from indexnow_finalize import finalize, Journal
    c = json.loads(Path('http-contract.json').read_text())
    key = (Path('release/dist') / c['ownershipFile']).read_text().strip()
    site = dict(siteKey='uijeongbu-flower-direct', siteUrl=ORIGIN, productionEnabled=True, launchMode='live', indexnowKey=key)
    result = finalize(site, revision(), Path('release'), Journal(REPOSITORY, RECEIPT_ISSUE),
                      run_url='https://github.com/' + REPOSITORY + '/actions/runs/' + os.environ['GITHUB_RUN_ID'])
    result['searchIndexing'] = 'not_verified'
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['package', 'artifact', 'preflight', 'attach', 'readback', 'http', 'indexnow'])
    p.add_argument('--source', type=Path)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    try:
        if args.mode == 'package': result = package(args.source)
        elif args.mode == 'artifact': result = artifact()
        elif args.mode in ('preflight', 'attach', 'readback'): result = provider(args.mode)
        elif args.mode == 'http': result = public_http()
        else: result = indexnow()
        save(args.report, result)
        print(json.dumps({k: v for k, v in result.items() if k not in ('urls', 'files')}, sort_keys=True))
        return 0
    except Exception as error:
        code = str(error) if type(error) is ValueError and re.fullmatch('[a-z0-9_]+', str(error)) else getattr(error, 'code', type(error).__name__)
        if not isinstance(code, (str, int)) or not re.fullmatch('[A-Za-z0-9_]+', str(code)):
            code = type(error).__name__
        result = dict(state='blocked_or_failed', mode=args.mode, code=code)
        save(args.report, result); print(json.dumps(result)); return 1


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

if __name__ == '__main__':
    raise SystemExit(main())
