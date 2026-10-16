import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
export const candidate=path.resolve(process.cwd());
if(!fs.existsSync(path.join(candidate,'src/lib/goheung-runtime.mjs')))throw new Error('Run from Goheung candidate root');
export const inputs=path.resolve(candidate,'../inputs');
export const author=path.join(inputs,'author');
export const reviewer=path.join(inputs,'review');
export const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
export function regularRead(root, relative) {
 if(path.isAbsolute(relative)||relative.split(/[\\/]/).includes('..')) throw new Error('Unsafe input path');
 const target=path.join(root,relative);
 let cursor=root;
 for(const segment of relative.split('/')) {cursor=path.join(cursor,segment);if(fs.lstatSync(cursor).isSymbolicLink())throw new Error('Symlink input forbidden');}
 if(!fs.statSync(target).isFile())throw new Error('Regular file required');
 return fs.readFileSync(target);
}
export function assertBoundary(env=process.env) {
 const prohibited=['SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION','SITE_RELEASE_MODE','SITE_INDEXABLE','SITE_RELEASE_BINDING_PATH','SITE_RELEASE_BINDING_SHA','CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID','PRODUCTION_APPROVED','OWNERSHIP_VERIFIED','INDEXNOW_ENABLED','PUBLIC_APPROVED','INDEXNOW_KEY','INDEXNOW_API_KEY','PUBLIC_INDEXNOW_KEY','CF_API_TOKEN','CLOUDFLARE_API_KEY'];
 for(const name of prohibited)if(env[name]!==undefined)throw new Error(`Private-only build rejects ${name}`);
}
export const bound={
  "author/MANIFEST.json": "993127577e4589cb7e745211ca7a682967c990079999e5c82272fa573b8a996c",
  "author/RENDER-STRUCTURE-PLAN.ko.md": "108f3825851d1548e729a46294d92da6a18ecd00aab0587cbfb1276dd57800b1",
  "author/customer-copy.json": "adf9c59c6b9d7cfcb8c62fe0a4a990c2e121067949fba9764cbf296daca5666e",
  "author/display-copy.json": "c76865f050702d9e429a5d02b705178bbd6b7f0578dd4b061073a02341c763bf",
  "author/draft-home.ko.md": "5099db69093d522b54b34399d330273af015f643bdcfc9d26363174ef4bbd5dc",
  "review/INDEPENDENT-REVIEW.ko.md": "98dd1577d003cc03edcb80ad93289f6b9452de130208ed76a7c57db3eb1399d7",
  "review/REVIEW-MANIFEST.json": "3c8c097e52741819c048e67fb6a012ad6a0adcfc9bff73f08a0122f004c552a6",
  "review/VERDICT.json": "33ebdf54713df7b1271a921b6cd44f5a4abcb986ad1ebe36016727dc88626042"
};

export function validateInputs(root=inputs){
 for(const [file,hash]of Object.entries(bound))if(sha(regularRead(root,file))!==hash)throw new Error('Accepted input changed: '+file);
 const review=JSON.parse(regularRead(root,'review/VERDICT.json'));
 if(review.status!=='ACCEPTED_LOCAL_COPY_ONLY'||review.copySha256!==bound['author/customer-copy.json']||review.publicationComplete!==false)throw new Error('Independent copy acceptance mismatch');
 return Object.keys(bound).length;
}
assertBoundary();validateInputs();
export const copy=JSON.parse(regularRead(author,'customer-copy.json'));
export const display=copy.display;
export const ui=display.siteUI;
export const products=display.products;
export const assetBinding=JSON.parse(regularRead(candidate,'asset-render-binding.json'));
export const banners=assetBinding.assets.filter(a=>a.role==='banner').map(a=>({...a,id:a.id.replace('flower-',''),width:a.dimensions[0],height:a.dimensions[1]}));
export function validateAssets(root=candidate){
 if(assetBinding.assets.length!==7||assetBinding.newBinaryBlobs!==0||assetBinding.newCrops!==0)throw new Error('Exactly seven unchanged assets required');
 const ids=new Set();
 for(const a of assetBinding.assets){
  if(ids.has(a.id))throw new Error('Duplicate asset');ids.add(a.id);
  const p=products.find(p=>a.id===p.sku+'-photo'),b=display.sharedBanners.find(b=>a.id==='flower-'+b.id);
  if(!p&&!b)throw new Error('Unknown asset');
  const sourceHash=p?p.photoSHA256:b.sha256,alt=p?p.photoAlt:b.alt;
  const expectedSrc=p?'/images/products/'+p.sku+'.jpg':'/images/shared-banners/'+b.filename;
  if(a.sha256!==sourceHash||a.alt!==alt||a.renderSrc!==expectedSrc||a.role!==(p?'product':'banner')||a.mime!==(p?'image/jpeg':'image/webp')||JSON.stringify(a.dimensions)!==JSON.stringify(p?[p.photoWidth,p.photoHeight]:[b.width,b.height]))throw new Error('Approved asset binding changed');
  const bytes=regularRead(root,'public'+a.renderSrc);
  if(bytes.length!==a.bytes||sha(bytes)!==sourceHash)throw new Error('Approved asset bytes changed');
  const git=createHash('sha1').update(Buffer.from(`blob ${bytes.length}\0`)).update(bytes).digest('hex');
  if(git!==a.existingGitBlobSHA)throw new Error('Existing Git blob changed');
 }
}
validateAssets();
export function blocks(markdown){
 const result=[];let para=[],list=[];
 const flushP=()=>{if(para.length){result.push({type:'p',text:para.join('\n')});para=[];}};
 const flushL=()=>{if(list.length){result.push({type:'ul',items:list});list=[];}};
 for(const line of markdown.split('\n')){if(!line.trim()){flushP();flushL();}else if(line.startsWith('- ')){flushP();list.push(line.slice(2));}else{flushL();if(line.startsWith('#'))throw new Error('Heading not permitted inside plain section renderer');para.push(line);}}
 flushP();flushL();return result;
}
export const sections=copy.sections.filter(s=>s.id!=='questions').map(s=>({...s,blocks:blocks(s.markdown)}));
export const homePage={id:'home',title:display.page.title,description:display.page.description};
export const notFoundPage={id:'not-found',title:display.notFoundCopyPlan.title,description:display.notFoundCopyPlan.body};
