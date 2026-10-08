import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {spawnSync} from 'node:child_process';

// Evidence-only runner: fixed actual production host, no deploy client and no external navigation.
const workflowRoot=process.cwd(),root=path.join(workflowRoot,'target'),site=path.join(root,'site-factory/ansan-flower');
const expectedSourceRevision='a8116e0991c9a009ab1bfa085510fb1066cced9e';
const expectedVerificationRevision='69a7fee6a64a21443be19eca50d734d9652a968c';
const expectedVerificationHelperSha256='ad1b8ba2667f992e39875bbfc4b819578e9f25770ecbf4d20848af6312d59e39';
const dist=fs.realpathSync(path.join(site,'dist'));
const phase=process.env.MANUAL_QA_PHASE;
assert(['production'].includes(phase),'Fixed evidence phase required');
const hosted=process.env.MANUAL_HOSTED_PRODUCTION==='true';
assert(!hosted||phase==='production','Hosted capture is fixed to fixed approved public hostname');
const output=path.join(root,'ansan-'+phase+'-evidence');
const canonicalOrigin='https://ansan.fwith.kr';
const origin=canonicalOrigin;
assert.equal(process.env.SITE_URL,canonicalOrigin);
assert.equal(process.env.SITE_INDEXABLE,'true');
assert.equal(process.env.GITHUB_REF,'refs/heads/manual-ansan-supplemental-public-check-20261008');
assert.equal(phase,'production');assert(hosted);
assert(process.env.PLAYWRIGHT_INSTALL_ROOT);
fs.mkdirSync(path.join(output,'screenshots'),{recursive:true});
const require=createRequire(path.join(process.env.PLAYWRIGHT_INSTALL_ROOT,'package.json'));
const {chromium}=require('playwright');
assert.equal(require('playwright/package.json').version,'1.63.0');
const read=file=>JSON.parse(fs.readFileSync(path.join(site,file),'utf8'));
const manual=read('src/data/manual-page-map.json').pages;
const products=[...read('src/data/products.json'),...read('src/data/site-catalog.json').products];
const {validateManual,manualDigests}=await import(new URL('../../target/site-factory/ansan-flower/src/lib/manual-contract.mjs',import.meta.url));
const artifactDigest=()=>manualDigests(site).bundleHash;
const expectedArtifact='39582656da702e5485ec22e2a60bd517ce07e6513de947b3ad41675d17f27f34';
const native=validateManual(site,process.env);assert(native.production);assert.equal(artifactDigest(),expectedArtifact);
assert.equal(manual.length,24);
const frozen=read('src/data/publish-manifest.json').pages;assert.equal(frozen.length,14);
const walk=dir=>fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)]);
const targets=walk(dist).filter(f=>f.endsWith('/index.html')).sort().map(file=>{
 const rel=path.relative(dist,file),url=rel==='index.html'?'/':'/'+rel.slice(0,-10),html=fs.readFileSync(file,'utf8');
 const manualPage=manual.find(p=>p.url===url),frozenPage=frozen.find(p=>p.url===url);
 const get=re=>html.match(re)?.[1];
 return {id:manualPage?.pageKey??frozenPage?.pageKey??(url==='/'?'home':'r'+crypto.createHash('sha256').update(url).digest('hex').slice(0,24)),url,requestUrl:new URL(url,origin).href,page:manualPage,manual:!!manualPage,expectedRobots:get(/<meta name="robots" content="([^"]*)"/),expectedCanonical:get(/<link rel="canonical" href="([^"]*)"/),expectedSnapshot:get(/data-snapshot-id="([^"]*)"/),expectedManual:get(/data-manual-page="([^"]*)"/)};
});
assert.equal(targets.length,47);assert.equal(new Set(targets.map(t=>t.url)).size,47);
assert.equal(targets.filter(t=>t.manual).length,24);
for(const target of targets){assert(target.url.startsWith('/')&&target.url.endsWith('/')&&!target.url.split('/').includes('..'));assert(target.expectedRobots&&target.expectedCanonical);}
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
 assert.equal(receipt.comparison.expectedArtifactSha256,httpReceipt.expectedSha256,'Browser artifact differs from preflight C2 artifact');
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
 if(row.blockedMethod)return false;
 if(row.blockedExternal||row.failure)return permittedBlockedTelemetry(row,verifiedDocuments);
 return !(row.status>=400);
}
// END receipt-bound telemetry isolation functions.
const httpReceipt=JSON.parse(fs.readFileSync(path.join(workflowRoot,'ansan-hosted-http/http-receipts.json'),'utf8'));
assert.equal(httpReceipt.passed,true);assert.equal(httpReceipt.phase,'production');
for(const [key,env] of [['deploymentRunId','VERIFIED_UPLOAD_RUN_ID'],['deploymentProviderVersion','VERIFIED_PROVIDER_VERSION'],['deploymentAuthorityRevision','VERIFIED_AUTHORITY_REVISION'],['deploymentReceiptSha256','VERIFIED_UPLOAD_RECEIPT_SHA256']]){
 assert(process.env[env]&&process.env[env]!=='PENDING','Pending verified upload pin');assert.equal(httpReceipt[key],process.env[env],'Frozen upload pin mismatch');
}
assert.equal(httpReceipt.deploymentControlRevision,'657b9ce62b1a519ba606f9fb0110aa3679d0931c');assert.equal(httpReceipt.deploymentControlRole,'immutable-M2-hashing-helper-dependency');assert.equal(httpReceipt.deploymentGateRevision,expectedSourceRevision);assert.equal(httpReceipt.deploymentGatePath,'.github/scripts/ansan-supplemental-gate.py');assert.equal(httpReceipt.deploymentGateSha256,'b3d434f814e810bb376fae76d7378347997056068f754ca722d99138c5686322');
assert.equal(httpReceipt.sourceRevision,expectedSourceRevision);assert.equal(httpReceipt.verificationControlRevision,expectedVerificationRevision);
assert.equal(httpReceipt.verificationHelperSha256,expectedVerificationHelperSha256);
assert.equal(httpReceipt.executionRevision,process.env.GITHUB_SHA);assert.equal(httpReceipt.executionRef,process.env.GITHUB_REF);
assert.equal(httpReceipt.origin,canonicalOrigin);assert.equal(httpReceipt.responses.length,70);
const documentReceipts=new Map();
for(const row of httpReceipt.responses){
 if(row.expectedStatus!==200||!row.route.endsWith('/'))continue;
 const file=path.join(dist,row.route==='/'?'index.html':row.route.slice(1)+'index.html');
 const expected=crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
 assert.equal(row.status,200);assert.equal(row.exactFinalUrl,true);assert.equal(row.url,new URL(row.route,canonicalOrigin).href);
 assert.equal(row.expectedSha256,expected);assert.equal(row.comparison.expectedArtifactSha256,expected);
 assert.equal(row.bodySha256,row.comparison.rawBodySha256);
 assert(['exact','pinned-managed-beacon'].includes(row.comparison.matchMode));
 assert(!documentReceipts.has(row.url),'Duplicate document receipt');documentReceipts.set(row.url,row);
}
assert.equal(documentReceipts.size,47);
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
 const checked=spawnSync('python3',[path.join(workflowRoot,'.github/scripts/ansan-hosted-receipts-20261007.py'),'--browser-input',inputFile],{encoding:'utf8'});
 assert.equal(checked.status,0,'Bound immutable M4 rejected actual browser HTML; raw evidence retained');
 const receipt=JSON.parse(fs.readFileSync(receiptFile,'utf8'));
 assert.equal(receipt.sourceRevision,expectedSourceRevision);assert.equal(receipt.verificationControlRevision,expectedVerificationRevision);assert.equal(receipt.verificationHelperSha256,expectedVerificationHelperSha256);assert.equal(receipt.executionRevision,process.env.GITHUB_SHA);assert.equal(receipt.artifactManifestSha256,httpReceipt.artifactManifestSha256);
 const row=bindBrowserReceipt(expectedUrl,data,receipt,prior,navigation.key,verifiedDocuments);documentResponseChecks.push(row);return row;
}
const network=[],consoleMessages=[],pageErrors=[],results=[];
let deniedResponse=null;
let browser,browserVersion=null;
try {
 browser=await chromium.launch();browserVersion=browser.version();
 for(const viewport of [{name:'desktop',width:1440,height:1100},{name:'mobile',width:390,height:844}]){
  let activeNavigation=null,navigationSequence=0;
  const beginNavigation=url=>activeNavigation={key:viewport.name+':'+(++navigationSequence),expectedUrl:url};
  const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},deviceScaleFactor:1,locale:'ko-KR',reducedMotion:'reduce',serviceWorkers:'block'});
  await context.route('**/*',async route=>{
   if(deniedResponse){await route.abort();return;}
   const request=route.request(),url=request.url();
   if(new URL(url).origin!==origin){
    const frameUrl=request.frame().url();
    const row={viewport:viewport.name,url,frameUrl,blockedExternal:true,expectedPinnedTelemetry:knownManagedBeaconRequest(url,request.resourceType(),frameUrl,documentReceipts,activeNavigation),documentKey:activeNavigation?.key};
    network.push(row);blockedRequests.set(request,row);await route.abort();
   }else if(!['GET','HEAD'].includes(request.method())){
    const row={viewport:viewport.name,url,method:request.method(),blockedMethod:true};
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
    beginNavigation(target.requestUrl);
    const response=await page.goto(target.requestUrl,{waitUntil:'networkidle'});
    assert(!deniedResponse,'Access/rate-limit denial: stop capture without retries');
    assert.equal(response.status(),200,'HTTP status');
    row.initialDocument=await verifyBrowserDocument(response,target.requestUrl,activeNavigation);
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
      manualMarker:document.querySelector('[data-manual-page]')?.getAttribute('data-manual-page'),
      originalSnapshot:document.querySelector('[data-original-snapshot]')?.getAttribute('data-original-snapshot')??null,
      contentRevision:document.querySelector('[data-content-revision]')?.getAttribute('data-content-revision'),
      contentSha256:document.querySelector('[data-content-sha256]')?.getAttribute('data-content-sha256'),
      productKeys:[...document.querySelectorAll('.product-section.compact [data-product-key]')].map(e=>e.getAttribute('data-product-key')),
      snapshotId:document.querySelector('[data-snapshot-id]')?.getAttribute('data-snapshot-id'),
      frozenMarker:!!document.querySelector('[data-snapshot-id]'),
      images:[...document.images].map(i=>({src:new URL(i.src).pathname,alt:i.alt,width:i.naturalWidth,height:i.naturalHeight})),
      articleProductImages:[...document.querySelectorAll('.article-products img')].map(i=>new URL(i.src).pathname),
      productCards:[...document.querySelectorAll('.article-products .product-card')].map(p=>({name:p.querySelector('h4')?.textContent,price:p.querySelector('.product-price')?.textContent,image:new URL(p.querySelector('img').src).pathname})),
      phoneLinks:[...document.querySelectorAll('a[href="tel:18440644"]')].length,
      orderLinks:[...document.querySelectorAll('a[href="https://fwith.co.kr"]')].length,
      h1Box:(()=>{const b=document.querySelector('h1')?.getBoundingClientRect();return b?{x:b.x,y:b.y,width:b.width,height:b.height}:null;})(),
      fontFamily:getComputedStyle(document.body).fontFamily
    }));
    row.facts=facts;
    assert.equal(facts.robots,target.expectedRobots,'Exact native indexability including deliberate noindex');
    assert.equal(decodeURI(facts.canonical),decodeURI(target.expectedCanonical),'Exact phase canonical distinct from local transport');
    assert.equal(facts.revision,expectedSourceRevision,'Exact commit marker');
    assert.equal(facts.h1.length,1,'H1 count');assert.equal(facts.width,viewport.width,'Exact viewport width');
    assert(facts.scrollWidth<=facts.width+1,'Horizontal overflow');
    assert(facts.phoneLinks>0&&facts.orderLinks>0,'Real order anchors');
    assert(facts.images.every(i=>i.width>0&&i.height>0&&i.alt.trim()),'Image decode/alt');
    assert.equal(facts.snapshotId,target.expectedSnapshot,'Exact native frozen marker');
    assert.equal(facts.manualMarker,target.expectedManual,'Exact native manual marker');
    if(target.page){
      assert.equal(facts.manualMarker,target.id);assert.equal(facts.frozenMarker,false);
      const selected=target.page.productKeys.map(k=>products.find(p=>p.productKey===k));assert(selected.every(Boolean));
      assert.deepEqual([...facts.articleProductImages].sort(),selected.map(p=>p.image).sort(),'Native Ans manual product image selection');
      for(const product of selected){const card=facts.productCards.find(p=>p.image===product.image);assert(card);assert.equal(card.name,product.name);assert.equal(card.price,new Intl.NumberFormat('ko-KR').format(product.price)+'원');}
      const hub=`/${target.page.category}/`;
      beginNavigation(origin+hub);
      const [hubResponse]=await Promise.all([
        page.waitForResponse(response=>response.request().isNavigationRequest()&&response.url()===origin+hub),
        page.locator(`a[href="${hub}"]:visible`).first().click()
      ]);
      await page.waitForURL(origin+hub);
      assert(!deniedResponse,'Access/rate-limit denial: no back-navigation request');
      row.hubDocument=await verifyBrowserDocument(hubResponse,origin+hub,activeNavigation);
      beginNavigation(target.requestUrl);
      const backResponse=await page.goBack({waitUntil:'networkidle'});
      assert(!deniedResponse,'Access/rate-limit denial: no capture continuation');
      row.backDocument=await verifyBrowserDocument(backResponse,target.requestUrl,activeNavigation);
      await page.waitForURL(target.requestUrl);
      await page.evaluate(()=>document.fonts.ready);
      for(const img of await page.locator('img').all())await img.scrollIntoViewIfNeeded();
      await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
      row.postNavigationImages=await page.evaluate(()=>[...document.images].map(i=>({src:new URL(i.src).pathname,complete:i.complete,width:i.naturalWidth,height:i.naturalHeight})));
      assert(row.postNavigationImages.every(i=>i.complete&&i.width>0&&i.height>0),'Post-navigation decoded images');
      row.afterBackSettledFrame=await settleCaptureFrame(page);row.backNavigationVerified=true;
    }
    await page.keyboard.press('Tab');await page.keyboard.press('Tab');await page.keyboard.press('Tab');await page.evaluate(()=>document.activeElement?.blur());
    row.afterFocusSettledFrame=await settleCaptureFrame(page);
    row.checks=['repeated-focus','http-200','native-production-indexability','canonical','exact-commit','one-h1','no-horizontal-overflow','decoded-images','real-cta',...(target.page?['exact-page-marker','product-families','local-back-navigation']:[])];
   } catch(error){row.errors.push(error.stack||String(error));}
   if(deniedResponse){row.errors.push('Access/rate-limit denial: capture stopped');results.push(row);break;}
   try {
    row.screenshot=`screenshots/${viewport.name}/${target.id}-${viewport.name}.jpg`;
    fs.mkdirSync(path.join(output,'screenshots',viewport.name),{recursive:true});
    row.captureFrame=await settleCaptureFrame(page);assert.equal(page.url(),target.requestUrl,'Screenshot exact requested URL');row.screenshotUrl=page.url();
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

 const summary={state:'captured-awaiting-independent-pixel-review',commit:expectedSourceRevision,diagnosticWorkflowRevision:process.env.GITHUB_SHA,browserVersion,playwrightVersion:'1.63.0',captureEnvironment:{runnerOs:process.env.RUNNER_OS,runnerImage:process.env.ImageOS,runnerImageVersion:process.env.ImageVersion,node:process.version,platform:process.platform,arch:process.arch},runId:process.env.GITHUB_RUN_ID,runAttempt:process.env.GITHUB_RUN_ATTEMPT,transportOrigin:origin,canonicalOrigin,phase,hosted,deniedResponse,deploymentControlRevision:httpReceipt.deploymentControlRevision,deploymentControlRole:httpReceipt.deploymentControlRole,deploymentGateRevision:httpReceipt.deploymentGateRevision,deploymentGatePath:httpReceipt.deploymentGatePath,deploymentGateSha256:httpReceipt.deploymentGateSha256,verificationControlRevision:expectedVerificationRevision,verificationHelperSha256:expectedVerificationHelperSha256,documentResponseChecks,analyticsRequestIntentionallyBlocked:true,analyticsFunctionalityVerified:false,frozenPageCount:frozen.length,nativeSourceBundle:artifactDigest(),manualPageCount:manual.length,resultCount:results.length,results,machineChecksPassed:results.length===targets.length*2&&results.every(r=>!r.errors.length)&&pageErrors.length===0&&network.every(r=>acceptedNetworkRow(r,verifiedDocuments))&&artifactDigest()===expectedArtifact,pixelReview:'pending',productionApproval:'not-issued'};
 fs.writeFileSync(path.join(output,'capture-results.json'),JSON.stringify(summary,null,2)+'\n');
 fs.writeFileSync(path.join(output,'browser-console.json'),JSON.stringify(consoleMessages,null,2)+'\n');
 fs.writeFileSync(path.join(output,'page-errors.json'),JSON.stringify(pageErrors,null,2)+'\n');
 fs.writeFileSync(path.join(output,'network.json'),JSON.stringify(network,null,2)+'\n');
 if(!summary.machineChecksPassed)process.exitCode=1;
 console.log(JSON.stringify({captured:results.length,machineChecksPassed:summary.machineChecksPassed,pixelReview:'pending',productionApproval:'not-issued'}));
}

