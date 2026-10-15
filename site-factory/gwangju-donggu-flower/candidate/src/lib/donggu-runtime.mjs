import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {isDeepStrictEqual} from 'node:util';
export const BUNDLE=path.resolve(process.cwd(),'..');
export const INPUT=path.join(BUNDLE,'inputs/reviewed-copy');
export const sha256=b=>crypto.createHash('sha256').update(b).digest('hex');
export const PIN=JSON.parse(fs.readFileSync(path.join(BUNDLE,'candidate/src/data/input-binding.json')));
export const EXPECTED_REQUIRED_SHA='20b5944750be6fe3d897d2eb0a0d266a1c6f13972a2d5fcc6a6d13b3e6be7230';
export const EXPECTED_COPY_SHA='9f4643d1aa73945983497c953296716bbe0449ce93960a1a3427a6a6933d7687';
const read=name=>JSON.parse(fs.readFileSync(path.join(INPUT,name)));
export const copy=read('customer-copy.json'),home=copy.home,detail=copy.detail,products=copy.productCards,ui=copy.sharedUI,plan=read('render-plan.json');
export const copySHA={home:EXPECTED_COPY_SHA,article:EXPECTED_COPY_SHA,support:EXPECTED_COPY_SHA,'not-found':EXPECTED_COPY_SHA};
export const previewConfig=Object.freeze({mode:'private-local-preview',origin:null,domain:null,canonical:null,productionEnabled:false,coreHubLaunchStatus:'NOT_ASSESSED',fullLaunchStatus:'NOT_ASSESSED',crossRegionPublicationPrerequisites:false});
export function assertBoundary(config=previewConfig,env=process.env){
 if(!isDeepStrictEqual(config,previewConfig))throw new Error('Donggu private boundary changed');
 for(const key of ['SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION','SITE_RELEASE_MODE','SITE_INDEXABLE','SITE_RELEASE_BINDING_PATH','SITE_RELEASE_BINDING_SHA256','CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID'])if(env[key])throw new Error('Donggu private boundary: '+key+' must not be set');return true;
}
function regular(root,relative){
 if(typeof relative!=='string'||path.isAbsolute(relative)||relative.split('/').some(x=>!x||x==='.'||x==='..'||x.startsWith('.')))throw new Error('Unsafe input path');
 const file=path.resolve(root,relative);if(!file.startsWith(path.resolve(root)+path.sep))throw new Error('Input path escape');
 let current=root;for(const part of relative.split('/')){current=path.join(current,part);if(fs.lstatSync(current).isSymbolicLink())throw new Error('Input symlink forbidden');}
 if(!fs.lstatSync(file).isFile())throw new Error('Input regular file required');return fs.readFileSync(file);
}
export function verifyInputs(root=BUNDLE){
 const raw=regular(root,'inputs/required-originals.json');if(sha256(raw)!==EXPECTED_REQUIRED_SHA)throw new Error('Required originals manifest changed');
 const rows=JSON.parse(raw);if(rows.length!==27||new Set(rows.map(r=>r.path)).size!==27)throw new Error('Required originals denominator changed');
 for(const r of rows){const b=regular(root,r.path);if(b.length!==r.bytes||sha256(b)!==r.sha256)throw new Error('Required original changed: '+r.path);}
 const inventory=[];function scan(dir){for(const d of fs.readdirSync(dir,{withFileTypes:true})){if(d.name.startsWith('.')||d.isSymbolicLink())throw new Error('Unexpected hidden or symlink input');const f=path.join(dir,d.name);if(d.isDirectory())scan(f);else inventory.push(path.relative(root,f).split(path.sep).join('/'));}}
 scan(path.join(root,'inputs'));const want=['inputs/required-originals.json',...rows.filter(r=>r.path.startsWith('inputs/')).map(r=>r.path)].sort();if(!isDeepStrictEqual(inventory.sort(),want))throw new Error('Unexpected input file');
 const binding=JSON.parse(regular(root,'inputs/reviewed-copy/reviews/implementation-review-binding.json'));
 if(binding.result!=='PASS_EXACT_FINAL_COPY_ONLY'||binding.mandatoryChangesRemaining!==0||binding.canonicalCopySHA256!==EXPECTED_COPY_SHA)throw new Error('Independent copy review not accepted');
 for(const r of binding.boundCopyFiles){const name=r.path.replace(/^donggu-customer-copy-20261015\//,'');const b=regular(root,'inputs/reviewed-copy/'+name);if(b.length!==r.bytes||sha256(b)!==r.sha256)throw new Error('Review file changed');}
 if(sha256(regular(root,'inputs/reviewed-copy/reviews/independent-review-r2.json'))!==binding.reviewSHA256)throw new Error('Independent review report changed');return true;
}
export const routes=Object.fromEntries(plan.pages.map(p=>[p.id,p.proposedPath]));
export const detailPath=routes.detail;
export function mapTarget(value){if(!value||typeof value.href!=='string'||!['/',detailPath,detailPath+'#sources'].includes(value.href))throw new Error('Unapproved target');return value.href;}
export const banners=plan.commonBanners.map(b=>({...b,id:b.variant,alt:copy.sharedBannerAlt[b.variant],renderSrc:b.publicPath}));
export const pages=[{id:'home',copyKey:'home',role:'primary-home',...home,path:routes.home},{id:'article',copyKey:'detail',role:'primary-article',...detail,id:'article',path:detailPath},{id:'support',copyKey:'support',role:'support-navigation',...copy.support,path:routes.support},{id:'not-found',copyKey:'notFound',role:'technical-404',...copy.notFound,path:routes.notFound}];
export const pageMap={...previewConfig,articleCount:1,primaryCount:2,supportCount:1,contentHtmlCount:3,technicalHtmlCount:1,allHtmlCount:4,previewIndexableCount:0,previewSitemapUrlCount:0,nationalSelectionOrder:31,pages:pages.map(p=>({id:p.id,copyKey:p.copyKey,path:p.path,role:p.role,title:p.title,description:p.description,h1:p.h1,robots:'noindex,nofollow,noarchive',canonical:null,sitemapIncluded:false,mainMenuIncluded:['home','article'].includes(p.id),actualChildCount:p.id==='support'?1:0,marketingBannerCount:['home','article'].includes(p.id)?3:0,coreHub:false}))};
export function validateContract(c=copy,p=plan){
 if(!isDeepStrictEqual(p.region,{"name":"동구","officialCode":"12210","legalCode":"1221000000","officialParent":"전남광주통합특별시","customerQueryName":"광주 동구","nationalOrder":31}))throw new Error('Region contract changed');
 if(p.origin!==null||p.domain!==null||p.productionEnabled!==false)throw new Error('Private copy scope changed');
 if(p.canonicalCopySource!=='customer-copy.json'||p.markdownReviewOnly!==true||!p.faq.alwaysVisible||p.faq.accordion||p.faq.count!==3)throw new Error('Sole JSON or FAQ contract changed');
 if(!isDeepStrictEqual(p.pages.map(x=>[x.id,x.proposedPath]),[['home','/'],['detail','/regions/chosun-hospital-funeral-wreath/'],['support','/regions/'],['notFound','/404.html']]))throw new Error('Page route contract changed');
 if(c.detail.faq.length!==3||new Set(c.detail.faq.map(f=>f.question)).size!==3||c.productCards.map(p=>p.sku).join(',')!=='B201,B203,B205,B060')throw new Error('FAQ/product denominator changed');
 for(const [i,p] of c.productCards.entries())if(p.basePriceKRW!==[59000,79000,109000,149000][i]||p.shippingLabel!=='배송비 포함 최종금액은 주문 상담'||p.ctaHref!=='https://fwith.co.kr/shop/item.php?it_id='+p.sku)throw new Error('Product price/shipping/destination changed');
 if(p.commonBanners.map(b=>b.variant).join(',')!=='message,budget,consultation'||p.commonBanners.some(b=>b.width!==1774||b.height!==887||b.caption!==null)||Object.values(c.sharedBannerAlt).some(s=>s.split('1844-0644').length!==2))throw new Error('Banner contract changed');
 if(!isDeepStrictEqual(p.previewPolicy,{robotsMeta:'noindex,nofollow,noarchive',robotsTxt:'User-agent: *\nDisallow: /\n',sitemapURLs:[],IndexNow:false}))throw new Error('Private robots contract changed');
 if(p.socialMetadata['og:image']!=='Verified origin + /images/products/B201.jpg'||p.socialMetadata['twitter:card']!=='summary'||p.pages[3].socialMetadataIncluded!==false||p.pages[3].canonicalAtProduction!==null)throw new Error('Social/404 contract changed');
 if(c.home.cta.href!=='tel:18440644'||c.detail.cta.href!=='tel:18440644')throw new Error('Sales phone changed');return true;
}
export function validateRuntime(){assertBoundary();verifyInputs();validateContract();return true;}
validateRuntime();
