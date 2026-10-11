import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const pages=read('src/data/pages.json'), proof=read('src/data/customer-copy-review-20261011.json'), history=read('docs/customer-copy-history-20261011.json');
const customer=['title','primaryKeyword','h1','description','cardSummary','firstAnswer','contentMarkdown','sections','faq','sources','source','sourceData'];
test('all25 customer revisions equal independently reviewed exact copy inputs',()=>{
 assert.equal(pages.length,25);assert.equal(proof.approvedCustomerPages.length,25);
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
   assert.equal(current.directRelease.plannedOriginalCount,26);
   const d=x=>Object.fromEntries(Object.entries(x).filter(([k])=>k!=='contentHashes'));
   assert.deepEqual(d(current.directRelease),d(old.directRelease));
   assert.equal(current.customerCopyRevision.newArticles,0);
   assert.deepEqual(current.customerCopyRevision.heldRoutes,['/regions/mokhyeon-dong/']);
  }
 }
});
test('catalog descriptions are the only product changes; original business facts and image paths remain',()=>{
 const strip=p=>Object.fromEntries(Object.entries(p).filter(([k])=>k!=='desc'));
 assert.deepEqual(read('src/data/products.json').map(strip),history.oldData['products.json'].map(strip));
 const manifest=JSON.parse(proof.approvalBasis.choiceCommonManifest.utf8Content);
 for(const row of manifest.commonChanges){assert.equal(hash(fs.readFileSync(new URL('../'+row.path,import.meta.url))),row.proposalSha256,row.path);}
});
test('initial evidence stays historical and revised snapshots cannot reuse old content hashes',()=>{
 assert.equal(history.baselineSource,'b6373facad5548f3a4680d8e6eaaa588d5a93682');
 for(const p of pages){const old=history.oldData['pages.json'].find(x=>x.pageKey===p.pageKey);assert.notEqual(p.snapshotHash,old.snapshotHash);}
 assert.equal(proof.externalWrites,0);
 assert.equal(proof.releaseId,'gwangju-customer-copy-20261011');
});
test('shared delivery wording preserves business facts and ribbon notice is once per product group',()=>{
 const strip=x=>Object.fromEntries(Object.entries(x).filter(([k])=>k!=='deliveryNotice'));
 assert.deepEqual(strip(read('src/data/business-truth.json')),strip(history.oldData['business-truth.json']));
 const cards=fs.readFileSync(new URL('../src/components/ProductCards.astro',import.meta.url),'utf8');
 assert.equal((cards.match(/사진 속 리본은 예시입니다/g)||[]).length,1);
 assert.ok(cards.includes("products.some((p:any)=>p.family==='congrats')"));
 assert.ok(cards.includes('site.productVariationNotice'));assert.ok(cards.includes('site.deliveryNotice'));
});

// Exact independently reviewed bytes; independent data pins and pending-state invariants.
const evidencePins={
  "docs/customer-copy-history-20261011.json": "e6e1d80a89998d2a5c2babaff75aefc32cb7b2f6ddf7e3ac40031d1b5d682c21",
  "src/data/customer-copy-review-20261011.json": "a0c7a265f65b47d1a6612d665cb5298f179a9667a999642b7831cd3a808868db",
  "src/data/direct-checkpoint.json": "814e7ed18a2220f51d2a117bf389d141c99dce0fbe471df5d406ebc334f8551e"
};
const finalCommonPins={
  "src/components/InlineOrderBanner.astro": "2c6f04398566b692709fa30f825ec2c85e2cb18e3a605c64bc3b1a413995a3cc",
  "src/components/InlineText.astro": "ac748bd0e67c41dab43634bbb63a606d2f2124d1f2c089b1266a52795c3ceb0a",
  "src/components/MarkdownContent.astro": "664e29b01720f12ac6b479b9fe722907c192f1df44338ba3df9a764ba7e3ac77",
  "src/components/ProductCards.astro": "6ef4a76825ff25f4361ebd04b1e63f08cd571eda76e4ac99438c6b8af74d1511",
  "src/components/RegionDirectory.astro": "034be5528c34b7d791745a9ba9a1dfee06b0cf4db07cc05ac3fa7514d87d41ae",
  "src/data/business-truth.json": "3e1be4b64f26d88bc874a72ce8e0597ba092bd22e4e0c7d205314acb23349ee0",
  "src/data/products.json": "9f9470505da88ec2aab9ca86290014024e79c5730a7d4e82ce9478a6164b9e6d",
  "src/layouts/BaseLayout.astro": "cb0eadcc8d98bb3a61256d4efba40fb5c16370e5d0ba6189ed63531f9a437fa1",
  "src/lib/sources.mjs": "411ce236880502a2cbe25270ee76101211b3ce11223fb3225c3473da8baae5be",
  "src/pages/404.astro": "f4497cf673dd7cf0e2d045ec7c8253fb56f20b366689efea473e36c080adae9e",
  "src/pages/[category]/[slug].astro": "1ea6206b5eecd3aeedb323d69b980b7a64620b64b4386bbe6d0bace319f90f94",
  "src/pages/[category]/index.astro": "72a84be9582229b1aa56ee3253b7dab8fee655e31f8d15a81c76308aab452dc7",
  "src/pages/index.astro": "504d1de999d1d577ca6a8ff16d7661c9201ca9310f030feb158cce23214443c8"
};
const allowedCopyCheckpoint={
  "releaseId": "gwangju-customer-copy-20261011",
  "baselineSource": "b6373facad5548f3a4680d8e6eaaa588d5a93682",
  "originalPlanN": 26,
  "existingArticles": 25,
  "newArticles": 0,
  "heldRoutes": [
    "/regions/mokhyeon-dong/"
  ],
  "initialHistory": "docs/customer-copy-history-20261011.json",
  "copyReview": "src/data/customer-copy-review-20261011.json",
  "state": "local-integrated-source-pending-independent-code-review"
};
const bytes=p=>fs.readFileSync(new URL('../'+p,import.meta.url));
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
