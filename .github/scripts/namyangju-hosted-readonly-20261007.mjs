import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';

// Evidence-only runner: fixed loopback site, no deploy client and no external navigation.
const workflowRoot=process.cwd(),root=path.join(workflowRoot,'target'),site=path.join(root,'site-factory/namyangju-flower');
const expectedSourceRevision='d02e86ed7fc39131431a0332a84002906be2f88b';
const dist=fs.realpathSync(path.join(site,'dist'));
const phase=process.env.MANUAL_QA_PHASE;
assert(['preview','production'].includes(phase),'Fixed evidence phase required');
const hosted=process.env.MANUAL_HOSTED_PREVIEW==='true';
assert(!hosted||phase==='preview','Hosted capture is fixed to existing isolated QA Worker');
const output=path.join(root,'namyangju-'+phase+'-evidence');
const canonicalOrigin=phase==='preview'?'https://namyangju-flower-guide-qa.joseungil.workers.dev':'https://namyangju.fwith.kr';
const origin=hosted?canonicalOrigin:'http://127.0.0.1:8934'; // Local artifact transport or exact approved isolated host.
assert.equal(process.env.SITE_URL,canonicalOrigin);
assert.equal(process.env.SITE_INDEXABLE,phase==='preview'?'false':'true');
assert.equal(process.env.GITHUB_REF,'refs/heads/manual-namyangju-hosted-check-20261007');
assert.equal(phase,'preview');assert(hosted);
assert(process.env.PLAYWRIGHT_INSTALL_ROOT);
fs.mkdirSync(path.join(output,'screenshots'),{recursive:true});
const require=createRequire(path.join(process.env.PLAYWRIGHT_INSTALL_ROOT,'package.json'));
const {chromium}=require('playwright');
assert.equal(require('playwright/package.json').version,'1.63.0');
const read=file=>JSON.parse(fs.readFileSync(path.join(site,file),'utf8'));
const manual=read('src/data/manual-pages.json');
const frozen=read('src/data/pages.json');
const products=read('src/data/products.json');
const {selectProducts,productFamilies}=await import(new URL('../../target/site-factory/namyangju-flower/src/lib/catalog.mjs',import.meta.url));
assert.equal(manual.length,12,'Unexpected manual review scope');
assert.equal(frozen.length,20,'Unexpected frozen review scope');
const provenance=read('src/data/manual-provenance.json');
assert.equal(provenance.independentReview.status,'approved');
assert.equal(provenance.contentHash,'1fb3a55e1938a5a4b60a3712e5812db88d2145048b4f2fb80d91f87ff14b0365');
assert.equal(provenance.dependencyHash,'bcc8263b780a5c8479fc8eaf2db8c022db2f02b0e410ced09c97e1a698e90805');
const categories=[...new Set([...frozen,...manual].map(p=>p.category))];
const targets=[{id:'home',url:'/'},...categories.map(cat=>({id:cat+'-hub',url:`/${cat}/`})),...frozen.map(p=>({id:p.pageKey,url:p.url,page:p})),...manual.map(p=>({id:p.pageKey,url:p.url,page:p,manual:true}))];
assert.equal(targets.length,37);
for(const target of targets)assert(/^\/(?:[a-z0-9-]+\/)*$/.test(target.url),'Unsafe capture route');
async function settleCaptureFrame(page){
 const frame=await page.evaluate(async()=>{
  await document.fonts.ready;
  await Promise.all([...document.images].map(image=>image.decode()));
  window.scrollTo({left:0,top:0,behavior:'instant'});
  await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
  const header=document.querySelector('header'),h1=document.querySelector('h1');
  if(!header||!h1)throw new Error('Missing header/H1 capture geometry');
  return {scrollX:window.scrollX,scrollY:window.scrollY,headerBottom:header.getBoundingClientRect().bottom,h1Top:h1.getBoundingClientRect().top,decodedImageCount:document.images.length};
 });
 assert.equal(frame.scrollX,0,'Screenshot must have zero horizontal scroll');
 assert.equal(frame.scrollY,0,'Screenshot must have zero vertical scroll');
 assert(frame.h1Top>=frame.headerBottom,'Header/H1 overlap in settled capture');
 return frame;
}
const network=[],consoleMessages=[],pageErrors=[],results=[];
let deniedResponse=null;
const mimes={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json','.svg':'image/svg+xml','.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp','.woff2':'font/woff2','.txt':'text/plain; charset=utf-8','.xml':'application/xml; charset=utf-8'};
const server=http.createServer((req,res)=>{
 try {
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405);res.end();return;}
  const pathname=decodeURIComponent(new URL(req.url,origin).pathname);
  let file=path.resolve(dist,'.'+pathname);
  if(file!==dist&&!file.startsWith(dist+path.sep)){res.writeHead(403);res.end();return;}
  if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
  if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404,{'Content-Type':'text/plain'});res.end('Not found');return;}
  const real=fs.realpathSync(file);
  if(!real.startsWith(dist+path.sep)){res.writeHead(403);res.end();return;}
  res.writeHead(200,{'Content-Type':mimes[path.extname(real)]||'application/octet-stream','Cache-Control':'no-store'});
  if(req.method==='HEAD')res.end();else fs.createReadStream(real).pipe(res);
 } catch {res.writeHead(400);res.end('Invalid request');}
});
if(!hosted)await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(8934,'127.0.0.1',resolve);});
let browser;
try {
 browser=await chromium.launch();
 for(const viewport of [{name:'desktop',width:1440,height:1100},{name:'mobile',width:390,height:844}]){
  const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},deviceScaleFactor:1,locale:'ko-KR',reducedMotion:'reduce'});
  await context.route('**/*',async route=>{if(deniedResponse){await route.abort();return;}const url=route.request().url();if(new URL(url).origin!==origin){network.push({viewport:viewport.name,url,blockedExternal:true});await route.abort();}else await route.continue();});
  const page=await context.newPage();
  page.on('console',message=>consoleMessages.push({viewport:viewport.name,page:page.url(),type:message.type(),text:message.text()}));
  page.on('pageerror',error=>pageErrors.push({viewport:viewport.name,page:page.url(),message:error.message}));
  page.on('response',response=>{const row={viewport:viewport.name,url:response.url(),status:response.status()};network.push(row);if([401,403,429].includes(row.status)&&new URL(row.url).origin===origin)deniedResponse=row;});
  page.on('requestfailed',request=>network.push({viewport:viewport.name,url:request.url(),failure:request.failure()?.errorText}));
  for(const target of targets){
   const row={id:target.id,url:target.url,viewport:viewport.name,checks:[],errors:[]};
   try {
    const response=await page.goto(origin+target.url,{waitUntil:'networkidle'});
    assert(!deniedResponse,'Access/rate-limit denial: stop capture without retries');
    assert.equal(response.status(),200,'HTTP status');
    await page.evaluate(()=>document.fonts.ready);
    for(const img of await page.locator('img').all())await img.scrollIntoViewIfNeeded();
    await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
    row.initialSettledFrame=await settleCaptureFrame(page);
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
    if(phase==='preview')assert.match(facts.robots,/noindex/,'Preview robots');
    else if(target.page||target.id==='home'){assert.match(facts.robots,/(^|,)\s*index(,|$)/,'Production indexable route');assert(!facts.robots.includes('noindex'));}
    assert.equal(decodeURI(facts.canonical),decodeURI(canonicalOrigin+target.url),'Exact phase canonical distinct from local transport');
    assert.equal(facts.revision,expectedSourceRevision,'Exact commit marker');
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
      await page.locator(`a[href="${hub}"]:visible`).first().click();
      await page.waitForURL(origin+hub);
      assert(!deniedResponse,'Access/rate-limit denial: no back-navigation request');
      await page.goBack({waitUntil:'networkidle'});
      await page.waitForURL(origin+target.url);
      await page.evaluate(()=>document.fonts.ready);
      for(const img of await page.locator('img').all())await img.scrollIntoViewIfNeeded();
      await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
      row.postNavigationImages=await page.evaluate(()=>[...document.images].map(i=>({src:new URL(i.src).pathname,complete:i.complete,width:i.naturalWidth,height:i.naturalHeight})));
      assert(row.postNavigationImages.every(i=>i.complete&&i.width>0&&i.height>0),'Post-navigation decoded images');
      row.afterBackSettledFrame=await settleCaptureFrame(page);
    }
    row.checks=['http-200',phase==='preview'?'preview-noindex':'native-production-robots','canonical','exact-commit','one-h1','no-horizontal-overflow','decoded-images','real-cta',...(target.page?['exact-page-marker','product-families','local-back-navigation']:[])];
   } catch(error){row.errors.push(error.stack||String(error));}
   if(deniedResponse){row.errors.push('Access/rate-limit denial: capture stopped');results.push(row);break;}
   try {
    row.screenshot=`screenshots/${viewport.name}/${target.id}-${viewport.name}.jpg`;
    fs.mkdirSync(path.join(output,'screenshots',viewport.name),{recursive:true});
    row.captureFrame=await settleCaptureFrame(page);
    await page.screenshot({path:path.join(output,row.screenshot),type:'jpeg',quality:85,fullPage:true,animations:'disabled'});
    row.screenshotSha256=crypto.createHash('sha256').update(fs.readFileSync(path.join(output,row.screenshot))).digest('hex');
   } catch(error){row.errors.push('Screenshot: '+error.message);}
   results.push(row);
  }
  await context.close();
  if(deniedResponse)break;
 }
} finally {
 if(browser)await browser.close();
 if(server.listening)await new Promise(resolve=>server.close(resolve));
 const summary={state:'captured-awaiting-independent-pixel-review',commit:expectedSourceRevision,diagnosticWorkflowRevision:process.env.GITHUB_SHA,runId:process.env.GITHUB_RUN_ID,runAttempt:process.env.GITHUB_RUN_ATTEMPT,transportOrigin:origin,canonicalOrigin,phase,hosted,deniedResponse,frozenPageCount:frozen.length,provenance:read('src/data/manual-provenance.json'),manualPageCount:manual.length,resultCount:results.length,results,machineChecksPassed:results.length===targets.length*2&&results.every(r=>!r.errors.length)&&pageErrors.length===0&&network.every(r=>!r.blockedExternal&&!r.failure&&!(r.status>=400)),pixelReview:'pending',productionApproval:'not-issued'};
 fs.writeFileSync(path.join(output,'capture-results.json'),JSON.stringify(summary,null,2)+'\n');
 fs.writeFileSync(path.join(output,'browser-console.json'),JSON.stringify(consoleMessages,null,2)+'\n');
 fs.writeFileSync(path.join(output,'page-errors.json'),JSON.stringify(pageErrors,null,2)+'\n');
 fs.writeFileSync(path.join(output,'network.json'),JSON.stringify(network,null,2)+'\n');
 if(!summary.machineChecksPassed)process.exitCode=1;
 console.log(JSON.stringify({captured:results.length,machineChecksPassed:summary.machineChecksPassed,pixelReview:'pending',productionApproval:'not-issued'}));
}

