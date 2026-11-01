import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('pilot_package', Path(__file__).with_name('package.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sources = {}
        for region in module.PILOT:
            source = module.ROOT.parent / f'build-{region}/dist'
            destination = self.root / region
            shutil.copytree(source, destination)
            self.sources[region] = destination

    def test_package_and_reconstruct_original_files(self):
        output = self.root / 'combined'
        report = module.package(self.sources, output)
        self.assertEqual(report['packageFileCount'], 37)
        self.assertEqual(report['uploadableAssetCount'], 36)
        for region, source in self.sources.items():
            restored = self.root / f'restored-{region}'
            shutil.copytree(output / 'assets/__regional' / region, restored)
            # Original header bytes are retained with the source build, not inferred from merged rules.
            shutil.copyfile(source / '_headers', restored / '_headers')
            original = {p.relative_to(source): module.digest(p) for p in source.rglob('*') if p.is_file()}
            actual = {p.relative_to(restored): module.digest(p) for p in restored.rglob('*') if p.is_file()}
            self.assertEqual(actual, original)

    def test_changed_body_rejected_before_output_creation(self):
        (self.sources['dongjak'] / 'index.html').write_bytes(b'wrong region')
        output = self.root / 'combined'
        with self.assertRaisesRegex(ValueError, 'built_bytes_differ'):
            module.package(self.sources, output)
        self.assertFalse(output.exists())

    def test_missing_verification_file_rejected(self):
        (self.sources['geumcheon'] / '40ce75e866dc2c92254e7d1ad474326f.txt').unlink()
        with self.assertRaisesRegex(ValueError, 'built_bytes_differ'):
            module.package(self.sources, self.root / 'combined')

    def test_existing_output_and_partial_pilot_rejected(self):
        with self.assertRaisesRegex(ValueError, 'output_must_be_new'):
            module.package(self.sources, self.root)
        with self.assertRaisesRegex(ValueError, 'exact_two_regions_required'):
            module.package({'dongjak': self.sources['dongjak']}, self.root / 'combined')


if __name__ == '__main__':
    unittest.main(verbosity=2)
