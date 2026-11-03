import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const base='http://127.0.0.1:8787';
const out='qa-buyer-artifacts';
fs.mkdirSync(out,{recursive:true});
let ready=false;
for(let i=0;i<75;i++){
  try{const r=await fetch(base+'/request/');if(r.ok&&(await r.text()).includes('거래처 발주 요청')){ready=true;break}}catch(_){}
  await new Promise(resolve=>setTimeout(resolve,1000));
}
assert.equal(ready,true,'Buyer static page not served');
const browser=await chromium.launch({headless:true});
try{
 const admin=await browser.newContext({viewport:{width:390,height:844},locale:'ko-KR',timezoneId:'Asia/Seoul'});
 const page=await admin.newPage();
 const dialogs=[];
 page.on('dialog',async d=>{dialogs.push(d.message());await d.accept()});
 const errors=[];
 page.on('pageerror',e=>errors.push('admin: '+e.message));
 await page.goto(base,{waitUntil:'networkidle'});
 await page.locator('#login-form [name=password]').fill('ci-only-strong-example-password-2026');
 await page.locator('#login-form button[type=submit]').click();
 await page.locator('#app:not(.hidden) #metrics').waitFor();
 assert.equal(await page.locator('.metric').count(),6);
 await page.locator('[data-tab=clients]').click();
 await page.locator('[data-client-edit]').first().click();
 await page.locator('#client-form [name=person]').fill('QA발주담당');
 await page.locator('#client-form [name=phone]').fill('010-1111-2222');
 await page.locator('#client-form button[type=submit]').click();
 await page.locator('#client-list').getByText('QA발주담당').waitFor();
 await page.locator('[data-client-link]').first().click();
 await page.locator('#link-result:not(.hidden)').waitFor();
 const link=await page.locator('#generated-link-value').inputValue();
 assert.ok(link.includes('/request/#')&&link.split('#')[1].length===64,'Private link must have 256-bit token');
 await page.screenshot({path:path.join(out,'admin-share-link-390.png'),fullPage:true});
 const buyer=await browser.newContext({viewport:{width:390,height:844},locale:'ko-KR',timezoneId:'Asia/Seoul'});
 const buyerPage=await buyer.newPage();
 buyerPage.on('pageerror',e=>errors.push('buyer: '+e.message));
 await buyerPage.goto(link,{waitUntil:'networkidle'});
 await buyerPage.locator('#buyer-content:not(.hidden)').waitFor();
 assert.equal((await buyerPage.locator('#business-name').innerText()).trim(),'안산 중앙점');
 const visible=await buyerPage.locator('.buyer-product').count();
 assert.equal(visible,6);
 await buyerPage.locator('[data-product-id="1"]').fill('20');
 assert.ok((await buyerPage.locator('#estimated').innerText()).includes('220,000'));
 await buyerPage.screenshot({path:path.join(out,'buyer-request-390.png'),fullPage:true});
 const buyerDims=await buyerPage.evaluate(()=>[window.innerWidth,document.documentElement.scrollWidth]);
 assert.ok(buyerDims[1]<=buyerDims[0]+2,'Buyer page horizontal overflow '+buyerDims.join('/'));
 await buyerPage.locator('#submit-order').click();
 await buyerPage.locator('#result').getByText(/접수 완료/).waitFor();
 await buyerPage.locator('#request-history').getByText(/접수 대기/).waitFor();
 await page.locator('[data-tab=requests]').click();
 await page.locator('#request-list [data-request-fulfill]').waitFor();
 assert.ok((await page.locator('#request-shortages').innerText()).includes('추가 입고 20개 필요'));
 const before=await page.evaluate(async()=>await (await fetch('/api/state')).json());
 assert.equal(before.products[0].stock,0,'Pending buyer request may not debit stock');
 await page.screenshot({path:path.join(out,'admin-shortage-390.png'),fullPage:true});
 await page.locator('#request-list [data-request-fulfill]').first().click();
 for(let i=0;i<30&&!dialogs.some(x=>x.includes('재고 부족'));i++){
   await new Promise(resolve=>setTimeout(resolve,150));
 }
 assert.ok(dialogs.some(x=>x.includes('재고 부족')),'Insufficient stock must block approval. Dialogs: '+JSON.stringify(dialogs));
 await page.locator('[data-tab=stock]').click();
 await page.locator('#stock-product').selectOption('1');
 await page.locator('#stock-qty').fill('20');
 await page.locator('#stock-form button.primary').click();
 await page.locator('[data-tab=requests]').click();
 await page.locator('#request-list [data-request-fulfill]').waitFor();
 await page.locator('#request-list [data-request-fulfill]').first().click();
 await page.locator('#bill-preview:not(.hidden)').waitFor();
 assert.ok((await page.locator('#bill-sheet').innerText()).includes('220,000원'));
 const after=await page.evaluate(async()=>await (await fetch('/api/state')).json());
 assert.equal(after.products[0].stock,0,'Approved invoice should debit stock');
 assert.equal(after.buyer_dashboard.pending_count,0);
 await page.setViewportSize({width:1440,height:900});
 const snapshotBefore=await page.evaluate(async()=>({
   state:await (await fetch('/api/state')).json(),
   exportData:await (await fetch('/api/export')).json()
 }));
 await page.locator('#bill-delivery').getByText('배송완료 처리').waitFor();
 assert.ok((await page.locator('#bill-sheet').innerText()).includes('출고완료(배송전)'));
 await page.locator('#bill-delivery').click();
 await page.locator('#bill-delivery').getByText('배송전으로 변경').waitFor();
 assert.ok((await page.locator('#bill-sheet').innerText()).includes('출고완료(배송완료)'));
 const snapshotDelivered=await page.evaluate(async()=>({
   state:await (await fetch('/api/state')).json(),
   exportData:await (await fetch('/api/export')).json()
 }));
 assert.deepEqual(snapshotDelivered.state.metrics,snapshotBefore.state.metrics,'Delivery should not change sales dashboard');
 assert.deepEqual(snapshotDelivered.exportData.movements,snapshotBefore.exportData.movements,'Delivery cannot affect inventory movements');
 assert.deepEqual(snapshotDelivered.exportData.lines,snapshotBefore.exportData.lines,'Delivery cannot change sold items');
 assert.deepEqual(snapshotDelivered.state.products,snapshotBefore.state.products,'Delivery cannot affect stock counts');
 await page.screenshot({path:path.join(out,'admin-delivered-invoice-1440.png'),fullPage:true});
 await page.locator('#bill-delivery').click();
 await page.locator('#bill-delivery').getByText('배송완료 처리').waitFor();
 assert.ok((await page.locator('#bill-sheet').innerText()).includes('출고완료(배송전)'));
 await page.screenshot({path:path.join(out,'admin-issued-invoice-1440.png'),fullPage:true});
 assert.deepEqual(errors,[]);
 console.log('BUYER_BROWSER_QA_PASS: mobile 390, desktop 1440, client-only link, 20-unit order with zero stock, admin shortage, guarded approval, invoice, delivery-toggle no-stock-or-sales mutation');
}finally{await browser.close()}
