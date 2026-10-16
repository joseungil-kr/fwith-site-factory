#!/usr/bin/env python3
"""Damyang existing-host static caller; actual operational binding is required.

Consumes the actual retained build as data. It never executes source/artifact
code. The only HTTP write here is one durable claim on the original receipt.
The separately reviewed workflow owns one pinned static uploader invocation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPRedirectHandler

D = Path(__file__).resolve().parent
ROOT = D.parents[1]
OPERATIONAL_CONTROLS_ENABLED = True
IMPORT_PINS = {
  "assets_only.py": "2d424b7821d323c917fd92be3e6bdde062eb7754425011002d8564a1525b289c",
  "beacon_normalization.py": "6782ef230efcc88d7c17eb0e2f043317271a0b64c5b9150f2829ce4a3847cd67",
  "existing_provider.py": "f4e8bb7e4e0553d7535b713ecdae0fd4bc32608f692a91ba7c7f232b5a25ecb0",
  "existing_update.py": "52345dd7dfff910fc17441e1d2b91a58c532b88f34dcdc65aa752f851a3c99df",
  "finalize_recovery.py": "95585304bf31ed9b7b8c10fa3c42f20806c2d8e0b40867d8a2b27ed83af3ef8f",
  "indexnow_recovery.py": "59f23a38bc14925261901d182bd6d503827d16f95bda9368619159a1dd8021f4",
  "managed_robots.py": "51eebc7dc9a405ade4c5f7da6cdb086a8319d2df690b5b9429e20bd764cbdee5",
  "previous_public.py": "c88277a6c00bfecf5c360bfbe64b3a0b9aeceedd77fedf68e2e01d4d329b897a",
  "provider_baseline.py": "087d1047de4f236c5082cb6601007670854bdfc567d2e621310422afe8902111",
  "public_release.py": "712562d65952acacca6d33bb628e9f454eeef3cc2f4d3aac5166d4271ba7987c",
  "recovery_build.py": "5a1c4b9d7ec6ca79caf36688c183935af77694d572bf63201d3a028b2beb5da5",
  "recovery_output.py": "559c00b6dbbbe85ef1dbd9a0bef026a75d8fe241839d8392d0cef59c1c52a6fd"
}


def verify_imports(root=ROOT):
    # All transitive nonstdlib helpers are pinned BEFORE importing them.
    for name, expected in IMPORT_PINS.items():
        p = Path(root) / 'scripts/direct-damyang-recovery' / name
        if (not p.is_file() or any(q.is_symlink() for q in (p, *p.parents))
                or hashlib.sha256(p.read_bytes()).hexdigest() != expected):
            raise ValueError('immutable_update_helper_required')


verify_imports()
import finalize_recovery as reader
import existing_update as update
import provider_baseline as baseline
import indexnow_recovery as journal
import public_release

require = journal.require
sha = journal.sha
exact = journal.exact
read_json = reader.read_json
SOURCE = reader.SOURCE
TITLE = '[DAMYANG-EXISTING-STATIC-UPDATE] 20261016'
JOB = 'recovery_static_update'
WORKFLOW = reader.WORKFLOW
CONCURRENCY = reader.CONCURRENCY
DOWNLOAD_NAMES = {'build': 'damyang-recovery-build', 'baseline': 'damyang-recovery-baseline'}
ORIGINAL_WORKFLOW_BYTES = 11583
ORIGINAL_WORKFLOW_SHA256 = '877c5c678cd3c1e3c7b1299cf68cd1f735ae9a0f7c0bae6316e21ccc9dc9d87d'
PRIOR_CONFIG = 'docs/direct-damyang-recovery/prior-publication/wrangler.publish.json'
FIRST_PUBLISH_PATH = 'scripts/direct-damyang/publish.py'
FIRST_PUBLISH_SHA256 = 'd886a9e5091ab9b65d41e25b6cf181fb8af994da17c022b2e86a22a262560c71'
PRIOR_CONFIG_SHA256 = 'ce51a23cdaa8024f0fb1ade0764e53aa1bacd56dd5cd5ffedd5856f5c31f733c'
PROVIDER_KEYS = frozenset(('CLOUDFLARE_API_TOKEN', 'CLOUDFLARE_ACCOUNT_ID'))
PROVIDER_MODES = frozenset(('preflight', 'recheck', 'readback'))
MODES = ('prepare', 'artifact', 'preflight', 'claim', 'recheck', 'parse-upload', 'readback', 'public')
ENV_KEYS = reader.TRUSTED_ENV_KEYS | {'RUNNER_TEMP'}


def approved_pins(path):
    require(OPERATIONAL_CONTROLS_ENABLED is True, 'operational_review_seal_missing')
    pins = read_json(path)
    require(type(pins) is dict and pins.get('status') == 'INDEPENDENTLY_REVIEWED_ACTUAL_STATIC_UPDATE'
            and pins.get('operationalActivationAllowed') is True and pins.get('providerBaselineAccepted') is True,
            'actual_baseline_and_operational_acceptance_required')
    for key in ('baseline', 'review', 'controlFiles', 'workflowFiles'):
        require(type(pins.get(key)) is dict and bool(pins[key]), 'actual_' + key.lower() + '_binding_required')
    require(journal._valid_sha(pins.get('reviewedControlRevision'), 40), 'reviewed_control_revision_required')
    return pins


def authorize(pins, env, event, mode):
    require(sys.flags.optimize == 0 and mode in MODES, 'unoptimized_fixed_mode_required')
    allowed = ENV_KEYS | (PROVIDER_KEYS if mode in PROVIDER_MODES else set())
    require(set(env) <= allowed, 'clean_update_environment_required')
    if mode in PROVIDER_MODES:
        require(all(type(env.get(k)) is str and env[k] for k in PROVIDER_KEYS), 'provider_get_credentials_required')
    else:
        require(not any(k.startswith(('CLOUDFLARE_', 'CF_', 'WRANGLER_')) for k in env), 'provider_environment_forbidden')
    require(env.get('GITHUB_REPOSITORY') == journal.REPOSITORY and env.get('GITHUB_REF') == 'refs/heads/main'
            and env.get('GITHUB_ACTOR') == reader.OWNER and env.get('GITHUB_TRIGGERING_ACTOR') == reader.OWNER
            and env.get('GITHUB_RUN_ATTEMPT') == '1' and env.get('GITHUB_EVENT_NAME') == 'issues'
            and env.get('GITHUB_JOB') == JOB and env.get('RUNNER_ENVIRONMENT') == 'github-hosted'
            and journal._valid_sha(env.get('GITHUB_SHA'), 40)
            and re.fullmatch('[1-9][0-9]*', env.get('GITHUB_RUN_ID', '')),
            'exact_owner_main_first_hosted_job_required')
    repo = event.get('repository', {}); issue = event.get('issue', {})
    require(event.get('action') == 'opened' and repo.get('full_name') == journal.REPOSITORY
            and repo.get('owner', {}).get('login') == reader.OWNER and repo.get('owner', {}).get('type') == 'User'
            and event.get('sender', {}).get('login') == reader.OWNER and event.get('sender', {}).get('type') == 'User',
            'exact_event_identity_required')
    require(issue.get('title') == TITLE and issue.get('user', {}).get('login') == reader.OWNER
            and issue.get('user', {}).get('type') == 'User' and issue.get('state') == 'open'
            and reader.positive(issue.get('number')) and issue['number'] != 377 and 'pull_request' not in issue,
            'exact_update_request_issue_required')
    raw = issue.get('body')
    require(type(raw) is str and len(raw.encode()) <= 4096, 'bounded_request_body_required')
    expected = {'schemaVersion': 1, 'mode': 'existing-host-static-proof-update',
        'source_branch': reader.SOURCE_BRANCH, 'source_revision': SOURCE,
        'expected_control_revision': env['GITHUB_SHA'], 'receipt_issue': 377,
        'operational_binding_sha256': journal.digest(pins)}
    require(exact(reader.json_raw(raw), expected), 'closed_exact_request_required')
    require(pins.get('schemaVersion') == 1 and pins.get('sourceRevision') == SOURCE
            and pins.get('sourceBranch') == reader.SOURCE_BRANCH and pins.get('sourceTree') == reader.SOURCE_TREE,
            'fixed_successor_binding_required')
    require(exact(pins.get('build'), reader.ACTUAL_BUILD)
            and exact(pins.get('acceptedBuildReview'), reader.ACCEPTED_BUILD_REVIEW), 'fixed_actual_build_and_review_binding_required')
    require(type(pins.get('baseline')) is dict and type(pins.get('review')) is dict,
            'actual_baseline_and_review_required')
    for role in ('build', 'baseline'):
        row = pins[role]
        require(reader.positive(row.get('runId')) and reader.positive(row.get('artifactId'))
                and reader.positive(row.get('artifactBytes')) and journal._valid_sha(row.get('controlRevision'), 40)
                and type(row.get('artifactName')) is str and bool(row['artifactName'])
                and re.fullmatch('sha256:[0-9a-f]{64}', row.get('artifactDigest', '')), 'actual_run_artifact_identity_required')
    return expected


def verify_roots(workspace, build_root, baseline_root, *, preparing):
    require(type(workspace) is str and Path(workspace).is_absolute(), 'fixed_workspace_required')
    base = Path(workspace)
    require(base.is_dir() and Path.cwd() == base and not any(p.is_symlink() for p in (base, *base.parents)),
            'clean_workspace_required')
    for role, value in (('build', build_root), ('baseline', baseline_root)):
        p = Path(value)
        require('..' not in p.parts and p.absolute() == base / DOWNLOAD_NAMES[role]
                and not any(q.is_symlink() for q in (p.absolute(), *p.absolute().parents)), 'fixed_download_root_required')
        require(not p.exists() if preparing else p.is_dir(), 'fresh_or_downloaded_root_required')
    for name in ('release', 'update-source-config.json', 'deployment-attempt-claim.json', 'provider-state-before.json'):
        p = base / name
        require(not p.is_symlink(), 'update_output_symlink_forbidden')
        if preparing: require(not p.exists(), 'fresh_update_workspace_required')
    return True


def verify_controls(root, pins):
    root = Path(root); verify_imports(root)
    files = pins['controlFiles']
    for name, expected in files.items():
        require(type(name) is str and re.fullmatch('[A-Za-z0-9_./-]+', name)
                and not name.startswith('/') and '..' not in name.split('/'), 'unsafe_control_path')
        require(sha(public_release.read_file(root / name)) == expected, 'reviewed_control_bytes_changed')
    required = {'scripts/direct-damyang-recovery/' + n for n in IMPORT_PINS}
    required |= {WORKFLOW, 'scripts/direct-damyang-recovery/publish_existing_update.py',
        'scripts/direct-damyang-recovery/accepted-provider-baseline-binding.json',
        'scripts/direct-damyang-recovery/provider-baseline-policy.json',
        'docs/direct-damyang-recovery/source-files.json', PRIOR_CONFIG, FIRST_PUBLISH_PATH,
        reader.ACCEPTED_BUILD_REVIEW['path']}
    required |= {r['path'] for r in baseline.load_policy()['evidence']}
    require(required <= set(files), 'complete_update_control_inventory_required')
    for name, expected in IMPORT_PINS.items():
        require(files['scripts/direct-damyang-recovery/' + name] == expected, 'immutable_update_helper_pin_required')
    workflows = {p.relative_to(root).as_posix(): sha(public_release.read_file(p))
        for p in (root / '.github/workflows').iterdir() if p.suffix in ('.yml', '.yaml')}
    require(exact(workflows, pins['workflowFiles']), 'all_workflow_inventory_changed')
    require(sha(public_release.read_file(root / FIRST_PUBLISH_PATH)) == FIRST_PUBLISH_SHA256,
            'original_first_publish_absent_target_guard_changed')
    raw = public_release.read_file(root / WORKFLOW)
    require(sha(raw[:ORIGINAL_WORKFLOW_BYTES]) == ORIGINAL_WORKFLOW_SHA256,
            'original_publish_and_baseline_jobs_changed')
    text = raw.decode(); marker = '\n  ' + JOB + ':\n'
    require(text.count(marker) == 1 and text.count('\nconcurrency:\n  group: ' + CONCURRENCY
            + '\n  cancel-in-progress: false\n') == 1, 'shared_concurrency_and_single_update_job_required')
    suffix = re.split(r'\n  [A-Za-z0-9_-]+:\n', text.split(marker, 1)[1], maxsplit=1)[0]
    require(suffix.count('wrangler@4.148.0 deploy --config') == 1, 'single_pinned_static_upload_required')
    review = pins['review']; name = review.get('path')
    require(type(name) is str and name.startswith('docs/direct-damyang-recovery/')
            and '..' not in name.split('/') and journal._valid_sha(review.get('sha256'), 64), 'review_path_and_digest_required')
    body = public_release.read_file(root / name)
    require(sha(body) == review['sha256'], 'independent_operational_review_bytes_changed')
    report = reader.json_raw(body)
    expected = {'verdict': 'ACCEPT_ACTUAL_BASELINE_AND_DAMYANG_STATIC_UPDATE_CONTROLS',
        'sourceRevision': SOURCE, 'reviewedControlRevision': pins['reviewedControlRevision'],
        'controlFilesSHA256': journal.digest(files), 'workflowFilesSHA256': journal.digest(workflows),
        'buildBindingSHA256': journal.digest(pins['build']), 'baselineBindingSHA256': journal.digest(pins['baseline']),
        'artifactFilesSHA256': journal.digest(pins['artifactFiles']), 'releaseFilesSHA256': journal.digest(pins['releaseFiles']),
        'allHostPublishersUseSharedConcurrency': True, 'sourceAndArtifactCodeExecutionAllowed': False,
        'hostnameAttachAllowed': False, 'automaticReuploadAllowed': False, 'freshLiveBrowserPixelsClaimed': False}
    require(type(report) is dict and all(exact(report.get(k), v) for k, v in expected.items()),
            'complete_independent_update_review_required')
    return True


def validate_baseline(root, pins):
    desc, observation, review = update.accepted_baseline()
    row = pins['baseline']
    require(exact({k: row.get(k) for k in ('runId', 'controlRevision', 'artifactId', 'artifactDigest')},
        {'runId': desc['observationRunId'], 'controlRevision': desc['observationControlRevision'],
         'artifactId': desc['observationArtifactId'], 'artifactDigest': desc['observationArtifactDigest']}),
        'baseline_descriptor_artifact_cross_binding_required')
    require(type(row.get('files')) is dict and bool(row['files'])
            and public_release.file_inventory(root) == row['files'], 'exact_accepted_baseline_artifact_required')
    path = row.get('observationPath')
    require(type(path) is str and path in row['files'] and row['files'][path] == desc['sha256'],
            'actual_observation_artifact_membership_required')
    raw = public_release.read_file(Path(root) / path)
    require(sha(raw) == desc['sha256'] and exact(reader.json_raw(raw), observation)
            and exact(row.get('independentAcceptance'), review), 'independent_baseline_bytes_binding_required')
    reader.checked_version_coverage(observation['currentProviderState']['activeDeployment'])
    return observation


def release_review(pins):
    return {'buildRunId': pins['build']['runId'], 'artifactId': pins['build']['artifactId'],
        'artifactDigest': pins['build']['artifactDigest'], 'outputFilesSha256': journal.digest(pins['releaseFiles']),
        'releaseManifestSha256': pins['releaseManifestSha256']}


def original_config(root):
    raw = public_release.read_file(Path(root) / PRIOR_CONFIG)
    require(sha(raw) == PRIOR_CONFIG_SHA256, 'original_actual_static_config_bytes_required')
    # Provenance is original publication38861200090, not successor source81.
    return raw


def stage_release(build_root, pins, control_root):
    source = reader.validate_retained_artifact(build_root, pins)
    reader.validate_actual_build_review(build_root, pins, control_root)
    require(not Path('release').exists(), 'fresh_release_directory_required')
    Path('release').mkdir()
    shutil.copytree(source / 'dist', 'release/dist', symlinks=False)
    Path('release/release.json').write_bytes(public_release.read_file(source / 'release.json'))
    Path('release/wrangler.publish.json').write_bytes(original_config(control_root))
    public_release.verify_release('release/dist', pins['releaseFiles'], SOURCE)
    update.source_config()
    return {'state': 'EXACT_RETAINED_24_CONSUMED_AND_RELEASE17_STAGED', 'sourceRevision': SOURCE,
        'artifactId': pins['build']['artifactId'], 'artifactDigest': pins['build']['artifactDigest'],
        'files': 17, 'sourceCodeExecuted': False, 'artifactCodeExecuted': False, 'newLiveBrowserObserved': False}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None


class UpdateHTTP:
    """Fixed GET destinations; one original-receipt claim POST; no retry."""
    def __init__(self, token, api_urls, public_urls, *, opener=None, clock=time.monotonic):
        require(type(token) is str and token and '\r' not in token and '\n' not in token,
                'workflow_github_token_required')
        self.token = token; self.api_urls = frozenset(api_urls); self.public_urls = frozenset(public_urls)
        self.opener = opener if opener is not None else build_opener(NoRedirect())
        self.clock = clock; self.claim_reserved = False

    def call(self, method, url, payload=None):
        page = re.fullmatch(re.escape(journal.API_BASE) + r'/issues/comments\?per_page=100&page=([1-9][0-9]{0,4})', url)
        comment = re.fullmatch(re.escape(journal.API_BASE) + r'/issues/comments/[1-9][0-9]*', url)
        api = url in self.api_urls or (page is not None and int(page[1]) <= journal.MAX_PAGES) or comment is not None
        write = method == 'POST' and url == journal.ISSUE_URL + '/comments'
        require((method == 'GET' and payload is None and (api or url in self.public_urls))
                or (write and type(payload) is bytes and len(payload) <= 65536), 'fixed_update_http_scope_required')
        if write:
            require(not self.claim_reserved, 'single_claim_post_only')
            self.claim_reserved = True
        headers = {'User-Agent': 'Damyang-Existing-Static-Update/1.0', 'Accept-Encoding': 'identity',
            'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        if api or write:
            headers.update(Authorization='Bearer ' + self.token, Accept='application/vnd.github+json')
            headers['X-GitHub-Api-Version'] = '2022-11-28'
        if write: headers['Content-Type'] = 'application/json; charset=utf-8'
        request = Request(url, data=payload, headers=headers, method=method); start = self.clock()
        try: response = self.opener.open(request, timeout=20)
        except HTTPError as error: response = error
        except Exception: raise journal.RecoveryBlocked('http_outcome_unconfirmed') from None
        try:
            with response:
                require(response.geturl() == url and type(response.code) is int
                        and not 300 <= response.code < 400, 'redirect_or_unexpected_response_forbidden')
                pairs = list(response.headers.items())
                require(len(pairs) <= 100 and all(len(k) <= 128 and len(v) <= 4096 for k, v in pairs), 'http_header_limit')
                lengths = [v for k, v in pairs if k.lower() == 'content-length']
                require(len(lengths) <= 1 and (not lengths or lengths[0].isdigit()
                        and int(lengths[0]) <= journal.MAX_RESPONSE), 'http_length_limit')
                encodings = [v for k, v in pairs if k.lower() == 'content-encoding']
                require(len(encodings) <= 1 and (not encodings or encodings[0].lower() == 'identity'), 'compressed_response_forbidden')
                body = bytearray(); read = getattr(response, 'read1', response.read)
                while True:
                    require(self.clock() - start <= 60, 'http_deadline_exceeded')
                    part = read(min(65536, journal.MAX_RESPONSE + 1 - len(body)))
                    if not part: break
                    body.extend(part); require(len(body) <= journal.MAX_RESPONSE, 'http_body_limit')
                require(not lengths or len(body) == int(lengths[0]), 'truncated_http_body')
                return journal.RawResponse(response.code, bytes(body), pairs)
        except journal.RecoveryBlocked: raise
        except Exception: raise journal.RecoveryBlocked('http_outcome_unconfirmed') from None


class GitHubClient:
    # Reuse only strict GET/pagination; no inherited journal-writing method.
    get = reader.GitHubClient.get
    read_page = reader.GitHubClient.read_page
    def __init__(self, http): self.http = http
    def pages(self):
        pages = []
        for number in range(1, journal.MAX_PAGES + 1):
            page = self.read_page(number); pages.append(page)
            if page.next_url is None: return pages
        raise journal.RecoveryBlocked('repository_page_limit_reached')
    def create_claim(self, record):
        body = update.MARKER + json.dumps(record, ensure_ascii=False, sort_keys=True)
        response = self.http.call('POST', journal.ISSUE_URL + '/comments', json.dumps({'body': body}).encode())
        require(response.status == 201, 'claim_creation_unconfirmed_no_retry')
        created = reader.json_raw(response.body); journal._trusted_comment(created)
        require(created['body'] == body, 'claim_write_echo_mismatch')
        actual, _ = self.get(journal.API_BASE + '/issues/comments/' + str(created['id']))
        journal._trusted_comment(actual)
        require(actual['id'] == created['id'] and actual['body'] == body, 'claim_direct_readback_mismatch')
        return update.validate_claim_echo(record, actual, self.pages())


def api_urls(pins, run_id):
    urls = {journal.API_BASE + '/git/ref/heads/main', journal.API_BASE + '/git/ref/heads/' + reader.SOURCE_BRANCH,
        journal.API_BASE + '/git/commits/' + SOURCE, journal.API_BASE + '/git/trees/' + reader.SOURCE_TREE + '?recursive=1',
        journal.ISSUE_URL, journal.API_BASE + '/actions/runs/' + run_id}
    for role in ('build', 'baseline'):
        urls.add(journal.API_BASE + '/actions/runs/' + str(pins[role]['runId']))
        urls.add(journal.API_BASE + '/actions/artifacts/' + str(pins[role]['artifactId']))
    return urls


class Runtime:
    def __init__(self, pins, env, control_root, build_root, baseline_root, github, http):
        self.pins = pins; self.env = env; self.control_root = Path(control_root)
        self.build_root = Path(build_root); self.baseline_root = Path(baseline_root)
        self.github = github; self.http = http; self.review = release_review(pins)

    def metadata(self):
        main, _ = self.github.get(journal.API_BASE + '/git/ref/heads/main')
        require(main.get('object', {}).get('type') == 'commit'
                and main.get('object', {}).get('sha') == self.env['GITHUB_SHA'], 'main_moved_since_exact_request')
        run, _ = self.github.get(journal.API_BASE + '/actions/runs/' + self.env['GITHUB_RUN_ID'])
        reader.verify_run({'runId': int(self.env['GITHUB_RUN_ID']), 'controlRevision': self.env['GITHUB_SHA']}, run, WORKFLOW, current=True)
        reader.validate_source(self.github, read_json(self.control_root / 'docs/direct-damyang-recovery/source-files.json'))
        for role, path in (('build', reader.BUILD_WORKFLOW), ('baseline', WORKFLOW)):
            row = self.pins[role]
            run, _ = self.github.get(journal.API_BASE + '/actions/runs/' + str(row['runId']))
            reader.verify_run(row, run, path)
            artifact, _ = self.github.get(journal.API_BASE + '/actions/artifacts/' + str(row['artifactId']))
            reader.verify_artifact_meta(row, artifact)
        issue, _ = self.github.get(journal.ISSUE_URL)
        require(issue.get('number') == 377 and issue.get('state') == 'open'
                and issue.get('title') == '[DAMYANG-INDEXNOW-RECEIPTS] 20261016'
                and issue.get('user', {}).get('login') == reader.OWNER and 'pull_request' not in issue
                and issue.get('repository_url') == journal.API_BASE, 'original_receipt_identity_required')
        return True

    def artifact(self):
        reader.validate_retained_artifact(self.build_root, self.pins)
        reader.validate_actual_build_review(self.build_root, self.pins, self.control_root)
        return validate_baseline(self.baseline_root, self.pins)

    def stage_exact(self):
        public_release.verify_release('release/dist', self.pins['releaseFiles'], SOURCE)
        require(public_release.read_file('release/release.json') == public_release.read_file(self.build_root / 'release-recovery/release.json'),
                'staged_manifest_bytes_changed')
        original_config(self.control_root)
        if Path('update-source-config.json').exists():
            require(exact(read_json('update-source-config.json'), reader.json_raw(original_config(self.control_root))), 'original_config_changed')
        else:
            require(public_release.read_file('release/wrangler.publish.json') == original_config(self.control_root), 'original_config_changed')
        return True

    def claim(self):
        require(not Path('deployment-attempt-claim.json').exists(), 'local_claim_already_present_no_retry')
        before = read_json('binding-before.json')
        desc, observation, _ = update.accepted_baseline()
        require(before.get('state') == 'EXACT_ACCEPTED_EXISTING_TARGET_RECHECKED'
                and before.get('runId') == self.env['GITHUB_RUN_ID']
                and before.get('controlRevision') == self.env['GITHUB_SHA']
                and before.get('acceptedObservationSHA256') == desc['sha256']
                and before.get('providerStateSHA256') == journal.digest(observation['currentProviderState'])
                and exact(read_json('provider-state-before.json'), observation['currentProviderState']),
                'exact_current_run_preflight_required')
        record = update.select_claim(self.github.pages(), update.attempt_identity(self.review, self.env))
        # A failure after this reservation never retries the write or uploads.
        require(not Path('claim-write-reserved.json').exists(), 'claim_write_already_reserved_no_retry')
        baseline.save('claim-write-reserved.json', {'state': 'ONE_CLAIM_WRITE_RESERVED_NO_RETRY', 'runId': self.env['GITHUB_RUN_ID']})
        claim = self.github.create_claim(record)
        baseline.save('deployment-attempt-claim.json', claim)
        return claim

    def recheck(self):
        claim = update.verify_claim(self.review, self.env)
        self.metadata(); self.stage_exact()
        update.inspect_full_journal(self.github.pages(), own_claim=claim)
        result = update.recheck(self.review, self.env)
        self.stage_exact()
        return result

    def public(self):
        update.verify_claim(self.review, self.env)
        observations = []
        def get(url):
            try:
                response = self.http.call('GET', url)
                observations.append({'url': url, 'httpStatus': response.status, 'bodySHA256': sha(response.body)})
                return response
            except Exception:
                observations.append({'url': url, 'outcome': 'unconfirmed'})
                raise
        try:
            return public_release.verify_public_release(self.build_root / 'release-recovery/dist', self.pins['releaseFiles'], SOURCE, get)
        finally:
            baseline.save('public-http-observations.json', {'state': 'OBSERVATIONS_ONLY_NOT_ACCEPTANCE',
                'sourceRevision': SOURCE, 'responses': observations, 'liveBrowserPixelsVerified': False})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=MODES)
    parser.add_argument('--control-root', type=Path, default=Path('control'))
    parser.add_argument('--build-root', type=Path, default=Path('damyang-recovery-build'))
    parser.add_argument('--baseline-root', type=Path, default=Path('damyang-recovery-baseline'))
    parser.add_argument('--upload-log', type=Path); parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        pins = approved_pins(args.control_root / 'docs/direct-damyang-recovery/update-caller-binding.json')
        env = dict(os.environ); event = read_json(env.get('GITHUB_EVENT_PATH', ''))
        authorize(pins, env, event, args.mode)
        require(args.control_root.resolve() == ROOT, 'executing_control_root_mismatch')
        verify_roots(env.get('GITHUB_WORKSPACE'), args.build_root, args.baseline_root, preparing=args.mode == 'prepare')
        verify_controls(args.control_root, pins)
        # Acceptance is checked before any provider or GitHub transport exists.
        update.accepted_baseline()
        http = UpdateHTTP(env.get('GH_TOKEN', ''), api_urls(pins, env['GITHUB_RUN_ID']),
            [journal.ORIGIN + path for path, _, _ in public_release.inventory()])
        runtime = Runtime(pins, env, args.control_root, args.build_root, args.baseline_root, GitHubClient(http), http)
        if args.mode not in ('parse-upload', 'readback', 'public'): runtime.metadata()
        if args.mode == 'prepare':
            with Path(env['GITHUB_OUTPUT']).open('a') as stream:
                for role in ('build', 'baseline'):
                    stream.write(role + '_run_id=' + str(pins[role]['runId']) + '\n')
                    stream.write(role + '_artifact_id=' + str(pins[role]['artifactId']) + '\n')
            result = {'state': 'ACTUAL_REVIEWED_METADATA_SELECTED', 'sourceRevision': SOURCE, 'providerMutationsPerformed': False}
        else:
            runtime.artifact()
            if args.mode == 'artifact': result = stage_release(args.build_root, pins, args.control_root)
            else:
                if args.mode not in ('parse-upload', 'readback', 'public'): runtime.stage_exact()
                if args.mode == 'preflight':
                    update.inspect_full_journal(runtime.github.pages()); result = update.preflight()
                    result.update(runId=env['GITHUB_RUN_ID'], controlRevision=env['GITHUB_SHA'])
                elif args.mode == 'claim': result = runtime.claim()
                elif args.mode == 'recheck': result = runtime.recheck()
                elif args.mode == 'parse-upload':
                    update.verify_claim(runtime.review, env)
                    require(args.upload_log == Path(env['RUNNER_TEMP']) / 'damyang-static-update-private.log', 'fixed_private_upload_log_required')
                    result = update.extract_upload_version(args.upload_log, env)
                elif args.mode == 'readback': result = update.readback(runtime.review, env)
                else: result = runtime.public()
        baseline.save(args.report, result)
        print(json.dumps({'state': result['state'], 'sourceRevision': SOURCE, 'searchIndexing': 'not_verified'}))
        return 0
    except Exception as error:
        code = str(error) if isinstance(error, (ValueError, journal.RecoveryBlocked)) and re.fullmatch('[A-Za-z0-9_]+', str(error)) else 'update_blocked_or_outcome_uncertain'
        result = {'state': 'BLOCKED_OR_OUTCOME_UNCERTAIN_NO_AUTOMATIC_REUPLOAD', 'reason': code,
            'mode': args.mode, 'sourceRevision': SOURCE, 'liveBrowserPixelsVerified': False, 'searchIndexing': 'not_verified'}
        baseline.save(args.report, result); print(json.dumps({'state': result['state'], 'reason': code})); return 1


if __name__ == '__main__': sys.exit(main())
