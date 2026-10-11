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
const expected={"administrativeCrosswalk":[{"administrativeCode":"1123051500","aliasKey":"seoul-dongdaemun-gu/admin/1123051500","districtKey":"seoul-dongdaemun-gu","name":"신설동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/신설동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/용두동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1123053300","aliasKey":"seoul-dongdaemun-gu/admin/1123053300","districtKey":"seoul-dongdaemun-gu","name":"용두동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/용두동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1123054500","aliasKey":"seoul-dongdaemun-gu/admin/1123054500","districtKey":"seoul-dongdaemun-gu","name":"제기동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/제기동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1123056000","aliasKey":"seoul-dongdaemun-gu/admin/1123056000","districtKey":"seoul-dongdaemun-gu","name":"전농제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/전농동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1123057000","aliasKey":"seoul-dongdaemun-gu/admin/1123057000","districtKey":"seoul-dongdaemun-gu","name":"전농제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/전농동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1123060000","aliasKey":"seoul-dongdaemun-gu/admin/1123060000","districtKey":"seoul-dongdaemun-gu","name":"답십리제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/답십리동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1123061000","aliasKey":"seoul-dongdaemun-gu/admin/1123061000","districtKey":"seoul-dongdaemun-gu","name":"답십리제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/답십리동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1123065000","aliasKey":"seoul-dongdaemun-gu/admin/1123065000","districtKey":"seoul-dongdaemun-gu","name":"장안제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/장안동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1123066000","aliasKey":"seoul-dongdaemun-gu/admin/1123066000","districtKey":"seoul-dongdaemun-gu","name":"장안제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/장안동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1123070500","aliasKey":"seoul-dongdaemun-gu/admin/1123070500","districtKey":"seoul-dongdaemun-gu","name":"청량리동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/청량리동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1123071000","aliasKey":"seoul-dongdaemun-gu/admin/1123071000","districtKey":"seoul-dongdaemun-gu","name":"회기동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/회기동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1123072000","aliasKey":"seoul-dongdaemun-gu/admin/1123072000","districtKey":"seoul-dongdaemun-gu","name":"휘경제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/휘경동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1123073000","aliasKey":"seoul-dongdaemun-gu/admin/1123073000","districtKey":"seoul-dongdaemun-gu","name":"휘경제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/휘경동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1123074000","aliasKey":"seoul-dongdaemun-gu/admin/1123074000","districtKey":"seoul-dongdaemun-gu","name":"이문제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/이문동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1123075000","aliasKey":"seoul-dongdaemun-gu/admin/1123075000","districtKey":"seoul-dongdaemun-gu","name":"이문제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"동대문구/법정동/이문동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"}],"approved":["hoegi-dong-khmc-funeral-wreath","hwigyeong-dong-bellaluce-seoul-wedding-wreath","jeonnong-dong-l65-wedding-wreath","jegi-dong-kyungdong-market-opening-wreath","sinseol-dong-seoul-pungmul-market-opening-wreath"],"held":[],"membershipCounts":{"administrative":15,"legal":10,"relations":16},"membershipSourceSha256":"f2d795f035f8261fc8d838fc92f17ecc41c20ca55ac6648cb7119d6bf4b51508","partialRelationCount":12,"partialUnitKeys":["동대문구/법정동/용두동","동대문구/법정동/전농동","동대문구/법정동/답십리동","동대문구/법정동/장안동","동대문구/법정동/휘경동","동대문구/법정동/이문동"],"plannedUnitKeys":["동대문구/법정동/회기동","동대문구/법정동/휘경동","동대문구/법정동/전농동","동대문구/법정동/제기동","동대문구/법정동/신설동"],"proofFile":"395943542e37181dfd58159ac664dc8d.txt","queryEvidenceBySlug":{"hoegi-dong-khmc-funeral-wreath":{"finding":"경희라는 이름만 보고 강동구의 다른 장례식장으로 보내지 않도록, 회기동 경희의료원 주소와 공식 층별 빈소 번호를 함께 대조한다.","measuredSearchVolume":null,"originalResearchQuery":"경희의료원 장례식장 근조화환","sourceUrl":"https://funeral.khuhs.or.kr/10/1010.do"},"hwigyeong-dong-bellaluce-seoul-wedding-wreath":{"finding":"망우로61의 현재 예식장명과 서울점 지점을 확인하고, 여러 층의 홀 이름을 실제 청첩장과 맞추어 서로 다른 예식의 화환이 섞이지 않도록 준비한다.","measuredSearchVolume":null,"originalResearchQuery":"벨라루체 서울점 축하화환","sourceUrl":"https://www.bellaluceseoul.co.kr/"},"jegi-dong-kyungdong-market-opening-wreath":{"finding":"시장 전체를 가리키는 주소만으로 특정 가게가 확정되지 않으므로, 아케이드의 점포인지 별도 건물·층의 점포인지 구별하여 개업·이전 축하 주문에 필요한 도착지를 구체화한다.","measuredSearchVolume":null,"originalResearchQuery":"경동시장 개업화환","sourceUrl":"https://www.ddm.go.kr/tour/selectTourCntntsWebView.do?key=1488&pageIndex=1&pageUnit=12&searchClNo=8&searchCnd=all&tourNo=32"},"jeonnong-dong-l65-wedding-wreath":{"finding":"청량리역 생활권이라는 표현을 법정 청량리동으로 착각하지 않고, 전농동 타워동6층의 가든홀·컨벤션홀과 행사별 반입 조건을 확인한다.","measuredSearchVolume":null,"originalResearchQuery":"L65호텔웨딩컨벤션 축하화환","sourceUrl":"https://l65hotelwedding.co.kr/"},"sinseol-dong-seoul-pungmul-market-opening-wreath":{"finding":"두 개 층과 색상별 판매구역으로 나뉜 실내시장에서 상호만으로 도착지를 정하지 않고, 층·구역·점포번호·실제 인수인을 함께 받는 주문을 안내한다.","measuredSearchVolume":null,"originalResearchQuery":"서울풍물시장 개업화환","sourceUrl":"https://news.seoul.go.kr/economy/pungmul-time"}},"runtimeRegionsSha256":"59421a639f73ab10da4516ce069c8ab46dfa75ac3ad3a660847b8b647e0ed489","slugs":["hoegi-dong-khmc-funeral-wreath","hwigyeong-dong-bellaluce-seoul-wedding-wreath","jeonnong-dong-l65-wedding-wreath","jegi-dong-kyungdong-market-opening-wreath","sinseol-dong-seoul-pungmul-market-opening-wreath"],"unitKeys":["동대문구/법정동/신설동","동대문구/법정동/용두동","동대문구/법정동/제기동","동대문구/법정동/전농동","동대문구/법정동/답십리동","동대문구/법정동/장안동","동대문구/법정동/청량리동","동대문구/법정동/회기동","동대문구/법정동/휘경동","동대문구/법정동/이문동"],"unitTypeCounts":{"eup":0,"legal-dong":10,"myeon":0}};






const priorRegionPattern=/광진구|gwangjin|성동구|seongdong|용산구|yongsan|중구|seoul-jung|종로|jongno|양평|yangpyeong|가평|연천|(?<![가-힣])여주|포천|남양주|양주|김포|광주시|광주광역시|안성|이천(?!리)|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:gapyeong|yeoncheon|yeoju|pocheon|namyangju|yangju|gimpo|gwangju|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/;
test('Seoul Dongdaemun-gu complete official membership stays separate from frozen purchase-intent N',()=>{
 const pages=read('pages'),c=read('region-coverage'),policy=read('region-policy');
 assert.deepEqual(pages.map(p=>p.slug),expected.approved);
 assert.deepEqual(c.units.map(u=>u.unitKey),expected.unitKeys);
 assert.deepEqual(c.administrativeCrosswalk,expected.administrativeCrosswalk);
 assert.equal(c.membershipSourceSha256,expected.membershipSourceSha256);
 assert.equal(c.units.length,expected.membershipCounts.legal);assert.equal(c.administrativeCrosswalk.length,expected.membershipCounts.administrative);
 assert.equal(c.representatives.length,expected.slugs.length);
 assert.equal(c.districts.length,1);assert.equal(c.districts[0].name,'동대문구');
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
test('Seoul Dongdaemun-gu customer wording is allowed while copied prior-site names remain rejected',()=>{
 assert.doesNotMatch('서울 동대문구 신설동과 용두동 주문 안내',priorRegionPattern);
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
 assert.match(read('business-truth').deliveryNotice,/실제 배송지.*추가 배송비.*최종 결제금액.*배송·반입 가능 여부.*요청 시간.*주문 전에.*상담/);
 assert.doesNotMatch(read('business-truth').deliveryNotice,/양평|단월|양서|10,000원|무료/);
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
  assert.match(read('business-truth').deliveryNotice,/추가 배송비/);
  const cards=fs.readFileSync(new URL('../src/components/ProductCards.astro',import.meta.url),'utf8');
  const detail=fs.readFileSync(new URL('../src/pages/[category]/[slug].astro',import.meta.url),'utf8');
  assert.equal((cards.match(/site.deliveryNotice/g)||[]).length,1);
  assert.ok(detail.includes('<ProductCards products={productSet}/>'));
  assert.ok(selectProducts(p,products,p.productCardLimit).length>0);
 }
});
test('complete assembled graph and reviewed HTTPS source arrays pass unchanged shared validators',()=>{
 assert.equal(validateGraph(loadGraph()).pages,expected.approved.length);
 for(const p of read('pages'))assert.deepEqual(pageSources(p),p.sources);
});
