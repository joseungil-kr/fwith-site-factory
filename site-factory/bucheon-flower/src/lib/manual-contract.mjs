import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {productFamilies,selectProducts} from './catalog.mjs';
export const WRITER_ID='copy-author-bucheon-20261011';
export const REVIEWER_ID='independent-copy-integration-review-bucheon-20261011';
export const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');

const releaseProfiles=Object.freeze({
  "bucheon-missing-pages-20261007": {
    "writerId": "bucheon-manual-writer-20261007",
    "reviewerId": "regional-independent-review-20261007"
  },
  "bucheon-customer-copy-20261011": {
    "writerId": "copy-author-bucheon-20261011",
    "reviewerId": "independent-copy-integration-review-bucheon-20261011",
    "writerActor": "/root/plan_existing_region_updates",
    "reviewerActor": "/root",
    "baselineRevision": "1f00f46ef2afad7dcc0ca814d98ec31cf7abc73e",
    "copyInputPath": "src/data/copy-review-inputs-20261011.json",
    "copyInputSha256": "2f376e4d97ab6092d351bf9dad98042f3364bad25f36364739087837b039f5b5",
    "bindings": {
      "articleAndSurfaceReview": "c7cd6138f4f5027aeb52c19b954bff9bd1b278bffaae836a34063811542972e0",
      "surfaceManifest": "8e2ef0a9251d22e935a3872ef53e5f79215ae16ebd8bd1696d1d204f862a65ea",
      "surfaceReview": "e5b38d2db1719660d944e65cc0d192e21ad81d0f736e37374f19415e2a2eb369",
      "articleBatchReview1": "2a1bfa35f5f0dfa660dfb8940dc3907912727fde5a79606505b629de3908190d",
      "articleBatchManifest1": "b6ca2968354b298c0a71cab608d67ad26be1a6f81a71c4366385fdd089437557",
      "articleBatchReview2": "c3e49693dc17198da8b33e858921c33965ab622c39637a7017498a99135d2c39",
      "articleBatchManifest2": "c21f9179a67f85fed5f82ef2e40f54168ee23d9c4ca7a0d060cf9e5f4a88a1bb",
      "articleBatchReview3": "6d6241505e532e8e7433beaf2d09347dd9617232e406d723dcd43b34ce41757a",
      "articleBatchManifest3": "4d65cccd8d52564b2b96120b9fb980b009f463ff25f542cc91c6f2984dd6d0a3",
      "articleBatchReview4": "5a93fd76c9e2beae4b1e2797fcad96a03009acd2ddecfe279628c586d6422d15",
      "articleBatchManifest4": "9a1d4d6522f5a5496191867dc6437e99313079beb5aec0ae61d160586f242e17",
      "articleBatchReview5": "5171fe2e4524766d5ce3dd561cb1889c164ba51e36d7d3e193ff45fa1e1dbf1d",
      "articleBatchManifest5": "ed2cb8667164cf2f6a7ce720775b82bd12f373b33786abd85e5b67998405e6ce",
      "articleBatchReview6": "6ef469be652a38a2c94d5f47b3b479bd176cd9c2aad2a1716ab768519fb120b7",
      "articleBatchManifest6": "f3da90d7586b15ae75fd8954b6ae9df162846463983b444c94ee049871654680",
      "articleBatchReview7": "341fdfcb01c824b2d39f622e2897b9cd2aa28e64a1fddeb9fcd7bf0c1fc3fd30",
      "articleBatchManifest7": "2b37cff5bd785603c916029f896d4d9648b41599c5f969e39f3ad55a300813b2",
      "articleBatchReview8": "4a70a101194c02036efef4b68b219d36da48b088216bc66e49759db6cf487afb",
      "articleBatchManifest8": "8f8217ffbae8cd59c60fdcedadabbfafea3837c4019e1199a58d746e8dbf93c3",
      "articleBatchReview9": "e8efd67fdf2bc7344d3cd0b9d9c3ca7cb6bf78c50f1938f0aaba3588c04ecf2d",
      "articleBatchManifest9": "e4fb21c8a8f0e6ccce51a088f4f07d3b7712ee62a96c2d57b8a3af841320e883",
      "approvedArticles": "f22fef0f8a5f67f2b9f9dece3d5247292c5367532b8242fc90fd9d4564e62c80"
    }
  }
});
for(const p of Object.values(releaseProfiles)){if(p.bindings)Object.freeze(p.bindings);Object.freeze(p);}
export function manualReleaseProfile(provenance){
 assert(typeof provenance.manualReleaseId==='string' && Object.hasOwn(releaseProfiles,provenance.manualReleaseId),'Unknown manual release identity');
 return releaseProfiles[provenance.manualReleaseId];
}
export function validateManualContract(pages,provenance,bytes,products,{indexable=false,requireApproval=indexable,reviewEvidence=null,reviewEvidenceBytes=null,catalogBytes=null,dependencyHash=null,copyInputBytes=null}={}) {
 assert.equal(provenance.contentHash,digest(bytes),'Manual content digest drift');
 const profile=manualReleaseProfile(provenance);
 assert.equal(provenance.writerId,profile.writerId,'Unexpected writer identity');
 assert.equal(provenance.expectedReviewerId,profile.reviewerId,'Assigned reviewer changed');
 if(profile.copyInputPath){
  assert.equal(provenance.writerActor,profile.writerActor,'Unexpected writer actor');
  assert.equal(provenance.expectedReviewerActor,profile.reviewerActor,'Unexpected expected reviewer actor');
  assert.equal(provenance.baselineRevision,profile.baselineRevision,'Cross-release baseline mismatch');
  assert.equal(provenance.copyInputSha256,profile.copyInputSha256,'Copy input digest mismatch');
  assert.deepEqual(provenance.copyRevisionBindings,profile.bindings,'Copy binding mismatch');
  assert(copyInputBytes,'Missing actual copy input bytes');
  assert.equal(digest(copyInputBytes),profile.copyInputSha256,'Actual copy input digest mismatch');
  const inputs=JSON.parse(copyInputBytes.toString('utf8'));
  assert.equal(inputs.releaseId,provenance.manualReleaseId,'Copy input release mismatch');
  assert.deepEqual(inputs.bindings,profile.bindings,'Actual copy bindings mismatch');
  for(const [role,hash] of Object.entries(profile.bindings)){
   assert.equal(inputs.files[role]?.sha256,hash,'Copy evidence digest mismatch');
   assert.equal(digest(inputs.files[role].utf8Content),hash,'Copy evidence bytes mismatch');
  }
 }
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
  if(profile.copyInputPath){
   assert.notEqual(provenance.writerActor,profile.reviewerActor,'Writer actor cannot approve own content');
   for(const item of [review,reviewEvidence]){
    assert.equal(item.writerActor,profile.writerActor,'Evidence writer actor mismatch');
    assert.equal(item.reviewerActor,profile.reviewerActor,'Evidence reviewer actor mismatch');
    assert.equal(item.copyInputSha256,profile.copyInputSha256,'Evidence copy input digest mismatch');
    assert.deepEqual(item.copyRevisionBindings,profile.bindings,'Evidence copy bindings mismatch');
   }
  }
 }
 return true;
}
