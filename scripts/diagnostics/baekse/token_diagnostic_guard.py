"""Single-delta feature activation guard. All API calls are read-only; credentials are never printed."""
import os,json,urllib.request,hashlib,sys,pathlib
WORKER='funeralflower-home-preview'; HOST='order.baeksefood.com'
ROOT='https://api.cloudflare.com/client/v4'; ACCOUNT=os.environ['CLOUDFLARE_ACCOUNT_ID']; TOKEN=os.environ['CLOUDFLARE_API_TOKEN']
STATE=pathlib.Path(os.environ.get('RUNNER_TEMP','/tmp'))/'baekse-release-guard.json'
def get(path):
 r=urllib.request.Request(ROOT+path,headers={'Authorization':'Bearer '+TOKEN,'Accept':'application/json'})
 with urllib.request.urlopen(r,timeout=30) as response: data=json.load(response)
 assert data.get('success') is True,'Cloudflare read-only preflight failed'
 return data['result']
def normalize(bindings):
 keys={(b.get('type'),b.get('name')) for b in bindings}
 required={('assets','ASSETS'),('durable_object_namespace','ORDER_DB'),('secret_text','ADMIN_PASSWORD'),('secret_text','TELEGRAM_ORDER_BOT_TOKEN')}
 assert required<=keys and keys<=required|{('secret_text','TELEGRAM_ORDER_CHAT_ID'),('plain_text','TELEGRAM_ORDER_ENABLED')} and len(keys)==len(bindings),'Unexpected uploaded binding set'
 normalized=[]
 for b in bindings:
  t,n=b['type'],b['name']
  if t=='durable_object_namespace':
   assert b.get('class_name')=='OrderDatabase' and b.get('namespace_id'),'Unexpected DO class/namespace'
   assert not b.get('script_name') or b['script_name']==WORKER,'Unexpected external DO'
   normalized.append([t,n,b['class_name'],b['namespace_id'],b.get('script_name')])
  elif t=='plain_text':
   assert b.get('text') in ('false','true'),'Unexpected notifier value'
   normalized.append([t,n,b['text']])
  else:normalized.append([t,n])
 return sorted(normalized)
def snapshot():
 prefix='/accounts/'+ACCOUNT+'/workers/scripts/'+WORKER
 domains=get('/accounts/'+ACCOUNT+'/workers/domains')
 matches=[d for d in domains if d.get('service')==WORKER]
 assert len(matches)==1 and matches[0].get('hostname')==HOST,'Unexpected custom domain set'
 assert sum(d.get('hostname')==HOST for d in domains)==1,'Ambiguous domain'
 domain=matches[0];zone=domain.get('zone_id');assert zone,'Missing domain zone metadata'
 routes=get('/zones/'+zone+'/workers/routes')
 assert not [r for r in routes if r.get('script')==WORKER],'Unexpected zone route'
 schedules=get(prefix+'/schedules')
 assert not (schedules.get('schedules') or []),'Unexpected cron'
 subdomain=get(prefix+'/subdomain')
 assert subdomain.get('enabled') is True and subdomain.get('previews_enabled',False) is False,'Subdomain access differs from pinned config; do not change it'
 settings=get(prefix+'/script-settings')
 assert settings.get('tail_consumers')==[],'Tail consumers not explicitly empty; stop for review'
 assert settings.get('logpush') is False,'Logpush disabled metadata unavailable or enabled'
 # Dashboard independently confirmed Logs/Traces/Issues OFF and no exports.
 # Require API metadata to agree where the endpoint exposes those settings.
 obs=settings.get('observability')
 assert isinstance(obs,dict),'Observability metadata unavailable; stop for review'
 assert obs.get('enabled') is False,'Observability must already be disabled'
 for name in ('logs','traces','agents','issues'):
  item=obs.get(name)
  assert item is None or (isinstance(item,dict) and item.get('enabled') is False),'Enabled or ambiguous telemetry'
  assert item is None or not item.get('destinations'),'Telemetry export destinations present'
 deployments=get(prefix+'/deployments')['deployments'];assert deployments,'No deployment'
 versions=deployments[0].get('versions') or []
 assert len(versions)==1 and versions[0].get('percentage')==100,'Not stable100 deployment'
 version=versions[0]['version_id']
 immutable=get(prefix+'/versions/'+version)
 assert immutable.get('id')==version,'Immutable active identity mismatch'
 bindings=immutable.get('resources',{}).get('bindings') or []
 keys={(b.get('type'),b.get('name')) for b in bindings}
 required={('assets','ASSETS'),('durable_object_namespace','ORDER_DB'),('secret_text','ADMIN_PASSWORD'),('secret_text','TELEGRAM_ORDER_BOT_TOKEN')}
 allowed=required|{('secret_text','TELEGRAM_ORDER_CHAT_ID'),('plain_text','TELEGRAM_ORDER_ENABLED')}
 assert required<=keys and keys<=allowed and len(keys)==len(bindings),'Unexpected binding set'
 normalized=normalize(bindings)
 scope={'domain':{k:domain.get(k) for k in ('id','hostname','service','environment','zone_id')},'subdomain':subdomain}
 return {'version':version,'scope':scope,'bindings':normalized,'telemetry':obs,'tail_consumers':settings.get('tail_consumers') or [],'logpush':settings['logpush']}
def output(k,v):
 with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write(k+'='+v+'\n')
def main():
 mode=sys.argv[1]
 if mode=='telemetry-preflight':
  v=get('/accounts/'+ACCOUNT+'/workers/scripts/'+WORKER+'/script-settings')
  obs=v.get('observability')
  result={'logpush_false':v.get('logpush') is False,'tail_consumers_explicit_empty':v.get('tail_consumers')==[],'observability_false':isinstance(obs,dict) and obs.get('enabled') is False}
  for name in ('logs','traces','agents','issues'):
   item=obs.get(name) if isinstance(obs,dict) else None
   result[name]='absent' if item is None else ('disabled' if isinstance(item,dict) and item.get('enabled') is False and not item.get('destinations') else 'not_verified_disabled')
  print(json.dumps(result,sort_keys=True));return
 live=snapshot()
 if mode=='capture':
  assert live['version']=='8e38b102-c4a6-4321-befb-fae7b275c942','Live version changed'
  assert ['secret_text','TELEGRAM_ORDER_CHAT_ID'] in live['bindings'],'Recipient Secret absent'
  assert ['plain_text','TELEGRAM_ORDER_ENABLED','true'] in live['bindings'],'Notifier binding differs'
  STATE.write_text(json.dumps(live));os.chmod(STATE,0o600)
  output('previous_version',live['version']);print('READONLY_CAPTURE_PASS')
 elif mode=='preupload':
  prior=json.loads(STATE.read_text());assert live==prior,'Production metadata changed';print('PREUPLOAD_PASS')
 elif mode=='uploaded':
  prior=json.loads(STATE.read_text());assert live==prior,'Production metadata changed during upload'
  version_id=os.environ['UPLOADED_VERSION']
  assert version_id!=prior['version'],'Candidate not distinct'
  version=get('/accounts/'+ACCOUNT+'/workers/scripts/'+WORKER+'/versions/'+version_id)
  assert version.get('id')==version_id,'Uploaded identity mismatch'
  assert version.get('annotations',{}).get('workers/tag')==os.environ['SOURCE_SHA'],'Source tag mismatch'
  assert normalize(version.get('resources',{}).get('bindings') or [])==prior['bindings'],'Binding delta forbidden'
  print('INACTIVE_VERIFIED: '+version_id+'; NOT_ACTIVATED; NOT_INVOKED')
 else:raise AssertionError('Unsupported mode')
if __name__=='__main__':
 try:main()
 except Exception as e:
  print('GUARD_STOP:',str(e) if isinstance(e,AssertionError) else type(e).__name__);sys.exit(1)
