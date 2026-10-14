"""Fail-closed LOCAL source contract; this module grants no publication permission.

The checked-in source record names the approved host/proof scope. The controller
remains separately unbound until the exact source and actual build are reviewed.
No network, proof/key creation, provider settings or credential operations occur.
"""
from pathlib import Path
import hashlib
import json
import os
import re
from urllib.parse import urlsplit

BASELINE_REVISION = '9f9c5abde306c5855104ea4ae58175a8da77496f'
SITE_KEY = 'seoul-gwanak-flower-direct'
WORKER = 'seoul-gwanak-flower-guide'
BUSINESS_ZONE = 'fwith.kr'
SITEMAP_ROUTES = {'/', '/regions/gwanak-funeral-wreath/', '/regions/gwanak-celebration-wreath/'}
CUSTOMER_ROUTES = SITEMAP_ROUTES | {'/regions/'}
UNBOUND = {
    'schemaVersion': 1, 'state': 'unbound', 'siteKey': SITE_KEY,
    'baselineSourceRevision': BASELINE_REVISION, 'origin': None, 'hostname': None,
    'configuredWorkerTarget': WORKER, 'providerExistenceVerified': False, 'approvedRuntimeDataSha256': None,
    'approvals': {'publication': False, 'hostBinding': False, 'indexNowProof': False},
    'evidenceReferences': {'publication': None, 'hostBinding': None, 'indexNowProof': None},
}


def read(path):
    return json.loads(Path(path).read_text())


def require(value, code):
    if not value:
        raise AssertionError(code)


def runtime_data_digest(root):
    """Bind data/assets. Publisher phases separately verify the tracked build-revision and all code bytes."""
    root = Path(root)
    files = {}
    for directory in ('src/data', 'public'):
        for path in sorted((root / directory).rglob('*')):
            require(not path.is_symlink(), 'release_symlink_forbidden')
            if path.is_file():
                rel = path.relative_to(root).as_posix()
                if rel in ('src/data/release-approval.json', 'src/data/build-revision.json'):
                    continue
                files[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    require(files, 'release_runtime_data_missing')
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_approval(approval, config, manifest, runtime_digest, environment):
    require(set(approval) == set(UNBOUND), 'release_binding_schema_mismatch')
    require(approval['schemaVersion'] == 1 and approval['state'] == 'approved', 'release_binding_unapproved')
    require(approval['siteKey'] == SITE_KEY and config['siteKey'] == SITE_KEY
            and manifest['siteKey'] == SITE_KEY, 'release_site_mismatch')
    require(approval['baselineSourceRevision'] == BASELINE_REVISION, 'release_baseline_mismatch')
    require(approval['configuredWorkerTarget'] == config['worker'] == WORKER, 'release_worker_mismatch')
    require(approval['providerExistenceVerified'] is False, 'release_unverified_provider_claim')
    require(approval['approvals'] == {key: True for key in UNBOUND['approvals']}, 'release_approval_missing')
    refs = approval['evidenceReferences']
    require(isinstance(refs, dict) and set(refs) == set(UNBOUND['evidenceReferences'])
            and all(isinstance(ref, str) and ref.strip() for ref in refs.values()), 'release_evidence_missing')
    hostname, origin = approval['hostname'], approval['origin']
    require(isinstance(hostname, str) and re.fullmatch(r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?[.]' + re.escape(BUSINESS_ZONE), hostname), 'release_hostname_unbound')
    require(origin == 'https://' + hostname, 'release_origin_mismatch')
    parsed = urlsplit(origin)
    require(parsed.scheme == 'https' and parsed.netloc == hostname and not parsed.path
            and not parsed.query and not parsed.fragment, 'release_origin_invalid')
    require(environment.get('SITE_URL') == origin, 'release_environment_origin_mismatch')
    require(re.fullmatch(r'[0-9a-f]{40}', environment.get('SITE_FACTORY_REVISION', '')), 'release_revision_required')
    require(config.get('productionApproved') is True and manifest['directRelease'].get('publicationAuthorized') is True,
            'release_source_not_approved')
    # Approval to create a proof does not mean the future public proof has been verified.
    require(config.get('hostnameOwnershipVerified') is False, 'release_unverified_ownership_claim')
    require(approval['approvedRuntimeDataSha256'] == runtime_digest
            and re.fullmatch(r'[0-9a-f]{64}', runtime_digest or ''), 'release_runtime_data_changed')
    require(manifest['directRelease']['plannedOriginalCount'] == 2, 'release_article_quota_changed')
    require(manifest['directRelease'].get('sitemapUrlCount') == 3
            and manifest['directRelease'].get('intrinsicIndexableRouteCount') == 3
            and manifest['directRelease'].get('renderedHtmlRouteCount') == 5, 'release_route_counts_mismatch')
    require({page['url'] for page in manifest['pages']} == SITEMAP_ROUTES - {'/'}, 'release_routes_changed')
    return origin


def resolve_mode(root, environment=None):
    root = Path(root)
    environment = os.environ if environment is None else environment
    value = environment.get('SITE_INDEXABLE', 'false')
    require(value in ('', 'false', 'true'), 'release_indexable_value_invalid')
    config = read(root / 'src/data/site-config.json')
    manifest = read(root / 'src/data/publish-manifest.json')
    approval = read(root / 'src/data/release-approval.json')
    requested = value == 'true'
    if approval == UNBOUND:
        require(config.get('productionApproved') is False
                and manifest['directRelease'].get('publicationAuthorized') is False
                and config.get('hostnameOwnershipVerified') is False, 'release_partial_activation')
        require(not requested, 'production_not_approved_unbound_release')
        origin = environment.get('SITE_URL') or config['previewUrl']
    else:
        origin = validate_approval(approval, config, manifest, runtime_data_digest(root), environment)
    return {'indexable': requested, 'origin': origin.rstrip('/'),
            'robots': lambda route: expected_robots(route, requested)}


def expected_robots(route, indexable):
    require(route in CUSTOMER_ROUTES | {'/404.html'}, 'release_unknown_route')
    if not indexable or route == '/404.html':
        return 'noindex,nofollow,noarchive'
    return 'noindex,follow' if route == '/regions/' else 'index,follow'


def validate_search_output(dist, origin, indexable):
    """Exact mode-aware sitemap, robots and response-header contract."""
    import xml.etree.ElementTree as ET
    dist = Path(dist)
    entries = []
    for path in sorted(dist.glob('sitemap*.xml')):
        tree = ET.parse(path)
        root_name = tree.getroot().tag.rsplit('}', 1)[-1]
        require(root_name in ('sitemapindex', 'urlset'), 'release_sitemap_root_invalid')
        locs = [(el.text or '').strip() for el in tree.iter() if el.tag.rsplit('}', 1)[-1] == 'loc']
        if root_name == 'sitemapindex':
            for loc in locs:
                parsed = urlsplit(loc)
                require(loc.startswith(origin + '/') and parsed.path.endswith('.xml')
                        and not parsed.query and not parsed.fragment, 'release_sitemap_index_foreign')
                require((dist / parsed.path.lstrip('/')).is_file(), 'release_sitemap_child_missing')
        else:
            entries.extend(locs)
    wanted = {origin + route for route in SITEMAP_ROUTES} if indexable else set()
    require(len(entries) == len(set(entries)) and set(entries) == wanted, 'release_sitemap_exact_routes_mismatch')
    wanted_robots = ['User-agent: *', 'Allow: /', 'Sitemap: ' + origin + '/sitemap-index.xml'] if indexable else ['User-agent: *', 'Disallow: /']
    actual_robots = [line.strip() for line in (dist / 'robots.txt').read_text().splitlines() if line.strip()]
    require(actual_robots == wanted_robots, 'release_robots_txt_mismatch')
    headers = (dist / '_headers').read_text()
    if indexable:
        require(not re.search(r'^\s*X-Robots-Tag:.*\b(noindex|nofollow|none)\b', headers, re.I | re.M), 'release_blocking_header')
    else:
        require('X-Robots-Tag: noindex, nofollow, noarchive' in headers, 'release_preview_header_missing')
    return len(entries)


if __name__ == '__main__':
    result = resolve_mode(Path(__file__).resolve().parents[1])
    print('SOURCE BOUNDARY VERIFIED: ' + ('production binding' if result['indexable'] else 'preview/noindex') + '; publication not performed')
