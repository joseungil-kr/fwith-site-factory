"""Offline positive/negative contracts. Fixtures are not real remote/build evidence."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('two_banner_update', Path(__file__).with_name('update.py'))
u = importlib.util.module_from_spec(spec); spec.loader.exec_module(u)
REGION = 'seoul-geumcheon'
REV = 'e' * 40
ACCOUNT = '1' * 32

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')

def fixture(root):
    shutil.copytree(ROOT / u.DIRECTORY, root / u.DIRECTORY)
    deps = json.loads((root / u.DIRECTORY / 'shared-dependencies.json').read_text())['files']
    for rel in [*deps, *[f'scripts/direct-{r}/{f}' for r in u.REGIONS for f in ['publish.py', 'source-contract.json']]]:
        p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ROOT / rel, p)
    values = u.catalog(root)
    for region, plan in u.plans(root).items():
        target = values[region]; revision = REV if region == REGION else 'f' * 40
        rb = {'fixtureOnly': True, 'sourceCommit': revision, 'parentCommit': plan['parentCommit'], 'allFilesMatch': True,
              'sourceTree': plan['expectedTrees']['afterSource'], 'rootTree': plan['expectedTrees']['afterRepositoryRoot'],
              'remoteFiles': [dict(path=p['path'], mode=p['mode'], sha256=p['sha256'], gitBlob=p['gitBlobSha'], remoteBytesMatch=True, evidenceBasis=('fresh immutable fetch_file original bytes and full remote tree identity' if p['path'] in {c['path'] for c in plan['changedFiles']} else 'historical original bytes plus unchanged remote Git blob identity; exact full-tree reconstruction')) for p in plan['files']],
              'changedPaths': [p['path'] for p in plan['changedFiles']]}
        relative = u.DIRECTORY + '/' + region + '-test-only-readback.json'; save(root / relative, rb)
        target.update(status='independently_reviewed_source', revision=revision, releaseReview=None, releaseReviewSha256=None, sourceReadback=relative,
                      sourceReadbackSha256=u.sha((root / relative).read_bytes()))
    save(root / u.DIRECTORY / 'targets.json', dict(version=u.VERSION, targets=values))

def publish_review(root, target, output='a' * 64):
    proofs = []
    for kind in ['all-route-output', 'mobile-pixels', 'desktop-pixels']:
        relative = u.DIRECTORY + '/fixture-' + kind + '.txt'
        (root / relative).write_text('TEST ONLY synthetic proof for ' + kind)
        proofs.append(dict(kind=kind, path=relative, sha256=u.sha((root / relative).read_bytes())))
    review = dict(fixtureOnly=True, verdict='PASS_PUBLIC_UPDATE', sourceCommit=target['revision'],
                  previousRevision=target['previousRevision'], sourcePlanSha256=u.PLAN_SHA256,
                  allRouteOutputVerified=True, nativeTestsPassed=True, mobileAndDesktopPixelsVerified=True,
                  buildRunId='1', artifactId='2', outputFilesSha256=output, evidence=proofs)
    relative = u.DIRECTORY + '/fixture-release-review.json'; save(root / relative, review)
    target.update(releaseReview=relative, releaseReviewSha256=u.sha((root / relative).read_bytes()))
    values = u.catalog(root); values[REGION] = target
    save(root / u.DIRECTORY / 'targets.json', dict(version=u.VERSION, targets=values))
    return review

class Controls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'control'; self.root.mkdir(); fixture(self.root)
        self.environment = patch.dict(os.environ, dict(REVISION=REV, GITHUB_REPOSITORY='joseungil-kr/fwith-site-factory',
            GITHUB_RUN_ATTEMPT='1', EXISTING_UPDATE='true'), clear=False)
        self.environment.start(); self.addCleanup(self.environment.stop)
    def edit_target(self, **values):
        targets = u.catalog(self.root); targets[REGION].update(values)
        save(self.root/u.DIRECTORY/'targets.json', dict(version=u.VERSION, targets=targets))
    def test_exact_two_regions_and_complete_plans(self):
        p = u.plans(self.root)
        self.assertEqual({r:len(v['files']) for r,v in p.items()}, {'seoul-geumcheon':213,'seoul-yeongdeungpo':319})
        self.assertEqual({r:len(v['changedFiles']) for r,v in p.items()}, {'seoul-geumcheon':14,'seoul-yeongdeungpo':16})
        for row in p.values():
            self.assertEqual(set(row['customerChangedPaths']),u.CUSTOMER_PATHS)
            self.assertNotIn('src/data/build-revision.json',{x['path'] for x in row['files']})
    def test_build_accepts_saved_source_without_release_review(self):
        target,pub = u.load(self.root,REGION)
        self.assertIsNone(target['releaseReview'])
        self.assertTrue(u.authorize(self.root,REGION,for_public=False)['existingUpdate'])
    def test_public_null_release_review_fails_before_provider(self):
        with self.assertRaisesRegex(ValueError,'two_independent_actual_release_review_required'):
            u.authorize(self.root,REGION)
    def test_unknown_region_rejected(self):
        for region in ['seoul-guro','seoul-gangseo','seoul-dongjak','seoul-gwanak','other']:
            with self.assertRaisesRegex(ValueError,'unknown_two_update_target'):u.load(self.root,region)
    def test_null_and_placeholder_sha_failclosed(self):
        for revision in [None,'PENDING', '0'*39, 'A'*40]:
            self.edit_target(revision=revision)
            with self.assertRaisesRegex(ValueError,'two_saved_successor_revision_required'):u.load(self.root,REGION)
    def test_old_revision_cannot_be_update_successor(self):
        old=u.plans(self.root)[REGION]['parentCommit'];self.edit_target(revision=old)
        with patch.dict(os.environ,{'REVISION':old}), self.assertRaisesRegex(ValueError,'two_saved_successor_revision_required'):u.load(self.root,REGION)
    def test_new_revision_requires_update_mode_even_for_build(self):
        with patch.dict(os.environ,{'EXISTING_UPDATE':'false'}),self.assertRaisesRegex(ValueError,'two_successor_requires_existing_update'):
            u.authorize(self.root,REGION,for_public=False)
    def test_unknown_revision_cannot_fall_back_initial(self):
        with patch.dict(os.environ,{'EXISTING_UPDATE':'false','REVISION':'b'*40}),self.assertRaisesRegex(ValueError,'two_successor_requires_existing_update'):
            u.authorize(self.root,REGION,for_public=False)
    def test_initial_mode_only_exact_old_baseline(self):
        old=u.plans(self.root)[REGION]['parentCommit']
        with patch.dict(os.environ,{'EXISTING_UPDATE':'false','REVISION':old}):
            self.assertFalse(u.authorize(self.root,REGION)['existingUpdate'])
    def test_wrong_parent_rejected(self):
        self.edit_target(previousRevision='a'*40)
        with self.assertRaisesRegex(ValueError,'two_parent_revision_mismatch'):u.load(self.root,REGION)
    def test_wrong_fixed_identity_rejected(self):
        self.edit_target(worker='different')
        with self.assertRaisesRegex(ValueError,'two_fixed_identity_mismatch'):u.load(self.root,REGION)
    def test_rerun_rejected(self):
        with patch.dict(os.environ,{'GITHUB_RUN_ATTEMPT':'2'}),self.assertRaisesRegex(ValueError,'update_rerun_forbidden'):u.load(self.root,REGION)
    def test_wrong_repository_rejected(self):
        with patch.dict(os.environ,{'GITHUB_REPOSITORY':'other/repo'}),self.assertRaisesRegex(ValueError,'repository_mismatch'):u.load(self.root,REGION)
    def test_readback_all_files_digest_must_match(self):
        target=u.catalog(self.root)[REGION];p=self.root/target['sourceReadback'];r=json.loads(p.read_text());r['remoteFiles'][0]['sha256']='a'*64;save(p,r)
        self.edit_target(sourceReadbackSha256=u.sha(p.read_bytes()))
        with self.assertRaisesRegex(ValueError,'two_remote_whole_source_mismatch'):u.load(self.root,REGION)
    def test_readback_missing_file_rejected(self):
        target=u.catalog(self.root)[REGION];p=self.root/target['sourceReadback'];r=json.loads(p.read_text());r['remoteFiles'].pop();save(p,r)
        self.edit_target(sourceReadbackSha256=u.sha(p.read_bytes()))
        with self.assertRaisesRegex(ValueError,'two_remote_whole_source_mismatch'):u.load(self.root,REGION)
    def test_readback_root_tree_must_match(self):
        target=u.catalog(self.root)[REGION];p=self.root/target['sourceReadback'];r=json.loads(p.read_text());r['rootTree']='a'*40;save(p,r)
        self.edit_target(sourceReadbackSha256=u.sha(p.read_bytes()))
        with self.assertRaisesRegex(ValueError,'two_remote_readback_identity_mismatch'):u.load(self.root,REGION)
    def test_readback_changed_paths_cannot_expand(self):
        target=u.catalog(self.root)[REGION];p=self.root/target['sourceReadback'];r=json.loads(p.read_text());r['changedPaths'].append('src/data/products.json');save(p,r)
        self.edit_target(sourceReadbackSha256=u.sha(p.read_bytes()))
        with self.assertRaisesRegex(ValueError,'two_remote_delta_mismatch'):u.load(self.root,REGION)
    def test_evidence_rejects_symlink(self):
        target=u.catalog(self.root)[REGION];p=self.root/target['sourceReadback'];other=p.with_suffix('.orig');p.rename(other);p.symlink_to(other)
        with self.assertRaisesRegex(ValueError,'two_evidence_missing_or_symlink'):u.load(self.root,REGION)
    def test_source_contract_cannot_weaken(self):
        p=self.root/f'scripts/direct-{REGION}/source-contract.json';p.write_text('{}')
        with self.assertRaisesRegex(ValueError,'two_evidence_digest_mismatch'):u.load(self.root,REGION)
    def test_shared_helper_exact_bytes_dependency(self):
        p=self.root/'scripts/shared-banners/verify_update.py';p.write_text(p.read_text()+'\n# changed\n')
        with self.assertRaisesRegex(ValueError,'two_evidence_digest_mismatch'):u.load(self.root,REGION)
    def test_release_review_needs_pixels_and_exact_build(self):
        target,_=u.load(self.root,REGION);review=publish_review(self.root,target)
        self.assertEqual(u.release_review(self.root,target)['artifactId'],'2')
        for key,value in [('mobileAndDesktopPixelsVerified',False),('allRouteOutputVerified',False),('nativeTestsPassed',False),('outputFilesSha256','pending'),('sourceCommit','a'*40),('sourcePlanSha256','a'*64)]:
            bad={**review,key:value};p=self.root/target['releaseReview'];save(p,bad);target['releaseReviewSha256']=u.sha(p.read_bytes())
            with self.assertRaises(ValueError):u.release_review(self.root,target)
    def test_rebuilt_output_digest_mismatch_blocks_before_qa(self):
        target,pub=u.load(self.root,REGION);publish_review(self.root,target,output='a'*64)
        old=Path.cwd();work=Path(self.temp.name)/'work';work.mkdir();os.chdir(work);self.addCleanup(os.chdir,old)
        save(Path('release/release.json'),dict(revision=REV,worker=pub.WORKER,origin=pub.ORIGIN,files={'x':'b'*64}))
        with patch.object(pub,'inventory',return_value={'x':'b'*64}),self.assertRaisesRegex(ValueError,'two_rebuilt_output_differs_from_reviewed_build'):
            u.artifact(self.root,target,pub,for_public=True)

class DirectProductionBinding(Controls):
    def binding(self, target, pub, files):
        path=Path(pub.__file__).with_name('production-output-contract.json')
        value=dict(sourceRevision=target['revision'],files=files,
            state='independently_reviewed_actual_production_artifact',origin=pub.ORIGIN)
        save(path,value)
        return path,value
    def test_binding_independent_of_missing_or_false_environment(self):
        target,pub=u.load(self.root,REGION);files={'index.html':'a'*64};self.binding(target,pub,files)
        for value in [None,'false','true']:
            with self.subTest(value=value),patch.dict(os.environ,{},clear=False):
                if value is None:os.environ.pop('REQUIRE_REVIEWED_PRODUCTION',None)
                else:os.environ['REQUIRE_REVIEWED_PRODUCTION']=value
                self.assertTrue(u.reviewed_production_binding(pub,target,files))
    def test_binding_missing_rejects(self):
        target,pub=u.load(self.root,REGION)
        with self.assertRaisesRegex(ValueError,'independent_production_review_required'):
            u.reviewed_production_binding(pub,target,{'index.html':'a'*64})
    def test_binding_each_original_publisher_field_rejects_drift(self):
        target,pub=u.load(self.root,REGION);files={'index.html':'a'*64};path,value=self.binding(target,pub,files)
        for key,bad in [('sourceRevision','b'*40),('files',{}),('state','synthetic'),('origin','https://wrong.invalid')]:
            with self.subTest(key=key):
                save(path,{**value,key:bad})
                with self.assertRaisesRegex(ValueError,'reviewed_production_output_mismatch'):u.reviewed_production_binding(pub,target,files)
    def test_binding_symlink_rejects(self):
        target,pub=u.load(self.root,REGION);files={'index.html':'a'*64};path,_=self.binding(target,pub,files)
        other=path.with_suffix('.original');path.rename(other);path.symlink_to(other)
        with self.assertRaisesRegex(ValueError,'independent_production_review_required'):u.reviewed_production_binding(pub,target,files)
    def test_public_artifact_requires_original_binding_before_native_qa(self):
        target,pub=u.load(self.root,REGION);files={'x':'b'*64};publish_review(self.root,target,u.sha(u.json_bytes(files)))
        old=Path.cwd();work=Path(self.temp.name)/'gate-work';work.mkdir();os.chdir(work);self.addCleanup(os.chdir,old)
        save(Path('release/release.json'),dict(revision=REV,worker=pub.WORKER,origin=pub.ORIGIN,files=files))
        with patch.object(pub,'inventory',return_value=files),patch.object(u,'module',side_effect=AssertionError('native QA must not run')):
            with self.assertRaisesRegex(ValueError,'independent_production_review_required'):u.artifact(self.root,target,pub,for_public=True)

class Workflows(unittest.TestCase):
    def test_both_publishers_and_production_gates_preserved(self):
        for region in sorted(u.REGIONS):
            raw=(ROOT/f'.github/workflows/{region}-direct-publish.yml').read_text()
            pub=(ROOT/f'scripts/direct-{region}/publish.py').read_text()
            self.assertIn("require(not matches and not exists, 'initial_target_must_be_absent')",pub)
            self.assertIn("if os.environ.get('REQUIRE_REVIEWED_PRODUCTION') == 'true':",pub)
            self.assertEqual(raw.count("REQUIRE_REVIEWED_PRODUCTION: 'true'"),2)
            build,public=raw.split('  publish:\n',1)
            self.assertNotIn('secrets.',build)
            self.assertIn('authorize-build',build);self.assertIn('build-artifact',build)
            self.assertLess(public.index('authorize-mutation'),public.index('CLOUDFLARE_API_TOKEN'))
            self.assertLess(public.index(' artifact --region'),public.index('CLOUDFLARE_API_TOKEN'))
            self.assertIn('WRANGLER_PACKAGE=wrangler@4.147.0',public)
            self.assertIn("steps.deploy.outcome == 'success' && !(inputs.existing_update",public)
            self.assertIn('provider-after',public)
            self.assertLess(public.index('public-assets'),public.index('publish.py indexnow --report'))
            self.assertIn("steps.banners.outcome == 'success' || steps.banners.outcome == 'skipped'",public)
            finalize=raw.split('  finalize_indexnow:\n',1)[1]
            self.assertNotIn('secrets.',finalize);self.assertNotIn('CLOUDFLARE',finalize)
            self.assertLess(finalize.index('public-assets'),finalize.index('publish.py indexnow --report'))
    def test_catalog_public_requires_exact_review_when_enabled(self):
        for region,target in u.catalog(ROOT).items():
            if target['releaseReview'] is None:
                self.assertIsNone(target['releaseReviewSha256'])
            else:
                with patch.dict(os.environ,dict(REVISION=target['revision'],GITHUB_REPOSITORY=target['repository'],GITHUB_RUN_ATTEMPT='1',EXISTING_UPDATE='true')):
                    checked,pub=u.load(ROOT,region,require_release=True)
                    review=u.release_review(ROOT,checked)
                    binding=json.loads(Path(pub.__file__).with_name('production-output-contract.json').read_text())
                    self.assertEqual(u.sha(u.json_bytes(binding['files'])),review['outputFilesSha256'])
                    self.assertTrue(u.reviewed_production_binding(pub,checked,binding['files']))

class ProviderReuse(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'control';self.root.mkdir();fixture(self.root)
        self.env=patch.dict(os.environ,dict(REVISION=REV,GITHUB_REPOSITORY='joseungil-kr/fwith-site-factory',GITHUB_RUN_ATTEMPT='1',EXISTING_UPDATE='true'));self.env.start();self.addCleanup(self.env.stop)
        self.target,self.pub=u.load(self.root,REGION);self.shared=u.shared(self.root)
        self.calls=[]
        self.state={'settings':{'bindings':[],'compatibility_date':'2026-10-09','compatibility_flags':[],'logpush':False,'placement':{},'tags':[],'tail_consumers':[],'usage_model':'standard'},
                    'subdomain':{'enabled':False,'previews_enabled':False},
                    'domains':[{'id':'domain-1','hostname':self.pub.HOSTNAME,'service':self.pub.WORKER,'zone_id':'zone-1','zone_name':'fwith.kr','environment':'production','enabled':True,'previews_enabled':False}],
                    'scripts':[{'id':self.pub.WORKER}]}
        def get(path):
            self.calls.append(path)
            if '/workers/scripts?' in path:return {'result':self.state['scripts']}
            if '/workers/domains?' in path:return {'result':self.state['domains']}
            if path.endswith('/settings'):return {'result':self.state['settings']}
            if path.endswith('/subdomain'):return {'result':self.state['subdomain']}
            return {'result':{'id':ACCOUNT}}
        self.get=get
        self.config=dict(name=self.pub.WORKER,compatibility_date='2026-10-09',workers_dev=False,assets=dict(directory='./dist/',not_found_handling='404-page',html_handling='auto-trailing-slash'))
    def get_state(self):
        with patch.object(self.shared,'provider_get',return_value=(ACCOUNT,self.get)):
            return self.shared.state_and_config(self.target,self.pub,self.config)
    def test_exact_state_retains_flags_and_omits_routes(self):
        state,config,digest=self.get_state()
        self.assertFalse(config['workers_dev']);self.assertFalse(config['preview_urls'])
        for key in ['routes','route','domains','main','bindings']:self.assertNotIn(key,config)
        self.assertEqual(state['domains'][0]['environment'],'production')
        self.assertTrue(all('/zones/' not in p for p in self.calls))
    def test_existing_binding_worker_required(self):
        self.state['scripts']=[]
        with self.assertRaisesRegex(ValueError,'existing_worker_missing_or_ambiguous'):self.get_state()
    def test_foreign_hostname_or_worker_rejected(self):
        self.state['domains'][0]['service']='other'
        with self.assertRaisesRegex(ValueError,'Fixed production binding absent or changed'):self.get_state()
    def test_second_domain_rejected(self):
        self.state['domains'].append({**self.state['domains'][0],'id':'domain-2','hostname':'extra.fwith.kr'})
        with self.assertRaisesRegex(ValueError,'existing_exact_binding_required'):self.get_state()
    def test_environment_change_rejected(self):
        self.state['domains'][0]['environment']='staging'
        with self.assertRaisesRegex(ValueError,'Unreviewed nonproduction'):self.get_state()
    def test_runtime_binding_rejected_without_serializing(self):
        self.state['settings']['bindings']=[{'name':'private','text':'DO_NOT_STORE'}]
        with self.assertRaisesRegex(ValueError,'Unexpected runtime bindings') as cm:self.get_state()
        self.assertNotIn('DO_NOT_STORE',str(cm.exception))
    def test_settings_change_rejected(self):
        self.state['settings']['compatibility_date']='2026-10-10'
        with self.assertRaisesRegex(ValueError,'Nondefault existing settings'):self.get_state()
    def test_exposure_change_rejected(self):
        self.state['subdomain']['enabled']=True
        with self.assertRaisesRegex(ValueError,'Would change workers.dev'):self.get_state()
    def test_missing_preview_flag_rejected(self):
        del self.state['subdomain']['previews_enabled']
        with self.assertRaisesRegex(ValueError,'Incomplete exposure baseline'):self.get_state()
    def test_preflight_exact_old_live_revision_then_after_unchanged(self):
        old=Path.cwd();work=Path(self.temp.name)/'work';work.mkdir();os.chdir(work);self.addCleanup(os.chdir,old)
        save(Path('release/wrangler.publish.json'),self.config)
        page=('<meta name="site-factory-revision" content="'+self.target['previousRevision']+'">').encode()
        with patch.object(self.shared,'provider_get',return_value=(ACCOUNT,self.get)),patch.object(self.pub,'get',return_value=(page,{})):
            before=self.shared.preflight(self.target,self.pub);save(Path('binding-before.json'),before)
            result=self.shared.provider_after(self.target,self.pub)
            self.assertEqual(result['state'],'provider_settings_and_exposure_unchanged')
            self.state['domains'][0]['id']='different'
            with self.assertRaisesRegex(ValueError,'provider_state_changed'):self.shared.provider_after(self.target,self.pub)
    def test_preflight_unknown_or_duplicate_revision_rejected(self):
        old=Path.cwd();work=Path(self.temp.name)/'work';work.mkdir();os.chdir(work);self.addCleanup(os.chdir,old)
        save(Path('release/wrangler.publish.json'),self.config)
        for page in [b'<html></html>',b'<meta name="site-factory-revision" content="wrong">',(('<meta name="site-factory-revision" content="'+self.target['previousRevision']+'">')*2).encode()]:
            with patch.object(self.shared,'provider_get',return_value=(ACCOUNT,self.get)),patch.object(self.pub,'get',return_value=(page,{})),self.assertRaisesRegex(ValueError,'previous_public_revision_mismatch'):
                self.shared.preflight(self.target,self.pub)
    def test_public_assets_mime_and_digest_checked(self):
        target={**self.target,'version':'phone-20261013'}
        with patch.object(self.pub,'get',return_value=(b'not_webp',{'Content-Type':'image/jpeg'})),self.assertRaisesRegex(ValueError,'shared_banner_mime_mismatch'):
            self.shared.public_assets(target,self.pub)
        with patch.object(self.pub,'get',return_value=(b'not_webp',{'Content-Type':'image/webp'})),self.assertRaisesRegex(ValueError,'shared_banner_live_digest_mismatch'):
            self.shared.public_assets(target,self.pub)


@unittest.skipUnless(os.environ.get('TWO_SOURCE_BASE'), 'Set TWO_SOURCE_BASE for exact local source fixture checks')
class WholeSource(unittest.TestCase):
    # The subprocess responses below are explicit test fixtures, not GitHub readbacks.
    def setUp(self):
        Controls.setUp(self)
        self.plan=u.plans(self.root)[REGION]
        self.checkout=Path(self.temp.name)/'checkout'
        self.source=self.checkout/self.plan['root']
        source=Path(os.environ['TWO_SOURCE_BASE'])/REGION/self.plan['root']
        shutil.copytree(source,self.source)
        self.git_results={
            ('rev-parse','HEAD'):REV+'\n',
            ('rev-list','--parents','-n','1','HEAD'):REV+' '+self.plan['parentCommit']+'\n',
            ('status','--porcelain','--untracked-files=all'):'',
            ('rev-parse','HEAD^{tree}'):self.plan['expectedTrees']['afterRepositoryRoot']+'\n',
            ('rev-parse','HEAD:'+self.plan['root']):self.plan['expectedTrees']['afterSource']+'\n',
            ('diff','--name-only','-z',self.plan['parentCommit'],REV,'--'):'\0'.join(self.plan['root']+'/'+p['path'] for p in self.plan['changedFiles'])+'\0',
        }
    def check_source(self):
        def fake_git(command,**kwargs):
            self.assertEqual(command[:3],['git','-C',str(self.checkout)])
            self.assertEqual(kwargs['env']['GIT_NO_LAZY_FETCH'],'1')
            return self.git_results[tuple(command[3:])].encode()
        with patch.object(u.subprocess,'check_output',side_effect=fake_git):
            return u.source(self.root,REGION,self.checkout)
    def test_exact_real_source_bytes_with_explicit_git_fixture(self):
        self.assertEqual(self.check_source()['files'],213)
    def test_merge_parent_rejected(self):
        self.git_results[('rev-list','--parents','-n','1','HEAD')]+=' '+'a'*40
        with self.assertRaisesRegex(ValueError,'two_single_exact_parent_required'):self.check_source()
    def test_wrong_whole_branch_tree_rejected(self):
        self.git_results[('rev-parse','HEAD^{tree}')]='a'*40
        with self.assertRaisesRegex(ValueError,'two_exact_source_and_branch_trees_required'):self.check_source()
    def test_dirty_checkout_rejected(self):
        self.git_results[('status','--porcelain','--untracked-files=all')]=' M unexpected.txt'
        with self.assertRaisesRegex(ValueError,'two_source_checkout_not_clean'):self.check_source()
    def test_extra_branch_change_rejected(self):
        key=('diff','--name-only','-z',self.plan['parentCommit'],REV,'--');self.git_results[key]+='README.md\0'
        with self.assertRaisesRegex(ValueError,'two_git_delta_scope_mismatch'):self.check_source()
    def test_unchanged_historical_byte_change_rejected(self):
        p=self.source/'src/data/products.json';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'two_source_bytes_mismatch'):self.check_source()
    def test_changed_mode_rejected(self):
        p=self.source/'src/data/products.json';p.chmod(0o755)
        with self.assertRaisesRegex(ValueError,'two_source_mode_mismatch'):self.check_source()
    def test_generated_revision_forbidden_before_build(self):
        (self.source/'src/data/build-revision.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'source_file_digest_mismatch'):self.check_source()

if __name__=='__main__':unittest.main()
