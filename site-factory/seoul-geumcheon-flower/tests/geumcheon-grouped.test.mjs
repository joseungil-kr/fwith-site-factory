import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';import {spawnSync} from 'node:child_process';
import {validateDefinition,regionalRows,regionalMetadata,assertRegionalMetadata,validateRegionalPurchase,aliasTargets,directoryGroups} from '../src/lib/regions.mjs';
import {publishedDestinationsByUnit} from '../src/lib/directory-links.mjs';import {reviewedHeadingAnchors} from '../src/lib/heading-anchors.mjs';import {displayMarkdownBlocks} from '../src/lib/content.mjs';import {validateGraph,loadGraph} from '../scripts/qa_graph.mjs';
const read=n=>JSON.parse(fs.readFileSync(new URL('../src/data/'+n+'.json',import.meta.url),'utf8'));const bytes=p=>fs.readFileSync(new URL('../'+p,import.meta.url));const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const clone=structuredClone,c=read('region-coverage'),p=read('region-policy'),plan=read('geumcheon-plan-binding'),rows=read('pages'),a=read('architecture'),products=read('products'),copy=read('geumcheon-copy'),manifest=read('publish-manifest');
test('Geumcheon exact frozen N1 preserves 10 leads,2 active and8 held with3/10/10 membership',()=>{
 assert.equal(plan.fixedPlanSha256,'4371357faa2f5ff54d31689ec270f8cf8a5da76e7faa73a4e937f90ee6cecc37');assert.equal(plan.originalPlanN,1);assert.equal(plan.originalCandidateN,10);assert.equal(plan.activeCandidateN,2);assert.equal(plan.heldOriginalCandidateIds.length,8);
 assert.equal(c.facilities.length,2);assert.equal(c.areaContexts.length,0);assert.equal(c.units.length,3);assert.equal(c.administrativeCrosswalk.length,10);assert.equal(c.administrativeCrosswalk.flatMap(x=>x.relations).length,10);assert.doesNotThrow(()=>validateDefinition(c,p));assert.equal(regionalRows(rows,a,c,p).length,1);assert.equal(validateGraph(loadGraph()).pages,1);
 for(const id of plan.heldOriginalCandidateIds)assert.ok(!JSON.stringify([c,rows]).includes(id));
});
test('exact two active facility anchors and unit union on one canonical article',()=>{
 const page=rows[0],anchors=reviewedHeadingAnchors(displayMarkdownBlocks(page.contentMarkdown,page.firstAnswer),page.facilityAnchors);assert.equal(anchors.size,2);assert.deepEqual(page.regionUnitKeys,['금천구/법정동/가산동','금천구/법정동/독산동']);
 for(const f of page.facilityAnchors)assert.equal(f.href,page.url+'#'+f.anchor);
 const dest=publishedDestinationsByUnit(directoryGroups(rows,a,c,p));assert.equal(dest.get('금천구/법정동/가산동').length,1);assert.equal(dest.get('금천구/법정동/독산동').length,1);assert.equal(dest.get('금천구/법정동/시흥동'),undefined);
 assert.deepEqual(aliasTargets('독산제4동',rows,a,c,p),['/regions/geumcheon-funeral-wreath/#doksan-funeral']);assert.deepEqual(aliasTargets('시흥제1동',rows,a,c,p),[]);
});
test('zero,N2,membership,registry,held,union and anchor mutations fail closed',()=>{
 for(const change of [x=>x.representatives=[],x=>x.representatives.push(clone(x.representatives[0])),x=>x.units.pop(),x=>x.administrativeCrosswalk.pop(),x=>x.facilities[0].address='wrong',x=>x.facilities[0].sourceUrl='http://example.com/',x=>x.areaContexts.push({contextKey:'held'}),x=>x.representatives[0].candidateIds.push('gasan-digital-opening'),x=>x.representatives[0].unitKeys.reverse(),x=>x.representatives[0].facilityAnchors[0].anchor='wrong']){const v=clone(c);change(v);assert.throws(()=>validateDefinition(v,p));}
 assert.throws(()=>regionalRows([],a,c,p),/parity/);
});
test('site/scope/assignment opt-ins cannot downgrade or cross Guro/legacy',()=>{
 for(const field of ['siteKey','scopeKey','representativeAssignment'])for(const value of ['other','seoul-guro-flower-direct','facility-purchase-context-v1']){const v=clone(c);v[field]=value;assert.throws(()=>validateDefinition(v,p));}
});
test('route/approval/metadata/intent and family mutations fail closed',()=>{
 const changed=clone(rows);changed[0].approvalVerified=false;assert.throws(()=>regionalRows(changed,a,c,p),/approval/);
 for(const row of rows){assert.doesNotThrow(()=>assertRegionalMetadata(row,c,p,products));assert.doesNotThrow(()=>validateRegionalPurchase(row,products,row.contentMarkdown));}
 const v=clone(rows[0]);v.candidateIds=['wrong'];assert.throws(()=>assertRegionalMetadata(v,c,p,products));const bad=clone(rows[0]);bad.regionalProductFamilies=['congrats'];assert.throws(()=>validateRegionalPurchase(bad,products),/family/);assert.equal(regionalMetadata(c,p,products,rows[0].pageKey).candidateIds.length,2);
});
test('exact approved copy file, body, FAQ and customer fields are preserved',()=>{
 assert.equal(sha(bytes('src/data/geumcheon-copy.json')),'01f9e71d13ad3a11122b832d649f60b6da976c85513ee90b6ccb531737fb7455');
 for(const [key,value] of Object.entries(copy.article)){if(key==='facilityAnchors')assert.deepEqual(rows[0][key].map(({unitKey,...x})=>x),value);else assert.deepEqual(rows[0][key],value,key);}
 for(const row of rows){const omit=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);const digest=sha(canonical(Object.fromEntries(Object.entries(row).filter(([k])=>!omit.has(k)))));assert.equal(row.snapshotHash,digest);assert.equal(row.snapshotId,`direct-content-${row.slug}-${digest.slice(0,16)}`);for(const obj of [a,manifest,read('page-map')])assert.equal(obj.pages[0].snapshotHash,digest);assert.equal(manifest.directRelease.contentHashes[0].bodySha256,sha(row.contentMarkdown));}
});
test('four real funeral SKUs, exact photo bytes, prices and individual CTAs',()=>{
 assert.deepEqual(products.map(p=>p.officialSku),['B201','B203','B205','B060']);for(const product of products){const approved=copy.common.productCards.find(p=>p.key===product.key);assert.equal(product.name,approved.name);assert.equal(product.price,approved.basicPriceKRW);assert.equal(product.desc,approved.description);assert.equal(product.orderUrl,approved.ctaUrl);assert.equal(sha(bytes('public'+product.img)),approved.imageSha256);}
});
test('byte-preserved shared legacy,Guro and midpoint helper',()=>{
 for(const [file,expected] of Object.entries({'src/lib/regions-legacy.mjs':'cf2f44ce1feff2f44bb9213d55a63eac2f83dfadb49cac116c60769471ff29c1','src/lib/guro-regions.mjs':'c86a3994a4a1cac9e42371bd687d8dab47a4f14b7af9af6841021e4beeb2701f','src/lib/directory-banner-split.mjs':'04ed49395e2a3458c9b01c74eff57f425ed693e9f713b59bfe7343a4c433a19c','src/components/SharedFlowerBanner.astro':'bffdc5a802a911d688e388faa55ece9e1bf6b00e04c8fab0873e779b35702f74'}))assert.equal(sha(bytes(file)),expected,file);
});
test('baseline preview evidence remains immutable; current release authority is independently pinned',()=>{
 const baseline=JSON.parse(bytes('tests/reference/release-baseline/site-config.json'));assert.equal(baseline.productionApproved,false);assert.equal(read('site-config').productionApproved,true);assert.equal(read('site-config').hostnameOwnershipVerified,false);assert.equal(manifest.directRelease.publicationAuthorized,true);assert.deepEqual(manifest.directRelease.publishedCoverage,{numerator:0,denominator:1,percent:0});assert.equal(read('direct-checkpoint').productionEvidence,null);assert.equal(read('direct-checkpoint').searchIndexing,'not_verified');assert.equal(a.hubs.find(h=>h.category==='regions').indexable,false);
});

test('rendered common-copy source files retain independent-review bindings',()=>{
 const review=read('copy-review-bindings');for(const [file,digest] of Object.entries(review.commonSourceSha256))assert.equal(sha(bytes(file)),digest,file);assert.equal(review.approvedCopySha256,sha(bytes('src/data/geumcheon-copy.json')));
});
