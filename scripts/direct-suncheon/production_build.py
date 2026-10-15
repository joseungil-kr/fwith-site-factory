"""Pinned Suncheon build and artifact gates. Never contact a provider or publish."""
import argparse,hashlib,json,os,re,shutil,subprocess
from html.parser import HTMLParser
from pathlib import Path
import production_output as output
DIRECTORY=Path(__file__).resolve().parent
REPOSITORY='joseungil-kr/fwith-site-factory';OWNER='joseungil-kr'
ROOT='site-factory/suncheon-flower';BUILD_ROOT=ROOT+'/candidate';ADAPTER_ROOT=ROOT+'/release-adapter';BRANCH='source/suncheon-production-successor-20261015'
TITLE='[SUNCHEON-PRODUCTION-BUILD] 20261015'
HOSTNAME='suncheon.fwith.kr';ORIGIN='https://'+HOSTNAME;WORKER='suncheon-flower-guide'
INPUT_SHA='b4eb7bda5f666334286172fc1f8e95dbf72f7877b58a972813819d058d68add0'
PRIVATE_TREE_SHA='234d07643754d4411557ffbf6a417c3a4794b6a3a0d57fb34c3fb3de77a66371'
# Generated from the finished source/reviewed local manifests, not guessed remote commits.
PREVIEW_MANIFEST_SHA='a993c58fd81fb6adc7a4fcf97f2fd6685e3ab6cf9a72f116668a5d7e332a5141';PREVIEW_EQUIVALENCE_SHA='1fbdeb52f438a207a3c4c9636a1c6373616de0de989e3a93096bb24057d31623';BOUNDED_CONTRACT_SHA='d534df76b59b2304f226051b0688082770e0e1eb76f8d5fcd0bcf82abd9759a5'
CONTENT_REVIEW_BINDING_SHA='44755316d178e172ae87a394ec62abe1dd873f5b9835b5071b30086283bda0d7'
SOURCE_FILES=69;MODIFIED=[];ADDED=['release-adapter/README.ko.md', 'release-adapter/release-tests/suncheon-release.test.mjs', 'release-adapter/release/bounded-contract.json', 'release-adapter/release/existing-indexnow-proof.txt', 'release-adapter/release/preview-equivalence.json', 'release-adapter/release/private-source-manifest.json', 'release-adapter/scripts/build_suncheon_release.mjs', 'release-adapter/scripts/suncheon_adapter.py', 'release-adapter/scripts/suncheon_release.mjs', 'release-adapter/scripts/suncheon_release_output.py', 'release-adapter/scripts/test_suncheon_adapter.py', 'release-adapter/scripts/test_suncheon_release_output.py', 'release-adapter/scripts/test_suncheon_runner_output.py', 'release-adapter/scripts/write_suncheon_release_files.mjs']
def require(ok,reason):
 if not ok:raise ValueError(reason)
def read(p):
 p=Path(p);require(p.is_file() and not p.is_symlink(),'regular_file_required');return p.read_bytes()
def sha(data):return hashlib.sha256(data).hexdigest()
def same(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'))==json.dumps(b,sort_keys=True,separators=(',',':'))
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def git(checkout,*args):return subprocess.check_output(['git','-C',str(checkout),*args],stderr=subprocess.STDOUT)
def contract_template():return dict(schemaVersion=1,repository=REPOSITORY,sourceRoot=ROOT,buildRoot=BUILD_ROOT,sourceBranch=BRANCH,previewSourceManifestSha256=PREVIEW_MANIFEST_SHA,frozenPrivateTreeSha256=PRIVATE_TREE_SHA,sourceFiles=SOURCE_FILES,modifiedPaths=MODIFIED,addedPaths=ADDED,frozenInputSha256=INPUT_SHA,boundedContractSha256=BOUNDED_CONTRACT_SHA,contentReviewBindingSha256=CONTENT_REVIEW_BINDING_SHA)
def binding_template(c):return dict(schemaVersion=1,state='approved',repository=REPOSITORY,sourceRoot=ROOT,siteKey='suncheon-flower-direct',hostname=HOSTNAME,origin=ORIGIN,worker=WORKER,previewSourceRevision=c['previewSourceRevision'],frozenInputSha256=INPUT_SHA,frozenPrivateTreeSha256=PRIVATE_TREE_SHA,sourceRevision=c['sourceRevision'],proof=output.PROOF,sitemapRoutes=output.ROUTES,htmlFiles=4,directoryRobots='noindex,follow',notFoundStatus=404,publicHttpVerified=False,indexNowSubmitted=False,boundedContractSha256=BOUNDED_CONTRACT_SHA,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED',approvals=dict(publication=True,hostBinding=True,indexNowProof=True))
def load():
 raw=read(DIRECTORY/'production-source-contract.json');c=json.loads(raw);fixed=contract_template()
 require(set(c)==set(fixed)|{'sourceRevision','sourceTree','previewSourceRevision','frozenPreviewTree'},'source_contract_schema')
 require(all(same(c[k],v) for k,v in fixed.items()),'source_contract_identity')
 for k in ['sourceRevision','sourceTree','previewSourceRevision','frozenPreviewTree']:require(isinstance(c[k],str) and re.fullmatch('[0-9a-f]{40}',c[k]),'verified_full_commit_tree_required')
 require(c['sourceRevision']!=c['previewSourceRevision'],'production_successor_required')
 br=read(DIRECTORY/'production-binding.json');b=json.loads(br);expected={**binding_template(c),'sourceContractSha256':sha(raw)}
 require(set(b)==set(expected)|{'authorizationEvidence'},'binding_schema')
 require(all(same(b[k],v) for k,v in expected.items()),'exact_suncheon_binding_required')
 require(isinstance(b['authorizationEvidence'],str) and re.fullmatch(r'https://github[.]com/joseungil-kr/fwith-site-factory/blob/[0-9a-f]{40}/docs/direct-suncheon/production-authorization-20261015[.]json',b['authorizationEvidence']),'approval_reference_required')
 require(sha(read(DIRECTORY/'bounded-contract.json'))==BOUNDED_CONTRACT_SHA,'bounded_scope_contract_changed')
 cr=read(DIRECTORY/'content-review-binding.json');require(sha(cr)==CONTENT_REVIEW_BINDING_SHA,'content_review_binding_changed')
 for row in json.loads(cr)['files']:
  require(row['path'].startswith('docs/direct-suncheon/content-review-20261015/') and '..' not in Path(row['path']).parts,'content_review_path_invalid')
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
def exact_body(body):
 require(body.count(b'<main id="main-content" tabindex="-1">')==1,'exact_existing_focus_attribute_required')
 return body
def normalized_production_prefix(data):
 match=re.search(rb'<body[ >]',data);require(match,'body_start_required')
 prefix=data[:match.start()];pattern=rb'<meta name="site-factory-revision" content="[0-9a-f]{40}">'
 require(len(re.findall(pattern,prefix))==1,'exact_revision_prefix_required')
 return re.sub(pattern,b'<meta name="site-factory-revision" content="__REVISION__">',prefix,count=1)
def equivalence(dist):
 raw=read(DIRECTORY/'preview-equivalence.json');require(sha(raw)==PREVIEW_EQUIVALENCE_SHA,'preview_equivalence_bytes_changed');e=json.loads(raw)
 require(e['sourceScope']=='frozen-private-preview' and e['sourceManifestSha256']==PREVIEW_MANIFEST_SHA and e['remoteRunId'] is None and e['browserVerified'] is False,'reviewed_preview_identity_required')
 require(len(e['htmlBodyComparisons'])==4 and len(e['staticAssetsSha256'])==9,'equivalence_denominator')
 require({r['path'] for r in e['htmlBodyComparisons']}==set(output.FILES),'equivalence_route_identity')
 require(e.get('allowedGeneratedBodyChanges')==[],'body_modifications_forbidden')
 for row in e['htmlBodyComparisons']:
  match=re.search(rb'<body[ >][\s\S]*',read(Path(dist)/row['path']));require(match,'missing_body:'+row['path'])
  body=match.group();require(sha(exact_body(body))==row['sha256'],'reviewed_body_changed:'+row['path'])
  require(sha(normalized_production_prefix(read(Path(dist)/row['path'])))==row['productionPrefixNormalizedSHA256'],'reviewed_head_changed:'+row['path'])
  require(customer_text_sha(body)==row['customerTextSha256'],'customer_text_projection_changed:'+row['path'])
 for name,digest in e['staticAssetsSha256'].items():require(sha(read(Path(dist)/name))==digest,'reviewed_visual_asset_changed:'+name)
 return dict(previewEvidence='frozen-private-preview',remotePreviewRunVerified=False,htmlBodiesByteIdentical=4,htmlHeadPrefixesMatchDeclaredProductionTransform=4,customerTextAndStructureByteIdentical=True,customerTextProjectionsByteIdentical=4,visualAssetsByteIdentical=9)
def source(checkout,phase,env):
 c,b,digest=load();environment(c,digest,env);require(phase in {'prebuild','postbuild'},'invalid_phase')
 checkout=Path(checkout).resolve();root=checkout/ROOT;candidate=checkout/BUILD_ROOT;adapter=checkout/ADAPTER_ROOT
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
 require(read(adapter/'scripts/suncheon_release_output.py')==read(DIRECTORY/'production_output.py'),'source_control_output_validator_mismatch')
 require(read(adapter/'release/bounded-contract.json')==read(DIRECTORY/'bounded-contract.json'),'source_control_scope_mismatch')
 require(read(adapter/'release/private-source-manifest.json')==raw,'source_control_baseline_mismatch')
 result=dict(state=phase+'_production_source_verified',sourceRevision=c['sourceRevision'],sourceTree=c['sourceTree'],sourceFiles=SOURCE_FILES,providerCredentialsUsed=False,publicationExecuted=False,publicHTTPVerified=False,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED')
 if phase=='postbuild':result.update(output.inspect_dist(candidate/'dist',dict(mode='production',indexable=True,origin=ORIGIN,revision=c['sourceRevision'])));result['previewEquivalence']=equivalence(candidate/'dist')
 return result
def package(checkout,result,env):
 require(env.get('NATIVE_GATES_PASSED')=='true','native_preview_and_production_gates_required');c,b,digest=load();release=Path('release');release.mkdir(exist_ok=False);shutil.copytree(Path(checkout)/BUILD_ROOT/'dist',release/'dist')
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
