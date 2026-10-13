#!/usr/bin/env python3
"""One reviewed 33-site banner revision. Reuses fixed publishers; no provider calls."""
import argparse,hashlib,importlib.util,json,os,re,subprocess
from pathlib import Path
VERSION='phone-20261013'
DIRECTORY='docs/shared-banner-phone-20261013'
PLAN_SHA256='c06421db6e4c3244a491aac1a98a5f7da1bc3b8631a082c8947f2dffd0bd478b'
REVIEW_SHA256='70fa687a556c75ab43d9d0a47c9088c19813d9fdd8b8a6590f14e4512e106f71'
ASSETS_SHA256='6586d75a83366fbe261782648db1aec96d46790ef724e34c4b6e70025d1568ff'
REGIONS=frozenset('anseong dongducheon gapyeong gimpo gunpo guri gwacheon gwangju hanam icheon jongno osan paju pocheon seoul-dobong seoul-dongdaemun seoul-gangbuk seoul-gangseo seoul-guro seoul-gwangjin seoul-jung seoul-jungnang seoul-nowon seoul-seongbuk seoul-seongdong seoul-yangcheon seoul-yongsan siheung uijeongbu uiwang yangju yangpyeong yeoncheon'.split())
def require(value,code):
 if not value:raise ValueError(code)
def sha(data):return hashlib.sha256(data).hexdigest()
def json_bytes(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def checked_file(root,relative,digest):
 require(isinstance(relative,str)and relative.startswith(DIRECTORY+'/')and'..'not in Path(relative).parts,'phone_evidence_path_invalid')
 path=root/relative;require(path.is_file()and not path.is_symlink(),'phone_evidence_missing')
 require(re.fullmatch('[0-9a-f]{64}',digest or '')and sha(path.read_bytes())==digest,'phone_evidence_digest_mismatch')
 return path.read_bytes()
def plans(root):
 raw=checked_file(root,DIRECTORY+'/source-plans.json',PLAN_SHA256);rows=json.loads(raw)
 require(len(rows)==33 and {p['region']for p in rows}==REGIONS,'phone_exact_allowlist_required')
 return {p['region']:p for p in rows}
def catalog(root):
 path=root/DIRECTORY/'targets.json'
 if not path.is_file():return None
 value=json.loads(path.read_text());require(value.get('version')==VERSION and set(value.get('targets',{}))==REGIONS,'phone_catalog_version_or_allowlist_mismatch')
 return value['targets']
def selected(root,region):
 targets=catalog(root)
 return bool(targets and region in REGIONS and re.fullmatch('[0-9a-f]{40}',os.environ.get('REVISION','')) and targets[region].get('revision')==os.environ['REVISION'])
def load(root,region,require_release=False):
 require(region in REGIONS,'unknown_phone_update_target');plan=plans(root)[region];targets=catalog(root);require(targets is not None,'phone_catalog_missing');target=targets[region]
 require(target.get('version')==VERSION,'phone_target_version_mismatch')
 require(target.get('status')=='independently_reviewed_source','phone_source_review_required')
 require(target.get('previousRevision')==plan['parentCommit'],'phone_parent_revision_mismatch')
 require(re.fullmatch('[0-9a-f]{40}',target.get('revision')or '')and target['revision']!=plan['parentCommit']and target['revision']==os.environ.get('REVISION'),'phone_new_revision_mismatch')
 require(target.get('changedFileCount')==len(plan['changedFiles'])and target.get('exactChangedPaths')==[r['path']for r in plan['changedFiles']],'phone_exact_change_scope_required')
 review=checked_file(root,DIRECTORY+'/source-review.md',REVIEW_SHA256);require(b'PASS_SOURCE_SAVE_BUILD_ONLY'in review,'phone_source_review_verdict_missing')
 evidence=json.loads(checked_file(root,target.get('sourceReadback'),target.get('sourceReadbackSha256')))
 require(evidence.get('sourceCommit')==target['revision']and evidence.get('parentCommit')==plan['parentCommit']and evidence.get('allFilesMatch')is True,'phone_remote_readback_identity_mismatch')
 expected={r['path']:(r['newSha256'],r['newGitBlob'])for r in plan['changedFiles']};rows=evidence.get('remoteChangedFiles',[])
 require(len(rows)==len(expected)and len({r.get('path')for r in rows})==len(expected),'phone_readback_path_set_mismatch')
 require({r.get('path'):(r.get('sha256'),r.get('gitBlob'))for r in rows}==expected and all(r.get('remoteBytesMatch')is True for r in rows),'phone_readback_exact_hash_mismatch')
 pubpath=root/f'scripts/direct-{region}/publish.py';spec=importlib.util.spec_from_file_location('phone_fixed_'+region.replace('-','_'),pubpath);pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
 identity={'repository':pub.REPOSITORY,'branch':pub.BRANCH,'root':pub.SOURCE_ROOT,'hostname':pub.HOSTNAME,'worker':pub.WORKER}
 require(all(target.get(k)==v for k,v in identity.items())and target['branch']==plan['branch']and target['root']==plan['root']and target['hostname']==plan['hostname'],'phone_fixed_identity_mismatch')
 require(os.environ.get('GITHUB_REPOSITORY')==pub.REPOSITORY,'repository_mismatch');require(os.environ.get('GITHUB_RUN_ATTEMPT')=='1','update_rerun_forbidden')
 checked_file(root,DIRECTORY+'/approved-assets.json',ASSETS_SHA256)
 if require_release:release_review(root,target)
 return target,pub

def release_review(root,target):
 review=json.loads(checked_file(root,target.get('releaseReview'),target.get('releaseReviewSha256')))
 require(review.get('verdict')=='PASS_PUBLIC_UPDATE'and review.get('sourceCommit')==target['revision']and review.get('previousRevision')==target['previousRevision']and review.get('sourcePlanSha256')==PLAN_SHA256,'phone_release_review_identity_mismatch')
 require(review.get('allRouteOutputVerified')is True and review.get('nativeTestsPassed')is True and review.get('mobileAndDesktopPixelsVerified')is True,'phone_actual_build_and_pixel_review_required')
 require(re.fullmatch('[0-9]+',str(review.get('buildRunId','')))and re.fullmatch('[0-9]+',str(review.get('artifactId','')))and re.fullmatch('[0-9a-f]{64}',review.get('outputFilesSha256','')),'phone_actual_build_binding_required')
 proofs=review.get('evidence',[]);require(len(proofs)>=3,'phone_release_proofs_missing')
 require({r.get('kind')for r in proofs}>={'all-route-output','mobile-pixels','desktop-pixels'},'phone_release_proof_kinds_missing')
 for proof in proofs:checked_file(root,proof.get('path'),proof.get('sha256'))
 return review

def source(root,region,checkout):
 target,pub=load(root,region);plan=plans(root)[region];checkout=Path(checkout)
 def git(*args):return subprocess.check_output(['git','-C',str(checkout),*args],env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0'})
 require(git('rev-parse','HEAD').decode().strip()==target['revision'],'phone_checkout_revision_mismatch')
 require(git('rev-list','--parents','-n','1','HEAD').decode().split()==[target['revision'],target['previousRevision']],'phone_single_exact_parent_required')
 require(not git('status','--porcelain','--untracked-files=all').strip(),'phone_source_checkout_not_clean')
 changed=git('diff','--name-only','-z',target['previousRevision'],target['revision'],'--').decode().rstrip('\0').split('\0');expected=[r['path']for r in plan['changedFiles']]
 require(len(changed)==len(expected)and set(changed)==set(expected),'phone_git_delta_scope_mismatch')
 for row in plan['changedFiles']:
  path=checkout/row['path'];require(path.is_file()and not path.is_symlink()and sha(path.read_bytes())==row['newSha256'],'phone_source_bytes_mismatch')
  require(git('rev-parse','HEAD:'+row['path']).decode().strip()==row['newGitBlob'],'phone_source_git_blob_mismatch')
 return {'state':'exact_phone_source_successor_verified','revision':target['revision'],'previousRevision':target['previousRevision'],'changedFiles':len(expected),'scopeSha256':PLAN_SHA256}

def artifact(root,target,pub,for_public=False):
 manifest=json.loads(Path('release/release.json').read_text());require(manifest.get('revision')==target['revision']and manifest.get('worker')==pub.WORKER and manifest.get('origin')==pub.ORIGIN,'phone_artifact_identity_mismatch')
 actual=pub.inventory(Path('release/dist'));require(manifest.get('files')==actual,'phone_artifact_files_mismatch');digest=sha(json_bytes(actual))
 if for_public:require(release_review(root,target)['outputFilesSha256']==digest,'phone_rebuilt_output_differs_from_reviewed_build')
 spec=importlib.util.spec_from_file_location('phone_banner_qa',Path(__file__).with_name('qa_phone_banners.py'));qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
 os.environ['SITE_URL']=pub.ORIGIN;os.environ['SITE_INDEXABLE']='true';report=qa.inspect(Path('release'),root/DIRECTORY/'approved-assets.json')
 Path('release/shared-banner-qa.json').replace('phone-shared-banner-qa.json')
 return {'state':'phone_banner_artifact_verified','revision':target['revision'],'outputFilesSha256':digest,'assetSha256':report['assetSha256'],'files':report['files'],'banners':report['banners'],'customerHtml':report['customerHtml']}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['select','source','build-artifact']);parser.add_argument('--region',required=True);parser.add_argument('--checkout');parser.add_argument('--report',required=True);args=parser.parse_args();root=Path(__file__).resolve().parents[2];target,pub=load(root,args.region)
 if args.mode=='select':
  result={'state':'reviewed_phone_source_selected','region':args.region,'branch':target['branch'],'sourceRoot':target['root'],'publisher':f'scripts/direct-{args.region}/publish.py','origin':pub.ORIGIN,'revision':target['revision']}
  with open(os.environ['GITHUB_OUTPUT'],'a')as f:
   for key in ['branch','sourceRoot','publisher','origin','revision']:f.write(key+'='+result[key]+'\n')
 elif args.mode=='source':result=source(root,args.region,args.checkout)
 else:
  pub.artifact();result=artifact(root,target,pub);Path('release/wrangler.publish.json').replace('build-wrangler.publish.json')
 Path(args.report).write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
