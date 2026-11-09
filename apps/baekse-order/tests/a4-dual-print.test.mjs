import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {LINES_PER_PAGE,paginate,makeDemoDocument,fromOrderDetail,renderPrintSheets} from '../public/print-form/print-data.mjs';

const base=new URL('../public/',import.meta.url);
const page=readFileSync(new URL('print-form/index.html',base),'utf8');
const script=readFileSync(new URL('print-form/print-form.js',base),'utf8');
const css=readFileSync(new URL('print-form/print-form.css',base),'utf8');
const index=readFileSync(new URL('index.html',base),'utf8');
const app=readFileSync(new URL('app.js',base),'utf8');

test('33 simulated line items automatically render as three A4 landscape paper sheets',()=>{
 const doc=makeDemoDocument(),groups=paginate(doc.lines);
 assert.equal(doc.sample,true);
 assert.equal(LINES_PER_PAGE,15);
 assert.equal(doc.lines.length,33);
 assert.deepEqual(groups.map(x=>x.length),[15,15,3]);
 assert.equal(doc.supply,doc.lines.reduce((n,x)=>n+x.total,0));
 assert.equal(doc.tax,Math.round(doc.supply*.1));
 assert.equal(doc.total,doc.supply+doc.tax+doc.previous);
 assert.equal(doc.balance,doc.total-doc.paid);
 const html=renderPrintSheets(doc);
 assert.equal((html.match(/class="paper-sheet"/g)||[]).length,3);
 assert.equal((html.match(/data-copy="vendor"/g)||[]).length,3);
 assert.equal((html.match(/data-copy="customer"/g)||[]).length,3);
 assert.equal((html.match(/class="filled-line"/g)||[]).length,66);
 assert.equal((html.match(/class="empty-line"/g)||[]).length,24);
 assert.equal((html.match(/class="cut-line"/g)||[]).length,3);
 assert.equal((html.match(/data-line-index="33"/g)||[]).length,2);
 assert.equal((html.match(/data-line-index="16"/g)||[]).length,2);
 assert.equal((html.match(/data-line-index="31"/g)||[]).length,2);
 assert.ok(!html.includes('data-line-index="34"'));
 assert.ok(html.includes('가상 샘플 · 실제 거래 아님'));
});

test('legacy app functionality remains with an opt-in A4 landscape print action',()=>{
 for(const marker of ['id="bill-a4-dual"','id="bill-58"','id="bill-80"','id="serial-print"'])
  assert.ok(index.includes(marker),marker);
 assert.ok(!index.includes('id="bill-a4"'),'Legacy A4/PDF button must not appear');
 assert.ok(!app.includes("$('#bill-a4').onclick"),'Retired A4 handler must not remain');
 assert.ok(app.includes("$('#bill-a4-dual').onclick=()=>{"));
 assert.ok(app.includes("window.open('/print-form/?mode=invoice','_blank')"));
 assert.ok(app.includes("event.origin!==location.origin||event.source!==pop"));
 assert.ok(app.includes("pop.postMessage({type:'BAEKSE_PRINT_DATA',detail},location.origin)"));
 assert.ok(script.includes("event.origin!==location.origin||event.source!==window.opener"));
 assert.ok(script.includes("window.opener.postMessage({type:'BAEKSE_PRINT_READY'},location.origin)"));
 assert.ok(!script.includes("localStorage")&&!script.includes("sessionStorage"));
});

test('actual invoice data respects recorded supplier/recipient, tax, previous balance and cancellation',()=>{
 const detail={
  order:{id:12,order_date:'2026-11-09',order_type:'sale',status:'issued',supply:25000,tax:2500,
    previous_balance:100000,amount_due:127500,
    client:{business:'안산 중앙점',person:'고객담당',phone:'010-0000-0000',business_no:'111-11-11111',address:'고객주소'},
    bank:{company_name:'테스트 공급자',company_business_no:'222-22-22222',company_phone:'031-000-0000',
    company_address:'공급자 주소',bank_name:'은행',account_number:'가상계좌',account_holder:'예금주'}},
  items:[{name:'반죽',qty:2,unit_price:10000,line_total:20000},{name:'팥',qty:1,unit_price:5000,line_total:5000}]
 };
 const doc=fromOrderDetail(detail),html=renderPrintSheets(doc);
 assert.equal(doc.voucher,'B20261109-0012');
 assert.equal(doc.supplier.name,'테스트 공급자');
 assert.equal(doc.recipient.name,'안산 중앙점');
 assert.equal(doc.supply,25000);
 assert.equal(doc.tax,2500);
 assert.equal(doc.previous,100000);
 assert.equal(doc.total,127500);
 assert.equal(doc.paid,null);
 assert.equal(doc.lines[0].tax+doc.lines[1].tax,2500);
 assert.equal((html.match(/data-copy=/g)||[]).length,2);
 assert.ok(html.includes('127,500'));
 assert.ok(html.includes('가상계좌'));
 assert.ok(!html.includes('가상 샘플 · 실제 거래 아님'));
 detail.order.status='cancelled';
 assert.ok(renderPrintSheets(fromOrderDetail(detail)).includes('출고취소'));
});

test('two-copy layout has fixed rows, cut guides, A4 landscape and explicit user print control',()=>{
 for(const marker of ['@page{size:A4 landscape;margin:0}','height:209mm','height:112mm','page-break-after:always','.cut-line'])
   assert.ok(css.includes(marker),marker);
 assert.ok(page.includes('id="print-now"'));
 assert.ok(page.includes('출력하기 / PDF 저장'));
 assert.ok(script.includes('window.print()'));
 assert.ok(page.includes('noindex,nofollow,noarchive'));
});
