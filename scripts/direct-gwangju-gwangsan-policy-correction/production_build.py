"""Pinned Gwangsan one-paragraph correction build and artifact gates. Never contact a provider or publish."""
import argparse,hashlib,json,os,re,shutil,subprocess
from html.parser import HTMLParser
from pathlib import Path
import production_output as output
DIRECTORY=Path(__file__).resolve().parent
# Keep the exact source validator bytes but bind its baseline to this isolated control.
output.EQUIVALENCE_PATH=DIRECTORY/'preview-equivalence.json'
REPOSITORY='joseungil-kr/fwith-site-factory';OWNER='joseungil-kr'
ROOT='site-factory/gwangju-gwangsan-flower';BUILD_ROOT=ROOT+'/candidate';ADAPTER_ROOT=ROOT+'/release-adapter';BRANCH='source/gwangju-gwangsan-policy-correction-20261016'
TITLE='[GWANGJU-GWANGSAN-POLICY-CORRECTION-BUILD] 20261016'
NAMESPACE='gwangju-gwangsan-policy-correction'
SOURCE_REVISION='0da9982f8ea294c6fb38729d17e9043d45f7ca72'
SOURCE_GIT_TREE='f995e27d2e95f14de2e533a23aada0261b394a15'
BASE_SOURCE_REVISION='654dafd7cafa4c6a158684ac4b304ceb7a5996b5'
REVIEWED_SOURCE_REVISION=SOURCE_REVISION
HOSTNAME='gwangju-gwangsan.fwith.kr';ORIGIN='https://'+HOSTNAME;WORKER='gwangju-gwangsan-flower-guide'
INPUT_SHA='af97369e9140157e118e52d46e7e94b8612e4cc4a83fb7808572e2a33c7d4336'
PRIVATE_TREE_SHA='9f145c55ef0effa823d1c645142662312fe6d635b7c7c3493eec73b396975bfd'
ADAPTER_TREE_SHA='ed1135746cb660fa427ea666b26711802d9bb0c6f0ede47d258c06a0f2366eb7'
SOURCE_TREE_SHA='f27905b27ae97982d0caf0e8e5f052bb2406b02ba076a1f5aee418d9786b205b'
SOURCE_FILES=92;PRIVATE_FILES=77;ADAPTER_FILES=15
PRIVATE_MANIFEST_SHA='0c3864efe17af5c6f752a9dd623d00b2b8520889222bf258d2fc7af8b15d9955'
ADAPTER_MANIFEST_SHA='6c8643dcbaf9be12a5676a60c2a5a7e8a48167d4a78d43be99d7233f24d1805f'
SOURCE_MANIFEST_SHA='97f653138862c7a30e29414b291c5ef6b8b1cf4fa6eab981431b8a7cfc48a535'
PREVIEW_EQUIVALENCE_SHA='250841e6a47bf9ad8ea83d167a5e35b9407ff8b10093e735d83da54f38c19acb'
BOUNDED_CONTRACT_SHA='79047267be04e4b51e3ccd709404a83720d245138d81ecafb128785178a3b661'
CONTENT_REVIEW_BINDING_SHA='f320dc2baf26d277b8df628659e8f8c876baf3197e571541c71cbf339e9b5552'
HELPER_SHA256={'bucheon_domain_attach.py': 'a8662dd6ff232c53b6c55f193553f134c7055ec80eca421b65bab9bedd220da3', 'goyang_domain.py': '8a30e0ea75758344a5ff92903ec0a9dbd1e4f2bff230cdf603ea871ca1bf9c68', 'indexnow_finalize.py': '55f5274d3fcc713e82fd8ce18e280447e68e9e460bc1ff3f9bf5cc683834935f'}
HISTORICAL_CONTENT_REVIEW_BINDING_SHA='ddf1632e4ff6b66db64711bfb451bd08d5ce9a194a1582b86a512943e9ae913a'
CURRENT_REVIEW_INVENTORY_SHA='509b35d26c20a0a955c54219027c2f034c5bcfc8e92ffd7f3445e3b59f47d230'
CURRENT_REVIEW_FIELDS={'adapterFiles': 15, 'amendmentBindingSHA256': '86ced576296d166a47edf75a187ab932828c0eaa4dded52ef98e262eb06898c8', 'amendmentReviewSHA256': '4dce819ef5e1c9ac48b215c911a796dd102b3526b1492685f063299371c8c7b4', 'baseSourceCommit': '654dafd7cafa4c6a158684ac4b304ceb7a5996b5', 'copySHA256': '349aed309651211833a240394361352b95f8830c0f61e5829419047df74a7c72', 'customerCopyLeavesChanged': 1, 'customerCopyPointer': '/detail/sections/4/afterList/0', 'namespace': 'gwangju-gwangsan-policy-correction', 'originalContentReviewBindingPath': 'scripts/direct-gwangju-gwangsan/content-review-binding.json', 'originalContentReviewBindingSHA256': 'ddf1632e4ff6b66db64711bfb451bd08d5ce9a194a1582b86a512943e9ae913a', 'originalCopySHA256': '9a0044feabf70a7a5ae6994d2523169a48d374ae4697aeeda3ccff4f6aec0493', 'originalDenominators': {'assets': 7, 'customerStrings': 117, 'facility': 2, 'faq': 4, 'guidance': 159, 'policy': 24, 'questions': 13}, 'originalReviewBytesUnchanged': True, 'pendingFindingResolved': False, 'privateFiles': 77, 'productionGatePassed': False, 'region': 'gwangsan', 'renderPlanSHA256': 'eb39fac5d44663e89fe14003f26984b2cafc088e70e97e65a09e7ac85dbe294c', 'schema': 'gwangsan-policy-correction-content-review-binding/v1', 'scope': 'historical-originals-plus-native-one-leaf-amendment-and-independent-source-delta-not-production-pass', 'sourceDeltaBindingSHA256': '8d07e5100bf401abfe3556f2b9876565954b0ecdb50d02366a6ea24e747b366b', 'sourceDeltaReviewSHA256': '2f102a57b3c76219c67e4a0942c8d37da296ee45582fca627c16fd5bd5962290', 'sourceFiles': 92, 'sourceRevision': '0da9982f8ea294c6fb38729d17e9043d45f7ca72', 'sourceTreeSHA256': 'f27905b27ae97982d0caf0e8e5f052bb2406b02ba076a1f5aee418d9786b205b', 'supplementalDenominators': {'applicationScopeFollowupFacts': 1, 'upperImagePolicyClauses': 6}}
HISTORICAL_AUTHORIZATION_DESCRIPTOR_SHA='ab3d12bc78c28329a309128764f275c54460350f47088d2e5cbedb6c566b0551'
HISTORICAL_AUTHORIZATION_SHA='c7c26f5aac8ab9cb48d01afd921e877e9cd8f206e8132da03f5df7960ab4e622'
HISTORICAL_AUTHORIZATION_REVISION='887bcb5e6fc95a0240d3e2669a6c57541366c690'
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
 return dict(schemaVersion=1,state='approved',recordType='correction-user-authorization-not-readiness-proof',namespace=NAMESPACE,repository=REPOSITORY,sourceRoot=ROOT,siteKey='gwangju-gwangsan-flower-direct',hostname=HOSTNAME,origin=ORIGIN,worker=WORKER,baseSourceRevision=BASE_SOURCE_REVISION,sourceRevision=c['sourceRevision'],sourceTree=c['sourceTree'],approvedOperations=['source-and-control-storage','production-build-and-QA','existing-host-one-paragraph-correction-after-own-gates','existing-proof-and-two-URL-IndexNow-after-public-HTTP','public-build-publish-and-receipt-issues'],publicIssuesApproved=True,existingHostOnly=True,noNewHostnameOrWorker=True,ownQualityAndSafetyGatesRequired=True,noNewCredentialsOrPermissionChanges=True,noDomainOwnershipTransferOrOverride=True,historicalAuthorizationRole='prior-deployment-provenance-only-not-current-source-approval')
def public_issue_approval_evidence():
 return dict(approved=True,owner=OWNER,action='existing-gwangsan-host-one-paragraph-policy-correction',publicData=['site-url','commit','qa-and-receipt-results'],secretsExcluded=True)
def historical_authorization(b):
 raw=read(DIRECTORY/'historical-authorization-binding.json');require(sha(raw)==HISTORICAL_AUTHORIZATION_DESCRIPTOR_SHA,'historical_authorization_descriptor_changed');d=json.loads(raw)
 require(d==dict(schemaVersion=1,path='docs/direct-gwangju-gwangsan/production-authorization-20261016.json',sha256=HISTORICAL_AUTHORIZATION_SHA,revision=HISTORICAL_AUTHORIZATION_REVISION,publicIssuesApproved=True),'historical_authorization_identity_changed')
 raw=regular_under(DIRECTORY.parents[1],d['path']);require(sha(raw)==HISTORICAL_AUTHORIZATION_SHA,'historical_authorization_bytes_changed')
 a=json.loads(raw);require(a['sourceRevision']==BASE_SOURCE_REVISION,'historical_source_must_remain_original')
 require(b['authorizationEvidence']=='https://github.com/'+REPOSITORY+'/blob/'+d['revision']+'/'+d['path'],'historical_adapter_provenance_reference_required')
 return d

def authorization(c,b):
 """A historical adapter URL never supplies authorization for the new source."""
 historical_authorization(b)
 d=json.loads(read(DIRECTORY/'authorization-binding.json'))
 require(isinstance(d,dict) and set(d)=={'schemaVersion','path','sha256','revision','publicIssuesApproved'} and type(d['schemaVersion']) is int and d['schemaVersion']==1,'authorization_descriptor_schema')
 require(d['publicIssuesApproved'] is True,'current_correction_public_issue_approval_required')
 require(d['path']=='docs/direct-'+NAMESPACE+'/production-authorization-20261016.json' and re.fullmatch('[0-9a-f]{64}',d['sha256'] or '') and type(d['revision']) is str and re.fullmatch('[0-9a-f]{40}',d['revision']),'current_correction_activation_revision_required')
 raw=regular_under(DIRECTORY.parents[1],d['path']);require(sha(raw)==d['sha256'],'authorization_bytes_changed');a=json.loads(raw)
 expected=authorization_template(c);require(set(a)==set(expected)|{'authorizationEvidence'},'authorization_schema')
 require(all(same(a[k],v) for k,v in expected.items()),'exact_current_correction_authorization_required')
 require(same(a['authorizationEvidence'],[public_issue_approval_evidence()]),'exact_current_owner_action_evidence_required')
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

def verify_historical_content_reviews():
 """Preserve original74/59/15 native reviews; do not relabel them as amendment review."""
 SOURCE_TREE_SHA="8be81f2afb7b84571617494e030e880a9cbbdcc4887d1159da5119f8dda40483";PRIVATE_TREE_SHA="791ce17e1c824806f22380248dac47beb602eb7bf205771f32f331721b87a5a6";ADAPTER_TREE_SHA="acf613f31ae7d7b0f2399216bf0e73491f526cb320d384912c8fe7bd2cc92be0"
 SOURCE_FILES=74;PRIVATE_FILES=59;ADAPTER_FILES=15;SOURCE_MANIFEST_SHA="8a4f3f1696557753e61227e72e6f0062ee1df15e1cffb069800a2b65ca2e8612"
 raw=read(DIRECTORY/'historical-content-review-binding.json');require(sha(raw)==HISTORICAL_CONTENT_REVIEW_BINDING_SHA,'content_review_binding_changed');binding=json.loads(raw)
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
 source=manifest('historical-source-manifest.json',SOURCE_MANIFEST_SHA,SOURCE_FILES,SOURCE_TREE_SHA)
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


def verify_content_reviews():
 """Verify historical159/24/facility2 and separate current6+1 without promoting nulls."""
 historical=verify_historical_content_reviews()
 raw=read(DIRECTORY/'content-review-binding.json');require(sha(raw)==CONTENT_REVIEW_BINDING_SHA,'content_review_binding_changed');binding=json.loads(raw)
 require(set(binding)==set(CURRENT_REVIEW_FIELDS)|{'files'} and all(same(binding[k],v) for k,v in CURRENT_REVIEW_FIELDS.items()),'current_review_source_or_scope_changed')
 rows=binding['files'];require(type(rows) is list and len(rows)==68,'current_review_inventory_denominator')
 require(sha(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())==CURRENT_REVIEW_INVENTORY_SHA,'current_review_inventory_meaning_changed')
 originals={};docs={};root=DIRECTORY.parents[1]
 for row in rows:
  require(type(row) is dict and set(row)=={'path','originalPath','package','bytes','sha256'},'current_review_inventory_schema')
  name=row['path'];package=row['package'];require(package in {'amendment-review','source-delta-review','source-save'} and type(name) is str and name.startswith('docs/direct-'+NAMESPACE+'/'+package+'/'),'current_review_package_path_invalid')
  require(not Path(name).is_absolute() and not any(part in {'.','..'} or part.startswith('.') for part in name.split('/')) and '\\' not in name and name not in docs,'current_review_path_invalid')
  require(row['originalPath'] not in originals and type(row['bytes']) is int and row['bytes']>0,'current_review_original_path_invalid')
  data=regular_under(root,name);require(len(data)==row['bytes'] and sha(data)==row['sha256'],'current_review_bytes_changed:'+name)
  originals[row['originalPath']]=row;docs[name.removeprefix('docs/direct-'+NAMESPACE+'/')]=data
 def doc(name):require(name in docs,'current_review_document_missing:'+name);return json.loads(docs[name])
 def exact(obj,values,error):require(type(obj) is dict and all(k in obj and same(obj[k],v) for k,v in values.items()),error)
 def ref(value,prefix):
  require(type(value) is dict and set(value)=={'path','bytes','sha256'} and type(value['path']) is str and '..' not in Path(value['path']).parts,'current_review_reference_schema')
  name=prefix+value['path'];require(name in docs and type(value['bytes']) is int and len(docs[name])==value['bytes'] and sha(docs[name])==value['sha256'],'current_review_reference_mismatch:'+name)
 source=manifest('source-manifest.json',SOURCE_MANIFEST_SHA,SOURCE_FILES,SOURCE_TREE_SHA)
 old_denominators=dict(guidance=159,policy=24,facility=2,customerStrings=117,customerQuestions=13,faq=4,customerAssets=7,customerRoutes=4,plannedIndexableRoutes=2,detailCandidates=1,heldFacilities=9)
 supplement=dict(upperImagePolicyClauses=6,applicationScopeFollowupFacts=1)
 amendment=doc('amendment-review/independent-review-r2.json');ab=doc('amendment-review/review-binding.json')
 exact(amendment,dict(schema='gwangsan-independent-narrow-policy-successor-review/v1',assessmentScope='ONE_TIMING_PARAGRAPH_MANUSCRIPT_ONLY',verdict='ACCEPT_NARROW_TIMING_PARAGRAPH_WITH_SOURCE_AND_RELEASE_PENDING',customerCopySHA256=binding['copySHA256'],originalCopySHA256=binding['originalCopySHA256'],copyPointer=binding['customerCopyPointer'],baseSourceCommit=BASE_SOURCE_REVISION,successorSourceCommit=None,originalDenominators=old_denominators,supplementalDenominators=supplement,historicalScores=None,authorScores=None,numericReviewScore=None,blockingManuscriptIssues=[],copyChangesRequested=[],notAFullSiteReReview=True,publicationApprovedByThisReview=False,actualSuccessorBuildVerified=False,actualSuccessorHTMLVerified=False,actualSuccessorBrowserVerified=False,actualSuccessorPublicHTTPVerified=False,actualSuccessorRedeploymentVerified=False,pendingFindingResolved=False),'native_amendment_scope_or_nulls_changed')
 require(sha(docs['amendment-review/independent-review-r2.json'])==binding['amendmentReviewSHA256'] and sha(docs['amendment-review/review-binding.json'])==binding['amendmentBindingSHA256'],'native_amendment_binding_changed')
 exact(ab,dict(schema='gwangsan-narrow-policy-successor-review-binding/v1',pathBase='THIS_REVIEW_PACKAGE_ROOT',publicationEligible=False),'native_amendment_binding_scope_changed')
 for value in ab.values():
  if type(value) is dict and set(value)=={'path','bytes','sha256'}:ref(value,'amendment-review/')
 for value in amendment['reviewEvidence'].values():ref(value,'amendment-review/')
 before=doc('amendment-review/inputs/original-customer-copy.json');after=doc('amendment-review/inputs/customer-copy.json')
 differences=[]
 def compare(a,b,pointer=''):
  require(type(a) is type(b),'amendment_copy_shape_changed')
  if type(a) is dict:
   require(set(a)==set(b),'amendment_copy_keys_changed')
   for key in a:compare(a[key],b[key],pointer+'/'+key)
  elif type(a) is list:
   require(len(a)==len(b),'amendment_copy_list_shape_changed')
   for index,(left,right) in enumerate(zip(a,b)):compare(left,right,pointer+'/'+str(index))
  elif a!=b:require(type(a) is str and type(b) is str,'amendment_nonstring_changed');differences.append(pointer)
 compare(before,after);require(differences==['/detail/sections/4/afterList/0'],'exact_one_approved_copy_leaf_required')
 require(sha(docs['amendment-review/inputs/original-customer-copy.json'])==historical['copySHA256']==binding['originalCopySHA256'] and sha(docs['amendment-review/inputs/customer-copy.json'])==binding['copySHA256'],'original_resolved_copy_binding_changed')
 require(source['inputs/reviewed-copy/customer-copy.json']['sha256']==binding['originalCopySHA256'] and source['inputs/policy-amendment/customer-copy.json']['sha256']==binding['copySHA256'],'source_resolved_copy_binding_changed')
 # The immutable source carries an exact public-safe subset of the native review.
 for name,row in source.items():
  if name.startswith('inputs/policy-amendment/review/'):
   projected='amendment-review/'+name.removeprefix('inputs/policy-amendment/review/')
   require(projected in docs and sha(docs[projected])==row['sha256'] and len(docs[projected])==row['bytes'],'native_review_source_projection_changed')
 delta=doc('source-delta-review/source-delta-review.json');db=doc('source-delta-review/source-delta-binding.json')
 require(sha(docs['source-delta-review/source-delta-review.json'])==binding['sourceDeltaReviewSHA256'] and sha(docs['source-delta-review/source-delta-binding.json'])==binding['sourceDeltaBindingSHA256'],'source_delta_review_binding_changed')
 exact(delta,dict(schema='gwangsan-policy-source-delta-review/v1',disposition='SCOPED_SOURCE_AND_REBUILT_OUTPUTS_VERIFIED_RELEASE_CONTROLS_PENDING',blockingSourceFindings=[],sourceRevision=None,publicationEligible=False,pendingFindingResolved=False,actualBrowserVerified=False,actualPublicHTTPVerified=False,providerOwnershipVerified=False,IndexNowSubmitted=False,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED'),'source_delta_scope_or_nulls_changed')
 exact(db,dict(schema='gwangsan-policy-source-delta-binding/v1',disposition=delta['disposition'],publicationEligible=False,pendingFindingResolved=False,remoteCommitMustBeBoundSeparately=True),'source_delta_binding_scope_changed')
 require(same(db['source'],delta['sourceBinding']) and same(db['nativeAmendmentReview'],delta['nativeAmendmentReview']) and same(db['originalCodeReview'],delta['originalCodeReview']),'source_delta_native_reference_changed')
 exact(db['source'],dict(sourceRevision=None,sourceRemoteSaved=False,sourceFiles=SOURCE_FILES,privateFiles=PRIVATE_FILES,adapterFiles=ADAPTER_FILES,sourceTreeSHA256=SOURCE_TREE_SHA,privateTreeSHA256=PRIVATE_TREE_SHA,adapterTreeSHA256=ADAPTER_TREE_SHA),'source_delta_source_identity_changed')
 exact(db['nativeAmendmentReview'],dict(bytesModified=False,copyPointer=binding['customerCopyPointer'],customerCopySHA256=binding['copySHA256'],originalCopySHA256=binding['originalCopySHA256'],originalDenominators=old_denominators,supplementalDenominators=supplement,nativeSourceCommit=None,nativePublicationEligible=False,nativeScores=None),'source_delta_native_amendment_semantics_changed')
 exact(db['originalCodeReview'],dict(bytesModified=False,originalReviewerReranAmendment=False),'historical_reviewer_attribution_changed')
 for value in [db['review'],db['humanReview'],*db['evidence'],*delta['evidence']]:ref(value,'source-delta-review/')
 for group in ['source','originalCodeReview','nativeAmendmentReview']:
  for value in db[group].values():
   if type(value) is dict and set(value)=={'path','bytes','sha256'}:ref(value,'source-delta-review/')
 reviewed=doc('source-delta-review/source-manifest.json');require(reviewed['files']==list(source.values()) and reviewed['fileCount']==92 and reviewed['treeSHA256']==SOURCE_TREE_SHA and reviewed['actualRemoteCommit'] is None,'source_delta_manifest_identity_changed')
 for key,name in [('private','private-manifest.json'),('adapter','adapter-manifest.json')]:
  reviewed=doc('source-delta-review/'+name);require(reviewed['files']==[r for r in source.values() if r['path'].startswith('release-adapter/')==(key=='adapter')],'source_delta_split_manifest_changed')
 verified=delta['verified'];exact(verified,dict(sourceFiles=92,customerLeavesChanged=1,otherCustomerStringsUnchanged=116,originalInputsAllUnchanged=True,templatesLayoutsCSSAssetsAndDependenciesUnchanged=True,privateOutputFiles=16,productionLikeOutputFiles=18,onlyAllowedParagraphAndCopyMarkerChanges=True,bodyAssetParity=dict(htmlBodiesByteIdentical=4,staticAssetsByteIdentical=9,headChangesExactlyAllowed=4),sitemapURLs=2,htmlFiles=4,faq=4,products=4,customerAssets=7),'source_delta_verified_scope_changed')
 readback=doc('source-save/source-readback-verification.json');exact(readback,dict(sourceRevision=REVIEWED_SOURCE_REVISION,sourceFiles=92,privateFiles=77,adapterFiles=15,projectGitTree='f995e27d2e95f14de2e533a23aada0261b394a15',sourceTreeSHA256=SOURCE_TREE_SHA),'separate_remote_readback_identity_changed')
 require(len(readback['rows'])==92 and {r['path'] for r in readback['rows']}==set(source),'separate_remote_readback_inventory_changed')
 for row in readback['rows']:
  require(all(same(row[k],source[row['path']][k]) for k in ['path','bytes','sha256','gitBlobSHA1']) and row['remoteCommit']==REVIEWED_SOURCE_REVISION and row['exactReviewedBytes'] is True,'separate_remote_readback_bytes_changed')
 observed=doc('source-save/downloaded-output-delta.json');exact(observed,dict(baseSourceCommit=BASE_SOURCE_REVISION,amendmentSourceCommit=REVIEWED_SOURCE_REVISION,outputFilesCompared=34,privateFiles=16,productionLikeFiles=18,customerLeavesChanged=1,copyDigestMarkersChangedPerBuild=4,assetsCSSAndOtherBytesUnchanged=True,homeSupport404VisibleBodyExact=True,pendingFindingResolved=False,actualPublicHTTPVerified=False),'saved_output_delta_scope_changed')
 return binding


def load_source_contract():
 raw=read(DIRECTORY/'production-source-contract.json');c=json.loads(raw);fixed=contract_template()
 require(set(c)==set(fixed)|{'sourceRevision','sourceTree'},'source_contract_schema')
 require(all(same(c[k],v) for k,v in fixed.items()),'source_contract_identity')
 for k in ['sourceRevision','sourceTree']:require(isinstance(c[k],str) and re.fullmatch('[0-9a-f]{40}',c[k]),'verified_full_commit_tree_required')
 frozen_manifests()
 require(sha(read(DIRECTORY/'bounded-contract.json'))==BOUNDED_CONTRACT_SHA,'bounded_scope_contract_changed')
 require(sha(read(DIRECTORY/'preview-equivalence.json'))==PREVIEW_EQUIVALENCE_SHA,'output_baseline_changed')
 require(c['sourceRevision']==SOURCE_REVISION and c['sourceTree']==SOURCE_GIT_TREE,'exact_saved_source_commit_tree_required')
 verify_content_reviews()
 return c

def load():
 c=load_source_contract();raw=read(DIRECTORY/'production-source-contract.json')
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
 scopes=['scripts/direct-'+NAMESPACE,'docs/direct-gwangju-gwangsan','docs/direct-'+NAMESPACE,'.github/workflows/gwangju-gwangsan-policy-correction-build-only.yml','.github/workflows/gwangju-gwangsan-policy-correction-publish.yml','.github/workflows/gwangju-gwangsan-policy-baseline-inspect.yml',*['site-factory/engine/'+n for n in HELPER_SHA256]]
 require(not git(root,'status','--porcelain','--untracked-files=all','--',*scopes).strip(),'control_checkout_changed')
 for scope in scopes:
  entries=[e for e in git(root,'ls-tree','-r','-z','HEAD','--',scope).split(b'\0') if e];require(entries,'tracked_control_missing:'+scope)
  for entry in entries:
   meta,name=entry.split(b'\t');mode,kind,blob=meta.decode().split();name=name.decode();require(mode=='100644' and kind=='blob','control_entry_invalid')
   data=regular_under(root,name);require(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob,'control_bytes_changed:'+name)
 for name,digest in HELPER_SHA256.items():require(sha(read(root/'site-factory/engine'/name))==digest,'existing_helper_changed:'+name)
 c,b,_=load();a=authorization(c,b);require(git(root,'show',a['revision']+':'+a['path'])==read(root/a['path']),'authorization_revision_bytes_mismatch')
 git(root,'merge-base','--is-ancestor',a['revision'],'HEAD')
 historical=historical_authorization(b);require(git(root,'show',historical['revision']+':'+historical['path'])==read(root/historical['path']),'historical_authorization_revision_bytes_mismatch');git(root,'merge-base','--is-ancestor',historical['revision'],'HEAD')
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
