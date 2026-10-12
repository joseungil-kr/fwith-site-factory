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
const expected={"administrativeCrosswalk":[{"administrativeCode":"1144055500","aliasKey":"seoul-mapo-gu/admin/1144055500","districtKey":"seoul-mapo-gu","name":"아현동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/아현동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/공덕동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/염리동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1144056500","aliasKey":"seoul-mapo-gu/admin/1144056500","districtKey":"seoul-mapo-gu","name":"공덕동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/아현동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/공덕동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/신공덕동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/도화동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1144058500","aliasKey":"seoul-mapo-gu/admin/1144058500","districtKey":"seoul-mapo-gu","name":"도화동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/도화동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/마포동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1144059000","aliasKey":"seoul-mapo-gu/admin/1144059000","districtKey":"seoul-mapo-gu","name":"용강동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/도화동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/용강동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/토정동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/마포동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/대흥동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/염리동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1144060000","aliasKey":"seoul-mapo-gu/admin/1144060000","districtKey":"seoul-mapo-gu","name":"대흥동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/대흥동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/노고산동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/신수동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1144061000","aliasKey":"seoul-mapo-gu/admin/1144061000","districtKey":"seoul-mapo-gu","name":"염리동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/공덕동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/염리동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1144063000","aliasKey":"seoul-mapo-gu/admin/1144063000","districtKey":"seoul-mapo-gu","name":"신수동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/대흥동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/신수동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/현석동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/구수동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/신정동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1144065500","aliasKey":"seoul-mapo-gu/admin/1144065500","districtKey":"seoul-mapo-gu","name":"서강동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/창전동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/상수동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/하중동"},{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/신정동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/당인동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1144066000","aliasKey":"seoul-mapo-gu/admin/1144066000","districtKey":"seoul-mapo-gu","name":"서교동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/노고산동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/서교동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/동교동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1144068000","aliasKey":"seoul-mapo-gu/admin/1144068000","districtKey":"seoul-mapo-gu","name":"합정동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/합정동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1144069000","aliasKey":"seoul-mapo-gu/admin/1144069000","districtKey":"seoul-mapo-gu","name":"망원제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/망원동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1144070000","aliasKey":"seoul-mapo-gu/admin/1144070000","districtKey":"seoul-mapo-gu","name":"망원제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/망원동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1144071000","aliasKey":"seoul-mapo-gu/admin/1144071000","districtKey":"seoul-mapo-gu","name":"연남동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/연남동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1144072000","aliasKey":"seoul-mapo-gu/admin/1144072000","districtKey":"seoul-mapo-gu","name":"성산제1동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/성산동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1144073000","aliasKey":"seoul-mapo-gu/admin/1144073000","districtKey":"seoul-mapo-gu","name":"성산제2동","relations":[{"scope":"partial","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/성산동"},{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/중동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"},{"administrativeCode":"1144074000","aliasKey":"seoul-mapo-gu/admin/1144074000","districtKey":"seoul-mapo-gu","name":"상암동","relations":[{"scope":"whole","sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1","unitKey":"마포구/법정동/상암동"}],"sourceUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_0014963057q_I4g&fileSn=1"}],"approved":["mangwon-dong-mangwon-market-opening-wreath","sangam-dong-dmc-office-move-wreath","daeheung-dong-mapo-arts-performance-wreath"],"approvedDistinctUnitCount":3,"assetManifestSha256":"110e96be9e2d28dadcce3a5be5b14ae521340ebaa1ae83cadd905ec6eb9a82f0","assetSubstitutions":[{"alt":"근조 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":75206,"imagePath":"/images/products/funeral-basic.jpg","imageSha256":"7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3","key":"funeral-basic","mimeType":"image/jpeg","pageHtmlSha256":"444a5f3f5a615b6d413afaae0125e89fd4fc27861f2de792bab6e64dd9847a04","previousImagePath":"/images/products/funeral-basic.jpg","previousImageSha256":"7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B201/thumb-1_500x500.jpg","sku":"B201","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B201/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B201","verifiedAt":"2026-10-11T21:09:47.057151+00:00"},{"alt":"근조 고급 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":79304,"imagePath":"/images/products/funeral-premium.jpg","imageSha256":"0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114","key":"funeral-premium","mimeType":"image/jpeg","pageHtmlSha256":"b1433a0dfbb8d77cbb23c99684ba7dd3d7811a40034bf4b3b8f510b982120244","previousImagePath":"/images/products/funeral-premium.jpg","previousImageSha256":"0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B203/thumb-1_500x500.jpg","sku":"B203","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B203/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B203","verifiedAt":"2026-10-11T21:09:47.012024+00:00"},{"alt":"근조 특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":86279,"imagePath":"/images/products/funeral-large.jpg","imageSha256":"1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e","key":"funeral-large","mimeType":"image/jpeg","pageHtmlSha256":"3b441e2f42297493d6a5211e610489c46ca46a52ccdd71d5e4aa34714b9f5f2e","previousImagePath":"/images/products/funeral-large.jpg","previousImageSha256":"1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B205/thumb-1_500x500.jpg","sku":"B205","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B205/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B205","verifiedAt":"2026-10-11T21:09:46.794601+00:00"},{"alt":"근조 특특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":84178,"imagePath":"/images/products/funeral-xl.jpg","imageSha256":"a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3","key":"funeral-xl","mimeType":"image/jpeg","pageHtmlSha256":"1f5c2681dbd97e10fdb133b055d44b717223db6c18e8dd2668364d6b735a3dd2","previousImagePath":"/images/products/funeral-xl.jpg","previousImageSha256":"a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/B060/thumb-1_500x500.jpg","sku":"B060","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/B060/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=B060","verifiedAt":"2026-10-11T21:09:46.597031+00:00"},{"alt":"축하 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":77336,"imagePath":"/images/products/congrats-basic.jpg","imageSha256":"0e5c0e37f5a02b0448a0dd9b3aa48c4bd1ebe38862a9dde662ef2e1c14eee905","key":"congrats-basic","mimeType":"image/jpeg","pageHtmlSha256":"85b77046dfaef456e3964dc3cc0f3a90fa486e24ffb9075289bc05b1ca8a5278","previousImagePath":"/images/products/congrats-basic.jpg","previousImageSha256":"0e5c0e37f5a02b0448a0dd9b3aa48c4bd1ebe38862a9dde662ef2e1c14eee905","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C200/thumb-1_500x500.jpg","sku":"C200","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C200/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C200","verifiedAt":"2026-10-11T21:09:56.157653+00:00"},{"alt":"축하 고급 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":77920,"imagePath":"/images/products/congrats-premium.jpg","imageSha256":"d3bd30015f4465f6db3d43c37a3088d383173e1bc0b46ff429ed24b9c251625a","key":"congrats-premium","mimeType":"image/jpeg","pageHtmlSha256":"db7d94136f62b09e18d58d1bf14453964a52d69c747bda9996d736d0bcbd5c6c","previousImagePath":"/images/products/congrats-premium.jpg","previousImageSha256":"d3bd30015f4465f6db3d43c37a3088d383173e1bc0b46ff429ed24b9c251625a","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C203/thumb-1_500x500.jpg","sku":"C203","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C203/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C203","verifiedAt":"2026-10-11T21:09:56.109867+00:00"},{"alt":"축하 특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":83318,"imagePath":"/images/products/congrats-large.jpg","imageSha256":"05a71d0a3a624c7e27e0575baab02c21f87cc409a1de5389bd4c42b2789dc16d","key":"congrats-large","mimeType":"image/jpeg","pageHtmlSha256":"614c1815cddf6541dbb5756082888a8130d4dade1c3f7a1121131c463f7377f2","previousImagePath":"/images/products/congrats-large.jpg","previousImageSha256":"05a71d0a3a624c7e27e0575baab02c21f87cc409a1de5389bd4c42b2789dc16d","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C204/thumb-1_500x500.jpg","sku":"C204","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C204/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C204","verifiedAt":"2026-10-11T21:09:56.126426+00:00"},{"alt":"축하 특특대 3단 화환 공식 상품 사진","dimensions":[500,500],"imageBytes":85391,"imagePath":"/images/products/congrats-xl.jpg","imageSha256":"b0fa2c913adf258617e34ce0175cbdc282b83e6b47db556234380353c047d5e9","key":"congrats-xl","mimeType":"image/jpeg","pageHtmlSha256":"c95960464a7c28ca9116ece0523ed664b3e98e634da092d3cda8bbcc1ce2525c","previousImagePath":"/images/products/congrats-xl.jpg","previousImageSha256":"b0fa2c913adf258617e34ce0175cbdc282b83e6b47db556234380353c047d5e9","previousSourceImageUrl":"https://fwith.co.kr/data/item/flower379/C205/thumb-1_500x500.jpg","sku":"C205","sourceImageUrl":"https://fwith.co.kr/data/item/flower379/C205/thumb-1_500x500.jpg","sourceUrl":"https://fwith.co.kr/shop/item.php?it_id=C205","verifiedAt":"2026-10-11T21:09:56.010845+00:00"}],"commonSourceSha256":{"src/components/ProductCards.astro":"7425a400057b1b55d899ead0e577d93a11bea5428968f3643b1120d2b48b2563","src/components/RegionDirectory.astro":"83ebde701e2cdc28f4591a7d7ac99da169e697801065e11e2e4065ef833d4758","src/pages/[category]/[slug].astro":"2679caee82bf6516f55cf5a9187a89b7ffffd26d2b027e6c60f67700bcc68edf","src/pages/[category]/index.astro":"df0e9229c9af8af28d3486bba85f064278e890337ea0277cf5d8c266a47d9938","src/pages/index.astro":"d441a89db12aa7f57431d82d5f7ff7f0b6aaf356c9b84e05dac15549c0f4e52b"},"contextBySlug":{"daeheung-dong-mapo-arts-performance-wreath":{"contextKey":"mapo-art-center|event-congrats-wreath","facilityKey":"mapo-art-center","intentKey":"seoul-mapo|mapo-art-center|event-congrats-wreath","purchaseIntentKey":"event-congrats-wreath"},"mangwon-dong-mangwon-market-opening-wreath":{"contextKey":"mangwon-market|opening-congrats-wreath","facilityKey":"mangwon-market","intentKey":"seoul-mapo|mangwon-market|opening-congrats-wreath","purchaseIntentKey":"opening-congrats-wreath"},"sangam-dong-dmc-office-move-wreath":{"contextKey":"dmc-hightech-industry-center|event-congrats-wreath","facilityKey":"dmc-hightech-industry-center","intentKey":"seoul-mapo|dmc-hightech-industry-center|event-congrats-wreath","purchaseIntentKey":"event-congrats-wreath"}},"facilities":[{"address":"서울특별시 마포구 망원로8길 7 (망원동) 일대","facilityKey":"mangwon-market","name":"망원시장","sourceUrl":"https://www.mapo.go.kr/site/main/content/mapo05030101","unitKey":"마포구/법정동/망원동"},{"address":"서울특별시 마포구 성암로 330","facilityKey":"dmc-hightech-industry-center","name":"DMC첨단산업센터","sourceUrl":"https://www.sba.seoul.kr/Pages/BusinessApply/PostingDetail.aspx?p=0&mid=9620564b-72ec-f011-b404-d4f5ef4a1e33","unitKey":"마포구/법정동/상암동"},{"address":"서울특별시 마포구 대흥로20길 28 (대흥동)","facilityKey":"mapo-art-center","name":"마포아트센터","sourceUrl":"https://www.mfac.or.kr/foundation/facility_7.jsp","unitKey":"마포구/법정동/대흥동"}],"held":[],"membershipCounts":{"administrative":16,"legal":26,"relations":41},"membershipSourceSha256":"37a0f2c1c6c033d53fa2c2c1c2a351b6e82d89bb747b46482552e91807a5ec56","partialRelationCount":26,"partialUnitKeys":["마포구/법정동/아현동","마포구/법정동/공덕동","마포구/법정동/도화동","마포구/법정동/마포동","마포구/법정동/대흥동","마포구/법정동/염리동","마포구/법정동/노고산동","마포구/법정동/신수동","마포구/법정동/신정동","마포구/법정동/망원동","마포구/법정동/성산동"],"plannedDistinctUnitCount":3,"plannedUnitKeys":["마포구/법정동/망원동","마포구/법정동/상암동","마포구/법정동/대흥동"],"proofFile":"9e00c9cfa71a841672434ff5d0f82ec9.txt","queryEvidenceBySlug":{"daeheung-dong-mapo-arts-performance-wreath":{"canonicalFacility":{"address":"서울특별시 마포구 대흥로20길 28 (대흥동)","facilityKey":"mapo-art-center","name":"마포아트센터","sourceUrl":"https://www.mfac.or.kr/foundation/facility_7.jsp","unitKey":"마포구/법정동/대흥동"},"facilityKey":"mapo-art-center","finding":"발표회나 공연을 응원하는 단체가 사진과 예산을 비교하되, 주최측에서 수령 가능한 경우에만 화환 주문을 이어가는 상황.","purchaseIntentKey":"event-congrats-wreath","sourceProposalSha256":"1e1fcbc84f6bf026ec104dc5bdb1d9f558c141ac7ccd8cda52ac62e93c7ce8b4","sourceUrl":"https://www.mfac.or.kr/foundation/facility_7.jsp","unitKey":"마포구/법정동/대흥동"},"mangwon-dong-mangwon-market-opening-wreath":{"canonicalFacility":{"address":"서울특별시 마포구 망원로8길 7 (망원동) 일대","facilityKey":"mangwon-market","name":"망원시장","sourceUrl":"https://www.mapo.go.kr/site/main/content/mapo05030101","unitKey":"마포구/법정동/망원동"},"facilityKey":"mangwon-market","finding":"친구나 거래처의 개업 축하에서 예산과 꽃색을 먼저 고르고, 시장 내 실제 점포 수령과 리본 문구를 함께 정하는 상황.","purchaseIntentKey":"opening-congrats-wreath","sourceProposalSha256":"1e1fcbc84f6bf026ec104dc5bdb1d9f558c141ac7ccd8cda52ac62e93c7ce8b4","sourceUrl":"https://www.mapo.go.kr/site/main/content/mapo05030101","unitKey":"마포구/법정동/망원동"},"sangam-dong-dmc-office-move-wreath":{"canonicalFacility":{"address":"서울특별시 마포구 성암로 330","facilityKey":"dmc-hightech-industry-center","name":"DMC첨단산업센터","sourceUrl":"https://www.sba.seoul.kr/Pages/BusinessApply/PostingDetail.aspx?p=0&mid=9620564b-72ec-f011-b404-d4f5ef4a1e33","unitKey":"마포구/법정동/상암동"},"facilityKey":"dmc-hightech-industry-center","finding":"기업 이전을 축하하는 공동선물에서 예산·격식·발신 회사 표기를 맞추고, 같은 건물 여러 입주사 중 수령 팀에 연결하는 상황.","purchaseIntentKey":"event-congrats-wreath","sourceProposalSha256":"1e1fcbc84f6bf026ec104dc5bdb1d9f558c141ac7ccd8cda52ac62e93c7ce8b4","sourceUrl":"https://www.sba.seoul.kr/Pages/BusinessApply/PostingDetail.aspx?p=0&mid=9620564b-72ec-f011-b404-d4f5ef4a1e33","unitKey":"마포구/법정동/상암동"}},"representativeAssignment":"facility-purchase-context-v1","reviewedCommon":{"articleListingIntro":"축하할 사람과 자리를 떠올리며 원하는 상품을 고르고, 주문 상담으로 편하게 이어가세요.","home":{"description":"망원시장 새 가게, DMC첨단산업센터의 새 사무실, 마포아트센터의 무대에 전할 축하. 실제 화환사진과 가격을 살펴보고 편하게 상담하세요.","heading":"마포의 새로운 시작과 빛나는 무대에 전하는 꽃","heroParagraph":"첫 손님을 기다리는 망원시장 가게, 동료들과 새 도전을 시작하는 DMC 사무실, 오랜 연습 끝에 막을 올리는 마포아트센터의 무대. 마음으로 함께하고 싶은 순간에 어울릴 화환을 골라보세요.","title":"마포구 화환 주문 | 꽃이랑"},"regionDirectory":{"heading":"마포구 장소별 화환 주문 안내","intro":"가게의 시작을 반기는 축하, 거래처의 도약을 응원하는 인사, 무대에 서는 사람에게 전할 마음. 망원동·상암동·대흥동의 구매 상황별로 상품 선택을 살펴보세요."},"scopeKey":"seoul-mapo-direct-initial-20261011"},"reviewedProductDescriptions":{"B060":"흰 꽃 바탕에 연분홍·노랑이 더해진 사진을 비교해 보세요.","B201":"흰 꽃 사이에 노란 꽃이 놓인 기본형 사진을 살펴보세요.","B203":"위쪽으로 이어지는 흰 꽃과 노란 꽃의 배치를 비교해 보세요.","B205":"상단의 노란 장식과 흰 꽃이 어우러진 사진을 살펴보세요.","C200":"빨강·분홍과 노란 꽃이 어우러진 사진에서 원하는 색감을 찾아보세요.","C203":"가운데 노란 꽃이 강조된 사진을 보고 축하 선물의 분위기를 골라보세요.","C204":"노란 꽃과 여러 색의 둥근 꽃이 어우러진 모습을 살펴보세요.","C205":"노랑·분홍 꽃이 둥글게 이어지는 사진을 보며 축하 선물을 골라보세요."},"runtimeRegionsSha256":"6738e42441a0cd21c7ffe1522aecf2c00d8ad2123deb9f75a922c58a49560263","slugs":["mangwon-dong-mangwon-market-opening-wreath","sangam-dong-dmc-office-move-wreath","daeheung-dong-mapo-arts-performance-wreath"],"unitKeys":["마포구/법정동/아현동","마포구/법정동/공덕동","마포구/법정동/신공덕동","마포구/법정동/도화동","마포구/법정동/용강동","마포구/법정동/토정동","마포구/법정동/마포동","마포구/법정동/대흥동","마포구/법정동/염리동","마포구/법정동/노고산동","마포구/법정동/신수동","마포구/법정동/현석동","마포구/법정동/구수동","마포구/법정동/창전동","마포구/법정동/상수동","마포구/법정동/하중동","마포구/법정동/신정동","마포구/법정동/당인동","마포구/법정동/서교동","마포구/법정동/동교동","마포구/법정동/합정동","마포구/법정동/망원동","마포구/법정동/연남동","마포구/법정동/성산동","마포구/법정동/중동","마포구/법정동/상암동"],"unitTypeCounts":{"eup":0,"legal-dong":26,"myeon":0}};







const priorRegionPattern=/서대문구|seodaemun|은평구|eunpyeong|노원구|nowon|강북구|gangbuk|도봉구|dobong|성북구|seongbuk|동대문구|dongdaemun|중랑구|jungnang|광진구|gwangjin|성동구|seongdong|용산구|yongsan|중구|seoul-jung(?!nang)|종로|jongno|양평|yangpyeong|가평|연천|(?<![가-힣])여주|포천|남양주|양주|김포|광주시|광주광역시|안성|이천(?!리)|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:gapyeong|yeoncheon|yeoju|pocheon|namyangju|yangju|gimpo|gwangju|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/;
test('Seoul Mapo-gu complete official membership stays separate from frozen purchase-intent N',()=>{
 const pages=read('pages'),c=read('region-coverage'),policy=read('region-policy');
 assert.deepEqual(pages.map(p=>p.slug),expected.approved);
 assert.deepEqual(c.units.map(u=>u.unitKey),expected.unitKeys);
 assert.deepEqual(c.administrativeCrosswalk,expected.administrativeCrosswalk);
 assert.equal(c.membershipSourceSha256,expected.membershipSourceSha256);
 assert.equal(c.units.length,expected.membershipCounts.legal);assert.equal(c.administrativeCrosswalk.length,expected.membershipCounts.administrative);
 assert.equal(c.representatives.length,expected.slugs.length);
 assert.equal(c.districts.length,1);assert.equal(c.districts[0].name,'마포구');
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
test('Seoul Mapo-gu customer wording is allowed while copied prior-site names remain rejected',()=>{
 assert.doesNotMatch('서울 마포구 망원동과 상암동, 대흥동 주문 안내',priorRegionPattern);
 assert.doesNotMatch('상품을 보여주는 사진',priorRegionPattern);
 assert.doesNotMatch('https://seoul-mapo.fwith.kr/',priorRegionPattern);
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
  assert.equal(r.intentKey,`seoul-mapo|${r.contextKey}`);
  const facility=c.facilities.find(f=>f.facilityKey===r.facilityKey);assert.ok(facility);assert.deepEqual(r.unitKeys,[facility.unitKey]);
  if(r.status!=='approved')continue;
  for(const rows of [pages,m.pages,a.pages,pm.pages]){const page=rows.find(p=>p.pageKey===r.pageKey);assert.ok(page);for(const key of ['facilityKey','purchaseIntentKey','contextKey','intentKey'])assert.equal(page[key],binding[key]);assert.deepEqual(page.regionUnitKeys,r.unitKeys);}
 }
});

test('Mapo common purchase copy leads with purpose and choice while keeping delivery limits',()=>{
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
