// Shared, read-only A4 2-up invoice renderer. No API access or writes.
export const LINES_PER_PAGE=15;
const escapeMap={'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'};
export const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,char=>escapeMap[char]);
export const amount=value=>Math.round(Number(value)||0);
export const won=value=>amount(value).toLocaleString('ko-KR');
function text(value){return String(value??'').trim();}
function positive(value){return Math.max(0,amount(value));}
function dayOf(date){const d=text(date);return /^\d{4}-\d\d-\d\d$/.test(d)?d.slice(5).replace('-','/'):'';}

export function paginate(lines,perPage=LINES_PER_PAGE){
 if(!Array.isArray(lines))throw new TypeError('품목 배열이 필요합니다');
 if(!Number.isSafeInteger(perPage)||perPage<1)throw new RangeError('행 수가 올바르지 않습니다');
 const pages=[];
 for(let i=0;i<lines.length;i+=perPage)pages.push(lines.slice(i,i+perPage));
 return pages.length?pages:[[]];
}

function taxesByLine(lines,invoiceTax){
 const tax=positive(invoiceTax),values=lines.map(x=>positive(x.total)),sum=values.reduce((a,b)=>a+b,0);
 if(!tax||!sum)return lines.map(()=>0);
 const entries=values.map((v,index)=>{
  const exact=v/sum*tax;
  return {index,floor:Math.floor(exact),fraction:exact-Math.floor(exact)};
 });
 const allocated=entries.map(x=>x.floor);
 const remainder=tax-allocated.reduce((a,b)=>a+b,0);
 const order=[...entries].sort((a,b)=>b.fraction-a.fraction||a.index-b.index);
 for(let i=0;i<remainder;i++)allocated[order[i%order.length].index]++;
 return allocated;
}
function lineValue(item,internal){
 const qty=positive(item.qty),price=positive(internal?item.cost:item.unit_price);
 const supplied=internal?qty*price:Number(item.line_total);
 return {name:text(item.name)||'품목명 미입력',spec:text(item.spec),qty,price,
  total:Number.isFinite(supplied)&&!internal?positive(supplied):qty*price};
}
export function fromOrderDetail(detail){
 if(!detail||!detail.order||!Array.isArray(detail.items))throw new TypeError('명세표 정보가 없습니다');
 const o=detail.order,c=o.client||{},b=o.bank||{},internal=o.order_type==='internal';
 const lines=detail.items.map(x=>lineValue(x,internal));
 const supply=internal?lines.reduce((n,x)=>n+x.total,0):positive(o.supply??lines.reduce((n,x)=>n+x.total,0));
 const tax=internal?0:positive(o.tax);
 const previous=internal?0:positive(o.previous_balance);
 const due=internal?0:positive(o.amount_due??(supply+tax+previous));
 const allocated=taxesByLine(lines,tax);
 return {
  kind:internal?'internal':'sale',sample:false,cancelled:o.status!=='issued',
  voucher:'B'+text(o.order_date).replace(/-/g,'')+'-'+String(o.id??'').padStart(4,'0'),
  date:text(o.order_date),
  supplier:{name:text(b.company_name)||'백세푸드',number:text(b.company_business_no),phone:text(b.company_phone),address:text(b.company_address)},
  recipient:{name:text(c.business),person:text(c.person),number:text(c.business_no),phone:text(c.phone),address:text(c.address)},
  bank:[b.bank_name,b.account_number,b.account_holder].map(text).filter(Boolean).join(' / '),
  lines:lines.map((line,index)=>({...line,tax:allocated[index]})),
  supply,tax,previous,paid:null,total:due,balance:due
 };
}
const productNames=[
 '잉어반죽 5kg','팥앙금 5kg','슈크림 5kg','꼬치어묵 50개','어묵육수 1kg',
 '종이컵 13oz','종이컵 홀더','종이봉투 소형','붕어빵 종이봉투','냅킨 1팩',
 '나무젓가락 100개','꼬치막대 100개','위생장갑 100매','포장용 비닐봉투','소금 1kg',
 '설탕 3kg','계피가루 500g','식용유 1.8L','올리고당 1.2kg','시나몬시럽 1L',
 '초코소스 2kg','가루녹차 500g','우유 1L','버터 450g','치즈 1kg',
 '팥 토핑 1kg','찹쌀가루 1kg','콘치즈 토핑 2kg','컵 받침대 50개','종이 트레이 100개',
 '분말육수 2kg','일회용 수저 100개','식품용 랩 30m'
];
export function makeDemoDocument(){
 const lines=productNames.map((name,index)=>{
  const qty=index%5+1,price=1500+(index%9)*850;
  return {name,spec:index%2?'1팩':'1박스',qty,price,total:qty*price};
 });
 const supply=lines.reduce((n,x)=>n+x.total,0),tax=Math.round(supply*.1);
 const previous=100000,paid=50000,total=supply+tax+previous;
 const allocated=taxesByLine(lines,tax);
 return {
  kind:'sale',sample:true,cancelled:false,voucher:'DEMO-20261109-0033',date:'2026-11-09',
  supplier:{name:'백세푸드 (시연)',number:'000-00-00000',phone:'000-0000-0000',address:'가상 공급자 주소'},
  recipient:{name:'가상 거래처 중앙점',person:'가상 담당자',number:'000-00-00000',phone:'000-0000-0000',address:'가상 거래처 주소'},
  bank:'예시은행 / 000-0000-0000 / 가상 예금주',
  lines:lines.map((line,index)=>({...line,tax:allocated[index]})),
  supply,tax,previous,paid,total,balance:total-paid
 };
}
function th(label){return '<th scope="row">'+escapeHtml(label)+'</th>';}
function cell(value,cls=''){return '<td'+(cls?' class="'+cls+'"':'')+'>'+escapeHtml(value)+'</td>';}
function copyHtml(doc,chunk,page,totalPages,copyType){
 const vendor=copyType==='vendor';
 const title=doc.kind==='internal'?'내 부 출 고 명 세 표':'거 래 명 세 표';
 const copyLabel=vendor?'공급자 보관용':'공급받는 자 보관용';
 const rows=Array.from({length:LINES_PER_PAGE},(_,i)=>{
  const line=chunk[i],lineIndex=(page-1)*LINES_PER_PAGE+i;
  if(!line)return '<tr class="empty-line"><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>';
  const cols=[dayOf(doc.date),line.name,line.spec,won(line.qty),won(line.price),won(line.total),doc.kind==='internal'?'—':won(line.tax),''];
  return '<tr class="filled-line" data-line-index="'+(lineIndex+1)+'">'+cols.map((v,k)=>cell(v,k===1?'item-name':k>2&&k<7?'numeric':'')).join('')+'</tr>';
 }).join('');
 const sample=doc.sample?'<span class="sample-mark">가상 샘플 · 실제 거래 아님</span>':'';
 const cancelled=doc.cancelled?'<span class="cancel-mark">출고취소</span>':'';
 const bank=doc.kind==='internal'?'내부출고 · 매출 및 미수금 미반영':doc.bank?'입금처: '+doc.bank:'입금처 미등록';
 const invoiceAmount=doc.kind==='internal'?doc.supply:doc.total;
 // Net charge is the current supply plus tax; total additionally includes previous balance.
 const currentCharge=doc.kind==='internal'?'—':'₩ '+won(doc.supply+doc.tax);
 const grandTotal=doc.kind==='internal'?'—':'₩ '+won(doc.total);
 return [
  '<article class="slip-copy" data-copy="'+(vendor?'vendor':'customer')+'" data-page="'+page+'">',
  '<div class="slip-top"><span class="slip-number">'+escapeHtml(doc.voucher)+'</span><h2>'+title+'</h2><span class="slip-type">'+copyLabel+'</span></div>',
  '<table class="party-table" aria-label="사업자 및 거래처 정보"><colgroup><col style="width:13%"><col style="width:36%"><col style="width:17%"><col style="width:34%"></colgroup><tbody>',
  '<tr>'+th('작성일')+cell(doc.date,'date-value')+th('공급자 등록번호')+cell(doc.supplier.number,'party-number')+'</tr>',
  '<tr>'+th('공급받는자')+cell(doc.recipient.name,'party-name')+th('공급자 상호')+cell(doc.supplier.name,'party-name')+'</tr>',
  '<tr>'+th('연락처')+cell(doc.recipient.phone)+th('연락처')+cell(doc.supplier.phone)+'</tr>',
  '<tr>'+th('주소')+cell(doc.recipient.address,'wide-addr')+th('주소')+cell(doc.supplier.address,'wide-addr')+'</tr>',
  '</tbody></table>',
  '<div class="total-banner"><strong>합계금액<br> (전체)</strong><div>금 <b>'+won(invoiceAmount)+'</b> 원정 <span>(₩ '+won(invoiceAmount)+')</span></div></div>',
  '<table class="items-table" aria-label="품목 명세 15행"><colgroup><col style="width:9%"><col style="width:25%"><col style="width:11%"><col style="width:8%"><col style="width:12%"><col style="width:16%"><col style="width:10%"><col style="width:9%"></colgroup>',
  '<thead><tr><th>월일</th><th>품 목</th><th>규 격</th><th>수량</th><th>단 가</th><th>공급가액</th><th>세 액</th><th>비고</th></tr></thead><tbody>'+rows+'</tbody></table>',
  '<table class="summary-table" aria-label="금액 정산"><colgroup><col style="width:12%"><col style="width:21%"><col style="width:12%"><col style="width:21%"><col style="width:12%"><col style="width:22%"></colgroup><tbody>',
  '<tr>'+th(doc.kind==='internal'?'원가합계':'공급가액')+cell('₩ '+won(doc.supply),'numeric')+th('부가세')+cell('₩ '+won(doc.tax),'numeric')+th('청구액')+cell(currentCharge,'numeric')+'</tr>',
  '<tr>'+th('전 잔고')+cell(doc.kind==='internal'?'—':'₩ '+won(doc.previous),'numeric')+'<td colspan="2" class="summary-blank"></td>'+th('총액')+cell(grandTotal,'numeric')+'</tr>',
  '</tbody></table>',
  '<div class="bank-line">'+escapeHtml(bank)+'</div>',
  '<div class="slip-footer"><span>인수자: __________________</span><span>'+page+' / '+totalPages+' 페이지 · 전체 '+doc.lines.length+'품목</span></div>',
  sample,cancelled,'</article>'
 ].join('');
}
export function renderPrintSheets(doc){
 if(!doc||!Array.isArray(doc.lines))throw new TypeError('잘못된 출력 자료입니다');
 return paginate(doc.lines).map((chunk,index)=>{
  const page=index+1,totalPages=Math.ceil(Math.max(1,doc.lines.length)/LINES_PER_PAGE);
  return '<section class="paper-sheet" data-print-page="'+page+'" aria-label="A4 '+page+'페이지">'+
   '<div class="cut-line" aria-hidden="true"><span>✂ 절취선</span></div>'+
   copyHtml(doc,chunk,page,totalPages,'vendor')+
   copyHtml(doc,chunk,page,totalPages,'customer')+
   '</section>';
 }).join('');
}
