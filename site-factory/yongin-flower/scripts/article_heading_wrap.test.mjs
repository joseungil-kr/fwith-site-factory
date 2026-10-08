import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync, readdirSync } from 'node:fs';

const css = readFileSync(new URL('../src/styles/article.css', import.meta.url), 'utf8');
const dist = new URL('../dist/', import.meta.url);
test('article heading emergency wrapping is limited to narrow screens', () => {
  assert.match(css, /@media\s*\(max-width:\s*620px\)\s*\{\s*\.article-header h1\s*\{\s*overflow-wrap:\s*anywhere;\s*\}\s*\}\s*$/);
  assert.match(css, /font-size: clamp\(34px, 6vw, 60px\)/);
  assert.doesNotMatch(css, /word-break:\s*break-all/);
});
test('native build preserves full heading text and emits the emergency wrap rule', () => {
  const html = readFileSync(new URL('funeral/yongin-seoul-hospital-funeral-wreath/index.html', dist), 'utf8');
  assert.match(html, /<h1[^>]*>용인서울병원장례문화센터 근조화환, 전화·빈소·교통 확인사항<\/h1>/);
  const built = readdirSync(new URL('_astro/', dist)).filter(x => x.endsWith('.css')).map(x => readFileSync(new URL('_astro/' + x, dist), 'utf8')).join('\n');
  assert.match(built, /\.article-header h1\{overflow-wrap:anywhere\}/);
});
