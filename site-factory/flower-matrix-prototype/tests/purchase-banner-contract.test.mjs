import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const read=path=>fs.readFileSync(new URL('../'+path,import.meta.url),'utf8');

test('matrix customer routes use shared instance phone and order settings without hardcoded clone domains',()=>{
 for(const page of ['src/pages/index.astro','src/pages/[region]/index.astro','src/pages/products/[product].astro','src/pages/[region]/[product].astro']){
   const source=read(page);
   assert.ok(source.includes('active.phone')||source.includes('active.phoneHref'));
   assert.ok(source.includes('active.orderUrl'));
   assert.doesNotMatch(source,/flower-a\.fwith\.kr|flower-b\.fwith\.kr|prototype-a\.example\.invalid|prototype-b\.example\.invalid/);
 }
});

test('home region product and detail routes all render visible conversion paths',()=>{
 for(const page of ['src/pages/index.astro','src/pages/[region]/index.astro','src/pages/products/[product].astro','src/pages/[region]/[product].astro']){
   const source=read(page);
   assert.equal((source.match(/class="conversion-panel"/g)||[]).length,1,page);
   assert.ok(source.includes('전화주문'),page);
   assert.ok(source.includes('온라인 주문'),page);
 }
});

test('matrix OG image is supplied from explicit verified product data and 404 stays canonical-free',()=>{
 const layout=read('src/layouts/BaseLayout.astro');
 assert.ok(layout.includes('socialImageUrl=null'));
 assert.ok(layout.includes('resolvedSocialImage'));
 assert.ok(layout.includes('property="og:image"'));
 assert.ok(layout.includes("urlparse")===false);
 for(const page of ['src/pages/index.astro','src/pages/[region]/index.astro','src/pages/products/[product].astro','src/pages/[region]/[product].astro']){
   const source=read(page);assert.ok(source.includes('socialImageUrl='),page);assert.ok(source.includes('socialImageAlt='),page);
 }
 const notFound=read('src/pages/404.astro');
 assert.ok(notFound.includes('canonicalPath={false} includeSchema={false}'));
 assert.doesNotMatch(notFound,/socialImageUrl/);
});
