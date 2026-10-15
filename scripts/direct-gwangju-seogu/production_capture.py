#!/usr/bin/env python3
"""Capture a pinned Seogu production dist on a permitted runner, without publishing.

Prepared locally only: this module does not launch anything when imported. Runtime
requires Node 24, installed Playwright Chromium and permission to open loopback
sockets. It never substitutes a synthetic 404 server or weakens the browser sandbox.
The capture machine's checks cannot approve an independent review of the pixels.

Reused from verified Suncheon production_capture.py; Seogu expectations are read
from its actual immutable runtime and customer-copy.json, not Suncheon schema.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

SOURCE_ROOT = 'site-factory/gwangju-seogu-flower'
ROOT = SOURCE_ROOT + '/candidate'
ORIGIN = 'https://gwangju-seogu.fwith.kr'
ARTICLE = '/regions/gukbin-funeral-wreath/'
ROUTES = ('/', '/regions/', ARTICLE, '/404.html')
WIDTHS = (320, 390, 1280)
HEIGHT = 900
MISSING = '/does-not-exist-seogu-production-capture/'
PRODUCTS = ('B201', 'B203', 'B205', 'B060')
BANNERS = ('message', 'budget', 'consultation')
DIRECTORY = Path(__file__).resolve().parent


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


def expected_social(page, banner):
    """Exact metadata emitted by the reviewed Seogu release adapter."""
    if page['path'] == '/404.html':
        return []
    content = page['content']
    image = ORIGIN + '/images/products/B201.jpg'
    alt = '노란 꽃이 흰 꽃 사이에 놓인 B201 근조 3단 화환 상품사진'
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


def facility_card(copy):
    """Select the sole owned facility-guide card, independent of section position."""
    require(type(copy) is dict and type(copy.get('home')) is dict, 'home_object_required')
    sections = copy['home'].get('sections')
    require(type(sections) is list, 'home_sections_required')
    matches = [section for section in sections if type(section) is dict and section.get('id') == 'facility-guide']
    owners = [section for section in sections if type(section) is dict and 'card' in section]
    require(len(matches) == 1 and len(owners) == 1 and matches[0] is owners[0],
            'exactly_one_facility_guide_card_required')
    card = matches[0]['card']
    require(type(card) is dict and set(card) == {'title', 'summary', 'ctaLabel', 'href'},
            'exact_facility_card_keys_required')
    require(all(type(card[key]) is str and card[key].strip() for key in card),
            'nonempty_facility_card_strings_required')
    require(card['href'] == ARTICLE, 'exact_facility_card_article_href_required')
    return card


def capture_inputs(root):
    """Read immutable Seogu structured JSON/runtime; never replace reviewed copy."""
    root = Path(root).resolve()
    command = ['node', '--input-type=module', '-e',
        "import {copy,pages,products,home,detail,ui,banners,mapTarget,facilityCard} from './src/lib/donggu-runtime.mjs';console.log(JSON.stringify({copy,pages,products,home,detail,ui,banners,homeCardHref:mapTarget(facilityCard(copy)),supportCardHref:mapTarget(copy.support.card),sourceHref:mapTarget(home.sourceLink),notFoundHref:mapTarget(copy.notFound.cta)}));"]
    run = subprocess.run(command, cwd=root, env=clean_environment(os.environ), capture_output=True, text=True, check=True)
    data = json.loads(run.stdout)
    original, products, home, detail, ui = data['pages'], data['products'], data['home'], data['detail'], data['ui']
    require(len(original) == 4 and {p['path'] for p in original} == set(ROUTES), 'four_exact_routes_required')
    require(tuple(p['sku'] for p in products) == PRODUCTS, 'four_exact_products_required')
    home_card = facility_card(data['copy'])
    require([section.get('id') for section in home['sections']] == ['budget', 'facility-guide', 'consultation'],
            'exact_reviewed_home_section_order_required')
    require(data['homeCardHref'] == home_card['href'], 'facility_card_runtime_target_mismatch')
    faqs = detail['faq']
    require(len(faqs) == 3 and len({f['question'] for f in faqs}) == 3, 'exact_three_faqs_required')
    assets = json.loads((root.parent / 'inputs/reviewed-copy/asset-manifest.json').read_text())['productPhotos']
    require(len(assets) == 4 and tuple(row['sku'] for row in assets) == PRODUCTS, 'exact_four_product_assets_required')
    asset_by_sku = {row['sku']: row for row in assets}
    product_cards = []
    for product in products:
        asset = asset_by_sku[product['sku']]
        require(asset['path'] == product['localPhoto'] and asset['publicPath'] == '/images/products/' + product['sku'] + '.jpg', 'exact_product_asset_mapping_required')
        require(sha(root / 'dist/images/products' / (product['sku'] + '.jpg')) == asset['sha256'], 'frozen_product_image_bytes_changed:' + product['sku'])
        product_cards.append({'sku': product['sku'], 'photoSHA256': asset['sha256'],
            'name': product['name'] + ' ' + product['sku'], 'priceText': product['priceLabel'],
            'shippingText': product['shippingLabel'], 'description': product['description'], 'alt': product['photoAlt'],
            'cta': {'href': product['ctaHref'], 'label': product['ctaLabel'], 'accessibleLabel': None}})
    nav = [{'label': ui['homeLink'], 'href': '/'}, {'label': ui['detailLink'], 'href': ARTICLE}]
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
    for route in ROUTES:
        original_page = next(p for p in original if p['path'] == route)
        primary = original_page['id'] in ('home', 'article')
        copy = data['copy'][original_page['copyKey']]
        lead = copy['lead'] if primary else None
        first = lead[0] if isinstance(lead, list) else lead
        card = home_card if route == '/' else data['copy']['support']['card']
        card_href = data['homeCardHref'] if route == '/' else data['supportCardHref']
        cards = [{'title': card['title'], 'summary': card['summary'], 'ctaLabel': card['ctaLabel'], 'href': card_href,
                  'headingTag': 'h3' if route == '/' else 'h2'}] if route in ('/', '/regions/') else []
        ctas = [copy['cta']] if primary else []
        if cards:
            ctas.append({'label': card['ctaLabel'], 'href': card_href})
        if route == '/404.html':
            ctas.append({'label': copy['cta']['label'], 'href': data['notFoundHref']})
        internal = [{'label': card['ctaLabel'], 'href': card_href}] if cards else []
        if route == '/':
            internal.append({'label': home['sourceLink']['label'], 'href': data['sourceHref']})
        # Exact data-required-cta sequence follows the actual reviewed component.
        required_ctas = ([{'label': card['ctaLabel'], 'href': card_href}] if cards else [])
        if route == ARTICLE:
            required_ctas += [{'label': p['cta']['label'], 'href': p['cta']['href']} for p in product_cards]
        if primary:
            required_ctas.append(copy['cta'])
        if route == '/404.html':
            required_ctas += ctas
        crumbs = []
        if route in ('/regions/', ARTICLE):
            crumbs = [{'label': ui['homeLink'], 'href': '/', 'current': False}]
            if route == ARTICLE:
                crumbs.append({'label': data['copy']['support']['h1'], 'href': '/regions/', 'current': False})
            crumbs.append({'label': original_page['h1'], 'href': None, 'current': True})
            internal = [{key: crumb[key] for key in ('label', 'href')} for crumb in crumbs if not crumb['current']] + internal
        page = {'id': original_page['id'], 'path': route,
            'content': {'h1': original_page['h1'], 'title': original_page['title'],
                        'metaDescription': original_page['description'], 'firstAnswer': first},
            'productCardIds': list(PRODUCTS) if route == ARTICLE else [],
            'faqIds': list(range(3)) if route == ARTICLE else [],
            'breadcrumbVisible': bool(crumbs), 'breadcrumbs': crumbs,
            'breadcrumbAriaLabel': ui['breadcrumbLabel'] if crumbs else None, 'ctas': ctas, 'requiredCtas': required_ctas,
            'internalLinks': internal, 'contentCards': cards, 'navigation': nav, 'chromeLinks': chrome}
        page['mainLinks'] = [{key: crumb[key] for key in ('label', 'href')} for crumb in crumbs if not crumb['current']] + list(required_ctas)
        if route == '/':
            page['mainLinks'].append({'label': home['sourceLink']['label'], 'href': data['sourceHref']})
        if route == ARTICLE:
            page['mainLinks'] += [{'label': item['label'], 'href': item['url']} for item in detail['sources']]
        page['socialMetadata'] = expected_social(page, banners[0])
        pages.append(page)
    return pages, {'pages': pages, 'productCards': product_cards, 'faqs': faqs, 'banners': banners,
                   'productSampleNotice': ui['productSampleNotice'], 'menuOpen': ui['menuOpen'], 'menuClose': ui['menuClose'],
                   'sourceSpecSHA256': sha(root.parent / 'inputs/required-originals.json')}


def metadata_issues(metrics, expected, revision):
    route = expected['path']
    issues = []
    targets = {'robots': ['index,follow' if route in ('/', ARTICLE) else 'noindex,follow'],
               'canonical': [] if route == '/404.html' else [ORIGIN + route],
               'ogUrl': [] if route == '/404.html' else [ORIGIN + route],
               'revision': [revision], 'h1': [expected['content']['h1']]}
    for name, target in targets.items():
        if metrics.get(name) != target:
            issues.append('Exact metadata mismatch: ' + name)
    if metrics.get('socialMetadata') != expected['socialMetadata']:
        issues.append('Exact OG/Twitter metadata differs from Seogu release contract')
    if route == '/404.html' and (metrics.get('ogProperties') or metrics.get('socialMetadata')):
        issues.append('404 contains social metadata')
    if metrics.get('title') != expected['content']['title'] or metrics.get('description') != [expected['content']['metaDescription']]:
        issues.append('Title or description differs from frozen source')
    return issues


def expected_inventory(pages):
    return {(p['path'], width) for p in pages for width in WIDTHS}


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
   height:i.getBoundingClientRect().height,objectFit:getComputedStyle(i).objectFit})),
  products:all('[data-product-sku]').map(e=>({sku:e.dataset.productSku,
   image:e.querySelector('img')?.getAttribute('src'),alt:e.querySelector('img')?.alt,
   name:e.querySelector('h3')?.textContent.trim(),price:e.querySelector('.product-price')?.textContent.trim(),
   shipping:e.querySelector('.product-shipping')?.textContent.trim(),description:e.querySelector('.product-description')?.textContent.trim(),
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
    expected_first = [{'text': expected['content']['firstAnswer'], 'visible': True}] if expected['content']['firstAnswer'] is not None else []
    if metrics.get('firstAnswer') != expected_first:
        issues.append('Exact first answer missing, changed, or invisible')
    if metrics['viewport'] != width or metrics['scrollWidth'] > width or metrics['overflow']:
        issues.append('Horizontal overflow or viewport mismatch')
    if metrics['banners'] != (list(BANNERS) if route in ('/', ARTICLE) else []):
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
        if any(link.get('visible') is not True or link.get('width', 0) <= 0 or link.get('height', 0) < 44 for link in product['links']):
            issues.append('Required product CTA invisible or has invalid geometry: ' + sku)
        if actual_links != expected_links or product['image'] != '/images/products/' + sku + '.jpg' or product['price'] != source_product['priceText'] or product['alt'] != source_product['alt'] or product.get('name') != source_product['name'] or product.get('shipping') != source_product['shippingText'] or product.get('description') != source_product['description']:
            issues.append('Product source/CTA/image differs: ' + sku)
    notice = [{'text': spec['productSampleNotice'], 'visible': True}] if route == ARTICLE else []
    if metrics.get('productSampleNotice') != notice:
        issues.append('Exact product sample notice missing, changed, or invisible')
    image_inventory = ([{'src': b['src'], 'alt': b['alt']} for b in spec['banners']] if route in ('/', ARTICLE) else [])
    if route == ARTICLE:
        image_inventory += [{'src': '/images/products/' + p['sku'] + '.jpg', 'alt': p['alt']} for p in spec['productCards']]
    if sorted((i.get('src', ''), i.get('alt', '')) for i in metrics['images']) != sorted((i['src'], i['alt']) for i in image_inventory):
        issues.append('Exact image source/alt inventory mismatch')
    if len(metrics['images']) != (7 if route == ARTICLE else 3 if route == '/' else 0):
        issues.append('Exact page image count mismatch')
    for image in metrics['images']:
        if not image['loaded'] or image['objectFit'] != 'contain' or image['width'] <= 0 or image['height'] <= 0:
            issues.append('Image decode/contain/size failure: ' + str(image['src']))
        size = (1774, 887) if '/shared-banners/' in (image['src'] or '') else (500, 500)
        if (image['naturalWidth'], image['naturalHeight']) != size:
            issues.append('Image intrinsic dimensions changed: ' + str(image['src']))
        if size == (1774, 887) and (not image['height'] or abs(image['width'] / image['height'] - 2) > .01):
            issues.append('Banner display aspect ratio changed')
    if metrics.get('faqQuestionCount') != (3 if route == ARTICLE else 0) or metrics.get('faqAnswerCount') != (3 if route == ARTICLE else 0):
        issues.append('Exact FAQ question and answer node counts mismatch')
    expected_faq = [{k: f[k] for k in ('question', 'answer')} for f in spec['faqs']] if route == ARTICLE else []
    if [{k: f[k] for k in ('question', 'answer')} for f in metrics['faq']] != expected_faq:
        issues.append('Exact article-only FAQ text/count mismatch')
    if any(not f['visible'] or f['collapsed'] for f in metrics['faq']):
        issues.append('FAQ collapsed or invisible')
    if any(f.get('questionVisible') is not True or f.get('answerVisible') is not True for f in metrics['faq']):
        issues.append('FAQ question or answer hidden, missing, or has zero geometry')
    actual_required = metrics.get('requiredCtas', [])
    if [{key: c.get(key) for key in ('label', 'href')} for c in actual_required] != expected['requiredCtas']:
        issues.append('Exact required CTA inventory mismatch')
    if any(c.get('visible') is not True or c.get('width', 0) <= 0 or c.get('height', 0) < 44 for c in actual_required):
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


def menu_and_history(page, origin, width):
    page.goto(origin + '/', wait_until='networkidle')
    menu = page.locator('.mobile-menu')
    summary = menu.locator('summary')
    result = {'width': width, 'visible': menu.is_visible(), 'steps': [], 'issues': []}
    if width >= 860:
        if result['visible']:
            result['issues'].append('Desktop mobile menu visible')
        # Still exercise native history using the main visible navigation link.
        page.locator('.desktop-navigation a[href="'+ARTICLE+'"]').click()
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
                   'visibleLinks': menu.locator('nav a').evaluate_all('(links)=>links.filter(a=>a.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})).length')}
            result['steps'].append(row)
            if opened != expected_open or row['label'] != ('메뉴 닫기' if expected_open else '메뉴 열기') or row['visibleLinks'] != (2 if expected_open else 0):
                result['issues'].append('Repeated menu toggle/label/link visibility failure')
        summary.click()
        menu.locator('nav a[href="'+ARTICLE+'"]').click()
    result['articleUrl'] = page.url
    page.go_back(wait_until='networkidle')
    result['backUrl'] = page.url
    page.go_forward(wait_until='networkidle')
    result['forwardUrl'] = page.url
    if [result[k] for k in ('articleUrl', 'backUrl', 'forwardUrl')] != [origin + ARTICLE, origin + '/', origin + ARTICLE]:
        result['issues'].append('Native article navigation/back/forward failure')
    # Separate fresh document and native Tab/Enter, no scripted click/focus.
    page.goto(origin + '/', wait_until='networkidle')
    page.keyboard.press('Tab')
    result['firstKeyboardHref'] = page.locator(':focus').get_attribute('href')
    page.keyboard.press('Enter')
    result['skipHash'] = page.evaluate('location.hash')
    result['skipActiveId'] = page.evaluate('document.activeElement.id')
    if result['firstKeyboardHref'] != '#main-content' or result['skipHash'] != '#main-content' or result['skipActiveId'] != 'main-content':
        result['issues'].append('Native keyboard skip/focus failure')
    # Exercise the actual successor breadcrumb's detail-to-support inbound link,
    # then native history, the support child, both breadcrumb home links and brand.
    page.goto(origin + '/', wait_until='networkidle')
    page.locator('main [data-content-card] a[href="'+ARTICLE+'"]').click()
    result['bodyInboundUrl'] = page.url
    page.locator('main > nav.breadcrumb a[href="/regions/"]').click()
    result['supportInboundUrl'] = page.url
    page.go_back(wait_until='networkidle')
    result['breadcrumbBackUrl'] = page.url
    page.go_forward(wait_until='networkidle')
    result['breadcrumbForwardUrl'] = page.url
    page.locator('main [data-content-card] a[href="'+ARTICLE+'"]').click()
    result['supportChildUrl'] = page.url
    page.locator('main > nav.breadcrumb a[href="/"]').click()
    result['breadcrumbHomeUrl'] = page.url
    page.goto(origin + '/regions/', wait_until='networkidle')
    result['supportDirectUrl'] = page.url
    page.locator('main > nav.breadcrumb a[href="/"]').click()
    result['supportHomeUrl'] = page.url
    page.goto(origin + ARTICLE, wait_until='networkidle')
    page.locator('.brand').click()
    result['brandHomeUrl'] = page.url
    fields = ('bodyInboundUrl', 'supportInboundUrl', 'breadcrumbBackUrl', 'breadcrumbForwardUrl',
              'supportChildUrl', 'breadcrumbHomeUrl', 'supportDirectUrl', 'supportHomeUrl', 'brandHomeUrl')
    targets = (ARTICLE, '/regions/', ARTICLE, '/regions/', ARTICLE, '/', '/regions/', '/', '/')
    if [result[key] for key in fields] != [origin + route for route in targets]:
        result['issues'].append('Native breadcrumb inbound/back/forward/support-child/home navigation failure')
    result['supportReachedByInboundLink'] = result['supportInboundUrl'] == origin + '/regions/'
    result['supportReachedByDirectNavigation'] = result['supportDirectUrl'] == origin + '/regions/'
    result['breadcrumbFlowApplicable'] = True
    return result


def inspect(root, out, pages, spec, revision, port):
    from playwright.sync_api import sync_playwright
    root, out = Path(root), Path(out)
    report = {'status': 'machine-qa-failed', 'startedUTC': now(), 'sourceRevision': revision,
              'scope': 'Pinned production dist through genuine loopback Astro preview only',
              'routes': list(ROUTES), 'widths': list(WIDTHS), 'pages': [], 'flows': [],
              'unknownPath': [], 'failures': [], 'network': [], 'console': [], 'pageErrors': [],
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
                                # Preserve original reviewed article/product pixels as dedicated sections too.
                                for selector, label in (('.product-grid', 'products'), ('[data-visible-faq]', 'faq')):
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
                            missing['issues'].extend(metadata_issues(missing['metadata'], not_found, revision))
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
                            report['flows'].append(menu_and_history(page, origin, width))
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
        coverage = {(row['route'], row['width']) for row in report['pages']}
        report['coverage'] = {'expected': len(expected_inventory(pages)), 'attempted': len(coverage),
                              'complete': coverage == expected_inventory(pages)}
        if not report['coverage']['complete']:
            report['failures'].append({'phase': 'coverage', 'message': 'Missing route/viewport capture'})
        for group in ('pages', 'flows', 'unknownPath'):
            for row in report[group]:
                if row.get('issues') or row.get('evidenceFailures'):
                    report['failures'].append({'phase': group, 'route': row.get('route'), 'width': row['width'],
                       'issues': row.get('issues', []), 'evidenceFailures': row.get('evidenceFailures', [])})
        if len(report['flows']) != len(WIDTHS) or len(report['unknownPath']) != len(WIDTHS):
            report['failures'].append({'phase': 'flow-coverage', 'message': 'Missing navigation/unknown-path width'})
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
        require(contract['sourceRoot'] == SOURCE_ROOT, 'exact_Seogu_source_root_required')
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
