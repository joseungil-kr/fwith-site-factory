import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const read=path=>fs.readFileSync(new URL('../'+path,import.meta.url),'utf8');
test('purchase banner consumes current Truth/config and never hardcodes a region, phone or price',()=>{
 const component=read('src/components/InlineOrderBanner.astro');
 for(const key of ['site.brand','site.region','site.phoneHref','site.orderUrl','site.phoneOrderHours'])assert.ok(component.includes(key));
 assert.doesNotMatch(component,/다른지역|예시지역|1844|59,?000|꽃이랑 온라인 주문/);
 assert.match(component,/가능한 전달 일정도 함께 상담/);assert.doesNotMatch(component,/배송.*보장|배송.*확정/);assert.ok(read('src/components/ProductCards.astro').includes('site.deliveryNotice'));assert.match(read('src/data/business-truth.json'),/추가 배송비/);
});
test('home, hub and detail render a component outside frozen raw Markdown',()=>{
 for(const page of ['src/pages/index.astro','src/pages/[category]/index.astro','src/pages/[category]/[slug].astro']){
   const source=read(page);assert.equal((source.match(/<InlineOrderBanner\/>/g)||[]).length,1);
 }
 const markdown=read('src/components/MarkdownContent.astro');assert.doesNotMatch(markdown,/set:html|InlineOrderBanner/);
});
test('OG uses verified product metadata separately from the visible hero and excludes 404',()=>{
 const layout=read('src/layouts/BaseLayout.astro');
 assert.ok(layout.includes('productSocialImage(socialProduct,provenance,site.domain,site.brand)'));
 assert.ok(layout.includes('property="og:image"'));
 assert.ok(read('src/pages/404.astro').includes('canonicalPath={false} includeSchema={false}'));
});
