import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const slugs=["bongsan-dong", "sungin-dong", "yeong-dong", "bongnam-dong", "gupo-dong", "dongbon-dong", "myeongnyun-dong", "okcheon-dong", "nagwon-dong", "changjeon-dong", "seongnam-dong", "sinheung-dong", "inji-dong", "geumsan-dong", "yeonji-dong", "daecheon-dong", "seoin-dong", "seokjeong-dong", "ayang-dong", "geumseok-dong", "gye-dong", "oksan-dong", "sagok-dong", "dogi-dong", "dangwang-dong", "gasa-dong", "gahyeon-dong", "singeonji-dong", "sinsohyeon-dong", "sinmosan-dong", "hyeonsu-dong", "balhwa-dong", "jungni-dong", "gongdo-eup", "bogae-myeon", "geumgwang-myeon", "seoun-myeon", "miyang-myeon", "daedeok-myeon", "yangseong-myeon", "wongok-myeon", "iljuk-myeon", "juksan-myeon", "samjuk-myeon", "gosam-myeon"];
test('Anseong frozen official legal and administrative membership has no duplicate canonical aliases',()=>{
 const pages=read('pages'),coverage=read('region-coverage');
 assert.deepEqual(pages.map(p=>p.slug),["bongsan-dong", "sungin-dong", "yeong-dong", "bongnam-dong", "gupo-dong", "dongbon-dong", "myeongnyun-dong", "okcheon-dong", "nagwon-dong", "changjeon-dong", "seongnam-dong", "sinheung-dong", "inji-dong", "geumsan-dong", "yeonji-dong", "daecheon-dong", "seoin-dong", "seokjeong-dong", "ayang-dong", "geumseok-dong", "gye-dong", "oksan-dong", "sagok-dong", "dogi-dong", "dangwang-dong", "gasa-dong", "gahyeon-dong", "singeonji-dong", "sinsohyeon-dong", "sinmosan-dong", "hyeonsu-dong", "jungni-dong", "gongdo-eup", "bogae-myeon", "geumgwang-myeon", "seoun-myeon", "miyang-myeon", "daedeok-myeon", "yangseong-myeon", "wongok-myeon", "iljuk-myeon", "juksan-myeon", "samjuk-myeon", "gosam-myeon"]);assert.equal(coverage.units.length,45);assert.equal(coverage.administrativeCrosswalk.length,15);
 assert.equal(new Set(coverage.administrativeCrosswalk.map(a=>a.aliasKey)).size,15);
 assert.equal(coverage.districts.length,1);assert.equal(coverage.districts[0].name,'안성시');assert.equal(coverage.representatives.length,44);
 for(const p of pages){assert.equal(p.category,'regions');assert.equal(p.pageType,'regional-service');assert.equal(p.url,`/regions/${p.slug}/`);}
 const names=alias=>coverage.administrativeCrosswalk.find(a=>a.name===alias).relations.map(r=>coverage.units.find(u=>u.unitKey===r.unitKey).name).sort();
 for(const [admin,legal] of Object.entries({"고삼면": ["고삼면"], "공도읍": ["공도읍"], "금광면": ["금광면"], "대덕면": ["대덕면"], "미양면": ["미양면"], "보개면": ["보개면"], "삼죽면": ["삼죽면"], "서운면": ["서운면"], "안성1동": ["가사동", "가현동", "구포동", "낙원동", "동본동", "명륜동", "발화동", "봉남동", "봉산동", "성남동", "숭인동", "영동", "옥천동", "창전동", "현수동"], "안성2동": ["계동", "도기동", "서인동", "석정동", "신흥동", "아양동", "옥산동", "인지동", "중리동"], "안성3동": ["금산동", "금석동", "당왕동", "대천동", "사곡동", "신건지동", "신모산동", "신소현동", "연지동"], "양성면": ["양성면"], "원곡면": ["원곡면"], "일죽면": ["일죽면"], "죽산면": ["죽산면"]}))assert.deepEqual(names(admin),legal);
 for(const a of coverage.administrativeCrosswalk)for(const r of a.relations){const count=coverage.administrativeCrosswalk.filter(x=>x.relations.some(y=>y.unitKey===r.unitKey)).length;assert.equal(r.scope,count>1?'partial':'whole');}
 assert.ok(coverage.units.every(u=>u.unitKey===`안성시/${({'legal-dong':'법정동','eup':'읍','myeon':'면'})[u.unitType]}/${u.name}`));
 assert.deepEqual(Object.fromEntries(['legal-dong','eup','myeon'].map(type=>[type,coverage.units.filter(u=>u.unitType===type).length])),{'legal-dong':33,eup:1,myeon:11});
 assert.equal(coverage.administrativeCrosswalk.flatMap(a=>a.relations).length,45);
 assert.equal(coverage.units.length,slugs.length);
 assert.ok(pages.length*10>=slugs.length*9);
});
test('direct snapshot hashes bind every public customer field and all four page collections',()=>{
 const pages=read('pages'),manifest=read('publish-manifest');
 assert.equal(manifest.directRelease.sourceMode,'direct-git');assert.deepEqual(manifest.snapshotLedger,{});
 assert.equal(manifest.directRelease.plannedOriginalCount,45);assert.equal(manifest.directRelease.reviewedArticleCount,44);
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
 assert.ok(slugs.includes('sinmosan-dong'));
 const normalizeAnseongLegalSlug=text=>text.replaceAll('anseong-flower-direct-region-sinmosan-dong','verified-anseong-page-key').replace(/direct-content-sinmosan-dong-[a-f0-9]{16}/g,'verified-anseong-snapshot').replace(/(?<![a-z0-9-])sinmosan-dong(?![a-z0-9-])/g,'verified-anseong-legal-unit');
 assert.doesNotMatch(normalizeAnseongLegalSlug('/regions/sinmosan-dong/'),/오산|osan/);
 for(const donor of ['오산','오산시','osan','osan.fwith.kr','sinmosan-dong 오산 꽃배달','sinmosan-dong osan','prefix-sinmosan-dong'])assert.match(normalizeAnseongLegalSlug(donor),/오산|osan/);
 for(const name of ['pages','page-map','architecture','publish-manifest','region-coverage','region-policy','site-config']){
  const value=read(name);const text=normalizeAnseongLegalSlug(JSON.stringify(value));assert.doesNotMatch(text,/이천|icheon|파주|paju|하남|hanam|의왕|uiwang|군포|gunpo|시흥|siheung|오산|osan|구리|guri|과천|gwacheon|동두천|dongducheon|광명시|gwangmyeong|의정부|uijeongbu|안양|anyang|평택|pyeongtaek|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/);
 }
});
test('public ownership proof is unique and separate from prior sites',()=>{
 const root=new URL('../public/',import.meta.url);const matches=fs.readdirSync(root).filter(n=>/^[0-9a-f]{32}\.txt$/.test(n));assert.equal(matches.length,1);
 assert.equal(fs.readFileSync(new URL(matches[0],root),'utf8').trim(),matches[0].slice(0,-4));
 assert.ok(!["f88ebdde7a59131c1904448c47829aea.txt","10f7d592a626faefa7e881533ccb1b44.txt","12e5ff9bbb91144af0473171723b38be.txt","c8028cef3b87f4fecc2a9b7e371437d2.txt",'a63dfae2120ffef3d96bcfba24987a0e.txt','a63dfae2120ffef3d96bcfba24987a0e.txt','e30c4e1232b8f7c0e411afe25741fdb4.txt','3b41d9e91f04c1390fb4967e99f41bc6.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','5912b8b14ae0f13d37581a0545318989.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt','d1b2332b6ccd71de0129a2360bda9249.txt','03a3a58dae0eff6e73dbcfdd3b590699.txt'].includes(matches[0]));
});
test('only regional hub is emitted and all 46 normal routes are indexable',()=>{
 const pages=read('pages'),a=read('architecture'),m=read('publish-manifest');
 assert.deepEqual(a.hubs.filter(h=>h.indexable).map(h=>h.url),['/regions/']);
 assert.deepEqual(a.hubs.filter(h=>h.children>0).map(h=>h.url),['/regions/']);
 assert.equal(1+pages.length+a.hubs.filter(h=>h.children>0).length,46);
 assert.equal(m.directRelease.publicationState,'source-reviewed-deployment-pending');
 assert.deepEqual(m.directRelease.deferredRoutes,["/regions/balhwa-dong/"]);assert.deepEqual(m.directRelease.publishedCoverage,{"numerator": 44, "denominator": 45, "percent": 97.78});
});
test('every reviewed four-variant comparison renders all four exact family products',()=>{
 const products=read('products');
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
 }
});
