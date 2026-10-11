import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const root=path.resolve(path.dirname(new URL(import.meta.url).pathname),'../..');
const digest=s=>crypto.createHash('sha256').update(s).digest('hex');
export function artifactInventory(){
 const paths=[];const walk=dir=>{for(const e of fs.readdirSync(path.join(root,dir),{withFileTypes:true})){const rel=dir+'/'+e.name;if(e.isDirectory())walk(rel);else if(e.isFile()&&!['src/data/build-revision.json','src/data/manual-release-review.json','src/data/manual-supplemental-review-20261007.json','src/data/manual-integrated-review-20261011.json'].includes(rel))paths.push(rel);}};
 for(const dir of ['src','scripts','public'])walk(dir);
 for(const file of ['package.json','astro.config.mjs'])paths.push(file);
 return paths.sort().map(file=>({file,sha256:digest(fs.readFileSync(path.join(root,file)))}));
}
export function artifactDigest(){return digest(JSON.stringify(artifactInventory()));}
export const assignedWriter='/root/audit_regional_sales_copy';
export const assignedReviewer='/root';
export const releaseOrigin='https://yongin.fwith.kr';
export function isLocalNoindexPreview(env){
 if(env.SITE_INDEXABLE!=='false'||!env.SITE_URL)return false;
 let u;try{u=new URL(env.SITE_URL);}catch{return false;}
 return ['http:','https:'].includes(u.protocol)&&['localhost','127.0.0.1','[::1]'].includes(u.hostname)&&!u.username&&!u.password&&u.pathname==='/'&&!u.search&&!u.hash;
}
export const requiredCriteria=['sourceAccuracy','localDecisionValue','providerVoice','titleH1AnswerAlignment','distinctCardSummary','purchasePath','workingCta','catalogAndImageBinding','noFalsePolicyClaims','originalIntegrity','routeAndSitemapParity','mobileAndDesktopVisual'];
export function validateReview(review,currentDigest,manualKeys){
 if(review?.schemaVersion!==1||review?.decision!=='pass')throw Error('MANUAL_RELEASE_BLOCKED: independent PASS missing');
 if(review.releaseOrigin!==releaseOrigin)throw Error('MANUAL_RELEASE_BLOCKED: wrong release origin');
 if(review.artifactDigest!==currentDigest)throw Error('MANUAL_RELEASE_BLOCKED: reviewed artifact digest differs');
 if(review.writerLabel!==assignedWriter||review.reviewerLabel!==assignedReviewer||String(review.writerLabel).replace(/^writer-/, '')===String(review.reviewerLabel).replace(/^reviewer-/, ''))throw Error('MANUAL_RELEASE_BLOCKED: separate opaque writer/reviewer required');
 if(!review.reviewedAt||Number.isNaN(Date.parse(review.reviewedAt)))throw Error('MANUAL_RELEASE_BLOCKED: review timestamp missing');
 if(!review.evidence||!Array.isArray(review.evidence.pages)||review.evidence.pages.length!==manualKeys.length)throw Error('MANUAL_RELEASE_BLOCKED: complete page review missing');
 const seen=new Set(),deferredVisualKeys=[];
 for(const row of review.evidence.pages){
  if(!manualKeys.includes(row.pageKey)||seen.has(row.pageKey)||row.decision!=='pass')throw Error('MANUAL_RELEASE_BLOCKED: invalid reviewed page');seen.add(row.pageKey);
  for(const criterion of requiredCriteria){
   if(row.criteria?.[criterion]==='pass')continue;
   if(criterion==='mobileAndDesktopVisual'&&row.criteria?.[criterion]==='DEFERRED_NOT_PASS'){deferredVisualKeys.push(row.pageKey);continue;}
   throw Error('MANUAL_RELEASE_BLOCKED: '+criterion+' not passed');
  }
 }
 if(deferredVisualKeys.length){
  const d=review.evidence.visualDeferral;
  if(d?.status!=='DEFERRED_NOT_PASS'||d.criterion!=='mobileAndDesktopVisual'||d.authorization!=='user-requested-batch-deferral'||d.noVisualPassClaim!==true)throw Error('MANUAL_RELEASE_BLOCKED: explicit visual-only deferral missing');
  if(typeof d.authorizationReference!=='string'||!d.authorizationReference.trim()||typeof d.reason!=='string'||!d.reason.trim())throw Error('MANUAL_RELEASE_BLOCKED: visual deferral authorization/reason missing');
  if(!Array.isArray(d.pendingChecks)||JSON.stringify([...d.pendingChecks].sort())!==JSON.stringify(['desktop-actual-screen','narrow-actual-screen']))throw Error('MANUAL_RELEASE_BLOCKED: both actual-screen follow-ups required');
  if(!Array.isArray(d.pendingPageKeys)||JSON.stringify([...d.pendingPageKeys].sort())!==JSON.stringify([...deferredVisualKeys].sort()))throw Error('MANUAL_RELEASE_BLOCKED: visual deferral page coverage differs');
 }else if(review.evidence.visualDeferral!=null)throw Error('MANUAL_RELEASE_BLOCKED: stale visual deferral without deferred pages');
 const proof=digest(JSON.stringify(review.evidence));if(review.evidenceSha256!==proof)throw Error('MANUAL_RELEASE_BLOCKED: review evidence digest differs');
 return true;
}
export function assertManualProductionReady(){
 if(isLocalNoindexPreview(process.env))return {mode:'loopback-noindex-preview',releaseApproved:false};
 const target=new URL(process.env.SITE_URL||releaseOrigin);
 if(target.origin!==releaseOrigin||target.pathname!=='/'||target.search||target.hash||target.username||target.password)throw Error('MANUAL_RELEASE_BLOCKED: unknown public origin');
 const manual=JSON.parse(fs.readFileSync(path.join(root,'src/data/manual-pages.json'),'utf8'));
 const review=JSON.parse(fs.readFileSync(path.join(root,'src/data/manual-integrated-review-20261011.json'),'utf8'));
 validateReview(review,artifactDigest(),manual.pages.map(p=>p.pageKey));
 return {mode:'production',releaseApproved:true,visualQa:review.evidence.pages.some(row=>row.criteria.mobileAndDesktopVisual==='DEFERRED_NOT_PASS')?'DEFERRED_NOT_PASS':'PASS'};
}
