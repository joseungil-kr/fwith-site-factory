import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';import {fileURLToPath} from 'node:url';
import {digest,validateManualContract} from './manual-contract.mjs';import {isLocalPreview} from './manual-boundary.mjs';
export const projectRoot=fileURLToPath(new URL('../../',import.meta.url));
export const EVIDENCE_PATH='src/data/manual-review-evidence.json';
export const ROOT_INPUTS=['astro.config.mjs','package.json','package-lock.json','tsconfig.json','wrangler.jsonc','wrangler.staging.jsonc','production-indexing.enabled'];
const excluded=new Set(['src/data/manual-provenance.json',EVIDENCE_PATH,'src/data/build-revision.json']);
function ensureRegularPath(root,relative){
 let p=fs.realpathSync(root);
 for(const part of relative.split('/')){assert(part&&part!=='.'&&part!=='..','Unsafe bound path');p=path.join(p,part);assert(!fs.lstatSync(p).isSymbolicLink(),'Bound path symlink forbidden: '+relative);}
 return p;
}
export function dependencyInventory(root=projectRoot){
 const result={};
 const visit=relative=>{
  if(excluded.has(relative))return;
  const full=ensureRegularPath(root,relative),stat=fs.statSync(full);
  if(stat.isDirectory())for(const name of fs.readdirSync(full).sort()){if(name==='__pycache__')continue;visit(relative+'/'+name);}
  else if(stat.isFile())result[relative]=digest(fs.readFileSync(full));
 };
 for(const dir of ['src','public','scripts','tests'])visit(dir);
 for(const f of ROOT_INPUTS)visit(f);
 return Object.fromEntries(Object.entries(result).sort(([a],[b])=>a.localeCompare(b)));
}
export const dependencyDigest=(root=projectRoot)=>digest(JSON.stringify(dependencyInventory(root)));
export function readReviewEvidence(root=projectRoot,relative=EVIDENCE_PATH){
 assert.equal(relative,EVIDENCE_PATH,'Unexpected evidence file path');
 const target=ensureRegularPath(root,relative);assert(fs.statSync(target).isFile(),'Evidence must be a regular file');return fs.readFileSync(target);
}
export function assertManualRelease(root=projectRoot,env=process.env){
 const read=name=>JSON.parse(fs.readFileSync(ensureRegularPath(root,'src/data/'+name)));
 const config=read('site-config.json'),provenance=read('manual-provenance.json'),pages=read('manual-pages.json'),products=read('products.json');
 const requireApproval=!isLocalPreview(env);
 if(requireApproval&&config.productionApproved!==true)throw new Error('Production-indexable build is disabled for this unapproved regional template');
 const dependencyHash=dependencyDigest(root);
 let reviewEvidenceBytes=null,reviewEvidence=null;
 if(requireApproval&&provenance.independentReview?.status==='approved'){
  reviewEvidenceBytes=readReviewEvidence(root,provenance.independentReview.evidencePath);reviewEvidence=JSON.parse(reviewEvidenceBytes);
 }
 return validateManualContract(pages,provenance,fs.readFileSync(path.join(root,'src/data/manual-pages.json')),products,{requireApproval,reviewEvidence,reviewEvidenceBytes,dependencyHash,catalogBytes:fs.readFileSync(path.join(root,'src/data/products.json'))});
}
