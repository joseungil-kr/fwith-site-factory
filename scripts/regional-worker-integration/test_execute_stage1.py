import copy
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from execute_stage1 import execute, Stop, Provider, Wrangler, check_state, single_page_domains, DONGJAK, GEUMCHEON, D_VERSION, G_VERSION

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

    def test_concurrent_settings_change_before_recovery_stops_all_writes(self):
        for worker in [DONGJAK, GEUMCHEON]:
            changed = state(PILOT)
            changed[worker]['settings']['logpush'] = True
            runner = FakeRunner()
            with self.subTest(worker=worker), self.assertRaisesRegex(Stop, 'settings_drift'):
                self.run_case([state(), state(), state(PILOT), changed], ['same', 'different'], runner)
            self.assertEqual(runner.calls, ['deploy'])

    def test_initial_dongjak_settings_error_can_recover_only_if_unchanged(self):
        initial = state(PILOT)
        initial[DONGJAK]['settings']['logpush'] = True
        runner = FakeRunner([dict(ok=True, uuid=PILOT), dict(ok=True, uuid=D_VERSION)])
        self.assertEqual(self.run_case([state(), state(), initial, copy.deepcopy(initial), state()], ['same', 'same'], runner), 'rolled_back')
        self.assertEqual(runner.calls, ['deploy', 'rollback'])
        later = copy.deepcopy(initial)
        later[DONGJAK]['settings']['usage_model'] = 'concurrent-change'
        runner = FakeRunner()
        with self.assertRaisesRegex(Stop, 'rollback_dongjak_settings_drift'):
            self.run_case([state(), state(), initial, later], ['same'], runner)
        self.assertEqual(runner.calls, ['deploy'])

    def test_geumcheon_drift_in_first_postdeploy_snapshot_is_never_ours(self):
        changed = state(PILOT)
        changed[GEUMCHEON]['settings']['logpush'] = True
        runner = FakeRunner()
        with self.assertRaisesRegex(Stop, 'rollback_geumcheon_settings_drift'):
            self.run_case([state(), state(), changed, changed], ['same'], runner)
        self.assertEqual(runner.calls, ['deploy'])

    def test_no_first_postdeploy_snapshot_means_no_settings_recovery_baseline(self):
        runner = FakeRunner()
        with self.assertRaisesRegex(Stop, 'rollback_postdeploy_baseline_unavailable'):
            self.run_case([state(), state(), Stop('get_failed'), state(PILOT)], ['same'], runner)
        self.assertEqual(runner.calls, ['deploy'])

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
        for fault in [None, 'missing_metadata', 'pagination', 'mapping', 'split', 'missing_version', 'ignored_filter', 'missing_unfiltered']:
            provider = object.__new__(Provider)
            def get(path):
                if path.startswith('workers/domains'):
                    rows = [dict(id='domain-dongjak', hostname='seoul-dongjak.fwith.kr', service=DONGJAK, enabled=True, previews_enabled=False),
                            dict(id='domain-geumcheon', hostname='seoul-geumcheon.fwith.kr', service=GEUMCHEON, enabled=True, previews_enabled=False)]
                    if fault == 'mapping': rows[1]['service'] = DONGJAK
                    if fault == 'missing_unfiltered' and '?' not in path: rows = rows[:1]
                    if '?' in path and fault != 'ignored_filter':
                        key, value = path.split('?', 1)[1].split('=', 1)
                        rows = [r for r in rows if r[key] == value]
                    info = dict(page=1, total_pages=2 if fault == 'pagination' else 1, total_count=len(rows))
                    return dict(success=True, result=rows, **({} if fault == 'missing_metadata' else {'result_info': info}))
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
                if fault in [None, 'missing_metadata']: check_state(provider.snapshot(), D_VERSION)
                else:
                    with self.assertRaises(Stop): provider.snapshot()

    def test_single_page_optional_metadata_without_invented_pagination(self):
        row = dict(id='one', hostname='example.test', service='worker')
        for info in [None, {}, {'count': 1}, {'page': 1, 'total_pages': 1, 'total_count': 1, 'per_page': 100}]:
            payload = dict(success=True, result=[row])
            if info is not None: payload['result_info'] = info
            self.assertEqual(single_page_domains(payload), [row])

    def test_incomplete_or_advertised_continuation_is_never_accepted(self):
        row = dict(id='one', hostname='example.test', service='worker')
        for info in [{'total_count': 2}, {'count': 2}, {'page': 2}, {'total_pages': 2},
                     {'per_page': 0}, {'page': '1'}, {'page': True}, {'cursor': 'next'}, None]:
            with self.subTest(info=info), self.assertRaises(Stop):
                single_page_domains(dict(success=True, result=[row], result_info=info))
        for key in ['cursor', 'next', 'links', 'has_more']:
            with self.subTest(key=key), self.assertRaises(Stop):
                single_page_domains(dict(success=True, result=[row], **{key: 'continuation'}))

    def test_domain_errors_duplicate_ids_and_malformed_rows_stop(self):
        row = dict(id='one', hostname='example.test', service='worker')
        for patch in [dict(success=False), dict(errors=[{'code':1}]), dict(result=[row, row]),
                      dict(result=[{'id':'one'}]), dict(result={}), dict(result=[None])]:
            with self.subTest(patch=patch), self.assertRaises(Stop):
                single_page_domains({**dict(success=True, result=[row]), **patch})


if __name__ == '__main__': unittest.main(verbosity=2)
