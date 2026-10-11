import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const read=n=>JSON.parse(fs.readFileSync(new URL('../src/data/'+n+'.json',import.meta.url),'utf8'));
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const originals={"anyang-flower-direct-region-anyang-dong": "029c7386f42233f57ea742221f05e136b3441a4fce86690a12e65c7d40d539cc", "anyang-flower-direct-region-seoksu-dong": "a01c9b42db3e9b916ac6fd45c6324d80c913c3b9c8488bb70d794af2f490d06a", "anyang-flower-direct-region-bakdal-dong": "918542c192980c7180a14900806a04637a771c33ae85346497a04a03c6481508", "anyang-flower-direct-region-bisan-dong": "7e69e83997e112c2b7603462ccb566505faff298df53925e38c6db4a49aa7b03", "anyang-flower-direct-region-gwanyang-dong": "80a938c0589634bd705da34acba39eb93f2d28d60390f8fb5fa8543ce9b9e67d", "anyang-flower-direct-region-pyeongchon-dong": "861a48ad8740227aacb8cc6be21fdbe36a21f106f0733d5ba5ddf0f4ac362d1f", "anyang-flower-direct-region-hogye-dong": "5f5573b179ad18f5758606b4fc60e9e937f623a3bcbee06b6b0db3a6e64201fb", "anyang-flower-direct-funeral-anyang-funeral-hall-wreath": "81b628d6cc5d5cb61dc41624315980a25d2ca7ad55c2b430cba50707f52cc344", "anyang-flower-direct-funeral-sam-hospital-funeral-wreath": "80c78fe298dc94dc6b6d1227bdf125b4150a27a37491080b28ed6513cb5658d7", "anyang-flower-direct-funeral-hallym-hospital-funeral-wreath": "a6b334424acb4169f7e6993d3f3548cddea571528829d6721f34105d40af3876", "anyang-flower-direct-event-patiobella-wedding-wreath": "fe91cb67c53aab091774ea8abd833663a220a4dc40a76715df3180e18b9bc2de", "anyang-flower-direct-event-partyum-anyang-wedding-wreath": "75b89befff87ffc193e2f9b04072e849476224b457073ef4e72dae46e82b8665"};
test('all twelve original article objects retain their exact semantic digest and order',()=>{
 const p=read('pages');assert.deepEqual(p.slice(0,12).map(x=>x.pageKey),Object.keys(originals));
 for(const a of p.slice(0,12))assert.equal(sha(canonical(a)),originals[a.pageKey]);
});
test('the 20261011 additive scope has exactly two unique pages and separately fixed denominator',()=>{
 const p=read('pages'),m=read('publish-manifest'),a=read('architecture');
 const additions=p.slice(12);assert.equal(p.length,14);assert.equal(new Set(p.map(x=>x.url)).size,14);
 assert.deepEqual(additions.map(x=>x.url),['/business/pyeongchon-smart-square-opening-wreath/','/event/anyang-art-center-performance-wreath/']);
 assert.equal(m.directRelease.plannedOriginalCount,5);assert.equal(m.directRelease.appendedCount,5);
 const batch=m.additiveBatches.find(x=>x.scopeKey==='anyang-additions-20261011');assert.equal(batch.plannedOriginalCount,2);assert.equal(batch.previousPublishedCount,12);
 for(const n of additions){assert.equal(n.scopeKey,batch.scopeKey);assert.equal(n.h1,n.title);assert.equal(n.productCardKeys.length,4);assert.ok(a.hubs.some(h=>h.category===n.category&&h.children>0));assert.ok(n.relatedKeys.every(k=>p.some(z=>z.pageKey===k)));}
});

test('event hub only offers the active verified wreath family',async()=>{
 const {hubGuides}=await import('../src/lib/hubs.mjs');
 assert.deepEqual(hubGuides.event.families,['congrats']);
 assert.equal(hubGuides.event.cta,'축하화환 상품 확인');
 assert.doesNotMatch(JSON.stringify(hubGuides.event),/꽃다발|꽃바구니/);
});
