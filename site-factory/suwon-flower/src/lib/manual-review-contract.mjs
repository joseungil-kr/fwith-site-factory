import copyRevision from '../data/customer-copy-revision-20261011.json' with {type:'json'};
import assert from 'node:assert/strict';
export function assertIndependentReview(provenance,evidence,evidenceHash){
 const review=provenance.independentReview;
 assert.equal(review.status,'passed','Independent review remains pending');
 assert.equal(provenance.authorId,'/root/integrate_reviewed_legacy_copy','Unexpected actual writer identity');
 assert.equal(provenance.expectedReviewerId,'/root','Reviewer identity must be assigned by parent');
 assert.notEqual(provenance.authorId,provenance.expectedReviewerId,'Writer cannot review own release');
 assert.equal(review.reviewerId,provenance.expectedReviewerId,'Unexpected reviewer');
 assert.equal(review.evidenceSha256,evidenceHash,'Review evidence file changed');
 assert.equal(evidence.authorId,provenance.authorId,'Evidence author binding mismatch');
 assert.equal(evidence.reviewerId,provenance.expectedReviewerId,'Evidence reviewer binding mismatch');
 assert.notEqual(evidence.authorId,evidence.reviewerId,'Writer and reviewer are identical');
 assert.equal(evidence.releaseId,provenance.releaseId,'Evidence release mismatch');
 assert.equal(evidence.scopeDigest,provenance.scopeDigest,'Reviewed code/assets/catalog/content scope is stale');
 assert.equal(evidence.manualPagesSha256,provenance.manualPagesSha256,'Reviewed pages stale');
 assert.equal(evidence.manualRevisionsSha256,provenance.manualRevisionsSha256,'Reviewed addenda stale');
 assert.equal(evidence.decision,'PASS','Independent decision not PASS');
 assert.equal(evidence.fullBodiesRead,true,'Full independent content read missing');
 assert.equal(evidence.contentQa,'PASS');assert.equal(evidence.codeQa,'PASS');assert.equal(evidence.catalogAndAssetsQa,'PASS');
 assertVisualQa(evidence);
 assert.match(evidence.reviewedAt,/^\d{4}-\d{2}-\d{2}T/);
 return true;
}
export function assertScopeFiles(scopeFileHashes,readHash){
 assert(Object.keys(scopeFileHashes).length>0,'Empty release scope');
 for(const [file,expected] of Object.entries(scopeFileHashes))assert.equal(readHash(file),expected,'Reviewed scope changed: '+file);
 return true;
}

// User-authorized screen-review deferral is explicit evidence, never a visual PASS.
export function assertVisualQa(evidence){
 if(evidence.visualQa==='PASS')return true;
 assert.equal(evidence.visualQa,'DEFERRED_NOT_PASS','Actual rendered-screen review or explicit authorized deferral is required');
 const d=evidence.visualDeferral;assert(d,'Missing visual deferral evidence');
 assert.equal(d.status,'DEFERRED_NOT_PASS');assert.equal(d.criterion,'visualQa');
 assert.equal(d.authorization,'user-requested-batch-deferral');
 assert.equal(d.authorizationReference,"User instruction dated 2026-10-10, restated in scheduled request 2026-10-11T16:00:00Z",'Missing verified visual-deferral authority');
 assert(typeof d.reason==='string'&&d.reason.trim(),'Missing deferral reason');
 assert.deepEqual(d.pendingChecks,['desktop-actual-screen','narrow-actual-screen']);
 assert(Array.isArray(d.pendingPageKeys));assert.equal(new Set(d.pendingPageKeys).size,d.pendingPageKeys.length);
 assert.deepEqual(d.pendingPageKeys.slice().sort(),copyRevision.articles.map(p=>p.pageKey).sort(),'Visual deferral scope differs from exact current articles');
 assert.equal(d.noVisualPassClaim,true);return true;
}
