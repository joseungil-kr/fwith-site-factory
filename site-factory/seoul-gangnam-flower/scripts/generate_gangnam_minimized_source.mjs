/** Privacy-minimized local successor: exact source excerpts, never the full PDF/text.
 * Original generators, source-link amendment, ten-file selection and A04 seals stay historical.
 * Original PDF/text hashes are provenance identities, not full-byte verification in this candidate.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {projectRoot,sha,canonical,loadGangnamInputs,projectGangnamRuntime} from './generate_gangnam_runtime.mjs';
import {pageSources} from '../src/lib/gangnam-sources.mjs';

export const sourceAmendmentFile='src/data/gangnam-minimal-evidence-amendment.json';
export const sourceAmendmentSha256='035c8a4aef367f85a125869856cc016c7fb342bee46e182e5d41336561bc6dfc';
export const sourceSelectionFile='src/data/gangnam-current-facts/EXTRACT-SELECTION-MANIFEST.json';
export const sourceSelectionSha256='ca292b815888b3c360183941548806725f7055aba6f78f57931f0b7021d8d09d';
export const historicalAmendmentFile='src/data/gangnam-source-link-amendment.json';
export const historicalAmendmentSha256='16d302af3ae83e16482b52b338ecc834dbdd755bae673c9d701d940607cc01bb';
export const historicalSelectionFile='src/data/gangnam-current-facts/SELECTION-MANIFEST.json';
export const historicalSelectionSha256='b189f8127d5424d696814f226b17f4334f66c0e0fda61d0ffa989f3979262284';
const evidenceRoot='src/data/gangnam-current-facts';
const oldUrl='https://setec.or.kr/resources/front/files/01_SETEC.pdf';
const newUrl='https://www.setec.or.kr/resources/front/files/2025_SETEC.pdf';
const parentUrl='https://www.setec.or.kr/front/rent/rent01.do';
const pdfSha256='91745c11ecd4ca6e6964cf823be8e7325499ed585ba09017ae3fc222d56f476a';
const textSha256='befe8c7000e0003599519422d4d347e856b7523ff41e447560d53b801229af11';
const baselineCopySha256='893978677953deab30d9343b0dee00c0670dde668d8d53054252f1f0d034a816';
const currentCopySha256='b442c6ab713453dc4651ea27f1586f777cd5f9915c5b9dd932d6f09da761990b';
const predecessorSourceSha256='a25def8e1ee19991596762f4299c9dec7c2c695f12c9b861548675a9fbb762aa';
const omittedFiles=['raw/setec-current-linked-operations.pdf','text/setec-current-linked-operations.txt'];
const serialize=value=>JSON.stringify(value,null,2)+'\n';
const same=(a,b)=>canonical(a)===canonical(b);
const fail=reason=>{throw new Error('Gangnam minimal evidence: '+reason);};
function pinnedJson(bytes,expected,label){
 if(!bytes||sha(bytes)!==expected)fail(label+' SHA binding drift');
 return JSON.parse(Buffer.from(bytes).toString('utf8'));
}
function assertObject(actual,expected,label){if(!same(actual,expected))fail(label+' object drift');}
function safeEvidencePath(relative){
 if(typeof relative!=='string'||!relative||relative.includes('\\')||path.posix.isAbsolute(relative)||relative.split('/').some(part=>part==='..'||part==='.'||!part))fail('unsafe evidence path');
 return relative;
}
function readRegularFile(file){
 const stat=fs.lstatSync(file);
 if(!stat.isFile()||stat.isSymbolicLink())fail('nonregular or symlink evidence '+file);
 return fs.readFileSync(file);
}
function assertEvidenceInventory(root,selection){
 const base=path.join(root,evidenceRoot),actual=[];
 const walk=(dir,relative='')=>{
  for(const entry of fs.readdirSync(dir,{withFileTypes:true})){
   const name=relative?relative+'/'+entry.name:entry.name;
   if(entry.isSymbolicLink())fail('symlink evidence forbidden '+name);
   if(entry.isDirectory())walk(path.join(dir,entry.name),name);
   else if(entry.isFile())actual.push(name);
   else fail('nonregular evidence forbidden '+name);
  }
 };
 walk(base);
 for(const excluded of omittedFiles)if(actual.includes(excluded))fail('full-document evidence forbidden '+excluded);
 const expected=['SELECTION-MANIFEST.json','EXTRACT-SELECTION-MANIFEST.json',...selection.files.map(row=>safeEvidencePath(row.path))];
 if(!same(actual.sort(),expected.sort()))fail('missing or unexpected evidence inventory');
}

export function loadGangnamCurrentInputs(root=projectRoot){
 root=path.resolve(root);
 const amendmentBytes=readRegularFile(path.join(root,sourceAmendmentFile));
 const amendment=pinnedJson(amendmentBytes,sourceAmendmentSha256,'amendment');
 const selectionBytes=readRegularFile(path.join(root,sourceSelectionFile));
 const selection=pinnedJson(selectionBytes,sourceSelectionSha256,'evidence selection');
 const historicalAmendmentBytes=readRegularFile(path.join(root,historicalAmendmentFile));
 const historicalAmendment=pinnedJson(historicalAmendmentBytes,historicalAmendmentSha256,'historical amendment');
 const historicalSelectionBytes=readRegularFile(path.join(root,historicalSelectionFile));
 const historicalSelection=pinnedJson(historicalSelectionBytes,historicalSelectionSha256,'historical selection');
 assertEvidenceInventory(root,selection);
 const evidence=Object.fromEntries(selection.files.map(row=>[row.path,readRegularFile(path.join(root,evidenceRoot,safeEvidencePath(row.path)))]));
 return {root,baseline:loadGangnamInputs(root),amendment,amendmentBytes,selection,selectionBytes,historicalAmendment,historicalAmendmentBytes,historicalSelection,historicalSelectionBytes,evidence};
}

export function validateGangnamCurrentEvidence(inputs){
 const amendment=pinnedJson(inputs.amendmentBytes,sourceAmendmentSha256,'amendment');
 const selection=pinnedJson(inputs.selectionBytes,sourceSelectionSha256,'evidence selection');
 const historical=pinnedJson(inputs.historicalAmendmentBytes,historicalAmendmentSha256,'historical amendment');
 const priorSelection=pinnedJson(inputs.historicalSelectionBytes,historicalSelectionSha256,'historical selection');
 assertObject(inputs.amendment,amendment,'amendment');
 assertObject(inputs.selection,selection,'evidence selection');
 assertObject(inputs.historicalAmendment,historical,'historical amendment');
 assertObject(inputs.historicalSelection,priorSelection,'historical selection');
 assertEvidenceInventory(inputs.root,selection);
 if(amendment.evidenceMode!=='bounded-extracts-no-full-document'||amendment.baselineSourceContentSha256!==predecessorSourceSha256||amendment.baselineCustomerCopySha256!==currentCopySha256||amendment.customerUrlChangesFromBaseline!==0||amendment.bodySentencesChanged!==0||amendment.dateTextChanged!==false||amendment.originalApprovalSealsChanged!==false||amendment.originalResearch331Recovered!==false||amendment.publicationAuthorized!==false||amendment.fullDocumentIncluded!==false||amendment.fullDocumentBytesVerifiedByCandidate!==false)fail('minimized scope/publication boundary drift');
 assertObject(amendment.historicalSourceLinkAmendment,{path:historicalAmendmentFile,sha256:historicalAmendmentSha256},'historical amendment reference');
 assertObject(amendment.historicalEvidenceSelection,{path:historicalSelectionFile,sha256:historicalSelectionSha256},'historical selection reference');
 assertObject(amendment.evidenceSelection,{path:sourceSelectionFile,sha256:sourceSelectionSha256},'active selection reference');
 if(historical.effectiveCopyJsonPointer!=='/articles/2/sourceLinks/3/url'||historical.oldUrl!==oldUrl||historical.newUrl!==newUrl||historical.officialParentUrl!==parentUrl||historical.newPdfSha256!==pdfSha256||historical.baselineCopySha256!==baselineCopySha256||historical.publicationAuthorized!==false)fail('historical bounded URL contract drift');
 if(selection.evidenceMode!==amendment.evidenceMode||selection.originalPdfUrl!==newUrl||selection.originalPdfSha256!==pdfSha256||selection.originalTextSha256!==textSha256||selection.historicalSelectionSha256!==historicalSelectionSha256||selection.fileCount!==11||selection.files.length!==11||selection.historicalSnapshotRecovered!==false||selection.fullDocumentIncluded!==false||selection.fullDocumentBytesVerifiedByCandidate!==false||selection.publicationAuthorized!==false)fail('minimized evidence selection contract drift');
 assertObject(selection.excludedFiles,omittedFiles,'excluded full-document paths');
 assertObject(selection.selectedPdfPages,[1,2,13],'selected PDF pages');
 if(!same(Object.keys(inputs.evidence??{}).sort(),selection.files.map(row=>row.path).sort()))fail('missing or unexpected evidence files');
 for(const row of selection.files){
  safeEvidencePath(row.path);
  const bytes=inputs.evidence[row.path];
  if(!bytes||bytes.byteLength!==row.bytes||sha(bytes)!==row.sha256)fail('evidence bytes/hash drift '+row.path);
 }
 const retained=priorSelection.files.filter(row=>!omittedFiles.includes(row.path));
 assertObject(selection.files.filter(row=>!row.path.startsWith('extracts/')),retained,'eight retained evidence identities');
 const ranges=[['extracts/cover-page1.txt',1,[0,100],[1,11]],['extracts/revision-page2.txt',2,[100,1271],[12,26]],['extracts/article43-page13.txt',13,[34180,35010],[474,480]]];
 for(const [name,pdfPage,byteRange,lineRange] of ranges){
  const row=selection.files.find(row=>row.path===name);
  if(!row||row.sourcePdfPage!==pdfPage||!same(row.sourceTextByteRange,byteRange)||!same(row.sourceTextNewlineRangeInclusive,lineRange)||row.bytes!==byteRange[1]-byteRange[0])fail('exact extraction range drift '+name);
 }
 const text=name=>Buffer.from(inputs.evidence[name]).toString('utf8');
 const json=name=>JSON.parse(text(name));
 const fetch=json('current-linked-setec-fetch.json');
 // Retained acquisition record, not a re-download or verification of absent full bytes.
 if(fetch.url!==newUrl||fetch.finalUrl!==newUrl||fetch.httpStatus!==200||fetch.contentType!=='application/pdf'||fetch.sha256!==pdfSha256||fetch.bytes!==635857||fetch.fetchedAtUTC!==historical.sourceAcquiredAtUTC||fetch.savedFile!==omittedFiles[0]||fetch.textSha256!==textSha256)fail('retained PDF acquisition identity drift');
 const comparison=json('setec-version-comparison.json');
 if(comparison.oldURL!==oldUrl||comparison.currentLinkedURL!==newUrl||comparison.linkedFrom!==parentUrl||comparison.newRawSha256!==pdfSha256||comparison.currentLinkedCoverDate!=='2024.10'||comparison.currentLinkedRevisionDate!=='2024.10.04'||comparison.customerProseRevisionRequired!==false||comparison.customerSourceLinkRevisionRequired!==true||comparison.article43WhitespaceNormalizedEqual!==true||comparison.customerSourceLinkPointer!==historical.effectiveCopyJsonPointer)fail('retained source/date comparison drift');
 const html=text('raw/setec-rental-procedure.html');
 if(!html.includes('서울무역전시장(SETEC) 운영요령')||!html.includes('href="/resources/front/files/2025_SETEC.pdf"'))fail('official parent source link missing');
 if(!/2024\.\s*10\./.test(text(ranges[0][0]))||!text(ranges[1][0]).includes('2024.10.04.')||!text(ranges[2][0]).includes('제43조 (전시장 관리)')||!text(ranges[2][0]).includes('사용기간이 끝난 후 모든 물품을 수거'))fail('date/article43 extract content drift');
 const verdict=json('CURRENT-FACTS-VERDICT.json');
 if(verdict.candidateSourceContentSha256!==historical.baselineSourceContentSha256||verdict.candidateCopySha256!==baselineCopySha256||verdict.verdict!=='FACT_TEXT_SUPPORTED_SOURCE_LINK_REFRESH_REQUIRED'||verdict.requiredCustomerProseCorrections.length!==0||verdict.requiredSourceLinkCorrections.length!==1||verdict.publicationApproved!==false||verdict.historicalSnapshotRecovered!==false)fail('historical current facts verdict scope drift');
 const correction=verdict.requiredSourceLinkCorrections[0];
 if(correction.jsonPointer!==historical.effectiveCopyJsonPointer||correction.old!==oldUrl||correction.new!==newUrl||correction.verifiedParentPage!==parentUrl||correction.proseReplacement!==null)fail('historical current facts correction drift');
 return amendment;
}

export function projectGangnamCurrentRuntime(inputs=loadGangnamCurrentInputs()){
 const amendment=validateGangnamCurrentEvidence(inputs),historical=inputs.historicalAmendment;
 const output=Object.fromEntries(Object.entries(projectGangnamRuntime(inputs.baseline)).map(([name,value])=>[name,structuredClone(value)]));
 if(sha(serialize(output['gangnam-copy']))!==baselineCopySha256)fail('approved baseline copy bytes drift');
 const article=output['gangnam-copy'].articles[2];
 if(article.id!==historical.articleId||article.url!==historical.articleUrl||article.sourceLinks[3].url!==oldUrl)fail('exact article/source target drift');
 article.sourceLinks[3].url=newUrl;
 if(sha(serialize(output['gangnam-copy']))!==currentCopySha256)fail('customer copy must equal source1040 exactly');
 const binding={
  amendmentId:amendment.amendmentId,
  amendmentFile:sourceAmendmentFile,
  amendmentSha256:sourceAmendmentSha256,
  evidenceMode:amendment.evidenceMode,
  evidenceSelectionFile:sourceSelectionFile,
  evidenceSelectionSha256:sourceSelectionSha256,
  predecessorSourceContentSha256:predecessorSourceSha256,
  historicalSourceLinkAmendment:{file:historicalAmendmentFile,sha256:historicalAmendmentSha256},
  historicalEvidenceSelection:{file:historicalSelectionFile,sha256:historicalSelectionSha256},
  effectiveCopyJsonPointer:historical.effectiveCopyJsonPointer,
  currentSourceUrl:newUrl,
  officialParentUrl:parentUrl,
  sourcePdfSha256:pdfSha256,
  sourcePdfHashRole:'retained-acquisition-identity-not-full-document-byte-verification',
  sourceAcquiredAtUTC:historical.sourceAcquiredAtUTC,
  selectedPdfPages:[1,2,13],
  fullDocumentIncluded:false,
  fullDocumentBytesVerifiedByCandidate:false,
  publishedCoverDate:historical.publishedCoverDate,
  publishedRevisionDate:historical.publishedRevisionDate,
  customerUrlChangesFromPredecessor:0,
  bodySentencesChanged:0,
  publicationAuthorized:false
 };
 const page=output.pages[2];
 if(page.id!==article.id||page.url!==article.url||page.sourceLinks[3].url!==oldUrl||page.sources[3].url!==oldUrl)fail('event runtime target drift');
 page.sourceLinks=structuredClone(article.sourceLinks);page.sources[3].url=newUrl;pageSources(page);
 page.currentSourceBinding=structuredClone(binding);
 const omit=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);
 page.snapshotHash=sha(canonical(Object.fromEntries(Object.entries(page).filter(([key])=>!omit.has(key)))));
 page.snapshotId=`local-content-${page.slug}-${page.snapshotHash.slice(0,16)}`;
 const record=structuredClone(page);for(const key of ['sections','contentMarkdown','faq','uniqueBodyText'])delete record[key];
 output['page-map'].pages[2]=structuredClone(record);
 output['publish-manifest'].pages[2]=structuredClone(record);
 output.architecture.pages[2]={...structuredClone(record),status:'primary',pageRole:'REGION_SERVICE_LANDING',parentHub:'/regions/',contentRole:'question-answer',localizationPolicy:'local-required',sitemapIndexable:true};
 output['publish-manifest'].directRelease.contentHashes[2]={pageKey:page.pageKey,bodySha256:sha(page.contentMarkdown),publicSourceSha256:page.snapshotHash};
 output['publish-manifest'].directRelease.currentSourceBinding=structuredClone(binding);
 output['direct-checkpoint'].currentSourceBinding=structuredClone(binding);
 return output;
}

export function verifyGangnamCurrentRuntime(outputs,expected=projectGangnamCurrentRuntime()){
 if(!same(Object.keys(outputs).sort(),Object.keys(expected).sort()))fail('runtime output set drift');
 for(const [name,value] of Object.entries(expected))if(!same(outputs[name],value))fail('runtime projection drift '+name);
 return true;
}
export function regenerateGangnamCurrentRuntime({root=projectRoot,check=false}={}){
 const output=projectGangnamCurrentRuntime(loadGangnamCurrentInputs(root));
 if(check){
  const actual=Object.fromEntries(Object.keys(output).map(name=>[name,JSON.parse(readRegularFile(path.join(root,'src/data',name+'.json')).toString('utf8'))]));
  verifyGangnamCurrentRuntime(actual,output);
 }else for(const [name,value] of Object.entries(output)){
  const file=path.join(root,'src/data',name+'.json'),bytes=serialize(value);
  // Preserve unchanged runtime files' existing bytes and modification times.
  if(!fs.existsSync(file)||fs.readFileSync(file,'utf8')!==bytes)fs.writeFileSync(file,bytes);
 }
 return output;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 regenerateGangnamCurrentRuntime({check:process.argv.includes('--check')});
 console.log('GANGNAM minimized-evidence successor '+(process.argv.includes('--check')?'verified':'regenerated')+': customer copy unchanged from source1040, 11 exact evidence artifacts, full PDF/text absent and not reverified, 0 published.');
}
