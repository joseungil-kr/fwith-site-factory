"""Control-side gate for one exact noindex Seocho source revision. No network API."""
import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

REPOSITORY = 'joseungil-kr/fwith-site-factory'
OWNER = 'joseungil-kr'
TITLE = '[SEOCHO-PREVIEW-BUILD] 20261014'
SOURCE_ROOT = 'site-factory/seoul-seocho-flower'
BRANCH = 'source/seoul-seocho-production-successor-20261014'
FROZEN_REVISION = '2a4de872c85da0b66815c5e5668e0c7de9ce4341'
ORIGIN = 'https://seoul-seocho.local.invalid'
COPY_SHA = 'c466be6fd967a690cb008ca74ae35d7dec8e93f522cb0b19c8ae86a375b8b53c'
HTML_ROUTES = {'index.html': '/', '404.html': None, 'regions/index.html': '/regions/',
               'regions/seocho-funeral-wreath/index.html': '/regions/seocho-funeral-wreath/',
               'regions/seocho-celebration-wreath/index.html': '/regions/seocho-celebration-wreath/'}


def require(value, code):
    if not value: raise ValueError(code)


def sha(data): return hashlib.sha256(data).hexdigest()


def read(path):
    require(path.is_file() and not path.is_symlink(), 'regular_file_required')
    return path.read_bytes()


def load_contract():
    data = json.loads(Path(__file__).with_name('preview-source-contract.json').read_text(encoding='utf-8'))
    require(data['schemaVersion'] == 1 and data['repository'] == REPOSITORY and data['sourceRoot'] == SOURCE_ROOT
            and data['sourceBranch'] == BRANCH and data['frozenSourceRevision'] == FROZEN_REVISION, 'contract_identity_changed')
    require(re.fullmatch(r'[0-9a-f]{40}', data['expectedSourceRevision']) is not None, 'replace_source_revision_placeholder_before_use')
    require(data['customerCopySha256'] == COPY_SHA and len(data['sealedPins']) == 98, 'frozen_contract_changed')
    return data


def select(contract, env, event):
    require(env.get('GITHUB_REPOSITORY') == REPOSITORY and env.get('GITHUB_REF') == 'refs/heads/main'
            and env.get('GITHUB_ACTOR') == OWNER and env.get('GITHUB_RUN_ATTEMPT') == '1', 'untrusted_or_repeat_request')
    require(env.get('GITHUB_EVENT_NAME') == 'issues' and event.get('action') == 'opened', 'wrong_event')
    repo, issue = event.get('repository', {}), event.get('issue', {})
    require(repo.get('full_name') == REPOSITORY and repo.get('owner', {}).get('login') == OWNER
            and repo.get('owner', {}).get('type') == 'User', 'wrong_repository_owner')
    require(issue.get('title') == TITLE and issue.get('user', {}).get('login') == OWNER, 'wrong_issue')
    require(isinstance(issue.get('body'), str) and len(issue['body']) < 2048, 'invalid_request_body')
    body = json.loads(issue['body'])
    require(isinstance(body, dict) and type(body.get('schemaVersion')) is int, 'invalid_request_schema')
    require(re.fullmatch(r'[0-9a-f]{40}', env.get('GITHUB_SHA', '')) is not None, 'invalid_control_revision')
    require(body == dict(schemaVersion=1, source_branch=BRANCH, source_revision=contract['expectedSourceRevision'],
                        expected_control_revision=env['GITHUB_SHA'], mode='preview'), 'request_contract_mismatch')
    return dict(state='exact_preview_request_selected', sourceBranch=BRANCH, sourceRevision=contract['expectedSourceRevision'],
                sourceRoot=SOURCE_ROOT, controlRevision=env['GITHUB_SHA'], providerCredentialsUsed=False, publicationAuthorized=False)


def git(checkout, *args):
    return subprocess.check_output(['git', '-c', 'core.autocrlf=false', '-C', str(checkout), *args], timeout=30)


def preserved_inputs(source, contract, phase, revision):
    require(phase in {'prebuild', 'postbuild'}, 'invalid_phase')
    for path, digest in contract['protectedFiles'].items():
        raw = read(source / path)
        if phase == 'postbuild' and path == 'src/data/build-revision.json':
            require(json.loads(raw) == {'revision': revision}, 'generated_revision_mismatch')
        else:
            require(sha(raw) == digest, 'protected_source_changed:' + path)
    require(sha(read(source / 'src/data/seocho-copy.json')) == COPY_SHA, 'customer_copy_changed')
    pins = None
    for node in ast.parse(read(source / 'scripts/qa_seocho.py')).body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'PINS' for target in node.targets):
            require(pins is None, 'multiple_pin_assignments')
            pins = ast.literal_eval(node.value)
    require(pins == contract['sealedPins'], 'sealed_98_pins_changed')
    for path, digest in pins.items():
        require(sha(read(source / 'src/data/seocho-approved' / path)) == digest, 'sealed_input_changed')
    config = json.loads(read(source / 'src/data/site-config.json'))
    require(config['productionApproved'] is False and config['hostnameOwnershipVerified'] is False
            and config['worker'] is None and config['previewUrl'] == ORIGIN, 'preview_config_changed')
    proposal = json.loads(read(source / 'src/data/production-target.json'))
    require(proposal['state'] == 'proposed-unverified' and all(proposal[key] is False for key in
            ['providerOwnershipVerified', 'publicationApproved', 'hostBindingApproved', 'indexNowProofApproved']), 'proposal_falsely_approved')


class Metadata(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.robots=[]; self.revisions=[]; self.canonical=[]; self.h1=0
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs); require(len(a)==len(attrs), 'duplicate_html_attribute')
        if tag=='meta' and a.get('name')=='robots': self.robots.append(a.get('content'))
        if tag=='meta' and a.get('name')=='site-factory-revision': self.revisions.append(a.get('content'))
        if tag=='link' and a.get('rel')=='canonical': self.canonical.append(a.get('href'))
        if tag=='h1': self.h1+=1


def preview_output(dist, revision):
    paths=list(dist.rglob('*'))
    require(paths and not any(p.is_symlink() for p in paths), 'missing_or_symlinked_output')
    files={p.relative_to(dist).as_posix():sha(read(p)) for p in paths if p.is_file()}
    require({name for name in files if name.endswith('.html')}==set(HTML_ROUTES), 'exact_preview_routes_required')
    require(not any(Path(name).name in {'_worker.js','_routes.json','_redirects','package.json','package-lock.json'} for name in files), 'executable_or_routing_output_forbidden')
    for name, route in HTML_ROUTES.items():
        doc=Metadata(read(dist/name).decode('utf-8'))
        require(doc.robots==['noindex,nofollow,noarchive'] and doc.revisions==[revision] and doc.h1==1, 'preview_metadata_mismatch')
        require(doc.canonical==([] if route is None else [ORIGIN+route]), 'preview_canonical_mismatch')
    require(read(dist/'robots.txt').decode('utf-8')=='User-agent: *\nDisallow: /\n', 'preview_robots_mismatch')
    require('X-Robots-Tag: noindex, nofollow, noarchive' in read(dist/'_headers').decode('utf-8'), 'preview_response_noindex_missing')
    for path in dist.glob('sitemap*.xml'):
        for loc in ET.fromstring(read(path)).iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
            value=loc.text or ''
            require(value.startswith(ORIGIN+'/sitemap') and value.endswith('.xml'), 'preview_customer_sitemap_url_forbidden')
    manifest=json.dumps(files,sort_keys=True,separators=(',',':')).encode()
    return dict(files=files,distManifestSha256=sha(manifest),distManifestAlgorithm='sha256-compact-sorted-json-path-to-sha256',
                htmlFiles=5,sitemapCustomerUrls=0,browserVerified=False,publicHTTPVerified=False,publicationAuthorized=False)


def verify(checkout, contract, phase, env):
    revision=contract['expectedSourceRevision']; checkout=Path(checkout).resolve(); source=checkout/SOURCE_ROOT
    require(env.get('SITE_FACTORY_REVISION')==revision, 'build_revision_environment_mismatch')
    require(env.get('SITE_RELEASE_MODE')=='preview' and env.get('SITE_INDEXABLE')=='false'
            and env.get('SITE_URL')==ORIGIN and not env.get('SITE_RELEASE_BINDING_PATH')
            and not env.get('SITE_RELEASE_BINDING_SHA256'), 'preview_environment_required')
    require(git(checkout,'rev-parse','HEAD').decode().strip()==revision, 'checkout_revision_mismatch')
    git(checkout,'merge-base','--is-ancestor',FROZEN_REVISION,revision)
    tracked=[x.decode() for x in git(checkout,'ls-files','-z','--',SOURCE_ROOT).split(b'\0') if x]
    relative={name[len(SOURCE_ROOT)+1:] for name in tracked}
    require(relative==set(contract['expectedSourcePaths']), 'exact_source_path_set_mismatch')
    preserved_inputs(source,contract,phase,revision)
    report=dict(state='preview_'+phase+'_verified',sourceRevision=revision,frozenSourceRevision=FROZEN_REVISION,
                sourceFiles=len(relative),protectedFiles=len(contract['protectedFiles']),sealedPins=98,customerCopySha256=COPY_SHA,
                providerCredentialsUsed=False,publicationAuthorized=False,remoteMutationsPerformed=False)
    if phase=='postbuild': report.update(preview_output(source/'dist',revision))
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['select','prebuild','postbuild'])
    parser.add_argument('--checkout');parser.add_argument('--report',required=True);args=parser.parse_args()
    contract=load_contract()
    if args.mode=='select':
        event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
        report=select(contract,os.environ,event)
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as output:
            output.write('source_branch='+BRANCH+'\nsource_revision='+contract['expectedSourceRevision']+'\n')
    else:
        require(bool(args.checkout),'checkout_required');report=verify(args.checkout,contract,args.mode,os.environ)
    Path(args.report).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in report.items() if key!='files'},sort_keys=True))


if __name__=='__main__':main()
