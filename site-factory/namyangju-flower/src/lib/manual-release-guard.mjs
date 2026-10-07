import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {digest,validateManualContract} from './manual-contract.mjs';
export const projectRoot=fileURLToPath(new URL('../../',import.meta.url));
const excluded=new Set(['src/data/manual-provenance.json','src/data/manual-review-evidence.json','src/data/build-revision.json']);
export function dependencyInventory(root){
 const result={};
 function visit(relative){const absolute=path.join(root,relative);for(const entry of fs.readdirSync(absolute,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name))){const rel=relative+'/'+entry.name;if(excluded.has(rel))continue;assert(!entry.isSymbolicLink(),'Dependency symlinks forbidden');if(entry.isDirectory())visit(rel);else if(entry.isFile())result[rel]=digest(fs.readFileSync(path.join(root,rel)));}}
 for(const dir of ['src','public','scripts'])visit(dir);
 for(const file of ['astro.config.mjs','package.json'])result[file]=digest(fs.readFileSync(path.join(root,file)));
 return Object.fromEntries(Object.entries(result).sort(([a],[b])=>a.localeCompare(b)));
}
export function dependencyDigest(root){return digest(JSON.stringify(dependencyInventory(root)));}
export function isPrivatePreview(env,origin){
 const url=new URL(origin);return env.MANUAL_LOCAL_PREVIEW==='true'&&env.SITE_INDEXABLE==='false'&&['http:','https:'].includes(url.protocol)&&['localhost','127.0.0.1','[::1]'].includes(url.hostname)&&!url.username&&!url.password&&url.pathname==='/'&&!url.search&&!url.hash&&origin===url.origin;
}
export function assertManualRelease(root=projectRoot,env=process.env){
 const read=name=>JSON.parse(fs.readFileSync(path.join(root,'src/data',name)));
 const config=read('site-config.json'),provenance=read('manual-provenance.json'),pages=read('manual-pages.json'),products=read('products.json');
 const origin=env.SITE_URL||config.previewUrl;
 const protectedBuild=!isPrivatePreview(env,origin);
 if(env.SITE_INDEXABLE==='true')assert.equal(config.productionApproved,true,'Original production approval absent');
 const bytes=fs.readFileSync(path.join(root,'src/data/manual-pages.json'));
 const actualDependencies=dependencyDigest(root);
 assert.equal(actualDependencies,provenance.dependencyHash,'Source/catalog/renderer/assets digest drift');
 for(const [file,hash] of Object.entries(provenance.originalFileSha256))assert.equal(digest(fs.readFileSync(path.join(root,'src/data',file))),hash,'Frozen file drift: '+file);
 let evidenceBytes=null;
 if(protectedBuild&&provenance.independentReview?.status==='approved'){
  const rel=provenance.independentReview.evidencePath;
  assert.equal(rel,'src/data/manual-review-evidence.json','Unexpected evidence file path');
  const target=path.join(root,rel);assert(fs.existsSync(target),'Evidence file does not exist');assert.equal(fs.realpathSync(target),target,'Evidence symlink forbidden');evidenceBytes=fs.readFileSync(target);
 }
 return validateManualContract(pages,provenance,bytes,products,{indexable:protectedBuild,reviewEvidenceBytes:evidenceBytes,dependencyHash:actualDependencies});
}
