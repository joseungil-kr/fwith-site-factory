#!/usr/bin/env python3
"""Deferred Gwanak browser QA for an authorized browser executor. Not executed in the current LOCAL task."""
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
import json,os
from playwright.sync_api import sync_playwright

def inspect(root=Path('.')):
    root=root.resolve();dist=root/'dist';out=root/'browser-rendering-qa';out.mkdir(exist_ok=True)
    pages=json.loads((root/'src/data/pages.json').read_text())
    routes=['/','/regions/']+[p['url'] for p in pages]+['/404.html']
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(dist)))
    Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
    rows=[];errors=[]
    try:
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True)
            for width,height in [(320,740),(390,844),(1280,900)]:
                context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1)
                page=context.new_page()
                for route in routes:
                    response=page.goto(origin+route,wait_until='networkidle');page.locator('main').wait_for()
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
                    if any(not x['visible'] or x['collapsed'] or not x['question'] or not x['answer'] for x in checks['faq']):issue.append('FAQ is empty, invisible or collapsed')
                    if any(not image['loaded'] for image in checks['images']):issue.append('Image did not load')
                    if route=='/404.html' and checks['banners']:issue.append('404 has shared banners')
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
                        result=page.evaluate("""anchor=>{const nodes=document.querySelectorAll('#'+anchor.anchor);if(nodes.length!==1)return {id:anchor.anchor,count:nodes.length};const node=nodes[0];node.scrollIntoView({block:'start'});const rect=node.getBoundingClientRect();const header=document.querySelector('.site-header').getBoundingClientRect();return {id:anchor.anchor,count:1,tag:node.tagName,text:node.textContent,top:rect.top,headerBottom:header.bottom,visible:rect.top>=header.bottom-1};}""",anchor)
                        checks['anchors'].append(result)
                        if result.get('count')!=1 or not result.get('visible') or result.get('text')!=anchor['heading']:issue.append('Anchor missing, wrong, or hidden by sticky header: '+anchor['anchor'])
                    page.evaluate('scrollTo(0,document.body.scrollHeight)');page.wait_for_timeout(60)
                    checks['footer']=page.evaluate("""()=>{const bar=document.querySelector('.mobile-bar'),fixed=getComputedStyle(bar).display!=='none',bottom=fixed?bar.getBoundingClientRect().top:innerHeight;return [...document.querySelectorAll('footer a,footer strong')].map(el=>({text:el.textContent,bottom:el.getBoundingClientRect().bottom,visible:el.getBoundingClientRect().bottom<=bottom+1}));}""")
                    if any(not item['visible'] for item in checks['footer']):issue.append('Footer hidden by fixed order bar')
                    page.evaluate('scrollTo(0,0)');page.screenshot(path=str(out/((route.strip('/').replace('/','-').replace('.','-') or 'home')+f'-{width}.png')))
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
        (out/'report.json').write_text(json.dumps({'status':'blocked','scope':'Local static artifact only; not public HTTP verification','error':str(exc),'checks':rows},ensure_ascii=False,indent=2)+'\n')
        raise
    finally:server.shutdown()
    report={'localOrigin':origin,'scope':'Local static artifact only; not public HTTP verification','checks':rows,'errors':errors}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    assert not errors,json.dumps(errors,ensure_ascii=False)
    print(f'BROWSER RENDERING QA: {len(rows)} local route/viewport checks; visible FAQs, loaded images and no horizontal overflow')
    return report
if __name__=='__main__':inspect()
