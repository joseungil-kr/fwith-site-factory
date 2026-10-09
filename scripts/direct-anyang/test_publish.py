"""Read-only regression tests for the fixed direct Anyang publisher."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, os.environ.get('DIRECT_ANYANG_TEST_ENGINE', str(ROOT / 'site-factory/engine')))
spec = importlib.util.spec_from_file_location('publish', Path(__file__).with_name('publish.py'))
pub = importlib.util.module_from_spec(spec); spec.loader.exec_module(pub)
ACCOUNT = '1' * 32


class Provider:
    def __init__(self, scripts=None, domains=None, account=ACCOUNT, info=None):
        self.scripts, self.domains, self.account, self.info = scripts or [], domains or [], account, info
        self.calls = []
    def __call__(self, method, path, body=None):
        self.calls.append((method, path, body))
        if path.endswith('/workers/scripts'):
            value = dict(success=True, result=[{'id': name} for name in self.scripts])
        elif path.endswith('/workers/domains'):
            value = dict(success=True, result=self.domains)
            if self.info is not None: value['result_info'] = self.info
        else:
            value = dict(success=True, result={'id': self.account})
        return value


def binding(host=pub.HOSTNAME, worker=pub.WORKER):
    return {'hostname': host, 'service': worker}


class PublishTests(unittest.TestCase):
    def test_fixed_route_set(self):
        self.assertEqual(len(pub.SLUGS), 7)
        self.assertEqual(len(pub.ROUTES), 9)
        self.assertFalse(set(pub.DEFERRED) & pub.ROUTES)

    def test_absent_initial_target_allowed_get_only(self):
        p = Provider(['unrelated'], [binding('unrelated.fwith.kr', 'unrelated')])
        r = pub.inspect_provider(ACCOUNT, p, 'preflight')
        self.assertEqual(r['state'], 'target_absent_verified')
        self.assertTrue(all(c[0] == 'GET' and c[2] is None for c in p.calls))

    def test_same_exact_binding_allowed(self):
        p = Provider([pub.WORKER], [binding()])
        self.assertEqual(pub.inspect_provider(ACCOUNT, p, 'preflight')['state'], 'binding_verified')
        self.assertEqual(pub.inspect_provider(ACCOUNT, p, 'readback')['state'], 'binding_verified')

    def test_hostname_other_worker_collision(self):
        with self.assertRaisesRegex(ValueError, 'hostname_or_worker_collision'):
            pub.inspect_provider(ACCOUNT, Provider(['other'], [binding(worker='other')]), 'preflight')

    def test_worker_other_hostname_collision(self):
        with self.assertRaisesRegex(ValueError, 'hostname_or_worker_collision'):
            pub.inspect_provider(ACCOUNT, Provider([pub.WORKER], [binding(host='other.fwith.kr')]), 'preflight')

    def test_unbound_existing_worker_blocked(self):
        with self.assertRaisesRegex(ValueError, 'unbound_existing_worker_requires_review'):
            pub.inspect_provider(ACCOUNT, Provider([pub.WORKER]), 'preflight')

    def test_wrong_account_blocked(self):
        with self.assertRaisesRegex(ValueError, 'account_identity_mismatch'):
            pub.inspect_provider(ACCOUNT, Provider(account='2' * 32), 'preflight')

    def test_duplicate_bindings_blocked(self):
        with self.assertRaisesRegex(ValueError, 'hostname_or_worker_collision'):
            pub.inspect_provider(ACCOUNT, Provider([pub.WORKER], [binding(), binding()]), 'preflight')

    def test_incomplete_inventory_blocked(self):
        with self.assertRaises(Exception):
            pub.inspect_provider(ACCOUNT, Provider(info={'total_count': 3, 'count': 0}), 'preflight')

    def test_readback_requires_actual_binding(self):
        with self.assertRaisesRegex(ValueError, 'exact_binding_not_observed'):
            pub.inspect_provider(ACCOUNT, Provider([pub.WORKER]), 'readback')

    def test_native_attach_all_overrides_false(self):
        native, _ = pub.helpers(); calls = []
        def transport(method, path, body):
            calls.append((method, path, body)); return {'success': True}
        native.attach(transport, ACCOUNT)
        self.assertEqual(len(calls), 1)
        method, path, body = calls[0]
        self.assertEqual(method, 'PUT')
        self.assertEqual(path, '/accounts/' + ACCOUNT + '/workers/scripts/' + pub.WORKER + '/domains/records')
        self.assertEqual(body, dict(override_scope=False, override_existing_origin=False,
             override_existing_dns_record=False, origins=[dict(hostname=pub.HOSTNAME, zone_name='fwith.kr')]))

    def test_page_duplicate_metadata_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_metadata'):
            pub.Page('<meta name="robots" content="index"><meta name="robots" content="noindex">')

    def test_cloudflare_beacon_only_normalization(self):
        expected = b'<html><body>Exact content</body></html>'
        beacon = b'<script defer src="https://static.cloudflareinsights.com/beacon.min.js/v1" data-cf-beacon="{}"></script>'
        body = expected.replace(b'</body>', beacon + b'</body>')
        self.assertEqual(pub.strip_one_cf_beacon(body, pub.sha(expected)), expected)
        with self.assertRaises(AssertionError):
            pub.strip_one_cf_beacon(body.replace(b'Exact', b'Changed'), pub.sha(expected))
        with self.assertRaises(AssertionError):
            pub.strip_one_cf_beacon(body.replace(beacon, beacon + beacon), pub.sha(expected))

    def test_nonlocal_url_rejected(self):
        for url in ['https://other.fwith.kr/', pub.ORIGIN + '/../../file', pub.ORIGIN + '//file', pub.ORIGIN + '/?q=1']:
            with self.assertRaises(ValueError): pub.local_path(url)


if __name__ == '__main__':
    unittest.main()
