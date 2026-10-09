import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {selectProducts} from '../src/lib/catalog.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const slugs=['anyang-dong','seoksu-dong','bakdal-dong','bisan-dong','gwanyang-dong','pyeongchon-dong','hogye-dong'];
test('Anyang has seven distinct legal-unit pages and all 31 current administrative names',()=>{
 const pages=read('pages'),coverage=read('region-coverage');
 assert.deepEqual(pages.filter(p=>p.pageType==='regional-service').map(p=>p.slug),slugs);assert.equal(coverage.units.length,7);assert.equal(coverage.administrativeCrosswalk.length,31);
 assert.equal(new Set(coverage.administrativeCrosswalk.map(a=>a.aliasKey)).size,31);
 for(const name of ['명학동','병목안동','호현동','충훈동','인덕원동'])assert.ok(coverage.administrativeCrosswalk.some(a=>a.name===name));
 assert.equal(coverage.districts.length,2);
 assert.equal(coverage.representatives.length,7);
});
test('direct snapshot hashes bind the public content and all four page collections',()=>{
 const pages=read('pages'),manifest=read('publish-manifest');
 assert.equal(manifest.directRelease.sourceMode,'direct-git');assert.deepEqual(manifest.snapshotLedger,{});
 for(const p of pages){
  const omit=new Set(['approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash']);
  const digest=sha(canonical(Object.fromEntries(Object.entries(p).filter(([k])=>!omit.has(k)))));
  assert.equal(p.snapshotHash,digest);assert.equal(p.snapshotId,`direct-content-${p.slug}-${digest.slice(0,16)}`);
  const row=manifest.directRelease.contentHashes.find(x=>x.pageKey===p.pageKey);
  assert.equal(row.publicSourceSha256,digest);assert.equal(row.bodySha256,sha(p.contentMarkdown));
  for(const c of [manifest,read('page-map'),read('architecture')])assert.equal(c.pages.find(x=>x.pageKey===p.pageKey).snapshotHash,digest);
 }
});
test('Anyang source contains no copied regional data or old external workflow IDs',()=>{
 for(const name of ['pages','page-map','architecture','publish-manifest','region-coverage','region-policy','site-config']){
  const text=JSON.stringify(read(name));assert.doesNotMatch(text,/평택|pyeongtaek|rec[A-Za-z0-9]{14}|app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|queueRecordId|sourceIssueNumber/);
 }
});
test('public ownership proof is unique and distinct from previous city',()=>{
 const root=new URL('../public/',import.meta.url);
 const matches=fs.readdirSync(root).filter(n=>/^[0-9a-f]{32}\.txt$/.test(n));assert.equal(matches.length,1);
 assert.equal(fs.readFileSync(new URL(matches[0],root),'utf8').trim(),matches[0].slice(0,-4));
 assert.notEqual(matches[0],'708ecb57c729d9c61d08c73f117b9e03.txt');
});

test('the five approved additions preserve regional scope and index only supported hubs',()=>{
 const pages=read('pages'),manifest=read('publish-manifest'),architecture=read('architecture');
 const added=[['funeral','anyang-funeral-hall-wreath'],['funeral','sam-hospital-funeral-wreath'],['funeral','hallym-hospital-funeral-wreath'],['event','patiobella-wedding-wreath'],['event','partyum-anyang-wedding-wreath']];
 assert.equal(pages.length,12);assert.equal(manifest.directRelease.appendedCount,5);
 assert.deepEqual(pages.filter(p=>p.pageType!=='regional-service').map(p=>[p.category,p.slug]).sort(),added.sort());
 for(const [category,slug] of added){
  const p=pages.find(p=>p.slug===slug);assert.equal(p.url,`/${category}/${slug}/`);assert.equal(p.assetSlot,'REAL_PROOF');
  assert.equal(p.productCardLimit,4);assert.equal(p.productCardKeys.length,4);
  assert.deepEqual(selectProducts(p,read('products'),p.productCardLimit).map(x=>x.key),p.productCardKeys);
  assert.ok(selectProducts(p,read('products'),p.productCardLimit).every(x=>x.family===(category==='funeral'?'funeral':'congrats')));
  assert.ok(pages.some(q=>q.pageType==='regional-service'&&q.relatedKeys.includes(p.pageKey)),`Missing local inbound link for ${slug}`);
  assert.ok(p.sources.length>0);
 }
 const indexableHubs=architecture.hubs.filter(h=>h.indexable).map(h=>h.url).sort();
 assert.deepEqual(indexableHubs,['/funeral/','/regions/']);
 const htmlHubs=architecture.hubs.filter(h=>h.children>0).map(h=>h.url).sort();
 assert.deepEqual(htmlHubs,['/event/','/funeral/','/regions/']);
 assert.equal(1+pages.length+indexableHubs.length,15);assert.equal(1+pages.length+htmlHubs.length,16);
});

test('existing seven article URLs and bodies stay unchanged',()=>{
 const originals={"anyang-dong":{"url":"/regions/anyang-dong/","bodySha256":"eb10ecfaa5b39b2bed132f5119db8288b5045c1857e1d3cb8cb791e97dce553a"},"seoksu-dong":{"url":"/regions/seoksu-dong/","bodySha256":"d8deca014ee3023b7f386657514f0b59a5262289e3750112e5a82ce1a273a450"},"bakdal-dong":{"url":"/regions/bakdal-dong/","bodySha256":"a3dcd68886238bff48ec7b67dfc121c8c3f45407105c5175e4dc5b74ade2c890"},"bisan-dong":{"url":"/regions/bisan-dong/","bodySha256":"2f56b65c075f5cf32e8eadd4607f4326e82618527fb6ecd95b3304d32da691b1"},"gwanyang-dong":{"url":"/regions/gwanyang-dong/","bodySha256":"8ce15bfbaafda1d1866f838d5823ec3f997af7b427f6ed6989f5f88ff6593176"},"pyeongchon-dong":{"url":"/regions/pyeongchon-dong/","bodySha256":"ec824b858bf748e399094b153824e1804f9b2f1d20579ffa8428c954a39d3eb1"},"hogye-dong":{"url":"/regions/hogye-dong/","bodySha256":"2ba2029b4c2392696dcac84a38d582fa5eb10cde7559ea9c2cef710dbd27e4cf"}};
 const pages=read('pages');
 for(const [slug,expected] of Object.entries(originals)){
  const page=pages.find(p=>p.slug===slug);assert.ok(page);assert.equal(page.url,expected.url);assert.equal(sha(page.contentMarkdown),expected.bodySha256);
 }
});
