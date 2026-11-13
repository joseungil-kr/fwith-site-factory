"""DIAGNOSTIC ONLY: GET once per logical resource, no retries or mutations.
Only logical labels, HTTP status, boolean success and numeric CF error codes printed.
No body/header/URL/credential/exception-text output. No artifact with raw data.
"""
import os,json,sys,urllib.request,urllib.error
ROOT='https://api.cloudflare.com/client/v4'
WORKER='funeralflower-home-preview';HOST='order.baeksefood.com'
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
opener=urllib.request.build_opener(NoRedirect())
seen=set();failed=False;global_stop=False

def emit(label,status,ok,codes=()):
 print(json.dumps({'check':label,'http_status':status,'ok':ok,'error_codes':list(codes)},sort_keys=True),flush=True)
def codes(data):
 if not isinstance(data,dict):return []
 return [x['code'] for x in (data.get('errors') or [])[:20] if isinstance(x,dict) and isinstance(x.get('code'),int) and not isinstance(x['code'],bool)]
def inspect(label,path):
 global failed,global_stop
 if global_stop:emit(label,'SKIPPED_AUTH_STOP',False);return None
 assert path not in seen,'Duplicate diagnostic call prohibited'
 seen.add(path)
 request=urllib.request.Request(ROOT+path,headers={'Authorization':'Bearer '+os.environ['CLOUDFLARE_API_TOKEN'],'Accept':'application/json'},method='GET')
 try:
  with opener.open(request,timeout=20) as response:
   status=response.status;raw=response.read(1048577)
  if len(raw)>1048576:emit(label,status,False);failed=True;return None
  data=json.loads(raw)
  ok=isinstance(data,dict) and data.get('success') is True
  emit(label,status,ok,codes(data))
  if not ok:failed=True;return None
  return data.get('result')
 except urllib.error.HTTPError as error:
  try:data=json.loads(error.read(65536))
  except Exception:data={}
  emit(label,error.code,False,codes(data));failed=True
  # A resource-specific403 is not retried or approached via another endpoint.
  # Other independent already-authorized resource reads may still be diagnosed.
  #401 signals credential failure: stop all subsequent calls.
  if error.code==401:global_stop=True
 except Exception:
  emit(label,'TRANSPORT_OR_PARSE_FAILURE',False);failed=True
 return None

def main():
 global failed
 if not os.environ.get('CLOUDFLARE_ACCOUNT_ID') or not os.environ.get('CLOUDFLARE_API_TOKEN'):
  emit('credential_presence','MISSING',False);return 1
 account=os.environ['CLOUDFLARE_ACCOUNT_ID'];prefix='/accounts/'+account+'/workers/scripts/'+WORKER
 # Known historical successful resource families first; no duplicate capture call.
 domains=inspect('account_custom_domains','/accounts/'+account+'/workers/domains')
 inspect('worker_settings',prefix+'/settings')
 inspect('worker_cron_schedules',prefix+'/schedules')
 inspect('worker_deployments',prefix+'/deployments')
 # New checks added by release guard; possible missing permission / API support.
 inspect('worker_subdomain_access',prefix+'/subdomain')
 matches=[d for d in domains if isinstance(d,dict) and d.get('hostname')==HOST and d.get('service')==WORKER] if isinstance(domains,list) else []
 zone=matches[0].get('zone_id') if len(matches)==1 else None
 if isinstance(zone,str) and zone.isalnum():inspect('linked_zone_worker_routes','/zones/'+zone+'/workers/routes')
 else:emit('linked_zone_worker_routes','SKIPPED_DEPENDENCY_UNVERIFIED',False);failed=True
 return 1 if failed else 0
if __name__=='__main__':
 try:sys.exit(main())
 except Exception:
  emit('diagnostic_runner','LOCAL_FAILURE',False);sys.exit(1)
