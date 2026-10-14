import copy
from email.message import Message
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import publish as p
import test_production_output as fixture_tests


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixture_tests.OutputContractTests();self.fixture.setUp()
        self.tmp=tempfile.TemporaryDirectory();self.cwd=Path(self.tmp.name)
        self.old=Path.cwd();os.chdir(self.cwd)
        self.env=patch.dict(os.environ,{'REVISION':'a'*40});self.env.start()
        shutil.copytree(self.fixture.root,Path('release/dist'))
        for file,route in p.output.FILES.items():
            if route!='/404.html':
                path=Path('release/dist')/file
                path.write_text(path.read_text().replace('</body>','<a href="tel:1844-0644">Phone</a><a href="https://fwith.co.kr/">Order</a></body>'))
        self.binding={'proof':self.fixture.proof,'sourceContractSha256':'e'*64}
        self.contract={'expectedSourceRevision':'a'*40}
        self.files=p.gate.inventory(Path('release/dist'))
        manifest=dict(schemaVersion=1,repository=p.REPOSITORY,sourceBranch=p.BRANCH,sourceRoot=p.SOURCE_ROOT,
                      revision='a'*40,controlRevision='c'*40,runId='123',origin=p.ORIGIN,worker=p.WORKER,indexable=True,
                      bindingSha256='d'*64,sourceContractSha256='e'*64,files=self.files)
        p.save('release/release.json',manifest)
        self.review={'buildControlSha':'c'*40,'buildRunId':'123','artifactId':'456','qaRunId':'789',
                     'releaseManifestSha256':p.sha(Path('release/release.json').read_bytes()),
                     'outputFilesSha256':p.sha(json.dumps(self.files,sort_keys=True,separators=(',',':')).encode())}
        self.load=patch.object(p.gate,'load',return_value=(self.contract,self.binding,'d'*64));self.load.start()
        self.review_patch=patch.object(p,'release_review',return_value=self.review);self.review_patch.start()
    def tearDown(self):
        self.review_patch.stop();self.load.stop();self.env.stop();os.chdir(self.old);self.tmp.cleanup();self.fixture.tearDown()
    def headers(self,mime):
        h=Message();h['Content-Type']=mime;return h
    def transport(self,path,status=200):
        root=Path('release/dist')
        if status==404:return (root/'404.html').read_bytes(),self.headers('text/html; charset=utf-8')
        file=path.lstrip('/')+('index.html' if path.endswith('/') else '')
        return (root/file).read_bytes(),self.headers('text/html' if file.endswith('.html') else 'text/plain')
    def test_exact_five_html_three_sitemap_and_route_less_config(self):
        r=p.artifact();self.assertEqual((r['htmlFiles'],r['sitemapUrls'],r['noindexHubs']),(5,3,1))
        config=json.loads(Path('release/wrangler.publish.json').read_text())
        self.assertEqual(set(config),{'name','compatibility_date','workers_dev','assets'})
        self.assertFalse(config['workers_dev']);self.assertEqual(config['name'],'seoul-seocho-flower-guide')
        self.assertEqual(config['assets']['not_found_handling'],'404-page')
    def test_wrangler_runtime_files_do_not_relax_sealed_artifact_contract(self):
        self.assertEqual(p.artifact()['htmlFiles'],5)
        files=p.gate.inventory(Path('release/dist'))
        # Wrangler 4.148.0 tmp cleanup retains .wrangler/tmp; independently
        # reproduced with the exact pinned upstream function bodies.
        runtime=Path('release/.wrangler/tmp');runtime.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError,'^unexpected_release_files$'):p.artifact()
        cleanup=runtime.parent.resolve()
        self.assertTrue(cleanup.is_relative_to(self.cwd.resolve()) and cleanup.name=='.wrangler')
        shutil.rmtree(cleanup)
        (self.cwd/'isolated-wrangler/.wrangler/tmp').mkdir(parents=True)
        self.assertEqual(p.artifact()['htmlFiles'],5)
        self.assertEqual(p.gate.inventory(Path('release/dist')),files)
        rogue=Path('release/UNEXPECTED.txt');rogue.write_text('offline regression')
        with self.assertRaisesRegex(ValueError,'^unexpected_release_files$'):p.artifact()
        rogue.unlink()
        self.assertEqual(p.gate.inventory(Path('release/dist')),files)
    def test_workflow_runs_wrangler_outside_immutable_release(self):
        root=Path(__file__).resolve().parents[2]
        workflow=(root/'.github/workflows/seoul-seocho-production-publish.yml').read_text()
        deploy=workflow.split('      - name: Deploy fixed route-less static assets once\n',1)[1].split('      - name:',1)[0]
        self.assertNotIn('working-directory: release',deploy)
        self.assertIn('mktemp -d "$RUNNER_TEMP/seocho-wrangler.XXXXXX"',deploy)
        self.assertIn('cd "$wrangler_workdir"',deploy)
        self.assertIn('wrangler@4.148.0 deploy --config "$GITHUB_WORKSPACE/release/wrangler.publish.json"',deploy)
    def test_manifest_changed_rejected(self):
        q=Path('release/release.json');q.write_bytes(q.read_bytes()+b' ')
        with self.assertRaises(ValueError):p.artifact()
    def test_bytes_changed_rejected(self):
        q=Path('release/dist/index.html');q.write_bytes(q.read_bytes()+b' ')
        with self.assertRaises(ValueError):p.artifact()
    def reseal_fixture(self):
        manifest=json.loads(Path('release/release.json').read_text())
        manifest['files']=p.gate.inventory(Path('release/dist'))
        p.save('release/release.json',manifest)
        self.review['releaseManifestSha256']=p.sha(Path('release/release.json').read_bytes())
        self.review['outputFilesSha256']=p.sha(json.dumps(manifest['files'],sort_keys=True,separators=(',',':')).encode())
    def test_artifact_requires_preserved_seocho_ctas_even_when_hashes_match(self):
        substitutions=[(b'tel:1844-0644',b'tel:18440644'),(b'https://fwith.co.kr/',b'https://fwith.co.kr')]
        for file,route in p.output.FILES.items():
            if route=='/404.html':continue
            path=Path('release/dist')/file;original=path.read_bytes()
            for correct,wrong in substitutions:
                with self.subTest(route=route,wrong=wrong):
                    self.assertIn(correct,original)
                    path.write_bytes(original.replace(correct,wrong));self.reseal_fixture()
                    with self.assertRaisesRegex(ValueError,'^cta_mismatch$'):p.artifact()
                    path.write_bytes(original);self.reseal_fixture()
        self.assertEqual(p.artifact()['htmlFiles'],5)
    def test_live_requires_preserved_seocho_ctas_on_each_customer_route(self):
        p.artifact();contract=json.loads(Path('http-contract.json').read_text())
        substitutions=[(b'tel:1844-0644',b'tel:18440644'),(b'https://fwith.co.kr/',b'https://fwith.co.kr')]
        for route in sorted(p.ROUTES):
            for correct,wrong in substitutions:
                def altered(path,status=200):
                    data,headers=self.transport(path,status)
                    return (data.replace(correct,wrong) if path==route else data),headers
                with self.subTest(route=route,wrong=wrong),patch.object(p,'get',side_effect=altered):
                    with self.assertRaisesRegex(ValueError,'^live_cta_mismatch$'):p.http_once(contract)
    def test_artifact_cannot_execute_source_or_route_files(self):
        for name in ['_worker.js','_routes.json','_redirects','package.json','wrangler.toml']:
            q=Path('release/dist')/name;q.write_text('test')
            with self.assertRaises(ValueError):p.artifact()
            q.unlink()
    def test_exact_public_bytes_thin_noindex_and_real404(self):
        p.artifact();c=json.loads(Path('http-contract.json').read_text())
        self.assertNotIn(p.ORIGIN+'/regions/',c['sitemapUrls'])
        with patch.object(p,'get',side_effect=self.transport):
            r=p.http_once(c);self.assertEqual(r['sitemapUrls'],3)
        self.assertEqual(next(x['robots'] for x in c['pages'] if x['path']=='/regions/'),['follow','noindex'])
    def test_live_extra_bytes_rejected_without_verified_beacon(self):
        p.artifact();c=json.loads(Path('http-contract.json').read_text())
        def changed(path,status=200):
            data,headers=self.transport(path,status)
            return data+(b' ' if path=='/' else b''),headers
        with patch.object(p,'get',side_effect=changed),self.assertRaises((ValueError,AssertionError)):p.http_once(c)
    def test_verified_beacon_only_restores_exact_public_and404_bytes(self):
        p.artifact();c=json.loads(Path('http-contract.json').read_text())
        beacon=b'<script defer src="https://static.cloudflareinsights.com/beacon.min.js/v1" data-cf-beacon="{}"></script>'
        def injected(path,status=200):
            data,headers=self.transport(path,status)
            if path.endswith('/') or status==404:data=data.replace(b'</body>',beacon+b'</body>')
            return data,headers
        with patch.object(p,'get',side_effect=injected):
            self.assertEqual(p.http_once(c)['normalizedCloudflareBeacons'],5)
    def test_cloudflare_beacon_only_normalization(self):
        expected=b'<html><body>Exact content</body></html>'
        beacon=b'<script defer src="https://static.cloudflareinsights.com/beacon.min.js/v1" data-cf-beacon="{}"></script>'
        body=expected.replace(b'</body>',beacon+b'</body>')
        self.assertEqual(p.strip_one_cf_beacon(body,p.sha(expected)),expected)
        invalid=[body.replace(b'Exact',b'Changed'),body.replace(beacon,beacon+beacon),
                 body.replace(b'></script>',b'>alert(1)</script>'),
                 body.replace(b'static.cloudflareinsights.com',b'foreign.example.com'),
                 body.replace(b' defer ',b' src="https://evil.example/x.js" defer '),
                 body.replace(b' defer ',b' onclick="alert(1)" defer '),
                 body.replace(b'/v1"',b'/v1?query=yes"'),
                 body.replace(b'></script>',b'/>')]
        for changed in invalid:
            with self.subTest(changed=changed),self.assertRaises(AssertionError):
                p.strip_one_cf_beacon(changed,p.sha(expected))
    def test_soft404_or_wrong404_bytes_rejected(self):
        p.artifact();c=json.loads(Path('http-contract.json').read_text())
        def soft(path,status=200):
            if status==404:return (Path('release/dist')/'index.html').read_bytes(),self.headers('text/html')
            return self.transport(path,status)
        with patch.object(p,'get',side_effect=soft),self.assertRaises(ValueError):p.http_once(c)
    def test_missing_manual_review_descriptor_blocks(self):
        self.review_patch.stop()
        try:
            with self.assertRaises((ValueError,FileNotFoundError)):p.release_review()
        finally:self.review_patch.start()
    def test_provider_collision_and_inventory_reads_only(self):
        account='1'*32;calls=[]
        def single(t,path):return t('GET',path)['result']
        def run(scripts,domains,stage='preflight'):
            def transport(method,path,body=None):
                calls.append((method,path,body))
                if path.endswith('/workers/scripts'):return {'result':[{'id':x} for x in scripts]}
                if path.endswith('/workers/domains'):return {'result':domains}
                return {'result':{'id':account}}
            with patch.object(p,'helpers',return_value=(None,single)):return p.inspect_provider(account,transport,stage)
        self.assertEqual(run([],[])['state'],'target_absent_verified')
        self.assertTrue(all(method=='GET' and body is None for method,path,body in calls))
        with self.assertRaises(ValueError):run([p.WORKER],[])
        with self.assertRaises(ValueError):run(['other'],[{'hostname':p.HOSTNAME,'service':'other'}])
        with self.assertRaises(ValueError):run([p.WORKER],[{'hostname':'other.fwith.kr','service':p.WORKER}])
        self.assertEqual(run([p.WORKER],[{'hostname':p.HOSTNAME,'service':p.WORKER}],'readback')['state'],'binding_verified')
    def test_fixed_provider_write_and_journal_contract_in_source(self):
        source=Path(p.__file__).read_text()
        self.assertIn('override_scope=False, override_existing_origin=False, override_existing_dns_record=False',source)
        self.assertEqual(p.RECEIPT_ISSUE,266)
        self.assertIn('Journal(REPOSITORY, RECEIPT_ISSUE)',source)
        self.assertIn('strip_one_cf_beacon',source)
        workflow=Path(p.__file__).resolve().parents[2]/'.github/workflows/seoul-seocho-production-publish.yml'
        text=workflow.read_text();self.assertNotIn('path: target',text)
        self.assertIn('run_id: Number(process.env.BUILD_RUN_ID)',text)
        self.assertIn('run.run_attempt !== 1',text)
        self.assertIn("steps.attach.outcome == 'success'",text)

if __name__=='__main__':unittest.main()
