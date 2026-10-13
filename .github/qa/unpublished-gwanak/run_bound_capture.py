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
from adapter import bound_verify_source, assert_keyboard_focus, validate_bound_build

EXTRA_FACTS = r'''() => {
 const text=e=>e?.innerText.trim()||'';
 const anchor=e=>({href:e.getAttribute('href'),text:e.textContent.trim()});
 const ids=xs=>[...document.querySelectorAll('.markdown-content h2[id],.markdown-content h3[id]')].filter(e=>xs.includes(e.id)).map(e=>({id:e.id,heading:text(e),tag:e.tagName,count:document.querySelectorAll('#'+e.id).length}));
 return {
 duplicateIds:[...new Set([...document.querySelectorAll('[id]')].map(e=>e.id))].filter(id=>document.querySelectorAll('#'+CSS.escape(id)).length>1),
 social:{ogTitle:document.querySelector('meta[property="og:title"]')?.content,ogDescription:document.querySelector('meta[property="og:description"]')?.content,twitterTitle:document.querySelector('meta[name="twitter:title"]')?.content,twitterDescription:document.querySelector('meta[name="twitter:description"]')?.content,ogImage:document.querySelector('meta[property="og:image"]')?.content,twitterImage:document.querySelector('meta[name="twitter:image"]')?.content,ogAlt:document.querySelector('meta[property="og:image:alt"]')?.content,twitterAlt:document.querySelector('meta[name="twitter:image:alt"]')?.content,ogWidth:document.querySelector('meta[property="og:image:width"]')?.content,ogHeight:document.querySelector('meta[property="og:image:height"]')?.content},
 title:document.title,description:document.querySelector('meta[name="description"]')?.content,
 h1:[...document.querySelectorAll('h1')].map(text),schema:[...document.querySelectorAll('script[type="application/ld+json"]')].map(e=>JSON.parse(e.textContent)),
 firstAnswer:text(document.querySelector('.detail-hero>div>p')),
 sections:[...document.querySelectorAll('[data-approved-section]')].map(e=>({id:e.dataset.approvedSection,heading:text(e.querySelector('h2')),paragraphs:[...e.querySelectorAll(':scope>p')].map(text)})),
 banners:[...document.querySelectorAll('[data-shared-flower-banner]')].map(el=>{const i=el.querySelector('img'),r=i.getBoundingClientRect();return{variant:el.dataset.sharedFlowerBanner,src:new URL(i.currentSrc||i.src).pathname,naturalWidth:i.naturalWidth,naturalHeight:i.naturalHeight,width:r.width,height:r.height,alt:i.alt,caption:text(el.querySelector('figcaption'))};}),
 faq:[...document.querySelectorAll('[data-faq-entry]')].map(el=>({question:text(el.querySelector('[data-faq-question]')),answer:text(el.querySelector('[data-faq-answer]'))})),
 products:[...document.querySelectorAll('.product-card[data-product-key]')].map(el=>({key:el.dataset.productKey,sku:el.dataset.productSku,href:el.querySelector('a[data-order-product-key]').getAttribute('href'),priceLabel:text(el.querySelector('strong')),name:text(el.querySelector('h3')),description:text(el.querySelector('div>p')),image:new URL(el.querySelector('img').currentSrc||el.querySelector('img').src).pathname,alt:el.querySelector('img').alt,caption:text(el.querySelector('.product-notice')),cta:text(el.querySelector('a'))})),
 productImages:[...document.querySelectorAll('.hero-product img,.detail-product img,.product-card img')].map(i=>({src:new URL(i.currentSrc||i.src).pathname,alt:i.alt,width:i.naturalWidth,height:i.naturalHeight})),
 priceRuns:[...document.querySelectorAll('.hero-product strong,.product-card strong,.detail-product>span')].map(el=>{const text=el.textContent,m=text.match(/[0-9,]+원/);if(!m)return{text,valid:false};const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let n,offset=0,start=null,end=null;while(n=w.nextNode()){if(start===null&&offset+n.length>m.index)start={node:n,offset:m.index-offset};if(offset+n.length>=m.index+m[0].length){end={node:n,offset:m.index+m[0].length-offset};break;}offset+=n.length;}if(!start||!end)return{text,valid:false};const range=document.createRange();range.setStart(start.node,start.offset);range.setEnd(end.node,end.offset);const rects=[...range.getClientRects()];const tops=[...new Set(rects.map(r=>Math.round(r.top)))];return{text,valid:tops.length===1,lineTops:tops};}),
 facilities:ids(['wooshin-funeral','snu-faculty','snu-research-park','nakseongdae-traditional']),occasions:ids(['opening-occasion']),
 guideCards:[...document.querySelectorAll('.page-card')].map(e=>({href:e.getAttribute('href'),title:text(e.querySelector('strong')),summary:text(e.querySelector('span')),ctaLabel:text(e.querySelector('em'))})),
 legalUnits:[...document.querySelectorAll('[data-legal-unit]')].map(e=>e.dataset.legalUnit),
 legalLinks:[...document.querySelectorAll('[data-facility-legal-unit] a[data-candidate-id]')].map(e=>({unitKey:e.closest('[data-facility-legal-unit]').dataset.facilityLegalUnit,href:e.getAttribute('href'),candidateId:e.dataset.candidateId})),
 unassignedLinks:[...document.querySelectorAll('[data-district-unassigned] a[data-candidate-id]')].map(e=>({href:e.getAttribute('href'),candidateId:e.dataset.candidateId})),
 adminRows:[...document.querySelectorAll('[data-administrative-unit]')].map(e=>({key:e.dataset.administrativeUnit,code:e.dataset.administrativeCode,name:text(e),unitKey:e.closest('[data-legal-unit]')?.dataset.legalUnit})),
 adminFacilityLinks:[...document.querySelectorAll('[data-administrative-unit] a')].map(e=>e.getAttribute('href')),
 sources:[...document.querySelectorAll('.source-references .source-card a')].map(e=>({name:text(e),url:e.getAttribute('href')})),sourceNote:text(document.querySelector('.source-references>p')),
 relatedLink:document.querySelector('[data-related-link]')?{intro:text(document.querySelector('[data-related-link]>p')),href:document.querySelector('[data-related-link]>a').getAttribute('href'),label:text(document.querySelector('[data-related-link]>a'))}:null,
 footer:{brand:text(document.querySelector('footer strong')),anchors:[...document.querySelectorAll('footer a')].map(anchor)}
 };
}
'''

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


def keyboard_flow(page,origin,route,width,output):
 flow={'width':width,'route':route,'flow':'keyboard-tab-focus','passed':False,'issues':[],'targets':[]}
 try:
  assert page.goto(origin+route,wait_until='networkidle').status==200
  capture.settle(page)
  count=page.evaluate("()=>[...document.querySelectorAll('a[href],button,input,select,textarea,summary,[tabindex]')].filter(e=>e.tabIndex>=0&&getComputedStyle(e).display!=='none'&&getComputedStyle(e).visibility!=='hidden'&&e.getClientRects().length>0).length")
  assert 1<count<200,'Unexpected focus scope'
  for index in range(count):
   page.keyboard.press('Tab');page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
   fact=page.evaluate(r"""()=>{
    const e=document.activeElement,r=e.getBoundingClientRect(),c=getComputedStyle(e),header=document.querySelector('.site-header'),bar=document.querySelector('.mobile-bar');
    const visible=x=>!!x&&getComputedStyle(x).display!=='none'&&x.getBoundingClientRect().height>0;
    let region='content',safeTop=visible(header)?Math.max(0,header.getBoundingClientRect().bottom):0,safeBottom=visible(bar)?Math.min(innerHeight,bar.getBoundingClientRect().top):innerHeight;
    if(e.matches('body > a.skip-link[href="#main-content"]')){region='skip';safeTop=0;safeBottom=innerHeight;}
    else if(header?.contains(e)){region='header';safeTop=Math.max(0,header.getBoundingClientRect().top);safeBottom=Math.min(innerHeight,header.getBoundingClientRect().bottom);}
    else if(visible(bar)&&bar.contains(e)){region='mobile-bar';safeTop=Math.max(0,bar.getBoundingClientRect().top);safeBottom=Math.min(innerHeight,bar.getBoundingClientRect().bottom);}
    const fragments=[...e.getClientRects()].filter(x=>x.width>0&&x.height>0),hitTests=[];
    for(const box of fragments)for(const fx of [.1,.5,.9])for(const fy of [.1,.5,.9]){const hit=document.elementFromPoint(box.left+box.width*fx,box.top+box.height*fy);hitTests.push(!!hit&&(hit===e||e.contains(hit)));}
    return {domIndex:[...document.querySelectorAll('a[href],button,input,select,textarea,summary,[tabindex]')].indexOf(e),tag:e.tagName,href:e.getAttribute('href'),text:e.textContent.trim(),visible:e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}),left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,region,safeTop,safeBottom,fragmentCount:fragments.length,hitTests,focusVisible:e.matches(':focus-visible'),outlineWidth:parseFloat(c.outlineWidth),outlineStyle:c.outlineStyle,viewportWidth:innerWidth,viewportHeight:innerHeight};
   }""")
   flow['targets'].append(fact)
   assert_keyboard_focus(fact)
  assert len({x['domIndex']for x in flow['targets']})==count,'Tab key skipped or repeated a target'
  flow['passed']=True
 except Exception:flow['issues'].append(traceback.format_exc())
 try:
  name='home'if route=='/'else route.strip('/').replace('/','--').replace('.','-')
  flow.update(screenshot(page,output,f'supplemental/{width}/{name}/keyboard-final-focus.jpg'))
 except Exception:
  flow['passed']=False;flow['issues'].append(traceback.format_exc())
 return flow

def supplemental(source, spec, output, expected):
    from playwright.sync_api import sync_playwright
    site=source/SITE_PATH; dist=site/'dist'; before=validate_bound_build(site,spec)
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
                            targets += [('occasion-'+f['anchor'],'#'+f['anchor'],0)for f in detail['occasions']]
                            targets += [('product-'+p['key'],'.product-card[data-product-key="'+p['key']+'"]',0)for p in detail['products']]
                            targets += [('source-'+str(i),'.source-references .source-card',i)for i in range(len(detail['sources']))]
                            targets += [('heading-'+x['id'],'#'+x['id'],0)for x in detail['sections']]
                        if route=='/regions/':
                            targets += [('legal-'+str(i),'[data-legal-unit]',i)for i in range(3)]
                            targets += [('admin-'+str(i),'[data-administrative-unit]',i)for i in range(21)]
                            targets += [('district-unassigned','[data-district-unassigned]',0)]
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
                            for link in expected['anchorFlows']:
                                flow={'width':width,'flow':'anchor-first-landing','href':link['href'],'passed':False,'issues':[]}
                                try:
                                    if link['kind']=='facility':
                                        assert page.goto(origin+'/regions/',wait_until='networkidle').status==200
                                        target=page.locator(link['selector']);assert target.count()==1;target.click();page.wait_for_url(origin+link['href']);page.wait_for_load_state('networkidle')
                                    else:
                                        # No synthetic link or DOM mutation: direct hash navigation is the approved occasion URL contract.
                                        assert page.goto(origin+link['href'],wait_until='networkidle').status==200
                                    page.evaluate('async()=>{await document.fonts.ready;await Promise.all([...document.images].filter(i=>i.complete).map(i=>i.decode()));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));}')
                                    loc=page.locator('#'+link['anchor']);assert loc.count()==1;flow['facts']=loc.evaluate(FOCUS_FACTS)
                                    assert_focus(flow['facts']);flow['passed']=True
                                except Exception:flow['issues'].append(traceback.format_exc())
                                flow.update(screenshot(page,output,f'supplemental/{width}/anchor-first-landing/{link["anchor"]}.jpg'));flow_rows.append(flow)
                        flow_rows.append(keyboard_flow(page,origin,route,width,output))
                    context.close()
            finally:browser.close()
    except Exception: fatal_error=traceback.format_exc()
    finally:server.shutdown();server.server_close()
    try:
        verify_frozen_bytes(source,allow_generated=True);bound_verify_source(source,spec)
        assert validate_bound_build(site,spec)==before,'Built bytes changed during supplemental capture'
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
        if label.startswith(('facility-','occasion-')):
            refs += [f'supplemental/{row["width"]}/anchor-first-landing/{label.removeprefix("facility-").removeprefix("occasion-")}.jpg']
        row['screenReferences']=refs
    bad_network=[n for n in network if n.get('blocked') or n.get('blockedWebSocket') or n.get('failure') or n.get('status',200)>=400]
    passed=not fatal_error and not any(r['issues'] for r in rows) and not any(r.get('issues') for r in flow_rows) and not bad_network and not errors and not any(c['type']=='error' for c in console)
    result={'state':'captured-awaiting-independent-pixel-review' if passed else 'supplemental-machine-qa-failed',
            'machineChecksPassed':passed,'sourceSha':spec['sourceSha'],'controlSha':os.environ['GITHUB_SHA'],'runId':os.environ['GITHUB_RUN_ID'],
            'fatalError':fatal_error,'coverage':coverage,'rows':rows,'flows':flow_rows,'network':network,'console':console,'pageErrors':errors,'pixelReview':'pending','publicHttpVerified':False}
    write(output/'supplemental-results.json',result);return passed


# Gwanak approved tel URI includes hyphens. Exact source-bound validation precedes
# the single legacy phone-URI mismatch; order and font assertions still run on every
# route, including 404. Dongjak's missing-order exception is deliberately absent.
ORIGINAL_ASSERT_FACTS=capture.assert_facts

def assert_bound_facts(facts,spec,route,faq,width,expected):
 phones=[a['href']for a in facts['anchors']if a['href'].startswith('tel:')]
 assert phones and set(phones)=={expected['phoneHref']},'Exact approved Gwanak phone href'
 if route=='/404.html':validate_not_found_facts(facts,expected)
 try:ORIGINAL_ASSERT_FACTS(facts,spec,route,faq,width)
 except AssertionError as error:
  if error.args!=('CTA phone href',):raise
  orders=[a['href']for a in facts['anchors']if a['href'].startswith('https://fwith.co.kr')]
  assert orders and all(h=='https://fwith.co.kr'or h.startswith('https://fwith.co.kr/')for h in orders),'CTA order href'
  assert facts['fontStatus']=='loaded','Fonts incomplete'
 validate_extra_facts(facts['extra'],expected,route)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binding',type=Path,required=True);p.add_argument('--allow-loopback-runner',action='store_true');a=p.parse_args()
 assert a.allow_loopback_runner and os.environ.get('GITHUB_ACTIONS')=='true','Deferred authorized GitHub runner only; local browser prohibited'
 verify_upstream();spec=validate_spec(load(a.binding));validate_environment(spec)
 source=Path(os.environ['SOURCE_ROOT']).resolve();output=Path(os.environ['EVIDENCE_ROOT']).resolve()
 verify_frozen_bytes(source,allow_generated=True);expected=expectations(source/SITE_PATH)
 capture.FACTS='() => ({...('+capture.FACTS+')(),extra:('+EXTRA_FACTS+')()})'
 capture.verify_source=bound_verify_source
 capture.validate_build=validate_bound_build
 capture.assert_facts=lambda facts,spec,route,faq,width:assert_bound_facts(facts,spec,route,faq,width,expected)
 def only_bound_site(key):
  assert key=='gwanak','Unexpected scope';return spec
 capture.spec_for=only_bound_site;sys.argv=[sys.argv[0],'gwanak']
 native_exit=capture.main();supplement_pass=supplemental(source,spec,output,expected)
 write(output/'combined-verdict.json',{'status':'machine-checks-only-awaiting-independent-pixel-review'if native_exit==0 and supplement_pass else 'failed','nativeExit':native_exit,'supplementalMachinePass':supplement_pass,'sourceSha':spec['sourceSha'],'pixelReview':'pending','publicationAuthorization':'not-issued','publicHttpVerified':False})
 return 0 if native_exit==0 and supplement_pass else 1
if __name__=='__main__':sys.exit(main())
