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
const expected={"administrativeCrosswalk":[{"administrativeCode":"4180025000","aliasKey":"연천군/행정구역/연천읍","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yeoncheon-gun","name":"연천읍","relations":[{"scope":"whole","unitKey":"연천군/읍/연천읍"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4180025300","aliasKey":"연천군/행정구역/전곡읍","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yeoncheon-gun","name":"전곡읍","relations":[{"scope":"whole","unitKey":"연천군/읍/전곡읍"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4180031000","aliasKey":"연천군/행정구역/군남면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yeoncheon-gun","name":"군남면","relations":[{"scope":"whole","unitKey":"연천군/면/군남면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4180032000","aliasKey":"연천군/행정구역/청산면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yeoncheon-gun","name":"청산면","relations":[{"scope":"whole","unitKey":"연천군/면/청산면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4180033000","aliasKey":"연천군/행정구역/백학면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yeoncheon-gun","name":"백학면","relations":[{"scope":"whole","unitKey":"연천군/면/백학면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4180034000","aliasKey":"연천군/행정구역/미산면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yeoncheon-gun","name":"미산면","relations":[{"scope":"whole","unitKey":"연천군/면/미산면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4180035000","aliasKey":"연천군/행정구역/왕징면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yeoncheon-gun","name":"왕징면","relations":[{"scope":"whole","unitKey":"연천군/면/왕징면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4180036000","aliasKey":"연천군/행정구역/신서면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yeoncheon-gun","name":"신서면","relations":[{"scope":"whole","unitKey":"연천군/면/신서면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4180037000","aliasKey":"연천군/행정구역/중면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yeoncheon-gun","name":"중면","relations":[{"scope":"whole","unitKey":"연천군/면/중면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"},{"administrativeCode":"4180038000","aliasKey":"연천군/행정구역/장남면","attachmentUrl":"https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00149355_BR8t5D&fileSn=1","districtKey":"yeoncheon-gun","name":"장남면","relations":[{"scope":"whole","unitKey":"연천군/면/장남면"}],"sourceAttachmentSha256":"c9c2583919adfff992edc098fe7ea522e625fedabbfefedbd85564942c059d43","sourceUrl":"https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=129824","verifiedAt":"2026-10-10"}],"approved":["yeoncheon-eup","jeongok-eup","gunnam-myeon","cheongsan-myeon","baekhak-myeon","misan-myeon","wangjing-myeon","sinseo-myeon","jangnam-myeon"],"held":["jung-myeon"],"membershipSourceSha256":"539d4fd75d7a3d7d1949efc081864c4d98757f528d4b8f280e0939f9ca580df7","proofFile":"1a55e1dbf8d0930db2763008efdf9e39.txt","slugs":["yeoncheon-eup","jeongok-eup","gunnam-myeon","cheongsan-myeon","baekhak-myeon","misan-myeon","wangjing-myeon","sinseo-myeon","jung-myeon","jangnam-myeon"],"unitKeys":["연천군/읍/연천읍","연천군/읍/전곡읍","연천군/면/군남면","연천군/면/청산면","연천군/면/백학면","연천군/면/미산면","연천군/면/왕징면","연천군/면/신서면","연천군/면/중면","연천군/면/장남면"]};

test('Yeoncheon frozen official 2 eup and 8 myeon membership and exact whole-unit crosswalk remain separate from articles',()=>{
 const pages=read('pages'),c=read('region-coverage');
 assert.deepEqual(pages.map(p=>p.slug),expected.approved);
 assert.deepEqual(c.units.map(u=>u.unitKey),expected.unitKeys);
 assert.deepEqual(c.administrativeCrosswalk,expected.administrativeCrosswalk);
 assert.equal(c.membershipSourceSha256,expected.membershipSourceSha256);
 assert.equal(c.units.length,10);assert.equal(c.administrativeCrosswalk.length,10);assert.equal(c.representatives.length,10);
 assert.equal(c.districts.length,1);assert.equal(c.districts[0].name,'연천군');
 assert.equal(new Set(c.administrativeCrosswalk.map(a=>a.aliasKey)).size,10);
 assert.equal(c.administrativeCrosswalk.flatMap(a=>a.relations).length,10);
 assert.ok(c.administrativeCrosswalk.flatMap(a=>a.relations).every(r=>r.scope==='whole'));
 assert.deepEqual(Object.fromEntries(['legal-dong','eup','myeon'].map(t=>[t,c.units.filter(u=>u.unitType===t).length])),{'legal-dong':0,eup:2,myeon:8});
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
  assert.doesNotMatch(JSON.stringify(read(name)),/여주|포천|남양주|양주|김포|광주시|광주광역시|안성|이천|파주|하남|의왕|군포|시흥|오산|구리|과천|동두천|광명시|의정부|안양|평택|(?<![A-Za-z])(?:yeoju|pocheon|namyangju|yangju|gimpo|gwangju|anseong|icheon|paju|hanam|uiwang|gunpo|siheung|osan|guri|gwacheon|dongducheon|gwangmyeong|uijeongbu|anyang|pyeongtaek)(?![A-Za-z])|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/);
 }
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
 assert.match(read('business-truth').deliveryNotice,/연천군.*10,000원/);
 for(const p of read('pages')){
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,products,p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.deepEqual(p.productCardKeys,p.regionalProductKeys);
  assert.match(p.contentMarkdown,/10,000원/);
 }
});
test('complete assembled graph and reviewed HTTPS source arrays pass unchanged shared validators',()=>{
 assert.equal(validateGraph(loadGraph()).pages,expected.approved.length);
 for(const p of read('pages'))assert.deepEqual(pageSources(p),p.sources);
});
