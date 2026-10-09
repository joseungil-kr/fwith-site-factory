import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`,import.meta.url),'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const slugs=['anyang-dong','seoksu-dong','bakdal-dong','bisan-dong','gwanyang-dong','pyeongchon-dong','hogye-dong'];
test('Anyang has seven distinct legal-unit pages and all 31 current administrative names',()=>{
 const pages=read('pages'),coverage=read('region-coverage');
 assert.deepEqual(pages.map(p=>p.slug),slugs);assert.equal(coverage.units.length,7);assert.equal(coverage.administrativeCrosswalk.length,31);
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
