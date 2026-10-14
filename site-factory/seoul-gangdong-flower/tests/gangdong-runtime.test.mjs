import {verifyReuse} from '../scripts/verify_reuse_provenance.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {generateRuntime,validateRuntime,assertBoundary,verifyInputs,ORIGIN} from '../src/lib/gangdong-runtime.mjs';
import {normalizeFaq} from '../src/components/faq.mjs';
import {inlineTokens,safeHref} from '../src/lib/content.mjs';
const root=new URL('../',import.meta.url),runtime=generateRuntime(root);
test('deterministic exact projection, original caller remains unchanged',()=>{assert.deepEqual(generateRuntime(root),runtime);assert.equal(validateRuntime(runtime,root),true);});
test('fixed Gangdong routes and geographic denominators',()=>{assert.equal(runtime.N,2);assert.equal(runtime.pages.length,5);assert.equal(runtime.geography.parsed.relationships.length,19);assert.equal(runtime.facilities.filter(f=>f.administrativeDong!==null).length,0);});
const cases={
 'public mode injected':r=>r.mode.mode='PUBLIC',
 'wrong district':r=>r.district='서울특별시 관악구',
 'wrong region code':r=>r.districtCode='11680',
 'extra route':r=>r.pages.push({...r.pages[1],path:'/regions/extra/'}),
 'wrong N':r=>r.N=3,
 'missing administrative unit':r=>r.geography.parsed.administrative.pop(),
 'wrong relationship':r=>r.geography.parsed.relationships[0].legalCode='0000000000',
 'facility assigned administrative unit':r=>r.facilities[0].administrativeDong='풍납1동',
 'unassigned legal dong invented':r=>r.facilities.find(f=>f.legalDong===null).legalDong='문정동',
 'query adapter missing':r=>delete r.pageContracts[1].runtime_query_class,
 'editorial class overwritten':r=>r.pageContracts[1].query_class='local-commercial',
 'wrong family':r=>r.products[0].family='wedding',
 'future public contract changed':r=>r.futurePublicContract.routes[0].productionRobots='noindex',
 'wrong SKU':r=>r.products[0].sku='B999',
 'wrong price':r=>r.products[0].basePriceKRW=49000,
 'wrong product CTA':r=>r.products[0].cta.href=r.products[1].cta.href,
 'wrong photo':r=>r.products[0].img=r.products[1].img,
 'changed first answer':r=>r.pages[0].firstAnswer+=' 보장합니다.',
 'missing FAQ answer':r=>r.pages[1].faqs[0].answer='',
 'changed FAQ answer':r=>r.pages[1].faqs[0].answer='삭제',
 'missing source link':r=>r.pages[1].officialSources.pop(),
 'invented source URL':r=>r.pages[1].officialSources[0].href='https://example.com/',
 'unapproved HTTP URL':r=>r.pages[1].officialSources[0].href='http://example.com/',
 'banner caption added':r=>r.common.banners[0].caption='caption',
 'directory banner added':r=>r.pages[3].bannerPlacement.push({banner:'message',after:'opening'}),
 'banner missing':r=>r.pages[0].bannerPlacement.pop(),
 'wrong banner phone':r=>r.common.phone.display='1234-5678',
 'ownership true':r=>r.ownershipVerified=true,
 'production approved':r=>r.productionApproved=true,
 'public approved':r=>r.publicApproved=true,
 'indexNow enabled':r=>r.indexNowEnabled=true,
 'indexable':r=>r.indexable=true,
 'public hostname':r=>r.origin='https://example.com',
 'nonempty sitemap':r=>r.sitemap.push('https://example.com/'),
 'robots indexing':r=>r.robots='index,follow'
};
for(const[name,mutate]of Object.entries(cases))test(`rejects ${name}`,()=>{const r=structuredClone(runtime);mutate(r);assert.throws(()=>validateRuntime(r,root));});
test('all indexability, public hostname and external flags reject before building',()=>{
 assert.doesNotThrow(()=>assertBoundary({SITE_INDEXABLE:'false',SITE_URL:ORIGIN}));
 for(const env of [{SITE_INDEXABLE:'true'},{SITE_INDEXABLE:'1'},{SITE_URL:'https://example.com'},...['PRODUCTION_APPROVED','OWNERSHIP_VERIFIED','INDEXNOW_ENABLED','PUBLIC_APPROVED'].map(k=>({[k]:'true'}))])assert.throws(()=>assertBoundary(env));
});
test('selected input byte tampering, resealing, added files and symlinks fail closed',()=>{
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'gangdong-input-'));
 try{fs.cpSync(new URL('src/data',root),path.join(temp,'src/data'),{recursive:true});fs.cpSync(new URL('public',root),path.join(temp,'public'),{recursive:true});
 const f=path.join(temp,'src/data/frozen/home-copy.json'),original=fs.readFileSync(f);fs.appendFileSync(f,' ');assert.throws(()=>verifyInputs(temp),/Frozen input differs/);fs.writeFileSync(f,original);
 fs.renameSync(f,f+'.real');fs.symlinkSync(f+'.real',f);assert.throws(()=>verifyInputs(temp),/Frozen input differs/);fs.unlinkSync(f);fs.renameSync(f+'.real',f);
 const extra=path.join(temp,'src/data/frozen/extra.json');fs.writeFileSync(extra,'{}');assert.throws(()=>verifyInputs(temp),/Unexpected frozen/);fs.unlinkSync(extra);
 fs.appendFileSync(path.join(temp,'src/data/input-manifest.json'),' ');assert.throws(()=>verifyInputs(temp),/manifest changed/);
 }finally{fs.rmSync(temp,{recursive:true,force:true});}
});
test('FAQ normalization keeps exact answers and rejects missing answers',()=>{assert.deepEqual(normalizeFaq(runtime.pages[1].faqs),runtime.pages[1].faqs);for(const x of [{},[{}],[{question:'q',answer:''}]])assert.throws(()=>normalizeFaq(x));});
test('reused safe inline parsing never admits active protocols',()=>{for(const v of ['javascript:alert(1)','//evil.example','data:text/html,hi'])assert.equal(safeHref(v),null);assert.equal(inlineTokens('<script>')[0].text,'<script>');});

test('unchanged and adapted reuse provenance matches actual source and rejects stale rows',()=>{
 assert.ok(verifyReuse(root).unchanged>0);
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'gangdong-provenance-'));
 try{
  const provenance=JSON.parse(fs.readFileSync(new URL('src/data/template-provenance.json',root),'utf8'));
  for(const row of [...provenance.reusedUnchanged,...provenance.adaptedFrom,{path:'src/data/template-provenance.json'},{path:'release/successor-provenance.json'}]){
   const dest=path.join(temp,row.path);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.copyFileSync(new URL(row.path,root),dest);
  }
  assert.doesNotThrow(()=>verifyReuse(temp));
  fs.appendFileSync(path.join(temp,provenance.reusedUnchanged[0].path),' ');
  assert.throws(()=>verifyReuse(temp),/Stale reuse provenance/);
 }finally{fs.rmSync(temp,{recursive:true,force:true});}
});
