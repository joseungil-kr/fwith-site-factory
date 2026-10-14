/** Exact approved strings -> local runtime metadata; no customer text generation. */
import fs from 'node:fs';import crypto from 'node:crypto';
import {regionalMetadata} from '../src/lib/regions.mjs';
const read=n=>JSON.parse(fs.readFileSync('src/data/'+n+'.json','utf8'));
const write=(n,v)=>fs.writeFileSync('src/data/'+n+'.json',JSON.stringify(v,null,2)+'\n');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const copy=read('gwanak-copy'),plan=read('gwanak-approved/inputs/plan/fixed-plan'),coverage=read('region-coverage'),policy=read('region-policy'),products=read('products'),acceptance=read('gwanak-approved/acceptance');
const pages=copy.articles.map((a,index)=>{
 const approved=plan.articles.find(p=>p.slug===a.slug);if(!approved)throw new Error('Missing fixed article');
 const metadata=regionalMetadata(coverage,policy,products,a.slug);
 const sources=a.sourceLinks.map(s=>({...s,type:s.url.startsWith('https://fwith.co.kr/')?'business':'official',verifiedAt:'2026-10-13'}));
 const page={...a,description:a.metaDescription,pageKey:a.slug,category:'regions',routeType:'category',pageType:'regional-service',status:'approved',approvalVerified:true,file:'src/data/pages.json',order:index+1,sourceMode:'direct-git',queryClass:approved.queryClass,assetSlot:'REAL_PROOF',visualIntent:index===0?'funeral_wreath':'congrats_wreath',relatedKeys:copy.articles.filter(x=>x.slug!==a.slug).map(x=>x.slug),productCardLimit:4,productCardCount:4,productCardKeys:a.productSkus.map(sku=>products.find(p=>p.officialSku===sku).key),...metadata,sources,source:sources[0],secondary_keywords:approved.secondaryKeywords,keyword_cluster:approved.keywordCluster,query_class:approved.queryClass,query_priority:approved.queryPriority,query_evidence:approved.queryEvidence};
 // Reviewed original contentMarkdown is retained as evidence; rendered sections contain the body once.
 const omit=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);
 page.snapshotHash=sha(canonical(Object.fromEntries(Object.entries(page).filter(([k])=>!omit.has(k)))));
 page.snapshotId=`direct-content-${page.slug}-${page.snapshotHash.slice(0,16)}`;return page;
});
write('pages',pages);
const records=pages.map(p=>{const result={...p};for(const key of ['sections','contentMarkdown','faq','uniqueBodyText'])delete result[key];return result;});
const siteKey=coverage.siteKey;
write('architecture',{schemaVersion:'1.2',siteKey,home:{pageRole:'REGION_SERVICE_LANDING',primaryKeyword:'관악구 화환',url:'/',title:copy.common.home.title},hubs:[{category:'regions',children:2,indexable:false,label:copy.common.navigation.regions,menuVisible:false,url:'/regions/'}],pages:records.map(p=>({...p,status:'primary',pageRole:'REGION_SERVICE_LANDING',parentHub:'/regions/',contentRole:'question-answer',localizationPolicy:'local-required',sitemapIndexable:true}))});
const base={schemaVersion:2,siteKey,generatedFrom:'Direct Git customer-content source',snapshotMode:'direct-git-content',pages:records};
write('page-map',base);
write('publish-manifest',{...base,snapshotLedger:{},directRelease:{releaseId:coverage.scopeKey,sourceMode:'direct-git',plannedOriginalCount:2,reviewedArticleCount:2,candidateArticleCount:2,regionArticleCount:2,sitemapUrlCount:0,intrinsicIndexableRouteCount:3,renderedHtmlRouteCount:5,publicationState:'local-runtime-review-pending',screenQa:'UNVERIFIED',deferredPageKeys:[],deferredRoutes:[],publishedCoverage:{numerator:0,denominator:2,percent:0},localReviewedCoverage:{numerator:2,denominator:2},publicSourceHashAlgorithm:'sha256-sorted-utf8-json-v1',contentHashes:pages.map(p=>({pageKey:p.pageKey,bodySha256:sha(p.contentMarkdown),publicSourceSha256:p.snapshotHash})),reusedRuntimeCommits:['ca5c98b12420212d0aa8dd0c9a742f3e94237c07','430dada32f3f8b53f24aec8d9fdf3724529604e1'],officialMembership:{legalUnits:3,administrativeUnits:21,relations:21,plannedRepresentedUnits:2,unrepresentedUnits:1,countIsPageQuota:false},representativeAssignment:coverage.representativeAssignment,reviewStatus:'COPY_INPUT_PASS_RUNTIME_PENDING',independentPlanSha256:acceptance.planVerdict.sha256,fixedPlanSha256:acceptance.plan.sha256,candidateInventory:{original:15,active:5,physicalFacilities:4,buyerOccasions:1,held:10},publicationAuthorized:false}});
write('direct-checkpoint',{schemaVersion:1,siteKey,scopeKey:coverage.scopeKey,status:'LOCAL_IMPLEMENTED_VERIFICATION_PENDING',candidate:{originalPlanN:2,renderedHtmlRoutes:5},productionEvidence:null,searchIndexing:{submitted:false,receipt:null},productionApproved:false,hostnameOwnershipVerified:false});
console.log('GWANAK exact approved runtime generated:2 articles,5 HTML routes,0 published');
