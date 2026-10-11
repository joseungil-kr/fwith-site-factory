import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {validateCustomerCopyRevision,collectBindings,productionRequested,validateManualContract,readReviewEvidence} from '../src/lib/manual-contract.mjs';
import {selectProducts,productFamilies} from '../src/lib/catalog.mjs';import {validateCustomerIntent} from '../scripts/qa_intent.mjs';
const read=f=>JSON.parse(fs.readFileSync(f));const revision=read('src/data/customer-copy-revision-20261011.json');
const history=read(revision.history.file),pages=[...read('src/data/pages.json'),...read('src/data/manual-pages.json')],products=read('src/data/products.json');
const oldPages=[...JSON.parse(history.files['src/data/pages.json'].text),...JSON.parse(history.files['src/data/manual-pages.json'].text)];
const copyFields=new Set(['title','h1','description','cardSummary','firstAnswer','contentMarkdown','sources','source','sections','faq',...revision.operationalFields]);
test('all reviewed source bytes and historical evidence are bound',()=>assert.equal(validateCustomerCopyRevision('.').articles.length,67));
for(const e of revision.articles)test(e.url+' exact reviewed copy, actual catalog selectors and protected identity',()=>{
 const p=pages.find(x=>x.pageKey===e.pageKey),old=oldPages.find(x=>x.pageKey===e.pageKey);assert(p&&old);
 for(const k of new Set([...Object.keys(p),...Object.keys(old)]))if(!copyFields.has(k))assert.deepEqual(p[k],old[k],k);
 assert.deepEqual(selectProducts(p,products,productFamilies(p).length>3?4:3).map(x=>x.key),e.actualProductKeys);assert(validateCustomerIntent(p,products));
 if(e.kind==='manual'){for(const k of ['snapshotId','snapshotHash','approvalVerified','sourceRecordId','publishQueueRecordId'])assert.equal(p[k],undefined);}else{assert.notEqual(p.snapshotId,old.snapshotId);assert.equal(p.parentSnapshotId,old.snapshotId);}
});
test('routes, original snapshot ledger and regional plan are preserved',()=>{
 assert.deepEqual(pages.map(x=>x.url),oldPages.map(x=>x.url));const m=read('src/data/publish-manifest.json'),old=JSON.parse(history.files['src/data/publish-manifest.json'].text);for(const [k,v]of Object.entries(old.snapshotLedger))assert.deepEqual(m.snapshotLedger[k],v);assert.equal(fs.readFileSync('src/data/region-coverage.json','utf8'),history.files['src/data/region-coverage.json'].text);
});
test('explicit in-memory pending fixture cannot authorize production',()=>{const p=structuredClone(read('src/data/manual-provenance.json'));p.independentReview={status:'pending'};assert(productionRequested({SITE_URL:'https://goyang.fwith.kr',SITE_INDEXABLE:'true'},{}));assert.throws(()=>validateManualContract(read('src/data/manual-pages.json'),p,fs.readFileSync('src/data/manual-pages.json'),products,{production:true,bindings:collectBindings('.')}),/pending/);});
test('persisted receipt state and all seven actual release bindings validate',()=>{const p=read('src/data/manual-provenance.json');assert.equal(p.writerId,'/root/integrate_reviewed_legacy_copy');assert.equal(p.expectedReviewerId,'/root');assert(['pending','approved'].includes(p.independentReview.status));const approved=p.independentReview.status==='approved';assert(validateManualContract(read('src/data/manual-pages.json'),p,fs.readFileSync('src/data/manual-pages.json'),products,{production:approved,bindings:collectBindings('.'),reviewEvidenceBytes:approved?readReviewEvidence('.'):null}));});
test('all original catalog facts except separately approved descriptions stay exact',()=>{const old=JSON.parse(history.files['src/data/products.json'].text);for(const p of products){const o=old.find(x=>x.key===p.key);for(const k of Object.keys(o))if(k!=='desc')assert.deepEqual(p[k],o[k],p.key+':'+k);}});
test('reviewed order narrative cannot hide arbitrary invalid address copy',()=>{const p=structuredClone(pages.find(x=>x.pageKey==='goyang-manual-goyang-flower-order'));p.firstAnswer='changed';assert.throws(()=>validateCustomerIntent(p,products),/Customer intent address/);});

test('approved narrative exception cannot carry to another release',()=>{const p=structuredClone(pages.find(x=>x.pageKey==='goyang-manual-goyang-flower-order'));p.manualReleaseId='different';assert.throws(()=>validateCustomerIntent(p,products),/Customer intent address/);});
