import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const slugs=["cheonhyeon-dong", "hasangok-dong", "changu-dong", "baealmi-dong", "sangsangok-dong", "sinjang-dong", "dangjeong-dong", "deokpung-dong", "mangwol-dong", "pungsan-dong", "misa-dong", "seon-dong", "gambuk-dong", "gamil-dong", "gami-dong", "hagam-dong", "gyosan-dong", "chungung-dong", "hasachang-dong", "sangsachang-dong", "hang-dong", "choil-dong", "choi-dong", "gwangam-dong"];
test('Hanam frozen official legal and administrative membership has no duplicate canonical aliases',()=>{
 const pages=read('pages'),coverage=read('region-coverage');
 assert.deepEqual(pages.map(p=>p.slug),["cheonhyeon-dong", "hasangok-dong", "changu-dong", "baealmi-dong", "sangsangok-dong", "sinjang-dong", "deokpung-dong", "mangwol-dong", "pungsan-dong", "misa-dong", "seon-dong", "gambuk-dong", "gamil-dong", "gami-dong", "hagam-dong", "gyosan-dong", "chungung-dong", "hasachang-dong", "sangsachang-dong", "hang-dong", "choil-dong", "choi-dong", "gwangam-dong"]);assert.equal(coverage.units.length,24);assert.equal(coverage.administrativeCrosswalk.length,14);
 assert.equal(new Set(coverage.administrativeCrosswalk.map(a=>a.aliasKey)).size,14);
 assert.equal(coverage.districts.length,1);assert.equal(coverage.districts[0].name,'하남시');assert.equal(coverage.representatives.length,23);
 for(const p of pages){assert.equal(p.category,'regions');assert.equal(p.pageType,'regional-service');assert.equal(p.url,`/regions/${p.slug}/`);}
 const names=alias=>coverage.administrativeCrosswalk.find(a=>a.name===alias).relations.map(r=>coverage.units.find(u=>u.unitKey===r.unitKey).name).sort();
 for(const [admin,legal] of Object.entries({"감북동": ["감북동", "감일동", "광암동"], "감일동": ["감이동", "감일동"], "덕풍1동": ["덕풍동"], "덕풍2동": ["덕풍동"], "덕풍3동": ["덕풍동"], "미사1동": ["망월동", "미사동"], "미사2동": ["망월동", "선동"], "미사3동": ["풍산동"], "신장1동": ["신장동"], "신장2동": ["당정동", "신장동", "창우동"], "위례동": ["감이동", "학암동"], "천현동": ["배알미동", "상산곡동", "창우동", "천현동", "하산곡동"], "초이동": ["광암동", "초이동", "초일동"], "춘궁동": ["교산동", "상사창동", "춘궁동", "하사창동", "항동"]}))assert.deepEqual(names(admin),legal);
 for(const a of coverage.administrativeCrosswalk)for(const r of a.relations){const count=coverage.administrativeCrosswalk.filter(x=>x.relations.some(y=>y.unitKey===r.unitKey)).length;assert.equal(r.scope,count>1?'partial':'whole');}
 assert.ok(coverage.units.every(u=>u.unitKey.startsWith('하남시/법정동/')));
 assert.equal(coverage.units.length,slugs.length);
 assert.ok(pages.length*10>=slugs.length*9);
});
test('direct snapshot hashes bind every public customer field and all four page collections',()=>{
 const pages=read('pages'),manifest=read('publish-manifest');
 assert.equal(manifest.directRelease.sourceMode,'direct-git');assert.deepEqual(manifest.snapshotLedger,{});
 assert.equal(manifest.directRelease.plannedOriginalCount,24);assert.equal(manifest.directRelease.reviewedArticleCount,23);
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
  const value=read(name);const text=JSON.stringify(value).replaceAll('gyosan-dong','verified-hanam-legal-unit');assert.doesNotMatch(text,/의왕|uiwang|군포|gunpo|시흥|siheung|오산|osan|구리|guri|과천|gwacheon|동두천|dongducheon|광명시|gwangmyeong|의정부|uijeongbu|안양|anyang|평택|pyeongtaek|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/);
 }
});
test('public ownership proof is unique and separate from prior sites',()=>{
 const root=new URL('../public/',import.meta.url);const matches=fs.readdirSync(root).filter(n=>/^[0-9a-f]{32}\.txt$/.test(n));assert.equal(matches.length,1);
 assert.equal(fs.readFileSync(new URL(matches[0],root),'utf8').trim(),matches[0].slice(0,-4));
 assert.ok(!["12e5ff9bbb91144af0473171723b38be.txt","c8028cef3b87f4fecc2a9b7e371437d2.txt",'a63dfae2120ffef3d96bcfba24987a0e.txt','a63dfae2120ffef3d96bcfba24987a0e.txt','e30c4e1232b8f7c0e411afe25741fdb4.txt','3b41d9e91f04c1390fb4967e99f41bc6.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','5912b8b14ae0f13d37581a0545318989.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt'].includes(matches[0]));
});
test('only regional hub is emitted and all 25 normal routes are indexable',()=>{
 const pages=read('pages'),a=read('architecture'),m=read('publish-manifest');
 assert.deepEqual(a.hubs.filter(h=>h.indexable).map(h=>h.url),['/regions/']);
 assert.deepEqual(a.hubs.filter(h=>h.children>0).map(h=>h.url),['/regions/']);
 assert.equal(1+pages.length+a.hubs.filter(h=>h.children>0).length,25);
 assert.equal(m.directRelease.publicationState,'source-reviewed-deployment-pending');
 assert.deepEqual(m.directRelease.deferredRoutes,["/regions/dangjeong-dong/"]);assert.deepEqual(m.directRelease.publishedCoverage,{"numerator": 23, "denominator": 24, "percent": 95.83});
});
test('every reviewed four-variant comparison renders all four exact family products',()=>{
 const products=read('products');
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
 }
});
