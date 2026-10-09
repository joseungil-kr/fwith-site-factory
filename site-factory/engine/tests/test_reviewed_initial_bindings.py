"""Synthetic bindings only; these fixtures never authorize regional publication."""
import copy
import inspect
import json
import hashlib
import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import test_whole_initial as existing
import whole_initial as whole
import batch_barrier as barrier


def cross_district_fixture(members, coverage):
    """Reuse the exact existing Anyang exception shape, never factual approval."""
    from test_cross_district import ExactCrossDistrictTests
    fixture = ExactCrossDistrictTests(); fixture.setUp()
    member, unit, alias = members[0], coverage['units'][0], coverage['administrativeCrosswalk'][0]
    member.update(unit_key=fixture.unit['unitKey'], name='안양동', district_key='manan')
    unit.update(unitKey=member['unit_key'], name=member['name'], districtKeys=['manan'])
    alias.update(aliasKey=fixture.alias['aliasKey'], districtKey='dongan', name='비산1동',
                 relations=[{'unitKey':member['unit_key'], **fixture.relation}])
    coverage['representatives'][0]['unitKeys'] = [member['unit_key']]
    coverage['officialSourceUrls'].append(fixture.source)
    coverage['districts'].extend([{'key':key,'name':key,'sourceUrl':fixture.source}
                                 for key in ('manan','dongan')])


def regional_fixture(site, cross_district=False, runtime_files=False):
    slug = site.split('-')[0]
    city = whole.ALL_INITIAL_REGIONS[site]
    namespace = dict(existing.fixture.__globals__)
    namespace.update(SITE=site, SCOPE=site + '-dong-coverage-20261009',
                     ROOT='site-factory/' + slug + '-flower')
    source = inspect.getsource(existing.fixture).replace('namyangju', slug).replace('남양주', city)
    namespace['patch'] = patch
    source = source.replace("    registry={'sites':{SITE:target}}", "    target['initialReviewEvidenceUrl']='https://github.com/joseungil-kr/fwith-site-factory/issues/999999'\n    registry={'sites':{SITE:target}}")
    source = source.replace("            renderer.render(body,registry,workspace);", "            binding={'initialLaunch':target['initialLaunch'],'bootstrapSourceSha':BOOTSTRAP,'templateRevision':BASE,'reviewEvidenceUrl':target['initialReviewEvidenceUrl']}\n            with patch.dict(whole.ADDITIONAL_REVIEWED_RELEASES,{SITE:binding}), patch.dict(whole.ALL_INITIAL_SOURCE_PROFILES,{SITE:profile}):\n                renderer.render(body,registry,workspace);\n            ")
    if cross_district:
        source = source.replace("    policy={'schemaVersion'", "    cross_district_fixture(members, coverage)\n    initial['memberIdentitySha256']=barrier.digest(members)\n    policy={'schemaVersion'")
        namespace['cross_district_fixture'] = cross_district_fixture
    if runtime_files:
        source = source.replace('    history=[BASE]', "    deps.update({'scripts/qa_static.py':b'# synthetic original QA\\n','src/data/social-image-provenance.json':b'{}\\n','src/lib/catalog.mjs':b'// synthetic original catalog\\n','src/pages/index.astro':b'<!-- synthetic original index -->\\n'})\n    history=[BASE]")
    exec(compile(source, '<synthetic regional fixture>', 'exec'), namespace)
    batch, evidence, git, profile = namespace['fixture']()
    key = (existing.BASE, '.github/site-factory-sites.json')
    registry = json.loads(git.documents[key])
    target = registry['sites'][site]
    url = 'https://github.com/joseungil-kr/fwith-site-factory/issues/999999'
    target['initialReviewEvidenceUrl'] = url
    git.documents[key] = existing.encode(registry)
    binding = {'initialLaunch': copy.deepcopy(target['initialLaunch']),
               'bootstrapSourceSha': existing.BOOTSTRAP,
               'templateRevision': profile['sourceRevision'], 'reviewEvidenceUrl': url}
    return batch, evidence, git, profile, binding


def production_fixture(batch, evidence, git, site_key):
    """Build only the existing allowed production transition from rendered bytes."""
    preview = existing.FINAL
    production = 'c' * 40
    registry = json.loads(git.documents[(existing.BASE, '.github/site-factory-sites.json')])
    site = copy.deepcopy(registry['sites'][site_key])
    root = site['root']; key = 'a' * 64
    for (revision, path), raw in list(git.documents.items()):
        if revision == preview and path.startswith(root + '/'):
            git.documents[(production, path)] = raw
    config_path = root + '/src/data/site-config.json'
    config = json.loads(git.documents[(production, config_path)])
    config['productionApproved'] = True
    git.documents[(production, config_path)] = existing.encode(config)
    git.documents[(production, root + '/production-indexing.enabled')] = b'approved\n'
    git.documents[(production, root + '/public/' + key + '.txt')] = key.encode() + b'\n'
    git.history.append(production)
    scope = batch['scopeKey']; launch = site_key + '-initial-' + scope[-8:]
    folder = 'site-factory/releases/' + launch
    documents = {folder + '/batch.json': existing.encode(batch),
                 folder + '/evidence.json': existing.encode(evidence)}
    site.update(productionEnabled=True, launchMode='live', approvedRevision=production,
                approvalEvidenceUrl='https://github.com/joseungil-kr/fwith-site-factory/issues/999998',
                indexnowKey=key, initialBootstrapRevision=existing.BOOTSTRAP,
                initialPreviewRevision=preview, initialPreviewBaselineRevision=existing.BASE,
                initialPreviewManifestSha256=evidence['qa']['manifestSha256'])
    site['initialDeployment'] = {'enabled':True,'siteKey':site_key,'launchKey':launch,'scopeKey':scope,
        'bootstrapSourceSha':existing.BOOTSTRAP,'baselineSourceSha':existing.BASE,
        'batchPath':folder + '/batch.json','batchEvidencePath':folder + '/evidence.json',
        'batchSha256':hashlib.sha256(documents[folder + '/batch.json']).hexdigest(),
        'batchEvidenceSha256':hashlib.sha256(documents[folder + '/evidence.json']).hexdigest(),
        **{field:hashlib.sha256(git.documents[(production, root + '/src/data/' + filename)]).hexdigest()
           for field,filename in [('productionManifestSha256','publish-manifest.json'),
                                  ('coverageSha256','region-coverage.json'),('regionPolicySha256','region-policy.json')]}}
    return site, production, documents


class ReviewedInitialBindingTests(unittest.TestCase):
    def test_exact_historical_namyangju_renderer_replays_unchanged_snapshots(self):
        import render_snapshot as renderer
        batch,evidence,git,profile = existing.fixture()
        # Reconstruct the independently fetched original bytes, then require
        # their exact recorded digest before executing the historical fixture.
        raw = Path(renderer.__file__).read_text()
        start = raw.index('    initial_eligibility = (p["SITE_KEY"]')
        end = raw.index('    tables["architecture"][key] = ', start)
        raw = raw[:start] + raw[end:]
        raw = raw.replace('publication_approved if initial_eligibility else bool(target.get("productionEnabled"))',
            'publication_approved if (p["SITE_KEY"] == "namyangju-flower-v2" and target.get("initialLaunch", {}).get("scopeKey") == "namyangju-flower-v2-dong-coverage-20261005" and hub_policy == "child-threshold-v1") else bool(target.get("productionEnabled"))')
        expected = '3ea763515965fcdf43a0f013e0bc44e931e6fb16a21014f12a722f8cf87b2ad9'
        self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(), expected)
        self.assertEqual(barrier.INITIAL_RENDERER_ALLOWLIST,
            {(existing.SITE,'45f13097c9e951934486f88b0735fd59394f20c3'):expected})
        git.documents[(existing.BASE,'site-factory/engine/render_snapshot.py')] = raw.encode()
        initial=json.loads(git.documents[(existing.BASE,'.github/site-factory-sites.json')])['sites'][existing.SITE]['initialLaunch']
        with patch.object(whole,'REVIEWED_BOOTSTRAP_REVISION',existing.BOOTSTRAP), \
                patch.dict(whole.INITIAL_SOURCE_PROFILES,{existing.SITE:profile}), \
                patch.dict(whole.REVIEWED_INITIAL,initial,clear=True):
            # An unregistered historical tuple still fails before execution.
            with self.assertRaisesRegex(ValueError,'renderer differs'):
                barrier.check(batch,evidence,git)
            with patch.dict(barrier.INITIAL_RENDERER_ALLOWLIST,{(existing.SITE,existing.BASE):expected}):
                self.assertEqual(barrier.check(batch,evidence,git)['state'],'staging_complete')
                git.documents[(existing.BASE,'site-factory/engine/render_snapshot.py')] += b'\n'
                with self.assertRaisesRegex(ValueError,'renderer differs'):
                    barrier.check(batch,evidence,git)

    def test_known_initial_candidates_never_fall_back_without_binding(self):
        import yaml
        import provision_goyang as provision
        repo = Path(__file__).resolve().parents[3]
        targets = [('site-staging-deploy.yml','Resolve isolated preview target'),
                   ('site-production-deploy.yml','Resolve approved production target'),
                   ('site-production-deploy.yml','Resolve existing public target without deployment')]
        for site_key in ('pyeongtaek-flower-v2','anyang-flower-v2'):
            self.assertTrue(whole.is_initial_candidate(site_key))
            entry = provision.site_entry(site_key)
            entry.update(productionEnabled=True, launchMode='live', approvedRevision='a'*40,
                         approvalEvidenceUrl='https://github.com/joseungil-kr/fwith-site-factory/actions/runs/1')
            for filename, name in targets:
                doc = yaml.safe_load((repo/'.github/workflows'/filename).read_text())
                step = next(s for job in doc['jobs'].values() for s in job['steps'] if s.get('name') == name)
                code = step['run'].split("<<'PYTHON'\n",1)[1].split('\nPYTHON',1)[0]
                with self.subTest(site=site_key,step=name), tempfile.TemporaryDirectory() as directory:
                    temp = Path(directory); (temp/'control/.github').mkdir(parents=True)
                    (temp/'control/.github/site-factory-sites.json').write_text(json.dumps({'sites':{site_key:entry}}))
                    original = Path.cwd()
                    try:
                        os.chdir(temp)
                        with patch.dict(os.environ, {'SITE_KEY':site_key,'REVISION':'a'*40,'ISSUE_BODY':'',
                            'GITHUB_REPOSITORY':provision.REPOSITORY,'GITHUB_OUTPUT':str(temp/'outputs')},clear=True), \
                            self.assertRaisesRegex(ValueError,'reviewed release binding'):
                            exec(code, {})
                        self.assertFalse((temp/'outputs').exists())
                    finally: os.chdir(original)

    def test_real_renderer_barrier_preview_and_release_with_no_eligibility_repair(self):
        for site_key, cross_district in [('pyeongtaek-flower-v2',False),('anyang-flower-v2',True)]:
            batch,evidence,git,profile,binding = regional_fixture(site_key,cross_district)
            with self.subTest(site=site_key), patch.dict(whole.ALL_INITIAL_SOURCE_PROFILES,{site_key:profile}), \
                    patch.dict(whole.ADDITIONAL_REVIEWED_RELEASES,{site_key:binding}):
                self.assertEqual(barrier.check(batch,evidence,git)['state'],'staging_complete')
                site,production,documents = production_fixture(batch,evidence,git,site_key)
                architecture = json.loads(git.documents[(existing.FINAL,site['root']+'/src/data/architecture.json')])
                self.assertTrue(all(row['sitemapIndexable'] is True for row in architecture['pages']))
                class FixtureGit:
                    def __new__(cls, workspace): return git
                with tempfile.TemporaryDirectory() as directory:
                    workspace=Path(directory); preview_root=workspace/'preview'; production_root=workspace/'production'; control=workspace/'control'
                    for revision,destination in [(existing.FINAL,preview_root),(production,production_root)]:
                        for (source,path),raw in git.documents.items():
                            if source==revision and path.startswith(site['root']+'/'):
                                file=destination/path[len(site['root'])+1:];file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(raw)
                    for path,raw in documents.items():
                        file=control/path;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(raw)
                    self.assertEqual(whole.validate_preview_source(site,site_key,existing.FINAL,preview_root,git=git)['details'],3)
                    with patch.object(barrier,'GitEvidence',FixtureGit):
                        result=whole.verify_release(site,production,production_root,control,workspace)
                    self.assertEqual(result['pipelineState'],'initial_source_validated')
                    # The release gate must still reject stale eligibility, not repair it.
                    architecture['pages'][0]['sitemapIndexable']=False
                    (production_root/'src/data/architecture.json').write_bytes(existing.encode(architecture))
                    with patch.object(barrier,'GitEvidence',FixtureGit), self.assertRaisesRegex(ValueError,'sitemap eligibility'):
                        whole.verify_release(site,production,production_root,control,workspace)

    def test_exact_anyang_exception_rejects_other_pairs_scopes_and_evidence(self):
        site='anyang-flower-v2'
        batch,evidence,git,profile,binding=regional_fixture(site,True)
        coverage=json.loads(git.documents[(existing.BASE,'site-factory/anyang-flower/src/data/region-coverage.json')])
        barrier.bucheon_representatives(coverage,site,batch['scopeKey'])
        for mutation in ('missing','wrong_source','whole','wrong_pair','wrong_site'):
            changed=copy.deepcopy(coverage);alias=changed['administrativeCrosswalk'][0];relation=alias['relations'][0]
            if mutation=='missing':relation.pop('crossDistrictEvidence')
            elif mutation=='wrong_source':relation['crossDistrictEvidence']['sourceUrl']='https://example.com/'
            elif mutation=='whole':relation['scope']='whole'
            elif mutation=='wrong_pair':alias['aliasKey']='other'
            else:changed['siteKey']='pyeongtaek-flower-v2'
            with self.subTest(mutation=mutation),self.assertRaisesRegex(ValueError,'relation mismatch'):
                barrier.bucheon_representatives(changed,changed['siteKey'],batch['scopeKey'])

    def test_shipping_candidate_does_not_enable_unreviewed_sites(self):
        self.assertEqual(whole.ADDITIONAL_REVIEWED_RELEASES, {})
        for site in ('pyeongtaek-flower-v2', 'anyang-flower-v2', 'unknown'):
            with self.subTest(site=site):
                self.assertFalse(whole.is_reviewed_initial_site(site))
                with self.assertRaises(ValueError): whole.reviewed_release_binding(site)

    def test_existing_namyangju_profile_is_unchanged(self):
        binding = whole.reviewed_release_binding(existing.SITE)
        self.assertIs(binding['initialLaunch'], whole.REVIEWED_INITIAL)
        self.assertEqual(binding['bootstrapSourceSha'], whole.REVIEWED_BOOTSTRAP_REVISION)
        self.assertEqual(whole.REVIEWED_INITIAL['officialUnitCount'], 20)

    def test_both_provision_profiles_reuse_full_serial_barrier(self):
        for site in ('pyeongtaek-flower-v2', 'anyang-flower-v2'):
            batch, evidence, git, profile, binding = regional_fixture(site)
            with self.subTest(site=site), patch.dict(whole.ALL_INITIAL_SOURCE_PROFILES, {site: profile}), \
                    patch.dict(whole.ADDITIONAL_REVIEWED_RELEASES, {site: binding}):
                result = barrier.check(batch, evidence, git)
                self.assertEqual(result['detailCount'], 3)
                self.assertEqual(result['baselineDetailCount'], 0)
                self.assertEqual(result, barrier.check(batch, evidence, git))

    def test_missing_or_changed_exact_binding_fails(self):
        site = 'pyeongtaek-flower-v2'
        batch, evidence, git, profile, binding = regional_fixture(site)
        mutations = [
            lambda b: b.pop('reviewEvidenceUrl'),
            lambda b: b.update(reviewEvidenceUrl='https://example.com/unreviewed'),
            lambda b: b.update(templateRevision='0' * 40),
            lambda b: b.update(bootstrapSourceSha='0' * 40),
            lambda b: b['initialLaunch'].update(officialUnitCount=2),
            lambda b: b['initialLaunch'].update(officialUnitCount=True),
            lambda b: b['initialLaunch'].update(membershipSourceSha256='0' * 64),
            lambda b: b['initialLaunch'].update(memberIdentitySha256='0' * 64),
            lambda b: b['initialLaunch'].update(coverageSha256='0' * 64),
            lambda b: b['initialLaunch'].update(scopeKey=site + '-dong-coverage-20261309'),
        ]
        for index, mutate in enumerate(mutations):
            changed = copy.deepcopy(binding); mutate(changed)
            with self.subTest(index=index), patch.dict(whole.ALL_INITIAL_SOURCE_PROFILES, {site: profile}), \
                    patch.dict(whole.ADDITIONAL_REVIEWED_RELEASES, {site: changed}), self.assertRaises(ValueError):
                barrier.check(batch, evidence, git)

    def test_membership_and_independent_review_checks_stay_strict(self):
        site = 'pyeongtaek-flower-v2'
        for mutation in ('substitution', 'partial', 'self_approval', 'review_evidence', 'source_bytes'):
            batch, evidence, git, profile, binding = regional_fixture(site)
            if mutation == 'substitution': batch['members'][0]['pageKey'] = site + '-region-other'
            elif mutation == 'partial': batch['members'].pop()
            elif mutation == 'self_approval': evidence['items'][0]['reviewerApproval']['reviewer'] = 'synthetic-writer'
            elif mutation == 'review_evidence':
                key = (existing.BASE, '.github/site-factory-sites.json')
                registry = json.loads(git.documents[key]); registry['sites'][site]['initialReviewEvidenceUrl'] += '1'
                git.documents[key] = existing.encode(registry)
            else: git.documents[(existing.FINAL, 'site-factory/pyeongtaek-flower/src/lib/fixture.mjs')] = b'changed'
            if mutation in ('substitution', 'partial'):
                batch['membershipHash'] = barrier.identity(batch)
                evidence['membershipHash'] = batch['membershipHash']
            with self.subTest(mutation=mutation), patch.dict(whole.ALL_INITIAL_SOURCE_PROFILES, {site: profile}), \
                    patch.dict(whole.ADDITIONAL_REVIEWED_RELEASES, {site: binding}), self.assertRaises(ValueError):
                barrier.check(batch, evidence, git)

if __name__ == '__main__': unittest.main()
