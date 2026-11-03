/**
 * Local-only Web Serial thermal receipt printing.
 * No server or external print relay; the browser must explicitly grant port access.
 * Browser APIs cannot enumerate Windows COM numbers: COM1..COM6 are USER-ASSIGNED labels.
 * ESC/POS raster uses the documented GS v 0 command so Korean glyphs are drawn as pixels.
 */
export const COM_SLOTS = Object.freeze([1, 2, 3, 4, 5, 6]);
export const BAUD_RATES = Object.freeze([4800, 9600, 19200, 38400, 115200]);
export const PAPER_WIDTHS = Object.freeze({58: 384, 80: 512});
export const WIDTH_CHOICES = Object.freeze({58:[360,384], 80:[384,416,432,448,480,512,576]});
export const FONT_CHOICES = Object.freeze([22,26,30]);
const ESC = 0x1b, GS = 0x1d;
const formatWon = v => new Intl.NumberFormat('ko-KR').format(Number(v) || 0) + '원';

export function checkedSettings(raw) {
  const slot = Number(raw.slot), baudRate = Number(raw.baudRate), paperMm = Number(raw.paperMm);
  if (!COM_SLOTS.includes(slot)) throw new Error('COM1~COM6 중에서 선택하세요.');
  if (!BAUD_RATES.includes(baudRate)) throw new Error('지원하는 통신 속도를 선택하세요.');
  if (!Object.prototype.hasOwnProperty.call(PAPER_WIDTHS, paperMm)) {
    throw new Error('용지 폭을 58mm 또는 80mm로 선택하세요.');
  }
  const dotWidth = Number(raw.dotWidth ?? PAPER_WIDTHS[paperMm]);
  const fontSize = Number(raw.fontSize ?? 26);
  if (!WIDTH_CHOICES[paperMm].includes(dotWidth)) throw new Error('선택한 용지에서 사용할 수 없는 인쇄폭입니다.');
  if (!FONT_CHOICES.includes(fontSize)) throw new Error('글자 크기를 22, 26, 30 중에서 선택하세요.');
  const autoCut = raw.autoCut !== false;
  return {slot, baudRate, paperMm, dotWidth, fontSize, autoCut};
}

export function makeReceiptRows(invoice) {
  if (!invoice || !invoice.order || !Array.isArray(invoice.items)) {
    throw new Error('출력할 거래명세표를 먼저 선택하세요.');
  }
  const o = invoice.order;
  const c = o.client || {};
  const code = 'B' + String(o.order_date || '').replaceAll('-', '') + '-' +
    String(o.id || '').padStart(4, '0');
  const rows = [
    {text: String(o.bank?.company_name||'백세푸드'),align:'center',kind:'title'},
    {text: '거 래 명 세 표',align:'center',kind:'subtitle'},
    {text: '전표: ' + code},
    {text: '일자: ' + String(o.order_date || '')},
    {text: '거래처: ' + String(c.business || '')},
    {text: '담당자: ' + String(c.person || '') + '  ' + String(c.phone || '')},
  ];
  const company=o.bank||{};
  if(company.company_business_no)rows.push({text:'공급자 사업자번호: '+company.company_business_no});
  if(company.company_phone)rows.push({text:'공급자 연락처: '+company.company_phone});
  if(company.company_email)rows.push({text:'공급자 이메일: '+company.company_email});
  if(company.company_address)rows.push({text:'공급자 주소: '+company.company_address});
  if (c.business_no) rows.push({text: '사업자번호: ' + String(c.business_no)});
  if (c.address) rows.push({text: '주소: ' + String(c.address)});
  rows.push({line:true});
  rows.push({text:'품명 / 수량 x 단가',kind:'bold'});
  for (const item of invoice.items) {
    rows.push({text:String(item.name || ''),kind:'bold'});
    rows.push({
      text:String(item.qty) + ' x ' + formatWon(item.unit_price) + ' = ' + formatWon(item.line_total),
      align:'right'
    });
  }
  rows.push({line:true});
  rows.push({text:'공급가액: ' + formatWon(o.supply),align:'right'});
  rows.push({text:'부가세: ' + formatWon(o.tax),align:'right'});
  rows.push({text:'전 잔고: ' + formatWon(o.previous_balance||0),align:'right'});
  rows.push({text:'합계: ' + formatWon(o.amount_due??(Number(o.total)+Number(o.previous_balance||0))),align:'right',kind:'total'});
  if (o.status !== 'issued') rows.push({text:'[출고 취소된 명세표]',align:'center',kind:'bold'});
  if (o.memo) rows.push({text:'비고: ' + String(o.memo)});
  rows.push({line:true});
  rows.push({text:'위와같이 출고 하였습니다.',align:'center'});
  const bank=o.bank||{};
  if(bank.bank_name&&bank.account_number&&bank.account_holder){
    rows.push({line:true});
    rows.push({text:'입금처:',kind:'bold'});
    rows.push({text:String(bank.bank_name)+' '+String(bank.account_number)});
    rows.push({text:'예금주: '+String(bank.account_holder)});
  }
  return rows;
}

function fontFor(row, fontSize=26) {
  const family = '"Malgun Gothic", "Apple SD Gothic Neo", sans-serif';
  const px = row.kind === 'title' ? Math.round(fontSize*1.45) :
    row.kind === 'subtitle' ? Math.round(fontSize*1.15) :
    row.kind === 'total' ? Math.round(fontSize*1.27) : fontSize;
  const strong = ['title','subtitle','total','bold'].includes(row.kind);
  return (strong?'bold ':'') + px + 'px ' + family;
}

function wrapPixels(ctx, text, allowed) {
  const result = [];
  let line = '';
  for (const char of Array.from(String(text))) {
    if (char === '\n') { result.push(line); line = ''; continue; }
    const next = line + char;
    if (line && ctx.measureText(next).width > allowed) {
      result.push(line);
      line = char;
    } else {
      line = next;
    }
  }
  result.push(line);
  return result;
}

export function drawInvoiceCanvas(invoice, paperMm, doc = document, options={}) {
  const width = Number(options.dotWidth ?? PAPER_WIDTHS[paperMm]);
  if (!WIDTH_CHOICES[paperMm]?.includes(width)) throw new Error('지원하지 않는 인쇄폭입니다.');
  const fontSize = Number(options.fontSize ?? 26);
  if (!FONT_CHOICES.includes(fontSize)) throw new Error('지원하지 않는 글자 크기입니다.');
  const rows = makeReceiptRows(invoice);
  const canvas = doc.createElement('canvas');
  canvas.width = width;
  const ctx = canvas.getContext('2d', {willReadFrequently:true});
  if (!ctx) throw new Error('브라우저에서 인쇄용 이미지를 만들 수 없습니다.');
  const padding = paperMm === 58 ? 12 : 20;
  const maxWidth = width - padding * 2;
  const lines = [];
  for (const row of rows) {
    if (row.line) {
      lines.push({line:true,height:18});
      continue;
    }
    ctx.font = fontFor(row,fontSize);
    for (const text of wrapPixels(ctx, row.text, maxWidth)) {
      const big = ['title','subtitle','total'].includes(row.kind);
      lines.push({...row,text,height:Math.ceil((big ? fontSize*1.45 : fontSize)*1.36)+2});
    }
  }
  const height = 16 + lines.reduce((acc,line) => acc + line.height,0) + 18;
  if (height > 20000) throw new Error('명세표가 너무 길어 한 번에 출력할 수 없습니다.');
  canvas.height = height;
  ctx.fillStyle = '#fff';
  ctx.fillRect(0,0,width,height);
  ctx.fillStyle = '#000';
  ctx.textBaseline = 'top';
  let y = 15;
  for (const line of lines) {
    if (line.line) {
      ctx.fillRect(padding,y + 7,maxWidth,1);
    } else {
      ctx.font = fontFor(line,fontSize);
      ctx.textAlign = line.align || 'left';
      const x = line.align === 'right' ? width - padding :
                line.align === 'center' ? width/2 : padding;
      ctx.fillText(line.text,x,y);
    }
    y += line.height;
  }
  return canvas;
}

/** GS v 0, 0x1D 0x76 0x30; black pixel=1, MSB is leftmost. */
export function rasterBand(image, startRow = 0, rowCount = 48) {
  if (!image || !image.data || !Number.isSafeInteger(image.width) || !Number.isSafeInteger(image.height)) {
    throw new Error('유효하지 않은 이미지입니다.');
  }
  const width = image.width, height = image.height;
  if (width < 1 || width > 1024 || height < 1 || height > 20000 ||
      startRow < 0 || startRow >= height || rowCount < 1 || rowCount > 4096) {
    throw new Error('인쇄 이미지 크기가 유효하지 않습니다.');
  }
  const rows = Math.min(rowCount, height-startRow);
  const bytesPerRow = Math.ceil(width / 8);
  const data = new Uint8Array(8 + rows * bytesPerRow);
  data.set([GS,0x76,0x30,0,bytesPerRow&255,(bytesPerRow>>8)&255,rows&255,(rows>>8)&255]);
  for (let y=0; y<rows; y++) {
    for (let x=0; x<width; x++) {
      const offset=((startRow + y)*width + x)*4;
      const a=image.data[offset+3];
      // Luminance threshold reduces grey antialiasing and keeps small Korean text legible.
      const dark=a>80 && image.data[offset]*0.299 +
        image.data[offset+1]*0.587 + image.data[offset+2]*0.114 < 175;
      if (dark) data[8 + y*bytesPerRow + (x>>3)] |= 0x80 >> (x&7);
    }
  }
  return data;
}

/** One ESC/POS raster-image job, matching the operator's known printtest.mjs:
 * ESC @; GS v 0 [whole image, or 4096-row segments for unusually long receipts]; line feeds; optional GS V 0 cut.
 * Unlike 48-dot bands, ordinary receipts are printed as one image.
 */ 
export function buildRasterJob(image, autoCut=true) {
  if (!image || !Number.isInteger(image.height) || image.height < 1 || image.height > 20000) {
    throw new Error('인쇄 이미지가 올바르지 않습니다.');
  }
  const blocks=[Uint8Array.from([ESC,0x40])];
  for (let y=0; y<image.height; y+=4096) blocks.push(rasterBand(image,y,Math.min(4096,image.height-y)));
  blocks.push(Uint8Array.from(autoCut?[10,10,10,GS,0x56,0x00]:[10,10,10]));
  return blocks;
}

export function testReceiptBytes(settings) {
  const s = checkedSettings(settings);
  const msg = 'BAEKSE ORDER PRINT TEST\nSERIAL PROFILE COM' + s.slot +
    '\nBAUD ' + s.baudRate + ' 8N1\n(Confirm physical port in browser)\n\n\n';
  return new Uint8Array([ESC,0x40,...new TextEncoder().encode(msg)]);
}

export class SerialReceiptPrinter {
  constructor(serial = (typeof navigator !== 'undefined' ? navigator.serial : undefined)) {
    this.serial=serial;
    this.port=null;
    this.busy=false;
    this.settings=null;
  }
  get supported() { return !!this.serial && typeof this.serial.requestPort === 'function'; }
  get connected() { return !!this.port && !!this.port.writable; }
  async connect(settings) {
    if (!this.supported) throw new Error('이 브라우저는 COM 직접 출력을 지원하지 않습니다. Windows Chrome 또는 Edge에서 HTTPS로 접속하세요.');
    if (this.busy) throw new Error('출력이 진행 중입니다.');
    if (this.port) throw new Error('이미 연결된 포트가 있습니다. 먼저 연결을 해제하세요.');
    const s=checkedSettings(settings);
    // MUST invoke immediately from the click handler, before another async operation.
    // Browser chooser selects the real OS serial device; JS cannot force Windows COM4.
    const candidatePromise=this.serial.requestPort();
    const candidate=await candidatePromise;
    await candidate.open({baudRate:s.baudRate,dataBits:8,stopBits:1,parity:'none',flowControl:'none'});
    this.port=candidate;
    this.settings=s;
    return s;
  }
  async reconnectGranted(settings) {
    if (!this.supported) throw new Error('이 브라우저에서는 시리얼 포트를 사용할 수 없습니다.');
    if (this.port) throw new Error('이미 COM 연결 중입니다.');
    const s=checkedSettings(settings);
    const ports=await this.serial.getPorts();
    if (ports.length !== 1) throw new Error('기억된 장치가 한 개가 아닙니다. 장치 선택 버튼으로 실제 COM 포트를 다시 선택하세요.');
    await ports[0].open({baudRate:s.baudRate,dataBits:8,stopBits:1,parity:'none',flowControl:'none'});
    this.port=ports[0];this.settings=s;
    return s;
  }
  async disconnect() {
    if (this.busy) throw new Error('전송 중에는 연결을 해제할 수 없습니다.');
    if (this.port) await this.port.close();
    this.port=null;
    this.settings=null;
  }
  async _send(blocks, onProgress=()=>{}) {
    if (!this.connected || !this.settings) throw new Error('먼저 COM 포트를 연결하세요.');
    if (this.busy) throw new Error('이미 출력 중입니다.');
    this.busy=true;
    const writer=this.port.writable.getWriter();
    try {
      const total=blocks.reduce((n,b)=>n+b.length,0);
      let sent=0;
      for (const bytes of blocks) {
        // Web Serial WritableStream handles backpressure. Do not impose an extra
        // full wire-time delay per 128-byte fragment: that doubled perceived latency.
        // Keep one complete GS v 0 raster command, writing its payload in order.
        for(let i=0; i<bytes.length; i+=2048) {
          const chunk=bytes.subarray(i,i+2048);
          await writer.write(chunk);
          sent+=chunk.length;
          onProgress(sent,total);
        }
      }
    } finally {
      writer.releaseLock();
      this.busy=false;
    }
  }
  async test(onProgress) {
    await this._send([testReceiptBytes(this.settings)],onProgress);
  }
  async printInvoice(invoice,options,onProgress) {
    if (!this.connected) throw new Error('COM 포트가 연결되지 않았습니다.');
    const settings=checkedSettings({...this.settings,...(typeof options==='object'?options:{paperMm:options})});
    const canvas=drawInvoiceCanvas(invoice,settings.paperMm,document,settings);
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    const image=ctx.getImageData(0,0,canvas.width,canvas.height);
    await this._send(buildRasterJob(image,settings.autoCut),onProgress);
  }
  async testWidth(options,onProgress) {
    if (!this.connected) throw new Error('먼저 COM 포트를 연결하세요.');
    const settings=checkedSettings({...this.settings,...options});
    const c=document.createElement('canvas');
    c.width=settings.dotWidth;c.height=145;
    const ctx=c.getContext('2d',{willReadFrequently:true});
    ctx.fillStyle='#fff';ctx.fillRect(0,0,c.width,c.height);
    ctx.fillStyle='#000';
    // Bars should appear on both sides. If the right one clips, select a smaller dot width.
    ctx.fillRect(7,7,5,128);ctx.fillRect(c.width-12,7,5,128);
    ctx.fillRect(7,7,c.width-14,3);ctx.fillRect(7,132,c.width-14,3);
    ctx.textAlign='center';ctx.textBaseline='top';ctx.font='bold 25px "Malgun Gothic",sans-serif';
    ctx.fillText(String(settings.dotWidth)+' DOT WIDTH',c.width/2,37);
    ctx.font='20px "Malgun Gothic",sans-serif';
    ctx.fillText('LEFT  |  RIGHT',c.width/2,80);
    await this._send(buildRasterJob(ctx.getImageData(0,0,c.width,c.height),settings.autoCut),onProgress);
  }
}
