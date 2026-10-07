import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';
import {validateManualRegions,manualDirectoryGroups,assertRegionalKeySet} from '../src/lib/manual-regions.mjs';
import {loadSiteProducts} from '../src/lib/site-catalog.mjs';
const root=path.resolve(import.meta.dirname,'..');
const read=(r,f)=>JSON.parse(fs.readFileSync(path.join(r,f),'utf8'));
const rows=read(root,'src/data/manual-page-map.json').pages,coverage=read(root,'src/data/region-coverage.json');
function fixture(fn){const r=fs.mkdtempSync(path.join(os.tmpdir(),'ansan-regions-'));try{for(const d of ['src','public'])fs.cpSync(path.join(root,d),path.join(r,d),{recursive:true});return fn(r,structuredClone(rows));}finally{fs.rmSync(r,{recursive:true,force:true});}}
const run=(r,rows)=>validateManualRegions(r,rows,loadSiteProducts(r,'ansan-flower-test'),coverage);
test('two explicit manual regional bindings validate while frozen scope remains disabled',()=>{assert.equal(run(root,rows).length,2);assert.equal(read(root,'src/data/region-policy.json').enabled,false);});
for(const [field,value] of [['url','/regions/anything/'],['pageKey','m000000000000000000000000'],['regionUnitKeys',['안산시/상록구/법정동/이동']],['regionalProductKeys',['funeral-basic']],['ogImage','/images/products/funeral-basic.webp'],['ogImageSourceUrl','https://example.com/image.jpg'],['scopeKey','other']])test('binding drift rejects '+field,()=>fixture((r,p)=>{p.find(x=>x.category==='regions')[field]=value;assert.throws(()=>run(r,p));}));
test('invented regional category cannot gain route coverage',()=>fixture((r,p)=>{p[0].category='regions';p[0].pageType='regional-service';assert.throws(()=>run(r,p));}));
test('changed official source binding is rejected',()=>fixture((r,p)=>{const file='src/data/manual-regional-bindings.json',d=read(r,file);d.bindings[0].officialSourceUrls=['https://example.com/'];fs.writeFileSync(path.join(r,file),JSON.stringify(d));assert.throws(()=>run(r,p));}));
test('C200 label is rejected for preserved generic product',()=>fixture((r,p)=>{fs.appendFileSync(path.join(r,p.find(x=>x.slug.startsWith('daebu')).file),'C200');assert.throws(()=>run(r,p),/C200/);}));
for(const [field,value] of [['price',1],['sku','G999'],['sourceUrl','https://example.com'],['imageSha256','0'.repeat(64)]])test('catalog price SKU source image evidence drift rejected '+field,()=>fixture((r,p)=>{const file='src/data/site-catalog.json',d=read(r,file);d.products[0][field]=value;fs.writeFileSync(path.join(r,file),JSON.stringify(d));assert.throws(()=>run(r,p));}));
test('corrupt actual catalog image bytes rejected',()=>fixture((r,p)=>{fs.appendFileSync(path.join(r,'public/images/products/bouquet-g108.jpg'),'x');assert.throws(()=>run(r,p));}));
test('regional alias grouping is exact and duplicate-free',()=>{const groups=manualDirectoryGroups(rows,coverage);assert.equal(groups.length,1);assert.equal(groups[0].key,'sangnok');assert.equal(groups[0].items.length,2);const sa=groups[0].items.find(x=>x.page.slug==='sangnok-sa');assert.deepEqual(sa.aliases.map(x=>x.name),['사동','사이동','해양동']);const b=groups[0].items.find(x=>x.page.slug==='sangnok-banwol');assert.deepEqual(b.aliases.map(x=>x.name),['반월동']);});

const regional=rows.filter(p=>p.category==='regions');
test('regional input rejects duplicate page keys and a missing expected page',()=>{assert.throws(()=>assertRegionalKeySet([regional[0],regional[0]],regional),/Duplicate/);assert.throws(()=>assertRegionalKeySet([regional[0]],regional),/set mismatch/);});
test('regional input rejects URL drift and accepts exact source-frontmatter identity set',()=>{assert.throws(()=>assertRegionalKeySet([{...regional[0],url:'/regions/wrong/'},regional[1]],regional),/URL mismatch/);assertRegionalKeySet(regional.map(({url,...p})=>p),regional);});
