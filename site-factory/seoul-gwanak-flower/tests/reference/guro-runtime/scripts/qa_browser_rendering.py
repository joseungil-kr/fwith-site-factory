#!/usr/bin/env python3
"""Optional local Chromium read-only visual gate, separate from deployment verification."""
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
                    row={'route':route,'width':width,'height':height,'http':response.status,**checks,'issues':issue};rows.append(row)
                    if issue:errors.append(row)
                    if width==390 and route=='/':
                        page.evaluate('scrollTo(0,0)');page.screenshot(path=str(out/'home-mobile.png'))
                    if expected and expected==pages[0] and width in [390,1280]:
                        page.evaluate('scrollTo(0,0)');page.screenshot(path=str(out/f'detail-{width}-top.png'))
                        if page.locator('.markdown-content').count():page.locator('.markdown-content').screenshot(path=str(out/f'detail-{width}-body.png'))
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
