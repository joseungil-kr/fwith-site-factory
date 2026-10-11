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
const expected={"administrativeCrosswalk":[{"administrativeCode":"1126052000","aliasKey":"seoul-jungnang-gu/admin/1126052000","districtKey":"seoul-jungnang-gu","name":"면목제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/면목동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1126054000","aliasKey":"seoul-jungnang-gu/admin/1126054000","districtKey":"seoul-jungnang-gu","name":"면목제4동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/면목동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1126055000","aliasKey":"seoul-jungnang-gu/admin/1126055000","districtKey":"seoul-jungnang-gu","name":"면목제5동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/면목동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1126056500","aliasKey":"seoul-jungnang-gu/admin/1126056500","districtKey":"seoul-jungnang-gu","name":"면목본동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/면목동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1126057000","aliasKey":"seoul-jungnang-gu/admin/1126057000","districtKey":"seoul-jungnang-gu","name":"면목제7동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/면목동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1126057500","aliasKey":"seoul-jungnang-gu/admin/1126057500","districtKey":"seoul-jungnang-gu","name":"면목제3.8동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/면목동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1126058000","aliasKey":"seoul-jungnang-gu/admin/1126058000","districtKey":"seoul-jungnang-gu","name":"상봉제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/상봉동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1126059000","aliasKey":"seoul-jungnang-gu/admin/1126059000","districtKey":"seoul-jungnang-gu","name":"상봉제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/상봉동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1126060000","aliasKey":"seoul-jungnang-gu/admin/1126060000","districtKey":"seoul-jungnang-gu","name":"중화제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/중화동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1126061000","aliasKey":"seoul-jungnang-gu/admin/1126061000","districtKey":"seoul-jungnang-gu","name":"중화제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/중화동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1126062000","aliasKey":"seoul-jungnang-gu/admin/1126062000","districtKey":"seoul-jungnang-gu","name":"묵제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/묵동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1126063000","aliasKey":"seoul-jungnang-gu/admin/1126063000","districtKey":"seoul-jungnang-gu","name":"묵제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/묵동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1126065500","aliasKey":"seoul-jungnang-gu/admin/1126065500","districtKey":"seoul-jungnang-gu","name":"망우본동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/망우동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1126066000","aliasKey":"seoul-jungnang-gu/admin/1126066000","districtKey":"seoul-jungnang-gu","name":"망우제3동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/망우동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1126068000","aliasKey":"seoul-jungnang-gu/admin/1126068000","districtKey":"seoul-jungnang-gu","name":"신내1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/신내동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1126069000","aliasKey":"seoul-jungnang-gu/admin/1126069000","districtKey":"seoul-jungnang-gu","name":"신내2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"중랑구/법정동/신내동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"}],"approved":["sinnae-dong-seoul-medical-center-funeral-wreath","myeonmok-dong-green-hospital-funeral-wreath","sangbong-dong-dongbu-mideurang-opening-wreath"],"assetManifestSha256":"8edb0e9f8b7185e402ddaf42fca1c0f464c3b94f0afe4d6af7702013548eb54c","assetSubstitutions":[{"alt":"근조 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":75206,"imagePath":"/images/products/funeral-basic.jpg","imageSha256":"7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3","key":"funeral-basic","mimeType":"image/jpeg","pageHtmlSha256":"e93bb3e04d0cad05d702d37ed7454d9133cc565e22cbf7e59a9c9989717d839f","previousImagePath":"/images/products/funeral-basic.webp","previousImageSha256":"7b6a2ae56415c52ddc1e072c2250066366e31c177601f84055bf038a5541239b","previousSourceImageUrl":"https://fwith.kr/img/product/f1_hu_fe001f0cd4409b66.webp","sku":"B201","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B201/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B201","verifiedAt":"2026-10-11"},{"alt":"근조 고급 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":79304,"imagePath":"/images/products/funeral-premium.jpg","imageSha256":"0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114","key":"funeral-premium","mimeType":"image/jpeg","pageHtmlSha256":"423ad17b9c3e32b2341e351125915ccc795d5097cd43e6ff92bf986db075cf9b","previousImagePath":"/images/products/funeral-premium.webp","previousImageSha256":"c09af52edc3108584c0b76ae6d37715384d7b448dac3f3e7700f7ef10c5f7738","previousSourceImageUrl":"https://fwith.kr/img/product/f2_hu_c13ff56e9a54f74a.webp","sku":"B203","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B203/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B203","verifiedAt":"2026-10-11"},{"alt":"근조 특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":86279,"imagePath":"/images/products/funeral-large.jpg","imageSha256":"1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e","key":"funeral-large","mimeType":"image/jpeg","pageHtmlSha256":"17dca20d539c19731bb06cc637df3d270c659248f5ee715ef997bfeecad72214","previousImagePath":"/images/products/funeral-large.webp","previousImageSha256":"f3d1eba34c8b288c0f61582f98c4e0ef0de422842f7e9a12407ccaaab8e04210","previousSourceImageUrl":"https://fwith.kr/img/product/f3_hu_2dff149c34fa978f.webp","sku":"B205","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B205/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B205","verifiedAt":"2026-10-11"},{"alt":"근조 특특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":84178,"imagePath":"/images/products/funeral-xl.jpg","imageSha256":"a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3","key":"funeral-xl","mimeType":"image/jpeg","pageHtmlSha256":"ceb1b80333f8ac98301b3b87e94063a33a1969c6fd39dc4d48cb24a9d2291d2b","previousImagePath":"/images/products/funeral-xl.webp","previousImageSha256":"fab5752e7c2577efd0ed1713e69e943c83378107abe2f238d0e84a4faf9ffad6","previousSourceImageUrl":"https://fwith.kr/img/product/f4_hu_2d8d131f57c92d72.webp","sku":"B060","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B060/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B060","verifiedAt":"2026-10-11"},{"alt":"축하 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":77336,"imagePath":"/images/products/congrats-basic.jpg","imageSha256":"0e5c0e37f5a02b0448a0dd9b3aa48c4bd1ebe38862a9dde662ef2e1c14eee905","key":"congrats-basic","mimeType":"image/jpeg","pageHtmlSha256":"fe47afae87059224302f9cf8b4bd3c680c9c6f8e396ff46d3c8e8ee6cff7cda5","previousImagePath":"/images/products/congrats-basic.jpg","previousImageSha256":"2f58d64d26983bf9aa19f2410b47bfc193ad18b948b2ab54bf59b8a36bb1fdf6","previousSourceImageUrl":"https://www.baroflowers.com/product/c1.jpg","sku":"C200","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C200/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C200","verifiedAt":"2026-10-11"},{"alt":"축하 고급 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":77920,"imagePath":"/images/products/congrats-premium.jpg","imageSha256":"d3bd30015f4465f6db3d43c37a3088d383173e1bc0b46ff429ed24b9c251625a","key":"congrats-premium","mimeType":"image/jpeg","pageHtmlSha256":"dd90428adc0156f8a4cd42216880d71a2215599c0245f050742994c3aae6a938","previousImagePath":"/images/products/congrats-premium.jpg","previousImageSha256":"9b2a869a4aba5ab02af7c0efb5270f536b90d5989d040af5c2c7ead78ec6b46d","previousSourceImageUrl":"https://www.baroflowers.com/product/c2.jpg","sku":"C203","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C203/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C203","verifiedAt":"2026-10-11"},{"alt":"축하 특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":83318,"imagePath":"/images/products/congrats-large.jpg","imageSha256":"05a71d0a3a624c7e27e0575baab02c21f87cc409a1de5389bd4c42b2789dc16d","key":"congrats-large","mimeType":"image/jpeg","pageHtmlSha256":"32e3f97c8e1581801964e4fd6a8394f5f061b2cb6c53d32051ba0db985e5b1bc","previousImagePath":"/images/products/congrats-large.jpg","previousImageSha256":"2cffb47abdda01652a08e4f89372c5a32fed6b00d47f260afbbefe606bc72f15","previousSourceImageUrl":"https://www.baroflowers.com/product/c3.jpg","sku":"C204","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C204/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C204","verifiedAt":"2026-10-11"},{"alt":"축하 특특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":85391,"imagePath":"/images/products/congrats-xl.jpg","imageSha256":"b0fa2c913adf258617e34ce0175cbdc282b83e6b47db556234380353c047d5e9","key":"congrats-xl","mimeType":"image/jpeg","pageHtmlSha256":"4770377f7251588f01873910d0c44f565bb6872362c5e41f85ad649328be802a","previousImagePath":"/images/products/congrats-xl.jpg","previousImageSha256":"4929374434bd95de1cfe73421fd3033ef74f9532a68df1837a7e6e6afb51a410","previousSourceImageUrl":"https://www.baroflowers.com/product/c4.jpg","sku":"C205","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C205/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C205","verifiedAt":"2026-10-11"}],"held":[],"membershipCounts":{"administrative":16,"legal":6,"relations":16},"membershipSourceSha256":"22fb747f125254ad09bed2ea00ff27b467796e5aacc21d25fb648a70e11c3276","partialRelationCount":16,"partialUnitKeys":["중랑구/법정동/면목동","중랑구/법정동/상봉동","중랑구/법정동/중화동","중랑구/법정동/묵동","중랑구/법정동/망우동","중랑구/법정동/신내동"],"plannedUnitKeys":["중랑구/법정동/신내동","중랑구/법정동/면목동","중랑구/법정동/상봉동"],"proofFile":"dc766c6c4235b6ffe33d9f7efebc9a77.txt","queryEvidenceBySlug":{"myeonmok-dong-green-hospital-funeral-wreath":{"finding":"장례식장 24시간 운영과 꽃 판매자 제작·배송·야간 인수 가능성을 구분한다. 야간 문의 시 바로 결제할지 확인 가능한 다음 인수시각으로 잡을지 판단하도록, B2의 실제 호실과 시설·판매자 각각의 확인사항을 제시한다.","kind":"editorial_purchase_intent_hypothesis_from_verified_official_facility_facts","measuredSearchVolume":null,"originalResearchQuery":"녹색병원 장례식장 근조화환 주문","sourceUrl":"https://www.greenhospital.co.kr/sub08/sub10.php"},"sangbong-dong-dongbu-mideurang-opening-wreath":{"finding":"서울시가 별도로 등록한 상봉동 동부시장 미드랑길과 면목동 동부시장 백구단길을 구분해, 시장 이름만으로 개업 화환을 결제하지 않도록 실제 점포를 식별한다. 대표주소를 주문서에 복사하지 않고 점포 상호·도로명·층호·인수 담당자를 확보한다.","kind":"editorial_purchase_intent_hypothesis_from_distinct_official_registry_entries","measuredSearchVolume":null,"originalResearchQuery":"동부시장 미드랑길 개업 축하화환","sourceUrl":"https://news.seoul.go.kr/economy/archives/574563"},"sinnae-dong-seoul-medical-center-funeral-wreath":{"finding":"신내로 156 도착과 빈소 인수를 구분한다. 공식 B1 외부 연결 출입구·B2 빈소층을 확인하고, 실제 부고의 호실과 인수 장소가 정해진 뒤 주문할 수 있도록 돕는다.","kind":"editorial_purchase_intent_hypothesis_from_verified_official_facility_facts","measuredSearchVolume":null,"originalResearchQuery":"서울의료원 장례식장 근조화환 주문","sourceUrl":"https://as.seoulmc.or.kr/funeral/page/use/use_01.asp"}},"runtimeRegionsSha256":"59421a639f73ab10da4516ce069c8ab46dfa75ac3ad3a660847b8b647e0ed489","slugs":["sinnae-dong-seoul-medical-center-funeral-wreath","myeonmok-dong-green-hospital-funeral-wreath","sangbong-dong-dongbu-mideurang-opening-wreath"],"unitKeys":["중랑구/법정동/면목동","중랑구/법정동/상봉동","중랑구/법정동/중화동","중랑구/법정동/묵동","중랑구/법정동/망우동","중랑구/법정동/신내동"],"unitTypeCounts":{"eup":0,"legal-dong":6,"myeon":0}};






const priorRegionPattern=/동대문구|dongdaemun|광진구|gwangjin|성동구|seongdong|용산구|yongsan|중구|seoul-jung(?!nang)|종로|jongno|양평|yangpyeong|가평|연천|(?<![가-힣])여주|포천|남양주|양주|김포|광주시|광주광역시|안성|이천(?!리)|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:gapyeong|yeoncheon|yeoju|pocheon|namyangju|yangju|gimpo|gwangju|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/;
test('Seoul Jungnang-gu complete official membership stays separate from frozen purchase-intent N',()=>{
 const pages=read('pages'),c=read('region-coverage'),policy=read('region-policy');
 assert.deepEqual(pages.map(p=>p.slug),expected.approved);
 assert.deepEqual(c.units.map(u=>u.unitKey),expected.unitKeys);
 assert.deepEqual(c.administrativeCrosswalk,expected.administrativeCrosswalk);
 assert.equal(c.membershipSourceSha256,expected.membershipSourceSha256);
 assert.equal(c.units.length,expected.membershipCounts.legal);assert.equal(c.administrativeCrosswalk.length,expected.membershipCounts.administrative);
 assert.equal(c.representatives.length,expected.slugs.length);
 assert.equal(c.districts.length,1);assert.equal(c.districts[0].name,'중랑구');
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
 assert.match(source,/개별 안내 준비 중/);assert.match(source,/개별 주문 안내는 준비된 곳만 연결/);
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
test('Seoul Jungnang-gu customer wording is allowed while copied prior-site names remain rejected',()=>{
 assert.doesNotMatch('서울 중랑구 면목동과 상봉동 주문 안내',priorRegionPattern);
 assert.doesNotMatch('상품을 보여주는 사진',priorRegionPattern);
 assert.doesNotMatch('https://seoul-jungnang.fwith.kr/',priorRegionPattern);
 for(const copied of ['https://seoul-jung.fwith.kr/','서울 중구','동대문구','seoul-dongdaemun'])assert.match(copied,priorRegionPattern);
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
 const products=read('products'),proof=read('social-image-provenance');
 assert.equal(proof.assetSource,'fresh-same-sku-official-gallery');assert.equal(proof.assetSubstitutionManifestSha256,expected.assetManifestSha256);
 for(const asset of expected.assetSubstitutions){
  const p=products.find(p=>p.key===asset.key),row=proof.products.find(p=>p.key===asset.key);
  assert.equal(p.officialSku,asset.sku);assert.equal(p.img,asset.imagePath);assert.equal(p.sourceImageUrl,asset.sourceImageUrl);
  assert.equal(sha(fs.readFileSync(new URL('../public'+asset.imagePath,import.meta.url))),asset.imageSha256);
  assert.equal(row.image.sha256,asset.imageSha256);assert.equal(row.sourceImageUrl,asset.sourceImageUrl);assert.equal(row.sourceImageHttpStatus,200);
  assert.deepEqual(row.image.dimensions,asset.dimensions);assert.equal(row.image.type,asset.mimeType);assert.equal(row.previousImageSha256,asset.previousImageSha256);
  const reviewed=JSON.parse(read('customer-copy-review-20261011').approvalBasis.choiceCommonManifest.utf8Content);
  assert.equal(sha(fs.readFileSync(new URL('../src/data/products.json',import.meta.url))),reviewed.commonChanges.find(r=>r.path==='src/data/products.json').proposalSha256);
  const cards=fs.readFileSync(new URL('../src/components/ProductCards.astro',import.meta.url),'utf8');
  assert.match(cards,/사진 속 리본은 예시/);assert.match(cards,/site.productVariationNotice/);assert.match(cards,/site.deliveryNotice/);
 }
 assert.match(read('business-truth').deliveryNotice,/상품 기본가격.*실제 배송지.*추가 배송비.*최종 결제금액.*주문 전에.*상담/);
 assert.doesNotMatch(read('business-truth').deliveryNotice,/양평|단월|양서|10,000원|무료/);
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
  assert.match(p.contentMarkdown+' '+read('business-truth').deliveryNotice,/추가 배송비|추가배송비|배송비/); assert.ok(fs.readFileSync(new URL('../src/components/ProductCards.astro',import.meta.url),'utf8').includes('{site.deliveryNotice}'));
 }
});
test('complete assembled graph and reviewed HTTPS source arrays pass unchanged shared validators',()=>{
 assert.equal(validateGraph(loadGraph()).pages,expected.approved.length);
 for(const p of read('pages'))assert.deepEqual(pageSources(p),p.sources);
});
