import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {planDirectoryBannerSplit} from './directory-banner-split.mjs';
export const bundle=pathToFileURL(path.resolve(process.cwd(),'..')+path.sep);
export const inputRoot=new URL('inputs/reviewed-copy/',bundle);
export const sha256=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=(name)=>JSON.parse(fs.readFileSync(new URL(name,inputRoot)));
export const home=read('home-copy.json'),detail=read('detail-copy.json'),products=read('product-cards.json'),metadata=read('customer-copy-metadata.json'),plan=read('render-plan.json');
export const copySHA={home:sha256(fs.readFileSync(new URL('home-copy.json',inputRoot))),article:sha256(fs.readFileSync(new URL('detail-copy.json',inputRoot)))};
export const ui=JSON.parse(fs.readFileSync(new URL('candidate/src/data/ui-copy.json',bundle)));
export const previewConfig=Object.freeze({mode:'private-local-preview',origin:null,domain:null,canonical:null,productionEnabled:false,coreHubLaunchStatus:'NOT_ASSESSED',fullLaunchStatus:'NOT_ASSESSED'});
export function assertBoundary(config=previewConfig,env=process.env){
 if(JSON.stringify(config)!==JSON.stringify(previewConfig))throw new Error('Suncheon private boundary changed');
 for(const key of ['SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION'])if(env[key])throw new Error(`Suncheon private boundary: ${key} must not be set`);
 return true;
}
export function verifyInputs(){
 const requiredBytes=fs.readFileSync(new URL('inputs/required-originals.json',bundle));
 if(sha256(requiredBytes)!=='b4eb7bda5f666334286172fc1f8e95dbf72f7877b58a972813819d058d68add0')throw new Error('Required originals manifest changed');
 const rows=JSON.parse(requiredBytes);
 for(const b of rows){const data=fs.readFileSync(new URL(b.path,bundle));if(data.length!==b.bytes||sha256(data)!==b.sha256)throw new Error('Required original changed: '+b.path);}
 const review=read('reviews/final-review-binding.json');
 if(review.outcome!=='ACCEPTED_LOCAL_COPY_ONLY'||review.reviewedFiles.length!==7)throw new Error('Reviewed copy not accepted');
 for(const b of review.reviewedFiles){const data=fs.readFileSync(new URL(b.path,inputRoot));if(data.length!==b.bytes||sha256(data)!==b.sha256)throw new Error('Reviewed copy changed: '+b.path);}
 const binding=read('final-review-binding.json');
 if(sha256(fs.readFileSync(new URL(binding.independentReview.report,inputRoot)))!==binding.independentReview.reportSHA256||sha256(fs.readFileSync(new URL(binding.independentReview.binding,inputRoot)))!==binding.independentReview.bindingSHA256)throw new Error('Independent review binding changed');
 const scopedBytes=fs.readFileSync(new URL('inputs/ui-copy-review.json',bundle));
 if(sha256(scopedBytes)!=='3c033aa31df1793247324d4b31e58b7276659936fbb65f8529e0ea25f9fa3339')throw new Error('Scoped review bytes changed');
 const scoped=JSON.parse(scopedBytes);
 if(scoped.outcome!=='ACCEPTED_SCOPED_UI_COPY_ONLY'||scoped.uiCopySHA256!==sha256(fs.readFileSync(new URL('candidate/src/data/ui-copy.json',bundle))))throw new Error('Scoped UI review changed');
 return true;
}
export const detailPath='/regions/suncheon-stcarollo-funeral-wreath/';
export function mapHref(href){if(href==='suncheon-stcarollo-funeral.ko.md')return detailPath;if(href==='suncheon-stcarollo-funeral.ko.md#출처-및-확인-정보')return detailPath+'#sources';throw new Error('Unapproved local destination: '+href);}
export const banners=plan.commonBanners.map(b=>({...b,id:b.variant,renderSrc:'/images/shared-banners/'+b.assetName}));
export const pages=[{id:'home',path:'/',role:'primary-home',title:metadata.home.title,description:metadata.home.description,h1:home.h1},{id:'article',path:detailPath,role:'primary-article',title:metadata.detail.title,description:metadata.detail.description,h1:detail.h1},{id:'support',path:'/regions/',role:'support-navigation',...ui.support},{id:'not-found',path:'/404.html',role:'technical-404',...ui.notFound}];
export const pageMap={...previewConfig,articleCount:1,primaryCount:2,supportCount:1,contentHtmlCount:3,technicalHtmlCount:1,allHtmlCount:4,previewIndexableCount:0,previewSitemapUrlCount:0,launchOrder:{Mokpo:26,Yeosu:27,Suncheon:28,MokpoStillPending:true,YeosuStillPending:true,SuncheonIndependentPreparationOnly:true},pages:pages.map(p=>({...p,robots:'noindex,follow',canonical:null,sitemapIncluded:false,mainMenuIncluded:['home','article'].includes(p.id),actualChildCount:p.id==='support'?1:0,marketingBannerCount:['home','article'].includes(p.id)?3:0,coreHub:false}))};
export function validateRuntime(){
 assertBoundary();verifyInputs();
 if(metadata.region.code!=='12150'||metadata.region.order!==28||metadata.publication.domain!==null||metadata.publication.canonical!==null||metadata.publication.publicRoutes!==null)throw new Error('Input private scope changed');
 if(!plan.renderSourceContract.runtimeCanonical.startsWith('Structured JSON only:')||!plan.faq.alwaysVisibleText||plan.faq.accordion)throw new Error('JSON sole-render contract changed');
 if(pages.length!==4||detail.faq.length!==3||new Set(detail.faq.map(f=>f.question)).size!==3||planDirectoryBannerSplit([1],false).enabled)throw new Error('Page or FAQ denominator changed');
 if(products.map(p=>p.sku).join(',')!=='B201,B203,B205,B060')throw new Error('Product denominator changed');
 for(const [i,p] of products.entries())if(p.ctaHref!==plan.links.productDestinations[i].url||sha256(fs.readFileSync(new URL('candidate/public/images/products/'+p.sku+'.jpg',bundle)))!==p.photoSHA256)throw new Error('Product contract changed');
 for(const b of banners)if(sha256(fs.readFileSync(new URL('candidate/public'+b.renderSrc,bundle)))!==b.sha256||b.width!==1774||b.height!==887||b.alt.split('1844-0644').length!==2)throw new Error('Banner contract changed');
 if(detail.sections.find(s=>s.id==='products').productCardsAfterParagraph!==3)throw new Error('Product card insertion changed');
 return true;
}
validateRuntime();
