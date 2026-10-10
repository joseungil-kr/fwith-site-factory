import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const slugs=["changjeon-dong", "gwango-dong", "jungni-dong", "jeungil-dong", "yulhyeon-dong", "jilli-dong", "anheung-dong", "galsan-dong", "jeungpo-dong", "songjeong-dong", "saeum-dong", "danwol-dong", "daepo-dong", "godam-dong", "jangnok-dong", "janghowon-eup", "bubal-eup", "sindun-myeon", "baeksa-myeon", "hobeop-myeon", "majang-myeon", "daewol-myeon", "moga-myeon", "seolseong-myeon", "yul-myeon"];
test('Icheon frozen official legal and administrative membership has no duplicate canonical aliases',()=>{
 const pages=read('pages'),coverage=read('region-coverage');
 assert.deepEqual(pages.map(p=>p.slug),["changjeon-dong", "gwango-dong", "jungni-dong", "jeungil-dong", "yulhyeon-dong", "jilli-dong", "anheung-dong", "galsan-dong", "jeungpo-dong", "songjeong-dong", "saeum-dong", "danwol-dong", "daepo-dong", "godam-dong", "jangnok-dong", "janghowon-eup", "bubal-eup", "sindun-myeon", "baeksa-myeon", "hobeop-myeon", "majang-myeon", "daewol-myeon", "moga-myeon", "seolseong-myeon", "yul-myeon"]);assert.equal(coverage.units.length,25);assert.equal(coverage.administrativeCrosswalk.length,14);
 assert.equal(new Set(coverage.administrativeCrosswalk.map(a=>a.aliasKey)).size,14);
 assert.equal(coverage.districts.length,1);assert.equal(coverage.districts[0].name,'이천시');assert.equal(coverage.representatives.length,25);
 for(const p of pages){assert.equal(p.category,'regions');assert.equal(p.pageType,'regional-service');assert.equal(p.url,`/regions/${p.slug}/`);}
 const names=alias=>coverage.administrativeCrosswalk.find(a=>a.name===alias).relations.map(r=>coverage.units.find(u=>u.unitKey===r.unitKey).name).sort();
 for(const [admin,legal] of Object.entries({"관고동": ["관고동", "사음동"], "대월면": ["대월면"], "마장면": ["마장면"], "모가면": ["모가면"], "백사면": ["백사면"], "부발읍": ["부발읍"], "설성면": ["설성면"], "신둔면": ["신둔면"], "율면": ["율면"], "장호원읍": ["장호원읍"], "중리동": ["고담동", "단월동", "대포동", "율현동", "장록동", "중리동", "증일동", "진리동"], "증포동": ["갈산동", "송정동", "안흥동", "증포동"], "창전동": ["창전동"], "호법면": ["호법면"]}))assert.deepEqual(names(admin),legal);
 for(const a of coverage.administrativeCrosswalk)for(const r of a.relations){const count=coverage.administrativeCrosswalk.filter(x=>x.relations.some(y=>y.unitKey===r.unitKey)).length;assert.equal(r.scope,count>1?'partial':'whole');}
 assert.ok(coverage.units.every(u=>u.unitKey===`이천시/${({'legal-dong':'법정동','eup':'읍','myeon':'면'})[u.unitType]}/${u.name}`));
 assert.deepEqual(Object.fromEntries(['legal-dong','eup','myeon'].map(type=>[type,coverage.units.filter(u=>u.unitType===type).length])),{'legal-dong':15,eup:2,myeon:8});
 assert.equal(coverage.administrativeCrosswalk.flatMap(a=>a.relations).length,25);
 assert.equal(coverage.units.length,slugs.length);
 assert.ok(pages.length*10>=slugs.length*9);
});
test('direct snapshot hashes bind every public customer field and all four page collections',()=>{
 const pages=read('pages'),manifest=read('publish-manifest');
 assert.equal(manifest.directRelease.sourceMode,'direct-git');assert.deepEqual(manifest.snapshotLedger,{});
 assert.equal(manifest.directRelease.plannedOriginalCount,25);assert.equal(manifest.directRelease.reviewedArticleCount,25);
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
 const normalizeIcheonRoad=text=>text.replaceAll('임오산로','verified-icheon-road');
 assert.doesNotMatch(normalizeIcheonRoad('경기도 이천시 율면 임오산로 296'),/오산|osan/);
 for(const donor of ['오산','오산시','osan','오산시 임오산로','osan 임오산로','임오산로 오산 꽃배달'])assert.match(normalizeIcheonRoad(donor),/오산|osan/);
 for(const name of ['pages','page-map','architecture','publish-manifest','region-coverage','region-policy','site-config']){
  const value=read(name);const text=normalizeIcheonRoad(JSON.stringify(value));assert.doesNotMatch(text,/파주|paju|하남|hanam|의왕|uiwang|군포|gunpo|시흥|siheung|오산|osan|구리|guri|과천|gwacheon|동두천|dongducheon|광명시|gwangmyeong|의정부|uijeongbu|안양|anyang|평택|pyeongtaek|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/);
 }
});
test('public ownership proof is unique and separate from prior sites',()=>{
 const root=new URL('../public/',import.meta.url);const matches=fs.readdirSync(root).filter(n=>/^[0-9a-f]{32}\.txt$/.test(n));assert.equal(matches.length,1);
 assert.equal(fs.readFileSync(new URL(matches[0],root),'utf8').trim(),matches[0].slice(0,-4));
 assert.ok(!["10f7d592a626faefa7e881533ccb1b44.txt","12e5ff9bbb91144af0473171723b38be.txt","c8028cef3b87f4fecc2a9b7e371437d2.txt",'a63dfae2120ffef3d96bcfba24987a0e.txt','a63dfae2120ffef3d96bcfba24987a0e.txt','e30c4e1232b8f7c0e411afe25741fdb4.txt','3b41d9e91f04c1390fb4967e99f41bc6.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','5912b8b14ae0f13d37581a0545318989.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt'].includes(matches[0]));
});
test('only regional hub is emitted and all 27 normal routes are indexable',()=>{
 const pages=read('pages'),a=read('architecture'),m=read('publish-manifest');
 assert.deepEqual(a.hubs.filter(h=>h.indexable).map(h=>h.url),['/regions/']);
 assert.deepEqual(a.hubs.filter(h=>h.children>0).map(h=>h.url),['/regions/']);
 assert.equal(1+pages.length+a.hubs.filter(h=>h.children>0).length,27);
 assert.equal(m.directRelease.publicationState,'source-reviewed-deployment-pending');
 assert.deepEqual(m.directRelease.deferredRoutes,[]);assert.deepEqual(m.directRelease.publishedCoverage,{"numerator": 25, "denominator": 25, "percent": 100.0});
});
test('every reviewed four-variant comparison renders all four exact family products',()=>{
 const products=read('products');
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
 }
});
