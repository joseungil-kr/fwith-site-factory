import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('raw', Path(__file__).with_name('inspect_raw_http.py'))
raw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(raw)


class ManagedSuffixTests(unittest.TestCase):
    def setUp(self):
        self.original = b'User-agent: *\nAllow: /\nSitemap: https://example.test/sitemap.xml\n'
        self.prefix = raw.BEGIN + b'\nUser-agent: TestBot\nDisallow: /\n' + raw.END
        self.live = self.prefix + b'\n\n' + self.original

    def test_exact_original_suffix_is_preserved(self):
        self.assertEqual(raw.split_managed(self.live, self.original), self.prefix)

    def test_changed_sitemap_extra_directive_or_whitespace_is_rejected(self):
        for altered in [self.live.replace(b'example.test', b'foreign.test'), self.live + b'Disallow: /\n',
                        self.live.replace(b'\n\nUser-agent: *', b'\nUser-agent: *')]:
            with self.assertRaisesRegex(ValueError, 'original_suffix_changed'):
                raw.split_managed(altered, self.original)

    def test_missing_duplicate_or_reversed_markers_are_rejected(self):
        for altered in [self.live.replace(raw.END, b''), raw.BEGIN + self.live, raw.END + raw.BEGIN]:
            with self.assertRaisesRegex(ValueError, 'managed_markers'):
                raw.split_managed(altered, self.original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
