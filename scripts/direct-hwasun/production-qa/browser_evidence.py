"""Actual-success Goheung DOM/PNG evidence validators reused for bound Hwasun fixture.
Source/control identity is enforced by production_qa before these report checks.
"""
from pathlib import Path
import hashlib,json,re,datetime,math,struct,zlib,binascii
sha=lambda b:hashlib.sha256(b).hexdigest()
def fail(message):raise ValueError(message)
def read(path):return json.loads(Path(path).read_text())
def safe_file(root,relative):
 if not relative or relative.startswith('/') or '\\' in relative or '..' in Path(relative).parts:fail('Unsafe source path')
 root=Path(root);current=root
 if root.is_symlink():fail('Symlink root')
 for component in Path(relative).parts:
  current=current/component
  if current.is_symlink():fail('Symlink source')
 if not current.is_file():fail('Missing regular source file: '+relative)
 return current

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

FIXTURE_PURPOSE='SYNTHETIC_UNIT_TEST_NOT_ACTUAL_QA_EVIDENCE'
def check_fixture_boundary(report,allow_unit_fixture=False):
 if type(allow_unit_fixture)is not bool:fail('Explicit boolean test-only fixture argument required')
 if not isinstance(report,dict):fail('Browser report must be an object')
 marked=any(key in report for key in ['unitFixture','fixturePurpose'])
 if allow_unit_fixture:
  if report.get('unitFixture')is not True or report.get('fixturePurpose')!=FIXTURE_PURPOSE:fail('Explicit fixture mode requires canonical synthetic markers in both reports')
 elif marked:fail('Synthetic fixture markers forbidden in actual browser evidence')

def fixture_facts(result):
 excluded={'automatedBrowserChecksPassed','actualBrowserVerified','publicHTTPVerified','publicationReady','independentScreenshotReview'}
 return {key.replace('Verified','Evaluated').replace('localMissingRouteHTTPStatus','simulatedMissingRouteHTTPStatus'):value for key,value in result.items()if key not in excluded}

def fixture_result(result):
 return {'unitFixture':True,'fixturePurpose':FIXTURE_PURPOSE,'unitFixtureValidationPassed':True,'automatedBrowserChecksPassed':False,'actualBrowserVerified':False,'publicHTTPVerified':False,'publicationReady':False,'independentScreenshotReview':'NOT_APPLICABLE_SYNTHETIC_UNIT_FIXTURE','syntheticChecks':fixture_facts(result)}

def verify_browser(candidate,b,*,allow_unit_fixture=False):
 root=Path(candidate);report=read(root/'evidence/browser/browser-report.json');check_fixture_boundary(report,allow_unit_fixture);check_fixture_boundary(read(root/'evidence/browser/production-capture.json'),allow_unit_fixture);fixture=b['browserExpected'];widths=fixture['widths'];height=fixture['viewportHeight'];normalize=lambda value:re.sub(r'\s+',' ',value).strip()
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
  if state.get('links')!=fixture['allLinks'][route]:fail('Exact complete link href/text/aria inventory changed')
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
 for row,(width,key) in zip(records(report.get('scrollReachability'),len(reach_wanted),'Scroll reachability'),reach_wanted):
  if row.get('width')!=width or row.get('key')!=key:fail('Reachability viewport/key changed')
  r=rectangle(row.get('rect'),'Reachability')
  if r['x']< -1 or r['x']+r['width']>width+1 or r['y']>=height or r['y']+r['height']<=0:fail('Observed occurrence not viewport reachable')
 interactions=[]
 for width in widths:
  interactions.extend({'width':width,'route':route,'test':'keyboard skip focuses main','pass':True}for route in ['/','/404.html'])
  interactions.extend({'width':width,'test':'anchor/back/forward','href':href,'pass':True}for href in fixture['navigationHrefs'])
  interactions.extend([{'width':width,'test':'404 navigation home anchor','pass':True},{'width':width,'test':'404 recovery CTA','pass':True}])
 if records(report.get('interactions'),24,'Interactions')!=interactions:fail('Exact passing interactions missing')
 for row,(width,entry) in zip(records(report.get('touchTargets'),len(widths)*len(fixture['touchLinks']),'Touch targets'),[(w,e)for w in widths for e in fixture['touchLinks']]):
  if row.get('width')!=width or any(row.get(k)!=entry[k]for k in ['text','href','ariaLabel']) or positive_number(row.get('height'),'Touch height')<44 or positive_number(row.get('widthPx'),'Touch width')<44:fail('Touch label/viewport/44px target changed')
 if report.get('localMissingRouteStatus')!=404 or report.get('externalRequestsBlocked')!=[] or report.get('pageErrors')!=[] or report.get('externalCTAAndPhoneActivated') is not False or report.get('publicHTTPVerified') is not False or report.get('independentImplementationReview') is not False:fail('Browser execution boundary failed')
 if report.get('computedVisibilityMutationDetected') is not True:fail('Visibility negative test missing')
 mutations=[{'selector':selector,'rule':rule,'detected':True}for selector in ['#hospital-restriction','.product-eligibility']for rule in ['display:none','visibility:hidden','opacity:0']]
 if report.get('restrictionVisibilityMutations')!=mutations:fail('Hospital restriction computed visibility mutation evidence missing')
 responses=report.get('responses')
 if not isinstance(responses,list) or not responses:fail('Loopback HTTP observations missing')
 seen=set()
 for row in responses:
  if not isinstance(row,dict) or not isinstance(row.get('path'),str) or not row['path'].startswith('/') or row['path'].startswith('//'):fail('Non-loopback HTTP path')
  if row.get('status')!=200 and not(row.get('status')==404 and row['path']in ['/.hwasun-private-missing/','/favicon.ico']):fail('Unexpected loopback HTTP status')
  seen.add((row['path'],row['status']))
 required={('/',200),('/404.html',200),('/.hwasun-private-missing/',404)}|{(entry['src'],200)for entry in fixture['images']}|{('/'+name,200)for name in b['expectedDistFiles']if name.endswith('.css')}
 if not required<=seen:fail('Required actual route/image/CSS responses absent')
 screenshots=records(report.get('screenshots'),34,'Screenshots');wanted=screenshot_expectations(fixture)
 if {row.get('path')for row in screenshots}!=set(wanted):fail('Exact viewport screenshot filenames missing')
 decoded=[]
 for row in screenshots:
  path=row['path'];data=safe_file(root/'evidence/browser',path).read_bytes()
  if sha(data)!=row.get('sha256'):fail('Screenshot bytes mismatch')
  png=decode_png(data);width,expected_height=wanted[path]
  if png['width']!=width or (expected_height is not None and png['height']!=expected_height) or (expected_height is None and png['height']<height):fail('Screenshot viewport dimensions changed')
  decoded.append({'path':path,**png})
 result={'automatedBrowserChecksPassed':True,'screenshots':34,'decodedScreenshots':decoded,'widths':widths,'localMissingRouteHTTPStatus':404,'independentScreenshotReview':'PENDING','publicHTTPVerified':False,'publicationReady':False}
 return fixture_result(result)if allow_unit_fixture else result

def decoded_pixels(data):
 """Reuse accepted PNG validation; reconstruct its already-validated RGB(A) rows for crop comparison."""
 info=decode_png(data);width,height,channels=info['width'],info['height'],info['channels'];pos=8;parts=[]
 while pos<len(data):
  size=struct.unpack('>I',data[pos:pos+4])[0];kind=data[pos+4:pos+8]
  if kind==b'IDAT':parts.append(data[pos+8:pos+8+size])
  pos+=12+size
 raw=zlib.decompress(b''.join(parts));stride=width*channels;previous=bytearray(stride);rows=[]
 for y in range(height):
  start=y*(stride+1);filter_type=raw[start];row=bytearray(raw[start+1:start+1+stride])
  if filter_type:
   for x in range(stride):
    left=row[x-channels]if x>=channels else 0;up=previous[x];ul=previous[x-channels]if x>=channels else 0
    if filter_type==1:predictor=left
    elif filter_type==2:predictor=up
    elif filter_type==3:predictor=(left+up)//2
    else:
     estimate=left+up-ul;distances=[abs(estimate-left),abs(estimate-up),abs(estimate-ul)];predictor=[left,up,ul][distances.index(min(distances))]
    row[x]=(row[x]+predictor)&255
  rows.append(bytes(row));previous=row
 pixels=b''.join(rows)
 if sha(pixels)!=info['decodedPixelsSHA256']:fail('Pixel reconstruction differs from accepted decoder')
 return info,pixels



def verify_restriction(row,expected,width,scope):
 """Exact accepted hospital-only wording plus observed DOM/style/viewport contract.
 This checks recorded evidence; actual screenshot provenance and visual review remain required.
 """
 if type(row)is not dict or scope not in ['hospital','products']:fail('Restriction snapshot schema/scope')
 if row.get('heroBeforeActions')is not True or row.get('productAdjacent')is not True:fail('Hospital hero/anchor DOM adjacency changed')
 if row.get('heroActions')!=expected['heroActions'] or (type(row.get('selectedHospitalElements'))is not int or row['selectedHospitalElements']!=0):fail('Hospital-specific product recommendation or hero actions changed')
 wanted=[]
 for p in expected['products']:wanted.append({**p,'ctaHref':p['href'],'ctaLabel':p['label'],'sumElements':0})
 if row.get('products')!=wanted:fail('Product photo/CTA or nullable shipping/total boundary changed')
 exact={'heroText':expected['heroText'],'heroSource':expected['heroSourceLabel'],'productHeading':expected['productHeading'],'productNotice':expected['productText']}
 for key in ['hero','heroText','heroSource','productHeading','productNotice','productCards']:
  n=row.get(key)
  if type(n)is not dict or n.get('available')is not True:fail('Restriction computed visibility absent')
  r=rectangle(n.get('rect'),'Restriction '+key)
  if type(n.get('ancestors'))is not list:fail('Restriction ancestors absent')
  ancestors=records(n['ancestors'],len(n['ancestors']),'Restriction ancestors')
  if not ancestors or len(ancestors)>64:fail('Restriction ancestor evidence absent')
  for a in ancestors:
   if set(a)!={'display','visibility','opacity','hidden','inert','ariaHidden'} or type(a['hidden'])is not bool or type(a['inert'])is not bool:fail('Restriction ancestor schema changed')
   try:opacity=float(a['opacity'])
   except (TypeError,ValueError):fail('Restriction ancestor opacity invalid')
   if not math.isfinite(opacity)or opacity<=0 or opacity>1 or a['display']=='none'or a['visibility']in ['hidden','collapse']or a['hidden']or a['inert']or a['ariaHidden']=='true':fail('Restriction ancestor hides notice')
  if key in exact and n.get('text')!=exact[key]:fail('Exact hospital-only notice/heading changed')
  tag={'hero':'div','heroText':'p','heroSource':'a','productHeading':'h2','productNotice':'p','productCards':'div'}[key]
  if n.get('tag')!=tag or n.get('href')!=(expected['heroSourceHref']if key=='heroSource'else None):fail('Restriction node tag/href changed')
  if r['x'] < -1 or r['x']+r['width']>width+1:fail('Restriction horizontal overflow')
 # The complete selected notice must fit; a clipped or taller-than-viewport note
 # must fail and require a separately reviewed capture contract, never claim full visibility.
 keys=['hero','heroText','heroSource']if scope=='hospital'else['productHeading','productNotice']
 floor=71 if width==1280 else 0
 for key in keys:
  r=row[key]['rect']
  if r['y']<floor-1 or r['y']+r['height']>845:fail('Complete restriction notice not inside unobscured viewport')
 if scope=='hospital'and row.get('fragment')!='':fail('Hospital capture route changed')
 if scope=='products'and row.get('fragment')!='#products-cost':fail('Direct product anchor evidence missing')
 if row['productHeading']['rect']['y']+row['productHeading']['rect']['height']>row['productNotice']['rect']['y']+1 or row['productNotice']['rect']['y']+row['productNotice']['rect']['height']>row['productCards']['rect']['y']+1:fail('Product heading/notice/cards visual ordering changed')
 return {'scope':scope,'completeNoticeInViewport':True,'hospitalOnlyExactCopy':True,'productCards':4}
