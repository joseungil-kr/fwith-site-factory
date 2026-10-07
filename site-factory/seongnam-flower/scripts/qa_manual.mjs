import fs from 'node:fs';
import assert from 'node:assert/strict';
import pages,{manualPages,frozenPages,digest,hash,effectiveArchitecture,effectiveMap,effectiveManifest} from '../src/lib/all-pages.mjs';
import {validateCustomerIntent} from './qa_intent.mjs';
import {productFamilies,selectProducts} from '../src/lib/catalog.mjs';
const read=n=>JSON.parse(fs.readFileSync('src/data/'+n+'.json','utf8'));
const provenance=read('manual-provenance'),products=read('products');
assert.equal(manualPages.length,8);assert.equal(frozenPages.length,22);assert.equal(pages.length,30);
for(const [file,sha] of Object.entries(provenance.frozenFileHashes))assert.equal(hash(fs.readFileSync(file)),sha,'Original source changed: '+file);
for(const [file,sha] of Object.entries(provenance.scopeFileHashes))assert.equal(hash(fs.readFileSync(file)),sha,'Manual source scope changed: '+file);
assert.equal(digest(provenance.scopeFileHashes),provenance.scopeDigest);
assert.equal(hash(fs.readFileSync('src/data/manual-pages.json')),provenance.manualPagesSha256);
const routes=new Set(pages.map(p=>p.url)),keys=new Set(pages.map(p=>p.pageKey));
assert.equal(routes.size,30);assert.equal(keys.size,30);
const titles=new Set(pages.map(p=>p.title)),headings=new Set(pages.map(p=>p.h1));assert.equal(titles.size,30);assert.equal(headings.size,30);
const intents=new Set(effectiveArchitecture.pages.map(p=>p.intentKey));assert.equal(intents.size,30);
for(const p of manualPages){
 assert.equal(p.url,`/${p.category}/${p.slug}/`);assert(p.title.startsWith(p.primaryKeyword));assert(p.h1.includes(p.primaryKeyword));assert(p.firstAnswer.startsWith(p.primaryKeyword));
 assert(!p.cardSummary.startsWith(p.primaryKeyword));let prefix=0;while(p.title[prefix]&&p.title[prefix]===p.cardSummary[prefix])prefix++;assert(prefix<=8);
 assert.equal(p.reviewState,'pending-independent-review');assert.equal(p.titleAlignmentReview.score,null);
 assert(p.contentMarkdown.includes('tel:18440644'));assert(p.contentMarkdown.includes('https://fwith.co.kr'));
 assert(p.sources.length>=2&&p.sources.every(s=>s.url.startsWith('https://')&&s.verifiedAt));
 assert.equal(p.sources[0].url,p.source.url);assert.equal(p.queryClass,'local-commercial');
 assert(p.keywordCluster&&p.intentKey&&p.secondaryKeywords.length&&p.queryEvidence.sourceUrls.length);
 validateCustomerIntent(p,products);const families=productFamilies(p);assert(families.length&&selectProducts(p,products).length);assert(families.every(f=>['funeral','congrats'].includes(f)));
 for(const m of p.contentMarkdown.matchAll(/\]\((\/[^)]+)\)/g))assert(routes.has(m[1]),'Dead internal link '+m[1]);
 for(const collection of [effectiveArchitecture.pages,effectiveMap.pages,effectiveManifest.pages]){const row=collection.find(x=>x.pageKey===p.pageKey);assert(row&&row.contentSha256===p.contentSha256&&row.revisionId===p.revisionId&&row.url===p.url);}
}
const cov=read('manual-coverage');assert.equal(cov.completeLocalCoverageClaim,false);assert.equal(cov.legalNamesPreserved,44);assert.equal(read('region-coverage').units.length,44);assert.equal(read('region-policy').enabled,false);
console.log(JSON.stringify({manualIntegrity:'PASS',manual:8,frozenPreserved:22,routes:30,original44NameInventory:'preserved-no-completeness-claim',scopeDigest:provenance.scopeDigest,review:provenance.independentReview.status}));
