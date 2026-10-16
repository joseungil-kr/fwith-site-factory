import copy,hashlib,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import provider_baseline as b
ACCOUNT='a'*32;DEP='11111111-1111-1111-1111-111111111111';VID='22222222-2222-2222-2222-222222222222';SHA=b.sha(ACCOUNT.encode());SCRIPT='/accounts/'+ACCOUNT+'/workers/scripts/'+b.WORKER
SETTINGS={'bindings':[],'compatibility_date':'2026-10-09','compatibility_flags':[],'logpush':False,'placement':{},'tags':[],'tail_consumers':[],'usage_model':'standard'}
def ok(x,info=None):
 r={'success':True,'errors':[],'result':x}
 if info is not None:r['result_info']=info
 return r
def fixtures():
 active={'id':DEP,'created_on':'2026-10-16T02:58:20Z','source':'api','strategy':'percentage','versions':[{'version_id':VID,'percentage':100}],'author_email':'not-retained@example.test','annotations':{'workers/message':'not-retained-user-string'}}
 return {'/accounts/'+ACCOUNT:ok({'id':ACCOUNT,'name':'not-retained'}),'/accounts/'+ACCOUNT+'/workers/scripts':ok([{'id':b.WORKER}]),'/accounts/'+ACCOUNT+'/workers/domains':ok([{'id':'3'*32,'hostname':b.HOST,'service':b.WORKER,'zone_id':'4'*32,'zone_name':'fwith.kr','environment':'production'}]),SCRIPT+'/settings':ok(copy.deepcopy(SETTINGS)),SCRIPT+'/subdomain':ok({'enabled':False,'previews_enabled':False}),SCRIPT+'/deployments?page=1&per_page=1':ok({'deployments':[active]},{'page':1,'per_page':1,'count':1,'total_count':1,'total_pages':1}),SCRIPT+'/deployments/'+DEP:ok(copy.deepcopy(active)),SCRIPT+'/versions/'+VID:ok({'id':VID,'number':1,'metadata':{'created_on':'2026-10-16T02:58:19Z','source':'wrangler','author_email':'not-retained@example.test','author_id':'do-not-retain'},'resources':{'bindings':[],'script':{'etag':'do-not-use-as-assets-digest'},'script_runtime':{'compatibility_date':'2026-10-09'}}})}
def get_for(f,seen=None):
 def get(path):
  if seen is not None:seen.append(path)
  return copy.deepcopy(f[path])
 return get
class Positive(unittest.TestCase):
 def test_exact_current_projection_has_no_sensitive_values(self):
  with patch.object(b,'ACCOUNT_SHA',SHA):x=b.current_state(ACCOUNT,get_for(fixtures()))
  raw=json.dumps(x);self.assertEqual(x['activeDeployment']['versionIdSHA256'],b.sha(VID.encode()));self.assertFalse(x['activeDeployment']['versionIdentityIsAssetDigest']);self.assertNotIn(ACCOUNT,raw)
  for s in [DEP,VID,'not-retained','do-not-retain','do-not-use-as-assets-digest','author_email','author_id','annotations']:self.assertNotIn(s,raw)
 def test_endpoint_exact_allowlist(self):
  for p in fixtures():self.assertTrue(b.allowed_path(ACCOUNT,p,{'deployments':DEP,'versions':VID}),p)
 def test_active_read_twice_and_detail(self):
  seen=[];b.deployed_version(get_for(fixtures(),seen),ACCOUNT,SETTINGS);self.assertEqual(seen.count(SCRIPT+'/deployments?page=1&per_page=1'),2);self.assertIn(SCRIPT+'/versions/'+VID,seen)
 def test_empty_single_page(self):self.assertEqual(b.single_page(ok([],{'total_pages':0})),[])
 def test_historical_policy_actual_bytes(self):self.assertFalse(b.load_policy()['historicalVersionKnown'])
 def test_strict_managed_robots_pin(self):self.assertEqual(b.sha((b.D/'managed_robots.py').read_bytes()),'51eebc7dc9a405ade4c5f7da6cdb086a8319d2df690b5b9429e20bd764cbdee5')
class Rejects(unittest.TestCase):
 def test_endpoint_rejections(self):
  paths=['https://evil.test/'+SCRIPT,'//evil.test/'+SCRIPT,SCRIPT+'/../secrets',SCRIPT+'/versions/'+VID+'?x=1',SCRIPT+'/versions/'+VID+'#x',SCRIPT+'/versions/AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',SCRIPT+'/domains/records',SCRIPT+'/settings?x=1','/accounts/'+ACCOUNT+'/workers/domains?page=1&per_page=100','/accounts/'+ACCOUNT+'/workers/scripts?page=1&per_page=100',SCRIPT+'/deployments',SCRIPT+'/deployments?page=2&per_page=1',SCRIPT+'/deployments?page=1&per_page=20',SCRIPT+'/versions','/zones','/accounts/'+ACCOUNT+'/workers/workers/x/versions/'+VID,SCRIPT.replace(b.WORKER,'other-worker')+'/settings',SCRIPT+'/settings%3Fx=1']
  for p in paths:
   with self.subTest(p=p):
    try:r=b.allowed_path(ACCOUNT,p)
    except ValueError:r=False
    self.assertFalse(r)
 def test_missing_or_split_traffic(self):
  for value in [[],[{'version_id':VID,'percentage':50}],[{'version_id':VID,'percentage':True}],[{'version_id':VID,'percentage':100},{'version_id':DEP,'percentage':0}], [{'version_id':'invalid','percentage':100}]]:
   f=fixtures();f[SCRIPT+'/deployments?page=1&per_page=1']['result']['deployments'][0]['versions']=value
   with self.subTest(value=value),self.assertRaises(ValueError):b.deployed_version(get_for(f),ACCOUNT,SETTINGS)
 def test_empty_and_multi_active_rows(self):
  for mode in ['empty','multi']:
   f=fixtures();rows=f[SCRIPT+'/deployments?page=1&per_page=1']['result']['deployments'];rows.clear() if mode=='empty' else rows.append(copy.deepcopy(rows[0]))
   with self.subTest(mode=mode),self.assertRaises(ValueError):b.deployed_version(get_for(f),ACCOUNT,SETTINGS)
 def test_deployment_and_version_schema(self):
  mutations=[lambda f:f[SCRIPT+'/deployments/'+DEP]['result'].update(id=VID),lambda f:f[SCRIPT+'/versions/'+VID]['result'].update(id=DEP),lambda f:f[SCRIPT+'/versions/'+VID]['result'].update(assets={'jwt':'do-not-persist'}),lambda f:f[SCRIPT+'/versions/'+VID]['result']['resources'].update(bindings=[{'name':'SECRET','value':'do-not-persist'}]),lambda f:f[SCRIPT+'/versions/'+VID]['result']['resources'].update(assets={'jwt':'do-not-persist'}),lambda f:f[SCRIPT+'/versions/'+VID]['result'].update(number=True),lambda f:f[SCRIPT+'/versions/'+VID]['result']['metadata'].update(source='private note'),lambda f:f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime'].update(exports=['private']),lambda f:f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime'].update(migration_tag='x')]
  for i,mut in enumerate(mutations):
   f=fixtures();mut(f)
   with self.subTest(i=i),self.assertRaises(ValueError):b.deployed_version(get_for(f),ACCOUNT,SETTINGS)
 def test_current_state_identity_and_settings_rejections(self):
  mutations=[lambda f:f['/accounts/'+ACCOUNT]['result'].update(id='b'*32),lambda f:f['/accounts/'+ACCOUNT+'/workers/scripts']['result'].clear(),lambda f:f['/accounts/'+ACCOUNT+'/workers/scripts']['result'].append({'id':b.WORKER}),lambda f:f['/accounts/'+ACCOUNT+'/workers/domains']['result'][0].update(service='other'),lambda f:f['/accounts/'+ACCOUNT+'/workers/domains']['result'].append(copy.deepcopy(f['/accounts/'+ACCOUNT+'/workers/domains']['result'][0])),lambda f:f['/accounts/'+ACCOUNT+'/workers/domains']['result'][0].update(hostname=b.HOST.upper()),lambda f:f['/accounts/'+ACCOUNT+'/workers/domains']['result'][0].update(zone_name='other.test'),lambda f:f['/accounts/'+ACCOUNT+'/workers/domains']['result'][0].update(previews_enabled=True),lambda f:f[SCRIPT+'/subdomain']['result'].update(enabled=True),lambda f:f[SCRIPT+'/subdomain']['result'].pop('previews_enabled'),lambda f:f[SCRIPT+'/settings']['result'].update(bindings=[{'name':'SECRET','value':'do-not-persist'}]),lambda f:f[SCRIPT+'/settings']['result'].update(tags=['do-not-persist']),lambda f:f[SCRIPT+'/settings']['result'].update(compatibility_date='2026-01-01')]
  for i,mut in enumerate(mutations):
   f=fixtures();mut(f)
   with self.subTest(i=i),patch.object(b,'ACCOUNT_SHA',SHA),self.assertRaises(ValueError):b.current_state(ACCOUNT,get_for(f))
 def test_incomplete_inventory(self):
  for info in [{'page':True},{'total_count':True},{'page':2},{'count':2},{'total_count':2},{'total_pages':2},{'per_page':0}]:
   with self.subTest(info=info),self.assertRaises(ValueError):b.single_page(ok([{}],info))
 def test_account_digest_before_transport(self):
  with self.assertRaises(ValueError):b.provider_get({'CLOUDFLARE_ACCOUNT_ID':ACCOUNT,'CLOUDFLARE_API_TOKEN':'dummy'})
 def test_active_race(self):
  f=fixtures();count=0
  def get(path):
   nonlocal count
   x=copy.deepcopy(f[path])
   if path.endswith('per_page=1'):
    count+=1
    if count==2:x['result']['deployments'][0]['id']=VID
   return x
  with self.assertRaises(ValueError):b.deployed_version(get,ACCOUNT,SETTINGS)
class Authorization(unittest.TestCase):
 def case(self):
  env={'GITHUB_REPOSITORY':b.REPO,'GITHUB_REF':'refs/heads/main','GITHUB_ACTOR':b.OWNER,'GITHUB_TRIGGERING_ACTOR':b.OWNER,'GITHUB_RUN_ATTEMPT':'1','GITHUB_EVENT_NAME':'issues','GITHUB_SHA':'a'*40,'GITHUB_RUN_ID':'123'}
  body={'schemaVersion':1,'mode':'read-only-existing-provider-baseline','previous_source_revision':b.PREVIOUS,'correction_source_revision':b.CURRENT,'expected_control_revision':env['GITHUB_SHA'],'baseline_policy_sha256':b.POLICY_SHA}
  event={'action':'opened','repository':{'full_name':b.REPO,'owner':{'login':b.OWNER,'type':'User'}},'issue':{'number':123,'title':b.TITLE,'user':{'login':b.OWNER},'body':json.dumps(body)}};return env,event
 def test_exact_owner_readonly(self):env,event=self.case();self.assertFalse(b.authorize(env,event)['providerMutationsPerformed'])
 def test_env_mutations(self):
  for k,v in [('GITHUB_REPOSITORY','other/repo'),('GITHUB_REF','refs/heads/topic'),('GITHUB_ACTOR','other'),('GITHUB_TRIGGERING_ACTOR','other'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_EVENT_NAME','workflow_dispatch'),('GITHUB_SHA','x'),('GITHUB_RUN_ID','0')]:
   env,event=self.case();env[k]=v
   with self.subTest(k=k),self.assertRaises(ValueError):b.authorize(env,event)
 def test_request_mutations(self):
  for k,v in [('schemaVersion',True),('mode','publish'),('previous_source_revision',b.CURRENT),('correction_source_revision',b.PREVIOUS),('expected_control_revision','b'*40),('baseline_policy_sha256','b'*64),('extra',True)]:
   env,event=self.case();body=json.loads(event['issue']['body']);body[k]=v;event['issue']['body']=json.dumps(body)
   with self.subTest(k=k),self.assertRaises(ValueError):b.authorize(env,event)

class Transport(unittest.TestCase):
 def test_actual_request_shape_get_only(self):
  class Response:
   from email.message import Message
   headers=Message();headers['Content-Type']='application/json'
   status=200
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def read(self,limit):return json.dumps(ok({'id':ACCOUNT})).encode()
  class Opener:
   def __init__(self):self.requests=[]
   def open(self,request,timeout):self.requests.append(request);return Response()
  opener=Opener()
  with patch.object(b,'ACCOUNT_SHA',SHA):_,get=b.provider_get({'CLOUDFLARE_ACCOUNT_ID':ACCOUNT,'CLOUDFLARE_API_TOKEN':'fixture-token'},opener)
  get('/accounts/'+ACCOUNT);self.assertEqual(len(opener.requests),1);req=opener.requests[0];self.assertEqual(req.get_method(),'GET');self.assertIsNone(req.data)
  with self.assertRaises(ValueError):get(SCRIPT+'/domains/records')
  self.assertEqual(len(opener.requests),1)
 def test_transport_failure_does_not_expose_secret(self):
  class Opener:
   def open(self,*a,**k):raise RuntimeError('fixture-token private body')
  with patch.object(b,'ACCOUNT_SHA',SHA):_,get=b.provider_get({'CLOUDFLARE_ACCOUNT_ID':ACCOUNT,'CLOUDFLARE_API_TOKEN':'fixture-token'},Opener())
  with self.assertRaisesRegex(ValueError,'^provider_get_failed_no_response_disclosed$'):get('/accounts/'+ACCOUNT)
 def test_redirect_refused(self):self.assertIsNone(b.NoRedirect().redirect_request(None,None,None,None,None,None))

class PublicBefore(unittest.TestCase):
 def fixture(self):
  import previous_public as p
  from email.message import Message
  files={};responses={};pages=[]
  for file,route in [('index.html','/'),('regions/index.html','/regions/'),('regions/suwan-funeral-wreath/index.html','/regions/suwan-funeral-wreath/'),('404.html','/404.html')]:
   robots='noindex,follow' if route in ['/regions/','/404.html'] else 'index,follow';head='<meta name="site-factory-revision" content="'+b.PREVIOUS+'"><meta name="robots" content="'+robots+'">'
   if route!='/404.html':head+='<link rel="canonical" href="'+p.ORIGIN+route+'"><meta property="og:url" content="'+p.ORIGIN+route+'">'
   links='<a href="tel:18440644">call</a><a href="/regions/suwan-funeral-wreath/">detail</a>'+''.join('<a href="https://fwith.co.kr/shop/item.php?it_id='+sku+'">product</a>' for sku in ['B201','B203','B205','B060'])
   raw=('<!doctype html><html><head>'+head+'</head><body>'+links+'</body></html>').encode();files[file]=b.sha(raw);headers=Message();headers['Content-Type']='text/html'
   responses[route]=(raw,headers,404 if route=='/404.html' else 200)
   if route!='/404.html':pages.append({'file':file,'path':route,'url':p.ORIGIN+route,'robots':robots.split(',')})
  assets=['_astro/style.css','favicon.svg',*[f'images/products/{sku}.jpg' for sku in ['B060','B201','B203','B205']],*[f'images/shared-banners/{n}.webp' for n in ['budget','message','consultation']],p.PROOF_PATH,'robots.txt','sitemap-0.xml','sitemap-index.xml']
  for name in assets:
   raw=('synthetic '+name).encode();headers=Message();headers['Content-Type']={'.css':'text/css','.svg':'image/svg+xml','.jpg':'image/jpeg','.webp':'image/webp','.xml':'application/xml','.txt':'text/plain'}[Path(name).suffix];files[name]=b.sha(raw);responses['/'+name]=(raw,headers,200)
  files['_headers']=b.sha(b'fixture headers')
  contract={'origin':p.ORIGIN,'revision':b.PREVIOUS,'ownershipFile':p.PROOF_PATH,'pages':pages,'files':files,'sitemapUrls':sorted(p.ORIGIN+n for n in p.SITEMAP_ROUTES)}
  def get(path,status=200):
   if path.startswith('/.gwangsan-release-missing-'):path='/404.html'
   raw,h,s=responses[path];self.assertEqual(s,status);return raw,h
  return p,contract,responses,get
 def test_full_generated_seventeen_path_fixture(self):
  p,c,r,get=self.fixture()
  with tempfile.TemporaryDirectory() as td,patch.object(p,'get',get),patch.object(p.managed_robots,'verify_headers'),patch.object(p.managed_robots,'verify',return_value={'state':'synthetic_exact'}),patch.object(p,'save'),patch.object(Path,'write_bytes'):
   result=p.http_once(c)
  self.assertEqual(result['checkedPaths'],17);self.assertEqual(result['unknownHttpStatus'],404)
 def test_wrong_asset_and_wrong_404_are_rejected(self):
  for target in ['/images/products/B201.jpg','/404.html']:
   p,c,r,get=self.fixture();raw,h,s=r[target];r[target]=(raw+b'changed',h,s)
   with self.subTest(target=target),patch.object(p,'get',get),patch.object(p.managed_robots,'verify_headers'),patch.object(p.managed_robots,'verify',return_value={}),patch.object(p,'save'),patch.object(Path,'write_bytes'),self.assertRaises((ValueError,AssertionError)):p.http_once(c)
 def test_wrong_prior_revision_rejected(self):
  p,c,r,get=self.fixture();raw,h,s=r['/'];r['/']=(raw.replace(b.PREVIOUS.encode(),b.CURRENT.encode()),h,s)
  with patch.object(p,'get',get),self.assertRaises(ValueError):p.http_once(c)
 def test_policy_requires_all_original_output_hashes(self):
  p=b.load_policy();c=json.loads(b.read(b.ROOT/p['previousPublicContractPath']));self.assertEqual(len(c['files']),18);self.assertEqual(c['revision'],b.PREVIOUS)
class R2Regressions(unittest.TestCase):
 def state(self,f=None):
  with patch.object(b,'ACCOUNT_SHA',SHA):return b.current_state(ACCOUNT,get_for(f or fixtures()))
 def test_single_page_unknown_and_false_pagination(self):
  for info in [False,[],0,None,{'cursor':'NEXT'},{'next_cursor':'NEXT'},{'has_more':False},{'next_page':1},{'page':True},{'total_pages':False},{'count':True},{'total_count':False},{'per_page':True}]:
   obj=ok([{}]);obj['result_info']=info
   with self.subTest(info=info),self.assertRaises(ValueError):b.single_page(obj)
  for key in ['cursor','next_cursor','has_more','next_page']:
   obj=ok([{}]);obj[key]=False
   with self.subTest(top=key),self.assertRaises(ValueError):b.single_page(obj)
 def test_deployment_pagination_rejects_booleans_and_unknowns(self):
  for info in [False,[],0,None,*[{key:True} for key in ['page','per_page','count','total_count','total_pages']],{'cursor':'NEXT'},{'next_page':2},{'count':2},{'per_page':2},{'total_count':0},{'total_pages':0}]:
   f=fixtures();f[SCRIPT+'/deployments?page=1&per_page=1']['result_info']=info
   with self.subTest(info=info),self.assertRaises(ValueError):b.deployed_version(get_for(f),ACCOUNT,SETTINGS)
 def test_historical_deployment_pages_are_not_current_split_traffic(self):
  f=fixtures();f[SCRIPT+'/deployments?page=1&per_page=1']['result_info'].update(total_count=20,total_pages=20)
  self.assertEqual(b.deployed_version(get_for(f),ACCOUNT,SETTINGS)['trafficPercentage'],100)
 def test_domain_missing_flags_not_invented_and_worker_exposure_explicit(self):
  x=self.state();self.assertEqual(x['hostnameBinding']['optionalObservedFields'],{'environment':'production'});self.assertEqual(x['workersDev'],{'enabled':False,'previews_enabled':False})
  f=fixtures();f['/accounts/'+ACCOUNT+'/workers/domains']['result'][0].update(enabled=True,previews_enabled=False)
  y=self.state(f);self.assertNotEqual(b.digest(x),b.digest(y));self.assertEqual(y['hostnameBinding']['optionalObservedFields']['enabled'],True)
 def test_domain_optional_certificate_validated_but_not_retained(self):
  f=fixtures();f['/accounts/'+ACCOUNT+'/workers/domains']['result'][0]['cert_id']='c'*32
  x=self.state(f);self.assertNotIn('cert_id',json.dumps(x));self.assertNotIn('c'*32,json.dumps(x))
  for val in [None,False,[],{},'', 'private text with spaces', 'x'*129]:
   f['/accounts/'+ACCOUNT+'/workers/domains']['result'][0]['cert_id']=val
   with self.subTest(value=val),self.assertRaises(ValueError):self.state(f)
 def test_missing_and_invalid_worker_exposure_rejected(self):
  for key in ['enabled','previews_enabled']:
   for value in [None,0,1,'false',[],{}]:
    f=fixtures();f[SCRIPT+'/subdomain']['result'][key]=value
    with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.state(f)
   f=fixtures();del f[SCRIPT+'/subdomain']['result'][key]
   with self.assertRaises(ValueError):self.state(f)
 def test_active_runtime_mismatch_and_presence(self):
  for key,value in [('compatibility_date','1900-01-01'),('compatibility_flags',['nodejs_compat']),('compatibility_flags',{}),('usage_model','bundled')]:
   f=fixtures();f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime'][key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.state(f)
  original=self.state();f=fixtures();runtime=f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime'];runtime['compatibility_flags']=[];runtime['usage_model']='standard';present=self.state(f)
  self.assertNotEqual(b.digest(original),b.digest(present));self.assertEqual(present['activeDeployment']['versionRuntime']['fields'],{'compatibility_date':'2026-10-09','compatibility_flags':[],'usage_model':'standard'})
  del f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime'];absent=self.state(f);f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime']={};empty=self.state(f);self.assertNotEqual(b.digest(absent),b.digest(empty))
 def test_exact_settings_boolean_types_before_unchanged_helper(self):
  for key,values in [('logpush',[0,1,None,'false',[],{}]),('observability',[{'enabled':0},{'enabled':1},{'enabled':None},{'enabled':'false'},{'enabled':False,'logs':{}},False,{},None])]:
   for value in values:
    f=fixtures();f[SCRIPT+'/settings']['result'][key]=value
    with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.state(f)
  f=fixtures();f[SCRIPT+'/settings']['result']['observability']={'enabled':False};self.assertEqual(self.state(f)['settings'],SETTINGS)
 def test_safe_script_projection_and_conservative_capabilities(self):
  f=fixtures();script=f[SCRIPT+'/versions/'+VID]['result']['resources']['script'];script.update(handlers=['fetch'],named_handlers=[],last_deployed_from='wrangler');x=self.state(f)
  self.assertEqual(x['activeDeployment']['versionScript'],{'present':True,'fields':{'handlers':['fetch'],'named_handlers':[],'etagPresent':True,'last_deployed_fromPresent':True}});self.assertNotIn('do-not-use-as-assets-digest',json.dumps(x))
  original=copy.deepcopy(script)
  for key,values in [('handlers',[False,'fetch',{},['fetch','fetch'],['scheduled'],['unknown'],[1]]),('named_handlers',[{},False,[{'x':[]}]]),('etag',[None,1,[],{},'x'*129,'private text']),('last_deployed_from',[None,True,[],{},'x'*65,'private text'])]:
   for value in values:
    f[SCRIPT+'/versions/'+VID]['result']['resources']['script']={**original,key:value}
    with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.state(f)
  del f[SCRIPT+'/versions/'+VID]['result']['resources']['script'];absent=self.state(f);f[SCRIPT+'/versions/'+VID]['result']['resources']['script']={};empty=self.state(f);self.assertNotEqual(b.digest(absent),b.digest(empty));self.assertFalse(absent['activeDeployment']['versionScript']['present'])
 def test_documented_empty_runtime_exports_map(self):
  f=fixtures();f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime']['exports']={};self.assertEqual(self.state(f)['activeDeployment']['versionRuntime']['fields']['exports'],{})
  for value in [[],False,None,{'secret':'not-retained'}]:
   f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime']['exports']=value
   with self.subTest(value=value),self.assertRaises(ValueError):self.state(f)
 def test_provider_paths_never_normalized(self):
  for path in [' '+SCRIPT+'/settings',SCRIPT+'/settings ',SCRIPT+'/settings?',SCRIPT+'/settings\n',SCRIPT+'/set\ttings',SCRIPT+'/set\rtings','\x00'+SCRIPT+'/settings',SCRIPT+'/settings\x7f',SCRIPT+'/deployments?page=1&per_page=1\n']:
   with self.subTest(path=path),self.assertRaises(ValueError):b.allowed_path(ACCOUNT,path)
 def test_domain_and_zone_ids_must_be_opaque_identifiers(self):
  for key in ['id','zone_id']:
   for value in ['private identity text','abc','x'*32,'3'*31,'3'*33,'3'*32+'\n',[],None,True]:
    f=fixtures();f['/accounts/'+ACCOUNT+'/workers/domains']['result'][0][key]=value
    with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.state(f)
  f=fixtures();f['/accounts/'+ACCOUNT+'/workers/domains']['result'][0]['id']=DEP;self.assertEqual(self.state(f)['hostnameBinding']['domainIdSHA256'],b.sha(DEP.encode()))
 def test_digest_only_current_provider_ids(self):
  x=self.state();raw=json.dumps(x);self.assertNotIn(DEP,raw);self.assertNotIn(VID,raw);self.assertEqual(x['activeDeployment']['deploymentIdSHA256'],b.sha(DEP.encode()));self.assertEqual(x['activeDeployment']['versionIdSHA256'],b.sha(VID.encode()))
 def opener(self,responses,mime='application/json',status=200,encoding=None):
  from email.message import Message
  class Response:
   def __init__(self,raw):
    self.status=status;self.raw=raw;self.headers=Message()
    if mime is not None:
     for value in mime if type(mime) is list else [mime]:self.headers['Content-Type']=value
    if encoding:self.headers['Content-Encoding']=encoding
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,limit):return self.raw[:limit]
  class Opener:
   def __init__(self):self.requests=[]
   def open(self,request,timeout):
    self.requests.append(request);item=responses[len(self.requests)-1];return Response(item if type(item) is bytes else json.dumps(item).encode())
  return Opener()
 def transport(self,opener):
  with patch.object(b,'ACCOUNT_SHA',SHA):return b.provider_get({'CLOUDFLARE_ACCOUNT_ID':ACCOUNT,'CLOUDFLARE_API_TOKEN':'fixture-token'},opener)[1]
 def test_dynamic_get_requires_exact_selected_active_ids(self):
  f=fixtures();opener=self.opener([f[SCRIPT+'/deployments?page=1&per_page=1'],f[SCRIPT+'/deployments/'+DEP],f[SCRIPT+'/versions/'+VID]]);get=self.transport(opener)
  for path in [SCRIPT+'/versions/'+VID,SCRIPT+'/deployments/'+DEP]:
   with self.subTest(before=path),self.assertRaises(ValueError):get(path)
  self.assertEqual(len(opener.requests),0);get(SCRIPT+'/deployments?page=1&per_page=1')
  for path in [SCRIPT+'/versions/'+DEP,SCRIPT+'/deployments/'+VID]:
   with self.subTest(unselected=path),self.assertRaises(ValueError):get(path)
  get(SCRIPT+'/deployments/'+DEP);get(SCRIPT+'/versions/'+VID);self.assertEqual(len(opener.requests),3)
 def test_dynamic_selection_does_not_accept_split_traffic(self):
  f=fixtures();f[SCRIPT+'/deployments?page=1&per_page=1']['result']['deployments'][0]['versions'][0]['percentage']=50
  op=self.opener([f[SCRIPT+'/deployments?page=1&per_page=1']]);get=self.transport(op)
  with self.assertRaises(ValueError):get(SCRIPT+'/deployments?page=1&per_page=1')
  with self.assertRaises(ValueError):get(SCRIPT+'/versions/'+VID)
  self.assertEqual(len(op.requests),1)
 def test_json_transport_mime_and_encoding_rejected(self):
  for mime in [None,'text/html','application/jsonx','text/plain',['application/json','application/json']]:
   with self.subTest(mime=mime),self.assertRaises(ValueError):self.transport(self.opener([ok({})],mime))('/accounts/'+ACCOUNT)
  with self.assertRaises(ValueError):self.transport(self.opener([ok({})],encoding='gzip'))('/accounts/'+ACCOUNT)
 def test_json_transport_status_and_envelope_rejected(self):
  with self.assertRaises(ValueError):self.transport(self.opener([ok({})],status=301))('/accounts/'+ACCOUNT)
  for obj in [{'success':True,'result':{}},{'success':True,'errors':False,'result':{}},{'success':True,'errors':[],'result':{},'cursor':'next'},{'success':True,'errors':[],'result':{},'messages':False},{'success':False,'errors':[],'result':{}},b'{"success":true,"success":true,"errors":[],"result":{}}',b'{"success":true,"errors":[],"result":NaN}',b'not json',b'x'*(1024*1024+1)]:
   with self.subTest(value=str(obj)[:100]),self.assertRaises(ValueError):self.transport(self.opener([obj]))('/accounts/'+ACCOUNT)
 def test_public_mime_exact_extension_types(self):
  fixture=PublicBefore();p,c,responses,get=fixture.fixture()
  for path,wrong in [('/','text/htmlx'),('/_astro/style.css','text/plain'),('/favicon.svg','image/jpeg'),('/images/products/B201.jpg','image/svg+xml'),('/images/shared-banners/budget.webp','image/jpeg'),('/sitemap-0.xml','text/html'),('/robots.txt','text/html'),('/'+p.PROOF_PATH,'application/json'),('/404.html','text/plain')]:
   raw,headers,status=responses[path];old=headers['Content-Type'];headers.replace_header('Content-Type',wrong)
   with self.subTest(path=path),patch.object(p,'get',get),patch.object(p.managed_robots,'verify_headers'),patch.object(p.managed_robots,'verify',return_value={}),patch.object(p,'save'),patch.object(Path,'write_bytes'),self.assertRaises(ValueError):p.http_once(c)
   headers.replace_header('Content-Type',old)
 def test_public_mime_charset_and_parameters_are_bounded(self):
  import previous_public as p
  from email.message import Message
  for value in ['text/html;charset=utf-16','text/html; charset=latin1','text/html; charset=utf-8; charset=utf-8','text/html; boundary=x','text/html; charset=utf-8, text/plain','text/html\r\n','text/html\x00','text/html; charset=utf-8; foo=bar']:
   h=Message();h['Content-Type']=value
   with self.subTest(value=value),self.assertRaises(ValueError):p.media_type(h,'index.html')
  for value in ['text/html','text/html;charset=utf-8','text/html; charset="utf-8"','TEXT/HTML; CHARSET=UTF-8']:
   h=Message();h['Content-Type']=value;self.assertEqual(p.media_type(h,'index.html'),'text/html')
 def test_public_safe_observations_complete(self):
  p,c,responses,get=PublicBefore().fixture()
  with patch.object(p,'get',get),patch.object(p.managed_robots,'verify_headers'),patch.object(p.managed_robots,'verify',return_value={}),patch.object(p,'save'),patch.object(Path,'write_bytes'):r=p.http_once(c)
  self.assertEqual(len(r['observations']),17);self.assertTrue(all(set(x)<={'path','status','mediaType','bodySHA256','normalizedBodySHA256'} and len(x['bodySHA256'])==64 for x in r['observations']))

if __name__=='__main__':unittest.main(verbosity=2)
