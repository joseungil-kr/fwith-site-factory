"""Read-only pinned source58 build, loopback browser and artifact verification.

No provider credentials, publication client or IndexNow client is used.
"""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,math,os,re,subprocess,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
BINDING_SHA='1d1d93825760a6737ece812a74cb4472af8ce062441ac763683304b5fc37523f'
SOURCE='adb3bca82918744e99bbf23c346e95053af64322'
TITLE='[JANGHEUNG-PRODUCTION-BUILD] source58-20261017'
REPO='joseungil-kr/fwith-site-factory';OWNER='joseungil-kr'
def require(ok,message):
 if not ok:raise ValueError(message)
def sha(b):return hashlib.sha256(b).hexdigest()
def save(path,obj):p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def safe(root,rel):
 rel=Path(rel);require(not rel.is_absolute() and '..'not in rel.parts,'Unsafe relative path');p=Path(root).absolute()/rel
 for x in [p,*p.parents]:require(not x.is_symlink(),'Symlink source/control path')
 require(p.is_file(),'Regular source file required');return p

def binding():
 raw=safe(ROOT,'bindings.json').read_bytes();require(BINDING_SHA and sha(raw)==BINDING_SHA,'Unbound or changed production QA binding');b=json.loads(raw)
 require(b['schema']=='jangheung-production58-actions-qa/v1'and b['repository']==REPO and b['sourceBranch']=='source/jangheung-production-preparation-20261017'and b['privateSourceRevision']==SOURCE,'Fixed source identity mismatch')
 require(b['phase']=='BOUND_REVIEW_AND_REMOTE_SAVE'and re.fullmatch('[0-9a-f]{40}',b['assemblyRevision']or'')and b['assemblyRevision']!=SOURCE,'Actual reviewed saved source58 required')
 require(b['sourceFiles']==58 and len(b['files'])==58 and len({r['path']for r in b['files']})==58,'Exact source58 required')
 require(b['permissions']=={'contents':'read'}and all(b[k]is False for k in ['publicationReady','providerWrites','indexNowEnabled','newCredentials']),'Read-only boundary changed')
 refs={}
 for key in ['production4Review','source58SaveVerification','source58Readback']:
  ref=b[key];require(type(ref)is dict and sha(ref['rawUTF8'].encode())==ref['sha256'],'Embedded review/readback evidence changed');refs[key]=json.loads(ref['rawUTF8'])
 review=refs['production4Review'];saved=refs['source58SaveVerification'];readback=refs['source58Readback']
 require(review['overall']=='PASS_LOCAL_PRODUCTION4_OUTPUT15_ONLY'and review['production4ManifestSHA256']==b['production4ManifestSHA256']and review['requiredFindings']==[]and review['sourceRevision']==SOURCE and review['production4AcceptedFiles']==4 and review['productionOutputFiles']==15,'Exact production4 acceptance absent')
 require(saved['commit']==b['assemblyRevision']and saved['parent']==SOURCE and saved['branch']==b['sourceBranch']and saved['sourceFilesVerified']==58 and saved['readbackManifestSHA256']==b['source58Readback']['sha256']and saved['mainWrites']==0 and saved['providerWrites']==0 and saved['publicationReady']is False,'Saved source58 boundary changed')
 require(readback['files']==b['files']and readback['commit']==b['assemblyRevision'],'Source58 bytes projection mismatch')
 require(sha(json.dumps(b['browserExpected'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())==b['browserExpectedSHA256'],'Expected Jangheung observation fixture changed')
 for name,key in [('capture_production.py','captureSHA256'),('browser_evidence.py','browserEvidenceSHA256')]:require(sha(safe(ROOT,name).read_bytes())==b[key],'Reviewed browser control changed')
 return b

def owner(env,event):
 require(all(env.get(k)==v for k,v in {'GITHUB_REPOSITORY':REPO,'GITHUB_REF':'refs/heads/main','GITHUB_ACTOR':OWNER,'GITHUB_TRIGGERING_ACTOR':OWNER,'GITHUB_RUN_ATTEMPT':'1','GITHUB_EVENT_NAME':'issues'}.items()),'Owner/first-attempt/main boundary')
 require(re.fullmatch('[0-9a-f]{40}',env.get('GITHUB_SHA',''))and re.fullmatch('[1-9][0-9]*',env.get('GITHUB_RUN_ID','')),'Control/run identity absent')
 issue=event.get('issue',{});require(event.get('action')=='opened'and issue.get('title')==TITLE and issue.get('user',{}).get('login')==OWNER and issue.get('user',{}).get('type')=='User','Exact owner issue absent')
 require(type(issue.get('number'))is int and issue['number']>0,'Positive integer issue number required')
 return {'repository':REPO,'controlRevision':env['GITHUB_SHA'],'runId':int(env['GITHUB_RUN_ID']),'runAttempt':1,'issueNumber':issue['number']}

def control_identity(env):
 result=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT.parents[2],capture_output=True,text=True)
 require(result.returncode==0 and result.stdout.strip()==env.get('GITHUB_SHA'),'Actual control checkout HEAD mismatch')
 return result.stdout.strip()

def check_files(checkout,b,git_required=True):
 checkout=Path(checkout).absolute()
 if git_required:
  result=subprocess.run(['git','rev-parse','HEAD'],cwd=checkout,capture_output=True,text=True);require(result.returncode==0 and result.stdout.strip()==b['assemblyRevision'],'Actual checkout HEAD mismatch')
 for row in b['files']:
  raw=safe(checkout,row['path']).read_bytes();require(len(raw)==row['bytes']and sha(raw)==row['sha256']and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['gitBlobSHA'],'Source58 file changed: '+row['path'])
 prefix='scripts/direct-jangheung/production-release';parent=checkout/prefix;actual=set()
 for p in parent.rglob('*'):
  require(not p.is_symlink()and(p.is_dir()or p.is_file()),'Nonregular adapter input')
  if p.is_file():actual.add(p.relative_to(checkout).as_posix())
 require(actual=={r['path']for r in b['files']if r['path'].startswith(prefix+'/')},'Unexpected adapter input')
 spec=importlib.util.spec_from_file_location('jangheung_production',parent/'production_adapter.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 source=checkout/'site-factory/jangheung-flower';module.check_source(source);return module,source,b

def postbuild(checkout,dist,b):
 module,source,qb=check_files(checkout,b);r=module.validate(source,dist,b['assemblyRevision']);r['assemblyCommitExternallyVerified']=True;r['controlRevision']=os.environ.get('GITHUB_SHA');return r

def verify_geometry(g,width,height):
 require(type(g)is dict and set(g)=={'scrollX','scrollY','width','height','documentHeight','fontStatus'} and type(g.get('scrollX'))in [int,float] and g.get('width')==width and g.get('height')==height and g.get('scrollX')==0 and g.get('fontStatus')=='loaded','Capture viewport/fonts mismatch')
 for name in ['scrollY','documentHeight']:
  v=g.get(name);require(type(v)in [int,float]and math.isfinite(v)and v>=0,'Invalid capture geometry')
 require(g['documentHeight']>=height and int(g['scrollY'])==g['scrollY'],'Capture document/scroll geometry')
 return g

STICKY_SECTIONS=('products','eligibility','delivery','location','timing','ribbon','faq','sources')
def sticky_names():return {f'home-1280-{section}.png'for section in STICKY_SECTIONS}
def verify_header(header,expected):
 require(type(header)is dict and set(header)=={'rect','position','top','zIndex','backgroundColor','backdropFilter','borderBottomWidth','observations'},'Sticky header observation schema')
 require(type(header['rect'])is dict and all(type(v)in [int,float]and math.isfinite(v)for v in header['rect'].values()),'Sticky header rect numeric values')
 require(header['rect']=={'x':0,'y':0,'width':1280,'height':71} and all(header[k]==v for k,v in {'position':'sticky','top':'0px','zIndex':'20','backgroundColor':'rgba(255, 255, 255, 0.96)','backdropFilter':'blur(10px)','borderBottomWidth':'1px'}.items()),'Fixed sticky header geometry/style changed')
 rows=header['observations'];require(type(rows)is list and len(rows)==6,'Exact sticky header occurrences absent')
 for row,e in zip(rows,expected):
  require(row.get('key')==e['key'] and re.sub(r'\s+',' ',row.get('text','')).strip()==re.sub(r'\s+',' ',e['text']).strip() and row.get('tag')==e['tag'] and row.get('href')==e.get('href') and row.get('available')is True,'Sticky header copy/visibility mismatch')
  r=row.get('rect',{});require(set(r)=={'x','y','width','height'} and all(type(v)in [int,float]and math.isfinite(v)for v in r.values()),'Sticky header occurrence rect')
  require(r['width']>0 and r['height']>0 and r['x']>=0 and r['y']>=0 and r['x']+r['width']<=1280 and r['y']+r['height']<=71,'Sticky header occurrence outside actual clip')
 return header

def verify_browser(checkout,dist,b,git_required=True,*,allow_unit_fixture=False):
 module,source,qb=check_files(checkout,b,git_required);module.validate(source,dist,b['assemblyRevision']);import browser_evidence as q
 folder=source/'candidate/evidence/browser';r=q.read(folder/'production-capture.json');q.check_fixture_boundary(r,allow_unit_fixture)
 result=q.verify_browser(source/'candidate',qb,allow_unit_fixture=allow_unit_fixture)
 require(r['privateSourceRevision']==SOURCE and r['assemblyRevision']==b['assemblyRevision']and r['origin']=='loopback-only'and r['publicHTTPVerified']is False and r['publicationReady']is False,'Private capture identity/boundary')
 wanted=[(w,route)for w in [320,390,1280]for route in ['/','/404.html']]
 for row,(width,route)in zip(q.records(r.get('metadata'),6,'Production metadata'),wanted):
  require(row=={'width':width,'route':route,'robots':'index,follow'if route=='/'else'noindex,nofollow','canonical':['https://jangheung.fwith.kr/']if route=='/'else[],'source':b['assemblyRevision'],'privateSource':SOURCE,'releaseState':'production-candidate','social':[list(x)for x in module.social_values(module.read_contract(),module.verify_inputs(source)[2])]if route=='/'else[]},'Actual production DOM metadata changed')
 notfound=(Path(dist)/'404.html').read_bytes();require(r.get('missingRoute')=={'path':'/.jangheung-private-missing/','status':404,'sha256':sha(notfound),'bytes':len(notfound),'robots':'noindex,nofollow','canonicalCount':0},'Actual missing-route404 response mismatch')
 expected_http={('/'if n=='index.html'else'/'+n):(n,v)for n,v in sorted(module.inventory(dist).items())}
 rows=q.records(r.get('httpFiles'),15,'Exact production HTTP15');require([x.get('path')for x in rows]==list(expected_http),'HTTP path ordering/inventory mismatch')
 for row in rows:
  path=row['path'];name,data=expected_http[path];require(row.get('status')==200 and row.get('sha256')==sha(data)and row.get('bytes')==len(data)and row.get('finalURLPath')==path,'Actual HTTP bytes/status mismatch')
  expected_type='application/octet-stream'if name=='_headers'else'text/html'if name.endswith('.html')else 'text/plain'if name.endswith('.txt')else'text/css'if name.endswith('.css')else'application/xml'if name.endswith('.xml')else'image/jpeg'if name.endswith('.jpg')else'image/webp'
  require(str(row.get('contentType')).split(';')[0]==expected_type,'Actual HTTP MIME mismatch')
 paint=q
 captures=q.records(r.get('captures'),34,'Stable capture34');expected_names=q.screenshot_expectations(qb['browserExpected']);require(len({x.get('path')for x in captures})==34 and {x.get('path')for x in captures}==set(expected_names),'Capture34 inventory mismatch')
 geometries={};headers={}
 header_expected=[e for e in qb['browserExpected']['occurrences']['/']if e['key'] in ['ui.brandLabel','ui.regionLabel','ui.navigation.0','ui.navigation.1','ui.navigation.2','ui.navigation.3']]
 require(len(header_expected)==6,'Fixed header input mismatch')
 for cap in captures:
  name=cap['path'];width,height=expected_names[name];height=844
  before=verify_geometry(cap['before'],width,height);require(before==verify_geometry(cap['after'],width,height),'Capture geometry changed')
  s=cap.get('settle',{});samples=s.get('samples',[]);require(s.get('stableTransitions')==5 and type(samples)is list and 6<=len(samples)<=180,'Stable frame evidence absent')
  for sample in samples:verify_geometry(sample,width,height)
  require(all(x==before for x in samples[-6:]),'Last six frames differ');require(cap.get('fullPage')==name.endswith('-full.png'),'Full/viewport flag changed')
  geometries[name]=before
  scope='eligibility'if name.endswith('-eligibility.png')else None
  if scope:
   observed=cap.get('purchaseSnapshot');require(type(observed)is dict and set(observed)=={'scope','before','after','screenshotSHA256'}and observed['scope']==scope and observed['before']==observed['after'],'Purchase eligibility before/after snapshot absent or changed')
   q.verify_purchase(observed['before'],qb['browserExpected']['purchase'],width,scope)
   require(observed['screenshotSHA256']==sha(q.safe_file(folder,name).read_bytes()),'Purchase eligibility screenshot binding changed')
  else:require('purchaseSnapshot'not in cap,'Unexpected restriction screenshot scope')
  if name in sticky_names():
   h=cap.get('stickyHeader');require(type(h)is dict and set(h)=={'path','sha256','before','after','geometryAfter'},'Sticky header capture absent')
   require(h['path']=='sticky-headers/'+name and h['geometryAfter']==before,'Sticky clip path or scroll changed')
   require(verify_header(h['before'],header_expected)==verify_header(h['after'],header_expected),'Sticky header changed while capturing')
   raw=q.safe_file(folder,h['path']).read_bytes();require(sha(raw)==h['sha256'],'Sticky header PNG bytes mismatch');hi,hp=paint.decoded_pixels(raw)
   require(hi['width']==1280 and hi['height']==71,'Sticky header PNG dimensions changed');headers[name]=(hi,hp)
  else:require(cap.get('stickyHeader')is None,'Unexpected sticky exclusion')
 require(set(headers)==sticky_names(),'Exact eight desktop sticky references required')
 require({p.relative_to(folder).as_posix()for p in folder.rglob('*')if p.is_file()}==set(expected_names)|{'sticky-headers/'+n for n in sticky_names()}|{'browser-report.json','production-capture.json'},'Exact browser42 PNG/two-report inventory changed')
 for p in folder.rglob('*'):require(not p.is_symlink()and(p.is_file()or p.is_dir()),'Nonregular browser evidence')
 decoded={};pixel_results=[]
 for width in [320,390,1280]:
  full_name=f'home-{width}-full.png';fi,fp=paint.decoded_pixels((folder/full_name).read_bytes());require(geometries[full_name]['scrollY']==0 and geometries[full_name]['documentHeight']==fi['height'],'Full-page origin/height mismatch');stride=width*fi['channels']
  for name,g in geometries.items():
   if not name.startswith(f'home-{width}-')or name==full_name:continue
   vi,vp=paint.decoded_pixels((folder/name).read_bytes());start=int(g['scrollY'])*stride
   require(vi['channels']==fi['channels']and g['documentHeight']==fi['height']and g['scrollY']+844<=fi['height'],'Viewport/full geometry mismatch')
   reference=fp[start:start+844*stride];header_rows=0
   if name in headers:
    hi,hp=headers[name];require(hi['channels']==vi['channels']and vp[:71*stride]==hp,'Sticky header raster differs from observed clip: '+name);header_rows=71
   require(vp[header_rows*stride:]==reference[header_rows*stride:],'Incomplete/mismatched body raster versus full reference: '+name)
   pixel_results.append({'path':name,'matchingRows':844,'fullReferenceRows':844-header_rows,'stickyReferenceRows':header_rows,'scrollY':g['scrollY'],'decodedPixelsSHA256':sha(vp)})
 require(len(pixel_results)==27,'All 27 home viewport captures required')
 facts={'privateSourceRevision':SOURCE,'assemblyRevision':b['assemblyRevision'],'productionMetadataStatesVerified':6,'productionHTTPFilesVerified':15,'socialDOMStatesVerified':6,'stableCapturesVerified':34,'stickyHeaderReferencesVerified':8,'totalPNGFilesVerified':42,'purchaseViewportSnapshotsVerified':3,'homeViewportFullPixelComparisons':pixel_results,'independentScreenshotReview':'PENDING','publicHTTPVerified':False,'publicationReady':False}
 if allow_unit_fixture:result['syntheticChecks'].update(q.fixture_facts(facts))
 else:result.update(facts)
 return result

def package_release(checkout,dist,b,env,event):
 require(env.get('NATIVE_GATES_PASSED')=='true','Successful native gates required before packaging');selected=owner(env,event);control_identity(env)
 browser=verify_browser(checkout,dist,b);module,source,_=check_files(checkout,b);facts=module.validate(source,dist,b['assemblyRevision'])
 dist=Path(dist).absolute();release=dist.parent
 require(dist.name=='dist'and release.name=='release'and not release.is_symlink()and {p.name for p in release.iterdir()}=={'dist'},'Fresh exact release/dist package required')
 for p in [release,*release.parents]:require(not p.is_symlink(),'Release package parent symlink forbidden')
 manifest=module.release_manifest(facts['files'],b['assemblyRevision'],selected['controlRevision'],str(selected['runId']),BINDING_SHA)
 module.validate_release_manifest(manifest,facts['files'],b['assemblyRevision'],selected['controlRevision'],str(selected['runId']),BINDING_SHA)
 raw=module.release_manifest_bytes(manifest);path=release/'release.json';require(not path.exists(),'Existing release manifest forbidden');path.write_bytes(raw);require(path.read_bytes()==raw,'Release manifest write/readback mismatch')
 return {'state':'READONLY_PRODUCTION_PACKAGE_VERIFIED','assemblyRevision':b['assemblyRevision'],'controlRevision':selected['controlRevision'],'runId':selected['runId'],'releaseManifestSHA256':sha(raw),'outputFilesSHA256':sha(json.dumps(facts['files'],sort_keys=True,separators=(',',':')).encode()),'sourceContractSHA256':module.CONTRACT_SHA,'bindingSHA256':BINDING_SHA,'productionDistFiles':15,'releaseManifestKeys':sorted(module.RELEASE_KEYS),'automatedBrowserChecksPassed':browser['automatedBrowserChecksPassed'],'mainScreenshots':34,'stickyHeaderClips':8,'actualIndependentScreenshotReview':'PENDING','publicHTTPVerified':False,'publicationReady':False}

def seal(evidence):
 evidence=Path(evidence);rows=[]
 for p in sorted(evidence.rglob('*')):
  require(not p.is_symlink(),'Evidence symlink forbidden')
  if p.is_file()and p.name!='artifact-manifest.json':rows.append({'path':p.relative_to(evidence).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())})
 save(evidence/'artifact-manifest.json',{'files':rows,'independentReview':'PENDING','publicHTTPVerified':False,'publicationReady':False});return {'files':len(rows)}

def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['select','prebuild','postbuild','browser','package','seal']);p.add_argument('--checkout');p.add_argument('--dist');p.add_argument('--report');p.add_argument('--evidence');a=p.parse_args();b=binding();control_identity(os.environ)
 if a.mode=='select':
  event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text());r=owner(os.environ,event);control_identity(os.environ);r.update({'assemblyRevision':b['assemblyRevision'],'sourceBranch':b['sourceBranch'],'privateSourceRevision':SOURCE})
  with open(os.environ['GITHUB_OUTPUT'],'a')as f:f.write('source_sha='+b['assemblyRevision']+'\n')
 elif a.mode=='seal':r=seal(a.evidence)
 elif a.mode=='prebuild':m,s,q=check_files(a.checkout,b);r={'sourceFilesVerified':58,'privateSourceRevision':SOURCE,'assemblyRevision':b['assemblyRevision'],'assemblyCommitExternallyVerified':True,'publicationReady':False}
 elif a.mode=='postbuild':r=postbuild(a.checkout,a.dist,b)
 elif a.mode=='package':r=package_release(a.checkout,a.dist,b,os.environ,json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text()))
 else:r=verify_browser(a.checkout,a.dist,b)
 if a.report:save(a.report,r)
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
