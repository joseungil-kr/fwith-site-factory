import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';

// Evidence-only runner: fixed approved production host, no deploy client and no external navigation.
const workflowRoot=process.cwd(),root=path.join(workflowRoot,'target'),site=path.join(root,'site-factory/namyangju-flower');
const expectedSourceRevision='d02e86ed7fc39131431a0332a84002906be2f88b';
const expectedVerificationRevision='41ab5fd749d3e6f755788022158fefe06c523048';
const expectedVerificationHelperSha256='ceda678e546014bcf80704a5cc7f095ab7ce13594bc9f2583f9849db85ce0ddf';
const dist=fs.realpathSync(path.join(site,'dist'));
const phase=process.env.MANUAL_QA_PHASE;
assert(['preview','production'].includes(phase),'Fixed evidence phase required');
const hosted=process.env.MANUAL_HOSTED_PRODUCTION==='true';
assert(!hosted||phase==='production','Hosted capture is fixed to existing approved production hostname');
const output=path.join(root,'namyangju-'+phase+'-evidence');
const canonicalOrigin=phase==='preview'?'https://namyangju-flower-guide-qa.joseungil.workers.dev':'https://namyangju.fwith.kr';
const origin=hosted?canonicalOrigin:'http://127.0.0.1:8934'; // Local artifact transport or exact approved production host.
assert.equal(process.env.SITE_URL,canonicalOrigin);
assert.equal(process.env.SITE_INDEXABLE,phase==='preview'?'false':'true');
assert.equal(process.env.GITHUB_REF,'refs/heads/manual-namyangju-production-check-20261007');
assert.equal(phase,'production');assert(hosted);
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
// BEGIN receipt-bound telemetry isolation functions (offline-tested from these bytes).
const managedBeaconUrl='https://static.cloudflareinsights.com/beacon.min.js/v31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495';
const managedBeaconSha256='8a5cd48fb3f913d009a128498bef6fadc43d5561daec87e79f6adcd0bcc903f5';
function knownManagedBeaconRequest(url,resourceType,frameUrl,receipts){
 const receipt=receipts.get(frameUrl);
 return url===managedBeaconUrl&&resourceType==='script'&&receipt?.comparison?.matchMode==='pinned-managed-beacon'&&receipt.comparison.managedBeaconCount===1&&receipt.comparison.managedBeaconSha256===managedBeaconSha256;
}
function bindDocumentBytes(url,data,receipts,verifiedDocuments){
 const receipt=receipts.get(url);
 assert(receipt,'Document has no successful immutable-verifier receipt');
 const actual=crypto.createHash('sha256').update(data).digest('hex');
 assert.equal(actual,receipt.bodySha256,'Browser HTML differs from M3-verified raw body');
 assert.equal(actual,receipt.comparison.rawBodySha256,'Browser HTML differs from comparison receipt');
 assert.equal(data.length,receipt.comparison.rawBodyBytes,'Browser HTML byte count changed');
 verifiedDocuments.add(url);
 return {url,rawBodySha256:actual,rawBodyBytes:data.length,matchMode:receipt.comparison.matchMode};
}
function permittedBlockedTelemetry(row,verifiedDocuments){
 return row.expectedPinnedTelemetry===true&&row.blockedExternal===true&&row.url===managedBeaconUrl&&verifiedDocuments.has(row.frameUrl);
}
function acceptedNetworkRow(row,verifiedDocuments){
 if(row.blockedExternal||row.failure)return permittedBlockedTelemetry(row,verifiedDocuments);
 return !(row.status>=400);
}
// END receipt-bound telemetry isolation functions.
const httpReceipt=JSON.parse(fs.readFileSync(path.join(workflowRoot,'namyangju-hosted-http/http-receipts.json'),'utf8'));
assert.equal(httpReceipt.passed,true);assert.equal(httpReceipt.phase,'production');
assert.equal(httpReceipt.sourceRevision,expectedSourceRevision);assert.equal(httpReceipt.verificationControlRevision,expectedVerificationRevision);
assert.equal(httpReceipt.verificationHelperSha256,expectedVerificationHelperSha256);
assert.equal(httpReceipt.executionRevision,process.env.GITHUB_SHA);assert.equal(httpReceipt.executionRef,process.env.GITHUB_REF);
assert.equal(httpReceipt.origin,canonicalOrigin);assert.equal(httpReceipt.responses.length,57);
const documentReceipts=new Map();
for(const row of httpReceipt.responses){
 if(row.expectedStatus!==200||!row.route.endsWith('/'))continue;
 const file=path.join(dist,row.route==='/'?'index.html':row.route.slice(1)+'index.html');
 const expected=crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
 assert.equal(row.status,200);assert.equal(row.exactFinalUrl,true);assert.equal(row.url,canonicalOrigin+row.route);
 assert.equal(row.expectedSha256,expected);assert.equal(row.comparison.expectedArtifactSha256,expected);
 assert.equal(row.bodySha256,row.comparison.rawBodySha256);
 assert(['exact','pinned-managed-beacon'].includes(row.comparison.matchMode));
 assert(!documentReceipts.has(row.url),'Duplicate document receipt');documentReceipts.set(row.url,row);
}
assert.equal(documentReceipts.size,37);
const verifiedDocuments=new Set(),documentResponseChecks=[],blockedRequests=new WeakMap();
async function verifyBrowserDocument(response,expectedUrl){
 assert(response,'Missing browser navigation response');assert.equal(response.status(),200);assert.equal(response.url(),expectedUrl);
 const row=bindDocumentBytes(expectedUrl,await response.body(),documentReceipts,verifiedDocuments);documentResponseChecks.push(row);return row;
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
  await context.route('**/*',async route=>{
   if(deniedResponse){await route.abort();return;}
   const request=route.request(),url=request.url();
   if(new URL(url).origin!==origin){
    const frameUrl=request.frame().url();
    const row={viewport:viewport.name,url,frameUrl,blockedExternal:true,expectedPinnedTelemetry:knownManagedBeaconRequest(url,request.resourceType(),frameUrl,documentReceipts)};
    network.push(row);blockedRequests.set(request,row);await route.abort();
   }else await route.continue();
  });
  const page=await context.newPage();
  page.on('console',message=>consoleMessages.push({viewport:viewport.name,page:page.url(),type:message.type(),text:message.text()}));
  page.on('pageerror',error=>pageErrors.push({viewport:viewport.name,page:page.url(),message:error.message}));
  page.on('response',response=>{const row={viewport:viewport.name,url:response.url(),status:response.status()};network.push(row);if([401,403,429].includes(row.status)&&new URL(row.url).origin===origin)deniedResponse=row;});
  page.on('requestfailed',request=>{const blocked=blockedRequests.get(request);if(blocked)blocked.failure=request.failure()?.errorText;else network.push({viewport:viewport.name,url:request.url(),failure:request.failure()?.errorText});});
  for(const target of targets){
   const row={id:target.id,url:target.url,viewport:viewport.name,checks:[],errors:[]};
   try {
    const response=await page.goto(origin+target.url,{waitUntil:'networkidle'});
    assert(!deniedResponse,'Access/rate-limit denial: stop capture without retries');
    assert.equal(response.status(),200,'HTTP status');
    row.initialDocument=await verifyBrowserDocument(response,origin+target.url);
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
      const [hubResponse]=await Promise.all([
        page.waitForResponse(response=>response.request().isNavigationRequest()&&response.url()===origin+hub),
        page.locator(`a[href="${hub}"]:visible`).first().click()
      ]);
      await page.waitForURL(origin+hub);
      assert(!deniedResponse,'Access/rate-limit denial: no back-navigation request');
      row.hubDocument=await verifyBrowserDocument(hubResponse,origin+hub);
      const backResponse=await page.goBack({waitUntil:'networkidle'});
      assert(!deniedResponse,'Access/rate-limit denial: no capture continuation');
      row.backDocument=await verifyBrowserDocument(backResponse,origin+target.url);
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
 const summary={state:'captured-awaiting-independent-pixel-review',commit:expectedSourceRevision,diagnosticWorkflowRevision:process.env.GITHUB_SHA,runId:process.env.GITHUB_RUN_ID,runAttempt:process.env.GITHUB_RUN_ATTEMPT,transportOrigin:origin,canonicalOrigin,phase,hosted,deniedResponse,verificationControlRevision:expectedVerificationRevision,verificationHelperSha256:expectedVerificationHelperSha256,documentResponseChecks,analyticsRequestIntentionallyBlocked:true,analyticsFunctionalityVerified:false,frozenPageCount:frozen.length,provenance:read('src/data/manual-provenance.json'),manualPageCount:manual.length,resultCount:results.length,results,machineChecksPassed:results.length===targets.length*2&&results.every(r=>!r.errors.length)&&pageErrors.length===0&&network.every(r=>acceptedNetworkRow(r,verifiedDocuments)),pixelReview:'pending',productionApproval:'not-issued'};
 fs.writeFileSync(path.join(output,'capture-results.json'),JSON.stringify(summary,null,2)+'\n');
 fs.writeFileSync(path.join(output,'browser-console.json'),JSON.stringify(consoleMessages,null,2)+'\n');
 fs.writeFileSync(path.join(output,'page-errors.json'),JSON.stringify(pageErrors,null,2)+'\n');
 fs.writeFileSync(path.join(output,'network.json'),JSON.stringify(network,null,2)+'\n');
 if(!summary.machineChecksPassed)process.exitCode=1;
 console.log(JSON.stringify({captured:results.length,machineChecksPassed:summary.machineChecksPassed,pixelReview:'pending',productionApproval:'not-issued'}));
}

