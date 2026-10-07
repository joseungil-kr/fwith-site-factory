import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {productFamilies,selectProducts} from './catalog.mjs';
export const WRITER_ID='bucheon-manual-writer-20261007';
export const REVIEWER_ID='regional-independent-review-20261007';
export const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
export function validateManualContract(pages,provenance,bytes,products,{indexable=false,requireApproval=indexable,reviewEvidence=null,reviewEvidenceBytes=null,catalogBytes=null,dependencyHash=null}={}) {
 assert.equal(provenance.contentHash,digest(bytes),'Manual content digest drift');
 assert.equal(provenance.writerId,WRITER_ID,'Unexpected writer identity');
 assert.equal(provenance.expectedReviewerId,REVIEWER_ID,'Assigned reviewer changed');
 assert(catalogBytes,'Missing catalog bytes');
 assert.equal(provenance.catalogHash,digest(catalogBytes),'Catalog digest drift');
 assert(dependencyHash,'Missing actual runtime input digest');
 assert.equal(provenance.dependencyHash,dependencyHash,'Runtime input bundle drift');
 for(const page of pages){
  assert.equal(page.publicationMode,'manual-user-request');
  assert.equal(page.manualReleaseId,provenance.manualReleaseId);
  for(const f of ['snapshotId','snapshotHash','approvalVerified','sourceRecordId','publishQueueRecordId'])assert.equal(page[f],undefined,'Fabricated frozen provenance: '+f);
  const expected=selectProducts(page,products,productFamilies(page).length>3?4:3).map(p=>p.key);
  assert.deepEqual(page.productKeys,expected,'SKU/intent mismatch: '+page.pageKey);
  const families=productFamilies(page);
  if(page.pageType==='funeral-facility')assert.deepEqual(families,['funeral']);
  if(page.pageType==='event-venue')assert.deepEqual(families,['congrats']);
 }
 if(requireApproval&&pages.length){
  const review=provenance.independentReview;
  assert.equal(review?.status,'approved','Manual independent review pending');
  assert.equal(review.contentHash,provenance.contentHash,'Review does not bind current content');
  assert(review.reviewerId&&review.reviewerId!==provenance.writerId,'Writer cannot approve own content');
  assert.equal(review.evidencePath,'src/data/manual-review-evidence.json','Unexpected evidence file path');
  assert(review.reviewedAt&&!Number.isNaN(Date.parse(review.reviewedAt)),'Missing independent review date');
  assert.equal(review.dependencyHash,dependencyHash,'Review runtime mismatch');
  assert.equal(review.reviewerId,provenance.expectedReviewerId,'Unexpected independent reviewer');
  assert(reviewEvidence,'Missing independent evidence document');
  assert(reviewEvidenceBytes,'Missing independent evidence bytes');
  assert.equal(review.evidenceSha256,digest(reviewEvidenceBytes),'Evidence bytes digest mismatch');
  assert.deepEqual(reviewEvidence,JSON.parse(Buffer.from(reviewEvidenceBytes).toString('utf8')),'Evidence object does not match actual bytes');
  assert.equal(review.catalogHash,provenance.catalogHash,'Review catalog mismatch');
  assert.equal(reviewEvidence.catalogHash,provenance.catalogHash,'Evidence catalog mismatch');
  assert.equal(reviewEvidence.dependencyHash,dependencyHash,'Evidence runtime mismatch');
  assert.equal(reviewEvidence.reviewedAt,review.reviewedAt,'Evidence review date mismatch');
  assert.equal(reviewEvidence.status,'approved','Evidence is not approved');
  assert.equal(reviewEvidence.reviewerId,review.reviewerId,'Evidence reviewer mismatch');
  assert.equal(reviewEvidence.writerId,provenance.writerId,'Evidence writer mismatch');
  assert.equal(reviewEvidence.contentHash,provenance.contentHash,'Evidence digest mismatch');
  assert.equal(reviewEvidence.manualReleaseId,provenance.manualReleaseId,'Evidence release mismatch');
 }
 return true;
}
