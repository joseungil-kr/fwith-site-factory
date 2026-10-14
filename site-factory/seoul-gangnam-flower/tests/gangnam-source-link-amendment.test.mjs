/** Exact minimized-evidence successor tests. Old full-document validation remains fail-closed. */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {projectRoot,sha,canonical,loadGangnamInputs,projectGangnamRuntime,inputPins} from '../scripts/generate_gangnam_runtime.mjs';
import {sourceAmendmentFile,sourceAmendmentSha256,sourceSelectionFile,sourceSelectionSha256,loadGangnamCurrentInputs,validateGangnamCurrentEvidence,projectGangnamCurrentRuntime,verifyGangnamCurrentRuntime,regenerateGangnamCurrentRuntime} from '../scripts/generate_gangnam_minimized_source.mjs';
import {loadGangnamCurrentInputs as loadHistoricalFullEvidence} from '../scripts/generate_gangnam_current_source.mjs';
const oldUrl='https://setec.or.kr/resources/front/files/01_SETEC.pdf';
const newUrl='https://www.setec.or.kr/resources/front/files/2025_SETEC.pdf';
const extract='extracts/article43-page13.txt';
const omitted=['raw/setec-current-linked-operations.pdf','text/setec-current-linked-operations.txt'];
const clone=structuredClone;
const read=file=>JSON.parse(fs.readFileSync(path.join(projectRoot,file),'utf8'));
const baseline=projectGangnamRuntime(loadGangnamInputs());
const current=projectGangnamCurrentRuntime();
const json=value=>JSON.stringify(value,null,2)+'\n';
const actual=()=>Object.fromEntries(Object.keys(current).map(name=>[name,read('src/data/'+name+'.json')]));
function differences(before,after,pointer=''){
 if(canonical(before)===canonical(after))return [];
 if(!before||!after||typeof before!=='object'||typeof after!=='object')return [pointer];
 return [...new Set([...Object.keys(before),...Object.keys(after)])].flatMap(key=>differences(before[key],after[key],pointer+'/'+key));
}
function badOutput(mutate){const changed=clone(current);mutate(changed);assert.throws(()=>verifyGangnamCurrentRuntime(changed,current),/runtime (projection|output set) drift/);}

test('SETEC minimized evidence binds the active contract, historical seals and all eleven artifacts',()=>{
 const inputs=loadGangnamCurrentInputs();
 assert.equal(sha(fs.readFileSync(path.join(projectRoot,sourceAmendmentFile))),sourceAmendmentSha256);
 assert.equal(sha(fs.readFileSync(path.join(projectRoot,sourceSelectionFile))),sourceSelectionSha256);
 assert.equal(validateGangnamCurrentEvidence(inputs).evidenceMode,'bounded-extracts-no-full-document');
 assert.equal(inputs.historicalAmendment.newUrl,newUrl);
 assert.equal(inputs.selection.files.length,11);
 for(const entry of inputs.selection.files){assert.equal(inputs.evidence[entry.path].length,entry.bytes);assert.equal(sha(inputs.evidence[entry.path]),entry.sha256);}
 assert.equal(inputs.amendment.fullDocumentIncluded,false);
 assert.equal(inputs.amendment.fullDocumentBytesVerifiedByCandidate,false);
 for(const name of omitted)assert.equal(fs.existsSync(path.join(projectRoot,'src/data/gangnam-current-facts',name)),false);
 assert.equal(sha(json(current['gangnam-copy'])),'b442c6ab713453dc4651ea27f1586f777cd5f9915c5b9dd932d6f09da761990b');
 assert.equal(inputs.amendment.originalResearch331Recovered,false);
});

test('SETEC successor changes exactly one customer JSON pointer and keeps every sentence and 2024 date',()=>{
 assert.deepEqual(differences(baseline['gangnam-copy'],current['gangnam-copy']),['/articles/2/sourceLinks/3/url']);
 assert.equal(baseline['gangnam-copy'].articles[2].sourceLinks[3].url,oldUrl);
 assert.equal(current['gangnam-copy'].articles[2].sourceLinks[3].url,newUrl);
 const restored=clone(current['gangnam-copy']);restored.articles[2].sourceLinks[3].url=oldUrl;
 assert.deepEqual(restored,baseline['gangnam-copy']);
 assert.equal(sha(json(restored)),'893978677953deab30d9343b0dee00c0670dde668d8d53054252f1f0d034a816');
 assert.match(current['gangnam-copy'].articles[2].sections[3].paragraphs[1],/2024년 10월 운영요령/);
 assert.match(current['gangnam-copy'].articles[2].sourceNote,/2024년 10월 운영요령/);
});

test('SETEC event-only snapshot uses the original algorithm and preserves both unaffected page snapshots',()=>{
 const page=current.pages[2];
 for(const index of [0,1])assert.deepEqual(current.pages[index],baseline.pages[index]);
 assert.deepEqual(current['gangnam-a04-metadata'],baseline['gangnam-a04-metadata']);
 assert.deepEqual(current['gangnam-ui-copy'],baseline['gangnam-ui-copy']);
 assert.deepEqual(page.a04,baseline.pages[2].a04);
 assert.deepEqual(page.a04InputBinding,baseline.pages[2].a04InputBinding);
 assert.notEqual(page.snapshotHash,baseline.pages[2].snapshotHash);
 assert.equal(page.snapshotHash,'5e7772b74360af58d35b28bba5ee74e860e09f4ea38a9fb49389a9765b4ba2e2');
 const omit=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);
 assert.equal(page.snapshotHash,sha(canonical(Object.fromEntries(Object.entries(page).filter(([key])=>!omit.has(key))))));
 assert.equal(page.snapshotId,'local-content-gangnam-event-wreath-'+page.snapshotHash.slice(0,16));
 assert.equal(page.sources[3].url,newUrl);
 const restored=clone(page);delete restored.currentSourceBinding;
 restored.sourceLinks[3].url=oldUrl;restored.sources[3].url=oldUrl;
 restored.snapshotHash=baseline.pages[2].snapshotHash;restored.snapshotId=baseline.pages[2].snapshotId;
 assert.deepEqual(restored,baseline.pages[2]);
 for(const [name,expected] of Object.entries(inputPins))assert.equal(sha(fs.readFileSync(path.join(projectRoot,'src/data',name+'.json'))),expected,name);
});

test('SETEC event source binding propagates exactly to architecture, page map, manifest and checkpoint',()=>{
 const page=current.pages[2];
 const record=clone(page);for(const field of ['sections','contentMarkdown','faq','uniqueBodyText'])delete record[field];
 for(const name of ['page-map','publish-manifest'])assert.deepEqual(current[name].pages[2],record,name);
 assert.deepEqual(current.architecture.pages[2],{...record,status:'primary',pageRole:'REGION_SERVICE_LANDING',parentHub:'/regions/',contentRole:'question-answer',localizationPolicy:'local-required',sitemapIndexable:true});
 for(const name of ['architecture','page-map','publish-manifest'])for(const index of [0,1])assert.deepEqual(current[name].pages[index],baseline[name].pages[index]);
 assert.deepEqual(current['publish-manifest'].directRelease.currentSourceBinding,page.currentSourceBinding);
 assert.deepEqual(current['direct-checkpoint'].currentSourceBinding,page.currentSourceBinding);
 assert.equal(page.currentSourceBinding.amendmentSha256,sourceAmendmentSha256);
 assert.equal(page.currentSourceBinding.evidenceSelectionSha256,sourceSelectionSha256);
 assert.deepEqual(current['publish-manifest'].directRelease.contentHashes[2],{pageKey:page.pageKey,bodySha256:baseline['publish-manifest'].directRelease.contentHashes[2].bodySha256,publicSourceSha256:page.snapshotHash});
 for(const name of ['pages','architecture','page-map','publish-manifest']){
  const pages=name==='pages'?current.pages:current[name].pages;
  assert.ok(!Object.hasOwn(pages[0],'currentSourceBinding'));assert.ok(!Object.hasOwn(pages[1],'currentSourceBinding'));
 }
});

test('SETEC amendment rejects wrong URLs, a second pointer, date/prose edits and false approval',()=>{
 const mutations=[
  v=>v.amendment.newUrl=oldUrl,
  v=>v.amendment.newUrl='https://example.com/2025_SETEC.pdf',
  v=>v.amendment.oldUrl=newUrl,
  v=>v.amendment.effectiveCopyJsonPointer='/articles/2/sourceLinks/2/url',
  v=>v.amendment.secondUrl=newUrl,
  v=>v.amendment.articleId='wedding',
  v=>v.amendment.bodySentencesChanged=1,
  v=>v.amendment.dateTextChanged=true,
  v=>v.amendment.publishedCoverDate='2025.10',
  v=>v.amendment.newPdfSha256='0'.repeat(64),
  v=>v.amendment.originalApprovalSealsChanged=true,
  v=>v.amendment.originalResearch331Recovered=true,
  v=>v.amendment.publicationAuthorized=true,
  v=>v.amendment.evidenceSelection.sha256='0'.repeat(64),
  v=>v.amendment.fullDocumentIncluded=true,
  v=>v.amendment.fullDocumentBytesVerifiedByCandidate=true,
  v=>v.amendment.customerUrlChangesFromBaseline=1,
  v=>v.amendment.historicalSourceLinkAmendment.sha256='0'.repeat(64)
 ];
 for(const mutate of mutations){const inputs=loadGangnamCurrentInputs();mutate(inputs);assert.throws(()=>projectGangnamCurrentRuntime(inputs),/amendment object drift/);}
 const inputs=loadGangnamCurrentInputs();inputs.amendment.newUrl=oldUrl;inputs.amendmentBytes=Buffer.from(json(inputs.amendment));
 assert.throws(()=>projectGangnamCurrentRuntime(inputs),/amendment SHA binding drift/);
});

test('SETEC minimized evidence rejects wrong selection, extraction range drift, missing extracts and each altered artifact',()=>{
 const missing=loadGangnamCurrentInputs();delete missing.evidence[extract];assert.throws(()=>projectGangnamCurrentRuntime(missing),/missing or unexpected evidence files/);
 const extra=loadGangnamCurrentInputs();extra.evidence['invented.pdf']=Buffer.from('%PDF-fake');assert.throws(()=>projectGangnamCurrentRuntime(extra),/missing or unexpected evidence files/);
 const selection=loadGangnamCurrentInputs();selection.selection.files[4].sha256='0'.repeat(64);assert.throws(()=>projectGangnamCurrentRuntime(selection),/evidence selection object drift/);
 selection.selectionBytes=Buffer.from(json(selection.selection));assert.throws(()=>projectGangnamCurrentRuntime(selection),/evidence selection SHA binding drift/);
 const replacement=loadGangnamCurrentInputs();replacement.evidence[extract]=Buffer.from('invented text');assert.throws(()=>projectGangnamCurrentRuntime(replacement),/evidence bytes\/hash drift/);
 for(const entry of loadGangnamCurrentInputs().selection.files){const inputs=loadGangnamCurrentInputs();inputs.evidence[entry.path][0]^=1;assert.throws(()=>projectGangnamCurrentRuntime(inputs),/evidence bytes\/hash drift/,entry.path);}
 for(const mutate of [v=>v.selection.files[10].sourceTextByteRange[0]++,v=>v.selection.files[10].sourceTextNewlineRangeInclusive[1]++,v=>v.selection.files[10].sourcePdfPage=14,v=>v.selection.originalPdfSha256='0'.repeat(64),v=>v.selection.fullDocumentBytesVerifiedByCandidate=true]){const inputs=loadGangnamCurrentInputs();mutate(inputs);assert.throws(()=>projectGangnamCurrentRuntime(inputs),/evidence selection object drift/);}
 for(const mutate of [v=>v.historicalAmendment.newUrl=oldUrl,v=>v.historicalSelection.files[4].sha256='0'.repeat(64)]){const inputs=loadGangnamCurrentInputs();mutate(inputs);assert.throws(()=>projectGangnamCurrentRuntime(inputs),/historical (amendment|selection) object drift/);}
});

test('SETEC original full-document validator remains unchanged and fails for intentionally omitted PDF',()=>{
 assert.equal(sha(fs.readFileSync(path.join(projectRoot,'scripts/generate_gangnam_current_source.mjs'))),'ae4658f1fa67049f73c5fc8c95259ee621cd60fcf7302f55b26a3904e6f2526a');
 assert.equal(sha(fs.readFileSync(path.join(projectRoot,'scripts/source_link_amendment.py'))),'efcdb15913494381a0328b07e87b386adeab5b8320b6d9d2b8ec09c321bdb24c');
 assert.throws(()=>loadHistoricalFullEvidence(),/ENOENT.*setec-current-linked-operations\.pdf/);
});

test('SETEC missing extract, extra evidence and either reintroduced full file fail before outputs are written',()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'gangnam-minimal-evidence-negative-'));
 try{
  fs.cpSync(path.join(projectRoot,'src/data'),path.join(root,'src/data'),{recursive:true});
  const evidence=path.join(root,'src/data/gangnam-current-facts');
  const output=path.join(root,'src/data/pages.json');fs.writeFileSync(output,'unchanged sentinel\n');
  const saved=fs.readFileSync(path.join(evidence,extract));fs.unlinkSync(path.join(evidence,extract));
  assert.throws(()=>regenerateGangnamCurrentRuntime({root}),/missing or unexpected evidence inventory/);
  assert.equal(fs.readFileSync(output,'utf8'),'unchanged sentinel\n');
  fs.writeFileSync(path.join(evidence,extract),saved);
  for(const name of [...omitted,'extracts/extra.txt','raw/renamed-full-document.pdf']){
   fs.writeFileSync(path.join(evidence,name),'synthetic forbidden evidence, no personal data');
   assert.throws(()=>regenerateGangnamCurrentRuntime({root}),/full-document evidence forbidden|missing or unexpected evidence inventory/);
   assert.equal(fs.readFileSync(output,'utf8'),'unchanged sentinel\n');
   fs.unlinkSync(path.join(evidence,name));
  }
  fs.symlinkSync(path.join(evidence,extract),path.join(evidence,'extracts/extra-link.txt'));
  assert.throws(()=>regenerateGangnamCurrentRuntime({root}),/symlink evidence forbidden/);
  fs.unlinkSync(path.join(evidence,'extracts/extra-link.txt'));
  fs.writeFileSync(path.join(root,sourceAmendmentFile),'{}\n');
  assert.throws(()=>regenerateGangnamCurrentRuntime({root}),/amendment SHA binding drift/);
  assert.equal(fs.readFileSync(output,'utf8'),'unchanged sentinel\n');
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});

test('SETEC exact projection rejects old/wrong/new-source drift, a second URL, customer prose and year edits',()=>{
 const mutations=[
  v=>v['gangnam-copy'].articles[2].sourceLinks[3].url=oldUrl,
  v=>v['gangnam-copy'].articles[2].sourceLinks[3].url=newUrl+'?unreviewed=1',
  v=>v['gangnam-copy'].articles[2].sourceLinks[2].url=newUrl,
  v=>v['gangnam-copy'].articles[0].firstAnswer+=' 새 문장',
  v=>v['gangnam-copy'].articles[2].sections[3].paragraphs[1]=v['gangnam-copy'].articles[2].sections[3].paragraphs[1].replace('2024년','2025년'),
  v=>v.pages[2].sourceNote=v.pages[2].sourceNote.replace('2024년','2025년'),
  v=>v.pages[2].sourceLinks[3].url=oldUrl,
  v=>v.pages[2].sources[3].url=oldUrl,
  v=>v.pages[2].sources[3].verifiedAt='2026-10-14',
  v=>v.pages[2].snapshotHash=baseline.pages[2].snapshotHash,
  v=>v.pages[2].snapshotId=baseline.pages[2].snapshotId,
  v=>v.pages[2].currentSourceBinding.sourcePdfSha256='0'.repeat(64),
  v=>v.pages[2].currentSourceBinding.fullDocumentIncluded=true,
  v=>v.pages[2].currentSourceBinding.fullDocumentBytesVerifiedByCandidate=true,
  v=>v.pages[2].currentSourceBinding.evidenceMode='full-document',
  v=>v.pages[2].currentSourceBinding.selectedPdfPages.push(42),
  v=>v.pages[2].currentSourceBinding.historicalEvidenceSelection.sha256='0'.repeat(64),
  v=>v.pages[2].currentSourceBinding.evidenceSelectionSha256='0'.repeat(64),
  v=>delete v.pages[2].currentSourceBinding,
  v=>v.pages[0].currentSourceBinding=clone(v.pages[2].currentSourceBinding),
  v=>v['page-map'].pages[2].snapshotHash=baseline.pages[2].snapshotHash,
  v=>v.architecture.pages[2].sources[3].url=oldUrl,
  v=>v['publish-manifest'].pages[2].sourceLinks[3].url=oldUrl,
  v=>v['publish-manifest'].directRelease.contentHashes[2].publicSourceSha256=baseline.pages[2].snapshotHash,
  v=>delete v['direct-checkpoint'].currentSourceBinding,
  v=>v['gangnam-a04-metadata'].records[3].title_alignment_score=99
 ];
 for(const mutate of mutations)badOutput(mutate);
 badOutput(v=>v.extra={});
});

test('SETEC source refresh grants no publication, ownership, source-commit or IndexNow evidence',()=>{
 const release=current['publish-manifest'].directRelease,checkpoint=current['direct-checkpoint'];
 assert.deepEqual(release.publishedCoverage,{numerator:0,denominator:3,percent:0});
 assert.equal(release.publicationAuthorized,false);assert.equal(release.sourceCommit,null);
 assert.equal(release.screenQa,'UNVERIFIED');assert.equal(release.sitemapUrlCount,0);
 assert.equal(checkpoint.productionApproved,false);assert.equal(checkpoint.hostnameOwnershipVerified,false);
 assert.equal(checkpoint.productionEvidence,null);assert.deepEqual(checkpoint.searchIndexing,{submitted:false,receipt:null});
 for(const mutate of [
  v=>v['publish-manifest'].directRelease.publicationAuthorized=true,
  v=>v['publish-manifest'].directRelease.sourceCommit='a'.repeat(40),
  v=>v['publish-manifest'].directRelease.publishedCoverage.numerator=3,
  v=>v['publish-manifest'].directRelease.sitemapUrlCount=5,
  v=>v['publish-manifest'].directRelease.screenQa='PASS',
  v=>v['publish-manifest'].directRelease.currentSourceBinding.publicationAuthorized=true,
  v=>v['direct-checkpoint'].productionApproved=true,
  v=>v['direct-checkpoint'].hostnameOwnershipVerified=true,
  v=>v['direct-checkpoint'].productionEvidence={http:200},
  v=>v['direct-checkpoint'].searchIndexing.submitted=true,
  v=>v['direct-checkpoint'].searchIndexing.receipt='invented'
 ])badOutput(mutate);
});

test('SETEC runtime input guard fails closed on event provenance and source parity drift',async()=>{
 const {assertRegionalInput}=await import('../src/lib/regional-runtime.mjs');
 assert.equal(assertRegionalInput(current.pages).length,3);
 for(const mutate of [
  v=>delete v[2].currentSourceBinding,
  v=>v[2].currentSourceBinding.amendmentSha256='0'.repeat(64),
  v=>v[2].currentSourceBinding.currentSourceUrl=oldUrl,
  v=>v[2].sources[3].url=oldUrl,
  v=>v[2].sourceLinks[3].url=oldUrl,
  v=>v[2].snapshotHash=baseline.pages[2].snapshotHash,
  v=>v[2].snapshotId=baseline.pages[2].snapshotId,
  v=>v[0].currentSourceBinding=clone(v[2].currentSourceBinding)
 ]){const pages=clone(current.pages);mutate(pages);assert.throws(()=>assertRegionalInput(pages),/mismatch|drift/);}
});

test('SETEC current generation is deterministic and exact active outputs verify',()=>{
 assert.deepEqual(projectGangnamCurrentRuntime(),current);
 assert.equal(verifyGangnamCurrentRuntime(actual()),true);
 assert.deepEqual(regenerateGangnamCurrentRuntime({check:true}),current);
});
