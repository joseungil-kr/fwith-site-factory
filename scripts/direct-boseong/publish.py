#!/usr/bin/env python3
"""One fixed Boseong static release. No registry, queue or orchestration.

Reuses the existing native Custom Domains no-override operation. IndexNow submission is a separate, disabled phase. Source code never runs with provider credentials.
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
BRANCH = 'source/boseong-production-preparation-20261017'
SOURCE_ROOT = 'site-factory/boseong-flower'
HOSTNAME = 'boseong.fwith.kr'
ORIGIN = 'https://' + HOSTNAME
WORKER = 'boseong-flower-guide'
DIRECTORY = Path(__file__).resolve().parent
TITLE = '[BOSEONG-PRODUCTION-PUBLISH] 20261017'
REGION_ROUTES = {'/'}
ARTICLE_ROUTES = set()
THIN_HUB_ROUTES = set()
SITEMAP_ROUTES = {'/'}
ROUTES = {'/'}
import publication_gate as gate
import production_output as output
import managed_robots


def expected_robots(route):
    if route == '/404.html':
        return {'noindex', 'nofollow'}
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


def validate_fixed_target():
    require((REPOSITORY,BRANCH,SOURCE_ROOT,HOSTNAME,ORIGIN,WORKER) == (
        'joseungil-kr/fwith-site-factory','source/boseong-production-preparation-20261017',
        'site-factory/boseong-flower','boseong.fwith.kr','https://boseong.fwith.kr',
        'boseong-flower-guide'), 'fixed_boseong_target_required')


def purchase_ctas_valid(page, route):
    if 'tel:18440644' not in page.links: return False
    if route == '/': return all('https://fwith.co.kr/shop/item.php?it_id='+sku in page.links for sku in ('B201','B203','B205','B060'))
    return False


def publication_config():
    validate_fixed_target()
    c=json.loads(gate.read(DIRECTORY/'production-publication.json'))
    fixed=dict(schemaVersion=1,repository=REPOSITORY,hostname=HOSTNAME,worker=WORKER,
               mode='publish-and-verify-only',indexNowSubmissionEnabled=False)
    require(type(c) is dict and json.dumps(c,sort_keys=True)==json.dumps(fixed,sort_keys=True), 'publication_config_identity')
    return c


def authorize(contract, binding_sha, env, event):
    # Historical order labels in the frozen source contract are not release dependencies.
    config=publication_config()
    require(env.get('GITHUB_REPOSITORY')==REPOSITORY and env.get('GITHUB_REF')=='refs/heads/main', 'owner_main_required')
    require(env.get('GITHUB_ACTOR')==gate.OWNER and env.get('GITHUB_TRIGGERING_ACTOR')==gate.OWNER
            and env.get('GITHUB_RUN_ATTEMPT')=='1', 'owner_first_attempt_required')
    require(env.get('GITHUB_EVENT_NAME')=='issues' and event.get('action')=='opened', 'opened_issue_required')
    require(re.fullmatch('[0-9a-f]{40}',env.get('GITHUB_SHA','')), 'control_revision_required')
    repo,issue=event.get('repository',{}),event.get('issue',{})
    require(repo.get('full_name')==REPOSITORY and repo.get('owner',{}).get('login')==gate.OWNER
            and repo.get('owner',{}).get('type')=='User','repository_owner_mismatch')
    require(issue.get('title')==TITLE and issue.get('user',{}).get('login')==gate.OWNER, 'exact_issue_required')
    raw=issue.get('body');require(isinstance(raw,str) and len(raw)<2048, 'invalid_body')
    body=json.loads(raw)
    saved_authorization=gate.authorization(contract)
    expected=dict(schemaVersion=1,mode='publish-and-verify-only',source_branch=BRANCH,
        source_revision=contract['sourceRevision'],expected_control_revision=env['GITHUB_SHA'],
        binding_sha256=binding_sha,
        release_review_sha256=sha(gate.read(DIRECTORY/'production-release-review-binding.json')),
        authorization_sha256=saved_authorization['sha256'],authorization_revision=saved_authorization['revision'])
    require(isinstance(body,dict) and json.dumps(body,sort_keys=True)==json.dumps(expected,sort_keys=True), 'exact_request_required')
    return dict(state='exact_production_request_selected',sourceBranch=BRANCH,
                sourceRevision=contract['sourceRevision'],controlRevision=env['GITHUB_SHA'],bindingSha256=binding_sha)


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
        self.meta, self.canon, self.links, self.assets, self.images, self.og_urls = {}, [], [], set(), [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('name'):
            key = a['name'].lower()
            require(key not in self.meta, 'duplicate_metadata')
            self.meta[key] = a.get('content', '')
        if tag == 'meta' and a.get('property') == 'og:url':
            self.og_urls.append(a.get('content', ''))
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
    # Exact recovered bounded verdict plus independently checked actual artifact bindings.
    descriptor=json.loads(gate.read(DIRECTORY/'production-release-review-binding.json'))
    required={'schemaVersion','verdictPath','verdictSha256','nativeActualVerdictSha256','releaseManifestSha256','outputFilesSha256','artifactDigest','artifactId','buildRunId','buildControlSha','sourceCommit','bindingSha256','sourceContractSha256','originalNativeVerdictBytesRecoverable','originalReviewManifestBytesRecoverable'}
    require(type(descriptor)is dict and set(descriptor)==required and descriptor['schemaVersion']==1,'review_recovery_descriptor_schema')
    path=descriptor['verdictPath'];require(path=='production-review-recovery/bounded-VERDICT.json','review_recovery_path_invalid')
    raw=gate.read(DIRECTORY/path);require(sha(raw)==descriptor['verdictSha256']==gate.RECOVERED_VERDICT_SHA256,'recovered_bounded_verdict_hash_mismatch')
    verdict=json.loads(raw)
    require(verdict.get('accepted') is True and verdict.get('blockingFindings')==0 and verdict.get('verdict')=='PASS_BOSEONG_BOUNDED_LAUNCH_GATE','bounded_verdict_not_accepted')
    require(verdict.get('publicHttpVerified') is False and verdict.get('publicationReady') is False and verdict.get('remoteSaved') is False,'bounded_review_scope_overstated')
    contract,binding,binding_sha=gate.load()
    exact={'sourceCommit':contract['sourceRevision'],'bindingSha256':binding_sha,'sourceContractSha256':binding['sourceContractSha256'],'buildRunId':verdict['buildRunId'],'artifactId':verdict['artifactId'],'artifactDigest':verdict['artifactDigest'],'buildControlSha':verdict['buildControlSha']}
    require(all(verdict.get(k)==v for k,v in exact.items()),'bounded_review_binding_mismatch')
    require(all(descriptor.get(k)==v for k,v in exact.items() if k in descriptor),'recovery_descriptor_binding_mismatch')
    require(descriptor['nativeActualVerdictSha256']==verdict['nativeActualVerdictSHA256'],'native_verdict_hash_reference_mismatch')
    require(descriptor['releaseManifestSha256']==gate.RELEASE_MANIFEST_SHA256 and descriptor['outputFilesSha256']==gate.OUTPUT_FILES_SHA256,'actual_output_review_binding_mismatch')
    require(descriptor['artifactDigest']==gate.ARTIFACT_DIGEST and descriptor['artifactId']==gate.ARTIFACT_ID and descriptor['buildRunId']==gate.BUILD_RUN_ID,'actual_archive_review_binding_mismatch')
    require(descriptor['originalNativeVerdictBytesRecoverable'] is False and descriptor['originalReviewManifestBytesRecoverable'] is False,'recovery_limit_must_be_explicit')
    return dict(sourceCommit=contract['sourceRevision'],bindingSha256=binding_sha,sourceContractSha256=binding['sourceContractSha256'],reviewer=verdict['reviewer'],verdict=verdict['verdict'],buildRunId=verdict['buildRunId'],qaRunId=verdict['buildRunId'],artifactId=verdict['artifactId'],outputFilesSha256=descriptor['outputFilesSha256'],releaseManifestSha256=descriptor['releaseManifestSha256'],buildControlSha=verdict['buildControlSha'],artifactDigest=verdict['artifactDigest'],publicHttpVerified=False,publicationReady=False,recoveryProvenance='Exact recovered bounded verdict; native actual verdict bytes and original review manifest are unavailable and are not reconstructed.')


def restore_private_input(release=Path('release')):
    """Restore the exact private11 adapter fixture from the reviewed public15 archive.

    The pinned adapter requires the pre-publication dist as a byte-level input. A fresh
    source checkout may omit that ignored build output, so reconstruct only the original
    private files from the already-retained, digest-bound archive. This reads and writes
    bytes only; it never invokes source code, npm, or the adapter's build path.
    """
    contract,binding,binding_sha=gate.load();review=release_review()
    require(revision()==contract['sourceRevision'],'source_revision_mismatch')
    adapter=output.adapter
    checkout=Path(os.environ.get('BOSEONG_SOURCE_CHECKOUT','source'))
    source=checkout/SOURCE_ROOT
    source=adapter.safe_path(source)
    require(source.is_dir(),'regular_source_root_required')
    source_check=adapter.check_source(source)
    candidate=adapter.safe_path(source/'candidate')
    require(candidate.is_dir(),'regular_candidate_directory_required')
    destination=candidate/'dist'
    require(not destination.is_symlink(),'private_dist_symlink_forbidden')
    if destination.exists():
        # Never overwrite an existing checkout output. Reuse only if the pinned adapter
        # independently proves exact source46/private11 bytes.
        _,_,verified,_=adapter.verify_inputs(source)
        return dict(state='exact_private_inputs_already_present',sourceRevision=revision(),
                    sourceFilesVerified=source_check['verifiedSourceFiles'],privateFilesVerified=11,
                    privateOutputsSha256=sha(json.dumps({n:sha(v) for n,v in sorted(verified.items())},
                        sort_keys=True,separators=(',',':')).encode()))

    release=adapter.safe_path(release)
    release_dist=release/'dist'
    public=adapter.inventory(release_dist)
    public_files={name:sha(raw) for name,raw in sorted(public.items())}
    require(set(public_files)==set(adapter.read_contract()['productionOutputPaths']),'retained_public_output_set_mismatch')
    require(sha(json.dumps(public_files,sort_keys=True,separators=(',',':')).encode())==review['outputFilesSha256'],
            'retained_public_output_digest_mismatch')
    manifest_raw=gate.read(release/'release.json');manifest=json.loads(manifest_raw)
    require(sha(manifest_raw)==review['releaseManifestSha256'],'retained_release_manifest_digest_mismatch')
    expected_manifest=dict(schemaVersion=1,repository=REPOSITORY,sourceBranch=BRANCH,sourceRoot=SOURCE_ROOT,
        revision=revision(),controlRevision=review['buildControlSha'],runId=str(review['buildRunId']),
        origin=ORIGIN,worker=WORKER,indexable=True,bindingSha256=binding_sha,
        sourceContractSha256=binding['sourceContractSha256'],files=public_files)
    require(same_json(manifest,expected_manifest),'retained_release_manifest_binding_mismatch')

    private_expected=adapter.read_contract()['privateOutputs']
    baselines=adapter.read_contract()['htmlBaseline']
    private={}
    for name in sorted(private_expected):
        if name in ('index.html','404.html'):
            raw=public.get(name)
            require(isinstance(raw,bytes) and raw.count(b'<body')==1,'retained_html_body_boundary_invalid')
            body=b'<body'+raw.split(b'<body',1)[1]
            require(sha(body)==baselines[name]['bodySHA256'],'retained_html_body_digest_mismatch')
            private[name]=baselines[name]['prefixUTF8'].encode('utf-8')+body
        elif name=='robots.txt':
            # The public15 projection intentionally rewrites robots.txt. Recover this
            # private build input from the source46 public file after check_source pinned it.
            private[name]=adapter.regular(source/'candidate/public/robots.txt')
        else:
            require(name in public,'retained_private_asset_missing')
            private[name]=public[name]
        row=private_expected[name]
        require(len(private[name])==row['bytes'] and sha(private[name])==row['sha256'],
                'reconstructed_private_file_digest_mismatch')

    temp=candidate/'.boseong-private-dist-restore'
    require(not temp.exists() and not temp.is_symlink(),'private_restore_temp_exists')
    temp.mkdir()
    try:
        for name,raw in private.items():
            target=temp/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        observed=adapter.inventory(temp)
        require(observed==private,'reconstructed_private_inventory_mismatch')
        # Fail closed if anything created the target after the initial absence check.
        require(not destination.exists() and not destination.is_symlink(),'private_dist_appeared_during_restore')
        temp.rename(destination)
    finally:
        if temp.exists(): shutil.rmtree(temp)

    _,_,verified,checked=adapter.verify_inputs(source)
    return dict(state='exact_private_inputs_restored_from_retained_artifact',sourceRevision=revision(),
        sourceFilesVerified=checked['verifiedSourceFiles'],privateFilesVerified=len(verified),
        privateOutputsSha256=sha(json.dumps({n:sha(v) for n,v in sorted(verified.items())},
            sort_keys=True,separators=(',',':')).encode()),retainedArtifactDigest=review['artifactDigest'],
        retainedReleaseManifestSha256=review['releaseManifestSha256'],
        sourceCodeExecuted=False,networkOperations=0)


def artifact():
    contract,binding,binding_sha = gate.load(); review = release_review()
    require(revision() == contract['sourceRevision'], 'source_revision_mismatch')
    release=Path('release'); root=release/'dist'
    require(release.is_dir() and not release.is_symlink() and root.is_dir() and not root.is_symlink(), 'regular_release_directories_required')
    require({p.name for p in release.iterdir()} in ({'dist','release.json'},{'dist','release.json','wrangler.publish.json'}), 'unexpected_release_files')
    facts=output.inspect_dist(root,dict(mode='production',indexable=True,origin=ORIGIN,revision=revision()),binding['proof'])
    raw=gate.read(release/'release.json'); manifest=json.loads(raw); files=facts['files']
    require(sha(raw)==review['releaseManifestSha256'], 'reviewed_manifest_digest_mismatch')
    expected=dict(schemaVersion=1,repository=REPOSITORY,sourceBranch=BRANCH,sourceRoot=SOURCE_ROOT,
                  revision=revision(),controlRevision=review['buildControlSha'],runId=str(review['buildRunId']),
                  origin=ORIGIN,worker=WORKER,indexable=True,bindingSha256=binding_sha,
                  sourceContractSha256=binding['sourceContractSha256'],files=files)
    require(json.dumps(manifest,sort_keys=True)==json.dumps(expected,sort_keys=True), 'artifact_identity_or_files_mismatch')
    require(sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode())==review['outputFilesSha256'], 'reviewed_output_digest_mismatch')
    pages=[]; assets=set()
    for file,route in output.FILES.items():
        p=Page(gate.read(root/file).decode('utf-8'))
        require(p.og_urls == ([] if route == '/404.html' else [ORIGIN+route]), 'artifact_og_url_mismatch')
        if route!='/404.html':
            require(purchase_ctas_valid(p,route),'cta_mismatch')
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
    return dict(state='reviewed_production_artifact_verified',sourceRevision=revision(),
                publisherControlRevision=os.environ.get('GITHUB_SHA'),publisherRunId=os.environ.get('GITHUB_RUN_ID'),
                sourceContractSha256=binding['sourceContractSha256'],bindingSha256=binding_sha,
                htmlFiles=len(output.FILES),sitemapUrls=len(SITEMAP_ROUTES),noindexHubs=0,files=files,
                outputFilesSha256=sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode()),
                releaseManifestSha256=sha(raw),artifactDigest=review['artifactDigest'],
                buildRunId=review['buildRunId'],artifactId=review['artifactId'],qaRunId=review['qaRunId'],publicHttpVerified=False)


def current_release_files():
    root=Path('release/dist')
    require(root.is_dir() and not root.is_symlink(),'regular_release_dist_required')
    files={}
    for item in root.rglob('*'):
        require(not item.is_symlink(),'release_dist_symlink_forbidden')
        require(item.is_dir() or item.is_file(),'release_dist_nonregular_entry')
        if item.is_file():files[item.relative_to(root).as_posix()]=sha(gate.read(item))
    return files


def require_artifact_validation():
    """Credentialed provider phases only recheck the earlier secret-free attestation and bytes.

    The full source adapter is run by the separate `artifact` workflow step before provider
    credentials are introduced. This function never imports or executes source code.
    """
    contract,binding,binding_sha=gate.load();review=release_review()
    report=json.loads(gate.read(Path('artifact-check.json')))
    manifest_raw=gate.read(Path('release/release.json'));manifest=json.loads(manifest_raw)
    files=current_release_files()
    expected_manifest=dict(schemaVersion=1,repository=REPOSITORY,sourceBranch=BRANCH,sourceRoot=SOURCE_ROOT,
       revision=revision(),controlRevision=review['buildControlSha'],runId=str(review['buildRunId']),
       origin=ORIGIN,worker=WORKER,indexable=True,bindingSha256=binding_sha,
       sourceContractSha256=binding['sourceContractSha256'],files=files)
    expected=dict(state='reviewed_production_artifact_verified',sourceRevision=revision(),
       publisherControlRevision=os.environ.get('GITHUB_SHA'),publisherRunId=os.environ.get('GITHUB_RUN_ID'),
       sourceContractSha256=binding['sourceContractSha256'],bindingSha256=binding_sha,
       htmlFiles=len(output.FILES),sitemapUrls=len(SITEMAP_ROUTES),noindexHubs=0,files=files,
       outputFilesSha256=sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode()),
       releaseManifestSha256=sha(manifest_raw),artifactDigest=review['artifactDigest'],
       buildRunId=review['buildRunId'],artifactId=review['artifactId'],qaRunId=review['qaRunId'],publicHttpVerified=False)
    require(same_json(report,expected),'artifact_validation_report_binding_mismatch')
    require(sha(manifest_raw)==review['releaseManifestSha256'] and same_json(manifest,expected_manifest),
       'retained_artifact_changed_after_validation')
    require(sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode())==review['outputFilesSha256'],
       'retained_output_digest_changed_after_validation')
    return dict(state='secret_free_artifact_validation_reused',sourceRevision=contract['sourceRevision'],
       publisherControlRevision=os.environ.get('GITHUB_SHA'),publisherRunId=os.environ.get('GITHUB_RUN_ID'),
       releaseManifestSha256=review['releaseManifestSha256'],outputFilesSha256=review['outputFilesSha256'])


def same_json(a,b):
    return json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def helpers():
    validate_fixed_target()
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'site-factory/engine'))
    import bucheon_domain_attach as native
    from goyang_domain import single_page
    native.HOSTNAME, native.WORKER, native.ZONE_NAME = HOSTNAME, WORKER, 'fwith.kr'
    return native, single_page


def provider_transport():
    validate_fixed_target()
    account = os.environ.get('CLOUDFLARE_ACCOUNT_ID', '')
    token = os.environ.get('CLOUDFLARE_API_TOKEN', '')
    require(re.fullmatch('[0-9a-fA-F]{32}', account) and isinstance(token,str) and token and token == token.strip() and '\n' not in token and '\r' not in token, 'missing_provider_configuration')
    prefix = '/accounts/' + account
    reads = {prefix, prefix + '/workers/scripts', prefix + '/workers/domains'}
    write = prefix + '/workers/scripts/' + WORKER + '/domains/records'
    opener = build_opener(NoRedirect())
    def transport(method, path, body=None):
        validate_fixed_target()
        require((method == 'GET' and path in reads and body is None) or (method == 'PUT' and path == write
                and json.dumps(body,sort_keys=True) == json.dumps(dict(override_scope=False, override_existing_origin=False, override_existing_dns_record=False,
                                 origins=[dict(hostname=HOSTNAME, zone_name='fwith.kr')]),sort_keys=True)), 'provider_operation_forbidden')
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
    validate_fixed_target()
    require(stage in {'preflight','attach','readback'}, 'invalid_provider_stage')
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
    if bound:
        row=matches[0]
        require(row.get('environment','production') == 'production' and row.get('zone_name','fwith.kr') == 'fwith.kr'
                and row.get('enabled',True) is True and row.get('previews_enabled',False) is False, 'binding_configuration_mismatch')
    if stage == 'preflight':
        require(bound or not exists, 'unbound_existing_worker_requires_review')
        # This controller is for Boseong's first publication. Even an exact
        # name match is not proof that an existing deployment belongs to us.
        # Readback remains available after this run's one upload/attach attempt.
        require(not exists and not matches, 'first_publication_target_must_be_absent')
    else:
        require(exists, 'deployed_worker_not_observed')
    if stage == 'readback':
        require(bound, 'exact_binding_not_observed')
    return dict(state='binding_verified' if bound else 'target_absent_verified' if not exists else 'uploaded_worker_verified',
                accountVerified=True, accountSha256=sha(account.encode()), revision=revision(), workerExists=exists, hostnameBindingExists=bound,
                hostname=HOSTNAME, worker=WORKER, dnsState='dns_records_not_checked', mutationsPerformed=False)


def provider(mode):
    publication_config()
    require_artifact_validation()
    native, _ = helpers(); account, transport = provider_transport()
    result = inspect_provider(account, transport, mode)
    if mode == 'attach' and not result['hostnameBindingExists']:
        before = json.loads(Path('binding-before.json').read_text())
        require(before.get('state') == 'target_absent_verified' and before.get('hostname') == HOSTNAME
                and before.get('worker') == WORKER and before.get('accountVerified') is True
                and before.get('accountSha256') == sha(account.encode()) and before.get('revision') == revision()
                and before.get('workerExists') is False and before.get('hostnameBindingExists') is False
                and before.get('mutationsPerformed') is False, 'initial_preflight_required')
        native.attach(transport, account)
        result = dict(state='attach_request_accepted', hostname=HOSTNAME, worker=WORKER,
                      mutationsPerformed=True, liveVerification='pending')
    return result


def get(path, status=200):
    req = Request(ORIGIN + quote(path, safe='/%-._~'), headers={'User-Agent': 'Boseong-Direct-Release-QA/1.0',
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
    checked = 0; normalized = 0; robots_evidence = None
    require(contract.get('origin') == ORIGIN and contract.get('revision') == revision() and contract.get('ownershipFile') == output.PROOF['path'].lstrip('/'), 'http_contract_identity_mismatch')
    require(len(contract['pages']) == len(ROUTES) and {item['path'] for item in contract['pages']} == ROUTES,
            'http_contract_routes_mismatch')
    require(len(contract['sitemapUrls']) == len(SITEMAP_ROUTES) and
            {local_path(url) for url in contract['sitemapUrls']} == SITEMAP_ROUTES, 'http_contract_sitemap_mismatch')
    for item in contract['pages']:
        body, headers = get(item['path'])
        require(headers.get('Content-Type', '').lower().startswith('text/html'), 'html_content_type')
        p = Page(body.decode('utf-8'))
        require(p.meta.get('site-factory-revision') == revision() and p.canon == [item['url']], 'live_revision_or_canonical_mismatch')
        require(p.og_urls == [item['url']], 'live_og_url_mismatch')
        require(set(item['robots']) == expected_robots(item['path']) and
                set(re.split(r'\s*,\s*', p.meta.get('robots', '').lower())) == expected_robots(item['path']), 'live_meta_robots_mismatch')
        require(not re.search(r'\b(noindex|nofollow|none)\b', ','.join(headers.get_all('X-Robots-Tag', [])), re.I), 'live_header_not_indexable')
        require(purchase_ctas_valid(p,item['path']), 'live_cta_mismatch')
        if sha(body) != contract['files'][item['file']]:
            body = strip_one_cf_beacon(body, contract['files'][item['file']]); normalized += 1
        require(sha(body) == contract['files'][item['file']], 'live_html_digest_mismatch')
        checked += 1
    for path in sorted('/' + name for name in contract['files'] if not name.endswith('.html') and name != '_headers'):
        body, headers = get(path)
        if path == '/robots.txt':
            managed_robots.verify_headers(headers)
            robots_evidence = managed_robots.verify(body, contract['files']['robots.txt'], ORIGIN, contract['sitemapUrls'])
            Path('public-robots.txt').write_bytes(body)
            save(Path('public-robots-headers.json'), {k:v for k,v in headers.items() if k.lower() in ('content-type','x-robots-tag','cf-mitigated','content-length')})
        else:
            require(sha(body) == contract['files'][path.lstrip('/')], 'live_asset_digest_mismatch')
        if path.startswith('/images/'):
            require(headers.get('Content-Type', '').lower().startswith('image/'), 'image_content_type')
        checked += 1
    for path in [*DEFERRED, '/.boseong-release-missing-' + revision() + '/']:
        body, headers = get(path, 404)
        p = Page(body.decode('utf-8'))
        require(headers.get('Content-Type','').lower().startswith('text/html') and p.meta.get('site-factory-revision') == revision() and p.canon == [] and p.og_urls == [] and set(re.split(r'\s*,\s*', p.meta.get('robots','').lower())) == expected_robots('/404.html'), 'live_404_metadata_mismatch')
        if sha(body) != contract['files']['404.html']:
            body = strip_one_cf_beacon(body, contract['files']['404.html']); normalized += 1
        require(sha(body) == contract['files']['404.html'], 'live_404_digest_mismatch')
        checked += 1
    return dict(state='public_release_verified', revision=revision(), regionCount=len(REGION_ROUTES), purchaseHomeCount=1, articleCount=len(ARTICLE_ROUTES), htmlFiles=len(output.FILES), htmlRoutes=len(ROUTES),
                noindexHubs=len(THIN_HUB_ROUTES), sitemapUrls=len(SITEMAP_ROUTES),
                checkedPaths=checked, normalizedCloudflareBeacons=normalized, unknownHttpStatus=404, robotsVerification=robots_evidence)


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










def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['authorize','select','restore-input','artifact','preflight','attach','readback','http'])
    p.add_argument('--report',type=Path,required=True);args=p.parse_args()
    try:
        gate.trusted_control(os.environ)
        contract,binding,binding_sha=gate.load()
        selected=authorize(contract,binding_sha,os.environ,json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text()))
        require(revision()==contract['sourceRevision'],'source_revision_mismatch')
        review=release_review()
        if args.mode=='authorize':
            result=selected
            with open(os.environ['GITHUB_OUTPUT'],'a') as f:
                f.write('source_branch='+BRANCH+'\n')
        elif args.mode=='select':
            result=dict(state='reviewed_release_selected',buildRunId=review['buildRunId'],artifactId=review['artifactId'],revision=revision())
            with open(os.environ['GITHUB_OUTPUT'],'a') as f:
                f.write('build_run_id='+str(review['buildRunId'])+'\nartifact_id='+str(review['artifactId'])+'\n')
        elif args.mode=='restore-input':result=restore_private_input()
        elif args.mode=='artifact':result=artifact()
        elif args.mode in ('preflight','attach','readback'):result=provider(args.mode)
        elif args.mode=='http':
            require_artifact_validation()
            result=public_http()
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


