#!/usr/bin/env python3
"""Bindings for the exact Namyangju whole-region initial release.

Reuses the frozen snapshot/batch pipeline. This module does not select regions,
write content, approve evidence, schedule work or create credentials.
"""
import hashlib
import json
import re
import copy
from pathlib import Path

from provision_goyang import INITIAL_REGIONS as ALL_INITIAL_REGIONS, INITIAL_SOURCE_PROFILES as ALL_INITIAL_SOURCE_PROFILES, target_contract

INITIAL_REGIONS = {"namyangju-flower-v2": ALL_INITIAL_REGIONS["namyangju-flower-v2"]}
INITIAL_SOURCE_PROFILES = {"namyangju-flower-v2": ALL_INITIAL_SOURCE_PROFILES["namyangju-flower-v2"]}


REVIEWED_BOOTSTRAP_REVISION = '4da8820325530ad85ada7ea1dc25884cfe6f9145'
REVIEWED_INITIAL = {'mode': 'whole-dong-initial', 'scopeKey': 'namyangju-flower-v2-dong-coverage-20261005', 'membershipSourceSha256': 'e488450c0c79bc07ffdc6041066e27532c01f01c2c5e204424729612098a0aba', 'coverageSha256': 'e43e68aaa5225eb51c1e6fa39a8ad3916f1020da6d1dc3a454c4a800cfc0a5bb', 'memberIdentitySha256': 'd198acd7f26214c0c5591e48f40ce545715c5819a9e1573c3ffb2814b6df2073', 'officialUnitCount': 20}

RULE_REVISION = '8986a1936615cd0d814b816db7816488e40bacc1'
INITIAL_FIELDS = ('mode', 'scopeKey', 'membershipSourceSha256', 'coverageSha256',
                  'memberIdentitySha256', 'officialUnitCount')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def initial_batch_identity(batch):
    site, scope = batch.get('siteKey'), batch.get('scopeKey')
    require(site in INITIAL_REGIONS and site in INITIAL_SOURCE_PROFILES,
            'Initial region has no reviewed source and identity profile')
    require(scope == 'namyangju-flower-v2-dong-coverage-20261005',
            'Initial batch needs its exact whole-region scope')
    require(batch.get('ruleRevision') == RULE_REVISION and
            batch.get('templateRevision') == INITIAL_SOURCE_PROFILES[site]['sourceRevision'],
            'Initial batch rule/template revision differs from reviewed profile')
    target = target_contract(site)
    return site, scope, {'repo': 'joseungil-kr/fwith-site-factory',
                        'branch': target['branch'], 'root': target['root']}


def validate_initial_binding(batch, target, git, base, final):
    """Bind geographic membership and unchanged runtime to actual bootstrap bytes."""
    site, scope, identity = initial_batch_identity(batch)
    require(target.get('initialLaunch') == REVIEWED_INITIAL, 'Initial membership differs from exact reviewed20 profile')
    contract = target_contract(site)
    profile = INITIAL_SOURCE_PROFILES[site]
    bootstrap = batch.get('bootstrapSourceSha')
    require(bootstrap == REVIEWED_BOOTSTRAP_REVISION, 'Initial bootstrap differs from exact reviewed input source')
    require(isinstance(bootstrap, str) and re.fullmatch(r'[0-9a-f]{40}', bootstrap)
            and git.ancestor(bootstrap, base), 'Initial baseline must descend from exact bootstrap revision')
    require(target.get('hubPolicy') == 'child-threshold-v1', 'Initial hub policy opt-in is missing')
    path = contract['provenancePath']
    raw = git.read(base, path)
    require(git.read(final, path) == git.read(bootstrap, path) == raw, 'Initial bootstrap provenance changed')
    provenance = json.loads(raw)
    from provision_goyang import encode, sha256
    unsigned = {key: value for key, value in provenance.items() if key != 'bootstrapId'}
    require(provenance.get('bootstrapId') == sha256(encode(unsigned)), 'Initial bootstrap digest changed')
    require(provenance.get('siteKey') == site and provenance.get('branch') == identity['branch']
            and provenance.get('root') == identity['root'] and provenance.get('customerPages') == 0,
            'Initial bootstrap identity is invalid')
    require(provenance.get('sourceRevision') == profile['sourceRevision']
            and provenance.get('sourceTree') == profile['sourceTree']
            and provenance.get('sourceTemplateRegistryKey') == profile['registryKey']
            and provenance.get('sourceRoot') == 'site-factory/templates/flower-local-v2-initial',
            'Initial bootstrap runtime profile changed')
    initial = provenance.get('initialScope', {})
    require(initial.get('mode') == 'whole-dong-initial' and initial.get('scopeKey') == scope
            and target.get('initialLaunch') == {key: initial.get(key) for key in INITIAL_FIELDS},
            'Registered initial membership differs from bootstrap provenance')
    require(initial.get('membershipSourceSha256') == batch.get('membershipSourceSha256')
            and re.fullmatch(r'[0-9a-f]{64}', initial.get('membershipSourceSha256', '')),
            'Initial membership evidence hash is missing or changed')
    members = initial.get('members')
    require(isinstance(members, list) and members and initial.get('officialUnitCount') == len(members),
            'Initial whole-region member inventory is missing')
    digest = hashlib.sha256(json.dumps(members, ensure_ascii=False, sort_keys=True,
                                      separators=(',', ':')).encode()).hexdigest()
    require(digest == initial.get('memberIdentitySha256'), 'Initial member identity digest changed')
    for member in members:
        slug = member.get('slug', '')
        require(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug)
                and member.get('unit_key', '').startswith(INITIAL_REGIONS[site] + '시/')
                and member.get('page_key') == site + '-region-' + slug
                and member.get('route') == '/regions/' + slug + '/'
                and member.get('intent_key') == site.split('-')[0] + '|flower-delivery|local-order|' + slug,
                'Initial bootstrap member identity is invalid')
    coverage = json.loads(git.read(base, identity['root'] + '/src/data/region-coverage.json'))
    candidate_raw = git.read(bootstrap, identity['root'] + '/src/data/region-coverage.json')
    require(hashlib.sha256(candidate_raw).hexdigest() == initial.get('coverageSha256'),
            'Original initial candidate coverage hash changed')
    candidate = json.loads(candidate_raw)
    promoted = copy.deepcopy(candidate)
    require(all(row.get('status') == 'candidate' for row in promoted['representatives']),
            'Initial bootstrap must start with candidate geography')
    for row in promoted['representatives']:
        row['status'] = 'approved'
    require(coverage == promoted, 'Initial units/aliases/ri/names/evidence changed beyond candidate approval')
    baseline_policy = json.loads(git.read(base, identity['root'] + '/src/data/region-policy.json'))
    expected_policy = json.loads(git.read(bootstrap, identity['root'] + '/src/data/region-policy.json'))
    expected_policy.update(enabled=True, state='approved-for-frozen-publisher',
                           visualBindings=baseline_policy.get('visualBindings'))
    require(isinstance(expected_policy['visualBindings'], list) and expected_policy['visualBindings']
            and baseline_policy == expected_policy, 'Initial policy changed outside reviewed enablement and visual bindings')
    from provision_goyang import validate_initial_coverage_shape
    validate_initial_coverage_shape(coverage)
    reps = coverage.get('representatives', [])
    require(len(reps) == len(members) and {r.get('pageKey') for r in reps} == {m['page_key'] for m in members},
            'Approved coverage omits or adds initial members')
    for member in members:
        rows = [r for r in reps if r.get('pageKey') == member['page_key']]
        require(len(rows) == 1, 'Initial representative identity is duplicated')
        row = rows[0]
        require(row.get('unitKeys') == [member['unit_key']] and all(row.get(key) == member[field]
                for key, field in [('slug', 'slug'), ('url', 'route'), ('intentKey', 'intent_key')]),
                'Approved representative changed initial unit/route/intent')
    source_manifest = provenance.get('sourceManifest', [])
    require(len(source_manifest) == profile['sourceCount'] and
            len({row.get('path') for row in source_manifest}) == profile['sourceCount'],
            'Initial runtime source manifest is incomplete')
    # All executable/assets/Truth/catalog source bytes remain the independently
    # reviewed template. Only the dedicated eight adaptations may differ.
    from provision_goyang import INITIAL_ADAPTATIONS
    require(set(provenance.get('adaptedFiles', [])) == INITIAL_ADAPTATIONS,
            'Initial adapter boundary changed')
    paths = {row['path'] for row in source_manifest}
    targets = provenance.get('targetManifest', [])
    require(len(targets) == len(paths) and {row.get('path') for row in targets} == paths,
            'Initial adapted bootstrap manifest is incomplete')
    require(git.paths(bootstrap, identity['root']) == paths, 'Initial bootstrap source inventory differs from reviewed profile')
    for row in targets:
        actual = git.read(bootstrap, identity['root'] + '/' + row['path'])
        require(hashlib.sha256(actual).hexdigest() == row.get('sha256'), 'Initial adapted bootstrap source bytes changed')
    extras = {'production-indexing.enabled'}
    if re.fullmatch(r'[a-f0-9]{32,128}', target.get('indexnowKey', '')):
        extras.add('public/' + target['indexnowKey'] + '.txt')
    for revision in (base, final):
        observed = git.paths(revision, identity['root'])
        require(paths <= observed <= paths | extras, 'Initial source has missing or unreviewed extra files')
        for name in ('wrangler.jsonc', 'wrangler.staging.jsonc'):
            require(git.read(revision, identity['root'] + '/' + name) ==
                    git.read(bootstrap, identity['root'] + '/' + name), 'Initial Wrangler configuration changed after bootstrap')
        config = json.loads(git.read(revision, identity['root'] + '/src/data/site-config.json'))
        original = json.loads(git.read(bootstrap, identity['root'] + '/src/data/site-config.json'))
        require(type(config.get('productionApproved')) is bool, 'Initial source approval must be boolean')
        original['productionApproved'] = config['productionApproved']
        require(config == original, 'Initial site configuration changed outside production approval')
    source_files = {}
    for row in source_manifest:
        relative = row['path']
        require(isinstance(relative, str) and not relative.startswith('/') and '..' not in relative.split('/'),
                'Unsafe initial runtime source path')
        original = git.read(profile['sourceRevision'], provenance['sourceRoot'] + '/' + relative)
        source_files[relative] = original
        require(hashlib.sha256(original).hexdigest() == row.get('sha256'), 'Initial source manifest hash changed')
        if relative not in INITIAL_ADAPTATIONS | {'src/data/pages.json'}:
            for revision in (base, final):
                require(git.read(revision, identity['root'] + '/' + relative) == original,
                        'Initial reviewed runtime/Truth/catalog asset changed: ' + relative)
    from provision_goyang import adapt_initial
    reconstructed = adapt_initial(source_files, site, initial, candidate_raw, profile['sourceRevision'])
    require(all(git.read(bootstrap, identity['root'] + '/' + path) == raw for path, raw in reconstructed.items()),
            'Initial bootstrap differs from the exact reviewed eight adaptations')
    return initial


def resolve(site, repository, revision, launch_key, scope_key):
    """Public gate is bound to an exact reviewed initial batch, never growth flags."""
    key = site.get('initialDeployment', {}).get('siteKey')
    require(site.get('initialLaunch') == REVIEWED_INITIAL, 'Initial membership differs from exact reviewed20 profile')
    require(key in INITIAL_REGIONS and key in INITIAL_SOURCE_PROFILES, 'Unknown initial deployment identity')
    target = target_contract(key)
    require(repository == 'joseungil-kr/fwith-site-factory' and site.get('repo') == repository,
            'Initial repository identity mismatch')
    expected = {'branch': target['branch'], 'root': target['root'], 'siteUrl': target['siteUrl'],
                'worker': target['productionWorker'], 'stagingWorker': target['stagingWorker'],
                'stagingUrl': target['stagingUrl'], 'stagingWranglerConfig': 'wrangler.staging.jsonc',
                'templateKey': 'flower-local-v2', 'snapshotRenderer': 'structured-json-v12',
                'hubPolicy': 'child-threshold-v1'}
    require(all(site.get(k) == v for k, v in expected.items()), 'Initial production target identity mismatch')
    require(site.get('growthPaused') is True and site.get('autoDeploySnapshots') is False
            and site.get('requireSnapshotApproval') is True and site.get('requireRevisionApproval') is True
            and site.get('stagingBuildIsolation') is True, 'Initial review/isolation policy changed')
    require(site.get('productionEnabled') is True and site.get('launchMode') == 'live',
            'Initial Production Launch Gate is closed')
    require(re.fullmatch(r'[0-9a-f]{40}', revision or '') and site.get('approvedRevision') == revision,
            'Initial exact revision lacks independent approval')
    require(re.fullmatch(r'https://github\.com/joseungil-kr/fwith-site-factory/issues/[1-9][0-9]*(?:#issuecomment-[0-9]+)?',
                         site.get('approvalEvidenceUrl', '')), 'Initial independent review evidence missing')
    require(re.fullmatch(re.escape(key) + r'-dong-coverage-[0-9]{8}', scope_key or '')
            and launch_key == key + '-initial-' + scope_key[-8:], 'Initial launch/scope identity mismatch')
    require(site.get('initialLaunch', {}).get('mode') == 'whole-dong-initial'
            and site['initialLaunch'].get('scopeKey') == scope_key, 'Initial scope differs from reviewed bootstrap')
    regional = {'enabled': True, 'scopeKey': scope_key, 'definitionFile': 'src/data/region-coverage.json',
                'policyFile': 'src/data/region-policy.json'}
    require(site.get('regionalService') == regional and site.get('administrativeCoverage') is None,
            'Initial exact regional runtime opt-in missing')
    config = site['initialDeployment']
    folder = 'site-factory/releases/' + launch_key
    require(config.get('enabled') is True and config.get('launchKey') == launch_key
            and config.get('scopeKey') == scope_key and config.get('batchPath') == folder + '/batch.json'
            and config.get('batchEvidencePath') == folder + '/evidence.json'
            and re.fullmatch(r'[0-9a-f]{40}', config.get('baselineSourceSha', '')),
            'Initial deployment batch binding mismatch')
    require(re.fullmatch(r'[0-9a-f]{40}', site.get('initialBootstrapRevision', ''))
            and config.get('bootstrapSourceSha') == site['initialBootstrapRevision'],
            'Initial production bootstrap revision is not pinned')
    for field in ('batchSha256', 'batchEvidenceSha256', 'productionManifestSha256', 'coverageSha256', 'regionPolicySha256'):
        require(re.fullmatch(r'[0-9a-f]{64}', config.get(field, '')), 'Missing exact initial digest: ' + field)
    require(re.fullmatch(r'[a-f0-9]{32,128}', site.get('indexnowKey', '')) and site.get('naverVerification') == '',
            'Initial public ownership proof is missing')
    return {'site_key': key, 'branch': target['branch'], 'root': target['root'],
            'site_url': target['siteUrl'], 'worker': target['productionWorker'], 'wrangler': 'wrangler.jsonc',
            'revision': revision, 'build_root': 'release-build', 'graph': 'scripts/qa_graph.mjs',
            'naver': '', 'indexnow': site['indexnowKey'], 'initial_coverage': 'true',
            'template_revision': INITIAL_SOURCE_PROFILES[key]['sourceRevision'],
            'launch_key': launch_key, 'scope_key': scope_key}


def resolve_preview(site, repository, key, revision, launch_key, scope_key):
    require(site.get('initialLaunch') == REVIEWED_INITIAL, 'Initial membership differs from exact reviewed20 profile')
    require(key in INITIAL_REGIONS and key in INITIAL_SOURCE_PROFILES, 'Unknown initial preview identity')
    target = target_contract(key)
    require(repository == site.get('repo') == 'joseungil-kr/fwith-site-factory'
            and all(site.get(k) == target[v] for k, v in [('branch', 'branch'), ('root', 'root'),
                ('siteUrl', 'siteUrl'), ('worker', 'productionWorker'), ('stagingWorker', 'stagingWorker'), ('stagingUrl', 'stagingUrl')]),
            'Initial preview identity mismatch')
    require(site.get('growthPaused') is True and site.get('autoDeploySnapshots') is False
            and site.get('requireSnapshotApproval') is True and site.get('requireRevisionApproval') is True
            and site.get('stagingBuildIsolation') is True and site.get('hubPolicy') == 'child-threshold-v1'
            and site.get('templateKey') == 'flower-local-v2' and site.get('snapshotRenderer') == 'structured-json-v12'
            and site.get('stagingWranglerConfig') == 'wrangler.staging.jsonc', 'Initial preview isolation policy mismatch')
    require(re.fullmatch(r'[0-9a-f]{40}', revision or '') and site.get('initialPreviewRevision') == revision
            and re.fullmatch(r'[0-9a-f]{64}', site.get('initialPreviewManifestSha256', '')),
            'Initial preview revision and manifest are not frozen for QA')
    require(all(re.fullmatch(r'[0-9a-f]{40}', site.get(field, '')) for field in
                ('initialBootstrapRevision', 'initialPreviewBaselineRevision')), 'Initial preview baseline/ bootstrap pins missing')
    require(site.get('initialLaunch', {}).get('mode') == 'whole-dong-initial'
            and site['initialLaunch'].get('scopeKey') == scope_key
            and re.fullmatch(re.escape(key) + r'-dong-coverage-[0-9]{8}', scope_key or '')
            and launch_key == key + '-initial-' + scope_key[-8:], 'Initial preview launch/scope mismatch')
    require(site.get('regionalService') == {'enabled': True, 'scopeKey': scope_key,
            'definitionFile': 'src/data/region-coverage.json', 'policyFile': 'src/data/region-policy.json'},
            'Initial preview regional opt-in missing')
    return {'site_key': key, 'root': target['root'], 'url': target['stagingUrl'], 'config': 'wrangler.staging.jsonc',
            'revision': revision, 'branch': target['branch'], 'isolated': 'true', 'build_root': 'preview-build',
            'staging_worker': target['stagingWorker'], 'initial_coverage': 'true',
            'template_revision': INITIAL_SOURCE_PROFILES[key]['sourceRevision'],
            'launch_key': launch_key, 'scope_key': scope_key}


def validate_preview_source(site, key, revision, root, workspace=None, *, git=None):
    from bucheon_production import regular_bytes, indexed
    scope = site['initialLaunch']['scopeKey']
    resolve_preview(site, site['repo'], key, revision, key + '-initial-' + scope[-8:], scope)
    from batch_barrier import GitEvidence
    require(workspace is not None or git is not None, 'Initial preview needs committed source evidence')
    evidence_git = git if git is not None else GitEvidence(workspace)
    binding = {'siteKey': key, 'scopeKey': scope, 'ruleRevision': RULE_REVISION,
               'templateRevision': INITIAL_SOURCE_PROFILES[key]['sourceRevision'],
               'membershipSourceSha256': site['initialLaunch']['membershipSourceSha256'],
               'bootstrapSourceSha': site['initialBootstrapRevision']}
    validate_initial_binding(binding, site, evidence_git, site['initialPreviewBaselineRevision'], revision)
    raw = regular_bytes(root, 'src/data/publish-manifest.json')
    require(hashlib.sha256(raw).hexdigest() == site['initialPreviewManifestSha256'], 'Initial preview frozen manifest changed')
    manifest = json.loads(raw)
    rows = indexed(manifest['pages'], 'pageKey')
    coverage = json.loads(regular_bytes(root, 'src/data/region-coverage.json'))
    policy = json.loads(regular_bytes(root, 'src/data/region-policy.json'))
    reps = indexed(coverage['representatives'], 'pageKey')
    require(manifest.get('siteKey') == coverage.get('siteKey') == policy.get('siteKey') == key
            and coverage.get('scopeKey') == policy.get('scopeKey') == scope
            and coverage.get('membershipSourceSha256') == site['initialLaunch']['membershipSourceSha256']
            and policy.get('enabled') is True, 'Initial preview source scope mismatch')
    count = site['initialLaunch']['officialUnitCount']
    require(type(count) is int and count > 0 and len(rows) == len(reps) == len(coverage['units']) == count
            and rows.keys() == reps.keys(), 'Initial preview must contain the complete whole-region membership')
    require(all(row.get('status') == 'approved' and row.get('approvalVerified') is True
                and row.get('category') == 'regions' and row.get('pageType') == 'regional-service'
                and row.get('scopeKey') == scope and reps[k].get('status') == 'approved'
                for k, row in rows.items()), 'Initial preview includes unapproved or out-of-scope snapshot')
    return {'state': 'initial_preview_source_validated', 'siteKey': key, 'revision': revision, 'details': count}


def verify_release(site, revision, root, control, workspace):
    """Consume actual committed Publisher lineage and exact independently reviewed QA."""
    from batch_barrier import check, GitEvidence
    from bucheon_production import regular_bytes
    config = site['initialDeployment']
    result = resolve(site, site['repo'], revision, config['launchKey'], config['scopeKey'])
    documents = []
    for path_key, hash_key in [('batchPath', 'batchSha256'), ('batchEvidencePath', 'batchEvidenceSha256')]:
        raw = regular_bytes(control, config[path_key])
        require(hashlib.sha256(raw).hexdigest() == config[hash_key], 'Initial trusted batch evidence bytes changed')
        documents.append(json.loads(raw))
    batch, evidence = documents
    preview = site['initialPreviewRevision']
    require(batch.get('contractType') == 'whole-region-initial' and batch.get('siteKey') == result['site_key']
            and batch.get('scopeKey') == config['scopeKey'] and batch.get('baselineSourceSha') == config['baselineSourceSha']
            and batch.get('bootstrapSourceSha') == config['bootstrapSourceSha']
            and evidence.get('finalSourceSha') == preview, 'Initial batch does not bind staged revision')
    git = GitEvidence(workspace)
    barrier = check(batch, evidence, git)
    require(barrier.get('state') == 'staging_complete' and barrier.get('finalSourceSha') == preview,
            'Initial complete independent staging barrier failed')
    source_root = result['root']
    require(git.ancestor(preview, revision), 'Initial production revision does not descend from staged revision')
    prior_paths, final_paths = git.paths(preview, source_root), git.paths(revision, source_root)
    ownership = 'public/' + site['indexnowKey'] + '.txt'
    require(final_paths == prior_paths | {'production-indexing.enabled', ownership},
            'Initial production source inventory changed beyond approval and ownership')
    config_path = source_root + '/src/data/site-config.json'
    before = json.loads(git.read(preview, config_path))
    after = json.loads(git.read(revision, config_path))
    require(before.get('productionApproved') is False and after.get('productionApproved') is True,
            'Initial production approval transition is invalid')
    before['productionApproved'] = True
    require(after == before, 'Initial production configuration changed beyond approval')
    require(all(git.read(preview, source_root + '/' + name) == git.read(revision, source_root + '/' + name)
                for name in prior_paths - {'src/data/site-config.json'}),
            'Initial staged content or runtime changed during production approval')
    for filename, field in [('publish-manifest.json', 'productionManifestSha256'),
                            ('region-coverage.json', 'coverageSha256'), ('region-policy.json', 'regionPolicySha256')]:
        raw = regular_bytes(root, 'src/data/' + filename)
        require(hashlib.sha256(raw).hexdigest() == config[field], 'Initial approved source changed: ' + filename)
    source_config = json.loads(regular_bytes(root, 'src/data/site-config.json'))
    require(source_config.get('siteKey') == result['site_key'] and source_config.get('productionApproved') is True
            and bool(regular_bytes(root, 'production-indexing.enabled')), 'Initial source indexing gate is closed')
    worker = json.loads(regular_bytes(root, 'wrangler.jsonc'))
    require(worker.get('name') == result['worker'] and worker.get('workers_dev') is True
            and worker.get('assets', {}).get('directory') == './dist/'
            and not any(key in worker for key in ('routes', 'route', 'triggers')), 'Initial fixed Worker boundary changed')
    key = site['indexnowKey']
    require(regular_bytes(root, 'public/' + key + '.txt').decode().strip() == key,
            'Initial public ownership file does not match registered key')
    architecture = json.loads(regular_bytes(root, 'src/data/architecture.json'))
    require(all(row.get('sitemapIndexable') is True for row in architecture['pages']),
            'Initial approved detail sitemap eligibility is stale')
    return {'pipelineState': 'initial_source_validated', 'siteKey': result['site_key'], 'revision': revision,
            'scopeKey': config['scopeKey'], 'batchBarrier': barrier}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--site-key', required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        site = json.loads(args.registry.read_text())['sites'][args.site_key]
        require(site.get('initialDeployment', {}).get('siteKey') == args.site_key, 'Initial requested identity mismatch')
        result = verify_release(site, args.revision, args.root, args.control, args.workspace)
    except (ValueError, KeyError, TypeError, OSError) as error:
        result = {'pipelineState': 'verification_blocked', 'siteKey': args.site_key, 'reason': str(error)}
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return int(result['pipelineState'] != 'initial_source_validated')


if __name__ == '__main__':
    raise SystemExit(main())
