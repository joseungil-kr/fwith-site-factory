/** Bounded local successor: one current SETEC source URL plus its evidence/snapshot bindings.
 * Historical rev4 inputs, the original generator and A04 seals stay immutable.
 * Saved evidence is rehashed offline; this script makes no network or publication claims.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {projectRoot,sha,canonical,loadGangnamInputs,projectGangnamRuntime} from './generate_gangnam_runtime.mjs';
import {pageSources} from '../src/lib/gangnam-sources.mjs';

export const sourceAmendmentFile='src/data/gangnam-source-link-amendment.json';
export const sourceAmendmentSha256='16d302af3ae83e16482b52b338ecc834dbdd755bae673c9d701d940607cc01bb';
export const sourceSelectionFile='src/data/gangnam-current-facts/SELECTION-MANIFEST.json';
export const sourceSelectionSha256='b189f8127d5424d696814f226b17f4334f66c0e0fda61d0ffa989f3979262284';
const evidenceRoot='src/data/gangnam-current-facts';
const oldUrl='https://setec.or.kr/resources/front/files/01_SETEC.pdf';
const newUrl='https://www.setec.or.kr/resources/front/files/2025_SETEC.pdf';
const parentUrl='https://www.setec.or.kr/front/rent/rent01.do';
const pdfSha256='91745c11ecd4ca6e6964cf823be8e7325499ed585ba09017ae3fc222d56f476a';
const baselineCopySha256='893978677953deab30d9343b0dee00c0670dde668d8d53054252f1f0d034a816';
const serialize=value=>JSON.stringify(value,null,2)+'\n';
const same=(a,b)=>canonical(a)===canonical(b);
const fail=reason=>{throw new Error('Gangnam source amendment: '+reason);};
function pinnedJson(bytes,expected,label){
 if(!bytes||sha(bytes)!==expected)fail(label+' SHA binding drift');
 return JSON.parse(Buffer.from(bytes).toString('utf8'));
}
function assertObject(actual,expected,label){if(!same(actual,expected))fail(label+' object drift');}
function safeEvidencePath(relative){
 if(typeof relative!=='string'||!relative||relative.includes('\\')||path.posix.isAbsolute(relative)||relative.split('/').some(part=>part==='..'||part==='.'||!part))fail('unsafe evidence path');
 return relative;
}

export function loadGangnamCurrentInputs(root=projectRoot){
 const amendmentBytes=fs.readFileSync(path.join(root,sourceAmendmentFile));
 const amendment=pinnedJson(amendmentBytes,sourceAmendmentSha256,'amendment');
 if(amendment.evidenceSelection.path!==sourceSelectionFile||amendment.evidenceSelection.sha256!==sourceSelectionSha256)fail('selection reference drift');
 const selectionBytes=fs.readFileSync(path.join(root,sourceSelectionFile));
 const selection=pinnedJson(selectionBytes,sourceSelectionSha256,'evidence selection');
 const evidence=Object.fromEntries(selection.files.map(row=>[row.path,fs.readFileSync(path.join(root,evidenceRoot,safeEvidencePath(row.path)))]));
 return {baseline:loadGangnamInputs(root),amendment,amendmentBytes,selection,selectionBytes,evidence};
}

export function validateGangnamCurrentEvidence(inputs){
 const amendment=pinnedJson(inputs.amendmentBytes,sourceAmendmentSha256,'amendment');
 const selection=pinnedJson(inputs.selectionBytes,sourceSelectionSha256,'evidence selection');
 assertObject(inputs.amendment,amendment,'amendment');
 assertObject(inputs.selection,selection,'evidence selection');
 if(amendment.effectiveCopyJsonPointer!=='/articles/2/sourceLinks/3/url'||amendment.oldUrl!==oldUrl||amendment.newUrl!==newUrl||amendment.officialParentUrl!==parentUrl||amendment.newPdfSha256!==pdfSha256||amendment.baselineCopySha256!==baselineCopySha256)fail('bounded URL contract drift');
 if(amendment.publicationAuthorized!==false||amendment.originalApprovalSealsChanged!==false||amendment.originalResearch331Recovered!==false||amendment.bodySentencesChanged!==0||amendment.dateTextChanged!==false)fail('scope/publication boundary drift');
 if(amendment.evidenceSelection.path!==sourceSelectionFile||amendment.evidenceSelection.sha256!==sourceSelectionSha256||selection.fileCount!==10||selection.files.length!==10||selection.historicalSnapshotRecovered!==false)fail('evidence selection contract drift');
 if(!same(Object.keys(inputs.evidence??{}).sort(),selection.files.map(row=>row.path).sort()))fail('missing or unexpected evidence files');
 for(const row of selection.files){
  safeEvidencePath(row.path);
  const bytes=inputs.evidence[row.path];
  if(!bytes||bytes.byteLength!==row.bytes||sha(bytes)!==row.sha256)fail('evidence bytes/hash drift '+row.path);
 }
 const text=name=>Buffer.from(inputs.evidence[name]).toString('utf8');
 const json=name=>JSON.parse(text(name));
 const pdf=Buffer.from(inputs.evidence['raw/setec-current-linked-operations.pdf']);
 if(pdf.subarray(0,5).toString('ascii')!=='%PDF-'||sha(pdf)!==pdfSha256)fail('missing or wrong current PDF');
 const fetch=json('current-linked-setec-fetch.json');
 if(fetch.url!==newUrl||fetch.finalUrl!==newUrl||fetch.httpStatus!==200||fetch.contentType!=='application/pdf'||fetch.sha256!==pdfSha256||fetch.bytes!==pdf.length||fetch.fetchedAtUTC!==amendment.sourceAcquiredAtUTC||fetch.savedFile!=='raw/setec-current-linked-operations.pdf'||fetch.textSha256!==sha(inputs.evidence['text/setec-current-linked-operations.txt']))fail('PDF acquisition evidence drift');
 const comparison=json('setec-version-comparison.json');
 if(comparison.oldURL!==oldUrl||comparison.currentLinkedURL!==newUrl||comparison.linkedFrom!==parentUrl||comparison.newRawSha256!==pdfSha256||comparison.currentLinkedCoverDate!=='2024.10'||comparison.currentLinkedRevisionDate!=='2024.10.04'||comparison.customerProseRevisionRequired!==false||comparison.customerSourceLinkRevisionRequired!==true||comparison.article43WhitespaceNormalizedEqual!==true||comparison.customerSourceLinkPointer!==amendment.effectiveCopyJsonPointer)fail('current source/date comparison drift');
 const html=text('raw/setec-rental-procedure.html');
 if(!html.includes('서울무역전시장(SETEC) 운영요령')||!html.includes('href="/resources/front/files/2025_SETEC.pdf"'))fail('official parent source link missing');
 const pdfText=text('text/setec-current-linked-operations.txt');
 if(!/2024\.\s*10\./.test(pdfText.split('\f')[0])||!pdfText.includes('2024.10.04.')||!pdfText.includes('제43조 (전시장 관리)')||!pdfText.includes('사용기간이 끝난 후 모든 물품을 수거'))fail('PDF date/article43 text drift');
 const verdict=json('CURRENT-FACTS-VERDICT.json');
 if(verdict.candidateSourceContentSha256!==amendment.baselineSourceContentSha256||verdict.candidateCopySha256!==baselineCopySha256||verdict.verdict!=='FACT_TEXT_SUPPORTED_SOURCE_LINK_REFRESH_REQUIRED'||verdict.requiredCustomerProseCorrections.length!==0||verdict.requiredSourceLinkCorrections.length!==1||verdict.publicationApproved!==false||verdict.historicalSnapshotRecovered!==false)fail('current facts verdict scope drift');
 const correction=verdict.requiredSourceLinkCorrections[0];
 if(correction.jsonPointer!==amendment.effectiveCopyJsonPointer||correction.old!==oldUrl||correction.new!==newUrl||correction.verifiedParentPage!==parentUrl||correction.proseReplacement!==null)fail('current facts correction drift');
 return amendment;
}

export function projectGangnamCurrentRuntime(inputs=loadGangnamCurrentInputs()){
 const amendment=validateGangnamCurrentEvidence(inputs);
 // Always reconstruct the approved baseline first, using its unchanged SHA checks.
 const output=Object.fromEntries(Object.entries(projectGangnamRuntime(inputs.baseline)).map(([name,value])=>[name,structuredClone(value)]));
 if(sha(serialize(output['gangnam-copy']))!==baselineCopySha256)fail('baseline copy bytes drift');
 const article=output['gangnam-copy'].articles[2];
 if(article.id!==amendment.articleId||article.url!==amendment.articleUrl||article.sourceLinks[3].url!==oldUrl)fail('exact article/source target drift');
 const priorCopy=structuredClone(output['gangnam-copy']);
 article.sourceLinks[3].url=newUrl;
 const restored=structuredClone(output['gangnam-copy']);restored.articles[2].sourceLinks[3].url=oldUrl;
 assertObject(restored,priorCopy,'one-pointer customer copy scope');
 const binding={
  amendmentId:amendment.amendmentId,
  amendmentFile:sourceAmendmentFile,
  amendmentSha256:sourceAmendmentSha256,
  evidenceSelectionFile:sourceSelectionFile,
  evidenceSelectionSha256:sourceSelectionSha256,
  effectiveCopyJsonPointer:amendment.effectiveCopyJsonPointer,
  currentSourceUrl:newUrl,
  officialParentUrl:parentUrl,
  sourcePdfSha256:pdfSha256,
  sourceAcquiredAtUTC:amendment.sourceAcquiredAtUTC,
  publishedCoverDate:amendment.publishedCoverDate,
  publishedRevisionDate:amendment.publishedRevisionDate,
  bodySentencesChanged:0,
  publicationAuthorized:false
 };
 const page=output.pages[2];
 if(page.id!==article.id||page.url!==article.url||page.sourceLinks[3].url!==oldUrl||page.sources[3].url!==oldUrl)fail('event runtime target drift');
 page.sourceLinks=structuredClone(article.sourceLinks);
 page.sources[3].url=newUrl;
 pageSources(page);
 page.currentSourceBinding=structuredClone(binding);
 // Same snapshot algorithm and exclusions as the immutable rev4 generator.
 const omit=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);
 page.snapshotHash=sha(canonical(Object.fromEntries(Object.entries(page).filter(([key])=>!omit.has(key)))));
 page.snapshotId=`local-content-${page.slug}-${page.snapshotHash.slice(0,16)}`;
 const record=structuredClone(page);
 for(const key of ['sections','contentMarkdown','faq','uniqueBodyText'])delete record[key];
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
  const actual=Object.fromEntries(Object.keys(output).map(name=>[name,JSON.parse(fs.readFileSync(path.join(root,'src/data',name+'.json'),'utf8'))]));
  verifyGangnamCurrentRuntime(actual,output);
 }else for(const [name,value] of Object.entries(output))fs.writeFileSync(path.join(root,'src/data',name+'.json'),serialize(value));
 return output;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 regenerateGangnamCurrentRuntime({check:process.argv.includes('--check')});
 console.log('GANGNAM bounded SETEC local source successor '+(process.argv.includes('--check')?'verified':'regenerated')+': one effective customer URL, unchanged prose/date/A04 seals, 10 rehashed evidence files, 0 published.');
}
