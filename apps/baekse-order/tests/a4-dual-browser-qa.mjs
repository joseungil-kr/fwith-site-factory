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
 await page.locator('.paper-sheet').first().screenshot({path:resolve('qa-a4-artifacts/sheet1-screen.png')});
 await page.evaluate(()=>{window.__printClicked=false;window.print=()=>{window.__printClicked=true}});
 await page.locator('#print-now').click();
 assert.equal(await page.evaluate(()=>window.__printClicked),true,'Print button must invoke the browser print action');
 await page.pdf({path:resolve('qa-a4-artifacts/a4-landscape-33-items.pdf'),printBackground:true,preferCSSPageSize:true});
 assert.deepEqual(errors,[],'No browser JS errors');
 console.log('A4_DEMO_BROWSER_PASS 33 items / 3 A4 landscape pages / 6 slips / 15 rows per slip / Print action');
}finally{await browser.close()}
