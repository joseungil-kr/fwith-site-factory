import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {regionalMetadataFields,validateRegionalPurchase,isRegional} from './regions.mjs';
const allowed=new Map([
 ['m0ff66b0ce5a59abc73f06d93',{url:'/regions/sangnok-sa/',units:['안산시/상록구/법정동/사동']}],
 ['m3a2328ad676ccc2c2afc89b5',{url:'/regions/sangnok-banwol/',units:['안산시/상록구/법정동/건건동','안산시/상록구/법정동/사사동','안산시/상록구/법정동/팔곡일동']}],
]);
export function validateManualRegions(root,rows,products,coverage){
 const binding=JSON.parse(fs.readFileSync(path.join(root,'src/data/manual-regional-bindings.json'),'utf8'));
 assert.equal(binding.schemaVersion,1);assert.equal(binding.siteKey,coverage.siteKey);assert.equal(binding.publicationMode,'manual-user-request');assert.equal(binding.scopeKey,'ansan-manual-regional-20261007');
 const generic=products.find(p=>p.productKey==='congrats-basic');
 for(const id of ['ma3d7dfd189642fbadea1428a','m641df0d064a5948abe135570']){const row=rows.find(p=>p.pageKey===id);if(row){assert.deepEqual(row.productKeys,['bouquet-g108','basket-a155','congrats-basic']);assert.equal(generic?.sku,undefined,'Legacy product cannot impersonate a SKU');assert(!fs.readFileSync(path.join(root,row.file),'utf8').includes('C200'),'Unverified C200 identity');}}
 const regional=rows.filter(isRegional);assert.equal(regional.length,binding.bindings.length,'Manual region binding count');
 const ids=new Set(),units=new Set();
 for(const b of binding.bindings){
  assert(!ids.has(b.pageKey),'Duplicate manual regional binding');ids.add(b.pageKey);
  const expected=allowed.get(b.pageKey);assert(expected,'Unbound manual regional identity');assert.equal(b.url,expected.url);assert.deepEqual(b.regionUnitKeys,expected.units);
  const row=regional.find(p=>p.pageKey===b.pageKey);assert(row,'Missing manual regional row');
  for(const field of ['pageKey','url','category','pageType','routeType','publicationMode','manualPageId',...regionalMetadataFields])assert.deepEqual(row[field],b[field],'Manual region binding drift '+field);
  assert.equal(row.category,'regions');assert.equal(row.pageType,'regional-service');assert.equal(row.scopeKey,binding.scopeKey);assert.equal(row.parentHub,'/regions/');assert.equal(row.pageRole,'REGION_SERVICE_LANDING');
  assert.equal(row.publicationMode,'manual-user-request');assert.equal(row.manualPageId,row.pageKey);assert.deepEqual(row.productKeys,row.regionalProductKeys);
  assert(b.officialSourceUrls?.length);for(const u of b.officialSourceUrls){const url=new URL(u);assert.equal(url.protocol,'https:');assert.equal(url.hostname,'www.ansan.go.kr');assert(!url.username&&!url.password);}
  for(const unit of row.regionUnitKeys){assert(coverage.units.some(u=>u.unitKey===unit),'Unknown legal unit');assert(!units.has(unit),'Duplicate regional unit');units.add(unit);}
  const raw=fs.readFileSync(path.join(root,row.file),'utf8');const front=Object.fromEntries(raw.split('---')[1].trim().split('\n').map(line=>{let i=line.indexOf(':');return[line.slice(0,i),JSON.parse(line.slice(i+1))]}));
  for(const field of regionalMetadataFields)assert.deepEqual(front[field],row[field],'Manual region source drift '+field);
  for(const u of b.officialSourceUrls)assert(front.sourceUrls.includes(u),'Missing regional source');
  const product=products.find(p=>p.image===row.ogImage);assert(product?.sku&&product.sourceImageUrl===row.ogImageSourceUrl,'Unverified regional image');
  assert.equal(product.imageSha256,row.ogImageSha256);assert.equal(product.imageAlt,row.ogImageAlt);assert.equal(product.imageWidth,row.ogImageWidth);assert.equal(product.imageHeight,row.ogImageHeight);assert.equal(product.imageType,row.ogImageType);
  const file=path.resolve(root,'public',row.ogImage.replace(/^\//,''));assert(file.startsWith(path.resolve(root,'public')+path.sep));assert.equal(crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),row.ogImageSha256);
  validateRegionalPurchase(row,products,raw);
 }
 return regional;
}
export function manualDirectoryGroups(pages,coverage){
 const items=pages.filter(p=>p.publicationMode==='manual-user-request'&&isRegional(p));
 return coverage.districts.map(d=>({...d,items:items.filter(p=>p.regionUnitKeys.some(k=>coverage.units.find(u=>u.unitKey===k)?.districtKeys.includes(d.key))).map(page=>({page,aliases:coverage.administrativeCrosswalk.filter(a=>a.districtKey===d.key&&a.relations.some(r=>page.regionUnitKeys.includes(r.unitKey))).map(a=>({name:a.name,scope:a.relations.find(r=>page.regionUnitKeys.includes(r.unitKey)).scope}))}))})).filter(d=>d.items.length);
}

export function assertRegionalKeySet(pages,expected){
 const keys=pages.map(p=>p.pageKey),expectedKeys=expected.map(p=>p.pageKey);
 assert.equal(new Set(keys).size,keys.length,'Duplicate regional input pageKey');
 assert.deepEqual([...keys].sort(),[...expectedKeys].sort(),'Regional input pageKey set mismatch');
 for(const page of pages)if('url' in page)assert.equal(page.url,expected.find(p=>p.pageKey===page.pageKey)?.url,'Regional input URL mismatch');
}
