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
const expected={"administrativeCrosswalk":[{"administrativeCode":"1121571000","aliasKey":"seoul-gwangjin-gu/admin/1121571000","districtKey":"seoul-gwangjin-gu","name":"화양동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"광진구/법정동/화양동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1121573000","aliasKey":"seoul-gwangjin-gu/admin/1121573000","districtKey":"seoul-gwangjin-gu","name":"군자동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"광진구/법정동/군자동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1121574000","aliasKey":"seoul-gwangjin-gu/admin/1121574000","districtKey":"seoul-gwangjin-gu","name":"중곡제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"광진구/법정동/중곡동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1121575000","aliasKey":"seoul-gwangjin-gu/admin/1121575000","districtKey":"seoul-gwangjin-gu","name":"중곡제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"광진구/법정동/중곡동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1121576000","aliasKey":"seoul-gwangjin-gu/admin/1121576000","districtKey":"seoul-gwangjin-gu","name":"중곡제3동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"광진구/법정동/중곡동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1121577000","aliasKey":"seoul-gwangjin-gu/admin/1121577000","districtKey":"seoul-gwangjin-gu","name":"중곡제4동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"광진구/법정동/중곡동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1121578000","aliasKey":"seoul-gwangjin-gu/admin/1121578000","districtKey":"seoul-gwangjin-gu","name":"능동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"광진구/법정동/능동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1121581000","aliasKey":"seoul-gwangjin-gu/admin/1121581000","districtKey":"seoul-gwangjin-gu","name":"광장동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"광진구/법정동/광장동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1121582000","aliasKey":"seoul-gwangjin-gu/admin/1121582000","districtKey":"seoul-gwangjin-gu","name":"자양제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"광진구/법정동/자양동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1121583000","aliasKey":"seoul-gwangjin-gu/admin/1121583000","districtKey":"seoul-gwangjin-gu","name":"자양제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"광진구/법정동/자양동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1121584000","aliasKey":"seoul-gwangjin-gu/admin/1121584000","districtKey":"seoul-gwangjin-gu","name":"자양제3동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"광진구/법정동/자양동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1121584700","aliasKey":"seoul-gwangjin-gu/admin/1121584700","districtKey":"seoul-gwangjin-gu","name":"자양제4동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"광진구/법정동/자양동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1121585000","aliasKey":"seoul-gwangjin-gu/admin/1121585000","districtKey":"seoul-gwangjin-gu","name":"구의제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"광진구/법정동/구의동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1121586000","aliasKey":"seoul-gwangjin-gu/admin/1121586000","districtKey":"seoul-gwangjin-gu","name":"구의제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"광진구/법정동/구의동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1121587000","aliasKey":"seoul-gwangjin-gu/admin/1121587000","districtKey":"seoul-gwangjin-gu","name":"구의제3동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"광진구/법정동/구의동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"}],"approved":["hwayang-dong-konkuk-hospital-condolence-wreath","gwangjang-dong-walkerhill-wedding-wreath","guui-dong-weddingsquare-gangbyeon-wreath","junggok-dong-jeil-market-opening-wreath","jayang-dong-ku-convention-event-wreath"],"held":[],"membershipCounts":{"administrative":15,"legal":7,"relations":15},"membershipSourceSha256":"39e7a6061e48908ec47b72db9f197543df72ab631b517abf5c84872c6068bc84","partialRelationCount":11,"partialUnitKeys":["광진구/법정동/중곡동","광진구/법정동/구의동","광진구/법정동/자양동"],"plannedUnitKeys":["광진구/법정동/화양동","광진구/법정동/광장동","광진구/법정동/구의동","광진구/법정동/중곡동","광진구/법정동/자양동"],"proofFile":"50848994f56729f860c081255ea7fe8c.txt","queryEvidenceBySlug":{"guui-dong-weddingsquare-gangbyeon-wreath":{"finding":"복합 상가의 도로명주소와 웨딩 시설의 3–4층 표기를 구분하고, 루시드홀·그레이스홀 등 청첩장의 실제 홀을 확인하는 주문.","measuredSearchVolume":null,"originalResearchQuery":"웨딩스퀘어 강변 축하화환","sourceUrl":"https://www.weddingsquare.co.kr/"},"gwangjang-dong-walkerhill-wedding-wreath":{"finding":"호텔명과 공통 도로명주소만으로는 결혼식의 실제 행사장을 확정할 수 없어 여러 웨딩 공간의 정확한 장소명과 인수 담당을 먼저 구별하는 주문.","measuredSearchVolume":null,"originalResearchQuery":"워커힐 결혼식 축하화환","sourceUrl":"https://www.walkerhill.com/m/Map"},"hwayang-dong-konkuk-hospital-condolence-wreath":{"finding":"같은 건대입구 생활권의 예식장과 대학시설을 구분하고, 병원 이름만으로 보내지 않도록 빈소 호실과 발인 전 수령시각을 맞추는 조문 주문.","measuredSearchVolume":null,"originalResearchQuery":"건국대학교병원 장례식장 근조화환","sourceUrl":"https://www.kuh.ac.kr/m/funeral/guide/directions.do"},"jayang-dong-ku-convention-event-wreath":{"finding":"공식 기업연회 안내가 이취임식·리셉션·정기총회 등 행사와 3F/B1 연회층을 명시하므로, 건대입구 주변 다른 시설이나 웨딩공간과 혼동하지 않고 행사명·행사층·수령 담당자를 정하는 기업 축하 주문.","measuredSearchVolume":null,"originalResearchQuery":"KU컨벤션 기업행사 축하화환","sourceUrl":"https://kkweddinghall.co.kr/"},"junggok-dong-jeil-market-opening-wreath":{"finding":"비슷한 이름의 중곡제일시장과 중곡제일골목시장이 서울시 현황에 별도 주소·형태로 등재되어 있어 시장 대표주소를 실제 입점 점포의 배송지로 잘못 쓰지 않도록 하는 개업 주문.","measuredSearchVolume":null,"originalResearchQuery":"중곡제일시장 개업화환","sourceUrl":"https://news.seoul.go.kr/economy/archives/568162"}},"runtimeRegionsSha256":"59421a639f73ab10da4516ce069c8ab46dfa75ac3ad3a660847b8b647e0ed489","slugs":["hwayang-dong-konkuk-hospital-condolence-wreath","gwangjang-dong-walkerhill-wedding-wreath","guui-dong-weddingsquare-gangbyeon-wreath","junggok-dong-jeil-market-opening-wreath","jayang-dong-ku-convention-event-wreath"],"unitKeys":["광진구/법정동/중곡동","광진구/법정동/능동","광진구/법정동/구의동","광진구/법정동/광장동","광진구/법정동/자양동","광진구/법정동/화양동","광진구/법정동/군자동"],"unitTypeCounts":{"eup":0,"legal-dong":7,"myeon":0}};





const priorRegionPattern=/성동구|seongdong|용산구|yongsan|중구|seoul-jung|종로|jongno|양평|yangpyeong|가평|연천|(?<![가-힣])여주|포천|남양주|양주|김포|광주시|광주광역시|안성|이천(?!리)|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:gapyeong|yeoncheon|yeoju|pocheon|namyangju|yangju|gimpo|gwangju|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/;
test('Seoul Gwangjin-gu complete official membership stays separate from frozen purchase-intent N',()=>{
 const pages=read('pages'),c=read('region-coverage'),policy=read('region-policy');
 assert.deepEqual(pages.map(p=>p.slug),expected.approved);
 assert.deepEqual(c.units.map(u=>u.unitKey),expected.unitKeys);
 assert.deepEqual(c.administrativeCrosswalk,expected.administrativeCrosswalk);
 assert.equal(c.membershipSourceSha256,expected.membershipSourceSha256);
 assert.equal(c.units.length,expected.membershipCounts.legal);assert.equal(c.administrativeCrosswalk.length,expected.membershipCounts.administrative);
 assert.equal(c.representatives.length,expected.slugs.length);
 assert.equal(c.districts.length,1);assert.equal(c.districts[0].name,'광진구');
 assert.equal(new Set(c.administrativeCrosswalk.map(a=>a.aliasKey)).size,expected.membershipCounts.administrative);
 const relations=c.administrativeCrosswalk.flatMap(a=>a.relations);
 assert.equal(relations.length,expected.membershipCounts.relations);assert.equal(relations.filter(r=>r.scope==='partial').length,expected.partialRelationCount);
 const mixed=new Set(expected.partialUnitKeys);
 assert.ok(relations.every(r=>r.scope===(mixed.has(r.unitKey)?'partial':'whole')));
 assert.deepEqual(Object.fromEntries(['legal-dong','eup','myeon'].map(t=>[t,c.units.filter(u=>u.unitType===t).length])),expected.unitTypeCounts);
 assert.deepEqual(c.representatives.map(r=>r.slug),expected.slugs);
 assert.deepEqual(c.representatives.map(r=>r.unitKeys),expected.plannedUnitKeys.map(k=>[k]));
 assert.equal(new Set(c.representatives.flatMap(r=>r.unitKeys)).size,expected.slugs.length);
 assert.deepEqual(c.representatives.filter(r=>r.status==='approved').map(r=>r.slug),expected.approved);
 assert.deepEqual(c.representatives.filter(r=>r.status==='reserved').map(r=>r.slug),expected.held);
 assert.ok(pages.length*10>=expected.slugs.length*9);
 assert.doesNotThrow(()=>validateDefinition(c,policy));
 for(const p of pages){assert.equal(p.category,'regions');assert.equal(p.pageType,'regional-service');assert.equal(p.url,`/regions/${p.slug}/`);}
});
test('unchanged regional validator permits unrepresented membership but rejects fake or duplicate assignments',()=>{
 const c=read('region-coverage'),p=read('region-policy');
 assert.equal(sha(fs.readFileSync(new URL('../src/lib/regions.mjs',import.meta.url))),expected.runtimeRegionsSha256);
 assert.doesNotThrow(()=>validateDefinition({...structuredClone(c),representatives:[]},p));
 const duplicate=structuredClone(c);duplicate.representatives[1].unitKeys=duplicate.representatives[0].unitKeys;
 assert.throws(()=>validateDefinition(duplicate,p),/duplicate\/unknown canonical unit/);
 const unknown=structuredClone(c);unknown.representatives[0].unitKeys=['unverified/unknown'];
 assert.throws(()=>validateDefinition(unknown,p),/duplicate\/unknown canonical unit/);
 const invalidRelation=structuredClone(c);invalidRelation.administrativeCrosswalk[0].relations[0].scope='guessed';
 assert.throws(()=>validateDefinition(invalidRelation,p),/invalid alias relation/);
 const quota=structuredClone(c);quota.countIsPageQuota=true;
 assert.throws(()=>validateDefinition(quota,p),/unsupported unit basis or quota/);
});
test('directory links only reviewed planned articles and retains an honest unwritten membership state',()=>{
 const c=read('region-coverage'),p=read('region-policy'),a=read('architecture'),pages=read('pages');
 const groups=directoryGroups(pages,a,c,p),entries=groups.flatMap(d=>d.items);
 assert.deepEqual(entries.map(e=>e.page.slug),expected.approved);
 assert.equal(new Set(entries.flatMap(e=>e.representative.unitKeys)).size,expected.approved.length);
 for(const entry of entries)assert.deepEqual(entry.page.regionUnitKeys,entry.representative.unitKeys);
 const source=fs.readFileSync(new URL('../src/components/RegionDirectory.astro',import.meta.url),'utf8');
 assert.match(source,/개별 안내 준비 중/);assert.match(source,/관할 목록과 개별 주문 안내의 범위는 다릅니다/);
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
test('Seoul Gwangjin-gu customer wording is allowed while copied prior-site names remain rejected',()=>{
 assert.doesNotMatch('서울 광진구 자양동과 구의동 주문 안내',priorRegionPattern);
 assert.doesNotMatch('상품을 보여주는 사진',priorRegionPattern);
 for(const copied of ['양평군 꽃배달','https://yangpyeong.fwith.kr/','가평군 꽃배달','https://gapyeong.fwith.kr/','여주시 꽃배달','여주 꽃배달','이천시 꽃배달','이천 꽃배달','https://icheon.fwith.kr/regions/example/','연천군 꽃배달','https://yeoju.fwith.kr/'])
  assert.match(copied,priorRegionPattern);
});
test('public ownership proof is unique and specific to this source',()=>{
 const root=new URL('../public/',import.meta.url);const matches=fs.readdirSync(root).filter(n=>/^[0-9a-f]{32}\.txt$/.test(n));
 assert.deepEqual(matches,[expected.proofFile]);assert.notEqual(matches[0],'29a79c8ebd0e44a9c81400fd74a93cbc.txt');
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
test('every reviewed comparison renders four exact family products and truthful delivery surcharge',()=>{
 const products=read('products');
 assert.match(read('business-truth').deliveryNotice,/실제 배송지 주소.*추가 배송비.*최종 결제금액.*주문 전에.*확인/);
 assert.doesNotMatch(read('business-truth').deliveryNotice,/양평|단월|양서|10,000원|무료/);
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
  assert.match(p.contentMarkdown,/추가 배송비|추가배송비|배송비/);
 }
});
test('complete assembled graph and reviewed HTTPS source arrays pass unchanged shared validators',()=>{
 assert.equal(validateGraph(loadGraph()).pages,expected.approved.length);
 for(const p of read('pages'))assert.deepEqual(pageSources(p),p.sources);
});
