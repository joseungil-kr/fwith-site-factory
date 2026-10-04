#!/usr/bin/env python3
"""Prepare a deterministic, local-only reviewed v2 region bootstrap.

This deliberately has no network, commit, push, deployment, Airtable, content
writer or approval operation. The existing scheduled Creator consumes the bundle.
"""
import argparse
import ctypes
from datetime import datetime
import contextlib
import errno
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit

REPOSITORY = 'joseungil-kr/fwith-site-factory'
SITE_KEY = 'goyang-flower-v2'
LAUNCH_KEY = 'goyang-flower-v2-launch'
BRANCH = 'site-factory-goyang-v2'
ROOT = 'site-factory/goyang-flower'
TEMPLATE_KEY = 'flower-local-v2'
SOURCE_BRANCH = 'site-factory-flower-v2-template'
SOURCE_ROOT = 'site-factory/templates/flower-local-v2'
SOURCE_REVISION = '2ead40cecc0fe0925f69395e4798a35c0aec1894'
# Independently reviewed 54-file tree, not the source branch's mutable HEAD.
SOURCE_TREE = '52fa60037b12c0762dda16b61ab95c3fc62270b1'
SOURCE_COUNT = 54
STAGING_WORKER = 'goyang-flower-guide-qa'
PRODUCTION_PLACEHOLDER = 'goyang-flower-prod-disabled'
STAGING_URL = 'https://goyang-flower-guide-qa.joseungil.workers.dev'
SITE_URL = 'https://goyang.fwith.kr'
REGISTRY_PATH = '.github/site-factory-sites.json'
TEMPLATE_REGISTRY_PATH = '.github/site-factory-templates.json'
PROVENANCE_PATH = '.github/site-factory-provisioning/goyang-flower-v2.json'
ADAPTATIONS = {
    'src/data/site-config.json', 'src/data/architecture.json',
    'src/data/publish-manifest.json', 'src/data/page-map.json',
    'wrangler.staging.jsonc', 'wrangler.jsonc',
}
CATEGORY_TYPES = {
    'funeral': ['funeral-facility', 'order-help', 'price-guide'],
    'business': ['business-opening'], 'school': ['school-event'],
    'event': ['event-venue'],
    'gift': ['hospital-visit', 'personal-gift', 'station-transit'],
    'order': ['order-help', 'price-guide', 'message-guide'],
}
INITIAL_REGIONS = {'namyangju-flower-v2': '남양주', 'pyeongtaek-flower-v2': '평택', 'anyang-flower-v2': '안양'}
REGIONS = {'goyang-flower-v2': '고양', 'seongnam-flower-v2': '성남', 'bucheon-flower-v2': '부천', **INITIAL_REGIONS}
# A separate source profile leaves both existing bootstrap contracts unchanged.
BUCHEON_TEMPLATE_REGISTRY_KEY = 'flower-local-v2-bucheon-bootstrap-r1'
BUCHEON_SOURCE_TREE = '770d3f2d200d55ded378a649265cca3de81c130e'
BUCHEON_SOURCE_COUNT = 65
# Historical identities only. This table does not authorize new trial launches.
LEGACY_LAUNCH_KEYS = {
    SITE_KEY: LAUNCH_KEY,
    'seongnam-flower-v2': 'seongnam-flower-v2-trial-20261002',
    'bucheon-flower-v2': 'bucheon-flower-v2-trial-20261004',
}
# Independently reviewed clean runtime for the first three ordered initial sites.
# Registry-only declarations cannot self-approve a different source. Historical
# pins remain untouched and are never fallback initial-launch sources.
INITIAL_SOURCE_PROFILES = {site: {
    'registryKey': 'flower-local-v2-whole-initial-r2',
    'sourceRevision': 'cbf988f15527d951f72fa68391f6a03f84e29476',
    'sourceTree': '884abcbcbbc1d1f74095bb680e898e26c4498492',
    'sourceCount': 71,
} for site in INITIAL_REGIONS}
INITIAL_SOURCE_PROFILES['anyang-flower-v2'] = {
    'registryKey': 'flower-local-v2-whole-initial-r3-anyang',
    'sourceRevision': 'd7f7f15348c78d601356dcff2aaca2b3e426e216',
    'sourceTree': '08cd115e37f84014fcea8b708fa4d6cac74639a8',
    'sourceCount': 71,
}
INITIAL_SOURCE_ROOT = 'site-factory/templates/flower-local-v2-initial'
INITIAL_ADAPTATIONS = ADAPTATIONS | {'src/data/region-coverage.json', 'src/data/region-policy.json'}
INITIAL_MODES = ('whole-dong-initial', 'legacy-trial')
MEMBER_FIELDS = ('unit_key', 'name', 'district_key', 'page_key', 'intent_key', 'slug', 'route')


class ProvisionError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ProvisionError(message)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git(repo, *args, optional=False):
    # Ignore caller Git redirections/replacement objects and forbid promisor
    # lazy fetches: all source bytes must already be present locally.
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update(GIT_NO_REPLACE_OBJECTS='1', GIT_NO_LAZY_FETCH='1',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    run = subprocess.run(['git', '--no-optional-locks', '-C', str(repo), *args], capture_output=True, env=env)
    if run.returncode:
        if optional:
            return None
        raise ProvisionError('Git object read failed: ' + ' '.join(args) + '\n' + run.stderr.decode(errors='replace'))
    return run.stdout


def full_commit(repo, value):
    require(bool(re.fullmatch('[0-9a-f]{40}', value)), 'A full lowercase commit SHA is required')
    require(git(repo, 'cat-file', '-t', value).strip() == b'commit', 'Expected a commit object')
    return value


def safe_path(name):
    path = PurePosixPath(name)
    require(bool(name) and not path.is_absolute() and str(path) == name
            and all(p not in {'.', '..', '.git', 'node_modules', 'dist', '.astro'} for p in path.parts)
            and '\\' not in name and not any(ord(c) < 32 for c in name), 'Unsafe/untracked build path: ' + name)
    require(path.name != 'build-revision.json', 'Generated revision cannot be provisioned')
    return name


def read_tree(repo, revision, root):
    safe_path(root)
    rows = git(repo, 'ls-tree', '-rz', revision, '--', root).split(b'\0')
    files, manifest = {}, []
    for row in filter(None, rows):
        meta, raw_path = row.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        path = raw_path.decode('utf-8')
        require(path.startswith(root + '/'), 'Destination root is occupied by a non-directory')
        relative = safe_path(path[len(root) + 1:])
        require(mode == '100644' and kind == 'blob', 'Only regular non-executable source blobs are allowed: ' + path)
        require(relative not in files, 'Duplicate source path')
        data = git(repo, 'cat-file', 'blob', oid)
        # Verify bytes, even when Git is configured to use replacement objects.
        require(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == oid,
                'Source blob hash mismatch: ' + relative)
        files[relative] = data
        manifest.append({'path': relative, 'mode': mode, 'gitBlob': oid, 'sha256': sha256(data)})
    return files, manifest


def read_json(repo, revision, path):
    try:
        return json.loads(git(repo, 'show', revision + ':' + path))
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ProvisionError('Invalid JSON: ' + path) from error


def target_contract(site_key=SITE_KEY):
    require(site_key in REGIONS, 'Region is not in the reviewed v2 bootstrap allowlist')
    region_slug = site_key.split('-')[0]
    worker = region_slug + '-flower-guide-qa'
    return {'siteKey': site_key, 'region': REGIONS[site_key],
            'branch': 'site-factory-' + region_slug + '-v2', 'root': 'site-factory/' + region_slug + '-flower',
            'siteUrl': 'https://' + region_slug + '.fwith.kr', 'stagingWorker': worker,
            'productionWorker': region_slug + '-flower-prod-disabled',
            'stagingUrl': 'https://' + worker + '.joseungil.workers.dev',
            'provenancePath': '.github/site-factory-provisioning/' + site_key + '.json'}


def checked_launch_key(site_key, launch_key):
    if site_key == SITE_KEY:
        require(launch_key in (None, LAUNCH_KEY), 'Goyang launch identity is fixed')
        return LAUNCH_KEY
    require(isinstance(launch_key, str) and re.fullmatch(re.escape(site_key) + r'-trial-[a-z0-9][a-z0-9-]{0,50}', launch_key),
            'A distinct explicit regional trial launch key is required; legacy 30-page launch cannot be reused')
    return launch_key


def checked_json_bytes(raw, expected_hash, label):
    require(type(raw) is bytes, label + ' must be raw UTF-8 JSON bytes')
    require(isinstance(expected_hash, str) and re.fullmatch('[0-9a-f]{64}', expected_hash),
            label + ' requires an explicit lowercase raw-byte SHA-256')
    require(sha256(raw) == expected_hash, label + ' raw-byte hash mismatch')
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, label + ' has duplicate JSON object keys')
            result[key] = value
        return result
    def finite_float(value):
        number = float(value)
        require(math.isfinite(number), label + ' has a non-finite JSON number')
        return number
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=object_pairs, parse_float=finite_float,
                           parse_constant=lambda _: require(False, label + ' has a non-finite JSON number'))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ProvisionError(label + ' must be valid UTF-8 JSON') from error
    require(type(value) is dict, label + ' must be a JSON object')
    return value


def checked_initial_scope(site_key, launch_key, scope_key, membership_bytes, membership_sha256,
                          coverage_bytes, coverage_sha256):
    """Validate a declared complete set; never certify geography or approve content.

    The research bytes and schema-2 coverage bytes must be independently checked
    against current official sources before the existing Publisher can consume
    their exact hashes. Structural agreement alone is not a geographic review.
    """
    prefix = re.escape(site_key)
    require(isinstance(launch_key, str) and re.fullmatch(prefix + r'-initial-[0-9]{8}', launch_key),
            'A distinct explicit whole-dong initial launch key is required; no trial fallback')
    require(isinstance(scope_key, str) and re.fullmatch(prefix + r'-dong-coverage-[0-9]{8}', scope_key),
            'An explicit regional whole-dong scope key is required')
    require(launch_key[-8:] == scope_key[-8:], 'Initial launch and scope dates differ')
    try:
        datetime.strptime(scope_key[-8:], '%Y%m%d')
    except ValueError as error:
        raise ProvisionError('Invalid initial scope date') from error
    membership = checked_json_bytes(membership_bytes, membership_sha256, 'Membership')
    coverage = checked_json_bytes(coverage_bytes, coverage_sha256, 'Coverage')
    slug = site_key.split('-')[0]
    require(membership.get('schema') == slug + '-all-dong-membership-research-v1',
            'Unsupported explicit regional membership schema')
    require(membership.get('site_key') == site_key and membership.get('scope_key') == scope_key,
            'Membership site/scope identity mismatch')
    require(type(coverage.get('schemaVersion')) is int and coverage['schemaVersion'] == 2
            and coverage.get('siteKey') == site_key and coverage.get('scopeKey') == scope_key
            and coverage.get('membershipSourceSha256') == membership_sha256,
            'Coverage schema/site/scope/membership hash mismatch')
    require(membership.get('count_is_page_quota') is False and coverage.get('countIsPageQuota') is False,
            'Membership counts must not be page quotas')
    quota_keys = {'pageQuota', 'page_quota', 'targetPageCount', 'trialDetailTarget', 'first_detail_limit'}
    require(not quota_keys.intersection(membership) and not quota_keys.intersection(coverage),
            'Fixed page quotas and trial caps are forbidden in initial scope')
    require(membership.get('content_membership_approved') is False and membership.get('publication_approved') is False,
            'Initial membership must not grant content or publication approval')
    require(coverage.get('unitBasis') == 'legal-dong-plus-eup-myeon', 'Unsupported canonical unit basis')
    try:
        observed = datetime.fromisoformat(membership['prepared_at_utc'].replace('Z', '+00:00'))
        require(observed.tzinfo is not None, 'Membership observation must include timezone')
    except (KeyError, TypeError, AttributeError, ValueError) as error:
        raise ProvisionError('Membership requires an exact timezone-aware observation time') from error
    # Observation timestamps are evidence metadata, not an invented expiry.
    # Current official revisions/hashes must be compared at the release gate.
    official = membership.get('official_evidence')
    require(isinstance(official, list) and official, 'Official membership evidence is required')
    urls = []
    for source in official:
        require(type(source) is dict, 'Invalid official source')
        source_url = source.get('url', source.get('general_status_url'))
        require(isinstance(source_url, str), 'Invalid official source URL')
        url = urlsplit(source_url)
        require(url.scheme == 'https' and url.hostname and url.hostname.endswith('.go.kr')
                and not url.username and not url.password and not url.fragment, 'Official source must be an HTTPS government URL')
        urls.append(source_url)
    require(isinstance(coverage.get('officialSourceUrls'), list)
            and all(isinstance(url, str) for url in coverage['officialSourceUrls'])
            and set(coverage['officialSourceUrls']) == set(urls), 'Official source sets differ')
    members, units, representatives = membership.get('members'), coverage.get('units'), coverage.get('representatives')
    require(all(isinstance(value, list) and value for value in (members, units, representatives)),
            'Complete nonempty membership, units and representatives are required')
    identities = []
    for member in members:
        require(type(member) is dict and all(isinstance(member.get(k), str) and member[k].strip() == member[k]
                                             and member[k] for k in MEMBER_FIELDS), 'Malformed member identity')
        ident = {key: member[key] for key in MEMBER_FIELDS}
        require(re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*', ident['slug']), 'Unsafe member slug')
        require(ident['unit_key'].startswith(REGIONS[site_key] + '시/')
                and ident['page_key'] == site_key + '-region-' + ident['slug']
                and ident['route'] == '/regions/' + ident['slug'] + '/'
                and ident['intent_key'] == slug + '|flower-delivery|local-order|' + ident['slug'],
                'Member site/page/route/intent identity mismatch')
        identities.append(ident)
    for field in ('unit_key', 'page_key', 'intent_key', 'slug', 'route'):
        require(len({m[field] for m in identities}) == len(identities), 'Duplicate membership ' + field)
    by_unit = {m['unit_key']: m for m in identities}
    require(all(type(u) is dict and isinstance(u.get('unitKey'), str) for u in units), 'Malformed official unit')
    require(len({u['unitKey'] for u in units}) == len(units) and {u['unitKey'] for u in units} == set(by_unit),
            'Partial, extra or duplicate official unit membership')
    for unit in units:
        member = by_unit[unit['unitKey']]
        require(unit.get('name') == member['name'] and unit.get('districtKeys') == [member['district_key']]
                and unit.get('unitType') in ('legal-dong', 'eup', 'myeon'), 'Official unit identity mismatch')
    counts = membership.get('counts')
    require(type(counts) is dict and type(counts.get('legal_units')) is int
            and counts['legal_units'] == sum(u['unitType'] == 'legal-dong' for u in units),
            'Declared official legal-unit count differs from complete set')
    require(type(counts.get('eup_myeon_units', 0)) is int and counts.get('eup_myeon_units', 0)
            == sum(u['unitType'] in ('eup', 'myeon') for u in units), 'Official eup/myeon count differs')
    require(len(representatives) == len(identities), 'Partial representative membership')
    represented = []
    for representative in representatives:
        require(type(representative) is dict and type(representative.get('unitKeys')) is list
                and len(representative['unitKeys']) == 1 and isinstance(representative['unitKeys'][0], str)
                and representative['unitKeys'][0] in by_unit,
                'Every official unit requires one explicit canonical representative')
        member = by_unit[representative['unitKeys'][0]]
        require(all(representative.get(k) == member[v] for k, v in
                    (('pageKey', 'page_key'), ('slug', 'slug'), ('url', 'route'), ('intentKey', 'intent_key'))),
                'Representative identity differs from membership')
        require(representative.get('status') == 'candidate', 'Geographic representative must remain unapproved')
        represented.append(member['unit_key'])
    require(set(represented) == set(by_unit) and len(set(represented)) == len(represented),
            'Partial or duplicate representative membership')
    aliases, crosswalk = membership.get('administrative_alias_routes'), coverage.get('administrativeCrosswalk')
    require(isinstance(aliases, list) and isinstance(crosswalk, list), 'Explicit administrative crosswalk is required')
    def edges(rows, research):
        result, seen, relationships = set(), set(), set()
        for row in rows:
            require(type(row) is dict, 'Invalid administrative crosswalk row')
            key = row.get('administrative_unit_key' if research else 'aliasKey')
            require(isinstance(key, str) and key and key not in seen, 'Duplicate or missing administrative alias')
            seen.add(key)
            links = row.get('canonical_targets' if research else 'relations')
            require(isinstance(links, list) and links, 'Incomplete administrative alias relationships')
            for link in links:
                require(type(link) is dict, 'Invalid administrative alias relation')
                unit = link.get('unit_key' if research else 'unitKey')
                scope = link.get('scope')
                require(isinstance(unit, str) and unit in by_unit and scope in ('whole', 'partial'),
                        'Unknown administrative alias target/scope')
                relationship = (key, unit)
                require(relationship not in relationships, 'Duplicate administrative relationship, including contradictory whole/partial scope')
                relationships.add(relationship)
                exception = link.get('crossDistrictEvidence')
                result.add((key, unit, scope, json.dumps(exception, ensure_ascii=False, sort_keys=True)))
        return result
    require(edges(aliases, True) == edges(crosswalk, False), 'Partial or changed administrative crosswalk')
    for field, actual in (('administrative_units', len(aliases)),
                          ('administrative_legal_relations', len(edges(aliases, True)))):
        require(type(counts.get(field)) is int and counts[field] == actual, 'Declared crosswalk count mismatch')
    # No approval state is inherited from research, counts, registry or trials.
    return {
        'schemaVersion': 1, 'mode': 'whole-dong-initial', 'scopeKey': scope_key,
        'membershipSourceSha256': membership_sha256, 'coverageSha256': coverage_sha256,
        'membershipObservedAtUtc': membership['prepared_at_utc'],
        'unitBasis': coverage['unitBasis'], 'countIsPageQuota': False,
        'members': identities, 'memberIdentitySha256': sha256(json.dumps(identities, ensure_ascii=False,
                                    sort_keys=True, separators=(',', ':')).encode('utf-8')),
        'officialUnitCount': len(units), 'administrativeUnitCount': len(aliases),
        'officialSourceUrls': urls, 'preliminaryTrialRequired': False,
        'contentApprovalGranted': False, 'snapshotApprovalGranted': False,
        'finalBatchApprovalGranted': False, 'domainConnectionVerified': False,
        'productionReleaseApproved': False,
        'regionsRuntimeVerified': False, 'readyForContentSnapshots': False,
    }


def launch_scope(repo, target_revision, site_key, launch_key, scope_mode, **initial):
    require(scope_mode in (None,) + INITIAL_MODES, 'Unsupported initial scope mode')
    known = LEGACY_LAUNCH_KEYS.get(site_key)
    has_initial = any(value is not None for value in initial.values())
    # Preserve published historical invocations, including the original Goyang
    # default. Every other omitted mode selects whole coverage, never a trial.
    historical = known is not None and (launch_key == known or (site_key == SITE_KEY and launch_key is None))
    historical_resume = known is not None and target_revision != 'absent' and isinstance(launch_key, str) and bool(
        re.fullmatch(re.escape(site_key) + r'-trial-[a-z0-9][a-z0-9-]{0,50}', launch_key))
    if scope_mode is None:
        scope_mode = 'legacy-trial' if (historical or historical_resume) and not has_initial else 'whole-dong-initial'
    if scope_mode == 'legacy-trial':
        require(known is not None, 'This region has no historical trial; whole-dong initial scope is required')
        require(not has_initial, 'Legacy replay cannot consume initial membership')
        checked = checked_launch_key(site_key, launch_key)
        if not historical:
            require(target_revision != 'absent', 'New arbitrary trial launches are forbidden; use whole-dong initial scope')
            full_commit(repo, target_revision)
            previous = read_json(repo, target_revision, target_contract(site_key)['provenancePath'])
            require(previous.get('siteKey') == site_key and previous.get('launchKey') == checked
                    and 'initialScope' not in previous, 'Existing target has no matching bootstrap provenance')
        return checked, None
    return launch_key, checked_initial_scope(site_key, launch_key, **initial)


def site_entry(site_key=SITE_KEY, initial_scope=None):
    target = target_contract(site_key)
    entry = {
        'repo': REPOSITORY, 'branch': target['branch'], 'root': target['root'], 'siteUrl': target['siteUrl'],
        'primaryLandingSlug': '', 'heroPath': '', 'worker': target['productionWorker'],
        'launchMode': 'staging', 'productionEnabled': False,
        'naverVerification': '', 'indexnowKey': '', 'templateKey': TEMPLATE_KEY,
        'allowedCategories': list(CATEGORY_TYPES),
        'allowedPageTypes': list(dict.fromkeys(t for values in CATEGORY_TYPES.values() for t in values)),
        'categoryPageTypes': CATEGORY_TYPES, 'snapshotRenderer': 'structured-json-v12',
        'growthPaused': True, 'autoDeploySnapshots': False, 'graphScript': 'scripts/qa_graph.mjs',
        'stagingWranglerConfig': 'wrangler.staging.jsonc', 'stagingUrl': target['stagingUrl'],
        'requireRevisionApproval': True, 'requireSnapshotApproval': True,
        'approvedRevision': '', 'approvalEvidenceUrl': '',
    }
    if site_key != SITE_KEY:
        entry.update(stagingBuildIsolation=True, stagingWorker=target['stagingWorker'])
    if initial_scope is not None:
        entry['hubPolicy'] = 'child-threshold-v1'
        entry['initialLaunch'] = {key: initial_scope[key] for key in
            ('mode', 'scopeKey', 'membershipSourceSha256', 'coverageSha256', 'memberIdentitySha256', 'officialUnitCount')}
        entry['allowedCategories'].append('regions')
        entry['allowedPageTypes'].append('regional-service')
        entry['categoryPageTypes'] = {key: list(values) for key, values in CATEGORY_TYPES.items()}
        entry['categoryPageTypes']['regions'] = ['regional-service']
        entry['regionalService'] = {
            'enabled': False, 'scopeKey': initial_scope['scopeKey'],
            'definitionFile': 'src/data/region-coverage.json', 'policyFile': 'src/data/region-policy.json',
        }
    return entry


def validate_registry(registry, site_key=SITE_KEY, initial_scope=None):
    require(registry.get('schemaVersion') == 1 and isinstance(registry.get('sites'), dict),
            'Unsupported trusted site registry')
    target = target_contract(site_key)
    expected = site_entry(site_key, initial_scope)
    existing = registry['sites'].get(site_key)
    require(existing is None or existing == expected, 'Regional registry identity/policy collision; no overwrite')
    for key, site in registry['sites'].items():
        require(isinstance(site, dict), 'Malformed registered site: ' + key)
        if key == site_key:
            continue
        require(site.get('branch') != target['branch'], 'Protected/existing branch collision: ' + key)
        other_root = str(site.get('root', '')).strip('/')
        require(not other_root or not (other_root == target['root'] or target['root'].startswith(other_root + '/') or other_root.startswith(target['root'] + '/')),
                'Protected/existing root collision: ' + key)
        for field in ('siteUrl', 'stagingUrl'):
            require(str(site.get(field, '')).rstrip('/').lower() not in {target['siteUrl'].lower(), target['stagingUrl'].lower()},
                    'Registered URL collision: ' + key)
        for field in ('worker', 'stagingWorker'):
            require(site.get(field) not in {target['stagingWorker'], target['productionWorker']}, 'Registered Worker collision: ' + key)
    return existing is not None


def validate_empty(files, site_key):
    data = lambda name: json.loads(files['src/data/' + name + '.json'])
    require(data('pages') == [], 'Bootstrap must contain zero customer pages')
    for name in ('architecture', 'publish-manifest', 'page-map'):
        value = data(name)
        require(value['siteKey'] == site_key and value['pages'] == [], 'Nonempty or mismatched ' + name)
    require(data('publish-manifest')['snapshotLedger'] == {}, 'Snapshot ledger must be empty')
    architecture = data('architecture')
    require(architecture['home']['url'] == '/' and architecture['home']['pageRole'] == 'REGION_SERVICE_LANDING',
            'Unexpected home contract')
    require([h['category'] for h in architecture['hubs']] == list(CATEGORY_TYPES), 'Unexpected hubs')
    for hub in architecture['hubs']:
        require(hub['url'] == '/' + hub['category'] + '/' and hub['children'] == 0
                and hub['indexable'] is False and hub['menuVisible'] is False, 'Empty hub must remain hidden and noindex')
    config = data('site-config')
    require(config['siteKey'] == site_key and config['productionApproved'] is False and config['naverVerification'] == '',
            'Production/verification state must remain disabled')
    for name in ('wrangler.jsonc', 'wrangler.staging.jsonc'):
        conf = json.loads(files[name])
        require('route' not in conf and 'routes' not in conf and conf['workers_dev'] is True
                and conf['assets']['directory'] == './dist/', 'Worker must have no custom/production routes')
    require(json.loads(files['wrangler.jsonc'])['name'] != json.loads(files['wrangler.staging.jsonc'])['name'],
            'QA and production names must be distinct')


def adapt(source, site_key=SITE_KEY):
    validate_empty(source, 'template-only')
    target = target_contract(site_key)
    files = dict(source)
    for name in sorted(ADAPTATIONS):
        value = json.loads(files[name])
        if name.startswith('src/data/'):
            value['siteKey'] = site_key
            if name.endswith('/site-config.json'):
                value.update(region=target['region'], previewUrl=target['stagingUrl'], stagingWorker=target['stagingWorker'])
            elif name.endswith('/architecture.json'):
                value['home']['primaryKeyword'] = target['region'] + ' 꽃배달'
        else:
            value['name'] = target['stagingWorker'] if name == 'wrangler.staging.jsonc' else target['productionWorker']
        files[name] = encode(value)
    require({p for p in files if files[p] != source[p]} == ADAPTATIONS, 'Only the six reviewed adaptations are permitted')
    validate_empty(files, site_key)
    return files


def initial_coverage_template():
    return {'schemaVersion': 2, 'siteKey': 'template-only', 'scopeKey': '',
            'unitBasis': 'legal-dong-plus-eup-myeon', 'countIsPageQuota': False,
            'verifiedAt': '', 'sourceBasisDate': '', 'officialSourceUrls': [],
            'membershipSourceSha256': '', 'districts': [], 'units': [],
            'administrativeCrosswalk': [], 'representatives': []}


def initial_policy_template():
    return {'schemaVersion': 1, 'siteKey': 'template-only', 'scopeKey': '', 'enabled': False,
            'officialHosts': [], 'unitTypes': [], 'rulesRevision': '',
            'definitionFile': 'src/data/region-coverage.json', 'state': 'unbound-template',
            'membershipSourceSha256': '', 'visualBindings': []}


def initial_policy(coverage, source_revision):
    return {'schemaVersion': 1, 'siteKey': coverage['siteKey'], 'scopeKey': coverage['scopeKey'],
            'enabled': False, 'officialHosts': sorted({urlsplit(url).hostname for url in coverage['officialSourceUrls']}),
            'unitTypes': sorted({unit['unitType'] for unit in coverage['units']}),
            'rulesRevision': source_revision, 'definitionFile': 'src/data/region-coverage.json',
            'state': 'candidate-pending-independent-review',
            'membershipSourceSha256': coverage['membershipSourceSha256'], 'visualBindings': []}


def validate_initial_coverage_shape(coverage):
    """Additional schema-2 runtime shape. Geographic/content approval stays external."""
    require(isinstance(coverage.get('verifiedAt'), str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', coverage['verifiedAt'])
            and isinstance(coverage.get('sourceBasisDate'), str) and coverage['sourceBasisDate'].strip(),
            'Initial coverage requires recorded verification/source basis dates, without a TTL')
    try:
        datetime.strptime(coverage['verifiedAt'], '%Y-%m-%d')
    except ValueError as error:
        raise ProvisionError('Invalid coverage verification date') from error
    districts = coverage.get('districts')
    require(isinstance(districts, list) and districts, 'Initial runtime requires explicit districts')
    district_keys = set()
    for district in districts:
        require(type(district) is dict and isinstance(district.get('key'), str)
                and re.fullmatch('[a-z][a-z0-9-]*', district['key']) and district['key'] not in district_keys
                and isinstance(district.get('name'), str) and district['name'].strip()
                and district.get('sourceUrl') in coverage['officialSourceUrls'], 'Invalid/duplicate runtime district')
        district_keys.add(district['key'])
    for unit in coverage['units']:
        require(set(unit['districtKeys']) <= district_keys and isinstance(unit.get('legalRi'), list)
                and all(isinstance(name, str) and name.strip() for name in unit['legalRi']),
                'Invalid runtime unit district/legal-ri identity')
    for alias in coverage['administrativeCrosswalk']:
        require(isinstance(alias.get('name'), str) and alias['name'].strip()
                and alias.get('districtKey') in district_keys, 'Invalid runtime administrative alias')
        for relation in alias['relations']:
            unit = next(unit for unit in coverage['units'] if unit['unitKey'] == relation['unitKey'])
            require(alias['districtKey'] in unit['districtKeys'] or exact_cross_district_evidence(coverage, alias, unit, relation),
                    'Administrative alias district differs from its unit without exact reviewed exception evidence')
    keywords = set()
    for representative in coverage['representatives']:
        keyword = representative.get('primaryKeyword')
        require(isinstance(keyword, str) and keyword.strip() and keyword not in keywords
                and representative.get('queryEvidence') and representative.get('routeMode') == 'regional',
                'Initial runtime requires unique researched canonical representative queries')
        keywords.add(keyword)


def exact_cross_district_evidence(coverage, alias, unit, relation):
    """Structural recognition of one sourced exception; factual review stays external."""
    source = 'https://www.anyang.go.kr/main/downloadBbsFile.do?atchmnflNo=810157'
    evidence = relation.get('crossDistrictEvidence')
    return (coverage.get('siteKey') == 'anyang-flower-v2'
            and alias.get('aliasKey') == '안양시/동안구/행정동/비산1동' and alias.get('districtKey') == 'dongan'
            and unit.get('unitKey') == '안양시/만안구/법정동/안양동' and unit.get('districtKeys') == ['manan']
            and relation.get('scope') == 'partial' and source in coverage.get('officialSourceUrls', [])
            and type(evidence) is dict and set(evidence) == {'legalDistrictKey', 'administrativeDistrictKey', 'sourceUrl', 'sourceLocator', 'claim'}
            and evidence.get('legalDistrictKey') == 'manan' and evidence.get('administrativeDistrictKey') == 'dongan'
            and evidence.get('sourceUrl') == source
            and all(isinstance(evidence.get(field), str) and evidence[field].strip() for field in ('sourceLocator', 'claim')))


def validate_initial_empty(files, site_key, *, source_revision=None, initial_scope=None):
    architecture = json.loads(files['src/data/architecture.json'])
    require(isinstance(architecture.get('hubs'), list) and len(architecture['hubs']) == len(CATEGORY_TYPES) + 1,
            'Initial clean source requires exactly six legacy hubs plus regions')
    hub = architecture['hubs'][-1]
    require(hub.get('category') == 'regions' and hub.get('url') == '/regions/' and hub.get('children') == 0
            and hub.get('menuVisible') is False and hub.get('indexable') is False,
            'Empty initial regions hub must remain hidden and noindex')
    legacy = dict(files)
    architecture['hubs'] = architecture['hubs'][:-1]
    legacy['src/data/architecture.json'] = encode(architecture)
    validate_empty(legacy, site_key)
    coverage = json.loads(files['src/data/region-coverage.json'])
    policy = json.loads(files['src/data/region-policy.json'])
    if initial_scope is None:
        require(site_key == 'template-only' and coverage == initial_coverage_template()
                and policy == initial_policy_template(), 'Clean initial source must contain exact neutral unbound coverage/policy')
    else:
        require(coverage.get('siteKey') == site_key and coverage.get('scopeKey') == initial_scope['scopeKey']
                and sha256(files['src/data/region-coverage.json']) == initial_scope['coverageSha256'],
                'Initial target coverage must preserve the exact validated input bytes')
        validate_initial_coverage_shape(coverage)
        require(policy == initial_policy(coverage, source_revision),
                'Initial policy must remain exact disabled candidate with no visual approvals')


def adapt_initial(source, site_key, initial_scope, coverage_bytes, source_revision):
    validate_initial_empty(source, 'template-only')
    # Reuse the six historical transformations without relaxing their validator.
    legacy_source = dict(source)
    architecture = json.loads(source['src/data/architecture.json'])
    regions_hub = architecture['hubs'].pop()
    legacy_source['src/data/architecture.json'] = encode(architecture)
    files = adapt(legacy_source, site_key)
    architecture = json.loads(files['src/data/architecture.json'])
    architecture['hubs'].append(regions_hub)
    files['src/data/architecture.json'] = encode(architecture)
    files['src/data/region-coverage.json'] = coverage_bytes
    files['src/data/region-policy.json'] = encode(initial_policy(json.loads(coverage_bytes), source_revision))
    require({path for path in source if source[path] != files[path]} == INITIAL_ADAPTATIONS,
            'Only eight explicit initial adaptations are permitted')
    validate_initial_empty(files, site_key, source_revision=source_revision, initial_scope=initial_scope)
    return files


def manifest_for(files):
    return [{'path': name, 'sha256': sha256(data)} for name, data in sorted(files.items())]


def prepare(repo, control_revision, target_revision, site_key=SITE_KEY, launch_key=None, *,
            scope_mode=None, scope_key=None, membership_bytes=None, membership_sha256=None,
            coverage_bytes=None, coverage_sha256=None):
    target = target_contract(site_key)
    launch_key, initial_scope = launch_scope(repo, target_revision, site_key, launch_key, scope_mode,
        scope_key=scope_key, membership_bytes=membership_bytes, membership_sha256=membership_sha256,
        coverage_bytes=coverage_bytes, coverage_sha256=coverage_sha256)
    full_commit(repo, control_revision)
    template_registry = read_json(repo, control_revision, TEMPLATE_REGISTRY_PATH)
    require(template_registry.get('schemaVersion') == 1, 'Unsupported template registry')
    registry_key = TEMPLATE_KEY
    source_root = SOURCE_ROOT
    source_revision, source_tree, source_count = SOURCE_REVISION, SOURCE_TREE, SOURCE_COUNT
    initial_profile = None
    if initial_scope is not None:
        initial_profile = INITIAL_SOURCE_PROFILES.get(site_key)
        require(type(initial_profile) is dict, 'No explicitly reviewed runtime-ready clean initial profile for this site; no trial fallback')
        require(set(initial_profile) == {'registryKey', 'sourceRevision', 'sourceTree', 'sourceCount'},
                'Malformed reviewed initial source profile')
        registry_key = initial_profile['registryKey']
        source_root = INITIAL_SOURCE_ROOT
        source_revision, source_tree, source_count = (initial_profile[k] for k in
            ('sourceRevision', 'sourceTree', 'sourceCount'))
        require(isinstance(registry_key, str) and registry_key not in (TEMPLATE_KEY, BUCHEON_TEMPLATE_REGISTRY_KEY),
                'Initial profile must be distinct from historical trial profiles')
        require(isinstance(source_revision, str) and re.fullmatch('[0-9a-f]{40}', source_revision)
                and isinstance(source_tree, str) and re.fullmatch('[0-9a-f]{40}', source_tree)
                and type(source_count) is int and source_count > 0, 'Initial source must pin exact revision/tree/count')
    elif site_key == 'bucheon-flower-v2':
        registry_key = BUCHEON_TEMPLATE_REGISTRY_KEY
        entry = template_registry.get('templates', {}).get(registry_key)
        require(isinstance(entry, dict), 'Missing reviewed Bucheon source profile')
        source_revision = entry.get('sourceRevision')
        require(isinstance(source_revision, str) and bool(re.fullmatch('[0-9a-f]{40}', source_revision)),
                'Bucheon source profile requires an exact published commit')
        source_tree, source_count = BUCHEON_SOURCE_TREE, BUCHEON_SOURCE_COUNT
    expected_template = {'sourceBranch': SOURCE_BRANCH, 'sourceRoot': source_root,
                         'sourceRevision': source_revision, 'productionReady': False}
    if initial_profile is not None:
        expected_template.update(initialScopeMode='whole-dong-initial', regionsRuntimeReady=True,
                                 zeroCustomerContent=True, sourceTree=source_tree, sourceFileCount=source_count)
    require(template_registry.get('templates', {}).get(registry_key) == expected_template,
            'Trusted registry does not contain the exact reviewed source pin')
    full_commit(repo, source_revision)
    tree = git(repo, 'rev-parse', source_revision + ':' + source_root).decode().strip()
    require(tree == source_tree, 'Source tree differs from independently reviewed source')
    source, source_manifest = read_tree(repo, source_revision, source_root)
    require(len(source) == source_count, f'Expected exactly {source_count} tracked source files')
    files = (adapt_initial(source, site_key, initial_scope, coverage_bytes, source_revision)
             if initial_profile is not None else adapt(source, site_key))
    if initial_profile is not None:
        initial_scope['sourceRegionsRuntimeReviewed'] = True
        initial_scope['sourceTemplateRegistryKey'] = registry_key
    registry = read_json(repo, control_revision, REGISTRY_PATH)
    already_registered = validate_registry(registry, site_key, initial_scope)
    # A root accidentally present on main must never be silently overwritten.
    control_files, _ = read_tree(repo, control_revision, target['root'])
    require(not control_files, 'Target root already exists on control revision')
    provenance = {
        'schemaVersion': 1, 'kind': 'site-factory-infrastructure-bootstrap-v1',
        'siteKey': site_key, 'launchKey': launch_key, 'repository': REPOSITORY,
        'branch': target['branch'], 'root': target['root'],
        'templateKey': TEMPLATE_KEY, 'sourceBranch': SOURCE_BRANCH,
        'sourceRoot': source_root, 'sourceRevision': source_revision,
        'sourceTree': source_tree, 'sourceManifest': source_manifest,
        'sourceManifestSha256': sha256(encode(source_manifest)),
        'adaptedFiles': sorted(INITIAL_ADAPTATIONS if initial_scope is not None else ADAPTATIONS),
        'targetManifest': manifest_for(files),
        'customerPages': 0, 'snapshotApprovalGranted': False,
        'productionEnabled': False, 'growthPaused': True, 'autoDeploySnapshots': False,
    }
    if registry_key != TEMPLATE_KEY:
        provenance['sourceTemplateRegistryKey'] = registry_key
    if initial_scope is not None:
        provenance['initialScope'] = initial_scope
    elif site_key != SITE_KEY:
        provenance['trialDetailTarget'] = 1
    provenance['bootstrapId'] = sha256(encode(provenance))
    target_files = {target['root'] + '/' + name: data for name, data in files.items()}
    target_files[target['provenancePath']] = encode(provenance)
    # Caller must read branch existence remotely, then fetch the exact SHA.
    # Local refs provide a second collision guard, not remote absence evidence.
    known_refs = [git(repo, 'rev-parse', '--verify', ref, optional=True)
                  for ref in ('refs/heads/' + target['branch'], 'refs/remotes/origin/' + target['branch'])]
    if target_revision == 'absent':
        require(not any(known_refs), 'Target branch already exists locally; supply its exact remote revision')
        target_state = 'create'
    else:
        full_commit(repo, target_revision)
        require(all(ref is None or ref.decode().strip() == target_revision for ref in known_refs),
                'Observed target revision disagrees with a local branch/ref; refresh before retry')
        observed, _ = read_tree(repo, target_revision, target['root'])
        require(observed == files, 'Existing target differs from exact bootstrap; never overwrite customer content or conflicts')
        require(git(repo, 'show', target_revision + ':' + target['provenancePath'], optional=True) == encode(provenance),
                'Existing target has no matching bootstrap provenance')
        target_state = 'unchanged'
    registry['sites'][site_key] = site_entry(site_key, initial_scope)
    # Preserve the existing registry's ordering and formatting convention.
    proposed_registry = (json.dumps(registry, ensure_ascii=False, indent=2) + '\n').encode()
    plan = {
        'schemaVersion': 1, 'bootstrapId': provenance['bootstrapId'],
        'status': 'local_proposal_only', 'siteKey': site_key, 'launchKey': launch_key,
        'repository': REPOSITORY, 'controlRevision': control_revision,
        'expectedTargetRevision': target_revision, 'targetBranch': target['branch'],
        'targetState': target_state, 'registryState': 'unchanged' if already_registered else 'add',
        'sourceRevision': source_revision, 'sourceTree': source_tree,
        'targetFiles': manifest_for(target_files), 'registryPath': REGISTRY_PATH,
        'registrySha256': sha256(proposed_registry), 'customerPagesCreated': 0,
        'externalActionsPerformed': [],
        'publicationPreconditions': [
            'Cloudflare branch/build boundaries independently cleared by the parent',
            'Read current main and target refs; they must equal the expected revisions',
            'Recheck all registered and hosted Worker/route collisions before writing',
            'Use non-force optimistic Git updates; on races recompute from fresh control revision',
            'Commit only listed targetFiles to the target branch; registryPath alone to control main',
            'Actual reviewed Draft must later use the existing frozen Publisher and snapshot approval path',
        ],
    }
    if registry_key != TEMPLATE_KEY:
        plan['sourceTemplateRegistryKey'] = registry_key
    if initial_scope is not None:
        plan['initialScope'] = initial_scope
        plan['publicationPreconditions'].extend([
            'Independently compare current official revisions/hashes and complete member identities; timestamps do not impose a TTL and counts are not quotas',
            'Independently verify the prepared regions runtime and exact site scope bindings before accepting any Draft for publication',
            'Write and independently review the original body and local evidence for every member; never approve filler or omit failures',
            'Freeze exact approved payloads using the existing frozen Publisher and reconcile the complete final batch barrier',
            'Verify whole-site routes, aliases, canonical/robots/sitemap, graph, UI and intended fwith.kr domain connection',
            'Publish the complete initial site in one final batch only; no preliminary one-page trial',
        ])
    elif site_key != SITE_KEY:
        plan['trialDetailTarget'] = 1
    outputs = {'target-files/' + p: b for p, b in target_files.items()}
    outputs['control-files/' + REGISTRY_PATH] = proposed_registry
    outputs['provisioning-plan.json'] = encode(plan)
    return outputs, plan


def publish_directory(temporary, destination):
    """Atomic no-replace publication on the supported Linux execution hosts."""
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, 'renameat2', None)
    require(rename is not None, 'Atomic no-replace directory rename is unavailable; no output published')
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    # AT_FDCWD=-100; RENAME_NOREPLACE=1. A competing empty directory is a
    # collision too; ordinary Path.rename/os.rename would overwrite it.
    result = rename(-100, os.fsencode(temporary), -100, os.fsencode(destination), 1)
    if result:
        code = ctypes.get_errno()
        if code == errno.EEXIST:
            raise ProvisionError('Output was concurrently created; no overwrite')
        raise OSError(code, os.strerror(code), str(destination))


@contextlib.contextmanager
def anchored_parent(destination):
    """Keep writes beneath the checked directory even if its pathname moves."""
    require(hasattr(os, 'O_NOFOLLOW') and Path('/proc/self/fd').is_dir(),
            'Linux no-follow directory handles are required; no output published')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open('/', flags)
    try:
        for component in destination.parent.parts[1:]:
            next_fd = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        yield Path('/proc/self/fd') / str(fd)
    finally:
        os.close(fd)


def materialize(outputs, destination):
    destination = Path(os.path.abspath(destination))
    for path in outputs:
        safe_path(path)
    # Opening each parent with O_NOFOLLOW blocks both pre-existing symlinks
    # and parent-swap races. Paths below the retained fd stay on that directory.
    try:
        with anchored_parent(destination) as parent:
            anchored = parent / destination.name
            require(not anchored.is_symlink(), 'Symlink output path is forbidden')
            if anchored.exists():
                require(anchored.is_dir(), 'Output destination is occupied')
                found = {}
                for path in anchored.rglob('*'):
                    require(not path.is_symlink(), 'Symlink found in existing output')
                    if path.is_file():
                        found[path.relative_to(anchored).as_posix()] = path.read_bytes()
                    else:
                        require(path.is_dir(), 'Non-regular output entry')
                require(found == outputs, 'Output collision: remove nothing; choose a new empty destination')
                return False
            temporary = Path(tempfile.mkdtemp(prefix='.' + destination.name + '-', dir=parent))
            try:
                for name, data in sorted(outputs.items()):
                    path = temporary / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                current_parent = os.stat(destination.parent, follow_symlinks=False)
                held_parent = parent.stat()
                require((current_parent.st_dev, current_parent.st_ino) == (held_parent.st_dev, held_parent.st_ino),
                        'Output parent changed during preparation; no output published')
                publish_directory(temporary, anchored)
            finally:
                if temporary.exists():
                    shutil.rmtree(temporary)
            return True
    except OSError as error:
        if error.errno in (errno.ELOOP, errno.ENOTDIR):
            raise ProvisionError('Symlink or non-directory output parent is forbidden') from error
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--control-revision', required=True, help='Fresh full trusted main SHA, never a mutable ref')
    parser.add_argument('--target-revision', required=True, help='Fresh observed full target SHA, or explicit absent')
    parser.add_argument('--site-key', choices=sorted(REGIONS), default=SITE_KEY)
    parser.add_argument('--launch-key', help='New regional initial identity; known historical keys remain replay-compatible')
    parser.add_argument('--scope-mode', choices=INITIAL_MODES, help='New launches use whole-dong-initial; legacy-trial is historical replay only')
    parser.add_argument('--scope-key', help='Exact <site-key>-dong-coverage-YYYYMMDD identity')
    parser.add_argument('--membership-json', type=Path, help='Fresh complete official membership research JSON')
    parser.add_argument('--membership-sha256', help='Lowercase SHA-256 of exact membership file bytes')
    parser.add_argument('--coverage-json', type=Path, help='Schema-2 complete coverage JSON bound to membership hash')
    parser.add_argument('--coverage-sha256', help='Lowercase SHA-256 of exact coverage file bytes')
    output = parser.add_mutually_exclusive_group(required=True)
    output.add_argument('--output', type=Path, help='New bundle directory, or byte-identical prior output (Linux)')
    output.add_argument('--dry-run', action='store_true', help='Validate and print the proposal without writing files')
    args = parser.parse_args()
    try:
        outputs, plan = prepare(args.repo, args.control_revision, args.target_revision, args.site_key, args.launch_key,
            scope_mode=args.scope_mode, scope_key=args.scope_key,
            membership_bytes=args.membership_json.read_bytes() if args.membership_json else None,
            membership_sha256=args.membership_sha256,
            coverage_bytes=args.coverage_json.read_bytes() if args.coverage_json else None,
            coverage_sha256=args.coverage_sha256)
        if args.dry_run:
            print(json.dumps(plan, ensure_ascii=False, sort_keys=True))
            return
        written = materialize(outputs, args.output)
        print(json.dumps({'status': plan['status'], 'bootstrapId': plan['bootstrapId'],
                          'targetState': plan['targetState'], 'registryState': plan['registryState'],
                          'outputWritten': written, 'output': str(args.output)}, sort_keys=True))
    except (ProvisionError, KeyError, TypeError, json.JSONDecodeError, OSError) as error:
        parser.exit(1, 'PROVISIONING_BLOCKED: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
