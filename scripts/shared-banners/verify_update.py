#!/usr/bin/env python3
"""Update an already bound, exact reviewed static release. No provider writes exist here.
The existing fixed publisher owns static packaging, deployment and post-deploy QA.
"""
import argparse,importlib.util,json,os,re,sys,hashlib
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request,build_opener
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[2]
ALLOWED={r:f'scripts/direct-{r}/publish.py' for r in ['seoul-yangcheon', 'anseong', 'dongducheon', 'gapyeong', 'gimpo', 'gunpo', 'guri', 'gwacheon', 'gwangju', 'hanam', 'icheon', 'jongno', 'osan', 'paju', 'pocheon', 'seoul-dobong', 'seoul-dongdaemun', 'seoul-gangbuk', 'seoul-gwangjin', 'seoul-jung', 'seoul-jungnang', 'seoul-seongbuk', 'seoul-seongdong', 'seoul-yongsan', 'siheung', 'uijeongbu', 'uiwang', 'yangju', 'yangpyeong', 'yeoncheon', 'seoul-nowon']}
def require(ok,code):
 if not ok:raise ValueError(code)
def load(region):
 require(region in ALLOWED,'unknown_fixed_update_target')
 targets=json.loads((ROOT/'docs/shared-banner-release/targets.json').read_text())
 target=targets['targets'].get(region);require(target is not None,'update_target_not_reviewed')
 for key in ['previousRevision','revision']:require(re.fullmatch('[0-9a-f]{40}',target.get(key,'')),'invalid_revision_pin')
 require(target['revision']==os.environ.get('REVISION'),'new_revision_mismatch')
 require(target['revision']!=target['previousRevision'],'update_must_change_source')
 require(target.get('status')=='independently_reviewed_source','source_review_required')
 for file_key,hash_key in [('sourceReadback','sourceReadbackSha256'),('independentStaticReview','independentStaticReviewSha256')]:
  relative=target.get(file_key,'');require(relative.startswith('docs/shared-banner-release/') and '..' not in Path(relative).parts,'review_evidence_path_invalid')
  path=ROOT/relative;require(path.is_file() and not path.is_symlink(),'review_evidence_missing')
  require(hashlib.sha256(path.read_bytes()).hexdigest()==target.get(hash_key),'review_evidence_digest_mismatch')
 evidence=json.loads((ROOT/target['sourceReadback']).read_text())
 require(evidence.get('sourceCommit')==target['revision'] and evidence.get('parentCommit')==target['previousRevision'] and evidence.get('allFilesMatch',evidence.get('all13Match')) is True,'remote_source_readback_mismatch')
 count=target.get('changedFileCount');require(type(count) is int and 13<=count<=40,'reviewed_change_count_required')
 files=evidence.get('remoteChangedFiles',[]);paths=[r.get('path','') for r in files]
 require(len(files)==count and len(set(paths))==count and all(r.get('remoteBytesMatch') is True and r.get('path','').startswith(target['root']+'/') and '..' not in Path(r['path']).parts and re.fullmatch('[0-9a-f]{64}',r.get('sha256','')) for r in files),'source_change_scope_mismatch')
 spec=importlib.util.spec_from_file_location('fixed_publisher',ROOT/ALLOWED[region]);pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
 expected={'repository':pub.REPOSITORY,'branch':pub.BRANCH,'root':pub.SOURCE_ROOT,'hostname':pub.HOSTNAME,'worker':pub.WORKER}
 require(all(target.get(k)==v for k,v in expected.items()),'fixed_identity_mismatch')
 require(os.environ.get('GITHUB_REPOSITORY')==pub.REPOSITORY,'repository_mismatch')
 require(os.environ.get('GITHUB_RUN_ATTEMPT')=='1','update_rerun_forbidden')
 return target,pub
def authorize_mutation(region):
 require(region in ALLOWED,'unknown_fixed_update_target')
 target=json.loads((ROOT/'docs/shared-banner-release/targets.json').read_text())['targets'].get(region)
 reviewed=bool(target and target.get('revision')==os.environ.get('REVISION'))
 update=os.environ.get('EXISTING_UPDATE')=='true'
 require(not reviewed or update,'reviewed_banner_revision_requires_existing_update')
 if update:load(region)
 return dict(state='mutation_mode_verified',region=region,reviewedBannerRevision=reviewed,existingUpdate=update)

class RevisionPage(HTMLParser):
 def __init__(self):super().__init__();self.revisions=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='meta' and a.get('name')=='site-factory-revision':self.revisions.append(a.get('content'))
def readonly(transport):
 def call(method,path,body=None):
  require(method=='GET' and body is None,'provider_mutation_forbidden')
  return transport(method,path,body)
 return call
def helper(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/f'scripts/manual-release-20261007/{name}.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def provider_get(pub):
 account=os.environ.get('CLOUDFLARE_ACCOUNT_ID','');token=os.environ.get('CLOUDFLARE_API_TOKEN','')
 require(re.fullmatch('[0-9a-fA-F]{32}',account) and token,'missing_provider_configuration')
 prefix='/accounts/'+account;opener=build_opener(pub.NoRedirect())
 allowed={prefix,prefix+'/workers/scripts',prefix+'/workers/domains',prefix+'/workers/scripts/'+pub.WORKER+'/settings',prefix+'/workers/scripts/'+pub.WORKER+'/subdomain'}
 def get(path):
  u=urlsplit(path);require(u.path in allowed and (not u.query or (u.path in {prefix+'/workers/scripts',prefix+'/workers/domains'} and re.fullmatch('page=[0-9]+&per_page=100',u.query))),'provider_operation_forbidden')
  req=Request('https://api.cloudflare.com/client/v4'+path,method='GET',headers={'Authorization':'Bearer '+token})
  with opener.open(req,timeout=30) as response:
   require(response.status==200,'provider_http_status');raw=response.read(pub.LIMIT+1)
  require(len(raw)<=pub.LIMIT,'provider_response_limit');data=json.loads(raw)
  require(data.get('success') is True and not data.get('errors') and 'result' in data,'provider_response_unverified');return data
 return account,get

def state_and_config(target,pub,source):
 pc=helper('provider_check');writer=helper('write_assets_only_config');account,get=provider_get(pub);prefix='/accounts/'+account
 require(get(prefix)['result']['id']==account,'account_identity_mismatch')
 scripts=pc.paginate(get,prefix+'/workers/scripts');names=[r.get('id') for r in scripts]
 require(all(isinstance(n,str) and n for n in names) and len(names)==len(set(names)) and names.count(pub.WORKER)==1,'existing_worker_missing_or_ambiguous')
 policy={'worker':pub.WORKER,'productionOrigin':pub.ORIGIN}
 state=pc.inventory(get,account,policy,'production')
 require(len(state['domains'])==1 and state['domains'][0]['hostname']==pub.HOSTNAME and state['domains'][0]['service']==pub.WORKER,'existing_exact_binding_required')
 # Reuse the audited assets-only writer. It rejects nondefault settings, absent
 # exposure flags and any difference in workers.dev/date before serializing state.
 digest=writer.state_digest(state);policy['providerBaselineSha256']={'production':digest}
 config=writer.configuration(policy,'production',source,state)
 return state,config,hashlib.sha256(account.encode()).hexdigest()

def preflight(target,pub):
 source=json.loads(Path('release/wrangler.publish.json').read_text())
 state,config,account_hash=state_and_config(target,pub,source)
 body,headers=pub.get('/')
 page=RevisionPage();page.feed(body.decode('utf-8'))
 require(page.revisions==[target['previousRevision']],'previous_public_revision_mismatch')
 # Config contains neither routes nor domains, and it preserves both exposure flags.
 pub.save('update-source-config.json',source);pub.save('provider-state-before.json',state)
 pub.save('release/wrangler.publish.json',config)
 return dict(state='existing_update_preflight_verified',previousRevision=target['previousRevision'],revision=target['revision'],hostname=pub.HOSTNAME,worker=pub.WORKER,accountIdSha256=account_hash,publicHomeHttpStatus=200,publicHomeSha256=pub.sha(body),providerStateSha256=helper('write_assets_only_config').state_digest(state),providerMethods=['GET'],providerMutationsPerformed=False,hostnameAttachAllowed=False,legacyRoutes='not_read_not_modified')

def provider_after(target,pub):
 source=json.loads(Path('update-source-config.json').read_text());state,config,account_hash=state_and_config(target,pub,source)
 require(state==json.loads(Path('provider-state-before.json').read_text()),'provider_state_changed')
 require(config==json.loads(Path('release/wrangler.publish.json').read_text()),'update_config_changed')
 before=json.loads(Path('binding-before.json').read_text());require(before['accountIdSha256']==account_hash,'provider_account_changed')
 return dict(state='provider_settings_and_exposure_unchanged',accountIdSha256=account_hash,providerStateSha256=helper('write_assets_only_config').state_digest(state),providerMethods=['GET'],providerMutationsPerformed=False)

def artifact(target,pub):
 manifest=json.loads(Path('release/release.json').read_text())
 require(manifest.get('revision')==target['revision'] and manifest.get('worker')==pub.WORKER and manifest.get('origin')==pub.ORIGIN,'release_identity_mismatch')
 sys.path.insert(0,str(Path(__file__).parent))
 from qa_shared_banners import inspect
 os.environ['SITE_URL']=pub.ORIGIN;os.environ['SITE_INDEXABLE']='true'
 result=inspect(Path('release'),ROOT/'docs/shared-banner-release/approved-assets.json')
 return dict(state='reviewed_banner_artifact_verified',revision=target['revision'],customerHtml=result['customerHtml'],banners=result['banners'],assetSha256=result['assetSha256'])
def public_assets(target,pub):
 rows=[]
 for asset in json.loads((ROOT/'docs/shared-banner-release/approved-assets.json').read_text()):
  path='/images/shared-banners/'+asset['name']+'.webp';body,headers=pub.get(path)
  require(headers.get('Content-Type','').split(';')[0].strip().lower()=='image/webp','shared_banner_mime_mismatch')
  require(pub.sha(body)==asset['sha256'],'shared_banner_live_digest_mismatch')
  rows.append(dict(path=path,status=200,mime='image/webp',sha256=pub.sha(body)))
 return dict(state='public_banner_assets_verified',revision=target['revision'],assets=rows)
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['preflight','artifact','public-assets','provider-after','authorize-mutation']);p.add_argument('--region',required=True);p.add_argument('--report',required=True);a=p.parse_args()
 if a.mode=='authorize-mutation':
  Path(a.report).write_text(json.dumps(authorize_mutation(a.region),sort_keys=True,indent=2)+'\n');return
 target,pub=load(a.region)
 result={'preflight':preflight,'artifact':artifact,'public-assets':public_assets,'provider-after':provider_after}[a.mode](target,pub);pub.save(a.report,result)
if __name__=='__main__':main()
