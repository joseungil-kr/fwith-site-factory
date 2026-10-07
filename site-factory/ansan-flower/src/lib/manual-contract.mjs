import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {validateManualRegions} from './manual-regions.mjs';
import {loadSiteProducts} from './site-catalog.mjs';
export const WRITER_ID='wr6d547b77f81df4c03dcb151d';
export const EXPECTED_REVIEWER_ID='rvc2ed89ba6195167edeb9e7c1';
export const digest=value=>crypto.createHash('sha256').update(value).digest('hex');
const read=(root,file)=>JSON.parse(fs.readFileSync(path.join(root,file),'utf8'));
const files=(dir)=>fs.existsSync(dir)?fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?files(path.join(dir,e.name)):[path.join(dir,e.name)]):[];
export function manualBuildMode(env={}) {
 const target=new URL(env.SITE_URL||'https://ansan.fwith.kr');
 const local=target.protocol==='http:'&&['localhost','127.0.0.1','[::1]'].includes(target.hostname)&&!target.username&&!target.password;
 const preview=env.MANUAL_PREVIEW==='1'&&env.SITE_INDEXABLE==='false'&&local;
 if(env.MANUAL_PREVIEW==='1'&&!preview)throw new Error('Manual preview requires explicit local HTTP origin and noindex');
 return {preview,production:!preview};
}
export function manualDigests(root) {
 const contentFiles=files(path.join(root,'src/content/manual')).filter(f=>f.endsWith('.md')).sort();
 const content=contentFiles.map(f=>[path.relative(root,f),digest(fs.readFileSync(f))]);
 const catalogFiles=['src/data/products.json','src/data/site-catalog.json','src/data/site-catalog-evidence.json','src/data/business-truth.json','src/data/manual-regional-bindings.json','src/data/region-coverage.json','src/data/region-policy.json'];
 const catalog=catalogFiles.map(f=>[f,digest(fs.readFileSync(path.join(root,f)))]);
 const codeFiles=[...files(path.join(root,'src')).filter(f=>/\.(?:mjs|ts|astro|css)$/.test(f)),...files(path.join(root,'scripts')).filter(f=>/\.(?:mjs|py)$/.test(f)),...files(path.join(root,'tests')).filter(f=>f.endsWith('.mjs')),path.join(root,'package.json'),path.join(root,'astro.config.mjs')].sort();
 const code=codeFiles.map(f=>[path.relative(root,f),digest(fs.readFileSync(f))]);
 const contentHash=digest(JSON.stringify(content)),catalogHash=digest(JSON.stringify(catalog)),codeHash=digest(JSON.stringify(code));
 const pageMapHash=digest(fs.readFileSync(path.join(root,'src/data/manual-page-map.json')));
 const assets=files(path.join(root,'public')).sort().map(f=>[path.relative(root,f),digest(fs.readFileSync(f))]);
 const assetHash=digest(JSON.stringify(assets));
 return {contentHash,catalogHash,codeHash,pageMapHash,assetHash,bundleHash:digest(JSON.stringify({contentHash,catalogHash,codeHash,pageMapHash,assetHash})),contentFiles:content,catalogFiles:catalog,codeFiles:code,assetFiles:assets};
}
export function validateManual(root,env=process.env) {
 const map=read(root,'src/data/manual-page-map.json');
 const provenance=read(root,'src/data/manual-provenance.json');
 assert.equal(map.schemaVersion,1);assert.equal(map.siteKey,'ansan-flower-test');assert(Array.isArray(map.pages));
 assert.equal(provenance.origin,'manual-user-request');assert.equal(provenance.usesFactoryQueue,false);assert.equal(provenance.writerId,WRITER_ID,'Unexpected manual writer identity');assert.equal(provenance.expectedReviewerId,EXPECTED_REVIEWER_ID,'Unexpected assigned reviewer identity');
 const hashes=manualDigests(root),mode=manualBuildMode(env);
 for(const key of ['contentHash','catalogHash','codeHash','pageMapHash','assetHash','bundleHash'])assert.equal(provenance[key],hashes[key],'Manual '+key+' drift');
 assert.equal(map.pages.length,hashes.contentFiles.length,'Manual file/route count mismatch');
 const frozen=read(root,'src/data/publish-manifest.json'),architecture=read(root,'src/data/architecture.json');
 const frozenKeys=new Set(frozen.pages.map(p=>p.pageKey)),frozenUrls=new Set([...frozen.pages,...architecture.pages].map(p=>p.url));
 const keys=new Set(),urls=new Set(),sources=new Set(),intents=new Set();
 const products=loadSiteProducts(root,map.siteKey);
 const legalFamilies=new Set(['funeral_wreath','congrats_wreath','flower_bouquet','flower_basket']);
 for(const row of map.pages){
  for(const key of ['snapshotId','snapshotHash','sourceDraftKey','sourceRecordId','publishQueueRecordId','approvalVerified','draftStatus'])assert.equal(row[key],undefined,'Manual record has fabricated frozen provenance: '+key);
  assert(/^m[a-f0-9]{24}$/.test(row.pageKey));assert.equal(row.manualPageId,row.pageKey);assert.equal(row.publicationMode,'manual-user-request');
  assert(!keys.has(row.pageKey)&&!frozenKeys.has(row.pageKey),'Duplicate/frozen manual page key');keys.add(row.pageKey);
  assert(!urls.has(row.url)&&!frozenUrls.has(row.url),'Duplicate/frozen manual URL');urls.add(row.url);
  assert(!sources.has(row.file),'Duplicate manual source');sources.add(row.file);
  assert.equal(row.file,`src/content/manual/${row.pageKey}.md`);assert.equal(row.routeType,'category');
  assert(['funeral','places','occasions','order-help','guide','flower-knowledge','regions'].includes(row.category),'Invalid manual category');
  assert.equal(row.category==='regions',row.pageType==='regional-service','Manual regional category/type mismatch');assert.equal(row.url,`/${row.category}/${row.slug}/`);assert.equal(row.parentHub,`/${row.category}/`);
  assert(row.primaryKeyword&&row.intentKey&&row.cluster&&row.queryEvidence&&Array.isArray(row.secondaryKeywords));assert(!intents.has(row.intentKey),'Duplicate manual intent');intents.add(row.intentKey);assert.equal(row.queryClass,'local-commercial');
  const text=fs.readFileSync(path.join(root,row.file),'utf8'),header=text.split('---')[1];assert(header,'Missing manual frontmatter');
  const front=Object.fromEntries(header.trim().split('\n').map(line=>{const i=line.indexOf(':');return [line.slice(0,i),JSON.parse(line.slice(i+1).trim())];}));
  for(const key of ['snapshotId','snapshotHash','sourceDraftKey','sourceRecordId','publishQueueRecordId','approvalVerified','draftStatus'])assert.equal(front[key],undefined,'Manual source has fabricated frozen provenance: '+key);
  for(const key of ['pageKey','manualPageId','publicationMode','slug','routeType','category','pageType','queryClass','title'])assert.equal(front[key],row[key],'Manual frontmatter drift '+key);
  for(const key of ['title','h1','description','cardSummary','firstAnswer'])assert(front[key]?.trim(),'Missing customer field '+key);
  assert(front.sources?.length&&front.sourceUrls?.length,'Missing manual source evidence');
  assert(Array.isArray(row.productKeys)&&row.productKeys.length,'Missing manual product selection');
  const selected=row.productKeys.map(k=>{const product=products.find(p=>p.productKey===k);assert(product&&legalFamilies.has(product.category),'Unknown manual product');return product;});
  assert.equal(new Set(row.productKeys).size,row.productKeys.length);
  if(row.category==='funeral')assert(selected.every(p=>p.category==='funeral_wreath'),'Funeral product intent mismatch');
  if(row.pageType==='opening-business')assert(selected.every(p=>p.category==='congrats_wreath'),'Opening product intent mismatch');
 }
 validateManualRegions(root,map.pages,products,read(root,'src/data/region-coverage.json'));
 const review=read(root,'src/data/manual-review.json');
 if(mode.production&&map.pages.length){
  assert.equal(review.status,'approved','Manual independent review pending');
  assert(review.reviewerId&&review.reviewerId!==provenance.writerId,'Writer cannot approve own manual content');
  assert.equal(review.reviewerId,provenance.expectedReviewerId,'Unrecognized independent reviewer');
  assert.equal(review.writerId,provenance.writerId);assert(review.reviewedAt&&review.evidenceFile&&review.evidenceSha256,'Missing independent review evidence');
  assert.equal(review.evidenceFile,'src/data/manual-review-evidence.json','Untrusted evidence location');
  const evidenceBytes=fs.readFileSync(path.join(root,review.evidenceFile));assert.equal(digest(evidenceBytes),review.evidenceSha256,'Review evidence bytes drift');
  const evidence=JSON.parse(evidenceBytes);assert.equal(evidence.status,'approved');assert.equal(evidence.kind,'independent-manual-content-review');assert.equal(evidence.reviewerId,review.reviewerId);assert.equal(evidence.writerId,provenance.writerId);assert(evidence.checkedCustomerFields===true&&evidence.checkedSources===true&&evidence.checkedRenderer===true,'Incomplete independent review');
  for(const key of ['contentHash','catalogHash','codeHash','pageMapHash','assetHash','bundleHash']){assert.equal(review[key],hashes[key],'Review digest drift '+key);assert.equal(evidence[key],hashes[key],'Evidence digest drift '+key);}
  assert.deepEqual([...evidence.pageIds].sort(),[...keys].sort(),'Review scope differs from manual page set');
 }
 return {pages:map.pages,hashes,provenance,review,...mode};
}
