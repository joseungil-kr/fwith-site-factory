"""Pinned Namgu build and artifact gates. Never contact a provider or publish."""
import argparse,hashlib,json,os,re,shutil,subprocess
from html.parser import HTMLParser
from pathlib import Path
import production_output as output
DIRECTORY=Path(__file__).resolve().parent
# Keep the exact source validator bytes but bind its baseline to this isolated control.
output.EQUIVALENCE_PATH=DIRECTORY/'preview-equivalence.json'
REPOSITORY='joseungil-kr/fwith-site-factory';OWNER='joseungil-kr'
ROOT='site-factory/gwangju-namgu-flower';BUILD_ROOT=ROOT+'/candidate';ADAPTER_ROOT=ROOT+'/release-adapter';BRANCH='source/gwangju-namgu-production-preparation-20261015'
TITLE='[GWANGJU-NAMGU-PRODUCTION-BUILD] 20261015'
HOSTNAME='gwangju-namgu.fwith.kr';ORIGIN='https://'+HOSTNAME;WORKER='gwangju-namgu-flower-guide'
INPUT_SHA='32cb58009bb73093676362268a9a7c9110e336ad6f500d5fd30779a562ae101f'
PRIVATE_TREE_SHA='c4565e2ca2085c5191e1f44adb635054977265cb4f650c83d4c1c8f566819b02'
ADAPTER_TREE_SHA='1f6aa8791837b0d239dee94e21212546538c444346c199aeee73addffeaf2089'
SOURCE_TREE_SHA='ee961f55693294866d2e3ac607d517d74bf41072590c02f3fa11e47f95e19d9c'
SOURCE_FILES=82;PRIVATE_FILES=67;ADAPTER_FILES=15
PRIVATE_MANIFEST_SHA='1ebe39ec3f9e29487482395580afda6acd5409bc27ec7f3b6481ab337cc79e6a'
ADAPTER_MANIFEST_SHA='67801949a7e8da15535540a2321b403187923bb5b142c6364cc7fadf202a85a8'
SOURCE_MANIFEST_SHA='3f9ed697592511286651a4f2a49d0e4c6e3455ef7eeab486df2683791f967c86'
PREVIEW_EQUIVALENCE_SHA='225478fccf7cd6d390c112700eadab78b1e5257858061a7a2d348cef2d787135'
BOUNDED_CONTRACT_SHA='8de2d9ebbe3db1a9fbea00dbc042b91724ec5203cdfb3bdee12648e637dee33d'
CONTENT_REVIEW_BINDING_SHA='a5cc821573cc326ce809fd37965e12863e19bf2b1e8f6ae16d8d9a38d9905deb'
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
 return dict(schemaVersion=1,state='approved',repository=REPOSITORY,sourceRoot=ROOT,siteKey='gwangju-namgu-flower-direct',hostname=HOSTNAME,origin=ORIGIN,worker=WORKER,frozenInputSha256=INPUT_SHA,frozenPrivateTreeSha256=PRIVATE_TREE_SHA,sourceRevision=c['sourceRevision'],proof=output.PROOF,sitemapRoutes=output.ROUTES,htmlFiles=4,directoryRobots='noindex,follow',notFoundStatus=404,publicHttpVerified=False,indexNowSubmitted=False,boundedContractSha256=BOUNDED_CONTRACT_SHA,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED',approvals=dict(publication=True,hostBinding=True,indexNowProof=True))
def authorization_template(c):
 return dict(schemaVersion=1,recordType='user-authorization-not-readiness-proof',repository=REPOSITORY,sourceRoot=ROOT,siteKey='gwangju-namgu-flower-direct',hostname=HOSTNAME,origin=ORIGIN,worker=WORKER,sourceRevision=c['sourceRevision'],sourceTree=c['sourceTree'],approvedOperations=['source-and-control-storage','production-build-and-QA','publication-after-own-gates','existing-provider-first-host-binding-with-no-overrides','existing-proof-and-two-URL-IndexNow-after-public-HTTP','public-build-publish-and-receipt-issues'],publicIssuesApproved=True,crossRegionPublicationOrderRequired=False,ownQualityAndSafetyGatesRequired=True,noNewCredentialsOrPermissionChanges=True,noDomainOwnershipTransferOrOverride=True)
def public_issue_approval_evidence():
 return dict(approvedAtUTC='2026-10-15T18:24:17Z',approved=True,scope='remaining-171-planned-regions-public-github-qa-publish-indexnow-receipts',publicData=['site-url','commit','qa-and-receipt-results'],secretsExcluded=True)
def authorization(c,b):
 d=json.loads(read(DIRECTORY/'authorization-binding.json'))
 require(isinstance(d,dict) and set(d)=={'schemaVersion','path','sha256','revision','publicIssuesApproved'} and type(d['schemaVersion']) is int and d['schemaVersion']==1,'authorization_descriptor_schema')
 require(d['publicIssuesApproved'] is True,'public_issue_approval_required')
 require(d['path']=='docs/direct-gwangju-namgu/production-authorization-20261015.json' and re.fullmatch('[0-9a-f]{64}',d['sha256'] or '') and re.fullmatch('[0-9a-f]{40}',d['revision'] or ''),'pinned_authorization_required')
 raw=read(DIRECTORY.parents[1]/d['path']);require(sha(raw)==d['sha256'],'authorization_bytes_changed');a=json.loads(raw)
 expected=authorization_template(c);require(set(a)==set(expected)|{'authorizationEvidence'},'authorization_schema')
 require(all(same(a[k],v) for k,v in expected.items()),'exact_namgu_authorization_required')
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
 """Bind original Namgu review schemas and path-only successor; never imply publication approval."""
 raw=read(DIRECTORY/'content-review-binding.json');require(sha(raw)==CONTENT_REVIEW_BINDING_SHA,'content_review_binding_changed')
 binding=json.loads(raw)
 expected=dict(schemaVersion=1,region='namgu',namespace='gwangju-namgu',scope='retained-manuscript-and-local-code-output-reviews-not-production-pass',sourceTreeSHA256=SOURCE_TREE_SHA,sourceFiles=SOURCE_FILES,frozenPrivateTreeSha256=PRIVATE_TREE_SHA,inputSha256=INPUT_SHA,productionGatePassed=False,staticQualityIsProductionPass=False)
 require(set(binding)==set(expected)|{'copySHA256','renderPlanSHA256','metadataSHA256','customerReviewBindingSHA256','codeReviewBindingSHA256','files'} and all(same(binding[k],v) for k,v in expected.items()),'content_review_source_identity_mismatch')
 rows=binding['files'];require(type(rows) is list and len(rows)==24 and all(type(row) is dict and set(row)=={'path','originalPath','bytes','sha256'} for row in rows),'content_review_inventory_schema')
 originals={};docs={};original_paths={'implementation-review-binding.public-r1.json': 'namgu-customer-copy-independent-20261015/publication-r1/implementation-review-binding.public-r1.json', 'independent-copy-review-r2.json': 'namgu-customer-copy-independent-20261015/independent-review-r2.json', 'original-clause-assessment.json': 'namgu-customer-copy-independent-20261015/original-clause-assessment.json', 'purchase-intent-assessment.json': 'namgu-customer-copy-independent-20261015/purchase-intent-assessment.json', 'render-checklist.json': 'namgu-customer-copy-independent-20261015/render-checklist.json', 'closing-main-reconciliation.json': 'namgu-customer-copy-independent-20261015/evidence/closing-main-reconciliation.json', 'manuscript-review.ko.md': 'namgu-customer-copy-independent-20261015/REVIEW.ko.md', 'publication-path-reconciliation-r1.json': 'namgu-customer-copy-independent-20261015/publication-r1/publication-path-reconciliation-r1.json', 'reviewed-input-projection.json': 'namgu-customer-copy-independent-20261015/publication-r1/reviewed-input-projection.json', 'implementation-code-review-binding.json': 'namgu-candidate-code-independent-20261015/implementation-code-review-binding.json', 'independent-code-review.json': 'namgu-candidate-code-independent-20261015/independent-code-review.json', 'candidate-code-review.ko.md': 'namgu-candidate-code-independent-20261015/README.ko.md', 'code-review-publication-manifest.json': 'namgu-candidate-code-independent-20261015/PUBLICATION-MANIFEST.json', 'reviewed-source-manifest.json': 'namgu-candidate-code-independent-20261015/evidence/source-manifest.json', 'private-manifest.json': 'namgu-candidate-code-independent-20261015/evidence/private-manifest.json', 'adapter-manifest.json': 'namgu-candidate-code-independent-20261015/evidence/adapter-manifest.json', 'binding-and-reuse-checks.json': 'namgu-candidate-code-independent-20261015/evidence/binding-and-reuse-checks.json', 'independent-output-inspection.json': 'namgu-candidate-code-independent-20261015/evidence/independent-output-inspection.json', 'test-counts.json': 'namgu-candidate-code-independent-20261015/evidence/test-counts.json', 'independent-semantic-negatives.json': 'namgu-candidate-code-independent-20261015/evidence/independent-semantic-negatives.json', 'independent-runtime-semantics.json': 'namgu-candidate-code-independent-20261015/evidence/independent-runtime-semantics.json', 'verified-output-files.json': 'namgu-candidate-code-independent-20261015/evidence/verified-output-files.json', 'capture-fixture-checks.json': 'namgu-candidate-code-independent-20261015/evidence/capture-fixture-checks.json', 'source-final-reverification.json': 'namgu-candidate-code-independent-20261015/evidence/source-final-reverification.json'}
 for row in rows:
  name=row['path'];original=row['originalPath']
  require(type(name) is str and name.startswith('docs/direct-gwangju-namgu/content-review-20261015/') and '..' not in Path(name).parts and '\\' not in name,'content_review_path_invalid')
  require(type(original) is str and not Path(original).is_absolute() and '..' not in Path(original).parts and '\\' not in original and original not in originals and Path(name).name not in docs,'content_review_original_path_invalid')
  require(original_paths.get(Path(name).name)==original,'original_document_path_changed')
  data=read(DIRECTORY.parents[1]/name);require(type(row['bytes']) is int and len(data)==row['bytes'] and sha(data)==row['sha256'],'content_review_bytes_changed')
  originals[original]=row;docs[Path(name).name]=(data,json.loads(data) if name.endswith('.json') else None)
 require(set(docs)==set(original_paths),'exact_review_document_inventory_required')
 def doc(name):require(name in docs,'review_document_missing:'+name);return docs[name][1]
 def reference(ref,origin=None):
  require(type(ref) is dict and set(ref)=={'path','bytes','sha256'} and type(ref['bytes']) is int and ref['bytes']>0 and re.fullmatch('[0-9a-f]{64}',ref['sha256'] or ''),'review_reference_schema')
  row=originals.get(ref['path']);require(row is not None and (origin is None or ref['path']==origin) and ref['bytes']==row['bytes'] and ref['sha256']==row['sha256'],'review_reference_bytes_mismatch')
 def exact(obj,values,error):require(type(obj) is dict and all(k in obj and same(obj[k],v) for k,v in values.items()),error)
 def identity(obj):exact(obj,dict(schemaVersion=1,region='namgu',officialCode='12270',nationalOrder=33),'review_region_identity_mismatch')
 cp=doc('implementation-review-binding.public-r1.json');manuscript=doc('independent-copy-review-r2.json');code=doc('implementation-code-review-binding.json');report=doc('independent-code-review.json')
 for name,keys in {'implementation-review-binding.public-r1.json': ['actualBrowserChecked', 'actualBuildChecked', 'actualHTMLChecked', 'actualPublicHTTPChecked', 'allowedNextStage', 'assessmentScope', 'assetManifest', 'closingGuidanceSourceCommit', 'closingReconciliation', 'coreHubLaunchStatus', 'customerCopy', 'customerCopySHA256', 'frozenAuthorManifest', 'fullLaunchStatus', 'guidanceSourceCommit', 'humanReview', 'independentReview', 'invalidatesOn', 'metadata', 'nationalOrder', 'officialCode', 'originalClauseReview', 'publicationEligible', 'purchaseIntentMetadataSHA256', 'region', 'renderChecklist', 'renderPlan', 'renderPlanSHA256', 'reviewedUTC', 'revision', 'schemaVersion', 'sourceCommit', 'sourceCommitBinding', 'visibleStrings'], 'independent-copy-review-r2.json': ['actualBrowserChecked', 'actualBuildChecked', 'actualHTMLChecked', 'actualPublicHTTPChecked', 'assessmentScope', 'closingGuidanceSourceCommit', 'closingMainReconciliation', 'closurePolicy', 'coreHubLaunchStatus', 'customerCopySHA256', 'directlyConfirmed', 'fullLaunchStatus', 'guidanceSourceCommit', 'humanReview', 'judgments', 'mandatoryRevisions', 'mustFixRemaining', 'nationalOrder', 'officialCode', 'operations', 'publicationEligible', 'purchaseIntentMetadataSHA256', 'region', 'renderPlanSHA256', 'reviewFiles', 'reviewedUTC', 'revision', 'schemaVersion', 'sourceCommit', 'toolReports', 'unverified', 'verdict'], 'implementation-code-review-binding.json': ['actualActionsBuildChecked', 'actualBrowserChecked', 'actualLocalBuildChecked', 'actualPublicHTTPChecked', 'actualStaticHTMLChecked', 'adapterFiles', 'adapterSourceManifest', 'adapterTreeSHA256', 'assessmentScope', 'closurePolicy', 'coreHubLaunchStatus', 'customerCopySHA256', 'embeddedPrivateSourceManifestSHA256', 'fullLaunchStatus', 'independentCodeReview', 'independentOutputMutationCases', 'independentRuntimeCases', 'indexNowReceiptChecked', 'laterGates', 'mustFixRemaining', 'nationalOrder', 'nativeCommandCount', 'nativeTestCases', 'officialCode', 'originalAssetPixelsChecked', 'originalClosedManuscriptBindingSHA256', 'originalManuscriptReviewSHA256', 'originalManuscriptVerdictPreserved', 'privateFiles', 'privateSourceManifest', 'privateTreeSHA256', 'providerOwnershipChecked', 'publicationEligible', 'publicationPathReconciliationSHA256', 'publicationSafeManuscriptBindingSHA256', 'region', 'renderPlanSHA256', 'repository', 'schema', 'schemaVersion', 'separateComparisonFixtureCases', 'sourceCommit', 'sourceCommitBinding', 'sourceFiles', 'sourceManifest', 'sourceRemoteSaved', 'sourceRoot', 'sourceTreeSHA256', 'trustedReleaseControlsChecked', 'verdict'], 'independent-code-review.json': ['actualActionsBuildChecked', 'actualBrowserChecked', 'actualLocalBuildChecked', 'actualPublicHTTPChecked', 'actualStaticHTMLChecked', 'adapterFiles', 'assessmentScope', 'closurePolicy', 'coreHubLaunchStatus', 'customerCopySHA256', 'directlyConfirmed', 'evidence', 'fullLaunchStatus', 'indexNowReceiptChecked', 'judgment', 'mandatoryRevisions', 'mustFixRemaining', 'nationalOrder', 'newManuscriptOrFactualReviewPerformed', 'notVerified', 'officialCode', 'operations', 'original149ClauseAnd13PolicyAssessmentBytesUnchanged', 'originalAssetPixelsChecked', 'originalClosedManuscriptBindingSHA256', 'originalManuscriptReviewSHA256', 'originalManuscriptVerdictPreserved', 'privateFiles', 'providerOwnershipChecked', 'publicationEligible', 'publicationPathReconciliationSHA256', 'publicationSafeManuscriptBindingSHA256', 'region', 'renderPlanSHA256', 'schema', 'schemaVersion', 'sourceCommit', 'sourceFiles', 'sourceManifestSHA256', 'sourceRemoteSaved', 'sourceRoot', 'sourceTreeSHA256', 'toolReportsAndLimits', 'trustedReleaseControlsChecked', 'verdict', 'verificationIncidents']}.items():require(type(doc(name)) is dict and set(doc(name))==set(keys),'original_review_schema_required:'+name)
 for obj in [cp,manuscript,code,report]:identity(obj)
 require(sha(docs['implementation-review-binding.public-r1.json'][0])==binding['customerReviewBindingSHA256'],'copy_review_binding_changed')
 require(sha(docs['implementation-code-review-binding.json'][0])==binding['codeReviewBindingSHA256'],'code_review_binding_changed')
 scope=dict(assessmentScope='MANUSCRIPT_AND_RENDER_PLAN_ONLY',revision='namgu-copy-r2-20261015',customerCopySHA256=binding['copySHA256'],renderPlanSHA256=binding['renderPlanSHA256'],purchaseIntentMetadataSHA256=binding['metadataSHA256'],guidanceSourceCommit='ae19e5c305fec9e4fda60f0e8d39d635e1b5730c',sourceCommit=None,actualHTMLChecked=False,actualBuildChecked=False,actualBrowserChecked=False,actualPublicHTTPChecked=False,publicationEligible=False,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED')
 for obj in [cp,manuscript]+[doc(n) for n in ['original-clause-assessment.json','purchase-intent-assessment.json','render-checklist.json']]:identity(obj);exact(obj,scope,'manuscript_scope_or_unverified_flags_changed')
 for obj in [cp,manuscript]:exact(obj,dict(closingGuidanceSourceCommit='04e0a0d21f19b7cd5a2529da802119177c946703'),'closing_guidance_mismatch')
 exact(manuscript,dict(verdict='MANUSCRIPT_AND_SPEC_READY_FOR_IMPLEMENTATION_NOT_PRODUCTION_PASS',mustFixRemaining=[]),'manuscript_verdict_required')
 revisions=manuscript['mandatoryRevisions'];require(type(revisions) is list and len(revisions)==1 and revisions[0].get('id')=='F1_HOME_PHOTO_LOCATION' and revisions[0].get('status')=='VERIFIED_FIXED_IN_R2','manuscript_required_revisions_unresolved')
 clauses=doc('original-clause-assessment.json');exact(clauses,dict(guidanceClauseCount=149,policyImageClauseCount=13),'original_clause_scope_required')
 require(type(clauses['guidance']) is list and len(clauses['guidance'])==149 and type(clauses['policyImages']) is list and len(clauses['policyImages'])==13,'original_clause_inventory_required')
 checklist=doc('render-checklist.json');require(type(checklist['checks']) is list and len(checklist['checks'])==12 and len({r.get('id') for r in checklist['checks']})==12 and all(r.get('actualOutputStatus')=='NOT_IMPLEMENTED_OR_NOT_CHECKED' and r.get('specificationStatus')=='CONSISTENT_IN_PLAN' for r in checklist['checks']),'original_checklist_cannot_claim_actual_output')
 exact(doc('purchase-intent-assessment.json'),dict(seoScore=None,geoScore=None,aeoScore=None,rankingOrIndexingVerified=False),'manuscript_cannot_claim_technical_quality_scores')
 source=manifest('source-manifest.json',SOURCE_MANIFEST_SHA,SOURCE_FILES,SOURCE_TREE_SHA)
 projection=doc('reviewed-input-projection.json');reconciliation=doc('publication-path-reconciliation-r1.json')
 exact(projection,dict(schema='namgu-reviewed-input-publication-projection/v1',scope='PATH_RESOLUTION_ONLY_NOT_NEW_CONTENT_OR_EXECUTION_APPROVAL',successorPackagedPath='inputs/reviewed-copy/reviews/implementation-review-binding.public-r1.json'),'publication_projection_scope_required')
 reference(projection['binding'],'namgu-customer-copy-independent-20261015/publication-r1/implementation-review-binding.public-r1.json')
 fields={'independentReview','frozenAuthorManifest','customerCopy','renderPlan','metadata','visibleStrings','assetManifest','originalClauseReview','renderChecklist','closingReconciliation','humanReview'}
 require(type(projection['entries']) is list and len(projection['entries'])==11 and {row.get('bindingField') for row in projection['entries']}==fields,'exact_publication_projection_required')
 seen=set()
 for row in projection['entries']:
  require(type(row) is dict and set(row)=={'bindingField','originalPath','packagedPath','bytes','sha256','originalBytesPreserved'} and row['originalBytesPreserved'] is True and type(row['bytes']) is int,'projection_row_schema')
  field=row['bindingField'];ref=cp[field];require(type(ref) is dict and set(ref)=={'path','bytes','sha256'} and same(ref,dict(path=row['originalPath'],bytes=row['bytes'],sha256=row['sha256'])),'copy_source_reference_bytes_mismatch')
  name=row['packagedPath'];require(name not in seen and name in source and source[name]['sha256']==row['sha256'] and source[name]['bytes']==row['bytes'],'projection_source_bytes_mismatch');seen.add(name)
 for key,digest in [('customerCopy',binding['copySHA256']),('renderPlan',binding['renderPlanSHA256']),('metadata',binding['metadataSHA256'])]:require(cp[key]['sha256']==digest,'copy_top_level_digest_mismatch')
 exact(reconciliation,dict(schema='namgu-publication-path-reconciliation/v1',scope='PATH_REDACTION_AND_PUBLIC_PACKAGE_RESOLUTION_ONLY',originalVerdict='MANUSCRIPT_AND_SPEC_READY_FOR_IMPLEMENTATION_NOT_PRODUCTION_PASS',newContentReviewPerformed=False,newApplicationTestsPerformed=False,newBuildBrowserOrPublicVerificationPerformed=False,originalIndependentChecksNotRerun=481),'path_reconciliation_cannot_claim_new_review')
 exact(reconciliation['originalClosedBinding'],dict(sha256='b32ab0a65b18e1eae7a655d916ce57a3842cc2bb75919ea54ef2cc621ca16a4f',bytes=3733),'closed_original_binding_identity_required')
 reference(reconciliation['successorBinding']);reference(reconciliation['projectionManifest'])
 exact(reconciliation['originalReview'],dict(originalPath='namgu-customer-copy-independent-20261015/independent-review-r2.json',bytes=10681,sha256='c446871b38a2e53b5433a8b1ed7089d97fd3ddbcba4c2a766174ee464d0f96b3'),'original_manuscript_identity_required')
 require(type(reconciliation['exactSemanticDelta']) is list and len(reconciliation['exactSemanticDelta'])==1 and reconciliation['exactSemanticDelta'][0]['jsonPointer']=='/frozenAuthorManifest/path' and reconciliation['exactSemanticDelta'][0]['newRelativePath']=='namgu-customer-copy-r2-20261015/review-input-manifest-r2.json','only_path_reconciliation_allowed')
 for name,packaged in [('implementation-review-binding.public-r1.json','implementation-review-binding.public-r1.json'),('independent-copy-review-r2.json','independent-review-r2.json'),('original-clause-assessment.json','original-clause-assessment.json'),('render-checklist.json','render-checklist.json'),('publication-path-reconciliation-r1.json','publication-path-reconciliation-r1.json'),('reviewed-input-projection.json','reviewed-input-projection.json'),('closing-main-reconciliation.json','closing-main-reconciliation.json'),('manuscript-review.ko.md','REVIEW.ko.md')]:
  row=source['inputs/reviewed-copy/reviews/'+packaged];require(row['sha256']==sha(docs[name][0]) and row['bytes']==len(docs[name][0]),'source_manuscript_review_bytes_mismatch')
 exact(code,{'schema': 'namgu-independent-implementation-review-binding/v1', 'schemaVersion': 1, 'region': 'namgu', 'officialCode': '12270', 'nationalOrder': 33, 'assessmentScope': 'FROZEN_LOCAL_CODE_REBUILD_STATIC_HTML_AND_EXACT_INPUT_BINDINGS_ONLY', 'verdict': 'LOCAL_SOURCE_AND_STATIC_OUTPUT_READY_FOR_SOURCE_SAVE_NOT_PUBLICATION_PASS', 'repository': 'joseungil-kr/fwith-site-factory', 'sourceRoot': 'site-factory/gwangju-namgu-flower', 'sourceCommit': None, 'sourceRemoteSaved': False, 'sourceTreeSHA256': 'ee961f55693294866d2e3ac607d517d74bf41072590c02f3fa11e47f95e19d9c', 'sourceFiles': 82, 'privateFiles': 67, 'adapterFiles': 15, 'privateTreeSHA256': 'c4565e2ca2085c5191e1f44adb635054977265cb4f650c83d4c1c8f566819b02', 'adapterTreeSHA256': '1f6aa8791837b0d239dee94e21212546538c444346c199aeee73addffeaf2089', 'embeddedPrivateSourceManifestSHA256': '1ebe39ec3f9e29487482395580afda6acd5409bc27ec7f3b6481ab337cc79e6a', 'customerCopySHA256': '052f89035bce44c5e4f403e7e42b9306dc0f49588e10d7aa89a8f088a8cadf08', 'renderPlanSHA256': '1f0ca658c66f29ddce187ee5f255b5ba64804e86c6d980370492af6b9936d21c', 'originalManuscriptReviewSHA256': 'c446871b38a2e53b5433a8b1ed7089d97fd3ddbcba4c2a766174ee464d0f96b3', 'originalClosedManuscriptBindingSHA256': 'b32ab0a65b18e1eae7a655d916ce57a3842cc2bb75919ea54ef2cc621ca16a4f', 'publicationSafeManuscriptBindingSHA256': '80e7e096e427fd8720f3ac45a9dde5b4576c4715e4725e5a16849e1224fea6fb', 'publicationPathReconciliationSHA256': '12a8fdf25adfd7d1357a1f919a9e55266d5c32506ea0904f9061c769e411c173', 'originalManuscriptVerdictPreserved': 'MANUSCRIPT_AND_SPEC_READY_FOR_IMPLEMENTATION_NOT_PRODUCTION_PASS', 'actualLocalBuildChecked': True, 'actualStaticHTMLChecked': True, 'originalAssetPixelsChecked': True, 'actualBrowserChecked': False, 'actualPublicHTTPChecked': False, 'actualActionsBuildChecked': False, 'providerOwnershipChecked': False, 'trustedReleaseControlsChecked': False, 'indexNowReceiptChecked': False, 'nativeCommandCount': 10, 'nativeTestCases': 266, 'independentOutputMutationCases': 55, 'independentRuntimeCases': 37, 'separateComparisonFixtureCases': 19, 'publicationEligible': False, 'coreHubLaunchStatus': 'NOT_ASSESSED', 'fullLaunchStatus': 'NOT_ASSESSED', 'sourceCommitBinding': 'Pending. Future actual commit must bind the exact82 source files and these original review bytes through a separate versioned successor.', 'closurePolicy': 'These report bytes are final. A changed source or input needs a new versioned implementation review; actual remote commit binding belongs in a separate successor without overwriting this report.'},'code_review_identity_or_scope_mismatch')
 exact(report,{'schema': 'namgu-independent-implementation-review/v1', 'schemaVersion': 1, 'region': 'namgu', 'officialCode': '12270', 'nationalOrder': 33, 'assessmentScope': 'FROZEN_LOCAL_CODE_REBUILD_STATIC_HTML_AND_EXACT_INPUT_BINDINGS_ONLY', 'verdict': 'LOCAL_SOURCE_AND_STATIC_OUTPUT_READY_FOR_SOURCE_SAVE_NOT_PUBLICATION_PASS', 'sourceRoot': 'site-factory/gwangju-namgu-flower', 'sourceCommit': None, 'sourceRemoteSaved': False, 'sourceTreeSHA256': 'ee961f55693294866d2e3ac607d517d74bf41072590c02f3fa11e47f95e19d9c', 'sourceManifestSHA256': 'a2c6781008b18bddbef5874fc574e280cd0cc9859bc56c52417bdb9628564e6c', 'sourceFiles': 82, 'privateFiles': 67, 'adapterFiles': 15, 'customerCopySHA256': '052f89035bce44c5e4f403e7e42b9306dc0f49588e10d7aa89a8f088a8cadf08', 'renderPlanSHA256': '1f0ca658c66f29ddce187ee5f255b5ba64804e86c6d980370492af6b9936d21c', 'originalManuscriptReviewSHA256': 'c446871b38a2e53b5433a8b1ed7089d97fd3ddbcba4c2a766174ee464d0f96b3', 'originalClosedManuscriptBindingSHA256': 'b32ab0a65b18e1eae7a655d916ce57a3842cc2bb75919ea54ef2cc621ca16a4f', 'publicationSafeManuscriptBindingSHA256': '80e7e096e427fd8720f3ac45a9dde5b4576c4715e4725e5a16849e1224fea6fb', 'publicationPathReconciliationSHA256': '12a8fdf25adfd7d1357a1f919a9e55266d5c32506ea0904f9061c769e411c173', 'originalManuscriptVerdictPreserved': 'MANUSCRIPT_AND_SPEC_READY_FOR_IMPLEMENTATION_NOT_PRODUCTION_PASS', 'newManuscriptOrFactualReviewPerformed': False, 'original149ClauseAnd13PolicyAssessmentBytesUnchanged': True, 'judgment': 'No mandatory implementation defect found within the frozen local source/static-output scope. Exact source82 is ready for an independently authorized source save; later source/control/Actions/browser/provider/public gates remain required.', 'actualLocalBuildChecked': True, 'actualStaticHTMLChecked': True, 'originalAssetPixelsChecked': True, 'actualBrowserChecked': False, 'actualPublicHTTPChecked': False, 'actualActionsBuildChecked': False, 'providerOwnershipChecked': False, 'trustedReleaseControlsChecked': False, 'indexNowReceiptChecked': False, 'publicationEligible': False, 'coreHubLaunchStatus': 'NOT_ASSESSED', 'fullLaunchStatus': 'NOT_ASSESSED', 'closurePolicy': 'These report bytes are final. A changed source or input needs a new versioned implementation review; actual remote commit binding belongs in a separate successor without overwriting this report.'},'code_report_identity_or_scope_mismatch')
 require(code['sourceFiles']==SOURCE_FILES and code['sourceTreeSHA256']==SOURCE_TREE_SHA and code['privateTreeSHA256']==PRIVATE_TREE_SHA and code['adapterTreeSHA256']==ADAPTER_TREE_SHA and code['privateFiles']==PRIVATE_FILES and code['adapterFiles']==ADAPTER_FILES,'code_source_tree_identity_mismatch')
 def code_reference(ref):
  require(type(ref) is dict and set(ref)=={'path','bytes','sha256'} and type(ref['path']) is str and not Path(ref['path']).is_absolute() and '..' not in Path(ref['path']).parts,'code_relative_reference_schema')
  reference({**ref,'path':'namgu-candidate-code-independent-20261015/'+ref['path']})
 require(code['sourceManifest']['path']=='evidence/source-manifest.json' and code['independentCodeReview']['path']=='independent-code-review.json','code_original_reference_paths_required')
 code_reference(code['sourceManifest']);code_reference(code['independentCodeReview']);code_reference(code['privateSourceManifest']);code_reference(code['adapterSourceManifest'])
 require(doc('private-manifest.json')['files']==list(manifest('private-source-manifest.json',PRIVATE_MANIFEST_SHA,PRIVATE_FILES,PRIVATE_TREE_SHA).values()) and doc('adapter-manifest.json')['files']==list(manifest('adapter-manifest.json',ADAPTER_MANIFEST_SHA,ADAPTER_FILES,ADAPTER_TREE_SHA).values()),'code_split_manifest_identity_mismatch')
 reviewed=doc('reviewed-source-manifest.json');require(reviewed['files']==list(source.values()) and reviewed['fileCount']==SOURCE_FILES and reviewed['treeSHA256']==SOURCE_TREE_SHA,'code_source_manifest_identity_mismatch')
 require(code['mustFixRemaining']==[] and report['mustFixRemaining']==[] and report['mandatoryRevisions']==[],'code_mandatory_revisions_unresolved')
 require(code['publicationSafeManuscriptBindingSHA256']==binding['customerReviewBindingSHA256'] and code['originalManuscriptReviewSHA256']==sha(docs['independent-copy-review-r2.json'][0]) and code['publicationPathReconciliationSHA256']==sha(docs['publication-path-reconciliation-r1.json'][0]),'code_manuscript_reference_identity_mismatch')
 require(type(report['evidence']) is list and len(report['evidence'])==11 and len({r['path'] for r in report['evidence']})==11,'code_evidence_inventory_mismatch')
 for ref in report['evidence']:code_reference(ref)
 public_manifest=doc('code-review-publication-manifest.json');exact(public_manifest,dict(schema='namgu-independent-code-review-publication-files/v1',fileCount=14,reviewClosed=True),'code_publication_manifest_required')
 require(type(public_manifest['files']) is list and len(public_manifest['files'])==14 and {r['path'] for r in public_manifest['files']}=={'README.ko.md','independent-code-review.json','implementation-code-review-binding.json'}|{r['path'] for r in report['evidence']},'code_publication_file_scope_required')
 for ref in public_manifest['files']:code_reference(ref)
 # The original assessments are immutable. A rehashed transport envelope must not
 # alter a nested finding, evidence reference, test denominator or unverified flag.
 # These canonical digests supplement, rather than replace, schema and source checks.
 for name,digest in {'implementation-review-binding.public-r1.json': '9a25a8dbc154eb8ed73014142f640e378a201f8c9b91356d655a52eaa0365cea', 'independent-copy-review-r2.json': '8e5368869806fecedeb08fdbe89b11336f14eef022b10b136a1b83302f30dec7', 'original-clause-assessment.json': 'c0e15844d82134a8a9ea10c0e5f77f3d722129a462e1710154fa1e03f31a723a', 'purchase-intent-assessment.json': 'e92707f31200bc54e195f8520851755b7ec1b1b2d8d1f55ffb8136d7c74abb68', 'render-checklist.json': 'c130263d6233293e35fb9f3e8b6d632f88222f8b65a6a3456f76db1d118679a6', 'closing-main-reconciliation.json': '99f0bc37ffbcc71db0d3474ee33f5eb8dcca342231f52ebeb97f6dd096422a5e', 'publication-path-reconciliation-r1.json': '1f15baeadab2ced4de038633b6519f6ec02b1a420d7b13bbe9388dc3906c2b75', 'reviewed-input-projection.json': '899fbbe41652e6772bf3270dd6e7d5bd3eea95ff20fc45aec6472d88df7b2fbf', 'implementation-code-review-binding.json': '3cfd59616994e406ee2e5dea6d9a3bca4121517a9d31850e4465afea9a1533d8', 'independent-code-review.json': '3f4932f22d1168d1996e7e5d60e6aaacc68ba5512f51c695c247f73250e87fb1', 'code-review-publication-manifest.json': 'a944835af45392e87a7e0c77690854dab41547e3a7dd49c344307bc2f8b1ddf4', 'reviewed-source-manifest.json': '6040410a6246b8b370d09cb9ebb2076d3bee463eb3b49341348ae3ef230fc652', 'private-manifest.json': 'bd20943c709a166581d3917d3057ca39ad5d59d623e20603fae9a211d90931c5', 'adapter-manifest.json': '268996b3964e177916b221c626ebb990a379079b00c141ac783c71d0fbbb1b35', 'binding-and-reuse-checks.json': '64afa59bd69657a8c0987158cfe299860bfed9921ada16b39e23b86fe1be7f80', 'independent-output-inspection.json': '0b050be3d48bdcfbf88247f5e4f598be228470903efa3c63178793bbb87e981f', 'test-counts.json': '8b17ee7c44a7ce0968056da719636f2abeacb407bbdec28086e9c935c7694a6f', 'independent-semantic-negatives.json': '2e8b0b309f045877254c797c3da6ef751673b0e1e9c382fc0a6439646e2a9c74', 'independent-runtime-semantics.json': '9f07e2c87afbbac344c6b9275735d886b619b70d938143976af65a61fd673c69', 'verified-output-files.json': '27648926617c94099344beeee5eefff0870bb1b086c0dc886add54dccee9a1a6', 'capture-fixture-checks.json': '33526d5d7cc8739ecea1fbe5d2738715bfa98995419bff6251e1e25b501edba3', 'source-final-reverification.json': 'c3c52834778089922ab487c5d4e0c616108461b9283c0b82a3c36c29396b521e'}.items():
  require(sha(json.dumps(doc(name),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())==digest,'original_review_meaning_changed:'+name)
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
 require(all(same(b[k],v) for k,v in expected.items()),'exact_namgu_binding_required')
 authorization(c,b)
 return c,b,sha(br)

def trusted_control(env):
 require(env.get('GITHUB_REPOSITORY')==REPOSITORY and env.get('GITHUB_REF')=='refs/heads/main','owner_main_required')
 require(env.get('GITHUB_ACTOR')==OWNER and env.get('GITHUB_TRIGGERING_ACTOR')==OWNER and env.get('GITHUB_RUN_ATTEMPT')=='1','owner_first_attempt_required')
 require(env.get('GITHUB_EVENT_NAME')=='issues' and re.fullmatch('[1-9][0-9]*',env.get('GITHUB_RUN_ID','')),'actual_issue_run_required')
 root=DIRECTORY.parents[1];revision=env.get('GITHUB_SHA','');require(re.fullmatch('[0-9a-f]{40}',revision),'control_revision_required')
 require(git(root,'rev-parse','HEAD').decode().strip()==revision,'actual_control_revision_mismatch')
 scopes=['scripts/direct-gwangju-namgu','docs/direct-gwangju-namgu','.github/workflows/gwangju-namgu-production-build-only.yml','.github/workflows/gwangju-namgu-production-publish.yml',*['site-factory/engine/'+n for n in HELPER_SHA256]]
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
 require(read(adapter/'scripts/namgu_release_output.py')==read(DIRECTORY/'production_output.py'),'source_control_output_validator_mismatch')
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
