"""Offline fixture tests. No network, provider, or real journal writes occur.

The original pair, public proof, source and artifact pins come from retained
evidence. New controls, callbacks and recovery receipts are offline fixtures.
Passing tests is not a deployment or acceptance claim.
"""
import copy
import hashlib
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

import indexnow_recovery as r

DIRECTORY = Path(__file__).resolve().parent
SOURCE = DIRECTORY / 'fixtures/release'
HELPER = DIRECTORY.parents[1] / 'site-factory/engine/indexnow_finalize.py'
ORIGINAL = DIRECTORY / 'fixtures/original-journal.json'


def comment(identifier, record, **changes):
    value = {'id': identifier, 'user': {'id': r.BOT_ID, 'login': 'github-actions[bot]', 'type': 'Bot'},
             'url': r.API_BASE + '/issues/comments/' + str(identifier),
             'issue_url': r.ISSUE_URL,
             'html_url': r.WEB_ISSUE + '#issuecomment-' + str(identifier),
             'body': r.MARKER + json.dumps(record, ensure_ascii=False, sort_keys=True)}
    if identifier in r.ORIGINAL_COMMENT_PINS:
        pin=r.ORIGINAL_COMMENT_PINS[identifier];value.update(created_at=pin['createdAt'],updated_at=pin['updatedAt'])
    value.update(changes)
    return value


class Fixture:
    def __init__(self, root):
        self.root = root
        self.contract = r.load_contract(SOURCE)
        self.binding = r.Binding(r.CHAIN['originalSourceRevision'], 'b' * 40, 'deac983235eadbacb1fecee2b4f4249f738af94a609f4a544463977a9f124316',
            'https://github.com/joseungil-kr/fwith-site-factory/actions/runs/99999999999')
        originals = json.loads(ORIGINAL.read_text())
        self.comments = [comment(row['commentId'], row['record']) for row in originals]
        self.writes, self.calls, self.page_calls = [], [], []
        self.status = 200
        self.body = b'{"message":"received"}'
        self.headers = [('content-type', 'application/json')]
        self.throw_post = None
        self.throw_write = None
        self.page_transform = None
        self.before_write = None
        self.valid_binding = True
        self.serialized = True
        self.full_public = True
        dist = root / 'dist'
        dist.mkdir()
        html = ('<!doctype html><html><head><meta name="robots" content="index,follow">'
                '<meta name="site-factory-revision" content="' + self.binding.source_revision + '">'
                '<link rel="canonical" href="' + r.HOME + '"></head><body>Offline fixture</body></html>')
        files = {'index.html': html,
                 'robots.txt': 'User-agent: *\nAllow: /\n',
                 'sitemap-index.xml': '<sitemapindex><sitemap><loc>' + r.ORIGIN + '/sitemap-0.xml</loc></sitemap></sitemapindex>',
                 'sitemap-0.xml': '<urlset><url><loc>' + r.HOME + '</loc></url></urlset>',
                 self.contract.active_key + '.txt': self.contract.active_key + '\n'}
        self.public = {r.ORIGIN + ('/' if name == 'index.html' else '/' + name): raw.encode()
                       for name, raw in files.items()}
        for name, raw in files.items():
            (dist / name).write_text(raw)

    def site(self):
        return {'siteKey': r.SITE_KEY, 'siteUrl': r.ORIGIN, 'indexnowKey': self.contract.active_key,
                'productionEnabled': True, 'launchMode': 'live'}

    def read_page(self, number):
        self.page_calls.append(number)
        rows = copy.deepcopy(self.comments[(number - 1) * 100:number * 100])
        more = len(self.comments) > number * 100
        page = r.AuditPage(r.page_url(number), 200, rows,
                           r.page_url(number + 1) if more else None, True)
        return self.page_transform(number, page) if self.page_transform else page

    def write_record(self, record):
        if self.before_write:
            self.before_write(record)
        if self.throw_write and self.throw_write(record):
            raise RuntimeError('test failure token=DO_NOT_LOG')
        self.writes.append(copy.deepcopy(record))
        saved = comment(7000000000 + len(self.writes), copy.deepcopy(record))
        self.comments.append(saved)
        return copy.deepcopy(saved)

    def transport(self, method, url, payload):
        self.calls.append((method, url, payload))
        if method == 'GET':
            return r.RawResponse(200, self.public[url], [('content-type', 'text/plain')])
        if self.throw_post:
            raise self.throw_post
        return r.RawResponse(self.status, self.body, self.headers)

    def adapter(self, **overrides):
        kwargs = dict(contract=self.contract, binding=self.binding, helper_path=HELPER,
                      read_page=self.read_page, write_record=self.write_record, transport=self.transport,
                      validate_binding=lambda binding: self.valid_binding,
                      assert_serialized=lambda: self.serialized,
                      validate_full_public_release=lambda binding: self.full_public)
        kwargs.update(overrides)
        return r.RecoveryAdapter(**kwargs)

    def run(self, **overrides):
        return self.adapter(**overrides).run(self.root, self.site())

    @property
    def posts(self):
        return [call for call in self.calls if call[0] == 'POST']


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.f = Fixture(Path(self.temp.name))
        self.socket_patch = patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden'))
        self.socket_patch.start()
        self.addCleanup(self.socket_patch.stop)
        self.create_patch = patch('socket.create_connection', side_effect=AssertionError('network forbidden'))
        self.create_patch.start()
        self.addCleanup(self.create_patch.stop)

    def blocked(self, pattern=None, **overrides):
        with self.assertRaisesRegex(r.RecoveryBlocked, pattern or '^[a-z0-9_]+$'):
            self.f.run(**overrides)

    def test_original_pair_exactly_matches_retained_evidence(self):
        rows = json.loads(ORIGINAL.read_text())
        self.assertEqual(rows[0]['record'], r.original_record('started'))
        self.assertEqual(rows[1]['record'], r.original_record('rejected'))
        self.assertEqual(hashlib.sha256(HELPER.read_bytes()).hexdigest(), r.HELPER_SHA256)

    def test_200_single_post_exact_wire_digest_and_durable_pair(self):
        value = self.f.run()
        self.assertEqual(value['state'], 'received')
        self.assertEqual(len(self.f.posts), 1)
        self.assertEqual([v['state'] for v in self.f.writes], ['started', 'received'])
        payload = json.dumps(r._payload(self.f.contract)).encode()
        self.assertEqual(self.f.posts[0], ('POST', r.ENDPOINT, payload))
        for record in self.f.writes:
            self.assertEqual(record['attempt'], 2)
            self.assertEqual(record['lifetimeAttempt'], 2)
            self.assertEqual(record['maximumTotalPostAttempts'], 2)
            self.assertEqual(record['requestSha256'], hashlib.sha256(payload).hexdigest())
            self.assertEqual(record['requestBytes'], len(payload))
            self.assertEqual(record['originalFingerprint'], r.CHAIN['originalFingerprint'])
        self.assertEqual(value['response']['bodySha256'], hashlib.sha256(self.f.body).hexdigest())
        self.assertEqual(value['response']['bodyBytes'], len(self.f.body))
        r.audit_chain(self.f.read_page, self.f.contract)

    def test_202_receipt_state_and_no_claim_of_indexing(self):
        self.f.status = 202
        value = self.f.run()
        self.assertEqual(value['state'], 'received_key_validation_pending')
        self.assertEqual(value['searchIndexing'], 'not_verified')

    def test_accepted_same_chain_reuses_after_public_gets_without_post_or_writes(self):
        self.f.run()
        self.f.calls.clear()
        self.f.writes.clear()
        value = self.f.run()
        self.assertEqual(value['state'], 'already_received')
        self.assertTrue(self.f.calls)
        self.assertTrue(all(call[0] == 'GET' for call in self.f.calls))
        self.assertEqual(self.f.writes, [])

    def test_accepted_different_successor_never_reused(self):
        self.f.run()
        self.f.calls.clear()
        self.f.binding = r.Binding('d' * 40, self.f.binding.control_revision,
                                   self.f.binding.artifact_sha256, self.f.binding.run_url)
        self.blocked('actual_release_binding_required')
        self.assertEqual(self.f.calls, [])

    def test_accepted_reuse_rechecks_live_revision(self):
        self.f.run()
        self.f.calls.clear()
        self.f.public[r.HOME] = self.f.public[r.HOME].replace(r.CHAIN['originalSourceRevision'].encode(), b'd' * 40)
        self.blocked()
        self.assertEqual(self.f.posts, [])

    def test_accepted_reuse_requires_full_public_preflight(self):
        self.f.run()
        self.f.calls.clear()
        self.f.full_public = False
        self.blocked('full_public_release_not_verified')
        self.assertEqual(self.f.calls, [])

    def test_429_one_post_one_started_no_sleep_retry(self):
        self.f.status = 429
        self.f.headers += [('retry-after', '1')]
        self.blocked('automatic_retry_forbidden')
        self.assertEqual(len(self.f.posts), 1)
        self.assertEqual([v['state'] for v in self.f.writes], ['started', 'rejected'])
        self.f.calls.clear()
        self.blocked('recovery_budget_spent_or_unknown')
        self.assertEqual(self.f.calls, [])

    def test_429_long_or_malformed_delay_never_retries(self):
        for delay in ('99999999', 'bad\nheader', 'not-a-date'):
            with self.subTest(delay=delay), tempfile.TemporaryDirectory() as directory:
                fixture = Fixture(Path(directory))
                fixture.status = 429
                fixture.headers += [('retry-after', delay)]
                with self.assertRaises(r.RecoveryBlocked):
                    fixture.run()
                self.assertEqual(len(fixture.posts), 1)
                self.assertEqual(sum(v['state'] == 'started' for v in fixture.writes), 1)

    def test_new_rejected_receipt_blocks_every_followup_attempt(self):
        self.f.status = 422
        self.blocked()
        self.assertEqual(len(self.f.posts), 1)
        self.f.calls.clear()
        self.blocked('recovery_budget_spent_or_unknown')
        self.assertEqual(self.f.calls, [])

    def test_timeout_leaves_started_unknown_and_never_replays(self):
        self.f.throw_post = RuntimeError('password=NOT_FOR_LOGS')
        self.blocked()
        self.assertEqual([v['state'] for v in self.f.writes], ['started', 'unknown'])
        self.assertNotIn('NOT_FOR_LOGS', json.dumps(self.f.writes))
        self.f.calls.clear()
        self.blocked('recovery_budget_spent_or_unknown')
        self.assertEqual(self.f.calls, [])

    def test_started_alone_blocks_even_changed_source_and_key_budget(self):
        self.f.throw_write = lambda record: record['state'] != 'started'
        self.blocked('durable_journal_write_unconfirmed')
        self.assertEqual([v['state'] for v in self.f.writes], ['started'])
        self.f.calls.clear()
        self.f.binding = r.Binding('d' * 40, 'e' * 40, 'f' * 64, self.f.binding.run_url)
        self.blocked('actual_release_binding_required')
        self.assertEqual(self.f.calls, [])

    def test_failed_started_write_prevents_post(self):
        self.f.throw_write = lambda record: True
        self.blocked('durable_journal_write_unconfirmed')
        self.assertEqual(self.f.posts, [])

    def test_started_write_without_live_readback_prevents_post(self):
        def nondurable(record):
            return comment(7000000001, record)
        self.blocked('own_durable_started_not_exclusive', write_record=nondurable)
        self.assertEqual(self.f.posts, [])

    def test_write_that_persisted_then_raised_prevents_post_and_replay(self):
        def uncertain(record):
            self.f.write_record(record)
            raise RuntimeError('uncertain')
        self.blocked('durable_journal_write_unconfirmed', write_record=uncertain)
        self.assertEqual(self.f.posts, [])
        self.blocked('prior_recovery_outcome_uncertain')

    def test_failed_terminal_write_after_post_leaves_started(self):
        self.f.throw_write = lambda record: record['state'] != 'started'
        self.blocked('durable_journal_write_unconfirmed')
        self.assertEqual(len(self.f.posts), 1)
        self.assertEqual([v['state'] for v in self.f.writes], ['started'])
        self.f.calls.clear()
        self.blocked('prior_recovery_outcome_uncertain')
        self.assertEqual(self.f.calls, [])

    def test_malformed_diagnostics_after_post_leave_unknown(self):
        for headers in ({'content-type': 'text/plain'}, [('bad', object())],
                        [('bad\nname', 'x')], [('date', 'x' * 4097)]):
            with self.subTest(headers_type=type(headers).__name__), tempfile.TemporaryDirectory() as directory:
                fixture = Fixture(Path(directory))
                fixture.headers = headers
                with self.assertRaises(r.RecoveryBlocked):
                    fixture.run()
                self.assertEqual(len(fixture.posts), 1)
                self.assertEqual([v['state'] for v in fixture.writes], ['started', 'unknown'])
                fixture.calls.clear()
                with self.assertRaises(r.RecoveryBlocked):
                    fixture.run()
                self.assertEqual(fixture.calls, [])

    def test_unbounded_response_after_post_leaves_unknown(self):
        self.f.body = b'x' * (r.MAX_RESPONSE + 1)
        self.blocked()
        self.assertEqual([v['state'] for v in self.f.writes], ['started', 'unknown'])

    def test_safe_diagnostics_redact_both_proofs_and_credentials(self):
        self.f.status = 422
        self.f.body = json.dumps({'message': self.f.contract.active_key + ' ' + self.f.contract.retained_key
                          + ' password=secretpass Bearer bearer-secret-value ghp_' + 'Z' * 35,
                          'token': 'NEVER_KEEP', 'nested': {'password': 'NEVER_KEEP'}}).encode()
        self.f.headers += [('set-cookie', 'secret=NEVER_KEEP'), ('authorization', 'Bearer NEVER_KEEP'),
                           ('x-request-id', self.f.contract.active_key)]
        self.blocked()
        receipt = self.f.writes[-1]
        stored = json.dumps(receipt)
        for secret in (self.f.contract.active_key, self.f.contract.retained_key,
                       'secretpass', 'bearer-secret-value', 'NEVER_KEEP', 'Z' * 35):
            self.assertNotIn(secret, stored)
        self.assertIn('[REDACTED]', receipt['response']['sanitizedText'])
        self.assertEqual(receipt['response']['bodySha256'], hashlib.sha256(self.f.body).hexdigest())

    def test_ambiguous_credential_text_omitted_for_plain_and_json(self):
        for content in ('password is abc', 'secret abc', 'token abc', 'key abc',
                        '\"password\" \"abc\"', 'credential abc', 'api key is abc'):
            for content_type in ('text/plain', 'application/json'):
                body = (json.dumps({'message': content}) if content_type == 'application/json' else content).encode()
                with self.subTest(content_type=content_type):
                    value = r.diagnostics(r.RawResponse(422, body, [('content-type', content_type)]), self.f.contract)
                    self.assertNotIn('sanitizedText', value)
                    self.assertEqual(value['bodyBytes'], len(body))
                    forged = {**value, 'sanitizedText': body.decode()}
                    with self.assertRaises(r.RecoveryBlocked):
                        r.validate_diagnostics(forged, self.f.contract)

    def test_unsafe_malformed_text_omitted_but_raw_digest_kept(self):
        cases = [(b'\xff\xfe', 'text/plain'), (b'<html>secret</html>', 'text/plain'),
                 (b'{invalid', 'application/json'), (b'\x00secret', 'text/plain'),
                 (b'x' * 4097, 'text/plain'), (b'text', 'text/html'),
                 (b'{"message":"first","message":"second"}', 'application/json')]
        for body, content_type in cases:
            with self.subTest(body_length=len(body)):
                diagnostic = r.diagnostics(r.RawResponse(422, body, [('content-type', content_type)]), self.f.contract)
                self.assertNotIn('sanitizedText', diagnostic)
                self.assertEqual(diagnostic['bodySha256'], hashlib.sha256(body).hexdigest())
                self.assertEqual(diagnostic['bodyBytes'], len(body))

    def test_stored_diagnostics_revalidate_header_grammar_and_text(self):
        good = r.diagnostics(r.RawResponse(200, b'{"message":"safe"}',
                              [('content-type', 'application/json')]), self.f.contract)
        for name, value in [('content-type', 'text/html'), ('date', 'nonsense'),
                            ('content-type', 'application/json;\ncharset=utf-8'),
                            ('content-type', 'text/plain;charset=' + self.f.contract.active_key),
                            ('date', 'Fri, 16 Oct 2026 09:00:00 GMT abc'),
                            ('retry-after', '-1'), ('x-request-id', '<html>bad</html>'),
                            ('x-request-id', 'line\nbreak'), ('x-request-id', self.f.contract.active_key)]:
            mutated = copy.deepcopy(good)
            mutated['safeHeaders'][name] = value
            with self.subTest(name=name), self.assertRaises(r.RecoveryBlocked):
                r.validate_diagnostics(mutated, self.f.contract)
        for text in ('<html>bad</html>', '{broken', '{"password":"not-allowed"}',
                     '{"message":"' + self.f.contract.active_key + '"}'):
            mutated = {**good, 'sanitizedText': text}
            with self.subTest(text_type='omitted'), self.assertRaises(r.RecoveryBlocked):
                r.validate_diagnostics(mutated, self.f.contract)

    def test_problem_json_and_safe_escaped_text_roundtrip(self):
        good = r.diagnostics(r.RawResponse(422, b'{"detail":"line one\\nline two"}',
                              [('content-type', 'application/problem+json')]), self.f.contract)
        self.assertEqual(good['safeHeaders']['content-type'], 'application/problem+json')
        r.validate_diagnostics(good, self.f.contract)

    def test_malformed_write_metadata_leaves_safe_error_and_no_post(self):
        for body in (None, {}, 'missing-marker'):
            def write(record):
                saved = self.f.write_record(record)
                saved['body'] = body
                return saved
            with self.subTest(body_type=type(body).__name__), tempfile.TemporaryDirectory() as directory:
                fixture = Fixture(Path(directory))
                def local_write(record):
                    saved = fixture.write_record(record)
                    saved['body'] = body
                    return saved
                with self.assertRaisesRegex(r.RecoveryBlocked, '^[a-z0-9_]+$'):
                    fixture.run(write_record=local_write)
                self.assertEqual(fixture.posts, [])

    def test_old_proof_or_changed_key_not_accepted(self):
        for key in ('0'*32, 'different-public-proof'):
            site = self.f.site()
            site['indexnowKey'] = key
            with self.subTest(key='omitted'), self.assertRaisesRegex(r.RecoveryBlocked, 'fixed_site_configuration_required'):
                self.f.adapter().run(self.f.root, site)
        self.assertEqual(self.f.calls, [])

    def test_foreign_site_host_or_site_key_blocked(self):
        for name, value in [('siteUrl', 'https://example.com'), ('siteKey', 'other'),
                            ('siteUrl', r.ORIGIN + '/'), ('productionEnabled', 1)]:
            site = self.f.site()
            site[name] = value
            with self.subTest(name=name), self.assertRaises(r.RecoveryBlocked):
                self.f.adapter().run(self.f.root, site)
        self.assertEqual(self.f.calls, [])

    def test_foreign_or_extra_sitemap_url_cannot_post(self):
        for location in ('https://other.example/', r.ORIGIN + '/extra'):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as directory:
                fixture = Fixture(Path(directory))
                fixture.public[r.ORIGIN + '/sitemap-0.xml'] = ('<urlset><url><loc>' + location + '</loc></url></urlset>').encode()
                with self.assertRaises(r.RecoveryBlocked):
                    fixture.run()
                self.assertEqual(fixture.posts, [])
                self.assertEqual(fixture.writes, [])

    def test_active_public_proof_requires_exact_bytes(self):
        self.f.public[r.ORIGIN + '/' + self.f.contract.active_key + '.txt'] = (self.f.contract.active_key + '\n\n').encode()
        self.blocked()
        self.assertEqual(self.f.posts, [])

    def test_spoofed_bot_identity_is_blocked(self):
        for field, value in [('id', 1), ('login', 'github-actions'), ('type', 'User')]:
            original = self.f.comments[0]['user'][field]
            self.f.comments[0]['user'][field] = value
            with self.subTest(field=field):
                self.blocked('untrusted_relevant_journal_author')
            self.f.comments[0]['user'][field] = original
        self.assertEqual(self.f.calls, [])

    def test_original_body_id_issue_and_status_are_exact(self):
        mutations = [('attempt', 2), ('httpStatus', 200), ('revision', 'f' * 40),
                     ('fingerprint', '0' * 64), ('extra', True), ('attempt', True)]
        original = copy.deepcopy(self.f.comments)
        for key, value in mutations:
            self.f.comments = copy.deepcopy(original)
            record = json.loads(self.f.comments[1]['body'][len(r.MARKER):])
            record[key] = value
            self.f.comments[1]['body'] = r.MARKER + json.dumps(record)
            with self.subTest(key=key):
                self.blocked('original_receipt_bytes_or_time_changed')
        self.f.comments = copy.deepcopy(original)
        self.f.comments[1]['issue_url'] = r.API_BASE + '/issues/378'
        self.blocked('unexpected_relevant_receipt_location')
        self.assertEqual(self.f.calls, [])

    def test_unexpected_relevant_record_other_fingerprint_or_site_blocks(self):
        for changes in ({'fingerprint': 'e' * 64}, {'siteKey': 'other'},
                        {'origin': 'https://other.example', 'siteKey': 'other', 'fingerprint': 'e' * 64}):
            record = {**r.original_record('rejected'), **changes}
            self.f.comments.append(comment(7000000001, record))
            with self.subTest(changes=changes):
                self.blocked()
            self.f.comments.pop()
        self.assertEqual(self.f.calls, [])

    def test_duplicate_original_or_successor_chain_blocks(self):
        self.f.comments.append(copy.deepcopy(self.f.comments[-1]))
        self.blocked('duplicate_or_invalid_journal_comment')
        self.f.comments.pop()
        self.f.run()
        self.f.comments.append(comment(8000000001, copy.deepcopy(self.f.writes[0])))
        self.f.calls.clear()
        self.blocked('duplicate_or_excess_recovery_chain')
        self.assertEqual(self.f.calls, [])

    def test_reset_attempt_or_missing_lineage_cannot_reuse_accepted(self):
        self.f.run()
        original = copy.deepcopy(self.f.comments)
        for field, value in [('attempt', 1), ('lifetimeAttempt', 1), ('maximumTotalPostAttempts', 3),
                             ('originalFingerprint', '0' * 64), ('originalReceiptIssue', 378)]:
            self.f.comments = copy.deepcopy(original)
            for c in self.f.comments[2:]:
                data = json.loads(c['body'][len(r.MARKER):])
                data[field] = value
                c['body'] = r.MARKER + json.dumps(data)
            with self.subTest(field=field):
                self.blocked('successor_chain_or_budget_mismatch')
        self.f.comments = copy.deepcopy(original)
        data = json.loads(self.f.comments[-1]['body'][len(r.MARKER):])
        del data['originalFingerprint']
        self.f.comments[-1]['body'] = r.MARKER + json.dumps(data)
        self.blocked('unexpected_successor_record_schema')

    def test_truncated_or_wrong_pagination_cannot_post(self):
        transforms = [lambda n, p: r.AuditPage(p.url, 200, p.comments, None, False),
                      lambda n, p: r.AuditPage(r.ISSUE_URL + '/comments', 200, p.comments, None, True),
                      lambda n, p: r.AuditPage(p.url, 206, p.comments, None, True),
                      lambda n, p: r.AuditPage(p.url, 200, p.comments, r.page_url(2), True)]
        for transform in transforms:
            self.f.page_transform = transform
            self.blocked()
        self.assertEqual(self.f.calls, [])

    def test_full_pages_audit_later_unexpected_record(self):
        # Ordinary comments fill page 1. The original pair is on page 2.
        filler = [{'id': n, 'body': 'ordinary comment'} for n in range(1, 101)]
        self.f.comments = filler + self.f.comments
        self.f.run()
        self.assertIn(2, self.f.page_calls)
        extra = r.original_record('rejected')
        self.f.comments.append(comment(8000000001, extra))
        self.f.calls.clear()
        self.blocked('duplicate_or_excess_recovery_chain')
        self.assertEqual(self.f.calls, [])

    def test_full_final_page_without_next_is_ambiguous(self):
        self.f.comments += [{'id': 8000000000 + n, 'body': 'ordinary'} for n in range(98)]
        self.blocked('ambiguous_full_final_page')
        self.assertEqual(self.f.calls, [])

    def test_journal_reread_before_started_catches_new_record(self):
        counter = {'reads': 0}
        def read(number):
            counter['reads'] += 1
            if counter['reads'] == 3:
                self.f.comments.append(comment(8000000001, r.original_record('rejected')))
            return self.f.read_page(number)
        self.blocked(read_page=read)
        self.assertEqual(self.f.writes, [])
        self.assertEqual(self.f.posts, [])

    def test_competing_started_after_write_blocks_post(self):
        def write(record):
            saved = self.f.write_record(record)
            self.f.comments.append(comment(8000000001, copy.deepcopy(record)))
            return saved
        self.blocked('own_durable_started_not_exclusive', write_record=write)
        self.assertEqual(self.f.posts, [])

    def test_second_post_and_started_cannot_pass_guard(self):
        adapter = self.f.adapter()
        adapter.run(self.f.root, self.f.site())
        with self.assertRaisesRegex(r.RecoveryBlocked, 'single_durable_post_only'):
            adapter.transport('POST', r.ENDPOINT, r._payload(self.f.contract))
        record = {**r._identity(self.f.binding.source_revision), 'attempt': 1, 'state': 'started',
                  'fingerprint': r._fingerprint(self.f.contract, self.f.binding.source_revision),
                  'runUrl': self.f.binding.run_url, 'recordedAt': self.f.writes[0]['recordedAt']}
        with self.assertRaisesRegex(r.RecoveryBlocked, 'second_started_or_attempt_forbidden'):
            adapter.write(record)
        self.assertEqual(len(self.f.posts), 1)
        self.assertEqual(sum(x['state'] == 'started' for x in self.f.writes), 1)

    def test_foreign_post_endpoint_or_payload_blocked(self):
        adapter = self.f.adapter()
        payload = r._payload(self.f.contract)
        cases = [('https://other.example/indexnow', payload)]
        cases.append((r.ENDPOINT, dict(reversed(list(payload.items())))))
        for field, value in [('host', 'other.example'), ('urlList', [r.HOME, r.HOME + 'other']),
                             ('key', '0'*32), ('extra', 'unexpected')]:
            cases.append((r.ENDPOINT, {**payload, field: value}))
        for endpoint, data in cases:
            with self.subTest(endpoint=endpoint), self.assertRaisesRegex(r.RecoveryBlocked, 'fixed_post_payload_required'):
                adapter.transport('POST', endpoint, data)
        self.assertEqual(self.f.calls, [])

    def test_missing_serialization_or_binding_validation_blocks(self):
        self.f.serialized = False
        self.blocked('shared_serialization_not_verified')
        self.f.serialized = True
        self.f.valid_binding = False
        self.blocked('release_binding_not_verified')
        self.assertEqual(self.f.calls, [])

    def test_local_concurrency_lock_blocks(self):
        r._LOCK.acquire()
        try:
            self.blocked('concurrent_local_recovery_forbidden')
        finally:
            r._LOCK.release()
        self.assertEqual(self.f.calls, [])

    def test_mutated_shared_helper_rejected_before_execution(self):
        helper = self.f.root / 'helper.py'
        helper.write_bytes(HELPER.read_bytes() + b'\n')
        with self.assertRaisesRegex(r.RecoveryBlocked, 'unchanged_shared_helper_required'):
            self.f.adapter(helper_path=helper)
        self.assertEqual(self.f.calls, [])

    def test_duplicate_json_keys_rejected(self):
        self.f.comments[1]['body'] = r.MARKER + '{"origin":"' + r.ORIGIN + '","origin":"other"}'
        self.blocked('duplicate_journal_json_key')
        self.assertEqual(self.f.calls, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
