import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {validateDefinition,regionalRows,regionalMetadata,assertRegionalMetadata,validateRegionalPurchase,aliasTargets} from '../src/lib/regions.mjs';
import {publishedDestinationsByUnit} from '../src/lib/directory-links.mjs';
import {reviewedHeadingAnchors} from '../src/lib/heading-anchors.mjs';
import {displayMarkdownBlocks} from '../src/lib/content.mjs';
const read=n=>JSON.parse(fs.readFileSync(new URL('../src/data/'+n+'.json',import.meta.url),'utf8'));
const clone=x=>structuredClone(x),coverage=read('region-coverage'),policy=read('region-policy'),plan=read('guro-plan-binding'),pages=read('pages'),architecture=read('architecture'),products=read('products');
const approved=()=>{const c=clone(coverage),p=clone(policy),a=clone(architecture),rows=clone(pages);for(const r of c.representatives)r.status='approved';for(const row of rows)Object.assign(row,{status:'approved',approvalVerified:true});return {c,p,a,rows};};
test('Guro frozen N3 preserves original8 trace,7activecontexts and no held customer record',()=>{
 assert.equal(plan.fixedPlanSha256,'0e69c1417605fb97738e810c75e51d85c8595cd9835028bf9a38a4fa503630db');
 assert.equal(plan.originalPlanN,3);assert.equal(plan.originalCandidateN,8);assert.equal(plan.activeCandidateN,7);assert.deepEqual(plan.heldOriginalCandidateIds,['j-ostiel-tiffany']);
 assert.equal(coverage.facilities.length,6);assert.equal(coverage.areaContexts.length,1);assert.equal(coverage.units.length,10);assert.equal(coverage.administrativeCrosswalk.length,16);assert.equal(coverage.administrativeCrosswalk.flatMap(x=>x.relations).length,18);
 assert.doesNotThrow(()=>validateDefinition(coverage,policy));assert.ok(!JSON.stringify([coverage,pages]).includes('j-ostiel'));
});
test('all7 active member anchors exist once on exact H2 and use correct unit union',()=>{
 for(const r of coverage.representatives){const page=pages.find(p=>p.pageKey===r.pageKey),blocks=displayMarkdownBlocks(page.contentMarkdown,page.firstAnswer),anchors=reviewedHeadingAnchors(blocks,page.facilityAnchors);assert.equal(anchors.size,r.candidateIds.length);assert.deepEqual([...new Set(r.facilityAnchors.map(a=>a.unitKey))],r.unitKeys);for(const a of r.facilityAnchors)assert.equal(a.href,page.url+'#'+a.anchor);}
});
test('actual grouped route data satisfy structural approval rules only with explicit reviewed flags',()=>{
 const {c,p,a,rows}=approved();assert.equal(regionalRows(rows,a,c,p).length,3);
 const denied=clone(rows);denied[0].approvalVerified=false;assert.throws(()=>regionalRows(denied,a,c,p),/approval/);
 for(const row of rows){assert.doesNotThrow(()=>assertRegionalMetadata(row,c,p,products));assert.doesNotThrow(()=>validateRegionalPurchase(row,products,row.contentMarkdown));}
});
test('Guro cannot opt into another site/scope or the legacy single-facility mode',()=>{
 for(const mutation of [c=>c.siteKey='other',c=>c.scopeKey='other',c=>c.representativeAssignment='facility-purchase-context-v1']){const c=clone(coverage);mutation(c);assert.throws(()=>validateDefinition(c,policy),/opt-in/);}
});
test('unknown/duplicate/moved members, wrong union and denominator are rejected',()=>{
 for(const mutate of [c=>c.representatives[0].candidateIds.push('unknown'),c=>c.representatives[1].candidateIds.push(c.representatives[0].candidateIds[0]),c=>c.representatives[0].unitKeys.reverse(),c=>c.representatives.pop(),c=>c.representatives[0].purchaseIntentKey='wedding-congrats-wreath']){const c=clone(coverage);mutate(c);assert.throws(()=>validateDefinition(c,policy),/frozen|union|duplicate/);}
});
test('facility identity and strict HTTPS cannot drift or impersonate an area address',()=>{
 for(const mutate of [c=>c.facilities[0].sourceUrl=c.facilities[0].sourceUrl.replace('https:','http:'),c=>c.facilities[0].sourceUrl='https://u:p@example.com/',c=>c.facilities[0].address='fake',c=>c.areaContexts[0].address='fake office',c=>c.facilities.push({...c.facilities[0],facilityKey:'fake'})]){const c=clone(coverage);mutate(c);assert.throws(()=>validateDefinition(c,policy),/registry drift|HTTPS|invalid/);}
});
test('metadata and intent/product families are bound',()=>{
 const {c,p}=approved(),row=clone(pages[0]);row.candidateIds=['wrong'];assert.throws(()=>assertRegionalMetadata(row,c,p,products),/binding drift/);
 const bad=clone(pages[0]);bad.regionalProductFamilies=['congrats'];assert.throws(()=>validateRegionalPurchase(bad,products),/family/);
 const meta=regionalMetadata(c,p,products,pages[0].pageKey);assert.deepEqual(meta.candidateIds,pages[0].candidateIds);
});
test('same canonical article retains all distinct facility fragments on legal/admin aliases',()=>{
 const {c,p,a,rows}=approved();const group={items:c.representatives.map(r=>({representative:r,page:rows.find(x=>x.pageKey===r.pageKey)}))};const dest=publishedDestinationsByUnit([group]);
 assert.equal(dest.get('구로구/법정동/구로동').length,4);assert.equal(dest.get('구로구/법정동/신도림동').length,2);assert.equal(dest.get('구로구/법정동/고척동').length,1);
 assert.equal(new Set(dest.get('구로구/법정동/신도림동').map(x=>x.href.split('#')[0])).size,1);assert.equal(aliasTargets('신도림동',rows,a,c,p).length,2);
});
test('heading renderer rejects missing/duplicate headings and duplicate anchors, legacy stays unchanged',()=>{
 const blocks=[{type:'h2',text:'A'}];assert.equal(reviewedHeadingAnchors(blocks,undefined).size,0);assert.equal(reviewedHeadingAnchors(blocks,[{heading:'A',anchor:'a'}]).get('A'),'a');
 for(const [b,a] of [[blocks,[{heading:'B',anchor:'a'}]],[[...blocks,...blocks],[{heading:'A',anchor:'a'}]],[blocks,[{heading:'A',anchor:'a'},{heading:'A',anchor:'a'}]]])assert.throws(()=>reviewedHeadingAnchors(b,a),/missing|duplicate/);
});

test('frozen Guro N3 rejects zero representatives and empty emitted rows',()=>{const c=clone(coverage);c.representatives=[];assert.throws(()=>validateDefinition(c,policy),/denominator/);assert.throws(()=>regionalRows([],architecture,c,policy),/denominator/);const valid=approved();assert.throws(()=>regionalRows([],valid.a,valid.c,valid.p),/parity/);});
