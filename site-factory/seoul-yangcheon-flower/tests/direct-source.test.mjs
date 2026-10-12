import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';
import {validateGraph,loadGraph} from '../scripts/qa_graph.mjs';
import {pageSources} from '../src/lib/sources.mjs';
import {validateDefinition,directoryGroups} from '../src/lib/regions.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const expected=JSON.parse(fs.readFileSync(new URL('./direct-source-expectations.json',import.meta.url),'utf8'));







const priorRegionPattern=/마포구|seoul-mapo|서대문구|seodaemun|은평구|eunpyeong|노원구|nowon|강북구|gangbuk|도봉구|dobong|성북구|seongbuk|동대문구|dongdaemun|중랑구|jungnang|광진구|gwangjin|성동구|seongdong|용산구|yongsan|중구|seoul-jung(?!nang)|종로|jongno|양평|yangpyeong|가평|연천|(?<![가-힣])여주|포천|남양주|양주|김포|광주시|광주광역시|안성|이천(?!리)|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:gapyeong|yeoncheon|yeoju|pocheon|namyangju|yangju|gimpo|gwangju|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/;
test('Seoul Yangcheon-gu complete official membership stays separate from frozen purchase-intent N',()=>{
 const pages=read('pages'),c=read('region-coverage'),policy=read('region-policy');
 assert.deepEqual(pages.map(p=>p.slug),expected.approved);
 assert.deepEqual(c.units.map(u=>u.unitKey),expected.unitKeys);
 assert.deepEqual(c.administrativeCrosswalk,expected.administrativeCrosswalk);
 assert.equal(c.membershipSourceSha256,expected.membershipSourceSha256);
 assert.equal(c.units.length,expected.membershipCounts.legal);assert.equal(c.administrativeCrosswalk.length,expected.membershipCounts.administrative);
 assert.equal(c.representatives.length,expected.slugs.length);
 assert.equal(c.districts.length,1);assert.equal(c.districts[0].name,'양천구');
 assert.equal(new Set(c.administrativeCrosswalk.map(a=>a.aliasKey)).size,expected.membershipCounts.administrative);
 const relations=c.administrativeCrosswalk.flatMap(a=>a.relations);
 assert.equal(relations.length,expected.membershipCounts.relations);assert.equal(relations.filter(r=>r.scope==='partial').length,expected.partialRelationCount);
 const mixed=new Set(expected.partialUnitKeys);
 assert.ok(relations.every(r=>r.scope===(mixed.has(r.unitKey)?'partial':'whole')));
 assert.deepEqual(Object.fromEntries(['legal-dong','eup','myeon'].map(t=>[t,c.units.filter(u=>u.unitType===t).length])),expected.unitTypeCounts);
 assert.deepEqual(c.representatives.map(r=>r.slug),expected.slugs);
 assert.deepEqual(c.representatives.map(r=>r.unitKeys),expected.plannedUnitKeys.map(k=>[k]));
 assert.equal(new Set(c.representatives.flatMap(r=>r.unitKeys)).size,expected.plannedDistinctUnitCount);
 assert.deepEqual(c.representatives.filter(r=>r.status==='approved').map(r=>r.slug),expected.approved);
 assert.deepEqual(c.representatives.filter(r=>r.status==='reserved').map(r=>r.slug),expected.held);
 assert.ok(pages.length*10>=expected.slugs.length*9);
 assert.doesNotThrow(()=>validateDefinition(c,policy));
 for(const p of pages){assert.equal(p.category,'regions');assert.equal(p.pageType,'regional-service');assert.equal(p.url,`/regions/${p.slug}/`);}
});
test('review-bound regional validator permits unrepresented membership but rejects fake or duplicate identities',()=>{
 const c=read('region-coverage'),p=read('region-policy');
 assert.equal(sha(fs.readFileSync(new URL('../src/lib/regions.mjs',import.meta.url))),expected.runtimeRegionsSha256);
 assert.doesNotThrow(()=>validateDefinition({...structuredClone(c),representatives:[]},p));
 const duplicate=structuredClone(c);duplicate.representatives[1].unitKeys=duplicate.representatives[0].unitKeys;
 if(expected.representativeAssignment){for(const key of ['facilityKey','purchaseIntentKey','contextKey','intentKey'])duplicate.representatives[1][key]=duplicate.representatives[0][key];}
 assert.throws(()=>validateDefinition(duplicate,p),expected.representativeAssignment?/duplicate.*(?:intentKey|context)/:/duplicate\/unknown canonical unit/);
 const unknown=structuredClone(c);unknown.representatives[0].unitKeys=['unverified/unknown'];
 assert.throws(()=>validateDefinition(unknown,p),/canonical unit|unit mismatch/);
 const invalidRelation=structuredClone(c);invalidRelation.administrativeCrosswalk[0].relations[0].scope='guessed';
 assert.throws(()=>validateDefinition(invalidRelation,p),/invalid alias relation/);
 const quota=structuredClone(c);quota.countIsPageQuota=true;
 assert.throws(()=>validateDefinition(quota,p),/unsupported unit basis or quota/);
});
test('directory links only reviewed planned articles and retains an honest unwritten membership state',()=>{
 const c=read('region-coverage'),p=read('region-policy'),a=read('architecture'),pages=read('pages');
 const groups=directoryGroups(pages,a,c,p),entries=groups.flatMap(d=>d.items);
 assert.deepEqual(entries.map(e=>e.page.slug),expected.approved);
 assert.equal(new Set(entries.flatMap(e=>e.representative.unitKeys)).size,expected.approvedDistinctUnitCount);
 for(const entry of entries)assert.deepEqual(entry.page.regionUnitKeys,entry.representative.unitKeys);
 const source=fs.readFileSync(new URL('../src/components/RegionDirectory.astro',import.meta.url),'utf8');
 assert.match(source,/개별 안내 준비 중/);assert.match(source,/개별 주문 안내는 준비된 곳만 연결하며, 배송 가능 여부는 실제 주소로 상담해 주세요/);
 assert.match(source,/법정동 \{coverage.units.length\}개와 행정동 \{coverage.administrativeCrosswalk.length\}개/);assert.match(source,/relation.scope==='partial'/);
 assert.doesNotMatch(source,/양평|읍·면별/);
});
test('direct hashes bind every public customer field and all four collections',()=>{
 const pages=read('pages'),manifest=read('publish-manifest');
 assert.equal(manifest.directRelease.sourceMode,'direct-git');assert.deepEqual(manifest.snapshotLedger,{});
 assert.equal(manifest.directRelease.plannedOriginalCount,expected.slugs.length);assert.equal(manifest.directRelease.reviewedArticleCount,expected.approved.length);
 for(const p of pages){
  const omit=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);
  const digest=sha(canonical(Object.fromEntries(Object.entries(p).filter(([k])=>!omit.has(k)))));
  assert.equal(p.snapshotHash,digest);assert.equal(p.snapshotId,`direct-content-${p.slug}-${digest.slice(0,16)}`);
  const row=manifest.directRelease.contentHashes.find(x=>x.pageKey===p.pageKey);
  assert.equal(row.publicSourceSha256,digest);assert.equal(row.bodySha256,sha(p.contentMarkdown));
  for(const c of [manifest,read('page-map'),read('architecture')])assert.equal(c.pages.find(x=>x.pageKey===p.pageKey).snapshotHash,digest);
 }
});
test('customer collections contain no copied regional customer records or workflow identifiers',()=>{
 for(const name of ['pages','page-map','architecture','publish-manifest','region-coverage','region-policy','site-config','direct-checkpoint']){
  const data=read(name);
  if(name==='region-coverage'){
   // Frozen research may explicitly disambiguate similarly named external facilities.
   // Bind that evidence exactly rather than misclassifying it as copied customer copy.
   for(const row of data.representatives){assert.deepEqual(row.queryEvidence,expected.queryEvidenceBySlug[row.slug]);delete row.queryEvidence;}
  }
  assert.doesNotMatch(JSON.stringify(data),priorRegionPattern);
 }
});
test('Seoul Yangcheon-gu customer wording is allowed while copied prior-site names remain rejected',()=>{
 assert.doesNotMatch('서울 양천구 주문 안내',priorRegionPattern);
 assert.doesNotMatch('상품을 보여주는 사진',priorRegionPattern);
 assert.doesNotMatch('https://seoul-yangcheon.fwith.kr/',priorRegionPattern);
 for(const copied of ['서대문구','https://seoul-seodaemun.fwith.kr/','강북구','도봉구','https://seoul-gangbuk.fwith.kr/','https://seoul-dobong.fwith.kr/','https://seoul-jung.fwith.kr/','https://seoul-jungnang.fwith.kr/','중랑구','서울 중구','동대문구','seoul-dongdaemun'])assert.match(copied,priorRegionPattern);
 for(const copied of ['양평군 꽃배달','https://yangpyeong.fwith.kr/','가평군 꽃배달','https://gapyeong.fwith.kr/','여주시 꽃배달','여주 꽃배달','이천시 꽃배달','이천 꽃배달','https://icheon.fwith.kr/regions/example/','연천군 꽃배달','https://yeoju.fwith.kr/'])
  assert.match(copied,priorRegionPattern);
});
test('public ownership proof is unique and specific to this source',()=>{
 const root=new URL('../public/',import.meta.url);const matches=fs.readdirSync(root).filter(n=>/^[0-9a-f]{32}\.txt$/.test(n));
 assert.deepEqual(matches,[expected.proofFile]);assert.notEqual(matches[0],"cefb94457c510a65e3052f70bf843a5e.txt");assert.notEqual(matches[0],'29a79c8ebd0e44a9c81400fd74a93cbc.txt');assert.notEqual(matches[0],'dc766c6c4235b6ffe33d9f7efebc9a77.txt');
 assert.equal(fs.readFileSync(new URL(matches[0],root),'utf8'),matches[0].slice(0,-4)+'\n');
});
test('only approved articles and the regional hub are normal indexable routes',()=>{
 const pages=read('pages'),a=read('architecture'),m=read('publish-manifest');
 assert.deepEqual(a.hubs.filter(h=>h.indexable).map(h=>h.url),['/regions/']);
 assert.deepEqual(a.hubs.filter(h=>h.children>0).map(h=>h.url),['/regions/']);
 assert.equal(1+pages.length+a.hubs.filter(h=>h.children>0).length,expected.approved.length+2);
 assert.equal(m.directRelease.publicationState,'source-reviewed-deployment-pending');
 assert.deepEqual(m.directRelease.deferredRoutes,expected.held.map(s=>`/regions/${s}/`));
 assert.deepEqual(m.directRelease.publishedCoverage,{numerator:expected.approved.length,denominator:expected.slugs.length,percent:Math.round(expected.approved.length/expected.slugs.length*1000000)/10000});
 for(const p of pages){for(const slug of expected.held)assert.ok(!JSON.stringify(p).includes(`/regions/${slug}/`));}
});
function assertDeliveryNoticeVisible(markdown,notice,cardsSource){
 assert.match([markdown,notice].join(' '),/추가 배송비|추가배송비|배송비/);
 assert.ok(cardsSource.includes('{site.deliveryNotice}'),'delivery notice must remain rendered by every product group');
}
test('shared delivery notice rejects removal of both notice text or the rendering binding',()=>{
 const notice=read('business-truth').deliveryNotice;
 const cards=fs.readFileSync(new URL('../src/components/ProductCards.astro',import.meta.url),'utf8');
 assert.doesNotThrow(()=>assertDeliveryNoticeVisible('',notice,cards));
 assert.throws(()=>assertDeliveryNoticeVisible('안내',notice.replace(/배송비/g,'비용'),cards));
 assert.throws(()=>assertDeliveryNoticeVisible('추가 배송비 상담',notice,cards.replace('{site.deliveryNotice}','')));
});
test('every reviewed comparison renders four exact family products and truthful delivery surcharge',()=>{
 const products=read('products'),proof=read('social-image-provenance');
 assert.equal(proof.assetSource,'fresh-same-sku-official-gallery');assert.equal(proof.assetSubstitutionManifestSha256,expected.assetManifestSha256);
 for(const asset of expected.assetSubstitutions){
  const p=products.find(p=>p.key===asset.key),row=proof.products.find(p=>p.key===asset.key);
  assert.equal(p.officialSku,asset.sku);assert.equal(p.img,asset.imagePath);assert.equal(p.sourceImageUrl,asset.sourceImageUrl);
  assert.equal(sha(fs.readFileSync(new URL('../public'+asset.imagePath,import.meta.url))),asset.imageSha256);
  assert.equal(row.image.sha256,asset.imageSha256);assert.equal(row.sourceImageUrl,asset.sourceImageUrl);assert.equal(row.sourceImageHttpStatus,200);
  assert.deepEqual(row.image.dimensions,asset.dimensions);assert.equal(row.image.type,asset.mimeType);assert.equal(row.previousImageSha256,asset.previousImageSha256);
  assert.equal(p.desc,expected.reviewedProductDescriptions[p.officialSku]);
 }
 assert.match(read('business-truth').deliveryNotice,/실제 배송지 주소.*추가 배송비.*최종 결제금액.*주문 전에.*확인/);
 const cardsSource=fs.readFileSync(new URL('../src/components/ProductCards.astro',import.meta.url),'utf8');
 assert.ok(cardsSource.includes('{site.deliveryNotice}'),'shared price/delivery notice must render with every product group');
 assert.doesNotMatch(read('business-truth').deliveryNotice,/양평|단월|양서|10,000원|무료/);
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
  assertDeliveryNoticeVisible(p.contentMarkdown,read('business-truth').deliveryNotice,cardsSource);
 }
});
test('complete assembled graph and reviewed HTTPS source arrays pass unchanged shared validators',()=>{
 assert.equal(validateGraph(loadGraph()).pages,expected.approved.length);
 for(const p of read('pages'))assert.deepEqual(pageSources(p),p.sources);
});


test('frozen facility context registry and bindings remain exact across all customer collections',()=>{
 const c=read('region-coverage'),policy=read('region-policy'),pages=read('pages'),m=read('publish-manifest'),a=read('architecture'),pm=read('page-map');
 assert.equal(c.representativeAssignment??null,expected.representativeAssignment);
 assert.equal(policy.representativeAssignment??null,expected.representativeAssignment);
 assert.deepEqual(c.facilities??[],expected.facilities);
 assert.equal(m.directRelease.officialMembership.plannedRepresentedUnits,expected.plannedDistinctUnitCount);
 assert.equal(m.directRelease.officialMembership.unrepresentedUnits,c.units.length-expected.plannedDistinctUnitCount);
 if(!expected.representativeAssignment)return;
 for(const r of c.representatives){
  const binding=expected.contextBySlug[r.slug];
  for(const key of ['facilityKey','purchaseIntentKey','contextKey','intentKey'])assert.equal(r[key],binding[key]);
  assert.equal(r.contextKey,`${r.facilityKey}|${r.purchaseIntentKey}`);
  assert.equal(r.intentKey,`seoul-yangcheon|${r.contextKey}`);
  const facility=c.facilities.find(f=>f.facilityKey===r.facilityKey);assert.ok(facility);assert.deepEqual(r.unitKeys,[facility.unitKey]);
  if(r.status!=='approved')continue;
  for(const rows of [pages,m.pages,a.pages,pm.pages]){const page=rows.find(p=>p.pageKey===r.pageKey);assert.ok(page);for(const key of ['facilityKey','purchaseIntentKey','contextKey','intentKey'])assert.equal(page[key],binding[key]);assert.deepEqual(page.regionUnitKeys,r.unitKeys);}
 }
});

test('Yangcheon common purchase copy leads with purpose and choice while keeping delivery limits',()=>{
 const home=fs.readFileSync(new URL('../src/pages/index.astro',import.meta.url),'utf8');
 const directory=fs.readFileSync(new URL('../src/components/RegionDirectory.astro',import.meta.url),'utf8');
 const banner=fs.readFileSync(new URL('../src/components/InlineOrderBanner.astro',import.meta.url),'utf8');
 const truth=read('business-truth');
 assert.ok(home.includes(expected.reviewedCommon.home.heroParagraph));assert.match(home,/예산에 맞는 화환/);
 assert.ok(directory.includes(expected.reviewedCommon.regionDirectory.intro));assert.doesNotMatch(directory,/작성되었다는 뜻이 아닙니다/);
 assert.match(banner,/상품 선택이 어려우시면/);assert.match(banner,/상담시간과 실제 전달시간은 다를 수 있어요/); for(const term of ['전달 일정','반입 조건','추가비용','주문할 때 함께 확인'])assert.ok(banner.includes(term));
 for(const term of ['기본가격','추가 배송비','배송·반입 가능 여부','요청 시간','최종 결제금액','주문 전'])assert.ok(truth.deliveryNotice.includes(term));
});

test('independently reviewed shared customer copy stays exact in generated sources',()=>{
 for(const [name,digest] of Object.entries(expected.commonSourceSha256))assert.equal(sha(fs.readFileSync(new URL('../'+name,import.meta.url))),digest,name);
 const detail=fs.readFileSync(new URL('../src/pages/[category]/[slug].astro',import.meta.url),'utf8');
 const cards=fs.readFileSync(new URL('../src/components/ProductCards.astro',import.meta.url),'utf8');
 for(const field of ['{source.name}','sourceTypeLabels[source.type as keyof typeof sourceTypeLabels]','href={source.url}','datetime={source.verifiedAt}'])assert.ok(detail.includes(field),field);
 assert.doesNotMatch(detail,/상품 구성·배송조건이나 시설 반입 가능 여부는 주문 전에 해당 담당자에게 확인/);
 assert.equal((cards.match(/리본 문구는 보내는 목적에 맞춰 상담하실 수 있습니다/g)||[]).length,1);
 assert.doesNotMatch(cards,/p.family==='congrats'/);
 assert.ok(cards.includes('{site.productVariationNotice} {site.deliveryNotice}'));
});
