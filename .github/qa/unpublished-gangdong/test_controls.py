"""Offline unit/negative fixtures. Synthetic JPEG headers are NOT captured screenshots.
No browser, dependency installation, remote access, source writes or Git writes.
"""
from pathlib import Path
from unittest.mock import patch
import copy, json, os, shutil, struct, tempfile, unittest
import adapter as a
from artifact_receipt import receipt

SPEC=a.load(a.SPEC_PATH)
SITE=Path(os.environ.get('GANGDONG_TEST_SITE',str(Path(os.environ.get('SOURCE_ROOT','/missing'))/a.SITE_PATH))).absolute()

def synthetic_jpeg(w,h):
    # Header-only parser fixture, deliberately never named as real browser evidence.
    return b'\xff\xd8\xff\xc0'+struct.pack('>H',17)+b'\x08'+struct.pack('>HH',h,w)+b'\x03'+b'\x01\x11\x00\x02\x11\x00\x03\x11\x00'+b'\xff\xd9'

def geometry(w,h,index=0):
    return {'visible':True,'width':100,'height':20,'left':20,'right':120,'top':120,'bottom':140,'safeTop':80,'safeBottom':h-70,'viewportWidth':w,'viewportHeight':h,'hitTests':[True]*9,'focusVisible':True,'outlineWidth':3,'outlineStyle':'solid','domIndex':index}

def fixture_facts(runtime,route,width):
    p,products=a.expected_for(runtime,route)
    def img(src,alt,w,h):return {'src':src,'alt':alt,'complete':True,'naturalWidth':w,'naturalHeight':h,'width':100,'height':100*h/w,'objectFit':'contain'}
    banners=[]
    for placement in p['bannerPlacement']:
        b=next(x for x in runtime['common']['banners']if x['id']==placement['banner'])
        banners.append({'variant':b['id'],**img('/images/shared-banners/'+b['assetName'],b['alt'],1774,887)})
    products=[{'sku':p['sku'],'family':p['family'],'href':p['cta']['href'],'name':p['name'],'price':p['priceText'],'description':p['description'],'sampleLabel':runtime['common']['productLabels']['samplePhoto'],'descriptionVisible':True,'sampleLabelVisible':True,**img(p['img'],p['alt'],500,500)}for p in products]
    return {'h1':[p['h1']],'title':p['title'],'description':p['metaDescription'],'firstAnswer':p['firstAnswer'],'viewport':width,'scrollWidth':width,'overflow':[],'robots':'noindex,nofollow,noarchive','canonical':None if route=='/404.html'else a.ORIGIN+route,'pageId':p['id'],'copySha':runtime['inputSHA256'],'duplicateIds':[],'fontStatus':'loaded','faq':[{**f,'visible':True,'collapsed':False}for f in p.get('faqs',[])],'images':[dict(x)for x in banners+products],'banners':banners,'products':products,'sources':p.get('officialSources',[]),'sourceSectionCount':int(bool(p.get('officialSources'))),'sourceNote':p.get('sourceNote',''),'ids':runtime['presentation']['requiredAnchors'].get(route,[]),'phones':[runtime['common']['phone']['href']],'fixedBar':width<=860,'links':a.dom_contract()[route]['links']}

def fixture_report(output,runtime):
    def screen(route,w,h,label,full=False):
        slug='home'if route=='/'else route.strip('/').replace('/','--').replace('.','-')
        rel=f'screenshots/{w}/{slug}/{label}.jpg';data=synthetic_jpeg(w,h);p=output/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        return {'route':route,'width':w,'height':h,'label':label,'kind':'full-page'if full else'risk-viewport','screenshot':rel,'sha256':a.digest(data),'dimensions':{'width':w,'height':h},'issues':[]}
    rows=[]
    for w,h in a.VIEWPORTS:
        for route in a.ROUTES:
            menu={'passed':True,'mode':'desktop-navigation'}
            if w<=860:menu={'passed':True,'mode':'native-details','clickOpenClose':True,'keyboardEnterSpace':True,'navigationBackReload':True,'navigationForward':True,'screenshot':screen(route,w,h,'menu-open')}
            targets=[{**screen(route,w,h,label),'geometry':geometry(w,h),'geometryPassed':True,'selector':selector,'index':index}for label,(selector,index)in a.targets_for(runtime,route).items()]
            focus=a.dom_contract()[route]['keyboard'][str(w)]
            links=sorted(set(x for x in a.dom_contract()[route]['links']if x.startswith(('/','#'))))
            flows=[]
            for i,href in enumerate(links):
                target=a.urlsplit(a.urljoin('http://127.0.0.1:12345'+route,href))
                flow={'href':href,'passed':True,'resolvedPath':target.path,'fragment':target.fragment,'skipTargetVisible':True,'screenshot':screen(target.path,w,h,'anchor-from-'+('home'if route=='/'else route.strip('/').replace('/','--').replace('.','-'))+'-'+str(i))}
                if target.fragment and target.fragment!='main-content':flow['geometry']=geometry(w,h)
                flows.append(flow)
            rows.append({'route':route,'width':w,'height':h,'http':200,'issues':[],'safeNavigation':{'back':True,'forward':True,'reload':True},'facts':fixture_facts(runtime,route,w),'fullPage':screen(route,w,h,'full-page',True),'targets':targets,'keyboard':{'passed':True,'count':len(focus),'targets':[{**geometry(w,h,x['domIndex']),**x}for x in focus],'screenshot':screen(route,w,h,'keyboard-final-focus')},'menu':menu,'internalAnchors':flows})
    sha=next(x['sha256']for x in a.load(a.HERE/'output-manifest.json')['files']if x['path']=='404.html')
    return {'schema':'gangdong-browser-observations-v1','controlSha':os.environ.get('GITHUB_SHA','a'*40),'runId':os.environ.get('GITHUB_RUN_ID','123'),'runAttempt':'1','actor':'joseungil-kr','loopbackOrigin':'http://127.0.0.1:12345','sourceSha':a.SOURCE_SHA,'sourceContentSha256':SPEC['sourceContentSha256'],'outputContentSha256':SPEC['outputContentSha256'],'pixelReview':'pending','publicHttpVerified':False,'playwrightVersion':'1.63.0','browserVersion':'123.0.0.0','syntheticFixtureNotBrowserEvidence':True,'routes':rows,'true404':{'path':'/__gangdong_missing_route__/','status':404,'bodySha256':sha,'browserStatus':404,'browserBodySha256':sha},'pageErrors':[],'console':[],'expected404Console':[],'network':[{'url':'http://127.0.0.1:12345'+r,'status':200,'expected404':False}for r in a.ROUTES]+[{'url':'http://127.0.0.1:12345/__gangdong_missing_route__/','status':404,'expected404':True}],'sourceUnchanged':True,'outputUnchanged':True,'fatalError':None}

class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime=a.load(SITE/'src/data/gangdong-runtime.json')
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        cls.source=cls.root/'source';cls.site=cls.source/a.SITE_PATH;cls.site.mkdir(parents=True)
        for row in a.load(a.HERE/'source-manifest.json')['files']:
            dest=cls.site/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SITE/row['path'],dest)
        cls.dist=cls.site/'dist'
        # Runner executes this test before npm ci/build. Original frozen output is optional there.
        if (SITE/'dist').is_dir():shutil.copytree(SITE/'dist',cls.dist)
        cls.output=cls.root/'synthetic-report-fixtures';cls.output.mkdir()
        cls.report=fixture_report(cls.output,cls.runtime)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def reject(self,fn):
        with self.assertRaises((AssertionError,ValueError,KeyError,TypeError,ZeroDivisionError)):fn()
    def test_01_exact_source_and_reuse(self):
        self.assertEqual(len(a.verify_source_files(SITE)),69);self.assertEqual(len(a.verify_reuse()['files']),2)
    def test_02_exact_frozen_output_when_available(self):
        if not self.dist.exists():self.skipTest('Prebuild runner: output equivalence runs after each native build')
        self.assertEqual(len(a.validate_build(self.site)),21)
    def test_03_binding_negative_matrix(self):
        for key,value in [('sourceSha','0'*40),('repositoryTree','0'*40),('sourceTree','0'*40),('sourceParent','0'*40),('repository','x/y'),('path','../x'),('controlRef','refs/heads/main'),('siteUrl','https://example.com'),('mode','PUBLIC'),('routes',['/']),('indexable',True),('productionApproved',True),('ownershipVerified',True),('publicApproved',True),('indexNowEnabled',True),('sourceContentSha256','0'*64),('outputContentSha256','0'*64),('lockSha256','0'*64),('viewports',[[321,740]])]:
            with self.subTest(key=key):
                d=copy.deepcopy(SPEC);d[key]=value;self.reject(lambda:a.validate_spec(d))
    def test_04_source_mutation_rejected(self):
        p=self.site/'src/data/gangdong-runtime.json';original=p.read_bytes()
        try:p.write_bytes(original+b' ');self.reject(lambda:a.verify_source_files(self.site))
        finally:p.write_bytes(original)
    def test_05_source_mode_rejected(self):
        p=self.site/'package.json';mode=p.stat().st_mode
        try:p.chmod(0o755);self.reject(lambda:a.verify_source_files(self.site))
        finally:p.chmod(mode)
    def test_06_symlink_and_path_rejected(self):
        p=self.root/'link';p.symlink_to(self.site,target_is_directory=True)
        self.reject(lambda:a.verify_source_files(p))
        for value in ['../x','a/../../x','/tmp/x','a//b','a\\b','x\x00','a/./b','']:
            with self.subTest(value=value):self.reject(lambda:a.safe_path(value))
    def test_07_output_mutation_and_extra_rejected(self):
        if not self.dist.exists():self.skipTest('Output unavailable until native build')
        p=self.dist/'404.html';original=p.read_bytes()
        try:p.write_bytes(original+b' ');self.reject(lambda:a.validate_build(self.site))
        finally:p.write_bytes(original)
        extra=self.dist/'extra.txt'
        try:extra.write_text('fixture');self.reject(lambda:a.validate_build(self.site))
        finally:extra.unlink()
    def test_08_loopback_request_boundary(self):
        origin='http://127.0.0.1:1234';self.assertTrue(a.allowed_request(origin+'/', 'GET',origin))
        for url,method in [('https://127.0.0.1:1234/','GET'),('http://localhost:1234/','GET'),('http://127.0.0.1:1235/','GET'),('http://evil.test/','GET'),('tel:18440644','GET'),(origin,'POST'),('http://user@127.0.0.1:1234/','GET'),('http://127.0.0.1:bad/','GET')]:
            self.assertFalse(a.allowed_request(url,method,origin))
    def test_09_resolver_negative_paths(self):
        root=self.root/'resolver';root.mkdir(exist_ok=True);(root/'index.html').write_text('fixture');(root/'404.html').write_text('fixture404')
        self.assertEqual(a.upstream.resolve_request(root,'/'),root/'index.html')
        for path in ['/../package.json','/%2e%2e/package.json','/.git/config','https://example.com/x','//example.com/x','/%00','/a\\b']:
            self.reject(lambda:a.upstream.resolve_request(root,path))
    def test_10_environment_negative_matrix(self):
        # Each failure is evaluated before any Git or browser work.
        env={'GITHUB_ACTIONS':'true','GITHUB_EVENT_NAME':'push','GITHUB_RUN_ATTEMPT':'1','GITHUB_ACTOR':'joseungil-kr','GITHUB_TRIGGERING_ACTOR':'joseungil-kr','GITHUB_REPOSITORY':SPEC['repository'],'GITHUB_REF':a.REF,'SITE_FACTORY_REVISION':a.SOURCE_SHA,'SITE_URL':a.ORIGIN,'SITE_ORIGIN':a.ORIGIN,'SITE_INDEXABLE':'false','PRODUCTION_APPROVED':'false','OWNERSHIP_VERIFIED':'false','INDEXNOW_ENABLED':'false','PUBLIC_APPROVED':'false','PYTHONDONTWRITEBYTECODE':'1'}
        for key in env:
            with self.subTest(key=key):
                bad=dict(env);bad[key]='wrong';self.reject(lambda:a.validate_environment(SPEC,bad))
    def test_11_rendered_facts_positive_all_routes_widths(self):
        for w,h in a.VIEWPORTS:
            for route in a.ROUTES:a.assert_facts(fixture_facts(self.runtime,route,w),self.runtime,route,w)
    def test_12_rendered_facts_negative_matrix(self):
        base=fixture_facts(self.runtime,'/',320)
        changes=[('h1',[]),('firstAnswer','different'),('canonical','https://example.com/'),('robots','index,follow'),('viewport',321),('overflow',[{}]),('scrollWidth',330),('copySha','wrong'),('duplicateIds',['x']),('fontStatus','loading'),('faq',[]),('banners',[]),('products',[]),('sourceSectionCount',0),('sourceNote',''),('sources',[]),('phones',['tel:000']),('fixedBar',False),('ids',[])]
        for key,val in changes:
            with self.subTest(key=key):
                f=copy.deepcopy(base);f[key]=val;self.reject(lambda:a.assert_facts(f,self.runtime,'/',320))
        for group,key,val in [('faq','visible',False),('faq','collapsed',True),('images','complete',False),('images','naturalWidth',0),('images','width',0),('banners','naturalWidth',100),('banners','objectFit','cover'),('banners','height',70),('products','href','https://fwith.co.kr/'),('products','sku','WRONG'),('products','src','/wrong.jpg'),('products','objectFit','cover'),('products','descriptionVisible',False),('products','sampleLabelVisible',False)]:
            with self.subTest(group=group,key=key):
                f=copy.deepcopy(base);f[group][0][key]=val;self.reject(lambda:a.assert_facts(f,self.runtime,'/',320))
    def test_13_report_positive_synthetic_only(self):
        result=a.validate_report(copy.deepcopy(self.report),self.output,self.runtime)
        self.assertEqual(result['fullPageCount'],15);self.assertGreater(result['riskViewportCount'],100)
    def test_14_report_negative_matrix(self):
        operations={
          'string_boolean':lambda r:r['routes'][0]['targets'][0]['geometry'].__setitem__('visible','false'),
          'string_hit_test':lambda r:r['routes'][0]['targets'][0]['geometry'].__setitem__('hitTests',['false']*9),
          'menu_string_boolean':lambda r:r['routes'][0]['menu'].__setitem__('clickOpenClose','false'),
          'anchor_string_boolean':lambda r:r['routes'][0]['internalAnchors'][0].__setitem__('passed','false'),
          'external_success':lambda r:r['network'].append({'url':'https://evil.test/','status':200,'expected404':False}),
          'empty_network_record':lambda r:r['network'].append({}),
          'external_fake404':lambda r:r['network'].append({'url':'https://evil.test/','status':500,'expected404':True}),
          'missing_run_binding':lambda r:r.pop('runId'),
          'missing_issue_key':lambda r:r['routes'][0].pop('issues'),
          'unknown_schema':lambda r:r.__setitem__('schema','different'),
          'empty_images':lambda r:r['routes'][0]['facts'].__setitem__('images',[]),
          'dropped_route':lambda r:r['routes'].pop(),
          'reordered_route':lambda r:r['routes'].reverse(),
          'route_error':lambda r:r['routes'][0]['issues'].append('fixture'),
          'dropped_risk':lambda r:r['routes'][0]['targets'].pop(),
          'missing_full_sha':lambda r:r['routes'][0]['fullPage'].__setitem__('sha256','0'*64),
          'wrong_full_route':lambda r:r['routes'][0]['fullPage'].__setitem__('route','/404.html'),
          'wrong_screenshot_dimensions':lambda r:r['routes'][0]['fullPage']['dimensions'].__setitem__('width',321),
          'screenshot_traversal':lambda r:r['routes'][0]['fullPage'].__setitem__('screenshot','../secret'),
          'risk_geometry_lie':lambda r:r['routes'][0]['targets'][0]['geometry'].__setitem__('visible',False),
          'keyboard_lie':lambda r:r['routes'][0]['keyboard']['targets'][0].__setitem__('focusVisible',False),
          'keyboard_duplicate':lambda r:r['routes'][0]['keyboard']['targets'][1].__setitem__('domIndex',0),
          'menu_dropped':lambda r:r['routes'][0]['menu'].__setitem__('clickOpenClose',False),
          'anchor_dropped':lambda r:r['routes'][0]['internalAnchors'].pop(),
          'false404':lambda r:r['true404'].__setitem__('status',200),
          'browser404_mismatch':lambda r:r['true404'].__setitem__('browserBodySha256','0'*64),
          'source_mutated':lambda r:r.__setitem__('sourceUnchanged',False),
          'output_mutated':lambda r:r.__setitem__('outputUnchanged',False),
          'public_success_claim':lambda r:r.__setitem__('publicHttpVerified',True),
          'pixel_success_claim':lambda r:r.__setitem__('pixelReview','passed'),
          'wrong_browser_version':lambda r:r.__setitem__('playwrightVersion','1.62.0'),
          'network_failure':lambda r:r['network'].append({'failure':'fixture'}),
          'external_blocked':lambda r:r['network'].append({'blocked':True}),
          'unexpected500':lambda r:r['network'].append({'status':500}),
          'page_error':lambda r:r['pageErrors'].append('fixture'),
          'console_error':lambda r:r['console'].append({'type':'error'}),
          'fatal':lambda r:r.__setitem__('fatalError','fixture')}
        for name,mutate in operations.items():
            with self.subTest(name=name):
                report=copy.deepcopy(self.report);mutate(report);self.reject(lambda:a.validate_report(report,self.output,self.runtime))
    def test_15_screenshot_bytes_mutated(self):
        row=self.report['routes'][0]['fullPage'];p=self.output/row['screenshot'];original=p.read_bytes()
        try:p.write_bytes(original+b'x');self.reject(lambda:a.validate_report(self.report,self.output,self.runtime))
        finally:p.write_bytes(original)
    def test_16_artifact_receipt_negative_matrix(self):
        env={'ARTIFACT_ID':'123','GITHUB_RUN_ID':'456','GITHUB_RUN_ATTEMPT':'1','GITHUB_SHA':'a'*40,'ARTIFACT_DIGEST':'b'*64,'ARTIFACT_URL':'https://github.com/joseungil-kr/fwith-site-factory/actions/runs/456/artifacts/123'}
        self.assertFalse(receipt(env)['independentArtifactDownloadVerified'])
        for k in env:
            bad=dict(env);bad[k]='wrong';self.reject(lambda:receipt(bad))
    def test_17_browser_entry_denied_without_runner(self):
        import run_capture
        with patch.object(run_capture,'validate_environment',side_effect=AssertionError('not-runner')),patch.object(run_capture,'run')as run,patch('sys.argv',['run_capture.py','--allow-loopback-runner']):
            self.reject(run_capture.main);run.assert_not_called()
    def test_18_non_loopback_server_denied_before_bind(self):
        self.reject(lambda:a.SafeServer(('0.0.0.0',0),a.GangdongHandler))

    def test_19_source_git_binding_and_outside_mutation(self):
        outer=self.source/'outside-project-tracked.txt';outer.write_text('frozen outside bytes')
        files='\n'.join(a.SITE_PATH+'/'+r['path']for r in a.load(a.HERE/'source-manifest.json')['files'])
        def git(root,*args):
            if args[0]=='rev-parse':return {'HEAD':a.SOURCE_SHA,'HEAD^':SPEC['sourceParent'],'HEAD^{tree}':a.ROOT_TREE,'HEAD:'+a.SITE_PATH:a.PROJECT_TREE}[args[1]]
            if args==('diff','--name-only','HEAD'):return ''if outer.read_text()=='frozen outside bytes'else'outside-project-tracked.txt'
            if args==('diff','--cached','--name-only'):return ''
            if args==('ls-files','--',a.SITE_PATH):return files
            raise AssertionError('Unexpected or project-only Git query: '+repr(args))
        with patch.object(a.upstream,'git',side_effect=git):
            a.verify_source(self.source)
            outer.write_text('changed outside bytes');self.reject(lambda:a.verify_source(self.source));outer.write_text('frozen outside bytes')
            extra=self.site/'untracked.py';extra.write_text('fixture')
            try:self.reject(lambda:a.verify_source(self.source))
            finally:extra.unlink()
        for expression in ['HEAD','HEAD^','HEAD^{tree}','HEAD:'+a.SITE_PATH]:
            def bad(root,*args):return '0'*40 if args==('rev-parse',expression)else git(root,*args)
            with patch.object(a.upstream,'git',side_effect=bad):self.reject(lambda:a.verify_source(self.source))
    def test_20_handler_no_socket_true404_and_traversal(self):
        root=self.root/'handler';root.mkdir();(root/'404.html').write_bytes(b'frozen 404 body');(root/'index.html').write_bytes(b'home')
        for path,status,body in [('/',200,b'home'),('/404.html',200,b'frozen 404 body'),('/missing/',404,b'frozen 404 body'),('/../secret',403,None),('/.git/config',403,None),('https://example.com/',403,None)]:
            handler=a.GangdongHandler.__new__(a.GangdongHandler);handler.directory=str(root);handler.path=path;observed=[]
            handler.send_response=lambda code:observed.append(code);handler.send_error=lambda code,*args:observed.append(code);handler.send_header=lambda *args:None;handler.end_headers=lambda:None
            stream=handler.send_head();self.assertEqual(observed,[status])
            if stream:
                with stream:self.assertEqual(stream.read(),body)
    def test_21_artifact_partition_and_limits(self):
        from prepare_artifacts import prepare,group_for
        root=self.root/'partition-evidence';root.mkdir();(root/'report.json').write_text('{}')
        (root/'screenshots/320/home').mkdir(parents=True);(root/'screenshots/320/home/x.jpg').write_bytes(synthetic_jpeg(320,740))
        index=prepare(root,self.root/'partition-staging')
        self.assertEqual(index['coveragePathCount'],2);self.assertTrue(index['allEvidencePathsCoveredOnce']);self.assertFalse(index['completeExpectedGroups'])
        self.assertEqual({x['key']for x in index['groups']},{'reports','screen_320_home'})
        self.reject(lambda:group_for('screenshots/321/home/x.jpg'))
        self.reject(lambda:group_for('screenshots/320/wrong/x.jpg'))
        self.reject(lambda:group_for('unexpected/subdir/file'))
        with patch('prepare_artifacts.LIMIT',10):self.reject(lambda:prepare(root,self.root/'partition-too-large'))
    def test_22_environment_root_symlink_before_git(self):
        root=self.root/'workspace';root.mkdir();(root/'source').mkdir();control=root/'control/.github/qa/unpublished-gangdong';control.mkdir(parents=True)
        env={'GITHUB_ACTIONS':'true','GITHUB_EVENT_NAME':'push','GITHUB_RUN_ATTEMPT':'1','GITHUB_ACTOR':'joseungil-kr','GITHUB_TRIGGERING_ACTOR':'joseungil-kr','GITHUB_REPOSITORY':SPEC['repository'],'GITHUB_REF':a.REF,'SITE_FACTORY_REVISION':a.SOURCE_SHA,'SITE_URL':a.ORIGIN,'SITE_ORIGIN':a.ORIGIN,'SITE_INDEXABLE':'false','PRODUCTION_APPROVED':'false','OWNERSHIP_VERIFIED':'false','INDEXNOW_ENABLED':'false','PUBLIC_APPROVED':'false','PYTHONDONTWRITEBYTECODE':'1','GITHUB_SHA':'a'*40,'GITHUB_RUN_ID':'123','GITHUB_WORKSPACE':str(root),'SOURCE_ROOT':str(root/'source'),'EVIDENCE_ROOT':str(root/'evidence/gangdong')}
        with patch.object(a,'HERE',control),patch.object(a.upstream,'git',side_effect=lambda root,*args:'a'*40 if args[0]=='rev-parse'else''):
            a.validate_environment(SPEC,env)
            (root/'evidence').symlink_to(self.root,target_is_directory=True)
            self.reject(lambda:a.validate_environment(SPEC,env))
    def test_23_required_report_fields_and_strict_geometry(self):
        ops=[lambda r:r.pop('fatalError'),lambda r:r.__setitem__('browserVersion',True),lambda r:r['routes'][0]['safeNavigation'].__setitem__('back',1),lambda r:r['routes'][0]['targets'][0]['geometry'].__setitem__('safeTop',-200),lambda r:r['routes'][0]['targets'][0]['geometry'].__setitem__('width',55),lambda r:r['console'].append({'type':'madeup'}),lambda r:r.__setitem__('network',[{'url':'http://127.0.0.1:12345/favicon.svg','status':200,'expected404':False}])]
        for op in ops:
            r=copy.deepcopy(self.report);op(r);self.reject(lambda:a.validate_report(r,self.output,self.runtime))
        r=copy.deepcopy(self.report);r['routes'][0]['targets'].append(copy.deepcopy(r['routes'][0]['targets'][0]));self.reject(lambda:a.validate_report(r,self.output,self.runtime))
        row=copy.deepcopy(self.report['routes'][0]['fullPage']);p=self.output/row['screenshot'];original=p.read_bytes()
        try:p.write_bytes(original[:-2]);row['sha256']=a.digest(p.read_bytes());self.reject(lambda:a.validate_screen(row,self.output,True))
        finally:p.write_bytes(original)

    def test_24_receipt_collector_binding_duplicates_and_groups(self):
        from artifact_receipt import collect
        from prepare_artifacts import EXPECTED_GROUPS,LIMIT
        env={'GITHUB_SHA':'a'*40,'GITHUB_RUN_ID':'456','GITHUB_RUN_ATTEMPT':'1'}
        index={'schema':'gangdong-artifact-index-v1','sourceSha':a.SOURCE_SHA,'controlSha':env['GITHUB_SHA'],'runId':'456','runAttempt':'1','expectedGroups':sorted(EXPECTED_GROUPS),'groups':[{'key':key,'files':[],'totalBytes':0,'maxUncompressedBytes':LIMIT}for key in sorted(EXPECTED_GROUPS)],'missingGroups':[]}
        reported={key:{'id':str(i+100),'url':f'https://github.com/joseungil-kr/fwith-site-factory/actions/runs/456/artifacts/{i+100}','digest':'b'*64}for i,key in enumerate(sorted(EXPECTED_GROUPS))}
        rows,missing=collect(index,reported,env);self.assertEqual(len(rows),17);self.assertFalse(missing)
        for key in ['sourceSha','controlSha','runId','runAttempt']:
            bad=copy.deepcopy(index);bad[key]='wrong';self.reject(lambda:collect(bad,reported,env))
        bad=copy.deepcopy(index);bad['groups'].pop();bad['expectedGroups'].pop();bad_report={k:v for k,v in reported.items()if k in bad['expectedGroups']};self.reject(lambda:collect(bad,bad_report,env))
        bad=copy.deepcopy(reported);keys=list(bad);bad[keys[1]]=bad[keys[0]];self.reject(lambda:collect(index,bad,env))
        bad=copy.deepcopy(reported);bad[keys[0]]['unexpected']='field';self.reject(lambda:collect(index,bad,env))
    def test_25_frozen_dom_completeness_and_geometry_viewports(self):
        for mutate in [lambda r:r['routes'][0]['facts']['links'].pop(),lambda r:r['routes'][0]['keyboard']['targets'].pop(),lambda r:r['routes'][0]['targets'][0]['geometry'].__setitem__('viewportWidth',1280)]:
            report=copy.deepcopy(self.report);mutate(report);self.reject(lambda:a.validate_report(report,self.output,self.runtime))
        report=copy.deepcopy(self.report);row=report['routes'][0];href=row['internalAnchors'][-1]['href'];row['facts']['links']=[x for x in row['facts']['links']if x!=href];row['internalAnchors'].pop();self.reject(lambda:a.validate_report(report,self.output,self.runtime))
    def test_26_diagnostics_are_bounded(self):
        from write_diagnostics import diagnostics
        root=self.root/'diagnostic-workspace';(root/'evidence').mkdir(parents=True);(root/'evidence/gangdong-grouping.log').write_text('x'*20000)
        with patch.dict(os.environ,{'GITHUB_SHA':'a'*40,'GITHUB_RUN_ID':'456','GITHUB_RUN_ATTEMPT':'1'}):result=diagnostics(root)
        self.assertEqual(len(result['logs'][0]['tail']),8192);self.assertLess(len(a.compact(result)),128*1024);self.assertFalse(result['publicHttpVerified'])

if __name__=='__main__':unittest.main()
