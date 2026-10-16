import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
export const candidate=path.resolve(process.cwd());
if(!fs.existsSync(path.join(candidate,'src/lib/gangjin-runtime.mjs')))throw new Error('Run from Gangjin candidate root');
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
  "author/FULL-CUSTOMER-COPY.ko.md": "fe9f6c7457de52413f9c1fc26441a43468e3ae8bc19bd0e1d34a0f935e599bc1",
  "author/MANIFEST.json": "f7a3ac630294df2910b4fc9e5b1b414c6f1323b4b96edf1b05c14cb8cd774d01",
  "author/RENDER-STRUCTURE-PLAN.ko.md": "5a74ca61f23c229c2c2fb24806c2b250aa145264c6a103dfc25b3687f653c3d0",
  "author/customer-copy.json": "1477a7c9dc532e82d189edb5fe975ffdeded9cf5f876e2c4e070d4d1f23860ab",
  "author/display-copy.json": "a2d07fb553670de45dcb392c3405e61134e433beb286a6474d5143f12cb4b9dc",
  "author/draft-home.ko.md": "88074ff7bc6fa4085d58ba915354342b761e8dd02a7880a6721375fc68a33e0a",
  "research/MANIFEST.json": "dd00037f3de256a98055ed8ed84722771f1853c157d6a13984b22b7f62abc599",
  "review/MANIFEST.json": "2785295f91c96b99743cb8b77b1f43b314cbec81e347d7fc79db506b6fbd0319",
  "review/REVIEW.ko.md": "cfe151de3ec205568623a829b149603d1af71ec5943c32a750ec3526fd4b34d4",
  "review/VERDICT.json": "77c300af95ce3115813510de6edf621b396602a03599defd1b4c78aa574a33f1"
};

export function validateInputs(root=inputs){
 for(const [file,hash]of Object.entries(bound))if(sha(regularRead(root,file))!==hash)throw new Error('Accepted input changed: '+file);
 const review=JSON.parse(regularRead(root,'review/VERDICT.json'));
 if(review.status!=='PASS_LOCAL_RESEARCH_AND_CUSTOMER_COPY_ONLY'||review.customerCopySHA256!==bound['author/customer-copy.json']||review.sourceBodySHA256!==bound['author/draft-home.ko.md']||review.copyManifestSHA256!==bound['author/MANIFEST.json']||review.researchManifestSHA256!==bound['research/MANIFEST.json']||review.facilitySalesPages!=='HOLD_5'||review.blockingFindings.length||review.requiredCopyChanges.length||review.verdicts.implementationBuildDOM!=='NOT_PERFORMED'||review.bodyCharactersExcludingHeadingsIncludingWhitespace!==2991)throw new Error('Independent copy acceptance mismatch');
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
