#!/usr/bin/env python3
"""Capture a pinned Gokseong production dist on a permitted runner, without publishing.

Prepared locally only: this module does not launch anything when imported. Runtime
requires Node 24, installed Playwright Chromium and permission to open loopback
sockets. It never substitutes a synthetic 404 server or weakens the browser sandbox.
The capture machine's checks cannot approve an independent review of the pixels.

Reused from the current Damyang controller at main2595fac, preserving runner integrity and evidence
guards; Gokseong expectations are read from its own runtime and frozen JSON.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

SOURCE_ROOT = 'site-factory/gokseong-flower'
ROOT = SOURCE_ROOT + '/candidate'
ORIGIN = 'https://gokseong.fwith.kr'
ROUTES = ('/', '/404.html')
SECTIONS = ('products', 'budget', 'ribbon', 'destinations', 'order')
ANCHORS = ('products', 'budget', 'ribbon', 'order', 'faq')
REFERENCE_TOTALS = (69000, 89000, 119000, 159000)
WIDTHS = (320, 390, 1280)
HEIGHT = 900
MISSING = '/does-not-exist-gokseong-production-capture/'
PRODUCTS = ('B201', 'B203', 'B205', 'B060')
BANNERS = ('message', 'budget', 'consultation')
DIRECTORY = Path(__file__).resolve().parent
FROZEN_INPUT_SHA256 = {
    'customer-copy.json': '3829721f442682c7b07f02b043b5ba80a0e1e0d5264babb7c96a7b2eadd0332e',
    'render-plan.json': '0ef1ba508743a560d04a8217fbd9a35d80569f6808c3603367da2f7db2293b67',
    'output-context-map.json': 'fd3246be4a868f35d8ffdc82a64e37d3b9643af6600b462808fcf11b1731364f',
    'visible-strings.json': '9eefabed14d337939077a88c23ae4e2b50324b8343a3116074b204d9b1342631',
}
OCCURRENCE_STATES = tuple(
    {'id': str(width) + '-' + label, 'width': width, 'menuOpen': label == 'open',
     'skipFocused': label == 'skip-focused'}
    for width in WIDTHS
    for label in (('closed', 'open', 'skip-focused') if width <= 860 else ('normal', 'skip-focused'))
)


def validate_occurrence_contract(copy, mapping, visible):
    """Validate the frozen 102 leaves / 119 logical occurrences, not browser evidence."""
    require(mapping.get('schema') == 'single-home-output-context-map/v2'
            and mapping.get('authoredLeafCount') == 102 and len(mapping.get('contexts', [])) == 102,
            'exact_102_authored_leaf_contexts_required')
    require(mapping.get('states') == list(OCCURRENCE_STATES), 'exact_eight_occurrence_states_required')
    require(mapping.get('copySHA256') == FROZEN_INPUT_SHA256['customer-copy.json']
            and mapping.get('renderPlanSHA256') == FROZEN_INPUT_SHA256['render-plan.json'],
            'occurrence_copy_and_plan_binding_required')
    require(visible.get('count') == 102 and visible.get('rows') == mapping['contexts'],
            'visible_strings_and_occurrence_contexts_differ')
    pointers, identities, total = set(), set(), 0
    for row in mapping['contexts']:
        pointer = row['pointer']
        require(pointer not in pointers, 'duplicate_authored_leaf_pointer')
        pointers.add(pointer)
        value = copy
        for part in pointer.lstrip('/').split('/'):
            part = part.replace('~1', '/').replace('~0', '~')
            value = value[int(part)] if isinstance(value, list) else value[part]
        require(type(value) is str and value == row['text'], 'occurrence_source_leaf_differs:' + pointer)
        for occurrence in row['occurrences']:
            total += 1
            require(type(occurrence['expectedDOMMatchesPerPage']) is int
                    and occurrence['expectedDOMMatchesPerPage'] == 1
                    and occurrence['extraction'] in ('textContent', 'attribute:content', 'attribute:alt', 'attribute:aria-label')
                    and set(occurrence['layoutAvailableByState']) == {s['id'] for s in OCCURRENCE_STATES}
                    and all(type(v) is bool for v in occurrence['layoutAvailableByState'].values()),
                    'invalid_exact_occurrence_shape')
            require(occurrence['pageIds'] and set(occurrence['pageIds']) <= {'home', 'notFound'}
                    and len(set(occurrence['pageIds'])) == len(occurrence['pageIds']), 'invalid_occurrence_pages')
            for page_id in occurrence['pageIds']:
                identity = (pointer, occurrence['selector'], occurrence['extraction'], page_id)
                require(identity not in identities, 'duplicate_exact_occurrence_identity')
                identities.add(identity)
    require(total == 119 and len(identities) == 143, 'exact_119_logical_143_expanded_occurrences_required')
    supplemental = mapping.get('supplementalTechnicalIdentifiers', [])
    require(len(supplemental) == 4 and [r['value'] for r in supplemental] == list(PRODUCTS),
            'exact_four_supplemental_skus_required')
    for index, row in enumerate(supplemental):
        product = copy['productCards'][index]
        require(row['pointer'] == '/productCards/' + str(index) + '/sku'
                and row['pageIds'] == ['home'] and row['selector'] == '#product-' + product['sku'] + ' > h3'
                and row['requiredTag'] == 'H3' and row['expectedDOMMatchesPerPage'] == 1
                and row['expectedExtractedText'] == product['name'] + ' ' + product['sku']
                and row['authoredProse'] is False and row['countedIn102'] is False,
                'supplemental_sku_projection_differs')
    return True


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def inventory(directory):
    directory = Path(directory)
    require(directory.is_dir() and not directory.is_symlink(), 'inventory_directory_missing_or_symlink')
    result = {}
    for path in sorted(directory.rglob('*')):
        require(not path.is_symlink(), 'inventory_symlink_forbidden:' + str(path))
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = {'sha256': sha(path), 'bytes': path.stat().st_size}
    return result


def clean_environment(environ):
    """Only non-secret process essentials; never inherit release/provider credentials.

    Astro preview evaluates the original private config. Release variables must not
    leak into it; production metadata is already sealed into the existing dist.
    """
    allow = ('PATH', 'HOME', 'TMPDIR', 'TMP', 'TEMP', 'SYSTEMROOT', 'LANG', 'LC_ALL', 'TZ')
    env = {key: environ[key] for key in allow if key in environ}
    env.update({'CI': 'true', 'ASTRO_TELEMETRY_DISABLED': '1', 'NO_COLOR': '1'})
    return env


def reject_provider_credentials(environ):
    prefixes = ('CLOUDFLARE_', 'CF_API_', 'AWS_', 'AZURE_', 'VERCEL_', 'NETLIFY_',
                'FLY_API_', 'DIGITALOCEAN_', 'GOOGLE_APPLICATION_CREDENTIALS', 'GCP_')
    require(not any(value and key.startswith(prefixes) for key, value in environ.items()),
            'provider_credentials_forbidden_in_capture_environment')


def same_origin(url, origin):
    try:
        left, right = urlsplit(url), urlsplit(origin)
        return (left.scheme, left.hostname, left.port) == (right.scheme, right.hostname, right.port) and not left.username and not left.password
    except ValueError:
        return False


def source_binding(checkout, gate_result):
    """Hash actual tracked source bytes and actual output, not a claimed PASS flag."""
    checkout = Path(checkout).resolve()
    files = subprocess.run(['git', 'ls-files', '-z', '--', SOURCE_ROOT], cwd=checkout,
                           env=clean_environment(os.environ), capture_output=True, check=True).stdout
    tracked = {}
    for raw in files.split(b'\0'):
        if not raw:
            continue
        name = raw.decode('utf-8')
        path = checkout / name
        require(name.startswith(SOURCE_ROOT + '/') and path.is_file() and not path.is_symlink(),
                'tracked_source_file_invalid')
        tracked[name] = {'sha256': sha(path), 'bytes': path.stat().st_size}
    require(tracked, 'tracked_source_inventory_empty')
    return {'gate': gate_result, 'trackedSource': tracked,
            'dist': inventory(checkout / ROOT / 'dist'),
            'control': {name: sha(DIRECTORY / name) for name in (
                'production_capture.py', 'production_build.py',
                'production-source-contract.json', 'production-binding.json')}}


def expected_social(page, alt):
    """Exact metadata emitted by the reviewed Gokseong release adapter."""
    if page['path'] == '/404.html':
        return []
    content = page['content']
    image = ORIGIN + '/images/products/B201.jpg'
    og = [('og:type', 'website'), ('og:title', content['title']),
          ('og:description', content['metaDescription']), ('og:locale', 'ko_KR'),
          ('og:url', ORIGIN + page['path']), ('og:image', image),
          ('og:image:width', '500'), ('og:image:height', '500'),
          ('og:image:alt', alt)]
    twitter = [('twitter:card', 'summary'), ('twitter:title', content['title']),
               ('twitter:description', content['metaDescription']), ('twitter:image', image),
               ('twitter:image:alt', alt)]
    return ([{'attribute': 'property', 'name': key, 'content': value} for key, value in og]
            + [{'attribute': 'name', 'name': key, 'content': value} for key, value in twitter])


def reviewed_blocks(copy, key):
    """Independent exact JSON-to-DOM text projection, including list and afterList."""
    content, blocks = copy[key], []
    def add(tag, text):
        blocks.append({'tag': tag.upper(), 'text': text})
    add('h1', content['h1'])
    if key == 'notFound':
        add('p', content['body'])
        add('a', content['cta']['label'])
        return blocks
    for text in content['lead']:
        add('p', text)
    for section in content['sections']:
        add('h2', section['h2'])
        for text in section['paragraphs']:
            add('p', text)
        if section['id'] == 'products':
            for product in copy['productCards']:
                add('h3', product['name'] + ' ' + product['sku'])
                for field in ('priceLabel', 'shippingLabel', 'referenceTotalLabel', 'description'):
                    add('p', product[field])
                add('a', product['ctaLabel'])
            add('p', copy['sharedUI']['productSampleNotice'])
        for text in section.get('list', []):
            add('li', text)
        for text in section.get('afterList', []):
            add('p', text)
    add('h2', content['faqHeading'])
    for faq in content['faq']:
        add('h3', faq['question'])
        add('p', faq['answer'])
    add('p', content['closing'])
    add('a', content['cta']['label'])
    add('h2', content['sourceHeading'])
    add('p', content['sourceIntro'])
    for row in content['sources']:
        add('a', row['label'])
    return blocks


def validate_native_contract(copy, plan, navigation):
    require(type(copy) is dict and list(copy) == ['home', 'productCards', 'notFound', 'sharedUI', 'sharedBannerAlt'],
            'exact_five_key_home_schema_required')
    home = copy['home']
    require([s.get('id') for s in home['sections']] == list(SECTIONS)
            and not any('card' in s for s in home['sections']), 'exact_reviewed_home_section_order_required')
    require(home['sections'][0]['productCardIds'] == list(PRODUCTS), 'exact_home_product_ids_required')
    require(len(home['faq']) == 3 and len({f['question'] for f in home['faq']}) == 3, 'exact_three_faqs_required')
    require(tuple(p['sku'] for p in copy['productCards']) == PRODUCTS, 'four_exact_products_required')
    for index, product in enumerate(copy['productCards']):
        require(type(product['basePriceKRW']) is int and type(product['additionalShippingKRW']) is int
                and type(product['referenceTotalKRW']) is int
                and product['basePriceKRW'] == REFERENCE_TOTALS[index] - 10000
                and product['additionalShippingKRW'] == 10000
                and product['referenceTotalKRW'] == product['basePriceKRW'] + product['additionalShippingKRW']
                and product['finalPriceKRW'] is None, 'exact_reference_price_arithmetic_required')
        require(product['priceLabel'] == f"상품 기본가 {product['basePriceKRW']:,}원"
                and product['shippingLabel'] == '곡성 게시 추가배송비 10,000원'
                and product['referenceTotalLabel'] == f"게시금액 합산 참고예산 {product['referenceTotalKRW']:,}원",
                'exact_reviewed_price_labels_required')
    required_plan = [{'labelSource': 'sharedUI.' + anchor + 'Link', 'href': '/#' + anchor} for anchor in ANCHORS]
    require(plan['navigation']['mainMenu'] == required_plan, 'exact_reviewed_anchor_plan_required')
    require(navigation == [{'label': copy['sharedUI'][row['labelSource'].split('.')[1]], 'href': row['href']}
                           for row in required_plan], 'exact_reviewed_anchor_navigation_required')
    require([(p['id'], p['proposedPath']) for p in plan['pages']] == [('home', '/'), ('notFound', '/404.html')],
            'two_exact_planned_routes_required')
    return True


def capture_inputs(root):
    """Read actual frozen Gokseong runtime and reviewed inputs; no build or launch."""
    root = Path(root).resolve()
    inputs = root.parent / 'inputs/reviewed-copy'
    for name, digest in FROZEN_INPUT_SHA256.items():
        require(sha(inputs / name) == digest, 'frozen_capture_input_bytes_changed:' + name)
    command = ['node', '--input-type=module', '-e',
        "import {copy,pages,products,home,ui,plan,navigation,banners,mapTarget} from './src/lib/gokseong-runtime.mjs';console.log(JSON.stringify({copy,pages,products,home,ui,plan,navigation,banners,notFoundHref:mapTarget(copy.notFound.cta)}));"]
    run = subprocess.run(command, cwd=root, env=clean_environment(os.environ), capture_output=True, text=True, check=True)
    data = json.loads(run.stdout)
    original, products, home, ui = data['pages'], data['products'], data['home'], data['ui']
    validate_native_contract(data['copy'], data['plan'], data['navigation'])
    occurrence_map = json.loads((inputs / 'output-context-map.json').read_text())
    validate_occurrence_contract(data['copy'], occurrence_map, json.loads((inputs / 'visible-strings.json').read_text()))
    require([(p['id'], p['copyKey'], p['path']) for p in original] == [('home', 'home', '/'), ('not-found', 'notFound', '/404.html')],
            'two_exact_routes_required')
    require(products == data['copy']['productCards'] and home == data['copy']['home'] and ui == data['copy']['sharedUI'],
            'runtime_copy_exports_differ')
    asset_manifest = json.loads((inputs / 'asset-manifest.json').read_text())
    assets = reviewed_product_assets(asset_manifest)
    product_cards = []
    for product, asset in zip(products, assets):
        require(asset['path'] == product['localPhoto'] and asset['publicPath'] == '/images/products/' + product['sku'] + '.jpg', 'exact_product_asset_mapping_required')
        require(sha(root / 'dist/images/products' / (product['sku'] + '.jpg')) == asset['sha256'], 'frozen_product_image_bytes_changed:' + product['sku'])
        product_cards.append({'sku': product['sku'], 'photoSHA256': asset['sha256'],
            'name': product['name'] + ' ' + product['sku'], 'priceText': product['priceLabel'],
            'shippingText': product['shippingLabel'], 'referenceText': product['referenceTotalLabel'],
            'referenceTotalKRW': product['referenceTotalKRW'], 'description': product['description'], 'alt': product['photoAlt'],
            'cta': {'href': product['ctaHref'], 'label': product['ctaLabel'], 'accessibleLabel': None}})
    require(tuple(b['variant'] for b in data['banners']) == BANNERS, 'exact_three_banners_required')
    banners = []
    for banner in data['banners']:
        require(sha(root / 'dist' / banner['renderSrc'].lstrip('/')) == banner['sha256'], 'frozen_banner_image_bytes_changed:' + banner['variant'])
        banners.append({'variant': banner['variant'], 'src': banner['renderSrc'], 'alt': banner['alt'],
                        'sha256': banner['sha256'], 'width': banner['width'], 'height': banner['height']})
    chrome = {'skipLink': [{'label': ui['skipLink'], 'href': '#main-content'}],
              'brand': [{'label': ui['brand'], 'href': '/'}],
              'footer': [{'label': ui['phoneLink'], 'href': 'tel:18440644'}, {'label': ui['homeLink'], 'href': '/'}],
              'mobileBar': [{'label': ui['homeLink'], 'href': '/'}, {'label': ui['phoneLink'], 'href': 'tel:18440644'}]}
    pages = []
    for original_page in original:
        route, key = original_page['path'], original_page['copyKey']
        primary, content = route == '/', data['copy'][key]
        ctas = [{'label': content['cta']['label'], 'href': content['cta']['href'] if primary else data['notFoundHref']}]
        required_ctas = ([{'label': p['cta']['label'], 'href': p['cta']['href']} for p in product_cards] if primary else []) + ctas
        page = {'id': original_page['id'], 'path': route,
            'documentSHA256': sha(root / 'dist' / ('index.html' if primary else '404.html')),
            'content': {'h1': content['h1'], 'title': content['title'], 'metaDescription': content['description'],
                        'firstAnswer': content['lead'][0] if primary else None},
            'productCardIds': list(PRODUCTS) if primary else [], 'faqIds': list(range(3)) if primary else [],
            'breadcrumbVisible': False, 'breadcrumbs': [], 'breadcrumbAriaLabel': None,
            'ctas': ctas, 'requiredCtas': required_ctas,
            'internalLinks': [] if primary else ctas, 'contentCards': [],
            'navigation': data['navigation'], 'chromeLinks': chrome,
            'reviewedBlocks': reviewed_blocks(data['copy'], key),
            'sections': list(SECTIONS) if primary else [],
            'mainLinks': required_ctas + ([{'label': row['label'], 'href': row['url']} for row in home['sources']] if primary else [])}
        page['socialMetadata'] = expected_social(page, products[0]['photoAlt'])
        pages.append(page)
    return pages, {'pages': pages, 'productCards': product_cards, 'faqs': home['faq'], 'banners': banners,
                   'occurrenceMap': occurrence_map,
                   'occurrenceMapSHA256': sha(inputs / 'output-context-map.json'),
                   'visibleStringsSHA256': sha(inputs / 'visible-strings.json'),
                   'productSampleNotice': ui['productSampleNotice'], 'menuOpen': ui['menuOpen'], 'menuClose': ui['menuClose'],
                   'navigation': data['navigation'],
                   'sourceSpecSHA256': sha(root.parent / 'inputs/required-originals.json'),
                   'customerCopySHA256': sha(root.parent / 'inputs/reviewed-copy/customer-copy.json'),
                   'renderPlanSHA256': sha(root.parent / 'inputs/reviewed-copy/render-plan.json')}


def reviewed_product_assets(manifest):
    """Gokseong's original manifest has seven assets, sorted by path, not SKU order."""
    assets = manifest.get('assets', [])
    require(manifest.get('schema') == 'customer-copy-assets/v1' and manifest.get('count') == 7
            and len(assets) == 7 and len({a.get('path') for a in assets}) == 7,
            'exact_seven_asset_manifest_required')
    products = [asset for asset in assets if 'sku' in asset]
    require(len(products) == 4 and {a['sku'] for a in products} == set(PRODUCTS), 'exact_four_product_assets_required')
    by_sku = {asset['sku']: asset for asset in products}
    return [by_sku[sku] for sku in PRODUCTS]


def metadata_issues(metrics, expected, revision):
    route = expected['path']
    issues = []
    targets = {'robots': ['index,follow' if route == '/' else 'noindex,follow'],
               'canonical': [] if route == '/404.html' else [ORIGIN + route],
               'ogUrl': [] if route == '/404.html' else [ORIGIN + route],
               'revision': [revision], 'h1': [expected['content']['h1']]}
    for name, target in targets.items():
        if metrics.get(name) != target:
            issues.append('Exact metadata mismatch: ' + name)
    if metrics.get('socialMetadata') != expected['socialMetadata']:
        issues.append('Exact OG/Twitter metadata differs from Gokseong release contract')
    if route == '/404.html' and (metrics.get('ogProperties') or metrics.get('socialMetadata')):
        issues.append('404 contains social metadata')
    if metrics.get('title') != expected['content']['title'] or metrics.get('description') != [expected['content']['metaDescription']]:
        issues.append('Title or description differs from frozen source')
    return issues


def expected_inventory(pages):
    require(len(pages) == 2 and [p['path'] for p in pages] == list(ROUTES), 'exact_two_page_capture_inventory_required')
    return {(route, width) for route in ROUTES for width in WIDTHS}


def validate_capture_coverage(report, pages):
    """Pure exact-multiplicity check; duplicate records never count as coverage.

    Report order is immaterial. Every page/viewport pair occurs once, and each
    flow/real-404 group contains exactly one record for each approved integer width.
    Malformed records fail closed rather than being silently deduplicated.
    """
    expected = expected_inventory(pages)
    groups, issues = {}, []
    for group in ('pages', 'flows', 'unknownPath'):
        rows = report.get(group)
        valid_list = type(rows) is list
        rows = rows if valid_list else []
        keys, malformed = [], not valid_list
        for row in rows:
            if type(row) is not dict or type(row.get('width')) is not int:
                malformed = True
                continue
            if group == 'pages':
                if type(row.get('route')) is not str:
                    malformed = True
                    continue
                keys.append((row['route'], row['width']))
            else:
                if group == 'unknownPath' and row.get('route') != MISSING:
                    malformed = True
                keys.append(row['width'])
        target = expected if group == 'pages' else set(WIDTHS)
        unique = set(keys)
        complete = not malformed and len(rows) == len(target) and len(keys) == len(unique) and unique == target
        groups[group] = {'expected': len(target), 'attempted': len(rows),
                         'uniqueAttempted': len(unique), 'complete': complete}
        if not complete:
            issues.append({'phase': 'coverage' if group == 'pages' else 'flow-coverage', 'group': group,
                           'message': 'Missing, extra, duplicate, or malformed ' +
                           ('route/viewport capture' if group == 'pages' else 'navigation/unknown-path width')})
    return {'expected': len(expected), 'attempted': groups['pages']['attempted'],
            'uniqueAttempted': groups['pages']['uniqueAttempted'],
            'complete': not issues, 'groups': groups, 'issues': issues}


def seal(out, revision=None):
    """Inventory every retained evidence byte; manifest itself is deliberately excluded."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    require(not out.is_symlink() and not any(p.is_symlink() for p in out.rglob('*')), 'evidence_symlinks_forbidden')
    files = {p.relative_to(out).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size}
             for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'artifact-manifest.json'}
    write_json(out / 'artifact-manifest.json', {
        'sourceRevision': revision, 'files': files, 'pixelReview': 'pending',
        'publicationAuthorized': False, 'publicationExecuted': False, 'publicHTTPVerified': False})


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def loopback_get(origin, path):
    require(same_origin(origin + path, origin), 'nonlocal_http_probe')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(origin + path, timeout=1) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as response:
        return response.code, response.read()



def resolve_astro_cli(root):
    """Resolve the installed package's bin, bound to the pinned npm lock metadata.

    No package code is executed here. npm ci establishes package integrity; this
    readback verifies installed name/version/bin and records the bytes launched.
    """
    root = Path(root).resolve()
    package_root = (root / 'node_modules/astro').resolve()
    package_file = package_root / 'package.json'
    lock_file = root / 'package-lock.json'
    require(package_file.is_file() and lock_file.is_file(), 'installed_Astro_and_lock_required')
    package = json.loads(package_file.read_text())
    lock = json.loads(lock_file.read_text()).get('packages', {}).get('node_modules/astro', {})
    require(package.get('name') == 'astro' and package.get('version') == lock.get('version'),
            'installed_Astro_version_differs_from_lock')
    bins, locked_bins = package.get('bin'), lock.get('bin')
    require(isinstance(bins, dict) and isinstance(locked_bins, dict), 'Astro_bin_map_required')
    declared, locked = bins.get('astro'), locked_bins.get('astro')
    require(isinstance(declared, str) and isinstance(locked, str), 'Astro_cli_bin_required')
    relative = PurePosixPath(declared)
    require(not relative.is_absolute() and '..' not in relative.parts and '\\' not in declared
            and ':' not in declared and relative == PurePosixPath(locked), 'Astro_cli_bin_path_invalid')
    cli = (package_root / relative).resolve()
    require(package_root in cli.parents and cli.is_file(), 'installed_Astro_cli_missing_or_outside_package')
    return cli, {'package': package['name'], 'version': package['version'],
                 'declaredBin': declared, 'lockedBin': locked, 'resolvedCli': str(cli),
                 'packageJsonSha256': sha(package_file), 'lockSha256': sha(lock_file),
                 'cliSha256': sha(cli), 'npmIntegrity': lock.get('integrity')}


@contextmanager
def astro_preview(root, out, port):
    """Run the genuine pinned Astro preview CLI; never install/build during capture."""
    require(isinstance(port, int) and 1024 <= port <= 65535, 'invalid_loopback_port')
    root, out = Path(root).resolve(), Path(out)
    env = clean_environment(os.environ)
    node = shutil.which('node', path=env.get('PATH'))
    require(node is not None, 'Node_24_not_installed')
    version = subprocess.run([node, '--version'], env=env, capture_output=True, text=True, check=True).stdout.strip()
    require(re.fullmatch(r'v24[.]\d+[.]\d+', version), 'Node_24_required:' + version)
    cli, package_evidence = resolve_astro_cli(root)
    require((root / 'dist/index.html').is_file(), 'existing_dist_required')
    origin = 'http://127.0.0.1:' + str(port)
    try:
        loopback_get(origin, '/')
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        pass
    else:
        raise RuntimeError('loopback_port_already_serving_HTTP')
    command = [node, str(cli), 'preview', '--host', '127.0.0.1', '--port', str(port)]
    write_json(out / 'preview-process.json', {'command': command, 'cwd': str(root),
               'nodeVersion': version, 'origin': origin, 'environmentKeys': sorted(env),
               'server': 'genuine Astro preview', 'synthetic404': False, 'installedAstro': package_evidence})
    process = None
    with (out / 'astro-preview.log').open('wb') as log:
        try:
            process = subprocess.Popen(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                require(process.poll() is None, 'Astro_preview_exited_before_ready')
                try:
                    code, body = loopback_get(origin, '/')
                    require(code == 200 and hashlib.sha256(body).hexdigest() == sha(root / 'dist/index.html'),
                            'preview_home_does_not_match_pinned_dist')
                    break
                except (urllib.error.URLError, TimeoutError, ConnectionError):
                    time.sleep(.2)
            else:
                raise RuntimeError('Astro_preview_startup_timeout')
            yield origin
        finally:
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=8)
                write_json(out / 'preview-process-exit.json', {'pid': process.pid,
                           'returnCode': process.returncode, 'cleanupVerified': process.poll() is not None})


METRICS_JS = r'''() => {
 const all=(s)=>[...document.querySelectorAll(s)];
 const visible=(el)=>!!el&&el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})&&el.getBoundingClientRect().width>0&&el.getBoundingClientRect().height>0;
 const links=(els)=>els.map(a=>({label:a.textContent.trim(),href:a.getAttribute('href')}));
 return {
  viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,
  reviewedBlocks:all('[data-reviewed-body] [data-reviewed-block]').map(e=>({tag:e.tagName,text:e.textContent.trim(),visible:visible(e)})),
  sections:all('main .copy-section').map(e=>({id:e.id,visible:visible(e)})),
  ids:all('[id]').map(e=>e.id),
  bannerPositions:all('[data-shared-flower-banner]').map(e=>({variant:e.dataset.sharedFlowerBanner,previousId:e.previousElementSibling?.id,nextId:e.nextElementSibling?.id,nextClosing:e.nextElementSibling?.classList.contains('directory-closing')})),
  schemaCount:all('script[type="application/ld+json"]').length,
  anchors:all('a[href]').map(e=>e.getAttribute('href')),
  h1:all('h1').map(e=>e.innerText),title:document.title,
  firstAnswer:all('[data-first-answer]').map(e=>({text:e.innerText,visible:visible(e)})),
  description:all('meta[name="description"]').map(e=>e.content),
  robots:all('meta[name="robots"]').map(e=>e.content),
  canonical:all('link[rel="canonical"]').map(e=>e.href),
  ogUrl:all('meta[property="og:url"]').map(e=>e.content),
  ogProperties:all('meta[property^="og:"]').map(e=>({name:e.getAttribute('property'),content:e.content})),
  socialMetadata:all('meta').flatMap(e=>['property','name'].filter(a=>/^(og:|twitter:)/.test(e.getAttribute(a)||'')).map(a=>({attribute:a,name:e.getAttribute(a),content:e.content}))),
  revision:all('meta[name="site-factory-revision"]').map(e=>e.content),
  banners:all('[data-shared-flower-banner]').map(e=>e.getAttribute('data-shared-flower-banner')),
  images:all('img').map(i=>({src:i.getAttribute('src'),alt:i.alt,loaded:i.complete&&i.naturalWidth>0,
   naturalWidth:i.naturalWidth,naturalHeight:i.naturalHeight,width:i.getBoundingClientRect().width,
   height:i.getBoundingClientRect().height,visible:visible(i),objectFit:getComputedStyle(i).objectFit})),
  products:all('[data-product-sku]').map(e=>({sku:e.dataset.productSku,
   image:e.querySelector('img')?.getAttribute('src'),alt:e.querySelector('img')?.alt,
   name:e.querySelector('h3')?.textContent.trim(),price:e.querySelector('.product-price')?.textContent.trim(),
   shipping:e.querySelector('.product-shipping')?.textContent.trim(),reference:e.querySelector('.product-reference')?.textContent.trim(),referenceTotal:e.querySelector('.product-reference')?.getAttribute('data-reference-total-krw'),referenceVisible:visible(e.querySelector('.product-reference')),description:e.querySelector('.product-description')?.textContent.trim(),
   links:[...e.querySelectorAll('a[data-order-product-sku]')].map(a=>({sku:a.dataset.orderProductSku,href:a.getAttribute('href'),label:a.textContent.trim(),ariaLabel:a.getAttribute('aria-label'),visible:visible(a),width:a.getBoundingClientRect().width,height:a.getBoundingClientRect().height}))})),
  faq:all('[data-visible-faq] [data-faq-question]').map(question=>{const next=question.nextElementSibling,answer=next?.matches('[data-faq-answer]')?next:null;return {question:question.innerText,
   answer:answer?.innerText??null,visible:visible(question.closest('[data-visible-faq]')),questionVisible:visible(question),answerVisible:visible(answer),collapsed:!!question.closest('details:not([open])')};}),
  faqQuestionCount:all('[data-faq-question]').length,faqAnswerCount:all('[data-faq-answer]').length,
  navigation:links(all('.desktop-navigation a')),mobileNavigation:links(all('.mobile-menu nav a')),
  productSampleNotice:all('.product-notice').map(e=>({text:e.textContent.trim(),visible:visible(e)})),
  chromeLinks:{skipLink:links(all('.skip-link')),brand:all('.brand').map(e=>({label:e.querySelector('b')?.textContent.trim(),href:e.getAttribute('href')})),footer:links(all('footer a')),mobileBar:links(all('.mobile-bar a'))},
  chromeVisibleLinks:Object.fromEntries([['brand','.brand'],['footer','footer a'],['desktop','.desktop-navigation a'],['mobileBar','.mobile-bar a']].map(([name,selector])=>[name,all(selector).filter(visible).map(e=>({label:(name==='brand'?e.querySelector('b')?.textContent:e.textContent)?.trim(),href:e.getAttribute('href'),width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}))])),
  requiredCtas:all('[data-required-cta]').map(e=>({label:e.textContent.trim(),href:e.getAttribute('href'),visible:visible(e),width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height})),
  breadcrumbs:all('.breadcrumb a,.breadcrumb [aria-current]').map(e=>({label:e.textContent.trim(),href:e.getAttribute('href'),current:e.getAttribute('aria-current')==='page'})),
  breadcrumbContainers:all('.breadcrumb').map(e=>({tag:e.tagName,ariaLabel:e.getAttribute('aria-label'),ariaHidden:e.getAttribute('aria-hidden'),inert:e.inert,visible:visible(e),width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height,parentIsMain:e.parentElement===document.querySelector('main'),nextArticleId:e.nextElementSibling?.getAttribute('data-page-id'),children:[...e.children].map(child=>({tag:child.tagName,label:child.textContent.trim(),href:child.getAttribute('href'),ariaCurrent:child.getAttribute('aria-current'),ariaHidden:child.getAttribute('aria-hidden'),inert:child.inert,visible:visible(child),width:child.getBoundingClientRect().width,height:child.getBoundingClientRect().height}))})),
  supportCards:all('[data-content-card]').map(e=>({title:e.querySelector('h2,h3').textContent.trim(),summary:e.querySelector('p').textContent.trim(),links:links([...e.querySelectorAll('a')])})),
  internalLinks:links(all('main a[href^="/"]')),
  bodyCtas:all('main a[href]').map(e=>({label:e.textContent.trim(),href:e.getAttribute('href'),visible:visible(e),width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height})),
  overflow:all('main *').filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.left<-.5||r.right>innerWidth+.5)}).slice(0,12).map(e=>({tag:e.tagName,className:e.className})),
  ctas:all('[data-order-product-sku],.page-card > a,.actions a,.mobile-bar a').filter(visible).map(e=>({href:e.getAttribute('href'),height:e.getBoundingClientRect().height}))
 };}'''


def breadcrumb_issues(metrics, expected):
    """Verify actual DOM containers, child semantics and computed visibility."""
    issues = []
    crumbs = [{key: crumb[key] for key in ('label', 'href', 'current')}
              for crumb in expected['breadcrumbs']] if expected['breadcrumbVisible'] else []
    if metrics.get('breadcrumbs') != crumbs:
        issues.append('Exact breadcrumb chain mismatch')
    containers = metrics.get('breadcrumbContainers')
    if not isinstance(containers, list) or len(containers) != (1 if crumbs else 0):
        issues.append('Exact breadcrumb container count mismatch')
        return issues
    if not crumbs:
        return issues
    container = containers[0]
    if (container.get('tag') != 'NAV' or container.get('ariaLabel') != expected.get('breadcrumbAriaLabel')
        or container.get('ariaHidden') is not None or container.get('inert') is not False
        or container.get('parentIsMain') is not True or container.get('nextArticleId') != expected['id']):
        issues.append('Breadcrumb semantic label or before-article position mismatch')
    if container.get('visible') is not True or container.get('width', 0) <= 0 or container.get('height', 0) <= 0:
        issues.append('Breadcrumb container hidden or has zero geometry')
    children = []
    for index, crumb in enumerate(crumbs):
        if index:
            children.append({'tag': 'SPAN', 'label': '›', 'href': None, 'ariaCurrent': None, 'ariaHidden': 'true', 'inert': False})
        children.append({'tag': 'SPAN' if crumb['current'] else 'A', 'label': crumb['label'], 'href': crumb['href'],
                         'ariaCurrent': 'page' if crumb['current'] else None, 'ariaHidden': None, 'inert': False})
    actual_children = container.get('children', [])
    if [{key: child.get(key) for key in ('tag', 'label', 'href', 'ariaCurrent', 'ariaHidden', 'inert')}
        for child in actual_children] != children:
        issues.append('Exact breadcrumb parent/current/separator semantics mismatch')
    if any(child.get('visible') is not True or child.get('width', 0) <= 0 or child.get('height', 0) <= 0 for child in actual_children):
        issues.append('Breadcrumb parent/current/separator hidden or has zero geometry')
    return issues


def inspect_metrics(metrics, expected, spec, width, revision):
    issues = metadata_issues(metrics, expected, revision)
    route = expected['path']
    blocks = metrics.get('reviewedBlocks', [])
    if [{key: b.get(key) for key in ('tag', 'text')} for b in blocks] != expected['reviewedBlocks'] or any(b.get('visible') is not True for b in blocks):
        issues.append('Exact reviewed body blocks missing, changed, reordered, or invisible')
    if metrics.get('sections') != [{'id': name, 'visible': True} for name in expected['sections']]:
        issues.append('Exact five visible home sections required')
    ids = metrics.get('ids', [])
    if len(ids) != len(set(ids)) or any(ids.count(name) != 1 for name in (ANCHORS if route == '/' else ())):
        issues.append('Duplicate or missing home anchor IDs')
    if any('/regions/' in href or href.startswith('/') and href not in ('/', '/#products', '/#budget', '/#ribbon', '/#order', '/#faq') for href in metrics.get('anchors', [])):
        issues.append('Unsupported legacy/internal route present')
    positions = [{'variant': 'message', 'previousId': 'opening', 'nextId': 'products', 'nextClosing': False},
                 {'variant': 'budget', 'previousId': 'budget', 'nextId': 'ribbon', 'nextClosing': False},
                 {'variant': 'consultation', 'previousId': 'faq', 'nextId': '', 'nextClosing': True}] if route == '/' else []
    if metrics.get('bannerPositions') != positions:
        issues.append('Exact reviewed banner placement differs')
    if metrics.get('schemaCount') != 0:
        issues.append('Unapproved structured data present')
    expected_first = [{'text': expected['content']['firstAnswer'], 'visible': True}] if expected['content']['firstAnswer'] is not None else []
    if metrics.get('firstAnswer') != expected_first:
        issues.append('Exact first answer missing, changed, or invisible')
    if metrics['viewport'] != width or metrics['scrollWidth'] > width or metrics['overflow']:
        issues.append('Horizontal overflow or viewport mismatch')
    if metrics['banners'] != (list(BANNERS) if route == '/' else []):
        issues.append('Exact primary-only three-banner sequence mismatch')
    expected_skus = expected['productCardIds']
    if [p['sku'] for p in metrics['products']] != expected_skus:
        issues.append('Exact four-product sequence mismatch')
    for product in metrics['products']:
        source_product = next((p for p in spec['productCards'] if p['sku'] == product['sku']), None)
        if not source_product:
            issues.append('Unrecognized product')
            continue
        sku, cta = product['sku'], source_product['cta']
        expected_links = [{'sku': sku, 'href': cta['href'], 'label': cta['label'], 'ariaLabel': cta['accessibleLabel']}]
        actual_links = [{key: link.get(key) for key in ('sku', 'href', 'label', 'ariaLabel')} for link in product['links']]
        if any(link.get('visible') is not True or link.get('width', 0) < 44 or link.get('height', 0) < 44 for link in product['links']):
            issues.append('Required product CTA invisible or has invalid geometry: ' + sku)
        if actual_links != expected_links or product['image'] != '/images/products/' + sku + '.jpg' or product['price'] != source_product['priceText'] or product['alt'] != source_product['alt'] or product.get('name') != source_product['name'] or product.get('shipping') != source_product['shippingText'] or product.get('description') != source_product['description'] or product.get('reference') != source_product['referenceText'] or product.get('referenceTotal') != str(source_product['referenceTotalKRW']) or product.get('referenceVisible') is not True:
            issues.append('Product source/CTA/image differs: ' + sku)
    notice = [{'text': spec['productSampleNotice'], 'visible': True}] if route == '/' else []
    if metrics.get('productSampleNotice') != notice:
        issues.append('Exact product sample notice missing, changed, or invisible')
    image_inventory = ([{'src': b['src'], 'alt': b['alt']} for b in spec['banners']] if route == '/' else [])
    if route == '/':
        image_inventory += [{'src': '/images/products/' + p['sku'] + '.jpg', 'alt': p['alt']} for p in spec['productCards']]
    if sorted((i.get('src', ''), i.get('alt', '')) for i in metrics['images']) != sorted((i['src'], i['alt']) for i in image_inventory):
        issues.append('Exact image source/alt inventory mismatch')
    if len(metrics['images']) != (7 if route == '/' else 0):
        issues.append('Exact page image count mismatch')
    for image in metrics['images']:
        if image.get('visible') is not True or not image['loaded'] or image['objectFit'] != 'contain' or image['width'] <= 0 or image['height'] <= 0:
            issues.append('Image decode/contain/size failure: ' + str(image['src']))
        size = (1774, 887) if '/shared-banners/' in (image['src'] or '') else (500, 500)
        if (image['naturalWidth'], image['naturalHeight']) != size:
            issues.append('Image intrinsic dimensions changed: ' + str(image['src']))
        if not image['height'] or abs(image['width'] / image['height'] - size[0] / size[1]) > .01:
            issues.append('Image display aspect ratio changed')
    if metrics.get('faqQuestionCount') != (3 if route == '/' else 0) or metrics.get('faqAnswerCount') != (3 if route == '/' else 0):
        issues.append('Exact FAQ question and answer node counts mismatch')
    expected_faq = [{k: f[k] for k in ('question', 'answer')} for f in spec['faqs']] if route == '/' else []
    if [{k: f[k] for k in ('question', 'answer')} for f in metrics['faq']] != expected_faq:
        issues.append('Exact home-only FAQ text/count mismatch')
    if any(not f['visible'] or f['collapsed'] for f in metrics['faq']):
        issues.append('FAQ collapsed or invisible')
    if any(f.get('questionVisible') is not True or f.get('answerVisible') is not True for f in metrics['faq']):
        issues.append('FAQ question or answer hidden, missing, or has zero geometry')
    actual_required = metrics.get('requiredCtas', [])
    if [{key: c.get(key) for key in ('label', 'href')} for c in actual_required] != expected['requiredCtas']:
        issues.append('Exact required CTA inventory mismatch')
    if any(c.get('visible') is not True or c.get('width', 0) < 44 or c.get('height', 0) < 44 for c in actual_required):
        issues.append('Required CTA hidden or smaller than 44px')
    actual_main = metrics.get('bodyCtas', [])
    if [{key: link.get(key) for key in ('label', 'href')} for link in actual_main] != expected['mainLinks']:
        issues.append('Exact main link inventory differs')
    if any(link.get('visible') is not True or link.get('width', 0) <= 0 or link.get('height', 0) < 44 for link in actual_main):
        issues.append('Main link hidden or smaller than 44px')
    chrome_visible = {'brand': expected['chromeLinks']['brand'], 'footer': expected['chromeLinks']['footer'],
                      'desktop': expected['navigation'] if width > 860 else [],
                      'mobileBar': expected['chromeLinks']['mobileBar'] if width <= 860 else []}
    actual_chrome = metrics.get('chromeVisibleLinks', {})
    if {group: [{key: link.get(key) for key in ('label', 'href')} for link in links]
        for group, links in actual_chrome.items()} != chrome_visible:
        issues.append('Required shared navigation or phone links invisible')
    if any(link.get('width', 0) <= 0 or link.get('height', 0) <= 0 for links in actual_chrome.values() for link in links):
        issues.append('Shared link geometry invalid')
    if any(link.get('width', 0) < 44 or link.get('height', 0) < 44
           for group in ('footer', 'mobileBar') for link in actual_chrome.get(group, [])):
        issues.append('Footer or mobile-bar touch target smaller than 44px')
    if metrics.get('chromeLinks') != expected['chromeLinks']:
        issues.append('Exact shared navigation, phone, skip, or recovery links differ')
    nav = expected['navigation']
    if metrics['navigation'] != nav or metrics['mobileNavigation'] != nav:
        issues.append('Main navigation includes unsupported route or label')
    issues.extend(breadcrumb_issues(metrics, expected))
    for link in expected['internalLinks']:
        if {'label': link['label'], 'href': link['href']} not in metrics['internalLinks']:
            issues.append('Required body/breadcrumb inbound link missing: ' + link['href'])
    cards = [{'title': c['title'], 'summary': c['summary'], 'links': [{'label': c['ctaLabel'], 'href': c['href']}]} for c in expected['contentCards']]
    if metrics['supportCards'] != cards:
        issues.append('Exact home/support content card mismatch')
    for required_cta in expected['ctas']:
        if not any(link.get('href') == required_cta['href'] and link.get('label') == required_cta['label']
                   and link.get('visible') is True and link.get('width', 0) > 0 and link.get('height', 0) > 0
                   for link in metrics.get('bodyCtas', [])):
            issues.append('Required body CTA missing or invisible: ' + required_cta['label'])
    if any(c['height'] < 44 for c in metrics['ctas']):
        issues.append('Visible CTA is shorter than 44px')
    return issues


def settle(page):
    """Use actual browser loading/decode, never fabricated dimensions or image state."""
    for image in page.locator('img').all():
        image.scroll_into_view_if_needed()
        image.evaluate('(image)=>image.decode()')
    page.evaluate('window.scrollTo(0,0)')
    page.wait_for_timeout(60)


def retain_page(page, out, stem, record):
    """Try each evidence write separately so a screenshot failure retains the DOM."""
    record.setdefault('artifacts', [])
    record.setdefault('evidenceFailures', [])
    for suffix, action in (
        ('-dom.html', lambda p: p.write_text(page.content())),
        ('-full.png', lambda p: page.screenshot(path=str(p), full_page=True)),
        ('-viewport.png', lambda p: page.screenshot(path=str(p))),
    ):
        try:
            target = Path(out) / (stem + suffix)
            action(target)
            record['artifacts'].append({'file': target.name, 'sha256': sha(target), 'bytes': target.stat().st_size})
        except Exception as error:
            record['evidenceFailures'].append({'artifact': stem + suffix, 'type': type(error).__name__, 'message': str(error)})


def anchor_state(page, target):
    return page.evaluate("""(target)=>{
      const matches=[...document.querySelectorAll('[id]')].filter(e=>e.id===target);
      const e=matches[0],r=e?.getBoundingClientRect(),h=document.querySelector('header')?.getBoundingClientRect();
      return {target,count:matches.length,visible:!!e&&e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}),
        top:r?.top,bottom:r?.bottom,headerBottom:h?.bottom,viewport:innerHeight,hash:location.hash};
    }""", target)


def anchor_issues(state):
    if (state.get('count') != 1 or state.get('visible') is not True or state.get('hash') != '#' + state['target']
        or state.get('top', -1) < state.get('headerBottom', 0) - 1
        or state.get('top', 1e6) >= state.get('viewport', 0) or state.get('bottom', 0) <= state.get('headerBottom', 0)):
        return ['Anchor target is missing, hidden, or occluded by sticky header']
    return []


def menu_and_history(page, origin, width, spec):
    page.goto(origin + '/', wait_until='networkidle')
    menu, result = page.locator('.mobile-menu'), {'width': width, 'steps': [], 'anchors': [], 'issues': []}
    summary = menu.locator('summary')
    result['visible'] = menu.is_visible()
    mobile = width <= 860
    if not mobile:
        if result['visible']:
            result['issues'].append('Desktop mobile menu visible')
    else:
        require(result['visible'] and summary.count() == 1, 'unique_visible_mobile_menu_required')
        for event in ('click', 'click', 'Space', 'Space', 'Enter', 'Enter'):
            if event == 'click':
                summary.click()
            else:
                summary.focus()
                page.keyboard.press(event)
            opened = menu.get_attribute('open') is not None
            expected_open = len(result['steps']) % 2 == 0
            row = {'event': event, 'open': opened, 'label': summary.inner_text().strip(),
                   'summaryFocused': summary.evaluate('(e)=>document.activeElement===e'),
                   'visibleLinks': menu.locator('nav a').evaluate_all('(links)=>links.filter(a=>a.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})).length')}
            result['steps'].append(row)
            if opened != expected_open or row['label'] != (spec['menuClose'] if expected_open else spec['menuOpen']) or row['visibleLinks'] != (len(ANCHORS) if expected_open else 0) or not row['summaryFocused']:
                result['issues'].append('Repeated menu toggle/label/link visibility/focus failure')
        summary.click()
        summary.focus()
        before = page.url
        page.keyboard.press('Escape')
        result['escape'] = {'open': menu.get_attribute('open') is not None,
                            'summaryFocused': summary.evaluate('(e)=>document.activeElement===e'), 'urlUnchanged': page.url == before,
                            'closeBehavior': 'Native details observation only; no custom Escape-close promise'}
        if not result['escape']['summaryFocused'] or not result['escape']['urlUnchanged']:
            result['issues'].append('Escape unexpectedly changes summary focus or navigation')
        if menu.get_attribute('open') is not None:
            summary.click()
        result['dismissal'] = {'open': menu.get_attribute('open') is not None, 'summaryFocused': summary.evaluate('(e)=>document.activeElement===e')}
        if result['dismissal']['open'] or not result['dismissal']['summaryFocused']:
            result['issues'].append('Native summary dismissal/focus failure')
    # Each menu item is clicked from both home and the genuine unknown-path 404.
    for start in ('/', MISSING):
        for target in ANCHORS:
            response = page.goto(origin + start, wait_until='networkidle')
            row = {'from': start, 'target': target, 'startStatus': response.status if response else None}
            if row['startStatus'] != (404 if start == MISSING else 200):
                result['issues'].append('Anchor flow start HTTP status differs')
            if mobile:
                summary.click()
                menu.locator('nav a[href="/#'+target+'"]').click()
                if menu.get_attribute('open') is not None:
                    summary.click()
            else:
                page.locator('.desktop-navigation a[href="/#'+target+'"]').click()
            page.wait_for_timeout(80)
            row['url'], row['targetState'] = page.url, anchor_state(page, target)
            result['issues'].extend(anchor_issues(row['targetState']))
            page.go_back(wait_until='networkidle')
            row['backUrl'] = page.url
            page.go_forward(wait_until='networkidle')
            row['forwardUrl'] = page.url
            if [row['url'], row['backUrl'], row['forwardUrl']] != [origin+'/#'+target, origin+start, origin+'/#'+target]:
                result['issues'].append('Native anchor navigation/back/forward failure')
            result['anchors'].append(row)
    page.goto(origin + '/', wait_until='networkidle')
    page.keyboard.press('Tab')
    result['firstKeyboardHref'] = page.locator(':focus').get_attribute('href')
    page.keyboard.press('Enter')
    result['skipHash'] = page.evaluate('location.hash')
    result['skipActiveId'] = page.evaluate('document.activeElement.id')
    if result['firstKeyboardHref'] != '#main-content' or result['skipHash'] != '#main-content' or result['skipActiveId'] != 'main-content':
        result['issues'].append('Native keyboard skip/focus failure')
    page.goto(origin + MISSING, wait_until='networkidle')
    page.locator('.brand').click()
    result['brandHomeUrl'] = page.url
    if result['brandHomeUrl'] != origin + '/':
        result['issues'].append('404 brand recovery does not reach home')
    return result


OCCURRENCES_JS = r'''({map,pageId,state}) => {
 // Adapted from the frozen Gokseong browser_check.py occurrence evaluator.
 // Visibility here is layout availability, not viewport intersection in Y.
 function available(n) {
  if (n.closest('head')) return false;
  for (let e=n;e;e=e.parentElement) {
   const s=getComputedStyle(e);
   if (s.display==='none'||s.visibility==='hidden'||s.visibility==='collapse'||Number(s.opacity)===0||e.hidden||e.inert||e.getAttribute('aria-hidden')==='true') return false;
   if (e.tagName==='DETAILS'&&!e.open&&!e.querySelector('summary')?.contains(n)) return false;
  }
  const r=n.getBoundingClientRect();return r.width>0&&r.height>0&&r.right>0&&r.left<innerWidth;
 }
 function read(selector,extraction) {
  return [...document.querySelectorAll(selector)].map(n=>{
   const r=n.getBoundingClientRect();
   return {tag:n.tagName,text:extraction==='textContent'?n.textContent:n.getAttribute(extraction.split(':')[1]),
    available:available(n),rect:{x:r.x,y:r.y,width:r.width,height:r.height}};
  });
 }
 const observations=[];
 for (const row of map.contexts) for (const o of row.occurrences) {
  if (o.pageIds.includes(pageId)) observations.push({pointer:row.pointer,selector:o.selector,extraction:o.extraction,nodes:read(o.selector,o.extraction)});
 }
 return {pageId,stateId:state.id,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
  clientWidth:document.documentElement.clientWidth,menuOpen:document.querySelector('details.mobile-menu')?.open,
  skipFocused:document.activeElement===document.querySelector('.skip-link'),observations,
  supplemental:map.supplementalTechnicalIdentifiers.filter(o=>o.pageIds.includes(pageId)).map(o=>({pointer:o.pointer,selector:o.selector,nodes:read(o.selector,'textContent')}))};
}'''


def occurrence_issues(metrics, mapping, page_id, state):
    """Compare measured nodes against source expectations; never trust reported PASS."""
    issues = []
    expected = [(row['pointer'], o) for row in mapping['contexts'] for o in row['occurrences'] if page_id in o['pageIds']]
    rows = metrics.get('observations')
    if type(rows) is not list or len(rows) != len(expected):
        return ['Exact page-expanded occurrence inventory mismatch']
    if (metrics.get('pageId') != page_id or metrics.get('stateId') != state['id']
            or type(metrics.get('width')) is not int or metrics['width'] != state['width']
            or metrics.get('menuOpen') is not state['menuOpen']
            or metrics.get('skipFocused') is not state['skipFocused']):
        issues.append('Exact occurrence viewport/menu/skip-focus state mismatch')
    if (type(metrics.get('scrollWidth')) not in (int, float) or not math.isfinite(metrics['scrollWidth'])
            or type(metrics.get('clientWidth')) not in (int, float) or not math.isfinite(metrics['clientWidth'])
            or metrics.get('clientWidth') != state['width'] or metrics.get('scrollWidth', 0) > state['width']):
        issues.append('Occurrence state horizontal overflow or viewport mismatch')
    for observed, (pointer, occurrence) in zip(rows, expected):
        if type(observed) is not dict or any(observed.get(k) != v for k, v in {
            'pointer': pointer, 'selector': occurrence['selector'], 'extraction': occurrence['extraction']}.items()):
            issues.append('Exact occurrence identity/order mismatch:' + pointer)
            continue
        nodes = observed.get('nodes')
        if type(nodes) is not list or len(nodes) != occurrence['expectedDOMMatchesPerPage']:
            issues.append('Exact occurrence node multiplicity mismatch:' + pointer)
            continue
        for node in nodes:
            if (type(node) is not dict or node.get('tag') != occurrence['requiredTag']
                    or node.get('text') != occurrence['expectedExtractedText']
                    or node.get('available') is not occurrence['layoutAvailableByState'][state['id']]):
                issues.append('Exact occurrence tag/text/layout availability mismatch:' + pointer)
            elif node['available']:
                rect = node.get('rect')
                if (type(rect) is not dict or any(type(rect.get(k)) not in (int, float) or not math.isfinite(rect[k]) for k in ('x', 'y', 'width', 'height'))
                        or rect['width'] <= 0 or rect['height'] <= 0 or rect['x'] >= state['width'] or rect['x'] + rect['width'] <= 0):
                    issues.append('Available occurrence has invalid measured geometry:' + pointer)
    supplemental = metrics.get('supplemental')
    wanted = [r for r in mapping['supplementalTechnicalIdentifiers'] if page_id in r['pageIds']]
    if type(supplemental) is not list or len(supplemental) != len(wanted):
        issues.append('Exact supplemental SKU inventory mismatch')
    else:
        for observed, source in zip(supplemental, wanted):
            nodes = observed.get('nodes') if type(observed) is dict else None
            if (type(observed) is not dict or observed.get('pointer') != source['pointer']
                    or observed.get('selector') != source['selector'] or type(nodes) is not list or len(nodes) != 1
                    or type(nodes[0]) is not dict or nodes[0].get('tag') != source['requiredTag']
                    or nodes[0].get('text') != source['expectedExtractedText'] or nodes[0].get('available') is not True):
                issues.append('Exact supplemental SKU tag/text/availability mismatch')
    return issues


def validate_occurrence_coverage(report):
    """Every actual page/state pair occurs once, including the focused skip states."""
    rows = report.get('occurrenceStates')
    expected = {(page, state['id'], state['width']) for page in ('home', 'notFound') for state in OCCURRENCE_STATES}
    keys = []
    malformed = type(rows) is not list
    for row in rows if type(rows) is list else []:
        if (type(row) is not dict or type(row.get('pageId')) is not str
                or type(row.get('stateId')) is not str or type(row.get('width')) is not int):
            malformed = True
        else:
            keys.append((row['pageId'], row['stateId'], row['width']))
    complete = not malformed and len(rows) == len(expected) and len(keys) == len(set(keys)) and set(keys) == expected
    return {'expected': len(expected), 'attempted': len(rows) if type(rows) is list else 0,
            'uniqueAttempted': len(set(keys)), 'complete': complete,
            'issues': [] if complete else [{'phase': 'occurrence-coverage', 'message': 'Missing, extra, duplicate, or malformed page/state capture'}]}


def capture_occurrence_states(page, origin, expected, spec, width, out):
    records = []
    page_id = 'home' if expected['path'] == '/' else 'notFound'
    for state in (s for s in OCCURRENCE_STATES if s['width'] == width):
        record = {'route': expected['path'], 'pageId': page_id, 'stateId': state['id'], 'width': width, 'issues': []}
        stem = expected['id'] + '-state-' + state['id']
        try:
            response = page.goto(origin + expected['path'], wait_until='networkidle')
            record['httpStatus'] = response.status if response else None
            require(record['httpStatus'] == 200, 'occurrence_state_route_not_200')
            record['responseSha256'] = hashlib.sha256(response.body()).hexdigest()
            require(record['responseSha256'] == expected['documentSHA256'], 'occurrence_state_HTTP_bytes_differ_from_pinned_dist')
            settle(page)
            require(page.locator('details.mobile-menu > summary').count() == 1, 'unique_occurrence_menu_summary_required')
            if state['menuOpen']:
                page.locator('details.mobile-menu > summary').click()
            if state['skipFocused']:
                page.keyboard.press('Tab')
            record['metrics'] = page.evaluate(OCCURRENCES_JS, {'map': spec['occurrenceMap'], 'pageId': page_id, 'state': state})
            record['issues'].extend(occurrence_issues(record['metrics'], spec['occurrenceMap'], page_id, state))
        except Exception as error:
            record['issues'].append(type(error).__name__ + ': ' + str(error))
        finally:
            retain_page(page, out, stem, record)
            write_json(Path(out) / (stem + '.json'), record)
            records.append(record)
    return records


def scroll_reachability(page):
    """Measure every reviewed body node/image after scrolling, without clicking CTAs."""
    rows, issues = [], []
    for index, node in enumerate(page.locator('main [data-reviewed-block],main img').all()):
        node.scroll_into_view_if_needed()
        row = node.evaluate('''(e)=>{const r=e.getBoundingClientRect();return {tag:e.tagName,text:e.tagName==='IMG'?e.alt:e.textContent,
          left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,
          viewportWidth:innerWidth,viewportHeight:innerHeight,visible:e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})};}''')
        row['index'] = index
        rows.append(row)
        if (row['visible'] is not True or row['width'] <= 0 or row['height'] <= 0 or row['left'] < -1
                or row['right'] > row['viewportWidth'] + 1 or row['bottom'] <= 0 or row['top'] >= row['viewportHeight']):
            issues.append('Reviewed occurrence is not scroll reachable:' + str(index))
    page.evaluate('scrollTo(0,0)')
    return {'observations': rows, 'issues': issues}


def inspect(root, out, pages, spec, revision, port):
    from playwright.sync_api import sync_playwright
    root, out = Path(root), Path(out)
    report = {'status': 'machine-qa-failed', 'startedUTC': now(), 'sourceRevision': revision,
              'scope': 'Pinned production dist through genuine loopback Astro preview only',
              'routes': list(ROUTES), 'widths': list(WIDTHS), 'pages': [], 'flows': [],
              'unknownPath': [], 'occurrenceStates': [], 'failures': [], 'network': [], 'console': [], 'pageErrors': [],
              'authoredLeafCount': 102, 'logicalOccurrences': 119, 'pageExpandedOccurrencesPerState': 143,
              'occurrenceMapSHA256': spec['occurrenceMapSHA256'],
              'blockedExternalRequests': [], 'pixelReview': 'pending', 'publicHTTPVerified': False,
              'publicationAuthorized': False, 'publicationExecuted': False}
    try:
        with astro_preview(root, out, port) as origin, sync_playwright() as playwright:
            report['localOrigin'] = origin
            browser = playwright.chromium.launch(headless=True, chromium_sandbox=True, env=clean_environment(os.environ))
            report['browserVersion'] = browser.version
            report['browserExecutableSelection'] = 'Installed Playwright Chromium default; no executable override'
            try:
                for width in WIDTHS:
                    context = browser.new_context(viewport={'width': width, 'height': HEIGHT}, device_scale_factor=1,
                        locale='ko-KR', reduced_motion='reduce', service_workers='block', accept_downloads=False)
                    def route_request(route):
                        if same_origin(route.request.url, origin):
                            route.continue_()
                        else:
                            report['blockedExternalRequests'].append(route.request.url)
                            route.abort('blockedbyclient')
                    context.route('**/*', route_request)
                    def block_socket(socket):
                        report['blockedExternalRequests'].append(socket.url)
                        socket.close()
                    context.route_web_socket('**/*', block_socket)
                    page = context.new_page()
                    page.set_default_timeout(20000)
                    page.set_default_navigation_timeout(20000)
                    page.on('pageerror', lambda error: report['pageErrors'].append(str(error)))
                    page.on('console', lambda msg: report['console'].append({'type': msg.type, 'text': msg.text, 'location': msg.location}))
                    page.on('response', lambda response: report['network'].append({'url': response.url, 'status': response.status}))
                    page.on('requestfailed', lambda request: report['network'].append({'url': request.url, 'failure': request.failure}))
                    try:
                        for expected in pages:
                            stem = expected['id'] + '-' + str(width)
                            record = {'route': expected['path'], 'id': expected['id'], 'width': width, 'issues': []}
                            try:
                                response = page.goto(origin + expected['path'], wait_until='networkidle')
                                record['httpStatus'] = response.status if response else None
                                if response:
                                    record['responseSha256'] = hashlib.sha256(response.body()).hexdigest()
                                    dist_file = 'index.html' if expected['path'] == '/' else expected['path'].lstrip('/') + ('index.html' if expected['path'].endswith('/') else '')
                                    if record['responseSha256'] != sha(root / 'dist' / dist_file):
                                        record['issues'].append('Actual HTTP response bytes differ from pinned dist')
                                if record['httpStatus'] != 200:
                                    record['issues'].append('Direct file route is not HTTP 200')
                                settle(page)
                                record['metrics'] = page.evaluate(METRICS_JS)
                                record['issues'].extend(inspect_metrics(record['metrics'], expected, spec, width, revision))
                                record['scrollReachability'] = scroll_reachability(page)
                                record['issues'].extend(record['scrollReachability']['issues'])
                                if len(record['scrollReachability']['observations']) != len(expected['reviewedBlocks']) + (7 if expected['path'] == '/' else 0):
                                    record['issues'].append('Exact scroll-reachability inventory differs')
                                # Preserve original reviewed article/product pixels as dedicated sections too.
                                for selector, label in ([(('#' + name), name) for name in SECTIONS] + [('#faq', 'faq'), ('#sources', 'sources')]) if expected['path'] == '/' else []:
                                    if page.locator(selector).count():
                                        target = out / (stem + '-' + label + '.png')
                                        page.locator(selector).screenshot(path=str(target))
                                        record.setdefault('artifacts', []).append({'file': target.name, 'sha256': sha(target), 'bytes': target.stat().st_size})
                                page.evaluate('scrollTo(0,0)')
                            except Exception as error:
                                record['issues'].append(type(error).__name__ + ': ' + str(error))
                            finally:
                                retain_page(page, out, stem, record)
                                report['pages'].append(record)
                                write_json(out / 'report.json', report)
                            report['occurrenceStates'].extend(capture_occurrence_states(page, origin, expected, spec, width, out))
                            write_json(out / 'report.json', report)
                        # Real HTTP404 and actual custom document from Astro, not a QA-only handler.
                        missing = {'width': width, 'route': MISSING, 'issues': []}
                        try:
                            response = page.goto(origin + MISSING, wait_until='networkidle')
                            missing['httpStatus'] = response.status if response else None
                            missing['responseSha256'] = hashlib.sha256(response.body()).hexdigest() if response else None
                            if missing['responseSha256'] != sha(root / 'dist/404.html'):
                                missing['issues'].append('Actual unknown-path bytes differ from pinned custom 404')
                            missing['h1'] = page.locator('h1').all_inner_texts()
                            not_found = next(p for p in pages if p['path'] == '/404.html')
                            missing['metadata'] = page.evaluate(METRICS_JS)
                            missing['issues'].extend(inspect_metrics(missing['metadata'], not_found, spec, width, revision))
                            if missing['httpStatus'] != 404:
                                missing['issues'].append('Genuine Astro unknown path must return HTTP 404')
                            retain_page(page, out, 'unknown-path-' + str(width), missing)
                            page.locator('main').get_by_role('link', name=not_found['ctas'][0]['label'], exact=True).click()
                            missing['recoveryUrl'] = page.url
                            if page.url != origin + '/':
                                missing['issues'].append('404 recovery does not reach home')
                        except Exception as error:
                            missing['issues'].append(type(error).__name__ + ': ' + str(error))
                            retain_page(page, out, 'unknown-path-failure-' + str(width), missing)
                        report['unknownPath'].append(missing)
                        try:
                            report['flows'].append(menu_and_history(page, origin, width, spec))
                        except Exception as error:
                            failure = {'width': width, 'issues': [type(error).__name__ + ': ' + str(error)]}
                            retain_page(page, out, 'navigation-failure-' + str(width), failure)
                            report['flows'].append(failure)
                    finally:
                        context.close()
            finally:
                browser.close()
    except Exception as error:
        report['failures'].append({'phase': 'browser-or-preview', 'type': type(error).__name__, 'message': str(error)})
    finally:
        report['coverage'] = validate_capture_coverage(report, pages)
        report['failures'].extend(report['coverage']['issues'])
        report['occurrenceCoverage'] = validate_occurrence_coverage(report)
        report['failures'].extend(report['occurrenceCoverage']['issues'])
        for group in ('pages', 'flows', 'unknownPath', 'occurrenceStates'):
            for row in report[group]:
                if row.get('issues') or row.get('evidenceFailures'):
                    report['failures'].append({'phase': group, 'route': row.get('route'), 'width': row['width'],
                       'issues': row.get('issues', []), 'evidenceFailures': row.get('evidenceFailures', [])})
        # The only expected HTTP error is the deliberately requested genuine 404.
        bad_network = [r for r in report['network'] if r.get('failure') or
                       (r.get('status', 200) >= 400 and not (r.get('status') == 404 and urlsplit(r['url']).path == MISSING))]
        # Chromium logs an expected missing-page 404 as console error on some versions.
        bad_console = [c for c in report['console'] if c['type'] == 'error' and not
                       ('404' in c['text'] and 'Failed to load resource' in c['text'] and urlsplit(c.get('location', {}).get('url', '')).path == MISSING)]
        if report['blockedExternalRequests'] or report['pageErrors'] or bad_network or bad_console:
            report['failures'].append({'phase': 'network-or-console', 'badNetwork': bad_network, 'badConsole': bad_console,
                 'blockedExternalRequests': report['blockedExternalRequests'], 'pageErrors': report['pageErrors']})
        report['status'] = 'machine-qa-failed' if report['failures'] else 'captured-awaiting-independent-pixel-review'
        report['finishedUTC'] = now()
        write_json(out / 'report.json', report)
        write_json(out / 'network.json', report['network'])
        write_json(out / 'browser-console.json', report['console'])
        write_json(out / 'page-errors.json', report['pageErrors'])
    return report


def capture(checkout, out, port=43817):
    # Import gate only on an explicit invocation. Tests/imports perform no launch.
    out, checkout = Path(out).resolve(), Path(checkout).resolve()
    require(not out.exists() or not any(out.iterdir()), 'fresh_capture_output_directory_required')
    root = checkout / ROOT
    source_root = checkout / SOURCE_ROOT
    require(out != source_root and source_root not in out.parents, 'capture_output_must_be_outside_source_root')
    out.mkdir(parents=True, exist_ok=True)
    revision, before, failures = None, None, []
    try:
        from production_build import source, load
        reject_provider_credentials(os.environ)
        contract = load()[0]
        revision = contract['sourceRevision']
        require(re.fullmatch('[0-9a-f]{40}', revision), 'exact_source_revision_required')
        require(contract['sourceRoot'] == SOURCE_ROOT, 'exact_Gokseong_source_root_required')
        before_gate = source(checkout, 'postbuild', os.environ)
        write_json(out / 'source-before-capture.json', before_gate)
        before = source_binding(checkout, before_gate)
        write_json(out / 'input-binding-before.json', before)
        pages, spec = capture_inputs(root)
        write_json(out / 'exact-ui-inputs.json', {'pages': pages, 'spec': spec})
        report = inspect(root, out, pages, spec, revision, port)
        if report['failures']:
            failures.append({'phase': 'machine-qa', 'message': 'See report.json for measured failures'})
    except Exception as error:
        failures.append({'phase': 'capture-controller', 'type': type(error).__name__, 'message': str(error)})
    finally:
        if before is not None:
            try:
                after_gate = source(checkout, 'postbuild', os.environ)
                write_json(out / 'source-after-capture.json', after_gate)
                after = source_binding(checkout, after_gate)
                write_json(out / 'input-binding-after.json', after)
                require(before == after, 'source_or_dist_or_control_changed_during_capture')
            except Exception as error:
                failures.append({'phase': 'post-capture-integrity', 'type': type(error).__name__, 'message': str(error)})
        else:
            failures.append({'phase': 'post-capture-integrity', 'message': 'No verified pre-capture binding; source/browser not approved to run'})
        state = {'status': 'machine-qa-failed' if failures else 'captured-awaiting-independent-pixel-review',
                 'sourceRevision': revision, 'controllerFailures': failures, 'pixelReview': 'pending',
                 'publicHTTPVerified': False, 'publicationAuthorized': False, 'publicationExecuted': False,
                 'sourceAndOutputUnchanged': before is not None and not any(f['phase'] == 'post-capture-integrity' for f in failures)}
        report_path = out / 'report.json'
        report = json.loads(report_path.read_text()) if report_path.is_file() else {'pages': [], 'failures': []}
        report.update(state)
        write_json(report_path, report)
        write_json(out / 'capture-status.json', state)
        seal(out, revision)
    require(not failures, 'production_capture_failed; inspect sealed capture-status.json and report.json')
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout')
    parser.add_argument('--output', required=True)
    parser.add_argument('--port', type=int, default=43817)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    if args.seal:
        # Sealing is evidence bookkeeping, not execution or a success declaration.
        status = Path(args.output) / 'capture-status.json'
        revision = json.loads(status.read_text()).get('sourceRevision') if status.is_file() else None
        seal(args.output, revision)
    else:
        require(bool(args.checkout), 'checkout_required')
        print(json.dumps(capture(args.checkout, args.output, args.port), ensure_ascii=False))


if __name__ == '__main__':
    main()

