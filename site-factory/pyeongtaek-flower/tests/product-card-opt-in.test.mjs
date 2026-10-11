import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts,productFamilies,homeProducts} from '../src/lib/catalog.mjs';
import {resolveProductCardLimit} from '../src/lib/product-card-limit.mjs';
const text=p=>fs.readFileSync(new URL(p,import.meta.url),'utf8');
const read=p=>JSON.parse(text(p));
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const clone=x=>structuredClone(x);
const baseline=read('./fixtures/original-pages-before-copy.json');
const reviewed=read('./fixtures/reviewed-copy.json');
const pages=read('../src/data/pages.json');
const products=read('../src/data/products.json');
const j=pages.find(p=>p.slug==='jinwi-myeon');
const previous=p=>p.productCardLimit===4||productFamilies(p).length>3?4:3;
const chosen=p=>selectProducts(p,products,resolveProductCardLimit(p,products));

test('portable original and reviewed-copy fixtures have exact independently reviewed SHA pins',()=>{
 assert.equal(sha(text('./fixtures/original-pages-before-copy.json')),'06fda605f3d88a6f60414ebd3c7204233f73849083acd0fdc83b8ab267c1c29d');
 assert.equal(sha(text('./fixtures/reviewed-copy.json')),'090548dcb1d65ad72d19e1eab590f363ef5256bbdfc098203c1576740834a6b1');
 assert.equal(baseline.length,36);assert.equal(reviewed.length,36);
});
for(const p of pages)test(`persisted selector ${p.slug}: exactly ${p.productCardLimit} bound real cards`,()=>{
 const selected=chosen(p);assert.equal(selected.length,p.productCardLimit);assert.deepEqual(selected.map(x=>x.key),p.productCardKeys);
 assert.equal(new Set(selected.map(x=>x.key)).size,selected.length);
 for(const row of selected){assert.equal(row,products.find(x=>x.key===row.key));assert(p.regionalProductFamilies.includes(row.family));}
});
test('ordinary resolver retains pre-opt-in behavior for all36 original source pages',()=>{
 for(const p of baseline){assert.equal(resolveProductCardLimit(p,products),previous(p));assert.deepEqual(selectProducts(p,products,resolveProductCardLimit(p,products)),selectProducts(p,products,previous(p)));}
});
test('ordinary nonregional selection and home retain their original behavior',()=>{
 const examples=[{pageType:'business-opening'},{pageType:'funeral-facility'},{pageType:'event-venue',visualIntent:'event_wreath'},{pageType:'event-venue',visualIntent:'performance_venue'},{pageType:'hospital-visit'},{pageType:'price-guide',primaryKeyword:'화환'},{pageType:'unknown'}];
 for(const p of examples)for(const limit of [undefined,3,4,5,null]){const x={...p,productCardLimit:limit};assert.equal(resolveProductCardLimit(x,products),previous(x));}
 assert.equal(homeProducts(products).length,8);assert.equal(selectProducts({pageType:'event-venue',visualIntent:'event_wreath'},products).length,3);
});
test('only Jinwi has8 cards and all35 other current pages have4',()=>{
 assert.equal(pages.filter(p=>p.productCardLimit===8).length,1);assert.equal(pages.filter(p=>p.productCardLimit===4).length,35);
 assert.equal(j.pageKey,'pyeongtaek-flower-v2-region-jinwi-myeon');assert.equal(chosen(j).length,8);
});
for(const [field,value] of Object.entries({pageKey:'other',slug:'other',url:'/regions/other/',category:'event',pageType:'event-venue',regionalPurchaseMode:'consultation-only'})){
 test(`negative8: changed ${field} rejected`,()=>{const p=clone(j);p[field]=value;assert.throws(()=>resolveProductCardLimit(p,products),/restricted/);});
}
for(const [name,mutate] of [
 ['string8',p=>p.productCardLimit='8'],
 ['missing productCardKeys',p=>delete p.productCardKeys],
 ['missing card',p=>p.productCardKeys.pop()],
 ['duplicate card',p=>p.productCardKeys[7]=p.productCardKeys[0]],
 ['unknown SKU',p=>p.productCardKeys[7]='unregistered-sku'],
 ['reordered card keys',p=>p.productCardKeys.reverse()],
 ['wrong family',p=>p.regionalProductFamilies=['congrats']],
 ['reordered families',p=>p.regionalProductFamilies.reverse()],
 ['missing regional key',p=>p.regionalProductKeys.pop()],
 ['duplicate regional key',p=>p.regionalProductKeys[7]=p.regionalProductKeys[0]],
 ['wrong regional key order',p=>p.regionalProductKeys.reverse()],
 ['null key array',p=>p.productCardKeys=null],
 ])test(`negative8: ${name} rejected`,()=>{const p=clone(j);mutate(p);assert.throws(()=>resolveProductCardLimit(p,products));});
test('negative8: another regional page cannot opt in8',()=>{const p=clone(pages[0]);p.productCardLimit=8;p.productCardKeys=j.productCardKeys;assert.throws(()=>resolveProductCardLimit(p,products),/restricted/);});
test('negative8: missing registry SKU rejected',()=>assert.throws(()=>resolveProductCardLimit(j,products.filter(p=>p.key!=='funeral-xl')),/catalog binding/));
test('negative8: duplicate registry SKU rejected',()=>assert.throws(()=>resolveProductCardLimit(j,[...products,clone(products[0])]),/catalog binding/));
test('negative8: registry family mismatch rejected',()=>{const r=clone(products);r.find(p=>p.key==='funeral-xl').family='congrats';assert.throws(()=>resolveProductCardLimit(j,r),/catalog binding/);});
test('negative8: no registry rejected',()=>assert.throws(()=>resolveProductCardLimit(j,null),/real catalog/));
test('removing opt-in reproduces3, never falsely satisfies8',()=>{const p=clone(j);delete p.productCardLimit;assert.equal(chosen(p).length,3);assert.notEqual(chosen(p).length,p.productCardKeys.length);});
