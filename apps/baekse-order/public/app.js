import {SerialReceiptPrinter, checkedSettings, PAPER_WIDTHS, WIDTH_CHOICES} from './serial-printer.js';
const $=s=>document.querySelector(s),$$=s=>Array.from(document.querySelectorAll(s));
const money=n=>(Number(n)||0).toLocaleString('ko-KR')+'원',fmt=n=>(Number(n)||0).toLocaleString('ko-KR');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const today=()=>new Date(Date.now()+9*3600000).toISOString().slice(0,10);
let state={products:[],clients:[],orders:[],movements:[]},viewOrder=null;
const toast=s=>{const t=$('#toast');t.textContent=s;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3500)};
async function api(path,body){const opt=body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};let r=await fetch('/api/'+path,opt);let d=await r.json().catch(()=>({error:'서버 오류'}));if(!r.ok){if(r.status===401){$('#app').classList.add('hidden');$('#login').classList.remove('hidden')}throw new Error(d.error||'요청 실패')}return d}
function show(tab){$$('[data-page]').forEach(x=>x.classList.toggle('hidden',x.dataset.page!==tab));$$('[data-tab]').forEach(x=>x.classList.toggle('selected',x.dataset.tab===tab));window.scrollTo(0,0)}
async function refresh(){state=await api('state');render()}
function table(headers,rows){return `<div class="table-overflow"><table><thead><tr>${headers.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.join('')||`<tr><td colspan="${headers.length}">등록 내역이 없습니다.</td></tr>`}</tbody></table></div>`}
function render(){renderHome();renderOrder();renderStock();renderClients();renderProducts();renderBills();}
function renderHome(){const live=state.orders.filter(o=>o.status==='issued'&&o.order_date===today());const amount=live.reduce((a,o)=>a+o.total,0);const shortage=state.products.filter(p=>p.active&&p.stock<=3);const sales=state.orders.filter(o=>o.status==='issued').reduce((a,o)=>a+o.total,0);
 $('#metrics').innerHTML=[['오늘 출고',live.length+'건'],['오늘 출고금액',money(amount)],['재고 3개 이하',shortage.length+'개 제품'],['누적 출고금액',money(sales)]].map(([n,v])=>`<div class="metric"><small>${n}</small><b>${esc(v)}</b></div>`).join('');
 $('#home-stock').innerHTML=table(['제품','현재고','출고단가'],state.products.filter(p=>p.active).map(p=>`<tr><td>${esc(p.name)}</td><td><span class="pill ${p.stock<=3?'red':''}">${fmt(p.stock)}개</span></td><td>${money(p.price)}</td></tr>`));
 $('#home-orders').innerHTML=table(['날짜','거래처','금액','상태'],state.orders.slice(0,7).map(o=>`<tr><td>${esc(o.order_date)}</td><td>${esc(o.client_name)}</td><td>${money(o.total)}</td><td>${o.status==='issued'?'완료':'취소'}</td></tr>`));}
function renderOrder(){const client=$('#order-client').value;$('#order-client').innerHTML=`<option value="">거래처 선택</option>`+state.clients.filter(c=>c.active).map(c=>`<option value="${c.id}">${esc(c.business)}</option>`).join('');$('#order-client').value=client||String(state.clients.find(c=>c.active)?.id||'');
 const old={};$$('#order-items input').forEach(i=>old[i.dataset.id]=i.value);
 $('#order-items').innerHTML=state.products.filter(p=>p.active).map(p=>`<tr><td><b>${esc(p.name)}</b><span class="price-note">${money(p.price)} / 개 · 부가세 별도</span></td><td>${fmt(p.stock)}개</td><td><input type="number" min="0" max="${Math.max(0,p.stock)}" step="1" data-id="${p.id}" value="${esc(old[p.id]??0)}" aria-label="${esc(p.name)} 출고수량"></td><td class="right num" data-total="${p.id}">0원</td></tr>`).join('');updateTotals()}
function getItems(){const items=[];for(const i of $$('#order-items input')){const n=Number(i.value);if(!Number.isSafeInteger(n)||n<0)throw new Error('수량은 0 이상의 정수여야 합니다');if(n===0)continue;const p=state.products.find(p=>p.id===Number(i.dataset.id));if(n>p.stock)throw new Error(`${p.name} 재고 부족`);items.push({product_id:p.id,qty:n,unit_price:p.price,name:p.name});}
 for(const el of $$('.extra-row')){const name=el.querySelector('[data-extra="name"]').value.trim(),qty=Number(el.querySelector('[data-extra="qty"]').value),unit_price=Number(el.querySelector('[data-extra="price"]').value);if(!name&&!qty&&!unit_price)continue;if(!name||!Number.isSafeInteger(qty)||qty<1||!Number.isSafeInteger(unit_price)||unit_price<0)throw new Error('기타 품명·수량·단가를 모두 정확히 입력하세요');items.push({name,qty,unit_price})}return items}
function updateTotals(){try{let items=getItems(),supply=items.reduce((a,i)=>a+i.qty*i.unit_price,0),tax=$('#vat').value==='tax'?Math.round(supply*.1):0;$$('#order-items input').forEach(input=>{const p=state.products.find(p=>p.id===Number(input.dataset.id));const target=$(`[data-total="${p.id}"]`);if(target)target.textContent=money(Number(input.value)*p.price)});$('#order-total').innerHTML=`<div><span>공급가액 (부가세 제외)</span><b>${money(supply)}</b></div><div><span>부가세</span><b>${money(tax)}</b></div><div class="grand"><span>출고 합계</span><b>${money(supply+tax)}</b></div>`}catch(e){$('#order-total').textContent=e.message}}
function addExtra(){const r=document.createElement('div');r.className='extra-row';r.innerHTML=`<label>품명<input data-extra="name" maxlength="120" placeholder="예: 배송비"></label><label>수량<input data-extra="qty" type="number" min="1" step="1" placeholder="수량"></label><label>출고단가 (부가세 제외)<input data-extra="price" type="number" min="0" step="1" placeholder="금액"></label><button type="button" class="danger extra-remove" aria-label="기타 항목 삭제">삭제</button>`;$('#extras').append(r)}
function renderStock(){const old=$('#stock-product').value;$('#stock-product').innerHTML=state.products.filter(p=>p.active).map(p=>`<option value="${p.id}">${esc(p.name)} (현재 ${p.stock}개)</option>`).join('');$('#stock-product').value=old||String(state.products.find(p=>p.active)?.id||'');setStockCost();$('#stock-list').innerHTML=table(['제품','매입가','출고가 (VAT 별도)','재고'],state.products.filter(p=>p.active).map(p=>`<tr><td>${esc(p.name)}</td><td>${money(p.cost)}</td><td>${money(p.price)}</td><td><b>${fmt(p.stock)}개</b></td></tr>`));
 $('#movement-list').innerHTML=table(['일시','품명','수량변동','구분'],state.movements.slice(0,40).map(m=>`<tr><td>${esc(m.created_at.slice(0,16).replace('T',' '))}</td><td>${esc(m.product_name)}</td><td>${m.delta>0?'+':''}${fmt(m.delta)}개</td><td>${esc(m.source)}</td></tr>`));}
function setStockCost(){const p=state.products.find(p=>p.id===Number($('#stock-product').value));if(p)$('#stock-cost').value=p.cost}
function renderClients(){const id=$('#client-form [name=id]').value;$('#client-list').innerHTML=table(['상호 / 담당자','전화번호 / 사업자번호','상태','관리'],state.clients.map(c=>`<tr><td><b>${esc(c.business)}</b><span class="price-note">${esc(c.person)}${c.address?` · ${esc(c.address)}`:''}</span></td><td>${esc(c.phone)}<span class="price-note">${esc(c.business_no)}</span></td><td>${c.active?'사용중':'비활성'}</td><td><div class="row-action"><button class="secondary" data-client-edit="${c.id}">수정</button><button class="${c.active?'danger':'secondary'}" data-client-toggle="${c.id}">${c.active?'삭제':'복구'}</button></div></td></tr>`));$('#client-form-title').textContent=id?'거래처 수정':'거래처 추가'}
function renderProducts(){const id=$('#product-form [name=id]').value;$('#product-list').innerHTML=table(['제품명','매입단가','출고단가 (VAT 별도)','상태 / 관리'],state.products.map(p=>`<tr><td>${esc(p.name)}</td><td>${money(p.cost)}</td><td>${money(p.price)}</td><td><div class="row-action"><span class="pill ${p.active?'':'red'}">${p.active?'판매중':'비활성'}</span><button class="secondary" data-product-edit="${p.id}">수정</button><button class="${p.active?'danger':'secondary'}" data-product-toggle="${p.id}">${p.active?'삭제':'복구'}</button></div></td></tr>`));$('#product-form-title').textContent=id?'제품 수정':'제품 추가'}
function renderBills(){const selected=$('#bill-client-filter').value;$('#bill-client-filter').innerHTML='<option value="">전체 거래처</option>'+state.clients.map(c=>`<option value="${c.id}">${esc(c.business)}</option>`).join('');$('#bill-client-filter').value=selected;
 const filterDate=$('#bill-date-filter').value,filterClient=$('#bill-client-filter').selectedOptions[0]?.text;const list=state.orders.filter(o=>(!filterDate||o.order_date===filterDate)&&(!selected||o.client_name===filterClient));$('#bill-list').innerHTML=table(['명세표','출고일','거래처','공급가액','부가세','합계 / 상태',''],list.map(o=>`<tr><td class="num">#${o.id}</td><td>${esc(o.order_date)}</td><td>${esc(o.client_name)}</td><td>${money(o.supply)}</td><td>${money(o.tax)}</td><td>${money(o.total)}<span class="price-note">${o.status==='issued'?'출고완료':'취소됨'}</span></td><td><button class="secondary" data-bill-view="${o.id}">보기</button></td></tr>`))}
async function openBill(id){viewOrder=await api('orders/detail?id='+id);const {order:o,items}=viewOrder;$('#bill-preview').classList.remove('hidden');$('#bill-cancel').disabled=o.status!=='issued';$('#bill-sheet').innerHTML=`<article class="invoice ${o.status!=='issued'?'cancelled':''}"><h2>거 래 명 세 표</h2><div class="invoice-meta"><div><p><b>전표번호:</b> ${esc('B'+o.order_date.replaceAll('-','')+'-'+String(o.id).padStart(4,'0'))}</p><p><b>출고일:</b> ${esc(o.order_date)}</p><p><b>거래처:</b> ${esc(o.client.business)}</p><p><b>담당자:</b> ${esc(o.client.person)} / ${esc(o.client.phone)}</p>${o.client.business_no?`<p><b>사업자번호:</b> ${esc(o.client.business_no)}</p>`:''}${o.client.address?`<p><b>주소:</b> ${esc(o.client.address)}</p>`:''}</div><div><p><b>공급자:</b> 백세푸드</p><p><b>출고단가:</b> 부가세 미포함</p><p><b>상태:</b> ${o.status==='issued'?'출고완료':'취소'}</p></div></div>${table(['품명','수량','단가','금액'],items.map(i=>`<tr><td>${esc(i.name)}</td><td>${fmt(i.qty)}</td><td>${money(i.unit_price)}</td><td>${money(i.line_total)}</td></tr>`))}<div class="invoice-total">공급가액 ${money(o.supply)}<br><small>부가세 ${money(o.tax)}</small><br>합계 ${money(o.total)}</div>${o.memo?`<p><b>비고:</b> ${esc(o.memo)}</p>`:''}<div class="invoice-footer">위와 같이 출고하였습니다.</div></article>`;updateSerialControls();$('#bill-preview').scrollIntoView({behavior:'smooth',block:'start'})}
function printBill(size){if(!viewOrder)return toast('명세표를 먼저 선택하세요');document.body.classList.remove('print-58','print-80');if(size!=='a4')document.body.classList.add('print-'+size);window.print();setTimeout(()=>document.body.classList.remove('print-58','print-80'),1000)}
function resetClient(){$('#client-form').reset();$('#client-form [name=id]').value='';$('#client-form-title').textContent='거래처 추가'}
function resetProduct(){$('#product-form').reset();$('#product-form [name=id]').value='';$('#product-form-title').textContent='제품 추가'}
$('#login-form').addEventListener('submit',async e=>{e.preventDefault();try{await api('login',{password:e.target.password.value,remember:e.target.elements.namedItem('remember').checked});e.target.reset();$('#login').classList.add('hidden');$('#app').classList.remove('hidden');$('#login-error').textContent='';await refresh()}catch(e){$('#login-error').textContent=e.message}});
$('#logout').onclick=async()=>{await api('logout',{});location.reload()};
$('#nav').onclick=e=>{let b=e.target.closest('button[data-tab]');if(b)show(b.dataset.tab)};
document.body.addEventListener('click',e=>{const b=e.target.closest('[data-go]');if(b)show(b.dataset.go)});
$('#add-extra').onclick=addExtra;$('#extras').onclick=e=>{if(e.target.closest('.extra-remove')){e.target.closest('.extra-row').remove();updateTotals()}};
$('#order-form').addEventListener('input',updateTotals);$('#vat').addEventListener('change',updateTotals);
$('#order-form').addEventListener('submit',async e=>{e.preventDefault();try{const items=getItems();if(!items.length)throw new Error('출고 품목을 한 개 이상 입력하세요');if(!confirm('재고를 차감하고 거래명세표를 발행할까요?'))return;const r=await api('orders',{client_id:Number($('#order-client').value),order_date:$('#order-date').value,vat:$('#vat').value,memo:$('#order-memo').value,items});toast('출고 등록 및 거래명세표 발행 완료');$$('#order-items input').forEach(i=>i.value=0);$('#extras').innerHTML='';$('#order-memo').value='';await refresh();show('bills');await openBill(r.id)}catch(e){alert(e.message)}});
$('#stock-product').onchange=setStockCost;$('#stock-type').onchange=()=>{$('#stock-qty-label').firstChild.textContent=$('#stock-type').value==='adjust'?'실사 재고수량':'수량';$('#stock-qty').min=$('#stock-type').value==='adjust'?'0':'1'};
$('#stock-form').addEventListener('submit',async e=>{e.preventDefault();try{let type=$('#stock-type').value,quantity=Number($('#stock-qty').value);await api('stock',{product_id:Number($('#stock-product').value),type,quantity,adjustment:type==='adjust'?quantity:undefined,cost:Number($('#stock-cost').value),note:$('#stock-note').value});toast('재고 변경을 저장했습니다');$('#stock-qty').value='';$('#stock-note').value='';await refresh()}catch(e){alert(e.message)}});
$('#client-form').addEventListener('submit',async e=>{e.preventDefault();try{const f=new FormData(e.target),d=Object.fromEntries(f);if(d.id)d.id=Number(d.id);await api('clients',d);resetClient();await refresh();toast('거래처 저장 완료')}catch(e){alert(e.message)}});
$('#product-form').addEventListener('submit',async e=>{e.preventDefault();try{const f=new FormData(e.target),d=Object.fromEntries(f);if(d.id)d.id=Number(d.id);d.cost=Number(d.cost);d.price=Number(d.price);await api('products',d);resetProduct();await refresh();toast('제품 저장 완료')}catch(e){alert(e.message)}});
$('#client-reset').onclick=resetClient;$('#product-reset').onclick=resetProduct;
$('#client-list').onclick=async e=>{let edit=e.target.closest('[data-client-edit]'),toggle=e.target.closest('[data-client-toggle]');if(edit){const c=state.clients.find(c=>c.id===Number(edit.dataset.clientEdit));for(const k of ['id','business','person','phone','business_no','address'])$('#client-form [name="'+k+'"]').value=c[k];$('#client-form').scrollIntoView({behavior:'smooth'});renderClients()}if(toggle){if(!confirm('거래처의 사용 상태를 변경하시겠습니까? 과거 명세표는 유지됩니다.'))return;try{await api('clients/toggle',{id:Number(toggle.dataset.clientToggle)});await refresh()}catch(e){alert(e.message)}}};
$('#product-list').onclick=async e=>{let edit=e.target.closest('[data-product-edit]'),toggle=e.target.closest('[data-product-toggle]');if(edit){const p=state.products.find(p=>p.id===Number(edit.dataset.productEdit));for(const k of ['id','name','cost','price'])$('#product-form [name="'+k+'"]').value=p[k];$('#product-form').scrollIntoView({behavior:'smooth'});renderProducts()}if(toggle){if(!confirm('제품의 사용 상태를 변경하시겠습니까? 과거 출고내역은 유지됩니다.'))return;try{await api('products/toggle',{id:Number(toggle.dataset.productToggle)});await refresh()}catch(e){alert(e.message)}}};
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
  $('#serial-test').disabled=busy||!connected;
  $('#serial-width-test').disabled=busy||!connected;
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
$('#serial-test').addEventListener('click',()=>serialAction(
  ()=>serialPrinter.test((sent,total)=>sendProgress('시험 출력',sent,total)),
  ()=>'시험 출력 데이터 전송 완료. 종이 출력 여부를 확인하세요.'
));
$('#serial-width-test').addEventListener('click',()=>serialAction(
  ()=>serialPrinter.testWidth(readSerialSettings(),
      (sent,total)=>sendProgress('인쇄폭 확인',sent,total)),
  ()=>'인쇄폭 확인 전송 완료. 양 끝의 세로선이 모두 보이는지 확인하세요.'
));
$('#serial-print').addEventListener('click',()=>serialAction(
  ()=>serialPrinter.printInvoice(viewOrder,readSerialSettings(),
      (sent,total)=>sendProgress('거래명세표',sent,total)),
  ()=>'인쇄 명령과 절단 명령 전송 완료. 실제 용지 출력과 절단 여부를 확인하세요.'
));
if(serialPrinter.supported && window.isSecureContext) {
  setSerialStatus('기본값: COM4 · 9600bps · 80mm 용지 / 512도트. ' +
    '장치 선택·연결을 눌러 실제 COM4를 선택하세요.');
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
$('#bill-cancel').onclick=async()=>{if(!viewOrder||!confirm('이 출고를 취소하고 제품 재고를 복원할까요?'))return;try{await api('orders/cancel',{id:viewOrder.order.id});toast('출고 취소·재고 복원 완료');await refresh();await openBill(viewOrder.order.id)}catch(e){alert(e.message)}};
$('#backup').onclick=async()=>{try{const d=await api('export'),blob=new Blob([JSON.stringify(d,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='baekse-order-backup-'+today()+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1500)}catch(e){alert(e.message)}};
(async()=>{$('#current-date').textContent=today();$('#order-date').value=today();try{await api('session');$('#app').classList.remove('hidden');$('#login').classList.add('hidden');await refresh()}catch(e){$('#login').classList.remove('hidden')}})();
