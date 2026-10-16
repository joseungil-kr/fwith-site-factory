"""Trusted, provider-free checks of the fixed successor release and all 16 URLs.

No source execution. Only the exact existing managed robots prefix and single
Cloudflare beacon removal are permitted. Results are byte checks, never pixels.
"""
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import re
import stat
import xml.etree.ElementTree as ET

import indexnow_recovery as guard
import managed_robots
from beacon_normalization import strip_one_cf_beacon

SOURCE = '063e9eda9d33cb2f8b4dfd847bea966ff9443eb5'
ACTIVE = 'db5e090bdb87762ce7c7ec5c01f6ab73.txt'
LEGACY = '39c4ed924bc6084c670a963c26d9f018.txt'
EXPECTED_NAMES = frozenset({'index.html', '404.html', '_headers', 'robots.txt',
    'sitemap-index.xml', 'sitemap-0.xml', 'favicon.svg', ACTIVE, LEGACY,
    '_astro/CopyPage.iUxX7g7p.css', 'images/products/B060.jpg',
    'images/products/B201.jpg', 'images/products/B203.jpg', 'images/products/B205.jpg',
    'images/shared-banners/flower-budget.webp', 'images/shared-banners/flower-consultation.webp',
    'images/shared-banners/flower-message.webp'})
FIXED_ORIGINAL_NONHTML = {'robots.txt': 'd47b3053ab8722bd6de3e4a7f38022a0b9581c1811d0d5f48b0214437002c0b3', '_headers': '8732775eee770018db7d79d035a0163015a016de17ebbf8884902ec6d1d9fcf2', 'sitemap-0.xml': 'fe31bdd42fe7a68fbe1d990710352ea13433ddeb04974e5cba5f43f781d833b6', 'favicon.svg': '7ad52153b6e98b0b1a93bf546b2c1f3a9d9724a450703086fcedcb30fd05c3b4', '39c4ed924bc6084c670a963c26d9f018.txt': '5da3864d5327c6e4e41e6eef12510004b2302f55c3bc61593d7d49c1797739b5', 'sitemap-index.xml': '7514d38cc21218578a925bda9d3ccb112773cd9b7f560d6049bfd2fdd6d811a3', '_astro/CopyPage.iUxX7g7p.css': '833f9684e4b228e423465e2462796f1538dafa899b7d82a4e43478110aee441c', 'images/products/B205.jpg': '1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e', 'images/products/B201.jpg': '7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3', 'images/products/B060.jpg': 'a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3', 'images/products/B203.jpg': '0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114', 'images/shared-banners/flower-message.webp': 'a5ecdeb1914566a32d45b084351e2782fc8b234e9a4fbb8635a60a9921cac5f5', 'images/shared-banners/flower-consultation.webp': 'd6654aa44c365f64e330d0be2042972d3320fad54231425aaffca1dfdcd25ebc', 'images/shared-banners/flower-budget.webp': '081198095eb005603721be7c778f4d477f4dd93dcf96f0c261f18bf06bb91421'}
INHERITED_BODY_SHA256 = {'index.html': '284e1a5b1828ffdf503f2da22357d018a3e1e21b7835ab7d68e3023af00b30ce', '404.html': '190dce3da1a0258b91db84db839c4e11e8c83991bab92fbc732569db5b32db5c'}
require = guard.require
sha = guard.sha
LIMIT = 8 * 1024 * 1024


def read_file(path, limit=LIMIT):
    p = Path(path)
    require(p.is_file() and not p.is_symlink() and stat.S_ISREG(p.stat().st_mode),
            'regular_artifact_file_required')
    require(p.stat().st_size <= limit, 'artifact_file_too_large')
    raw = p.read_bytes()
    require(len(raw) <= limit, 'artifact_file_too_large')
    return raw


def file_inventory(root):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), 'regular_artifact_root_required')
    result = {}
    for p in root.rglob('*'):
        require(not p.is_symlink(), 'artifact_symlink_forbidden')
        require(p.is_dir() or (p.is_file() and stat.S_ISREG(p.stat().st_mode)),
                'artifact_special_file_forbidden')
        if p.is_file():
            key = p.relative_to(root).as_posix()
            require(re.fullmatch(r'[A-Za-z0-9_./-]+', key) is not None
                    and all(v not in ('', '.', '..') for v in key.split('/')), 'unsafe_artifact_name')
            result[key] = sha(read_file(p))
    require(len(result) <= 1000, 'artifact_file_count_limit')
    return result


class Metadata(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.meta = {}; self.canonical = []; self.og = []; self.images = []; self.links = []
        self.body_count = self.main_count = self.h1_count = 0
        self.feed(raw.decode('utf-8')); self.close()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        require(len(a) == len(attrs), 'duplicate_html_attribute')
        if tag == 'meta' and a.get('name'):
            name = a['name'].lower()
            require(name not in self.meta, 'duplicate_html_metadata')
            self.meta[name] = a.get('content', '')
        if tag == 'meta' and a.get('property') == 'og:url': self.og.append(a.get('content'))
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split():
            self.canonical.append(a.get('href'))
        if tag == 'img': self.images.append(a)
        if tag == 'a': self.links.append(a.get('href'))
        if tag == 'body': self.body_count += 1
        if tag == 'main': self.main_count += 1
        if tag == 'h1': self.h1_count += 1


def validate_html(raw, revision, missing=False):
    page = Metadata(raw)
    bodies = re.findall(rb'<body(?:\s[^>]*)?>.*?</body>', raw, re.S)
    require(len(bodies) == 1 and sha(bodies[0]) == INHERITED_BODY_SHA256['404.html' if missing else 'index.html'],
            'unchanged_customer_html_body_required')
    require(page.meta.get('site-factory-revision') == revision, 'html_revision_mismatch')
    tokens = set(re.split(r'\s*,\s*', page.meta.get('robots', '').lower()))
    require(tokens == ({'noindex', 'follow'} if missing else {'index', 'follow'}), 'html_robots_mismatch')
    for name in ('googlebot', 'bingbot', 'yeti', 'naverbot'):
        require(not re.search(r'\b(noindex|nofollow|none)\b', page.meta.get(name, ''), re.I),
                'html_search_agent_blocks_indexing')
    require(page.canonical == ([] if missing else [guard.HOME])
            and page.og == ([] if missing else [guard.HOME]), 'html_canonical_or_og_mismatch')
    require(page.body_count == 1 and page.main_count == 1 and page.h1_count == 1,
            'html_structure_mismatch')
    if not missing:
        require(len(page.images) == 7 and all(x.get('alt', '').strip() for x in page.images),
                'customer_image_scope_mismatch')
        require('tel:18440644' in page.links and all(
            'https://fwith.co.kr/shop/item.php?it_id=' + sku in page.links
            for sku in ('B201', 'B203', 'B205', 'B060')), 'customer_cta_mismatch')
    return page


def verify_release(dist, expected_files, revision=SOURCE):
    require(__debug__, 'optimized_python_forbidden')
    require(revision == SOURCE, 'successor_revision_required')
    require(type(expected_files) is dict and set(expected_files) == EXPECTED_NAMES
            and all(guard._valid_sha(v, 64) for v in expected_files.values()), 'exact_17_file_manifest_required')
    require(all(expected_files.get(k) == v for k, v in FIXED_ORIGINAL_NONHTML.items()),
            'unchanged_original_14_nonhtml_files_required')
    require(file_inventory(dist) == expected_files, 'artifact_file_bytes_mismatch')
    dist = Path(dist)
    require(expected_files[ACTIVE] == guard.ACTIVE_PROOF_SHA256
            and expected_files[LEGACY] == guard.RETAINED_PROOF_SHA256, 'both_proofs_required')
    require(read_file(dist / ACTIVE) == (ACTIVE[:-4] + '\n').encode()
            and read_file(dist / LEGACY) == (LEGACY[:-4] + '\n').encode(), 'proof_file_bytes_mismatch')
    validate_html(read_file(dist / 'index.html'), revision)
    validate_html(read_file(dist / '404.html'), revision, True)
    managed_robots.verify(read_file(dist / 'robots.txt'), expected_files['robots.txt'], guard.ORIGIN, [guard.HOME])
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    for name, root_tag, row_tag, wanted in (
        ('sitemap-index.xml', 'sitemapindex', 'sitemap', guard.ORIGIN + '/sitemap-0.xml'),
        ('sitemap-0.xml', 'urlset', 'url', guard.HOME)):
        raw = read_file(dist / name)
        require(b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(), 'unsafe_sitemap_xml')
        node = ET.fromstring(raw)
        require(node.tag == ns + root_tag and len(node) == 1 and node[0].tag == ns + row_tag,
                'exact_sitemap_graph_required')
        locs = node[0].findall(ns + 'loc')
        require(len(locs) == 1 and locs[0].text == wanted, 'exact_sitemap_location_required')
    return {'state': 'exact_successor_release_verified', 'revision': revision, 'files': 17,
            'filesSha256': guard.digest(expected_files), 'publicHttpVerified': False,
            'liveBrowserPixelsVerified': False}


def inventory(revision=SOURCE):
    require(revision == SOURCE, 'successor_revision_required')
    checks = [('/', 'index.html', 200)]
    checks += [('/' + name, name, 200) for name in sorted(EXPECTED_NAMES)
               if not name.endswith('.html') and name != '_headers']
    checks += [('/.damyang-release-missing-' + revision + '/', '404.html', 404)]
    require(len(checks) == 16, 'exact_16_public_checks_required')
    return checks


def checked_headers(response):
    require(type(response) is guard.RawResponse and type(response.status) is int
            and type(response.body) is bytes and len(response.body) <= LIMIT
            and type(response.headers) is list and len(response.headers) <= 100, 'invalid_public_response')
    result = {}
    for item in response.headers:
        require(type(item) is tuple and len(item) == 2 and all(type(x) is str for x in item),
                'invalid_public_response_header')
        name, value = item; name = name.lower()
        require(re.fullmatch(r'[a-z0-9-]{1,128}', name) is not None and len(value) <= 4096
                and '\r' not in value and '\n' not in value and name not in result,
                'duplicate_or_unsafe_public_header')
        result[name] = value
    require(not result.get('cf-mitigated', '').strip(), 'public_challenge_forbidden')
    require(result.get('content-encoding', 'identity').lower() in ('', 'identity'), 'compressed_public_response_forbidden')
    return result


def verify_public_response(path, name, status, response, expected_files, revision=SOURCE):
    require((path, name, status) in inventory(revision), 'fixed_public_response_identity_required')
    headers = checked_headers(response)
    require(response.status == status, 'public_http_status_mismatch')
    body = response.body; normalized = 'none'
    if name.endswith('.html'):
        require(re.fullmatch(r'text/html(?:;\s*charset=(?:utf-8|"utf-8"))?',
                headers.get('content-type', ''), re.I) is not None, 'public_html_content_type_mismatch')
        if name == 'index.html':
            require(not re.search(r'\b(noindex|nofollow|none)\b', headers.get('x-robots-tag', ''), re.I),
                    'public_home_header_blocks_search')
        if sha(body) != expected_files[name]:
            body = strip_one_cf_beacon(body, expected_files[name]); normalized = 'exact_existing_single_beacon'
        validate_html(body, revision, name == '404.html')
    elif name == 'robots.txt':
        managed_robots.verify_headers(headers)
        info = managed_robots.verify(body, expected_files[name], guard.ORIGIN, [guard.HOME])
        if info['managedComposites']:
            normalized = 'exact_existing_managed_robots_prefix'
            body = body[managed_robots.PREFIX_BYTES:]
    require(sha(body) == expected_files[name], 'public_bytes_mismatch')
    return {'path': path, 'file': name, 'httpStatus': response.status,
            'rawBodySha256': sha(response.body), 'rawBodyBytes': len(response.body),
            'artifactSha256': expected_files[name], 'normalization': normalized}


def verify_public_release(dist, expected_files, revision, get):
    verify_release(dist, expected_files, revision)
    evidence = []
    for path, name, status in inventory(revision):
        response = get(guard.ORIGIN + path)
        evidence.append(verify_public_response(path, name, status, response, expected_files, revision))
    return {'state': 'current_full_successor_public_verified', 'revision': revision,
            'checkedPaths': 16, 'status200': 15, 'status404': 1, 'checks': evidence,
            'liveBrowserPixelsVerified': False}
