import fs from 'node:fs';import path from 'node:path';import http from 'node:http';import assert from 'node:assert/strict';import crypto from 'node:crypto';import {createRequire} from 'node:module';
const workflowRoot=process.cwd(),root=path.join(workflowRoot,'target'),site=path.join(root,'site-factory/seongnam-flower'),dist=fs.realpathSync(path.join(site,'dist'));
const expectedSourceRevision='06f4049c2c8e818ef7474e628031c5f901b4ecab';
const phase=process.env.MANUAL_QA_PHASE;
assert(['preview','production'].includes(phase),'Fixed evidence phase required');
const hosted=process.env.MANUAL_HOSTED_PREVIEW==='true';
assert(!hosted||phase==='preview','Hosted capture is limited to the isolated preview Worker');
const canonicalOrigin=phase==='preview'?'https://seongnam-flower-guide-qa.joseungil.workers.dev':'https://seongnam.fwith.kr';
const origin=hosted?canonicalOrigin:'http://127.0.0.1:8936';
const output=path.join(root,'seongnam-'+phase+'-evidence');
assert.equal(process.env.SITE_URL,canonicalOrigin);assert.equal(process.env.SITE_INDEXABLE,phase==='preview'?'false':'true');
assert.equal(process.env.GITHUB_REF,'refs/heads/manual-seongnam-hosted-check-20261007');assert.equal(phase,'preview');assert(hosted);assert(process.env.PLAYWRIGHT_INSTALL_ROOT);
const require=createRequire(path.join(process.env.PLAYWRIGHT_INSTALL_ROOT,'package.json'));const {chromium}=require('playwright');assert.equal(require('playwright/package.json').version,'1.63.0');
const read=n=>JSON.parse(fs.readFileSync(path.join(site,'src/data/'+n+'.json'),'utf8'));
const frozen=read('pages'),manual=read('manual-pages'),products=read('products'),provenance=read('manual-provenance');
const {selectProducts,productFamilies}=await import(new URL('../../target/site-factory/seongnam-flower/src/lib/catalog.mjs',import.meta.url));
assert.equal(frozen.length,22);assert.equal(manual.length,8);assert.equal(provenance.independentReview.status,'passed');assert.equal(provenance.manualPagesSha256,'cb220c408b5b133384142c5dbbda9d2798b3d6e8590587264a874e3fe0343dd4');assert.equal(provenance.scopeDigest,'a3753ce1ee70136e93f4048c0e53d8fa22936d63cd520afb2cef0f9e6f9fd30b');const pages=[...frozen,...manual];
const categories=[...new Set(pages.map(p=>p.category))];const targets=[{id:'home',url:'/'},...categories.map(c=>({id:c+'-hub',url:`/${c}/`})),...pages.map(p=>({id:p.pageKey,url:p.url,page:p}))];assert.equal(targets.length,35);
let deniedResponse=null,browserVersion=null;
const network=[],consoleMessages=[],pageErrors=[],results=[];fs.mkdirSync(path.join(output,'metadata'),{recursive:true});
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
const mimes={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.json':'application/json','.svg':'image/svg+xml','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.txt':'text/plain','.xml':'application/xml'};
const server=http.createServer((req,res)=>{try{if(!['GET','HEAD'].includes(req.method)){res.writeHead(405);res.end();return;}const u=decodeURIComponent(new URL(req.url,origin).pathname);let f=path.resolve(dist,'.'+u);if(f!==dist&&!f.startsWith(dist+path.sep)){res.writeHead(403);res.end();return;}if(fs.existsSync(f)&&fs.statSync(f).isDirectory())f=path.join(f,'index.html');if(!fs.existsSync(f)||!fs.statSync(f).isFile()){res.writeHead(404);res.end();return;}f=fs.realpathSync(f);if(!f.startsWith(dist+path.sep)){res.writeHead(403);res.end();return;}res.writeHead(200,{'Content-Type':mimes[path.extname(f)]||'application/octet-stream','Cache-Control':'no-store'});if(req.method==='HEAD')res.end();else fs.createReadStream(f).pipe(res);}catch{res.writeHead(400);res.end();}});
if(!hosted)await new Promise((r,j)=>{server.once('error',j);server.listen(8936,'127.0.0.1',r);});let browser;
try{browser=await chromium.launch();browserVersion=browser.version();let capture=0;
 for(const viewport of [{name:'desktop',width:1440,height:1100},{name:'mobile',width:390,height:844}]){
  const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},deviceScaleFactor:1,locale:'ko-KR',reducedMotion:'reduce'});
  await context.route('**/*',async r=>{if(deniedResponse){await r.abort();return;}if(new URL(r.request().url()).origin!==origin){network.push({url:r.request().url(),blockedExternal:true});await r.abort();return;}await r.continue();});const page=await context.newPage();
  page.on('console',m=>consoleMessages.push({url:page.url(),type:m.type(),text:m.text()}));page.on('pageerror',e=>pageErrors.push({url:page.url(),error:e.message}));page.on('response',r=>{const row={url:r.url(),status:r.status()};network.push(row);if([401,403,429].includes(row.status)&&new URL(row.url).origin===origin)deniedResponse=row;});page.on('requestfailed',r=>network.push({url:r.url(),error:r.failure()?.errorText}));
  for(const t of targets){const row={id:t.id,url:t.url,viewport:viewport.name,errors:[]};
   try{const response=await page.goto(origin+t.url,{waitUntil:'networkidle'});assert(!deniedResponse,'Access/rate-limit denial: stop without retries');assert.equal(response.status(),200);await page.evaluate(()=>document.fonts.ready);for(const img of await page.locator('img').all())await img.scrollIntoViewIfNeeded();await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));row.settledFrame=await settleCaptureFrame(page);
    const facts=await page.evaluate(()=>({robots:document.querySelector('meta[name="robots"]')?.content,canonical:document.querySelector('link[rel="canonical"]')?.href,revision:document.querySelector('meta[name="site-factory-revision"]')?.content,h1:[...document.querySelectorAll('h1')].map(e=>e.textContent),width:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth,snapshot:document.querySelector('[data-snapshot-id]')?.getAttribute('data-snapshot-id'),manual:document.querySelector('[data-manual-release]')?.getAttribute('data-manual-release'),contentRevision:document.querySelector('[data-content-revision]')?.getAttribute('data-content-revision'),contentSha256:document.querySelector('[data-content-sha256]')?.getAttribute('data-content-sha256'),images:[...document.images].map(i=>({src:new URL(i.src).pathname,alt:i.alt,width:i.naturalWidth,height:i.naturalHeight})),products:[...document.querySelectorAll('.product-section.compact [data-product-key]')].map(e=>e.getAttribute('data-product-key')),phone:[...document.querySelectorAll('a[href="tel:18440644"]')].length,order:[...document.querySelectorAll('a[href="https://fwith.co.kr"]')].length}));row.facts=facts;
    assert.equal(facts.robots,phase==='preview'?'noindex,nofollow,noarchive':'index,follow');assert.equal(facts.canonical,canonicalOrigin+t.url);assert.equal(facts.revision,expectedSourceRevision);assert.equal(facts.h1.length,1);assert(facts.scrollWidth<=facts.width+1);assert(facts.phone>0&&facts.order>0);assert(facts.images.every(i=>i.alt.trim()&&i.width&&i.height));
    if(t.page){assert.equal(facts.h1[0],t.page.h1);if(t.page.sourceType==='manual-authored'){assert.equal(facts.manual,t.page.manualReleaseId);assert.equal(facts.snapshot,undefined);assert.equal(facts.contentRevision,t.page.revisionId);assert.equal(facts.contentSha256,t.page.contentSha256);}else{assert.equal(facts.snapshot,t.page.snapshotId);assert.equal(facts.manual,undefined);}assert.deepEqual(facts.products,selectProducts(t.page,products,productFamilies(t.page).length>3?4:3).map(p=>p.key));}
    if(t.page){const hub=`/${t.page.category}/`;await page.locator(`a[href="${hub}"]:visible`).first().click();await page.waitForURL(origin+hub);assert(!deniedResponse,'Access/rate-limit denial: no back-navigation');await page.goBack({waitUntil:'networkidle'});await page.waitForURL(origin+t.url);await page.evaluate(()=>document.fonts.ready);for(const img of await page.locator('img').all())await img.scrollIntoViewIfNeeded();await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));row.backNavigationVerified=true;}
    // Exercise repeated focus movement after page and back navigation.
    await page.keyboard.press('Tab');await page.keyboard.press('Tab');await page.keyboard.press('Tab');await page.evaluate(()=>document.activeElement?.blur());row.settledFrame=await settleCaptureFrame(page);
    assert(!deniedResponse,'Access/rate-limit denial: no capture');assert.equal(page.url(),origin+t.url,'Screenshot exact requested URL');row.screenshotUrl=page.url();const chunk=String(Math.floor(capture/18)+1).padStart(2,'0');const folder=path.join(output,'screens-'+chunk);fs.mkdirSync(folder,{recursive:true});const file=path.join(folder,t.id+'-'+viewport.name+'.jpg');await page.screenshot({path:file,fullPage:true,type:'jpeg',quality:75,animations:'disabled'});const bytes=fs.readFileSync(file);row.screenshot={file:path.relative(output,file),bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')};capture++;row.status='PASS';
   }catch(e){row.status='FAIL';row.errors.push(e.message);}results.push(row);if(deniedResponse)break;
  }await context.close();if(deniedResponse)break;
 }
 assert(!deniedResponse,'Access/rate-limit denial: no later requests');const check404=await fetch(origin+'/definitely-missing/');assert(![401,403,429].includes(check404.status),'Access/rate-limit denial on 404');assert.equal(check404.status,404);assert(network.every(r=>!r.blockedExternal&&!r.error&&!(r.status>=400)),'Unexpected browser network failure');assert.equal(results.length,70);assert.equal(pageErrors.length,0);assert(results.every(x=>x.status==='PASS'),'Capture integrity failures');
 for(let c=1;c<=4;c++){const folder=path.join(output,'screens-'+String(c).padStart(2,'0'));const files=fs.readdirSync(folder);assert(files.length<=18);assert(files.reduce((n,f)=>n+fs.statSync(path.join(folder,f)).size,0)<24*1024*1024,'Screenshot chunk above 24 MiB');}
}finally{await browser?.close();if(!hosted)server.close();const write=(n,o)=>fs.writeFileSync(path.join(output,'metadata',n+'.json'),JSON.stringify(o,null,2)+'\n');write('capture-results',results);write('network',network);write('browser-console',consoleMessages);write('page-errors',pageErrors);write('revision',{commit:expectedSourceRevision,diagnosticWorkflowRevision:process.env.GITHUB_SHA,browserVersion,playwrightVersion:'1.63.0',deniedResponse,captureEnvironment:{runnerOs:process.env.RUNNER_OS,runnerImage:process.env.ImageOS,runnerImageVersion:process.env.ImageVersion,node:process.version,platform:process.platform,arch:process.arch},runId:process.env.GITHUB_RUN_ID,runAttempt:process.env.GITHUB_RUN_ATTEMPT,manualPagesSha256:provenance.manualPagesSha256,scopeDigest:provenance.scopeDigest,phase,hosted,nativeReview:'passed',releaseAuthority:'separate-main-gate',transportOrigin:origin,canonicalOrigin});}
console.log(JSON.stringify({captures:70,targets:35,widths:[1440,390],status:'PASS',phase,hosted,independentPixelReview:'pending'}));
