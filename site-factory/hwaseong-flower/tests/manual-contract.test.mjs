import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {spawnSync} from 'node:child_process';import os from 'node:os';import path from 'node:path';
import {validateManualContract as coreValidate,digest,releaseDigest} from '../src/lib/manual-contract.mjs';
const manifest=JSON.parse(fs.readFileSync('src/data/manual-manifest.json'));const proof=JSON.parse(fs.readFileSync('src/data/manual-provenance.json'));const observed={...proof.bindings};
const evidence={status:'approved',fullBodiesRead:true,contentQa:'PASS',codeQa:'PASS',catalogAndAssetsQa:'PASS',visualQa:'PASS',ruleRevision:proof.ruleRevision,ruleHashes:proof.ruleHashes,reviewedAt:'2026-10-07T10:00:00.000Z',pages:manifest.pages.map(p=>({pageKey:p.pageKey,decision:'PASS',fullBodyRead:true,contentSha256:proof.bindings[p.file],metadataSha256:digest(JSON.stringify(p))})),releaseHash:proof.releaseHash,writerId:proof.writerId,reviewerId:proof.expectedReviewerId,manualReleaseId:proof.manualReleaseId};
const validateManualContract=(m,p,o,opt={})=>coreValidate(m,p,o,{inventory:Object.keys(o),...opt});
const pending=()=>({...structuredClone(proof),independentReview:{status:'pending'}});
// Exercise actual entrypoints in disposable copies; never revoke the reviewed source's proof.
function runPendingFixture(command,args,env,timeout=60000){
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'hwaseong-pending-'));
 try{
  for(const file of Object.keys(proof.bindings)){const target=path.join(root,file);fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(file,target);}
  fs.writeFileSync(path.join(root,'src/data/manual-provenance.json'),JSON.stringify(pending()));
  fs.symlinkSync(path.resolve('node_modules'),path.join(root,'node_modules'),'dir');
  return spawnSync(command,args,{cwd:root,env:{...process.env,...env,ASTRO_TELEMETRY_DISABLED:'1',XDG_CONFIG_HOME:path.join(root,'.config')},encoding:'utf8',timeout});
 }finally{fs.rmSync(root,{recursive:true,force:true});}
}
const approved=()=>({...structuredClone(proof),independentReview:{status:'approved',reviewerId:proof.expectedReviewerId,reviewedAt:evidence.reviewedAt,evidencePath:'test-only',releaseHash:proof.releaseHash,evidenceHash:digest(JSON.stringify(evidence))}});
test('pending candidate permits only nonindex preview',()=>assert(validateManualContract(manifest,pending(),observed,{preview:true})));
test('indexable preview rejects',()=>assert.throws(()=>validateManualContract(manifest,proof,observed,{preview:true,indexable:true}),/cannot be indexable/));
test('pending production rejects',()=>assert.throws(()=>validateManualContract(manifest,pending(),observed),/review pending/));
test('genuine bound evidence fixture passes contract',()=>assert(validateManualContract(manifest,approved(),observed,{evidence})));
test('tampered source rejects',()=>{const o={...observed};o[Object.keys(o)[0]]='bad';assert.throws(()=>validateManualContract(manifest,approved(),o,{evidence}),/hash drift/)});
test('missing hash rejects',()=>{const p=approved();p.bindings=null;assert.throws(()=>validateManualContract(manifest,p,observed,{evidence}),/Missing file hashes/)});
test('invalid hash rejects',()=>{const p=approved();p.bindings[Object.keys(p.bindings)[0]]='invalid';p.releaseHash=releaseDigest(p.bindings);assert.throws(()=>validateManualContract(manifest,p,observed,{evidence}),/Invalid file hash/)});
test('same writer reviewer rejects',()=>{const p=approved();p.independentReview.reviewerId=p.writerId;assert.throws(()=>validateManualContract(manifest,p,observed,{evidence}),/cannot approve/)});
test('missing evidence rejects',()=>assert.throws(()=>validateManualContract(manifest,approved(),observed),/Missing independent evidence/));
test('stale evidence rejects',()=>assert.throws(()=>validateManualContract(manifest,approved(),observed,{evidence:{...evidence,releaseHash:'stale'}}),/Evidence mismatch/));
test('wrong release evidence rejects',()=>assert.throws(()=>validateManualContract(manifest,approved(),observed,{evidence:{...evidence,manualReleaseId:'wrong'}}),/Evidence mismatch/));
test('frozen provenance on manual page rejects',()=>{const m=structuredClone(manifest);m.pages[0].snapshotId='fake';assert.throws(()=>validateManualContract(m,proof,observed,{preview:true}),/Fabricated frozen/)});
test('actual script rejects indexable preview env combination',()=>{const r=runPendingFixture(process.execPath,['scripts/validate_manual.mjs'],{MANUAL_PREVIEW:'true',SITE_INDEXABLE:'true'});assert.notEqual(r.status,0);assert.match(r.stderr,/cannot be indexable/)});
test('actual script rejects production with pending review regardless legacy flags',()=>{const r=runPendingFixture(process.execPath,['scripts/validate_manual.mjs'],{MANUAL_PREVIEW:'false',SITE_INDEXABLE:'true',ALLOW_MANUAL_CANDIDATE:'1',MANUAL_CANDIDATE_BUILD:'1'});assert.notEqual(r.status,0);assert.match(r.stderr,/review pending/)});
test('rendered manual pages match requested indexing, manual ID only',()=>{for(const p of manifest.pages){const h=fs.readFileSync('dist'+p.url+'index.html','utf8');const indexable=process.env.SITE_INDEXABLE==='true';assert.match(h,indexable?/<meta[^>]*name="robots"[^>]*content="index,follow/:/<meta[^>]*name="robots"[^>]*content="noindex/);assert.match(h,/data-manual-publication-id="mp-[a-f0-9]{20}"/);assert(!h.includes('data-snapshot-id='));}});
test('direct Astro invocation cannot bypass independent production gate',()=>{const r=runPendingFixture(path.resolve('node_modules/.bin/astro'),['build'],{MANUAL_PREVIEW:'false',SITE_INDEXABLE:'true'});assert.notEqual(r.status,0);assert.match(r.stderr+r.stdout,/Independent review pending/)});

for(const field of ['contentQa','codeQa','catalogAndAssetsQa','visualQa'])test('reject incomplete '+field,()=>assert.throws(()=>validateManualContract(manifest,approved(),observed,{evidence:{...evidence,[field]:'UNVERIFIED'}}),/QA incomplete/));
test('fullBodiesRead false fails',()=>assert.throws(()=>validateManualContract(manifest,approved(),observed,{evidence:{...evidence,fullBodiesRead:false}}),/Full bodies/));
test('invalid timestamp fails',()=>{let p=approved();p.independentReview.reviewedAt='invalid';assert.throws(()=>validateManualContract(manifest,p,observed,{evidence}),/Invalid review date/)});
test('per-page content REVISE fails despite aggregate PASS',()=>{let e=structuredClone(evidence);e.pages[0].decision='REVISE';assert.throws(()=>validateManualContract(manifest,approved(),observed,{evidence:e}),/Page not approved/)});
test('stale rules fail',()=>assert.throws(()=>validateManualContract(manifest,approved(),observed,{evidence:{...evidence,ruleRevision:'wrong'}}),/rule revision/));
test('missing per-page decision fails',()=>assert.throws(()=>validateManualContract(manifest,approved(),observed,{evidence:{...evidence,pages:[]}}),/Per-page inventory/));
for(const file of ['src/content/manual-articles/unbound-test.md','src/lib/unbound-runtime-test.mjs'])test('actual boundary catches added '+file,()=>{try{fs.writeFileSync(file,'unbound test fixture');let r=spawnSync(process.execPath,['scripts/validate_manual.mjs'],{env:{...process.env,MANUAL_PREVIEW:'true',SITE_INDEXABLE:'false'},encoding:'utf8'});assert.notEqual(r.status,0);assert.match(r.stderr,/Unbound or missing runtime/)}finally{fs.unlinkSync(file)}});
test('invalid rule content digest fails even with bound revision label',()=>{const p=approved();p.ruleHashes[Object.keys(p.ruleHashes)[0]]='0'.repeat(64);assert.throws(()=>validateManualContract(manifest,p,observed,{evidence}),/Pinned rule hash|Rule file/)});
test('per-page metadata hash drift fails',()=>{const e=structuredClone(evidence);e.pages[0].metadataSha256='0'.repeat(64);assert.throws(()=>validateManualContract(manifest,approved(),observed,{evidence:e}),/Page metadata/)});
test('invalid calendar date rejects',()=>{const p=approved();p.independentReview.reviewedAt='2026-02-30T10:00:00.000Z';assert.throws(()=>validateManualContract(manifest,p,observed,{evidence}),/Invalid review date/)});
