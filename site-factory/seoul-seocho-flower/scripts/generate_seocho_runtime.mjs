/** Deterministic projection from exact accepted Seocho inputs; does not write customer prose. */
import fs from 'node:fs';import crypto from 'node:crypto';import {spawnSync} from 'node:child_process';
import {regionalMetadata} from '../src/lib/regions.mjs';
const read=n=>JSON.parse(fs.readFileSync('src/data/'+n+'.json','utf8'));
const write=(n,v)=>fs.writeFileSync('src/data/'+n+'.json',JSON.stringify(v,null,2)+'\n');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const copy=read('seocho-copy'),plan=read('seocho-approved/plan/fixed-plan'),coverage=read('region-coverage'),policy=read('region-policy'),products=read('products'),acceptance=read('seocho-approved/handoff/acceptance');
if(acceptance.status!=='LOCAL_PLAN_AND_CUSTOMER_COPY_ACCEPTED')throw new Error('Exact copy approval required');
// Validate the sealed minimal amendment before generating any runtime file.
const correctionCheck=spawnSync('python3',['scripts/seocho_floor_correction.py'],{encoding:'utf8'});
if(correctionCheck.status!==0)throw new Error('Exact floor correction required: '+correctionCheck.stdout+correctionCheck.stderr);
const correction=read('seocho-corrections/floor-20261013/amendment');
const pages=copy.articles.map((a,index)=>{
 const approved=plan.pages.find(p=>p.slug===a.slug);if(!approved)throw new Error('Missing fixed article');
 const metadata=regionalMetadata(coverage,policy,products,a.slug);
 const sources=a.sourceLinks.map(s=>({...s,type:s.url.startsWith('https://fwith.co.kr/')?'business':'official',verifiedAt:'2026-10-13'}));
 const page={...a,description:a.metaDescription,pageKey:a.slug,category:'regions',routeType:'category',pageType:'regional-service',status:'approved',approvalVerified:true,file:'src/data/pages.json',order:index+1,sourceMode:'local-preparation',queryClass:approved.queryClass,assetSlot:'REAL_PROOF',visualIntent:index===0?'funeral_wreath':'congrats_wreath',relatedKeys:copy.articles.filter(x=>x.slug!==a.slug).map(x=>x.slug),productCardLimit:4,productCardCount:4,productCardKeys:a.productSkus.map(sku=>products.find(p=>p.officialSku===sku).key),...metadata,sources,source:sources.find(s=>s.type==='business'),secondary_keywords:approved.secondary_keywords,keyword_cluster:approved.keyword_cluster,query_class:approved.query_class,query_priority:approved.query_priority,query_evidence:approved.query_evidence};
 const omit=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);
 page.snapshotHash=sha(canonical(Object.fromEntries(Object.entries(page).filter(([k])=>!omit.has(k)))));
 page.snapshotId=`local-content-${page.slug}-${page.snapshotHash.slice(0,16)}`;return page;
});
write('pages',pages);
const records=pages.map(p=>{const result={...p};for(const key of ['sections','contentMarkdown','faq','uniqueBodyText'])delete result[key];return result;});
const siteKey=coverage.siteKey;
write('architecture',{schemaVersion:'1.2',siteKey,home:{pageRole:'REGION_SERVICE_LANDING',primaryKeyword:copy.common.home.primaryKeyword,url:'/',title:copy.common.home.title},hubs:[{category:'regions',children:2,indexable:false,label:copy.common.navigation.regions,menuVisible:false,url:'/regions/'}],pages:records.map(p=>({...p,status:'primary',pageRole:'REGION_SERVICE_LANDING',parentHub:'/regions/',contentRole:'question-answer',localizationPolicy:'local-required',sitemapIndexable:true}))});
const base={schemaVersion:2,siteKey,generatedFrom:'Exact accepted local customer copy plus bounded floor correction candidate',snapshotMode:'local-preparation',pages:records};
write('page-map',base);
write('publish-manifest',{...base,snapshotLedger:{},directRelease:{releaseId:coverage.scopeKey,sourceMode:'local-preparation',plannedOriginalCount:2,reviewedArticleCount:2,candidateArticleCount:2,regionArticleCount:2,sitemapUrlCount:0,intrinsicIndexableRouteCount:3,renderedHtmlRouteCount:5,publicationState:'local-runtime-review-pending',screenQa:'UNVERIFIED',deferredPageKeys:[],deferredRoutes:[],publishedCoverage:{numerator:0,denominator:2,percent:0},localReviewedCoverage:{numerator:2,denominator:2},publicSourceHashAlgorithm:'sha256-sorted-utf8-json-v1',contentHashes:pages.map(p=>({pageKey:p.pageKey,bodySha256:sha(p.contentMarkdown),publicSourceSha256:p.snapshotHash})),reusedRuntimeCommits:['ca5c98b12420212d0aa8dd0c9a742f3e94237c07','4f982994513cb7913f869b0114b3427be50b1362'],officialMembership:{legalUnits:10,administrativeUnits:18,relations:23,plannedRepresentedUnits:2,unrepresentedUnits:8,countIsPageQuota:false},representativeAssignment:coverage.representativeAssignment,reviewStatus:'COPY_CORRECTION_PENDING_INDEPENDENT_REVIEW',copyCorrection:{id:correction.id,amendmentSha256:sha(fs.readFileSync('src/data/seocho-corrections/floor-20261013/amendment.json')),runtimeCopySha256:correction.correctedRuntimeCopySha256,status:correction.status},independentPlanSha256:acceptance.planReview.sha256,fixedPlanSha256:acceptance.currentPlan.sha256,candidateInventory:{groups:8,physicalFacilities:3,buyerOccasions:1,separateUrlHoldDecisions:7},candidateLedger:plan.candidateLedger,heldPageDecisions:plan.heldPageDecisions,publicationAuthorized:false}});
write('direct-checkpoint',{schemaVersion:1,siteKey,scopeKey:coverage.scopeKey,status:'LOCAL_IMPLEMENTED_VERIFICATION_PENDING',candidate:{originalPlanN:2,renderedHtmlRoutes:5},productionEvidence:null,searchIndexing:{submitted:false,receipt:null},productionApproved:false,hostnameOwnershipVerified:false});
console.log('SEOCHO exact historical copy plus bounded correction candidate projected: 2 articles, 5 HTML routes, 0 published');
