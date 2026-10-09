"""Read-only regression tests for the fixed direct Anyang publisher."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from email.message import Message
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
        self.assertEqual(len(pub.ARTICLE_ROUTES), 12)
        self.assertEqual(len(pub.ROUTES), 16)
        self.assertEqual(len(pub.SITEMAP_ROUTES), 15)
        self.assertEqual(pub.THIN_HUB_ROUTES, {'/event/'})
        self.assertEqual(pub.ROUTES - pub.SITEMAP_ROUTES, pub.THIN_HUB_ROUTES)
        self.assertTrue(pub.REGION_ROUTES <= pub.SITEMAP_ROUTES)
        self.assertTrue(pub.ADDED_ROUTES <= pub.SITEMAP_ROUTES)
        self.assertFalse(set(pub.DEFERRED) & pub.ROUTES)

    def test_explicit_thin_hub_robots_only(self):
        self.assertEqual(pub.expected_robots('/event/'), {'noindex', 'follow'})
        for route in pub.SITEMAP_ROUTES:
            self.assertEqual(pub.expected_robots(route), {'index', 'follow'})
        self.assertEqual(pub.expected_robots('/404.html'), {'noindex', 'nofollow', 'noarchive'})

    def test_bound_update_attach_is_get_only(self):
        p = Provider([pub.WORKER], [binding()])
        with patch.object(pub, 'provider_transport', return_value=(ACCOUNT, p)):
            result = pub.provider('attach')
        self.assertEqual(result['state'], 'binding_verified')
        self.assertFalse(result['mutationsPerformed'])
        self.assertTrue(all(method == 'GET' and body is None for method, path, body in p.calls))

    def test_http_contract_fails_before_network_on_missing_route(self):
        with patch.object(pub, 'get', side_effect=AssertionError('network must not run')):
            with self.assertRaisesRegex(ValueError, 'http_contract_routes_mismatch'):
                pub.http_once({'pages': []})

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


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_cwd = Path.cwd()
        os.chdir(self.temp.name)
        self.env = patch.dict(os.environ, dict(REVISION='a' * 40, GITHUB_REPOSITORY=pub.REPOSITORY,
                              GITHUB_SHA='b' * 40, GITHUB_RUN_ID='fixture'))
        self.env.start()
        self.root = Path('release/dist'); self.root.mkdir(parents=True)
        for route in pub.ROUTES:
            file = self.root / (route.lstrip('/') + 'index.html'); file.parent.mkdir(parents=True, exist_ok=True)
            robots = ','.join(sorted(pub.expected_robots(route)))
            file.write_text('<html><head><meta name="site-factory-revision" content="' + 'a' * 40 +
                '"><meta name="robots" content="' + robots + '"><link rel="canonical" href="' +
                pub.ORIGIN + route + '"></head><body><a href="tel:18440644">Call</a>' +
                '<a href="https://fwith.co.kr">Order</a><img src="/image.webp" alt="Verified product"></body></html>')
        (self.root / '404.html').write_text('<meta name="site-factory-revision" content="' + 'a' * 40 +
                '"><meta name="robots" content="noindex,nofollow,noarchive">Missing')
        (self.root / 'image.webp').write_bytes(b'fixture-image')
        (self.root / '_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n')
        (self.root / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: ' + pub.ORIGIN + '/sitemap-index.xml\n')
        (self.root / 'ownership123.txt').write_text('ownership123')
        (self.root / 'sitemap-index.xml').write_text('<sitemapindex><sitemap><loc>' + pub.ORIGIN + '/sitemap-0.xml</loc></sitemap></sitemapindex>')
        (self.root / 'sitemap-0.xml').write_text('<urlset>' + ''.join('<url><loc>' + pub.ORIGIN +
                route + '</loc></url>' for route in sorted(pub.SITEMAP_ROUTES)) + '</urlset>')
        self.seal()

    def tearDown(self):
        self.env.stop(); os.chdir(self.original_cwd); self.temp.cleanup()

    def seal(self):
        pub.save('release/release.json', dict(**pub.identity(), files=pub.inventory(self.root)))
        os.environ['RELEASE_SHA256'] = pub.sha(Path('release/release.json').read_bytes())

    def test_exact_fixed_artifact_and_http_counts(self):
        result = pub.artifact()
        self.assertEqual((result['articleCount'], result['sitemapUrls'], result['htmlRoutes']), (12, 15, 16))
        contract = json.loads(Path('http-contract.json').read_text())
        self.assertEqual(next(p['robots'] for p in contract['pages'] if p['path'] == '/event/'), ['follow', 'noindex'])
        def fixture_get(path, status=200):
            headers = Message(); headers['Content-Type'] = 'text/html'
            file = '404.html' if status == 404 else (path.lstrip('/') + 'index.html' if path.endswith('/') else path.lstrip('/'))
            return (self.root / file).read_bytes(), headers
        with patch.object(pub, 'get', side_effect=fixture_get):
            result = pub.http_once(contract)
        self.assertEqual((result['articleCount'], result['sitemapUrls'], result['htmlRoutes']), (12, 15, 16))

    def test_missing_article_is_blocked(self):
        (self.root / 'funeral/anyang-funeral-hall-wreath/index.html').unlink(); self.seal()
        with self.assertRaisesRegex(ValueError, 'exact_reviewed_routes_mismatch'): pub.artifact()

    def test_unreviewed_article_is_blocked(self):
        (self.root / 'unreviewed.html').write_text('Unexpected route'); self.seal()
        with self.assertRaisesRegex(ValueError, 'exact_reviewed_routes_mismatch'): pub.artifact()

    def test_noindexed_article_is_blocked(self):
        file = self.root / 'funeral/anyang-funeral-hall-wreath/index.html'
        file.write_text(file.read_text().replace('follow,index', 'follow,noindex')); self.seal()
        with self.assertRaisesRegex(ValueError, 'robots_meta_mismatch'): pub.artifact()

    def test_indexed_thin_hub_is_blocked(self):
        file = self.root / 'event/index.html'
        file.write_text(file.read_text().replace('follow,noindex', 'follow,index')); self.seal()
        with self.assertRaisesRegex(ValueError, 'robots_meta_mismatch'): pub.artifact()

    def test_thin_hub_in_sitemap_is_blocked(self):
        file = self.root / 'sitemap-0.xml'
        file.write_text(file.read_text().replace('</urlset>', '<url><loc>' + pub.ORIGIN + '/event/</loc></url></urlset>')); self.seal()
        with self.assertRaisesRegex(ValueError, 'sitemap_exact_reviewed_urls_mismatch'): pub.artifact()


if __name__ == '__main__':
    unittest.main()
