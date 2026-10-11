import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';
const read=n=>JSON.parse(fs.readFileSync(new URL('../src/data/'+n+'.json',import.meta.url),'utf8'));
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const old={"uijeongbu-flower-direct-region-uijeongbu-dong": "519096eb1f698babbfe5a1537a1968a78722554ebd923f17c4630964f3346167", "uijeongbu-flower-direct-region-howon-dong": "2635d17b894c334124f9475dc45c507981563ec3d768bb991171bb031c896b51", "uijeongbu-flower-direct-region-jangam-dong": "c6910e166ac2339b50575d56551f726eef933a9bf65d1c1e69e7961786da47b7", "uijeongbu-flower-direct-region-singok-dong": "1d45d7c2f07e888f45c617766197b0d810616680bbd602289de5cc67a5404ad2", "uijeongbu-flower-direct-region-yonghyeon-dong": "61732005e335678ba8fd11d954b35c91f4303a9b170b090f80d0a2c9eb66f8df", "uijeongbu-flower-direct-region-millak-dong": "22739d55062ac2178c3230bbf60bcc02f9b85cec24e658774dc23fe626713067", "uijeongbu-flower-direct-region-nakyang-dong": "aba488a2a34b98f20e64c559cf3dc64f2359df6d36b86cf992d7a27d9fef2b83", "uijeongbu-flower-direct-region-geumo-dong": "c885ba4499c39ad1f9aacd47344168122766cf20a80a1685667f7932a45be56c", "uijeongbu-flower-direct-region-ganeung-dong": "57ccbf266469a5f95df80cc89a5c73fda75db0790cb7b54df847dca1e28ba4d4", "uijeongbu-flower-direct-region-nogyang-dong": "5dbd5169c1b2555697273b14cfe37a2544e36dbe8093866065e72b69cd99ddb7", "uijeongbu-flower-direct-region-gosan-dong": "6e9746b222ffc9d594648030b46c42261efe5ab5f50cf4ff84372e8e672d35bb", "uijeongbu-flower-direct-region-sangok-dong": "b5cb924eb652e9020e862cb1765c667bf1389a2b7ba2b5d820b94ffde71a1f20"};
test('twelve original entire article objects and order are preserved',()=>{
 const p=read('pages');assert.deepEqual(p.slice(0,12).map(x=>x.pageKey),Object.keys(old));for(const a of p.slice(0,12))assert.equal(sha(canonical(a)),old[a.pageKey]);
});
test('new named facility N1 does not consume held Jail or alter original regional denominator',()=>{
 const p=read('pages'),m=read('publish-manifest');assert.equal(p.length,13);assert.equal(p.filter(x=>x.pageType==='regional-service').length,12);assert.equal(m.directRelease.plannedOriginalCount,13);assert.equal(m.directRelease.reviewedArticleCount,12);assert.deepEqual(m.directRelease.deferredRoutes,['/regions/jail-dong/']);assert.equal(m.additiveBatches[0].plannedOriginalCount,1);assert.equal(m.additiveBatches[0].previousPublishedCount,12);
 const a=p.at(-1);assert.equal(a.url,'/funeral/uijeongbu-st-marys-funeral-wreath/');assert.equal(a.pageType,'funeral-facility');assert.equal(a.productCardLimit,3);assert.deepEqual(a.productCardKeys,['funeral-basic','funeral-premium','funeral-large']);assert.deepEqual(selectProducts(a,read('products'),3).map(x=>x.key),a.productCardKeys);assert.ok(a.relatedKeys.every(k=>p.some(z=>z.pageKey===k)));assert.equal(a.title,a.h1);
});
test('funeral hub is discoverable but excluded from index at one child',()=>{
 const h=read('architecture').hubs.find(x=>x.category==='funeral');assert.equal(h.children,1);assert.equal(h.indexable,false);assert.equal(1+read('pages').length+read('architecture').hubs.filter(x=>x.indexable).length,15);
});
