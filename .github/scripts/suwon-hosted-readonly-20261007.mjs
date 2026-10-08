import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {spawnSync} from 'node:child_process';

// Read-only hosted supplemental isolated preview capture: immutable deployed source and separate execution revision; no deploy client or external navigation.
const workflowRoot=process.cwd(),root=path.join(workflowRoot,'target'),site=path.join(root,'site-factory/suwon-flower');
const expectedSourceRevision='962a279cfb7e3787a02d89c17847bf5f908b7b70';
const expectedVerificationRevision='69a7fee6a64a21443be19eca50d734d9652a968c';
const expectedVerificationHelperSha256='ad1b8ba2667f992e39875bbfc4b819578e9f25770ecbf4d20848af6312d59e39';
const dist=fs.realpathSync(path.join(site,'dist'));
const phase=process.env.MANUAL_QA_PHASE;
assert(['preview'].includes(phase),'Fixed evidence phase required');
const hosted=process.env.MANUAL_HOSTED_PREVIEW==='true';
assert(!hosted||phase==='preview','Hosted capture is fixed to existing approved production hostname');
const output=path.join(root,'suwon-'+phase+'-evidence');
const canonicalOrigin=phase==='preview'?'https://suwon-flower-guide-qa.joseungil.workers.dev':'https://suwon-flower-guide-qa.joseungil.workers.dev';
const origin=hosted?canonicalOrigin:'http://127.0.0.1:8934';
assert.equal(process.env.SITE_URL,canonicalOrigin);
assert.equal(process.env.SITE_INDEXABLE,'false');
assert.equal(process.env.GITHUB_REF,'refs/heads/manual-suwon-supplemental-hosted-check-20261008');
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
const {selectProducts,productFamilies}=await import(new URL('../../target/site-factory/suwon-flower/src/lib/catalog.mjs',import.meta.url));
assert.equal(manual.length,17,'Unexpected manual review scope');
assert.equal(frozen.length,30,'Unexpected frozen review scope');
const provenance=read('src/data/manual-provenance.json');
assert.equal(provenance.independentReview.status,'passed');
assert.equal(provenance.manualPagesSha256,'6bac9e54f6110a2ceaa39ff4ec6754917815221ecc6001dc221b26efa8e9c77a');
assert.equal(provenance.scopeDigest,'c371c14fd94f320780d8764ab605a684d56f4e0a76ad860b835f36a89a87a96d');
assert.equal(provenance.manualRevisionsSha256,'8e2749262675e4f35b707cf2119ce99f272ed8ff454e086c706ff6aa448dde5c');
const revisions=read('src/data/manual-revisions.json');assert.equal(revisions.length,5);
assert.equal(manual.filter(p=>p.category==='regions').length,4,'Four district detail cards required');
const categories=[...new Set([...frozen,...manual].map(p=>p.category))];
const targets=[{id:'home',url:'/'},...categories.map(cat=>({id:cat+'-hub',url:`/${cat}/`})),...frozen.map(p=>({id:p.pageKey,url:p.url,page:p})),...manual.map(p=>({id:p.pageKey,url:p.url,page:p,manual:true}))];
assert.equal(targets.length,55);
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
const managedBeaconPairs=new Map([
 ['https://static.cloudflareinsights.com/beacon.min.js/v31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495','8a5cd48fb3f913d009a128498bef6fadc43d5561daec87e79f6adcd0bcc903f5'],
 ['https://static.cloudflareinsights.com/beacon.min.js/v4bc70e2c01a94c73b74392e4234840661791215815920','53ed6266d9ab3cb60b83bb38278a519b4b688707f7254f5ffeeeb8bcaa3a5e4c']
]);
function knownManagedBeaconRequest(url,resourceType,frameUrl,receipts,navigation){
 return managedBeaconPairs.has(url)&&resourceType==='script'&&receipts.has(frameUrl)&&navigation?.expectedUrl===frameUrl;
}
function bindBrowserReceipt(url,data,receipt,httpReceipt,documentKey,verifiedDocuments){
 const actual=crypto.createHash('sha256').update(data).digest('hex');
 assert.equal(receipt.passed,true);assert.equal(receipt.url,url);assert.equal(receipt.status,200);
 assert.equal(receipt.comparison.rawBodySha256,actual,'Browser comparison is not bound to its actual bytes');
 assert.equal(receipt.comparison.rawBodyBytes,data.length,'Browser body byte count changed');
 assert.equal(receipt.comparison.expectedArtifactSha256,httpReceipt.expectedSha256,'Browser artifact differs from preflight exact-source artifact');
 assert(['exact','pinned-managed-beacon'].includes(receipt.comparison.matchMode));
 if(receipt.comparison.matchMode==='exact'){assert.equal(receipt.comparison.managedBeaconCount,0);assert.equal(receipt.comparison.managedBeaconSha256,null);}
 else {assert.equal(receipt.comparison.managedBeaconCount,1);assert([...managedBeaconPairs.values()].includes(receipt.comparison.managedBeaconSha256));}
 const row={url,documentKey,httpRawBodySha256:httpReceipt.bodySha256,browserRawBodySha256:actual,browserRawBodyBytes:data.length,comparison:receipt.comparison,bodyFile:receipt.bodyFile};
 assert(!verifiedDocuments.has(documentKey),'Browser navigation receipt duplicated');verifiedDocuments.set(documentKey,row);return row;
}
function permittedBlockedTelemetry(row,verifiedDocuments){
 const receipt=verifiedDocuments.get(row.documentKey);
 return row.expectedPinnedTelemetry===true&&row.blockedExternal===true&&receipt?.url===row.frameUrl&&receipt.comparison.matchMode==='pinned-managed-beacon'&&managedBeaconPairs.get(row.url)===receipt.comparison.managedBeaconSha256;
}
function acceptedNetworkRow(row,verifiedDocuments){
 if(row.blockedExternal||row.failure)return permittedBlockedTelemetry(row,verifiedDocuments);
 return !(row.status>=400);
}
// END receipt-bound telemetry isolation functions.
const httpReceipt=JSON.parse(fs.readFileSync(path.join(workflowRoot,'suwon-hosted-http/http-receipts.json'),'utf8'));
assert.equal(httpReceipt.passed,true);assert.equal(httpReceipt.phase,'preview');
assert.equal(httpReceipt.sourceRevision,expectedSourceRevision);assert.equal(httpReceipt.verificationControlRevision,expectedVerificationRevision);
assert.equal(httpReceipt.verificationHelperSha256,expectedVerificationHelperSha256);
assert.equal(httpReceipt.executionRevision,process.env.GITHUB_SHA);assert.equal(httpReceipt.executionRef,process.env.GITHUB_REF);
assert.equal(httpReceipt.origin,canonicalOrigin);assert.equal(httpReceipt.responses.length,75);
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
assert.equal(documentReceipts.size,55);
const verifiedDocuments=new Map(),documentResponseChecks=[],blockedRequests=new WeakMap();
const declaredHeaderNames=fs.readFileSync(path.join(dist,'_headers'),'utf8').split('\n').filter(line=>/^\s+[^#\s][^:]*:/.test(line)).map(line=>line.trim().split(':',1)[0].toLowerCase());
async function verifyBrowserDocument(response,expectedUrl,navigation){
 assert(response,'Missing browser navigation response');assert.equal(response.status(),200);assert.equal(response.url(),expectedUrl);assert.equal(navigation.expectedUrl,expectedUrl);
 const prior=documentReceipts.get(expectedUrl);assert(prior,'Unknown browser document');
 const data=await response.body(),bodyHash=crypto.createHash('sha256').update(data).digest('hex');
 for(const dir of ['browser-html','browser-input','browser-receipts'])fs.mkdirSync(path.join(output,dir),{recursive:true});
 const bodyFile=path.join(output,'browser-html',bodyHash+'.html');fs.writeFileSync(bodyFile,data);
 const identity=crypto.createHash('sha256').update(expectedUrl+'\0'+bodyHash+'\0'+navigation.key).digest('hex');
 const inputFile=path.join(output,'browser-input',identity+'.json'),receiptFile=path.join(output,'browser-receipts',identity+'.json');
 const allHeaders=await response.allHeaders(),headers=Object.fromEntries([...new Set(['content-type','cf-ray','cf-cache-status','cache-control','x-robots-tag',...declaredHeaderNames])].filter(key=>allHeaders[key]!==undefined).map(key=>[key,allHeaders[key]]));
 fs.writeFileSync(inputFile,JSON.stringify({route:prior.route,url:response.url(),status:response.status(),headers,bodyFile,receiptFile})+'\n');
 const checked=spawnSync('python3',[path.join(workflowRoot,'.github/scripts/suwon-hosted-receipts-20261007.py'),'--browser-input',inputFile],{encoding:'utf8'});
 assert.equal(checked.status,0,'Bound immutable M4 rejected actual browser HTML; raw evidence retained');
 const receipt=JSON.parse(fs.readFileSync(receiptFile,'utf8'));
 assert.equal(receipt.sourceRevision,expectedSourceRevision);assert.equal(receipt.verificationControlRevision,expectedVerificationRevision);assert.equal(receipt.verificationHelperSha256,expectedVerificationHelperSha256);assert.equal(receipt.executionRevision,process.env.GITHUB_SHA);assert.equal(receipt.artifactManifestSha256,httpReceipt.artifactManifestSha256);
 const row=bindBrowserReceipt(expectedUrl,data,receipt,prior,navigation.key,verifiedDocuments);documentResponseChecks.push(row);return row;
}
const network=[],consoleMessages=[],pageErrors=[],results=[];
let deniedResponse=null,browserVersion=null;
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
 browserVersion=browser.version();
 for(const viewport of [{name:'desktop',width:1440,height:1100},{name:'mobile',width:390,height:844}]){
  let activeNavigation=null,navigationSequence=0;
  const beginNavigation=url=>activeNavigation={key:viewport.name+':'+(++navigationSequence),expectedUrl:url};
  const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},deviceScaleFactor:1,locale:'ko-KR',reducedMotion:'reduce'});
  await context.route('**/*',async route=>{
   if(deniedResponse){await route.abort();return;}
   const request=route.request(),url=request.url();
   if(new URL(url).origin!==origin){
    const frameUrl=request.frame().url();
    const row={viewport:viewport.name,url,frameUrl,blockedExternal:true,expectedPinnedTelemetry:knownManagedBeaconRequest(url,request.resourceType(),frameUrl,documentReceipts,activeNavigation),documentKey:activeNavigation?.key};
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
    beginNavigation(origin+target.url);
    const response=await page.goto(origin+target.url,{waitUntil:'networkidle'});
    assert(!deniedResponse,'Access/rate-limit denial: stop capture without retries');
    assert.equal(response.status(),200,'HTTP status');
    row.initialDocument=await verifyBrowserDocument(response,origin+target.url,activeNavigation);
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
      manualMarker:document.querySelector('[data-manual-release]')?.getAttribute('data-manual-release'),
      pageKey:document.querySelector('[data-page-key]')?.getAttribute('data-page-key'),
      manualRevision:document.querySelector('[data-manual-revision]')?.getAttribute('data-manual-revision'),
      addendumDigest:document.querySelector('[data-addendum-digest]')?.getAttribute('data-addendum-digest'),
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
    if(target.id==='home'){assert.equal(await page.locator('.purpose-navigation a[href="/regions/"]:visible').count(),1,'Visible manual district home entry on every viewport');for(const guide of manual.filter(p=>p.category==='regions'))assert(await page.locator('.hub-overview a[href="'+guide.url+'"]:visible').count()===1,'Visible manual district detail link');}
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
      const revision=revisions.find(r=>r.pageKey===target.id);
      if(revision){assert.equal(facts.manualRevision,revision.revisionId,'Separate original-URL manual revision');assert.equal(facts.addendumDigest,revision.sectionsSha256,'Exact addendum digest');for(const section of revision.sectionsToAppend)assert(await page.getByRole('heading',{name:section[0],exact:true}).count()===1,'Rendered exact addendum heading');}
      const expected=selectProducts(target.page,products,productFamilies(target.page).length>3?4:3).map(p=>p.img);
      assert.deepEqual(facts.articleProductImages,expected,'Native renderer product selection');
      const hub=`/${target.page.category}/`;
      beginNavigation(origin+hub);
      const [hubResponse]=await Promise.all([
        page.waitForResponse(response=>response.request().isNavigationRequest()&&response.url()===origin+hub),
        page.locator(`.breadcrumb a[href="${hub}"]:visible`).first().click()
      ]);
      await page.waitForURL(origin+hub);
      assert(!deniedResponse,'Access/rate-limit denial: no back-navigation request');
      row.hubDocument=await verifyBrowserDocument(hubResponse,origin+hub,activeNavigation);
      beginNavigation(origin+target.url);
      const backResponse=await page.goBack({waitUntil:'networkidle'});
      assert(!deniedResponse,'Access/rate-limit denial: no capture continuation');
      row.backDocument=await verifyBrowserDocument(backResponse,origin+target.url,activeNavigation);
      await page.waitForURL(origin+target.url);
      assert(!deniedResponse,'Access/rate-limit denial: no reload request');
      beginNavigation(origin+target.url);
      const reloadResponse=await page.reload({waitUntil:'networkidle'});
      assert(!deniedResponse,'Access/rate-limit denial: no capture continuation');
      row.reloadDocument=await verifyBrowserDocument(reloadResponse,origin+target.url,activeNavigation);
      await page.waitForLoadState('networkidle');
      await page.evaluate(()=>document.fonts.ready);
      for(const img of await page.locator('img').all())await img.scrollIntoViewIfNeeded();
      await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
      assert.equal(await page.locator('[data-page-key]').getAttribute('data-page-key'),target.id,'History restored exact target');
      row.afterBackSettledFrame=await settleCaptureFrame(page);
    }
    assert(!(await page.locator('body').innerText()).includes('**'),'Visible Markdown marker');
    row.checks=['no-visible-markdown-markers','receipt-bound-browser-html','http-200',phase==='preview'?'preview-noindex':'native-production-robots','canonical','exact-commit','one-h1','no-horizontal-overflow','decoded-images','real-cta',...(target.page?['exact-page-marker','product-families','local-back-navigation']:[])];
   } catch(error){row.errors.push(error.stack||String(error));}
   if(deniedResponse){row.errors.push('Access/rate-limit denial: capture stopped');results.push(row);break;}
   try {
    await page.waitForLoadState('networkidle');
    await page.evaluate(()=>document.fonts.ready);
    for(const img of await page.locator('img').all())await img.scrollIntoViewIfNeeded();
    await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
    row.captureFrame=await settleCaptureFrame(page);
    assert.equal(page.url(),origin+target.url,'Screenshot must show exact requested route');
    row.postNavigationImages=await page.evaluate(()=>[...document.images].map(i=>({src:new URL(i.src).pathname,complete:i.complete,width:i.naturalWidth,height:i.naturalHeight})));
    assert(row.postNavigationImages.every(i=>i.complete&&i.width>0&&i.height>0),'Screenshot images decoded after history/reload');
    row.screenshotUrl=page.url();
    row.screenshot=`screenshots/${viewport.name}/${target.id}-${viewport.name}.jpg`;
    fs.mkdirSync(path.join(output,'screenshots',viewport.name),{recursive:true});
    await page.screenshot({path:path.join(output,row.screenshot),type:'jpeg',quality:85,fullPage:true,animations:'disabled'});
    row.screenshotSha256=crypto.createHash('sha256').update(fs.readFileSync(path.join(output,row.screenshot))).digest('hex');
   } catch(error){row.errors.push('Screenshot: '+error.message);}
   results.push(row);
   if(deniedResponse)break;
  }
  await context.close();
  if(deniedResponse)break;
 }
} finally {
 if(browser)await browser.close();
 if(server.listening)await new Promise(resolve=>server.close(resolve));
 const summary={state:'captured-awaiting-independent-pixel-review',commit:expectedSourceRevision,diagnosticWorkflowRevision:process.env.GITHUB_SHA,browserVersion,playwrightVersion:'1.63.0',captureEnvironment:{runnerOs:process.env.RUNNER_OS,runnerImage:process.env.ImageOS,runnerImageVersion:process.env.ImageVersion,node:process.version,platform:process.platform,arch:process.arch},runId:process.env.GITHUB_RUN_ID,runAttempt:process.env.GITHUB_RUN_ATTEMPT,transportOrigin:origin,canonicalOrigin,phase,hosted,deniedResponse,verificationControlRevision:expectedVerificationRevision,verificationHelperSha256:expectedVerificationHelperSha256,documentResponseChecks,analyticsRequestIntentionallyBlocked:true,analyticsFunctionalityVerified:false,frozenPageCount:frozen.length,provenance:read('src/data/manual-provenance.json'),manualPageCount:manual.length,addendumCount:revisions.length,resultCount:results.length,results,machineChecksPassed:results.length===targets.length*2&&results.every(r=>!r.errors.length)&&pageErrors.length===0&&network.every(r=>acceptedNetworkRow(r,verifiedDocuments)),pixelReview:'pending',productionApproval:'not-issued'};
 fs.writeFileSync(path.join(output,'capture-results.json'),JSON.stringify(summary,null,2)+'\n');
 fs.writeFileSync(path.join(output,'browser-console.json'),JSON.stringify(consoleMessages,null,2)+'\n');
 fs.writeFileSync(path.join(output,'page-errors.json'),JSON.stringify(pageErrors,null,2)+'\n');
 fs.writeFileSync(path.join(output,'network.json'),JSON.stringify(network,null,2)+'\n');
 if(!summary.machineChecksPassed)process.exitCode=1;
 console.log(JSON.stringify({captured:results.length,machineChecksPassed:summary.machineChecksPassed,pixelReview:'pending',productionApproval:'not-issued'}));
}
