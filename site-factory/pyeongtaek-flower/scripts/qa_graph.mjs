import fs from 'node:fs';
import {productFamilies,selectProducts} from '../src/lib/catalog.mjs';
import {validateCustomerIntent,customerText} from './qa_intent.mjs';
import {regionalRows,isRegional,assertRegionalMetadata,validateRegionalPurchase} from '../src/lib/regions.mjs';
export function validateHubMetadata(pages,architecture) {
 for(const h of architecture.hubs){
  const count=pages.filter(p=>p.category===h.category).length;
  if(h.children!==count)throw new Error('Stale hub child count '+h.url);
  if(h.indexable!==(count>=3)||h.menuVisible!==(count>=5))throw new Error('Stale hub index/menu policy '+h.url);
 }
}
export function validateGraph(data) {
 const {pages,manifest,map,architecture,products,coverage,policy}=data;
 regionalRows(pages,architecture,coverage,policy);
 if(!pages.length) throw new Error('No approved pages');
 const compatible={funeral:['funeral-facility','order-help','price-guide'],business:['business-opening'],school:['school-event'],event:['event-venue'],gift:['hospital-visit','personal-gift','station-transit'],order:['order-help','price-guide','message-guide'],regions:['regional-service']};
 const seen=new Set(), urls=new Set(), intents=new Set();
 for(const p of pages){
  if(!compatible[p.category]?.includes(p.pageType))throw new Error('Category/pageType mismatch '+p.pageKey);
  if(!p.pageKey || seen.has(p.pageKey))throw new Error('Duplicate/missing pageKey');seen.add(p.pageKey);
  if(!/^\/[a-z0-9-]+\/[a-z0-9-]+\/$/.test(p.url) || urls.has(p.url))throw new Error('Duplicate/unsafe URL '+p.url);urls.add(p.url);
  if(p.url!==`/${p.category}/${p.slug}/`)throw new Error('Route mismatch '+p.pageKey);
  if(!p.snapshotId)throw new Error('Missing snapshotId '+p.pageKey);
  if(!p.title || !p.h1 || !p.firstAnswer || !p.description || !p.cardSummary)throw new Error('Incomplete content '+p.pageKey);
  validateCustomerIntent(p,products);
  if(isRegional(p)){validateRegionalPurchase(p,products,customerText(p));assertRegionalMetadata(p,coverage,policy,products);}
  const a=architecture.pages.find(x=>x.pageKey===p.pageKey);
  const intent=a?.intentKey || p.intentKey || p.primaryKeyword;
  if(intents.has(intent))throw new Error('Intent collision '+intent);intents.add(intent);
  if(!p.source?.url || !p.source?.verifiedAt || new URL(p.source.url).protocol!=='https:')throw new Error('Missing source provenance '+p.pageKey);
  if(!architecture.hubs.some(h=>h.category===p.category&&h.url===`/${p.category}/`))throw new Error('Missing hub '+p.pageKey);
  const allowed=productFamilies(p), selected=selectProducts(p,products);
  if(selected.some(x=>!allowed.includes(x.family)))throw new Error('Product intent mismatch '+p.pageKey);
  for(const collection of [manifest.pages,map.pages,architecture.pages]){
   const entries=collection.filter(x=>x.pageKey===p.pageKey);
   if(entries.length!==1 || entries[0].url!==p.url || entries[0].snapshotId!==p.snapshotId)throw new Error('Registry parity '+p.pageKey);
   if(isRegional(p))assertRegionalMetadata(entries[0],coverage,policy,products);
  }
 }
 for(const p of pages) for(const key of p.relatedKeys||[])if(!seen.has(key)||key===p.pageKey)throw new Error('Invalid related key '+key);
 for(const collection of [manifest.pages,map.pages,architecture.pages])if(collection.length!==pages.length)throw new Error('Registry count mismatch');
 validateHubMetadata(pages,architecture);
 for(const p of products){
  if(!p.sourceUrl || !['operator_confirmed','official_business_source'].includes(p.sourceLevel) || p.assetType!=='real_product' || !p.verifiedAt)throw new Error('Unverified product '+p.key);
  if(p.orderUrl!=='https://fwith.co.kr'&&!p.orderUrl.startsWith('https://fwith.co.kr/'))throw new Error('Untrusted order destination '+p.key);
  if(!Number.isFinite(p.price)||p.price<0)throw new Error('Invalid product price '+p.key);
 }
 return {pages:pages.length,hubs:architecture.hubs.filter(h=>h.children>0).length};
}
export function loadGraph(root='.') {
 const read=name=>JSON.parse(fs.readFileSync(`${root}/src/data/${name}.json`,'utf8'));
 return {pages:read('pages'),manifest:read('publish-manifest'),map:read('page-map'),architecture:read('architecture'),products:read('products'),coverage:read('region-coverage'),policy:read('region-policy')};
}
if(process.argv[1]?.endsWith('/qa_graph.mjs'))console.log('GRAPH QA PASSED',validateGraph(loadGraph()));
