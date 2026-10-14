"""Additional artifact pixel evidence; no source build or publication capability."""
from pathlib import Path
from preview_qa import require,ROUTE_ORDER as ROUTES,VIEWPORTS,ORIGIN
from reused import allowed_request,settle,center_in_safe_area,digest,jpeg_dimensions

def configure_context(context,origin,network):
    def guard(route):
        if allowed_request(route.request.url,route.request.method,origin):route.continue_()
        else:
            network.append({'url':route.request.url,'method':route.request.method,'blocked':True});route.abort()
    context.route('**/*',guard)
    context.route_web_socket('**/*',lambda socket:(network.append({'url':socket.url,'blockedWebSocket':True}),socket.close()))

FACTS=r'''caption => ({
 url:location.href,viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,
 revisions:[...document.querySelectorAll('meta[name="site-factory-revision"]')].map(x=>x.content),
 canonical:[...document.querySelectorAll('link[rel="canonical"]')].map(x=>x.href),
 robots:[...document.querySelectorAll('meta[name="robots"]')].map(x=>x.content),
 h1:[...document.querySelectorAll('h1')].map(x=>x.textContent.trim()),title:document.title,
 descriptions:[...document.querySelectorAll('meta[name="description"]')].map(x=>x.content),fontStatus:document.fonts.status,
 removedCaptionOccurrences:document.body.textContent.split(caption).length-1,
 sharedImageCount:[...document.images].filter(i=>new URL(i.currentSrc||i.src).pathname.startsWith('/images/shared-banners/')).length,
 images:[...document.images].map(i=>({src:new URL(i.currentSrc||i.src).pathname,complete:i.complete,width:i.naturalWidth,height:i.naturalHeight,alt:i.alt})),
 banners:[...document.querySelectorAll('[data-shared-flower-banner]')].map(el=>{
   const images=[...el.querySelectorAll('img')],i=images[0],r=i?.getBoundingClientRect();
   return {kind:el.dataset.sharedFlowerBanner,imageCount:images.length,captionCount:el.querySelectorAll('figcaption').length,
     src:i?new URL(i.currentSrc||i.src).pathname:null,alt:i?.alt,complete:i?.complete,naturalWidth:i?.naturalWidth,naturalHeight:i?.naturalHeight,
     width:r?.width,height:r?.height,loading:i?.loading,decoding:i?.decoding,
     visible:el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})};
 })
})'''

FOCUS=r'''el => {
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

def banner_kinds(route):return [] if route in ('/regions/','/404.html') else ['message','budget','consultation']

def assert_facts(facts,route,width,origin,revision,spec):
    require(facts['url']==origin+route,'rendered route identity')
    require(facts['viewport']==width and facts['scrollWidth']<=width+1,'horizontal overflow')
    mode=spec.get('releaseMode','preview');require(mode in ('preview','production'),'invalid_release_mode')
    require(facts['revisions']==([revision] if mode=='production' else []),'rendered source revision')
    site='https://seoul-songpa.fwith.kr' if mode=='production' else ORIGIN
    require(facts['canonical']==([] if route=='/404.html' else [site+route]),'rendered canonical')
    robots='noindex,nofollow,noarchive' if mode=='preview' or route=='/404.html' else 'noindex,follow' if route=='/regions/' else 'index,follow'
    require(facts['robots']==[robots],'rendered robots')
    require(len(facts['h1'])==1 and facts['h1'][0] and facts['title'] and len(facts['descriptions'])==1 and facts['descriptions'][0],'headings/title/description')
    kinds=banner_kinds(route)
    require([b['kind'] for b in facts['banners']]==kinds and facts['sharedImageCount']==len(kinds),'exact rendered banner set')
    require(facts['removedCaptionOccurrences']==0,'removed caption returned')
    require(facts['fontStatus']=='loaded','fonts settled')
    require(all(i['complete'] and i['width']>0 and i['height']>0 and i['alt'].strip() for i in facts['images']),'all images loaded/alt')
    for b in facts['banners']:
        require(b['imageCount']==1 and b['captionCount']==0,'banner image/caption count')
        accepted=spec['banners'][b['kind']]
        require(b['src']=='/images/shared-banners/'+accepted['file'] and b['alt']==accepted['alt'] and b['alt'].count('1844-0644')==1,'exact banner path/alt/phone')
        require([b['naturalWidth'],b['naturalHeight']]==[1774,887] and b['complete'],'banner intrinsic pixels')
        require(b['width']>0 and b['height']>0 and abs(b['width']/b['height']-2)<.02,'banner aspect ratio')
        require(b['visible'] and b['loading']=='lazy' and b['decoding']=='async','banner visibility/attributes')

def assert_focus(f,width,height):
    require(f['viewportWidth']==width and f['viewportHeight']==height,'focus viewport')
    require(f['visible'] and f['width']>0 and f['height']>0,'focus visible')
    require(f['left']>=-.5 and f['right']<=width+.5 and f['top']>=f['safeTop']-.5 and f['bottom']<=f['safeBottom']+.5,'banner outside sticky safe viewport')
    require(len(f['hitTests'])==9 and all(f['hitTests']),'banner covered by overlay')

def screenshot(page,out,relative,width,height,full=False):
    path=out/relative;path.parent.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(path),type='jpeg',quality=95,full_page=full,animations='disabled')
    dimensions=jpeg_dimensions(path.read_bytes())
    require(dimensions['width']==width and (dimensions['height']>=height if full else dimensions['height']==height),'screenshot dimensions')
    return {'screenshot':relative,'screenshotSha256':digest(path.read_bytes()),'dimensions':dimensions}

def capture_page(page,route,width,height,origin,revision,spec,out):
    # Native skip-link tests leave #main-content. Capture is a separate pass;
    # reload only after every native interaction/first-landing check finished.
    response=page.goto(origin+route,wait_until='networkidle')
    require(response is not None and response.status==200 and page.url==origin+route,'capture route HTTP/identity')
    settle(page)
    facts=page.evaluate(FACTS,spec['removedCaption']);assert_facts(facts,route,width,origin,revision,spec)
    name='home' if route=='/' else route.strip('/').replace('/','--').replace('.','-')
    row={'route':route,'width':width,'height':height,'facts':facts,'banners':[]}
    row['fullPage']=screenshot(page,out,f'screenshots/{width}/{name}/full.jpg',width,height,True)
    for kind in banner_kinds(route):
        image=page.locator(f'[data-shared-flower-banner="{kind}"] img')
        require(image.count()==1,'unique focused banner image')
        center_in_safe_area(page,image);focus=image.evaluate(FOCUS);assert_focus(focus,width,height)
        row['banners'].append({'kind':kind,'focusFacts':focus,**screenshot(page,out,f'screenshots/{width}/{name}/{kind}.jpg',width,height)})
    return row

def assert_capture_coverage(rows,routes,out):
    require(routes==ROUTES,'exact Songpa routes/order')
    expected=[(route,width,height) for width,height in VIEWPORTS for route in ROUTES]
    require([(r['route'],r['width'],r['height']) for r in rows]==expected,'all 15 route/viewport pairs')
    shots=[]
    for row in rows:
        require(row.get('fullPage') and [b['kind'] for b in row['banners']]==banner_kinds(row['route']),'full/focused screenshot coverage')
        shots.extend([row['fullPage']]+row['banners'])
    require(len(shots)==42 and len({s['screenshot'] for s in shots})==42,'15 full plus 27 focused screenshots required')
    for shot in shots:
        rel=shot['screenshot'];require(rel.startswith('screenshots/') and '..' not in Path(rel).parts,'screenshot path')
        file=out/rel
        require(file.is_file() and not file.is_symlink() and digest(file.read_bytes())==shot['screenshotSha256'],'actual screenshot bytes/hash')
        require(jpeg_dimensions(file.read_bytes())==shot['dimensions'],'actual screenshot dimensions')
    return {'routeViewportPairs':15,'fullPageScreenshots':15,'focusedBannerScreenshots':27,'requiredFullAndFocusedScreenshots':42}

