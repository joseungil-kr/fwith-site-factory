#!/usr/bin/env python3
"""Exact Bucheon initial-coverage release contract. Missing evidence fails closed."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

SITE = 'bucheon-flower-v2'
SCOPE = SITE + '-dong-coverage-20261004'
REGIONAL_SERVICE = {'enabled': True, 'scopeKey': SCOPE,
    'definitionFile': 'src/data/region-coverage.json', 'policyFile': 'src/data/region-policy.json'}
ORIGIN = 'https://bucheon.fwith.kr'
WORKER = 'bucheon-flower-prod-disabled'
BASELINE = 'ed5d30763d38ae1580974b1d377c07d4927dcdeb'
MEMBERSHIP_SHA256 = '71d937f74782ed7628122937008f6da698b393ea29c031a642dae28a7654a8a3'
RELEASE_DIR = 'site-factory/releases/bucheon-dong-coverage-20261004'
IDENTITY = {'repo': 'joseungil-kr/fwith-site-factory', 'branch': 'site-factory-bucheon-v2',
    'root': 'site-factory/bucheon-flower', 'siteUrl': ORIGIN, 'worker': WORKER,
    'templateKey': 'flower-local-v2', 'snapshotRenderer': 'structured-json-v12',
    'stagingWorker': 'bucheon-flower-guide-qa',
    'stagingUrl': 'https://bucheon-flower-guide-qa.joseungil.workers.dev',
    'stagingWranglerConfig': 'wrangler.staging.jsonc'}
DIGEST_FIELDS = ('productionManifestSha256', 'coverageSha256', 'regionPolicySha256',
                 'batchSha256', 'batchEvidenceSha256')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def regular_bytes(root, relative):
    root = Path(root)
    current = root
    require(not current.is_symlink(), 'Symlink root is not release evidence')
    for part in Path(relative).parts:
        require(part not in ('..', '/'), 'Unsafe release evidence path')
        current = current / part
        require(not current.is_symlink(), 'Symlink is not regular release evidence: ' + str(relative))
    require(current.is_file(), 'Missing regular release evidence: ' + str(relative))
    return current.read_bytes()


def indexed(rows, key):
    require(isinstance(rows, list), 'Expected list: ' + key)
    result = {}
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get(key), str) and row[key]
                and row[key] not in result, 'Duplicate or missing: ' + key)
        result[row[key]] = row
    return result


def resolve(site, repository, revision, launch_key, scope_key):
    require(repository == IDENTITY['repo'] and all(site.get(k) == v for k, v in IDENTITY.items()),
            'Bucheon registered identity mismatch')
    require(site.get('growthPaused') is True and site.get('autoDeploySnapshots') is False
            and site.get('requireRevisionApproval') is True and site.get('requireSnapshotApproval') is True
            and site.get('stagingBuildIsolation') is True, 'Bucheon review/isolation policy mismatch')
    require(site.get('regionalService') == REGIONAL_SERVICE
            and site['regionalService'].get('enabled') is True, 'Bucheon region opt-in missing')
    from indexnow_ownership import key_allowed
    require(key_allowed(site) and site.get('naverVerification') == '', 'Bucheon ownership settings changed')
    require(launch_key == scope_key == SCOPE, 'Bucheon exact initial-coverage scope required')
    require(site.get('productionEnabled') is True and site.get('launchMode') == 'live',
            'Production Launch Gate is closed')
    require(re.fullmatch(r'[0-9a-f]{40}', revision or '') is not None and site.get('approvedRevision') == revision,
            'Bucheon exact revision lacks approval')
    require(re.fullmatch(r'https://github\.com/joseungil-kr/fwith-site-factory/(?:issues|pull|commit)/[^\s?#]+(?:#[^\s]+)?',
                         site.get('approvalEvidenceUrl', '')) is not None, 'Bucheon independent review evidence missing')
    config = site.get('coverageDeployment', {})
    wanted = {'enabled': True, 'launchKey': SCOPE, 'scopeKey': SCOPE, 'canonicalOrigin': ORIGIN,
        'worker': WORKER, 'wranglerConfig': 'wrangler.jsonc', 'baselineSourceSha': BASELINE,
        'membershipSha256': MEMBERSHIP_SHA256, 'batchPath': RELEASE_DIR + '/batch.json',
        'batchEvidencePath': RELEASE_DIR + '/evidence.json'}
    require(config.get('enabled') is True and all(config.get(k) == v for k, v in wanted.items()), 'Bucheon deployment binding mismatch')
    require(all(re.fullmatch(r'[0-9a-f]{64}', config.get(k, '')) for k in DIGEST_FIELDS),
            'Bucheon reviewed source/barrier digests missing')
    return {'site_key': SITE, 'branch': IDENTITY['branch'], 'root': IDENTITY['root'], 'site_url': ORIGIN,
        'worker': WORKER, 'wrangler': 'wrangler.jsonc', 'revision': revision, 'build_root': 'release-build',
        'graph': 'scripts/qa_graph.mjs', 'naver': '', 'indexnow': site.get('indexnowKey', ''), 'bucheon_coverage': 'true',
        'launch_key': launch_key, 'scope_key': scope_key}


def validate_barrier_inputs(control, site, revision):
    config = site['coverageDeployment']
    docs = []
    for path_key, hash_key in [('batchPath', 'batchSha256'), ('batchEvidencePath', 'batchEvidenceSha256')]:
        raw = regular_bytes(control, config[path_key])
        require(digest(raw) == config[hash_key], 'Trusted barrier file digest mismatch: ' + path_key)
        docs.append(json.loads(raw))
    batch, evidence = docs
    require(batch.get('siteKey') == SITE and batch.get('scopeKey') == SCOPE
            and batch.get('membershipSourceSha256') == MEMBERSHIP_SHA256,
            'Bucheon batch geographic identity mismatch')
    require(evidence.get('finalSourceSha') == revision, 'Batch evidence does not identify approved source')
    return config['batchPath'], config['batchEvidencePath']


def validate_source(root, baseline_root, site):
    root, baseline_root = Path(root), Path(baseline_root)
    config = site['coverageDeployment']
    read = lambda base, name: json.loads(regular_bytes(base, 'src/data/' + name))
    for name, key in [('publish-manifest.json', 'productionManifestSha256'),
                      ('region-coverage.json', 'coverageSha256'), ('region-policy.json', 'regionPolicySha256')]:
        require(digest(regular_bytes(root, 'src/data/' + name)) == config[key], 'Reviewed source changed: ' + name)
    manifest, old = read(root, 'publish-manifest.json'), read(baseline_root, 'publish-manifest.json')
    pages, old_pages = read(root, 'pages.json'), read(baseline_root, 'pages.json')
    architecture = read(root, 'architecture.json')
    by_key, rows, nodes = indexed(pages, 'pageKey'), indexed(manifest['pages'], 'pageKey'), indexed(architecture['pages'], 'pageKey')
    require(manifest.get('siteKey') == architecture.get('siteKey') == SITE
            and manifest.get('snapshotMode') == 'git-frozen', 'Bucheon frozen source identity mismatch')
    require(by_key.keys() == rows.keys() == nodes.keys() and len(rows) == 25, 'Bucheon needs 24 geographic details plus preserved facility')
    require(read(root, 'page-map.json').get('pages') == manifest['pages'], 'Frozen map mismatch')
    indexed(pages, 'url'); indexed(pages, 'snapshotId')
    require(len(old['pages']) == len(old_pages) == 1, 'Historical facility baseline mismatch')
    for name, before in [('pages.json', old_pages), ('publish-manifest.json', old['pages']),
                         ('architecture.json', read(baseline_root, 'architecture.json')['pages'])]:
        after = {'pages.json': by_key, 'publish-manifest.json': rows, 'architecture.json': nodes}[name]
        require(all(after.get(p['pageKey']) == p for p in before), 'Historical trial content changed: ' + name)
    require(all(manifest.get('snapshotLedger', {}).get(k) == v for k, v in old['snapshotLedger'].items()),
            'Historical trial ledger changed')
    require(all(r.get('status') == 'approved' and r.get('approvalVerified') is True for r in rows.values()),
            'Unapproved frozen detail')
    coverage, policy = read(root, 'region-coverage.json'), read(root, 'region-policy.json')
    require(coverage.get('schemaVersion') == 2 and policy.get('schemaVersion') == 1
            and coverage.get('siteKey') == policy.get('siteKey') == SITE
            and coverage.get('scopeKey') == policy.get('scopeKey') == SCOPE and policy.get('enabled') is True,
            'Schema-2 regional source identity mismatch')
    units = indexed(coverage['units'], 'unitKey'); aliases = indexed(coverage['administrativeCrosswalk'], 'aliasKey')
    reps = indexed(coverage['representatives'], 'pageKey')
    require(len(units) == len(reps) == 24 and len(aliases) == 37
            and sum(len(a['relations']) for a in aliases.values()) == 48, 'Bucheon geographic membership incomplete')
    require(len({u['name'] for u in units.values()} | {a['name'] for a in aliases.values()}) == 49,
            'Bucheon name coverage incomplete')
    require(set(reps) == set(rows) - {old['pages'][0]['pageKey']}, 'Regional membership missing or extra details')
    assigned = []
    for key, rep in reps.items():
        page, node = by_key[key], nodes[key]
        require(rep.get('status') == 'approved' and rep.get('routeMode') == 'regional'
                and len(rep.get('unitKeys', [])) == 1, 'Every reviewed legal dong needs one representative')
        assigned.extend(rep['unitKeys'])
        require(page.get('scopeKey') == node.get('scopeKey') == SCOPE
                and page.get('category') == 'regions' and page.get('pageType') == 'regional-service'
                and page.get('url') == rep.get('url') == '/regions/' + rep['slug'] + '/'
                and page.get('regionUnitKeys') == rep['unitKeys']
                and node.get('intentKey') == rep['intentKey'], 'Regional frozen identity mismatch')
    require(len(assigned) == len(set(assigned)) == 24 and set(assigned) == set(units), 'Canonical unit coverage incomplete')
    bindings = indexed(policy.get('visualBindings', []), 'pageKey')
    require(set(bindings) == set(reps) and all(b.get('status') == 'approved' for b in bindings.values()),
            'Independent visual bindings incomplete')
    require(read(root, 'site-config.json').get('productionApproved') is True
            and bool(regular_bytes(root, 'production-indexing.enabled')), 'Bucheon source indexing gate is closed')
    for name in ('wrangler.jsonc', 'wrangler.staging.jsonc'):
        require(regular_bytes(root, name) == regular_bytes(baseline_root, name), 'Worker routing settings changed')
    wrangler = json.loads(regular_bytes(root, 'wrangler.jsonc'))
    require(wrangler.get('name') == WORKER and wrangler.get('assets', {}).get('directory') == './dist/'
            and not any(k in wrangler for k in ('route', 'routes', 'triggers')), 'Bucheon fixed Worker boundary changed')
    for name in ('products.json', 'business-truth.json'):
        require(regular_bytes(root, 'src/data/' + name) == regular_bytes(baseline_root, 'src/data/' + name),
                'Historical product/business source changed')
    for original in (baseline_root/'public/images').rglob('*'):
        if original.is_file():
            current = root/original.relative_to(baseline_root)
            require(regular_bytes(root, original.relative_to(baseline_root)) == regular_bytes(baseline_root, original.relative_to(baseline_root)), 'Historical image changed')
    return {'pipelineState': 'bucheon_source_validated', 'siteKey': SITE, 'scopeKey': SCOPE,
            'legalUnits': 24, 'administrativeUnits': 37, 'manifestPages': len(rows), 'historicalTrialPreserved': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--baseline-root', type=Path, required=True)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        site = json.loads(args.registry.read_text())['sites'][SITE]
        resolve(site, IDENTITY['repo'], args.revision, SCOPE, SCOPE)
        reviewed_revision = args.revision
        if site.get('indexnowOwnership', {}).get('revision') == args.revision:
            from indexnow_ownership import verify_source
            proof = verify_source(site, args.revision, args.workspace)
            reviewed_revision = proof['previousRevision']
        batch, evidence = validate_barrier_inputs(args.control, site, reviewed_revision)
        # Existing helper remains authoritative. Unsupported schema/site fails closed
        # until the independently reviewed Bucheon adapter is installed on main.
        run = subprocess.run(['python3', str(args.control/'site-factory/engine/batch_barrier.py'),
              '--batch', str(args.control/batch), '--evidence', str(args.control/evidence),
              '--workspace', str(args.workspace)], check=True, capture_output=True, text=True)
        barrier = json.loads(run.stdout)
        require(barrier.get('state') == 'staging_complete' and barrier.get('finalSourceSha') == reviewed_revision,
                'Independent whole-batch barrier did not complete')
        result = validate_source(args.root, args.baseline_root, site)
        result['revision'] = args.revision
        result['reviewedContentRevision'] = reviewed_revision
        result['batchBarrier'] = barrier
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
        result = {'pipelineState': 'verification_blocked', 'siteKey': SITE, 'reason': str(error)}
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result, ensure_ascii=False))
    return int(result['pipelineState'] != 'bucheon_source_validated')


if __name__ == '__main__':
    raise SystemExit(main())

