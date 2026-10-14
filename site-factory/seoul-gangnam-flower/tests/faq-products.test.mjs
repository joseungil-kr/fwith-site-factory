import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {normalizeFaq} from '../src/components/faq.mjs';
const read=file=>readFileSync(new URL(`../${file}`,import.meta.url),'utf8');
test('FAQ normalizes object and legacy tuple entries in original order',()=>{
 const original=[{question:'질문 하나',answer:'답변 하나'},['질문 둘','답변 둘']];
 assert.deepEqual(normalizeFaq(original),[{question:'질문 하나',answer:'답변 하나'},{question:'질문 둘',answer:'답변 둘'}]);
 assert.deepEqual(original[1],['질문 둘','답변 둘']);
 assert.deepEqual(normalizeFaq(null),[]);assert.deepEqual(normalizeFaq(undefined),[]);assert.deepEqual(normalizeFaq([]),[]);
});
test('FAQ rejects malformed entries rather than rendering blank answers',()=>{
 for(const value of [{},'FAQ',[null],[['q']],[{question:'q'}],[{question:' ',answer:'a'}],[{question:'q',answer:0}]])assert.throws(()=>normalizeFaq(value),TypeError);
});
test('detail FAQ renders independently of Markdown and is never collapsed',()=>{
 const page=read('src/pages/[category]/[slug].astro'),component=read('src/components/FaqSection.astro');
 assert.match(page,/<FaqSection items=\{page\.faq\}/);assert.doesNotMatch(page,/!page\.contentMarkdown\s*&&\s*page\.faq/);
 assert.match(component,/normalizeFaq\(items\)/);assert.match(component,/data-visible-faq/);assert.match(component,/data-faq-question/);assert.match(component,/data-faq-answer/);
 assert.doesNotMatch(component,/<details|<summary|\bhidden\b|display\s*:\s*none|set:html/);
});
test('product cards keep individual order URL without a homepage fallback',()=>{
 const cards=read('src/components/ProductCards.astro');
 assert.match(cards,/href=\{p\.orderUrl\} data-order-product-key=\{p\.key\}/);
 assert.doesNotMatch(cards,/href=\{p\.orderUrl\s*\|\|/);
});
test('source cards use H3 beneath one source-section H2',()=>{
 const detail=read('src/pages/[category]/[slug].astro');
 assert.match(detail,/<h2 id="source-references-title">/);assert.match(detail,/<h3><a href=\{source.url\}[^>]*>\{approvedSourceNames.get\(source.url\)\}<\/a><\/h3>/);assert.doesNotMatch(detail,/<h2>\{source\.name\}/);
});
