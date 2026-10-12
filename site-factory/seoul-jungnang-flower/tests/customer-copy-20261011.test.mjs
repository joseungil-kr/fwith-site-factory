import {readHistoricalBannerSource} from './shared-banner-amendment.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const read=p=>JSON.parse(readHistoricalBannerSource(new URL('../'+p,import.meta.url),'utf8'));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const pages=read('src/data/pages.json'), proof=read('src/data/customer-copy-review-20261011.json'), history=read('docs/customer-copy-history-20261011.json');
const customer=['title','primaryKeyword','h1','description','cardSummary','firstAnswer','contentMarkdown','sections','faq','sources','source','sourceData'];
test('all3 customer revisions equal independently reviewed exact copy inputs',()=>{
 assert.equal(pages.length,3);assert.equal(proof.approvedCustomerPages.length,3);
 for(const p of pages){const a=proof.approvedCustomerPages.find(a=>a.pageKey===p.pageKey);assert.ok(a);for(const k of customer){const expected=k==='contentMarkdown'?read('src/data/notice-followon-review-20261011.json').approvedCustomerPages.find(q=>q.pageKey===p.pageKey)[k]:a[k];assert.deepEqual(p[k],expected,`${p.slug}:${k}`);}}
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
   assert.equal(current.directRelease.plannedOriginalCount,3);
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
 assert.equal(history.baselineSource,'73d92b941fcb3025321adc88f82179c914086551');
 for(const p of pages){const old=history.oldData['pages.json'].find(x=>x.pageKey===p.pageKey);assert.notEqual(p.snapshotHash,old.snapshotHash);}
 assert.equal(proof.externalWrites,0);
 assert.equal(proof.releaseId,'jungnang-customer-copy-20261011');
});

// Exact independently reviewed bytes; independent data pins and pending-state invariants.
const evidencePins={
  "docs/customer-copy-history-20261011.json": "90fabd02cb1236aa2fdcb559d7f64d6470afe399aa0b662a869d4aedbf53038b",
  "src/data/customer-copy-review-20261011.json": "eb14258f4d9f6038cf82abedafba45c7f26974a3c61935e4626b476ef4879117",
  "src/data/direct-checkpoint.json": "4351a9a5b9c21fc958789e7a15034cb1b33e095904c146c3abcf40cd6adf14e3"
};
const finalCommonPins={
  "src/components/InlineOrderBanner.astro": "1dc7a9149f1f1f3fbea6c80de149da09955a9ac2b7939eaf7e04777f3b683202",
  "src/components/InlineText.astro": "ac748bd0e67c41dab43634bbb63a606d2f2124d1f2c089b1266a52795c3ceb0a",
  "src/components/MarkdownContent.astro": "664e29b01720f12ac6b479b9fe722907c192f1df44338ba3df9a764ba7e3ac77",
  "src/components/ProductCards.astro": "77ab69e0b60c08c57849a99de125b8ce370fde2b2d14929416838f6b798ff880",
  "src/components/RegionDirectory.astro": "56ced6b6514d4bb27672921ebf63989d70850c3a8570a168ee400098c00f41d0",
  "src/data/business-truth.json": "f4c6ba8b636a739a40edbb85982a23c00b28a09f43685393afb80a431514153b",
  "src/data/products.json": "ef1e505337590f4cb80e0ff770de13487324d0a7f5d867354ef5fd3d8fa9d97c",
  "src/layouts/BaseLayout.astro": "cb0eadcc8d98bb3a61256d4efba40fb5c16370e5d0ba6189ed63531f9a437fa1",
  "src/lib/sources.mjs": "0bea1d95eed1c8544baf757baabdd4eaf2827788250575b626c9a0879efd1d9f",
  "src/pages/404.astro": "f4497cf673dd7cf0e2d045ec7c8253fb56f20b366689efea473e36c080adae9e",
  "src/pages/[category]/[slug].astro": "d8a0b2be0215d73b28ed45637baebc852d3a044fe958947c8e27cafe5a8c8ff2",
  "src/pages/[category]/index.astro": "a96bf9335870b43847b376579427c8c60ddd3c2e6a27f91093aa01bbad00a620",
  "src/pages/index.astro": "6b301ce1c7392b97d8d44cd9d3587ad53414b130df8802f97a010c1f5f2f3114"
};
const allowedCopyCheckpoint={
  "releaseId": "jungnang-customer-copy-20261011",
  "baselineSource": "73d92b941fcb3025321adc88f82179c914086551",
  "originalPlanN": 3,
  "existingArticles": 3,
  "newArticles": 0,
  "heldRoutes": [],
  "initialHistory": "docs/customer-copy-history-20261011.json",
  "copyReview": "src/data/customer-copy-review-20261011.json",
  "state": "local-integrated-source-pending-independent-code-review"
};
const bytes=p=>readHistoricalBannerSource(new URL('../'+p,import.meta.url));
const validatePinned=(values,pins)=>{for(const [p,expected] of Object.entries(pins))assert.equal(hash(values[p]),expected,p);};
const validateCheckpoint=x=>assert.deepEqual(x,allowedCopyCheckpoint,'copy checkpoint must retain exact pending state and allowed fields');
test('proof, original history and initial checkpoint are pinned to independently reviewed bytes',()=>{
 validatePinned(Object.fromEntries(Object.keys(evidencePins).map(p=>[p,bytes(p)])),evidencePins);
});
test('all final customer common surfaces remain bound to reviewed bytes',()=>{
 validatePinned(Object.fromEntries(Object.keys(finalCommonPins).map(p=>[p,bytes(p)])),finalCommonPins);
});
test('local copy state cannot become false hosted or visual completion',()=>{
 validateCheckpoint(read('src/data/publish-manifest.json').customerCopyRevision);
});
test('negative evidence, common copy and false completion fixtures fail closed',()=>{
 const e=Object.fromEntries(Object.keys(evidencePins).map(p=>[p,bytes(p)]));
 for(const path of Object.keys(evidencePins)){const changed={...e,[path]:Buffer.concat([e[path],Buffer.from(' ')] )};assert.throws(()=>validatePinned(changed,evidencePins));}
 const c=Object.fromEntries(Object.keys(finalCommonPins).map(p=>[p,bytes(p)]));
 for(const path of Object.keys(finalCommonPins)){const changed={...c,[path]:Buffer.concat([c[path],Buffer.from('<!-- changed -->')])};assert.throws(()=>validatePinned(changed,finalCommonPins));}
 for(const fields of [{state:'published',publicComplete:true},{visualQa:'PASS'},{indexnow:'received'},{integrationReview:'PASS'}])assert.throws(()=>validateCheckpoint({...allowedCopyCheckpoint,...fields}));
});
