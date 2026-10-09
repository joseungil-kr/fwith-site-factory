"""Synthetic37/35 release tests. Test evidence never authorizes publication."""
import copy
import hashlib
import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import test_whole_initial as old
import test_reviewed_initial_bindings as reviewed
import whole_initial as whole
import batch_barrier as barrier
import render_snapshot as renderer
import verify_initial

SITE = 'pyeongtaek-flower-v2'
ROOT = 'site-factory/pyeongtaek-flower'


def fixture():
    namespace = dict(reviewed.regional_fixture.__globals__)
    code = inspect.getsource(reviewed.regional_fixture).replace("namespace['fixture']()", "namespace['fixture'](37)")
    exec(compile(code, '<partial synthetic fixture>', 'exec'), namespace)
    batch, evidence, git, profile, binding = namespace['regional_fixture'](SITE)
    keys = sorted(row['pageKey'] for row in batch['members'])
    deferred = sorted([SITE + '-region-dong-36', SITE + '-region-dong-37'])
    released = sorted(set(keys) - set(deferred))
    subset = {'schemaVersion':1,'mode':'reviewed-partial-initial','siteKey':SITE,
        **{key:binding['initialLaunch'][key] for key in
            ('scopeKey','membershipSourceSha256','memberIdentitySha256','officialUnitCount')},
        'minimumReleasePercent':90,'releasedPageKeys':released,'deferredPageKeys':deferred,
        'reviewEvidenceUrl':'https://github.com/joseungil-kr/fwith-site-factory/issues/999997'}
    binding['releaseSubset'] = subset
    subset_hash = whole.release_subset_digest(subset)
    registry = json.loads(git.documents[(old.BASE,'.github/site-factory-sites.json')])
    registry['sites'][SITE]['initialReleaseSubsetSha256'] = subset_hash
    git.documents[(old.BASE,'.github/site-factory-sites.json')] = old.encode(registry)
    for (revision,path),raw in list(git.documents.items()):
        if revision == old.BOOTSTRAP or not path.startswith(ROOT + '/src/data/'):
            continue
        doc = json.loads(raw)
        name = path.rsplit('/',1)[1]
        if name == 'region-coverage.json':
            for row in doc['representatives']:
                if row['pageKey'] in deferred: row['status'] = 'candidate'
        elif name == 'region-policy.json':
            doc['visualBindings'] = [row for row in doc['visualBindings'] if row['pageKey'] in released]
        elif name in ('pages.json','page-map.json','publish-manifest.json','architecture.json'):
            if isinstance(doc,list): doc = [row for row in doc if row['pageKey'] in released]
            else:
                doc['pages'] = [row for row in doc['pages'] if row['pageKey'] in released]
                if 'snapshotLedger' in doc:
                    doc['snapshotLedger'] = {key:row for key,row in doc['snapshotLedger'].items() if row['pageKey'] in released}
                if 'hubs' in doc:
                    for hub in doc['hubs']:
                        count = sum(row['category'] == hub['category'] for row in doc['pages'])
                        hub.update(children=count,indexable=count>=3,menuVisible=count>=5)
        else: continue
        git.documents[(revision,path)] = old.encode(doc)
    batch['members'] = [row for row in batch['members'] if row['pageKey'] in released]
    batch['releaseSubsetSha256'] = subset_hash
    for field,name in [('coverageSha256','region-coverage'),('policySha256','region-policy')]:
        batch[field] = hashlib.sha256(git.documents[(old.BASE,ROOT+'/src/data/'+name+'.json')]).hexdigest()
    batch['membershipHash'] = barrier.identity(batch)
    evidence['membershipHash'] = batch['membershipHash']
    evidence['items'] = [row for row in evidence['items'] if row['pageKey'] in released]
    for row in evidence['items']: row['reviewerApproval']['membershipHash'] = batch['membershipHash']
    qa = evidence['qa']
    qa['manifestSha256'] = hashlib.sha256(git.documents[(old.FINAL,ROOT+'/src/data/publish-manifest.json')]).hexdigest()
    qa['aliasCoverageSha256'] = batch['coverageSha256']
    qa['releaseSubsetSha256'] = subset_hash
    absent = ['/regions/dong-36/', '/regions/dong-37/']
    qa['routes'] = [row for row in qa['routes'] if row['url'] not in absent]
    qa['notFoundRoutes'] += [{'url':url,'state':'passed','status':404,'canonicalAbsent':True} for url in absent]
    qa['discoverableNames'] = sorted(name for name in qa['discoverableNames'] if name not in
        {'합성36동','합성37동','행정합성36동','행정합성37동'})
    return batch,evidence,git,profile,binding


class PartialInitialTests(unittest.TestCase):
    def setUp(self):
        self.batch,self.evidence,self.git,self.profile,self.binding = fixture()
        self.context = patch.dict(whole.ADDITIONAL_REVIEWED_RELEASES,{SITE:self.binding})
        self.context.start(); self.addCleanup(self.context.stop)
        self.profiles = patch.dict(whole.ALL_INITIAL_SOURCE_PROFILES,{SITE:self.profile})
        self.profiles.start(); self.addCleanup(self.profiles.stop)

    def test_35_of_original37_full_batch_replays(self):
        before = self.git.read(old.BOOTSTRAP,ROOT+'/src/data/region-coverage.json')
        result = barrier.check(self.batch,self.evidence,self.git)
        self.assertEqual(result['state'],'staging_complete')
        self.assertEqual(result['detailCount'],35)
        self.assertEqual(result['qaRouteCount'],37)
        self.assertEqual(self.binding['initialLaunch']['officialUnitCount'],37)
        self.assertEqual(self.git.read(old.BOOTSTRAP,ROOT+'/src/data/region-coverage.json'),before)

    def test_original_partition_not_replaceable(self):
        self.binding['releaseSubset']['deferredPageKeys'][0] = SITE+'-region-invented'
        self.binding['releaseSubset']['deferredPageKeys'].sort()
        with self.assertRaisesRegex(ValueError,'partition differs'):
            whole.released_initial_keys(self.binding,SITE,{row['pageKey'] for row in self.batch['members']} | {SITE+'-region-dong-36',SITE+'-region-dong-37'})

    def test_too_many_deferred_rejected(self):
        subset = self.binding['releaseSubset']
        subset['deferredPageKeys'] = sorted(subset['deferredPageKeys'] + subset['releasedPageKeys'][:2])
        subset['releasedPageKeys'] = subset['releasedPageKeys'][2:]
        with self.assertRaisesRegex(ValueError,'least90'):
            whole.reviewed_release_binding(SITE)

    def test_34_of37_and_exact90_percent_are_accepted(self):
        subset=self.binding['releaseSubset']
        subset['deferredPageKeys']=sorted(subset['deferredPageKeys']+subset['releasedPageKeys'][:1])
        subset['releasedPageKeys']=subset['releasedPageKeys'][1:]
        self.assertIs(whole.reviewed_release_binding(SITE),self.binding)
        keys=sorted(subset['releasedPageKeys'][:9]+subset['deferredPageKeys'][:1])
        self.binding['initialLaunch']['officialUnitCount']=10
        subset.update(officialUnitCount=10,releasedPageKeys=keys[:9],deferredPageKeys=keys[9:])
        self.assertIs(whole.reviewed_release_binding(SITE),self.binding)

    def test_duplicate_or_unreviewed_subset_rejected(self):
        subset = self.binding['releaseSubset']
        subset['releasedPageKeys'].append(subset['releasedPageKeys'][0])
        with self.assertRaises(ValueError):whole.reviewed_release_binding(SITE)
        subset['releasedPageKeys'].pop();subset['reviewEvidenceUrl']=None
        with self.assertRaises(ValueError):whole.reviewed_release_binding(SITE)

    def test_original_denominator_mutation_rejected(self):
        self.binding['releaseSubset']['officialUnitCount']=35
        with self.assertRaisesRegex(ValueError,'original membership'):
            whole.reviewed_release_binding(SITE)

    def test_batch_subset_hash_required(self):
        self.batch.pop('releaseSubsetSha256')
        with self.assertRaises(ValueError):barrier.check(self.batch,self.evidence,self.git)

    def test_registry_subset_hash_required(self):
        target=json.loads(self.git.read(old.BASE,'.github/site-factory-sites.json'))['sites'][SITE]
        target.pop('initialReleaseSubsetSha256')
        with self.assertRaisesRegex(ValueError,'subset binding'):
            whole.validate_reviewed_membership(SITE,target)

    def test_deferred_candidate_cannot_be_promoted(self):
        path=ROOT+'/src/data/region-coverage.json'
        doc=json.loads(self.git.read(old.BASE,path))
        next(row for row in doc['representatives'] if row['pageKey'].endswith('dong-36'))['status']='approved'
        self.git.documents[(old.BASE,path)]=old.encode(doc)
        with self.assertRaisesRegex(ValueError,'beyond candidate approval'):
            barrier.check(self.batch,self.evidence,self.git)

    def test_missing_deferred404_or_alias_hash_fails(self):
        self.evidence['qa']['notFoundRoutes']=[row for row in self.evidence['qa']['notFoundRoutes'] if row['url']!='/regions/dong-36/']
        with self.assertRaisesRegex(ValueError,'404 QA'):
            barrier.check(self.batch,self.evidence,self.git)

    def test_preview_accepts35_not37_and_preserves_denominator(self):
        site,production,documents=reviewed.production_fixture(self.batch,self.evidence,self.git,SITE)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for (revision,path),raw in self.git.documents.items():
                if revision==old.FINAL and path.startswith(ROOT+'/'):
                    p=root/path[len(ROOT)+1:];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            result=whole.validate_preview_source(site,SITE,old.FINAL,root,git=self.git)
            self.assertEqual((result['details'],result['officialUnits']),(35,37))
            doc=json.loads((root/'src/data/publish-manifest.json').read_text());doc['pages'].pop()
            (root/'src/data/publish-manifest.json').write_bytes(old.encode(doc))
            site['initialPreviewManifestSha256']=hashlib.sha256(old.encode(doc)).hexdigest()
            with self.assertRaisesRegex(ValueError,'release membership'):
                whole.validate_preview_source(site,SITE,old.FINAL,root,git=self.git)

    def test_preview_rejects_final_and_local_geographic_visual_drift(self):
        site,_,_=reviewed.production_fixture(self.batch,self.evidence,self.git,SITE)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for (revision,path),raw in self.git.documents.items():
                if revision==old.FINAL and path.startswith(ROOT+'/'):
                    p=root/path[len(ROOT)+1:];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            for name in ('region-coverage.json','region-policy.json'):
                path=ROOT+'/src/data/'+name;original=self.git.documents[(old.FINAL,path)]
                changed=json.loads(original)
                if name=='region-coverage.json': changed['administrativeCrosswalk'][0]['name']='Changed alias'
                else: changed['visualBindings'][0]['image']='/images/nonexistent.png'
                for where in ('committed','local'):
                    with self.subTest(file=name,where=where):
                        if where=='committed': self.git.documents[(old.FINAL,path)]=old.encode(changed)
                        else: (root/'src/data'/name).write_bytes(old.encode(changed))
                        with self.assertRaisesRegex(ValueError,'dependency bytes changed'):
                            whole.validate_preview_source(site,SITE,old.FINAL,root,git=self.git)
                        self.git.documents[(old.FINAL,path)]=original
                        (root/'src/data'/name).write_bytes(original)

    def test_production_transition_keeps_existing_gates(self):
        site,production,documents=reviewed.production_fixture(self.batch,self.evidence,self.git,SITE)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'target';control=Path(d)/'control'
            for path,raw in documents.items():
                p=control/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            for (revision,path),raw in self.git.documents.items():
                if revision==production and path.startswith(ROOT+'/'):
                    p=root/path[len(ROOT)+1:];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            source_git=self.git
            class FixtureGit:
                def __new__(cls,workspace):return source_git
            with patch.object(barrier,'GitEvidence',FixtureGit):
                self.assertEqual(whole.verify_release(site,production,root,control,Path(d))['pipelineState'],'initial_source_validated')
            site['productionEnabled']=False
            with self.assertRaisesRegex(ValueError,'Gate is closed'):
                whole.resolve(site,site['repo'],production,site['initialDeployment']['launchKey'],site['initialDeployment']['scopeKey'])

    def test_no_new_public_binding_is_enabled(self):
        self.context.stop()
        self.assertEqual(whole.ADDITIONAL_REVIEWED_RELEASES,{})
        self.assertFalse(whole.is_reviewed_initial_site(SITE))

    def test_http_links_cannot_target_deferred_routes(self):
        routes={'/','/regions/','/regions/dong-1/'}
        verify_initial.validate_release_links('<a href="/regions/dong-1/">ok</a><a href="https://fwith.co.kr/">shop</a>', 'https://pyeongtaek.fwith.kr','/',routes)
        for href in ['/regions/dong-36/','https://pyeongtaek.fwith.kr/regions/dong-37/','../dong-36/',
                     'https://PYEONGTAEK.FWITH.KR/regions/dong-36/','https://pyeongtaek.fwith.kr:443/regions/dong-37/',
                     '//PYEONGTAEK.FWITH.KR/regions/dong-36/','http://pyeongtaek.fwith.kr/regions/dong-37/']:
            with self.subTest(href=href),self.assertRaisesRegex(ValueError,'absent release route'):
                verify_initial.validate_release_links('<a href="'+href+'">bad</a>','https://pyeongtaek.fwith.kr','/regions/dong-1/',routes)


if __name__=='__main__': unittest.main()
