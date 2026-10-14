import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
import {pageSources} from '../src/lib/sources.mjs';
const read=p=>fs.readFileSync(new URL('../'+p,import.meta.url),'utf8');
const json=p=>JSON.parse(read(p));
const approved=json('src/data/gwanak-approved/inputs/copy/article-copy.rev4.json').articles;
const pages=json('src/data/pages.json');
const detail=read('src/pages/[category]/[slug].astro');

test('Gwanak retained first answer is escaped once while approved sections replace the legacy full-Markdown renderer',()=>{
 assert.equal((detail.match(/<p>\{page\.firstAnswer\}<\/p>/g)||[]).length,1);
 assert.match(detail,/copy\.sections\.map/);
 assert.match(detail,/section\.paragraphs\.map\(paragraph=><p>\{paragraph\}<\/p>\)/);
 assert.match(detail,/<h2 id=\{section.id\}>\{section.heading\}<\/h2>/);
 assert.doesNotMatch(detail,/<MarkdownContent|set:html|<style|contentMarkdown\s*[}=]/);
 for(const a of approved){
  assert.equal(pages.find(p=>p.id===a.id).firstAnswer,a.firstAnswer);
  assert.deepEqual(pages.find(p=>p.id===a.id).sections,a.sections);
 }
});
test('Gwanak source names/URLs use escaped expressions under a single H2 and one H3 per source',()=>{
 const source=detail.slice(detail.indexOf('<section class="source-references"'),detail.indexOf('\n<FaqSection'));
 assert.equal((source.match(/<h2 /g)||[]).length,1);
 assert.match(source,/<h2 id="source-references-title">\{common.sourceHeading\}<\/h2>/);
 assert.match(source,/<h3><a href=\{source.url\}[^>]*aria-label=\{source.name\}>\{source.name\}<\/a><\/h3>/);
 assert.match(source,/data-source-type=\{source.type\}/);
 assert.match(source,/data-source-verified-at=\{source.verifiedAt\}/);
 assert.doesNotMatch(source,/<time|<h2>\{source\.name\}|set:html|>\{source\.verifiedAt\}</);
 for(const [i,page] of pages.entries())assert.deepEqual(pageSources(page).map(({name,url})=>({name,url})),approved[i].sourceLinks);
});
test('Gwanak exact source URLs retain professor FAQ page2 and never collapse to a generic page',()=>{
 const exact='https://www.snufacultyclub.com/board/bbs47?page=2';
 assert.equal(approved[1].sourceLinks.filter(s=>s.url===exact).length,1);
 assert.equal(pageSources(pages[1]).filter(s=>s.url===exact).length,1);
 assert.equal(detail.includes('JSON.stringify(sources.map(({name,url})=>({name,url})))!==JSON.stringify(copy.sourceLinks)'),true);
});
test('Gwanak template rejects ambiguous article selection and binds products by SKU identity',()=>{
 assert.match(detail,/approvedCopy\.articles\.filter\(a=>a.slug===page.slug\)/);
 assert.match(detail,/matches.length!==1/);
 assert.match(detail,/productSet\.map\(p=>p.officialSku\)/);
 assert.match(detail,/section.id==='products'/);
 assert.doesNotMatch(detail,/sections\[0\].*ProductCards|contentMarkdown.*ProductCards/);
});
test('Gwanak cards render approved exact price label, description, photo notice and individual destination',()=>{
 const cards=read('src/components/ProductCards.astro');
 for(const expression of ['{p.priceLabel}','{p.desc}','{p.photoCaption}','href={p.orderUrl}','alt={p.imageAlt}','{p.ctaLabel}'])assert.ok(cards.includes(expression));
 assert.doesNotMatch(cards,/p\.priceLabel\s*\+|price\.toLocaleString|set:html|p\.orderUrl\s*\|\|/);
});
test('Gwanak compiled HTML is independently inspected against immutable source and actual asset bytes',()=>{
 assert.ok(fs.existsSync(new URL('../dist/index.html',import.meta.url)),'Run local build before surface acceptance');
 const result=spawnSync('python3',['-c','from pathlib import Path; import sys; sys.path.insert(0,"scripts"); from qa_gwanak import inspect; inspect(Path("."),write=False,quiet=True)'],{cwd:new URL('..',import.meta.url),encoding:'utf8'});
 assert.equal(result.status,0,result.stdout+result.stderr);
});
