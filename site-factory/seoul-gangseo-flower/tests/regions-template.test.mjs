import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {coverage,policy,architecture,regionalPages,groupsFor,assertRegionalInput,isUnboundTemplate} from '../src/lib/regional-runtime.mjs';
import {validateDefinition,regionalMetadata} from '../src/lib/regions.mjs';
import {validateHubMetadata} from '../scripts/qa_graph.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const c={schemaVersion:2,siteKey:'template-only',scopeKey:'',unitBasis:'legal-dong-plus-eup-myeon',countIsPageQuota:false,verifiedAt:'',sourceBasisDate:'',officialSourceUrls:[],membershipSourceSha256:'',districts:[],units:[],administrativeCrosswalk:[],representatives:[]};
const p={schemaVersion:1,siteKey:'template-only',scopeKey:'',enabled:false,officialHosts:[],unitTypes:[],rulesRevision:'',definitionFile:'src/data/region-coverage.json',state:'unbound-template',membershipSourceSha256:'',visualBindings:[]};
const a={siteKey:'template-only',pages:[]},m={siteKey:'template-only',pages:[],snapshotLedger:{}};
test('stored hub policy matches runtime thresholds, including empty and paused previews',()=>{
 for(const count of [0,1,2,3,4,5,53]){
  const pages=Array.from({length:count},()=>({category:'regions'}));
  const hub={category:'regions',url:'/regions/',children:count,indexable:count>=3,menuVisible:count>=5};
  assert.doesNotThrow(()=>validateHubMetadata(pages,{hubs:[hub]}));
  for(const field of ['indexable','menuVisible'])assert.throws(()=>validateHubMetadata(pages,{hubs:[{...hub,[field]:!hub[field]}]}),/Stale hub index\/menu policy/);
  assert.throws(()=>validateHubMetadata(pages,{hubs:[{...hub,children:count+1}]}),/Stale hub child count/);
 }
});
test('actual runtime input matches its frozen manifest without template-only assumptions',()=>{
 const pages=read('pages');
 assert.deepEqual(assertRegionalInput(pages),regionalPages);
 assert.equal(Array.isArray(groupsFor(pages)),true);
});
test('unbound template has no customers, geography, snapshots or approvals',()=>{
 if(coverage.siteKey!=='template-only'){assert.equal(isUnboundTemplate(coverage,policy,architecture,read('publish-manifest')),false);return;}
 const manifest=read('publish-manifest');
 assert.equal(isUnboundTemplate(coverage,policy,architecture,manifest),true);
 assert.deepEqual(read('pages'),[]);assert.deepEqual(manifest.snapshotLedger,{});
 for(const field of ['districts','units','administrativeCrosswalk','representatives'])assert.deepEqual(coverage[field],[]);
 assert.equal(policy.enabled,false);assert.deepEqual(policy.visualBindings,[]);
 assert.deepEqual(regionalPages,[]);assert.deepEqual(groupsFor([]),[]);assert.deepEqual(assertRegionalInput([]),[]);
 assert.deepEqual(architecture.hubs.map(h=>h.category),['funeral','business','school','event','gift','order','regions']);
 assert.ok(architecture.hubs.every(h=>h.children===0&&!h.indexable&&!h.menuVisible));
});
test('unbound sentinel is exact and cannot silently accept claims or content',()=>{
 for(const [kind,field,value] of [['c','scopeKey','scope'],['c','verifiedAt','2026-01-01'],['c','extra',true],['p','enabled',true],['p','visualBindings',[{}]],['p','state','approved']]){
  const cc=structuredClone(c),pp=structuredClone(p);(kind==='c'?cc:pp)[field]=value;
  assert.throws(()=>isUnboundTemplate(cc,pp,a,m),/Invalid unbound/);
 }
 assert.equal(isUnboundTemplate(c,p,a,m),true);
 assert.throws(()=>isUnboundTemplate(c,p,{...a,pages:[{}]},m),/Invalid unbound/);
 assert.throws(()=>isUnboundTemplate(c,p,a,{...m,pages:[{}]}),/Invalid unbound/);
 assert.throws(()=>validateDefinition(c,p),/opt-in mismatch/);
 assert.throws(()=>regionalMetadata(c,p,read('products'),'missing'),/reviewed binding/);
 if(coverage.siteKey==='template-only'){assert.throws(()=>groupsFor([{}]),/customer pages/);assert.throws(()=>assertRegionalInput([{}]),/customer pages/);}
});
