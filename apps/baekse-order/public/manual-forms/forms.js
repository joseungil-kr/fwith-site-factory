// Independent client-only editable forms. No network access, cookies, storage or ERP mutation.
const mode=document.body.dataset.form==='receipt'?'receipt':'invoice';
const receipt=mode==='receipt';
const verticalInvoice=document.body.dataset.form==='invoice-vertical';
const blankMode=!receipt&&new URLSearchParams(location.search).get('blank')==='1';
const count=verticalInvoice?10:15;
const root=document.getElementById('print-root');
const feedback=document.getElementById('feedback');
const currency=new Intl.NumberFormat('ko-KR');
const totalFields=['supply','tax','previous','paid','balance','grand'];
const cleanNumber=v=>{
 const n=Number(String(v??'').replace(/[,\s]/g,''));
 return Number.isFinite(n)&&n>0?Math.floor(n):0;
};
const won=n=>currency.format(Math.max(0,Math.round(n)));
const fieldNames=['writtenDate','slipNumber','supplier','supplierNo','supplierAddress','supplierPhone','buyer','buyerAddress','buyerContact','memo','previous','paid','vatMode'];
const rows=Array.from({length:count},(_,index)=>index);
const input=(key,label,kind='text',placeholder='')=>{
 const max=key.includes('Address')?80:key==='memo'?110:50;
 const attrs=kind==='number'?'type="text" inputmode="numeric" pattern="[0-9,]*"':'type="text"';
 return '<input aria-label="'+label+'" data-field="'+key+'" '+attrs+' maxlength="'+max+'" placeholder="'+placeholder+'" autocomplete="off">';
};
const mirror=key=>'<span class="mirror" data-mirror="'+key+'"></span>';
function field(key,label,editable,kind='text',placeholder=''){
 return editable?input(key,label,kind,placeholder):mirror(key);
}
const output=(key)=>'<span class="calculated" data-calc="'+key+'">0</span>';
function headline(copy){
 return '<div class="form-head"><span class="form-id">'+field('slipNumber','명세표 번호',copy==='supplier','text','No.')+'</span>'+
 '<strong>'+(receipt?'간 이 영 수 증':'거 래 명 세 표')+'</strong><span class="copy-name">'+
 (copy==='supplier'?'공급자 보관용':'공급받는자 보관용')+'</span></div>';
}
function parties(editable){
 if(verticalInvoice){
  return '<div class="vertical-party-details">'+
   '<div class="vertical-date-row"><strong>거래일자</strong>'+field('writtenDate','작성일',editable)+'</div>'+
   '<table class="vertical-party-table" aria-label="공급받는자 및 공급자 정보"><colgroup>'+
   '<col class="vertical-party-side"><col class="vertical-party-field"><col class="vertical-party-data">'+
   '<col class="vertical-party-side"><col class="vertical-party-field"><col class="vertical-party-data">'+
   '</colgroup><tbody>'+
   '<tr><th class="vertical-side-label" rowspan="4" scope="rowgroup">공급받는자</th><th scope="row">상호</th><td>'+field('buyer','공급받는자 상호',editable)+'</td>'+
   '<th class="vertical-side-label" rowspan="4" scope="rowgroup">공급자</th><th scope="row">상호</th><td>'+field('supplier','공급자 상호',editable)+'</td></tr>'+
   '<tr><th scope="row">등록번호</th><td>'+field('buyerNo','공급받는자 등록번호',editable)+'</td>'+
   '<th scope="row">등록번호</th><td>'+field('supplierNo','공급자 등록번호',editable)+'</td></tr>'+
   '<tr><th scope="row">소재지</th><td>'+field('buyerAddress','공급받는자 소재지',editable)+'</td>'+
   '<th scope="row">소재지</th><td>'+field('supplierAddress','공급자 소재지',editable)+'</td></tr>'+
   '<tr><th scope="row">연락처</th><td>'+field('buyerPhone','공급받는자 연락처',editable)+'</td>'+
   '<th scope="row">연락처</th><td>'+field('supplierPhone','공급자 연락처',editable)+'</td></tr>'+
   '</tbody></table></div>';
 }
 return '<table class="parties"><colgroup><col class="p-label"><col class="p-data"><col class="p-label"><col class="p-data"></colgroup><tbody>'+
 '<tr><th>작성일</th><td colspan="3">'+field('writtenDate','작성일',editable)+'</td></tr>'+
 '<tr class="party-supplier party-supplier-start"><th>'+(receipt?'공급자(상호)':'공급자')+'</th><td>'+field('supplier','공급자 상호',editable)+'</td><th>등록번호</th><td>'+field('supplierNo','공급자 사업자번호',editable)+'</td></tr>'+
 '<tr class="party-supplier"><th>소재지</th><td>'+field('supplierAddress','공급자 주소',editable)+'</td><th>연락처</th><td>'+field('supplierPhone','공급자 전화번호',editable)+'</td></tr>'+
 '<tr class="party-buyer party-buyer-start"><th>공급받는자</th><td>'+field('buyer','공급받는자 상호',editable)+'</td><th>담당자</th><td><span class="buyer-contact-entry">'+field('buyerContact','공급받는자 담당자',editable)+'<span class="buyer-honorific">귀하</span></span></td></tr>'+
 '<tr class="party-buyer"><th>소재지</th><td colspan="3">'+field('buyerAddress','공급받는자 주소',editable)+'</td></tr>'+
 '</tbody></table>';
}
function unitRow(i,editable){
 const keys=receipt?['name','spec','qty','price','amount']:['date','name','spec','qty','price','amount','tax','note'];
 const labels={date:'월일',name:'품목',spec:'규격',qty:'수량',price:'단가',amount:receipt?'금액':'공급가액',tax:'세액',note:'비고'};
 return '<tr data-line="'+i+'">'+keys.map(k=>{
  const rawKey='item-'+i+'-'+k;
  if(k==='amount'||k==='tax')return '<td class="numeric">'+output(rawKey)+'</td>';
  const type=(k==='qty'||k==='price')?'number':'text';
  return '<td class="'+(k==='name'?'product-name ':'')+((k==='qty'||k==='price')?'numeric':'')+'">'+field(rawKey,labels[k]+' '+(i+1)+'행',editable,type)+'</td>';
 }).join('')+'</tr>';
}
function itemsTable(editable){
 const headers=receipt?['품 목','규 격','수 량','단 가','금 액']:['월일','품 목','규 격','수 량','단 가','공급가액','세 액','비 고'];
 const classes=receipt?['name','spec','qty','price','amount']:['date','name','spec','qty','price','amount','tax','note'];
 return '<table class="item-table"><colgroup>'+classes.map(x=>'<col class="col-'+x+'">').join('')+'</colgroup>'+
 '<thead><tr>'+headers.map(x=>'<th scope="col">'+x+'</th>').join('')+'</tr></thead><tbody>'+
 rows.map(i=>unitRow(i,editable)).join('')+'</tbody></table>';
}
function preface(){
 return '<div class="amount-line"><span'+(receipt?'':' data-tax-caption')+'>'+(receipt?'영수 합계금액':'합계금액(부가세별도)')+'</span><strong>₩ '+output(receipt?'grand':'invoiceTotal')+'</strong><span>원정</span></div>';
}
function summary(editable){
 if(receipt){
  return '<table class="summary receipt-summary"><tbody>'+
   '<tr><th>공급가액</th><td>₩ '+output('supply')+'</td><th>영수금액</th><td>₩ '+output('grand')+'</td></tr>'+
   '</tbody></table>'+
   '<div class="receipt-ack">위 금액을 정히 영수합니다.</div>';
 }
 const vat=editable?'<button id="vat-toggle" class="vat-toggle" type="button" aria-label="부가세 자동입력 전환" aria-pressed="false" data-field="vatMode" value="none">부가세 자동입력</button>':mirror('vatMode');
 return '<table class="summary invoice-summary"><tbody>'+
  '<tr><th>공급가액</th><td>₩ '+output('supply')+'</td><th>부가세 '+vat+'</th><td>₩ '+output('tax')+'</td></tr>'+
  '<tr><th>전 잔고</th><td>'+ (editable?field('previous','전 잔고',true,'number','0'):mirror('previous'))+'</td><th>입 금</th><td>'+(editable?field('paid','입금액',true,'number','0'):mirror('paid'))+'</td></tr>'+
  '<tr><th>잔 금</th><td>₩ '+output('balance')+'</td><th>청구합계</th><td>₩ '+output('grand')+'</td></tr>'+
  '</tbody></table>';
}
function copy(type){
 const editable=type==='supplier';
 return '<article class="slip" data-copy="'+type+'">'+headline(type)+parties(editable)+preface()+itemsTable(editable)+summary(editable)+
  '<div class="notice">'+(receipt?'공급자 서명 또는 날인: __________________':'추가 메모: ')+(receipt?'':field('memo','메모',editable))+'</div>'+
  '<div class="bottom-row"><span>'+(receipt?'위와 같이 영수함':'위와 같이 거래함')+'</span><span>인수자: __________________</span></div></article>';
}
root.innerHTML='<section class="print-sheet '+mode+(verticalInvoice?' invoice-vertical':'')+'" aria-label="'+(receipt||verticalInvoice?'A4 세로':'A4 가로')+' 2부 인쇄 양식">'+
 '<span class="cut-marker" aria-hidden="true"><span class="cut-label">✂ 절취선</span></span>'+
 '<div class="slips">'+copy('supplier')+copy('recipient')+'</div></section>';
function read(key){
 const field=root.querySelector('.slip[data-copy="supplier"] [data-field="'+key+'"]');
 return field?field.value:'';
}
function setCalculated(key,value){
 root.querySelectorAll('[data-calc="'+key+'"]').forEach(el=>{el.textContent=blankMode?'':won(value)});
}
function synchronize(){
 for(const el of root.querySelectorAll('.slip[data-copy="supplier"] [data-field]')){
  const value=el.value;
  const key=el.dataset.field;
  root.querySelectorAll('.slip[data-copy="recipient"] [data-mirror="'+key+'"]').forEach(target=>{
   target.textContent=key==='vatMode'?(value==='tax'?'10%':'미계산'):value;
  });
 }
 let supply=0,tax=0;
 for(const i of rows){
  const qty=cleanNumber(read('item-'+i+'-qty'));
  const price=cleanNumber(read('item-'+i+'-price'));
  const amount=qty*price;
  const lineTax=receipt||read('vatMode')!=='tax'?0:Math.round(amount*.1);
  supply+=amount;tax+=lineTax;
  setCalculated('item-'+i+'-amount',amount);
  if(!receipt)setCalculated('item-'+i+'-tax',lineTax);
 }
 if(!receipt){
  const enabled=read('vatMode')==='tax';
  root.querySelectorAll('[data-tax-caption]').forEach(el=>{el.textContent=enabled?'합계금액(부가세포함)':'합계금액(부가세별도)'});
  setCalculated('invoiceTotal',supply+tax);
 }
 const previous=receipt?0:cleanNumber(read('previous'));
 const paid=receipt?0:cleanNumber(read('paid'));
 const grand=supply+tax+previous;
 const balance=Math.max(0,grand-paid);
 const values={supply,tax,previous,paid,grand,balance};
 for(const key of totalFields)setCalculated(key,values[key]);
 if(!receipt&&paid>grand)feedback.textContent='입금액이 청구합계를 초과합니다. 입력값을 확인하세요.';
 else feedback.textContent='';
}
root.addEventListener('input',synchronize);
root.addEventListener('change',synchronize);
if(!receipt){
 root.addEventListener('click',event=>{
  const toggle=event.target.closest('#vat-toggle');
  if(!toggle)return;
  const enabled=toggle.value!=='tax';
  toggle.value=enabled?'tax':'none';
  toggle.textContent=enabled?'부가세 별도':'부가세 자동입력';
  toggle.setAttribute('aria-pressed',String(enabled));
  synchronize();
 });
}
const now=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
const dateField=root.querySelector('.slip[data-copy="supplier"] [data-field="writtenDate"]');
if(dateField&&!blankMode)dateField.value=now;
synchronize();
document.getElementById('print-form').addEventListener('click',()=>window.print());
document.getElementById('clear-form').addEventListener('click',()=>{
 if(!window.confirm('모든 입력 내용을 초기화할까요?'))return;
 root.querySelectorAll('.slip[data-copy="supplier"] input').forEach(i=>{i.value=''});
 const vat=root.querySelector('#vat-toggle');
 if(vat){
  vat.value='none';
  vat.textContent='부가세 자동입력';
  vat.setAttribute('aria-pressed','false');
 }
 if(dateField)dateField.value=now;
 synchronize();
});
if(blankMode&&new URLSearchParams(location.search).get('print')==='1'){
 window.addEventListener('load',()=>{
  window.focus();
  setTimeout(()=>window.print(),350);
 },{once:true});
}
