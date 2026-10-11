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
const expected={"administrativeCrosswalk":[{"administrativeCode":"1132051100","aliasKey":"seoul-dobong-gu/admin/1132051100","districtKey":"seoul-dobong-gu","name":"창제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"도봉구/법정동/창동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1132051200","aliasKey":"seoul-dobong-gu/admin/1132051200","districtKey":"seoul-dobong-gu","name":"창제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"도봉구/법정동/창동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1132051300","aliasKey":"seoul-dobong-gu/admin/1132051300","districtKey":"seoul-dobong-gu","name":"창제3동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"도봉구/법정동/창동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1132051400","aliasKey":"seoul-dobong-gu/admin/1132051400","districtKey":"seoul-dobong-gu","name":"창제4동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"도봉구/법정동/창동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1132051500","aliasKey":"seoul-dobong-gu/admin/1132051500","districtKey":"seoul-dobong-gu","name":"창제5동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"도봉구/법정동/창동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1132052100","aliasKey":"seoul-dobong-gu/admin/1132052100","districtKey":"seoul-dobong-gu","name":"도봉제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"도봉구/법정동/도봉동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1132052200","aliasKey":"seoul-dobong-gu/admin/1132052200","districtKey":"seoul-dobong-gu","name":"도봉제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"도봉구/법정동/도봉동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1132066000","aliasKey":"seoul-dobong-gu/admin/1132066000","districtKey":"seoul-dobong-gu","name":"쌍문제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"도봉구/법정동/쌍문동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1132067000","aliasKey":"seoul-dobong-gu/admin/1132067000","districtKey":"seoul-dobong-gu","name":"쌍문제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"도봉구/법정동/쌍문동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1132068000","aliasKey":"seoul-dobong-gu/admin/1132068000","districtKey":"seoul-dobong-gu","name":"쌍문제3동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"도봉구/법정동/쌍문동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1132068100","aliasKey":"seoul-dobong-gu/admin/1132068100","districtKey":"seoul-dobong-gu","name":"쌍문제4동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"도봉구/법정동/쌍문동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1132069000","aliasKey":"seoul-dobong-gu/admin/1132069000","districtKey":"seoul-dobong-gu","name":"방학제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"도봉구/법정동/방학동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1132070000","aliasKey":"seoul-dobong-gu/admin/1132070000","districtKey":"seoul-dobong-gu","name":"방학제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"도봉구/법정동/방학동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1132071000","aliasKey":"seoul-dobong-gu/admin/1132071000","districtKey":"seoul-dobong-gu","name":"방학제3동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"도봉구/법정동/방학동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"}],"approved":["ssangmun-dong-hanil-hospital-funeral-wreath","banghak-dong-dokkaebi-market-opening-wreath","chang-dong-dobong-harmony-hall-congrats-wreath","dobong-dong-peace-culture-bunker-exhibition-wreath"],"approvedDistinctUnitCount":4,"assetManifestSha256":"34ceabd6872c6774b4de7c48efa633c5099d57491a6b5e763ed5e4d108c457bc","assetSubstitutions":[{"alt":"근조 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":75206,"imagePath":"/images/products/funeral-basic.jpg","imageSha256":"7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3","key":"funeral-basic","mimeType":"image/jpeg","pageHtmlSha256":"745d392b9a2bcd7dfb8a72e8716f1679379f04e268ee39e2412b6fdb152be6e8","previousImagePath":"/images/products/funeral-basic.jpg","previousImageSha256":"7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B201/thumb-1_500x500.jpg","sku":"B201","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B201/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B201","verifiedAt":"2026-10-11T11:31:13.715136+00:00"},{"alt":"근조 고급 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":79304,"imagePath":"/images/products/funeral-premium.jpg","imageSha256":"0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114","key":"funeral-premium","mimeType":"image/jpeg","pageHtmlSha256":"eb93dcdcc4d4d025cdb633174bdf86ac1a9da32697fb0c7ea1935250f1ac0475","previousImagePath":"/images/products/funeral-premium.jpg","previousImageSha256":"0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B203/thumb-1_500x500.jpg","sku":"B203","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B203/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B203","verifiedAt":"2026-10-11T11:31:13.951286+00:00"},{"alt":"근조 특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":86279,"imagePath":"/images/products/funeral-large.jpg","imageSha256":"1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e","key":"funeral-large","mimeType":"image/jpeg","pageHtmlSha256":"4acb92e23f93ef92b74d4a3f27c2591e87d7898cfd8c0fbfb1800f8c23312318","previousImagePath":"/images/products/funeral-large.jpg","previousImageSha256":"1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B205/thumb-1_500x500.jpg","sku":"B205","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B205/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B205","verifiedAt":"2026-10-11T11:31:13.680651+00:00"},{"alt":"근조 특특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":84178,"imagePath":"/images/products/funeral-xl.jpg","imageSha256":"a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3","key":"funeral-xl","mimeType":"image/jpeg","pageHtmlSha256":"43448673a188e6f42a5ba34b7752deee78133516686280b84b4c8e04d4c77f5d","previousImagePath":"/images/products/funeral-xl.jpg","previousImageSha256":"a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B060/thumb-1_500x500.jpg","sku":"B060","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B060/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B060","verifiedAt":"2026-10-11T11:31:13.671652+00:00"},{"alt":"축하 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":77336,"imagePath":"/images/products/congrats-basic.jpg","imageSha256":"0e5c0e37f5a02b0448a0dd9b3aa48c4bd1ebe38862a9dde662ef2e1c14eee905","key":"congrats-basic","mimeType":"image/jpeg","pageHtmlSha256":"f43073c8bfed004ed4280828ea441be0c0cf33297fac690f0b5b2ed5db7cb7f7","previousImagePath":"/images/products/congrats-basic.jpg","previousImageSha256":"0e5c0e37f5a02b0448a0dd9b3aa48c4bd1ebe38862a9dde662ef2e1c14eee905","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C200/thumb-1_500x500.jpg","sku":"C200","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C200/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C200","verifiedAt":"2026-10-11T11:31:17.279912+00:00"},{"alt":"축하 고급 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":77920,"imagePath":"/images/products/congrats-premium.jpg","imageSha256":"d3bd30015f4465f6db3d43c37a3088d383173e1bc0b46ff429ed24b9c251625a","key":"congrats-premium","mimeType":"image/jpeg","pageHtmlSha256":"0a01195d6a6ccb51e7c14bb6d72648ee8b8a8aee924f68d2e2a04a0b80e15bda","previousImagePath":"/images/products/congrats-premium.jpg","previousImageSha256":"d3bd30015f4465f6db3d43c37a3088d383173e1bc0b46ff429ed24b9c251625a","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C203/thumb-1_500x500.jpg","sku":"C203","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C203/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C203","verifiedAt":"2026-10-11T11:31:17.357770+00:00"},{"alt":"축하 특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":83318,"imagePath":"/images/products/congrats-large.jpg","imageSha256":"05a71d0a3a624c7e27e0575baab02c21f87cc409a1de5389bd4c42b2789dc16d","key":"congrats-large","mimeType":"image/jpeg","pageHtmlSha256":"a72fd20b4994791416a56e1509a59cb35f07192d721091f2cddcf2c43c0d702e","previousImagePath":"/images/products/congrats-large.jpg","previousImageSha256":"05a71d0a3a624c7e27e0575baab02c21f87cc409a1de5389bd4c42b2789dc16d","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C204/thumb-1_500x500.jpg","sku":"C204","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C204/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C204","verifiedAt":"2026-10-11T11:31:17.085097+00:00"},{"alt":"축하 특특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":85391,"imagePath":"/images/products/congrats-xl.jpg","imageSha256":"b0fa2c913adf258617e34ce0175cbdc282b83e6b47db556234380353c047d5e9","key":"congrats-xl","mimeType":"image/jpeg","pageHtmlSha256":"be374cdcb9400119abf622fc7f2a3cf6728ea375aa9a320ccca6e7afa6921b0d","previousImagePath":"/images/products/congrats-xl.jpg","previousImageSha256":"b0fa2c913adf258617e34ce0175cbdc282b83e6b47db556234380353c047d5e9","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C205/thumb-1_500x500.jpg","sku":"C205","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C205/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C205","verifiedAt":"2026-10-11T11:31:17.508821+00:00"}],"contextBySlug":{},"facilities":[],"held":[],"membershipCounts":{"administrative":14,"legal":4,"relations":14},"membershipSourceSha256":"b07ccb7c85c78478e1566d6138344acadb3926dfab688ff53594a43c835ded99","partialRelationCount":14,"partialUnitKeys":["도봉구/법정동/쌍문동","도봉구/법정동/방학동","도봉구/법정동/창동","도봉구/법정동/도봉동"],"plannedDistinctUnitCount":4,"plannedUnitKeys":["도봉구/법정동/쌍문동","도봉구/법정동/방학동","도봉구/법정동/창동","도봉구/법정동/도봉동"],"proofFile":"22b6729f36d195ce3cecd699d9ccf3ff.txt","queryEvidenceBySlug":{"banghak-dong-dokkaebi-market-opening-wreath":{"canonicalFacility":{"address":"서울특별시 도봉구 도당로 85-7 (방학동)","name":"방학동도깨비시장","sourceURL":"https://www.dobongmarket.kr/dokkaebimarket"},"facilityKey":"banghak-dokkaebi-market","finding":"센터 주소와 공영주차장 주소를 실제 주문 목적지로 오인하지 않도록 개업점포 상호·도로명·호수를 분리해 받는다.","measuredSearchVolume":null,"originalResearchQuery":"방학동도깨비시장 점포 개업화환 주문","purchaseIntentKey":"opening-congrats-wreath","sourceUrl":"https://www.dobongmarket.kr/dokkaebimarket","status":"official_facility_supported_purchase_hypothesis_not_measured_demand","unitKey":"도봉구/법정동/방학동"},"chang-dong-dobong-harmony-hall-congrats-wreath":{"canonicalFacility":{"address":"서울특별시 도봉구 도봉로 552 (창동)","name":"도봉구민회관 하모니홀","sourceURL":"https://yeyak.seoul.go.kr/web/reservation/selectReservView.do?rsv_svc_id=S251113115433740026"},"facilityKey":"dobong-civic-harmony-hall","finding":"공연 시작시각과 대관 개방시각을 구분해 문이 닫힌 시간에 화환을 보내는 실패를 막고, 같은 건물의 소공연장 혼동을 해소한다.","measuredSearchVolume":null,"originalResearchQuery":"도봉구민회관 하모니홀 공연 축하화환 주문","purchaseIntentKey":"event-congrats-wreath","sourceUrl":"https://yeyak.seoul.go.kr/web/reservation/selectReservView.do?rsv_svc_id=S251113115433740026","status":"official_facility_supported_purchase_hypothesis_not_measured_demand","unitKey":"도봉구/법정동/창동"},"dobong-dong-peace-culture-bunker-exhibition-wreath":{"canonicalFacility":{"address":"서울특별시 도봉구 마들로 932 (도봉동)","name":"평화문화진지","sourceURL":"https://tour.dobong.go.kr/Contents.asp?code=10007287"},"facilityKey":"peace-culture-bunker","finding":"동 번호와 전시실을 지정해 사무실·공연장·외부 주차장으로 잘못 인도하는 일을 막고, 제한된 전시공간 배치와 행사 종료 후 처리를 주문 전에 분리 확인한다.","measuredSearchVolume":null,"originalResearchQuery":"평화문화진지 전시 개막 축하화환 주문","purchaseIntentKey":"event-congrats-wreath","sourceUrl":"https://tour.dobong.go.kr/Contents.asp?code=10007287","status":"official_facility_supported_purchase_hypothesis_not_measured_demand","unitKey":"도봉구/법정동/도봉동"},"ssangmun-dong-hanil-hospital-funeral-wreath":{"canonicalFacility":{"address":"서울특별시 도봉구 우이천로 308 (쌍문동)","name":"한일병원 장례식장","sourceURL":"https://m.hanilmed.net/m/contents.do?menuNo=81101348"},"facilityKey":"hanil-hospital-funeral","finding":"같은 병원 주소라도 병동·응급실과 장례식장을 구분하고 공식 문상실 번호를 대조해 근조화환 목적지를 정한다.","measuredSearchVolume":null,"originalResearchQuery":"한일병원 장례식장 근조화환 주문","purchaseIntentKey":"funeral-condolence-wreath","sourceUrl":"https://m.hanilmed.net/m/contents.do?menuNo=81101348","status":"official_facility_supported_purchase_hypothesis_not_measured_demand","unitKey":"도봉구/법정동/쌍문동"}},"representativeAssignment":null,"runtimeRegionsSha256":"59421a639f73ab10da4516ce069c8ab46dfa75ac3ad3a660847b8b647e0ed489","slugs":["ssangmun-dong-hanil-hospital-funeral-wreath","banghak-dong-dokkaebi-market-opening-wreath","chang-dong-dobong-harmony-hall-congrats-wreath","dobong-dong-peace-culture-bunker-exhibition-wreath"],"unitKeys":["도봉구/법정동/쌍문동","도봉구/법정동/방학동","도봉구/법정동/창동","도봉구/법정동/도봉동"],"unitTypeCounts":{"eup":0,"legal-dong":4,"myeon":0}};







const priorRegionPattern=/강북구|gangbuk|성북구|seongbuk|동대문구|dongdaemun|중랑구|jungnang|광진구|gwangjin|성동구|seongdong|용산구|yongsan|중구|seoul-jung(?!nang)|종로|jongno|양평|yangpyeong|가평|연천|(?<![가-힣])여주|포천|남양주|양주|김포|광주시|광주광역시|안성|(?:(?<!우)이천(?!리)|(?<=[가-힣]우)이천(?!리)|(?<=우)이천(?!로(?![가-힣])|리))|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:gapyeong|yeoncheon|yeoju|pocheon|namyangju|yangju|gimpo|gwangju|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/;
test('Seoul Dobong-gu complete official membership stays separate from frozen purchase-intent N',()=>{
 const pages=read('pages'),c=read('region-coverage'),policy=read('region-policy');
 assert.deepEqual(pages.map(p=>p.slug),expected.approved);
 assert.deepEqual(c.units.map(u=>u.unitKey),expected.unitKeys);
 assert.deepEqual(c.administrativeCrosswalk,expected.administrativeCrosswalk);
 assert.equal(c.membershipSourceSha256,expected.membershipSourceSha256);
 assert.equal(c.units.length,expected.membershipCounts.legal);assert.equal(c.administrativeCrosswalk.length,expected.membershipCounts.administrative);
 assert.equal(c.representatives.length,expected.slugs.length);
 assert.equal(c.districts.length,1);assert.equal(c.districts[0].name,'도봉구');
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
 assert.throws(()=>validateDefinition(duplicate,p),/duplicate\/unknown canonical unit/);
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
test('Seoul Dobong-gu customer wording is allowed while copied prior-site names remain rejected',()=>{
 assert.doesNotMatch('서울 도봉구 쌍문동과 방학동 주문 안내',priorRegionPattern);
 assert.doesNotMatch('서울특별시 도봉구 우이천로 308',priorRegionPattern);
 for(const copied of ['이천','이천시','경기도 이천시','경기도이천시','이천 화환','이천꽃배달','이천로','가짜우이천로','우이천로꽃배달','우이천시','우이천 화환','https://seoul-icheon.fwith.kr/','/icheon/flower/'])assert.match(copied,priorRegionPattern);
 assert.doesNotMatch('상품을 보여주는 사진',priorRegionPattern);
 assert.doesNotMatch('https://seoul-dobong.fwith.kr/',priorRegionPattern);
 for(const copied of ['https://seoul-jung.fwith.kr/','https://seoul-jungnang.fwith.kr/','중랑구','서울 중구','동대문구','seoul-dongdaemun'])assert.match(copied,priorRegionPattern);
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
test('every reviewed comparison renders four exact family products and truthful delivery surcharge',()=>{
 const products=read('products'),proof=read('social-image-provenance');
 assert.equal(proof.assetSource,'fresh-same-sku-official-gallery');assert.equal(proof.assetSubstitutionManifestSha256,expected.assetManifestSha256);
 for(const asset of expected.assetSubstitutions){
  const p=products.find(p=>p.key===asset.key),row=proof.products.find(p=>p.key===asset.key);
  assert.equal(p.officialSku,asset.sku);assert.equal(p.img,asset.imagePath);assert.equal(p.sourceImageUrl,asset.sourceImageUrl);
  assert.equal(sha(fs.readFileSync(new URL('../public'+asset.imagePath,import.meta.url))),asset.imageSha256);
  assert.equal(row.image.sha256,asset.imageSha256);assert.equal(row.sourceImageUrl,asset.sourceImageUrl);assert.equal(row.sourceImageHttpStatus,200);
  assert.deepEqual(row.image.dimensions,asset.dimensions);assert.equal(row.image.type,asset.mimeType);assert.equal(row.previousImageSha256,asset.previousImageSha256);
  assert.match(p.desc,/공식 상품 예시.*리본 문구.*구성.*추가 배송비.*주문 전에 확인/);
 }
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


test('legacy coverage counters stay exact without runtime context fields',()=>{
 const c=read('region-coverage'),policy=read('region-policy'),m=read('publish-manifest');
 assert.equal(c.representativeAssignment,undefined);assert.equal(policy.representativeAssignment,undefined);assert.equal(c.facilities,undefined);
 assert.equal(m.directRelease.officialMembership.plannedRepresentedUnits,expected.plannedDistinctUnitCount);
 assert.equal(m.directRelease.officialMembership.unrepresentedUnits,c.units.length-expected.plannedDistinctUnitCount);
});

// Evidence-side exact-set gate supplements, but never changes, the pristine runtime.
test('legacy frozen facility evidence and exact approved collection sets remain bound',()=>{
 const c=read('region-coverage'),policy=read('region-policy');
 assert.equal(c.representativeAssignment,undefined);assert.equal(policy.representativeAssignment,undefined);assert.equal(c.facilities,undefined);
 const approved=expected.approved.map(slug=>'seoul-dobong-flower-direct-region-'+slug);
 for(const rows of [read('pages'),read('page-map').pages,read('publish-manifest').pages,read('architecture').pages]){
  assert.deepEqual(rows.map(p=>p.pageKey),approved);assert.equal(new Set(rows.map(p=>p.pageKey)).size,rows.length);
  for(const p of rows){
   const r=c.representatives.find(r=>r.pageKey===p.pageKey);assert.ok(r);assert.equal(p.url,r.url);assert.equal(p.slug,r.slug);assert.equal(p.primaryKeyword,r.primaryKeyword);assert.equal(p.scopeKey,c.scopeKey);assert.deepEqual(p.regionUnitKeys,r.unitKeys);
   for(const key of ['facilityKey','purchaseIntentKey','contextKey'])assert.equal(p[key],undefined);
   const q=expected.queryEvidenceBySlug[r.slug];assert.deepEqual(r.queryEvidence,q);
   if(q.facilityKey){const family=q.purchaseIntentKey==='funeral-condolence-wreath'?'funeral':'congrats';assert.deepEqual(p.regionalProductFamilies,[family]);}
  }
 }
 const architecture=read('architecture');for(const r of c.representatives.filter(r=>r.status==='approved')){const p=architecture.pages.find(p=>p.pageKey===r.pageKey);assert.equal(p.intentKey,r.intentKey);}
});
