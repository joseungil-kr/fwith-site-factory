"""Offline synthetic contracts only. No production assignment, proof or network."""
from pathlib import Path
import copy
import json
import os
import tempfile
import unittest
from unittest.mock import patch
import release_mode as mode


class ReleaseModeTests(unittest.TestCase):
    def setUp(self):
        self.approval = copy.deepcopy(mode.UNBOUND)
        self.approval.update(state='approved', hostname='synthetic-only.invalid', origin='https://synthetic-only.invalid', approvedRuntimeDataSha256='a' * 64)
        self.approval['approvals'] = {key: True for key in self.approval['approvals']}
        self.approval['evidenceReferences'] = {key: 'SYNTHETIC_TEST_ONLY_NOT_APPROVAL' for key in self.approval['evidenceReferences']}
        self.config = dict(siteKey=mode.SITE_KEY, worker=mode.WORKER, productionApproved=True, hostnameOwnershipVerified=False)
        self.manifest = dict(siteKey=mode.SITE_KEY, directRelease=dict(publicationAuthorized=True, plannedOriginalCount=2, sitemapUrlCount=3, intrinsicIndexableRouteCount=3, renderedHtmlRouteCount=5), pages=[{'url': p} for p in sorted(mode.SITEMAP_ROUTES - {'/'})])
        self.environment = dict(SITE_URL=self.approval['origin'], SITE_FACTORY_REVISION='f' * 40, SITE_INDEXABLE='true')

    def validate(self):
        # Restricted mock is local to this test, never an environment/build option.
        with patch.object(mode, 'BUSINESS_ZONE', 'invalid'):
            return mode.validate_approval(self.approval, self.config, self.manifest, 'a' * 64, self.environment)

    def test_synthetic_exact_complete_contract(self):
        self.assertEqual(self.validate(), 'https://synthetic-only.invalid')

    def test_real_validator_rejects_reserved_synthetic_host(self):
        with self.assertRaisesRegex(AssertionError, 'release_hostname_unbound'):
            mode.validate_approval(self.approval, self.config, self.manifest, 'a' * 64, self.environment)

    def test_each_missing_approval_fails(self):
        for key in self.approval['approvals']:
            with self.subTest(key=key):
                self.approval['approvals'][key] = False
                with self.assertRaisesRegex(AssertionError, 'release_approval_missing'): self.validate()
                self.approval['approvals'][key] = True

    def test_each_missing_evidence_fails(self):
        for key in self.approval['evidenceReferences']:
            with self.subTest(key=key):
                self.approval['evidenceReferences'][key] = None
                with self.assertRaisesRegex(AssertionError, 'release_evidence_missing'): self.validate()
                self.approval['evidenceReferences'][key] = 'SYNTHETIC_TEST_ONLY_NOT_APPROVAL'

    def test_runtime_digest_change_fails(self):
        self.approval['approvedRuntimeDataSha256'] = 'b' * 64
        with self.assertRaisesRegex(AssertionError, 'release_runtime_data_changed'): self.validate()

    def test_ownership_is_not_claimed_by_permission(self):
        self.config['hostnameOwnershipVerified'] = True
        with self.assertRaisesRegex(AssertionError, 'release_unverified_ownership_claim'): self.validate()

    def test_origin_override_fails(self):
        self.environment['SITE_URL'] = 'https://different.invalid'
        with self.assertRaisesRegex(AssertionError, 'release_environment_origin_mismatch'): self.validate()

    def test_revision_must_be_exact(self):
        self.environment['SITE_FACTORY_REVISION'] = 'main'
        with self.assertRaisesRegex(AssertionError, 'release_revision_required'): self.validate()

    def test_cross_region_worker_fails(self):
        self.approval['configuredWorkerTarget'] = 'seoul-guro-flower-guide'
        with self.assertRaisesRegex(AssertionError, 'release_worker_mismatch'): self.validate()

    def test_cross_region_baseline_fails(self):
        self.approval['baselineSourceRevision'] = 'b' * 40
        with self.assertRaisesRegex(AssertionError, 'release_baseline_mismatch'): self.validate()

    def test_unbound_source_is_preview_only_and_environment_cannot_activate(self):
        # Isolated record, so the same negative test remains valid after an approved
        # production successor is later bound. Never hard-code preview on live source.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data = root / 'src/data'; data.mkdir(parents=True)
            config = dict(siteKey=mode.SITE_KEY, worker=mode.WORKER, productionApproved=False,
                          hostnameOwnershipVerified=False, previewUrl='https://synthetic-only.invalid')
            manifest = copy.deepcopy(self.manifest); manifest['directRelease']['publicationAuthorized'] = False
            (data/'site-config.json').write_text(json.dumps(config))
            (data/'publish-manifest.json').write_text(json.dumps(manifest))
            (data/'release-approval.json').write_text(json.dumps(mode.UNBOUND))
            self.assertFalse(mode.resolve_mode(root, {})['indexable'])
            with self.assertRaisesRegex(AssertionError, 'production_not_approved_unbound_release'):
                mode.resolve_mode(root, {'SITE_INDEXABLE': 'true'})
            with self.assertRaisesRegex(AssertionError, 'release_indexable_value_invalid'):
                mode.resolve_mode(root, {'SITE_INDEXABLE': 'TRUE'})
            config['productionApproved'] = True
            (data/'site-config.json').write_text(json.dumps(config))
            with self.assertRaisesRegex(AssertionError, 'release_partial_activation'):
                mode.resolve_mode(root, {})

    def test_non_boolean_source_approval_fails(self):
        self.config['productionApproved'] = 'true'
        with self.assertRaisesRegex(AssertionError, 'release_source_not_approved'): self.validate()

    def test_extra_contract_field_is_not_silently_accepted(self):
        self.approval['skipHostApproval'] = True
        with self.assertRaisesRegex(AssertionError, 'release_binding_schema_mismatch'): self.validate()

    def test_missing_article_is_rejected(self):
        self.manifest['pages'].pop()
        with self.assertRaisesRegex(AssertionError, 'release_routes_changed'): self.validate()

    def test_changed_quota_is_rejected(self):
        self.manifest['directRelease']['plannedOriginalCount'] = 3
        with self.assertRaisesRegex(AssertionError, 'release_article_quota_changed'): self.validate()

    def test_stale_preview_sitemap_count_rejected_in_production(self):
        self.manifest['directRelease']['sitemapUrlCount'] = 0
        with self.assertRaisesRegex(AssertionError, 'release_route_counts_mismatch'): self.validate()

    def test_route_robots_exact_both_modes(self):
        for route in mode.CUSTOMER_ROUTES | {'/404.html'}:
            self.assertEqual(mode.expected_robots(route, False), 'noindex,nofollow,noarchive')
            wanted = 'noindex,nofollow,noarchive' if route == '/404.html' else 'noindex,follow' if route == '/regions/' else 'index,follow'
            self.assertEqual(mode.expected_robots(route, True), wanted)
        with self.assertRaises(AssertionError): mode.expected_robots('/unplanned/', True)

    def test_synthetic_three_sitemap_and_thin_directory_exclusion(self):
        self.assertEqual(len(mode.SITEMAP_ROUTES), 3)
        self.assertNotIn('/regions/', mode.SITEMAP_ROUTES)
        self.assertEqual(len(mode.CUSTOMER_ROUTES), 4)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); origin = 'https://synthetic-only.invalid'
            (root / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+origin+'/sitemap-index.xml\n')
            (root / '_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n')
            (root / 'sitemap-index.xml').write_text('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>'+origin+'/sitemap-0.xml</loc></sitemap></sitemapindex>')
            def write(routes):
                (root / 'sitemap-0.xml').write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+origin+r+'</loc></url>' for r in routes)+'</urlset>')
            write(sorted(mode.SITEMAP_ROUTES))
            self.assertEqual(mode.validate_search_output(root, origin, True), 3)
            for bad in [sorted(mode.SITEMAP_ROUTES | {'/regions/'}), ['/', '/regions/'], sorted(mode.SITEMAP_ROUTES)+['/'], []]:
                write(bad)
                with self.assertRaisesRegex(AssertionError, 'release_sitemap_exact_routes_mismatch'):
                    mode.validate_search_output(root, origin, True)
            write(sorted(mode.SITEMAP_ROUTES))
            (root / '_headers').write_text('/*\n  X-Robots-Tag: noindex\n')
            with self.assertRaisesRegex(AssertionError, 'release_blocking_header'):
                mode.validate_search_output(root, origin, True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
