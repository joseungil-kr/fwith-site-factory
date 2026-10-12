import test from 'node:test';
import assert from 'node:assert/strict';
import {splitBannerContent,stripSharedFlowerBanners,originalOrderBannerPositions} from '../src/lib/shared-banner-content.mjs';
test('shared banners retain exact markup and split only after balanced top-level blocks',()=>{
 for(const html of ['<h2>Title</h2><p>First.</p><p>Last.</p>','<section><h2>Title</h2><ul><li>A<p>Inner.</p></li></ul></section><p>End.</p>','<p><a href="https://example.com/?a=>">Linked</a></p><p>End.</p>']) {
  const chunks=splitBannerContent(html);assert.equal(chunks.join(''),html);assert(chunks.every(Boolean));assert(!chunks[0].endsWith('</li>'));
 }
});
test('a single unsplittable block fails instead of stacking banners',()=>assert.throws(()=>splitBannerContent('<p>Only</p>'),/balanced/));

test('artwork captions do not change original body length or existing order CTA quotas',()=>{
 const body='<p>'+('x'.repeat(1199))+'</p>';
 const art='<figure class="shared-flower-banner" data-shared-flower-banner="message"><img alt="Flowers"/><figcaption>AI editorial artwork</figcaption></figure>';
 const order='<figure class="content-order-banner"><figcaption>Original order help</figcaption></figure>';
 assert.equal(stripSharedFlowerBanners(body+art).trim(),body);
 assert.equal(stripSharedFlowerBanners(order),order);
 for(const length of [1199,1200,2199,2200]){
  const plain='x'.repeat(length);assert.equal(stripSharedFlowerBanners(plain+art).trim().length,length);
 }
});

test('shared artwork never moves the original order CTA editorial boundary',()=>{
 const blocks=Array.from({length:9},(_,i)=>`<h2>Title ${i}</h2><p>${String(i).repeat(137+i*31)}</p>`);
 const body=blocks.join('');
 const banner='<figure data-shared-flower-banner="budget"><img alt="Flower"/><figcaption>AI artwork</figcaption></figure>';
 for(const fractions of [[.5],[.34,.68],[.26,.53,.8]]){
  const expected=originalOrderBannerPositions(body,fractions).map(pos=>body.slice(0,pos));
  for(const at of [0,blocks[0].length,blocks.slice(0,4).join('').length,body.length]){
   const decorated=body.slice(0,at)+banner+body.slice(at);
   const actual=originalOrderBannerPositions(decorated,fractions).map(pos=>decorated.slice(0,pos).replace(banner,''));
   assert.deepEqual(actual,expected);
  }
 }
});
test('original CTA positioning remains byte-for-byte equivalent without artwork',()=>{
 for(const body of ['<p>First</p><p>Last</p>','<h2>Empty</h2>','<p>A</p><ul><li><p>B</p></li></ul><blockquote>C</blockquote>']){
  const boundaries=[...body.matchAll(/<\/(?:p|ul|ol|blockquote)>/gi)].map(m=>m.index+m[0].length);
  const fractions=[.26,.53,.80];const expected=boundaries.length?fractions.map(f=>{const t=Math.floor(body.length*f);return boundaries.reduce((b,x)=>Math.abs(x-t)<Math.abs(b-t)?x:b,boundaries[0]);}):[];
  assert.deepEqual(originalOrderBannerPositions(body,fractions),expected);
 }
});
