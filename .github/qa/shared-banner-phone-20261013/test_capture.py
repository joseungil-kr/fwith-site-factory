"""Offline adversarial tests. Never installs or launches a browser."""
from pathlib import Path
from copy import deepcopy
import importlib.util,json,os,stat,tempfile,unittest,zipfile
from unittest.mock import patch
from bind import (HERE,BUILD_CONTROL,REGIONS,REPRESENTATIVES,validate_bindings,validate_metadata,
 extract_bound_archive,verify_runner,inspect_artifact,summarize_run,summarize_artifact)
from reused import digest,compact,resolve_request,allowed_request,SafeServer,manifest
from capture import assert_facts,assert_focus,validate_capture

class BoundTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.data=json.loads((HERE/'bindings.json').read_text());self.data['selectedRegions']=['seoul-yangcheon']
  self.row=self.data['sites']['seoul-yangcheon'];self.b=self.row['build']
  require=self.assertIsNotNone;require(self.b)
  self.control=self.root/'control';(self.control/'docs/shared-banner-phone-20261013').mkdir(parents=True)
  catalog={r:{'revision':v['sourceSha'],'releaseReview':None,'releaseReviewSha256':None}for r,v in self.data['sites'].items()}
  (self.control/'docs/shared-banner-phone-20261013/targets.json').write_text(json.dumps({'targets':catalog}))
  self.run={'id':int(self.b['runId']),'head_sha':self.b['controlSha'],'head_branch':'main','path':'.github/workflows/shared-banner-phone-build-only.yml','status':'completed','conclusion':'success','run_attempt':1,'event':'issues','repository':{'full_name':'joseungil-kr/fwith-site-factory'},'actor':{'login':'joseungil-kr'},'triggering_actor':{'login':'joseungil-kr'}}
  self.artifact={'id':int(self.b['artifactId']),'name':f'phone-banner-seoul-yangcheon-build-{self.b["runId"]}','expired':False,'digest':'sha256:'+self.b['archiveSha256'],'workflow_run':{'id':int(self.b['runId']),'head_sha':self.b['controlSha'],'head_branch':'main'},'size_in_bytes':123}
 def test_catalog_exact_33(self):self.assertEqual(len(validate_bindings(self.data,self.control)),33)
 def test_unknown_region(self):
  self.data['sites']['unknown']=self.row
  with self.assertRaises(ValueError):validate_bindings(self.data,self.control)
 def test_selection_cannot_duplicate(self):
  self.data['selectedRegions']=['seoul-yangcheon']*2
  with self.assertRaises(ValueError):validate_bindings(self.data,self.control)
 def test_selection_cannot_be_empty(self):
  self.data['selectedRegions']=[]
  with self.assertRaises(ValueError):validate_bindings(self.data,self.control)
 def test_selected_unbound_rejected(self):
  self.data['selectedRegions']=['anseong'];self.data['sites']['anseong']['build']=None
  with self.assertRaises(ValueError):validate_bindings(self.data,self.control)
 def test_capture_route_cannot_drift(self):
  self.row['captureRoutes']=['/']
  with self.assertRaises(ValueError):validate_bindings(self.data,self.control)
 def test_source_cannot_drift(self):
  self.row['sourceSha']='a'*40
  with self.assertRaises(ValueError):validate_bindings(self.data,self.control)
 def test_all_missing_bindings_cannot_be_complete(self):
  self.data['selectedRegions']=sorted(REGIONS)
  for r in self.data['sites'].values():r['build']=None
  with self.assertRaises(ValueError):validate_bindings(self.data,self.control)
 def test_bound_metadata(self):validate_metadata('seoul-yangcheon',self.row,self.run,self.artifact)
 def test_each_metadata_boundary(self):
  for field,value in [('head_sha','b'*40),('head_branch','other'),('status','in_progress'),('conclusion','failure'),('run_attempt',2),('path','wrong.yml'),('id',1),('event','pull_request')]:
   with self.subTest(field=field):
    bad=deepcopy(self.run);bad[field]=value
    with self.assertRaises(ValueError):validate_metadata('seoul-yangcheon',self.row,bad,self.artifact)
 def test_actor_boundary(self):
  self.run['actor']['login']='another-owner'
  with self.assertRaises(ValueError):validate_metadata('seoul-yangcheon',self.row,self.run,self.artifact)
 def test_artifact_digest(self):
  self.artifact['digest']='sha256:'+'0'*64
  with self.assertRaises(ValueError):validate_metadata('seoul-yangcheon',self.row,self.run,self.artifact)
 def test_artifact_expired(self):
  self.artifact['expired']=True
  with self.assertRaises(ValueError):validate_metadata('seoul-yangcheon',self.row,self.run,self.artifact)
 def test_artifact_cross_run(self):
  self.artifact['workflow_run']['id']=123
  with self.assertRaises(ValueError):validate_metadata('seoul-yangcheon',self.row,self.run,self.artifact)
 def test_artifact_wrong_name(self):
  self.artifact['name']='evidence-not-release'
  with self.assertRaises(ValueError):validate_metadata('seoul-yangcheon',self.row,self.run,self.artifact)
 def archive(self,entries):
  f=self.root/'input.zip'
  with zipfile.ZipFile(f,'w')as z:
   for name,value in entries:z.writestr(name,value)
  return f
 def test_archive_exact_bytes(self):
  f=self.archive([('release.json','{}'),('dist/index.html','ok')]);out=extract_bound_archive(f,self.root/'release',digest(f.read_bytes()));self.assertEqual((out/'dist/index.html').read_text(),'ok')
 def test_archive_digest(self):
  f=self.archive([('release.json','{}'),('dist/index.html','ok')])
  with self.assertRaises(ValueError):extract_bound_archive(f,self.root/'release','0'*64)
 def test_archive_path_boundaries(self):
  for path in ['../x','/absolute','dist/../x','dist/.secret','dist\\escape','dist//index.html','executable.py']:
   with self.subTest(path=path):
    f=self.archive([(path,'x')])
    with self.assertRaises(ValueError):extract_bound_archive(f,self.root/'release',digest(f.read_bytes()))
 def test_archive_symlink(self):
  i=zipfile.ZipInfo('dist/link');i.create_system=3;i.external_attr=(stat.S_IFLNK|0o777)<<16;f=self.archive([(i,'/tmp')])
  with self.assertRaises(ValueError):extract_bound_archive(f,self.root/'release',digest(f.read_bytes()))
 def test_archive_duplicate(self):
  import warnings
  with warnings.catch_warnings():warnings.simplefilter('ignore');f=self.archive([('release.json','{}'),('release.json','{}')])
  with self.assertRaises(ValueError):extract_bound_archive(f,self.root/'release',digest(f.read_bytes()))
 def test_existing_destination(self):
  f=self.archive([('release.json','{}'),('dist/index.html','ok')]);d=self.root/'release';d.mkdir()
  with self.assertRaises(ValueError):extract_bound_archive(f,d,digest(f.read_bytes()))
 def test_no_local_runner(self):
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaises(ValueError):verify_runner()
 def test_request_origin_and_method(self):
  self.assertTrue(allowed_request('http://127.0.0.1:1234/','GET','http://127.0.0.1:1234'))
  for url,method in [('https://example.com/','GET'),('http://127.0.0.1:1235/','GET'),('http://localhost:1234/','GET'),('http://a@127.0.0.1:1234/','GET'),('http://127.0.0.1:1234/','POST'),('file:///tmp','GET')]:self.assertFalse(allowed_request(url,method,'http://127.0.0.1:1234'))
 def test_server_nonloopback(self):
  with self.assertRaises(AssertionError):SafeServer(('0.0.0.0',0),None)
 def test_path_traversal(self):
  for p in ['/../x','/%2e%2e/x','/.git/config','//example.com/x','/x\\y']:
   with self.subTest(path=p):
    with self.assertRaises((ValueError,FileNotFoundError)):resolve_request(self.root,p)
 def test_missing_capture_grid(self):
  with self.assertRaises(ValueError):validate_capture([],{'routes':['/'],'captureRoutes':['/']},self.root)
 def test_focus_obstruction(self):
  f={'viewportWidth':375,'viewportHeight':812,'visible':True,'width':343,'height':171.5,'left':16,'right':359,'top':200,'bottom':371.5,'safeTop':60,'safeBottom':750,'hitTests':[True]*9};assert_focus(f,375,812)
  f['hitTests'][0]=False
  with self.assertRaises(ValueError):assert_focus(f,375,812)
 def test_focus_clipping(self):
  f={'viewportWidth':375,'viewportHeight':812,'visible':True,'width':343,'height':171.5,'left':16,'right':359,'top':10,'bottom':181.5,'safeTop':60,'safeBottom':750,'hitTests':[True]*9}
  with self.assertRaises(ValueError):assert_focus(f,375,812)
 def test_rendered_dom_semantic_mutations(self):
  proof={'sourceSha':'a'*40,'origin':'https://site.example','thinHubRoutes':[],'exactAlts':{k:k+' 1844-0644'for k in ['message','budget','consultation']}}
  f={'url':'http://127.0.0.1:1234/','viewport':375,'scrollWidth':375,'revision':'a'*40,'canonical':['https://site.example/'],'h1':['title'],'title':'title','description':'description','robots':'index,follow','sharedImageCount':3,'removedCaptionOccurrences':0,'fontStatus':'loaded','images':[{'complete':True,'width':1774,'height':887,'alt':'image'}], 'banners':[{'kind':k,'imageCount':1,'captionCount':0,'src':'/images/shared-banners/flower-'+k+'.webp','alt':proof['exactAlts'][k],'naturalWidth':1774,'naturalHeight':887,'complete':True,'width':343,'height':171.5,'loading':'lazy','decoding':'async','visible':True}for k in ['message','budget','consultation']]}
  assert_facts(f,proof,'/','http://127.0.0.1:1234',375)
  for key,value in [('alt','wrong 1844-0644'),('captionCount',1),('naturalWidth',1),('width',300),('loading','eager'),('complete',False),('src','/other.webp')]:
   with self.subTest(key=key):
    bad=deepcopy(f);bad['banners'][0][key]=value
    with self.assertRaises(ValueError):assert_facts(bad,proof,'/','http://127.0.0.1:1234',375)
  for key,value in [('removedCaptionOccurrences',1),('revision','b'*40),('robots','noindex,follow'),('sharedImageCount',4),('scrollWidth',400),('canonical',['https://wrong.example/'])]:
   with self.subTest(key=key):
    bad=deepcopy(f);bad[key]=value
    with self.assertRaises(ValueError):assert_facts(bad,proof,'/','http://127.0.0.1:1234',375)
 def test_api_evidence_strips_personal_and_unknown_fields(self):
  raw=deepcopy(self.run);raw.update(head_commit={'author':{'email':'FORBIDDEN_EMAIL@example.invalid','name':'FORBIDDEN_NAME'}},node_id='FORBIDDEN_NODE',unrelated='FORBIDDEN_UNKNOWN')
  raw['actor'].update(email='FORBIDDEN_ACTOR_EMAIL',avatar_url='FORBIDDEN_AVATAR',node_id='FORBIDDEN_ACTOR_NODE')
  raw['repository'].update(owner={'email':'FORBIDDEN_OWNER_EMAIL'},description='FORBIDDEN_DESCRIPTION')
  raw['triggering_actor'].update(avatar_url='FORBIDDEN_TRIGGER_AVATAR')
  summary=summarize_run(raw)
  self.assertEqual(set(summary),{'id','status','conclusion','head_sha','head_branch','path','event','run_attempt','html_url','actorLogin','triggeringActorLogin','repository'})
  self.assertNotIn('FORBIDDEN',json.dumps(summary));self.assertEqual(summary['actorLogin'],'joseungil-kr')
  artifact=deepcopy(self.artifact);artifact.update(node_id='FORBIDDEN_NODE',creator={'email':'FORBIDDEN_EMAIL'},archive_download_url='FORBIDDEN_DOWNLOAD_URL');artifact['workflow_run'].update(node_id='FORBIDDEN_WORKFLOW_NODE',actor={'email':'FORBIDDEN_EMAIL'})
  a=summarize_artifact(artifact);self.assertEqual(set(a),{'id','name','size_in_bytes','digest','expired','url','workflow_run'});self.assertEqual(set(a['workflow_run']),{'id','head_sha','head_branch'});self.assertNotIn('FORBIDDEN',json.dumps(a))
 def test_capture_never_copies_raw_api_to_evidence(self):
  code=(HERE/'capture.py').read_text();self.assertIn("write_json(output/'build-run-api.json',summarize_run(run))",code);self.assertIn("write_json(output/'build-artifact-api.json',summarize_artifact(artifact))",code)
 def test_readonly_workflow(self):
  workflow=(HERE.parents[1]/'workflows/shared-banner-phone-artifact-qa.yml').read_text()
  self.assertIn('contents: read',workflow);self.assertIn('actions: read',workflow)
  for token in ['contents: write','actions: write','CLOUDFLARE_API_TOKEN','AIRTABLE','git push','wrangler deploy']:self.assertNotIn(token,workflow)

if __name__=='__main__':unittest.main()
