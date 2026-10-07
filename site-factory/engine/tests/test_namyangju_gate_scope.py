"""Local prerequisite candidate validation, never a release or rendered QA approval."""
import copy,hashlib,json,pathlib,sys,unittest
P=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(P/'site-factory/engine'))
import whole_initial as w
SITE='namyangju-flower-v2';ROOT='site-factory/namyangju-flower';SCOPE=SITE+'-dong-coverage-20261005'
def read(p):return json.loads((P/p).read_text())
class NamyangjuGateScopeTests(unittest.TestCase):
 def test_exact_twenty_profile_is_pinned(self):
  site=read('.github/site-factory-sites.json')['sites'][SITE]
  self.assertEqual(w.REVIEWED_INITIAL,site['initialLaunch']);self.assertEqual(w.REVIEWED_INITIAL['officialUnitCount'],20)
  self.assertEqual(set(w.INITIAL_REGIONS),{SITE});self.assertEqual(set(w.INITIAL_SOURCE_PROFILES),{SITE})
 def test_public_gate_remains_closed(self):
  site=read('.github/site-factory-sites.json')['sites'][SITE]
  self.assertFalse(site['productionEnabled']);self.assertTrue(site['growthPaused']);self.assertFalse(site['autoDeploySnapshots'])
  self.assertEqual(site['approvedRevision'],'');self.assertEqual(site['approvalEvidenceUrl'],'');self.assertNotIn('initialDeployment',site)
  with self.assertRaises(ValueError):w.resolve(site,site['repo'],'4'*40,SITE+'-initial-20261005',SCOPE)
 def test_exact_visual_and_query_inputs(self):
  c=read(ROOT+'/src/data/region-coverage.json');p=read(ROOT+'/src/data/region-policy.json')
  reps={r['pageKey']:r for r in c['representatives']};bindings={r['pageKey']:r for r in p['visualBindings']}
  self.assertEqual(len(reps),20);self.assertEqual(len(p['visualBindings']),20);self.assertEqual(reps.keys(),bindings.keys())
  self.assertTrue(p['enabled']);self.assertEqual(p['scopeKey'],SCOPE)
  for key,b in bindings.items():
   self.assertEqual(reps[key]['status'],'approved');self.assertTrue(reps[key]['queryEvidence'])
   self.assertEqual(b['renderedQaStatus'],'pending');self.assertEqual(b['assetType'],'real_product');self.assertTrue(b['productKeys'])
   self.assertRegex(b['inputReviewSha256'],r'^[a-f0-9]{64}$');self.assertTrue(b['inputReviewRunId']);self.assertRegex(b['draftBodySha256'],r'^[a-f0-9]{64}$')
 def test_other_initial_sites_and_scopes_fail(self):
  profile=w.INITIAL_SOURCE_PROFILES[SITE]
  good={'siteKey':SITE,'scopeKey':SCOPE,'ruleRevision':w.RULE_REVISION,'templateRevision':profile['sourceRevision']}
  w.initial_batch_identity(good)
  for field,value in [('siteKey','pyeongtaek-flower-v2'),('siteKey','anyang-flower-v2'),('scopeKey',SITE+'-dong-coverage-20261006')]:
   bad={**good,field:value}
   with self.subTest(field=field,value=value),self.assertRaises(ValueError):w.initial_batch_identity(bad)
 def test_shrunken_registry_twenty_fails_before_preview(self):
  site=read('.github/site-factory-sites.json')['sites'][SITE];site['initialLaunch']['officialUnitCount']=19
  with self.assertRaisesRegex(ValueError,'exact reviewed20'):w.resolve_preview(site,site['repo'],SITE,'4'*40,SITE+'-initial-20261005',SCOPE)
 def test_other_regions_keep_existing_live_verifier(self):
  import tempfile
  import verify_live
  class ReachedLegacyFetch(Exception):pass
  def fetch(route):raise ReachedLegacyFetch(route)
  with tempfile.TemporaryDirectory() as directory:
   root=pathlib.Path(directory);(root/'src/data').mkdir(parents=True)
   (root/'src/data/publish-manifest.json').write_text('{"pages": []}')
   for key in ['pyeongtaek-flower-v2','anyang-flower-v2','suwon-flower-test']:
    with self.subTest(site=key),self.assertRaises(ReachedLegacyFetch):
     verify_live.verify(root,'https://example.com','4'*40,fetch,site_key=key)
   with self.assertRaisesRegex(ValueError,'Namyangju initial release'):
    verify_live.verify(root,'https://example.com','4'*40,fetch,site_key=SITE)
 def test_recovery_shell_dispatches_only_namyangju_to_initial(self):
  import re,subprocess
  text=(P/'.github/workflows/site-production-deploy.yml').read_text()
  condition=re.search(r'elif (.+); then\n\s+python3 control/site-factory/engine/verify_initial.py',text).group(1)
  for key,expected in [(SITE,'initial'),('pyeongtaek-flower-v2','legacy'),('anyang-flower-v2','legacy')]:
   run=subprocess.run(['bash','-c','SITE_KEY="$1"; if '+condition+'; then echo initial; else echo legacy; fi','test',key],capture_output=True,text=True,check=True)
   self.assertEqual(run.stdout.strip(),expected)
  self.assertNotIn('pyeongtaek-flower-v2',text);self.assertNotIn('anyang-flower-v2',text)
 def test_changed_bootstrap_source_fails_before_git_access(self):
  site=read('.github/site-factory-sites.json')['sites'][SITE]
  batch={'siteKey':SITE,'scopeKey':SCOPE,'ruleRevision':w.RULE_REVISION,'templateRevision':w.INITIAL_SOURCE_PROFILES[SITE]['sourceRevision'],'bootstrapSourceSha':'0'*40}
  with self.assertRaisesRegex(ValueError,'exact reviewed input source'):
   w.validate_initial_binding(batch,site,None,'1'*40,'2'*40)
if __name__=='__main__':unittest.main()
