"""Cloud-computer Chromium/Playwright loopback verification only. No public URL requests."""
from pathlib import Path
import argparse,json,hashlib,threading,http.server,socketserver,functools,sys,time
from urllib.parse import urlsplit,unquote
from playwright.sync_api import sync_playwright

def run(source,dist,evidence):
 source=Path(source).resolve();dist=Path(dist).resolve();evidence=Path(evidence).resolve();evidence.mkdir(parents=True,exist_ok=True)
 m=json.loads((source/'inputs/reviewed-copy/output-context-map.json').read_text());copy=json.loads((source/'inputs/reviewed-copy/customer-copy.json').read_text());states=m['states'];results=[];requests=[];blocked=[]
 class Handler(http.server.SimpleHTTPRequestHandler):
  def __init__(self,*a,**kw):super().__init__(*a,directory=str(dist),**kw)
  def log_message(self,*args):pass
  def do_GET(self):
   name=unquote(urlsplit(self.path).path).lstrip('/') or 'index.html';file=(dist/name).resolve()
   if not file.is_relative_to(dist) or not file.is_file():
    body=(dist/'404.html').read_bytes();self.send_response(404);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
   super().do_GET()
 server=socketserver.ThreadingTCPServer(('127.0.0.1',0),Handler);server.daemon_threads=True;threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_address[1]}'
 def route_handler(route):
  if route.request.url.startswith(origin+'/'):route.continue_()
  else:blocked.append(route.request.url);route.abort()
 evaluator=r'''({map,pageId,state})=>{
 function available(n){
  if(n.closest('head'))return false;
  for(let e=n;e;e=e.parentElement){let s=getComputedStyle(e);if(s.display==='none'||s.visibility==='hidden'||s.visibility==='collapse'||Number(s.opacity)===0||e.hidden||e.inert||e.getAttribute('aria-hidden')==='true')return false;if(e.tagName==='DETAILS'&&!e.open&&!e.querySelector('summary')?.contains(n))return false;}
  const r=n.getBoundingClientRect();return r.width>0&&r.height>0&&r.right>0&&r.left<innerWidth;
 }
 const observations=[],failures=[];
 for(const row of map.contexts)for(const o of row.occurrences){if(!o.pageIds.includes(pageId))continue;const ns=[...document.querySelectorAll(o.selector)];if(ns.length!==o.expectedDOMMatchesPerPage){failures.push({pointer:row.pointer,selector:o.selector,kind:'count',actual:ns.length});continue;}
  for(const n of ns){const t=o.extraction==='textContent'?n.textContent:n.getAttribute(o.extraction.split(':')[1]);const a=available(n),want=o.layoutAvailableByState[state.id],r=n.getBoundingClientRect();const x={pointer:row.pointer,selector:o.selector,tag:n.tagName,extraction:o.extraction,text:t,actualAvailable:a,expectedAvailable:want,rect:{x:r.x,y:r.y,width:r.width,height:r.height}};observations.push(x);if(n.tagName!==o.requiredTag||t!==o.expectedExtractedText||a!==want)failures.push(x);}
 }
 return {pageId,state,observations,failures,scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,activeTag:document.activeElement.tagName,activeClass:document.activeElement.className};}'''
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox']);version=browser.version
  context=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1,reduced_motion='reduce');context.route('**/*',route_handler)
  page=context.new_page();errors=[];page.on('pageerror',lambda err:errors.append(str(err)));page.on('response',lambda response:requests.append({'url':response.url.replace(origin,'LOOPBACK'),'status':response.status}))
  for pageid,url in [('home','/'),('notFound','/404.html')]:
   for state in states:
    page.set_viewport_size({'width':state['width'],'height':844});response=page.goto(origin+url,wait_until='networkidle');assert response.status==200
    page.evaluate('document.fonts.ready');assert page.locator('details.mobile-menu').count()==1
    if state['menuOpen']:page.locator('details.mobile-menu > summary').click()
    if state['skipFocused']:
     page.keyboard.press('Tab');assert page.locator('.skip-link').evaluate('(el)=>el===document.activeElement')
    data=page.evaluate(evaluator,{'map':m,'pageId':pageid,'state':state});results.append(data)
    (evidence/f'{pageid}-{state["id"]}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    page.screenshot(path=str(evidence/f'{pageid}-{state["id"]}.png'))
    assert not data['failures'],('occurrence mismatch',pageid,state,data['failures'][:3])
    assert data['scrollWidth']<=data['clientWidth'],('horizontal overflow',pageid,state)
  interactions=[];images=[];scrolls=[]
  for width in [320,390,1280]:
   page.set_viewport_size({'width':width,'height':844});page.goto(origin+'/',wait_until='networkidle')
   page.keyboard.press('Tab');assert page.locator('.skip-link').evaluate('(el)=>el===document.activeElement');page.keyboard.press('Enter');assert page.locator('#main-content').evaluate('(el)=>el===document.activeElement');interactions.append({'width':width,'test':'keyboard skip Enter focuses main','pass':True})
   if width<861:
    summary=page.locator('details.mobile-menu > summary');summary.focus()
    for key in ['Enter','Enter','Space','Space']:
     was=page.locator('details.mobile-menu').evaluate('(el)=>el.open');page.keyboard.press(key);assert page.locator('details.mobile-menu').evaluate('(el)=>el.open')!=was
    for _ in range(2):summary.click();assert page.locator('details.mobile-menu').evaluate('(el)=>el.open');summary.click();assert not page.locator('details.mobile-menu').evaluate('(el)=>el.open')
    interactions.append({'width':width,'test':'native menu repeated Enter/Space/click toggles','pass':True})
   # Exact internal nav links, hash, browser Back and Forward. No telephone or external CTA activation.
   for fragment in ['products','budget','ribbon','order','faq']:
    page.goto(origin+'/',wait_until='networkidle')
    if width<861:page.locator('details.mobile-menu > summary').click();nav='details.mobile-menu nav'
    else:nav='nav.desktop-navigation'
    page.locator(nav+f' a[href="/#{fragment}"]').click();assert page.url.endswith('/#'+fragment)
    if width<861:page.locator('details.mobile-menu > summary').click()
    r=page.locator('#'+fragment).bounding_box();assert r and r['y']>=-1 and r['y']<844
    page.go_back();assert not urlsplit(page.url).fragment;page.go_forward();assert urlsplit(page.url).fragment==fragment
    interactions.append({'width':width,'test':'anchor/back/forward','fragment':fragment,'pass':True})
   page.goto(origin+'/404.html',wait_until='networkidle')
   if width<861:page.locator('details.mobile-menu > summary').click();nav='details.mobile-menu nav'
   else:nav='nav.desktop-navigation'
   page.locator(nav+' a[href="/#products"]').click();assert page.url==origin+'/#products'
   interactions.append({'width':width,'test':'404 menu returns to home fragment','pass':True})
   page.goto(origin+'/',wait_until='networkidle')
   # Every authored visual occurrence gets a scroll-reachability check. State changes/focus were tested above.
   for i,n in enumerate(page.locator('main [data-reviewed-block],main img').all()):
    n.scroll_into_view_if_needed();r=n.bounding_box();assert r and r['width']>0 and r['height']>0
    geometry=n.evaluate('(el)=>{const r=el.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,viewportWidth:innerWidth,viewportHeight:innerHeight,scrollHeight:el.scrollHeight,clientHeight:el.clientHeight}}')
    assert geometry['left']>=-1 and geometry['right']<=width+1 and geometry['bottom']>0 and geometry['top']<844
    scrolls.append({'width':width,'index':i,'tag':n.evaluate('(el)=>el.tagName'),'text':n.text_content() if n.evaluate('(el)=>el.tagName')!='IMG' else n.get_attribute('alt'),'geometry':geometry})
   for n in page.locator('main img').all():
    n.scroll_into_view_if_needed();n.evaluate('(el)=>el.decode()');d=n.evaluate('(el)=>({src:el.getAttribute("src"),naturalWidth:el.naturalWidth,naturalHeight:el.naturalHeight,objectFit:getComputedStyle(el).objectFit,width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height})');assert d['naturalWidth']>0 and abs(d['width']/d['height']-d['naturalWidth']/d['naturalHeight'])<0.01;images.append({'width':width,**d})
   for selector in ['#opening','[data-shared-flower-banner="message"]','#products','#budget','#ribbon','#destinations','#order','#faq','[data-shared-flower-banner="consultation"]','#sources','footer']:
    n=page.locator(selector);n.scroll_into_view_if_needed();name=selector.replace('#','').replace('[data-shared-flower-banner="','').replace('"]','');n.screenshot(path=str(evidence/f'home-{width}-{name}-section.png'))
   page.locator('#opening').scroll_into_view_if_needed();page.screenshot(path=str(evidence/f'home-{width}-full.png'),full_page=True)
   for n in page.locator('[data-required-cta],footer a,.mobile-bar a').all():
    if not n.is_visible():continue
    r=n.bounding_box();assert r and r['height']>=44 and r['width']>=44,('touch target',width,n.text_content(),r)
   page.goto(origin+'/404.html',wait_until='networkidle');page.locator('main [data-required-cta]').click();assert page.url==origin+'/'
   interactions.append({'width':width,'test':'404 recovery CTA returns home','pass':True})
  missing=page.goto(origin+'/.gokseong-local-missing/',wait_until='networkidle');assert missing.status==404 and page.locator('h1').text_content()==copy['notFound']['h1'];assert page.locator('meta[name=robots]').get_attribute('content')=='noindex,follow'
  assert not errors and not blocked,(errors,blocked)
  context.close();browser.close()
 server.shutdown();server.server_close()
 manifest=[{'path':p.relative_to(evidence).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(evidence.rglob('*')) if p.is_file()]
 result={'status':'PASS_LOCAL_CHROMIUM_EXACT_OCCURRENCES_AND_STATES','browser':'Cloud computer headless Chromium via existing Playwright','browserVersion':version,'origin':'LOOPBACK_ONLY','publicHTTPVerified':False,'sourceRevision':None,'statesPerPage':8,'pages':2,'stateChecks':len(results),'authoredLeaves':102,'logicalOccurrences':119,'supplementalTechnicalSKUIdentifiers':4,'pageExpandedOccurrenceObservations':sum(len(r['observations']) for r in results),'stateResults':[{k:v for k,v in r.items() if k!='observations'} for r in results],'interactions':interactions,'scrollReachabilityChecks':scrolls,'imageChecks':images,'localResponses':requests,'localMissingRouteStatus':404,'externalRequestsBlocked':blocked,'pageErrors':errors,'externalOrderingAndPhoneNotActivated':True,'artifacts':manifest,'limitations':['Local browser only; no public provider behavior or public release verified.','Source evidence author review is not independent pixel review.','No real checkout, calls, availability, indexing or ranking verified.']}
 (evidence/'browser-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['scrollReachabilityChecks','stateResults','interactions','localResponses','artifacts','imageChecks']},ensure_ascii=False,indent=2));return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--dist',required=True);p.add_argument('--evidence',required=True);a=p.parse_args();run(a.source,a.dist,a.evidence)
