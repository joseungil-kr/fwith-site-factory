"""Preserve native QA, then capture every route/viewport on runner loopback only.
Reuse: Suwon 7da50ec9ffbad8c83916fdeffaaaf2cfa5f55756 request blocking,
image.decode(), instant scroll and two-frame paint settling. No public navigation.
"""
from pathlib import Path
from functools import partial
from threading import Thread
from unittest.mock import patch
from importlib.metadata import version
import importlib.util, json, os, shutil, sys, traceback
from controls import (BRANCH, VIEWPORTS, SafeHandler, SafeServer, allowed_request,
    spec_for, verify_source, validate_build, digest, compact, run_binding, write_json, jpeg_dimensions, validate_branch, validate_capture_evidence)


def settle(page):
    page.evaluate('() => document.fonts.ready')
    for image in page.locator('img').all(): image.scroll_into_view_if_needed()
    page.wait_for_function('() => [...document.images].every(i => i.complete && i.naturalWidth > 0)')
    page.evaluate('''async () => {
      await Promise.all([...document.images].map(i => i.decode()));
      window.scrollTo({top:0,left:0,behavior:'instant'});
      await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
    }''')
    page.wait_for_function('() => scrollX === 0 && scrollY === 0')

FACTS = '''() => ({
 url:location.href,scrollX,scrollY,viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,
 h1:[...document.querySelectorAll('h1')].map(e=>e.textContent.trim()),
 robots:document.querySelector('meta[name="robots"]')?.content,
 canonical:document.querySelector('link[rel="canonical"]')?.href || null,
 revision:document.querySelector('meta[name="site-factory-revision"]')?.content,
 faq:[...document.querySelectorAll('[data-faq-entry]')].map(el=>({
   question:el.querySelector('[data-faq-question]').innerText.trim(),
   answer:el.querySelector('[data-faq-answer]').innerText.trim(),
   visible:el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}),
   collapsed:!!el.closest('details:not([open])')})),
 overflow:[...document.querySelectorAll('main *')].filter(el=>{
   const r=el.getBoundingClientRect();return r.width>0&&(r.left<-.5||r.right>innerWidth+.5);
 }).slice(0,8).map(el=>({tag:el.tagName,class:el.className,width:el.getBoundingClientRect().width})),
 images:[...document.images].map(i=>({src:new URL(i.currentSrc||i.src).pathname,alt:i.alt,
   complete:i.complete,width:i.naturalWidth,height:i.naturalHeight,
   displayWidth:i.getBoundingClientRect().width,displayHeight:i.getBoundingClientRect().height})),
 anchors:[...document.querySelectorAll('a[href]')].map(a=>({href:a.getAttribute('href'),text:a.textContent.trim()})),
 banners:document.querySelectorAll('[data-shared-flower-banner]').length,
 fixedBar:!!document.querySelector('.mobile-bar')&&getComputedStyle(document.querySelector('.mobile-bar')).display!=='none',
 bodyFont:getComputedStyle(document.body).fontFamily,
 fontStatus:document.fonts.status
})'''

def assert_facts(facts, spec, route, expected_faq, width):
    assert len(facts['h1'])==1 and facts['h1'][0], 'H1 count/text'
    assert facts['viewport']==width and facts['scrollWidth']<=width+1 and not facts['overflow'], 'Horizontal overflow'
    assert len(facts['faq'])==len(expected_faq), 'FAQ count differs from source'
    assert all(x['visible'] and not x['collapsed'] and x['question'] and x['answer'] for x in facts['faq']), 'FAQ empty/invisible/collapsed'
    assert all(i['complete'] and i['width']>0 and i['height']>0 and i['alt'].strip() for i in facts['images']), 'Image decode/alt'
    assert facts['revision']==spec['sourceSha'], 'Incorrect source revision'
    assert facts['canonical']==(None if route=='/404.html' else spec['siteUrl']+route), 'Canonical'
    robots='index,follow' if spec['indexable'] and route!='/404.html' else 'noindex,nofollow,noarchive'
    assert facts['robots']==robots, 'Robots'
    if route=='/404.html': assert facts['banners']==0, '404 banners'
    phones=[a['href'] for a in facts['anchors'] if a['href'].startswith('tel:')]
    orders=[a['href'] for a in facts['anchors'] if a['href'].startswith('https://fwith.co.kr')]
    assert phones and set(phones)=={'tel:18440644'}, 'CTA phone href'
    assert orders and all(h=='https://fwith.co.kr' or h.startswith('https://fwith.co.kr/') for h in orders), 'CTA order href'
    assert facts['fontStatus']=='loaded', 'Fonts incomplete'


def main():
    from playwright.sync_api import sync_playwright, Browser
    assert version('playwright')=='1.63.0', 'Unpinned Playwright'
    validate_branch(os.environ['GITHUB_REF'])
    key=sys.argv[1]; spec=spec_for(key)
    source=Path(os.environ['SOURCE_ROOT']).resolve(); site=verify_source(source,spec)
    output=Path(os.environ['EVIDENCE_ROOT']).resolve(); output.mkdir(parents=True,exist_ok=True)
    files=validate_build(site,spec); binding=run_binding(spec,files)
    assert (output/'logs/first.manifest.json').read_bytes()==compact(files)
    assert (output/'logs/second.manifest.json').read_bytes()==compact(files)
    pages=json.loads((site/'src/data/pages.json').read_text())
    network=[]; console=[]; page_errors=[]; results=[]; active_origin=[None]
    native_error=None; fatal_error=None; server=None; browser_version=None
    original_context=Browser.new_context
    def guarded_context(browser,*args,**kwargs):
        kwargs['service_workers']='block'; kwargs['accept_downloads']=False
        context=original_context(browser,*args,**kwargs)
        def guard(route):
            request=route.request
            if not allowed_request(request.url,request.method,active_origin[0]):
                network.append({'url':request.url,'method':request.method,'blocked':True}); route.abort()
            else: route.continue_()
        context.route('**/*',guard)
        context.route_web_socket('**/*',lambda socket: (network.append({'url':socket.url,'blockedWebSocket':True}),socket.close()))
        context.on('page',lambda page: (
            page.on('console',lambda msg: console.append({'url':page.url,'type':msg.type,'text':msg.text})),
            page.on('pageerror',lambda error: page_errors.append({'url':page.url,'error':str(error)})),
            page.on('response',lambda response: network.append({'url':response.url,'status':response.status})),
            page.on('requestfailed',lambda request: network.append({'url':request.url,'failure':request.failure}))))
        return context
    def native_server(address,handler):
        server=SafeServer(address,handler); active_origin[0]=f'http://127.0.0.1:{server.server_port}'; return server
    # Import and execute the immutable native script. Patches only restrict I/O;
    # native route list, viewport sizes, assertions and report remain unchanged.
    native_path=site/'scripts/qa_browser_rendering.py'
    loader=importlib.util.spec_from_file_location('immutable_native_qa',native_path)
    native=importlib.util.module_from_spec(loader); loader.loader.exec_module(native)
    with patch.object(Browser,'new_context',guarded_context):
        try:
            with sync_playwright() as playwright:
                os.environ['CHROMIUM_PATH']=playwright.chromium.executable_path
            with patch.object(native,'ThreadingHTTPServer',native_server),patch.object(native,'SimpleHTTPRequestHandler',SafeHandler):
                native.inspect(site)
        except Exception:
            native_error=traceback.format_exc()
        finally:
            native_output=site/'browser-rendering-qa'
            if native_output.exists(): shutil.copytree(native_output,output/'native',dirs_exist_ok=True)
        try:
            server=SafeServer(('127.0.0.1',0),partial(SafeHandler,directory=str(site/'dist')))
            Thread(target=server.serve_forever,daemon=True).start()
            origin=f'http://127.0.0.1:{server.server_port}'; active_origin[0]=origin
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch(headless=True)
                browser_version=browser.version
                try:
                    for width,height in VIEWPORTS:
                        context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,locale='ko-KR',reduced_motion='reduce')
                        page=context.new_page()
                        for route in spec['routes']:
                            row={'route':route,'width':width,'height':height,'issues':[]}
                            expected=next((p for p in pages if p['url']==route),{})
                            try:
                                response=page.goto(origin+route,wait_until='networkidle'); assert response.status==200
                                page.locator('main').wait_for(); settle(page)
                                facts=page.evaluate(FACTS); row['facts']=facts
                                assert_facts(facts,spec,route,expected.get('faq',[]),width)
                                destination='/regions/' if route=='/' else '/'
                                link=page.locator(f'a[href="{destination}"]:visible').first
                                assert link.count()==1 and link.get_attribute('onclick') is None and link.get_attribute('download') is None, 'Unsafe navigation link'
                                assert link.get_attribute('target') in (None,'','_self'), 'External browsing context'
                                link.click(); page.wait_for_url(origin+destination); page.wait_for_load_state('networkidle')
                                page.go_back(wait_until='networkidle'); page.wait_for_url(origin+route)
                                page.reload(wait_until='networkidle'); settle(page)
                                assert page.url==origin+route, 'Wrong history/reload destination'
                                facts=page.evaluate(FACTS); row['postNavigationFacts']=facts
                                assert_facts(facts,spec,route,expected.get('faq',[]),width)
                                row['safeNavigation']={'destination':destination,'back':True,'reload':True,'ctaHrefsInspectedOnly':True}
                            except Exception: row['issues'].append(traceback.format_exc())
                            try:
                                assert page.url==origin+route, 'Capture at wrong route'
                                settle(page)
                                name='home' if route=='/' else route.strip('/').replace('/','--').replace('.','-')
                                rel=f'screenshots/{width}/{name}.jpg'; file=output/rel; file.parent.mkdir(parents=True,exist_ok=True)
                                row['finalScreenshotFacts']=page.evaluate(FACTS)
                                page.screenshot(path=str(file),type='jpeg',quality=85,full_page=True,animations='disabled')
                                row['screenshot']=rel; row['screenshotSha256']=digest(file.read_bytes())
                                row['screenshotDimensions']=jpeg_dimensions(file.read_bytes())
                                assert row['screenshotDimensions']['width']==width and row['screenshotDimensions']['height']>=height, 'Screenshot dimensions'
                                row['imageReadiness']='decode-completed-and-two-paint-frames-awaited'
                            except Exception: row['issues'].append('Screenshot: '+traceback.format_exc())
                            results.append(row)
                        context.close()
                finally: browser.close()
        except Exception: fatal_error=traceback.format_exc()
        finally:
            if server: server.shutdown();server.server_close()
    # Ensure captured build and source controls were not changed by browser work.
    try:
        verify_source(source,spec)
        assert validate_build(site,spec)==files, 'Artifact changed during capture'
        validate_capture_evidence(results,spec,output)
    except Exception: fatal_error=(fatal_error or '')+traceback.format_exc()
    native_report=json.loads((output/'native/report.json').read_text()) if (output/'native/report.json').exists() else None
    native_grid=[(x['route'],x['width'],x['height']) for x in (native_report or {}).get('checks',[])]
    expected_grid=[(route,w,h) for w,h in VIEWPORTS for route in spec['routes']]
    passed=(not native_error and not fatal_error and native_grid==expected_grid and
            native_report is not None and not native_report.get('errors') and len(results)==len(expected_grid) and
            [(r['route'],r['width'],r['height']) for r in results]==expected_grid and
            len({r.get('screenshot') for r in results})==len(expected_grid) and
            all(not r['issues'] and r.get('screenshotSha256') for r in results) and not page_errors and
            all(not r.get('blocked') and not r.get('blockedWebSocket') and not r.get('failure') and r.get('status',200)<400 for r in network) and
            not [r for r in console if r['type']=='error'])
    summary={**binding,'state':'captured-awaiting-independent-pixel-review' if passed else 'machine-qa-failed',
             'machineChecksPassed':bool(passed),'nativeError':native_error,'fatalError':fatal_error,'nativeGrid':native_grid,
             'expectedGrid':expected_grid,'resultCount':len(results),'results':results,
             'publicHttpVerified':False,'productionApprovalVerified':False,'playwrightVersion':version('playwright'),'browserVersion':browser_version}
    write_json(output/'capture-results.json',summary)
    write_json(output/'browser-console.json',console);write_json(output/'page-errors.json',page_errors);write_json(output/'network.json',network)
    print(json.dumps({'key':key,'machineChecksPassed':bool(passed),'captures':len(results),'pixelReview':'pending','publicHttpVerified':False}))
    return 0 if passed else 1

if __name__=='__main__': sys.exit(main())
