"""Pinned Gwangsan build and artifact gates. Never contact a provider or publish."""
import argparse,hashlib,json,os,re,shutil,subprocess
from html.parser import HTMLParser
from pathlib import Path
import production_output as output
DIRECTORY=Path(__file__).resolve().parent
# Keep the exact source validator bytes but bind its baseline to this isolated control.
output.EQUIVALENCE_PATH=DIRECTORY/'preview-equivalence.json'
REPOSITORY='joseungil-kr/fwith-site-factory';OWNER='joseungil-kr'
ROOT='site-factory/gwangju-gwangsan-flower';BUILD_ROOT=ROOT+'/candidate';ADAPTER_ROOT=ROOT+'/release-adapter';BRANCH='source/gwangju-gwangsan-production-preparation-20261016'
TITLE='[GWANGJU-GWANGSAN-PRODUCTION-BUILD] 20261016'
HOSTNAME='gwangju-gwangsan.fwith.kr';ORIGIN='https://'+HOSTNAME;WORKER='gwangju-gwangsan-flower-guide'
INPUT_SHA='af97369e9140157e118e52d46e7e94b8612e4cc4a83fb7808572e2a33c7d4336'
PRIVATE_TREE_SHA='791ce17e1c824806f22380248dac47beb602eb7bf205771f32f331721b87a5a6'
ADAPTER_TREE_SHA='acf613f31ae7d7b0f2399216bf0e73491f526cb320d384912c8fe7bd2cc92be0'
SOURCE_TREE_SHA='8be81f2afb7b84571617494e030e880a9cbbdcc4887d1159da5119f8dda40483'
SOURCE_FILES=74;PRIVATE_FILES=59;ADAPTER_FILES=15
PRIVATE_MANIFEST_SHA='a5eb69f3a7b3705819d6b2228770bcbfd132faf22bb3795224474e1bfeea2019'
ADAPTER_MANIFEST_SHA='dc6547697ca3785a055a327d8048fe2fe7b056922d7efb3f06cff1edab68b5ad'
SOURCE_MANIFEST_SHA='8a4f3f1696557753e61227e72e6f0062ee1df15e1cffb069800a2b65ca2e8612'
PREVIEW_EQUIVALENCE_SHA='c670a86adbefd94df63e51b5572be1a467be09dd642659832e9f1116a83efdb7'
BOUNDED_CONTRACT_SHA='ec08e94c62e8b43e765f2e4bb4ea17c3bdfd93340b3fe150ee8a71a21b8b2421'
CONTENT_REVIEW_BINDING_SHA='ddf1632e4ff6b66db64711bfb451bd08d5ce9a194a1582b86a512943e9ae913a'
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
 return dict(schemaVersion=1,state='approved',repository=REPOSITORY,sourceRoot=ROOT,siteKey='gwangju-gwangsan-flower-direct',hostname=HOSTNAME,origin=ORIGIN,worker=WORKER,frozenInputSha256=INPUT_SHA,frozenPrivateTreeSha256=PRIVATE_TREE_SHA,sourceRevision=c['sourceRevision'],proof=output.PROOF,sitemapRoutes=output.ROUTES,htmlFiles=4,directoryRobots='noindex,follow',notFoundStatus=404,publicHttpVerified=False,indexNowSubmitted=False,boundedContractSha256=BOUNDED_CONTRACT_SHA,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED',approvals=dict(publication=True,hostBinding=True,indexNowProof=True))
def authorization_template(c):
 return dict(schemaVersion=1,recordType='user-authorization-not-readiness-proof',repository=REPOSITORY,sourceRoot=ROOT,siteKey='gwangju-gwangsan-flower-direct',hostname=HOSTNAME,origin=ORIGIN,worker=WORKER,sourceRevision=c['sourceRevision'],sourceTree=c['sourceTree'],approvedOperations=['source-and-control-storage','production-build-and-QA','publication-after-own-gates','existing-provider-first-host-binding-with-no-overrides','existing-proof-and-two-URL-IndexNow-after-public-HTTP','public-build-publish-and-receipt-issues'],publicIssuesApproved=True,crossRegionPublicationOrderRequired=False,ownQualityAndSafetyGatesRequired=True,noNewCredentialsOrPermissionChanges=True,noDomainOwnershipTransferOrOverride=True)
def public_issue_approval_evidence():
 return dict(approvedAtUTC='2026-10-15T18:24:17Z',approved=True,scope='remaining-171-planned-regions-public-github-qa-publish-indexnow-receipts',publicData=['site-url','commit','qa-and-receipt-results'],secretsExcluded=True)
def authorization(c,b):
 d=json.loads(read(DIRECTORY/'authorization-binding.json'))
 require(isinstance(d,dict) and set(d)=={'schemaVersion','path','sha256','revision','publicIssuesApproved'} and type(d['schemaVersion']) is int and d['schemaVersion']==1,'authorization_descriptor_schema')
 require(d['publicIssuesApproved'] is True,'public_issue_approval_required')
 require(d['path']=='docs/direct-gwangju-gwangsan/production-authorization-20261016.json' and re.fullmatch('[0-9a-f]{64}',d['sha256'] or '') and re.fullmatch('[0-9a-f]{40}',d['revision'] or ''),'pinned_authorization_required')
 raw=read(DIRECTORY.parents[1]/d['path']);require(sha(raw)==d['sha256'],'authorization_bytes_changed');a=json.loads(raw)
 expected=authorization_template(c);require(set(a)==set(expected)|{'authorizationEvidence'},'authorization_schema')
 require(all(same(a[k],v) for k,v in expected.items()),'exact_gwangsan_authorization_required')
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
 """Bind unchanged native Gwangsan schemas; never invent scores or production PASS."""
 raw=read(DIRECTORY/'content-review-binding.json');require(sha(raw)==CONTENT_REVIEW_BINDING_SHA,'content_review_binding_changed');binding=json.loads(raw)
 expected=dict(schemaVersion=1,region='gwangsan',namespace='gwangju-gwangsan',scope='retained-manuscript-and-local-code-output-reviews-not-production-pass',sourceTreeSHA256=SOURCE_TREE_SHA,sourceFiles=SOURCE_FILES,frozenPrivateTreeSha256=PRIVATE_TREE_SHA,inputSha256=INPUT_SHA,productionGatePassed=False,staticQualityIsProductionPass=False)
 require(set(binding)==set(expected)|{'copySHA256','renderPlanSHA256','metadataSHA256','customerReviewBindingSHA256','codeReviewBindingSHA256','files'} and all(same(binding[k],v) for k,v in expected.items()),'content_review_source_identity_mismatch')
 rows=binding['files'];require(type(rows) is list and len(rows)==18 and all(type(row) is dict and set(row)=={'path','originalPath','bytes','sha256'} for row in rows),'content_review_inventory_schema')
 originals={};docs={};original_paths={'INDEPENDENT-REVIEW.ko.md': 'gwangsan-customer-copy-20261016/independent-review/INDEPENDENT-REVIEW.ko.md', 'current-main-guidance-readback.json': 'gwangsan-customer-copy-20261016/independent-review/current-main-guidance-readback.json', 'customer-context-review.json': 'gwangsan-customer-copy-20261016/independent-review/customer-context-review.json', 'independent-audit.json': 'gwangsan-customer-copy-20261016/independent-review/independent-audit.json', 'original-row-review.json': 'gwangsan-customer-copy-20261016/independent-review/original-row-review.json', 'question-review.json': 'gwangsan-customer-copy-20261016/independent-review/question-review.json', 'review-bindings.json': 'gwangsan-customer-copy-20261016/independent-review/review-bindings.json', 'review-result.json': 'gwangsan-customer-copy-20261016/independent-review/review-result.json', 'public-safe-review-allowlist.json': 'gwangsan-customer-copy-20261016/independent-review/public-safe-review-allowlist.json', 'review-manifest-r1.json': 'gwangsan-customer-copy-20261016/independent-review/review-manifest-r1.json', 'final-readback.json': 'gwangsan-customer-copy-20261016/independent-review/final-readback.json', 'source-input-projection.json': 'gwangsan-local-implementation-20261016/source/inputs/reviewed-input-projection.json', 'code-review.json': 'gwangsan-candidate-code-independent-20261016/code-review.json', 'code-review-bindings.json': 'gwangsan-candidate-code-independent-20261016/code-review-bindings.json', 'verification-evidence-summary.json': 'gwangsan-candidate-code-independent-20261016/verification-evidence-summary.json', 'reviewed-source-manifest.json': 'gwangsan-candidate-code-independent-20261016/final-source-manifest.json', 'candidate-code-review.ko.md': 'gwangsan-candidate-code-independent-20261016/INDEPENDENT-REVIEW.ko.md', 'code-review-publication-manifest.json': 'gwangsan-candidate-code-independent-20261016/source-publication-manifest.json'}
 for row in rows:
  name=row['path'];original=row['originalPath']
  require(type(name) is str and name.startswith('docs/direct-gwangju-gwangsan/content-review-20261016/') and '..' not in Path(name).parts and '\\' not in name,'content_review_path_invalid')
  require(type(original) is str and not Path(original).is_absolute() and '..' not in Path(original).parts and '\\' not in original and original not in originals and Path(name).name not in docs,'content_review_original_path_invalid')
  require(original_paths.get(Path(name).name)==original,'original_document_path_changed')
  data=read(DIRECTORY.parents[1]/name);require(type(row['bytes']) is int and len(data)==row['bytes'] and sha(data)==row['sha256'],'content_review_bytes_changed')
  originals[original]=row;docs[Path(name).name]=(data,json.loads(data) if name.endswith('.json') else None)
 require(set(docs)==set(original_paths),'exact_review_document_inventory_required')
 def doc(name):require(name in docs,'review_document_missing:'+name);return docs[name][1]
 def exact(obj,values,error):require(type(obj) is dict and all(k in obj and same(obj[k],v) for k,v in values.items()),error)
 def reference(ref,prefix):
  require(type(ref) is dict and set(ref)=={'path','bytes','sha256'} and type(ref['path']) is str and not Path(ref['path']).is_absolute() and '..' not in Path(ref['path']).parts and type(ref['bytes']) is int and ref['bytes']>0,'review_reference_schema')
  row=originals.get(prefix+ref['path']);require(row is not None and ref['bytes']==row['bytes'] and ref['sha256']==row['sha256'],'review_reference_bytes_mismatch')
 for name,keys in {'current-main-guidance-readback.json': ['allFourEqual', 'branchURL', 'classification', 'files', 'observedAtUTC', 'observedMain', 'remoteWrites'], 'customer-context-review.json': ['actualHTMLVerified', 'all117Read', 'copySHA256', 'embeddedBannerPixelsIndependentlyRead', 'embeddedBannerText', 'newJudgmentOnly', 'rows', 'schema'], 'independent-audit.json': ['actualHTMLVerified', 'assets', 'authoredKoreanLeaves', 'bodyCharacters', 'checkedAtUTC', 'checks', 'checksVerified', 'classification', 'facilityRows', 'faqCount', 'frozenInputFiles', 'guidanceOriginalRows', 'guidanceTotal', 'historicalScores', 'overlapRecomputed', 'policyRows', 'products', 'publicHTTPVerified', 'questionCount', 'recoveredReadError', 'remoteWrites', 'sourceCommitSHA', 'status'], 'original-row-review.json': ['copySHA256', 'denominators', 'facilityRows', 'fullProductionPass', 'guidanceRows', 'historicalScores', 'newJudgmentOnly', 'originalInputSHA256', 'otherObservedMerchantClaimsRetained', 'policyRows', 'renderPlanSHA256', 'schema'], 'question-review.json': ['actualHTMLVerified', 'copySHA256', 'lengthUsedAsPassThreshold', 'missingCriticalAnswers', 'questionCount', 'remainingOrderSpecificUnknowns', 'rows', 'schema', 'toneAssessedSeparately'], 'review-bindings.json': ['authorInputManifest', 'authorInputManifestSHA256', 'copySHA256', 'originalInputFiles', 'renderPlanSHA256', 'reviewEvidence', 'rule', 'schema', 'sourceCommitSHA'], 'review-result.json': ['actualBrowserVerified', 'actualBuildVerified', 'actualHTMLVerified', 'actualIndexingVerified', 'authorInputManifestSHA256', 'authorScores', 'blockingManuscriptIssues', 'copyChangesRequested', 'copySHA256', 'coreHubLaunch', 'denominators', 'fullLaunch', 'guidanceMain', 'historicalScores', 'indexNowReceiptVerified', 'newJudgmentOnly', 'newJudgments', 'numericReviewScore', 'publicHTTPVerified', 'publicationApprovedByThisReview', 'renderPlanSHA256', 'reviewEvidence', 'reviewedAtUTC', 'schema', 'scope', 'sourceCommitSHA', 'status', 'unchangedOriginals'], 'public-safe-review-allowlist.json': ['customerHTML', 'excluded', 'originalAllowlistUnchanged', 'paths', 'status'], 'review-manifest-r1.json': ['actualHTMLOrPublicPass', 'copySHA256', 'exclusions', 'files', 'frozenAtUTC', 'newJudgmentOnly', 'originalInputFilesCount', 'renderPlanSHA256', 'result', 'revision', 'schema', 'sourceCommitSHA'], 'final-readback.json': ['actualHTMLVerified', 'bindings', 'checkedAtUTC', 'countsRechecked', 'failures', 'filesChecked', 'historicalNullsUntouched', 'manifest', 'originalInputFilesUnchanged', 'publicHTTPVerified', 'reviewResult', 'sourceCommitSHA', 'status'], 'source-input-projection.json': ['authorManifestSHA256', 'bindingSHA256', 'files', 'originalPathBase', 'reviewManifestSHA256', 'reviewSHA256', 'schemaVersion', 'sourcePublicationScope'], 'code-review.json': ['actualBrowserVerified', 'actualIndexingVerified', 'actualRemoteSourceSaved', 'coreHubLaunch', 'directlyVerified', 'evidenceSummary', 'fullLaunch', 'historicalExecutionLimit', 'indexNowReceiptVerified', 'judgment', 'originalManuscript', 'providerOwnershipVerified', 'publicHTTPVerified', 'publicationApprovedByThisReview', 'realHTTP404Verified', 'resolvedIssues', 'reviewedAtUTC', 'revision', 'schema', 'scope', 'source', 'sourceCommitSHA', 'sourceManifest', 'status', 'toolReportedNotFreshlyReobserved', 'unresolvedLocalCodeIssues', 'unverifiedReleaseGates'], 'code-review-bindings.json': ['adapterTreeSHA256', 'customerCopySHA256', 'evidenceSummary', 'frozenSourceZipSHA256', 'humanReview', 'independentCodeReview', 'meaning', 'originalManuscriptBindingSHA256', 'originalManuscriptReviewSHA256', 'privateTreeSHA256', 'renderPlanSHA256', 'revision', 'schema', 'sourceCommitSHA', 'sourceManifest', 'sourceTreeSHA256'], 'verification-evidence-summary.json': ['absoluteMachinePathsIncluded', 'checkedAtUTC', 'commands', 'independentNegativeCaseCount', 'independentNegativeCases', 'limitations', 'offlineOutputFiles', 'originalInputVerification', 'privateOutputFiles', 'rawResearchOrAccountDataIncluded', 'recoveredFindings', 'remoteWrites', 'renderedContexts', 'runtime', 'schema', 'sourceIntegrity', 'sourceTreesSHA256'], 'reviewed-source-manifest.json': ['actualRemoteCommit', 'fileCount', 'files', 'remoteSaved', 'treeSHA256'], 'code-review-publication-manifest.json': ['allowlistSelfExcludedFromDigestRows', 'excluded', 'reviewFiles', 'schema', 'scope', 'selfBindingInstruction', 'sourceCommitSHA', 'sourceFileCount', 'sourceManifest', 'sourceRoot', 'sourceTreeSHA256']}.items():require(type(doc(name)) is dict and set(doc(name))==set(keys),'original_review_schema_required:'+name)
 cp=doc('review-bindings.json');manuscript=doc('review-result.json')
 exact(cp,dict(schema='gwangsan-independent-review-bindings/v1',copySHA256=binding['copySHA256'],renderPlanSHA256=binding['renderPlanSHA256'],sourceCommitSHA=None),'manuscript_binding_identity_required')
 exact(manuscript,dict(schema='gwangsan-independent-manuscript-review/v1',status='MANUSCRIPT_REVIEW_ACCEPTED_WITH_RENDER_PENDING',newJudgmentOnly=True,copySHA256=binding['copySHA256'],renderPlanSHA256=binding['renderPlanSHA256'],sourceCommitSHA=None,blockingManuscriptIssues=[],copyChangesRequested=[],historicalScores=None,authorScores=None,numericReviewScore=None,coreHubLaunch='NOT_ASSESSED',fullLaunch='NOT_ASSESSED',actualBuildVerified=False,actualHTMLVerified=False,actualBrowserVerified=False,publicHTTPVerified=False,indexNowReceiptVerified=False,actualIndexingVerified=False,publicationApprovedByThisReview=False),'original_manuscript_scope_or_null_scores_changed')
 exact(manuscript['denominators'],dict(guidance=159,policy=24,facility=2,customerStrings=117,customerQuestions=13,faq=4,customerAssets=7,customerRoutes=4,plannedIndexableRoutes=2,detailCandidates=1,heldFacilities=9),'original_159_24_2_117_4_denominators_required')
 require(sha(docs['review-bindings.json'][0])==binding['customerReviewBindingSHA256'],'review_top_level_binding_changed')
 clauses=doc('original-row-review.json');exact(clauses['denominators'],dict(guidanceOriginalRows=159,policyOriginalRows=24,facilityOriginalRows=2),'original_clause_denominators_required')
 require(len(clauses['guidanceRows'])==159 and len(clauses['policyRows'])==24 and len(clauses['facilityRows'])==2 and clauses['historicalScores'] is None and clauses['fullProductionPass'] is False,'original_row_review_required')
 visible=doc('customer-context-review.json');require(visible['all117Read'] is True and len(visible['rows'])==117 and visible['copySHA256']==binding['copySHA256'] and visible['actualHTMLVerified'] is False and all(row['actualRenderedVerified'] is False for row in visible['rows']),'original_117_contexts_not_render_pass')
 questions=doc('question-review.json');require(questions['questionCount']==13 and len(questions['rows'])==13 and questions['missingCriticalAnswers']==[] and questions['actualHTMLVerified'] is False and all(row['actualRenderedVisibleVerified'] is False for row in questions['rows']),'original_13_questions_not_render_pass')
 source=manifest('source-manifest.json',SOURCE_MANIFEST_SHA,SOURCE_FILES,SOURCE_TREE_SHA)
 projection=doc('source-input-projection.json');exact(projection,dict(schemaVersion=1,originalPathBase='GWANGSAN_CLOSED_MANUSCRIPT_ROOT',reviewSHA256=sha(docs['review-result.json'][0]),bindingSHA256=binding['customerReviewBindingSHA256'],authorManifestSHA256=cp['authorInputManifestSHA256'],reviewManifestSHA256=sha(docs['review-manifest-r1.json'][0])),'source_projection_identity_required')
 require(type(projection['files']) is list and len(projection['files'])==17,'source_projection_inventory_required');by_original={}
 for row in projection['files']:
  require(set(row)=={'originalPath','packagedPath','bytes','sha256'} and type(row['bytes']) is int and row['originalPath'] not in by_original,'source_projection_row_schema');name=row['packagedPath'];require(name in source and source[name]['sha256']==row['sha256'] and source[name]['bytes']==row['bytes'],'projection_source_bytes_mismatch');by_original[row['originalPath']]=row
 for name,field in [('customer-copy.json','copySHA256'),('render-plan.json','renderPlanSHA256'),('purchase-intent-metadata.json','metadataSHA256')]:require(by_original[name]['sha256']==binding[field],'review_source_input_digest_mismatch')
 prefix='gwangsan-customer-copy-20261016/'
 for row in rows:
  if row['originalPath'].startswith(prefix):
   original=row['originalPath'].removeprefix(prefix);source_row=by_original.get(original)
   if source_row:require(source_row['sha256']==row['sha256'] and source_row['bytes']==row['bytes'],'original_review_source_bytes_mismatch')
 for ref in cp['reviewEvidence']:reference(ref,prefix)
 allowlist=doc('public-safe-review-allowlist.json');require({row['originalPath'].removeprefix(prefix) for row in rows if row['originalPath'].startswith(prefix)}==set(allowlist['paths']),'review_public_allowlist_scope_required')
 source_row=source['inputs/reviewed-input-projection.json'];require(source_row['sha256']==sha(docs['source-input-projection.json'][0]) and source_row['bytes']==len(docs['source-input-projection.json'][0]),'source_projection_bytes_mismatch')
 require(True,'local_code_review_not_yet_bound')
 code=doc('code-review-bindings.json');report=doc('code-review.json')
 require(sha(docs['code-review-bindings.json'][0])==binding['codeReviewBindingSHA256'],'code_binding_digest_mismatch')
 exact(code,dict(schema='gwangsan-independent-code-review-bindings/v1',revision='r2',sourceCommitSHA=None,sourceTreeSHA256=SOURCE_TREE_SHA,privateTreeSHA256=PRIVATE_TREE_SHA,adapterTreeSHA256=ADAPTER_TREE_SHA,customerCopySHA256=binding['copySHA256'],renderPlanSHA256=binding['renderPlanSHA256'],originalManuscriptReviewSHA256=sha(docs['review-result.json'][0]),originalManuscriptBindingSHA256=binding['customerReviewBindingSHA256']),'code_native_binding_identity_mismatch')
 exact(report,dict(schema='gwangsan-independent-code-review/v1',revision='r2',status='LOCAL_CODE_REVIEW_ACCEPTED_WITH_RELEASE_GATES_PENDING',sourceCommitSHA=None,actualRemoteSourceSaved=False,unresolvedLocalCodeIssues=[],actualBrowserVerified=False,publicHTTPVerified=False,realHTTP404Verified=False,providerOwnershipVerified=False,publicationApprovedByThisReview=False,indexNowReceiptVerified=False,actualIndexingVerified=False,coreHubLaunch='NOT_ASSESSED',fullLaunch='NOT_ASSESSED'),'code_native_scope_or_flags_mismatch')
 exact(report['source'],dict(sourceFiles=SOURCE_FILES,privateFiles=PRIVATE_FILES,adapterFiles=ADAPTER_FILES,treesSHA256=dict(source=SOURCE_TREE_SHA,private=PRIVATE_TREE_SHA,adapter=ADAPTER_TREE_SHA),manifestSHA256=sha(docs['reviewed-source-manifest.json'][0]),zipSHA256=code['frozenSourceZipSHA256'],privateFilesUnchangedFromR1=True),'code_source_identity_mismatch')
 exact(report['originalManuscript'],dict(status='MANUSCRIPT_REVIEW_ACCEPTED_WITH_RENDER_PENDING',copySHA256=binding['copySHA256'],renderPlanSHA256=binding['renderPlanSHA256'],reviewSHA256=sha(docs['review-result.json'][0]),bindingSHA256=binding['customerReviewBindingSHA256'],historicalScores=None,authorScores=None,numericReviewScore=None,guidanceRows=159,policyRows=24,facilityRows=2,originalBytesUnchanged=True,originalRenderPendingFlagsUnchanged=True),'code_original_manuscript_changed')
 prefix='gwangsan-candidate-code-independent-20261016/'
 for obj in [code,report]:
  for value in obj.values():
   if type(value) is dict and set(value)=={'path','bytes','sha256'}:reference(value,prefix)
 public_manifest=doc('code-review-publication-manifest.json');exact(public_manifest,dict(schema='gwangsan-code-review-publication-allowlist/v1',sourceCommitSHA=None,sourceRoot=ROOT,sourceFileCount=SOURCE_FILES,sourceTreeSHA256=SOURCE_TREE_SHA,allowlistSelfExcludedFromDigestRows=True),'code_publication_manifest_required')
 require(type(public_manifest['reviewFiles']) is list and len(public_manifest['reviewFiles'])==5 and {row['path'] for row in public_manifest['reviewFiles']}=={'code-review.json','code-review-bindings.json','verification-evidence-summary.json','final-source-manifest.json','INDEPENDENT-REVIEW.ko.md'},'code_exact_publication_scope_required')
 for ref in public_manifest['reviewFiles']:reference(ref,prefix)
 reference(public_manifest['sourceManifest'],prefix)
 reviewed=doc('reviewed-source-manifest.json');require(reviewed['files']==list(source.values()) and reviewed['fileCount']==SOURCE_FILES and reviewed['treeSHA256']==SOURCE_TREE_SHA,'code_source_manifest_identity_mismatch')
 evidence=doc('verification-evidence-summary.json');require(evidence['sourceIntegrity']['manifestSHA256']==sha(docs['reviewed-source-manifest.json'][0]) and evidence['sourceIntegrity']['sourceTreeSHA256']==SOURCE_TREE_SHA and evidence['sourceIntegrity']['sourceFiles']==SOURCE_FILES and evidence['sourceIntegrity']['zipSHA256']==code['frozenSourceZipSHA256'],'code_evidence_source_identity_mismatch')
 # Canonical semantic seals reject arbitrary nested claims, type coercion and invented historic verdicts even if outer envelopes are rehashed.
 for name,digest in {'current-main-guidance-readback.json': '4e51b83168632caba2bfa6545b69d39a2416a3027eee7930335165e10f496820', 'customer-context-review.json': '3b746aacb66645e9be8d0d7efeb0753efaacb9af9deba3d23caeb46fd958f362', 'independent-audit.json': '20ebec7baf795dd25cfa4e27106610097fec4e8007bdbc4e08a2dd56b42deb04', 'original-row-review.json': 'f69e4dbc236b92fe29786326738dc67878728b2e3a269076d745a736352fad8e', 'question-review.json': 'bd38817f20cbc44270c2a53109f050cba469a42e90882e579b645fdbd391408d', 'review-bindings.json': '5af2f178bec2df49ea5c6e424ae78a5e24a0da03cb59739e63cef2752481e7b3', 'review-result.json': 'f8aeab2bb26ab1b5dc7a3b2ea23fa5a15a9cb2fb34d09e3f3eba5b59511b6816', 'public-safe-review-allowlist.json': '0a99a96aa065969173473de4947e8c6be2265cd8b3a67c0a2d4041611fad18bd', 'review-manifest-r1.json': '5c1798a1e9cd4b563cb7c5ea904390fb4a6a752ba9654dec8333f1dcfbd5c1f0', 'final-readback.json': '3d1a7bc5dc0e525e104081a970d4ad3a0b4b2ad24f3b1aba0eabee1e88e47bf8', 'source-input-projection.json': 'ac60c45fc626c185d8ba651601050989c471825901e28875fbab022ada56b4f7', 'code-review.json': '75cd89a75139731754bf621accd8823456842857f475bbf12ec5e8028ccc386c', 'code-review-bindings.json': '3a970ae53d34dd440db8d5645b463ddced59afa9c157fe9a1e3c1f157105a2d2', 'verification-evidence-summary.json': 'dd910214e39006e72e8e30484f2259f6c4b2f03531f28260def741242ce7396d', 'reviewed-source-manifest.json': 'e959603db9db1bd2e60e19694f63513fb347404bf1ef2c0c19a4fb3cde30b19f', 'code-review-publication-manifest.json': 'c186f27e2189ac294c3ad9674c39ae419b796aec518e59946c7ab023d994f5da'}.items():require(sha(json.dumps(doc(name),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())==digest,'original_review_meaning_changed:'+name)
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
 require(all(same(b[k],v) for k,v in expected.items()),'exact_gwangsan_binding_required')
 authorization(c,b)
 return c,b,sha(br)

def trusted_control(env):
 require(env.get('GITHUB_REPOSITORY')==REPOSITORY and env.get('GITHUB_REF')=='refs/heads/main','owner_main_required')
 require(env.get('GITHUB_ACTOR')==OWNER and env.get('GITHUB_TRIGGERING_ACTOR')==OWNER and env.get('GITHUB_RUN_ATTEMPT')=='1','owner_first_attempt_required')
 require(env.get('GITHUB_EVENT_NAME')=='issues' and re.fullmatch('[1-9][0-9]*',env.get('GITHUB_RUN_ID','')),'actual_issue_run_required')
 root=DIRECTORY.parents[1];revision=env.get('GITHUB_SHA','');require(re.fullmatch('[0-9a-f]{40}',revision),'control_revision_required')
 require(git(root,'rev-parse','HEAD').decode().strip()==revision,'actual_control_revision_mismatch')
 scopes=['scripts/direct-gwangju-gwangsan','docs/direct-gwangju-gwangsan','.github/workflows/gwangju-gwangsan-production-build-only.yml','.github/workflows/gwangju-gwangsan-production-publish.yml',*['site-factory/engine/'+n for n in HELPER_SHA256]]
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
 require(read(adapter/'scripts/gwangsan_release_output.py')==read(DIRECTORY/'production_output.py'),'source_control_output_validator_mismatch')
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
