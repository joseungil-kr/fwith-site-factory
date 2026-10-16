import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
export const candidate=path.resolve(process.cwd());
if(!fs.existsSync(path.join(candidate,'src/lib/jangheung-runtime.mjs')))throw new Error('Run from Jangheung candidate root');
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
  "author/FULL-CUSTOMER-COPY.ko.md": "ebe30e96d8f59b5e57298134048295e3ca5b1e290e10d3a9a1f0e823c3fce33f",
  "author/MANIFEST.json": "d584dc6808b767c5d36c51715d31ec359f16a3da9806a94bd727e334247cde74",
  "author/RENDER-STRUCTURE-PLAN.ko.md": "3984d89526f649388276fc8dfde575641344bee846a4570f29c328f7b473ea2a",
  "author/customer-copy.json": "f57ff99f45b63ff35a74dcff190b32212dd24479ce8d881054d354e48c98c8aa",
  "author/display-copy.json": "0c2d9424e489ca044584252ebcfc06b86886ef7baab48acecc9c0381da5557a4",
  "author/draft-home.ko.md": "e478f449801b741f2d2db1c2029c449cfade6e66ed22147d66b423c69ef5e33d",
  "derived/FULL-CUSTOMER-COPY.ko.md": "34bae877bfaa3c1b428611369ed97e5aae175624465d468424f59134ccb1e820",
  "derived/MANIFEST.json": "dec583a8c9343c3634d60e64e509f9e94a4129cd9cf1e394f9dd300ed287a0ee",
  "derived/REVISION.json": "d0ae5bb64f482093c527d418e7aae58724ff271272a30db533911cc4529dc849",
  "derived/customer-copy.json": "cf5a2c4bbbec131181bd66a2e40a59dca5a0935803f83d2d951f583613cab301",
  "derived/draft-home.ko.md": "34d3d7ff6c40c09f24b44df2e05580fdc3d0f3fc0426e43b62249e311810994d",
  "research/FINAL-HANDOFF.json": "1b1e2360f6137783cb2234e123f4fa66a8eaa61a19a6bfff4010bdd28cb13d12",
  "research/MANIFEST.json": "48e5bb1cd8d228c91a7082b1a71ae40330d14bd6a93aa4ddf233fb7e3a1ffd47",
  "review/OUTPUT-MANIFEST.json": "9a3382b5fa96c64695a6d53be9086e48558b9a9a51f95ad4717bd16e58dda6f4",
  "review/REVIEW.json": "a8f7995cba1d5affcdb376255c41d881a8e08dc8df09f1939d24e2ab291d6f87",
  "review/REVIEW.ko.md": "1750273dc958722f986c91619ced765c124fc9533426f1062bb1e324ec7a582b"
};

export function validateInputs(root=inputs){
 for(const [file,hash]of Object.entries(bound))if(sha(regularRead(root,file))!==hash)throw new Error('Accepted input changed: '+file);
 const review=JSON.parse(regularRead(root,'review/REVIEW.json'));
 if(review.overall!=='PASS_LOCAL_COPY_ONLY'||review.revision!=='r3'||review.independentOfAuthor!==true||review.fileDigests['customer-copy.json']!==bound['author/customer-copy.json']||review.fileDigests['draft-home.ko.md']!==bound['author/draft-home.ko.md']||review.fileDigests['display-copy.json']!==bound['author/display-copy.json']||review.authorPacketManifestSHA256!==bound['author/MANIFEST.json']||review.researchPacketManifestSHA256!==bound['research/MANIFEST.json']||review.actualRenderPerformed!==false||review.publicHttpPerformed!==false||review.facilityPages!=='HOLD_5'||review.openRequiredFindingIds.length||review.openOptionalFindingIds.length)throw new Error('Independent copy acceptance mismatch');
 const handoff=JSON.parse(regularRead(root,'research/FINAL-HANDOFF.json'));
 if(handoff.reviewJSONSHA256!==bound['review/REVIEW.json']||handoff.code!=='12770'||handoff.order!==42||handoff.bodyCharactersExcludingHeadingsIncludingWhitespace!==2847||handoff.FAQCount!==4||handoff.facilityDetailHOLDCount!==5)throw new Error('Final handoff mismatch');
 const manuscript=JSON.parse(regularRead(root,'author/customer-copy.json'));
 if(manuscript.sourceSHA256['draft-home.ko.md']!==bound['author/draft-home.ko.md']||manuscript.sourceSHA256['display-copy.json']!==bound['author/display-copy.json'])throw new Error('Manuscript source binding mismatch');
 const derived=JSON.parse(regularRead(root,'derived/customer-copy.json'));
 const baseline=JSON.parse(regularRead(root,'author/customer-copy.json'));
 const original='아래 네 상품은 모두 3단 화환이며',replacement='이 페이지의 네 상품은 모두 3단 화환이며';
 const section=baseline.sections.find(s=>s.id==='locations');
 if(section.markdown.split(original).length!==2)throw new Error('Unique location correction anchor required');
 section.markdown=section.markdown.replace(original,replacement);
 baseline.sourceSHA256['draft-home.ko.md']=bound['derived/draft-home.ko.md'];
 if(JSON.stringify(derived)!==JSON.stringify(baseline))throw new Error('Only the exact reviewed-scope location transformation is permitted');
 for(const name of ['draft-home.ko.md','FULL-CUSTOMER-COPY.ko.md']){
  const text=regularRead(root,'author/'+name).toString();
  if(text.split(original).length!==2||regularRead(root,'derived/'+name).toString()!==text.replace(original,replacement))throw new Error('Derived manuscript exceeds single-phrase scope');
 }
 return Object.keys(bound).length;
}
assertBoundary();validateInputs();
export const copy=JSON.parse(regularRead(inputs,'derived/customer-copy.json'));
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
