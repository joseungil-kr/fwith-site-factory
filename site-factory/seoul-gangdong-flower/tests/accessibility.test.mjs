import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('skip link has a programmatically focusable main target',()=>{
 const layout=read('src/layouts/BaseLayout.astro');
 assert.match(layout,/<a class="skip-link" href="#main-content">/);
 assert.match(layout,/<main id="main-content" tabindex="-1">/);
});
test('desktop focus scroll has sticky-header clearance without changing mobile',()=>{
 const css=read('src/styles/global.css');
 assert.match(css,/@media\(min-width:861px\)\{html\{scroll-padding-block-start:83px\}\}/);
 assert.match(css,/scroll-padding-block-start:75px/);
});
