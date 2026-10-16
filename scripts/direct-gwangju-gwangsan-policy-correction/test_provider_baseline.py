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
  for key,values in [('handlers',[False,'fetch',{},['fetch','fetch'],['scheduled'],['unknown'],[1]]),('named_handlers',[{},False,[{'x':[]}]]),('etag',[None,1,[],{}]),('last_deployed_from',[None,True,[],{}])]:
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
  for key in ['zone_id']:
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
  mutations=[lambda obj:obj['result'][0].update(hostname='other.example'),lambda obj:obj['result'][0].update(service='other-worker'),lambda obj:obj['result'][0].update(zone_name='other.example'),lambda obj:obj['result'][0].update(enabled=False),lambda obj:obj['result'][0].update(previews_enabled=True),lambda obj:obj['result'].clear(),lambda obj:obj['result'].append(copy.deepcopy(obj['result'][0])),lambda obj:obj['result'][0].update(id='invalid space'),lambda obj:obj.update(result_info={'total_pages':2})]
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


class CompatibilityContract(unittest.TestCase):
 def state(self,fixture=None):
  with patch.object(b,'ACCOUNT_SHA',SHA):return b.current_state(ACCOUNT,get_for(fixture or fixtures()))
 def domain(self,value):
  f=fixtures();f['/accounts/'+ACCOUNT+'/workers/domains']['result'][0]['id']=value;return f
 def times(self,deployment,version=None):
  f=fixtures();f[SCRIPT+'/deployments?page=1&per_page=1']['result']['deployments'][0]['created_on']=deployment;f[SCRIPT+'/deployments/'+DEP]['result']['created_on']=deployment;f[SCRIPT+'/versions/'+VID]['result']['metadata']['created_on']=version or deployment;return f
 def test_domain_accepts_exact_ascii_graphic_1_to_128(self):
  values=[chr(i) for i in range(33,127)]+['x'*128,'3'*32,DEP,'AbC-._~:/?#[]@!$&\'()*+,;=%','https://elsewhere.test/secret?x=1#part']
  for value in values:
   with self.subTest(value=value):self.assertEqual(self.state(self.domain(value))['hostnameBinding']['domainIdSHA256'],b.sha(value.encode('utf-8')))
 def test_domain_rejects_types_lengths_whitespace_controls_and_nonascii(self):
  class StringSubclass(str):pass
  values=[None,False,True,0,1,1.5,[],{},'',StringSubclass('abc'),'x'*129,'private identity text',' abc','abc ','\u00e9','\uff21','\u200b','\u00a0']+['a'+chr(i)+'b' for i in list(range(33))+[127,128,255]]
  for value in values:
   with self.subTest(value=repr(value)),self.assertRaises(ValueError):self.state(self.domain(value))
 def test_domain_digest_preserves_case_punctuation_and_exact_bytes(self):
  values=['Opaque:ID/a','opaque:ID/a','Opaque:ID/b','Opaque%3AID/a','Opaque:ID/a!'];states=[self.state(self.domain(value)) for value in values]
  self.assertEqual(states[0],self.state(self.domain(values[0])));self.assertEqual(len({b.digest(s) for s in states}),len(values))
  for state,value in zip(states,values):self.assertEqual(state['hostnameBinding']['domainIdSHA256'],b.sha(value.encode()));self.assertNotIn(value,json.dumps(state))
 def test_every_positive_domain_still_requires_fixed_target_and_security_guards(self):
  domain_key='/accounts/'+ACCOUNT+'/workers/domains'
  mutations=[lambda f:f['/accounts/'+ACCOUNT]['result'].update(id='b'*32),lambda f:f['/accounts/'+ACCOUNT+'/workers/scripts']['result'].clear(),lambda f:f['/accounts/'+ACCOUNT+'/workers/scripts']['result'].append({'id':b.WORKER}),lambda f:f[domain_key]['result'][0].update(hostname='other.test'),lambda f:f[domain_key]['result'][0].update(service='other'),lambda f:f[domain_key]['result'][0].update(zone_name='other.test'),lambda f:f[domain_key]['result'].append(copy.deepcopy(f[domain_key]['result'][0])),lambda f:f[domain_key].update(result_info={'total_pages':2}),lambda f:f[domain_key]['result'][0].update(environment='staging'),lambda f:f[domain_key]['result'][0].update(enabled=False),lambda f:f[domain_key]['result'][0].update(previews_enabled=True),lambda f:f[domain_key]['result'][0].update(zone_id='opaque.zone'),lambda f:f[domain_key]['result'][0].update(cert_id='bad cert'),lambda f:f[SCRIPT+'/subdomain']['result'].update(enabled=True),lambda f:f[SCRIPT+'/subdomain']['result'].update(previews_enabled='false'),lambda f:f[SCRIPT+'/settings']['result'].update(bindings=[{'name':'SECRET','value':'secret-canary'}])]
  for value in ['!', 'x'*128,DEP,'opaque:+/%?ID']:
   for i,mutate in enumerate(mutations):
    with self.subTest(value=value,mutation=i):
     f=self.domain(value);mutate(f)
     with self.assertRaises(ValueError):self.state(f)
 def test_opaque_url_like_domain_never_changes_get_paths_or_leaks(self):
  expected=['/accounts/'+ACCOUNT,'/accounts/'+ACCOUNT+'/workers/scripts','/accounts/'+ACCOUNT+'/workers/domains',SCRIPT+'/settings',SCRIPT+'/subdomain',SCRIPT+'/deployments?page=1&per_page=1',SCRIPT+'/deployments/'+DEP,SCRIPT+'/versions/'+VID,SCRIPT+'/deployments?page=1&per_page=1']
  raw='https://example.invalid/private-canary?token=abc#fragment';f=self.domain(raw);op=R2Regressions().opener([f[path] for path in expected])
  with patch.object(b,'ACCOUNT_SHA',SHA):
   account,get=b.provider_get({'CLOUDFLARE_ACCOUNT_ID':ACCOUNT,'CLOUDFLARE_API_TOKEN':'fixture-token'},op);state=b.current_state(account,get)
  self.assertEqual([r.full_url for r in op.requests],['https://api.cloudflare.com/client/v4'+path for path in expected]);self.assertEqual(len(op.requests),9)
  for request in op.requests:self.assertEqual(request.get_method(),'GET');self.assertIsNone(request.data)
  report=b.provider_shape_diagnostic(ACCOUNT,expected[2],f[expected[2]]);self.assertNotIn(raw,json.dumps(state));self.assertNotIn('private-canary',json.dumps(report))
 def test_timestamp_positive_fractions_offsets_calendar_and_rollovers(self):
  import datetime as dt
  for digits in range(10):
   fraction='' if digits==0 else '.'+'123456789'[:digits]
   for zone,offset in [('Z',0),('+00:00',0),('+09:00',540),('-05:30',-330),('+23:59',1439),('-23:59',-1439)]:
    value='2024-02-29T23:59:59'+fraction+zone
    with self.subTest(value=value):
     actual=b.timestamp(value);self.assertEqual(actual.microsecond,int(('123456789'[:digits]).ljust(6,'0')[:6]));self.assertEqual(actual.utcoffset(),dt.timedelta(minutes=offset));self.assertEqual((actual.year,actual.month,actual.day),(2024,2,29))
  pairs=[('2025-01-01T00:00:00+09:00','2024-12-31T15:00:00Z'),('2024-03-01T00:00:00+00:01','2024-02-29T23:59:00Z'),('2024-12-31T23:59:00-00:01','2025-01-01T00:00:00Z')]
  for left,right in pairs:
   with self.subTest(left=left):self.assertEqual(b.timestamp(left),b.timestamp(right))
  for value in ['0001-01-01T00:00:00Z','9999-12-31T23:59:59.999999999Z','2000-02-29T12:30:30Z']:self.assertIsNotNone(b.timestamp(value))
 def test_timestamp_rejects_outside_explicit_profile_with_fixed_error(self):
  class StringSubclass(str):pass
  values=[None,True,0,1.2,[],{},StringSubclass('2026-01-01T00:00:00Z'),'', '2026-01-01','2026-01-01T00:00:00','2026-01-01t00:00:00Z','2026-01-01T00:00:00z','2026-01-01 00:00:00Z','2026-01-01\u202800:00:00Z','20260101T000000Z','2026-W01-1T00:00:00Z','2026-001T00:00:00Z','0000-01-01T00:00:00Z','10000-01-01T00:00:00Z','2025-02-29T00:00:00Z','1900-02-29T00:00:00Z','2026-04-31T00:00:00Z','2026-00-01T00:00:00Z','2026-13-01T00:00:00Z','2026-01-00T00:00:00Z','2026-01-32T00:00:00Z','2026-01-01T24:00:00Z','2026-01-01T00:60:00Z','2026-01-01T00:00:60Z','2026-01-01T00:00:00-00:00','2026-01-01T00:00:00+24:00','2026-01-01T00:00:00+00:60','2026-01-01T00:00:00-24:00','2026-01-01T00:00:00-00:60','2026-01-01T00:00:00.Z','2026-01-01T00:00:00.1234567890Z','2026-01-01T00:00:00,123Z','2026-01-01T00:00.5Z','2026-01-01T00.5Z','2026-01-01T00:00:00+0000','2026-01-01T00:00:00+00','2026-01-01T00:00:00+00:00:00','2026-01-01T00:00:00+00:00.1','２０２６-01-01T00:00:00Z','2026-01-01T00:00:00.١Z','0001-01-01T00:00:00+00:01','9999-12-31T23:59:59-00:01']
  values += [x+'2026-01-01T00:00:00Z' for x in [' ','\t','\r','\n','\0']]+['2026-01-01T00:00:00Z'+x for x in [' ','\t','\r','\n','\0','extra-secret-canary']]
  for value in values:
   with self.subTest(value=repr(value)),self.assertRaisesRegex(ValueError,'^invalid_provider_timestamp$'):b.timestamp(value)
 def test_nanosecond_provider_raw_state_digest_and_equivalent_offsets_stay_distinct(self):
  pairs=[('2026-10-16T02:58:20.123456001Z','2026-10-16T02:58:20.123456999Z'),('2026-10-16T02:58:20.123456789Z','2026-10-16T11:58:20.123456789+09:00')]
  for left,right in pairs:
   with self.subTest(left=left):
    self.assertEqual(b.timestamp(left),b.timestamp(right));a=self.state(self.times(left));z=self.state(self.times(right));self.assertNotEqual(a,z);self.assertNotEqual(b.digest(a),b.digest(z));self.assertEqual(a['activeDeployment']['deploymentCreatedOn'],left);self.assertEqual(a['activeDeployment']['versionCreatedOn'],left)
    f=self.times(left);f[SCRIPT+'/deployments/'+DEP]['result']['created_on']=right
    with self.assertRaisesRegex(ValueError,'active_deployment_detail_changed'):self.state(f)
    f=self.times(left);count=0
    def get(path):
     nonlocal count
     obj=copy.deepcopy(f[path])
     if path==SCRIPT+'/deployments?page=1&per_page=1':
      count+=1
      if count==2:obj['result']['deployments'][0]['created_on']=right
     return obj
    with patch.object(b,'ACCOUNT_SHA',SHA),self.assertRaisesRegex(ValueError,'active_deployment_changed_during_observation'):b.current_state(ACCOUNT,get)
    env,event=Authorization().case()
    with patch.object(b,'trusted_control'),patch.object(b,'provider_get',return_value=(ACCOUNT,None)),patch.object(b,'state_with_diagnostics',side_effect=[a,z]),patch.object(b,'old_public',return_value={}),self.assertRaisesRegex(ValueError,'provider_changed_across_full_public_check'):b.observe(env,event)
 def test_timestamp_rejection_stops_active_before_dynamic_requests(self):
  for value in ['2026-01-01T00:00:60Z','2026-01-01T00:00:00.1234567890Z','2026-01-01T00:00:00Zsecret-canary']:
   f=self.times(value);op=R2Regressions().opener([f[SCRIPT+'/deployments?page=1&per_page=1']]);get=R2Regressions().transport(op)
   with self.subTest(value=value),self.assertRaisesRegex(ValueError,'^invalid_provider_timestamp$'):get(SCRIPT+'/deployments?page=1&per_page=1')
   for path in [SCRIPT+'/deployments/'+DEP,SCRIPT+'/versions/'+VID]:
    with self.assertRaises(ValueError):get(path)
   self.assertEqual(len(op.requests),1);report,diag=StateShapeDiagnostics().run_sweep(f);self.assertEqual(len(diag.requests),6);self.assertEqual(report['endpoints']['selected-deployment']['status'],'not_requested');self.assertNotIn('secret-canary',json.dumps(report))

class R11FixedDiagnostics(unittest.TestCase):
 DIRECT='annotations assets bindings body_part cache_options compatibility_date compatibility_flags containers created_on etag exports exports_reconciliation handlers has_assets has_modules id keep_assets keep_bindings last_deployed_from limits logpush main_module migration_tag migrations modified_on named_handlers observability package_dependencies placement placement_mode placement_status routes tag tags tail_consumers usage_model'
 RUNTIME='compatibility_date compatibility_flags containers exports limits migration_tag usage_model'
 TOKENS=set(('schema gwangsan-fixed-version-diagnostic/v1 versionMeaningEstablished baselineAccepted outer metadata annotations resources script script_runtime runtime versionFields state fields predicates nested children object parent_wrong_type parent_absent unique_target_after_inventory_gate present type absent null boolean number string array other author_email author_id source hasPreview number startup_time_ms workers/triggered_by workers/message workers/tag enabled head_sampling_rate issues logs redact_query_string traces invocation_logs destinations persist propagation_policy mode region hostname host target config _headers _redirects base_path html_handling not_found_handling run_worker_first serve_directly cross_version_cache cpu_ms subrequests onlyDocumentedOuterUnionKeys onlyDocumentedMetadataKeys onlyDocumentedResourceKeys onlyDocumentedScriptUnionKeys onlyVersionDocumentedRuntimeKeys versionSemanticUnverifiedRuntimeKeysPresent outsideExploratoryMetadataInventoryKeysPresent outsideExploratoryRuntimeInventoryKeysPresent knownPresentAnnotationValuesAreStrings remainingUnknownObjectKeysPresent exactDisabledObject credentialFieldPresent configObject exactFalse exactTrue exactNull exactEmptyArray exactFetchOnly exactEmptyObject exactString exactEmptyString exactNonemptyString exactRoot finiteUnitInterval finiteNonnegative not_evaluated evaluated_false evaluated_true comparisonContext earlier_separate_settings_response_in_same_sweep earlierSettingsOriginalGuardsPassed '+DIRECT).split())
 CANARY='R11_PRIVATE_VALUE_DO_NOT_EMIT'
 UNKNOWN='R11_PRIVATE_UNKNOWN_KEY_DO_NOT_EMIT'
 def version(self):return fixtures()[SCRIPT+'/versions/'+VID]['result']
 def project(self,version=None):return b.provider_shape_diagnostic(ACCOUNT,SCRIPT+'/versions/'+VID,ok(self.version() if version is None else version))['expandedVersion']
 def assert_vocabulary(self,value):
  if type(value) is dict:
   for key,child in value.items():self.assertIn(key,self.TOKENS);self.assert_vocabulary(child)
  elif type(value) is str:self.assertIn(value,self.TOKENS)
  else:self.assertIs(type(value),bool)
 def test_exact_fixed_vocab_and_source_identity(self):
  self.assertEqual(b.R11_EXPLORATORY_FIELDS,self.DIRECT);self.assertEqual(len(self.DIRECT.split()),36);self.assertEqual(b.R11_VERSION_RUNTIME_FIELDS,self.RUNTIME);self.assertEqual(b.CURRENT,'0da9982f8ea294c6fb38729d17e9043d45f7ca72')
 def test_all_36_fields_types_canaries_and_real_parent_status(self):
  samples=[None,False,True,0,1,3.5,'',self.CANARY,[],[self.CANARY],{}, {self.UNKNOWN:self.CANARY}]
  for location in ('metadata','script_runtime'):
   for key in self.DIRECT.split():
    for value in samples:
     with self.subTest(location=location,key=key,kind=type(value).__name__):
      v=self.version();parent=v if location=='metadata' else v['resources'];parent[location]={key:copy.deepcopy(value),self.UNKNOWN:self.CANARY};before=copy.deepcopy(v);out=self.project(v);self.assertEqual(v,before);self.assert_vocabulary(out);raw=json.dumps(out);self.assertNotIn(self.CANARY,raw);self.assertNotIn(self.UNKNOWN,raw)
      node=out['metadata' if location=='metadata' else 'runtime'];self.assertEqual(node['state'],'object');self.assertTrue(node['fields'][key]['present']);self.assertEqual(node['fields'][key]['type'],b.diagnostic_type(value))
 def test_missing_null_empty_and_malformed_parents_remain_distinct(self):
  for key in ('metadata','resources','annotations'):
   for value in [None,False,0,'',[],{},[{}]]:
    with self.subTest(key=key,kind=type(value).__name__):
     v=self.version();v[key]=value;out=self.project(v);self.assert_vocabulary(out);self.assertEqual(out[key]['state'],'object' if type(value) is dict else 'parent_wrong_type')
     if type(value) is not dict:self.assertEqual(out[key]['fields'],{})
   v=self.version();v.pop(key,None);out=self.project(v);self.assertEqual(out[key]['state'],'parent_absent');self.assert_vocabulary(out)
  for key in ('script','script_runtime'):
   for value in [None,False,0,'',[],{}]:
    v=self.version();v['resources'][key]=value;out=self.project(v);node=out['script' if key=='script' else 'runtime'];self.assertEqual(node['state'],'object' if type(value) is dict else 'parent_wrong_type');self.assert_vocabulary(out)
   v=self.version();v['resources'].pop(key,None);self.assertEqual(self.project(v)['script' if key=='script' else 'runtime']['state'],'parent_absent')
 def test_broad_coverage_does_not_establish_version_semantics_or_accept(self):
  for key in self.DIRECT.split():
   for value in [None,{},[],False]:
    with self.subTest(key=key,value=type(value).__name__):
     v=self.version();v['resources']['script_runtime'][key]=value;out=self.project(v)['runtime']['predicates'];self.assertEqual(out['outsideExploratoryRuntimeInventoryKeysPresent'],'evaluated_false');self.assertEqual(out['onlyVersionDocumentedRuntimeKeys'],'evaluated_true' if key in self.RUNTIME.split() else 'evaluated_false');self.assertEqual(out['versionSemanticUnverifiedRuntimeKeysPresent'],'evaluated_false' if key in self.RUNTIME.split() else 'evaluated_true')
     if key not in ('compatibility_date','compatibility_flags','usage_model','exports','limits','migration_tag'):
      f=fixtures();f[SCRIPT+'/versions/'+VID]['result']=v
      with self.assertRaises(ValueError):b.deployed_version(get_for(f),ACCOUNT,SETTINGS)
  v=self.version();v['resources']['script_runtime'][self.UNKNOWN]=None;pred=self.project(v)['runtime']['predicates'];self.assertEqual(pred['outsideExploratoryRuntimeInventoryKeysPresent'],'evaluated_true');self.assertEqual(pred['versionSemanticUnverifiedRuntimeKeysPresent'],'evaluated_true')
 def test_prior_diagnostic_checks_do_not_imply_current_acceptance(self):
  for key,value in [('annotations',{}),('annotations',{'workers/message':self.CANARY,self.UNKNOWN:self.CANARY}),('startup_time_ms',0),('startup_time_ms',1.5)]:
   with self.subTest(key=key):
    v=self.version();v[key]=value;out=self.project(v);self.assertEqual(out['outer']['predicates']['onlyDocumentedOuterUnionKeys'],'evaluated_true');self.assert_vocabulary(out);f=fixtures();f[SCRIPT+'/versions/'+VID]['result']=v
    self.assertNotIn(self.CANARY,json.dumps(b.deployed_version(get_for(f),ACCOUNT,SETTINGS)))
  v=self.version();v[self.UNKNOWN]=self.CANARY;self.assertEqual(self.project(v)['outer']['predicates']['onlyDocumentedOuterUnionKeys'],'evaluated_false')
 def test_annotation_known_values_str_exact_and_unknown_value_unread(self):
  for key in ('workers/triggered_by','workers/message','workers/tag'):
   for value in [None,False,0,1,[],{},'',self.CANARY]:
    with self.subTest(key=key,kind=type(value).__name__):
     v=self.version();v['annotations']={key:value,self.UNKNOWN:object()};out=self.project(v);self.assertEqual(out['annotations']['predicates']['knownPresentAnnotationValuesAreStrings'],'evaluated_true' if type(value) is str else 'evaluated_false');self.assert_vocabulary(out)
 def test_finite_numbers_exclude_bool_and_json_overflow(self):
  for value in [False,True,None,'0',[],{},-1,float('nan'),float('inf'),-float('inf'),json.loads('1e999'),0,1,0.5,10**500]:
   with self.subTest(kind=type(value).__name__):
    expected=type(value) in (int,float) and 0<=value<float('inf');v=self.version();v['startup_time_ms']=value;out=self.project(v);self.assertEqual(out['outer']['predicates']['startup_time_ms']['finiteNonnegative'],'evaluated_true' if expected else 'evaluated_false');self.assert_vocabulary(out)
    for key in ('observability','logs','traces'):
     node=b.diagnostic_r11_nested({key:{'head_sampling_rate':value}},key);self.assertEqual(node['predicates']['head_sampling_rate']['finiteUnitInterval'],'evaluated_true' if type(value) in (int,float) and 0<=value<=1 else 'evaluated_false');self.assert_vocabulary(node)
 def test_every_nested_shape_is_fixed_and_wrong_parent_never_empty_pass(self):
  for key,names in b.R11_NESTED_FIELDS.items():
   for value in [None,False,0,'',[],{}, {name:self.CANARY for name in names.split()}, {self.UNKNOWN:self.CANARY}]:
    with self.subTest(key=key,kind=type(value).__name__):
     out=b.diagnostic_r11_nested({key:value},key);self.assert_vocabulary(out);self.assertNotIn(self.CANARY,json.dumps(out));self.assertNotIn(self.UNKNOWN,json.dumps(out));self.assertEqual(out['state'],'object' if type(value) is dict else 'parent_wrong_type')
     if type(value) is not dict:self.assertEqual(out['predicates']['exactEmptyObject'],'not_evaluated');self.assertEqual(out['predicates']['remainingUnknownObjectKeysPresent'],'not_evaluated')
   self.assertEqual(b.diagnostic_r11_nested({},key)['state'],'parent_absent')
 def test_typed_boolean_and_null_handlers_never_coerced(self):
  for value in [None,0,1,False,True,'false',[],{}]:
   for key in ('logpush','keep_assets','has_assets','has_modules'):
    node=b.diagnostic_r11_exploratory({'script_runtime':{key:value}},'script_runtime');self.assertEqual(node['predicates'][key]['exactFalse'],'evaluated_true' if value is False else 'evaluated_false');self.assertEqual(node['predicates'][key]['exactTrue'],'evaluated_true' if value is True else 'evaluated_false')
   node=b.diagnostic_r11_nested({'observability':{'enabled':value}},'observability');self.assertEqual(node['predicates']['exactDisabledObject'],'evaluated_true' if value is False else 'evaluated_false')
  for value in [None,[],['fetch'],['scheduled'],['fetch','fetch'],False,'fetch',{},[1]]:
   v=self.version();v['resources']['script']['handlers']=value;out=self.project(v);self.assert_vocabulary(out);pred=out['script']['predicates']['handlers'];self.assertEqual(pred['exactNull'],'evaluated_true' if value is None else 'evaluated_false');self.assertEqual(pred['exactEmptyArray'],'evaluated_true' if type(value) is list and not value else 'evaluated_false')
   if value is None:
    f=fixtures();f[SCRIPT+'/versions/'+VID]['result']=v
    self.assertIsNone(b.deployed_version(get_for(f),ACCOUNT,SETTINGS)['versionScript']['fields']['handlers'])
 def test_jwt_membership_without_value_type_or_serialization_access(self):
  class NeverRead(dict):
   def __getitem__(self,key):
    if key=='jwt':raise AssertionError('credential value accessed')
    return super().__getitem__(key)
   def get(self,key,*args):
    if key=='jwt':raise AssertionError('credential value accessed')
    return super().get(key,*args)
   def values(self):raise AssertionError('values accessed')
   def items(self):raise AssertionError('items accessed')
  assets=NeverRead(jwt=object(),config={'run_worker_first':False});real_type=type
  # Instrument an exact-dict boundary to make a value-access attempt observable.
  with patch.object(b,'type',lambda value:dict if real_type(value) is NeverRead else real_type(value),create=True):out=b.diagnostic_r11_nested({'assets':assets},'assets')
  self.assertEqual(out['state'],'object');self.assertEqual(out['predicates']['credentialFieldPresent'],'evaluated_true');self.assertNotIn('jwt',json.dumps(out));self.assert_vocabulary(out)
 def test_nonempty_resource_arrays_are_never_traversed_or_serialized(self):
  class Poison:
   def __eq__(self,other):raise AssertionError('item equality forbidden')
   def __str__(self):raise AssertionError('item string forbidden')
   def __repr__(self):raise AssertionError('item repr forbidden')
  for key in ('bindings','keep_bindings','compatibility_flags','containers','tail_consumers','tags','package_dependencies'):
   node=b.diagnostic_r11_exploratory({'script_runtime':{key:[Poison()]}},'script_runtime');self.assertEqual(node['predicates'][key]['exactEmptyArray'],'evaluated_false');self.assert_vocabulary(node)
  for key in ('logs','traces'):
   node=b.diagnostic_r11_nested({key:{'destinations':[Poison()]}},key);self.assertEqual(node['predicates']['destinations']['exactEmptyArray'],'evaluated_false');self.assert_vocabulary(node)
  self.assertEqual(b.diagnostic_r11_equality([Poison()],[Poison()],'bindings'),'not_evaluated')
 def test_settings_comparison_is_separate_guarded_and_nontraversing(self):
  f=fixtures();v=f[SCRIPT+'/versions/'+VID]['result'];v['resources']['script_runtime'].update(logpush=False,placement={},bindings=[]);v['metadata']['logpush']=False;report,op=StateShapeDiagnostics().run_sweep(f);out=report['earlierSettingsComparison'];self.assertTrue(out['earlierSettingsOriginalGuardsPassed']);self.assertEqual(out['comparisonContext'],'earlier_separate_settings_response_in_same_sweep');self.assertEqual(out['fields']['runtime']['logpush'],'evaluated_true');self.assertEqual(out['fields']['metadata']['logpush'],'evaluated_true');self.assert_vocabulary(out);self.assertEqual(len(op.requests),8)
  f[SCRIPT+'/settings']['result']['logpush']=True;report,_=StateShapeDiagnostics().run_sweep(f);out=report['earlierSettingsComparison'];self.assertFalse(out['earlierSettingsOriginalGuardsPassed']);self.assertEqual(out['fields']['runtime']['logpush'],'evaluated_false')
  for bad in [None,[],{}, {'logpush':False,'bindings':[{'value':self.CANARY}]}]:
   f[SCRIPT+'/settings']['result']=bad;report,_=StateShapeDiagnostics().run_sweep(f);out=report['earlierSettingsComparison'];self.assertFalse(out['earlierSettingsOriginalGuardsPassed']);self.assertEqual(out['fields']['runtime']['bindings'],'not_evaluated');self.assert_vocabulary(out)
 def test_bounded_equality_known_objects_unknown_nonfinite_and_aliasing(self):
  for left,right,kind,expected in [({'enabled':False},{'enabled':False},'observability','evaluated_true'),({'enabled':False},{'enabled':0},'observability','evaluated_false'),({self.UNKNOWN:None},{self.UNKNOWN:None},'placement','not_evaluated'),({'logs':{'destinations':[self.CANARY]}},{'logs':{'destinations':[self.CANARY]}},'observability','not_evaluated'),(float('inf'),float('inf'),'limits','not_evaluated'),([],{},'bindings','evaluated_false'),({'enabled':False},{},'observability','evaluated_false')]:
   with self.subTest(kind=kind):self.assertEqual(b.diagnostic_r11_equality(left,right,kind),expected)
  v=self.version();v['metadata']['assets']={'config':{'_headers':self.CANARY},'jwt':self.CANARY};out=self.project(v);before=copy.deepcopy(out);v.clear();self.assertEqual(out,before);self.assert_vocabulary(out)
 def test_target_projection_requires_account_complete_unique_inventory(self):
  for mutate in [lambda f:f['/accounts/'+ACCOUNT]['result'].update(id='other'),lambda f:f['/accounts/'+ACCOUNT+'/workers/scripts']['result'].append({'id':b.WORKER,'etag':self.CANARY}),lambda f:f['/accounts/'+ACCOUNT+'/workers/scripts'].update(result_info={'total_pages':2}),lambda f:f['/accounts/'+ACCOUNT+'/workers/scripts']['result'].append({'id':None}),lambda f:f['/accounts/'+ACCOUNT+'/workers/scripts']['result'].clear()]:
   f=fixtures();mutate(f);report,op=StateShapeDiagnostics().run_sweep(f);self.assertLessEqual(len(op.requests),2);self.assertNotIn('selectedTarget',json.dumps(report));self.assertNotIn(self.CANARY,json.dumps(report))
  f=fixtures();f['/accounts/'+ACCOUNT+'/workers/scripts']['result']=[{'id':'other','etag':self.CANARY,'has_assets':True},{'id':b.WORKER,'has_assets':False,'has_modules':False}];report,_=StateShapeDiagnostics().run_sweep(f);out=report['endpoints']['scripts-list']['shape']['selectedTarget'];self.assertEqual(out['predicates']['has_assets']['exactFalse'],'evaluated_true');self.assert_vocabulary(out);self.assertNotIn(self.CANARY,json.dumps(report))
 def test_wrong_selected_id_cannot_get_nested_or_settings_attribution(self):
  for bad in [DEP,None,'other',VID.upper()]:
   if bad==VID:continue
   with self.subTest(kind=type(bad).__name__):
    f=fixtures();f[SCRIPT+'/versions/'+VID]['result']['id']=bad;report,op=StateShapeDiagnostics().run_sweep(f);shape=report['endpoints']['selected-version']['shape'];self.assertNotIn('expandedVersion',shape);self.assertNotIn('earlierSettingsComparison',report);self.assertEqual(report['state'],'selected_version_identity_gate_failed');self.assertEqual(len(op.requests),8)
  f=fixtures();f[SCRIPT+'/deployments/'+DEP]['result']['id']=VID;report,op=StateShapeDiagnostics().run_sweep(f);self.assertEqual(len(op.requests),7);self.assertEqual(report['endpoints']['selected-version']['status'],'not_requested')
 def test_new_projector_errors_preserve_original_code_and_get_budget(self):
  for name,count in [('diagnostic_r11_target',2),('diagnostic_r11_version',8),('diagnostic_r11_settings_comparison',8)]:
   with self.subTest(name=name),patch.object(b,name,side_effect=RuntimeError(self.CANARY)):report,op=StateShapeDiagnostics().run_sweep()
   self.assertEqual(len(op.requests),count);self.assertNotIn(self.CANARY,json.dumps(report));self.assertFalse(report['baselineAccepted'])
   with patch.object(b,'current_state',side_effect=ValueError('version_identity_or_schema')),patch.object(b,'state_diagnostic_sweep',return_value=report),self.assertRaises(b.ProviderStateDiagnosticError) as caught:b.state_with_diagnostics(StateShapeDiagnostics().env(),ACCOUNT,None)
   self.assertEqual(caught.exception.original_code,'version_identity_or_schema')
 def test_normal_transport_never_invokes_new_projectors(self):
  with patch.object(b,'diagnostic_r11_version',side_effect=AssertionError('diagnostic invoked')),patch.object(b,'diagnostic_r11_target',side_effect=AssertionError('diagnostic invoked')),patch.object(b,'diagnostic_r11_settings_comparison',side_effect=AssertionError('diagnostic invoked')),patch.object(b,'ACCOUNT_SHA',SHA):
   out=b.current_state(ACCOUNT,get_for(fixtures()));self.assertEqual(out['hostname'],b.HOST);self.assertNotIn('expandedVersion',json.dumps(out))
 def test_total_normal_plus_diagnostic_get_bound_is_26(self):
  f=fixtures();paths=StateShapeDiagnostics().paths();normal_paths=paths+[SCRIPT+'/deployments?page=1&per_page=1'];responses=[copy.deepcopy(f[path]) for path in normal_paths*2];responses[-1]['result']['deployments'][0]['created_on']='2026-10-16T03:00:00Z';normal=R2Regressions().opener(responses);diagnostic=R2Regressions().opener([f[path] for path in paths])
  with patch.object(b,'ACCOUNT_SHA',SHA),patch.object(b,'build_opener',side_effect=[normal,diagnostic]),patch.object(b,'load_policy',return_value={}),patch.object(b,'authorize',return_value={}),patch.object(b,'trusted_control'),patch.object(b,'old_public',return_value={}) as public,self.assertRaises(b.ProviderStateDiagnosticError) as caught:b.observe(StateShapeDiagnostics().env(),{})
  self.assertEqual(caught.exception.original_code,'active_deployment_changed_during_observation');self.assertEqual(len(normal.requests),18);self.assertEqual(len(diagnostic.requests),8);self.assertEqual(len(normal.requests)+len(diagnostic.requests),26);public.assert_called_once()
  for request in normal.requests+diagnostic.requests:self.assertEqual(request.get_method(),'GET');self.assertIsNone(request.data)
 def test_runtime_unknown_metadata_capability_and_strings_remain_rejected(self):
  cases=[('runtime','logpush',False),('runtime','assets',{}),('runtime',self.UNKNOWN,None),('script','placement_mode','off')]
  for location,key,value in cases:
   with self.subTest(location=location,key=key):
    f=fixtures();v=f[SCRIPT+'/versions/'+VID]['result'];parent=v['metadata'] if location=='metadata' else v['resources']['script_runtime' if location=='runtime' else 'script'];parent[key]=value
    with self.assertRaises(ValueError):b.deployed_version(get_for(f),ACCOUNT,SETTINGS)



class R12AssetsPreservation(unittest.TestCase):
 BETA='/accounts/'+ACCOUNT+'/workers/workers/'+b.WORKER+'/versions/'+VID+'?include=modules'
 CANARY='R12-PRIVATE-CANARY-DO-NOT-OUTPUT'
 @classmethod
 def fixtures(cls):
  f=fixtures();v=f[SCRIPT+'/versions/'+VID]['result']
  v['metadata']['unconsumed_field']=cls.CANARY;v.update(annotations={'workers/message':cls.CANARY,'unknown':{'secret':cls.CANARY}},startup_time_ms=0)
  v['resources']['script'].update(handlers=None,etag='',last_deployed_from='')
  v['resources']['script_runtime']['assets']={'unconsumed_internal':cls.CANARY}
  f[cls.BETA]=ok({'id':VID,'number':1,'created_on':v['metadata']['created_on'],'assets':{'config':{'html_handling':'auto-trailing-slash','not_found_handling':'404-page'},'jwt':cls.CANARY},'modules':[{'name':'_headers','content_type':'text/plain','content_base64':'LyoK'},{'name':'private-module-'+cls.CANARY,'content_type':cls.CANARY,'content_base64':cls.CANARY}],'other_unconsumed':cls.CANARY})
  return f
 def state(self,f=None,get=None):
  with patch.object(b,'ACCOUNT_SHA',SHA):return b.current_state(ACCOUNT,get or get_for(f or self.fixtures()))
 def projection(self,f=None):return self.state(f)['activeDeployment']['versionRuntime']['fields']['assetsPreservation']
 def reject(self,f,code):
  with patch.object(b,'state_diagnostic_sweep') as sweep,patch.object(b,'ACCOUNT_SHA',SHA),self.assertRaisesRegex(ValueError,'^'+code+'$') as caught:b.state_with_diagnostics({},ACCOUNT,get_for(f))
  self.assertNotIn(self.CANARY,str(caught.exception))
  if code.startswith('selected_assets_'):sweep.assert_not_called()
 def test_positive_exact_projection_and_coverage(self):
  seen=[];state=self.state(get=get_for(self.fixtures(),seen));active=state['activeDeployment'];p=active['versionRuntime']['fields']['assetsPreservation']
  self.assertEqual(len(seen),10);self.assertEqual(seen[-2],self.BETA);self.assertEqual(seen[-1],SCRIPT+'/deployments?page=1&per_page=1');self.assertEqual(p,{'schema':'gwangsan-selected-version-assets-preservation/v1','configFields':{'html_handling':'auto-trailing-slash','not_found_handling':'404-page'},'headers':'present_exact_source_bytes','redirects':'absent','modulesInventoryProvided':True,'legacyRuntimeAssetsInternalsInspected':False,'otherModuleContentInspected':False,'workerCodeAbsenceProven':False})
  self.assertEqual(active['assetsVersionCreatedOn'],'2026-10-16T02:58:19Z');self.assertIsNone(active['versionScript']['fields']['handlers']);self.assertNotIn('versionResourcesKnownShape',active);self.assertEqual(active['versionResourceCoverage'],{'resourceContainerAndBindingsChecked':True,'knownRuntimeCapabilityGuardsChecked':True,'legacyAssetsInternalsInspected':False,'selectedAssetsConfigCompared':True,'workerCodeInspected':False})
  raw=json.dumps(state)
  for forbidden in (self.CANARY,ACCOUNT,DEP,VID,'unconsumed_field','unconsumed_internal','other_unconsumed','content_base64','jwt','author_email'):self.assertNotIn(forbidden,raw)
 def test_original_assets_absent_path_still_nine_requests(self):
  seen=[];state=self.state(fixtures(),get=get_for(fixtures(),seen));self.assertEqual(len(seen),9);self.assertNotIn(self.BETA,seen);self.assertNotIn('assetsPreservation',state['activeDeployment']['versionRuntime']['fields']);self.assertFalse(state['activeDeployment']['versionResourceCoverage']['selectedAssetsConfigCompared'])
 def test_header_absence_is_distinct_source_noop_equivalence(self):
  f=self.fixtures();present=self.projection(f);f[self.BETA]['result']['modules']=[];absent=self.projection(f)
  self.assertEqual(absent['headers'],'absent_source_noop_equivalent');self.assertNotEqual(present,absent);self.assertNotEqual(b.digest(present),b.digest(absent))
 def test_optional_config_presence_is_preserved_and_not_normalized(self):
  states=[]
  for base in (False,True):
   for first in (False,True):
    f=self.fixtures();config=f[self.BETA]['result']['assets']['config']
    if base:config['base_path']='/'
    if first:config['run_worker_first']=False
    p=self.projection(f);self.assertEqual('base_path' in p['configFields'],base);self.assertEqual('run_worker_first' in p['configFields'],first);states.append(self.state(f))
  self.assertEqual(len({b.digest(s) for s in states}),4)
 def test_null_missing_empty_fetch_handlers_stay_distinct(self):
  states=[]
  for value in ('missing',None,[],['fetch']):
   f=self.fixtures();s=f[SCRIPT+'/versions/'+VID]['result']['resources']['script']
   if value=='missing':s.pop('handlers')
   else:s['handlers']=value
   states.append(self.state(f))
  self.assertEqual(len({b.digest(s) for s in states}),4)
 def test_script_strings_are_type_only_and_discarded(self):
  for name in ('etag','last_deployed_from'):
   for value in ('',' ',self.CANARY,'Unicode 한글','x'*4096):
    with self.subTest(name=name,length=len(value)):
     f=self.fixtures();f[SCRIPT+'/versions/'+VID]['result']['resources']['script'][name]=value;self.assertNotIn(value if value.strip() else self.CANARY,json.dumps(self.state(f)))
   for value in (None,False,0,[],{}):
    f=self.fixtures();f[SCRIPT+'/versions/'+VID]['result']['resources']['script'][name]=value
    with self.subTest(name=name,kind=type(value).__name__),self.assertRaisesRegex(ValueError,'version_script_metadata_type_required'):self.state(f)
 def test_annotation_known_types_and_metric_rejections(self):
  for name in ('workers/message','workers/tag','workers/triggered_by'):
   for value in (None,False,0,[],{}):
    f=self.fixtures();f[SCRIPT+'/versions/'+VID]['result']['annotations'][name]=value
    with self.subTest(name=name,kind=type(value).__name__),self.assertRaisesRegex(ValueError,'version_annotations_type_required'):self.state(f)
  for value in (None,False,[],0,''):
   f=self.fixtures();f[SCRIPT+'/versions/'+VID]['result']['annotations']=value
   with self.subTest(parent=type(value).__name__),self.assertRaisesRegex(ValueError,'version_annotations_type_required'):self.state(f)
  for value in (None,False,True,-1,-0.1,float('nan'),float('inf'),-float('inf'),json.loads('1e999'),'',[],{}):
   f=self.fixtures();f[SCRIPT+'/versions/'+VID]['result']['startup_time_ms']=value
   with self.subTest(metric=repr(value)),self.assertRaisesRegex(ValueError,'version_startup_metric_required'):self.state(f)
  for value in (0,0.0,1,0.5,1e100):
   f=self.fixtures();f[SCRIPT+'/versions/'+VID]['result']['startup_time_ms']=value;self.state(f)
 def test_selected_beta_identity_number_and_exact_raw_time(self):
  for key,values,code in [('id',[None,False,0,'',DEP,VID[:8],VID+'x'],'selected_assets_version_identity'),('number',[None,False,True,0,-1,1.0,2,'1'],'selected_assets_version_number'),('created_on',[None,'2026-02-29T00:00:00Z','2026-10-16T02:58:19.000000000Z','2026-10-16T11:58:19+09:00','2026-10-16T02:58:20Z'],'selected_assets_version_time')]:
   for value in values:
    f=self.fixtures();f[self.BETA]['result'][key]=value
    with self.subTest(key=key,value=value):self.reject(f,code)
  for value in (None,[],False,''):
   f=self.fixtures();f[self.BETA]['result']=value;self.reject(f,'selected_assets_version_identity')
 def test_same_raw_nanoseconds_preserved_and_equivalent_variants_rejected(self):
  states=[]
  for raw in ('2026-10-16T02:58:19.123456001Z','2026-10-16T02:58:19.123456999Z','2026-10-16T11:58:19.123456001+09:00'):
   f=self.fixtures();f[SCRIPT+'/versions/'+VID]['result']['metadata']['created_on']=raw;f[self.BETA]['result']['created_on']=raw;state=self.state(f);self.assertEqual(state['activeDeployment']['assetsVersionCreatedOn'],raw);states.append(state)
  self.assertEqual(len({b.digest(s) for s in states}),3)
  for raw in ('2026-10-16T02:58:19.123456999Z','2026-10-16T11:58:19.123456001+09:00'):
   f=self.fixtures();f[SCRIPT+'/versions/'+VID]['result']['metadata']['created_on']='2026-10-16T02:58:19.123456001Z';f[self.BETA]['result']['created_on']=raw;self.reject(f,'selected_assets_version_time')
 def test_assets_parent_config_schema_and_expected_values(self):
  for value in (None,False,0,[], '', {'unknown':self.CANARY}):
   f=self.fixtures();f[self.BETA]['result']['assets']=value;self.reject(f,'selected_assets_schema')
  f=self.fixtures();del f[self.BETA]['result']['assets'];self.reject(f,'selected_assets_schema')
  for value in (None,False,0,[], '', {'unknown':self.CANARY}):
   f=self.fixtures();f[self.BETA]['result']['assets']['config']=value;self.reject(f,'selected_assets_config_schema')
  f=self.fixtures();del f[self.BETA]['result']['assets']['config'];self.reject(f,'selected_assets_config_schema')
  for key,values in [('html_handling',[None,False,0,[],{},'none','force-trailing-slash','drop-trailing-slash','']),('not_found_handling',[None,False,0,[],{},'none','single-page-application','']),('base_path',[None,False,0,[],{},'/else','']),('run_worker_first',[None,True,0,1,[],['/*'],{},'false'])]:
   for value in values:
    with self.subTest(key=key,kind=type(value).__name__):
     f=self.fixtures();f[self.BETA]['result']['assets']['config'][key]=value;self.reject(f,'selected_assets_'+key)
  for key in ('html_handling','not_found_handling'):
   f=self.fixtures();del f[self.BETA]['result']['assets']['config'][key];self.reject(f,'selected_assets_'+key)
 def test_modules_must_be_present_typed_inventory(self):
  for value in (None,False,0,{},''):
   f=self.fixtures();f[self.BETA]['result']['modules']=value;self.reject(f,'selected_assets_modules_inventory_required')
  f=self.fixtures();del f[self.BETA]['result']['modules'];self.reject(f,'selected_assets_modules_inventory_required')
  for value in (None,False,0,[],{}, {'name':None},{'name':False},{'name':0},{'name':[]},{'name':''}):
   f=self.fixtures();f[self.BETA]['result']['modules']=[value];self.reject(f,'selected_assets_module_name_required')
 def test_fixed_headers_exact_canonical_bytes_and_redirect_absence(self):
  for key,values in [('content_type',[None,False,[],{},'application/javascript','text/plain; charset=utf-8','TEXT/PLAIN','']),('content_base64',[None,False,[],{},'','Lyo=','LyoK=','LyoK\n',' LyoK','LyoN','Ly8K','LyoKAA==','LyoKLyoK'])]:
   for value in values:
    f=self.fixtures();f[self.BETA]['result']['modules'][0][key]=value
    with self.subTest(key=key,value=repr(value)):self.reject(f,'selected_assets_headers_bytes')
  for key in ('content_type','content_base64'):
   f=self.fixtures();del f[self.BETA]['result']['modules'][0][key];self.reject(f,'selected_assets_headers_bytes')
  f=self.fixtures();f[self.BETA]['result']['modules'][0]['unknown']=self.CANARY;self.reject(f,'selected_assets_headers_bytes')
  f=self.fixtures();f[self.BETA]['result']['modules'].append(copy.deepcopy(f[self.BETA]['result']['modules'][0]));self.reject(f,'selected_assets_duplicate_headers')
  for value in ({'name':'_redirects'},{'name':'_redirects','content_type':'text/plain','content_base64':''},{'name':'_redirects','content_type':None,'content_base64':self.CANARY}):
   f=self.fixtures();f[self.BETA]['result']['modules'].append(value);self.reject(f,'selected_assets_redirects_present')
 def test_unconsumed_jwt_unknown_metadata_and_module_content_getters_forbidden(self):
  class ReadSelected(dict):
   def __init__(self,allowed,**values):super().__init__(values);self.allowed=allowed
   def __getitem__(self,key):
    if key not in self.allowed:raise AssertionError('forbidden value read')
    return super().__getitem__(key)
   def get(self,key,*default):
    if key not in self.allowed:raise AssertionError('forbidden get')
    return super().get(key,*default)
   def items(self):raise AssertionError('items forbidden')
   def values(self):raise AssertionError('values forbidden')
  f=self.fixtures();v=f[SCRIPT+'/versions/'+VID]['result'];beta=f[self.BETA]['result'];v['metadata']=ReadSelected({'source','created_on'},**v['metadata']);v['annotations']=ReadSelected({'workers/message','workers/tag','workers/triggered_by'},**v['annotations']);v['resources']['script_runtime']['assets']=ReadSelected(set(),private=object(),jwt=object());beta['assets']=ReadSelected({'config'},config=beta['assets']['config'],jwt=object());beta['modules'][1]=ReadSelected({'name'},name='private-module-'+self.CANARY,content_type=object(),content_base64=object());real_type=type
  with patch.object(b,'type',lambda value:dict if real_type(value) is ReadSelected else real_type(value),create=True):state=self.state(get=lambda path:f[path])
  self.assertNotIn(self.CANARY,json.dumps(state))
 def test_known_caps_and_target_gates_run_before_beta(self):
  mutations=[lambda f:f['/accounts/'+ACCOUNT]['result'].update(id='b'*32),lambda f:f['/accounts/'+ACCOUNT+'/workers/scripts']['result'].clear(),lambda f:f['/accounts/'+ACCOUNT+'/workers/domains']['result'][0].update(hostname='other.test'),lambda f:f[SCRIPT+'/settings']['result'].update(logpush=True),lambda f:f[SCRIPT+'/subdomain']['result'].update(enabled=True),lambda f:f[SCRIPT+'/deployments/'+DEP]['result'].update(id=VID),lambda f:f[SCRIPT+'/versions/'+VID]['result'].update(id=DEP),lambda f:f[SCRIPT+'/versions/'+VID]['result']['resources'].update(bindings=[{'secret':self.CANARY}]),lambda f:f[SCRIPT+'/versions/'+VID]['result']['resources']['script'].update(handlers=['scheduled']),lambda f:f[SCRIPT+'/versions/'+VID]['result']['resources']['script'].update(named_handlers=['fetch']),lambda f:f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime'].update(limits={'cpu_ms':1}),lambda f:f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime'].update(exports=['fetch']),lambda f:f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime'].update(migration_tag='x'),lambda f:f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime'].update(compatibility_flags=['nodejs_compat'])]
  for location in ('resources','script_runtime'):
   for name in ('containers','logpush','observability','bindings','unknown'):
    for value in (None,[],{}):
     if location=='resources' and name=='bindings':continue
     def mutate(f,location=location,name=name,value=value):
      parent=f[SCRIPT+'/versions/'+VID]['result']['resources'];parent=parent if location=='resources' else parent['script_runtime'];parent[name]=value
     mutations.append(mutate)
  for i,mutate in enumerate(mutations):
   f=self.fixtures();mutate(f);seen=[]
   with self.subTest(mutation=i),self.assertRaises(ValueError):self.state(get=get_for(f,seen))
   self.assertNotIn(self.BETA,seen)
  for value in (None,False,0,[], ''):
   f=self.fixtures();f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime']['assets']=value;seen=[]
   with self.assertRaisesRegex(ValueError,'version_assets_object_required'):self.state(get=get_for(f,seen))
   self.assertNotIn(self.BETA,seen)
 def test_exact_beta_transport_selection_and_query(self):
  f=self.fixtures();op=R2Regressions().opener([f[SCRIPT+'/deployments?page=1&per_page=1'],f[self.BETA]]);get=R2Regressions().transport(op)
  with self.assertRaisesRegex(ValueError,'provider_get_endpoint_forbidden'):get(self.BETA)
  self.assertEqual(len(op.requests),0);get(SCRIPT+'/deployments?page=1&per_page=1')
  bad=[self.BETA.replace(ACCOUNT,'b'*32),self.BETA.replace(b.WORKER,'other-worker'),self.BETA.replace(VID,DEP),self.BETA.replace(VID,VID[:8]),self.BETA.replace(VID,'latest'),self.BETA.replace('?include=modules',''),self.BETA+'&x=1',self.BETA.replace('include=modules','include=bindings'),self.BETA+'#x',self.BETA.replace('include=modules','include=%6dodules')]
  for path in bad:
   with self.subTest(path=path),self.assertRaises(ValueError):get(path)
  self.assertEqual(len(op.requests),1);get(self.BETA);self.assertEqual(len(op.requests),2);self.assertEqual(op.requests[-1].get_method(),'GET');self.assertIsNone(op.requests[-1].data)
 def test_beta_transport_failures_fixed_no_retry_fallback_or_sweep(self):
  f=self.fixtures()
  for error in (RuntimeError(self.CANARY),ValueError(self.CANARY),b.ProviderEnvelopeError({'secret':self.CANARY})):
   seen=[]
   def get(path):
    seen.append(path)
    if path==self.BETA:raise error
    return f[path]
   with patch.object(b,'state_diagnostic_sweep') as sweep,patch.object(b,'ACCOUNT_SHA',SHA),self.assertRaisesRegex(ValueError,'^selected_assets_transport_unverified$'):b.state_with_diagnostics({},ACCOUNT,get)
   sweep.assert_not_called();self.assertEqual(seen.count(self.BETA),1);self.assertEqual(len(seen),9)
 def test_beta_http_json_cap_and_access_failures_stop_once(self):
  from email.message import Message
  good=json.dumps(self.fixtures()[self.BETA]).encode()
  class Response:
   def __init__(self,status,body,mime='application/json',encoding=None):
    self.status=status;self.body=body;self.headers=Message();self.headers['Content-Type']=mime
    if encoding is not None:self.headers['Content-Encoding']=encoding
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,n):self.limit=n;return self.body[:n]
  variants=[(code,good,'application/json',None) for code in (204,301,302,401,403,404,429,500)]+[(200,b'x'*(1024*1024+1),'application/json',None),(200,good,'text/plain',None),(200,good,'application/json','gzip'),(200,b'{invalid '+self.CANARY.encode(),'application/json',None),(200,b'{"success":true,"success":true,"errors":[],"result":{}}','application/json',None),(200,b'{"success":true,"errors":[],"result":{"x":NaN}}','application/json',None),(200,b'{"success":false,"errors":[{"message":"'+self.CANARY.encode()+b'"}],"result":{}}','application/json',None)]
  for status,raw,mime,encoding in variants:
   response=Response(status,raw,mime,encoding)
   class Opener:
    def __init__(self):self.requests=[]
    def open(self,request,timeout):
     self.requests.append(request)
     return Response(200,json.dumps(self_outer.fixtures()[SCRIPT+'/deployments?page=1&per_page=1']).encode()) if len(self.requests)==1 else response
   self_outer=self;op=Opener();get=R2Regressions().transport(op);get(SCRIPT+'/deployments?page=1&per_page=1')
   with self.subTest(status=status,mime=mime,size=len(raw)),self.assertRaisesRegex(ValueError,'^selected_assets_transport_unverified$'):b.selected_assets_preservation(get,ACCOUNT,VID,1,'2026-10-16T02:58:19Z')
   self.assertEqual(len(op.requests),2)
 def test_total_assets_normal_plus_existing_diagnostic_bound_28(self):
  f=self.fixtures();paths=StateShapeDiagnostics().paths();normal_paths=paths+[self.BETA,SCRIPT+'/deployments?page=1&per_page=1'];responses=[copy.deepcopy(f[path]) for path in normal_paths*2];responses[-1]['result']['deployments'][0]['created_on']='2026-10-16T03:00:00Z';normal=R2Regressions().opener(responses);diagnostic=R2Regressions().opener([f[path] for path in paths])
  with patch.object(b,'ACCOUNT_SHA',SHA),patch.object(b,'build_opener',side_effect=[normal,diagnostic]),patch.object(b,'load_policy',return_value={}),patch.object(b,'authorize',return_value={}),patch.object(b,'trusted_control'),patch.object(b,'old_public',return_value={}) as public,self.assertRaises(b.ProviderStateDiagnosticError) as caught:b.observe(StateShapeDiagnostics().env(),{})
  self.assertEqual(caught.exception.original_code,'active_deployment_changed_during_observation');self.assertEqual(len(normal.requests),20);self.assertEqual(len(diagnostic.requests),8);self.assertEqual(len(normal.requests)+len(diagnostic.requests),28);public.assert_called_once()
  for request in normal.requests+diagnostic.requests:self.assertEqual(request.get_method(),'GET');self.assertIsNone(request.data)
 def test_cross_public_check_detects_raw_beta_and_preservation_changes(self):
  first=self.state()
  for key,value in [('base_path','/'),('run_worker_first',False)]:
   f=self.fixtures();f[self.BETA]['result']['assets']['config'][key]=value;second=self.state(f)
   env,event=Authorization().case()
   with patch.object(b,'trusted_control'),patch.object(b,'provider_get',return_value=(ACCOUNT,None)),patch.object(b,'state_with_diagnostics',side_effect=[first,second]),patch.object(b,'old_public',return_value={}),self.assertRaisesRegex(ValueError,'provider_changed_across_full_public_check'):b.observe(env,event)
 def test_source_fixed_config_headers_and_no_redirects_are_pinned(self):
  policy=b.load_policy();source=json.loads(b.read(b.ROOT/'docs/direct-gwangju-gwangsan-policy-correction/prior-publication/wrangler-publish.json'));contract=json.loads(b.read(b.ROOT/policy['previousPublicContractPath']))
  self.assertEqual(source,{'name':b.WORKER,'compatibility_date':'2026-10-09','workers_dev':False,'assets':{'directory':'./dist/','html_handling':'auto-trailing-slash','not_found_handling':'404-page'}});self.assertEqual(contract['files']['_headers'],b.sha(b'/*\n'));self.assertNotIn('_redirects',contract['files']);self.assertEqual(b.CURRENT,'0da9982f8ea294c6fb38729d17e9043d45f7ca72')


if __name__=='__main__':
 print('Python runtime: '+'.'.join(str(v) for v in b.sys.version_info[:3]),flush=True)
 unittest.main(verbosity=2)
