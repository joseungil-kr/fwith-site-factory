#!/usr/bin/env python3
"""Complete one already-uploaded Seocho release; never build or deploy a Worker."""
import argparse
import json
import os
from pathlib import Path
import re
import stat
from datetime import datetime, timezone
import publish as core

SOURCE = '52741146f4147f64d6804a757f560db0acf0d92c'
BUILD_RUN = '38529418686'
BUILD_ARTIFACT = '11877630325'
BUILD_CONTROL = '17b0120247c2561591fdfd0b6cfd54d6642d1a80'
PRIOR_RUN = '38532307939'
PRIOR_JOB = 115746811691
PRIOR_CONTROL = '80c4427cadefd387fc06d84104049335b5b4078f'
PRIOR_ARTIFACT = '11877743999'
PRIOR_ZIP_SHA = 'f86b758d5081d0fe1571a925d66bde1594a03cd1159308cdad721adbf27934e3'
BINDING_SHA = '46b852e1fa80cfd4965f9e5abb2e5087c17cff4b42b6be2df76c43de342b87e3'
CONTRACT_SHA = '905ff30fe7ae7ac5ae995174b002ee75010c6c9da038157f34d1b8bb9f22b68a'
CORE_SHA = 'ff695e5fc01ca5cb15a0a7102a8f347931464773a7aae42554853347a2ed761f'
REVIEW_SHA = 'd0436af5a8afe2f022a5e55388735e32b3350718042126a2d1f50c7952ddcfe8'
TITLE = '[SEOCHO-COMPLETE-UPLOADED] 20261014'
PRIOR_FILES = {
    'artifact-check.json': '4a22959031406139e9986750989e4cdec8da673b94f6eb0ee995f33431d5a604',
    'binding-after.json': '10d387305197d045a657f2aa105e28ba048bd2089445a3305149aa237445cc36',
    'binding-before.json': '84331a7f021fc7407a8a2913f10b23fc9d50385af26788d0460cf9c68c04ed2a',
    'domain-attach.json': '1e4615d64a5793b6dfbbbacbe075122729d706439ba3d2e58cc0932320999850',
    'http-contract.json': '3dbdaab4b3481e27a174aa384313da22ad7f74e5dc0d8311c9935a12460328d4',
    'release/release.json': 'd02507a8684efe6c27c24eebf30f6b98379284b8d5b8ceb33a72f9866d52dd4e',
    'release/wrangler.publish.json': '2c22a9eec4da8513a6822f7c3ceebf99418850fdc31b915ac38b30ecdd032446',
    'selected-release.json': '024b3ce8d7bce873570e90f225a8265f7c267fd835ac698e50cfe66065dcda06',
    'selected-source.json': '6bd749b1000b7d85c98987dbc154026fda68efd43dbb0e0bfe6f6b36081a779e',
}
require = core.require


def read(path):
    return json.loads(core.gate.read(Path(path)))


def authorize(env, event):
    require(env.get('GITHUB_REPOSITORY') == core.REPOSITORY and env.get('GITHUB_REF') == 'refs/heads/main'
            and env.get('GITHUB_ACTOR') == core.gate.OWNER and env.get('GITHUB_RUN_ATTEMPT') == '1',
            'owner_main_first_attempt_required')
    require(env.get('GITHUB_EVENT_NAME') == 'issues' and event.get('action') == 'opened', 'opened_issue_required')
    repo, issue = event.get('repository', {}), event.get('issue', {})
    require(repo.get('full_name') == core.REPOSITORY and repo.get('owner', {}).get('login') == core.gate.OWNER
            and repo.get('owner', {}).get('type') == 'User', 'repository_owner_mismatch')
    require(issue.get('title') == TITLE and issue.get('user', {}).get('login') == core.gate.OWNER,
            'issue_owner_or_title_mismatch')
    require(re.fullmatch('[0-9a-f]{40}', env.get('GITHUB_SHA', '')), 'control_sha_required')
    raw = issue.get('body')
    require(isinstance(raw, str) and len(raw) < 2048, 'request_body_invalid')
    request = json.loads(raw)
    require(type(request.get('schemaVersion')) is int and request == dict(schemaVersion=1, mode='complete_uploaded',
            source_branch=core.BRANCH, source_revision=SOURCE, expected_control_revision=env['GITHUB_SHA'],
            binding_sha256=BINDING_SHA, prior_run_id=PRIOR_RUN, prior_artifact_id=PRIOR_ARTIFACT),
            'exact_completion_request_required')
    require(env.get('REVISION') == SOURCE, 'fixed_revision_required')


def fixed_release():
    require(core.sha(core.gate.read(Path(core.__file__))) == CORE_SHA, 'reviewed_core_bytes_required')
    contract, binding, digest = core.gate.load()
    require(contract['expectedSourceRevision'] == SOURCE and digest == BINDING_SHA
            and binding['sourceContractSha256'] == CONTRACT_SHA, 'fixed_release_contract_required')
    descriptor = read(Path(core.__file__).with_name('production-release-review-binding.json'))
    require(descriptor.get('sha256') == REVIEW_SHA, 'fixed_review_required')
    review = core.release_review()
    require(str(review['buildRunId']) == BUILD_RUN and str(review['artifactId']) == BUILD_ARTIFACT
            and review['buildControlSha'] == BUILD_CONTROL, 'fixed_build_required')
    return review


def validate_api_proof(proof):
    expected = dict(state='prior_upload_actual_outcomes_verified', priorRunId=PRIOR_RUN,
                    priorControlSha=PRIOR_CONTROL, priorArtifactId=PRIOR_ARTIFACT,
                    priorArchiveSha256=PRIOR_ZIP_SHA, runAttempt=1,
                    deployOutcome='success', attachOutcome='failure', bindingOutcome='failure',
                    httpOutcome='skipped', indexnowOutcome='skipped', buildRunId=BUILD_RUN,
                    buildArtifactId=BUILD_ARTIFACT, buildControlSha=BUILD_CONTROL)
    require(all(proof.get(k) == v for k, v in expected.items()), 'prior_actual_outcome_proof_required')
    require(isinstance(proof.get('jobLogSha256'), str) and re.fullmatch('[0-9a-f]{64}', proof['jobLogSha256'])
            and type(proof.get('jobId')) is int and proof['jobId'] == PRIOR_JOB, 'prior_job_log_binding_required')


def prior_evidence(root=Path('prior-result'), proof_path=Path('prior-upload-api.json')):
    require(root.is_dir() and not root.is_symlink(), 'prior_artifact_root_invalid')
    files = {}
    for path in root.rglob('*'):
        require(stat.S_ISDIR(path.lstat().st_mode) or stat.S_ISREG(path.lstat().st_mode), 'prior_unsafe_file_type')
        if path.is_file():
            files[path.relative_to(root).as_posix()] = core.sha(core.gate.read(path))
    # This evidence package includes one pinned Wrangler JSON, never executed.
    # The independent clean release/dist gate remains unchanged.
    require(files == PRIOR_FILES, 'prior_artifact_digest_or_inventory_mismatch')
    before = read(root / 'binding-before.json')
    require(before == dict(accountVerified=True, dnsState='not_observed', hostname=core.HOSTNAME,
            hostnameBindingExists=False, mutationsPerformed=False, state='target_absent_verified',
            worker=core.WORKER, workerExists=False), 'prior_target_absent_required')
    for name, mode in [('domain-attach.json', 'attach'), ('binding-after.json', 'readback')]:
        require(read(root / name) == dict(code='unexpected_release_files', mode=mode, state='blocked_or_failed'),
                'prior_pre_provider_failure_required')
    validate_api_proof(read(proof_path))
    return dict(state='prior_upload_evidence_verified', priorRunId=PRIOR_RUN, priorArtifactId=PRIOR_ARTIFACT,
                priorFiles=len(PRIOR_FILES), previousProviderAttachAttempted=False)


def prepare():
    fixed_release()
    previous = prior_evidence()
    result = core.artifact()
    require(core.sha(core.gate.read(Path('http-contract.json'))) == PRIOR_FILES['http-contract.json'],
            'previous_http_contract_mismatch')
    return dict(result, recovery=previous, workerDeploymentPerformed=False)


def identity_projection(facts):
    require(facts.get('state') == 'uploaded_worker_identity_observed'
            and facts.get('worker') == core.WORKER and facts.get('hostname') == core.HOSTNAME
            and facts.get('workerExists') is True and facts.get('accountVerified') is True
            and facts.get('mutationsPerformed') is False, 'uploaded_identity_report_invalid')
    require(not facts.get('inspectionErrors') and not facts.get('scriptMetadataErrors') and not facts.get('errorCode'),
            'uploaded_identity_incomplete')
    deployment, version, settings = facts['deployment'], facts['version'], facts['settings']
    require(deployment['versions'] == [dict(version_id=version['id'], percentage=100)], 'single_pinned_active_version_required')
    require(facts['subdomain'] == dict(enabled=False, previews_enabled=False), 'workers_dev_or_previews_enabled')
    presence = dict(scriptHasAssets=facts.get('script', {}).get('has_assets'),
                    versionAssetsPresent=version['assets'].get('present') is True,
                    settingsAssetsPresent=settings['assets'].get('present') is True)
    require(presence['scriptHasAssets'] is True or presence['versionAssetsPresent'] or presence['settingsAssetsPresent'],
            'positive_assets_presence_required')
    etag = version['script']['etag']
    require(isinstance(etag, dict) and set(etag) == {'present', 'type', 'length', 'sha256', 'isEmpty'},
            'opaque_version_etag_representation_required')
    require(isinstance(facts.get('rawSettingsSha256'), str) and re.fullmatch('[0-9a-f]{64}', facts['rawSettingsSha256']),
            'raw_settings_digest_required')
    require(isinstance(facts.get('rawVersionSha256'), str) and re.fullmatch('[0-9a-f]{64}', facts['rawVersionSha256']),
            'raw_version_digest_required')
    assets = dict(version=version['assets'], settings=settings['assets'], rawSettingsSha256=facts['rawSettingsSha256'])
    return dict(deploymentId=deployment['id'], workerVersionId=version['id'], versionEtag=etag, assetPresence=presence,
                rawVersionSha256=facts['rawVersionSha256'],
                assets=assets, bindingTypes=version['bindingTypes'], settingsBindingTypes=settings['bindingTypes'],
                subdomain=facts['subdomain'])


def identity_hash(value):
    return core.sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def uploaded_identity(require_bound):
    """Pending until a separately reviewed exact GET-only inspector and pins exist.

    Worker version/assets metadata is continuity evidence, not a file-byte proof.
    core.public_http() supplies the separate end-to-end sealed-byte verification.
    """
    binding = read(Path(__file__).with_name('uploaded-worker-identity-binding.json'))
    require(binding.get('schemaVersion') == 1 and binding.get('state') == 'verified',
            'uploaded_worker_identity_evidence_pending')
    require(binding.get('priorPublishRunId') == PRIOR_RUN and binding.get('sourceRevision') == SOURCE
            and binding.get('worker') == core.WORKER and binding.get('hostname') == core.HOSTNAME,
            'uploaded_worker_identity_scope_mismatch')
    require(isinstance(binding.get('workerVersionId'), str) and re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', binding['workerVersionId'])
            and all(isinstance(binding.get(k), str) and re.fullmatch('[0-9a-f]{64}', binding[k])
                    for k in ['assetsMetadataSha256', 'inspectorSha256', 'providerReadonlySha256', 'evidenceSha256']),
            'uploaded_worker_identity_pins_required')
    # The inspector is supplied by the separate read-only identity task. The
    # shipped pending descriptor deliberately prevents reaching this import.
    module_path = Path(__file__).with_name('uploaded_identity.py')
    require(core.sha(core.gate.read(module_path)) == binding['inspectorSha256'], 'identity_inspector_digest_mismatch')
    require(core.sha(core.gate.read(Path(__file__).with_name('provider_readonly.py'))) == binding['providerReadonlySha256'],
            'identity_inventory_inspector_digest_mismatch')
    path = binding.get('evidencePath', '')
    require(isinstance(path, str) and path.startswith('docs/direct-seoul-seocho/') and '..' not in Path(path).parts
            and not Path(path).is_absolute() and '\\' not in path, 'identity_evidence_path_invalid')
    raw = core.gate.read(Path(__file__).resolve().parents[2] / path)
    require(core.sha(raw) == binding['evidenceSha256'], 'identity_evidence_digest_mismatch')
    evidence = json.loads(raw)
    expected = identity_projection(evidence)
    require(expected == binding.get('expectedIdentity') and expected['workerVersionId'] == binding['workerVersionId']
            and identity_hash(expected['assets']) == binding['assetsMetadataSha256'], 'identity_evidence_projection_mismatch')
    # This bounds the observed provider creation time to the actual successful
    # upload interval. It does not identify Git source bytes.
    created = datetime.fromisoformat(evidence['version']['metadata']['created_on'].replace('Z', '+00:00'))
    require(datetime(2026, 10, 14, 8, 2, 23, tzinfo=timezone.utc) <= created
            <= datetime(2026, 10, 14, 8, 2, 37, tzinfo=timezone.utc), 'version_outside_prior_upload_interval')
    import uploaded_identity as inspector
    account = os.environ.get('CLOUDFLARE_ACCOUNT_ID', '')
    statuses, domains = {}, []
    transport = inspector.make_transport(account, os.environ.get('CLOUDFLARE_API_TOKEN', ''), statuses)
    def capture(method, path, body=None):
        payload = transport(method, path, body)
        if path == '/accounts/' + account + '/workers/domains':
            domains.extend(inspector.base.single_page(payload))
        return payload
    try:
        partial = {}
        observed = inspector.inspect(account, capture, report=partial)
        current = identity_projection(observed)
        require(current == expected, 'current_uploaded_identity_mismatch')
        matches = [row for row in domains if row.get('hostname', '').lower() == core.HOSTNAME or row.get('service') == core.WORKER]
        if matches:
            require(len(matches) == 1, 'identity_domain_collision')
            row = matches[0]
            require(row.get('hostname', '').lower() == core.HOSTNAME and row.get('service') == core.WORKER
                    and row.get('environment') == 'production' and row.get('zone_name') == 'fwith.kr'
                    and ('enabled' not in row or row['enabled'] is True)
                    and ('previews_enabled' not in row or row['previews_enabled'] is False), 'identity_domain_configuration_mismatch')
        require(not require_bound or len(matches) == 1, 'identity_exact_domain_binding_required')
        return dict(state='uploaded_worker_identity_verified', worker=core.WORKER, hostname=core.HOSTNAME,
                    workerVersionId=current['workerVersionId'], assetsMetadataSha256=identity_hash(current['assets']),
                    identitySha256=identity_hash(current), hostnameBindingExists=bool(matches), collisionFree=True,
                    domainConfigurationChecked=True, subdomain=current['subdomain'], httpStatus=statuses,
                    mutationsPerformed=False, publicHttpVerified=False, uploadedContentMatchesExpectedSource=False)
    except Exception as error:
        core.save('completion-identity-failure.json', dict(state='blocked_or_failed', httpStatus=statuses,
                  error=sanitized_error(error), partialObservations=partial, mutationsPerformed=False))
        raise


def sanitized_error(error):
    name = type(error).__name__
    code = getattr(error, 'code', None)
    if code is None and (isinstance(error, ValueError) or name == 'Rejected'):
        code = str(error)
    code = code if isinstance(code, str) and re.fullmatch('[a-z0-9_]{1,100}', code) else None
    status = getattr(error, 'status', None)
    status = status if type(status) is int and 100 <= status <= 599 else None
    codes = getattr(error, 'cloudflare_codes', [])
    codes = [x for x in codes[:5] if type(x) is int and 0 <= x <= 1000000000] if isinstance(codes, (list, tuple)) else []
    return dict(type=name if name in {'TimeoutError', 'ValueError', 'PreflightError', 'Rejected', 'HTTPError', 'URLError'} else 'Exception',
                code=code, httpStatus=status, cloudflareCodes=codes)


def complete_binding(account, transport, attach, inspect=core.inspect_provider, identity=uploaded_identity):
    # stage=attach requires the exact Worker to exist but permits an unbound Worker.
    # Caller has already revalidated the fixed successful upload and absent target evidence.
    identity_before = identity(False)
    core.save('completion-identity-before.json', identity_before)
    before = inspect(account, transport, 'attach')
    core.save('completion-binding-before.json', before)
    requested = False
    uncertain = False
    attach_error = None
    if not before['hostnameBindingExists']:
        # Exclusive local marker prevents a second PUT within this first-attempt job.
        with Path('completion-attach-attempt.json').open('x', encoding='utf-8') as stream:
            json.dump(dict(state='attempting_once', hostname=core.HOSTNAME, worker=core.WORKER,
                           priorRunId=PRIOR_RUN), stream)
        requested = True
        try:
            attach(transport, account)
        except Exception as error:
            # No automatic retry. A GET readback may resolve an uncertain server result.
            attach_error = sanitized_error(error)
            uncertain = isinstance(error, TimeoutError) or attach_error['code'] == 'attach_result_uncertain'
        core.save('completion-attach-result.json', dict(requestAttempted=True, acknowledgementUncertain=uncertain,
                  error=attach_error, hostname=core.HOSTNAME, worker=core.WORKER, retryAttempted=False))
    else:
        core.save('completion-attach-result.json', dict(requestAttempted=False, alreadyBound=True,
                  hostname=core.HOSTNAME, worker=core.WORKER, retryAttempted=False))
    after = inspect(account, transport, 'readback')
    core.save('completion-binding-after.json', after)
    identity_after = identity(True)
    core.save('completion-identity-after.json', identity_after)
    require(identity_after['workerVersionId'] == identity_before['workerVersionId']
            and identity_after['assetsMetadataSha256'] == identity_before['assetsMetadataSha256'],
            'uploaded_identity_changed_during_binding')
    require(attach_error is None or uncertain, 'attach_explicitly_rejected')
    return dict(state='uploaded_release_binding_verified', hostname=core.HOSTNAME, worker=core.WORKER,
                priorRunId=PRIOR_RUN, requestAttempted=requested, acknowledgementUncertain=uncertain,
                workerDeploymentPerformed=False, publicHttpVerified=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['select', 'artifact', 'complete-binding', 'http', 'indexnow'])
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        authorize(os.environ, read(os.environ['GITHUB_EVENT_PATH']))
        fixed_release()
        if args.mode == 'select':
            result = dict(state='fixed_completion_selected', revision=SOURCE, priorRunId=PRIOR_RUN,
                          workerDeploymentPerformed=False)
        else:
            result = prepare()
            if args.mode == 'complete-binding':
                native, _ = core.helpers()
                account, transport = core.provider_transport()
                result = complete_binding(account, transport, native.attach)
            elif args.mode in ('http', 'indexnow'):
                identity = uploaded_identity(True)
                core.save('completion-identity-' + args.mode + '.json', identity)
                bound = read('completion-binding-after.json')
                require(bound.get('state') == 'binding_verified' and bound.get('hostname') == core.HOSTNAME
                        and bound.get('worker') == core.WORKER, 'completion_readback_required')
                result = core.public_http()
                if args.mode == 'indexnow':
                    require(read('completion-public-http.json').get('state') == 'public_release_verified',
                            'completion_http_report_required')
                    final_identity = uploaded_identity(True)
                    require(final_identity['workerVersionId'] == identity['workerVersionId']
                            and final_identity['assetsMetadataSha256'] == identity['assetsMetadataSha256'],
                            'uploaded_identity_changed_before_indexnow')
                    core.save('completion-identity-before-indexnow-post.json', final_identity)
                    result = core.indexnow()
        core.save(args.report, result)
        print(json.dumps({k: v for k, v in result.items() if k not in ('files', 'urls')}, sort_keys=True))
        return 0
    except Exception as error:
        code = str(error) if type(error) is ValueError and re.fullmatch('[a-z0-9_]+', str(error)) else type(error).__name__
        result = dict(state='blocked_or_failed', mode=args.mode, code=code, workerDeploymentPerformed=False)
        core.save(args.report, result)
        print(json.dumps(result))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
