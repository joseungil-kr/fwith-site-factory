import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import pages from '../src/data/manual-pages.json' with {type:'json'};
import proof from '../src/data/manual-provenance.json' with {type:'json'};
import products from '../src/data/products.json' with {type:'json'};
import {validateManualContract,collectBindings,readReviewEvidence,digest,productionRequested,BINDING_KEYS,WRITER_ID,REVIEWER_ID,RELEASE_ID,EVIDENCE_PATH} from '../src/lib/manual-contract.mjs';
const clone=structuredClone,bytes=fs.readFileSync(new URL('../src/data/manual-pages.json',import.meta.url));
const actual=collectBindings('.');
// Synthetic approvals are test-only objects. Nothing writes approval to release provenance.
function fixture(){
 const evidence={status:'approved',manualReleaseId:RELEASE_ID,writerId:WRITER_ID,reviewerId:REVIEWER_ID,reviewedAt:'2026-10-07T00:00:00Z',...actual};
 const eb=Buffer.from(JSON.stringify(evidence));
 const p={...clone(proof),independentReview:{...evidence,evidencePath:EVIDENCE_PATH,evidenceSha256:digest(eb)}};
 return {p,eb,evidence};
}
const validate=(p=proof,opts={})=>validateManualContract(pages,p,bytes,products,{bindings:actual,...opts});
test('local candidate validates complete actual source bindings',()=>assert(validate()));
test('pending production fails',()=>assert.throws(()=>validate(proof,{production:true}),/pending/));
test('synthetic test-only complete evidence passes contract',()=>{const {p,eb}=fixture();assert(validate(p,{production:true,reviewEvidenceBytes:eb}));});
test('truthy missing evidence is insufficient',()=>{const {p}=fixture();assert.throws(()=>validate(p,{production:true}),/actual independent evidence bytes/);});
test('modified evidence bytes fail checksum',()=>{const {p,eb}=fixture();assert.throws(()=>validate(p,{production:true,reviewEvidenceBytes:Buffer.concat([eb,Buffer.from(' ')])}),/bytes\/hash/);});
for(const key of BINDING_KEYS)test('independent evidence binds exact '+key,()=>{const {p,evidence}=fixture();evidence[key]='wrong';const eb=Buffer.from(JSON.stringify(evidence));p.independentReview.evidenceSha256=digest(eb);assert.throws(()=>validate(p,{production:true,reviewEvidenceBytes:eb}),/Evidence does not bind/);});
for(const key of ['status','manualReleaseId','writerId','reviewerId','reviewedAt'])test('evidence cannot change '+key,()=>{const {p,evidence}=fixture();evidence[key]='wrong';const eb=Buffer.from(JSON.stringify(evidence));p.independentReview.evidenceSha256=digest(eb);assert.throws(()=>validate(p,{production:true,reviewEvidenceBytes:eb}),/identity\/status/);});
test('self review is rejected',()=>{const {p,eb}=fixture();p.independentReview.reviewerId=WRITER_ID;assert.throws(()=>validate(p,{production:true,reviewEvidenceBytes:eb}),/Unrecognized/);});
test('arbitrary independent reviewer is rejected',()=>{const {p,eb}=fixture();p.independentReview.reviewerId='other-reviewer';assert.throws(()=>validate(p,{production:true,reviewEvidenceBytes:eb}),/Unrecognized/);});
test('assigning another expected reviewer cannot bypass fixed identity',()=>{const {p}=fixture();p.expectedReviewerId='other-reviewer';assert.throws(()=>validate(p),/assigned reviewer/);});
for(const key of ['rendererHash','assetsHash','sourcesHash','frozenHash'])test('actual '+key+' drift fails in preview too',()=>assert.throws(()=>validate(proof,{bindings:{...actual,[key]:'changed'}}),/binding drift/));
test('changed catalog price is rejected',()=>{const p=clone(products);p[0].price+=1;assert.throws(()=>validateManualContract(pages,proof,bytes,p,{bindings:actual}),/catalog digest drift/);});
function mutate(fn){const p=clone(pages);fn(p);const b=Buffer.from(JSON.stringify(p));const bindings={...actual,contentHash:digest(b),sourcesHash:digest(JSON.stringify(p.map(p=>({pageKey:p.pageKey,sources:p.sources,source:p.source}))))};const v={...clone(proof),...bindings};return()=>validateManualContract(p,v,b,products,{bindings});}
test('fake historical snapshot is rejected',()=>assert.throws(mutate(p=>p[0].snapshotId='fake'),/Fabricated/));
test('wrong SKU is rejected',()=>assert.throws(mutate(p=>p[0].productKeys=['congrats-basic']),/SKU\/intent/));
test('changed raw bytes rejected',()=>assert.throws(()=>validateManualContract(pages,proof,Buffer.from('changed'),products,{bindings:actual}),/digest drift/));
test('all public origins including staging require approval',()=>{for(const origin of ['https://goyang.fwith.kr','https://goyang-flower-guide-qa.joseungil.workers.dev','https://other.example'])assert(productionRequested({SITE_URL:origin,SITE_INDEXABLE:'false',ALLOW_MANUAL_CANDIDATE:'1'},{previewUrl:origin}));});
test('only noindex loopback remains preview',()=>{assert.equal(productionRequested({SITE_URL:'http://127.0.0.1:8736',SITE_INDEXABLE:'false'},{}),false);assert(productionRequested({SITE_URL:'http://localhost:8736',SITE_INDEXABLE:'true'},{}));});
test('safe evidence reader rejects missing file and arbitrary path',()=>{const dir=fs.mkdtempSync(path.join(os.tmpdir(),'goyang-evidence-test-'));try{assert.throws(()=>readReviewEvidence(dir),/ENOENT/);assert.throws(()=>readReviewEvidence(dir,'../../elsewhere'),/Unexpected evidence path/);const f=path.join(dir,EVIDENCE_PATH);fs.mkdirSync(path.dirname(f),{recursive:true});fs.writeFileSync(f,'{"syntheticTestOnly":true}');assert.equal(readReviewEvidence(dir).toString(),'{"syntheticTestOnly":true}');}finally{fs.rmSync(dir,{recursive:true,force:true});}});

test('local preview requires exact false indexability',()=>{for(const value of [undefined,'','0','False','invalid'])assert(productionRequested({SITE_URL:'https://localhost:8736',SITE_INDEXABLE:value},{}));});
test('credentialed local URL is not preview',()=>assert(productionRequested({SITE_URL:'https://user:pass@localhost:8736',SITE_INDEXABLE:'false'},{})));
test('local path is not preview',()=>assert(productionRequested({SITE_URL:'https://localhost:8736/extra',SITE_INDEXABLE:'false'},{})));
test('local query is not preview',()=>assert(productionRequested({SITE_URL:'https://localhost:8736/?candidate=1',SITE_INDEXABLE:'false'},{})));
test('local fragment is not preview',()=>assert(productionRequested({SITE_URL:'https://localhost:8736/#candidate',SITE_INDEXABLE:'false'},{})));
test('all added runtime data files enter the frozen binding',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'goyang-binding-test-'));
 try{
  for(const name of ['src','scripts','public','astro.config.mjs','package.json','package-lock.json'])fs.cpSync(name,path.join(dir,name),{recursive:true});
  const before=collectBindings(dir);fs.writeFileSync(path.join(dir,'src/data/region-policy.json'),'{"syntheticTestOnly":true}');
  const policy=collectBindings(dir);assert.notEqual(policy.frozenHash,before.frozenHash);
  fs.writeFileSync(path.join(dir,'src/data/new-runtime-input.json'),'{"syntheticTestOnly":true}');assert.notEqual(collectBindings(dir).frozenHash,policy.frozenHash);
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
