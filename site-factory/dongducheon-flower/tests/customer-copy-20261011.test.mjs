import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';import {validateGraph,loadGraph} from '../scripts/qa_graph.mjs';
const read=n=>JSON.parse(fs.readFileSync(new URL('../src/data/'+n+'.json',import.meta.url),'utf8'));
const history=JSON.parse(fs.readFileSync(new URL('../docs/customer-copy-history-20261011.json',import.meta.url),'utf8'));
const evidence=JSON.parse(fs.readFileSync(new URL('../docs/customer-copy-review-evidence-20261011.json',import.meta.url),'utf8'));
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const copyFields=["title", "h1", "primaryKeyword", "description", "cardSummary", "firstAnswer", "contentMarkdown", "sections", "faq", "sources", "source"];
const omitted=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);
const expectedHistory="c39bd2b22e8f8868a8727951b75dce98c086663cecd842332dade6737ffff43a",expectedEvidence="ed15675184b7f001f792e55181a03d3778a0402bf4d928c92ab0ac7e820a9687";
test('exact original history and independent copy evidence are retained',()=>{
 assert.equal(sha(fs.readFileSync(new URL('../docs/customer-copy-history-20261011.json',import.meta.url))),expectedHistory);
 assert.equal(sha(fs.readFileSync(new URL('../docs/customer-copy-review-evidence-20261011.json',import.meta.url))),expectedEvidence);
});
for(const old of history.pages)test(old.url+' exact approved copy, new snapshot, protected original fields and four cards',()=>{
 const p=read('pages').find(x=>x.pageKey===old.pageKey),a=evidence.approvedAuthor.find(x=>x.pageKey===old.pageKey);assert(p&&a);
 for(const k of copyFields)assert.deepEqual(p[k],k==='contentMarkdown'?read('notice-followon-review-20261011').approvedCustomerPages.find(q=>q.pageKey===p.pageKey)[k]:a[k],k);
 const allowed=new Set([...copyFields,'snapshotId','snapshotHash']);for(const k of new Set([...Object.keys(old),...Object.keys(p)]))if(!allowed.has(k))assert.deepEqual(p[k],old[k],k);
 const digest=sha(canonical(Object.fromEntries(Object.entries(p).filter(([k])=>!omitted.has(k)))));assert.equal(p.snapshotHash,digest);assert.equal(p.snapshotId,'direct-content-'+p.slug+'-'+digest.slice(0,16));
 for(const n of ['page-map','architecture','publish-manifest']){const m=read(n).pages.find(x=>x.pageKey===p.pageKey);assert.equal(m.snapshotHash,digest);assert.equal(m.snapshotId,p.snapshotId);for(const k of copyFields)if(k in m)assert.deepEqual(m[k],p[k],k);}
 assert.deepEqual(selectProducts(p,read('products'),p.productCardLimit).map(x=>x.key),old.productCardKeys);assert.equal(p.productCardLimit,old.productCardLimit);
});
test('original planned denominator and held routes are not reduced or published',()=>{
 const m=read('publish-manifest'),d=m.directRelease,old=history.directRelease,pages=read('pages');assert.deepEqual(pages.map(x=>x.url),history.pages.map(x=>x.url));
 for(const k of Object.keys(old))if(k!=='contentHashes')assert.deepEqual(d[k],old[k],k);
 assert.equal(d.plannedOriginalCount,old.plannedOriginalCount);assert.equal(d.reviewedArticleCount,old.reviewedArticleCount);assert.equal(pages.filter(p=>p.pageType==='regional-service').length,d.reviewedArticleCount);assert.equal(pages.length,12);assert.equal(pages.filter(p=>p.pageType==='event-venue').length,1);assert(d.reviewedArticleCount*10>=d.plannedOriginalCount*9);assert.deepEqual(m.additiveBatches,history.additiveBatches);
 for(const url of d.deferredRoutes)assert(!pages.some(x=>x.url===url));assert.deepEqual(m.snapshotLedger,{});
 const revision=m.copyRevisions.at(-1);assert.equal(revision.newArticleCount,0);assert.equal(revision.changedExistingArticleCount,pages.length);assert.equal(revision.articleAuthorSha256,evidence.approvedAuthorSha256);assert.equal(revision.independentArticleCopyReviewSha256,evidence.independentArticleReviewSha256);assert.equal(revision.independentCommonCopyReviewSha256,evidence.independentCommonReviewSha256);
});
test('all eight common files equal independently reviewed exact bytes',()=>{assert.equal(evidence.commonFiles.length,8);for(const f of evidence.commonFiles)assert.equal(sha(historicalNoticeCommonBytes(f.path)),f.sha256,f.path);});
test('all product facts except reviewed descriptions remain exact',()=>{for(const p of read('products')){const old=history.products.find(x=>x.key===p.key);for(const k of Object.keys(old))if(k!=='desc')assert.deepEqual(p[k],old[k],p.key+':'+k);}});
test('reviewed full graph passes unchanged validator',()=>assert.equal(validateGraph(loadGraph()).pages,history.pages.length));
test('snapshot mismatch and missing route cannot pass graph parity',()=>{const d=loadGraph();d.pages[0].snapshotId='tampered';assert.throws(()=>validateGraph(d),/Registry parity/);const e=loadGraph();e.pages.pop();assert.throws(()=>validateGraph(e),/Registry count mismatch|Invalid related key|Stale hub/);});

test('current checkpoint separates original regional11of12 and additional event1 from current copy',()=>{
 const historic=JSON.parse(fs.readFileSync(new URL('../docs/notice-followon-history-20261011.json',import.meta.url),'utf8'));const c=JSON.parse(historic.files['src/data/direct-checkpoint.json'].utf8Content),q=c.currentCopyReview;const oldManifest=JSON.parse(historic.files['src/data/publish-manifest.json'].utf8Content);assert.deepEqual(c.historicalInitialRelease.record,history.directCheckpoint);for(const[k,v]of Object.entries(history.directCheckpoint))assert.deepEqual(c[k],v,k);assert.equal(q.articleCount,12);assert.equal(q.originalRegionalPlan,12);assert.equal(q.qualifiedRegionalArticles,11);assert.equal(q.existingAdditionalEventArticles,1);assert.deepEqual(q.heldRoutes,['/regions/geolsan-dong/']);assert.deepEqual(q.contentHashes,oldManifest.directRelease.contentHashes);assert.deepEqual(q.currentCommonFiles,evidence.commonFiles);assert.equal(q.reviewEvidenceSha256,expectedEvidence);assert.equal(q.followupReviewSha256,evidence.independentFollowupReviewSha256);assert.equal(q.articleInputSha256,evidence.approvedAuthorSha256);assert.equal(q.priorArticleInputSha256,evidence.priorApprovedAuthorSha256);assert.equal(q.articleReviewSha256,evidence.independentArticleReviewSha256);assert.equal(q.commonReviewSha256,evidence.independentCommonReviewSha256);assert.equal(q.baselineSource,history.baselineSourceRevision);assert.equal(q.scopeKey,read('publish-manifest').copyRevisions.at(-1).scopeKey);assert.equal(q.state,'independently_reviewed_customer_copy_publication_pending');assert.deepEqual(q.contentHashes,JSON.parse(historic.files['src/data/pages.json'].utf8Content).map(p=>({pageKey:p.pageKey,publicSourceSha256:p.snapshotHash,bodySha256:sha(p.contentMarkdown)})));assert.equal(q.publicSourceRevision,null);for(const k of ['dispatch','publicVerification','searchSubmission'])assert.equal(q[k],'not_performed_for_this_copy_revision');assert.equal(q.visualQa,'DEFERRED_NOT_PASS');
});
test('followup changes only the approved one-phrase deletion and preserves all other approved article fields',()=>{
 let changes=0;for(const p of evidence.approvedAuthor){const prior=evidence.priorApprovedAuthor.find(x=>x.pageKey===p.pageKey);for(const k of new Set([...Object.keys(p),...Object.keys(prior)]))if(JSON.stringify(p[k])!==JSON.stringify(prior[k])){changes++;assert.equal(p.slug,'anheung-dong');assert.equal(k,'contentMarkdown');assert.equal(prior[k].replace('예식 규모에 맞춰 지출을 늘리기보다 ',''),p[k]);}}assert.equal(changes,1);
});
test('friendly ribbon example is once outside the card map and basic price label appears once',()=>{const t=fs.readFileSync(new URL('../src/components/ProductCards.astro',import.meta.url),'utf8');assert.equal(t.split('사진 속 리본은 예시입니다.').length,2);assert.equal(t.split('표시금액은 상품 기본가격입니다.').length,2);assert(t.includes("products.some((p:any)=>p.family==='congrats')"));assert(!t.includes("{p.family==='congrats'"));});

function historicalNoticeCommonBytes(path){const changed=["src/components/ProductCards.astro", "src/layouts/BaseLayout.astro"];return changed.includes(path)?Buffer.from(JSON.parse(fs.readFileSync(new URL('../docs/notice-followon-history-20261011.json',import.meta.url),'utf8')).files[path].utf8Content):fs.readFileSync(new URL('../'+path,import.meta.url));}
