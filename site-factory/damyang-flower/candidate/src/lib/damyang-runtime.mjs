import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {isDeepStrictEqual as equal} from 'node:util';
export const BUNDLE=path.resolve(process.cwd(),'..');
export const INPUT=path.join(BUNDLE,'inputs/reviewed-copy');
export const sha256=b=>crypto.createHash('sha256').update(b).digest('hex');
export const PIN=JSON.parse(fs.readFileSync(path.join(BUNDLE,'candidate/src/data/input-binding.json')));
export const EXPECTED_REQUIRED_SHA='29cefed099c2c622bb5f9338683696e50e592327692bcadca9b2ee00c8bf7202';
export const EXPECTED_COPY_SHA='3bc9a15e452efbc3afac06f366f711ac45008b136d3597a6a15d997ddfb741d0';
const read=name=>JSON.parse(fs.readFileSync(path.join(INPUT,name)));
export const copy=read('customer-copy.json'),home=copy.home,products=copy.productCards,ui=copy.sharedUI,plan=read('render-plan.json');
export const copySHA={home:EXPECTED_COPY_SHA,'not-found':EXPECTED_COPY_SHA};
export const previewConfig=Object.freeze({mode:'private-local-preview',origin:null,domain:null,canonical:null,productionEnabled:false,coreHubLaunchStatus:'NOT_ASSESSED',fullLaunchStatus:'NOT_ASSESSED',crossRegionPublicationPrerequisites:false});
export function assertBoundary(config=previewConfig,env=process.env){
 if(!equal(config,previewConfig))throw new Error('Damyang private boundary changed');
 for(const key of ['SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION','SITE_RELEASE_MODE','SITE_INDEXABLE','SITE_RELEASE_BINDING_PATH','SITE_RELEASE_BINDING_SHA256','CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID'])if(env[key])throw new Error('Damyang private boundary: '+key+' must not be set');return true;
}
function regular(root,relative){
 if(typeof relative!=='string'||path.isAbsolute(relative)||relative.split('/').some(x=>!x||x==='.'||x==='..'||x.startsWith('.')))throw new Error('Unsafe input path');
 const file=path.resolve(root,relative);if(!file.startsWith(path.resolve(root)+path.sep))throw new Error('Input path escape');
 let current=root;for(const part of relative.split('/')){current=path.join(current,part);if(fs.lstatSync(current).isSymbolicLink())throw new Error('Input symlink forbidden');}
 if(!fs.lstatSync(file).isFile())throw new Error('Input regular file required');return fs.readFileSync(file);
}
export function verifyInputs(root=BUNDLE){
 const raw=regular(root,'inputs/required-originals.json');if(sha256(raw)!==EXPECTED_REQUIRED_SHA)throw new Error('Required originals manifest changed');
 const rows=JSON.parse(raw);if(rows.length!==33||new Set(rows.map(r=>r.path)).size!==33)throw new Error('Required originals denominator changed');
 for(const r of rows){const b=regular(root,r.path);if(b.length!==r.bytes||sha256(b)!==r.sha256)throw new Error('Required original changed: '+r.path);}
 const inventory=[];function scan(dir){for(const d of fs.readdirSync(dir,{withFileTypes:true})){if(d.name.startsWith('.')||d.isSymbolicLink())throw new Error('Unexpected hidden or symlink input');const f=path.join(dir,d.name);if(d.isDirectory())scan(f);else inventory.push(path.relative(root,f).split(path.sep).join('/'));}}
 scan(path.join(root,'inputs'));const want=['inputs/required-originals.json',...rows.filter(r=>r.path.startsWith('inputs/')).map(r=>r.path)].sort();if(!equal(inventory.sort(),want))throw new Error('Unexpected input file');
 const rdir='inputs/reviewed-copy/independent-review/';
 const bindingRaw=regular(root,rdir+'implementation-review-binding.json'),reviewRaw=regular(root,rdir+'independent-review-r2.json'),manifestRaw=regular(root,rdir+'REVIEW-MANIFEST.json');
 if(sha256(bindingRaw)!=='2fa8925f86de9169c064f4ab28c75f0d2a04e45ed71ae95931321ea3f67e3e17'||sha256(reviewRaw)!=='03459961bc8d1e71e80f06dfc827b02b16683bc4e5a724592b87ffa406f1a101'||sha256(manifestRaw)!=='2e2643c366cccce780e643fde839e5f90184c36226a3e199b923761b60305ca4')throw new Error('Independent review original changed');
 const binding=JSON.parse(bindingRaw),review=JSON.parse(reviewRaw),manifest=JSON.parse(manifestRaw);
 for(const original of [binding,review]){
  if(original.customerCopySHA256!==EXPECTED_COPY_SHA||original.renderPlanSHA256!=='99c7106fece161c1cd5ffe5308a3c3155bee287292607627e85322fe23c7c7d7'||original.sourceCommit!==null||original.assessmentScope!=='MANUSCRIPT_AND_RENDER_PLAN_ONLY'||original.originalAuthorScores!==null||original.originalIndependentScores!==null||original.independentNumericScores!==null)throw new Error('Original review scope/null scores changed');
  for(const k of ['actualHTMLChecked','actualBuildChecked','actualBrowserChecked','actualPublicHTTPChecked','publicationEligible'])if(original[k]!==false)throw new Error('Manuscript review upgraded without evidence');
  if(original.coreHubLaunchStatus!=='NOT_ASSESSED'||original.fullLaunchStatus!=='NOT_ASSESSED')throw new Error('Launch scope changed');
 }
 if(review.verdict!=='MANUSCRIPT_AND_SPEC_READY_FOR_IMPLEMENTATION_NOT_PRODUCTION_PASS'||review.mustFixRemaining.length||review.mandatoryRevisions.length||!equal(review.originalDenominators,{guidance:165,policy:24,currentFacts:16,facilities:3}))throw new Error('Original verdict/denominators changed');
 if(!equal(review.plannedStructure,{copyRootKeys:['home','productCards','notFound','sharedUI','sharedBannerAlt'],authoredStrings:100,substantiveHomeCount:1,facilityDetailCount:0,emptyHubCount:0,technical404Count:1,plannedHTMLCount:2,plannedIndexableURLCount:1,actualHTMLCount:null,actualSitemapURLCount:null,productCards:4,FAQObjects:4,assets:7}))throw new Error('Native manuscript planned scope changed');
 const projection=JSON.parse(regular(root,'inputs/reviewed-input-projection.json'));
 if(projection.independentReviewSHA256!==sha256(reviewRaw)||projection.bindingSHA256!==sha256(bindingRaw)||projection.reviewManifestSHA256!==sha256(manifestRaw)||projection.files.length!==32)throw new Error('Projection scope changed');
 for(const row of projection.files){const b=regular(root,row.packagedPath);if(b.length!==row.bytes||sha256(b)!==row.sha256||row.transformation!=='EXACT_BYTES')throw new Error('Projected bytes changed');const ref=manifest.files.find(r=>r.path===row.originalPath);if(!ref&&row.originalPath!=='REVIEW-MANIFEST.json'||ref&&(ref.bytes!==row.bytes||ref.sha256!==row.sha256))throw new Error('Projected original manifest mismatch');}
 const clauses=JSON.parse(regular(root,rdir+'original-clause-assessment.json'));
 for(const [k,n] of [['guidanceClauses',165],['merchantPolicyClauses',24],['currentFactClauses',16],['facilityClauses',3]])if(clauses[k].length!==n)throw new Error('Original clause denominator changed');
 if(clauses.originalAuthorScores!==null||clauses.originalIndependentScores!==null||clauses.independentNumericScores!==null||clauses.actualHTMLChecked!==false)throw new Error('Original clause assessment meaning changed');
 const supplemental=JSON.parse(regular(root,rdir+'supplemental-policy-assessment.json'));
 const expectedSupplement={upperImagePolicyClauses:6,applicationScopeFollowupFacts:1};
 if(review.schemaVersion!==2||binding.schemaVersion!==2||review.revision!=='damyang-copy-r2-20261016'||!equal(review.supplementalDenominators,expectedSupplement)||!equal(clauses.supplementalDenominators,expectedSupplement)||!equal(supplemental.supplementalDenominators,expectedSupplement))throw new Error('Native r2 supplemental scope changed');
 if(supplemental.supplementalUpperPolicyClauses.length!==6||supplemental.applicationScopeFollowupFacts.length!==1||supplemental.authorScores!==null||supplemental.independentScores!==null||supplemental.independentNumericScores!==null||supplemental.actualRenderingVerified!==false||supplemental.publicHTTPVerified!==false)throw new Error('Supplemental review meaning changed');
 if(supplemental.copySHA256!==EXPECTED_COPY_SHA||supplemental.copyPointer!=='/home/sections/4/afterList/1'||supplemental.verdict!=='SIX_UPPER_CLAUSES_AND_ONE_SCOPE_LIMIT_SATISFIED_IN_R2_MANUSCRIPT')throw new Error('Supplemental review binding changed');
 if(!equal(supplemental.upperPolicyBySKU.map(r=>r.sku),['B201','B203','B205'])||!equal(supplemental.lowerPolicyBySKU.map(r=>r.afterHour),[19,19,19,21]))throw new Error('SKU timing distinction changed');
 const priorRaw=regular(root,rdir+'prior/r1/independent-review-r1.json'),prior=JSON.parse(priorRaw);
 if(sha256(priorRaw)!=='a0f4ea2988a8ab7104fb952c9d44cf644f5288bbf6283a29bd5abb709b748037'||review.priorReview.sha256!==sha256(priorRaw)||binding.priorReview.sha256!==sha256(priorRaw)||prior.customerCopySHA256!=='6244d474b6c01bbfe452897ee90fdce7aa30819a51cfee7091f9a0cde883e3a8'||review.supersession.r1NoRequiredTimingRevisionRemainsCurrent!==false)throw new Error('Historical r1 or narrow supersession changed');
 return true;
}
export const routes=Object.fromEntries(plan.pages.map(p=>[p.id,p.proposedPath]));
export const navigation=plan.navigation.mainMenu.map(x=>({label:ui[x.labelSource.split('.')[1]],href:x.href}));
export function mapTarget(value){if(!value||typeof value.href!=='string'||!['/',...navigation.map(x=>x.href)].includes(value.href))throw new Error('Unapproved target');return value.href;}
export const banners=plan.commonBanners.map(b=>({...b,id:b.variant,alt:copy.sharedBannerAlt[b.variant],renderSrc:b.publicPath}));
export const pages=[{id:'home',copyKey:'home',role:'primary-home',...home,path:routes.home},{id:'not-found',copyKey:'notFound',role:'technical-404',...copy.notFound,path:routes.notFound}];
export const pageMap={...previewConfig,articleCount:0,substantiveHomeCount:1,primaryCount:1,supportCount:0,facilityDetailCount:0,contentHtmlCount:1,technicalHtmlCount:1,allHtmlCount:2,previewIndexableCount:0,previewSitemapUrlCount:0,productionPlannedIndexableCount:1,nationalSelectionOrder:36,pages:pages.map(p=>({id:p.id,copyKey:p.copyKey,path:p.path,role:p.role,title:p.title,description:p.description,h1:p.h1,robots:'noindex,nofollow,noarchive',canonical:null,sitemapIncluded:false,mainMenuIncluded:p.id==='home',actualChildCount:0,marketingBannerCount:p.id==='home'?3:0,coreHub:false}))};
export function validateContract(c=copy,p=plan){
 if(!equal(Object.keys(c),['home','productCards','notFound','sharedUI','sharedBannerAlt']))throw new Error('Exact five-key native render schema required');
 if(!equal(c.home.sections.map(s=>s.id),['products','budget','ribbon','destinations','order'])||c.home.sections.some(s=>Object.hasOwn(s,'card'))||!equal(c.home.sections[0].productCardIds,['B201','B203','B205','B060']))throw new Error('Reviewed home section/card scope changed');
 if(!equal(p.region,{name:'담양군',officialCode:'12710',legalCode:'1271000000',officialParent:'전남광주통합특별시',nationalOrder:36}))throw new Error('Region contract changed');
 if(p.origin!==null||p.domain!==null||p.productionEnabled!==false)throw new Error('Private copy scope changed');
 if(p.productCards.source!=='customer-copy.json#/productCards'||p.faq.source!=='customer-copy.json#/home/faq'||!p.faq.alwaysVisible||p.faq.accordion||p.faq.count!==4)throw new Error('Sole JSON or FAQ contract changed');
 if(!equal(p.pages.map(x=>[x.id,x.proposedPath]),[['home','/'],['notFound','/404.html']])||!equal(p.productionPolicy.sitemapPageIds,['home'])||p.productionPolicy.plannedIndexableURLCount!==1)throw new Error('Two-page/one-indexable route contract changed');
 if(c.home.faq.length!==4||new Set(c.home.faq.map(f=>f.question)).size!==4||c.productCards.map(p=>p.sku).join(',')!=='B201,B203,B205,B060')throw new Error('FAQ/product denominator changed');
 for(const [i,product] of c.productCards.entries())if(product.basePriceKRW!==[59000,79000,109000,149000][i]||product.additionalShippingKRW!==10000||product.referenceTotalKRW!==product.basePriceKRW+product.additionalShippingKRW||product.finalPriceKRW!==null||product.priceLabel!==`상품 기본가 ${product.basePriceKRW.toLocaleString('en-US')}원`||product.shippingLabel!=='담양 게시 추가배송비 10,000원'||product.referenceTotalLabel!==`게시금액 합산 참고예산 ${product.referenceTotalKRW.toLocaleString('en-US')}원`||product.ctaHref!=='https://fwith.co.kr/shop/item.php?it_id='+product.sku)throw new Error('Product price/shipping/reference/destination changed');
 if(!equal(p.navigation.mainMenu,[{labelSource:'sharedUI.productsLink',href:'/#products'},{labelSource:'sharedUI.budgetLink',href:'/#budget'},{labelSource:'sharedUI.ribbonLink',href:'/#ribbon'},{labelSource:'sharedUI.orderLink',href:'/#order'},{labelSource:'sharedUI.faqLink',href:'/#faq'}]))throw new Error('Reviewed navigation changed');
 if(p.commonBanners.map(b=>b.variant).join(',')!=='message,budget,consultation'||p.commonBanners.some(b=>b.width!==1774||b.height!==887||b.caption!==null)||Object.values(c.sharedBannerAlt).some(s=>s.split('1844-0644').length!==2))throw new Error('Banner contract changed');
 if(p.pages.some(x=>x.previewRobots!=='noindex,nofollow,noarchive'||x.previewSitemapIncluded!==false||x.canonical!==null))throw new Error('Private robots contract changed');
 if(p.socialMetadata['og:image']!=='Verified origin + /images/products/B201.jpg'||p.socialMetadata['twitter:card']!=='summary'||p.pages[1].socialMetadataIncluded!==false||p.pages[1].canonicalAtProduction!==null)throw new Error('Social/404 contract changed');
 const delta=read('version-diff.json');
 if(delta.changedCustomerLeafCount!==1||delta.changes[0].pointer!=='/home/sections/4/afterList/1'||c.home.sections[4].afterList[1]!==delta.changes[0].after||p.policyContextRetention?.revision!==2||p.policyContextRetention?.copyPointer!=='/home/sections/4/afterList/1')throw new Error('Complete reviewed r2 timing context required');
 if(c.home.cta.href!=='tel:18440644'||c.notFound.cta.href!=='/')throw new Error('CTA changed');return true;
}
export function validateRuntime(){assertBoundary();verifyInputs();validateContract();return true;}
validateRuntime();
