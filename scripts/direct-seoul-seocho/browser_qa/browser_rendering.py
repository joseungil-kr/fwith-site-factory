#!/usr/bin/env python3
"""Reviewed Seocho native render checks, adapted only for sealed artifact QA. See reuse-provenance.json."""
from functools import partial
from reused import SafeServer,SafeHandler,settle,write_json
from capture_checks import configure_context,capture_page,assert_capture_coverage
from pathlib import Path
from threading import Thread
import json,os,hashlib
from playwright.sync_api import sync_playwright

def inspect(dist,out,pages,revision,spec):
    dist=Path(dist).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    routes=['/','/regions/']+[p['url'] for p in pages]+['/404.html']
    server=SafeServer(('127.0.0.1',0),partial(SafeHandler,directory=str(dist)))
    Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
    rows=[];errors=[];network=[];console=[];page_errors=[];captures=[];browser_version=None
    try:
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(headless=True);browser_version=browser.version
            for width,height in [(320,740),(390,844),(1280,900)]:
                context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,locale='ko-KR',reduced_motion='reduce',service_workers='block',accept_downloads=False)
                configure_context(context,origin,network)
                page=context.new_page();page.set_default_timeout(20000);page.set_default_navigation_timeout(20000)
                page.on('console',lambda msg:console.append({'type':msg.type,'text':msg.text}))
                page.on('pageerror',lambda error:page_errors.append(str(error)))
                page.on('response',lambda response:network.append({'url':response.url,'status':response.status}))
                page.on('requestfailed',lambda request:network.append({'url':request.url,'failure':request.failure}))
                for route in routes:
                    response=page.goto(origin+route,wait_until='networkidle');page.locator('main').wait_for();settle(page)
                    checks=page.evaluate('''() => {
                      const faq=[...document.querySelectorAll('[data-faq-entry]')].map(el=>({
                        question:el.querySelector('[data-faq-question]').innerText.trim(),
                        answer:el.querySelector('[data-faq-answer]').innerText.trim(),
                        visible:el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}),
                        collapsed:!!el.closest('details:not([open])')
                      }));
                      const overflow=[...document.querySelectorAll('main *')].filter(el=>{
                        const r=el.getBoundingClientRect();return r.width>0&&(r.left<-.5||r.right>innerWidth+.5);
                      }).slice(0,8).map(el=>({tag:el.tagName,class:el.className,width:el.getBoundingClientRect().width}));
                      return {h1:document.querySelectorAll('h1').length,viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,
                        faq,overflow,banners:document.querySelectorAll('[data-shared-flower-banner]').length,
                        images:[...document.querySelectorAll('img')].map(el=>({src:el.getAttribute('src'),loaded:el.complete&&el.naturalWidth>0})),
                        fixedBar:!!document.querySelector('.mobile-bar')&&getComputedStyle(document.querySelector('.mobile-bar')).display!=='none'};
                    }''')
                    # Lazy images should be inspected only after scrolling through the page.
                    for image in page.locator('img').all():image.scroll_into_view_if_needed()
                    page.wait_for_timeout(150)
                    checks['images']=page.locator('img').evaluate_all('(images)=>images.map(el=>({src:el.getAttribute("src"),loaded:el.complete&&el.naturalWidth>0}))')
                    expected=next((p for p in pages if p['url']==route),{})
                    issue=[]
                    if response.status!=200:issue.append(f'Local route HTTP {response.status}')
                    if checks['h1']!=1:issue.append('H1 count differs from one')
                    if checks['scrollWidth']>width+1 or checks['overflow']:issue.append('Horizontal overflow')
                    if len(checks['faq'])!=len(expected.get('faq',[])):issue.append('FAQ count differs from source')
                    if [{k:f[k] for k in ('question','answer')} for f in checks['faq']] != [{k:f[k] for k in ('question','answer')} for f in expected.get('faq',[])]:issue.append('Visible FAQ text differs from accepted source')
                    if any(not x['visible'] or x['collapsed'] or not x['question'] or not x['answer'] for x in checks['faq']):issue.append('FAQ is empty, invisible or collapsed')
                    if any(not image['loaded'] for image in checks['images']):issue.append('Image did not load')
                    if route in ('/404.html','/regions/') and checks['banners']:issue.append('Thin/404 has shared banners')
                    # A number and its currency unit must stay on one visual line.
                    checks['priceRuns']=page.evaluate(r"""() => [...document.querySelectorAll('.hero-product strong,.product-card strong,.detail-product>span')].map(el=>{
                      const text=el.textContent;const match=text.match(/[0-9,]+원/);if(!match)return {text,valid:false};
                      const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let node,offset=0,start=null,end=null;
                      while(node=walker.nextNode()){if(start===null&&offset+node.length>match.index)start={node,offset:match.index-offset};if(offset+node.length>=match.index+match[0].length){end={node,offset:match.index+match[0].length-offset};break;}offset+=node.length;}
                      const range=document.createRange();range.setStart(start.node,start.offset);range.setEnd(end.node,end.offset);
                      const rects=[...range.getClientRects()];const lines=[...new Set(rects.map(r=>Math.round(r.top)))];return {text,valid:lines.length===1,lineTops:lines};
                    })""")
                    if any(not price['valid'] for price in checks['priceRuns']):issue.append('Amount/currency breaks across lines')
                    checks['anchors']=[]
                    for anchor in expected.get('facilityAnchors',[])+expected.get('buyerOccasionAnchors',[]):
                        baseline=page.goto(origin+'/regions/',wait_until='networkidle')
                        assert baseline is not None and baseline.status==200 and page.url==origin+'/regions/'
                        if anchor in expected.get('facilityAnchors',[]):
                            link=page.locator('[data-directory-facilities] a[href="'+anchor['href']+'"]');assert link.count()==1;link.click();page.wait_for_url(origin+anchor['href']);page.wait_for_load_state('networkidle')
                        else:
                            document=page.goto(origin+anchor['href'],wait_until='networkidle');assert document is not None and document.status==200
                        assert page.url==origin+anchor['href']
                        # Inspect native hash first landing. Do not correct its scroll or alter the DOM/CSS.
                        result=page.evaluate("""anchor=>{const nodes=document.querySelectorAll('#'+anchor.anchor);if(nodes.length!==1)return {id:anchor.anchor,count:nodes.length};const node=nodes[0],rect=node.getBoundingClientRect(),header=document.querySelector('.site-header').getBoundingClientRect(),bar=document.querySelector('.mobile-bar'),bottom=getComputedStyle(bar).display!=='none'?bar.getBoundingClientRect().top:innerHeight;return {id:anchor.anchor,count:1,tag:node.tagName,text:node.textContent,top:rect.top,bottom:rect.bottom,headerBottom:header.bottom,safeBottom:bottom,visible:rect.top>=header.bottom-1&&rect.bottom<=bottom+1};}""",anchor)
                        checks['anchors'].append(result)
                        page.screenshot(path=str(out/f'anchor-{anchor["anchor"]}-{width}.png'))
                        if result.get('count')!=1 or not result.get('visible') or result.get('text')!=anchor['heading']:issue.append('Native anchor first landing failed: '+anchor['anchor'])
                    page.goto(origin+route,wait_until='networkidle')
                    # Native Tab/Enter flow across every rendered visible link, including sticky bars.
                    page.keyboard.press('Tab')
                    skip=page.locator(':focus');checks['skipLabel']=skip.inner_text()
                    if skip.get_attribute('href')!='#main-content':issue.append('Skip link is not first keyboard target')
                    page.keyboard.press('Enter')
                    if page.evaluate('document.activeElement.id')!='main-content':issue.append('Skip target did not receive focus')
                    count=page.locator('a').evaluate_all('(links)=>links.filter(el=>el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})).length')
                    checks['keyboard']=[]
                    for number in range(count+1):
                        page.keyboard.press('Tab')
                        focus=page.evaluate("""()=>{const el=document.activeElement,r=el.getBoundingClientRect(),header=document.querySelector('.site-header'),bar=document.querySelector('.mobile-bar'),safeTop=el.closest('header')||el.classList.contains('skip-link')?0:header.getBoundingClientRect().bottom,safeBottom=el.closest('.mobile-bar')||getComputedStyle(bar).display==='none'?innerHeight:bar.getBoundingClientRect().top;const fragments=[...el.getClientRects()].filter(x=>x.width&&x.height);const hits=fragments.flatMap(b=>[.1,.5,.9].flatMap(x=>[.1,.5,.9].map(y=>{const h=document.elementFromPoint(b.left+b.width*x,b.top+b.height*y);return !!h&&(h===el||el.contains(h));})));return {tag:el.tagName,text:el.innerText,href:el.getAttribute('href'),top:r.top,bottom:r.bottom,left:r.left,right:r.right,safeTop,safeBottom,viewportWidth:innerWidth,visible:el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}),hitTests:hits};}""")
                        # BODY is a browser-cycle sentinel, never counted as a successful target.
                        if focus['tag']=='BODY':continue
                        checks['keyboard'].append(focus)
                        if len(checks['keyboard'])==1:page.screenshot(path=str(out/f'keyboard-first-{width}-{route.strip("/").replace("/","-").replace(".","-") or "home"}.png'))
                        failed=not focus['visible'] or focus['top']<focus['safeTop']-.5 or focus['bottom']>focus['safeBottom']+.5 or focus['left']<-.5 or focus['right']>width+.5 or not focus['hitTests'] or not all(focus['hitTests'])
                        if failed:
                            issue.append('Native keyboard target occluded/clipped: '+str(focus['href']))
                            page.screenshot(path=str(out/f'keyboard-{width}-{route.strip("/").replace("/","-").replace(".","-") or "home"}-{number}.png'))
                    if not checks['keyboard']:issue.append('No native keyboard targets inspected')
                    page.evaluate('scrollTo(0,document.body.scrollHeight)');page.wait_for_timeout(60)
                    checks['footer']=page.evaluate("""()=>{const bar=document.querySelector('.mobile-bar'),fixed=getComputedStyle(bar).display!=='none',bottom=fixed?bar.getBoundingClientRect().top:innerHeight;return [...document.querySelectorAll('footer a,footer strong')].map(el=>({text:el.textContent,bottom:el.getBoundingClientRect().bottom,visible:el.getBoundingClientRect().bottom<=bottom+1}));}""")
                    if any(not item['visible'] for item in checks['footer']):issue.append('Footer hidden by fixed order bar')
                    page.evaluate('scrollTo(0,0)');page.screenshot(path=str(out/((route.strip('/').replace('/','-').replace('.','-') or 'home')+f'-{width}.png')))
                    captures.append(capture_page(page,route,width,height,origin,revision,spec,out))
                    row={'route':route,'width':width,'height':height,'http':response.status,**checks,'issues':issue};rows.append(row)
                    if issue:errors.append(row)
                    if width==390 and route=='/':
                        page.evaluate('scrollTo(0,0)');page.screenshot(path=str(out/'home-mobile.png'))
                    if expected and expected==pages[0] and width in [390,1280]:
                        page.evaluate('scrollTo(0,0)');page.screenshot(path=str(out/f'detail-{width}-top.png'))
                        for index,section in enumerate(page.locator('.markdown-content').all()):section.screenshot(path=str(out/f'detail-{width}-body-{index+1}.png'))
                        if page.locator('[data-visible-faq]').count():page.locator('[data-visible-faq]').screenshot(path=str(out/f'detail-{width}-faq.png'))
                context.close()
            browser.close()
    except Exception as exc:
        write_json(out/'report.json',{'status':'blocked','scope':'Sealed artifact loopback only','error':str(exc),'checks':rows,'captures':captures,'pixelReview':'pending','publicHTTPVerified':False})
        raise
    finally:
        server.shutdown();server.server_close()
        write_json(out/'network.json',network);write_json(out/'browser-console.json',console);write_json(out/'page-errors.json',page_errors)
    assert not page_errors and not any(c['type']=='error' for c in console),'Browser console/page errors'
    assert not any(n.get('blocked') or n.get('blockedWebSocket') or n.get('failure') or n.get('status',200)>=400 for n in network),'Blocked/failed browser requests'
    coverage=assert_capture_coverage(captures,routes,out)
    report={'status':'captured-awaiting-independent-pixel-review' if not errors else 'machine-qa-failed','sourceRevision':revision,'captures':captures,'coverage':coverage,'browserVersion':browser_version,'pixelReview':'pending','publicHTTPVerified':False,'publicationAuthorized':False,'htmlSha256':{p.relative_to(dist).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dist.rglob('*.html')},'localOrigin':origin,'scope':'Local static artifact only; not public HTTP verification','checks':rows,'errors':errors}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    assert not errors,json.dumps(errors,ensure_ascii=False)
    print(f'BROWSER RENDERING QA: {len(rows)} local route/viewport checks; visible FAQs, loaded images and no horizontal overflow')
    return report
# Runner entry point is capture.py; this module is not a source/build command.
