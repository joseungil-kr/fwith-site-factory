import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';

// Evidence-only runner: fixed loopback site, no deploy client and no external navigation.
const root=process.cwd(),site=path.join(root,'site-factory/yongin-flower');
const dist=fs.realpathSync(path.join(site,'dist'));
const output=path.join(root,'yongin-preview-evidence');
const origin='http://127.0.0.1:8935';
assert.equal(process.env.SITE_URL,origin);
assert.equal(process.env.SITE_INDEXABLE,'false');
assert.equal(process.env.GITHUB_REF,'refs/heads/manual-yongin-qa-20261007');
assert(process.env.PLAYWRIGHT_INSTALL_ROOT);
fs.mkdirSync(path.join(output,'screenshots'),{recursive:true});
fs.mkdirSync(path.join(output,'html'),{recursive:true});
const require=createRequire(path.join(process.env.PLAYWRIGHT_INSTALL_ROOT,'package.json'));
const {chromium}=require('playwright');
assert.equal(require('playwright/package.json').version,'1.63.0');
const read=file=>JSON.parse(fs.readFileSync(path.join(site,file),'utf8'));
const manual=read('src/data/manual-pages.json').pages;
const products=read('src/data/products.json');
const {artifactDigest}=await import(new URL('../../site-factory/yongin-flower/src/lib/manual-release-gate.mjs',import.meta.url));
const expectedArtifact='7caf84d1504636b10fdd1fd9e38878279f2aefd96efa630bd03296bc4d31bf8a';
assert.equal(artifactDigest(),expectedArtifact,'Exact reviewed bundle');
assert.equal(manual.length,14,'Unexpected review scope');
assert.equal(manual.filter(p=>p.supersedesSnapshotId).length,5,'Existing URL revision count');
assert.equal(manual.filter(p=>!p.supersedesSnapshotId).length,9,'New URL count');
const targets=[{id:'home',url:'/'},{id:'funeral-hub',url:'/funeral/'},{id:'business-hub',url:'/business/'},{id:'event-hub',url:'/event/'},...manual.map(p=>({id:p.pageKey,url:p.url,manual:p}))];
const network=[],consoleMessages=[],pageErrors=[],results=[];
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
await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(8935,'127.0.0.1',resolve);});
let browser;
try {
 browser=await chromium.launch();
 for(const viewport of [{name:'desktop',width:1440,height:1100},{name:'mobile',width:390,height:844}]){
  const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},deviceScaleFactor:1,locale:'ko-KR',reducedMotion:'reduce',serviceWorkers:'block'});
  await context.route('**/*',async route=>{const url=route.request().url();if(new URL(url).origin!==origin){network.push({viewport:viewport.name,url,blockedExternal:true});await route.abort();}else await route.continue();});
  const page=await context.newPage();
  page.setDefaultTimeout(15000);
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
    await page.evaluate(()=>window.scrollTo(0,0));
    const facts=await page.evaluate(()=>({
      robots:document.querySelector('meta[name="robots"]')?.content,
      canonical:document.querySelector('link[rel="canonical"]')?.href,
      revision:document.querySelector('meta[name="site-factory-revision"]')?.content,
      h1:[...document.querySelectorAll('h1')].map(n=>n.textContent),
      width:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth,
      manualMarker:document.querySelector('[data-manual-revision]')?.getAttribute('data-manual-revision'),
      originalSnapshot:document.querySelector('[data-original-snapshot]')?.getAttribute('data-original-snapshot')??null,
      frozenMarker:!!document.querySelector('[data-snapshot-id]'),
      images:[...document.images].map(i=>({src:new URL(i.src).pathname,alt:i.alt,width:i.naturalWidth,height:i.naturalHeight})),
      articleProductImages:[...document.querySelectorAll('.manual-products img')].map(i=>new URL(i.src).pathname),
      phoneLinks:[...document.querySelectorAll('a[href="tel:18440644"]')].length,
      orderLinks:[...document.querySelectorAll('a[href="https://fwith.co.kr"]')].length,
      h1Box:(()=>{const b=document.querySelector('h1')?.getBoundingClientRect();return b?{x:b.x,y:b.y,width:b.width,height:b.height}:null;})(),
      fontFamily:getComputedStyle(document.body).fontFamily
    }));
    row.facts=facts;
    assert.match(facts.robots,/noindex/,'Preview robots');
    assert.equal(decodeURI(facts.canonical),decodeURI(origin+target.url),'Canonical');
    assert.equal(facts.revision,process.env.GITHUB_SHA,'Exact commit marker');
    assert.equal(facts.h1.length,1,'H1 count');
    assert(facts.scrollWidth<=facts.width+1,'Horizontal overflow');
    assert(facts.phoneLinks>0&&facts.orderLinks>0,'Real order anchors');
    assert(facts.images.every(i=>i.width>0&&i.height>0&&i.alt.trim()),'Image decode/alt');
    if(target.manual){
      assert.equal(facts.manualMarker,target.manual.revisionId,'Exact manual revision marker');
      assert.equal(facts.originalSnapshot,target.manual.supersedesSnapshotId??null,'Original snapshot provenance');assert.equal(facts.frozenMarker,false,'No synthetic frozen marker');
      const family=target.manual.category==='funeral'?'funeral_wreath':'congrats_wreath';
      const expected=products.filter(p=>p.category===family).slice(0,2).map(p=>p.image);
      assert.deepEqual(facts.articleProductImages,expected,'Actual rendered product families');
      // Read-only local history round trip; never click phone or merchant links.
      const hub='/'+target.manual.category+'/';
      await page.locator(`.breadcrumbs a[href="${hub}"]:visible`).first().click();
      await page.waitForURL(origin+hub);
      await page.goBack({waitUntil:'networkidle'});
      await page.waitForURL(origin+target.url);
      await page.evaluate(()=>document.fonts.ready);
      for(const img of await page.locator('img').all())await img.scrollIntoViewIfNeeded();
      await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
      await page.evaluate(()=>window.scrollTo(0,0));
    }
    row.checks=['http-200','local-noindex','canonical','exact-commit','one-h1','no-horizontal-overflow','decoded-images','real-cta',...(target.manual?['opaque-marker','product-families','local-back-navigation']:[])];
   } catch(error){row.errors.push(error.stack||String(error));}
   try {
    row.html=`html/${target.id}-${viewport.name}.html`;
    fs.writeFileSync(path.join(output,row.html),await page.content());
    row.htmlSha256=crypto.createHash('sha256').update(fs.readFileSync(path.join(output,row.html))).digest('hex');
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
 const summary={state:'captured-awaiting-independent-pixel-review',commit:process.env.GITHUB_SHA,runId:process.env.GITHUB_RUN_ID,runAttempt:process.env.GITHUB_RUN_ATTEMPT,origin,reviewedArtifactDigest:expectedArtifact,finalArtifactDigest:artifactDigest(),manualPageCount:manual.length,resultCount:results.length,results,machineChecksPassed:results.length===targets.length*2&&results.every(r=>!r.errors.length)&&pageErrors.length===0&&consoleMessages.every(m=>m.type!=='error')&&artifactDigest()===expectedArtifact&&network.every(r=>!r.blockedExternal&&!r.failure&&!(r.status>=400)),pixelReview:'pending',productionApproval:'not-issued'};
 fs.writeFileSync(path.join(output,'capture-results.json'),JSON.stringify(summary,null,2)+'\n');
 fs.writeFileSync(path.join(output,'browser-console.json'),JSON.stringify(consoleMessages,null,2)+'\n');
 fs.writeFileSync(path.join(output,'page-errors.json'),JSON.stringify(pageErrors,null,2)+'\n');
 fs.writeFileSync(path.join(output,'network.json'),JSON.stringify(network,null,2)+'\n');
 const artifactFiles=[];const collect=dir=>{for(const e of fs.readdirSync(dir,{withFileTypes:true})){const f=path.join(dir,e.name);if(e.isDirectory())collect(f);else if(e.isFile())artifactFiles.push({path:path.relative(output,f),sha256:crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex')});}};collect(output);
 fs.writeFileSync(path.join(output,'evidence-sha256.json'),JSON.stringify(artifactFiles,null,2)+'\n');
 if(!summary.machineChecksPassed)process.exitCode=1;
 console.log(JSON.stringify({captured:results.length,machineChecksPassed:summary.machineChecksPassed,pixelReview:'pending',productionApproval:'not-issued'}));
}
