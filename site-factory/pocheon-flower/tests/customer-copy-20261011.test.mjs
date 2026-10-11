import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const pages=read('src/data/pages.json'), proof=read('src/data/customer-copy-review-20261011.json'), history=read('docs/customer-copy-history-20261011.json');
const customer=['title','primaryKeyword','h1','description','cardSummary','firstAnswer','contentMarkdown','sections','faq','sources','source','sourceData'];
test('all17 customer revisions equal independently reviewed exact copy inputs',()=>{
 assert.equal(pages.length,17);assert.equal(proof.approvedCustomerPages.length,17);
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
   assert.equal(current.directRelease.plannedOriginalCount,18);
   const d=x=>Object.fromEntries(Object.entries(x).filter(([k])=>k!=='contentHashes'));
   assert.deepEqual(d(current.directRelease),d(old.directRelease));
   assert.equal(current.customerCopyRevision.newArticles,0);
   assert.deepEqual(current.customerCopyRevision.heldRoutes,['/regions/changsu-myeon/']);
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
 assert.equal(history.baselineSource,'80885f720b382cd71fab0f68228040e7637a8b34');
 for(const p of pages){const old=history.oldData['pages.json'].find(x=>x.pageKey===p.pageKey);assert.notEqual(p.snapshotHash,old.snapshotHash);}
 assert.equal(proof.externalWrites,0);
 assert.equal(proof.releaseId,'pocheon-customer-copy-20261011');
});
