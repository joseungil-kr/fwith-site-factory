#!/usr/bin/env python3
"""One fixed SeoulGwanak static release. No registry, queue or orchestration.

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
BRANCH = 'site-factory-seoul-gwanak-direct'
SOURCE_ROOT = 'site-factory/seoul-gwanak-flower'
HOSTNAME = None  # UNBOUND: no production hostname has been approved or assigned.
ORIGIN = None
LOCAL_PREPARATION_ONLY = False
WORKER = 'seoul-gwanak-flower-guide'
RECEIPT_ISSUE = 266
SLUGS = ['gwanak-funeral-wreath', 'gwanak-celebration-wreath']
DEFERRED_SLUGS = set()
REGION_ROUTES = {'/regions/' + slug + '/' for slug in SLUGS}
ADDED_ROUTES = set()
ARTICLE_ROUTES = REGION_ROUTES
THIN_HUB_ROUTES = {'/regions/'}
SITEMAP_ROUTES = {'/'} | ARTICLE_ROUTES
ROUTES = SITEMAP_ROUTES | THIN_HUB_ROUTES


def expected_robots(route):
    if route == '/404.html':
        return {'noindex', 'nofollow', 'noarchive'}
    return {'noindex', 'follow'} if route in THIN_HUB_ROUTES else {'index', 'follow'}

EXPECTED_ANCHORS = {'/regions/gwanak-funeral-wreath/': ['wooshin-funeral'], '/regions/gwanak-celebration-wreath/': ['snu-faculty', 'snu-research-park', 'nakseongdae-traditional', 'opening-occasion']}
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


def bind_exact_release():
    """No generic host/environment override; only a separately reviewed exact binding.

    This preparation remains locked even if the template is edited. The parent
    must obtain the held approvals and review a new activation diff separately.
    """
    require(not LOCAL_PREPARATION_ONLY, 'local_preparation_release_activation_disabled')
    binding = json.loads(Path(__file__).with_name('publication-binding.json').read_text())
    require(binding['state'] == 'approved', 'release_binding_unbound')
    require(binding['repository'] == REPOSITORY and binding['branch'] == BRANCH
            and binding['sourceRoot'] == SOURCE_ROOT and binding['configuredWorkerTarget'] == WORKER,
            'release_binding_identity_mismatch')
    require(binding['providerExistenceVerified'] is False, 'release_unverified_provider_claim')
    require(binding['sourceRevision'] == revision(), 'release_binding_revision_mismatch')
    require(binding['approvals'] == dict(publication=True, hostBinding=True, indexNowProof=True),
            'release_binding_approval_missing')
    require(set(binding['evidenceReferences']) == {'publication', 'hostBinding', 'indexNowProof'}
            and all(isinstance(v, str) and v.strip() for v in binding['evidenceReferences'].values()),
            'release_binding_evidence_missing')
    hostname = binding['hostname']
    require(isinstance(hostname, str) and re.fullmatch(r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?[.]fwith[.]kr', hostname),
            'release_binding_hostname_missing')
    require(binding['origin'] == 'https://' + hostname, 'release_binding_origin_mismatch')
    contract = Path(__file__).with_name('source-contract.json')
    require(sha(contract.read_bytes()) == binding['sourceContractSha256'], 'release_source_contract_changed')
    global HOSTNAME, ORIGIN
    HOSTNAME, ORIGIN = hostname, binding['origin']
    return binding


def require_reviewed_output():
    """Publishing requires a previously inspected build-only output for this SHA.

    The digest is the canonical file inventory, independent of run IDs. No build
    may approve its own new output by merely generating a fresh release.json.
    """
    binding = bind_exact_release()
    reviewed = binding.get('reviewedBuildOutput', {})
    require(reviewed.get('approved') is True, 'independent_build_output_review_required')
    require(reviewed.get('sourceRevision') == binding['sourceRevision'], 'reviewed_output_source_mismatch')
    require(re.fullmatch(r'[0-9a-f]{64}', reviewed.get('distManifestSha256', '') or ''), 'reviewed_output_digest_required')
    require(isinstance(reviewed.get('artifactId'), int) and reviewed['artifactId'] > 0
            and re.fullmatch(r'https://github[.]com/' + re.escape(REPOSITORY) + r'/actions/runs/[1-9][0-9]*', reviewed.get('buildRunUrl', '') or '')
            and isinstance(reviewed.get('independentReviewEvidence'), str) and reviewed['independentReviewEvidence'].strip(),
            'reviewed_output_evidence_missing')
    files = inventory(Path('release/dist'))
    digest = sha(json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
    require(digest == reviewed['distManifestSha256'], 'rebuilt_output_differs_from_reviewed_artifact')
    return dict(state='independent_build_output_binding_verified', sourceRevision=binding['sourceRevision'], distManifestSha256=digest)


def verify_source_bytes(source, contract, *, phase, bound_revision=None):
    """Prebuild: every tracked byte. Postbuild: exactly one bound writer output.

    No path is globally exempt. Generated metadata is a regular, non-symlink
    tracked file in BOTH phases; postbuild permits only exact writer bytes.
    """
    require(phase in {'prebuild', 'postbuild'}, 'source_phase_required')
    expected = contract['files']
    modes = contract['gitModes']
    require(set(modes) == set(expected) and set(modes.values()) <= {'100644', '100755'}, 'source_mode_contract_mismatch')
    generated = 'src/data/build-revision.json'
    require(generated in expected, 'tracked_generated_revision_missing_from_contract')
    policy = contract['generatedRevisionPolicy']
    require(policy == dict(path=generated, prebuildSha256=expected[generated],
                           postbuildEncoding='JSON.stringify({revision:bound_source_sha},null,2); UTF-8; no trailing newline'),
            'generated_revision_policy_mismatch')
    if phase == 'postbuild':
        require(re.fullmatch(r'[0-9a-f]{40}', bound_revision or ''), 'postbuild_bound_revision_required')
        generated_bytes = json.dumps({'revision': bound_revision}, indent=2).encode('utf-8')
    require(source.is_dir() and not source.is_symlink(), 'unsafe_source_root')
    require({p.name for p in source.iterdir()} <= {p.split('/')[0] for p in expected} | {'node_modules', 'dist', '.astro', 'faq-product-qa.json', 'shared-banner-qa.json', 'directory-spacing-qa.json', 'gwanak-static-qa.json'}, 'unreviewed_source_root_entry')
    for path, digest in expected.items():
        target = source / path
        require(target.is_file() and not target.is_symlink(), 'source_file_missing_or_unsafe')
        require(stat.S_ISREG(target.lstat().st_mode) and stat.S_IMODE(target.lstat().st_mode) == (0o755 if modes[path] == '100755' else 0o644), 'source_file_mode_mismatch')
        require(all(not parent.is_symlink() for parent in target.parents), 'source_parent_symlink')
        actual = target.read_bytes()
        if path == generated and phase == 'postbuild':
            require(actual == generated_bytes, 'postbuild_generated_revision_bytes_mismatch')
        else:
            require(sha(actual) == digest, 'source_file_digest_mismatch')
    # Inspect every entry before filtering files: is_file() alone silently drops
    # dangling and directory symlinks, FIFOs and other non-regular entries.
    for entry in source.iterdir():
        require(not entry.is_symlink(), 'source_root_entry_symlink')
        require(stat.S_ISREG(entry.lstat().st_mode) or stat.S_ISDIR(entry.lstat().st_mode), 'source_special_entry')
    scoped = set()
    for dirname in ['src', 'public', 'scripts', 'tests']:
        for entry in (source / dirname).rglob('*'):
            require(not entry.is_symlink(), 'source_tree_symlink')
            entry_mode = entry.lstat().st_mode
            require(stat.S_ISREG(entry_mode) or stat.S_ISDIR(entry_mode), 'source_special_entry')
            require('__pycache__' not in entry.relative_to(source).parts, 'source_python_cache_forbidden')
            if stat.S_ISREG(entry_mode):
                scoped.add(entry.relative_to(source).as_posix())
    require(scoped == {p for p in expected if p.split('/')[0] in {'src', 'public', 'scripts', 'tests'}},
            'unreviewed_source_file')
    return dict(state='source_bytes_checked_only_no_activation', files=len(expected),
                phase=phase, generatedRevisionException=(generated if phase == 'postbuild' else None))


def source_contract(source, *, phase):
    binding = bind_exact_release()
    contract = json.loads(Path(__file__).with_name('source-contract.json').read_text())
    require(contract['repository'] == REPOSITORY and contract['branch'] == BRANCH
            and contract['root'] == SOURCE_ROOT and contract['origin'] == ORIGIN
            and contract['worker'] == WORKER, 'source_contract_identity_mismatch')
    require(contract['originalPlanN'] == len(SLUGS), 'frozen_plan_mismatch')
    verify_source_bytes(source, contract, phase=phase, bound_revision=binding['sourceRevision'])
    config = json.loads((source / 'src/data/site-config.json').read_text())
    manifest = json.loads((source / 'src/data/publish-manifest.json').read_text())
    require(config['productionApproved'] is True and manifest['directRelease']['publicationAuthorized'] is True,
            'source_publication_not_authorized')
    require(manifest['directRelease']['plannedOriginalCount'] == len(SLUGS)
            and [p['slug'] for p in manifest['pages']] == SLUGS, 'source_fixed_plan_mismatch')
    return dict(state='source_contract_verified', files=len(contract['files']), baselineSourceRevision=contract['baselineSourceRevision'])


def package(source):
    source_contract(source, phase='postbuild')
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
        self.ids = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'): self.ids.append(a['id'])
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
    require(len(ARTICLE_ROUTES) * 10 >= len(SLUGS) * 9, 'minimum_reviewed_coverage_not_met')
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
            require(all(p.ids.count(anchor) == 1 for anchor in EXPECTED_ANCHORS.get(route, [])), 'reviewed_anchor_missing_or_duplicate')
            require('tel:1844-0644' in p.links and 'https://fwith.co.kr/' in p.links, 'cta_mismatch')
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
    require(not LOCAL_PREPARATION_ONLY, 'local_preparation_external_execution_disabled')
    require_reviewed_output()
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
    if bound:
        row = matches[0]
        require('environment' not in row or row['environment'] == 'production', 'nonproduction_binding')
        require('zone_name' not in row or row['zone_name'] == 'fwith.kr', 'binding_zone_mismatch')
        require('enabled' not in row or row['enabled'] is True, 'binding_disabled')
        require('previews_enabled' not in row or row['previews_enabled'] is False, 'unexpected_preview_binding')
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
                hostname=HOSTNAME, worker=WORKER, dnsState='not_observed',
                environment=matches[0].get('environment', 'not_reported') if bound else 'not_observed',
                zoneName=matches[0].get('zone_name', 'not_reported') if bound else 'not_observed', mutationsPerformed=False)


def provider(mode):
    require(not LOCAL_PREPARATION_ONLY, 'local_preparation_external_execution_disabled')
    require_reviewed_output()
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
    require(not LOCAL_PREPARATION_ONLY, 'local_preparation_external_execution_disabled')
    require_reviewed_output()
    req = Request(ORIGIN + quote(path, safe='/%-._~'), headers={'User-Agent': 'SeoulGwanak-Direct-Release-QA/1.0',
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
        require(all(p.ids.count(anchor) == 1 for anchor in EXPECTED_ANCHORS.get(item['path'], [])), 'live_reviewed_anchor_missing_or_duplicate')
        require('tel:1844-0644' in p.links and 'https://fwith.co.kr/' in p.links, 'live_cta_mismatch')
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
    require(not LOCAL_PREPARATION_ONLY, 'local_preparation_external_execution_disabled')
    require_reviewed_output()
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
    return dict(siteKey='seoul-gwanak-flower-direct', siteUrl=ORIGIN, productionEnabled=True, launchMode='live', indexnowKey=key)


def safe_indexnow_response_diagnostic(body):
    """Retain protocol error classes, never arbitrary upstream text or keys."""
    allowed = {'InvalidApiKey', 'InvalidRequest', 'InvalidRequestParameters',
               'InvalidUrl', 'TooManyRequests', 'InternalServerError'}
    result = dict(bodyBytes=len(body.encode('utf-8')), bodyRetained=False)
    try:
        value = json.loads(body)
    except (ValueError, TypeError, RecursionError):
        return dict(result, responseFormat='non_json', protocolErrorCode=None)
    result.update(responseFormat='json', protocolErrorCode=None)
    if isinstance(value, dict):
        candidates = [value.get('code'), value.get('errorCode')]
        if isinstance(value.get('error'), dict):
            candidates.append(value['error'].get('code'))
        result['protocolErrorCode'] = next((v for v in candidates if isinstance(v, str) and v in allowed), None)
    return result


def observed_indexnow_request(method, url, payload=None):
    require(not LOCAL_PREPARATION_ONLY, 'local_preparation_external_execution_disabled')
    require_reviewed_output()
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
        if method == 'POST':
            record['responseDiagnostic'] = safe_indexnow_response_diagnostic(body)
        save(path, previous + [record])
        return status, body, headers
    except Exception as error:
        record.update(httpStatus=None, errorType=type(error).__name__)
        save(path, previous + [record])
        raise


def indexnow_probe():
    require(not LOCAL_PREPARATION_ONLY, 'local_preparation_external_execution_disabled')
    require_reviewed_output()
    helpers()
    from indexnow_finalize import verify_public
    urls = verify_public(indexnow_site(), revision(), Path('release'),
                         lambda url: observed_indexnow_request('GET', url))
    return dict(state='indexnow_get_preflight_verified', revision=revision(),
                sitemapUrls=len(urls), mutationsPerformed=False, submissionAttempted=False)


class DiagnosticReviewJournal:
    """SeoulGwanak-only: a prior 403 for the exact fingerprint needs diagnosis."""
    def __init__(self, journal):
        self.journal = journal

    def records(self):
        return self.journal.records()

    def write(self, record):
        if record.get('state') == 'started':
            # Use the unchanged finalizer's fingerprint; do not approximate its
            # source, sitemap, endpoint or ownership-proof identity here.
            previous = self.journal.records()
            require(not any(row.get('fingerprint') == record.get('fingerprint')
                            and row.get('state') == 'rejected'
                            and row.get('httpStatus') == 403 for row in previous),
                    'indexnow_403_diagnostic_review_required')
        return self.journal.write(record)


def indexnow():
    require(not LOCAL_PREPARATION_ONLY, 'local_preparation_external_execution_disabled')
    require_reviewed_output()
    helpers()
    from indexnow_finalize import finalize, Journal
    result = finalize(indexnow_site(), revision(), Path('release'), DiagnosticReviewJournal(Journal(REPOSITORY, RECEIPT_ISSUE)),
                      transport=observed_indexnow_request,
                      run_url='https://github.com/' + REPOSITORY + '/actions/runs/' + os.environ['GITHUB_RUN_ID'])
    result['searchIndexing'] = 'not_verified'
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['binding', 'source', 'package', 'artifact', 'preflight', 'attach', 'readback', 'http', 'indexnow-probe', 'indexnow'])
    p.add_argument('--source', type=Path)
    p.add_argument('--phase', choices=['prebuild', 'postbuild'])
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    try:
        binding = bind_exact_release()
        if args.mode in {'artifact', 'preflight', 'attach', 'readback', 'http', 'indexnow-probe', 'indexnow'}:
            require_reviewed_output()
        required_phase = {'source': 'prebuild', 'package': 'postbuild'}.get(args.mode)
        require(args.phase == required_phase, 'source_command_phase_mismatch')
        if args.mode == 'binding':
            result = dict(state='exact_release_binding_verified', origin=binding['origin'])
            if os.environ.get('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'], 'a') as output: output.write('origin=' + binding['origin'] + '\n')
        elif args.mode == 'source': result = source_contract(args.source, phase=args.phase)
        elif args.mode == 'package': result = package(args.source)
        elif args.mode == 'artifact': result = artifact()
        elif args.mode in ('preflight', 'attach', 'readback'): result = provider(args.mode)
        elif args.mode == 'http': result = public_http()
        elif args.mode == 'indexnow-probe': result = indexnow_probe()
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




