"""Offline initial-scope contract tests; synthetic geography is not an approval."""
import copy
from datetime import datetime, timedelta, timezone
from contextlib import redirect_stdout
import io
import json
import sys
import unittest
from unittest.mock import patch
import test_provision_goyang as fixture

p = fixture.p
SITE = 'seongnam-flower-v2'
LAUNCH = SITE + '-initial-20261004'
SCOPE = SITE + '-dong-coverage-20261004'


def membership_pair(count=2):
    """Synthetic identities, never published or represented as official research."""
    members = [{'unit_key': f'성남시/수정구/법정동/시험{i}동', 'name': f'시험{i}동',
                'district_key': 'sujeong', 'page_key': f'{SITE}-region-test-{i}',
                'slug': f'test-{i}', 'route': f'/regions/test-{i}/',
                'intent_key': f'seongnam|flower-delivery|local-order|test-{i}'} for i in range(count)]
    url = 'https://www.seongnam.go.kr/'
    aliases = [{'administrative_unit_key': '성남시/수정구/행정동/시험행정동', 'name': '시험행정동',
                'district_key': 'sujeong', 'canonical_targets': [
                    {'unit_key': m['unit_key'], 'scope': 'partial'} for m in members]}]
    membership = {'schema': 'seongnam-all-dong-membership-research-v1', 'site_key': SITE,
                  'scope_key': SCOPE, 'prepared_at_utc': datetime.now(timezone.utc).isoformat(),
                  'count_is_page_quota': False, 'content_membership_approved': False,
                  'publication_approved': False, 'official_evidence': [{'url': url}],
                  'counts': {'legal_units': count, 'administrative_units': 1,
                             'administrative_legal_relations': count},
                  'members': members, 'administrative_alias_routes': aliases}
    coverage = {'schemaVersion': 2, 'siteKey': SITE, 'scopeKey': SCOPE,
                'membershipSourceSha256': '', 'unitBasis': 'legal-dong-plus-eup-myeon',
                'countIsPageQuota': False, 'officialSourceUrls': [url],
                'verifiedAt': '2026-10-04', 'sourceBasisDate': '2025-01-01',
                'districts': [{'key': 'sujeong', 'name': '수정구', 'sourceUrl': url}],
                'units': [{'unitKey': m['unit_key'], 'name': m['name'], 'unitType': 'legal-dong',
                           'districtKeys': [m['district_key']], 'legalRi': []} for m in members],
                'representatives': [{'pageKey': m['page_key'], 'url': m['route'], 'slug': m['slug'],
                                    'intentKey': m['intent_key'], 'unitKeys': [m['unit_key']],
                                    'status': 'candidate', 'routeMode': 'regional', 'primaryKeyword': m['name'] + ' 꽃배달',
                                    'queryEvidence': [{'fixture': True, 'note': 'Synthetic local test only'}]} for m in members],
                'administrativeCrosswalk': [{'aliasKey': aliases[0]['administrative_unit_key'],
                                           'name': '시험행정동', 'districtKey': 'sujeong',
                                           'relations': [{'unitKey': m['unit_key'], 'scope': 'partial'} for m in members]}]}
    return membership, coverage


class InitialScopeTests(unittest.TestCase):
    def test_first_three_new_regions_are_explicit_and_have_no_trial_fallback(self):
        self.assertEqual(p.INITIAL_REGIONS,{'namyangju-flower-v2':'남양주','pyeongtaek-flower-v2':'평택','anyang-flower-v2':'안양'})
        for site in p.INITIAL_REGIONS:
            with self.subTest(site=site):
                self.assertNotIn(site,p.LEGACY_LAUNCH_KEYS)
                target=p.target_contract(site)
                self.assertEqual(target['siteUrl'],'https://'+site.split('-')[0]+'.fwith.kr')
                with self.assertRaisesRegex(p.ProvisionError,'no historical trial'):
                    p.launch_scope(None,'absent',site,site+'-trial-20261005','legacy-trial')
                with self.assertRaisesRegex(p.ProvisionError,'whole-dong initial launch key'):
                    p.launch_scope(None,'absent',site,None,None,scope_key=None,membership_bytes=None,
                        membership_sha256=None,coverage_bytes=None,coverage_sha256=None)
    def setUp(self):
        self.f = fixture.BootstrapTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.membership, self.coverage = membership_pair()

    def kwargs(self):
        membership = p.encode(self.membership)
        coverage = copy.deepcopy(self.coverage)
        coverage['membershipSourceSha256'] = p.sha256(membership)
        coverage = p.encode(coverage)
        return dict(scope_key=SCOPE, membership_bytes=membership, membership_sha256=p.sha256(membership),
                    coverage_bytes=coverage, coverage_sha256=p.sha256(coverage))

    def check(self, **changes):
        return p.checked_initial_scope(SITE, LAUNCH, **{**self.kwargs(), **changes})

    def prepare(self, target='absent', **changes):
        return p.prepare(self.f.repo, self.f.control, target, SITE, LAUNCH, **{**self.kwargs(), **changes})

    def install_fixture_profile(self):
        """Tests contract plumbing only; no real profile or review is registered."""
        self.initial_source = dict(self.f.source)
        architecture = json.loads(self.initial_source['src/data/architecture.json'])
        architecture['hubs'].append({'category': 'regions', 'url': '/regions/', 'label': '지역',
                                     'children': 0, 'menuVisible': False, 'indexable': False})
        self.initial_source['src/data/architecture.json'] = p.encode(architecture)
        self.initial_source['src/data/region-coverage.json'] = p.encode(p.initial_coverage_template())
        self.initial_source['src/data/region-policy.json'] = p.encode(p.initial_policy_template())
        for name, data in self.initial_source.items(): self.f.write(p.INITIAL_SOURCE_ROOT + '/' + name, data)
        source_revision = self.f.commit()
        source_tree = self.f.run_git('rev-parse', source_revision + ':' + p.INITIAL_SOURCE_ROOT).strip()
        profile = {'registryKey': 'fixture-only-clean-initial', 'sourceRevision': source_revision,
                   'sourceTree': source_tree, 'sourceCount': len(self.initial_source)}
        pin = patch.object(p, 'INITIAL_SOURCE_PROFILES', {SITE: profile})
        pin.start()
        self.addCleanup(pin.stop)
        self.f.templates['templates'][profile['registryKey']] = {
            'sourceBranch': p.SOURCE_BRANCH, 'sourceRoot': p.INITIAL_SOURCE_ROOT,
            'sourceRevision': source_revision, 'productionReady': False,
            'initialScopeMode': 'whole-dong-initial', 'regionsRuntimeReady': True, 'zeroCustomerContent': True,
            'sourceTree': source_tree, 'sourceFileCount': len(self.initial_source)}
        self.f.write(p.TEMPLATE_REGISTRY_PATH, p.encode(self.f.templates))
        self.f.control = self.f.commit()

    def test_full_identity_and_nonquota_count(self):
        result = self.check()
        self.assertEqual(result['scopeKey'], SCOPE)
        self.assertEqual(result['members'], self.membership['members'])
        self.assertEqual(result['officialUnitCount'], 2)
        self.assertFalse(result['countIsPageQuota'])
        self.assertFalse(result['preliminaryTrialRequired'])
        self.assertNotIn('trialDetailTarget', result)
        for key in ['contentApprovalGranted', 'snapshotApprovalGranted', 'finalBatchApprovalGranted',
                    'domainConnectionVerified', 'productionReleaseApproved', 'regionsRuntimeVerified', 'readyForContentSnapshots']:
            self.assertIs(result[key], False)
        canonical = json.dumps(result['members'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(result['memberIdentitySha256'], p.sha256(canonical))

    def test_51_is_a_membership_fact_not_a_50_page_ceiling(self):
        self.membership, self.coverage = membership_pair(51)
        self.assertEqual(self.check()['officialUnitCount'], 51)

    def test_initial_profile_missing_cannot_fallback_to_reviewed_trial_pin(self):
        self.assertNotIn(SITE,p.INITIAL_SOURCE_PROFILES)
        with self.assertRaisesRegex(p.ProvisionError, 'No explicitly reviewed runtime-ready clean initial profile'):
            self.prepare()
        self.assertFalse((self.f.repo / p.target_contract(SITE)['root']).exists())

    def test_registry_alone_cannot_self_approve_initial_profile(self):
        self.f.templates['templates']['unreviewed-initial'] = {
            'sourceRevision': self.f.source_revision, 'regionsRuntimeReady': True}
        self.f.write(p.TEMPLATE_REGISTRY_PATH, p.encode(self.f.templates)); self.f.control = self.f.commit()
        with self.assertRaisesRegex(p.ProvisionError, 'No explicitly reviewed'):
            self.prepare()

    def test_explicit_initial_positive_zero_pages_eight_adaptations_and_exact_resume(self):
        self.install_fixture_profile()
        outputs, plan = self.prepare(scope_mode='whole-dong-initial')
        self.assertEqual((outputs, plan), self.prepare())
        target = p.target_contract(SITE)
        proof = json.loads(outputs['target-files/' + target['provenancePath']])
        self.assertEqual(proof['initialScope'], plan['initialScope'])
        self.assertNotIn('trialDetailTarget', plan)
        self.assertNotIn('trialDetailTarget', proof)
        self.assertEqual(plan['customerPagesCreated'], 0)
        self.assertEqual(plan['externalActionsPerformed'], [])
        adapted = {name[len('target-files/' + target['root'] + '/'):]: data for name, data in outputs.items()
                   if name.startswith('target-files/' + target['root'] + '/')}
        self.assertEqual({name for name in adapted if adapted[name] != self.initial_source[name]}, p.INITIAL_ADAPTATIONS)
        p.validate_initial_empty(adapted, SITE, source_revision=plan['sourceRevision'], initial_scope=plan['initialScope'])
        for name, data in outputs.items():
            if name.startswith('target-files/'):
                self.f.write(name[len('target-files/'):], data)
        revision = self.f.commit()
        self.assertEqual(self.prepare(revision)[1]['targetState'], 'unchanged')
        self.membership['members'].reverse()
        with self.assertRaisesRegex(p.ProvisionError, 'never overwrite|matching bootstrap provenance'):
            self.prepare(revision)

    def test_initial_registry_and_policy_are_disabled_without_mutating_legacy_categories(self):
        self.install_fixture_profile()
        legacy = copy.deepcopy(p.site_entry(SITE))
        outputs, plan = self.prepare()
        registry = json.loads(outputs['control-files/' + p.REGISTRY_PATH])['sites'][SITE]
        self.assertEqual(p.site_entry(SITE), legacy)
        self.assertNotIn('regions', p.CATEGORY_TYPES)
        self.assertEqual(registry['categoryPageTypes']['regions'], ['regional-service'])
        self.assertFalse(registry['regionalService']['enabled'])
        self.assertEqual(registry['regionalService']['scopeKey'], SCOPE)
        self.assertFalse(registry['productionEnabled'])
        self.assertTrue(registry['growthPaused'])
        self.assertEqual(registry['hubPolicy'],'child-threshold-v1')
        self.assertEqual(registry['initialLaunch'],{key:plan['initialScope'][key] for key in
            ('mode','scopeKey','membershipSourceSha256','coverageSha256','memberIdentitySha256','officialUnitCount')})
        prefix = 'target-files/' + p.target_contract(SITE)['root'] + '/'
        self.assertEqual(outputs[prefix + 'src/data/region-coverage.json'], self.kwargs()['coverage_bytes'])
        policy = json.loads(outputs[prefix + 'src/data/region-policy.json'])
        self.assertFalse(policy['enabled'])
        self.assertEqual(policy['state'], 'candidate-pending-independent-review')
        self.assertEqual(policy['visualBindings'], [])
        self.assertEqual(policy['rulesRevision'], plan['sourceRevision'])
        self.assertEqual(policy['membershipSourceSha256'], plan['initialScope']['membershipSourceSha256'])
        self.assertEqual(policy['officialHosts'], ['www.seongnam.go.kr'])
        self.assertEqual(policy['unitTypes'], ['legal-dong'])

    def test_neutral_initial_source_cannot_contain_membership_or_approval(self):
        self.install_fixture_profile()
        for name, change in [('region-coverage', {'siteKey': SITE}),
                             ('region-coverage', {'units': [{'unitKey': 'old-region'}]}),
                             ('region-policy', {'enabled': True}),
                             ('region-policy', {'visualBindings': [{'status': 'approved'}]})]:
            source = dict(self.initial_source)
            path = 'src/data/' + name + '.json'
            value = json.loads(source[path]); value.update(change); source[path] = p.encode(value)
            with self.subTest(name=name, change=change), self.assertRaisesRegex(p.ProvisionError, 'neutral unbound'):
                p.validate_initial_empty(source, 'template-only')

    def test_initial_policy_cannot_inherit_enabled_state_or_visual_approval(self):
        self.install_fixture_profile()
        outputs, plan = self.prepare()
        prefix = 'target-files/' + p.target_contract(SITE)['root'] + '/'
        adapted = {name[len(prefix):]: data for name, data in outputs.items() if name.startswith(prefix)}
        for change in ({'enabled': True}, {'visualBindings': [{'status': 'approved'}]},
                       {'officialHosts': ['unapproved.example']}, {'state': 'approved'}):
            files = dict(adapted); policy = json.loads(files['src/data/region-policy.json']); policy.update(change)
            files['src/data/region-policy.json'] = p.encode(policy)
            with self.subTest(change=change), self.assertRaisesRegex(p.ProvisionError, 'disabled candidate'):
                p.validate_initial_empty(files, SITE, source_revision=plan['sourceRevision'], initial_scope=plan['initialScope'])

    def test_initial_runtime_missing_query_district_or_definition_shape_is_blocked(self):
        self.install_fixture_profile()
        for field, value in [('verifiedAt', ''), ('sourceBasisDate', ''), ('districts', [])]:
            original = self.coverage[field]; self.coverage[field] = value
            with self.subTest(field=field), self.assertRaises(p.ProvisionError): self.prepare()
            self.coverage[field] = original
        for field, value in [('queryEvidence', []), ('primaryKeyword', ''), ('routeMode', 'existing')]:
            original = self.coverage['representatives'][0][field]
            self.coverage['representatives'][0][field] = value
            with self.subTest(field=field), self.assertRaises(p.ProvisionError): self.prepare()
            self.coverage['representatives'][0][field] = original

    def test_new_initial_root_cannot_use_historical_root_or_loosen_legacy_validator(self):
        self.install_fixture_profile()
        with self.assertRaisesRegex(p.ProvisionError, 'Unexpected hubs'):
            p.adapt(self.initial_source, SITE)
        entry = self.f.templates['templates']['fixture-only-clean-initial']
        entry['sourceRoot'] = p.SOURCE_ROOT
        self.f.write(p.TEMPLATE_REGISTRY_PATH, p.encode(self.f.templates)); self.f.control = self.f.commit()
        with self.assertRaisesRegex(p.ProvisionError, 'exact reviewed source pin'): self.prepare()

    def test_initial_source_tree_count_and_registry_flags_are_pinned(self):
        self.install_fixture_profile()
        profile = p.INITIAL_SOURCE_PROFILES[SITE]
        original = copy.deepcopy(profile)
        for key, value in [('sourceTree', 'f' * 40), ('sourceCount', 50)]:
            with self.subTest(key=key):
                profile[key] = value
                with self.assertRaises(p.ProvisionError): self.prepare()
                profile.update(original)
        entry = self.f.templates['templates'][profile['registryKey']]
        entry['regionsRuntimeReady'] = False
        self.f.write(p.TEMPLATE_REGISTRY_PATH, p.encode(self.f.templates)); self.f.control = self.f.commit()
        with self.assertRaisesRegex(p.ProvisionError, 'exact reviewed source pin'): self.prepare()

    def test_arbitrary_new_trial_is_never_an_implicit_or_explicit_fallback(self):
        for mode in (None, 'legacy-trial', 'whole-dong-initial'):
            with self.subTest(mode=mode), self.assertRaises(p.ProvisionError):
                p.prepare(self.f.repo, self.f.control, 'absent', SITE, SITE + '-trial-new', scope_mode=mode)
        with self.assertRaisesRegex(p.ProvisionError, 'initial launch key'):
            p.prepare(self.f.repo, self.f.control, 'absent', SITE)

    def test_unknown_site_is_still_rejected(self):
        with self.assertRaisesRegex(p.ProvisionError, 'allowlist'):
            p.prepare(self.f.repo, self.f.control, 'absent', 'unreviewed-flower-v2', 'unreviewed-flower-v2-initial-20261004', **self.kwargs())

    def test_initial_missing_membership_or_hashes_is_blocked(self):
        for key in self.kwargs():
            with self.subTest(key=key), self.assertRaises(p.ProvisionError):
                self.check(**{key: None})
        with self.assertRaisesRegex(p.ProvisionError, 'Legacy replay'):
            p.prepare(self.f.repo, self.f.control, 'absent', SITE, SITE + '-trial-20261002', scope_mode='legacy-trial', **self.kwargs())

    def test_membership_hashes_types_and_duplicate_json_keys(self):
        with self.assertRaisesRegex(p.ProvisionError, 'raw-byte hash mismatch'):
            self.check(membership_sha256='f' * 64)
        with self.assertRaisesRegex(p.ProvisionError, 'raw UTF-8 JSON bytes'):
            self.check(membership_bytes=self.membership)
        with self.assertRaisesRegex(p.ProvisionError, 'raw-byte SHA-256'):
            self.check(coverage_sha256='F' * 64)
        raw = b'{"site_key": "one", "site_key": "two"}'
        with self.assertRaisesRegex(p.ProvisionError, 'duplicate JSON object keys'):
            self.check(membership_bytes=raw, membership_sha256=p.sha256(raw))
        raw = b'[]'
        with self.assertRaisesRegex(p.ProvisionError, 'JSON object'):
            self.check(membership_bytes=raw, membership_sha256=p.sha256(raw))

    def test_numeric_overflow_and_nonfinite_literals_are_rejected(self):
        for value in ('1e999', '-1e999', '1E+999', '-1E+999', 'NaN', 'Infinity', '-Infinity'):
            raw = ('{"value":' + value + '}').encode()
            with self.subTest(value=value), self.assertRaisesRegex(p.ProvisionError, 'non-finite JSON number'):
                p.checked_json_bytes(raw, p.sha256(raw), 'Membership')
        raw = b'{"value":1e-999,"finite":1.5}'
        self.assertEqual(p.checked_json_bytes(raw, p.sha256(raw), 'Membership'), {'value': 0.0, 'finite': 1.5})

    def test_whole_partial_collision_is_rejected_even_when_both_artifacts_and_counts_match(self):
        unit = self.membership['members'][0]['unit_key']
        self.membership['administrative_alias_routes'][0]['canonical_targets'].append({'unit_key': unit, 'scope': 'whole'})
        self.coverage['administrativeCrosswalk'][0]['relations'].append({'unitKey': unit, 'scope': 'whole'})
        self.membership['counts']['administrative_legal_relations'] += 1
        with self.assertRaisesRegex(p.ProvisionError, 'Duplicate administrative relationship'):
            self.check()
        # Each input also rejects the contradiction by itself; it must not be
        # accepted as two distinct edges just because the scope string differs.
        self.membership['administrative_alias_routes'][0]['canonical_targets'].pop()
        self.membership['counts']['administrative_legal_relations'] -= 1
        with self.assertRaisesRegex(p.ProvisionError, 'Duplicate administrative relationship'):
            self.check()

    def test_duplicate_member_identities_are_rejected(self):
        for field in ('unit_key', 'page_key', 'intent_key', 'slug', 'route'):
            original = copy.deepcopy(self.membership)
            self.membership['members'][1][field] = self.membership['members'][0][field]
            with self.subTest(field=field), self.assertRaises(p.ProvisionError): self.check()
            self.membership = original

    def test_partial_members_units_and_representatives_are_rejected(self):
        for name in ('members', 'units', 'representatives'):
            target = self.membership if name == 'members' else self.coverage
            original = target[name].copy(); target[name].pop()
            with self.subTest(name=name), self.assertRaises(p.ProvisionError): self.check()
            target[name] = original
        self.coverage['representatives'][1] = copy.deepcopy(self.coverage['representatives'][0])
        with self.assertRaisesRegex(p.ProvisionError, 'duplicate representative'): self.check()

    def test_partial_duplicate_or_unknown_administrative_edges_are_rejected(self):
        rows = self.coverage['administrativeCrosswalk']
        original = copy.deepcopy(rows)
        rows[0]['relations'].pop()
        with self.assertRaisesRegex(p.ProvisionError, 'crosswalk'): self.check()
        self.coverage['administrativeCrosswalk'] = copy.deepcopy(original)
        self.coverage['administrativeCrosswalk'][0]['relations'].append(copy.deepcopy(original[0]['relations'][0]))
        with self.assertRaisesRegex(p.ProvisionError, 'Duplicate administrative relationship'): self.check()
        self.coverage['administrativeCrosswalk'] = copy.deepcopy(original)
        self.coverage['administrativeCrosswalk'][0]['relations'][0]['unitKey'] = 'unknown'
        with self.assertRaisesRegex(p.ProvisionError, 'Unknown administrative alias'): self.check()

    def test_quota_caps_self_approval_and_false_boolean_types_rejected(self):
        for field, value in [('count_is_page_quota', True), ('count_is_page_quota', 0),
                             ('content_membership_approved', True), ('publication_approved', True),
                             ('pageQuota', 50), ('trialDetailTarget', 1)]:
            original = copy.deepcopy(self.membership); self.membership[field] = value
            with self.subTest(field=field), self.assertRaises(p.ProvisionError): self.check()
            self.membership = original
        self.membership['counts']['legal_units'] = True
        with self.assertRaisesRegex(p.ProvisionError, 'official legal-unit count'): self.check()

    def test_observation_is_metadata_not_an_arbitrary_expiry(self):
        self.membership['prepared_at_utc'] = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()
        self.assertEqual(self.check()['membershipObservedAtUtc'], self.membership['prepared_at_utc'])
        self.membership['prepared_at_utc'] = '2026-10-04T00:00:00'
        with self.assertRaisesRegex(p.ProvisionError, 'timezone'): self.check()
        self.membership['prepared_at_utc'] = datetime.now(timezone.utc).isoformat()
        self.membership['official_evidence'] = [{'url': 'https://unofficial.example/'}]
        with self.assertRaisesRegex(p.ProvisionError, 'government URL'): self.check()

    def test_cli_explicit_inputs_print_proposal_without_materialization(self):
        self.install_fixture_profile()
        args = self.kwargs()
        membership, coverage = self.f.base / 'membership.json', self.f.base / 'coverage.json'
        membership.write_bytes(args['membership_bytes']); coverage.write_bytes(args['coverage_bytes'])
        argv = ['provision_goyang.py', '--repo', str(self.f.repo), '--control-revision', self.f.control,
                '--target-revision', 'absent', '--site-key', SITE, '--launch-key', LAUNCH,
                '--scope-mode', 'whole-dong-initial', '--scope-key', SCOPE,
                '--membership-json', str(membership), '--membership-sha256', args['membership_sha256'],
                '--coverage-json', str(coverage), '--coverage-sha256', args['coverage_sha256'], '--dry-run']
        out = io.StringIO()
        with patch.object(sys, 'argv', argv), patch.object(p, 'materialize', side_effect=AssertionError('no write')), redirect_stdout(out):
            p.main()
        plan = json.loads(out.getvalue())
        self.assertEqual(plan['initialScope']['scopeKey'], SCOPE)
        self.assertNotIn('trialDetailTarget', plan)


if __name__ == '__main__':
    unittest.main()
