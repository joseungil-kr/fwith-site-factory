import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts,productFamilies} from '../src/lib/catalog.mjs';
const read=n=>JSON.parse(fs.readFileSync(new URL('../src/data/'+n+'.json',import.meta.url),'utf8'));
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const old={"dongducheon-flower-direct-region-songnae-dong": "9fd1b4713db47ef0bebc974722ce9ed2c77f7e0c9a76fa2f5c1b52a50d694329", "dongducheon-flower-direct-region-jihaeng-dong": "e44aeb5f0d7cb28b13cb7582db16660778fda18a50d60ccb62e2edbfdbaf16d0", "dongducheon-flower-direct-region-saengyeon-dong": "138dafb818ed449d22715c3c33bfe8578e38e5c800fc114d3b0e5ad10234855e", "dongducheon-flower-direct-region-gwangam-dong": "c29a22b89a922c5fa880ef97f0e069ecc6072644790a69aea8b8e3a542303f20", "dongducheon-flower-direct-region-bosan-dong": "86c0cd28ad396555b0bedba102129aacbcefa03f615371fadd4c5b65a08a833e", "dongducheon-flower-direct-region-dongducheon-dong": "565fd9d6c1780b4e8aa0929b3bd6e623ba4371f692d9654f214b1eb44a252a18", "dongducheon-flower-direct-region-anheung-dong": "a6fc2ceb1b01fb9f3b63c33fd6908f12bdcc2b5130df91d8c51c67e6f1be08cc", "dongducheon-flower-direct-region-sangbongam-dong": "de24e636aaea4672af3bb2ab89547119e026e2a16444233d8e51701c5aecc36a", "dongducheon-flower-direct-region-habongam-dong": "b897cccf9f9d58c5631a0f2c82fc33128b69355b1dd3f825bb536a49cc531c9f", "dongducheon-flower-direct-region-tapdong-dong": "75b5a014811935ce1d38aca68476dcc40f240a86ea2d517de449e333b8522b52", "dongducheon-flower-direct-region-sangpae-dong": "bedfa4ec84afed8134033ffdde709eeaedd3c2a7f2e34b9eaa020d26533cff14"};
test('eleven original entire article objects and order are preserved',()=>{
 const p=read('pages');assert.deepEqual(p.slice(0,11).map(x=>x.pageKey),Object.keys(old));for(const a of p.slice(0,11))assert.equal(sha(canonical(a)),old[a.pageKey]);
});
test('new named venue N1 preserves original regional denominator',()=>{
 const p=read('pages'),m=read('publish-manifest');assert.equal(p.length,12);assert.equal(p.filter(x=>x.pageType==='regional-service').length,11);assert.equal(m.directRelease.plannedOriginalCount,12);assert.equal(m.directRelease.reviewedArticleCount,11);assert.deepEqual(m.directRelease.deferredRoutes,['/regions/geolsan-dong/']);assert.equal(m.additiveBatches[0].plannedOriginalCount,1);assert.equal(m.additiveBatches[0].previousPublishedCount,11);
 const a=p.at(-1);assert.equal(a.url,'/event/dongducheon-civic-hall-event-wreath/');assert.equal(a.pageType,'event-venue');assert.equal(a.productCardLimit,4);assert.equal(a.visualIntent,'event_wreath');assert.deepEqual(productFamilies(a),['congrats']);assert.deepEqual(a.productCardKeys,['congrats-basic','congrats-premium','congrats-large','congrats-xl']);assert.deepEqual(selectProducts(a,read('products'),4).map(x=>x.key),a.productCardKeys);assert.ok(a.relatedKeys.every(k=>p.some(z=>z.pageKey===k)));assert.equal(a.title,a.h1);
});
test('event hub is discoverable but excluded from index at one child',()=>{
 const h=read('architecture').hubs.find(x=>x.category==='event');assert.equal(h.children,1);assert.equal(h.indexable,false);assert.equal(1+read('pages').length+read('architecture').hubs.filter(x=>x.indexable).length,14);
});
