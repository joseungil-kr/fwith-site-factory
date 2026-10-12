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
if __name__=='__main__':unittest.main()
