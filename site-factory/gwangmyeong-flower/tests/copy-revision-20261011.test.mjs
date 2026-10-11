import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const read=n=>JSON.parse(fs.readFileSync(new URL('../src/data/'+n+'.json',import.meta.url),'utf8'));
const history=JSON.parse(fs.readFileSync(new URL('../docs/customer-copy-history-20261011.json',import.meta.url),'utf8'));
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const expected={"gwangmyeong-flower-direct-region-gwangmyeong-dong": {"snapshot": "0ea9cba9ba80789b08aeb2487f918aea47aa4ca924c4dab206a8ff9fe857f519", "body": "52490743019d34ec84ca59e025de8612d18140ff35b8a292350f3fd01cd40942"}, "gwangmyeong-flower-direct-region-cheolsan-dong": {"snapshot": "457249b63fb556a685aded2bf03bb685e1cc057776bf81a2b7a65f392a217323", "body": "c6371725fdb8c11483ef5b8a941c8321ab6919ba75d3a397de199f0358f7e5c2"}, "gwangmyeong-flower-direct-region-haan-dong": {"snapshot": "72042e7848912d435b5730d4de0f2eb6dd7daf6c224599f64036f4a9068992ca", "body": "f05281414dac5a7edd7f821a40b4e36c7a8b7a9b66df41e6ba9e3dcc9da2c063"}, "gwangmyeong-flower-direct-region-soha-dong": {"snapshot": "5add20da8181d907592ab42ffe18da79864e08d891af4b15803c812206eb906c", "body": "b16b75acd294f5fc47906dad55bdc4f1e439218189061136bedc1282b80624ac"}, "gwangmyeong-flower-direct-region-iljik-dong": {"snapshot": "e9b635e29220a50fa9d822f319475c868bf5daa4b8e7d37d27afdd97a1750cbd", "body": "71f5d7e1e3ff5e8650b82f5b1f1ba71d3bad191bde3b8160acc80fe80d08fd5a"}, "gwangmyeong-flower-direct-region-noonsa-dong": {"snapshot": "265e27fe5d5d10a4b240231c6cd35ce75ed8361d5afe3313156f52759472d4fb", "body": "e0303fe2f5d0a289859f983a9d36f1227767ddaf62d164889b32fe2d7c285862"}, "gwangmyeong-flower-direct-region-gahak-dong": {"snapshot": "0b51300018a70dcd11eff8925c1e4d5c81a615934c5445be22622d967fd49f4f", "body": "754bfe03a69430fa711867ac1a4f47d254a5df2d4c30b3ce4821ed1cc740e9d9"}, "gwangmyeong-flower-direct-region-okgil-dong": {"snapshot": "e504abb00ab4a8bfa8e196b4af4b4b2473457fd0e05f49b1ab8a8bcb21dfa411", "body": "60449472770e05ea54bb2a47e57b59a04f38f1288608c4633cb14c5f955bc2aa"}, "gwangmyeong-flower-direct-event-gwangmyeong-lapoete-wedding-wreath": {"snapshot": "2c5900e42c0e8eb1db96ada5ca1ee25475028283a790cc7cc7dc5cc1a382aee1", "body": "7122e63e53f37184da62cfc8c310aa2dee9ab39e32c46a49e800492e35d5a9d7"}};
const expectedReviews={"independentRegionalCopyReviewSha256": "8fbda6461545bf2a81b80613ff9635a62265449b4ab7a8b6c8ad4331e21b89fc", "independentVenueCopyReviewSha256": "aa59eeee5e88a5fb6a10b6040a352b82823cc3fafa3c713d52b7a3c3e3a31428", "independentSurfaceCopyReviewSha256": "8fbda6461545bf2a81b80613ff9635a62265449b4ab7a8b6c8ad4331e21b89fc"};
const allowed=new Set(['description','cardSummary','firstAnswer','contentMarkdown','buyerQuestion','uniqueLocalDecision','sources','source','snapshotId','snapshotHash']);
test('all nine reviewed articles keep every non-copy field and original denominator',()=>{
 const p=read('pages'),m=read('publish-manifest');assert.equal(p.length,9);assert.equal(history.publicPages.length,9);
 for(const old of history.publicPages){const a=p.find(x=>x.pageKey===old.pageKey);assert.ok(a);for(const key of new Set([...Object.keys(old),...Object.keys(a)]))if(!allowed.has(key))assert.deepEqual(a[key],old[key],old.slug+':'+key);}
 assert.equal(m.directRelease.plannedOriginalCount,8);assert.equal(m.directRelease.reviewedArticleCount,8);assert.deepEqual(m.directRelease.deferredRoutes,[]);assert.equal(m.additiveBatches[0].plannedOriginalCount,1);assert.equal(m.additiveBatches[0].resultingArticleCount,9);
});
test('all nine current bodies and snapshots equal independently reviewed revisions',()=>{
 const p=read('pages');assert.deepEqual(p.map(x=>x.pageKey).sort(),Object.keys(expected).sort());
 for(const a of p){assert.equal(a.snapshotHash,expected[a.pageKey].snapshot);assert.equal(sha(a.contentMarkdown),expected[a.pageKey].body);assert.notEqual(a.cardSummary,a.firstAnswer);assert.doesNotMatch(a.contentMarkdown,/드림어스|811·812|주차장 안내|추정하지|가정하지|검증 도구|검색 공개문/);}
 const revision=read('publish-manifest').copyRevisions.at(-1);
 assert.equal(revision.changedExistingArticleCount,9);
 for(const [key,digest] of Object.entries(expectedReviews))assert.equal(revision[key],digest);
});
test('product identities, photos, prices, and factual delivery notices remain intact',()=>{
 const p=read('products');assert.equal(p.length,history.previousProducts.length);
 for(const old of history.previousProducts){const a=p.find(x=>x.key===old.key);for(const k of new Set([...Object.keys(old),...Object.keys(a)]))if(k!=='desc')assert.deepEqual(a[k],old[k]);}
 const truth=read('business-truth');assert.match(truth.deliveryNotice,/추가 배송비/);assert.match(truth.productVariationNotice,/지역 및 계절/);
});
test('actual facility restriction remains while repeated source-card warnings are removed',()=>{
 const a=read('pages').find(x=>x.slug==='iljik-dong');assert.match(a.contentMarkdown,/통로가 아닌 분향소 안/);
 const detail=fs.readFileSync(new URL('../src/pages/[category]/[slug].astro',import.meta.url),'utf8');assert.doesNotMatch(detail,/확인한 출처입니다\. 상품 구성/);assert.ok(detail.includes('source.verifiedAt'));
});
