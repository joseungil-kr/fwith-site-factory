import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';import {spawnSync} from 'node:child_process';
import {validateDefinition,regionalRows,regionalMetadata,assertRegionalMetadata,validateRegionalPurchase,aliasTargets,directoryGroups} from '../src/lib/regions.mjs';
import {publishedDestinationsByUnit} from '../src/lib/directory-links.mjs';import {validateGraph,loadGraph} from '../scripts/qa_graph.mjs';import {pageSources} from '../src/lib/sources.mjs';
const read=n=>JSON.parse(fs.readFileSync(new URL('../src/data/'+n+'.json',import.meta.url),'utf8'));const bytes=p=>fs.readFileSync(new URL('../'+p,import.meta.url));const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const clone=structuredClone,c=read('region-coverage'),p=read('region-policy'),plan=read('dongjak-plan-binding'),rows=read('pages'),a=read('architecture'),products=read('products'),article=read('dongjak-article-copy'),common=read('dongjak-common-copy'),manifest=read('publish-manifest');
test('Dongjak N1 retains12 candidates=2 active+10 held and exact9/15/18 membership',()=>{
 assert.equal(plan.fixedPlanSha256,'8c17e681bc49944eec59698fbd6dfea3ff4c91773e0d45dbe955dae20b443e7c');assert.equal(plan.originalPlanN,1);assert.equal(plan.originalCandidateN,12);assert.equal(plan.activeCandidateN,2);assert.equal(plan.heldOriginalCandidateIds.length,10);assert.equal(c.units.length,9);assert.equal(c.administrativeCrosswalk.length,15);assert.equal(c.administrativeCrosswalk.flatMap(x=>x.relations).length,18);assert.equal(c.facilities.length,2);assert.equal(c.areaContexts.length,0);assert.doesNotThrow(()=>validateDefinition(c,p));assert.equal(regionalRows(rows,a,c,p).length,1);assert.equal(validateGraph(loadGraph()).pages,1);
 for(const id of plan.heldOriginalCandidateIds)assert.ok(!JSON.stringify([c,rows]).includes(id));
 assert.ok(c.units.some(u=>u.name==='상도1동'));assert.ok(c.administrativeCrosswalk.some(u=>u.name==='상도제1동'));
});
test('exact facility union never assigns Boramae to partial administrative relations',()=>{
 const page=rows[0];assert.deepEqual(page.regionUnitKeys,['동작구/법정동/흑석동','동작구/법정동/신대방동']);assert.deepEqual(page.facilityAnchors.map(a=>a.anchor),['cau-hospital','boramae-hospital']);
 for(const f of page.facilityAnchors)assert.equal(f.href,page.url+'#'+f.anchor);
 assert.deepEqual(aliasTargets('신대방동',rows,a,c,p),[page.url+'#boramae-hospital']);assert.deepEqual(aliasTargets('흑석동',rows,a,c,p),[page.url+'#cau-hospital']);assert.deepEqual(aliasTargets('신대방제1동',rows,a,c,p),[]);assert.deepEqual(aliasTargets('신대방제2동',rows,a,c,p),[]);
 const dest=publishedDestinationsByUnit(directoryGroups(rows,a,c,p));assert.equal(dest.size,2);assert.equal(dest.get('동작구/법정동/신대방동').length,1);
});
test('zero,N2,membership,policy,registry,held,union and anchor mutations fail closed',()=>{
 for(const change of [x=>x.representatives=[],x=>x.representatives.push(clone(x.representatives[0])),x=>x.units.pop(),x=>x.administrativeCrosswalk.pop(),x=>x.membershipRelationCount=17,x=>x.administrativeCrosswalk.at(-1).relations[0].scope='whole',x=>x.facilities[0].address='wrong',x=>x.facilities[0].sourceUrl='http://example.com/',x=>x.areaContexts.push({contextKey:'held'}),x=>x.representatives[0].candidateIds.push('pium-seoul'),x=>x.representatives[0].unitKeys.reverse(),x=>x.representatives[0].facilityAnchors[0].anchor='wrong']){const v=clone(c);change(v);assert.throws(()=>validateDefinition(v,p));}
 const bad=clone(p);bad.membershipSourceSha256='0'.repeat(64);assert.throws(()=>validateDefinition(c,bad));assert.throws(()=>regionalRows([],a,c,p),/parity/);
});
test('site/scope/assignment cannot downgrade or cross original regional modes',()=>{
 for(const field of ['siteKey','scopeKey','representativeAssignment'])for(const value of ['other','seoul-guro-flower-direct','seoul-geumcheon-flower-direct','seoul-yeongdeungpo-flower-direct','facility-purchase-context-v1']){const v=clone(c);v[field]=value;assert.throws(()=>validateDefinition(v,p));}
});
test('route/approval/metadata/purchase intent mutations fail closed',()=>{
 const changed=clone(rows);changed[0].approvalVerified=false;assert.throws(()=>regionalRows(changed,a,c,p),/approval/);
 for(const row of rows){assert.doesNotThrow(()=>assertRegionalMetadata(row,c,p,products));assert.doesNotThrow(()=>validateRegionalPurchase(row,products,row.contentMarkdown));}
 const v=clone(rows[0]);v.candidateIds=['wrong'];assert.throws(()=>assertRegionalMetadata(v,c,p,products));const bad=clone(rows[0]);bad.regionalProductFamilies=['congrats'];assert.throws(()=>validateRegionalPurchase(bad,products),/family/);assert.equal(regionalMetadata(c,p,products,rows[0].pageKey).candidateIds.length,2);
});
test('exact reviewed rev6 article/common byte pins and every public copy field',()=>{
 assert.equal(sha(bytes('src/data/dongjak-article-copy.json')),'428b4c3a66e648c15cf35c3887aee619c1e8eeb724f98ea8cdaa044e55001489');assert.equal(sha(bytes('src/data/dongjak-common-copy.json')),'b158fa9b9faa4049f11b94c8023073ab3aee7fa8fdd3088b7e5b6d5a9701649f');
 for(const [key,value] of Object.entries(article))assert.deepEqual(rows[0][key],value,key);
 const blocks=[];for(const section of article.sections){blocks.push('## '+section.heading,...(section.paragraphs||[]));for(const sub of section.subsections||[])blocks.push('### '+sub.heading,...sub.paragraphs);}assert.equal(rows[0].contentMarkdown,blocks.join('\n\n'));
 const review=read('copy-review-bindings');assert.equal(review.approvedArticleSha256,sha(bytes('src/data/dongjak-article-copy.json')));assert.equal(review.approvedCommonSha256,sha(bytes('src/data/dongjak-common-copy.json')));assert.equal(review.independentCopyReviewSha256,'fda619d326350cc6e1c47d6e67e6d3e8411e1872690089efd4ce89a5040b1c6b');
});
test('canonical snapshot and registry binding preserve full exact public article',()=>{
 for(const row of rows){const omit=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);const digest=sha(canonical(Object.fromEntries(Object.entries(row).filter(([k])=>!omit.has(k)))));assert.equal(row.snapshotHash,digest);assert.equal(row.snapshotId,`direct-content-${row.slug}-${digest.slice(0,16)}`);for(const obj of [a,manifest,read('page-map')])assert.equal(obj.pages[0].snapshotHash,digest);assert.equal(manifest.directRelease.contentHashes[0].bodySha256,sha(row.contentMarkdown));}
});
test('four actual funeral SKU prices,individual destinations and exact product photo bytes',()=>{
 assert.deepEqual(products.map(p=>p.officialSku),['B201','B203','B205','B060']);for(const product of products){const approved=common.productCards.find(p=>p.sku===product.officialSku);assert.equal(product.name,approved.name);assert.equal(product.price,approved.basicPriceKRW);assert.equal(product.desc,approved.caption);assert.equal(product.priceLabel,approved.priceLabel+' '+approved.basicPriceKRW.toLocaleString('en-US')+'원');assert.equal(product.orderUrl,approved.href);assert.equal(product.sourceUrl,approved.href);assert.equal(product.imageAlt,approved.imageAlt);assert.equal(sha(bytes('public'+product.img)),approved.imageSha256);}
});
test('all original adapters,bindings,helpers and native guard remain byte-preserved',()=>{
 for(const name of ['regions-legacy.mjs','guro-regions.mjs','geumcheon-regions.mjs','directory-banner-split.mjs','heading-anchors.mjs','sources.mjs'])assert.equal(sha(bytes('src/lib/'+name)),sha(bytes('tests/reference/geumcheon-runtime/src/lib/'+name)),name);
 for(const name of ['yeongdeungpo-regions.mjs','yeongdeungpo-heading-anchors.mjs'])assert.equal(sha(bytes('src/lib/'+name)),sha(bytes('tests/reference/yeongdeungpo-runtime/src/lib/'+name)),name);
 for(const name of ['guro-plan-binding','geumcheon-plan-binding'])assert.equal(sha(bytes('src/data/'+name+'.json')),sha(bytes('tests/reference/geumcheon-runtime/src/data/'+name+'.json')));
 for(const file of ['scripts/assert_preview_boundary.mjs','scripts/qa_static.py','scripts/qa_faq_products.py','scripts/test_faq_products.py','scripts/qa_shared_banners.py','scripts/test_shared_banners.py','scripts/test_directory_spacing.py','src/components/SharedFlowerBanner.astro'])assert.equal(sha(bytes(file)),sha(bytes('tests/reference/geumcheon-runtime/'+file)),file);
});
test('original template-specific tests retained unchanged in fixtures and relocation evidence',()=>{
 for(const name of ['answer-opening.test.mjs','sources.test.mjs'])assert.equal(sha(bytes('tests/reference/geumcheon-'+name+'.txt')),sha(bytes('tests/reference/geumcheon-runtime/tests/'+name)));
});
test('structured renderer safely exposes exact H3 anchors,real FAQ and sources last',()=>{
 const detail=bytes('src/pages/[category]/[slug].astro').toString();assert.match(detail,/<p>\{copy.firstAnswer\}<\/p>/);assert.match(detail,/copy.sections/);assert.match(detail,/<h3 id=\{sub.id\}>\{sub.heading\}<\/h3>/);assert.match(detail,/sub.paragraphs.map\(text=><p>\{text\}<\/p>\)/);assert.ok(detail.indexOf('<FaqSection')<detail.indexOf('<section class="source-references"'));assert.match(detail,/href=\{source.url\}/);assert.match(detail,/datetime=\{source.verifiedAt\}/);assert.match(detail,/data-source-type=\{source.type\}/);assert.match(detail,/approvedSourceNames.get\(source.url\)/);assert.doesNotMatch(detail,/set:html/);
 assert.deepEqual(pageSources(rows[0]),rows[0].sources);assert.deepEqual(rows[0].sources.map(s=>({label:s.name,url:s.url})),article.sourceLinks);
});
test('preview source cannot grant publication authority and indexable build fails',()=>{
 assert.equal(read('site-config').productionApproved,false);assert.equal(read('site-config').previewUrl,'https://dongjak-preview.invalid');assert.equal(read('site-config').hostnameOwnershipVerified,false);assert.equal(manifest.directRelease.publicationAuthorized,false);assert.deepEqual(manifest.directRelease.publishedCoverage,{numerator:0,denominator:1,percent:0});assert.equal(read('direct-checkpoint').productionEvidence,null);assert.equal(read('direct-checkpoint').searchIndexing,'not_verified');
 const result=spawnSync(process.execPath,['scripts/assert_preview_boundary.mjs'],{env:{...process.env,SITE_INDEXABLE:'true'},encoding:'utf8'});assert.notEqual(result.status,0);assert.match(result.stderr,/Production-indexable build is disabled/);assert.equal(a.hubs.find(h=>h.category==='regions').indexable,false);assert.equal(a.hubs.find(h=>h.category==='regions').children,1);
});
