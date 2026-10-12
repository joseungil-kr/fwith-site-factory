import {readHistoricalBannerSource} from './shared-banner-amendment.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';
import {validateGraph,loadGraph} from '../scripts/qa_graph.mjs';
import {pageSources} from '../src/lib/sources.mjs';
import {validateDefinition,directoryGroups} from '../src/lib/regions.mjs';
const read=name=>JSON.parse(readHistoricalBannerSource(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const expected={"administrativeCrosswalk":[{"administrativeCode":"1138051000","aliasKey":"seoul-eunpyeong-gu/admin/1138051000","districtKey":"seoul-eunpyeong-gu","name":"녹번동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/녹번동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"},{"administrativeCode":"1138052000","aliasKey":"seoul-eunpyeong-gu/admin/1138052000","districtKey":"seoul-eunpyeong-gu","name":"불광제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/불광동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"},{"administrativeCode":"1138053000","aliasKey":"seoul-eunpyeong-gu/admin/1138053000","districtKey":"seoul-eunpyeong-gu","name":"불광제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/불광동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"},{"administrativeCode":"1138055100","aliasKey":"seoul-eunpyeong-gu/admin/1138055100","districtKey":"seoul-eunpyeong-gu","name":"갈현제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/갈현동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"},{"administrativeCode":"1138055200","aliasKey":"seoul-eunpyeong-gu/admin/1138055200","districtKey":"seoul-eunpyeong-gu","name":"갈현제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/갈현동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"},{"administrativeCode":"1138056000","aliasKey":"seoul-eunpyeong-gu/admin/1138056000","districtKey":"seoul-eunpyeong-gu","name":"구산동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/구산동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"},{"administrativeCode":"1138057000","aliasKey":"seoul-eunpyeong-gu/admin/1138057000","districtKey":"seoul-eunpyeong-gu","name":"대조동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/대조동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"},{"administrativeCode":"1138058000","aliasKey":"seoul-eunpyeong-gu/admin/1138058000","districtKey":"seoul-eunpyeong-gu","name":"응암제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/응암동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"},{"administrativeCode":"1138059000","aliasKey":"seoul-eunpyeong-gu/admin/1138059000","districtKey":"seoul-eunpyeong-gu","name":"응암제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/응암동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"},{"administrativeCode":"1138060000","aliasKey":"seoul-eunpyeong-gu/admin/1138060000","districtKey":"seoul-eunpyeong-gu","name":"응암제3동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/응암동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"},{"administrativeCode":"1138062500","aliasKey":"seoul-eunpyeong-gu/admin/1138062500","districtKey":"seoul-eunpyeong-gu","name":"역촌동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/역촌동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"},{"administrativeCode":"1138063100","aliasKey":"seoul-eunpyeong-gu/admin/1138063100","districtKey":"seoul-eunpyeong-gu","name":"신사제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/신사동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"},{"administrativeCode":"1138063200","aliasKey":"seoul-eunpyeong-gu/admin/1138063200","districtKey":"seoul-eunpyeong-gu","name":"신사제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/신사동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"},{"administrativeCode":"1138064000","aliasKey":"seoul-eunpyeong-gu/admin/1138064000","districtKey":"seoul-eunpyeong-gu","name":"증산동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/증산동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"},{"administrativeCode":"1138065000","aliasKey":"seoul-eunpyeong-gu/admin/1138065000","districtKey":"seoul-eunpyeong-gu","name":"수색동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/수색동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"},{"administrativeCode":"1138069000","aliasKey":"seoul-eunpyeong-gu/admin/1138069000","districtKey":"seoul-eunpyeong-gu","name":"진관동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109","unitKey":"은평구/법정동/진관동"}],"sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=130109"}],"approved":["jingwan-dong-eunpyeong-st-mary-funeral-wreath","bulgwang-dong-yeonseo-market-opening-wreath","nokbeon-dong-eunpyeong-arts-performance-wreath","susaek-dong-seoul-arts-eunpyeong-wedding-wreath"],"approvedDistinctUnitCount":4,"assetManifestSha256":"0c3fd88f693706288dfeb0968fa4ebfdbecb1e3b5aeb32506560ea228274229d","assetSubstitutions":[{"alt":"근조 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":75206,"imagePath":"/images/products/funeral-basic.jpg","imageSha256":"7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3","key":"funeral-basic","mimeType":"image/jpeg","pageHtmlSha256":"dd899d25daa9b0038133f2b49083fe1c705c7769b0c205642d9eac0462dc4044","previousImagePath":"/images/products/funeral-basic.jpg","previousImageSha256":"7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B201/thumb-1_500x500.jpg","sku":"B201","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B201/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B201","verifiedAt":"2026-10-11T19:04:11.540114+00:00"},{"alt":"근조 고급 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":79304,"imagePath":"/images/products/funeral-premium.jpg","imageSha256":"0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114","key":"funeral-premium","mimeType":"image/jpeg","pageHtmlSha256":"a63c23ecce3518fb6a6437f4e5f6044a8b7afbd203cca01350f426c638e38638","previousImagePath":"/images/products/funeral-premium.jpg","previousImageSha256":"0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B203/thumb-1_500x500.jpg","sku":"B203","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B203/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B203","verifiedAt":"2026-10-11T19:04:11.769685+00:00"},{"alt":"근조 특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":86279,"imagePath":"/images/products/funeral-large.jpg","imageSha256":"1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e","key":"funeral-large","mimeType":"image/jpeg","pageHtmlSha256":"1985d1e5721058c4c70d2ea2681db855dab016b51917fa652fc7a0a3824e3281","previousImagePath":"/images/products/funeral-large.jpg","previousImageSha256":"1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B205/thumb-1_500x500.jpg","sku":"B205","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B205/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B205","verifiedAt":"2026-10-11T19:04:11.975529+00:00"},{"alt":"근조 특특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":84178,"imagePath":"/images/products/funeral-xl.jpg","imageSha256":"a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3","key":"funeral-xl","mimeType":"image/jpeg","pageHtmlSha256":"8881df9d30b78989afc79d8ba158a5e1a225ed30988279e046526f9132c881dc","previousImagePath":"/images/products/funeral-xl.jpg","previousImageSha256":"a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B060/thumb-1_500x500.jpg","sku":"B060","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B060/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B060","verifiedAt":"2026-10-11T19:04:11.745928+00:00"},{"alt":"축하 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":77336,"imagePath":"/images/products/congrats-basic.jpg","imageSha256":"0e5c0e37f5a02b0448a0dd9b3aa48c4bd1ebe38862a9dde662ef2e1c14eee905","key":"congrats-basic","mimeType":"image/jpeg","pageHtmlSha256":"d70d9335747897f6d2c8b39ddc2f36d249e92fdd5264ae1275c5294284720ca5","previousImagePath":"/images/products/congrats-basic.jpg","previousImageSha256":"0e5c0e37f5a02b0448a0dd9b3aa48c4bd1ebe38862a9dde662ef2e1c14eee905","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C200/thumb-1_500x500.jpg","sku":"C200","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C200/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C200","verifiedAt":"2026-10-11T19:04:22.832036+00:00"},{"alt":"축하 고급 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":77920,"imagePath":"/images/products/congrats-premium.jpg","imageSha256":"d3bd30015f4465f6db3d43c37a3088d383173e1bc0b46ff429ed24b9c251625a","key":"congrats-premium","mimeType":"image/jpeg","pageHtmlSha256":"9451e934dc686095c75a301287e93d729e607b6eef89a8c8668bda155664916a","previousImagePath":"/images/products/congrats-premium.jpg","previousImageSha256":"d3bd30015f4465f6db3d43c37a3088d383173e1bc0b46ff429ed24b9c251625a","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C203/thumb-1_500x500.jpg","sku":"C203","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C203/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C203","verifiedAt":"2026-10-11T19:04:22.811197+00:00"},{"alt":"축하 특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":83318,"imagePath":"/images/products/congrats-large.jpg","imageSha256":"05a71d0a3a624c7e27e0575baab02c21f87cc409a1de5389bd4c42b2789dc16d","key":"congrats-large","mimeType":"image/jpeg","pageHtmlSha256":"8726f32f5bf3edc2021a6e87c55c1ed9dd6790c69a06547a1bf8d84d52828d0d","previousImagePath":"/images/products/congrats-large.jpg","previousImageSha256":"05a71d0a3a624c7e27e0575baab02c21f87cc409a1de5389bd4c42b2789dc16d","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C204/thumb-1_500x500.jpg","sku":"C204","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C204/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C204","verifiedAt":"2026-10-11T19:04:22.623147+00:00"},{"alt":"축하 특특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":85391,"imagePath":"/images/products/congrats-xl.jpg","imageSha256":"b0fa2c913adf258617e34ce0175cbdc282b83e6b47db556234380353c047d5e9","key":"congrats-xl","mimeType":"image/jpeg","pageHtmlSha256":"e527447f8de044a5452e4da6bf7281f2d452004f3df07a3d017d0e84ed7ebc6c","previousImagePath":"/images/products/congrats-xl.jpg","previousImageSha256":"b0fa2c913adf258617e34ce0175cbdc282b83e6b47db556234380353c047d5e9","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C205/thumb-1_500x500.jpg","sku":"C205","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C205/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C205","verifiedAt":"2026-10-11T19:04:22.821666+00:00"}],"commonSourceSha256":{"src/components/ProductCards.astro":"7425a400057b1b55d899ead0e577d93a11bea5428968f3643b1120d2b48b2563","src/components/RegionDirectory.astro":"81e059b20f68f08a1a5666d2da80adbccb18836fb4f664984289aaf6dfaaa86a","src/pages/[category]/[slug].astro":"2679caee82bf6516f55cf5a9187a89b7ffffd26d2b027e6c60f67700bcc68edf","src/pages/[category]/index.astro":"96ca62ff3dc6085f878a9d718b24a9e7a1ccafdf701a0499194da12b4dff77db","src/pages/index.astro":"be2eabefe1e0cad9a2b38d4f13b422ef9f492df905b734082862a5111d2845a9"},"contextBySlug":{"bulgwang-dong-yeonseo-market-opening-wreath":{"contextKey":"yeonseo-market|opening-congrats-wreath","facilityKey":"yeonseo-market","intentKey":"seoul-eunpyeong|yeonseo-market|opening-congrats-wreath","purchaseIntentKey":"opening-congrats-wreath"},"jingwan-dong-eunpyeong-st-mary-funeral-wreath":{"contextKey":"eunpyeong-st-mary-funeral|funeral-condolence-wreath","facilityKey":"eunpyeong-st-mary-funeral","intentKey":"seoul-eunpyeong|eunpyeong-st-mary-funeral|funeral-condolence-wreath","purchaseIntentKey":"funeral-condolence-wreath"},"nokbeon-dong-eunpyeong-arts-performance-wreath":{"contextKey":"eunpyeong-culture-arts-center|event-congrats-wreath","facilityKey":"eunpyeong-culture-arts-center","intentKey":"seoul-eunpyeong|eunpyeong-culture-arts-center|event-congrats-wreath","purchaseIntentKey":"event-congrats-wreath"},"susaek-dong-seoul-arts-eunpyeong-wedding-wreath":{"contextKey":"seoul-arts-education-center-eunpyeong|wedding-congrats-wreath","facilityKey":"seoul-arts-education-center-eunpyeong","intentKey":"seoul-eunpyeong|seoul-arts-education-center-eunpyeong|wedding-congrats-wreath","purchaseIntentKey":"wedding-congrats-wreath"}},"facilities":[{"address":"서울특별시 은평구 통일로 1021(진관동)","facilityKey":"eunpyeong-st-mary-funeral","name":"은평성모장례식장","sourceUrl":"https://www.cmcep.or.kr/page/main","unitKey":"은평구/법정동/진관동"},{"address":"서울특별시 은평구 통일로 850(불광동, 연서시장)","facilityKey":"yeonseo-market","name":"연서시장","sourceUrl":"https://korean.visitseoul.net/shopping/%EC%97%B0%EC%84%9C%EC%8B%9C%EC%9E%A5/KOP028254","unitKey":"은평구/법정동/불광동"},{"address":"서울특별시 은평구 녹번로 16(녹번동)","facilityKey":"eunpyeong-culture-arts-center","name":"은평문화예술회관","sourceUrl":"https://efac.or.kr/page06/sub0103.php","unitKey":"은평구/법정동/녹번동"},{"address":"서울특별시 은평구 수색로 322-2(수색동 358-10)","facilityKey":"seoul-arts-education-center-eunpyeong","name":"서울문화예술교육센터 은평","sourceUrl":"https://www.sfac.or.kr/site/SFAC_KOR/10/11037020000002024072904.jsp","unitKey":"은평구/법정동/수색동"}],"held":[],"membershipCounts":{"administrative":16,"legal":11,"relations":16},"membershipSourceSha256":"2fedb1e2353ae9ef1d8441ead7d93734bf01effb0faa9cff2e9133f72ca32d57","partialRelationCount":9,"partialUnitKeys":["은평구/법정동/불광동","은평구/법정동/갈현동","은평구/법정동/응암동","은평구/법정동/신사동"],"plannedDistinctUnitCount":4,"plannedUnitKeys":["은평구/법정동/진관동","은평구/법정동/불광동","은평구/법정동/녹번동","은평구/법정동/수색동"],"proofFile":"d7e9dfc9284537fc424b4b25376b4c17.txt","queryEvidenceBySlug":{"bulgwang-dong-yeonseo-market-opening-wreath":{"canonicalFacility":{"address":"서울특별시 은평구 통일로 850(불광동, 연서시장)","facilityKey":"yeonseo-market","name":"연서시장","sourceUrl":"https://korean.visitseoul.net/shopping/%EC%97%B0%EC%84%9C%EC%8B%9C%EC%9E%A5/KOP028254","unitKey":"은평구/법정동/불광동"},"facilityKey":"yeonseo-market","finding":"점포 앞에 축하화환을 두려는 용도와 예산에 맞춰 실제 네 상품을 비교하고, 받는 점포의 공간과 수령 일정에 맞춰 상담한다.","measuredSearchVolume":null,"purchaseIntentKey":"opening-congrats-wreath","sourceProposalSha256":"3d9f81bf7a8236c578a8e2a24c00259d4e915149c7be954267459f4d829dad5b","sourceUrl":"https://korean.visitseoul.net/shopping/%EC%97%B0%EC%84%9C%EC%8B%9C%EC%9E%A5/KOP028254","unitKey":"은평구/법정동/불광동"},"jingwan-dong-eunpyeong-st-mary-funeral-wreath":{"canonicalFacility":{"address":"서울특별시 은평구 통일로 1021(진관동)","facilityKey":"eunpyeong-st-mary-funeral","name":"은평성모장례식장","sourceUrl":"https://www.cmcep.or.kr/page/main","unitKey":"은평구/법정동/진관동"},"facilityKey":"eunpyeong-st-mary-funeral","finding":"근조 네 상품의 실제 가격·사진으로 예산을 정한 뒤, 은평성모장례식장의 빈소와 발인 일정에 맞는 전달을 상담한다.","measuredSearchVolume":null,"purchaseIntentKey":"funeral-condolence-wreath","sourceProposalSha256":"3d9f81bf7a8236c578a8e2a24c00259d4e915149c7be954267459f4d829dad5b","sourceUrl":"https://www.cmcep.or.kr/page/main","unitKey":"은평구/법정동/진관동"},"nokbeon-dong-eunpyeong-arts-performance-wreath":{"canonicalFacility":{"address":"서울특별시 은평구 녹번로 16(녹번동)","facilityKey":"eunpyeong-culture-arts-center","name":"은평문화예술회관","sourceUrl":"https://efac.or.kr/page06/sub0103.php","unitKey":"은평구/법정동/녹번동"},"facilityKey":"eunpyeong-culture-arts-center","finding":"공연팀이 받을 수 있는 화환인지 간단히 맞춘 뒤, 공연 축하의 마음과 예산에 맞는 실제 상품을 골라 전달 시점을 상담한다.","measuredSearchVolume":null,"purchaseIntentKey":"event-congrats-wreath","sourceProposalSha256":"3d9f81bf7a8236c578a8e2a24c00259d4e915149c7be954267459f4d829dad5b","sourceUrl":"https://efac.or.kr/page06/sub0103.php","unitKey":"은평구/법정동/녹번동"},"susaek-dong-seoul-arts-eunpyeong-wedding-wreath":{"canonicalFacility":{"address":"서울특별시 은평구 수색로 322-2(수색동 358-10)","facilityKey":"seoul-arts-education-center-eunpyeong","name":"서울문화예술교육센터 은평","sourceUrl":"https://www.sfac.or.kr/site/SFAC_KOR/10/11037020000002024072904.jsp","unitKey":"은평구/법정동/수색동"},"facilityKey":"seoul-arts-education-center-eunpyeong","finding":"공공예식에 외부 축하화환을 받을 수 있는지 예식 담당자와 먼저 짧게 맞추고, 예산별 네 상품 중 마음에 맞는 상품을 고른다. 예식 장식 계약과 별개인 축하 선물 주문이다.","measuredSearchVolume":null,"purchaseIntentKey":"wedding-congrats-wreath","sourceProposalSha256":"3d9f81bf7a8236c578a8e2a24c00259d4e915149c7be954267459f4d829dad5b","sourceUrl":"https://www.sfac.or.kr/site/SFAC_KOR/10/11037020000002024072904.jsp","unitKey":"은평구/법정동/수색동"}},"representativeAssignment":"facility-purchase-context-v1","reviewedCommon":{"articleListingIntro":"받는 사람과 그날의 의미를 떠올리며 골라 보세요. 각 안내에서 실제 상품 사진과 가격, 그 자리에 필요한 짧은 주문 정보를 함께 살펴보실 수 있습니다.","home":{"description":"연서시장 새 가게의 출발부터 공연과 결혼식의 축하, 은평성모장례식장에 전할 조의까지. 자리와 마음에 맞는 화환을 꽃이랑에서 살펴보세요.","heading":"은평에서 전하는 축하와 조의의 마음","heroParagraph":"문을 여는 가게에 힘을 보태고, 기다려 온 무대에 박수를 보내고, 두 사람의 앞날을 함께 기뻐합니다. 은평에서 마음을 전할 자리가 정해졌다면 원하는 꽃부터 살펴보세요. 조심스러운 위로가 필요한 날에도 상품과 전달 일정을 편하게 상담하실 수 있습니다.","title":"은평구 화환 주문 | 꽃이랑"},"region":"서울특별시 은평구","regionDirectory":{"heading":"마음을 전할 은평의 자리","intro":"은평성모장례식장의 조의, 연서시장 개업의 응원, 은평문화예술회관 공연의 축하, 서울문화예술교육센터 은평 예식의 축복을 준비했습니다. 보내는 이유에 맞는 안내에서 상품과 상담 방법을 만나보세요."},"scope":"Only Eunpyeong-local customer hero and directory intro; no code, routes, product names, prices or business policies changed.","status":"AUTHOR_PROPOSAL_PENDING_INDEPENDENT_REVIEW"},"reviewedProductDescriptions":{"B060":"흰 꽃 바탕에 연분홍·노랑이 더해진 사진을 비교해 보세요.","B201":"흰 꽃 사이에 노란 꽃이 놓인 기본형 사진을 살펴보세요.","B203":"위쪽으로 이어지는 흰 꽃과 노란 꽃의 배치를 비교해 보세요.","B205":"상단의 노란 장식과 흰 꽃이 어우러진 사진을 살펴보세요.","C200":"빨강·분홍과 노란 꽃이 어우러진 사진에서 원하는 색감을 찾아보세요.","C203":"가운데 노란 꽃이 강조된 사진을 보고 축하 선물의 분위기를 골라보세요.","C204":"노란 꽃과 여러 색의 둥근 꽃이 어우러진 모습을 살펴보세요.","C205":"노랑·분홍 꽃이 둥글게 이어지는 사진을 보며 축하 선물을 골라보세요."},"runtimeRegionsSha256":"bfb941ac0663b4d4578f100eb8e5c4f410597cb85c9907151df1a3b76abce080","slugs":["jingwan-dong-eunpyeong-st-mary-funeral-wreath","bulgwang-dong-yeonseo-market-opening-wreath","nokbeon-dong-eunpyeong-arts-performance-wreath","susaek-dong-seoul-arts-eunpyeong-wedding-wreath"],"unitKeys":["은평구/법정동/수색동","은평구/법정동/녹번동","은평구/법정동/불광동","은평구/법정동/갈현동","은평구/법정동/구산동","은평구/법정동/대조동","은평구/법정동/응암동","은평구/법정동/역촌동","은평구/법정동/신사동","은평구/법정동/증산동","은평구/법정동/진관동"],"unitTypeCounts":{"eup":0,"legal-dong":11,"myeon":0}};







const priorRegionPattern=/노원구|nowon|강북구|gangbuk|도봉구|dobong|성북구|seongbuk|동대문구|dongdaemun|중랑구|jungnang|광진구|gwangjin|성동구|seongdong|용산구|yongsan|중구|seoul-jung(?!nang)|종로|jongno|양평|yangpyeong|가평|연천|(?<![가-힣])여주|포천|남양주|양주|김포|광주시|광주광역시|안성|이천(?!리)|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:gapyeong|yeoncheon|yeoju|pocheon|namyangju|yangju|gimpo|gwangju|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/;
test('Seoul Eunpyeong-gu complete official membership stays separate from frozen purchase-intent N',()=>{
 const pages=read('pages'),c=read('region-coverage'),policy=read('region-policy');
 assert.deepEqual(pages.map(p=>p.slug),expected.approved);
 assert.deepEqual(c.units.map(u=>u.unitKey),expected.unitKeys);
 assert.deepEqual(c.administrativeCrosswalk,expected.administrativeCrosswalk);
 assert.equal(c.membershipSourceSha256,expected.membershipSourceSha256);
 assert.equal(c.units.length,expected.membershipCounts.legal);assert.equal(c.administrativeCrosswalk.length,expected.membershipCounts.administrative);
 assert.equal(c.representatives.length,expected.slugs.length);
 assert.equal(c.districts.length,1);assert.equal(c.districts[0].name,'은평구');
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
 assert.equal(sha(readHistoricalBannerSource(new URL('../src/lib/regions.mjs',import.meta.url))),expected.runtimeRegionsSha256);
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
 const source=readHistoricalBannerSource(new URL('../src/components/RegionDirectory.astro',import.meta.url),'utf8');
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
test('Seoul Eunpyeong-gu customer wording is allowed while copied prior-site names remain rejected',()=>{
 assert.doesNotMatch('서울 은평구 진관동과 불광동, 녹번동, 수색동 주문 안내',priorRegionPattern);
 assert.doesNotMatch('상품을 보여주는 사진',priorRegionPattern);
 assert.doesNotMatch('https://seoul-eunpyeong.fwith.kr/',priorRegionPattern);
 for(const copied of ['강북구','도봉구','https://seoul-gangbuk.fwith.kr/','https://seoul-dobong.fwith.kr/','https://seoul-jung.fwith.kr/','https://seoul-jungnang.fwith.kr/','중랑구','서울 중구','동대문구','seoul-dongdaemun'])assert.match(copied,priorRegionPattern);
 for(const copied of ['양평군 꽃배달','https://yangpyeong.fwith.kr/','가평군 꽃배달','https://gapyeong.fwith.kr/','여주시 꽃배달','여주 꽃배달','이천시 꽃배달','이천 꽃배달','https://icheon.fwith.kr/regions/example/','연천군 꽃배달','https://yeoju.fwith.kr/'])
  assert.match(copied,priorRegionPattern);
});
test('public ownership proof is unique and specific to this source',()=>{
 const root=new URL('../public/',import.meta.url);const matches=fs.readdirSync(root).filter(n=>/^[0-9a-f]{32}\.txt$/.test(n));
 assert.deepEqual(matches,[expected.proofFile]);assert.notEqual(matches[0],"cefb94457c510a65e3052f70bf843a5e.txt");assert.notEqual(matches[0],'29a79c8ebd0e44a9c81400fd74a93cbc.txt');assert.notEqual(matches[0],'dc766c6c4235b6ffe33d9f7efebc9a77.txt');
 assert.equal(readHistoricalBannerSource(new URL(matches[0],root),'utf8'),matches[0].slice(0,-4)+'\n');
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
 const cards=readHistoricalBannerSource(new URL('../src/components/ProductCards.astro',import.meta.url),'utf8');
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
  assert.equal(sha(readHistoricalBannerSource(new URL('../public'+asset.imagePath,import.meta.url))),asset.imageSha256);
  assert.equal(row.image.sha256,asset.imageSha256);assert.equal(row.sourceImageUrl,asset.sourceImageUrl);assert.equal(row.sourceImageHttpStatus,200);
  assert.deepEqual(row.image.dimensions,asset.dimensions);assert.equal(row.image.type,asset.mimeType);assert.equal(row.previousImageSha256,asset.previousImageSha256);
  assert.equal(p.desc,expected.reviewedProductDescriptions[p.officialSku]);
 }
 assert.match(read('business-truth').deliveryNotice,/실제 배송지 주소.*추가 배송비.*최종 결제금액.*주문 전에.*확인/);
 const cardsSource=readHistoricalBannerSource(new URL('../src/components/ProductCards.astro',import.meta.url),'utf8');
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
  assert.equal(r.intentKey,`seoul-eunpyeong|${r.contextKey}`);
  const facility=c.facilities.find(f=>f.facilityKey===r.facilityKey);assert.ok(facility);assert.deepEqual(r.unitKeys,[facility.unitKey]);
  if(r.status!=='approved')continue;
  for(const rows of [pages,m.pages,a.pages,pm.pages]){const page=rows.find(p=>p.pageKey===r.pageKey);assert.ok(page);for(const key of ['facilityKey','purchaseIntentKey','contextKey','intentKey'])assert.equal(page[key],binding[key]);assert.deepEqual(page.regionUnitKeys,r.unitKeys);}
 }
});

test('Eunpyeong common purchase copy leads with purpose and choice while keeping delivery limits',()=>{
 const home=readHistoricalBannerSource(new URL('../src/pages/index.astro',import.meta.url),'utf8');
 const directory=readHistoricalBannerSource(new URL('../src/components/RegionDirectory.astro',import.meta.url),'utf8');
 const banner=readHistoricalBannerSource(new URL('../src/components/InlineOrderBanner.astro',import.meta.url),'utf8');
 const truth=read('business-truth');
 assert.ok(home.includes(expected.reviewedCommon.home.heroParagraph));assert.match(home,/예산에 맞는 화환/);
 assert.ok(directory.includes(expected.reviewedCommon.regionDirectory.intro));assert.doesNotMatch(directory,/작성되었다는 뜻이 아닙니다/);
 assert.match(banner,/상품 선택이 어려우시면/);assert.match(banner,/상담시간과 실제 전달시간은 다를 수 있어요/); for(const term of ['전달 일정','반입 조건','추가비용','주문할 때 함께 확인'])assert.ok(banner.includes(term));
 for(const term of ['기본가격','추가 배송비','배송·반입 가능 여부','요청 시간','최종 결제금액','주문 전'])assert.ok(truth.deliveryNotice.includes(term));
});

test('independently reviewed shared customer copy stays exact in generated sources',()=>{
 for(const [name,digest] of Object.entries(expected.commonSourceSha256))assert.equal(sha(readHistoricalBannerSource(new URL('../'+name,import.meta.url))),digest,name);
 const detail=readHistoricalBannerSource(new URL('../src/pages/[category]/[slug].astro',import.meta.url),'utf8');
 const cards=readHistoricalBannerSource(new URL('../src/components/ProductCards.astro',import.meta.url),'utf8');
 for(const field of ['{source.name}','sourceTypeLabels[source.type as keyof typeof sourceTypeLabels]','href={source.url}','datetime={source.verifiedAt}'])assert.ok(detail.includes(field),field);
 assert.doesNotMatch(detail,/상품 구성·배송조건이나 시설 반입 가능 여부는 주문 전에 해당 담당자에게 확인/);
 assert.equal((cards.match(/리본 문구는 보내는 목적에 맞춰 상담하실 수 있습니다/g)||[]).length,1);
 assert.doesNotMatch(cards,/p.family==='congrats'/);
 assert.ok(cards.includes('{site.productVariationNotice} {site.deliveryNotice}'));
});
