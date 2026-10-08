import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {productFamilies,selectProducts} from './catalog.mjs';
export const WRITER_ID='7aeb5b8d-fab3-4526-8598-dcea31bd73e6';
export const REVIEWER_ID='supplement-source-review-9739ec25610d44e7';
export const RELEASE_ID='goyang-missing-pages-20261007';
export const EVIDENCE_PATH='src/data/manual-review/goyang-supplemental-source-review-20261007.json';
export const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
export const BINDING_KEYS=['contentHash','sourcesHash','catalogHash','catalogFileHash','rendererHash','assetsHash','frozenHash'];
const filesUnder=(root,relative)=>{
 const out=[];
 const walk=rel=>{const p=path.join(root,rel);const stat=fs.lstatSync(p);assert(!stat.isSymbolicLink(),'Bound file cannot be symlink: '+rel);if(stat.isDirectory())for(const child of fs.readdirSync(p).sort())walk(path.posix.join(rel,child));else if(stat.isFile())out.push(rel);};
 walk(relative);return out;
};
const fileSetHash=(root,names)=>digest(JSON.stringify([...new Set(names)].sort().map(name=>[name,digest(fs.readFileSync(path.join(root,name)))])));
export function collectBindings(root) {
 const bytes=fs.readFileSync(path.join(root,'src/data/manual-pages.json'));
 const pages=JSON.parse(bytes);const catalogBytes=fs.readFileSync(path.join(root,'src/data/products.json'));
 const renderer=['astro.config.mjs','package.json','package-lock.json',...['src/components','src/layouts','src/pages','src/lib','src/styles','src/config','scripts'].flatMap(p=>filesUnder(root,p).filter(name=>/\.(?:mjs|js|ts|astro|css|py)$/.test(name)))];
 // Bind every data input, including new runtime controls. Exclusions are individually
 // bound elsewhere or generated build metadata, never arbitrary unrecognized inputs.
 const excludedData=new Set(['src/data/manual-provenance.json','src/data/manual-pages.json','src/data/build-revision.json',EVIDENCE_PATH]);
 const frozen=filesUnder(root,'src/data').filter(f=>!excludedData.has(f));
 return {contentHash:digest(bytes),sourcesHash:digest(JSON.stringify(pages.map(p=>({pageKey:p.pageKey,sources:p.sources,source:p.source})))),catalogHash:digest(JSON.stringify(JSON.parse(catalogBytes))),catalogFileHash:digest(catalogBytes),rendererHash:fileSetHash(root,renderer),assetsHash:fileSetHash(root,filesUnder(root,'public')),frozenHash:fileSetHash(root,frozen)};
}
export function readReviewEvidence(root,relative=EVIDENCE_PATH) {
 assert.equal(relative,EVIDENCE_PATH,'Unexpected evidence path');
 const base=fs.realpathSync(root);const target=path.join(base,relative);
 const real=fs.realpathSync(target);
 assert(real.startsWith(base+path.sep),'Evidence path escapes release root');
 assert(!fs.lstatSync(target).isSymbolicLink(),'Evidence file cannot be symlink');
 return fs.readFileSync(real);
}
export function validateManualContract(pages,provenance,bytes,products,{indexable=false,production=false,bindings,reviewEvidenceBytes=null}={}) {
 assert.equal(provenance.manualReleaseId,RELEASE_ID,'Unexpected release identity');
 assert.equal(provenance.writerId,WRITER_ID,'Unexpected writer identity');
 assert.equal(provenance.expectedReviewerId,REVIEWER_ID,'Unexpected assigned reviewer');
 assert(bindings,'Missing actual release bindings');
 assert.equal(provenance.contentHash,digest(bytes),'Manual content digest drift');
 assert.equal(provenance.catalogHash,digest(JSON.stringify(products)),'Manual catalog digest drift');
 for(const key of BINDING_KEYS)assert.equal(provenance[key],bindings[key],'Release binding drift: '+key);
 for(const page of pages){
  assert.equal(page.publicationMode,'manual-user-request');assert.equal(page.manualReleaseId,RELEASE_ID);
  for(const f of ['snapshotId','snapshotHash','approvalVerified','sourceRecordId','publishQueueRecordId'])assert.equal(page[f],undefined,'Fabricated frozen provenance: '+f);
  assert.deepEqual(page.productKeys,selectProducts(page,products,productFamilies(page).length>3?4:3).map(p=>p.key),'SKU/intent mismatch: '+page.pageKey);
  const families=productFamilies(page);if(page.pageType==='funeral-facility')assert.deepEqual(families,['funeral']);if(page.pageType==='event-venue')assert.deepEqual(families,['congrats']);
 }
 if((indexable||production)&&pages.length){
  const review=provenance.independentReview;
  assert.equal(review?.status,'approved','Manual independent review pending');
  assert.equal(review.reviewerId,REVIEWER_ID,'Unrecognized independent reviewer');
  assert.notEqual(review.reviewerId,provenance.writerId,'Writer cannot approve own content');
  assert.equal(review.evidencePath,EVIDENCE_PATH,'Unexpected evidence path');
  assert(review.reviewedAt&&!Number.isNaN(Date.parse(review.reviewedAt)),'Missing review timestamp');
  assert(reviewEvidenceBytes,'Missing actual independent evidence bytes');
  assert.equal(review.evidenceSha256,digest(reviewEvidenceBytes),'Review evidence bytes/hash mismatch');
  const evidence=JSON.parse(reviewEvidenceBytes);
  for(const [key,value] of Object.entries({status:'approved',manualReleaseId:RELEASE_ID,writerId:WRITER_ID,reviewerId:REVIEWER_ID,reviewedAt:review.reviewedAt}))assert.equal(evidence[key],value,'Evidence identity/status mismatch: '+key);
  for(const key of BINDING_KEYS){assert.equal(review[key],bindings[key],'Review does not bind current '+key);assert.equal(evidence[key],bindings[key],'Evidence does not bind current '+key);}
 }
 return true;
}
export function productionRequested(env,config) {
 const target=new URL(env.SITE_URL||config.previewUrl);
 const clean=!target.username&&!target.password&&target.pathname==='/'&&!target.search&&!target.hash;
 const local=clean&&['http:','https:'].includes(target.protocol)&&['localhost','127.0.0.1','[::1]'].includes(target.hostname);
 return env.SITE_INDEXABLE!=='false'||!local||env.MANUAL_PUBLISH==='true';
}
