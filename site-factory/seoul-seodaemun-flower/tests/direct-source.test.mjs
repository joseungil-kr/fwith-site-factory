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
const expected={"administrativeCrosswalk":[{"administrativeCode":"1141052000","aliasKey":"seoul-seodaemun-gu/admin/1141052000","districtKey":"seoul-seodaemun-gu","name":"천연동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/냉천동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/천연동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/옥천동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/영천동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/현저동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1141055500","aliasKey":"seoul-seodaemun-gu/admin/1141055500","districtKey":"seoul-seodaemun-gu","name":"북아현동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/북아현동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/대현동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1141056500","aliasKey":"seoul-seodaemun-gu/admin/1141056500","districtKey":"seoul-seodaemun-gu","name":"충현동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/충정로2가"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/충정로3가"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/합동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/미근동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/북아현동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1141058500","aliasKey":"seoul-seodaemun-gu/admin/1141058500","districtKey":"seoul-seodaemun-gu","name":"신촌동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/대현동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/대신동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/신촌동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/봉원동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/창천동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1141061500","aliasKey":"seoul-seodaemun-gu/admin/1141061500","districtKey":"seoul-seodaemun-gu","name":"연희동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/연희동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1141062000","aliasKey":"seoul-seodaemun-gu/admin/1141062000","districtKey":"seoul-seodaemun-gu","name":"홍제제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/홍제동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1141064000","aliasKey":"seoul-seodaemun-gu/admin/1141064000","districtKey":"seoul-seodaemun-gu","name":"홍제제3동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/홍제동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1141065500","aliasKey":"seoul-seodaemun-gu/admin/1141065500","districtKey":"seoul-seodaemun-gu","name":"홍제제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/홍제동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1141066000","aliasKey":"seoul-seodaemun-gu/admin/1141066000","districtKey":"seoul-seodaemun-gu","name":"홍은제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/홍은동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1141068500","aliasKey":"seoul-seodaemun-gu/admin/1141068500","districtKey":"seoul-seodaemun-gu","name":"홍은제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/홍은동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1141069000","aliasKey":"seoul-seodaemun-gu/admin/1141069000","districtKey":"seoul-seodaemun-gu","name":"남가좌제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/남가좌동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1141070000","aliasKey":"seoul-seodaemun-gu/admin/1141070000","districtKey":"seoul-seodaemun-gu","name":"남가좌제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/남가좌동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1141071000","aliasKey":"seoul-seodaemun-gu/admin/1141071000","districtKey":"seoul-seodaemun-gu","name":"북가좌제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/북가좌동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1141072000","aliasKey":"seoul-seodaemun-gu/admin/1141072000","districtKey":"seoul-seodaemun-gu","name":"북가좌제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"서대문구/법정동/북가좌동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"}],"approved":["sinchon-dong-yonsei-funeral-wreath","yeongcheon-dong-market-opening-wreath","hongeun-dong-seodaemun-arts-performance-wreath","sinchon-dong-yonsei-alumni-wedding-wreath"],"approvedDistinctUnitCount":3,"assetManifestSha256":"f388d88b827e5a1283e65ab1924437ffc7b3e675f497f584e90b7f11573d2ef2","assetSubstitutions":[{"alt":"근조 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":75206,"imagePath":"/images/products/funeral-basic.jpg","imageSha256":"7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3","key":"funeral-basic","mimeType":"image/jpeg","pageHtmlSha256":"403c7023aefc58c756a64b2ab2cd41e9512861bdf0763930aaa5854e9af30dfa","previousImagePath":"/images/products/funeral-basic.jpg","previousImageSha256":"7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B201/thumb-1_500x500.jpg","sku":"B201","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B201/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B201","verifiedAt":"2026-10-11T20:11:44.590498+00:00"},{"alt":"근조 고급 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":79304,"imagePath":"/images/products/funeral-premium.jpg","imageSha256":"0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114","key":"funeral-premium","mimeType":"image/jpeg","pageHtmlSha256":"18cde725eaac7f800c8ba6472c030021ae5241f4415c9ac70efd12cb1157fb48","previousImagePath":"/images/products/funeral-premium.jpg","previousImageSha256":"0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B203/thumb-1_500x500.jpg","sku":"B203","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B203/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B203","verifiedAt":"2026-10-11T20:11:44.891472+00:00"},{"alt":"근조 특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":86279,"imagePath":"/images/products/funeral-large.jpg","imageSha256":"1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e","key":"funeral-large","mimeType":"image/jpeg","pageHtmlSha256":"6e7602f055140c04134846a7a1e3cb67a40c6e2f63e76e0631e1108ac11b7cac","previousImagePath":"/images/products/funeral-large.jpg","previousImageSha256":"1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B205/thumb-1_500x500.jpg","sku":"B205","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B205/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B205","verifiedAt":"2026-10-11T20:11:45.040041+00:00"},{"alt":"근조 특특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":84178,"imagePath":"/images/products/funeral-xl.jpg","imageSha256":"a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3","key":"funeral-xl","mimeType":"image/jpeg","pageHtmlSha256":"1f5c2681dbd97e10fdb133b055d44b717223db6c18e8dd2668364d6b735a3dd2","previousImagePath":"/images/products/funeral-xl.jpg","previousImageSha256":"a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B060/thumb-1_500x500.jpg","sku":"B060","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B060/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B060","verifiedAt":"2026-10-11T20:11:44.779457+00:00"},{"alt":"축하 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":77336,"imagePath":"/images/products/congrats-basic.jpg","imageSha256":"0e5c0e37f5a02b0448a0dd9b3aa48c4bd1ebe38862a9dde662ef2e1c14eee905","key":"congrats-basic","mimeType":"image/jpeg","pageHtmlSha256":"ec4aab219118c16053b5aa2cfadebc32cd8482ac321894d3b8186ca9a99494c2","previousImagePath":"/images/products/congrats-basic.jpg","previousImageSha256":"0e5c0e37f5a02b0448a0dd9b3aa48c4bd1ebe38862a9dde662ef2e1c14eee905","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C200/thumb-1_500x500.jpg","sku":"C200","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C200/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C200","verifiedAt":"2026-10-11T20:11:54.294176+00:00"},{"alt":"축하 고급 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":77920,"imagePath":"/images/products/congrats-premium.jpg","imageSha256":"d3bd30015f4465f6db3d43c37a3088d383173e1bc0b46ff429ed24b9c251625a","key":"congrats-premium","mimeType":"image/jpeg","pageHtmlSha256":"101d1cfe9d92dc233fa79797590ed7e2c338f0f4d29ec1871cd050588b2526b9","previousImagePath":"/images/products/congrats-premium.jpg","previousImageSha256":"d3bd30015f4465f6db3d43c37a3088d383173e1bc0b46ff429ed24b9c251625a","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C203/thumb-1_500x500.jpg","sku":"C203","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C203/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C203","verifiedAt":"2026-10-11T20:11:54.518216+00:00"},{"alt":"축하 특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":83318,"imagePath":"/images/products/congrats-large.jpg","imageSha256":"05a71d0a3a624c7e27e0575baab02c21f87cc409a1de5389bd4c42b2789dc16d","key":"congrats-large","mimeType":"image/jpeg","pageHtmlSha256":"96ffa353681b32e23a0b4d7474b4b2d89dc9e566685d0b9eb6628de0c6cc110e","previousImagePath":"/images/products/congrats-large.jpg","previousImageSha256":"05a71d0a3a624c7e27e0575baab02c21f87cc409a1de5389bd4c42b2789dc16d","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C204/thumb-1_500x500.jpg","sku":"C204","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C204/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C204","verifiedAt":"2026-10-11T20:11:54.550688+00:00"},{"alt":"축하 특특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":85391,"imagePath":"/images/products/congrats-xl.jpg","imageSha256":"b0fa2c913adf258617e34ce0175cbdc282b83e6b47db556234380353c047d5e9","key":"congrats-xl","mimeType":"image/jpeg","pageHtmlSha256":"1dbee1c2b8be7e7c61c55d2d6646a9ca5f0cd08f278f8680461f1f56ddc55f84","previousImagePath":"/images/products/congrats-xl.jpg","previousImageSha256":"b0fa2c913adf258617e34ce0175cbdc282b83e6b47db556234380353c047d5e9","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C205/thumb-1_500x500.jpg","sku":"C205","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C205/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C205","verifiedAt":"2026-10-11T20:11:54.479476+00:00"}],"commonSourceSha256":{"src/components/ProductCards.astro":"7425a400057b1b55d899ead0e577d93a11bea5428968f3643b1120d2b48b2563","src/components/RegionDirectory.astro":"6568a2f2f31af9208163489cccbaded945586ca02c95097dea1dd9b6684b2103","src/pages/[category]/[slug].astro":"2679caee82bf6516f55cf5a9187a89b7ffffd26d2b027e6c60f67700bcc68edf","src/pages/[category]/index.astro":"d9404df13fb4a7da7dc82e19c2e6f434094aa18ab534f4f478f29fb7077a8c4b","src/pages/index.astro":"7adcbc7ccbf25746546f93eaebc79fd0b3412f3cd3814112c5f9db653d303338"},"contextBySlug":{"hongeun-dong-seodaemun-arts-performance-wreath":{"contextKey":"seodaemun-culture-sports-center|event-congrats-wreath","facilityKey":"seodaemun-culture-sports-center","intentKey":"seoul-seodaemun|seodaemun-culture-sports-center|event-congrats-wreath","purchaseIntentKey":"event-congrats-wreath"},"sinchon-dong-yonsei-alumni-wedding-wreath":{"contextKey":"yonsei-alumni-building|wedding-congrats-wreath","facilityKey":"yonsei-alumni-building","intentKey":"seoul-seodaemun|yonsei-alumni-building|wedding-congrats-wreath","purchaseIntentKey":"wedding-congrats-wreath"},"sinchon-dong-yonsei-funeral-wreath":{"contextKey":"yonsei-sinchon-funeral|funeral-condolence-wreath","facilityKey":"yonsei-sinchon-funeral","intentKey":"seoul-seodaemun|yonsei-sinchon-funeral|funeral-condolence-wreath","purchaseIntentKey":"funeral-condolence-wreath"},"yeongcheon-dong-market-opening-wreath":{"contextKey":"yeongcheon-market|opening-congrats-wreath","facilityKey":"yeongcheon-market","intentKey":"seoul-seodaemun|yeongcheon-market|opening-congrats-wreath","purchaseIntentKey":"opening-congrats-wreath"}},"facilities":[{"address":"서울특별시 서대문구 연세로 50 (신촌동 134)","facilityKey":"yonsei-sinchon-funeral","name":"연세대학교 신촌장례식장","sourceUrl":"https://www.yonseifuneral.com/am/am_3.asp","unitKey":"서대문구/법정동/신촌동"},{"address":"서울특별시 서대문구 영천시장길 27","facilityKey":"yeongcheon-market","name":"영천시장","sourceUrl":"https://www.sdm.go.kr/genre/economic/traditional/state.do","unitKey":"서대문구/법정동/영천동"},{"address":"서울특별시 서대문구 백련사길 39 (홍은동 산26-155)","facilityKey":"seodaemun-culture-sports-center","name":"서대문문화체육회관","sourceUrl":"https://cs.sscmc.or.kr/sdmcs/29","unitKey":"서대문구/법정동/홍은동"},{"address":"서울특별시 서대문구 연세로 50 (신촌동 134)","facilityKey":"yonsei-alumni-building","name":"연세대학교 동문회관","sourceUrl":"https://www.ysab.co.kr/index.php","unitKey":"서대문구/법정동/신촌동"}],"held":[],"membershipCounts":{"administrative":14,"legal":20,"relations":27},"membershipSourceSha256":"6aca22196ef15ce016aa6e7fd372b541f0cc669bd5f4e0d5a4e624ee50c673cf","partialRelationCount":13,"partialUnitKeys":["서대문구/법정동/북아현동","서대문구/법정동/홍제동","서대문구/법정동/대현동","서대문구/법정동/홍은동","서대문구/법정동/북가좌동","서대문구/법정동/남가좌동"],"plannedDistinctUnitCount":3,"plannedUnitKeys":["서대문구/법정동/신촌동","서대문구/법정동/영천동","서대문구/법정동/홍은동","서대문구/법정동/신촌동"],"proofFile":"d7d0895e23d60da7c9d75883fdfd46bb.txt","queryEvidenceBySlug":{"hongeun-dong-seodaemun-arts-performance-wreath":{"canonicalFacility":{"address":"서울특별시 서대문구 백련사길 39 (홍은동 산26-155)","facilityKey":"seodaemun-culture-sports-center","name":"서대문문화체육회관","sourceUrl":"https://cs.sscmc.or.kr/sdmcs/29","unitKey":"서대문구/법정동/홍은동"},"facilityKey":"seodaemun-culture-sports-center","finding":"무대에 오르기까지 함께한 준비를 응원하는 단체의 축하 선물. 실제 축하4종 사진의 선호 분위기를 고르고 공연 주최측의 허용 수령 공간과 행사후 처리 일정은 짧게 확인한다.","purchaseIntentKey":"event-congrats-wreath","sourceProposalSha256":"b9423519bd7879c106e21a86b29456217cbf78599c48877e625aa0c9c196b8d3","sourceUrl":"https://cs.sscmc.or.kr/sdmcs/29","unitKey":"서대문구/법정동/홍은동"},"sinchon-dong-yonsei-alumni-wedding-wreath":{"canonicalFacility":{"address":"서울특별시 서대문구 연세로 50 (신촌동 134)","facilityKey":"yonsei-alumni-building","name":"연세대학교 동문회관","sourceUrl":"https://www.ysab.co.kr/index.php","unitKey":"서대문구/법정동/신촌동"},"facilityKey":"yonsei-alumni-building","finding":"두 사람의 새로운 일상을 축복하는 동문·친구의 선물. 실제 축하4종의 꽃색을 함께 고르고 예식 일정에 맞춰 상담한다. 장례식장과 같은 법정동·번지여도 완전히 다른 시설과 구매목적이므로 별개 문서다.","purchaseIntentKey":"wedding-congrats-wreath","sourceProposalSha256":"b9423519bd7879c106e21a86b29456217cbf78599c48877e625aa0c9c196b8d3","sourceUrl":"https://www.ysab.co.kr/index.php","unitKey":"서대문구/법정동/신촌동"},"sinchon-dong-yonsei-funeral-wreath":{"canonicalFacility":{"address":"서울특별시 서대문구 연세로 50 (신촌동 134)","facilityKey":"yonsei-sinchon-funeral","name":"연세대학교 신촌장례식장","sourceUrl":"https://www.yonseifuneral.com/am/am_3.asp","unitKey":"서대문구/법정동/신촌동"},"facilityKey":"yonsei-sinchon-funeral","finding":"유가족에게 전할 위로를 담아 실제 근조4종 사진의 색·배치와 정한 예산을 함께 비교한다. 참석하지 못하는 조문객도 현재 빈소와 전달 일정을 한 번에 상담할 수 있도록 한다.","purchaseIntentKey":"funeral-condolence-wreath","sourceProposalSha256":"b9423519bd7879c106e21a86b29456217cbf78599c48877e625aa0c9c196b8d3","sourceUrl":"https://www.yonseifuneral.com/am/am_3.asp","unitKey":"서대문구/법정동/신촌동"},"yeongcheon-dong-market-opening-wreath":{"canonicalFacility":{"address":"서울특별시 서대문구 영천시장길 27","facilityKey":"yeongcheon-market","name":"영천시장","sourceUrl":"https://www.sdm.go.kr/genre/economic/traditional/state.do","unitKey":"서대문구/법정동/영천동"},"facilityKey":"yeongcheon-market","finding":"처음 가게 문을 여는 지인의 시작을 응원하는 선물. 축하4종의 실제 꽃색과 매장에 둘 자리에 맞는 실제규격 상담을 연결한다.","purchaseIntentKey":"opening-congrats-wreath","sourceProposalSha256":"b9423519bd7879c106e21a86b29456217cbf78599c48877e625aa0c9c196b8d3","sourceUrl":"https://www.sdm.go.kr/genre/economic/traditional/state.do","unitKey":"서대문구/법정동/영천동"}},"representativeAssignment":"facility-purchase-context-v1","reviewedCommon":{"articleListingIntro":"축하할 소식이 생겼거나 조심스레 마음을 전하고 싶은 날, 목적에 맞는 안내를 만나보세요. 실제 상품 사진에서 원하는 꽃을 고르고 전화로 이야기를 이어가실 수 있습니다.","home":{"description":"신촌장례식장 조의, 영천시장 개업, 문화체육회관 공연과 연세동문회관 결혼식. 소중한 사람에게 보낼 화환을 사진과 가격으로 살펴보세요.","heading":"서대문에서 나누는 기쁨과 따뜻한 위로","heroParagraph":"오랜 친구의 결혼을 축복하는 동문회관, 첫 손님을 맞는 영천시장 가게, 연습의 결실을 펼치는 공연장, 조용히 위로를 전하는 신촌장례식장. 서대문구에서 꽃을 보내려는 마음에 맞춰 실제 상품을 살펴보세요.","title":"서대문구 화환 주문 | 꽃이랑"},"region":"서울특별시 서대문구","regionDirectory":{"heading":"꽃을 전할 서대문의 네 순간","intro":"축하와 조의의 뜻을 전할 장소를 골라보세요. 예식·개업·공연·장례의 서로 다른 순간에 어울리는 상품 선택과 편한 상담을 안내합니다."},"scope":"Seodaemun local customer copy only; no route/product/security change.","status":"AUTHOR_PROPOSAL_PENDING_INDEPENDENT_REVIEW"},"reviewedProductDescriptions":{"B060":"흰 꽃 바탕에 연분홍·노랑이 더해진 사진을 비교해 보세요.","B201":"흰 꽃 사이에 노란 꽃이 놓인 기본형 사진을 살펴보세요.","B203":"위쪽으로 이어지는 흰 꽃과 노란 꽃의 배치를 비교해 보세요.","B205":"상단의 노란 장식과 흰 꽃이 어우러진 사진을 살펴보세요.","C200":"빨강·분홍과 노란 꽃이 어우러진 사진에서 원하는 색감을 찾아보세요.","C203":"가운데 노란 꽃이 강조된 사진을 보고 축하 선물의 분위기를 골라보세요.","C204":"노란 꽃과 여러 색의 둥근 꽃이 어우러진 모습을 살펴보세요.","C205":"노랑·분홍 꽃이 둥글게 이어지는 사진을 보며 축하 선물을 골라보세요."},"runtimeRegionsSha256":"fc3f08e4807703882097c0c96a9e27e6f7d9487c6940a9dd9ad06e5e1b460723","slugs":["sinchon-dong-yonsei-funeral-wreath","yeongcheon-dong-market-opening-wreath","hongeun-dong-seodaemun-arts-performance-wreath","sinchon-dong-yonsei-alumni-wedding-wreath"],"unitKeys":["서대문구/법정동/충정로2가","서대문구/법정동/충정로3가","서대문구/법정동/합동","서대문구/법정동/미근동","서대문구/법정동/냉천동","서대문구/법정동/천연동","서대문구/법정동/옥천동","서대문구/법정동/영천동","서대문구/법정동/현저동","서대문구/법정동/북아현동","서대문구/법정동/홍제동","서대문구/법정동/대현동","서대문구/법정동/대신동","서대문구/법정동/신촌동","서대문구/법정동/봉원동","서대문구/법정동/창천동","서대문구/법정동/연희동","서대문구/법정동/홍은동","서대문구/법정동/북가좌동","서대문구/법정동/남가좌동"],"unitTypeCounts":{"eup":0,"legal-dong":20,"myeon":0}};







const priorRegionPattern=/은평구|eunpyeong|노원구|nowon|강북구|gangbuk|도봉구|dobong|성북구|seongbuk|동대문구|dongdaemun|중랑구|jungnang|광진구|gwangjin|성동구|seongdong|용산구|yongsan|중구|seoul-jung(?!nang)|종로|jongno|양평|yangpyeong|가평|연천|(?<![가-힣])여주|포천|남양주|양주|김포|광주시|광주광역시|안성|이천(?!리)|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:gapyeong|yeoncheon|yeoju|pocheon|namyangju|yangju|gimpo|gwangju|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/;
test('Seoul Seodaemun-gu complete official membership stays separate from frozen purchase-intent N',()=>{
 const pages=read('pages'),c=read('region-coverage'),policy=read('region-policy');
 assert.deepEqual(pages.map(p=>p.slug),expected.approved);
 assert.deepEqual(c.units.map(u=>u.unitKey),expected.unitKeys);
 assert.deepEqual(c.administrativeCrosswalk,expected.administrativeCrosswalk);
 assert.equal(c.membershipSourceSha256,expected.membershipSourceSha256);
 assert.equal(c.units.length,expected.membershipCounts.legal);assert.equal(c.administrativeCrosswalk.length,expected.membershipCounts.administrative);
 assert.equal(c.representatives.length,expected.slugs.length);
 assert.equal(c.districts.length,1);assert.equal(c.districts[0].name,'서대문구');
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
test('Seoul Seodaemun-gu customer wording is allowed while copied prior-site names remain rejected',()=>{
 assert.doesNotMatch('서울 서대문구 신촌동과 영천동, 홍은동 주문 안내',priorRegionPattern);
 assert.doesNotMatch('상품을 보여주는 사진',priorRegionPattern);
 assert.doesNotMatch('https://seoul-seodaemun.fwith.kr/',priorRegionPattern);
 for(const copied of ['강북구','도봉구','https://seoul-gangbuk.fwith.kr/','https://seoul-dobong.fwith.kr/','https://seoul-jung.fwith.kr/','https://seoul-jungnang.fwith.kr/','중랑구','서울 중구','동대문구','seoul-dongdaemun'])assert.match(copied,priorRegionPattern);
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
  assert.equal(r.intentKey,`seoul-seodaemun|${r.contextKey}`);
  const facility=c.facilities.find(f=>f.facilityKey===r.facilityKey);assert.ok(facility);assert.deepEqual(r.unitKeys,[facility.unitKey]);
  if(r.status!=='approved')continue;
  for(const rows of [pages,m.pages,a.pages,pm.pages]){const page=rows.find(p=>p.pageKey===r.pageKey);assert.ok(page);for(const key of ['facilityKey','purchaseIntentKey','contextKey','intentKey'])assert.equal(page[key],binding[key]);assert.deepEqual(page.regionUnitKeys,r.unitKeys);}
 }
});

test('Seodaemun common purchase copy leads with purpose and choice while keeping delivery limits',()=>{
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
