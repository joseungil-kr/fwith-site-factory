import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const slugs=["gyeongan-dong", "ssangnyeong-dong", "songjeong-dong", "hoedeok-dong", "tanbeol-dong", "mokhyeon-dong", "sam-dong", "jungdae-dong", "jik-dong", "taejeon-dong", "jangji-dong", "yeok-dong", "mok-dong", "gosan-dong", "sinhyeon-dong", "neungpyeong-dong", "munhyeong-dong", "chuja-dong", "maesan-dong", "yangbeol-dong", "chowol-eup", "gonjiam-eup", "docheok-myeon", "toechon-myeon", "namjong-myeon", "namhansanseong-myeon"];
test('Gwangju frozen official legal and administrative membership has no duplicate canonical aliases',()=>{
 const pages=read('pages'),coverage=read('region-coverage');
 assert.deepEqual(pages.map(p=>p.slug),["gyeongan-dong", "ssangnyeong-dong", "songjeong-dong", "hoedeok-dong", "tanbeol-dong", "sam-dong", "jungdae-dong", "jik-dong", "taejeon-dong", "jangji-dong", "yeok-dong", "mok-dong", "gosan-dong", "sinhyeon-dong", "neungpyeong-dong", "munhyeong-dong", "chuja-dong", "maesan-dong", "yangbeol-dong", "chowol-eup", "gonjiam-eup", "docheok-myeon", "toechon-myeon", "namjong-myeon", "namhansanseong-myeon"]);assert.equal(coverage.units.length,26);assert.equal(coverage.administrativeCrosswalk.length,16);
 assert.equal(new Set(coverage.administrativeCrosswalk.map(a=>a.aliasKey)).size,16);
 assert.equal(coverage.districts.length,1);assert.equal(coverage.districts[0].name,'광주시');assert.equal(coverage.representatives.length,25);
 for(const p of pages){assert.equal(p.category,'regions');assert.equal(p.pageType,'regional-service');assert.equal(p.url,`/regions/${p.slug}/`);}
 const names=alias=>coverage.administrativeCrosswalk.find(a=>a.name===alias).relations.map(r=>coverage.units.find(u=>u.unitKey===r.unitKey).name).sort();
 for(const [admin,legal] of Object.entries({"경안동": ["경안동", "역동"], "곤지암읍": ["곤지암읍"], "광남1동": ["목동", "삼동", "장지동", "중대동", "직동", "태전동"], "광남2동": ["태전동"], "남종면": ["남종면"], "남한산성면": ["남한산성면"], "능평동": ["능평동"], "도척면": ["도척면"], "송정동": ["송정동"], "신현동": ["신현동"], "쌍령동": ["쌍령동"], "오포1동": ["고산동", "문형동", "추자동"], "오포2동": ["매산동", "양벌동"], "초월읍": ["초월읍"], "탄벌동": ["목현동", "탄벌동", "회덕동"], "퇴촌면": ["퇴촌면"]}))assert.deepEqual(names(admin),legal);
 const actualRelations=coverage.administrativeCrosswalk.flatMap(a=>a.relations.map(r=>({administrativeDong:a.name,name:coverage.units.find(u=>u.unitKey===r.unitKey).name,coverage:r.scope}))); const relationKey=r=>`${r.administrativeDong}|${r.name}`; const sortRelations=values=>values.sort((a,b)=>relationKey(a)<relationKey(b)?-1:relationKey(a)>relationKey(b)?1:0); assert.deepEqual(sortRelations(actualRelations),sortRelations([{"administrativeDong": "경안동", "name": "경안동", "coverage": "whole"}, {"administrativeDong": "경안동", "name": "역동", "coverage": "whole"}, {"administrativeDong": "곤지암읍", "name": "곤지암읍", "coverage": "whole"}, {"administrativeDong": "광남1동", "name": "목동", "coverage": "whole"}, {"administrativeDong": "광남1동", "name": "삼동", "coverage": "whole"}, {"administrativeDong": "광남1동", "name": "장지동", "coverage": "whole"}, {"administrativeDong": "광남1동", "name": "중대동", "coverage": "whole"}, {"administrativeDong": "광남1동", "name": "직동", "coverage": "whole"}, {"administrativeDong": "광남1동", "name": "태전동", "coverage": "partial"}, {"administrativeDong": "광남2동", "name": "태전동", "coverage": "partial"}, {"administrativeDong": "남종면", "name": "남종면", "coverage": "whole"}, {"administrativeDong": "남한산성면", "name": "남한산성면", "coverage": "whole"}, {"administrativeDong": "능평동", "name": "능평동", "coverage": "whole"}, {"administrativeDong": "도척면", "name": "도척면", "coverage": "whole"}, {"administrativeDong": "송정동", "name": "송정동", "coverage": "whole"}, {"administrativeDong": "신현동", "name": "신현동", "coverage": "whole"}, {"administrativeDong": "쌍령동", "name": "쌍령동", "coverage": "whole"}, {"administrativeDong": "오포1동", "name": "고산동", "coverage": "whole"}, {"administrativeDong": "오포1동", "name": "문형동", "coverage": "whole"}, {"administrativeDong": "오포1동", "name": "추자동", "coverage": "whole"}, {"administrativeDong": "오포2동", "name": "매산동", "coverage": "whole"}, {"administrativeDong": "오포2동", "name": "양벌동", "coverage": "whole"}, {"administrativeDong": "초월읍", "name": "초월읍", "coverage": "whole"}, {"administrativeDong": "탄벌동", "name": "목현동", "coverage": "whole"}, {"administrativeDong": "탄벌동", "name": "탄벌동", "coverage": "whole"}, {"administrativeDong": "탄벌동", "name": "회덕동", "coverage": "whole"}, {"administrativeDong": "퇴촌면", "name": "퇴촌면", "coverage": "whole"}])); assert.equal(actualRelations.filter(r=>r.coverage==='partial').length,2);
 assert.ok(coverage.units.every(u=>u.unitKey===`광주시/${({'legal-dong':'법정동','eup':'읍','myeon':'면'})[u.unitType]}/${u.name}`));
 assert.deepEqual(Object.fromEntries(['legal-dong','eup','myeon'].map(type=>[type,coverage.units.filter(u=>u.unitType===type).length])),{'legal-dong':20,eup:2,myeon:4});
 assert.equal(coverage.administrativeCrosswalk.flatMap(a=>a.relations).length,27);
 assert.equal(coverage.units.length,slugs.length);
 assert.ok(pages.length*10>=slugs.length*9);
});
test('direct snapshot hashes bind every public customer field and all four page collections',()=>{
 const pages=read('pages'),manifest=read('publish-manifest');
 assert.equal(manifest.directRelease.sourceMode,'direct-git');assert.deepEqual(manifest.snapshotLedger,{});
 assert.equal(manifest.directRelease.plannedOriginalCount,26);assert.equal(manifest.directRelease.reviewedArticleCount,25);
 for(const p of pages){
  const omit=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);
  const digest=sha(canonical(Object.fromEntries(Object.entries(p).filter(([k])=>!omit.has(k)))));
  assert.equal(p.snapshotHash,digest);assert.equal(p.snapshotId,`direct-content-${p.slug}-${digest.slice(0,16)}`);
  const row=manifest.directRelease.contentHashes.find(x=>x.pageKey===p.pageKey);
  assert.equal(row.publicSourceSha256,digest);assert.equal(row.bodySha256,sha(p.contentMarkdown));
  for(const c of [manifest,read('page-map'),read('architecture')])assert.equal(c.pages.find(x=>x.pageKey===p.pageKey).snapshotHash,digest);
 }
});
// BEGIN TARGET_CONTAMINATION_GUARD
function assertNoCopiedRegionalRecords(name,value){
 const inspected=structuredClone(value);
 if(name==='pages'){
  const contrasts=inspected.filter(p=>p.slug==='jik-dong');assert.ok(contrasts.length<=1);
  if(contrasts.length){
   const page=contrasts[0];assert.equal(page.pageKey,'gwangju-flower-direct-region-jik-dong');
   assert.deepEqual(page.regionUnitKeys,['광주시/법정동/직동']);
   for(const [name,url] of [['경동하이테크 연혁 및 사업장 안내','https://www.kdhitech.com/myboard/history'],['경동하이테크 오시는길','https://www.kdhitech.com/page/map_01']]){
    assert.equal(page.sources.filter(s=>s.name===name&&s.url===url&&s.type==='business'&&s.verifiedAt==='2026-10-10').length,1);
   }
   const clauses=['경동하이테크 공식 연혁에는 2026년 본사를 이천시로 이전한 내용이 있고, 사업장 안내에는 광주사무실을 경기도 광주시 고불로 377, 직동으로 따로 표시합니다.','초청장에는 직동, 회사 소개에는 이천이 나온다면 받는 사람에게 행사 장소를 짧게 되물으세요.'];
   assert.equal((page.contentMarkdown.match(/이천/g)||[]).length,2);
   for(const clause of clauses){assert.equal(page.contentMarkdown.split(clause).length-1,1);page.contentMarkdown=page.contentMarkdown.replace(clause,clause.replace('이천','[검증된 타지역 사업장]'));}
  }
 }
 const text=JSON.stringify(inspected);
 assert.doesNotMatch(text,/김포|광주광역시|안성|이천|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:gimpo|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/);
}
// END TARGET_CONTAMINATION_GUARD
test('source contains no copied regional customer records or external workflow identifiers',()=>{
 for(const name of ['pages','page-map','architecture','publish-manifest','region-coverage','region-policy','site-config'])assertNoCopiedRegionalRecords(name,read(name));
});
test('public ownership proof is unique and separate from prior sites',()=>{
 const root=new URL('../public/',import.meta.url);const matches=fs.readdirSync(root).filter(n=>/^[0-9a-f]{32}\.txt$/.test(n));assert.equal(matches.length,1);
 assert.equal(fs.readFileSync(new URL(matches[0],root),'utf8').trim(),matches[0].slice(0,-4));
 assert.ok(!["272a8595f71fcf78ed7a4b2c845a6534.txt","571527e8fc99381afcffacc561788ea3.txt","f88ebdde7a59131c1904448c47829aea.txt","10f7d592a626faefa7e881533ccb1b44.txt","12e5ff9bbb91144af0473171723b38be.txt","c8028cef3b87f4fecc2a9b7e371437d2.txt",'a63dfae2120ffef3d96bcfba24987a0e.txt','a63dfae2120ffef3d96bcfba24987a0e.txt','e30c4e1232b8f7c0e411afe25741fdb4.txt','3b41d9e91f04c1390fb4967e99f41bc6.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','5912b8b14ae0f13d37581a0545318989.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt'].includes(matches[0]));
});
test('only regional hub is emitted and all 27 normal routes are indexable',()=>{
 const pages=read('pages'),a=read('architecture'),m=read('publish-manifest');
 assert.deepEqual(a.hubs.filter(h=>h.indexable).map(h=>h.url),['/regions/']);
 assert.deepEqual(a.hubs.filter(h=>h.children>0).map(h=>h.url),['/regions/']);
 assert.equal(1+pages.length+a.hubs.filter(h=>h.children>0).length,27);
 assert.equal(m.directRelease.publicationState,'source-reviewed-deployment-pending');
 assert.deepEqual(m.directRelease.deferredRoutes,["/regions/mokhyeon-dong/"]);assert.deepEqual(m.directRelease.publishedCoverage,{"numerator": 25, "denominator": 26, "percent": 96.15});
});
test('every reviewed four-variant comparison renders all four exact family products',()=>{
 const products=read('products');
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
 }
});
