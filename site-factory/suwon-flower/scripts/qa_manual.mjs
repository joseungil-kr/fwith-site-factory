import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import pages,{frozenPages,manualPages,manualRevisions,digest} from '../src/lib/all-pages.mjs';
import {assertIndependentReview,assertScopeFiles} from '../src/lib/manual-review-contract.mjs';
import {validateCustomerIntent} from './qa_intent.mjs';
import {productFamilies,selectProducts} from '../src/lib/catalog.mjs';
const read=n=>JSON.parse(fs.readFileSync('src/data/'+n+'.json','utf8'));
const provenance=read('manual-provenance'),products=read('products');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
for(const [file,expected] of Object.entries(provenance.frozenFileHashes))assert.equal(hash(fs.readFileSync('src/data/'+file)),expected,'Frozen file modified: '+file);
assert.equal(hash(fs.readFileSync('src/data/manual-pages.json')),provenance.manualPagesSha256);
assert.equal(hash(fs.readFileSync('src/data/manual-revisions.json')),provenance.manualRevisionsSha256);
// The exact reviewed scope includes content, originals, renderer, tests, catalog and all retained assets.
assertScopeFiles(provenance.scopeFileHashes,file=>hash(fs.readFileSync(file)));
assert.equal(digest(provenance.scopeFileHashes),provenance.scopeDigest,'Scope digest mismatch');
if(process.env.SITE_INDEXABLE==='true'){
 const review=provenance.independentReview;
 assert(typeof review.evidencePath==='string' && /^reviews\/[a-z0-9-]+\.json$/.test(review.evidencePath),'Missing actual independent evidence');
 const bytes=fs.readFileSync(review.evidencePath);assertIndependentReview(provenance,JSON.parse(bytes),hash(bytes));
}
const routes=new Set(pages.map(p=>p.url)),keys=new Set(pages.map(p=>p.pageKey));
assert.equal(routes.size,pages.length);assert.equal(keys.size,pages.length);
const coverage=read('manual-coverage');
const expectedDongs=coverage.legalDongs;
assert.equal(coverage.completeLocalCoverageClaim,false);
assert.equal(coverage.ledger.length,56);assert.equal(new Set(expectedDongs).size,56);
assert.deepEqual(coverage.ledger.map(r=>r.legalDong).sort(),expectedDongs.slice().sort());
assert(coverage.ledger.every(r=>r.completeLocalIntent===false && routes.has(r.route)),'Residual coverage overclaimed');
const legal=new Set(expectedDongs);
const titleSet=new Set(),h1Set=new Set(),cards=new Set(),bodySet=new Set();
for(const p of manualPages){
 assert.equal(p.url,`/${p.category}/${p.slug}/`);assert(/^\/[a-z0-9-]+\/[a-z0-9-]+\/$/.test(p.url));
 for(const k of ['title','h1','description','cardSummary','firstAnswer','primaryKeyword','contentRevision'])assert(p[k],k+' absent');
 assert(p.title.startsWith(p.primaryKeyword));assert.equal(p.h1,p.primaryKeyword);
 assert(!p.cardSummary.startsWith(p.primaryKeyword));
 assert(!titleSet.has(p.title)&&!h1Set.has(p.h1)&&!cards.has(p.cardSummary),'Duplicate manual metadata');titleSet.add(p.title);h1Set.add(p.h1);cards.add(p.cardSummary);
 assert(p.sections.length>=3 && p.sections.every(s=>s.length===2&&s[0]&&s[1].length>=50));
 assert(p.firstAnswer.length>=100 && p.firstAnswer.length<=220);
 assert(['core-commercial','commercial-modifier','work-commercial','local-commercial','support-info'].includes(p.queryClass));
 assert(p.secondaryKeywords.length && p.keywordCluster && p.queryPriority && p.queryEvidence.sourceUrls.length);
 assert(p.titleAlignmentReview.rubric.keywordAtTitleStart && p.titleAlignmentReview.rubric.exactH1 && p.titleAlignmentReview.rubric.keywordAtAnswerStart);
 assert(p.source?.url.startsWith('https://')&&p.source.verifiedAt==='2026-10-07');
 assert(p.sources.every(s=>s.url.startsWith('https://')&&s.verifiedAt));
 for(const section of p.sections){assert(!bodySet.has(section[1]),'Repeated full manual body section');bodySet.add(section[1]);}
 validateCustomerIntent(p,products);
 const fam=productFamilies(p),selected=selectProducts(p,products,4);assert(fam.length&&selected.length);assert(selected.every(x=>fam.includes(x.family)));
 for(const k of p.relatedKeys||[])assert(keys.has(k)&&k!==p.pageKey);
 for(const s of p.sections)for(const m of s[1].matchAll(/\]\((\/[^)]+)\)/g))assert(routes.has(m[1]),'Broken authored link '+m[1]);
 assert.equal(provenance.pages.find(r=>r.pageKey===p.pageKey)?.contentRevision,p.contentRevision);
 const canonicalPage={...p};delete canonicalPage.contentRevision;assert.equal(p.contentRevision,'manual-'+digest(canonicalPage).slice(0,16),'Stale page revision');
}
for(const r of manualRevisions){
 const original=frozenPages.find(p=>p.pageKey===r.pageKey);assert(original);
 assert.equal(digest(original),r.baseContentSha256);assert.equal(digest(r.sectionsToAppend),r.sectionsSha256);
 assert(r.sectionsToAppend.every(s=>s.length===2&&s[0]&&s[1]));assert(!('snapshotId' in r));
}
if(process.argv.includes('--rendered')){
 const site=(process.env.SITE_URL||'https://suwon.fwith.kr').replace(/\/$/,'');
 for(const p of manualPages){const html=fs.readFileSync('dist'+p.url+'index.html','utf8');assert(html.includes('data-content-revision="'+p.contentRevision+'"'));assert(html.includes('data-manual-release="'+p.manualReleaseId+'"'));assert(!html.includes('data-snapshot-id='),'New manual page falsely claims frozen snapshot');assert.equal((html.match(/<h1\b/g)||[]).length,1);assert(html.includes(p.h1));assert(html.includes('tel:18440644'));assert(html.includes('https://fwith.co.kr/shop/item.php?it_id='));}
 for(const r of manualRevisions){const html=fs.readFileSync('dist'+r.url+'index.html','utf8');assert(html.includes('data-manual-revision="'+r.revisionId+'"'));assert(html.includes('data-addendum-digest="'+r.sectionsSha256+'"'));for(const s of r.sectionsToAppend)assert(html.includes(s[0]));}
 const htmlFiles=fs.readdirSync('dist',{recursive:true}).filter(p=>p.endsWith('index.html'));const expected=['/',...pages.map(p=>p.url),...new Set(pages.map(p=>'/'+p.category+'/'))];assert.equal(htmlFiles.length,expected.length);
}
console.log('MANUAL QA PASSED',JSON.stringify({newPages:manualPages.length,addenda:manualRevisions.length,legalDongs:legal.size,review:provenance.independentReview.status,rendered:process.argv.includes('--rendered')}));
