/**
 * Local-only Web Serial thermal receipt printing.
 * No server or external print relay; the browser must explicitly grant port access.
 * Browser APIs cannot enumerate Windows COM numbers: COM1..COM6 are USER-ASSIGNED labels.
 * ESC/POS raster uses the documented GS v 0 command so Korean glyphs are drawn as pixels.
 */
export const COM_SLOTS = Object.freeze([1, 2, 3, 4, 5, 6]);
export const BAUD_RATES = Object.freeze([4800, 9600, 19200, 38400, 115200]);
export const PAPER_WIDTHS = Object.freeze({58: 384, 80: 576});
const ESC = 0x1b, GS = 0x1d;
const formatWon = v => new Intl.NumberFormat('ko-KR').format(Number(v) || 0) + '원';
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

export function checkedSettings(raw) {
  const slot = Number(raw.slot), baudRate = Number(raw.baudRate), paperMm = Number(raw.paperMm);
  if (!COM_SLOTS.includes(slot)) throw new Error('COM1~COM6 중에서 선택하세요.');
  if (!BAUD_RATES.includes(baudRate)) throw new Error('지원하는 통신 속도를 선택하세요.');
  if (!Object.prototype.hasOwnProperty.call(PAPER_WIDTHS, paperMm)) {
    throw new Error('용지 폭을 58mm 또는 80mm로 선택하세요.');
  }
  return {slot, baudRate, paperMm};
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
    {text: '백세푸드',align:'center',kind:'title'},
    {text: '거 래 명 세 표',align:'center',kind:'subtitle'},
    {text: '전표: ' + code},
    {text: '일자: ' + String(o.order_date || '')},
    {text: '거래처: ' + String(c.business || '')},
    {text: '담당자: ' + String(c.person || '') + '  ' + String(c.phone || '')},
  ];
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
  rows.push({text:'합계: ' + formatWon(o.total),align:'right',kind:'total'});
  if (o.status !== 'issued') rows.push({text:'[출고 취소된 명세표]',align:'center',kind:'bold'});
  if (o.memo) rows.push({text:'비고: ' + String(o.memo)});
  rows.push({line:true});
  rows.push({text:'위와 같이 출고하였습니다.',align:'center'});
  return rows;
}

function fontFor(row) {
  const family = '"Malgun Gothic", "Apple SD Gothic Neo", sans-serif';
  if (row.kind === 'title') return 'bold 28px ' + family;
  if (row.kind === 'subtitle') return 'bold 21px ' + family;
  if (row.kind === 'total') return 'bold 21px ' + family;
  return (row.kind === 'bold' ? 'bold ' : '') + '17px ' + family;
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

export function drawInvoiceCanvas(invoice, paperMm, doc = document) {
  const width = PAPER_WIDTHS[paperMm];
  if (!width) throw new Error('지원하지 않는 용지 폭입니다.');
  const rows = makeReceiptRows(invoice);
  const canvas = doc.createElement('canvas');
  canvas.width = width;
  const ctx = canvas.getContext('2d', {willReadFrequently:true});
  if (!ctx) throw new Error('브라우저에서 인쇄용 이미지를 만들 수 없습니다.');
  const padding = paperMm === 58 ? 12 : 18;
  const maxWidth = width - padding * 2;
  const lines = [];
  for (const row of rows) {
    if (row.line) {
      lines.push({line:true,height:18});
      continue;
    }
    ctx.font = fontFor(row);
    for (const text of wrapPixels(ctx, row.text, maxWidth)) {
      const big = ['title','subtitle','total'].includes(row.kind);
      lines.push({...row,text,height:big ? 36 : 27});
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
      ctx.font = fontFor(line);
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
      startRow < 0 || startRow >= height || rowCount < 1 || rowCount > 256) {
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
        for(let i=0;i<bytes.length;i+=128){
          const chunk=bytes.subarray(i,i+128);
          await writer.write(chunk);
          sent+=chunk.length;
          onProgress(sent,total);
          // At 9600bps a byte takes roughly ten serial bits. Allow buffer to drain.
          await delay(Math.ceil(10000 * chunk.length / this.settings.baudRate));
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
  async printInvoice(invoice,paperMm,onProgress) {
    if (!this.connected) throw new Error('COM 포트가 연결되지 않았습니다.');
    const width=Number(paperMm);
    if (![58,80].includes(width)) throw new Error('58mm 또는 80mm를 선택하세요.');
    const canvas=drawInvoiceCanvas(invoice,width);
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    const image=ctx.getImageData(0,0,canvas.width,canvas.height);
    const blocks=[Uint8Array.from([ESC,0x40])];
    for (let y=0;y<image.height;y+=48) blocks.push(rasterBand(image,y,48));
    blocks.push(Uint8Array.from([10,10,10,10]));
    await this._send(blocks,onProgress);
  }
}
