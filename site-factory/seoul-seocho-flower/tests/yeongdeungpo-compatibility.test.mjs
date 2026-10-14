/** Compare unchanged Yeongdeungpo fixtures through the original and current shared runtime. */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import * as current from '../src/lib/regions.mjs';
import * as original from './reference/yeongdeungpo-runtime/src/lib/regions.mjs';
import * as currentLinks from '../src/lib/directory-links.mjs';
import * as originalLinks from './reference/yeongdeungpo-runtime/src/lib/directory-links.mjs';

const fixtureUrl=new URL('./reference/yeongdeungpo-runtime/',import.meta.url);
const read=name=>JSON.parse(fs.readFileSync(new URL('src/data/'+name+'.json',fixtureUrl),'utf8'));
const clone=structuredClone;
const coverage=read('region-coverage'),policy=read('region-policy'),pages=read('pages'),architecture=read('architecture'),products=read('products');
const fixture=()=>({coverage:clone(coverage),policy:clone(policy),pages:clone(pages),architecture:clone(architecture),products:clone(products)});
const compare=invoke=>assert.deepEqual(invoke(current,fixture()),invoke(original,fixture()));
function rejectsBoth(label,mutate,invoke) {
 for(const [name,runtime] of [['original',original],['current',current]]){
  const input=fixture();mutate(input);
  assert.throws(()=>invoke(runtime,input),undefined,name+': '+label);
 }
}
const groupsFor=(runtime,input)=>runtime.directoryGroups(input.pages,input.architecture,input.coverage,input.policy);
const sourceDigest=runtime=>crypto.createHash('sha256').update(fs.readFileSync(runtime)).digest('hex');

test('Yeongdeungpo unchanged original adapter and fixed N2 data pass both dispatchers',()=>{
 assert.equal(sourceDigest(new URL('../src/lib/yeongdeungpo-regions.mjs',import.meta.url)),sourceDigest(new URL('src/lib/yeongdeungpo-regions.mjs',fixtureUrl)));
 assert.deepEqual(current.regionalMetadataFields,original.regionalMetadataFields);
 compare((runtime,input)=>runtime.validateDefinition(input.coverage,input.policy));
 compare((runtime,input)=>runtime.regionalRows(input.pages,input.architecture,input.coverage,input.policy));
 assert.equal(current.regionalRows(pages,architecture,coverage,policy).length,2);
});

test('Yeongdeungpo exact catalog metadata and record assertions retain original results',()=>{
 for(const page of pages){
  compare((runtime,input)=>runtime.regionalMetadata(input.coverage,input.policy,input.products,page.pageKey));
  compare((runtime,input)=>runtime.assertRegionalMetadata(input.pages.find(row=>row.pageKey===page.pageKey),input.coverage,input.policy,input.products));
  for(const runtime of [original,current])assert.doesNotThrow(()=>runtime.validateRegionalPurchase(clone(page),clone(products),page.contentMarkdown));
 }
});

test('Yeongdeungpo directory groups and all legal/admin/facility aliases remain equivalent',()=>{
 compare(groupsFor);
 const names=new Set([...coverage.units.flatMap(unit=>[unit.name,...unit.legalRi]),...coverage.administrativeCrosswalk.map(alias=>alias.name),...coverage.facilities.map(facility=>facility.name),'여의동','신길제1동','신길제5동','대림제1동','대림제2동','대림제3동','관악구','unknown']);
 for(const name of names)compare((runtime,input)=>runtime.aliasTargets(name,input.pages,input.architecture,input.coverage,input.policy));
 assert.deepEqual(current.aliasTargets('여의동',pages,architecture,coverage,policy),['/regions/yeongdeungpo-funeral-wreath/#yeouido-stmary','/regions/yeongdeungpo-wedding-wreath/#partyum']);
 for(const name of ['신길제1동','신길제5동','대림제1동','대림제2동','대림제3동'])assert.deepEqual(current.aliasTargets(name,pages,architecture,coverage,policy),[]);
});

test('Yeongdeungpo eight facility destinations and six legal unit entries match original helper output',()=>{
 const currentGroups=groupsFor(current,fixture()),originalGroups=groupsFor(original,fixture());
 const currentDestinations=currentLinks.publishedDestinationsByUnit(currentGroups),originalDestinations=originalLinks.publishedDestinationsByUnit(originalGroups);
 assert.deepEqual(currentDestinations,originalDestinations);
 assert.deepEqual(currentLinks.publishedEntriesByUnit(currentGroups),originalLinks.publishedEntriesByUnit(originalGroups));
 assert.equal(currentDestinations.size,6);
 const destinations=[...currentDestinations.values()].flat();assert.equal(destinations.length,8);
 assert.deepEqual(new Set(destinations.map(destination=>destination.candidateId)),new Set(coverage.facilities.map(facility=>facility.facilityKey)));
 for(const facility of coverage.facilities)assert.equal(currentDestinations.get(facility.unitKey).filter(destination=>destination.candidateId===facility.facilityKey).length,1);
 assert.equal(currentDestinations.get('영등포구/법정동/여의도동').length,2);
 assert.equal(currentDestinations.get('영등포구/법정동/영등포동7가').length,2);
 assert.equal(currentDestinations.get('영등포구/법정동/신길동'),undefined);
 assert.deepEqual(currentLinks.publishedUnassignedDistrictDestinations(currentGroups),new Map());
});

test('Yeongdeungpo representative membership and frozen geography mutations reject in both dispatchers',()=>{
 const changes=[
  ['N0',value=>value.coverage.representatives=[]],
  ['N1',value=>value.coverage.representatives.pop()],
  ['duplicate representative',value=>value.coverage.representatives.push(clone(value.coverage.representatives[0]))],
  ['unknown candidate',value=>value.coverage.representatives[0].candidateIds[0]='unknown'],
  ['duplicate candidate',value=>value.coverage.representatives[0].candidateIds.push(value.coverage.representatives[0].candidateIds[0])],
  ['held candidate',value=>value.coverage.representatives[0].candidateIds.push('bokji')],
  ['removed anchor',value=>value.coverage.representatives[0].facilityAnchors.pop()],
  ['changed anchor',value=>value.coverage.representatives[0].facilityAnchors[0].anchor='wrong'],
  ['null geography',value=>value.coverage.representatives[0].facilityAnchors[0].unitKey=null],
  ['changed unit union',value=>value.coverage.representatives[0].unitKeys.reverse()],
  ['wrong intent',value=>value.coverage.representatives[0].purchaseIntentKey='opening-congrats-wreath'],
  ['wrong context',value=>value.coverage.representatives[0].contextKey='wrong'],
  ['wrong URL',value=>value.coverage.representatives[0].url='/regions/wrong/'],
  ['invalid representative status',value=>value.coverage.representatives[0].status='invalid'],
  ['empty keyword',value=>value.coverage.representatives[0].primaryKeyword=''],
  ['removed facility',value=>value.coverage.facilities.pop()],
  ['null facility unit',value=>value.coverage.facilities[0].unitKey=null],
  ['changed membership',value=>value.coverage.administrativeCrosswalk[0].relations.pop()],
  ['wrong membership hash',value=>value.coverage.membershipSourceSha256='0'.repeat(64)],
  ['wrong policy scope',value=>value.policy.scopeKey='wrong'],
  ['Gwanak cross-site opt-in',value=>value.policy.siteKey='seoul-gwanak-flower-direct'],
 ];
 for(const [label,change] of changes)rejectsBoth(label,change,(runtime,input)=>runtime.validateDefinition(input.coverage,input.policy));
});

test('Yeongdeungpo approved rows and architecture context mutations reject in both dispatchers',()=>{
 const changes=[
  ['missing article',value=>value.pages.pop()],
  ['duplicate article',value=>value.pages=[value.pages[0],clone(value.pages[0])]],
  ['unapproved article',value=>value.pages[0].approvalVerified=false],
  ['unapproved coverage representative',value=>value.coverage.representatives[0].status='candidate'],
  ['coverage keyword mismatches page',value=>value.coverage.representatives[0].primaryKeyword='wrong'],
  ['candidate article',value=>value.pages[0].status='candidate'],
  ['wrong URL',value=>value.pages[0].url='/regions/wrong/'],
  ['wrong scope',value=>value.pages[0].scopeKey='wrong'],
  ['wrong candidate members',value=>value.pages[0].candidateIds=['wrong']],
  ['wrong physical anchor',value=>value.pages[0].facilityAnchors[0].anchor='wrong'],
  ['wrong regional unit',value=>value.pages[0].regionUnitKeys=['wrong']],
  ['wrong purchase intent',value=>value.pages[0].purchaseIntentKey='opening-congrats-wreath'],
  ['wrong keyword',value=>value.pages[0].primaryKeyword='wrong'],
  ['missing architecture node',value=>value.architecture.pages.pop()],
  ['duplicate architecture node',value=>value.architecture.pages.push(clone(value.architecture.pages[0]))],
  ['wrong architecture hub',value=>value.architecture.pages[0].parentHub='/'],
  ['wrong architecture scope',value=>value.architecture.pages[0].scopeKey='wrong'],
  ['wrong architecture intent',value=>value.architecture.pages[0].intentKey='wrong'],
  ['wrong architecture context',value=>value.architecture.pages[0].contextKey='wrong'],
 ];
 for(const [label,change] of changes)rejectsBoth(label,change,(runtime,input)=>runtime.regionalRows(input.pages,input.architecture,input.coverage,input.policy));
});

test('Yeongdeungpo all inherited metadata fields and grouped fields reject record drift equally',()=>{
 const fields=[...current.regionalMetadataFields,'candidateIds','purchaseIntentKey','contextKey','intentKey','facilityAnchors'];
 for(const field of fields)rejectsBoth('removed '+field,input=>delete input.pages[0][field],(runtime,input)=>runtime.assertRegionalMetadata(input.pages[0],input.coverage,input.policy,input.products));
 for(const field of ['primaryKeyword','facilityKey','unitKey'])rejectsBoth('forged '+field,input=>input.pages[0][field]='wrong',(runtime,input)=>runtime.assertRegionalMetadata(input.pages[0],input.coverage,input.policy,input.products));
});

test('Yeongdeungpo invalid helper anchors retain original rejection including null units',()=>{
 const changes=[
  ['non-array anchors',groups=>groups[0].items[0].representative.facilityAnchors={}],
  ['null unit',groups=>groups[0].items[0].representative.facilityAnchors[0].unitKey=null],
  ['unknown unit',groups=>groups[0].items[0].representative.facilityAnchors[0].unitKey='wrong'],
  ['empty href',groups=>groups[0].items[0].representative.facilityAnchors[0].href=''],
  ['empty heading',groups=>groups[0].items[0].representative.facilityAnchors[0].heading=''],
 ];
 for(const [label,change] of changes)for(const [name,runtime,links] of [['original',original,originalLinks],['current',current,currentLinks]]){const groups=groupsFor(runtime,fixture());change(groups);assert.throws(()=>links.publishedDestinationsByUnit(groups),undefined,name+': '+label);}
});
