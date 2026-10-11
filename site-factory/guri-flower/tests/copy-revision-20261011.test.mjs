import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts,productFamilies} from '../src/lib/catalog.mjs';

const text=p=>fs.readFileSync(new URL(p,import.meta.url),'utf8');
const read=p=>JSON.parse(text(p));
const pages=read('../src/data/pages.json'),copy=read('./fixtures/reviewed-copy.json'),products=read('../src/data/products.json');
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
test('all reviewed customer fields are exact independently approved copy, with original route order',()=>{
 assert.equal(sha(text('./fixtures/reviewed-copy.json')),'d9c156d4824072e4ad3151a34c19354fcf640435e17cf741c86116a9065f124b');assert.equal(pages.length,7);
 const omit=new Set(['status','approvalVerified','snapshotId','snapshotHash']);
 assert.deepEqual(pages.map(p=>p.pageKey),copy.map(p=>p.pageKey));
 for(let i=0;i<pages.length;i++){
  const project=x=>Object.fromEntries(Object.entries(x).filter(([k])=>!omit.has(k)));
  assert.deepEqual(project(pages[i]),project(copy[i]));
 }
});
for(const page of pages)test(`integrated ${page.slug}: exact cards, current hash and all mirror metadata`,()=>{
 const expected=4;assert.equal(page.productCardLimit,expected);assert.equal(page.productCardKeys.length,expected);
 const selected=selectProducts(page,products,(page.productCardLimit===4||productFamilies(page).length>3?4:3));assert.deepEqual(selected.map(p=>p.key),page.productCardKeys);
 const omit=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);
 const hash=sha(canonical(Object.fromEntries(Object.entries(page).filter(([k])=>!omit.has(k)))));
 assert.equal(page.snapshotHash,hash);assert.equal(page.snapshotId,`direct-content-${page.slug}-${hash.slice(0,16)}`);
 for(const name of ['page-map','architecture','publish-manifest']){
  const row=read('../src/data/'+name+'.json').pages.find(p=>p.pageKey===page.pageKey);
  for(const key of ['snapshotHash','snapshotId','productCardLimit','productCardKeys','url'])assert.deepEqual(row[key],page[key]);
 }
 const m=read('../src/data/publish-manifest.json');assert.deepEqual(m.snapshotLedger[page.snapshotId],{pageKey:page.pageKey,snapshotHash:hash});
 const record=m.directRelease.contentHashes.find(p=>p.pageKey===page.pageKey);assert.equal(record.publicSourceSha256,hash);assert.equal(record.bodySha256,sha(page.contentMarkdown));
});
