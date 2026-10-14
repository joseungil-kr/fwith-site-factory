import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';import {spawnSync} from 'node:child_process';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const encoded=x=>JSON.stringify(x,null,2)+'\n';
const amendmentPath='src/data/seocho-corrections/floor-20261013/amendment.json';
const amendment=read(amendmentPath),runtimeBytes=fs.readFileSync('src/data/seocho-copy.json','utf8'),runtime=JSON.parse(runtimeBytes);
const historical={articles:read(amendment.originalArticle.path).articles,common:read(amendment.originalCommon.path).common};
test('floor correction changes exactly two named fields and no other customer-copy bytes',()=>{
 const before=encoded(historical);assert.equal(sha(before),amendment.previousRuntimeCopySha256);assert.equal(sha(runtimeBytes),amendment.correctedRuntimeCopySha256);
 assert.equal(before.split(amendment.oldSentence).length-1,2);assert.equal(runtimeBytes.split(amendment.newSentence).length-1,2);
 assert.equal(runtimeBytes,before.replaceAll(amendment.oldSentence,amendment.newSentence));
 const expected=structuredClone(historical);const article=expected.articles.find(x=>x.id==='funeral');const section=article.sections.find(x=>x.id==='seoul-st-mary-funeral');
 section.paragraphs[0]=section.paragraphs[0].replace(amendment.oldSentence,amendment.newSentence);article.contentMarkdown=article.contentMarkdown.replace(amendment.oldSentence,amendment.newSentence);
 assert.deepEqual(runtime,expected);assert.deepEqual(runtime.common,historical.common);assert.deepEqual(runtime.articles[1],historical.articles[1]);
});
test('floor correction has sealed evidence and remains explicitly pending independent review',()=>{
 const run=spawnSync('python3',['scripts/seocho_floor_correction.py'],{encoding:'utf8'});assert.equal(run.status,0,run.stdout+run.stderr);
 const release=read('src/data/publish-manifest.json').directRelease;assert.equal(release.reviewStatus,'COPY_CORRECTION_PENDING_INDEPENDENT_REVIEW');
 assert.deepEqual(release.copyCorrection,{id:amendment.id,amendmentSha256:sha(fs.readFileSync(amendmentPath)),runtimeCopySha256:sha(runtimeBytes),status:amendment.status});
 assert.equal(release.publicationAuthorized,false);
});
test('floor correction runtime projections carry the exact corrected content hash',()=>{
 const pages=read('src/data/pages.json'),release=read('src/data/publish-manifest.json').directRelease;
 for(let i=0;i<pages.length;i++){
  assert.deepEqual(pages[i].sections,runtime.articles[i].sections);assert.equal(pages[i].contentMarkdown,runtime.articles[i].contentMarkdown);
  assert.equal(release.contentHashes[i].bodySha256,sha(runtime.articles[i].contentMarkdown));
 }
});
