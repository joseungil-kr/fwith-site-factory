"""Read-only private Gangjin source48, output11 and loopback browser controls.

No provider writes, publication adapter, release packaging, key creation or remote Git writes.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,math,os,re,subprocess,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
BINDING_SHA='014b603e47c65ee63e89273e189908e1feb64eb61119b56e7118c15a92d6fd40'
SOURCE_REVISION='683487ff86f8505076e8f595a6b8e54b2aa9a6e6'
TITLE='[GANGJIN-PRIVATE-QA] source48-20261016'
REPO='joseungil-kr/fwith-site-factory';OWNER='joseungil-kr'
PREFIX='site-factory/gangjin-flower';BRANCH='source/gangjin-private-qa-20261016'
SOURCE_MANIFEST_SHA='422050e5f6c153d92406f245dc8050d9710e8811e53b6014b231206a41b3d72a'
SOURCE_ZIP_SHA='b9b7828b82ff63fb8ed6b161b7dd8d3e62a7ae7cecde61f5f270fd980ba55533'
STATIC_REVIEW_MANIFEST_SHA='8b97f15f5514ba94f17d1cfeed8973dbfc72117a8b5fe98a15b8ca55476abc15'
STICKY_SECTIONS=('restriction','products','delivery','location','timing','ribbon','faq','sources')
def require(ok,message):
 if not ok:raise ValueError(message)
def fail(message):raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def save(path,obj):p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def safe_file(root,relative):
 require(isinstance(relative,str)and relative and not relative.startswith('/')and '\\'not in relative and '..'not in Path(relative).parts,'Unsafe source path')
 root=Path(root);current=root;require(not root.is_symlink(),'Symlink root')
 for part in Path(relative).parts:
  current=current/part;require(not current.is_symlink(),'Symlink source')
 require(current.is_file(),'Missing regular source file: '+relative);return current
safe=safe_file

def validate_binding(b,require_bound=True):
 require(b.get('schema')=='gangjin-private-source48-actions-qa/v1'and b.get('repository')==REPO and b.get('owner')==OWNER and b.get('sourceBranch')==BRANCH and b.get('sourcePrefix')==PREFIX,'Fixed source identity changed')
 require(b.get('sourceManifestSHA256')==SOURCE_MANIFEST_SHA and sha(b.get('sourceManifestUTF8','').encode())==SOURCE_MANIFEST_SHA and b.get('sourceZIP_SHA256')==SOURCE_ZIP_SHA,'Frozen source identity changed')
 m=json.loads(b['sourceManifestUTF8']);original=m['files'];rows=b.get('files',[])
 require(b.get('sourceFiles')==48 and len(original)==len(rows)==len({r['path']for r in rows})==48,'Exact source48 required')
 for row,origin in zip(rows,original):
  require({k:row[k]for k in ['path','bytes','sha256','gitBlobSHA']}==origin and re.fullmatch('[0-9a-f]{40}',row.get('gitBlobSHA','')),'Frozen source row changed')
 require(b.get('permissions')=={'contents':'read'} and all(b.get(k)is False for k in ['providerWrites','productionEnabled','indexNowEnabled','newCredentials','remoteGitWrites','publicationReady']),'Read-only private boundary changed')
 require(b.get('facilityPages')=='HOLD'and b.get('facilityPageCount')==5 and b.get('copyCharacters')==2991 and 'shippingKRW'in b and b['shippingKRW']is None and b.get('specificShippingKRW')=={'마량면':10000},'Accepted content boundary changed')
 ref=b.get('staticReview',{});require(ref.get('manifestSHA256')==STATIC_REVIEW_MANIFEST_SHA and sha(ref.get('rawUTF8','').encode())==ref.get('sha256'),'Static review evidence changed')
 review=json.loads(ref['rawUTF8']);require(review.get('status')=='PASS_LOCAL_STATIC_IMPLEMENTATION_AND_REPRODUCTION_ONLY'and review.get('blockingFindings')==[] and review.get('requiredCodeChanges')==[] and review.get('sourceFiles')==48 and review.get('outputFiles')==11 and review.get('directOutputByteEquality')is True and review.get('sourceManifestSHA256')==SOURCE_MANIFEST_SHA and review.get('sourceArchiveSHA256')==SOURCE_ZIP_SHA and review.get('verdicts',{}).get('actualScreen')=='UNVERIFIED_CHROMIUM_SOCKET_DENIAL'and review.get('facilitySalesPages')=='HOLD_5','Independent static acceptance absent')
 fixture=b.get('browserExpected');require(sha(json.dumps(fixture,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())==b.get('browserExpectedSHA256'),'Expected browser observations changed')
 require(fixture['widths']==[320,390,1280]and fixture['viewportHeight']==844 and len(fixture['occurrences']['/'])==89 and len(fixture['occurrences']['/404.html'])==14 and len(fixture['images'])==7,'Browser fixture scope changed')
 output=b.get('expectedDistFiles',{});require(sha(json.dumps(output,sort_keys=True,separators=(',',':')).encode())==b.get('expectedDistFilesSHA256')and len(output)==11 and {'index.html','404.html','robots.txt'}<=set(output)and len([x for x in output if x.endswith('.html')])==2,'Exact private output11 map changed')
 require(all(re.fullmatch('[0-9a-f]{64}',x)for x in output.values()),'Invalid output digest')
 if require_bound:
  require(b.get('phase')=='BOUND_REMOTE_SOURCE48'and re.fullmatch('[0-9a-f]{40}',SOURCE_REVISION or'')and b.get('sourceRevision')==SOURCE_REVISION,'Source commit not bound; preparation is not executable')
  ref=b.get('remoteSaveVerification');require(type(ref)is dict and sha(ref.get('rawUTF8','').encode())==ref.get('sha256'),'Remote source save verification missing or changed')
  receipt=json.loads(ref['rawUTF8']);require(receipt.get('commit')==SOURCE_REVISION and receipt.get('branch')==BRANCH and receipt.get('sourceManifestSHA256')==SOURCE_MANIFEST_SHA and receipt.get('sourceFiles')==48 and receipt.get('source48UnchangedAfterBuild')is True and receipt.get('acceptedOutput11DirectByteParity')is True and receipt.get('downloadedOnlySourceBuild')is True and receipt.get('mainWrites')==0 and receipt.get('providerWrites')==0 and receipt.get('publicationReady')is False,'Remote source48 readback scope changed')
  back=b.get('remoteSourceReadback',{});require(sha(back.get('rawUTF8','').encode())==back.get('sha256')==receipt.get('readbackManifestSHA256'),'Remote byte readback manifest changed')
  readback=json.loads(back['rawUTF8']);require(readback.get('commit')==SOURCE_REVISION and readback.get('branch')==BRANCH and readback.get('fileCount')==48 and readback.get('allFilesMatchAcceptedSource')is True,'Remote source48 byte receipt changed')
  remote_rows=readback.get('files',[]);require(len(remote_rows)==48,'Remote source48 byte projection count changed')
  for row,remote in zip(rows,remote_rows):require(all(remote.get(k)==row[k]for k in ['path','bytes','sha256','gitBlobSHA'])and remote.get('remotePath')==PREFIX+'/'+row['path']and remote.get('fetchedSHA256')==row['sha256']and remote.get('fetchedGitBlobSHA')==row['gitBlobSHA'],'Remote source48 byte projection changed')
  independent=b.get('independentRemoteSourceReview',{});require(type(independent)is dict and independent.get('sha256')=='6365e23282571f52c64d5af30d6eb5c55b2669f37de822630fc776079c22798a'and independent.get('manifestSHA256')=='c6d2bab4738e29bc1f4650ec4b0ab7cdfd75fe086553730fc6e9a4dc28aae40e'and sha(independent.get('rawUTF8','').encode())==independent.get('sha256'),'Independent remote source acceptance changed')
  accepted=json.loads(independent['rawUTF8']);require(accepted.get('status')=='PASS_SOURCE48_REMOTE_SAVE_AND_DOWNLOADED_ONLY_REPRODUCTION'and accepted.get('blockingFindings')==[]and accepted.get('requiredSourceChanges')==[]and accepted.get('sourceCommit')==SOURCE_REVISION and accepted.get('branch')==BRANCH and accepted.get('sourceManifestSHA256')==SOURCE_MANIFEST_SHA and accepted.get('sourceArchiveSHA256')==SOURCE_ZIP_SHA and accepted.get('authorSaveManifestSHA256')==b.get('sourceSaveManifestSHA256')=='5937084cd045d055839cd20efcfe165fbc18c0df44da422e22350f2fb60fab45'and accepted.get('acceptedStaticReviewManifestSHA256')==STATIC_REVIEW_MANIFEST_SHA and accepted.get('sourceFilesIndependentlyFetched')==48 and accepted.get('sourceBytesSHA256GitBlobAndZIPParity')is True and accepted.get('downloadedOnlyBuild')is True and accepted.get('outputFilesActualBytesEqualBothAcceptedOutputs')==11 and accepted.get('sourceUnchangedAfterBuild')is True and accepted.get('controlsAccepted')is False and accepted.get('browserExecuted')is False and accepted.get('publicHTTPVerified')is False and accepted.get('IndexNowSubmitted')is False and accepted.get('keysOrProofCreated')is False and accepted.get('publicationReady')is False and accepted.get('facilityPages')=='HOLD_5','Independent remote acceptance scope changed')
 return m

def binding(require_bound=True):
 raw=safe_file(ROOT,'bindings.json').read_bytes();require(sha(raw)==BINDING_SHA,'Unbound or changed QA binding');b=json.loads(raw);validate_binding(b,require_bound)
 for name,key in [('capture_private.py','captureSHA256'),('browser_evidence.py','browserEvidenceSHA256')]:require(sha(safe_file(ROOT,name).read_bytes())==b[key],'Reviewed browser control changed')
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



def check_source_files(root,b,postbuild=False):
 m=validate_binding(b,require_bound=False);root=Path(root);expected={r['path']:r for r in b['files']};actual=[]
 for p in root.rglob('*'):
  rel=p.relative_to(root)
  # These are generated only by authorized dependency install/build/QA, never accepted as source.
  if postbuild and len(rel.parts)>=2 and rel.parts[:2] in [('candidate','node_modules'),('candidate','dist'),('candidate','.astro'),('candidate','evidence')]:continue
  if postbuild and len(rel.parts)==4 and rel.parts[:3]==('candidate','scripts','__pycache__'):
   modules={Path(name).stem for name in expected if name.startswith('candidate/scripts/') and name.endswith('.py')}
   if any(re.fullmatch(re.escape(module)+r'\.cpython-[0-9]+(?:\.opt-[0-9]+)?\.pyc',rel.name) for module in modules):
    if p.is_symlink() or not p.is_file():fail('Unexpected compiled cache type')
    continue
  if p.is_symlink():fail('Unexpected source symlink')
  if p.is_file():actual.append(rel.as_posix())
 if set(actual)!=set(expected):fail('Exact source file inventory mismatch')
 for name,row in expected.items():
  data=safe_file(root,name).read_bytes()
  if len(data)!=row['bytes'] or sha(data)!=row['sha256']:fail('Source byte mismatch: '+name)
  if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=row['gitBlobSHA']:fail('Git blob mismatch')
  if not name.startswith('candidate/public/images/'):data.decode('utf8')
 return {'verifiedSourceFiles':48,'utf8Files':41,'existingBinaryPaths':7,'sourceBytesUnchanged':True}

def check_dist(dist,b):
 dist=Path(dist);require(dist.is_dir()and not dist.is_symlink(),'Regular output directory required');actual={}
 for p in dist.rglob('*'):
  if p.is_symlink():fail('Symlink output')
  if p.is_file():actual[p.relative_to(dist).as_posix()]=sha(p.read_bytes())
 if actual!=b['expectedDistFiles']:fail('Private output differs from independently accepted exact bytes')
 return {'distFiles':11,'exactAcceptedPrivateOutputParity':True,'canonical':None,'sitemap':False,'robots':'noindex,nofollow','actualBrowserVerified':False}



def check_files(checkout,b,git_required=True,postbuild=False):
 checkout=Path(checkout).resolve()
 if git_required:
  result=subprocess.run(['git','rev-parse','HEAD'],cwd=checkout,capture_output=True,text=True);require(result.returncode==0 and result.stdout.strip()==b['sourceRevision'],'Actual checkout HEAD mismatch')
 return check_source_files(checkout/PREFIX,b,postbuild)

def inventory(dist):
 dist=Path(dist);result={}
 for p in sorted(dist.rglob('*')):
  require(not p.is_symlink()and(p.is_file()or p.is_dir()),'Nonregular output')
  if p.is_file():result[p.relative_to(dist).as_posix()]=p.read_bytes()
 return result

def verify_geometry(g,width,height):
 require(type(g)is dict and set(g)=={'scrollX','scrollY','width','height','documentHeight','fontStatus'} and type(g.get('scrollX'))in [int,float] and g.get('width')==width and g.get('height')==height and g.get('scrollX')==0 and g.get('fontStatus')=='loaded','Capture viewport/fonts mismatch')
 for name in ['scrollY','documentHeight']:
  v=g.get(name);require(type(v)in [int,float]and math.isfinite(v)and v>=0,'Invalid capture geometry')
 require(g['documentHeight']>=height and int(g['scrollY'])==g['scrollY'],'Capture document/scroll geometry')
 return g

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
 check_files(checkout,b,git_required,postbuild=True);source=Path(checkout)/PREFIX;qb=b;check_dist(dist,b);import browser_evidence as q
 folder=source/'candidate/evidence/browser';r=q.read(folder/'private-capture.json');q.check_fixture_boundary(r,allow_unit_fixture)
 result=q.verify_browser(source/'candidate',qb,allow_unit_fixture=allow_unit_fixture)
 require(r['sourceRevision']==b['sourceRevision']and r['origin']=='loopback-only'and r['publicHTTPVerified']is False and r['publicationReady']is False,'Private capture identity/boundary')
 wanted=[(w,route)for w in [320,390,1280]for route in ['/','/404.html']]
 for row,(width,route)in zip(q.records(r.get('metadata'),6,'Private metadata'),wanted):
  require(row=={'width':width,'route':route,'robots':'noindex,nofollow','canonical':[],'productionMetadata':[],'social':[]},'Actual private DOM metadata changed')
 notfound=(Path(dist)/'404.html').read_bytes();require(r.get('missingRoute')=={'path':'/.gangjin-private-missing/','status':404,'sha256':sha(notfound),'bytes':len(notfound),'robots':'noindex,nofollow','canonicalCount':0},'Actual missing-route404 response mismatch')
 expected_http={('/'if n=='index.html'else'/'+n):(n,v)for n,v in sorted(inventory(dist).items())}
 rows=q.records(r.get('httpFiles'),11,'Exact private HTTP11');require([x.get('path')for x in rows]==list(expected_http),'HTTP path ordering/inventory mismatch')
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
  scope='restriction'if name.endswith('-restriction.png')else'products'if name.endswith('-products.png')else None
  if scope:
   observed=cap.get('restrictionSnapshot');require(type(observed)is dict and set(observed)=={'scope','before','after','screenshotSHA256'}and observed['scope']==scope and observed['before']==observed['after'],'Restriction before/after snapshot absent or changed')
   q.verify_restriction(observed['before'],qb['browserExpected']['restriction'],width,scope)
   require(observed['screenshotSHA256']==sha(q.safe_file(folder,name).read_bytes()),'Restriction screenshot binding changed')
  else:require('restrictionSnapshot'not in cap,'Unexpected restriction screenshot scope')
  if name in sticky_names():
   h=cap.get('stickyHeader');require(type(h)is dict and set(h)=={'path','sha256','before','after','geometryAfter'},'Sticky header capture absent')
   require(h['path']=='sticky-headers/'+name and h['geometryAfter']==before,'Sticky clip path or scroll changed')
   require(verify_header(h['before'],header_expected)==verify_header(h['after'],header_expected),'Sticky header changed while capturing')
   raw=q.safe_file(folder,h['path']).read_bytes();require(sha(raw)==h['sha256'],'Sticky header PNG bytes mismatch');hi,hp=paint.decoded_pixels(raw)
   require(hi['width']==1280 and hi['height']==71,'Sticky header PNG dimensions changed');headers[name]=(hi,hp)
  else:require(cap.get('stickyHeader')is None,'Unexpected sticky exclusion')
 require(set(headers)==sticky_names(),'Exact eight desktop sticky references required')
 require({p.relative_to(folder).as_posix()for p in folder.rglob('*')if p.is_file()}==set(expected_names)|{'sticky-headers/'+n for n in sticky_names()}|{'browser-report.json','private-capture.json'},'Exact browser42 PNG/two-report inventory changed')
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
 facts={'sourceRevision':b['sourceRevision'],'privateMetadataStatesVerified':6,'privateHTTPFilesVerified':11,'stableCapturesVerified':34,'stickyHeaderReferencesVerified':8,'totalPNGFilesVerified':42,'restrictionViewportSnapshotsVerified':6,'homeViewportFullPixelComparisons':pixel_results,'independentScreenshotReview':'PENDING','publicHTTPVerified':False,'publicationReady':False}
 if allow_unit_fixture:result['syntheticChecks'].update(q.fixture_facts(facts))
 else:result.update(facts)
 return result



def seal(evidence,b):
 evidence=Path(evidence);evidence.mkdir(parents=True,exist_ok=True);rows=[]
 for p in sorted(evidence.rglob('*')):
  require(not p.is_symlink(),'Evidence symlink forbidden')
  if p.is_file()and p.name!='artifact-manifest.json':rows.append({'path':p.relative_to(evidence).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())})
 save(evidence/'artifact-manifest.json',{'sourceRevision':b['sourceRevision'],'files':rows,'independentReview':'PENDING','publicHTTPVerified':False,'publicationReady':False});return {'files':len(rows)}

def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['select','prebuild','postbuild','browser','seal']);p.add_argument('--checkout');p.add_argument('--report');p.add_argument('--evidence');a=p.parse_args();b=binding()
 if a.mode=='select':
  event=read(os.environ['GITHUB_EVENT_PATH']);r=owner(os.environ,event);control_identity(os.environ);r.update({'sourceRevision':b['sourceRevision'],'sourceBranch':BRANCH,'sourceManifestSHA256':SOURCE_MANIFEST_SHA})
  with open(os.environ['GITHUB_OUTPUT'],'a')as f:f.write('source_sha='+b['sourceRevision']+'\n')
 elif a.mode=='seal':r=seal(a.evidence,b)
 elif a.mode in ['prebuild','postbuild']:
  r=check_files(a.checkout,b,postbuild=a.mode=='postbuild')
  if a.mode=='postbuild':r.update(check_dist(Path(a.checkout)/PREFIX/'candidate/dist',b))
  r.update(sourceRevision=b['sourceRevision'],publicationReady=False)
 else:r=verify_browser(a.checkout,Path(a.checkout)/PREFIX/'candidate/dist',b)
 if a.report:save(a.report,r)
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
