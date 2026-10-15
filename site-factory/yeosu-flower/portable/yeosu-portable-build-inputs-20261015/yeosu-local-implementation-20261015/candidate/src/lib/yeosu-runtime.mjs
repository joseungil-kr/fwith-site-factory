import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {planDirectoryBannerSplit} from './directory-banner-split.mjs';
// npm runs from candidate; cwd stays stable when Astro bundles runtime into dist/.prerender.
export const workspace=pathToFileURL(path.resolve(process.cwd(),'../..')+path.sep);
export const inputRoot=new URL('yeosu-customer-copy-20261014/',workspace);
export const SPEC_SHA='b7fd276f969d473b60619cafca6ed160a442fdf5feb36b1bb1addccdaeb96b1f';
export const sha256=b=>crypto.createHash('sha256').update(b).digest('hex');
export const specBytes=fs.readFileSync(new URL('yeosu-page-spec-addendum-20261015/page-spec-addendum.ko.json',workspace));
export const spec=JSON.parse(specBytes);
export const previewConfig=Object.freeze({mode:'private-local-preview',origin:null,domain:null,canonical:null,productionEnabled:false,coreHubLaunchStatus:'NOT_ASSESSED',fullLaunchStatus:'NOT_ASSESSED'});
export function assertBoundary(config=previewConfig,env=process.env){
 if(JSON.stringify(config)!==JSON.stringify(previewConfig))throw new Error('Yeosu private boundary changed');
 for(const key of ['SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION'])if(env[key])throw new Error(`Yeosu private boundary: ${key} must not be set`);
 return true;
}
export function verifyInputs(){
 if(sha256(specBytes)!==SPEC_SHA)throw new Error('Reviewed specification digest mismatch');
 for(const b of spec.sourceBindings){const bytes=fs.readFileSync(new URL(b.file,inputRoot));if(bytes.length!==b.bytes||sha256(bytes)!==b.sha256)throw new Error(`Reviewed source changed: ${b.file}`);}
 const review=JSON.parse(fs.readFileSync(new URL('yeosu-page-spec-addendum-20261015/scoped-copy-review.json',workspace)));
 const projection=Object.fromEntries(spec.newCopyRequiringIndependentReview.onlyNewCustomerCopy.slice().sort().map(path=>[path,path.split('.').reduce((v,k)=>v[k],spec.newCopyRequiringIndependentReview)]));
 if(review.specSHA256!==SPEC_SHA||review.reviewResult!=='PASS_FOR_NINE_FIELDS_ONLY'||sha256(JSON.stringify(projection))!==review.projectionSHA256)throw new Error('Nine-field copy review binding changed');
 for(const [key,binding] of [['productBinding',spec.productBinding],['faqBinding',spec.faqBinding]]){
  const bytes=fs.readFileSync(new URL('drafts/yeosu-jeonnam-hospital-funeral.ko.md',inputRoot));const span=bytes.subarray(binding.span.startByteInclusive,binding.span.endByteExclusive);
  if(span.length!==binding.span.bytes||sha256(span)!==binding.span.sha256)throw new Error(`${key} source byte span changed`);
 }
 return true;
}
export function mapHref(href){return href==='yeosu-jeonnam-hospital-funeral.ko.md'?'/regions/yeosu-jeonnam-hospital-funeral-wreath/':href;}
export function inline(text){
 const result=[];let end=0;const pattern=/\[([^\]]+)\]\(([^)]+)\)/g;
 for(const match of text.matchAll(pattern)){if(match.index>end)result.push({kind:'text',text:text.slice(end,match.index)});const href=mapHref(match[2]);if(!/^(https:\/\/|tel:18440644$|\/regions\/)/.test(href))throw new Error('Unapproved inline destination');result.push({kind:'link',text:match[1],href});end=match.index+match[0].length;}
 if(end<text.length)result.push({kind:'text',text:text.slice(end)});
 if(result.some(t=>/[<>]/.test(t.text)))throw new Error('Unapproved inline HTML');return result;
}
// Strict parser of the reviewed grammar only; original files are read, never rewritten or copied.
export function parseDraft(markdown){
 const result={h1:null,opening:[],sections:[]};let blocks=result.opening;let products=false;let card=null;
 const lines=markdown.trim().split('\n');
 for(let i=0;i<lines.length;i++){
  const line=lines[i];if(!line.trim())continue;
  if(line==='# '+result.h1)throw new Error('Duplicate H1');
  if(line.startsWith('# ')){if(result.h1||i!==0)throw new Error('Expected exactly one initial H1');result.h1=line.slice(2);continue;}
  if(line.startsWith('## ')){if(products)throw new Error('Unclosed product region');const section={heading:line.slice(3),blocks:[]};result.sections.push(section);blocks=section.blocks;continue;}
  if(line==='<!-- PRODUCT_CARDS_START -->'){if(products)throw new Error('Nested product region');products=true;const group={kind:'products',cards:[]};blocks.push(group);continue;}
  if(line==='<!-- PRODUCT_CARDS_END -->'){if(!products)throw new Error('Unopened product region');products=false;card=null;continue;}
  if(line.startsWith('### ')){if(products){card={kind:'product',heading:line.slice(4),blocks:[]};blocks.at(-1).cards.push(card);}else blocks.push({kind:'h3',text:line.slice(4)});continue;}
  const target=products?card?.blocks:blocks;if(!target)throw new Error('Product content before heading');
  const image=line.match(/^!\[([^\]]+)\]\(([^)]+)\)$/);
  if(image){const src=spec.productBinding.imageMappings[image[2]];if(!products||!src)throw new Error('Unapproved image');target.push({kind:'image',alt:image[1],src});continue;}
  if(line.startsWith('- ')){const items=[line.slice(2)];while(lines[i+1]?.startsWith('- '))items.push(lines[++i].slice(2));target.push({kind:'list',items});continue;}
  if(/^(#|<!--|!\[)/.test(line))throw new Error('Unsupported Markdown');
  let text=line;while(lines[i+1]&&lines[i+1].trim()&&!/^(#|<!--|- |!\[)/.test(lines[i+1]))text+='\n'+lines[++i];
  const action=text.match(/^\[([^\]]+)\]\(([^)]+)\)$/);target.push(action?{kind:'action',label:action[1],href:mapHref(action[2])}:{kind:'paragraph',text});
 }
 if(!result.h1||products)throw new Error('Incomplete draft');return result;
}
export const products=JSON.parse(fs.readFileSync(new URL('product-cards.json',inputRoot)));
export const banners=spec.sharedBannerBinding.assets.map(b=>({...b,id:b.variant,assetName:b.renderSrc.split('/').at(-1)}));
export const pages=spec.pages.map(p=>{
 const source=p.sourceFile?fs.readFileSync(new URL(p.sourceFile,inputRoot)):null;const copy=p.id==='support'?spec.newCopyRequiringIndependentReview.support:p.id==='not-found'?spec.newCopyRequiringIndependentReview.notFound:p;
 return {...p,title:copy.title,h1:copy.h1,metaDescription:copy.metaDescription,body:copy.body,sourceSHA:source?sha256(source):null,draft:source?parseDraft(source.toString('utf8')):null,breadcrumbs:p.breadcrumbs?.map(b=>({...b,label:b.label||spec.newCopyRequiringIndependentReview.support.breadcrumbLabel}))};
});
export const supportSummary=pages[0].draft.sections[0].blocks[0].text;
export const pageMap={...previewConfig,articleCount:1,primaryCount:2,supportCount:1,contentHtmlCount:3,technicalHtmlCount:1,allHtmlCount:4,previewIndexableCount:0,previewSitemapUrlCount:0,launchOrder:spec.launchOrder,pages:pages.map(p=>({id:p.id,path:p.path,role:p.role,sourceSHA:p.sourceSHA,robots:'noindex,follow',canonical:null,sitemapIncluded:false,mainMenuIncluded:['home','article'].includes(p.id),actualChildCount:p.id==='support'?1:0,marketingBannerCount:p.draft?3:0,coreHub:false}))};
export function validateRuntime(){
 assertBoundary();verifyInputs();
 if(spec.preview.origin!==null||spec.preview.productionModeEnabled!==false||pages.length!==4||spec.architecture.articleCount!==1||planDirectoryBannerSplit([1],false).enabled)throw new Error('Private scope mismatch');
 const article=pages.find(p=>p.id==='article');const cards=article.draft.sections.flatMap(s=>s.blocks.filter(b=>b.kind==='products').flatMap(b=>b.cards));
 if(cards.length!==4||products.map(p=>p.sku).join(',')!=='B201,B203,B205,B060')throw new Error('Product denominator mismatch');
 for(const [i,c] of cards.entries()){const p=products[i];if(c.heading!==`${p.name} ${p.sku}`||c.blocks[1].text!==p.priceLabel||c.blocks[2].href!==p.ctaHref||c.blocks[2].label!==p.ctaLabel)throw new Error('Product source projection mismatch');}
 const faq=article.draft.sections.find(s=>s.heading===spec.faqBinding.heading);
 for(const [i,f] of spec.faqBinding.items.entries()){if(faq.blocks[i*2].text!==f.question||sha256(faq.blocks[i*2+1].text)!==f.answerUTF8SHA256)throw new Error('FAQ source projection mismatch');}
 return true;
}
validateRuntime();
