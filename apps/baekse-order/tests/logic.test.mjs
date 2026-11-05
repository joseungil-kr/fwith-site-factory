import test from 'node:test';import assert from 'node:assert/strict';
import {DEFAULT_PRODUCTS,calcTotals,calcInternalCost,normalizeOrderType,calculatePayable,dateCheck,onlyInt,safeText,stockRemaining,sessionDurationSeconds,SESSION_SHORT_SECONDS,SESSION_REMEMBER_SECONDS} from '../logic.js';
test('초기 제품 6개와 단가',()=>{assert.equal(DEFAULT_PRODUCTS.length,6);assert.deepEqual(DEFAULT_PRODUCTS[0],['잉어반죽',6850,11000])});
test('부가세 별도 10% 계산',()=>{assert.deepEqual(calcTotals([{qty:3,unit_price:11000},{qty:2,unit_price:9000},{qty:1,unit_price:9000}],'tax'),{supply:60000,tax:6000,total:66000});assert.equal(calcTotals([{qty:2,unit_price:9000}],'none').total,18000)});
test('직접입력 기타 품목 금액',()=>{assert.equal(calcTotals([{qty:2,unit_price:3500}],'tax').total,7700)});
test('수량 금액 날짜 검증',()=>{assert.throws(()=>onlyInt(-1));assert.throws(()=>onlyInt(1.5));assert.throws(()=>calcTotals([{qty:0,unit_price:10}],'tax'));assert.equal(dateCheck('2026-11-03'),'2026-11-03');assert.throws(()=>dateCheck('2026-02-30'));assert.equal(safeText(' 안산 중앙점 ','상호',true),'안산 중앙점')});
test('입고 출고 취소 후 재고 일치',()=>assert.equal(stockRemaining(0,[{delta:10},{delta:-3},{delta:3}]),10));

test('로그인 유지 30일은 명시적 선택만 허용',()=>{
  assert.equal(SESSION_SHORT_SECONDS,28800);
  assert.equal(SESSION_REMEMBER_SECONDS,2592000);
  assert.equal(sessionDurationSeconds(undefined),28800);
  assert.equal(sessionDurationSeconds(false),28800);
  assert.equal(sessionDurationSeconds('true'),28800);
  assert.equal(sessionDurationSeconds(true),2592000);
});

test('전 잔고는 청구 합계만 바꾸며 기존 매출금액은 보존',()=>{const sale=calcTotals([{qty:1,unit_price:93000}],'none');assert.equal(sale.total,93000);assert.equal(calculatePayable(sale.total,100000),193000);assert.equal(calculatePayable(sale.total,0),93000);assert.throws(()=>calculatePayable(sale.total,-1));});

test('internal order type is strict',()=>{
  assert.equal(normalizeOrderType(),'sale');
  assert.equal(normalizeOrderType('sale'),'sale');
  assert.equal(normalizeOrderType('internal'),'internal');
  assert.throws(()=>normalizeOrderType('none'),/출고 구분/);
});
test('internal cost uses procurement cost not selling price',()=>{
  assert.equal(calcInternalCost([{qty:7,cost:6850,unit_price:11000},{qty:3,cost:5150,unit_price:9000}]),63400);
  assert.throws(()=>calcInternalCost([{qty:1,cost:-1}]),/원가/);
  assert.throws(()=>calcInternalCost([{qty:999999,cost:100000000}]),/한도/);
});
