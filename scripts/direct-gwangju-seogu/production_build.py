"""Pinned Seogu build and artifact gates. Never contact a provider or publish."""
import argparse,hashlib,json,os,re,shutil,subprocess
from html.parser import HTMLParser
from pathlib import Path
import production_output as output
DIRECTORY=Path(__file__).resolve().parent
# Keep the exact source validator bytes but bind its baseline to this isolated control.
output.EQUIVALENCE_PATH=DIRECTORY/'preview-equivalence.json'
REPOSITORY='joseungil-kr/fwith-site-factory';OWNER='joseungil-kr'
ROOT='site-factory/gwangju-seogu-flower';BUILD_ROOT=ROOT+'/candidate';ADAPTER_ROOT=ROOT+'/release-adapter';BRANCH='source/gwangju-seogu-production-preparation-20261015'
TITLE='[GWANGJU-SEOGU-PRODUCTION-BUILD] 20261015'
HOSTNAME='gwangju-seogu.fwith.kr';ORIGIN='https://'+HOSTNAME;WORKER='gwangju-seogu-flower-guide'
INPUT_SHA='6747e2f571792e56f53b9b1e3759a4e703d05c27b37ef8ea0eda747e837943a6'
PRIVATE_TREE_SHA='bdb1d5457de356432b988b7e125cb2b7c8d504c854719d7483be78952623e27d'
ADAPTER_TREE_SHA='53598bce7a6c18fbf1b940cc994896a2479e3ea87dc2824e264be5a6e61da189'
SOURCE_TREE_SHA='0e7c01bb8a7d296580758f7bd4c8eea4d4d88f6aae3a8d83be19d429c5fb97a0'
SOURCE_FILES=79;PRIVATE_FILES=64;ADAPTER_FILES=15
PRIVATE_MANIFEST_SHA='5d354f324183cb10964715a6381cd13db1b5c4f0ea4d343a559b714d608074e7'
ADAPTER_MANIFEST_SHA='de9a59a5b31ccf2b3b79e3e099e3f1b23771d18859bf17e81a55bc3594775050'
SOURCE_MANIFEST_SHA='e01429266e1f45cc534c94b42446138c541384ab1b69202c394c16b1d041b94f'
PREVIEW_EQUIVALENCE_SHA='f5d58443bf5c1b4e61924f5dec5f859caabd86a7675f7a6b0e473686a9a0e7c4'
BOUNDED_CONTRACT_SHA='48207a1e0665aefca762ff9dd1f2f453833b8ebd43a10984ecadf18e73ba2ab5'
CONTENT_REVIEW_BINDING_SHA='52c769747a1ca9fe40561466646c754c9d4cbf9f2e9d5903ef3abe059652db55'
HELPER_SHA256={'bucheon_domain_attach.py': 'a8662dd6ff232c53b6c55f193553f134c7055ec80eca421b65bab9bedd220da3', 'goyang_domain.py': '8a30e0ea75758344a5ff92903ec0a9dbd1e4f2bff230cdf603ea871ca1bf9c68', 'indexnow_finalize.py': '55f5274d3fcc713e82fd8ce18e280447e68e9e460bc1ff3f9bf5cc683834935f'}
def require(ok,reason):
 if not ok:raise ValueError(reason)
def read(p):
 p=Path(p);require(p.is_file() and not p.is_symlink(),'regular_file_required');return p.read_bytes()
def sha(data):return hashlib.sha256(data).hexdigest()
def same(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'))==json.dumps(b,sort_keys=True,separators=(',',':'))
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def git(checkout,*args):return subprocess.check_output(['git','-C',str(checkout),*args],stderr=subprocess.STDOUT)
def contract_template():
 return dict(schemaVersion=1,repository=REPOSITORY,sourceRoot=ROOT,buildRoot=BUILD_ROOT,sourceBranch=BRANCH,privateSourceManifestSha256=PRIVATE_MANIFEST_SHA,adapterSourceManifestSha256=ADAPTER_MANIFEST_SHA,sourceManifestSha256=SOURCE_MANIFEST_SHA,frozenPrivateTreeSha256=PRIVATE_TREE_SHA,frozenAdapterTreeSha256=ADAPTER_TREE_SHA,frozenSourceTreeSha256=SOURCE_TREE_SHA,sourceFiles=SOURCE_FILES,privateFiles=PRIVATE_FILES,adapterFiles=ADAPTER_FILES,frozenInputSha256=INPUT_SHA,boundedContractSha256=BOUNDED_CONTRACT_SHA,contentReviewBindingSha256=CONTENT_REVIEW_BINDING_SHA)
def binding_template(c):
 return dict(schemaVersion=1,state='approved',repository=REPOSITORY,sourceRoot=ROOT,siteKey='gwangju-seogu-flower-direct',hostname=HOSTNAME,origin=ORIGIN,worker=WORKER,frozenInputSha256=INPUT_SHA,frozenPrivateTreeSha256=PRIVATE_TREE_SHA,sourceRevision=c['sourceRevision'],proof=output.PROOF,sitemapRoutes=output.ROUTES,htmlFiles=4,directoryRobots='noindex,follow',notFoundStatus=404,publicHttpVerified=False,indexNowSubmitted=False,boundedContractSha256=BOUNDED_CONTRACT_SHA,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED',approvals=dict(publication=True,hostBinding=True,indexNowProof=True))
def authorization_template(c):
 return dict(schemaVersion=1,recordType='user-authorization-not-readiness-proof',repository=REPOSITORY,sourceRoot=ROOT,siteKey='gwangju-seogu-flower-direct',hostname=HOSTNAME,origin=ORIGIN,worker=WORKER,sourceRevision=c['sourceRevision'],sourceTree=c['sourceTree'],approvedOperations=['source-and-control-storage','production-build-and-QA','publication-after-own-gates','existing-provider-first-host-binding-with-no-overrides','existing-proof-and-two-URL-IndexNow-after-public-HTTP','public-build-publish-and-receipt-issues'],publicIssuesApproved=True,crossRegionPublicationOrderRequired=False,ownQualityAndSafetyGatesRequired=True,noNewCredentialsOrPermissionChanges=True,noDomainOwnershipTransferOrOverride=True)
def public_issue_approval_evidence():
 return dict(approvedAtUTC='2026-10-15T18:24:17Z',approved=True,scope='remaining-171-planned-regions-public-github-qa-publish-indexnow-receipts',publicData=['site-url','commit','qa-and-receipt-results'],secretsExcluded=True)
def authorization(c,b):
 d=json.loads(read(DIRECTORY/'authorization-binding.json'))
 require(isinstance(d,dict) and set(d)=={'schemaVersion','path','sha256','revision','publicIssuesApproved'} and type(d['schemaVersion']) is int and d['schemaVersion']==1,'authorization_descriptor_schema')
 require(d['publicIssuesApproved'] is True,'public_issue_approval_required')
 require(d['path']=='docs/direct-gwangju-seogu/production-authorization-20261015.json' and re.fullmatch('[0-9a-f]{64}',d['sha256'] or '') and re.fullmatch('[0-9a-f]{40}',d['revision'] or ''),'pinned_authorization_required')
 raw=read(DIRECTORY.parents[1]/d['path']);require(sha(raw)==d['sha256'],'authorization_bytes_changed');a=json.loads(raw)
 expected=authorization_template(c);require(set(a)==set(expected)|{'authorizationEvidence'},'authorization_schema')
 require(all(same(a[k],v) for k,v in expected.items()),'exact_seogu_authorization_required')
 require(same(a['authorizationEvidence'],[public_issue_approval_evidence()]),'exact_public_safe_approval_evidence_required')
 require(b['authorizationEvidence']=='https://github.com/'+REPOSITORY+'/blob/'+d['revision']+'/'+d['path'],'approval_reference_required')
 return d

def manifest(name,digest,count,tree):
 raw=read(DIRECTORY/name);require(sha(raw)==digest,'frozen_manifest_changed:'+name);rows=json.loads(raw)
 require(isinstance(rows,list) and len(rows)==count and all(isinstance(row,dict) for row in rows),'manifest_denominator:'+name)
 paths=[row.get('path') for row in rows];require(all(isinstance(n,str) and n and not Path(n).is_absolute() and not any(p in {'.','..'} or p.startswith('.') for p in n.split('/')) and '\\' not in n for n in paths) and len(set(paths))==count,'manifest_path_invalid')
 require(sha(''.join(row['sha256']+'  '+row['path']+'\n' for row in sorted(rows,key=lambda r:r['path'])).encode())==tree,'manifest_tree_mismatch:'+name)
 for row in rows:require(re.fullmatch('[0-9a-f]{64}',row.get('sha256','')) and type(row.get('bytes')) is int and row['bytes']>0,'manifest_record_invalid')
 return {row['path']:row for row in rows}

def frozen_manifests():
 private=manifest('private-source-manifest.json',PRIVATE_MANIFEST_SHA,PRIVATE_FILES,PRIVATE_TREE_SHA)
 adapter=manifest('adapter-manifest.json',ADAPTER_MANIFEST_SHA,ADAPTER_FILES,ADAPTER_TREE_SHA)
 source=manifest('source-manifest.json',SOURCE_MANIFEST_SHA,SOURCE_FILES,SOURCE_TREE_SHA)
 require(not set(private)&set(adapter) and set(private)|set(adapter)==set(source),'split_manifest_inventory_mismatch')
 require(all(not n.startswith('release-adapter/') for n in private) and all(n.startswith('release-adapter/') for n in adapter),'split_manifest_scope_mismatch')
 for name,row in {**private,**adapter}.items():require(row['sha256']==source[name]['sha256'] and row['bytes']==source[name]['bytes'],'split_manifest_bytes_mismatch')
 return private,adapter,source

def verify_content_reviews():
 """Verify actual Seo-gu schemas, meanings and source-byte links without rewriting reviews."""
 raw=read(DIRECTORY/'content-review-binding.json');require(sha(raw)==CONTENT_REVIEW_BINDING_SHA,'content_review_binding_changed')
 binding=json.loads(raw)
 expected=dict(schemaVersion=1,region='seogu',namespace='gwangju-seogu',scope='retained-manuscript-and-local-code-output-reviews-not-production-pass',sourceTreeSHA256=SOURCE_TREE_SHA,sourceFiles=SOURCE_FILES,frozenPrivateTreeSha256=PRIVATE_TREE_SHA,inputSha256=INPUT_SHA,productionGatePassed=False,staticQualityIsProductionPass=False)
 require(set(binding)==set(expected)|{'copySHA256','renderPlanSHA256','metadataSHA256','customerReviewBindingSHA256','codeReviewBindingSHA256','files'} and all(same(binding[k],v) for k,v in expected.items()),'content_review_source_identity_mismatch')
 rows=binding['files'];require(type(rows) is list and rows and all(type(row) is dict and set(row)=={'path','originalPath','bytes','sha256'} for row in rows),'content_review_inventory_schema')
 originals={};docs={}
 for row in rows:
  name=row['path'];original=row['originalPath']
  require(type(name) is str and name.startswith('docs/direct-gwangju-seogu/content-review-20261015/') and '..' not in Path(name).parts and '\\' not in name,'content_review_path_invalid')
  require(type(original) is str and not Path(original).is_absolute() and '..' not in Path(original).parts and '\\' not in original and original not in originals and Path(name).name not in docs,'content_review_original_path_invalid')
  data=read(DIRECTORY.parents[1]/name);require(type(row['bytes']) is int and len(data)==row['bytes'] and sha(data)==row['sha256'],'content_review_bytes_changed')
  originals[original]=row;docs[Path(name).name]=(data,json.loads(data) if name.endswith('.json') else None)
 def doc(name):require(name in docs,'review_document_missing:'+name);return docs[name][1]
 def reference(ref,origin=None):
  require(type(ref) is dict and set(ref)=={'path','bytes','sha256'} and type(ref['bytes']) is int and ref['bytes']>0 and re.fullmatch('[0-9a-f]{64}',ref['sha256'] or ''),'review_reference_schema')
  row=originals.get(ref['path']);require(row is not None and (origin is None or ref['path']==origin) and ref['bytes']==row['bytes'] and ref['sha256']==row['sha256'],'review_reference_bytes_mismatch')
 def identity(obj):
  require(all(same(obj.get(k),v) for k,v in dict(schemaVersion=1,region='seogu',officialCode='12240',nationalOrder=32).items()),'review_region_identity_mismatch')
 def exact(obj,values,error):require(all(k in obj and same(obj[k],v) for k,v in values.items()),error)
 copy_review=doc('implementation-review-binding.json');manuscript=doc('independent-copy-review-r2.json');code=doc('implementation-code-review-binding.json');code_report=doc('independent-code-review.json')
 require(type(copy_review) is dict and set(copy_review)==set(['actualBrowserChecked', 'actualBuildChecked', 'actualHTMLChecked', 'actualPublicHTTPChecked', 'allowedNextStage', 'assessmentScope', 'assetManifest', 'bound18Review', 'coreHubLaunchStatus', 'customerCopy', 'customerCopySHA256', 'frozenAuthorManifest', 'fullLaunchStatus', 'guidanceSourceCommit', 'humanReview', 'independentReview', 'invalidatesOn', 'metadata', 'nationalOrder', 'officialCode', 'publicationEligible', 'purchaseIntentMetadataSHA256', 'region', 'renderChecklist', 'renderPlan', 'renderPlanSHA256', 'reviewedUTC', 'revision', 'schemaVersion', 'sourceCommit', 'sourceCommitBinding', 'visibleStrings']),'original_copy_binding_schema_required')
 require(type(manuscript) is dict and set(manuscript)==set(['actualBrowserChecked', 'actualBuildChecked', 'actualHTMLChecked', 'actualPublicHTTPChecked', 'assessmentScope', 'coreHubLaunchStatus', 'customerCopySHA256', 'directlyConfirmed', 'evidence', 'fullLaunchStatus', 'guidanceSourceCommit', 'judgments', 'mandatoryRevisions', 'nationalOrder', 'officialCode', 'privacy', 'publicationEligible', 'purchaseIntentMetadataSHA256', 'region', 'renderPlanSHA256', 'reviewedUTC', 'revision', 'schemaVersion', 'sourceCommit', 'toolReports', 'unverified', 'verdict']),'original_manuscript_schema_required')
 require(type(code) is dict and set(code)==set(['actualActionsChecked', 'actualBrowserChecked', 'actualLocalBuildChecked', 'actualPublicHTTPChecked', 'actualRemoteSourceChecked', 'actualStaticHTMLChecked', 'adapterTreeSHA256', 'assessmentScope', 'correctedClosureSHA256', 'customerCopySHA256', 'evidence', 'humanReview', 'independentCodeReview', 'invalidatesOn', 'mandatoryChangesRemaining', 'manuscriptBindingSHA256', 'manuscriptReviewSHA256', 'namespace', 'nationalOrder', 'officialCode', 'originalAssetImagesOpened', 'privateTreeSHA256', 'providerOwnershipChecked', 'publicationEligible', 'region', 'renderPlanSHA256', 'schemaVersion', 'sourceCommit', 'sourceCommitBinding', 'sourceFiles', 'sourceManifest', 'sourceTreeSHA256', 'verdict']),'original_code_binding_schema_required')
 for obj in [copy_review,manuscript,code,code_report]:identity(obj)
 require(sha(docs['implementation-review-binding.json'][0])==binding['customerReviewBindingSHA256'],'copy_review_binding_changed')
 require(sha(docs['implementation-code-review-binding.json'][0])==binding['codeReviewBindingSHA256'],'code_review_binding_changed')
 manuscript_scope=dict(assessmentScope='MANUSCRIPT_AND_RENDER_PLAN_ONLY',revision='seogu-copy-r2-20261015',customerCopySHA256=binding['copySHA256'],renderPlanSHA256=binding['renderPlanSHA256'],purchaseIntentMetadataSHA256=binding['metadataSHA256'],guidanceSourceCommit='33ff2bb8dc969e8e43399f593541db0fd9f7a11d',sourceCommit=None,actualHTMLChecked=False,actualBuildChecked=False,actualBrowserChecked=False,actualPublicHTTPChecked=False,publicationEligible=False,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED')
 for obj in [copy_review,manuscript]+[doc(n) for n in ['bounded-18-clause-review.json','a04-manuscript-assessment.json','render-checklist.json']]:
  identity(obj);exact(obj,manuscript_scope,'manuscript_scope_or_unverified_flags_changed')
 bounded=doc('bounded-18-clause-review.json');checklist=doc('render-checklist.json');a04=doc('a04-manuscript-assessment.json')
 exact(bounded,dict(checkCount=18,verdict='MANUSCRIPT_AND_SPEC_READY_FOR_IMPLEMENTATION_NOT_PRODUCTION_PASS'),'bounded_manuscript_scope_required')
 require(type(bounded['checks']) is list and len(bounded['checks'])==18 and len({r['id'] for r in bounded['checks']})==18 and all(r.get('productionStatus')=='PENDING_IMPLEMENTATION_AND_OUTPUT_VERIFICATION' and r.get('technicalOutputPoints') is None for r in bounded['checks']),'bounded_manuscript_is_not_production_review')
 exact(a04,dict(SEO=None,GEO=None,AEO=None),'a04_cannot_claim_technical_quality_scores')
 require(checklist['status']=='ALL_ACTUAL_OUTPUT_CHECKS_PENDING' and type(checklist['checks']) is list and len(checklist['checks'])==25 and all(r.get('status')=='PENDING_ACTUAL_OUTPUT' for r in checklist['checks']),'original_checklist_cannot_claim_actual_output')
 exact(manuscript,dict(verdict='MANUSCRIPT_AND_SPEC_READY_FOR_IMPLEMENTATION_NOT_PRODUCTION_PASS'),'manuscript_verdict_required')
 revisions=manuscript['mandatoryRevisions'];require(type(revisions) is list and len(revisions)==2 and {r.get('id') for r in revisions if type(r) is dict}=={'KST_SOURCE_DATE','A04_KEYWORD_METADATA'} and all(r.get('status')=='VERIFIED_FIXED' for r in revisions),'manuscript_required_revisions_unresolved')
 reference(copy_review['independentReview'],'seogu-customer-plan-review-20261015/independent-review-r2.json')
 reference(copy_review['bound18Review'],'seogu-customer-plan-review-20261015/bounded-18-clause-review.json')
 reference(copy_review['renderChecklist'],'seogu-customer-plan-review-20261015/render-checklist.json')
 reference(copy_review['humanReview'],'seogu-customer-plan-review-20261015/REVIEW.ko.md')
 source=manifest('source-manifest.json',SOURCE_MANIFEST_SHA,SOURCE_FILES,SOURCE_TREE_SHA)
 for key,filename in [('customerCopy','customer-copy.json'),('renderPlan','render-plan.json'),('metadata','purchase-intent-metadata.json'),('visibleStrings','visible-strings.json'),('assetManifest','asset-manifest.json'),('frozenAuthorManifest','review-input-manifest-r2.json')]:
  ref=copy_review[key];require(type(ref) is dict and set(ref)=={'path','bytes','sha256'} and type(ref['bytes']) is int and ref['path']=='seogu-customer-copy-20261015/'+filename,'copy_source_reference_schema')
  row=source['inputs/reviewed-copy/'+filename];require(ref['sha256']==row['sha256'] and ref['bytes']==row['bytes'],'copy_source_reference_bytes_mismatch')
 for key,digest in [('customerCopy',binding['copySHA256']),('renderPlan',binding['renderPlanSHA256']),('metadata',binding['metadataSHA256'])]:require(copy_review[key]['sha256']==digest,'copy_top_level_digest_mismatch')
 for name in ['implementation-review-binding.json','independent-review-r2.json']:
  packaged='inputs/reviewed-copy/reviews/'+name;retained='independent-copy-review-r2.json' if name=='independent-review-r2.json' else name
  require(source[packaged]['sha256']==sha(docs[retained][0]) and source[packaged]['bytes']==len(docs[retained][0]),'source_manuscript_review_bytes_mismatch')
 exact(code,dict(namespace='gwangju-seogu',assessmentScope='FROZEN_LOCAL_SOURCE_AND_STATIC_OUTPUT_ONLY',verdict='PASS_FROZEN_LOCAL_SOURCE_AND_OUTPUT_ONLY',sourceCommit=None,sourceFiles=SOURCE_FILES,sourceTreeSHA256=SOURCE_TREE_SHA,privateTreeSHA256=PRIVATE_TREE_SHA,adapterTreeSHA256=ADAPTER_TREE_SHA,customerCopySHA256=binding['copySHA256'],renderPlanSHA256=binding['renderPlanSHA256'],manuscriptReviewSHA256=sha(docs['independent-copy-review-r2.json'][0]),manuscriptBindingSHA256=binding['customerReviewBindingSHA256'],mandatoryChangesRemaining=0,actualLocalBuildChecked=True,actualStaticHTMLChecked=True,originalAssetImagesOpened=7,actualRemoteSourceChecked=False,actualActionsChecked=False,actualBrowserChecked=False,actualPublicHTTPChecked=False,providerOwnershipChecked=False,publicationEligible=False),'code_review_identity_or_scope_mismatch')
 reference(code['sourceManifest'],'seogu-candidate-code-independent-20261015/evidence/source-manifest.json')
 reviewed_manifest=doc('reviewed-source-manifest.json');require(reviewed_manifest['files']==list(source.values()) and reviewed_manifest['fileCount']==SOURCE_FILES and reviewed_manifest['treeSHA256']==SOURCE_TREE_SHA,'code_source_manifest_identity_mismatch')
 reference(code['independentCodeReview'],'seogu-candidate-code-independent-20261015/independent-code-review.json')
 reference(code['humanReview'],'seogu-candidate-code-independent-20261015/REVIEW.ko.md')
 exact(code_report,dict(namespace='gwangju-seogu',verdict=code['verdict'],mandatoryChangesRemaining=0,sourceCommit=None,sourceFiles=SOURCE_FILES,privateFiles=PRIVATE_FILES,adapterFiles=ADAPTER_FILES,sourceTreeSHA256=SOURCE_TREE_SHA,privateTreeSHA256=PRIVATE_TREE_SHA,adapterTreeSHA256=ADAPTER_TREE_SHA,actualActionsVerified=False,actualBrowserVerified=False,actualPublicHTTPVerified=False,actual404HTTPVerified=False,providerOwnershipVerified=False,indexNowSubmitted=False,publicationEligible=False,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED'),'code_report_identity_or_scope_mismatch')
 exact(code_report['testCounts'],dict(implementationRegressions=dict(privateNode=64,privatePython=80,adapterNode=36,adapterPython=30,outputPython=55,nodePythonParity=1,total=266),independentNegativeTests=80,stringsEachMode=114,bodyParity=4,staticAssetParity=9),'code_output_review_required')
 require(code_report['sourceManifest']==code['sourceManifest'] and code_report['manuscriptBinding']['sha256']==binding['customerReviewBindingSHA256'] and code_report['manuscriptReview']['sha256']==code['manuscriptReviewSHA256'] and code_report['correctedClosure']['sha256']==code['correctedClosureSHA256'],'code_report_reference_identity_mismatch')
 require(type(code['evidence']) is dict and code['evidence']==code_report['evidence'] and len(code['evidence'])==8,'code_evidence_inventory_mismatch')
 for name,ref in code['evidence'].items():reference(ref,'seogu-candidate-code-independent-20261015/evidence/'+name)
 require(len(originals)==18,'exact_review_document_inventory_required')
 return binding

def load():
 raw=read(DIRECTORY/'production-source-contract.json');c=json.loads(raw);fixed=contract_template()
 require(set(c)==set(fixed)|{'sourceRevision','sourceTree'},'source_contract_schema')
 require(all(same(c[k],v) for k,v in fixed.items()),'source_contract_identity')
 for k in ['sourceRevision','sourceTree']:require(isinstance(c[k],str) and re.fullmatch('[0-9a-f]{40}',c[k]),'verified_full_commit_tree_required')
 frozen_manifests()
 require(sha(read(DIRECTORY/'bounded-contract.json'))==BOUNDED_CONTRACT_SHA,'bounded_scope_contract_changed')
 require(sha(read(DIRECTORY/'preview-equivalence.json'))==PREVIEW_EQUIVALENCE_SHA,'output_baseline_changed')
 verify_content_reviews()
 br=read(DIRECTORY/'production-binding.json');b=json.loads(br);expected={**binding_template(c),'sourceContractSha256':sha(raw)}
 require(set(b)==set(expected)|{'authorizationEvidence'},'binding_schema')
 require(all(same(b[k],v) for k,v in expected.items()),'exact_seogu_binding_required')
 authorization(c,b)
 return c,b,sha(br)

def trusted_control(env):
 require(env.get('GITHUB_REPOSITORY')==REPOSITORY and env.get('GITHUB_REF')=='refs/heads/main','owner_main_required')
 require(env.get('GITHUB_ACTOR')==OWNER and env.get('GITHUB_TRIGGERING_ACTOR')==OWNER and env.get('GITHUB_RUN_ATTEMPT')=='1','owner_first_attempt_required')
 require(env.get('GITHUB_EVENT_NAME')=='issues' and re.fullmatch('[1-9][0-9]*',env.get('GITHUB_RUN_ID','')),'actual_issue_run_required')
 root=DIRECTORY.parents[1];revision=env.get('GITHUB_SHA','');require(re.fullmatch('[0-9a-f]{40}',revision),'control_revision_required')
 require(git(root,'rev-parse','HEAD').decode().strip()==revision,'actual_control_revision_mismatch')
 scopes=['scripts/direct-gwangju-seogu','docs/direct-gwangju-seogu','.github/workflows/gwangju-seogu-production-build-only.yml','.github/workflows/gwangju-seogu-production-publish.yml',*['site-factory/engine/'+n for n in HELPER_SHA256]]
 require(not git(root,'status','--porcelain','--untracked-files=all','--',*scopes).strip(),'control_checkout_changed')
 for scope in scopes:
  entries=[e for e in git(root,'ls-tree','-r','-z','HEAD','--',scope).split(b'\0') if e];require(entries,'tracked_control_missing:'+scope)
  for entry in entries:
   meta,name=entry.split(b'\t');mode,kind,blob=meta.decode().split();name=name.decode();require(mode=='100644' and kind=='blob','control_entry_invalid')
   data=regular_under(root,name);require(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob,'control_bytes_changed:'+name)
 for name,digest in HELPER_SHA256.items():require(sha(read(root/'site-factory/engine'/name))==digest,'existing_helper_changed:'+name)
 c,b,_=load();a=authorization(c,b);require(git(root,'show',a['revision']+':'+a['path'])==read(root/a['path']),'authorization_revision_bytes_mismatch')
 git(root,'merge-base','--is-ancestor',a['revision'],'HEAD')
 return dict(controlRevision=revision,controlCheckoutVerified=True)

def regular_under(root,name):
 root=Path(root);cursor=root
 require(root.is_dir() and not root.is_symlink(),'source_root_symlink')
 for part in Path(name).parts:
  cursor=cursor/part;require(not cursor.is_symlink(),'source_parent_symlink')
 return read(cursor)

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
 require(sha(read(DIRECTORY/'preview-equivalence.json'))==PREVIEW_EQUIVALENCE_SHA,'preview_equivalence_bytes_changed')
 c,_,_=load();return output.equivalence(dist,c['sourceRevision'])

def source(checkout,phase,env):
 c,b,digest=load();trusted_control(env);environment(c,digest,env);require(phase in {'prebuild','postbuild'},'invalid_phase')
 checkout=Path(checkout).resolve();root=checkout/ROOT;candidate=checkout/BUILD_ROOT;adapter=checkout/ADAPTER_ROOT
 require(git(checkout,'rev-parse','HEAD').decode().strip()==c['sourceRevision'],'source_revision_mismatch')
 require(git(checkout,'rev-parse','HEAD:'+ROOT).decode().strip()==c['sourceTree'],'source_tree_mismatch')
 if phase=='prebuild':require(not git(checkout,'status','--porcelain','--untracked-files=all').strip(),'source_checkout_not_clean')
 require(not git(checkout,'diff','--name-only','HEAD','--',ROOT).strip(),'tracked_source_delta')
 private,adapters,expected=frozen_manifests()
 entries=[e for e in git(checkout,'ls-tree','-r','-z','HEAD','--',ROOT).split(b'\0') if e];require(len(entries)==SOURCE_FILES,'source_file_count_mismatch');actual={}
 for entry in entries:
  meta,name=entry.split(b'\t');mode,kind,blob=meta.decode().split();name=name.decode();require(mode=='100644' and kind=='blob' and name.startswith(ROOT+'/'),'source_entry_invalid')
  relative=name.removeprefix(ROOT+'/');require(relative in expected,'unexpected_source_entry')
  data=regular_under(checkout,name);row=expected[relative]
  require(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob==row['gitBlobSHA1'],'source_bytes_changed:'+name)
  require(sha(data)==row['sha256'] and len(data)==row['bytes'],'frozen_source_bytes_changed:'+name);actual[relative]=sha(data)
 require(set(actual)==set(expected),'source_inventory_mismatch')
 # Only these generated build directories are excluded after the frozen prebuild pass.
 allowed={'candidate/node_modules','candidate/.astro','candidate/dist','candidate/evidence','candidate/scripts/__pycache__','release-adapter/scripts/__pycache__'} if phase=='postbuild' else set()
 disk=set()
 def visit(base):
  for item in sorted(base.iterdir()):
   rel=item.relative_to(root).as_posix();require(not item.is_symlink(),'source_symlink_forbidden:'+rel)
   if rel in allowed:require(item.is_dir(),'generated_path_not_directory:'+rel);continue
   require(not item.name.startswith('.'),'hidden_source_forbidden:'+rel)
   if item.is_dir():visit(item)
   else:require(item.is_file(),'nonregular_source_entry:'+rel);disk.add(rel)
 visit(root);require(disk==set(expected),'unexpected_disk_source_entries')
 require(read(adapter/'scripts/seogu_release_output.py')==read(DIRECTORY/'production_output.py'),'source_control_output_validator_mismatch')
 require(read(adapter/'release/bounded-contract.json')==read(DIRECTORY/'bounded-contract.json'),'source_control_scope_mismatch')
 require(read(adapter/'release/private-source-manifest.json')==read(DIRECTORY/'private-source-manifest.json'),'source_control_baseline_mismatch')
 require(read(adapter/'release/preview-equivalence.json')==read(DIRECTORY/'preview-equivalence.json'),'source_control_equivalence_mismatch')
 result=dict(state=phase+'_production_source_verified',sourceRevision=c['sourceRevision'],sourceTree=c['sourceTree'],sourceFiles=SOURCE_FILES,privateFiles=PRIVATE_FILES,adapterFiles=ADAPTER_FILES,sourceTreeSHA256=SOURCE_TREE_SHA,privateTreeSHA256=PRIVATE_TREE_SHA,adapterTreeSHA256=ADAPTER_TREE_SHA,providerCredentialsUsed=False,publicationExecuted=False,publicHTTPVerified=False,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED')
 if phase=='postbuild':result.update(output.inspect_dist(candidate/'dist',dict(mode='production',indexable=True,origin=ORIGIN,revision=c['sourceRevision'])));result['previewEquivalence']=equivalence(candidate/'dist')
 return result
def package(checkout,result,env):
 require(env.get('NATIVE_GATES_PASSED')=='true','native_preview_and_production_gates_required');c,b,digest=load();release=Path('release');release.mkdir(exist_ok=False);shutil.copytree(Path(checkout)/BUILD_ROOT/'dist',release/'dist')
 manifest=dict(schemaVersion=1,repository=REPOSITORY,sourceBranch=BRANCH,sourceRoot=ROOT,revision=c['sourceRevision'],controlRevision=env['GITHUB_SHA'],runId=env['GITHUB_RUN_ID'],origin=ORIGIN,worker=WORKER,indexable=True,bindingSha256=digest,sourceContractSha256=sha(read(DIRECTORY/'production-source-contract.json')),files=result['files']);save(release/'release.json',manifest)
 result.update(releaseManifestSha256=sha(read(release/'release.json')),outputFilesSha256=sha(json.dumps(result['files'],sort_keys=True,separators=(',',':')).encode()),nativePreviewRegressionPassed=True,productionBuildAndMutationQaPassed=True,mobileAndDesktopPixelsVerified=False,productionLaunchGateStatus='PENDING_INDEPENDENT_ASSESSMENT_AND_PIXELS')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['select','prebuild','postbuild']);p.add_argument('--checkout');p.add_argument('--report',required=True);p.add_argument('--package',action='store_true');a=p.parse_args();c,b,digest=load();trusted_control(os.environ)
 if a.phase=='select':
  result=select(c,digest,os.environ,json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text()))
  with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('source_revision='+c['sourceRevision']+'\nbinding_sha256='+digest+'\n')
 else:
  result=source(a.checkout,a.phase,os.environ)
  if a.package:require(a.phase=='postbuild','package_requires_postbuild');package(a.checkout,result,os.environ)
 save(a.report,result);print(json.dumps({k:v for k,v in result.items() if k!='files'},sort_keys=True))
