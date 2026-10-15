#!/usr/bin/env python3
"""Loopback-only browser QA. Uses installed Playwright and Chromium; never submits orders."""
from pathlib import Path
import json,hashlib,datetime,urllib.request
from playwright.sync_api import sync_playwright
C=Path(__file__).resolve().parents[1];R=C.parent;E=R/'evidence/browser';E.mkdir(parents=True,exist_ok=True)
BASE='http://127.0.0.1:43817'
SPEC=json.loads((C/'src/data/frozen/content-spec.ko.json').read_text())
result={'scope':'Local Astro preview at 127.0.0.1 only. No public URL, provider routing or external order tested.','startedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'browser':'/usr/bin/chromium','widths':[320,390,1280],'pages':[],'failures':[],'blockedExternalRequests':[]}
def check(value,label):
 if not value:result['failures'].append(label)
with sync_playwright() as pw:
 # Safe prepared revision only; not executed after the socket restriction.
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,chromium_sandbox=True)
 for width in result['widths']:
  context=browser.new_context(viewport={'width':width,'height':900},device_scale_factor=1)
  def route(request):
   if request.request.url.startswith(BASE+'/'):request.continue_()
   else:result['blockedExternalRequests'].append(request.request.url);request.abort()
  context.route('**/*',route)
  page=context.new_page();console_errors=[];page.on('pageerror',lambda e:console_errors.append(str(e)))
  for data in SPEC['pages']:
   response=page.goto(BASE+data['path'],wait_until='networkidle');name=f"{data['id']}-{width}"
   check(response.status==200,f'{name}: expected direct file 200 got {response.status}')
   # Load every lazy image using normal scrolling, then inspect its actual decoded pixels and geometry.
   for img in page.locator('img').all():img.scroll_into_view_if_needed();img.evaluate('(img)=>img.decode()')
   page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(50)
   metrics=page.evaluate('''()=>({viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,h1:[...document.querySelectorAll('h1')].map(n=>n.innerText),robots:document.querySelector('meta[name=robots]').content,canonical:document.querySelector('link[rel=canonical]')?.href??null,images:[...document.images].map(i=>({src:i.getAttribute('src'),loaded:i.complete&&i.naturalWidth>0,naturalWidth:i.naturalWidth,naturalHeight:i.naturalHeight,clientWidth:i.getBoundingClientRect().width,clientHeight:i.getBoundingClientRect().height,objectFit:getComputedStyle(i).objectFit})),faq:[...document.querySelectorAll('[data-faq-entry]')].map(e=>({question:e.querySelector('h3').innerText,answer:e.querySelector('p').innerText,visible:checkVisibility(e)}))});function checkVisibility(e){return e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})&&e.getBoundingClientRect().height>0}''')
   check(metrics['scrollWidth']<=width,f'{name}: horizontal overflow {metrics["scrollWidth"]}>{width}')
   check(metrics['h1']==[data['content']['h1']] and metrics['robots']=='noindex,follow' and metrics['canonical'] is None,f'{name}: metadata')
   for im in metrics['images']:
    check(im['loaded'] and im['objectFit']=='contain',f'{name}: image loaded/contain {im["src"]}')
    if 'shared-banners' in im['src']:check(im['naturalWidth']==1774 and im['naturalHeight']==887 and abs(im['clientWidth']/im['clientHeight']-2)<.01,f'{name}: banner dimensions {im["src"]}')
   check(len(metrics['faq'])==len(data['faqIds']),f'{name}: FAQ count')
   for f,expected in zip(metrics['faq'],SPEC['faqs']):check(f['visible'] and f['question']==expected['question'] and f['answer']==expected['answer'],f'{name}: visible FAQ text')
   for selector in ['[data-order-product-sku]','.page-card > a','.actions a','.mobile-bar a']:
    for link in page.locator(selector).all():
     if link.is_visible():check(link.bounding_box()['height']>=44,f'{name}: small CTA {selector}')
   page.screenshot(path=str(E/(name+'-full.png')),full_page=True)
   (E/(name+'-dom.html')).write_text(page.content())
   if width in [390,1280]:
    page.screenshot(path=str(E/(name+'-top.png')))
    for section in (['.product-grid','[data-visible-faq]'] if data['article'] else ['.product-grid'] if data['id']=='home' else []):
     page.locator(section).scroll_into_view_if_needed();page.screenshot(path=str(E/(name+('-faq' if 'faq' in section else '-products')+'.png')))
   result['pages'].append({'id':data['id'],'width':width,'httpStatus':response.status,'metrics':metrics,'screenshot':name+'-full.png','dom':name+'-dom.html'})
  # True unknown-path status from Astro's preview server, not a synthetic QA handler.
  missing=page.goto(BASE+'/does-not-exist-mokpo-qa/',wait_until='networkidle')
  check(missing.status==404,f'{width}: unknown path status {missing.status}')
  check(page.locator('h1').inner_text()==SPEC['pages'][-1]['content']['h1'],f'{width}: custom 404 content')
  result.setdefault('unknownPath',[]).append({'width':width,'httpStatus':missing.status,'h1':page.locator('h1').inner_text()})
  page.get_by_role('link',name='목포 근조화환 홈으로',exact=True).click();check(page.url==BASE+'/',f'{width}: 404 recovery')
  if width<860:
   menu=page.locator('.mobile-menu');summary=menu.locator('summary')
   for _ in range(2):
    summary.click();check(menu.get_attribute('open') is not None,f'{width}: menu open');summary.click();check(menu.get_attribute('open') is None,f'{width}: menu close')
   summary.click();menu.get_by_role('link',name='목포한국병원 장례식장',exact=True).click();check(page.url==BASE+'/regions/hankook-hospital-funeral-wreath/',f'{width}: mobile article navigation')
   page.go_back();check(page.url==BASE+'/',f'{width}: browser back')
   page.go_forward();check(page.url==BASE+'/regions/hankook-hospital-funeral-wreath/',f'{width}: browser forward')
  page.goto(BASE+'/',wait_until='networkidle');page.keyboard.press('Tab');check(page.locator('.skip-link').evaluate('(e)=>e===document.activeElement'),f'{width}: keyboard skip link');page.keyboard.press('Enter');check(page.evaluate('location.hash')=='#main-content',f'{width}: keyboard skip target')
  check(not console_errors,f'{width}: console errors {console_errors}')
  context.close()
 browser.close()
result['finishedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();result['status']='PASS_LOCAL_BROWSER_ONLY' if not result['failures'] else 'FAIL_LOCAL_BROWSER';result['artifacts']=[{'file':str(p.relative_to(E)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(E.iterdir()) if p.is_file() and p.name!='browser-qa.json']
(E/'browser-qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['pages','artifacts']},ensure_ascii=False,indent=2));raise SystemExit(0 if not result['failures'] else 1)
