"""Frozen Gangdong preview reference and shared primitives. No preview workflow is installed."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path

REPOSITORY = 'joseungil-kr/fwith-site-factory'
OWNER = 'joseungil-kr'
TITLE = '[GANGDONG-PREVIEW-QA] accessibility-20261014'
BRANCH = 'site-factory-seoul-gangdong-direct'
REVISION = '9c044584505eec60c71f2bc7add497f0902f5424'
ROOT = 'site-factory/seoul-gangdong-flower'
TREE = 'a7e8ff540822dc7ee326f1503a9a2bbccf07f996'
SOURCE_FILES = 69
ORIGIN = 'https://seoul-gangdong.local.invalid'
ROUTES = {'index.html':'/', 'regions/index.html':'/regions/',
          'regions/gangdong-condolence-wreath/index.html':'/regions/gangdong-condolence-wreath/',
          'regions/gangdong-wedding-wreath/index.html':'/regions/gangdong-wedding-wreath/', '404.html':None}
ROUTE_ORDER=['/','/regions/','/regions/gangdong-condolence-wreath/','/regions/gangdong-wedding-wreath/','/404.html']
EMPTY_SITEMAP = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>\n'
VIEWPORTS=[(320,740),(390,844),(1280,900)]
ASSET_PATHS={f'images/products/{sku}.jpg' for sku in ('B201','B203','B205','B060','C200','C203','C204','C205')}|{f'images/shared-banners/flower-{kind}.webp' for kind in ('message','budget','consultation')}
STATIC_PATHS=set(ROUTES)|ASSET_PATHS|{'robots.txt','_headers','sitemap.xml','favicon.svg'}

def require(value, reason):
    if not value: raise ValueError(reason)


def read(path):
    require(path.is_file() and not path.is_symlink(), 'regular_file_required:' + str(path))
    return path.read_bytes()


def sha(data): return hashlib.sha256(data).hexdigest()


def git(checkout, *args):
    return subprocess.check_output(['git','-c','core.autocrlf=false','-C',str(checkout),*args],timeout=30)


def select(env, event):
    require(re.fullmatch('[0-9a-f]{40}',REVISION) and re.fullmatch('[0-9a-f]{40}',TREE),'source_pins_not_finalized')
    require(env.get('GITHUB_REPOSITORY') == REPOSITORY and env.get('GITHUB_REF') == 'refs/heads/main', 'wrong_repository_or_ref')
    require(env.get('GITHUB_ACTOR') == OWNER and env.get('GITHUB_TRIGGERING_ACTOR') == OWNER, 'wrong_actor')
    require(env.get('GITHUB_RUN_ATTEMPT') == '1', 'rerun_forbidden')
    require(env.get('GITHUB_EVENT_NAME') == 'issues' and event.get('action') == 'opened', 'wrong_event')
    require(re.fullmatch('[0-9a-f]{40}', env.get('GITHUB_SHA','')), 'invalid_control_sha')
    repo, issue = event.get('repository',{}), event.get('issue',{})
    require(repo.get('full_name') == REPOSITORY and repo.get('owner',{}).get('login') == OWNER and repo.get('owner',{}).get('type') == 'User', 'wrong_owner')
    require(issue.get('title') == TITLE and issue.get('user',{}).get('login') == OWNER, 'wrong_issue')
    body = issue.get('body'); require(isinstance(body,str) and len(body)<2048, 'invalid_body')
    data = json.loads(body)
    require(isinstance(data,dict) and type(data.get('schemaVersion')) is int, 'invalid_schema')
    require(data == {'schemaVersion':1,'source_branch':BRANCH,'source_revision':REVISION,
                     'expected_control_revision':env['GITHUB_SHA'],'mode':'preview-only'}, 'request_mismatch')
    return {'state':'pinned_preview_only_selected','sourceRevision':REVISION,'sourceBranch':BRANCH,
            'sourceRoot':ROOT,'controlRevision':env['GITHUB_SHA'],'publicationAuthorized':False,'providerCredentialsUsed':False}


def preview_environment(env):
    require(env.get('SITE_FACTORY_REVISION') == REVISION and env.get('SITE_INDEXABLE') == 'false'
            and env.get('SITE_URL') == ORIGIN and env.get('SITE_RELEASE_MODE') == 'preview', 'preview_environment_required')
    require(all(env.get(k,'false')=='false' for k in ('PRODUCTION_APPROVED','OWNERSHIP_VERIFIED','INDEXNOW_ENABLED','PUBLIC_APPROVED')),'public_flags_forbidden')
    require(not env.get('SITE_RELEASE_BINDING_PATH') and not env.get('SITE_RELEASE_BINDING_SHA256'), 'release_binding_forbidden')


def accessibility_contract(layout, css):
    require('<main id="main-content" tabindex="-1">' in layout, 'skip_target_not_programmatically_focusable')
    require('@media(min-width:861px){html{scroll-padding-block-start:83px}}' in css, 'desktop_native_focus_clearance_missing')


def source_inventory(root, expected):
    root=Path(root);require(root.is_dir() and not root.is_symlink(),'regular_source_root_required')
    allowed_outputs={'gangdong-static-qa.json','gangdong-negative-fixtures.json','rendered-copy-extraction.json','customer-string-output-role-map.json'}
    ignored_dirs={'node_modules','dist','.astro','__pycache__'}
    actual=set()
    for directory,dirs,files in os.walk(root):
        current=Path(directory)
        for name in list(dirs):
            child=current/name
            if name in ignored_dirs:
                dirs.remove(name)
                continue
            require(not child.is_symlink(),'source_directory_symlink_forbidden')
        for name in files:
            child=current/name
            require(child.is_file() and not child.is_symlink(),'source_file_symlink_forbidden')
            relative=child.relative_to(root).as_posix()
            if relative not in allowed_outputs:actual.add(relative)
    require(actual==set(expected),'untracked_or_missing_source_file')


def source(checkout, phase, env):
    require(phase in ('prebuild','postbuild'), 'invalid_phase'); preview_environment(env)
    checkout = Path(checkout).resolve(); root = checkout / ROOT
    require(git(checkout,'rev-parse','HEAD').decode().strip() == REVISION, 'checkout_revision_mismatch')
    require(git(checkout,'rev-parse','HEAD:'+ROOT).decode().strip() == TREE, 'source_tree_mismatch')
    entries = git(checkout,'ls-tree','-r','-z','HEAD','--',ROOT).split(b'\0'); checked=[]
    for entry in entries:
        if not entry: continue
        meta,name = entry.split(b'\t'); mode,kind,blob = meta.decode().split(); name=name.decode()
        require(mode == '100644' and kind == 'blob' and name.startswith(ROOT+'/'), 'unexpected_source_entry')
        data = read(checkout/name)
        require(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() == blob, 'tracked_source_changed:'+name)
        checked.append(name)
    require(len(checked) == SOURCE_FILES, 'frozen_source_count_mismatch')
    source_inventory(root,[name.removeprefix(ROOT+'/') for name in checked])
    runtime = json.loads(read(root/'src/data/gangdong-runtime.json'))
    require(runtime['schema']=='gangdong-local-static-v1' and runtime['districtCode']=='11740'
            and runtime['origin']==ORIGIN and runtime['robots']=='noindex,nofollow,noarchive'
            and runtime['sitemap']==[] and runtime['htmlCount']==5
            and all(runtime[k] is False for k in ('ownershipVerified','productionApproved','publicApproved','indexNowEnabled','indexable')), 'preview_config_changed')
    require(set(p['path'] for p in runtime['pages'])==set(ROUTE_ORDER),'runtime_route_mismatch')
    result = {'state':phase+'_verified','sourceRevision':REVISION,'sourceTree':TREE,'sourceFiles':SOURCE_FILES,
              'publicationAuthorized':False,'providerCredentialsUsed':False,'publicHTTPVerified':False}
    if phase == 'postbuild': result.update(output(root/'dist',REVISION))
    return result


class Metadata(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.robots=[]; self.revisions=[]; self.canonical=[]; self.h1=0; self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs); require(len(a)==len(attrs),'duplicate_attribute')
        if tag=='h1':self.h1+=1
        if tag=='meta' and a.get('name')=='robots':self.robots.append(a.get('content'))
        if tag=='meta' and a.get('name')=='site-factory-revision':self.revisions.append(a.get('content'))
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href'))


def output(dist,revision=REVISION):
    dist=Path(dist); paths=list(dist.rglob('*')); require(paths,'empty_output')
    require(not any(p.is_symlink() for p in paths),'symlink_output')
    files={p.relative_to(dist).as_posix():sha(read(p)) for p in paths if p.is_file()}
    require(len(files)==21 and {p for p in files if p.endswith('.html')}==set(ROUTES),'output_inventory_mismatch')
    css={p for p in files if re.fullmatch(r'_astro/[A-Za-z0-9_.-]+\.css',p)}
    require(len(css)==1 and set(files)==STATIC_PATHS|css,'exact_static_output_paths_required')
    require(not any(Path(p).name in {'_worker.js','_routes.json','_redirects','package.json','package-lock.json'} for p in files),'executable_output_forbidden')
    require({p for p in files if Path(p).name.startswith('sitemap')}=={'sitemap.xml'},'preview_sitemap_inventory_mismatch')
    require(read(dist/'sitemap.xml').decode()==EMPTY_SITEMAP,'preview_sitemap_must_be_exact_empty')
    for name,route in ROUTES.items():
        doc=Metadata(read(dist/name).decode())
        require(doc.h1==1 and doc.robots==['noindex,nofollow,noarchive'] and doc.revisions==[],'preview_metadata_mismatch:'+name)
        require(doc.canonical==([] if route is None else [ORIGIN+route]),'preview_canonical_mismatch:'+name)
    require(read(dist/'robots.txt').decode()=='User-agent: *\nDisallow: /\n','preview_robots_mismatch')
    require('X-Robots-Tag: noindex, nofollow, noarchive' in read(dist/'_headers').decode(),'preview_header_missing')
    return {'files':files,'distManifestSha256':sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode()),
            'htmlFiles':5,'sitemapCustomerUrls':0,'browserVerified':False,'publicHTTPVerified':False,'publicationAuthorized':False}


def main():
    p=argparse.ArgumentParser(); p.add_argument('phase',choices=['select','prebuild','postbuild']);p.add_argument('--checkout');p.add_argument('--report',required=True);a=p.parse_args()
    result=select(os.environ,json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())) if a.phase=='select' else source(a.checkout,a.phase,os.environ)
    Path(a.report).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='files'}))

if __name__=='__main__':main()
