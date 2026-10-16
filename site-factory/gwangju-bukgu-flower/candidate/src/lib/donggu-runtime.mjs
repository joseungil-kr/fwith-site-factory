import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {isDeepStrictEqual} from 'node:util';
export const BUNDLE=path.resolve(process.cwd(),'..');
export const INPUT=path.join(BUNDLE,'inputs/reviewed-copy');
export const sha256=b=>crypto.createHash('sha256').update(b).digest('hex');
export const PIN=JSON.parse(fs.readFileSync(path.join(BUNDLE,'candidate/src/data/input-binding.json')));
export const EXPECTED_REQUIRED_SHA='8184f0b23b8b6d180bcd61c46ed1a35bfef165d09ee8896dce968fa15bb8566d';
export const EXPECTED_COPY_SHA='7669c489a95e2c82888cb3623fa962000e21d7b76092038e1c2d2a8ab702b429';
const read=name=>JSON.parse(fs.readFileSync(path.join(INPUT,name)));
export const copy=read('customer-copy.json'),home=copy.home,detail=copy.detail,products=copy.productCards,ui=copy.sharedUI,plan=read('render-plan.json');
export const copySHA={home:EXPECTED_COPY_SHA,article:EXPECTED_COPY_SHA,support:EXPECTED_COPY_SHA,'not-found':EXPECTED_COPY_SHA};
export const previewConfig=Object.freeze({mode:'private-local-preview',origin:null,domain:null,canonical:null,productionEnabled:false,coreHubLaunchStatus:'NOT_ASSESSED',fullLaunchStatus:'NOT_ASSESSED',crossRegionPublicationPrerequisites:false});
export function assertBoundary(config=previewConfig,env=process.env){
 if(!isDeepStrictEqual(config,previewConfig))throw new Error('Buk-gu private boundary changed');
 for(const key of ['SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION','SITE_RELEASE_MODE','SITE_INDEXABLE','SITE_RELEASE_BINDING_PATH','SITE_RELEASE_BINDING_SHA256','CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID'])if(env[key])throw new Error('Buk-gu private boundary: '+key+' must not be set');return true;
}
function regular(root,relative){
 if(typeof relative!=='string'||path.isAbsolute(relative)||relative.split('/').some(x=>!x||x==='.'||x==='..'||x.startsWith('.')))throw new Error('Unsafe input path');
 const file=path.resolve(root,relative);if(!file.startsWith(path.resolve(root)+path.sep))throw new Error('Input path escape');
 let current=root;for(const part of relative.split('/')){current=path.join(current,part);if(fs.lstatSync(current).isSymbolicLink())throw new Error('Input symlink forbidden');}
 if(!fs.lstatSync(file).isFile())throw new Error('Input regular file required');return fs.readFileSync(file);
}
export function verifyInputs(root=BUNDLE){
 const raw=regular(root,'inputs/required-originals.json');if(sha256(raw)!==EXPECTED_REQUIRED_SHA)throw new Error('Required originals manifest changed');
 const rows=JSON.parse(raw);if(rows.length!==34||new Set(rows.map(r=>r.path)).size!==34)throw new Error('Required originals denominator changed');
 for(const r of rows){const b=regular(root,r.path);if(b.length!==r.bytes||sha256(b)!==r.sha256)throw new Error('Required original changed: '+r.path);}
 const inventory=[];function scan(dir){for(const d of fs.readdirSync(dir,{withFileTypes:true})){if(d.name.startsWith('.')||d.isSymbolicLink())throw new Error('Unexpected hidden or symlink input');const f=path.join(dir,d.name);if(d.isDirectory())scan(f);else inventory.push(path.relative(root,f).split(path.sep).join('/'));}}
 scan(path.join(root,'inputs'));const want=['inputs/required-originals.json',...rows.filter(r=>r.path.startsWith('inputs/')).map(r=>r.path)].sort();if(!isDeepStrictEqual(inventory.sort(),want))throw new Error('Unexpected input file');
 const bindingRaw=regular(root,'inputs/reviewed-copy/reviews/implementation-review-binding.json'),reviewRaw=regular(root,'inputs/reviewed-copy/reviews/independent-review-r1.json');
 if(sha256(bindingRaw)!=='7b18ab565db0323d539417a84f1f6d631f550c3b388899d9061425dff0245b3c'||sha256(reviewRaw)!=='9a3a1516925f3801fd041a2f3a6273e8771b63ab3318b44645dd7d2d225d99c3')throw new Error('Independent review original changed');
 const binding=JSON.parse(bindingRaw),review=JSON.parse(reviewRaw);
 if(binding.region!=='bukgu'||binding.officialCode!=='12300'||binding.nationalOrder!==34||binding.customerCopySHA256!==EXPECTED_COPY_SHA||binding.renderPlanSHA256!=='1d294f23cd7826c362514391f91c36abd7ead623d1e863459b890355e9191a75'||binding.pathBase!=='THIS_REVIEW_PACKAGE_ROOT'||binding.assessmentScope!=='MANUSCRIPT_AND_RENDER_PLAN_ONLY'||binding.sourceCommit!==null||binding.publicationEligible!==false||binding.actualHTMLChecked!==false||binding.actualBuildChecked!==false||binding.actualBrowserChecked!==false||binding.actualPublicHTTPChecked!==false)throw new Error('Final review binding scope changed');
 if(review.verdict!=='MANUSCRIPT_AND_SPEC_READY_FOR_IMPLEMENTATION_NOT_PRODUCTION_PASS'||review.customerCopySHA256!==EXPECTED_COPY_SHA||review.renderPlanSHA256!==binding.renderPlanSHA256||review.mandatoryRevisions.length!==0||review.mustFixRemaining.length!==0)throw new Error('Independent final verdict not accepted');
 const projection=JSON.parse(regular(root,'inputs/reviewed-input-projection.json'));
 if(projection.reviewSHA256!=='9a3a1516925f3801fd041a2f3a6273e8771b63ab3318b44645dd7d2d225d99c3'||projection.bindingSHA256!=='7b18ab565db0323d539417a84f1f6d631f550c3b388899d9061425dff0245b3c'||projection.files.length!==26)throw new Error('Reviewed input projection changed');
 for(const row of projection.files){const bytes=regular(root,row.packagedPath);if(bytes.length!==row.bytes||sha256(bytes)!==row.sha256)throw new Error('Reviewed projected original changed');}
 for(const key of ["independentReview", "frozenAuthorManifest", "customerCopy", "renderPlan", "metadata", "visibleStrings", "assetManifest", "originalClauseReview", "visibleStringReview", "purchaseIntentReview", "renderChecklist", "closingReconciliation", "humanReview", "inputProjection"]){const ref=binding[key],row=projection.files.find(x=>x.originalPath===ref.path);if(!row||row.bytes!==ref.bytes||row.sha256!==ref.sha256)throw new Error('Review reference not covered: '+key);}
 const clauses=JSON.parse(regular(root,'inputs/reviewed-copy/reviews/original-clause-assessment.json'));
 if(clauses.guidanceClauses.length!==154||clauses.merchantPolicyClauses.length!==15||clauses.facilityClauses.length!==1)throw new Error('Exact original assessment schema changed');
 return true;
}
export const routes=Object.fromEntries(plan.pages.map(p=>[p.id,p.proposedPath]));
export const detailPath=routes.detail;
export function mapTarget(value){if(!value||typeof value.href!=='string'||!['/',detailPath,detailPath+'#sources'].includes(value.href))throw new Error('Unapproved target');return value.href;}
export const banners=plan.commonBanners.map(b=>({...b,id:b.variant,alt:copy.sharedBannerAlt[b.variant],renderSrc:b.publicPath}));
export const pages=[{id:'home',copyKey:'home',role:'primary-home',...home,path:routes.home},{id:'article',copyKey:'detail',role:'primary-article',...detail,id:'article',path:detailPath},{id:'support',copyKey:'support',role:'support-navigation',...copy.support,path:routes.support},{id:'not-found',copyKey:'notFound',role:'technical-404',...copy.notFound,path:routes.notFound}];
export const pageMap={...previewConfig,articleCount:1,primaryCount:2,supportCount:1,contentHtmlCount:3,technicalHtmlCount:1,allHtmlCount:4,previewIndexableCount:0,previewSitemapUrlCount:0,nationalSelectionOrder:34,pages:pages.map(p=>({id:p.id,copyKey:p.copyKey,path:p.path,role:p.role,title:p.title,description:p.description,h1:p.h1,robots:'noindex,nofollow,noarchive',canonical:null,sitemapIncluded:false,mainMenuIncluded:['home','article'].includes(p.id),actualChildCount:p.id==='support'?1:0,marketingBannerCount:['home','article'].includes(p.id)?3:0,coreHub:false}))};
export function facilityCard(c=copy){
 const sections=c?.home?.sections;
 if(!Array.isArray(sections))throw new Error('Home sections required');
 const matches=sections.filter(s=>s?.id==='facility-guide'),cards=sections.filter(s=>s&&Object.hasOwn(s,'card'));
 if(matches.length!==1||cards.length!==1||matches[0]!==cards[0])throw new Error('Exactly one facility-guide card required');
 const card=matches[0].card;
 if(!card||Array.isArray(card)||typeof card!=='object'||Object.keys(card).sort().join('|')!=='ctaLabel|href|summary|title'||['title','summary','ctaLabel'].some(k=>typeof card[k]!=='string'||!card[k].trim())||card.href!==detailPath)throw new Error('Reviewed facility card shape/target required');
 return card;
}
export function validateContract(c=copy,p=plan){
 facilityCard(c);
 if(!isDeepStrictEqual(Object.keys(c),['home','detail','productCards','support','notFound','sharedUI','sharedBannerAlt']))throw new Error('Exact seven-key render schema required');
 if(!isDeepStrictEqual(c.home.sections.map(s=>s.id),['selection','facility-guide','consultation'])||!isDeepStrictEqual(c.detail.sections.map(s=>s.id),['products','ribbon','budget','facility','order']))throw new Error('Reviewed section order changed');

 if(!isDeepStrictEqual(p.region,{"name":"북구","officialCode":"12300","legalCode":"1230000000","officialParent":"전남광주통합특별시","customerQueryName":"광주 북구","nationalOrder":34}))throw new Error('Region contract changed');
 if(p.origin!==null||p.domain!==null||p.productionEnabled!==false)throw new Error('Private copy scope changed');
 if(p.canonicalCopySource!=='customer-copy.json'||p.markdownReviewOnly!==true||!p.faq.alwaysVisible||p.faq.accordion||p.faq.count!==3)throw new Error('Sole JSON or FAQ contract changed');
 if(!isDeepStrictEqual(p.pages.map(x=>[x.id,x.proposedPath]),[['home','/'],['detail','/regions/green-funeral-wreath/'],['support','/regions/'],['notFound','/404.html']]))throw new Error('Page route contract changed');
 if(c.detail.faq.length!==3||new Set(c.detail.faq.map(f=>f.question)).size!==3||c.productCards.map(p=>p.sku).join(',')!=='B201,B203,B205,B060')throw new Error('FAQ/product denominator changed');
 for(const [i,p] of c.productCards.entries())if(p.basePriceKRW!==[59000,79000,109000,149000][i]||p.shippingLabel!=='배송비 포함 최종금액은 주문 상담'||p.ctaHref!=='https://fwith.co.kr/shop/item.php?it_id='+p.sku)throw new Error('Product price/shipping/destination changed');
 if(p.commonBanners.map(b=>b.variant).join(',')!=='message,budget,consultation'||p.commonBanners.some(b=>b.width!==1774||b.height!==887||b.caption!==null)||Object.values(c.sharedBannerAlt).some(s=>s.split('1844-0644').length!==2))throw new Error('Banner contract changed');
 if(!isDeepStrictEqual(p.previewPolicy,{robotsMeta:'noindex,nofollow,noarchive',robotsTxt:'User-agent: *\nDisallow: /\n',sitemapURLs:[],IndexNow:false}))throw new Error('Private robots contract changed');
 if(p.socialMetadata['og:image']!=='Verified origin + /images/products/B201.jpg'||p.socialMetadata['twitter:card']!=='summary'||p.pages[3].socialMetadataIncluded!==false||p.pages[3].canonicalAtProduction!==null)throw new Error('Social/404 contract changed');
 if(c.home.cta.href!=='tel:18440644'||c.detail.cta.href!=='tel:18440644')throw new Error('Sales phone changed');return true;
}
export function validateRuntime(){assertBoundary();verifyInputs();validateContract();return true;}
validateRuntime();
