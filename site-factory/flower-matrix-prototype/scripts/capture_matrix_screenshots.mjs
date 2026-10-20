import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const outRoot='screenshots';
fs.mkdirSync(outRoot,{recursive:true});
const origins={A:process.env.PREVIEW_A||'http://127.0.0.1:4173',B:process.env.PREVIEW_B||'http://127.0.0.1:4174'};
const routes=[
  {key:'home',path:'/'},
  {key:'region-hub-ansan',path:'/ansan/'},
  {key:'product-hub-funeral',path:'/products/funeral-wreath/'},
  {key:'detail-funeral',path:'/ansan/funeral-wreath/'},
  {key:'detail-congrats',path:'/ansan/congrats-wreath/'},
  {key:'detail-orchid',path:'/ansan/promotion-orchid/'},
  {key:'detail-bouquet',path:'/ansan/bouquet/'},
  {key:'detail-b-variant',path:'/uijeongbu/funeral-wreath/'}
];
const viewports=[
  {key:'desktop',width:1440,height:1000},
  {key:'mobile-392',width:392,height:844}
];
const browser=await chromium.launch({headless:true});
const results=[];
try{
 for(const [instance,origin] of Object.entries(origins)){
  for(const viewport of viewports){
   const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},deviceScaleFactor:1});
   for(const route of routes){
    const page=await context.newPage();
    const errors=[];
    page.on('pageerror',e=>errors.push('pageerror:'+e.message));
    const response=await page.goto(origin+route.path,{waitUntil:'networkidle',timeout:45000});
    await page.evaluate(async()=>{await document.fonts.ready;for(const img of document.images)img.loading='eager';await Promise.all([...document.images].map(img=>img.decode().catch(()=>null)));});
    const check=await page.evaluate(()=>{
      const visible=e=>!!e&&e.getClientRects().length>0&&getComputedStyle(e).visibility!=='hidden'&&getComputedStyle(e).display!=='none';
      const h1=[...document.querySelectorAll('h1')];
      const faq=document.querySelector('.faq');
      const phone=[...document.querySelectorAll('a[href^="tel:"]')].find(visible);
      const order=[...document.querySelectorAll('a[href="https://fwith.co.kr"]')].find(visible);
      const images=[...document.images].map(img=>({src:img.getAttribute('src'),alt:img.alt,widthAttr:img.getAttribute('width'),heightAttr:img.getAttribute('height'),loaded:img.complete&&img.naturalWidth>0,naturalWidth:img.naturalWidth,naturalHeight:img.naturalHeight,visible:visible(img)}));
      const paras=[...document.querySelectorAll('main p')].filter(visible);
      const h1Style=h1[0]?getComputedStyle(h1[0]):null;
      const pSizes=paras.map(p=>parseFloat(getComputedStyle(p).fontSize));
      return {
        viewport:{width:innerWidth,height:innerHeight},
        documentWidth:document.documentElement.scrollWidth,bodyWidth:document.body.scrollWidth,
        horizontalOverflow:document.documentElement.scrollWidth>innerWidth+1||document.body.scrollWidth>innerWidth+1,
        title:document.title,h1Count:h1.length,h1Text:h1[0]?.innerText||'',
        h1FontSize:h1Style?parseFloat(h1Style.fontSize):0,
        bodyTextLength:document.body.innerText.trim().length,
        faqVisible:visible(faq)&&!!faq.querySelector('h2')&&visible(faq.querySelector('h2')),
        faqText:faq?.innerText?.slice(0,120)||'',
        phoneVisible:!!phone,orderVisible:!!order,
        images,paragraphFontMin:pSizes.length?Math.min(...pSizes):0,
        screenshotsReady:document.readyState==='complete'
      };
    });
    const name=instance+'-'+viewport.key+'-'+route.key+'.png';
    await page.screenshot({path:path.join(outRoot,name),fullPage:true,animations:'disabled'});
    const failures=[];
    if(!response||response.status()!==200)failures.push('http-'+(response?.status()??'no-response'));
    if(check.horizontalOverflow)failures.push('horizontal-overflow');
    if(check.h1Count!==1)failures.push('h1-count');
    if(!check.title||check.bodyTextLength<350)failures.push('thin-or-missing-content');
    if(!check.faqVisible)failures.push('faq-not-visible');
    if(!check.phoneVisible||!check.orderVisible)failures.push('cta-not-visible');
    if(check.images.some(i=>!i.loaded||!i.alt?.trim()||!i.widthAttr||!i.heightAttr))failures.push('image-load-or-alt-dimensions');
    if(check.paragraphFontMin<14)failures.push('paragraph-font-too-small');
    if(errors.length)failures.push('browser-errors');
    results.push({instance,viewport:viewport.key,route:route.path,screenshot:name,httpStatus:response?.status()??null,checks:check,consoleErrors:errors,failures});
    await page.close();
   }
   await context.close();
  }
 }
}finally{await browser.close();}
const report={schemaVersion:1,runMode:'build-only-localhost-preview',captures:results.length,viewports:viewports.map(x=>x.key),routes:routes.map(x=>x.path),results,failed:results.filter(x=>x.failures.length)};
fs.writeFileSync(path.join(outRoot,'visual-qa.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({captures:report.captures,failed:report.failed.length,failures:report.failed.map(x=>({instance:x.instance,viewport:x.viewport,route:x.route,failures:x.failures}))},null,2));
if(report.failed.length)process.exitCode=1;
