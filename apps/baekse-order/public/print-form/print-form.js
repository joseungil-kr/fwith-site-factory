import {makeDemoDocument,fromOrderDetail,renderPrintSheets,paginate} from './print-data.mjs';
const pages=document.getElementById('pages');
const status=document.getElementById('status');
const description=document.getElementById('description');
const button=document.getElementById('print-now');
const demoLink=document.getElementById('demo-link');
const liveMode=new URL(location.href).searchParams.get('mode')==='invoice';
let hasDocument=false;
button.disabled=true;
function showDocument(documentData){
 const html=renderPrintSheets(documentData);
 pages.innerHTML=html;
 hasDocument=true;
 const count=paginate(documentData.lines).length;
 status.textContent=count+'장 · 총 '+documentData.lines.length+'품목 · 공급자용 '+count+'부 / 공급받는 자용 '+count+'부';
 description.textContent=(documentData.sample?'33품목 가상 샘플 · 실제 거래 아님':documentData.voucher+' · 발행 당시 기록')+
  ' · '+count+'페이지 · 한 장에 동일 명세표 2부';
 document.title=(documentData.sample?'33품목 샘플':'거래명세표 '+documentData.voucher)+' | A4 가로 2분할';
 button.disabled=false;
}
button.addEventListener('click',()=>{if(hasDocument)window.print();});
if(!liveMode){
 showDocument(makeDemoDocument());
}else{
 pages.innerHTML='<div class="missing">선택한 거래명세표를 불러오고 있습니다.</div>';
 status.textContent='관리자 화면에서 선택한 명세표를 전달받는 중입니다.';
 demoLink.hidden=true;
 window.addEventListener('message',event=>{
  if(event.origin!==location.origin||event.source!==window.opener||event.data?.type!=='BAEKSE_PRINT_DATA')return;
  try{
   const model=fromOrderDetail(event.data.detail);
   showDocument(model);
  }catch(error){
   pages.innerHTML='<div class="missing">명세표를 표시할 수 없습니다. 원래 화면에서 명세표를 다시 선택해 주세요.</div>';
   status.textContent='출력 데이터가 올바르지 않습니다.';
  }
 },{once:false});
 if(window.opener)window.opener.postMessage({type:'BAEKSE_PRINT_READY'},location.origin);
 else{
  pages.innerHTML='<div class="missing">관리자 화면에서 거래명세표를 선택한 후 A4 가로 2분할을 눌러 주세요.</div>';
  status.textContent='거래명세표 정보가 없습니다.';
 }
}
