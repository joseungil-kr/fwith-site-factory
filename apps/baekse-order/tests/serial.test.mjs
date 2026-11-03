import test from 'node:test';
import assert from 'node:assert/strict';
import {checkedSettings,makeReceiptRows,rasterBand,testReceiptBytes,SerialReceiptPrinter,PAPER_WIDTHS} from '../public/serial-printer.js';

test('COM1..COM6 only, COM4 9600 default profile supported',()=>{
  assert.deepEqual(checkedSettings({slot:'4',baudRate:'9600',paperMm:'58'}),{slot:4,baudRate:9600,paperMm:58});
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
