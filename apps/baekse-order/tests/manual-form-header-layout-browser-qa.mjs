import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';

const origin='http://127.0.0.1:8787';
const forms=[['manual-invoice/','invoice'],['manual-invoice-vertical/','invoice-vertical'],['simple-receipt/','receipt']];
for(let i=0;i<50;i++){
 try{const r=await fetch(origin+'/manual-invoice/');if(r.ok)break;}catch{}
 if(i===49)throw new Error('Local form server not started');
 await new Promise(resolve=>setTimeout(resolve,200));
}
mkdirSync('qa-manual-forms',{recursive:true});
const browser=await chromium.launch({headless:true});
try{
 const context=await browser.newContext({locale:'ko-KR',timezoneId:'Asia/Seoul',viewport:{width:1440,height:940}});
 const page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 for(const width of [1440,800,390,320]){
  await page.setViewportSize({width,height:940});
  for(const [route,kind] of forms){
   const response=await page.goto(origin+'/'+route,{waitUntil:'networkidle'});
   assert.equal(response.status(),200,route);
   const nav=page.locator('#form-menu'),actions=nav.locator(':scope > a, :scope > button');
   assert.equal(await actions.count(),5);
   assert.equal(await page.locator('#print-form').count(),1);
   assert.equal(await page.locator('#menu-toggle').count(),1);
   assert.equal(await page.locator('#recipient-toggle').count(),1);
   const geo=await page.evaluate(()=>{
    const b=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,right:r.right,bottom:r.bottom}};
    return {documentWidth:document.documentElement.scrollWidth,viewport:document.documentElement.clientWidth,
     sheet:b(document.querySelector('.print-sheet')),
     first:b(document.querySelector('.slip[data-copy="supplier"]')),
     second:b(document.querySelector('.slip[data-copy="recipient"]')),
     rootOverflow:document.querySelector('#print-root').scrollWidth>document.querySelector('#print-root').clientWidth+1};
   });
   if(width<=1100){
    assert.ok(geo.documentWidth<=geo.viewport+1,'Horizontal body scroll '+width+' '+route+JSON.stringify(geo));
    assert.equal(geo.rootOverflow,false,'Form overflow '+width+' '+route+JSON.stringify(geo));
    assert.ok(geo.sheet.w<=width+1,'Sheet should fit screen '+route);
    assert.ok(geo.first.bottom<geo.second.y,'Copies must be top/bottom in mobile '+route);
    assert.equal(await nav.isVisible(),false);
    assert.equal(await page.locator('#menu-toggle').isVisible(),true);
    assert.equal(await page.locator('#print-form').isVisible(),true);
    await page.locator('#menu-toggle').click();
    assert.equal(await nav.isVisible(),true);
    assert.equal(await page.locator('#menu-toggle').getAttribute('aria-expanded'),'true');
    for(const action of await actions.all()){
     const b=await action.boundingBox();
     assert.ok(b.x>=-1&&b.x+b.width<=width+1&&b.height>=40,'Menu touch target out of viewport');
    }
    await page.keyboard.press('Escape');
    assert.equal(await nav.isVisible(),false,'Escape must close menu');
    const card=page.locator('.slip[data-copy="supplier"] .item-table tbody tr');
    assert.equal(await card.count(),kind==='invoice-vertical'?10:15);
    assert.equal(await card.first().evaluate(el=>getComputedStyle(el).display),'grid');
    await page.locator('.slip[data-copy="supplier"] [data-field="item-0-name"]').fill('테스트품목');
    assert.equal((await page.locator('.slip[data-copy="recipient"] [data-mirror="item-0-name"]').innerText()).trim(),'테스트품목');
    await page.locator('#recipient-toggle').click();
    assert.equal(await page.locator('.slip[data-copy="recipient"]').isVisible(),false);
    await page.emulateMedia({media:'print'});
    assert.equal(await page.locator('.slip[data-copy="recipient"]').isVisible(),true,'Collapsed copy must still print');
    const pw=await page.locator('.print-sheet').evaluate(e=>parseFloat(getComputedStyle(e).width));
    assert.ok(pw>(kind==='invoice'?1050:755),'A4 paper width must be unscaled');
    await page.emulateMedia({media:'screen'});
    await page.locator('#recipient-toggle').click();
   }else{
    assert.equal(await nav.isVisible(),true);
    assert.equal(await page.locator('#menu-toggle').isVisible(),false);
    if(kind==='invoice-vertical')assert.ok(geo.first.bottom<geo.second.y);
    else assert.ok(geo.first.right<geo.second.right);
   }
   if(width===390||width===1440)await page.screenshot({path:resolve('qa-manual-forms/responsive-'+width+'-'+kind+'.png'),fullPage:false});
   console.log('STACKED_MOBILE_MORE_MENU_PRINT_PASS',width,kind);
  }
 }
 assert.deepEqual(errors,[],'No JS runtime exceptions');
}finally{await browser.close();}
