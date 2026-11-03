const $=selector=>document.querySelector(selector);
const fmt=n=>(Number(n)||0).toLocaleString('ko-KR')+'원';
const toDate=new Date(Date.now()+9*3600000).toISOString().slice(0,10);
const token=location.hash.slice(1).trim();
let products=[],requestKey=null,working=false;
const statusLabels={pending:'접수 대기',fulfilled:'출고 완료',cancelled:'취소됨'};
const wait=async(path,payload)=>{
 const res=await fetch('/api/buyer/'+path,{method:'POST',headers:{'Content-Type':'application/json'},
   cache:'no-store',referrerPolicy:'no-referrer',body:JSON.stringify({token,...payload})});
 const data=await res.json().catch(()=>({error:'서버 응답을 확인할 수 없습니다.'}));
 if(!res.ok)throw new Error(data.error||'요청이 실패했습니다.');
 return data;
};
const elem=(tag,className,text)=>{
 const node=document.createElement(tag);
 if(className)node.className=className;
 if(text!=null)node.textContent=String(text);
 return node;
};
function parseItems(){
 return [...document.querySelectorAll('[data-product-id]')].map(input=>{
   const qty=Number(input.value||0),product_id=Number(input.dataset.productId);
   if(!Number.isSafeInteger(qty)||qty<0||qty>10000)throw new Error('제품 수량은 0~10,000개로 입력해 주세요.');
   return {product_id,qty};
 }).filter(item=>item.qty>0);
}
function refreshTotal(){
 try {
  const items=parseItems();
  const sum=items.reduce((total,item)=>{
    const p=products.find(p=>p.id===item.product_id);
    return total+item.qty*Number(p?.price||0);
  },0);
  $('#estimated').textContent=fmt(sum);
  $('#estimated').classList.remove('invalid');
 }catch(e){$('#estimated').textContent=e.message;$('#estimated').classList.add('invalid')}
}
function renderProducts(){
 const root=$('#buyer-products');root.replaceChildren();
 for(const p of products){
  const row=elem('div','buyer-product');
  const info=elem('div','buyer-product-info');
  info.append(elem('strong','',p.name),elem('small','',fmt(p.price)+' / 개'));
  const input=elem('input','qty');
  input.type='number';input.min='0';input.max='10000';input.step='1';
  input.value='0';input.inputMode='numeric';input.dataset.productId=p.id;
  input.setAttribute('aria-label',p.name+' 발주수량');
  const qty=elem('div','qty-box');
  const label=elem('span','', '수량');
  qty.append(label,input);
  row.append(info,qty);root.append(row);
 }
 root.addEventListener('input',refreshTotal);
}
function renderHistory(history){
 const target=$('#request-history');target.replaceChildren();
 if(!history?.length){target.textContent='발주 내역이 없습니다.';return}
 for(const item of history){
  const row=elem('div','history-row');
  row.append(elem('span','', '발주 #'+item.id+' · '+item.requested_delivery),
    elem('strong','history-'+item.status,statusLabels[item.status]||item.status));
  target.append(row);
 }
}
async function load(){
 try {
  if(!/^[a-f0-9]{64}$/.test(token))throw new Error('거래처 발주 링크가 올바르지 않습니다. 전달받은 링크를 다시 확인하세요.');
  const data=await wait('overview',{});
  products=data.products||[];
  $('#supplier').textContent=data.supplier_name||'백세푸드';
  $('#business-name').textContent=data.client.business;
  $('#delivery-date').min=toDate;
  $('#delivery-date').value=toDate;
  const latest=new Date(Date.now()+90*86400000+9*3600000).toISOString().slice(0,10);
  $('#delivery-date').max=latest;
  renderProducts();renderHistory(data.history);
  $('#buyer-content').classList.remove('hidden');
 }catch(e){
  $('#failed').textContent=e.message;
  $('#failed').classList.remove('hidden');
 }finally{$('#loading').classList.add('hidden')}
}
$('#buyer-form').addEventListener('submit',async event=>{
 event.preventDefault();
 if(working)return;
 const output=$('#result');
 try{
  const items=parseItems();
  if(!items.length)throw new Error('발주할 제품의 수량을 하나 이상 입력해 주세요.');
  const requested_delivery=$('#delivery-date').value;
  if(!requested_delivery)throw new Error('희망 납품일을 선택해 주세요.');
  if(!requestKey)requestKey=crypto.randomUUID();
  working=true;$('#submit-order').disabled=true;output.textContent='발주 요청을 접수하고 있습니다.';
  const result=await wait('submit',{request_key:requestKey,requested_delivery,note:$('#request-note').value,items});
  output.textContent='발주 #'+result.id+'번 접수 완료. 공급업체가 확인한 후 출고합니다.';
  requestKey=null;
  document.querySelectorAll('[data-product-id]').forEach(x=>{x.value='0'});
  $('#request-note').value='';
  refreshTotal();
  const latest=await wait('overview',{});
  renderHistory(latest.history);
 }catch(e){output.textContent=e.message}
 finally{working=false;$('#submit-order').disabled=false}
});
load();
