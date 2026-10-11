import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {validateCustomerCopyRevision,WRITER_ID,EXPECTED_REVIEWER_ID} from '../src/lib/manual-contract.mjs';
const root=path.resolve(new URL('..',import.meta.url).pathname);
const bytes=n=>fs.readFileSync(path.join(root,n));
const read=n=>JSON.parse(bytes(n));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const revision=read('src/data/customer-copy-revision-20261011.json');
test('exact independently COPY-approved38 and9 surfaces are pinned and match delivered files',()=>{
 assert.equal(sha(bytes('src/data/customer-copy-revision-20261011.json')),'e88d5124e05a55ffc06d540fa5a72ae7e34876bc631c6e63257454efb2e6ea32');
 assert.equal(sha(bytes('docs/customer-copy-history-20261011.json')),'0f016c81efefcb859d6697fa61ffa4814c72e0df3387dbc8ad20b4353206bf36');
 assert.equal(validateCustomerCopyRevision(root).articles.length,39);
 assert.equal(revision.surfaceFiles.length,9);
 assert.equal(revision.articles.filter(p=>p.publicationMode==='manual').length,24);
 assert.equal(revision.articles.filter(p=>p.publicationMode==='frozen').length,15);
});
test('new revision has actual assigned identities and does not reuse old independent approval',()=>{
 assert.equal(WRITER_ID,'/root/review_remaining_regional_copy');assert.equal(EXPECTED_REVIEWER_ID,'/root');assert.notEqual(WRITER_ID,EXPECTED_REVIEWER_ID);
 const history=read('docs/customer-copy-history-20261011.json');
 assert.equal(JSON.parse(history.files['src/data/manual-provenance.json'].text).writerId,'60aca2bf-e351-4d63-971a-b8eb1095b0f8');
 assert.equal(JSON.parse(history.files['src/data/manual-review.json'].text).reviewerId,'3eef5a0b-25df-4af7-97a8-fe838dd6d708');
 assert.equal(read('src/data/manual-review.json').evidenceFile,'src/data/manual-copy-review-evidence-20261011.json');
});
test('all14 revised frozen snapshots get current hashes while old ledger stays immutable',()=>{
 const history=read('docs/customer-copy-history-20261011.json');const old=JSON.parse(history.files['src/data/publish-manifest.json'].text);const manifest=read('src/data/publish-manifest.json');
 for(const [id,value] of Object.entries(old.snapshotLedger))assert.deepEqual(manifest.snapshotLedger[id],value);
 for(const entry of revision.articles.filter(p=>p.publicationMode==='frozen')){
  const previous=old.pages.find(p=>p.pageKey===entry.pageKey);if(entry.noindexAlias){assert.equal(entry.pageKey,'ansan-flower-launch-08');assert.equal(entry.parentSnapshotId,'ansan-flower-launch-08-v1');assert.notEqual(entry.snapshotId,entry.parentSnapshotId);continue;}assert.equal(previous.snapshotId,entry.parentSnapshotId);
  for(const name of ['publish-manifest','page-map']){const row=read('src/data/'+name+'.json').pages.find(p=>p.pageKey===entry.pageKey);assert.equal(row.snapshotId,entry.snapshotId);assert.equal(row.snapshotHash,entry.snapshotHash);assert.equal(row.parentSnapshotId,previous.snapshotId);}
  assert.notEqual(entry.snapshotId,entry.parentSnapshotId);assert.equal(manifest.snapshotLedger[entry.snapshotId].sourceFileSha256,entry.currentFileSha256);
 }
});
test('all38 original public URLs retain order and no new manual or frozen URL is added',()=>{
 const history=read('docs/customer-copy-history-20261011.json');
 for(const name of ['page-map','manual-page-map'])assert.deepEqual(read('src/data/'+name+'.json').pages.map(p=>[p.pageKey,p.url]),JSON.parse(history.files['src/data/'+name+'.json'].text).pages.map(p=>[p.pageKey,p.url]));
 assert.equal(read('src/data/page-map.json').pages.length+read('src/data/manual-page-map.json').pages.length,38);
});
