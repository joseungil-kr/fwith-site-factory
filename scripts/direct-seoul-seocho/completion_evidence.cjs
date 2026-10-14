'use strict';
// Fixed GitHub GETs only; raw job logs are neither printed nor retained.
const fs = require('node:fs');
const crypto = require('node:crypto');
const repo = { owner: 'joseungil-kr', repo: 'fwith-site-factory' };
const priorRun = 38532307939;
const priorControl = '80c4427cadefd387fc06d84104049335b5b4078f';
const priorArtifact = 11877743999;
const priorDigest = 'f86b758d5081d0fe1571a925d66bde1594a03cd1159308cdad721adbf27934e3';
const buildRun = 38529418686;
const buildControl = '17b0120247c2561591fdfd0b6cfd54d6642d1a80';
const buildArtifact = 11877630325;
const buildDigest = '2869763b5413c999e83f571f8ee7aef87fd1080f9671a3bc4c9fbf6740421ff4';
function requireCheck(value, code) { if (!value) throw new Error(code); }

function actualOutcomes(logs) {
  const expected = {DEPLOY: 'success', ATTACH: 'failure', BINDING: 'failure', HTTP: 'skipped', INDEXNOW: 'skipped'};
  for (const [name, value] of Object.entries(expected)) {
    const matches = [...logs.matchAll(new RegExp('^.*?\\s' + name + ': (success|failure|skipped|cancelled)\\s*$', 'gm'))];
    requireCheck(matches.length === 1 && matches[0][1] === value, 'actual_' + name.toLowerCase() + '_outcome_unverified');
  }
  requireCheck(logs.includes('unexpected_release_files'), 'pre_provider_failure_log_required');
  return expected;
}

async function getJobLogs(jobId, token) {
  // Send the token solely to the fixed GitHub API URL. Follow one signed HTTPS
  // download location without an Authorization header, never with inherited auth.
  let response = await fetch(`https://api.github.com/repos/${repo.owner}/${repo.repo}/actions/jobs/${jobId}/logs`, {
    headers: { Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' },
    redirect: 'manual', signal: AbortSignal.timeout(30000)
  });
  if (response.status === 302) {
    const target = new URL(response.headers.get('location'));
    requireCheck(target.protocol === 'https:' && !target.username && !target.password && !target.port, 'unsafe_signed_log_url');
    response = await fetch(target, {redirect: 'error', signal: AbortSignal.timeout(30000)});
  }
  requireCheck(response.status === 200, 'job_log_get_failed');
  const bytes = Buffer.from(await response.arrayBuffer());
  requireCheck(bytes.length > 0 && bytes.length <= 5 * 1024 * 1024, 'job_log_size_invalid');
  return bytes;
}

async function run({github, token}) {
  for (const [id, sha, path] of [[priorRun, priorControl, '.github/workflows/seoul-seocho-production-publish.yml'],
                               [buildRun, buildControl, '.github/workflows/seoul-seocho-production-build-only.yml']]) {
    const {data} = await github.rest.actions.getWorkflowRun({...repo, run_id: id});
    requireCheck(data.id === id && data.run_attempt === 1 && data.status === 'completed' && data.event === 'issues'
      && data.head_branch === 'main' && data.head_sha === sha && data.path === path
      && data.repository.full_name === `${repo.owner}/${repo.repo}`
      && data.actor.login === repo.owner && data.triggering_actor.login === repo.owner, 'run_identity_mismatch');
    if (id === buildRun) requireCheck(data.conclusion === 'success', 'build_failed');
    // The previous publish summary may say success despite continued failures.
  }
  for (const [id, runId, sha, name, digest] of [
    [priorArtifact, priorRun, priorControl, `seoul-seocho-production-result-${priorRun}`, priorDigest],
    [buildArtifact, buildRun, buildControl, `seoul-seocho-production-build-${buildRun}`, buildDigest]]) {
    const {data} = await github.rest.actions.getArtifact({...repo, artifact_id: id});
    requireCheck(data.id === id && !data.expired && data.name === name && data.workflow_run.id === runId
      && data.workflow_run.head_sha === sha && data.digest === 'sha256:' + digest, 'artifact_identity_or_digest_mismatch');
  }
  const {data: jobs} = await github.rest.actions.listJobsForWorkflowRun({...repo, run_id: priorRun, filter: 'all', per_page: 100});
  requireCheck(jobs.total_count === jobs.jobs.length && jobs.total_count === 1, 'prior_jobs_inventory_mismatch');
  const job = jobs.jobs[0];
  requireCheck(job.id === 115746811691 && job.name === 'publish' && job.run_id === priorRun && job.run_attempt === 1 && job.status === 'completed'
    && job.head_sha === priorControl, 'prior_job_identity_mismatch');
  for (const [name, conclusion] of [
    ['GET-only exact account, Worker and hostname collision preflight', 'success'],
    ['Deploy fixed route-less static assets once', 'success'],
    ['Verify every public output byte, exact SEO, thin noindex and real 404', 'skipped'],
    ['Finalize exactly three URLs through existing idempotent journal 266', 'skipped']]) {
    const steps = job.steps.filter(step => step.name === name);
    requireCheck(steps.length === 1 && steps[0].conclusion === conclusion, 'prior_step_unverified');
  }
  // Do not demand attach/readback API conclusion=failure: continue-on-error
  // reports success there. The actual environment outcomes and pinned reports bind them.
  const rawLogs = await getJobLogs(job.id, token);
  actualOutcomes(rawLogs.toString('utf8'));
  const proof = {state: 'prior_upload_actual_outcomes_verified', priorRunId: String(priorRun), priorControlSha: priorControl,
    priorArtifactId: String(priorArtifact), priorArchiveSha256: priorDigest, runAttempt: 1, jobId: job.id,
    jobLogSha256: crypto.createHash('sha256').update(rawLogs).digest('hex'), deployOutcome: 'success', attachOutcome: 'failure',
    bindingOutcome: 'failure', httpOutcome: 'skipped', indexnowOutcome: 'skipped', buildRunId: String(buildRun),
    buildArtifactId: String(buildArtifact), buildControlSha: buildControl};
  fs.writeFileSync('prior-upload-api.json', JSON.stringify(proof, null, 2) + '\n');
}
module.exports = {run, actualOutcomes};
