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
 assert.ok(js.includes("const count=verticalInvoice?10:15;"));
 assert.ok(js.includes('data-copy="'+( 'vendor' || 'supplier')+'"')===false); // no hidden third-party data model
 assert.ok(js.includes("copy('supplier')+copy('recipient')"));
 assert.ok(js.includes("root.addEventListener('input',event=>{"));
 assert.ok(js.includes("root.addEventListener('change',synchronize)"));
 assert.ok(js.includes("Math.round(amount*.1)"));
 assert.ok(js.includes("toggle.textContent=enabled?'부가세 별도':'부가세 자동입력'"));
 assert.ok(js.includes("setCalculated('invoiceTotal',supply+tax)"));
 assert.ok(js.includes("const grand=supply+tax+previous"));
 assert.ok(js.includes("const balance=Math.max(0,grand-paid)"));
 assert.ok(js.includes("document.getElementById('clear-form')"));
 for(const token of ['supplier','supplierNo','supplierAddress','supplierPhone','buyer','buyerAddress','buyerContact','writtenDate','slipNumber','qty','price','vatMode','previous','paid'])
  assert.ok(js.includes(token),token);
});
test('public forms have no ERP credentials or transaction/PII persistence',()=>{
 for(const fragment of ['fetch(', 'localStorage', 'sessionStorage', 'document.cookie', '/api/', 'indexedDB','navigator.sendBeacon']){
  assert.ok(!js.includes(fragment),'Forms must not use '+fragment);
 }
 assert.ok(!js.includes('innerHTML=el.value'));
 assert.ok(js.includes('target.textContent='));
});

test('both public forms are separately indexable; admin and blank variants remain noindex',()=>{
 const worker=readFileSync(new URL('../src.js',import.meta.url),'utf8');
 const robots=readFileSync(new URL('robots.txt',root),'utf8');
 const sitemap=readFileSync(new URL('sitemap.xml',root),'utf8');
 assert.ok(invoice.includes('meta name="robots" content="index,follow'));
 assert.ok(receipt.includes('meta name="robots" content="index,follow'));
 assert.ok(invoice.includes('<link rel="canonical" href="https://order.baeksefood.com/manual-invoice/">'));
 for(const item of ['name="description"','property="og:image"','property="og:title"','name="twitter:card"','"@type":"WebApplication"','"@type":"FAQPage"'])
  assert.ok(invoice.includes(item),item);
 assert.ok(worker.includes("!url.searchParams.has('blank')"),'Blank print page must be noindex');
 assert.ok(worker.includes("indexableInvoice||indexableReceipt||publicOgImage?'index, follow, max-image-preview:large':'noindex, nofollow, noarchive'"));
 assert.ok(robots.includes('Sitemap: https://order.baeksefood.com/sitemap.xml'));
 assert.ok(sitemap.includes('<loc>https://order.baeksefood.com/manual-invoice/</loc>'));
 assert.ok(sitemap.includes('<loc>https://order.baeksefood.com/simple-receipt/</loc>'));
 assert.ok(robots.includes('Allow: /simple-receipt/'));
 assert.ok(!robots.includes('Disallow: /simple-receipt/'));
 assert.ok(!sitemap.includes('<loc>https://order.baeksefood.com/request/</loc>'));
 const img=readFileSync(new URL('manual-invoice/og-image.png',root));
 assert.equal(img.subarray(0,8).toString('hex'),'89504e470d0a1a0a');
 assert.equal(img.readUInt32BE(16),1200);
 assert.equal(img.readUInt32BE(20),630);
 assert.ok(img.length>5000);
 const receiptOg=readFileSync(new URL('simple-receipt/og-image.png',root));
 assert.equal(receiptOg.subarray(0,8).toString('hex'),'89504e470d0a1a0a');
 assert.equal(receiptOg.readUInt32BE(16),1200);
 assert.equal(receiptOg.readUInt32BE(20),630);
 assert.ok(receiptOg.length>5000);
 assert.ok(receipt.includes('<link rel="canonical" href="https://order.baeksefood.com/simple-receipt/">'));
 for(const marker of ['name="description"','property="og:image"','property="og:title"','name="twitter:card"','"@type":"WebApplication"','"@type":"FAQPage"'])
   assert.ok(receipt.includes(marker),'Missing receipt SEO: '+marker);
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

test('receipt and invoice retain 15 rows and use the exact recipient business and contact labels',()=>{
 assert.ok(js.includes("const count=verticalInvoice?10:15;"));
 assert.ok(js.includes("(receipt?'공급자(상호)':'공급자')"));
 assert.ok(js.includes('<th>공급받는자</th>'));
 assert.ok(js.includes('<th>담당자</th><td><span class="buyer-contact-entry">'));
 assert.ok(js.includes('buyer-honorific'));
 assert.ok(js.includes('귀하</span>'));
 assert.ok(js.includes("field('buyerContact','공급받는자 담당자',editable)"));
 assert.ok(js.includes("field('buyerNo','공급받는자 등록번호',editable)"),'Recipient registration is available only in the vertical format');
 assert.ok(css.includes('.receipt .item-table tbody tr{height:8.75mm}'));
 assert.ok(css.includes('.receipt .parties .p-label{width:21%}'));
});
test('supplier and buyer information blocks are separated within each slip, with neutral white paper styling',()=>{
 for(const marker of [
   'party-supplier party-supplier-start',
   'party-buyer party-buyer-start',
   'class="party-supplier"',
   'class="party-buyer"'
 ])assert.ok(js.includes(marker),'Missing party information block marker: '+marker);
 for(const marker of [
   '.print-sheet .slip[data-copy="supplier"],',
   '.print-sheet .slip[data-copy="recipient"]{border:.35mm solid #303a3b}',
   '.parties tr.party-supplier-start > *,',
   '.parties tr.party-buyer-start > *{border-top:.18mm solid #526062}',
   '.print-sheet .slip .form-head{',
   'background:#fff!important;',
   '.print-sheet .slip .parties th{background:#fff}'
 ])assert.ok(css.includes(marker),'Missing white print or party divider: '+marker);
 assert.ok(!css.includes('background:#dff3e9'));
 assert.ok(!css.includes('background:#e3eef8'));
 assert.ok(!css.includes('border:.65mm solid #0a715e'));
 assert.ok(!css.includes('border:.65mm solid #305e82'));
 assert.ok(!css.includes('border-top:.75mm double'));
 assert.ok(!css.includes('border-top:.4mm solid #606a6c'));
 for(const marker of ['.buyer-contact-entry{display:flex','buyer-honorific{flex:0 0 auto',
   '.cut-marker .cut-label{position:absolute','transform:rotate(90deg)'])
  assert.ok(css.includes(marker),'Missing contact suffix or rotated cut caption: '+marker);
 assert.ok(js.includes('<span class="cut-label">✂ 절취선</span>'));
});
test('receipt SEO has unique crawlable guide with real instructions and print exclusion',()=>{
 assert.ok(receipt.includes('<title>무료 간이영수증 양식 | 온라인 영수증 작성·PDF 저장</title>'));
 for(const marker of [
   '<h1>무료 온라인 간이영수증 양식',
   '<h2 id="guide-title">',
   '<h3>간이영수증 온라인 작성 방법',
   '<h3>자주 묻는 질문',
   'A4 세로',
   '15개 품목',
   '세금계산서·현금영수증',
   'class="seo-guide"',
   '간이영수증 PDF'
 ])assert.ok(receipt.includes(marker),'Missing receipt guide: '+marker);
 assert.ok(css.includes(' .seo-guide{display:none!important}'),'SEO guidance must not print');
 const jsonLds=[...receipt.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)];
 assert.equal(jsonLds.length,2,'WebApplication + FAQPage required');
 for(const [,source] of jsonLds)assert.doesNotThrow(()=>JSON.parse(source));
 assert.deepEqual(jsonLds.map(([,source])=>JSON.parse(source)['@type']),['WebApplication','FAQPage']);
});


test('top-bottom A4 uses 10 rows and preserves shared financial input fields',()=>{
 const vertical=readFileSync(new URL('manual-invoice-vertical/index.html',root),'utf8');
 assert.ok(vertical.includes('data-form="invoice-vertical"'));
 assert.ok(vertical.includes('@page{size:A4 portrait;margin:0}'));
 assert.ok(vertical.includes('href="/manual-forms/forms.css"'));
 assert.ok(vertical.includes('src="/manual-forms/forms.js"'));
 assert.ok(vertical.includes('noindex,follow,noarchive'));
 assert.ok(vertical.includes('id="print-root"'));
 assert.ok(vertical.includes('id="print-form"'));
 assert.ok(vertical.includes('id="blank-pdf"'));
 assert.ok(vertical.includes('id="clear-form"'));
 assert.ok(invoice.includes('href="/manual-invoice-vertical/"'),'Original free invoice must link the variant');
 assert.ok(js.includes("const verticalInvoice=document.body.dataset.form==='invoice-vertical'"));
 assert.ok(js.includes("verticalInvoice?' invoice-vertical':''"));
 assert.ok(js.includes("copy('supplier')+copy('recipient')"));
 assert.ok(js.includes('const count=verticalInvoice?10:15;'));
 for(const name of ['writtenDate','slipNumber','supplier','supplierNo','supplierAddress','supplierPhone',
   'buyer','buyerAddress','buyerContact','memo','previous','paid','vatMode','item-'])
  assert.ok(js.includes(name),'Existing field must remain in shared form engine: '+name);
});

test('portrait top-bottom A4 has a horizontal cut guide and compact 10-row grid',()=>{
 for(const marker of [
  '.print-sheet.invoice.invoice-vertical{width:210mm;height:296mm;padding:4mm}',
  '.print-sheet.invoice-vertical .slips{',
  'grid-template-columns:minmax(0,1fr);',
  'grid-template-rows:repeat(2,minmax(0,1fr));',
  '.print-sheet.invoice-vertical .slip .item-table{height:72mm',
  '.print-sheet.invoice-vertical .slip .item-table tbody tr{height:6.7mm}',
  '.print-sheet.invoice-vertical .cut-marker{',
  'border-top:.3mm dashed #626c6c;',
  '.print-sheet.invoice-vertical .cut-marker .cut-label{',
  'transform:none;',
  '.print-sheet.invoice.invoice-vertical{',
  'height:294mm!important;',
 ])
  assert.ok(css.includes(marker),'Missing portrait print constraint '+marker);
 assert.ok(css.includes('.print-sheet.invoice{width:297mm;height:209mm'));
 assert.ok(css.includes('.print-sheet.receipt{width:210mm;height:296mm'));
});


test('portrait invoice colors every supplier/red and recipient/blue table/text separately',()=>{
 const red='.print-sheet.invoice-vertical .slip[data-copy="supplier"]{--copy-ink:#9a2630}';
 const blue='.print-sheet.invoice-vertical .slip[data-copy="recipient"]{--copy-ink:#244a89}';
 assert.ok(css.includes(red),'Supplier top copy must be red');
 assert.ok(css.includes(blue),'Recipient bottom copy must be blue');
 for(const marker of [
  '.print-sheet.invoice-vertical .slip[data-copy]{',
  'border-color:var(--copy-ink);',
  '.print-sheet.invoice-vertical .slip[data-copy] th,',
  '.print-sheet.invoice-vertical .slip[data-copy] td,',
  '.print-sheet.invoice-vertical .slip[data-copy] input,',
  '.print-sheet.invoice-vertical .slip[data-copy] .mirror,',
  '.print-sheet.invoice-vertical .slip[data-copy] .calculated{',
  'color:var(--copy-ink);',
  'color:var(--copy-ink)!important;',
  'border-color:var(--copy-ink)!important;',
  '-webkit-print-color-adjust:exact;'
 ])assert.ok(css.includes(marker),'Missing exact-color role rule '+marker);
 assert.ok(!css.includes('.print-sheet.invoice .slip[data-copy="supplier"]{--copy-ink:'),
   'Color must be scoped to vertical variant, not original landscape invoice');
 assert.ok(css.includes('background:#fff!important;'),'Paper must remain white');
});


test('vertical invoice has exactly four rows each for buyer-left and supplier-right, vertical names',()=>{
 assert.ok(js.includes('if(verticalInvoice){'),'Only vertical invoice may use paired 4-field layout');
 assert.ok(js.includes('<table class="vertical-party-table"'));
 assert.ok(js.includes('<th class="vertical-side-label" rowspan="4" scope="rowgroup">공급받는자</th>'));
 assert.ok(js.includes('<th class="vertical-side-label" rowspan="4" scope="rowgroup">공급자</th>'));
 for(const name of ['상호','등록번호','소재지','연락처']){
  const re=new RegExp('scope="row">'+name+'</th>','g');
  assert.equal([...js.matchAll(re)].length,2,name+' must appear for buyer and supplier');
 }
 for(const fragment of [
  "field('buyer','공급받는자 상호',editable)",
  "field('buyerNo','공급받는자 등록번호',editable)",
  "field('buyerAddress','공급받는자 소재지',editable)",
  "field('buyerPhone','공급받는자 연락처',editable)",
  "field('supplier','공급자 상호',editable)",
  "field('supplierNo','공급자 등록번호',editable)",
  "field('supplierAddress','공급자 소재지',editable)",
  "field('supplierPhone','공급자 연락처',editable)",
  "field('writtenDate','작성일',editable)"
 ])assert.ok(js.includes(fragment),fragment);
 for(const fragment of [
  'writing-mode:vertical-rl;',
  'text-orientation:upright;',
  '.vertical-party-table tr{height:5.125mm}',
  '.vertical-party-table col.vertical-party-side{width:5.5%}',
  '.vertical-party-table col.vertical-party-field{width:11%}',
  '.vertical-party-table col.vertical-party-data{width:33.5%}'
 ])assert.ok(css.includes(fragment),fragment);
 const vertical=readFileSync(new URL('manual-invoice-vertical/index.html',root),'utf8');
 assert.ok(vertical.includes('10품목'));
 assert.ok(vertical.includes('좌측')||vertical.includes('왼쪽 공급받는자'));
 assert.ok(!vertical.includes('15품목'),'Outdated vertical page description');
});


test('both invoices display Korean full-won totals, while receipt remains numeric',()=>{
 assert.ok(js.startsWith("import {koreanWonText} from './korean-money.mjs';"));
 assert.ok(js.includes("if(!receipt){"));
 assert.ok(js.includes('invoice-korean-line'));
 assert.ok(js.includes('class="amount-korean" data-amount-korean'));
 assert.ok(js.includes("koreanWonText(supply+tax)"),'Words are current supply+VAT, without old balance');
 assert.ok(js.includes("el.textContent=blankMode?'':koreanWonText(supply+tax)"),'Blank PDF must not print a total');
 assert.ok(css.includes('.print-sheet.invoice:not(.invoice-vertical) .slip .invoice-korean-line strong.amount-korean{'));
 assert.ok(css.includes('.print-sheet.invoice-vertical .slip .vertical-amount-line strong.amount-korean{'));
 const original=readFileSync(new URL('manual-invoice/index.html',root),'utf8');
 const vertical=readFileSync(new URL('manual-invoice-vertical/index.html',root),'utf8');
 assert.ok(original.includes('data-form="invoice"')&&vertical.includes('data-form="invoice-vertical"'));
 assert.ok(!receipt.includes('data-amount-korean'));
});

test('three form variants group unit prices and show no 0 in unfilled rows',()=>{
 for(const fragment of [
  'function formatUnitPriceInput(el){',
  "const digits=raw.replace(/\\D/g,'');",
  "const grouped=digits.replace(/\\B(?=(\\d{3})+(?!\\d))/g,',');",
  'el.setSelectionRange(at,at);',
  "const complete=qtyText.trim()!==''&&priceText.trim()!=='';",
  "setCalculated('item-'+i+'-amount',amount,!complete);",
  "setCalculated('item-'+i+'-tax',lineTax,!complete);",
  "root.addEventListener('input',event=>{",
  "el.textContent=blankMode||empty?'':won(value)",
  'data-field$="-price"',
  'const count=verticalInvoice?10:15;'
 ])assert.ok(js.includes(fragment),'Missing shared format/blank behavior: '+fragment);
 assert.ok(js.includes('const output=(key)=>'));
 assert.ok(!js.includes('">0</span>'),'Calculated item cells must not contain default zero');
});
