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
const expected={"administrativeCrosswalk":[{"administrativeCode":"1130553400","aliasKey":"seoul-gangbuk-gu/admin/1130553400","districtKey":"seoul-gangbuk-gu","name":"삼양동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"강북구/법정동/미아동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1130553500","aliasKey":"seoul-gangbuk-gu/admin/1130553500","districtKey":"seoul-gangbuk-gu","name":"미아동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"강북구/법정동/미아동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1130554500","aliasKey":"seoul-gangbuk-gu/admin/1130554500","districtKey":"seoul-gangbuk-gu","name":"송중동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"강북구/법정동/미아동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1130555500","aliasKey":"seoul-gangbuk-gu/admin/1130555500","districtKey":"seoul-gangbuk-gu","name":"송천동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"강북구/법정동/미아동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1130557500","aliasKey":"seoul-gangbuk-gu/admin/1130557500","districtKey":"seoul-gangbuk-gu","name":"삼각산동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"강북구/법정동/미아동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1130559500","aliasKey":"seoul-gangbuk-gu/admin/1130559500","districtKey":"seoul-gangbuk-gu","name":"번1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"강북구/법정동/번동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1130560300","aliasKey":"seoul-gangbuk-gu/admin/1130560300","districtKey":"seoul-gangbuk-gu","name":"번2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"강북구/법정동/번동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1130560800","aliasKey":"seoul-gangbuk-gu/admin/1130560800","districtKey":"seoul-gangbuk-gu","name":"번3동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"강북구/법정동/번동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1130561500","aliasKey":"seoul-gangbuk-gu/admin/1130561500","districtKey":"seoul-gangbuk-gu","name":"수유1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"강북구/법정동/수유동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1130562500","aliasKey":"seoul-gangbuk-gu/admin/1130562500","districtKey":"seoul-gangbuk-gu","name":"수유2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"강북구/법정동/수유동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1130563500","aliasKey":"seoul-gangbuk-gu/admin/1130563500","districtKey":"seoul-gangbuk-gu","name":"수유3동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"강북구/법정동/수유동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1130564500","aliasKey":"seoul-gangbuk-gu/admin/1130564500","districtKey":"seoul-gangbuk-gu","name":"우이동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"강북구/법정동/수유동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"강북구/법정동/우이동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"},{"administrativeCode":"1130566000","aliasKey":"seoul-gangbuk-gu/admin/1130566000","districtKey":"seoul-gangbuk-gu","name":"인수동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","unitKey":"강북구/법정동/수유동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824"}],"approved":["suyu-dong-daehan-funeral-wreath","mia-dong-the-victoria-wedding-wreath","ui-dong-anto-wedding-wreath","suyu-dong-suyu-market-opening-wreath","suyu-dong-gangbuk-arts-congratulation-wreath"],"approvedDistinctUnitCount":3,"assetManifestSha256":"398c6626a5c1f7147097c55f9d9077e04f91a001e762efb029cdc7dcc9cac07e","assetSubstitutions":[{"alt":"근조 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":75206,"imagePath":"/images/products/funeral-basic.jpg","imageSha256":"7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3","key":"funeral-basic","mimeType":"image/jpeg","pageHtmlSha256":"02124c015c3f2b106d2a7b83a555508342b0f5788eda48ef0c82f20ab44a691a","previousImagePath":"/images/products/funeral-basic.jpg","previousImageSha256":"7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B201/thumb-1_500x500.jpg","sku":"B201","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B201/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B201","verifiedAt":"2026-10-11T10:49:37.147072+00:00"},{"alt":"근조 고급 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":79304,"imagePath":"/images/products/funeral-premium.jpg","imageSha256":"0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114","key":"funeral-premium","mimeType":"image/jpeg","pageHtmlSha256":"18b0a311bf02a66ded9179bc3d7a196571f6b62f038155e25ca3ca3d676a9b55","previousImagePath":"/images/products/funeral-premium.jpg","previousImageSha256":"0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B203/thumb-1_500x500.jpg","sku":"B203","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B203/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B203","verifiedAt":"2026-10-11T10:49:37.400070+00:00"},{"alt":"근조 특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":86279,"imagePath":"/images/products/funeral-large.jpg","imageSha256":"1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e","key":"funeral-large","mimeType":"image/jpeg","pageHtmlSha256":"b8aa0ba5fbc364fa7f1f63406a4f190167a18af2b59af484a4a72b082a8635a0","previousImagePath":"/images/products/funeral-large.jpg","previousImageSha256":"1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B205/thumb-1_500x500.jpg","sku":"B205","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B205/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B205","verifiedAt":"2026-10-11T10:49:37.101833+00:00"},{"alt":"근조 특특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":84178,"imagePath":"/images/products/funeral-xl.jpg","imageSha256":"a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3","key":"funeral-xl","mimeType":"image/jpeg","pageHtmlSha256":"e3ae358ef96c0186dda9a9ca05b0a1d4c705dd62ca738de29ebe78679c7a4877","previousImagePath":"/images/products/funeral-xl.jpg","previousImageSha256":"a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B060/thumb-1_500x500.jpg","sku":"B060","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B060/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B060","verifiedAt":"2026-10-11T10:49:37.110636+00:00"},{"alt":"축하 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":77336,"imagePath":"/images/products/congrats-basic.jpg","imageSha256":"0e5c0e37f5a02b0448a0dd9b3aa48c4bd1ebe38862a9dde662ef2e1c14eee905","key":"congrats-basic","mimeType":"image/jpeg","pageHtmlSha256":"61389cba10203459c017d9cdda0ffeae174ead86e73f03aa502d8be74076c9e3","previousImagePath":"/images/products/congrats-basic.jpg","previousImageSha256":"0e5c0e37f5a02b0448a0dd9b3aa48c4bd1ebe38862a9dde662ef2e1c14eee905","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C200/thumb-1_500x500.jpg","sku":"C200","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C200/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C200","verifiedAt":"2026-10-11T10:49:42.988849+00:00"},{"alt":"축하 고급 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":77920,"imagePath":"/images/products/congrats-premium.jpg","imageSha256":"d3bd30015f4465f6db3d43c37a3088d383173e1bc0b46ff429ed24b9c251625a","key":"congrats-premium","mimeType":"image/jpeg","pageHtmlSha256":"3f12e1093b0373812e0276326b44d20cf3727e6555de48216b0714c461336249","previousImagePath":"/images/products/congrats-premium.jpg","previousImageSha256":"d3bd30015f4465f6db3d43c37a3088d383173e1bc0b46ff429ed24b9c251625a","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C203/thumb-1_500x500.jpg","sku":"C203","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C203/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C203","verifiedAt":"2026-10-11T10:49:43.150309+00:00"},{"alt":"축하 특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":83318,"imagePath":"/images/products/congrats-large.jpg","imageSha256":"05a71d0a3a624c7e27e0575baab02c21f87cc409a1de5389bd4c42b2789dc16d","key":"congrats-large","mimeType":"image/jpeg","pageHtmlSha256":"47cc625571774db3bdb17b97d8aee555806ed87e69e9b2b585a4ea16018b07ad","previousImagePath":"/images/products/congrats-large.jpg","previousImageSha256":"05a71d0a3a624c7e27e0575baab02c21f87cc409a1de5389bd4c42b2789dc16d","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C204/thumb-1_500x500.jpg","sku":"C204","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C204/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C204","verifiedAt":"2026-10-11T10:49:43.463089+00:00"},{"alt":"축하 특특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":85391,"imagePath":"/images/products/congrats-xl.jpg","imageSha256":"b0fa2c913adf258617e34ce0175cbdc282b83e6b47db556234380353c047d5e9","key":"congrats-xl","mimeType":"image/jpeg","pageHtmlSha256":"884364076a58792f802344a4cc7eb0a8c2ff60da04310f0b40ea2db076bbd512","previousImagePath":"/images/products/congrats-xl.jpg","previousImageSha256":"b0fa2c913adf258617e34ce0175cbdc282b83e6b47db556234380353c047d5e9","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C205/thumb-1_500x500.jpg","sku":"C205","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C205/thumb-1_500x500.jpg","sourceSelector":"#sit_pvi_big first img src","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C205","verifiedAt":"2026-10-11T10:49:43.214029+00:00"}],"contextBySlug":{"mia-dong-the-victoria-wedding-wreath":{"contextKey":"the-victoria-wedding-party|wedding-congrats-wreath","facilityKey":"the-victoria-wedding-party","intentKey":"seoul-gangbuk|the-victoria-wedding-party|wedding-congrats-wreath","purchaseIntentKey":"wedding-congrats-wreath"},"suyu-dong-daehan-funeral-wreath":{"contextKey":"daehan-hospital-funeral|funeral-condolence-wreath","facilityKey":"daehan-hospital-funeral","intentKey":"seoul-gangbuk|daehan-hospital-funeral|funeral-condolence-wreath","purchaseIntentKey":"funeral-condolence-wreath"},"suyu-dong-gangbuk-arts-congratulation-wreath":{"contextKey":"gangbuk-culture-arts-center|event-congrats-wreath","facilityKey":"gangbuk-culture-arts-center","intentKey":"seoul-gangbuk|gangbuk-culture-arts-center|event-congrats-wreath","purchaseIntentKey":"event-congrats-wreath"},"suyu-dong-suyu-market-opening-wreath":{"contextKey":"suyu-market|opening-congrats-wreath","facilityKey":"suyu-market","intentKey":"seoul-gangbuk|suyu-market|opening-congrats-wreath","purchaseIntentKey":"opening-congrats-wreath"},"ui-dong-anto-wedding-wreath":{"contextKey":"anto-resort|wedding-congrats-wreath","facilityKey":"anto-resort","intentKey":"seoul-gangbuk|anto-resort|wedding-congrats-wreath","purchaseIntentKey":"wedding-congrats-wreath"}},"facilities":[{"address":"서울특별시 강북구 도봉로 301(수유동)","facilityKey":"daehan-hospital-funeral","name":"대한병원장례식장","sourceUrl":"https://www.kfcpi.or.kr/link/2025/09/29/831da0f4-5acd-43d4-b0ae-60e6111f33f7.pdf","unitKey":"강북구/법정동/수유동"},{"address":"서울특별시 강북구 도봉로 16(미아동)","facilityKey":"the-victoria-wedding-party","name":"더빅토리아웨딩파티","sourceUrl":"https://thevictoria.co.kr/About","unitKey":"강북구/법정동/미아동"},{"address":"서울특별시 강북구 삼양로 689(우이동)","facilityKey":"anto-resort","name":"안토 리조트","sourceUrl":"https://antoresort.co.kr/reservation/search","unitKey":"강북구/법정동/우이동"},{"address":"서울특별시 강북구 도봉로67길 18","facilityKey":"suyu-market","name":"수유시장","sourceUrl":"https://news.seoul.go.kr/economy/archives/571689","unitKey":"강북구/법정동/수유동"},{"address":"서울특별시 강북구 삼각산로 85(수유동)","facilityKey":"gangbuk-culture-arts-center","name":"강북문화예술회관","sourceUrl":"https://www.gbcf.or.kr/load.asp?subPage=210","unitKey":"강북구/법정동/수유동"}],"held":[],"membershipCounts":{"administrative":13,"legal":4,"relations":14},"membershipSourceSha256":"fbea10e76f72c94f3cea61ae4f330c052b0cc82d7fc7433d9d5fb040af2c75c1","partialRelationCount":13,"partialUnitKeys":["강북구/법정동/미아동","강북구/법정동/번동","강북구/법정동/수유동"],"plannedDistinctUnitCount":3,"plannedUnitKeys":["강북구/법정동/수유동","강북구/법정동/미아동","강북구/법정동/우이동","강북구/법정동/수유동","강북구/법정동/수유동"],"proofFile":"1b5d445f91752b21e17f249556424dec.txt","queryEvidenceBySlug":{"mia-dong-the-victoria-wedding-wreath":{"finding":"같은 도로명 건물 안 복수 예식홀과 예식시간을 함께 확인하는 주문 판단","measuredSearchVolume":null,"originalResearchQuery":"더빅토리아웨딩파티 결혼식 축하화환 주문","sourceUrl":"https://thevictoria.co.kr/About","status":"official_facility_supported_purchase_intent_hypothesis_not_measured_demand"},"suyu-dong-daehan-funeral-wreath":{"finding":"병원명만 받은 경우 정확한 장례식장·빈소 수령처를 확정하는 구매 판단","measuredSearchVolume":null,"originalResearchQuery":"대한병원장례식장 근조화환 주문","sourceUrl":"https://www.kfcpi.or.kr/link/2025/09/29/831da0f4-5acd-43d4-b0ae-60e6111f33f7.pdf","status":"official_facility_supported_purchase_intent_hypothesis_not_measured_demand"},"suyu-dong-gangbuk-arts-congratulation-wreath":{"finding":"기관 사무실과 실제 행사 공간·주최자를 구별하고 반입/회수 시점을 조정하는 구매 판단","measuredSearchVolume":null,"originalResearchQuery":"강북문화예술회관 공연·전시 축하화환 주문","sourceUrl":"https://www.gbcf.or.kr/load.asp?subPage=210","status":"official_facility_supported_purchase_intent_hypothesis_not_measured_demand"},"suyu-dong-suyu-market-opening-wreath":{"finding":"유사한 시장명에서 실제 점포 배송지를 확정하고 건물형과 골목형 수령을 구분하는 구매 판단","measuredSearchVolume":null,"originalResearchQuery":"수유시장 점포 개업화환 주문","sourceUrl":"https://news.seoul.go.kr/economy/archives/571689","status":"official_facility_supported_purchase_intent_hypothesis_not_measured_demand"},"ui-dong-anto-wedding-wreath":{"finding":"옛 명칭·리조트 대표주소만으로 끝내지 않고 실제 실내/야외 행사 수령점을 확정하는 구매 판단","measuredSearchVolume":null,"originalResearchQuery":"안토 리조트 웨딩 축하화환 주문","sourceUrl":"https://antoresort.co.kr/reservation/search","status":"official_facility_supported_purchase_intent_hypothesis_not_measured_demand"}},"representativeAssignment":"facility-purchase-context-v1","runtimeRegionsSha256":"83468ad9954362247054fd35013d8eee5fec260998e3d89c33d323f66736e321","slugs":["suyu-dong-daehan-funeral-wreath","mia-dong-the-victoria-wedding-wreath","ui-dong-anto-wedding-wreath","suyu-dong-suyu-market-opening-wreath","suyu-dong-gangbuk-arts-congratulation-wreath"],"unitKeys":["강북구/법정동/미아동","강북구/법정동/번동","강북구/법정동/수유동","강북구/법정동/우이동"],"unitTypeCounts":{"eup":0,"legal-dong":4,"myeon":0}};







const priorRegionPattern=/성북구|seongbuk|동대문구|dongdaemun|중랑구|jungnang|광진구|gwangjin|성동구|seongdong|용산구|yongsan|중구|seoul-jung(?!nang)|종로|jongno|양평|yangpyeong|가평|연천|(?<![가-힣])여주|포천|남양주|양주|김포|광주시|광주광역시|안성|이천(?!리)|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:gapyeong|yeoncheon|yeoju|pocheon|namyangju|yangju|gimpo|gwangju|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/;
test('Seoul Gangbuk-gu complete official membership stays separate from frozen purchase-intent N',()=>{
 const pages=read('pages'),c=read('region-coverage'),policy=read('region-policy');
 assert.deepEqual(pages.map(p=>p.slug),expected.approved);
 assert.deepEqual(c.units.map(u=>u.unitKey),expected.unitKeys);
 assert.deepEqual(c.administrativeCrosswalk,expected.administrativeCrosswalk);
 assert.equal(c.membershipSourceSha256,expected.membershipSourceSha256);
 assert.equal(c.units.length,expected.membershipCounts.legal);assert.equal(c.administrativeCrosswalk.length,expected.membershipCounts.administrative);
 assert.equal(c.representatives.length,expected.slugs.length);
 assert.equal(c.districts.length,1);assert.equal(c.districts[0].name,'강북구');
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
test('Seoul Gangbuk-gu customer wording is allowed while copied prior-site names remain rejected',()=>{
 assert.doesNotMatch('서울 강북구 미아동과 수유동 주문 안내',priorRegionPattern);
 assert.doesNotMatch('상품을 보여주는 사진',priorRegionPattern);
 assert.doesNotMatch('https://seoul-gangbuk.fwith.kr/',priorRegionPattern);
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
  assert.match(p.contentMarkdown,/추가 배송비|추가배송비|배송비/);
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
  assert.equal(r.intentKey,`seoul-gangbuk|${r.contextKey}`);
  const facility=c.facilities.find(f=>f.facilityKey===r.facilityKey);assert.ok(facility);assert.deepEqual(r.unitKeys,[facility.unitKey]);
  if(r.status!=='approved')continue;
  for(const rows of [pages,m.pages,a.pages,pm.pages]){const page=rows.find(p=>p.pageKey===r.pageKey);assert.ok(page);for(const key of ['facilityKey','purchaseIntentKey','contextKey','intentKey'])assert.equal(page[key],binding[key]);assert.deepEqual(page.regionUnitKeys,r.unitKeys);}
 }
});
