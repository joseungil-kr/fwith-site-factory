"""Pinned Gangnam production build only. No provider credentials or publication."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from preview_qa import REPOSITORY, OWNER, ROOT, require, read, sha, git, accessibility_contract
import production_output as output

DIRECTORY=Path(__file__).resolve().parent
TITLE='[GANGNAM-PRODUCTION-BUILD] 20261014'
BRANCH='source/seoul-gangnam-production-successor-20261014'
PREDECESSOR='0952966db104f562467d26fdc91ab13c46c0366a'
PREVIEW_TREE='c76786865fdd529e4fd618edb20d6326809e2c1f'
ORIGIN='https://seoul-gangnam.fwith.kr'
HOSTNAME='seoul-gangnam.fwith.kr'
WORKER='seoul-gangnam-flower-guide'
MODIFIED=['astro.config.mjs','package.json','scripts/qa_directory_spacing.py','scripts/qa_gangnam.py','scripts/qa_source_link_amendment.py','src/config/site.ts']
ADDED=['public/39c4ed924bc6084c670a963c26d9f018.txt','scripts/gangnam_release.mjs','scripts/gangnam_release_output.py','scripts/html_surface.py','scripts/test_gangnam_release_output.py','tests/gangnam-release.test.mjs']
COPY_SHA='b442c6ab713453dc4651ea27f1586f777cd5f9915c5b9dd932d6f09da761990b'
UI_SHA='5834b9cabf57f394d83ba3744df7691d7b9d6167a95ba8d04aee1a94eeaa5a5a'

def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n')

def load():
    raw=read(DIRECTORY/'production-source-contract.json');c=json.loads(raw)
    fixed=dict(schemaVersion=1,repository=REPOSITORY,sourceRoot=ROOT,sourceBranch=BRANCH,
               previewSourceRevision=PREDECESSOR,previewSourceTree=PREVIEW_TREE,sourceFiles=1051,
               modifiedPaths=MODIFIED,addedPaths=ADDED,customerCopySha256=COPY_SHA,uiCopySha256=UI_SHA)
    require(set(c)==set(fixed)|{'sourceRevision','sourceTree'},'source_contract_schema')
    require(all(json.dumps(c[k],sort_keys=True)==json.dumps(v,sort_keys=True) for k,v in fixed.items()),'source_contract_identity')
    require(re.fullmatch('[0-9a-f]{40}',c['sourceRevision']) and c['sourceRevision']!=PREDECESSOR
            and re.fullmatch('[0-9a-f]{40}',c['sourceTree']),'source_commit_tree_required')
    br=read(DIRECTORY/'production-binding.json');b=json.loads(br)
    expected=dict(schemaVersion=1,state='approved',repository=REPOSITORY,sourceRoot=ROOT,
        siteKey='seoul-gangnam-flower-direct',hostname=HOSTNAME,origin=ORIGIN,worker=WORKER,
        previewSourceRevision=PREDECESSOR,customerCopySha256=COPY_SHA,uiCopySha256=UI_SHA,
        sourceRevision=c['sourceRevision'],sourceContractSha256=sha(raw),proof=output.PROOF,
        sitemapRoutes=output.ROUTES,htmlFiles=6,directoryRobots='index,follow',notFoundStatus=404,
        publicHttpVerified=False,indexNowSubmitted=False,
        approvals=dict(publication=True,hostBinding=True,indexNowProof=True))
    require(set(b)==set(expected)|{'authorizationEvidence'},'binding_schema')
    require(all(json.dumps(b[k],sort_keys=True)==json.dumps(v,sort_keys=True) for k,v in expected.items()),'exact_gangnam_binding_required')
    require(re.fullmatch(r'https://github[.]com/joseungil-kr/fwith-site-factory/blob/[0-9a-f]{40}/docs/direct-seoul-gangnam/production-authorization-20261014[.]json',b['authorizationEvidence']),'approval_reference_required')
    return c,b,sha(br)

def select(c,binding_sha,env,event):
    require(env.get('GITHUB_REPOSITORY')==REPOSITORY and env.get('GITHUB_REF')=='refs/heads/main','owner_main_required')
    require(env.get('GITHUB_ACTOR')==OWNER and env.get('GITHUB_TRIGGERING_ACTOR')==OWNER and env.get('GITHUB_RUN_ATTEMPT')=='1','owner_first_attempt_required')
    require(env.get('GITHUB_EVENT_NAME')=='issues' and event.get('action')=='opened','opened_issue_required')
    require(re.fullmatch('[0-9a-f]{40}',env.get('GITHUB_SHA','')),'control_revision_required')
    repo,issue=event.get('repository',{}),event.get('issue',{})
    require(repo.get('full_name')==REPOSITORY and repo.get('owner',{}).get('login')==OWNER and repo.get('owner',{}).get('type')=='User','repository_owner_mismatch')
    require(issue.get('title')==TITLE and issue.get('user',{}).get('login')==OWNER,'exact_issue_required')
    raw=issue.get('body');require(isinstance(raw,str) and len(raw)<2048,'invalid_body')
    body=json.loads(raw)
    expected=dict(schemaVersion=1,mode='production-build-only',source_branch=BRANCH,source_revision=c['sourceRevision'],expected_control_revision=env['GITHUB_SHA'],binding_sha256=binding_sha)
    require(isinstance(body,dict) and type(body.get('schemaVersion')) is int and body==expected,'exact_request_required')
    return dict(state='pinned_production_build_selected',sourceRevision=c['sourceRevision'],sourceBranch=BRANCH,controlRevision=env['GITHUB_SHA'],bindingSha256=binding_sha,publicationExecuted=False)

def environment(c,binding_sha,env):
    require(env.get('SITE_RELEASE_MODE')=='production' and env.get('SITE_INDEXABLE')=='true' and env.get('SITE_URL')==ORIGIN and env.get('SITE_FACTORY_REVISION')==c['sourceRevision'],'production_environment_mismatch')
    require(Path(env.get('SITE_RELEASE_BINDING_PATH','')).resolve()==DIRECTORY/'production-binding.json' and env.get('SITE_RELEASE_BINDING_SHA256')==binding_sha,'exact_control_binding_required')
    require(not env.get('CLOUDFLARE_API_TOKEN') and not env.get('CLOUDFLARE_ACCOUNT_ID'),'provider_credentials_forbidden')

def equivalence(dist):
    e=json.loads(read(DIRECTORY/'preview-equivalence.json'))
    require(e['sourceRevision']==PREDECESSOR and e['comparedToActualRun']=='38550139715' and e['artifactSha256']=='9cc5b7330a31c3b81181803e53f0a48e22f534798d35281187012c5b0c991d04','reviewed_preview_identity_required')
    require(len(e['htmlBodyComparisons'])==6 and len(e['staticAssetsSha256'])==13,'equivalence_denominator')
    for row in e['htmlBodyComparisons']:
        match=re.search(rb'<body[ >][\s\S]*',read(dist/row['path']))
        require(match and sha(match.group())==row['sha256'],'reviewed_body_changed:'+row['path'])
    for name,digest in e['staticAssetsSha256'].items():require(sha(read(dist/name))==digest,'reviewed_visual_asset_changed:'+name)
    return dict(previewRun='38550139715',htmlBodiesByteIdentical=6,visualAssetsByteIdentical=13)

def source(checkout,phase,env):
    c,b,binding_sha=load();environment(c,binding_sha,env)
    require(phase in {'prebuild','postbuild'},'invalid_phase')
    checkout=Path(checkout).resolve();root=checkout/ROOT
    require(git(checkout,'rev-parse','HEAD').decode().strip()==c['sourceRevision'],'source_revision_mismatch')
    require(git(checkout,'rev-parse','HEAD:'+ROOT).decode().strip()==c['sourceTree'],'source_tree_mismatch')
    if phase=='prebuild':require(not git(checkout,'status','--porcelain','--untracked-files=all').strip(),'source_checkout_not_clean')
    entries=[e for e in git(checkout,'ls-tree','-r','-z','HEAD','--',ROOT).split(b'\0') if e]
    require(len(entries)==1051,'source_file_count_mismatch')
    for entry in entries:
        meta,name=entry.split(b'\t');mode,kind,blob=meta.decode().split();name=name.decode()
        require(mode=='100644' and kind=='blob' and name.startswith(ROOT+'/'),'source_entry_invalid')
        data=read(checkout/name)
        if phase=='postbuild' and name==ROOT+'/src/data/build-revision.json':require(json.loads(data)=={'revision':c['sourceRevision']},'generated_revision_mismatch')
        else:require(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob,'source_bytes_changed:'+name)
    require(sha(read(root/'src/data/gangnam-copy.json'))==COPY_SHA and sha(read(root/'src/data/gangnam-ui-copy.json'))==UI_SHA,'approved_copy_changed')
    accessibility_contract(read(root/'src/layouts/BaseLayout.astro').decode(),read(root/'src/styles/global.css').decode())
    result=dict(state=phase+'_production_source_verified',sourceRevision=c['sourceRevision'],sourceTree=c['sourceTree'],sourceFiles=1051,providerCredentialsUsed=False,publicationExecuted=False,publicHTTPVerified=False)
    if phase=='postbuild':
        result.update(output.inspect_dist(root/'dist',dict(mode='production',indexable=True,origin=ORIGIN,revision=c['sourceRevision'])))
        result['previewEquivalence']=equivalence(root/'dist')
    return result

def package(checkout,result,env):
    require(env.get('NATIVE_GATES_PASSED')=='true','native_preview_and_production_gates_required')
    c,b,binding_sha=load();release=Path('release');release.mkdir(exist_ok=False)
    shutil.copytree(Path(checkout)/ROOT/'dist',release/'dist')
    manifest=dict(schemaVersion=1,repository=REPOSITORY,sourceBranch=BRANCH,sourceRoot=ROOT,revision=c['sourceRevision'],controlRevision=env['GITHUB_SHA'],runId=env['GITHUB_RUN_ID'],origin=ORIGIN,worker=WORKER,indexable=True,bindingSha256=binding_sha,sourceContractSha256=sha(read(DIRECTORY/'production-source-contract.json')),files=result['files'])
    save(release/'release.json',manifest)
    result.update(releaseManifestSha256=sha(read(release/'release.json')),outputFilesSha256=sha(json.dumps(result['files'],sort_keys=True,separators=(',',':')).encode()),nativePreviewRegressionPassed=True,productionBuildAndMutationQaPassed=True,mobileAndDesktopPixelsVerified=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['select','prebuild','postbuild']);p.add_argument('--checkout');p.add_argument('--report',required=True);p.add_argument('--package',action='store_true');a=p.parse_args()
    c,b,digest=load()
    if a.phase=='select':
        result=select(c,digest,os.environ,json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text()))
        with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('source_revision='+c['sourceRevision']+'\nbinding_sha256='+digest+'\n')
    else:
        result=source(a.checkout,a.phase,os.environ)
        if a.package:require(a.phase=='postbuild','package_requires_postbuild');package(a.checkout,result,os.environ)
    save(a.report,result);print(json.dumps({k:v for k,v in result.items() if k!='files'},sort_keys=True))
