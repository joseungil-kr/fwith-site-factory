"""Damyang source063e9 build-only controls. No provider access or publication.

Reuses the source-bound production validator byte-for-byte and the established
Damyang exact checkout/owner/first-attempt/request checks. Original first-publish
controls are not imported, rewritten or weakened to accept this successor.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import recovery_output as output

DIRECTORY = Path(__file__).resolve().parent
ROOT = 'site-factory/damyang-flower'
REPOSITORY = 'joseungil-kr/fwith-site-factory'
OWNER = 'joseungil-kr'
REVISION = '063e9eda9d33cb2f8b4dfd847bea966ff9443eb5'
TREE = '5069d911505b4588d354f71f109cd668c3896237'
ORIGINAL = '89c92dff3dca6456c1b0a3f7ee0587efe0361bed'
BRANCH = 'source/damyang-dedicated-proof-recovery-20261016'
TITLE = '[DAMYANG-RECOVERY-BUILD] 20261016 source063e9'
WORKFLOW = '.github/workflows/damyang-production-build-only.yml'
CONTROL_REVIEW_PATH = 'docs/direct-damyang-recovery/phase1-control-review-20261016.json'
# Closed phase1 inventory: only activation and the review itself are excluded.
REVIEWED_CONTROL_PATHS = frozenset(['.github/workflows/damyang-production-build-only.yml', '.github/workflows/damyang-production-publish.yml', 'docs/direct-damyang-recovery/prior-publication/artifact-check.json', 'docs/direct-damyang-recovery/prior-publication/binding-after.json', 'docs/direct-damyang-recovery/prior-publication/http-contract.json', 'docs/direct-damyang-recovery/prior-publication/public-http.json', 'docs/direct-damyang-recovery/prior-publication/release-manifest.json', 'docs/direct-damyang-recovery/prior-publication/selected-release.json', 'docs/direct-damyang/indexnow-key-recovery-authorization-20261016.json', 'scripts/direct-damyang-recovery/artifact-review-pending.json', 'scripts/direct-damyang-recovery/bounded-contract.json', 'scripts/direct-damyang-recovery/existing_provider.py', 'scripts/direct-damyang-recovery/managed_robots.py', 'scripts/direct-damyang-recovery/original-bounded-launch-assessment.json', 'scripts/direct-damyang-recovery/original-evidence.json', 'scripts/direct-damyang-recovery/original-production-authorization.json', 'scripts/direct-damyang-recovery/original-release-manifest.json', 'scripts/direct-damyang-recovery/original-release-review.json', 'scripts/direct-damyang-recovery/preview-equivalence.json', 'scripts/direct-damyang-recovery/previous_public.py', 'scripts/direct-damyang-recovery/private-source-manifest.json', 'scripts/direct-damyang-recovery/provider-baseline-policy.json', 'scripts/direct-damyang-recovery/provider_baseline.py', 'scripts/direct-damyang-recovery/recovery-authorization-proposed.json', 'scripts/direct-damyang-recovery/recovery_build.py', 'scripts/direct-damyang-recovery/recovery_output.py', 'scripts/direct-damyang-recovery/source-manifest.json', 'scripts/direct-damyang-recovery/test_damyang_baseline.py', 'scripts/direct-damyang-recovery/test_provider_baseline.py', 'scripts/direct-damyang-recovery/test_recovery_build.py'])
ORIGIN = 'https://damyang.fwith.kr'
WORKER = 'damyang-flower-guide'
GENERATED = {'candidate/node_modules', 'candidate/.astro', 'candidate/dist',
             'candidate/evidence', 'candidate/scripts/__pycache__',
             'release-adapter/scripts/__pycache__'}
output.EQUIVALENCE_PATH = DIRECTORY / 'preview-equivalence.json'
PINS = {
    'source-manifest.json': '43b576eb99c65f14bfeea698d4a9ec57a14fb442c25aaae7cc79e28dcbd2f8bb',
    'recovery_output.py': '559c00b6dbbbe85ef1dbd9a0bef026a75d8fe241839d8392d0cef59c1c52a6fd',
    'original-release-manifest.json': '8838618e13ec9b147f8674f8bf7f4e588a13424bd515c72033dd940f2efbc7af',
    'preview-equivalence.json': '2c2de80fb814b3b69c636cd952c8b84bf65fccfcb8aa0f53184ef280d481eb52',
    'bounded-contract.json': '9b7be12391a574527cd61958ebf61a87523f52df134ccd9e0e1ad769281b175d',
    'recovery-authorization-proposed.json': '31ea9f5c11fdca57b79f5a1eb00b4c7f49acca5fa394b068245fb4a884e23dd4',
    'original-production-authorization.json': '1fc4f2aa1435cad2429eaa39318f6a35b11d07ae5788f8082273f024c0ad6749',
    'original-release-review.json': '154483c5fd3a0f09114c2472bfca9e7045f2a928cb5b9b282fa518c17c558c75',
    'original-evidence.json': '41a63fe80413066f73672500cb915d4aa6cee24532219a28b60af80de69ff817',
    'original-bounded-launch-assessment.json': '34e28cbddeeb8e6f0ff39c317b04bae5b74ef52f9dd1adf8a11dc52310d861d0',
}

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate_json_key_forbidden')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda value: require(False, 'nonfinite_json_forbidden'))

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')

def read(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), 'regular_file_required')
    return path.read_bytes()

def regular_under(root, name):
    p = PurePosixPath(name)
    require(isinstance(name, str) and str(p) == name and not p.is_absolute() and
            all(part not in {'.', '..'} and not part.startswith('.') for part in p.parts)
            and '\\' not in name, 'safe_relative_path_required')
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), 'root_symlink_forbidden')
    cursor = root
    for part in p.parts:
        cursor = cursor / part
        require(not cursor.is_symlink(), 'path_symlink_forbidden')
    return read(cursor)

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.STDOUT)

def no_credentials(env):
    require(not any(value for name, value in env.items() if
                    re.search(r'(?:CLOUDFLARE|CF_API|AWS_|AZURE_|GOOGLE_APPLICATION_CREDENTIALS|PROVIDER)', name)),
            'provider_credentials_forbidden')

def owner_context(env):
    no_credentials(env)
    require(env.get('GITHUB_REPOSITORY') == REPOSITORY and env.get('GITHUB_REF') == 'refs/heads/main', 'owner_main_required')
    require(env.get('GITHUB_ACTOR') == OWNER and env.get('GITHUB_TRIGGERING_ACTOR') == OWNER and env.get('GITHUB_RUN_ATTEMPT') == '1', 'owner_first_attempt_required')
    require(env.get('GITHUB_EVENT_NAME') == 'issues' and re.fullmatch('[1-9][0-9]*', env.get('GITHUB_RUN_ID', '')), 'actual_issue_run_required')
    require(re.fullmatch('[0-9a-f]{40}', env.get('GITHUB_SHA', '')), 'actual_control_revision_required')

def source_contract():
    require(__debug__, 'optimized_python_forbidden')
    for name, digest in PINS.items():
        require(sha(read(DIRECTORY / name)) == digest, 'pinned_control_input_changed:' + name)
    rows = json.loads(read(DIRECTORY / 'source-manifest.json'))
    require(type(rows) is list and len(rows) == 81, 'exact_81_source_files_required')
    require(len({r['path'] for r in rows}) == 81, 'unique_source_paths_required')
    tree = {}
    for row in rows:
        cursor = tree
        parts = row['path'].split('/')
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = row['gitBlobSHA1']
    def tree_hash(node):
        payload = b''
        for name, value in sorted(node.items(), key=lambda x: (x[0] + ('/' if isinstance(x[1], dict) else '')).encode()):
            mode, digest = ('40000', tree_hash(value)) if isinstance(value, dict) else ('100644', value)
            payload += mode.encode() + b' ' + name.encode() + b'\0' + bytes.fromhex(digest)
        return hashlib.sha1(b'tree ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()
    require(tree_hash(tree) == TREE, 'source_manifest_git_tree_mismatch')
    return dict(schemaVersion=1, repository=REPOSITORY, sourceRoot=ROOT,
                sourceRevision=REVISION, sourceTree=TREE, sourceBranch=BRANCH,
                sourceFiles=81, privateFiles=65, adapterFiles=16,
                sourceManifestSha256=sha(read(DIRECTORY / 'source-manifest.json')),
                boundedContractSha256=sha(read(DIRECTORY / 'bounded-contract.json')))

def check_source_files(root, phase='prebuild'):
    """Pure byte inventory check, reusable in local fixtures without claiming Git provenance."""
    require(phase in {'prebuild', 'postbuild'}, 'phase_invalid')
    root = Path(root)
    rows = json.loads(read(DIRECTORY / 'source-manifest.json'))
    source_contract()
    expected = {row['path']: row for row in rows}
    for name, row in expected.items():
        raw = regular_under(root, name)
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        require(sha(raw) == row['sha256'] and len(raw) == row['bytes'] and blob == row['gitBlobSHA1'], 'source_bytes_changed:' + name)
    found = set()
    def visit(base):
        for item in base.iterdir():
            rel = item.relative_to(root).as_posix()
            require(not item.is_symlink(), 'source_symlink_forbidden:' + rel)
            if phase == 'postbuild' and rel in GENERATED:
                require(item.is_dir(), 'generated_path_not_directory')
                continue
            require(not item.name.startswith('.'), 'hidden_source_forbidden')
            if item.is_dir():
                visit(item)
            else:
                require(item.is_file(), 'source_nonregular_file')
                found.add(rel)
    visit(root)
    require(found == set(expected), 'exact_source_disk_inventory_required')
    require(read(root / 'release-adapter/scripts/damyang_release_output.py') == read(DIRECTORY / 'recovery_output.py'), 'source_control_validator_mismatch')
    for name in ['preview-equivalence.json', 'private-source-manifest.json', 'bounded-contract.json']:
        require(read(root / 'release-adapter/release' / name) == read(DIRECTORY / name), 'source_control_binding_mismatch:' + name)
    return expected

def trusted_control(env):
    owner_context(env)
    root = DIRECTORY.parents[1]
    require(git(root, 'rev-parse', 'HEAD').decode().strip() == env['GITHUB_SHA'], 'actual_control_checkout_required')
    scopes = ['scripts/direct-damyang-recovery', WORKFLOW,
              '.github/workflows/damyang-production-publish.yml',
              'docs/direct-damyang', 'docs/direct-damyang-recovery']
    require(not git(root, 'status', '--porcelain', '--untracked-files=all', '--', *scopes).strip(), 'control_checkout_changed')
    for scope in scopes:
        entries = [x for x in git(root, 'ls-tree', '-r', '-z', 'HEAD', '--', scope).split(b'\0') if x]
        require(entries, 'tracked_control_missing')
        for entry in entries:
            meta, name = entry.split(b'\t'); mode, kind, blob = meta.decode().split()
            require(mode == '100644' and kind == 'blob', 'control_entry_invalid')
            # .github is an explicitly tracked control path; all other paths use the common guard.
            path = root / name.decode()
            require(not any(p.is_symlink() for p in [path, *path.parents]), 'control_symlink_forbidden')
            raw = read(path)
            require(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == blob, 'control_bytes_changed')
    return root

def activation(root):
    a = strict_json(read(DIRECTORY / 'build-activation.json'))
    require(type(a) is dict and a.get('state') == 'INDEPENDENT_CONTROL_REVIEW_ACCEPTED', 'recovery_build_not_activated')
    required = {'schemaVersion', 'state', 'sourceRevision', 'authorizationRevisions',
                'independentControlReview', 'publicationReady', 'actualControlRevision',
                'actualBuildRunId', 'actualArtifactId', 'actualArtifactDigest'}
    require(set(a) == required and type(a['schemaVersion']) is int and a['schemaVersion'] == 1,
            'closed_build_activation_schema_required')
    require(a['sourceRevision'] == REVISION and a['publicationReady'] is False,
            'build_only_activation_required')
    require(all(a[key] is None for key in ('actualControlRevision', 'actualBuildRunId',
                                         'actualArtifactId', 'actualArtifactDigest')),
            'actual_identity_cannot_be_prepopulated')
    # Runtime control SHA comes from the immutable event and trusted checkout, not
    # a guessed self-referential commit value stored in this preparation file.
    d = a['independentControlReview']
    require(type(d) is dict and set(d) == {'path', 'sha256'} and
            d['path'] == CONTROL_REVIEW_PATH and type(d['sha256']) is str and
            re.fullmatch('[0-9a-f]{64}', d['sha256']), 'independent_control_review_required')
    raw = regular_under(root, d['path'])
    require(sha(raw) == d['sha256'], 'control_review_bytes_changed')
    review = strict_json(raw)
    require(type(review) is dict and set(review) == {'schemaVersion', 'verdict', 'sourceRevision', 'controlFiles'} and
            type(review['schemaVersion']) is int and review['schemaVersion'] == 1 and
            review['verdict'] == 'ACCEPT_BUILD_ONLY_RECOVERY_CONTROLS' and
            review['sourceRevision'] == REVISION, 'independent_control_review_verdict_required')
    rows = review['controlFiles']
    require(type(rows) is list and all(type(row) is dict and set(row) == {'path', 'sha256', 'bytes'} and
            type(row['path']) is str and type(row['sha256']) is str and
            re.fullmatch('[0-9a-f]{64}', row['sha256']) and type(row['bytes']) is int and row['bytes'] > 0
            for row in rows), 'reviewed_control_inventory_required')
    require(len(rows) == len(REVIEWED_CONTROL_PATHS) and
            {row['path'] for row in rows} == REVIEWED_CONTROL_PATHS,
            'exact_reviewed_control_scope_required')
    root = Path(root)
    for row in rows:
        # Paths came from the closed literal inventory, including explicit .github.
        path = root
        for part in row['path'].split('/'):
            path = path / part
            require(not path.is_symlink(), 'reviewed_path_unsafe')
        file_raw = read(path)
        require(len(file_raw) == row['bytes'] and sha(file_raw) == row['sha256'], 'reviewed_control_file_changed')
    auth = a['authorizationRevisions']
    require(type(auth) is dict and set(auth) == {'production', 'recovery'}, 'closed_authorization_revisions_required')
    for key, path in [('production', 'docs/direct-damyang/production-authorization-20261016.json'), ('recovery', 'docs/direct-damyang/indexnow-key-recovery-authorization-20261016.json')]:
        rev = auth[key]
        require(type(rev) is str and re.fullmatch('[0-9a-f]{40}', rev), 'actual_authorization_revision_required')
        require(git(root, 'show', rev + ':' + path) == read(root / path), 'authorization_revision_bytes_mismatch')
        git(root, 'merge-base', '--is-ancestor', rev, 'HEAD')
    require(read(root / 'docs/direct-damyang/indexnow-key-recovery-authorization-20261016.json') == read(DIRECTORY / 'recovery-authorization-proposed.json'), 'exact_recovery_authorization_required')
    require(read(root / 'docs/direct-damyang/production-authorization-20261016.json') == read(DIRECTORY / 'original-production-authorization.json'), 'exact_original_authorization_required')
    return a

def binding(a):
    c = json.loads(read(DIRECTORY / 'bounded-contract.json'))
    return dict(schemaVersion=1, state='approved', repository=REPOSITORY, sourceRoot=ROOT,
                siteKey='damyang-flower-direct', hostname='damyang.fwith.kr', origin=ORIGIN,
                worker=WORKER, frozenInputSha256=c['frozenInputsManifestSHA256'],
                frozenPrivateTreeSha256=c['frozenSource']['frozenTreeSHA256'],
                sourceRevision=REVISION, proof=output.PROOF, retainedProofs=output.RETAINED_PROOFS,
                proofRecoveryChain=output.PROOF_RECOVERY_CHAIN, sitemapRoutes=['/'], htmlFiles=2,
                notFoundRobots='noindex,follow', notFoundStatus=404, publicHttpVerified=False,
                indexNowSubmitted=False, boundedContractSha256=sha(read(DIRECTORY / 'bounded-contract.json')),
                coreHubLaunchStatus='NOT_ASSESSED', fullLaunchStatus='NOT_ASSESSED',
                approvals=dict(publication=True, hostBinding=True, indexNowProof=True, indexNowProofReplacement=True),
                authorizationEvidence=f"https://github.com/{REPOSITORY}/blob/{a['authorizationRevisions']['production']}/docs/direct-damyang/production-authorization-20261016.json",
                recoveryAuthorizationEvidence=f"https://github.com/{REPOSITORY}/blob/{a['authorizationRevisions']['recovery']}/docs/direct-damyang/indexnow-key-recovery-authorization-20261016.json",
                sourceContractSha256=sha(canonical(source_contract())))

def request(env, event, binding_sha):
    owner_context(env)
    require(event.get('action') == 'opened', 'opened_issue_required')
    repo, issue = event.get('repository', {}), event.get('issue', {})
    require(repo.get('full_name') == REPOSITORY and repo.get('owner', {}).get('login') == OWNER and repo.get('owner', {}).get('type') == 'User', 'repository_owner_mismatch')
    require(issue.get('title') == TITLE and issue.get('user', {}).get('login') == OWNER, 'exact_recovery_issue_required')
    raw = issue.get('body')
    require(type(raw) is str and len(raw) < 2048, 'exact_request_body_required')
    expected = dict(schemaVersion=1, mode='damyang-proof-recovery-build-only', source_branch=BRANCH,
                    source_revision=REVISION, source_tree=TREE, expected_control_revision=env['GITHUB_SHA'],
                    source_manifest_sha256=source_contract()['sourceManifestSha256'], binding_sha256=binding_sha)
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate_request_key_forbidden')
            result[key] = value
        return result
    require(canonical(json.loads(raw, object_pairs_hook=unique_pairs)) == canonical(expected), 'closed_recovery_request_mismatch')
    return expected

def source(checkout, phase, env):
    root = trusted_control(env); a = activation(root)
    bound_path = Path(env['GITHUB_WORKSPACE']) / 'recovery-binding/production-binding.json'
    require(not bound_path.parent.is_symlink() and read(bound_path) == canonical(binding(a)), 'exact_runtime_control_binding_required')
    checkout = Path(checkout)
    require(git(checkout, 'rev-parse', 'HEAD').decode().strip() == REVISION, 'source_revision_mismatch')
    require(git(checkout, 'rev-parse', 'HEAD:' + ROOT).decode().strip() == TREE, 'source_tree_mismatch')
    require(not git(checkout, 'diff', '--name-only', 'HEAD', '--', ROOT).strip(), 'tracked_source_delta')
    if phase == 'prebuild':
        require(not git(checkout, 'status', '--porcelain', '--untracked-files=all').strip(), 'source_checkout_not_clean')
    expected = check_source_files(checkout / ROOT, phase)
    entries = [x for x in git(checkout, 'ls-tree', '-r', '-z', 'HEAD', '--', ROOT).split(b'\0') if x]
    actual = {}
    for entry in entries:
        meta, name = entry.split(b'\t'); mode, kind, blob = meta.decode().split()
        require(mode == '100644' and kind == 'blob', 'source_entry_invalid')
        actual[name.decode().removeprefix(ROOT + '/')] = blob
    require(actual == {n: r['gitBlobSHA1'] for n, r in expected.items()}, 'exact_git_source_inventory_required')
    return a

def inspect_dist(dist):
    source_contract()
    result = output.inspect_dist(dist, dict(mode='production', indexable=True, origin=ORIGIN, revision=REVISION))
    require(len(result['files']) == 17, 'exact_17_recovery_output_required')
    original = json.loads(read(DIRECTORY / 'original-release-manifest.json'))
    require(original['revision'] == ORIGINAL and len(original['files']) == 16, 'exact_original_16_baseline_required')
    for name, digest in original['files'].items():
        if not name.endswith('.html'):
            require(result['files'].get(name) == digest, 'original_nonhtml_changed:' + name)
    require(set(result['files']) - set(original['files']) == {Path(output.PROOF['path']).name}, 'only_dedicated_proof_added')
    for name in ['index.html', '404.html']:
        raw = read(Path(dist) / name)
        marker = ('<meta name="site-factory-revision" content="' + REVISION + '">').encode()
        prior = ('<meta name="site-factory-revision" content="' + ORIGINAL + '">').encode()
        require(raw.count(marker) == 1 and sha(raw.replace(marker, prior)) == original['files'][name], 'original_html_revision_only_required')
    payload = output.indexnow_payload(result['sitemapUrls'])
    require(payload == dict(host='damyang.fwith.kr', key=Path(output.PROOF['path']).stem,
                            keyLocation=ORIGIN + output.PROOF['path'], urlList=[ORIGIN + '/']), 'active_only_payload_required')
    rows = []
    for name, digest in sorted(result['files'].items()):
        if name == '_headers':
            continue
        path = '/' if name == 'index.html' else ('/.damyang-release-missing-' + REVISION + '/' if name == '404.html' else '/' + name)
        rows.append(dict(file=name, path=path, expectedStatus=404 if name == '404.html' else 200, sha256=digest))
    require(len(rows) == 16 and sum(r['expectedStatus'] == 200 for r in rows) == 15 and sum(r['expectedStatus'] == 404 for r in rows) == 1, 'exact_public_16_plan_required')
    result.update(sourceRevision=REVISION, sourceTree=TREE, httpPlan=rows, actualPublicHTTPRequests=0,
                  originalNonHTMLExact=14, originalHTMLRevisionOnly=2, inheritedBodyByteEquality=2,
                  activeOnlyPayloadSha256=sha(canonical(payload)), publicationReady=False,
                  productionRunnerVerified=False, independentArtifactReviewRequired=True,
                  newLiveBrowserObserved=False, providerObserved=False, indexNowSubmitted=False)
    prior_review = json.loads(read(DIRECTORY / 'original-release-review.json'))
    require(prior_review['artifactId'] == '12027923402' and prior_review['buildRunId'] == '38858258621' and
            prior_review['sourceCommit'] == ORIGINAL and prior_review['verdict'] == 'PASS_DAMYANG_PRODUCTION_ARTIFACT_REVIEW', 'original_pixel_review_identity_required')
    result['browserInheritance'] = dict(originalRunId='38858258621', originalArtifactId='12027923402',
        originalArtifactDigest='sha256:568fe460b03f9c3c0b03bde435f6921a75126f0add8e272316af71ec1fa43d7b',
        reviewedViewports=[320, 390, 1280], scope='prior runner-loopback rendered evidence plus exact body/CSS/image bytes; no fresh live observation',
        priorReviewSHA256=PINS['original-release-review.json'], independentSuccessorInheritanceAccepted=False)
    return result

def artifact_name(env):
    owner_context(env)
    return 'damyang-proof-recovery-build-' + env['GITHUB_RUN_ID'] + '-' + env['GITHUB_SHA']

def package(checkout, destination, env):
    a = source(checkout, 'postbuild', env)
    require(env.get('NATIVE_GATES_PASSED') == 'true', 'native_preview_and_recovery_gates_required')
    dist = Path(checkout) / ROOT / 'candidate/dist'
    result = inspect_dist(dist)
    destination = Path(destination)
    require(not destination.exists(), 'new_artifact_directory_required')
    destination.mkdir(parents=True)
    shutil.copytree(dist, destination / 'dist')
    manifest = dict(schemaVersion=1, mode='damyang-proof-recovery-build-only', repository=REPOSITORY,
                    sourceRevision=REVISION, sourceTree=TREE, sourceBranch=BRANCH, sourceRoot=ROOT,
                    controlRevision=env['GITHUB_SHA'], runId=env['GITHUB_RUN_ID'], runAttempt=1,
                    artifactName=artifact_name(env), sourceContract=source_contract(),
                    bindingSha256=sha(canonical(binding(a))), files=result['files'],
                    publicationReady=False, independentArtifactReviewRequired=True)
    save(destination / 'release.json', manifest)
    save(destination / 'output-verification.json', result)
    return manifest

def verify_artifact_identity(run, artifact, archive_bytes, manifest):
    """Validate independently fetched API metadata plus downloaded ZIP digest.
    Pure comparison only: callers must obtain API evidence independently. Tests
    can validate synthetic envelopes but cannot turn them into execution approval.
    """
    require(run.get('repository', {}).get('full_name') == REPOSITORY and run.get('head_branch') == 'main', 'artifact_repo_main_required')
    require(re.fullmatch('[0-9a-f]{40}', manifest.get('controlRevision', '')) and re.fullmatch('[1-9][0-9]*', manifest.get('runId', '')), 'actual_artifact_control_run_required')
    require(manifest.get('artifactName') == 'damyang-proof-recovery-build-' + manifest['runId'] + '-' + manifest['controlRevision'], 'exact_recovery_artifact_name_required')
    require(run.get('head_sha') == manifest['controlRevision'] and str(run.get('id')) == manifest['runId'], 'artifact_run_control_mismatch')
    require(run.get('event') == 'issues' and type(run.get('run_attempt')) is int and run['run_attempt'] == 1, 'artifact_first_issue_run_required')
    require(run.get('actor', {}).get('login') == OWNER and run.get('triggering_actor', {}).get('login') == OWNER, 'artifact_owner_required')
    require(run.get('path') == WORKFLOW and run.get('status') == 'completed' and run.get('conclusion') == 'success', 'successful_actual_build_run_required')
    require(type(artifact.get('id')) is int and artifact['id'] > 0 and artifact.get('expired') is False, 'actual_nonexpired_artifact_required')
    require(artifact.get('name') == manifest['artifactName'] and artifact.get('digest') == 'sha256:' + sha(archive_bytes), 'artifact_name_digest_mismatch')
    require(artifact.get('workflow_run', {}).get('id') == run['id'] and artifact['workflow_run'].get('head_sha') == manifest['controlRevision'], 'artifact_run_binding_required')
    require(manifest.get('sourceRevision') == REVISION and manifest.get('sourceTree') == TREE and manifest.get('runAttempt') == 1 and manifest.get('sourceContract') == source_contract(), 'artifact_source_binding_required')
    require(manifest.get('publicationReady') is False and manifest.get('independentArtifactReviewRequired') is True, 'artifact_cannot_self_approve')
    return dict(state='ARTIFACT_IDENTITY_STRUCTURALLY_VERIFIED_REVIEW_STILL_REQUIRED', artifactId=artifact['id'], archiveSha256=sha(archive_bytes), publicationReady=False)

def verify_independent_review(review_raw, accepted_digest, manifest, identity, output_report, dist=None):
    """An immutable, separately accepted review must bind the actual downloaded artifact.

    A caller must pin accepted_digest through a separately reviewed activation;
    an author-generated result, empty descriptor or fixture is never acceptance.
    This only closes build review. Existing-host/provider/public gates stay open.
    """
    require(type(accepted_digest) is str and re.fullmatch('[0-9a-f]{64}', accepted_digest), 'accepted_independent_review_digest_required')
    require(sha(review_raw) == accepted_digest, 'accepted_review_bytes_mismatch')
    review = strict_json(review_raw)
    expected = dict(schemaVersion=1, verdict='ACCEPT_SOURCE063E9_BUILD_ARTIFACT_ONLY', fixture=False,
                    sourceRevision=REVISION, sourceTree=TREE, controlRevision=manifest['controlRevision'],
                    runId=manifest['runId'], runAttempt=1, artifactId=identity['artifactId'],
                    artifactDigest='sha256:'+identity['archiveSha256'],
                    releaseManifestCanonicalSha256=sha(canonical(manifest)),
                    outputVerificationCanonicalSha256=sha(canonical(output_report)),
                    exactSourceFiles=81, exactReleaseFiles=17, expectedHTTPPaths=16,
                    actualPublicHTTPRequests=0, inheritedBrowserEvidenceAccepted=True,
                    originalBrowserRunId='38858258621', originalBrowserArtifactId='12027923402',
                    originalBrowserArtifactDigest='sha256:568fe460b03f9c3c0b03bde435f6921a75126f0add8e272316af71ec1fa43d7b',
                    originalHTMLBodiesExact=2, originalNonHTMLFilesExact=14,
                    newLiveBrowserObserved=False, providerBaselineAccepted=False, publicationReady=False)
    require(canonical(review) == canonical(expected), 'exact_independent_artifact_review_required')
    require(dist is not None, 'actual_downloaded_dist_required')
    require(canonical(inspect_dist(dist)) == canonical(output_report), 'independent_downloaded_output_recheck_required')
    require(output_report.get('sourceRevision') == REVISION and len(output_report.get('files',{})) == 17 and output_report.get('files') == manifest.get('files'), 'review_output_manifest_mismatch')
    return dict(buildArtifactReviewAccepted=True, providerBaselineAccepted=False,
                publicHTTPVerified=False, publicationReady=False)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['select', 'prebuild', 'postbuild'])
    p.add_argument('--checkout'); p.add_argument('--report', required=True)
    p.add_argument('--package', default='release-recovery')
    args = p.parse_args(); env = os.environ
    root = trusted_control(env); a = activation(root)
    if args.phase == 'select':
        b = binding(a); digest = sha(canonical(b))
        result = request(env, strict_json(read(env['GITHUB_EVENT_PATH'])), digest)
        # Binding bytes use canonical serialization so the closed request digest is exact.
        destination = Path(env['GITHUB_WORKSPACE']) / 'recovery-binding/production-binding.json'
        destination.parent.mkdir(exist_ok=False)
        destination.write_bytes(canonical(b))
        with open(env['GITHUB_OUTPUT'], 'a') as f:
            f.write('source_revision=' + REVISION + '\nbinding_sha256=' + digest + '\n')
    elif args.phase == 'prebuild':
        source(args.checkout, 'prebuild', env)
        result = dict(state='SOURCE81_VERIFIED', sourceRevision=REVISION, sourceTree=TREE, publicationReady=False)
    else:
        result = package(args.checkout, args.package, env)
    save(args.report, result)

if __name__ == '__main__':
    main()
