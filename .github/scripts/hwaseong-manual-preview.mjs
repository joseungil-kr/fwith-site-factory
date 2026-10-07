import fs from 'node:fs';import path from 'node:path';import http from 'node:http';import crypto from 'node:crypto';import assert from 'node:assert/strict';import {createRequire} from 'node:module';
// Evidence-only: fixed loopback origin, fixed branch, no merchant/phone click or external navigation.
const root=process.cwd(),site=path.join(root,'site-factory/hwaseong-flower'),dist=fs.realpathSync(path.join(site,'dist')),output=path.join(root,'hwaseong-preview-evidence'),origin='http://127.0.0.1:8935';
assert.equal(process.env.GITHUB_REF,'refs/heads/manual-hwaseong-qa-20261007');assert.equal(process.env.SITE_URL,origin);assert.equal(process.env.SITE_INDEXABLE,'false');assert.equal(process.env.MANUAL_PREVIEW,'true');assert(process.env.PLAYWRIGHT_INSTALL_ROOT);
const read=f=>JSON.parse(fs.readFileSync(path.join(site,f),'utf8'));const proof=read('src/data/manual-provenance.json');assert.equal(proof.independentReview.status,'pending','Screenshot CI cannot issue production approval');assert.equal(proof.releaseHash,process.env.EXPECTED_QA_RELEASE_HASH,'Wrong independently reviewed QA boundary');
const manual=read('src/data/manual-manifest.json').pages,frozen=read('src/data/publish-manifest.json').pages,products=read('src/data/products.json');assert.equal(manual.length,18);assert.equal(frozen.length,40);
const urls=[...manual,...frozen].map(p=>p.url);assert.equal(new Set(urls).size,58);
const targetPages=[...frozen.map(p=>({id:p.pageKey,url:p.url,kind:'frozen',page:p})),...manual.map(p=>({id:p.pageKey,url:p.url,kind:'manual',page:p}))];
const targets=[{id:'home',url:'/',kind:'hub'},...['guide','funeral','places','occasions','flower-knowledge','order-help'].map(c=>({id:c+'-hub',url:`/${c}/`,kind:'hub'})),...targetPages];assert.equal(targets.length,65);
fs.mkdirSync(path.join(output,'screenshots'),{recursive:true});const require=createRequire(path.join(process.env.PLAYWRIGHT_INSTALL_ROOT,'package.json'));assert.equal(require('playwright/package.json').version,'1.63.0');const {chromium}=require('playwright');
const mime={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json','.svg':'image/svg+xml','.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp','.woff2':'font/woff2','.txt':'text/plain; charset=utf-8','.xml':'application/xml; charset=utf-8'};
const server=http.createServer((req,res)=>{try{if(!['GET','HEAD'].includes(req.method)){res.writeHead(405);res.end();return;}let file=path.resolve(dist,'.'+decodeURIComponent(new URL(req.url,origin).pathname));if(file!==dist&&!file.startsWith(dist+path.sep)){res.writeHead(403);res.end();return;}if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end('Not found');return;}const real=fs.realpathSync(file);if(!real.startsWith(dist+path.sep)){res.writeHead(403);res.end();return;}res.writeHead(200,{'Content-Type':mime[path.extname(real)]||'application/octet-stream','Cache-Control':'no-store'});if(req.method==='HEAD')res.end();else fs.createReadStream(real).pipe(res);}catch{res.writeHead(400);res.end('Invalid request');}});
await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(8935,'127.0.0.1',resolve)});
const network=[],consoleMessages=[],pageErrors=[],results=[];let browser;
async function settleImages(page){
 await page.evaluate(()=>document.fonts.ready);
 for(const img of await page.locator('img').all())await img.scrollIntoViewIfNeeded();
 await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
 await page.evaluate(async()=>{
  await Promise.all([...document.images].map(i=>i.decode()));
  // The site's smooth-scroll CSS must not leave a sticky header mid-capture.
  window.scrollTo({top:0,left:0,behavior:'instant'});
  await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
 });
 await page.waitForFunction(()=>window.scrollX===0&&window.scrollY===0);
}

try{
 browser=await chromium.launch();
 for(const viewport of [{name:'desktop',width:1440,height:1100},{name:'mobile',width:390,height:844}]){
  const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},deviceScaleFactor:1,locale:'ko-KR',reducedMotion:'reduce'});
  await context.route('**/*',async route=>{const url=route.request().url();if(new URL(url).origin!==origin){network.push({viewport:viewport.name,url,blockedExternal:true});await route.abort();}else await route.continue();});
  const page=await context.newPage();page.setDefaultTimeout(15000);page.setDefaultNavigationTimeout(30000);
  page.on('console',m=>consoleMessages.push({viewport:viewport.name,page:page.url(),type:m.type(),text:m.text()}));page.on('pageerror',e=>pageErrors.push({viewport:viewport.name,page:page.url(),message:e.message}));page.on('response',r=>network.push({viewport:viewport.name,url:r.url(),status:r.status()}));page.on('requestfailed',r=>network.push({viewport:viewport.name,url:r.url(),failure:r.failure()?.errorText}));
  for(const target of targets){const row={id:target.id,url:target.url,kind:target.kind,viewport:viewport.name,checks:[],errors:[]};
   try{
    const response=await page.goto(origin+target.url,{waitUntil:'networkidle'});assert.equal(response.status(),200);await settleImages(page);
    const facts=await page.evaluate(()=>({robots:document.querySelector('meta[name="robots"]')?.content,canonical:document.querySelector('link[rel="canonical"]')?.href,revision:document.querySelector('meta[name="site-factory-revision"]')?.content,h1:[...document.querySelectorAll('h1')].map(n=>n.textContent),width:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth,manualMarker:document.querySelector('[data-manual-publication-id]')?.getAttribute('data-manual-publication-id')||null,frozenMarker:document.querySelector('[data-snapshot-id]')?.getAttribute('data-snapshot-id')||null,ogImage:document.querySelector('meta[property="og:image"]')?.content,images:[...document.images].map(i=>({src:new URL(i.src).pathname,alt:i.alt,width:i.naturalWidth,height:i.naturalHeight})),panelImages:[...document.querySelectorAll('.manual-order .manual-products img')].map(i=>new URL(i.src).pathname),phoneLinks:document.querySelectorAll('a[href="tel:18440644"]').length,orderLinks:document.querySelectorAll('a[href="https://fwith.co.kr"]').length,fontFamily:getComputedStyle(document.body).fontFamily}));row.facts=facts;
    assert.match(facts.robots,/noindex/);assert.equal(decodeURI(facts.canonical),decodeURI(origin+target.url));assert.equal(facts.revision,process.env.GITHUB_SHA);assert.equal(facts.h1.length,1);assert(facts.scrollWidth<=facts.width+1,'Horizontal overflow');assert(facts.phoneLinks>0&&facts.orderLinks>0);assert(facts.images.every(i=>i.width>0&&i.height>0&&i.alt.trim()));
    if(target.kind==='manual'){
     assert.equal(facts.manualMarker,target.page.manualPublicationId);assert.equal(facts.frozenMarker,null);assert.equal(new URL(facts.ogImage).pathname,target.page.ogImage);
     if(target.page.orderPanel==='funeral-catalog'){const expected=products.filter(p=>['funeral-basic','funeral-premium'].includes(p.productKey)).map(p=>p.image);assert.deepEqual(facts.panelImages,expected,'Funeral-only catalogue panel');}
    }
    if(target.kind==='frozen'){assert.equal(facts.frozenMarker,target.page.snapshotId);assert.equal(facts.manualMarker,null);}
    if(target.kind!=='hub'&&target.page.routeType==='category'){
     const hub=`/${target.page.category}/`;
     // Match the always-visible article breadcrumb, never a hidden mobile header anchor.
     const anchor=page.locator(`nav.breadcrumbs a[href="${hub}"]:visible`).first();assert.equal(await anchor.count(),1,'Visible breadcrumb missing');await anchor.scrollIntoViewIfNeeded();assert(await anchor.isVisible());await anchor.click();await page.waitForURL(origin+hub);await page.goBack({waitUntil:'networkidle'});await page.waitForURL(origin+target.url);await settleImages(page);row.checks.push('visible-breadcrumb-roundtrip');
    }
    row.checks.push('http-200','noindex','canonical','exact-commit','single-h1','no-overflow','decoded-images','cta-hrefs','correct-provenance');
   }catch(e){row.errors.push(e.stack||String(e));}
   try{
    await settleImages(page);
    row.captureGeometry=await page.evaluate(()=>{
     const box=element=>{const r=element.getBoundingClientRect();return {top:r.top,bottom:r.bottom,left:r.left,right:r.right,width:r.width,height:r.height};};
     return {scrollX:window.scrollX,scrollY:window.scrollY,header:box(document.querySelector('.site-header')),h1:box(document.querySelector('h1'))};
    });
    assert.equal(row.captureGeometry.scrollX,0,'Capture horizontal scroll not settled');
    assert.equal(row.captureGeometry.scrollY,0,'Capture vertical scroll not settled');
    assert(Math.abs(row.captureGeometry.header.top)<=1,'Sticky header not at viewport top');
    assert(row.captureGeometry.h1.top>=row.captureGeometry.header.bottom-1,'Sticky header overlaps H1');
    row.checks.push('settled-top-capture','unobscured-h1');
    row.screenshot=`screenshots/${target.id}-${viewport.name}.jpg`;await page.screenshot({path:path.join(output,row.screenshot),type:'jpeg',quality:85,fullPage:true,animations:'disabled'});row.screenshotSha256=crypto.createHash('sha256').update(fs.readFileSync(path.join(output,row.screenshot))).digest('hex');
   }catch(e){row.errors.push('Screenshot: '+e.message);}
   results.push(row);
  }
  await context.close();
 }
}finally{
 if(browser)await browser.close();await new Promise(r=>server.close(r));
 const summary={state:'captured-awaiting-independent-pixel-review',commit:process.env.GITHUB_SHA,runId:process.env.GITHUB_RUN_ID,runAttempt:process.env.GITHUB_RUN_ATTEMPT,origin,releaseHash:proof.releaseHash,manualPages:18,frozenPages:40,hubPages:7,expectedScreenshots:130,resultCount:results.length,results,machineChecksPassed:results.length===130&&results.every(r=>r.errors.length===0)&&pageErrors.length===0&&network.every(r=>!r.blockedExternal&&!r.failure&&!(r.status>=400)),pixelReview:'pending',productionApproval:'not-issued'};
 fs.writeFileSync(path.join(output,'capture-results.json'),JSON.stringify(summary,null,2)+'\n');fs.writeFileSync(path.join(output,'network.json'),JSON.stringify(network,null,2)+'\n');fs.writeFileSync(path.join(output,'browser-console.json'),JSON.stringify(consoleMessages,null,2)+'\n');fs.writeFileSync(path.join(output,'page-errors.json'),JSON.stringify(pageErrors,null,2)+'\n');if(!summary.machineChecksPassed)process.exitCode=1;console.log(JSON.stringify({captured:results.length,machineChecksPassed:summary.machineChecksPassed,pixelReview:'pending',productionApproval:'not-issued'}));
}
