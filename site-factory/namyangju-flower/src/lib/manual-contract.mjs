import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {productFamilies,selectProducts} from './catalog.mjs';
export const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');

const releaseProfiles=Object.freeze({
  "namyangju-missing-pages-20261007": {
    "writerId": "manual-writer-namyangju-20261007",
    "reviewerId": "independent-manual-review-20261007"
  },
  "namyangju-customer-copy-20261011": {
    "writerId": "copy-author-namyangju-20261011",
    "reviewerId": "independent-copy-integration-review-namyangju-20261011",
    "writerActor": "/root/resume_gwangjin_and_next_region/publish_dongdaemun_direct/prepare_dongdaemun_runtime",
    "reviewerActor": "/root/resume_gwangjin_and_next_region/publish_dongdaemun_direct",
    "baselineRevision": "d02e86ed7fc39131431a0332a84002906be2f88b",
    "copyInputPath": "src/data/copy-review-inputs-20261011.json",
    "copyInputSha256": "69116759669f9a8b3021796412b514c51c83864648ad46db438c34b94923c03e",
    "bindings": {
      "approvedArticles": "a1badf2ad757f1781dde09935d8aae22b326332945cccc1bc0398769d0ca4895",
      "articleStatus": "bb8e9cb9aaa0c4740b12537fbbc233c3c093a6723091ebd84bba7efd7fc726ee",
      "articleMergeReview": "ff8b04afd74fe0dc4cce5178a1a37390adb5de5c7e45aed132acbae59e9ec95f",
      "commonManifest": "fb16179ed21703088ab30c7f6bfac3d9256928736db3f13cab0b84d7ec3374bd",
      "commonReview": "cca4eeb94602f1f5ae819d635f0c53ed4caddaa0876c2abcb5fdd260b803ec5a",
      "cardFields": "d967f56b2c05968bd22827763f70382e005d1f07c6fcea04705cbcaef8c6020a",
      "cardMapping": "be182293946b86bda70659622150fe77bd09dbaca6c53b4bb5cc00c6ab289f1f",
      "cardTechnicalReview": "99fd1d07ba0b293e25497ce5c6b90a241289d2ea8ded39aa7a227397c41acd2e",
      "catalogRegistration": "cd5c02492771336f4b35802e41d0632da2e328f84a58a07cbcd45ea858ed888a",
      "imageReview": "509e825c91d4994fe36ab33847ec123d7f3e3ca3fa25768cc986c21e9a7ca815",
      "articleBatchReview1": "83168ffc9c17b70c6997ba6067713dea33a9de261622cccaf89c3093e3d9d19e",
      "articleBatchReview2": "0466d2707b0eacb16cb1c4403dbc8045617e6661c9a90090bdaf18cb0a1643ad",
      "articleBatchReview3": "318f1494f3cea7b0495075029c25c2a4ec6388cc88241de3e9356bd6044e1ffb",
      "articleBatchReview4": "ed3b7e87fee0a8f7431537a83fdaed301c07407075759861b713cfcc8e940aad",
      "articleBatchReview5": "ef7290cca1aedfea87df88d5fe56df6e97b039730bb73ab68cb92ebbc527bbcd"
    }
  }
});
for(const profile of Object.values(releaseProfiles)){if(profile.bindings)Object.freeze(profile.bindings);Object.freeze(profile);}
export function manualReleaseProfile(provenance){
 assert(typeof provenance.manualReleaseId==='string' && Object.hasOwn(releaseProfiles,provenance.manualReleaseId),"Unknown manual release identity");
 const profile=releaseProfiles[provenance.manualReleaseId];
 return profile;
}
// Preserve the historical keyword check. Current copy uses the exact independently reviewed identity.
export function validateManualArticleIdentity(page,provenance,copyInputBytes=null) {
 const profile=manualReleaseProfile(provenance);
 if(!profile.copyInputPath){
  assert(page.firstAnswer.startsWith(page.primaryKeyword.replace(' 안내',''))||page.firstAnswer.includes(page.primaryKeyword.split(' ').slice(0,2).join(' ')));
  return true;
 }
 assert.equal(provenance.writerId,profile.writerId,'Unexpected writer identity');
 assert.equal(provenance.writerActor,profile.writerActor,'Unexpected writer actor');
 assert.equal(provenance.expectedReviewerId,profile.reviewerId,'Unexpected expected reviewer identity');
 assert.equal(provenance.expectedReviewerActor,profile.reviewerActor,'Unexpected expected reviewer actor');
 assert.equal(provenance.baselineRevision,profile.baselineRevision,'Cross-release baseline mismatch');
 assert.equal(provenance.copyInputSha256,profile.copyInputSha256,'Copy input digest mismatch');
 assert.deepEqual(provenance.copyRevisionBindings,profile.bindings,'Copy bindings mismatch');
 assert(copyInputBytes,'Missing actual approved copy input bytes');
 assert.equal(digest(copyInputBytes),profile.copyInputSha256,'Actual copy input bytes mismatch');
 const inputs=JSON.parse(copyInputBytes.toString('utf8'));
 assert.equal(inputs.releaseId,provenance.manualReleaseId,'Copy input release mismatch');
 const artifact=inputs.files.approvedArticles;
 assert.equal(artifact?.sha256,profile.bindings.approvedArticles,'Approved article digest missing');
 assert.equal(digest(artifact.utf8Content),profile.bindings.approvedArticles,'Approved article bytes mismatch');
 const approved=JSON.parse(artifact.utf8Content);
 assert.equal(approved.length,32,'Unexpected approved article count');
 assert.equal(new Set(approved.map(p=>p.pageKey)).size,32,'Duplicate approved article identity');
 const matches=approved.filter(p=>p.pageKey===page.pageKey);
 assert.equal(matches.length,1,'Missing exact approved article identity');
 for(const field of ['pageKey','firstAnswer','primaryKeyword','h1','title','slug','url','contentMarkdown'])
  assert.equal(page[field],matches[0][field],'Approved article identity mismatch: '+field);
 return true;
}
export function validateManualContract(pages,provenance,bytes,products,{indexable=false,reviewEvidenceBytes=null,dependencyHash=null,copyInputBytes=null}={}) {
 assert.equal(provenance.contentHash,digest(bytes),'Manual content digest drift');
 const profile=manualReleaseProfile(provenance);
 assert.equal(provenance.writerId,profile.writerId,'Unexpected writer identity');
 if(profile.copyInputPath){
  assert.equal(provenance.writerActor,profile.writerActor,'Unexpected writer actor');
  assert.equal(provenance.expectedReviewerActor,profile.reviewerActor,'Unexpected expected reviewer actor');
  assert.equal(provenance.baselineRevision,profile.baselineRevision,'Cross-release baseline mismatch');
  assert.equal(provenance.copyInputSha256,profile.copyInputSha256,'Copy input digest mismatch');
  assert.deepEqual(provenance.copyRevisionBindings,profile.bindings,'Copy bindings mismatch');
  assert(copyInputBytes,'Missing actual approved copy input bytes');
  assert.equal(digest(copyInputBytes),profile.copyInputSha256,'Actual copy input bytes mismatch');
  const inputs=JSON.parse(copyInputBytes.toString('utf8'));
  assert.equal(inputs.releaseId,provenance.manualReleaseId,'Copy input release mismatch');
  assert.deepEqual(inputs.bindings,profile.bindings,'Actual copy bindings mismatch');
  for(const [role,hash] of Object.entries(profile.bindings)){
   assert.equal(inputs.files[role]?.sha256,hash,'Missing copy evidence '+role);
   assert.equal(digest(inputs.files[role].utf8Content),hash,'Copy evidence bytes mismatch '+role);
  }
 }
 for(const page of pages){
  assert.equal(page.publicationMode,'manual-user-request');
  assert.equal(page.manualReleaseId,provenance.manualReleaseId);
  for(const f of ['snapshotId','snapshotHash','approvalVerified','sourceRecordId','publishQueueRecordId'])assert.equal(page[f],undefined,'Fabricated frozen provenance: '+f);
  const expected=selectProducts(page,products,profile.copyInputPath&&productFamilies(page).length>3?4:3).map(p=>p.key);
  assert.deepEqual(page.productKeys,expected,'SKU/intent mismatch: '+page.pageKey);
  const families=productFamilies(page);
  if(page.pageType==='funeral-facility')assert.deepEqual(families,['funeral']);
  if(page.pageType==='event-venue')assert.deepEqual(families,['congrats']);
 }
 if(indexable&&pages.length){
  const review=provenance.independentReview;
  assert.equal(review?.status,'approved','Manual independent review pending');
  if(profile.copyInputPath)assert.match(provenance.dependencyHash||'',/^[a-f0-9]{64}$/,'Invalid current dependency digest');
  assert.equal(review.contentHash,provenance.contentHash,'Review does not bind current content');
  assert(review.reviewerId&&review.reviewerId!==provenance.writerId,'Writer cannot approve own content');
  assert(review.evidencePath&&review.reviewedAt,'Missing independent review evidence');
  assert.equal(review.reviewerId,profile.reviewerId,'Unrecognized independent reviewer');
  assert.equal(provenance.expectedReviewerId,review.reviewerId,'Expected reviewer mismatch');
  assert(reviewEvidenceBytes,'Missing actual evidence file bytes');
  assert.equal(digest(reviewEvidenceBytes),review.evidenceSha256,'Evidence file digest mismatch');
  const evidence=JSON.parse(reviewEvidenceBytes.toString('utf8'));
  for(const field of ['manualReleaseId','contentHash','writerId'])assert.equal(evidence[field],provenance[field],'Evidence binding mismatch: '+field);
  assert.equal(evidence.status,'approved','Evidence is not approved');
  assert.equal(evidence.reviewerId,review.reviewerId,'Evidence reviewer mismatch');
  assert.equal(evidence.reviewedAt,review.reviewedAt,'Evidence date mismatch');
  if(profile.copyInputPath){
   assert.equal(review.reviewerActor,profile.reviewerActor,'Unexpected independent reviewer actor');
   assert.notEqual(review.reviewerActor,provenance.writerActor,'Writer actor cannot approve own content');
   for(const item of [review,evidence]){
    assert.equal(item.writerActor,profile.writerActor,'Evidence writer actor mismatch');
    assert.equal(item.reviewerActor,profile.reviewerActor,'Evidence reviewer actor mismatch');
    assert.equal(item.copyInputSha256,profile.copyInputSha256,'Evidence copy input digest mismatch');
    assert.deepEqual(item.copyRevisionBindings,profile.bindings,'Evidence copy bindings mismatch');
   }
  }
  assert(dependencyHash,'Missing computed dependency digest');
  assert.equal(provenance.dependencyHash,dependencyHash,'Source/catalog/renderer/assets digest drift');
  assert.equal(evidence.dependencyHash,dependencyHash,'Evidence dependency mismatch');
  assert.equal(review.dependencyHash,dependencyHash,'Review dependency mismatch');
 }
 return true;
}
