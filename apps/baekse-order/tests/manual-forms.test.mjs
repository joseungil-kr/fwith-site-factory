import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const root=new URL('../public/',import.meta.url);
const invoice=readFileSync(new URL('manual-invoice/index.html',root),'utf8');
const receipt=readFileSync(new URL('simple-receipt/index.html',root),'utf8');
const js=readFileSync(new URL('manual-forms/forms.js',root),'utf8');
const css=readFileSync(new URL('manual-forms/forms.css',root),'utf8');
test('standalone invoice and receipt have correct page orientations and print actions',()=>{
 assert.match(invoice,/<body data-form="invoice">/);
 assert.match(receipt,/<body data-form="receipt">/);
 assert.ok(invoice.includes('@page{size:A4 landscape;margin:0}'));
 assert.ok(receipt.includes('@page{size:A4 portrait;margin:0}'));
 for(const html of [invoice,receipt]){
  assert.ok(html.includes('id="print-form"'));
  assert.ok(html.includes('id="print-root"'));
  assert.ok(html.includes('id="clear-form"'));
 }
 assert.ok(js.includes("window.print()"));
 assert.ok(css.includes('.print-sheet.invoice{width:297mm;height:209mm'));
 assert.ok(css.includes('.print-sheet.receipt{width:210mm;height:296mm'));
});
test('right-hand form mirrors the left-hand form; amounts are calculated client-side',()=>{
 assert.ok(js.includes("const count=receipt?10:15"));
 assert.ok(js.includes('data-copy="'+( 'vendor' || 'supplier')+'"')===false); // no hidden third-party data model
 assert.ok(js.includes("copy('supplier')+copy('recipient')"));
 assert.ok(js.includes("root.addEventListener('input',synchronize)"));
 assert.ok(js.includes("root.addEventListener('change',synchronize)"));
 assert.ok(js.includes("Math.round(amount*.1)"));
 assert.ok(js.includes("toggle.textContent=enabled?'부가세 별도':'부가세 자동입력'"));
 assert.ok(js.includes("setCalculated('invoiceTotal',supply+tax)"));
 assert.ok(js.includes("const grand=supply+tax+previous"));
 assert.ok(js.includes("const balance=Math.max(0,grand-paid)"));
 assert.ok(js.includes("document.getElementById('clear-form')"));
 for(const token of ['supplier','supplierNo','supplierAddress','supplierPhone','buyer','buyerNo','buyerAddress','buyerContact','writtenDate','slipNumber','qty','price','vatMode','previous','paid'])
  assert.ok(js.includes(token),token);
});
test('public forms have no ERP credentials or transaction/PII persistence',()=>{
 for(const fragment of ['fetch(', 'localStorage', 'sessionStorage', 'document.cookie', '/api/', 'indexedDB','navigator.sendBeacon']){
  assert.ok(!js.includes(fragment),'Forms must not use '+fragment);
 }
 assert.ok(!js.includes('innerHTML=el.value'));
 assert.ok(js.includes('target.textContent='));
});

test('manual invoice is the only search-indexable static page; noindex protects admin and receipt',()=>{
 const worker=readFileSync(new URL('../src.js',import.meta.url),'utf8');
 const robots=readFileSync(new URL('robots.txt',root),'utf8');
 const sitemap=readFileSync(new URL('sitemap.xml',root),'utf8');
 assert.ok(invoice.includes('meta name="robots" content="index,follow'));
 assert.ok(receipt.includes('noindex,nofollow,noarchive'));
 assert.ok(invoice.includes('<link rel="canonical" href="https://order.baeksefood.com/manual-invoice/">'));
 for(const item of ['name="description"','property="og:image"','property="og:title"','name="twitter:card"','"@type":"WebApplication"','"@type":"FAQPage"'])
  assert.ok(invoice.includes(item),item);
 assert.ok(worker.includes("!url.searchParams.has('blank')"),'Blank print page must be noindex');
 assert.ok(worker.includes("indexableInvoice||publicOgImage?'index, follow, max-image-preview:large':'noindex, nofollow, noarchive'"));
 assert.ok(robots.includes('Sitemap: https://order.baeksefood.com/sitemap.xml'));
 assert.ok(sitemap.includes('<loc>https://order.baeksefood.com/manual-invoice/</loc>'));
 assert.ok(!sitemap.includes('<loc>https://order.baeksefood.com/request/</loc>'));
 const img=readFileSync(new URL('manual-invoice/og-image.png',root));
 assert.equal(img.subarray(0,8).toString('hex'),'89504e470d0a1a0a');
 assert.equal(img.readUInt32BE(16),1200);
 assert.equal(img.readUInt32BE(20),630);
 assert.ok(img.length>5000);
});
test('free manual invoice landing has meaningful crawlable guide but printing hides guide',()=>{
 for(const item of ['class="seo-guide"','무료 온라인 거래명세표','빈 양식 PDF 다운로드','거래명세서 작성 방법','자주 묻는 질문','세금계산서의 차이'])
  assert.ok(invoice.includes(item),item);
 assert.ok(css.includes('.seo-guide,.guide-inner,body>noscript{display:none!important}'));
 assert.ok(invoice.includes('href="/manual-invoice/?blank=1&amp;print=1"'));
 assert.ok(js.includes("const blankMode=!receipt&&new URLSearchParams(location.search).get('blank')==='1'"));
 assert.ok(js.includes("setTimeout(()=>window.print(),350)"));
 assert.ok(js.includes("if(dateField&&!blankMode)dateField.value=now;"));
 assert.ok(js.includes('vat-toggle'));
 assert.ok(!js.includes('<select aria-label="부가세 계산"'));
 assert.ok(css.includes('.invoice .amount-line>span:first-child{font-size:11pt'));
});
