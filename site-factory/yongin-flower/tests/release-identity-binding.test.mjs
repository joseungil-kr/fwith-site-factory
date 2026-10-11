import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';
import {assignedWriter,assignedReviewer,releaseOrigin,requiredCriteria,validateReview,assertManualProductionReady,artifactDigest,isLocalNoindexPreview} from '../src/lib/manual-release-gate.mjs';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const keys=read('src/data/manual-pages.json').pages.map(p=>p.pageKey);
const proof=e=>crypto.createHash('sha256').update(JSON.stringify(e)).digest('hex');
const rehash=x=>(x.evidenceSha256=proof(x.evidence),x);
const fixture=()=>{const evidence={pages:keys.map(pageKey=>({pageKey,decision:'pass',criteria:Object.fromEntries(requiredCriteria.map(k=>[k,'pass']))}))};return {schemaVersion:1,decision:'pass',releaseOrigin,artifactDigest:'a'.repeat(64),writerLabel:assignedWriter,reviewerLabel:assignedReviewer,reviewedAt:'2026-10-11T00:00:00Z',evidence,evidenceSha256:proof(evidence)};};
const deferred=()=>{const x=fixture();for(const p of x.evidence.pages)p.criteria.mobileAndDesktopVisual='DEFERRED_NOT_PASS';x.evidence.visualDeferral={status:'DEFERRED_NOT_PASS',criterion:'mobileAndDesktopVisual',authorization:'user-requested-batch-deferral',authorizationReference:'SYNTHETIC_UNIT_TEST_ONLY_NOT_REAL_AUTHORIZATION',reason:'Synthetic fixture for explicit visual deferral validation.',pendingChecks:['desktop-actual-screen','narrow-actual-screen'],pendingPageKeys:[...keys],noVisualPassClaim:true};return rehash(x);};
// All PASS and deferral authorization objects below are in-memory test fixtures, never production receipts.
test('designated actual writer and independent final reviewer remain distinct',()=>{assert.equal(assignedWriter,'/root/audit_regional_sales_copy');assert.equal(assignedReviewer,'/root');assert.notEqual(assignedWriter,assignedReviewer);assert.equal(validateReview(fixture(),'a'.repeat(64),keys),true);});
const invalid={
 'historical identity tuple':x=>Object.assign(x,{writerLabel:'bf80b5b2-7a03-4e58-8ec1-0f855389ba48',reviewerLabel:'supplement-guide-review-89bc7a8013c04401'}),
 'author acting as own reviewer':x=>x.reviewerLabel=x.writerLabel,
 'other independent reviewer not assigned to final receipt':x=>x.reviewerLabel='/root/review_remaining_regional_copy',
 'pending decision':x=>x.decision='pending',
 'changed artifact digest':x=>x.artifactDigest='b'.repeat(64),
 'wrong origin':x=>x.releaseOrigin='https://other.invalid',
 'missing review date':x=>x.reviewedAt=null,
 'missing reviewed page':x=>{x.evidence.pages.pop();rehash(x);},
 'duplicate reviewed page':x=>{x.evidence.pages[1]=x.evidence.pages[0];rehash(x);},
 'visual pending without explicit deferral':x=>{x.evidence.pages[0].criteria.mobileAndDesktopVisual='pending';rehash(x);},
 'tampered evidence hash':x=>x.evidenceSha256='0'.repeat(64)
};
for(const [name,mutate] of Object.entries(invalid))test('production receipt still rejects '+name,()=>{const x=fixture();mutate(x);assert.throws(()=>validateReview(x,'a'.repeat(64),keys),/MANUAL_RELEASE_BLOCKED/);});
test('explicit visual deferral succeeds without changing criterion values to PASS',()=>{const x=deferred(),before=JSON.stringify(x);assert.equal(validateReview(x,'a'.repeat(64),keys),true);assert.equal(JSON.stringify(x),before);assert.ok(x.evidence.pages.every(p=>p.criteria.mobileAndDesktopVisual==='DEFERRED_NOT_PASS'));});
test('already passed visual pages remain passed while exact remaining pages are deferred',()=>{const x=deferred();x.evidence.pages[0].criteria.mobileAndDesktopVisual='pass';x.evidence.visualDeferral.pendingPageKeys.shift();rehash(x);assert.equal(validateReview(x,'a'.repeat(64),keys),true);assert.equal(x.evidence.pages[0].criteria.mobileAndDesktopVisual,'pass');});
const invalidDeferral={
 'missing deferral object':x=>delete x.evidence.visualDeferral,
 'wrong status':x=>x.evidence.visualDeferral.status='pass',
 'another criterion':x=>x.evidence.visualDeferral.criterion='sourceAccuracy',
 'implicit authorization':x=>delete x.evidence.visualDeferral.authorization,
 'missing authorization reference':x=>x.evidence.visualDeferral.authorizationReference=null,
 'blank authorization reference':x=>x.evidence.visualDeferral.authorizationReference=' ',
 'missing reason':x=>x.evidence.visualDeferral.reason='',
 'false visual PASS claim':x=>x.evidence.visualDeferral.noVisualPassClaim=false,
 'missing desktop follow-up':x=>x.evidence.visualDeferral.pendingChecks=['narrow-actual-screen'],
 'missing narrow follow-up':x=>x.evidence.visualDeferral.pendingChecks=['desktop-actual-screen'],
 'duplicate follow-up':x=>x.evidence.visualDeferral.pendingChecks=['desktop-actual-screen','desktop-actual-screen'],
 'missing deferred page':x=>x.evidence.visualDeferral.pendingPageKeys.pop(),
 'duplicate deferred page':x=>x.evidence.visualDeferral.pendingPageKeys[1]=keys[0],
 'unknown deferred page':x=>x.evidence.visualDeferral.pendingPageKeys[0]='unknown-page',
 'lowercase informal deferral':x=>x.evidence.pages[0].criteria.mobileAndDesktopVisual='deferred',
 'stale deferral after all visual checks passed':x=>{for(const p of x.evidence.pages)p.criteria.mobileAndDesktopVisual='pass';}
};
for(const [name,mutate] of Object.entries(invalidDeferral))test('visual deferral rejects '+name,()=>{const x=deferred();mutate(x);rehash(x);assert.throws(()=>validateReview(x,'a'.repeat(64),keys),/MANUAL_RELEASE_BLOCKED/);});
for(const criterion of requiredCriteria.filter(c=>c!=='mobileAndDesktopVisual'))test('DEFERRED_NOT_PASS cannot excuse '+criterion,()=>{const x=deferred();x.evidence.pages[0].criteria[criterion]='DEFERRED_NOT_PASS';rehash(x);assert.throws(()=>validateReview(x,'a'.repeat(64),keys),/not passed/);});
test('deferral evidence remains hash protected',()=>{const x=deferred();x.evidence.visualDeferral.reason+=' changed';assert.throws(()=>validateReview(x,'a'.repeat(64),keys),/evidence digest differs/);});
test('persisted receipt validates according to actual pending or independently approved state',()=>{const x=read('src/data/manual-integrated-review-20261011.json');assert.ok(['pending','pass'].includes(x.decision));assert.equal(x.writerLabel,assignedWriter);assert.equal(x.reviewerLabel,assignedReviewer);assert.equal(x.artifactDigest,artifactDigest());assert.equal(x.evidenceSha256,proof(x.evidence));assert.deepEqual(x.evidence.pages.map(p=>p.pageKey),keys);assert.throws(()=>validateReview({...structuredClone(x),decision:'pending'},artifactDigest(),keys),/independent PASS missing/);if(x.decision==='pass')assert.equal(validateReview(x,artifactDigest(),keys),true);else assert.equal(x.reviewedAt,null);});
for(const mode of ['pass','DEFERRED_NOT_PASS'])test('production result preserves visual disposition '+mode,t=>{const x=mode==='pass'?fixture():deferred();x.artifactDigest=artifactDigest();const original=fs.readFileSync.bind(fs);t.mock.method(fs,'readFileSync',(file,...args)=>String(file).endsWith('/src/data/manual-integrated-review-20261011.json')?(args[0]==='utf8'?JSON.stringify(x):Buffer.from(JSON.stringify(x))):original(file,...args));const old={SITE_URL:process.env.SITE_URL,SITE_INDEXABLE:process.env.SITE_INDEXABLE};try{process.env.SITE_URL=releaseOrigin;process.env.SITE_INDEXABLE='true';assert.deepEqual(assertManualProductionReady(),{mode:'production',releaseApproved:true,visualQa:mode==='pass'?'PASS':'DEFERRED_NOT_PASS'});}finally{t.mock.restoreAll();for(const [k,v] of Object.entries(old))if(v===undefined)delete process.env[k];else process.env[k]=v;}});
test('preview remains loopback only and explicitly noindex',()=>{assert.equal(isLocalNoindexPreview({SITE_URL:'http://127.0.0.1:4321',SITE_INDEXABLE:'false'}),true);for(const env of [{SITE_URL:releaseOrigin,SITE_INDEXABLE:'false'},{SITE_URL:'http://127.0.0.1:4321',SITE_INDEXABLE:'true'},{SITE_URL:'http://127.0.0.1:4321/path',SITE_INDEXABLE:'false'}])assert.equal(isLocalNoindexPreview(env),false);});
