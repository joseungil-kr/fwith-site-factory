#!/usr/bin/env python3
"""Proposed trusted no-deploy caller. Shipped operational seal is deliberately null.

Preparing this program is not permission to execute it. Reviewed real QA/update
bindings and a separately reviewed control seal are prerequisites. No fixtures,
format-valid SHAs, or request body can open the null operational seal.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, build_opener, HTTPRedirectHandler

import indexnow_recovery as guard
import public_release

OWNER = 'joseungil-kr'
SOURCE = public_release.SOURCE
SOURCE_BRANCH = 'source/damyang-dedicated-proof-recovery-20261016'
SOURCE_TREE = '5069d911505b4588d354f71f109cd668c3896237'
SOURCE_ROOT_TREE = '355b93fd183f5fb6a7bcbdf9c56a8f99974583d4'
WORKFLOW = '.github/workflows/damyang-production-publish.yml'
BUILD_WORKFLOW = '.github/workflows/damyang-production-build-only.yml'
TITLE = '[DAMYANG-INDEXNOW-RECOVERY-FINALIZE] 20261016'
CONCURRENCY = 'damyang-direct-public-release'
JOB = 'recovery_finalize_indexnow'
GUARD_SHA256 = '59f23a38bc14925261901d182bd6d503827d16f95bda9368619159a1dd8021f4'
# Intentionally not configurable by issue body, environment, CLI, or JSON.
# Replace only in a separately reviewed future controls revision after the
# complete actual bindings and write/execute lease have been established.
OPERATIONAL_CONTROLS_ENABLED = False
ACTUAL_BUILD = {'artifactBytes': 799100, 'artifactDigest': 'sha256:43b618dc55c0536a16fe8887e6ce4b6a16254b82db7c34657fd23d976824b408', 'artifactId': 12040108398, 'artifactName': 'damyang-proof-recovery-build-38888053867-33ca99b04ae43af120d5799d926f1611b1d59942', 'controlRevision': '33ca99b04ae43af120d5799d926f1611b1d59942', 'runAttempt': 1, 'runId': 38888053867}
ACCEPTED_BUILD_REVIEW = {'commit': 'cd1dd949acc90ad896935d7a5fa11cab0ceb4de6', 'path': 'docs/direct-damyang-recovery/build-artifact-review-38888053867.json', 'sha256': '3a2263b174c32c161716a43cf4451186a1213b862125b7b44c9f8a9032fc5842', 'verdict': 'ACCEPT_SOURCE063E9_BUILD_ARTIFACT_ONLY'}
BUILD_READER_HELPERS = {'scripts/direct-damyang-recovery/recovery_build.py': '5a1c4b9d7ec6ca79caf36688c183935af77694d572bf63201d3a028b2beb5da5', 'scripts/direct-damyang-recovery/recovery_output.py': '559c00b6dbbbe85ef1dbd9a0bef026a75d8fe241839d8392d0cef59c1c52a6fd'}
DOWNLOAD_NAMES = {'build': 'damyang-recovery-build', 'baseline': 'damyang-recovery-baseline', 'update': 'damyang-recovery-update'}
TRUSTED_ENV_KEYS = frozenset(['PATH', 'HOME', 'LANG', 'LC_CTYPE', 'PYTHONDONTWRITEBYTECODE', 'GH_TOKEN', 'GITHUB_REPOSITORY', 'GITHUB_REF', 'GITHUB_ACTOR', 'GITHUB_TRIGGERING_ACTOR', 'GITHUB_RUN_ATTEMPT', 'GITHUB_EVENT_NAME', 'GITHUB_JOB', 'RUNNER_ENVIRONMENT', 'GITHUB_SHA', 'GITHUB_RUN_ID', 'GITHUB_EVENT_PATH', 'GITHUB_OUTPUT', 'GITHUB_WORKSPACE'])
require = guard.require
sha = guard.sha
canonical = guard.canonical


def json_raw(raw):
    def pairs(values):
        out = {}
        for key, value in values:
            require(key not in out, 'duplicate_json_key')
            out[key] = value
        return out
    def constant(_): raise guard.RecoveryBlocked('nonfinite_json')
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except guard.RecoveryBlocked: raise
    except Exception: raise guard.RecoveryBlocked('invalid_json') from None


def read_json(path):
    return json_raw(public_release.read_file(path))


def positive(value): return type(value) is int and value > 0


def approved_pins(path):
    # Deliberately first: even an environment containing credentials is not read
    # by the CLI until this missing independent review has been resolved.
    require(OPERATIONAL_CONTROLS_ENABLED is True, 'operational_review_seal_missing')
    pins = read_json(path)
    review = pins.get('review') if type(pins) is dict else None
    require(type(review) is dict and guard._valid_sha(review.get('sha256'), 64),
            'exact_independent_operational_review_required')
    return pins


def authorize(pins, env, event):
    require(sys.flags.optimize == 0, 'optimized_python_forbidden')
    require(env.get('GITHUB_REPOSITORY') == guard.REPOSITORY
            and env.get('GITHUB_REF') == 'refs/heads/main'
            and env.get('GITHUB_ACTOR') == OWNER and env.get('GITHUB_TRIGGERING_ACTOR') == OWNER
            and env.get('GITHUB_RUN_ATTEMPT') == '1' and env.get('GITHUB_EVENT_NAME') == 'issues'
            and env.get('GITHUB_JOB') == JOB and env.get('RUNNER_ENVIRONMENT') == 'github-hosted',
            'exact_owner_main_first_hosted_job_required')
    require(not any(k.startswith(('CLOUDFLARE_', 'CF_API_', 'CF_ACCOUNT_', 'WRANGLER_')) for k in env),
            'provider_environment_forbidden')
    require(set(env) <= TRUSTED_ENV_KEYS, 'trusted_finalizer_environment_required')
    require(guard._valid_sha(env.get('GITHUB_SHA'), 40)
            and re.fullmatch('[1-9][0-9]*', env.get('GITHUB_RUN_ID', '')) is not None,
            'actual_execution_identity_required')
    repo = event.get('repository', {}); issue = event.get('issue', {})
    require(event.get('action') == 'opened' and repo.get('full_name') == guard.REPOSITORY
            and repo.get('owner', {}).get('login') == OWNER
            and repo.get('owner', {}).get('type') == 'User'
            and event.get('sender', {}).get('login') == OWNER
            and event.get('sender', {}).get('type') == 'User', 'exact_event_identity_required')
    require(issue.get('title') == TITLE and issue.get('user', {}).get('login') == OWNER
            and issue.get('user', {}).get('type') == 'User' and issue.get('state') == 'open'
            and positive(issue.get('number')) and issue['number'] != 377 and 'pull_request' not in issue,
            'exact_recovery_request_issue_required')
    raw = issue.get('body')
    require(type(raw) is str and len(raw.encode()) <= 4096, 'bounded_request_body_required')
    expected = {'schemaVersion': 1, 'mode': 'no-deploy-indexnow-recovery',
                'source_branch': SOURCE_BRANCH, 'source_revision': SOURCE,
                'expected_control_revision': env['GITHUB_SHA'], 'receipt_issue': 377,
                'operational_binding_sha256': sha(canonical(pins).encode())}
    require(guard.exact(json_raw(raw), expected), 'closed_exact_request_required')
    require(pins.get('status') == 'INDEPENDENTLY_REVIEWED_ACTUAL_RECOVERY', 'actual_operational_acceptance_required')
    require(pins.get('sourceRevision') == SOURCE and pins.get('sourceBranch') == SOURCE_BRANCH
            and pins.get('sourceTree') == SOURCE_TREE and pins.get('schemaVersion') == 1,
            'fixed_successor_pins_required')
    for field in ('build', 'baseline', 'update', 'review', 'controlFiles', 'workflowFiles',
                  'artifactFiles', 'releaseFiles', 'releaseManifest'):
        require(type(pins.get(field)) is dict and bool(pins[field]), 'actual_' + field.lower() + '_binding_missing')
    require(guard._valid_sha(pins.get('reviewedControlRevision'), 40)
            and guard._valid_sha(pins.get('releaseManifestSha256'), 64), 'actual_control_manifest_binding_missing')
    for field in ('build', 'baseline', 'update'):
        row = pins[field]
        require(positive(row.get('runId')) and positive(row.get('artifactId'))
                and guard._valid_sha(row.get('controlRevision'), 40)
                and re.fullmatch('sha256:[0-9a-f]{64}', row.get('artifactDigest', '')) is not None
                and type(row.get('artifactName')) is str and row['artifactName'], 'actual_run_artifact_binding_missing')
    require(pins['build']['runId'] not in (guard.CHAIN['originalPublicationRunId'], 38858258621),
            'original_run_cannot_substitute_successor_qa')
    require(guard.exact(pins['build'], ACTUAL_BUILD)
            and guard.exact(pins.get('acceptedBuildReview'), ACCEPTED_BUILD_REVIEW),
            'fixed_actual_build_and_review_binding_required')
    return expected


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None


class BoundedHTTP:
    """No redirect, no retry, fixed destinations, bounded bytes/headers/time.

    The sole token is injected by the reviewed workflow. It is sent only to the
    exact repository GitHub API URLs admitted by GitHubClient, never public URLs.
    """
    def __init__(self, token, api_urls, public_urls, *, opener=None, clock=time.monotonic):
        require(type(token) is str and bool(token) and '\r' not in token and '\n' not in token,
                'workflow_github_token_required')
        self._token = token
        self.api_urls = frozenset(api_urls); self.public_urls = frozenset(public_urls)
        self.opener = opener if opener is not None else build_opener(NoRedirect())
        self.clock = clock; self.post_reserved = False

    def call(self, method, url, payload=None):
        comment_page = re.fullmatch(
            re.escape(guard.API_BASE) + r'/issues/comments\?per_page=100&page=([1-9][0-9]{0,4})', url)
        api = url in self.api_urls or (comment_page is not None and int(comment_page[1]) <= guard.MAX_PAGES)
        comment_write = url == guard.ISSUE_URL + '/comments'
        require((method == 'GET' and payload is None and (api or url in self.public_urls))
                or (method == 'POST' and type(payload) is bytes and len(payload) <= 65536
                    and (comment_write or url == guard.ENDPOINT)), 'fixed_http_scope_required')
        if method == 'POST' and url == guard.ENDPOINT:
            require(not self.post_reserved, 'caller_single_post_only')
            self.post_reserved = True
        headers = {'User-Agent': 'Damyang-Reviewed-Recovery/1.0', 'Accept-Encoding': 'identity',
                   'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        if api or comment_write:
            headers.update({'Authorization': 'Bearer ' + self._token,
                            'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
        if method == 'POST': headers['Content-Type'] = 'application/json; charset=utf-8'
        req = Request(url, method=method, data=payload, headers=headers)
        start = self.clock()
        try:
            response = self.opener.open(req, timeout=20)
        except HTTPError as error:
            response = error
        except Exception:
            raise guard.RecoveryBlocked('http_outcome_unconfirmed') from None
        try:
            with response:
                require(response.geturl() == url, 'unexpected_response_url')
                require(type(response.code) is int and not 300 <= response.code < 400, 'redirect_forbidden')
                pairs = list(response.headers.items())
                require(len(pairs) <= 100 and all(len(k) <= 128 and len(v) <= 4096 for k, v in pairs),
                        'http_header_limit')
                lengths = [v for k, v in pairs if k.lower() == 'content-length']
                require(len(lengths) <= 1 and (not lengths or (lengths[0].isdigit()
                        and int(lengths[0]) <= guard.MAX_RESPONSE)), 'http_length_limit')
                encodings = [v for k, v in pairs if k.lower() == 'content-encoding']
                require(len(encodings) <= 1 and (not encodings or encodings[0].lower() == 'identity'),
                        'compressed_response_forbidden')
                body = bytearray()
                reader = getattr(response, 'read1', response.read)
                while True:
                    require(self.clock() - start <= 60, 'http_deadline_exceeded')
                    part = reader(min(65536, guard.MAX_RESPONSE + 1 - len(body)))
                    if not part: break
                    body.extend(part)
                    require(len(body) <= guard.MAX_RESPONSE, 'http_body_limit')
                require(not lengths or len(body) == int(lengths[0]), 'truncated_http_body')
                return guard.RawResponse(response.code, bytes(body), pairs)
        except guard.RecoveryBlocked: raise
        except Exception:
            raise guard.RecoveryBlocked('http_outcome_unconfirmed') from None


def api_urls(pins, run_id):
    urls = {guard.API_BASE + '/git/ref/heads/main',
        guard.API_BASE + '/git/ref/heads/' + SOURCE_BRANCH,
        guard.API_BASE + '/git/commits/' + SOURCE,
        guard.API_BASE + '/git/trees/' + SOURCE_TREE + '?recursive=1', guard.ISSUE_URL,
        guard.API_BASE + '/actions/runs/' + str(run_id)}
    for field in ('build', 'baseline', 'update'):
        row = pins[field]
        urls.add(guard.API_BASE + '/actions/runs/' + str(row['runId']))
        urls.add(guard.API_BASE + '/actions/artifacts/' + str(row['artifactId']))
    return urls


class GitHubClient:
    def __init__(self, http): self.http = http

    def get(self, url):
        response = self.http.call('GET', url)
        require(response.status == 200, 'github_get_not_http200')
        ctypes = [v for k, v in response.headers if k.lower() == 'content-type']
        require(len(ctypes) == 1 and ctypes[0].lower().startswith('application/json'), 'github_json_content_type_required')
        return json_raw(response.body), response

    def read_page(self, number):
        require(type(number) is int and 1 <= number <= guard.MAX_PAGES, 'journal_page_number_invalid')
        url = guard.page_url(number); comments, response = self.get(url)
        require(type(comments) is list and len(comments) <= 100, 'github_full_comment_page_required')
        links = [v for k, v in response.headers if k.lower() == 'link']
        require(len(links) <= 1, 'ambiguous_github_link_header')
        next_url = None; rels = set()
        if links:
            require(len(links[0]) <= 4096, 'github_link_header_limit')
            for link in links[0].split(','):
                match = re.fullmatch(r'\s*<([^<>]+)>;\s*rel="(next|prev|first|last)"\s*', link)
                require(match is not None, 'unrecognized_github_pagination')
                dest, rel = match.groups()
                require(rel not in rels, 'duplicate_github_pagination_relation'); rels.add(rel)
                page_match = re.fullmatch(re.escape(guard.API_BASE) + r'/issues/comments\?per_page=100&page=([1-9][0-9]*)', dest)
                require(page_match is not None and int(page_match[1]) <= guard.MAX_PAGES,
                        'foreign_or_noncanonical_github_pagination')
                if rel == 'next':
                    require(dest == guard.page_url(number + 1), 'github_next_page_mismatch'); next_url = dest
                if rel == 'prev': require(number > 1 and dest == guard.page_url(number - 1), 'github_prev_page_mismatch')
                if rel == 'first': require(dest == guard.page_url(1), 'github_first_page_mismatch')
        return guard.AuditPage(url, response.status, comments, next_url, True)

    def write_record(self, record):
        payload = json.dumps({'body': guard.MARKER + json.dumps(record, ensure_ascii=False, sort_keys=True)}).encode()
        response = self.http.call('POST', guard.ISSUE_URL + '/comments', payload)
        require(response.status == 201, 'journal_comment_creation_unconfirmed')
        value = json_raw(response.body)
        guard._trusted_comment(value)
        return value


def verify_run(row, data, path, *, current=False):
    require(type(data) is dict and data.get('id') == row['runId'] and type(data.get('id')) is int
            and type(data.get('run_attempt')) is int and data.get('run_attempt') == 1 and data.get('event') == 'issues'
            and data.get('head_branch') == 'main' and data.get('head_sha') == row['controlRevision']
            and data.get('path') == path and data.get('repository', {}).get('full_name') == guard.REPOSITORY
            and data.get('actor', {}).get('login') == OWNER and data.get('triggering_actor', {}).get('login') == OWNER,
            'actual_workflow_run_identity_mismatch')
    require((data.get('status') == 'in_progress' and data.get('conclusion') is None) if current else
            (data.get('status') == 'completed' and data.get('conclusion') == 'success'),
            'workflow_run_not_successful_or_current')


def verify_artifact_meta(row, data):
    require(type(data) is dict and data.get('id') == row['artifactId'] and type(data.get('id')) is int
            and data.get('expired') is False and data.get('name') == row['artifactName']
            and data.get('digest') == row['artifactDigest'] and positive(data.get('size_in_bytes'))
            and positive(row.get('artifactBytes')) and data['size_in_bytes'] == row['artifactBytes']
            and data['size_in_bytes'] <= 32 * 1024 * 1024
            and type(data.get('workflow_run', {}).get('id')) is int
            and data.get('workflow_run', {}).get('id') == row['runId']
            and data.get('workflow_run', {}).get('head_sha') == row['controlRevision']
            and data.get('workflow_run', {}).get('head_branch') == 'main',
            'actual_artifact_metadata_mismatch')


def verify_download_roots(workspace, roots, *, preparing):
    """Fixed fresh Actions roots, not a staging package or receipt protocol.

    Uses the trusted hosted runner's exclusively controlled workspace. This is
    not a general defense against an arbitrary hostile same-UID process.
    """
    require(type(workspace) is str and workspace and Path(workspace).is_absolute()
            and type(preparing) is bool and set(roots) == set(DOWNLOAD_NAMES),
            'fixed_download_workspace_required')
    base = Path(workspace)
    require(all(part not in ('.', '..') for part in base.parts)
            and base.is_dir() and not any(p.is_symlink() for p in (base, *base.parents)),
            'symlink_free_download_workspace_required')
    for role, name in DOWNLOAD_NAMES.items():
        supplied = Path(roots[role])
        require(all(part not in ('.', '..') for part in supplied.parts), 'fixed_download_root_required')
        actual = supplied.absolute(); expected = base / name
        require(actual == expected and not any(p.is_symlink() for p in (actual, *actual.parents)),
                'fixed_symlink_free_download_root_required')
        if preparing:
            require(not actual.exists(), 'fresh_download_root_required')
        else:
            require(actual.is_dir(), 'downloaded_fixed_directory_required')
    return True


def validate_actual_build_review(root, pins, control_root):
    """Reuse the already reviewed phase1 pure comparison on exact Actions bytes.

    archiveSha256 below is the pinned, fresh-API-checked digest. This path does
    not retrieve or hash a fresh ZIP and does not execute site/artifact code.
    """
    require(guard.exact(pins.get('build'), ACTUAL_BUILD)
            and guard.exact(pins.get('acceptedBuildReview'), ACCEPTED_BUILD_REVIEW),
            'fixed_actual_build_and_review_binding_required')
    # Reused code and its imported output module are verified before import.
    for name, expected in BUILD_READER_HELPERS.items():
        require(sha(public_release.read_file(Path(control_root) / name)) == expected,
                'immutable_build_reader_helper_required')
    import recovery_build as build
    review = public_release.read_file(Path(control_root) / ACCEPTED_BUILD_REVIEW['path'])
    release = Path(root) / 'release-recovery'
    identity = {'artifactId': ACTUAL_BUILD['artifactId'],
                'archiveSha256': ACTUAL_BUILD['artifactDigest'][7:]}
    return build.verify_independent_review(review, ACCEPTED_BUILD_REVIEW['sha256'],
        read_json(release / 'release.json'), identity,
        read_json(release / 'output-verification.json'), release / 'dist')


def checked_version_coverage(active):
    """Only the reviewed consumed scope; no blanket code/resources assertion."""
    require(type(active) is dict and 'versionResourcesKnownShape' not in active,
            'exact_version_resource_coverage_required')
    runtime = active.get('versionRuntime')
    require(type(runtime) is dict and type(runtime.get('fields')) is dict,
            'exact_version_runtime_projection_required')
    has_assets = 'assetsPreservation' in runtime['fields']
    expected = {'resourceContainerAndBindingsChecked': True,
        'knownRuntimeCapabilityGuardsChecked': True, 'legacyAssetsInternalsInspected': False,
        'selectedAssetsConfigCompared': has_assets, 'workerCodeInspected': False}
    require(guard.exact(active.get('versionResourceCoverage'), expected),
            'exact_version_resource_coverage_required')
    if has_assets:
        projection = runtime['fields']['assetsPreservation']
        require(type(projection) is dict
                and projection.get('schema') == 'damyang-selected-version-assets-preservation/v1',
                'fixed_damyang_assets_projection_required')
    return True


def validate_source(github, source_manifest):
    branch, _ = github.get(guard.API_BASE + '/git/ref/heads/' + SOURCE_BRANCH)
    require(branch.get('ref') == 'refs/heads/' + SOURCE_BRANCH
            and branch.get('object') == {'type': 'commit', 'sha': SOURCE,
                'url': guard.API_BASE + '/git/commits/' + SOURCE}, 'source_branch_moved_or_invalid')
    commit, _ = github.get(guard.API_BASE + '/git/commits/' + SOURCE)
    require(commit.get('sha') == SOURCE and commit.get('tree', {}).get('sha') == SOURCE_ROOT_TREE
            and [p.get('sha') for p in commit.get('parents', [])] == [guard.CHAIN['originalSourceRevision']],
            'actual_successor_commit_mismatch')
    tree, _ = github.get(guard.API_BASE + '/git/trees/' + SOURCE_TREE + '?recursive=1')
    require(tree.get('sha') == SOURCE_TREE and tree.get('truncated') is False
            and type(tree.get('tree')) is list, 'full_successor_tree_required')
    files = {}; seen = set()
    for row in tree['tree']:
        name = row.get('path'); require(type(name) is str and name not in seen, 'duplicate_source_tree_path'); seen.add(name)
        if row.get('type') == 'tree': require(row.get('mode') == '040000', 'source_tree_mode_mismatch'); continue
        require(row.get('type') == 'blob' and row.get('mode') == '100644', 'source_nonregular_file_forbidden')
        files[name] = {'sha': row.get('sha'), 'size': row.get('size')}
    require(len(source_manifest) == 81 and files == {k: {'sha': v['gitBlobSHA1'], 'size': v['bytes']}
            for k, v in source_manifest.items()}, 'exact_saved_81_source_files_required')


def verify_local_control(control_root, pins):
    root = Path(control_root)
    for name, expected in pins['controlFiles'].items():
        require(type(name) is str and re.fullmatch(r'[A-Za-z0-9_./-]+', name) is not None
                and not name.startswith('/') and '..' not in name.split('/'), 'unsafe_control_file_path')
        require(sha(public_release.read_file(root / name)) == expected, 'reviewed_control_file_mismatch')
    required = {'scripts/direct-damyang-recovery/finalize_recovery.py',
                'scripts/direct-damyang-recovery/public_release.py',
                'scripts/direct-damyang-recovery/indexnow_recovery.py',
                'scripts/direct-damyang-recovery/managed_robots.py',
                'scripts/direct-damyang-recovery/beacon_normalization.py',
                'site-factory/engine/indexnow_finalize.py', WORKFLOW,
                'docs/direct-damyang-recovery/source-files.json',
                'scripts/direct-damyang-recovery/contract-source/release-adapter/scripts/damyang_release_output.py',
                'scripts/direct-damyang-recovery/contract-source/release-adapter/release/damyang-indexnow-proof.txt',
                'scripts/direct-damyang-recovery/contract-source/release-adapter/release/existing-indexnow-proof.txt'}
    required.update(BUILD_READER_HELPERS)
    require(required.issubset(pins['controlFiles']), 'complete_reviewed_control_inventory_required')
    require(all(pins['controlFiles'][name] == expected for name, expected in BUILD_READER_HELPERS.items()),
            'immutable_build_reader_helper_pin_required')
    require(pins['controlFiles']['scripts/direct-damyang-recovery/indexnow_recovery.py'] == GUARD_SHA256
            and pins['controlFiles']['site-factory/engine/indexnow_finalize.py'] == guard.HELPER_SHA256,
            'immutable_guard_and_helper_required')
    workflows = {p.relative_to(root).as_posix(): sha(public_release.read_file(p))
                 for p in (root / '.github/workflows').iterdir() if p.suffix in ('.yml', '.yaml')}
    require(workflows == pins['workflowFiles'], 'reviewed_all_workflow_inventory_changed')
    raw = public_release.read_file(root / WORKFLOW).decode('utf-8')
    require(raw.count('\nconcurrency:\n  group: ' + CONCURRENCY + '\n  cancel-in-progress: false\n') == 1,
            'shared_top_level_concurrency_required')
    require(raw.count('\n  ' + JOB + ':\n') == 1, 'exact_no_deploy_job_required')
    job = raw.split('\n  ' + JOB + ':\n')[1]
    require(not re.search(r'\n  [A-Za-z0-9_-]+:\n', job), 'finalizer_job_must_be_last_for_review')
    require(not re.search(r'(CLOUDFLARE_|\bnpx\b|\bnpm\b|setup-node|wrangler|\bnode\s|\bdeploy\s|\battach\s)', job),
            'provider_or_source_execution_in_finalizer_job')
    return True


def validate_retained_artifact(root, pins):
    root = Path(root)
    require(public_release.file_inventory(root) == pins['artifactFiles'], 'complete_retained_artifact_bytes_mismatch')
    release = root / 'release-recovery'; manifest = public_release.read_file(release / 'release.json')
    require(sha(manifest) == pins['releaseManifestSha256']
            and guard.exact(json_raw(manifest), pins['releaseManifest']), 'exact_release_manifest_required')
    expected = pins['releaseManifest']
    require(expected.get('sourceRevision') == SOURCE and expected.get('sourceBranch') == SOURCE_BRANCH
            and expected.get('sourceTree') == SOURCE_TREE and expected.get('runAttempt') == 1
            and expected.get('publicationReady') is False
            and expected.get('artifactName') == pins['build']['artifactName']
            and expected.get('sourceRoot') == 'site-factory/damyang-flower'
            and expected.get('repository') == guard.REPOSITORY
            and expected.get('mode') == 'damyang-proof-recovery-build-only'
            and expected.get('independentArtifactReviewRequired') is True
            and guard._valid_sha(expected.get('bindingSha256'), 64)
            and type(expected.get('sourceContract')) is dict
            and expected.get('runId') == str(pins['build']['runId'])
            and expected.get('controlRevision') == pins['build']['controlRevision']
            and expected.get('files') == pins['releaseFiles'], 'actual_release_manifest_binding_mismatch')
    source_contract = expected['sourceContract']
    require(source_contract.get('sourceRevision') == SOURCE and source_contract.get('sourceTree') == SOURCE_TREE
            and source_contract.get('sourceBranch') == SOURCE_BRANCH
            and source_contract.get('sourceRoot') == 'site-factory/damyang-flower'
            and source_contract.get('repository') == guard.REPOSITORY
            and source_contract.get('sourceFiles') == 81 and source_contract.get('privateFiles') == 65
            and source_contract.get('adapterFiles') == 16
            and guard._valid_sha(source_contract.get('sourceManifestSha256'), 64)
            and guard._valid_sha(source_contract.get('boundedContractSha256'), 64), 'exact_artifact_source_contract_required')
    public_release.verify_release(release / 'dist', pins['releaseFiles'], SOURCE)
    output = read_json(release / 'output-verification.json')
    require(output.get('sourceRevision') == SOURCE and output.get('sourceTree') == SOURCE_TREE
            and output.get('files') == pins['releaseFiles'] and output.get('originalNonHTMLExact') == 14
            and output.get('originalHTMLRevisionOnly') == 2 and output.get('inheritedBodyByteEquality') == 2
            and output.get('newLiveBrowserObserved') is False and output.get('publicationReady') is False
            and output.get('actualPublicHTTPRequests') == 0, 'exact_new_source_output_evidence_required')
    expected_http = [{'file': name, 'path': path, 'expectedStatus': status, 'sha256': pins['releaseFiles'][name]}
                     for path, name, status in public_release.inventory()]
    require(sorted(output.get('httpPlan', []), key=lambda x: x['file']) == sorted(expected_http, key=lambda x: x['file']),
            'exact_new_source_public_16_plan_required')
    payload = {'host': 'damyang.fwith.kr', 'key': public_release.ACTIVE[:-4],
               'keyLocation': guard.ORIGIN + '/' + public_release.ACTIVE, 'urlList': [guard.HOME]}
    require(output.get('activeOnlyPayloadSha256') == guard.digest(payload), 'active_only_output_payload_required')
    return release


def validate_update_evidence(baseline_root, update_root, pins):
    """Rehash actual artifacts and cross-check reports without upgrading claims.

    The baseline observation is explicitly not acceptance. The update provider
    readback explicitly has publicHTTPVerified=False; the separate 16-URL report
    establishes public byte checks. No provider call is made by this reader.
    """
    for role, root in (('baseline', baseline_root), ('update', update_root)):
        row = pins[role]
        require(type(row.get('files')) is dict and row['files']
                and public_release.file_inventory(root) == row['files'], 'exact_' + role + '_artifact_required')
    def report(role, root, key):
        row = pins[role]; entry = row.get('reports', {}).get(key)
        require(type(entry) is dict and set(entry) == {'path', 'sha256', 'reviewedReport'}
                and entry['path'] in row['files'] and row['files'][entry['path']] == entry['sha256'],
                'exact_pinned_evidence_report_required')
        value = read_json(Path(root) / entry['path'])
        require(guard.exact(value, entry['reviewedReport']), 'independently_reviewed_actual_report_required')
        return value
    baseline = report('baseline', baseline_root, 'observation')
    require(baseline.get('schema') == 'damyang-recovery-current-provider-baseline-observation/v1'
            and baseline.get('state') == 'OBSERVED_NOT_ACCEPTED_FOR_MUTATION'
            and baseline.get('previousSourceRevision') == guard.CHAIN['originalSourceRevision']
            and baseline.get('correctionSourceRevision') == SOURCE
            and baseline.get('previousPublicationRunId') == 38861200090
            and baseline.get('baselineAccepted') is False and baseline.get('publicationEligible') is False
            and baseline.get('historicalProviderVersionKnown') is False
            and baseline.get('providerMethods') == ['GET'] and baseline.get('providerMutationsPerformed') is False
            and baseline.get('IndexNowSubmitted') is False, 'actual_baseline_scope_required')
    identity = baseline.get('identity', {})
    require(identity.get('repository') == guard.REPOSITORY
            and identity.get('runId') == str(pins['baseline']['runId'])
            and identity.get('controlRevision') == pins['baseline']['controlRevision']
            and identity.get('runAttempt') == 1, 'baseline_actual_run_binding_required')
    old_public = baseline.get('previousPublicHTTP', {})
    require(old_public.get('state') == 'public_release_verified'
            and old_public.get('revision') == guard.CHAIN['originalSourceRevision']
            and old_public.get('checkedPaths') == 15 and old_public.get('unknownHttpStatus') == 404,
            'baseline_old_public_15_required')
    before = report('update', update_root, 'providerBefore')
    after = report('update', update_root, 'providerAfter')
    require(guard.exact(before, baseline.get('currentProviderState'))
            and guard.digest(before) == baseline.get('currentProviderStateSHA256'),
            'update_current_baseline_binding_required')
    require(guard.exact({k:v for k,v in before.items() if k != 'activeDeployment'},
                        {k:v for k,v in after.items() if k != 'activeDeployment'}),
            'provider_settings_binding_or_exposure_changed')
    account_sha = 'd5bbfc5383872f2c9e36138452e0c880f46b03bbd4aaffa278490c2ad6d7bcbf'
    for state in (before, after):
        require(state.get('accountSHA256') == account_sha and state.get('hostname') == 'damyang.fwith.kr'
                and state.get('worker') == 'damyang-flower-guide'
                and guard.exact(state.get('workersDev'), {'enabled': False, 'previews_enabled': False})
                and guard.exact(state.get('settings'), {'bindings': [], 'compatibility_date': '2026-10-09',
                    'compatibility_flags': [], 'logpush': False, 'placement': {}, 'tags': [],
                    'tail_consumers': [], 'usage_model': 'standard'})
                and state.get('hostnameBinding', {}).get('hostname') == 'damyang.fwith.kr'
                and state.get('hostnameBinding', {}).get('worker') == 'damyang-flower-guide'
                and state.get('hostnameBinding', {}).get('zoneName') == 'fwith.kr'
                and guard._valid_sha(state.get('hostnameBinding', {}).get('domainIdSHA256'), 64)
                and guard._valid_sha(state.get('hostnameBinding', {}).get('zoneIdSHA256'), 64)
                and state.get('activeDeployment', {}).get('trafficPercentage') == 100
                and checked_version_coverage(state.get('activeDeployment')),
                'actual_fixed_single_version_state_required')
    old = before['activeDeployment']; new = after['activeDeployment']
    require(all(guard._valid_sha(new.get(k), 64) and guard._valid_sha(old.get(k), 64)
                and new[k] != old[k] for k in ('versionIdSHA256', 'deploymentIdSHA256'))
            and guard.exact(new.get('versionRuntime'), old.get('versionRuntime'))
            and guard.exact(new.get('versionScript'), old.get('versionScript')),
            'actual_new_static_version_required')
    provider = report('update', update_root, 'providerReadback')
    expected_provider = {'state': 'EXACT_NEW_VERSION_AND_UNCHANGED_BINDING_VERIFIED',
        'sourceRevision': SOURCE, 'previousSourceRevision': guard.CHAIN['originalSourceRevision'],
        'accountSHA256': account_sha, 'hostname': 'damyang.fwith.kr', 'worker': 'damyang-flower-guide',
        'currentProviderStateSHA256': guard.digest(after), 'deploymentIdSHA256': new['deploymentIdSHA256'],
        'versionIdSHA256': new['versionIdSHA256'], 'providerMethods': ['GET'],
        'providerMutationsPerformed': False, 'hostnameAttached': False, 'publicHTTPVerified': False}
    require(guard.exact(provider, expected_provider), 'exact_provider_readback_scope_required')
    public = report('update', update_root, 'publicRelease')
    require(public.get('state') == 'current_full_successor_public_verified'
            and public.get('revision') == SOURCE and public.get('checkedPaths') == 16
            and public.get('status200') == 15 and public.get('status404') == 1
            and public.get('liveBrowserPixelsVerified') is False, 'separate_actual_public_16_report_required')
    checks = public.get('checks')
    require(type(checks) is list and len(checks) == 16, 'exact_public_evidence_rows_required')
    expected = {(path, name, status) for path, name, status in public_release.inventory()}
    require({(r.get('path'), r.get('file'), r.get('httpStatus')) for r in checks} == expected,
            'public_evidence_inventory_mismatch')
    require(all(r.get('artifactSha256') == pins['releaseFiles'][r['file']]
                and guard._valid_sha(r.get('rawBodySha256'), 64) and positive(r.get('rawBodyBytes'))
                and r.get('normalization') in ('none', 'exact_existing_single_beacon',
                                              'exact_existing_managed_robots_prefix') for r in checks),
            'public_evidence_artifact_binding_mismatch')
    for item in checks:
        mode = item['normalization']
        require((mode == 'none' and item['rawBodySha256'] == item['artifactSha256'])
                or (mode == 'exact_existing_single_beacon' and item['file'] in ('index.html', '404.html'))
                or (mode == 'exact_existing_managed_robots_prefix' and item['file'] == 'robots.txt'),
                'public_evidence_normalization_scope_mismatch')
    claim = report('update', update_root, 'deploymentClaim')
    require(claim.get('schema') == 'damyang-proof-recovery-deployment-attempt/v1'
            and claim.get('state') == 'STARTED_NO_AUTOMATIC_REUPLOAD'
            and claim.get('repository') == guard.REPOSITORY and claim.get('hostname') == 'damyang.fwith.kr'
            and claim.get('sourceRevision') == SOURCE
            and claim.get('previousSourceRevision') == guard.CHAIN['originalSourceRevision']
            and claim.get('runId') == str(pins['update']['runId'])
            and claim.get('controlRevision') == pins['update']['controlRevision']
            and claim.get('runAttempt') == 1 and positive(claim.get('commentId'))
            and claim.get('buildRunId') == pins['build']['runId']
            and claim.get('artifactId') == pins['build']['artifactId']
            and claim.get('artifactDigest') == pins['build']['artifactDigest']
            and claim.get('providerStateSHA256') == guard.digest(before)
            and claim.get('outputFilesSha256') == guard.digest(pins['releaseFiles'])
            and claim.get('releaseManifestSha256') == pins['releaseManifestSha256'],
            'actual_update_claim_artifact_chain_required')
    acceptance = pins['baseline'].get('independentAcceptance')
    require(type(acceptance) is dict and acceptance.get('verdict') ==
            'ACCEPT_CURRENT_GET_ONLY_BASELINE_FOR_DAMYANG_PROOF_RECOVERY'
            and acceptance.get('observationArtifactId') == pins['baseline']['artifactId']
            and acceptance.get('observationArtifactDigest') == pins['baseline']['artifactDigest']
            and acceptance.get('currentProviderStateSHA256') == guard.digest(before)
            and acceptance.get('observationSHA256') == pins['baseline']['reports']['observation']['sha256']
            and acceptance.get('actualLiveGETVerified') is True
            and acceptance.get('priorPublic15Verified') is True
            and acceptance.get('singleVersion100Verified') is True
            and acceptance.get('settingsAndBindingReviewed') is True
            and acceptance.get('publicationApproved') is False, 'independent_baseline_acceptance_required')


class Runtime:
    def __init__(self, *, pins, env, control_root, artifact_root, baseline_root, update_root, github, http):
        self.pins = pins; self.env = env; self.control_root = Path(control_root)
        self.artifact_root = Path(artifact_root); self.baseline_root = Path(baseline_root); self.update_root = Path(update_root)
        self.github = github; self.http = http; self.public_observations = []; self.adapter = None
        self.binding = guard.Binding(SOURCE, env['GITHUB_SHA'], pins['build']['artifactDigest'][7:],
            'https://github.com/' + guard.REPOSITORY + '/actions/runs/' + env['GITHUB_RUN_ID'])

    def serialized(self):
        verify_local_control(self.control_root, self.pins)
        main, _ = self.github.get(guard.API_BASE + '/git/ref/heads/main')
        require(main.get('object', {}).get('type') == 'commit'
                and main.get('object', {}).get('sha') == self.env['GITHUB_SHA'], 'main_moved_since_exact_request')
        run, _ = self.github.get(guard.API_BASE + '/actions/runs/' + self.env['GITHUB_RUN_ID'])
        verify_run({'runId': int(self.env['GITHUB_RUN_ID']), 'controlRevision': self.env['GITHUB_SHA']}, run, WORKFLOW, current=True)
        # GitHub owns the repository-scoped workflow concurrency lease. The
        # complete reviewed workflow inventory, current main, exact current run,
        # hosted runner and job check bind this callback to that configured lock.
        return True

    def validate_binding(self, binding):
        require(binding == self.binding, 'runtime_binding_changed')
        source_file = self.control_root / 'docs/direct-damyang-recovery/source-files.json'
        validate_source(self.github, read_json(source_file))
        for field, path in (('build', BUILD_WORKFLOW), ('baseline', WORKFLOW), ('update', WORKFLOW)):
            row = self.pins[field]
            data, _ = self.github.get(guard.API_BASE + '/actions/runs/' + str(row['runId']))
            verify_run(row, data, path)
            meta, _ = self.github.get(guard.API_BASE + '/actions/artifacts/' + str(row['artifactId']))
            verify_artifact_meta(row, meta)
        journal, _ = self.github.get(guard.ISSUE_URL)
        require(journal.get('number') == 377 and journal.get('state') == 'open'
                and journal.get('title') == '[DAMYANG-INDEXNOW-RECEIPTS] 20261016'
                and journal.get('user', {}).get('login') == OWNER and 'pull_request' not in journal
                and journal.get('repository_url') == guard.API_BASE, 'original_receipt_issue_required')
        validate_retained_artifact(self.artifact_root, self.pins)
        validate_actual_build_review(self.artifact_root, self.pins, self.control_root)
        validate_update_evidence(self.baseline_root, self.update_root, self.pins)
        review = self.pins['review']; name = review.get('path')
        require(type(name) is str and name.startswith('docs/direct-damyang-recovery/')
                and '..' not in name.split('/'), 'review_path_invalid')
        raw = public_release.read_file(self.control_root / name)
        require(sha(raw) == review.get('sha256'), 'independent_operational_review_digest_mismatch')
        reviewed = json_raw(raw)
        require(reviewed.get('verdict') == 'APPROVED_ACTUAL_DAMYANG_NO_DEPLOY_RECOVERY'
                and reviewed.get('sourceRevision') == SOURCE
                and reviewed.get('reviewedControlRevision') == self.pins['reviewedControlRevision']
                and reviewed.get('allHostPublishersUseSharedConcurrency') is True
                and reviewed.get('workflowInventorySha256') == guard.digest(self.pins['workflowFiles'])
                and reviewed.get('controlFilesSha256') == guard.digest(self.pins['controlFiles'])
                and reviewed.get('buildBindingSha256') == guard.digest(self.pins['build'])
                and reviewed.get('baselineBindingSha256') == guard.digest(self.pins['baseline'])
                and reviewed.get('updateBindingSha256') == guard.digest(self.pins['update'])
                and reviewed.get('artifactFilesSha256') == guard.digest(self.pins['artifactFiles'])
                and reviewed.get('releaseFilesSha256') == guard.digest(self.pins['releaseFiles'])
                and reviewed.get('oldPixelScope') == 'unchanged-html-bodies-css-images-only'
                and reviewed.get('freshLiveBrowserPixelsClaimed') is False, 'complete_independent_actual_review_required')
        return True

    def validate_public(self, binding):
        require(binding == self.binding, 'runtime_binding_changed')
        evidence = public_release.verify_public_release(self.artifact_root / 'release-recovery/dist', self.pins['releaseFiles'], SOURCE,
            lambda url: self.http.call('GET', url))
        self.public_observations.append(evidence)
        return True

    def transport(self, method, url, payload=None):
        response = self.http.call(method, url, payload)
        if method == 'GET':
            selected = [(path, name, status) for path, name, status in public_release.inventory()
                        if guard.ORIGIN + path == url]
            require(len(selected) == 1, 'fixed_helper_probe_required')
            public_release.verify_public_response(*selected[0], response, self.pins['releaseFiles'], SOURCE)
        return response

    def run(self):
        require(OPERATIONAL_CONTROLS_ENABLED is True, 'operational_review_seal_missing')
        # Contract files are immutable reviewed literal data; no source checkout
        # or source code execution occurs. load_contract only parses AST literals.
        contract = guard.load_contract(self.control_root / 'scripts/direct-damyang-recovery/contract-source')
        adapter = guard.RecoveryAdapter(contract=contract, binding=self.binding,
            helper_path=self.control_root / 'site-factory/engine/indexnow_finalize.py',
            read_page=self.github.read_page, write_record=self.github.write_record,
            transport=self.transport, validate_binding=self.validate_binding,
            assert_serialized=self.serialized, validate_full_public_release=self.validate_public)
        self.adapter = adapter
        site = {'siteKey': guard.SITE_KEY, 'siteUrl': guard.ORIGIN, 'indexnowKey': contract.active_key,
                'productionEnabled': True, 'launchMode': 'live'}
        return adapter.run(self.artifact_root / 'release-recovery', site)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'finalize'])
    parser.add_argument('--control-root', type=Path, default=Path('control'))
    parser.add_argument('--artifact-root', type=Path, default=Path('damyang-recovery-build'))
    parser.add_argument('--baseline-root', type=Path, default=Path('damyang-recovery-baseline'))
    parser.add_argument('--update-root', type=Path, default=Path('damyang-recovery-update'))
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args(); runtime = None
    try:
        pins_path = args.control_root / 'docs/direct-damyang-recovery/finalizer-binding.json'
        pins = approved_pins(pins_path)
        env = dict(os.environ); event = read_json(env.get('GITHUB_EVENT_PATH', ''))
        authorize(pins, env, event)
        verify_download_roots(env.get('GITHUB_WORKSPACE'),
            {'build': args.artifact_root, 'baseline': args.baseline_root, 'update': args.update_root},
            preparing=args.mode == 'prepare')
        token = env.get('GH_TOKEN', '')
        http = BoundedHTTP(token, api_urls(pins, env['GITHUB_RUN_ID']),
            [guard.ORIGIN + path for path, _, _ in public_release.inventory()])
        github = GitHubClient(http)
        runtime = Runtime(pins=pins, env=env, control_root=args.control_root,
            artifact_root=args.artifact_root, baseline_root=args.baseline_root,
            update_root=args.update_root, github=github, http=http)
        if args.mode == 'prepare':
            runtime.serialized()
            validate_source(github, read_json(args.control_root / 'docs/direct-damyang-recovery/source-files.json'))
            for role, path in (('build', BUILD_WORKFLOW), ('baseline', WORKFLOW), ('update', WORKFLOW)):
                row = pins[role]; run, _ = github.get(guard.API_BASE + '/actions/runs/' + str(row['runId']))
                verify_run(row, run, path)
                art, _ = github.get(guard.API_BASE + '/actions/artifacts/' + str(row['artifactId']))
                verify_artifact_meta(row, art)
            out = Path(env['GITHUB_OUTPUT'])
            with out.open('a') as stream:
                for role in ('build', 'baseline', 'update'):
                    stream.write(role + '_run_id=' + str(pins[role]['runId']) + '\n')
                    stream.write(role + '_artifact_id=' + str(pins[role]['artifactId']) + '\n')
            result = {'state': 'actual_artifact_metadata_selected', 'mutationsPerformed': False}
        else:
            result = runtime.run()
        args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
        if runtime.public_observations:
            args.report.with_name('finalizer-public-http.json').write_text(json.dumps(runtime.public_observations, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'state': result['state'], 'searchIndexing': 'not_verified'}))
        return 0
    except Exception as error:
        code = str(error) if isinstance(error, guard.RecoveryBlocked) and re.fullmatch('[a-zA-Z0-9_]+', str(error)) else 'finalizer_blocked_or_outcome_uncertain'
        result = {'state': 'blocked_or_outcome_uncertain', 'reason': code,
                  'searchIndexing': 'not_verified', 'liveBrowserPixelsVerified': False}
        if runtime is not None and runtime.adapter is not None:
            adapter = runtime.adapter
            result['executionObservation'] = {'postReservations': adapter.post_calls,
                'startedWriteReservations': adapter.start_writes,
                'durableStartedCommentId': adapter.started[0] if adapter.started else None,
                'responseDiagnostics': adapter.last_diagnostics,
                'retryAllowed': False}
            # A reservation does not prove the remote POST arrived. Retain that
            # uncertainty; never write raw bodies, secrets, or exception text.
        args.report.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
        if runtime is not None and runtime.public_observations:
            args.report.with_name('finalizer-public-http.json').write_text(json.dumps(runtime.public_observations, indent=2, sort_keys=True) + '\n')
        print(json.dumps(result, sort_keys=True)); return 1


if __name__ == '__main__': raise SystemExit(main())
