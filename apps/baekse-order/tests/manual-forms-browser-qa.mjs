import {chromium} from 'playwright';
import {mkdirSync} from 'node:fs';
import assert from 'node:assert/strict';
const base='http://127.0.0.1:8787';
mkdirSync('qa-manual-forms',{recursive:true});
for(let i=0;i<80;i++){
 try {const r=await fetch(base+'/manual-invoice/');if(r.ok&&(await r.text()).includes('id="print-form"'))break}
 catch{}
 if(i===79)throw new Error('Manual invoice not served');
 await new Promise(resolve=>setTimeout(resolve,1000));
}
const browser=await chromium.launch({headless:true});
try{
 const context=await browser.newContext({viewport:{width:1440,height:960},locale:'ko-KR',timezoneId:'Asia/Seoul'});
 const page=await context.newPage();
 const errors=[],writes=[];
 page.on('pageerror',err=>errors.push(err.message));
 page.on('request',req=>{if(req.method()!=='GET')writes.push(req.method()+' '+req.url())});
 const testWithinPage=async()=>{
  const geometry=await page.locator('.print-sheet').evaluate(el=>{
   const sheet=el.getBoundingClientRect();
   const slips=[...el.querySelectorAll('.slip')].map(s=>{
     const r=s.getBoundingClientRect();
     return {inside:r.top>=sheet.top-1&&r.bottom<=sheet.bottom+1&&r.left>=sheet.left-1&&r.right<=sheet.right+1,
       overflow:s.scrollHeight>s.clientHeight+3};
   });
   return {slips};
  });
  assert.ok(geometry.slips.every(s=>s.inside&&!s.overflow),'Form overflows physical paper: '+JSON.stringify(geometry));
 };
 await page.goto(base+'/manual-invoice/',{waitUntil:'networkidle'});
 assert.equal(await page.locator('.slip').count(),2,'one supplier + one recipient copy');
 assert.equal(await page.locator('[data-copy=supplier] .item-table tbody tr').count(),15);
 assert.equal(await page.locator('[data-copy=recipient] .item-table tbody tr').count(),15);
 await page.locator('[data-copy=supplier] [data-field=supplier]').fill('백세푸드 테스트');
 await page.locator('[data-copy=supplier] [data-field=buyer]').fill('안산 중앙점 테스트');
 await page.locator('[data-copy=supplier] [data-field=supplierNo]').fill('123-45-67890');
 await page.locator('[data-copy=supplier] [data-field=item-0-name]').fill('잉어반죽');
 await page.locator('[data-copy=supplier] [data-field=item-0-qty]').fill('2');
 await page.locator('[data-copy=supplier] [data-field=item-0-price]').fill('12500');
 await page.locator('[data-copy=supplier] [data-field=previous]').fill('100000');
 await page.locator('[data-copy=supplier] [data-field=paid]').fill('30000');
 assert.equal((await page.locator('[data-copy=recipient] [data-mirror=supplier]').innerText()).trim(),'백세푸드 테스트');
 assert.equal((await page.locator('[data-copy=recipient] [data-mirror=buyer]').innerText()).trim(),'안산 중앙점 테스트');
 assert.equal((await page.locator('[data-copy=recipient] [data-mirror=item-0-name]').innerText()).trim(),'잉어반죽');
 assert.equal((await page.locator('[data-copy=recipient] [data-mirror=item-0-qty]').innerText()).trim(),'2');
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=item-0-amount]').innerText()).trim(),'25,000');
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=supply]').first().innerText()).trim(),'25,000');
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=tax]').innerText()).trim(),'0');
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=grand]').first().innerText()).trim(),'125,000');
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=balance]').innerText()).trim(),'95,000');
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=invoiceTotal]').innerText()).trim(),'25,000','Transaction total excludes previous balance');
 assert.equal((await page.locator('[data-copy=supplier] [data-tax-caption]').innerText()).trim(),'합계금액(부가세별도)');
 await page.locator('#vat-toggle').click();
 assert.equal((await page.locator('#vat-toggle').innerText()).trim(),'부가세 별도');
 assert.equal(await page.locator('#vat-toggle').getAttribute('aria-pressed'),'true');
 assert.equal((await page.locator('[data-copy=supplier] [data-tax-caption]').innerText()).trim(),'합계금액(부가세포함)');
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=invoiceTotal]').innerText()).trim(),'27,500');
 assert.equal((await page.locator('[data-copy=recipient] [data-mirror=vatMode]').innerText()).trim(),'10%');
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=tax]').innerText()).trim(),'2,500');
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=grand]').first().innerText()).trim(),'127,500');
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=balance]').innerText()).trim(),'97,500');
 await testWithinPage();
 await page.screenshot({path:'qa-manual-forms/manual-invoice-desktop.png',fullPage:true});
 await page.pdf({path:'qa-manual-forms/manual-invoice-A4-landscape.pdf',printBackground:true,preferCSSPageSize:true});
 assert.equal((await page.locator('.seo-guide').isVisible()),true,'Search help is visible on screen');
 await page.emulateMedia({media:'print'});
 assert.equal(await page.locator('.seo-guide').isVisible(),false,'Search help must not print');
 await page.emulateMedia({media:null});
 // A clean blank-print tab must not alter the current entry in the original tab.
 const blankPopupPromise=page.waitForEvent('popup');
 await page.locator('#blank-pdf').click();
 const blank=await blankPopupPromise;
 await blank.waitForLoadState('load');
 await blank.locator('[data-copy=supplier] [data-field=supplier]').waitFor();
 assert.ok(blank.url().includes('blank=1'));
 assert.equal(await blank.locator('[data-copy=supplier] [data-field=supplier]').inputValue(),'');
 assert.equal(await blank.locator('[data-copy=supplier] [data-field=writtenDate]').inputValue(),'');
 assert.equal((await blank.locator('[data-copy=recipient] [data-calc=invoiceTotal]').innerText()).trim(),'');
 assert.equal((await blank.locator('[data-copy=recipient] [data-mirror=buyer]').innerText()).trim(),'');
 await blank.pdf({path:'qa-manual-forms/blank-manual-invoice.pdf',printBackground:true,preferCSSPageSize:true});
 await blank.close();
 assert.equal(await page.locator('[data-copy=supplier] [data-field=supplier]').inputValue(),'백세푸드 테스트');
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=invoiceTotal]').innerText()).trim(),'27,500');
 await page.locator('#vat-toggle').click();
 assert.equal((await page.locator('#vat-toggle').innerText()).trim(),'부가세 자동입력');
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=tax]').innerText()).trim(),'0');
 await page.locator('#vat-toggle').click();
 await page.evaluate(()=>{window.__printWasCalled=false;window.print=()=>{window.__printWasCalled=true}});
 await page.locator('#print-form').click();
 assert.equal(await page.evaluate(()=>window.__printWasCalled),true,'Invoice print button');
 page.on('dialog',d=>d.accept());
 await page.locator('#clear-form').click();
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=supply]').innerText()).trim(),'0');
 assert.equal((await page.locator('[data-copy=recipient] [data-mirror=supplier]').innerText()).trim(),'');

 await page.goto(base+'/simple-receipt/',{waitUntil:'networkidle'});
 assert.equal(await page.locator('.slip').count(),2);
 assert.equal(await page.locator('[data-copy=supplier] .item-table tbody tr').count(),15);
 assert.equal(await page.locator('[data-copy=recipient] .item-table tbody tr').count(),15);
 await page.locator('[data-copy=supplier] [data-field=supplier]').fill('영수증 공급자');
 await page.locator('[data-copy=supplier] [data-field=buyer]').fill('영수증 고객');
 await page.locator('[data-copy=supplier] [data-field=item-0-name]').fill('꼬치어묵');
 await page.locator('[data-copy=supplier] [data-field=item-0-qty]').fill('3');
 await page.locator('[data-copy=supplier] [data-field=item-0-price]').fill('8000');
 await page.locator('[data-copy=supplier] [data-field=item-14-name]').fill('추가 품목 15번');
 await page.locator('[data-copy=supplier] [data-field=item-14-qty]').fill('2');
 await page.locator('[data-copy=supplier] [data-field=item-14-price]').fill('3500');
 assert.equal(await page.locator('[data-copy=supplier] .parties tr:nth-child(2) th').first().innerText(),'공급자(상호)');
 assert.equal(await page.locator('[data-copy=recipient] .parties tr:nth-child(4) th').first().innerText(),'공급받는자(상호)');
 assert.equal((await page.locator('[data-copy=recipient] [data-mirror=item-14-name]').innerText()).trim(),'추가 품목 15번');
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=item-14-amount]').innerText()).trim(),'7,000');
 assert.equal((await page.locator('[data-copy=recipient] [data-mirror=supplier]').innerText()).trim(),'영수증 공급자');
 assert.equal((await page.locator('[data-copy=recipient] [data-mirror=buyer]').innerText()).trim(),'영수증 고객');
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=grand]').first().innerText()).trim(),'31,000');
 assert.equal((await page.locator('[data-copy=recipient] [data-calc=item-0-amount]').innerText()).trim(),'24,000');
 await testWithinPage();
 const roleVisuals=await page.locator('.print-sheet').evaluate(sheet=>{
   const style=sel=>getComputedStyle(sheet.querySelector(sel));
   return {
     leftBorder:style('[data-copy="supplier"]').borderTopColor,
     rightBorder:style('[data-copy="recipient"]').borderTopColor,
     leftHeading:style('[data-copy="supplier"] .form-head').backgroundColor,
     rightHeading:style('[data-copy="recipient"] .form-head').backgroundColor,
     cutWidth:style('.cut-marker').borderLeftWidth
   };
 });
 assert.notEqual(roleVisuals.leftBorder,roleVisuals.rightBorder,'Supplier vs recipient borders must have distinct colors');
 assert.notEqual(roleVisuals.leftHeading,roleVisuals.rightHeading,'Headers must look visibly different');
 assert.ok(parseFloat(roleVisuals.cutWidth)>1,'Central cut guide should be visible');
 assert.equal(await page.locator('h1').count(),1,'Only one SEO h1');
 assert.ok(await page.locator('.seo-guide').isVisible(),'Receipt help must be visible on screen');
 await page.screenshot({path:'qa-manual-forms/simple-receipt-desktop.png',fullPage:true});
 await page.emulateMedia({media:'print'});
 assert.equal(await page.locator('.seo-guide').isVisible(),false,'SEO instructions must not be included in PDF/print');
 await page.emulateMedia({media:null});
 await page.pdf({path:'qa-manual-forms/simple-receipt-A4-portrait.pdf',printBackground:true,preferCSSPageSize:true});
 await page.evaluate(()=>{window.__printWasCalled=false;window.print=()=>{window.__printWasCalled=true}});
 await page.locator('#print-form').click();
 assert.equal(await page.evaluate(()=>window.__printWasCalled),true,'Receipt print button');
 assert.deepEqual(errors,[],'Browser JS errors');
 assert.deepEqual(writes,[],'No server write requests from standalone forms');
 console.log('MANUAL_FORMS_BROWSER_PASS: live mirroring, invoice 15 rows A4 landscape, receipt 15 rows A4 portrait, colored roles, print-only template, no server writes');
}finally{await browser.close()}
