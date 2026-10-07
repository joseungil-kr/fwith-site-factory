"""GET-only existing state inspection, with no secret values persisted or printed."""
import hashlib,json,os,re,sys,urllib.request,urllib.error
from pathlib import Path

def require(ok,message):
 if not ok:raise ValueError(message)
def paginate(get,path):
 rows=[];page=1
 while True:
  d=get(path+('&' if '?' in path else '?')+'page='+str(page)+'&per_page=100')
  require(isinstance(d.get('result'),list),'Provider list malformed');batch=d['result'];rows.extend(batch)
  info=d.get('result_info') or {};total=info.get('total_pages')
  if total is not None:
   require(isinstance(total,int) and total>=0 and page<=max(total,1),'Provider pagination malformed')
   if page>=total:
    require(info.get('total_count',len(rows))==len(rows),'Provider list truncated');return rows
  elif len(batch)<100:return rows
  page+=1;require(page<=100,'Provider pagination unbounded')

def settings(value):
 require(isinstance(value,dict),'Missing Worker settings')
 # Static sites must not carry runtime credentials or other resource bindings.
 # Reject before examining or serializing any user-controlled binding values.
 require(value.get('bindings')==[],'Unexpected runtime bindings: stop without exposing values')
 require(not value.get('tail_consumers') and not value.get('migrations'),'Unexpected runtime resource capability')
 fields={'bindings','compatibility_date','compatibility_flags','usage_model','limits','logpush','observability','placement','tail_consumers','tags','cache_options','annotations','migrations'}
 require(set(value)<=fields,'Unreviewed provider settings shape')
 require(isinstance(value.get('compatibility_date'),str),'Missing compatibility date')
 # Deployment annotations identify the version, not persistent settings; do not persist free text.
 normalized={k:v for k,v in value.items() if k not in ('annotations','migrations')}
 # Pinned Wrangler explicitly patches disabled observability; absent and exact
 # {enabled:false} are the same disabled state, never equivalent to enabled.
 if normalized.get('observability')=={'enabled':False}:normalized.pop('observability')
 return normalized

def inventory(get,account,p,phase):
 worker=p['previewWorker' if phase=='preview' else 'worker'];require(isinstance(worker,str) and re.fullmatch('[a-z0-9-]+',worker),'Missing fixed Worker')
 base='/accounts/'+account
 current=settings(get(base+'/workers/scripts/'+worker+'/settings')['result'])
 sub=get(base+'/workers/scripts/'+worker+'/subdomain')['result']
 require(isinstance(sub,dict) and set(sub)<={'enabled','previews_enabled'} and isinstance(sub.get('enabled'),bool),'Malformed workers.dev settings')
 require('previews_enabled' not in sub or isinstance(sub['previews_enabled'],bool),'Malformed preview URL setting')
 domains=[]
 for row in paginate(get,base+'/workers/domains'):
  require(isinstance(row,dict) and all(isinstance(row.get(k),str) for k in ('id','hostname','service','zone_id')),'Incomplete domain record')
  require(row.get('environment') in (None,'production'),'Unreviewed nonproduction domain environment')
  domains.append({k:row.get(k) for k in ('id','hostname','service','environment','zone_id','zone_name','enabled','previews_enabled')})
 host=p['productionOrigin'].removeprefix('https://');found=[r for r in domains if r['hostname']==host]
 require(len(found)==1 and found[0]['service']==p['worker'],'Fixed production binding absent or changed')
 if phase=='preview':
  require(sub['enabled'] is True,'Existing QA workers.dev is disabled')
  require(get(base+'/workers/subdomain')['result'].get('subdomain')=='joseungil','Unexpected account subdomain')
  require(not any(r['service']==worker for r in domains),'QA Worker has unexpected custom domains')
 # Do not repeat the denied legacy zone-route endpoint. The proposed release
 # config has no routes at all; pinned Wrangler 4.147.0 skips both route and
 # custom-domain publication. This is explicitly NOT a legacy-route inventory.
 relevant=[r for r in domains if r['service']==worker or r['hostname']==host]
 require(all(r['hostname'].endswith('.fwith.kr') for r in relevant),'Unexpected non-fwith target domain')
 require(all(r.get('zone_name') in (None,'fwith.kr') for r in relevant),'Unexpected target zone')
 return {'worker':worker,'settings':current,'workersDev':sub,'domains':sorted(relevant,key=lambda x:x['id']),'legacyRoutes':{'state':'not_read_not_modified','requiresAssetsOnlyConfig':True},'scope':'fixed-worker-and-existing-fwith.kr-domains'}

def main():
 p=json.loads(Path(sys.argv[1]).read_text());phase=sys.argv[2];checkpoint=sys.argv[3]
 account=os.environ['CLOUDFLARE_ACCOUNT_ID'];token=os.environ['CLOUDFLARE_API_TOKEN'];require(bool(re.fullmatch('[0-9A-Fa-f]{32}',account)) and bool(token),'Missing provider credentials')
 def get(path):
  req=urllib.request.Request('https://api.cloudflare.com/client/v4'+path,headers={'Authorization':'Bearer '+token})
  family=('settings' if path.endswith('/settings') else 'subdomain' if path.endswith('/subdomain') else 'domains' if '/workers/domains' in path else 'routes' if '/workers/routes' in path else 'zones' if path.startswith('/zones?') else 'unexpected-endpoint')
  try:
   with urllib.request.urlopen(req,timeout=30) as r:d=json.load(r)
  except urllib.error.HTTPError as exc:raise ValueError('Provider GET '+family+' HTTP '+str(exc.code)) from None
  require(d.get('success') is True and not d.get('errors') and 'result' in d,'Provider read failed');return d
 state=inventory(get,account,p,phase)
 receipt=Path(os.environ['RUNNER_TEMP'])/('manual-20261007-'+p['siteKey']+'-'+phase+'-binding.json')
 require(not receipt.is_symlink(),'Provider receipt symlink forbidden')
 if checkpoint=='inspect':
  receipt.write_text(json.dumps(state,sort_keys=True,indent=2));print('Read-only nonsecret provider inventory saved: '+str(receipt));return
 require(checkpoint in ('before','after'),'Invalid checkpoint')
 expected=p.get('providerBaselineSha256',{}).get(phase)
 state_hash=hashlib.sha256(json.dumps(state,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 require(isinstance(expected,str) and re.fullmatch('[0-9a-f]{64}',expected) and state_hash==expected,'Provider state differs from independently accepted baseline digest')
 if checkpoint=='before':receipt.write_text(json.dumps(state,sort_keys=True))
 else:
  require(json.loads(receipt.read_text())==state,'Provider state changed during deployment')
  config=json.loads(Path('.manual-assets-only-20261007.jsonc').read_text())
  require('routes' not in config and 'route' not in config,'Unexpected route/domain declaration')
  require(config.get('workers_dev')==state['workersDev']['enabled'],'workers.dev exposure changed')
  require(config.get('preview_urls')==state['workersDev'].get('previews_enabled'),'Preview URL exposure changed')
 print('Existing reviewed settings, fixed fwith domains and workers.dev unchanged; legacy routes unrequested: '+checkpoint)
if __name__=='__main__':
 try:main()
 except Exception as exc:
  # No HTTP response bodies, credentials, resource values or traceback locals in logs.
  print('Provider verification blocked: '+(str(exc) if type(exc) is ValueError else type(exc).__name__));sys.exit(1)
