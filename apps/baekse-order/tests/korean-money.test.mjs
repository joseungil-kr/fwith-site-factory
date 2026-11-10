import test from 'node:test';
import assert from 'node:assert/strict';
import {koreanWonText} from '../public/manual-forms/korean-money.mjs';

test('Korean won spelling matches the requested 1,594,500-won example',()=>{
 assert.equal(koreanWonText(1594500),'일백오십구만사천오백원 정 (₩1,594,500)');
});

test('Korean won spelling handles zero, small units, man, eok and jo without losing zeros',()=>{
 const values=[
  [0,'영원 정 (₩0)'],
  [1,'일원 정 (₩1)'],
  [10,'일십원 정 (₩10)'],
  [100,'일백원 정 (₩100)'],
  [1000,'일천원 정 (₩1,000)'],
  [10000,'일만원 정 (₩10,000)'],
  [100500,'일십만오백원 정 (₩100,500)'],
  [1000001,'일백만일원 정 (₩1,000,001)'],
  [100000000,'일억원 정 (₩100,000,000)'],
  [1000000000000,'일조원 정 (₩1,000,000,000,000)']
 ];
 for(const [value,expected] of values)assert.equal(koreanWonText(value),expected,'Amount '+value);
});

test('Unsafe/negative/fractional amounts must never be represented as valid accounting words',()=>{
 for(const amount of [-1,1.5,Number.POSITIVE_INFINITY,Number.NaN,Number.MAX_SAFE_INTEGER+2]){
  assert.equal(koreanWonText(amount),'금액 확인 필요','Invalid amount '+amount);
 }
});
