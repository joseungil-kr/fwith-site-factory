import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {effectiveManifest,manual,validateArticleProductSelections,getArticleProductSelection} from '../src/lib/manual-source.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
const json=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const cfg=json('../src/data/article-product-selection.json');
const catalog=json('../src/data/products.json');
const authors=json('fixtures/reviewed-copy.json');
const authorDecisions=json('fixtures/reviewed-card-decisions.json');
const read=p=>fs.readFileSync(path.join(root,'..',p));
const run=(c=structuredClone(cfg),pages=effectiveManifest.pages,products=catalog,reader=read)=>validateArticleProductSelections(c,pages,products,manual.pages.map(p=>p.pageKey),reader);
for(const a of authors) test(`exact approved article/products/date/route: ${a.url}`,()=>{
 const k=a.metadata.pageKey,row=getArticleProductSelection(k,a.metadata.category),review=authorDecisions.find(r=>r.pageKey===k);
 assert.deepEqual(row.productKeys,review.productMentionKeys);assert.equal(row.url,a.url);assert.equal(row.sourceFile,a.sourceFile);assert.equal(row.verifiedAt,a.metadata.verifiedAt);
 assert.deepEqual(row.products.map(p=>p.productKey),review.productMentionKeys);
 for(const p of row.products) assert.deepEqual(p,catalog.find(x=>x.productKey===p.productKey));
 assert.equal(row.mode,review.productMentionKeys.length?'catalog':'consultation');
});
const negatives={
 'missing page':c=>c.pages.pop(),
 'extra page':c=>c.pages.push(structuredClone(c.pages[0])),
 'duplicate page':c=>c.pages[1]=structuredClone(c.pages[0]),
 'unknown page':c=>c.pages[0].pageKey='unregistered',
 'unknown top field':c=>c.fallback='congrats',
 'unknown row field':c=>c.pages[0].quota=4,
 'missing row field':c=>delete c.pages[0].mode,
 'wrong site':c=>c.siteKey='gangbuk-flower',
 'wrong schema':c=>c.schemaVersion=2,
 'invalid author digest':c=>c.reviewedArticlesSha256='PASS',
 'route changed':c=>c.pages[0].url='/order/fake/',
 'category changed':c=>c.pages[0].category='funeral',
 'renderer boundary changed':c=>c.pages[0].rendererType='legacy',
 'source traversal':c=>c.pages[0].sourceFile='src/content/manual/../secret.md',
 'source encoded traversal':c=>c.pages[0].sourceFile='src/content/manual/%2e%2e/secret.md',
 'source hash changed':c=>c.pages[0].contentSha256='0'.repeat(64),
 'date refresh invented':c=>c.pages[0].verifiedAt='2026-10-11',
 'date malformed':c=>c.pages[0].verifiedAt='later',
 'unknown product':c=>c.pages[0].productKeys=['fake'],
 'duplicate product':c=>c.pages[0].productKeys.push(c.pages[0].productKeys[0]),
 'zero cards declared catalog':c=>c.pages[0].productKeys=[],
 'catalog declared consultation':c=>c.pages[0].mode='consultation',
 'fallback mode':c=>c.pages[0].mode='automatic',
 'business uses condolence':c=>c.pages.find(r=>r.category==='business').productKeys=['funeral-basic'],
 'funeral uses congratulations':c=>c.pages.find(r=>r.category==='funeral').productKeys=['congrats-basic'],
 'event uses condolence':c=>c.pages.find(r=>r.category==='event'&&r.mode==='catalog').productKeys=['funeral-basic'],
 'school forced wreath':c=>Object.assign(c.pages.find(r=>r.category==='school'),{mode:'catalog',productKeys:['congrats-basic']}),
 'personal gift forced wreath':c=>Object.assign(c.pages.find(r=>r.category==='gift'),{mode:'catalog',productKeys:['congrats-basic']})
};
for(const [name,mutate] of Object.entries(negatives))test(`fail closed: ${name}`,()=>{const c=structuredClone(cfg);mutate(c);assert.throws(()=>run(c),/ARTICLE_PRODUCT_SELECTION_BLOCKED/);});
test('full config valid',()=>assert.equal(run(),true));
test('changed source bytes blocked',()=>assert.throws(()=>run(structuredClone(cfg),effectiveManifest.pages,catalog,p=>Buffer.concat([read(p),Buffer.from('tamper')])),/article bytes changed/));
test('catalog duplicate blocked',()=>assert.throws(()=>run(structuredClone(cfg),effectiveManifest.pages,[...catalog,catalog[0]]),/duplicate catalog/));
test('bad price blocked',()=>{const c=structuredClone(catalog);c[0].price=0;assert.throws(()=>run(structuredClone(cfg),effectiveManifest.pages,c),/asset or price/);});
test('bad image path blocked',()=>{const c=structuredClone(catalog);c[0].image='https://unregistered.invalid/a.jpg';assert.throws(()=>run(structuredClone(cfg),effectiveManifest.pages,c),/asset or price/);});
test('unknown requested key blocked',()=>assert.throws(()=>getArticleProductSelection('nope','funeral'),/unknown requested article/));
test('wrong requested category blocked',()=>assert.throws(()=>getArticleProductSelection(cfg.pages[0].pageKey,'funeral'),/unknown requested article/));
test('returned data cannot mutate catalog or map',()=>{const a=cfg.pages.find(r=>r.productKeys.length);const s=getArticleProductSelection(a.pageKey,a.category);s.products[0].price=0;s.productKeys.length=0;assert.deepEqual(getArticleProductSelection(a.pageKey,a.category).productKeys,a.productKeys);assert.ok(getArticleProductSelection(a.pageKey,a.category).products[0].price>0);});
test('40 exact unique URLs; 15 manual / 25 legacy; 2/4/8/consultation distribution',()=>{
 assert.equal(new Set(cfg.pages.map(p=>p.url)).size,40);assert.equal(cfg.pages.filter(p=>p.rendererType==='manual').length,15);assert.equal(cfg.pages.filter(p=>p.rendererType==='legacy').length,25);
 assert.deepEqual(cfg.pages.reduce((o,p)=>(o[p.productKeys.length]=(o[p.productKeys.length]||0)+1,o),{}),{'0':11,'2':18,'4':10,'8':1});
});
test('original six runtime hashes retained; explicit reviewed identity and visual-only deferral changes reversible',()=>{
 for(const f of ['src/lib/manual-release-gate.mjs','src/lib/display-articles.mjs','src/lib/regions.mjs','src/lib/regional-runtime.mjs','src/content.config.ts','src/pages/[category]/[slug].astro']){
  let bytes=read(f);
  if(f==='src/lib/manual-release-gate.mjs'){
   assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),'a2f031eecdec924461bc5b6b42a526813082cda8963d620b396fe8990c4748ea');
   let text=bytes.toString();
   assert.equal(text.split("export const assignedWriter='/root/audit_regional_sales_copy';").length-1,1);text=text.replace("export const assignedWriter='/root/audit_regional_sales_copy';","export const assignedWriter='bf80b5b2-7a03-4e58-8ec1-0f855389ba48';");
   assert.equal(text.split("export const assignedReviewer='/root';").length-1,1);text=text.replace("export const assignedReviewer='/root';","export const assignedReviewer='supplement-guide-review-89bc7a8013c04401';");
   assert.equal(text.split("'src/data/manual-supplemental-review-20261007.json','src/data/manual-integrated-review-20261011.json'].includes(rel)").length-1,1);text=text.replace("'src/data/manual-supplemental-review-20261007.json','src/data/manual-integrated-review-20261011.json'].includes(rel)","'src/data/manual-supplemental-review-20261007.json'].includes(rel)");
   assert.equal(text.split("path.join(root,'src/data/manual-integrated-review-20261011.json')").length-1,1);text=text.replace("path.join(root,'src/data/manual-integrated-review-20261011.json')","path.join(root,'src/data/manual-supplemental-review-20261007.json')");
   assert.equal(text.split(" const seen=new Set(),deferredVisualKeys=[];\n for(const row of review.evidence.pages){\n  if(!manualKeys.includes(row.pageKey)||seen.has(row.pageKey)||row.decision!=='pass')throw Error('MANUAL_RELEASE_BLOCKED: invalid reviewed page');seen.add(row.pageKey);\n  for(const criterion of requiredCriteria){\n   if(row.criteria?.[criterion]==='pass')continue;\n   if(criterion==='mobileAndDesktopVisual'&&row.criteria?.[criterion]==='DEFERRED_NOT_PASS'){deferredVisualKeys.push(row.pageKey);continue;}\n   throw Error('MANUAL_RELEASE_BLOCKED: '+criterion+' not passed');\n  }\n }\n if(deferredVisualKeys.length){\n  const d=review.evidence.visualDeferral;\n  if(d?.status!=='DEFERRED_NOT_PASS'||d.criterion!=='mobileAndDesktopVisual'||d.authorization!=='user-requested-batch-deferral'||d.noVisualPassClaim!==true)throw Error('MANUAL_RELEASE_BLOCKED: explicit visual-only deferral missing');\n  if(typeof d.authorizationReference!=='string'||!d.authorizationReference.trim()||typeof d.reason!=='string'||!d.reason.trim())throw Error('MANUAL_RELEASE_BLOCKED: visual deferral authorization/reason missing');\n  if(!Array.isArray(d.pendingChecks)||JSON.stringify([...d.pendingChecks].sort())!==JSON.stringify(['desktop-actual-screen','narrow-actual-screen']))throw Error('MANUAL_RELEASE_BLOCKED: both actual-screen follow-ups required');\n  if(!Array.isArray(d.pendingPageKeys)||JSON.stringify([...d.pendingPageKeys].sort())!==JSON.stringify([...deferredVisualKeys].sort()))throw Error('MANUAL_RELEASE_BLOCKED: visual deferral page coverage differs');\n }else if(review.evidence.visualDeferral!=null)throw Error('MANUAL_RELEASE_BLOCKED: stale visual deferral without deferred pages');").length-1,1);text=text.replace(" const seen=new Set(),deferredVisualKeys=[];\n for(const row of review.evidence.pages){\n  if(!manualKeys.includes(row.pageKey)||seen.has(row.pageKey)||row.decision!=='pass')throw Error('MANUAL_RELEASE_BLOCKED: invalid reviewed page');seen.add(row.pageKey);\n  for(const criterion of requiredCriteria){\n   if(row.criteria?.[criterion]==='pass')continue;\n   if(criterion==='mobileAndDesktopVisual'&&row.criteria?.[criterion]==='DEFERRED_NOT_PASS'){deferredVisualKeys.push(row.pageKey);continue;}\n   throw Error('MANUAL_RELEASE_BLOCKED: '+criterion+' not passed');\n  }\n }\n if(deferredVisualKeys.length){\n  const d=review.evidence.visualDeferral;\n  if(d?.status!=='DEFERRED_NOT_PASS'||d.criterion!=='mobileAndDesktopVisual'||d.authorization!=='user-requested-batch-deferral'||d.noVisualPassClaim!==true)throw Error('MANUAL_RELEASE_BLOCKED: explicit visual-only deferral missing');\n  if(typeof d.authorizationReference!=='string'||!d.authorizationReference.trim()||typeof d.reason!=='string'||!d.reason.trim())throw Error('MANUAL_RELEASE_BLOCKED: visual deferral authorization/reason missing');\n  if(!Array.isArray(d.pendingChecks)||JSON.stringify([...d.pendingChecks].sort())!==JSON.stringify(['desktop-actual-screen','narrow-actual-screen']))throw Error('MANUAL_RELEASE_BLOCKED: both actual-screen follow-ups required');\n  if(!Array.isArray(d.pendingPageKeys)||JSON.stringify([...d.pendingPageKeys].sort())!==JSON.stringify([...deferredVisualKeys].sort()))throw Error('MANUAL_RELEASE_BLOCKED: visual deferral page coverage differs');\n }else if(review.evidence.visualDeferral!=null)throw Error('MANUAL_RELEASE_BLOCKED: stale visual deferral without deferred pages');"," const seen=new Set();for(const row of review.evidence.pages){if(!manualKeys.includes(row.pageKey)||seen.has(row.pageKey)||row.decision!=='pass')throw Error('MANUAL_RELEASE_BLOCKED: invalid reviewed page');seen.add(row.pageKey);for(const criterion of requiredCriteria)if(row.criteria?.[criterion]!=='pass')throw Error('MANUAL_RELEASE_BLOCKED: '+criterion+' not passed');}");
   assert.equal(text.split(" return {mode:'production',releaseApproved:true,visualQa:review.evidence.pages.some(row=>row.criteria.mobileAndDesktopVisual==='DEFERRED_NOT_PASS')?'DEFERRED_NOT_PASS':'PASS'};").length-1,1);text=text.replace(" return {mode:'production',releaseApproved:true,visualQa:review.evidence.pages.some(row=>row.criteria.mobileAndDesktopVisual==='DEFERRED_NOT_PASS')?'DEFERRED_NOT_PASS':'PASS'};"," return {mode:'production',releaseApproved:true};");
   bytes=Buffer.from(text);
  }
  assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),json('fixtures/protected-runtime.json')[f]);
 }
 const original=fs.readFileSync(path.join(root,'fixtures/manual-source-original.mjs.txt'),'utf8');assert.ok(read('src/lib/manual-source.mjs').toString().startsWith(original));
 const layout=read('src/layouts/ArticleLayout.astro').toString();assert.ok(layout.includes('data-manual-revision={manualEntry?.revisionId}'));assert.ok(layout.includes('data-snapshot-id={manualEntry?undefined:snapshotId}'));assert.ok(layout.includes('data-original-snapshot={manualEntry?.supersedesSnapshotId}'));assert.ok(layout.includes('removeRepeatedOpeningParagraph'));assert.ok(layout.includes('<ManualProductCards pageKey={pageKey} category={category} />'));
});
test('unchanged production artifact-digest gate rejects later selection edits',async()=>{
 const {validateReview,assignedWriter,assignedReviewer,releaseOrigin,requiredCriteria}=await import('../src/lib/manual-release-gate.mjs');
 // Synthetic unit fixture, never a production approval file.
 const evidence={pages:manual.pages.map(p=>({pageKey:p.pageKey,decision:'pass',criteria:Object.fromEntries(requiredCriteria.map(k=>[k,'pass']))}))};
 const fixture={schemaVersion:1,decision:'pass',releaseOrigin,artifactDigest:'a'.repeat(64),writerLabel:assignedWriter,reviewerLabel:assignedReviewer,reviewedAt:'2026-10-11T00:00:00Z',evidence,evidenceSha256:crypto.createHash('sha256').update(JSON.stringify(evidence)).digest('hex')};
 assert.equal(validateReview(fixture,'a'.repeat(64),manual.pages.map(p=>p.pageKey)),true);
 assert.throws(()=>validateReview(fixture,'b'.repeat(64),manual.pages.map(p=>p.pageKey)),/reviewed artifact digest differs/);
});

test('approved copy and selection decisions have immutable review-input SHA pins',()=>{
 const digest=p=>crypto.createHash('sha256').update(fs.readFileSync(path.join(root,p))).digest('hex');
 assert.equal(digest('fixtures/reviewed-copy.json'),'45d95f772496ee2cd0e9a4e0f1ab24fdc14b7a240bfe609f35f722faf9b1b83b');
 assert.equal(digest('fixtures/reviewed-card-decisions.json'),'374003ec27897cc135c07872d4119e8f350d9aef497fbc6fe2a62be3fb1c8e19');
});

test('source hash reader remains rooted at the npm project after Astro relocates the bundle',()=>{
 const source=read('src/lib/manual-source.mjs').toString();
 assert.ok(source.includes('const contentRoot = process.cwd();'));
 assert.ok(source.includes('fs.readFileSync(path.resolve(contentRoot,file))'));
 assert.ok(!source.includes("new URL('../../', import.meta.url)"));
 assert.equal(run(),true);
});
