import copy
import json
import unittest
from provider_readonly import authorize, inspect, make_transport, single_page, Rejected, REPOSITORY, OWNER, HOSTNAME, WORKER, TITLE

ACCOUNT = 'a' * 32
REVISION = 'b' * 40


def authorized_request():
    env = dict(GITHUB_REPOSITORY=REPOSITORY, GITHUB_REF='refs/heads/main', GITHUB_ACTOR=OWNER,
               GITHUB_RUN_ATTEMPT='1', GITHUB_EVENT_NAME='issues', GITHUB_SHA=REVISION)
    body = dict(schemaVersion=1, expected_control_revision=REVISION, hostname=HOSTNAME, worker=WORKER, read_only=True)
    event = dict(action='opened', repository=dict(full_name=REPOSITORY, owner=dict(login=OWNER, type='User')),
                 issue=dict(title=TITLE, user=dict(login=OWNER), body=json.dumps(body)))
    return env, event


def payloads():
    return [dict(success=True, result=dict(id=ACCOUNT)), dict(success=True, result=[]), dict(success=True, result=[])]


def transport_for(data, calls):
    def transport(method, path, body=None):
        calls.append((method, path, body))
        return data[len(calls) - 1]
    return transport


class ProviderReadOnly(unittest.TestCase):
    def test_exact_request(self):
        env, event = authorized_request()
        self.assertEqual(authorize(env, event), REVISION)

    def test_event_guards(self):
        for key, value in [('GITHUB_REPOSITORY', 'other/repo'), ('GITHUB_REF', 'refs/heads/other'),
                           ('GITHUB_ACTOR', 'other'), ('GITHUB_RUN_ATTEMPT', '2'), ('GITHUB_EVENT_NAME', 'workflow_dispatch'),
                           ('GITHUB_SHA', 'short')]:
            with self.subTest(key=key):
                env, event = authorized_request(); env[key] = value
                with self.assertRaises(Rejected): authorize(env, event)

    def test_issue_scope(self):
        for key, value in [('title', 'other'), ('user', {'login': 'other'}), ('body', '{}')]:
            with self.subTest(key=key):
                env, event = authorized_request(); event['issue'][key] = value
                with self.assertRaises(Rejected): authorize(env, event)

    def test_request_body_scope(self):
        for key, value in [('read_only', False), ('hostname', 'other.fwith.kr'), ('worker', 'other'),
                           ('expected_control_revision', 'c' * 40), ('extra', 'not-allowed')]:
            with self.subTest(key=key):
                env, event = authorized_request(); body = json.loads(event['issue']['body']); body[key] = value
                event['issue']['body'] = json.dumps(body)
                with self.assertRaises(Rejected): authorize(env, event)

    def test_only_three_reads_and_redacted_absence(self):
        calls = []; report = inspect(ACCOUNT, transport_for(payloads(), calls))
        self.assertEqual(calls, [('GET', '/accounts/' + ACCOUNT, None),
                                ('GET', '/accounts/' + ACCOUNT + '/workers/scripts', None),
                                ('GET', '/accounts/' + ACCOUNT + '/workers/domains', None)])
        self.assertEqual(report['state'], 'target_absent_observed')
        self.assertNotIn(ACCOUNT, json.dumps(report))
        self.assertFalse(report['dnsOwnershipVerified']); self.assertFalse(report['publicationAuthorizedByThisReport'])

    def test_existing_exact_binding(self):
        data = payloads(); data[1]['result'] = [dict(id=WORKER)]
        data[2]['result'] = [dict(hostname=HOSTNAME, service=WORKER)]
        self.assertEqual(inspect(ACCOUNT, transport_for(data, []))['state'], 'exact_binding_observed')

    def test_worker_present_unbound(self):
        data = payloads(); data[1]['result'] = [dict(id=WORKER)]
        self.assertEqual(inspect(ACCOUNT, transport_for(data, []))['state'], 'worker_present_unbound')

    def test_collision_and_invalid_binding(self):
        rows = [[dict(hostname=HOSTNAME, service='other')], [dict(hostname='other.fwith.kr', service=WORKER)],
                [dict(hostname=HOSTNAME, service=WORKER), dict(hostname=HOSTNAME, service=WORKER)],
                [dict(hostname=HOSTNAME, service=WORKER, enabled=False)],
                [dict(hostname=HOSTNAME, service=WORKER, environment='staging')],
                [dict(hostname=HOSTNAME, service=WORKER, previews_enabled=True)],
                [dict(hostname=HOSTNAME, service=WORKER, zone_name='other.kr')]]
        for row in rows:
            with self.subTest(row=row):
                data = payloads(); data[1]['result'] = [dict(id=WORKER)]; data[2]['result'] = row
                with self.assertRaises(Rejected): inspect(ACCOUNT, transport_for(data, []))

    def test_binding_without_worker(self):
        data = payloads(); data[2]['result'] = [dict(hostname=HOSTNAME, service=WORKER)]
        with self.assertRaises(Rejected): inspect(ACCOUNT, transport_for(data, []))

    def test_incomplete_inventory(self):
        for info in [{'page': 2}, {'total_pages': 2}, {'total_count': 1}, {'count': 1}, {'per_page': -1}, {'page': True}]:
            with self.subTest(info=info):
                with self.assertRaises(Rejected): single_page(dict(success=True, result=[], result_info=info))

    def test_invalid_account_and_duplicate_scripts(self):
        data = payloads(); data[0]['result']['id'] = 'other'
        with self.assertRaises(Rejected): inspect(ACCOUNT, transport_for(data, []))
        data = payloads(); data[1]['result'] = [dict(id=WORKER), dict(id=WORKER)]
        with self.assertRaises(Rejected): inspect(ACCOUNT, transport_for(data, []))

    def test_no_mutation_dns_or_content_transport(self):
        transport = make_transport(ACCOUNT, 'TEST-ONLY-NOT-A-CREDENTIAL', {})
        for method, path, body in [('POST', '/accounts/' + ACCOUNT, None), ('PUT', '/accounts/' + ACCOUNT + '/workers/domains', {}),
                                   ('GET', '/zones', None), ('GET', '/accounts/' + ACCOUNT + '/workers/scripts/' + WORKER, None),
                                   ('GET', '/accounts/' + ACCOUNT, {})]:
            with self.subTest(method=method, path=path):
                with self.assertRaises(Rejected): transport(method, path, body)


if __name__ == '__main__':
    unittest.main()
