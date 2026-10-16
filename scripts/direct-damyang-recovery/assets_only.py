"""Generate only the reviewed static upload config from a digest-accepted live receipt."""
import hashlib,json,os,re,sys
from pathlib import Path

def require(ok,message):
 if not ok:raise ValueError(message)
def state_digest(s):return hashlib.sha256(json.dumps(s,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def configuration(policy,phase,source,state):
 require(phase in ('preview','production'),'Invalid phase')
 require(state_digest(state)==policy['providerBaselineSha256'][phase],'Unreviewed live receipt')
 worker=policy['previewWorker' if phase=='preview' else 'worker']
 require(bool(worker) and source['name']==worker and state['worker']==worker,'Wrong existing Worker')
 require(set(source)<={'$schema','name','compatibility_date','workers_dev','assets','routes'},'Unreviewed source configuration capability')
 require(isinstance(source.get('workers_dev'),bool),'Explicit workers.dev state required')
 require(source['assets']['directory'] in ('./dist/','./dist','dist'),'Wrong artifact path')
 require(set(source['assets'])=={'directory','not_found_handling','html_handling'},'Unreviewed asset router capability')
 require(source['assets']['not_found_handling']=='404-page' and source['assets']['html_handling']=='auto-trailing-slash','Unreviewed asset routing behavior')
 require(all(r=={'pattern':policy['productionOrigin'].removeprefix('https://'),'custom_domain':True} for r in source.get('routes',[])),'Foreign route forbidden')
 settings=state['settings'];date=source['compatibility_date']
 expected={'bindings':[],'compatibility_date':date,'compatibility_flags':[],'logpush':False,'placement':{},'tags':[],'tail_consumers':[],'usage_model':'standard'}
 require(settings==expected,'Nondefault existing settings require independent preservation design')
 sub=state['workersDev']
 require(isinstance(sub.get('enabled'),bool) and isinstance(sub.get('previews_enabled'),bool),'Incomplete exposure baseline')
 require(source['workers_dev']==sub['enabled'],'Would change workers.dev exposure')
 result={k:v for k,v in source.items() if k!='routes'}
 result.update(preview_urls=sub['previews_enabled'],compatibility_flags=[],logpush=False,observability={'enabled':False})
 # No main/user Worker, bindings, provisioning, crons, routes, domains, or auto-config.
 require('routes' not in result and 'route' not in result,'Routing mutation forbidden')
 return result

def main():
 policy=json.loads(Path(sys.argv[1]).read_text());phase=sys.argv[2]
 receipt=Path(os.environ['RUNNER_TEMP'])/('manual-20261007-'+policy['siteKey']+'-'+phase+'-binding.json')
 require(not receipt.is_symlink(),'Receipt symlink forbidden')
 state=json.loads(receipt.read_text());source=Path(policy['previewConfig' if phase=='preview' else 'productionConfig'])
 require(not source.is_symlink(),'Source config symlink forbidden')
 output=Path('.manual-assets-only-20261007.jsonc');require(not output.is_symlink(),'Generated config symlink forbidden')
 output.write_text(json.dumps(configuration(policy,phase,json.loads(source.read_text()),state),indent=2)+'\n')
 print('Digest-verified existing settings retained; generated config contains no domain or legacy route declarations')
if __name__=='__main__':main()
