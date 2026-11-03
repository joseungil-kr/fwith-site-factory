import {SerialReceiptPrinter, checkedSettings, PAPER_WIDTHS, WIDTH_CHOICES} from './serial-printer.js';
const $=s=>document.querySelector(s),$$=s=>Array.from(document.querySelectorAll(s));
const money=n=>(Number(n)||0).toLocaleString('ko-KR')+'원',fmt=n=>(Number(n)||0).toLocaleString('ko-KR');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const today=()=>new Date(Date.now()+9*3600000).toISOString().slice(0,10);
let state={products:[],clients:[],orders:[],movements:[]},viewOrder=null,buyerRequests=[];
const toast=s=>{const t=$('#toast');t.textContent=s;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3500)};
async function api(path,body){const opt=body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};let r=await fetch('/api/'+path,opt);let d=await r.json().catch(()=>({error:'서버 오류'}));if(!r.ok){if(r.status===401){$('#app').classList.add('hidden');$('#login').classList.remove('hidden')}throw new Error(d.error||'요청 실패')}return d}
function show(tab){$$('[data-page]').forEach(x=>x.classList.toggle('hidden',x.dataset.page!==tab));$$('[data-tab]').forEach(x=>x.classList.toggle('selected',x.dataset.tab===tab));window.scrollTo(0,0);if(tab==='requests')loadBuyerRequests().catch(e=>$('#request-list').textContent=e.message)}
async function refresh(){state=await api('state');render()}
function table(headers,rows){return `<div class="table-overflow"><table><thead><tr>${headers.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.join('')||`<tr><td colspan="${headers.length}">등록 내역이 없습니다.</td></tr>`}</tbody></table></div>`}
function render(){renderHome();renderBuyerDashboard();renderOrder();renderStock();renderClients();renderProducts();renderBills();renderSettings();}
function renderSettings(){
 const s=state.receipt_settings||{};
 for(const key of ['company_name','company_business_no','company_address','company_phone','company_email','bank_name','account_number','account_holder']){
   $('#payment-form [name="'+key+'"]').value=s[key]||(key==='company_name'?'백세푸드':'');
 }
 $('.brand b').textContent=s.company_name||'백세푸드';
}
function renderBuyerDashboard(){
 const v=state.buyer_dashboard||{pending_count:0,shortage_count:0,shortages:[]};
 const pieces=['<div class="buyer-kpi"><strong>'+Number(v.pending_count||0)+'건</strong><span>신규 발주 대기</span></div>',
   '<div class="buyer-kpi'+(v.shortage_count?' shortage-alert':'')+'"><strong>'+Number(v.shortage_count||0)+'품목</strong><span>추가 입고 필요</span></div>'];
 if(v.shortages?.length){
   pieces.push('<div class="buyer-alert-list">'+v.shortages.slice(0,4).map(p=>
     '<span>'+esc(p.name)+' <b>부족 '+fmt(p.shortage)+'개</b></span>').join('')+'</div>');
 }
 $('#buyer-home-summary').innerHTML='<div class="buyer-dashboard-row">'+pieces.join('')+'</div>';
}
async function loadBuyerRequests(){
 $('#request-list').textContent='발주 요청을 불러오는 중입니다.';
 const result=await api('requests/list');
 buyerRequests=result.requests||[];
 const shortages=result.summary?.shortages||[];
 $('#request-shortages').innerHTML=shortages.length?
   shortages.map(p=>'<div class="shortage-item"><b>'+esc(p.name)+'</b><span>현재고 '+fmt(p.stock)+'개 / 미처리 발주 '+fmt(p.requested)+'개</span><strong>추가 입고 '+fmt(p.shortage)+'개 필요</strong></div>').join(''):
   '<p class="hint">현재 추가 입고가 필요한 품목이 없습니다.</p>';
 const labels={pending:'발주 대기',fulfilled:'출고 완료',cancelled:'발주 취소'};
 $('#request-list').innerHTML=buyerRequests.length?buyerRequests.map(req=>{
   const pending=req.status==='pending';
   const rows=req.items.map(p=>'<li>'+esc(p.name)+' · '+fmt(p.qty)+'개 × '+money(p.unit_price)+'</li>').join('');
   const total=req.items.reduce((n,p)=>n+p.qty*p.unit_price,0);
   return '<article class="buyer-request-card"><div class="buyer-request-head"><div><strong>#'+req.id+' · '+esc(req.client_name)+'</strong><span>납품 요청일 '+esc(req.requested_delivery)+' · '+esc(req.created_at.slice(0,10))+'</span></div><span class="request-state '+(pending?'state-waiting':'')+'">'+labels[req.status]+'</span></div>'+
   '<ul class="buyer-request-items">'+rows+'</ul><p class="buyer-request-sum">예상 공급가액: <b>'+money(total)+'</b></p>'+
   (req.note?'<p class="buyer-request-note">요청사항: '+esc(req.note)+'</p>':'')+
   (pending?'<div class="buyer-approval-controls"><label>부가세<select data-request-vat="'+req.id+'"><option value="none">0원</option><option value="tax">10% 추가</option></select></label><label>전 잔고<input data-request-balance="'+req.id+'" type="number" min="0" max="2000000000" value="0" inputmode="numeric"></label></div><div class="action-row"><button class="primary" data-request-fulfill="'+req.id+'" type="button">출고처리</button><button class="danger" data-request-cancel="'+req.id+'" type="button">발주 취소</button></div>':
      req.issued_order_id?'<div class="action-row"><button class="secondary" data-request-invoice="'+req.issued_order_id+'" type="button">거래명세표 보기</button></div>':'')+
   '</article>';
 }).join(''):'<p class="hint">발주 요청 내역이 없습니다.</p>';
}
function renderHome(){
 const active=state.orders.filter(o=>o.status==='issued');
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
   ['재고 3개 이하 제품',shortage.length+'개',true],['누적출고금액',money(cumulative),false]];
 $('#metrics').innerHTML=cards.map(([name,value,warning])=>'<div class="metric'+(warning?' metric-orange':'')+
   '"><small>'+esc(name)+'</small><b>'+esc(value)+'</b></div>').join('');
 $('#home-stock').innerHTML=table(['제품','현재고','출고단가'],state.products.filter(p=>p.active).map(p=>`<tr><td>${esc(p.name)}</td><td><span class="pill ${p.stock<=3?'orange':''}">${fmt(p.stock)}개</span></td><td>${money(p.price)}</td></tr>`));
 $('#home-orders').innerHTML=table(['날짜','거래처','금액','상태'],state.orders.slice(0,7).map(o=>`<tr><td>${esc(o.order_date)}</td><td>${esc(o.client_name)}</td><td>${money(o.total)}</td><td>${o.status==='issued'?'완료':'취소'}</td></tr>`));
}
function renderOrder(){const client=$('#order-client').value;$('#order-client').innerHTML=`<option value="">거래처 선택</option>`+state.clients.filter(c=>c.active).map(c=>`<option value="${c.id}">${esc(c.business)}</option>`).join('');$('#order-client').value=client||String(state.clients.find(c=>c.active)?.id||'');
 const old={};$$('#order-items input').forEach(i=>old[i.dataset.id]=i.value);
 $('#order-items').innerHTML=state.products.filter(p=>p.active).map(p=>`<tr><td><b>${esc(p.name)}</b><span class="price-note">${money(p.price)} / 개 · 부가세 별도</span></td><td>${fmt(p.stock)}개</td><td><input type="number" min="0" max="${Math.max(0,p.stock)}" step="1" data-id="${p.id}" value="${esc(old[p.id]??0)}" aria-label="${esc(p.name)} 출고수량"></td><td class="right num" data-total="${p.id}">0원</td></tr>`).join('');updateTotals()}
function getItems(){const items=[];for(const i of $$('#order-items input')){const n=Number(i.value);if(!Number.isSafeInteger(n)||n<0)throw new Error('수량은 0 이상의 정수여야 합니다');if(n===0)continue;const p=state.products.find(p=>p.id===Number(i.dataset.id));if(n>p.stock)throw new Error(`${p.name} 재고 부족`);items.push({product_id:p.id,qty:n,unit_price:p.price,name:p.name});}
 for(const el of $$('.extra-row')){const name=el.querySelector('[data-extra="name"]').value.trim(),qty=Number(el.querySelector('[data-extra="qty"]').value),unit_price=Number(el.querySelector('[data-extra="price"]').value);if(!name&&!qty&&!unit_price)continue;if(!name||!Number.isSafeInteger(qty)||qty<1||!Number.isSafeInteger(unit_price)||unit_price<0)throw new Error('기타 품명·수량·단가를 모두 정확히 입력하세요');items.push({name,qty,unit_price})}return items}
function updateTotals(){try{let items=getItems(),supply=items.reduce((a,i)=>a+i.qty*i.unit_price,0),tax=$('#vat').value==='tax'?Math.round(supply*.1):0,previousBalance=Number($('#previous-balance').value);if(!Number.isSafeInteger(previousBalance)||previousBalance<0||previousBalance>2000000000)throw new Error('전 잔고는 0원 이상의 정수로 입력하세요');$$('#order-items input').forEach(input=>{const p=state.products.find(p=>p.id===Number(input.dataset.id));const target=$(`[data-total="${p.id}"]`);if(target)target.textContent=money(Number(input.value)*p.price)});$('#order-total').innerHTML=`<div><span>공급가액 (부가세 제외)</span><b>${money(supply)}</b></div><div><span>부가세</span><b>${money(tax)}</b></div><div><span>전 잔고</span><b>${money(previousBalance)}</b></div><div class="grand"><span>합계</span><b>${money(supply+tax+previousBalance)}</b></div>`}catch(e){$('#order-total').textContent=e.message}}
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
 $('#client-list').innerHTML=table(['상호 / 담당자','전화번호 / 사업자번호','상태','관리'],
   state.clients.map(c=>{
     const link=(state.buyer_links||[]).find(l=>l.client_id===c.id);
     const activeLink=link&&!link.revoked_at;
     const buttons=c.active?'<button class="secondary" data-client-link="'+c.id+'">'+(activeLink?'발주 링크 재발급':'발주 링크 만들기')+'</button>'+
       (activeLink?'<button class="danger" data-client-link-revoke="'+c.id+'">링크 중지</button>':''):'';
     return `<tr><td><b>${esc(c.business)}</b><span class="price-note">${esc(c.person)}${c.address?' · '+esc(c.address):''}</span></td><td>${esc(c.phone)}<span class="price-note">${esc(c.business_no)}</span></td><td>${c.active?'사용중':'비활성'}${activeLink?'<span class="price-note"> · 발주 링크 활성</span>':''}</td><td><div class="row-action"><button class="secondary" data-client-edit="${c.id}">수정</button><button class="${c.active?'danger':'secondary'}" data-client-toggle="${c.id}">${c.active?'삭제':'복구'}</button>${buttons}</div></td></tr>`;
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
function renderBills(){const selected=$('#bill-client-filter').value;$('#bill-client-filter').innerHTML='<option value="">전체 거래처</option>'+state.clients.map(c=>`<option value="${c.id}">${esc(c.business)}</option>`).join('');$('#bill-client-filter').value=selected;
 const filterDate=$('#bill-date-filter').value,filterClient=$('#bill-client-filter').selectedOptions[0]?.text;const list=state.orders.filter(o=>(!filterDate||o.order_date===filterDate)&&(!selected||o.client_name===filterClient));$('#bill-list').innerHTML=table(['명세표','출고일','거래처','공급가액','부가세','전 잔고','합계 / 상태',''],list.map(o=>`<tr class="${o.status==='cancelled'?'cancelled-order-row':''}"><td class="num">#${o.id}</td><td>${esc(o.order_date)}</td><td>${esc(o.client_name)}</td><td>${money(o.supply)}</td><td>${money(o.tax)}</td><td>${money(o.previous_balance||0)}</td><td>${money(o.amount_due??o.total)}<span class="price-note">${esc(deliveryLabel(o))}</span></td><td><button class="secondary" data-bill-view="${o.id}">보기</button></td></tr>`))}
async function openBill(id){viewOrder=await api('orders/detail?id='+id);const {order:o,items}=viewOrder;const bank=o.bank||{};const bankFields=[bank.bank_name,bank.account_number,bank.account_holder].filter(Boolean).map(esc).join(' ');const bankBlock=bankFields?'<div class="invoice-payment"><b>입금처:</b> '+bankFields+'</div>':'';$('#bill-preview').classList.remove('hidden');$('#bill-cancel').disabled=false;$('#bill-cancel').textContent=o.status==='issued'?'출고취소':'출고처리';$('#bill-cancel').className=o.status==='issued'?'danger':'secondary';$('#bill-delivery').classList.toggle('hidden',o.status!=='issued');$('#bill-delivery').textContent=o.delivery_status==='delivered'?'배송전으로 변경':'배송완료 처리';$('#bill-sheet').innerHTML=`<article class="invoice ${o.status!=='issued'?'cancelled':''}"><h2>거 래 명 세 표</h2><div class="invoice-meta"><div><p><b>전표번호:</b> ${esc('B'+o.order_date.replaceAll('-','')+'-'+String(o.id).padStart(4,'0'))}</p><p><b>출고일:</b> ${esc(o.order_date)}</p><p><b>거래처:</b> ${esc(o.client.business)}</p><p><b>담당자:</b> ${esc(o.client.person)} / ${esc(o.client.phone)}</p>${o.client.business_no?`<p><b>사업자번호:</b> ${esc(o.client.business_no)}</p>`:''}${o.client.address?`<p><b>주소:</b> ${esc(o.client.address)}</p>`:''}</div><div><p><b>공급자:</b> ${esc(bank.company_name||'백세푸드')}</p>${bank.company_business_no?`<p><b>사업자등록번호:</b> ${esc(bank.company_business_no)}</p>`:''}${bank.company_address?`<p><b>주소:</b> ${esc(bank.company_address)}</p>`:''}${bank.company_phone?`<p><b>연락처:</b> ${esc(bank.company_phone)}</p>`:''}${bank.company_email?`<p><b>이메일:</b> ${esc(bank.company_email)}</p>`:''}<p><b>출고단가:</b> 부가세 미포함</p><p><b>상태:</b> ${esc(deliveryLabel(o))}</p></div></div>${table(['품명','수량','단가','금액'],items.map(i=>`<tr><td>${esc(i.name)}</td><td>${fmt(i.qty)}</td><td>${money(i.unit_price)}</td><td>${money(i.line_total)}</td></tr>`))}<div class="invoice-total"><div class="invoice-amount-small">공급가액 ${money(o.supply)}</div><div class="invoice-amount-small">부가세 ${money(o.tax)}</div><div class="invoice-amount-small">전 잔고 ${money(o.previous_balance||0)}</div><div class="invoice-grand">합계 ${money(o.amount_due??(o.total+Number(o.previous_balance||0)))}</div></div>${o.memo?`<p><b>비고:</b> ${esc(o.memo)}</p>`:''}<div class="invoice-footer">위와같이 출고 하였습니다.</div>${bankBlock}</article>`;updateSerialControls();$('#bill-preview').scrollIntoView({behavior:'smooth',block:'start'})}
function printBill(size){if(!viewOrder)return toast('명세표를 먼저 선택하세요');document.body.classList.remove('print-58','print-80');if(size!=='a4')document.body.classList.add('print-'+size);window.print();setTimeout(()=>document.body.classList.remove('print-58','print-80'),1000)}
function resetClient(){$('#client-form').reset();$('#client-form [name=id]').value='';$('#client-form-title').textContent='거래처 추가'}
function resetProduct(){$('#product-form').reset();$('#product-form [name=id]').value='';$('#product-form-title').textContent='제품 추가'}
$('#login-form').addEventListener('submit',async e=>{e.preventDefault();try{await api('login',{password:e.target.password.value,remember:e.target.elements.namedItem('remember').checked});e.target.reset();$('#login').classList.add('hidden');$('#app').classList.remove('hidden');$('#login-error').textContent='';await refresh()}catch(e){$('#login-error').textContent=e.message}});
$('#logout').onclick=async()=>{await api('logout',{});location.reload()};
$('#nav').onclick=e=>{let b=e.target.closest('button[data-tab]');if(b)show(b.dataset.tab)};
document.body.addEventListener('click',e=>{const b=e.target.closest('[data-go]');if(b)show(b.dataset.go)});
$('#add-extra').onclick=addExtra;$('#extras').onclick=e=>{if(e.target.closest('.extra-remove')){e.target.closest('.extra-row').remove();updateTotals()}};
$('#order-form').addEventListener('input',updateTotals);$('#vat').addEventListener('change',updateTotals);
$('#order-form').addEventListener('submit',async e=>{e.preventDefault();try{const items=getItems();if(!items.length)throw new Error('출고 품목을 한 개 이상 입력하세요');if(!confirm('재고를 차감하고 거래명세표를 발행할까요?'))return;const r=await api('orders',{client_id:Number($('#order-client').value),order_date:$('#order-date').value,vat:$('#vat').value,previous_balance:Number($('#previous-balance').value||0),memo:$('#order-memo').value,items});toast('출고 등록 및 거래명세표 발행 완료');$$('#order-items input').forEach(i=>i.value=0);$('#extras').innerHTML='';$('#order-memo').value='';$('#previous-balance').value='0';await refresh();show('bills');await openBill(r.id)}catch(e){alert(e.message)}});
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
 const edit=e.target.closest('[data-client-edit]'),
       toggle=e.target.closest('[data-client-toggle]'),
       issue=e.target.closest('[data-client-link]'),
       revoke=e.target.closest('[data-client-link-revoke]');
 if(edit){
   const client=state.clients.find(c=>c.id===Number(edit.dataset.clientEdit));
   for(const key of ['id','business','person','phone','business_no','address'])$('#client-form [name="'+key+'"]').value=client[key];
   $('#client-form').scrollIntoView({behavior:'smooth'});renderClients();return;
 }
 if(toggle){
   if(!confirm('거래처의 사용 상태를 변경하시겠습니까? 기존 발주와 명세표는 유지됩니다.'))return;
   try{await api('clients/toggle',{id:Number(toggle.dataset.clientToggle)});await refresh()}
   catch(err){alert(err.message)}
   return;
 }
 if(issue){
   const clientId=Number(issue.dataset.clientLink);
   const client=state.clients.find(c=>c.id===clientId);
   const existing=(state.buyer_links||[]).find(l=>l.client_id===clientId&&!l.revoked_at);
   if(existing&&!confirm('새 발주 링크를 만들면 이 업체의 이전 링크는 더 이상 사용할 수 없습니다. 재발급할까요?'))return;
   try{
     const result=await api('requests/link/issue',{client_id:clientId});
     $('#generated-link-value').value=result.url;
     $('#link-client-name').textContent=client.business+'에만 전달하세요.';
     $('#link-result').classList.remove('hidden');
     await refresh();
     $('#link-result').scrollIntoView({behavior:'smooth',block:'start'});
   }catch(err){alert(err.message)}
   return;
 }
 if(revoke){
   const clientId=Number(revoke.dataset.clientLinkRevoke);
   if(!confirm('이 거래처의 발주 링크를 중지할까요? 기존 발주 기록은 유지됩니다.'))return;
   try{await api('requests/link/revoke',{client_id:clientId});$('#link-result').classList.add('hidden');await refresh();toast('발주 링크가 중지되었습니다.');}
   catch(err){alert(err.message)}
 }
};
$('#copy-generated-link').onclick=async()=>{
 const input=$('#generated-link-value');
 let copied=false;
 try{
   if(navigator.clipboard?.writeText){await navigator.clipboard.writeText(input.value);copied=true}
 }catch(_){}
 if(!copied){
   input.focus();input.select();
   try{copied=document.execCommand('copy')}catch(_){}
 }
 toast(copied?'발주 링크를 복사했습니다. 카카오톡이나 문자에 붙여넣으세요.':'링크가 선택되었습니다. 길게 눌러 복사해 주세요.');
};
$('#hide-generated-link').onclick=()=>{$('#generated-link-value').value='';$('#link-result').classList.add('hidden')};
$('#refresh-requests').onclick=()=>loadBuyerRequests().catch(e=>alert(e.message));
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
   const vat=$('[data-request-vat="'+id+'"]').value;
   const balance=Number($('[data-request-balance="'+id+'"]').value);
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
(async()=>{$('#current-date').textContent=today();$('#order-date').value=today();try{await api('session');$('#app').classList.remove('hidden');$('#login').classList.add('hidden');await refresh()}catch(e){$('#login').classList.remove('hidden')}})();
