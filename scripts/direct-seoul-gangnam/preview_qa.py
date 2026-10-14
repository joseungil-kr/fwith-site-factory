"""Pinned Gangnam preview-only runner gate. No release_mode or provider access."""
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
TITLE = '[GANGNAM-PREVIEW-QA] 20261014'
BRANCH = 'source/seoul-gangnam-frozen-git-push-20261014'
REVISION = 'b2c63dc3fd44da869e3c8ebe2ebe7a083054d3bf'
ROOT = 'site-factory/seoul-gangnam-flower'
TREE = 'bdd0d85113eb568ce17e30d386dd255a2836f678'
ORIGIN = 'https://seoul-gangnam.local.invalid'
ROUTES = {'index.html':'/', 'regions/index.html':'/regions/', '404.html':None,
          **{f'regions/gangnam-{p}-wreath/index.html':f'/regions/gangnam-{p}-wreath/' for p in ('funeral','wedding','event')}}

ROUTE_ORDER=['/','/regions/']+[f'/regions/gangnam-{p}-wreath/' for p in ('funeral','wedding','event')]+['/404.html']
VIEWPORTS=[(320,740),(390,844),(1280,900)]

def require(value, reason):
    if not value: raise ValueError(reason)


def read(path):
    require(path.is_file() and not path.is_symlink(), 'regular_file_required:' + str(path))
    return path.read_bytes()


def sha(data): return hashlib.sha256(data).hexdigest()


def git(checkout, *args):
    return subprocess.check_output(['git','-c','core.autocrlf=false','-C',str(checkout),*args],timeout=30)


def select(env, event):
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
    require(not env.get('SITE_RELEASE_BINDING_PATH') and not env.get('SITE_RELEASE_BINDING_SHA256'), 'release_binding_forbidden')


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
        if phase == 'postbuild' and name == ROOT+'/src/data/build-revision.json':
            require(json.loads(data) == {'revision':REVISION}, 'generated_revision_mismatch')
        else:
            require(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() == blob, 'tracked_source_changed:'+name)
        checked.append(name)
    require(len(checked) == 1045, 'frozen_source_count_mismatch')
    config = json.loads(read(root/'src/data/site-config.json'))
    require(config['siteKey']=='seoul-gangnam-flower-direct' and config['worker'] is None
            and config['productionApproved'] is False and config['hostnameOwnershipVerified'] is False
            and config['previewUrl']==ORIGIN and config['canonicalHostname'] is None, 'preview_config_changed')
    # The historical Gwanak release module is retained, never imported or invoked.
    result = {'state':phase+'_verified','sourceRevision':REVISION,'sourceTree':TREE,'sourceFiles':1045,
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
    require(not any(Path(p).name in {'_worker.js','_routes.json','_redirects','package.json','package-lock.json'} for p in files),'executable_output_forbidden')
    require(not any(p.startswith('sitemap') for p in files),'preview_sitemap_forbidden')
    for name,route in ROUTES.items():
        doc=Metadata(read(dist/name).decode())
        require(doc.h1==1 and doc.robots==['noindex,nofollow,noarchive'] and doc.revisions==[revision],'preview_metadata_mismatch:'+name)
        require(doc.canonical==([] if route is None else [ORIGIN+route]),'preview_canonical_mismatch:'+name)
    require(read(dist/'robots.txt').decode()=='User-agent: *\nDisallow: /\n','preview_robots_mismatch')
    require('X-Robots-Tag: noindex, nofollow, noarchive' in read(dist/'_headers').decode(),'preview_header_missing')
    return {'files':files,'distManifestSha256':sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode()),
            'htmlFiles':6,'sitemapCustomerUrls':0,'browserVerified':False,'publicHTTPVerified':False,'publicationAuthorized':False}


def main():
    p=argparse.ArgumentParser(); p.add_argument('phase',choices=['select','prebuild','postbuild']);p.add_argument('--checkout');p.add_argument('--report',required=True);a=p.parse_args()
    result=select(os.environ,json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())) if a.phase=='select' else source(a.checkout,a.phase,os.environ)
    Path(a.report).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='files'}))

if __name__=='__main__':main()
