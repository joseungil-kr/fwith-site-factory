"""Static/pure correction gate mutations; no browser, socket, remote or deployment.
Actual output tests require explicit YEOSU_CORRECTION_DIST; synthetic revisions are
fixtures, never evidence of GitHub execution or rendered screenshots.
"""
import ast,copy,hashlib,json,os,re,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import production_build as B
D=Path(__file__).resolve().parent
class FrozenControls(unittest.TestCase):
 def test_frozen_source88_output18_and_independent_inputs(self):
  source,baseline,output=B.frozen();self.assertEqual((len(source),len(baseline),len(output)),(88,85,18));self.assertEqual(len(B.data('private-source75.json')),75)
  p,s=B.load_ui_expectations();self.assertEqual(len(p),4);self.assertEqual(len(s['faqs']),4);self.assertEqual(s['productCards'],[])
  self.assertTrue(all(not x['productCardIds'] for x in p));self.assertEqual(sum(len(x['images']) for x in p),6)
 def test_saved_source_binding_is_not_historical_revision(self):
  c,b,h=B.load();self.assertNotEqual(c['sourceRevision'],B.R3_SOURCE);self.assertNotEqual(c['sourceRevision'],B.BASE)
  self.assertEqual(b['sourceRevision'],c['sourceRevision']);self.assertFalse(B.data('qa-scope.json')['publicationAuthorized'])
 def test_frozen_control_mutation_fails(self):
  for name in ['expected-source88.json','expected-output18.json','ui-expectations.json','patch-spec.json','original-html/404.html','r3-review-binding.json','r4-layout-binding.json','r4-source-review.json','frozen-source-save-review.r4.json','original-assets/CopyPage.BgCFg6FO.css','trusted-frozen-files.json']:
   with self.subTest(name=name),tempfile.TemporaryDirectory() as temp:
    p=Path(temp)/'controls';shutil.copytree(D,p,ignore=shutil.ignore_patterns('__pycache__'));f=p/name;f.write_bytes(f.read_bytes()+b' ')
    with patch.object(B,'DIRECTORY',p),self.assertRaises(ValueError):B.load()
 def test_changed_revision_tree_parent_scope_or_binding_fails(self):
  mutations=[('correction-source-contract.json','sourceRevision','a'*40),('correction-source-contract.json','sourceTree','b'*40),('correction-source-contract.json','sourceParentRevision','c'*40),('qa-scope.json','publicationAuthorized',True),('production-binding.json','sourceRevision',B.BASE)]
  for name,key,value in mutations:
   with self.subTest(key=key),tempfile.TemporaryDirectory() as temp:
    p=Path(temp)/'controls';shutil.copytree(D,p,ignore=shutil.ignore_patterns('__pycache__'));v=json.loads((p/name).read_text());v[key]=value;B.save(p/name,v)
    with patch.object(B,'DIRECTORY',p),self.assertRaises(ValueError):B.load()
 def test_independent_expectations_not_read_from_target(self):
  import production_capture as C
  with patch('subprocess.run',side_effect=AssertionError('no source execution allowed')):
   a,s=C.capture_inputs('/does-not-exist');self.assertEqual(len(a),4)
 def test_r3_exact_two_phrase_changes_bound(self):
  r=B.data('r3-review-binding.json');self.assertEqual(r['operationIndexes'],[36,41]);self.assertIn('직접 확인한 내용은 아닙니다',r['newSentence'])
  for page in B.data('ui-expectations.json')['pages']:
   if page['path'] in ['/', '/regions/yeosu-jeonnam-hospital-funeral-wreath/']:self.assertIn(r['newSentence'],page['requiredBodyPhrases'])

class SelectRequest(unittest.TestCase):
 def setUp(self):
  self.c,_,self.digest=B.load();self.env={'GITHUB_REPOSITORY':B.REPOSITORY,'GITHUB_REF':'refs/heads/main','GITHUB_ACTOR':B.OWNER,'GITHUB_TRIGGERING_ACTOR':B.OWNER,'GITHUB_RUN_ATTEMPT':'1','GITHUB_EVENT_NAME':'issues','GITHUB_SHA':'a'*40}
  self.body=dict(schemaVersion=1,mode='yeosu-policy-correction-readonly-qa',source_branch=B.BRANCH,source_revision=self.c['sourceRevision'],expected_control_revision=self.env['GITHUB_SHA'],binding_sha256=self.digest,frozen_review_manifest_sha256=B.FROZEN_SHA,correction_spec_sha256=B.R4_SPEC_SHA)
  self.event={'action':'opened','repository':{'full_name':B.REPOSITORY,'owner':{'login':B.OWNER,'type':'User'}},'issue':{'title':B.TITLE,'user':{'login':B.OWNER},'body':json.dumps(self.body),'number':123,'state':'open'}}
 def go(self):return B.select(self.c,self.digest,self.env,self.event)
 def test_only_exact_owner_main_first_attempt_request(self):
  r=self.go();self.assertFalse(r['publicationAuthorized']);self.assertFalse(r['publicationExecuted']);self.assertFalse(r['indexNowSubmitted'])
 def test_environment_mutations_rejected(self):
  for key in list(self.env)+['CLOUDFLARE_API_TOKEN','AWS_ACCESS_KEY_ID']:
   with self.subTest(key=key),patch.dict(self.env,{key:'wrong'}),self.assertRaises(ValueError):self.go()
 def test_all_body_fields_and_extra_mutations_rejected(self):
  for key in list(self.body)+['extra']:
   v={**self.body,key:'wrong'}
   with self.subTest(key=key),patch.dict(self.event['issue'],{'body':json.dumps(v)}),self.assertRaises(ValueError):self.go()
 def test_issue_author_title_state_action_and_pull_request_rejected(self):
  for key,value in [('title','wrong'),('user',{'login':'someone'}),('state','closed'),('number',None),('pull_request',{})]:
   with self.subTest(key=key),patch.dict(self.event['issue'],{key:value}),self.assertRaises(ValueError):self.go()
  with patch.dict(self.event,{'action':'edited'}),self.assertRaises(ValueError):self.go()
 def test_wrong_repository_owner_rejected(self):
  with patch.dict(self.event['repository'],{'owner':{'login':B.OWNER,'type':'Organization'}}),self.assertRaises(ValueError):self.go()
 def test_environment_path_digest_revision_and_provider(self):
  e={'SITE_RELEASE_MODE':'production','SITE_INDEXABLE':'true','SITE_URL':B.ORIGIN,'SITE_FACTORY_REVISION':self.c['sourceRevision'],'SITE_RELEASE_BINDING_PATH':str(D/'production-binding.json'),'SITE_RELEASE_BINDING_SHA256':self.digest};B.environment(self.c,self.digest,e)
  for k in list(e)+['CLOUDFLARE_API_TOKEN','VERCEL_TOKEN']:
   with patch.dict(e,{k:'wrong'}),self.assertRaises(ValueError):B.environment(self.c,self.digest,e)

class ActualOutputMutations(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  raw=os.environ.get('YEOSU_CORRECTION_DIST')
  if not raw:raise unittest.SkipTest('Actual correction output path not supplied; pure tests only')
  cls.original=Path(raw);require=cls.original/'index.html'
  if not require.is_file():raise RuntimeError('explicit_output_missing')
  cls.revision=re.search(r'<meta name="site-factory-revision" content="([0-9a-f]{40})">',require.read_text()).group(1)
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.dist=Path(t.name)/'dist';shutil.copytree(self.original,self.dist)
 def go(self):return B.inspect_dist(self.dist,self.revision)
 def test_actual18_matches_frozen_expected(self):
  r=self.go();self.assertEqual(r['outputFiles'],18);self.assertFalse(r['mobileAndDesktopPixelsVerified']);self.assertFalse(r['publicationAuthorized'])
 def test_each_of18_bytes_is_bound(self):
  for name in B.data('expected-output18.json'):
   p=self.dist/name;old=p.read_bytes()
   with self.subTest(name=name):
    p.write_bytes(old+b'\n')
    with self.assertRaises(ValueError):self.go()
    p.write_bytes(old)
 def test_every_file_is_required_and_extras_rejected(self):
  for name in B.data('expected-output18.json'):
   p=self.dist/name;old=p.read_bytes();p.unlink()
   with self.subTest(name=name),self.assertRaises(ValueError):self.go()
   p.write_bytes(old)
  (self.dist/'extra').write_text('fixture')
  with self.assertRaises(ValueError):self.go()
 def test_symlink_output_fails(self):
  p=self.dist/'favicon.svg';p.unlink();p.symlink_to(self.dist/'robots.txt')
  with self.assertRaisesRegex(ValueError,'symlink'):self.go()
 def test_each_html_revision_duplicate_and_missing(self):
  for p in self.dist.rglob('*.html'):
   old=p.read_text();needle='<meta name="site-factory-revision" content="'+self.revision+'">'
   for altered in ['',needle+needle,needle.replace(self.revision,'f'*40)]:
    p.write_text(old.replace(needle,altered))
    with self.subTest(path=str(p),altered=altered),self.assertRaises(ValueError):self.go()
   p.write_text(old)
 def test_synthetic_revision_only_normalization_fixture(self):
  for p in self.dist.rglob('*.html'):p.write_text(p.read_text().replace(self.revision,'e'*40))
  self.assertEqual(B.inspect_dist(self.dist,'e'*40)['outputFiles'],18)
 def test_metadata_or_body_injection_on_all_four_html_fails(self):
  for p in self.dist.rglob('*.html'):
   old=p.read_text()
   for tail,injection in [('</head>','<meta name="twitter:site" content="invented">'),('</body>','<a href="https://fwith.co.kr/shop/item.php?it_id=B201">상품</a>'),('</body>','<p>시설에 확인해 주세요.</p>')]:
    p.write_text(old.replace(tail,injection+tail))
    with self.subTest(path=str(p),injection=injection),self.assertRaises(ValueError):self.go()
   p.write_text(old)

class WorkflowBoundaries(unittest.TestCase):
 def test_readonly_exact_source_branch_and_historical_gate_order(self):
  s=(D.parents[1]/'.github/workflows/yeosu-policy-correction-qa.yml').read_text()
  self.assertIn('contents: read',s);self.assertNotIn('secrets.',s);self.assertNotIn('contents: write',s);self.assertNotIn('issues: write',s)
  self.assertIn('python3 control/scripts/direct-yeosu-correction/run_control_tests.py',s);self.assertIn('minimum40_correction_control_tests_required',(D/'run_control_tests.py').read_text())
  self.assertIn('persist-credentials: false',s);self.assertIn(B.BRANCH,s);self.assertIn(B.TITLE,s);self.assertIn('github.run_attempt == 1',s)
  self.assertLess(s.index('npm run build'),s.index('npm test'));self.assertLess(s.index('npm test'),s.index('write_yeosu_release_files.mjs'));self.assertLess(s.index('test_yeosu_release_output.py'),s.index('build_yeosu_release.mjs'))
  self.assertNotIn('publish.py',s);self.assertNotIn('wrangler',s);self.assertNotIn('indexnow',s.lower());self.assertIn('env -i ',s)
 def test_no_unsafe_browser_override(self):
  s=(D/'production_capture.py').read_text();self.assertIn('chromium_sandbox=True',s);self.assertNotIn('executable_path=',s);self.assertNotIn('--no-sandbox',s);self.assertNotIn('HTTPServer',s)

if __name__=='__main__':unittest.main(verbosity=2)
