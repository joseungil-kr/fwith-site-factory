import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';import {validateGraph,loadGraph} from '../scripts/qa_graph.mjs';
const read=n=>JSON.parse(fs.readFileSync(new URL('../src/data/'+n+'.json',import.meta.url),'utf8'));
const history=JSON.parse(fs.readFileSync(new URL('../docs/customer-copy-history-20261011.json',import.meta.url),'utf8'));
const evidence=JSON.parse(fs.readFileSync(new URL('../docs/customer-copy-review-evidence-20261011.json',import.meta.url),'utf8'));
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const copyFields=["title", "h1", "primaryKeyword", "description", "cardSummary", "firstAnswer", "contentMarkdown", "sections", "faq", "sources", "source"];
const omitted=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);
const expectedHistory="afa595eaf57f4835efe2933574199c99badc2bc7bddaa25e8b58a4d285957458",expectedEvidence="0f54e55aca5360beb0ff5d16cb3e556d62c0f323469745ef745da8b37be4849f";
test('exact original history and independent copy evidence are retained',()=>{
 assert.equal(sha(fs.readFileSync(new URL('../docs/customer-copy-history-20261011.json',import.meta.url))),expectedHistory);
 assert.equal(sha(fs.readFileSync(new URL('../docs/customer-copy-review-evidence-20261011.json',import.meta.url))),expectedEvidence);
});
for(const old of history.pages)test(old.url+' exact approved copy, new snapshot, protected original fields and four cards',()=>{
 const p=read('pages').find(x=>x.pageKey===old.pageKey),a=evidence.approvedAuthor.find(x=>x.pageKey===old.pageKey);assert(p&&a);
 for(const k of copyFields)assert.deepEqual(p[k],a[k],k);
 const allowed=new Set([...copyFields,'snapshotId','snapshotHash']);for(const k of new Set([...Object.keys(old),...Object.keys(p)]))if(!allowed.has(k))assert.deepEqual(p[k],old[k],k);
 const digest=sha(canonical(Object.fromEntries(Object.entries(p).filter(([k])=>!omitted.has(k)))));assert.equal(p.snapshotHash,digest);assert.equal(p.snapshotId,'direct-content-'+p.slug+'-'+digest.slice(0,16));
 for(const n of ['page-map','architecture','publish-manifest']){const m=read(n).pages.find(x=>x.pageKey===p.pageKey);assert.equal(m.snapshotHash,digest);assert.equal(m.snapshotId,p.snapshotId);for(const k of copyFields)if(k in m)assert.deepEqual(m[k],p[k],k);}
 assert.deepEqual(selectProducts(p,read('products'),p.productCardLimit).map(x=>x.key),old.productCardKeys);assert.equal(p.productCardLimit,4);
});
test('original planned denominator and held routes are not reduced or published',()=>{
 const m=read('publish-manifest'),d=m.directRelease,old=history.directRelease,pages=read('pages');assert.deepEqual(pages.map(x=>x.url),history.pages.map(x=>x.url));
 for(const k of Object.keys(old))if(k!=='contentHashes')assert.deepEqual(d[k],old[k],k);
 assert.equal(d.plannedOriginalCount,old.plannedOriginalCount);assert.equal(d.reviewedArticleCount,old.reviewedArticleCount);assert.equal(pages.length,d.reviewedArticleCount);assert(pages.length*10>=d.plannedOriginalCount*9);
 for(const url of d.deferredRoutes)assert(!pages.some(x=>x.url===url));assert.deepEqual(m.snapshotLedger,{});
 const revision=m.copyRevisions.at(-1);assert.equal(revision.newArticleCount,0);assert.equal(revision.changedExistingArticleCount,pages.length);assert.equal(revision.articleAuthorSha256,evidence.approvedAuthorSha256);assert.equal(revision.independentArticleCopyReviewSha256,evidence.independentArticleReviewSha256);assert.equal(revision.independentCommonCopyReviewSha256,evidence.independentCommonReviewSha256);
});
test('eight approved common files plus exact single-particle correction preserve all other bytes',()=>{assert.equal(evidence.commonFiles.length,8);for(const f of evidence.commonFiles){let bytes=fs.readFileSync(new URL('../'+f.path,import.meta.url));if(f.path==='src/components/InlineOrderBanner.astro'){const text=bytes.toString('utf8');assert.equal(text.split('{site.brand}과 편하게 이야기해 보세요').length,2);assert(!text.includes('{site.brand}와 편하게 이야기해 보세요'));bytes=Buffer.from(text.replace('{site.brand}과 편하게 이야기해 보세요','{site.brand}와 편하게 이야기해 보세요'));}assert.equal(sha(bytes),f.newSha256,f.path);}});
 test('banner brand interpolation has the correct Korean particle',()=>{const component=fs.readFileSync(new URL('../src/components/InlineOrderBanner.astro',import.meta.url),'utf8');const label=component.match(/<strong>([^<]+)<\/strong>/)[1].replace('{site.brand}',read('business-truth').brand);assert.equal(label,'꽃이랑과 편하게 이야기해 보세요');assert(!label.includes('꽃이랑와'));});
test('all product facts except reviewed descriptions remain exact',()=>{for(const p of read('products')){const old=history.products.find(x=>x.key===p.key);for(const k of Object.keys(old))if(k!=='desc')assert.deepEqual(p[k],old[k],p.key+':'+k);}});
test('reviewed full graph passes unchanged validator',()=>assert.equal(validateGraph(loadGraph()).pages,history.pages.length));
test('snapshot mismatch and missing route cannot pass graph parity',()=>{const d=loadGraph();d.pages[0].snapshotId='tampered';assert.throws(()=>validateGraph(d),/Registry parity/);const e=loadGraph();e.pages.pop();assert.throws(()=>validateGraph(e),/Registry count mismatch|Invalid related key|Stale hub/);});

test('obsolete external return-address exception remains in history only',()=>{
 const old=history.pages.find(p=>p.slug==='cheonsong-dong'),current=read('pages').find(p=>p.slug==='cheonsong-dong');
 assert.match(old.contentMarkdown,/광명시 일직로 72/);assert(old.sources.some(s=>s.url==='https://dapiofficial.co.kr/shopinfo/company.html'));
 assert.doesNotMatch(current.contentMarkdown,/광명시 일직로 72|다피|DAPI/);assert(!current.sources.some(s=>s.url==='https://dapiofficial.co.kr/shopinfo/company.html'));
 const guard=fs.readFileSync(new URL('./direct-source.test.mjs',import.meta.url),'utf8');assert(guard.includes('assert.doesNotMatch(text,'));assert(!guard.includes('verified external return-address contrast'));
});
