import assert from 'node:assert/strict';
export function assertIndependentReview(provenance,evidence,evidenceHash){
 const review=provenance.independentReview;
 assert.equal(review.status,'passed','Independent review remains pending');
 assert.match(provenance.authorId,/^[a-f0-9-]{36}$/,'Missing opaque writer identity');
 assert.match(provenance.expectedReviewerId,/^[a-zA-Z0-9][a-zA-Z0-9-]{15,99}$/,'Reviewer identity must be assigned by parent');
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
 assert.equal(evidence.visualQa,'PASS','Actual rendered-screen review is still required');
 assert.match(evidence.reviewedAt,/^\d{4}-\d{2}-\d{2}T/);
 return true;
}
export function assertScopeFiles(scopeFileHashes,readHash){
 assert(Object.keys(scopeFileHashes).length>0,'Empty release scope');
 for(const [file,expected] of Object.entries(scopeFileHashes))assert.equal(readHash(file),expected,'Reviewed scope changed: '+file);
 return true;
}
