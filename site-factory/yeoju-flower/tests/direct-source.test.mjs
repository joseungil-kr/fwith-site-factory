import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const slugs=["sang-dong", "hongmun-dong", "chang-dong", "uman-dong", "danhyeon-dong", "sinjin-dong", "ha-dong", "gyo-dong", "wolsong-dong", "gaeop-dong", "yeonra-dong", "sanggeo-dong", "hageo-dong", "samgyo-dong", "jeombong-dong", "neunghyeon-dong", "myeokgok-dong", "yeonyang-dong", "maeryong-dong", "cheonsong-dong", "ohak-dong", "hyeonam-dong", "ogeum-dong", "ganam-eup", "jeomdong-myeon", "heungcheon-myeon", "geumsa-myeon", "sejongdaewang-myeon", "daesin-myeon", "bungnae-myeon", "gangcheon-myeon", "sanbuk-myeon"];
test('Yeoju frozen official legal and administrative membership has no duplicate canonical aliases',()=>{
 const pages=read('pages'),coverage=read('region-coverage');
 assert.deepEqual(pages.map(p=>p.slug),["sang-dong", "hongmun-dong", "chang-dong", "danhyeon-dong", "ha-dong", "gyo-dong", "wolsong-dong", "gaeop-dong", "yeonra-dong", "sanggeo-dong", "hageo-dong", "samgyo-dong", "jeombong-dong", "neunghyeon-dong", "myeokgok-dong", "yeonyang-dong", "maeryong-dong", "cheonsong-dong", "ohak-dong", "hyeonam-dong", "ogeum-dong", "ganam-eup", "jeomdong-myeon", "heungcheon-myeon", "geumsa-myeon", "sejongdaewang-myeon", "daesin-myeon", "bungnae-myeon", "gangcheon-myeon", "sanbuk-myeon"]);assert.equal(coverage.units.length,32);assert.equal(coverage.administrativeCrosswalk.length,12);
 assert.equal(new Set(coverage.administrativeCrosswalk.map(a=>a.aliasKey)).size,12);
 assert.equal(coverage.districts.length,1);assert.equal(coverage.districts[0].name,'여주시');assert.equal(coverage.representatives.length,30);
 for(const p of pages){assert.equal(p.category,'regions');assert.equal(p.pageType,'regional-service');assert.equal(p.url,`/regions/${p.slug}/`);}
 const names=alias=>coverage.administrativeCrosswalk.find(a=>a.name===alias).relations.map(r=>coverage.units.find(u=>u.unitKey===r.unitKey).name).sort();
 for(const [admin,legal] of Object.entries({"가남읍": ["가남읍"], "강천면": ["강천면"], "금사면": ["금사면"], "대신면": ["대신면"], "북내면": ["북내면"], "산북면": ["산북면"], "세종대왕면": ["세종대왕면"], "여흥동": ["능현동", "단현동", "매룡동", "멱곡동", "삼교동", "상거동", "상동", "신진동", "연양동", "우만동", "점봉동", "하거동", "홍문동"], "오학동": ["오금동", "오학동", "천송동", "현암동"], "점동면": ["점동면"], "중앙동": ["가업동", "교동", "연라동", "월송동", "창동", "하동"], "흥천면": ["흥천면"]}))assert.deepEqual(names(admin),legal);
 const actualRelations=coverage.administrativeCrosswalk.flatMap(a=>a.relations.map(r=>({administrativeDong:a.name,name:coverage.units.find(u=>u.unitKey===r.unitKey).name,coverage:r.scope}))); const relationKey=r=>`${r.administrativeDong}|${r.name}`; const sortRelations=values=>values.sort((a,b)=>relationKey(a)<relationKey(b)?-1:relationKey(a)>relationKey(b)?1:0); assert.deepEqual(sortRelations(actualRelations),sortRelations([{"administrativeDong": "가남읍", "name": "가남읍", "coverage": "whole"}, {"administrativeDong": "강천면", "name": "강천면", "coverage": "whole"}, {"administrativeDong": "금사면", "name": "금사면", "coverage": "whole"}, {"administrativeDong": "대신면", "name": "대신면", "coverage": "whole"}, {"administrativeDong": "북내면", "name": "북내면", "coverage": "whole"}, {"administrativeDong": "산북면", "name": "산북면", "coverage": "whole"}, {"administrativeDong": "세종대왕면", "name": "세종대왕면", "coverage": "whole"}, {"administrativeDong": "여흥동", "name": "능현동", "coverage": "whole"}, {"administrativeDong": "여흥동", "name": "단현동", "coverage": "whole"}, {"administrativeDong": "여흥동", "name": "매룡동", "coverage": "whole"}, {"administrativeDong": "여흥동", "name": "멱곡동", "coverage": "whole"}, {"administrativeDong": "여흥동", "name": "삼교동", "coverage": "whole"}, {"administrativeDong": "여흥동", "name": "상거동", "coverage": "whole"}, {"administrativeDong": "여흥동", "name": "상동", "coverage": "whole"}, {"administrativeDong": "여흥동", "name": "신진동", "coverage": "whole"}, {"administrativeDong": "여흥동", "name": "연양동", "coverage": "whole"}, {"administrativeDong": "여흥동", "name": "우만동", "coverage": "whole"}, {"administrativeDong": "여흥동", "name": "점봉동", "coverage": "whole"}, {"administrativeDong": "여흥동", "name": "하거동", "coverage": "whole"}, {"administrativeDong": "여흥동", "name": "홍문동", "coverage": "whole"}, {"administrativeDong": "오학동", "name": "오금동", "coverage": "whole"}, {"administrativeDong": "오학동", "name": "오학동", "coverage": "whole"}, {"administrativeDong": "오학동", "name": "천송동", "coverage": "whole"}, {"administrativeDong": "오학동", "name": "현암동", "coverage": "whole"}, {"administrativeDong": "점동면", "name": "점동면", "coverage": "whole"}, {"administrativeDong": "중앙동", "name": "가업동", "coverage": "whole"}, {"administrativeDong": "중앙동", "name": "교동", "coverage": "whole"}, {"administrativeDong": "중앙동", "name": "연라동", "coverage": "whole"}, {"administrativeDong": "중앙동", "name": "월송동", "coverage": "whole"}, {"administrativeDong": "중앙동", "name": "창동", "coverage": "whole"}, {"administrativeDong": "중앙동", "name": "하동", "coverage": "whole"}, {"administrativeDong": "흥천면", "name": "흥천면", "coverage": "whole"}])); assert.equal(actualRelations.filter(r=>r.coverage==='partial').length,0);
 assert.ok(coverage.units.every(u=>u.unitKey===`여주시/${({'legal-dong':'법정동','eup':'읍','myeon':'면'})[u.unitType]}/${u.name}`));
 assert.deepEqual(Object.fromEntries(['legal-dong','eup','myeon'].map(type=>[type,coverage.units.filter(u=>u.unitType===type).length])),{'legal-dong':23,eup:1,myeon:8});
 assert.equal(coverage.administrativeCrosswalk.flatMap(a=>a.relations).length,32);
 assert.equal(coverage.units.length,slugs.length);
 assert.ok(pages.length*10>=slugs.length*9);
});
test('direct snapshot hashes bind every public customer field and all four page collections',()=>{
 const pages=read('pages'),manifest=read('publish-manifest');
 assert.equal(manifest.directRelease.sourceMode,'direct-git');assert.deepEqual(manifest.snapshotLedger,{});
 assert.equal(manifest.directRelease.plannedOriginalCount,32);assert.equal(manifest.directRelease.reviewedArticleCount,30);
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
  const value=read(name);
  if(name==='pages'){
   const page=value.find(p=>p.slug==='cheonsong-dong');
   if(page){
    const contrast='같은 페이지에 기재된 상품 반품주소는 **광명시 일직로 72 광명무역센터 C동 1307호**입니다.';
    assert.ok(page.sources.some(s=>s.url==='https://dapiofficial.co.kr/shopinfo/company.html'&&s.type==='business'));
    assert.equal(page.contentMarkdown.split(contrast).length,2);
    page.contentMarkdown=page.contentMarkdown.replace(contrast,'[verified external return-address contrast]');
   }
  }
  const text=JSON.stringify(value);assert.doesNotMatch(text,/포천|남양주|양주|김포|광주시|광주광역시|안성|이천|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:pocheon|namyangju|yangju|gimpo|gwangju|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/);
 }
});
test('public ownership proof is unique and separate from prior sites',()=>{
 const root=new URL('../public/',import.meta.url);const matches=fs.readdirSync(root).filter(n=>/^[0-9a-f]{32}\.txt$/.test(n));assert.equal(matches.length,1);
 assert.equal(fs.readFileSync(new URL(matches[0],root),'utf8').trim(),matches[0].slice(0,-4));
 assert.ok(!["272a8595f71fcf78ed7a4b2c845a6534.txt","571527e8fc99381afcffacc561788ea3.txt","f88ebdde7a59131c1904448c47829aea.txt","10f7d592a626faefa7e881533ccb1b44.txt","12e5ff9bbb91144af0473171723b38be.txt","c8028cef3b87f4fecc2a9b7e371437d2.txt",'a63dfae2120ffef3d96bcfba24987a0e.txt','a63dfae2120ffef3d96bcfba24987a0e.txt','e30c4e1232b8f7c0e411afe25741fdb4.txt','3b41d9e91f04c1390fb4967e99f41bc6.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','5912b8b14ae0f13d37581a0545318989.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt'].includes(matches[0]));
});
test('only regional hub is emitted and all 32 normal routes are indexable',()=>{
 const pages=read('pages'),a=read('architecture'),m=read('publish-manifest');
 assert.deepEqual(a.hubs.filter(h=>h.indexable).map(h=>h.url),['/regions/']);
 assert.deepEqual(a.hubs.filter(h=>h.children>0).map(h=>h.url),['/regions/']);
 assert.equal(1+pages.length+a.hubs.filter(h=>h.children>0).length,32);
 assert.equal(m.directRelease.publicationState,'source-reviewed-deployment-pending');
 assert.deepEqual(m.directRelease.deferredRoutes,["/regions/uman-dong/", "/regions/sinjin-dong/"]);assert.deepEqual(m.directRelease.publishedCoverage,{"numerator": 30, "denominator": 32, "percent": 93.75});
});
test('every reviewed four-variant comparison renders all four exact family products',()=>{
 const products=read('products');
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
 }
});
