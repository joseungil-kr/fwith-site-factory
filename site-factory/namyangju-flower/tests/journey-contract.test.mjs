import test from 'node:test';
import assert from 'node:assert/strict';
import {nextSteps,relatedReading} from '../src/lib/journey.mjs';
import {hubGuide,hubProducts} from '../src/lib/hubs.mjs';
const gift={pageKey:'gift',category:'gift',pageType:'hospital-visit',primaryKeyword:'꽃선물',relatedKeys:['help']};
const help={pageKey:'help',category:'order',pageType:'order-help',primaryKeyword:'배송 상담',visualIntent:'consultation'};
test('every explicit cross-category reading reference remains reachable',()=>{
  assert.deepEqual(relatedReading(gift,[gift,help]),[help]);
});
test('gift pages cannot inherit a funeral-only price guide',()=>{
  const funeral={pageKey:'funeral-price',category:'order',pageType:'price-guide',primaryKeyword:'근조화환 가격',visualIntent:'funeral_wreath'};
  const broad={pageKey:'flower-price',category:'order',pageType:'price-guide',primaryKeyword:'꽃 가격',visualIntent:'flower_price'};
  assert.deepEqual(nextSteps(gift,[gift,funeral]),[]);
  assert.deepEqual(nextSteps(gift,[gift,funeral,broad]),[broad]);
});
test('hub selected cards follow changed catalog while summaries avoid duplicate prices and preserve Truth hours',()=>{
  const products=[{key:'fixture',family:'funeral',name:'검증 새 상품',price:71234}];
  const guide=hubGuide('funeral',products,{onlineOrderHours:'09:00~18:00'});
  assert.deepEqual(hubProducts('funeral',products),products);
  assert.match(guide.intro,/상품 사진과 기본가격을 아래/);assert.doesNotMatch(guide.intro,/71,234원|59,000/);
  const order=hubGuide('order',products,{onlineOrderHours:'09:00~18:00'});
  assert.match(order.intro,/온라인 09:00~18:00 접수하며/);assert.doesNotMatch(order.intro,/24시간/);
});
