#!/usr/bin/env python3
"""Trusted no-deploy caller candidate; operational metadata starts pending.

One historical failed upload and one successful GET-only observation are kept
separate. The unchanged helper supplies a semantic intent; the adapter submits
one official single-URL GET only after durable journal reservation.
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
GUARD_SHA256 = 'a87729473bde88187a6db5a6c78c071bb6889dbd932c3142e9d18c0a1e6bd70f'
# Intentionally not configurable by issue body, environment, CLI, or JSON.
# Code seal alone cannot activate the caller: exact native review and stored
# operational metadata are required before reading environment or credentials.
OPERATIONAL_CONTROLS_ENABLED = True
ACTUAL_BUILD = {'artifactBytes': 799100, 'artifactDigest': 'sha256:43b618dc55c0536a16fe8887e6ce4b6a16254b82db7c34657fd23d976824b408', 'artifactId': 12040108398, 'artifactName': 'damyang-proof-recovery-build-38888053867-33ca99b04ae43af120d5799d926f1611b1d59942', 'controlRevision': '33ca99b04ae43af120d5799d926f1611b1d59942', 'runAttempt': 1, 'runId': 38888053867}
ACCEPTED_BUILD_REVIEW = {'commit': 'cd1dd949acc90ad896935d7a5fa11cab0ceb4de6', 'path': 'docs/direct-damyang-recovery/build-artifact-review-38888053867.json', 'sha256': '3a2263b174c32c161716a43cf4451186a1213b862125b7b44c9f8a9032fc5842', 'verdict': 'ACCEPT_SOURCE063E9_BUILD_ARTIFACT_ONLY'}
BUILD_READER_HELPERS = {'scripts/direct-damyang-recovery/recovery_build.py': '5a1c4b9d7ec6ca79caf36688c183935af77694d572bf63201d3a028b2beb5da5', 'scripts/direct-damyang-recovery/recovery_output.py': '559c00b6dbbbe85ef1dbd9a0bef026a75d8fe241839d8392d0cef59c1c52a6fd'}
DOWNLOAD_NAMES = {'build': 'damyang-recovery-build', 'baseline': 'damyang-recovery-baseline', 'update': 'damyang-recovery-update', 'reconciliation': 'damyang-recovery-reconciliation'}
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


def save(path,value):
    Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


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
                'operational_binding_sha256': sha(canonical(pins).encode()), 'submission_method': 'GET'}
    require(guard.exact(json_raw(raw), expected), 'closed_exact_request_required')
    require(pins.get('status') == 'INDEPENDENTLY_REVIEWED_ACTUAL_RECOVERY', 'actual_operational_acceptance_required')
    require(pins.get('sourceRevision') == SOURCE and pins.get('sourceBranch') == SOURCE_BRANCH
            and pins.get('sourceTree') == SOURCE_TREE and pins.get('schemaVersion') == 1,
            'fixed_successor_pins_required')
    for field in ('build', 'baseline', 'update', 'reconciliation', 'review', 'controlFiles', 'workflowFiles',
                  'artifactFiles', 'releaseFiles', 'releaseManifest'):
        require(type(pins.get(field)) is dict and bool(pins[field]), 'actual_' + field.lower() + '_binding_missing')
    require(guard._valid_sha(pins.get('reviewedControlRevision'), 40)
            and guard._valid_sha(pins.get('releaseManifestSha256'), 64), 'actual_control_manifest_binding_missing')
    for field in ('build', 'baseline', 'update', 'reconciliation'):
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
    contract = guard.Contract(public_release.ACTIVE[:-4], '39c4ed924bc6084c670a963c26d9f018')
    require(guard.exact(pins.get('submission'),guard._submission_binding(contract)),
            'exact_single_get_submission_binding_required')
    return expected


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None


class BoundedHTTP:
    """No redirect, no retry, fixed destinations, bounded bytes/headers/time.

    The sole token is injected by the reviewed workflow. It is sent only to the
    exact repository GitHub API URLs admitted by GitHubClient, never public URLs.
    """
    def __init__(self, token, api_urls, public_urls, *, opener=None, clock=time.monotonic, contract=None, evidence=None):
        require(type(token) is str and bool(token) and '\r' not in token and '\n' not in token,
                'workflow_github_token_required')
        self._token = token
        self.api_urls = frozenset(api_urls); self.public_urls = frozenset(public_urls)
        self.opener = opener if opener is not None else build_opener(NoRedirect())
        self.clock = clock; self.submission_reserved = False
        self.contract = contract; self.evidence = Path(evidence) if evidence is not None else None
        self.submission_url = guard._submission_url(contract) if contract is not None else None
        self.request_evidence_state = 'not_observed'; self.response_evidence_state = 'not_observed'

    def call(self, method, url, payload=None):
        comment_page = re.fullmatch(
            re.escape(guard.API_BASE) + r'/issues/comments\?per_page=100&page=([1-9][0-9]{0,4})', url)
        api = url in self.api_urls or (comment_page is not None and int(comment_page[1]) <= guard.MAX_PAGES)
        comment_write = url == guard.ISSUE_URL + '/comments'
        submission = method == 'GET' and payload is None and url == self.submission_url
        require((method == 'GET' and payload is None and (api or url in self.public_urls or submission))
                or (method == 'POST' and type(payload) is bytes and len(payload) <= 65536
                    and comment_write), 'fixed_http_scope_required')
        if submission:
            require(not self.submission_reserved, 'caller_single_submission_only')
            self.submission_reserved = True
        headers = {'User-Agent': 'Damyang-Reviewed-Recovery/1.0', 'Accept-Encoding': 'identity',
                   'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        if api or comment_write:
            headers.update({'Authorization': 'Bearer ' + self._token,
                            'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
        if method == 'POST': headers['Content-Type'] = 'application/json; charset=utf-8'
        req = Request(url, method=method, data=payload, headers=headers)
        if submission: self.observe_request(req)
        start = self.clock()
        try:
            response = self.opener.open(req, timeout=20)
        except HTTPError as error:
            response = error
        except Exception:
            raise guard.RecoveryBlocked('http_outcome_unconfirmed') from None
        response_started = False; body_complete = False
        body = bytearray(); pairs = []; lengths = []
        try:
            with response:
                require(response.geturl() == url, 'unexpected_response_url')
                require(type(response.code) is int and not 300 <= response.code < 400, 'redirect_forbidden')
                response_started = True
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
                body_complete = True
                result = guard.RawResponse(response.code, bytes(body), pairs)
                if submission: self.observe_response(result)
                return result
        except guard.RecoveryBlocked as error:
            if submission and response_started:
                self.observe_response_failure(response.code, bytes(body), lengths, str(error), body_complete)
            raise
        except Exception as error:
            # HTTPError is handled above as a response. IncompleteRead.partial
            # contains additional bytes from the failed read, not prior chunks.
            extra = getattr(error, 'partial', None)
            omitted = 0
            if type(extra) is bytes:
                available = max(0, guard.MAX_RESPONSE + 1 - len(body))
                body.extend(extra[:available]); omitted = max(0, len(extra)-available)
            if submission and response_started:
                self.observe_response_failure(response.code, bytes(body), lengths,
                    'response_capture_failed' if body_complete else 'http_read_incomplete_or_unconfirmed',
                    body_complete, omitted)
            raise guard.RecoveryBlocked('http_outcome_unconfirmed') from None

    def observe_response_failure(self, status, captured, lengths, reason, body_complete, omitted=0):
        # Best-effort evidence cannot spend another HTTP attempt or promote an
        # incomplete body to a completed response. Failure to save is still an
        # unknown, already-spent outcome under the durable started journal.
        self.response_evidence_state = 'failed_response_capture_unconfirmed'
        try:
            safe = safe_raw_body(guard.RawResponse(status,captured,[]),self.contract)
            declared = int(lengths[0]) if len(lengths)==1 and lengths[0].isdigit() and len(lengths[0])<16 else None
            value=dict(state='response_failed_or_capture_incomplete',httpStatusObserved=status,
                responseBodyReadComplete=body_complete,submissionOutcomeConfirmed=False,
                declaredContentLength=declared,capturedPrefixBytes=len(captured),
                capturedPrefixSha256=sha(captured),additionalExceptionBytesOmitted=omitted,
                rawPrefixRetained=safe is not None,rawPrefixFile='response-body.failed-prefix.txt' if safe is not None else None,
                prefixOmissionReason=None if safe is not None else 'bounded_public_safety_check_not_satisfied',
                reason=reason,submissionBudgetSpent=self.submission_reserved,retryAllowed=False)
            self.evidence.mkdir(parents=True,exist_ok=True)
            if safe is not None:
                require(safe==captured,'response_prefix_bytes_changed')
                (self.evidence/'response-body.failed-prefix.txt').write_bytes(safe)
            save(self.evidence/'response-failure-observation.json',value)
            self.response_evidence_state = 'failed_response_prefix_retained' if safe is not None else 'failed_response_prefix_withheld'
        except Exception:
            return False
        return True

    def observe_request(self, request):
        self.request_evidence_state = 'request_capture_unconfirmed'
        require(request.get_method() == 'GET' and request.data is None
                and request.full_url == self.submission_url, 'actual_single_get_request_mismatch')
        require(request.get_header('Authorization') is None, 'public_request_credential_forbidden')
        raw = request.full_url.encode('utf-8')
        require(len(raw) == 197 and sha(raw) == '92698d7bc01532f06447a75b8cf642d7cd5f779d3044c8c34cf9da224c00da67',
                'pinned_single_get_request_url_required')
        self.evidence.mkdir(parents=True,exist_ok=True)
        save(self.evidence/'request-observation.json',dict(method=request.get_method(),url=request.full_url,
            urlBytes=len(raw),urlSha256=sha(raw),bodyBytes=0,bodySha256=sha(b''),
            semanticIntentBytes=193,semanticIntentSha256='a5001635f14e4165cf75a248dc41c421c8e3045c0c5f0dd4d27d6d668ad2b23d',
            provenance='Actual urllib Request.get_method/full_url/data immediately before opener.open; no packet capture claimed',
            authorizationHeaderPresent=False,actualDataIsNone=True,submissionBudgetReserved=self.submission_reserved))
        self.request_evidence_state = 'actual_single_get_request_retained'

    def observe_response(self, response):
        self.response_evidence_state = 'complete_response_capture_unconfirmed'
        safe=safe_raw_body(response,self.contract)
        evidence=dict(responseBodyReadComplete=True,httpStatus=response.status,rawBodyBytes=len(response.body),rawBodySha256=sha(response.body),rawBodyRetained=safe is not None,rawBodyFile='response-body.txt' if safe is not None else None,bodyOmissionReason=None if safe is not None else 'bounded_public_safety_check_not_satisfied',diagnostics=guard.diagnostics(response,self.contract))
        if safe is not None:
            require(safe==response.body,'response_raw_bytes_changed')
            (self.evidence/'response-body.txt').write_bytes(safe)
        save(self.evidence/'response-observation.json',evidence)
        self.response_evidence_state = 'complete_response_retained' if safe is not None else 'complete_response_withheld'

def safe_raw_body(response,contract):
    """Optional exact diagnostic literals only; all other bodies are withheld.

    This is not a credential detector or redactor. Status, length, digest and
    existing sanitized diagnostics remain independent of raw retention.
    """
    if type(response.body) is bytes and response.body in (b'', b'Invalid urls'):
        return response.body
    return None

def api_urls(pins, run_id):
    urls = {guard.API_BASE + '/git/ref/heads/main',
        guard.API_BASE + '/git/ref/heads/' + SOURCE_BRANCH,
        guard.API_BASE + '/git/commits/' + SOURCE,
        guard.API_BASE + '/git/trees/' + SOURCE_TREE + '?recursive=1', guard.ISSUE_URL,
        guard.API_BASE + '/actions/runs/' + str(run_id)}
    for field in ('build', 'baseline', 'update', 'reconciliation'):
        row = pins[field]
        urls.add(guard.API_BASE + '/actions/runs/' + str(row['runId']))
        urls.add(guard.API_BASE + '/actions/artifacts/' + str(row['artifactId']))
    urls.update({guard.API_BASE + '/actions/jobs/117062829774',
                 guard.API_BASE + '/actions/jobs/117108113694',
                 guard.API_BASE + '/issues/comments/6219311010'})
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
                # GitHub's Link may identify this exact repository by immutable ID.
                # Normalize only the Link; HTTP still uses the original name URL.
                page_match = re.fullmatch(r'(?:' + re.escape(guard.API_BASE)
                    + r'|https://api\.github\.com/repositories/1360554691)'
                    + r'/issues/comments\?per_page=100&page=([1-9][0-9]*)', dest)
                require(page_match is not None and int(page_match[1]) <= guard.MAX_PAGES,
                        'foreign_or_noncanonical_github_pagination')
                dest = guard.page_url(int(page_match[1]))
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


# One historical upload only. Default verify_run remains success-only.
EXACT_FAILED_UPDATE = {'artifactBytes': 11493, 'artifactDigest': 'sha256:3127f575d0cf493ce65df79f7e55b1594fd9f5feb45e812f612218b9aa4b1e96', 'artifactId': 12056828086, 'artifactName': 'damyang-existing-static-update-result-38927541164', 'controlRevision': '683aae06c27d18e0a674fb32b61be17abcfd5996', 'runAttempt': 1, 'runId': 38927541164}
EXACT_FAILED_UPDATE_FILES = {'binding-after.json': '601e3b99010397566a51a25811a282af9c7a55c946b76e1b2a6381c1eb14f7ff', 'binding-before.json': 'c8c2cf48b9041f1f72cfd637f554638d6434a293c804358c0f3e629ce1cdeafd', 'claim-write-reserved.json': 'e4cbe2632e2ad3774a20e2738ae195c1dd83aabae629f02efb10d490d0d4cc92', 'deployment-attempt-claim.json': '67bd424d870f392aa67af38adcf6650bc431a85aadc56f148dc659f4fb8811ad', 'immediately-before-upload.json': 'a4139060a9680229e23217f234607f9d2387b5844777e81f9a86b13bd299be20', 'previous-public-http.json': 'b5f7fe6d61425f8a5a46b29bdf100dbeaefa8a74e2aad63cc3a45c411a35dd47', 'provider-state-after-observed.json': '25ff5d454f1ee9cbb47e8d1c24057c39096b6c07f9854b7aa7bb555e5bb53d5d', 'provider-state-before.json': 'e76c786f99a3e0547c8f6a000304b8735f6d8b492a9fcc62490a33dae7abec77', 'public-http-observations.json': '2aea3773609a4f541596d6efe87da0a3daa99b4a7426cb7b33a5a939c6513428', 'public-http.json': 'f8bf906ab0cd6d8b3ced04e9ab94f113f63a879a1eee1ff24a27945ffb193e65', 'release/release.json': 'b99c33011de1afe318779e8d750a2f267aa2c47d5a042455928fc720ab9fc986', 'release/wrangler.publish.json': '119e436410aa12cccd99f6ecac29619cd298202e7c911465a1bfaa1b702b9610', 'update-artifact-check.json': '2c1b3eb28807d1e162eb7d5562d0754196b1592fb0dc92c40dfe00f6efd6b86a', 'update-claim-result.json': '67bd424d870f392aa67af38adcf6650bc431a85aadc56f148dc659f4fb8811ad', 'update-selection.json': 'ff2a0ea56c293c34ac209944bd2428d24ea0b4a8327b8dbfdd87ec2638e6e300', 'update-source-config.json': 'ce51a23cdaa8024f0fb1ade0764e53aa1bacd56dd5cd5ffedd5856f5c31f733c', 'upload-version.json': '2a3deee30c1df2f177d20e9624059748f77aa9ee522d4fe2e72c3918a56fd2b1'}
EXACT_FAILED_UPDATE_STEPS = [{'number': 1, 'name': 'Set up job', 'status': 'completed', 'conclusion': 'success'}, {'number': 2, 'name': 'Run actions/checkout@v4', 'status': 'completed', 'conclusion': 'success'}, {'number': 3, 'name': 'Run trusted control regressions without credentials or site code', 'status': 'completed', 'conclusion': 'success'}, {'number': 4, 'name': 'Require actual baseline acceptance and reviewed metadata before retrieval', 'status': 'completed', 'conclusion': 'success'}, {'number': 5, 'name': 'Run actions/download-artifact@v4', 'status': 'completed', 'conclusion': 'success'}, {'number': 6, 'name': 'Run actions/download-artifact@v4', 'status': 'completed', 'conclusion': 'success'}, {'number': 7, 'name': 'Read exact actual build24 and baseline artifact then copy release17 only', 'status': 'completed', 'conclusion': 'success'}, {'number': 8, 'name': 'Run actions/setup-node@v4', 'status': 'completed', 'conclusion': 'success'}, {'number': 9, 'name': 'GET accepted current target and old public15 before and after', 'status': 'completed', 'conclusion': 'success'}, {'number': 10, 'name': 'Write one claim to original receipt377 and read it directly and repository-wide', 'status': 'completed', 'conclusion': 'success'}, {'number': 11, 'name': 'Recheck source main full journal accepted state config and old public15', 'status': 'completed', 'conclusion': 'success'}, {'number': 12, 'name': 'Upload fixed existing route-less static assets once', 'status': 'completed', 'conclusion': 'success'}, {'number': 13, 'name': 'Parse only one version UUID digest from successful private upload log', 'status': 'completed', 'conclusion': 'success'}, {'number': 14, 'name': 'GET-only provider observation retained even after uncertain upload', 'status': 'completed', 'conclusion': 'success'}, {'number': 15, 'name': 'Check public16 independently of provider readback success', 'status': 'completed', 'conclusion': 'success'}, {'number': 16, 'name': 'Retain bounded evidence without raw uploader output or provider responses', 'status': 'completed', 'conclusion': 'success'}, {'number': 17, 'name': 'Require upload success and independently recorded provider and public results', 'status': 'completed', 'conclusion': 'failure'}, {'number': 33, 'name': 'Post Run actions/setup-node@v4', 'status': 'completed', 'conclusion': 'skipped'}, {'number': 34, 'name': 'Post Run actions/checkout@v4', 'status': 'completed', 'conclusion': 'success'}, {'number': 35, 'name': 'Complete job', 'status': 'completed', 'conclusion': 'success'}]
EXACT_UPLOADED_STATE_SHA256 = '16ab9442d70e3e75ef69320b70769456bc8eef62408bb979c93753e484a5ee63'
EXACT_UPLOAD_CLAIM_ID = 6219311010


def verify_exact_uploaded_failure(data, job):
    """Verify one historical failed run as failure; never alter its conclusion."""
    row = EXACT_FAILED_UPDATE
    require(type(data) is dict and type(data.get('id')) is int and data['id'] == row['runId']
            and type(data.get('run_attempt')) is int and data['run_attempt'] == 1
            and data.get('event') == 'issues' and data.get('head_branch') == 'main'
            and data.get('head_sha') == row['controlRevision'] and data.get('path') == WORKFLOW
            and data.get('repository', {}).get('full_name') == guard.REPOSITORY
            and type(data.get('repository', {}).get('id')) is int
            and data['repository']['id'] == 1360554691
            and data.get('actor', {}).get('login') == OWNER
            and data.get('triggering_actor', {}).get('login') == OWNER
            and data.get('status') == 'completed' and data.get('conclusion') == 'failure',
            'exact_historical_failed_upload_run_required')
    require(type(job) is dict and type(job.get('id')) is int and job['id'] == 117062829774
            and type(job.get('run_id')) is int and job['run_id'] == row['runId']
            and type(job.get('run_attempt')) is int and job['run_attempt'] == 1
            and job.get('head_branch') == 'main' and job.get('head_sha') == row['controlRevision']
            and job.get('name') == 'recovery_static_update' and job.get('status') == 'completed'
            and job.get('conclusion') == 'failure' and type(job.get('steps')) is list,
            'exact_historical_upload_job_required')
    steps = [{k:s.get(k) for k in ('number','name','status','conclusion')} for s in job['steps'] if type(s) is dict]
    require(len(steps) == len(job['steps']) and guard.exact(steps, EXACT_FAILED_UPDATE_STEPS),
            'exact_completed_upload_readback_and_failed_aggregate_required')
    # The original public step wrapper returned success, but artifact public-http
    # is blocked and the aggregate failed. Its API status is not public acceptance.
    return {'state': 'EXACT_HISTORICAL_FAILED_UPLOAD_IDENTITY_VERIFIED',
        'runId': row['runId'], 'controlRevision': row['controlRevision'], 'conclusion': 'failure',
        'uploadAndProviderReadbackSucceeded': True, 'publicAccepted': False}


def validate_failed_uploaded_artifact(update_root, pins, baseline):
    """Consume exact retained17 as historical data, not a new successful run."""
    require(guard.exact(pins.get('failedUpdate'), EXACT_FAILED_UPDATE), 'exact_failed_update_binding_required')
    require(public_release.file_inventory(update_root) == EXACT_FAILED_UPDATE_FILES,
            'exact_historical_failed_artifact17_required')
    root = Path(update_root)
    report = lambda name: read_json(root / name)
    before = report('provider-state-before.json'); after = report('provider-state-after-observed.json')
    require(guard.exact(before, baseline.get('currentProviderState'))
            and guard.digest(before) == baseline.get('currentProviderStateSHA256'),
            'historical_upload_actual_baseline_mismatch')
    require(guard.digest(after) == EXACT_UPLOADED_STATE_SHA256
            and guard.exact({k:v for k,v in before.items() if k != 'activeDeployment'},
                            {k:v for k,v in after.items() if k != 'activeDeployment'})
            and checked_version_coverage(after.get('activeDeployment')),
            'historical_exact_uploaded_projection_required')
    upload = report('upload-version.json'); active = after['activeDeployment']
    require(guard.exact(upload, {'state':'ONE_UPLOAD_SUCCEEDED_VERSION_PARSED',
            'runId':str(EXACT_FAILED_UPDATE['runId']), 'sourceRevision':SOURCE,
            'versionIdSHA256':active['versionIdSHA256']}), 'historical_upload_version_binding_required')
    require(guard.exact(report('release/release.json'), pins['releaseManifest'])
            and sha(public_release.read_file(root/'release/release.json')) == pins['releaseManifestSha256'],
            'historical_upload_manifest_binding_required')
    require(guard.exact(report('public-http.json'), {
            'liveBrowserPixelsVerified':False, 'mode':'public',
            'reason':'duplicate_or_unsafe_public_header', 'searchIndexing':'not_verified',
            'sourceRevision':SOURCE, 'state':'BLOCKED_OR_OUTCOME_UNCERTAIN_NO_AUTOMATIC_REUPLOAD'}),
            'original_public_failure_must_be_retained')
    claim = report('deployment-attempt-claim.json')
    require(guard.exact(claim, report('update-claim-result.json'))
            and claim.get('commentId') == EXACT_UPLOAD_CLAIM_ID and type(claim.get('commentId')) is int
            and claim.get('runId') == str(EXACT_FAILED_UPDATE['runId'])
            and claim.get('controlRevision') == EXACT_FAILED_UPDATE['controlRevision']
            and claim.get('state') == 'STARTED_NO_AUTOMATIC_REUPLOAD'
            and claim.get('sourceRevision') == SOURCE and claim.get('hostname') == 'damyang.fwith.kr'
            and claim.get('buildRunId') == pins['build']['runId']
            and claim.get('artifactId') == pins['build']['artifactId']
            and claim.get('artifactDigest') == pins['build']['artifactDigest']
            and claim.get('outputFilesSha256') == guard.digest(pins['releaseFiles'])
            and claim.get('releaseManifestSha256') == pins['releaseManifestSha256']
            and claim.get('providerStateSHA256') == guard.digest(before),
            'historical_claim_source_and_build_binding_required')
    require(guard.exact(report('binding-after.json'), {
            'state':'EXACT_NEW_VERSION_AND_UNCHANGED_BINDING_VERIFIED', 'sourceRevision':SOURCE,
            'previousSourceRevision':guard.CHAIN['originalSourceRevision'],
            'accountSHA256':after['accountSHA256'], 'hostname':after['hostname'], 'worker':after['worker'],
            'currentProviderStateSHA256':guard.digest(after), 'deploymentIdSHA256':active['deploymentIdSHA256'],
            'versionIdSHA256':active['versionIdSHA256'], 'providerMethods':['GET'],
            'providerMutationsPerformed':False,'hostnameAttached':False,'publicHTTPVerified':False}),
            'historical_exact_provider_readback_required')
    return {'claim':claim, 'providerAfter':after, 'originalFailure':report('public-http.json')}

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


def verify_download_roots(workspace, roots, *, preparing, reconciliation=False):
    """Fixed fresh Actions roots, not a staging package or receipt protocol.

    Uses the trusted hosted runner's exclusively controlled workspace. This is
    not a general defense against an arbitrary hostile same-UID process.
    """
    require(type(workspace) is str and workspace and Path(workspace).is_absolute()
            and type(preparing) is bool and type(reconciliation) is bool
            and set(roots) == (set(DOWNLOAD_NAMES) if reconciliation else set(DOWNLOAD_NAMES)-{'reconciliation'}),
            'fixed_download_workspace_required')
    base = Path(workspace)
    require(all(part not in ('.', '..') for part in base.parts)
            and base.is_dir() and not any(p.is_symlink() for p in (base, *base.parents)),
            'symlink_free_download_workspace_required')
    for role, name in DOWNLOAD_NAMES.items():
        if role == 'reconciliation' and not reconciliation: continue
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
                'scripts/direct-damyang-recovery/test_finalizer_reconciliation.py',
                'docs/direct-damyang-recovery/update-caller-binding.json',
                'docs/direct-damyang-recovery/reconciliation-binding.json',
                'docs/direct-damyang-recovery/source-files.json',
                'scripts/direct-damyang-recovery/contract-source/release-adapter/scripts/damyang_release_output.py',
                'scripts/direct-damyang-recovery/contract-source/release-adapter/release/damyang-indexnow-proof.txt',
                'scripts/direct-damyang-recovery/contract-source/release-adapter/release/existing-indexnow-proof.txt'}
    required.update(BUILD_READER_HELPERS)
    require(type(ACTUAL_RECONCILIATION_REVIEW) is dict, 'actual_reconciliation_native_required')
    required.add(ACTUAL_RECONCILIATION_REVIEW['path'])
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
    for name in ('update-caller-binding.json','reconciliation-binding.json'):
        other = read_json(root / 'docs/direct-damyang-recovery' / name)
        require(other.get('operationalActivationAllowed') is False
                and all(other.get(k) is None for k in ('review','reviewedControlRevision','controlFiles','workflowFiles')),
                'other_damyang_mutation_routes_must_remain_pending')
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


def validate_update_evidence(baseline_root, update_root, pins, *, reconciliation_root=None, control_root=None):
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
    if reconciliation_root is None:
        public = report('update', update_root, 'publicRelease')
    else:
        validate_failed_uploaded_artifact(update_root,pins,baseline)
        public = validate_reconciliation_evidence(reconciliation_root,update_root,pins,control_root)
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


ACTUAL_RECONCILIATION = {'artifactBytes': 799164, 'artifactDigest': 'sha256:6f7241bb89cfedb9426cfc8cf180e7fbedb2e224f84d5599496005771c4d0e10', 'artifactId': 12063760673, 'artifactName': 'damyang-uploaded-get-reconciliation-result-38940944526', 'controlRevision': '5f72a3a86a68f3a6e3f43589519881658842613d', 'runAttempt': 1, 'runId': 38940944526}
ACTUAL_RECONCILIATION_FILES = {'reconciliation-inputs.json': '446df7dfbcf75b33b82f1a6df3bec8ebf53e0a53fec94676a31218f7442ad5e9', 'reconciliation-provider-after.json': '25ff5d454f1ee9cbb47e8d1c24057c39096b6c07f9854b7aa7bb555e5bb53d5d', 'reconciliation-provider-before.json': '25ff5d454f1ee9cbb47e8d1c24057c39096b6c07f9854b7aa7bb555e5bb53d5d', 'reconciliation-public-bodies/39c4ed924bc6084c670a963c26d9f018.txt': '5da3864d5327c6e4e41e6eef12510004b2302f55c3bc61593d7d49c1797739b5', 'reconciliation-public-bodies/404.html': '774d19dd4d453fa7eb301c259cf6decb0ab2df968db3e1fce4b874a9566c8cc1', 'reconciliation-public-bodies/_astro/CopyPage.iUxX7g7p.css': '833f9684e4b228e423465e2462796f1538dafa899b7d82a4e43478110aee441c', 'reconciliation-public-bodies/db5e090bdb87762ce7c7ec5c01f6ab73.txt': 'a818ead0cec264f34e0763edc923803719244855f8b281c214688c296790ecec', 'reconciliation-public-bodies/favicon.svg': '7ad52153b6e98b0b1a93bf546b2c1f3a9d9724a450703086fcedcb30fd05c3b4', 'reconciliation-public-bodies/images/products/B060.jpg': 'a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3', 'reconciliation-public-bodies/images/products/B201.jpg': '7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3', 'reconciliation-public-bodies/images/products/B203.jpg': '0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114', 'reconciliation-public-bodies/images/products/B205.jpg': '1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e', 'reconciliation-public-bodies/images/shared-banners/flower-budget.webp': '081198095eb005603721be7c778f4d477f4dd93dcf96f0c261f18bf06bb91421', 'reconciliation-public-bodies/images/shared-banners/flower-consultation.webp': 'd6654aa44c365f64e330d0be2042972d3320fad54231425aaffca1dfdcd25ebc', 'reconciliation-public-bodies/images/shared-banners/flower-message.webp': 'a5ecdeb1914566a32d45b084351e2782fc8b234e9a4fbb8635a60a9921cac5f5', 'reconciliation-public-bodies/index.html': 'ec4b4913af8b7b020de451ea70c5f21e8c5ebb359422e2de6e0515010997400b', 'reconciliation-public-bodies/robots.txt': '465a928d5df6c1d9b4a25dce1450f4a3d2e9beaa686c6301212e295dd51eab46', 'reconciliation-public-bodies/sitemap-0.xml': 'fe31bdd42fe7a68fbe1d990710352ea13433ddeb04974e5cba5f43f781d833b6', 'reconciliation-public-bodies/sitemap-index.xml': '7514d38cc21218578a925bda9d3ccb112773cd9b7f560d6049bfd2fdd6d811a3', 'reconciliation-public-http.json': 'a33890ac0df2265e0e743bde4a6404c67ae707b23dd1ba0f330bb58cbcc8f83c', 'reconciliation-public-observations.json': '2bc8c0d89073f3fc78ef37e0762f26e056bc06c1c781711b670ce56c2cce4b51', 'reconciliation-result.json': '40f2a558288ec01eb2c7564535d6637cdea5253abf3514bb673c036a70b292ee', 'reconciliation-selection.json': 'a58e031a70c24ada101105b1381907c87c1a94ce142714feed8d87efc3b8a1b3'}
ACTUAL_RECONCILIATION_STEPS = [{'number': 1, 'name': 'Set up job', 'status': 'completed', 'conclusion': 'success'}, {'number': 2, 'name': 'Run actions/checkout@v4', 'status': 'completed', 'conclusion': 'success'}, {'number': 3, 'name': 'Run trusted control regressions without credentials or site code', 'status': 'completed', 'conclusion': 'success'}, {'number': 4, 'name': 'Require actual baseline acceptance and reviewed metadata before retrieval', 'status': 'completed', 'conclusion': 'success'}, {'number': 5, 'name': 'Run actions/download-artifact@v4', 'status': 'completed', 'conclusion': 'success'}, {'number': 6, 'name': 'Run actions/download-artifact@v4', 'status': 'completed', 'conclusion': 'success'}, {'number': 7, 'name': 'Run actions/download-artifact@v4', 'status': 'completed', 'conclusion': 'success'}, {'number': 8, 'name': 'Read exact actual build24 and baseline artifact then copy release17 only', 'status': 'completed', 'conclusion': 'success'}, {'number': 9, 'name': 'Run actions/setup-node@v4', 'status': 'completed', 'conclusion': 'skipped'}, {'number': 10, 'name': 'GET accepted current target and old public15 before and after', 'status': 'completed', 'conclusion': 'skipped'}, {'number': 11, 'name': 'Write one claim to original receipt377 and read it directly and repository-wide', 'status': 'completed', 'conclusion': 'skipped'}, {'number': 12, 'name': 'Recheck source main full journal accepted state config and old public15', 'status': 'completed', 'conclusion': 'skipped'}, {'number': 13, 'name': 'Upload fixed existing route-less static assets once', 'status': 'completed', 'conclusion': 'skipped'}, {'number': 14, 'name': 'Parse only one version UUID digest from successful private upload log', 'status': 'completed', 'conclusion': 'skipped'}, {'number': 15, 'name': 'GET-only provider observation retained even after uncertain upload', 'status': 'completed', 'conclusion': 'success'}, {'number': 16, 'name': 'Check public16 independently of provider readback success', 'status': 'completed', 'conclusion': 'skipped'}, {'number': 17, 'name': 'Retain bounded evidence without raw uploader output or provider responses', 'status': 'completed', 'conclusion': 'success'}, {'number': 18, 'name': 'Require upload success and independently recorded provider and public results', 'status': 'completed', 'conclusion': 'success'}, {'number': 36, 'name': 'Post Run actions/checkout@v4', 'status': 'completed', 'conclusion': 'success'}, {'number': 37, 'name': 'Complete job', 'status': 'completed', 'conclusion': 'success'}]
ACTUAL_RECONCILIATION_REVIEW = {'path': 'docs/direct-damyang-recovery/uploaded-get-reconciliation-actual-review-38940944526.json', 'sha256': '559a7680ac57725a9318b929217e7a1c60d19e97b50f08fe5555e530cb660dbb', 'verdict': 'ACCEPT_ACTUAL_UPLOADED_GET_ONLY_RECONCILIATION'}

# Exact successful GET-only run, separate from the historical failed upload.
# This artifact never becomes the failed upload artifact or changes its verdict.

def verify_reconciliation_run(data, job):
    verify_run(ACTUAL_RECONCILIATION, data, WORKFLOW)
    require(type(data.get('repository', {}).get('id')) is int
            and data['repository']['id'] == 1360554691, 'exact_reconciliation_repository_required')
    require(type(job) is dict and type(job.get('id')) is int and job['id'] == 117108113694
            and type(job.get('run_id')) is int and job['run_id'] == ACTUAL_RECONCILIATION['runId']
            and type(job.get('run_attempt')) is int and job['run_attempt'] == 1
            and job.get('head_branch') == 'main' and job.get('head_sha') == ACTUAL_RECONCILIATION['controlRevision']
            and job.get('name') == 'recovery_static_update' and job.get('status') == 'completed'
            and job.get('conclusion') == 'success' and type(job.get('steps')) is list,
            'exact_successful_reconciliation_job_required')
    steps = [{k:s.get(k) for k in ('number','name','status','conclusion')} for s in job['steps'] if type(s) is dict]
    require(len(steps) == len(job['steps']) and guard.exact(steps, ACTUAL_RECONCILIATION_STEPS),
            'exact_get_only_steps_and_skipped_mutations_required')
    return True


def verify_bound_role(github, role, pins):
    row = pins[role]
    data, _ = github.get(guard.API_BASE + '/actions/runs/' + str(row['runId']))
    if role == 'update':
        require(guard.exact({k:row.get(k) for k in EXACT_FAILED_UPDATE}, EXACT_FAILED_UPDATE),
                'one_exact_failed_upload_only')
        job, _ = github.get(guard.API_BASE + '/actions/jobs/117062829774')
        verify_exact_uploaded_failure(data, job)
    elif role == 'reconciliation':
        require(guard.exact({k:row.get(k) for k in ACTUAL_RECONCILIATION}, ACTUAL_RECONCILIATION),
                'one_exact_get_reconciliation_only')
        job, _ = github.get(guard.API_BASE + '/actions/jobs/117108113694')
        verify_reconciliation_run(data, job)
    else:
        verify_run(row, data, BUILD_WORKFLOW if role == 'build' else WORKFLOW)
    meta, _ = github.get(guard.API_BASE + '/actions/artifacts/' + str(row['artifactId']))
    verify_artifact_meta(row, meta)


def validate_reconciliation_evidence(root, update_root, pins, control_root):
    """Consume exact historical17 + successful GET23 as two provenances.

    Retained policy headers and all bodies are replayed. Omitted telemetry is
    not reconstructed; its original safety check is bound to the reviewed run.
    This is sequential observed state, not an atomic/ABA or new browser proof.
    """
    root = Path(root)
    row = pins['reconciliation']
    require(guard.exact({k:row.get(k) for k in ACTUAL_RECONCILIATION}, ACTUAL_RECONCILIATION)
            and guard.exact(row.get('files'), ACTUAL_RECONCILIATION_FILES)
            and public_release.file_inventory(root) == ACTUAL_RECONCILIATION_FILES,
            'exact_successful_reconciliation_artifact23_required')
    require(public_release.file_inventory(update_root) == EXACT_FAILED_UPDATE_FILES,
            'historical_failed17_must_remain_distinct')
    expected = read_json(Path(update_root) / 'provider-state-after-observed.json')
    for name in ('reconciliation-provider-before.json','reconciliation-provider-after.json'):
        require(guard.exact(read_json(root / name), expected)
                and guard.digest(expected) == EXACT_UPLOADED_STATE_SHA256,
                'reconciled_provider_must_equal_original_uploaded_projection')
    result = read_json(root / 'reconciliation-result.json')
    required = {'schema':'damyang-uploaded-get-only-reconciliation/v1',
        'state':'EXACT_UPLOADED_PROVIDER_AND_PUBLIC16_REVERIFIED_PENDING_INDEPENDENT_ACCEPTANCE',
        'currentRunId':str(ACTUAL_RECONCILIATION['runId']),
        'currentControlRevision':ACTUAL_RECONCILIATION['controlRevision'], 'currentRunAttempt':1,
        'sourceRevision':SOURCE, 'originalUpdate':EXACT_FAILED_UPDATE, 'originalUpdateConclusion':'failure',
        'originalArtifactFilesSHA256':guard.digest(EXACT_FAILED_UPDATE_FILES),
        'originalClaimCommentId':EXACT_UPLOAD_CLAIM_ID, 'providerStateSHA256':EXACT_UPLOADED_STATE_SHA256,
        'providerSnapshots':2, 'publicPaths':16, 'providerMethods':['GET'], 'githubMethods':['GET'],
        'publicMethods':['GET'], 'newClaimCreated':False, 'providerMutationsPerformed':False,
        'IndexNowSubmitted':False, 'originalFailureHeadersRetained':False,
        'independentAcceptance':False, 'liveBrowserPixelsVerified':False}
    require(all(guard.exact(result.get(k),v) for k,v in required.items()),
            'separate_get_only_provenance_required')
    observation = read_json(root / 'reconciliation-public-observations.json')
    require(observation.get('currentRunId') == str(ACTUAL_RECONCILIATION['runId'])
            and observation.get('currentControlRevision') == ACTUAL_RECONCILIATION['controlRevision']
            and observation.get('originalUpdateRunId') == EXACT_FAILED_UPDATE['runId']
            and observation.get('sourceRevision') == SOURCE, 'separate_public_observation_identity_required')
    rows = observation.get('observations')
    require(type(rows) is list and len(rows) == 16, 'exact_reconciled_public_rows_required')
    checks = []; consumed = {'content-type','content-length','content-encoding','x-robots-tag',
                            'cf-mitigated','location','content-security-policy','cache-control'}
    require([(r.get('path'),r.get('file'),r.get('httpStatus')) for r in rows] == public_release.inventory(),
            'exact_reconciled_public_inventory_required')
    for item in rows:
        body = public_release.read_file(root / 'reconciliation-public-bodies' / item['file'])
        require(len(body) == item.get('bodyBytes') and sha(body) == item.get('bodySHA256'),
                'reconciled_public_body_mismatch')
        validation = item.get('headerValidation', {})
        headers = validation.get('rows')
        require(validation.get('state') == 'ALL_ORIGINAL_ROWS_VALIDATED_BEFORE_VALUE_PROJECTION'
                and validation.get('checkerSHA256') == '3edb22cfc985fc47bcf5a7533e1dd1190e4ad147aa40a0e7e235631741c45390'
                and validation.get('allRowsTuple2Strings') is True
                and validation.get('responseAndBodyBoundsChecked') is True
                and type(headers) is list and type(validation.get('rawRowCount')) is int
                and len(headers) == validation['rawRowCount'] <= 100,
                'reviewed_before_discard_header_checks_required')
        retained = []; counts = {}
        for h in headers:
            name = h.get('name')
            require(type(name) is str and re.fullmatch('[A-Za-z0-9-]{1,128}', name) is not None
                    and h.get('valueType') == 'str'
                    and all(h.get(k) is True for k in ('namePatternValid','lengthWithin4096','noCRorLF'))
                    and type(h.get('valueCharacters')) is int and 0 <= h['valueCharacters'] <= 4096
                    and type(h.get('valueUTF8Bytes')) is int and h['valueUTF8Bytes'] >= 0
                    and guard._valid_sha(h.get('valueSHA256'),64), 'reconciled_header_projection_invalid')
            lower = name.lower(); counts[lower] = counts.get(lower,0) + 1
            if lower in consumed:
                value = h.get('value')
                require(type(value) is str and len(value) == h['valueCharacters']
                        and len(value.encode()) == h['valueUTF8Bytes'] and sha(value.encode()) == h['valueSHA256']
                        and '\r' not in value and '\n' not in value and 'valueOmitted' not in h,
                        'retained_public_policy_header_mismatch')
                retained.append((name,value))
            else:
                require(h.get('valueOmitted') is True and 'value' not in h, 'omitted_telemetry_not_reconstructed')
        duplicate = {k:v for k,v in counts.items() if v > 1}
        require(guard.exact(duplicate,validation.get('duplicates')) and set(duplicate) <= {'server-timing'},
                'reconciled_only_timing_duplicates_allowed')
        check = public_release.verify_public_response(item['path'],item['file'],item['httpStatus'],
            guard.RawResponse(item['httpStatus'],body,retained),pins['releaseFiles'],SOURCE)
        require(guard.exact(check,item.get('publicCheck')), 'reconciled_policy_body_replay_mismatch')
        checks.append(check)
    public = read_json(root / 'reconciliation-public-http.json')
    require(guard.exact(public.get('checks'),checks)
            and public_release.file_inventory(root / 'reconciliation-public-bodies') ==
                {r['file']:r['rawBodySha256'] for r in checks}, 'complete_reconciled_body16_required')
    acceptance = pins.get('acceptedReconciliationReview')
    require(type(acceptance) is dict and acceptance == ACTUAL_RECONCILIATION_REVIEW,
            'fixed_independent_reconciliation_acceptance_required')
    raw = public_release.read_file(Path(control_root) / acceptance['path'])
    require(sha(raw) == acceptance['sha256'], 'independent_reconciliation_review_bytes_required')
    return public


def verify_original_upload_claim(github, claim, *, whole_repository):
    """Read original claim; independently retain full-repository exclusivity.

    Recovery receipt budget is still checked by the unchanged adapter audit.
    This scan does not reject our own newly started receipt or create a claim.
    """
    marker = '<!-- damyang-proof-recovery-attempt-v1 -->\n'
    expected = {k:v for k,v in claim.items() if k != 'commentId'}
    comment, _ = github.get(guard.API_BASE + '/issues/comments/6219311010')
    guard._trusted_comment(comment)
    require(comment.get('id') == EXACT_UPLOAD_CLAIM_ID and comment['body'].startswith(marker)
            and guard.exact(json_raw(comment['body'][len(marker):]), expected),
            'original_upload_claim_direct_readback_required')
    if not whole_repository: return True
    found = []; ids = set()
    for number in range(1,guard.MAX_PAGES + 1):
        page = github.read_page(number)
        require(type(page) is guard.AuditPage and page.url == guard.page_url(number)
                and page.status == 200 and page.complete is True and type(page.comments) is list,
                'complete_original_claim_journal_required')
        require((page.next_url == guard.page_url(number+1) and len(page.comments) == 100)
                or (page.next_url is None and len(page.comments) < 100), 'original_claim_pagination_incomplete')
        for value in page.comments:
            require(type(value) is dict and type(value.get('id')) is int and value['id'] not in ids,
                    'duplicate_original_claim_journal_comment')
            ids.add(value['id']); body = value.get('body')
            require(type(body) is str, 'original_claim_comment_body_required')
            if marker not in body: continue
            guard._trusted_comment(value)
            require(body.startswith(marker), 'misplaced_original_upload_claim_marker')
            record = json_raw(body[len(marker):])
            require(guard.exact(record,expected), 'foreign_or_changed_damyang_upload_claim')
            found.append(value['id'])
        if page.next_url is None:
            require(found == [EXACT_UPLOAD_CLAIM_ID], 'original_upload_claim_not_exclusive')
            return True
    raise guard.RecoveryBlocked('original_claim_journal_page_limit')


class Runtime:
    def __init__(self, *, pins, env, control_root, artifact_root, baseline_root, update_root, github, http, reconciliation_root=None):
        self.pins = pins; self.env = env; self.control_root = Path(control_root)
        self.artifact_root = Path(artifact_root); self.baseline_root = Path(baseline_root); self.update_root = Path(update_root)
        self.reconciliation_root = Path(reconciliation_root) if reconciliation_root is not None else None
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
        for field in ('build','baseline','update','reconciliation'):
            verify_bound_role(self.github,field,self.pins)
        journal, _ = self.github.get(guard.ISSUE_URL)
        require(journal.get('number') == 377 and journal.get('state') == 'open'
                and journal.get('title') == '[DAMYANG-INDEXNOW-RECEIPTS] 20261016'
                and journal.get('user', {}).get('login') == OWNER and 'pull_request' not in journal
                and journal.get('repository_url') == guard.API_BASE, 'original_receipt_issue_required')
        validate_retained_artifact(self.artifact_root, self.pins)
        validate_actual_build_review(self.artifact_root, self.pins, self.control_root)
        require(self.reconciliation_root is not None, 'actual_reconciliation_root_required')
        validate_update_evidence(self.baseline_root, self.update_root, self.pins,
            reconciliation_root=self.reconciliation_root, control_root=self.control_root)
        claim = read_json(self.update_root / 'deployment-attempt-claim.json')
        verify_original_upload_claim(self.github,claim,whole_repository=True)
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
                and reviewed.get('reconciliationBindingSha256') == guard.digest(self.pins['reconciliation'])
                and reviewed.get('acceptedReconciliationReview') == self.pins.get('acceptedReconciliationReview')
                and reviewed.get('originalUpdateConclusion') == 'failure'
                and reviewed.get('originalClaimCommentId') == EXACT_UPLOAD_CLAIM_ID
                and reviewed.get('submissionBindingSha256') == guard.digest(self.pins['submission'])
                and reviewed.get('maximumAdditionalSubmissions') == 1
                and reviewed.get('submissionMethod') == 'GET'
                and reviewed.get('artifactFilesSha256') == guard.digest(self.pins['artifactFiles'])
                and reviewed.get('releaseFilesSha256') == guard.digest(self.pins['releaseFiles'])
                and reviewed.get('oldPixelScope') == 'unchanged-html-bodies-css-images-only'
                and reviewed.get('freshLiveBrowserPixelsClaimed') is False, 'complete_independent_actual_review_required')
        return True

    def validate_public(self, binding):
        require(binding == self.binding, 'runtime_binding_changed')
        claim = read_json(self.update_root / 'deployment-attempt-claim.json')
        verify_original_upload_claim(self.github,claim,whole_repository=True)
        evidence = public_release.verify_public_release(self.artifact_root / 'release-recovery/dist', self.pins['releaseFiles'], SOURCE,
            lambda url: self.http.call('GET', url))
        self.public_observations.append(evidence)
        return True

    def transport(self, method, url, payload=None):
        response = self.http.call(method, url, payload)
        if method == 'GET' and url != self.http.submission_url:
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
    parser.add_argument('--reconciliation-root', type=Path, default=Path('damyang-recovery-reconciliation'))
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args(); runtime = None
    try:
        pins_path = args.control_root / 'docs/direct-damyang-recovery/finalizer-binding.json'
        pins = approved_pins(pins_path)
        env = dict(os.environ); event = read_json(env.get('GITHUB_EVENT_PATH', ''))
        authorize(pins, env, event)
        verify_download_roots(env.get('GITHUB_WORKSPACE'),
            {'build': args.artifact_root, 'baseline': args.baseline_root, 'update': args.update_root,
             'reconciliation': args.reconciliation_root},
            preparing=args.mode == 'prepare', reconciliation=True)
        require(not (args.report.parent / 'submission-evidence').exists(), 'fresh_submission_evidence_required')
        token = env.get('GH_TOKEN', '')
        http = BoundedHTTP(token, api_urls(pins, env['GITHUB_RUN_ID']),
            [guard.ORIGIN + path for path, _, _ in public_release.inventory()],
            contract=guard.load_contract(args.control_root / 'scripts/direct-damyang-recovery/contract-source'),
            evidence=args.report.parent / 'submission-evidence')
        github = GitHubClient(http)
        runtime = Runtime(pins=pins, env=env, control_root=args.control_root,
            artifact_root=args.artifact_root, baseline_root=args.baseline_root,
            update_root=args.update_root, github=github, http=http, reconciliation_root=args.reconciliation_root)
        if args.mode == 'prepare':
            runtime.serialized()
            validate_source(github, read_json(args.control_root / 'docs/direct-damyang-recovery/source-files.json'))
            for role in ('build','baseline','update','reconciliation'):
                verify_bound_role(github,role,pins)
            out = Path(env['GITHUB_OUTPUT'])
            with out.open('a') as stream:
                for role in ('build', 'baseline', 'update', 'reconciliation'):
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
            result['executionObservation'] = {'submissionReservations': adapter.submission_calls,
                'httpPostCallsThisInvocation': 0,
                'submissionMethod': 'GET',
                'startedWriteReservations': adapter.start_writes,
                'durableStartedCommentId': adapter.started[0] if adapter.started else None,
                'responseDiagnostics': adapter.last_diagnostics,
                'retryAllowed': False,
                'requestEvidenceState': runtime.http.request_evidence_state,
                'responseEvidenceState': runtime.http.response_evidence_state}
            # A reservation does not prove the submission GET arrived. This
            # report omits raw values; separate evidence retains only bounded
            # safety-checked diagnostics, never credentials or exception text.
        args.report.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
        if runtime is not None and runtime.public_observations:
            args.report.with_name('finalizer-public-http.json').write_text(json.dumps(runtime.public_observations, indent=2, sort_keys=True) + '\n')
        print(json.dumps(result, sort_keys=True)); return 1


if __name__ == '__main__': raise SystemExit(main())
