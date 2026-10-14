import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {getReleaseMode, TARGET, PREVIEW_ORIGIN, SITEMAP_ROUTES} from '../scripts/release_mode.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const fixtureProof = 'TEST-ONLY-NOT-FOR-PUBLICATION';
function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'seocho-release-test-'));
  t.after(() => rmSync(root, {recursive: true, force: true}));
  mkdirSync(join(root, 'src/data'), {recursive: true}); mkdirSync(join(root, 'public'));
  for (const name of ['site-config.json', 'production-target.json', 'seocho-copy.json'])
    writeFileSync(join(root, 'src/data', name), readFileSync(new URL('../src/data/' + name, import.meta.url)));
  writeFileSync(join(root, 'public', fixtureProof + '.txt'), fixtureProof + '\n');
  const reference = 'https://github.com/joseungil-kr/fwith-site-factory/blob/' + 'b'.repeat(40) + '/TEST-ONLY.json';
  const binding = {schemaVersion: 1, state: 'approved', ...TARGET,
    sourceRevision: 'a'.repeat(40), sourceContractSha256: 'c'.repeat(64),
    approvals: {publication: true, hostBinding: true, indexNowProof: true},
    evidenceReferences: {publication: reference, hostBinding: reference, indexNowProof: reference},
    proof: {origin: TARGET.origin, path: '/' + fixtureProof + '.txt', sha256: sha(fixtureProof + '\n')},
    sitemapRoutes: [...SITEMAP_ROUTES], notFoundStatus: 404, thinDirectoryRobots: 'noindex,follow'};
  const env = {SITE_RELEASE_MODE: 'production', SITE_INDEXABLE: 'true', SITE_URL: TARGET.origin,
    SITE_FACTORY_REVISION: binding.sourceRevision, SITE_RELEASE_BINDING_PATH: join(root, 'TEST-ONLY-binding.json')};
  const save = () => { const data = JSON.stringify(binding); writeFileSync(env.SITE_RELEASE_BINDING_PATH, data); env.SITE_RELEASE_BINDING_SHA256 = sha(data); };
  save(); return {root, binding, env, save};
}

test('default preview retains local origin and no indexing', () => {
  const result = getReleaseMode(process.cwd(), {});
  assert.equal(result.origin, PREVIEW_ORIGIN); assert.equal(result.indexable, false); assert.deepEqual(result.sitemapRoutes, []);
});
for (const [name, env] of Object.entries({
  indexing: {SITE_INDEXABLE: 'true'}, hostname: {SITE_URL: TARGET.origin},
  mode: {SITE_RELEASE_MODE: 'anything'}, binding: {SITE_RELEASE_BINDING_PATH: '/fake'},
})) test('preview rejects ' + name, () => assert.throws(() => getReleaseMode(process.cwd(), env)));

test('explicit pinned fixture permits only three indexable production routes', t => {
  const f = fixture(t); const result = getReleaseMode(f.root, f.env);
  assert.equal(result.indexable, true); assert.deepEqual(result.sitemapRoutes, SITEMAP_ROUTES);
  assert.equal(result.notFoundStatus, 404); assert.equal(result.thinDirectoryRobots, 'noindex,follow');
});
for (const [name, mutate] of Object.entries({
  pending: b => { b.state = 'pending'; },
  hostname: b => { b.hostname = 'other.fwith.kr'; },
  origin: b => { b.origin = PREVIEW_ORIGIN; },
  worker: b => { b.worker += '-other'; },
  sourceRoot: b => { b.sourceRoot = 'site-factory/other'; },
  siteKey: b => { b.siteKey = 'other'; },
  repository: b => { b.repository = 'other/other'; },
  frozenRevision: b => { b.frozenSourceRevision = 'd'.repeat(40); },
  copyFingerprint: b => { b.customerCopySha256 = 'd'.repeat(64); },
  sourceRevision: b => { b.sourceRevision = 'd'.repeat(40); },
  shortRevision: b => { b.sourceRevision = 'a'.repeat(7); },
  contractMissing: b => { delete b.sourceContractSha256; },
  publication: b => { b.approvals.publication = false; },
  hostApproval: b => { b.approvals.hostBinding = false; },
  proofApproval: b => { b.approvals.indexNowProof = false; },
  approvalString: b => { b.approvals.publication = 'true'; },
  missingEvidence: b => { delete b.evidenceReferences.hostBinding; },
  movingEvidence: b => { b.evidenceReferences.publication = 'https://github.com/joseungil-kr/fwith-site-factory/blob/main/approval.json'; },
  unrelatedEvidence: b => { b.evidenceReferences.publication = 'https://example.com/approval'; },
  missingProof: b => { delete b.proof; },
  proofOrigin: b => { b.proof.origin = 'https://other.fwith.kr'; },
  proofTraversal: b => { b.proof.path = '/../other.txt'; },
  proofDigest: b => { b.proof.sha256 = 'd'.repeat(64); },
  extraSitemap: b => { b.sitemapRoutes.push('/regions/'); },
  missingSitemap: b => { b.sitemapRoutes.pop(); },
  duplicateSitemap: b => { b.sitemapRoutes.push('/'); },
  thinDirectory: b => { b.thinDirectoryRobots = 'index,follow'; },
  soft404: b => { b.notFoundStatus = 200; },
})) test('production rejects ' + name, t => {
  const f = fixture(t); mutate(f.binding); f.save(); assert.throws(() => getReleaseMode(f.root, f.env));
});
for (const [name, mutate] of Object.entries({
  flag: e => { delete e.SITE_INDEXABLE; }, origin: e => { e.SITE_URL += '/'; },
  revision: e => { delete e.SITE_FACTORY_REVISION; }, missingPath: e => { delete e.SITE_RELEASE_BINDING_PATH; },
  relativePath: e => { e.SITE_RELEASE_BINDING_PATH = 'local-binding.json'; },
  missingDigest: e => { delete e.SITE_RELEASE_BINDING_SHA256; },
  changedDigest: e => { e.SITE_RELEASE_BINDING_SHA256 = 'd'.repeat(64); },
})) test('production rejects environment ' + name, t => {
  const f = fixture(t); mutate(f.env); assert.throws(() => getReleaseMode(f.root, f.env));
});
test('production rejects modified customer copy', t => {
  const f = fixture(t); writeFileSync(join(f.root, 'src/data/seocho-copy.json'), '{}'); assert.throws(() => getReleaseMode(f.root, f.env));
});
test('matching proof hash cannot disguise incorrect proof body', t => {
  const f = fixture(t); writeFileSync(join(f.root, 'public', fixtureProof + '.txt'), 'wrong');
  f.binding.proof.sha256 = sha('wrong'); f.save(); assert.throws(() => getReleaseMode(f.root, f.env), /body_mismatch/);
});
for (const suffix of ['', '\r\n', '\n\n', ' \n']) {
  test('proof keeps exact existing LF bytes: reject ' + JSON.stringify(suffix), t => {
    const f = fixture(t); const body = fixtureProof + suffix;
    writeFileSync(join(f.root, 'public', fixtureProof + '.txt'), body);
    f.binding.proof.sha256 = sha(body); f.save();
    assert.throws(() => getReleaseMode(f.root, f.env), /body_mismatch/);
  });
}
test('proposed target cannot promote itself to approval', t => {
  const f = fixture(t); const path = join(f.root, 'src/data/production-target.json');
  const proposal = JSON.parse(readFileSync(path)); proposal.publicationApproved = true;
  writeFileSync(path, JSON.stringify(proposal)); assert.throws(() => getReleaseMode(f.root, f.env), /must_not_claim/);
});
test('historical preview config remains immutable', t => {
  const f = fixture(t); const path = join(f.root, 'src/data/site-config.json');
  const config = JSON.parse(readFileSync(path)); config.productionApproved = true;
  writeFileSync(path, JSON.stringify(config)); assert.throws(() => getReleaseMode(f.root, f.env), /frozen_preview/);
});
