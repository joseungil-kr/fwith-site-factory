#!/usr/bin/env python3
"""Capture the separately pinned Yeosu corrected production dist on a permitted runner, without publishing.

Prepared locally only: this module does not launch anything when imported. Runtime
requires Node 24, installed Playwright Chromium and permission to open loopback
sockets. It never substitutes a synthetic 404 server or weakens the browser sandbox.
The capture machine's checks cannot approve an independent review of the pixels.

Reused check design: Yeosu candidate/scripts/browser_qa.py and Gangdong
control/scripts/direct-seoul-gangdong/{production_capture,browser_rendering}.py.
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
from layout_evidence import HEADING_METRICS_JS, heading_issues, supplemental_evidence

SOURCE_ROOT = 'site-factory/yeosu-flower'
ROOT = SOURCE_ROOT + '/portable/yeosu-portable-build-inputs-20261015/yeosu-local-implementation-20261015/candidate'
ORIGIN = 'https://yeosu.fwith.kr'
ARTICLE = '/regions/yeosu-jeonnam-hospital-funeral-wreath/'
ROUTES = ('/', '/regions/', ARTICLE, '/404.html')
WIDTHS = (320, 390, 1280)
HEIGHT = 900
MISSING = '/does-not-exist-yeosu-production-capture/'
PRODUCTS = ()  # Historical image files remain frozen; no displayed product cards are applicable.
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
            'control': {p.relative_to(DIRECTORY).as_posix(): sha(p)
                        for p in sorted(DIRECTORY.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}}



def capture_inputs(root):
    """Load independent frozen original/spec expectations; never observe candidate DOM."""
    from production_build import load_ui_expectations
    return load_ui_expectations()


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
    if route == '/404.html' and metrics.get('ogProperties'):
        issues.append('404 contains social metadata')
    if metrics.get('title') != expected['content']['title'] or metrics.get('description') != [expected['content']['metaDescription']]:
        issues.append('Title or description differs from frozen source')
    if metrics.get('ogProperties') != expected['socialProperties']:
        issues.append('Full frozen OG metadata mismatch')
    if metrics.get('twitterProperties') != expected['twitterProperties']:
        issues.append('Full frozen Twitter metadata mismatch')
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
  twitterProperties:all('meta[name^="twitter:"]').map(e=>({name:e.getAttribute('name'),content:e.content})),
  bodyText:document.body.innerText,
  skuOrderLinks:all('a[data-order-product-sku],a[href*="shop/item.php"],a[href*="it_id="]').map(e=>({href:e.getAttribute('href'),label:e.textContent.trim()})),
  noticeLinks:all('main a[href="https://fwith.co.kr/page/notice.php"]').map(e=>({href:e.getAttribute('href'),visible:visible(e)})),
  revision:all('meta[name="site-factory-revision"]').map(e=>e.content),
  banners:all('[data-shared-flower-banner]').map(e=>e.getAttribute('data-shared-flower-banner')),
  images:all('img').map(i=>({src:i.getAttribute('src'),alt:i.alt,loaded:i.complete&&i.naturalWidth>0,
   naturalWidth:i.naturalWidth,naturalHeight:i.naturalHeight,width:i.getBoundingClientRect().width,
   height:i.getBoundingClientRect().height,objectFit:getComputedStyle(i).objectFit})),
  products:all('[data-product-sku]').map(e=>({sku:e.dataset.productSku,
   image:e.querySelector('img')?.getAttribute('src'),alt:e.querySelector('img')?.alt,
   price:e.querySelector('.product-price')?.textContent.trim(),
   links:[...e.querySelectorAll('a[data-order-product-sku]')].map(a=>({sku:a.dataset.orderProductSku,href:a.getAttribute('href'),label:a.textContent.trim(),ariaLabel:a.getAttribute('aria-label'),visible:visible(a),width:a.getBoundingClientRect().width,height:a.getBoundingClientRect().height}))})),
  faq:all('[data-visible-faq] [data-faq-question]').map(question=>{const next=question.nextElementSibling,answer=next?.matches('[data-faq-answer]')?next:null;return {question:question.innerText,
   answer:answer?.innerText??null,visible:visible(question.closest('[data-visible-faq]')),questionVisible:visible(question),answerVisible:visible(answer),collapsed:!!question.closest('details:not([open])')};}),
  faqQuestionCount:all('[data-faq-question]').length,faqAnswerCount:all('[data-faq-answer]').length,
  navigation:links(all('.desktop-navigation a')),mobileNavigation:links(all('.mobile-menu nav a')),
  breadcrumbs:all('.breadcrumb a,.breadcrumb [aria-current="page"]').map(e=>({label:e.textContent.trim(),href:e.getAttribute('href'),current:e.getAttribute('aria-current')==='page'})),
  supportCards:all('[data-content-card]').map(e=>({title:e.querySelector('h2').textContent.trim(),summary:e.querySelector('p').textContent.trim(),links:links([...e.querySelectorAll('a')])})),
  internalLinks:links(all('main a[href^="/"]')),
  bodyCtas:all('main a[href]').map(e=>({label:e.textContent.trim(),href:e.getAttribute('href'),visible:visible(e),width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height})),
  overflow:all('main *').filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.left<-.5||r.right>innerWidth+.5)}).slice(0,12).map(e=>({tag:e.tagName,className:e.className})),
  ctas:all('[data-order-product-sku],.page-card > a,.actions a,.mobile-bar a').filter(visible).map(e=>({href:e.getAttribute('href'),height:e.getBoundingClientRect().height}))
 };}'''


def inspect_metrics(metrics, expected, spec, width, revision):
    issues = metadata_issues(metrics, expected, revision)
    route = expected['path']
    issues.extend(heading_issues(metrics.get('headingGlyphs'), expected['h2Headings'], width))
    expected_first = [{'text': expected['content']['firstAnswer'], 'visible': True}] if expected['content']['firstAnswer'] is not None else []
    if metrics.get('firstAnswer') != expected_first:
        issues.append('Exact first answer missing, changed, or invisible')
    if metrics['viewport'] != width or metrics['scrollWidth'] > width or metrics['overflow']:
        issues.append('Horizontal overflow or viewport mismatch')
    if metrics['banners'] != (list(BANNERS) if route in ('/', ARTICLE) else []):
        issues.append('Exact primary-only three-banner sequence mismatch')
    if metrics.get('skuOrderLinks') != []:
        issues.append('Zero SKU order links required')
    if [{'src': i['src'], 'alt': i.get('alt')} for i in metrics['images']] != expected['images']:
        issues.append('Exact frozen image src/alt sequence mismatch')
    for phrase in expected['requiredBodyPhrases']:
        if phrase not in metrics.get('bodyText', ''):
            issues.append('Restriction/seller attribution phrase missing: ' + phrase)
    if expected['requiredNoticeHref'] and not any(
            a.get('href') == expected['requiredNoticeHref'] and a.get('visible') is True
            for a in metrics.get('noticeLinks', [])):
        issues.append('Seller notice link missing or invisible')
    expected_skus = expected['productCardIds']
    if [p['sku'] for p in metrics['products']] != expected_skus:
        issues.append('Zero displayed product cards required')
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
        if actual_links != expected_links or product['image'] != '/images/products/' + sku + '.jpg' or product['price'] != source_product['priceText'] or product['alt'] != source_product['alt']:
            issues.append('Product source/CTA/image differs: ' + sku)
    if len(metrics['images']) != (3 if route in ('/', ARTICLE) else 0):
        issues.append('Exact page image count mismatch')
    for image in metrics['images']:
        if not image['loaded'] or image['objectFit'] != 'contain' or image['width'] <= 0 or image['height'] <= 0:
            issues.append('Image decode/contain/size failure: ' + str(image['src']))
        size = (1774, 887) if '/shared-banners/' in (image['src'] or '') else (500, 500)
        if (image['naturalWidth'], image['naturalHeight']) != size:
            issues.append('Image intrinsic dimensions changed: ' + str(image['src']))
        if size == (1774, 887) and (not image['height'] or abs(image['width'] / image['height'] - 2) > .01):
            issues.append('Banner display aspect ratio changed')
    if metrics.get('faqQuestionCount') != (4 if route == ARTICLE else 0) or metrics.get('faqAnswerCount') != (4 if route == ARTICLE else 0):
        issues.append('Exact FAQ question and answer node counts mismatch')
    expected_faq = [{k: f[k] for k in ('question', 'answer')} for f in spec['faqs']] if route == ARTICLE else []
    if [{k: f[k] for k in ('question', 'answer')} for f in metrics['faq']] != expected_faq:
        issues.append('Exact article-only FAQ text/count mismatch')
    if any(not f['visible'] or f['collapsed'] for f in metrics['faq']):
        issues.append('FAQ collapsed or invisible')
    if any(f.get('questionVisible') is not True or f.get('answerVisible') is not True for f in metrics['faq']):
        issues.append('FAQ question or answer hidden, missing, or has zero geometry')
    nav = expected['navigation']
    if metrics['navigation'] != nav or metrics['mobileNavigation'] != nav:
        issues.append('Main navigation includes unsupported route or label')
    crumbs = [{k: b[k] for k in ('label', 'href', 'current')} for b in expected['breadcrumbs']] if expected['breadcrumbVisible'] else []
    if metrics['breadcrumbs'] != crumbs:
        issues.append('Exact breadcrumb chain mismatch')
    for link in expected['internalLinks']:
        if {'label': link['label'], 'href': link['href']} not in metrics['internalLinks']:
            issues.append('Required body/breadcrumb inbound link missing: ' + link['href'])
    cards = [{'title': c['title'], 'summary': c['summary'], 'links': [{'label': c['ctaLabel'], 'href': c['href']}]} for c in expected['contentCards']] if route == '/regions/' else []
    if metrics['supportCards'] != cards:
        issues.append('Support page must have exactly its one real child')
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
        page.locator('.desktop-navigation a').filter(has_text='여수전남병원장례식장 오브제 안내와 상담').click()
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
        menu.get_by_role('link', name='여수전남병원장례식장 오브제 안내와 상담', exact=True).click()
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
    # Inspect the real body inbound link, parent breadcrumb and single-child support loop.
    page.goto(origin + '/', wait_until='networkidle')
    page.locator('main').get_by_role('link', name='여수전남병원장례식장 오브제·주문 조건 안내', exact=True).click()
    result['bodyInboundUrl'] = page.url
    page.locator('.breadcrumb').get_by_role('link', name='안내 바로가기', exact=True).click()
    result['breadcrumbParentUrl'] = page.url
    page.locator('[data-content-card]').get_by_role('link', name='여수전남병원장례식장 오브제·주문 조건 안내', exact=True).click()
    result['supportChildUrl'] = page.url
    page.locator('.breadcrumb').get_by_role('link', name='여수 장례식장 오브제 안내와 상담', exact=True).click()
    result['breadcrumbHomeUrl'] = page.url
    if [result[k] for k in ('bodyInboundUrl', 'breadcrumbParentUrl', 'supportChildUrl', 'breadcrumbHomeUrl')] != [origin + ARTICLE, origin + '/regions/', origin + ARTICLE, origin + '/']:
        result['issues'].append('Native body inbound/support/breadcrumb navigation failure')
    return result


def inspect(root, out, pages, spec, revision, port):
    from playwright.sync_api import sync_playwright
    root, out = Path(root), Path(out)
    report = {'status': 'machine-qa-failed', 'startedUTC': now(), 'sourceRevision': revision,
              'scope': 'Source88 correction read-only QA through genuine loopback Astro preview only',
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
                                record['metrics']['headingGlyphs'] = page.evaluate(HEADING_METRICS_JS)
                                record['issues'].extend(inspect_metrics(record['metrics'], expected, spec, width, revision))
                                # Retain restriction guidance and four-FAQ pixels as dedicated sections too.
                                for selector, label in (('#section-1', 'seller-restriction'), ('[data-visible-faq]', 'faq')):
                                    if page.locator(selector).count():
                                        target = out / (stem + '-' + label + '.png')
                                        page.locator(selector).screenshot(path=str(target))
                                        record.setdefault('artifacts', []).append({'file': target.name, 'sha256': sha(target), 'bytes': target.stat().st_size})
                                supplemental_evidence(page, out, stem, expected, record, width)
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
    require(out != root and root not in out.parents, 'capture_output_must_be_outside_source_root')
    out.mkdir(parents=True, exist_ok=True)
    revision, before, failures = None, None, []
    try:
        from production_build import source, load
        reject_provider_credentials(os.environ)
        contract = load()[0]
        revision = contract['sourceRevision']
        require(re.fullmatch('[0-9a-f]{40}', revision), 'exact_source_revision_required')
        require(contract['sourceRoot'] == SOURCE_ROOT, 'exact_Yeosu_source_root_required')
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
