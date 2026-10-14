import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import preview_qa as q
from capture_checks import banner_kinds, assert_facts, assert_capture_coverage
from reused import allowed_request, resolve_request, manifest


def env():
    return {'GITHUB_REPOSITORY':q.REPOSITORY,'GITHUB_REF':'refs/heads/main','GITHUB_ACTOR':q.OWNER,
            'GITHUB_TRIGGERING_ACTOR':q.OWNER,'GITHUB_RUN_ATTEMPT':'1','GITHUB_EVENT_NAME':'issues','GITHUB_SHA':'a'*40,
            'SITE_FACTORY_REVISION':q.REVISION,'SITE_INDEXABLE':'false','SITE_URL':q.ORIGIN,'SITE_RELEASE_MODE':'preview'}


def event():
    return {'action':'opened','repository':{'full_name':q.REPOSITORY,'owner':{'login':q.OWNER,'type':'User'}},
            'issue':{'title':q.TITLE,'user':{'login':q.OWNER},'body':json.dumps({'schemaVersion':1,'source_branch':q.BRANCH,
             'source_revision':q.REVISION,'expected_control_revision':'a'*40,'mode':'preview-only'})}}


def html(route,revision=q.REVISION):
    canonical='' if route is None else f'<link rel="canonical" href="{q.ORIGIN}{route}">'
    return f'<html><head>{canonical}<meta name="robots" content="noindex,nofollow,noarchive"><meta name="site-factory-revision" content="{revision}"></head><body><h1>강남</h1></body></html>'


def fixture(root):
    for name,route in q.ROUTES.items():
        f=root/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(html(route))
    (root/'robots.txt').write_text('User-agent: *\nDisallow: /\n')
    (root/'_headers').write_text('/*\n  X-Robots-Tag: noindex, nofollow, noarchive\n')
    for i in range(13):(root/f'asset-{i}.css').write_text('/* static */')


class RequestTests(unittest.TestCase):
    def test_exact_request(self):self.assertEqual(q.select(env(),event())['sourceRevision'],q.REVISION)
    def test_environment_identity_changes_rejected(self):
        for key,value in [('GITHUB_REPOSITORY','other/repo'),('GITHUB_REF','refs/heads/other'),('GITHUB_ACTOR','other'),('GITHUB_TRIGGERING_ACTOR','other'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_EVENT_NAME','push'),('GITHUB_SHA','bad')]:
            with self.subTest(key=key):
                e=env();e[key]=value
                with self.assertRaises(ValueError):q.select(e,event())
    def test_event_identity_changes_rejected(self):
        for kind in ['action','repo','owner','owner_type','title','user','body']:
            e=event()
            if kind=='action':e['action']='reopened'
            elif kind=='repo':e['repository']['full_name']='other/repo'
            elif kind=='owner':e['repository']['owner']['login']='other'
            elif kind=='owner_type':e['repository']['owner']['type']='Organization'
            elif kind=='title':e['issue']['title']='[SEOCHO-PREVIEW-BUILD] 20261014'
            elif kind=='user':e['issue']['user']['login']='other'
            else:e['issue']['body']='x'*2048
            with self.subTest(kind=kind),self.assertRaises(ValueError):q.select(env(),e)
    def test_body_contract_changes_rejected(self):
        for key,value in [('schemaVersion',True),('source_branch','source/other'),('source_revision','a'*40),('expected_control_revision','b'*40),('mode','production'),('worker','seoul-gwanak-flower-guide')]:
            e=event();b=json.loads(e['issue']['body']);b[key]=value;e['issue']['body']=json.dumps(b)
            with self.subTest(key=key),self.assertRaises(ValueError):q.select(env(),e)
    def test_preview_environment(self):q.preview_environment(env())
    def test_production_or_binding_environment_rejected(self):
        for key,value in [('SITE_FACTORY_REVISION','a'*40),('SITE_INDEXABLE','true'),('SITE_URL','https://seoul-gwanak.fwith.kr'),('SITE_RELEASE_MODE','production'),('SITE_RELEASE_BINDING_PATH','approval.json'),('SITE_RELEASE_BINDING_SHA256','a'*64)]:
            e=env();e[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):q.preview_environment(e)


class OutputTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);fixture(self.root)
    def tearDown(self):self.tmp.cleanup()
    def test_exact_output(self):self.assertEqual(q.output(self.root)['htmlFiles'],6)
    def test_no_public_or_pixel_success_claim(self):
        out=q.output(self.root)
        self.assertFalse(out['browserVerified']);self.assertFalse(out['publicationAuthorized']);self.assertFalse(out['publicHTTPVerified'])
    def test_wrong_canonical(self):
        f=self.root/'index.html';f.write_text(f.read_text().replace(q.ORIGIN,'https://seoul-gwanak.fwith.kr'))
        with self.assertRaises(ValueError):q.output(self.root)
    def test_indexable_html(self):
        f=self.root/'index.html';f.write_text(f.read_text().replace('noindex,nofollow,noarchive','index,follow'))
        with self.assertRaises(ValueError):q.output(self.root)
    def test_wrong_revision(self):
        (self.root/'index.html').write_text(html('/','a'*40))
        with self.assertRaises(ValueError):q.output(self.root)
    def test_duplicate_headings(self):
        f=self.root/'index.html';f.write_text(f.read_text()+'<h1>extra</h1>')
        with self.assertRaises(ValueError):q.output(self.root)
    def test_duplicate_attribute(self):
        f=self.root/'index.html';f.write_text(f.read_text().replace('name="robots"','name="robots" name="robots"'))
        with self.assertRaises(ValueError):q.output(self.root)
    def test_404_canonical_forbidden(self):
        (self.root/'404.html').write_text(html('/404.html'))
        with self.assertRaises(ValueError):q.output(self.root)
    def test_missing_file(self):
        (self.root/'asset-0.css').unlink()
        with self.assertRaises(ValueError):q.output(self.root)
    def test_sitemap_forbidden(self):
        (self.root/'asset-0.css').rename(self.root/'sitemap.xml')
        with self.assertRaises(ValueError):q.output(self.root)
    def test_executable_forbidden(self):
        (self.root/'asset-0.css').rename(self.root/'_worker.js')
        with self.assertRaises(ValueError):q.output(self.root)
    def test_robots_must_disallow(self):
        (self.root/'robots.txt').write_text('User-agent: *\nAllow: /\n')
        with self.assertRaises(ValueError):q.output(self.root)
    def test_noindex_header_required(self):
        (self.root/'_headers').write_text('/*\n')
        with self.assertRaises(ValueError):q.output(self.root)
    def test_symlink_rejected(self):
        f=self.root/'asset-0.css';f.unlink();f.symlink_to(self.root/'asset-1.css')
        with self.assertRaises(ValueError):q.output(self.root)


class SourceTests(unittest.TestCase):
    def test_wrong_commit_rejected_before_files(self):
        with patch.object(q,'git',return_value=('a'*40+'\n').encode()),self.assertRaisesRegex(ValueError,'checkout_revision_mismatch'):q.source('/tmp','prebuild',env())
    def test_wrong_tree_rejected_before_files(self):
        with patch.object(q,'git',side_effect=[(q.REVISION+'\n').encode(),('a'*40+'\n').encode()]),self.assertRaisesRegex(ValueError,'source_tree_mismatch'):q.source('/tmp','prebuild',env())
    def test_empty_inventory_rejected(self):
        with patch.object(q,'git',side_effect=[(q.REVISION+'\n').encode(),(q.TREE+'\n').encode(),b'']),self.assertRaisesRegex(ValueError,'frozen_source_count_mismatch'):q.source('/tmp','prebuild',env())
    def test_bad_mode_rejected(self):
        entries=('120000 blob '+'a'*40+'\t'+q.ROOT+'/malicious\0').encode()
        with patch.object(q,'git',side_effect=[q.REVISION.encode(),q.TREE.encode(),entries]),self.assertRaisesRegex(ValueError,'unexpected_source_entry'):q.source('/tmp','prebuild',env())
    def test_tracked_mutation_rejected(self):
        entries=('100644 blob '+'a'*40+'\t'+q.ROOT+'/package.json\0').encode()
        with patch.object(q,'git',side_effect=[q.REVISION.encode(),q.TREE.encode(),entries]),patch.object(q,'read',return_value=b'changed'),self.assertRaisesRegex(ValueError,'tracked_source_changed'):q.source('/tmp','prebuild',env())
    def test_generated_revision_must_be_exact(self):
        entries=('100644 blob '+'a'*40+'\t'+q.ROOT+'/src/data/build-revision.json\0').encode()
        with patch.object(q,'git',side_effect=[q.REVISION.encode(),q.TREE.encode(),entries]),patch.object(q,'read',return_value=b'{"revision":"local"}'),self.assertRaisesRegex(ValueError,'generated_revision_mismatch'):q.source('/tmp','postbuild',env())


class BrowserBoundaryTests(unittest.TestCase):
    def test_loopback_get_allowed(self):self.assertTrue(allowed_request('http://127.0.0.1:1234/index.html','GET','http://127.0.0.1:1234'))
    def test_external_and_mutating_requests_blocked(self):
        for url,method in [('https://seoul-gangnam.fwith.kr/','GET'),('http://localhost:1234/','GET'),('http://127.0.0.1:5678/','GET'),('http://127.0.0.1:1234/','POST'),('http://user@127.0.0.1:1234/','GET'),('https://127.0.0.1:1234/','GET')]:
            with self.subTest(url=url,method=method):self.assertFalse(allowed_request(url,method,'http://127.0.0.1:1234'))
    def test_directory_has_three_banners(self):self.assertEqual(banner_kinds('/regions/'),['message','budget','consultation'])
    def test_404_has_no_banners(self):self.assertEqual(banner_kinds('/404.html'),[])
    def test_exact_18_capture_pairs_required(self):
        with tempfile.TemporaryDirectory() as d,self.assertRaises(ValueError):assert_capture_coverage([],q.ROUTE_ORDER,Path(d))
    def test_server_path_traversal_forbidden(self):
        with tempfile.TemporaryDirectory() as d:
            for p in ['/../secret','/%2e%2e/secret','/.git/config','/a\\b','https://external/a']:
                with self.subTest(path=p),self.assertRaises(ValueError):resolve_request(Path(d),p)
    def test_server_missing_route_is_missing(self):
        with tempfile.TemporaryDirectory() as d,self.assertRaises(FileNotFoundError):resolve_request(Path(d),'/missing')
    def test_manifest_symlink_forbidden(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'a').write_text('x');(p/'b').symlink_to(p/'a')
            with self.assertRaises(AssertionError):manifest(p)


class CaptureFailureTests(unittest.TestCase):
    def exercise(self,browser_error=None,changed=False):
        import types
        import capture
        with tempfile.TemporaryDirectory() as d:
            checkout=Path(d)/'checkout';root=checkout/q.ROOT;out=Path(d)/'evidence';(root/'src/data').mkdir(parents=True)
            (root/'src/data/pages.json').write_text(json.dumps([{'url':u} for u in q.ROUTE_ORDER[2:-1]]))
            (root/'src/data/common-banner-phone-amendment.json').write_text(json.dumps({'assets':{},'removedVisibleCaption':'removed'}))
            module=types.ModuleType('browser_rendering')
            def inspect(*args):
                if browser_error:raise ValueError(browser_error)
            module.inspect=inspect
            results=[{'unchanged':True},{'unchanged':not changed}]
            with patch.dict('sys.modules',{'browser_rendering':module}),patch.object(capture,'source',side_effect=results) as check:
                if browser_error or changed:
                    with self.assertRaises(RuntimeError):capture.capture(checkout,out)
                    report=json.loads((out/'report.json').read_text());self.assertEqual(report['status'],'machine-qa-failed')
                else:capture.capture(checkout,out)
                self.assertEqual(check.call_count,2)
                self.assertTrue((out/'source-after-capture.json').is_file())
                return json.loads((out/'capture-status.json').read_text())
    def test_failed_browser_still_checks_source(self):self.assertEqual(self.exercise('network blocked')['failures'][0]['phase'],'browser')
    def test_mutation_failure_is_recorded(self):self.assertEqual(self.exercise(changed=True)['failures'][0]['phase'],'post-capture-integrity')
    def test_success_keeps_pixel_review_pending(self):self.assertEqual(self.exercise()['pixelReview'],'pending')


class AccessibilityRegressionTests(unittest.TestCase):
    layout='<main id="main-content" tabindex="-1">'
    css='@media(min-width:861px){html{scroll-padding-block-start:83px}}'
    def test_exact_fix(self):q.accessibility_contract(self.layout,self.css)
    def test_missing_tabindex_rejected(self):
        with self.assertRaises(ValueError):q.accessibility_contract('<main id="main-content">',self.css)
    def test_positive_tabindex_rejected(self):
        with self.assertRaises(ValueError):q.accessibility_contract(self.layout.replace('-1','1'),self.css)
    def test_mobile_only_clearance_rejected(self):
        with self.assertRaises(ValueError):q.accessibility_contract(self.layout,self.css.replace('min-width:861px','max-width:860px'))


if __name__=='__main__':unittest.main()
