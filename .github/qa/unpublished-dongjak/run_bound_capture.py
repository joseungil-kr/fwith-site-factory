#!/usr/bin/env python3
"""DEFERRED: unchanged native + upstream QA, then additive visible-pixel evidence.

Do not run in the present cloud workspace. Requires authorized exact-source GitHub
Actions execution; this script is preparation, not approval to save or run anything.
"""
from pathlib import Path
from functools import partial
from threading import Thread
import argparse, json, os, sys, traceback
from adapter import (HERE, SITE_PATH, ROUTES, load, validate_spec, validate_environment,
                     verify_upstream, verify_frozen_bytes, expectations,
                     validate_extra_facts, validate_not_found_facts, assert_focus, assert_footer_content, screenshot_selection, validate_supplemental_evidence, write)
import controls, capture

EXTRA_FACTS = r'''() => ({
  banners:[...document.querySelectorAll('[data-shared-flower-banner]')].map(el=>{
    const i=el.querySelector('img'),r=i.getBoundingClientRect();return {
      variant:el.dataset.sharedFlowerBanner,src:new URL(i.currentSrc||i.src).pathname,
      naturalWidth:i.naturalWidth,naturalHeight:i.naturalHeight,width:r.width,height:r.height,
      alt:i.alt,caption:el.querySelector('figcaption')?.innerText||'',figcaptionCount:el.querySelectorAll('figcaption').length};}),
  faq:[...document.querySelectorAll('[data-faq-entry]')].map(el=>({
    question:el.querySelector('[data-faq-question]').innerText.trim(),
    answer:el.querySelector('[data-faq-answer]').innerText.trim()})),
  products:[...document.querySelectorAll('.product-card[data-product-key]')].map(el=>({
    key:el.dataset.productKey,href:el.querySelector('a[data-order-product-key]').getAttribute('href'),
    priceLabel:el.querySelector('strong').innerText.trim()})),
  facilities:[...document.querySelectorAll('.markdown-content h2[id], .markdown-content h3[id]')]
    .filter(el=>['cau-hospital','boramae-hospital'].includes(el.id))
    .map(el=>({id:el.id,heading:el.innerText.trim(),tag:el.tagName})),
  guideLinks:[...document.querySelectorAll('[data-region-district] .page-card')].map(el=>el.getAttribute('href')),
  legalUnits:[...document.querySelectorAll('[data-legal-unit]')].map(el=>el.dataset.legalUnit),
  legalLinks:[...document.querySelectorAll('[data-legal-unit] a[data-candidate-id]')].map(el=>({
    unitKey:el.closest('[data-legal-unit]').dataset.legalUnit,href:el.getAttribute('href'),candidateId:el.dataset.candidateId})),
  adminRows:[...document.querySelectorAll('[data-administrative-unit]')].map(el=>({
    key:el.dataset.administrativeUnit,relations:[...el.querySelectorAll('span')].map(x=>x.textContent.trim())})),
  adminFacilityLinks:[...document.querySelectorAll('[data-administrative-unit] a')].map(el=>el.getAttribute('href'))
})'''

FOOTER_CONTENT_SELECTOR='footer > div'

RENDER_SNAPSHOT = r'''el => {
  const root=el.getBoundingClientRect();
  const css=(node,pseudo=null)=>{const c=getComputedStyle(node,pseudo);return Object.fromEntries(Array.from(c).sort().map(k=>[k,c.getPropertyValue(k)]));};
  const pseudo=(node,name)=>{const c=getComputedStyle(node,name);return c.content&&c.content!=='none'&&c.content!=='normal'?css(node,name):null;};
  const round=n=>Math.round(n*100)/100;
  return [el,...el.querySelectorAll('*')].map(node=>{
    const r=node.getBoundingClientRect();
    return {tag:node.tagName,text:node.innerText||'',visible:node.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}),
      relativeBox:{left:round(r.left-root.left),top:round(r.top-root.top),width:round(r.width),height:round(r.height)},
      css:css(node),before:pseudo(node,'::before'),after:pseudo(node,'::after'),
      image:node.tagName==='IMG'?{src:new URL(node.currentSrc||node.src).pathname,alt:node.alt,naturalWidth:node.naturalWidth,naturalHeight:node.naturalHeight,complete:node.complete}:null};
  });
}'''

FOCUS_FACTS = r'''el => {
  const r=el.getBoundingClientRect(),header=document.querySelector('.site-header'),bar=document.querySelector('.mobile-bar');
  const visible=e=>!!e&&getComputedStyle(e).display!=='none'&&e.getBoundingClientRect().height>0;
  const safeTop=visible(header)?Math.max(0,header.getBoundingClientRect().bottom):0;
  const safeBottom=visible(bar)?Math.min(innerHeight,bar.getBoundingClientRect().top):innerHeight;
  const hits=[];
  for(const fx of [.1,.5,.9])for(const fy of [.1,.5,.9]) {
    const x=r.left+r.width*fx,y=r.top+r.height*fy,hit=document.elementFromPoint(x,y);
    hits.push(!!hit&&(el===hit||el.contains(hit)));
  }
  const renderSignature=el.matches('[data-shared-flower-banner],footer > div')?JSON.stringify(__RENDER_SNAPSHOT__(el)):null;
  const shell=el.matches('footer > div')?el.parentElement:null;
  const footerContent=shell?{selector:'footer > div',shellBottom:shell.getBoundingClientRect().bottom,
    shellPaddingBottom:parseFloat(getComputedStyle(shell).paddingBottom),contentBottom:r.bottom,barTop:safeBottom,barVisible:visible(bar),
    items:[...el.children].map(child=>{const c=child.getBoundingClientRect(),points=[];
      for(const fx of [.1,.5,.9])for(const fy of [.1,.5,.9]){const hit=document.elementFromPoint(c.left+c.width*fx,c.top+c.height*fy);points.push(!!hit&&(child===hit||child.contains(hit)));}
      return {tag:child.tagName,text:child.innerText,href:child.getAttribute('href'),visible:child.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}),top:c.top,bottom:c.bottom,left:c.left,right:c.right,hitTests:points};})}:null;
  return {renderSignature,footerContent,visible:el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}),
    left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,
    safeTop,safeBottom,viewportWidth:innerWidth,viewportHeight:innerHeight,scrollY,hitTests:hits};
}'''.replace('__RENDER_SNAPSHOT__','('+RENDER_SNAPSHOT+')')


def center_in_safe_area(page, locator):
    # Scroll only. Never hide the native sticky header or CTA, rewrite CSS, or edit DOM.
    locator.evaluate(r'''el => {
      const r=el.getBoundingClientRect(),h=document.querySelector('.site-header'),b=document.querySelector('.mobile-bar');
      const visible=e=>!!e&&getComputedStyle(e).display!=='none';
      const top=visible(h)?h.getBoundingClientRect().height:0;
      const bottom=visible(b)?b.getBoundingClientRect().height:0;
      const room=innerHeight-top-bottom;
      window.scrollTo({top:scrollY+r.top-top-Math.max(8,(room-r.height)/2),behavior:'instant'});
    }''')
    page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')


def screenshot(page, output, rel):
    file=output/rel;file.parent.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(file),type='jpeg',quality=90,full_page=False,animations='disabled')
    return {'screenshot':rel,'screenshotSha256':controls.digest(file.read_bytes()),'dimensions':controls.jpeg_dimensions(file.read_bytes())}


def supplemental(source, spec, output, expected):
    from playwright.sync_api import sync_playwright
    site=source/SITE_PATH; dist=site/'dist'; before=controls.validate_build(site,spec)
    rows=[]; network=[]; console=[]; errors=[]; flow_rows=[]; fatal_error=None; coverage=None
    server=controls.SafeServer(('127.0.0.1',0),partial(controls.SafeHandler,directory=str(dist)))
    Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            try:
                for width,height in controls.VIEWPORTS:
                    context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,locale='ko-KR',reduced_motion='reduce',service_workers='block',accept_downloads=False)
                    def guard(route):
                        req=route.request
                        if controls.allowed_request(req.url,req.method,origin): route.continue_()
                        else: network.append({'url':req.url,'method':req.method,'blocked':True});route.abort()
                    context.route('**/*',guard)
                    context.route_web_socket('**/*',lambda socket:(network.append({'url':socket.url,'blockedWebSocket':True}),socket.close()))
                    page=context.new_page()
                    page.on('console',lambda m:console.append({'type':m.type,'text':m.text}))
                    page.on('pageerror',lambda e:errors.append(str(e)))
                    page.on('response',lambda r:network.append({'url':r.url,'status':r.status}))
                    page.on('requestfailed',lambda r:network.append({'url':r.url,'failure':r.failure}))
                    for route in ROUTES:
                        assert page.goto(origin+route,wait_until='networkidle').status==200
                        capture.settle(page);validate_extra_facts(page.evaluate(EXTRA_FACTS),expected,route)
                        name='home' if route=='/' else route.strip('/').replace('/','--').replace('.','-')
                        targets=[('header','.site-header',0),('footer',FOOTER_CONTENT_SELECTOR,0)]
                        targets += [('banner-'+b['variant'],f'[data-shared-flower-banner="{b["variant"]}"]',0)for b in expected['banners']] if route not in ('/regions/','/404.html') else []
                        if route=='/':
                            targets += [('product-'+p['key'],'.product-card[data-product-key="'+p['key']+'"]',0)for p in expected['homeProducts']]
                        if route in expected['pages']:
                            detail=expected['pages'][route]
                            targets += [('faq-'+str(i),'[data-faq-entry]',i)for i in range(len(detail['faq']))]
                            targets += [('facility-'+f['anchor'],'#'+f['anchor'],0)for f in detail['facilities']]
                            targets += [('product-'+p['key'],'.product-card[data-product-key="'+p['key']+'"]',0)for p in detail['products']]
                        if route=='/regions/':
                            summary=page.locator('details:has([data-administrative-unit]) > summary')
                            assert summary.count()==1
                            details=page.locator('details:has([data-administrative-unit])')
                            assert not details.evaluate('(el)=>el.open')
                            for desired in (True,False,True):
                                summary.click();assert details.evaluate('(el)=>el.open') is desired
                            flow_rows.append({'width':width,'flow':'admin-open-close-reopen','passed':True})
                            validate_extra_facts(page.evaluate(EXTRA_FACTS),expected,route)
                            targets += [('legal-'+str(i),'[data-legal-unit]',i)for i in range(9)]
                            targets += [('admin-'+str(i),'[data-administrative-unit]',i)for i in range(15)]
                        current_rows=[]
                        for label,selector,index in targets:
                            row={'route':route,'width':width,'height':height,'label':label,'selector':selector,'index':index,'issues':[]}
                            loc=page.locator(selector).nth(index)
                            try:
                                assert loc.count()==1,'Missing focus target'
                                # Header itself defines safeTop and is intentionally outside the content band.
                                if label=='header':
                                    page.evaluate("scrollTo({top:0,behavior:'instant'})")
                                    row['facts']=loc.evaluate(FOCUS_FACTS)
                                    assert row['facts']['visible'] and all(row['facts']['hitTests'])
                                else:
                                    center_in_safe_area(page,loc);row['facts']=loc.evaluate(FOCUS_FACTS)
                                    (assert_footer_content if label=='footer' else assert_focus)(row['facts'])
                            except Exception:row['issues'].append(traceback.format_exc())
                            rows.append(row);current_rows.append(row)
                        selection=screenshot_selection(rows)
                        for row in current_rows:
                            key=(row['width'],row['route'],row['label'])
                            row['screenshotReasons']=selection.get(key,[])
                            if not row['screenshotReasons']:
                                row['screenshotDisposition']='Geometry checked; full-page image and representative shared-component/row capture cover repeated pixels.'
                                continue
                            loc=page.locator(row['selector']).nth(row['index'])
                            if row['label']=='header':page.evaluate("scrollTo({top:0,behavior:'instant'})")
                            else:center_in_safe_area(page,loc)
                            row['captureFacts']=loc.evaluate(FOCUS_FACTS)
                            try:
                                if row['label']!='header':(assert_footer_content if row['label']=='footer' else assert_focus)(row['captureFacts'])
                            except Exception:row['issues'].append(traceback.format_exc())
                            row.update(screenshot(page,output,f'supplemental/{width}/{name}/{row["label"]}.jpg'))
                        if route=='/regions/':
                            # Test real first landing, before centering, with the original frozen CSS unchanged. Preserve any obstruction as failure.
                            for link in expected['legalLinks']:
                                flow={'width':width,'flow':'legal-facility-anchor-first-landing','href':link['href'],'issues':[]}
                                try:
                                    assert page.goto(origin+'/regions/',wait_until='networkidle').status==200
                                    target=page.locator('[data-legal-unit] a[data-candidate-id="'+link['candidateId']+'"]')
                                    target.click();page.wait_for_url(origin+link['href']);page.wait_for_load_state('networkidle')
                                    # Decode assets without resetting anchor scroll position.
                                    page.evaluate('async()=>{await document.fonts.ready;await Promise.all([...document.images].filter(i=>i.complete).map(i=>i.decode()));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));}')
                                    loc=page.locator('#'+link['href'].split('#')[1]);flow['facts']=loc.evaluate(FOCUS_FACTS)
                                    assert_focus(flow['facts'])
                                except Exception:flow['issues'].append(traceback.format_exc())
                                flow.update(screenshot(page,output,f'supplemental/{width}/anchor-first-landing/{link["candidateId"]}.jpg'))
                                flow_rows.append(flow)
                    context.close()
            finally:browser.close()
    except Exception: fatal_error=traceback.format_exc()
    finally:server.shutdown();server.server_close()
    try:
        verify_frozen_bytes(source,allow_generated=True);controls.verify_source(source,spec)
        assert controls.validate_build(site,spec)==before,'Built bytes changed during supplemental capture'
        coverage=validate_supplemental_evidence(rows,flow_rows,expected,output)
    except Exception: fatal_error=(fatal_error or '')+traceback.format_exc()
    # Give omitted duplicate views explicit evidence references, not a bare skip.
    for row in rows:
        if 'screenshot' in row:continue
        name='home' if row['route']=='/' else row['route'].strip('/').replace('/','--').replace('.','-')
        refs=[f'screenshots/{row["width"]}/{name}.jpg']
        label=row['label'];facts=row.get('facts',{})
        if label.startswith('banner-') or label=='footer':
            refs += [other['screenshot']for other in rows if 'screenshot'in other and other['width']==row['width'] and other['label']==label and other.get('facts',{}).get('renderSignature')==facts.get('renderSignature') and round(other.get('facts',{}).get('width',0),2)==round(facts.get('width',0),2) and round(other.get('facts',{}).get('height',0),2)==round(facts.get('height',0),2)]
        if label.startswith(('legal-','admin-')):
            prefix=label.split('-')[0]+'-'
            refs += [other['screenshot']for other in rows if 'screenshot'in other and other['width']==row['width'] and other['route']==row['route'] and other['label'].startswith(prefix)]
        if label.startswith('facility-'):
            refs += [f'supplemental/{row["width"]}/anchor-first-landing/{label.removeprefix("facility-")}.jpg']
        row['screenReferences']=refs
    bad_network=[n for n in network if n.get('blocked') or n.get('blockedWebSocket') or n.get('failure') or n.get('status',200)>=400]
    passed=not fatal_error and not any(r['issues'] for r in rows) and not any(r.get('issues') for r in flow_rows) and not bad_network and not errors and not any(c['type']=='error' for c in console)
    result={'state':'captured-awaiting-independent-pixel-review' if passed else 'supplemental-machine-qa-failed',
            'machineChecksPassed':passed,'sourceSha':spec['sourceSha'],'controlSha':os.environ['GITHUB_SHA'],'runId':os.environ['GITHUB_RUN_ID'],
            'fatalError':fatal_error,'coverage':coverage,'rows':rows,'flows':flow_rows,'network':network,'console':console,'pageErrors':errors,'pixelReview':'pending','publicHttpVerified':False}
    # Image bytes are pinned, but rendered phone legibility requires an independent
    # pixel review of each of the three banners at 320, 390 and 1280 pixels.
    phone_shots=[{k:r[k]for k in ('width','height','route','label','screenshot','screenshotSha256','dimensions')}for r in rows if r['label'].startswith('banner-') and 'screenshot' in r]
    write(output/'banner-phone-pixel-review.json',{'status':'pending-independent-pixel-review','expectedPhoneText':'1844-0644','requiredWidthVariantPairs':9,'sourceSha':spec['sourceSha'],'controlSha':os.environ['GITHUB_SHA'],'imageAssets':expected['banners'],'screenshots':phone_shots,'pixelReviewPassed':False,'publicHttpVerified':False})
    write(output/'supplemental-results.json',result);return passed


# The immutable upstream helper assumes a storefront anchor on every page.
# Dongjak's approved 404 instead has a strictly source-bound guide/phone/home
# contract. Never alter DOM/facts or suppress any other assertion.
ORIGINAL_ASSERT_FACTS=capture.assert_facts

def assert_bound_facts(facts, specification, route, faq, width, expected):
    if route=='/404.html':validate_not_found_facts(facts,expected)
    try:
        ORIGINAL_ASSERT_FACTS(facts,specification,route,faq,width)
    except AssertionError as error:
        if route!='/404.html' or error.args!=('CTA order href',):raise
        # Exact source anchor equality above forbids storefront/external anchors.
        # Upstream's only assertion after order href must still execute here.
        assert facts['fontStatus']=='loaded', 'Fonts incomplete'
    validate_extra_facts(facts['extra'],expected,route)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding',type=Path,required=True)
    parser.add_argument('--allow-loopback-runner',action='store_true')
    args=parser.parse_args()
    assert args.allow_loopback_runner and os.environ.get('GITHUB_ACTIONS')=='true','Deferred authorized GitHub runner only; local browser prohibited'
    verify_upstream();spec=validate_spec(load(args.binding));validate_environment(spec)
    source=Path(os.environ['SOURCE_ROOT']).resolve();output=Path(os.environ['EVIDENCE_ROOT']).resolve()
    verify_frozen_bytes(source,allow_generated=True);expected=expectations(source/SITE_PATH)
    # Add checks without altering original on-disk scripts or removing any original assertion.
    capture.FACTS='() => ({...('+capture.FACTS+')(),extra:('+EXTRA_FACTS+')()})'
    def assert_all(facts,specification,route,faq,width):
        assert_bound_facts(facts,specification,route,faq,width,expected)
    capture.assert_facts=assert_all
    def only_bound_site(key):
        assert key=='dongjak','Unexpected execution scope';return spec
    capture.spec_for=only_bound_site
    sys.argv=[sys.argv[0],'dongjak']
    native_exit=capture.main()
    supplement_pass=supplemental(source,spec,output,expected)
    write(output/'combined-verdict.json',{'status':'machine-checks-only-awaiting-independent-pixel-review' if native_exit==0 and supplement_pass else 'failed',
        'nativeExit':native_exit,'supplementalMachinePass':supplement_pass,'sourceSha':spec['sourceSha'],
        'pixelReview':'pending','publicationAuthorization':'not-issued','publicHttpVerified':False})
    return 0 if native_exit==0 and supplement_pass else 1

if __name__=='__main__':sys.exit(main())
