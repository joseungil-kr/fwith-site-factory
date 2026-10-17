"""Read-only Hwasun source51 production15 and retained private47/11 evidence.

No provider or IndexNow client, key generation, credential access or Git writes.
"""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,math,os,re,subprocess,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
BINDING_SHA='c1e89ecd1676f65ebdeed79b3aa25dd5bca56f267468ad6ebdfd2de76d94ddc5'
SOURCE_REVISION='17703e6e4c8a82f3271088a76b8cf7d76bf1ff08'
TITLE='[HWASUN-PRODUCTION-BUILD] source51-20261017'
REPO='joseungil-kr/fwith-site-factory';OWNER='joseungil-kr'
PREFIX='site-factory/hwasun-flower';BRANCH='source/hwasun-private-qa-20261016'
SOURCE_MANIFEST_SHA='0e2ec9c9a9dc6ed5e477f9bf67b347943b6fe4800ffcf13787288389c9e86580'
SOURCE_ZIP_SHA='2b5e5490a2dc9e908fa97845414eb87ce3d6eb05034cae2c468853d289ae7d40'
STATIC_REVIEW_MANIFEST_SHA='2202d69b24931f7117e81bfd183582cffa92f894c90cf39fcfd210cf5f377340'
STICKY_SECTIONS=('hospital','products','ribbon','appearance','timing','location','faq','sources')
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
 require(b.get('schema')=='hwasun-private-source47-actions-qa/v1'and b.get('repository')==REPO and b.get('owner')==OWNER and b.get('sourceBranch')==BRANCH and b.get('sourcePrefix')==PREFIX,'Fixed source identity changed')
 require(b.get('sourceManifestSHA256')==SOURCE_MANIFEST_SHA and sha(b.get('sourceManifestUTF8','').encode())==SOURCE_MANIFEST_SHA and b.get('sourceZIP_SHA256')==SOURCE_ZIP_SHA,'Frozen source identity changed')
 m=json.loads(b['sourceManifestUTF8']);original=m['files'];rows=b.get('files',[])
 require(b.get('sourceFiles')==47 and len(original)==len(rows)==len({r['path']for r in rows})==47,'Exact source47 required')
 for row,origin in zip(rows,original):
  require({k:row[k]for k in ['path','bytes','sha256']}==origin and re.fullmatch('[0-9a-f]{40}',row.get('gitBlobSHA','')),'Frozen source row changed')
 require(b.get('permissions')=={'contents':'read'} and all(b.get(k)is False for k in ['providerWrites','productionEnabled','indexNowEnabled','newCredentials','remoteGitWrites','publicationReady']),'Read-only private boundary changed')
 require(b.get('facilityPages')=='HOLD'and b.get('facilityPageCount')==4 and b.get('copyCharacters')==2963 and 'shippingKRW'in b and b['shippingKRW']is None,'Accepted content boundary changed')
 ref=b.get('staticReview',{});require(ref.get('manifestSHA256')==STATIC_REVIEW_MANIFEST_SHA and sha(ref.get('rawUTF8','').encode())==ref.get('sha256'),'Static review evidence changed')
 review=json.loads(ref['rawUTF8']);require(review.get('verdict')=='ACCEPTED_LOCAL_STATIC_IMPLEMENTATION_ONLY'and review.get('mustFix')==[] and review.get('sourceEdited')is False and review.get('sourceFiles')==47 and review.get('outputFiles')==11 and review.get('allOutputBytesEqualToAuthor')is True and review.get('sourceManifestSHA256')==SOURCE_MANIFEST_SHA and review.get('sourceArchiveSHA256')==SOURCE_ZIP_SHA and review.get('publicationReady')is False and review.get('browserExecuted')is False and review.get('bodyCharacters')==2963 and review.get('facilityPagesHeld')==4,'Independent static acceptance absent')
 fixture=b.get('browserExpected');require(sha(json.dumps(fixture,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())==b.get('browserExpectedSHA256'),'Expected browser observations changed')
 require(fixture['widths']==[320,390,1280]and fixture['viewportHeight']==844 and len(fixture['occurrences']['/'])==86 and len(fixture['occurrences']['/404.html'])==14 and len(fixture['images'])==7,'Browser fixture scope changed')
 output=b.get('expectedDistFiles',{});require(sha(json.dumps(output,sort_keys=True,separators=(',',':')).encode())==b.get('expectedDistFilesSHA256')and len(output)==11 and {'index.html','404.html','robots.txt'}<=set(output)and len([x for x in output if x.endswith('.html')])==2,'Exact private output11 map changed')
 require(all(re.fullmatch('[0-9a-f]{64}',x)for x in output.values()),'Invalid output digest')
 if require_bound:
  require(b.get('phase')=='BOUND_REMOTE_SOURCE47'and re.fullmatch('[0-9a-f]{40}',SOURCE_REVISION or'')and b.get('sourceRevision')==SOURCE_REVISION,'Source commit not bound; preparation is not executable')
  ref=b.get('remoteSaveVerification');require(type(ref)is dict and sha(ref.get('rawUTF8','').encode())==ref.get('sha256'),'Remote source save verification missing or changed')
  receipt=json.loads(ref['rawUTF8']);require(receipt.get('commit')==SOURCE_REVISION and receipt.get('branch')==BRANCH and receipt.get('sourceManifestSHA256')==SOURCE_MANIFEST_SHA and receipt.get('sourceFiles')==47 and receipt.get('source47UnchangedAfterBuild')is True and receipt.get('acceptedOutput11DirectByteParity')is True and receipt.get('downloadedOnlySourceBuild')is True and receipt.get('mainWrites')==0 and receipt.get('providerWrites')==0 and receipt.get('publicationReady')is False,'Remote source47 readback scope changed')
  back=b.get('remoteSourceReadback',{});require(sha(back.get('rawUTF8','').encode())==back.get('sha256')==receipt.get('readbackManifestSHA256'),'Remote byte readback manifest changed')
  readback=json.loads(back['rawUTF8']);require(readback.get('commit')==SOURCE_REVISION and readback.get('branch')==BRANCH and readback.get('fileCount')==47 and readback.get('allFilesMatchAcceptedSource')is True,'Remote source47 byte receipt changed')
  remote_rows=readback.get('files',[]);require(len(remote_rows)==47,'Remote source47 byte projection count changed')
  for row,remote in zip(rows,remote_rows):require(all(remote.get(k)==row[k]for k in ['path','bytes','sha256','gitBlobSHA'])and remote.get('remotePath')==PREFIX+'/'+row['path']and remote.get('fetchedSHA256')==row['sha256']and remote.get('fetchedGitBlobSHA')==row['gitBlobSHA'],'Remote source47 byte projection changed')
  independent=b.get('independentRemoteSourceReview',{});require(independent.get('sha256')=='1deda674983270d229f3df81fa85559994cbf3274da389a6070b7feff7e1068b'and independent.get('manifestSHA256')=='c8475ea62d29d4c86f343e775c3ddcb778cd482ccebfc85293c5640bdc7586b6'and sha(independent.get('rawUTF8','').encode())==independent.get('sha256'),'Independent remote source acceptance changed')
  accepted=json.loads(independent['rawUTF8']);require(accepted.get('verdict')=='ACCEPTED_SOURCE47_SAVE_AND_READBACK_ONLY'and accepted.get('mustFix')==[] and accepted.get('sourceCommit')==SOURCE_REVISION and accepted.get('sourceBranch')==BRANCH and accepted.get('sourceManifestSHA256')==SOURCE_MANIFEST_SHA and accepted.get('saveManifestSHA256')==b.get('sourceSaveManifestSHA256')=='8bd6e8412a8c1b9308bf7230cdc51542cdca7f3a090d1517e69f7c89500c8dfe'and accepted.get('acceptedStaticManifestSHA256')==STATIC_REVIEW_MANIFEST_SHA and accepted.get('freshReadbackFileCount')==47 and accepted.get('allReadbackBytesSHA256GitBlobMatchAccepted')is True and accepted.get('downloadedOnlyBuildAndTestsVerified')is True and accepted.get('outputCount')==11 and accepted.get('allOutputBytesEqualIndependentAccepted')is True and accepted.get('sourceUnchangedAfterBuild')is True and accepted.get('controlsAccepted')is False and accepted.get('sitePixelsVerified')is False and accepted.get('siteHTTPVerified')is False and accepted.get('publicationReady')is False,'Independent remote acceptance scope changed')
 return m

def binding(require_bound=True):
 raw=safe_file(ROOT,'bindings.json').read_bytes();require(sha(raw)==BINDING_SHA,'Unbound or changed QA binding');b=json.loads(raw);validate_binding(b,require_bound);validate_production_binding(b)
 for name,key in [('capture_production.py','captureSHA256'),('browser_evidence.py','browserEvidenceSHA256')]:require(sha(safe_file(ROOT,name).read_bytes())==b[key],'Reviewed browser control changed')
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
 return {'verifiedSourceFiles':47,'utf8Files':40,'existingBinaryPaths':7,'sourceBytesUnchanged':True}

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
  result=subprocess.run(['git','rev-parse','HEAD'],cwd=checkout,capture_output=True,text=True);require(result.returncode==0 and result.stdout.strip()==b['assemblyRevision'],'Actual checkout HEAD mismatch')
 return check_source_files(checkout/PREFIX,b,postbuild)


def validate_production_binding(b):
 require(b.get('productionSchema')=='hwasun-production51-actions-qa/v1'and b.get('productionSourceBranch')=='source/hwasun-production-preparation-20261017','Fixed production identity changed')
 require(b.get('productionPhase')=='BOUND_REVIEW_AND_REMOTE_SAVE'and re.fullmatch('[0-9a-f]{40}',b.get('assemblyRevision')or'')and b['assemblyRevision']!=SOURCE_REVISION,'Actual reviewed saved source51 required')
 rows=b.get('assemblyFiles',[]);require(b.get('assemblySourceFiles')==51 and len(rows)==len({r['path']for r in rows})==51,'Exact source51 required')
 require(b.get('readOnlyProductionEnabled')is True and b.get('indexNowSubmissionAuthorized')is False,'Production/IndexNow boundary changed')
 refs={}
 for key in ['production4Review','source51SaveVerification','source51Readback']:
  ref=b.get(key);require(type(ref)is dict and sha(ref.get('rawUTF8','').encode())==ref.get('sha256'),'Embedded production review/readback changed');refs[key]=json.loads(ref['rawUTF8'])
 review=refs['production4Review'];saved=refs['source51SaveVerification'];readback=refs['source51Readback']
 require(b['production4Review']['sha256']==b['production4DecisionSHA256']=='8fc039b52c0149db6a3a9885d3b2cff2b6be22941625efc7d47d99dbc4ecf662'and b['production4Review']['manifestSHA256']==b['production4ReviewManifestSHA256']=='754d52dfa6bee84912b8c1623e6997e1bba813d038093115fef17b1b416ba943','Production4 native acceptance pin changed')
 require(review.get('verdict')=='ACCEPTED_EXACT_PRODUCTION4_AND_LOCAL_PRODUCTION15_ONLY'and review.get('mustFix')==[] and review.get('production4ManifestSHA256')==b['production4ManifestSHA256'],'Exact production4 acceptance absent')
 require(saved.get('commit')==b['assemblyRevision']and saved.get('parent')==SOURCE_REVISION and saved.get('branch')==b['productionSourceBranch']and saved.get('sourceFilesVerified')==51 and saved.get('readbackManifestSHA256')==b['source51Readback']['sha256']and saved.get('mainWrites')==0 and saved.get('providerWrites')==0 and saved.get('publicationReady')is False,'Saved source51 boundary changed')
 require(readback.get('files')==rows and readback.get('commit')==b['assemblyRevision'],'Source51 bytes projection changed')
 original={PREFIX+'/'+r['path']:{k:r[k]for k in ['bytes','sha256','gitBlobSHA']}for r in b['files']}
 require({r['path']:{k:r[k]for k in ['bytes','sha256','gitBlobSHA']}for r in rows if r['path'].startswith(PREFIX+'/')}==original,'Private source47 projection changed')
 prod=[r for r in rows if r['path'].startswith('scripts/direct-hwasun/production-release/')]
 require(len(prod)==4 and b.get('production4ManifestUTF8')and sha(b['production4ManifestUTF8'].encode())==b['production4ManifestSHA256'],'Production4 manifest changed')
 require(json.loads(b['production4ManifestUTF8'])['files']==prod,'Exact production4 projection changed')

def check_assembly_files(checkout,b,git_required=True,postbuild=False):
 check_files(checkout,b,git_required,postbuild);checkout=Path(checkout).absolute()
 for row in b['assemblyFiles']:
  raw=safe_file(checkout,row['path']).read_bytes();require(len(raw)==row['bytes']and sha(raw)==row['sha256']and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['gitBlobSHA'],'Source51 file changed: '+row['path'])
 prefix='scripts/direct-hwasun/production-release';parent=checkout/prefix;actual=set()
 for p in parent.rglob('*'):
  require(not p.is_symlink()and(p.is_dir()or p.is_file()),'Nonregular adapter input')
  if p.is_file():actual.add(p.relative_to(checkout).as_posix())
 require(actual=={r['path']for r in b['assemblyFiles']if r['path'].startswith(prefix+'/')},'Unexpected adapter input')
 spec=importlib.util.spec_from_file_location('hwasun_production',parent/'production_adapter.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 source=checkout/PREFIX;module.check_source(source);return module,source,b

def postbuild(checkout,dist,b):
 module,source,qb=check_assembly_files(checkout,b,postbuild=True);check_dist(source/'candidate/dist',b);r=module.validate(source,dist,b['assemblyRevision']);r['assemblyCommitExternallyVerified']=True;r['controlRevision']=os.environ.get('GITHUB_SHA');return r

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
 module,source,qb=check_assembly_files(checkout,b,git_required,postbuild=True);check_dist(source/'candidate/dist',b);module.validate(source,dist,b['assemblyRevision']);import browser_evidence as q
 folder=source/'candidate/evidence/browser';r=q.read(folder/'production-capture.json');q.check_fixture_boundary(r,allow_unit_fixture)
 result=q.verify_browser(source/'candidate',qb,allow_unit_fixture=allow_unit_fixture)
 require(r['privateSourceRevision']==SOURCE_REVISION and r['assemblyRevision']==b['assemblyRevision']and r['origin']=='loopback-only'and r['publicHTTPVerified']is False and r['publicationReady']is False,'Production capture identity/boundary')
 wanted=[(w,route)for w in [320,390,1280]for route in ['/','/404.html']]
 for row,(width,route)in zip(q.records(r.get('metadata'),6,'Private metadata'),wanted):
  require(row=={'width':width,'route':route,'robots':'index,follow'if route=='/'else'noindex,nofollow','canonical':['https://hwasun.fwith.kr/']if route=='/'else[],'source':b['assemblyRevision'],'privateSource':SOURCE_REVISION,'releaseState':'production-candidate','social':[list(x)for x in module.social_values(module.read_contract(),module.verify_inputs(source)[2])]if route=='/'else[]},'Actual production DOM metadata changed')
 notfound=(Path(dist)/'404.html').read_bytes();require(r.get('missingRoute')=={'path':'/.hwasun-private-missing/','status':404,'sha256':sha(notfound),'bytes':len(notfound),'robots':'noindex,nofollow','canonicalCount':0},'Actual missing-route404 response mismatch')
 expected_http={('/'if n=='index.html'else'/'+n):(n,v)for n,v in sorted(inventory(dist).items())}
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
  scope='hospital'if name.endswith('-hospital.png')else'products'if name.endswith('-products.png')else None
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
 facts={'privateSourceRevision':SOURCE_REVISION,'assemblyRevision':b['assemblyRevision'],'productionMetadataStatesVerified':6,'productionHTTPFilesVerified':15,'socialDOMStatesVerified':6,'stableCapturesVerified':34,'stickyHeaderReferencesVerified':8,'totalPNGFilesVerified':42,'restrictionViewportSnapshotsVerified':6,'homeViewportFullPixelComparisons':pixel_results,'independentScreenshotReview':'PENDING','publicHTTPVerified':False,'publicationReady':False}
 if allow_unit_fixture:result['syntheticChecks'].update(q.fixture_facts(facts))
 else:result.update(facts)
 return result



def seal(evidence,b):
 evidence=Path(evidence);evidence.mkdir(parents=True,exist_ok=True);rows=[]
 for p in sorted(evidence.rglob('*')):
  require(not p.is_symlink(),'Evidence symlink forbidden')
  if p.is_file()and p.name!='artifact-manifest.json':rows.append({'path':p.relative_to(evidence).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())})
 save(evidence/'artifact-manifest.json',{'sourceRevision':b['sourceRevision'],'files':rows,'independentReview':'PENDING','publicHTTPVerified':False,'publicationReady':False});return {'files':len(rows)}

def package_release(checkout,dist,b,env,event):
 require(env.get('NATIVE_GATES_PASSED')=='true','Successful native gates required before packaging');selected=owner(env,event);control_identity(env)
 browser=verify_browser(checkout,dist,b);module,source,_=check_assembly_files(checkout,b,postbuild=True);facts=module.validate(source,dist,b['assemblyRevision'])
 dist=Path(dist).absolute();release=dist.parent
 require(dist.name=='dist'and release.name=='release'and not release.is_symlink()and {p.name for p in release.iterdir()}=={'dist'},'Fresh exact release/dist package required')
 for p in [release,*release.parents]:require(not p.is_symlink(),'Release package parent symlink forbidden')
 manifest=module.release_manifest(facts['files'],b['assemblyRevision'],selected['controlRevision'],str(selected['runId']),BINDING_SHA)
 module.validate_release_manifest(manifest,facts['files'],b['assemblyRevision'],selected['controlRevision'],str(selected['runId']),BINDING_SHA)
 raw=module.release_manifest_bytes(manifest);path=release/'release.json';require(not path.exists(),'Existing release manifest forbidden');path.write_bytes(raw);require(path.read_bytes()==raw,'Release manifest write/readback mismatch')
 return {'state':'READONLY_PRODUCTION_PACKAGE_VERIFIED','assemblyRevision':b['assemblyRevision'],'controlRevision':selected['controlRevision'],'runId':selected['runId'],'releaseManifestSHA256':sha(raw),'outputFilesSHA256':sha(json.dumps(facts['files'],sort_keys=True,separators=(',',':')).encode()),'sourceContractSHA256':module.CONTRACT_SHA,'bindingSHA256':BINDING_SHA,'productionDistFiles':15,'releaseManifestKeys':sorted(module.RELEASE_KEYS),'automatedBrowserChecksPassed':browser['automatedBrowserChecksPassed'],'mainScreenshots':34,'stickyHeaderClips':8,'restrictionViewportSnapshotsVerified':6,'actualIndependentScreenshotReview':'PENDING','publicHTTPVerified':False,'publicationReady':False}

def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['select','prebuild','postbuild','browser','package','seal']);p.add_argument('--checkout');p.add_argument('--dist');p.add_argument('--report');p.add_argument('--evidence');a=p.parse_args();b=binding()
 if a.mode=='select':
  event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text());r=owner(os.environ,event);control_identity(os.environ);r.update({'assemblyRevision':b['assemblyRevision'],'sourceBranch':b['productionSourceBranch'],'privateSourceRevision':SOURCE_REVISION})
  with open(os.environ['GITHUB_OUTPUT'],'a')as f:f.write('source_sha='+b['assemblyRevision']+'\n')
 elif a.mode=='seal':r=seal(a.evidence,b)
 elif a.mode=='prebuild':m,s,q=check_assembly_files(a.checkout,b);r={'sourceFilesVerified':51,'privateSourceRevision':SOURCE_REVISION,'assemblyRevision':b['assemblyRevision'],'assemblyCommitExternallyVerified':True,'publicationReady':False}
 elif a.mode=='postbuild':r=postbuild(a.checkout,a.dist,b)
 elif a.mode=='package':r=package_release(a.checkout,a.dist,b,os.environ,json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text()))
 else:r=verify_browser(a.checkout,a.dist,b)
 if a.report:save(a.report,r)
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
