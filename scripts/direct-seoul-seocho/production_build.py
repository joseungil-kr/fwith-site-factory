"""Fixed, credential-free Seocho production build gate. Control checkout only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import preview_build_only as frozen
import production_output as output

REPOSITORY = frozen.REPOSITORY
OWNER = frozen.OWNER
BRANCH = frozen.BRANCH
SOURCE_ROOT = frozen.SOURCE_ROOT
SUCCESSOR = '23bc1f2a42b0a6a01c41e8fe8a1f417f36122fa8'
HOSTNAME = 'seoul-seocho.fwith.kr'
ORIGIN = 'https://' + HOSTNAME
WORKER = 'seoul-seocho-flower-guide'
DIRECTORY = Path(__file__).resolve().parent
require, sha, read, git = frozen.require, frozen.sha, frozen.read, frozen.git


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def load():
    baseline = frozen.load_contract()
    contract_raw = read(DIRECTORY / 'production-source-contract.json')
    contract = json.loads(contract_raw)
    for key in ['schemaVersion', 'repository', 'sourceRoot', 'sourceBranch', 'frozenSourceRevision',
                'customerCopySha256', 'protectedFiles', 'sealedPins']:
        require(contract.get(key) == baseline[key], 'frozen_contract_changed')
    revision = contract.get('expectedSourceRevision', '')
    require(re.fullmatch('[0-9a-f]{40}', revision) and revision != SUCCESSOR, 'proof_successor_revision_required')
    proof = contract.get('proof', {})
    require(proof.get('origin') == ORIGIN and re.fullmatch('/[A-Za-z0-9-]{8,128}[.]txt', proof.get('path', ''))
            and re.fullmatch('[0-9a-f]{64}', proof.get('sha256', '')), 'exact_existing_proof_required')
    proof_source = 'public' + proof['path']
    paths = contract.get('expectedSourcePaths', [])
    require(len(paths) == len(set(paths)) and set(paths) == set(baseline['expectedSourcePaths']) | {proof_source}
            and proof_source not in baseline['expectedSourcePaths'], 'proof_only_source_addition_required')
    hashes = contract.get('sourceFilesSha256', {})
    require(set(hashes) == set(paths) and all(re.fullmatch('[0-9a-f]{64}', v) for v in hashes.values()), 'complete_source_hashes_required')
    require(hashes[proof_source] == proof['sha256'], 'source_proof_hash_mismatch')
    binding_raw = read(DIRECTORY / 'production-binding.json')
    binding = json.loads(binding_raw)
    required = dict(schemaVersion=1, state='approved', repository=REPOSITORY, sourceRoot=SOURCE_ROOT,
                    siteKey='seoul-seocho-flower-direct', hostname=HOSTNAME, origin=ORIGIN, worker=WORKER,
                    frozenSourceRevision=frozen.FROZEN_REVISION, customerCopySha256=frozen.COPY_SHA,
                    sourceRevision=revision, sourceContractSha256=sha(contract_raw), proof=proof,
                    sitemapRoutes=output.ROUTES, notFoundStatus=404, thinDirectoryRobots='noindex,follow')
    require(all(binding.get(k) == v for k, v in required.items()), 'binding_identity_or_source_contract_mismatch')
    require(binding.get('approvals') == {'hostBinding': True, 'indexNowProof': True, 'publication': True}, 'explicit_approvals_required')
    refs = binding.get('evidenceReferences', {})
    require(set(refs) == {'hostBinding', 'indexNowProof', 'publication'}, 'approval_references_required')
    for ref in refs.values():
        require(isinstance(ref, str) and re.fullmatch(r'https://github[.]com/joseungil-kr/fwith-site-factory/(?:blob/[0-9a-f]{40}/[^\s]+|issues/[1-9][0-9]*(?:#issuecomment-[0-9]+)?)', ref), 'auditable_approval_reference_required')
    return contract, binding, sha(binding_raw)


def authorize(contract, binding_sha, env, event, mode):
    require(mode in {'build', 'publish'}, 'invalid_mode')
    title = '[SEOCHO-PRODUCTION-' + mode.upper() + '] 20261014'
    require(env.get('GITHUB_REPOSITORY') == REPOSITORY and env.get('GITHUB_REF') == 'refs/heads/main'
            and env.get('GITHUB_ACTOR') == OWNER and env.get('GITHUB_RUN_ATTEMPT') == '1', 'owner_main_first_attempt_required')
    require(env.get('GITHUB_EVENT_NAME') == 'issues' and event.get('action') == 'opened', 'opened_issue_required')
    repo, issue = event.get('repository', {}), event.get('issue', {})
    require(repo.get('full_name') == REPOSITORY and repo.get('owner', {}).get('login') == OWNER
            and repo.get('owner', {}).get('type') == 'User', 'repository_owner_mismatch')
    require(issue.get('title') == title and issue.get('user', {}).get('login') == OWNER, 'issue_owner_or_title_mismatch')
    require(re.fullmatch('[0-9a-f]{40}', env.get('GITHUB_SHA', '')), 'control_sha_required')
    raw = issue.get('body')
    require(isinstance(raw, str) and len(raw) < 2048, 'request_body_invalid')
    body = json.loads(raw)
    require(type(body.get('schemaVersion')) is int and body == dict(schemaVersion=1, mode=mode,
            source_branch=BRANCH, source_revision=contract['expectedSourceRevision'],
            expected_control_revision=env['GITHUB_SHA'], binding_sha256=binding_sha), 'exact_request_binding_required')
    return dict(state='exact_production_request_selected', mode=mode, sourceBranch=BRANCH,
                sourceRevision=contract['expectedSourceRevision'], sourceRoot=SOURCE_ROOT, bindingSha256=binding_sha,
                controlRevision=env['GITHUB_SHA'], providerCredentialsUsed=False)


def environment(contract, binding_sha, env):
    require(env.get('SITE_RELEASE_MODE') == 'production' and env.get('SITE_INDEXABLE') == 'true'
            and env.get('SITE_URL') == ORIGIN and env.get('SITE_FACTORY_REVISION') == contract['expectedSourceRevision'], 'production_environment_mismatch')
    require(Path(env.get('SITE_RELEASE_BINDING_PATH', '')).resolve() == DIRECTORY / 'production-binding.json'
            and env.get('SITE_RELEASE_BINDING_SHA256') == binding_sha, 'pinned_control_binding_required')
    require(not env.get('CLOUDFLARE_API_TOKEN') and not env.get('CLOUDFLARE_ACCOUNT_ID'), 'provider_credentials_forbidden_during_build')


def verify_source(checkout, contract, phase):
    checkout = Path(checkout).resolve(); source = checkout / SOURCE_ROOT
    revision = contract['expectedSourceRevision']
    require(phase in {'prebuild', 'postbuild'}, 'phase_invalid')
    require(git(checkout, 'rev-parse', 'HEAD').decode().strip() == revision, 'checkout_revision_mismatch')
    require(git(checkout, 'rev-list', '--parents', '-n', '1', revision).decode().split() == [revision, SUCCESSOR], 'exact_proof_successor_parent_required')
    git(checkout, 'merge-base', '--is-ancestor', frozen.FROZEN_REVISION, revision)
    changed = [x.decode() for x in git(checkout, 'diff', '--name-only', '-z', SUCCESSOR, revision, '--').split(b'\0') if x]
    allowed = {'scripts/qa_release_output.py', 'scripts/release_mode.mjs', 'scripts/test_release_output.py', 'tests/release-mode.test.mjs', 'PRODUCTION_SUCCESSOR.md', 'public' + contract['proof']['path']}
    require(len(changed) == len(set(changed)) and set(changed) == {SOURCE_ROOT + '/' + name for name in allowed}, 'whole_repository_exact_release_successor_delta_required')
    tracked = [x.decode()[len(SOURCE_ROOT)+1:] for x in git(checkout, 'ls-files', '-z', '--', SOURCE_ROOT).split(b'\0') if x]
    require(len(tracked) == len(set(tracked)) and set(tracked) == set(contract['expectedSourcePaths']), 'source_inventory_mismatch')
    if phase == 'prebuild':
        require(not git(checkout, 'status', '--porcelain', '--untracked-files=all').strip(), 'source_checkout_not_clean')
    for name, digest in contract['sourceFilesSha256'].items():
        data = read(source / name)
        if phase == 'postbuild' and name == 'src/data/build-revision.json':
            require(json.loads(data) == {'revision': revision}, 'generated_revision_mismatch')
        else: require(sha(data) == digest, 'source_bytes_changed:' + name)
    frozen.preserved_inputs(source, contract, phase, revision)
    proof = read(source / ('public' + contract['proof']['path']))
    require(sha(proof) == contract['proof']['sha256'] and proof.decode('utf-8') == Path(contract['proof']['path']).stem + '\n', 'proof_body_mismatch')
    return dict(state='production_' + phase + '_source_verified', revision=revision, protectedFiles=946,
                sealedPins=98, exactSourceFiles=len(tracked), customerCopySha256=frozen.COPY_SHA,
                providerCredentialsUsed=False, remoteMutationsPerformed=False)


def inventory(root):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), 'artifact_root_invalid')
    files = {}
    for path in sorted(root.rglob('*')):
        mode = path.lstat().st_mode
        require(stat.S_ISDIR(mode) or stat.S_ISREG(mode), 'unsafe_artifact_type')
        rel = path.relative_to(root)
        require(not any(x.startswith('.') for x in rel.parts), 'hidden_artifact_forbidden')
        require(path.name not in {'_worker.js','_routes.json','_redirects','package.json','package-lock.json'}
                and not path.name.startswith('wrangler.'), 'executable_artifact_forbidden')
        if path.is_file(): files[rel.as_posix()] = sha(read(path))
    return files


def package(source, contract, binding_sha, env):
    dist = Path(source) / 'dist'
    facts = output.inspect_dist(dist, dict(mode='production', indexable=True, origin=ORIGIN,
                                revision=contract['expectedSourceRevision']), contract['proof'])
    files = inventory(dist)
    require(files == facts['files'], 'output_inventory_mismatch')
    release = Path('release'); release.mkdir()
    shutil.copytree(dist, release / 'dist')
    manifest = dict(schemaVersion=1, repository=REPOSITORY, sourceBranch=BRANCH, sourceRoot=SOURCE_ROOT,
                    revision=contract['expectedSourceRevision'], controlRevision=env['GITHUB_SHA'], runId=env['GITHUB_RUN_ID'],
                    origin=ORIGIN, worker=WORKER, indexable=True, bindingSha256=binding_sha,
                    sourceContractSha256=sha(read(DIRECTORY/'production-source-contract.json')), files=files)
    save(release/'release.json', manifest)
    facts.update(state='production_build_artifact_verified', sourceCommit=manifest['revision'],
                 buildControlSha=env['GITHUB_SHA'], buildRunId=env['GITHUB_RUN_ID'], bindingSha256=binding_sha,
                 outputFilesSha256=sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode()),
                 releaseManifestSha256=sha(read(release/'release.json')), nativeTestsPassed=True, nativeTestsMode='preview', productionBuildAndMutationQaPassed=True,
                 mobileAndDesktopPixelsVerified=False, publicationExecuted=False)
    return facts


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('mode', choices=['select','prebuild','postbuild'])
    parser.add_argument('--checkout'); parser.add_argument('--request-mode', choices=['build','publish'], default='build')
    parser.add_argument('--report', required=True); args=parser.parse_args()
    contract,binding,binding_sha=load()
    if args.mode == 'select':
        result=authorize(contract,binding_sha,os.environ,json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text()),args.request_mode)
        with open(os.environ['GITHUB_OUTPUT'],'a') as f:
            f.write('source_branch='+BRANCH+'\nsource_revision='+contract['expectedSourceRevision']+'\nbinding_sha256='+binding_sha+'\n')
    else:
        environment(contract,binding_sha,os.environ)
        result=verify_source(args.checkout,contract,args.mode)
        if args.mode == 'postbuild':
            require(os.environ.get('NATIVE_GATES_PASSED') == 'true', 'native_build_test_qa_gates_required')
            result.update(package(Path(args.checkout)/SOURCE_ROOT,contract,binding_sha,os.environ))
    save(args.report,result)
    print(json.dumps({k:v for k,v in result.items() if k != 'files'},sort_keys=True))

if __name__=='__main__':main()
