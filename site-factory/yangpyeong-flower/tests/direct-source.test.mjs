import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';
import {validateGraph,loadGraph} from '../scripts/qa_graph.mjs';
import {pageSources} from '../src/lib/sources.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const expected={"administrativeCrosswalk":[{"administrativeCode":"4183025000","aliasKey":"양평군/행정구역/양평읍","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yangpyeong-gun","name":"양평읍","relations":[{"scope":"whole","unitKey":"양평군/읍/양평읍"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4183031000","aliasKey":"양평군/행정구역/강상면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yangpyeong-gun","name":"강상면","relations":[{"scope":"whole","unitKey":"양평군/면/강상면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4183032000","aliasKey":"양평군/행정구역/강하면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yangpyeong-gun","name":"강하면","relations":[{"scope":"whole","unitKey":"양평군/면/강하면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4183033000","aliasKey":"양평군/행정구역/양서면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yangpyeong-gun","name":"양서면","relations":[{"scope":"whole","unitKey":"양평군/면/양서면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4183034000","aliasKey":"양평군/행정구역/옥천면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yangpyeong-gun","name":"옥천면","relations":[{"scope":"whole","unitKey":"양평군/면/옥천면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4183035000","aliasKey":"양평군/행정구역/서종면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yangpyeong-gun","name":"서종면","relations":[{"scope":"whole","unitKey":"양평군/면/서종면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4183036000","aliasKey":"양평군/행정구역/단월면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yangpyeong-gun","name":"단월면","relations":[{"scope":"whole","unitKey":"양평군/면/단월면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4183037000","aliasKey":"양평군/행정구역/청운면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yangpyeong-gun","name":"청운면","relations":[{"scope":"whole","unitKey":"양평군/면/청운면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4183038000","aliasKey":"양평군/행정구역/양동면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yangpyeong-gun","name":"양동면","relations":[{"scope":"whole","unitKey":"양평군/면/양동면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4183039500","aliasKey":"양평군/행정구역/지평면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yangpyeong-gun","name":"지평면","relations":[{"scope":"whole","unitKey":"양평군/면/지평면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4183040000","aliasKey":"양평군/행정구역/용문면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yangpyeong-gun","name":"용문면","relations":[{"scope":"whole","unitKey":"양평군/면/용문면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4183041000","aliasKey":"양평군/행정구역/개군면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yangpyeong-gun","name":"개군면","relations":[{"scope":"whole","unitKey":"양평군/면/개군면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"}],"approved":["yangpyeong-eup","gangsang-myeon","gangha-myeon","yangseo-myeon","okcheon-myeon","seojong-myeon","danwol-myeon","yangdong-myeon","jipyeong-myeon","yongmun-myeon","gaegun-myeon"],"held":["cheongun-myeon"],"membershipSourceSha256":"bfc74b39e9864d1bb29407837807b41f96aa9dfd200d9ae23785bce6e1c1cd93","proofFile":"29a79c8ebd0e44a9c81400fd74a93cbc.txt","slugs":["yangpyeong-eup","gangsang-myeon","gangha-myeon","yangseo-myeon","okcheon-myeon","seojong-myeon","danwol-myeon","cheongun-myeon","yangdong-myeon","jipyeong-myeon","yongmun-myeon","gaegun-myeon"],"unitKeys":["양평군/읍/양평읍","양평군/면/강상면","양평군/면/강하면","양평군/면/양서면","양평군/면/옥천면","양평군/면/서종면","양평군/면/단월면","양평군/면/청운면","양평군/면/양동면","양평군/면/지평면","양평군/면/용문면","양평군/면/개군면"],"unitTypeCounts":{"eup":1,"legal-dong":0,"myeon":11}};

const priorRegionPattern=/가평|연천|(?<![가-힣])여주|포천|남양주|양주|김포|광주시|광주광역시|안성|이천(?!리)|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:gapyeong|yeoncheon|yeoju|pocheon|namyangju|yangju|gimpo|gwangju|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/;
test('Yangpyeong frozen official eup/myeon membership and exact whole-unit crosswalk remain separate from articles',()=>{
 const pages=read('pages'),c=read('region-coverage');
 assert.deepEqual(pages.map(p=>p.slug),expected.approved);
 assert.deepEqual(c.units.map(u=>u.unitKey),expected.unitKeys);
 assert.deepEqual(c.administrativeCrosswalk,expected.administrativeCrosswalk);
 assert.equal(c.membershipSourceSha256,expected.membershipSourceSha256);
 assert.equal(c.units.length,expected.unitKeys.length);assert.equal(c.administrativeCrosswalk.length,expected.administrativeCrosswalk.length);assert.equal(c.representatives.length,expected.slugs.length);
 assert.equal(c.districts.length,1);assert.equal(c.districts[0].name,'양평군');
 assert.equal(new Set(c.administrativeCrosswalk.map(a=>a.aliasKey)).size,expected.administrativeCrosswalk.length);
 assert.equal(c.administrativeCrosswalk.flatMap(a=>a.relations).length,expected.unitKeys.length);
 assert.ok(c.administrativeCrosswalk.flatMap(a=>a.relations).every(r=>r.scope==='whole'));
 assert.deepEqual(Object.fromEntries(['legal-dong','eup','myeon'].map(t=>[t,c.units.filter(u=>u.unitType===t).length])),expected.unitTypeCounts);
 assert.deepEqual(c.representatives.filter(r=>r.status==='approved').map(r=>r.slug),expected.approved);
 assert.deepEqual(c.representatives.filter(r=>r.status==='reserved').map(r=>r.slug),expected.held);
 assert.ok(pages.length*10>=expected.slugs.length*9);
 for(const p of pages){assert.equal(p.category,'regions');assert.equal(p.pageType,'regional-service');assert.equal(p.url,`/regions/${p.slug}/`);}
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
  assert.doesNotMatch(JSON.stringify(read(name)),priorRegionPattern);
 }
});
test('Yangpyeong customer wording is allowed while copied prior-site names remain rejected',()=>{
 assert.doesNotMatch('양평군 단월면과 양서면 주문 안내',priorRegionPattern);
 assert.doesNotMatch('상품을 보여주는 사진',priorRegionPattern);
 for(const copied of ['가평군 꽃배달','https://gapyeong.fwith.kr/','여주시 꽃배달','여주 꽃배달','이천시 꽃배달','이천 꽃배달','https://icheon.fwith.kr/regions/example/','연천군 꽃배달','https://yeoju.fwith.kr/'])
  assert.match(copied,priorRegionPattern);
});
test('public ownership proof is unique and specific to this source',()=>{
 const root=new URL('../public/',import.meta.url);const matches=fs.readdirSync(root).filter(n=>/^[0-9a-f]{32}\.txt$/.test(n));
 assert.deepEqual(matches,[expected.proofFile]);assert.notEqual(matches[0],'5dd9187791acb5060b7beea480e40c38.txt');
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
 assert.match(read('business-truth').deliveryNotice,/양평군 단월면·양서면 10,000원/);
 assert.match(read('business-truth').deliveryNotice,/전 지역에 적용하거나.*무료라고 단정하지 마세요.*최종 결제금액.*확인/);
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
  if(['danwol-myeon','yangseo-myeon'].includes(p.slug))assert.match(p.contentMarkdown,/10,000원/);
  assert.match(p.contentMarkdown,/추가 배송비|추가배송비|배송비/);
 }
});
test('complete assembled graph and reviewed HTTPS source arrays pass unchanged shared validators',()=>{
 assert.equal(validateGraph(loadGraph()).pages,expected.approved.length);
 for(const p of read('pages'))assert.deepEqual(pageSources(p),p.sources);
});
