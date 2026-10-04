"""Read-only initial preflight wrappers, never actual account evidence."""
import json
from pathlib import Path
import tempfile
import unittest
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import initial_domain as initial


class InitialDomainTests(unittest.TestCase):
    def test_exact_targets_use_only_existing_preflight_and_restore_defaults(self):
        original = initial.adapter.HOSTNAME, initial.adapter.WORKER
        for key in initial.INITIAL_REGIONS:
            with self.subTest(site=key), tempfile.TemporaryDirectory() as directory:
                report = Path(directory) / 'report.json'
                def fake(args):
                    self.assertEqual(args, ['--preflight', '--report', str(report)])
                    self.assertEqual(initial.adapter.HOSTNAME, key.split('-')[0] + '.fwith.kr')
                    self.assertEqual(initial.adapter.WORKER, key.split('-')[0] + '-flower-prod-disabled')
                    report.write_text(json.dumps({'state':'bucheon_initial_target_absent_verified', 'mutationsPerformed':False}))
                    return 0
                with patch.object(initial.adapter, 'main', fake):
                    self.assertEqual(initial.inspect_initial(key, report), 0)
                self.assertEqual((initial.adapter.HOSTNAME, initial.adapter.WORKER), original)
                value = json.loads(report.read_text())
                self.assertEqual(value['state'], 'initial_target_absent_verified')
                self.assertEqual(value['siteKey'], key)
                self.assertIs(value['mutationsPerformed'], False)

    def test_unknown_or_unreviewed_target_cannot_touch_adapter(self):
        with patch.object(initial.adapter, 'main') as call:
            with self.assertRaises(ValueError):
                initial.inspect_initial('unknown-flower-v2', Path('/tmp/not-created'))
            call.assert_not_called()

    def test_failure_never_becomes_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / 'report.json'
            def fake(args):
                report.write_text(json.dumps({'state':'blocked','httpStatus':403,'mutationsPerformed':False}))
                return 1
            with patch.object(initial.adapter, 'main', fake):
                self.assertEqual(initial.inspect_initial('namyangju-flower-v2', report), 1)
            self.assertEqual(json.loads(report.read_text())['state'], 'initial_target_blocked')

    def test_exception_restores_historical_adapter_identity(self):
        original = initial.adapter.HOSTNAME, initial.adapter.WORKER
        with patch.object(initial.adapter, 'main', side_effect=RuntimeError('fixture')):
            with self.assertRaises(RuntimeError):
                initial.inspect_initial('namyangju-flower-v2', Path('/tmp/not-created'))
        self.assertEqual((initial.adapter.HOSTNAME, initial.adapter.WORKER), original)


if __name__ == '__main__':
    unittest.main()
