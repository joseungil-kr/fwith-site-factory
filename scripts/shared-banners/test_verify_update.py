#!/usr/bin/env python3
import unittest,types,json,os,tempfile,copy
from pathlib import Path
from unittest.mock import patch
import verify_update as v
class ExistingUpdateBoundary(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.old=Path.cwd();os.chdir(self.temp.name);Path('release').mkdir()
  self.source={'name':'seoul-yangcheon-flower-guide','compatibility_date':'2026-10-10','workers_dev':False,'assets':{'directory':'./dist/','not_found_handling':'404-page','html_handling':'auto-trailing-slash'}}
  Path('release/wrangler.publish.json').write_text(json.dumps(self.source));self.target={'previousRevision':'a'*40,'revision':'b'*40}
 def tearDown(self):os.chdir(self.old);self.temp.cleanup()
 def pub(self,revisions=None):
  html=''.join(f'<meta name="site-factory-revision" content="{s}">' for s in (revisions if revisions is not None else ['a'*40]))
  return types.SimpleNamespace(get=lambda path:(html.encode(),{}),HOSTNAME='seoul-yangcheon.fwith.kr',ORIGIN='https://seoul-yangcheon.fwith.kr',WORKER='seoul-yangcheon-flower-guide',sha=lambda b:v.hashlib.sha256(b).hexdigest(),save=lambda p,d:Path(p).write_text(json.dumps(d)))
 def settings(self):return dict(bindings=[],compatibility_date='2026-10-10',compatibility_flags=[],logpush=False,placement={},tags=[],tail_consumers=[],usage_model='standard')
 def get(self,settings=None,sub=None,domains=None):
  account='1'*32;prefix='/accounts/'+account;pub=self.pub();self.requests=[]
  rows=domains if domains is not None else [dict(id='2'*32,hostname=pub.HOSTNAME,service=pub.WORKER,zone_id='3'*32,zone_name='fwith.kr')]
  def request(path):
   self.requests.append(path)
   if path==prefix:return {'result':{'id':account}}
   if path==prefix+'/workers/scripts?page=1&per_page=100':return {'result':[{'id':pub.WORKER}]}
   if path==prefix+'/workers/domains?page=1&per_page=100':return {'result':rows}
   if path==prefix+'/workers/scripts/'+pub.WORKER+'/settings':return {'result':settings if settings is not None else self.settings()}
   if path==prefix+'/workers/scripts/'+pub.WORKER+'/subdomain':return {'result':sub if sub is not None else {'enabled':False,'previews_enabled':False}}
   raise AssertionError('Unexpected provider endpoint: '+path)
  return account,request
 def test_exact_existing_target(self):
  with patch.object(v,'provider_get',return_value=self.get()):r=v.preflight(self.target,self.pub())
  self.assertEqual(r['state'],'existing_update_preflight_verified');self.assertFalse(r['providerMutationsPerformed']);self.assertFalse(r['hostnameAttachAllowed']);self.assertTrue(all('/zones' not in p for p in self.requests))
  after=json.loads(Path('release/wrangler.publish.json').read_text());self.assertFalse(after['preview_urls']);self.assertNotIn('routes',after)
 def test_provider_before_after_unchanged(self):
  with patch.object(v,'provider_get',return_value=self.get()):before=v.preflight(self.target,self.pub())
  Path('binding-before.json').write_text(json.dumps(before))
  with patch.object(v,'provider_get',return_value=self.get()):self.assertEqual(v.provider_after(self.target,self.pub())['state'],'provider_settings_and_exposure_unchanged')
 def test_changed_preview_state_after_upload_rejected(self):
  with patch.object(v,'provider_get',return_value=self.get()):before=v.preflight(self.target,self.pub())
  Path('binding-before.json').write_text(json.dumps(before))
  with patch.object(v,'provider_get',return_value=self.get(sub={'enabled':False,'previews_enabled':True})):
   with self.assertRaisesRegex(ValueError,'provider_state_changed'):v.provider_after(self.target,self.pub())
 def test_missing_existing_binding_rejected(self):
  with patch.object(v,'provider_get',return_value=self.get(domains=[])):
   with self.assertRaises(ValueError):v.preflight(self.target,self.pub())
 def test_wrong_old_revision_rejected(self):
  with patch.object(v,'provider_get',return_value=self.get()):
   with self.assertRaisesRegex(ValueError,'previous_public_revision_mismatch'):v.preflight(self.target,self.pub(['c'*40]))
 def test_duplicate_revision_meta_rejected(self):
  with patch.object(v,'provider_get',return_value=self.get()):
   with self.assertRaisesRegex(ValueError,'previous_public_revision_mismatch'):v.preflight(self.target,self.pub(['a'*40,'a'*40]))
 def test_bindings_rejected_before_persistence(self):
  settings=self.settings();settings['bindings']=[{'name':'DO_NOT_PERSIST','type':'secret_text'}]
  with patch.object(v,'provider_get',return_value=self.get(settings=settings)):
   with self.assertRaises(ValueError):v.preflight(self.target,self.pub())
  self.assertFalse(Path('provider-state-before.json').exists())
 def test_unknown_settings_rejected(self):
  settings=self.settings();settings['new_capability']=True
  with patch.object(v,'provider_get',return_value=self.get(settings=settings)):
   with self.assertRaises(ValueError):v.preflight(self.target,self.pub())
 def test_nondefault_logging_rejected(self):
  settings=self.settings();settings['logpush']=True
  with patch.object(v,'provider_get',return_value=self.get(settings=settings)):
   with self.assertRaises(ValueError):v.preflight(self.target,self.pub())
 def test_compatibility_date_drift_rejected(self):
  settings=self.settings();settings['compatibility_date']='2026-10-09'
  with patch.object(v,'provider_get',return_value=self.get(settings=settings)):
   with self.assertRaises(ValueError):v.preflight(self.target,self.pub())
 def test_workers_dev_drift_rejected(self):
  with patch.object(v,'provider_get',return_value=self.get(sub={'enabled':True,'previews_enabled':False})):
   with self.assertRaises(ValueError):v.preflight(self.target,self.pub())
 def test_absent_preview_exposure_rejected(self):
  with patch.object(v,'provider_get',return_value=self.get(sub={'enabled':False})):
   with self.assertRaises(ValueError):v.preflight(self.target,self.pub())
 def test_no_provider_write_method(self):
  calls=[];transport=v.readonly(lambda *args:calls.append(args))
  for method in ['POST','PUT','PATCH','DELETE']:
   with self.assertRaisesRegex(ValueError,'provider_mutation_forbidden'):transport(method,'/accounts/fixed-account',{})
  self.assertEqual(calls,[])
 def test_unknown_targets_rejected(self):
  with self.assertRaisesRegex(ValueError,'unknown_fixed_update_target'):v.load('unrelated')
 def test_workflow_retains_initial_guard_and_excludes_attach_in_update(self):
  w=(v.ROOT/'.github/workflows/seoul-yangcheon-direct-publish.yml').read_text();p=(v.ROOT/'scripts/direct-seoul-yangcheon/publish.py').read_text()
  self.assertIn("require(not matches and not exists, 'initial_target_must_be_absent')",p)
  self.assertIn("if: steps.deploy.outcome == 'success' && !(inputs.existing_update == true",w)
  self.assertIn('verify_update.py provider-after --region seoul-yangcheon',w)
  self.assertIn('WRANGLER_PACKAGE=wrangler@4.147.0',w)
  self.assertIn('WRANGLER_PACKAGE=wrangler@4.148.0',w)
  self.assertEqual(w.count('npx --yes "$WRANGLER_PACKAGE" deploy'),1)
  self.assertNotIn('override_existing_dns_record=True',w+p)
class ReviewedEvidenceBoundary(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.real=v.ROOT
  self.target=json.loads((self.real/'docs/shared-banner-release/targets.json').read_text())['targets']['seoul-yangcheon']
  self.target['changedFileCount']=13
  for key in ['sourceReadback','independentStaticReview']:
   p=self.root/self.target[key];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((self.real/self.target[key]).read_bytes())
  pub=self.root/v.ALLOWED['seoul-yangcheon'];pub.parent.mkdir(parents=True,exist_ok=True);pub.write_bytes((self.real/v.ALLOWED['seoul-yangcheon']).read_bytes())
  self.env=patch.dict(os.environ,REVISION=self.target['revision'],GITHUB_REPOSITORY=self.target['repository'],GITHUB_RUN_ATTEMPT='1');self.env.start();self.patch=patch.object(v,'ROOT',self.root);self.patch.start()
 def tearDown(self):self.patch.stop();self.env.stop();self.temp.cleanup()
 def load(self):
  (self.root/'docs/shared-banner-release/targets.json').write_text(json.dumps({'targets':{'seoul-yangcheon':self.target}}));return v.load('seoul-yangcheon')
 def evidence(self,fn):
  p=self.root/self.target['sourceReadback'];d=json.loads(p.read_text());fn(d);p.write_text(json.dumps(d));self.target['sourceReadbackSha256']=v.hashlib.sha256(p.read_bytes()).hexdigest()
 def test_exact_reviewed_source(self):self.assertEqual(self.load()[0]['changedFileCount'],13)
 def test_wrong_count_rejected(self):
  self.target['changedFileCount']=14
  with self.assertRaisesRegex(ValueError,'source_change_scope_mismatch'):self.load()
 def test_missing_count_rejected(self):
  self.target.pop('changedFileCount')
  with self.assertRaisesRegex(ValueError,'reviewed_change_count_required'):self.load()
 def test_duplicate_path_rejected(self):
  self.evidence(lambda d:d['remoteChangedFiles'].__setitem__(1,d['remoteChangedFiles'][0]))
  with self.assertRaisesRegex(ValueError,'source_change_scope_mismatch'):self.load()
 def test_parent_path_rejected(self):
  self.evidence(lambda d:d['remoteChangedFiles'][0].update(path=self.target['root']+'/../other'))
  with self.assertRaisesRegex(ValueError,'source_change_scope_mismatch'):self.load()
 def test_unverified_readback_rejected(self):
  self.evidence(lambda d:d['remoteChangedFiles'][0].update(remoteBytesMatch=False))
  with self.assertRaisesRegex(ValueError,'source_change_scope_mismatch'):self.load()
 def test_wrong_evidence_digest_rejected(self):
  self.target['sourceReadbackSha256']='0'*64
  with self.assertRaisesRegex(ValueError,'review_evidence_digest_mismatch'):self.load()
 def test_wrong_revision_rejected(self):
  with patch.dict(os.environ,REVISION='0'*40):
   with self.assertRaisesRegex(ValueError,'new_revision_mismatch'):self.load()
 def test_unreviewed_source_rejected(self):
  self.target['status']='pending'
  with self.assertRaisesRegex(ValueError,'source_review_required'):self.load()
 def test_wrong_hostname_rejected(self):
  self.target['hostname']='other.fwith.kr'
  with self.assertRaisesRegex(ValueError,'fixed_identity_mismatch'):self.load()
 def test_mutation_rerun_rejected(self):
  with patch.dict(os.environ,GITHUB_RUN_ATTEMPT='2'):
   with self.assertRaisesRegex(ValueError,'update_rerun_forbidden'):self.load()
 def test_reviewed_banner_revision_cannot_use_ordinary_mutation(self):
  self.load()
  for flag in ['false','','TRUE','1']:
   with patch.dict(os.environ,EXISTING_UPDATE=flag):
    with self.assertRaisesRegex(ValueError,'reviewed_banner_revision_requires_existing_update'):v.authorize_mutation('seoul-yangcheon')
 def test_reviewed_banner_update_requires_exact_review(self):
  self.load()
  with patch.dict(os.environ,EXISTING_UPDATE='true'):
   self.assertTrue(v.authorize_mutation('seoul-yangcheon')['reviewedBannerRevision'])
   self.target['status']='pending';(self.root/'docs/shared-banner-release/targets.json').write_text(json.dumps({'targets':{'seoul-yangcheon':self.target}}))
   with self.assertRaisesRegex(ValueError,'source_review_required'):v.authorize_mutation('seoul-yangcheon')
 def test_other_source_ordinary_mode_is_preserved(self):
  self.load()
  with patch.dict(os.environ,REVISION='0'*40,EXISTING_UPDATE='false'):
   self.assertFalse(v.authorize_mutation('seoul-yangcheon')['reviewedBannerRevision'])
 def test_unpinned_source_cannot_claim_existing_update(self):
  self.load()
  with patch.dict(os.environ,REVISION='0'*40,EXISTING_UPDATE='true'):
   with self.assertRaisesRegex(ValueError,'new_revision_mismatch'):v.authorize_mutation('seoul-yangcheon')
class BatchWorkflowBoundary(unittest.TestCase):
 def test_every_fixed_workflow_preserves_existing_update_boundaries(self):
  for region in v.ALLOWED:
   with self.subTest(region=region):
    w=(v.ROOT/f'.github/workflows/{region}-direct-publish.yml').read_text()
    self.assertIn('group: '+region+'-direct-public-release',w)
    self.assertIn('cancel-in-progress: false',w)
    self.assertIn("if: steps.deploy.outcome == 'success' && !(inputs.existing_update == true",w)
    for mode in ['artifact','preflight','provider-after','public-assets']:self.assertIn(f'verify_update.py {mode} --region {region}',w)
    self.assertIn('WRANGLER_PACKAGE=wrangler@4.147.0',w);self.assertIn('WRANGLER_PACKAGE=wrangler@4.148.0',w)
    self.assertEqual(w.count('npx --yes "$WRANGLER_PACKAGE" deploy'),1)
    self.assertIn('Source branch moved; do not publish stale source',w)
    self.assertNotIn('override_existing_dns_record=True',w)
    self.assertEqual(w.count('verify_update.py authorize-mutation --region '+region),1)
    if '  finalize_indexnow:' in w:self.assertNotIn('authorize-mutation',w.split('  finalize_indexnow:',1)[1])
    else:self.assertIn(region,{'anyang','pyeongtaek'}) # Existing workflows have no finalization-only job.
class Direct7ReviewBoundary(unittest.TestCase):
 def test_expanded_targets_still_require_reviewed_manifest(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);p=root/'docs/shared-banner-release/targets.json';p.parent.mkdir(parents=True);p.write_text(json.dumps({'targets':{}}))
   with patch.object(v,'ROOT',root):
    for region in ('anyang','gwangmyeong','pyeongtaek','yeoju','seoul-eunpyeong','seoul-seodaemun','seoul-mapo'):
     with self.subTest(region=region):
      with self.assertRaisesRegex(ValueError,'update_target_not_reviewed'):v.load(region)
 def test_every_reviewed_direct7_revision_requires_update_mode(self):
  regions=('anyang','gwangmyeong','pyeongtaek','yeoju','seoul-eunpyeong','seoul-seodaemun','seoul-mapo')
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);p=root/'docs/shared-banner-release/targets.json';p.parent.mkdir(parents=True);p.write_text(json.dumps({'targets':{r:{'revision':'b'*40} for r in regions}}))
   with patch.object(v,'ROOT',root),patch.dict(os.environ,REVISION='b'*40,EXISTING_UPDATE='false'):
    for region in regions:
     with self.subTest(region=region):
      with self.assertRaisesRegex(ValueError,'reviewed_banner_revision_requires_existing_update'):v.authorize_mutation(region)
if __name__=='__main__':unittest.main()
