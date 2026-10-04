import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateDefinition,regionalRows,directoryGroups,aliasTargets,regionalMetadata,assertRegionalMetadata} from '../src/lib/regions.mjs';
import {selectProducts} from '../src/lib/catalog.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const coverage=read('region-coverage'),policy=read('region-policy'),products=read('products');
function fixture(){
 const c=structuredClone(coverage),p=structuredClone(policy);
 for(const r of c.representatives)r.status='approved';
 for(const v of p.visualBindings)v.status='approved';
 const pages=c.representatives.map(r=>({...r,...regionalMetadata(c,p,products,r.pageKey),category:'regions',pageType:'regional-service',routeType:'category',status:'approved',approvalVerified:true,snapshotId:'offline-fixture-only',snapshotHash:'a'.repeat(64),cardSummary:'Fixture'}));
 const architecture={siteKey:p.siteKey,pages:pages.map(page=>({...page,pageRole:'REGION_SERVICE_LANDING',parentHub:'/regions/',localizationPolicy:'local-required'}))};
 return {c,p,pages,architecture};
}
test('canonical24 and administrative37/48 match the pinned membership without page quota',()=>{
 validateDefinition(coverage,policy);assert.equal(coverage.countIsPageQuota,false);
 assert.equal(coverage.units.length,24);assert.equal(coverage.representatives.length,24);
 assert.equal(coverage.administrativeCrosswalk.length,37);assert.equal(coverage.administrativeCrosswalk.flatMap(a=>a.relations).length,48);
 assert.equal(new Set([...coverage.units.map(u=>u.name),...coverage.administrativeCrosswalk.map(a=>a.name)]).size,49);
 assert.deepEqual(coverage.districts.map(d=>coverage.units.filter(u=>u.districtKeys.includes(d.key)).length),[9,7,8]);
});
test('pending source has no regional pages or links and cannot become approved by geography',()=>{
 assert.deepEqual(directoryGroups([],read('architecture'),coverage,policy),[]);
 const f=fixture(),pendingCoverage=structuredClone(coverage),pendingPolicy=structuredClone(policy);
 for(const r of pendingCoverage.representatives)r.status='candidate';
 for(const v of pendingPolicy.visualBindings)v.status='pending-independent-review';
 assert.throws(()=>regionalRows(f.pages,f.architecture,pendingCoverage,pendingPolicy),/approval/);
 assert.throws(()=>regionalMetadata(pendingCoverage,pendingPolicy,products,pendingCoverage.representatives[0].pageKey),/reviewed binding/);
});
test('complete membership yields exactly24 unique routes and each administrative multi-target edge',()=>{
 const f=fixture();const groups=directoryGroups(f.pages,f.architecture,f.c,f.p);
 assert.deepEqual(groups.map(d=>d.items.length),[9,7,8]);
 for(const a of f.c.administrativeCrosswalk){
  const wanted=a.relations.map(rel=>f.c.representatives.find(r=>r.unitKeys.includes(rel.unitKey)).url).sort();
  assert.deepEqual(aliasTargets(a.name,f.pages,f.architecture,f.c,f.p).sort(),[...new Set(wanted)].sort(),a.name);
 }
 assert.deepEqual(aliasTargets('역곡3동',f.pages,f.architecture,f.c,f.p),['/regions/sosa-goean/']);
 assert.deepEqual(aliasTargets('신흥동',f.pages,f.architecture,f.c,f.p).sort(),['/regions/ojeong-nae/','/regions/ojeong-samjeong/']);
});
test('unknown routes, duplicate units, unapproved scope and metadata drift fail closed',()=>{
 const f=fixture();assert.throws(()=>regionalRows(f.pages,f.architecture,f.c,{...f.p,enabled:false}),/disabled/);
 const c=structuredClone(f.c);c.representatives[1].unitKeys=c.representatives[0].unitKeys;assert.throws(()=>validateDefinition(c,f.p),/canonical unit/);
 for(const patch of [{scopeKey:'other'},{url:'/regions/unknown/'},{approvalVerified:false},{snapshotHash:''}])assert.throws(()=>regionalRows([{...f.pages[0],...patch}],f.architecture,f.c,f.p));
 const p=structuredClone(f.p);p.visualBindings[0].productKeys=['funeral-basic'];assert.throws(()=>assertRegionalMetadata(f.pages[0],f.c,p,products),/binding drift/);
});
test('regional product cards consume only the four reviewed product keys in the frozen purchase binding',()=>{
 const f=fixture(),page=f.pages[0];const selected=selectProducts(page,products,4);
 assert.deepEqual(selected.map(p=>p.key),['bouquet-happiness','basket-sunshine','funeral-basic','congrats-basic']);
 assert.ok(selected.every(p=>p.orderUrl==='https://fwith.co.kr/'));
});
