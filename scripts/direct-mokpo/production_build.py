"""Pinned Mokpo build and artifact gates. Never contact a provider or publish."""
import argparse,hashlib,json,os,re,shutil,subprocess
from html.parser import HTMLParser
from pathlib import Path
import production_output as output
DIRECTORY=Path(__file__).resolve().parent
REPOSITORY='joseungil-kr/fwith-site-factory';OWNER='joseungil-kr'
ROOT='site-factory/mokpo-flower';BRANCH='source/mokpo-production-successor-20261015'
TITLE='[MOKPO-PRODUCTION-BUILD] 20261015'
HOSTNAME='mokpo.fwith.kr';ORIGIN='https://'+HOSTNAME;WORKER='mokpo-flower-guide'
INPUT_SHA='90f43c2fb14ca8756453f1b2af1339f68e1ec24d3b38cb06f09a4cf73fd12f44'
PRIVATE_TREE_SHA='271e834444f31e479024764d3ae9f30fbb6816f89a90ce41458a654e31877311'
# Generated from the finished source/reviewed local manifests, not guessed remote commits.
PREVIEW_MANIFEST_SHA='d2b5a3762febb6f935c5fe7b7af9f23b7b4adb98653dacca6faef79246d9c957';PREVIEW_EQUIVALENCE_SHA='dd06f2817ed14e2a7eb49477fc05f7422f02c51a3c768dd79bde5f6e223ec18f';BOUNDED_CONTRACT_SHA='29c01a09a26786e5ad302b4e6334001c05c403810a36b358edb69fd5a1b0c948'
CONTENT_REVIEW_BINDING_SHA='5e499299e803d9168ebe24a26749683678a6209d6174148a67572ffc95b6a15b'
SOURCE_FILES=81;MODIFIED=['package.json'];ADDED=['PRODUCTION_PREPARATION.md', 'release-tests/mokpo-release.test.mjs', 'release/bounded-contract.json', 'release/existing-indexnow-proof.txt', 'release/private-source-manifest.json', 'scripts/build_mokpo_release.mjs', 'scripts/mokpo_release.mjs', 'scripts/mokpo_release_output.py', 'scripts/test_mokpo_release_output.py', 'scripts/write_mokpo_release_files.mjs']
def require(ok,reason):
 if not ok:raise ValueError(reason)
def read(p):
 p=Path(p);require(p.is_file() and not p.is_symlink(),'regular_file_required');return p.read_bytes()
def sha(data):return hashlib.sha256(data).hexdigest()
def same(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'))==json.dumps(b,sort_keys=True,separators=(',',':'))
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def git(checkout,*args):return subprocess.check_output(['git','-C',str(checkout),*args],stderr=subprocess.STDOUT)
def contract_template():return dict(schemaVersion=1,repository=REPOSITORY,sourceRoot=ROOT,sourceBranch=BRANCH,previewSourceManifestSha256=PREVIEW_MANIFEST_SHA,frozenPrivateTreeSha256=PRIVATE_TREE_SHA,sourceFiles=SOURCE_FILES,modifiedPaths=MODIFIED,addedPaths=ADDED,frozenInputSha256=INPUT_SHA,boundedContractSha256=BOUNDED_CONTRACT_SHA,contentReviewBindingSha256=CONTENT_REVIEW_BINDING_SHA)
def binding_template(c):return dict(schemaVersion=1,state='approved',repository=REPOSITORY,sourceRoot=ROOT,siteKey='mokpo-flower-direct',hostname=HOSTNAME,origin=ORIGIN,worker=WORKER,previewSourceRevision=c['previewSourceRevision'],frozenInputSha256=INPUT_SHA,frozenPrivateTreeSha256=PRIVATE_TREE_SHA,sourceRevision=c['sourceRevision'],proof=output.PROOF,sitemapRoutes=output.ROUTES,htmlFiles=4,directoryRobots='noindex,follow',notFoundStatus=404,publicHttpVerified=False,indexNowSubmitted=False,boundedContractSha256=BOUNDED_CONTRACT_SHA,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED',approvals=dict(publication=True,hostBinding=True,indexNowProof=True))
def load():
 raw=read(DIRECTORY/'production-source-contract.json');c=json.loads(raw);fixed=contract_template()
 require(set(c)==set(fixed)|{'sourceRevision','sourceTree','previewSourceRevision','frozenPreviewTree'},'source_contract_schema')
 require(all(same(c[k],v) for k,v in fixed.items()),'source_contract_identity')
 for k in ['sourceRevision','sourceTree','previewSourceRevision','frozenPreviewTree']:require(isinstance(c[k],str) and re.fullmatch('[0-9a-f]{40}',c[k]),'verified_full_commit_tree_required')
 require(c['sourceRevision']!=c['previewSourceRevision'],'production_successor_required')
 br=read(DIRECTORY/'production-binding.json');b=json.loads(br);expected={**binding_template(c),'sourceContractSha256':sha(raw)}
 require(set(b)==set(expected)|{'authorizationEvidence'},'binding_schema')
 require(all(same(b[k],v) for k,v in expected.items()),'exact_mokpo_binding_required')
 require(isinstance(b['authorizationEvidence'],str) and re.fullmatch(r'https://github[.]com/joseungil-kr/fwith-site-factory/blob/[0-9a-f]{40}/docs/direct-mokpo/production-authorization-20261015[.]json',b['authorizationEvidence']),'approval_reference_required')
 require(sha(read(DIRECTORY/'bounded-contract.json'))==BOUNDED_CONTRACT_SHA,'bounded_scope_contract_changed')
 cr=read(DIRECTORY/'content-review-binding.json');require(sha(cr)==CONTENT_REVIEW_BINDING_SHA,'content_review_binding_changed')
 for row in json.loads(cr)['files']:
  require(row['path'].startswith('docs/direct-mokpo/content-review-20261015/') and '..' not in Path(row['path']).parts,'content_review_path_invalid')
  evidence=read(DIRECTORY.parents[1]/row['path']);require(sha(evidence)==row['sha256'] and len(evidence)==row['bytes'],'content_review_bytes_changed')
 return c,b,sha(br)
def select(c,binding_sha,env,event):
 require(env.get('GITHUB_REPOSITORY')==REPOSITORY and env.get('GITHUB_REF')=='refs/heads/main','owner_main_required')
 require(env.get('GITHUB_ACTOR')==OWNER and env.get('GITHUB_TRIGGERING_ACTOR')==OWNER and env.get('GITHUB_RUN_ATTEMPT')=='1','owner_first_attempt_required')
 require(env.get('GITHUB_EVENT_NAME')=='issues' and event.get('action')=='opened','opened_issue_required')
 require(re.fullmatch('[0-9a-f]{40}',env.get('GITHUB_SHA','')),'control_revision_required')
 repo,issue=event.get('repository',{}),event.get('issue',{})
 require(repo.get('full_name')==REPOSITORY and repo.get('owner',{}).get('login')==OWNER and repo.get('owner',{}).get('type')=='User','repository_owner_mismatch')
 require(issue.get('title')==TITLE and issue.get('user',{}).get('login')==OWNER,'exact_issue_required')
 raw=issue.get('body');require(isinstance(raw,str) and len(raw)<2048,'invalid_body');body=json.loads(raw)
 expected=dict(schemaVersion=1,mode='production-build-only',source_branch=BRANCH,source_revision=c['sourceRevision'],expected_control_revision=env['GITHUB_SHA'],binding_sha256=binding_sha)
 require(same(body,expected),'exact_request_required')
 return dict(state='pinned_production_build_selected',sourceRevision=c['sourceRevision'],sourceBranch=BRANCH,controlRevision=env['GITHUB_SHA'],bindingSha256=binding_sha,publicationExecuted=False)
def environment(c,binding_sha,env):
 require(env.get('SITE_RELEASE_MODE')=='production' and env.get('SITE_INDEXABLE')=='true' and env.get('SITE_URL')==ORIGIN and env.get('SITE_FACTORY_REVISION')==c['sourceRevision'],'production_environment_mismatch')
 require(Path(env.get('SITE_RELEASE_BINDING_PATH','')).resolve()==DIRECTORY/'production-binding.json' and env.get('SITE_RELEASE_BINDING_SHA256')==binding_sha,'exact_control_binding_required')
 require(not env.get('CLOUDFLARE_API_TOKEN') and not env.get('CLOUDFLARE_ACCOUNT_ID'),'provider_credentials_forbidden')
def customer_text_sha(body):
 class Text(HTMLParser):
  def __init__(self):super().__init__();self.text=[]
  def handle_data(self,data):self.text.append(data)
 parser=Text();parser.feed(body.decode('utf-8'));return sha(''.join(parser.text).encode('utf-8'))
def normalize_focus_body(body):
 old=b'<main id="main-content">';new=b'<main id="main-content" tabindex="-1">'
 require(body.count(new)==1 and old not in body,'exact_focus_attribute_required')
 return body.replace(new,old,1)
def equivalence(dist):
 raw=read(DIRECTORY/'preview-equivalence.json');require(sha(raw)==PREVIEW_EQUIVALENCE_SHA,'preview_equivalence_bytes_changed');e=json.loads(raw)
 require(e['sourceScope']=='frozen-private-preview' and e['sourceManifestSha256']==PREVIEW_MANIFEST_SHA and e['remoteRunId'] is None and e['browserVerified'] is False,'reviewed_preview_identity_required')
 require(len(e['htmlBodyComparisons'])==4 and len(e['staticAssetsSha256'])==9,'equivalence_denominator')
 require({r['path'] for r in e['htmlBodyComparisons']}==set(output.FILES),'equivalence_route_identity')
 require(e.get('allowedGeneratedBodyChange')=={'from':'<main id="main-content">','to':'<main id="main-content" tabindex="-1">','occurrencesPerHTML':1},'undeclared_body_normalization')
 for row in e['htmlBodyComparisons']:
  match=re.search(rb'<body[ >][\s\S]*',read(Path(dist)/row['path']));require(match,'missing_body:'+row['path'])
  body=match.group();require(sha(normalize_focus_body(body))==row['sha256'],'reviewed_body_changed:'+row['path'])
  require(customer_text_sha(body)==row['customerTextSha256'],'customer_text_projection_changed:'+row['path'])
 for name,digest in e['staticAssetsSha256'].items():require(sha(read(Path(dist)/name))==digest,'reviewed_visual_asset_changed:'+name)
 return dict(previewEvidence='frozen-private-preview',remotePreviewRunVerified=False,htmlBodiesIdenticalAfterDeclaredFocusAttributeNormalization=4,customerTextAndStructureOtherwiseByteIdentical=True,customerTextProjectionsByteIdentical=4,visualAssetsByteIdentical=9)
def source(checkout,phase,env):
 c,b,digest=load();environment(c,digest,env);require(phase in {'prebuild','postbuild'},'invalid_phase')
 checkout=Path(checkout).resolve();root=checkout/ROOT
 require(git(checkout,'rev-parse','HEAD').decode().strip()==c['sourceRevision'],'source_revision_mismatch')
 require(git(checkout,'rev-parse','HEAD:'+ROOT).decode().strip()==c['sourceTree'],'source_tree_mismatch')
 require(git(checkout,'rev-parse',c['previewSourceRevision']+':'+ROOT).decode().strip()==c['frozenPreviewTree'],'predecessor_tree_mismatch')
 git(checkout,'merge-base','--is-ancestor',c['previewSourceRevision'],c['sourceRevision'])
 if phase=='prebuild':require(not git(checkout,'status','--porcelain','--untracked-files=all').strip(),'source_checkout_not_clean')
 entries=[e for e in git(checkout,'ls-tree','-r','-z','HEAD','--',ROOT).split(b'\0') if e];require(len(entries)==SOURCE_FILES,'source_file_count_mismatch');actual={}
 for entry in entries:
  meta,name=entry.split(b'\t');mode,kind,blob=meta.decode().split();name=name.decode();require(mode=='100644' and kind=='blob' and name.startswith(ROOT+'/'),'source_entry_invalid')
  data=read(checkout/name);require(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob,'source_bytes_changed:'+name);actual[name.removeprefix(ROOT+'/')]=sha(data)
 raw=read(DIRECTORY/'preview-source-manifest.json');require(sha(raw)==PREVIEW_MANIFEST_SHA,'preview_manifest_changed');baseline={r['path']:r for r in json.loads(raw)}
 require(sorted(set(actual)-set(baseline))==ADDED and not set(baseline)-set(actual),'source_delta_added_removed_mismatch')
 require(sorted(n for n in baseline if baseline[n]['sha256']!=actual[n])==MODIFIED,'source_delta_modified_mismatch')
 for name,row in baseline.items():require(sha(git(checkout,'show',c['previewSourceRevision']+':'+ROOT+'/'+name))==row['sha256'],'private_predecessor_bytes_changed:'+name)
 require(read(root/'scripts/mokpo_release_output.py')==read(DIRECTORY/'production_output.py'),'source_control_output_validator_mismatch')
 require(read(root/'release/bounded-contract.json')==read(DIRECTORY/'bounded-contract.json'),'source_control_scope_mismatch')
 require(read(root/'release/private-source-manifest.json')==raw,'source_control_baseline_mismatch')
 result=dict(state=phase+'_production_source_verified',sourceRevision=c['sourceRevision'],sourceTree=c['sourceTree'],sourceFiles=SOURCE_FILES,providerCredentialsUsed=False,publicationExecuted=False,publicHTTPVerified=False,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED')
 if phase=='postbuild':result.update(output.inspect_dist(root/'dist',dict(mode='production',indexable=True,origin=ORIGIN,revision=c['sourceRevision'])));result['previewEquivalence']=equivalence(root/'dist')
 return result
def package(checkout,result,env):
 require(env.get('NATIVE_GATES_PASSED')=='true','native_preview_and_production_gates_required');c,b,digest=load();release=Path('release');release.mkdir(exist_ok=False);shutil.copytree(Path(checkout)/ROOT/'dist',release/'dist')
 manifest=dict(schemaVersion=1,repository=REPOSITORY,sourceBranch=BRANCH,sourceRoot=ROOT,revision=c['sourceRevision'],controlRevision=env['GITHUB_SHA'],runId=env['GITHUB_RUN_ID'],origin=ORIGIN,worker=WORKER,indexable=True,bindingSha256=digest,sourceContractSha256=sha(read(DIRECTORY/'production-source-contract.json')),files=result['files']);save(release/'release.json',manifest)
 result.update(releaseManifestSha256=sha(read(release/'release.json')),outputFilesSha256=sha(json.dumps(result['files'],sort_keys=True,separators=(',',':')).encode()),nativePreviewRegressionPassed=True,productionBuildAndMutationQaPassed=True,mobileAndDesktopPixelsVerified=False,productionLaunchGateStatus='PENDING_INDEPENDENT_ASSESSMENT_AND_PIXELS')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['select','prebuild','postbuild']);p.add_argument('--checkout');p.add_argument('--report',required=True);p.add_argument('--package',action='store_true');a=p.parse_args();c,b,digest=load()
 if a.phase=='select':
  result=select(c,digest,os.environ,json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text()))
  with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('source_revision='+c['sourceRevision']+'\nbinding_sha256='+digest+'\n')
 else:
  result=source(a.checkout,a.phase,os.environ)
  if a.package:require(a.phase=='postbuild','package_requires_postbuild');package(a.checkout,result,os.environ)
 save(a.report,result);print(json.dumps({k:v for k,v in result.items() if k!='files'},sort_keys=True))
