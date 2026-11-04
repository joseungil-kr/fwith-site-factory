import test from 'node:test';
import assert from 'node:assert/strict';
import {checkedSettings,makeReceiptRows,receiptShippingLabel,rasterBand,testReceiptBytes,SerialReceiptPrinter,PAPER_WIDTHS,WIDTH_CHOICES,buildRasterJob} from '../public/serial-printer.js';

test('COM1..COM6 only, COM4 9600 default profile supported',()=>{
  assert.deepEqual(checkedSettings({slot:'4',baudRate:'9600',paperMm:'58'}),{slot:4,baudRate:9600,paperMm:58,dotWidth:384,fontSize:26,autoCut:true});
  assert.deepEqual(Object.keys(PAPER_WIDTHS),['58','80']);
  for (const v of [0,7,'COM4','abc']) assert.throws(()=>checkedSettings({slot:v,baudRate:9600,paperMm:58}));
  assert.throws(()=>checkedSettings({slot:4,baudRate:300,paperMm:58}));
  assert.throws(()=>checkedSettings({slot:4,baudRate:9600,paperMm:70}));
});
test('Korean invoice content includes customer, VAT and manual item',()=>{
  const rows=makeReceiptRows({
    order:{id:10,order_date:'2026-11-03',status:'issued',supply:23000,tax:2300,total:25300,
           client:{business:'안산 중앙점',person:'테스트담당',phone:'010-1111-2222'}},
    items:[{name:'잉어반죽',qty:2,unit_price:11000,line_total:22000},
           {name:'기타 배송비',qty:1,unit_price:1000,line_total:1000}]
  });
  const text=rows.map(x=>x.text||'').join(' | ');
  for(const word of ['안산 중앙점','잉어반죽','기타 배송비','23,000원','2,300원','25,300원']) assert.ok(text.includes(word));
});
test('GS v 0 image encodes black pixels and preserves byte/padding order',()=>{
  const width=10,height=2,pixels=new Uint8ClampedArray(width*height*4).fill(255);
  for (const n of [0, width+8]) { for (let channel=0;channel<3;channel++) pixels[n*4+channel]=0; }
  const cmd=rasterBand({data:pixels,width,height},0,2);
  assert.deepEqual([...cmd.slice(0,8)],[29,118,48,0,2,0,2,0]);
  assert.deepEqual([...cmd.slice(8)],[128,0,0,128]);
});
test('ASCII test print carries serial settings without pretending to identify actual Windows COM port',()=>{
  const cmd=testReceiptBytes({slot:4,baudRate:9600,paperMm:58});
  assert.deepEqual([...cmd.slice(0,2)],[27,64]);
  const message=new TextDecoder().decode(cmd.slice(2));
  assert.ok(message.includes('PROFILE COM4'));
  assert.ok(message.includes('9600'));
});
test('Web Serial requestPort and 8N1 open, safe send, disconnect',async()=>{
  const writes=[], opened=[], port={
    writable:{getWriter:()=>({write:async b=>writes.push([...b]),releaseLock(){}})},
    open:async args=>opened.push(args),
    close:async ()=>{port.writable=null}
  };
  const serial={requestPort:()=>Promise.resolve(port),getPorts:()=>Promise.resolve([port])};
  const p=new SerialReceiptPrinter(serial);
  await p.connect({slot:4,baudRate:9600,paperMm:58});
  assert.equal(p.connected,true);
  assert.equal(opened[0].baudRate,9600);
  assert.equal(opened[0].dataBits,8);
  assert.equal(opened[0].stopBits,1);
  assert.equal(opened[0].parity,'none');
  await p.test();
  assert.ok(writes.length>0);
  await p.disconnect();
  assert.equal(p.connected,false);
});
test('Already-allowed reconnect fails closed with multiple ports',async()=>{
  const p=new SerialReceiptPrinter({requestPort:()=>Promise.reject(new Error('should not call')),getPorts:async()=>[{},{}]});
  await assert.rejects(p.reconnectGranted({slot:4,baudRate:9600,paperMm:58}),/한 개가 아닙니다/);
});

test('80mm SAM4S 512-dot default, font 26px, cut enabled; adjustable width and type',()=>{
  assert.equal(PAPER_WIDTHS[80],512);
  assert.equal(PAPER_WIDTHS[58],384);
  assert.ok(WIDTH_CHOICES[80].includes(432));
  assert.ok(WIDTH_CHOICES[80].includes(512));
  const s=checkedSettings({slot:4,baudRate:9600,paperMm:80});
  assert.equal(s.dotWidth,512);
  assert.equal(s.fontSize,26);
  assert.equal(s.autoCut,true);
  const alt=checkedSettings({slot:4,baudRate:9600,paperMm:80,dotWidth:448,fontSize:30,autoCut:false});
  assert.equal(alt.dotWidth,448);
  assert.equal(alt.fontSize,30);
  assert.equal(alt.autoCut,false);
  assert.throws(()=>checkedSettings({slot:4,baudRate:9600,paperMm:58,dotWidth:576}));
});
test('full-width single raster image, linefeed, and one GS V 0 auto-cut from working printtest script',()=>{
  const width=512,height=150,raw=new Uint8ClampedArray(width*height*4).fill(255);
  const command=buildRasterJob({width,height,data:raw},true);
  assert.equal(command.length,3,'short receipt must use one GS v 0 command');
  assert.deepEqual([...command[0]],[0x1b,0x40]);
  assert.deepEqual([...command[1].subarray(0,8)],[0x1d,0x76,0x30,0,64,0,150,0]);
  assert.equal(command[1].length,8+64*150);
  assert.deepEqual([...command[2]],[10,10,10,0x1d,0x56,0]);
  assert.deepEqual([...buildRasterJob({width,height,data:raw},false)[2]],[10,10,10]);
});

test('전 잔고는 부가세와 같은 글자 유형이고 입금처는 하단에 출력',()=>{const r=makeReceiptRows({order:{id:11,order_date:'2026-11-03',status:'issued',supply:93000,tax:0,total:93000,previous_balance:100000,amount_due:193000,client:{business:'안산 중앙점'},bank:{bank_name:'테스트은행',account_number:'987-654',account_holder:'테스트예금주'}},items:[{name:'잉어반죽',qty:1,unit_price:93000,line_total:93000}]});const txt=r.map(x=>x.text||'').join('|');for(const s of ['공급가액: 93,000원','부가세: 0원','전 잔고: 100,000원','합계: 193,000원','테스트은행 987-654','예금주: 테스트예금주'])assert.ok(txt.includes(s));assert.equal(r.find(x=>x.text?.startsWith('전 잔고')).kind,r.find(x=>x.text?.startsWith('부가세')).kind);});

test('배송상태 출력은 취소를 최우선 처리하고 기존 출고는 미확인으로 남김',()=>{
  assert.equal(receiptShippingLabel({status:'issued',delivery_status:'pending'}),'출고완료(배송전)');
  assert.equal(receiptShippingLabel({status:'issued',delivery_status:'delivered'}),'출고완료(배송완료)');
  assert.equal(receiptShippingLabel({status:'issued',delivery_status:'unknown'}),'출고완료(배송상태 미확인)');
  assert.equal(receiptShippingLabel({status:'cancelled',delivery_status:'delivered'}),'취소됨');
  const o={id:31,order_date:'2026-11-04',status:'issued',delivery_status:'delivered',
    supply:1000,tax:0,total:1000,client:{business:'테스트'}};
  const rows=makeReceiptRows({order:{...o,memo:'내부 참고',bank:{company_name:'백세푸드',company_email:'private@example.com',company_business_no:'000-00-00000',company_address:'테스트 공급자 주소',company_phone:'031-000-0000'},client:{business:'테스트 거래처',person:'담당자',phone:'010-0000-0000',address:'테스트 배송 주소'}},items:[]});
  const text=rows.map(row=>row.text||'').join('|');
  for(const word of ['상태:','비고:','이메일:','출고단가:','private@example.com','내부 참고'])assert.ok(!text.includes(word),word+' must not appear on printed receipt');
  for(const word of ['전표번호:','출고일:','거래처:','공급자: 백세푸드','사업자등록번호:','테스트 배송 주소','테스트 공급자 주소','연락처:','공급가액:','합계:'])assert.ok(text.includes(word),word+' must remain');
  const recipient=rows.findIndex(row=>row.text?.includes('테스트 배송 주소'));
  const supplier=rows.findIndex(row=>row.text==='공급자: 백세푸드');
  const items=rows.findIndex(row=>row.text==='품명 / 수량 x 단가');
  assert.ok(recipient<supplier && supplier<items,'recipient, supplier, items must stay in order');
  assert.ok(rows.slice(recipient+1,supplier).some(row=>row.line),'divider between recipient and supplier');
  assert.ok(rows.slice(supplier+1,items).some(row=>row.line),'divider before item table');
  const cancelled=makeReceiptRows({order:{...o,status:'cancelled'},items:[]});
  assert.ok(cancelled.some(row=>row.text==='[출고 취소된 명세표]'),'Cancelled slip must keep safety warning');
});
