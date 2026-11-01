import unittest
from stage1_commands import prepare, DONGJAK, GEUMCHEON, D_VERSION, G_VERSION


class Stage1Commands(unittest.TestCase):
    def setUp(self):
        self.pilot = '11111111-1111-4111-8111-111111111111'
        self.state = dict(fresh_readback=True, dongjak_service=DONGJAK, geumcheon_service=GEUMCHEON,
                          dongjak_version=D_VERSION, geumcheon_version=G_VERSION,
                          dongjak_percentage=100, geumcheon_percentage=100, expected_pilot_uuid=self.pilot)

    def test_deploy_only_from_original_and_rollback_only_from_recorded_pilot(self):
        self.assertIn('deploy', prepare(self.state, 'deploy'))
        with self.assertRaises(ValueError): prepare(self.state, 'rollback')
        self.state['dongjak_version'] = self.pilot
        self.assertIn(D_VERSION, prepare(self.state, 'rollback'))
        with self.assertRaises(ValueError): prepare(self.state, 'deploy')

    def test_unknown_conflict_and_moved_domain_refused(self):
        for patch in [dict(dongjak_version=None), dict(dongjak_version=''), dict(dongjak_version='unknown'),
                      dict(dongjak_version='22222222-2222-4222-8222-222222222222'),
                      dict(geumcheon_service=DONGJAK), dict(fresh_readback=False)]:
            for operation in ['deploy', 'rollback']:
                with self.subTest(patch=patch, operation=operation), self.assertRaises(ValueError):
                    prepare({**self.state, **patch}, operation)


if __name__ == '__main__': unittest.main(verbosity=2)
