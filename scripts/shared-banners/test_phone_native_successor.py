#!/usr/bin/env python3
"""Synthetic successor proofs and Git responses. Never a real save/build/release record."""
import copy,json,os,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import phone_update as phone
ROOT=Path(__file__).resolve().parents[2]

class NativeEvidenceBoundary(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  shutil.copytree(ROOT/phone.DIRECTORY,self.root/phone.DIRECTORY)
  for region in ['anseong','seoul-yangcheon','seoul-gangseo','seoul-guro']:
   dst=self.root/f'scripts/direct-{region}/publish.py';dst.parent.mkdir(parents=True);shutil.copyfile(ROOT/f'scripts/direct-{region}/publish.py',dst)
  self.path=self.root/phone.DIRECTORY/'targets.json';self.data=json.loads(self.path.read_text());self.target=self.data['targets']['anseong'];self.parent=json.loads((self.root/self.target['sourceReadback']).read_text())['sourceCommit'];self.revision='f'*40
  self.target['releaseReview']=None;self.target['releaseReviewSha256']=None
  self.plan=next(r for r in json.loads((self.root/phone.DIRECTORY/'native-successor-plans.json').read_text())if r['region']=='anseong')
  self.target['revision']=self.revision;self.native={'sourceParentRevision':self.parent};self.target['nativeSuccessor']=self.native
  self.readback={'syntheticUnitFixtureOnly':True,'sourceCommit':self.revision,'parentCommit':self.parent,'previousPublicRevision':self.target['previousRevision'],'allFilesMatch':True,'remoteChangedFiles':[{'path':r['path'],'sha256':r['newSha256'],'gitBlob':r['newGitBlob'],'remoteBytesMatch':True}for r in self.plan['changedFiles']]}
  self.save_readback()
  proofs=[]
  for kind in ['source-scope','native-tests']:
   relative=phone.DIRECTORY+'/synthetic-'+kind+'.txt';p=self.root/relative;p.write_text('Synthetic unit fixture only. No GitHub commit or build exists.');proofs.append({'kind':kind,'path':relative,'sha256':phone.sha(p.read_bytes())})
  self.review={'syntheticUnitFixtureOnly':True,'verdict':'PASS_NATIVE_SOURCE_BUILD_ONLY','region':'anseong','repository':self.target['repository'],'branch':self.target['branch'],'root':self.target['root'],'sourceCommit':self.revision,'sourceParentRevision':self.parent,'previousPublicRevision':self.target['previousRevision'],'originalSourcePlanSha256':phone.PLAN_SHA256,'nativeSuccessorPlanSha256':phone.NATIVE_PLAN_SHA256,'originalSourceReadbackSha256':self.target['sourceReadbackSha256'],'sourceReadbackSha256':self.native['sourceReadbackSha256'],'independentlyReviewed':True,'exactChangedFileCount':5,'customerFilesChanged':0,'historicalFixtureAndTestsUnchanged':True,'nativeTestsPassed':True,'evidence':proofs}
  self.save_review();self.env=patch.dict(os.environ,REVISION=self.revision,GITHUB_REPOSITORY='joseungil-kr/fwith-site-factory',GITHUB_RUN_ATTEMPT='1');self.env.start()
 def tearDown(self):self.env.stop();self.temp.cleanup()
 def save(self):self.path.write_text(json.dumps(self.data))
 def write_proof(self,name,value):
  relative=phone.DIRECTORY+'/synthetic-native-'+name+'.json';p=self.root/relative;p.write_text(json.dumps(value));return relative,phone.sha(p.read_bytes())
 def save_readback(self):
  self.native['sourceReadback'],self.native['sourceReadbackSha256']=self.write_proof('readback',self.readback);self.save()
 def save_review(self):
  self.native['independentReview'],self.native['independentReviewSha256']=self.write_proof('review',self.review);self.save()
 def reject(self,code='phone_'):
  self.save()
  with self.assertRaisesRegex(ValueError,code):phone.load(self.root,'anseong')
 def test_complete_synthetic_native_record_selects_build_only(self):
  target,_=phone.load(self.root,'anseong');self.assertEqual(target['revision'],self.revision);self.assertNotEqual(target['previousRevision'],self.parent)
 def test_unactivated_new_revision_fails_closed(self):self.target.pop('nativeSuccessor');self.reject('phone_remote_readback_identity_mismatch')
 def test_missing_successor_fields_fail_closed(self):
  original=copy.deepcopy(self.native)
  for key in original:
   with self.subTest(key=key):self.native.clear();self.native.update(original);self.native.pop(key);self.reject()
 def test_null_or_empty_successor_fails_closed(self):
  for value in [None,{},[],False]:
   with self.subTest(value=value):self.target['nativeSuccessor']=value;self.reject()
 def test_r2_is_not_a_new_native_revision(self):
  self.target['revision']=self.parent
  with patch.dict(os.environ,REVISION=self.parent):self.reject('phone_native_parent_mismatch')
 def test_public_revision_cannot_be_replaced_by_source_parent(self):self.target['previousRevision']=self.parent;self.reject('phone_parent_revision_mismatch')
 def test_unaffected_three_cannot_opt_in(self):
  for region in ['seoul-yangcheon','seoul-gangseo','seoul-guro']:
   target=self.data['targets'][region];target['nativeSuccessor']=copy.deepcopy(self.native);target['revision']=self.revision;self.save()
   with self.subTest(region=region),self.assertRaisesRegex(ValueError,'phone_native_target_forbidden'):phone.load(self.root,region)
 def test_original_evidence_cannot_be_refreshed(self):
  p=self.root/self.target['sourceReadback'];p.write_text(p.read_text()+' ');self.target['sourceReadbackSha256']=phone.sha(p.read_bytes());self.reject('phone_native_original_readback_changed')
 def test_native_plan_digest_drift_fails_closed(self):
  p=self.root/phone.DIRECTORY/'native-successor-plans.json';p.write_text(p.read_text()+' ');self.reject('phone_evidence_digest_mismatch')
 def test_original_plan_digest_still_required(self):
  p=self.root/phone.DIRECTORY/'source-plans.json';p.write_text(p.read_text()+' ');self.reject('phone_evidence_digest_mismatch')
 def test_original_scope_stays_exact_seven(self):self.target['changedFileCount']=12;self.reject('phone_exact_change_scope_required')
 def test_native_readback_wrong_identities_fail_closed(self):
  original=copy.deepcopy(self.readback)
  for key in ['sourceCommit','parentCommit','previousPublicRevision','allFilesMatch']:
   with self.subTest(key=key):self.readback=copy.deepcopy(original);self.readback[key]='wrong';self.save_readback();self.reject('phone_native_readback_identity_mismatch')
 def test_native_readback_wrong_paths_hashes_and_flags_fail_closed(self):
  original=copy.deepcopy(self.readback)
  for key,value in [('path',self.target['root']+'/src/data/products.json'),('sha256','0'*64),('gitBlob','0'*40),('remoteBytesMatch',False)]:
   with self.subTest(key=key):self.readback=copy.deepcopy(original);self.readback['remoteChangedFiles'][0][key]=value;self.save_readback();self.reject('phone_native_readback_exact_hash_mismatch')
 def test_native_readback_extra_missing_and_duplicate_fail_closed(self):
  original=copy.deepcopy(self.readback)
  for case in ['extra','missing','duplicate']:
   with self.subTest(case=case):
    self.readback=copy.deepcopy(original);rows=self.readback['remoteChangedFiles']
    if case=='extra':rows.append(rows[0])
    elif case=='missing':rows.pop()
    else:rows[1]=rows[0]
    self.save_readback();self.reject('phone_native_readback_path_set_mismatch')
 def test_each_review_identity_is_required(self):
  original=copy.deepcopy(self.review)
  for key in ['verdict','region','repository','branch','root','sourceCommit','sourceParentRevision','previousPublicRevision','originalSourcePlanSha256','nativeSuccessorPlanSha256','originalSourceReadbackSha256','sourceReadbackSha256']:
   with self.subTest(key=key):self.review=copy.deepcopy(original);self.review[key]='wrong';self.save_review();self.reject('phone_native_independent_review_identity_mismatch')
 def test_each_independent_review_gate_is_required(self):
  original=copy.deepcopy(self.review)
  for key in ['independentlyReviewed','exactChangedFileCount','customerFilesChanged','historicalFixtureAndTestsUnchanged','nativeTestsPassed']:
   with self.subTest(key=key):self.review=copy.deepcopy(original);self.review.pop(key);self.save_review();self.reject('phone_native_independent_review_required')
 def test_review_proof_kinds_missing_rejected(self):
  self.review['evidence'].pop();self.save_review();self.reject('phone_native_review_proofs_missing')
 def test_review_proof_bytes_changed_rejected(self):
  (self.root/self.review['evidence'][0]['path']).write_text('changed');self.reject('phone_evidence_digest_mismatch')
 def test_readback_bytes_changed_without_rehash_rejected(self):
  (self.root/self.native['sourceReadback']).write_text('{}');self.reject('phone_evidence_digest_mismatch')
 def test_missing_readback_file_rejected(self):
  (self.root/self.native['sourceReadback']).unlink();self.reject('phone_evidence_missing')
 def test_missing_review_file_rejected(self):
  (self.root/self.native['independentReview']).unlink();self.reject('phone_evidence_missing')
 def test_review_path_traversal_rejected(self):self.native['independentReview']=phone.DIRECTORY+'/../outside.json';self.reject('phone_evidence_path_invalid')
 def test_null_release_review_remains_provider_blocker(self):
  with self.assertRaisesRegex(ValueError,'phone_evidence_path_invalid'):phone.load(self.root,'anseong',require_release=True)
 def test_existing_mutation_flow_cannot_use_native_source_review_as_release(self):
  import verify_update as legacy
  with patch.object(legacy,'ROOT',self.root),patch.dict(os.environ,EXISTING_UPDATE='true'),self.assertRaisesRegex(ValueError,'phone_evidence_path_invalid'):legacy.authorize_mutation('anseong')
 def test_native_release_requires_both_lineage_and_new_review_bindings(self):
  release={'syntheticUnitFixtureOnly':True,'verdict':'PASS_PUBLIC_UPDATE','sourceCommit':self.revision,'previousRevision':self.target['previousRevision'],'sourcePlanSha256':phone.PLAN_SHA256,'nativeSuccessorPlanSha256':phone.NATIVE_PLAN_SHA256,'sourceParentRevision':self.parent,'nativeSourceReadbackSha256':self.native['sourceReadbackSha256'],'nativeSourceReviewSha256':self.native['independentReviewSha256'],'allRouteOutputVerified':True,'nativeTestsPassed':True,'mobileAndDesktopPixelsVerified':True,'buildRunId':'123','artifactId':'456','outputFilesSha256':'a'*64,'evidence':[]}
  for kind in ['all-route-output','mobile-pixels','desktop-pixels']:
   path,digest=self.write_proof(kind,{'syntheticUnitFixtureOnly':True});release['evidence'].append({'kind':kind,'path':path,'sha256':digest})
  def record(value):self.target['releaseReview'],self.target['releaseReviewSha256']=self.write_proof('release',value);self.save()
  record(release);phone.load(self.root,'anseong',require_release=True)
  for key in ['nativeSuccessorPlanSha256','sourceParentRevision','nativeSourceReadbackSha256','nativeSourceReviewSha256']:
   value=copy.deepcopy(release);value.pop(key);record(value)
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,'phone_native_release_binding_required'):phone.load(self.root,'anseong',require_release=True)
  value=copy.deepcopy(release);value['sourceCommit']=self.parent;record(value)
  with self.assertRaisesRegex(ValueError,'phone_release_review_identity_mismatch'):phone.load(self.root,'anseong',require_release=True)

class NativeGitBoundary(unittest.TestCase):
 """Synthetic Git object maps; this test makes no Git/network writes."""
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.public='a'*40;self.parent='b'*40;self.tip='c'*40
  self.target={'revision':self.tip,'previousRevision':self.public,'nativeSuccessor':{'sourceParentRevision':self.parent}}
  self.original={'changedFiles':[]};self.plan={'sourceParentRevision':self.parent,'changedFiles':[]};self.snapshots={x:{}for x in [self.public,self.parent,self.tip]};self.parents={self.parent:[self.public],self.tip:[self.parent]};self.case='clean'
  for i in range(7):self.add('banner-'+str(i),'old-banner-'+str(i),'new-banner-'+str(i),self.original,self.public,self.parent)
  self.snapshots[self.tip]=copy.deepcopy(self.snapshots[self.parent])
  for i in range(5):self.add('tests/qa-'+str(i),'old-qa'if i==0 else None,'new-qa-'+str(i),self.plan,self.parent,self.tip)
  # A preexisting helper is present at the public baseline too.
  self.snapshots[self.public]['tests/qa-0']=self.snapshots[self.parent]['tests/qa-0']
  for path,blob in self.snapshots[self.tip].items():p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob['bytes'])
 def tearDown(self):self.temp.cleanup()
 def object(self,value):
  import hashlib
  b=value.encode();return {'bytes':b,'sha':phone.sha(b),'blob':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),'mode':'100644'}
 def add(self,path,before,after,plan,start,end):
  old=self.object(before)if before is not None else None;new=self.object(after)
  if old:self.snapshots[start][path]=old
  self.snapshots[end][path]=new;plan['changedFiles'].append({'path':path,'oldSha256':old['sha']if old else None,'oldGitBlob':old['blob']if old else None,'newSha256':new['sha'],'newGitBlob':new['blob']})
 def git(self,args,**kwargs):
  command=args[3:]
  if command==['rev-parse','HEAD']:return (self.tip+'\n').encode()
  if command[:4]==['rev-list','--parents','-n','1']:
   rev=command[4];return (' '.join([rev]+self.parents[rev])+'\n').encode()
  if command==['status','--porcelain','--untracked-files=all']:return b' M unrelated'if self.case=='dirty'else b''
  if command[:3]==['diff','--name-only','-z']:
   a,b=self.snapshots[command[3]],self.snapshots[command[4]];paths=[p for p in sorted(set(a)|set(b))if a.get(p)!=b.get(p)]
   if self.case=='combined'and command[3:5]==[self.public,self.tip]:paths.append('unapproved')
   return ''.join(p+'\0'for p in paths).encode()
  if command[:2]==['ls-tree','-z']:
   rev,path=command[2],command[4];obj=self.snapshots[rev].get(path)
   return (obj['mode']+' blob '+obj['blob']+'\t'+path+'\0').encode()if obj else b''
  if command[:2]==['cat-file','blob']:
   rev,path=command[2].split(':',1);b=self.snapshots[rev][path]['bytes'];return b+'drift'.encode()if self.case=='cat-drift'else b
  raise AssertionError(command)
 def run_source(self):
  with patch.object(phone,'load',return_value=(self.target,None)),patch.object(phone,'plans',return_value={'fixture':self.original}),patch.object(phone,'native_plan',return_value=self.plan),patch.object(phone.subprocess,'check_output',side_effect=self.git):return phone.source(ROOT,'fixture',self.root)
 def reject(self,code='phone_'):
  with self.assertRaisesRegex(ValueError,code):self.run_source()
 def test_exact_two_edges_preserve_public_parent(self):
  result=self.run_source();self.assertEqual(result['changedFiles'],12);self.assertEqual(result['previousRevision'],self.public);self.assertEqual(result['sourceParentRevision'],self.parent)
 def test_both_edges_require_single_exact_parent(self):
  for rev in [self.parent,self.tip]:
   original=self.parents[rev]
   for parents in [[],['d'*40],original+['d'*40]]:
    with self.subTest(rev=rev,parents=parents):self.parents[rev]=parents;self.reject('phone_native_single_exact_parent_required')
   self.parents[rev]=original
 def test_squashed_source_cannot_skip_r2(self):self.parents[self.tip]=[self.public];self.reject('phone_native_single_exact_parent_required')
 def test_dirty_checkout_rejected(self):self.case='dirty';self.reject('phone_source_checkout_not_clean')
 def test_second_stage_customer_change_rejected(self):self.snapshots[self.tip]['banner-0']=self.object('extra customer edit');self.reject('phone_native_git_delta_scope_mismatch')
 def test_first_stage_extra_change_rejected(self):self.snapshots[self.parent]['unapproved']=self.object('extra');self.reject('phone_native_git_delta_scope_mismatch')
 def test_second_stage_missing_file_rejected(self):self.snapshots[self.tip].pop('tests/qa-4');self.reject('phone_native_git_delta_scope_mismatch')
 def test_combined_diff_must_equal_exact_twelve_paths(self):self.case='combined';self.reject('phone_native_combined_scope_mismatch')
 def test_old_git_bytes_checked_independently(self):self.case='cat-drift';self.reject('phone_native_historical_bytes_mismatch')
 def test_new_git_blob_drift_rejected(self):self.snapshots[self.tip]['tests/qa-0']['blob']='d'*40;self.reject('phone_native_git_blob_or_mode_mismatch')
 def test_source_mode_change_rejected(self):self.snapshots[self.tip]['tests/qa-0']['mode']='100755';self.reject('phone_native_git_blob_or_mode_mismatch')
 def test_added_qa_path_cannot_preexist(self):
  old=self.object('already here');self.snapshots[self.public]['tests/qa-1']=old;self.snapshots[self.parent]['tests/qa-1']=old;self.reject('phone_native_added_path_preexists')
 def test_worktree_customer_bytes_cannot_drift(self):(self.root/'banner-0').write_text('changed');self.reject('phone_source_bytes_mismatch')
 def test_worktree_qa_bytes_cannot_drift(self):(self.root/'tests/qa-0').write_text('changed');self.reject('phone_source_bytes_mismatch')
 def test_worktree_symlink_rejected(self):p=self.root/'tests/qa-0';p.unlink();p.symlink_to('qa-1');self.reject('phone_source_bytes_mismatch')

class FrozenNativeBoundary(unittest.TestCase):
 def test_shipping_catalog_has_no_synthetic_successor_authority(self):
  targets=phone.catalog(ROOT);self.assertEqual(set(targets),phone.REGIONS)
  for region,t in targets.items():
   with self.subTest(region=region):
    self.assertNotEqual(t['revision'],'f'*40)
    if 'nativeSuccessor'in t:
     for field in ['sourceReadback','independentReview']:
      proof=json.loads(phone.checked_file(ROOT,t['nativeSuccessor'][field],t['nativeSuccessor'][field+'Sha256']));self.assertNotIn('syntheticUnitFixtureOnly',proof)
 def test_frozen_plan_preserves_original_thirty_r2_and_public_boundaries(self):
  plans=phone.plans(ROOT);targets=phone.catalog(ROOT);rows=json.loads(phone.checked_file(ROOT,phone.DIRECTORY+'/native-successor-plans.json',phone.NATIVE_PLAN_SHA256));self.assertEqual(len(rows),30);self.assertEqual({r['region']for r in rows},phone.NATIVE_REGIONS)
  for row in rows:
   region=row['region'];self.assertEqual(row['sourceParentRevision'],json.loads((ROOT/targets[region]['sourceReadback']).read_text())['sourceCommit']);self.assertEqual(row['previousPublicRevision'],plans[region]['parentCommit']);self.assertEqual(len(row['changedFiles']),5);self.assertEqual(row['customerFilesChanged'],0)
if __name__=='__main__':unittest.main()
