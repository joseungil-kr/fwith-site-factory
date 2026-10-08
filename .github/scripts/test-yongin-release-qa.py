#!/usr/bin/env python3
"""Offline regression cases for original/manual release identities and IndexNow scope."""
from email.message import Message
import importlib.util
import json
import unittest
from unittest.mock import patch
import os
import tempfile
import io
from pathlib import Path

spec = importlib.util.spec_from_file_location('release_qa', Path(__file__).with_name('yongin-release-qa.py'))
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)
SITE = Path(__file__).resolve().parents[2] / 'site-factory/yongin-flower'
REVISION = 'a' * 40


def document(identity, title='수지구 개업·이전 꽃배달', robots='index,follow', canonical=qa.ORIGIN + '/business/suji-opening-flowers/', revision=REVISION):
    return f'''<html><head><title>{title} | 꽃이랑 용인</title><meta name="robots" content="{robots}"><meta name="site-factory-revision" content="{revision}"><link rel="canonical" href="{canonical}"><script type="application/ld+json">{{}}</script></head><body><h1>{title}</h1><section class="article-shell" {identity}></section></body></html>'''


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages, cls.manual = qa.read_pages(SITE)
        cls.revised = next(p for p in cls.manual if p.get('supersedesSnapshotId'))
        cls.new = next(p for p in cls.manual if not p.get('supersedesSnapshotId'))
        cls.frozen = next(p for p in cls.pages if p.get('sourceType') != 'manual-authored')

    def check_page(self, page, identity, patch=None, indexable=True):
        defaults = {'canonical': qa.ORIGIN + page['url'], 'robots': 'index,follow' if indexable else 'noindex,follow'}
        built = document(identity, **defaults)
        live = document(identity, **(defaults | (patch or {})))
        qa.verify_page(live, built, page['url'], REVISION, indexable, page)

    def identity(self, page):
        if page.get('sourceType') != 'manual-authored':
            return f'data-snapshot-id="{page["snapshotId"]}"'
        identity = f'data-manual-revision="{page["revisionId"]}"'
        if page.get('supersedesSnapshotId'):
            identity += f' data-original-snapshot="{page["supersedesSnapshotId"]}"'
        return identity

    def test_effective_manifest_has_25_original_and_15_manual(self):
        self.assertEqual(len(self.pages), 40)
        self.assertEqual(sum(p.get('sourceType') == 'manual-authored' for p in self.pages), 15)

    def test_replacement_set_cannot_swap_an_unapproved_original(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'src/data').mkdir(parents=True)
            frozen = json.loads((SITE / 'src/data/publish-manifest.json').read_text())
            authored = json.loads((SITE / 'src/data/manual-pages.json').read_text())
            row = next(p for p in authored['pages'] if p['pageKey'] == 'yongin-flower-launch-14')
            other = next(p for p in frozen['pages'] if p['pageKey'] == 'yongin-flower-launch-12')
            row.update(pageKey=other['pageKey'], url=other['url'], supersedesSnapshotId=other['snapshotId'])
            (root / 'src/data/publish-manifest.json').write_text(json.dumps(frozen))
            (root / 'src/data/manual-pages.json').write_text(json.dumps(authored))
            with self.assertRaisesRegex(ValueError, 'six declared manual replacements'):
                qa.read_pages(root)

    def test_release_receipt_counts_effective_frozen_pages(self):
        def response(base, path):
            if path == '/robots.txt':
                return 200, 'User-agent: *\nDisallow: /', {}
            if path in ['/sitemap-index.xml', '/sitemap-0.xml', '/용인꽃배달/']:
                return 404, '', {}
            return 200, 'offline test document', {}
        with patch.object(qa, 'read_pages', return_value=(self.pages, self.manual)), patch.object(qa, 'get', response), patch.object(qa, 'verify_page'), patch.object(Path, 'read_text', return_value='offline test document'):
            receipt = qa.verify_release(SITE, 'http://127.0.0.1:8935', REVISION, False)
        self.assertEqual(receipt['detailCount'], 40)
        self.assertEqual(receipt['manualCount'], 15)
        self.assertEqual(receipt['frozenCount'], 25)

    def test_all_manifest_identities_pass(self):
        for page in self.pages:
            with self.subTest(page=page['pageKey']):
                self.check_page(page, self.identity(page))

    def test_staging_checks_all_same_identities_with_noindex(self):
        for page in self.pages:
            with self.subTest(page=page['pageKey']):
                self.check_page(page, self.identity(page), indexable=False)

    def test_new_manual_page_cannot_claim_snapshot(self):
        with self.assertRaisesRegex(ValueError, 'impersonate'):
            self.check_page(self.new, self.identity(self.new) + ' data-snapshot-id="fake"')

    def test_revised_manual_page_cannot_claim_old_snapshot(self):
        with self.assertRaisesRegex(ValueError, 'impersonate'):
            self.check_page(self.revised, self.identity(self.revised) + f' data-snapshot-id="{self.revised["supersedesSnapshotId"]}"')

    def test_revised_page_requires_original_reference(self):
        with self.assertRaisesRegex(ValueError, 'original snapshot'):
            self.check_page(self.revised, f'data-manual-revision="{self.revised["revisionId"]}"')

    def test_revised_page_rejects_wrong_original_reference(self):
        with self.assertRaisesRegex(ValueError, 'original snapshot'):
            self.check_page(self.revised, f'data-manual-revision="{self.revised["revisionId"]}" data-original-snapshot="wrong"')

    def test_manual_page_requires_exact_revision(self):
        with self.assertRaisesRegex(ValueError, 'manual revision'):
            self.check_page(self.new, 'data-manual-revision="old"')

    def test_frozen_page_requires_unchanged_snapshot(self):
        with self.assertRaisesRegex(ValueError, 'frozen snapshot changed'):
            self.check_page(self.frozen, 'data-snapshot-id="wrong"')

    def test_frozen_page_cannot_claim_manual_revision(self):
        with self.assertRaisesRegex(ValueError, 'claims manual'):
            self.check_page(self.frozen, self.identity(self.frozen) + ' data-manual-revision="fake"')

    def test_stale_canary_title_fails(self):
        with self.assertRaisesRegex(ValueError, 'H1 differs'):
            self.check_page(self.revised, self.identity(self.revised), {'title': '수지구 개업 축하꽃'})

    def test_old_live_commit_fails(self):
        with self.assertRaisesRegex(ValueError, 'live revision'):
            self.check_page(self.revised, self.identity(self.revised), {'revision': 'b' * 40})

    def test_production_noindex_fails(self):
        with self.assertRaisesRegex(ValueError, 'indexing directive'):
            self.check_page(self.revised, self.identity(self.revised), {'robots': 'noindex,follow'})

    def test_staging_index_fails(self):
        with self.assertRaisesRegex(ValueError, 'indexing directive'):
            self.check_page(self.revised, self.identity(self.revised), {'robots': 'index,follow'}, indexable=False)

    def test_conflicting_robots_fail(self):
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            self.check_page(self.revised, self.identity(self.revised), {'robots': 'index,noindex,follow'})

    def test_wrong_canonical_fails(self):
        with self.assertRaisesRegex(ValueError, 'canonical'):
            self.check_page(self.revised, self.identity(self.revised), {'canonical': 'https://hwaseong.fwith.kr/'})

    def test_production_meta_none_fails(self):
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            self.check_page(self.revised, self.identity(self.revised), {'robots': 'index,none,follow'})

    def test_restrictive_x_robots_headers_fail(self):
        for value in ['noindex', 'none', 'googlebot: noindex', 'all, NOINDEX', 'index, follow, none']:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'X-Robots-Tag'):
                qa.verify_http_indexing({'X-Robots-Tag': value}, '/business/a/')

    def test_duplicate_x_robots_headers_cannot_hide_noindex(self):
        headers = Message()
        headers['X-Robots-Tag'] = 'all'
        headers['X-Robots-Tag'] = 'googlebot: none'
        with self.assertRaisesRegex(ValueError, 'X-Robots-Tag'):
            qa.verify_http_indexing(headers, '/business/a/')

    def test_nonrestrictive_http_headers_pass(self):
        for value in ['', 'all', 'index, follow', 'max-image-preview:large']:
            qa.verify_http_indexing({'X-Robots-Tag': value}, '/business/a/')

    def test_indexnow_exact_20_changed_urls(self):
        live = {qa.ORIGIN + '/', *(qa.ORIGIN + p['url'] for p in self.pages), *(qa.ORIGIN + p for p in qa.HUBS)}
        urls = qa.indexnow_scope(self.manual, live)
        self.assertEqual(len(urls), 20)
        self.assertEqual(set(urls), {qa.ORIGIN + '/', *(qa.ORIGIN + p['url'] for p in self.manual), *(qa.ORIGIN + '/' + p['category'] + '/' for p in self.manual)})

    def test_indexnow_rejects_missing_live_url(self):
        with self.assertRaisesRegex(ValueError, 'missing from live sitemap'):
            qa.indexnow_scope(self.manual, set())

    def test_xml_parser_accepts_sitemap_namespace_and_escapes(self):
        self.assertEqual(qa.locations('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://yongin.fwith.kr/a%20b/</loc></url></urlset>'), ['https://yongin.fwith.kr/a b/'])


class SubmissionReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('indexnow_once', Path(__file__).with_name('yongin-indexnow-once.py'))
        cls.once = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.once)

    def execute_fixture(self, output, returncode=0, attempt='1', prior_receipt=False):
        with tempfile.TemporaryDirectory() as folder:
            previous = Path.cwd()
            os.chdir(folder)
            try:
                Path('indexnow-urls.json').write_text(json.dumps([qa.ORIGIN + f'/fixture-{i}/' for i in range(18)]))
                if prior_receipt:
                    Path('indexnow-submission-receipt.json').write_text('{}')
                calls = []
                class Process:
                    stdout = io.StringIO(output)
                    def wait(self):
                        return returncode
                def spawn(*args, **kwargs):
                    receipt = json.loads(Path('indexnow-submission-receipt.json').read_text())
                    self.assertEqual(receipt['state'], 'started-do-not-retry-if-terminal-receipt-missing')
                    self.assertEqual(receipt['urlCount'], 18)
                    self.assertEqual(receipt['sourceRevision'], REVISION)
                    calls.append(args)
                    return Process()
                env = {'GITHUB_SHA': REVISION, 'GITHUB_RUN_ID': 'test-fixture-only', 'GITHUB_RUN_ATTEMPT': attempt, 'INDEXNOW_ENDPOINT': 'https://searchadvisor.naver.com/indexnow', 'INDEXNOW_KEY': 'fixture-key-not-a-real-key'}
                with patch.dict(os.environ, env), patch.object(self.once.subprocess, 'Popen', spawn), patch('builtins.print'):
                    try:
                        self.once.main()
                    except (SystemExit, FileExistsError) as error:
                        terminal = error
                receipt = json.loads(Path('indexnow-submission-receipt.json').read_text()) if Path('indexnow-submission-receipt.json').exists() else None
                if Path('indexnow-receipt.log').exists():
                    self.assertNotIn('fixture-key-not-a-real-key', Path('indexnow-receipt.log').read_text())
                return receipt, calls, terminal
            finally:
                os.chdir(previous)

    def test_started_receipt_precedes_native_helper_and_200_is_accepted(self):
        receipt, calls, error = self.execute_fixture('IndexNow accepted 18 URL(s): HTTP 200\n')
        self.assertEqual(len(calls), 1)
        self.assertEqual(error.code, 0)
        self.assertEqual(receipt['state'], 'accepted')
        self.assertEqual(receipt['httpStatus'], 200)
        self.assertEqual(len(receipt['urlsSha256']), 64)
        self.assertEqual(len(receipt['keySha256']), 64)
        self.assertEqual(len(receipt['fingerprint']), 64)
        self.assertNotIn('fixture-key-not-a-real-key', json.dumps(receipt))

    def test_202_remains_key_validation_pending(self):
        receipt, calls, error = self.execute_fixture('IndexNow accepted 18 URL(s): HTTP 202\n')
        self.assertEqual(receipt['state'], 'received-key-validation-pending')
        self.assertEqual(receipt['httpStatus'], 202)

    def test_process_failure_is_unknown_and_never_retried(self):
        receipt, calls, error = self.execute_fixture('network failure\n', returncode=1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(error.code, 1)
        self.assertEqual(receipt['state'], 'failed-or-unknown-do-not-retry')
        self.assertFalse(receipt['automaticRetryAllowed'])

    def test_unrecognized_success_output_is_not_accepted(self):
        receipt, calls, error = self.execute_fixture('done\n')
        self.assertEqual(error.code, 1)
        self.assertEqual(receipt['state'], 'failed-or-unknown-do-not-retry')

    def test_native_output_key_is_redacted(self):
        receipt, calls, error = self.execute_fixture('Failed URL contains fixture-key-not-a-real-key\n', returncode=1)
        self.assertEqual(receipt['state'], 'failed-or-unknown-do-not-retry')

    def test_rerun_never_starts_helper(self):
        receipt, calls, error = self.execute_fixture('', attempt='2')
        self.assertEqual(calls, [])
        self.assertIsNone(receipt)

    def test_existing_receipt_never_starts_helper(self):
        receipt, calls, error = self.execute_fixture('', prior_receipt=True)
        self.assertEqual(calls, [])
        self.assertIsInstance(error, FileExistsError)


if __name__ == '__main__':
    unittest.main(verbosity=2)
