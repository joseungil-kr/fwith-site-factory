import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {validateDefinition,regionalRows,regionalMetadata,assertRegionalMetadata,validateRegionalPurchase,aliasTargets,directoryGroups,hubState} from '../src/lib/regions.mjs';
import {contextFields,frozenBindingSha256} from '../src/lib/gwanak-regions.mjs';
import {publishedDestinationsByUnit,publishedUnassignedDistrictDestinations} from '../src/lib/directory-links.mjs';

const read=file=>JSON.parse(fs.readFileSync(new URL('../'+file,import.meta.url),'utf8'));
const bytes=file=>fs.readFileSync(new URL('../'+file,import.meta.url));
const sha=buffer=>crypto.createHash('sha256').update(buffer).digest('hex');
const canonical=value=>JSON.stringify(value,(_,item)=>item&&typeof item==='object'&&!Array.isArray(item)?Object.fromEntries(Object.keys(item).sort().map(key=>[key,item[key]])):item);
const clone=structuredClone;
const c=read('src/data/region-coverage.json'),p=read('src/data/region-policy.json'),plan=read('src/data/gwanak-plan-binding.json');
const original=read('src/data/gwanak-approved/inputs/plan/fixed-plan.json');
const membership=read('src/data/gwanak-approved/inputs/plan/membership.json');
const inventory=read('src/data/gwanak-approved/inputs/plan/candidate-inventory.json');
const approvedCopy=read('src/data/gwanak-approved/inputs/copy/article-copy.rev4.json');
// Isolated adapter fixtures deliberately use no publication, network or remote state.
const products=plan.catalog.map(({image,...product})=>({...product,img:image,orderUrl:product.sourceUrl}));
const rows=c.representatives.map(row=>({pageKey:row.pageKey,slug:row.slug,url:row.url,primaryKeyword:row.primaryKeyword,...regionalMetadata(c,p,products,row.pageKey),category:'regions',pageType:'regional-service',routeType:'category',status:'approved',approvalVerified:true,snapshotId:'isolated-gwanak-adapter-'+row.slug,snapshotHash:'a'.repeat(64)}));
const a={siteKey:c.siteKey,pages:rows.map(page=>({...page,pageRole:'REGION_SERVICE_LANDING',parentHub:'/regions/',localizationPolicy:'local-required'}))};

test('Gwanak frozen original inputs and transformed binding have exact independent SHA256 pins',()=>{
 const pairs=[
  ['inputs/plan/fixed-plan.json','fixedPlanSha256','e68fa31eee4b3d375fb5a73cf8652828ef01e8c34ab6648bc0d6c44e8786a522'],
  ['inputs/plan/candidate-inventory.json','candidateInventorySha256','21c65e56b849cb9c7f09be8676e8673111bfd69c9f83709607d94f6b2ce64634'],
  ['inputs/plan/membership.json','membershipSourceSha256','5327b48e818dd13094d3cd9ee1b6e343c810c18d9f91567d80c114caed5f21a8'],
  ['inputs/copy/article-copy.rev4.json','approvedArticlesSha256','e51f8afdf54145750ce88e3f9c35924ec11671a047090f9d457e23eeacdd5969'],
  ['inputs/copy/common-visible-copy.rev3.json','approvedCommonSha256','a433bc613087ad61ce4f2a044e6a06e827b5fc726db141c3b9a31ea19c9ee96b'],
 ];
 for(const [file,key,expected] of pairs){assert.equal(sha(bytes('src/data/gwanak-approved/'+file)),expected,file);assert.equal(plan[key],expected,key);}
 assert.equal(sha(canonical(plan)),frozenBindingSha256);
 assert.equal(plan.planReviewSha256,'7673f8f3556faa1cbfa390c3b5d25a753955f72390bb49da6466f2fccbb630f4');
 assert.equal(plan.copyReviewSha256,'9bd75bd7e3b14de4c7dbf6074994d2563580dfab8344dc86ed31405d66b6f818');
 assert.equal(sha(bytes('src/data/gwanak-approved/runtime-input-bindings.json')),plan.runtimeInputSha256);
 assert.equal(sha(bytes('src/data/gwanak-approved/inputs/plan/location-reconciliation.json')),plan.locationReconciliationSha256);
});
test('Gwanak N2 is fifteen candidates, four physical facilities, one separate buyer occasion and ten held',()=>{
 assert.deepEqual([plan.originalPlanN,plan.originalCandidateN,plan.activeCandidateN,plan.activePhysicalFacilityN,plan.activeBuyerOccasionN,plan.heldCandidateN],[2,15,5,4,1,10]);
 assert.equal(original.originalPlanN,2);assert.equal(inventory.candidates.length,15);
 assert.deepEqual(plan.heldOriginalCandidateIds,inventory.candidates.filter(candidate=>candidate.status==='held').map(candidate=>candidate.id));
 assert.equal(c.facilities.length,4);assert.equal(c.buyerOccasions.length,1);
 assert.equal(regionalRows(rows,a,c,p).length,2);assert.deepEqual(rows.map(row=>row.slug),original.articles.map(article=>article.slug));
 for(const id of plan.heldOriginalCandidateIds)assert.ok(!JSON.stringify(c).includes(id),id);
 for(const change of [value=>value.representatives=[],value=>value.representatives.pop(),value=>value.representatives.push(clone(value.representatives[0])),value=>value.facilities.pop(),value=>value.facilities.push(clone(value.facilities[0])),value=>value.buyerOccasions=[],value=>value.buyerOccasions.push(clone(value.buyerOccasions[0])),value=>value.representatives[1].candidateIds.push('gwanak-arthall')]){const value=clone(c);change(value);assert.throws(()=>validateDefinition(value,p));}
 assert.throws(()=>regionalRows([],a,c,p),/parity/);assert.throws(()=>regionalRows([rows[0]],a,c,p),/parity/);
});
test('Gwanak exact three legal units and twenty-one administrative relations have zero facility assignments',()=>{
 assert.equal(c.units.length,3);assert.equal(c.administrativeCrosswalk.length,21);assert.equal(c.membershipRelationCount,21);
 assert.deepEqual(c.units.map(unit=>({code:unit.legalCode,name:unit.name})),membership.legal);
 assert.deepEqual(c.administrativeCrosswalk.map(alias=>({code:alias.administrativeCode,name:alias.name})),membership.administrative);
 const relations=c.administrativeCrosswalk.flatMap(alias=>alias.relations.map(relation=>({administrativeCode:alias.administrativeCode,legalCode:c.units.find(unit=>unit.unitKey===relation.unitKey).legalCode})));
 assert.deepEqual(relations,membership.relationships.map(({administrativeCode,legalCode})=>({administrativeCode,legalCode})));
 assert.deepEqual(c.administrativeFacilityAssignments,[]);assert.ok(c.facilities.every(facility=>facility.administrativeCode===null));
 assert.equal(c.facilities.filter(facility=>facility.unitKey==='관악구/법정동/남현동').length,0);
 assert.equal(c.facilities.find(facility=>facility.facilityKey==='snu-faculty').unitKey,null);
 assert.equal(c.sourceAttachmentSha256,'3702ee001f131968983fbba1e08c6bffc89f6ee4377de327e5eff6946b1098d7');
 for(const change of [value=>value.units.pop(),value=>value.administrativeCrosswalk.pop(),value=>value.administrativeCrosswalk[0].relations.pop(),value=>value.units[0].legalCode='1153010100',value=>value.administrativeCrosswalk[0].relations[0].scope='whole',value=>value.facilities[0].administrativeCode='1162069500',value=>value.administrativeFacilityAssignments.push({facilityKey:'wooshin-funeral',administrativeCode:'1162069500'}),value=>value.membershipSourceSha256='0'.repeat(64),value=>value.sourceAttachmentSha256='0'.repeat(64),value=>value.membershipRelationCount=22]){const value=clone(c);change(value);assert.throws(()=>validateDefinition(value,p));}
});
test('Gwanak null faculty and buyer occasion cannot acquire fabricated geographic identities',()=>{
 const faculty=c.facilities.find(facility=>facility.facilityKey==='snu-faculty');assert.equal(faculty.unitKey,null);
 const occasion=c.buyerOccasions[0];for(const key of ['unitKey','legalCode','administrativeCode','physicalAddress'])assert.equal(occasion[key],null);
 assert.equal(occasion.contextType,'buyer-occasion');assert.deepEqual(rows.map(row=>row.regionUnitKeys),[['관악구/법정동/신림동'],['관악구/법정동/봉천동']]);
 for(const change of [value=>value.facilities.find(facility=>facility.facilityKey==='snu-faculty').unitKey='관악구/법정동/신림동',value=>value.facilities.find(facility=>facility.facilityKey==='snu-faculty').unitKey='관악구/법정동/봉천동',value=>value.facilities[0].unitKey=null,value=>value.facilities[0].unitKey='관악구/법정동/남현동',value=>value.buyerOccasions[0].unitKey='관악구/법정동/신림동',value=>value.buyerOccasions[0].physicalAddress='관악구',value=>value.buyerOccasions[0].contextType='physical-facility',value=>value.facilities.push({facilityKey:'gwanak-opening-occasion',name:'개업',address:'관악구',unitKey:'관악구/법정동/신림동'}),value=>value.areaContexts=[],value=>value.facilities[0].unexpected=true]){const value=clone(c);change(value);assert.throws(()=>validateDefinition(value,p));}
});
test('Gwanak exact physical four and occasion one anchors retain approved H2 headings and separate types',()=>{
 for(const row of rows){
  const article=approvedCopy.articles.find(article=>article.slug===row.slug);
  assert.deepEqual(row.facilityAnchors.map(anchor=>anchor.anchor),article.facilityAnchors);
  assert.equal(row.intentKey,article.intentKey);
  for(const anchor of [...row.facilityAnchors,...row.buyerOccasionAnchors]){assert.equal(anchor.href,row.url+'#'+anchor.anchor);assert.equal(article.sections.filter(section=>section.id===anchor.anchor&&section.heading===anchor.heading).length,1);}
 }
 assert.deepEqual(rows.map(row=>row.facilityAnchors.length),[1,3]);assert.deepEqual(rows.map(row=>row.buyerOccasionAnchors.length),[0,1]);
 assert.equal(rows[1].buyerOccasionAnchors[0].candidateId,'gwanak-opening-occasion');assert.equal(rows[1].buyerOccasionAnchors[0].anchor,'opening-occasion');
 for(const change of [value=>value.representatives[0].facilityAnchors.pop(),value=>value.representatives[1].facilityAnchors.push(clone(value.representatives[1].buyerOccasionAnchors[0])),value=>value.representatives[1].buyerOccasionAnchors[0].anchor='gwanak-opening-occasion',value=>value.representatives[1].facilityAnchors[0].unitKey='관악구/법정동/봉천동',value=>value.representatives[0].facilityAnchors[0].heading='우신병원 장례식장',value=>value.representatives[0].facilityAnchors[0].href='/regions/wooshin-funeral/',value=>value.representatives[1].unitKeys.push('관악구/법정동/남현동')]){const value=clone(c);change(value);assert.throws(()=>validateDefinition(value,p));}
});
test('Gwanak directory has two rich cards, three legal facility links and one district-unassigned link',()=>{
 const groups=directoryGroups(rows,a,c,p),legal=publishedDestinationsByUnit(groups),unassigned=publishedUnassignedDistrictDestinations(groups);
 assert.equal(groups.length,1);assert.equal(groups.flatMap(group=>group.items).length,2);assert.ok(groups[0].items.every(entry=>entry.aliases.length===0));
 assert.equal([...legal.values()].flat().length,3);assert.equal(legal.get('관악구/법정동/봉천동').length,2);assert.equal(legal.get('관악구/법정동/신림동').length,1);assert.equal(legal.get('관악구/법정동/남현동'),undefined);assert.equal(legal.get(null),undefined);
 assert.deepEqual(unassigned.get('seoul-gwanak-gu'),[{href:'/regions/gwanak-celebration-wreath/#snu-faculty',name:'서울대학교 교수회관 65동',candidateId:'snu-faculty'}]);
 assert.ok(!JSON.stringify([...legal.values(),...unassigned.values()]).includes('opening-occasion'));
 assert.deepEqual(aliasTargets('봉천동',rows,a,c,p),['/regions/gwanak-celebration-wreath/#snu-research-park','/regions/gwanak-celebration-wreath/#nakseongdae-traditional']);
 assert.deepEqual(aliasTargets('낙성대 전통혼례식장',rows,a,c,p),['/regions/gwanak-celebration-wreath/#nakseongdae-traditional']);
 for(const name of ['낙성대동','대학동','보라매동','남현동','호암교수회관','우신병원 장례식장','개업축하화환'])assert.deepEqual(aliasTargets(name,rows,a,c,p),[],name);
 assert.deepEqual(hubState(2,true),{exists:true,indexable:false,menu:false,sitemap:false});
});
test('Null handling is additive and cannot permit old or cross-site null facility destinations',()=>{
 const groups=directoryGroups(rows,a,c,p);
 for(const change of [value=>value[0].key='seoul-other-gu',value=>value[0].items[1].page.scopeKey='legacy',value=>value[0].items[1].representative.facilityAnchors[0].candidateId='gwanak-opening-occasion',value=>value[0].items[1].representative.facilityAnchors[0].href='/regions/other/#snu-faculty']){
  const value=clone(groups);change(value);assert.throws(()=>publishedDestinationsByUnit(value));assert.throws(()=>publishedUnassignedDistrictDestinations(value));
 }
 const legacy=[{key:'legacy',items:[{page:{url:'/regions/legacy/'},representative:{unitKeys:['known'],facilityAnchors:[{candidateId:'legacy',unitKey:null,href:'/regions/legacy/#legacy',heading:'Legacy'}]}}]}];
 assert.throws(()=>publishedDestinationsByUnit(legacy),/null/);assert.throws(()=>publishedUnassignedDistrictDestinations(legacy),/district/);
});
test('Gwanak site, scope and opt-in refuse downgrade and all cross-adapter combinations',()=>{
 for(const field of ['siteKey','scopeKey','representativeAssignment'])for(const value of ['other','seoul-guro-flower-direct','seoul-geumcheon-flower-direct','seoul-yeongdeungpo-flower-direct','facility-purchase-context-v1','guro-grouped-purchase-context-v1','geumcheon-grouped-purchase-context-v1','yeongdeungpo-grouped-occasion-context-v1'])for(const side of ['coverage','policy']){const cc=clone(c),pp=clone(p);(side==='coverage'?cc:pp)[field]=value;assert.throws(()=>validateDefinition(cc,pp),field+':'+value);}
 for(const field of ['siteKey','scopeKey','representativeAssignment']){const cc=clone(c);delete cc[field];assert.throws(()=>validateDefinition(cc,p));}
 for(const field of ['membershipSourceSha256','state','rulesRevision']){const pp=clone(p);pp[field]='wrong';assert.throws(()=>validateDefinition(c,pp));}
});
test('Gwanak route parity, architecture and all six context fields fail closed on drift',()=>{
 for(const change of [value=>value[0].approvalVerified=false,value=>value[0].status='candidate',value=>value[0].url='/regions/held/',value=>value[0].scopeKey='other',value=>value[0].candidateIds=['wrong'],value=>value[0].facilityAnchors[0].anchor='wrong',value=>value[1].buyerOccasionAnchors=[],value=>value[0].regionUnitKeys=['wrong'],value=>value[1].intentKey='gwanak-wedding-only',value=>value[0].facilityKey='wooshin-funeral',value=>value[0].unitKey='관악구/법정동/신림동']){const value=clone(rows);change(value);assert.throws(()=>regionalRows(value,a,c,p));}
 for(const change of [value=>value.pages.pop(),value=>value.pages.push(clone(value.pages[0])),value=>value.pages[0].parentHub='/',value=>value.pages[0].scopeKey='other',value=>value.pages[1].buyerOccasionAnchors=[],value=>value.siteKey='other']){const value=clone(a);change(value);assert.throws(()=>regionalRows(rows,value,c,p));}
 assert.equal(contextFields.length,6);
});
test('Gwanak four SKU per intent and exact photo, price and order bindings reject changed catalog data',()=>{
 for(const row of rows){assert.doesNotThrow(()=>assertRegionalMetadata(row,c,p,products));assert.doesNotThrow(()=>validateRegionalPurchase(row,products));assert.equal(row.regionalProductKeys.length,4);}
 assert.deepEqual(rows.map(row=>row.purchaseIntentKey),['funeral-condolence-wreath','celebration-congratulation-wreath']);
 for(const change of [value=>value[0].officialSku='C200',value=>value[0].price=59001,value=>value[0].img='/images/products/generated.webp',value=>value[0].imageSha256='0'.repeat(64),value=>value[0].imageAlt='Wrong',value=>value[0].orderUrl='https://fwith.co.kr/',value=>value[0].sourceUrl='https://example.com/',value=>value[0].family='congrats',value=>value[0].name='Wrong',value=>value.push(clone(value[0])),value=>value.pop()]){const value=clone(products);change(value);assert.throws(()=>regionalMetadata(c,p,value,rows[0].pageKey));}
 for(const change of [value=>value.regionalProductFamilies=['congrats'],value=>value.regionalProductKeys.reverse(),value=>value.regionalProductKeys.pop(),value=>value.purchaseIntentKey='wedding-congratulation-wreath',value=>value.intentKey='wrong',value=>value.regionalPurchaseMode='consultation-only']){const value=clone(rows[0]);change(value);assert.throws(()=>validateRegionalPurchase(value,products));}
 for(const change of [value=>value.visualBindings[0].sha256='0'.repeat(64),value=>value.visualBindings[0].productKeys.reverse(),value=>value.visualBindings[0].image='/images/products/funeral-basic.jpg']){const value=clone(p);change(value);assert.throws(()=>regionalMetadata(c,value,products,rows[0].pageKey));}
});
test('Gwanak current runtime products and eight actual image bytes match the frozen approved source',()=>{
 const actual=read('src/data/products.json');assert.equal(actual.length,8);
 for(const row of rows)assert.doesNotThrow(()=>regionalMetadata(c,p,actual,row.pageKey));
 for(const product of actual){const expected=plan.catalog.find(item=>item.key===product.key);assert.equal(sha(bytes('public'+product.img)),expected.imageSha256,product.officialSku);}
});
test('Gwanak actual pages, manifest and architecture preserve current grouped metadata and input guard',async()=>{
 const actualRows=read('src/data/pages.json'),architecture=read('src/data/architecture.json'),manifest=read('src/data/publish-manifest.json'),actualProducts=read('src/data/products.json');
 assert.equal(regionalRows(actualRows,architecture,c,p).length,2);assert.equal(regionalRows(manifest.pages,architecture,c,p).length,2);
 for(const row of actualRows)assert.doesNotThrow(()=>assertRegionalMetadata(row,c,p,actualProducts));
 const {assertRegionalInput}=await import('../src/lib/regional-runtime.mjs');
 assert.equal(assertRegionalInput(actualRows).length,2);
 for(const field of contextFields){const changed=clone(actualRows);delete changed[1][field];assert.throws(()=>assertRegionalInput(changed),/mismatch|drift/);}
 assert.throws(()=>assertRegionalInput([actualRows[0],clone(actualRows[0])]),/duplicate/);
 for(const field of ['url','primaryKeyword','status']){const changed=clone(actualRows);changed[0][field]='wrong';assert.throws(()=>assertRegionalInput(changed));}
});
