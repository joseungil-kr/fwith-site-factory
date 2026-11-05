import {SerialReceiptPrinter, checkedSettings, PAPER_WIDTHS, WIDTH_CHOICES} from './serial-printer.js';
const $=s=>document.querySelector(s),$$=s=>Array.from(document.querySelectorAll(s));
const money=n=>(Number(n)||0).toLocaleString('ko-KR')+'원',fmt=n=>(Number(n)||0).toLocaleString('ko-KR');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const today=()=>new Date(Date.now()+9*3600000).toISOString().slice(0,10);
let state={products:[],clients:[],orders:[],movements:[]},viewOrder=null,buyerRequests=[],lastBalanceClientId=null,paymentRequestKey=null;
// Per-client links come from authenticated state; never cache bearer tokens in browser storage.
const toast=s=>{const t=$('#toast');t.textContent=s;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3500)};
async function api(path,body){const opt=body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};let r=await fetch('/api/'+path,opt);let d=await r.json().catch(()=>({error:'서버 오류'}));if(!r.ok){if(r.status===401){$('#app').classList.add('hidden');$('#login').classList.remove('hidden')}throw new Error(d.error||'요청 실패')}return d}
function setMobileMenuOpen(open){
 const expanded=Boolean(open);
 $('#nav').classList.toggle('mobile-expanded',expanded);
 const toggle=$('#mobile-menu-toggle');
 toggle.setAttribute('aria-expanded',String(expanded));
 toggle.setAttribute('aria-label',expanded?'전체 메뉴 닫기':'전체 메뉴 열기');
 $('#mobile-menu-glyph').textContent=expanded?'×':'☰';
}
function closeMobileMenu(){setMobileMenuOpen(false)}
function show(tab){closeMobileMenu();$$('[data-page]').forEach(x=>x.classList.toggle('hidden',x.dataset.page!==tab));$$('[data-tab]').forEach(x=>x.classList.toggle('selected',x.dataset.tab===tab));window.scrollTo(0,0);if(tab==='requests')loadBuyerRequests().catch(e=>$('#request-list').textContent=e.message);if(tab==='receivables')loadReceivableDetail().catch(e=>alert(e.message))}
async function refresh(){state=await api('state');render();loadBuyerRequests().catch(e=>{const el=$('#home-request-preview');if(el)el.textContent='발주 목록을 확인할 수 없습니다. 새로고침해 주세요.'})}
function table(headers,rows){return `<div class="table-overflow"><table><thead><tr>${headers.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.join('')||`<tr><td colspan="${headers.length}">등록 내역이 없습니다.</td></tr>`}</tbody></table></div>`}
function renderRequestNavCount(){
 const pending=Number(state.buyer_dashboard?.pending_count??0);
 const count=String(Number.isSafeInteger(pending)&&pending>=0?pending:0);
 $('#nav-requests-pending').textContent=count;
 $('#mobile-requests-pending').textContent=count;
 $('#mobile-requests').classList.toggle('has-pending',Number(count)>0);
}
function render(){renderRequestNavCount();renderHome();renderBuyerDashboard();renderReceivableHome();renderOrder();renderStock();renderClients();renderReceivables();renderSalesTables();renderProducts();renderBills();renderSettings();}
function renderSettings(){
 const s=state.receipt_settings||{};
 for(const key of ['company_name','company_business_no','company_address','company_phone','company_email','bank_name','account_number','account_holder']){
   $('#payment-form [name="'+key+'"]').value=s[key]||(key==='company_name'?'백세푸드':'');
 }
 $('.brand b').textContent=s.company_name||'백세푸드';
}
function clientReceivable(id){
 return (state.receivables?.accounts||[]).find(a=>a.client_id===Number(id))||null;
}
function renderReceivableHome(){
 const accounts=state.receivables||{accounts:[],total:0,tracked_clients:0};
 const missing=Math.max(0,state.clients.filter(c=>c.default_order_type!=='internal').length-accounts.tracked_clients);
 $('#receivable-home-summary').innerHTML='<div class="buyer-dashboard-row">'+
   '<div class="buyer-kpi"><strong>'+money(accounts.total||0)+'</strong><span>미수금 관리 중인 거래처 합계</span></div>'+
   '<div class="buyer-kpi'+(missing?' shortage-alert':'')+'"><strong>'+missing+'곳</strong><span>기초 미수금 미설정</span></div></div>';
}
function renderSalesTables(){
 const clients=state.clients.filter(c=>c.default_order_type!=='internal');
 const details=state.sales?.by_client||[],payments=state.sales?.completed_payments||[];
 $('#sales-by-client').innerHTML=table(['거래처','판매매출 누계','입금완료 누계','현재 미수금'],clients.map(c=>{
   const r=details.find(x=>Number(x.client_id)===Number(c.id))||{},a=clientReceivable(c.id);
   return '<tr><td><b>'+esc(c.business)+'</b></td><td>'+money(r.sale_amount||0)+'</td><td>'+money(r.paid_amount||0)+'</td><td>'+(a?money(a.balance):'<span class="muted">기초잔액 미설정</span>')+'</td></tr>';
 }));
 $('#sales-payments').innerHTML=payments.length?table(['입금일','거래처','입금액','상태','메모'],payments.map(p=>'<tr><td>'+esc(p.paid_date)+'</td><td>'+esc(p.client_name)+'</td><td>'+money(p.amount)+'</td><td><span class="pill">입금완료</span></td><td>'+esc(p.memo||'')+'</td></tr>')):'<p class="hint">실제 입금으로 등록된 내역이 없습니다. 판매출고만으로 입금완료가 되지는 않습니다.</p>';
}
function renderReceivables(){
 const accountList=state.receivables?.accounts||[];
 const selected=$('#ar-client-select').value;
 $('#ar-client-select').innerHTML='<option value="">거래처 선택</option>'+
   state.clients.filter(client=>client.default_order_type!=='internal').map(client=>'<option value="'+client.id+'">'+esc(client.business)+'</option>').join('');
 if(selected&&state.clients.some(client=>String(client.id)===selected&&client.default_order_type!=='internal'))$('#ar-client-select').value=selected;
 const count=state.clients.filter(c=>c.default_order_type!=='internal').length,tracked=accountList.length,missing=Math.max(0,count-tracked);
 $('#ar-count-label').textContent='관리 '+tracked+'곳 / 전체 '+count+'곳';
 $('#receivables-overview').innerHTML=
   '<div class="receivable-stat"><span>현재 미수금 합계</span><strong>'+money(state.receivables?.total||0)+'</strong></div>'+
   '<div class="receivable-stat"><span>관리 거래처</span><strong>'+tracked+'곳</strong></div>'+
   '<div class="receivable-stat'+(missing?' warn':'')+'"><span>기초잔액 미설정</span><strong>'+missing+'곳</strong></div>';
 $('#receivables-list').innerHTML=table(['거래처','입금 누계','현재 미수금'],
   state.clients.filter(client=>client.default_order_type!=='internal').map(client=>{
     const account=clientReceivable(client.id);
     const balance=account?money(account.balance):'미설정';
     return '<tr class="'+(selected===String(client.id)?'highlighted':'')+'"><td><strong>'+esc(client.business)+
       '</strong><span class="price-note">'+(account?'미수금 관리 중':'기초잔액 미설정')+'</span></td>'+
       '<td>'+(account?money(account.paid_amount):'—')+'</td><td><strong class="'+(account?'bk-ar-amount':'')+'">'+
       balance+'</strong><div class="ar-table-action"><button class="secondary" type="button" data-ar-client="'+client.id+'">상세 관리</button></div></td></tr>';
   }));
}
async function loadReceivableDetail(){
 const id=Number($('#ar-client-select').value);
 if(!id){
   $('#ar-current').textContent='거래처를 선택하세요.';
   $('#ar-opening-form').classList.add('hidden');$('#ar-payment-form').classList.add('hidden');
   $('#ar-payment-history').replaceChildren();return;
 }
 const d=await api('receivables/detail?client_id='+id),a=d.account;
 $('#ar-opening-form').classList.remove('hidden');
 $('#ar-opening-amount').value=String(a?.opening_balance??0);
 $('#ar-opening-reason-wrap').classList.toggle('hidden',!a);
 $('#ar-opening-reason').required=Boolean(a);
 $('#ar-opening-reason').value='';
 $('#ar-opening-save').textContent=a?'기초잔액 수정':'기초 미수금 등록·관리 시작';
 $('#ar-payment-form').classList.toggle('hidden',!a);
 if(a){
   $('#ar-current').innerHTML='<div class="ar-current-stats"><div><span>현재 미수금</span><strong>'+money(a.balance)+
     '</strong></div><div><span>기초 미수금</span><b>'+money(a.opening_balance)+
     '</b></div><div><span>관리 시작 후 출고 누계</span><b>'+money(a.issued_amount)+
     '</b></div><div><span>입금 누계</span><b>'+money(a.paid_amount)+'</b></div></div>'+
     '<p class="hint">관리 시작: '+esc(a.activated_at.slice(0,10))+' · 기존 명세표는 기초잔액에 포함된 것으로 간주합니다.</p>';
 }else{
   $('#ar-current').innerHTML='<p>이 업체는 아직 미수금 자동계산이 설정되지 않았습니다.</p>'+
     '<p class="hint">거래처의 현재 실제 미수금을 확인해 기초잔액으로 입력하세요. 과거 명세표는 다시 합산하지 않습니다.</p>';
 }
 const payments=(d.payments||[]).filter(p=>p.kind==='cash');
 $('#ar-payment-history').innerHTML=a?
   '<h2>입금완료 내역 (최근 100건)</h2>'+table(['입금일','금액','메모','처리'],
     payments.map(p=>'<tr class="'+(p.voided_at?'ar-voided':'')+'"><td>'+esc(p.paid_date)+'</td>'+
       '<td>'+money(p.amount)+'</td><td>'+esc(p.memo||'')+'</td><td>'+
       (p.voided_at?'취소됨':'입금완료 <button class="danger" type="button" data-ar-void="'+p.id+'">입금 취소</button>')+'</td></tr>')):'';
}
function currentOrderType(){return $('#order-type').value==='internal'?'internal':'sale'}
function setOrderTypeUI(){
 const internal=currentOrderType()==='internal';
 $('#order-vat-field').classList.toggle('hidden',internal);$('#order-balance-field').classList.toggle('hidden',internal);
 if(internal){$('#vat').value='none';$('#previous-balance').value='0';$('#previous-balance').readOnly=true;}
 $('#order-submit').textContent=internal?'내부출고 저장·원가 기록':'판매출고 저장·거래명세표 발행';
 $('#order-type-help').textContent=internal?'재고를 차감하고 원가만 기록합니다. 매출·미수금은 0원입니다.':'판매출고는 매출 및 미수금에 반영됩니다.';
 const ps=state.products.filter(p=>p.active);
 $$('#order-items .price-note').forEach((el,i)=>{const p=ps[i];if(p)el.textContent=money(internal?p.cost:p.price)+' / 개 · '+(internal?'내부사용 원가':'부가세 별도')});
 updateTotals();
}
function syncOrderPreviousBalance(){
 const clientId=Number($('#order-client').value),client=state.clients.find(c=>c.id===clientId),a=clientReceivable(clientId);
 const previous=$('#previous-balance'),hint=$('#previous-balance-help');
 if(lastBalanceClientId!==clientId)$('#order-type').value=client?.default_order_type==='internal'?'internal':'sale';
 $('#order-type option[value="sale"]').disabled=client?.default_order_type==='internal';
 if(currentOrderType()==='internal'){
  previous.value='0';previous.readOnly=true;hint.textContent='내부출고에는 미수금이 없습니다.';
  lastBalanceClientId=clientId;setOrderTypeUI();return;
 }
 if(a){previous.value=String(a.balance);previous.readOnly=true;hint.textContent='미수금 자동 입력: '+money(a.balance);}
 else{if(lastBalanceClientId!==clientId)previous.value='0';previous.readOnly=false;hint.textContent='기초 미수금 미설정 · 기본 0원';}
 lastBalanceClientId=clientId;setOrderTypeUI();
}
function renderBuyerDashboard(){
 const v=state.buyer_dashboard||{pending_count:0,shortage_count:0,shortages:[]};
 const pending=Number(v.pending_count||0),shortCount=Number(v.shortage_count||0);
 $('#buyer-home-summary').innerHTML='<div class="buyer-dashboard-row">'+
    '<div class="buyer-kpi"><strong>'+pending+'건</strong><span>출고 처리 대기</span></div>'+
    '<div class="buyer-kpi'+(shortCount?' shortage-alert':'')+'"><strong>'+shortCount+'품목</strong><span>추가 입고 검토</span></div></div>'+
    (v.shortages?.length?'<div class="buyer-alert-list">'+v.shortages.slice(0,3).map(p=>
      '<span>'+esc(p.name)+' <b>부족 '+fmt(p.shortage)+'개</b></span>').join('')+'</div>':'');
 const shortages=v.shortages||[];
 $('#home-shortages').innerHTML=shortages.length?shortages.slice(0,5).map(p=>{
   const stock=Math.max(0,Number(p.stock)||0),requested=Math.max(0,Number(p.requested)||0);
   const fill=requested>0?Math.min(100,Math.round(stock/requested*100)):100;
   return '<div class="dashboard-shortage-item"><div class="dashboard-shortage-line"><b>'+esc(p.name)+
     '</b><span class="dashboard-shortage-value">부족 '+fmt(p.shortage)+'개</span></div>'+
     '<div class="dashboard-shortage-progress"><span style="width:'+fill+'%"></span></div>'+
     '<p class="dashboard-shortage-help">현재 '+fmt(stock)+'개 / 전체 미처리 발주 '+fmt(requested)+'개</p></div>';
 }).join(''):'<div class="dashboard-empty">현재 추가 입고가 필요한 제품이 없습니다.</div>';
}
function renderHomeRequestPreview(){
 const pending=buyerRequests.filter(r=>r.status==='pending').slice(0,4);
 const target=$('#home-request-preview');
 if(!target)return;
 if(!pending.length){
   target.innerHTML=state.buyer_dashboard?.pending_count?
     '<p class="dashboard-empty">발주 요청을 불러오는 중입니다.</p>':
     '<p class="dashboard-empty">확인할 발주 요청이 없습니다.</p>';
   return;
 }
 target.innerHTML=pending.map(req=>{
   const total=req.items.reduce((v,item)=>v+Number(item.qty)*Number(item.unit_price),0);
   const short=requestNeedsRestock(req);
   const first=req.items[0];
   const product=first?esc(first.name)+(req.items.length>1?' 외 '+(req.items.length-1)+'종':''):'품목 없음';
   return '<div class="dashboard-request-item"><div class="dashboard-request-name">'+
     '<span class="dashboard-request-avatar" aria-hidden="true">'+esc(req.client_name.slice(0,1))+'</span>'+
     '<div><strong>'+esc(req.client_name)+'</strong><span>'+product+' · '+money(total)+
     ' · 납품 '+esc(req.requested_delivery)+'</span></div></div>'+
     '<span class="request-state '+(short?'state-waiting':'')+'">'+(short?'입고 검토':'출고 대기')+'</span></div>';
 }).join('');
}
async function loadBuyerRequests(){
 $('#request-list').textContent='발주 요청을 불러오는 중입니다.';
 const result=await api('requests/list');
 buyerRequests=result.requests||[];
 if(result.summary){
   state.buyer_dashboard=result.summary;
   renderRequestNavCount();
   renderBuyerDashboard();
 }
 const shortages=result.summary?.shortages||[];
 $('#request-shortages').innerHTML=shortages.length?
   shortages.map(p=>'<div class="shortage-item"><b>'+esc(p.name)+'</b><span>현재고 '+fmt(p.stock)+'개 / 미처리 발주 '+fmt(p.requested)+'개</span><strong>추가 입고 '+fmt(p.shortage)+'개 필요</strong></div>').join(''):
   '<p class="hint">현재 추가 입고가 필요한 품목이 없습니다.</p>';
 const shortagesAll=result.summary?.shortages||[];
 const pendingCount=Number(result.summary?.pending_count||0);
 const reviewCount=shortagesAll.length;
 const canReview=buyerRequests.filter(req=>req.status==='pending'&&!requestNeedsRestock(req)).length;
 $('#request-overview').innerHTML=
   '<div class="request-overview-card"><strong>'+pendingCount+'건</strong><span>처리 대기</span></div>'+
   '<div class="request-overview-card'+(reviewCount?' warn':'')+'"><strong>'+reviewCount+'품목</strong><span>추가 입고 필요</span></div>'+
   '<div class="request-overview-card"><strong>'+canReview+'건</strong><span>재고 검토 가능</span></div>';
 renderBuyerRequestCards();
 renderHomeRequestPreview();
}
let requestFilter='all';
function requestNeedsRestock(req){
 if(req.status!=='pending')return false;
 const shortages=new Set((state.buyer_dashboard?.shortages||[]).map(x=>Number(x.product_id)));
 return req.items.some(item=>shortages.has(Number(item.product_id)));
}
function renderBuyerRequestCards(){
 const query=$('#request-search').value.trim().toLowerCase();
 const rows=buyerRequests.filter(req=>{
   if(requestFilter==='pending'&&req.status!=='pending')return false;
   if(requestFilter==='shortage'&&!requestNeedsRestock(req))return false;
   const hay=[String(req.id),String(req.client_name||''),...req.items.map(item=>String(item.name||''))].join(' ').toLowerCase();
   return !query||hay.includes(query);
 });
 $$('#request-filters button').forEach(button=>{
   const active=button.dataset.requestFilter===requestFilter;
   button.classList.toggle('active',active);
   button.setAttribute('aria-pressed',String(active));
 });
 const stocks=new Map((state.products||[]).map(p=>[Number(p.id),Number(p.stock||0)]));
 const labels={pending:'발주 대기',fulfilled:'출고 완료',cancelled:'발주 취소'};
 $('#request-list').innerHTML=rows.length?rows.map(req=>{
   const pending=req.status==='pending',short=requestNeedsRestock(req);
   const internal=state.clients.find(c=>Number(c.id)===Number(req.client_id))?.default_order_type==='internal';
   const clientBalance=clientReceivable(req.client_id);
   const total=req.items.reduce((v,item)=>{const p=state.products.find(p=>Number(p.id)===Number(item.product_id));return v+Number(item.qty)*Number(internal?(p?.cost||0):item.unit_price)},0);
   const lines=req.items.map(item=>{
     const stock=stocks.get(Number(item.product_id));
     const stockLabel=stock===undefined?'미확인':fmt(stock)+'개';
     return '<div class="buyer-request-item"><span class="request-item-name">'+esc(item.name)+
       '</span><span>'+fmt(item.qty)+'개</span><span class="'+(stock!==undefined&&stock<item.qty?'request-item-low':'')+'">'+
       stockLabel+'</span><span>'+money(Number(item.qty)*Number(internal?(state.products.find(p=>Number(p.id)===Number(item.product_id))?.cost||0):item.unit_price))+'</span></div>';
   }).join('');
   const status=pending?(short?'입고 검토':'출고 검토'):labels[req.status]||esc(req.status);
   const controls=pending?
     (internal?'':'<div class="buyer-approval-controls"><label>부가세<select data-request-vat="'+req.id+'"><option value="none">0원</option><option value="tax">10% 추가</option></select></label>'+
     '<label>전 잔고<input data-request-balance="'+req.id+'" type="number" min="0" max="2000000000" value="'+(clientBalance?clientBalance.balance:0)+'" '+(clientBalance?'readonly':'')+' inputmode="numeric"></label></div>')+
     (internal?'<p class="hint">내부출고: 재고만 차감하며 매출은 0원입니다.</p>':clientBalance?'<p class="hint">전 잔고 자동 입력: '+money(clientBalance.balance)+' (출고 확정 시 최신 잔액 적용)</p>':
       '<p class="hint">미수금 관리 미설정: 전 잔고 수동 입력</p>')+
     '<div class="action-row"><button class="primary" type="button" data-request-fulfill="'+req.id+'">출고처리</button>'+
     '<button class="secondary" type="button" data-request-cancel="'+req.id+'">발주 취소</button></div>':
     (req.issued_order_id?'<div class="action-row"><button class="secondary" type="button" data-request-invoice="'+req.issued_order_id+'">거래명세표 보기</button></div>':'');
   const note=req.note?'<p class="buyer-request-note">요청사항: '+esc(req.note)+'</p>':'';
   const label=short?'<div class="bk-shortage-note">전체 미처리 발주량을 기준으로 추가 입고가 필요한 제품이 포함되어 있습니다.</div>':'';
   return '<article class="buyer-request-card"><div class="buyer-request-head"><div class="buyer-request-identity">'+
     '<span class="request-avatar" aria-hidden="true">'+esc(String(req.client_name||'업').slice(0,1))+'</span>'+
     '<div class="buyer-request-identity-details"><strong>'+esc(req.client_name)+' <small>#'+req.id+'</small></strong>'+
     '<span>접수 '+esc(req.created_at.slice(0,10))+' · 납품 요청 '+esc(req.requested_delivery)+'</span></div></div>'+
     '<span class="request-state '+(pending&&short?'state-waiting':'')+'">'+status+'</span></div>'+
     '<div class="buyer-request-items-header" aria-hidden="true"><span>발주 제품</span><span>수량</span><span>현재고</span><span>공급금액</span></div>'+
     '<div class="buyer-request-items">'+lines+'</div>'+note+label+
     '<div class="buyer-request-sum"><span>'+(internal?'예상 내부출고 원가 · 매출 0원':'예상 공급가액 · 부가세 별도')+'</span><b>'+money(total)+'</b></div>'+
     controls+'</article>';
 }).join(''):'<div class="panel"><p class="dashboard-empty">조건에 맞는 발주 내역이 없습니다.</p></div>';
}

function renderHome(){
 const active=state.orders.filter(o=>o.status==='issued'&&o.order_type!=='internal');
 const day=today(),month=day.slice(0,7),monthLabel=Number(day.slice(5,7))+'월';
 const stats=state.metrics||{};
 const countDay=stats.today_count??active.filter(o=>o.order_date===day).length;
 const sumDay=stats.today_amount??active.filter(o=>o.order_date===day).reduce((n,o)=>n+o.total,0);
 const countMonth=stats.month_count??active.filter(o=>o.order_date.startsWith(month)).length;
 const sumMonth=stats.month_amount??active.filter(o=>o.order_date.startsWith(month)).reduce((n,o)=>n+o.total,0);
 const cumulative=stats.cumulative_amount??active.reduce((n,o)=>n+o.total,0);
 const shortage=state.products.filter(p=>p.active&&p.stock<=3);
 const cards=[['오늘 출고',countDay+'건',false],['오늘 출고금액',money(sumDay),false],
   [monthLabel+' 출고',countMonth+'건',false],[monthLabel+' 출고금액',money(sumMonth),false],
   ['재고 3개 이하 제품',shortage.length+'개',true],['누적출고금액',money(cumulative),false],
   [monthLabel+' 내부출고 원가',money(stats.month_internal_cost||0),false],['누적 내부출고 원가',money(stats.cumulative_internal_cost||0),false]];
 $('#metrics').innerHTML=cards.map(([name,value,warning])=>'<div class="metric'+(warning?' metric-orange':'')+
   '"><small>'+esc(name)+'</small><b>'+esc(value)+'</b></div>').join('');
 $('#home-stock').innerHTML=table(['제품','현재고','출고단가'],state.products.filter(p=>p.active).map(p=>`<tr><td>${esc(p.name)}</td><td><span class="pill ${p.stock<=3?'orange':''}">${fmt(p.stock)}개</span></td><td>${money(p.price)}</td></tr>`));
 $('#home-orders').innerHTML=table(['날짜','거래처','구분','매출 / 내부원가','상태'],state.orders.slice(0,7).map(o=>`<tr><td>${esc(o.order_date)}</td><td>${esc(o.client_name)}</td><td>${o.order_type==='internal'?'내부출고':'판매출고'}</td><td>${money(o.order_type==='internal'?o.internal_cost:o.total)}</td><td>${o.status==='issued'?'완료':'취소'}</td></tr>`));
 renderHomeRequestPreview();
}
function renderOrder(){
 const client=$('#order-client').value;
 $('#order-client').innerHTML='<option value="">거래처 선택</option>'+state.clients.filter(c=>c.active).map(c=>'<option value="'+c.id+'">'+esc(c.business)+'</option>').join('');
 $('#order-client').value=client||String(state.clients.find(c=>c.active)?.id||'');
 const old={};$$('#order-items input').forEach(i=>old[i.dataset.id]=i.value);
 $('#order-items').innerHTML=state.products.filter(p=>p.active).map(p=>'<tr><td><b>'+esc(p.name)+'</b><span class="price-note">'+money(p.price)+' / 개 · 부가세 별도</span></td><td>'+fmt(p.stock)+'개</td><td><input type="number" min="0" max="'+Math.max(0,p.stock)+'" step="1" data-id="'+p.id+'" value="'+esc(old[p.id]??0)+'" aria-label="'+esc(p.name)+' 출고수량"></td><td class="right num" data-total="'+p.id+'">0원</td></tr>').join('');
 syncOrderPreviousBalance();
}
function getItems(){const items=[];for(const i of $$('#order-items input')){const n=Number(i.value);if(!Number.isSafeInteger(n)||n<0)throw new Error('수량은 0 이상의 정수여야 합니다');if(n===0)continue;const p=state.products.find(p=>p.id===Number(i.dataset.id));if(n>p.stock)throw new Error(`${p.name} 재고 부족`);items.push({product_id:p.id,qty:n,unit_price:p.price,name:p.name});}
 for(const el of $$('.extra-row')){const name=el.querySelector('[data-extra="name"]').value.trim(),qty=Number(el.querySelector('[data-extra="qty"]').value),unit_price=Number(el.querySelector('[data-extra="price"]').value);if(!name&&!qty&&!unit_price)continue;if(!name||!Number.isSafeInteger(qty)||qty<1||!Number.isSafeInteger(unit_price)||unit_price<0)throw new Error('기타 품명·수량·단가를 모두 정확히 입력하세요');items.push({name,qty,unit_price})}return items}
function updateTotals(){
 try{
  const items=getItems(),internal=currentOrderType()==='internal';
  const supply=internal?0:items.reduce((n,i)=>n+i.qty*i.unit_price,0);
  const cost=items.reduce((n,i)=>{const p=state.products.find(p=>p.id===Number(i.product_id));return n+i.qty*(p?p.cost:i.unit_price)},0);
  const tax=internal?0:($('#vat').value==='tax'?Math.round(supply*.1):0),previousBalance=internal?0:Number($('#previous-balance').value);
  if(!Number.isSafeInteger(previousBalance)||previousBalance<0||previousBalance>2000000000)throw new Error('전 잔고는 0원 이상의 정수로 입력하세요');
  $$('#order-items input').forEach(input=>{const p=state.products.find(p=>p.id===Number(input.dataset.id));const target=$('[data-total="'+p.id+'"]');if(target)target.textContent=money(Number(input.value)*(internal?p.cost:p.price))});
  $('#order-total').innerHTML=internal?'<div><span>내부출고 원가</span><b>'+money(cost)+'</b></div><div class="grand"><span>판매매출 반영</span><b>0원</b></div>':'<div><span>공급가액 (부가세 제외)</span><b>'+money(supply)+'</b></div><div><span>부가세</span><b>'+money(tax)+'</b></div><div><span>전 잔고</span><b>'+money(previousBalance)+'</b></div><div class="grand"><span>합계</span><b>'+money(supply+tax+previousBalance)+'</b></div>';
 }catch(e){$('#order-total').textContent=e.message}
}
function addExtra(){const r=document.createElement('div');r.className='extra-row';r.innerHTML=`<label>품명<input data-extra="name" maxlength="120" placeholder="예: 배송비"></label><label>수량<input data-extra="qty" type="number" min="1" step="1" placeholder="수량"></label><label>출고단가 (부가세 제외)<input data-extra="price" type="number" min="0" step="1" placeholder="금액"></label><button type="button" class="danger extra-remove" aria-label="기타 항목 삭제">삭제</button>`;$('#extras').append(r)}
function movementLabel(source){
 const value=String(source||'');
 const labels={in:'입고',return:'반품 입고',adjust:'재고수량 조정'};
 if(labels[value])return labels[value];
 const m=value.match(/^(order|cancel|reissue):([0-9]+)$/);
 return m?({order:'출고',cancel:'출고 취소',reissue:'출고처리(복원)'})[m[1]]+' #'+m[2]:value;
}
function renderStock(){const old=$('#stock-product').value;$('#stock-product').innerHTML=state.products.filter(p=>p.active).map(p=>`<option value="${p.id}">${esc(p.name)} (현재 ${p.stock}개)</option>`).join('');$('#stock-product').value=old||String(state.products.find(p=>p.active)?.id||'');setStockCost();$('#stock-list').innerHTML=table(['제품','매입가','출고가 (VAT 별도)','재고'],state.products.filter(p=>p.active).map(p=>`<tr><td>${esc(p.name)}</td><td>${money(p.cost)}</td><td>${money(p.price)}</td><td><b>${fmt(p.stock)}개</b></td></tr>`));
 $('#movement-list').innerHTML=table(['일시','품명','수량변동','구분'],state.movements.slice(0,40).map(m=>`<tr><td>${esc(m.created_at.slice(0,16).replace('T',' '))}</td><td>${esc(m.product_name)}</td><td>${m.delta>0?'+':''}${fmt(m.delta)}개</td><td>${esc(movementLabel(m.source))}</td></tr>`));}
function setStockCost(){const p=state.products.find(p=>p.id===Number($('#stock-product').value));if(p)$('#stock-cost').value=p.cost}
function renderClients(){
 const id=$('#client-form [name=id]').value;
 $('#client-list').innerHTML=table(['상호 / 담당자','전화번호 / 사업자번호','현재 미수금','상태','관리'],
   state.clients.map(client=>{
     const link=(state.buyer_links||[]).find(l=>l.client_id===client.id);
     const activeLink=link&&!link.revoked_at;
     const balance=client.default_order_type==='internal'?null:clientReceivable(client.id);
     const buttons=client.active?'<button class="secondary" data-client-link="'+client.id+'">'+(activeLink?'발주 링크 재발급':'발주 링크 만들기')+'</button>'+
       (activeLink?'<button class="danger" data-client-link-revoke="'+client.id+'">링크 중지</button>':''):'';
     const linkRow=activeLink&&client.active&&link.url?
       '<span class="buyer-link-row"><span class="buyer-link-label">발주링크 :</span><a class="buyer-link-url" href="'+esc(link.url)+'" target="_blank" rel="noopener noreferrer">'+esc(link.url)+'</a><button class="client-link-copy" type="button" data-client-link-copy="'+client.id+'">링크복사</button></span>':
       '<span class="buyer-link-row buyer-link-empty">발주링크 : '+(activeLink?'표시할 수 없음':'미발급')+'</span>';
     return `<tr><td><b>${esc(client.business)}</b><span class="price-note">${esc(client.person)}${client.address?' · '+esc(client.address):''}</span>${linkRow}</td><td>${esc(client.phone)}<span class="price-note">${esc(client.business_no)}</span></td><td><b>${client.default_order_type==='internal'?'해당 없음':balance?money(balance.balance):'미설정'}</b></td><td>${client.active?'사용중':'비활성'} · ${client.default_order_type==='internal'?'내부출고':'판매출고'}${activeLink?'<span class="price-note"> · 발주 링크 활성</span>':''}</td><td><div class="row-action"><button class="secondary" data-client-edit="${client.id}">수정</button><button class="${client.active?'danger':'secondary'}" data-client-toggle="${client.id}">${client.active?'삭제':'복구'}</button>${client.default_order_type==='internal'?'':'<button class="secondary" data-client-ar="${client.id}">매출관리</button>'}${buttons}</div></td></tr>`;
   })
 );
 $('#client-form-title').textContent=id?'거래처 수정':'거래처 추가';
}
function renderProducts(){
 const id=$('#product-form [name=id]').value;
 $('#product-list').innerHTML=table(['순서','제품명','매입단가','출고단가 (VAT 별도)','상태 / 관리'],state.products.map((p,index)=>`<tr><td><div class="order-move-buttons"><button class="secondary" type="button" data-product-move="up" data-id="${p.id}" aria-label="${esc(p.name)} 위로 이동" ${index===0?'disabled':''}>▲</button><button class="secondary" type="button" data-product-move="down" data-id="${p.id}" aria-label="${esc(p.name)} 아래로 이동" ${index===state.products.length-1?'disabled':''}>▼</button></div></td><td>${esc(p.name)}</td><td>${money(p.cost)}</td><td>${money(p.price)}</td><td><div class="row-action"><span class="pill ${p.active?'':'red'}">${p.active?'판매중':'비활성'}</span><button class="secondary" data-product-edit="${p.id}">수정</button><button class="${p.active?'danger':'secondary'}" data-product-toggle="${p.id}">${p.active?'삭제':'복구'}</button></div></td></tr>`));
 $('#product-form-title').textContent=id?'제품 수정':'제품 추가';
}
function deliveryLabel(order){
 if(order.status!=='issued')return '취소됨';
 if(order.delivery_status==='delivered')return '출고완료(배송완료)';
 if(order.delivery_status==='pending')return '출고완료(배송전)';
 return '출고완료(배송상태 미확인)';
}
function renderBills(){
 const selected=$('#bill-client-filter').value;
 $('#bill-client-filter').innerHTML='<option value="">전체 거래처</option>'+state.clients.map(c=>'<option value="'+c.id+'">'+esc(c.business)+'</option>').join('');
 $('#bill-client-filter').value=selected;
 const filterDate=$('#bill-date-filter').value,filterClient=$('#bill-client-filter').selectedOptions[0]?.text;
 const rows=state.orders.filter(o=>(!filterDate||o.order_date===filterDate)&&(!selected||o.client_name===filterClient));
 $('#bill-list').innerHTML=table(['명세표','출고일','거래처','구분','금액 / 원가','상태',''],rows.map(o=>{
   const internal=o.order_type==='internal';
   return '<tr class="'+(o.status==='cancelled'?'cancelled-order-row':'')+'"><td class="num">#'+o.id+'</td><td>'+esc(o.order_date)+'</td><td>'+esc(o.client_name)+'</td><td>'+(internal?'내부출고':'판매출고')+'</td><td>'+money(internal?o.internal_cost:(o.amount_due??o.total))+'</td><td>'+esc(deliveryLabel(o))+'</td><td><button class="secondary" data-bill-view="'+o.id+'">보기</button></td></tr>';
 }));
}
async function openBill(id){
 viewOrder=await api('orders/detail?id='+id);
 const {order:o,items}=viewOrder,internal=o.order_type==='internal',bank=o.bank||{};
 const bankFields=[bank.bank_name,bank.account_number,bank.account_holder].filter(Boolean).map(esc).join(' ');
 const bankBlock=!internal&&bankFields?'<div class="invoice-payment"><b>입금처:</b> '+bankFields+'</div>':'';
 $('#bill-preview').classList.remove('hidden');
 $('#bill-cancel').disabled=false;
 $('#bill-cancel').textContent=o.status==='issued'?'출고취소':'출고처리';
 $('#bill-cancel').className=o.status==='issued'?'danger':'secondary';
 $('#bill-delivery').classList.toggle('hidden',o.status!=='issued');
 $('#bill-delivery').textContent=o.delivery_status==='delivered'?'배송전으로 변경':'배송완료 처리';
 const lineTable=table(['품명','수량',internal?'원가':'단가',internal?'원가합계':'금액'],
   items.map(i=>'<tr><td>'+esc(i.name)+'</td><td>'+fmt(i.qty)+'</td><td>'+money(internal?i.cost:i.unit_price)+'</td><td>'+money(internal?i.qty*i.cost:i.line_total)+'</td></tr>'));
 const totals=internal?
   '<div class="invoice-total"><div class="invoice-grand">내부출고 원가 합계 '+money(o.internal_cost??items.reduce((n,i)=>n+i.qty*i.cost,0))+'</div><div class="invoice-amount-small">판매매출 반영 0원 · 입금 없음</div></div>':
   '<div class="invoice-total"><div class="invoice-amount-small">공급가액 '+money(o.supply)+'</div><div class="invoice-amount-small">부가세 '+money(o.tax)+'</div><div class="invoice-amount-small">전 잔고 '+money(o.previous_balance||0)+'</div><div class="invoice-grand">합계 '+money(o.amount_due??(o.total+Number(o.previous_balance||0)))+'</div></div>';
 $('#bill-sheet').innerHTML='<article class="invoice '+(o.status!=='issued'?'cancelled':'')+'"><h2>'+(internal?'내 부 출 고 내 역 서':'거 래 명 세 표')+'</h2><div class="invoice-meta"><div><p><b>전표번호:</b> '+esc('B'+o.order_date.replaceAll('-','')+'-'+String(o.id).padStart(4,'0'))+'</p><p><b>출고일:</b> '+esc(o.order_date)+'</p><p><b>거래처:</b> '+esc(o.client.business)+'</p><p><b>담당자:</b> '+esc(o.client.person)+' / '+esc(o.client.phone)+'</p>'+(o.client.business_no?'<p><b>사업자번호:</b> '+esc(o.client.business_no)+'</p>':'')+(o.client.address?'<p><b>주소:</b> '+esc(o.client.address)+'</p>':'')+'</div><div><p><b>공급자:</b> '+esc(bank.company_name||'백세푸드')+'</p>'+(bank.company_business_no?'<p><b>사업자등록번호:</b> '+esc(bank.company_business_no)+'</p>':'')+(bank.company_address?'<p><b>주소:</b> '+esc(bank.company_address)+'</p>':'')+(bank.company_phone?'<p><b>연락처:</b> '+esc(bank.company_phone)+'</p>':'')+'</div></div>'+lineTable+totals+'<div class="invoice-footer">위와같이 출고 하였습니다.</div>'+bankBlock+'</article>';
 updateSerialControls();
 $('#bill-preview').scrollIntoView({behavior:'smooth',block:'start'});
}
function printBill(size){if(!viewOrder)return toast('명세표를 먼저 선택하세요');document.body.classList.remove('print-58','print-80');if(size!=='a4')document.body.classList.add('print-'+size);window.print();setTimeout(()=>document.body.classList.remove('print-58','print-80'),1000)}
function resetClient(){$('#client-form').reset();$('#client-form [name=id]').value='';$('#client-form-title').textContent='거래처 추가'}
function resetProduct(){$('#product-form').reset();$('#product-form [name=id]').value='';$('#product-form-title').textContent='제품 추가'}
$('#login-form').addEventListener('submit',async e=>{e.preventDefault();try{await api('login',{password:e.target.password.value,remember:e.target.elements.namedItem('remember').checked});e.target.reset();$('#login').classList.add('hidden');$('#app').classList.remove('hidden');$('#login-error').textContent='';await refresh()}catch(e){$('#login-error').textContent=e.message}});
$('#logout').onclick=async()=>{await api('logout',{});location.reload()};
$('#nav').onclick=e=>{let b=e.target.closest('button[data-tab]');if(b)show(b.dataset.tab)};
$('#mobile-menu-toggle').onclick=()=>{
 const opening=$('#mobile-menu-toggle').getAttribute('aria-expanded')!=='true';
 setMobileMenuOpen(opening);
 if(opening)$('#nav button[data-tab].selected')?.focus();
};
$('#mobile-logout').onclick=()=>$('#logout').click();
document.addEventListener('keydown',e=>{
 if(e.key==='Escape'&&$('#mobile-menu-toggle').getAttribute('aria-expanded')==='true'){
   closeMobileMenu();$('#mobile-menu-toggle').focus();
 }
});
document.addEventListener('click',e=>{
 if(window.innerWidth<=768&&$('#mobile-menu-toggle').getAttribute('aria-expanded')==='true'&&
    !e.target.closest('#nav')&&!e.target.closest('#mobile-menu-toggle'))closeMobileMenu();
});
window.addEventListener('resize',()=>{
 if(window.innerWidth>768&&$('#mobile-menu-toggle').getAttribute('aria-expanded')==='true')closeMobileMenu();
});
document.body.addEventListener('click',e=>{const b=e.target.closest('[data-go]');if(b)show(b.dataset.go)});
$('#add-extra').onclick=addExtra;$('#extras').onclick=e=>{if(e.target.closest('.extra-remove')){e.target.closest('.extra-row').remove();updateTotals()}};
$('#order-form').addEventListener('input',updateTotals);$('#vat').addEventListener('change',updateTotals);$('#order-type').addEventListener('change',setOrderTypeUI);$('#order-client').addEventListener('change',syncOrderPreviousBalance);
$('#order-form').addEventListener('submit',async e=>{e.preventDefault();try{
 const items=getItems(),internal=currentOrderType()==='internal';
 if(!items.length)throw new Error('출고 품목을 한 개 이상 입력하세요');
 if(!confirm(internal?'재고를 차감하고 내부출고 원가만 기록할까요? 매출은 발생하지 않습니다.':'재고를 차감하고 판매 거래명세표를 발행할까요?'))return;
 const r=await api('orders',{client_id:Number($('#order-client').value),order_type:currentOrderType(),order_date:$('#order-date').value,vat:$('#vat').value,previous_balance:internal?0:Number($('#previous-balance').value||0),memo:$('#order-memo').value,items});
 toast(internal?'내부출고 및 원가 기록 완료':'판매출고 및 명세표 발행 완료');
 $$('#order-items input').forEach(i=>i.value=0);$('#extras').innerHTML='';$('#order-memo').value='';$('#previous-balance').value='0';
 await refresh();show('bills');await openBill(r.id);
}catch(e){alert(e.message)}});
$('#stock-product').onchange=setStockCost;$('#stock-type').onchange=()=>{$('#stock-qty-label').firstChild.textContent=$('#stock-type').value==='adjust'?'실사 재고수량':'수량';$('#stock-qty').min=$('#stock-type').value==='adjust'?'0':'1'};
$('#stock-form').addEventListener('submit',async e=>{e.preventDefault();try{let type=$('#stock-type').value,quantity=Number($('#stock-qty').value);await api('stock',{product_id:Number($('#stock-product').value),type,quantity,adjustment:type==='adjust'?quantity:undefined,cost:Number($('#stock-cost').value),note:$('#stock-note').value});toast('재고 변경을 저장했습니다');$('#stock-qty').value='';$('#stock-note').value='';await refresh()}catch(e){alert(e.message)}});
$('#client-form').addEventListener('submit',async e=>{e.preventDefault();try{const f=new FormData(e.target),d=Object.fromEntries(f);if(d.id)d.id=Number(d.id);await api('clients',d);resetClient();await refresh();toast('거래처 저장 완료')}catch(e){alert(e.message)}});
$('#product-form').addEventListener('submit',async e=>{e.preventDefault();try{const f=new FormData(e.target),d=Object.fromEntries(f);if(d.id)d.id=Number(d.id);d.cost=Number(d.cost);d.price=Number(d.price);await api('products',d);resetProduct();await refresh();toast('제품 저장 완료')}catch(e){alert(e.message)}});
$('#client-reset').onclick=resetClient;$('#product-reset').onclick=resetProduct;
$('#payment-form').addEventListener('submit',async e=>{
  e.preventDefault();
  try{
    const data=Object.fromEntries(new FormData(e.target));
    await api('receipt-settings',data);
    await refresh();
    toast('관리자 설정을 저장했습니다.');
  }catch(e){alert(e.message)}
});
$('#client-list').onclick=async e=>{
 const arManage=e.target.closest('[data-client-ar]');
 if(arManage){show('receivables');$('#ar-client-select').value=arManage.dataset.clientAr;loadReceivableDetail().catch(err=>alert(err.message));return;}
 const edit=e.target.closest('[data-client-edit]'),
       toggle=e.target.closest('[data-client-toggle]'),
       issue=e.target.closest('[data-client-link]'),
       copy=e.target.closest('[data-client-link-copy]'),
       revoke=e.target.closest('[data-client-link-revoke]');
 if(edit){
   const client=state.clients.find(c=>c.id===Number(edit.dataset.clientEdit));
   for(const key of ['id','business','person','phone','business_no','address','default_order_type'])$('#client-form [name="'+key+'"]').value=client[key]||'sale';
   $('#client-form').scrollIntoView({behavior:'smooth'});renderClients();return;
 }
 if(toggle){
   if(!confirm('거래처의 사용 상태를 변경하시겠습니까? 기존 발주와 명세표는 유지됩니다.'))return;
   try{await api('clients/toggle',{id:Number(toggle.dataset.clientToggle)});await refresh()}
   catch(err){alert(err.message)}
   return;
 }
 if(copy){
   const id=Number(copy.dataset.clientLinkCopy);
   const entry=(state.buyer_links||[]).find(l=>Number(l.client_id)===id&&!l.revoked_at);
   const url=entry?.url;
   if(!url){alert('해당 거래처의 발주 링크를 확인할 수 없습니다. 새로고침한 후 다시 시도하세요.');return;}
   try{
     let copied=false;
     if(navigator.clipboard?.writeText){
       try{await navigator.clipboard.writeText(url);copied=true}catch(_){}
     }
     if(!copied){
       const input=document.createElement('textarea');
       input.value=url;input.readOnly=true;input.setAttribute('aria-hidden','true');
       input.style.cssText='position:fixed;left:-9999px;top:0;opacity:0';
       document.body.appendChild(input);
       try{input.focus();input.select();copied=document.execCommand('copy')}finally{input.remove()}
     }
     if(!copied)throw new Error('클립보드 복사 실패');
     const client=state.clients.find(c=>Number(c.id)===id);
     toast((client?.business||'해당 거래처')+'의 발주 링크를 복사했습니다.');
   }catch(err){alert('복사가 차단되었습니다. 해당 거래처 이름 아래의 발주링크를 길게 눌러 직접 복사해 주세요.');}
   return;
 }
 if(issue){
   const clientId=Number(issue.dataset.clientLink);
   const existing=(state.buyer_links||[]).find(l=>l.client_id===clientId&&!l.revoked_at);
   if(existing&&!confirm('새 발주 링크를 만들면 이 업체의 이전 링크는 더 이상 사용할 수 없습니다. 재발급할까요?'))return;
   try{
     await api('requests/link/issue',{client_id:clientId});
     await refresh();
     toast('발주 링크가 생성되었습니다. 거래처 이름 아래의 주소를 복사하세요.');
   }catch(err){alert(err.message)}
   return;
 }
 if(revoke){
   const clientId=Number(revoke.dataset.clientLinkRevoke);
   if(!confirm('이 거래처의 발주 링크를 중지할까요? 기존 발주 기록은 유지됩니다.'))return;
   try{await api('requests/link/revoke',{client_id:clientId});await refresh();toast('발주 링크가 중지되었습니다.');}
   catch(err){alert(err.message)}
 }
};
$('#refresh-requests').onclick=()=>loadBuyerRequests().catch(e=>alert(e.message));
$('#request-filters').onclick=e=>{const button=e.target.closest('button[data-request-filter]');if(!button)return;requestFilter=button.dataset.requestFilter;renderBuyerRequestCards()};
$('#request-search').oninput=renderBuyerRequestCards;
$('#request-list').onclick=async e=>{
 const fulfill=e.target.closest('[data-request-fulfill]'),
       cancel=e.target.closest('[data-request-cancel]'),
       invoice=e.target.closest('[data-request-invoice]');
 if(invoice){show('bills');openBill(Number(invoice.dataset.requestInvoice)).catch(err=>alert(err.message));return}
 if(cancel){
   const id=Number(cancel.dataset.requestCancel);
   if(!confirm('발주 #'+id+'을 취소할까요?'))return;
   try{await api('requests/cancel',{id});await refresh();await loadBuyerRequests();toast('발주 요청을 취소했습니다.')}
   catch(err){alert(err.message)}
   return;
 }
 if(fulfill){
   const id=Number(fulfill.dataset.requestFulfill),req=buyerRequests.find(r=>r.id===id);
   const internal=state.clients.find(c=>Number(c.id)===Number(req.client_id))?.default_order_type==='internal';
   const vat=internal?'none':$('[data-request-vat="'+id+'"]').value;
   const balance=internal?0:Number($('[data-request-balance="'+id+'"]').value);
   if(!Number.isSafeInteger(balance)||balance<0){alert('전 잔고는 0원 이상의 정수로 입력하세요.');return}
   if(!confirm(req.client_name+'의 발주 #'+id+'을 출고 처리할까요? 제품 재고가 차감되고 거래명세표가 발행됩니다.'))return;
   fulfill.disabled=true;
   try{
     const result=await api('requests/fulfill',{id,vat,previous_balance:balance,order_date:today()});
     await refresh();
     toast('발주 #'+id+' 출고 완료, 명세표 #'+result.issued_order_id+' 발행');
     show('bills');
     await openBill(result.issued_order_id);
   }catch(err){alert(err.message);await loadBuyerRequests()}
   finally{fulfill.disabled=false}
 }
};
$('#ar-client-select').addEventListener('change',()=>{paymentRequestKey=null;loadReceivableDetail().catch(err=>alert(err.message))});
$('#receivables-list').onclick=e=>{
 const control=e.target.closest('[data-ar-client]');
 if(!control)return;
 $('#ar-client-select').value=control.dataset.arClient;
 loadReceivableDetail().catch(err=>alert(err.message));
 $('#ar-client-select').scrollIntoView({behavior:'smooth',block:'center'});
};
$('#ar-opening-form').addEventListener('submit',async event=>{
 event.preventDefault();
 const id=Number($('#ar-client-select').value),current=clientReceivable(id),
       balance=Number($('#ar-opening-amount').value);
 if(!id||!Number.isSafeInteger(balance)||balance<0){alert('거래처와 올바른 기초 미수금 금액을 입력하세요.');return}
 const note=current?'수정 후 기존 입금·출고 내역은 그대로 유지됩니다. 계속할까요?':
   '기존 거래명세표의 매출은 다시 합산하지 않습니다. 지금 확인한 실제 미수금을 기초잔액으로 등록할까요?';
 if(!confirm(note))return;
 try{
   const payload={client_id:id,opening_balance:balance};
   if(current)payload.reason=$('#ar-opening-reason').value.trim();
   await api(current?'receivables/opening/revise':'receivables/opening',payload);
   await refresh();await loadReceivableDetail();toast(current?'기초 미수금을 수정했습니다.':'미수금 자동관리를 시작했습니다.');
 }catch(err){alert(err.message)}
});
$('#ar-payment-form').addEventListener('submit',async event=>{
 event.preventDefault();
 const id=Number($('#ar-client-select').value);
 const amount=Number($('#ar-paid-amount').value);
 if(!id||!Number.isSafeInteger(amount)||amount<1){alert('입금액은 1원 이상의 정수여야 합니다.');return}
 if(!confirm(money(amount)+'을(를) 해당 거래처의 입금 내역으로 등록할까요?'))return;
 const button=event.target.querySelector('button[type="submit"]');
 button.disabled=true;
 try{
   paymentRequestKey=paymentRequestKey||crypto.randomUUID();
   const result=await api('receivables/payments',{client_id:id,amount,
      paid_date:$('#ar-paid-date').value,memo:$('#ar-paid-memo').value,request_key:paymentRequestKey});
   await refresh();await loadReceivableDetail();
   paymentRequestKey=null;
   $('#ar-paid-amount').value='';$('#ar-paid-memo').value='';
   toast(result.duplicate?'이미 접수된 입금 내역입니다.':'입금 내역을 저장했습니다.');
 }catch(err){alert(err.message)}finally{button.disabled=false}
});
$('#ar-payment-history').onclick=async e=>{
 const button=e.target.closest('[data-ar-void]');if(!button)return;
 const reason=prompt('입금 취소 사유를 입력하세요. 취소 후 미수금에 다시 반영됩니다.');
 if(reason===null||!reason.trim())return;
 if(!confirm('입금 #'+button.dataset.arVoid+'을 취소할까요? 입금 내역은 감사 기록에 남습니다.'))return;
 try{
   await api('receivables/payments/void',{id:Number(button.dataset.arVoid),reason:reason.trim()});
   await refresh();await loadReceivableDetail();toast('입금 취소를 반영했습니다.');
 }catch(err){alert(err.message)}
};
$('#product-list').onclick=async e=>{
 const move=e.target.closest('[data-product-move]');
 if(move){
   try{await api('products/move',{id:Number(move.dataset.id),direction:move.dataset.productMove});await refresh()}
   catch(err){alert(err.message)}
   return;
 }
 let edit=e.target.closest('[data-product-edit]'),toggle=e.target.closest('[data-product-toggle]');if(edit){const p=state.products.find(p=>p.id===Number(edit.dataset.productEdit));for(const k of ['id','name','cost','price'])$('#product-form [name="'+k+'"]').value=p[k];$('#product-form').scrollIntoView({behavior:'smooth'});renderProducts()}if(toggle){if(!confirm('제품의 사용 상태를 변경하시겠습니까? 과거 출고내역은 유지됩니다.'))return;try{await api('products/toggle',{id:Number(toggle.dataset.productToggle)});await refresh()}catch(e){alert(e.message)}}};
$('#bill-date-filter').onchange=renderBills;$('#bill-client-filter').onchange=renderBills;
$('#bill-list').onclick=e=>{const b=e.target.closest('[data-bill-view]');if(b)openBill(Number(b.dataset.billView)).catch(e=>alert(e.message))};

/* Serial receipt printer: COM labels are user settings, not native OS port enumeration.
   The browser only opens the physical device chosen by the operator in requestPort(). */
const serialPrinter = new SerialReceiptPrinter();
const serialSelectIds = ['serial-slot','serial-baud','serial-paper','serial-dots','serial-font'];
const readSerialSettings = () => checkedSettings({
  slot: $('#serial-slot').value, baudRate: $('#serial-baud').value,
  paperMm: $('#serial-paper').value, dotWidth: $('#serial-dots').value,
  fontSize: $('#serial-font').value, autoCut: $('#serial-cut').checked
});
function syncWidthOptions(requested=null) {
  const paper=Number($('#serial-paper').value), choices=WIDTH_CHOICES[paper]||[];
  const previous=Number(requested ?? $('#serial-dots').value);
  const chosen=choices.includes(previous)?previous:PAPER_WIDTHS[paper];
  const labels={360:'360도트',384:'384도트 (좁은 폭)',416:'416도트',432:'432도트',
    448:'448도트',480:'480도트',512:'512도트 (기본 권장)',576:'576도트 (203dpi)'};
  $('#serial-dots').innerHTML=choices.map(d=>'<option value="'+d+'">'+labels[d]+'</option>').join('');
  $('#serial-dots').value=String(chosen);
}
function setSerialStatus(text, isError=false) {
  const el=$('#serial-status');
  el.textContent=text;
  el.classList.toggle('serial-error',!!isError);
}
function updateSerialControls() {
  const enabled=serialPrinter.supported && window.isSecureContext;
  const busy=serialPrinter.busy;
  const connected=serialPrinter.connected;
  $('#serial-connect').disabled=!enabled||busy||connected;
  $('#serial-reconnect').disabled=!enabled||busy||connected;
  $('#serial-disconnect').disabled=busy||!connected;
  $('#serial-print').disabled=busy||!connected||!viewOrder;
  for(const id of serialSelectIds) $('#'+id).disabled=busy||((id==='serial-slot'||id==='serial-baud')&&connected);
  $('#serial-cut').disabled=busy;
}
let initialSerialPreferences={};
try {
  initialSerialPreferences=JSON.parse(localStorage.getItem('baekse-serial-preferences')||'{}');
  for(const id of ['serial-slot','serial-baud','serial-paper','serial-font']) {
    const key=id.replace('serial-',''), value=initialSerialPreferences[key];
    if(value!=null){
      const element=$('#'+id);
      if([...element.options].some(o=>o.value===String(value))) element.value=String(value);
    }
  }
  if(typeof initialSerialPreferences.cut==='boolean') $('#serial-cut').checked=initialSerialPreferences.cut;
} catch (_) { /* Storage may be unavailable; do not persist secrets here. */ }
syncWidthOptions(initialSerialPreferences.dots);
function rememberSerialSettings() {
  try {
    const s=readSerialSettings();
    localStorage.setItem('baekse-serial-preferences',JSON.stringify({
      slot:s.slot,baud:s.baudRate,paper:s.paperMm,dots:s.dotWidth,font:s.fontSize,cut:s.autoCut
    }));
    setSerialStatus('설정: COM'+s.slot+' / '+s.baudRate+'bps / '+s.dotWidth+'도트 / 글자 '+s.fontSize+'px. 인쇄폭 확인 출력으로 잘림을 조정하세요.');
  } catch(e){setSerialStatus(e.message,true)}
}
for(const id of serialSelectIds) {
  $('#'+id).addEventListener('change',()=>{
    if(id==='serial-paper') syncWidthOptions();
    rememberSerialSettings();
  });
}
$('#serial-cut').addEventListener('change',rememberSerialSettings);

async function serialAction(action, successText) {
  try {
    // Call action synchronously in this click event before the first await (Web Serial activation).
    const pending=action();
    updateSerialControls();
    await pending;
    setSerialStatus(successText());
  } catch (e) {
    const msg=String(e && e.message || e);
    const hint=/NetworkError|already open|Failed to open|Access denied|in use|사용 중|busy/i.test(msg)?
      ' 기존 POS가 COM 포트를 사용 중인지 확인한 후 POS 쪽 연결을 해제해 보세요.':'';
    setSerialStatus('COM 작업 실패: '+msg+hint,true);
  } finally {updateSerialControls()}
}
$('#serial-connect').addEventListener('click',()=>serialAction(
  ()=>serialPrinter.connect(readSerialSettings()),
  ()=>{const s=serialPrinter.settings;return '장치 연결됨 · COM'+s.slot+' 설정 / '+s.baudRate+'bps. 실제 포트 번호는 브라우저 선택창 기준입니다.';}
));
$('#serial-reconnect').addEventListener('click',()=>serialAction(
  ()=>serialPrinter.reconnectGranted(readSerialSettings()),
  ()=>{const s=serialPrinter.settings;return '이전에 허용한 장치로 재연결됨 · COM'+s.slot+' 설정 / '+s.baudRate+'bps';}
));
$('#serial-disconnect').addEventListener('click',()=>serialAction(
  ()=>serialPrinter.disconnect(),
  ()=>'연결 해제됨. POS 프로그램에서 COM 포트를 다시 사용할 수 있습니다.'
));
function sendProgress(label,sent,total) {
  const percent=Math.min(100,Math.round(100*sent/Math.max(1,total)));
  setSerialStatus(label+' · 전송 '+percent+'% (전송 완료 후 용지 출력이 끝날 수 있습니다)');
}
$('#serial-print').addEventListener('click',()=>serialAction(
  ()=>serialPrinter.printInvoice(viewOrder,readSerialSettings(),
      (sent,total)=>sendProgress('거래명세표',sent,total)),
  ()=>'인쇄 명령과 절단 명령 전송 완료. 실제 용지 출력과 절단 여부를 확인하세요.'
));
if(serialPrinter.supported && window.isSecureContext) {
  setSerialStatus('COM4 / 9600bps 설정이 준비됐습니다. ‘장치 선택·연결’을 누르고 목록에서 프린터를 선택하세요.');
  if(typeof navigator.serial.addEventListener==='function') {
    navigator.serial.addEventListener('disconnect',event=>{
      if(serialPrinter.port===event.target) {
        serialPrinter.port=null;
        serialPrinter.settings=null;
        setSerialStatus('장치 연결이 끊어졌습니다. 다시 연결하세요.',true);
        updateSerialControls();
      }
    });
  }
} else {
  setSerialStatus('COM 직접 출력은 Windows용 Chrome/Edge의 HTTPS 연결에서 지원됩니다. 현재 브라우저에서는 사용할 수 없습니다.',true);
}
updateSerialControls();

$('#bill-a4').onclick=()=>printBill('a4');$('#bill-58').onclick=()=>printBill('58');$('#bill-80').onclick=()=>printBill('80');
$('#bill-delivery').onclick=async()=>{
 if(!viewOrder||viewOrder.order.status!=='issued')return;
 const id=viewOrder.order.id;
 const target=viewOrder.order.delivery_status==='delivered'?'pending':'delivered';
 const text=target==='delivered'?'이 명세표를 배송완료로 표시할까요? 재고와 매출은 변경되지 않습니다.':'배송전으로 다시 표시할까요? 재고와 매출은 변경되지 않습니다.';
 if(!confirm(text))return;
 const button=$('#bill-delivery');button.disabled=true;
 try{
   const result=await api('orders/delivery',{id,delivery_status:target});
   toast(result.unchanged?'이미 해당 배송상태입니다.':target==='delivered'?'배송완료로 변경했습니다.':'배송전으로 변경했습니다.');
   await refresh();await openBill(id);
 }catch(e){alert(e.message)}
 finally{button.disabled=false}
};
$('#bill-cancel').onclick=async()=>{
 if(!viewOrder)return;
 const id=viewOrder.order.id;
 const issued=viewOrder.order.status==='issued';
 const message=issued?'출고를 취소하고 제품 재고를 복원할까요?':'이 명세표를 다시 출고처리할까요? 제품 재고가 다시 차감됩니다.';
 if(!confirm(message))return;
 try{
   await api(issued?'orders/cancel':'orders/reissue',{id});
   toast(issued?'출고취소 및 재고 복원 완료':'출고처리 및 재고 차감 완료');
   await refresh();await openBill(id);
 }catch(e){alert(e.message)}
};
$('#bill-delete').onclick=async()=>{
 if(!viewOrder)return;
 const id=viewOrder.order.id;
 if(!confirm('명세표 #'+id+'을(를) 영구 삭제할까요? 출고 내역과 관련 재고 변동도 삭제됩니다.'))return;
 if(!confirm('마지막 확인: 영구 삭제한 명세표는 복원할 수 없습니다. 정말 삭제하시겠습니까?'))return;
 try{
   await api('orders/delete',{id,confirm:'DELETE'});
   viewOrder=null;$('#bill-preview').classList.add('hidden');
   await refresh();updateSerialControls();
   toast('명세표가 영구 삭제되었습니다.');
 }catch(e){alert(e.message)}
};
$('#backup').onclick=async()=>{try{const d=await api('export'),blob=new Blob([JSON.stringify(d,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='baekse-order-backup-'+today()+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1500)}catch(e){alert(e.message)}};
(async()=>{$('#current-date').textContent=today();$('#order-date').value=today();$('#ar-paid-date').value=today();try{await api('session');$('#app').classList.remove('hidden');$('#login').classList.add('hidden');await refresh()}catch(e){$('#login').classList.remove('hidden')}})();
