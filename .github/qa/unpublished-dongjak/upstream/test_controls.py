"""Offline negative tests. No browser launch or socket binding."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy, json, subprocess, unittest
import controls
from capture import assert_facts

class ControlsTest(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'dist';self.root.mkdir()
        (self.root/'index.html').write_text('home');(self.root/'regions').mkdir();(self.root/'regions/index.html').write_text('hub')
    def test_routes(self):
        for route in ['/', '/regions/', '/regions/a-b/', '/404.html']: self.assertTrue(controls.safe_route(route))
        for route in ['https://x/', '//x/', '/../', '/a?x=1', '/%2e%2e/']: self.assertFalse(controls.safe_route(route))
    def test_exact_get_head(self):
        for method in ['GET','HEAD']: self.assertTrue(controls.allowed_request('http://127.0.0.1:8911/regions/',method,'http://127.0.0.1:8911'))
    def test_external_network_methods(self):
        for url in ['https://fwith.co.kr/','http://localhost:8911/','http://127.0.0.1:8912/','file:///tmp/a','data:text/html,x','http://u:p@127.0.0.1:8911/','http://127.0.0.1.evil:8911/']:
            self.assertFalse(controls.allowed_request(url,'GET','http://127.0.0.1:8911'))
        for method in ['POST','PUT','DELETE','OPTIONS','PATCH']:
            self.assertFalse(controls.allowed_request('http://127.0.0.1:8911/',method,'http://127.0.0.1:8911'))
    def test_paths(self):
        self.assertEqual(controls.resolve_request(self.root,'/'),self.root/'index.html')
        self.assertEqual(controls.resolve_request(self.root,'/regions/?q=x'),self.root/'regions/index.html')
    def test_traversal_denied(self):
        for route in ['/../index.html','/%2e%2e/index.html','/.git/config','/a/./b','/a%5c..%5cb','/a%00b','https://evil/','//evil/']:
            with self.subTest(route=route),self.assertRaises((ValueError,UnicodeError)): controls.resolve_request(self.root,route)
    def test_missing_not_directory_listing(self):
        (self.root/'empty').mkdir()
        for route in ['/missing','/empty/']:
            with self.assertRaises(FileNotFoundError): controls.resolve_request(self.root,route)
    def test_symlink_file_denied(self):
        (self.root/'alias').symlink_to(self.root/'index.html')
        with self.assertRaises(ValueError): controls.resolve_request(self.root,'/alias')
        with self.assertRaises(AssertionError): controls.manifest(self.root)
    def test_symlink_directory_denied(self):
        (self.root/'alias').symlink_to(self.root/'regions',target_is_directory=True)
        with self.assertRaises(ValueError): controls.resolve_request(self.root,'/alias/')
    def test_manifest_changes(self):
        a=controls.manifest(self.root);(self.root/'index.html').write_text('changed')
        self.assertNotEqual(a,controls.manifest(self.root))
    def test_branch_drift(self):
        controls.validate_branch(controls.BRANCH)
        for branch in ['refs/heads/main', controls.BRANCH+'-other', 'refs/pull/1/merge']:
            with self.assertRaises(AssertionError): controls.validate_branch(branch)
    def test_capture_grid_hash_dimensions(self):
        spec={'routes':['/']}; rows=[]
        for width,height in controls.VIEWPORTS:
            rel=f'screenshots/{width}/home.jpg';file=self.root/rel;file.parent.mkdir(parents=True)
            # Minimal SOF bytes exercise metadata/hash integrity without a browser.
            data=b'\xff\xd8\xff\xc0\x00\x11\x08'+height.to_bytes(2,'big')+width.to_bytes(2,'big')+b'\x03'
            file.write_bytes(data)
            rows.append({'route':'/','width':width,'height':height,'issues':[],'screenshot':rel,'screenshotSha256':controls.digest(data),'screenshotDimensions':{'width':width,'height':height}})
        controls.validate_capture_evidence(rows,spec,self.root)
        for broken in [rows[:-1],rows[:-1]+[rows[0]], [{**rows[0],'screenshotSha256':'0'*64}]+rows[1:], [{**rows[0],'screenshotDimensions':{'width':1,'height':1}}]+rows[1:]]:
            with self.assertRaises(AssertionError): controls.validate_capture_evidence(broken,spec,self.root)
    def test_binding(self):
        spec=controls.spec_for('guro')
        with patch.dict('os.environ',{'GITHUB_SHA':'control-sha','GITHUB_RUN_ID':'123','GITHUB_RUN_ATTEMPT':'1'}):
            result=controls.run_binding(spec,{'a':'b'})
        self.assertEqual(result['sourceSha'],spec['sourceSha']);self.assertEqual(result['controlSha'],'control-sha')
        self.assertEqual(result['pixelReview'],'pending');self.assertEqual(result['publicationAuthorization'],'not-issued')
    def test_fixture_pins(self):
        specs=json.loads((controls.HERE/'sites.json').read_text())
        self.assertEqual(sum(len(s['routes'])*3 for s in specs.values()),51)
        self.assertEqual([s['productionApproved'] for s in specs.values()],[True,False,False])
        for spec in specs.values():
            self.assertRegex(spec['sourceSha'],r'^[0-9a-f]{40}$');self.assertRegex(spec['sourceTree'],r'^[0-9a-f]{40}$')

class SourceTest(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.site=self.root/'site-factory/test';(self.site/'src/data').mkdir(parents=True);(self.site/'scripts').mkdir()
        (self.site/'src/data/site-config.json').write_text(json.dumps({'productionApproved':False,'previewUrl':'https://test.example'}))
        (self.site/'src/data/pages.json').write_text('[]');(self.site/'src/data/build-revision.json').write_text('{}')
        (self.site/'scripts/qa_browser_rendering.py').write_text('# immutable native test fixture\n')
        def cmd(*args): subprocess.run(['git','-C',str(self.root),*args],check=True,capture_output=True)
        cmd('init');cmd('add','.');cmd('-c','user.name=QA fixture','-c','user.email=qa@example.invalid','commit','-m','fixture')
        self.spec={'sourceSha':controls.git(self.root,'rev-parse','HEAD'),'sourceTree':controls.git(self.root,'rev-parse','HEAD:site-factory/test'),'repositoryTree':controls.git(self.root,'rev-parse','HEAD^{tree}'),'path':'site-factory/test','productionApproved':False,'siteUrl':'https://test.example','routes':['/','/regions/','/404.html']}
        self.patch=patch.object(controls,'NATIVE_BLOB',controls.git(self.root,'rev-parse','HEAD:site-factory/test/scripts/qa_browser_rendering.py'));self.patch.start();self.addCleanup(self.patch.stop)
    def test_exact_checkout(self): controls.verify_source(self.root,self.spec,pristine=True)
    def test_wrong_sha(self):
        spec={**self.spec,'sourceSha':'0'*40}
        with self.assertRaises(AssertionError): controls.verify_source(self.root,spec)
    def test_wrong_tree(self):
        spec={**self.spec,'sourceTree':'0'*40}
        with self.assertRaises(AssertionError): controls.verify_source(self.root,spec)
    def test_guard_edit_rejected(self):
        (self.site/'scripts/qa_browser_rendering.py').write_text('changed')
        with self.assertRaises(AssertionError): controls.verify_source(self.root,self.spec)
    def test_approval_mismatch(self):
        with self.assertRaises(AssertionError): controls.verify_source(self.root,{**self.spec,'productionApproved':True})
    def test_routes_mismatch(self):
        with self.assertRaises(AssertionError): controls.verify_source(self.root,{**self.spec,'routes':['/']})
    def test_generated_revision_only_after_build(self):
        (self.site/'src/data/build-revision.json').write_text('{"revision":"new"}')
        controls.verify_source(self.root,self.spec)
        with self.assertRaises(AssertionError): controls.verify_source(self.root,self.spec,pristine=True)
    def test_untracked_pristine_rejected(self):
        (self.site/'src/data/new.json').write_text('{}')
        with self.assertRaises(AssertionError): controls.verify_source(self.root,self.spec,pristine=True)
    def test_content_mutation_rejected(self):
        # Tracked bytes are the immutable source contract; generated files are
        # not allowed to enter the served manifest unnoticed (HTML scope test).
        (self.site/'src/data/pages.json').write_text('[{"url":"/new/"}]')
        with self.assertRaises(AssertionError): controls.verify_source(self.root,self.spec)

class BrowserAssertionsTest(unittest.TestCase):
    def setUp(self):
        self.spec=controls.spec_for('guro')
        self.facts={'h1':['Title'],'viewport':320,'scrollWidth':320,'overflow':[], 'faq':[],
          'images':[{'complete':True,'width':20,'height':20,'alt':'꽃'}], 'revision':self.spec['sourceSha'],
          'canonical':self.spec['siteUrl']+'/', 'robots':'noindex,nofollow,noarchive','banners':1,
          'anchors':[{'href':'tel:18440644'},{'href':'https://fwith.co.kr'}], 'fontStatus':'loaded'}
    def test_valid_facts(self): assert_facts(self.facts,self.spec,'/',[],320)
    def test_negative_native_and_extra_semantics(self):
        mutations={'h1':[], 'scrollWidth':322,'overflow':[{}], 'faq':[{'visible':False,'collapsed':True,'question':'','answer':''}],
            'images':[{'complete':False,'width':0,'height':0,'alt':''}], 'revision':'qa-control-sha',
            'canonical':'https://wrong/','robots':'index,follow','anchors':[{'href':'tel:999'}],'fontStatus':'loading'}
        for key,value in mutations.items():
            with self.subTest(key=key),self.assertRaises(AssertionError): assert_facts({**self.facts,key:value},self.spec,'/',[],320)
    def test_404_banner_rejected(self):
        with self.assertRaises(AssertionError): assert_facts({**self.facts,'canonical':None},self.spec,'/404.html',[],320)

if __name__=='__main__': unittest.main()
