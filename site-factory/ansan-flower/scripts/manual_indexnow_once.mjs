import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const PRODUCTION_SHA = 'aeb04a9ed1f9f36692fd3e679e6e71c5c065224d';
const HELPER_SHA256 = 'bd31f6c934c8f34b6b37e3d00c01d2753e3b90f15123063b632409b186df9954';
const MAP_SHA256 = '8b4a1176aae289032d546e60aec88caf64242c87baa152304792e4d6d9013f1b';
const ORIGIN = 'https://ansan.fwith.kr';
const ENDPOINT = 'https://searchadvisor.naver.com/indexnow';
const REPO = 'joseungil-kr/fwith-site-factory';
const BRANCH = 'manual-ansan-indexnow-20261007';
const hash = value => createHash('sha256').update(value).digest('hex');
const requireThat = (condition, message) => { if (!condition) throw new Error(message); };
const git = (...args) => execFileSync('git', args, { encoding: 'utf8' }).trim();
const save = (name, value) => writeFileSync(name, JSON.stringify(value, null, 2) + '\n');

function attrs(tag) {
  return Object.fromEntries([...tag.matchAll(/([\w-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g)]
    .map(match => [match[1].toLowerCase(), match[2] ?? match[3]]));
}

export function verifyHtml(html, url, header = '') {
  const metas = [...html.matchAll(/<meta\b[^>]*>/gi)].map(match => attrs(match[0]));
  const revisions = metas.filter(meta => meta.name === 'site-factory-revision');
  requireThat(revisions.length === 1 && revisions[0].content === PRODUCTION_SHA, 'Production revision mismatch');
  const robots = metas.filter(meta => /^(robots|googlebot|bingbot)$/i.test(meta.name ?? ''));
  const generic = robots.filter(meta => meta.name.toLowerCase() === 'robots');
  const tokens = generic.flatMap(meta => (meta.content ?? '').toLowerCase().split(/[\s,]+/));
  requireThat(generic.length === 1 && tokens.includes('index') && tokens.includes('follow'), 'Explicit index,follow missing');
  requireThat(!robots.some(meta => /\b(noindex|nofollow|none)\b/i.test(meta.content ?? '')), 'Restrictive robots meta');
  requireThat(!/\b(noindex|nofollow|none)\b/i.test(header), 'Restrictive X-Robots-Tag');
  const canonicals = [...html.matchAll(/<link\b[^>]*>/gi)].map(match => attrs(match[0]))
    .filter(link => link.rel?.toLowerCase().split(/\s+/).includes('canonical'));
  requireThat(canonicals.length === 1 && canonicals[0].href === url, 'Canonical mismatch');
}

export function selectUrls(map) {
  requireThat(map.siteKey === 'ansan-flower-test' && map.pages?.length === 20, 'Expected exactly 20 Ansan manual pages');
  const urls = map.pages.map(page => {
    requireThat(page.publicationMode === 'manual-user-request' && page.sitemapIndexable === true, 'Unexpected page mode');
    requireThat(/^\/(funeral|places|occasions)\/[a-z0-9-]+\/$/.test(page.url), 'Unexpected manual route');
    return ORIGIN + page.url;
  });
  requireThat(new Set(urls).size === 20, 'Duplicate manual URLs');
  return urls;
}

export function sitemapLocations(xml) {
  return [...xml.matchAll(/<loc>\s*([^<]+?)\s*<\/loc>/g)].map(match => match[1].replace(/&amp;/g, '&'));
}

export function singlePostFetch(nativeFetch, { key, urls, receipt, persist }) {
  let count = 0;
  return async (destination, options = {}) => {
    requireThat(destination === ENDPOINT && options.method === 'POST' && count === 0, 'Unexpected or repeated submission blocked');
    const payload = JSON.parse(options.body);
    requireThat(payload.host === new URL(ORIGIN).host && payload.key === key && payload.keyLocation === `${ORIGIN}/${key}.txt`, 'Unexpected submission target');
    requireThat(JSON.stringify(payload.urlList) === JSON.stringify(urls), 'Submission URL list mismatch');
    count += 1;
    receipt.postAttempts = count;
    receipt.state = 'post-started-outcome-unknown';
    receipt.submittedAt = new Date().toISOString();
    persist();
    let response;
    try {
      response = await nativeFetch(destination, { ...options, redirect: 'error', signal: AbortSignal.timeout(45000) });
    } catch {
      receipt.state = 'outcome-unknown-do-not-retry';
      persist();
      throw new Error('Submission outcome unknown; inspect this receipt before any further action');
    }
    receipt.httpStatus = response.status;
    receipt.state = response.status === 200 ? 'received' : response.status === 202 ? 'received_key_validation_pending' : 'rejected-do-not-retry';
    receipt.responseAt = new Date().toISOString();
    persist();
    try {
      receipt.responseBodySha256 = hash(await response.text());
    } catch {
      receipt.responseBodyRead = 'unavailable';
    }
    persist();
    return new Response('Response body omitted from logs; see sanitized receipt.', { status: response.status });
  };
}

async function main() {
  const receipt = {
    schemaVersion: 1, state: 'not-submitted', postAttempts: 0,
    productionSha: PRODUCTION_SHA, executionSha: process.env.GITHUB_SHA,
    runId: process.env.GITHUB_RUN_ID, endpoint: ENDPOINT, origin: ORIGIN,
    helperSha256: HELPER_SHA256, mapSha256: MAP_SHA256,
    startedAt: new Date().toISOString(),
  };
  const persist = () => save('manual-indexnow-receipt.json', receipt);
  persist();
  let key;
  try {
    requireThat(process.env.GITHUB_REPOSITORY === REPO && process.env.GITHUB_REF === `refs/heads/${BRANCH}`, 'Unexpected repository or branch');
    requireThat(process.env.GITHUB_EVENT_NAME === 'push' && process.env.GITHUB_RUN_ATTEMPT === '1', 'Only the first push attempt is allowed');
    const event = JSON.parse(readFileSync(process.env.GITHUB_EVENT_PATH, 'utf8'));
    requireThat(event.before === PRODUCTION_SHA && event.after === process.env.GITHUB_SHA, 'Unexpected push event');
    requireThat(git('rev-parse', 'HEAD') === process.env.GITHUB_SHA && git('rev-parse', 'HEAD^') === PRODUCTION_SHA, 'Unexpected commit ancestry');
    const permitted = [
      'A\t.github/workflows/ansan-manual-indexnow-once.yml',
      'A\tsite-factory/ansan-flower/scripts/manual_indexnow_once.mjs',
    ].sort();
    const diff = git('diff', '--name-status', PRODUCTION_SHA, 'HEAD').split('\n').sort();
    requireThat(JSON.stringify(diff) === JSON.stringify(permitted), 'Change scope exceeds the two one-time files');
    requireThat(hash(readFileSync('scripts/submit_indexnow.mjs')) === HELPER_SHA256, 'Native submit helper changed');
    const mapBytes = readFileSync('src/data/manual-page-map.json');
    requireThat(hash(mapBytes) === MAP_SHA256, 'Manual page map changed');
    requireThat(readFileSync('production-indexing.enabled', 'utf8').length >= 0, 'Production indexing gate missing');
    const urls = selectUrls(JSON.parse(mapBytes));
    receipt.urlCount = urls.length;
    receipt.urlsSha256 = hash(JSON.stringify(urls));
    receipt.urls = urls;
    save('indexnow-urls.json', urls);
    persist();
    const repoRoot = git('rev-parse', '--show-toplevel');
    const nativeWorkflow = readFileSync(path.join(repoRoot, '.github/workflows/ansan-indexnow-production.yml'), 'utf8');
    key = nativeWorkflow.match(/^\s+INDEXNOW_KEY:\s*([A-Za-z0-9-]{8,128})\s*$/m)?.[1];
    requireThat(Boolean(key), 'Existing native ownership key unavailable');
    requireThat(nativeWorkflow.includes(`INDEXNOW_ENDPOINT: ${ENDPOINT}`), 'Native endpoint changed');
    receipt.keySha256 = hash(key);
    receipt.fingerprintSha256 = hash(JSON.stringify({
      origin: ORIGIN, sourceRevision: PRODUCTION_SHA, endpoint: ENDPOINT,
      keySha256: receipt.keySha256, urls: [...urls].sort(),
    }));
    persist();
    const nativeFetch = globalThis.fetch.bind(globalThis);
    async function get(url) {
      const response = await nativeFetch(url, { redirect: 'error', signal: AbortSignal.timeout(20000) });
      requireThat(response.status === 200, `Verification GET failed: HTTP ${response.status}`);
      return { response, text: await response.text() };
    }
    async function api(resource) { return JSON.parse((await get(`https://api.github.com/repos/${REPO}/${resource}`)).text); }
    const productionRef = await api('git/ref/heads/site-factory-ansan-v1');
    requireThat(productionRef.object?.sha === PRODUCTION_SHA, 'Production branch moved');
    for (const runId of ['37615544046', '37615544098']) {
      const run = await api(`actions/runs/${runId}`);
      requireThat(run.head_sha === PRODUCTION_SHA && run.status === 'completed' && run.conclusion === 'success', 'Required production QA run is not successful');
    }
    const runs = await api(`actions/runs?branch=${BRANCH}&per_page=100`);
    const prior = runs.workflow_runs.filter(run => run.path === '.github/workflows/ansan-manual-indexnow-once.yml' && String(run.id) !== process.env.GITHUB_RUN_ID);
    requireThat(prior.length === 0 && runs.total_count <= 100, 'Prior one-time run found; automatic retry blocked');
    const validation = { productionSha: PRODUCTION_SHA, checkedAt: new Date().toISOString(), pages: [], sitemaps: [] };
    const keyFile = await get(`${ORIGIN}/${key}.txt`);
    requireThat(keyFile.text.trim() === key, 'Live ownership key mismatch');
    validation.ownershipKeyVerified = true;
    const sitemapIndex = await get(`${ORIGIN}/sitemap-index.xml`);
    const sitemapUrls = sitemapLocations(sitemapIndex.text);
    requireThat(sitemapUrls.length > 0 && sitemapUrls.length <= 10, 'Invalid sitemap index');
    const allUrls = new Set();
    for (const sitemapUrl of sitemapUrls) {
      requireThat(sitemapUrl.startsWith(ORIGIN + '/') && new URL(sitemapUrl).origin === ORIGIN, 'Unexpected sitemap origin');
      const sitemap = await get(sitemapUrl);
      const found = sitemapLocations(sitemap.text);
      found.forEach(url => allUrls.add(url));
      validation.sitemaps.push({ url: sitemapUrl, status: 200, urls: found.length });
    }
    requireThat(allUrls.size === 38, 'Expected full 38-URL production sitemap');
    validation.sitemapUrlCount = allUrls.size;
    for (const url of [ORIGIN + '/', ...urls]) {
      requireThat(allUrls.has(url), 'Public URL absent from sitemap');
      const page = await get(url);
      verifyHtml(page.text, url, page.response.headers.get('x-robots-tag') ?? '');
      validation.pages.push({ url, status: 200, revision: PRODUCTION_SHA, canonical: true, indexFollow: true, headerIndexable: true, sitemapMember: true });
    }
    validation.completedAt = new Date().toISOString();
    save('manual-indexnow-validation.json', validation);
    receipt.state = 'verified-not-submitted';
    persist();
    process.env.SITE_ORIGIN = ORIGIN;
    delete process.env.SITE_URL;
    process.env.INDEXNOW_KEY = key;
    process.env.INDEXNOW_ENDPOINT = ENDPOINT;
    globalThis.fetch = singlePostFetch(nativeFetch, { key, urls, receipt, persist });
    await import('./submit_indexnow.mjs');
    requireThat(receipt.postAttempts === 1 && [200, 202].includes(receipt.httpStatus), 'Received receipt missing');
    console.log(`Verified receipt: ${urls.length} URLs, HTTP ${receipt.httpStatus}, production ${PRODUCTION_SHA}`);
  } catch (error) {
    if (receipt.postAttempts === 0) receipt.state = 'validation-failed-no-post';
    const message = String(error?.message ?? error);
    receipt.error = key ? message.split(key).join('[redacted]') : message;
    persist();
    console.error(receipt.error);
    process.exitCode = 1;
  } finally {
    delete process.env.INDEXNOW_KEY;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
