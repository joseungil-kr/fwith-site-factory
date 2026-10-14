/** Deterministic local successor reconstruction from reviewed Gangnam rev4 inputs.
 * The retained data is a reconstruction oracle, not recovered implementation source.
 * No remote calls, new customer copy, publication approval, or historical QA claims.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {regionalMetadata,regionalRows,validateDefinition} from '../src/lib/regions.mjs';
import {pageSources} from '../src/lib/gangnam-sources.mjs';
export const projectRoot=fileURLToPath(new URL('../',import.meta.url));
export const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
export const canonical=value=>JSON.stringify(value,(_,item)=>item&&typeof item==='object'&&!Array.isArray(item)?Object.fromEntries(Object.keys(item).sort().map(key=>[key,item[key]])):item);
const same=(a,b)=>canonical(a)===canonical(b);
const fail=reason=>{throw new Error('Gangnam runtime: '+reason);};
export const inputPins={
 'gangnam-approved/plan/fixed-plan':'82bf53fb58d01c65d7fe87e730fcaf39ec60620603f671696074ba41510e68c3',
 'gangnam-approved/plan/candidate-inventory':'c4f10d104402b5c7635141b7fc7de4130e1be5a44c6046c202edfdbe71a45175',
 'gangnam-approved/plan/membership':'38232426ff252a356e0ed2655577316292d57daaa57dd9d5334141131559d685',
 'gangnam-approved/copy/article-copy.final':'6aa8e1f7acefaed276486ebefbb93bddb1e9b5eb1b15023ed9d7fda3ec3daeb3',
 'gangnam-approved/copy/common-visible-copy.final':'da15580bb4f05ae39a60a51d6bdc3fe9fcc65d9e2d738dcd573ebc483aa70cdd',
 'gangnam-approved/handoff/runtime-input':'a1cbb9a616a3558afc2d3e037e8ca6d6297591ae0d4c2ad14f2d5e80b88635e3',
 'gangnam-approved/handoff/approved-assets':'cdc9c486ad7f141c42abf4ad89c68293eeba5277203edafb8ab0da39e87ad511',
 'gangnam-approved/handoff/directory-input':'fdfb903a200d1add7ac769efbd1dbe28b3afce35c1a539a7db73bf1b3a31fea1',
 'gangnam-approved/handoff/acceptance':'e603f88799f71cca0cc91f824570d53f5426226d47c1f26f7ac229f4d460374c',
 'gangnam-a04-rev4/revised-input/copy/article-copy.rev4':'ca721a7a712c7814b21599d7a16d49e9476465527213c8496a1c2d2bb61b3e0f',
 'gangnam-a04-rev4/revised-input/handoff/runtime-input.rev4':'0927a9a0acde256900e41377819c46fe89118dea2e33ffada13afbe233f62f82',
 'gangnam-a04-rev4/mapping/keyword-mapping.rev4.final':'fd4f54ac139055fabe6694c316286afcb7b22792cb77133cf8c56f54b9f0c5e4',
 'gangnam-a04-rev4/revised-input/input-manifest.rev4':'ecae498ef320e9122f665f3db1787f6084a4084042fce0d5e03114216ae790ca',
 'gangnam-a04-rev4/revised-input/acceptance.rev4':'63d3244d9d060b3a96f8cdb35cc383453edda00e3d3fa2c7350648baa1d4176c',
 'gangnam-plan-binding':'a7b79a18e01423861cede3916e23f483bc042d7712ec8229238121cce6b0e923'
};
export function loadGangnamInputs(root=projectRoot){
 const read=name=>JSON.parse(fs.readFileSync(path.join(root,'src/data',name+'.json'),'utf8'));
 const pinned={};
 for(const [name,expected] of Object.entries(inputPins)){
  const bytes=fs.readFileSync(path.join(root,'src/data',name+'.json'));
  if(sha(bytes)!==expected)fail('input SHA binding drift '+name);
  pinned[name]=JSON.parse(bytes.toString('utf8'));
 }
 return {pinned,coverage:read('region-coverage'),policy:read('region-policy'),products:read('products')};
}
export const a04Fields=['primary_keyword','secondary_keywords','keyword_cluster','query_class','query_priority','query_evidence','title_alignment_score','title_alignment_raw_score','title_alignment_status','title_alignment_gates','alignment_provenance','query_priority_semantics'];
export function projectGangnamRuntime({pinned,coverage,policy,products}){
 // Recheck in-memory values too: callers cannot mutate a previously verified input.
 for(const [name,expected] of Object.entries(inputPins)){
  const original=fs.readFileSync(path.join(projectRoot,'src/data',name+'.json'));
  if(sha(original)!==expected||!same(pinned[name],JSON.parse(original.toString('utf8'))))fail('verified input object drift '+name);
 }
 const frozen=pinned['gangnam-plan-binding'];
 const plan=pinned['gangnam-approved/plan/fixed-plan'];
 const runtime=pinned['gangnam-a04-rev4/revised-input/handoff/runtime-input.rev4'];
 const article=pinned['gangnam-a04-rev4/revised-input/copy/article-copy.rev4'];
 const common=pinned['gangnam-approved/copy/common-visible-copy.final'].common;
 const a04=pinned['gangnam-a04-rev4/mapping/keyword-mapping.rev4.final'];
 const inputManifest=pinned['gangnam-a04-rev4/revised-input/input-manifest.rev4'];
 const acceptance=pinned['gangnam-a04-rev4/revised-input/acceptance.rev4'];
 validateDefinition(coverage,policy);
 if(!same(runtime.articles,article.articles)||!same(runtime.common,common))fail('logical article/common projection drift');
 if(!same([plan.originalPlanN,plan.routeDenominator.length,runtime.originalPlanN,inputManifest.originalPlanN,inputManifest.routeDenominator,inputManifest.a04PrimaryDenominator,inputManifest.a04NonPrimaryDenominator],[3,6,3,3,6,4,2]))fail('frozen denominator drift');
 if(acceptance.status!=='LOCAL_REV4_EXACT_COPY_AND_A04_INPUT_REVIEWED_ONLY'||acceptance.productionApprovedByThisDocument!==false)fail('review/publication boundary drift');
 if(a04.records.length!==4||a04.nonPrimaryRoutes.length!==2||new Set(a04.records.map(record=>record.url)).size!==4)fail('A04 primary/non-primary denominator drift');
 if(!same(runtime.publication,{sourceCommit:null,canonicalHostname:null,productionApproved:false,hostnameOwnershipVerified:false,publicHttpVerified:false,indexNowSubmitted:false}))fail('local publication boundary drift');
 const copy={articles:runtime.articles,common:runtime.common};
 const a04InputBinding={articleRevision:4,inputManifestSha256:frozen.inputOverlay.inputManifestSha256,acceptanceSha256:frozen.inputOverlay.acceptanceSha256,mappingSha256:frozen.inputOverlay.a04MappingSha256};
 const alignment=url=>{
  const record=a04.records.find(record=>record.url===url);
  if(!record||record.title_alignment_score!==100||record.title_alignment_raw_score!==100||record.query_priority!==1||record.title_alignment_status!=='A04_ALIGNMENT_MEETS_INTERNAL_THRESHOLD')fail('A04 URL/score/tier binding drift '+url);
  return {...Object.fromEntries(a04Fields.map(field=>[field,record[field]])),a04:record,a04InputBinding};
 };
 const pages=copy.articles.map((article,index)=>{
  const approved=plan.pages.find(page=>page.slug===article.slug);
  if(!approved||approved.url!==article.url||approved.id!==article.id)fail('missing fixed article');
  const contentMarkdown=[article.firstAnswer,...article.sections.map(section=>['## '+section.heading,...section.paragraphs].join('\n\n'))].join('\n\n');
  const uniqueBodyText=article.sections.flatMap(section=>section.paragraphs).join('\n\n');
  const metadata=regionalMetadata(coverage,policy,products,article.slug);
  // verifiedAt is the retained approved-input observation date, not a fresh source/network verification.
  const sources=pageSources({sources:article.sourceLinks.map(source=>({...source,type:source.url.startsWith('https://fwith.co.kr/')?'business':'official',verifiedAt:'2026-10-13'}))});
  const page={...article,contentMarkdown,uniqueBodyText,description:article.metaDescription,pageKey:article.slug,category:'regions',routeType:'category',pageType:'regional-service',status:'approved',approvalVerified:true,file:'src/data/pages.json',order:index+1,sourceMode:'local-preparation',queryClass:approved.queryClass,assetSlot:'REAL_PROOF',visualIntent:index===0?'funeral_wreath':'congrats_wreath',relatedKeys:copy.articles.filter(other=>other.slug!==article.slug).map(other=>other.slug),productCardLimit:4,productCardCount:4,productCardKeys:article.productSkus.map(sku=>products.find(product=>product.officialSku===sku)?.key),...metadata,sources,source:sources.find(source=>source.type==='business'),...alignment(article.url)};
  if(page.primaryKeyword!==page.primary_keyword||page.queryClass!==page.query_class||page.intentKey!==page.keyword_cluster)fail('A04 article intent/keyword binding drift');
  const omit=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);
  page.snapshotHash=sha(canonical(Object.fromEntries(Object.entries(page).filter(([key])=>!omit.has(key)))));
  page.snapshotId=`local-content-${page.slug}-${page.snapshotHash.slice(0,16)}`;
  return page;
 });
 const records=pages.map(page=>{const result={...page};for(const key of ['sections','contentMarkdown','faq','uniqueBodyText'])delete result[key];return result;});
 const siteKey=coverage.siteKey,homeMetadata=alignment('/');
 const architecture={schemaVersion:'1.2',siteKey,home:{pageRole:'REGION_SERVICE_LANDING',primaryKeyword:copy.common.home.primaryKeyword,url:'/',title:copy.common.home.title,...homeMetadata},a04NonPrimary:a04.nonPrimaryRoutes,hubs:[{category:'regions',children:3,indexable:true,label:copy.common.navigation.regions,menuVisible:false,url:'/regions/'}],pages:records.map(page=>({...page,status:'primary',pageRole:'REGION_SERVICE_LANDING',parentHub:'/regions/',contentRole:'question-answer',localizationPolicy:'local-required',sitemapIndexable:true}))};
 const base={schemaVersion:2,siteKey,generatedFrom:'Exact accepted local customer copy',snapshotMode:'local-preparation',homeMetadata,a04NonPrimary:a04.nonPrimaryRoutes,pages:records};
 const manifest={...base,snapshotLedger:{},directRelease:{releaseId:coverage.scopeKey,sourceMode:'local-preparation',plannedOriginalCount:3,reviewedArticleCount:3,candidateArticleCount:3,regionArticleCount:3,sitemapUrlCount:0,intrinsicIndexableRouteCount:5,renderedHtmlRouteCount:6,publicationState:'local-runtime-review-pending',screenQa:'UNVERIFIED',inputOverlay:frozen.inputOverlay,a04PrimaryCount:4,a04NonPrimaryCount:2,deferredPageKeys:[],deferredRoutes:[],publishedCoverage:{numerator:0,denominator:3,percent:0},localReviewedCoverage:{numerator:3,denominator:3},publicSourceHashAlgorithm:'sha256-sorted-utf8-json-v1',contentHashes:pages.map(page=>({pageKey:page.pageKey,bodySha256:sha(page.contentMarkdown),publicSourceSha256:page.snapshotHash})),
 // Retained historical metadata only; the successor's actual code provenance is recorded separately.
 reusedRuntimeSourceContentSha256:'e4babffe6b37215f1278b23652f3c8781321a094f67663fd6910e5e6bc4fb45d',sourceCommit:null,officialMembership:{legalUnits:14,administrativeUnits:22,relations:31,plannedRepresentedUnits:3,unrepresentedUnits:11,countIsPageQuota:false},representativeAssignment:coverage.representativeAssignment,reviewStatus:'COPY_INPUT_REVIEWED_RUNTIME_PENDING',independentPlanSha256:frozen.planReviewSha256,fixedPlanSha256:frozen.fixedPlanSha256,candidateInventory:{groups:12,physicalFacilities:5,buyerOccasions:0,separateUrlHoldDecisions:6},candidateLedger:frozen.candidateLedger,heldPageDecisions:frozen.heldPageDecisions,publicationAuthorized:false}};
 const checkpoint={schemaVersion:1,siteKey,scopeKey:coverage.scopeKey,status:'LOCAL_IMPLEMENTED_VERIFICATION_PENDING',candidate:{originalPlanN:3,renderedHtmlRoutes:6},inputOverlay:frozen.inputOverlay,a04:{primaryCount:4,nonPrimaryCount:2,internalReviewedScores:a04.records.map(record=>record.title_alignment_score),notSeoPerformance:true},productionEvidence:null,searchIndexing:{submitted:false,receipt:null},productionApproved:false,hostnameOwnershipVerified:false};
 regionalRows(pages,architecture,coverage,policy);
 return {pages,architecture,'page-map':base,'publish-manifest':manifest,'direct-checkpoint':checkpoint,'gangnam-copy':copy,'gangnam-ui-copy':{accessibility:common.accessibility,articleUi:common.articleUi},'gangnam-a04-metadata':a04};
}
export function verifyGangnamRuntime(outputs,expected=projectGangnamRuntime(loadGangnamInputs())){
 for(const [name,value] of Object.entries(expected))if(!same(outputs[name],value))fail('runtime projection drift '+name);
 return true;
}
export function regenerateGangnamRuntime({root=projectRoot,check=false}={}){
 const output=projectGangnamRuntime(loadGangnamInputs(root));
 if(check){
  const actual=Object.fromEntries(Object.keys(output).map(name=>[name,JSON.parse(fs.readFileSync(path.join(root,'src/data',name+'.json'),'utf8'))]));
  verifyGangnamRuntime(actual,output);
 }else for(const [name,value] of Object.entries(output))fs.writeFileSync(path.join(root,'src/data',name+'.json'),JSON.stringify(value,null,2)+'\n');
 return output;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 regenerateGangnamRuntime({check:process.argv.includes('--check')});
 console.log('GANGNAM rev4 exact local runtime '+(process.argv.includes('--check')?'verified':'regenerated')+': 3 articles, 6 expected HTML routes, 4 primary A04 records, 0 published.');
}
