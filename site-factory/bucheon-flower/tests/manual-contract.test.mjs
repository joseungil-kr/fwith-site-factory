import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {spawnSync} from 'node:child_process';
import pages from '../src/data/manual-pages.json' with {type:'json'};import proof from '../src/data/manual-provenance.json' with {type:'json'};import products from '../src/data/products.json' with {type:'json'};
import {validateManualContract,digest,WRITER_ID,REVIEWER_ID} from '../src/lib/manual-contract.mjs';import {isLocalPreview} from '../src/lib/manual-boundary.mjs';
import {dependencyDigest,readReviewEvidence,ROOT_INPUTS} from '../src/lib/manual-release-guard.mjs';
const bytes=fs.readFileSync(new URL('../src/data/manual-pages.json',import.meta.url));const catalogBytes=fs.readFileSync(new URL('../src/data/products.json',import.meta.url));
function approved(data=pages,body=bytes){
 const p=structuredClone(proof);p.contentHash=digest(body);
 const evidence={status:'approved',reviewedAt:'2026-10-07',dependencyHash:p.dependencyHash,contentHash:p.contentHash,catalogHash:p.catalogHash,writerId:WRITER_ID,reviewerId:REVIEWER_ID,manualReleaseId:p.manualReleaseId};
 const evidenceBytes=Buffer.from(JSON.stringify(evidence));
 p.independentReview={status:'approved',dependencyHash:p.dependencyHash,contentHash:p.contentHash,catalogHash:p.catalogHash,reviewerId:REVIEWER_ID,reviewedAt:'2026-10-07',evidencePath:'src/data/manual-review-evidence.json',evidenceSha256:digest(evidenceBytes)};
 return {data,p,body,options:{requireApproval:true,catalogBytes,dependencyHash:p.dependencyHash,reviewEvidence:evidence,reviewEvidenceBytes:evidenceBytes}};
}
function pending(){const p=structuredClone(proof);p.independentReview={status:'pending'};return p;}
const run=x=>validateManualContract(x.data,x.p,x.body,products,x.options);
function mutation(fn){const data=structuredClone(pages);fn(data);return approved(data,Buffer.from(JSON.stringify(data)));}
test('candidate contract content checks pass without claiming approval',()=>assert(validateManualContract(pages,proof,bytes,products,{catalogBytes,dependencyHash:proof.dependencyHash})));
test('pending manual review blocks production',()=>assert.throws(()=>validateManualContract(pages,pending(),bytes,products,{requireApproval:true,catalogBytes,dependencyHash:proof.dependencyHash}),/review pending/));
test('exact independent evidence permits production contract only in a fixture',()=>assert(run(approved())));
test('content drift blocks even an approved review',()=>{const x=approved();x.body=Buffer.from('changed');assert.throws(()=>run(x),/digest drift/);});
test('review digest mismatch fails closed',()=>{const x=approved();x.p.independentReview.contentHash='stale';assert.throws(()=>run(x),/bind current/);});
test('writer cannot act as own reviewer',()=>{const x=approved();x.p.independentReview.reviewerId=WRITER_ID;assert.throws(()=>run(x),/cannot approve/);});
test('fabricated frozen provenance is rejected',()=>assert.throws(()=>run(mutation(p=>p[0].snapshotId='fake')),/Fabricated/));
test('wrong SKU and intent is rejected',()=>assert.throws(()=>run(mutation(p=>p[0].productKeys=['congrats-basic'])),/SKU\/intent/));
test('venue with wrong flower intent is rejected',()=>assert.throws(()=>run(mutation(p=>{const r=p.find(x=>x.pageType==='event-venue');r.visualIntent='performance_venue';r.productKeys=['bouquet-happiness','bouquet-blue'];}))));
test('missing evidence document cannot authorize production',()=>{const x=approved();x.options.reviewEvidence=null;assert.throws(()=>run(x),/evidence document/);});
test('evidence content digest must match exact candidate',()=>{const x=approved();x.options.reviewEvidence.contentHash='stale';x.options.reviewEvidenceBytes=Buffer.from(JSON.stringify(x.options.reviewEvidence));x.p.independentReview.evidenceSha256=digest(x.options.reviewEvidenceBytes);assert.throws(()=>run(x),/Evidence digest/);});
test('unrecognized reviewer identity cannot authorize production',()=>{const x=approved();x.p.independentReview.reviewerId='unrelated';assert.throws(()=>run(x),/Unexpected independent/);});
test('assigned reviewer cannot be rewritten together with claimed reviewer',()=>{const x=approved();x.p.expectedReviewerId=x.p.independentReview.reviewerId='other';assert.throws(()=>run(x),/Assigned reviewer/);});
test('fixed writer identity cannot be rewritten',()=>{const x=approved();x.p.writerId='other';assert.throws(()=>run(x),/Unexpected writer/);});
test('actual evidence bytes hash mismatch is rejected',()=>{const x=approved();x.options.reviewEvidenceBytes=Buffer.concat([x.options.reviewEvidenceBytes,Buffer.from(' ')]);assert.throws(()=>run(x),/bytes digest/);});
test('evidence object cannot differ from file bytes',()=>{const x=approved();x.options.reviewEvidence.status='pending';assert.throws(()=>run(x),/actual bytes/);});
test('catalog byte changes invalidate candidate contract',()=>{const x=approved();x.options.catalogBytes=Buffer.concat([catalogBytes,Buffer.from(' ')]);assert.throws(()=>run(x),/Catalog digest/);});
test('review must bind the same catalog',()=>{const x=approved();x.p.independentReview.catalogHash='stale';assert.throws(()=>run(x),/Review catalog/);});
test('candidate environment flags never substitute for approval',()=>{process.env.ALLOW_MANUAL_CANDIDATE='1';process.env.MANUAL_CANDIDATE_BUILD='1';try{assert.throws(()=>validateManualContract(pages,pending(),bytes,products,{requireApproval:true,catalogBytes,dependencyHash:proof.dependencyHash}),/review pending/);}finally{delete process.env.ALLOW_MANUAL_CANDIDATE;delete process.env.MANUAL_CANDIDATE_BUILD;}});
for(const url of ['http://127.0.0.1:8871','http://localhost:8871/','http://[::1]:8871/'])test('explicit false clean loopback accepted: '+url,()=>assert(isLocalPreview({SITE_URL:url,SITE_INDEXABLE:'false'})));
for(const env of [{SITE_URL:'https://bucheon.fwith.kr',SITE_INDEXABLE:'false'},{SITE_URL:'https://unknown.example',SITE_INDEXABLE:'false'},{SITE_URL:'http://localhost:8871'}, {SITE_INDEXABLE:'false'}, {SITE_URL:'http://localhost:8871',SITE_INDEXABLE:'true'},{SITE_URL:'http://u:p@localhost:8871',SITE_INDEXABLE:'false'},{SITE_URL:'http://localhost:8871/path',SITE_INDEXABLE:'false'},{SITE_URL:'http://localhost:8871/?x=1',SITE_INDEXABLE:'false'},{SITE_URL:'http://localhost:8871/#x',SITE_INDEXABLE:'false'},{SITE_URL:'http://localhost.attacker.example',SITE_INDEXABLE:'false'}])test('not a pending local preview: '+JSON.stringify(env),()=>assert.equal(isLocalPreview(env),false));
function boundaryFixture({productionApproved=true,env={},approvedReview=false,entry='script',mutate=null}={}){
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'bucheon-boundary-test-'));
 for(const name of ['src','public','scripts','tests',...ROOT_INPUTS]){
  const src=new URL('../'+name,import.meta.url);fs.cpSync(src,path.join(root,name),{recursive:true,filter:(p)=>!p.includes('__pycache__')});
 }
 const config=JSON.parse(fs.readFileSync(path.join(root,'src/data/site-config.json')));config.productionApproved=productionApproved;fs.writeFileSync(path.join(root,'src/data/site-config.json'),JSON.stringify(config));
 const fixture=approved();fixture.p.dependencyHash=dependencyDigest(root);fixture.p.independentReview.dependencyHash=fixture.p.dependencyHash;fixture.options.reviewEvidence.dependencyHash=fixture.p.dependencyHash;fixture.options.reviewEvidenceBytes=Buffer.from(JSON.stringify(fixture.options.reviewEvidence));fixture.p.independentReview.evidenceSha256=digest(fixture.options.reviewEvidenceBytes);const pendingProof={...pending(),dependencyHash:fixture.p.dependencyHash};fs.writeFileSync(path.join(root,'src/data/manual-provenance.json'),JSON.stringify(approvedReview?fixture.p:pendingProof));
 if(approvedReview)fs.writeFileSync(path.join(root,'src/data/manual-review-evidence.json'),fixture.options.reviewEvidenceBytes);
 if(mutate)mutate(root);
 if(entry==='astro')fs.symlinkSync(fs.realpathSync(new URL('../node_modules',import.meta.url)),path.join(root,'node_modules'),'dir');
 const environment={...process.env};delete environment.SITE_URL;delete environment.SITE_INDEXABLE;
 const result=spawnSync(process.execPath,entry==='astro'?['--input-type=module','-e',"await import('./astro.config.mjs')"]:['scripts/assert_preview_boundary.mjs'],{cwd:root,env:{...environment,MANUAL_CANDIDATE_BUILD:'1',ALLOW_MANUAL_CANDIDATE:'1',...env},encoding:'utf8'});fs.rmSync(root,{recursive:true,force:true});return result;
}
test('actual boundary rejects both candidate flags on indexable production',()=>{const r=boundaryFixture({env:{SITE_INDEXABLE:'true',SITE_URL:'https://bucheon.fwith.kr'}});assert.notEqual(r.status,0);assert.match(r.stderr,/review pending/);});
test('original productionApproved false remains a hard block',()=>{const r=boundaryFixture({productionApproved:false,approvedReview:true,env:{SITE_INDEXABLE:'false',SITE_URL:'https://bucheon.fwith.kr'}});assert.notEqual(r.status,0);assert.match(r.stderr,/unapproved regional template/);});
test('actual boundary blocks public noindex with pending review',()=>assert.notEqual(boundaryFixture({env:{SITE_INDEXABLE:'false',SITE_URL:'https://bucheon.fwith.kr'}}).status,0));
test('actual boundary blocks missing explicitfalse even on loopback',()=>assert.notEqual(boundaryFixture({env:{SITE_URL:'http://localhost:8871'}}).status,0));
test('actual boundary permits explicitfalse clean loopback preview',()=>assert.equal(boundaryFixture({env:{SITE_INDEXABLE:'false',SITE_URL:'http://127.0.0.1:8871'}}).status,0));
test('actual fixture boundary reads exact independent evidence bytes',()=>{const r=boundaryFixture({approvedReview:true,env:{SITE_INDEXABLE:'true',SITE_URL:'https://bucheon.fwith.kr'}});assert.equal(r.status,0,r.stderr);});

for(const url of ['http://127.1','http://2130706433','http://localhost/?','http://localhost/#',' http://localhost/','http://localhost./'])test('obfuscated or unclean loopback rejected: '+url,()=>assert.equal(isLocalPreview({SITE_URL:url,SITE_INDEXABLE:'false'}),false));

test('direct Astro config import blocks production noindex pending review',()=>{const r=boundaryFixture({entry:'astro',env:{SITE_INDEXABLE:'false',SITE_URL:'https://bucheon.fwith.kr'}});assert.notEqual(r.status,0);assert.match(r.stderr,/review pending/);});
test('direct Astro config import permits clean local noindex preview',()=>{const r=boundaryFixture({entry:'astro',env:{SITE_INDEXABLE:'false',SITE_URL:'https://127.0.0.1:8934'}});assert.equal(r.status,0,r.stderr);});
for(const file of ['src/data/business-truth.json','src/styles/global.css','scripts/qa_static.py','public/favicon.svg','package-lock.json'])test('runtime byte drift blocks approved fixture: '+file,()=>{const r=boundaryFixture({approvedReview:true,env:{SITE_INDEXABLE:'false',SITE_URL:'https://bucheon.fwith.kr'},mutate:root=>fs.appendFileSync(path.join(root,file),' ')});assert.notEqual(r.status,0);assert.match(r.stderr,/Runtime input bundle drift/);});
test('runtime review digest mismatch rejected',()=>{const x=approved();x.p.independentReview.dependencyHash='stale';assert.throws(()=>run(x),/Review runtime/);});
test('fixed evidence path cannot be overridden',()=>{const x=approved();x.p.independentReview.evidencePath='src/data/other.json';assert.throws(()=>run(x),/evidence file path/);});
test('evidence final symlink rejected',()=>{const root=fs.mkdtempSync(path.join(os.tmpdir(),'bucheon-evidence-test-'));fs.mkdirSync(path.join(root,'src/data'),{recursive:true});fs.writeFileSync(path.join(root,'real.json'),'{}');fs.symlinkSync(path.join(root,'real.json'),path.join(root,'src/data/manual-review-evidence.json'));assert.throws(()=>readReviewEvidence(root),/symlink/);fs.rmSync(root,{recursive:true,force:true});});
test('evidence parent directory symlink rejected even inside root',()=>{const root=fs.mkdtempSync(path.join(os.tmpdir(),'bucheon-evidence-test-'));fs.mkdirSync(path.join(root,'src'));fs.mkdirSync(path.join(root,'real-data'));fs.writeFileSync(path.join(root,'real-data/manual-review-evidence.json'),'{}');fs.symlinkSync(path.join(root,'real-data'),path.join(root,'src/data'),'dir');assert.throws(()=>readReviewEvidence(root),/symlink/);fs.rmSync(root,{recursive:true,force:true});});
