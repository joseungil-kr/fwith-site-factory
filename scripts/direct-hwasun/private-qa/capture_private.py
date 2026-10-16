"""Own cloud Chromium, loopback only. Actual-success Goheung capture reused for private Hwasun source47."""
from pathlib import Path
import argparse,json,hashlib,threading,http.server,socketserver,datetime,sys
from urllib.request import urlopen
from urllib.parse import urlsplit,unquote
from playwright.sync_api import sync_playwright


SETTLE=r'''async()=>{await document.fonts.ready;let prior='',stable=0;const samples=[];for(let i=0;i<180;i++){await new Promise(requestAnimationFrame);const row={scrollX,scrollY,width:innerWidth,height:innerHeight,documentHeight:document.documentElement.scrollHeight,fontStatus:document.fonts.status};samples.push(row);const key=JSON.stringify(row);stable=key===prior?stable+1:0;prior=key;if(stable>=5)return {stableTransitions:stable,samples};}throw new Error('Capture geometry did not settle');}'''
HEADER=r"""()=>{const n=document.querySelector('.site-header'),r=n.getBoundingClientRect(),s=getComputedStyle(n);const observations=[...n.querySelectorAll('[data-copy-key]')].map(e=>{const r=e.getBoundingClientRect();let available=true;for(let p=e;p;p=p.parentElement){const s=getComputedStyle(p);if(s.display==='none'||s.visibility==='hidden'||s.visibility==='collapse'||Number(s.opacity)===0||p.hidden||p.inert||p.getAttribute('aria-hidden')==='true')available=false;}return {key:e.dataset.copyKey,text:e.textContent,tag:e.tagName.toLowerCase(),href:e.getAttribute('href'),available:available&&r.width>0&&r.height>0,rect:{x:r.x,y:r.y,width:r.width,height:r.height}};});return {rect:{x:r.x,y:r.y,width:r.width,height:r.height},position:s.position,top:s.top,zIndex:s.zIndex,backgroundColor:s.backgroundColor,backdropFilter:s.backdropFilter,borderBottomWidth:s.borderBottomWidth,observations};}"""
GEOMETRY='()=>({scrollX,scrollY,width:innerWidth,height:innerHeight,documentHeight:document.documentElement.scrollHeight,fontStatus:document.fonts.status})'
METADATA=r"""()=>({robots:document.querySelector('meta[name=robots]').content,canonical:[...document.querySelectorAll('link[rel=canonical]')].map(x=>x.href),productionMetadata:[...document.querySelectorAll('meta[name^="site-factory-"]')].map(x=>[x.name,x.content]),social:[...document.querySelectorAll('meta[property^="og:"],meta[name^="twitter:"]')].map(x=>[x.hasAttribute('property')?'property':'name',x.getAttribute('property')||x.getAttribute('name'),x.content])})"""
STICKY_NAMES={f'home-1280-{section}.png'for section in ['hospital','products','ribbon','appearance','timing','location','faq','sources']}

RESTRICTION='()=>{const obs=n=>{if(!n)return null;const r=n.getBoundingClientRect();let available=true;const ancestors=[];for(let p=n;p;p=p.parentElement){const s=getComputedStyle(p);const a={display:s.display,visibility:s.visibility,opacity:s.opacity,hidden:p.hidden,inert:p.inert,ariaHidden:p.getAttribute(\'aria-hidden\')};ancestors.push(a);if(a.display===\'none\'||[\'hidden\',\'collapse\'].includes(a.visibility)||Number(a.opacity)===0||a.hidden||a.inert||a.ariaHidden===\'true\')available=false;}return {text:n.textContent,tag:n.tagName.toLowerCase(),href:n.getAttribute(\'href\'),rect:{x:r.x,y:r.y,width:r.width,height:r.height},available:available&&r.width>0&&r.height>0,ancestors};};const h=document.querySelector(\'#hospital-restriction\'),a=document.querySelector(\'#opening .actions\'),section=document.querySelector(\'#products-cost\'),heading=section?.querySelector(\'h2\'),notice=section?.querySelector(\'.product-eligibility\'),cards=section?.querySelector(\'[data-purchase-cards]\');return {fragment:location.hash,hero:obs(h),heroText:obs(h?.querySelector(\'[data-copy-key="restriction.text"]\')),heroSource:obs(h?.querySelector(\'a\')),heroActions:[...document.querySelectorAll(\'#opening .actions a\')].map(n=>({text:n.textContent,href:n.getAttribute(\'href\')})),heroBeforeActions:!!h&&h.parentElement?.id===\'opening\'&&h.previousElementSibling?.dataset.copyKey===\'intro.0\'&&h.nextElementSibling===a,productHeading:obs(heading),productNotice:obs(notice),productCards:obs(cards),productAdjacent:!!heading&&heading.parentElement===section&&section.firstElementChild===heading&&heading.nextElementSibling===notice&&notice.nextElementSibling===cards,products:[...document.querySelectorAll(\'[data-product-sku]\')].map(c=>({sku:c.dataset.productSku,heading:c.querySelector(\'h3\')?.textContent,href:c.querySelector(\'.product-photo-link\')?.getAttribute(\'href\'),label:c.querySelector(\'.product-photo-link\')?.getAttribute(\'aria-label\'),ctaHref:c.querySelector(\'[data-order-product-sku]\')?.getAttribute(\'href\'),ctaLabel:c.querySelector(\'[data-order-product-sku]\')?.textContent,shippingLabel:c.querySelector(\'.product-shipping\')?.textContent,sumElements:c.querySelectorAll(\'.product-reference,[data-copy-key$=".sumLabel"]\').length})),selectedHospitalElements:document.querySelectorAll(\'[data-selected-hospital],[itemscope],[itemtype],[itemprop]\').length};}'
LINKS="()=>[...document.querySelectorAll('a')].map(n=>({text:n.textContent,href:n.getAttribute('href'),ariaLabel:n.getAttribute('aria-label')}))"

def run(source,dist,source_revision,browser_source="playwright"):
 global C,D,U,expected
 source=Path(source).resolve();dist=Path(dist).resolve();sys.path.insert(0,str(source/'candidate/scripts'))
 from qa_hwasun import ROOT as C,D,U,expected
 import qa_control as control
 import browser_evidence as validator
 bound=control.binding();assert source_revision==bound['sourceRevision']
 restriction_expected=bound['browserExpected']['restriction']
 evidence=C/'evidence/browser';evidence.mkdir(parents=True,exist_ok=False);captures=[];metadata=[];http_rows=[]
 def screenshot(page,name,full=False):
  settled=page.evaluate(SETTLE);restriction_before=None
  scope='hospital'if name.endswith('-hospital.png')else'products'if name.endswith('-products.png')else None
  if scope:
   restriction_before=page.evaluate(RESTRICTION);validator.verify_restriction(restriction_before,restriction_expected,page.viewport_size['width'],scope)
  before=page.evaluate('()=>({scrollX,scrollY,width:innerWidth,height:innerHeight,documentHeight:document.documentElement.scrollHeight,fontStatus:document.fonts.status})');page.screenshot(path=str(evidence/name),full_page=full);after=page.evaluate('()=>({scrollX,scrollY,width:innerWidth,height:innerHeight,documentHeight:document.documentElement.scrollHeight,fontStatus:document.fonts.status})');assert before==after and settled['samples'][-1]==before
  row={'path':name,'fullPage':full,'before':before,'after':after,'settle':settled}
  if scope:
   restriction_after=page.evaluate(RESTRICTION);assert restriction_after==restriction_before
   row['restrictionSnapshot']={'scope':scope,'before':restriction_before,'after':restriction_after,'screenshotSHA256':hashlib.sha256((evidence/name).read_bytes()).hexdigest()}
   assert page.evaluate(GEOMETRY)==before
  if name in STICKY_NAMES:
   header_before=page.evaluate(HEADER);clip=evidence/'sticky-headers'/name;clip.parent.mkdir(exist_ok=True)
   page.locator('.site-header').screenshot(path=str(clip));header_after=page.evaluate(HEADER);geometry_after=page.evaluate(GEOMETRY)
   assert header_before==header_after and before==geometry_after
   row['stickyHeader']={'path':'sticky-headers/'+name,'sha256':hashlib.sha256(clip.read_bytes()).hexdigest(),'before':header_before,'after':header_after,'geometryAfter':geometry_after}
  captures.append(row)
 responses=[];blocked=[];errors=[];states=[];images=[];interactions=[];reach=[];touch=[]
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
     state=page.evaluate(evaluator,expected(route));state.update({'width':width,'route':route,'links':page.evaluate(LINKS)});assert not state['failures'] and state['bodyExact'],state['failures'];assert state['scrollWidth']<=width,state
     states.append(state);metadata.append({'width':width,'route':route,**page.evaluate(METADATA)});name='home' if route=='/' else '404';screenshot(page,f'{name}-{width}-top.png')
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
     r=n.bounding_box();assert r and r['width']>=44 and r['height']>=44,(width,n.text_content(),r);touch.append({'width':width,'text':n.text_content(),'href':n.get_attribute('href'),'ariaLabel':n.get_attribute('aria-label'),'height':r['height'],'widthPx':r['width']})
    for label,selector in [('hospital','#hospital-restriction'),('products','#products-cost'),('ribbon','#ribbon-order'),('appearance','#appearance'),('timing','#order-timing'),('location','#locations'),('faq','#questions'),('sources','#sources')]:
     if label=='products':page.goto(origin+'/#products-cost',wait_until='networkidle')
     elif label=='hospital':
      page.locator(selector).evaluate('(e)=>window.scrollTo({top:e.getBoundingClientRect().top+scrollY-(innerWidth>860?90:16),behavior:"instant"})')
     else:page.locator(selector).evaluate('(e)=>e.scrollIntoView({block:"start",behavior:"instant"})')
     screenshot(page,f'home-{width}-{label}.png')
    page.evaluate('window.scrollTo({top:0,behavior:"instant"})');screenshot(page,f'home-{width}-full.png',full=True)
    for link in U['navigation']:
     page.goto(origin+'/',wait_until='networkidle');page.locator('nav a[href="'+link['href']+'"]').click();assert urlsplit(page.url).fragment==link['href'][1:];r=page.locator(link['href']).bounding_box();assert r and -1<=r['y']<844,(width,link,r)
     page.go_back();assert not urlsplit(page.url).fragment;page.go_forward();assert urlsplit(page.url).fragment==link['href'][1:];interactions.append({'width':width,'test':'anchor/back/forward','href':link['href'],'pass':True})
    page.goto(origin+'/404.html',wait_until='networkidle');page.locator('nav a').first.click();assert page.url==origin+'/'+U['navigation'][0]['href'];interactions.append({'width':width,'test':'404 navigation home anchor','pass':True})
    page.goto(origin+'/404.html',wait_until='networkidle');page.locator('[data-copy-key="404.ctaLabel"]').click();assert page.url==origin+'/';interactions.append({'width':width,'test':'404 recovery CTA','pass':True})
   # Prove computed-style visibility checks detect hidden FAQ even when source text remains.
   page.goto(origin+'/',wait_until='networkidle');style=page.add_style_tag(content='#questions{display:none!important}');bad=page.evaluate(evaluator,expected('/'));assert set(bad['failures'])=={x['key']for x in expected('/')if x['key']=='section.questions.heading'or x['key'].startswith('question-')};style.evaluate('(e)=>e.remove()');assert not page.evaluate(evaluator,expected('/'))['failures']
   restriction_mutations=[]
   for selector,key in [('#hospital-restriction','hero'),('.product-eligibility','productNotice')]:
    for rule in ['display:none','visibility:hidden','opacity:0']:
     style=page.add_style_tag(content=selector+'{'+rule+'!important}');bad=page.evaluate(RESTRICTION);assert bad[key]['available']is False
     restriction_mutations.append({'selector':selector,'rule':rule,'detected':True});style.evaluate('(e)=>e.remove()');assert page.evaluate(RESTRICTION)[key]['available']is True
   missing=page.goto(origin+'/.hwasun-private-missing/',wait_until='networkidle');assert missing.status==404 and page.locator('h1').text_content()==D['notFoundCopyPlan']['h1'];assert page.locator('meta[name="robots"]').get_attribute('content')=='noindex,nofollow';missing_row={'path':'/.hwasun-private-missing/','status':missing.status,'sha256':hashlib.sha256(missing.body()).hexdigest(),'bytes':len(missing.body()),'robots':page.locator('meta[name=robots]').get_attribute('content'),'canonicalCount':page.locator('link[rel=canonical]').count()};screenshot(page,'missing-route-404.png')
   for file in sorted(p for p in dist.rglob('*')if p.is_file()):
    relative=file.relative_to(dist).as_posix();route='/'if relative=='index.html'else'/'+relative
    with urlopen(origin+route,timeout=20)as response:
     raw=response.read();assert response.status==200 and raw==file.read_bytes();http_rows.append({'path':route,'status':response.status,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'contentType':response.headers.get('Content-Type'),'finalURLPath':urlsplit(response.url).path})
   assert not errors and not blocked,(errors,blocked);context.close();browser.close()
 finally:server.shutdown();server.server_close()
 report={'status':'PASS_AUTHOR_LOCAL_CHROMIUM_CHECKS','checkedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'browser':'GitHub Actions headless Chromium via pinned Playwright; loopback only; no user computer used','browserVersion':version,'origin':'loopback-only','widths':[320,390,1280],'pages':2,'states':states,'scrollReachability':reach,'imageAspectChecks':images,'touchTargets':touch,'interactions':interactions,'computedVisibilityMutationDetected':True,'restrictionVisibilityMutations':restriction_mutations,'localMissingRouteStatus':404,'responses':responses,'externalRequestsBlocked':blocked,'pageErrors':errors,'externalCTAAndPhoneActivated':False,'publicHTTPVerified':False,'independentImplementationReview':False,'screenshots':[{'path':x.name,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()}for x in sorted(evidence.glob('*.png'))]}
 (evidence/'private-capture.json').write_text(json.dumps({'sourceRevision':source_revision,'origin':'loopback-only','captures':captures,'metadata':metadata,'httpFiles':http_rows,'missingRoute':missing_row,'publicHTTPVerified':False,'publicationReady':False},ensure_ascii=False,indent=2)+'\n');(evidence/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','browserVersion','widths','pages','computedVisibilityMutationDetected','localMissingRouteStatus','externalRequestsBlocked','pageErrors','publicHTTPVerified']},ensure_ascii=False))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--dist',required=True);parser.add_argument('--source-revision',required=True);args=parser.parse_args();run(args.source,args.dist,args.source_revision)
