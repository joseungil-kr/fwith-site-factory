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

class EnvelopeDiagnostics(unittest.TestCase):
 def transport(self,obj):
  helper=R2Regressions();opener=helper.opener([obj]);return helper.transport(opener),opener
 def test_expected_endpoint_labels_only(self):
  expected=['account','scripts-list','domains-list','script-settings','script-exposure','active-deployment-list','selected-deployment','selected-version']
  for path,label in zip(fixtures(),expected):
   with self.subTest(label=label):
    report=b.envelope_diagnostic(ACCOUNT,path,ok({}));self.assertEqual(report['endpoint'],label)
    for forbidden in [ACCOUNT,DEP,VID,SCRIPT]:self.assertNotIn(forbidden,json.dumps(report))
  for path in ['https://evil.test/private','/accounts/'+ACCOUNT+'/workers/scripts/other/settings',SCRIPT+'/versions/not-uuid',SCRIPT+'/versions/'+VID+'?secret=value']:
   with self.subTest(path=path),self.assertRaisesRegex(ValueError,'^diagnostic_endpoint_label_unavailable$'):b.envelope_diagnostic(ACCOUNT,path,{})
 def test_presence_types_and_validation_flags_only(self):
  obj={'success':False,'errors':[{'code':123,'message':'fixture-private-error'}],'messages':['fixture-private-message'],'result':{'secret':'fixture-private-result'},'unknown-fixture-private-key':'fixture-private-value'}
  report=b.envelope_diagnostic(ACCOUNT,'/accounts/'+ACCOUNT,obj)
  self.assertEqual(report['expectedFields'],{'success':{'present':True,'type':'boolean'},'errors':{'present':True,'type':'array'},'messages':{'present':True,'type':'array'},'result':{'present':True,'type':'object'},'result_info':{'present':False,'type':'absent'}})
  self.assertEqual(report['checks'],{'object':True,'onlyAllowedTopLevelKeys':False,'successIsTrue':False,'errorsIsEmptyArray':False,'resultPresent':True,'messagesAbsentOrArray':True})
  self.assertNotIn('fixture-private',json.dumps(report));self.assertNotIn('123',json.dumps(report));self.assertTrue(all(type(v) is bool for v in report['checks'].values()))
 def test_response_types_never_echo_values(self):
  for obj,typ in [(None,'null'),(False,'boolean'),(123,'number'),(1.5,'number'),('fixture-private','string'),(['fixture-private'],'array'),({'fixture-private':'fixture-private'},'object')]:
   with self.subTest(type=typ):
    report=b.envelope_diagnostic(ACCOUNT,'/accounts/'+ACCOUNT,obj);self.assertEqual(report['responseType'],typ);self.assertNotIn('fixture-private',json.dumps(report));self.assertNotIn('123',json.dumps(report))
 def test_exact_original_envelope_predicate_preserved(self):
  variants=[ok({}),{**ok({}),'messages':[]},{**ok({}),'result_info':{}},None,[],False,'fixture-private']
  for key in ['success','errors','messages','result','result_info','unknown-fixture-private-key']:
   for value in [None,False,True,0,1,'fixture-private',[],['fixture-private'],{}, {'fixture-private':'fixture-private'}]:
    obj=ok({});obj[key]=value;variants.append(obj)
   obj=ok({});obj.pop(key,None);variants.append(obj)
  for i,obj in enumerate(variants):
   old=(type(obj) is dict and set(obj)<={'success','errors','messages','result','result_info'} and obj.get('success') is True and obj.get('errors')==[] and 'result' in obj and ('messages' not in obj or type(obj['messages']) is list))
   with self.subTest(case=i):
    get,opener=self.transport(obj)
    if old:self.assertEqual(get('/accounts/'+ACCOUNT),obj)
    else:
     with self.assertRaises(b.ProviderEnvelopeError) as caught:get('/accounts/'+ACCOUNT)
     self.assertEqual(str(caught.exception),'provider_response_unverified');self.assertNotIn('fixture-private',json.dumps(caught.exception.diagnostic));self.assertNotIn(ACCOUNT,json.dumps(caught.exception.diagnostic))
    self.assertEqual(len(opener.requests),1);self.assertEqual(opener.requests[0].get_method(),'GET');self.assertIsNone(opener.requests[0].data)
 def test_dynamic_endpoint_error_uses_only_selected_label(self):
  helper=R2Regressions();f=fixtures();opener=helper.opener([f[SCRIPT+'/deployments?page=1&per_page=1'],{'success':False,'errors':['fixture-private'],'result':None}]);get=helper.transport(opener);get(SCRIPT+'/deployments?page=1&per_page=1')
  with self.assertRaises(b.ProviderEnvelopeError) as caught:get(SCRIPT+'/versions/'+VID)
  self.assertEqual(caught.exception.diagnostic['endpoint'],'selected-version');self.assertNotIn(VID,json.dumps(caught.exception.diagnostic));self.assertEqual(len(opener.requests),2)
 def test_cli_failure_retains_only_safe_diagnostic_and_exit_one(self):
  diag=b.envelope_diagnostic(ACCOUNT,'/accounts/'+ACCOUNT,{'success':False,'errors':['fixture-private'],'result':None})
  with tempfile.TemporaryDirectory() as td:
   output=Path(td)/'failure.json'
   with patch.object(b.sys,'argv',['provider_baseline.py','observe','--report',str(output)]),patch.dict(b.os.environ,{'GITHUB_EVENT_PATH':'synthetic-event.json'}),patch.object(b,'load_policy'),patch.object(b,'read',return_value=b'{}'),patch.object(b,'observe',side_effect=b.ProviderEnvelopeError(diag)),patch('sys.stdout',new_callable=io.StringIO) as stdout:
    self.assertEqual(b.main(),1)
   report=json.loads(output.read_text());self.assertEqual(report,{'state':'BLOCKED_WITH_NO_PROVIDER_MUTATION','code':'provider_response_unverified','providerMutationsPerformed':False,'baselineAccepted':False,'diagnostic':diag});self.assertNotIn('fixture-private',output.read_text()+stdout.getvalue())
 def test_other_failures_do_not_gain_diagnostic_or_raw_messages(self):
  for error,code in [(ValueError('safe_code'),'safe_code'),(ValueError('fixture private error'),'ValueError'),(RuntimeError('fixture-private'),'RuntimeError')]:
   with self.subTest(code=code),tempfile.TemporaryDirectory() as td:
    output=Path(td)/'failure.json'
    with patch.object(b.sys,'argv',['provider_baseline.py','observe','--report',str(output)]),patch.dict(b.os.environ,{'GITHUB_EVENT_PATH':'synthetic-event.json'}),patch.object(b,'load_policy'),patch.object(b,'read',return_value=b'{}'),patch.object(b,'observe',side_effect=error),patch('sys.stdout',new_callable=io.StringIO) as stdout:self.assertEqual(b.main(),1)
    report=json.loads(output.read_text());self.assertEqual(report['code'],code);self.assertNotIn('diagnostic',report);self.assertNotIn('fixture',output.read_text()+stdout.getvalue())
 def test_success_output_does_not_gain_diagnostic(self):
  expected={'state':'OBSERVED_NOT_ACCEPTED_FOR_MUTATION','baselineAccepted':False,'publicationEligible':False}
  with tempfile.TemporaryDirectory() as td:
   output=Path(td)/'observation.json'
   with patch.object(b.sys,'argv',['provider_baseline.py','observe','--report',str(output)]),patch.dict(b.os.environ,{'GITHUB_EVENT_PATH':'synthetic-event.json'}),patch.object(b,'load_policy'),patch.object(b,'read',return_value=b'{}'),patch.object(b,'observe',return_value=expected),patch('sys.stdout',new_callable=io.StringIO):self.assertEqual(b.main(),0)
   self.assertEqual(json.loads(output.read_text()),expected)

class DomainNullEnvelopeCompatibility(unittest.TestCase):
 def nullable(self):return {'success':True,'errors':None,'messages':None,'result':[],'result_info':{}}
 def transport(self,objects):
  helper=R2Regressions();opener=helper.opener(objects);return helper.transport(opener),opener
 def test_exact_observed_shape_retains_nulls_and_records_boolean(self):
  obj=self.nullable();obj['result']=[{'fixture':'do-not-retain-in-observation'}];original=copy.deepcopy(obj);get,opener=self.transport([obj]);self.assertEqual(get.envelope_compatibility,{'domainsListNullPairObserved':False});actual=get('/accounts/'+ACCOUNT+'/workers/domains');self.assertEqual(actual,original);self.assertIsNone(actual['errors']);self.assertIsNone(actual['messages']);self.assertEqual(get.envelope_compatibility,{'domainsListNullPairObserved':True});self.assertEqual(len(opener.requests),1);self.assertEqual(opener.requests[0].get_method(),'GET');self.assertIsNone(opener.requests[0].data)
 def test_no_general_nullable_error_fallback(self):
  for path in fixtures():
   if path=='/accounts/'+ACCOUNT+'/workers/domains':continue
   with self.subTest(path=path):
    self.assertFalse(b.domain_null_envelope(ACCOUNT,path,self.nullable()))
    if '/versions/' in path or re_match_selected(path):continue
    get,_=self.transport([self.nullable()])
    with self.assertRaises(b.ProviderEnvelopeError):get(path)
    self.assertFalse(get.envelope_compatibility['domainsListNullPairObserved'])
 def test_exact_five_keys_and_typed_null_pair_required(self):
  variants=[]
  for key in self.nullable():
   obj=self.nullable();obj.pop(key);variants.append(obj)
  obj=self.nullable();obj['fixture-private-extra']='fixture-private';variants.append(obj)
  for key in ['errors','messages']:
   for value in [False,0,'',{},[],['fixture-private']]:
    obj=self.nullable();obj[key]=value;variants.append(obj)
  for value in [False,0,1,'true',None,[],{}]:
   obj=self.nullable();obj['success']=value;variants.append(obj)
  for key in ['result','result_info']:
   for value in [None,False,0,'fixture-private',{'fixture-private':'fixture-private'} if key=='result' else []]:
    obj=self.nullable();obj[key]=value;variants.append(obj)
  for i,obj in enumerate(variants):
   with self.subTest(case=i):
    self.assertFalse(b.domain_null_envelope(ACCOUNT,'/accounts/'+ACCOUNT+'/workers/domains',obj));get,_=self.transport([obj])
    with self.assertRaises(b.ProviderEnvelopeError) as caught:get('/accounts/'+ACCOUNT+'/workers/domains')
    self.assertFalse(get.envelope_compatibility['domainsListNullPairObserved']);self.assertNotIn('fixture-private',json.dumps(caught.exception.diagnostic))
 def test_prior_array_representation_still_unchanged(self):
  for obj in [ok([]),{**ok([]),'messages':[],'result_info':{}}]:
   with self.subTest(has_messages='messages' in obj):
    get,_=self.transport([obj]);self.assertEqual(get('/accounts/'+ACCOUNT+'/workers/domains'),obj);self.assertFalse(get.envelope_compatibility['domainsListNullPairObserved'])
 def test_null_domain_envelope_does_not_bypass_pagination(self):
  variants=[{'page':2},{'total_pages':2},{'total_count':2},{'count':2},{'page':True},{'total_count':True},{'count':False},{'per_page':0},{'cursor':'fixture-private'}]
  for info in variants:
   with self.subTest(info=info):
    obj=self.nullable();obj['result']=[{}];obj['result_info']=info;get,_=self.transport([obj]);raw=get('/accounts/'+ACCOUNT+'/workers/domains')
    with self.assertRaises(ValueError):b.single_page(raw)
 def state_transport(self,domain_mutation=None):
  f=fixtures();key='/accounts/'+ACCOUNT+'/workers/domains';f[key].update(errors=None,messages=None,result_info={})
  if domain_mutation:domain_mutation(f[key])
  paths=['/accounts/'+ACCOUNT,'/accounts/'+ACCOUNT+'/workers/scripts',key,SCRIPT+'/settings',SCRIPT+'/subdomain',SCRIPT+'/deployments?page=1&per_page=1',SCRIPT+'/deployments/'+DEP,SCRIPT+'/versions/'+VID,SCRIPT+'/deployments?page=1&per_page=1'];get,opener=self.transport([f[path] for path in paths]);return get,opener
 def test_full_synthetic_state_still_requires_exact_domain_identity(self):
  mutations=[lambda obj:obj['result'][0].update(hostname='other.example'),lambda obj:obj['result'][0].update(service='other-worker'),lambda obj:obj['result'][0].update(zone_name='other.example'),lambda obj:obj['result'][0].update(enabled=False),lambda obj:obj['result'][0].update(previews_enabled=True),lambda obj:obj['result'].clear(),lambda obj:obj['result'].append(copy.deepcopy(obj['result'][0])),lambda obj:obj['result'][0].update(id='invalid'),lambda obj:obj.update(result_info={'total_pages':2})]
  for i,mutation in enumerate(mutations):
   with self.subTest(case=i):
    get,_=self.state_transport(mutation)
    with patch.object(b,'ACCOUNT_SHA',SHA),self.assertRaises(ValueError):b.current_state(ACCOUNT,get)
 def test_full_synthetic_state_retains_existing_normalized_projection(self):
  get,opener=self.state_transport()
  with patch.object(b,'ACCOUNT_SHA',SHA):actual=b.current_state(ACCOUNT,get);expected=b.current_state(ACCOUNT,get_for(fixtures()))
  self.assertEqual(actual,expected);self.assertEqual(len(opener.requests),9);self.assertTrue(get.envelope_compatibility['domainsListNullPairObserved'])
 def test_observation_reports_compatibility_without_acceptance(self):
  get,_=self.state_transport();get.envelope_compatibility['domainsListNullPairObserved']=True
  env,event=Authorization().case()
  with patch.object(b,'trusted_control'),patch.object(b,'provider_get',return_value=(ACCOUNT,get)),patch.object(b,'current_state',return_value={'syntheticState':True}),patch.object(b,'old_public',return_value={'checkedPaths':17,'unknownHttpStatus':404}),patch.object(b,'save'):
   report=b.observe(env,event)
  self.assertEqual(report['providerEnvelopeCompatibility'],{'domainsListNullPairObserved':True});self.assertFalse(report['baselineAccepted']);self.assertFalse(report['publicationEligible']);self.assertFalse(report['providerMutationsPerformed']);self.assertFalse(report['IndexNowSubmitted']);self.assertEqual(report['providerMethods'],['GET']);self.assertEqual(report['state'],'OBSERVED_NOT_ACCEPTED_FOR_MUTATION')

def re_match_selected(path):
 return '/deployments/' in path

class StateShapeDiagnostics(unittest.TestCase):
 def env(self):return {'CLOUDFLARE_ACCOUNT_ID':ACCOUNT,'CLOUDFLARE_API_TOKEN':'fixture-token'}
 def paths(self):return ['/accounts/'+ACCOUNT,'/accounts/'+ACCOUNT+'/workers/scripts','/accounts/'+ACCOUNT+'/workers/domains',SCRIPT+'/settings',SCRIPT+'/subdomain',SCRIPT+'/deployments?page=1&per_page=1',SCRIPT+'/deployments/'+DEP,SCRIPT+'/versions/'+VID]
 def run_sweep(self,f=None,responses=None):
  f=f or fixtures();opener=R2Regressions().opener(responses if responses is not None else [f[path] for path in self.paths()])
  with patch.object(b,'ACCOUNT_SHA',SHA):result=b.state_diagnostic_sweep(self.env(),opener)
  return result,opener
 def assert_safe(self,value):
  if type(value) is dict:
   for k,v in value.items():self.assertIs(type(k),str);self.assert_safe(v)
  else:self.assertIn(type(value),(bool,str))
 def test_full_sweep_is_bounded_get_only_never_baseline(self):
  result,op=self.run_sweep();self.assertEqual(len(op.requests),8);self.assertEqual(result['state'],'BOUNDED_DIAGNOSTIC_SWEEP_FINISHED_NOT_A_BASELINE');self.assert_safe(result)
  for request in op.requests:self.assertEqual(request.get_method(),'GET');self.assertIsNone(request.data)
  for flag in ('baselineAccepted','publicationEligible','providerMutationsPerformed'):self.assertFalse(result[flag])
  raw=json.dumps(result)
  for forbidden in [ACCOUNT,DEP,VID,'fixture-token','not-retained','do-not-retain','do-not-use-as-assets-digest']:self.assertNotIn(forbidden,raw)
 def test_bad_opaque_id_is_diagnosed_without_acceptance_or_pattern_change(self):
  f=fixtures();f['/accounts/'+ACCOUNT+'/workers/domains']['result'][0].update(id='opaque-fixture-value-not-a-uuid',zone_id='A'*64)
  with patch.object(b,'ACCOUNT_SHA',SHA),self.assertRaisesRegex(ValueError,'opaque_domain_zone_identity_required'):b.current_state(ACCOUNT,get_for(f))
  result,op=self.run_sweep(f);self.assertEqual(len(op.requests),8);fields=result['endpoints']['domains-list']['shape']['fields'];self.assertFalse(fields['domainIdPattern']['currentOpaquePattern']);self.assertFalse(fields['zoneIdPattern']['currentOpaquePattern']);self.assertTrue(fields['zoneIdPattern']['hex64']);self.assertNotIn('opaque-fixture',json.dumps(result));self.assertFalse(result['baselineAccepted'])
 def test_prefix_identity_failures_stop_all_later_requests(self):
  cases=[(lambda f:f['/accounts/'+ACCOUNT]['result'].update(id='other'),1),(lambda f:f['/accounts/'+ACCOUNT+'/workers/scripts']['result'].clear(),2),(lambda f:f['/accounts/'+ACCOUNT+'/workers/domains']['result'][0].update(service='other'),3),(lambda f:f['/accounts/'+ACCOUNT+'/workers/domains']['result'][0].update(zone_name='other'),3),(lambda f:f['/accounts/'+ACCOUNT+'/workers/domains'].update(result_info={'total_pages':2}),3)]
  for mutate,n in cases:
   with self.subTest(requests=n):
    f=fixtures();mutate(f);result,op=self.run_sweep(f);self.assertEqual(len(op.requests),n);self.assertFalse(result['baselineAccepted']);self.assertEqual(result['endpoints']['selected-version']['status'],'not_requested')
 def test_every_transport_or_envelope_failure_stops_without_retry(self):
  for i in range(8):
   for bad in [b'not-json',{'success':False,'errors':[],'result':{}},{'success':True,'errors':['fixture-private'],'result':{}}]:
    with self.subTest(index=i,bad=type(bad).__name__):
     f=fixtures();responses=[f[path] for path in self.paths()];responses[i]=bad;result,op=self.run_sweep(responses=responses);self.assertEqual(len(op.requests),i+1);self.assertEqual(result['state'],'request_or_selection_gate_failed');self.assertNotIn('fixture-private',json.dumps(result))
 def test_all_http_and_network_failures_stop_without_retry(self):
  for status in [301,401,403,404,429,500]:
   with self.subTest(status=status),patch.object(b,'ACCOUNT_SHA',SHA):
    op=R2Regressions().opener([ok({})],status=status);result=b.state_diagnostic_sweep(self.env(),op);self.assertEqual(len(op.requests),1);self.assertEqual(result['state'],'request_or_selection_gate_failed')
  class Failed:
   def __init__(self):self.requests=[]
   def open(self,request,timeout):self.requests.append(request);raise RuntimeError('fixture-private-transport')
  op=Failed()
  with patch.object(b,'ACCOUNT_SHA',SHA):result=b.state_diagnostic_sweep(self.env(),op)
  self.assertEqual(len(op.requests),1);self.assertNotIn('fixture-private',json.dumps(result))
 def test_invalid_active_selection_keeps_snapshot_and_zero_dynamic_calls(self):
  for percentage in [50,True,None,'100']:
   with self.subTest(percentage=percentage):
    f=fixtures();f[SCRIPT+'/deployments?page=1&per_page=1']['result']['deployments'][0]['versions'][0]['percentage']=percentage;result,op=self.run_sweep(f);self.assertEqual(len(op.requests),6);row=result['endpoints']['active-deployment-list'];self.assertEqual(row['status'],'selection_rejected_stop');self.assertFalse(row['shape']['checks']['unchangedActiveIdentityPasses']);self.assertEqual(result['endpoints']['selected-deployment']['status'],'not_requested');self.assertEqual(result['endpoints']['selected-version']['status'],'not_requested')
 def test_recorder_disabled_in_normal_transport_and_resets_before_failure(self):
  with patch.object(b,'ACCOUNT_SHA',SHA),patch.object(b,'provider_shape_diagnostic',side_effect=RuntimeError('must not run')):
   get=b.provider_get(self.env(),R2Regressions().opener([ok({'id':ACCOUNT})]))[1];self.assertEqual(get('/accounts/'+ACCOUNT),ok({'id':ACCOUNT}));self.assertFalse(hasattr(get,'shape_snapshot'))
  op=R2Regressions().opener([ok({'id':ACCOUNT}),b'bad-json'])
  with patch.object(b,'ACCOUNT_SHA',SHA):get=b.provider_get(self.env(),op,diagnostic=True)[1]
  get('/accounts/'+ACCOUNT);self.assertEqual(get.shape_snapshot['endpoint'],'account')
  with self.assertRaises(ValueError):get('/accounts/'+ACCOUNT+'/workers/scripts')
  self.assertIsNone(get.shape_snapshot);self.assertFalse(get.diagnostic_transport_passed)
 def test_projection_failure_is_fixed_and_preserves_original_failure(self):
  with patch.object(b,'provider_shape_diagnostic',side_effect=RuntimeError('fixture-private')):result,op=self.run_sweep()
  self.assertEqual(len(op.requests),1);self.assertEqual(result['state'],'request_or_selection_gate_failed');self.assertNotIn('fixture-private',json.dumps(result))
  with patch.object(b,'current_state',side_effect=ValueError('opaque_domain_zone_identity_required')),patch.object(b,'state_diagnostic_sweep',return_value=result),self.assertRaises(b.ProviderStateDiagnosticError) as caught:b.state_with_diagnostics(self.env(),ACCOUNT,lambda p:None)
  self.assertEqual(caught.exception.original_code,'opaque_domain_zone_identity_required');self.assertFalse(caught.exception.diagnostic['baselineAccepted'])
 def test_wrapper_never_sweeps_for_transport_envelope_unknown_or_other_exceptions(self):
  failures=[ValueError('provider_get_failed_no_response_disclosed'),ValueError('provider_get_http_status'),ValueError('provider_json_invalid'),ValueError('provider_get_endpoint_forbidden'),b.ProviderEnvelopeError({'safe':True}),ValueError('private provider text'),RuntimeError('private')]
  for failure in failures:
   with self.subTest(kind=type(failure).__name__),patch.object(b,'current_state',side_effect=failure),patch.object(b,'state_diagnostic_sweep') as sweep,self.assertRaises(type(failure)):b.state_with_diagnostics(self.env(),ACCOUNT,None)
   sweep.assert_not_called()
 def test_all_fixed_fields_project_types_and_booleans_without_values_or_aliases(self):
  canary='fixture-secret-canary-123';samples=[None,False,0,1,3.5,'',canary,[],[canary],{}, {'unknown-private-key':canary}]
  for path in fixtures():
   for value in samples:
    with self.subTest(path=path,value=type(value).__name__):
     obj=ok(copy.deepcopy(value));original=copy.deepcopy(obj);out=b.provider_shape_diagnostic(ACCOUNT,path,obj);self.assertEqual(obj,original);self.assert_safe(out);serialized=json.dumps(out);self.assertNotIn(canary,serialized);self.assertNotIn('unknown-private-key',serialized);self.assertNotIn(ACCOUNT,serialized)
  f=fixtures()
  for path,obj in f.items():
   original=copy.deepcopy(obj);out=b.provider_shape_diagnostic(ACCOUNT,path,obj);self.assertEqual(obj,original);obj.clear();self.assert_safe(out);self.assertNotIn('not-retained',json.dumps(out))
 def test_later_state_anomalies_are_shape_only_not_silently_accepted(self):
  f=fixtures();f[SCRIPT+'/settings']['result'].update(tags=None,tail_consumers=None,logpush=None);f[SCRIPT+'/versions/'+VID]['result'].update(startup_time_ms=1,annotations={'private':'fixture-secret'});f[SCRIPT+'/versions/'+VID]['result']['resources']['script'].update(handlers=None,placement_mode='fixture-private');f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime'].update(containers=[{'value':'fixture-secret'}]);result,op=self.run_sweep(f);self.assertEqual(len(op.requests),8);self.assertFalse(result['endpoints']['script-settings']['shape']['checks']['existingSettingsProjectionExactlyExpected']);self.assertFalse(result['endpoints']['selected-version']['shape']['checks']['onlyPriorVersionKeys']);self.assertFalse(result['endpoints']['selected-version']['shape']['checks']['staticHandlersAllowed']);self.assertNotIn('fixture-secret',json.dumps(result));self.assertNotIn('fixture-private',json.dumps(result));self.assertFalse(result['baselineAccepted'])
 def test_main_retains_original_failure_and_only_safe_diagnostics(self):
  diagnostic={'schema':'fixture-safe','baselineAccepted':False};failure=b.ProviderStateDiagnosticError('opaque_domain_zone_identity_required',diagnostic)
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'report.json'
   with patch.object(b.sys,'argv',['provider_baseline.py','observe','--report',str(p)]),patch.dict(b.os.environ,{'GITHUB_EVENT_PATH':'fixture-event'}),patch.object(b,'load_policy'),patch.object(b,'read',return_value=b'{}'),patch.object(b,'observe',side_effect=failure),patch('sys.stdout',new_callable=io.StringIO):self.assertEqual(b.main(),1)
   report=json.loads(p.read_text());self.assertEqual(report['code'],'opaque_domain_zone_identity_required');self.assertEqual(report['stateDiagnostics'],diagnostic);self.assertFalse(report['baselineAccepted']);self.assertNotIn('currentProviderState',report)

 def test_selected_identity_mismatch_stops_and_suppresses_nested_attribution(self):
  for endpoint,n in [('selected-deployment',7),('selected-version',8)]:
   with self.subTest(endpoint=endpoint):
    f=fixtures();path=SCRIPT+'/deployments/'+DEP if endpoint=='selected-deployment' else SCRIPT+'/versions/'+VID;f[path]['result']['id']='33333333-3333-3333-3333-333333333333';result,op=self.run_sweep(f);self.assertEqual(len(op.requests),n);self.assertEqual(result['endpoints'][endpoint]['status'],'identity_mismatch_stop')
    if endpoint=='selected-deployment':self.assertEqual(result['endpoints']['selected-version']['status'],'not_requested')
    else:self.assertNotIn('resources',result['endpoints'][endpoint]['shape']['fields']);self.assertNotIn('metadata',result['endpoints'][endpoint]['shape']['fields']);self.assertFalse(result['endpoints'][endpoint]['shape']['checks']['versionIdMatchesRequested'])
 def test_unexpected_sweep_exception_cannot_replace_original_failure(self):
  with patch.object(b,'current_state',side_effect=ValueError('opaque_domain_zone_identity_required')),patch.object(b,'state_diagnostic_sweep',side_effect=RuntimeError('fixture-private-failure')),self.assertRaises(b.ProviderStateDiagnosticError) as caught:b.state_with_diagnostics(self.env(),ACCOUNT,None)
  self.assertEqual(caught.exception.original_code,'opaque_domain_zone_identity_required');self.assertEqual(caught.exception.diagnostic['state'],'diagnostic_unexpected_failure');self.assertNotIn('fixture-private',json.dumps(caught.exception.diagnostic))
 def test_empty_inventory_and_missing_domain_checks_are_explicit(self):
  for path in ['/accounts/'+ACCOUNT+'/workers/scripts','/accounts/'+ACCOUNT+'/workers/domains']:
   out=b.provider_shape_diagnostic(ACCOUNT,path,ok([]));self.assertFalse(out['checks']['rowsNonempty'])
   if path.endswith('/domains'):self.assertFalse(out['checks']['selectedDomainChecksEvaluated']);self.assertNotIn('environmentAllowed',out['checks'])

 def test_missing_or_malformed_parent_checks_are_unevaluated_not_true(self):
  version_path=SCRIPT+'/versions/'+VID
  for parent in [None,False,0,'fixture-private',[],{}]:
   with self.subTest(parent=type(parent).__name__):
    f=fixtures();f[version_path]['result']['resources']=parent;out=b.provider_shape_diagnostic(ACCOUNT,version_path,f[version_path]);real=type(parent) is dict
    for key in ('onlyPriorScriptKeys','staticHandlersAllowed','namedHandlersAllowed','etagAbsentOrAllowedPattern','onlyPriorRuntimeKeys','exportsAbsentOrExactEmpty','limitsAbsentOrExactEmpty','migration_tagAbsentOrExactEmpty'):
     self.assertEqual(out['checkEvaluated'][key],real)
     if not real:self.assertNotIn(key,out['checks'])
    self.assertEqual(out['checks']['scriptDefaultUsed'],real);self.assertEqual(out['checks']['runtimeDefaultUsed'],real)
  for parent in [None,False,0,'fixture-private',[]]:
   out=b.provider_shape_diagnostic(ACCOUNT,SCRIPT+'/settings',ok(parent))
   for key in ('observabilityAbsentOrExactDisabled','migrationsAbsentOrEmpty'):
    self.assertFalse(out['checkEvaluated'][key]);self.assertNotIn(key,out['checks'])
 def test_wrong_optional_script_runtime_objects_do_not_use_empty_defaults(self):
  path=SCRIPT+'/versions/'+VID
  for key,check,default in [('script','staticHandlersAllowed','scriptDefaultUsed'),('script_runtime','exportsAbsentOrExactEmpty','runtimeDefaultUsed')]:
   for value in [None,False,0,'fixture-private',[]]:
    with self.subTest(member=key,value=type(value).__name__):
     f=fixtures();f[path]['result']['resources'][key]=value;out=b.provider_shape_diagnostic(ACCOUNT,path,f[path]);self.assertFalse(out['checkEvaluated'][check]);self.assertNotIn(check,out['checks']);self.assertFalse(out['checks'][default]);self.assertNotIn('fixture-private',json.dumps(out))
 def test_runtime_settings_comparison_requires_real_parent_or_valid_default(self):
  path=SCRIPT+'/versions/'+VID
  for value in [None,False,0,'fixture-private',[]]:
   f=fixtures();f[path]['result']['resources']=value;out,op=self.run_sweep(f);self.assertEqual(len(op.requests),8)
   for key in ('compatibility_date','compatibility_flags','usage_model'):
    name='runtime_'+key+'_AbsentOrMatchesSettings';self.assertFalse(out['checkEvaluated'][name]);self.assertNotIn(name,out['checks'])

if __name__=='__main__':unittest.main(verbosity=2)
