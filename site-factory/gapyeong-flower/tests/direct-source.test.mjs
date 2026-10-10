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
const expected={"administrativeCrosswalk":[{"administrativeCode":"4182025000","aliasKey":"가평군/행정구역/가평읍","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"gapyeong-gun","name":"가평읍","relations":[{"scope":"whole","unitKey":"가평군/읍/가평읍"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4182031000","aliasKey":"가평군/행정구역/설악면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"gapyeong-gun","name":"설악면","relations":[{"scope":"whole","unitKey":"가평군/면/설악면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4182032500","aliasKey":"가평군/행정구역/청평면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"gapyeong-gun","name":"청평면","relations":[{"scope":"whole","unitKey":"가평군/면/청평면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4182033000","aliasKey":"가평군/행정구역/상면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"gapyeong-gun","name":"상면","relations":[{"scope":"whole","unitKey":"가평군/면/상면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4182034500","aliasKey":"가평군/행정구역/조종면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"gapyeong-gun","name":"조종면","relations":[{"scope":"whole","unitKey":"가평군/면/조종면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4182035000","aliasKey":"가평군/행정구역/북면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"gapyeong-gun","name":"북면","relations":[{"scope":"whole","unitKey":"가평군/면/북면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"}],"approved":["gapyeong-eup","seorak-myeon","cheongpyeong-myeon","sang-myeon","jojong-myeon","buk-myeon"],"held":[],"membershipSourceSha256":"0410925f3642a366e68becbcc7e1e130d85c54607dee307faa6b155cb733c755","proofFile":"30794662da02fb15a2b879dd349da716.txt","slugs":["gapyeong-eup","seorak-myeon","cheongpyeong-myeon","sang-myeon","jojong-myeon","buk-myeon"],"unitKeys":["가평군/읍/가평읍","가평군/면/설악면","가평군/면/청평면","가평군/면/상면","가평군/면/조종면","가평군/면/북면"],"unitTypeCounts":{"eup":1,"legal-dong":0,"myeon":5}};

const priorRegionPattern=/연천|(?<![가-힣])여주|포천|남양주|양주|김포|광주시|광주광역시|안성|이천(?!리)|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:yeoncheon|yeoju|pocheon|namyangju|yangju|gimpo|gwangju|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/;
test('Gapyeong frozen official eup/myeon membership and exact whole-unit crosswalk remain separate from articles',()=>{
 const pages=read('pages'),c=read('region-coverage');
 assert.deepEqual(pages.map(p=>p.slug),expected.approved);
 assert.deepEqual(c.units.map(u=>u.unitKey),expected.unitKeys);
 assert.deepEqual(c.administrativeCrosswalk,expected.administrativeCrosswalk);
 assert.equal(c.membershipSourceSha256,expected.membershipSourceSha256);
 assert.equal(c.units.length,expected.unitKeys.length);assert.equal(c.administrativeCrosswalk.length,expected.administrativeCrosswalk.length);assert.equal(c.representatives.length,expected.slugs.length);
 assert.equal(c.districts.length,1);assert.equal(c.districts[0].name,'가평군');
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
test('real Seorak-myeon Icheon-ri is allowed without admitting copied Icheon city records',()=>{
 assert.doesNotMatch('가평군 설악면 이천리',priorRegionPattern);
 assert.doesNotMatch('상품을 보여주는 사진',priorRegionPattern);
 for(const copied of ['여주시 꽃배달','여주 꽃배달','이천시 꽃배달','이천 꽃배달','https://icheon.fwith.kr/regions/example/','연천군 꽃배달','https://yeoju.fwith.kr/'])
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
 assert.match(read('business-truth').deliveryNotice,/가평군 10,000원.*설악면 20,000원/);
 assert.match(read('business-truth').deliveryNotice,/합계로 계산하지 말고.*최종 결제금액.*확인/);
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
  assert.match(p.contentMarkdown,p.slug==='seorak-myeon'?/20,000원/:/10,000원/);
 }
});
test('complete assembled graph and reviewed HTTPS source arrays pass unchanged shared validators',()=>{
 assert.equal(validateGraph(loadGraph()).pages,expected.approved.length);
 for(const p of read('pages'))assert.deepEqual(pageSources(p),p.sources);
});
