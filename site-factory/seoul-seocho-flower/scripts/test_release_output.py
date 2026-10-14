from pathlib import Path
import copy
import hashlib
import tempfile
import unittest
from qa_release_output import inspect_dist, FILES, ORIGIN, ROUTES


class OutputContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.mode = dict(mode='production', indexable=True, origin=ORIGIN, revision='a' * 40)
        key = 'TEST-ONLY-NOT-FOR-PUBLICATION'
        self.proof = dict(origin=ORIGIN, path='/' + key + '.txt', sha256=hashlib.sha256((key + '\n').encode()).hexdigest())
        for name, route in FILES.items():
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True)
            robots = 'noindex,nofollow,noarchive' if route == '/404.html' else 'noindex,follow' if route == '/regions/' else 'index,follow'
            canonical = '' if route == '/404.html' else '<link rel="canonical" href="' + ORIGIN + route + '">'
            path.write_text('<!doctype html><html><head><meta name="robots" content="' + robots + '"><meta name="site-factory-revision" content="' + self.mode['revision'] + '">' + canonical + '</head><body><h1>Test fixture only</h1></body></html>', encoding='utf-8')
        (self.root / (key + '.txt')).write_bytes((key + '\n').encode('utf-8'))
        (self.root / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: ' + ORIGIN + '/sitemap-index.xml\n', encoding='utf-8')
        (self.root / '_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n', encoding='utf-8')
        (self.root / 'sitemap-index.xml').write_text('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>' + ORIGIN + '/sitemap-0.xml</loc></sitemap></sitemapindex>', encoding='utf-8')
        (self.root / 'sitemap-0.xml').write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>' + ORIGIN + route + '</loc></url>' for route in ROUTES) + '</urlset>', encoding='utf-8')

    def tearDown(self): self.temp.cleanup()

    def check(self): return inspect_dist(self.root, self.mode, self.proof)

    def mutate(self, path, old, new):
        path = self.root / path; path.write_text(path.read_text(encoding='utf-8').replace(old, new), encoding='utf-8')

    def test_exact_fixture(self):
        result = self.check(); self.assertEqual(result['htmlFiles'], 5)
        self.assertEqual(result['notFoundProbe']['expectedStatus'], 404); self.assertFalse(result['publicHTTPVerified'])

    def test_bad_output(self):
        mutations = [
            ('index.html', self.mode['revision'], 'b' * 40),
            ('index.html', 'index,follow', 'noindex,follow'),
            ('regions/index.html', 'noindex,follow', 'index,follow'),
            ('index.html', ORIGIN, 'https://other.fwith.kr'),
            ('404.html', '</head>', '<link rel="canonical" href="' + ORIGIN + '/"></head>'),
            ('404.html', '</head>', '<meta property="og:title" content="wrong"></head>'),
            ('404.html', '</head>', '<script type="application/ld+json">{}</script></head>'),
            ('index.html', '</head>', '<meta name="robots" content="index,follow"></head>'),
            ('index.html', '</body>', '<h1>Duplicate</h1></body>'),
            ('sitemap-0.xml', '</urlset>', '<url><loc>' + ORIGIN + '/regions/</loc></url></urlset>'),
            ('sitemap-0.xml', ROUTES[1], ROUTES[2]),
            ('sitemap-index.xml', ORIGIN, 'https://other.fwith.kr'),
            ('robots.txt', 'Allow: /', 'Disallow: /'),
            ('_headers', '/*', '/*\n  X-Robots-Tag: noindex'),
        ]
        for name, old, new in mutations:
            with self.subTest(name=name, old=old):
                original = (self.root / name).read_bytes()
                self.mutate(name, old, new)
                with self.assertRaises(AssertionError): self.check()
                (self.root / name).write_bytes(original)

    def test_missing_proof(self):
        (self.root / self.proof['path'].lstrip('/')).unlink()
        with self.assertRaises(AssertionError): self.check()

    def test_proof_exact_existing_lf_even_with_matching_hash(self):
        path = self.root / self.proof['path'].lstrip('/')
        for suffix in ['', '\r\n', '\n\n', ' \n']:
            with self.subTest(suffix=suffix):
                body = (path.stem + suffix).encode('utf-8')
                path.write_bytes(body)
                self.proof['sha256'] = hashlib.sha256(body).hexdigest()
                with self.assertRaises(AssertionError): self.check()

    def test_extra_html_and_worker(self):
        for name in ['extra.html', '_worker.js']:
            (self.root / name).write_text('test', encoding='utf-8')
            with self.assertRaises(AssertionError): self.check()
            (self.root / name).unlink()

    def test_sitemap_index_counterexamples(self):
        ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
        cases = {
            'empty_index': '<sitemapindex xmlns="' + ns + '"/>',
            'wrong_root': '<not-a-sitemap/>',
            'self_cycle': '<sitemapindex xmlns="' + ns + '"><sitemap><loc>' + ORIGIN + '/sitemap-index.xml</loc></sitemap></sitemapindex>',
            'index_as_urlset': '<urlset xmlns="' + ns + '"><url><loc>' + ORIGIN + '/</loc></url></urlset>',
            'missing_child': '<sitemapindex xmlns="' + ns + '"><sitemap><loc>' + ORIGIN + '/sitemap-missing.xml</loc></sitemap></sitemapindex>',
            'duplicate_child': '<sitemapindex xmlns="' + ns + '">' + ('<sitemap><loc>' + ORIGIN + '/sitemap-0.xml</loc></sitemap>') * 2 + '</sitemapindex>',
            'duplicate_loc': '<sitemapindex xmlns="' + ns + '"><sitemap>' + ('<loc>' + ORIGIN + '/sitemap-0.xml</loc>') * 2 + '</sitemap></sitemapindex>',
        }
        path = self.root / 'sitemap-index.xml'; original = path.read_bytes()
        for name, xml in cases.items():
            with self.subTest(case=name):
                path.write_text(xml, encoding='utf-8')
                with self.assertRaises(AssertionError): self.check()
                path.write_bytes(original)

    def test_child_role_and_cycle_counterexamples(self):
        ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
        path = self.root / 'sitemap-0.xml'; original = path.read_bytes()
        for xml in ['<not-a-sitemap/>', '<urlset xmlns="' + ns + '"/>',
                    '<sitemapindex xmlns="' + ns + '"><sitemap><loc>' + ORIGIN + '/sitemap-index.xml</loc></sitemap></sitemapindex>',
                    '<sitemapindex xmlns="' + ns + '"><sitemap><loc>' + ORIGIN + '/sitemap-0.xml</loc></sitemap></sitemapindex>']:
            with self.subTest(xml=xml):
                path.write_text(xml, encoding='utf-8')
                with self.assertRaises(AssertionError): self.check()
                path.write_bytes(original)

    def test_orphan_sitemap_is_rejected_even_if_empty(self):
        for name in ['sitemap-orphan.xml', 'unlinked.xml', 'nested/sitemap-orphan.xml']:
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>', encoding='utf-8')
            with self.assertRaises(AssertionError): self.check()
            path.unlink()

    def test_valid_split_reachable_urlsets(self):
        ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
        (self.root / 'sitemap-index.xml').write_text('<sitemapindex xmlns="' + ns + '">' + ''.join('<sitemap><loc>' + ORIGIN + '/sitemap-' + str(i) + '.xml</loc></sitemap>' for i in range(2)) + '</sitemapindex>', encoding='utf-8')
        for index, routes in enumerate([ROUTES[:1], ROUTES[1:]]):
            (self.root / ('sitemap-' + str(index) + '.xml')).write_text('<urlset xmlns="' + ns + '">' + ''.join('<url><loc>' + ORIGIN + route + '</loc></url>' for route in routes) + '</urlset>', encoding='utf-8')
        self.assertEqual(len(self.check()['sitemapUrls']), 3)


if __name__ == '__main__': unittest.main()
