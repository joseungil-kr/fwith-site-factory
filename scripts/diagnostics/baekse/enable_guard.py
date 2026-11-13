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
 settings=get(prefix+'/settings'); bindings=settings.get('bindings') or []
 keys={(b.get('type'),b.get('name')) for b in bindings}
 required={('assets','ASSETS'),('durable_object_namespace','ORDER_DB'),('secret_text','ADMIN_PASSWORD'),('secret_text','TELEGRAM_ORDER_BOT_TOKEN')}
 allowed=required|{('secret_text','TELEGRAM_ORDER_CHAT_ID'),('plain_text','TELEGRAM_ORDER_ENABLED')}
 assert required<=keys and keys<=allowed and len(keys)==len(bindings),'Unexpected binding set'
 normalized=normalize(bindings)
 deployments=get(prefix+'/deployments')['deployments'];assert deployments,'No deployment'
 versions=deployments[0].get('versions') or []
 assert len(versions)==1 and versions[0].get('percentage')==100,'Not stable 100% deployment'
 version=versions[0]['version_id']
 scope={'domain':{k:domain.get(k) for k in ('id','hostname','service','environment','zone_id')},'subdomain':subdomain}
 return {'version':version,'scope':scope,'bindings':normalized}
def output(k,v):
 with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write(k+'='+v+'\n')
def enabled_bindings(prior):
 return sorted([b for b in prior['bindings'] if b[:2]!=['plain_text','TELEGRAM_ORDER_ENABLED']]+[['plain_text','TELEGRAM_ORDER_ENABLED','true']])
def main():
 mode=sys.argv[1];live=snapshot()
 if mode=='capture':
  expected=os.environ['EXPECTED_LIVE_VERSION'];assert len(expected)==36 and live['version']==expected,'Live version changed'
  assert ['secret_text','TELEGRAM_ORDER_CHAT_ID'] in live['bindings'],'Recipient Secret absent'
  assert not any(b[:2]==['plain_text','TELEGRAM_ORDER_ENABLED'] and b[2]!='false' for b in live['bindings']),'Notifier unexpectedly already enabled'
  STATE.write_text(json.dumps(live));os.chmod(STATE,0o600)
  output('previous_version',live['version']);print('PREFLIGHT_PASS: exact host; stable version captured; namespace/bindings/access fingerprint retained')
 elif mode=='predeploy':
  prior=json.loads(STATE.read_text());assert live==prior,'Production changed after preflight';print('IMMEDIATE_PREDEPLOY_PASS')
 elif mode=='uploaded':
  prior=json.loads(STATE.read_text());assert live==prior,'Production changed during upload'
  version_id=os.environ['UPLOADED_VERSION']
  version=get('/accounts/'+ACCOUNT+'/workers/scripts/'+WORKER+'/versions/'+version_id)
  assert version.get('id')==version_id,'Uploaded version mismatch'
  assert version.get('annotations',{}).get('workers/tag')==os.environ['SOURCE_SHA'],'Uploaded source tag mismatch'
  bindings=version.get('resources',{}).get('bindings')
  assert isinstance(bindings,list) and normalize(bindings)==enabled_bindings(prior),'Uploaded bindings must differ only by enabled flag'
  print('UPLOADED_VERSION_METADATA_PASS: no production activation yet')
 elif mode=='post':
  prior=json.loads(STATE.read_text());assert live['scope']==prior['scope'] and live['bindings']==enabled_bindings(prior),'Unexpected bindings/namespace/access delta'
  assert live['version']==os.environ['UPLOADED_VERSION'],'Wrong production version observed'
  STATE.with_suffix('.deployed.json').write_text(json.dumps(live));output('deployed_version',live['version']);print('POST_VERSION_BINDING_PASS')
 elif mode=='rollback-safe':
  deployed=json.loads(STATE.with_suffix('.deployed.json').read_text());assert live==deployed,'Concurrent change; automatic rollback forbidden'
  prior=json.loads(STATE.read_text());assert live['scope']==prior['scope'] and live['bindings']==enabled_bindings(prior),'Unsafe rollback metadata difference'
  print('ROLLBACK_SAFE_CHECK_PASS')
 elif mode=='rolled-back':
  prior=json.loads(STATE.read_text());assert live==prior,'Rollback not independently verified';print('ROLLBACK_VERIFIED')
 else:raise AssertionError('Unknown guard mode')
if __name__=='__main__':
 try:main()
 except Exception as e:
  print('GUARD_STOP:',str(e) if isinstance(e,AssertionError) else type(e).__name__);sys.exit(1)

