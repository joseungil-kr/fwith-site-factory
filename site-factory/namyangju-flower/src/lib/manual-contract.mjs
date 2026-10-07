import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {productFamilies,selectProducts} from './catalog.mjs';
export const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
export function validateManualContract(pages,provenance,bytes,products,{indexable=false,reviewEvidenceBytes=null,dependencyHash=null}={}) {
 assert.equal(provenance.contentHash,digest(bytes),'Manual content digest drift');
 assert.equal(provenance.writerId,'manual-writer-namyangju-20261007','Unexpected writer identity');
 for(const page of pages){
  assert.equal(page.publicationMode,'manual-user-request');
  assert.equal(page.manualReleaseId,provenance.manualReleaseId);
  for(const f of ['snapshotId','snapshotHash','approvalVerified','sourceRecordId','publishQueueRecordId'])assert.equal(page[f],undefined,'Fabricated frozen provenance: '+f);
  const expected=selectProducts(page,products).map(p=>p.key);
  assert.deepEqual(page.productKeys,expected,'SKU/intent mismatch: '+page.pageKey);
  const families=productFamilies(page);
  if(page.pageType==='funeral-facility')assert.deepEqual(families,['funeral']);
  if(page.pageType==='event-venue')assert.deepEqual(families,['congrats']);
 }
 if(indexable&&pages.length){
  const review=provenance.independentReview;
  assert.equal(review?.status,'approved','Manual independent review pending');
  assert.equal(review.contentHash,provenance.contentHash,'Review does not bind current content');
  assert(review.reviewerId&&review.reviewerId!==provenance.writerId,'Writer cannot approve own content');
  assert(review.evidencePath&&review.reviewedAt,'Missing independent review evidence');
  assert.equal(review.reviewerId,'independent-manual-review-20261007','Unrecognized independent reviewer');
  assert.equal(provenance.expectedReviewerId,review.reviewerId,'Expected reviewer mismatch');
  assert(reviewEvidenceBytes,'Missing actual evidence file bytes');
  assert.equal(digest(reviewEvidenceBytes),review.evidenceSha256,'Evidence file digest mismatch');
  const evidence=JSON.parse(reviewEvidenceBytes.toString('utf8'));
  for(const field of ['manualReleaseId','contentHash','writerId'])assert.equal(evidence[field],provenance[field],'Evidence binding mismatch: '+field);
  assert.equal(evidence.status,'approved','Evidence is not approved');
  assert.equal(evidence.reviewerId,review.reviewerId,'Evidence reviewer mismatch');
  assert.equal(evidence.reviewedAt,review.reviewedAt,'Evidence date mismatch');
  assert(dependencyHash,'Missing computed dependency digest');
  assert.equal(provenance.dependencyHash,dependencyHash,'Source/catalog/renderer/assets digest drift');
  assert.equal(evidence.dependencyHash,dependencyHash,'Evidence dependency mismatch');
  assert.equal(review.dependencyHash,dependencyHash,'Review dependency mismatch');
 }
 return true;
}
