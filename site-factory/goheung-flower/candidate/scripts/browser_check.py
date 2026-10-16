"""Own cloud Chromium, loopback only. Reused Gurye browser/HTTP checker adapted to accepted Goheung occurrences; unexecuted in the socket-restricted local preparation."""
from pathlib import Path
import argparse,json,hashlib,threading,http.server,socketserver,datetime
from urllib.parse import urlsplit,unquote
from playwright.sync_api import sync_playwright
from qa_goheung import ROOT as C,D,U,COPY as copy,expected,norm

def run(browser_source="system"):
 dist=C/'dist';evidence=C/'evidence/browser';evidence.mkdir(parents=True,exist_ok=True);responses=[];blocked=[];errors=[];states=[];images=[];interactions=[];reach=[];touch=[]
 class Handler(http.server.SimpleHTTPRequestHandler):
  def __init__(self,*a,**kw):super().__init__(*a,directory=str(dist),**kw)
  def log_message(self,*args):pass
  def do_GET(self):
   target=unquote(urlsplit(self.path).path).lstrip('/') or 'index.html';file=(dist/target).resolve()
   if not file.is_relative_to(dist) or not file.is_file():
    data=(dist/'404.html').read_bytes();self.send_response(404);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
   super().do_GET()
 server=socketserver.ThreadingTCPServer(('127.0.0.1',0),Handler);server.daemon_threads=True;threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_address[1]}'
 evaluator=r'''(want)=>{const norm=s=>s.replace(/\s+/g,' ').trim();const nodes=[...document.querySelectorAll('[data-copy-key]')];const failures=[],observations=[];
 if(nodes.length!==want.length)failures.push('wrong occurrence count');
 for(let i=0;i<want.length;i++){const e=want[i],n=nodes[i];if(!n){failures.push(e.key);continue;}const r=n.getBoundingClientRect();let available=true;for(let p=n;p;p=p.parentElement){const s=getComputedStyle(p);if(s.display==='none'||s.visibility==='hidden'||s.visibility==='collapse'||Number(s.opacity)===0||p.hidden||p.inert||p.getAttribute('aria-hidden')==='true')available=false;}
 const row={key:n.dataset.copyKey,text:n.textContent,tag:n.tagName.toLowerCase(),href:n.getAttribute('href'),available:available&&r.width>0&&r.height>0,rect:{x:r.x,y:r.y,width:r.width,height:r.height}};observations.push(row);
 if(row.key!==e.key||norm(row.text)!==norm(e.text)||row.tag!==e.tag||('href'in e&&row.href!==e.href)||!row.available)failures.push(e.key);
 }
 return {failures,observations,scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,bodyExact:(()=>{const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT),parts=[];let n;while(n=walker.nextNode())if(n.textContent.trim())parts.push(n.textContent);return norm(parts.join(' '))===norm(want.map(x=>x.text).join(' '));})()};}'''
 try:
  with sync_playwright() as p:
   launch={'headless':True,'args':['--no-sandbox']}
   if browser_source=='system':launch['executable_path']='/usr/bin/chromium'
   browser=p.chromium.launch(**launch);version=browser.version;context=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1,reduced_motion='reduce')
   def routing(route):
    if route.request.url.startswith(origin+'/'):route.continue_()
    else:blocked.append(route.request.url);route.abort()
   context.route('**/*',routing);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:responses.append({'path':r.url.replace(origin,''),'status':r.status}))
   for width in [320,390,1280]:
    page.set_viewport_size({'width':width,'height':844})
    for route in ['/','/404.html']:
     response=page.goto(origin+route,wait_until='networkidle');assert response.status==200;page.evaluate('document.fonts.ready')
     state=page.evaluate(evaluator,expected(route));state.update({'width':width,'route':route});assert not state['failures'] and state['bodyExact'],state['failures'];assert state['scrollWidth']<=width,state
     states.append(state);name='home' if route=='/' else '404';page.screenshot(path=str(evidence/f'{name}-{width}-top.png'))
     page.keyboard.press('Tab');assert page.locator('.skip-link').evaluate('(e)=>e===document.activeElement');r=page.locator('.skip-link').bounding_box();assert r['x']>=0;page.keyboard.press('Enter');assert page.locator('#main-content').evaluate('(e)=>e===document.activeElement');interactions.append({'width':width,'route':route,'test':'keyboard skip focuses main','pass':True})
    page.goto(origin+'/',wait_until='networkidle')
    for entry in expected('/'):
     if entry['key']=='ui.skipLabel':continue
     n=page.locator(f'[data-copy-key="{entry["key"]}"]');n.scroll_into_view_if_needed();r=n.bounding_box();assert r and r['width']>0 and r['height']>0 and r['x']>=-1 and r['x']+r['width']<=width+1 and r['y']<844 and r['y']+r['height']>0,(width,entry,r)
     reach.append({'width':width,'key':entry['key'],'rect':r})
    for n in page.locator('img').all():
     n.scroll_into_view_if_needed();n.evaluate('(e)=>e.decode()');row=n.evaluate('(e)=>{const r=e.getBoundingClientRect();return {src:e.getAttribute("src"),naturalWidth:e.naturalWidth,naturalHeight:e.naturalHeight,displayWidth:r.width,displayHeight:r.height,objectFit:getComputedStyle(e).objectFit};}')
     assert row['naturalWidth']>0 and row['objectFit']=='contain' and abs(row['displayWidth']/row['displayHeight']-row['naturalWidth']/row['naturalHeight'])<.01,row
     images.append({'width':width,**row})
    for n in page.locator('a:not(.skip-link)').all():
     r=n.bounding_box();assert r and r['width']>=44 and r['height']>=44,(width,n.text_content(),r);touch.append({'width':width,'text':n.text_content(),'height':r['height'],'widthPx':r['width']})
    for label,selector in [('products','#budget'),('ribbon','#message-order'),('appearance','#appearance'),('timing','#timing'),('location','#location'),('faq','#questions'),('sources','#sources')]:
     n=page.locator(selector);n.evaluate('(e)=>e.scrollIntoView({block:"start"})');page.screenshot(path=str(evidence/f'home-{width}-{label}.png'))
    page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(evidence/f'home-{width}-full.png'),full_page=True)
    for link in U['navigation']:
     page.goto(origin+'/',wait_until='networkidle');page.locator('nav a[href="'+link['href']+'"]').click();assert urlsplit(page.url).fragment==link['href'][1:];r=page.locator(link['href']).bounding_box();assert r and -1<=r['y']<844,(width,link,r)
     page.go_back();assert not urlsplit(page.url).fragment;page.go_forward();assert urlsplit(page.url).fragment==link['href'][1:];interactions.append({'width':width,'test':'anchor/back/forward','href':link['href'],'pass':True})
    page.goto(origin+'/404.html',wait_until='networkidle');page.locator('nav a').first.click();assert page.url==origin+'/#budget';interactions.append({'width':width,'test':'404 navigation home anchor','pass':True})
    page.goto(origin+'/404.html',wait_until='networkidle');page.locator('[data-copy-key="404.ctaLabel"]').click();assert page.url==origin+'/';interactions.append({'width':width,'test':'404 recovery CTA','pass':True})
   # Prove computed-style visibility checks detect hidden FAQ even when source text remains.
   page.goto(origin+'/',wait_until='networkidle');style=page.add_style_tag(content='#questions{display:none!important}');bad=page.evaluate(evaluator,expected('/'));assert len(bad['failures'])==7;style.evaluate('(e)=>e.remove()');assert not page.evaluate(evaluator,expected('/'))['failures']
   missing=page.goto(origin+'/.goheung-private-missing/',wait_until='networkidle');assert missing.status==404 and page.locator('h1').text_content()==D['notFoundCopyPlan']['h1'];assert page.locator('meta[name="robots"]').get_attribute('content')=='noindex,nofollow';page.screenshot(path=str(evidence/'missing-route-404.png'))
   assert not errors and not blocked,(errors,blocked);context.close();browser.close()
 finally:server.shutdown();server.server_close()
 report={'status':'AUTHOR_BROWSER_CHECKS_PASSED_PENDING_INDEPENDENT_PIXEL_REVIEW','checkedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'browser':'Own cloud headless Chromium via installed Playwright; no user computer used','browserVersion':version,'origin':'loopback-only','widths':[320,390,1280],'pages':2,'states':states,'scrollReachability':reach,'imageAspectChecks':images,'touchTargets':touch,'interactions':interactions,'computedVisibilityMutationDetected':True,'localMissingRouteStatus':404,'responses':responses,'externalRequestsBlocked':blocked,'pageErrors':errors,'externalCTAAndPhoneActivated':False,'publicHTTPVerified':False,'independentImplementationReview':False,'screenshots':[{'path':x.name,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()}for x in sorted(evidence.glob('*.png'))]}
 (evidence/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','browserVersion','widths','pages','computedVisibilityMutationDetected','localMissingRouteStatus','externalRequestsBlocked','pageErrors','publicHTTPVerified']},ensure_ascii=False))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--browser-source',choices=['system','playwright'],default='system');args=parser.parse_args();run(args.browser_source)
