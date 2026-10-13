"""Offline regressions for Dongjak's one tracked generated revision file.
These are synthetic byte fixtures, never source edits or Git commit evidence.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy,hashlib,json,unittest
import adapter
from adapter import controls

class DongjakBindingTests(unittest.TestCase):
    def fixture(self):
        return next(copy.deepcopy(e)for e in adapter.frozen_entries() if e['path']==adapter.GENERATED_REVISION)
    def check_bytes(self,data,allow=True,head=None):
        with TemporaryDirectory() as t:
            root=Path(t);e=self.fixture();p=root/e['path'];p.parent.mkdir(parents=True);p.write_bytes(data)
            with patch.object(adapter,'frozen_entries',return_value=[e]),patch.object(controls,'git',return_value=head or adapter.SOURCE_SHA):
                return adapter.verify_frozen_bytes(root,allow_generated=allow)
    def exact(self):return json.dumps({'revision':adapter.SOURCE_SHA},indent=2).encode()
    def test_original_tracked_revision_accepted_pristine(self):
        self.check_bytes(b'{\n  "revision": "local"\n}',allow=False)
    def test_exact_generated_revision_accepted_only_postbuild(self):
        self.check_bytes(self.exact())
        with self.assertRaisesRegex(AssertionError,'Frozen source changed'):self.check_bytes(self.exact(),allow=False)
    def test_different_full_commit_rejected(self):
        with self.assertRaisesRegex(AssertionError,'Generated revision bytes differ'):self.check_bytes(self.exact().replace(adapter.SOURCE_SHA.encode(),b'a'*40))
    def test_wrong_checkout_head_rejected(self):
        with self.assertRaisesRegex(AssertionError,'exact saved HEAD'):self.check_bytes(self.exact(),head='a'*40)
    def test_additional_keys_rejected(self):
        with self.assertRaises(AssertionError):self.check_bytes((json.dumps({'revision':adapter.SOURCE_SHA,'approval':True},indent=2)+'\n').encode())
    def test_compact_whitespace_or_added_newline_rejected(self):
        for b in [json.dumps({'revision':adapter.SOURCE_SHA}).encode(),self.exact()+b'\n',b' '+self.exact()]:
            with self.subTest(data=b),self.assertRaises(AssertionError):self.check_bytes(b)
    def test_nested_reference_revision_has_no_exception(self):
        with TemporaryDirectory() as t:
            root=Path(t);e=next(copy.deepcopy(e)for e in adapter.frozen_entries() if 'tests/reference/geumcheon-runtime/src/data/build-revision.json' in e['path'])
            p=root/e['path'];p.parent.mkdir(parents=True);p.write_bytes(self.exact())
            with patch.object(adapter,'frozen_entries',return_value=[e]),self.assertRaisesRegex(AssertionError,'Frozen source changed'):adapter.verify_frozen_bytes(root,allow_generated=True)
    def test_revision_file_symlink_rejected(self):
        with TemporaryDirectory() as t:
            root=Path(t);e=self.fixture();p=root/e['path'];p.parent.mkdir(parents=True);target=root/'outside';target.write_bytes(self.exact());p.symlink_to(target)
            with patch.object(adapter,'frozen_entries',return_value=[e]),self.assertRaisesRegex(AssertionError,'Symlink'):adapter.verify_frozen_bytes(root,allow_generated=True)
    def test_exact_source_tree_repository_pins(self):
        spec=adapter.load(adapter.HERE/'bound-spec.json');adapter.validate_spec(spec)
        for key in ('sourceSha','sourceTree','repositoryTree'):
            with self.subTest(key=key),self.assertRaisesRegex(AssertionError,'Exact saved source'):adapter.validate_spec({**spec,key:'a'*40})
    def test_n1_membership_and_two_facilities(self):
        from test_adapter import SOURCE
        e=adapter.expectations(SOURCE/adapter.SITE_PATH)
        self.assertEqual(len(e['pages']),1);self.assertEqual(len(e['legalUnits']),9);self.assertEqual(len(e['adminRows']),15)
        self.assertEqual(sum(len(r['relations']) for r in e['adminRows']),18)
        self.assertEqual([r['candidateId']for r in e['legalLinks']],['cau-hospital','boramae-hospital'])
    def test_home_product_mutation_rejected(self):
        from test_adapter import SOURCE,static_facts
        facts=static_facts('/');facts['products'].pop()
        with self.assertRaisesRegex(AssertionError,'Home product'):adapter.validate_extra_facts(facts,adapter.expectations(SOURCE/adapter.SITE_PATH),'/')
    def test_native_generator_bytes_match_allowance(self):
        from test_adapter import SOURCE
        script=(SOURCE/adapter.SITE_PATH/'scripts/write_build_revision.mjs').read_text()
        self.assertIn('JSON.stringify({revision:rev},null,2)',script)
        path=SOURCE/adapter.GENERATED_REVISION
        if path.read_bytes()!=b'{\n  "revision": "local"\n}':self.assertEqual(path.read_bytes(),self.exact())
    def test_every_home_product_gets_distinct_geometry(self):
        from test_adapter import SOURCE
        e=adapter.expectations(SOURCE/adapter.SITE_PATH)
        self.assertEqual([x for x in adapter.focus_labels(e,'/')if x.startswith('product-')],['product-'+x['key']for x in e['homeProducts']])
        self.assertEqual(sum(len(adapter.focus_labels(e,r))for r in adapter.ROUTES)*3,150)
    def test_home_product_selector_excludes_duplicate_hero_key(self):
        import inspect,run_bound_capture
        from test_adapter import SOURCE,DOM,cls
        source=inspect.getsource(run_bound_capture.supplemental)
        self.assertIn("'.product-card[data-product-key=",source)
        root=DOM((SOURCE/adapter.SITE_PATH/'dist/index.html').read_text()).root
        all_basic=root.all(lambda n:n.attrs.get('data-product-key')=='funeral-basic')
        cards=[x for x in all_basic if 'product-card'in x.attrs.get('class','').split()]
        self.assertEqual(len(all_basic),2);self.assertEqual(len(cards),1)
    def test_native_original_assertions_still_present(self):
        import inspect,capture,run_bound_capture
        self.assertIn('not facts[\'overflow\']',inspect.getsource(capture.assert_facts))
        source=inspect.getsource(run_bound_capture.supplemental)
        self.assertIn("assert_focus(flow['facts'])",source)
        self.assertIn("page.wait_for_url(origin+link['href'])",source)
        self.assertNotIn('add_style_tag',source)

if __name__=='__main__':unittest.main()
