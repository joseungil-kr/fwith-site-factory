#!/usr/bin/env python3
"""Capture-contract tests. No browser, server, sockets, build or provider calls.

Optional explicit retained-HTML readback imports the Gokseong runtime with installed
Node in a clean environment; no new dependencies are installed.

Temporary fixtures test rejection/reporting only. Passing these tests does NOT
mean the capture ran or that any screenshot/public URL was verified.
"""
import ast
from copy import deepcopy
import importlib.util
from html.parser import HTMLParser
import os
import json
from pathlib import Path
import sys
import tempfile
import subprocess
import shlex
import shutil
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('gokseong_capture_under_test', HERE / 'production_capture.py')
CAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CAP)
SOURCE = (HERE / 'production_capture.py').read_text()
TREE = ast.parse(SOURCE)
REVISION = 'a' * 40


def fixture_copy():
    products = []
    for sku, total in zip(CAP.PRODUCTS, CAP.REFERENCE_TOTALS):
        products.append({'sku': sku, 'name': 'Fixture', 'photoAlt': sku, 'basePriceKRW': total-10000,
            'additionalShippingKRW': 10000, 'referenceTotalKRW': total, 'finalPriceKRW': None,
            'priceLabel': f'상품 기본가 {total-10000:,}원', 'shippingLabel': '곡성 게시 추가배송비 10,000원',
            'referenceTotalLabel': f'게시금액 합산 참고예산 {total:,}원', 'description': 'Fixture product prose',
            'ctaHref': 'https://fwith.co.kr/shop/item.php?it_id='+sku, 'ctaLabel': 'detail'})
    home = {'h1': 'Fixture H1', 'title': 'Fixture title', 'description': 'Fixture description',
            'lead': ['Fixture first answer'], 'sections': [{'id': key, 'h2': key, 'paragraphs': [key+' prose']} for key in CAP.SECTIONS],
            'faqHeading': 'Fixture FAQ', 'faq': [{'question': 'q'+str(i), 'answer': 'a'+str(i)} for i in range(3)],
            'closing': 'Fixture closing', 'cta': {'label': 'Fixture body action', 'href': 'tel:18440644'},
            'sourceHeading': 'Fixture sources', 'sourceIntro': 'Fixture source intro',
            'sources': [{'label': 'Fixture source', 'url': 'https://example.invalid/source'}]}
    home['sections'][0]['productCardIds'] = list(CAP.PRODUCTS)
    for section in home['sections'][3:]:
        section.update(list=['Fixture item1', 'Fixture item2'], afterList=['Fixture after1', 'Fixture after2'])
    return {'home': home, 'productCards': products,
        'notFound': {'h1': 'Fixture H1', 'title': 'Fixture title', 'description': 'Fixture description',
                     'body': 'Fixture missing', 'cta': {'label': 'Fixture body action', 'href': '/'}},
        'sharedUI': {'productSampleNotice': 'Fixture sample notice', **{x+'Link':x for x in CAP.ANCHORS}},
        'sharedBannerAlt': {x:'Fixture '+x for x in CAP.BANNERS}}


def fixture_plan():
    return {'pages':[{'id':'home','proposedPath':'/'},{'id':'notFound','proposedPath':'/404.html'}],
            'navigation':{'mainMenu':[{'labelSource':'sharedUI.'+x+'Link','href':'/#'+x} for x in CAP.ANCHORS]}}


def fixture_spec():
    copy = fixture_copy()
    return {'productCards': [{'sku': p['sku'], 'name': p['name']+' '+p['sku'], 'priceText': p['priceLabel'],
             'shippingText': p['shippingLabel'], 'referenceText': p['referenceTotalLabel'], 'referenceTotalKRW':p['referenceTotalKRW'],
             'description': p['description'], 'alt': p['photoAlt'],
             'cta': {'href':p['ctaHref'],'label':p['ctaLabel'],'accessibleLabel':None}} for p in copy['productCards']],
            'faqs': copy['home']['faq'],
            'banners': [{'src':'/images/shared-banners/flower-'+name+'.webp','alt':'Fixture '+name} for name in CAP.BANNERS],
            'productSampleNotice':'Fixture sample notice', 'menuOpen':'Fixture menu open', 'menuClose':'Fixture menu close'}


def fixture_page(route='/'):
    primary, copy, spec = route=='/', fixture_copy(), fixture_spec()
    content = copy['home' if primary else 'notFound']
    required = ([{'label':p['cta']['label'],'href':p['cta']['href']} for p in spec['productCards']] if primary else []) + [content['cta']]
    page = {'path':route,'id':'home' if primary else 'not-found',
        'content':{'h1':content['h1'],'title':content['title'],'metaDescription':content['description'],'firstAnswer':content['lead'][0] if primary else None},
        'productCardIds':list(CAP.PRODUCTS) if primary else [],'faqIds':list(range(3)) if primary else [],
        'navigation':[{'label':x,'href':'/#'+x} for x in CAP.ANCHORS],
        'breadcrumbVisible':False,'breadcrumbs':[],'breadcrumbAriaLabel':None,'contentCards':[],
        'internalLinks':[] if primary else [content['cta']], 'ctas':[content['cta']], 'requiredCtas':required,
        'sections':list(CAP.SECTIONS) if primary else [],'reviewedBlocks':CAP.reviewed_blocks(copy,'home' if primary else 'notFound'),
        'mainLinks':required+([{'label':r['label'],'href':r['url']} for r in content['sources']] if primary else []),
        'chromeLinks':{'skipLink':[{'label':'Fixture skip','href':'#main-content'}], 'brand':[{'label':'Fixture brand','href':'/'}],
            'footer':[{'label':'Fixture phone','href':'tel:18440644'},{'label':'Fixture home','href':'/'}],
            'mobileBar':[{'label':'Fixture home','href':'/'},{'label':'Fixture phone','href':'tel:18440644'}]}}
    page['socialMetadata'] = CAP.expected_social(page,spec['productCards'][0]['alt'])
    return page


def fixture_metrics(route='/', width=390):
    primary, spec, page = route=='/', fixture_spec(), fixture_page(route)
    geometry = lambda links:[{**r,'visible':True,'width':200,'height':44} for r in links]
    metrics={'viewport':width,'scrollWidth':width,'overflow':[], 'h1':['Fixture H1'],'title':'Fixture title','description':['Fixture description'],
        'revision':[REVISION],'firstAnswer':[{'text':'Fixture first answer','visible':True}] if primary else [],
        'robots':['index,follow' if primary else 'noindex,follow'],'canonical':[CAP.ORIGIN+'/'] if primary else [],
        'ogUrl':[CAP.ORIGIN+'/'] if primary else [],'ogProperties':[], 'socialMetadata':deepcopy(page['socialMetadata']),
        'banners':list(CAP.BANNERS) if primary else [],'images':[],'products':[],
        'faq':[{**f,'visible':True,'questionVisible':True,'answerVisible':True,'collapsed':False} for f in spec['faqs']] if primary else [],
        'faqQuestionCount':3 if primary else 0,'faqAnswerCount':3 if primary else 0,
        'navigation':deepcopy(page['navigation']),'mobileNavigation':deepcopy(page['navigation']),'chromeLinks':deepcopy(page['chromeLinks']),
        'breadcrumbs':[],'breadcrumbContainers':[],'internalLinks':deepcopy(page['internalLinks']),'supportCards':[],
        'ctas':[{'href':'/','height':44}],'bodyCtas':geometry(page['mainLinks']),'requiredCtas':geometry(page['requiredCtas']),
        'productSampleNotice':[{'text':spec['productSampleNotice'],'visible':True}] if primary else [],
        'reviewedBlocks':[{**b,'visible':True} for b in page['reviewedBlocks']],
        'sections':[{'id':name,'visible':True} for name in page['sections']],
        'ids':['main-content']+list(CAP.SECTIONS)+['faq'] if primary else ['main-content'],
        'anchors':[r['href'] for r in page['navigation']+page['mainLinks']], 'schemaCount':0,
        'bannerPositions':[{'variant':'message','previousId':'opening','nextId':'products','nextClosing':False},
            {'variant':'budget','previousId':'budget','nextId':'ribbon','nextClosing':False},
            {'variant':'consultation','previousId':'faq','nextId':'','nextClosing':True}] if primary else []}
    metrics['chromeVisibleLinks']={group:[{**r,'width':100,'height':44} for r in rows] for group,rows in {
        'brand':page['chromeLinks']['brand'],'footer':page['chromeLinks']['footer'],
        'desktop':page['navigation'] if width>860 else [],'mobileBar':page['chromeLinks']['mobileBar'] if width<=860 else []}.items()}
    if primary:
        metrics['images']=[{**b,'loaded':True,'visible':True,'objectFit':'contain','width':300,'height':150,'naturalWidth':1774,'naturalHeight':887} for b in spec['banners']]
        metrics['images'] += [{'src':'/images/products/'+p['sku']+'.jpg','alt':p['alt'],'loaded':True,'visible':True,'objectFit':'contain','width':200,'height':200,'naturalWidth':500,'naturalHeight':500} for p in spec['productCards']]
        metrics['products']=[{'sku':p['sku'],'name':p['name'],'image':'/images/products/'+p['sku']+'.jpg','alt':p['alt'],
            'price':p['priceText'],'shipping':p['shippingText'],'reference':p['referenceText'],'referenceTotal':str(p['referenceTotalKRW']),
            'referenceVisible':True,'description':p['description'],
            'links':[{'sku':p['sku'],'href':p['cta']['href'],'label':p['cta']['label'],'ariaLabel':None,'visible':True,'width':200,'height':44}]} for p in spec['productCards']]
    return metrics


class StaticHarnessContract(unittest.TestCase):
    def test_exact_routes_and_viewports(self):
        self.assertEqual(CAP.ROUTES, ('/', '/404.html'))
        self.assertEqual(CAP.WIDTHS, (320, 390, 1280))
        self.assertEqual(len(CAP.expected_inventory([fixture_page(r) for r in CAP.ROUTES])), 6)

    def test_only_sandboxed_default_browser_launch(self):
        launches = [n for n in ast.walk(TREE) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'launch']
        self.assertEqual(len(launches), 1)
        values = {kw.arg: kw.value for kw in launches[0].keywords}
        self.assertIs(ast.literal_eval(values['chromium_sandbox']), True)
        self.assertNotIn('executable_path', values)
        self.assertNotIn('args', values)
        self.assertNotIn('--' + 'no-' + 'sandbox', SOURCE)
        self.assertIn("context.route_web_socket('**/*', block_socket)", SOURCE)
        self.assertIn("service_workers='block'", SOURCE)

    def test_real_astro_preview_and_clean_env(self):
        self.assertIn('cli, package_evidence = resolve_astro_cli(root)', SOURCE)
        self.assertIn("lock.get('bin')", SOURCE)
        self.assertIn("'preview', '--host', '127.0.0.1', '--port'", SOURCE)
        self.assertIn("r'v24[.]\\d+[.]\\d+'", SOURCE)
        self.assertNotIn('HTTPServer', SOURCE)
        self.assertNotIn('SafeServer', SOURCE)
        self.assertNotIn('serve_forever', SOURCE)
        self.assertIn('process.terminate()', SOURCE)
        self.assertIn('process.kill()', SOURCE)
        self.assertIn("env=clean_environment(os.environ)", SOURCE)

    def test_genuine_http_and_dist_byte_checks(self):
        self.assertIn("missing['httpStatus'] != 404", SOURCE)
        self.assertIn("sha(root / 'dist/404.html')", SOURCE)
        self.assertIn('hashlib.sha256(response.body()).hexdigest()', SOURCE)
        self.assertIn("source(checkout, 'postbuild', os.environ)", SOURCE)
        self.assertIn('contract = load()[0]', SOURCE)
        self.assertIn('before == after', SOURCE)


    def test_unknown_path_recovery_uses_verified_gokseong_cta(self):
        self.assertIn("name=not_found['ctas'][0]['label']", SOURCE)
        self.assertNotIn('목포', SOURCE)
        calls = [n for n in ast.walk(TREE) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr == 'get_by_role']
        dynamic = [n for n in calls if any(k.arg == 'name' and isinstance(k.value,ast.Subscript) for k in n.keywords)]
        self.assertEqual(len(dynamic),1)
        self.assertTrue(any(k.arg == 'exact' and ast.literal_eval(k.value) is True for k in dynamic[0].keywords))

    def test_import_has_no_runner_side_effect(self):
        # Runtime calls exist only in functions or __main__; loading does not start anything.
        with patch('subprocess.Popen', side_effect=AssertionError('process must not start')), \
             patch('subprocess.run', side_effect=AssertionError('command must not run')):
            again = importlib.util.module_from_spec(SPEC)
            SPEC.loader.exec_module(again)
            self.assertEqual(again.SOURCE_ROOT, 'site-factory/gokseong-flower')


class PureHelpers(unittest.TestCase):
    def test_exact_origin_rejects_lookalikes_and_external_schemes(self):
        origin = 'http://127.0.0.1:43817'
        for url in (origin + '/', origin + '/images/image.jpg?a=b'):
            self.assertTrue(CAP.same_origin(url, origin))
        for url in ('http://127.0.0.1:43818/', 'https://127.0.0.1:43817/', 'http://localhost:43817/',
                    'http://127.0.0.1.evil:43817/', 'http://user@127.0.0.1:43817/',
                    'https://gokseong.fwith.kr/', 'file:///tmp/x', 'data:text/plain,hello', 'ws://127.0.0.1:43817/'):
            self.assertFalse(CAP.same_origin(url, origin), url)

    def test_source_process_env_is_allowlisted(self):
        supplied = {'PATH': '/safe/bin', 'HOME': '/safe/home', 'LANG': 'C.UTF-8', 'SITE_URL': CAP.ORIGIN,
             'SITE_RELEASE_MODE': 'production', 'CLOUDFLARE_API_TOKEN': 'test-value', 'GITHUB_TOKEN': 'test-value',
             'GITHUB_SHA': REVISION, 'GITHUB_RUN_ID': '12345', 'NODE_OPTIONS': '--require=unexpected', 'LD_PRELOAD': 'unexpected', 'HTTPS_PROXY': 'unexpected'}
        clean = CAP.clean_environment(supplied)
        self.assertEqual(set(clean), {'PATH', 'HOME', 'LANG', 'CI', 'ASTRO_TELEMETRY_DISABLED', 'NO_COLOR'})
        self.assertEqual(clean['PATH'], '/safe/bin')
        self.assertEqual(clean['ASTRO_TELEMETRY_DISABLED'], '1')

    def test_provider_credentials_fail_closed(self):
        CAP.reject_provider_credentials({'PATH': '/bin', 'CLOUDFLARE_API_TOKEN': ''})
        for key in ('CLOUDFLARE_API_TOKEN', 'CF_API_TOKEN', 'AWS_ACCESS_KEY_ID', 'VERCEL_TOKEN', 'NETLIFY_AUTH_TOKEN'):
            with self.assertRaisesRegex(RuntimeError, 'provider_credentials_forbidden'):
                CAP.reject_provider_credentials({key: 'test-value'})


    def test_all_exact_og_and_twitter_fields_reject_mutations(self):
        for route in ('/',):
            for index in range(len(fixture_page(route)['socialMetadata'])):
                for mutation in ('missing', 'duplicate', 'changed', 'wrong-attribute'):
                    metrics = fixture_metrics(route)
                    if mutation == 'missing':
                        metrics['socialMetadata'].pop(index)
                    elif mutation == 'duplicate':
                        metrics['socialMetadata'].append(deepcopy(metrics['socialMetadata'][index]))
                    elif mutation == 'changed':
                        metrics['socialMetadata'][index]['content'] = 'wrong'
                    else:
                        metrics['socialMetadata'][index]['attribute'] = 'wrong'
                    self.assertTrue(CAP.metadata_issues(metrics, fixture_page(route), REVISION), (route, index, mutation))
        metrics = fixture_metrics('/404.html')
        metrics['socialMetadata'] = [{'attribute': 'name', 'name': 'twitter:card', 'content': 'summary'}]
        self.assertIn('404 contains social metadata', CAP.metadata_issues(metrics, fixture_page('/404.html'), REVISION))

    def test_gokseong_shipping_name_description_notice_and_banner_alt_are_required(self):
        for field in ('shipping', 'name', 'description', 'reference', 'referenceTotal'):
            for index in range(4):
                metrics = fixture_metrics('/')
                metrics['products'][index][field] = 'Changed'
                self.assertTrue(CAP.inspect_metrics(metrics, fixture_page('/'), fixture_spec(), 390, REVISION))
        for mutation in ('wrong-text', 'hidden', 'missing', 'duplicate'):
            metrics = fixture_metrics('/')
            if mutation == 'wrong-text':
                metrics['productSampleNotice'][0]['text'] = 'Changed'
            elif mutation == 'hidden':
                metrics['productSampleNotice'][0]['visible'] = False
            elif mutation == 'missing':
                metrics['productSampleNotice'] = []
            else:
                metrics['productSampleNotice'] *= 2
            self.assertTrue(CAP.inspect_metrics(metrics, fixture_page('/'), fixture_spec(), 390, REVISION))
        for field in ('src', 'alt'):
            metrics = fixture_metrics('/')
            metrics['images'][0][field] = 'Changed'
            self.assertIn('Exact image source/alt inventory mismatch', CAP.inspect_metrics(metrics, fixture_page('/'), fixture_spec(), 390, REVISION))

    def test_exact_cta_and_shared_links_reject_missing_extra_changed_or_hidden(self):
        mutations = (
            lambda m: m['requiredCtas'].clear(),
            lambda m: m['requiredCtas'].append(deepcopy(m['requiredCtas'][0])),
            lambda m: m['requiredCtas'][0].update(visible=False),
            lambda m: m['requiredCtas'][0].update(height=43),
            lambda m: m['requiredCtas'][0].update(href='/wrong/'),
            lambda m: m['bodyCtas'].append({'label': 'Unapproved link', 'href': '/wrong/', 'visible': True, 'width': 100, 'height': 44}),
            lambda m: m['chromeLinks']['mobileBar'][1].update(href='tel:00000000'),
            lambda m: m['chromeVisibleLinks']['footer'].pop(),
            lambda m: m['chromeVisibleLinks']['mobileBar'].clear(),
            lambda m: m['chromeVisibleLinks']['brand'][0].update(width=0),
        )
        for index, mutation in enumerate(mutations):
            metrics = fixture_metrics('/')
            mutation(metrics)
            self.assertTrue(CAP.inspect_metrics(metrics, fixture_page('/'), fixture_spec(), 390, REVISION), index)

    def test_frozen_page_metadata_denominators(self):
        for route in CAP.ROUTES:
            with self.subTest(route=route):
                self.assertEqual(CAP.metadata_issues(fixture_metrics(route), fixture_page(route), REVISION), [])
                metrics = fixture_metrics(route)
                metrics['revision'] = ['b' * 40]
                self.assertIn('Exact metadata mismatch: revision', CAP.metadata_issues(metrics, fixture_page(route), REVISION))


    def test_404_must_have_no_canonical_or_og(self):
        metrics = fixture_metrics('/404.html')
        metrics.update(canonical=[CAP.ORIGIN + '/404.html'], ogUrl=[CAP.ORIGIN + '/404.html'], ogProperties=[{'name': 'og:title'}])
        self.assertEqual(len(CAP.metadata_issues(metrics, fixture_page('/404.html'), REVISION)), 3)

    def test_positive_metric_fixtures_are_only_pure_fixtures(self):
        for route in CAP.ROUTES:
            for width in CAP.WIDTHS:
                self.assertEqual(CAP.inspect_metrics(fixture_metrics(route, width), fixture_page(route), fixture_spec(), width, REVISION), [])

    def test_mutated_banner_product_faq_image_and_overflow_fail(self):
        mutations = (
            lambda m: m['banners'].pop(),
            lambda m: m['products'].pop(),
            lambda m: m['products'][0]['links'][0].update(href='https://example.invalid/'),
            lambda m: m['images'][0].update(loaded=False),
            lambda m: m['images'][0].update(objectFit='cover'),
            lambda m: m['images'][0].update(naturalWidth=1),
            lambda m: m['images'][0].update(width=150),
            lambda m: m.update(scrollWidth=391),
            lambda m: m.update(overflow=[{'tag': 'P'}]),
            lambda m: m['faq'][0].update(answer='Changed'),
            lambda m: m['faq'][0].update(collapsed=True),
            lambda m: m['ctas'][0].update(height=43),
            lambda m: m['navigation'].append({'href': '/regions/', 'label': 'extra'}),
        )
        for index, mutate in enumerate(mutations):
            metrics = fixture_metrics('/')
            mutate(metrics)
            self.assertTrue(CAP.inspect_metrics(metrics, fixture_page('/'), fixture_spec(), 390, REVISION), index)

    def test_first_answer_must_match_and_be_individually_visible(self):
        self.assertIn("firstAnswer:all('[data-first-answer]')", CAP.METRICS_JS)
        for kind in ('hidden', 'missing-visibility', 'changed', 'missing-node', 'duplicate'):
            metrics = fixture_metrics('/')
            if kind == 'hidden':
                metrics['firstAnswer'][0]['visible'] = False
            elif kind == 'missing-visibility':
                del metrics['firstAnswer'][0]['visible']
            elif kind == 'changed':
                metrics['firstAnswer'][0]['text'] = 'Changed'
            elif kind == 'missing-node':
                metrics['firstAnswer'] = []
            else:
                metrics['firstAnswer'].append(deepcopy(metrics['firstAnswer'][0]))
            errors = CAP.inspect_metrics(metrics, fixture_page('/'), fixture_spec(), 390, REVISION)
            self.assertIn('Exact first answer missing, changed, or invisible', errors)

    def test_each_product_cta_must_be_visible_with_real_geometry(self):
        self.assertIn('visible:visible(a),width:a.getBoundingClientRect().width,height:a.getBoundingClientRect().height', CAP.METRICS_JS)
        for product_index in range(4):
            for change in ({'visible': False}, {'width': 0}, {'height': 0}, {'height': 43}, {'visible': None}):
                metrics = fixture_metrics('/')
                metrics['products'][product_index]['links'][0].update(change)
                errors = CAP.inspect_metrics(metrics, fixture_page('/'), fixture_spec(), 390, REVISION)
                self.assertTrue(any('Required product CTA invisible or has invalid geometry' in e for e in errors))

    def test_required_body_cta_cannot_disappear_behind_visible_other_cta(self):
        self.assertIn("bodyCtas:all('main a[href]')", CAP.METRICS_JS)
        for kind in ('hidden', 'missing-visibility', 'zero-width', 'zero-height', 'absent', 'wrong-label', 'wrong-href'):
            metrics = fixture_metrics('/')
            if kind == 'hidden':
                metrics['bodyCtas'][4]['visible'] = False
            elif kind == 'missing-visibility':
                del metrics['bodyCtas'][4]['visible']
            elif kind == 'zero-width':
                metrics['bodyCtas'][4]['width'] = 0
            elif kind == 'zero-height':
                metrics['bodyCtas'][4]['height'] = 0
            elif kind == 'absent':
                metrics['bodyCtas'] = []
            elif kind == 'wrong-label':
                metrics['bodyCtas'][4]['label'] = 'Other label'
            else:
                metrics['bodyCtas'][4]['href'] = '/'
            metrics['bodyCtas'].append({'label': 'Unrelated action', 'href': '/', 'visible': True, 'width': 200, 'height': 44})
            errors = CAP.inspect_metrics(metrics, fixture_page('/'), fixture_spec(), 390, REVISION)
            self.assertTrue(any('Required body CTA missing or invisible' in e for e in errors))

    def test_hidden_or_missing_question_cannot_pass_visible_faq_wrapper(self):
        self.assertIn('questionVisible:visible(question)', CAP.METRICS_JS)
        self.assertIn('getBoundingClientRect().width>0', CAP.METRICS_JS)
        for value in (False, None, 0, '', 'true', 'remove-field'):
            metrics = fixture_metrics('/')
            self.assertTrue(metrics['faq'][0]['visible'])
            if value == 'remove-field':
                del metrics['faq'][0]['questionVisible']
            else:
                metrics['faq'][0]['questionVisible'] = value
            errors = CAP.inspect_metrics(metrics, fixture_page('/'), fixture_spec(), 390, REVISION)
            self.assertIn('FAQ question or answer hidden, missing, or has zero geometry', errors)

    def test_hidden_or_missing_answer_cannot_pass_visible_faq_wrapper(self):
        self.assertIn('answerVisible:visible(answer)', CAP.METRICS_JS)
        self.assertIn('checkVisibility({checkOpacity:true,checkVisibilityCSS:true})', CAP.METRICS_JS)
        self.assertIn('getBoundingClientRect().height>0', CAP.METRICS_JS)
        for value in (False, None, 0, '', 'true', 'remove-field'):
            metrics = fixture_metrics('/')
            self.assertTrue(metrics['faq'][0]['visible'])
            if value == 'remove-field':
                del metrics['faq'][0]['answerVisible']
            else:
                metrics['faq'][0]['answerVisible'] = value
            errors = CAP.inspect_metrics(metrics, fixture_page('/'), fixture_spec(), 390, REVISION)
            self.assertIn('FAQ question or answer hidden, missing, or has zero geometry', errors)




    def test_seal_hashes_real_file_bytes_and_keeps_pending_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / 'fixture.txt').write_bytes(b'fixture-only; not captured browser evidence')
            CAP.seal(out, REVISION)
            sealed = json.loads((out / 'artifact-manifest.json').read_text())
            self.assertEqual(sealed['files']['fixture.txt']['sha256'], CAP.sha(out / 'fixture.txt'))
            self.assertNotIn('artifact-manifest.json', sealed['files'])
            self.assertEqual(sealed['pixelReview'], 'pending')
            self.assertFalse(sealed['publicHTTPVerified'])
            self.assertFalse(sealed['publicationExecuted'])
            original = sealed['files']['fixture.txt']['sha256']
            (out / 'fixture.txt').write_bytes(b'mutated test fixture')
            self.assertNotEqual(original, CAP.sha(out / 'fixture.txt'))

    def test_symlink_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'actual').write_text('fixture')
            (root / 'link').symlink_to(root / 'actual')
            with self.assertRaisesRegex(RuntimeError, 'symlink'):
                CAP.inventory(root)
            with self.assertRaisesRegex(RuntimeError, 'symlink'):
                CAP.seal(root, REVISION)



class StaticElement:
    def __init__(self, tag='document', attrs=None):
        self.tag, self.attrs, self.children = tag, dict(attrs or []), []

    def text(self):
        return ''.join(c if isinstance(c, str) else c.text() for c in self.children).strip()

    def all(self, tag=None, attr=None, value=None, css_class=None):
        found = []
        for child in self.children:
            if isinstance(child, str):
                continue
            if (tag is None or child.tag == tag) and (attr is None or attr in child.attrs and (value is None or child.attrs[attr] == value)) and (css_class is None or css_class in child.attrs.get('class', '').split()):
                found.append(child)
            found.extend(child.all(tag, attr, value, css_class))
        return found


class StaticHTML(HTMLParser):
    """Parse retained HTML only. This does not assert rendered DOM/visibility/focus."""
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = StaticElement()
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        element = StaticElement(tag, attrs)
        self.stack[-1].children.append(element)
        if tag not in ('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'):
            self.stack.append(element)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)





class GokseongSingleHomeContract(unittest.TestCase):
    def test_native_contract_accepts_exact_reviewed_scope(self):
        self.assertTrue(CAP.validate_native_contract(fixture_copy(),fixture_plan(),fixture_page()['navigation']))

    def test_no_partial_duplicate_or_legacy_capture_inventory(self):
        for routes in ([], ['/'], ['/','/'], ['/','/regions/','/404.html'], ['/404.html','/']):
            with self.assertRaisesRegex(RuntimeError,'exact_two_page'):
                CAP.expected_inventory([{'path':r} for r in routes])

    def test_scope_and_reference_price_mutations_rejected(self):
        mutations = [lambda c:c.update(detail={}),lambda c:c['home']['sections'].reverse(),
            lambda c:c['home']['sections'][0].update(card={}),lambda c:c['home']['faq'].pop(),
            lambda c:c['productCards'].reverse(),lambda c:c['home']['sections'][0]['productCardIds'].reverse()]
        for field,value in [('basePriceKRW',59001),('additionalShippingKRW',None),('additionalShippingKRW',False),
            ('referenceTotalKRW',69001),('finalPriceKRW',69000),('priceLabel','0원'),('shippingLabel','unknown'),('referenceTotalLabel','0원')]:
            mutations.append(lambda c,f=field,v=value:c['productCards'][0].update({f:v}))
        for mutate in mutations:
            copy=fixture_copy();mutate(copy)
            with self.assertRaises(RuntimeError):CAP.validate_native_contract(copy,fixture_plan(),fixture_page()['navigation'])

    def test_navigation_is_bound_to_reviewed_plan_and_labels(self):
        for mutation in ('href','label','extra'):
            nav=fixture_page()['navigation'];plan=fixture_plan()
            if mutation=='extra':nav.append({'href':'/regions/','label':'legacy'})
            elif mutation=='href':plan['navigation']['mainMenu'][0]['href']='#products'
            else:nav[0]['label']='Changed'
            with self.assertRaises(RuntimeError):CAP.validate_native_contract(fixture_copy(),plan,nav)

    def test_list_afterlist_reference_and_source_projection_are_required(self):
        blocks=fixture_page()['reviewedBlocks']
        for text in ['Fixture item1','Fixture item2','Fixture after1','Fixture after2','Fixture source intro']:
            self.assertIn(text,[b['text'] for b in blocks])
        for index in range(len(blocks)):
            for change in ('missing','text','hidden','tag'):
                metrics=fixture_metrics()
                if change=='missing':metrics['reviewedBlocks'].pop(index)
                elif change=='hidden':metrics['reviewedBlocks'][index]['visible']=False
                else:metrics['reviewedBlocks'][index][change]='changed'
                self.assertIn('Exact reviewed body blocks missing, changed, reordered, or invisible',CAP.inspect_metrics(metrics,fixture_page(),fixture_spec(),390,REVISION))

    def test_all_five_sections_and_anchor_targets_are_unique_visible(self):
        mutations=[lambda m:m['sections'].reverse(),lambda m:m['sections'].pop(),lambda m:m['sections'][0].update(visible=False),
            lambda m:m['ids'].append('products'),lambda m:m['ids'].remove('faq'),lambda m:m['anchors'].append('/regions/'),
            lambda m:m['bannerPositions'][1].update(nextId='order'),lambda m:m.update(schemaCount=1)]
        for mutate in mutations:
            m=fixture_metrics();mutate(m);self.assertTrue(CAP.inspect_metrics(m,fixture_page(),fixture_spec(),390,REVISION))

    def test_reference_total_and_every_image_must_be_visible(self):
        for index in range(4):
            m=fixture_metrics();m['products'][index]['referenceVisible']=False
            self.assertTrue(CAP.inspect_metrics(m,fixture_page(),fixture_spec(),390,REVISION))
        for index in range(7):
            m=fixture_metrics();m['images'][index]['visible']=False
            self.assertTrue(CAP.inspect_metrics(m,fixture_page(),fixture_spec(),390,REVISION))

    def test_anchor_geometry_rejects_hidden_duplicate_and_header_occlusion(self):
        state={'target':'products','count':1,'visible':True,'top':90,'bottom':1500,'headerBottom':62,'viewport':900,'hash':'#products'}
        self.assertEqual(CAP.anchor_issues(state),[])
        for delta in [{'count':0},{'count':2},{'visible':False},{'top':0},{'top':901},{'hash':'#budget'},{'bottom':0}]:
            self.assertTrue(CAP.anchor_issues({**state,**delta}))

    def test_native_navigation_focus_escape_and_section_evidence_are_in_controller(self):
        for token in ["('click', 'click', 'Space', 'Space', 'Enter', 'Enter')", "page.keyboard.press('Escape')",
            "page.keyboard.press('Tab')", "page.keyboard.press('Enter')", 'page.go_back(', 'page.go_forward(',
            "for start in ('/', MISSING)", 'for target in ANCHORS', 'anchor_issues(', 'summaryFocused',
            "'Native details observation only; no custom Escape-close promise'", "('#sources', 'sources')"]:
            self.assertIn(token,SOURCE)
        self.assertNotIn('ARTICLE',SOURCE)
        self.assertNotIn('facility_card(',SOURCE)
        self.assertIn("'pixelReview': 'pending'",SOURCE)
        self.assertNotIn("'pixelReview': 'approved'",SOURCE)


class ActualGokseongReadback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        supplied=os.environ.get('GOKSEONG_CAPTURE_INSPECTION_ROOT')
        if not supplied:raise unittest.SkipTest('Explicit retained Gokseong candidate path required; browser not run')
        cls.root=Path(supplied);cls.pages,cls.spec=CAP.capture_inputs(cls.root)
        cls.dist=Path(os.environ.get('GOKSEONG_CAPTURE_INSPECTION_DIST',cls.root/'dist'))

    def test_exact_two_retained_html_files_and_asset_hash_binding(self):
        self.assertEqual({p.relative_to(self.dist).as_posix() for p in self.dist.rglob('*.html')},{'index.html','404.html'})
        self.assertEqual([p['path'] for p in self.pages],list(CAP.ROUTES))
        self.assertEqual(len(CAP.expected_inventory(self.pages)),6)
        self.assertEqual(self.spec['sourceSpecSHA256'],CAP.sha(self.root.parent/'inputs/required-originals.json'))
        self.assertEqual([p['referenceTotalKRW'] for p in self.spec['productCards']],list(CAP.REFERENCE_TOTALS))

    def test_actual_all_blocks_images_faq_products_and_navigation_match_frozen_input(self):
        for expected in self.pages:
            primary=expected['path']=='/';doc=StaticHTML((self.dist/('index.html' if primary else '404.html')).read_text()).root
            blocks=doc.all(attr='data-reviewed-block')
            self.assertEqual([{'tag':e.tag.upper(),'text':e.text()} for e in blocks],expected['reviewedBlocks'])
            self.assertEqual(len(doc.all('img')),7 if primary else 0)
            images=[(x.attrs['src'],x.attrs['alt']) for x in doc.all('img')]
            want=([(x['src'],x['alt']) for x in self.spec['banners']]+[('/images/products/'+p['sku']+'.jpg',p['alt']) for p in self.spec['productCards']]) if primary else []
            self.assertEqual(sorted(images),sorted(want))
            self.assertEqual([x.attrs['data-product-sku'] for x in doc.all(attr='data-product-sku')],expected['productCardIds'])
            self.assertEqual([x.text() for x in doc.all(attr='data-faq-question')],[f['question'] for f in self.spec['faqs']] if primary else [])
            self.assertEqual([x.text() for x in doc.all(attr='data-faq-answer')],[f['answer'] for f in self.spec['faqs']] if primary else [])
            self.assertEqual([x.attrs['id'] for x in doc.all(css_class='copy-section')],expected['sections'])
            self.assertEqual(doc.all(css_class='breadcrumb'),[]);self.assertEqual(doc.all(attr='data-content-card'),[])
            for name in ('desktop-navigation','mobile-menu'):
                nav=doc.all(css_class=name);self.assertEqual(len(nav),1)
                self.assertEqual([{'label':e.text(),'href':e.attrs['href']} for e in nav[0].all('a')],expected['navigation'])
            main=doc.all('main')[0]
            self.assertEqual([{'label':e.text(),'href':e.attrs['href']} for e in main.all('a')],expected['mainLinks'])
            self.assertEqual([{'label':e.text(),'href':e.attrs['href']} for e in main.all('a','data-required-cta')],expected['requiredCtas'])
            for product,source in zip(doc.all(attr='data-product-sku'),self.spec['productCards']):
                reference=product.all(css_class='product-reference');self.assertEqual(len(reference),1)
                self.assertEqual(reference[0].text(),source['referenceText']);self.assertEqual(reference[0].attrs['data-reference-total-krw'],str(source['referenceTotalKRW']))

    def test_actual_source_first_product_social_alt(self):
        home=self.pages[0]
        self.assertEqual([r['content'] for r in home['socialMetadata'] if r['name'] in ('og:image:alt','twitter:image:alt')],[self.spec['productCards'][0]['alt']]*2)
        self.assertEqual(self.pages[1]['socialMetadata'],[])

    def test_actual_metadata_and_document_bytes_match_explicit_fixture_revision(self):
        revision = os.environ.get('GOKSEONG_CAPTURE_INSPECTION_REVISION')
        if not revision:
            self.skipTest('Explicit retained-build revision required; fixture is not a saved source commit')
        for expected in self.pages:
            file = self.dist / ('index.html' if expected['path'] == '/' else '404.html')
            doc = StaticHTML(file.read_text()).root
            meta = doc.all('meta')
            named = lambda name: [e.attrs['content'] for e in meta if e.attrs.get('name') == name]
            properties = lambda name: [e.attrs['content'] for e in meta if e.attrs.get('property') == name]
            metrics = {'title': doc.all('title')[0].text(), 'h1': [e.text() for e in doc.all('h1')],
                'description': named('description'), 'robots': named('robots'),
                'revision': named('site-factory-revision'),
                'canonical': [e.attrs['href'] for e in doc.all('link') if e.attrs.get('rel') == 'canonical'],
                'ogUrl': properties('og:url'),
                'ogProperties': [e.attrs for e in meta if e.attrs.get('property', '').startswith('og:')],
                'socialMetadata': [{'attribute': attr, 'name': e.attrs[attr], 'content': e.attrs['content']}
                    for e in meta for attr in ('property', 'name')
                    if e.attrs.get(attr, '').startswith(('og:', 'twitter:'))]}
            self.assertEqual(CAP.metadata_issues(metrics, expected, revision), [])
            self.assertEqual(CAP.sha(file), expected['documentSHA256'])


class AstroCliPathMutations(unittest.TestCase):
    def test_wrong_version_and_unsafe_bin_fail_without_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_root = root / 'node_modules/astro'
            (package_root / 'bin').mkdir(parents=True)
            (package_root / 'bin/astro.mjs').write_text('// fixture only')
            package = {'name': 'astro', 'version': '7.3.5', 'bin': {'astro': './bin/astro.mjs'}}
            locked = {'version': '7.3.5', 'bin': {'astro': 'bin/astro.mjs'}}
            def save():
                (package_root / 'package.json').write_text(json.dumps(package))
                (root / 'package-lock.json').write_text(json.dumps({'packages': {'node_modules/astro': locked}}))
            save()
            self.assertEqual(CAP.resolve_astro_cli(root)[0], package_root / 'bin/astro.mjs')
            package['version'] = '7.3.6'
            save()
            with self.assertRaisesRegex(RuntimeError, 'version_differs'):
                CAP.resolve_astro_cli(root)
            package['version'] = '7.3.5'
            for bad in ('../outside.mjs', '/tmp/outside.mjs', 'bin/../astro.mjs', 'C:\\outside.mjs'):
                package['bin']['astro'] = locked['bin']['astro'] = bad
                save()
                with self.assertRaisesRegex(RuntimeError, 'bin_path_invalid'):
                    CAP.resolve_astro_cli(root)


class FailurePreservation(unittest.TestCase):
    def test_gate_failure_retains_sealed_failure_without_launch(self):
        fake_gate = types.SimpleNamespace(load=lambda: ({'sourceRevision': REVISION, 'sourceRoot': CAP.SOURCE_ROOT},),
             source=lambda *args: (_ for _ in ()).throw(RuntimeError('fixture gate rejection')))
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, {'production_build': fake_gate}), \
             patch.dict(CAP.os.environ, {'PATH': '/bin'}, clear=True), patch.object(CAP, 'inspect') as inspect, \
             patch('subprocess.Popen') as launch:
            out = Path(tmp) / 'failure-fixture'
            with self.assertRaisesRegex(RuntimeError, 'production_capture_failed'):
                CAP.capture(Path(tmp) / 'checkout', out)
            status = json.loads((out / 'capture-status.json').read_text())
            report = json.loads((out / 'report.json').read_text())
            self.assertEqual(status['status'], 'machine-qa-failed')
            self.assertFalse(status['sourceAndOutputUnchanged'])
            self.assertEqual(report['pages'], [])
            self.assertTrue((out / 'artifact-manifest.json').is_file())
            inspect.assert_not_called()
            launch.assert_not_called()

    def test_browser_failure_still_runs_postbuild_gate_and_seals(self):
        calls = []
        def gate(*args):
            calls.append(args)
            return {'sourceRevision': REVISION}
        fake_gate = types.SimpleNamespace(load=lambda: ({'sourceRevision': REVISION, 'sourceRoot': CAP.SOURCE_ROOT},), source=gate)
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, {'production_build': fake_gate}), \
             patch.dict(CAP.os.environ, {'PATH': '/bin'}, clear=True), \
             patch.object(CAP, 'source_binding', return_value={'fixtureBinding': 'unchanged'}), \
             patch.object(CAP, 'capture_inputs', return_value=([], {})), \
             patch.object(CAP, 'inspect', side_effect=RuntimeError('fixture browser unavailable')), \
             patch('subprocess.Popen') as launch:
            out = Path(tmp) / 'browser-failure-fixture'
            with self.assertRaisesRegex(RuntimeError, 'production_capture_failed'):
                CAP.capture(Path(tmp) / 'checkout', out)
            self.assertEqual(len(calls), 2)
            self.assertEqual([c[1] for c in calls], ['postbuild', 'postbuild'])
            status = json.loads((out / 'capture-status.json').read_text())
            self.assertEqual(status['status'], 'machine-qa-failed')
            self.assertTrue(status['sourceAndOutputUnchanged'])
            self.assertTrue((out / 'source-after-capture.json').is_file())
            self.assertTrue((out / 'input-binding-after.json').is_file())
            launch.assert_not_called()

    def test_changed_source_or_output_cannot_report_success(self):
        fake_gate = types.SimpleNamespace(load=lambda: ({'sourceRevision': REVISION, 'sourceRoot': CAP.SOURCE_ROOT},), source=lambda *args: {})
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, {'production_build': fake_gate}), \
             patch.dict(CAP.os.environ, {'PATH': '/bin'}, clear=True), \
             patch.object(CAP, 'source_binding', side_effect=[{'digest': 'before'}, {'digest': 'after'}]), \
             patch.object(CAP, 'capture_inputs', return_value=([], {})), \
             patch.object(CAP, 'inspect', return_value={'failures': []}), patch('subprocess.Popen') as launch:
            out = Path(tmp) / 'changed-binding-fixture'
            with self.assertRaisesRegex(RuntimeError, 'production_capture_failed'):
                CAP.capture(Path(tmp) / 'checkout', out)
            status = json.loads((out / 'capture-status.json').read_text())
            self.assertEqual(status['status'], 'machine-qa-failed')
            self.assertFalse(status['sourceAndOutputUnchanged'])
            self.assertTrue(any(f['phase'] == 'post-capture-integrity' for f in status['controllerFailures']))
            launch.assert_not_called()

    def test_capture_output_cannot_be_inside_any_source_subtree(self):
        with tempfile.TemporaryDirectory() as tmp:
            checkout = Path(tmp) / 'checkout'
            for relative in ('', 'inputs/evidence', 'release-adapter/evidence', 'candidate/evidence'):
                out = checkout / CAP.SOURCE_ROOT / relative
                with self.assertRaisesRegex(RuntimeError, 'capture_output_must_be_outside_source_root'):
                    CAP.capture(checkout, out)
                self.assertFalse(out.exists())

    def test_existing_capture_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'existing.txt').write_text('kept')
            with self.assertRaisesRegex(RuntimeError, 'fresh_capture_output'):
                CAP.capture(Path(tmp) / 'checkout', tmp)
            self.assertEqual((Path(tmp) / 'existing.txt').read_text(), 'kept')


if __name__ == '__main__':
    unittest.main(verbosity=2)

