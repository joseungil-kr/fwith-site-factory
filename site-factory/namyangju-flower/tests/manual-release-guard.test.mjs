import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {assertManualRelease,dependencyDigest,projectRoot,isPrivatePreview} from '../src/lib/manual-release-guard.mjs';
import {digest} from '../src/lib/manual-contract.mjs';
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'nyj-guard-tests-'));
for(const name of ['src','public','scripts','astro.config.mjs','package.json'])fs.cpSync(path.join(projectRoot,name),path.join(tmp,name),{recursive:true});
const proofFile=path.join(tmp,'src/data/manual-provenance.json');
const original=JSON.parse(fs.readFileSync(proofFile));
const publicEnv={SITE_URL:'https://namyangju.fwith.kr',SITE_INDEXABLE:'false',MANUAL_LOCAL_PREVIEW:'true'};
const localEnv={SITE_URL:'http://127.0.0.1:8877',SITE_INDEXABLE:'false',MANUAL_LOCAL_PREVIEW:'true'};
function save(proof){fs.writeFileSync(proofFile,JSON.stringify(proof));}
function approval(){const proof=structuredClone(original);const evidence={status:'approved',manualReleaseId:proof.manualReleaseId,writerId:proof.writerId,reviewerId:'independent-manual-review-20261007',reviewedAt:'2026-10-07',contentHash:proof.contentHash,dependencyHash:proof.dependencyHash};const bytes=Buffer.from(JSON.stringify(evidence));fs.writeFileSync(path.join(tmp,'src/data/manual-review-evidence.json'),bytes);proof.independentReview={...evidence,evidencePath:'src/data/manual-review-evidence.json',evidenceSha256:digest(bytes)};return proof;}
test('explicit loopback noindex candidate is allowed',()=>{save(original);assert(assertManualRelease(tmp,localEnv));});
test('public production remains blocked even noindex with preview flag',()=>{save(original);assert.throws(()=>assertManualRelease(tmp,publicEnv),/pending/);});
test('workers staging is also public and blocked',()=>{save(original);assert.throws(()=>assertManualRelease(tmp,{...publicEnv,SITE_URL:'https://namyangju-flower-guide-qa.joseungil.workers.dev'}),/pending/);});
test('loopback requires explicit local mode and nonindexability',()=>{assert(!isPrivatePreview({},'http://localhost:8'));assert(!isPrivatePreview({MANUAL_LOCAL_PREVIEW:'true',SITE_INDEXABLE:'true'},'http://localhost:8'));assert(!isPrivatePreview(localEnv,'http://127.0.0.1.evil.example'));});
test('synthetic test-only exact evidence bytes bind a release',()=>{save(approval());assert(assertManualRelease(tmp,publicEnv));});
test('nonexistent evidence file is rejected',()=>{save(approval());fs.unlinkSync(path.join(tmp,'src/data/manual-review-evidence.json'));assert.throws(()=>assertManualRelease(tmp,publicEnv),/does not exist/);});
test('unexpected evidence path is rejected',()=>{const p=approval();p.independentReview.evidencePath='does-not-exist.json';save(p);assert.throws(()=>assertManualRelease(tmp,publicEnv),/Unexpected evidence/);});
test('unrecognized reviewer cannot authorize release',()=>{const p=approval();p.independentReview.reviewerId='unassigned-reviewer';save(p);assert.throws(()=>assertManualRelease(tmp,publicEnv),/Unrecognized/);});
test('evidence bytes tampering is rejected',()=>{save(approval());fs.appendFileSync(path.join(tmp,'src/data/manual-review-evidence.json'),' ');assert.throws(()=>assertManualRelease(tmp,publicEnv),/file digest mismatch/);});
test('catalog source renderer and asset drift are rejected',()=>{for(const rel of ['src/data/products.json','src/data/manual-pages.json','src/pages/index.astro','public/images/products/funeral-basic.webp']){save(approval());const f=path.join(tmp,rel),b=fs.readFileSync(f);fs.appendFileSync(f,' ');assert.throws(()=>assertManualRelease(tmp,publicEnv),/digest drift/);fs.writeFileSync(f,b);}});
test('evidence release and dependency binding cannot be substituted',()=>{for(const field of ['manualReleaseId','dependencyHash','contentHash','writerId']){const p=approval(),file=path.join(tmp,'src/data/manual-review-evidence.json'),e=JSON.parse(fs.readFileSync(file));e[field]='substituted';const b=Buffer.from(JSON.stringify(e));fs.writeFileSync(file,b);p.independentReview.evidenceSha256=digest(b);save(p);assert.throws(()=>assertManualRelease(tmp,publicEnv));}});
test.after(()=>fs.rmSync(tmp,{recursive:true,force:true}));

test('local candidate requires exact false indexability',()=>{for(const value of [undefined,'','False','0','invalid']){const env={...localEnv,SITE_INDEXABLE:value};assert(!isPrivatePreview(env,'https://localhost:8877'));save(original);assert.throws(()=>assertManualRelease(tmp,env),/pending/);}});
test('loopback must be a clean canonical origin',()=>{for(const origin of ['https://localhost:8877/','https://localhost:8877/path','https://localhost:8877/?x=1','https://localhost:8877/#part','https://user@localhost:8877','https://127.1','https://LOCALHOST:8877','https://localhost:8877/a/..'])assert(!isPrivatePreview(localEnv,origin),origin);});
test('fixed writer identity cannot be substituted',()=>{const p=structuredClone(original);p.writerId='another-writer';save(p);assert.throws(()=>assertManualRelease(tmp,localEnv),/Unexpected writer identity/);});
