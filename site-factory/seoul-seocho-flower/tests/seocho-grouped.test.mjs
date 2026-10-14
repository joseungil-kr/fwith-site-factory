import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';import {spawnSync} from 'node:child_process';
import {validateDefinition,regionalRows,regionalMetadata,assertRegionalMetadata,validateRegionalPurchase,directoryGroups,aliasTargets,hubState} from '../src/lib/regions.mjs';
import {pageSources,isExactReviewedHttp} from '../src/lib/seocho-sources.mjs';
import {pageSources as strictSources} from '../src/lib/sources.mjs';
import {frozenBindingSha256} from '../src/lib/seocho-regions.mjs';
import {publishedDestinationsByUnit,publishedUnassignedDistrictDestinations} from '../src/lib/directory-links.mjs';
import {validateGraph,loadGraph} from '../scripts/qa_graph.mjs';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const c=read('src/data/region-coverage.json'),p=read('src/data/region-policy.json'),b=read('src/data/seocho-plan-binding.json'),pages=read('src/data/pages.json'),a=read('src/data/architecture.json'),products=read('src/data/products.json');
const original=read('src/data/seocho-approved/plan/fixed-plan.json'),membership=read('src/data/seocho-approved/plan/membership.json'),copy=read('src/data/seocho-copy.json');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
test('Seocho exact accepted source hashes and frozen transform are pinned',()=>{
 assert.equal(sha(canonical(b)),frozenBindingSha256);
 for(const [file,key,digest] of [['plan/fixed-plan.json','fixedPlanSha256','5675a7cc1cf5b142458133cb2fc55ce7224ca5e819b2e11f6684bc2d59728318'],['copy/article-copy.rev4.json','approvedArticlesSha256','78bc5af47bf4d1b8bd4c17e4cedd34ecd857c763e79c90df53607d1849c1623f'],['copy/common-visible-copy.rev2.json','approvedCommonSha256','22b4b6d12142767cee9dbba40c31db290675f942000a6b86338fbf29b4a3b4cb']]){
  assert.equal(sha(fs.readFileSync('src/data/seocho-approved/'+file)),digest);assert.equal(b[key],digest);
 }
 assert.deepEqual(b.candidateLedger,original.candidateLedger);assert.deepEqual(b.heldPageDecisions,original.heldPageDecisions);
 assert.deepEqual([original.originalPlanN,b.originalCandidateN,b.heldSeparateURLDecisionN],[2,8,7]);
});
test('Seocho exact ten legal, eighteen administrative and twenty-three relationships',()=>{
 assert.deepEqual(c.units.map(x=>({code:x.legalCode,name:x.name})),membership.legalUnits.map(({code,name})=>({code,name})));
 assert.deepEqual(c.administrativeCrosswalk.map(x=>({code:x.administrativeCode,name:x.name})),membership.administrativeUnits.map(({code,name})=>({code,name})));
 assert.deepEqual(c.administrativeCrosswalk.flatMap(x=>x.relations.map(r=>[x.administrativeCode,r.unitKey])),membership.relations.map(r=>[r.administrativeCode,'서초구/법정동/'+r.legalName]));
 assert.deepEqual([c.units.length,c.administrativeCrosswalk.length,c.membershipRelationCount],[10,18,23]);
 assert.deepEqual(c.administrativeCrosswalk.find(x=>x.name==='반포3동').relations.map(x=>x.unitKey),['서초구/법정동/잠원동']);
});
test('Three physical facilities and one addressless occasion generate only two grouped routes',()=>{
 assert.deepEqual(c.facilities.map(f=>[f.facilityKey,f.unitKey,f.administrativeCode]),[['seoul-st-mary-funeral','서초구/법정동/반포동',null],['eltower','서초구/법정동/양재동',null],['at-center-exhibition','서초구/법정동/양재동',null]]);
 for(const key of ['unitKey','legalCode','administrativeCode','physicalAddress'])assert.equal(c.buyerOccasions[0][key],null);
 assert.deepEqual(c.administrativeFacilityAssignments,[]);assert.equal(regionalRows(pages,a,c,p).length,2);assert.equal(pages[1].buyerOccasionAnchors[0].anchor,'opening-relocation');assert.equal(pages[1].buyerOccasionAnchors[0].candidateId,'opening-relocation-occasion');
 const groups=directoryGroups(pages,a,c,p);assert.equal(groups.flatMap(x=>x.items).length,2);
 assert.equal([...publishedDestinationsByUnit(groups).values()].flat().length,3);assert.equal([...publishedUnassignedDistrictDestinations(groups).values()].flat().length,0);
 assert.deepEqual(aliasTargets('반포3동',pages,a,c,p),[]);assert.deepEqual(aliasTargets('방배동',pages,a,c,p),[]);
 assert.equal(aliasTargets('양재동',pages,a,c,p).length,2);assert.equal(aliasTargets('반포동',pages,a,c,p).length,1);
 assert.deepEqual(hubState(2,true),{exists:true,indexable:false,menu:false,sitemap:false});
});
const mutations={
 'missing legal':x=>x.units.pop(),'missing admin':x=>x.administrativeCrosswalk.pop(),'missing relation':x=>x.administrativeCrosswalk.at(-1).relations.pop(),'wrong legal code':x=>x.units[0].legalCode='wrong','wrong admin code':x=>x.administrativeCrosswalk[0].administrativeCode='wrong','wrong membership hash':x=>x.membershipSourceSha256='0'.repeat(64),'invented facility':x=>x.facilities.push(structuredClone(x.facilities[0])),'unassigned facility':x=>x.facilities[0].unitKey=null,'admin facility inference':x=>x.facilities[0].administrativeCode='1165058100','wrong address':x=>x.facilities[0].address='wrong','occasion as facility':x=>x.facilities.push(structuredClone(x.buyerOccasions[0])),'occasion location':x=>x.buyerOccasions[0].physicalAddress='서울','occasion as physical':x=>x.buyerOccasions[0].contextType='physical-facility','unknown opt in':x=>x.representativeAssignment='unknown','cross region opt in':x=>x.siteKey='seoul-gwanak-flower-direct','held facility promoted':x=>x.representatives[1].candidateIds.push('at-center-wedding'),'missing route':x=>x.representatives.pop(),'duplicate route':x=>x.representatives.push(structuredClone(x.representatives[0])),'wrong anchor':x=>x.representatives[0].facilityAnchors[0].anchor='changed','facility into occasion':x=>x.representatives[1].buyerOccasionAnchors.push(x.representatives[1].facilityAnchors[0]),'invented geo field':x=>x.deliveryGuaranteed=true
};
for(const [name,change] of Object.entries(mutations))test('Seocho rejects '+name,()=>{const value=structuredClone(c);change(value);assert.throws(()=>validateDefinition(value,p));});
test('Four exact SKU products per intent, all metadata and graph parity',()=>{
 assert.deepEqual(validateGraph(loadGraph()),{pages:2,hubs:1});
 for(const page of pages){assertRegionalMetadata(page,c,p,products);validateRegionalPurchase(page,products);assert.equal(page.regionalProductKeys.length,4);assert.equal(page.productCardLimit,4);const got=regionalMetadata(c,p,products,page.pageKey);assert.deepEqual(got.regionUnitKeys,page.regionUnitKeys);}
 for(const field of ['price','officialSku','imageAlt','imageSha256','sourceUrl']){const changed=structuredClone(products);changed[0][field]='changed';assert.throws(()=>regionalMetadata(c,p,changed,pages[0].pageKey));}
});
test('Reviewed exact public HTTP sources retain original strings without weakening shared HTTPS gate',()=>{
 const actual=pageSources(pages[0]);assert.deepEqual(actual.map(({name,url})=>({name,url})),copy.articles[0].sourceLinks);
 assert.equal(actual.filter(s=>isExactReviewedHttp(s.url)).length,2);assert.throws(()=>strictSources(pages[0]));
 const source=actual[0];for(const url of [source.url+'#changed',source.url+'&extra=1',source.url.replace('kfh.','evil.'),'http://example.com/',source.url.replace('http:','javascript:')])assert.throws(()=>pageSources({sources:[{...source,url}]}));
 for(const key of ['type','verifiedAt'])assert.throws(()=>pageSources({sources:[{...source,[key]:'changed'}]}));
});
test('Seocho renderer escapes single-copy sections and renders exact section SKUs',()=>{
 const detail=fs.readFileSync('src/pages/[category]/[slug].astro','utf8');assert.match(detail,/matches.length!==1/);assert.match(detail,/section\.productCardSkus/);assert.match(detail,/section\.paragraphs\.map\(paragraph=><p>\{paragraph\}<\/p>\)/);assert.doesNotMatch(detail,/<MarkdownContent|set:html/);assert.equal((detail.match(/<p>\{page.firstAnswer\}<\/p>/g)||[]).length,1);
 const layout=fs.readFileSync('src/layouts/BaseLayout.astro','utf8');assert.match(layout,/<main id="main-content" tabindex="-1">/);
});
test('Compiled all-route exact text and assets gate runs on current output',()=>{const run=spawnSync('python3',['-c','from pathlib import Path; import sys; sys.path.insert(0,"scripts"); from qa_seocho import inspect; inspect(Path("."),write=False,quiet=True)'],{encoding:'utf8'});assert.equal(run.status,0,run.stdout+run.stderr);});
test('Preview boundary rejects production and arbitrary host configuration',()=>{
 for(const extra of [{SITE_INDEXABLE:'true'},{SITE_URL:'https://example.com'}]){const run=spawnSync(process.execPath,['scripts/assert_preview_boundary.mjs'],{env:{...process.env,...extra},encoding:'utf8'});assert.notEqual(run.status,0);}
 assert.equal(spawnSync(process.execPath,['scripts/assert_preview_boundary.mjs'],{env:{...process.env,SITE_INDEXABLE:'false',SITE_URL:'https://seoul-seocho.local.invalid'}}).status,0);
});
