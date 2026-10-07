import test from 'node:test';import assert from 'node:assert/strict';import crypto from 'node:crypto';
import {validateReview,requiredCriteria,isLocalNoindexPreview,assignedWriter,assignedReviewer,releaseOrigin} from '../src/lib/manual-release-gate.mjs';
import {validateIndexNowDomain} from './indexnow-domain.mjs';
const hash=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const evidence={pages:[{pageKey:'test-only',decision:'pass',criteria:Object.fromEntries(requiredCriteria.map(k=>[k,'pass']))}]};
const valid={schemaVersion:1,decision:'pass',writerLabel:assignedWriter,reviewerLabel:assignedReviewer,releaseOrigin,artifactDigest:'test-digest',reviewedAt:'2026-10-07T10:00:00Z',evidence,evidenceSha256:hash(evidence)};
test('test fixture complete review succeeds; never writes release evidence',()=>assert.equal(validateReview(valid,'test-digest',['test-only']),true));
for(const [name,patch] of [['pending',{decision:'pending'}],['digest drift',{artifactDigest:'old'}],['same identity',{writerLabel:'writer-same',reviewerLabel:'reviewer-same'}],['unknown reviewer',{reviewerLabel:'reviewer-unknown'}],['swapped aliases',{writerLabel:assignedReviewer,reviewerLabel:assignedWriter}],['proof drift',{evidenceSha256:'bad'}],['missing timestamp',{reviewedAt:null}]])test('reject '+name,()=>assert.throws(()=>validateReview({...valid,...patch},'test-digest',['test-only'])));
test('reject missing visual result',()=>{const ev=structuredClone(evidence);ev.pages[0].criteria.mobileAndDesktopVisual='not-run';assert.throws(()=>validateReview({...valid,evidence:ev,evidenceSha256:hash(ev)},'test-digest',['test-only']));});
test('IndexNow allows exact Yongin host only',()=>assert.equal(validateIndexNowDomain('https://yongin.fwith.kr',['https://yongin.fwith.kr/business/a/']),true));
for(const wrong of ['https://hwaseong.fwith.kr','http://yongin.fwith.kr','https://yongin.fwith.kr.evil.example'])test('IndexNow rejects wrong origin '+wrong,()=>assert.throws(()=>validateIndexNowDomain(wrong,[])));
test('IndexNow rejects mixed-host URL list before any request',()=>assert.throws(()=>validateIndexNowDomain('https://yongin.fwith.kr',['https://hwaseong.fwith.kr/a/'])));

for(const origin of ['https://yongin.fwith.kr','https://unknown.example','https://localhost.evil.example','https://localhost@evil.example','file:///tmp/site','http://localhost/path'])test('noindex public/invalid origin cannot bypass review '+origin,()=>assert.equal(isLocalNoindexPreview({SITE_INDEXABLE:'false',SITE_URL:origin}),false));
test('noindex without explicit preview origin cannot bypass',()=>assert.equal(isLocalNoindexPreview({SITE_INDEXABLE:'false'}),false));
test('indexable loopback cannot bypass review',()=>assert.equal(isLocalNoindexPreview({SITE_INDEXABLE:'true',SITE_URL:'http://localhost:4321'}),false));
test('explicit loopback noindex preview allowed',()=>assert.equal(isLocalNoindexPreview({SITE_INDEXABLE:'false',SITE_URL:'http://127.0.0.1:4321'}),true));
