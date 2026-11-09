import {chromium} from 'playwright';
import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const base='http://127.0.0.1:8787';
for(let attempt=0;attempt<80;attempt++){
 try {const r=await fetch(base+'/print-form/');if(r.ok&&(await r.text()).includes('id="print-now"'))break}
 catch{}
 if(attempt===79)throw new Error('A4 sample page not served');
 await new Promise(r=>setTimeout(r,1000));
}
const browser=await chromium.launch({headless:true});
mkdirSync('qa-a4-artifacts',{recursive:true});
try{
 const context=await browser.newContext({viewport:{width:1440,height:900},locale:'ko-KR',timezoneId:'Asia/Seoul'});
 const page=await context.newPage();
 const errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/print-form/',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>document.querySelectorAll('.paper-sheet').length===3);
 assert.equal(await page.locator('.paper-sheet').count(),3);
 assert.equal(await page.locator('.slip-copy').count(),6);
 assert.equal(await page.locator('.slip-copy[data-copy="vendor"]').count(),3);
 assert.equal(await page.locator('.slip-copy[data-copy="customer"]').count(),3);
 assert.equal(await page.locator('.filled-line').count(),66);
 assert.equal(await page.locator('.empty-line').count(),24);
 for(let p=1;p<=3;p++){
  const sheet=page.locator('.paper-sheet[data-print-page="'+p+'"]');
  assert.equal(await sheet.locator('.slip-copy').count(),2);
  for(const copy of ['vendor','customer']){
   assert.equal(await sheet.locator('.slip-copy[data-copy="'+copy+'"] .items-table tbody tr').count(),15);
  }
 }
 assert.match((await page.locator('#status').innerText()),/3장.*33품목/);
 assert.equal(await page.locator('.party-table').count(),6);
 assert.equal(await page.locator('.summary-table').count(),6);
 for(const table of await page.locator('.party-table').all()){
  assert.equal(await table.locator('col').count(),4,'Four fixed information columns');
  assert.equal(await table.locator('tr').count(),4,'Four distinct information rows');
  for(const row of await table.locator('tr').all()){
   assert.equal(await row.locator('th').count(),2);
   assert.equal(await row.locator('td').count(),2);
  }
  assert.deepEqual(await table.locator('tr:first-child th').allTextContents(),['작성일','공급자 등록번호']);
  assert.deepEqual(await table.locator('tr:nth-child(2) th').allTextContents(),['공급받는자','공급자 상호']);
  assert.deepEqual(await table.locator('tr:nth-child(3) th').allTextContents(),['연락처','연락처']);
  assert.deepEqual(await table.locator('tr:nth-child(4) th').allTextContents(),['주소','주소']);
 }
 for(const table of await page.locator('.summary-table').all()){
  assert.deepEqual(await table.locator('tr:first-child th').allTextContents(),['공급가액','부가세','청구액']);
  assert.deepEqual(await table.locator('tr:nth-child(2) th').allTextContents(),['전 잔고','총액']);
  assert.equal(await table.locator('tr:nth-child(2) td[colspan="2"]').count(),1);
  assert.ok(!(await table.innerText()).includes('입 금'));
  assert.ok(!(await table.innerText()).includes('잔 금'));
 }
 await page.locator('.paper-sheet').first().screenshot({path:resolve('qa-a4-artifacts/sheet1-screen.png')});
 await page.evaluate(()=>{window.__printClicked=false;window.print=()=>{window.__printClicked=true}});
 await page.locator('#print-now').click();
 assert.equal(await page.evaluate(()=>window.__printClicked),true,'Print button must invoke the browser print action');
 await page.pdf({path:resolve('qa-a4-artifacts/a4-landscape-33-items.pdf'),printBackground:true,preferCSSPageSize:true});
 const parent=await context.newPage();
 await parent.goto(base+'/print-form/',{waitUntil:'networkidle'});
 const fixture={
  order:{id:9,order_date:'2026-11-09',order_type:'sale',status:'issued',supply:20000,tax:2000,previous_balance:80000,amount_due:102000,
   client:{business:'안산중앙점',person:'수령인',phone:'010-0000-5555',business_no:'000-00-00000',address:'경기도 안산 고객주소'},
   bank:{company_name:'백세푸드',company_business_no:'304-04-85025',company_phone:'031-407-0103',company_address:'경기도 안산 공급자주소'}},
  items:[{name:'잉어반죽',qty:2,unit_price:10000,line_total:20000}]
 };
 await parent.evaluate(detail=>{
  window.addEventListener('message',event=>{
   if(event.origin===location.origin&&event.data?.type==='BAEKSE_PRINT_READY')
    event.source.postMessage({type:'BAEKSE_PRINT_DATA',detail},location.origin);
  });
  const b=document.createElement('button');
  b.id='open-live-invoice-test';
  b.onclick=()=>window.open('/print-form/?mode=invoice','_blank');
  document.body.append(b);
 },fixture);
 const popupWait=parent.waitForEvent('popup');
 await parent.locator('#open-live-invoice-test').click();
 const actual=await popupWait;
 await actual.waitForFunction(()=>document.querySelectorAll('.party-table').length===2);
 const table=actual.locator('.slip-copy[data-copy="vendor"] .party-table');
 assert.equal(await table.locator('tr').count(),4);
 assert.deepEqual(await table.locator('tr:first-child th').allTextContents(),['작성일','공급자 등록번호']);
 assert.deepEqual(await table.locator('tr:nth-child(2) th').allTextContents(),['공급받는자','공급자 상호']);
 assert.equal((await table.locator('tr:nth-child(2) td').first().innerText()).trim(),'안산중앙점');
 assert.equal((await table.locator('tr:nth-child(2) td').last().innerText()).trim(),'백세푸드');
 assert.equal((await table.locator('tr:nth-child(3) td').first().innerText()).trim(),'010-0000-5555');
 assert.equal((await table.locator('tr:nth-child(3) td').last().innerText()).trim(),'031-407-0103');
 assert.equal((await table.locator('tr:nth-child(4) td').first().innerText()).trim(),'경기도 안산 고객주소');
 assert.equal((await table.locator('tr:nth-child(4) td').last().innerText()).trim(),'경기도 안산 공급자주소');
 const finance=actual.locator('.slip-copy[data-copy="vendor"] .summary-table');
 assert.deepEqual(await finance.locator('tr:first-child th').allTextContents(),['공급가액','부가세','청구액']);
 assert.deepEqual(await finance.locator('tr:nth-child(2) th').allTextContents(),['전 잔고','총액']);
 const charge=await finance.locator('tr:first-child td').allTextContents();
 assert.ok(charge[2].includes('22,000'),'Current delivery charge excludes previous balance');
 const due=await finance.locator('tr:nth-child(2) td').allTextContents();
 assert.ok(due[2].includes('102,000'),'Grand total includes previous balance, not payment');
 assert.equal(await actual.locator('.party-table').count(),2);
 assert.equal(await actual.locator('.paper-sheet').count(),1);
 await actual.pdf({path:resolve('qa-a4-artifacts/live-invoice-A4-four-column.pdf'),printBackground:true,preferCSSPageSize:true});
 await actual.close();
 await parent.close();
 assert.deepEqual(errors,[],'No browser JS errors');
 console.log('A4_DEMO_BROWSER_PASS 33 items / 3 A4 landscape pages / 6 slips / 15 rows per slip / Print action');
}finally{await browser.close()}
