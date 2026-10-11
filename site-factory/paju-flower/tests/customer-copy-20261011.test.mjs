import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const pages=read('src/data/pages.json'), proof=read('src/data/customer-copy-review-20261011.json'), history=read('docs/customer-copy-history-20261011.json');
const customer=['title','primaryKeyword','h1','description','cardSummary','firstAnswer','contentMarkdown','sections','faq','sources','source','sourceData'];
test('all32 customer revisions equal independently reviewed exact copy inputs',()=>{
 assert.equal(pages.length,32);assert.equal(proof.approvedCustomerPages.length,32);
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
   assert.equal(current.directRelease.plannedOriginalCount,35);
   const d=x=>Object.fromEntries(Object.entries(x).filter(([k])=>k!=='contentHashes'));
   assert.deepEqual(d(current.directRelease),d(old.directRelease));
   assert.equal(current.customerCopyRevision.newArticles,0);
   assert.deepEqual(current.customerCopyRevision.heldRoutes,['/regions/jangdan-myeon/','/regions/jindong-myeon/','/regions/jinseo-myeon/']);
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
 assert.equal(history.baselineSource,'4a8011cfaac421aacb6ab4b753ad0a792d11dfc1');
 for(const p of pages){const old=history.oldData['pages.json'].find(x=>x.pageKey===p.pageKey);assert.notEqual(p.snapshotHash,old.snapshotHash);}
 assert.equal(proof.externalWrites,0);
 assert.equal(proof.releaseId,'paju-customer-copy-20261011');
});
test('shared delivery wording preserves business facts and ribbon notice is once per product group',()=>{
 const strip=x=>Object.fromEntries(Object.entries(x).filter(([k])=>k!=='deliveryNotice'));
 assert.deepEqual(strip(read('src/data/business-truth.json')),strip(history.oldData['business-truth.json']));
 const cards=fs.readFileSync(new URL('../src/components/ProductCards.astro',import.meta.url),'utf8');
 assert.equal((cards.match(/사진 속 리본은 예시입니다/g)||[]).length,1);
 assert.ok(cards.includes("products.some((p:any)=>p.family==='congrats')"));
 assert.ok(cards.includes('site.productVariationNotice'));assert.ok(cards.includes('site.deliveryNotice'));
});

// Exact independently reviewed bytes; these are not hashes supplied by the data under test.
const evidencePins={
  "docs/customer-copy-history-20261011.json": "b6aba2188a04b5e87fe02599b05e0a5485779c785cc109121c9aa084c7a56694",
  "src/data/customer-copy-review-20261011.json": "9f2bcab4683a31affc2447591e75bb26e4da95da4ce33b99b5883b30f10dd23f",
  "src/data/direct-checkpoint.json": "1fa9b5fa136ddfc6fe4a8cc1db86948eb28fe0e7ba106931c7ea73632fe40218"
};
const finalCommonPins={
  "src/components/InlineOrderBanner.astro": "a73a1e97d36f63923870360a00aa0ac5a8c7cac3fa06ea0694cf2e9acda947c8",
  "src/components/ProductCards.astro": "d26eefffb698baceaa06d30a1f40c8d7c576d02f47e76db107f0084dd589605c",
  "src/components/RegionDirectory.astro": "956bcb3826530335ec932a630a339627937ec05dd1231fcadb2980bff737ed8c",
  "src/data/business-truth.json": "3e1be4b64f26d88bc874a72ce8e0597ba092bd22e4e0c7d205314acb23349ee0",
  "src/data/products.json": "9f9470505da88ec2aab9ca86290014024e79c5730a7d4e82ce9478a6164b9e6d",
  "src/layouts/BaseLayout.astro": "cb0eadcc8d98bb3a61256d4efba40fb5c16370e5d0ba6189ed63531f9a437fa1",
  "src/lib/sources.mjs": "411ce236880502a2cbe25270ee76101211b3ce11223fb3225c3473da8baae5be",
  "src/pages/[category]/[slug].astro": "7d7396db8a3a722778ee90a254a1780383990b671c94e470bd326d04229823b2",
  "src/pages/[category]/index.astro": "ee9c0213f71a38dd9fb366531c8b4559e75adf2fb49d4ebc367b87f9376f030f",
  "src/pages/index.astro": "4da0bb4544e167eefe3e16941871bd736794977741df9382be234019a865a8ee"
};
const allowedCopyCheckpoint={
  "releaseId": "paju-customer-copy-20261011",
  "baselineSource": "4a8011cfaac421aacb6ab4b753ad0a792d11dfc1",
  "originalPlanN": 35,
  "existingArticles": 32,
  "newArticles": 0,
  "heldRoutes": [
    "/regions/jangdan-myeon/",
    "/regions/jindong-myeon/",
    "/regions/jinseo-myeon/"
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
