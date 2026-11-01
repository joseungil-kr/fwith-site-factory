import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('reconcile', Path(__file__).with_name('reconcile_release_evidence.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DifferenceClassificationTests(unittest.TestCase):
    def test_redirect_is_not_claimed_as_file_match(self):
        self.assertTrue(module.classify('/404.html', '307', module.EMPTY_SHA, 'retained').startswith('redirect_response'))
        self.assertTrue(module.classify('/404.html', '307', 'unexpected-body', 'retained').startswith('unexplained'))

    def test_robots_is_not_blindly_normalized(self):
        self.assertTrue(module.classify('/robots.txt', '200', 'different', 'original').startswith('robots_difference'))
        self.assertTrue(module.classify('/robots.txt', '403', 'different', 'original').startswith('unexplained'))

    def test_body_hash_requires_success_status(self):
        self.assertEqual(module.classify('/', '200', 'same', 'same'), 'exact_public_body_match')
        self.assertTrue(module.classify('/', '403', 'same', 'same').startswith('unexplained'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
