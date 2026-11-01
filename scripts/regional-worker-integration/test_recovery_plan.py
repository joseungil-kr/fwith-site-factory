import unittest
from recovery_plan import next_action, DONGJAK, GEUMCHEON, D_VERSION, G_VERSION


class RecoveryOrderTests(unittest.TestCase):
    def setUp(self):
        self.state = dict(fresh_readback=True, geumcheon_version=G_VERSION,
                          geumcheon_service=DONGJAK, dongjak_service=DONGJAK,
                          dongjak_version='integrated-candidate', geumcheon_public_verified=False)

    def test_moved_domain_must_be_restored_before_rollback(self):
        self.assertEqual(next_action(self.state)['action'], 'RESTORE_GEUMCHEON_DOMAIN')

    def test_binding_readback_requires_public_verification(self):
        self.state['geumcheon_service'] = GEUMCHEON
        self.assertEqual(next_action(self.state)['action'], 'VERIFY_GEUMCHEON')
        self.state['geumcheon_public_verified'] = True
        self.assertEqual(next_action(self.state)['action'], 'ROLLBACK_DONGJAK')

    def test_original_versions_need_verification_not_redeployment(self):
        self.state.update(geumcheon_service=GEUMCHEON, geumcheon_public_verified=True, dongjak_version=D_VERSION)
        self.assertEqual(next_action(self.state)['action'], 'VERIFY_FINAL')

    def test_unknown_or_stale_state_stops(self):
        for patch in [dict(fresh_readback=False), dict(geumcheon_service='unexpected'), dict(geumcheon_version='drift')]:
            with self.subTest(patch=patch):
                self.assertEqual(next_action({**self.state, **patch})['action'], 'STOP')


if __name__ == '__main__':
    unittest.main(verbosity=2)
