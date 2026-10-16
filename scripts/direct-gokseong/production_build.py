"""Pinned Gokseong build and artifact gates. Never contact a provider or publish."""
import argparse,hashlib,json,os,re,shutil,subprocess
from html.parser import HTMLParser
from pathlib import Path
import production_output as output
DIRECTORY=Path(__file__).resolve().parent
# Keep the exact source validator bytes but bind its baseline to this isolated control.
output.EQUIVALENCE_PATH=DIRECTORY/'preview-equivalence.json'
REPOSITORY='joseungil-kr/fwith-site-factory';OWNER='joseungil-kr'
ROOT='site-factory/gokseong-flower';BUILD_ROOT=ROOT+'/candidate';ADAPTER_ROOT=ROOT+'/release-adapter';BRANCH='source/gokseong-dedicated-proof-production-20261016'
TITLE='[GOKSEONG-PRODUCTION-BUILD] 20261016'
HOSTNAME='gokseong.fwith.kr';ORIGIN='https://'+HOSTNAME;WORKER='gokseong-flower-guide'
INPUT_SHA='d9e4e75f99370c51201bf411f613b58ef1af6aa3be182a10a043741c0fcfb3dd'
PRIVATE_TREE_SHA='d37ad2fa7bdcedc33dd0a223fc8434e83b404167a07a8e056046c0c58caa3dbb'
ADAPTER_TREE_SHA='a6d1cecec04c3b16ba194329481baca6a4ac8af829f1501a7ea30b4624f106d1'
SOURCE_TREE_SHA='c335a528bfbcdc735cd0eb588acb18c1721ccb7db28839ac0c3217a215affd18'
SOURCE_FILES=91;PRIVATE_FILES=73;ADAPTER_FILES=18
PRIVATE_MANIFEST_SHA='7898d5136d3e4d96efae7f5bc2d65b09455e913ab8d21f89556c37f330d38341'
ADAPTER_MANIFEST_SHA='ab8991996161e558d9d06f1261ad3d472875e09ced44fda9606e411b92e3f1e4'
SOURCE_MANIFEST_SHA='122a17d058eeb15161fab64f2b6ac475373eede0b32366e082cac06a41e15f2e'
PREVIEW_EQUIVALENCE_SHA='c337efd945a3090f5f48ea69c4f79c5866065bfaf7e76fd60c010b154e45338e'
BOUNDED_CONTRACT_SHA='de4c9c56c1532a923d1b26b0f7cb035542b2197a3ac3b142e54fc02ef18fdb2f'
CONTENT_REVIEW_BINDING_SHA='9baf59912c83d4b6359a97d84f24aeb2aa9c42fe05a1b1a7f54f0f39ad354117'
HELPER_SHA256={'bucheon_domain_attach.py': 'a8662dd6ff232c53b6c55f193553f134c7055ec80eca421b65bab9bedd220da3', 'goyang_domain.py': '8a30e0ea75758344a5ff92903ec0a9dbd1e4f2bff230cdf603ea871ca1bf9c68', 'indexnow_finalize.py': '55f5274d3fcc713e82fd8ce18e280447e68e9e460bc1ff3f9bf5cc683834935f'}
HISTORICAL_REVIEW_PINS={'INPUT-BINDING.json': '06282b19cb8d585e924ab768e0a6eb28caad09ae0f7ddbf1712c96fe9e5717c5', 'MANIFEST.json': 'fb213b1bbdde350fa02b145eec351a95d33015ba4428526d09cd41293c6002ac', 'review.json': '145d7add2e54d25990ee723279b4db22eee8bd014e0a9ea4e7eee49029666201'}
SUCCESSOR_REVIEW_PINS={'review.json': 'f0391014194f2df9c74964f0dc662912550a4d7028aaabf9d3ea77135884c2e1', 'REPORT.ko.md': 'e2337fbc3b54aa3bd3d9afe9b1aad33b474f2d2eceac31be2ec76c1b687ce3ab', 'acceptance-binding.json': 'eda691e8471c2a9c782d79f1309879b4b37c8ed9e7042213189a85841d5fe0d7', 'MANIFEST.json': '001fd87bc25bda228f07e688fd5345e3fd2ac1a82455c44506216f703a7755ba'}
SUCCESSOR_ACCEPTANCE={'actualActionsRunId': None, 'actualBrowserVerified': False, 'actualProductionRunnerExecuted': False, 'actualProviderOwnershipVerified': False, 'adapterFiles': 18, 'adapterTreeSHA256': 'a6d1cecec04c3b16ba194329481baca6a4ac8af829f1501a7ea30b4624f106d1', 'authorEvidenceManifestSHA256': '3727f3f30c871e3a9ed143c02465156bf8502831712df955de43835ae0be394c', 'boundedContractSHA256': 'de4c9c56c1532a923d1b26b0f7cb035542b2197a3ac3b142e54fc02ef18fdb2f', 'customerCopySHA256': '3829721f442682c7b07f02b043b5ba80a0e1e0d5264babb7c96a7b2eadd0332e', 'equivalenceSHA256': 'c337efd945a3090f5f48ea69c4f79c5866065bfaf7e76fd60c010b154e45338e', 'evidenceBindings': [{'bytes': 2161, 'path': 'evidence/adapter-node-tests-final.log', 'sha256': '09ca66351e65bdc12d2bd10d6c735391d1181f63a93bbd34f377f244318f7702'}, {'bytes': 3203, 'path': 'evidence/adapter-python-tests-final.log', 'sha256': 'b9a318afd9c54219cd667dc19e6834d19095483135b28cf4727ea84c17bdadf3'}, {'bytes': 82, 'path': 'evidence/additional-reference-checks.log', 'sha256': '974590887a4f9693fbe94fd95acc2f68cc975ee8dd82345a6ba8685269e2f6c1'}, {'bytes': 13086, 'path': 'evidence/additional-reference-mutations.json', 'sha256': 'c191bcf51b362087af704c347969e3a862ba3fd50a8e2580604e3d9e0644efc1'}, {'bytes': 51469, 'path': 'evidence/build-and-private-qa-final.log', 'sha256': '4558655b066a456a12e467ffb447b6eb639fec044b4615c04be08a679860f0b8'}, {'bytes': 1248, 'path': 'evidence/build-order-tests-final.log', 'sha256': 'e1caa3a564ce7f9810beb56bb23c87ce358eca44a7412a8f0c834cc3be298c27'}, {'bytes': 228, 'path': 'evidence/dependency-cache.json', 'sha256': '4e691603dc3edb6e671df0e6ceb1c322c11ac867ab09084998148bb760f96380'}, {'bytes': 620, 'path': 'evidence/environment-boundary.json', 'sha256': '76bde028691d80c59a7a9811af6ee871ea53dc5f1efcf2ae54ed3544422b5c1a'}, {'bytes': 881, 'path': 'evidence/exact-occurrence-tests-final.log', 'sha256': 'dc9188a0da8e84d53392e94fd669289067c0017620c8004b0877bcf5431580f2'}, {'bytes': 2794, 'path': 'evidence/final-command-results.json', 'sha256': '7b43ab67be5ca0822ca81a240c84e8775e3107e302444691a6f322d9626f0265'}, {'bytes': 2531, 'path': 'evidence/final-inspection-result.json', 'sha256': '0d4376b92fc687aed55e205bc233adda8473a38f1ccf7859db73ee7603b3cd8a'}, {'bytes': 162, 'path': 'evidence/historical-preservation-readback.json', 'sha256': '64947e51da75802aba1fd9ee110729eef4af43f311e5707abf4c75515ef690ed'}, {'bytes': 371, 'path': 'evidence/independent-aggregate.log', 'sha256': '1422b12dbc40c588f5cc91e48499f4674be6c022dfb4629f18656fd6b9b49522'}, {'bytes': 963, 'path': 'evidence/independent-delta.json', 'sha256': 'e677f2ac83b0cbe89ba7438b68caceb9506027ccacb7c9a7a5599bf8619f8288'}, {'bytes': 28441, 'path': 'evidence/independent-dependency-versions.json', 'sha256': '779d05ae00c1374ab70f364553b13d9e569012db8a949ff81b6bd2e9cb96e2b2'}, {'bytes': 5595, 'path': 'evidence/independent-private-offline-parity.json', 'sha256': '4769748573614de1d7d96898e16bf8058ffd9229379d4ce5a4313e9aa8a3959e'}, {'bytes': 1495, 'path': 'evidence/independent-production-output-mutations.json', 'sha256': 'a1e53a5fe5e7a709b5a9a02fb257559110601aa2f0f544b9c4e73d043db34766'}, {'bytes': 7310, 'path': 'evidence/independent-production-results.json', 'sha256': '973ecc6bc64b03b15ea029d167d291cbe22cc66defd6718885520322ecee44f3'}, {'bytes': 16454, 'path': 'evidence/independent-source-manifest.json', 'sha256': 'ace7bfc1b88fef0f20aed542cca76038fc922301ae07e943887613ef8e3253aa'}, {'bytes': 36936, 'path': 'evidence/independent-source.diff', 'sha256': '8e0d786a7dafe7c7cc8d5945ff94b47a671866ed5aba6cfb7ee325c75afca8f2'}, {'bytes': 2745, 'path': 'evidence/independent-test-counts.json', 'sha256': '48240663ca7c4ff337d462f1a1712e9de24e65a26591310033d26ea34d6d01e3'}, {'bytes': 7912, 'path': 'evidence/input-evidence-readback.json', 'sha256': '9432dab8fcd29ad87df00e557f087ebb610041243b7dbeed849fa941a3c31d61'}, {'bytes': 1566, 'path': 'evidence/node-python-parity-final.log', 'sha256': '6e9962e2a01990f650f88e0935fb001eb7aea091e44af7d7f827a2db781dc6b6'}, {'bytes': 10375, 'path': 'evidence/output-python-tests-final.log', 'sha256': '3d1818a39dd2a36b3ae7e446d52e76f2ce1e0cd6e9bc334e73352193a26cedad'}, {'bytes': 45326, 'path': 'evidence/private-exact-occurrences.json', 'sha256': 'f83ca9bd2501d23b9bb1d5abbfd1daf272a41d0c0f71e53bde730fc208a793aa'}, {'bytes': 6240, 'path': 'evidence/private-node-tests-final.log', 'sha256': '1c10d4e64f35ed3cbf90dfa70f3519babd2db65a8a322bd8a44577e4855f0b97'}, {'bytes': 6622, 'path': 'evidence/private-python-tests-final.log', 'sha256': 'f207b59474407d3be00654a87de17a3ef9adcdd3c34e83166a5b5febf91bc45d'}, {'bytes': 45860, 'path': 'evidence/production-like-exact-occurrences.json', 'sha256': '35dac926b30c878aeb40c9ea7d151f37715d09b464d2558383cc46212588b138'}, {'bytes': 762, 'path': 'evidence/reviewer-retry-record.json', 'sha256': '0ef6e046939c0bb0f56369cdbe3f6545be6cdc96de2826dde7041f586cc3d0b4'}, {'bytes': 12636, 'path': 'evidence/runner-output-tests-final.log', 'sha256': 'ba158efa3dddef2a8837108ccd3fca4a6684d0376bd4c2814d71ca22009b5764'}, {'bytes': 326, 'path': 'evidence/typecheck-final.log', 'sha256': 'c0ec094b5e57d4020f6220e9f21c50e4a668391b8b5708a87bd818e5b22e9148'}, {'bytes': 187, 'path': 'evidence/verify-inputs-final.log', 'sha256': '835cddf05c64f2eb7905edf311cc88ba63bf69c1b4f9053df5605f454a5cb983'}, {'bytes': 1475, 'path': 'evidence/production-attempt-1/production-binding.json', 'sha256': '8f952d23925256a29b142efc913daf6a636ec4d60cb8aabbcb27c1ef19648602'}, {'bytes': 80312, 'path': 'evidence/production-attempt-1/full-build.log', 'sha256': 'ea7452cacfbbabbc585202da2d994b62a06d3fd64f8544f695535e9b6753eb43'}, {'bytes': 2562, 'path': 'evidence/production-attempt-1/inspection-result.json', 'sha256': 'e5acc6fc50e9b4d4c4d0ad3540805970a6f70c9628c5d6c47e1fb72216fdf95c'}, {'bytes': 45860, 'path': 'evidence/production-attempt-1/exact-occurrences.json', 'sha256': '35dac926b30c878aeb40c9ea7d151f37715d09b464d2558383cc46212588b138'}, {'bytes': 1475, 'path': 'evidence/production-attempt-2/production-binding.json', 'sha256': '8f952d23925256a29b142efc913daf6a636ec4d60cb8aabbcb27c1ef19648602'}, {'bytes': 80307, 'path': 'evidence/production-attempt-2/full-build.log', 'sha256': '6b1cb4a2871222eb0229c1b15cec14cc08e64272fc02f7661aa225ba97383747'}, {'bytes': 2562, 'path': 'evidence/production-attempt-2/inspection-result.json', 'sha256': 'e5acc6fc50e9b4d4c4d0ad3540805970a6f70c9628c5d6c47e1fb72216fdf95c'}, {'bytes': 45860, 'path': 'evidence/production-attempt-2/exact-occurrences.json', 'sha256': '35dac926b30c878aeb40c9ea7d151f37715d09b464d2558383cc46212588b138'}], 'expandedTestMethodEntries': 539, 'frozenPrivateTreeSha256': 'd37ad2fa7bdcedc33dd0a223fc8434e83b404167a07a8e056046c0c58caa3dbb', 'offlineOutputTreeSHA256': 'd0b0f16df8b3f4c0f1db131a77d034beb044d4e464236142719a7aee94d2ff00', 'originalNativeBindingSHA256': '06282b19cb8d585e924ab768e0a6eb28caad09ae0f7ddbf1712c96fe9e5717c5', 'originalNativeReviewSHA256': '145d7add2e54d25990ee723279b4db22eee8bd014e0a9ea4e7eee49029666201', 'originalSourceRevision': '6eb8484612879e380bac31b689ec6a16058df06b', 'privateFiles': 73, 'privateOutputTreeSHA256': '4748aa01d2f56740e6063fea910402a91905ff171546c4850f7528eeb4e12442', 'privateSourceManifestSHA256': '7898d5136d3e4d96efae7f5bc2d65b09455e913ab8d21f89556c37f330d38341', 'privateTreeSHA256': 'd37ad2fa7bdcedc33dd0a223fc8434e83b404167a07a8e056046c0c58caa3dbb', 'productionOutputFiles': 16, 'proof': {'origin': 'https://gokseong.fwith.kr', 'path': '/049d6c691d2c4cb824d23f82e9883ce4.txt', 'sha256': '6b2ca7c4565ff09d97fa259ca5df416fdcb8408e92b0f0edf3dcf7af3a1fdcc4'}, 'publicHTTPVerified': False, 'publicationEligible': False, 'referenceManifestSHA256': 'd1e40cbf681a1ca9797bd3e80c872dbe90ee5865da60cc1a8a6bd820c9d87df3', 'remainingProductionGates': ['Exact new remote source commit and all91 Git blob/tree readback', 'Independent release-control/workflow review bound to actual source and authorization commits', 'Actual Actions build artifact and source/control/run identities', 'Actual desktop/mobile browser behavior, images/buttons/focus and independent pixels', 'Provider ownership and target collision preflight', 'Published full-byte HTTP GETs and real404 status/body', 'Published dedicated proof GET and accepted IndexNow receipt for only the home URL'], 'renderPlanSHA256': '0ef1ba508743a560d04a8217fbd9a35d80569f6808c3603367da2f7db2293b67', 'reportSHA256': 'e2337fbc3b54aa3bd3d9afe9b1aad33b474f2d2eceac31be2ec76c1b687ce3ab', 'requiredInputsSHA256': 'd9e4e75f99370c51201bf411f613b58ef1af6aa3be182a10a043741c0fcfb3dd', 'reviewSHA256': 'f0391014194f2df9c74964f0dc662912550a4d7028aaabf9d3ea77135884c2e1', 'reviewerScriptBindings': [{'bytes': 10657, 'path': 'replay.py', 'sha256': '47127fa8908f469f18ff3a92ecfe185143cd386e8fd05c27fec6acfee256e060'}, {'bytes': 2860, 'path': 'additional-reference-checks.mjs', 'sha256': '305a80536aa746cbf5d4dad8873d5e036d980db6a536b21ca87ee34f5ad4c3f5'}, {'bytes': 14351, 'path': 'finalize_review.py', 'sha256': 'c190d7b32a9a98d6ed19c78053888cbb4720defa27ffba6ac0d6d8ff53ab6622'}, {'bytes': 1786, 'path': 'recover_test_counts.py', 'sha256': '0f58ae0e77a6e2a91a9f532b65ce8f9b0c0bf5e54f23f2700e37befe1ed5f1cd'}], 'schema': 'gokseong-source91-independent-acceptance-binding/v1', 'scope': 'SOURCE_ONLY_STATIC_ACCEPTANCE', 'sourceFiles': 91, 'sourceFreezeSHA256': '5a8c274433097a6a5341191ab5c3e7895733c94ff2fa4464f308383b48b401eb', 'sourceOnlyStorageStaticReviewPass': True, 'sourceRevision': None, 'sourceTreeSHA256': 'c335a528bfbcdc735cd0eb588acb18c1721ccb7db28839ac0c3217a215affd18', 'sourceZIPBytes': 1784534, 'sourceZIP_SHA256': 'bf07f2573cad02519027e2930c9849d40150489e63edfc0444ba9fea10173998', 'syntheticProductionOutputTreeSHA256': 'a7aab87c44fe337625d490b178d277d39fff409deb6f2ba0fef410e665100dd2', 'verdict': 'SOURCE91_LOCAL_STATIC_ACCEPTANCE_PRODUCTION_GATES_PENDING'}
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
 return dict(schemaVersion=1,state='approved',repository=REPOSITORY,sourceRoot=ROOT,siteKey='gokseong-flower-direct',hostname=HOSTNAME,origin=ORIGIN,worker=WORKER,frozenInputSha256=INPUT_SHA,frozenPrivateTreeSha256=PRIVATE_TREE_SHA,sourceRevision=c['sourceRevision'],proof=output.PROOF,sitemapRoutes=output.ROUTES,htmlFiles=2,notFoundRobots='noindex,follow',notFoundStatus=404,publicHttpVerified=False,indexNowSubmitted=False,boundedContractSha256=BOUNDED_CONTRACT_SHA,coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED',approvals=dict(publication=True,hostBinding=True,indexNowProof=True))
def authorization_template(c):
 return dict(schemaVersion=1,recordType='user-authorization-not-readiness-proof',repository=REPOSITORY,sourceRoot=ROOT,siteKey='gokseong-flower-direct',hostname=HOSTNAME,origin=ORIGIN,worker=WORKER,sourceRevision=c['sourceRevision'],sourceTree=c['sourceTree'],approvedOperations=['source-and-control-storage','production-build-and-QA','publication-after-own-gates','existing-provider-first-host-binding-with-no-overrides','approved-dedicated-proof-and-one-URL-IndexNow-after-public-HTTP','public-build-publish-and-receipt-issues'],publicIssuesApproved=True,crossRegionPublicationOrderRequired=False,ownQualityAndSafetyGatesRequired=True,noNewCredentialsOrPermissionChanges=True,noDomainOwnershipTransferOrOverride=True)
def public_issue_approval_evidence():
 return dict(approvedAtUTC='2026-10-15T18:24:17Z',approved=True,scope='remaining-171-planned-regions-public-github-qa-publish-indexnow-receipts',publicData=['site-url','commit','qa-and-receipt-results'],secretsExcluded=True)
def dedicated_proof_approval_evidence():
 return dict(approvedAtUTC='2026-10-16T14:31:30.443765+00:00',approved=True,scope='gokseong.fwith.kr-dedicated-public-IndexNow-verification-key-creation-application-and-one-sitemap-URL-submission-after-public-verification',loginCredentialsUnchanged=True,dnsOwnershipUnchanged=True)
def authorization(c,b):
 d=json.loads(read(DIRECTORY/'authorization-binding.json'))
 require(isinstance(d,dict) and set(d)=={'schemaVersion','path','sha256','revision','publicIssuesApproved'} and type(d['schemaVersion']) is int and d['schemaVersion']==1,'authorization_descriptor_schema')
 require(d['publicIssuesApproved'] is True,'public_issue_approval_required')
 require(d['path']=='docs/direct-gokseong/production-authorization-20261016.json' and re.fullmatch('[0-9a-f]{64}',d['sha256'] or '') and re.fullmatch('[0-9a-f]{40}',d['revision'] or ''),'pinned_authorization_required')
 raw=read(DIRECTORY.parents[1]/d['path']);require(sha(raw)==d['sha256'],'authorization_bytes_changed');a=json.loads(raw)
 expected=authorization_template(c);require(set(a)==set(expected)|{'authorizationEvidence'},'authorization_schema')
 require(all(same(a[k],v) for k,v in expected.items()),'exact_gokseong_authorization_required')
 require(same(a['authorizationEvidence'],[public_issue_approval_evidence(),dedicated_proof_approval_evidence()]),'exact_public_safe_approval_evidence_required')
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
 raw=read(DIRECTORY/'content-review-binding.json');require(sha(raw)==CONTENT_REVIEW_BINDING_SHA,'content_review_binding_changed');binding=json.loads(raw)
 expected=dict(schemaVersion=1,region='gokseong',scope='native-source89-review-and-independent-proof-successor-review-not-production-pass',sourceTreeSHA256=SOURCE_TREE_SHA,sourceFiles=SOURCE_FILES,frozenPrivateTreeSha256=PRIVATE_TREE_SHA,inputSha256=INPUT_SHA,productionGatePassed=False,staticQualityIsProductionPass=False)
 require(set(binding)==set(expected)|{'files','historicalReviewPins','successorReviewPins'} and all(same(binding[k],v) for k,v in expected.items()),'content_review_source_identity_mismatch')
 rows=binding['files'];require(type(rows) is list and rows and len({r['path'] for r in rows})==len(rows),'content_review_inventory_invalid');docs={}
 for row in rows:
  name=row.get('path','');require(type(name) is str and name.startswith('docs/direct-gokseong/') and not Path(name).is_absolute() and not any(x in {'.','..'} for x in name.split('/')) and '\\' not in name,'content_review_path_invalid')
  data=regular_under(DIRECTORY.parents[1],name);require(sha(data)==row['sha256'] and len(data)==row['bytes'],'content_review_bytes_changed:'+name);docs[name]=data
 prefix='docs/direct-gokseong/reference-source89-review/'
 historical=HISTORICAL_REVIEW_PINS
 require(same(binding['historicalReviewPins'],historical),'original_review_pin_changed')
 for name,digest in historical.items():require(sha(docs[prefix+name])==digest,'original_review_pin_changed')
 report=json.loads(docs[prefix+'review.json']);native=json.loads(docs[prefix+'INPUT-BINDING.json']);manifest=json.loads(docs[prefix+'MANIFEST.json'])
 require(report['source']['files']==89 and report['source']['privateFiles']==PRIVATE_FILES and report['source']['privateTreeSHA256']==PRIVATE_TREE_SHA and report['source']['sourceTreeSHA256']=='de77566ca5f7bef98881afdaf446c029e1c367d593bac10490bc0b9090a89be0','historical_source_scope_changed')
 require(report['publicationEligible'] is False and report['actualBrowserChecked'] is False and report['actualPublicHTTPChecked'] is False and report['proofBoundary']['proof'] is None and native['sourceRevision'] is None,'historical_review_upgraded')
 require(report['mustFixRemainingInReviewedScope']==[] and report['verdict']=='LOCAL_REFERENCE_SOURCE_SUCCESSOR_STATIC_PASS_BROWSER_AND_PRODUCTION_GATES_PENDING','historical_review_verdict_changed')
 require(report['historicalManuscript']['originalDenominators']==dict(currentFacts=17,facilities=5,guidance=171,policy=16) and report['historicalManuscript']['independentNumericScores'] is None and report['historicalManuscript']['originalAuthorScores'] is None and report['historicalManuscript']['originalIndependentScores'] is None,'historical_denominators_or_scores_changed')
 require(manifest['fileCountExcludingManifest']==40 and len(manifest['files'])==40,'historical_manifest_count_changed')
 require(set(n for n in docs if n.startswith(prefix))=={prefix+n for n in historical},'historical_summary_projection_inventory_changed')
 # Full original 40-row evidence remains archived and was independently examined; this
 # public control retains three native documents byte-exact, not a claim to publish all logs.
 # The new review must separately bind the exact source that is built. Its raw report is immutable.
 require(same(binding['successorReviewPins'],SUCCESSOR_REVIEW_PINS),'successor_review_pin_changed')
 for name,digest in SUCCESSOR_REVIEW_PINS.items():require(sha(docs['docs/direct-gokseong/proof-successor-review/'+name])==digest,'successor_review_pin_changed')
 successor=json.loads(docs['docs/direct-gokseong/proof-successor-review/acceptance-binding.json'])
 require(same(successor,SUCCESSOR_ACCEPTANCE),'successor_review_acceptance_changed')
 require(successor['sourceTreeSHA256']==SOURCE_TREE_SHA and successor['sourceFiles']==SOURCE_FILES and successor['privateTreeSHA256']==PRIVATE_TREE_SHA and successor['privateFiles']==PRIVATE_FILES and successor['publicationEligible'] is False and successor['actualBrowserVerified'] is False and successor['publicHTTPVerified'] is False,'successor_review_scope_invalid')
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
 require(all(same(b[k],v) for k,v in expected.items()),'exact_gokseong_binding_required')
 authorization(c,b)
 return c,b,sha(br)

def trusted_control(env):
 require(env.get('GITHUB_REPOSITORY')==REPOSITORY and env.get('GITHUB_REF')=='refs/heads/main','owner_main_required')
 require(env.get('GITHUB_ACTOR')==OWNER and env.get('GITHUB_TRIGGERING_ACTOR')==OWNER and env.get('GITHUB_RUN_ATTEMPT')=='1','owner_first_attempt_required')
 require(env.get('GITHUB_EVENT_NAME')=='issues' and re.fullmatch('[1-9][0-9]*',env.get('GITHUB_RUN_ID','')),'actual_issue_run_required')
 root=DIRECTORY.parents[1];revision=env.get('GITHUB_SHA','');require(re.fullmatch('[0-9a-f]{40}',revision),'control_revision_required')
 require(git(root,'rev-parse','HEAD').decode().strip()==revision,'actual_control_revision_mismatch')
 scopes=['scripts/direct-gokseong','docs/direct-gokseong','.github/workflows/gokseong-production-build-only.yml','.github/workflows/gokseong-production-publish.yml',*['site-factory/engine/'+n for n in HELPER_SHA256]]
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
 require(read(adapter/'scripts/gokseong_release_output.py')==read(DIRECTORY/'production_output.py'),'source_control_output_validator_mismatch')
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

