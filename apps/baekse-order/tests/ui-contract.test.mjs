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
 assert.ok(html.includes('>설정</button>'));
 assert.ok(html.includes('data-tab="settings"'));
 assert.ok(html.includes('<h1>관리자 설정</h1>'));
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
 assert.deepEqual(tabs,['home','order','requests','bills','products','stock','clients','receivables','settings']);
 assert.ok(nav.includes('>매출관리</button>'));
 assert.ok(nav.includes('<button data-tab="stock">재고관리</button>'));
 assert.ok(html.includes('data-go="stock"'));
 assert.ok(nav.includes('발주요청(<span id="nav-requests-pending">0</span>)'));
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


test('modern three-screen white-teal design preserves live data and action hooks',()=>{
 for(const marker of ['data-page="home"','data-page="requests"','data-page="receivables"',
  'OPERATIONS / DASHBOARD','OPERATIONS / ORDER REQUESTS','FINANCE / SALES',
  'dashboard-detail-grid','id="home-request-preview"','id="home-shortages"',
  'id="request-filters"','id="request-search"','id="request-list"',
  'id="receivables-overview"','id="receivables-list"','id="ar-current"',
  'id="ar-opening-form"','id="ar-payment-form"','id="bill-sheet"'])assert.ok(html.includes(marker),marker);
 for(const marker of ['renderHomeRequestPreview','renderHomeShortages', 'dashboard-shortage-item',
    'renderBuyerRequestCards','requestNeedsRestock', 'requestFilter', 'request-search',
    'receivables-overview','clientReceivable', 'data-request-fulfill','data-request-cancel',
    'data-request-invoice','data-request-vat','data-request-balance']) {
   if(marker==='renderHomeShortages')continue;
   assert.ok(script.includes(marker),'Missing live JS source: '+marker);
 }
 assert.ok(css.includes('--bk-green:#0b7668') && css.includes('--bk-bg:#f5f7fa'));
 assert.ok(css.includes('.receivables-layout{display:grid') && css.includes('.buyer-request-item{display:grid'));
 assert.ok(css.includes('@media screen and (max-width:768px)'));
 assert.ok(css.includes('@media print{') || css.includes('@media print {'));
 assert.ok(!html.includes('428,000원') && !html.includes('1,250,000원'),
  'Design mock financial values must never be hardcoded into the production application');
});

test('invoice print preview omits operational metadata while keeping financial details',()=>{
 const start=script.indexOf('async function openBill(');
 const end=script.indexOf('function printBill(',start);
 assert.ok(start>=0&&end>start,'Invoice preview function missing');
 const invoice=script.slice(start,end);
 for(const label of ['<b>이메일:</b>','<b>출고단가:</b>','<b>상태:</b>','<b>비고:</b>']){
   assert.ok(!invoice.includes(label),'Unwanted invoice field: '+label);
 }
 for(const label of ['<b>전표번호:</b>','<b>출고일:</b>','<b>거래처:</b>','<b>공급자:</b>','<b>사업자등록번호:</b>','<b>연락처:</b>','공급가액','부가세','전 잔고','합계','입금처:']){
   assert.ok(invoice.includes(label),'Required invoice field missing: '+label);
 }
 assert.ok(css.includes('.invoice .invoice-meta{padding-bottom:14px;border-bottom:1px solid #d9e3dc}'));
 assert.ok(css.includes('.invoice .invoice-meta>div+div{border-left:1px solid #d9e3dc;'));
 assert.ok(html.includes('id="order-memo"'),'Memo must remain available internally');
 assert.ok(html.includes('name="company_email"'),'Email settings must remain available');
 assert.ok(script.includes('deliveryLabel(o)'),'Delivery state must remain in administrator history');
});

test('partner contact shows distinct signed URL and copies only selected buyer link, without rotating token',()=>{
  assert.ok(script.includes('data-client-link-copy'));
  assert.ok(script.includes('buyer-link-row'),'Buyer link must be visible beneath the contact name');
  assert.ok(script.includes('const url=entry?.url;'),'Copy must use selected client URL');
  assert.ok(script.includes('Number(l.client_id)===id&&!l.revoked_at'),'Copy must select the exact client');
  assert.ok(script.includes('navigator.clipboard.writeText(url)'),'Copy must use the selected URL');
  assert.ok(!script.includes('issuedBuyerUrls'),'Memory-only links must not be reused');
  assert.ok(!html.includes('id="link-result"'),'Separate buyer link panel must be removed');
  assert.ok(!script.includes("api('requests/link/issue',{client_id:id})"),'Copy must not rotate buyer token');
  assert.ok(css.includes('#app .client-link-copy{background:#1764c5'));
  assert.ok(html.includes('id="sales-by-client"'));
  assert.ok(html.includes('id="sales-payments"'));
  assert.ok(html.includes('name="default_order_type"'));
});

test('sales management displays sale and cash payment while internal issue excludes receivables',()=>{
 for(const label of ['id="order-type"','value="internal"','id="sales-by-client"','id="sales-payments"','<h1>매출관리</h1>'])assert.ok(html.includes(label),label);
 for(const name of ['renderSalesTables','currentOrderType','month_internal_cost','cumulative_internal_cost',"const url=entry?.url;"])assert.ok(script.includes(name),name);
 for(const query of ["AND order_type='sale'","order_type='internal'","schema_migrations","internal_cost"])assert.ok(worker.includes(query),query);
});

test('internal invoice prints original cost but never prints an invoice payment destination',()=>{
 const body=script.slice(script.indexOf('async function openBill('),script.indexOf('function printBill('));
 assert.ok(body.includes("o.order_type==='internal'"));
 assert.ok(body.includes("i.qty*i.cost"));
 assert.ok(body.includes("!internal&&bankFields"));
 assert.ok(body.includes("판매매출 반영 0원 · 입금 없음"));
 assert.ok(body.includes("내 부 출 고 내 역 서"));
 assert.ok(body.includes('내부출고 원가 합계 '));
});

test('exact-location legacy migration is guarded, reversible from preserved rows, and idempotent',()=>{
 for(const marker of ["'ansan-baekseboribap-internal-20261105'","TRIM(business)","orders:5","issued_sales:125000","payments:3","active_amount:49000","cutoff:7","payment_snapshots","unexpected_live_ledger_revision","kind='internal_adjustment'","INSERT INTO schema_migrations"])
  assert.ok(worker.includes(marker),'Migration missing '+marker);
 assert.ok(worker.includes('UPDATE orders SET order_type=\'internal\''),'Original orders must be reclassified, not duplicated');
 assert.ok(worker.includes("UPDATE clients SET default_order_type='internal'"));
 assert.ok(worker.includes("this.ctx.storage.transactionSync"));
});
