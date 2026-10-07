import {dependencyDigest} from '../src/lib/manual-release-guard.mjs';
import {validateManualContract} from '../src/lib/manual-contract.mjs';
import fs from 'node:fs';import crypto from 'node:crypto';import assert from 'node:assert/strict';
import original from '../src/data/pages.json' with {type:'json'};import manual from '../src/data/manual-pages.json' with {type:'json'};import provenance from '../src/data/manual-provenance.json' with {type:'json'};import products from '../src/data/products.json' with {type:'json'};
import {validateGraph,loadGraph} from './qa_graph.mjs';import {validateCustomerIntent} from './qa_intent.mjs';import {pageSources} from '../src/lib/sources.mjs';import {selectProducts,productFamilies} from '../src/lib/catalog.mjs';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
validateGraph(loadGraph());
validateManualContract(manual,provenance,fs.readFileSync('src/data/manual-pages.json'),products,{catalogBytes:fs.readFileSync('src/data/products.json'),dependencyHash:dependencyDigest()});
for(const [file,expected] of Object.entries(provenance.immutableFiles))assert.equal(hash(fs.readFileSync(file)),expected,`Frozen file modified: ${file}`);
assert.equal(hash(fs.readFileSync('src/data/manual-pages.json')),provenance.contentHash,'Manual content hash drift');
const pages=[...original,...manual];for(const field of ['pageKey','url','slug','primaryKeyword'])assert.equal(new Set(pages.map(p=>p[field])).size,pages.length,`Duplicate ${field}`);
const keys=new Set(pages.map(p=>p.pageKey));
for(const p of manual){
 assert.equal(p.publicationMode,'manual-user-request');assert.equal(p.manualReleaseId,provenance.manualReleaseId);assert.equal(p.status,'manual-candidate');
 for(const forbidden of ['snapshotId','snapshotHash','approvalVerified','sourceRecordId','publishQueueRecordId'])assert.ok(!Object.hasOwn(p,forbidden),`Invented frozen approval ${p.pageKey}`);
 assert.equal(p.url,`/${p.category}/${p.slug}/`);assert.match(p.url,/^\/[a-z0-9-]+\/[a-z0-9-]+\/$/);
 assert.ok(p.title.startsWith(p.primaryKeyword));assert.ok(p.h1.includes(p.primaryKeyword.replace(/ 주문$| 확인$/,'')));assert.ok(p.firstAnswer.startsWith(p.primaryKeyword));
 for(const f of ['h1','description','cardSummary','firstAnswer','contentMarkdown','intentKey'])assert.ok(p[f]?.trim(),`Missing ${f}`);
 assert.ok(!p.cardSummary.startsWith(p.primaryKeyword));assert.ok(p.contentMarkdown.startsWith(p.firstAnswer));
 validateCustomerIntent(p,products);pageSources(p);assert.ok(p.sources.length);assert.equal(p.assetSlot,'REAL_PROOF');assert.ok(selectProducts(p,products).length);assert.ok(selectProducts(p,products).every(x=>productFamilies(p).includes(x.family)));
 for(const key of p.relatedKeys)assert.ok(keys.has(key)&&key!==p.pageKey);
}
console.log(JSON.stringify({status:'PASS',baselineDetails:original.length,manualCandidates:manual.length,contentHash:provenance.contentHash,independentReview:provenance.independentReview.status,productionReady:provenance.independentReview.status==='approved'}));
