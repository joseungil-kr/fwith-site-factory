import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const pages=read('src/data/pages.json'), proof=read('src/data/customer-copy-review-20261011.json'), history=read('docs/customer-copy-history-20261011.json');
const customer=['title','primaryKeyword','h1','description','cardSummary','firstAnswer','contentMarkdown','sections','faq','sources','source','sourceData'];
test('all5 customer revisions equal independently reviewed exact copy inputs',()=>{
 assert.equal(pages.length,5);assert.equal(proof.approvedCustomerPages.length,5);
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
 for(const row of manifest.commonChanges){assert.equal(hash(fs.readFileSync(new URL('../'+row.path,import.meta.url))),row.proposalSha256,row.path);}
});
test('initial evidence stays historical and revised snapshots cannot reuse old content hashes',()=>{
 assert.equal(history.baselineSource,'292baeb3ba0edc5bed8491bd6cee2e8ffb2c33d2');
 for(const p of pages){const old=history.oldData['pages.json'].find(x=>x.pageKey===p.pageKey);assert.notEqual(p.snapshotHash,old.snapshotHash);}
 assert.equal(proof.externalWrites,0);
 assert.equal(proof.releaseId,'gangbuk-customer-copy-20261011');
});

// Exact independently reviewed bytes; independent data pins and pending-state invariants.
const evidencePins={
  "docs/customer-copy-history-20261011.json": "d72d349257e38c53a48cb80c43d7ea2cd64fa55a670393303ca2c4d10ca97f7c",
  "src/data/customer-copy-review-20261011.json": "e9f0659980e609ebaf05528d5ade8f9562f7cf6d1da16bcf99a63c6b8adfbdca",
  "src/data/direct-checkpoint.json": "56270c770a2c275017222526d36fcd72a113fcfe8fd375106514b98e5a87c318"
};
const finalCommonPins={
  "src/components/InlineOrderBanner.astro": "1dc7a9149f1f1f3fbea6c80de149da09955a9ac2b7939eaf7e04777f3b683202",
  "src/components/InlineText.astro": "ac748bd0e67c41dab43634bbb63a606d2f2124d1f2c089b1266a52795c3ceb0a",
  "src/components/MarkdownContent.astro": "664e29b01720f12ac6b479b9fe722907c192f1df44338ba3df9a764ba7e3ac77",
  "src/components/ProductCards.astro": "5febb0edfaa1b1825fb7783957e7ec0a7373329bd85200e076daafe157ac7c6e",
  "src/components/RegionDirectory.astro": "56ced6b6514d4bb27672921ebf63989d70850c3a8570a168ee400098c00f41d0",
  "src/data/business-truth.json": "f4c6ba8b636a739a40edbb85982a23c00b28a09f43685393afb80a431514153b",
  "src/data/products.json": "ef1e505337590f4cb80e0ff770de13487324d0a7f5d867354ef5fd3d8fa9d97c",
  "src/layouts/BaseLayout.astro": "cb0eadcc8d98bb3a61256d4efba40fb5c16370e5d0ba6189ed63531f9a437fa1",
  "src/lib/sources.mjs": "0bea1d95eed1c8544baf757baabdd4eaf2827788250575b626c9a0879efd1d9f",
  "src/pages/404.astro": "f4497cf673dd7cf0e2d045ec7c8253fb56f20b366689efea473e36c080adae9e",
  "src/pages/[category]/[slug].astro": "d8a0b2be0215d73b28ed45637baebc852d3a044fe958947c8e27cafe5a8c8ff2",
  "src/pages/[category]/index.astro": "bb7e4bbb0e9d43212f391a89788e163d38f4629d9fa7b41856f56e6c01dd70d3",
  "src/pages/index.astro": "1e1ad7a6f54a2877b658affd137e4cda9a3b417a687bd8a969639776c3ec0801"
};
const allowedCopyCheckpoint={
  "releaseId": "gangbuk-customer-copy-20261011",
  "baselineSource": "292baeb3ba0edc5bed8491bd6cee2e8ffb2c33d2",
  "originalPlanN": 5,
  "existingArticles": 5,
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
