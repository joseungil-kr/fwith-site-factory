import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';
import {validateGraph,loadGraph} from '../scripts/qa_graph.mjs';
import {pageSources} from '../src/lib/sources.mjs';
import {validateDefinition,assertRegionalMetadata,directoryGroups} from '../src/lib/regions.mjs';
import {selectProducts} from '../src/lib/catalog.mjs';
const read=n=>JSON.parse(fs.readFileSync(new URL('../src/data/'+n+'.json',import.meta.url),'utf8'));
const bytes=p=>fs.readFileSync(new URL('../'+p,import.meta.url));const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const plan=read('guro-plan-binding'),pages=read('pages'),coverage=read('region-coverage'),policy=read('region-policy'),products=read('products'),manifest=read('publish-manifest');
test('Guro geography and fixed purchase plan are distinct exact inventories',()=>{
 assert.equal(coverage.districts[0].name,'구로구');assert.equal(coverage.units.length,10);assert.equal(coverage.administrativeCrosswalk.length,16);assert.equal(coverage.administrativeCrosswalk.flatMap(a=>a.relations).length,18);
 assert.equal(pages.length,plan.originalPlanN);assert.deepEqual(pages.map(p=>p.url),plan.representatives.map(r=>r.url));assert.equal(new Set(coverage.representatives.flatMap(r=>r.unitKeys)).size,3);assert.ok(coverage.administrativeCrosswalk.flatMap(a=>a.relations).every(r=>r.scope==='partial'));assert.doesNotThrow(()=>validateDefinition(coverage,policy));
});
test('all customer fields are snapshot-bound across all four collections',()=>{
 for(const p of pages){const omit=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);const digest=sha(canonical(Object.fromEntries(Object.entries(p).filter(([k])=>!omit.has(k)))));assert.equal(p.snapshotHash,digest);assert.equal(p.snapshotId,`direct-content-${p.slug}-${digest.slice(0,16)}`);
 for(const c of [manifest,read('page-map'),read('architecture')]){const x=c.pages.find(x=>x.pageKey===p.pageKey);assert.equal(x.snapshotHash,digest);for(const k of ['candidateIds','facilityAnchors','contextKey','purchaseIntentKey','regionUnitKeys'])assert.deepEqual(x[k],p[k]);}
 const h=manifest.directRelease.contentHashes.find(x=>x.pageKey===p.pageKey);assert.equal(h.publicSourceSha256,digest);assert.equal(h.bodySha256,sha(p.contentMarkdown));}
});
test('shared graph and strict HTTPS citations remain unchanged gates',()=>{
 assert.equal(validateGraph(loadGraph()).pages,3);for(const p of pages){assert.ok(pageSources(p).length>0);assert.doesNotThrow(()=>assertRegionalMetadata(p,coverage,policy,products));}
});
test('no prior regional prose, held venue or fake area address leaks into customer records',()=>{
 const text=JSON.stringify(pages);assert.doesNotMatch(text,/강서구|이대서울병원|메이필드|강서아트리움|서울창업허브|seoul-gangseo|제이오스티엘|j-ostiel|14층|432-30/);
 assert.equal(Object.hasOwn(coverage.areaContexts[0],'address'),false);assert.equal(coverage.facilities.length,6);assert.equal(coverage.areaContexts.length,1);
});
test('products keep exact fresh SKU prices, photo hashes and individual detail CTAs',()=>{
 const expected={B201:[59000,'7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3'],B203:[79000,'0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114'],B205:[109000,'1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e'],B060:[149000,'a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3'],C200:[59000,'0e5c0e37f5a02b0448a0dd9b3aa48c4bd1ebe38862a9dde662ef2e1c14eee905'],C203:[79000,'d3bd30015f4465f6db3d43c37a3088d383173e1bc0b46ff429ed24b9c251625a'],C204:[99000,'05a71d0a3a624c7e27e0575baab02c21f87cc409a1de5389bd4c42b2789dc16d'],C205:[149000,'b0fa2c913adf258617e34ce0175cbdc282b83e6b47db556234380353c047d5e9']};
 assert.deepEqual(products.map(p=>p.officialSku),Object.keys(expected));for(const p of products){assert.equal(p.price,expected[p.officialSku][0]);assert.equal(sha(bytes('public'+p.img)),expected[p.officialSku][1]);assert.equal(p.orderUrl,'https://fwith.co.kr/shop/item.php?it_id='+p.officialSku);}
 for(const p of pages){assert.equal(p.productCardLimit,4);assert.deepEqual(selectProducts(p,products,4).map(x=>x.key),p.regionalProductKeys);for(const key of p.regionalProductKeys)assert.ok(p.contentMarkdown.includes(products.find(x=>x.key===key).orderUrl));}
});
test('shared banners preserve the three approved image bytes and intrinsic dimensions',()=>{
 const expected=['b8d973861fe81839ec7765d9dd506deb9d1055614c200479aa72a632cf0c5253','bc782e91dadd7d07840ea9cbe6154fb21941dd7f9bf32c53bb2991bc301439df','4cae6c69e4c6549ed277fd3b2acc32c9a797a570de194bc48a6045b50f28283b'];
 const m=read('shared-banner-manifest');assert.deepEqual(m.map(x=>x.previousWebpSha256),expected);const amendment=read('shared-banner-phone-amendment');assert.deepEqual(m.map(x=>x.sha256),m.map(x=>amendment.replacements['public/images/shared-banners/'+x.name+'.webp'].toSha256));for(const a of m){assert.equal(a.width,1774);assert.equal(a.height,887);assert.equal(sha(bytes('public/images/shared-banners/'+a.name+'.webp')),a.sha256);}
});
test('customer-copy approval never becomes public deployment or indexing evidence',()=>{
 assert.equal(read('site-config').productionApproved,true);assert.equal(manifest.directRelease.publicationAuthorized,true);assert.deepEqual(manifest.directRelease.publishedCoverage,{numerator:0,denominator:3,percent:0});assert.equal(read('direct-checkpoint').productionEvidence,null);assert.equal(read('direct-checkpoint').searchIndexing,'not_verified');
});
test('one canonical article per intent with complete named-destination directory',()=>{
 const groups=directoryGroups(pages,read('architecture'),coverage,policy);assert.equal(groups.flatMap(g=>g.items).length,3);assert.equal(groups.flatMap(g=>g.items).flatMap(x=>x.representative.facilityAnchors).length,7);
 assert.deepEqual(read('architecture').hubs.filter(h=>h.children>0).map(h=>h.url),['/regions/']);assert.equal(manifest.directRelease.renderedHtmlRouteCount,5);
});
test('approved copy and common customer UI are bound to independent review hashes',()=>{
 const review=read('copy-review-bindings');assert.equal(review.verdict,'PASS');for(const [file,digest] of Object.entries(review.commonSourceSha256)){let current=file==='src/data/site-config.json'?bytes('tests/reference/release-baseline/site-config.json'):bytes(file);if(file==='src/components/SharedFlowerBanner.astro'){const text=current.toString();assert.ok(!text.includes('<figcaption>'));assert.equal(sha(current),read('shared-banner-phone-amendment').replacements[file].toSha256);const marker='\n</figure>';assert.equal(text.split(marker).length,2);assert.equal(text.split(' 전화 1844-0644.').length,4);current=Buffer.from(text.replaceAll(' 전화 1844-0644.','').replace(marker,'\n  <figcaption>꽃이랑 공통 안내 이미지 · 실제 판매상품 사진이 아닌 AI 생성 이미지입니다.</figcaption>'+marker));}assert.equal(sha(current),digest,file);}
 const strip=v=>Array.isArray(v)?v.map(strip):v&&typeof v==='object'?Object.fromEntries(Object.entries(v).filter(([k])=>!['status','approvalVerified'].includes(k)).map(([k,x])=>[k,strip(x)])):v;
 for(const [file,digest] of Object.entries(review.approvedMetadataOnlyTransform.normalizedFileSha256))assert.equal(sha(canonical(strip(JSON.parse(bytes(file).toString())))),digest);
 assert.deepEqual(pages.map(p=>sha(canonical(Object.fromEntries(review.customerFields.map(k=>[k,p[k]]))))),review.customerCopyObjectSha256);
 assert.deepEqual(pages.map(p=>sha(p.contentMarkdown)),review.bodySha256);assert.deepEqual(pages.map(p=>sha(canonical(p.faq))),review.faqSha256);
});
