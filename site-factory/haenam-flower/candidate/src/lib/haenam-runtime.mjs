import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
export const candidate=path.resolve(process.cwd());
if(!fs.existsSync(path.join(candidate,'src/lib/haenam-runtime.mjs')))throw new Error('Run from Haenam candidate root');
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
  "author/FULL-CUSTOMER-COPY.ko.md": "4eda9b2ce57639a681d17f9f207254c5a6366b949d716c74393170b2322733b0",
  "author/MANIFEST.json": "25ba5959d0a22e0e8da5766f8f077a123897cab0fdb91f8f25ad09967a7e38c5",
  "author/RENDER-STRUCTURE-PLAN.ko.md": "e45e31a89a06c8e16f3b49627880f0bfe5ab0d355a480aae5f6d5235b875dacf",
  "author/customer-copy.json": "64d5f3ffaad8b3f40c4b3ca5c1bf1a689938dae59e167518b61ea2985e9e267a",
  "author/display-copy.json": "4571da7eea2977dbf1f6db85476c91758c17a49186fe8a656f821f12c326231e",
  "author/draft-home.ko.md": "d09202a06ed991794e04770da0eb15a69ec88ee35e30c38fa8b00be2e0082cba",
  "research/MANIFEST.json": "d148bf08b4455bd1a7ec73f79b39a5dadebfc6d73eec8a7d91e27b0ebc696b55",
  "review/MANIFEST.json": "fe3580498c3bbfdf8fd7604872fe0e5920c5503e1f27dc723cbe967f152b32df",
  "review/independent-review.json": "26451245041cdc0b96831ce4171ec371522dc4f939a402ecb3ca80dcecf506b0",
  "review/independent-review.ko.md": "dd24d9d1246698bf9bb04c1cf677f127df0dd2d0e2891668c77b101a4203e7d4"
};

export function validateInputs(root=inputs){
 for(const [file,hash]of Object.entries(bound))if(sha(regularRead(root,file))!==hash)throw new Error('Accepted input changed: '+file);
 const review=JSON.parse(regularRead(root,'review/independent-review.json'));
 if(review.verdict!=='ACCEPTED_AS_LOCAL_RESEARCH_AND_COPY_INPUT_ONLY'||review.releaseApproval!==false||review.buildDOMVisualPublicVerification!=='NOT_PERFORMED'||review.localCopyBlockers.length||review.region.order!==44||review.region.code!=='12790'||review.bodyLength.characters!==2873)throw new Error('Independent copy acceptance mismatch');
 for(const [name,digest]of Object.entries(review.copyDigests))if(bound['author/'+name]!==digest)throw new Error('Independent copy digest mismatch');
 for(const packet of review.frozenPackageBindings){const role=packet.root==='haenam-research-preparation-20261016'?'research':packet.root==='haenam-customer-copy-20261016'?'author':null;if(!role||bound[role+'/MANIFEST.json']!==packet.manifestSHA256)throw new Error('Independent packet binding mismatch');}
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
