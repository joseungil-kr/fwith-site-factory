"""Offline counterexamples. No browser, provider, source build or external calls."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from threading import Thread
from functools import partial
import ast,copy,hashlib,json,os,stat,unittest,urllib.request,urllib.error,zipfile
import artifact_bind as bind
from reused import digest,compact,manifest,resolve_request,SafeServer,SafeHandler,allowed_request
from capture_checks import assert_facts,assert_focus,assert_capture_coverage,banner_kinds

HERE=Path(__file__).resolve().parent

def bindings():
    b=json.loads((HERE/'bindings.json').read_text(encoding='utf-8'))
    for key in b:
        if key.endswith('Sha256'):b[key]='d'*64
    b.update(sourceSha='a'*40,buildControlSha='b'*40,runId='123',artifactId='456')
    return b

def metadata(b):
    run=dict(id=123,head_sha=b['buildControlSha'],head_branch='main',path=bind.BUILD_WORKFLOW,status='completed',conclusion='success',run_attempt=1,event='issues',
             repository={'full_name':bind.REPOSITORY},actor={'login':'joseungil-kr'},triggering_actor={'login':'joseungil-kr'})
    artifact=dict(id=456,name='seoul-seocho-production-build-123',expired=False,digest='sha256:'+b['archiveSha256'],size_in_bytes=50,
                  workflow_run={'id':123,'head_sha':b['buildControlSha'],'head_branch':'main'})
    return run,artifact

def request_fixture():
    raw=b'exact reviewed binding bytes'
    env=dict(GITHUB_ACTIONS='true',GITHUB_REPOSITORY=bind.REPOSITORY,GITHUB_REF='refs/heads/main',GITHUB_ACTOR='joseungil-kr',
             GITHUB_TRIGGERING_ACTOR='joseungil-kr',GITHUB_RUN_ATTEMPT='1',GITHUB_SHA='a'*40,GITHUB_EVENT_NAME='issues')
    body=dict(schemaVersion=1,expected_control_revision=env['GITHUB_SHA'],bindings_sha256=digest(raw),scope='sealed-production-artifact-loopback-only')
    event={'action':'opened','repository':{'full_name':bind.REPOSITORY},'issue':{'title':bind.ISSUE_TITLE,'user':{'login':'joseungil-kr','type':'User'},'body':json.dumps(body)}}
    return env,event,raw

class BindingTests(unittest.TestCase):
    def test_complete_binding(self):self.assertEqual(bind.validate_bindings(bindings())['runId'],'123')
    def test_unfilled_template_fails(self):
        # This proposal intentionally ships an unfilled production artifact pin.
        b=bindings();b['runId']='REPLACE_ME'
        with self.assertRaises(ValueError):bind.validate_bindings(b)
    def test_wrong_scope_and_types(self):
        for key,value in [('schemaVersion',True),('sourceBranch','main'),('sourceRoot','site-factory/other'),('sourceSha','main'),('runId',123),('artifactId','0'),('archiveSha256','d'*63)]:
            with self.subTest(key=key):
                b=bindings();b[key]=value
                with self.assertRaises(ValueError):bind.validate_bindings(b)
    def test_extra_binding_key(self):
        b=bindings();b['preview']=True
        with self.assertRaises(ValueError):bind.validate_bindings(b)
    def test_valid_owner_request(self):
        env,event,raw=request_fixture();bind.verify_runner(env,event,raw)
    def test_owner_branch_attempt_and_event_guards(self):
        for key,value in [('GITHUB_ACTIONS','false'),('GITHUB_REPOSITORY','elsewhere/repo'),('GITHUB_REF','refs/heads/topic'),('GITHUB_ACTOR','other'),('GITHUB_TRIGGERING_ACTOR','other'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_EVENT_NAME','workflow_dispatch')]:
            with self.subTest(key=key):
                env,event,raw=request_fixture();env[key]=value
                with self.assertRaises(ValueError):bind.verify_runner(env,event,raw)
    def test_replayed_or_broadened_issue(self):
        for key,value in [('expected_control_revision','b'*40),('bindings_sha256','b'*64),('scope','production'),('schemaVersion',True)]:
            with self.subTest(key=key):
                env,event,raw=request_fixture();body=json.loads(event['issue']['body']);body[key]=value;event['issue']['body']=json.dumps(body)
                with self.assertRaises(ValueError):bind.verify_runner(env,event,raw)
    def test_nonowner_bot_or_edited_issue(self):
        for mutate in [lambda e:e.update(action='edited'),lambda e:e['issue']['user'].update(login='other'),lambda e:e['issue']['user'].update(type='Bot'),lambda e:e['issue'].update(title='run anything')]:
            env,event,raw=request_fixture();mutate(event)
            with self.assertRaises(ValueError):bind.verify_runner(env,event,raw)
    def test_exact_metadata(self):
        b=bindings();bind.validate_metadata(b,*metadata(b))
    def test_wrong_run_metadata(self):
        for key,value in [('id',124),('head_sha','c'*40),('head_branch','topic'),('path','.github/workflows/seoul-seocho-preview-build-only.yml'),('status','in_progress'),('conclusion','failure'),('run_attempt',2),('event','pull_request')]:
            with self.subTest(key=key):
                b=bindings();run,a=metadata(b);run[key]=value
                with self.assertRaises(ValueError):bind.validate_metadata(b,run,a)
    def test_wrong_artifact_metadata(self):
        for key,value in [('id',457),('name','seoul-seocho-preview-build-123'),('expired',True),('digest','sha256:'+'c'*64),('size_in_bytes',0),('size_in_bytes',33554433)]:
            with self.subTest(key=key,value=value):
                b=bindings();run,a=metadata(b);a[key]=value
                with self.assertRaises(ValueError):bind.validate_metadata(b,run,a)
    def test_foreign_artifact_run(self):
        b=bindings();run,a=metadata(b);a['workflow_run']['id']=124
        with self.assertRaises(ValueError):bind.validate_metadata(b,run,a)
    def test_metadata_summary_omits_unneeded_identities(self):
        b=bindings();run,a=metadata(b);run['head_commit']={'author':{'email':'do-not-retain@example.invalid'}}
        self.assertNotIn('head_commit',bind.summarize_run(run))

class ArchiveTests(unittest.TestCase):
    def archive(self,root,names):
        p=root/'artifact.zip'
        with zipfile.ZipFile(p,'w') as z:
            for name in names:
                # ZipInfo on Windows normalizes separators at construction;
                # override afterwards to preserve this malformed raw ZIP case.
                item=zipfile.ZipInfo('fixture');item.filename=name;z.writestr(item,b'fixture')
        return p
    def test_exact_release_roots(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);p=self.archive(root,['release.json','dist/index.html'])
            target=bind.extract_bound_archive(p,root/'out',digest(p.read_bytes()));self.assertEqual(set(manifest(target/'dist')),{'index.html'})
    def test_wrong_archive_digest(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);p=self.archive(root,['release.json','dist/index.html'])
            with self.assertRaises(ValueError):bind.extract_bound_archive(p,root/'out','0'*64)
            self.assertFalse((root/'out').exists())
    def test_archive_path_counterexamples(self):
        for name in ['dist/../outside.txt','/dist/index.html','dist\\index.html','dist/.env','other.txt','dist/a//b','dist/./index.html']:
            with self.subTest(name=name),TemporaryDirectory() as tmp:
                root=Path(tmp);p=self.archive(root,['release.json',name])
                with self.assertRaises(ValueError):bind.extract_bound_archive(p,root/'out',digest(p.read_bytes()))
                self.assertFalse((root/'out').exists())
    def test_symlink_archive_rejected(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'artifact.zip';link=zipfile.ZipInfo('dist/link');link.create_system=3;link.external_attr=(stat.S_IFLNK|0o777)<<16
            with zipfile.ZipFile(p,'w') as z:z.writestr('release.json','{}');z.writestr(link,'../../outside')
            with self.assertRaises(ValueError):bind.extract_bound_archive(p,root/'out',digest(p.read_bytes()))
    def test_existing_destination_not_overwritten(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);p=self.archive(root,['release.json','dist/index.html']);(root/'out').mkdir();sentinel=root/'out/keep';sentinel.write_bytes(b'preserve')
            with self.assertRaises(ValueError):bind.extract_bound_archive(p,root/'out',digest(p.read_bytes()))
            self.assertEqual(sentinel.read_bytes(),b'preserve')

class LoopbackTests(unittest.TestCase):
    def test_request_allowlist(self):
        origin='http://127.0.0.1:54321'
        self.assertTrue(allowed_request(origin+'/regions/','GET',origin));self.assertTrue(allowed_request(origin+'/','HEAD',origin))
        for url,method in [(origin+'/','POST'),('https://seoul-seocho.fwith.kr/','GET'),('http://localhost:54321/','GET'),('http://127.0.0.1:54322/','GET'),('http://user@127.0.0.1:54321/','GET'),('file:///etc/passwd','GET'),('https://127.0.0.1:54321/','GET')]:
            self.assertFalse(allowed_request(url,method,origin),(url,method))
    def test_path_resolution_and_no_listing(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'index.html').write_bytes(b'only artifact');(root/'empty').mkdir()
            self.assertEqual(resolve_request(root,'/'),root/'index.html')
            for path in ['/../secret','/%2e%2e/secret','/.env','/%5csecret','https://example.invalid/a']:
                with self.assertRaises(ValueError):resolve_request(root,path)
            with self.assertRaises(FileNotFoundError):resolve_request(root,'/empty/')
    def test_loopback_bind_only(self):
        with self.assertRaises(AssertionError):SafeServer(('0.0.0.0',0),SafeHandler)
    def test_actual_server_only_serves_fixture_dist(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'index.html').write_bytes(b'fixture-dist');(root/'empty').mkdir()
            server=SafeServer(('127.0.0.1',0),partial(SafeHandler,directory=str(root)));Thread(target=server.serve_forever,daemon=True).start()
            try:
                origin=f'http://127.0.0.1:{server.server_port}'
                try:
                    with urllib.request.urlopen(origin+'/',timeout=2) as r:self.assertEqual(r.read(),b'fixture-dist')
                except urllib.error.URLError as exc:
                    if os.name=='nt' and isinstance(exc.reason,PermissionError) and exc.reason.winerror==10013:
                        self.skipTest('Windows sandbox denied loopback socket; mandatory unskipped on Linux runner')
                    raise
                for url,method,status in [('/empty/','GET',404),('/../secret','GET',403),('/','POST',405)]:
                    with self.assertRaises(urllib.error.HTTPError) as ctx:urllib.request.urlopen(urllib.request.Request(origin+url,method=method),timeout=2)
                    self.assertEqual(ctx.exception.code,status)
            finally:server.shutdown();server.server_close()

def facts_fixture(route='/regions/'):
    return dict(url='http://127.0.0.1:54321'+route,viewport=320,scrollWidth=320,revisions=['a'*40],canonical=[bind.ORIGIN+route],robots=['noindex,follow'],
                h1=['fixture'],title='fixture',descriptions=['fixture'],sharedImageCount=0,banners=[],removedCaptionOccurrences=0,fontStatus='loaded',images=[])

class CaptureTests(unittest.TestCase):
    def test_fixed_grid_and_thin_routes(self):
        self.assertEqual(bind.VIEWPORTS,[(320,740),(390,844),(1280,900)])
        self.assertEqual(len(bind.ROUTES),5);self.assertEqual(banner_kinds('/regions/'),[]);self.assertEqual(banner_kinds('/404.html'),[])
    def test_thin_directory_has_no_fake_banners(self):
        spec=json.loads((HERE/'ui-spec.json').read_text(encoding='utf-8'));f=facts_fixture()
        assert_facts(f,'/regions/',320,'http://127.0.0.1:54321','a'*40,spec)
        f['sharedImageCount']=1
        with self.assertRaises(ValueError):assert_facts(f,'/regions/',320,'http://127.0.0.1:54321','a'*40,spec)
    def test_render_metadata_and_loaded_images(self):
        spec=json.loads((HERE/'ui-spec.json').read_text(encoding='utf-8'))
        for key,value in [('scrollWidth',330),('revisions',['b'*40]),('canonical',['https://wrong.invalid/regions/']),('robots',['index,follow']),('removedCaptionOccurrences',1),('fontStatus','loading'),('images',[{'complete':False,'width':0,'height':0,'alt':'x'}])]:
            with self.subTest(key=key):
                f=facts_fixture();f[key]=value
                with self.assertRaises(ValueError):assert_facts(f,'/regions/',320,'http://127.0.0.1:54321','a'*40,spec)
    def test_focus_clipping_and_overlay_counterexamples(self):
        f=dict(viewportWidth=320,viewportHeight=740,visible=True,width=288,height=144,left=16,right=304,top=200,bottom=344,safeTop=64,safeBottom=680,hitTests=[True]*9)
        assert_focus(f,320,740)
        for key,value in [('top',63),('bottom',681),('right',321),('left',-1),('hitTests',[True]*8+[False]),('visible',False)]:
            bad={**f,key:value}
            with self.assertRaises(ValueError):assert_focus(bad,320,740)
    def test_missing_route_viewport_fails(self):
        with self.assertRaises(ValueError):assert_capture_coverage([],bind.ROUTES,Path('.'))
    def test_missing_full_or_focus_fails(self):
        rows=[{'route':r,'width':w,'height':h,'banners':[]} for w,h in bind.VIEWPORTS for r in bind.ROUTES]
        with self.assertRaises(ValueError):assert_capture_coverage(rows,bind.ROUTES,Path('.'))
    def test_exact_42_file_coverage_then_byte_mutation(self):
        # Synthetic unit-fixture bytes test identity only, never a pixel claim.
        with TemporaryDirectory() as tmp:
            out=Path(tmp);rows=[]
            def shot(name,w,h):
                rel='screenshots/'+name+'.jpg';path=out/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(json.dumps({'width':w,'height':h}).encode())
                return {'screenshot':rel,'screenshotSha256':digest(path.read_bytes()),'dimensions':{'width':w,'height':h}}
            for w,h in bind.VIEWPORTS:
                for n,r in enumerate(bind.ROUTES):
                    rows.append({'route':r,'width':w,'height':h,'fullPage':shot(f'{w}-{n}-full',w,h),
                                 'banners':[{'kind':k,**shot(f'{w}-{n}-{k}',w,h)} for k in banner_kinds(r)]})
            with patch('capture_checks.jpeg_dimensions',lambda raw:json.loads(raw)):
                self.assertEqual(assert_capture_coverage(rows,bind.ROUTES,out)['requiredFullAndFocusedScreenshots'],42)
                (out/rows[0]['fullPage']['screenshot']).write_bytes(b'changed')
                with self.assertRaises(ValueError):assert_capture_coverage(rows,bind.ROUTES,out)
    def test_native_first_landing_and_javascript_preserved(self):
        provenance=json.loads((HERE/'reuse-provenance.json').read_text(encoding='utf-8'));tree=ast.parse((HERE/'browser_rendering.py').read_text(encoding='utf-8'))
        strings={digest(n.value.encode()) for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
        self.assertTrue(set(provenance['preservedNativeJavaScriptSha256'])<=strings)
        anchors=[n for n in ast.walk(tree) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='anchor']
        self.assertEqual(len(anchors),1);self.assertEqual(digest(ast.dump(anchors[0],include_attributes=False).encode()),provenance['preservedNativeAnchorLoopAstSha256'])
    def test_accepted_ui_frozen_pin(self):
        s=json.loads((HERE/'ui-spec.json').read_text(encoding='utf-8'))
        self.assertEqual(s['customerCopySha256'],bind.COPY_SHA)
        self.assertEqual([p['url'] for p in s['pages']],bind.ROUTES[2:4])
        self.assertEqual(sum(len(p['facilityAnchors'])+len(p['buyerOccasionAnchors']) for p in s['pages']),4)
        self.assertEqual(set(s['banners']),{'message','budget','consultation'})

if __name__=='__main__':unittest.main()
