"""Pinned Bukgu build and artifact gates. Never contact a provider or publish."""
import argparse,hashlib,json,os,re,shutil,subprocess
from html.parser import HTMLParser
from pathlib import Path
import production_output as output
DIRECTORY=Path(__file__).resolve().parent
# Keep the exact source validator bytes but bind its baseline to this isolated control.
output.EQUIVALENCE_PATH=DIRECTORY/'preview-equivalence.json'
REPOSITORY='joseungil-kr/fwith-site-factory';OWNER='joseungil-kr'
ROOT='site-factory/gwangju-bukgu-flower';BUILD_ROOT=ROOT+'/candidate';ADAPTER_ROOT=ROOT+'/release-adapter';BRANCH='source/gwangju-bukgu-production-preparation-20261015'
TITLE='[GWANGJU-BUKGU-PRODUCTION-BUILD] 20261015'
HOSTNAME='gwangju-bukgu.fwith.kr';ORIGIN='https://'+HOSTNAME;WORKER='gwangju-bukgu-flower-guide'
INPUT_SHA='8184f0b23b8b6d180bcd61c46ed1a35bfef165d09ee8896dce968fa15bb8566d'
PRIVATE_TREE_SHA='31612324d1f4101b9068747c16c7fcc5fa88cd727a842e9863dc7cb1c19cf64d'
ADAPTER_TREE_SHA='c70d6a7bb367cc9ef9edc7a1cb739282dd16304bd96f554f52c08b33900662b1'
SOURCE_TREE_SHA='757ec67969fea73236773222f97aad9e37f29fad5ebf5851ee96af27c12d1c08'
SOURCE_FILES=83;PRIVATE_FILES=68;ADAPTER_FILES=15
PRIVATE_MANIFEST_SHA='ed242ac51f515685a576da7772123d44ea1449d690966081df8857ef28aa33f4'
ADAPTER_MANIFEST_SHA='65214e22ff8edbeda9a81ef578a16413391d6b588d0981ee6ecbff050b88e882'
SOURCE_MANIFEST_SHA='1858f15e5b78eef692a6bbe5bd0396760494072395c28e6d57b62328936cc360'
PREVIEW_EQUIVALENCE_SHA='e3f46f842e5502bf0a60ff04f3f7ff0a7cedfa1f5a56fc7d358e3ac3c8f77613'
BOUNDED_CONTRACT_SHA='85f6b8b769802c36045bbe2c30e368e150c4b078dfebf412dd5ad0fb9ff9dd88'
CONTENT_REVIEW_BINDING_SHA='582d3b3cbd4b4004a4304d163d051e1590068b22ae68ca03098385024eb8e4a8'
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
 return dict(schemaVersion=1,state='approved',repository=REPOSITORY,sourceRoot=ROOT,siteKey='gwangju-bukgu-flower-direct',hostname=HOSTNAME,origin=ORIGIN,worker=WORKER,frozenInputSha256=INPUT_SHA,frozenPrivateTreeSha256=PRIVATE_TREE_SHA,sourceRevision=c['sourceRevision'],proof=output.PROOF,sitemapRoutes=output.ROUTES,htmlFiles=4,directoryRobots='noindex,follow',notFoundStatus=404,publicHttpVerified=False,indexNowSubmitted=False,boundedContractSha256=BOUNDED_CONTRACT_SHA,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED',approvals=dict(publication=True,hostBinding=True,indexNowProof=True))
def authorization_template(c):
 return dict(schemaVersion=1,recordType='user-authorization-not-readiness-proof',repository=REPOSITORY,sourceRoot=ROOT,siteKey='gwangju-bukgu-flower-direct',hostname=HOSTNAME,origin=ORIGIN,worker=WORKER,sourceRevision=c['sourceRevision'],sourceTree=c['sourceTree'],approvedOperations=['source-and-control-storage','production-build-and-QA','publication-after-own-gates','existing-provider-first-host-binding-with-no-overrides','existing-proof-and-two-URL-IndexNow-after-public-HTTP','public-build-publish-and-receipt-issues'],publicIssuesApproved=True,crossRegionPublicationOrderRequired=False,ownQualityAndSafetyGatesRequired=True,noNewCredentialsOrPermissionChanges=True,noDomainOwnershipTransferOrOverride=True)
def public_issue_approval_evidence():
 return dict(approvedAtUTC='2026-10-15T18:24:17Z',approved=True,scope='remaining-171-planned-regions-public-github-qa-publish-indexnow-receipts',publicData=['site-url','commit','qa-and-receipt-results'],secretsExcluded=True)
def authorization(c,b):
 d=json.loads(read(DIRECTORY/'authorization-binding.json'))
 require(isinstance(d,dict) and set(d)=={'schemaVersion','path','sha256','revision','publicIssuesApproved'} and type(d['schemaVersion']) is int and d['schemaVersion']==1,'authorization_descriptor_schema')
 require(d['publicIssuesApproved'] is True,'public_issue_approval_required')
 require(d['path']=='docs/direct-gwangju-bukgu/production-authorization-20261015.json' and re.fullmatch('[0-9a-f]{64}',d['sha256'] or '') and re.fullmatch('[0-9a-f]{40}',d['revision'] or ''),'pinned_authorization_required')
 raw=read(DIRECTORY.parents[1]/d['path']);require(sha(raw)==d['sha256'],'authorization_bytes_changed');a=json.loads(raw)
 expected=authorization_template(c);require(set(a)==set(expected)|{'authorizationEvidence'},'authorization_schema')
 require(all(same(a[k],v) for k,v in expected.items()),'exact_bukgu_authorization_required')
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
 """Bind native Bukgu review schemas, exact source projections and immutable meaning."""
 raw=read(DIRECTORY/'content-review-binding.json');require(sha(raw)==CONTENT_REVIEW_BINDING_SHA,'content_review_binding_changed');binding=json.loads(raw)
 expected=dict(schemaVersion=1,region='bukgu',namespace='gwangju-bukgu',scope='retained-manuscript-and-local-code-output-reviews-not-production-pass',sourceTreeSHA256=SOURCE_TREE_SHA,sourceFiles=SOURCE_FILES,frozenPrivateTreeSha256=PRIVATE_TREE_SHA,inputSha256=INPUT_SHA,productionGatePassed=False,staticQualityIsProductionPass=False)
 require(set(binding)==set(expected)|{'copySHA256','renderPlanSHA256','metadataSHA256','customerReviewBindingSHA256','codeReviewBindingSHA256','files'} and all(same(binding[k],v) for k,v in expected.items()),'content_review_source_identity_mismatch')
 rows=binding['files'];require(type(rows) is list and len(rows)==25 and all(type(row) is dict and set(row)=={'path','originalPath','bytes','sha256'} for row in rows),'content_review_inventory_schema')
 originals={};docs={};original_paths={'implementation-review-binding.json': 'bukgu-customer-copy-independent-20261015/implementation-review-binding.json', 'original-clause-assessment.json': 'bukgu-customer-copy-independent-20261015/original-clause-assessment.json', 'visible-string-assessment.json': 'bukgu-customer-copy-independent-20261015/visible-string-assessment.json', 'purchase-intent-assessment.json': 'bukgu-customer-copy-independent-20261015/purchase-intent-assessment.json', 'render-checklist.json': 'bukgu-customer-copy-independent-20261015/render-checklist.json', 'reviewed-input-projection.json': 'bukgu-customer-copy-independent-20261015/reviewed-input-projection.json', 'independent-copy-review-r1.json': 'bukgu-customer-copy-independent-20261015/independent-review-r1.json', 'closing-main-reconciliation.json': 'bukgu-customer-copy-independent-20261015/evidence/closing-main-reconciliation.json', 'manuscript-review.ko.md': 'bukgu-customer-copy-independent-20261015/REVIEW.ko.md', 'source-input-projection.json': 'bukgu-local-implementation-20261015/source/inputs/reviewed-input-projection.json', 'implementation-code-review-binding.json': 'bukgu-candidate-code-independent-20261015/implementation-code-review-binding.json', 'independent-code-review.json': 'bukgu-candidate-code-independent-20261015/independent-code-review.json', 'candidate-code-review.ko.md': 'bukgu-candidate-code-independent-20261015/README.ko.md', 'code-review-publication-manifest.json': 'bukgu-candidate-code-independent-20261015/PUBLICATION-MANIFEST.json', 'reviewed-source-manifest.json': 'bukgu-candidate-code-independent-20261015/evidence/source-manifest.json', 'private-manifest.json': 'bukgu-candidate-code-independent-20261015/evidence/private-manifest.json', 'adapter-manifest.json': 'bukgu-candidate-code-independent-20261015/evidence/adapter-manifest.json', 'binding-and-reuse-checks.json': 'bukgu-candidate-code-independent-20261015/evidence/binding-and-reuse-checks.json', 'full-source-diff-reverification.json': 'bukgu-candidate-code-independent-20261015/evidence/full-source-diff-reverification.json', 'independent-output-inspection.json': 'bukgu-candidate-code-independent-20261015/evidence/independent-output-inspection.json', 'test-counts.json': 'bukgu-candidate-code-independent-20261015/evidence/test-counts.json', 'independent-semantic-negatives.json': 'bukgu-candidate-code-independent-20261015/evidence/independent-semantic-negatives.json', 'independent-runtime-semantics.json': 'bukgu-candidate-code-independent-20261015/evidence/independent-runtime-semantics.json', 'verified-output-files.json': 'bukgu-candidate-code-independent-20261015/evidence/verified-output-files.json', 'source-final-reverification.json': 'bukgu-candidate-code-independent-20261015/evidence/source-final-reverification.json'}
 for row in rows:
  name=row['path'];original=row['originalPath']
  require(type(name) is str and name.startswith('docs/direct-gwangju-bukgu/content-review-20261015/') and '..' not in Path(name).parts and '\\' not in name,'content_review_path_invalid')
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
 for name,keys in {'implementation-review-binding.json': ['actualBrowserChecked', 'actualBuildChecked', 'actualHTMLChecked', 'actualPublicHTTPChecked', 'allowedNextStage', 'assessmentScope', 'assetManifest', 'closingGuidanceSourceCommit', 'closingReconciliation', 'coreHubLaunchStatus', 'customerCopy', 'customerCopySHA256', 'frozenAuthorManifest', 'fullLaunchStatus', 'guidanceSourceCommit', 'humanReview', 'independentReview', 'inputProjection', 'invalidatesOn', 'metadata', 'nationalOrder', 'officialCode', 'originalClauseReview', 'pathBase', 'publicationEligible', 'purchaseIntentMetadataSHA256', 'purchaseIntentReview', 'region', 'renderChecklist', 'renderPlan', 'renderPlanSHA256', 'reviewedUTC', 'revision', 'schemaVersion', 'sourceCommit', 'sourceCommitBinding', 'visibleStringReview', 'visibleStrings'], 'original-clause-assessment.json': ['actualHTMLChecked', 'assessmentScope', 'denominator', 'facilityClauses', 'guidanceClauses', 'merchantPolicyClauses', 'mustFixRemaining', 'originalInput', 'schemaVersion'], 'visible-string-assessment.json': ['allVisibleStringInventoryReviewed', 'count', 'customerCopySHA256', 'footerReuses', 'mustFixRemaining', 'schemaVersion', 'strings'], 'purchase-intent-assessment.json': ['customerCopySHA256', 'mustFixRemaining', 'originalityReview', 'pageRoleReview', 'questions', 'schemaVersion', 'unverified', 'verdict', 'wordCountReview'], 'render-checklist.json': ['actualBrowserChecked', 'actualHTMLChecked', 'actualPublicHTTPChecked', 'checks', 'publicationEligible', 'renderPlanSHA256', 'schemaVersion', 'status'], 'reviewed-input-projection.json': ['authorOriginalPathBase', 'files', 'mappedFileCount', 'originalAuthorManifestSHA256', 'pathBase', 'publicWebsiteBoundary', 'purpose', 'schemaVersion'], 'independent-copy-review-r1.json': ['actualBrowserChecked', 'actualBuildChecked', 'actualHTMLChecked', 'actualPublicHTTPChecked', 'assessmentScope', 'closingGuidanceSourceCommit', 'closurePolicy', 'coreHubLaunchStatus', 'customerCopySHA256', 'directlyConfirmed', 'fullLaunchStatus', 'guidanceSourceCommit', 'humanReview', 'judgments', 'mandatoryRevisions', 'mustFixRemaining', 'nationalOrder', 'officialCode', 'operations', 'pathBase', 'publicationEligible', 'purchaseIntentMetadataSHA256', 'region', 'renderPlanSHA256', 'reviewFiles', 'reviewedUTC', 'revision', 'schemaVersion', 'searchIntentCompletenessVerdict', 'sourceCommit', 'styleQualityVerdict', 'toolReports', 'unverified', 'verdict'], 'closing-main-reconciliation.json': ['baseline', 'classification', 'closing', 'compareURL', 'files', 'guidanceChanged', 'mainURL', 'meaning', 'observedAtUTC', 'progressChanged', 'schemaVersion', 'status', 'totalCommits', 'tree'], 'source-input-projection.json': ['bindingSHA256', 'files', 'fullAuthorManifestFilesRehashed', 'fullClosedReviewFilesRehashed', 'originalPathBase', 'reviewSHA256', 'schemaVersion', 'sourcePublicationScope'], 'implementation-code-review-binding.json': ['actualActionsBuildChecked', 'actualBrowserChecked', 'actualLocalBuildChecked', 'actualPublicHTTPChecked', 'actualStaticHTMLChecked', 'adapterFiles', 'adapterSourceManifest', 'adapterTreeSHA256', 'assessmentScope', 'closurePolicy', 'coreHubLaunchStatus', 'customerCopySHA256', 'embeddedPrivateSourceManifestSHA256', 'fullLaunchStatus', 'httpExceptionMutationCases', 'independentCodeReview', 'independentOutputMutationCases', 'independentRuntimeCases', 'indexNowReceiptChecked', 'laterGates', 'mustFixRemaining', 'nationalOrder', 'nativeCommandCount', 'nativeTestCases', 'officialCode', 'originalAssessmentDenominator', 'originalAssetPixelsChecked', 'originalClosedManuscriptBindingSHA256', 'originalManuscriptReviewSHA256', 'originalManuscriptVerdictPreserved', 'pathBase', 'privateFiles', 'privateSourceManifest', 'privateTreeSHA256', 'providerOwnershipChecked', 'publicationEligible', 'region', 'renderPlanSHA256', 'repository', 'schema', 'schemaVersion', 'sourceCommit', 'sourceCommitBinding', 'sourceFiles', 'sourceManifest', 'sourceRemoteSaved', 'sourceRoot', 'sourceTreeSHA256', 'trustedReleaseControlsChecked', 'verdict'], 'independent-code-review.json': ['actualActionsBuildChecked', 'actualBrowserChecked', 'actualLocalBuildChecked', 'actualPublicHTTPChecked', 'actualStaticHTMLChecked', 'adapterFiles', 'assessmentScope', 'closurePolicy', 'coreHubLaunchStatus', 'customerCopySHA256', 'directlyConfirmed', 'evidence', 'fullLaunchStatus', 'indexNowReceiptChecked', 'judgment', 'mandatoryRevisions', 'mustFixRemaining', 'nationalOrder', 'newManuscriptOrFactualReviewPerformed', 'notVerified', 'officialCode', 'operations', 'originalAssessmentBytesUnchanged', 'originalAssessmentDenominator', 'originalAssetPixelsChecked', 'originalClosedManuscriptBindingSHA256', 'originalManuscriptReviewSHA256', 'originalManuscriptVerdictPreserved', 'pathBase', 'predecessorScoreReused', 'privateFiles', 'providerOwnershipChecked', 'publicationEligible', 'region', 'renderPlanSHA256', 'reviewedUTC', 'schema', 'schemaVersion', 'sourceCommit', 'sourceFiles', 'sourceManifestSHA256', 'sourceRemoteSaved', 'sourceRoot', 'sourceTreeSHA256', 'toolReportsAndLimits', 'trustedReleaseControlsChecked', 'verdict', 'verificationIncidents'], 'code-review-publication-manifest.json': ['actualBrowserChecked', 'actualPublicHTTPChecked', 'fileCount', 'files', 'pathBase', 'reviewClosed', 'schema', 'schemaVersion', 'scope', 'sourceCommit'], 'reviewed-source-manifest.json': ['actualRemoteCommit', 'fileCount', 'files', 'remoteSaved', 'treeSHA256'], 'private-manifest.json': ['actualRemoteCommit', 'fileCount', 'files', 'remoteSaved', 'treeSHA256'], 'adapter-manifest.json': ['actualRemoteCommit', 'fileCount', 'files', 'remoteSaved', 'treeSHA256'], 'binding-and-reuse-checks.json': ['adapterFiles', 'allSourceBytesAndGitBlobsChecked', 'authorClosureFilesRehashed', 'completeNoncopyDiffReproduced', 'coreReferencesChecked', 'exactArchiveEntries', 'freshMain', 'freshRemoteQueryByThisReviewer', 'freshWorkflowFiles', 'fullDiffManifestEntriesRehashed', 'lockDependencyGraphUnchanged', 'oldSourceTreeIsRetainedToolReport', 'originalAssessmentDenominator', 'originalReviewClosureFilesRehashed', 'originalSourceCommit', 'originalSourceFilesComparedToRetainedGitTree', 'originalVerdictUnmodified', 'packagedProjectionOriginalsChecked', 'privateFiles', 'sameByteReusedFiles', 'schemaVersion', 'sourceFiles', 'sourceManifestSHA256', 'sourcePrivatePathFindings', 'sourceTreeSHA256'], 'full-source-diff-reverification.json': ['completeDiffReproducedFromActualBytes', 'customerInputChangesReviewed', 'fullDiffLines', 'fullDiffSHA256', 'noncopyChangesReviewed', 'noncopyDiffLines', 'noncopyDiffSHA256', 'previousRemoteReadbackFiles', 'previousSourceCommit', 'sourceFiles'], 'independent-output-inspection.json': ['actualBrowserOrPublicHTTP', 'assets', 'htmlBodiesByteIdentical', 'internalInboundSources', 'offlineFileCount', 'originalRebuildAllFilesByteIdentical', 'pages', 'privateFileCount', 'realHTTP404Verified', 'reviewedStrings', 'sitemapURLs', 'standardLibraryParserIndependentOfCandidate', 'staticAssetsByteIdentical', 'status'], 'test-counts.json': ['allCommandsExitZero', 'caseCounts', 'commands', 'httpVariantSubcasesInsideOneCase', 'httpsVariantSubcasesInsideOneCase', 'nativeCases'], 'independent-semantic-negatives.json': ['cases', 'offlineCases', 'privateCases', 'status', 'totalCases'], 'independent-runtime-semantics.json': ['cases', 'passed', 'results', 'scope'], 'verified-output-files.json': ['artifactUploaded', 'outputs', 'publicHTTPChecked', 'schemaVersion', 'sourceTreeSHA256'], 'source-final-reverification.json': ['mandatorySourceChanges', 'originalAuthorFilesRehashed', 'originalClosedReviewFilesRehashed', 'originalSourceAndIndependentCopyBothMatch', 'remoteSaved', 'schemaVersion', 'sourceCommit', 'sourceFilesRehashed', 'sourceManifestSHA256', 'sourceTreeSHA256', 'status']}.items():require(type(doc(name)) is dict and set(doc(name))==set(keys),'original_review_schema_required:'+name)
 cp=doc('implementation-review-binding.json');manuscript=doc('independent-copy-review-r1.json');code=doc('implementation-code-review-binding.json');report=doc('independent-code-review.json')
 for obj in [cp,manuscript,code,report]:exact(obj,dict(schemaVersion=1,region='bukgu',officialCode='12300',nationalOrder=34),'review_region_identity_mismatch')
 for obj in [cp,manuscript]:exact(obj,dict(assessmentScope='MANUSCRIPT_AND_RENDER_PLAN_ONLY',revision='bukgu-copy-r1-20261015',customerCopySHA256=binding['copySHA256'],renderPlanSHA256=binding['renderPlanSHA256'],purchaseIntentMetadataSHA256=binding['metadataSHA256'],sourceCommit=None,actualHTMLChecked=False,actualBuildChecked=False,actualBrowserChecked=False,actualPublicHTTPChecked=False,publicationEligible=False,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED'),'manuscript_scope_or_unverified_flags_changed')
 require(sha(docs['implementation-review-binding.json'][0])==binding['customerReviewBindingSHA256'] and sha(docs['implementation-code-review-binding.json'][0])==binding['codeReviewBindingSHA256'],'review_top_level_binding_changed')
 exact(manuscript,dict(verdict='MANUSCRIPT_AND_SPEC_READY_FOR_IMPLEMENTATION_NOT_PRODUCTION_PASS',mustFixRemaining=[],mandatoryRevisions=[]),'manuscript_verdict_required')
 clauses=doc('original-clause-assessment.json');require(clauses['denominator']['guidanceNonemptyNonheadingLines']==154 and len(clauses['guidanceClauses'])==154 and len(clauses['merchantPolicyClauses'])==15 and len(clauses['facilityClauses'])==1,'original_154_15_1_denominators_required')
 visible=doc('visible-string-assessment.json');require(visible['count']==115 and len(visible['strings'])==115 and visible['customerCopySHA256']==binding['copySHA256'],'original_115_visible_strings_required')
 checklist=doc('render-checklist.json');require(checklist['status']=='REQUIRED_NEXT_STAGE_NOT_EXECUTED' and len(checklist['checks'])==13 and len({r['id'] for r in checklist['checks']})==13 and all(r['status']=='NOT_EXECUTED' for r in checklist['checks']) and all(checklist[k] is False for k in ['actualHTMLChecked','actualBrowserChecked','actualPublicHTTPChecked','publicationEligible']),'original_render_checks_not_production_pass')
 source=manifest('source-manifest.json',SOURCE_MANIFEST_SHA,SOURCE_FILES,SOURCE_TREE_SHA)
 projection=doc('source-input-projection.json');exact(projection,dict(schemaVersion=1,originalPathBase='BUKGU_CLOSED_REVIEW_ROOT',reviewSHA256=sha(docs['independent-copy-review-r1.json'][0]),bindingSHA256=binding['customerReviewBindingSHA256'],fullAuthorManifestFilesRehashed=51,fullClosedReviewFilesRehashed=77),'source_projection_identity_required')
 require(type(projection['files']) is list and len(projection['files'])==26,'source_projection_inventory_required');by_original={}
 for row in projection['files']:
  require(set(row)=={'originalPath','packagedPath','bytes','sha256'} and type(row['bytes']) is int and row['originalPath'] not in by_original,'source_projection_row_schema');name=row['packagedPath'];require(name in source and source[name]['sha256']==row['sha256'] and source[name]['bytes']==row['bytes'],'projection_source_bytes_mismatch');by_original[row['originalPath']]=row
 for field,ref in cp.items():
  if type(ref) is not dict or set(ref)!={'path','bytes','sha256'}:continue
  row=by_original.get(ref['path']);require(row is not None and type(ref['bytes']) is int and ref['bytes']==row['bytes'] and ref['sha256']==row['sha256'],'copy_reference_source_bytes_mismatch:'+field)
 for row in rows:
  if row['originalPath'].startswith('bukgu-customer-copy-independent-20261015/'):
   original=row['originalPath'].removeprefix('bukgu-customer-copy-independent-20261015/');source_row=by_original.get(original);require(source_row is not None and source_row['sha256']==row['sha256'] and source_row['bytes']==row['bytes'],'original_review_source_bytes_mismatch')
 source_row=source['inputs/reviewed-input-projection.json'];require(source_row['sha256']==sha(docs['source-input-projection.json'][0]) and source_row['bytes']==len(docs['source-input-projection.json'][0]),'source_projection_bytes_mismatch')
 for obj in [code,report]:exact(obj,dict(sourceCommit=None,sourceRemoteSaved=False,sourceFiles=SOURCE_FILES,privateFiles=PRIVATE_FILES,adapterFiles=ADAPTER_FILES,sourceTreeSHA256=SOURCE_TREE_SHA,publicationEligible=False,actualBrowserChecked=False,actualPublicHTTPChecked=False,actualActionsBuildChecked=False,providerOwnershipChecked=False,trustedReleaseControlsChecked=False,indexNowReceiptChecked=False,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED',mustFixRemaining=[]),'code_source_identity_or_flags_mismatch')
 require(code['privateTreeSHA256']==PRIVATE_TREE_SHA and code['adapterTreeSHA256']==ADAPTER_TREE_SHA and same(code['originalAssessmentDenominator'],dict(guidance=154,policy=15,facility=1)),'code_split_or_denominators_mismatch')
 require(code['originalClosedManuscriptBindingSHA256']==binding['customerReviewBindingSHA256'] and code['originalManuscriptReviewSHA256']==sha(docs['independent-copy-review-r1.json'][0]),'code_manuscript_reference_identity_mismatch')
 prefix='bukgu-candidate-code-independent-20261015/'
 for key in ['sourceManifest','independentCodeReview','privateSourceManifest','adapterSourceManifest']:reference(code[key],prefix)
 require(doc('private-manifest.json')['files']==list(manifest('private-source-manifest.json',PRIVATE_MANIFEST_SHA,PRIVATE_FILES,PRIVATE_TREE_SHA).values()) and doc('adapter-manifest.json')['files']==list(manifest('adapter-manifest.json',ADAPTER_MANIFEST_SHA,ADAPTER_FILES,ADAPTER_TREE_SHA).values()),'code_split_manifest_identity_mismatch')
 reviewed=doc('reviewed-source-manifest.json');require(reviewed['files']==list(source.values()) and reviewed['fileCount']==SOURCE_FILES and reviewed['treeSHA256']==SOURCE_TREE_SHA,'code_source_manifest_identity_mismatch')
 require(type(report['evidence']) is list and len(report['evidence'])==11 and len({r['path'] for r in report['evidence']})==11,'code_evidence_inventory_mismatch')
 for ref in report['evidence']:reference(ref,prefix)
 public_manifest=doc('code-review-publication-manifest.json');exact(public_manifest,dict(schema='bukgu-independent-code-review-publication-files/v1',fileCount=14,reviewClosed=True),'code_publication_manifest_required')
 require(type(public_manifest['files']) is list and len(public_manifest['files'])==14 and {r['path'] for r in public_manifest['files']}=={'README.ko.md','independent-code-review.json','implementation-code-review-binding.json'}|{r['path'] for r in report['evidence']},'code_publication_file_scope_required')
 for ref in public_manifest['files']:reference(ref,prefix)
 # Canonical semantic digests also reject type, nested finding and count mutations even when envelopes are rehashed.
 for name,digest in {'implementation-review-binding.json': '5c6bb1ddb078646727d64522c8303314fd7deac341687da10d54ea1bc9b45e39', 'original-clause-assessment.json': 'd4f8745b41d71fc0b48b53142e887159eb737a878ff0ec4ff593d86ec303dcf0', 'visible-string-assessment.json': '0714bed403e768f7fb839b76834a96e1b21e697690c9036bda2268b87d6c87a9', 'purchase-intent-assessment.json': '27ac1d447c29e6a93ad6b8c65538972ee359e11fd356428f61e26b014e877f36', 'render-checklist.json': '6025758906d2fe2e1097ad5b1dc4aa03673b13e32eb124e2a9154ac461f96a23', 'reviewed-input-projection.json': 'bcb2afdfabe6ac8cf6d55c5c965cbbe1fb234f10069042730b537d0318310fed', 'independent-copy-review-r1.json': 'fd2ffe20647eaa0974dfe208e66445dca4f1b772c876cffd4d742738ae7dab58', 'closing-main-reconciliation.json': '1e2be68a21e453f3503df0afc2e26a96fbcf60254ef3630bf628a2ae3555f7a4', 'source-input-projection.json': '94af0f4e81f222e1436e8dedb7ca6022a4a2ffbefb8261abf593dc8711e9c194', 'implementation-code-review-binding.json': '9061dfabc7a9c8a53bd37a4694f78700788385b0b27be43b23b7586d09b54733', 'independent-code-review.json': '6e58bc8aebe8d936170a8090fb3436d711098d2fb6ffa0f9550e61877db7fab5', 'code-review-publication-manifest.json': '97b2c891c7cee78c7c6a579501e3b3dbd4536e95bb3ae8996cc5dc9ea9e7b0d5', 'reviewed-source-manifest.json': 'a87d71e35fa06fe72bb1b88079d00b4cc811f9c7a23d8f967acc5eb63cabd476', 'private-manifest.json': '52f43697a0b924735998bf013d56dc7edc78b21c2a8f4cd6be54813343653a1d', 'adapter-manifest.json': 'f6a8d4f98ac21bb47201f3dc2d522c72e4d59d2d0d05b4aa63741e1dca5c5e1a', 'binding-and-reuse-checks.json': '2950def258c8620e7bb4604163909e0a7cf4020326b792a4bcc78085ca0df379', 'full-source-diff-reverification.json': '942bcf25c2b112be46bfcedc6a975d4710e402fb936e67086efb0ebec8e67677', 'independent-output-inspection.json': 'f358860a8daf16be5464f3318a741ab7a6c861c490b1a42d680075c2a57ab2b7', 'test-counts.json': 'b1779189afa5d837d297bb9a1fb7da67954ce63a6cbeb5f965bcb7f5c78e0854', 'independent-semantic-negatives.json': '4a7118f8d3aa097c4245b7bcfd9c827c02d1b0d6419ba24e88f0e7d53d0a8846', 'independent-runtime-semantics.json': '05c7c8f3f15f80b7941094f8634061c04e3375895418d487f23ce5c61374ec21', 'verified-output-files.json': '227f4fa8b5b2f33c29f85e5348d8a6a841e5319129256b60741461b25bd55dcb', 'source-final-reverification.json': 'c51c9b32c3ac3383bd2ce2b3ecb3a406b8994a5c8ca0b3ebc727998c539cf7fa'}.items():require(sha(json.dumps(doc(name),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())==digest,'original_review_meaning_changed:'+name)
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
 require(all(same(b[k],v) for k,v in expected.items()),'exact_bukgu_binding_required')
 authorization(c,b)
 return c,b,sha(br)

def trusted_control(env):
 require(env.get('GITHUB_REPOSITORY')==REPOSITORY and env.get('GITHUB_REF')=='refs/heads/main','owner_main_required')
 require(env.get('GITHUB_ACTOR')==OWNER and env.get('GITHUB_TRIGGERING_ACTOR')==OWNER and env.get('GITHUB_RUN_ATTEMPT')=='1','owner_first_attempt_required')
 require(env.get('GITHUB_EVENT_NAME')=='issues' and re.fullmatch('[1-9][0-9]*',env.get('GITHUB_RUN_ID','')),'actual_issue_run_required')
 root=DIRECTORY.parents[1];revision=env.get('GITHUB_SHA','');require(re.fullmatch('[0-9a-f]{40}',revision),'control_revision_required')
 require(git(root,'rev-parse','HEAD').decode().strip()==revision,'actual_control_revision_mismatch')
 scopes=['scripts/direct-gwangju-bukgu','docs/direct-gwangju-bukgu','.github/workflows/gwangju-bukgu-production-build-only.yml','.github/workflows/gwangju-bukgu-production-publish.yml',*['site-factory/engine/'+n for n in HELPER_SHA256]]
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
 require(read(adapter/'scripts/bukgu_release_output.py')==read(DIRECTORY/'production_output.py'),'source_control_output_validator_mismatch')
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
