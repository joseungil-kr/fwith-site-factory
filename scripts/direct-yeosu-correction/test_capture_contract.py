#!/usr/bin/env python3
"""Pure capture-contract tests. No browser, Node, server, sockets or provider calls.

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
SPEC = importlib.util.spec_from_file_location('yeosu_capture_under_test', HERE / 'production_capture.py')
CAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CAP)
SOURCE = (HERE / 'production_capture.py').read_text()
TREE = ast.parse(SOURCE)
REVISION = 'a' * 40


FROZEN = json.loads((HERE/'ui-expectations.json').read_text())
def fixture_page(route='/'):
    return deepcopy(next(p for p in FROZEN['pages'] if p['path']==route))
def fixture_spec(): return deepcopy(FROZEN['spec'])
def fixture_metrics(route='/'):
    p=fixture_page(route);primary=route in ('/',CAP.ARTICLE);faqs=fixture_spec()['faqs'] if route==CAP.ARTICLE else []
    return {'viewport':390,'scrollWidth':390,'overflow':[],'h1':[p['content']['h1']],'title':p['content']['title'],
      'description':[p['content']['metaDescription']],'revision':[REVISION],
      'firstAnswer':[{'text':p['content']['firstAnswer'],'visible':True}] if p['content']['firstAnswer'] is not None else [],
      'robots':['index,follow' if primary else 'noindex,follow'],'canonical':[] if route=='/404.html' else [CAP.ORIGIN+route],
      'ogUrl':[] if route=='/404.html' else [CAP.ORIGIN+route],'ogProperties':p['socialProperties'],'twitterProperties':p['twitterProperties'],
      'banners':list(CAP.BANNERS) if primary else [],'images':[{**i,'loaded':True,'objectFit':'contain','width':300,'height':150,'naturalWidth':1774,'naturalHeight':887} for i in p['images']],
      'products':[],'skuOrderLinks':[],'bodyText':' '.join(p['requiredBodyPhrases']),
      'noticeLinks':[{'href':p['requiredNoticeHref'],'visible':True}] if p['requiredNoticeHref'] else [],
      'faq':[{**f,'visible':True,'questionVisible':True,'answerVisible':True,'collapsed':False} for f in faqs],
      'faqQuestionCount':len(faqs),'faqAnswerCount':len(faqs),'navigation':p['navigation'],'mobileNavigation':deepcopy(p['navigation']),
      'breadcrumbs':p['breadcrumbs'],'internalLinks':p['internalLinks'],
      'supportCards':[{'title':c['title'],'summary':c['summary'],'links':[{'label':c['ctaLabel'],'href':c['href']}]} for c in p['contentCards']],
      'ctas':[{'href':'/','height':44}], 'bodyCtas':[{**v,'visible':True,'width':200,'height':44} for v in p['ctas']]}


class StaticHarnessContract(unittest.TestCase):
    def test_exact_routes_and_viewports(self):
        self.assertEqual(CAP.ROUTES, ('/', '/regions/', '/regions/yeosu-jeonnam-hospital-funeral-wreath/', '/404.html'))
        self.assertEqual(CAP.WIDTHS, (320, 390, 1280))
        self.assertEqual(len(CAP.expected_inventory([fixture_page(r) for r in CAP.ROUTES])), 12)

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

    def test_required_native_flows(self):
        self.assertIn("('click', 'click', 'Space', 'Space', 'Enter', 'Enter')", SOURCE)
        for label in ('page.go_back(', 'page.go_forward(', "page.keyboard.press('Tab')", "page.keyboard.press('Enter')",
                      "'bodyInboundUrl'", "'breadcrumbParentUrl'", "'supportChildUrl'", "'breadcrumbHomeUrl'"):
            self.assertIn(label, SOURCE)
        self.assertIn("image.evaluate('(image)=>image.decode()')", SOURCE)
        self.assertIn("'pixelReview': 'pending'", SOURCE)
        self.assertNotIn("'pixelReview': 'approved'", SOURCE)

    def test_unknown_path_recovery_uses_verified_yeosu_cta(self):
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
            self.assertEqual(again.SOURCE_ROOT, 'site-factory/yeosu-flower')


class PureHelpers(unittest.TestCase):
    def test_exact_origin_rejects_lookalikes_and_external_schemes(self):
        origin = 'http://127.0.0.1:43817'
        for url in (origin + '/', origin + '/images/image.jpg?a=b'):
            self.assertTrue(CAP.same_origin(url, origin))
        for url in ('http://127.0.0.1:43818/', 'https://127.0.0.1:43817/', 'http://localhost:43817/',
                    'http://127.0.0.1.evil:43817/', 'http://user@127.0.0.1:43817/',
                    'https://yeosu.fwith.kr/', 'file:///tmp/x', 'data:text/plain,hello', 'ws://127.0.0.1:43817/'):
            self.assertFalse(CAP.same_origin(url, origin), url)

    def test_source_process_env_is_allowlisted(self):
        supplied = {'PATH': '/safe/bin', 'HOME': '/safe/home', 'LANG': 'C.UTF-8', 'SITE_URL': CAP.ORIGIN,
             'SITE_RELEASE_MODE': 'production', 'CLOUDFLARE_API_TOKEN': 'test-value', 'GITHUB_TOKEN': 'test-value',
             'NODE_OPTIONS': '--require=unexpected', 'LD_PRELOAD': 'unexpected', 'HTTPS_PROXY': 'unexpected'}
        clean = CAP.clean_environment(supplied)
        self.assertEqual(set(clean), {'PATH', 'HOME', 'LANG', 'CI', 'ASTRO_TELEMETRY_DISABLED', 'NO_COLOR'})
        self.assertEqual(clean['PATH'], '/safe/bin')
        self.assertEqual(clean['ASTRO_TELEMETRY_DISABLED'], '1')

    def test_provider_credentials_fail_closed(self):
        CAP.reject_provider_credentials({'PATH': '/bin', 'CLOUDFLARE_API_TOKEN': ''})
        for key in ('CLOUDFLARE_API_TOKEN', 'CF_API_TOKEN', 'AWS_ACCESS_KEY_ID', 'VERCEL_TOKEN', 'NETLIFY_AUTH_TOKEN'):
            with self.assertRaisesRegex(RuntimeError, 'provider_credentials_forbidden'):
                CAP.reject_provider_credentials({key: 'test-value'})

    def test_workflow_capture_controller_environment_is_empty_then_allowlisted(self):
        workflow = (HERE.parents[1] / '.github/workflows/yeosu-policy-correction-qa.yml').read_text()
        section = workflow.split('      - name: Inspect production artifact on runner loopback only\n', 1)[1].split('      - name:', 1)[0]
        command = section.split('          env -i ', 1)[1].split('            python3 control/scripts/direct-yeosu-correction/production_capture.py', 1)[0]
        # Execute the exact shell environment prefix, replacing only the capture
        # program with a no-launch reader. Values are synthetic and never secrets.
        command = 'env -i ' + command + 'python3 -c ' + shlex.quote('import os,json;print(json.dumps(dict(os.environ)))')
        supplied = {'PATH': os.environ['PATH'], 'HOME': '/tmp/yeosu-capture-test-home',
            'SITE_RELEASE_MODE': 'production', 'SITE_INDEXABLE': 'true', 'SITE_URL': CAP.ORIGIN,
            'SITE_FACTORY_REVISION': REVISION, 'SITE_RELEASE_BINDING_PATH': '/tmp/yeosu-binding.json',
            'SITE_RELEASE_BINDING_SHA256': 'b' * 64,
            'CLOUDFLARE_API_TOKEN': 'synthetic', 'AZURE_HTTP_USER_AGENT': 'synthetic',
            'AWS_ACCESS_KEY_ID': 'synthetic', 'GITHUB_TOKEN': 'synthetic',
            'NODE_OPTIONS': '--require=synthetic', 'LD_PRELOAD': '', 'HTTPS_PROXY': 'synthetic'}
        result = subprocess.run(['bash', '-c', command], env=supplied, capture_output=True, text=True, check=True)
        actual = json.loads(result.stdout)
        essentials = {'PATH', 'HOME', 'LANG', 'PYTHONDONTWRITEBYTECODE', 'ASTRO_TELEMETRY_DISABLED'}
        bindings = {k for k in supplied if k.startswith('SITE_')}
        # Python may add LC_CTYPE during locale coercion on minimal systems.
        self.assertLessEqual(set(actual), essentials | bindings | {'LC_CTYPE'})
        self.assertTrue(essentials | bindings <= set(actual))
        self.assertEqual({k: actual[k] for k in bindings}, {k: supplied[k] for k in bindings})
        CAP.reject_provider_credentials(actual)
        self.assertIn('reject_provider_credentials(os.environ)', SOURCE)

    def test_frozen_page_metadata_denominators(self):
        for route in CAP.ROUTES:
            with self.subTest(route=route):
                self.assertEqual(CAP.metadata_issues(fixture_metrics(route), fixture_page(route), REVISION), [])
                metrics = fixture_metrics(route)
                metrics['revision'] = ['b' * 40]
                self.assertIn('Exact metadata mismatch: revision', CAP.metadata_issues(metrics, fixture_page(route), REVISION))

    def test_support_noindex_and_self_canonical_are_required(self):
        metrics = fixture_metrics('/regions/')
        metrics['robots'] = ['index,follow']
        metrics['canonical'] = [CAP.ORIGIN + '/']
        errors = CAP.metadata_issues(metrics, fixture_page('/regions/'), REVISION)
        self.assertIn('Exact metadata mismatch: robots', errors)
        self.assertIn('Exact metadata mismatch: canonical', errors)

    def test_404_must_have_no_canonical_or_og(self):
        metrics = fixture_metrics('/404.html')
        metrics.update(canonical=[CAP.ORIGIN + '/404.html'], ogUrl=[CAP.ORIGIN + '/404.html'], ogProperties=[{'name': 'og:title'}])
        self.assertGreaterEqual(len(CAP.metadata_issues(metrics, fixture_page('/404.html'), REVISION)), 3)

    def test_positive_metric_fixtures_are_only_pure_fixtures(self):
        for route in CAP.ROUTES:
            self.assertEqual(CAP.inspect_metrics(fixture_metrics(route), fixture_page(route), fixture_spec(), 390, REVISION), [])

    def test_mutated_banner_product_faq_image_and_overflow_fail(self):
        mutations = (
            lambda m: m['banners'].pop(),
            lambda m: m['products'].append({'sku':'B201','links':[]}),
            lambda m: m['skuOrderLinks'].append({'href':'https://fwith.co.kr/shop/item.php?it_id=B201'}),
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
            metrics = fixture_metrics(CAP.ARTICLE)
            mutate(metrics)
            self.assertTrue(CAP.inspect_metrics(metrics, fixture_page(CAP.ARTICLE), fixture_spec(), 390, REVISION), index)

    def test_first_answer_must_match_and_be_individually_visible(self):
        self.assertIn("firstAnswer:all('[data-first-answer]')", CAP.METRICS_JS)
        for kind in ('hidden', 'missing-visibility', 'changed', 'missing-node', 'duplicate'):
            metrics = fixture_metrics(CAP.ARTICLE)
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
            errors = CAP.inspect_metrics(metrics, fixture_page(CAP.ARTICLE), fixture_spec(), 390, REVISION)
            self.assertIn('Exact first answer missing, changed, or invisible', errors)

    def test_zero_sku_links_and_restriction_metadata_mutations(self):
        mutations=(lambda m:m.update(skuOrderLinks=[{'href':'https://fwith.co.kr/shop/item.php?it_id=B060'}]),
            lambda m:m.update(bodyText=''),lambda m:m.update(noticeLinks=[]),
            lambda m:m['ogProperties'][0].update(content='wrong'),lambda m:m['twitterProperties'][0].update(content='wrong'),
            lambda m:m['images'][0].update(alt='wrong'),lambda m:m['images'][0].update(src='/images/products/B201.jpg'),
            lambda m:m.update(faqQuestionCount=3))
        for change in mutations:
            m=fixture_metrics(CAP.ARTICLE);change(m)
            self.assertTrue(CAP.inspect_metrics(m,fixture_page(CAP.ARTICLE),fixture_spec(),390,REVISION))

    def test_required_body_cta_cannot_disappear_behind_visible_other_cta(self):
        self.assertIn("bodyCtas:all('main a[href]')", CAP.METRICS_JS)
        for kind in ('hidden', 'missing-visibility', 'zero-width', 'zero-height', 'absent', 'wrong-label', 'wrong-href'):
            metrics = fixture_metrics(CAP.ARTICLE)
            if kind == 'hidden':
                metrics['bodyCtas'][0]['visible'] = False
            elif kind == 'missing-visibility':
                del metrics['bodyCtas'][0]['visible']
            elif kind == 'zero-width':
                metrics['bodyCtas'][0]['width'] = 0
            elif kind == 'zero-height':
                metrics['bodyCtas'][0]['height'] = 0
            elif kind == 'absent':
                metrics['bodyCtas'] = []
            elif kind == 'wrong-label':
                metrics['bodyCtas'][0]['label'] = 'Other label'
            else:
                metrics['bodyCtas'][0]['href'] = '/wrong/'
            metrics['bodyCtas'].append({'label': 'Unrelated action', 'href': '/', 'visible': True, 'width': 200, 'height': 44})
            errors = CAP.inspect_metrics(metrics, fixture_page(CAP.ARTICLE), fixture_spec(), 390, REVISION)
            self.assertTrue(any('Required body CTA missing or invisible' in e for e in errors))

    def test_hidden_or_missing_question_cannot_pass_visible_faq_wrapper(self):
        self.assertIn('questionVisible:visible(question)', CAP.METRICS_JS)
        self.assertIn('getBoundingClientRect().width>0', CAP.METRICS_JS)
        for value in (False, None, 0, '', 'true', 'remove-field'):
            metrics = fixture_metrics(CAP.ARTICLE)
            self.assertTrue(metrics['faq'][0]['visible'])
            if value == 'remove-field':
                del metrics['faq'][0]['questionVisible']
            else:
                metrics['faq'][0]['questionVisible'] = value
            errors = CAP.inspect_metrics(metrics, fixture_page(CAP.ARTICLE), fixture_spec(), 390, REVISION)
            self.assertIn('FAQ question or answer hidden, missing, or has zero geometry', errors)

    def test_hidden_or_missing_answer_cannot_pass_visible_faq_wrapper(self):
        self.assertIn('answerVisible:visible(answer)', CAP.METRICS_JS)
        self.assertIn('checkVisibility({checkOpacity:true,checkVisibilityCSS:true})', CAP.METRICS_JS)
        self.assertIn('getBoundingClientRect().height>0', CAP.METRICS_JS)
        for value in (False, None, 0, '', 'true', 'remove-field'):
            metrics = fixture_metrics(CAP.ARTICLE)
            self.assertTrue(metrics['faq'][0]['visible'])
            if value == 'remove-field':
                del metrics['faq'][0]['answerVisible']
            else:
                metrics['faq'][0]['answerVisible'] = value
            errors = CAP.inspect_metrics(metrics, fixture_page(CAP.ARTICLE), fixture_spec(), 390, REVISION)
            self.assertIn('FAQ question or answer hidden, missing, or has zero geometry', errors)

    def test_support_and_breadcrumb_mutations_fail(self):
        page = fixture_page('/regions/')
        page.update(breadcrumbVisible=True, breadcrumbs=[{'label': 'Home', 'href': '/', 'current': False}],
                    internalLinks=[{'label': 'Child', 'href': CAP.ARTICLE}],
                    contentCards=[{'title': 'Child', 'summary': 'Summary', 'ctaLabel': 'Visit', 'href': CAP.ARTICLE}])
        errors = CAP.inspect_metrics(fixture_metrics('/regions/'), page, fixture_spec(), 390, REVISION)
        self.assertIn('Exact breadcrumb chain mismatch', errors)
        self.assertTrue(any('inbound link missing' in e for e in errors))
        self.assertIn('Support page must have exactly its one real child', errors)

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


class InstalledPackageAndRetainedHTML(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        supplied = os.environ.get('YEOSU_CAPTURE_INSPECTION_ROOT')
        cls.root = Path(supplied) if supplied else HERE.parents[2] / 'source/candidate'
        # CI runs pure controls before npm ci/build. Actual fixture readback is
        # explicit locally or in a second post-build control invocation.
        if not (cls.root / 'node_modules/astro/package.json').is_file() or not (cls.root / 'dist/index.html').is_file():
            if supplied:
                raise RuntimeError('explicit_capture_inspection_source_unavailable')
            raise unittest.SkipTest('Installed Astro/built local HTML absent; actual readback not performed in this invocation')
        cls.pages, cls.spec = CAP.capture_inputs(cls.root)

    def test_actual_frozen_output_rejects_undeclared_head_changes(self):
        import production_build as build_gate
        revision=next(e.attrs['content'] for e in StaticHTML((self.root/'dist/index.html').read_text()).root.all('meta','name','site-factory-revision'))
        self.assertEqual(build_gate.inspect_dist(self.root/'dist',revision)['outputFiles'],18)
        for injection in ('<meta http-equiv="refresh" content="0;url=https://wrong.invalid">','<script>void(0)</script>','<meta name="description" content="extra">'):
            with tempfile.TemporaryDirectory() as temp:
                copied=Path(temp)/'dist';shutil.copytree(self.root/'dist',copied);target=copied/'index.html';target.write_text(target.read_text().replace('</head>',injection+'</head>',1))
                with self.assertRaisesRegex(ValueError,'frozen_corrected_output_mismatch'):build_gate.inspect_dist(copied,revision)

    def test_actual_installed_astro_cli_matches_lock_and_exists(self):
        cli, evidence = CAP.resolve_astro_cli(self.root)
        package = json.loads((self.root / 'node_modules/astro/package.json').read_text())
        locked = json.loads((self.root / 'package-lock.json').read_text())['packages']['node_modules/astro']
        self.assertEqual(evidence['version'], package['version'])
        self.assertEqual(evidence['version'], locked['version'])
        self.assertEqual(evidence['declaredBin'], package['bin']['astro'])
        self.assertEqual(evidence['lockedBin'], locked['bin']['astro'])
        self.assertTrue(cli.is_file())
        self.assertEqual(evidence['cliSha256'], CAP.sha(cli))
        # Concrete installed 7.3.5 regression: historical astro.js did not exist.
        if package['version'] == '7.3.5':
            self.assertEqual(cli.name, 'astro.mjs')
            self.assertEqual(cli.parent.name, 'bin')

    def test_actual_source_and_dist_selectors_match_frozen_contract(self):
        for expected in self.pages:
            route = expected['path']
            name = 'index.html' if route == '/' else route.lstrip('/') + ('index.html' if route.endswith('/') else '')
            doc = StaticHTML((self.root / 'dist' / name).read_text()).root
            with self.subTest(route=route):
                self.assertEqual([e.text() for e in doc.all('h1')], [expected['content']['h1']])
                self.assertEqual([e.text() for e in doc.all('title')], [expected['content']['title']])
                self.assertEqual([e.attrs['content'] for e in doc.all('meta', 'name', 'description')], [expected['content']['metaDescription']])
                self.assertEqual([e.attrs['data-shared-flower-banner'] for e in doc.all(attr='data-shared-flower-banner')], list(CAP.BANNERS) if route in ('/', CAP.ARTICLE) else [])
                self.assertEqual(len(doc.all('img')), 3 if route in ('/',CAP.ARTICLE) else 0)
                products = doc.all(attr='data-product-sku')
                self.assertEqual([e.attrs['data-product-sku'] for e in products], expected['productCardIds'])
                for product in products:
                    source = next(p for p in self.spec['productCards'] if p['sku'] == product.attrs['data-product-sku'])
                    image = product.all('img')
                    self.assertEqual(len(image), 1)
                    self.assertEqual(image[0].attrs['src'], '/images/products/' + source['sku'] + '.jpg')
                    self.assertEqual(image[0].attrs['alt'], source['alt'])
                    cta = product.all('a', 'data-order-product-sku')
                    self.assertEqual(len(cta), 1)
                    self.assertEqual((cta[0].text(), cta[0].attrs['href'], cta[0].attrs.get('aria-label')),
                         (source['cta']['label'], source['cta']['href'], source['cta']['accessibleLabel']))
                questions = doc.all(attr='data-faq-question');answers = doc.all(attr='data-faq-answer')
                self.assertEqual(len(questions), len(expected['faqIds']));self.assertEqual(len(answers),len(expected['faqIds']))
                for question,answer,source in zip(questions,answers,self.spec['faqs']):
                    self.assertEqual(question.text(),source['question']);self.assertEqual(answer.text(),source['answer'])
                crumb_containers = doc.all(css_class='breadcrumb')
                self.assertEqual(len(crumb_containers), 1 if expected['breadcrumbVisible'] else 0)
                if crumb_containers:
                    actual = []
                    for element in crumb_containers[0].children:
                        if isinstance(element, StaticElement) and (element.tag == 'a' or element.attrs.get('aria-current') == 'page'):
                            actual.append({'label': element.text(), 'href': element.attrs.get('href'), 'current': element.attrs.get('aria-current') == 'page'})
                    self.assertEqual(actual, [{k: b[k] for k in ('label', 'href', 'current')} for b in expected['breadcrumbs']])
                main = doc.all('main')
                self.assertEqual(len(main), 1)
                links = [{'label': e.text(), 'href': e.attrs['href']} for e in main[0].all('a', 'href') if e.attrs['href'].startswith('/')]
                for link in expected['internalLinks']:
                    self.assertIn({k: link[k] for k in ('label', 'href')}, links)
                cards = doc.all(attr='data-content-card')
                self.assertEqual(len(cards), 1 if route == '/regions/' else 0)
                if cards:
                    source = expected['contentCards'][0]
                    self.assertEqual([e.text() for e in cards[0].all('h2')], [source['title']])
                    self.assertEqual([e.text() for e in cards[0].all('p')], [source['summary']])
                    self.assertEqual([{'label': e.text(), 'href': e.attrs['href']} for e in cards[0].all('a')],
                         [{'label': source['ctaLabel'], 'href': source['href']}])
                nav = expected['navigation']
                for css_class in ('desktop-navigation', 'mobile-menu'):
                    containers = doc.all(css_class=css_class)
                    self.assertEqual(len(containers), 1)
                    self.assertEqual([{'label': e.text(), 'href': e.attrs['href']} for e in containers[0].all('a')], nav)
                self.assertEqual([e.attrs.get('href') for e in doc.all('a', css_class='skip-link')], ['#main-content'])
                self.assertEqual(main[0].attrs.get('id'), 'main-content')
                self.assertEqual([e.text() for e in doc.all(attr='data-first-answer')], [expected['content']['firstAnswer']] if expected['content']['firstAnswer'] is not None else [])
                body_links = [{'label': e.text(), 'href': e.attrs['href']} for e in main[0].all('a', 'href')]
                for cta in expected['ctas']:
                    self.assertIn({key: cta[key] for key in ('label', 'href')}, body_links)


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

    def test_existing_capture_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'existing.txt').write_text('kept')
            with self.assertRaisesRegex(RuntimeError, 'fresh_capture_output'):
                CAP.capture(Path(tmp) / 'checkout', tmp)
            self.assertEqual((Path(tmp) / 'existing.txt').read_text(), 'kept')


if __name__ == '__main__':
    unittest.main(verbosity=2)
