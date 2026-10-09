#!/usr/bin/env python3
"""Read-only initial-50 and exact Goyang/Bucheon single-snapshot completion barriers."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import os
import tempfile
from urllib.parse import urlsplit

import render_snapshot as snapshot_renderer

from render_snapshot import parse_payload, validate_content, frozen_hashes

REVISIONS = ('ruleRevision', 'templateRevision', 'registryRevision')
GATES = {'build', 'static', 'graph', 'canonical', 'h1', 'schema', 'robots', 'sitemap', '404'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def sha(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{40}', value) is not None


def identity(batch):
    """Order-independent identity; callers must retain the originally frozen hash."""
    if batch.get("schemaVersion") == 2:
        return goyang_identity(batch)
    return digest({key: batch[key] for key in
                   ('batchId', 'siteKey', 'targetDetails', 'canaryPageKey', *REVISIONS)} |
                  {'members': sorted(batch['members'], key=lambda row: row['pageKey'])})


def indexed(rows, key):
    require(isinstance(rows, list), f'{key} rows must be a list')
    result = {}
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get(key), str) and row[key], f'Missing {key}')
        require(row[key] not in result, f'Duplicate {key}: {row[key]}')
        result[row[key]] = row
    return result


class GitEvidence:
    """Only committed bytes: dirty working files cannot satisfy the barrier."""
    def __init__(self, workspace):
        self.workspace = workspace

    def run(self, *args):
        return subprocess.check_output(['git', '-C', str(self.workspace), *args], stderr=subprocess.PIPE)

    def read(self, revision, path):
        require(sha(revision), 'Expected full lowercase source SHA')
        p = PurePosixPath(path)
        require(not p.is_absolute() and '..' not in p.parts, 'Unsafe evidence path')
        return self.run('show', f'{revision}:{path}')

    def ancestor(self, older, newer):
        require(sha(older) and sha(newer), 'Expected full checkpoint SHA')
        return subprocess.run(['git', '-C', str(self.workspace), 'merge-base', '--is-ancestor', older, newer],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

    def paths(self, revision, root):
        rows = self.run('ls-tree', '-rz', revision, '--', root).split(b'\0')
        result = set()
        for row in filter(None, rows):
            meta, raw_path = row.split(b'\t', 1)
            mode, kind, _ = meta.decode().split()
            path = raw_path.decode()
            require(mode == '100644' and kind == 'blob' and path.startswith(root + '/'),
                    'Initial source inventory contains non-regular files')
            result.add(path[len(root) + 1:])
        return result


def check(batch, evidence, git):
    """Fail closed; external reviewer/QA assertions must come from trusted consumers."""
    if batch.get("schemaVersion") == 2:
        return check_goyang(batch, evidence, git)
    require(batch.get('schemaVersion') == 1, 'Unsupported batch schema')
    require(batch.get('targetDetails') == 50 and type(batch['targetDetails']) is int,
            'Initial batch target is exactly 50; never shrink for query shortage')
    for key in ('batchId', 'siteKey', 'canaryPageKey'):
        require(isinstance(batch.get(key), str) and batch[key].strip(), f'Missing {key}')
    for key in REVISIONS:
        require(sha(batch.get(key)), f'Missing pinned {key}')
    members = indexed(batch['members'], 'pageKey')
    require(len(members) == 50, 'Exactly 50 researched detail members required; insufficient queries remain blocked')
    indexed(batch['members'], 'intentKey')
    require(all(set(m) == {'pageKey', 'intentKey'} for m in members.values()), 'Membership is detail page/intent only')
    require(batch['canaryPageKey'] in members, 'Canary must be a counted detail member')
    require(batch.get('membershipHash') == identity(batch), 'Frozen membership/revision identity changed')
    require(evidence.get('batchId') == batch['batchId'] and
            evidence.get('membershipHash') == batch['membershipHash'], 'Evidence batch identity mismatch')
    final = evidence.get('finalSourceSha')
    require(sha(final), 'Final exact source SHA required')
    registry = json.loads(git.read(batch['registryRevision'], '.github/site-factory-sites.json'))
    target = registry['sites'][batch['siteKey']]
    root = target['root'].strip('/')
    path = root + '/src/data/publish-manifest.json'
    raw_manifest = git.read(final, path)
    manifest = json.loads(raw_manifest)
    require(manifest.get('siteKey') == batch['siteKey'], 'Manifest site mismatch')
    pages = indexed(manifest['pages'], 'pageKey')
    architecture = json.loads(git.read(final, root + '/src/data/architecture.json'))
    architecture_pages = indexed(architecture['pages'], 'pageKey')
    indexed(manifest['pages'], 'url')
    checkpoints = indexed(evidence['items'], 'pageKey')
    require(set(checkpoints) == set(members), 'Missing or extra item checkpoint')
    for field in ('queueRecordId', 'issueUrl', 'snapshotId'):
        indexed(evidence['items'], field)
    for key, member in members.items():
        item = checkpoints[key]
        require(key in architecture_pages and architecture_pages[key].get('intentKey') == member['intentKey'],
                f'{key}: final architecture intent mismatch')
        require(item.get('intentKey') == member['intentKey'], f'{key}: intent mismatch')
        require(all(item.get(r) == batch[r] for r in REVISIONS), f'{key}: pinned revisions changed')
        require(isinstance(item.get('draftRevision'), str) and item['draftRevision'].strip(), f'{key}: missing Writer revision')
        require(re.fullmatch(r'https://github\.com/' + re.escape(target['repo']) + r'/issues/[1-9][0-9]*', item['issueUrl']), f'{key}: wrong Publisher issue')
        payload = validate_content(parse_payload(item['payload']))
        require(payload['SITE_KEY'] == batch['siteKey'] and payload['PAGE_KEY'] == key and
                payload.get('INTENT_KEY') == member['intentKey'], f'{key}: payload identity mismatch')
        require(payload['TARGET_REPO'] == target['repo'] and payload['TARGET_BRANCH'] == target['branch'] and
                payload['TARGET_ROOT'] == target['root'], f'{key}: Publisher target mismatch')
        require(payload['ROUTE_TYPE'] == 'category', f'{key}: HOME/HUB cannot count as details')
        require(architecture_pages[key].get('url') == payload['url'], f'{key}: final architecture route mismatch')
        storage, reviewed = frozen_hashes(payload)
        require(item.get('reviewDigest') == reviewed and item.get('snapshotHash') == storage,
                f'{key}: changed content or graph needs new Writer revision and Reviewer approval')
        approval = item.get('reviewerApproval', {})
        require(approval.get('status') == 'approved' and bool(approval.get('reviewer')) and
                bool(approval.get('evidenceUrl')) and approval.get('draftRevision') == item['draftRevision'] and
                approval.get('reviewDigest') == reviewed and approval.get('membershipHash') == batch['membershipHash'],
                f'{key}: exact Reviewer approval required')
        require(payload.get('APPROVAL_STATUS') == 'approved' and payload.get('APPROVED_SNAPSHOT_HASH') == reviewed,
                f'{key}: Publisher approval mismatch')
        require(item['queueRecordId'] == payload['PUBLISH_QUEUE_RECORD_ID'] and item['snapshotId'] == payload['SNAPSHOT_ID'],
                f'{key}: Queue/snapshot mismatch')
        commit, review_source = item.get('commitSha'), item.get('reviewSourceSha')
        require(git.ancestor(review_source, commit) and git.ancestor(commit, final), f'{key}: checkpoints outside final history')
        baseline = indexed(json.loads(git.read(review_source, path))['pages'], 'pageKey')
        require(all(related in baseline and baseline[related].get('status') == 'approved' and
                    baseline[related].get('approvalVerified') is True for related in payload['relatedKeys']),
                f'{key}: related links must exist in the current explicitly approved review manifest')
        committed = indexed(json.loads(git.read(commit, path))['pages'], 'pageKey')
        expected = {'snapshotId': payload['SNAPSHOT_ID'], 'snapshotHash': storage, 'draftKey': payload['DRAFT_KEY'],
                    'sourceRecordId': payload['SOURCE_RECORD_ID'], 'publishQueueRecordId': item['queueRecordId'],
                    'url': payload['url'], 'status': 'approved', 'approvalVerified': True}
        for label, table in [('checkpoint', committed), ('final', pages)]:
            require(key in table and all(table[key].get(k) == v for k, v in expected.items()),
                    f'{key}: {label} manifest no longer matches approved snapshot')
    routes = {'/'} | {row['url'] for row in pages.values()} | {row['url'] for row in architecture.get('hubs', [])}
    qa = evidence.get('qa', {})
    require(qa.get('sourceSha') == final and qa.get('manifestSha256') == hashlib.sha256(raw_manifest).hexdigest(),
            'QA must bind exact final source and manifest bytes')
    require(qa.get('state') == 'passed' and qa.get('environment') == 'staging' and qa.get('noindex') is True and
            bool(qa.get('reviewer')) and bool(qa.get('evidenceUrl')), 'Independent noindex staging QA required')
    require(set(qa.get('gates', [])) == GATES, 'Missing whole-site QA gates')
    reports = indexed(qa.get('routes', []), 'url')
    require(set(reports) == routes and all(r.get('state') == 'passed' and r.get('noindex') is True for r in reports.values()),
            'Every final HOME/HUB/detail route must pass noindex QA; blocked HTTP is not success')
    return {'state': 'staging_complete', 'batchId': batch['batchId'], 'membershipHash': batch['membershipHash'],
            'finalSourceSha': final, 'detailCount': 50, 'homeCount': 1,
            'hubCount': len({r['url'] for r in architecture.get('hubs', [])}), 'qaRouteCount': len(routes),
            'productionApproved': False, 'indexNowAllowed': False}


GOYANG_SITE = 'goyang-flower-v2'
GOYANG_SCOPE = 'goyang-flower-v2-dong-coverage-20261003'
GOYANG_TARGET = {'repo': 'joseungil-kr/fwith-site-factory', 'branch': 'site-factory-goyang-v2',
                 'root': 'site-factory/goyang-flower'}
GOYANG_GATES = GATES | {'source', 'snapshot', 'assets', 'banner', 'og', 'cta', 'inbound', 'aliases', 'responsive', 'isolation'}
GOYANG_IDENTITY = ('schemaVersion', 'contractType', 'batchId', 'siteKey', 'scopeKey',
                   'baselineSourceSha', 'baselineManifestSha256', 'coverageSha256', *REVISIONS)


BUCHEON_SITE = 'bucheon-flower-v2'
BUCHEON_SCOPE = 'bucheon-flower-v2-dong-coverage-20261004'
BUCHEON_TARGET = {'repo': 'joseungil-kr/fwith-site-factory', 'branch': 'site-factory-bucheon-v2',
                  'root': 'site-factory/bucheon-flower'}
# Exact existing Namyangju frozen batch controller. This pin preserves its
# already-reviewed renderer when current main gains additional strict adapters.
INITIAL_RENDERER_ALLOWLIST = {
    ('namyangju-flower-v2', '45f13097c9e951934486f88b0735fd59394f20c3'):
        '3ea763515965fcdf43a0f013e0bc44e931e6fb16a21014f12a722f8cf87b2ad9',
}
LEGACY_RENDERER_ALLOWLIST = {
    (BUCHEON_SITE, '00d63c5b557401100ae44b25e8c804c28c9c461e'):
        'bd3d22c3a584c94133e8bea1ea0603b94f2dbd6c60ad3ca25c5e9d5e0f6fdcd3',
}


def bucheon_representatives(coverage, site=BUCHEON_SITE, scope=BUCHEON_SCOPE, unit_types=('legal-dong',)):
    """One reviewed schema-2 representative for every exact Bucheon legal dong."""
    require(type(coverage.get('schemaVersion')) is int and coverage['schemaVersion'] == 2
            and coverage.get('siteKey') == site and coverage.get('scopeKey') == scope
            and coverage.get('unitBasis') == 'legal-dong-plus-eup-myeon'
            and coverage.get('countIsPageQuota') is False, 'Bucheon coverage adapter mismatch')
    units = indexed(coverage['units'], 'unitKey')
    districts = indexed(coverage['districts'], 'key')
    require(units and districts and all(u.get('unitType') in unit_types
            and isinstance(u.get('name'), str) and u['name']
            and isinstance(u.get('districtKeys'), list) and len(u['districtKeys']) == 1
            and u['districtKeys'][0] in districts and isinstance(u.get('legalRi'), list)
            and (u['unitType'] != 'legal-dong' or u['legalRi'] == []) for u in units.values()),
            'Bucheon requires district-bound legal dongs')
    aliases = indexed(coverage['administrativeCrosswalk'], 'aliasKey')
    for alias in aliases.values():
        relations = indexed(alias['relations'], 'unitKey')
        require(isinstance(alias.get('name'), str) and alias['name'] and relations
                and alias.get('districtKey') in districts and not alias.get('unresolvedCandidateNames')
                and all(key in units and (alias['districtKey'] in units[key]['districtKeys']
                        or __import__('provision_goyang').exact_cross_district_evidence(coverage, alias, units[key], rel))
                        and rel.get('scope') in ('whole', 'partial') for key, rel in relations.items()),
                'Bucheon administrative relation mismatch')
    rows = coverage['representatives']
    representatives = indexed(rows, 'pageKey')
    for field in ('url', 'slug', 'intentKey', 'primaryKeyword'):
        indexed(rows, field)
    assigned = []
    for row in representatives.values():
        require(isinstance(row.get('unitKeys'), list) and len(row['unitKeys']) == 1
                and row['unitKeys'][0] in units and row.get('status') == 'approved'
                and row.get('routeMode') == 'regional' and row.get('queryEvidence'),
                'Bucheon representative needs one independently reviewed legal dong')
        assigned.extend(row['unitKeys'])
    require(len(assigned) == len(set(assigned)) and set(assigned) == set(units),
            'Bucheon representatives must cover every legal dong exactly once')
    require(set(units) == {key for alias in aliases.values() for key in indexed(alias['relations'], 'unitKey')},
            'Bucheon aliases must cover every legal dong')
    return representatives


def require_bucheon_reviewer(record):
    reviewer, evidence_url = record.get('reviewer'), record.get('evidenceUrl')
    require(isinstance(reviewer, str) and reviewer.strip(), 'Bucheon reviewer must be a nonblank string')
    require(isinstance(evidence_url, str) and evidence_url and not any(c.isspace() for c in evidence_url),
            'Bucheon evidence URL must be a nonblank HTTPS URL')
    parsed = urlsplit(evidence_url)
    require(parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password,
            'Bucheon evidence URL must be a nonblank HTTPS URL')


def require_no_bucheon_site_catalog(git, revision, root):
    # This pinned renderer supports site-local catalogs only for Ansan. Omitting a
    # present catalog from replay could otherwise conceal a real renderer failure.
    path = root + '/src/data/site-catalog.json'
    if isinstance(git, GitEvidence):
        require(not git.run('ls-tree', '-z', revision, '--', path),
                'Bucheon site-local catalog is unsupported by this exact profile')
        return
    try:
        git.read(revision, path)
    except KeyError:  # The in-memory committed-byte test adapter.
        return
    raise ValueError('Bucheon site-local catalog is unsupported by this exact profile')


def read_bucheon_dependency(git, revision, path):
    # Replay materializes regular files; never silently dereference or convert a
    # committed symlink/gitlink into a different renderer input.
    if isinstance(git, GitEvidence):
        row = git.run('ls-tree', '-z', revision, '--', path)
        require(row.startswith(b'100644 blob ') or row.startswith(b'100755 blob '),
                'Bucheon renderer dependency must be a committed regular file')
    return git.read(revision, path)


def bucheon_dependencies(batch, coverage_raw, git, revision, root, site=BUCHEON_SITE, scope=BUCHEON_SCOPE, unit_types=('legal-dong',)):
    require(read_bucheon_dependency(git, revision, root + '/src/data/region-coverage.json') == coverage_raw,
            'Bucheon baseline coverage dependency changed')
    dependencies = {'src/data/region-coverage.json': coverage_raw}
    for field, path in (('policySha256', 'src/data/region-policy.json'),
                        ('productsSha256', 'src/data/products.json')):
        require(isinstance(batch.get(field), str) and re.fullmatch(r'[0-9a-f]{64}', batch[field]),
                'Missing pinned Bucheon dependency digest: ' + field)
        raw = read_bucheon_dependency(git, revision, root + '/' + path)
        require(hashlib.sha256(raw).hexdigest() == batch[field], 'Bucheon dependency digest mismatch: ' + field)
        dependencies[path] = raw
    policy = json.loads(dependencies['src/data/region-policy.json'])
    require(type(policy.get('schemaVersion')) is int and policy['schemaVersion'] == 1
            and policy.get('enabled') is True and policy.get('siteKey') == site
            and policy.get('scopeKey') == scope and policy.get('unitTypes') == list(unit_types),
            'Bucheon regional policy mismatch')
    coverage = json.loads(coverage_raw)
    require(isinstance(batch.get('membershipSourceSha256'), str)
            and re.fullmatch(r'[0-9a-f]{64}', batch['membershipSourceSha256'])
            and coverage.get('membershipSourceSha256') == batch['membershipSourceSha256']
            and policy.get('membershipSourceSha256') == batch['membershipSourceSha256'],
            'Bucheon membership research binding mismatch')
    bindings = indexed(policy['visualBindings'], 'pageKey')
    require(set(bindings) == set(indexed(coverage['representatives'], 'pageKey')),
            'Bucheon exact representative visual bindings required')
    for asset in bindings.values():
        image = asset.get('image', '')
        require(isinstance(image, str) and re.fullmatch(r'/images/[A-Za-z0-9_./-]+\.(?:png|jpe?g|webp)', image)
                and '..' not in image, 'Unsafe Bucheon image dependency')
        path = 'public' + image
        raw = read_bucheon_dependency(git, revision, root + '/' + path)
        require(hashlib.sha256(raw).hexdigest() == asset.get('sha256'), 'Bucheon image dependency digest mismatch')
        dependencies[path] = raw
    require_no_bucheon_site_catalog(git, revision, root)
    return dependencies


def check_bucheon_dependencies(dependencies, git, revision, root):
    require(all(read_bucheon_dependency(git, revision, root + '/' + path) == raw for path, raw in dependencies.items()),
            'Bucheon frozen renderer dependency changed')
    require_no_bucheon_site_catalog(git, revision, root)


def goyang_identity(batch):
    fields = GOYANG_IDENTITY + (('policySha256', 'productsSha256', 'membershipSourceSha256') if batch.get('siteKey') == BUCHEON_SITE or batch.get('contractType') == 'whole-region-initial' else ())
    if batch.get('contractType') == 'whole-region-initial':
        fields += ('bootstrapSourceSha',)
    return digest({key: batch[key] for key in fields} |
                  {'members': sorted(batch['members'], key=lambda row: row['pageKey'])})


def snapshot_tables(git, revision, root, site=GOYANG_SITE):
    documents, tables, raw = {}, {}, {}
    for name in ('publish-manifest', 'page-map', 'pages', 'architecture'):
        path = root + '/src/data/' + name + '.json'
        raw[name] = (read_bucheon_dependency(git, revision, path) if site == BUCHEON_SITE
                     else git.read(revision, path))
        documents[name] = json.loads(raw[name])
        rows = documents[name] if name == 'pages' else documents[name]['pages']
        tables[name] = indexed(rows, 'pageKey')
        if name != 'pages':
            require(documents[name].get('siteKey') == site, 'Goyang data site mismatch')
    expected = set(tables['publish-manifest'])
    require(all(set(table) == expected for table in tables.values()), 'Goyang frozen table parity mismatch')
    for field in ('url', 'snapshotId', 'publishQueueRecordId'):
        indexed(documents['publish-manifest']['pages'], field)
    return documents, tables, raw


def goyang_replay_checkpoint(payload, registry, prior_raw, root, dependencies=None, renderer_bytes=None):
    """Replay the actual approved snapshot renderer in disposable local storage.

    Neither the evidence checkout nor remote state is written. Only the existing
    renderer, whose file bytes are checked against the pinned controller, runs.
    """
    with tempfile.TemporaryDirectory(prefix='goyang-barrier-replay-') as directory:
        workspace = Path(directory)
        data = workspace / root / 'src/data'
        data.mkdir(parents=True)
        for name, raw in prior_raw.items():
            (data / (name + '.json')).write_bytes(raw)
        dependencies = dependencies or {}
        for path, raw in dependencies.items():
            destination = workspace / root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        if renderer_bytes is None:
            result = snapshot_renderer.render(payload, registry, workspace)
        else:
            # Historical batches retain their exact reviewed renderer bytes.
            # Do not weaken old proof hashes because current main gained an
            # opt-in adapter. The isolated control files stay outside workspace.
            with tempfile.TemporaryDirectory(prefix='pinned-renderer-') as controls:
                control = Path(controls)
                (control / 'render_snapshot.py').write_bytes(renderer_bytes)
                (control / 'registry.json').write_text(json.dumps(registry))
                (control / 'payload.txt').write_text(payload)
                run = subprocess.run([sys.executable, '-I', str(control / 'render_snapshot.py'),
                    '--registry', str(control / 'registry.json'), '--payload', str(control / 'payload.txt'),
                    '--workspace', str(workspace)], capture_output=True, text=True, check=True,
                    env={'PATH': os.defpath, 'PYTHONIOENCODING': 'utf-8'}, timeout=30)
                result = json.loads(run.stdout)
        expected_paths = {root + '/src/data/' + name + '.json' for name in prior_raw}
        require(result.get('publicationApproved') is True and result.get('approvalVerified') is True
                and set(result.get('changedFiles', [])) == expected_paths,
                'Pinned renderer did not produce exactly one approved four-file snapshot')
        require({file.relative_to(workspace).as_posix() for file in workspace.rglob('*') if file.is_file()}
                == expected_paths | {root + '/' + path for path in dependencies},
                'Pinned renderer produced an unexpected file')
        require(all((workspace / root / path).read_bytes() == raw for path, raw in dependencies.items()),
                'Pinned renderer changed a frozen dependency')
        return {name: (data / (name + '.json')).read_bytes() for name in prior_raw}


def check_goyang(batch, evidence, git):
    """Scoped all-remaining barrier. Geography gives membership, never approval."""
    initial = batch.get('contractType') == 'whole-region-initial'
    bucheon = batch.get('siteKey') == BUCHEON_SITE
    scoped = bucheon or initial
    site, scope, expected_target, contract = (
        (BUCHEON_SITE, BUCHEON_SCOPE, BUCHEON_TARGET, 'bucheon-all-remaining-legal-dongs') if bucheon else
        (GOYANG_SITE, GOYANG_SCOPE, GOYANG_TARGET, 'goyang-all-remaining-legal-dongs'))
    if initial:
        from whole_initial import initial_batch_identity
        site, scope, expected_target = initial_batch_identity(batch)
        contract = 'whole-region-initial'
    require(type(batch.get('schemaVersion')) is int and batch['schemaVersion'] == 2
            and batch.get('contractType') == contract, 'Unsupported scoped batch schema')
    require(batch.get('siteKey') == site and batch.get('scopeKey') == scope, 'Registered batch scope mismatch')
    require(isinstance(batch.get('batchId'), str) and batch['batchId'].strip(), 'Missing batchId')
    require(all(sha(batch.get(key)) for key in (*REVISIONS, 'baselineSourceSha')), 'Missing pinned Goyang revision')
    require(all(re.fullmatch(r'[0-9a-f]{64}', batch.get(key, '')) for key in
                ('baselineManifestSha256', 'coverageSha256')), 'Missing pinned raw-byte digest')
    require(batch.get('membershipHash') == goyang_identity(batch), 'Frozen Goyang membership identity changed')
    require(evidence.get('batchId') == batch['batchId'] and evidence.get('membershipHash') == batch['membershipHash'],
            'Goyang evidence identity mismatch')
    final, base = evidence.get('finalSourceSha'), batch['baselineSourceSha']
    require(sha(final) and git.ancestor(base, final), 'Final source does not descend from baseline')
    if scoped:
        for path in ('.github/site-factory-sites.json', 'site-factory/engine/render_snapshot.py'):
            read_bucheon_dependency(git, batch['registryRevision'], path)
    registry = json.loads(git.read(batch['registryRevision'], '.github/site-factory-sites.json'))
    renderer_bytes = git.read(batch['registryRevision'], 'site-factory/engine/render_snapshot.py')
    same_renderer = renderer_bytes == Path(snapshot_renderer.__file__).read_bytes()
    renderer_allowlist = INITIAL_RENDERER_ALLOWLIST if initial else LEGACY_RENDERER_ALLOWLIST
    require(same_renderer or (renderer_allowlist.get((site, batch['registryRevision']))
            == hashlib.sha256(renderer_bytes).hexdigest()), 'Executing renderer differs from pinned controller bytes')
    target = registry['sites'][site]
    require(all(target.get(k) == v for k, v in expected_target.items())
            and target.get('snapshotRenderer') == 'structured-json-v12'
            and target.get('categoryPageTypes', {}).get('regions') == ['regional-service'], 'Registered target mismatch')
    if scoped:
        require(target.get('regionalService') == {
                    'enabled': True, 'scopeKey': scope,
                    'definitionFile': 'src/data/region-coverage.json', 'policyFile': 'src/data/region-policy.json'}
                and target['regionalService']['enabled'] is True
                and target.get('administrativeCoverage') is None, 'Bucheon registered adapter mismatch')
    else:
        require(target.get('regionalService') is None and target.get('administrativeCoverage') ==
                {'enabled': True, 'regionKey': 'goyang', 'unitBasis': 'legal'}, 'Goyang registered target mismatch')
    require(target.get('growthPaused') is True and target.get('autoDeploySnapshots') is False
            and target.get('requireSnapshotApproval') is True and target.get('requireRevisionApproval') is True,
            'Goyang batch requires explicit snapshots and no intermediate automatic deploy')
    root = target['root']
    if initial:
        from whole_initial import validate_initial_binding
        validate_initial_binding(batch, target, git, base, final)
    base_docs, baseline, base_raw = snapshot_tables(git, base, root, site)
    require(hashlib.sha256(base_raw['publish-manifest']).hexdigest() == batch['baselineManifestSha256'],
            'Baseline raw manifest digest mismatch')
    coverage_raw = git.read(base, root + '/src/data/region-coverage.json')
    require(hashlib.sha256(coverage_raw).hexdigest() == batch['coverageSha256']
            and git.read(final, root + '/src/data/region-coverage.json') == coverage_raw, 'Coverage bytes changed')
    coverage = json.loads(coverage_raw)
    dependencies = {}
    if scoped:
        unit_types = tuple(sorted({u['unitType'] for u in coverage['units']})) if initial else ('legal-dong',)
        units = bucheon_representatives(coverage, site, scope, unit_types)
        dependencies = bucheon_dependencies(batch, coverage_raw, git, base, root, site, scope, unit_types)
        check_bucheon_dependencies(dependencies, git, final, root)
    else:
        require(coverage.get('siteKey') == GOYANG_SITE and coverage.get('scopeKey') == GOYANG_SCOPE
                and coverage.get('unitBasis') == 'legal', 'Official coverage scope mismatch')
        units = indexed(coverage['units'], 'pageKey'); indexed(coverage['units'], 'unitKey')
        indexed(coverage['units'], 'url'); indexed(coverage['units'], 'slug')
    members = indexed(batch['members'], 'pageKey'); indexed(batch['members'], 'intentKey')
    require(members and all(set(m) == {'pageKey', 'intentKey'} for m in members.values()), 'Invalid Goyang member fields')
    baseline_keys = set(baseline['publish-manifest'])
    require(members.keys() == units.keys() - baseline_keys, 'Membership must include every remaining legal dong exactly once')
    for key, member in members.items():
        unit = units[key]
        require(re.fullmatch(r'[a-z0-9-]+', unit['slug'])
                and unit['url'] == '/regions/' + unit['slug'] + '/'
                and member['intentKey'] == site.split('-')[0] + '|flower-delivery|local-order|' + unit['slug']
                and (not scoped or member['intentKey'] == unit['intentKey']), 'Goyang member route/intent mismatch')
    require((not baseline_keys if initial else bool(baseline_keys)) and all(row.get('status') == 'approved' and row.get('approvalVerified') is True
                                for row in baseline['publish-manifest'].values()), 'Initial baseline must be empty; historical baseline must contain approved details')
    if initial:
        require(base_docs['publish-manifest'].get('snapshotLedger') == {}, 'Initial baseline ledger must be empty')
    docs, tables, raw = snapshot_tables(git, final, root, site)
    require(set(tables['publish-manifest']) == baseline_keys | set(members), 'Final manifest has missing or extra details')
    for name, old in baseline.items():
        require(all(tables[name].get(k) == v for k, v in old.items()), 'Existing baseline frozen content changed')
    require(all(docs['publish-manifest'].get('snapshotLedger', {}).get(k) == v
                for k, v in base_docs['publish-manifest'].get('snapshotLedger', {}).items()), 'Baseline snapshot ledger changed')
    items = indexed(evidence['items'], 'pageKey')
    require(set(items) == set(members), 'Missing or extra Goyang checkpoint')
    for field in ('queueRecordId', 'issueUrl', 'snapshotId', 'commitSha'):
        indexed(evidence['items'], field)
    previous, accumulated = base, set(baseline_keys)
    prior_tables, prior_raw = baseline, base_raw
    prior_ledger = base_docs['publish-manifest'].get('snapshotLedger', {})
    require(isinstance(prior_ledger, dict), 'Baseline snapshot ledger must be an object')
    for item in evidence['items']:
        key = item['pageKey']; unit = units[key]
        require(item.get('intentKey') == members[key]['intentKey'] and
                all(item.get(r) == batch[r] for r in REVISIONS), key + ': checkpoint identity mismatch')
        require(isinstance(item.get('draftRevision'), str) and item['draftRevision'].strip()
                and isinstance(item.get('writerRunId'), str) and item['writerRunId'].strip(), key + ': missing Writer identity')
        p = validate_content(parse_payload(item['payload']))
        wanted = {'SITE_KEY': site, 'PAGE_KEY': key, 'INTENT_KEY': item['intentKey'],
                  'TARGET_REPO': target['repo'], 'TARGET_BRANCH': target['branch'], 'TARGET_ROOT': root,
                  'SLUG': unit['slug'], 'CATEGORY': 'regions', 'ROUTE_TYPE': 'category',
                  'PAGE_TYPE': 'regional-service', 'PAGE_ROLE': 'REGION_SERVICE_LANDING',
                  'PARENT_HUB': '/regions/',
                  'LOCALIZATION_POLICY': 'local-required', 'QUERY_CLASS': 'local-commercial',
                  'VISUAL_INTENT': 'flower_delivery', 'ASSET_SLOT': 'REAL_PROOF'}
        structures = ({'address_specific_purchase_decision', 'REGION_SERVICE_LANDING'} if initial else {'REGION_SERVICE_LANDING'})
        require(all(p.get(k) == v for k, v in wanted.items()) and p.get('STRUCTURE_TYPE') in structures
                and p['url'] == unit['url']
                and all(p.get(k) for k in ('H1', 'FIRST-ANSWER', 'CARD-SUMMARY'))
                and not p.get('SUPERSEDES_SNAPSHOT_ID'), key + ': regional frozen payload mismatch')
        storage, reviewed = frozen_hashes(p)
        require(item.get('reviewDigest') == reviewed and item.get('snapshotHash') == storage
                and p.get('APPROVAL_STATUS') == 'approved' and p.get('APPROVED_SNAPSHOT_HASH') == reviewed,
                key + ': exact frozen approval mismatch')
        approval = item.get('reviewerApproval', {})
        if scoped:
            require_bucheon_reviewer(approval)
            require(approval['reviewer'].strip() != item['writerRunId'].strip(),
                    key + ': independent Bucheon reviewer required')
        require(approval.get('status') == 'approved' and approval.get('reviewer')
                and approval['reviewer'] != item['writerRunId'] and approval.get('evidenceUrl')
                and approval.get('draftRevision') == item['draftRevision']
                and approval.get('reviewDigest') == reviewed and approval.get('membershipHash') == batch['membershipHash'],
                key + ': independent exact-revision approval required')
        require(item['queueRecordId'] == p['PUBLISH_QUEUE_RECORD_ID'] and item['snapshotId'] == p['SNAPSHOT_ID']
                and re.fullmatch(r'https://github\.com/' + re.escape(target['repo']) + r'/issues/[1-9][0-9]*', item['issueUrl']),
                key + ': Publisher checkpoint mismatch')
        commit, reviewed_source = item['commitSha'], item.get('reviewSourceSha')
        require(commit != previous and git.ancestor(previous, commit) and git.ancestor(commit, final)
                and git.ancestor(base, reviewed_source) and git.ancestor(reviewed_source, previous),
                key + ': checkpoint order or review ancestry mismatch')
        review_docs, _, _ = snapshot_tables(git, reviewed_source, root, site)
        approved_targets = {r['pageKey'] for r in review_docs['publish-manifest']['pages']
                            if r.get('status') == 'approved' and r.get('approvalVerified') is True}
        require(all(k in approved_targets for k in p['relatedKeys']), key + ': future/unapproved related link')
        commit_docs, committed, commit_raw = snapshot_tables(git, commit, root, site)
        if scoped:
            check_bucheon_dependencies(dependencies, git, reviewed_source, root)
            check_bucheon_dependencies(dependencies, git, commit, root)
        expected_raw = goyang_replay_checkpoint(item['payload'], registry, prior_raw, root, dependencies,
                                               None if same_renderer else renderer_bytes)
        for name in expected_raw:
            require(commit_raw[name] == expected_raw[name],
                    key + ': checkpoint four JSON files differ from pinned renderer: ' + name)
        accumulated.add(key)
        require(set(committed['publish-manifest']) == accumulated, key + ': checkpoint is not one sequential addition')
        for name, old in prior_tables.items():
            require(all(committed[name].get(k) == v for k, v in old.items()), key + ': earlier frozen checkpoint changed')
        require(all(tables[name][key] == committed[name][key] for name in tables), key + ': checkpoint changed in final')
        ledger = {'pageKey': key, 'snapshotHash': storage, 'publishQueueRecordId': item['queueRecordId']}
        require(item['snapshotId'] not in prior_ledger, key + ': new snapshot reuses historical ledger identity')
        expected_ledger = {**prior_ledger, item['snapshotId']: ledger}
        require(commit_docs['publish-manifest'].get('snapshotLedger') == expected_ledger
                and docs['publish-manifest'].get('snapshotLedger', {}).get(item['snapshotId']) == ledger,
                key + ': checkpoint must preserve the whole ledger and add only this snapshot')
        previous, prior_tables, prior_ledger, prior_raw = commit, committed, expected_ledger, commit_raw
    require(all(raw[name] == commit_raw[name] for name in raw), 'Frozen data changed after final checkpoint')
    hubs = indexed(docs['architecture']['hubs'], 'url')
    baseline_hubs = indexed(base_docs['architecture']['hubs'], 'url')
    require(hubs.keys() == baseline_hubs.keys(), 'Unexpected Goyang hub inventory change')
    active, absent = set(), {'/site-factory-live-qa-definitely-not-found/'}
    for route, hub in hubs.items():
        children = sum(p.get('category') == hub.get('category') for p in tables['publish-manifest'].values())
        require(route == '/' + hub['category'] + '/' and hub.get('children') == children, 'Hub route/count mismatch')
        derived = {'children', 'indexable', 'menuVisible'} if initial else {'children'}
        require({k: v for k, v in hub.items() if k not in derived} ==
                {k: v for k, v in baseline_hubs[route].items() if k not in derived}, 'Baseline hub policy changed')
        if initial:
            require(hub.get('indexable') is (children >= 3) and hub.get('menuVisible') is (children >= 5), 'Initial hub policy differs from runtime')
        (active if children else absent).add(route)
    routes = {'/'} | active | {r['url'] for r in tables['publish-manifest'].values()}
    qa = evidence.get('qa', {}); manifest_hash = hashlib.sha256(raw['publish-manifest']).hexdigest()
    if scoped:
        require_bucheon_reviewer(qa)
        require(qa['reviewer'].strip() not in {item['writerRunId'].strip() for item in evidence['items']},
                'Independent Bucheon visual QA required')
    require(qa.get('sourceSha') == final and qa.get('manifestSha256') == manifest_hash
            and qa.get('state') == 'passed' and qa.get('environment') == 'staging' and qa.get('noindex') is True
            and qa.get('reviewer') and qa.get('evidenceUrl'), 'Whole final-source independent preview QA required')
    require(set(qa.get('gates', [])) == GOYANG_GATES, 'Missing Goyang whole-batch QA gates')
    reports = indexed(qa.get('routes', []), 'url'); not_found = indexed(qa.get('notFoundRoutes', []), 'url')
    require(set(reports) == routes and all(r.get('state') == 'passed' and r.get('noindex') is True for r in reports.values()),
            'Every final rendered route needs actual noindex QA')
    require(set(not_found) == absent and all(r.get('state') == 'passed' and r.get('status') == 404
                and r.get('canonicalAbsent') is True for r in not_found.values()), 'Exact empty-hub/unknown 404 QA required')
    names = sorted({r['name'] for r in coverage['units'] + coverage['administrativeCrosswalk']})
    require(qa.get('aliasCoverageSha256') == batch['coverageSha256'] and qa.get('discoverableNames') == names,
            'Complete legal/administrative alias discovery not verified')
    require(qa.get('reviewer') not in {item['writerRunId'] for item in evidence['items']}, 'Independent visual QA required')
    return {'state': 'staging_complete', 'batchId': batch['batchId'], 'membershipHash': batch['membershipHash'],
            'finalSourceSha': final, 'baselineDetailCount': len(baseline_keys), 'newDetailCount': len(members),
            'detailCount': len(tables['publish-manifest']), 'homeCount': 1, 'hubCount': len(active),
            'qaRouteCount': len(routes), 'notFoundRouteCount': len(absent), 'discoverableNameCount': len(names),
            'productionApproved': False, 'indexNowAllowed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, default=Path('.'))
    args = parser.parse_args()
    try:
        result = check(json.loads(args.batch.read_text()), json.loads(args.evidence.read_text()), GitEvidence(args.workspace))
    except (ValueError, KeyError, TypeError, AttributeError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({'state': 'blocked', 'reason': str(error)}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
