import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const pages=read('src/data/pages.json'), proof=read('src/data/customer-copy-review-20261011.json'), history=read('docs/customer-copy-history-20261011.json');
const customer=['title','primaryKeyword','h1','description','cardSummary','firstAnswer','contentMarkdown','sections','faq','sources','source','sourceData'];
test('all11 customer revisions equal independently reviewed exact copy inputs',()=>{
 assert.equal(pages.length,11);assert.equal(proof.approvedCustomerPages.length,11);
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
   assert.equal(current.directRelease.plannedOriginalCount,11);
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
 const manifest=JSON.parse(proof.approvalBasis.surfaceManifest.utf8Content);
 const dedup=JSON.parse(proof.approvalBasis.noteDedupManifest.utf8Content);
 for(const row of manifest.records){const expected=row.path==='src/components/ProductCards.astro'?dedup.proposalSha256:row.proposalSha256;assert.equal(hash(fs.readFileSync(new URL('../'+row.path,import.meta.url))),expected,row.path);}
});
test('initial evidence stays historical and revised snapshots cannot reuse old content hashes',()=>{
 assert.equal(history.baselineSource,'559669d44ed6a4dc3d2c5a2fef760ca5f53f9412');
 for(const p of pages){const old=history.oldData['pages.json'].find(x=>x.pageKey===p.pageKey);assert.notEqual(p.snapshotHash,old.snapshotHash);}
 assert.equal(proof.externalWrites,0);
 assert.equal(proof.releaseId,'uiwang-customer-copy-20261011');
});

// Exact independently reviewed bytes; independent data pins and pending-state invariants.
const evidencePins={
  "docs/customer-copy-history-20261011.json": "8fb76cbc88da4b5c49a122e08e02995e45201cd6b490187bcb54d8b323c412f6",
  "src/data/customer-copy-review-20261011.json": "fd74fd2e189a2b26403d9b3ded73b5c350643a5c87cc6771e4eb0a1508eb094b",
  "src/data/direct-checkpoint.json": "d118061f0730fffac6c9832115ecf2b0dc1f5e78e715d1af9816b4acfb1af715"
};
const finalCommonPins={
  "src/components/InlineOrderBanner.astro": "99484d4dd1d755a54fedcd2a2d1c27b8983cd5d3391e64190d4635e751c866ee",
  "src/components/InlineText.astro": "ac748bd0e67c41dab43634bbb63a606d2f2124d1f2c089b1266a52795c3ceb0a",
  "src/components/MarkdownContent.astro": "664e29b01720f12ac6b479b9fe722907c192f1df44338ba3df9a764ba7e3ac77",
  "src/components/ProductCards.astro": "c5748db96cebcb8ee26b19e551a5dcdbd3a5157f502607dd4fa1dc5031422107",
  "src/components/RegionDirectory.astro": "ce32ec98d3b19b69b1adf97e2d732d0a0de9b0055773532fe5302af4905cfffb",
  "src/data/business-truth.json": "2284855a674c3a63930f751f4fbea376cd0b776c169633dcff2b9502096874a6",
  "src/data/products.json": "9f9470505da88ec2aab9ca86290014024e79c5730a7d4e82ce9478a6164b9e6d",
  "src/layouts/BaseLayout.astro": "cb0eadcc8d98bb3a61256d4efba40fb5c16370e5d0ba6189ed63531f9a437fa1",
  "src/lib/sources.mjs": "0bea1d95eed1c8544baf757baabdd4eaf2827788250575b626c9a0879efd1d9f",
  "src/pages/404.astro": "f4497cf673dd7cf0e2d045ec7c8253fb56f20b366689efea473e36c080adae9e",
  "src/pages/[category]/[slug].astro": "1d348bc64a8e2dcb77b8c5520823cd9a70956abf82d710a6ac0ffd52733599c9",
  "src/pages/[category]/index.astro": "ed373458aad28a9f6a188d2642dd31c0eda20a2bdcad24daaf735b5ec5f06b6b",
  "src/pages/index.astro": "f70f904d287b86ccb9876f435ef73bc3ea7369d61a3474b9644975cfa494f059"
};
const allowedCopyCheckpoint={
  "releaseId": "uiwang-customer-copy-20261011",
  "baselineSource": "559669d44ed6a4dc3d2c5a2fef760ca5f53f9412",
  "originalPlanN": 11,
  "existingArticles": 11,
  "newArticles": 0,
  "heldRoutes": [],
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
