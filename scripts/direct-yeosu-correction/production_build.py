"""Trusted separate source88/output18 read-only QA gate. No deploy, provider, IndexNow.
Historical source85 and production controls remain unchanged. Producer legacy flags
are compatibility input only: this namespace explicitly grants no publication.
"""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
DIRECTORY=Path(__file__).resolve().parent
REPOSITORY='joseungil-kr/fwith-site-factory';OWNER='joseungil-kr'
ROOT='site-factory/yeosu-flower'
BUILD_ROOT=ROOT+'/portable/yeosu-portable-build-inputs-20261015/yeosu-local-implementation-20261015/candidate'
BRANCH='source/yeosu-product-policy-correction-20261017'
TITLE='[YEOSU-POLICY-CORRECTION-QA-R4] 20261017'
ORIGIN='https://yeosu.fwith.kr';BASE='472c54a40cf873c925ed2d314748351381ee8682'
BASE_TREE='d75e698601a4e01cfc0d6f784ceeb408cd624d5a'
FROZEN_SHA='6be75320887c8deaf9571da8490daa7db62561970fe33b171e6a3fc6ee2caf85'
TRUSTED_MANIFEST_SHA='5719a6a0fd2dc5024eb3f28ba8995f15fc42c06a74a0885db0b0b8d8ab1e54fc'
SOURCE_SAVE_REVIEW_SHA='35e8f61466f7f13e00b628adc181839dd2cf4f7f76340ee258d6457e0950fd9c'
R3_SPEC_SHA='43c3295fc63b3e4ab81019c086bf07eb1c74629f37cfb8a525d5948e4e074fc5'
R4_SPEC_SHA='646c1ee6f82b96a2feac4c2e1ea8692857b2f93a7047708396987a084a4bce4f'
R4_SOURCE_REVIEW_SHA='26b9ce71b5b5024c53056504ed1fed06e5070da689c34535e9834e0a75413d22'
R4_SOURCE_REVIEW_INPUT_SHA='f866bd6223160cb940cdb8ee95db2bca4bd4c54ce0c1dfd16efcc1c502afd8e5'
R3_SOURCE='97382615bf24f164f097f323295f495b84561f8d'
R4_MODIFIED=['release-adapter/correction/apply_policy_correction.py','release-adapter/correction/patch-spec.json']
MODIFIED=['release-adapter/scripts/build_yeosu_release.mjs']
ADDED=['release-adapter/correction/apply_policy_correction.py','release-adapter/correction/baseline-output-manifest.json','release-adapter/correction/patch-spec.json']
PROVIDER_PREFIXES=('CLOUDFLARE_','CF_API_','AWS_','AZURE_','VERCEL_','NETLIFY_','FLY_API_','DIGITALOCEAN_','GOOGLE_APPLICATION_CREDENTIALS','GCP_')
def require(ok,msg):
 if not ok:raise ValueError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p);require(p.is_file() and not p.is_symlink(),'regular_file_required:'+str(p));return p.read_bytes()
def data(name):return json.loads(read(DIRECTORY/name))
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def same(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'))==json.dumps(b,sort_keys=True,separators=(',',':'))
def git(checkout,*args):return subprocess.check_output(['git','-C',str(checkout),*args],stderr=subprocess.STDOUT)
def no_provider(env):require(not any(v and k.startswith(PROVIDER_PREFIXES) for k,v in env.items()),'provider_credentials_forbidden')
def safe_name(name):return isinstance(name,str) and not Path(name).is_absolute() and '..' not in Path(name).parts and '\\' not in name

def frozen():
 raw=read(DIRECTORY/'trusted-frozen-files.json');require(sha(raw)==TRUSTED_MANIFEST_SHA,'trusted_frozen_manifest_changed')
 for name,row in json.loads(raw).items():
  require(safe_name(name),'unsafe_trusted_path');b=read(DIRECTORY/name)
  require(sha(b)==row['sha256'] and len(b)==row['bytes'],'frozen_control_changed:'+name)
 require(sha(read(DIRECTORY/'frozen-review-manifest.r2.json'))==FROZEN_SHA,'frozen_r2_changed')
 source=data('expected-source88.json');original=data('expected-original-source85.json');expected=data('expected-output18.json')
 require(sha(read(DIRECTORY/'frozen-source-save-review.r3.json'))==SOURCE_SAVE_REVIEW_SHA,'frozen_r3_source_save_changed')
 require(sha(read(DIRECTORY/'r4-source-review.json'))==R4_SOURCE_REVIEW_SHA and sha(read(DIRECTORY/'frozen-source-save-review.r4.json'))==R4_SOURCE_REVIEW_INPUT_SHA,'frozen_r4_saved_source_review_changed')
 require(sha(read(DIRECTORY/'r3-patch-spec.json'))==R3_SPEC_SHA,'r3_history_spec_changed')
 require(sha(read(DIRECTORY/'patch-spec.json'))==R4_SPEC_SHA,'r4_spec_changed')
 require(len(source)==88 and len(original)==85 and len(expected)==18,'exact_denominators_required')
 require(sorted(set(source)-set(original))==ADDED and not set(original)-set(source),'source_added_removed_delta')
 require(sorted(p for p in original if source[p]['sha256']!=original[p]['sha256'])==MODIFIED,'source_modified_delta')
 for row in data('private-source75.json'):
  require(source[row['path']]=={k:row[k] for k in ['bytes','sha256']},'frozen_private_source_changed')
 require(len(data('private-source75.json'))==75,'private75_required')
 prior_source=data('r3-expected-source88.json');layout_binding=data('r4-layout-binding.json')
 require(set(prior_source)==set(source),'r4_source_inventory_changed')
 require(sorted(p for p in source if source[p]!=prior_source[p])==R4_MODIFIED,'exact_r4_source_delta2_required')
 require(layout_binding['sourceChangedPaths']==R4_MODIFIED and layout_binding['sourceParentRevision']==R3_SOURCE and layout_binding['sourceFiles']==88 and layout_binding['sourceAddedPaths']==[] and layout_binding['sourceRemovedPaths']==[],'r4_layout_source_boundary')
 require(layout_binding['specSha256']==R4_SPEC_SHA and layout_binding['sourceApplySha256']==source[R4_MODIFIED[0]]['sha256'],'r4_layout_source_bytes')
 baseline=data('baseline-output-manifest.json');spec=data('patch-spec.json');prior_spec=data('r3-patch-spec.json')
 require(spec['operations']==prior_spec['operations'] and spec['resultHtmlSha256']==prior_spec['resultHtmlSha256'],'r3_policy_operations_must_remain_exact')
 layout=spec['layoutCorrection'];require(layout==layout_binding['layout'],'layout_contract_mismatch')
 oldcss='_astro/CopyPage.BgCFg6FO.css';rule=b'.copy-section h2{overflow-wrap:anywhere}\n'
 original_css=read(DIRECTORY/'original-assets/CopyPage.BgCFg6FO.css')
 require(sha(original_css)==baseline['files'][oldcss]==layout['sourceCSSSha256'],'original_css_bytes_required')
 newcss=original_css+rule;newname='_astro/CopyPage.yeosu-wrap-'+sha(newcss)[:16]+'.css'
 require(layout['scope']=='existing-copy-section-h2-wrap-only' and layout['appendCSS'].encode()==rule and layout['sourceCSS']==oldcss and layout['resultCSS']==newname and layout['resultCSSSha256']==sha(newcss),'exact_41byte_wrap_append_required')
 require(set(expected)==(set(baseline['files'])-{oldcss})|{newname},'exact_r4_output_inventory_required')
 require(layout['htmlFiles']==sorted(n for n in baseline['files'] if n.endswith('.html')) and layout['stylesheetReferencesPerHTML']==1,'exact_four_stylesheet_refs_required')
 prior_output=data('r3-expected-output18.json')
 for name,row in expected.items():
  if name.endswith('.html'):
   b=read(DIRECTORY/'original-html'/name);require(sha(b)==baseline['files'][name],'original_html_changed')
   for op in spec['operations']:
    if op['file']!=name:continue
    before,after=op['before'].encode(),op['after'].encode()
    require(b.count(before)==op['expectedOccurrences'],'reviewed_spec_occurrence_mismatch');b=b.replace(before,after)
   require(sha(b)==prior_output[name]['sha256'],'r3_expected_html_changed')
   oldtag=('<link rel="stylesheet" href="/'+oldcss+'">').encode();newtag=('<link rel="stylesheet" href="/'+newname+'">').encode()
   require(b.count(oldtag)==1,'original_stylesheet_exact_one');b=b.replace(oldtag,newtag)
   require(sha(b)==row['sha256'] and len(b)==row['bytes'],'reviewed_r4_expected_output_changed')
  elif name==newname:require(row=={'bytes':len(newcss),'sha256':sha(newcss)},'new_css_expectation_changed')
  else:require(row==prior_output[name] and row['sha256']==baseline['files'][name],'nonhtml13_expected_changed')
 require({n:r['sha256'] for n,r in expected.items()}==layout['resultNormalizedFilesSha256'],'r4_output_hash_set_changed')
 return source,original,expected

def load_ui_expectations():
 frozen();ui=data('ui-expectations.json');require(ui['frozenInputManifestSha256']==FROZEN_SHA,'ui_frozen_input_mismatch')
 require(len(ui['pages'])==4 and len(ui['spec']['faqs'])==4 and ui['spec']['productCards']==[],'ui_denominators')
 return ui['pages'],ui['spec']

def load():
 frozen();c=data('correction-source-contract.json');scope=data('qa-scope.json')
 fixed=dict(schemaVersion=1,repository=REPOSITORY,sourceRoot=ROOT,buildRoot=BUILD_ROOT,sourceBranch=BRANCH,baselineSourceRevision=BASE,baselineSourceTree=BASE_TREE,frozenReviewManifestSha256=FROZEN_SHA,frozenSourceSaveReviewSha256=SOURCE_SAVE_REVIEW_SHA,frozenSourceSaveReviewR4Sha256=R4_SOURCE_REVIEW_INPUT_SHA,savedSourceReviewR4Sha256=R4_SOURCE_REVIEW_SHA,correctionSpecSha256=R4_SPEC_SHA,layoutCorrection='existing-copy-section-h2-wrap-only',r3SourceRevision=R3_SOURCE,r4ChangedPaths=R4_MODIFIED,sourceFiles=88,outputFiles=18,modifiedPaths=MODIFIED,addedPaths=ADDED,scope='READONLY_QA_ONLY_NO_PUBLICATION_NO_INDEXNOW')
 require(set(c)==set(fixed)|{'sourceRevision','sourceTree','sourceParentRevision'},'correction_contract_schema')
 require(all(same(c[k],v) for k,v in fixed.items()),'correction_contract_identity')
 r4=data('r4-layout-binding.json')
 require(r4['state']=='SAVED_R4_SOURCE_BOUND','actual_r4_source_pin_pending')
 require(c['sourceRevision']==r4['sourceRevision'] and c['sourceTree']==r4['sourceTree'] and c['sourceParentRevision']==R3_SOURCE,'independently_saved_r4_source_binding_changed')
 require(c['sourceRevision']!=R3_SOURCE,'historical_r3_cannot_be_r4')
 review=data('r4-source-review.json')
 require(review['verdict']==r4['savedSourceReviewState']=='SAVED_R4_SOURCE_AND_LOCAL_PRODUCER_ACCEPTED_NATIVE_VISUAL_QA_REQUIRED' and review['sourceRevision']==c['sourceRevision'] and review['sourceProjectTree']==c['sourceTree'] and review['soleParent']==c['sourceParentRevision'],'saved_r4_independent_review_identity')
 require(review['reviewInputManifest']['sha256']==r4['savedSourceReviewInputSha256']==R4_SOURCE_REVIEW_INPUT_SHA and r4['savedSourceReviewSha256']==R4_SOURCE_REVIEW_SHA,'saved_r4_independent_review_digests')
 require(review['sourceSaveAccepted'] is True and review['actualSavedRevisionLocalProducerAccepted'] is True and all(review[k] is False for k in ['newNativeActionsVerified','newPixelsVerified','fullReleasePass','publicationAuthorized','providerAuthorized','indexNowAuthorized']),'source_review_must_not_grant_native_or_public_approval')
 for k in ['sourceRevision','sourceTree','sourceParentRevision']:require(isinstance(c[k],str) and re.fullmatch('[0-9a-f]{40}',c[k]),'actual_saved_source_binding_required')
 require(c['sourceRevision']!=BASE and c['sourceTree']!=BASE_TREE,'new_correction_source_required')
 require(scope=={'schemaVersion':1,'scope':'READONLY_QA_ONLY','providerOperationsAllowed':False,'publicationAuthorized':False,'indexNowSubmissionAllowed':False,'historicalBindingCompatibilityOnly':True},'qa_scope_mismatch')
 b=data('production-binding.json');expected=data('historical-production-binding.json')
 expected.update(sourceRevision=c['sourceRevision'],sourceContractSha256=sha(read(DIRECTORY/'correction-source-contract.json')))
 require(same(b,expected),'exact_qa_compatibility_binding_required')
 return c,b,sha(read(DIRECTORY/'production-binding.json'))

def select(c,binding_sha,env,event):
 no_provider(env)
 require(env.get('GITHUB_REPOSITORY')==REPOSITORY and env.get('GITHUB_REF')=='refs/heads/main','owner_main_required')
 require(env.get('GITHUB_ACTOR')==OWNER and env.get('GITHUB_TRIGGERING_ACTOR')==OWNER and env.get('GITHUB_RUN_ATTEMPT')=='1','owner_first_attempt_required')
 require(env.get('GITHUB_EVENT_NAME')=='issues' and event.get('action')=='opened','opened_issue_required')
 require(re.fullmatch('[0-9a-f]{40}',env.get('GITHUB_SHA','')),'exact_control_revision_required')
 repo,issue=event.get('repository',{}),event.get('issue',{})
 require(repo.get('full_name')==REPOSITORY and repo.get('owner',{}).get('login')==OWNER and repo.get('owner',{}).get('type')=='User','repository_owner_mismatch')
 require(issue.get('title')==TITLE and issue.get('user',{}).get('login')==OWNER and issue.get('state')=='open' and 'pull_request' not in issue,'exact_owner_issue_required')
 require(isinstance(issue.get('number'),int) and issue['number']>0,'issue_number_required')
 raw=issue.get('body');require(isinstance(raw,str) and len(raw)<2048,'invalid_body')
 body=json.loads(raw);expected=dict(schemaVersion=1,mode='yeosu-policy-correction-readonly-qa',source_branch=BRANCH,source_revision=c['sourceRevision'],expected_control_revision=env['GITHUB_SHA'],binding_sha256=binding_sha,frozen_review_manifest_sha256=FROZEN_SHA,correction_spec_sha256=R4_SPEC_SHA)
 require(same(body,expected),'exact_request_required')
 return dict(state='readonly_correction_qa_selected',issueNumber=issue['number'],sourceRevision=c['sourceRevision'],sourceBranch=BRANCH,controlRevision=env['GITHUB_SHA'],bindingSha256=binding_sha,publicationAuthorized=False,publicationExecuted=False,indexNowSubmitted=False)

def environment(c,digest,env):
 no_provider(env)
 require(env.get('SITE_RELEASE_MODE')=='production' and env.get('SITE_INDEXABLE')=='true' and env.get('SITE_URL')==ORIGIN and env.get('SITE_FACTORY_REVISION')==c['sourceRevision'],'qa_production_environment_mismatch')
 require(Path(env.get('SITE_RELEASE_BINDING_PATH','')).resolve()==DIRECTORY/'production-binding.json' and env.get('SITE_RELEASE_BINDING_SHA256')==digest,'exact_qa_binding_required')

def inspect_dist(dist,revision):
 require(isinstance(revision,str) and re.fullmatch('[0-9a-f]{40}',revision),'full_revision_required')
 expected=frozen()[2];dist=Path(dist);require(dist.is_dir() and not dist.is_symlink(),'dist_directory_required')
 require(not any(p.is_symlink() for p in dist.rglob('*')),'output_symlink_forbidden')
 files={p.relative_to(dist).as_posix():read(p) for p in dist.rglob('*') if p.is_file()}
 require(set(files)==set(expected),'exact_output18_inventory_required')
 result={}
 for name,b in files.items():
  raw=b
  if name.endswith('.html'):
   needle=('<meta name="site-factory-revision" content="'+revision+'">').encode()
   require(b.count(needle)==1 and len(re.findall(rb'<meta name="site-factory-revision"[^>]*>',b))==1,'exact_revision_meta_required:'+name)
   b=b.replace(needle,('<meta name="site-factory-revision" content="'+BASE+'">').encode())
  require(sha(b)==expected[name]['sha256'] and len(b)==expected[name]['bytes'],'frozen_corrected_output_mismatch:'+name)
  result[name]=sha(raw)
 return dict(files=result,outputFiles=18,htmlFiles=4,nonHtmlPreserved=13,imageFilesPreserved=7,notFoundContentPreserved=True,notFoundAllowedDelta=['revisionMeta','stylesheetHref'],layoutCorrection='existing-copy-section-h2-wrap-only',outputExpectationOrigin='Frozen reviewed original/spec, not observed candidate',mobileAndDesktopPixelsVerified=False,publicationAuthorized=False,publicationExecuted=False,indexNowSubmitted=False)

def source(checkout,phase,env):
 c,b,digest=load();environment(c,digest,env);require(phase in ['prebuild','postbuild'],'invalid_phase');checkout=Path(checkout).resolve()
 expected,baseline,_=frozen()
 require(git(checkout,'rev-parse','HEAD').decode().strip()==c['sourceRevision'],'source_revision_mismatch')
 require(git(checkout,'rev-parse','HEAD:'+ROOT).decode().strip()==c['sourceTree'],'source_tree_mismatch')
 require(git(checkout,'rev-parse',BASE+':'+ROOT).decode().strip()==BASE_TREE,'baseline_source_tree_changed')
 require(git(checkout,'rev-list','--parents','-n','1','HEAD').decode().split()==[c['sourceRevision'],c['sourceParentRevision']],'sole_exact_parent_required')
 git(checkout,'merge-base','--is-ancestor',BASE,c['sourceRevision'])
 require(git(checkout,'rev-parse',R3_SOURCE+':'+ROOT).decode().strip()==data('r3-source-contract.json')['sourceTree'],'r3_parent_tree_changed')
 require(sorted(git(checkout,'diff','--no-renames','--name-status',R3_SOURCE,'HEAD').decode().splitlines())==['M\t'+ROOT+'/'+p for p in R4_MODIFIED],'exact_r3_to_r4_whole_repo_delta2_required')
 status=git(checkout,'status','--porcelain','--untracked-files=all' if phase=='prebuild' else '--untracked-files=no')
 require(not status.strip(),'source_checkout_changed')
 wanted=sorted(['M\t'+ROOT+'/'+p for p in MODIFIED]+['A\t'+ROOT+'/'+p for p in ADDED])
 require(sorted(git(checkout,'diff','--no-renames','--name-status',BASE,'HEAD').decode().splitlines())==wanted,'exact_whole_repository_delta4_required')
 entries=[v for v in git(checkout,'ls-tree','-r','-z','HEAD','--',ROOT).split(b'\0') if v];require(len(entries)==88,'source88_required');actual={}
 for entry in entries:
  meta,name=entry.split(b'\t');mode,kind,blob=meta.decode().split();name=name.decode();require(mode=='100644' and kind=='blob' and name.startswith(ROOT+'/'),'source_entry_invalid')
  p=name.removeprefix(ROOT+'/');raw=read(checkout/name);require(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==blob,'tracked_blob_mismatch:'+p)
  actual[p]={'bytes':len(raw),'sha256':sha(raw)}
 require(same(actual,expected),'frozen_source88_changed')
 for name,row in data('r3-expected-source88.json').items():
  raw=git(checkout,'show',R3_SOURCE+':'+ROOT+'/'+name);require(sha(raw)==row['sha256'] and len(raw)==row['bytes'],'r3_predecessor_source88_changed:'+name)
 for name,row in baseline.items():
  raw=git(checkout,'show',BASE+':'+ROOT+'/'+name)
  require(sha(raw)==row['sha256'] and len(raw)==row['bytes'],'original_source85_changed:'+name)
 result=dict(state=phase+'_correction_source_verified',sourceRevision=c['sourceRevision'],sourceTree=c['sourceTree'],baselineSourceRevision=BASE,sourceFiles=88,unchangedSourceFiles=84,private75Preserved=True,exactModifiedPaths=MODIFIED,exactAddedPaths=ADDED,r3SourceRevision=R3_SOURCE,r4ExactModifiedPaths=R4_MODIFIED,savedSourceReviewR4Sha256=R4_SOURCE_REVIEW_SHA,providerCredentialsUsed=False,publicationAuthorized=False,publicationExecuted=False,publicHTTPVerified=False,indexNowSubmitted=False)
 if phase=='postbuild':result.update(inspect_dist(checkout/BUILD_ROOT/'dist',c['sourceRevision']))
 return result

def package(checkout,result,env):
 require(env.get('NATIVE_GATES_PASSED')=='true','native_regression_gates_required');c,b,digest=load()
 require(env.get('GITHUB_RUN_ATTEMPT')=='1' and re.fullmatch('[0-9a-f]{40}',env.get('GITHUB_SHA','')) and re.fullmatch('[0-9]+',env.get('GITHUB_RUN_ID','')),'actual_control_and_run_required')
 release=Path('release');release.mkdir(exist_ok=False);shutil.copytree(Path(checkout)/BUILD_ROOT/'dist',release/'dist')
 copied=inspect_dist(release/'dist',c['sourceRevision']);require(copied['files']==result['files'],'packaged_output_readback_mismatch')
 controls={p.relative_to(DIRECTORY).as_posix():sha(read(p)) for p in sorted(DIRECTORY.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
 manifest=dict(schemaVersion=1,scope='READONLY_QA_NOT_DEPLOYMENT_AUTHORITY',repository=REPOSITORY,sourceBranch=BRANCH,sourceRoot=ROOT,revision=c['sourceRevision'],sourceTree=c['sourceTree'],sourceFiles=88,controlRevision=env['GITHUB_SHA'],runId=env['GITHUB_RUN_ID'],runAttempt=env['GITHUB_RUN_ATTEMPT'],origin=ORIGIN,bindingSha256=digest,frozenReviewManifestSha256=FROZEN_SHA,correctionSpecSha256=R4_SPEC_SHA,savedSourceReviewR4Sha256=R4_SOURCE_REVIEW_SHA,sourceContractSha256=sha(read(DIRECTORY/'correction-source-contract.json')),files=result['files'],controls=controls,publicationAuthorized=False,indexNowSubmitted=False)
 save(release/'release.json',manifest)
 result.update(releaseManifestSha256=sha(read(release/'release.json')),nativeRegressionPassed=True,mobileAndDesktopPixelsVerified=False,pixelReview='PENDING_INDEPENDENT_REVIEW')

def main():
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['select','prebuild','postbuild']);p.add_argument('--checkout');p.add_argument('--report',required=True);p.add_argument('--package',action='store_true');a=p.parse_args();c,b,digest=load()
 if a.phase=='select':
  result=select(c,digest,os.environ,json.loads(read(os.environ['GITHUB_EVENT_PATH'])))
  if os.environ.get('GITHUB_OUTPUT'):
   with open(os.environ['GITHUB_OUTPUT'],'a') as out:out.write('source_revision='+c['sourceRevision']+'\nbinding_sha256='+digest+'\n')
 else:
  require(a.checkout,'checkout_required');result=source(a.checkout,a.phase,os.environ)
  if a.package:require(a.phase=='postbuild','package_postbuild_only');package(a.checkout,result,os.environ)
 save(a.report,result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
