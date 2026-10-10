import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const slugs=["bukbyeon-dong", "geolpo-dong", "unyang-dong", "janggi-dong", "gamjeong-dong", "sau-dong", "pungmu-dong", "masan-dong", "gurae-dong", "tongjin-eup", "gochon-eup", "yangchon-eup", "daegot-myeon", "wolgot-myeon", "haseong-myeon"];
test('Gimpo frozen official legal and administrative membership has no duplicate canonical aliases',()=>{
 const pages=read('pages'),coverage=read('region-coverage');
 assert.deepEqual(pages.map(p=>p.slug),["bukbyeon-dong", "geolpo-dong", "unyang-dong", "janggi-dong", "gamjeong-dong", "sau-dong", "pungmu-dong", "masan-dong", "gurae-dong", "tongjin-eup", "gochon-eup", "yangchon-eup", "daegot-myeon", "wolgot-myeon"]);assert.equal(coverage.units.length,15);assert.equal(coverage.administrativeCrosswalk.length,14);
 assert.equal(new Set(coverage.administrativeCrosswalk.map(a=>a.aliasKey)).size,14);
 assert.equal(coverage.districts.length,1);assert.equal(coverage.districts[0].name,'김포시');assert.equal(coverage.representatives.length,14);
 for(const p of pages){assert.equal(p.category,'regions');assert.equal(p.pageType,'regional-service');assert.equal(p.url,`/regions/${p.slug}/`);}
 const names=alias=>coverage.administrativeCrosswalk.find(a=>a.name===alias).relations.map(r=>coverage.units.find(u=>u.unitKey===r.unitKey).name).sort();
 for(const [admin,legal] of Object.entries({"고촌읍": ["고촌읍"], "구래동": ["구래동"], "김포본동": ["감정동", "걸포동", "북변동"], "대곶면": ["대곶면"], "마산동": ["마산동"], "사우동": ["사우동"], "양촌읍": ["양촌읍"], "운양동": ["운양동"], "월곶면": ["월곶면"], "장기동": ["감정동", "장기동"], "장기본동": ["장기동"], "통진읍": ["통진읍"], "풍무동": ["풍무동"], "하성면": ["하성면"]}))assert.deepEqual(names(admin),legal);
 const actualRelations=coverage.administrativeCrosswalk.flatMap(a=>a.relations.map(r=>({administrativeDong:a.name,name:coverage.units.find(u=>u.unitKey===r.unitKey).name,coverage:r.scope}))); const relationKey=r=>`${r.administrativeDong}|${r.name}`; const sortRelations=values=>values.sort((a,b)=>relationKey(a)<relationKey(b)?-1:relationKey(a)>relationKey(b)?1:0); assert.deepEqual(sortRelations(actualRelations),sortRelations([{"administrativeDong": "고촌읍", "name": "고촌읍", "coverage": "whole"}, {"administrativeDong": "구래동", "name": "구래동", "coverage": "whole"}, {"administrativeDong": "김포본동", "name": "감정동", "coverage": "partial"}, {"administrativeDong": "김포본동", "name": "걸포동", "coverage": "whole"}, {"administrativeDong": "김포본동", "name": "북변동", "coverage": "whole"}, {"administrativeDong": "대곶면", "name": "대곶면", "coverage": "whole"}, {"administrativeDong": "마산동", "name": "마산동", "coverage": "whole"}, {"administrativeDong": "사우동", "name": "사우동", "coverage": "whole"}, {"administrativeDong": "양촌읍", "name": "양촌읍", "coverage": "whole"}, {"administrativeDong": "운양동", "name": "운양동", "coverage": "whole"}, {"administrativeDong": "월곶면", "name": "월곶면", "coverage": "whole"}, {"administrativeDong": "장기동", "name": "감정동", "coverage": "partial"}, {"administrativeDong": "장기동", "name": "장기동", "coverage": "partial"}, {"administrativeDong": "장기본동", "name": "장기동", "coverage": "partial"}, {"administrativeDong": "통진읍", "name": "통진읍", "coverage": "whole"}, {"administrativeDong": "풍무동", "name": "풍무동", "coverage": "whole"}, {"administrativeDong": "하성면", "name": "하성면", "coverage": "whole"}])); assert.equal(actualRelations.filter(r=>r.coverage==='partial').length,4);
 assert.ok(coverage.units.every(u=>u.unitKey===`김포시/${({'legal-dong':'법정동','eup':'읍','myeon':'면'})[u.unitType]}/${u.name}`));
 assert.deepEqual(Object.fromEntries(['legal-dong','eup','myeon'].map(type=>[type,coverage.units.filter(u=>u.unitType===type).length])),{'legal-dong':9,eup:3,myeon:3});
 assert.equal(coverage.administrativeCrosswalk.flatMap(a=>a.relations).length,17);
 assert.equal(coverage.units.length,slugs.length);
 assert.ok(pages.length*10>=slugs.length*9);
});
test('direct snapshot hashes bind every public customer field and all four page collections',()=>{
 const pages=read('pages'),manifest=read('publish-manifest');
 assert.equal(manifest.directRelease.sourceMode,'direct-git');assert.deepEqual(manifest.snapshotLedger,{});
 assert.equal(manifest.directRelease.plannedOriginalCount,15);assert.equal(manifest.directRelease.reviewedArticleCount,14);
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
  const value=read(name);const text=JSON.stringify(value);assert.doesNotMatch(text,/안성|anseong|이천|icheon|파주|paju|하남|hanam|의왕|uiwang|군포|gunpo|시흥|siheung|오산|osan|구리|guri|과천|gwacheon|동두천|dongducheon|광명시|gwangmyeong|의정부|uijeongbu|안양|anyang|평택|pyeongtaek|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/);
 }
});
test('public ownership proof is unique and separate from prior sites',()=>{
 const root=new URL('../public/',import.meta.url);const matches=fs.readdirSync(root).filter(n=>/^[0-9a-f]{32}\.txt$/.test(n));assert.equal(matches.length,1);
 assert.equal(fs.readFileSync(new URL(matches[0],root),'utf8').trim(),matches[0].slice(0,-4));
 assert.ok(!["571527e8fc99381afcffacc561788ea3.txt","f88ebdde7a59131c1904448c47829aea.txt","10f7d592a626faefa7e881533ccb1b44.txt","12e5ff9bbb91144af0473171723b38be.txt","c8028cef3b87f4fecc2a9b7e371437d2.txt",'a63dfae2120ffef3d96bcfba24987a0e.txt','a63dfae2120ffef3d96bcfba24987a0e.txt','e30c4e1232b8f7c0e411afe25741fdb4.txt','3b41d9e91f04c1390fb4967e99f41bc6.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','5912b8b14ae0f13d37581a0545318989.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt'].includes(matches[0]));
});
test('only regional hub is emitted and all 16 normal routes are indexable',()=>{
 const pages=read('pages'),a=read('architecture'),m=read('publish-manifest');
 assert.deepEqual(a.hubs.filter(h=>h.indexable).map(h=>h.url),['/regions/']);
 assert.deepEqual(a.hubs.filter(h=>h.children>0).map(h=>h.url),['/regions/']);
 assert.equal(1+pages.length+a.hubs.filter(h=>h.children>0).length,16);
 assert.equal(m.directRelease.publicationState,'source-reviewed-deployment-pending');
 assert.deepEqual(m.directRelease.deferredRoutes,["/regions/haseong-myeon/"]);assert.deepEqual(m.directRelease.publishedCoverage,{"numerator": 14, "denominator": 15, "percent": 93.33});
});
test('every reviewed four-variant comparison renders all four exact family products',()=>{
 const products=read('products');
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
 }
});
