import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';import {spawnSync} from 'node:child_process';
import {validateDefinition,regionalRows,regionalMetadata,assertRegionalMetadata,validateRegionalPurchase,aliasTargets,directoryGroups,hubState} from '../src/lib/regions.mjs';
import {publishedDestinationsByUnit} from '../src/lib/directory-links.mjs';import {reviewedHeadingAnchors} from '../src/lib/yeongdeungpo-heading-anchors.mjs';import {reviewedHeadingAnchors as legacyHeadings} from '../src/lib/heading-anchors.mjs';import {displayMarkdownBlocks} from '../src/lib/content.mjs';import {validateGraph,loadGraph} from '../scripts/qa_graph.mjs';import {assertRegionalInput} from '../src/lib/regional-runtime.mjs';
const read=n=>JSON.parse(fs.readFileSync(new URL('../src/data/'+n+'.json',import.meta.url),'utf8'));const bytes=p=>fs.readFileSync(new URL('../'+p,import.meta.url));const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const clone=structuredClone,c=read('region-coverage'),p=read('region-policy'),plan=read('yeongdeungpo-plan-binding'),rows=read('pages'),a=read('architecture'),products=read('products'),copy=read('yeongdeungpo-copy'),manifest=read('publish-manifest');
test('frozen N2 preserves 19 evaluated,8 active,11 held and46 separate observed leads',()=>{
 assert.equal(plan.fixedPlanSha256,'bd952a480edd4d2382d957929695eef130f80868e5f14579550e3759dae14d5c');assert.equal(plan.candidatePlanSha256,'a8592244dfed186300634b10bad60ed899af116ac941f7a4293e3978ecf75627');assert.equal(plan.planReviewSha256,'023958d8c4770bf88e49d657056f14f9d8bbc70dc77c20453f7de950e02815ef');
 assert.deepEqual([plan.originalPlanN,plan.originalCandidateN,plan.activeCandidateN,plan.heldCandidateN,plan.observedLeadN],[2,19,8,11,46]);assert.equal(plan.heldOriginalCandidateIds.length,11);assert.equal(new Set(plan.heldOriginalCandidateIds).size,11);
 assert.equal(plan.candidateInventorySha256,'c9e67c160bb8fddd66ec66efdcd80ed2c2de921b4f819d49a5928f6727ee9582');assert.equal(plan.observedLeadSha256,'1d6dfaf2b9357520af00ec8ef5f8ef38d9087a31ffa4754e5505ed71ab97b9c9');
 assert.doesNotThrow(()=>validateDefinition(c,p));assert.equal(regionalRows(rows,a,c,p).length,2);assert.equal(validateGraph(loadGraph()).pages,2);
 for(const id of plan.heldOriginalCandidateIds)assert.ok(!JSON.stringify([c,rows]).includes(id));
});
test('official34legal/18admin/45relations bind6represented/28unrepresented without fabricated precise admin assignment',()=>{
 assert.equal(c.units.length,34);assert.equal(c.administrativeCrosswalk.length,18);assert.equal(c.administrativeCrosswalk.flatMap(x=>x.relations).length,45);assert.equal(new Set(c.facilities.map(f=>f.unitKey)).size,6);assert.equal(c.units.filter(u=>!c.facilities.some(f=>f.unitKey===u.unitKey)).length,28);
 assert.equal(c.membershipSourceSha256,'cea038c0368af338c658399e4cb6846430326780b204d5e905571c1bbb0d1fda');assert.equal(c.sourceAttachmentSha256,'3702ee001f131968983fbba1e08c6bffc89f6ee4377de327e5eff6946b1098d7');assert.equal(c.countIsPageQuota,false);
 assert.ok(c.facilities.every(f=>!Object.hasOwn(f,'administrativeDong')));
});
test('five funeral and three wedding anchors target only two canonical articles',()=>{
 assert.deepEqual(rows.map(row=>row.candidateIds.length),[5,3]);assert.equal(c.facilities.length,8);assert.equal(c.areaContexts.length,0);
 for(const page of rows){const anchors=reviewedHeadingAnchors(displayMarkdownBlocks(page.contentMarkdown,page.firstAnswer),page.facilityAnchors);assert.equal(anchors.size,page.candidateIds.length);for(const f of page.facilityAnchors)assert.equal(f.href,page.url+'#'+f.anchor);}
 const dest=publishedDestinationsByUnit(directoryGroups(rows,a,c,p));assert.equal(dest.get('영등포구/법정동/여의도동').length,2);assert.equal(dest.get('영등포구/법정동/영등포동7가').length,2);assert.equal(dest.get('영등포구/법정동/신길동'),undefined);
 assert.deepEqual(aliasTargets('여의동',rows,a,c,p),['/regions/yeongdeungpo-funeral-wreath/#yeouido-stmary','/regions/yeongdeungpo-wedding-wreath/#partyum']);assert.deepEqual(aliasTargets('신길제1동',rows,a,c,p),[]);for(const name of ['신길제5동','대림제1동','대림제2동','대림제3동'])assert.deepEqual(aliasTargets(name,rows,a,c,p),[]);
});
test('N0,N1,N3 and mutated active/held facility memberships fail closed',()=>{
 for(const change of [x=>x.representatives=[],x=>x.representatives.pop(),x=>x.representatives.push(clone(x.representatives[0])),x=>x.facilities.pop(),x=>x.facilities.push(clone(x.facilities[0])),x=>x.areaContexts.push({contextKey:'held'}),x=>x.representatives[0].candidateIds.push('bokji'),x=>x.representatives[1].candidateIds[0]='yeouido-stmary',x=>x.representatives[0].facilityAnchors.pop()]){const v=clone(c);change(v);assert.throws(()=>validateDefinition(v,p));}
 assert.throws(()=>regionalRows([],a,c,p),/parity/);assert.throws(()=>regionalRows([rows[0]],a,c,p),/parity/);
});
test('geography,source hash and legal/admin relation mutations fail closed',()=>{
 for(const change of [x=>x.units.pop(),x=>x.administrativeCrosswalk.pop(),x=>x.administrativeCrosswalk[0].relations.pop(),x=>x.units[0].legalCode='1153000000',x=>x.units[0].name='wrong',x=>x.administrativeCrosswalk[0].relations[0].scope='whole',x=>x.membershipSourceSha256='0'.repeat(64),x=>x.membershipRelationCount=46,x=>x.facilities[0].address='wrong',x=>x.facilities[0].sourceUrl='http://example.com/',x=>x.representatives[0].unitKeys.reverse()]){const v=clone(c);change(v);assert.throws(()=>validateDefinition(v,p));}
 const v=clone(p);v.membershipSourceSha256='0'.repeat(64);assert.throws(()=>validateDefinition(c,v));
});
test('site,scope and assignment cannot downgrade into Guro,Geumcheon or legacy modes',()=>{
 for(const field of ['siteKey','scopeKey','representativeAssignment'])for(const value of ['other','seoul-guro-flower-direct','seoul-geumcheon-flower-direct','facility-purchase-context-v1']){for(const which of ['coverage','policy']){const cc=clone(c),pp=clone(p);(which==='coverage'?cc:pp)[field]=value;assert.throws(()=>validateDefinition(cc,pp));}}
 for(const field of ['siteKey','scopeKey','representativeAssignment']){const cc=clone(c);delete cc[field];assert.throws(()=>validateDefinition(cc,p));}
});
test('frozen named H2/H3 hierarchy is explicit and cannot loosen original H2-only contract',()=>{
 for(const page of rows){const b=displayMarkdownBlocks(page.contentMarkdown,page.firstAnswer),spec=page.facilityAnchors[0],level=page===rows[0]?'h3':'h2';assert.equal(b.find(x=>x.text===spec.heading).type,level);
  for(const change of [x=>x.splice(x.findIndex(b=>b.text===spec.heading),1),x=>x.push(clone(x.find(b=>b.text===spec.heading))),x=>x.find(b=>b.text===spec.heading).type=level==='h3'?'h2':'h3']){const v=clone(b);change(v);assert.throws(()=>reviewedHeadingAnchors(v,page.facilityAnchors));}
  const specs=clone(page.facilityAnchors);specs[0].href='/regions/not-approved/#bad';assert.throws(()=>reviewedHeadingAnchors(b,specs));
 }
 assert.throws(()=>legacyHeadings([{type:'h3',text:'Original'}],[{heading:'Original',anchor:'original'}]),/H2/);
});
test('route,approval,architecture,anchor and metadata mutations are rejected',()=>{
 for(const change of [r=>r[0].approvalVerified=false,r=>r[0].status='candidate',r=>r[0].url='/regions/held/',r=>r[0].scopeKey='other',r=>r[0].candidateIds=['wrong'],r=>r[0].facilityAnchors[0].anchor='wrong',r=>r[0].regionUnitKeys=['wrong']]){const v=clone(rows);change(v);assert.throws(()=>regionalRows(v,a,c,p));}
 for(const change of [v=>v.pages.pop(),v=>v.pages.push(clone(v.pages[0])),v=>v.pages[0].parentHub='/',v=>v.pages[0].scopeKey='other']){const v=clone(a);change(v);assert.throws(()=>regionalRows(rows,v,c,p));}
 const changed=clone(rows);changed[0].snapshotId='wrong';assert.throws(()=>assertRegionalInput(changed));
});
test('intent and exact four-product family bindings stay separate',()=>{
 assert.deepEqual(rows.map(r=>r.purchaseIntentKey),['funeral-condolence-wreath','wedding-congratulation-wreath']);
 for(const row of rows){assert.doesNotThrow(()=>assertRegionalMetadata(row,c,p,products));assert.doesNotThrow(()=>validateRegionalPurchase(row,products,row.contentMarkdown));assert.equal(regionalMetadata(c,p,products,row.pageKey).regionalProductKeys.length,4);
  const v=clone(row);v.regionalProductFamilies=[row===rows[0]?'congrats':'funeral'];assert.throws(()=>validateRegionalPurchase(v,products),/family/);
  const wrong=clone(row);wrong.purchaseIntentKey='opening-congrats-wreath';assert.throws(()=>validateRegionalPurchase(wrong,products),/intent/);
 }
});
test('exact approved copy bytes and every public article field survive the adapter',()=>{
 assert.equal(sha(bytes('src/data/yeongdeungpo-copy.json')),'cdc2fda4970414d2d80c0aae7a939fb2d13f2bfbb210f3c2e663864945c01a1f');
 for(const approved of copy.articles){const row=rows.find(r=>r.slug===approved.slug);for(const [key,value] of Object.entries(approved)){if(key==='facilityAnchors')assert.deepEqual(row[key],value.map(({sourceIds,urlFragment,...rest})=>({...rest,href:urlFragment})));else assert.deepEqual(row[key],value,key);}}
 for(const row of rows){const omit=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);const digest=sha(canonical(Object.fromEntries(Object.entries(row).filter(([k])=>!omit.has(k)))));assert.equal(row.snapshotHash,digest);assert.equal(row.snapshotId,`direct-content-${row.slug}-${digest.slice(0,16)}`);for(const obj of [a,manifest,read('page-map')])assert.equal(obj.pages.find(p=>p.pageKey===row.pageKey).snapshotHash,digest);assert.equal(manifest.directRelease.contentHashes.find(p=>p.pageKey===row.pageKey).bodySha256,sha(row.contentMarkdown));}
});
test('eight exact fresh SKU photos,prices,alts and individual order destinations',()=>{
 assert.deepEqual(products.map(p=>p.officialSku),['B201','B203','B205','B060','C200','C203','C204','C205']);
 for(const product of products){const approved=copy.common.productCards.find(p=>p.sku===product.officialSku);assert.equal(product.name,approved.name);assert.equal(product.price,approved.basicPriceKRW);assert.equal(product.desc,approved.caption);assert.equal(product.imageAlt,approved.imageAlt);assert.equal(product.ctaLabel,approved.buttonLabel);assert.equal(product.orderUrl,approved.href);assert.equal(sha(bytes('public'+product.img)),approved.imageSha256);}
});
test('all prior regional adapters,bindings and common helpers remain byte-identical',()=>{
 for(const file of ['src/lib/regions-legacy.mjs','src/lib/guro-regions.mjs','src/lib/geumcheon-regions.mjs','src/lib/heading-anchors.mjs','src/lib/directory-banner-split.mjs','src/data/guro-plan-binding.json','src/data/geumcheon-plan-binding.json','src/components/SharedFlowerBanner.astro'])assert.equal(sha(bytes(file)),sha(bytes('tests/reference/geumcheon-runtime/'+file)),file);
});
test('baseline preview evidence remains immutable; current release authority is independently pinned',()=>{
 const baseline=JSON.parse(bytes('tests/reference/release-baseline/site-config.json'));assert.equal(baseline.productionApproved,false);assert.equal(read('site-config').productionApproved,true);assert.equal(read('site-config').hostnameOwnershipVerified,false);assert.equal(manifest.directRelease.publicationAuthorized,true);assert.deepEqual(manifest.directRelease.publishedCoverage,{numerator:0,denominator:2,percent:0});assert.equal(read('direct-checkpoint').productionEvidence,null);assert.equal(read('direct-checkpoint').searchIndexing,'not_verified');assert.equal(a.hubs.find(h=>h.category==='regions').indexable,false);
});
test('separate independent full rendered-copy review binds the final interface source',()=>{
 const review=read('copy-review-bindings');assert.equal(review.verdict,'COPY_AND_STATIC_INTERFACE_PASS');assert.equal(review.independentRenderedCopyReviewSha256,'11742cb949a22ddb9db9e6d6b04367269cde51f41976ff18ed1a9f7bbd93f1b5');assert.equal(review.additionalUiCopySha256,sha(bytes('src/data/yeongdeungpo-ui-copy.json')));for(const [file,expected] of Object.entries(review.commonSourceSha256))assert.equal(sha(bytes(file)),expected,file);assert.equal(review.screenQa,'UNVERIFIED');assert.equal(review.productionApproval,false);
});
