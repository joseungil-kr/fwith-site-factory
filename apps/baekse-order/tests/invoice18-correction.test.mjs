import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const src=readFileSync(new URL('../src.js',import.meta.url),'utf8');
test('issued invoice 18 correction is single-use, strict, and ledger neutral',()=>{
 assert.ok(src.includes("const invoice18Marker='ansan-central-issued-invoice18-previous-312000-to-zero-20261111'"));
 for(const expected of [
  "order.order_date==='2026-11-11'",
  "order.order_type==='sale'",
  "order.status==='issued'",
  'order.supply===258000',
  'order.tax===0',
  'order.total===258000',
  'order.previous_balance===312000',
  "client?.business==='안산 중앙점'",
  "['잉어반죽',12,11000,132000]",
  "['팥앙금',8,9000,72000]",
  "['슈크림',6,9000,54000]",
  "if(matches){",
  "this.ctx.storage.transactionSync(()=>{",
  "this.audit('invoice_previous_balance_corrected_once',receipt);"
 ])assert.ok(src.includes(expected),'Missing fail-closed invoice guard: '+expected);
 const onlyUpdate=src.match(/UPDATE orders SET previous_balance\s*=\s*0[^"']*/g)||[];
 assert.equal(onlyUpdate.length,1,'Must touch previous balance only once, for the exact order');
 assert.ok(onlyUpdate[0].includes('WHERE id=18 AND previous_balance=312000 AND total=258000'));
 assert.ok(!onlyUpdate[0].includes('receivable_'),'Must not modify ledger during this correction');
 assert.ok(src.includes('INSERT INTO schema_migrations(name,applied_at,details)'));
 assert.ok(src.includes('if(!this.getOne('),'One-time marker must prevent reruns');
});
