import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const slugs=['uijeongbu-dong','howon-dong','jangam-dong','singok-dong','yonghyeon-dong','millak-dong','nakyang-dong','jail-dong','geumo-dong','ganeung-dong','nogyang-dong','gosan-dong','sangok-dong'];
test('Uijeongbu initial scope is 13 legal units, 15 current administrative units and no duplicate canonical aliases',()=>{
 const pages=read('pages'),coverage=read('region-coverage');
 assert.deepEqual(pages.map(p=>p.slug),slugs.filter(s=>s!=='jail-dong'));assert.equal(coverage.units.length,13);assert.equal(coverage.administrativeCrosswalk.length,15);
 assert.equal(new Set(coverage.administrativeCrosswalk.map(a=>a.aliasKey)).size,15);
 assert.equal(coverage.districts.length,1);assert.equal(coverage.districts[0].name,'의정부시');assert.equal(coverage.representatives.length,13);
 for(const p of pages){assert.equal(p.category,'regions');assert.equal(p.pageType,'regional-service');assert.equal(p.url,`/regions/${p.slug}/`);}
 const names=alias=>coverage.administrativeCrosswalk.find(a=>a.name===alias).relations.map(r=>coverage.units.find(u=>u.unitKey===r.unitKey).name).sort();
 assert.deepEqual(names('고산동'),['고산동','산곡동']);assert.deepEqual(names('송산1동'),['용현동']);
 assert.deepEqual(names('의정부1동'),['가능동','의정부동','호원동']);assert.deepEqual(names('자금동'),['금오동','녹양동','자일동']);
});
test('direct snapshot hashes bind every public customer field and all four page collections',()=>{
 const pages=read('pages'),manifest=read('publish-manifest');
 assert.equal(manifest.directRelease.sourceMode,'direct-git');assert.deepEqual(manifest.snapshotLedger,{});
 assert.equal(manifest.directRelease.plannedOriginalCount,13);assert.equal(manifest.directRelease.reviewedArticleCount,12);
 for(const p of pages){
  const omit=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);
  const digest=sha(canonical(Object.fromEntries(Object.entries(p).filter(([k])=>!omit.has(k)))));
  assert.equal(p.snapshotHash,digest);assert.equal(p.snapshotId,`direct-content-${p.slug}-${digest.slice(0,16)}`);
  const row=manifest.directRelease.contentHashes.find(x=>x.pageKey===p.pageKey);
  assert.equal(row.publicSourceSha256,digest);assert.equal(row.bodySha256,sha(p.contentMarkdown));
  for(const c of [manifest,read('page-map'),read('architecture')])assert.equal(c.pages.find(x=>x.pageKey===p.pageKey).snapshotHash,digest);
 }
});
test('source contains no copied regional customer records or external workflow identifiers',()=>{
 for(const name of ['pages','page-map','architecture','publish-manifest','region-coverage','region-policy','site-config']){
  const text=JSON.stringify(read(name));assert.doesNotMatch(text,/안양|anyang|평택|pyeongtaek|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/);
 }
});
test('public ownership proof is unique and separate from prior site',()=>{
 const root=new URL('../public/',import.meta.url);const matches=fs.readdirSync(root).filter(n=>/^[0-9a-f]{32}\.txt$/.test(n));assert.equal(matches.length,1);
 assert.equal(fs.readFileSync(new URL(matches[0],root),'utf8').trim(),matches[0].slice(0,-4));
 assert.notEqual(matches[0],'3b41d9e91f04c1390fb4967e99f41bc6.txt');
});
test('only regional hub is emitted and all 14 normal routes are indexable',()=>{
 const pages=read('pages'),a=read('architecture');
 assert.deepEqual(a.hubs.filter(h=>h.indexable).map(h=>h.url),['/regions/']);
 assert.deepEqual(a.hubs.filter(h=>h.children>0).map(h=>h.url),['/regions/']);
 assert.equal(1+pages.length+a.hubs.filter(h=>h.children>0).length,14);
 assert.equal(read('publish-manifest').directRelease.publicationState,'source-reviewed-deployment-pending');
});

test('every reviewed four-variant comparison renders all four exact family products',()=>{
 const products=read('products');
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
 }
});

test('deferred Jail retains the original denominator and cannot become a customer route',()=>{
 const c=read('region-coverage'),m=read('publish-manifest'),p=read('pages');
 assert.equal(c.units.length,13);assert.equal(p.length,12);assert.equal(m.directRelease.plannedOriginalCount,13);
 assert.deepEqual(m.directRelease.deferredRoutes,['/regions/jail-dong/']);
 assert.equal(c.representatives.find(r=>r.slug==='jail-dong').status,'reserved');
 assert.ok(!p.some(p=>p.slug==='jail-dong'));assert.ok(p.every(p=>!p.relatedKeys.includes('uijeongbu-flower-direct-region-jail-dong')));
});
