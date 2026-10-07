import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {regionalPages,policy} from '../src/lib/regional-runtime.mjs';
const root='site-factory/hwaseong-flower/';
const read=f=>JSON.parse(fs.readFileSync(f));
const baseline='2aa6703b81e25dbc3ec1a7def16799a02e4b34be';
const reviewed='3225fcf46b31d511a15ce865cddad690f2dd4480';
const prior='3ffc1443558ae6b375a472b2224c0c0125b5ebea';
const compare=(revision,file)=>assert.deepEqual(fs.readFileSync(file),execFileSync('git',['show',revision+':'+root+file]),file);
test('40 frozen bodies and frozen manifest remain byte-identical to public baseline',()=>{
 const pages=read('src/data/publish-manifest.json').pages;assert.equal(pages.length,40);
 compare(baseline,'src/data/publish-manifest.json');for(const p of pages)compare(baseline,p.file);
});
test('18 independently reviewed manual bodies and metadata remain byte-identical',()=>{
 const pages=read('src/data/manual-manifest.json').pages;assert.equal(pages.length,18);
 compare(reviewed,'src/data/manual-manifest.json');for(const p of pages)compare(reviewed,p.file);
});
test('all eight pre-existing regional-only files are preserved byte-for-byte',()=>{
 for(const file of ['scripts/qa_regions.mjs','src/components/RegionDirectory.astro','src/components/RegionalHub.astro','src/data/region-coverage.json','src/data/region-policy.json','src/lib/regional-runtime.mjs','src/lib/regions.mjs','tests/regional-contract.test.mjs'])compare(prior,file);
});
test('disabled regional implementation produces no routes, links, sitemap entry or extra HTML',()=>{
 assert.equal(policy.enabled,false);assert.deepEqual(regionalPages,[]);assert(!fs.existsSync('dist/regions'));
 const files=fs.readdirSync('dist',{recursive:true}).filter(p=>p.endsWith('.html'));assert.equal(files.length,66);
 for(const file of files)assert(!/href=["']\/regions\//.test(fs.readFileSync('dist/'+file,'utf8')),file);
 for(const name of ['sitemap-index.xml','sitemap-0.xml'])assert(!fs.readFileSync('dist/'+name,'utf8').includes('/regions/'));
});
