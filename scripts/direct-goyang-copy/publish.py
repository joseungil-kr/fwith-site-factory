#!/usr/bin/env python3
"""Fixed Goyang existing-host assets-only wrapper, adapted from direct Uijeongbu.
No target code in publisher, no attach operation, no provider settings writes.
"""
import argparse, hashlib, importlib.util, json, os, re, shutil, stat, sys, time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
import xml.etree.ElementTree as ET
import guard
REPOSITORY='joseungil-kr/fwith-site-factory'
BRANCH=guard.BRANCH
SOURCE_ROOT=guard.ROOT
HOSTNAME='goyang.fwith.kr'
ORIGIN='https://'+HOSTNAME
WORKER='goyang-flower-guide-qa'
RECEIPT_ISSUE=219
LIMIT=20*1024*1024
AUTH=guard.AUTH

def helper(name):
    spec=importlib.util.spec_from_file_location('trusted_'+name,guard.CONTROL/'scripts/manual-release-20261007'/ (name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

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

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def inventory(root):
    # Reused direct-publisher static boundary; strengthened to reject executable bits.
    require(root.is_dir() and not root.is_symlink(),'invalid_artifact_root')
    files={}
    for path in sorted(root.rglob('*')):
        mode=path.lstat().st_mode;rel=path.relative_to(root)
        require(stat.S_ISDIR(mode) or stat.S_ISREG(mode),'unsafe_artifact_type')
        require(not any(p.startswith('.') for p in rel.parts),'hidden_artifact_path')
        require(path.name not in {'_worker.js','_routes.json','_redirects','package.json','package-lock.json'} and not path.name.startswith('wrangler.'),'executable_artifact_forbidden')
        if path.is_file():
            require(not mode & 0o111,'executable_artifact_mode')
            files[rel.as_posix()]=sha(path.read_bytes())
    require({'index.html','404.html','_headers','robots.txt','sitemap-index.xml'}<=set(files),'required_artifact_missing')
    return files


def normalized_inventory(root, revision_value):
    files=inventory(root);out={}
    marker=re.compile(rb'(<meta name="site-factory-revision" content=")'+revision_value.encode()+rb'("\s*/?>)')
    for name in files:
        raw=(root/name).read_bytes()
        if name.endswith('.html'):
            raw,n=marker.subn(rb'\1__REVIEWED_RELEASE_REVISION__\2',raw)
            require(n==1,'single_exact_revision_meta_required')
        out[name]=sha(raw)
    return out


def check_static(root, contract, revision_value, held):
    files=inventory(root)
    require(normalized_inventory(root,revision_value)==contract['normalizedFiles'],'reviewed_artifact_bytes_mismatch')
    require(len(files)==94 and len(contract['pages'])==74 and contract['detailCount']==67 and contract['actualProductCards']==255,'reviewed_scope_mismatch')
    routes={p['route'] for p in contract['pages'] if p['file']!='404.html'}
    require(not routes & set(held),'held_route_built')
    for entry in contract['pages']:
        p=Page((root/entry['file']).read_text())
        require(p.meta.get('site-factory-revision')==revision_value,'revision_mismatch')
        require(p.canon==entry['canonical'] and [p.meta.get('robots')]==entry['robots'],'canonical_or_robots_mismatch')
        for asset in p.assets:
            require(asset.startswith('/') and not asset.startswith('//') and local_path(ORIGIN+asset).lstrip('/') in files,'missing_or_foreign_asset')
        for href in p.links:
            u=urlsplit(href)
            if href.startswith('/') or href.startswith(ORIGIN+'/'):
                require(u.path not in held,'held_link_published')
    urls=[];maps=[]
    for name in files:
        if name.startswith('sitemap') and name.endswith('.xml'):
            xml=ET.fromstring((root/name).read_bytes());locs=[n.text for n in xml.iter() if n.tag.split('}')[-1]=='loc']
            for u in locs:local_path(u)
            if xml.tag.split('}')[-1]=='urlset':urls+=locs
            else:maps+=locs
    require(len(urls)==len(set(urls)) and sorted(urls)==contract['sitemapUrls'],'sitemap_exact_reviewed_urls_mismatch')
    require(all(local_path(u).lstrip('/') in files for u in maps),'missing_sitemap')
    ownership=[p for p in root.glob('*.txt') if re.fullmatch(r'[A-Za-z0-9-]{8,128}',p.stem) and p.read_text().strip()==p.stem]
    require(len(ownership)==1,'ownership_file_missing_or_ambiguous')
    return dict(origin=ORIGIN,revision=revision_value,pages=contract['pages'],sitemapUrls=urls,ownershipFile=ownership[0].name,files=files,heldRoutes=held)


def no_redirect_config():
    release=Path('release')
    require(not release.is_symlink(),'release_symlink')
    for parent in [release.resolve(),*release.resolve().parents]:
        require(not (parent/'.wrangler/deploy/config.json').exists(),'wrangler_config_redirect')


def identity(a, authority):
    return dict(schemaVersion=1,repository=REPOSITORY,sourceBranch=BRANCH,sourceRoot=SOURCE_ROOT,
        revision=revision(),controlRevision=os.environ['GITHUB_SHA'],authority=authority,runId=os.environ['GITHUB_RUN_ID'],
        origin=ORIGIN,worker=WORKER,indexable=True,sourceManifestSha256=a['sourceManifestSha256'],staticContractSha256=a['staticContractSha256'])


def package(source):
    a,authority=guard.control(revision());guard.source(source.parents[1],revision(),after=True)
    contract=guard.load(AUTH/'reviewed-static-contract.json')
    check_static(source/'dist',contract,revision(),a['plan']['heldRoutes'])
    release=Path('release');require(not release.exists(),'release_directory_exists');release.mkdir()
    shutil.copytree(source/'dist',release/'dist');save(release/'release.json',dict(**identity(a,authority),files=inventory(release/'dist')))
    h=sha((release/'release.json').read_bytes())
    with open(os.environ['GITHUB_OUTPUT'],'a') as out:out.write('release_sha256='+h+'\n')
    return dict(state='packaged',releaseSha256=h,revision=revision(),visualQa='DEFERRED_NOT_PASS')


def artifact():
    a,authority=guard.control(revision());release=Path('release');no_redirect_config()
    require({p.name for p in release.iterdir()}=={'dist','release.json'},'unexpected_release_files')
    raw=(release/'release.json').read_bytes();require(not (release/'release.json').is_symlink() and sha(raw)==os.environ.get('RELEASE_SHA256'),'manifest_digest_mismatch')
    require(json.loads(raw)==dict(**identity(a,authority),files=inventory(release/'dist')),'artifact_identity_or_digest_mismatch')
    c=check_static(release/'dist',guard.load(AUTH/'reviewed-static-contract.json'),revision(),a['plan']['heldRoutes']);save('http-contract.json',c)
    return dict(state='artifact_verified',files=len(c['files']),htmlRoutes=len(c['pages']),sitemapUrls=len(c['sitemapUrls']),visualQa='DEFERRED_NOT_PASS')


def provider_transport():
    account=os.environ.get('CLOUDFLARE_ACCOUNT_ID','');token=os.environ.get('CLOUDFLARE_API_TOKEN','')
    require(re.fullmatch('[0-9a-fA-F]{32}',account) and token,'missing_provider_configuration')
    prefix='/accounts/'+account;opener=build_opener(NoRedirect())
    endpoints={prefix,prefix+'/workers/scripts',prefix+'/workers/domains',prefix+'/workers/scripts/'+WORKER+'/settings',prefix+'/workers/scripts/'+WORKER+'/subdomain'}
    def get(path):
        u=urlsplit(path);require(u.path in endpoints and (not u.query or (u.path in {prefix+'/workers/scripts',prefix+'/workers/domains'} and re.fullmatch(r'page=[0-9]+&per_page=100',u.query))),'provider_operation_forbidden')
        req=Request('https://api.cloudflare.com/client/v4'+path,method='GET',headers={'Authorization':'Bearer '+token})
        with opener.open(req,timeout=30) as response:
            require(response.status==200,'provider_http_status');raw=response.read(LIMIT+1)
        require(len(raw)<=LIMIT,'provider_response_limit');data=json.loads(raw)
        require(data.get('success') is True and not data.get('errors') and 'result' in data,'provider_response_unverified');return data
    return account,get


def provider_policy(a):
    p=guard.load(AUTH/'policy.json');require(p['worker']==WORKER and p['productionOrigin']==ORIGIN and p['productionConfig']=='wrangler.staging.jsonc','fixed_policy_mismatch')
    p['providerBaselineSha256']={'production':a['provider']['acceptedStateSha256']};return p


def inspect_existing(account,get,p):
    pc=helper('provider_check');prefix='/accounts/'+account
    require(get(prefix)['result']['id']==account,'account_identity_mismatch')
    scripts=pc.paginate(get,prefix+'/workers/scripts');names=[r.get('id') for r in scripts]
    require(len(names)==len(set(names)) and names.count(WORKER)==1,'existing_worker_missing_or_ambiguous')
    return pc.inventory(get,account,p,'production')


def provider(mode):
    # Post-upload GET must still run if main moved during an attempted upload.
    a,_=guard.control(revision(),check_remote=mode!='after');p=provider_policy(a)
    account,get=provider_transport();state=inspect_existing(account,get,p)
    save('provider-observed-'+mode+'.json',state)
    state_hash=sha(guard.compact(state));require(state_hash==a['provider']['acceptedStateSha256'],'provider_state_differs_from_accepted_baseline')
    receipt=Path('provider-state-before.json')
    if mode=='before':
        require(not receipt.exists(),'preflight_receipt_exists');save(receipt,state)
        config=helper('write_assets_only_config').configuration(p,'production',guard.load(AUTH/'wrangler.staging.jsonc'),state)
        no_redirect_config();save(Path('release/.manual-assets-only-20261007.jsonc'),config)
    else:
        require(guard.load(receipt)==state,'provider_state_changed')
        expected=helper('write_assets_only_config').configuration(p,'production',guard.load(AUTH/'wrangler.staging.jsonc'),state)
        require(guard.load(Path('release/.manual-assets-only-20261007.jsonc'))==expected,'upload_config_changed')
    return dict(state='provider_unchanged',checkpoint=mode,providerStateSha256=state_hash,mutationsPerformed=False,legacyRoutes='not_read_not_modified')


def upload_ready():
    a,authority=guard.control(revision());p=provider_policy(a);no_redirect_config()
    require({x.name for x in Path('release').iterdir()}=={'dist','release.json','.manual-assets-only-20261007.jsonc'},'unexpected_upload_files')
    raw=Path('release/release.json').read_bytes()
    require(sha(raw)==os.environ.get('RELEASE_SHA256') and json.loads(raw)==dict(**identity(a,authority),files=inventory(Path('release/dist'))),'upload_manifest_drift')
    state=guard.load(Path('provider-state-before.json'))
    config=helper('write_assets_only_config').configuration(p,'production',guard.load(AUTH/'wrangler.staging.jsonc'),state)
    require(guard.load(Path('release/.manual-assets-only-20261007.jsonc'))==config,'upload_config_drift')
    check_static(Path('release/dist'),guard.load(AUTH/'reviewed-static-contract.json'),revision(),a['plan']['heldRoutes'])
    return dict(state='exact_assets_only_upload_ready',providerStateSha256=sha(guard.compact(state)))


def public_http():
    # Diagnostic exact-byte reads remain allowed after an attempted upload if refs moved.
    # IndexNow still requires current main/source CAS in its separate control gate.
    a,_=guard.control(revision(),check_remote=False);c=guard.load(Path('http-contract.json'));root=Path('release/dist')
    require(c==check_static(root,guard.load(AUTH/'reviewed-static-contract.json'),revision(),a['plan']['heldRoutes']),'http_contract_drift')
    http=helper('verify_http');rules=http.rules(root/'_headers');checked=0
    for name,h in c['files'].items():
        if name in ('_headers','404.html'):continue
        route='/' if name=='index.html' else '/'+name.removesuffix('index.html') if name.endswith('/index.html') else '/'+name
        url=ORIGIN+quote(route,safe='/')
        with http.request_response(url,'production',opener=build_opener(NoRedirect()).open) as response:
            http.assert_response_status(response,url,route,200);raw=response.read(LIMIT+1);require(len(raw)<=LIMIT,'http_response_limit')
            http.verify_headers(route,response.headers,rules);require(sha(raw)==h,'public_artifact_bytes_mismatch')
        checked+=1
    for route in [*c['heldRoutes'],'/__goyang_release_missing_'+revision()+'__/']:
        url=ORIGIN+quote(route,safe='/')
        with http.request_response(url,'production',opener=build_opener(NoRedirect()).open) as response:
            http.assert_response_status(response,url,route,404);raw=response.read(LIMIT+1);http.verify_headers(route,response.headers,rules)
            require(sha(raw)==c['files']['404.html'],'public_404_bytes_mismatch')
        checked+=1
    return dict(state='public_release_verified',revision=revision(),controlRevision=os.environ['GITHUB_SHA'],releaseSha256=sha(Path('release/release.json').read_bytes()),checkedPaths=checked,unknownHttpStatus=404,visualQa='DEFERRED_NOT_PASS')


def helpers():
    # Existing trusted IndexNow engine only; no domain-attach imports or functions.
    sys.path.insert(0,str(guard.CONTROL/'site-factory/engine'))


def indexnow_site():
    c=guard.load(Path('http-contract.json'));key=(Path('release/dist')/c['ownershipFile']).read_text().strip()
    return dict(siteKey='goyang-flower-v2',siteUrl=ORIGIN,productionEnabled=True,launchMode='live',indexnowKey=key)

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
    a,_=guard.control(revision())
    receipt=guard.load(Path('public-http.json'))
    require(receipt.get('state')=='public_release_verified' and receipt.get('revision')==revision() and receipt.get('controlRevision')==os.environ['GITHUB_SHA'] and receipt.get('releaseSha256')==sha(Path('release/release.json').read_bytes()),'public_receipt_missing_or_stale')
    helpers()
    from indexnow_finalize import finalize, Journal
    result = finalize(indexnow_site(), revision(), Path('release'), Journal(REPOSITORY, RECEIPT_ISSUE),
                      transport=observed_indexnow_request,
                      run_url='https://github.com/' + REPOSITORY + '/actions/runs/' + os.environ['GITHUB_RUN_ID'])
    result['searchIndexing'] = 'not_verified'
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['source-before','source-after','package','artifact','provider-before','provider-after','upload-ready','http','indexnow-probe','indexnow']);p.add_argument('--source',type=Path);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
    try:
        if args.mode.startswith('source-'):result=guard.source(args.source,revision(),after=args.mode=='source-after')
        elif args.mode=='package':result=package(args.source)
        elif args.mode=='artifact':result=artifact()
        elif args.mode.startswith('provider-'):result=provider(args.mode.split('-')[1])
        elif args.mode=='upload-ready':result=upload_ready()
        elif args.mode=='http':result=public_http()
        elif args.mode=='indexnow-probe':result=indexnow_probe()
        else:result=indexnow()
        save(args.report,result);print(json.dumps({k:v for k,v in result.items() if k not in ('files','urls')},sort_keys=True));return 0
    except Exception as error:
        code=str(error) if type(error) is ValueError and re.fullmatch('[a-zA-Z0-9_]+',str(error)) else type(error).__name__
        result=dict(state='blocked_or_failed',mode=args.mode,code=code);save(args.report,result);print(json.dumps(result));return 1
if __name__=='__main__':raise SystemExit(main())
