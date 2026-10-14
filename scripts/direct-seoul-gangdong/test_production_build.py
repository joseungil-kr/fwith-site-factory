import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import production_build as b
from capture_checks import assert_facts

class ProductionTests(unittest.TestCase):
    def fixture(self,d):
        c=dict(schemaVersion=1,repository=b.REPOSITORY,sourceRoot=b.ROOT,sourceBranch=b.BRANCH,previewSourceRevision=b.PREDECESSOR,previewSourceManifestSha256=b.PREVIEW_MANIFEST_SHA,sourceFiles=b.SOURCE_FILES,frozenPreviewTree=b.FROZEN_PREVIEW_TREE,modifiedPaths=b.MODIFIED,addedPaths=b.ADDED,frozenInputSha256=b.INPUT_SHA,frozenRuntimeSha256=b.RUNTIME_SHA,sourceRevision='a'*40,sourceTree='b'*40)
        v=dict(schemaVersion=1,state='approved',repository=b.REPOSITORY,sourceRoot=b.ROOT,siteKey='seoul-gangdong-flower-direct',hostname=b.HOSTNAME,origin=b.ORIGIN,worker=b.WORKER,previewSourceRevision=b.PREDECESSOR,frozenInputSha256=b.INPUT_SHA,frozenRuntimeSha256=b.RUNTIME_SHA,sourceRevision=c['sourceRevision'],proof=b.output.PROOF,sitemapRoutes=b.output.ROUTES,htmlFiles=5,directoryRobots='noindex,follow',notFoundStatus=404,publicHttpVerified=False,indexNowSubmitted=False,approvals=dict(publication=True,hostBinding=True,indexNowProof=True),authorizationEvidence='https://github.com/'+b.REPOSITORY+'/blob/'+('c'*40)+'/docs/direct-seoul-gangdong/production-authorization-20261014.json')
        def save():
            raw=json.dumps(c).encode();(d/'production-source-contract.json').write_bytes(raw);v['sourceContractSha256']=b.sha(raw);(d/'production-binding.json').write_text(json.dumps(v))
        save();return c,v,save
    def test_exact_pinned_contract(self):
        with tempfile.TemporaryDirectory() as d,patch.object(b,'DIRECTORY',Path(d)):
            self.fixture(Path(d));self.assertEqual(b.load()[1]['worker'],'seoul-gangdong-flower-guide')
    def test_binding_gwanak_and_schema_changes_rejected(self):
        with tempfile.TemporaryDirectory() as d,patch.object(b,'DIRECTORY',Path(d)):
            c,v,save=self.fixture(Path(d))
            changes=[('worker','seoul-gwanak-flower-guide'),('hostname','seoul-gwanak.fwith.kr'),('origin','https://seoul-gwanak.fwith.kr'),('siteKey','seoul-gwanak-flower-direct'),('sourceRoot','site-factory/seoul-gwanak-flower'),('schemaVersion',True),('sitemapRoutes',['/']),('directoryRobots','index,follow'),('approvals',dict(publication=1,hostBinding=True,indexNowProof=True)),('publicHttpVerified',True),('authorizationEvidence','unverified'),('extra',True)]
            for key,val in changes:
                with self.subTest(key=key):
                    old=copy.deepcopy(v);v[key]=val;save()
                    with self.assertRaises(ValueError):b.load()
                    v.clear();v.update(old);save()
    def test_source_contract_hash_enforced(self):
        with tempfile.TemporaryDirectory() as d,patch.object(b,'DIRECTORY',Path(d)):
            self.fixture(Path(d));p=Path(d)/'production-source-contract.json';p.write_text(p.read_text()+' ')
            with self.assertRaises(ValueError):b.load()
    def test_source_contract_scope_changes_rejected(self):
        with tempfile.TemporaryDirectory() as d,patch.object(b,'DIRECTORY',Path(d)):
            c,v,save=self.fixture(Path(d))
            for key,val in [('sourceFiles',69),('frozenPreviewTree','f'*40),('modifiedPaths',b.MODIFIED+['src/data/gangdong-runtime.json']),('addedPaths',[]),('previewSourceRevision','d'*40),('schemaVersion',True),('sourceRevision',b.PREDECESSOR),('sourceTree','short')]:
                with self.subTest(key=key):
                    old=copy.deepcopy(c);c[key]=val;save()
                    with self.assertRaises(ValueError):b.load()
                    c.clear();c.update(old);save()
    def request(self):
        c={'sourceRevision':'a'*40};digest='b'*64
        env=dict(GITHUB_REPOSITORY=b.REPOSITORY,GITHUB_REF='refs/heads/main',GITHUB_ACTOR=b.OWNER,GITHUB_TRIGGERING_ACTOR=b.OWNER,GITHUB_RUN_ATTEMPT='1',GITHUB_EVENT_NAME='issues',GITHUB_SHA='c'*40)
        body=dict(schemaVersion=1,mode='production-build-only',source_branch=b.BRANCH,source_revision=c['sourceRevision'],expected_control_revision=env['GITHUB_SHA'],binding_sha256=digest)
        event=dict(action='opened',repository=dict(full_name=b.REPOSITORY,owner=dict(login=b.OWNER,type='User')),issue=dict(title=b.TITLE,user=dict(login=b.OWNER),body=json.dumps(body)))
        return c,digest,env,event
    def test_exact_request(self):self.assertFalse(b.select(*self.request())['publicationExecuted'])
    def test_request_env_mutations(self):
        for key,val in [('GITHUB_ACTOR','other'),('GITHUB_TRIGGERING_ACTOR','other'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_EVENT_NAME','push'),('GITHUB_SHA','short'),('GITHUB_REF','refs/heads/source'),('GITHUB_REPOSITORY','other/repo')]:
            c,d,e,v=self.request();e[key]=val
            with self.subTest(key=key),self.assertRaises(ValueError):b.select(c,d,e,v)
    def test_request_body_mutations(self):
        for key,val in [('schemaVersion',True),('mode','publish'),('source_revision','d'*40),('expected_control_revision','d'*40),('binding_sha256','d'*64),('worker','seoul-gwanak-flower-guide')]:
            c,d,e,v=self.request();body=json.loads(v['issue']['body']);body[key]=val;v['issue']['body']=json.dumps(body)
            with self.subTest(key=key),self.assertRaises(ValueError):b.select(c,d,e,v)
    def test_production_build_requires_no_credentials(self):
        env=dict(SITE_RELEASE_MODE='production',SITE_INDEXABLE='true',SITE_URL=b.ORIGIN,SITE_FACTORY_REVISION='a'*40,SITE_RELEASE_BINDING_PATH=str(b.DIRECTORY/'production-binding.json'),SITE_RELEASE_BINDING_SHA256='b'*64)
        b.environment({'sourceRevision':'a'*40},'b'*64,env)
        for key,val in [('CLOUDFLARE_API_TOKEN','TEST_ONLY'),('CLOUDFLARE_ACCOUNT_ID','TEST_ONLY'),('SITE_URL','https://seoul-gwanak.fwith.kr'),('SITE_RELEASE_BINDING_PATH','/tmp/production-binding.json'),('SITE_RELEASE_BINDING_SHA256','c'*64)]:
            with self.subTest(key=key),self.assertRaises(ValueError):b.environment({'sourceRevision':'a'*40},'b'*64,{**env,key:val})
    def test_source_wrong_revision_rejected(self):
        with patch.object(b,'load',return_value=({'sourceRevision':'a'*40,'sourceTree':'b'*40},{},'c'*64)),patch.object(b,'environment'),patch.object(b,'git',return_value=b'wrong'),self.assertRaisesRegex(ValueError,'source_revision_mismatch'):b.source('/tmp','prebuild',{})
    def test_source_wrong_tree_rejected(self):
        with patch.object(b,'load',return_value=({'sourceRevision':'a'*40,'sourceTree':'b'*40},{},'c'*64)),patch.object(b,'environment'),patch.object(b,'git',side_effect=[b'a'*40,b'wrong']),self.assertRaisesRegex(ValueError,'source_tree_mismatch'):b.source('/tmp','prebuild',{})
    def test_missing_reviewed_body_fails(self):
        with tempfile.TemporaryDirectory() as d,self.assertRaises((FileNotFoundError,ValueError)):b.equivalence(Path(d))
    def facts(self):
        return dict(url='http://127.0.0.1:1/404.html',viewport=320,scrollWidth=320,revisions=['a'*40],canonical=[],robots=['noindex,follow'],h1=['없는 페이지'],title='없는 페이지',descriptions=['다시 찾기'],banners=[],sharedImageCount=0,removedCaptionOccurrences=0,fontStatus='loaded',images=[])
    def test_production_directory_keeps_canonical_but_noindex(self):
        f=self.facts();f.update(url='http://127.0.0.1:1/regions/',canonical=[b.ORIGIN+'/regions/'],robots=['noindex,follow'])
        assert_facts(f,'/regions/',320,'http://127.0.0.1:1','a'*40,{'releaseMode':'production'})
        f['robots']=['index,follow']
        with self.assertRaises(ValueError):assert_facts(f,'/regions/',320,'http://127.0.0.1:1','a'*40,{'releaseMode':'production'})
    def test_production_404_stays_noindex(self):assert_facts(self.facts(),'/404.html',320,'http://127.0.0.1:1','a'*40,{'releaseMode':'production'})
    def test_production_404_indexing_rejected(self):
        f=self.facts();f['robots']=['index,follow']
        with self.assertRaises(ValueError):assert_facts(f,'/404.html',320,'http://127.0.0.1:1','a'*40,{'releaseMode':'production'})
    def test_unknown_capture_mode_rejected(self):
        with self.assertRaises(ValueError):assert_facts(self.facts(),'/404.html',320,'http://127.0.0.1:1','a'*40,{'releaseMode':'unknown'})
    def production_facts(self):
        f=self.facts();f.update(url='http://127.0.0.1:1/',canonical=[b.ORIGIN+'/'],robots=['index,follow'],sharedImageCount=3)
        spec={'releaseMode':'production','banners':{}}
        for kind in ['message','budget','consultation']:
            accepted={'file':kind+'.webp','alt':'꽃이랑 전화 1844-0644.'};spec['banners'][kind]=accepted
            f['banners'].append(dict(kind=kind,imageCount=1,captionCount=0,src='/images/shared-banners/'+accepted['file'],alt=accepted['alt'],naturalWidth=1774,naturalHeight=887,complete=True,width=290,height=145,visible=True,loading='lazy',decoding='async'))
        return f,spec
    def test_production_home_exact_indexable_identity(self):
        f,s=self.production_facts();assert_facts(f,'/',320,'http://127.0.0.1:1','a'*40,s)
    def test_production_home_preview_robots_rejected(self):
        f,s=self.production_facts();f['robots']=['noindex,nofollow,noarchive']
        with self.assertRaises(ValueError):assert_facts(f,'/',320,'http://127.0.0.1:1','a'*40,s)
    def test_production_home_gwanak_canonical_rejected(self):
        f,s=self.production_facts();f['canonical']=['https://seoul-gwanak.fwith.kr/']
        with self.assertRaises(ValueError):assert_facts(f,'/',320,'http://127.0.0.1:1','a'*40,s)
    def test_pinned_supported_runner_keeps_chromium_sandbox(self):
        root=Path(__file__).resolve().parents[2]
        workflow=(root/'.github/workflows/seoul-gangdong-production-build-only.yml').read_text()
        browser=(Path(__file__).resolve().parent/'browser_rendering.py').read_text()
        self.assertIn('runs-on: ubuntu-22.04',workflow);self.assertIn('chromium_sandbox=True',browser)
        for word in ['--no-sandbox','sysctl','apparmor_restrict']:
            self.assertNotIn(word,workflow);self.assertNotIn(word,browser)
    def test_workflow_never_publishes_or_uses_credentials(self):
        s=(Path(__file__).resolve().parents[2]/'.github/workflows/seoul-gangdong-production-build-only.yml').read_text()
        for word in ['secrets.','issues: write','publish.py','cloudflare/wrangler','release_mode.py']:self.assertNotIn(word,s)
        self.assertIn('export SITE_RELEASE_MODE=preview SITE_INDEXABLE=false',s);self.assertIn('npm test',s);self.assertIn('npm run test:production',s);self.assertIn('production_capture.py',s)

class ProductionCaptureFailureTests(unittest.TestCase):
    def exercise(self,browser_error=None,changed=False):
        import importlib,types
        with patch.object(b,'load',return_value=({'sourceRevision':'a'*40},{},'b'*64)):
            capture=importlib.import_module('production_capture')
        with tempfile.TemporaryDirectory() as d:
            checkout=Path(d)/'checkout';root=checkout/b.ROOT;out=Path(d)/'evidence';(root/'src/data').mkdir(parents=True)
            pages=[{'path':u} for u in capture.ROUTE_ORDER];spec={'banners':{},'removedCaption':'removed'}
            module=types.ModuleType('browser_rendering')
            def inspect(*args):
                self.assertEqual(args[-1]['releaseMode'],'production')
                if browser_error:raise ValueError(browser_error)
            module.inspect=inspect
            with patch.object(capture,'capture_inputs',return_value=(pages,spec)),patch.dict('sys.modules',{'browser_rendering':module}),patch.object(capture,'source',side_effect=[{'unchanged':True},{'unchanged':not changed}]) as check:
                if browser_error or changed:
                    with self.assertRaises(RuntimeError):capture.capture(checkout,out)
                    self.assertEqual(json.loads((out/'report.json').read_text())['status'],'machine-qa-failed')
                else:capture.capture(checkout,out)
                self.assertEqual(check.call_count,2);self.assertTrue((out/'source-after-capture.json').is_file())
                return json.loads((out/'capture-status.json').read_text())
    def test_browser_failure_rechecks_integrity(self):self.assertEqual(self.exercise('network blocked')['failures'][0]['phase'],'browser')
    def test_source_mutation_fails_after_capture(self):self.assertEqual(self.exercise(changed=True)['failures'][0]['phase'],'post-capture-integrity')
    def test_success_requires_pixel_review(self):self.assertEqual(self.exercise()['pixelReview'],'pending')

class PreservedPreviewEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.prep=Path(__file__).resolve().parents[3]
    def test_equivalence_file_digest_pinned(self):
        self.assertEqual(b.sha(b.read(b.DIRECTORY/'preview-equivalence.json')),b.PREVIEW_EQUIVALENCE_SHA)
    def test_preview_source_manifest_digest_pinned(self):
        self.assertEqual(b.sha(b.read(b.DIRECTORY/'preview-source-manifest.json')),b.PREVIEW_MANIFEST_SHA)
        self.assertEqual(len(json.loads(b.read(b.DIRECTORY/'preview-source-manifest.json'))),69)
    def test_control_output_validator_matches_source(self):
        source=self.prep/'source/candidate/scripts/gangdong_release_output.py'
        if source.exists():self.assertEqual(source.read_bytes(),(b.DIRECTORY/'production_output.py').read_bytes())
    def test_exact_equivalence_using_frozen_body_files(self):
        data=json.loads(b.read(b.DIRECTORY/'preview-equivalence.json'))
        self.assertEqual({r['path'] for r in data['htmlBodyComparisons']},set(b.output.FILES))
        self.assertEqual(len(data['staticAssetsSha256']),13)
        self.assertFalse(data['browserVerified']);self.assertIsNone(data['remoteRunId'])
    def test_altered_equivalence_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as d,patch.object(b,'DIRECTORY',Path(d)):
            (Path(d)/'preview-equivalence.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'preview_equivalence_bytes_changed'):b.equivalence(Path(d))

if __name__=='__main__':unittest.main()
