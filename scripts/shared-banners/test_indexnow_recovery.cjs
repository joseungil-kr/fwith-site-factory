'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {isIndexNowOnly, authorizeRecovery} = require('./indexnow_recovery.cjs');
const root = path.resolve(__dirname, '../..');
const regions = ['gwacheon', 'gwangju', 'jongno', 'seoul-yongsan', 'seoul-jungnang', 'yangju', 'yangpyeong'];
const targets = JSON.parse(fs.readFileSync(path.join(root, 'docs/shared-banner-release/targets.json'))).targets;
const phone = JSON.parse(fs.readFileSync(path.join(root, 'docs/shared-banner-phone-20261013/targets.json'))).targets;
function setup(region = 'gwacheon') {
  const revision = targets[region].revision;
  const tip = 'a'.repeat(40);
  const context = {repo: {owner: 'joseungil-kr', repo: 'fwith-site-factory'}, ref: 'refs/heads/main',
    eventName: 'issues', actor: 'joseungil-kr', payload: {action: 'opened',
      repository: {full_name: 'joseungil-kr/fwith-site-factory', owner: {type: 'User', login: 'joseungil-kr'}},
      issue: {title: '[REGIONAL-INDEXNOW-ONLY] batch', user: {login: 'joseungil-kr'}, body: JSON.stringify({revisions: {[region]: revision}})}}};
  const ref = {ref: `refs/heads/site-factory-${region}-direct`, object: {type: 'commit', sha: tip}};
  const calls = [];
  const comparison = {status: 'ahead', base_commit: {sha: revision}, merge_base_commit: {sha: revision}};
  const permission = {permission: 'write'};
  const github = {rest: {repos: {
    async compareCommitsWithBasehead(args) {calls.push(args); return {data: comparison};},
    async getCollaboratorPermissionLevel() {return {data: permission};},
  }}};
  const env = {REVISION: revision, GITHUB_REPOSITORY: 'joseungil-kr/fwith-site-factory', GITHUB_RUN_ATTEMPT: '1'};
  return {github, context, env, region, ref, controlRoot: root, calls, comparison, permission};
}
function requestRevision(s, revision) {
  s.env.REVISION = revision;
  s.context.payload.issue.body = JSON.stringify({revisions: {[s.region]: revision}});
}
for (const region of regions) {
  test(`${region}: accepts only recorded published pin with read-only ancestry`, async () => {
    const s = setup(region), result = await authorizeRecovery(s);
    assert.equal(result.revision, targets[region].revision);
    assert.equal(result.providerMutationsAllowed, false);
    assert.equal(result.liveVerificationStillRequired, true);
    assert.deepEqual(s.calls, [{...s.context.repo, basehead: `${s.env.REVISION}...${s.ref.object.sha}`, per_page: 1}]);
  });
  for (const kind of ['arbitrary', 'earlier', 'phone', 'native']) {
    test(`${region}: rejects ${kind} source`, async () => {
      const s = setup(region);
      const native = phone[region];
      const revision = {arbitrary: 'b'.repeat(40), earlier: targets[region].previousRevision,
        phone: native.nativeSuccessor.sourceParentRevision, native: native.revision}[kind];
      assert.notEqual(revision, targets[region].revision);
      requestRevision(s, revision);
      await assert.rejects(authorizeRecovery(s), /Not the pinned published revision/);
      assert.equal(s.calls.length, 0);
    });
  }
}
test('dispatch accepts explicit true only and enforces collaborator permissions', async () => {
  for (const value of [true, 'true']) {
    const s = setup(); s.context.eventName = 'workflow_dispatch'; s.context.actor = 'reviewer';
    s.context.payload.inputs = {indexnow_only: value, expected_revision: s.env.REVISION};
    await authorizeRecovery(s);
    s.permission.permission = 'read';
    await assert.rejects(authorizeRecovery(s), /Untrusted recovery actor/);
  }
  for (const value of [false, 'false', 1, '1', undefined]) {
    const s = setup(); s.context.eventName = 'workflow_dispatch';
    s.context.payload.inputs = {indexnow_only: value, expected_revision: s.env.REVISION};
    await assert.rejects(authorizeRecovery(s), /Explicit IndexNow-only event/);
  }
});
test('recovery is never enabled by deploy issue body or other legacy region title', async () => {
  const s = setup(); s.context.payload.issue.title = '[REGIONAL-COPY-DEPLOY] batch';
  s.context.payload.issue.body = JSON.stringify({indexnow_only: true, revisions: {gwacheon: s.env.REVISION}});
  assert.equal(isIndexNowOnly(s.context, 'gwacheon'), false);
  await assert.rejects(authorizeRecovery(s), /Explicit IndexNow-only event/);
  s.context.payload.issue.title = '[REGIONAL-INDEXNOW-ONLY] seoul-jungnang';
  assert.equal(isIndexNowOnly(s.context, 'gwacheon'), false);
  assert.equal(isIndexNowOnly(s.context, 'seoul-jungnang'), true);
});
for (const [name, change, error] of [
  ['unknown region', s => s.region = 'anseong', /outside published recovery pins/],
  ['wrong main', s => s.context.ref = 'refs/heads/dev', /repository\/main mismatch/],
  ['wrong env repository', s => s.env.GITHUB_REPOSITORY = 'evil/repo', /repository\/main mismatch/],
  ['wrong context repository', s => s.context.repo.owner = 'evil', /repository\/main mismatch/],
  ['wrong payload repository', s => s.context.payload.repository.full_name = 'evil/repo', /repository\/main mismatch/],
  ['rerun', s => s.env.GITHUB_RUN_ATTEMPT = '2', /reruns disabled/],
  ['missing attempt', s => delete s.env.GITHUB_RUN_ATTEMPT, /reruns disabled/],
  ['wrong actor', s => s.context.actor = 'evil', /Untrusted recovery issue/],
  ['wrong issue author', s => s.context.payload.issue.user.login = 'evil', /Untrusted recovery issue/],
  ['wrong action', s => s.context.payload.action = 'edited', /Untrusted recovery issue/],
  ['wrong ref kind', s => s.ref.object.type = 'tag', /branch identity mismatch/],
  ['wrong ref name', s => s.ref.ref = 'refs/heads/other', /branch identity mismatch/],
  ['invalid branch SHA', s => s.ref.object.sha = '123', /branch identity mismatch/],
  ['body-env mismatch', s => s.context.payload.issue.body = '{"revisions":{}}', /pinned published revision/],
  ['unrelated head', s => s.comparison.status = 'diverged', /not an ancestor/],
  ['older head', s => s.comparison.status = 'behind', /not an ancestor/],
  ['wrong merge base', s => s.comparison.merge_base_commit.sha = 'b'.repeat(40), /not an ancestor/],
  ['wrong base', s => s.comparison.base_commit.sha = 'b'.repeat(40), /not an ancestor/],
]) test(`rejects ${name}`, async () => {
  const s = setup(); change(s); await assert.rejects(authorizeRecovery(s), error);
});
test('identical exact public branch is allowed', async () => {
  const s = setup(); s.ref.object.sha = s.env.REVISION; s.comparison.status = 'identical';
  await authorizeRecovery(s);
});
test('changed historical evidence fails before ancestry query', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'public-pin-recovery-'));
  try {
    const folder = path.join(dir, 'docs/shared-banner-release'); fs.mkdirSync(folder, {recursive: true});
    fs.writeFileSync(path.join(folder, 'targets.json'), JSON.stringify({targets}));
    const s = setup(); s.controlRoot = dir;
    await assert.rejects(authorizeRecovery(s), /Evidence digest mismatch/);
    assert.equal(s.calls.length, 0);
  } finally {fs.rmSync(dir, {recursive: true, force: true});}
});
