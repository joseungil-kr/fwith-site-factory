import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts,productFamilies} from '../src/lib/catalog.mjs';
const read=n=>JSON.parse(fs.readFileSync(new URL('../src/data/'+n+'.json',import.meta.url),'utf8'));
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const old={"gwangmyeong-flower-direct-region-gwangmyeong-dong": "4e516157c68345cb2d76eabba1fd1b6e822a622a17723a34774ad3a1a4473b3e", "gwangmyeong-flower-direct-region-cheolsan-dong": "23f93f0191d8c8172e8baeb77136e74573a0dc94b9afdaea272ba123c55cffac", "gwangmyeong-flower-direct-region-haan-dong": "b8a6c6fd0991bc9a39bac0cde41522e6b450fdd8563d66a92588e3b13557da8e", "gwangmyeong-flower-direct-region-soha-dong": "09d03d3391be886e8a2f41f9a5733f31ec3fe7ac7d6a96757f98d77b8b581009", "gwangmyeong-flower-direct-region-iljik-dong": "54e2f111d1eec7d2e076ec2cee457ac9590f80e01ba9c87274bd856da3d85073", "gwangmyeong-flower-direct-region-noonsa-dong": "9e431a6847e036867b13b4246d40c7a6dbbbb792b40727004536ab8c53d3c021", "gwangmyeong-flower-direct-region-gahak-dong": "71222446fa160b9afd0ec9075187f7a99a0d31f06155b1ac011454c0302a6940", "gwangmyeong-flower-direct-region-okgil-dong": "9b1c532e2773eeedc142c2b364fb5549d3a3d93fe610574d8a86f8e7f3059a3d"};
test('eight original entire article objects and order are preserved',()=>{
 const p=read('pages');assert.deepEqual(p.slice(0,8).map(x=>x.pageKey),Object.keys(old));for(const a of p.slice(0,8))assert.equal(sha(canonical(a)),old[a.pageKey]);
});
test('new named venue N1 preserves original regional denominator',()=>{
 const p=read('pages'),m=read('publish-manifest');assert.equal(p.length,9);assert.equal(p.filter(x=>x.pageType==='regional-service').length,8);assert.equal(m.directRelease.plannedOriginalCount,8);assert.equal(m.directRelease.reviewedArticleCount,8);assert.deepEqual(m.directRelease.deferredRoutes,[]);assert.equal(m.additiveBatches[0].plannedOriginalCount,1);assert.equal(m.additiveBatches[0].previousPublishedCount,8);
 const a=p.at(-1);assert.equal(a.url,'/event/gwangmyeong-lapoete-wedding-wreath/');assert.equal(a.pageType,'event-venue');assert.equal(a.productCardLimit,4);assert.equal(a.visualIntent,'event_wreath');assert.deepEqual(productFamilies(a),['congrats']);assert.deepEqual(a.productCardKeys,['congrats-basic','congrats-premium','congrats-large','congrats-xl']);assert.deepEqual(selectProducts(a,read('products'),4).map(x=>x.key),a.productCardKeys);assert.ok(a.relatedKeys.every(k=>p.some(z=>z.pageKey===k)));assert.equal(a.title,a.h1);
});
test('event hub is discoverable but excluded from index at one child',()=>{
 const h=read('architecture').hubs.find(x=>x.category==='event');assert.equal(h.children,1);assert.equal(h.indexable,false);assert.equal(1+read('pages').length+read('architecture').hubs.filter(x=>x.indexable).length,11);
});
