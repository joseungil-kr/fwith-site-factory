"""Offline local Git fixtures. No fixture run IDs, approvals or commits are release evidence."""
import contextlib,copy,json,os,shutil,socket,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import production_build as b

HERE=Path(__file__).resolve().parent
class LocalGitTests(unittest.TestCase):
 def command(self,root,*args):
  return subprocess.check_output(['git','-c','core.hooksPath=/dev/null','-c','user.name=Offline Fixture','-c','user.email=fixture@example.invalid','-C',str(root),*args],stderr=subprocess.STDOUT).decode().strip()
 def commit(self,root,label):
  self.command(root,'add','.');self.command(root,'commit','-m','OFFLINE TEST ONLY: '+label);return self.command(root,'rev-parse','HEAD')
 def setUp(self):
  self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
  self.stack.enter_context(patch.object(socket,'create_connection',side_effect=AssertionError('network forbidden')))
  self.root=Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix='gwangsan-offline-git-fixture-')))
  self.target=self.root/'target';self.target.mkdir();self.command(self.target,'init','-b','fixture-source')
  original=Path(os.environ.get('GWANGSAN_SOURCE_TEST_ROOT',str(HERE.parents[3]/'gwangsan-policy-source-save-r2-20261016/remote-readback')))
  # Source paths must be explicitly provided on CI, which has its pinned checkout.
  if not original.is_dir():original=Path(os.environ.get('GITHUB_WORKSPACE',''))/'target'/b.ROOT
  if not original.is_dir():self.fail('exact pinned correction source checkout required for local Git fixtures')
  rows=json.loads((HERE/'source-manifest.json').read_text())
  for row in rows:
   data=(original/row['path']).read_bytes();self.assertEqual(b.sha(data),row['sha256']);target=self.target/b.ROOT/row['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  self.source_commit=self.commit(self.target,'single-source92')
  self.control=self.root/'control';shutil.copytree(HERE.parents[1],self.control,ignore=shutil.ignore_patterns('.git','__pycache__','*.pyc'))
  self.command(self.control,'init','-b','fixture-main');self.d=self.control/'scripts/direct-gwangju-gwangsan-policy-correction'
  self.stack.enter_context(patch.object(b,'DIRECTORY',self.d))
  self.env=dict(GITHUB_REPOSITORY=b.REPOSITORY,GITHUB_REF='refs/heads/main',GITHUB_ACTOR=b.OWNER,GITHUB_TRIGGERING_ACTOR=b.OWNER,GITHUB_RUN_ATTEMPT='1',GITHUB_EVENT_NAME='issues',GITHUB_RUN_ID='999999',SITE_RELEASE_MODE='production',SITE_INDEXABLE='true',SITE_URL=b.ORIGIN,SITE_FACTORY_REVISION=self.source_commit,SITE_RELEASE_BINDING_PATH=str(self.d/'production-binding.json'))
  self.original_revision=b.SOURCE_REVISION;self.original_git_tree=b.SOURCE_GIT_TREE
  self.stack.enter_context(patch.object(b,'SOURCE_REVISION',self.source_commit));self.stack.enter_context(patch.object(b,'SOURCE_GIT_TREE',self.command(self.target,'rev-parse','HEAD:'+b.ROOT)))
  historical=json.loads((self.d/'historical-authorization-binding.json').read_text());historical['revision']=self.commit(self.control,'historical authorization bytes only');b.save(self.d/'historical-authorization-binding.json',historical)
  self.stack.enter_context(patch.object(b,'HISTORICAL_AUTHORIZATION_REVISION',historical['revision']));self.stack.enter_context(patch.object(b,'HISTORICAL_AUTHORIZATION_DESCRIPTOR_SHA',b.sha((self.d/'historical-authorization-binding.json').read_bytes())))
  self.bind_source()
 def bind_source(self):
  self.source_commit=self.command(self.target,'rev-parse','HEAD');self.env['SITE_FACTORY_REVISION']=self.source_commit
  b.SOURCE_REVISION=self.source_commit;b.SOURCE_GIT_TREE=self.command(self.target,'rev-parse','HEAD:'+b.ROOT)
  c={**b.contract_template(),'sourceRevision':self.source_commit,'sourceTree':self.command(self.target,'rev-parse','HEAD:'+b.ROOT)};b.save(self.d/'production-source-contract.json',c)
  auth={**b.authorization_template(c),'authorizationEvidence':[b.public_issue_approval_evidence()]}
  name='docs/direct-gwangju-gwangsan-policy-correction/production-authorization-20261016.json';b.save(self.control/name,auth)
  auth_commit=self.commit(self.control,'local authorization fixture')
  b.save(self.d/'authorization-binding.json',dict(schemaVersion=1,path=name,sha256=b.sha((self.control/name).read_bytes()),revision=auth_commit,publicIssuesApproved=True))
  binding={**b.binding_template(c),'sourceContractSha256':b.sha((self.d/'production-source-contract.json').read_bytes()),'authorizationEvidence':'https://github.com/'+b.REPOSITORY+'/blob/'+b.HISTORICAL_AUTHORIZATION_REVISION+'/docs/direct-gwangju-gwangsan/production-authorization-20261016.json'};b.save(self.d/'production-binding.json',binding)
  self.env.update(GITHUB_SHA=self.commit(self.control,'bound control fixture'),SITE_RELEASE_BINDING_SHA256=b.sha((self.d/'production-binding.json').read_bytes()))
 def verify(self,phase='prebuild'):return b.source(self.target,phase,self.env)
 def test_actual_local_git_head_tree_all_92_and_split_manifests(self):
  result=self.verify();self.assertEqual((result['sourceFiles'],result['privateFiles'],result['adapterFiles']),(92,77,15));self.assertFalse(result['publicationExecuted'])
 def test_actual_control_wrong_head_or_changed_files(self):
  bad={**self.env,'GITHUB_SHA':'0'*40}
  with self.assertRaisesRegex(ValueError,'actual_control_revision_mismatch'):b.trusted_control(bad)
  p=self.d/'production-source-contract.json';p.write_bytes(p.read_bytes()+b' ')
  with self.assertRaisesRegex(ValueError,'control_checkout_changed'):b.trusted_control(self.env)
 def test_all_owner_main_first_attempt_identity_mutations(self):
  for key,value in [('GITHUB_REPOSITORY','other/repo'),('GITHUB_REF','refs/heads/source'),('GITHUB_ACTOR','other'),('GITHUB_TRIGGERING_ACTOR','other'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_RUN_ID','0'),('GITHUB_EVENT_NAME','push')]:
   with self.subTest(key=key),self.assertRaises(ValueError):b.trusted_control({**self.env,key:value})
 def test_private_and_adapter_mutations_rejected_pre_and_post(self):
  for name in ['candidate/src/lib/donggu-runtime.mjs','release-adapter/scripts/gwangsan_release.mjs']:
   p=self.target/b.ROOT/name;raw=p.read_bytes();p.write_bytes(raw+b'\n')
   for phase in ['prebuild','postbuild']:
    with self.subTest(name=name,phase=phase),self.assertRaises(ValueError):self.verify(phase)
   p.write_bytes(raw)
 def test_missing_source_file_rejected(self):
  p=self.target/b.ROOT/'candidate/README.md';p.unlink()
  with self.assertRaises(ValueError):self.verify()
 def test_untracked_hidden_and_extra_files_rejected_both_phases(self):
  for name in ['candidate/.env','inputs/extra.json','release-adapter/.hidden']:
   p=self.target/b.ROOT/name;p.write_text('OFFLINE')
   for phase in ['prebuild','postbuild']:
    with self.subTest(name=name,phase=phase),self.assertRaises(ValueError):self.verify(phase)
   p.unlink()
 def test_parent_symlink_rejected_even_when_bytes_match(self):
  p=self.target/b.ROOT/'inputs';outside=self.root/'outside';p.rename(outside);p.symlink_to(outside,target_is_directory=True)
  with self.assertRaises((ValueError,subprocess.CalledProcessError)):self.verify('postbuild')
 def test_executable_git_mode_rejected(self):
  p=self.target/b.ROOT/'candidate/README.md';p.chmod(0o755);self.commit(self.target,'wrong executable source mode');self.bind_source()
  with self.assertRaisesRegex(ValueError,'source_entry_invalid'):self.verify()
 def test_added_tracked_source_file_rejected(self):
  (self.target/b.ROOT/'inputs/extra.json').write_text('{}');self.commit(self.target,'extra tracked source');self.bind_source()
  with self.assertRaisesRegex(ValueError,'source_file_count_mismatch'):self.verify()
 def test_committed_changed_private_or_adapter_bytes_rejected(self):
  p=self.target/b.ROOT/'release-adapter/README.ko.md';p.write_bytes(p.read_bytes()+b'\n');self.commit(self.target,'changed adapter');self.bind_source()
  with self.assertRaisesRegex(ValueError,'source_bytes_changed'):self.verify()
 def test_source_head_changed_without_control_binding_rejected(self):
  p=self.target/b.ROOT/'candidate/README.md';p.write_bytes(p.read_bytes()+b'\n');self.commit(self.target,'new unapproved source commit')
  with self.assertRaisesRegex(ValueError,'source_revision_mismatch'):self.verify()
 def test_authorization_changed_even_if_recommitted_rejected(self):
  p=self.control/'docs/direct-gwangju-gwangsan-policy-correction/production-authorization-20261016.json';a=json.loads(p.read_text());a['publicIssuesApproved']=False;b.save(p,a)
  self.env['GITHUB_SHA']=self.commit(self.control,'changed authorization')
  with self.assertRaisesRegex(ValueError,'authorization_bytes_changed'):b.trusted_control(self.env)
 def test_pending_public_issues_cannot_promote_synthetic_node_binding(self):
  p=self.d/'authorization-binding.json';a=json.loads(p.read_text());a['publicIssuesApproved']=False;b.save(p,a)
  self.env['GITHUB_SHA']=self.commit(self.control,'unapproved issue descriptor')
  with self.assertRaisesRegex(ValueError,'current_correction_public_issue_approval_required'):b.trusted_control(self.env)
 def test_no_predecessor_is_invented(self):
  c,_,_=b.load();self.assertNotIn('previewSourceRevision',c);self.assertNotIn('frozenPreviewTree',c)
  self.assertEqual(len(b.frozen_manifests()[0]),77);self.assertEqual(len(b.frozen_manifests()[1]),15)
if __name__=='__main__':unittest.main()
