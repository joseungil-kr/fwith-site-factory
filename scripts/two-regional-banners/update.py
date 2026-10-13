#!/usr/bin/env python3
"""Two exact successors only. Reuse pinned helpers; never perform provider writes."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = 'docs/two-regional-banner-phone-20261013'
VERSION = 'two-phone-20261013'
REGIONS = frozenset({'seoul-geumcheon', 'seoul-yeongdeungpo'})
PLAN_SHA256 = '2b580875509fad5ccd9d70d7a989de2be8110a113d812a0cf8fcd2d6608c4ad0'
DEPENDENCIES_SHA256 = 'a99f00fe13e951f8e25fa24f00c6440cde947645111b79a2d9126ef64b3e184d'
CUSTOMER_PATHS = frozenset({'public/images/shared-banners/flower-message.webp',
    'public/images/shared-banners/flower-budget.webp', 'public/images/shared-banners/flower-consultation.webp',
    'src/components/SharedFlowerBanner.astro', 'src/data/shared-banner-manifest.json'})

def require(value, code):
    if not value:
        raise ValueError(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()

def checked_file(root, relative, digest, prefix=DIRECTORY + '/'):
    require(isinstance(relative, str) and relative.startswith(prefix)
            and '..' not in Path(relative).parts and not Path(relative).is_absolute(), 'two_evidence_path_invalid')
    path = root / relative
    require(path.is_file() and not any(p.is_symlink() for p in [path, *path.parents]), 'two_evidence_missing_or_symlink')
    require(re.fullmatch('[0-9a-f]{64}', digest or '') and sha(path.read_bytes()) == digest, 'two_evidence_digest_mismatch')
    return path.read_bytes()

def module(root, relative, name):
    spec = importlib.util.spec_from_file_location(name, root / relative)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

def dependencies(root):
    manifest = json.loads(checked_file(root, DIRECTORY + '/shared-dependencies.json', DEPENDENCIES_SHA256))
    for relative, digest in manifest['files'].items():
        checked_file(root, relative, digest, prefix=relative.split('/')[0] + '/')
    return manifest

def shared(root):
    dependencies(root)
    return module(root, 'scripts/shared-banners/verify_update.py', 'two_reviewed_shared_provider')

def plans(root):
    rows = json.loads(checked_file(root, DIRECTORY + '/source-plans.json', PLAN_SHA256))
    require(len(rows) == 2 and {row['region'] for row in rows} == REGIONS, 'two_exact_allowlist_required')
    for row in rows:
        require(set(row['customerChangedPaths']) == CUSTOMER_PATHS and len(row['customerChangedPaths']) == 5,
                'two_exact_five_customer_changes_required')
    return {row['region']: row for row in rows}

def catalog(root):
    path = root / DIRECTORY / 'targets.json'
    require(path.is_file() and not path.is_symlink(), 'two_catalog_missing')
    value = json.loads(path.read_text())
    require(value.get('version') == VERSION and set(value.get('targets', {})) == REGIONS, 'two_catalog_allowlist_mismatch')
    return value['targets']

def selected(root, region):
    require(region in REGIONS, 'unknown_two_update_target')
    revision = os.environ.get('REVISION', '')
    return bool(re.fullmatch('[0-9a-f]{40}', revision) and catalog(root)[region].get('revision') == revision)

def load(root, region, require_release=False):
    require(region in REGIONS, 'unknown_two_update_target')
    plan = plans(root)[region]
    target = catalog(root)[region]
    require(target.get('version') == VERSION, 'two_target_version_mismatch')
    require(target.get('previousRevision') == plan['parentCommit'], 'two_parent_revision_mismatch')
    require(re.fullmatch('[0-9a-f]{40}', target.get('revision') or '')
            and target['revision'] != plan['parentCommit'] and target['revision'] == os.environ.get('REVISION'),
            'two_saved_successor_revision_required')
    require(target.get('status') == 'independently_reviewed_source', 'two_source_review_required')
    review = json.loads(checked_file(root, target.get('sourceReview'), target.get('sourceReviewSha256')))
    require(review.get('verdict') == 'PASS_SOURCE_SAVE' and review.get('sourcePlanSha256') == PLAN_SHA256
            and review.get('sourceTrees') == {r: p['expectedTrees']['afterSource'] for r, p in plans(root).items()},
            'two_source_review_identity_mismatch')
    for proof in review.get('evidence', []):
        checked_file(root, proof.get('path'), proof.get('sha256'))
    require(bool(review.get('evidence')), 'two_independent_source_proof_required')
    readback = json.loads(checked_file(root, target.get('sourceReadback'), target.get('sourceReadbackSha256')))
    require(readback.get('sourceCommit') == target['revision'] and readback.get('parentCommit') == plan['parentCommit']
            and readback.get('allFilesMatch') is True
            and readback.get('sourceTree') == plan['expectedTrees']['afterSource']
            and readback.get('rootTree') == plan['expectedTrees']['afterRepositoryRoot'], 'two_remote_readback_identity_mismatch')
    expected = {p['path']: (p['mode'], p['sha256'], p['gitBlobSha']) for p in plan['files']}
    rows = readback.get('remoteFiles', [])
    require(len(rows) == len(expected) and len({p.get('path') for p in rows}) == len(expected)
            and {p.get('path'): (p.get('mode'), p.get('sha256'), p.get('gitBlob')) for p in rows} == expected
            and all(p.get('remoteBytesMatch') is True for p in rows), 'two_remote_whole_source_mismatch')
    require(readback.get('changedPaths') == [p['path'] for p in plan['changedFiles']], 'two_remote_delta_mismatch')
    changed_paths = {p['path'] for p in plan['changedFiles']}
    require(all(p.get('evidenceBasis') == ('fresh immutable fetch_file original bytes and full remote tree identity' if p['path'] in changed_paths else 'historical original bytes plus unchanged remote Git blob identity; exact full-tree reconstruction')
                for p in rows), 'two_remote_verification_basis_required')
    pub = module(root, f'scripts/direct-{region}/publish.py', 'two_fixed_' + region.replace('-', '_'))
    identity = {'repository': pub.REPOSITORY, 'branch': pub.BRANCH, 'root': pub.SOURCE_ROOT,
                'hostname': pub.HOSTNAME, 'worker': pub.WORKER}
    require(all(target.get(k) == v for k, v in identity.items()) and target['branch'] == plan['branch']
            and target['root'] == plan['root'] and target['hostname'] == plan['hostname'], 'two_fixed_identity_mismatch')
    require(os.environ.get('GITHUB_REPOSITORY') == pub.REPOSITORY, 'repository_mismatch')
    require(os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'update_rerun_forbidden')
    checked_file(root, f'scripts/direct-{region}/source-contract.json', plan['sourceContractSha256'], prefix='scripts/')
    dependencies(root)
    if require_release:
        release_review(root, target)
    return target, pub

def release_review(root, target):
    require(target.get('releaseReview') is not None, 'two_independent_actual_release_review_required')
    review = json.loads(checked_file(root, target.get('releaseReview'), target.get('releaseReviewSha256')))
    require(review.get('verdict') == 'PASS_PUBLIC_UPDATE' and review.get('sourceCommit') == target['revision']
            and review.get('previousRevision') == target['previousRevision'] and review.get('sourcePlanSha256') == PLAN_SHA256,
            'two_release_review_identity_mismatch')
    require(review.get('allRouteOutputVerified') is True and review.get('nativeTestsPassed') is True
            and review.get('mobileAndDesktopPixelsVerified') is True, 'two_actual_build_and_pixel_review_required')
    require(re.fullmatch('[0-9]+', str(review.get('buildRunId', '')))
            and re.fullmatch('[0-9]+', str(review.get('artifactId', '')))
            and re.fullmatch('[0-9a-f]{64}', review.get('outputFilesSha256', '')), 'two_actual_build_binding_required')
    proofs = review.get('evidence', [])
    require(len(proofs) >= 3 and {r.get('kind') for r in proofs} >= {'all-route-output', 'mobile-pixels', 'desktop-pixels'},
            'two_actual_release_proofs_missing')
    for proof in proofs:
        checked_file(root, proof.get('path'), proof.get('sha256'))
    return review

def authorize(root, region, for_public=True):
    plan = plans(root)[region]
    update = os.environ.get('EXISTING_UPDATE') == 'true'
    if not update:
        # The sole old baseline may still use the unmodified absent-target path.
        # No new, unknown, or reviewed successor can fall back to initial mode.
        require(os.environ.get('REVISION') == plan['parentCommit'], 'two_successor_requires_existing_update')
        return {'state': 'initial_absent_target_mode_only', 'existingUpdate': False}
    target, _ = load(root, region, require_release=for_public)
    return {'state': 'two_existing_update_authorized', 'revision': target['revision'], 'existingUpdate': True}

def source(root, region, checkout):
    authorize(root, region, for_public=False)
    target, pub = load(root, region)
    plan = plans(root)[region]
    checkout = Path(checkout)
    def git(*args):
        return subprocess.check_output(['git', '-C', str(checkout), *args], env={**os.environ,
            'GIT_NO_LAZY_FETCH': '1', 'GIT_OPTIONAL_LOCKS': '0'})
    require(git('rev-parse', 'HEAD').decode().strip() == target['revision'], 'two_checkout_revision_mismatch')
    require(git('rev-list', '--parents', '-n', '1', 'HEAD').decode().split() == [target['revision'], target['previousRevision']],
            'two_single_exact_parent_required')
    require(not git('status', '--porcelain', '--untracked-files=all').strip(), 'two_source_checkout_not_clean')
    require(git('rev-parse', 'HEAD^{tree}').decode().strip() == plan['expectedTrees']['afterRepositoryRoot']
            and git('rev-parse', 'HEAD:' + plan['root']).decode().strip() == plan['expectedTrees']['afterSource'],
            'two_exact_source_and_branch_trees_required')
    changed = git('diff', '--name-only', '-z', target['previousRevision'], target['revision'], '--').decode().rstrip('\0').split('\0')
    require(set(changed) == {plan['root'] + '/' + row['path'] for row in plan['changedFiles']}
            and len(changed) == len(plan['changedFiles']), 'two_git_delta_scope_mismatch')
    for row in plan['files']:
        path = checkout / plan['root'] / row['path']
        require(path.is_file() and not path.is_symlink() and sha(path.read_bytes()) == row['sha256'], 'two_source_bytes_mismatch')
        mode = '100755' if path.stat().st_mode & stat.S_IXUSR else '100644'
        require(mode == row['mode'], 'two_source_mode_mismatch')
    # Unlike Dongjak, generated build-revision.json MUST be absent at prebuild.
    report = pub.source_contract(checkout / plan['root'], phase='prebuild')
    return {'state': 'two_exact_source_successor_verified', 'revision': target['revision'], 'previousRevision': target['previousRevision'],
            'sourceTree': plan['expectedTrees']['afterSource'], 'files': report['files'], 'changedFiles': len(changed)}

def artifact(root, target, pub, for_public=False):
    manifest = json.loads(Path('release/release.json').read_text())
    require(manifest.get('revision') == target['revision'] and manifest.get('worker') == pub.WORKER
            and manifest.get('origin') == pub.ORIGIN, 'two_artifact_identity_mismatch')
    actual = pub.inventory(Path('release/dist'))
    require(manifest.get('files') == actual, 'two_artifact_files_mismatch')
    digest = sha(json_bytes(actual))
    if for_public:
        require(release_review(root, target)['outputFilesSha256'] == digest, 'two_rebuilt_output_differs_from_reviewed_build')
    dependencies(root)
    qa = module(root, 'scripts/shared-banners/qa_phone_banners.py', 'two_reviewed_phone_qa')
    os.environ['SITE_URL'] = pub.ORIGIN
    os.environ['SITE_INDEXABLE'] = 'true'
    report = qa.inspect(Path('release'), root / 'docs/shared-banner-phone-20261013/approved-assets.json')
    Path('release/shared-banner-qa.json').replace('two-banner-native-qa.json')
    return {'state': 'two_banner_artifact_verified', 'revision': target['revision'], 'outputFilesSha256': digest,
            'assetSha256': report['assetSha256'], 'files': report['files'], 'banners': report['banners'], 'customerHtml': report['customerHtml']}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['source', 'authorize-build', 'authorize-mutation', 'build-artifact', 'artifact', 'preflight', 'provider-after', 'public-assets'])
    parser.add_argument('--region', required=True, choices=sorted(REGIONS))
    parser.add_argument('--checkout')
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    if args.mode in ('authorize-build', 'authorize-mutation'):
        result = authorize(ROOT, args.region, for_public=args.mode == 'authorize-mutation')
    elif args.mode == 'source':
        result = source(ROOT, args.region, args.checkout)
    else:
        public = args.mode != 'build-artifact'
        authorize(ROOT, args.region, for_public=public)
        target, pub = load(ROOT, args.region, require_release=public)
        if args.mode in ('artifact', 'build-artifact'):
            result = artifact(ROOT, target, pub, for_public=public)
        elif args.mode == 'preflight':
            artifact(ROOT, target, pub, for_public=True)  # Checked again before any credentialed GET.
            result = shared(ROOT).preflight(target, pub)
        elif args.mode == 'provider-after':
            result = shared(ROOT).provider_after(target, pub)
        else:
            # Same pinned phone assets; no widening of the 33-site selector/catalog.
            result = shared(ROOT).public_assets({**target, 'version': 'phone-20261013'}, pub)
    Path(args.report).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n')

if __name__ == '__main__':
    main()
