import assert from 'node:assert/strict';
import test from 'node:test';
import router from './router.mjs';

const origins = ['https://seoul-dongjak.fwith.kr', 'https://seoul-geumcheon.fwith.kr'];
const prefixes = ['/__regional/dongjak', '/__regional/geumcheon'];

test('unknown hostname never reaches assets, including suffix and prototype names', async () => {
  for (const host of ['example.com', 'seoul-dongjak.fwith.kr.example.com', 'constructor', 'generic-skycar-shadow.workers.dev']) {
    const response = await router.fetch(new Request('https://' + host), {ASSETS: {fetch() {assert.fail('assets reached');}}});
    assert.equal(response.status, 404);
  }
});

test('same external paths use distinct asset paths, retain query/method/conditional headers and bytes', async () => {
  const cache = new Map();
  for (let repeat = 0; repeat < 2; repeat++) for (const [i, origin] of origins.entries()) {
    for (const path of ['/', '/robots.txt', '/sitemap-index.xml', '/images/a.webp', '/proof.txt']) {
      const response = await router.fetch(new Request(origin + path + '?v=1', {headers: {'If-None-Match': 'etag'}}), {
        ASSETS: {async fetch(req) {
          const url = new URL(req.url);
          assert.equal(url.pathname, prefixes[i] + path);
          assert.equal(url.search, '?v=1');
          assert.equal(req.headers.get('If-None-Match'), 'etag');
          if (!cache.has(url.pathname)) cache.set(url.pathname, new Uint8Array([0, i, 255]));
          return new Response(cache.get(url.pathname), {headers: {'X-Robots-Tag': 'noindex'}});
        }},
      });
      assert.deepEqual(new Uint8Array(await response.arrayBuffer()), new Uint8Array([0, i, 255]));
      assert.equal(response.headers.get('X-Robots-Tag'), 'noindex');
    }
  }
});

test('internal-looking and other-region paths remain inside requesting region', async () => {
  for (const [i, origin] of origins.entries()) {
    for (const path of ['/__regional/geumcheon/index.html', '/__regional/dongjak/index.html', '/regions/other-region/']) {
      const response = await router.fetch(new Request(origin + path), {ASSETS: {async fetch(req) {
        assert.equal(new URL(req.url).pathname, prefixes[i] + path);
        return new Response('region-' + i + '-404', {status: 404});
      }}});
      assert.equal(response.status, 404);
      assert.equal(await response.text(), 'region-' + i + '-404');
    }
  }
});

test('encoded namespace traversal/separators never reach assets', async () => {
  for (const path of ['/%2f__regional/geumcheon/', '/%5c..%5c', '/%252e%252e/']) {
    assert.equal((await router.fetch(new Request(origins[0] + path), {ASSETS: {fetch() {assert.fail();}}})).status, 400);
  }
});

test('slash redirects remove internal prefix and preserve origin/query/status', async () => {
  for (const [i, origin] of origins.entries()) {
    const response = await router.fetch(new Request(origin + '/regions?q=1'), {ASSETS: {async fetch() {
      return new Response(null, {status: 307, headers: {Location: prefixes[i] + '/regions/?q=1'}});
    }}});
    assert.equal(response.status, 307);
    assert.equal(response.headers.get('Location'), '/regions/?q=1');
  }
});

test('foreign or cross-region asset redirects fail closed', async () => {
  for (const location of ['https://example.com/', '/__regional/geumcheon/', '/__regional/dongjak-other/']) {
    assert.equal((await router.fetch(new Request(origins[0]), {ASSETS: {async fetch() {
      return new Response(null, {status: 301, headers: {Location: location}});
    }}})).status, 502);
  }
});

test('HEAD and asset conditional responses are preserved', async () => {
  const response = await router.fetch(new Request(origins[0] + '/image.webp', {method: 'HEAD'}), {ASSETS: {async fetch(req) {
    assert.equal(req.method, 'HEAD');
    return new Response(null, {status: 304, headers: {ETag: 'same'}});
  }}});
  assert.equal(response.status, 304);
  assert.equal(response.headers.get('ETag'), 'same');
  assert.equal(await response.text(), '');
});

test('404.html canonical redirect preserves 307, relative location, query and empty body', async () => {
  for (const [i, origin] of origins.entries()) {
    const response = await router.fetch(new Request(origin + '/404.html?audit=1'), {ASSETS: {async fetch(req) {
      assert.equal(new URL(req.url).pathname, prefixes[i] + '/404.html');
      return new Response(null, {status: 307, headers: {Location: prefixes[i] + '/404?audit=1'}});
    }}});
    assert.equal(response.status, 307);
    assert.equal(response.headers.get('Location'), '/404?audit=1');
    assert.equal(await response.text(), '');
  }
});

test('robots policy bytes are opaque; router neither strips nor adds managed directives', async () => {
  // Synthetic policy fixture, not a claimed copy of current public robots.txt.
  const body = '# Managed test fixture\nUser-agent: ExampleTrainingBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n';
  for (const origin of origins) {
    const response = await router.fetch(new Request(origin + '/robots.txt'), {ASSETS: {async fetch() {
      return new Response(body, {headers: {'Content-Type': 'text/plain', 'ETag': 'policy-version'}});
    }}});
    assert.equal(await response.text(), body);
    assert.equal(response.headers.get('ETag'), 'policy-version');
  }
});
