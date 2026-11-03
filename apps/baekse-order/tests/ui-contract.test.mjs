import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
const appPath=new URL('../public/app.js',import.meta.url);
const html=readFileSync(fileURLToPath(new URL('../public/index.html',import.meta.url)),'utf8');
const script=readFileSync(fileURLToPath(appPath),'utf8');
const css=readFileSync(fileURLToPath(new URL('../public/style.css',import.meta.url)),'utf8');
const worker=readFileSync(fileURLToPath(new URL('../src.js',import.meta.url)),'utf8');

test('six KPI cards include current month and orange low stock',()=>{
 for(const word of ['오늘 출고','오늘 출고금액','재고 3개 이하 제품','누적출고금액','monthLabel'])assert.ok(script.includes(word));
 assert.ok(css.includes('.metric.metric-orange'));
 for(const word of ['month_count','month_amount','cumulative_amount',"SUM(total)"])assert.ok(worker.includes(word));
});
test('company settings have five fields and a three-column bank row',()=>{
 assert.ok(html.includes('>관리자 설정</button>'));
 for(const key of ['company_name','company_business_no','company_address','company_phone','company_email','bank_name','account_number','account_holder']){
   assert.ok(html.includes('name="'+key+'"'),key);
 }
 assert.ok(css.includes('.bank-settings-grid{display:grid;grid-template-columns:repeat(3'));
 assert.ok(script.includes("$('.brand b').textContent"));
});
test('product elevator, localized movement types and invoice restore/delete controls',()=>{
 for(const marker of ['data-product-move','orders/reissue','orders/delete','confirm:\'DELETE\'','cancelled-order-row','재고수량 조정','반품 입고'])assert.ok(script.includes(marker),marker);
 assert.ok(worker.includes("transactionSync"));
 assert.ok(worker.includes("WHERE source IN (?,?,?)"));
 assert.ok(html.includes('id="bill-delete"'));
 assert.ok(!html.includes('id="serial-test"'));
 assert.ok(!html.includes('id="serial-width-test"'));
 assert.ok(!script.includes("$('#serial-test')"));
 assert.ok(!script.includes("$('#serial-width-test')"));
});
test('serial port directions are phrased for operators',()=>{
 assert.ok(html.includes('처음 한 번은'));
 assert.ok(html.includes('장치 선택·연결'));
 assert.ok(html.includes('프린터가 사용 중'));
 assert.ok(!html.includes('COM 번호는 아래 설정용 이름'));
});

test('navigation order, pending request count and removed AR hint',()=>{
 const nav=html.match(/<nav class="nav" id="nav">([\s\S]*?)<\/nav>/)?.[1]||'';
 const tabs=[...nav.matchAll(/data-tab="([^"]+)"/g)].map(m=>m[1]);
 assert.deepEqual(tabs,['home','order','requests','stock','bills','receivables','products','clients','settings']);
 assert.ok(nav.includes('발주 요청(<span id="nav-requests-pending">0</span>)'));
 assert.ok(script.includes('state.buyer_dashboard?.pending_count'));
 assert.ok(script.includes('state.buyer_dashboard=result.summary'));
 assert.ok(script.includes('renderRequestNavCount()'));
 assert.ok(!html.includes('관리 시작 전 발행한 명세표는 기초 미수금에 이미 반영된 것으로 간주하며 다시 합산하지 않습니다.'));
 assert.ok(!html.includes('기존 명세표의 ‘전 잔고’는 중복 계산하지 않습니다.'));
});


test('mobile hamburger menu, persistent request count and quick-order shortcuts',()=>{
 assert.ok(html.includes('id="mobile-menu-toggle"') && html.includes('aria-controls="nav"') && html.includes('aria-expanded="false"'));
 assert.ok(html.includes('id="mobile-requests-pending"') && html.includes('id="mobile-requests"'));
 assert.ok(html.includes('class="mobile-shortcuts"') && html.includes('data-go="order"'));
 assert.ok(html.includes('id="mobile-logout"'));
 for(const identifier of ['function setMobileMenuOpen','function closeMobileMenu',
   "toggle.setAttribute('aria-expanded'",'mobile-requests-pending',"$('#mobile-menu-toggle').onclick",
   "if(e.key==='Escape'",'window.innerWidth>768'])assert.ok(script.includes(identifier),identifier);
 assert.ok(css.includes('@media screen and (max-width:768px)'));
 assert.ok(css.includes('.nav.mobile-expanded{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))'));
 assert.ok(css.includes('.nav{display:none;overflow:visible'));
 assert.ok(css.includes('.top-right{display:none'));
 assert.ok(script.includes("function show(tab){closeMobileMenu();$$('[data-page]').forEach("),
   'Mobile navigation must update all pages, not only the first matching page');
});
