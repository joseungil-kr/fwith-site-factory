"""Same-source, read-only 390px ribbon raster recheck. Original run/screenshots stay immutable."""
from pathlib import Path
import argparse,datetime,hashlib,http.server,json,math,socketserver,struct,threading,zlib
from urllib.parse import unquote,urlsplit
import qa_control as q
SOURCE='557324cfdea14a5dec3354f2124cc887e2ff7555'
ORIGINAL_RUN=38902113958
ORIGINAL_ARTIFACT=12046102572
ORIGINAL_ARCHIVE_SHA='8fc7defab8691dbefc701b055ad0439e64493eb0f391b535eeafc2da6bb5bad6'
ORIGINAL_BAD_SHA='40f75070ff4b04f53f39a5562241018d28981b8004bed5209b86ef47f8abc877'
WIDTH=390;HEIGHT=844;SECTION='#ribbon-and-order'
PINNED_CONTROL={'qa_control.py':'04aad69ab531a987e0de1b87981dfde328b5783986f1452706fe4b7add1b2e7e','bindings.json':'34b2e8e415e27937681d280a88e9ff8cc4c2a68001243e0bdd6d9b6d6c1e7039'}

def binding():
 root=Path(__file__).resolve().parent
 for name,want in PINNED_CONTROL.items():
  if q.sha((root/name).read_bytes())!=want:q.fail('Accepted control dependency changed: '+name)
 b=q.read(root/'bindings.json');q.validate_binding(b)
 if b['sourceRevision']!=SOURCE:q.fail('Source revision changed')
 return b

def decoded_pixels(data):
 """Reuse accepted PNG validation; reconstruct its already-validated RGB(A) rows for crop comparison."""
 info=q.decode_png(data);width,height,channels=info['width'],info['height'],info['channels'];pos=8;parts=[]
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
 if q.sha(pixels)!=info['decodedPixelsSHA256']:q.fail('Pixel reconstruction differs from accepted decoder')
 return info,pixels

def compare_viewport_to_full(view,full,scroll_y):
 vi,vp=decoded_pixels(view);fi,fp=decoded_pixels(full)
 if vi['width']!=WIDTH or vi['height']!=HEIGHT or fi['width']!=WIDTH or vi['channels']!=fi['channels']:q.fail('390px viewport/full PNG dimensions or channels differ')
 if isinstance(scroll_y,bool) or not isinstance(scroll_y,(int,float)) or not math.isfinite(scroll_y) or scroll_y<0 or int(scroll_y)!=scroll_y or scroll_y+HEIGHT>fi['height']:q.fail('Invalid full-page comparison scroll offset')
 stride=WIDTH*vi['channels'];start=int(scroll_y)*stride;reference=fp[start:start+HEIGHT*stride]
 mismatched_rows=[y for y in range(HEIGHT)if vp[y*stride:(y+1)*stride]!=reference[y*stride:(y+1)*stride]]
 if mismatched_rows:q.fail('Viewport pixels differ from same-source full-page reference: '+str(len(mismatched_rows))+' rows; first '+str(mismatched_rows[0]))
 return {'comparedRows':HEIGHT,'matchingRows':HEIGHT,'scrollY':scroll_y,'decodedViewportSHA256':vi['decodedPixelsSHA256'],'referenceRegionSHA256':q.sha(reference)}

GEOMETRY=r'''()=>{const r=document.querySelector('#ribbon-and-order').getBoundingClientRect();return {scrollX:scrollX,scrollY:scrollY,width:innerWidth,height:innerHeight,documentHeight:document.documentElement.scrollHeight,fontStatus:document.fonts.status,rect:{x:r.x,y:r.y,width:r.width,height:r.height}};}'''
SURFACE=r'''()=>[...document.querySelectorAll('#ribbon-and-order [data-copy-key]')].map(n=>{const r=n.getBoundingClientRect();let available=true;for(let p=n;p;p=p.parentElement){const s=getComputedStyle(p);if(s.display==='none'||s.visibility==='hidden'||s.visibility==='collapse'||Number(s.opacity)===0||p.hidden||p.inert||p.getAttribute('aria-hidden')==='true')available=false;}return {key:n.dataset.copyKey,text:n.textContent,tag:n.tagName.toLowerCase(),href:n.getAttribute('href'),available:available&&r.width>0&&r.height>0,rect:{x:r.x,y:r.y,width:r.width,height:r.height}};})'''
SETTLE=r'''async()=>{await document.fonts.ready;const samples=[];let stable=0,prior='';for(let i=0;i<180;i++){await new Promise(requestAnimationFrame);const r=document.querySelector('#ribbon-and-order').getBoundingClientRect();const row={scrollX:scrollX,scrollY:scrollY,width:innerWidth,height:innerHeight,documentHeight:document.documentElement.scrollHeight,fontStatus:document.fonts.status,rect:{x:r.x,y:r.y,width:r.width,height:r.height}};samples.push(row);const key=JSON.stringify(row);stable=key===prior?stable+1:0;prior=key;if(stable>=5)return {stableTransitions:stable,samples};}throw new Error('scroll/rect/font geometry did not settle within 180 frames');}'''

def capture(candidate,output):
 from playwright.sync_api import sync_playwright
 candidate=Path(candidate).resolve();output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True);b=binding();q.check_source_files(candidate.parent,b,True);q.check_dist(candidate/'dist',b);dist=candidate/'dist'
 class Handler(http.server.SimpleHTTPRequestHandler):
  def __init__(self,*a,**kw):super().__init__(*a,directory=str(dist),**kw)
  def log_message(self,*args):pass
  def do_GET(self):
   requested=unquote(urlsplit(self.path).path).lstrip('/')or'index.html';file=(dist/requested).resolve()
   if not file.is_relative_to(dist)or not file.is_file():self.send_error(404);return
   super().do_GET()
 server=socketserver.ThreadingTCPServer(('127.0.0.1',0),Handler);server.daemon_threads=True;threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_address[1]}';blocked=[];errors=[];responses=[];flows=[];failure=None
 report={'status':'CAPTURE_PENDING','sourceRevision':SOURCE,'originalRun':ORIGINAL_RUN,'originalArtifact':ORIGINAL_ARTIFACT,'originalArchiveSHA256':ORIGINAL_ARCHIVE_SHA,'originalProblemPNGSHA256':ORIGINAL_BAD_SHA,'width':WIDTH,'height':HEIGHT,'originalEvidenceReplaced':False,'layoutOrCopyChanged':False,'flows':flows,'externalRequestsBlocked':blocked,'pageErrors':errors,'responses':responses,'publicHTTPVerified':False,'publicationReady':False}
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(headless=True,args=['--no-sandbox']);report['browserVersion']=browser.version;context=browser.new_context(viewport={'width':WIDTH,'height':HEIGHT},device_scale_factor=1,reduced_motion='reduce')
   def route(request):
    if request.request.url.startswith(origin+'/'):request.continue_()
    else:blocked.append(request.request.url);request.abort()
   context.route('**/*',route);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:responses.append({'path':r.url.replace(origin,''),'status':r.status}));response=page.goto(origin+'/',wait_until='networkidle')
   if response.status!=200:q.fail('Loopback home status changed')
   page.evaluate('document.fonts.ready')
   # Load the same seven raster files without editing source attributes, CSS or text.
   for image in page.locator('img').all():image.scroll_into_view_if_needed();image.evaluate('(e)=>e.decode()')
   for name,neighbor,direction in [('from-facility','#receiving-place','down'),('from-timing','#order-timing','up')]:
    page.locator(neighbor).evaluate('(e)=>e.scrollIntoView({block:"start",behavior:"instant"})');neighbor_state=page.evaluate(GEOMETRY);page.locator(SECTION).evaluate('(e)=>e.scrollIntoView({block:"start",behavior:"instant"})');flow={'name':name,'neighbor':neighbor,'direction':direction,'neighborState':neighbor_state,'frames':[]};flows.append(flow)
    for number in [1,2]:
     settled=page.evaluate(SETTLE);before=page.evaluate(GEOMETRY);observations=page.evaluate(SURFACE);filename=f'ribbon390-{name}-frame{number}.png';page.screenshot(path=str(output/filename));after=page.evaluate(GEOMETRY);flow['frames'].append({'number':number,'path':filename,'sha256':q.sha((output/filename).read_bytes()),'settle':settled,'before':before,'after':after,'observations':observations})
   page.evaluate('window.scrollTo({top:0,behavior:"instant"})');settled=page.evaluate(SETTLE);before=page.evaluate(GEOMETRY);filename='home390-full-reference.png';page.screenshot(path=str(output/filename),full_page=True);after=page.evaluate(GEOMETRY);report['fullReference']={'path':filename,'sha256':q.sha((output/filename).read_bytes()),'before':before,'after':after,'settle':settled};context.close();browser.close()
  q.check_source_files(candidate.parent,b,True);q.check_dist(dist,b)
  if blocked or errors:q.fail('Unexpected external request or page error')
  report['status']='CAPTURED_PENDING_PIXEL_VERIFICATION'
 except Exception as error:failure=error;report['status']='CAPTURE_FAILED';report['error']=str(error)
 finally:
  server.shutdown();server.server_close();report['checkedAtUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();q.save(output/'capture-report.json',report)
 if failure:raise failure

def verify_geometry(value):
 if not isinstance(value,dict)or value.get('width')!=WIDTH or value.get('height')!=HEIGHT or value.get('scrollX')!=0 or value.get('fontStatus')!='loaded':q.fail('Stable viewport/font geometry missing')
 q.positive_number(value.get('documentHeight'),'Document height');q.rectangle(value.get('rect'),'Ribbon geometry')
 y=value.get('scrollY')
 if isinstance(y,bool)or not isinstance(y,(int,float))or not math.isfinite(y)or y<0:q.fail('Scroll position invalid')
 return value

def verify_settle(record):
 if not isinstance(record,dict)or record.get('stableTransitions')!=5:q.fail('Consecutive stable paint frames missing')
 samples=q.records(record.get('samples'),len(record.get('samples',[])),'Frame geometry')
 if not 6<=len(samples)<=180:q.fail('Stable frame sample denominator invalid')
 for sample in samples:verify_geometry(sample)
 if any(x!=samples[-1]for x in samples[-6:]):q.fail('Last six geometry frames differ')
 return samples[-1]

def verify_capture(output,b):
 output=Path(output);r=q.read(output/'capture-report.json')
 for key,value in {'status':'CAPTURED_PENDING_PIXEL_VERIFICATION','sourceRevision':SOURCE,'originalRun':ORIGINAL_RUN,'originalArtifact':ORIGINAL_ARTIFACT,'originalArchiveSHA256':ORIGINAL_ARCHIVE_SHA,'originalProblemPNGSHA256':ORIGINAL_BAD_SHA,'width':WIDTH,'height':HEIGHT,'originalEvidenceReplaced':False,'layoutOrCopyChanged':False,'externalRequestsBlocked':[],'pageErrors':[],'publicHTTPVerified':False,'publicationReady':False}.items():
  if r.get(key)!=value:q.fail('Capture boundary changed: '+key)
 full=r.get('fullReference',{});expected_names={'home390-full-reference.png'};data=q.safe_file(output,full.get('path','')).read_bytes()
 if full.get('path')!='home390-full-reference.png'or q.sha(data)!=full.get('sha256'):q.fail('Full reference binding changed')
 if verify_geometry(full['before'])!=verify_geometry(full['after'])or full['before']['scrollY']!=0 or verify_settle(full['settle'])!=full['before']:q.fail('Full reference geometry changed during capture')
 expected=[x for x in b['browserExpected']['occurrences']['/']if x['key'].startswith('section.ribbon-and-order.')];results=[]
 for flow,(name,neighbor,direction)in zip(q.records(r.get('flows'),2,'Scroll directions'),[('from-facility','#receiving-place','down'),('from-timing','#order-timing','up')]):
  if flow.get('name')!=name or flow.get('neighbor')!=neighbor or flow.get('direction')!=direction:q.fail('Scroll direction contract changed')
  neighbor_y=verify_geometry(flow['neighborState'])['scrollY'];pair=[]
  for frame,number in zip(q.records(flow.get('frames'),2,'Consecutive screenshots'),[1,2]):
   filename=f'ribbon390-{name}-frame{number}.png';expected_names.add(filename)
   if frame.get('number')!=number or frame.get('path')!=filename:q.fail('Exact consecutive frame filename missing')
   before=verify_geometry(frame['before']);after=verify_geometry(frame['after'])
   if before!=after or verify_settle(frame['settle'])!=before:q.fail('Geometry shifted during screenshot')
   if (direction=='down'and neighbor_y>=before['scrollY'])or(direction=='up'and neighbor_y<=before['scrollY']):q.fail('Forward/backward scroll not observed')
   if not 0<=before['rect']['y']<HEIGHT:q.fail('Ribbon is not at viewport start')
   for row,want in zip(q.records(frame.get('observations'),len(expected),'Ribbon observations'),expected):
    if any(row.get(k)!=want.get(k)for k in ['key','text','tag','href'])or row.get('available')is not True:q.fail('Ribbon customer occurrence changed')
    q.rectangle(row.get('rect'),'Ribbon occurrence')
   png=q.safe_file(output,filename).read_bytes()
   if q.sha(png)!=frame.get('sha256'):q.fail('Consecutive screenshot SHA changed')
   compared=compare_viewport_to_full(png,data,before['scrollY']);pair.append(compared['decodedViewportSHA256']);results.append({'path':filename,**compared})
  if pair[0]!=pair[1]:q.fail('Consecutive viewport pixels differ')
 if {p.name for p in output.glob('*.png')}!=expected_names:q.fail('Unexpected screenshot inventory')
 responses=r.get('responses')
 if not isinstance(responses,list)or not responses or any(not isinstance(x,dict)or not isinstance(x.get('path'),str)or not x['path'].startswith('/')or x['path'].startswith('//')or x.get('status')!=200 for x in responses):q.fail('Unexpected loopback response')
 required={'/'}|{x['src']for x in b['browserExpected']['images']}|{'/'+x for x in b['expectedDistFiles']if x.endswith('.css')}
 if not required<={x['path']for x in responses}:q.fail('Same-source raster/CSS responses missing')
 return {'status':'PASS_STABLE_RIBBON_FRAMES_AND_FULL_REFERENCE_PIXEL_PARITY','sourceRevision':SOURCE,'originalRun':ORIGINAL_RUN,'actualNewScreenshots':5,'directions':['down','up'],'consecutiveFramesEachDirection':2,'pixelComparisons':results,'originalEvidenceReplaced':False,'rootCause':'Capture/paint timing remains an inference; no source/layout changes were tested','independentVisualReview':'PENDING','publicHTTPVerified':False,'publicationReady':False}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['capture','verify']);parser.add_argument('--candidate',required=True);parser.add_argument('--output',required=True);args=parser.parse_args();b=binding();candidate=Path(args.candidate).resolve();q.check_source_files(candidate.parent,b,True);q.check_dist(candidate/'dist',b)
 if args.mode=='capture':capture(candidate,args.output)
 else:
  result=verify_capture(args.output,b);q.save(Path(args.output)/'verification.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
