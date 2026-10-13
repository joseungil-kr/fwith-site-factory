"""Portable offline regressions for the control/target release workflow.

DIRECT_SOURCE_ROOT names the separate target checkout. These tests do not assume
an unbound or locked publisher. Preparation-only checks are kept outside this
controller; no provider or website is contacted by these regressions.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

CONTROL_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = Path(os.environ['DIRECT_SOURCE_ROOT']).resolve()
WORKFLOW = Path(os.environ.get('DIRECT_WORKFLOW_PATH', CONTROL_ROOT / '.github/workflows/seoul-gwanak-direct-publish.yml'))
spec = importlib.util.spec_from_file_location('gwanak_fixed_publisher', Path(__file__).with_name('publish.py'))
pub = importlib.util.module_from_spec(spec); spec.loader.exec_module(pub)
CONTRACT = json.loads(Path(pub.__file__).with_name('source-contract.json').read_text())
REVISION = 'f' * 40  # Explicit synthetic bound revision, never a claimed commit.
ORIGIN = 'https://seoul-gwanak.fwith.kr'
GENERATED = 'src/data/build-revision.json'
OBSERVATIONS = []


def writer_bytes(revision=REVISION):
    return json.dumps({'revision': revision}, indent=2).encode()


class SourcePhaseTests(unittest.TestCase):
    def test_actual_prebuild_snapshot_includes_every_tracked_file(self):
        self.assertIn(GENERATED, CONTRACT['files'])
        result = pub.verify_source_bytes(SOURCE_ROOT, CONTRACT, phase='prebuild')
        self.assertEqual(result['files'], len(CONTRACT['files']))
        self.assertIsNone(result['generatedRevisionException'])

    def test_source_phase_must_be_explicit(self):
        with self.assertRaises(TypeError): pub.verify_source_bytes(SOURCE_ROOT, CONTRACT)
        with self.assertRaisesRegex(ValueError, 'source_phase_required'):
            pub.verify_source_bytes(SOURCE_ROOT, CONTRACT, phase='unknown')
        with self.assertRaisesRegex(ValueError, 'postbuild_bound_revision_required'):
            pub.verify_source_bytes(SOURCE_ROOT, CONTRACT, phase='postbuild')

    def test_full_postbuild_snapshot_permits_only_exact_writer_bytes(self):
        with tempfile.TemporaryDirectory(prefix='gwanak-phase-') as tmp:
            target = Path(tmp) / 'source'; shutil.copytree(SOURCE_ROOT, target, ignore=shutil.ignore_patterns('dist', '__pycache__'))
            (target / GENERATED).write_bytes(writer_bytes())
            result = pub.verify_source_bytes(target, CONTRACT, phase='postbuild', bound_revision=REVISION)
            self.assertEqual(result['generatedRevisionException'], GENERATED)
            with self.assertRaisesRegex(ValueError, 'source_file_digest_mismatch'):
                pub.verify_source_bytes(target, CONTRACT, phase='prebuild')

    def test_five_generated_revision_negatives_in_each_phase(self):
        for phase in ['prebuild', 'postbuild']:
            with tempfile.TemporaryDirectory(prefix='gwanak-five-negative-') as tmp:
                target = Path(tmp) / 'source'; shutil.copytree(SOURCE_ROOT, target, ignore=shutil.ignore_patterns('dist', '__pycache__'))
                path = target / GENERATED
                expected = path.read_bytes() if phase == 'prebuild' else writer_bytes()
                alias = Path(tmp) / 'alias.json'; alias.write_bytes(expected)
                for case in ['wrong_revision', 'not_json', 'extra_content', 'missing_generated_revision', 'symlink_generated_revision']:
                    with self.subTest(phase=phase, case=case):
                        if path.exists() or path.is_symlink(): path.unlink()
                        if case == 'wrong_revision': path.write_bytes(writer_bytes('0' * 40))
                        elif case == 'not_json': path.write_bytes(b'not JSON')
                        elif case == 'extra_content': path.write_bytes(expected + b'\nextra content')
                        elif case == 'symlink_generated_revision': path.symlink_to(alias)
                        error = None
                        try: pub.verify_source_bytes(target, CONTRACT, phase=phase, bound_revision=REVISION)
                        except ValueError as caught: error = str(caught)
                        self.assertIsNotNone(error, 'Generated revision mutation was accepted')
                        OBSERVATIONS.append(dict(phase=phase, case=case, rejected=True, error=error))

    def test_other_source_bytes_remain_pinned_after_build(self):
        with tempfile.TemporaryDirectory(prefix='gwanak-other-source-') as tmp:
            target = Path(tmp) / 'source'; shutil.copytree(SOURCE_ROOT, target, ignore=shutil.ignore_patterns('dist', '__pycache__'))
            (target / GENERATED).write_bytes(writer_bytes())
            changed = target / 'scripts/assert_preview_boundary.mjs'; changed.write_text(changed.read_text() + '\n// synthetic mutation')
            with self.assertRaisesRegex(ValueError, 'source_file_digest_mismatch'):
                pub.verify_source_bytes(target, CONTRACT, phase='postbuild', bound_revision=REVISION)

    def test_untracked_executable_and_package_configuration_rejected(self):
        with tempfile.TemporaryDirectory(prefix='gwanak-untracked-') as tmp:
            target = Path(tmp) / 'source'; shutil.copytree(SOURCE_ROOT, target, ignore=shutil.ignore_patterns('dist', '__pycache__'))
            for rel in ['src/unreviewed.js', '.npmrc']:
                path = target / rel; path.write_text('synthetic-only')
                with self.assertRaisesRegex(ValueError, 'unreviewed_source_file|unreviewed_source_root_entry'):
                    pub.verify_source_bytes(target, CONTRACT, phase='prebuild')
                path.unlink()
    def test_parent_directory_symlinks_rejected_in_both_phases(self):
        for phase in ['prebuild', 'postbuild']:
            with self.subTest(phase=phase), tempfile.TemporaryDirectory(prefix='gwanak-parent-link-') as tmp:
                target=Path(tmp)/'source';shutil.copytree(SOURCE_ROOT,target,ignore=shutil.ignore_patterns('dist','__pycache__'))
                if phase=='postbuild':(target/GENERATED).write_bytes(writer_bytes())
                actual=Path(tmp)/'actual-data';(target/'src/data').rename(actual);(target/'src/data').symlink_to(actual,target_is_directory=True)
                with self.assertRaisesRegex(ValueError,'source_parent_symlink'):
                    pub.verify_source_bytes(target,CONTRACT,phase=phase,bound_revision=REVISION)
                OBSERVATIONS.append(dict(phase=phase,case='parent_directory_symlink',rejected=True))

    def test_source_parent_symlink_rejected_in_both_phases(self):
        for phase in ['prebuild', 'postbuild']:
            with self.subTest(phase=phase), tempfile.TemporaryDirectory(prefix='gwanak-source-parent-link-') as tmp:
                root=Path(tmp);actual=root/'actual-site-factory';target=actual/'seoul-gwanak-flower'
                shutil.copytree(SOURCE_ROOT,target,ignore=shutil.ignore_patterns('dist','__pycache__'))
                if phase=='postbuild':(target/GENERATED).write_bytes(writer_bytes())
                alias=root/'site-factory';alias.symlink_to(actual,target_is_directory=True)
                with self.assertRaisesRegex(ValueError,'source_parent_symlink'):
                    pub.verify_source_bytes(alias/'seoul-gwanak-flower',CONTRACT,phase=phase,bound_revision=REVISION)
                OBSERVATIONS.append(dict(phase=phase,case='source_parent_directory_symlink',rejected=True))

    def test_untracked_unsafe_tree_entries_rejected_in_both_phases(self):
        for phase in ['prebuild', 'postbuild']:
            for case in ['directory_symlink', 'dangling_symlink', 'fifo']:
                with self.subTest(phase=phase,case=case), tempfile.TemporaryDirectory(prefix='gwanak-unsafe-tree-') as tmp:
                    root=Path(tmp);target=root/'source';shutil.copytree(SOURCE_ROOT,target,ignore=shutil.ignore_patterns('dist','__pycache__'))
                    if phase=='postbuild':(target/GENERATED).write_bytes(writer_bytes())
                    extra=target/'public/unreviewed-entry'
                    if case=='directory_symlink':
                        actual=root/'unreviewed-directory';actual.mkdir();(actual/'payload.js').write_text('SYNTHETIC_ONLY');extra.symlink_to(actual,target_is_directory=True)
                    elif case=='dangling_symlink':extra.symlink_to(root/'nonexistent')
                    else:os.mkfifo(extra)
                    with self.assertRaisesRegex(ValueError,'source_tree_symlink|source_special_entry'):
                        pub.verify_source_bytes(target,CONTRACT,phase=phase,bound_revision=REVISION)
                    OBSERVATIONS.append(dict(phase=phase,case=case,rejected=True))

    def test_all_python_cache_entries_rejected_in_both_phases(self):
        for phase in ['prebuild', 'postbuild']:
            for rel in ['scripts/__pycache__/unreviewed.cpython-312.pyc', 'public/__pycache__/extra.html', 'scripts/__pycache__/extra.py', 'scripts/__pycache__/nested/qa_gwanak.cpython-312.pyc', 'scripts/__pycache__/qa_gwanak.cpython-312.pyc']:
                with self.subTest(phase=phase,rel=rel), tempfile.TemporaryDirectory(prefix='gwanak-cache-negative-') as tmp:
                    target=Path(tmp)/'source';shutil.copytree(SOURCE_ROOT,target,ignore=shutil.ignore_patterns('dist','__pycache__'))
                    if phase=='postbuild':(target/GENERATED).write_bytes(writer_bytes())
                    path=target/rel;path.parent.mkdir(parents=True);path.write_bytes(b'INERT_TEST_BYTES_NO_EXECUTION')
                    with self.assertRaisesRegex(ValueError,'source_python_cache_forbidden'):
                        pub.verify_source_bytes(target,CONTRACT,phase=phase,bound_revision=REVISION)
                    OBSERVATIONS.append(dict(phase=phase,case='forbidden_cache:'+rel,rejected=True))

    def test_exact_serialization_and_file_mode_in_both_phases(self):
        for phase in ['prebuild', 'postbuild']:
            with tempfile.TemporaryDirectory(prefix='gwanak-serialization-') as tmp:
                target=Path(tmp)/'source';shutil.copytree(SOURCE_ROOT,target,ignore=shutil.ignore_patterns('dist','__pycache__'))
                path=target/GENERATED;expected=path.read_bytes() if phase=='prebuild' else writer_bytes()
                for case,bad in [('extra_newline',expected+b'\n'),('minified_json',json.dumps(json.loads(expected),separators=(',',':')).encode())]:
                    with self.subTest(phase=phase,case=case):
                        path.write_bytes(bad)
                        with self.assertRaises(ValueError):pub.verify_source_bytes(target,CONTRACT,phase=phase,bound_revision=REVISION)
                        OBSERVATIONS.append(dict(phase=phase,case=case,rejected=True))
                path.write_bytes(expected);path.chmod(0o755)
                with self.assertRaisesRegex(ValueError,'source_file_mode_mismatch'):
                    pub.verify_source_bytes(target,CONTRACT,phase=phase,bound_revision=REVISION)
                OBSERVATIONS.append(dict(phase=phase,case='changed_file_mode',rejected=True))


class PortableWorkflowTests(unittest.TestCase):
    def test_separate_source_path_and_control_paths_are_used(self):
        self.assertTrue(SOURCE_ROOT.is_dir())
        self.assertTrue(CONTROL_ROOT.is_dir())
        self.assertNotEqual(SOURCE_ROOT, CONTROL_ROOT / 'site-factory/seoul-gwanak-flower')
        source = Path(__file__).read_text()
        self.assertNotIn("ROOT/" + "'candidate'", source)
        self.assertNotIn('from synthetic_' + 'fixture import', source)

    def test_expected_revision_is_explicit_in_test_step_environment(self):
        self.assertRegex(os.environ.get('REVISION',''),r'^[0-9a-f]{40}$')
        workflow=WORKFLOW.read_text()
        for name in ['Verify fixed reviewed source bytes before running source code','Test fixed publisher safety contracts against exact separate target']:
            step=workflow.split('      - name: '+name+'\n',1)[1].split('      - ',1)[0]
            self.assertIn('          REVISION: ${{',step)
            self.assertIn('inputs.expected_revision',step)

    def test_build_order_and_explicit_phases(self):
        workflow = WORKFLOW.read_text()
        self.assertIn('DIRECT_SOURCE_ROOT: ${{ github.workspace }}/target/site-factory/seoul-gwanak-flower', workflow)
        self.assertIn("  PYTHONDONTWRITEBYTECODE: '1'",workflow.split('jobs:',1)[0])
        self.assertEqual(os.environ.get('PYTHONDONTWRITEBYTECODE'),'1')
        self.assertIn('publish.py source --phase prebuild', workflow)
        self.assertIn('publish.py package --phase postbuild', workflow)
        self.assertLess(workflow.index('publish.py source --phase prebuild'), workflow.index('          npm ci'))
        self.assertLess(workflow.index('          npm ci'), workflow.index('          npm run build'))
        self.assertLess(workflow.index('          npm run build'), workflow.index('          npm test'))
        self.assertIn('SITE_URL: ${{ steps.binding.outputs.origin }}', workflow)
        self.assertIn('      build_only:',workflow)
        for job in ['publish', 'finalize_indexnow']:
            self.assertIn('  '+job+':\n    if: ${{ false }} # Build-only activation: public job disabled', workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("GITHUB_RUN_ATTEMPT !== '1'", workflow)
        build, _ = workflow.split('  publish:\n', 1)
        self.assertNotIn('secrets.', build)
        self.assertNotIn('  push:', workflow.split('permissions:', 1)[0])

    def test_indexnow_finalize_has_no_provider_credentials(self):
        finalize = WORKFLOW.read_text().split('  finalize_indexnow:\n', 1)[1]
        for forbidden in ['secrets.', 'wrangler@', 'CLOUDFLARE', 'publish.py attach']:
            self.assertNotIn(forbidden, finalize)

    def test_source_and_package_cli_implement_distinct_phases(self):
        source = Path(pub.__file__).read_text()
        self.assertIn("{'source': 'prebuild', 'package': 'postbuild'}", source)
        self.assertIn("source_contract(source, phase='postbuild')", source)
        self.assertIn('source_contract(args.source, phase=args.phase)', source)


class FixedContractTests(unittest.TestCase):
    def test_exact_route_counts_and_robots(self):
        self.assertEqual(len(pub.ARTICLE_ROUTES), 2)
        self.assertEqual(len(pub.ROUTES), 4)
        self.assertEqual(len(pub.SITEMAP_ROUTES), 3)
        self.assertEqual(pub.THIN_HUB_ROUTES, {'/regions/'})
        self.assertEqual(pub.expected_robots('/regions/'), {'noindex', 'follow'})
        self.assertEqual(pub.expected_robots('/404.html'), {'noindex', 'nofollow', 'noarchive'})

    def test_anchors_ctas_no_overrides_and_journal(self):
        self.assertEqual(pub.EXPECTED_ANCHORS['/regions/gwanak-celebration-wreath/'], ['snu-faculty', 'snu-research-park', 'nakseongdae-traditional', 'opening-occasion'])
        source = Path(pub.__file__).read_text()
        self.assertIn("'tel:1844-0644' in p.links", source)
        self.assertIn("'https://fwith.co.kr/' in p.links", source)
        self.assertIn('override_scope=False, override_existing_origin=False, override_existing_dns_record=False', source)
        self.assertEqual(pub.RECEIPT_ISSUE, 266)

    def test_missing_host_approval_rejected_in_pure_binding_fixture(self):
        binding = dict(schemaVersion=1, state='approved', repository=pub.REPOSITORY, branch=pub.BRANCH,
                       sourceRoot=pub.SOURCE_ROOT, configuredWorkerTarget=pub.WORKER,
                       providerExistenceVerified=False, hostname='seoul-gwanak.fwith.kr', origin=ORIGIN,
                       sourceRevision=REVISION, sourceContractSha256='0' * 64,
                       approvals=dict(publication=True, hostBinding=False, indexNowProof=True),
                       evidenceReferences={key:'SYNTHETIC_TEST_ONLY' for key in ['publication','hostBinding','indexNowProof']})
        with tempfile.TemporaryDirectory(prefix='gwanak-binding-') as tmp:
            root=Path(tmp);(root/'publication-binding.json').write_text(json.dumps(binding))
            with patch.object(pub,'__file__',str(root/'publish.py')),patch.object(pub,'LOCAL_PREPARATION_ONLY',False),patch.dict(os.environ,{'REVISION':REVISION}):
                with self.assertRaisesRegex(ValueError,'release_binding_approval_missing'):pub.bind_exact_release()

    def test_exact_bound_source_contract_both_phases_in_isolated_fixture(self):
        with tempfile.TemporaryDirectory(prefix='gwanak-bound-source-') as tmp:
            root=Path(tmp);target=root/'target';shutil.copytree(SOURCE_ROOT,target,ignore=shutil.ignore_patterns('dist','__pycache__'))
            control=root/'control';control.mkdir();(control/'source-contract.json').write_text(json.dumps(CONTRACT))
            with patch.object(pub,'__file__',str(control/'publish.py')),patch.object(pub,'ORIGIN',ORIGIN),patch.object(pub,'bind_exact_release',return_value={'sourceRevision':REVISION,'syntheticOnly':True}):
                result=pub.source_contract(target,phase='prebuild')
                self.assertEqual(result['files'],len(CONTRACT['files']))
                (target/GENERATED).write_bytes(writer_bytes())
                self.assertEqual(pub.source_contract(target,phase='postbuild')['files'],len(CONTRACT['files']))


class ReviewedOutputGateTests(unittest.TestCase):
    def test_unreviewed_build_output_blocks_publication(self):
        with patch.object(pub,'bind_exact_release',return_value={'sourceRevision':REVISION,'reviewedBuildOutput':{'approved':False}}):
            with self.assertRaisesRegex(ValueError,'independent_build_output_review_required'):pub.require_reviewed_output()

    def test_wrong_source_and_missing_review_evidence_block(self):
        reviewed=dict(approved=True,sourceRevision='0'*40,distManifestSha256='a'*64,artifactId=1,buildRunUrl='https://github.com/'+pub.REPOSITORY+'/actions/runs/1',independentReviewEvidence='SYNTHETIC_ONLY')
        binding={'sourceRevision':REVISION,'reviewedBuildOutput':reviewed}
        with patch.object(pub,'bind_exact_release',return_value=binding):
            with self.assertRaisesRegex(ValueError,'reviewed_output_source_mismatch'):pub.require_reviewed_output()
            reviewed['sourceRevision']=REVISION;reviewed['independentReviewEvidence']=None
            with self.assertRaisesRegex(ValueError,'reviewed_output_evidence_missing'):pub.require_reviewed_output()

    def test_bound_source_without_review_cannot_reach_provider_transport(self):
        binding={'sourceRevision':REVISION,'reviewedBuildOutput':{'approved':False}}
        with patch.object(pub,'LOCAL_PREPARATION_ONLY',False),patch.object(pub,'bind_exact_release',return_value=binding),patch.object(pub,'build_opener',side_effect=AssertionError('NETWORK MUST NOT RUN')):
            for action in [pub.provider_transport,pub.indexnow]:
                with self.assertRaisesRegex(ValueError,'independent_build_output_review_required'):action()

    def test_exact_inventory_pin_then_any_output_change_rejects(self):
        with tempfile.TemporaryDirectory(prefix='gwanak-reviewed-output-') as tmp:
            old=Path.cwd();os.chdir(tmp)
            try:
                root=Path('release/dist');root.mkdir(parents=True)
                for rel in ['index.html','regions/index.html','404.html','_headers','robots.txt','sitemap-index.xml']:
                    path=root/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('SYNTHETIC_ONLY '+rel)
                digest=pub.sha(json.dumps(pub.inventory(root),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
                reviewed=dict(approved=True,sourceRevision=REVISION,distManifestSha256=digest,artifactId=1,buildRunUrl='https://github.com/'+pub.REPOSITORY+'/actions/runs/1',independentReviewEvidence='SYNTHETIC_ONLY_NOT_ACTUAL_REVIEW')
                with patch.object(pub,'bind_exact_release',return_value={'sourceRevision':REVISION,'reviewedBuildOutput':reviewed}):
                    self.assertEqual(pub.require_reviewed_output()['distManifestSha256'],digest)
                    (root/'index.html').write_text('changed synthetic output')
                    with self.assertRaisesRegex(ValueError,'rebuilt_output_differs_from_reviewed_artifact'):pub.require_reviewed_output()
            finally:os.chdir(old)


if __name__ == '__main__':
    result = unittest.main(verbosity=2, exit=False)
    if os.environ.get('PUBLISH_TEST_REPORT'):
        Path(os.environ['PUBLISH_TEST_REPORT']).write_text(json.dumps({'scope':'OFFLINE SYNTHETIC CONTRACT REGRESSIONS ONLY','testsRun':result.result.testsRun,'successful':result.result.wasSuccessful(),'generatedRevisionMutations':OBSERVATIONS,'controlRoot':str(CONTROL_ROOT),'sourceRoot':str(SOURCE_ROOT)},indent=2)+'\n')
    raise SystemExit(0 if result.result.wasSuccessful() else 1)
