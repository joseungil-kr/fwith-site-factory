import copy,unittest
from write_assets_only_config import configuration,state_digest
class ConfigTests(unittest.TestCase):
 def setUp(self):
  self.state={'worker':'existing','settings':{'bindings':[],'compatibility_date':'2026-09-29','compatibility_flags':[],'logpush':False,'placement':{},'tags':[],'tail_consumers':[],'usage_model':'standard'},'workersDev':{'enabled':False,'previews_enabled':False},'domains':[],'legacyRoutes':{'state':'not_read_not_modified','requiresAssetsOnlyConfig':True},'scope':'fixed-worker-and-existing-fwith.kr-domains'}
  self.policy={'worker':'existing','productionOrigin':'https://s.fwith.kr','providerBaselineSha256':{'production':state_digest(self.state)}}
  self.source={'name':'existing','compatibility_date':'2026-09-29','workers_dev':False,'assets':{'directory':'./dist/','not_found_handling':'404-page','html_handling':'auto-trailing-slash'},'routes':[{'pattern':'s.fwith.kr','custom_domain':True}]}
 def run_config(self):return configuration(self.policy,'production',self.source,self.state)
 def test_omits_domains_preserves_disabled_preview(self):
  result=self.run_config();self.assertNotIn('routes',result);self.assertNotIn('route',result);self.assertFalse(result['preview_urls']);self.assertEqual(result['observability'],{'enabled':False})
 def test_preserves_enabled_preview(self):
  self.state['workersDev']['previews_enabled']=True;self.policy['providerBaselineSha256']['production']=state_digest(self.state);self.assertTrue(self.run_config()['preview_urls'])
 def test_missing_preview_blocks(self):
  del self.state['workersDev']['previews_enabled'];self.policy['providerBaselineSha256']['production']=state_digest(self.state)
  with self.assertRaisesRegex(ValueError,'Incomplete'):self.run_config()
 def test_exposure_drift_blocks(self):
  self.source['workers_dev']=True
  with self.assertRaisesRegex(ValueError,'exposure'):self.run_config()
 def test_foreign_route_blocks(self):
  self.source['routes'][0]['pattern']='foreign.invalid'
  with self.assertRaisesRegex(ValueError,'Foreign route'):self.run_config()
 def test_legacy_route_blocks(self):
  self.source['routes']=['s.fwith.kr/*']
  with self.assertRaisesRegex(ValueError,'Foreign route'):self.run_config()
 def test_digest_drift_blocks(self):
  self.state['settings']['tags']=['new']
  with self.assertRaisesRegex(ValueError,'Unreviewed live receipt'):self.run_config()
 def test_nondefault_settings_block_even_with_digest(self):
  self.state['settings']['logpush']=True;self.policy['providerBaselineSha256']['production']=state_digest(self.state)
  with self.assertRaisesRegex(ValueError,'Nondefault'):self.run_config()
 def test_date_change_blocks(self):
  self.source['compatibility_date']='2026-10-07'
  with self.assertRaisesRegex(ValueError,'Nondefault'):self.run_config()
 def test_new_binding_config_blocks(self):
  self.source['vars']={'x':'private'}
  with self.assertRaisesRegex(ValueError,'capability'):self.run_config()
if __name__=='__main__':unittest.main()
