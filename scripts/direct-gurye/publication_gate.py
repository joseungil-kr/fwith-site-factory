"""Trusted-main adapter for the accepted Gurye QA binding. No source code executes here.

Reuses the publisher's control-tree, authorization-commit and immutable-input gates;
the source model is the already-reviewed source60/QA5 chain rather than Damyang data.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,subprocess
DIRECTORY=Path(__file__).resolve().parent
REPOSITORY='joseungil-kr/fwith-site-factory';OWNER='joseungil-kr'
SOURCE='de6147d063dc563a6ef0f82e6ebf0e6e4ca3d10f'
TREE='eda3ec8db749acf21ed8e7e23d718e2bc46c02fe'
BRANCH='source/gurye-production-metadata-preparation-20261016'
PRODUCTION_CONTRACT_SHA='0f6c1c070405afbf7cc5d6a51191caf8664c868f9c87f07ac1167efac40e33a2'
BOUNDED_CONTRACT_SHA='a1effa3234cbf8fd900ec086cffb4de09fac7cf85ce0537826f9559769f779b7'
QA_BINDING_SHA='819387431b999d24321be95cb052101188f37bbf1e1d2e67058730c137676c9c'
QA_CODE_SHA='db12b43142cbd98a910dc621c27eb48b96426fb81880ae66d9e2096ea0e6618d'
HELPER_SHA256={'bucheon_domain_attach.py':'a8662dd6ff232c53b6c55f193553f134c7055ec80eca421b65bab9bedd220da3','goyang_domain.py':'8a30e0ea75758344a5ff92903ec0a9dbd1e4f2bff230cdf603ea871ca1bf9c68','indexnow_finalize.py':'55f5274d3fcc713e82fd8ce18e280447e68e9e460bc1ff3f9bf5cc683834935f'}
def require(ok,code):
 if not ok:raise ValueError(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def same(a,b):return json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)
def read(path):
 p=Path(path);require(p.is_file()and not p.is_symlink(),'regular_file_required')
 for parent in p.absolute().parents:require(not parent.is_symlink(),'parent_symlink_forbidden')
 return p.read_bytes()
def git(checkout,*args):return subprocess.check_output(['git','-C',str(checkout),*args],stderr=subprocess.STDOUT)
def regular_under(root,name):
 require(not Path(name).is_absolute()and '..'not in Path(name).parts,'unsafe_control_path');return read(Path(root)/name)
def inputs():
 qpath=DIRECTORY/'production-qa/production_qa.py';require(sha(read(qpath))==QA_CODE_SHA,'reviewed_main_qa_code_changed')
 spec=importlib.util.spec_from_file_location('gurye_trusted_main_qa',qpath);q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
 b=q.binding();require(q.BINDING_SHA==QA_BINDING_SHA and b['assemblyRevision']==SOURCE and b['sourceBranch']==BRANCH,'reviewed_main_qa_binding_changed')
 raw=read(DIRECTORY/'production-source-contract.json');require(sha(raw)==PRODUCTION_CONTRACT_SHA,'production_contract_changed');p=json.loads(raw)
 require(p['repository']==REPOSITORY and p['origin']=='https://gurye.fwith.kr'and p['hostname']=='gurye.fwith.kr'and p['workerCandidate']=='gurye-flower-guide'and p['successorBranch']==BRANCH and p['sourceRoot']=='site-factory/gurye-flower','fixed_source_identity')
 require(sha(read(DIRECTORY/'bounded-contract.json'))==BOUNDED_CONTRACT_SHA,'bounded_contract_changed')
 for path,digest in [('scripts/direct-gurye/production-release/production-contract.json',PRODUCTION_CONTRACT_SHA),('scripts/direct-gurye/keyless-release/bounded-contract.json',BOUNDED_CONTRACT_SHA)]:require(next(r['sha256']for r in b['files']if r['path']==path)==digest,'source60_contract_projection_changed')
 proof=p['dedicatedPublicProof'];require(proof['path']=='/cc583d309cec4f73ff7832d6a7d7b36f.txt'and proof['sha256']=='3e26b5fd0f182a58af4f4905ba49b397f0f99d4dde26fc5b50e9839bb73ecb72','approved_same_proof_required')
 c=dict(sourceRevision=SOURCE,sourceTree=TREE,sourceRoot=p['sourceRoot'],sourceBranch=BRANCH,repository=REPOSITORY)
 derived=dict(sourceContractSha256=PRODUCTION_CONTRACT_SHA,boundedContractSha256=BOUNDED_CONTRACT_SHA,proof=dict(origin=p['origin'],path=proof['path'],sha256=proof['sha256']))
 return c,derived,QA_BINDING_SHA

def authorization_template(c):
 return dict(schemaVersion=1,recordType='user-authorization-not-readiness-proof',repository=REPOSITORY,sourceRoot=c['sourceRoot'],siteKey='gurye-flower-direct',hostname='gurye.fwith.kr',origin='https://gurye.fwith.kr',worker='gurye-flower-guide',sourceRevision=SOURCE,sourceTree=TREE,approvedOperations=['source-and-control-storage','production-build-and-QA','publication-after-own-gates','existing-provider-first-host-binding-with-no-overrides','same-approved-gurye-proof-and-one-URL-IndexNow-after-public-HTTP','public-build-publish-and-receipt-issues'],publicIssuesApproved=True,ownQualityAndSafetyGatesRequired=True,noNewCredentialsOrPermissionChanges=True,noDomainOwnershipTransferOrOverride=True,dedicatedProofApprovalVerifiedAtUTC='2026-10-16T14:31:30.443765+00:00')
def authorization(c,b):
 d=json.loads(read(DIRECTORY/'authorization-binding.json'));require(type(d)is dict and set(d)=={'schemaVersion','path','sha256','revision','publicIssuesApproved'}and type(d['schemaVersion'])is int and d['schemaVersion']==1,'authorization_descriptor_schema')
 require(d['publicIssuesApproved']is True,'public_issue_approval_required');require(d['path']=='docs/direct-gurye/production-authorization-20261016.json'and re.fullmatch('[0-9a-f]{64}',d['sha256']or'')and re.fullmatch('[0-9a-f]{40}',d['revision']or''),'pinned_authorization_required')
 raw=read(DIRECTORY.parents[1]/d['path']);require(sha(raw)==d['sha256'],'authorization_bytes_changed');a=json.loads(raw)
 require(same(a,authorization_template(c)),'exact_gurye_authorization_required');require(b['authorizationEvidence']=='https://github.com/'+REPOSITORY+'/blob/'+d['revision']+'/'+d['path'],'approval_reference_required');return d

def load():
 c,b,digest=inputs();d=json.loads(read(DIRECTORY/'authorization-binding.json'));b['authorizationEvidence']='https://github.com/'+REPOSITORY+'/blob/'+str(d.get('revision'))+'/'+str(d.get('path'));authorization(c,b);return c,b,digest

def trusted_control(env):
 require(env.get('GITHUB_REPOSITORY')==REPOSITORY and env.get('GITHUB_REF')=='refs/heads/main','owner_main_required')
 require(env.get('GITHUB_ACTOR')==OWNER and env.get('GITHUB_TRIGGERING_ACTOR')==OWNER and env.get('GITHUB_RUN_ATTEMPT')=='1','owner_first_attempt_required')
 require(env.get('GITHUB_EVENT_NAME')=='issues'and re.fullmatch('[1-9][0-9]*',env.get('GITHUB_RUN_ID','')),'actual_issue_run_required')
 root=DIRECTORY.parents[1];revision=env.get('GITHUB_SHA','');require(re.fullmatch('[0-9a-f]{40}',revision),'control_revision_required')
 require(git(root,'rev-parse','HEAD').decode().strip()==revision,'actual_control_revision_mismatch')
 scopes=['scripts/direct-gurye','docs/direct-gurye','.github/workflows/gurye-production-build-only.yml','.github/workflows/gurye-production-publish.yml',*['site-factory/engine/'+n for n in HELPER_SHA256]]
 require(not git(root,'status','--porcelain','--untracked-files=all','--',*scopes).strip(),'control_checkout_changed')
 for scope in scopes:
  entries=[e for e in git(root,'ls-tree','-r','-z','HEAD','--',scope).split(b'\0')if e];require(entries,'tracked_control_missing:'+scope)
  for entry in entries:
   meta,name=entry.split(b'\t');mode,kind,blob=meta.decode().split();name=name.decode();require(mode=='100644'and kind=='blob','control_entry_invalid');data=regular_under(root,name);require(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob,'control_bytes_changed:'+name)
 for name,digest in HELPER_SHA256.items():require(sha(read(root/'site-factory/engine'/name))==digest,'existing_helper_changed:'+name)
 c,b,_=load();a=authorization(c,b);require(git(root,'show',a['revision']+':'+a['path'])==read(root/a['path']),'authorization_revision_bytes_mismatch');git(root,'merge-base','--is-ancestor',a['revision'],'HEAD')
 return dict(controlRevision=revision,controlCheckoutVerified=True)
