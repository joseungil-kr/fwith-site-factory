import {chromium} from 'playwright';
import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';

const host='http://127.0.0.1:8787';
for(let i=0;i<65;i++){
 try{
  const response=await fetch(host+'/manual-invoice-vertical/');
  if(response.ok&&(await response.text()).includes('data-form="invoice-vertical"'))break;
 }catch{}
 if(i===64)throw new Error('Vertical invoice page not served');
 await new Promise(resolve=>setTimeout(resolve,500));
}
mkdirSync('qa-manual-vertical',{recursive:true});
const browser=await chromium.launch({headless:true});
try{
 const context=await browser.newContext({viewport:{width:1440,height:1000},locale:'ko-KR',timezoneId:'Asia/Seoul'});
 const page=await context.newPage();
 const pageErrors=[],networkWrites=[];
 page.on('pageerror',e=>pageErrors.push(e.message));
 page.on('request',r=>{if(r.method()!=='GET')networkWrites.push(r.method()+' '+r.url())});
 await page.goto(host+'/manual-invoice-vertical/',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>document.querySelectorAll('.slip').length===2);
 assert.equal(await page.locator('.print-sheet.invoice.invoice-vertical').count(),1);
 assert.equal(await page.locator('.slip[data-copy="supplier"]').count(),1);
 assert.equal(await page.locator('.slip[data-copy="recipient"]').count(),1);
 for(const copy of ['supplier','recipient'])
  assert.equal(await page.locator('.slip[data-copy="'+copy+'"] .item-table tbody tr').count(),10);
 const upperInputNames=await page.locator('[data-copy="supplier"] [data-field]').evaluateAll(nodes=>nodes.map(n=>n.dataset.field).sort());
 const original=await context.newPage();
 await original.goto(host+'/manual-invoice/',{waitUntil:'networkidle'});
 const oldInputNames=await original.locator('[data-copy="supplier"] [data-field]').evaluateAll(nodes=>nodes.map(n=>n.dataset.field).sort());
 assert.equal(await original.locator('[data-copy="supplier"] .item-table tbody tr').count(),15);
 const oldShared=oldInputNames.filter(name=>name!=='buyerContact'&&!/^item-(1[0-4])-/u.test(name));
 const verticalShared=upperInputNames.filter(name=>!['buyerNo','buyerPhone'].includes(name));
 assert.deepEqual(verticalShared,oldShared,'Finance and 10 shared item rows must retain identical field names');
 assert.ok(upperInputNames.includes('buyerNo'),'Recipient registration number required');
 assert.ok(upperInputNames.includes('buyerPhone'),'Recipient phone required');
 assert.ok(!upperInputNames.includes('buyerContact'),'New 4-field layout replaces separate contact-person entry');
 const originalInk=await original.locator('.slip[data-copy="supplier"]').evaluate(el=>getComputedStyle(el).borderTopColor);
 assert.notEqual(originalInk,'rgb(154, 38, 48)','Existing A4 landscape invoice must not inherit the new red ink');
 await original.close();
 const expectedEntries=[['상호','buyer','supplier'],['등록번호','buyerNo','supplierNo'],['소재지','buyerAddress','supplierAddress'],['연락처','buyerPhone','supplierPhone']];
 for(const copy of ['supplier','recipient']){
  const table=page.locator('.slip[data-copy="'+copy+'"] .vertical-party-table');
  assert.equal(await table.locator('tbody tr').count(),4,'There must be four business information rows');
  assert.equal(await table.locator('col').count(),6,'Buyer and supplier each have 3 physical columns');
  const heads=await table.locator('.vertical-side-label').allTextContents();
  assert.deepEqual(heads,['공급받는자','공급자']);
  for(const label of await table.locator('.vertical-side-label').all()){
   assert.equal(await label.getAttribute('rowspan'),'4','Vertical title spans exactly four rows');
   assert.equal(await label.evaluate(el=>getComputedStyle(el).writingMode),'vertical-rl');
   assert.equal(await label.evaluate(el=>getComputedStyle(el).textOrientation),'upright');
  }
  for(let n=0;n<4;n++){
   const row=table.locator('tbody tr').nth(n);
   assert.deepEqual(await row.locator('th:not(.vertical-side-label)').allTextContents(),[expectedEntries[n][0],expectedEntries[n][0]]);
   const cells=await row.locator('td').all();
   assert.equal(cells.length,2);
   for(let j=0;j<2;j++){
    const field=expectedEntries[n][j+1];
    const target=copy==='supplier'?cells[j].locator('input[data-field="'+field+'"]'):cells[j].locator('[data-mirror="'+field+'"]');
    assert.equal(await target.count(),1,'Correct '+(j===0?'buyer':'supplier')+' field on row '+n);
   }
  }
 }
 const geometry=await page.locator('.print-sheet').evaluate(sheet=>{
  const box=sheet.getBoundingClientRect();
  const top=sheet.querySelector('[data-copy="supplier"]');
  const bottom=sheet.querySelector('[data-copy="recipient"]');
  const a=top.getBoundingClientRect(),b=bottom.getBoundingClientRect();
  const cut=sheet.querySelector('.cut-marker');
  const cutStyle=getComputedStyle(cut);
  const labelStyle=getComputedStyle(sheet.querySelector('.cut-label'));
  return {
   w:box.width,h:box.height,
   top:a.top,bottom:a.bottom,
   otherTop:b.top,otherBottom:b.bottom,
   horizontalCut:cutStyle.borderTopStyle,
   verticalCut:cutStyle.borderLeftStyle,
   cutRotation:labelStyle.transform,
   cutTop:cut.getBoundingClientRect().top,
   topOverflow:top.scrollHeight>top.clientHeight+3,
   bottomOverflow:bottom.scrollHeight>bottom.clientHeight+3,
   within:a.top>=box.top-1&&b.bottom<=box.bottom+1&&a.left>=box.left-1&&b.right<=box.right+1
  };
 });
 assert.ok(geometry.w<geometry.h,'A4 preview must be portrait');
 assert.ok(geometry.top<geometry.otherTop,'Supplier must be on top');
 assert.ok(geometry.bottom<geometry.otherTop,'Two copies must have a cut gap');
 assert.equal(geometry.horizontalCut,'dashed');
 assert.equal(geometry.verticalCut,'none');
 assert.equal(geometry.cutRotation,'none','Horizontal cut should have readable, unrotated label');
 assert.ok(Math.abs(geometry.cutTop-(geometry.top+(geometry.otherBottom-geometry.top)/2))<18,'Cut should be near physical middle');
 assert.equal(geometry.topOverflow,false,'Top slip overflowed');
 assert.equal(geometry.bottomOverflow,false,'Bottom slip overflowed');
 assert.equal(geometry.within,true,'Slips must fit inside A4 page');
 const fill=async(k,v)=>page.locator('[data-copy="supplier"] [data-field="'+k+'"]').fill(v);
 await fill('writtenDate','2026-11-10');
 await fill('supplier','백세푸드');
 await fill('supplierNo','304-04-85025');
 await fill('supplierPhone','031-407-0103');
 await fill('supplierAddress','경기 안산 공급자주소');
 await fill('buyer','안산중앙점');
 await fill('buyerNo','110-11-11011');
 await fill('buyerPhone','010-1234-5678');
 await fill('buyerAddress','경기 안산 거래처주소');
 await fill('item-0-name','잉어반죽');
 await fill('item-0-qty','2');
 await fill('item-0-price','12500');
 await fill('item-9-name','팥앙금');
 await fill('item-9-qty','1');
 await fill('item-9-price','8000');
 await fill('previous','100000');
 await fill('paid','30000');
 assert.equal((await page.locator('[data-copy="recipient"] [data-mirror=buyer]').innerText()).trim(),'안산중앙점');
 assert.equal((await page.locator('[data-copy="recipient"] [data-mirror=buyerNo]').innerText()).trim(),'110-11-11011');
 assert.equal((await page.locator('[data-copy="recipient"] [data-mirror=buyerPhone]').innerText()).trim(),'010-1234-5678');
 assert.equal((await page.locator('[data-copy="recipient"] [data-mirror=supplier]').innerText()).trim(),'백세푸드');
 assert.equal((await page.locator('[data-copy="recipient"] [data-mirror=item-9-name]').innerText()).trim(),'팥앙금');
 assert.equal((await page.locator('[data-copy="recipient"] [data-calc=item-0-amount]').innerText()).trim(),'25,000');
 assert.equal((await page.locator('[data-copy="recipient"] [data-calc=item-9-amount]').innerText()).trim(),'8,000');
 assert.equal((await page.locator('[data-copy="recipient"] [data-calc=supply]').first().innerText()).trim(),'33,000');
 assert.equal((await page.locator('[data-copy="recipient"] [data-calc=invoiceTotal]').innerText()).trim(),'33,000');
 assert.equal((await page.locator('[data-copy="recipient"] [data-calc=grand]').first().innerText()).trim(),'133,000');
 await page.locator('#vat-toggle').click();
 assert.equal((await page.locator('#vat-toggle').innerText()).trim(),'부가세 별도');
 assert.equal((await page.locator('[data-copy="recipient"] [data-calc=tax]').innerText()).trim(),'3,300');
 assert.equal((await page.locator('[data-copy="recipient"] [data-calc=invoiceTotal]').innerText()).trim(),'36,300');
 assert.equal((await page.locator('[data-copy="recipient"] [data-calc=grand]').first().innerText()).trim(),'136,300');
 assert.equal((await page.locator('[data-copy="recipient"] [data-calc=balance]').innerText()).trim(),'106,300');
 for(const media of ['screen','print']){
  await page.emulateMedia({media});
  for(const [copy,expected] of [['supplier','rgb(154, 38, 48)'],['recipient','rgb(36, 74, 137)']]){
   const ink=await page.locator('.slip[data-copy="'+copy+'"]').evaluate(slip=>{
    const get=(selector,property)=>getComputedStyle(slip.querySelector(selector))[property];
    return {
     border:getComputedStyle(slip).borderTopColor,
     title:get('.form-head>strong','color'),
     heading:get('.form-head','borderLeftColor'),
     headingBackground:get('.form-head','backgroundColor'),
     copyLabel:get('.copy-name','color'),
     tableLabel:get('.vertical-party-table th','color'),
     tableGrid:get('.item-table td','borderTopColor'),
     typedText:slip.dataset.copy==='supplier'?get('input[data-field="supplier"]','color'):null,
     calculatedText:get('.calculated','color'),
     mirrorText:slip.dataset.copy==='recipient'?get('[data-mirror="buyer"]','color'):null
    };
   });
   for(const key of ['border','title','heading','copyLabel','tableLabel','tableGrid','typedText','calculatedText']){
    if(key==='typedText'&&copy==='recipient')continue;
    assert.equal(ink[key],expected,media+' '+copy+' '+key+' must use the requested role color');
   }
   if(copy==='recipient')assert.equal(ink.mirrorText,expected,media+' recipient mirrored data text');
   if(media==='print')assert.equal(ink.headingBackground,'rgb(255, 255, 255)','Both printed forms must have white background');
  }
 }
 await page.emulateMedia({media:null});
 await page.locator('.print-sheet').screenshot({path:resolve('qa-manual-vertical/vertical-screen.png')});
 await page.pdf({path:resolve('qa-manual-vertical/vertical-invoice-portrait.pdf'),printBackground:true,preferCSSPageSize:true});
 await page.evaluate(()=>{window.__didPrint=false;window.print=()=>{window.__didPrint=true}});
 await page.locator('#print-form').click();
 assert.equal(await page.evaluate(()=>window.__didPrint),true,'Print button must work');
 const blank=await context.newPage();
 await blank.goto(host+'/manual-invoice-vertical/?blank=1',{waitUntil:'networkidle'});
 assert.equal(await blank.locator('[data-copy="supplier"] [data-field=writtenDate]').inputValue(),'');
 assert.equal(await blank.locator('[data-copy="supplier"] [data-field=supplier]').inputValue(),'');
 assert.equal((await blank.locator('[data-copy="recipient"] [data-calc=grand]').first().innerText()).trim(),'');
 await blank.pdf({path:resolve('qa-manual-vertical/vertical-blank-portrait.pdf'),printBackground:true,preferCSSPageSize:true});
 await blank.close();
 assert.deepEqual(pageErrors,[],'Unexpected client errors');
 assert.deepEqual(networkWrites,[],'Independent form must never send input data to server');
 console.log('TOP_BOTTOM_INVOICE_BROWSER_PASS A4 portrait supplier RED top and recipient BLUE bottom in screen/print, same 10 shared line fields, VAT mirror, blank PDF, horizontal cut');
}finally{await browser.close()}
