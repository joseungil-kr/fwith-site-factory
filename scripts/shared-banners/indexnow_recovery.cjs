'use strict';
// Read-only authorization for seven already published revisions. Live byte,
// sitemap, proof and receipt checks remain mandatory in the fixed finalizer.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const REPOSITORY = 'joseungil-kr/fwith-site-factory';
const PINS = Object.freeze({
  gwacheon: ['855ea7aa92314b455071b6d82d356604a8020de4', 12],
  gwangju: ['4f86e9db78469f031e4e3bfc9aee38e75d104cea', 27],
  jongno: ['f7b71f9f44738ebc828de8bd1521600a0f05dddd', 8],
  'seoul-yongsan': ['351de5198085c8de9815560652f66d642b08aed6', 7],
  'seoul-jungnang': ['db82b948eda3558b1352ef5c7e1eecdc118ff6ad', 5],
  yangju: ['cebd1a3c0863b18d81db204b7d879cfbe6f80565', 22],
  yangpyeong: ['4924895406ec29babb4bc82d1dbc5fd5d712d4fd', 13],
});
const TARGETS = 'docs/shared-banner-release/targets.json';
const RUNTIME = 'docs/shared-banner-release/batch30-runtime-evidence.json';
const DIGESTS = Object.freeze({
  [TARGETS]: '7cae9ae1b78dfc5d55122b95a497cecd9c674458416c099a8fd09bf7cecfc81e',
  [RUNTIME]: 'a0e567e3401d44556527401c906bdd1d7b6c47c12118b6aac15ff07ebce58f53',
});
function requireThat(ok, message) { if (!ok) throw new Error(message); }
function readEvidence(root, relative, digest) {
  requireThat(typeof relative === 'string' && relative.startsWith('docs/shared-banner-release/') &&
    !relative.split('/').includes('..') && !relative.includes('\\'), 'Invalid evidence path');
  const file = path.join(root, relative);
  const stat = fs.lstatSync(file);
  requireThat(stat.isFile() && !stat.isSymbolicLink(), 'Evidence must be a regular file');
  const bytes = fs.readFileSync(file);
  requireThat(crypto.createHash('sha256').update(bytes).digest('hex') === digest, 'Evidence digest mismatch');
  return JSON.parse(bytes);
}
function isIndexNowOnly(context, region) {
  if (context.eventName === 'workflow_dispatch') {
    const flag = context.payload.inputs?.indexnow_only;
    return flag === true || flag === 'true';
  }
  if (context.eventName !== 'issues') return false;
  const title = context.payload.issue?.title;
  return title === '[REGIONAL-INDEXNOW-ONLY] batch' ||
    (region === 'seoul-jungnang' && title === '[REGIONAL-INDEXNOW-ONLY] seoul-jungnang');
}
async function authorizeRecovery({github, context, env = process.env, region, ref, controlRoot}) {
  requireThat(Object.hasOwn(PINS, region), 'Region is outside published recovery pins');
  requireThat(isIndexNowOnly(context, region), 'Explicit IndexNow-only event required');
  requireThat(context.ref === 'refs/heads/main' && env.GITHUB_REPOSITORY === REPOSITORY &&
    `${context.repo.owner}/${context.repo.repo}` === REPOSITORY &&
    context.payload.repository?.full_name === REPOSITORY, 'Recovery repository/main mismatch');
  requireThat(env.GITHUB_RUN_ATTEMPT === '1', 'Recovery reruns disabled');
  if (context.eventName === 'issues') {
    requireThat(context.payload.action === 'opened' && context.actor === 'joseungil-kr' &&
      context.payload.issue?.user?.login === 'joseungil-kr', 'Untrusted recovery issue');
  } else {
    const owner = context.payload.repository.owner;
    if (!(owner?.type === 'User' && context.actor === owner.login)) {
      const {data} = await github.rest.repos.getCollaboratorPermissionLevel({...context.repo, username: context.actor});
      requireThat(['admin', 'maintain', 'write'].includes(data.permission), 'Untrusted recovery actor');
    }
  }
  const [revision, count] = PINS[region];
  const requested = context.eventName === 'issues' ?
    JSON.parse(context.payload.issue.body).revisions?.[region] : context.payload.inputs?.expected_revision;
  requireThat(env.REVISION === revision && requested === revision, 'Not the pinned published revision');
  requireThat(ref?.ref === `refs/heads/site-factory-${region}-direct` && ref.object?.type === 'commit' &&
    /^[0-9a-f]{40}$/.test(ref.object.sha), 'Recovery branch identity mismatch');
  const targets = readEvidence(controlRoot, TARGETS, DIGESTS[TARGETS]);
  const target = targets.targets?.[region];
  const fixed = {repository: REPOSITORY, branch: `site-factory-${region}-direct`,
    root: `site-factory/${region}-flower`, hostname: `${region}.fwith.kr`, worker: `${region}-flower-guide`, revision};
  requireThat(target && Object.entries(fixed).every(([k, v]) => target[k] === v) &&
    target.status === 'independently_reviewed_source', 'Reviewed source identity mismatch');
  const source = readEvidence(controlRoot, target.sourceReadback, target.sourceReadbackSha256);
  readEvidence(controlRoot, target.independentStaticReview, target.independentStaticReviewSha256);
  requireThat(source.sourceCommit === revision && source.parentCommit === target.previousRevision &&
    (source.allFilesMatch ?? source.all13Match) === true, 'Published source readback mismatch');
  const runtime = readEvidence(controlRoot, RUNTIME, DIGESTS[RUNTIME]);
  const sites = runtime.sites.filter(s => s.region === region);
  requireThat(sites.length === 1, 'Ambiguous historical publication');
  const evidence = sites[0].verifiedEvidence;
  const binding = evidence['binding-after.json'];
  const http = evidence['public-http.json'];
  const artifact = evidence['artifact-check.json'];
  requireThat(binding.state === 'binding_verified' && binding.accountVerified === true &&
    binding.hostname === fixed.hostname && binding.worker === fixed.worker &&
    binding.hostnameBindingExists === true && binding.workerExists === true &&
    http.state === 'public_release_verified' && http.revision === revision &&
    http.sitemapUrls === count && http.unknownHttpStatus === 404 &&
    artifact.state === 'artifact_verified' && artifact.revision === revision &&
    artifact.sitemapUrls === count, 'Historical public release mismatch');
  const {data: comparison} = await github.rest.repos.compareCommitsWithBasehead({
    ...context.repo, basehead: `${revision}...${ref.object.sha}`, per_page: 1,
  });
  requireThat(['ahead', 'identical'].includes(comparison.status) &&
    comparison.base_commit?.sha === revision && comparison.merge_base_commit?.sha === revision,
    'Published revision is not an ancestor of current branch');
  return {state: 'pinned_public_recovery_authorized', region, revision, branchHead: ref.object.sha,
    sitemapUrls: count, historicalRunId: sites[0].runId, providerMutationsAllowed: false,
    liveVerificationStillRequired: true};
}
module.exports = {isIndexNowOnly, authorizeRecovery};
