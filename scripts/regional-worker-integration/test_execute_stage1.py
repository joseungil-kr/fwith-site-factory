import copy
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from execute_stage1 import execute, Stop, Provider, Wrangler, check_state, DONGJAK, GEUMCHEON, D_VERSION, G_VERSION

PILOT = '11111111-1111-4111-8111-111111111111'
OTHER = '22222222-2222-4222-8222-222222222222'


def state(version=D_VERSION):
    settings = dict(compatibility_date='2026-10-09', compatibility_flags=[],
                    logpush=False, usage_model='standard', placement={}, bindings=[])
    result = {DONGJAK: dict(version=version, settings=copy.deepcopy(settings)),
              GEUMCHEON: dict(version=G_VERSION, settings=copy.deepcopy(settings))}
    if version != D_VERSION:
        result[DONGJAK]['settings']['bindings'] = [{'name': 'ASSETS', 'type': 'assets'}]
    return result


class FakeProvider:
    def __init__(self, snapshots):
        self.snapshots = iter(snapshots)
    def snapshot(self):
        value = next(self.snapshots)
        if isinstance(value, Exception): raise value
        return value


class FakeRunner:
    def __init__(self, outcomes=None):
        self.calls = []
        self.outcomes = iter(outcomes or [dict(ok=True, uuid=PILOT)])
    def run(self, operation):
        self.calls.append(operation)
        return next(self.outcomes)


class ExecutorTests(unittest.TestCase):
    def run_case(self, snapshots, probes, runner=None):
        runner = runner or FakeRunner()
        probes = iter(probes)
        return execute(FakeProvider(snapshots), runner, lambda: next(probes), lambda *a, **k: None)

    def test_normal_exact_pilot_readback(self):
        runner = FakeRunner()
        self.assertEqual(self.run_case([state(), state(), state(PILOT), state(PILOT)], ['same', 'same'], runner), 'pilot_verified')
        self.assertEqual(runner.calls, ['deploy'])

    def test_get_failure_and_predeploy_concurrent_change_never_write(self):
        for snapshots in [[Stop('get_failed')], [state(), Stop('get_failed')], [state(), state(OTHER)]]:
            runner = FakeRunner()
            with self.assertRaises(Stop): self.run_case(snapshots, ['same'], runner)
            self.assertEqual(runner.calls, [])

    def test_postdeploy_concurrent_change_is_not_overwritten(self):
        runner = FakeRunner()
        with self.assertRaises(Stop):
            self.run_case([state(), state(), state(OTHER), state(OTHER)], ['same'], runner)
        self.assertEqual(runner.calls, ['deploy'])

    def test_uncertain_deploy_reads_but_never_redeploys_or_adopts_uuid(self):
        for current in [state(), state(PILOT), Stop('get_failed')]:
            runner = FakeRunner([dict(ok=False, uuid=None)])
            with self.assertRaisesRegex(Stop, 'deploy_uuid_uncertain'):
                self.run_case([state(), state(), current], ['same'], runner)
            self.assertEqual(runner.calls, ['deploy'])

    def test_public_failure_restores_only_confirmed_pilot(self):
        runner = FakeRunner([dict(ok=True, uuid=PILOT), dict(ok=True, uuid=D_VERSION)])
        self.assertEqual(self.run_case([state(), state(), state(PILOT), state(PILOT), state()], ['same', 'different', 'same'], runner), 'rolled_back')
        self.assertEqual(runner.calls, ['deploy', 'rollback'])

    def test_get_failure_before_rollback_stops(self):
        runner = FakeRunner()
        with self.assertRaises(Stop):
            self.run_case([state(), state(), Stop('get_failed'), Stop('get_failed')], ['same'], runner)
        self.assertEqual(runner.calls, ['deploy'])

    def test_rollback_failure_is_not_retried(self):
        runner = FakeRunner([dict(ok=True, uuid=PILOT), dict(ok=False, uuid=None)])
        with self.assertRaises(Stop):
            self.run_case([state(), state(), state(PILOT), state(PILOT), state(PILOT)], ['same', 'different'], runner)
        self.assertEqual(runner.calls, ['deploy', 'rollback'])

    def test_uncertain_rollback_success_requires_readback_and_public_proof(self):
        runner = FakeRunner([dict(ok=True, uuid=PILOT), dict(ok=False, uuid=None)])
        self.assertEqual(self.run_case([state(), state(), state(PILOT), state(PILOT), state()], ['same', 'different', 'same'], runner), 'rolled_back')

    def test_nonzero_deploy_with_recorded_uuid_requires_guarded_recovery(self):
        runner = FakeRunner([dict(ok=False, uuid=PILOT), dict(ok=True, uuid=D_VERSION)])
        self.assertEqual(self.run_case([state(), state(), state(PILOT), state(PILOT), state()], ['same', 'same'], runner), 'rolled_back')

    def test_settings_and_unexpected_bindings_rejected(self):
        for key, value in [('logpush', True), ('usage_model', 'other'), ('bindings', [{'type':'secret_text'}])]:
            sample = state()
            sample[DONGJAK]['settings'][key] = value
            with self.assertRaises(Stop): check_state(sample, D_VERSION)

    def test_transport_refuses_unlisted_or_mutating_paths_without_network(self):
        provider = object.__new__(Provider)
        for path in ['workers/scripts/other/settings', 'workers/scripts/' + DONGJAK, 'workers/domains/anything', '../tokens']:
            with self.assertRaisesRegex(Stop, 'get_path_not_allowed'): provider.get(path)

    def test_runner_never_repeats_command(self):
        runner = object.__new__(Wrangler)
        runner.called = {'deploy', 'rollback'}
        for action in ['deploy', 'rollback', 'attach', 'delete']:
            with self.assertRaisesRegex(Stop, 'mutation_retry_refused'): runner.run(action)

    def test_fixed_subprocess_arguments_and_ambiguous_output(self):
        for output, expected in [(f'Current Version ID: {PILOT}', PILOT),
                                 (f'Current Version ID: {PILOT}\nCurrent Version ID: {OTHER}', None),
                                 ('no UUID', None)]:
            runner = object.__new__(Wrangler)
            runner.called, runner.cli, runner.bundle = set(), Path('pinned/wrangler.js'), Path('verified-bundle')
            with patch('execute_stage1.verify_bundle'), patch('execute_stage1.subprocess.run',
                    return_value=SimpleNamespace(returncode=0, stdout=output)) as command:
                self.assertEqual(runner.run('deploy')['uuid'], expected)
                self.assertEqual(command.call_args.args[0], ['node', str(runner.cli), 'deploy', '--config', str(runner.bundle / 'wrangler.stage1.json')])
                self.assertTrue(command.call_args.kwargs['capture_output'])
                self.assertNotIn('--force', command.call_args.args[0])
                self.assertNotIn('shell', command.call_args.kwargs)

    def test_real_snapshot_parser_accepts_only_complete_expected_domains_and_100_percent(self):
        for fault in [None, 'pagination', 'mapping', 'split', 'missing_version']:
            provider = object.__new__(Provider)
            def get(path):
                if path.startswith('workers/domains'):
                    rows = [dict(hostname='seoul-dongjak.fwith.kr', service=DONGJAK, enabled=True, previews_enabled=False),
                            dict(hostname='seoul-geumcheon.fwith.kr', service=GEUMCHEON, enabled=True, previews_enabled=False)]
                    if fault == 'mapping': rows[1]['service'] = DONGJAK
                    info = dict(page=1, total_pages=1, total_count=2)
                    return dict(result=rows, result_info={} if fault == 'pagination' else info)
                worker = DONGJAK if DONGJAK in path else GEUMCHEON
                version = D_VERSION if worker == DONGJAK else G_VERSION
                if path.endswith('/deployments'):
                    return dict(result=dict(deployments=[dict(created_on='2026-11-01T00:00:00Z',
                        versions=[dict(version_id=version, percentage=50 if fault == 'split' else 100)])]))
                if '/versions/' in path:
                    return dict(result=dict(id=None if fault == 'missing_version' else version))
                if path.endswith('/settings'): return dict(result=state()[worker]['settings'])
                raise AssertionError(path)
            provider.get = get
            with self.subTest(fault=fault):
                if fault is None: check_state(provider.snapshot(), D_VERSION)
                else:
                    with self.assertRaises(Stop): provider.snapshot()


if __name__ == '__main__': unittest.main(verbosity=2)
