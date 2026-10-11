import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';
const root=new URL('../',import.meta.url);const text=p=>fs.readFileSync(new URL(p,root),'utf8');const read=p=>JSON.parse(text(p));const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const rows=read('tests/fixtures/approved-article-bindings.json');
for(const row of rows)test(`reviewed copy preserved except new identity: ${row.pageKey}`,()=>{
 const content=text(row.file),pattern=new RegExp('^'+row.identityField+':.*$','m');assert.equal(sha(content),row.preparedFileSha256);assert.equal(sha(content.replace(pattern,row.originalIdentityLine)),row.approvedFileSha256);assert.ok(content.includes(row.afterId));
 if(row.identityField==='revisionId'){
  for(const n of ['manual-pages','manual-page-map','manual-intents']){const p=read('src/data/'+n+'.json').pages.find(p=>p.pageKey===row.pageKey);assert.equal(p.revisionId,row.afterId);assert.equal(p.contentSha256,row.preparedFileSha256);}
  assert.doesNotMatch(content,/^draftStatus:/m);
 }else for(const n of ['publish-manifest','page-map']){const p=read('src/data/'+n+'.json').pages.find(p=>p.pageKey===row.pageKey);assert.equal(p.snapshotId,row.afterId);assert.equal(p.contentSha256,row.preparedFileSha256);}
 const selection=read('src/data/article-product-selection.json').pages.find(p=>p.pageKey===row.pageKey);assert.equal(selection.contentSha256,row.preparedFileSha256);
});
test('integrated receipt remains exact-bound; pending fixture always blocks and real status is validated conditionally',async()=>{
 const {assertManualProductionReady,artifactDigest,validateReview}=await import('../src/lib/manual-release-gate.mjs');const review=read('src/data/manual-integrated-review-20261011.json'),keys=read('src/data/manual-pages.json').pages.map(p=>p.pageKey);assert.equal(review.artifactDigest,artifactDigest());
 // In-memory negative fixture only. A real independently issued PASS receipt is not forced back to pending.
 assert.throws(()=>validateReview({...structuredClone(review),decision:'pending'},artifactDigest(),keys),/independent PASS missing/);
 assert.ok(['pending','pass'].includes(review.decision));
 const old={SITE_URL:process.env.SITE_URL,SITE_INDEXABLE:process.env.SITE_INDEXABLE};try{process.env.SITE_URL='https://yongin.fwith.kr';process.env.SITE_INDEXABLE='true';
  if(review.decision==='pass'){assert.equal(validateReview(review,artifactDigest(),keys),true);const result=assertManualProductionReady();assert.equal(result.releaseApproved,true);assert.equal(result.visualQa,review.evidence.pages.some(p=>p.criteria.mobileAndDesktopVisual==='DEFERRED_NOT_PASS')?'DEFERRED_NOT_PASS':'PASS');}
  else{assert.equal(review.reviewedAt,null);assert.throws(()=>assertManualProductionReady(),/independent PASS missing/);}
 }finally{for(const [k,v] of Object.entries(old))if(v===undefined)delete process.env[k];else process.env[k]=v;}
});
