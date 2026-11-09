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
  assert.ok(html.includes('noindex,nofollow,noarchive'));
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
