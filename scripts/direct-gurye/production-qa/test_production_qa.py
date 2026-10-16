"""Real source60/output15 plus explicitly synthetic browser-report fixtures.

These are validator tests, not a production browser run or screenshot acceptance.
"""
from pathlib import Path
import copy,hashlib,json,mimetypes,os,shutil,struct,tempfile,unittest,zlib
import production_qa as g

def png_rows(width,values):
 def chunk(k,b):return struct.pack('>I',len(b))+k+b+struct.pack('>I',zlib.crc32(k+b)&0xffffffff)
 raw=b''.join(b'\0'+bytes([value])*(width*3)for value in values)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,len(values),8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
def png(width,height,value=0):return png_rows(width,[value]*height)

def synthetic_reports(source,dist,b,module,qb):
 q=module.base.q;f=qb['browserExpected'];folder=source/'candidate/evidence/browser';folder.mkdir(parents=True)
 states=[];images=[];reach=[];interactions=[];touch=[];screens=[];captures=[];metadata=[];rect={'x':0,'y':0,'width':100,'height':50}
 for width in f['widths']:
  for route in ['/','/404.html']:
   observations=[{'key':e['key'],'text':e['text'],'tag':e['tag'],'href':e.get('href'),'available':True,'rect':dict(rect)}for e in f['occurrences'][route]]
   states.append({'width':width,'route':route,'failures':[],'bodyExact':True,'scrollWidth':width,'clientWidth':width,'observations':observations})
   interactions.append({'width':width,'route':route,'test':'keyboard skip focuses main','pass':True})
   metadata.append({'width':width,'route':route,'robots':'index,follow'if route=='/'else'noindex,follow','canonical':['https://gurye.fwith.kr/']if route=='/'else[],'source':b['assemblyRevision'],'privateSource':g.SOURCE,'releaseState':'production-candidate','social':[list(x)for x in module.social_values(module.read_contract(),module.verify_inputs(source)[4])]if route=='/'else[]})
  for e in f['images']:images.append({'width':width,**e,'displayWidth':100,'displayHeight':100*e['naturalHeight']/e['naturalWidth'],'objectFit':'contain'})
  reach.extend({'width':width,'key':e['key'],'rect':dict(rect)}for e in f['occurrences']['/']if e['key']!='ui.skipLabel')
  interactions.extend({'width':width,'test':'anchor/back/forward','href':href,'pass':True}for href in f['navigationHrefs'])
  interactions.extend([{'width':width,'test':'404 navigation home anchor','pass':True},{'width':width,'test':'404 recovery CTA','pass':True}])
  touch.extend({'width':width,'text':label,'height':44,'widthPx':100}for label in f['touchLabels'])
 for name,(width,height)in q.screenshot_expectations(f).items():
  home=name.startswith('home-');full=name.endswith('-full.png');section=home and not full and not name.endswith('-top.png');scroll=100 if section else 0;document_height=2000 if home else 844
  values=[y%211 for y in range(document_height)]
  raster=values if full else values[scroll:scroll+844]
  if name in g.sticky_names():raster=[237]*71+raster[71:]
  data=png_rows(width,raster);(folder/name).write_bytes(data);screens.append({'path':name,'sha256':q.sha(data)})
  geometry={'scrollX':0,'scrollY':scroll,'width':width,'height':844,'documentHeight':document_height,'fontStatus':'loaded'}
  cap={'path':name,'fullPage':full,'before':geometry,'after':dict(geometry),'settle':{'stableTransitions':5,'samples':[dict(geometry)for _ in range(6)]}}
  if name in g.sticky_names():
   header_expected=[e for e in f['occurrences']['/']if e['key']in ['ui.brandLabel','ui.regionLabel','ui.navigation.0','ui.navigation.1','ui.navigation.2','ui.navigation.3']]
   header={'rect':{'x':0,'y':0,'width':1280,'height':71},'position':'sticky','top':'0px','zIndex':'20','backgroundColor':'rgba(255, 255, 255, 0.96)','backdropFilter':'blur(10px)','borderBottomWidth':'1px','observations':[{'key':e['key'],'text':e['text'],'tag':e['tag'],'href':e.get('href'),'available':True,'rect':{'x':i*180,'y':15,'width':100,'height':40}}for i,e in enumerate(header_expected)]}
   raw=png(1280,71,237);path='sticky-headers/'+name;(folder/path).parent.mkdir(exist_ok=True);(folder/path).write_bytes(raw)
   cap['stickyHeader']={'path':path,'sha256':q.sha(raw),'before':header,'after':copy.deepcopy(header),'geometryAfter':dict(geometry)}
  captures.append(cap)
 paths={'/','/404.html'}|{e['src']for e in f['images']}|{'/'+n for n in qb['expectedDistFiles']if n.endswith('.css')}
 report={'status':'PASS_AUTHOR_LOCAL_CHROMIUM_CHECKS','checkedAtUTC':'2026-10-16T14:00:00+00:00','browserVersion':'123.0.0.0','origin':'loopback-only','widths':f['widths'],'pages':2,'states':states,'imageAspectChecks':images,'scrollReachability':reach,'interactions':interactions,'touchTargets':touch,'computedVisibilityMutationDetected':True,'localMissingRouteStatus':404,'responses':[{'path':n,'status':200}for n in sorted(paths)]+[{'path':'/.gurye-private-missing/','status':404}],'externalRequestsBlocked':[],'pageErrors':[],'externalCTAAndPhoneActivated':False,'publicHTTPVerified':False,'independentImplementationReview':False,'screenshots':screens}
 http=[]
 for name,data in sorted(module.base.inventory(dist).items()):
  path='/'if name=='index.html'else'/'+name;http.append({'path':path,'status':200,'sha256':q.sha(data),'bytes':len(data),'contentType':'application/octet-stream'if name=='_headers'else mimetypes.guess_type(name)[0],'finalURLPath':path})
 capture={'privateSourceRevision':g.SOURCE,'assemblyRevision':b['assemblyRevision'],'origin':'loopback-only','captures':captures,'metadata':metadata,'httpFiles':http,'missingRoute':{'path':'/.gurye-private-missing/','status':404,'sha256':g.sha((dist/'404.html').read_bytes()),'bytes':(dist/'404.html').stat().st_size,'robots':'noindex,follow','canonicalCount':0},'publicHTTPVerified':False,'publicationReady':False}
 g.save(folder/'browser-report.json',report);g.save(folder/'production-capture.json',capture);return report,capture

class ControlTests(unittest.TestCase):
 def test_owner_boundary(self):
  env={'GITHUB_REPOSITORY':g.REPO,'GITHUB_REF':'refs/heads/main','GITHUB_ACTOR':g.OWNER,'GITHUB_TRIGGERING_ACTOR':g.OWNER,'GITHUB_RUN_ATTEMPT':'1','GITHUB_EVENT_NAME':'issues','GITHUB_SHA':'1'*40,'GITHUB_RUN_ID':'123'};event={'action':'opened','issue':{'title':g.TITLE,'number':1,'user':{'login':g.OWNER,'type':'User'}}};g.owner(env,event)
  for k in env:
   bad=dict(env);bad[k]='wrong'
   with self.assertRaises(ValueError):g.owner(bad,event)
  for mutate in [lambda e:e.update(action='edited'),lambda e:e['issue'].update(title='wrong'),lambda e:e['issue']['user'].update(login='other'),lambda e:e['issue']['user'].update(type='Bot')]:
   bad=copy.deepcopy(event);mutate(bad)
   with self.assertRaises(ValueError):g.owner(env,bad)
 def test_geometry_and_path_guards(self):
  good={'scrollX':0,'scrollY':0,'width':390,'height':844,'documentHeight':1000,'fontStatus':'loaded'};g.verify_geometry(good,390,844)
  for k,v in [('scrollX',1),('scrollY',float('nan')),('scrollY',True),('scrollY',.5),('width',320),('height',600),('documentHeight',500),('fontStatus','loading')]:
   bad=dict(good);bad[k]=v
   with self.assertRaises(ValueError):g.verify_geometry(bad,390,844)
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);(root/'x').write_text('x');(root/'link').symlink_to(root/'x')
   for rel in ['../x','/x','link','missing']:
    with self.assertRaises(ValueError):g.safe(root,rel)

class RealInputAndSyntheticObservationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.b=g.binding();cls.original=Path(os.environ['GURYE_PRODUCTION_CHECKOUT']).resolve();cls.dist=Path(os.environ['GURYE_PRODUCTION_DIST']).resolve()
  if os.environ.get('GURYE_UNIT_REMOTE_READBACK_ONLY')=='1':
   # Local downloaded-only fixture has no fabricated .git; CLI/Actions always verifies HEAD.
   module,source,_=g.check_files(cls.original,cls.b,False);module.validate(source,cls.dist,cls.b['assemblyRevision'])
  else:g.postbuild(cls.original,cls.dist,cls.b)
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='gurye-control60-test-');self.root=Path(self.tmp.name);self.checkout=self.root/'target';self.checkout.mkdir()
  for row in self.b['files']:
   p=self.checkout/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((self.original/row['path']).read_bytes())
  self.source=self.checkout/'site-factory/gurye-flower';shutil.copytree(self.original/'site-factory/gurye-flower/candidate/dist',self.source/'candidate/dist');self.output=self.root/'release15';shutil.copytree(self.dist,self.output)
 def tearDown(self):self.tmp.cleanup()
 def test_real_source60_and_output15_positive(self):
  module,source,qb=g.check_files(self.checkout,self.b,git_required=False);self.assertEqual(module.validate(source,self.output,self.b['assemblyRevision'])['productionFilesVerified'],15)
 def test_actual_head_is_required_by_default(self):
  with self.assertRaisesRegex(ValueError,'checkout HEAD'):g.check_files(self.checkout,self.b)
 def test_source_mutations_and_nested_generated_name_rejected(self):
  p=self.source/'candidate/src/layouts/BaseLayout.astro';before=p.read_bytes();p.write_bytes(before+b'\n')
  with self.assertRaises(ValueError):g.check_files(self.checkout,self.b,False)
  p.write_bytes(before)
  for name in ['site-factory/gurye-flower/candidate/src/evidence/unreviewed.py','scripts/direct-gurye/keyless-release/extra.py','scripts/direct-gurye/production-release/extra.py']:
   p=self.checkout/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('bad')
   with self.assertRaises(ValueError):g.check_files(self.checkout,self.b,False)
   p.unlink()
 def test_synthetic_complete_contract_and_negative_metadata_http_frames(self):
  module,source,qb=g.check_files(self.checkout,self.b,False);report,capture=synthetic_reports(source,self.output,self.b,module,qb);folder=source/'candidate/evidence/browser'
  result=g.verify_browser(self.checkout,self.output,self.b,git_required=False);self.assertEqual(result['stableCapturesVerified'],31);self.assertEqual(len(result['homeViewportFullPixelComparisons']),24);self.assertFalse(result['publicationReady']);self.assertEqual(result['stickyHeaderReferencesVerified'],7);self.assertEqual(sum(x['stickyReferenceRows']for x in result['homeViewportFullPixelComparisons']),7*71)
  mutations=[lambda r:r.update(assemblyRevision='f'*40),lambda r:r['metadata'][0].update(robots='noindex,nofollow'),lambda r:r['metadata'][0].update(canonical=['https://gokseong.fwith.kr/']),lambda r:r['metadata'][0].update(source='0'*40),lambda r:r['metadata'][0].update(width=390),lambda r:r['httpFiles'].pop(),lambda r:r['httpFiles'][0].update(status=404),lambda r:r['httpFiles'][0].update(sha256='0'*64),lambda r:r['httpFiles'][0].update(contentType='wrong/type'),lambda r:r['httpFiles'][0].update(finalURLPath='/other'),lambda r:r['captures'][0]['settle'].update(samples=[]),lambda r:r['captures'][0]['settle']['samples'][0].update(scrollY=1),lambda r:r['captures'][0]['before'].update(fontStatus='loading'),lambda r:r['captures'][0].update(path='wrong.png'),lambda r:r['captures'][0].update(fullPage=True)]
  for mutate in mutations:
   bad=copy.deepcopy(capture);mutate(bad);g.save(folder/'production-capture.json',bad)
   with self.assertRaises(ValueError):g.verify_browser(self.checkout,self.output,self.b,git_required=False)
  g.save(folder/'production-capture.json',capture)
  # A real PNG with the right dimensions/hash but different raster must fail full comparison.
  name='home-390-ribbon.png';data=png(390,844,1);(folder/name).write_bytes(data)
  for row in report['screenshots']:
   if row['path']==name:row['sha256']=g.sha(data)
  g.save(folder/'browser-report.json',report)
  with self.assertRaisesRegex(ValueError,'raster'):g.verify_browser(self.checkout,self.output,self.b,git_required=False)
 def test_sticky_overlay_observations_and_pixels_are_bounded(self):
  module,source,qb=g.check_files(self.checkout,self.b,False);report,capture=synthetic_reports(source,self.output,self.b,module,qb);folder=source/'candidate/evidence/browser';target=next(i for i,x in enumerate(capture['captures'])if x['path']=='home-1280-ribbon.png')
  mutations=[lambda h:h['before'].update(position='relative'),lambda h:h['before']['rect'].update(height=400),lambda h:h['before']['observations'][0].update(available=False),lambda h:h['before']['observations'][0].update(text='wrong'),lambda h:h['before']['observations'][0]['rect'].update(y=100),lambda h:h['after'].update(top='1px'),lambda h:h['geometryAfter'].update(scrollY=101),lambda h:h.update(path='../wrong.png'),lambda h:h.update(sha256='0'*64)]
  for mutate in mutations:
   bad=copy.deepcopy(capture);mutate(bad['captures'][target]['stickyHeader']);g.save(folder/'production-capture.json',bad)
   with self.assertRaises(ValueError):g.verify_browser(self.checkout,self.output,self.b,False)
  original_view=(folder/'home-1280-ribbon.png').read_bytes()
  for values,error in [([238]*71+[y%211 for y in range(171,944)],'Sticky header raster'),([237]*71+[0]*773,'body raster')]:
   data=png_rows(1280,values);name='home-1280-ribbon.png';(folder/name).write_bytes(data);changed=copy.deepcopy(report)
   for row in changed['screenshots']:
    if row['path']==name:row['sha256']=g.sha(data)
   g.save(folder/'browser-report.json',changed);g.save(folder/'production-capture.json',capture)
   with self.assertRaisesRegex(ValueError,error):g.verify_browser(self.checkout,self.output,self.b,False)
  (folder/'home-1280-ribbon.png').write_bytes(original_view);g.save(folder/'browser-report.json',report)
  bad=copy.deepcopy(capture);h=bad['captures'][target]['stickyHeader'];raw=png(1280,70,237);(folder/h['path']).write_bytes(raw);h['sha256']=g.sha(raw);g.save(folder/'production-capture.json',bad)
  with self.assertRaisesRegex(ValueError,'dimensions'):g.verify_browser(self.checkout,self.output,self.b,False)
  raw=png(1280,71,237);(folder/h['path']).write_bytes(raw);g.save(folder/'production-capture.json',capture);(folder/'unreviewed.png').write_text('bad')
  with self.assertRaisesRegex(ValueError,'inventory'):g.verify_browser(self.checkout,self.output,self.b,False)
 def test_social_dom_and_empty_headers_are_verified(self):
  module,source,qb=g.check_files(self.checkout,self.b,False);report,capture=synthetic_reports(source,self.output,self.b,module,qb);folder=source/'candidate/evidence/browser'
  for index in range(14):
   for change in ['missing','duplicate','value']:
    bad=copy.deepcopy(capture);social=bad['metadata'][0]['social']
    if change=='missing':social.pop(index)
    elif change=='duplicate':social.append(social[index])
    else:social[index][2]='unreviewed'
    g.save(folder/'production-capture.json',bad)
    with self.assertRaisesRegex(ValueError,'DOM metadata'):g.verify_browser(self.checkout,self.output,self.b,False)
  bad=copy.deepcopy(capture);bad['metadata'][1]['social']=capture['metadata'][0]['social'];g.save(folder/'production-capture.json',bad)
  with self.assertRaises(ValueError):g.verify_browser(self.checkout,self.output,self.b,False)
  g.save(folder/'production-capture.json',capture);headers=self.output/'_headers';headers.write_text('/*\n  X-Robots-Tag: noindex\n')
  with self.assertRaises(ValueError):g.verify_browser(self.checkout,self.output,self.b,False)
 def test_actual_package_requires_control_head_and_native_gates(self):
  env={'GITHUB_REPOSITORY':g.REPO,'GITHUB_REF':'refs/heads/main','GITHUB_ACTOR':g.OWNER,'GITHUB_TRIGGERING_ACTOR':g.OWNER,'GITHUB_RUN_ATTEMPT':'1','GITHUB_EVENT_NAME':'issues','GITHUB_SHA':'1'*40,'GITHUB_RUN_ID':'123'};event={'action':'opened','issue':{'title':g.TITLE,'number':1,'user':{'login':g.OWNER,'type':'User'}}}
  with self.assertRaisesRegex(ValueError,'native gates'):g.package_release(self.checkout,self.output,self.b,env,event)
  env['NATIVE_GATES_PASSED']='true'
  with self.assertRaisesRegex(ValueError,'control checkout HEAD'):g.package_release(self.checkout,self.output,self.b,env,event)
  self.assertFalse((self.output.parent/'release.json').exists())
 def test_real_output15_release_manifest_pure_contract(self):
  module,source,qb=g.check_files(self.checkout,self.b,False);facts=module.validate(source,self.output,self.b['assemblyRevision']);control='1'*40;run='123';manifest=module.release_manifest(facts['files'],self.b['assemblyRevision'],control,run,g.BINDING_SHA)
  module.validate_release_manifest(manifest,facts['files'],self.b['assemblyRevision'],control,run,g.BINDING_SHA);raw=module.release_manifest_bytes(manifest)
  self.assertEqual(raw,(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode());self.assertEqual(manifest['sourceBranch'],self.b['sourceBranch']);self.assertEqual(manifest['sourceContractSha256'],module.CONTRACT_SHA);self.assertEqual(manifest['revision'],self.b['assemblyRevision'])
  for key in manifest:
   bad=copy.deepcopy(manifest);bad[key]=None
   with self.assertRaises(ValueError):module.validate_release_manifest(bad,facts['files'],self.b['assemblyRevision'],control,run,g.BINDING_SHA)
 def test_real_capture_startup_reaches_socket_boundary_without_module_shadowing(self):
  # Execute the unchanged capture startup and real Handler construction. No socket or browser starts.
  import importlib.util,sys,types
  from unittest.mock import patch,Mock
  class StopBeforeSocket(RuntimeError):pass
  api=types.ModuleType('playwright.sync_api');api.sync_playwright=Mock(side_effect=AssertionError('browser_must_not_start'))
  parent=types.ModuleType('playwright');parent.sync_api=api
  with patch.dict(sys.modules,{'playwright':parent,'playwright.sync_api':api}):
   sys.modules.pop('expected_surface',None)
   spec=importlib.util.spec_from_file_location('gurye_capture_startup',g.ROOT/'capture_production.py');capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)
   with patch.object(capture.socketserver,'ThreadingTCPServer',side_effect=StopBeforeSocket('socket boundary reached'))as server:
    with self.assertRaisesRegex(StopBeforeSocket,'socket boundary reached'):capture.run(self.source,self.output,self.b['assemblyRevision'])
    server.assert_called_once();self.assertEqual(server.call_args.args[0],('127.0.0.1',0));self.assertTrue(issubclass(server.call_args.args[1],capture.http.server.SimpleHTTPRequestHandler))
   api.sync_playwright.assert_not_called()
if __name__=='__main__':unittest.main()
