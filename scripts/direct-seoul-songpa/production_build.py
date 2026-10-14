"""Pinned Songpa production build only. No provider credentials or publication."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from preview_qa import REPOSITORY, OWNER, ROOT, require, read, sha, git, accessibility_contract, source_inventory
import production_output as output

DIRECTORY=Path(__file__).resolve().parent
TITLE='[SONGPA-PRODUCTION-BUILD] 20261014'
BRANCH='source/seoul-songpa-production-successor-20261014'
PREDECESSOR='823c99cd8e5162e5890d24df1b89a2aadcb145a3'
ACCESSIBILITY_PREVIEW_REVISION='34c78310942910c9622784680cedcbfbb5dbf898'
ACCESSIBILITY_PREVIEW_TREE='4e37a2443812324d78bc52c018a7a3c470eb211f'
PREVIEW_MANIFEST_SHA='a8a6aaf45a2d69a344fa64fe0722770c5bfab7624fda8eeb93808d7d42687cce'
PREVIEW_EQUIVALENCE_SHA='ad9cba4a5fd3e23c3e182c1e2721c1ed52442caf1912d188310365ff7fa437e4'
ORIGIN='https://seoul-songpa.fwith.kr'
HOSTNAME='seoul-songpa.fwith.kr'
WORKER='seoul-songpa-flower-guide'
MODIFIED=['astro.config.mjs', 'package.json', 'scripts/qa_songpa.py', 'scripts/test_songpa.py', 'src/layouts/BaseLayout.astro']
ADDED=['PRODUCTION_PREPARATION.md', 'public/39c4ed924bc6084c670a963c26d9f018.txt', 'scripts/songpa_release.mjs', 'scripts/songpa_release_output.py', 'scripts/test_songpa_release_output.py', 'scripts/write_songpa_release_files.mjs', 'tests/songpa-release.test.mjs']
INPUT_SHA='bd62488171b10f6b0441baa9598dcff99bafb3ee64339504d9119a128c0bae80'
RUNTIME_SHA='0f3acd7e99a91169fdafefac47ce1bfa8cd614d3a875beeee62dc48e898bc037'

def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n')

def load():
    raw=read(DIRECTORY/'production-source-contract.json');c=json.loads(raw)
    fixed=dict(schemaVersion=1,repository=REPOSITORY,sourceRoot=ROOT,sourceBranch=BRANCH,
               previewSourceRevision=PREDECESSOR,previewSourceManifestSha256=PREVIEW_MANIFEST_SHA,sourceFiles=76,
               accessibilityPreviewRevision=ACCESSIBILITY_PREVIEW_REVISION,accessibilityPreviewTree=ACCESSIBILITY_PREVIEW_TREE,
               modifiedPaths=MODIFIED,addedPaths=ADDED,frozenInputSha256=INPUT_SHA,frozenRuntimeSha256=RUNTIME_SHA)
    require(set(c)==set(fixed)|{'sourceRevision','sourceTree'},'source_contract_schema')
    require(all(json.dumps(c[k],sort_keys=True)==json.dumps(v,sort_keys=True) for k,v in fixed.items()),'source_contract_identity')
    require(re.fullmatch('[0-9a-f]{40}',c['sourceRevision']) and c['sourceRevision']!=PREDECESSOR
            and re.fullmatch('[0-9a-f]{40}',c['sourceTree']),'source_commit_tree_required')
    br=read(DIRECTORY/'production-binding.json');b=json.loads(br)
    expected=dict(schemaVersion=1,state='approved',repository=REPOSITORY,sourceRoot=ROOT,
        siteKey='seoul-songpa-flower-direct',hostname=HOSTNAME,origin=ORIGIN,worker=WORKER,
        previewSourceRevision=PREDECESSOR,frozenInputSha256=INPUT_SHA,frozenRuntimeSha256=RUNTIME_SHA,
        sourceRevision=c['sourceRevision'],sourceContractSha256=sha(raw),proof=output.PROOF,
        sitemapRoutes=output.ROUTES,htmlFiles=5,directoryRobots='noindex,follow',notFoundStatus=404,
        publicHttpVerified=False,indexNowSubmitted=False,
        approvals=dict(publication=True,hostBinding=True,indexNowProof=True))
    require(set(b)==set(expected)|{'authorizationEvidence'},'binding_schema')
    require(all(json.dumps(b[k],sort_keys=True)==json.dumps(v,sort_keys=True) for k,v in expected.items()),'exact_songpa_binding_required')
    require(re.fullmatch(r'https://github[.]com/joseungil-kr/fwith-site-factory/blob/[0-9a-f]{40}/docs/direct-seoul-songpa/production-authorization-20261014[.]json',b['authorizationEvidence']),'approval_reference_required')
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
    raw=read(DIRECTORY/'preview-equivalence.json');require(sha(raw)==PREVIEW_EQUIVALENCE_SHA,'preview_equivalence_bytes_changed')
    e=json.loads(raw)
    require(e['sourceScope']=='local-accessibility-successor' and e['sourceManifestSha256']==PREVIEW_MANIFEST_SHA and e['remoteRunId'] is None and e['browserVerified'] is False,'reviewed_preview_identity_required')
    require(len(e['htmlBodyComparisons'])==5 and len(e['staticAssetsSha256'])==13,'equivalence_denominator')
    require({row['path'] for row in e['htmlBodyComparisons']}==set(output.FILES),'equivalence_route_identity')
    for row in e['htmlBodyComparisons']:
        match=re.search(rb'<body[ >][\s\S]*',read(dist/row['path']))
        require(match and sha(match.group())==row['sha256'],'reviewed_body_changed:'+row['path'])
    for name,digest in e['staticAssetsSha256'].items():require(sha(read(dist/name))==digest,'reviewed_visual_asset_changed:'+name)
    return dict(previewEvidence='local-accessibility-successor',remotePreviewRunVerified=False,htmlBodiesByteIdentical=5,visualAssetsByteIdentical=13)


def source(checkout,phase,env):
    c,b,binding_sha=load();environment(c,binding_sha,env)
    require(phase in {'prebuild','postbuild'},'invalid_phase')
    checkout=Path(checkout).resolve();root=checkout/ROOT
    require(git(checkout,'rev-parse','HEAD').decode().strip()==c['sourceRevision'],'source_revision_mismatch')
    require(git(checkout,'rev-parse','HEAD:'+ROOT).decode().strip()==c['sourceTree'],'source_tree_mismatch')
    if phase=='prebuild':require(not git(checkout,'status','--porcelain','--untracked-files=all').strip(),'source_checkout_not_clean')
    entries=[e for e in git(checkout,'ls-tree','-r','-z','HEAD','--',ROOT).split(b'\0') if e]
    require(len(entries)==76,'source_file_count_mismatch')
    for entry in entries:
        meta,name=entry.split(b'\t');mode,kind,blob=meta.decode().split();name=name.decode()
        require(mode=='100644' and kind=='blob' and name.startswith(ROOT+'/'),'source_entry_invalid')
        data=read(checkout/name)
        require(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob,'source_bytes_changed:'+name)
    source_inventory(root,[entry.split(b'\t')[1].decode().removeprefix(ROOT+'/') for entry in entries])
    baseline_raw=read(DIRECTORY/'preview-source-manifest.json');require(sha(baseline_raw)==PREVIEW_MANIFEST_SHA,'preview_manifest_changed')
    baseline={row['path']:row for row in json.loads(baseline_raw)}
    actual={entry.split(b'\t')[1].decode().removeprefix(ROOT+'/'):sha(read(checkout/entry.split(b'\t')[1].decode())) for entry in entries}
    require(sorted(set(actual)-set(baseline))==ADDED and not set(baseline)-set(actual),'source_delta_added_removed_mismatch')
    require(sorted(name for name in baseline if baseline[name]['sha256']!=actual[name])==MODIFIED,'source_delta_modified_mismatch')
    require(sha(read(root/'src/data/input-manifest.json'))==INPUT_SHA and sha(read(root/'src/data/songpa-runtime.json'))==RUNTIME_SHA,'frozen_input_runtime_changed')
    require(read(root/'scripts/songpa_release_output.py')==read(DIRECTORY/'production_output.py'),'source_control_output_validator_mismatch')
    accessibility_contract(read(root/'src/layouts/BaseLayout.astro').decode(),read(root/'src/styles/global.css').decode())
    result=dict(state=phase+'_production_source_verified',sourceRevision=c['sourceRevision'],sourceTree=c['sourceTree'],sourceFiles=76,providerCredentialsUsed=False,publicationExecuted=False,publicHTTPVerified=False)
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
