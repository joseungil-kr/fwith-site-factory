"""Trusted-main gate for the fixed Boseong source50 and accepted Actions QA binding."""
from pathlib import Path
import hashlib, json, re, subprocess
DIRECTORY=Path(__file__).resolve().parent
REPOSITORY='joseungil-kr/fwith-site-factory'
OWNER='joseungil-kr'
SOURCE='eb4f931242e7b8f7598cd2fec957b0d988740e7a'
TREE='f7d6e5b1c4b1d649532519e66e23b840bc716472'
BRANCH='source/boseong-production-preparation-20261017'
SOURCE_ROOT='site-factory/boseong-flower'
HOSTNAME='boseong.fwith.kr'
ORIGIN='https://boseong.fwith.kr'
WORKER='boseong-flower-guide'
PRODUCTION_CONTRACT_SHA='40e26405a96a77cf8550df66d1aa06381149c6f107bb049ab5bd51cab5410273'
PRODUCTION_ADAPTER_SHA='bd49eede0bd3286c20af3f042156615af1d0b998e71a155e196b4d87ca5fbf56'
PROOF_FILE_SHA='58be5dbed02ccb2703e99e881d616982477ae2d22797a3f0d41995db6c35ad9a'
QA_BINDING_SHA='f7c8fd6d4f94bdfe70aaf70822e871219166ed75230bff94eaf940110ec25f9d'
RECOVERED_VERDICT_SHA256='2ac93a79f13cbc74937057c9317f7e3cc95caab12acac514b89daa1dbf46cef2'
RELEASE_MANIFEST_SHA256='33a78138a1f69f7a1ead53b0d3d7a31eea68114360cbc98710bb87de6fc9b3ce'
OUTPUT_FILES_SHA256='b4bd83e674d3b0aa66f17b0f5d0c5f57cd8afb88c98cea25078f4fb588a1367a'
ARTIFACT_ID='12086568586'
BUILD_RUN_ID='38994862258'
ARTIFACT_DIGEST='sha256:af5732bdc751630c7f7546f597947e0e00ea7d599e830f61a63d59ad9361a1a8'
AUTHORIZATION_PATH='docs/direct-boseong/production-authorization-20261017.json'
AUTHORIZATION_BINDING_PATH='authorization-binding.json'
def require(ok,code):
 if not ok: raise ValueError(code)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def same(a,b): return json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)
def read(path):
 p=Path(path); require(p.is_file() and not p.is_symlink(),'regular_file_required')
 for parent in p.absolute().parents: require(not parent.is_symlink(),'parent_symlink_forbidden')
 return p.read_bytes()
def git(root,*args): return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.STDOUT)
def load():
 raw=read(DIRECTORY/'production-release/production-contract.json')
 require(sha(raw)==PRODUCTION_CONTRACT_SHA,'production_contract_changed')
 c=json.loads(raw)
 require(c['repository']==REPOSITORY and c['sourceRoot']==SOURCE_ROOT and c['successorBranch']==BRANCH and c['hostname']==HOSTNAME and c['origin']==ORIGIN and c['workerCandidate']==WORKER and c['privateSourceRevision']=='e4fea02b97a46aa4e3853ed8d63a242a20b1dee3','source_contract_identity')
 require(c['indexRoutes']==['/'] and c['productionOutputFiles']==15 and c['bodyChangesAllowed']==[] and c['facilityPages']=='HOLD','approved_bounded_scope_required')
 require(c['approval']['dedicatedPublicProofGenerationAndApplication'] is True and c['approval']['indexNowSubmissionAuthorized'] is False,'approval_scope_changed')
 adapter=read(DIRECTORY/'production-release/production_adapter.py')
 require(sha(adapter)==PRODUCTION_ADAPTER_SHA,'accepted_adapter_changed')
 proof=read(DIRECTORY/'production-release/boseong-indexnow-proof.txt')
 row=c['dedicatedPublicProof']
 require(sha(proof)==row['sha256'] and row['path']=='/'+proof.decode().strip()+'.txt','approved_proof_mismatch')
 binding={'sourceContractSha256':PRODUCTION_CONTRACT_SHA,'proof':{'origin':ORIGIN,'path':row['path'],'sha256':row['sha256']}}
 return dict(sourceRevision=SOURCE,sourceTree=TREE,sourceRoot=SOURCE_ROOT,sourceBranch=BRANCH,repository=REPOSITORY,origin=ORIGIN,hostname=HOSTNAME,worker=WORKER),binding,QA_BINDING_SHA

def authorization_template(c):
 return dict(schemaVersion=1,recordType='user-authorized-boseong-publication-not-readiness-proof',repository=REPOSITORY,
   sourceRoot=SOURCE_ROOT,sourceBranch=BRANCH,sourceRevision=SOURCE,sourceTree=TREE,
   sourceContractSha256=PRODUCTION_CONTRACT_SHA,qaBindingSha256=QA_BINDING_SHA,
   actualProductionBuild=dict(runId=BUILD_RUN_ID,artifactId=ARTIFACT_ID,artifactDigest=ARTIFACT_DIGEST,
      buildControlRevision='d9e237974308c77af027a0f9ff70f17c3b34f8ad',releaseManifestSha256=RELEASE_MANIFEST_SHA256,
      outputFilesSha256=OUTPUT_FILES_SHA256),
   userAuthorization=dict(issuedAtUTC='2026-10-17T05:06:52Z',followupAtUTC='2026-10-17T05:07:26Z',
      scope=['finish already-started regional work in economy mode','publish the already-started Boseong site after its own quality, provider and public-HTTP gates'],
      explicitTask='사용량 절약모드로 나머지 지역 작업 진행바람',followup='하던 작업만 마무리'),
   publicationPhase=dict(name='boseong-first-publication-after-independent-review-and-own-gates',
      workflowPath='.github/workflows/boseong-production-publish.yml',ownerIssueTitle='[BOSEONG-PRODUCTION-PUBLISH] 20261017',
      controlRevisionMustMatchOwnerIssueAndGitHubSha=True,firstPublicationOnly=True,stopAndReconcileAfterAnyUncertainWrite=True),
   target=dict(origin=ORIGIN,hostname=HOSTNAME,worker=WORKER,workerMode='static-assets-only',routes=['/']),
   authorizedProviderEffects=dict(workerAssetUpload='one fixed retained artifact upload after GET preflight',
      customDomainAttach=dict(hostname=HOSTNAME,zone='fwith.kr',overrideScope=False,overrideExistingOrigin=False,
         overrideExistingDnsRecord=False,mayAutomaticallyCreateDnsRecord=True,mayInitiateTlsCertificateProvisioning=True),
      domainOwnershipTransfer=False,existingRecordOverride=False),
   exclusions=dict(indexNowSubmissionAuthorized=False,newIndexNowKeyOrCredentialAuthorized=False,
      productionReadyClaimBeforePublicHttp=False,facilityPages='HOLD'))

def authorization(c):
 d=json.loads(read(DIRECTORY/AUTHORIZATION_BINDING_PATH))
 require(type(d)is dict and set(d)=={'schemaVersion','path','sha256','revision','publicIssuesApproved'}
    and type(d['schemaVersion'])is int and d['schemaVersion']==1,'authorization_descriptor_schema')
 require(d['publicIssuesApproved'] is True and d['path']==AUTHORIZATION_PATH
    and re.fullmatch('[0-9a-f]{64}',d['sha256'] or '') and re.fullmatch('[0-9a-f]{40}',d['revision'] or ''),
    'saved_publication_authorization_required')
 root=DIRECTORY.parents[1]; raw=read(root/AUTHORIZATION_PATH)
 require(sha(raw)==d['sha256'],'publication_authorization_bytes_changed')
 require(same(json.loads(raw),authorization_template(c)),'exact_publication_authorization_required')
 try:saved=git(root,'show',d['revision']+':'+d['path'])
 except subprocess.CalledProcessError as error:raise ValueError('publication_authorization_revision_commit_missing') from error
 require(saved==raw,'publication_authorization_revision_bytes_mismatch')
 try:git(root,'merge-base','--is-ancestor',d['revision'],'HEAD')
 except subprocess.CalledProcessError as error:raise ValueError('publication_authorization_commit_not_in_history') from error
 return d
def trusted_control(env):
 require(env.get('GITHUB_REPOSITORY')==REPOSITORY and env.get('GITHUB_REF')=='refs/heads/main','owner_main_required')
 require(env.get('GITHUB_ACTOR')==OWNER and env.get('GITHUB_TRIGGERING_ACTOR')==OWNER and env.get('GITHUB_RUN_ATTEMPT')=='1','owner_first_attempt_required')
 require(env.get('GITHUB_EVENT_NAME')=='issues' and re.fullmatch('[1-9][0-9]*',env.get('GITHUB_RUN_ID','')),'actual_issue_run_required')
 root=DIRECTORY.parents[1]; rev=env.get('GITHUB_SHA','')
 require(re.fullmatch('[0-9a-f]{40}',rev),'control_revision_required')
 require(git(root,'rev-parse','HEAD').decode().strip()==rev,'actual_control_revision_mismatch')
 scopes=['scripts/direct-boseong','docs/direct-boseong','.github/workflows/boseong-production-publish.yml',*['site-factory/engine/'+n for n in ['bucheon_domain_attach.py','goyang_domain.py']]]
 require(not git(root,'status','--porcelain','--untracked-files=all','--',*scopes).strip(),'control_checkout_changed')
 for scope in scopes:
  entries=[e for e in git(root,'ls-tree','-r','-z','HEAD','--',scope).split(b'\0') if e]
  require(entries,'tracked_control_missing:'+scope)
  for entry in entries:
   meta,name=entry.split(b'\t');mode,kind,blob=meta.decode().split();name=name.decode()
   require(mode=='100644' and kind=='blob','control_entry_invalid')
   data=read(root/name)
   require(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob,'control_bytes_changed:'+name)
 c,b,_=load()
 d=authorization(c)
 require(d['path']==AUTHORIZATION_PATH,'publication_authorization_path_mismatch')
 return dict(controlRevision=rev,controlCheckoutVerified=True)
