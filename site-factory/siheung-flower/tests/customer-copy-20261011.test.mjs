import {readHistoricalBannerSource} from './shared-banner-amendment.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const read=p=>JSON.parse(readHistoricalBannerSource(new URL('../'+p,import.meta.url),'utf8'));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const pages=read('src/data/pages.json'), proof=read('src/data/customer-copy-review-20261011.json'), history=read('docs/customer-copy-history-20261011.json');
const customer=['title','primaryKeyword','h1','description','cardSummary','firstAnswer','contentMarkdown','sections','faq','sources','source','sourceData'];
test('all31 customer revisions equal independently reviewed exact copy inputs',()=>{
 assert.equal(pages.length,31);assert.equal(proof.approvedCustomerPages.length,31);
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
   assert.equal(current.directRelease.plannedOriginalCount,31);
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
 assert.equal(history.baselineSource,'25608a70c4abfe992a7a0eb4fd8fc1365402a683');
 for(const p of pages){const old=history.oldData['pages.json'].find(x=>x.pageKey===p.pageKey);assert.notEqual(p.snapshotHash,old.snapshotHash);}
 assert.equal(proof.externalWrites,0);
 assert.equal(proof.releaseId,'siheung-customer-copy-20261011');
});

// Exact independently reviewed bytes; independent data pins and pending-state invariants.
const evidencePins={
  "docs/customer-copy-history-20261011.json": "8146ab66e923923c5d44c595d6151008392e43dde23178b87c0cb01a282340a4",
  "src/data/customer-copy-review-20261011.json": "2c74151f3497daffefb23e5470af9d805322d24465b01fcd4fb7c962a05b9475",
  "src/data/direct-checkpoint.json": "6b729b41ff5e37eec314512cc6fc181a6b893cde8f0e250ce7e6c543bcd2b190"
};
const finalCommonPins={
  "src/components/InlineOrderBanner.astro": "a73a1e97d36f63923870360a00aa0ac5a8c7cac3fa06ea0694cf2e9acda947c8",
  "src/components/InlineText.astro": "ac748bd0e67c41dab43634bbb63a606d2f2124d1f2c089b1266a52795c3ceb0a",
  "src/components/MarkdownContent.astro": "664e29b01720f12ac6b479b9fe722907c192f1df44338ba3df9a764ba7e3ac77",
  "src/components/ProductCards.astro": "d26eefffb698baceaa06d30a1f40c8d7c576d02f47e76db107f0084dd589605c",
  "src/components/RegionDirectory.astro": "cfe6533631f9c99e9beeebe4f53223a5f2bfe57cf328645d87d1eb3fe5243690",
  "src/data/business-truth.json": "3e1be4b64f26d88bc874a72ce8e0597ba092bd22e4e0c7d205314acb23349ee0",
  "src/data/products.json": "9f9470505da88ec2aab9ca86290014024e79c5730a7d4e82ce9478a6164b9e6d",
  "src/layouts/BaseLayout.astro": "cb0eadcc8d98bb3a61256d4efba40fb5c16370e5d0ba6189ed63531f9a437fa1",
  "src/lib/sources.mjs": "411ce236880502a2cbe25270ee76101211b3ce11223fb3225c3473da8baae5be",
  "src/pages/404.astro": "f4497cf673dd7cf0e2d045ec7c8253fb56f20b366689efea473e36c080adae9e",
  "src/pages/[category]/[slug].astro": "7d7396db8a3a722778ee90a254a1780383990b671c94e470bd326d04229823b2",
  "src/pages/[category]/index.astro": "d147d68f7e26e17962f3da021405f993d2293756d86ebbcf4923b22e45b0f4b3",
  "src/pages/index.astro": "035fff136d481093dfc383c20fae5198e9fa2f7dc5a42dd02958885df65c6f0d"
};
const allowedCopyCheckpoint={
  "releaseId": "siheung-customer-copy-20261011",
  "baselineSource": "25608a70c4abfe992a7a0eb4fd8fc1365402a683",
  "originalPlanN": 31,
  "existingArticles": 31,
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
