"""Dependency-injected, single-attempt IndexNow recovery control proposal.

No CLI, HTTP implementation, GitHub writes, credentials, or provider operations
live here. A future reviewed caller must bind the actual source/control/artifact,
provide trustworthy full API pages and durable writes, and serialize the entire
operation with every publisher that can submit this host. The process lock is
additional protection, not a substitute for that cross-workflow serialization.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from datetime import datetime
from email.utils import parsedate_to_datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import threading
from typing import Callable

REPOSITORY = 'joseungil-kr/fwith-site-factory'
ORIGIN = 'https://damyang.fwith.kr'
HOME = ORIGIN + '/'
SITE_KEY = 'damyang-flower-direct'
ENDPOINT = 'https://searchadvisor.naver.com/indexnow'
MARKER = 'SITE_FACTORY_INDEXNOW_V1 '
API_BASE = 'https://api.github.com/repos/' + REPOSITORY
ISSUE_URL = API_BASE + '/issues/377'
WEB_ISSUE = 'https://github.com/' + REPOSITORY + '/issues/377'
BOT_ID = 41898282
HELPER_SHA256 = '55f5274d3fcc713e82fd8ce18e280447e68e9e460bc1ff3f9bf5cc683834935f'
ACTIVE_PROOF_SHA256 = 'a818ead0cec264f34e0763edc923803719244855f8b281c214688c296790ecec'
RETAINED_PROOF_SHA256 = '5da3864d5327c6e4e41e6eef12510004b2302f55c3bc61593d7d49c1797739b5'
CHAIN = {
    'originalSourceRevision': '89c92dff3dca6456c1b0a3f7ee0587efe0361bed',
    'originalPublicationRunId': 38861200090,
    'originalReceiptIssue': 377,
    'originalStartedCommentId': 6209522619,
    'originalRejectedCommentId': 6209523005,
    'originalFingerprint': 'ccef3be8005323e66f2038a490f94df15a843fd7abbc2726801f233db2807d22',
    'originalUrlSetSha256': 'bcd12b5887c8bccc074ca964fc5b39c55599264b5084641320fcb267a76960c7',
    'originalHttpStatus': 422,
    'historicalPostAttempts': 1,
    'maximumRecoveryPostAttempts': 1,
    'maximumTotalPostAttempts': 2,
}
MAX_RESPONSE = 8 * 1024 * 1024
MAX_PAGES = 10000
_LOCK = threading.Lock()


class RecoveryBlocked(ValueError):
    """Messages are fixed reason codes, never exception text or response bodies."""


def require(ok, code):
    if not ok:
        raise RecoveryBlocked(code)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(canonical(value).encode())


def exact(left, right):
    return canonical(left) == canonical(right)


@dataclass(frozen=True)
class Contract:
    active_key: str = field(repr=False)
    retained_key: str = field(repr=False)


def load_contract(source_root):
    """Read only frozen literal constants and exact public proof files."""
    root = Path(source_root) / 'release-adapter'
    path = root / 'scripts/damyang_release_output.py'
    require(path.is_file() and not path.is_symlink(), 'contract_regular_file_required')
    tree = ast.parse(path.read_text())
    names = {'ORIGIN', 'ROUTES', 'PROOF', 'LEGACY_PROOF', 'PROOF_RECOVERY_CHAIN'}
    found = {}
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    require(target.id not in found, 'duplicate_contract_constant')
                    found[target.id] = ast.literal_eval(statement.value)
    require(found.keys() == names, 'contract_constants_missing')
    require(found['ORIGIN'] == ORIGIN and found['ROUTES'] == ['/']
            and exact(found['PROOF_RECOVERY_CHAIN'], CHAIN), 'contract_chain_mismatch')
    values = []
    for name, filename, expected_sha in (
        ('PROOF', 'damyang-indexnow-proof.txt', ACTIVE_PROOF_SHA256),
        ('LEGACY_PROOF', 'existing-indexnow-proof.txt', RETAINED_PROOF_SHA256),
    ):
        proof = found[name]
        p = root / 'release' / filename
        require(p.is_file() and not p.is_symlink(), 'proof_regular_file_required')
        raw = p.read_bytes()
        require(len(raw) <= 129 and sha(raw) == expected_sha, 'proof_bytes_mismatch')
        key = raw.decode('ascii').removesuffix('\n')
        require(re.fullmatch(r'[A-Za-z0-9-]{8,128}', key) is not None
                and raw == (key + '\n').encode(), 'proof_format_invalid')
        require(exact(proof, {'origin': ORIGIN, 'path': '/' + key + '.txt',
                            'sha256': expected_sha}), 'proof_binding_mismatch')
        values.append(key)
    require(values[0] != values[1], 'new_proof_required')
    return Contract(*values)


@dataclass(frozen=True)
class Binding:
    """Actual externally verified values; fixture values grant no authority."""
    source_revision: str
    control_revision: str
    artifact_sha256: str
    run_url: str


@dataclass(frozen=True)
class AuditPage:
    """Trusted raw GitHub API page. next_url must come from the API Link header.

    The callback must not use a search API, issue-only scan, connector-truncated
    response, cached excerpt, or synthesized pagination metadata.
    """
    url: str
    status: int
    comments: list
    next_url: str | None
    complete: bool


@dataclass(frozen=True)
class RawResponse:
    status: int
    body: bytes = field(repr=False)
    headers: list[tuple[str, str]] = field(repr=False)


def page_url(number):
    return API_BASE + '/issues/comments?per_page=100&page=' + str(number)


def original_record(state):
    record = {
        'attempt': 1, 'endpoint': ENDPOINT,
        'fingerprint': CHAIN['originalFingerprint'], 'origin': ORIGIN,
        'recordedAt': '2026-10-16T06:27:23.430862+00:00',
        'revision': CHAIN['originalSourceRevision'],
        'runUrl': 'https://github.com/' + REPOSITORY + '/actions/runs/38861200090',
        'siteKey': SITE_KEY, 'state': state, 'urlCount': 1,
        'urlSetSha256': CHAIN['originalUrlSetSha256'],
    }
    if state == 'rejected':
        record['httpStatus'] = 422
    return record


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate_journal_json_key')
            result[key] = value
        return result
    def invalid_constant(_):
        raise RecoveryBlocked('nonfinite_journal_json')
    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=invalid_constant)
    except RecoveryBlocked:
        raise
    except Exception:
        raise RecoveryBlocked('malformed_journal_json') from None
    require(type(value) is dict, 'journal_object_required')
    return value


def _relevant(record):
    # Any relevant identity field reserves the lifetime budget, across sites,
    # source/key changes, fingerprints, and receipt issues in this repository.
    serialized = canonical(record)
    return (record.get('urlSetSha256') == CHAIN['originalUrlSetSha256']
            or record.get('fingerprint') == CHAIN['originalFingerprint']
            or record.get('siteKey') == SITE_KEY
            or record.get('originalReceiptIssue') == CHAIN['originalReceiptIssue']
            or 'damyang.fwith.kr' in serialized.lower()
            or CHAIN['originalFingerprint'] in serialized
            or str(CHAIN['originalRejectedCommentId']) in serialized
            or str(CHAIN['originalStartedCommentId']) in serialized)


def _trusted_comment(comment):
    require(type(comment) is dict and type(comment.get('id')) is int
            and comment['id'] > 0, 'invalid_comment_metadata')
    author = comment.get('user')
    require(type(author) is dict and author.get('login') == 'github-actions[bot]'
            and type(author.get('id')) is int and author['id'] == BOT_ID
            and author.get('type') == 'Bot', 'untrusted_relevant_journal_author')
    require(comment.get('issue_url') == ISSUE_URL
            and comment.get('html_url') == WEB_ISSUE + '#issuecomment-' + str(comment['id'])
            and comment.get('url') == API_BASE + '/issues/comments/' + str(comment['id']),
            'unexpected_relevant_receipt_location')
    require(type(comment.get('body')) is str and len(comment['body'].encode()) <= 65536,
            'invalid_comment_body')


def _identity(revision):
    return {'siteKey': SITE_KEY, 'origin': ORIGIN, 'revision': revision,
            'endpoint': ENDPOINT, 'urlSetSha256': CHAIN['originalUrlSetSha256'], 'urlCount': 1}


def _payload(contract):
    # Keep insertion order and default json.dumps identical to the shared helper.
    return {'host': 'damyang.fwith.kr', 'key': contract.active_key,
            'keyLocation': ORIGIN + '/' + contract.active_key + '.txt', 'urlList': [HOME]}


def _fingerprint(contract, revision):
    return digest({**_identity(revision), 'keySha256': digest(contract.active_key)})


def _lineage():
    return {**CHAIN, 'lifetimeAttempt': 2, 'recoveryAttempt': 1,
            'activeProofSha256': ACTIVE_PROOF_SHA256}


def _valid_sha(value, size):
    return type(value) is str and re.fullmatch('[0-9a-f]{' + str(size) + '}', value) is not None


def _validate_binding(binding):
    require(type(binding) is Binding, 'binding_required')
    require(_valid_sha(binding.source_revision, 40)
            and binding.source_revision != CHAIN['originalSourceRevision']
            and _valid_sha(binding.control_revision, 40)
            and _valid_sha(binding.artifact_sha256, 64), 'actual_release_binding_required')
    require(re.fullmatch(r'https://github\.com/joseungil-kr/fwith-site-factory/actions/runs/[1-9][0-9]*',
                         binding.run_url or '') is not None, 'exact_workflow_run_required')


def _validate_successor(record, contract):
    base = {'attempt', 'endpoint', 'fingerprint', 'origin', 'recordedAt', 'revision',
            'runUrl', 'siteKey', 'state', 'urlCount', 'urlSetSha256', 'controlRevision',
            'sourceArtifactSha256', 'requestSha256', 'requestBytes', *_lineage().keys()}
    require(set(record).issubset(base | {'httpStatus', 'response', 'retryNotBefore'})
            and base.issubset(record), 'unexpected_successor_record_schema')
    binding = Binding(record['revision'], record['controlRevision'],
                      record['sourceArtifactSha256'], record['runUrl'])
    _validate_binding(binding)
    expected = {**_identity(binding.source_revision), **_lineage(), 'attempt': 2,
                'fingerprint': _fingerprint(contract, binding.source_revision),
                'requestSha256': sha(json.dumps(_payload(contract)).encode()),
                'requestBytes': len(json.dumps(_payload(contract)).encode())}
    require(exact({k: record[k] for k in expected}, expected), 'successor_chain_or_budget_mismatch')
    require(type(record['recordedAt']) is str and len(record['recordedAt']) < 64,
            'successor_timestamp_invalid')
    try:
        timestamp = datetime.fromisoformat(record['recordedAt'])
        require(timestamp.tzinfo is not None, 'successor_timestamp_invalid')
    except (TypeError, ValueError):
        raise RecoveryBlocked('successor_timestamp_invalid') from None
    require(record['state'] in {'started', 'received', 'received_key_validation_pending',
                                'rejected', 'unknown'}, 'successor_state_invalid')
    if record['state'] == 'started':
        require(not ({'httpStatus', 'response', 'retryNotBefore'} & record.keys()),
                'started_must_not_claim_response')
    if 'httpStatus' in record:
        require(type(record['httpStatus']) is int and 100 <= record['httpStatus'] <= 599,
                'response_status_invalid')
    if 'retryNotBefore' in record:
        require(record['state'] == 'rejected' and record.get('httpStatus') == 429
                and type(record['retryNotBefore']) in (int, float)
                and math.isfinite(record['retryNotBefore']) and record['retryNotBefore'] >= 0,
                'retry_diagnostic_invalid')
    if 'response' in record:
        validate_diagnostics(record['response'], contract)


@dataclass(frozen=True)
class ChainAudit:
    successor: tuple

    @property
    def accepted(self):
        return self.successor[-1][1] if len(self.successor) == 2 else None


def audit_chain(read_page: Callable[[int], AuditPage], contract: Contract,
                *, own_started=None):
    """Validate every returned repository comment page; never filter by new fp."""
    relevant, seen = [], set()
    for number in range(1, MAX_PAGES + 1):
        try:
            page = read_page(number)
        except Exception:
            raise RecoveryBlocked('journal_page_read_failed') from None
        require(type(page) is AuditPage and page.url == page_url(number)
                and type(page.status) is int and page.status == 200
                and page.complete is True and type(page.comments) is list
                and len(page.comments) <= 100, 'untrusted_or_truncated_journal_page')
        for comment in page.comments:
            require(type(comment) is dict and type(comment.get('id')) is int
                    and comment['id'] > 0 and comment['id'] not in seen,
                    'duplicate_or_invalid_journal_comment')
            seen.add(comment['id'])
            body = comment.get('body')
            require(type(body) is str and len(body.encode()) <= 65536, 'unbounded_journal_body')
            if MARKER not in body:
                continue
            require(body.startswith(MARKER), 'misplaced_journal_marker')
            record = strict_json(body[len(MARKER):])
            if _relevant(record):
                _trusted_comment(comment)
                relevant.append((comment['id'], record))
        if page.next_url is None:
            require(len(page.comments) < 100, 'ambiguous_full_final_page')
            break
        require(len(page.comments) == 100 and page.next_url == page_url(number + 1),
                'truncated_or_noncanonical_pagination')
    else:
        raise RecoveryBlocked('journal_page_bound_exceeded')
    relevant.sort(key=lambda item: item[0])
    require(len(relevant) >= 2, 'pinned_original_receipt_pair_missing')
    expected = [(CHAIN['originalStartedCommentId'], original_record('started')),
                (CHAIN['originalRejectedCommentId'], original_record('rejected'))]
    require(exact(relevant[:2], expected), 'pinned_original_receipt_pair_mismatch')
    successor = relevant[2:]
    require(len(successor) <= 2, 'duplicate_or_excess_recovery_chain')
    for _, record in successor:
        _validate_successor(record, contract)
    if own_started is not None:
        require(len(successor) == 1 and exact(successor[0], own_started),
                'own_durable_started_not_exclusive')
        return ChainAudit(tuple(successor))
    if successor:
        require(len(successor) == 2, 'prior_recovery_outcome_uncertain')
        started, terminal = successor[0][1], successor[1][1]
        require(started['state'] == 'started', 'successor_started_missing')
        expected_started = {k: v for k, v in terminal.items()
                            if k not in {'httpStatus', 'response', 'retryNotBefore'}}
        expected_started['state'] = 'started'
        require(exact(expected_started, started), 'successor_receipt_pair_mismatch')
        require((terminal['state'], terminal.get('httpStatus')) in
                {('received', 200), ('received_key_validation_pending', 202)},
                'recovery_budget_spent_or_unknown')
        require('response' in terminal and terminal['response']['httpStatus'] == terminal['httpStatus'],
                'accepted_diagnostics_missing_or_mismatched')
    return ChainAudit(tuple(successor))


def _redact(text, contract):
    for key in (contract.active_key, contract.retained_key):
        text = re.sub(re.escape(key), '[REDACTED]', text, flags=re.I)
    text = re.sub(r'(?i)\b(?:bearer|basic)\s+[^\s,;]+', '[REDACTED]', text)
    text = re.sub(r'(?i)\b(?:password|passwd|secret|token|api[-_ ]?key|authorization|cookie|credential)'
                  r'\b\s*[:=]\s*(?:"[^"]*"|\x27[^\x27]*\x27|[^\s,;]+)', '[REDACTED]', text)
    text = re.sub(r'\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|'
                  r'AKIA[A-Z0-9]+|sk-[A-Za-z0-9_-]+)\b', '[REDACTED]', text)
    text = re.sub(r'\b[A-Za-z0-9_+/=-]{20,}\b', '[REDACTED]', text)
    return text


def _safe_text(text, contract, limit=1024):
    if type(text) is not str or len(text) > 4096 or any(ord(c) < 32 and c not in '\n\t' for c in text):
        return None
    # HTML, markup and escape-obfuscated text are intentionally omitted.
    if '<' in text or '>' in text or '\\' in text:
        return None
    redacted = _redact(text, contract)
    # Do not attempt to infer where a loosely formatted credential ends. If a
    # credential-bearing label survives the explicit patterns, omit the entire
    # excerpt (the raw-byte digest and length remain available).
    if re.search(r'(?i)\b(?:passwords?|passwd|secrets?|tokens?|api[-_ ]?keys?|keys?|'
                 r'authorization|auth|cookies?|credentials?|bearer|basic|'
                 r'access[-_ ]?keys?|private[-_ ]?keys?|session)\b', redacted):
        return None
    return redacted if len(redacted.encode()) <= limit else None


def diagnostics(response, contract):
    require(type(response) is RawResponse and type(response.status) is int
            and 100 <= response.status <= 599 and type(response.body) is bytes
            and len(response.body) <= MAX_RESPONSE and type(response.headers) is list
            and len(response.headers) <= 100, 'malformed_or_unbounded_response')
    headers = {}
    for item in response.headers:
        require(type(item) is tuple and len(item) == 2 and all(type(x) is str for x in item),
                'malformed_response_headers')
        name, value = item
        require(len(name) <= 128 and len(value) <= 4096, 'unbounded_response_header')
        name = name.lower()
        require(re.fullmatch(r'[a-z0-9-]+', name) is not None, 'malformed_response_header_name')
        # Duplicate headers are ambiguous: retain none of that header's values.
        headers[name] = None if name in headers else value
    safe_headers = _select_safe_headers(headers, contract)
    result = {'httpStatus': response.status, 'bodySha256': sha(response.body),
              'bodyBytes': len(response.body), 'safeHeaders': safe_headers}
    # A byte digest and length survive invalid UTF-8. Never store the raw body.
    if len(response.body) <= 4096:
        try:
            text = response.body.decode('utf-8')
        except UnicodeDecodeError:
            text = None
        content_type = safe_headers.get('content-type', '').lower()
        if text is not None and content_type.startswith('application/'):
            try:
                data = strict_json(text)
            except (RecoveryBlocked, RecursionError):
                data = None
            if data is not None:
                selected = {}
                for key in ('code', 'error', 'message', 'status', 'detail', 'title'):
                    value = data.get(key)
                    if type(value) is str:
                        safe = _safe_text(value, contract, 512)
                        if safe is not None:
                            selected[key] = safe
                    elif type(value) is int and abs(value) < 1000000:
                        selected[key] = value
                if selected:
                    safe = canonical(selected)
                    if len(safe.encode()) <= 1024:
                        result['sanitizedText'] = safe
        elif text is not None and content_type.startswith('text/plain'):
            safe = _safe_text(text, contract)
            if safe is not None:
                result['sanitizedText'] = safe
    return result


def _select_safe_headers(headers, contract):
    safe_headers = {}
    for name in ('content-type', 'retry-after', 'date', 'x-request-id'):
        value = headers.get(name)
        if value is None:
            continue
        # Media-type grammar is restrictive enough to validate before redaction.
        # This avoids mistaking application/problem+json for an opaque token.
        if name == 'content-type':
            if type(value) is str and re.fullmatch(r'(?:text/plain|application/(?:json|problem\+json))(?:; *charset=(?:utf-8|us-ascii))?', value, re.I):
                safe_headers[name] = value
            continue
        safe = _safe_text(value, contract, 256)
        if safe is None or '\n' in safe or '\t' in safe:
            continue
        if name == 'retry-after' and not re.fullmatch(r'[0-9]{1,8}', safe):
            continue
        if name == 'date':
            if not re.fullmatch(r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), [0-9]{2} '
                    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) '
                    r'[0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2} GMT', safe):
                continue
            try:
                parsedate_to_datetime(safe)
            except (ValueError, TypeError, OverflowError):
                continue
        safe_headers[name] = safe
    return safe_headers


def validate_diagnostics(value, contract):
    require(type(value) is dict and set(value).issubset(
        {'httpStatus', 'bodySha256', 'bodyBytes', 'safeHeaders', 'sanitizedText'})
        and {'httpStatus', 'bodySha256', 'bodyBytes', 'safeHeaders'}.issubset(value),
        'stored_diagnostics_invalid')
    require(type(value['httpStatus']) is int and 100 <= value['httpStatus'] <= 599
            and _valid_sha(value['bodySha256'], 64)
            and type(value['bodyBytes']) is int and 0 <= value['bodyBytes'] <= MAX_RESPONSE
            and type(value['safeHeaders']) is dict
            and set(value['safeHeaders']).issubset({'content-type', 'retry-after', 'date', 'x-request-id'}),
            'stored_diagnostics_invalid')
    require(exact(_select_safe_headers(value['safeHeaders'], contract), value['safeHeaders']),
            'stored_diagnostics_unsafe')
    if 'sanitizedText' in value:
        text = value['sanitizedText']
        # Already-sanitized JSON contains quotes; it is safe only if re-redaction
        # is idempotent and size/control constraints hold.
        require(type(text) is str and len(text.encode()) <= 1024
                and _redact(text, contract) == text
                and not any(ord(c) < 32 and c not in '\n\t' for c in text),
                'stored_diagnostics_unsafe')
        replay = diagnostics(RawResponse(value['httpStatus'], text.encode(),
                                         list(value['safeHeaders'].items())), contract)
        require(replay.get('sanitizedText') == text, 'stored_diagnostics_unsafe')


def load_shared_helper(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and sha(path.read_bytes()) == HELPER_SHA256,
            'unchanged_shared_helper_required')
    spec = importlib.util.spec_from_file_location('_damyang_pinned_indexnow_finalize', path)
    module = importlib.util.module_from_spec(spec)
    # compile/exec avoids import bytecode writes beside the unchanged shared file.
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


class RecoveryAdapter:
    """Single-use wrapper. All effectful dependencies are explicit callbacks.

    validate_binding must independently validate source/control/artifact and the
    caller's authorization. assert_serialized must verify the shared workflow
    lock (including other direct publishers); both must return exactly True.
    validate_full_public_release must verify the bound full 16-object release,
    including the retained proof and all static assets, and return exactly True.
    It runs before reuse and again before the fresh started write. The shared
    helper additionally verifies current home/active proof/sitemaps/robots itself.
    read_page returns full raw repository comment pages, write_record returns a
    full raw API comment, and transport accepts exact serialized bytes or None.
    No default implementation can access a network or a credential.
    """
    def __init__(self, *, contract, binding, helper_path, read_page, write_record,
                 transport, validate_binding, assert_serialized, validate_full_public_release):
        require(type(contract) is Contract, 'contract_required')
        require(sha((contract.active_key + '\n').encode()) == ACTIVE_PROOF_SHA256
                and sha((contract.retained_key + '\n').encode()) == RETAINED_PROOF_SHA256,
                'exact_active_and_retained_proofs_required')
        _validate_binding(binding)
        self.contract, self.binding = contract, binding
        self.helper = load_shared_helper(helper_path)
        self.read_page, self.write_record, self.transport_callback = read_page, write_record, transport
        self.validate_binding, self.assert_serialized = validate_binding, assert_serialized
        self.validate_full_public_release = validate_full_public_release
        self.started = None
        self.start_writes = self.post_calls = 0
        self.last_diagnostics = None
        self.used = False

    def _guard(self):
        require(self.assert_serialized() is True, 'shared_serialization_not_verified')
        require(self.validate_binding(self.binding) is True, 'release_binding_not_verified')

    def records(self):
        self._guard()
        audit = audit_chain(self.read_page, self.contract)
        return [record for _, record in audit.successor]

    def write(self, record):
        self._guard()
        require(record.get('attempt') == 1, 'second_started_or_attempt_forbidden')
        require(exact({k: record.get(k) for k in _identity(self.binding.source_revision)},
                      _identity(self.binding.source_revision))
                and record.get('fingerprint') == _fingerprint(self.contract, self.binding.source_revision)
                and record.get('runUrl') == self.binding.run_url, 'helper_record_identity_mismatch')
        decorated = {**record, **_lineage(), 'attempt': 2,
                     'controlRevision': self.binding.control_revision,
                     'sourceArtifactSha256': self.binding.artifact_sha256,
                     'requestSha256': sha(json.dumps(_payload(self.contract)).encode()),
                     'requestBytes': len(json.dumps(_payload(self.contract)).encode())}
        if record['state'] == 'started':
            require(self.start_writes == 0 and self.post_calls == 0 and self.started is None,
                    'second_started_or_attempt_forbidden')
            require(self.validate_full_public_release(self.binding) is True,
                    'full_public_release_not_verified')
            # Last action before the durable started write is a fresh chain scan.
            require(not audit_chain(self.read_page, self.contract).successor,
                    'recovery_budget_already_spent')
            self.start_writes += 1
        else:
            require(self.started is not None and self.start_writes == 1 and self.post_calls == 1,
                    'terminal_without_single_attempt')
            audit_chain(self.read_page, self.contract, own_started=self.started)
            if self.last_diagnostics is not None:
                decorated['response'] = self.last_diagnostics
        _validate_successor(decorated, self.contract)
        try:
            saved = self.write_record(decorated)
        except Exception:
            raise RecoveryBlocked('durable_journal_write_unconfirmed') from None
        _trusted_comment(saved)
        require(saved['body'].startswith(MARKER)
                and exact(strict_json(saved['body'][len(MARKER):]), decorated),
                'journal_write_echo_mismatch')
        if record['state'] == 'started':
            self.started = (saved['id'], decorated)
            audit_chain(self.read_page, self.contract, own_started=self.started)
        else:
            # Read back the exact terminal write even for rejected/unknown states.
            self._readback_terminal(saved['id'], decorated)

    def _readback_terminal(self, comment_id, record):
        # audit_chain deliberately rejects nonaccepted terminal states. Read its
        # complete pages with only this known terminal temporarily omitted, then
        # verify the started record and exact terminal bytes independently.
        found = []
        def excluding(number):
            page = self.read_page(number)
            if type(page) is not AuditPage:
                return page
            # Keep page counts unchanged by replacing the one terminal with an
            # ordinary non-journal comment. Pagination validation remains exact.
            comments = []
            for c in page.comments:
                if c.get('id') == comment_id:
                    _trusted_comment(c)
                    require(c.get('body', '').startswith(MARKER)
                            and exact(strict_json(c['body'][len(MARKER):]), record),
                            'terminal_readback_mismatch')
                    found.append(c['id'])
                    comments.append({**c, 'body': ''})
                else:
                    comments.append(c)
            return AuditPage(page.url, page.status, comments, page.next_url, page.complete)
        audit_chain(excluding, self.contract, own_started=self.started)
        require(found == [comment_id], 'terminal_readback_missing_or_duplicate')

    def transport(self, method, url, payload=None):
        self._guard()
        if method == 'POST':
            require(url == ENDPOINT and type(payload) is dict
                    and json.dumps(payload).encode() == json.dumps(_payload(self.contract)).encode(),
                    'fixed_post_payload_required')
            require(self.post_calls == 0 and self.start_writes == 1 and self.started is not None,
                    'single_durable_post_only')
            audit_chain(self.read_page, self.contract, own_started=self.started)
            self.post_calls += 1  # Reserve before callback: even a timeout spends it.
            response = self.transport_callback(method, url, json.dumps(payload).encode())
            self.last_diagnostics = diagnostics(response, self.contract)
            return response.status, '', self.last_diagnostics['safeHeaders']
        require(method == 'GET' and payload is None and url in {
            HOME, ORIGIN + '/robots.txt', ORIGIN + '/sitemap-index.xml', ORIGIN + '/sitemap-0.xml',
            ORIGIN + '/' + self.contract.active_key + '.txt'}, 'unexpected_public_probe')
        response = self.transport_callback(method, url, None)
        require(type(response) is RawResponse and type(response.status) is int
                and type(response.body) is bytes and len(response.body) <= MAX_RESPONSE
                and type(response.headers) is list, 'invalid_public_probe_response')
        headers = {}
        for pair in response.headers:
            require(type(pair) is tuple and len(pair) == 2 and all(type(x) is str for x in pair),
                    'invalid_public_probe_headers')
            name, value = pair
            name = name.lower()
            require(name not in headers and '\n' not in value and '\r' not in value,
                    'ambiguous_public_probe_headers')
            headers[name] = value
        try:
            text = response.body.decode('utf-8')
        except UnicodeDecodeError:
            raise RecoveryBlocked('invalid_public_probe_encoding') from None
        if url.endswith('/' + self.contract.active_key + '.txt'):
            require(response.status == 200 and response.body == (self.contract.active_key + '\n').encode(),
                    'active_public_proof_not_exact')
        return response.status, text, headers

    @staticmethod
    def no_retry_sleep(_):
        raise RecoveryBlocked('automatic_retry_forbidden')

    def run(self, root, site):
        require(not self.used, 'adapter_instance_already_used')
        self.used = True
        require(_LOCK.acquire(blocking=False), 'concurrent_local_recovery_forbidden')
        try:
            self._guard()
            require(exact(site, {'siteKey': SITE_KEY, 'siteUrl': ORIGIN,
                                'indexnowKey': self.contract.active_key,
                                'productionEnabled': True, 'launchMode': 'live'}),
                    'fixed_site_configuration_required')
            require(self.validate_full_public_release(self.binding) is True,
                    'full_public_release_not_verified')
            audit = audit_chain(self.read_page, self.contract)
            if audit.accepted is not None:
                receipt = audit.accepted
                require(receipt['fingerprint'] == _fingerprint(self.contract, self.binding.source_revision)
                        and receipt['revision'] == self.binding.source_revision
                        and receipt['controlRevision'] == self.binding.control_revision
                        and receipt['sourceArtifactSha256'] == self.binding.artifact_sha256,
                        'accepted_receipt_for_different_successor')
                require(self.helper.verify_public(site, self.binding.source_revision, root,
                    lambda url: self.transport('GET', url)) == [HOME],
                    'reuse_public_surface_not_verified')
                return {'state': 'already_received', 'receiptState': receipt['state'],
                        'httpStatus': receipt['httpStatus'], 'receiptRevision': receipt['revision'],
                        'requestedRevision': self.binding.source_revision,
                        'receiptCommentId': audit.successor[-1][0],
                        'fingerprint': receipt['fingerprint'], 'postCallsThisInvocation': 0,
                        'urlSetSha256': CHAIN['originalUrlSetSha256'], 'lifetimeAttempt': 2,
                        'searchIndexing': 'not_verified'}
            self.helper.finalize(site, self.binding.source_revision, root, self,
                                 transport=self.transport, run_url=self.binding.run_url,
                                 sleep=self.no_retry_sleep)
            verified = audit_chain(self.read_page, self.contract)
            require(verified.accepted is not None and self.post_calls == 1,
                    'accepted_receipt_not_verified')
            return {**verified.accepted, 'postCallsThisInvocation': 1, 'searchIndexing': 'not_verified'}
        except RecoveryBlocked:
            raise
        except Exception:
            # Do not allow a callback exception to print credentials/body text.
            raise RecoveryBlocked('recovery_blocked_or_outcome_uncertain') from None
        finally:
            _LOCK.release()
