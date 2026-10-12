import {readHistoricalBannerSource} from './shared-banner-amendment.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const read=p=>JSON.parse(readHistoricalBannerSource(new URL('../'+p,import.meta.url),'utf8'));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const pages=read('src/data/pages.json'), proof=read('src/data/customer-copy-review-20261011.json'), history=read('docs/customer-copy-history-20261011.json');
const customer=['title','primaryKeyword','h1','description','cardSummary','firstAnswer','contentMarkdown','sections','faq','sources','source','sourceData'];
test('all5 customer revisions equal independently reviewed exact copy inputs',()=>{
 assert.equal(pages.length,5);assert.equal(proof.approvedCustomerPages.length,5);
 const approved=JSON.parse(proof.approvalBasis.approvedArticles.utf8Content);
 for(const p of pages){const a=approved.find(x=>x.slug===p.slug);assert.ok(a);for(const [key,value] of Object.entries(a))assert.deepEqual(p[key],value,`${p.slug}:${key}`);}
 for(const p of pages){const a=proof.approvedCustomerPages.find(a=>a.pageKey===p.pageKey);assert.ok(a);for(const k of customer)assert.deepEqual(p[k],a[k],`${p.slug}:${k}`);}
 for(const [role,item] of Object.entries(proof.approvalBasis))assert.equal(hash(item.utf8Content),item.sha256,role);
});
test('original identities, membership, products and initial denominator remain unchanged',()=>{
 const omit=new Set([...customer,'snapshotId','snapshotHash']);
 const filtered=p=>Object.fromEntries(Object.entries(p).filter(([k])=>!omit.has(k)));
 assert.deepEqual(pages.map(filtered),history.oldData['pages.json'].map(filtered));
 for(const name of ['page-map','architecture','publish-manifest']){
  const current=read(`src/data/${name}.json`), old=history.oldData[`${name}.json`];
  assert.equal(current.pages.length,old.pages.length);
  if(name==='publish-manifest'){
   assert.equal(current.directRelease.plannedOriginalCount,5);
   const d=x=>Object.fromEntries(Object.entries(x).filter(([k])=>k!=='contentHashes'));
   assert.deepEqual(d(current.directRelease),d(old.directRelease));
   assert.equal(current.customerCopyRevision.newArticles,0);
   assert.deepEqual(current.customerCopyRevision.heldRoutes,[]);
  }
 }
});
test('catalog descriptions are the only product changes; original business facts and image paths remain',()=>{
 const strip=p=>Object.fromEntries(Object.entries(p).filter(([k])=>k!=='desc'));
 assert.deepEqual(read('src/data/products.json').map(strip),history.oldData['products.json'].map(strip));
 const manifest=JSON.parse(proof.approvalBasis.choiceCommonManifest.utf8Content);
 for(const row of manifest.commonChanges){assert.equal(hash(readHistoricalBannerSource(new URL('../'+row.path,import.meta.url))),row.proposalSha256,row.path);}
});
test('initial evidence stays historical and revised snapshots cannot reuse old content hashes',()=>{
 assert.equal(history.baselineSource,'c7950231a67ff2494f0c37298029343456089b39');
 for(const p of pages){const old=history.oldData['pages.json'].find(x=>x.pageKey===p.pageKey);assert.notEqual(p.snapshotHash,old.snapshotHash);}
 assert.equal(proof.externalWrites,0);
 assert.equal(proof.releaseId,'seoul-dongdaemun-customer-copy-20261011');
});
test('delivery and ribbon notices remain once per purchase group rather than every card and footer',()=>{
 const cards=readHistoricalBannerSource(new URL('../src/components/ProductCards.astro',import.meta.url),'utf8');
 const layout=readHistoricalBannerSource(new URL('../src/layouts/BaseLayout.astro',import.meta.url),'utf8');
 assert.equal((cards.match(/site.deliveryNotice/g)||[]).length,1);
 assert.equal((layout.match(/site.deliveryNotice/g)||[]).length,0);
 assert.match(cards,/products.some\(\(p:any\)=>p.family==='congrats'\)/);
 assert.equal((cards.match(/사진 속 리본은 예시입니다/g)||[]).length,1);
 for(const p of pages)assert.ok(!p.contentMarkdown.includes('표시가격은 상품 기본가격입니다.'));
});
