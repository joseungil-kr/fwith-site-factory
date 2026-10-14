"""Deferred runner-only capture. Does not publish, dial, order, or request external URLs."""
from functools import partial
from pathlib import Path
from threading import Thread
from urllib.parse import urlsplit,urljoin
from importlib.metadata import version
import argparse,json,os,sys,traceback,urllib.request
from adapter import *
import capture as upstream_capture

FACTS=r'''() => {
 const text=e=>e?.innerText.trim()||'';
 const image=i=>({src:new URL(i.currentSrc||i.src).pathname,alt:i.alt,complete:i.complete,naturalWidth:i.naturalWidth,naturalHeight:i.naturalHeight,width:i.getBoundingClientRect().width,height:i.getBoundingClientRect().height,objectFit:getComputedStyle(i).objectFit});
 const article=document.querySelector('article[data-page-id]');
 return {title:document.title,description:document.querySelector('meta[name="description"]')?.content,
 h1:[...document.querySelectorAll('h1')].map(text),firstAnswer:text(document.querySelector('[data-first-answer]')),
 viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,
 overflow:[...document.querySelectorAll('main *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.left<-.5||r.right>innerWidth+.5)}).map(e=>({tag:e.tagName,class:e.className})),
 robots:document.querySelector('meta[name="robots"]')?.content,canonical:document.querySelector('link[rel="canonical"]')?.href||null,
 pageId:article?.dataset.pageId,copySha:article?.dataset.copySha,
 ids:[...document.querySelectorAll('[id]')].map(e=>e.id),duplicateIds:[...new Set([...document.querySelectorAll('[id]')].map(e=>e.id))].filter(id=>document.querySelectorAll('#'+CSS.escape(id)).length>1),
 fontStatus:document.fonts.status,bodyFont:getComputedStyle(document.body).fontFamily,
 faq:[...document.querySelectorAll('[data-faq-entry]')].map(e=>({question:text(e.querySelector('[data-faq-question]')),answer:text(e.querySelector('[data-faq-answer]')),visible:e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}),collapsed:!!e.closest('details:not([open])')})),
 images:[...document.images].map(image),banners:[...document.querySelectorAll('[data-shared-flower-banner]')].map(e=>({variant:e.dataset.sharedFlowerBanner,...image(e.querySelector('img'))})),
 products:[...document.querySelectorAll('[data-product-sku]')].map(e=>({sku:e.dataset.productSku,family:e.dataset.productFamily,...image(e.querySelector('img')),href:e.querySelector('[data-order-product-sku]').getAttribute('href'),name:text(e.querySelector('h3,h4')),price:text(e.querySelector('strong')),description:text(e.querySelector('p:not(.product-sku):not(.product-notice)')),sampleLabel:text(e.querySelector('.product-notice')),descriptionVisible:e.querySelector('p:not(.product-sku):not(.product-notice)').checkVisibility({checkOpacity:true,checkVisibilityCSS:true}),sampleLabelVisible:e.querySelector('.product-notice').checkVisibility({checkOpacity:true,checkVisibilityCSS:true})})),
 sources:[...document.querySelectorAll('[data-source-references] .copy-links a')].map(e=>({label:text(e),href:e.getAttribute('href')})),sourceSectionCount:document.querySelectorAll('[data-source-references]').length,sourceNote:text(document.querySelector('[data-source-references]>p')),
 phones:[...document.querySelectorAll('a[href^="tel:"]')].map(e=>e.getAttribute('href')),
 links:[...document.querySelectorAll('a[href]')].map(e=>e.getAttribute('href')),
 fixedBar:!!document.querySelector('.mobile-bar')&&getComputedStyle(document.querySelector('.mobile-bar')).display!=='none'};
}'''

GEOMETRY=r'''el => {
 const r=el.getBoundingClientRect(),h=document.querySelector('.site-header'),b=document.querySelector('.mobile-bar');
 const visible=e=>!!e&&getComputedStyle(e).display!=='none'&&e.getBoundingClientRect().height>0;
 let safeTop=visible(h)?Math.max(0,h.getBoundingClientRect().bottom):0,safeBottom=visible(b)?Math.min(innerHeight,b.getBoundingClientRect().top):innerHeight,region='content';
 if(el.matches('.skip-link')){safeTop=0;safeBottom=innerHeight;region='skip';}
 else if(h?.contains(el)||el===h){safeTop=Math.max(0,h.getBoundingClientRect().top);safeBottom=Math.min(innerHeight,h.getBoundingClientRect().bottom);region='header';}
 else if(visible(b)&&b.contains(el)){safeTop=Math.max(0,b.getBoundingClientRect().top);safeBottom=Math.min(innerHeight,b.getBoundingClientRect().bottom);region='mobile-bar';}
 const hitTests=[];for(const fx of [.1,.5,.9])for(const fy of [.1,.5,.9]){const hit=document.elementFromPoint(r.left+r.width*fx,r.top+r.height*fy);hitTests.push(!!hit&&(hit===el||el.contains(hit)));}
 const c=getComputedStyle(el);
 return{visible:el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}),left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,safeTop,safeBottom,viewportWidth:innerWidth,viewportHeight:innerHeight,region,hitTests,focusVisible:el.matches(':focus-visible'),outlineWidth:parseFloat(c.outlineWidth),outlineStyle:c.outlineStyle,tag:el.tagName,href:el.getAttribute('href'),domIndex:[...document.querySelectorAll('a[href],button,input,select,textarea,summary,[tabindex]')].indexOf(el)};
}'''

geometry_ok=assert_geometry

def center(page,locator):
    # Scroll only: original CSS, DOM and sticky controls stay unchanged.
    locator.evaluate(r'''el=>{const r=el.getBoundingClientRect(),h=document.querySelector('.site-header'),b=document.querySelector('.mobile-bar');const visible=e=>!!e&&getComputedStyle(e).display!=='none';const top=visible(h)?h.getBoundingClientRect().height:0,bottom=visible(b)?b.getBoundingClientRect().height:0;scrollTo({top:scrollY+r.top-top-Math.max(8,(innerHeight-top-bottom-r.height)/2),behavior:'instant'});}''')
    page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')

def shot(page,output,route,width,height,label,full=False):
    name='home'if route=='/'else route.strip('/').replace('/','--').replace('.','-')
    rel=f'screenshots/{width}/{name}/{label}.jpg';p=output/rel;p.parent.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(p),type='jpeg',quality=90,full_page=full,animations='disabled')
    return {'route':route,'width':width,'height':height,'label':label,'kind':'full-page'if full else'risk-viewport','screenshot':rel,'sha256':digest(p.read_bytes()),'dimensions':upstream.jpeg_dimensions(p.read_bytes()),'issues':[]}

def go(page,origin,route):
    response=page.goto(origin+route,wait_until='networkidle');require(response and response.status==200,'Loopback route HTTP')
    page.locator('main').wait_for();upstream_capture.settle(page)
    return response

def keyboard(page,origin,route,output,width,height):
    go(page,origin,route)
    count=page.evaluate("()=>[...document.querySelectorAll('a[href],button,input,select,textarea,summary,[tabindex]')].filter(e=>e.tabIndex>=0&&getComputedStyle(e).display!=='none'&&getComputedStyle(e).visibility!=='hidden'&&e.getClientRects().length>0&&!e.closest('details:not([open]) nav')).length")
    require(1<count<250,'Keyboard target count');rows=[]
    for _ in range(count):
        page.keyboard.press('Tab');page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
        fact=page.locator(':focus').evaluate(GEOMETRY);geometry_ok(fact,True);rows.append(fact)
    require(len({r['domIndex']for r in rows})==count,'Keyboard skipped/repeated target')
    return {'passed':True,'count':count,'targets':rows,'externalAndPhoneTargetsActivated':False,'screenshot':shot(page,output,route,width,height,'keyboard-final-focus')}

def menu(page,origin,route,width,output,height):
    go(page,origin,route)
    if width>860:
        require(not page.locator('.mobile-menu').is_visible() and page.locator('.desktop-navigation').is_visible(),'Desktop menu breakpoint')
        return {'passed':True,'mode':'desktop-navigation'}
    details=page.locator('.mobile-menu');summary=details.locator('summary');require(details.is_visible(),'Native details menu missing')
    require(details.get_attribute('open') is None,'Menu initially open')
    summary.click();require(details.get_attribute('open') is not None,'Click failed to open native menu')
    require(details.locator('nav a').count()>0 and all(a.is_visible()for a in details.locator('nav a').all()),'Menu links invisible')
    receipt=shot(page,output,route,width,height,'menu-open')
    summary.click();require(details.get_attribute('open') is None,'Click failed to close')
    summary.focus();page.keyboard.press('Enter');require(details.get_attribute('open') is not None,'Enter failed to open')
    page.keyboard.press('Space');require(details.get_attribute('open') is None,'Space failed to close')
    summary.click();destination='/'if route!='/'else'/regions/gangdong-condolence-wreath/';link=details.locator(f'nav a[href="{destination}"]').first
    require(link.count()==1,'Safe menu target missing');link.click();page.wait_for_url(origin+destination);page.wait_for_load_state('networkidle')
    page.go_back(wait_until='networkidle');require(page.url==origin+route,'Menu back failed')
    page.go_forward(wait_until='networkidle');require(page.url==origin+destination,'Menu forward failed')
    page.go_back(wait_until='networkidle');require(page.url==origin+route,'Menu second back failed')
    page.reload(wait_until='networkidle');require(details.get_attribute('open') is None,'Reload did not reset native menu')
    return {'passed':True,'mode':'native-details','clickOpenClose':True,'keyboardEnterSpace':True,'navigationBackReload':True,'navigationForward':True,'screenshot':receipt}

def internal_anchors(page,origin,route,links,output,width,height):
    rows=[]
    for index,href in enumerate(sorted(set(x for x in links if x.startswith(('/','#'))))):
        target=urlsplit(urljoin(origin+route,href));require(target.scheme=='http' and target.netloc==urlsplit(origin).netloc,'External internal-link target')
        require(target.path in ROUTES and not target.query,'Unknown internal route/query')
        # Start on a distinct document, so a real target response exists even for hash URLs.
        distinct='/'if target.path!='/'else'/regions/';go(page,origin,distinct)
        response=page.goto(target.geturl(),wait_until='networkidle');require(response and response.status==200,'Internal link HTTP')
        page.evaluate('async()=>{await document.fonts.ready;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));}')
        row={'href':href,'resolvedPath':target.path,'fragment':target.fragment,'method':'real-URL-navigation-no-DOM-mutation','passed':False}
        if target.fragment:
            loc=page.locator('[id="'+target.fragment+'"]');require(loc.count()==1,'Broken internal anchor')
            if target.fragment=='main-content':
                row['skipTargetVisible']=loc.is_visible();require(row['skipTargetVisible'],'Skip target hidden')
            else:
                # Verify first landing without corrective scroll. Tall sections are checked by their first heading.
                focus=loc.locator(':scope > h1, :scope > h2').first if loc.locator(':scope > h1, :scope > h2').count() else loc
                row['geometry']=focus.evaluate(GEOMETRY);geometry_ok(row['geometry'])
        row['screenshot']=shot(page,output,target.path,width,height,'anchor-from-'+('home'if route=='/'else route.strip('/').replace('/','--').replace('.','-'))+'-'+str(index));row['passed']=True;rows.append(row)
    require(bool(rows),'Missing internal anchor scope');go(page,origin,route);return rows

def run(source,output):
    spec=validate_spec(load(SPEC_PATH));site=verify_source(source);before=validate_build(site)
    require((output/'logs/first.manifest.json').read_bytes()==compact(before) and (output/'logs/second.manifest.json').read_bytes()==compact(before),'Two build receipts missing/different')
    runtime=load(site/'src/data/gangdong-runtime.json')
    report={'schema':'gangdong-browser-observations-v1','sourceSha':SOURCE_SHA,'sourceContentSha256':spec['sourceContentSha256'],'outputContentSha256':spec['outputContentSha256'],'controlSha':os.environ['GITHUB_SHA'],'runId':os.environ['GITHUB_RUN_ID'],'runAttempt':os.environ['GITHUB_RUN_ATTEMPT'],'actor':os.environ['GITHUB_ACTOR'],'pixelReview':'pending','publicHttpVerified':False,'playwrightVersion':version('playwright'),'browserVersion':None,'routes':[],'network':[],'console':[],'pageErrors':[],'expected404Console':[],'sourceUnchanged':False,'outputUnchanged':False,'fatalError':None,'artifactReceipts':'Pending GitHub upload-artifact step outputs and independent download/readback'}
    require(report['playwrightVersion']=='1.63.0','Unpinned Playwright')
    server=SafeServer(('127.0.0.1',0),partial(GangdongHandler,directory=str(site/'dist')))
    Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}';report['loopbackOrigin']=origin
    try:
        # HTTP-only request avoids mistaking Chromium's expected 404 console message for a JS fault.
        try:urllib.request.urlopen(origin+'/__gangdong_missing_route__/',timeout=10)
        except urllib.error.HTTPError as e:
            require(e.code==404,'Wrong missing route status');body=e.read();report['true404']={'path':'/__gangdong_missing_route__/','status':e.code,'bodySha256':digest(body),'contentType':e.headers.get('Content-Type'),'transport':'loopback-http-GET'}
        require('true404'in report,'Missing route unexpectedly succeeded')
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True);report['browserVersion']=browser.version
            try:
                for width,height in VIEWPORTS:
                    context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,locale='ko-KR',reduced_motion='reduce',service_workers='block',accept_downloads=False)
                    def guard(route):
                        r=route.request
                        if allowed_request(r.url,r.method,origin):route.continue_()
                        else:report['network'].append({'url':r.url,'method':r.method,'blocked':True});route.abort()
                    context.route('**/*',guard)
                    context.route_web_socket('**/*',lambda s:(report['network'].append({'url':s.url,'blockedWebSocket':True}),s.close()))
                    page=context.new_page()
                    def record_console(m):
                        row={'type':m.type,'text':m.text,'location':m.location}
                        if m.type=='error' and m.location.get('url')==origin+'/__gangdong_missing_route__/' and '404' in m.text and 'Failed to load resource' in m.text:report['expected404Console'].append(row)
                        else:report['console'].append(row)
                    page.on('console',record_console)
                    page.on('pageerror',lambda e:report['pageErrors'].append(str(e)))
                    page.on('response',lambda r:report['network'].append({'url':r.url,'status':r.status,'expected404':r.url==origin+'/__gangdong_missing_route__/' and r.status==404}))
                    page.on('requestfailed',lambda r:report['network'].append({'url':r.url,'failure':r.failure}))
                    page.on('download',lambda d:(_ for _ in ()).throw(AssertionError('Download forbidden')))
                    if width==320:
                        missing=page.goto(origin+'/__gangdong_missing_route__/',wait_until='networkidle');require(missing and missing.status==404,'Browser missing route status')
                        report['true404']['browserStatus']=missing.status;report['true404']['browserBodySha256']=digest(missing.body())
                        require(report['true404']['browserBodySha256']==report['true404']['bodySha256'],'Browser missing body differs from HTTP readback')
                    for route in ROUTES:
                        row={'route':route,'width':width,'height':height,'issues':[]};report['routes'].append(row)
                        try:
                            row['http']=go(page,origin,route).status;row['facts']=page.evaluate(FACTS);assert_facts(row['facts'],runtime,route,width)
                            destination='/regions/'if route=='/'else'/'
                            link=page.locator(f'a[href="{destination}"]:visible').first
                            require(link.count()==1 and link.get_attribute('onclick') is None and link.get_attribute('download') is None and link.get_attribute('target')in(None,'','_self'),'Unsafe local link')
                            link.click();page.wait_for_url(origin+destination);page.wait_for_load_state('networkidle');page.go_back(wait_until='networkidle');require(page.url==origin+route,'History route changed');page.go_forward(wait_until='networkidle');require(page.url==origin+destination,'Forward route changed');page.go_back(wait_until='networkidle');require(page.url==origin+route,'Second back route changed');page.reload(wait_until='networkidle');upstream_capture.settle(page)
                            row['safeNavigation']={'back':True,'forward':True,'reload':True};row['facts']=page.evaluate(FACTS);assert_facts(row['facts'],runtime,route,width)
                            row['fullPage']=shot(page,output,route,width,height,'full-page',True)
                            row['targets']=[]
                            for label,(selector,index) in targets_for(runtime,route).items():
                                loc=page.locator(selector).nth(index);require(loc.count()==1,'Risk target missing')
                                if label=='header':page.evaluate("scrollTo({top:0,behavior:'instant'})")
                                else:center(page,loc)
                                facts=loc.evaluate(GEOMETRY);geometry_ok(facts)
                                receipt=shot(page,output,route,width,height,label);receipt.update({'selector':selector,'index':index,'geometry':facts,'geometryPassed':True});row['targets'].append(receipt)
                            row['menu']=menu(page,origin,route,width,output,height)
                            row['keyboard']=keyboard(page,origin,route,output,width,height)
                            row['internalAnchors']=internal_anchors(page,origin,route,row['facts']['links'],output,width,height)
                        except Exception:row['issues'].append(traceback.format_exc())
                    context.close()
            finally:browser.close()
    except Exception:report['fatalError']=traceback.format_exc()
    finally:server.shutdown();server.server_close()
    try:
        verify_source(source);report['sourceUnchanged']=True;require(validate_build(site)==before,'Browser mutated output');report['outputUnchanged']=True
        report['coverage']=validate_report(report,output,runtime);report['state']='machine-checks-only-awaiting-independent-pixel-review'
    except Exception:
        report['fatalError']=(report['fatalError']or'')+traceback.format_exc();report['state']='machine-qa-failed'
    write(output/'capture-results.json',report)
    write(output/'browser-console.json',report['console']);write(output/'page-errors.json',report['pageErrors']);write(output/'network.json',report['network'])
    return 0 if report['state']=='machine-checks-only-awaiting-independent-pixel-review'else 1

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--allow-loopback-runner',action='store_true');args=parser.parse_args()
    require(args.allow_loopback_runner,'Explicit runner entry required');spec=validate_spec(load(SPEC_PATH))
    source,output=validate_environment(spec);verify_reuse() # Before importing Playwright or launching any browser.
    return run(source,output)
if __name__=='__main__':sys.exit(main())
