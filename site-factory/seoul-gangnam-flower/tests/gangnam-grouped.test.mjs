/** New successor tests. Retained inputs are evidence; historical runtime source is not claimed. */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {validateDefinition,regionalRows,regionalMetadata,assertRegionalMetadata,validateRegionalPurchase,aliasTargets,directoryGroups,hubState} from '../src/lib/regions.mjs';
import {contextFields,frozenBindingSha256} from '../src/lib/gangnam-regions.mjs';
import {pageSources,isExactReviewedHttp} from '../src/lib/gangnam-sources.mjs';
import {pageSources as sharedSources} from '../src/lib/sources.mjs';
import {inputPins,a04Fields,loadGangnamInputs,projectGangnamRuntime,verifyGangnamRuntime,sha,canonical} from '../scripts/generate_gangnam_runtime.mjs';
import {loadGangnamCurrentInputs,projectGangnamCurrentRuntime,verifyGangnamCurrentRuntime} from '../scripts/generate_gangnam_minimized_source.mjs';
const root=new URL('../',import.meta.url);
const bytes=file=>fs.readFileSync(new URL(file,root));
const read=file=>JSON.parse(bytes(file));
const clone=structuredClone;
const c=read('src/data/region-coverage.json'),p=read('src/data/region-policy.json'),plan=read('src/data/gangnam-plan-binding.json');
const products=read('src/data/products.json'),rows=read('src/data/pages.json'),architecture=read('src/data/architecture.json');
const approved=read('src/data/gangnam-a04-rev4/revised-input/copy/article-copy.rev4.json').articles;
const effective=projectGangnamCurrentRuntime(loadGangnamCurrentInputs());
const membership=read('src/data/gangnam-approved/plan/membership.json');
const fresh=()=>({coverage:clone(c),policy:clone(p),pages:clone(rows),architecture:clone(architecture),products:clone(products)});
function rejectDefinition(changes){for(const change of changes){const value=clone(c);change(value);assert.throws(()=>validateDefinition(value,p));}}

test('Gangnam original/rev4 logical inputs and binding have independently retained SHA256 pins',()=>{
 for(const [name,expected] of Object.entries(inputPins))assert.equal(sha(bytes('src/data/'+name+'.json')),expected,name);
 assert.equal(sha(canonical(plan)),frozenBindingSha256);
 assert.doesNotThrow(()=>validateDefinition(c,p));
 assert.equal(plan.approvedArticlesSha256,'ca721a7a712c7814b21599d7a16d49e9476465527213c8496a1c2d2bb61b3e0f');
 assert.equal(plan.inputOverlay.baseApprovedArticlesSha256,'6aa8e1f7acefaed276486ebefbb93bddb1e9b5eb1b15023ed9d7fda3ec3daeb3');
 assert.equal(plan.inputOverlay.a04MappingSha256,'fd4f54ac139055fabe6694c316286afcb7b22792cb77133cf8c56f54b9f0c5e4');
});
test('Gangnam keeps N3, twelve discovery groups, five physical anchors, zero buyer occasions and six hold decisions',()=>{
 assert.deepEqual([plan.originalPlanN,plan.originalCandidateN,plan.activeCandidateN,plan.activePhysicalFacilityN,plan.activeBuyerOccasionN,plan.heldSeparateURLDecisionN],[3,12,5,5,0,6]);
 assert.equal(plan.candidateLedger.length,12);assert.equal(plan.candidateLedger.filter(row=>row.status==='active_factual_anchor').length,5);assert.equal(plan.heldPageDecisions.length,6);
 assert.equal(c.facilities.length,5);assert.deepEqual(c.buyerOccasions,[]);assert.equal(regionalRows(rows,architecture,c,p).length,3);
 assert.deepEqual(rows.map(row=>row.slug),['gangnam-funeral-wreath','gangnam-wedding-wreath','gangnam-event-wreath']);
 rejectDefinition([v=>v.representatives=[],v=>v.representatives.pop(),v=>v.representatives.push(clone(v.representatives[0])),v=>v.facilities.pop(),v=>v.facilities.push(clone(v.facilities[0])),v=>v.buyerOccasions.push({contextKey:'gangnam-opening-occasion'}),v=>v.representatives[0].candidateIds.push('sparkplus-gangnam3')]);
 for(const subset of [[],rows.slice(0,2),[...rows,clone(rows[0])]])assert.throws(()=>regionalRows(subset,architecture,c,p));
});
test('Gangnam exactly preserves 14 legal, 22 administrative and 31 many-to-many membership relations',()=>{
 assert.deepEqual([c.units.length,c.administrativeCrosswalk.length,c.membershipRelationCount],[14,22,31]);
 assert.deepEqual(c.units.map(unit=>({code:unit.legalCode,name:unit.name})),membership.legalUnits.map(({code,name})=>({code,name})));
 assert.deepEqual(c.administrativeCrosswalk.map(alias=>({code:alias.administrativeCode,name:alias.name})),membership.administrativeUnits.map(({code,name})=>({code,name})));
 const relations=c.administrativeCrosswalk.flatMap(alias=>alias.relations.map(relation=>({administrativeCode:alias.administrativeCode,legalCode:c.units.find(unit=>unit.unitKey===relation.unitKey).legalCode})));
 assert.deepEqual(relations,membership.relations.map(({administrativeCode,legalCode})=>({administrativeCode,legalCode})));
 assert.deepEqual(c.administrativeFacilityAssignments,[]);assert.ok(c.facilities.every(facility=>facility.administrativeCode===null));
 rejectDefinition([v=>v.units.pop(),v=>v.administrativeCrosswalk.pop(),v=>v.administrativeCrosswalk[0].relations.pop(),v=>v.membershipRelationCount=30,v=>v.units[0].legalCode='1165010100',v=>v.facilities[0].administrativeCode='1168066000',v=>v.administrativeFacilityAssignments.push({facilityKey:'samsung-seoul-funeral',administrativeCode:'1168066000'}),v=>v.membershipSourceSha256='0'.repeat(64),v=>v.sourceAttachmentSha256='0'.repeat(64)]);
});
test('Gangnam cannot fabricate Samsung/SETEC legal units or any facility administrative identity',()=>{
 assert.deepEqual(c.facilities.filter(facility=>facility.unitKey===null).map(facility=>facility.facilityKey),['samsung-seoul-funeral','setec']);
 for(const id of ['samsung-seoul-funeral','setec'])for(const unitKey of ['강남구/법정동/일원동','강남구/법정동/대치동','강남구/법정동/개포동'])rejectDefinition([v=>v.facilities.find(facility=>facility.facilityKey===id).unitKey=unitKey]);
 rejectDefinition([v=>v.facilities[1].unitKey=null,v=>v.facilities[2].unitKey='강남구/법정동/역삼동',v=>v.facilities[3].districtKey='seoul-seocho-gu',v=>v.facilities[0].unexpected='unknown',v=>v.facilities[0].legalDong='일원동',v=>v.areaContexts=[]]);
 for(const id of c.facilities.map(facility=>facility.facilityKey))rejectDefinition([v=>v.facilities.find(facility=>facility.facilityKey===id).administrativeCode='1168061000']);
});
test('Gangnam exact five physical anchors have approved headings and article destinations',()=>{
 assert.deepEqual(rows.map(row=>row.facilityAnchors.length),[2,1,2]);assert.ok(rows.every(row=>row.buyerOccasionAnchors.length===0));
 assert.deepEqual(rows.map(row=>row.regionUnitKeys),[['강남구/법정동/도곡동'],['강남구/법정동/대치동'],['강남구/법정동/삼성동']]);
 for(const row of rows){const article=approved.find(article=>article.slug===row.slug);assert.deepEqual(row.facilityAnchors.map(anchor=>anchor.candidateId),article.facilityAnchors);for(const anchor of row.facilityAnchors){assert.equal(anchor.href,row.url+'#'+anchor.anchor);assert.equal(article.sections.filter(section=>section.id===anchor.anchor&&section.heading===anchor.heading).length,1);}}
 rejectDefinition([v=>v.representatives[0].facilityAnchors.pop(),v=>v.representatives[0].facilityAnchors[0].unitKey='강남구/법정동/일원동',v=>v.representatives[2].facilityAnchors[1].href='/regions/setec/',v=>v.representatives[1].facilityAnchors[0].heading='그랜드힐 역삼동',v=>v.representatives[1].unitKeys.push('강남구/법정동/역삼동'),v=>v.representatives[2].buyerOccasionAnchors=[{candidateId:'opening'}]]);
});
test('Gangnam district directory exposes three unique cards, three legal anchors and two explicitly null anchors',()=>{
 const groups=directoryGroups(rows,architecture,c,p);assert.equal(groups.length,1);assert.equal(groups[0].items.length,3);assert.ok(groups[0].items.every(entry=>entry.aliases.length===0));
 const anchors=groups[0].items.flatMap(entry=>entry.representative.facilityAnchors);assert.equal(anchors.filter(anchor=>anchor.unitKey!==null).length,3);assert.equal(anchors.filter(anchor=>anchor.unitKey===null).length,2);
 assert.deepEqual(aliasTargets('도곡동',rows,architecture,c,p),['/regions/gangnam-funeral-wreath/#yonsei-gangnam-funeral']);
 assert.deepEqual(aliasTargets('대치동',rows,architecture,c,p),['/regions/gangnam-wedding-wreath/#grandhill-convention']);
 assert.deepEqual(aliasTargets('삼성동',rows,architecture,c,p),['/regions/gangnam-event-wreath/#coex']);
 assert.deepEqual(aliasTargets('삼성서울병원 장례식장',rows,architecture,c,p),['/regions/gangnam-funeral-wreath/#samsung-seoul-funeral']);
 for(const name of ['일원동','역삼동','강남성모병원','서울성모병원','세곡동','신사동','개업축하화환','일원1동','대치1동'])assert.deepEqual(aliasTargets(name,rows,architecture,c,p),[],name);
 assert.deepEqual(hubState(3,true),{exists:true,indexable:true,menu:false,sitemap:true});
});
test('Gangnam site, scope and opt-in reject all historical cross-region combinations and downgrades',()=>{
 for(const field of ['siteKey','scopeKey','representativeAssignment'])for(const value of ['other','seoul-guro-flower-direct','seoul-geumcheon-flower-direct','seoul-yeongdeungpo-flower-direct','seoul-gwanak-flower-direct','seoul-seocho-flower-direct','facility-purchase-context-v1','gwanak-grouped-occasion-context-v1'])for(const side of ['coverage','policy']){const f=fresh();f[side][field]=value;assert.throws(()=>validateDefinition(f.coverage,f.policy));}
 for(const field of ['siteKey','scopeKey','representativeAssignment']){const value=clone(c);delete value[field];assert.throws(()=>validateDefinition(value,p));}
});
test('Gangnam route, architecture and all six context fields fail closed on drift',()=>{
 for(const change of [v=>v[0].approvalVerified=false,v=>v[0].status='candidate',v=>v[0].url='/regions/seocho-funeral-wreath/',v=>v[0].scopeKey='other',v=>v[0].candidateIds=['wrong'],v=>v[0].facilityAnchors[0].anchor='wrong',v=>v[1].buyerOccasionAnchors=[{candidateId:'opening'}],v=>v[0].regionUnitKeys=['wrong'],v=>v[2].intentKey='gangnam-wedding-purchase',v=>v[0].facilityKey='samsung-seoul-funeral',v=>v[0].unitKey='강남구/법정동/일원동']){const value=clone(rows);change(value);assert.throws(()=>regionalRows(value,architecture,c,p));}
 for(const change of [v=>v.pages.pop(),v=>v.pages.push(clone(v.pages[0])),v=>v.pages[0].parentHub='/',v=>v.pages[0].scopeKey='other',v=>v.pages[2].intentKey='wrong',v=>v.siteKey='other']){const value=clone(architecture);change(value);assert.throws(()=>regionalRows(rows,value,c,p));}
 assert.equal(contextFields.length,6);
});
test('Gangnam three intents retain exact four SKUs, eight catalog photos, prices and individual order destinations',()=>{
 assert.deepEqual(rows.map(row=>row.purchaseIntentKey),['funeral-condolence-wreath','wedding-congrats-wreath','event-congrats-wreath']);
 for(const row of rows){assert.doesNotThrow(()=>assertRegionalMetadata(row,c,p,products));assert.doesNotThrow(()=>validateRegionalPurchase(row,products));assert.equal(row.regionalProductKeys.length,4);}
 for(const product of products){const expected=plan.catalog.find(row=>row.key===product.key);assert.equal(sha(bytes('public'+product.img)),expected.imageSha256,product.officialSku);}
 for(const change of [v=>v[0].officialSku='C200',v=>v[0].price=59001,v=>v[0].img='/images/fake.jpg',v=>v[0].imageSha256='0'.repeat(64),v=>v[0].imageAlt='Wrong',v=>v[0].orderUrl='https://fwith.co.kr/',v=>v[0].sourceUrl='https://example.com/',v=>v[0].family='congrats',v=>v[0].name='Wrong',v=>v.pop()]){const value=clone(products);change(value);assert.throws(()=>regionalMetadata(c,p,value,rows[0].pageKey));}
 for(const change of [v=>v.regionalProductFamilies=['congrats'],v=>v.regionalProductKeys.reverse(),v=>v.regionalProductKeys.pop(),v=>v.purchaseIntentKey='opening-congrats-wreath',v=>v.intentKey='wrong',v=>v.regionalPurchaseMode='consultation-only']){const value=clone(rows[0]);change(value);assert.throws(()=>validateRegionalPurchase(value,products));}
});
test('Only two exact reviewed Samsung HTTP source strings are allowed without weakening shared HTTPS validation',()=>{
 const urls=['http://www.samsunghospital.com/home/funerals/guide.do?view=procedure','http://www.samsunghospital.com/home/funerals/service.do?view=flower'];
 const source=url=>({url,name:'검증된 삼성서울병원 원문',type:'official',verifiedAt:'2026-10-13'});
 for(const url of urls){const value=source(url);assert.equal(isExactReviewedHttp(url),true);assert.deepEqual(pageSources({sources:[value]}),[value]);assert.throws(()=>sharedSources({sources:[value]}),/HTTPS/);for(const edited of [{...value,type:'business'},{...value,verifiedAt:'2026-10-14'}])assert.throws(()=>pageSources({sources:[edited]}),/provenance/);}
 for(const url of [urls[0]+'#section',urls[0]+'&extra=1',urls[0].replace('www.',''),urls[0].replace('.com/','.com:80/'),urls[0].replace('procedure','other'),'http://www.samsunghospital.com/','http://example.com/','http://evil@www.samsunghospital.com/home/funerals/guide.do?view=procedure'])assert.throws(()=>pageSources({sources:[source(url)]}),/HTTPS/);
 for(const row of rows)assert.deepEqual(pageSources(row).map(({name,url})=>({name,url})),effective['gangnam-copy'].articles.find(article=>article.slug===row.slug).sourceLinks);
});
test('Gangnam rev4 reconstruction reproduces all eight retained JSON byte hashes and stable page snapshots',()=>{
 const hashes={pages:'fab628b5b2ec6db10823287ef3a9709f8ce84849d58cd05a2c96126a530ae577',architecture:'c6802877fedb9ef111be0023cb3c6282ab47f248f07ee173d29d56b7d0ee259f','page-map':'6953008295b3e0fd31e794066ec08159a4eb2fa4df01a5d1fbaa314167705ccc','publish-manifest':'2f942206ba7fdc26b8cca127d4dcb7f5e5e2b38003cd8b66fe7fda28454c2acf','direct-checkpoint':'402dfc63ca797ee0c21a63f5df5016508adb5a14510dabdfe5282ab548813694','gangnam-copy':'893978677953deab30d9343b0dee00c0670dde668d8d53054252f1f0d034a816','gangnam-ui-copy':'5834b9cabf57f394d83ba3744df7691d7b9d6167a95ba8d04aee1a94eeaa5a5a','gangnam-a04-metadata':'fd4f54ac139055fabe6694c316286afcb7b22792cb77133cf8c56f54b9f0c5e4'};
 const first=projectGangnamRuntime(loadGangnamInputs()),second=projectGangnamRuntime(loadGangnamInputs());assert.deepEqual(first,second);
 for(const [name,expected] of Object.entries(hashes)){assert.equal(sha(JSON.stringify(first[name],null,2)+'\n'),expected,name);assert.deepEqual(read('src/data/'+name+'.json'),effective[name],name);}
 assert.deepEqual(first.pages.map(page=>page.snapshotHash),['4522a5643f0bacad08105d93c67167148df80a9fea706379f314471f30033ce2','bab9d80779d7fbc3d0d3d7d867b7a263fba357c3987f7c4c2f7e42c5438c8ae6','d99a84a666c1185edbae505671850abbb3d75ca113b9af7812bc3894bfd9a1c2']);
 assert.equal(verifyGangnamRuntime(first),true);
 assert.equal(verifyGangnamCurrentRuntime(Object.fromEntries(Object.keys(effective).map(name=>[name,read('src/data/'+name+'.json')]))),true);
});
test('Gangnam regeneration fails before output for misbound raw input hashes, wrong logical copy or A04',()=>{
 for(const [name,mutate] of [['gangnam-a04-rev4/revised-input/copy/article-copy.rev4',v=>v.articles[2].firstAnswer='wrong region'],['gangnam-a04-rev4/revised-input/handoff/runtime-input.rev4',v=>v.originalPlanN=4],['gangnam-approved/copy/common-visible-copy.final',v=>v.common.home.title='서초구 화환'],['gangnam-a04-rev4/mapping/keyword-mapping.rev4.final',v=>v.records[3].url='/regions/gangnam-wedding-wreath/'],['gangnam-a04-rev4/revised-input/input-manifest.rev4',v=>v.routeDenominator=5],['gangnam-plan-binding',v=>v.inputOverlay.a04MappingSha256='0'.repeat(64)]]){const inputs=loadGangnamInputs();mutate(inputs.pinned[name]);assert.throws(()=>projectGangnamRuntime(inputs),/input object drift/);}
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'gangnam-pin-negative-'));try{const target=path.join(temp,'src/data/gangnam-approved/plan');fs.mkdirSync(target,{recursive:true});fs.writeFileSync(path.join(target,'fixed-plan.json'),'{}\n');assert.throws(()=>loadGangnamInputs(temp),/SHA binding drift/);}finally{fs.rmSync(temp,{recursive:true,force:true});}
});
test('Gangnam full runtime projection rejects mismatched snapshots, A04, false publication and denominator inflation',()=>{
 const expected=projectGangnamRuntime(loadGangnamInputs());
 const mutations=[v=>v.pages[0].snapshotHash='0'.repeat(64),v=>v.pages[2].firstAnswer=approved[1].firstAnswer,v=>v.pages[0].title='서초구 근조화환',v=>v.pages[0].a04=clone(v.pages[1].a04),v=>v.pages[0].a04InputBinding.mappingSha256='0'.repeat(64),v=>v.pages[0].title_alignment_score=89,v=>v.architecture.home.title_alignment_score=0,v=>v.architecture.home.query_priority=2,v=>v['page-map'].homeMetadata.a04InputBinding.articleRevision=3,v=>v['publish-manifest'].directRelease.plannedOriginalCount=5,v=>v['publish-manifest'].directRelease.renderedHtmlRouteCount=5,v=>v['publish-manifest'].directRelease.candidateInventory.groups=5,v=>v['publish-manifest'].directRelease.publishedCoverage.numerator=3,v=>v['publish-manifest'].directRelease.publicationAuthorized=true,v=>v['direct-checkpoint'].productionApproved=true,v=>v['direct-checkpoint'].searchIndexing.submitted=true];
 for(const mutate of mutations){const changed=clone(expected);mutate(changed);assert.throws(()=>verifyGangnamRuntime(changed,expected),/runtime projection drift/);}
 const manifest=expected['publish-manifest'];assert.deepEqual(manifest.directRelease.publishedCoverage,{numerator:0,denominator:3,percent:0});assert.equal(manifest.directRelease.sourceCommit,null);assert.equal(manifest.directRelease.screenQa,'UNVERIFIED');assert.equal(manifest.directRelease.sitemapUrlCount,0);
});
test('Gangnam primary A04 records bind every article plus home while directory and 404 keep null scores',()=>{
 const generated=projectGangnamRuntime(loadGangnamInputs()),mapping=generated['gangnam-a04-metadata'];
 assert.deepEqual(mapping.records.map(record=>record.url),['/',...rows.map(page=>page.url)]);
 for(const page of generated.pages){const record=mapping.records.find(record=>record.url===page.url);for(const key of a04Fields)assert.deepEqual(page[key],record[key],key);assert.deepEqual(page.a04,record);}
 for(const key of a04Fields)assert.deepEqual(generated.architecture.home[key],mapping.records[0][key],key);
 assert.equal(mapping.nonPrimaryRoutes.length,2);assert.ok(mapping.nonPrimaryRoutes.every(record=>record.title_alignment_score===null&&record.applicability==='NOT_APPLICABLE'));
 const old=read('src/data/gangnam-approved/copy/article-copy.final.json').articles[2];assert.notEqual(old.firstAnswer,approved[2].firstAnswer);assert.ok(approved[2].firstAnswer.startsWith('강남구 전시와 기업행사를'));
});
test('Gangnam actual runtime guard binds context, snapshot hashes and A04 metadata to the retained manifest',async()=>{
 const {assertRegionalInput}=await import('../src/lib/regional-runtime.mjs');assert.equal(assertRegionalInput(rows).length,3);
 for(const field of [...contextFields,'snapshotHash',...a04Fields,'a04','a04InputBinding']){const value=clone(rows);delete value[0][field];assert.throws(()=>assertRegionalInput(value),/mismatch|drift/,field);}
 assert.throws(()=>assertRegionalInput([rows[0],rows[1],clone(rows[1])]));
});
