/** Explicit Seocho N2 adapter. Frozen research is not publication or delivery approval. */
import {createHash} from 'node:crypto';
import * as legacy from './regions-legacy.mjs';
import {pageSources} from './seocho-sources.mjs';
import frozenPlan from '../data/seocho-plan-binding.json' with {type:'json'};

export const assignment='seocho-grouped-occasion-context-v1';
export const siteKey='seoul-seocho-flower-direct';
export const scopeKey='seoul-seocho-direct-local-preparation-20261013';
export const contextFields=['candidateIds','purchaseIntentKey','contextKey','intentKey','facilityAnchors','buyerOccasionAnchors'];
export const frozenBindingSha256='8ff9c1dbf8882152b4275e4ce6dafbb5c0c3656663fe669be9834d056a454f83';
const intents=new Set(['funeral-condolence-wreath','celebration-congratulation-wreath']);
const fail=message=>{throw new Error('Seocho grouped: '+message);};
const canonical=value=>JSON.stringify(value,(_,item)=>item&&typeof item==='object'&&!Array.isArray(item)?Object.fromEntries(Object.keys(item).sort().map(key=>[key,item[key]])):item);
const same=(left,right)=>canonical(left)===canonical(right);
const own=(record,key)=>record!=null&&Object.hasOwn(record,key);
const kebab=value=>typeof value==='string'&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value);
const text=value=>typeof value==='string'&&value.trim()===value&&!!value&&!/[\p{Cc}\p{Cf}]/u.test(value);
const unique=(values,label)=>{if(!Array.isArray(values)||values.some(value=>!value)||new Set(values).size!==values.length)fail('duplicate/missing '+label);};
const exactKeys=(record,keys)=>record&&typeof record==='object'&&!Array.isArray(record)&&same(Object.keys(record).sort(),[...keys].sort());
export const isSeochoMode=(coverage,policy)=>coverage?.representativeAssignment===assignment||policy?.representativeAssignment===assignment||coverage?.siteKey===siteKey||policy?.siteKey===siteKey;

function validateFrozenBinding() {
 if(createHash('sha256').update(canonical(frozenPlan)).digest('hex')!==frozenBindingSha256)fail('frozen transform hash drift');
 if(frozenPlan.fixedPlanSha256!=='5675a7cc1cf5b142458133cb2fc55ce7224ca5e819b2e11f6684bc2d59728318')fail('original plan SHA binding drift');
 if(!same([frozenPlan.originalPlanN,frozenPlan.originalCandidateN,frozenPlan.activeCandidateN,frozenPlan.activePhysicalFacilityN,frozenPlan.activeBuyerOccasionN,frozenPlan.heldSeparateURLDecisionN],[2,8,4,3,1,7]))fail('frozen inventory denominator drift');
 unique(frozenPlan.candidateLedger.map(row=>row.id),'candidate group');
 unique(frozenPlan.heldPageDecisions.map(row=>row.id),'held separate URL decision');
 if(frozenPlan.candidateLedger.length!==8||frozenPlan.heldPageDecisions.length!==7)fail('held inventory drift');
}
function sourceIdentity(value) {
 pageSources({sources:[{url:value,name:'검증된 시설 원문',type:'official',verifiedAt:'2026-10-13'}]});
 if(!/^[\x21-\x7e]+$/.test(value)||/["'<>\{\}|`^]/u.test(value))fail('unsafe facility source URL');
 const url=new URL(value);
 if(!/^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:[a-z]{2,63}|xn--[a-z0-9-]+)$/i.test(url.hostname))fail('unsafe facility source hostname');
 url.hash='';url.pathname=url.pathname.replace(/\/+$/,'')||'/';return url.href;
}
function geography(coverage,policy) {
 // Only the new opt-in fields are removed for the unchanged shared geography validator.
 const c={...coverage,representatives:[]},p={...policy};
 for(const field of ['representativeAssignment','facilities','buyerOccasions','administrativeFacilityAssignments']){delete c[field];delete p[field];}
 legacy.validateDefinition(c,p);
}
function registry(coverage) {
 if(!Array.isArray(coverage.facilities)||coverage.facilities.length!==3||!Array.isArray(coverage.buyerOccasions)||coverage.buyerOccasions.length!==1)fail('exact three facilities and separate buyer occasion required');
 const result=new Map(),identities=new Set(),units=new Set(coverage.units.map(unit=>unit.unitKey));
 for(const facility of coverage.facilities){
  if(!exactKeys(facility,['facilityKey','name','sourceUrl','address','unitKey','districtKey','administrativeCode','aliases'])||!kebab(facility.facilityKey)||!text(facility.name)||!text(facility.address)||facility.districtKey!=='seoul-seocho-gu'||facility.administrativeCode!==null||result.has(facility.facilityKey))fail('invalid physical facility');
  if(!units.has(facility.unitKey))fail('physical facility legal assignment mismatch');
  const identity=JSON.stringify([sourceIdentity(facility.sourceUrl),facility.address.normalize('NFKC').replace(/\p{White_Space}+/gu,' ')]);
  if(identities.has(identity))fail('duplicate physical source/address identity');
  identities.add(identity);result.set(facility.facilityKey,{...facility,candidateId:facility.facilityKey,contextType:'physical-facility'});
 }
 for(const occasion of coverage.buyerOccasions){
  if(!exactKeys(occasion,['contextKey','name','contextType','districtKey','unitKey','legalCode','administrativeCode','physicalAddress','aliases','sourceEvidence'])||occasion.contextKey!=='opening-relocation-occasion'||occasion.contextType!=='buyer-occasion'||occasion.districtKey!=='seoul-seocho-gu'||!text(occasion.name)||result.has(occasion.contextKey)||['unitKey','legalCode','administrativeCode','physicalAddress'].some(key=>occasion[key]!==null))fail('invalid buyer occasion; no physical or geographic identity allowed');
  result.set(occasion.contextKey,{...occasion,candidateId:occasion.contextKey});
 }
 return result;
}
export function validateDefinition(coverage,policy) {
 if(coverage?.representativeAssignment!==assignment||policy?.representativeAssignment!==assignment||coverage.siteKey!==siteKey||policy.siteKey!==siteKey||coverage.scopeKey!==scopeKey||policy.scopeKey!==scopeKey)fail('site/scope/assignment opt-in mismatch');
 validateFrozenBinding();geography(coverage,policy);
 // Exact fields, not subset comparisons: unknown geographic or facility fields cannot smuggle claims.
 if(!same(coverage,frozenPlan.coverage))fail('frozen geography/registry/representative binding drift');
 if(!same(policy,frozenPlan.policy))fail('frozen policy/visual binding drift');
 if(coverage.units.length!==10||coverage.administrativeCrosswalk.length!==18||coverage.administrativeCrosswalk.flatMap(alias=>alias.relations).length!==23||coverage.membershipRelationCount!==23||!same(coverage.administrativeFacilityAssignments,[]))fail('official geography or administrative assignment drift');
 const registered=registry(coverage),assigned=new Set(),anchorIds=new Set();
 for(const field of ['pageKey','url','slug','intentKey','primaryKeyword'])unique(coverage.representatives.map(row=>row[field]),field);
 for(const row of coverage.representatives){
  if(!kebab(row.pageKey)||row.pageKey!==row.slug||row.url!==`/regions/${row.slug}/`||row.routeMode!=='regional'||row.status!=='approved'||!text(row.primaryKeyword)||!row.queryEvidence)fail('invalid canonical representative');
  unique(row.candidateIds,'candidate');
  if(!intents.has(row.purchaseIntentKey)||row.contextKey!=='seocho|'+row.purchaseIntentKey||own(row,'facilityKey')||own(row,'unitKey'))fail('invalid grouped context');
  const members=row.candidateIds.map(id=>{if(!registered.has(id)||assigned.has(id))fail('unknown/duplicate candidate');assigned.add(id);return registered.get(id);});
  const facilities=members.filter(member=>member.contextType==='physical-facility');
  const occasions=members.filter(member=>member.contextType==='buyer-occasion');
  const unitUnion=[...new Set(facilities.map(member=>member.unitKey).filter(key=>key!==null))];
  if(!same(row.unitKeys,unitUnion)||row.unitKeys.includes(null))fail('canonical legal unit union mismatch');
  if(row.facilityAnchors.length!==facilities.length||row.buyerOccasionAnchors.length!==occasions.length)fail('physical/occasion anchor membership mismatch');
  if(occasions.length&&row.purchaseIntentKey!=='celebration-congratulation-wreath')fail('buyer occasion purchase intent mismatch');
  for(const [anchors,contexts,isOccasion] of [[row.facilityAnchors,facilities,false],[row.buyerOccasionAnchors,occasions,true]]){
   for(let index=0;index<contexts.length;index++){
    const anchor=anchors[index],member=contexts[index],fields=['candidateId','anchor','heading','unitKey','href',...(isOccasion?['contextType']:[])];
    if(!exactKeys(anchor,fields)||anchor.candidateId!==member.candidateId||anchor.anchor!==(isOccasion?'opening-relocation':member.candidateId)||!kebab(anchor.anchor)||!text(anchor.heading)||anchor.unitKey!==member.unitKey||anchor.href!==row.url+'#'+anchor.anchor||anchorIds.has(anchor.anchor)||(isOccasion&&anchor.contextType!=='buyer-occasion'))fail('invalid/duplicate destination anchor');
    anchorIds.add(anchor.anchor);
   }
  }
 }
 if(assigned.size!==4||registered.size!==4||coverage.representatives.length!==2)fail('active context/page denominator mismatch');
 return coverage;
}
function assertContext(record,representative) {
 for(const field of contextFields)if(!same(record[field],representative[field]))fail('grouped context binding drift '+field);
 if(!same(record.regionUnitKeys,representative.unitKeys)||record.primaryKeyword!==representative.primaryKeyword||own(record,'facilityKey')||own(record,'unitKey')||(own(record,'unitKeys')&&!same(record.unitKeys,representative.unitKeys)))fail('grouped unit/keyword binding drift');
}
export function regionalRows(pages,architecture,coverage,policy) {
 validateDefinition(coverage,policy);
 const rows=pages.filter(legacy.isRegional),approved=coverage.representatives;
 unique(rows.map(row=>row.pageKey),'pageKey');unique(rows.map(row=>row.url),'url');
 if(architecture.siteKey!==siteKey||policy.enabled!==true||rows.length!==2||approved.some(row=>!rows.some(page=>page.pageKey===row.pageKey)))fail('approved route parity mismatch');
 for(const page of rows){
  const representative=approved.find(row=>row.pageKey===page.pageKey),nodes=architecture.pages.filter(node=>node.pageKey===page.pageKey),node=nodes[0];
  if(!representative||page.category!=='regions'||page.pageType!=='regional-service'||page.routeType!=='category'||page.url!==representative.url||page.slug!==representative.slug||page.scopeKey!==scopeKey||page.status!=='approved'||page.approvalVerified!==true||!page.snapshotId||!page.snapshotHash)fail('route/approval mismatch');
  if(nodes.length!==1||node.url!==page.url||node.slug!==page.slug||node.pageRole!=='REGION_SERVICE_LANDING'||node.parentHub!=='/regions/'||node.localizationPolicy!=='local-required'||node.scopeKey!==scopeKey)fail('architecture semantic mismatch');
  assertContext(page,representative);assertContext(node,representative);
 }
 return rows;
}
export function directoryGroups(pages,architecture,coverage,policy) {
 const rows=regionalRows(pages,architecture,coverage,policy),byKey=new Map(rows.map(row=>[row.pageKey,row]));
 // All two article cards live at district level once. No facility-to-administrative inference.
 return coverage.districts.map(district=>({...district,items:coverage.representatives.filter(row=>byKey.has(row.pageKey)).map(representative=>({representative,page:byKey.get(representative.pageKey),aliases:[]}))}));
}
export function aliasTargets(name,pages,architecture,coverage,policy) {
 const groups=directoryGroups(pages,architecture,coverage,policy);
 const legalUnits=coverage.units.filter(unit=>unit.name===name||unit.legalRi.includes(name)).map(unit=>unit.unitKey);
 const facilityIds=coverage.facilities.filter(facility=>facility.name===name||facility.aliases.includes(name)).map(facility=>facility.facilityKey);
 // A MOIS relation describes names and membership, not a facility's precise administrative address.
 return [...new Set(groups.flatMap(district=>district.items).flatMap(entry=>entry.representative.facilityAnchors.filter(anchor=>legalUnits.includes(anchor.unitKey)||facilityIds.includes(anchor.candidateId)).map(anchor=>anchor.href)))];
}
export function validatePurchaseIntent(page) {
 const representative=frozenPlan.coverage.representatives.find(row=>row.pageKey===page.pageKey);
 if(!representative||!intents.has(page.purchaseIntentKey)||page.purchaseIntentKey!==representative.purchaseIntentKey||page.intentKey!==representative.intentKey)fail('unknown/mismatched purchase intent');
 const visual=frozenPlan.policy.visualBindings.find(binding=>binding.pageKey===page.pageKey);
 const expectedFamily=page.purchaseIntentKey==='funeral-condolence-wreath'?'funeral':'congrats';
 if(page.regionalPurchaseMode!=='catalog'||!same(page.regionalProductFamilies,[expectedFamily])||!same(page.regionalProductKeys,visual.productKeys))fail('purchase intent/family/four-product binding mismatch');
}
function validateCatalog(products) {
 if(!Array.isArray(products)||products.length!==8)fail('exact eight-product catalog required');
 unique(products.map(product=>product.key||product.productKey),'product key');unique(products.map(product=>product.officialSku),'official SKU');
 for(const expected of frozenPlan.catalog){
  const product=products.find(row=>(row.key||row.productKey)===expected.key);
  if(!product)fail('missing exact catalog product '+expected.key);
  for(const field of ['officialSku','family','name','price','imageAlt','imageSha256','sourceUrl'])if(product[field]!==expected[field])fail('catalog '+field+' drift '+expected.key);
  if(product.img!==expected.image||product.orderUrl!==expected.sourceUrl)fail('catalog image/order destination drift '+expected.key);
 }
}
export function regionalMetadata(coverage,policy,products,pageKey) {
 validateDefinition(coverage,policy);validateCatalog(products);
 const row=coverage.representatives.find(representative=>representative.pageKey===pageKey);if(!row)fail('missing representative');
 const c={...coverage},p={...policy};
 for(const field of ['representativeAssignment','facilities','buyerOccasions','administrativeFacilityAssignments']){delete c[field];delete p[field];}
 c.representatives=coverage.representatives.map(representative=>{const out={...representative};for(const field of ['purchaseIntentKey','contextKey'])delete out[field];return out;});
 const output={...legacy.regionalMetadata(c,p,products,pageKey),...Object.fromEntries(contextFields.map(field=>[field,row[field]]))};
 validatePurchaseIntent({...output,pageKey});return output;
}
export function assertRegionalMetadata(record,coverage,policy,products) {
 const expected=regionalMetadata(coverage,policy,products,record.pageKey);
 for(const field of [...legacy.regionalMetadataFields,...contextFields])if(!same(record[field],expected[field]))fail('reviewed source binding drift '+field);
 assertContext(record,coverage.representatives.find(row=>row.pageKey===record.pageKey));return expected;
}
