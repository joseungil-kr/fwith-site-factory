"""Fail-closed exact build artifact binding. No credentials or publication API."""
from pathlib import Path, PurePosixPath
import argparse, importlib.util, json, os, re, stat, subprocess, zipfile
from reused import digest, compact, manifest, write_json
HERE = Path(__file__).resolve().parent
REPOSITORY = 'joseungil-kr/fwith-site-factory'
BUILD_CONTROL = 'd8c40e41c1dfacef47f43bf0b463919f330a48a5'
QA_REF = 'refs/heads/main'
BATCH_ID = 'phone-batch1-20261014'
ISSUE_TITLE = '[REGIONAL-BANNER-ARTIFACT-QA] batch1-20261014'
DOC = 'docs/shared-banner-phone-20261013/'
REGIONS = frozenset('anseong dongducheon gapyeong gimpo gunpo guri gwacheon gwangju hanam icheon jongno osan paju pocheon seoul-dobong seoul-dongdaemun seoul-gangbuk seoul-gangseo seoul-guro seoul-gwangjin seoul-jung seoul-jungnang seoul-nowon seoul-seongbuk seoul-seongdong seoul-yangcheon seoul-yongsan siheung uijeongbu uiwang yangju yangpyeong yeoncheon'.split())
CAPTURE_ROUTES = {'anseong': ['/', '/regions/ayang-dong/', '/regions/'], 'dongducheon': ['/', '/event/dongducheon-civic-hall-event-wreath/', '/regions/', '/event/'], 'gapyeong': ['/', '/regions/cheongpyeong-myeon/', '/regions/']}
REPRESENTATIVES = {k:v[1] for k,v in CAPTURE_ROUTES.items()}

VIEWPORTS = [(375,812),(1440,1000)]

def require(ok, message):
 if not ok: raise ValueError(message)

def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def validate_bindings(data,control,complete=True):
 require(data.get('schemaVersion')==1 and data.get('buildControlSha')==BUILD_CONTROL,'binding version/control')
 catalog=json.loads((control/DOC/'targets.json').read_text())['targets']
 require(set(catalog)==REGIONS and set(data.get('sites',{}))==REGIONS,'exact 33-site scope')
 selected=data.get('selectedRegions',[])
 require(isinstance(selected,list)and selected and len(selected)==len(set(selected))and set(selected)<=REGIONS,'explicit selected region scope')
 for region,row in data['sites'].items():
  target=catalog[region]
  require(row['sourceSha']==target['revision'],'source catalog mismatch: '+region)
  if region in selected:require(target['releaseReview'] is None and target['releaseReviewSha256'] is None,'publication gate changed')
  require(row['captureRoutes']==CAPTURE_ROUTES.get(region,['/']),'capture route selection')
  if row.get('build') is None:
   require(not complete or region not in selected,'incomplete build binding: '+region);continue
  build=row['build']
  require(set(build)=={'controlSha','runId','artifactId','archiveSha256','outputFilesSha256','releaseManifestSha256'},'build binding keys')
  require(re.fullmatch('[0-9a-f]{40}',build['controlSha']),'build control SHA')
  require(all(re.fullmatch('[0-9]+',str(build[k])) for k in ['runId','artifactId']),'run/artifact ids')
  require(all(re.fullmatch('[0-9a-f]{64}',build[k]) for k in ['archiveSha256','outputFilesSha256','releaseManifestSha256']),'artifact digest pins')
 return catalog

def validate_metadata(region,row,run,artifact):
 b=row['build'];require(b is not None,'build not bound')
 expected={'id':int(b['runId']),'head_sha':b['controlSha'],'head_branch':'main','path':'.github/workflows/shared-banner-phone-build-only.yml','status':'completed','conclusion':'success','run_attempt':1}
 require(all(run.get(k)==v for k,v in expected.items()),'build run metadata mismatch')
 require(run.get('event') in ('issues','workflow_dispatch'),'unexpected build event')
 require(run.get('repository',{}).get('full_name')==REPOSITORY,'build repository')
 require(run.get('actor',{}).get('login')=='joseungil-kr' and run.get('triggering_actor',{}).get('login')=='joseungil-kr','build actor')
 require(artifact.get('id')==int(b['artifactId']) and artifact.get('name')==f'phone-banner-{region}-build-{b["runId"]}','artifact identity')
 require(artifact.get('expired') is False and artifact.get('digest')=='sha256:'+b['archiveSha256'],'artifact API digest/expiry')
 wr=artifact.get('workflow_run',{})
 require(wr.get('id')==int(b['runId']) and wr.get('head_sha')==b['controlSha'] and wr.get('head_branch')=='main','artifact workflow binding')
 require(0<artifact.get('size_in_bytes',0)<=32*1024*1024,'archive size')

def summarize_run(run):
 """Public QA evidence excludes commit author emails and unrelated account data."""
 return {**{k:run.get(k)for k in ['id','status','conclusion','head_sha','head_branch','path','event','run_attempt','html_url']},'actorLogin':run['actor']['login'],'triggeringActorLogin':run['triggering_actor']['login'],'repository':run['repository']['full_name']}

def summarize_artifact(artifact):
 return {**{k:artifact.get(k)for k in ['id','name','size_in_bytes','digest','expired','url']},'workflow_run':{k:artifact['workflow_run'].get(k)for k in ['id','head_sha','head_branch']}}

def extract_bound_archive(archive,destination,expected_sha):
 require(digest(archive.read_bytes())==expected_sha,'downloaded ZIP digest mismatch')
 require(not destination.exists(),'extraction destination must be new')
 with zipfile.ZipFile(archive) as z:
  items=z.infolist();names=[i.filename for i in items]
  require(len(names)==len(set(names)) and len(items)<5000,'duplicate/oversized ZIP listing')
  require(sum(i.file_size for i in items)<=128*1024*1024,'ZIP expansion limit')
  for item in items:
   p=PurePosixPath(item.filename);mode=item.external_attr>>16
   require(not item.flag_bits&1 and not item.filename.startswith('/') and '\\'not in item.filename and '\x00'not in item.filename,'unsafe ZIP path')
   require(p.parts and all(x not in ('.','..') and not x.startswith('.') for x in p.parts),'ZIP traversal/hidden path')
   require(p.as_posix()==item.filename.rstrip('/'),'noncanonical ZIP path')
   require(stat.S_IFMT(mode) in (0,stat.S_IFREG,stat.S_IFDIR),'ZIP nonregular/symlink')
   require(item.filename=='release.json' or p.parts[0]=='dist','unexpected artifact root')
  destination.mkdir(parents=True)
  for item in items:
   p=destination/item.filename
   if item.is_dir():p.mkdir(parents=True,exist_ok=True)
   else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(item))
 require({p.name for p in destination.iterdir()}=={'dist','release.json'},'exact release root')
 return destination

def inspect_artifact(region,row,control,release,output):
 target=json.loads((control/DOC/'targets.json').read_text())['targets'][region]
 pub=load_module('fixed_'+region.replace('-','_'),control/f'scripts/direct-{region}/publish.py')
 qa=load_module('shared_phone_qa',control/'scripts/shared-banners/qa_phone_banners.py')
 raw=(release/'release.json').read_bytes();data=json.loads(raw);b=row['build']
 require(digest(raw)==b['releaseManifestSha256'],'release manifest bytes')
 files=pub.inventory(release/'dist')
 expected={'schemaVersion':1,'repository':REPOSITORY,'sourceBranch':target['branch'],'sourceRoot':target['root'],'revision':target['revision'],'controlRevision':b['controlSha'],'runId':str(b['runId']),'origin':'https://'+target['hostname'],'worker':target['worker'],'indexable':True,'files':files}
 require(data==expected,'exact release identity/inventory')
 require(digest(compact(files))==b['outputFilesSha256'],'output inventory digest')
 require(set(p for p in files if p.endswith('.html'))=={'404.html'}|{r.lstrip('/')+'index.html'for r in pub.ROUTES},'exact fixed HTML route set')
 require(set(row['captureRoutes'])<=pub.ROUTES,'capture route absent')
 previous={k:os.environ.get(k) for k in ['SITE_URL','SITE_INDEXABLE']}
 try:
  os.environ.update(SITE_URL=pub.ORIGIN,SITE_INDEXABLE='true');report=qa.inspect(release,control/DOC/'approved-assets.json')
 finally:
  for k,v in previous.items():
   if v is None:os.environ.pop(k,None)
   else:os.environ[k]=v
 (release/'shared-banner-qa.json').replace(output/'all-route-static-dom.json')
 for route in sorted(pub.ROUTES|{'/404.html'}):
  rel='404.html'if route=='/404.html'else route.lstrip('/')+'index.html';page=pub.Page((release/'dist'/rel).read_text())
  require(page.meta.get('site-factory-revision')==target['revision'],'all-route source revision')
  require(set(re.split(r'\s*,\s*',page.meta.get('robots','').lower()))==pub.expected_robots(route),'all-route robots')
 proof={'sourceSha':row['sourceSha'],'catalogControlSha':BUILD_CONTROL,'buildControlSha':b['controlSha'],**b,'region':region,'origin':pub.ORIGIN,'staticRouteCount':len(report['files']),'staticBannerCount':report['banners'],'files':files,'routes':sorted(pub.ROUTES|{'/404.html'}),'thinHubRoutes':sorted(pub.THIN_HUB_ROUTES),'captureRoutes':row['captureRoutes'],'exactAlts':qa.APPROVED_BANNER_ALTS}
 write_json(output/'artifact-binding.json',proof);return proof

def verify_checkout(root,sha):
 def git(*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
 require(git('rev-parse','HEAD')==sha,'control checkout SHA')
 require(not git('status','--porcelain','--untracked-files=all'),'control checkout changed')

def verify_runner():
 require(os.environ.get('GITHUB_ACTIONS')=='true','GitHub Actions runner required; local browser prohibited')
 require(os.environ.get('GITHUB_REPOSITORY')==REPOSITORY and os.environ.get('GITHUB_REF')==QA_REF,'QA repository/branch')
 require(os.environ.get('GITHUB_RUN_ATTEMPT')=='1','QA rerun requires new evidence')
 require(re.fullmatch('[0-9a-f]{40}',os.environ.get('GITHUB_SHA','')),'QA control SHA')
 require(os.environ.get('GITHUB_ACTOR')=='joseungil-kr' and os.environ.get('GITHUB_TRIGGERING_ACTOR')=='joseungil-kr','QA owner actor')
 event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
 expected_sha=digest((HERE/'bindings.json').read_bytes())
 if os.environ.get('GITHUB_EVENT_NAME')=='issues':
  issue=event.get('issue',{})
  require(event.get('action')=='opened' and issue.get('title')==ISSUE_TITLE and issue.get('user',{}).get('login')=='joseungil-kr','QA issue owner/title')
  payload=json.loads(issue.get('body',''))
  require(payload=={'schemaVersion':1,'batchId':BATCH_ID,'bindingsSha256':expected_sha},'QA exact issue payload')
 elif os.environ.get('GITHUB_EVENT_NAME')=='workflow_dispatch':
  require(event.get('inputs',{})=={'batch_id':BATCH_ID,'expected_bindings_sha256':expected_sha},'QA exact dispatch payload')
 else:raise ValueError('QA event not allowed')

def main():
 p=argparse.ArgumentParser();p.add_argument('--control',type=Path,required=True);p.add_argument('--bindings',type=Path,default=HERE/'bindings.json');a=p.parse_args()
 verify_runner();verify_checkout(a.control,BUILD_CONTROL);verify_checkout(HERE.parents[2],os.environ['GITHUB_SHA'])
 data=json.loads(a.bindings.read_text());validate_bindings(data,a.control)
 print(json.dumps({'region':data['selectedRegions']}))
if __name__=='__main__':main()

