"""Runner-only artifact capture: all-route DOM, selected actual viewport pixels.
No build, source mutation, public navigation, provider or publication capability.
"""
from pathlib import Path
from functools import partial
from threading import Thread
from importlib.metadata import version
import argparse, json, os, re, sys, traceback
from bind import (HERE, BUILD_CONTROL, VIEWPORTS, require, validate_bindings,
 validate_metadata, extract_bound_archive, inspect_artifact, verify_checkout, verify_runner, summarize_run, summarize_artifact)
from reused import (SafeServer, SafeHandler, allowed_request, settle, center_in_safe_area,
 digest, compact, write_json, manifest, jpeg_dimensions)

FACTS = r'''() => ({
 url:location.href, viewport:innerWidth, scrollWidth:document.documentElement.scrollWidth,
 revision:document.querySelector('meta[name="site-factory-revision"]')?.content,
 canonical:[...document.querySelectorAll('link[rel="canonical"]')].map(x=>x.href),
 h1:[...document.querySelectorAll('h1')].map(x=>x.textContent.trim()),
 robots:document.querySelector('meta[name="robots"]')?.content,
 title:document.title, description:document.querySelector('meta[name="description"]')?.content,
 fontStatus:document.fonts.status,
 removedCaptionOccurrences:document.body.textContent.split('꽃이랑 공통 안내 이미지 · 실제 판매상품 사진이 아닌 AI 생성 이미지입니다.').length-1,
 sharedImageCount:[...document.images].filter(i=>new URL(i.currentSrc||i.src).pathname.startsWith('/images/shared-banners/')).length,
 images:[...document.images].map(i=>({src:new URL(i.currentSrc||i.src).pathname,complete:i.complete,width:i.naturalWidth,height:i.naturalHeight,alt:i.alt})),
 banners:[...document.querySelectorAll('[data-shared-flower-banner]')].map(el=>{
  const images=[...el.querySelectorAll('img')],i=images[0],r=i?.getBoundingClientRect(),c=i?getComputedStyle(i):null;
  return {kind:el.dataset.sharedFlowerBanner,imageCount:images.length,captionCount:el.querySelectorAll('figcaption').length,
    src:i?new URL(i.currentSrc||i.src).pathname:null,alt:i?.alt,complete:i?.complete,naturalWidth:i?.naturalWidth,naturalHeight:i?.naturalHeight,
    width:r?.width,height:r?.height,loading:i?.loading,decoding:i?.decoding,objectFit:c?.objectFit,
    visible:el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})};
 })
})'''

FOCUS = r'''el => {
 const r=el.getBoundingClientRect(),h=document.querySelector('.site-header'),b=document.querySelector('.mobile-bar');
 const visible=e=>!!e&&getComputedStyle(e).display!=='none'&&e.getBoundingClientRect().height>0;
 const hits=[];
 for(const fx of [.05,.5,.95])for(const fy of [.05,.5,.95]){
  const hit=document.elementFromPoint(r.left+r.width*fx,r.top+r.height*fy);hits.push(!!hit&&(el===hit||el.contains(hit)));
 }
 return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,scrollY,
 safeTop:visible(h)?Math.max(0,h.getBoundingClientRect().bottom):0,
 safeBottom:visible(b)?Math.min(innerHeight,b.getBoundingClientRect().top):innerHeight,
 viewportWidth:innerWidth,viewportHeight:innerHeight,
 visible:el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}),hitTests:hits};
}'''

def assert_facts(facts,proof,route,origin,width):
 require(facts['url']==origin+route,'rendered route identity')
 require(facts['viewport']==width and facts['scrollWidth']<=width+1,'horizontal overflow')
 require(facts['revision']==proof['sourceSha'],'rendered source revision')
 require(facts['canonical']==([]if route=='/404.html'else[proof['origin']+route]),'rendered canonical')
 require(len(facts['h1'])==1 and bool(facts['h1'][0]) and facts['title'] and facts['description'],'headings/title/description')
 robots={'noindex','nofollow','noarchive'}if route=='/404.html'else({'noindex','follow'}if route in proof['thinHubRoutes']else{'index','follow'})
 require(set(re.split(r'\s*,\s*',facts['robots'].lower()))==robots,'rendered robots')
 no_banner=route=='/404.html' or route in proof['thinHubRoutes']
 expected=[]if no_banner else ['message','budget','consultation']
 require([x['kind']for x in facts['banners']]==expected and facts['sharedImageCount']==len(expected),'exact rendered banner set')
 require(facts['removedCaptionOccurrences']==0,'removed caption text returned')
 require(facts['fontStatus']=='loaded','font settling')
 require(all(i['complete']and i['width']>0 and i['height']>0 and i['alt'].strip()for i in facts['images']),'all images decode/alt')
 for b in facts['banners']:
  require(b['captionCount']==0 and b['imageCount']==1,'banner caption/count')
  require(b['src']==f'/images/shared-banners/flower-{b["kind"]}.webp','exact banner src')
  require(b['alt']==proof['exactAlts'][b['kind']] and b['alt'].count('1844-0644')==1,'exact banner alt/phone')
  require(b['naturalWidth']==1774 and b['naturalHeight']==887 and b['complete'],'banner decode/intrinsic pixels')
  require(b['width']>0 and b['height']>0 and abs(b['width']/b['height']-2)<.02,'banner ratio/crop')
  require(b['loading']=='lazy' and b['decoding']=='async' and b['visible'],'banner attributes/visibility')

def assert_focus(f,width,height):
 require(f['viewportWidth']==width and f['viewportHeight']==height,'focus viewport')
 require(f['visible'] and f['width']>0 and f['height']>0,'focus visible')
 require(f['left']>=-.5 and f['right']<=width+.5 and f['top']>=f['safeTop']-.5 and f['bottom']<=f['safeBottom']+.5,'banner outside safe viewport')
 require(len(f['hitTests'])==9 and all(f['hitTests']),'banner covered by overlay')

def screenshot(page,output,relative,width,height,full=False):
 file=output/relative;file.parent.mkdir(parents=True,exist_ok=True)
 page.screenshot(path=str(file),type='jpeg',quality=95,full_page=full,animations='disabled')
 dimensions=jpeg_dimensions(file.read_bytes())
 require(dimensions['width']==width and (dimensions['height']>=height if full else dimensions['height']==height),'screenshot dimensions')
 return {'screenshot':relative,'screenshotSha256':digest(file.read_bytes()),'dimensions':dimensions}

def validate_capture(rows,proof,output):
 grid=[(route,w,h)for w,h in VIEWPORTS for route in proof['routes']]
 require([(r['route'],r['width'],r['height'])for r in rows]==grid,'all-route DOM grid incomplete')
 shots=[]
 for row in rows:
  require(not row['issues'],'rendered DOM/focused capture failed')
  selected=row['route']in proof['captureRoutes']
  require(bool(row.get('fullPage'))==selected,'full-page capture coverage')
  require([s['kind']for s in row['banners']]==(['message','budget','consultation']if selected else[]),'three-banner focus capture coverage')
  shots.extend(([row['fullPage']]if selected else[])+row['banners'])
 require(len(shots)==len(proof['captureRoutes'])*2*4,'screenshot coverage')
 require(len({s['screenshot']for s in shots})==len(shots),'duplicate screenshot')
 for s in shots:
  rel=s['screenshot'];require(rel.startswith('screenshots/')and'..'not in Path(rel).parts,'screenshot path')
  file=output/rel;require(file.is_file()and not file.is_symlink()and digest(file.read_bytes())==s['screenshotSha256'],'screenshot hash')
  require(jpeg_dimensions(file.read_bytes())==s['dimensions'],'screenshot bytes/dimensions')
 return {'domRouteViewportPairs':len(grid),'selectedRouteViewportPairs':len(proof['captureRoutes'])*2,'focusedBannerScreenshots':len(proof['captureRoutes'])*6,'totalScreenshots':len(shots)}

def seal(output):
 files={p.relative_to(output).as_posix():digest(p.read_bytes())for p in sorted(output.rglob('*'))if p.is_file()and p.name!='evidence-manifest.json'}
 write_json(output/'evidence-manifest.json',{'qaControlSha':os.environ.get('GITHUB_SHA'),'qaRunId':os.environ.get('GITHUB_RUN_ID'),'qaRunAttempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'files':files,'pixelReview':'pending','publicationAuthorization':'not-issued','publicHttpVerified':False})

def main():
 p=argparse.ArgumentParser();p.add_argument('--region');p.add_argument('--control',type=Path);p.add_argument('--inputs',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--seal',action='store_true');a=p.parse_args()
 output=a.output.resolve();output.mkdir(parents=True,exist_ok=True)
 if a.seal:seal(output);return 0
 verify_runner();verify_checkout(a.control,BUILD_CONTROL);verify_checkout(HERE.parents[2],os.environ['GITHUB_SHA'])
 require(version('playwright')=='1.63.0','pinned Playwright required')
 data=json.loads((HERE/'bindings.json').read_text());validate_bindings(data,a.control);require(a.region in data['selectedRegions'],'region not selected');row=data['sites'][a.region]
 run=json.loads((a.inputs/'run.json').read_text());artifact=json.loads((a.inputs/'artifact.json').read_text());validate_metadata(a.region,row,run,artifact)
 require((a.inputs/'artifact.zip').stat().st_size==artifact['size_in_bytes'],'downloaded archive size')
 release=extract_bound_archive(a.inputs/'artifact.zip',output/'release',row['build']['archiveSha256'])
 proof=inspect_artifact(a.region,row,a.control,release,output)
 proof.update(qaControlSha=os.environ['GITHUB_SHA'],qaRunId=os.environ['GITHUB_RUN_ID'],qaRunAttempt=os.environ['GITHUB_RUN_ATTEMPT'],bindingsSha256=digest((HERE/'bindings.json').read_bytes()),runnerFiles={p.name:digest(p.read_bytes())for p in sorted(HERE.iterdir())if p.is_file()})
 write_json(output/'artifact-binding.json',proof);write_json(output/'build-run-api.json',summarize_run(run));write_json(output/'build-artifact-api.json',summarize_artifact(artifact))
 server=SafeServer(('127.0.0.1',0),partial(SafeHandler,directory=str(release/'dist')));Thread(target=server.serve_forever,daemon=True).start()
 origin=f'http://127.0.0.1:{server.server_port}';rows=[];network=[];console=[];errors=[];fatal=None;coverage=None;browser_version=None
 try:
  from playwright.sync_api import sync_playwright
  with sync_playwright()as playwright:
   browser=playwright.chromium.launch(headless=True);browser_version=browser.version
   try:
    for width,height in VIEWPORTS:
     context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,locale='ko-KR',reduced_motion='reduce',service_workers='block',accept_downloads=False)
     def guard(route):
      if allowed_request(route.request.url,route.request.method,origin):route.continue_()
      else:network.append({'url':route.request.url,'method':route.request.method,'blocked':True});route.abort()
     context.route('**/*',guard);context.route_web_socket('**/*',lambda socket:(network.append({'url':socket.url,'blockedWebSocket':True}),socket.close()))
     page=context.new_page();page.set_default_timeout(30000)
     page.on('console',lambda msg:console.append({'type':msg.type,'text':msg.text}));page.on('pageerror',lambda error:errors.append(str(error)))
     page.on('response',lambda response:network.append({'url':response.url,'status':response.status}));page.on('requestfailed',lambda request:network.append({'url':request.url,'failure':request.failure}))
     for route in proof['routes']:
      result={'route':route,'width':width,'height':height,'issues':[],'banners':[]};rows.append(result)
      try:
       response=page.goto(origin+route,wait_until='networkidle');require(response is not None and response.status==200,'loopback HTTP 200')
       settle(page);result['facts']=page.evaluate(FACTS);assert_facts(result['facts'],proof,route,origin,width)
       if route in proof['captureRoutes']:
        name='home'if route=='/'else route.strip('/').replace('/','--')
        result['fullPage']=screenshot(page,output,f'screenshots/{width}/{name}/full.jpg',width,height,True)
        for kind in ['message','budget','consultation']:
         focus={'kind':kind};result['banners'].append(focus)
         try:
          loc=page.locator(f'[data-shared-flower-banner="{kind}"]');require(loc.count()==1,'unique banner')
          center_in_safe_area(page,loc);focus['focusFacts']=loc.evaluate(FOCUS);assert_focus(focus['focusFacts'],width,height)
          focus.update(screenshot(page,output,f'screenshots/{width}/{name}/{kind}.jpg',width,height))
         except Exception:result['issues'].append(traceback.format_exc())
      except Exception:result['issues'].append(traceback.format_exc())
     context.close()
   finally:browser.close()
  require(manifest(release/'dist')==proof['files'],'dist changed during capture')
  require(digest((release/'release.json').read_bytes())==proof['releaseManifestSha256'],'manifest changed during capture')
  coverage=validate_capture(rows,proof,output);verify_checkout(a.control,BUILD_CONTROL);verify_checkout(HERE.parents[2],os.environ['GITHUB_SHA'])
 except Exception:fatal=traceback.format_exc()
 finally:server.shutdown();server.server_close()
 bad_network=[x for x in network if x.get('blocked')or x.get('blockedWebSocket')or x.get('failure')or x.get('status',200)>=400]
 passed=not fatal and not errors and not bad_network and not any(c['type']=='error'for c in console)and not any(r['issues']for r in rows)
 write_json(output/'capture-results.json',{'state':'captured-awaiting-independent-pixel-review'if passed else'machine-qa-failed','machineChecksPassed':passed,'artifactBinding':proof,'coverage':coverage,'results':rows,'fatalError':fatal,'playwrightVersion':version('playwright'),'browserVersion':browser_version,'scope':'runner loopback only','pixelReview':'pending','publicHttpVerified':False,'publicationAuthorization':'not-issued'})
 write_json(output/'network.json',network);write_json(output/'browser-console.json',console);write_json(output/'page-errors.json',errors);seal(output)
 print(json.dumps({'region':a.region,'machineChecksPassed':passed,'coverage':coverage,'pixelReview':'pending'}));return 0 if passed else 1
if __name__=='__main__':sys.exit(main())
