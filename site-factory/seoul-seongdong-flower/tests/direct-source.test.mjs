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
const expected={"administrativeCrosswalk":[{"administrativeCode":"1120052000","aliasKey":"seoul-seongdong-gu/admin/1120052000","districtKey":"seoul-seongdong-gu","name":"왕십리제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/하왕십리동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120053500","aliasKey":"seoul-seongdong-gu/admin/1120053500","districtKey":"seoul-seongdong-gu","name":"왕십리도선동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/상왕십리동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/하왕십리동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/홍익동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/도선동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120054000","aliasKey":"seoul-seongdong-gu/admin/1120054000","districtKey":"seoul-seongdong-gu","name":"마장동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/마장동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120055000","aliasKey":"seoul-seongdong-gu/admin/1120055000","districtKey":"seoul-seongdong-gu","name":"사근동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/사근동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/행당동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120056000","aliasKey":"seoul-seongdong-gu/admin/1120056000","districtKey":"seoul-seongdong-gu","name":"행당제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/행당동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120057000","aliasKey":"seoul-seongdong-gu/admin/1120057000","districtKey":"seoul-seongdong-gu","name":"행당제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/행당동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120058000","aliasKey":"seoul-seongdong-gu/admin/1120058000","districtKey":"seoul-seongdong-gu","name":"응봉동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/응봉동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120059000","aliasKey":"seoul-seongdong-gu/admin/1120059000","districtKey":"seoul-seongdong-gu","name":"금호1가동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/금호동1가"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120061500","aliasKey":"seoul-seongdong-gu/admin/1120061500","districtKey":"seoul-seongdong-gu","name":"금호2.3가동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/금호동2가"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/금호동3가"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120062000","aliasKey":"seoul-seongdong-gu/admin/1120062000","districtKey":"seoul-seongdong-gu","name":"금호4가동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/금호동4가"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120064500","aliasKey":"seoul-seongdong-gu/admin/1120064500","districtKey":"seoul-seongdong-gu","name":"옥수동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/옥수동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120065000","aliasKey":"seoul-seongdong-gu/admin/1120065000","districtKey":"seoul-seongdong-gu","name":"성수1가제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/성수동1가"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120066000","aliasKey":"seoul-seongdong-gu/admin/1120066000","districtKey":"seoul-seongdong-gu","name":"성수1가제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/성수동1가"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120067000","aliasKey":"seoul-seongdong-gu/admin/1120067000","districtKey":"seoul-seongdong-gu","name":"성수2가제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/성수동2가"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120069000","aliasKey":"seoul-seongdong-gu/admin/1120069000","districtKey":"seoul-seongdong-gu","name":"성수2가제3동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/성수동2가"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120072000","aliasKey":"seoul-seongdong-gu/admin/1120072000","districtKey":"seoul-seongdong-gu","name":"송정동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/송정동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1120079000","aliasKey":"seoul-seongdong-gu/admin/1120079000","districtKey":"seoul-seongdong-gu","name":"용답동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/송정동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"성동구/법정동/용답동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"}],"approved":["sageun-dong-hanyang-hospital-condolence-wreath","seongsu1-ga-bottega-maggio-wedding-wreath","seongsu2-ga-sfactory-popup-opening-wreath","majang-dong-market-opening-wreath"],"held":[],"membershipCounts":{"administrative":17,"legal":17,"relations":23},"membershipSourceSha256":"31b46ca5812dd1aad113e307af40ae59f2dc52ec176dbb2706778e929e804b83","partialRelationCount":11,"partialUnitKeys":["성동구/법정동/하왕십리동","성동구/법정동/행당동","성동구/법정동/성수동1가","성동구/법정동/성수동2가","성동구/법정동/송정동"],"plannedUnitKeys":["성동구/법정동/사근동","성동구/법정동/성수동1가","성동구/법정동/성수동2가","성동구/법정동/마장동"],"proofFile":"add58a1e6b5d1bc5ac6423ae2934f8c1.txt","queryEvidenceBySlug":{"majang-dong-market-opening-wreath":{"finding":"축산 도소매 점포의 판매장·작업장·사무실 중 실제 개업과 축하화환 수령이 이루어지는 지점을 구별한다. 상호만 같은 작업공간이나 시장 상인회로 보내지 않고 점포 담당자와 수령 공간을 맞춘다.","measuredSearchVolume":null,"originalResearchQuery":"마장축산물시장 개업 축하화환, 점포명과 영업장 수령 위치 확인","sourceUrl":"https://bogunso.sd.go.kr/main/contents.do?key=1694"},"sageun-dong-hanyang-hospital-condolence-wreath":{"finding":"한양대 서울·구리병원 혼동, 병원 본관·서관 구분, 빈소와 발인 전 수령 시각을 구분한다.","measuredSearchVolume":null,"originalResearchQuery":"한양대학교병원 장례식장 근조화환 주문, 서관·빈소·발인 일정 확인","sourceUrl":"https://www.hyumc.com/conts/102009001000000.do"},"seongsu1-ga-bottega-maggio-wedding-wreath":{"finding":"주거동·갤러리와 예식장을 같은 주소만으로 혼동하지 않고 G층(B2), 청첩장 홀과 예식 정보를 확인한다.","measuredSearchVolume":null,"originalResearchQuery":"보테가마지오 결혼식 축하화환 주문, 갤러리아포레 G층과 예식 정보 확인","sourceUrl":"https://www.bottegamaggio.co.kr/location"},"seongsu2-ga-sfactory-popup-opening-wreath":{"finding":"상설 점포 개업과 일시적 팝업·전시 개막을 구분하고 행사별 주최 측, 동·층, 설치 전후 수령창과 회수를 맞춘다.","measuredSearchVolume":null,"originalResearchQuery":"에스팩토리 팝업·전시 개막 축하화환, 행사명과 동·층 확인","sourceUrl":"https://www.sfactory.co.kr/"}},"runtimeRegionsSha256":"59421a639f73ab10da4516ce069c8ab46dfa75ac3ad3a660847b8b647e0ed489","slugs":["sageun-dong-hanyang-hospital-condolence-wreath","seongsu1-ga-bottega-maggio-wedding-wreath","seongsu2-ga-sfactory-popup-opening-wreath","majang-dong-market-opening-wreath"],"unitKeys":["성동구/법정동/상왕십리동","성동구/법정동/하왕십리동","성동구/법정동/홍익동","성동구/법정동/도선동","성동구/법정동/마장동","성동구/법정동/사근동","성동구/법정동/행당동","성동구/법정동/응봉동","성동구/법정동/금호동1가","성동구/법정동/금호동2가","성동구/법정동/금호동3가","성동구/법정동/금호동4가","성동구/법정동/옥수동","성동구/법정동/성수동1가","성동구/법정동/성수동2가","성동구/법정동/송정동","성동구/법정동/용답동"],"unitTypeCounts":{"eup":0,"legal-dong":17,"myeon":0}};




const priorRegionPattern=/용산구|yongsan|중구|seoul-jung|종로|jongno|양평|yangpyeong|가평|연천|(?<![가-힣])여주|포천|남양주|양주|김포|광주시|광주광역시|안성|이천(?!리)|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:gapyeong|yeoncheon|yeoju|pocheon|namyangju|yangju|gimpo|gwangju|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/;
test('Seoul Seongdong-gu complete official membership stays separate from frozen purchase-intent N',()=>{
 const pages=read('pages'),c=read('region-coverage'),policy=read('region-policy');
 assert.deepEqual(pages.map(p=>p.slug),expected.approved);
 assert.deepEqual(c.units.map(u=>u.unitKey),expected.unitKeys);
 assert.deepEqual(c.administrativeCrosswalk,expected.administrativeCrosswalk);
 assert.equal(c.membershipSourceSha256,expected.membershipSourceSha256);
 assert.equal(c.units.length,expected.membershipCounts.legal);assert.equal(c.administrativeCrosswalk.length,expected.membershipCounts.administrative);
 assert.equal(c.representatives.length,expected.slugs.length);
 assert.equal(c.districts.length,1);assert.equal(c.districts[0].name,'성동구');
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
test('Seoul Seongdong-gu customer wording is allowed while copied prior-site names remain rejected',()=>{
 assert.doesNotMatch('서울 성동구 사근동과 송정동 주문 안내',priorRegionPattern);
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
