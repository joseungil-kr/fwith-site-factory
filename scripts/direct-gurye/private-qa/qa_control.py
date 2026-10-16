"""Prepared read-only Gurye Actions QA control. No provider, Git writes, network client or key creation."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,datetime,math,struct,zlib,binascii
REPOSITORY='joseungil-kr/fwith-site-factory';OWNER='joseungil-kr';PREFIX='site-factory/gurye-flower';BRANCH='source/gurye-private-qa-20261016';ISSUE='[GURYE-PRIVATE-QA] source51-20261016'
BROWSER_EXPECTED_SHA='3407a7a0a7518364b51ee73033500a6be70ccfbbebc517916e24f94273df7f5a'
SOURCE_REVISION='557324cfdea14a5dec3354f2124cc887e2ff7555'
SOURCE_SAVE_RESULT_SHA='5a04b10d7755fb72bad51f80d96c66ef3ec7fc9bb62f2ca22fbb176baa641ccb'
SOURCE_MANIFEST_SHA='efcdd0a44ccb7ffb96243a7a0b696130239161c13dc5908d6abf4a9e3cca57ed'
SOURCE_ZIP_SHA='41a83c231838e86e877c7263552ce6714dc67b9ddb1e75ed4cd55c87d0370465'
EXPECTED_DIST_MAP_SHA='75fa655fd0ca635faa09835c0e9081f28eb50fd6c7925a7a46b7ec1a5b6985cd'
IMPLEMENTATION_REVIEW_SHA='d91aefa3aabbbf23ab66aff25e0205c04e80fa5beb0d6c22894af2b1de49abdb'
sha=lambda b:hashlib.sha256(b).hexdigest()
def fail(message):raise ValueError(message)
def read(path):return json.loads(Path(path).read_text())
def save(path,data):p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def validate_binding(b,require_bound=True):
 if b.get('schema')!='gurye-private-source51-actions-qa/v1' or b.get('repository')!=REPOSITORY or b.get('owner')!=OWNER or b.get('sourceBranch')!=BRANCH or b.get('sourcePrefix')!=PREFIX or b.get('issueTitle')!=ISSUE:fail('Fixed repository/source/owner/issue identity changed')
 if b.get('sourceManifestSHA256')!=SOURCE_MANIFEST_SHA or sha(b.get('sourceManifestUTF8','').encode())!=SOURCE_MANIFEST_SHA or b.get('sourceZIP_SHA256')!=SOURCE_ZIP_SHA:fail('Frozen source51 identity changed')
 m=json.loads(b['sourceManifestUTF8']);rows=m['files']
 if len(rows)!=51 or len({r['path'] for r in rows})!=51 or sum(r['storageMode']=='UTF8_CONTENT' for r in rows)!=44 or sum(r['storageMode']=='EXISTING_BINARY_BLOB' for r in rows)!=7:fail('Source51 denominator changed')
 if b.get('permissions')!={'contents':'read'} or any(b.get(k) is not False for k in ['providerWrites','productionEnabled','newCredentials','IndexNowEnabled','remoteGitWrites']):fail('Read-only private QA boundary changed')
 if b.get('historicalImplementationReviewSHA256')!=IMPLEMENTATION_REVIEW_SHA:fail('Historical independent implementation review changed')
 browser_expected=b.get('browserExpected')
 if b.get('browserExpectedSHA256')!=BROWSER_EXPECTED_SHA or sha(json.dumps(browser_expected,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())!=BROWSER_EXPECTED_SHA:fail('Browser expected observations changed')
 expected=b.get('expectedDistFiles',{})
 if sha(json.dumps(expected,sort_keys=True,separators=(',',':')).encode())!=EXPECTED_DIST_MAP_SHA:fail('Accepted output map changed')
 if len(expected)!=11 or len([x for x in expected if x.endswith('.html')])!=2 or not {'index.html','404.html','robots.txt'}<=set(expected):fail('Expected private output changed')
 if any(not re.fullmatch(r'[0-9a-f]{64}',v) for v in expected.values()):fail('Invalid expected output SHA')
 if require_bound:
  if b.get('phase')!='BOUND_SOURCE_AND_PROJECTION_REVIEW' or b.get('sourceRevision')!=SOURCE_REVISION:fail('Source commit not bound; preparation is not executable')
  saved=b.get('remoteSaveVerification')
  if not isinstance(saved,dict) or saved.get('resultSHA256')!=SOURCE_SAVE_RESULT_SHA or sha(saved.get('resultUTF8','').encode())!=SOURCE_SAVE_RESULT_SHA or saved.get('manifestSHA256')!='d8802216c4db511e60def875764926de1e408cfe5be25e5fbfe98167c412351c':fail('Remote source save verification changed')
  v=json.loads(saved['resultUTF8'])
  if v.get('commit')!=SOURCE_REVISION or v.get('sourceManifestSHA256')!=SOURCE_MANIFEST_SHA or v.get('remoteFilesByteVerified')!=51 or v.get('source51UnchangedAfterBuild') is not True or v.get('acceptedOutput11ByteParity') is not True or v.get('publicationReady') is not False:fail('Remote source save scope changed')
  review=b.get('independentProjectionReview')
  if not isinstance(review,dict) or review.get('accepted') is not True or review.get('resultSHA256')!='5e14c6abcedd9e0ae26b45a0c2f7d35b040d3c042187f2c0b6312d07999520e4' or sha(review.get('resultUTF8','').encode())!=review['resultSHA256'] or review.get('manifestSHA256')!='ba5fe39893ad66da6075d90474363928388e53331b592c384c3b8c8850d6bfb2':fail('Independent source projection review not bound')
  r=json.loads(review['resultUTF8'])
  if r.get('verdict')!='ACCEPT_SOURCE51_R2_STATIC_PROJECTION_ONLY__VISUAL_HTTP_AND_REMOTE_UNVERIFIED' or r.get('sourceManifestSHA256')!=SOURCE_MANIFEST_SHA or r.get('sourceZipSHA256')!=SOURCE_ZIP_SHA or r.get('sourceFilesVerified')!=51 or r.get('publicationReady') is not False or r.get('remoteReadbackVerified') is not False or r.get('screenshots')!=0:fail('Independent review scope changed')
 return m

def validate_owner_event(env,event):
 for key,value in {'GITHUB_REPOSITORY':REPOSITORY,'GITHUB_ACTOR':OWNER,'GITHUB_TRIGGERING_ACTOR':OWNER,'GITHUB_REF':'refs/heads/main','GITHUB_EVENT_NAME':'issues','GITHUB_RUN_ATTEMPT':'1'}.items():
  if env.get(key)!=value:fail('Owner/event boundary: '+key)
 issue=event.get('issue',{})
 if event.get('action')!='opened' or issue.get('title')!=ISSUE or issue.get('user',{}).get('login')!=OWNER or issue.get('user',{}).get('type')!='User':fail('Exact owner issue required')

def safe_file(root,relative):
 if not relative or relative.startswith('/') or '\\' in relative or '..' in Path(relative).parts:fail('Unsafe source path')
 root=Path(root);current=root
 if root.is_symlink():fail('Symlink root')
 for component in Path(relative).parts:
  current=current/component
  if current.is_symlink():fail('Symlink source')
 if not current.is_file():fail('Missing regular source file: '+relative)
 return current

def check_source_files(root,b,postbuild=False):
 m=validate_binding(b,require_bound=False);root=Path(root);expected={r['path']:r for r in m['files']};actual=[]
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
  if row['storageMode']=='UTF8_CONTENT':data.decode('utf8')
 return {'verifiedSourceFiles':51,'utf8Files':44,'existingBinaryPaths':7,'historicalOriginal132Reverified':False,'sourceBytesUnchanged':True}

def check_dist(dist,b):
 dist=Path(dist);actual={}
 for p in dist.rglob('*'):
  if p.is_symlink():fail('Symlink output')
  if p.is_file():actual[p.relative_to(dist).as_posix()]=sha(p.read_bytes())
 if actual!=b['expectedDistFiles']:fail('Private output differs from independently accepted exact bytes')
 return {'distFiles':11,'exactAcceptedPrivateOutputParity':True,'canonical':None,'sitemap':False,'robots':'noindex,nofollow','actualBrowserVerified':False}

def positive_number(value, label):
 if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:fail(label+' must be a positive finite number')
 return value

def rectangle(value, label):
 if not isinstance(value,dict) or set(value)!={'x','y','width','height'}:fail(label+' rectangle missing')
 for key in ['x','y']:
  if isinstance(value[key],bool) or not isinstance(value[key],(int,float)) or not math.isfinite(value[key]):fail(label+' coordinate invalid')
 positive_number(value['width'],label+' width');positive_number(value['height'],label+' height')
 return value

def records(value,count,label):
 if not isinstance(value,list) or len(value)!=count or any(not isinstance(row,dict) for row in value):fail(label+' exact records missing')
 return value

def decode_png(data):
 """Decode actual non-interlaced 8-bit RGB/RGBA PNG scanlines using only stdlib.
 Browser screenshots use this supported form. No Pillow or local-only package is required.
 """
 if not data.startswith(b'\x89PNG\r\n\x1a\n'):fail('PNG signature missing')
 pos=8;header=None;compressed=[];ended=False;idat_closed=False;seen_idat=False
 while pos<len(data):
  if pos+12>len(data):fail('Truncated PNG chunk')
  length=struct.unpack('>I',data[pos:pos+4])[0];kind=data[pos+4:pos+8];end=pos+12+length
  if length>64*1024*1024 or end>len(data):fail('Invalid PNG chunk size')
  payload=data[pos+8:pos+8+length];crc=struct.unpack('>I',data[pos+8+length:end])[0]
  if binascii.crc32(kind+payload)&0xffffffff!=crc:fail('PNG CRC mismatch')
  if header is None and kind!=b'IHDR':fail('PNG IHDR must be first')
  if kind==b'IHDR':
   if header is not None or length!=13:fail('Invalid or duplicate PNG IHDR')
   width,height,depth,color,compression,filter_method,interlace=struct.unpack('>IIBBBBB',payload)
   if width<1 or height<1 or width>1280 or height>50000 or width*height>64000000:fail('PNG dimensions outside bounded screenshot range')
   if depth!=8 or color not in [2,6] or compression!=0 or filter_method!=0 or interlace!=0:fail('Unsupported browser screenshot PNG encoding')
   header=(width,height,3 if color==2 else 4)
  elif kind==b'IDAT':
   if idat_closed:fail('Non-contiguous PNG IDAT')
   compressed.append(payload);seen_idat=True
  elif kind==b'IEND':
   if length or not seen_idat or end!=len(data):fail('Invalid PNG IEND or trailing bytes')
   ended=True;pos=end;break
  elif kind[:1].isupper():fail('Unsupported critical PNG chunk')
  if seen_idat and kind!=b'IDAT':idat_closed=True
  pos=end
 if not ended or header is None:fail('Incomplete PNG')
 width,height,channels=header;stride=width*channels;expected=height*(stride+1)
 inflater=zlib.decompressobj()
 try:raw=inflater.decompress(b''.join(compressed),expected+1)
 except zlib.error:fail('PNG compressed stream invalid')
 if len(raw)!=expected or not inflater.eof or inflater.unused_data or inflater.unconsumed_tail:fail('PNG decompressed scanline size or stream boundary invalid')
 previous=bytearray(stride);decoded=hashlib.sha256()
 for y in range(height):
  start=y*(stride+1);filter_type=raw[start];row=bytearray(raw[start+1:start+1+stride])
  if filter_type not in [0,1,2,3,4]:fail('Invalid PNG scanline filter')
  if filter_type==0:
   decoded.update(row);previous=row;continue
  for x in range(stride):
   left=row[x-channels]if x>=channels else 0;up=previous[x];upper_left=previous[x-channels]if x>=channels else 0
   if filter_type==1:predictor=left
   elif filter_type==2:predictor=up
   elif filter_type==3:predictor=(left+up)//2
   elif filter_type==4:
    estimate=left+up-upper_left;dl=abs(estimate-left);du=abs(estimate-up);dul=abs(estimate-upper_left);predictor=left if dl<=du and dl<=dul else up if du<=dul else upper_left
   else:predictor=0
   row[x]=(row[x]+predictor)&255
  decoded.update(row);previous=row
 return {'width':width,'height':height,'channels':channels,'decodedPixelsSHA256':decoded.hexdigest()}

def screenshot_expectations(fixture):
 result={}
 for width in fixture['widths']:
  for route in ['home','404']:result[f'{route}-{width}-top.png']=(width,fixture['viewportHeight'])
  for section in fixture['screenshotSections']:result[f'home-{width}-{section}.png']=(width,fixture['viewportHeight'])
  result[f'home-{width}-full.png']=(width,None)
 result['missing-route-404.png']=(fixture['widths'][-1],fixture['viewportHeight'])
 return result

def verify_browser(candidate,b):
 validate_binding(b);root=Path(candidate);report=read(root/'evidence/browser/browser-report.json');fixture=b['browserExpected'];widths=fixture['widths'];height=fixture['viewportHeight'];normalize=lambda value:re.sub(r'\s+',' ',value).strip()
 check_source_files(root.parent,b,postbuild=True);check_dist(root/'dist',b)
 if report.get('status')!='PASS_AUTHOR_LOCAL_CHROMIUM_CHECKS' or report.get('widths')!=widths or report.get('pages')!=2 or report.get('origin')!='loopback-only':fail('Browser coverage missing')
 if not isinstance(report.get('browserVersion'),str) or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)+',report['browserVersion']):fail('Browser version missing')
 try:observed_at=datetime.datetime.fromisoformat(report.get('checkedAtUTC',''))
 except (ValueError,TypeError):fail('Browser observation time missing')
 if observed_at.tzinfo is None:fail('Browser observation time has no timezone')
 expected_states=[(w,route)for w in widths for route in ['/','/404.html']]
 states=records(report.get('states'),6,'Browser states')
 for state,(width,route) in zip(states,expected_states):
  if state.get('width')!=width or state.get('route')!=route or state.get('failures')!=[] or state.get('bodyExact') is not True:fail('Exact width/route or body state changed')
  if positive_number(state.get('scrollWidth'),'Scroll width')>width or positive_number(state.get('clientWidth'),'Client width')>width:fail('Browser horizontal overflow')
  wanted=fixture['occurrences'][route];observations=records(state.get('observations'),len(wanted),'Exact visible occurrence observations')
  for row,entry in zip(observations,wanted):
   if row.get('key')!=entry['key'] or not isinstance(row.get('text'),str) or normalize(row['text'])!=normalize(entry['text']) or row.get('tag')!=entry['tag'] or row.get('href')!=entry.get('href') or row.get('available') is not True:fail('Observed key/text/tag/href/visibility differs from accepted copy')
   rectangle(row.get('rect'),'Occurrence')
 images=records(report.get('imageAspectChecks'),21,'Image aspect')
 for row,(width,entry) in zip(images,[(w,e)for w in widths for e in fixture['images']]):
  if row.get('width')!=width or any(row.get(k)!=entry[k]for k in ['src','naturalWidth','naturalHeight']) or row.get('objectFit')!='contain':fail('Image identity/dimensions/contain changed')
  dw=positive_number(row.get('displayWidth'),'Image display width');dh=positive_number(row.get('displayHeight'),'Image display height')
  if dw>width+1 or abs(dw/dh-entry['naturalWidth']/entry['naturalHeight'])>=.01:fail('Image display ratio or viewport changed')
 reach_wanted=[(w,e['key'])for w in widths for e in fixture['occurrences']['/']if e['key']!='ui.skipLabel']
 for row,(width,key) in zip(records(report.get('scrollReachability'),261,'Scroll reachability'),reach_wanted):
  if row.get('width')!=width or row.get('key')!=key:fail('Reachability viewport/key changed')
  r=rectangle(row.get('rect'),'Reachability')
  if r['x']< -1 or r['x']+r['width']>width+1 or r['y']>=height or r['y']+r['height']<=0:fail('Observed occurrence not viewport reachable')
 interactions=[]
 for width in widths:
  interactions.extend({'width':width,'route':route,'test':'keyboard skip focuses main','pass':True}for route in ['/','/404.html'])
  interactions.extend({'width':width,'test':'anchor/back/forward','href':href,'pass':True}for href in fixture['navigationHrefs'])
  interactions.extend([{'width':width,'test':'404 navigation home anchor','pass':True},{'width':width,'test':'404 recovery CTA','pass':True}])
 if records(report.get('interactions'),24,'Interactions')!=interactions:fail('Exact passing interactions missing')
 for row,(width,label) in zip(records(report.get('touchTargets'),66,'Touch targets'),[(w,label)for w in widths for label in fixture['touchLabels']]):
  if row.get('width')!=width or row.get('text')!=label or positive_number(row.get('height'),'Touch height')<44 or positive_number(row.get('widthPx'),'Touch width')<44:fail('Touch label/viewport/44px target changed')
 if report.get('localMissingRouteStatus')!=404 or report.get('externalRequestsBlocked')!=[] or report.get('pageErrors')!=[] or report.get('externalCTAAndPhoneActivated') is not False or report.get('publicHTTPVerified') is not False or report.get('independentImplementationReview') is not False:fail('Browser execution boundary failed')
 if report.get('computedVisibilityMutationDetected') is not True:fail('Visibility negative test missing')
 responses=report.get('responses')
 if not isinstance(responses,list) or not responses:fail('Loopback HTTP observations missing')
 seen=set()
 for row in responses:
  if not isinstance(row,dict) or not isinstance(row.get('path'),str) or not row['path'].startswith('/') or row['path'].startswith('//'):fail('Non-loopback HTTP path')
  if row.get('status')!=200 and not(row.get('status')==404 and row['path']in ['/.gurye-private-missing/','/favicon.ico']):fail('Unexpected loopback HTTP status')
  seen.add((row['path'],row['status']))
 required={('/',200),('/404.html',200),('/.gurye-private-missing/',404)}|{(entry['src'],200)for entry in fixture['images']}|{('/'+name,200)for name in b['expectedDistFiles']if name.endswith('.css')}
 if not required<=seen:fail('Required actual route/image/CSS responses absent')
 screenshots=records(report.get('screenshots'),31,'Screenshots');wanted=screenshot_expectations(fixture)
 if {row.get('path')for row in screenshots}!=set(wanted):fail('Exact viewport screenshot filenames missing')
 decoded=[]
 for row in screenshots:
  path=row['path'];data=safe_file(root/'evidence/browser',path).read_bytes()
  if sha(data)!=row.get('sha256'):fail('Screenshot bytes mismatch')
  png=decode_png(data);width,expected_height=wanted[path]
  if png['width']!=width or (expected_height is not None and png['height']!=expected_height) or (expected_height is None and png['height']<height):fail('Screenshot viewport dimensions changed')
  decoded.append({'path':path,**png})
 return {'automatedBrowserChecksPassed':True,'screenshots':31,'decodedScreenshots':decoded,'widths':widths,'localMissingRouteHTTPStatus':404,'independentScreenshotReview':'PENDING','publicHTTPVerified':False,'publicationReady':False}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['select','prebuild','postbuild','browser','seal']);parser.add_argument('--binding',required=True);parser.add_argument('--checkout');parser.add_argument('--report');parser.add_argument('--evidence');args=parser.parse_args();b=read(args.binding)
 if args.mode=='seal':
  root=Path(args.evidence);root.mkdir(parents=True,exist_ok=True);items=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}for p in sorted(root.rglob('*'))if p.is_file() and p.name!='evidence-manifest.json'];save(root/'evidence-manifest.json',{'sourceRevision':b.get('sourceRevision'),'files':items,'independentScreenshotReview':'PENDING','publicationReady':False});return
 validate_binding(b)
 if args.mode=='select':
  validate_owner_event(os.environ,read(os.environ['GITHUB_EVENT_PATH']));save(args.report,{'repository':REPOSITORY,'sourceRevision':b['sourceRevision'],'sourceBranch':BRANCH,'sourcePrefix':PREFIX,'sourceManifestSHA256':SOURCE_MANIFEST_SHA,'providerWrites':False})
  with open(os.environ['GITHUB_OUTPUT'],'a')as f:f.write('source_sha='+b['sourceRevision']+'\n')
  return
 checkout=Path(args.checkout).resolve();head=subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()
 if head!=b['sourceRevision']:fail('Checkout commit differs from pinned source')
 root=checkout/PREFIX
 if args.mode in ['prebuild','postbuild']:
  result=check_source_files(root,b,args.mode=='postbuild')
  if args.mode=='postbuild':result.update(check_dist(root/'candidate/dist',b))
 else:result=verify_browser(root/'candidate',b)
 result.update(sourceRevision=head,sourceManifestSHA256=SOURCE_MANIFEST_SHA);save(args.report,result)
if __name__=='__main__':main()
