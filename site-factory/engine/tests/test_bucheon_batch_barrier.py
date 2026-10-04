"""Synthetic integrity fixtures only, never actual content approval or HTTP QA."""
import base64
import copy
import hashlib
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import render_snapshot as renderer
from batch_barrier import BUCHEON_SITE, BUCHEON_SCOPE, BUCHEON_TARGET, GOYANG_GATES, GitEvidence, check, identity
from test_goyang_batch_barrier import MemoryGit, make_body, encode, BASE, FINAL

ROOT = BUCHEON_TARGET['root']
MEMBERSHIP = hashlib.sha256(b'synthetic-membership-not-real-geography').hexdigest()
FILES = ('publish-manifest', 'page-map', 'pages', 'architecture')
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9ZlS8AAAAASUVORK5CYII=')


def fixture(count=3):
    units = [{'unitKey': f'unit-{i}', 'name': f'합성{i}동', 'unitType': 'legal-dong',
              'districtKeys': ['fixture'], 'legalRi': []} for i in range(1, count + 1)]
    representatives = [{'pageKey': f'region-{i}', 'slug': f'dong-{i}', 'url': f'/regions/dong-{i}/',
                       'unitKeys': [u['unitKey']], 'intentKey': f'bucheon|flower-delivery|local-order|dong-{i}',
                       'primaryKeyword': f'합성{i}동 꽃배달', 'status': 'approved', 'routeMode': 'regional',
                       'queryEvidence': 'Synthetic fixture, not actual approval'} for i, u in enumerate(units, 1)]
    coverage = {'membershipSourceSha256': MEMBERSHIP, 'schemaVersion': 2, 'siteKey': BUCHEON_SITE, 'scopeKey': BUCHEON_SCOPE,
                'unitBasis': 'legal-dong-plus-eup-myeon', 'countIsPageQuota': False,
                'officialSourceUrls': ['https://www.bucheon.go.kr/'],
                'districts': [{'key': 'fixture', 'name': '합성구'}], 'units': units,
                'administrativeCrosswalk': [{'aliasKey': f'admin-{i}', 'name': f'합성행정{i}동',
                   'districtKey': 'fixture', 'relations': [{'unitKey': u['unitKey'], 'scope': 'whole'}]}
                   for i, u in enumerate(units, 1)], 'representatives': representatives}
    policy = {'membershipSourceSha256': MEMBERSHIP, 'schemaVersion': 1, 'siteKey': BUCHEON_SITE, 'scopeKey': BUCHEON_SCOPE, 'enabled': True,
              'unitTypes': ['legal-dong'], 'officialHosts': ['www.bucheon.go.kr'],
              'visualBindings': [{'pageKey': r['pageKey'], 'image': '/images/fixture.png', 'alt': 'Synthetic fixture',
                 'sha256': hashlib.sha256(PNG).hexdigest(), 'sourceUrl': 'https://fwith.co.kr/',
                 'status': 'approved', 'purchaseMode': 'catalog', 'productKeys': ['fixture-product'],
                 'assetType': 'brand', 'verifiedAt': '2026-10-04', 'width': 1, 'height': 1, 'type': 'image/png'}
                 for r in representatives]}
    products = [{'key': 'fixture-product', 'family': 'bouquet', 'sourceUrl': 'https://fwith.co.kr/'}]
    registry = {'sites': {BUCHEON_SITE: {**BUCHEON_TARGET, 'snapshotRenderer': 'structured-json-v12',
       'allowedCategories': ['regions', 'funeral'], 'allowedPageTypes': ['regional-service', 'funeral-facility'],
       'categoryPageTypes': {'regions': ['regional-service'], 'funeral': ['funeral-facility']},
       'regionalService': {'enabled': True, 'scopeKey': BUCHEON_SCOPE,
                           'definitionFile': 'src/data/region-coverage.json', 'policyFile': 'src/data/region-policy.json'},
       'productionEnabled': False,
       'growthPaused': True, 'autoDeploySnapshots': False, 'requireRevisionApproval': True, 'requireSnapshotApproval': True}}}
    docs = {(BASE, '.github/site-factory-sites.json'): encode(registry),
            (BASE, 'site-factory/engine/render_snapshot.py'): Path(renderer.__file__).read_bytes()}
    history = [BASE]
    deps = {'src/data/region-coverage.json': encode(coverage), 'src/data/region-policy.json': encode(policy),
            'src/data/products.json': encode(products), 'public/images/fixture.png': PNG}
    with tempfile.TemporaryDirectory(prefix='bucheon-fixture-') as temp:
        workspace = Path(temp); data = workspace / ROOT / 'src/data'; data.mkdir(parents=True)
        for path, raw in deps.items():
            file = workspace / ROOT / path; file.parent.mkdir(parents=True, exist_ok=True); file.write_bytes(raw)
        for name in FILES:
            value = [] if name == 'pages' else {'siteKey': BUCHEON_SITE, 'pages': []}
            if name == 'architecture':
                value['hubs'] = [{'url': f'/{category}/', 'category': category, 'children': 0, 'indexable': False}
                                 for category in ('funeral', 'regions', 'gift')]
            (data / (name + '.json')).write_bytes(encode(value))
        common = dict(SITE_KEY=BUCHEON_SITE, TARGET_REPO=BUCHEON_TARGET['repo'],
                      TARGET_BRANCH=BUCHEON_TARGET['branch'], TARGET_ROOT=ROOT, REGION='부천')
        baseline_body = make_body(900, **common, PAGE_KEY='existing-facility', CATEGORY='funeral',
            PAGE_TYPE='funeral-facility', PAGE_ROLE='PLACE_LANDING', PARENT_HUB='/funeral/')
        renderer.render(baseline_body, registry, workspace)
        def checkpoint(revision):
            for name in FILES:
                docs[(revision, ROOT + '/src/data/' + name + '.json')] = (data / (name + '.json')).read_bytes()
            docs.update({(revision, ROOT + '/' + path): raw for path, raw in deps.items()})
        checkpoint(BASE)
        batch = {'membershipSourceSha256': MEMBERSHIP, 'schemaVersion': 2, 'contractType': 'bucheon-all-remaining-legal-dongs', 'batchId': 'synthetic-bucheon',
            'siteKey': BUCHEON_SITE, 'scopeKey': BUCHEON_SCOPE, 'baselineSourceSha': BASE,
            'baselineManifestSha256': hashlib.sha256(docs[(BASE, ROOT + '/src/data/publish-manifest.json')]).hexdigest(),
            'coverageSha256': hashlib.sha256(deps['src/data/region-coverage.json']).hexdigest(),
            'policySha256': hashlib.sha256(deps['src/data/region-policy.json']).hexdigest(),
            'productsSha256': hashlib.sha256(deps['src/data/products.json']).hexdigest(),
            'ruleRevision': BASE, 'templateRevision': BASE, 'registryRevision': BASE,
            'members': [{key: r[key] for key in ('pageKey', 'intentKey')} for r in representatives]}
        batch['membershipHash'] = identity(batch); items = []
        for i, member in enumerate(batch['members'], 1):
            body = make_body(i, **common, INTENT_KEY=member['intentKey'], SOURCES='https://www.bucheon.go.kr/',
                             **{'SOURCE-TYPES': 'official'})
            p = renderer.validate_content(renderer.parse_payload(body)); storage, reviewed = renderer.frozen_hashes(p)
            renderer.render(body, registry, workspace); commit = f'{i:040x}'; history.append(commit); checkpoint(commit)
            items.append({**member, 'ruleRevision': BASE, 'templateRevision': BASE, 'registryRevision': BASE,
               'draftRevision': 'synthetic-r1', 'writerRunId': 'synthetic-writer', 'payload': body,
               'reviewDigest': reviewed, 'snapshotHash': storage, 'queueRecordId': p['PUBLISH_QUEUE_RECORD_ID'],
               'issueUrl': f'https://github.com/{BUCHEON_TARGET["repo"]}/issues/{i}', 'snapshotId': p['SNAPSHOT_ID'],
               'commitSha': commit, 'reviewSourceSha': BASE, 'reviewerApproval': {'status': 'approved',
                  'reviewer': 'synthetic-independent-reviewer', 'evidenceUrl': 'https://example.com/not-real-approval',
                  'draftRevision': 'synthetic-r1', 'reviewDigest': reviewed, 'membershipHash': batch['membershipHash']}})
        history.append(FINAL); checkpoint(FINAL)
    manifest = json.loads(docs[(FINAL, ROOT + '/src/data/publish-manifest.json')])
    qa = {'sourceSha': FINAL, 'manifestSha256': hashlib.sha256(docs[(FINAL, ROOT + '/src/data/publish-manifest.json')]).hexdigest(),
          'state': 'passed', 'environment': 'staging', 'noindex': True, 'reviewer': 'synthetic-qa',
          'evidenceUrl': 'https://example.com/not-real-qa', 'gates': sorted(GOYANG_GATES),
          'routes': [{'url': url, 'state': 'passed', 'noindex': True}
                     for url in ['/', '/funeral/', '/regions/'] + [p['url'] for p in manifest['pages']]],
          'notFoundRoutes': [{'url': url, 'state': 'passed', 'status': 404, 'canonicalAbsent': True}
                            for url in ['/gift/', '/site-factory-live-qa-definitely-not-found/']],
          'aliasCoverageSha256': batch['coverageSha256'],
          'discoverableNames': sorted({r['name'] for r in units + coverage['administrativeCrosswalk']})}
    return batch, {'batchId': batch['batchId'], 'membershipHash': batch['membershipHash'], 'finalSourceSha': FINAL,
                   'items': items, 'qa': qa}, MemoryGit(docs, history)


class BucheonBarrierTests(unittest.TestCase):
    def setUp(self): self.batch, self.evidence, self.git = fixture()
    def check(self): return check(self.batch, self.evidence, self.git)
    def doc(self, revision, path, change):
        key = (revision, ROOT + '/' + path); value = json.loads(self.git.documents[key]); change(value)
        self.git.documents[key] = encode(value)
    def rebind(self):
        self.batch['membershipHash'] = identity(self.batch); self.evidence['membershipHash'] = self.batch['membershipHash']
        for item in self.evidence['items']: item['reviewerApproval']['membershipHash'] = self.batch['membershipHash']
    def test_readonly_repeat_and_derived_counts(self):
        before = copy.deepcopy((self.batch, self.evidence, self.git.documents))
        result = self.check(); self.assertEqual(result, self.check())
        self.assertEqual((result['baselineDetailCount'], result['newDetailCount'], result['detailCount'], result['qaRouteCount']), (1, 3, 4, 7))
        self.assertFalse(result['productionApproved']); self.assertFalse(result['indexNowAllowed'])
        self.assertEqual(before, (self.batch, self.evidence, self.git.documents))
    def test_synthetic_24_renderer_replay_is_not_a_quota(self):
        b, e, g = fixture(24); result = check(b, e, g)
        self.assertEqual((result['newDetailCount'], result['detailCount'], result['qaRouteCount']), (24, 25, 28))
    def test_two_members_are_valid_when_pinned_geography_has_two(self):
        b, e, g = fixture(2); self.assertEqual(check(b,e,g)['newDetailCount'], 2)
    def test_exact_site_scope_contract_only(self):
        for field, value in [('siteKey', 'other-city'), ('scopeKey', 'future-scope'), ('contractType', 'generic'), ('schemaVersion', True)]:
            with self.subTest(field=field):
                b = copy.deepcopy(self.batch); b[field] = value
                with self.assertRaises((ValueError, KeyError)): check(b, self.evidence, self.git)
    def test_registered_adapter_and_target_fail_closed(self):
        for field, value in [('regionalService', {'enabled': False, 'scopeKey': BUCHEON_SCOPE}),
                             ('regionalService', {'enabled': True, 'scopeKey': 'other'}),
                             ('administrativeCoverage', {'enabled': True}), ('root', 'other'),
                             ('branch', 'other'), ('growthPaused', False), ('autoDeploySnapshots', True),
                             ('requireSnapshotApproval', False), ('requireRevisionApproval', False)]:
            with self.subTest(field=field):
                g = copy.deepcopy(self.git); key = (BASE, '.github/site-factory-sites.json'); reg = json.loads(g.documents[key])
                reg['sites'][BUCHEON_SITE][field] = value; g.documents[key] = encode(reg)
                with self.assertRaises(ValueError): check(self.batch, self.evidence, g)
    def test_exact_four_field_adapter_contract_rejects_missing_changed_or_extra_keys(self):
        key = (BASE, '.github/site-factory-sites.json')
        original = json.loads(self.git.documents[key])
        profile = original['sites'][BUCHEON_SITE]['regionalService']
        changes = []
        for field in profile:
            candidate = copy.deepcopy(profile); del candidate[field]; changes.append(candidate)
        for field, value in [('enabled', False), ('enabled', 1), ('scopeKey', 'unregistered-scope'),
                             ('definitionFile', 'src/data/other.json'), ('definitionFile', '../coverage.json'),
                             ('policyFile', 'src/data/other.json'), ('policyFile', True)]:
            changes.append({**profile, field: value})
        changes.append({**profile, 'arbitraryFutureOverride': True})
        for candidate in changes:
            with self.subTest(profile=candidate):
                git = copy.deepcopy(self.git); registry = copy.deepcopy(original)
                registry['sites'][BUCHEON_SITE]['regionalService'] = candidate
                git.documents[key] = encode(registry)
                with self.assertRaisesRegex(ValueError, 'Bucheon registered adapter mismatch'):
                    check(self.batch, self.evidence, git)

    def test_membership_shrink_even_rehashed_fails(self):
        self.batch['members'].pop(); self.rebind()
        with self.assertRaisesRegex(ValueError, 'every remaining'): self.check()
    def test_each_dependency_is_pinned_at_every_checkpoint_and_final(self):
        paths = ['src/data/region-coverage.json', 'src/data/region-policy.json', 'src/data/products.json', 'public/images/fixture.png']
        for revision in self.git.history[1:]:
            for path in paths:
                with self.subTest(revision=revision, path=path):
                    g = copy.deepcopy(self.git); g.documents[(revision, ROOT + '/' + path)] += b'\n'
                    with self.assertRaises(ValueError): check(self.batch, self.evidence, g)
    def test_dependency_digest_and_identity_binding(self):
        for field in ['policySha256', 'productsSha256', 'membershipSourceSha256']:
            with self.subTest(field=field):
                b=copy.deepcopy(self.batch); b[field]='0'*64
                self.assertNotEqual(identity(b), self.batch['membershipHash'])
                b['membershipHash']=identity(b); e=copy.deepcopy(self.evidence); e['membershipHash']=b['membershipHash']
                with self.assertRaises(ValueError): check(b,e,self.git)
    def test_renderer_bytes_pin(self):
        self.git.documents[(BASE,'site-factory/engine/render_snapshot.py')] += b'\n'
        with self.assertRaisesRegex(ValueError,'pinned controller'): self.check()
    def test_unsupported_site_catalog_not_silently_omitted(self):
        for revision in self.git.history:
            with self.subTest(revision=revision):
                g=copy.deepcopy(self.git); g.documents[(revision, ROOT+'/src/data/site-catalog.json')]=b'{}'
                with self.assertRaisesRegex(ValueError,'site-local catalog'): check(self.batch,self.evidence,g)
    def test_coverage_alias_and_representative_counterexamples(self):
        mutations = [lambda c:c['representatives'].pop(), lambda c:c['representatives'][0].update(status='candidate'),
           lambda c:c['representatives'][0].update(unitKeys=[]), lambda c:c['representatives'][0].update(unitKeys=['unknown']),
           lambda c:c['representatives'][0].update(unitKeys=c['representatives'][1]['unitKeys']),
           lambda c:c['units'][0].update(unitType='eup'), lambda c:c['administrativeCrosswalk'][0].update(relations=[]),
           lambda c:c['administrativeCrosswalk'][0]['relations'][0].update(unitKey='unknown'),
           lambda c:c['administrativeCrosswalk'][0]['relations'][0].update(scope='name-only'),
           lambda c:c['administrativeCrosswalk'][0].update(unresolvedCandidateNames=['unknown'])]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                b,e,g=copy.deepcopy((self.batch,self.evidence,self.git)); key=(BASE,ROOT+'/src/data/region-coverage.json')
                value=json.loads(g.documents[key]); mutate(value); raw=encode(value)
                for revision in g.history:g.documents[(revision,ROOT+'/src/data/region-coverage.json')]=raw
                b['coverageSha256']=hashlib.sha256(raw).hexdigest(); b['membershipHash']=identity(b);e['membershipHash']=b['membershipHash']
                with self.assertRaises(ValueError):check(b,e,g)
    def test_baseline_and_whole_snapshot_bytes_preserved(self):
        for name in FILES:
            with self.subTest(name=name):
                g=copy.deepcopy(self.git); g.documents[(self.evidence['items'][0]['commitSha'],ROOT+'/src/data/'+name+'.json')] += b'\n'
                with self.assertRaisesRegex(ValueError,'pinned renderer'):check(self.batch,self.evidence,g)
    def test_reviewer_identity_and_evidence_url_types_fail_closed(self):
        invalid = {'reviewer': [True, 1, None, {}, [], '', '   '],
                   'evidenceUrl': [True, 1, None, {}, [], '', ' ', 'http://example.com/proof',
                      'https://', 'https://user:password@example.com/proof',
                      'https://example.com/proof with space', ' https://example.com/proof']}
        for target in ('content', 'qa'):
            for field, values in invalid.items():
                for value in values:
                    with self.subTest(target=target, field=field, value=value):
                        evidence = copy.deepcopy(self.evidence)
                        record = evidence['qa'] if target == 'qa' else evidence['items'][0]['reviewerApproval']
                        record[field] = value
                        with self.assertRaises(ValueError): check(self.batch, evidence, self.git)
        for target in ('content', 'qa'):
            evidence = copy.deepcopy(self.evidence)
            record = evidence['qa'] if target == 'qa' else evidence['items'][0]['reviewerApproval']
            record['reviewer'] = ' synthetic-writer '
            with self.assertRaisesRegex(ValueError, '[Ii]ndependent'): check(self.batch, evidence, self.git)

    def test_actual_approval_sequence_and_qa_required(self):
        mutations=[lambda e:e['items'][0]['reviewerApproval'].update(status='pending'),
          lambda e:e['items'][0]['reviewerApproval'].update(reviewer='synthetic-writer'),
          lambda e:e['items'][0].update(reviewSourceSha=FINAL),lambda e:e['items'].reverse(),lambda e:e['items'].pop(),
          lambda e:e['qa']['routes'].pop(),lambda e:e['qa']['notFoundRoutes'].pop(),
          lambda e:e['qa']['discoverableNames'].pop(),lambda e:e['qa'].update(sourceSha=BASE),
          lambda e:e['qa'].update(manifestSha256='0'*64),lambda e:e['qa'].update(noindex=False)]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                e=copy.deepcopy(self.evidence);mutate(e)
                with self.assertRaises(ValueError):check(self.batch,e,self.git)


def committed_fixture(workspace, mode_target=None):
    """Disposable real Git proof, optionally change only an input's tree mode."""
    batch, evidence, memory = fixture(2)
    review = 'e' * 40
    memory.history.insert(1, review)
    for (revision, path), raw in list(memory.documents.items()):
        if revision == BASE:
            memory.documents[(review, path)] = raw
    evidence['items'][1]['reviewSourceSha'] = review
    def git(*args):
        return subprocess.check_output(['git', '-C', str(workspace), *args], stderr=subprocess.PIPE).decode().strip()
    git('init', '-q'); git('config', 'user.name', 'Synthetic Test')
    git('config', 'user.email', 'test@example.invalid')
    revisions = {}
    for revision in memory.history:
        for (rev, path), raw in memory.documents.items():
            if rev == revision:
                file = workspace / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(raw)
        git('add', '.')
        if mode_target and revision == mode_target[0]:
            path = mode_target[1]
            blob = git('hash-object', path)
            git('update-index', '--cacheinfo', f'120000,{blob},{path}')
        git('commit', '-q', '--allow-empty', '-m', 'Synthetic integrity fixture')
        revisions[revision] = git('rev-parse', 'HEAD')
    for field in ('baselineSourceSha', 'ruleRevision', 'templateRevision', 'registryRevision'):
        batch[field] = revisions[batch[field]]
    batch['membershipHash'] = identity(batch)
    evidence['membershipHash'] = batch['membershipHash']
    evidence['finalSourceSha'] = evidence['qa']['sourceSha'] = revisions[FINAL]
    for item in evidence['items']:
        for field in ('commitSha', 'reviewSourceSha', 'ruleRevision', 'templateRevision', 'registryRevision'):
            item[field] = revisions[item[field]]
        item['reviewerApproval']['membershipHash'] = batch['membershipHash']
    return batch, evidence, GitEvidence(workspace)


class BucheonGitModeTests(unittest.TestCase):
    def test_regular_committed_files_and_dirty_files_are_separate(self):
        with tempfile.TemporaryDirectory(prefix='bucheon-regular-files-test-') as directory:
            workspace = Path(directory)
            batch, evidence, git = committed_fixture(workspace)
            result = check(batch, evidence, git)
            (workspace / ROOT / 'src/data/pages.json').write_text('dirty bytes must not count')
            (workspace / ROOT / 'src/data/site-catalog.json').write_text('untracked file must not count')
            self.assertEqual(result, check(batch, evidence, git))
    def test_byte_identical_json_symlinks_at_all_consumed_revisions_fail(self):
        # Includes a distinct review revision before the first snapshot commit.
        for revision in (BASE, '1'.zfill(40), 'e' * 40, FINAL):
            for name in FILES:
                with self.subTest(revision=revision, name=name):
                    with tempfile.TemporaryDirectory(prefix='bucheon-json-mode-test-') as directory:
                        args = committed_fixture(Path(directory), (revision, ROOT + '/src/data/' + name + '.json'))
                        with self.assertRaisesRegex(ValueError, 'committed regular file'):
                            check(*args)
    def test_byte_identical_pinned_controller_symlinks_fail(self):
        for path in ('.github/site-factory-sites.json', 'site-factory/engine/render_snapshot.py'):
            with self.subTest(path=path):
                with tempfile.TemporaryDirectory(prefix='bucheon-controller-mode-test-') as directory:
                    args = committed_fixture(Path(directory), (BASE, path))
                    with self.assertRaisesRegex(ValueError, 'committed regular file'):
                        check(*args)
    def test_goyang_profile_does_not_use_bucheon_mode_guards(self):
        from test_goyang_batch_barrier import fixture as goyang_fixture
        args = goyang_fixture()
        with patch('batch_barrier.read_bucheon_dependency', side_effect=AssertionError('Bucheon-only scope')):
            self.assertEqual(check(*args)['state'], 'staging_complete')


if __name__ == '__main__': unittest.main()
