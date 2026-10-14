import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import complete_uploaded as recovery


class CompletionTests(unittest.TestCase):
    def request(self):
        env = dict(GITHUB_REPOSITORY=recovery.core.REPOSITORY, GITHUB_REF='refs/heads/main',
                   GITHUB_ACTOR=recovery.core.gate.OWNER, GITHUB_RUN_ATTEMPT='1', GITHUB_EVENT_NAME='issues',
                   GITHUB_SHA='a' * 40, REVISION=recovery.SOURCE)
        body = dict(schemaVersion=1, mode='complete_uploaded', source_branch=recovery.core.BRANCH,
                    source_revision=recovery.SOURCE, expected_control_revision=env['GITHUB_SHA'],
                    binding_sha256=recovery.BINDING_SHA, prior_run_id=recovery.PRIOR_RUN,
                    prior_artifact_id=recovery.PRIOR_ARTIFACT)
        event = dict(action='opened', repository=dict(full_name=recovery.core.REPOSITORY,
                     owner=dict(login=recovery.core.gate.OWNER, type='User')),
                     issue=dict(title=recovery.TITLE, user=dict(login=recovery.core.gate.OWNER), body=json.dumps(body)))
        return env, event

    def test_exact_owner_request_and_mutations_rejected(self):
        env, event = self.request()
        recovery.authorize(env, event)
        for key, value in [('GITHUB_RUN_ATTEMPT', '2'), ('REVISION', 'b' * 40),
                           ('GITHUB_ACTOR', 'other'), ('GITHUB_REF', 'refs/heads/other')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                recovery.authorize(dict(env, **{key: value}), event)
        for key, value in [('prior_run_id', '1'), ('prior_artifact_id', '1'), ('mode', 'publish'),
                           ('source_revision', 'b' * 40), ('expected_control_revision', 'b' * 40),
                           ('binding_sha256', 'b' * 64), ('extra', True)]:
            altered = copy.deepcopy(event)
            body = json.loads(altered['issue']['body']); body[key] = value
            altered['issue']['body'] = json.dumps(body)
            with self.subTest(key=key), self.assertRaises(ValueError):
                recovery.authorize(env, altered)

    def proof(self):
        return dict(state='prior_upload_actual_outcomes_verified', priorRunId=recovery.PRIOR_RUN,
                    priorControlSha=recovery.PRIOR_CONTROL, priorArtifactId=recovery.PRIOR_ARTIFACT,
                    priorArchiveSha256=recovery.PRIOR_ZIP_SHA, runAttempt=1,
                    deployOutcome='success', attachOutcome='failure', bindingOutcome='failure',
                    httpOutcome='skipped', indexnowOutcome='skipped', buildRunId=recovery.BUILD_RUN,
                    buildArtifactId=recovery.BUILD_ARTIFACT, buildControlSha=recovery.BUILD_CONTROL,
                    jobLogSha256='a' * 64, jobId=recovery.PRIOR_JOB)

    def test_actual_outcomes_not_success_summary(self):
        recovery.validate_api_proof(self.proof())
        for key, value in [('deployOutcome', 'failure'), ('attachOutcome', 'success'),
                           ('bindingOutcome', 'success'), ('httpOutcome', 'success'),
                           ('runAttempt', 2), ('priorControlSha', 'b' * 40), ('jobLogSha256', None)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                recovery.validate_api_proof(dict(self.proof(), **{key: value}))

    def run_binding(self, states, attach_error=False, marker=False, identity_after=None):
        calls = []
        def inspect(account, transport, stage):
            calls.append(('GET-inspection', stage))
            value = states.pop(0)
            if isinstance(value, Exception): raise value
            return value
        def attach(transport, account):
            calls.append(('PUT', recovery.core.HOSTNAME))
            if attach_error: raise attach_error if isinstance(attach_error, Exception) else TimeoutError()
        def identity(require_bound):
            calls.append(('identity-GET', require_bound))
            if require_bound and identity_after is not None:
                return identity_after
            return dict(workerVersionId='pinned-version', assetsMetadataSha256='pinned-assets')
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                if marker: Path('completion-attach-attempt.json').write_text('{}')
                result = recovery.complete_binding('a' * 32, object(), attach, inspect, identity)
            finally:
                path = Path('completion-attach-result.json')
                self.last_attach_report = json.loads(path.read_text()) if path.exists() else None
                os.chdir(previous)
        return result, calls

    def bound(self, yes):
        return dict(state='binding_verified' if yes else 'uploaded_worker_verified',
                    hostnameBindingExists=yes, workerExists=True, hostname=recovery.core.HOSTNAME,
                    worker=recovery.core.WORKER)

    def test_existing_exact_binding_never_puts(self):
        result, calls = self.run_binding([self.bound(True), self.bound(True)])
        self.assertFalse(result['requestAttempted'])
        self.assertEqual(calls, [('identity-GET', False), ('GET-inspection', 'attach'),
                                 ('GET-inspection', 'readback'), ('identity-GET', True)])

    def test_unbound_worker_attaches_exactly_once_and_reads_back(self):
        result, calls = self.run_binding([self.bound(False), self.bound(True)])
        self.assertTrue(result['requestAttempted'])
        self.assertEqual([c[0] for c in calls], ['identity-GET', 'GET-inspection', 'PUT', 'GET-inspection', 'identity-GET'])

    def test_uncertain_put_only_gets_no_retry(self):
        result, calls = self.run_binding([self.bound(False), self.bound(True)], attach_error=True)
        self.assertTrue(result['acknowledgementUncertain'])
        self.assertEqual(sum(c[0] == 'PUT' for c in calls), 1)
        self.assertEqual(self.last_attach_report['error']['type'], 'TimeoutError')

    def test_explicit_rejection_is_preserved_and_not_called_uncertain(self):
        with self.assertRaisesRegex(ValueError, 'attach_explicitly_rejected'):
            self.run_binding([self.bound(False), self.bound(True)], attach_error=ValueError('provider_rejected'))
        self.assertEqual(self.last_attach_report['error']['code'], 'provider_rejected')
        self.assertFalse(self.last_attach_report['acknowledgementUncertain'])

    def test_first_put_error_survives_readback_failure(self):
        with self.assertRaisesRegex(ValueError, 'binding_missing'):
            self.run_binding([self.bound(False), ValueError('binding_missing')], attach_error=ValueError('provider_rejected'))
        self.assertEqual(self.last_attach_report['error']['code'], 'provider_rejected')

    def test_collision_fails_before_any_attach(self):
        with self.assertRaisesRegex(ValueError, 'collision'):
            self.run_binding([ValueError('collision')])

    def test_readback_failure_remains_blocked(self):
        with self.assertRaisesRegex(ValueError, 'missing'):
            self.run_binding([self.bound(False), ValueError('missing')])

    def test_prior_attempt_marker_blocks_repeat_put(self):
        with self.assertRaises(FileExistsError):
            self.run_binding([self.bound(False)], marker=True)

    def test_original_strict_artifact_gate_is_reused(self):
        with patch.object(recovery, 'fixed_release'), patch.object(recovery, 'prior_evidence', return_value={}), \
             patch.object(recovery.core, 'artifact', side_effect=ValueError('unexpected_release_files')):
            with self.assertRaisesRegex(ValueError, 'unexpected_release_files'):
                recovery.prepare()

    def test_pending_identity_is_blocked_before_inspector_import(self):
        with patch.object(recovery, 'read', return_value=dict(schemaVersion=1, state='pending')):
            with self.assertRaisesRegex(ValueError, 'uploaded_worker_identity_evidence_pending'):
                recovery.uploaded_identity(False)

    def test_identity_failure_occurs_before_provider_or_attach(self):
        inspect, attach = unittest.mock.Mock(), unittest.mock.Mock()
        identity = unittest.mock.Mock(side_effect=ValueError('identity_mismatch'))
        with self.assertRaisesRegex(ValueError, 'identity_mismatch'):
            recovery.complete_binding('a' * 32, object(), attach, inspect, identity)
        inspect.assert_not_called(); attach.assert_not_called()

    def test_identity_drift_after_binding_blocks_completion(self):
        for changed in [dict(workerVersionId='other-version', assetsMetadataSha256='pinned-assets'),
                        dict(workerVersionId='pinned-version', assetsMetadataSha256='other-assets')]:
            with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, 'uploaded_identity_changed_during_binding'):
                self.run_binding([self.bound(False), self.bound(True)], identity_after=changed)

    def test_error_redaction_does_not_preserve_raw_response_or_message(self):
        result = recovery.sanitized_error(ValueError('secret token raw upstream text'))
        self.assertEqual(result, dict(type='ValueError', code=None, httpStatus=None, cloudflareCodes=[]))

    def test_readonly_rejected_keeps_only_sanitized_code(self):
        class Rejected(RuntimeError):
            pass
        self.assertEqual(recovery.sanitized_error(Rejected('account_identity_unverified'))['code'],
                         'account_identity_unverified')
        self.assertIsNone(recovery.sanitized_error(Rejected('upstream raw value token=secret'))['code'])

    def test_identity_projection_requires_raw_settings_and_disabled_subdomains(self):
        facts = dict(state='uploaded_worker_identity_observed', worker=recovery.core.WORKER,
                     hostname=recovery.core.HOSTNAME, workerExists=True, accountVerified=True, mutationsPerformed=False,
                     deployment=dict(id='d', versions=[dict(version_id='v', percentage=100)]),
                     script=dict(has_assets=True),
                     version=dict(id='v', script=dict(etag=dict(present=False,type='absent',length=None,sha256=None,isEmpty=None)), assets={}, bindingTypes=[]),
                     settings=dict(assets={}, bindingTypes=[]), rawSettingsSha256='a' * 64, rawVersionSha256='b' * 64,
                     subdomain=dict(enabled=False, previews_enabled=False))
        self.assertEqual(recovery.identity_projection(facts)['workerVersionId'], 'v')
        for label, change in [('rawSettingsSha256', None),
                              ('rawVersionSha256', None),
                              ('inspectionErrors', {'version': 'unverified'}),
                              ('scriptMetadataErrors', {'has_assets': 'invalid'}),
                              ('script', dict(has_assets=False)),
                              ('subdomain', dict(enabled=False, previews_enabled=True)),
                              ('deployment', dict(id='d', versions=[dict(version_id='v2', percentage=100)]))]:
            with self.subTest(label=label), self.assertRaises(ValueError):
                recovery.identity_projection(dict(facts, **{label: change}))


if __name__ == '__main__':
    unittest.main()
