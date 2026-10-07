import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {assertRegionalInput,regionalPages,policy} from '../src/lib/regional-runtime.mjs';
import allPages,{manualPages,frozenPages} from '../src/lib/all-pages.mjs';
import {selectProducts} from '../src/lib/catalog.mjs';
const products=JSON.parse(fs.readFileSync(new URL('../src/data/products.json',import.meta.url)));
test('disabled regional registry coexists with four separately authored district guides',()=>{
 assert.equal(policy.enabled,false);assert.equal(regionalPages.length,0);
 assert.equal(frozenPages.length,30);assert.equal(manualPages.length,16);assert.equal(manualPages.filter(p=>p.category==='regions').length,4);
 assert.deepEqual(assertRegionalInput(allPages),[]);
});
test('manual flag alone cannot bypass frozen regional provenance',()=>{
 const guide=manualPages.find(p=>p.category==='regions');
 assert.throws(()=>assertRegionalInput([{...guide,url:'/regions/forged/'}]),/mismatch/);
 assert.throws(()=>assertRegionalInput([{...guide,publicationMode:'registry'}]),/mismatch/);
});
test('regional product bindings fail closed and retain ordered official catalog rows',()=>{
 for(const guide of manualPages.filter(p=>p.category==='regions'))assert.deepEqual(selectProducts(guide,products,4).map(p=>p.key),guide.regionalProductKeys.slice(0,4));
 assert.throws(()=>selectProducts({pageType:'regional-service'},products),/binding/);
 assert.throws(()=>selectProducts({pageType:'regional-service',regionalProductKeys:['missing']},products),/registered/);
});

test('manual district guides retain explicit mobile-visible home purpose and detail entries',()=>{
 const html=fs.readFileSync('dist/index.html','utf8');
 assert.match(html,/<a[^>]*class="page-card purpose-card"[^>]*href="\/regions\/"/);
 for(const page of manualPages.filter(p=>p.category==='regions'))assert(html.includes('href="'+page.url+'"'));
});
