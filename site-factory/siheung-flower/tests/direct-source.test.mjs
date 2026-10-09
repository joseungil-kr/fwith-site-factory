import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const slugs=["daeya-dong", "sincheon-dong", "bangsan-dong", "po-dong", "misan-dong", "eunhaeng-dong", "anhyeon-dong", "maehwa-dong", "dochang-dong", "geumi-dong", "gwarim-dong", "gyesu-dong", "hwajeong-dong", "neunggok-dong", "hajung-dong", "hasang-dong", "gwangseok-dong", "murwang-dong", "sanhyeon-dong", "jonam-dong", "nongok-dong", "mokgam-dong", "geomo-dong", "gunja-dong", "janghyeon-dong", "janggok-dong", "wolgot-dong", "jeongwang-dong", "jugyul-dong", "mujinae-dong", "baegot-dong"];
test('Siheung frozen official legal and administrative membership has no duplicate canonical aliases',()=>{
 const pages=read('pages'),coverage=read('region-coverage');
 assert.deepEqual(pages.map(p=>p.slug),["daeya-dong", "sincheon-dong", "bangsan-dong", "po-dong", "misan-dong", "eunhaeng-dong", "anhyeon-dong", "maehwa-dong", "dochang-dong", "geumi-dong", "gwarim-dong", "gyesu-dong", "hwajeong-dong", "neunggok-dong", "hajung-dong", "hasang-dong", "gwangseok-dong", "murwang-dong", "sanhyeon-dong", "jonam-dong", "nongok-dong", "mokgam-dong", "geomo-dong", "gunja-dong", "janghyeon-dong", "janggok-dong", "wolgot-dong", "jeongwang-dong", "jugyul-dong", "mujinae-dong", "baegot-dong"]);assert.equal(coverage.units.length,31);assert.equal(coverage.administrativeCrosswalk.length,20);
 assert.equal(new Set(coverage.administrativeCrosswalk.map(a=>a.aliasKey)).size,20);
 assert.equal(coverage.districts.length,1);assert.equal(coverage.districts[0].name,'시흥시');assert.equal(coverage.representatives.length,31);
 for(const p of pages){assert.equal(p.category,'regions');assert.equal(p.pageType,'regional-service');assert.equal(p.url,`/regions/${p.slug}/`);}
 const names=alias=>coverage.administrativeCrosswalk.find(a=>a.name===alias).relations.map(r=>coverage.units.find(u=>u.unitKey===r.unitKey).name).sort();
 for(const [admin,legal] of Object.entries({"거북섬동": ["정왕동"], "과림동": ["과림동", "무지내동"], "군자동": ["거모동", "군자동"], "능곡동": ["광석동", "군자동", "능곡동", "장현동", "화정동"], "대야동": ["계수동", "대야동"], "매화동": ["금이동", "도창동", "매화동"], "목감동": ["논곡동", "목감동", "물왕동", "산현동", "조남동"], "배곧1동": ["배곧동"], "배곧2동": ["배곧동"], "신천동": ["신천동"], "신현동": ["미산동", "방산동", "포동"], "연성동": ["광석동", "장현동", "하상동", "하중동"], "월곶동": ["월곶동"], "은행동": ["안현동", "은행동"], "장곡동": ["장곡동", "장현동"], "정왕1동": ["정왕동"], "정왕2동": ["정왕동"], "정왕3동": ["정왕동"], "정왕4동": ["정왕동"], "정왕본동": ["정왕동", "죽율동"]}))assert.deepEqual(names(admin),legal);
 for(const a of coverage.administrativeCrosswalk)for(const r of a.relations){const count=coverage.administrativeCrosswalk.filter(x=>x.relations.some(y=>y.unitKey===r.unitKey)).length;assert.equal(r.scope,count>1?'partial':'whole');}
 assert.ok(coverage.units.every(u=>u.unitKey.startsWith('시흥시/법정동/')));
 assert.equal(coverage.units.length,slugs.length);
 assert.ok(pages.length*10>=slugs.length*9);
});
test('direct snapshot hashes bind every public customer field and all four page collections',()=>{
 const pages=read('pages'),manifest=read('publish-manifest');
 assert.equal(manifest.directRelease.sourceMode,'direct-git');assert.deepEqual(manifest.snapshotLedger,{});
 assert.equal(manifest.directRelease.plannedOriginalCount,31);assert.equal(manifest.directRelease.reviewedArticleCount,31);
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
  const value=read(name);const text=JSON.stringify(value);assert.doesNotMatch(text,/오산|osan|구리|guri|과천|gwacheon|동두천|dongducheon|광명시|gwangmyeong|의정부|uijeongbu|안양|anyang|평택|pyeongtaek|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/);
 }
});
test('public ownership proof is unique and separate from prior sites',()=>{
 const root=new URL('../public/',import.meta.url);const matches=fs.readdirSync(root).filter(n=>/^[0-9a-f]{32}\.txt$/.test(n));assert.equal(matches.length,1);
 assert.equal(fs.readFileSync(new URL(matches[0],root),'utf8').trim(),matches[0].slice(0,-4));
 assert.ok(!['a63dfae2120ffef3d96bcfba24987a0e.txt','e30c4e1232b8f7c0e411afe25741fdb4.txt','3b41d9e91f04c1390fb4967e99f41bc6.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','5912b8b14ae0f13d37581a0545318989.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt'].includes(matches[0]));
});
test('only regional hub is emitted and all 33 normal routes are indexable',()=>{
 const pages=read('pages'),a=read('architecture'),m=read('publish-manifest');
 assert.deepEqual(a.hubs.filter(h=>h.indexable).map(h=>h.url),['/regions/']);
 assert.deepEqual(a.hubs.filter(h=>h.children>0).map(h=>h.url),['/regions/']);
 assert.equal(1+pages.length+a.hubs.filter(h=>h.children>0).length,33);
 assert.equal(m.directRelease.publicationState,'source-reviewed-deployment-pending');
 assert.deepEqual(m.directRelease.deferredRoutes,[]);assert.deepEqual(m.directRelease.publishedCoverage,{"numerator": 31, "denominator": 31, "percent": 100.0});
});
test('every reviewed four-variant comparison renders all four exact family products',()=>{
 const products=read('products');
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
 }
});
