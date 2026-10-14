/** Explicit Geumcheon grouped destination model. A plan does not grant publication permission. */
import * as legacy from './regions-legacy.mjs';
import {pageSources} from './sources.mjs';
import frozenPlan from '../data/geumcheon-plan-binding.json' with {type:'json'};
export const assignment='geumcheon-grouped-funeral-context-v1';
export const siteKey='seoul-geumcheon-flower-direct';
export const scopeKey='seoul-geumcheon-direct-independent-preparation-20261012';
export const contextFields=['candidateIds','purchaseIntentKey','contextKey','intentKey','facilityAnchors'];
const intents=new Set(['funeral-condolence-wreath']);
const fail=message=>{throw new Error('Geumcheon grouped: '+message);};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const kebab=x=>typeof x==='string'&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(x);
const own=(x,k)=>x!=null&&Object.hasOwn(x,k);
const unique=(values,label)=>{if(!Array.isArray(values)||values.some(v=>!v)||new Set(values).size!==values.length)fail('duplicate/missing '+label);};
const text=x=>typeof x==='string'&&x.trim()===x&&!!x&&!/[\p{Cc}\p{Cf}]/u.test(x);
const exactKeys=(x,keys)=>x&&typeof x==='object'&&!Array.isArray(x)&&same(Object.keys(x).sort(),[...keys].sort());
export const isGeumcheonMode=(c,p)=>c?.representativeAssignment===assignment||p?.representativeAssignment===assignment||c?.siteKey===siteKey||p?.siteKey===siteKey;
function sourceIdentity(value){
 pageSources({sources:[{url:value,name:'검증된 시설 원문',type:'official',verifiedAt:'2026-10-12'}]});
 if(!/^[\x21-\x7e]+$/.test(value)||/["'<>\{\}|`^]/u.test(value))fail('unsafe facility source URL');
 const u=new URL(value);if(!/^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:[a-z]{2,63}|xn--[a-z0-9-]+)$/i.test(u.hostname))fail('unsafe facility source hostname');
 u.hash='';u.pathname=u.pathname.replace(/\/+$/,'')||'/';return u.href;
}
function geography(c,p){
 const cc={...c,representatives:[]},pp={...p};
 for(const k of ['representativeAssignment','facilities','areaContexts']){delete cc[k];delete pp[k];}
 legacy.validateDefinition(cc,pp);
}
function registry(c){
 if(!Array.isArray(c.facilities)||c.facilities.length!==2||!Array.isArray(c.areaContexts)||c.areaContexts.length!==0)fail('exact two-facility registry required');
 const result=new Map(),identity=new Set(),units=new Set(c.units.map(u=>u.unitKey));
 for(const f of c.facilities){
  if(!exactKeys(f,['facilityKey','name','sourceUrl','address','unitKey'])||!kebab(f.facilityKey)||!text(f.name)||!text(f.address)||!units.has(f.unitKey)||result.has(f.facilityKey))fail('invalid physical facility');
  const id=JSON.stringify([sourceIdentity(f.sourceUrl),f.address.normalize('NFKC').replace(/\p{White_Space}+/gu,' ')]);
  if(identity.has(id))fail('duplicate facility source/address identity');identity.add(id);result.set(f.facilityKey,{...f,candidateId:f.facilityKey,contextType:'physical-facility'});
 }
 for(const a of c.areaContexts){
  if(!exactKeys(a,['contextKey','name','sourceUrl','unitKey','contextType'])||a.contextType!=='area-context'||!kebab(a.contextKey)||!text(a.name)||!units.has(a.unitKey)||result.has(a.contextKey))fail('invalid area context; no physical address allowed');
  sourceIdentity(a.sourceUrl);result.set(a.contextKey,{...a,candidateId:a.contextKey});
 }
 return result;
}
export function validateDefinition(c,p){
 if(c?.representativeAssignment!==assignment||p?.representativeAssignment!==assignment||c.siteKey!==siteKey||p.siteKey!==siteKey||c.scopeKey!==scopeKey||p.scopeKey!==scopeKey)fail('site/scope/assignment opt-in mismatch');
 geography(c,p);
 if(frozenPlan.originalPlanN!==1||frozenPlan.originalCandidateN!==10||frozenPlan.activeCandidateN!==2||c.units.length!==3||c.administrativeCrosswalk.length!==10||c.administrativeCrosswalk.flatMap(a=>a.relations).length!==10)fail('frozen Geumcheon inventory mismatch');
 if(c.membershipSourceSha256!==frozenPlan.membershipSourceSha256||!same(c.units,frozenPlan.units)||!same(c.administrativeCrosswalk,frozenPlan.administrativeCrosswalk))fail('official membership binding drift');
 if(!same(c.facilities,frozenPlan.facilities)||!same(c.areaContexts,frozenPlan.areaContexts))fail('frozen plan registry drift');
 for(const r of c.representatives){const bound=frozenPlan.representatives.find(x=>x.pageKey===r.pageKey);if(!bound||Object.keys(bound).some(k=>!same(r[k],bound[k])))fail('frozen plan member/anchor binding drift');}
 if(c.representatives.length!==frozenPlan.originalPlanN)fail('frozen plan denominator drift');
 const reg=registry(c),assigned=new Set(),anchors=new Set();
 for(const field of ['pageKey','url','slug','intentKey','primaryKeyword'])unique(c.representatives.map(r=>r[field]),field);
 for(const r of c.representatives){
  if(!kebab(r.pageKey)||!kebab(r.slug)||r.url!==`/regions/${r.slug}/`||r.routeMode!=='regional'||!['candidate','approved','reserved'].includes(r.status)||!text(r.primaryKeyword)||!r.queryEvidence)fail('invalid representative');
  unique(r.candidateIds,'candidate');if(!r.candidateIds.length||!intents.has(r.purchaseIntentKey)||r.contextKey!=='geumcheon|'+r.purchaseIntentKey||r.intentKey!=='seoul-geumcheon|'+r.purchaseIntentKey||own(r,'facilityKey'))fail('invalid canonical grouped context');
  const members=r.candidateIds.map(id=>{if(!reg.has(id)||assigned.has(id))fail('unknown/duplicate candidate');assigned.add(id);return reg.get(id);});
  const union=[...new Set(members.map(m=>m.unitKey))];
  if(!same(r.unitKeys,union)||own(r,'unitKey'))fail('canonical unit union mismatch');
  if(members.some(m=>m.contextType==='area-context')&&(members.length!==1||r.purchaseIntentKey!=='opening-congrats-wreath'))fail('area intent mismatch');
  if(!Array.isArray(r.facilityAnchors)||r.facilityAnchors.length!==members.length)fail('anchor membership mismatch');
  for(let i=0;i<members.length;i++){
   const a=r.facilityAnchors[i],m=members[i];
   if(!exactKeys(a,['candidateId','anchor','heading','unitKey','href'])||a.candidateId!==m.candidateId||a.anchor!==m.candidateId||!kebab(a.anchor)||a.heading!==m.name||a.unitKey!==m.unitKey||a.href!==r.url+'#'+a.anchor||anchors.has(a.anchor))fail('invalid/duplicate facility anchor');
   anchors.add(a.anchor);
  }
 }
 if(assigned.size!==reg.size)fail('unassigned active context');
 return c;
}
function assertContext(record,r){
 for(const key of contextFields)if(!same(record[key],r[key]))fail('grouped context binding drift '+key);
 if(!same(record.regionUnitKeys,r.unitKeys)||record.primaryKeyword!==r.primaryKeyword||own(record,'facilityKey')||own(record,'unitKey'))fail('grouped unit/keyword binding drift');
}
export function regionalRows(pages,a,c,p){
 validateDefinition(c,p);const rows=pages.filter(legacy.isRegional),approved=c.representatives.filter(r=>r.status==='approved');
 unique(rows.map(x=>x.pageKey),'pageKey');unique(rows.map(x=>x.url),'url');
 if(a.siteKey!==siteKey||p.enabled!==true||rows.length!==approved.length||approved.some(r=>!rows.some(x=>x.pageKey===r.pageKey)))fail('approved route parity mismatch');
 for(const page of rows){
  const r=approved.find(r=>r.pageKey===page.pageKey),nodes=a.pages.filter(n=>n.pageKey===page.pageKey),n=nodes[0];
  if(!r||page.category!=='regions'||page.pageType!=='regional-service'||page.routeType!=='category'||page.url!==r.url||page.slug!==r.slug||page.scopeKey!==scopeKey||page.status!=='approved'||page.approvalVerified!==true||!page.snapshotId||!page.snapshotHash)fail('route/approval mismatch');
  if(nodes.length!==1||n.url!==page.url||n.slug!==page.slug||n.pageRole!=='REGION_SERVICE_LANDING'||n.parentHub!=='/regions/'||n.localizationPolicy!=='local-required'||n.scopeKey!==scopeKey)fail('architecture semantic mismatch');
  assertContext(page,r);assertContext(n,r);
 }
 return rows;
}
export function directoryGroups(pages,a,c,p){
 const rows=regionalRows(pages,a,c,p),byKey=new Map(rows.map(row=>[row.pageKey,row]));
 return c.districts.map(d=>({...d,items:c.representatives.filter(r=>byKey.has(r.pageKey)&&r.unitKeys.some(k=>c.units.find(u=>u.unitKey===k).districtKeys.includes(d.key))).map(r=>({representative:r,page:byKey.get(r.pageKey),aliases:c.administrativeCrosswalk.filter(x=>x.districtKey===d.key&&x.relations.some(rel=>r.unitKeys.includes(rel.unitKey))).map(x=>({name:x.name,scope:x.relations.find(rel=>r.unitKeys.includes(rel.unitKey)).scope}))}))})).filter(d=>d.items.length);
}
export function aliasTargets(name,pages,a,c,p){
 const groups=directoryGroups(pages,a,c,p),unitKeys=c.units.filter(u=>u.name===name||u.legalRi.includes(name)).map(u=>u.unitKey);
 const aliases=c.administrativeCrosswalk.filter(x=>x.name===name);for(const x of aliases)for(const rel of x.relations)unitKeys.push(rel.unitKey);
 return [...new Set(groups.flatMap(d=>d.items).flatMap(e=>e.representative.facilityAnchors.filter(a=>unitKeys.includes(a.unitKey)).map(a=>a.href)))];
}
export function validatePurchaseIntent(page){
 if(!intents.has(page.purchaseIntentKey))fail('unknown purchase intent');
 const expected=page.purchaseIntentKey==='funeral-condolence-wreath'?'funeral':'congrats';
 if(page.regionalPurchaseMode==='catalog'&&!same(page.regionalProductFamilies,[expected]))fail('purchase intent/family mismatch');
}
export function regionalMetadata(c,p,products,key){
 validateDefinition(c,p);const r=c.representatives.find(x=>x.pageKey===key);if(!r)fail('missing representative');
 // The old metadata validator remains authoritative for SKU and image bindings.
 const cc={...c},pp={...p};delete cc.representativeAssignment;delete pp.representativeAssignment;delete cc.facilities;delete cc.areaContexts;cc.representatives=c.representatives.map(row=>{const out={...row};delete out.facilityKey;delete out.purchaseIntentKey;delete out.contextKey;return out;});
 const base=legacy.regionalMetadata(cc,pp,products,key);
 const output={...base,...Object.fromEntries(contextFields.map(k=>[k,r[k]]))};validatePurchaseIntent(output);return output;
}
export function assertRegionalMetadata(record,c,p,products){
 const expected=regionalMetadata(c,p,products,record.pageKey);
 for(const field of [...legacy.regionalMetadataFields,...contextFields])if(!same(record[field],expected[field]))fail('reviewed source binding drift '+field);
 assertContext(record,c.representatives.find(r=>r.pageKey===record.pageKey));return expected;
}
