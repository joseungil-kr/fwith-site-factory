import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';

// Evidence-only runner: fixed loopback site, no deploy client and no external navigation.
const root=process.cwd(),site=path.join(root,'site-factory/goyang-flower');
const dist=fs.realpathSync(path.join(site,'dist'));
const output=path.join(root,'goyang-preview-evidence');
const origin='http://127.0.0.1:8936'; // Transport only: never a publication destination.
const canonicalOrigin='https://goyang.fwith.kr'; // Production metadata; HTTP loopback transport never publishes.
assert.equal(process.env.SITE_URL,canonicalOrigin);
assert.equal(process.env.SITE_INDEXABLE,'true');
assert.equal(process.env.SITE_ORIGIN,canonicalOrigin);
assert.equal(process.env.GITHUB_REF,'refs/heads/manual-goyang-supplement-artifacts-20261008');
assert(process.env.PLAYWRIGHT_INSTALL_ROOT);
fs.mkdirSync(path.join(output,'screenshots'),{recursive:true});
const require=createRequire(path.join(process.env.PLAYWRIGHT_INSTALL_ROOT,'package.json'));
const {chromium}=require('playwright');
assert.equal(require('playwright/package.json').version,'1.63.0');
const read=file=>JSON.parse(fs.readFileSync(path.join(site,file),'utf8'));
const manual=read('src/data/manual-pages.json');
const frozen=read('src/data/pages.json');
const products=read('src/data/products.json');
const {selectProducts,productFamilies}=await import(new URL('../../site-factory/goyang-flower/src/lib/catalog.mjs',import.meta.url));
assert.equal(manual.length,13,'Unexpected manual review scope');
assert.equal(frozen.length,54,'Unexpected frozen review scope');
const provenance=read('src/data/manual-provenance.json');
assert.equal(provenance.independentReview.status,'approved');
assert.equal(provenance.contentHash,'283a46f49d6489cd1636341cdbcf2e16b59b15738dbe0ce2188cc77d4f588f99');
assert.equal(provenance.rendererHash,'93500f6f3b7f7e815aba8baf510145d879e3b6da703eb953748b118b2ab6efa2');
assert.equal(provenance.assetsHash,'1f983822d5b6b40f56fd548d76f0bcd78953b2a7076de6ac5b34f85be01821ec');
assert.equal(provenance.frozenHash,'761074ecc3d88ab4ccd6dbf72a809214094a28be82669caa1f9b8daab7231ede');
assert.equal(provenance.sourcesHash,'b141db9cc04b5126b6e63700e32944e6c3d212d5d29bf359c68c908443ffd956');
assert.equal(provenance.catalogHash,'ec5a547cf59a5641f3858deccf22f5961ac651229fc8f8e7f67d07d07527ac15');
assert.equal(provenance.catalogFileHash,'33b543a8a051e5755742b8dacf22a77194e0d184e6173eea8c46386fd49c5b01');
const {architecture}=await import(new URL('../../site-factory/goyang-flower/src/lib/all-pages.mjs',import.meta.url));
const categories=[...new Set([...frozen,...manual].map(p=>p.category))];
const targets=[{id:'home',url:'/'},...categories.map(cat=>({id:cat+'-hub',url:`/${cat}/`})),...frozen.map(p=>({id:p.pageKey,url:p.url,page:p})),...manual.map(p=>({id:p.pageKey,url:p.url,page:p,manual:true}))];
assert.equal(targets.length,73);
for(const target of targets)assert(/^\/(?:[a-z0-9-]+\/)*$/.test(target.url),'Unsafe capture route');
const network=[],consoleMessages=[],pageErrors=[],results=[],routeGuards=[];
const mimes={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json','.svg':'image/svg+xml','.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp','.woff2':'font/woff2','.txt':'text/plain; charset=utf-8','.xml':'application/xml; charset=utf-8'};
const server=http.createServer((req,res)=>{
 try {
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405);res.end();return;}
  const pathname=decodeURIComponent(new URL(req.url,origin).pathname);
  let file=path.resolve(dist,'.'+pathname);
  if(file!==dist&&!file.startsWith(dist+path.sep)){res.writeHead(403);res.end();return;}
  if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
  if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404,{'Content-Type':'text/html; charset=utf-8'});res.end(fs.readFileSync(path.join(dist,'404.html')));return;}
  const real=fs.realpathSync(file);
  if(!real.startsWith(dist+path.sep)){res.writeHead(403);res.end();return;}
  res.writeHead(200,{'Content-Type':mimes[path.extname(real)]||'application/octet-stream','Cache-Control':'no-store'});
  if(req.method==='HEAD')res.end();else fs.createReadStream(real).pipe(res);
 } catch {res.writeHead(400);res.end('Invalid request');}
});
await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(8936,'127.0.0.1',resolve);});
let browser;
try {
 const missing=await fetch(origin+'/supplement-definitely-missing/');const missingBody=await missing.text();assert.equal(missing.status,404);assert.match(missingBody,/<meta[^>]*name="robots"[^>]*content="noindex/);routeGuards.push({url:'/supplement-definitely-missing/',status:404,noindex:true});
 browser=await chromium.launch();
 for(const viewport of [{name:'desktop',width:1440,height:1100},{name:'mobile',width:390,height:844}]){
  const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},deviceScaleFactor:1,locale:'ko-KR',reducedMotion:'reduce'});
  await context.route('**/*',async route=>{const url=route.request().url();if(new URL(url).origin!==origin){network.push({viewport:viewport.name,url,blockedExternal:true});await route.abort();}else await route.continue();});
  const page=await context.newPage();
  page.on('console',message=>consoleMessages.push({viewport:viewport.name,page:page.url(),type:message.type(),text:message.text()}));
  page.on('pageerror',error=>pageErrors.push({viewport:viewport.name,page:page.url(),message:error.message}));
  page.on('response',response=>network.push({viewport:viewport.name,url:response.url(),status:response.status()}));
  page.on('requestfailed',request=>network.push({viewport:viewport.name,url:request.url(),failure:request.failure()?.errorText}));
  for(const target of targets){
   const row={id:target.id,url:target.url,viewport:viewport.name,checks:[],errors:[]};
   try {
    const response=await page.goto(origin+target.url,{waitUntil:'networkidle'});
    assert.equal(response.status(),200,'HTTP status');
    await page.evaluate(()=>document.fonts.ready);
    for(const img of await page.locator('img').all())await img.scrollIntoViewIfNeeded();
    await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
    await page.evaluate(()=>Promise.all([...document.images].map(i=>i.decode())));
    await page.evaluate(async()=>{window.scrollTo({top:0,left:0,behavior:'instant'});await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));});
    const facts=await page.evaluate(()=>({
      robots:document.querySelector('meta[name="robots"]')?.content,
      canonical:document.querySelector('link[rel="canonical"]')?.href,
      revision:document.querySelector('meta[name="site-factory-revision"]')?.content,
      h1:[...document.querySelectorAll('h1')].map(n=>n.textContent),
      width:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth,
      manualMarker:document.querySelector('[data-manual-release-id]')?.getAttribute('data-manual-release-id'),
      pageKey:document.querySelector('[data-page-key]')?.getAttribute('data-page-key'),
      snapshotId:document.querySelector('[data-snapshot-id]')?.getAttribute('data-snapshot-id'),
      frozenMarker:!!document.querySelector('[data-snapshot-id]'),
      images:[...document.images].map(i=>({src:new URL(i.src).pathname,alt:i.alt,width:i.naturalWidth,height:i.naturalHeight})),
      articleProductImages:[...document.querySelectorAll('.product-section.compact .product-card img')].map(i=>new URL(i.src).pathname),
      phoneLinks:[...document.querySelectorAll('a[href="tel:18440644"]')].length,
      orderLinks:[...document.querySelectorAll('a[href]')].filter(a=>/^https:\/\/fwith\.co\.kr(?:\/|$)/.test(a.href)).length,
      h1Box:(()=>{const b=document.querySelector('h1')?.getBoundingClientRect();return b?{x:b.x,y:b.y,width:b.width,height:b.height}:null;})(),
      fontFamily:getComputedStyle(document.body).fontFamily
    }));
    row.facts=facts;
    assert.equal(facts.robots,architecture.hubs.some(h=>h.url===target.url&&h.children<3)?'noindex,follow':'index,follow','Production indexability');
    assert.equal(decodeURI(facts.canonical),decodeURI(canonicalOrigin+target.url),'Production canonical distinct from HTTP loopback transport');
    assert.equal(facts.revision,process.env.GITHUB_SHA,'Exact commit marker');
    assert.equal(facts.h1.length,1,'H1 count');
    assert(facts.scrollWidth<=facts.width+1,'Horizontal overflow');
    assert(facts.phoneLinks>0&&facts.orderLinks>0,'Real order anchors');
    assert(facts.images.every(i=>i.width>0&&i.height>0&&i.alt.trim()),'Image decode/alt');
    if(target.page){
      assert.equal(facts.pageKey,target.id,'Exact page key');
      if(target.manual){assert.equal(facts.manualMarker,target.page.manualReleaseId,'Manual release marker');assert.equal(facts.frozenMarker,false,'No synthetic frozen marker');}
      else {assert.equal(facts.snapshotId,target.page.snapshotId,'Preserved original snapshot');assert.equal(facts.manualMarker,undefined,'Frozen page not relabeled');}
      const expected=selectProducts(target.page,products,productFamilies(target.page).length>3?4:3).map(p=>p.img);
      assert.deepEqual(facts.articleProductImages,expected,'Native renderer product selection');
      const hub=`/${target.page.category}/`;
      await page.locator(`nav.breadcrumb a[href="${hub}"]:visible`).first().click();
      await page.waitForURL(origin+hub);
      await page.goBack({waitUntil:'networkidle'});
      await page.waitForURL(origin+target.url);
      await page.evaluate(()=>document.fonts.ready);
      for(const img of await page.locator('img').all())await img.scrollIntoViewIfNeeded();
      await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
    await page.evaluate(()=>Promise.all([...document.images].map(i=>i.decode())));
      row.postNavigationImages=await page.evaluate(()=>[...document.images].map(i=>({src:new URL(i.src).pathname,complete:i.complete,width:i.naturalWidth,height:i.naturalHeight})));
      assert(row.postNavigationImages.every(i=>i.complete&&i.width>0&&i.height>0),'Post-navigation decoded images');
      await page.evaluate(async()=>{window.scrollTo({top:0,left:0,behavior:'instant'});await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));});
    }
    row.checks=['http-200','production-indexability','canonical','exact-commit','one-h1','no-horizontal-overflow','decoded-images','real-cta',...(target.page?['exact-page-marker','product-families','local-back-navigation']:[])];
   } catch(error){row.errors.push(error.stack||String(error));}
   try {
    assert(!(await page.locator('body').innerText()).includes('**'),'Visible Markdown marker');
    row.captureGeometry=await page.evaluate(()=>({scrollY:scrollY,scrollX:scrollX,h1Top:document.querySelector('h1').getBoundingClientRect().top,headerBottom:document.querySelector('header').getBoundingClientRect().bottom}));
    assert.equal(row.captureGeometry.scrollY,0);assert.equal(row.captureGeometry.scrollX,0);assert(row.captureGeometry.h1Top>=row.captureGeometry.headerBottom-1,'Header overlaps H1');
    row.checks.push('settled-top-capture','unobscured-h1','no-visible-markdown-markers');
    row.screenshot=`screenshots/${target.id}-${viewport.name}.jpg`;
    await page.screenshot({path:path.join(output,row.screenshot),type:'jpeg',quality:85,fullPage:true,animations:'disabled'});
    row.screenshotSha256=crypto.createHash('sha256').update(fs.readFileSync(path.join(output,row.screenshot))).digest('hex');
   } catch(error){row.errors.push('Screenshot: '+error.message);}
   results.push(row);
  }
  await context.close();
 }
} finally {
 if(browser)await browser.close();
 await new Promise(resolve=>server.close(resolve));
 const summary={state:'captured-awaiting-independent-pixel-review',commit:process.env.GITHUB_SHA,runId:process.env.GITHUB_RUN_ID,runAttempt:process.env.GITHUB_RUN_ATTEMPT,transportOrigin:origin,canonicalOrigin,frozenPageCount:frozen.length,provenance:read('src/data/manual-provenance.json'),manualPageCount:manual.length,resultCount:results.length,results,routeGuards,machineChecksPassed:routeGuards.length===1&&results.length===targets.length*2&&results.every(r=>!r.errors.length)&&pageErrors.length===0&&network.every(r=>!r.blockedExternal&&!r.failure&&!(r.status>=400)),pixelReview:'pending',productionApproval:'not-issued'};
 fs.writeFileSync(path.join(output,'capture-results.json'),JSON.stringify(summary,null,2)+'\n');
 fs.writeFileSync(path.join(output,'browser-console.json'),JSON.stringify(consoleMessages,null,2)+'\n');
 fs.writeFileSync(path.join(output,'page-errors.json'),JSON.stringify(pageErrors,null,2)+'\n');
 fs.writeFileSync(path.join(output,'network.json'),JSON.stringify(network,null,2)+'\n');
 if(!summary.machineChecksPassed)process.exitCode=1;
 console.log(JSON.stringify({captured:results.length,machineChecksPassed:summary.machineChecksPassed,pixelReview:'pending',productionApproval:'not-issued'}));
}

