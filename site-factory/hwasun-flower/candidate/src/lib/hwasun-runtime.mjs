import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
export const candidate=path.resolve(process.cwd());
if(!fs.existsSync(path.join(candidate,'src/lib/hwasun-runtime.mjs')))throw new Error('Run from Hwasun candidate root');
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
  "author/FULL-CUSTOMER-COPY.ko.md": "ddc7ab20a7ab79e1ff2f8b66e29ec098ac2df41cc835ca6b9b139ff32e6abcc5",
  "author/MANIFEST.json": "94e0a40e7c72b816bef7dcdf079240c461a0a39c03ed36a35af90947443290fd",
  "author/RENDER-STRUCTURE-PLAN.ko.md": "694feebf9059153d186cf162ea37be675f68209f04c2288d0aacf43bdfe50ce9",
  "author/customer-copy.json": "25297aba5604718ca425c2844cc63b70fad40e0bad1c464514db4ec3ef5a9cdb",
  "author/display-copy.json": "128be3522eac01260a93eac4734f88314f5cddb15988fd6ccb75503761ec7593",
  "author/draft-home.ko.md": "d02f02b9944fc7d070f85ec7f70fdb240b41b5972a154262fe93b98743195761",
  "review/MANIFEST.json": "13b57f8c913422ad504c66dbf238d984a37dbc849942249edf6d0215fb79f551",
  "review/RESULT.json": "f0ba6c6519d4809819ee89db0a59d2f5e64874f34b5e7fe6fe294982604b3a56",
  "review/REVIEW.ko.md": "87fd39069c1c5093a09ec1143ab06802304b5814f03b2dac13eb5e98317a2c12"
};

export function validateInputs(root=inputs){
 for(const [file,hash]of Object.entries(bound))if(sha(regularRead(root,file))!==hash)throw new Error('Accepted input changed: '+file);
 const review=JSON.parse(regularRead(root,'review/RESULT.json'));
 if(review.verdict!=='ACCEPTED_LOCAL_COPY_R2_ONLY'||review.acceptedSourceSHA256['customer-copy.json']!==bound['author/customer-copy.json']||review.acceptedSourceSHA256['draft-home.ko.md']!==bound['author/draft-home.ko.md']||review.acceptedSourceSHA256['display-copy.json']!==bound['author/display-copy.json']||review.r2ManifestSHA256!==bound['author/MANIFEST.json']||review.renderedHTMLVerified!==false||review.sitePixelsVerified!==false||review.facilityPagesHeld!==4)throw new Error('Independent copy acceptance mismatch');
 const manuscript=JSON.parse(regularRead(root,'author/customer-copy.json'));
 if(manuscript.sourceSHA256['draft-home.ko.md']!==bound['author/draft-home.ko.md']||manuscript.sourceSHA256['display-copy.json']!==bound['author/display-copy.json'])throw new Error('Manuscript source binding mismatch');
 return Object.keys(bound).length;
}
assertBoundary();validateInputs();
export const copy=JSON.parse(regularRead(author,'customer-copy.json'));
export const display=JSON.parse(regularRead(author,'display-copy.json'));
// FAQ IDs are technical presentation identifiers, absent from the immutable source schema.
export const faqs=copy.faq.map((f,i)=>({...f,id:`question-${i+1}`}));
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
