import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {isDeepStrictEqual as equal} from 'node:util';
export const BUNDLE=path.resolve(process.cwd(),'..');
export const INPUT=path.join(BUNDLE,'inputs/reviewed-copy');
export const sha256=b=>crypto.createHash('sha256').update(b).digest('hex');
export const PIN=JSON.parse(fs.readFileSync(path.join(BUNDLE,'candidate/src/data/input-binding.json')));
export const EXPECTED_REQUIRED_SHA='d9e4e75f99370c51201bf411f613b58ef1af6aa3be182a10a043741c0fcfb3dd';
export const EXPECTED_COPY_SHA='3829721f442682c7b07f02b043b5ba80a0e1e0d5264babb7c96a7b2eadd0332e';
const read=name=>JSON.parse(fs.readFileSync(path.join(INPUT,name)));
export const copy=read('customer-copy.json'),home=copy.home,products=copy.productCards,ui=copy.sharedUI,plan=read('render-plan.json');
export const copySHA={home:EXPECTED_COPY_SHA,'not-found':EXPECTED_COPY_SHA};
export const previewConfig=Object.freeze({mode:'private-local-preview',origin:null,domain:null,canonical:null,productionEnabled:false,coreHubLaunchStatus:'NOT_ASSESSED',fullLaunchStatus:'NOT_ASSESSED',crossRegionPublicationPrerequisites:false});
export function assertBoundary(config=previewConfig,env=process.env){
 if(!equal(config,previewConfig))throw new Error('Gokseong private boundary changed');
 for(const key of ['SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION','SITE_RELEASE_MODE','SITE_INDEXABLE','SITE_RELEASE_BINDING_PATH','SITE_RELEASE_BINDING_SHA256','CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID','PRODUCTION_APPROVED','OWNERSHIP_VERIFIED','INDEXNOW_ENABLED','PUBLIC_APPROVED'])if(env[key])throw new Error('Gokseong private boundary: '+key+' must not be set');return true;
}
function regular(root,relative){
 if(typeof relative!=='string'||path.isAbsolute(relative)||relative.split('/').some(x=>!x||x==='.'||x==='..'||x.startsWith('.')))throw new Error('Unsafe input path');
 const file=path.resolve(root,relative);if(!file.startsWith(path.resolve(root)+path.sep))throw new Error('Input path escape');
 let current=root;for(const part of relative.split('/')){current=path.join(current,part);if(fs.lstatSync(current).isSymbolicLink())throw new Error('Input symlink forbidden');}
 if(!fs.lstatSync(file).isFile())throw new Error('Input regular file required');return fs.readFileSync(file);
}


// This successor inventories references separately. Historical crop bytes are not fetched or claimed present.
export const EXPECTED_REFERENCE_SHA='d1e40cbf681a1ca9797bd3e80c872dbe90ee5865da60cc1a8a6bd820c9d87df3';
const EVIDENCE_ORIGINALS=[{"id":"B201-merchant-detail","sku":"B201","url":"https://fwith.co.kr/data/item/flower379/B201/main_pc.jpg","sha256":"69a56afede4f5cb2c4d94361f61c39deffd189ca170ee17cca0f63d290dc6ef5","bytes":2457249,"dimensions":[960,14311],"contentType":"image/jpeg","observedGETAt":"2026-10-16T03:30:46.508390+00:00","observedHTTPStatus":200,"observationScope":"Archived GET bytes, not a new current HTTP check"},{"id":"B203-merchant-detail","sku":"B203","url":"https://fwith.co.kr/data/item/flower379/B203/main_pc.jpg","sha256":"c1bb20ce75cfd96f9f9de4ca06edaba5ffe4d46c035b25f17c7a33aa2cb94455","bytes":2485184,"dimensions":[960,14311],"contentType":"image/jpeg","observedGETAt":"2026-10-16T03:30:46.509396+00:00","observedHTTPStatus":200,"observationScope":"Archived GET bytes, not a new current HTTP check"},{"id":"B205-merchant-detail","sku":"B205","url":"https://fwith.co.kr/data/item/flower379/B205/main_pc.jpg","sha256":"27a3e495b90b3409c675eb71de9fee2649a815aa06424f72f77c397782cccea0","bytes":2592349,"dimensions":[960,14311],"contentType":"image/jpeg","observedGETAt":"2026-10-16T03:30:51.948504+00:00","observedHTTPStatus":200,"observationScope":"Archived GET bytes, not a new current HTTP check"},{"id":"B060-merchant-detail","sku":"B060","url":"https://fwith.co.kr/data/item/flower379/B060/main_pc.jpg","sha256":"67c7d7f16ca2b4bffe2694a7e2de06f41b90e5ea8fcaa57681eb2f5b8f890cfa","bytes":797246,"dimensions":[960,3750],"contentType":"image/jpeg","observedGETAt":"2026-10-16T03:30:52.345390+00:00","observedHTTPStatus":200,"observationScope":"Archived GET bytes, not a new current HTTP check"}];
const HISTORICAL_SOURCE={"sourceZIP_SHA256":"885379cb5da1bf3e9331990424592ed2b056545bd26d541cbf3b726e2a571433","sourceTreeSHA256":"f5d0e054908814f889e88aab482f6f9eabc73459571496b5e884829e377156db","sourceFiles":95,"nativeReviewSHA256":"e6181c6da9d55ac3773b02ba30793d69ce79c117bd85591ce719f99277db5630","nativeReviewBindingSHA256":"b49f0464f3602f05ca70f4d31e21c27ded069dc60e66851a6b957a9512e8ef59","scope":"Historical exact source review, not approval of this successor"};
const REFERENCE_POLICY={"schema":"gokseong-archived-merchant-crop-references/v1","purpose":"Historical merchant policy evidence references; never customer runtime assets","archivedCropCount":7,"originalImageCount":4,"newRepositoryBinaryFiles":0,"buildNetworkRequests":false,"customerImageHotlinks":false,"rawImagesOrCropsPackaged":false,"sourceRevision":null,"proof":null,"publicationEligible":false,"verificationBoundary":"Raw JPEG and crop PNG bytes remain in the preserved local historical archives. The source build validates pinned reference metadata, not absent image bytes. A later original URL response may change; never silently replace these hashes."};
function exactKeys(value,keys){return value&&typeof value==='object'&&!Array.isArray(value)&&equal(Object.keys(value).sort(),keys.slice().sort());}
export function validateEvidenceReferences(ref,manifest=read('MANIFEST.json'),timing=read('timing-context-addendum.json')){
 if(!exactKeys(ref,[...Object.keys(REFERENCE_POLICY),'historicalSource','originalImages','references'])||Object.entries(REFERENCE_POLICY).some(([k,v])=>!equal(ref[k],v))||!equal(ref.historicalSource,HISTORICAL_SOURCE)||!equal(ref.originalImages,EVIDENCE_ORIGINALS))throw new Error('Archived evidence reference provenance changed');
 if(ref.references.length!==7||new Set(ref.references.map(r=>r.originalPath)).size!==7)throw new Error('Archived crop reference denominator changed');
 const expected=[];
 for(const source of EVIDENCE_ORIGINALS){
  for(const kind of source.sku==='B060'?['detail-lower']:['detail-lower','timing-top']){
   const originalPath=`evidence/research/evidence/image-inspection/${source.sku}-${kind}.png`,native=manifest.files.find(r=>r.path===originalPath);
   if(!native||!Number.isSafeInteger(native.bytes)||native.bytes<=0||!/^[a-f0-9]{64}$/.test(native.sha256))throw new Error('Historical crop identity missing');
   const upper=kind==='timing-top',box=upper?[0,0,960,600]:[0,source.dimensions[1]-2700,960,source.dimensions[1]];
   expected.push({originalPath,sourceImageId:source.id,sku:source.sku,originalCropSHA256:native.sha256,originalCropBytes:native.bytes,cropBox:box,cropDimensions:[box[2]-box[0],box[3]-box[1]],coordinateConvention:'xyxy-left-top-inclusive-right-bottom-exclusive',archivedPixelVerification:'EXACT_DECODED_RGB_REGION',repositoryArtifactIncluded:false,transformation:'ARCHIVED_BINARY_REFERENCE_ONLY'});
  }
 }
 expected.sort((a,b)=>a.originalPath.localeCompare(b.originalPath));
 if(!equal(ref.references,expected))throw new Error('Archived crop source, coordinates or original hash changed');
 const used=[...timing.upperBySKU,...timing.lowerBySKU].map(r=>r.source).sort();
 if(!equal(used,expected.map(r=>r.originalPath).sort()))throw new Error('Historical timing evidence coverage changed');
 return true;
}
export function verifyInputs(root=BUNDLE){
 const raw=regular(root,'inputs/required-originals.json');if(sha256(raw)!==EXPECTED_REQUIRED_SHA)throw new Error('Required originals manifest changed');
 const rows=JSON.parse(raw);if(rows.length!==38||new Set(rows.map(r=>r.path)).size!==38)throw new Error('Required originals denominator changed');
 for(const r of rows){const b=regular(root,r.path);if(b.length!==r.bytes||sha256(b)!==r.sha256)throw new Error('Required original changed: '+r.path);}
 const inventory=[];function scan(dir){for(const d of fs.readdirSync(dir,{withFileTypes:true})){if(d.name.startsWith('.')||d.isSymbolicLink())throw new Error('Unexpected hidden or symlink input');const f=path.join(dir,d.name);if(d.isDirectory())scan(f);else inventory.push(path.relative(root,f).split(path.sep).join('/'));}}
 scan(path.join(root,'inputs'));const want=['inputs/required-originals.json',...rows.filter(r=>r.path.startsWith('inputs/')).map(r=>r.path)].sort();if(!equal(inventory.sort(),want))throw new Error('Unexpected input file');
 const rdir='inputs/reviewed-copy/';const load=n=>JSON.parse(regular(root,rdir+n));
 const bindingRaw=regular(root,rdir+'INPUT-BINDING.json'),reviewRaw=regular(root,rdir+'independent-review-effective-r2.json'),manifestRaw=regular(root,rdir+'MANIFEST.json');
 if(sha256(bindingRaw)!=='94966aca6e69f432c7f1d5dff3bcd93511d3c760269c6129ae335d89db1533de'||sha256(reviewRaw)!=='6fc2af121a507982902285d410822a41f6939d9303d3ca5751f2ca020a742326'||sha256(manifestRaw)!=='1e61a43cb9a3504f16c6186d91d228fb8aaa8b5fdcd361ecfc93f23820d2f120')throw new Error('Independent review original changed');
 const binding=JSON.parse(bindingRaw),review=JSON.parse(reviewRaw),manifest=JSON.parse(manifestRaw);
 if(binding.customerCopySHA256!==EXPECTED_COPY_SHA||review.customerCopySHA256!==EXPECTED_COPY_SHA||review.renderPlanSHA256!=='0ef1ba508743a560d04a8217fbd9a35d80569f6808c3603367da2f7db2293b67'||review.sourceCommit!==null||review.assessmentScope!=='MANUSCRIPT_AND_RENDER_PLAN_ONLY')throw new Error('Original manuscript scope changed');
 for(const k of ['originalAuthorScores','originalIndependentScores','independentNumericScores'])if(review[k]!==null)throw new Error('Original null score changed');
 for(const original of [review,binding])for(const k of ['actualHTMLChecked','actualBuildChecked','actualBrowserChecked','actualPublicHTTPChecked','publicationEligible'])if(original[k]!==false)throw new Error('Original review upgraded without evidence');
 if(binding.sourceCommit!==null||binding.numericScore!==null||binding.implementationApproved!==false||review.implementationPermissionGranted!==false||review.publicationPermissionGranted!==false)throw new Error('Original review permission/scope changed');
 if(review.coreHubLaunchStatus!=='NOT_ASSESSED'||review.fullLaunchStatus!=='NOT_ASSESSED'||review.verdict!=='MANUSCRIPT_AND_SPEC_READY_FOR_IMPLEMENTATION_NOT_PRODUCTION_PASS'||review.mustFixRemaining.length||review.mandatoryRevisions.length||!equal(review.originalDenominators,{guidance:171,policy:16,currentFacts:17,facilities:5}))throw new Error('Native verdict/denominators changed');
 if(!equal(review.plannedStructure,{copyRootKeys:['home','productCards','notFound','sharedUI','sharedBannerAlt'],authoredStrings:102,substantiveHomeCount:1,facilityDetailCount:0,emptyHubCount:0,technical404Count:1,plannedHTMLCount:2,plannedIndexableURLCount:1,actualHTMLCount:null,actualSitemapURLCount:null,productCards:4,FAQObjects:3,assets:7}))throw new Error('Native manuscript planned scope changed');
 const originalRaw=regular(root,rdir+'independent-review-r1.json'),original=JSON.parse(originalRaw);
 if(sha256(originalRaw)!==binding.independentOriginalReviewSHA256||sha256(originalRaw)!==review.originalVerdictSHA256||original.verdict!=='MANUSCRIPT_CONTENT_ACCEPTED_RENDER_MAPPING_REVISION_REQUIRED'||original.renderSpecVerdict!=='MUST_FIX_GOK_MAP_01'||original.mustFixRemaining.length!==1)throw new Error('Original r1 failure erased');
 const clauses=load('native-clause-public-projection.json'),resolution=load('design-r2-clause-resolution.json');
 for(const [k,n] of [['guidanceClauses',171],['merchantPolicyClauses',16],['currentFactClauses',17],['facilityClauses',5]])if(clauses[k].length!==n)throw new Error('Original clause denominator changed');
 if(clauses.projectionOfSHA256!==binding.nativeFullClauseAssessmentSHA256||sha256(regular(root,rdir+'native-clause-public-projection.json'))!==binding.publicSafeProjectionOfFullClausesSHA256||clauses.independentNumericScores!==null||clauses.actualHTMLChecked!==false||clauses.originalGuidanceTextIncluded!==false)throw new Error('Native public projection changed');
 if(resolution.originalAssessmentSHA256!==clauses.projectionOfSHA256||resolution.effectiveRenderPlanSHA256!==review.renderPlanSHA256||resolution.issue!=='GOK-MAP-01'||resolution.actualHTMLChecked!==false||resolution.numericScores!==null||review.resolution.customerTextChanged!==false||review.resolution.exactOccurrences!==119||review.resolution.states!==8)throw new Error('Design-only resolution changed');
 for(const r of binding.effectiveFiles)if(sha256(regular(root,rdir+r.path))!==r.sha256)throw new Error('Effective file binding changed');
 const projection=JSON.parse(regular(root,'inputs/reviewed-input-projection.json'));
 if(projection.reviewSHA256!==sha256(reviewRaw)||projection.bindingSHA256!==sha256(bindingRaw)||projection.publicManifestSHA256!==sha256(manifestRaw)||projection.files.length!==36||projection.sourceRevision!==null||projection.publicationEligible!==false)throw new Error('Projection scope changed');
 for(const row of projection.files){const b=regular(root,row.packagedPath);if(b.length!==row.bytes||sha256(b)!==row.sha256||row.transformation!=='EXACT_BYTES')throw new Error('Projected bytes changed');const ref=manifest.files.find(r=>r.path===row.originalPath);if(!ref&&!['MANIFEST.json','SHA256SUMS','PACKAGE-VERIFICATION.json'].includes(row.originalPath)||ref&&(ref.bytes!==row.bytes||ref.sha256!==row.sha256))throw new Error('Projected original manifest mismatch');}
 const refRaw=regular(root,'inputs/reviewed-crop-references.json'),ref=JSON.parse(refRaw);
 if(sha256(refRaw)!==EXPECTED_REFERENCE_SHA||projection.referenceManifestSHA256!==EXPECTED_REFERENCE_SHA)throw new Error('Archived reference manifest changed');
 validateEvidenceReferences(ref,manifest,load('timing-context-addendum.json'));
 const projectedReferences=ref.references.map(r=>({originalPath:r.originalPath,referenceManifestPath:'inputs/reviewed-crop-references.json',referenceId:r.originalPath,originalBytes:r.originalCropBytes,originalSHA256:r.originalCropSHA256,transformation:'ARCHIVED_BINARY_REFERENCE_ONLY',repositoryArtifactIncluded:false}));
 if(projection.schema!=='gokseong-implementation-input-projection/v2'||!equal(projection.archivedEvidenceReferences,projectedReferences)||!equal(projection.historicalSource,HISTORICAL_SOURCE)||projection.newRepositoryBinaryFiles!==0||projection.customerOutputChangesAllowed!==false||projection.sourceProjectionChanged!==true)throw new Error('Reference projection scope changed');
 const covered=[...projection.files.map(r=>r.originalPath),...ref.references.map(r=>r.originalPath)];
 if(covered.length!==43||new Set(covered).size!==36||ref.references.some(r=>fs.existsSync(path.join(root,'inputs/reviewed-copy',r.originalPath))))throw new Error('Evidence reference must not masquerade as packaged crop');
 const visible=load('visible-strings.json'),map=load('output-context-map.json');if(visible.count!==102||visible.rows.length!==102||map.contexts.length!==102||map.contexts.reduce((n,r)=>n+r.occurrences.length,0)!==119||map.states.length!==8||map.supplementalTechnicalIdentifiers.length!==4)throw new Error('Exact occurrence specification changed');
 return true;
}
export const routes=Object.fromEntries(plan.pages.map(p=>[p.id,p.proposedPath]));
export const navigation=plan.navigation.mainMenu.map(x=>({label:ui[x.labelSource.split('.')[1]],href:x.href}));
export function mapTarget(value){if(!value||typeof value.href!=='string'||!['/',...navigation.map(x=>x.href)].includes(value.href))throw new Error('Unapproved target');return value.href;}
export const banners=plan.commonBanners.map(b=>({...b,id:b.variant,alt:copy.sharedBannerAlt[b.variant],renderSrc:b.publicPath}));
export const pages=[{id:'home',copyKey:'home',role:'primary-home',...home,path:routes.home},{id:'not-found',copyKey:'notFound',role:'technical-404',...copy.notFound,path:routes.notFound}];
export const pageMap={...previewConfig,articleCount:0,substantiveHomeCount:1,primaryCount:1,supportCount:0,facilityDetailCount:0,contentHtmlCount:1,technicalHtmlCount:1,allHtmlCount:2,previewIndexableCount:0,previewSitemapUrlCount:0,productionPlannedIndexableCount:1,nationalSelectionOrder:37,pages:pages.map(p=>({id:p.id,copyKey:p.copyKey,path:p.path,role:p.role,title:p.title,description:p.description,h1:p.h1,robots:'noindex,nofollow,noarchive',canonical:null,sitemapIncluded:false,mainMenuIncluded:p.id==='home',actualChildCount:0,marketingBannerCount:p.id==='home'?3:0,coreHub:false}))};
export function validateContract(c=copy,p=plan){
 if(!equal(Object.keys(c),['home','productCards','notFound','sharedUI','sharedBannerAlt']))throw new Error('Exact five-key native render schema required');
 if(!equal(c.home.sections.map(s=>s.id),['products','budget','ribbon','destinations','order'])||c.home.sections.some(s=>Object.hasOwn(s,'card'))||!equal(c.home.sections[0].productCardIds,['B201','B203','B205','B060']))throw new Error('Reviewed home section/card scope changed');
 if(!equal(p.region,{name:'곡성군',officialCode:'12720',legalCode:'1272000000',officialParent:'전남광주통합특별시',nationalOrder:37}))throw new Error('Region contract changed');
 if(p.origin!==null||p.domain!==null||p.productionEnabled!==false)throw new Error('Private copy scope changed');
 if(p.productCards.source!=='customer-copy.json#/productCards'||p.faq.source!=='customer-copy.json#/home/faq'||!p.faq.alwaysVisible||p.faq.accordion||p.faq.count!==3)throw new Error('Sole JSON or FAQ contract changed');
 if(!equal(p.pages.map(x=>[x.id,x.proposedPath]),[['home','/'],['notFound','/404.html']])||!equal(p.productionPolicy.sitemapPageIds,['home'])||p.productionPolicy.plannedIndexableURLCount!==1)throw new Error('Two-page/one-indexable route contract changed');
 if(c.home.faq.length!==3||new Set(c.home.faq.map(f=>f.question)).size!==3||c.productCards.map(p=>p.sku).join(',')!=='B201,B203,B205,B060')throw new Error('FAQ/product denominator changed');
 for(const [i,product] of c.productCards.entries())if(product.basePriceKRW!==[59000,79000,109000,149000][i]||product.additionalShippingKRW!==10000||product.referenceTotalKRW!==product.basePriceKRW+product.additionalShippingKRW||product.finalPriceKRW!==null||product.priceLabel!==`상품 기본가 ${product.basePriceKRW.toLocaleString('en-US')}원`||product.shippingLabel!=='곡성 게시 추가배송비 10,000원'||product.referenceTotalLabel!==`게시금액 합산 참고예산 ${product.referenceTotalKRW.toLocaleString('en-US')}원`||product.ctaHref!=='https://fwith.co.kr/shop/item.php?it_id='+product.sku)throw new Error('Product price/shipping/reference/destination changed');
 if(!equal(p.navigation.mainMenu,[{labelSource:'sharedUI.productsLink',href:'/#products'},{labelSource:'sharedUI.budgetLink',href:'/#budget'},{labelSource:'sharedUI.ribbonLink',href:'/#ribbon'},{labelSource:'sharedUI.orderLink',href:'/#order'},{labelSource:'sharedUI.faqLink',href:'/#faq'}]))throw new Error('Reviewed navigation changed');
 if(p.commonBanners.map(b=>b.variant).join(',')!=='message,budget,consultation'||p.commonBanners.some(b=>b.width!==1774||b.height!==887||b.caption!==null)||Object.values(c.sharedBannerAlt).some(s=>s.split('1844-0644').length!==2))throw new Error('Banner contract changed');
 if(p.pages.some(x=>x.previewRobots!=='noindex,nofollow,noarchive'||x.previewSitemapIncluded!==false||x.canonical!==null))throw new Error('Private robots contract changed');
 if(p.socialMetadata['og:image']!=='Verified origin + /images/products/B201.jpg'||p.socialMetadata['twitter:card']!=='summary'||p.pages[1].socialMetadataIncluded!==false||p.pages[1].canonicalAtProduction!==null)throw new Error('Social/404 contract changed');
 if(!equal(c,copy)||!equal(p,plan))throw new Error('Exact reviewed content and design required');
 if(c.home.cta.href!=='tel:18440644'||c.notFound.cta.href!=='/')throw new Error('CTA changed');return true;
}
export function validateRuntime(){assertBoundary();verifyInputs();validateContract();return true;}
validateRuntime();
