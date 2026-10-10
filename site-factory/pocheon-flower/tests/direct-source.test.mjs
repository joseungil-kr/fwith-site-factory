import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const slugs=["sineup-dong", "eoryong-dong", "jajak-dong", "seondan-dong", "seolun-dong", "donggyo-dong", "soheul-eup", "gunnae-myeon", "naechon-myeon", "gasan-myeon", "sinbuk-myeon", "changsu-myeon", "yeongjung-myeon", "ildong-myeon", "idong-myeon", "yeongbuk-myeon", "gwanin-myeon", "hwahyeon-myeon"];
test('Pocheon frozen official legal and administrative membership has no duplicate canonical aliases',()=>{
 const pages=read('pages'),coverage=read('region-coverage');
 assert.deepEqual(pages.map(p=>p.slug),["sineup-dong", "eoryong-dong", "jajak-dong", "seondan-dong", "seolun-dong", "donggyo-dong", "soheul-eup", "gunnae-myeon", "naechon-myeon", "gasan-myeon", "sinbuk-myeon", "yeongjung-myeon", "ildong-myeon", "idong-myeon", "yeongbuk-myeon", "gwanin-myeon", "hwahyeon-myeon"]);assert.equal(coverage.units.length,18);assert.equal(coverage.administrativeCrosswalk.length,14);
 assert.equal(new Set(coverage.administrativeCrosswalk.map(a=>a.aliasKey)).size,14);
 assert.equal(coverage.districts.length,1);assert.equal(coverage.districts[0].name,'포천시');assert.equal(coverage.representatives.length,17);
 for(const p of pages){assert.equal(p.category,'regions');assert.equal(p.pageType,'regional-service');assert.equal(p.url,`/regions/${p.slug}/`);}
 const names=alias=>coverage.administrativeCrosswalk.find(a=>a.name===alias).relations.map(r=>coverage.units.find(u=>u.unitKey===r.unitKey).name).sort();
 for(const [admin,legal] of Object.entries({"가산면": ["가산면"], "관인면": ["관인면"], "군내면": ["군내면"], "내촌면": ["내촌면"], "선단동": ["동교동", "선단동", "설운동", "자작동"], "소흘읍": ["소흘읍"], "신북면": ["신북면"], "영북면": ["영북면"], "영중면": ["영중면"], "이동면": ["이동면"], "일동면": ["일동면"], "창수면": ["창수면"], "포천동": ["신읍동", "어룡동"], "화현면": ["화현면"]}))assert.deepEqual(names(admin),legal);
 const actualRelations=coverage.administrativeCrosswalk.flatMap(a=>a.relations.map(r=>({administrativeDong:a.name,name:coverage.units.find(u=>u.unitKey===r.unitKey).name,coverage:r.scope}))); const relationKey=r=>`${r.administrativeDong}|${r.name}`; const sortRelations=values=>values.sort((a,b)=>relationKey(a)<relationKey(b)?-1:relationKey(a)>relationKey(b)?1:0); assert.deepEqual(sortRelations(actualRelations),sortRelations([{"administrativeDong": "가산면", "name": "가산면", "coverage": "whole"}, {"administrativeDong": "관인면", "name": "관인면", "coverage": "whole"}, {"administrativeDong": "군내면", "name": "군내면", "coverage": "whole"}, {"administrativeDong": "내촌면", "name": "내촌면", "coverage": "whole"}, {"administrativeDong": "선단동", "name": "동교동", "coverage": "whole"}, {"administrativeDong": "선단동", "name": "선단동", "coverage": "whole"}, {"administrativeDong": "선단동", "name": "설운동", "coverage": "whole"}, {"administrativeDong": "선단동", "name": "자작동", "coverage": "whole"}, {"administrativeDong": "소흘읍", "name": "소흘읍", "coverage": "whole"}, {"administrativeDong": "신북면", "name": "신북면", "coverage": "whole"}, {"administrativeDong": "영북면", "name": "영북면", "coverage": "whole"}, {"administrativeDong": "영중면", "name": "영중면", "coverage": "whole"}, {"administrativeDong": "이동면", "name": "이동면", "coverage": "whole"}, {"administrativeDong": "일동면", "name": "일동면", "coverage": "whole"}, {"administrativeDong": "창수면", "name": "창수면", "coverage": "whole"}, {"administrativeDong": "포천동", "name": "신읍동", "coverage": "whole"}, {"administrativeDong": "포천동", "name": "어룡동", "coverage": "whole"}, {"administrativeDong": "화현면", "name": "화현면", "coverage": "whole"}])); assert.equal(actualRelations.filter(r=>r.coverage==='partial').length,0);
 assert.ok(coverage.units.every(u=>u.unitKey===`포천시/${({'legal-dong':'법정동','eup':'읍','myeon':'면'})[u.unitType]}/${u.name}`));
 assert.deepEqual(Object.fromEntries(['legal-dong','eup','myeon'].map(type=>[type,coverage.units.filter(u=>u.unitType===type).length])),{'legal-dong':6,eup:1,myeon:11});
 assert.equal(coverage.administrativeCrosswalk.flatMap(a=>a.relations).length,18);
 assert.equal(coverage.units.length,slugs.length);
 assert.ok(pages.length*10>=slugs.length*9);
});
test('direct snapshot hashes bind every public customer field and all four page collections',()=>{
 const pages=read('pages'),manifest=read('publish-manifest');
 assert.equal(manifest.directRelease.sourceMode,'direct-git');assert.deepEqual(manifest.snapshotLedger,{});
 assert.equal(manifest.directRelease.plannedOriginalCount,18);assert.equal(manifest.directRelease.reviewedArticleCount,17);
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
  const text=JSON.stringify(read(name));assert.doesNotMatch(text,/남양주|양주|김포|광주시|광주광역시|안성|이천|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:namyangju|yangju|gimpo|gwangju|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/);
 }
});
test('public ownership proof is unique and separate from prior sites',()=>{
 const root=new URL('../public/',import.meta.url);const matches=fs.readdirSync(root).filter(n=>/^[0-9a-f]{32}\.txt$/.test(n));assert.equal(matches.length,1);
 assert.equal(fs.readFileSync(new URL(matches[0],root),'utf8').trim(),matches[0].slice(0,-4));
 assert.ok(!["272a8595f71fcf78ed7a4b2c845a6534.txt","571527e8fc99381afcffacc561788ea3.txt","f88ebdde7a59131c1904448c47829aea.txt","10f7d592a626faefa7e881533ccb1b44.txt","12e5ff9bbb91144af0473171723b38be.txt","c8028cef3b87f4fecc2a9b7e371437d2.txt",'a63dfae2120ffef3d96bcfba24987a0e.txt','a63dfae2120ffef3d96bcfba24987a0e.txt','e30c4e1232b8f7c0e411afe25741fdb4.txt','3b41d9e91f04c1390fb4967e99f41bc6.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','5912b8b14ae0f13d37581a0545318989.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt'].includes(matches[0]));
});
test('only regional hub is emitted and all 19 normal routes are indexable',()=>{
 const pages=read('pages'),a=read('architecture'),m=read('publish-manifest');
 assert.deepEqual(a.hubs.filter(h=>h.indexable).map(h=>h.url),['/regions/']);
 assert.deepEqual(a.hubs.filter(h=>h.children>0).map(h=>h.url),['/regions/']);
 assert.equal(1+pages.length+a.hubs.filter(h=>h.children>0).length,19);
 assert.equal(m.directRelease.publicationState,'source-reviewed-deployment-pending');
 assert.deepEqual(m.directRelease.deferredRoutes,["/regions/changsu-myeon/"]);assert.deepEqual(m.directRelease.publishedCoverage,{"numerator": 17, "denominator": 18, "percent": 94.44});
});
test('every reviewed four-variant comparison renders all four exact family products',()=>{
 const products=read('products');
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
 }
});
