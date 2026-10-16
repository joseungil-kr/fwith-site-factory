"""Pure and explicit retained-source/HTML tests. Never launches a browser or server."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch
import production_capture as cap
from test_capture_contract import fixture_metrics, fixture_page, fixture_spec, REVISION


def fixture_mapping():
    return {
        'contexts': [{'pointer': '/fixture/text', 'occurrences': [{
            'selector': '#fixture', 'extraction': 'textContent', 'requiredTag': 'P',
            'expectedExtractedText': 'Fixture only', 'expectedDOMMatchesPerPage': 1,
            'pageIds': ['home', 'notFound'],
            'layoutAvailableByState': {s['id']: True for s in cap.OCCURRENCE_STATES}}]}],
        'supplementalTechnicalIdentifiers': [{
            'pointer': '/fixture/sku', 'selector': '#fixture-sku', 'requiredTag': 'H3',
            'expectedExtractedText': 'Fixture B201', 'pageIds': ['home']}]}


def fixture_observations(mapping, page_id, state):
    def node(tag, text, available=True):
        return {'tag': tag, 'text': text, 'available': available,
                'rect': {'x': 10, 'y': 100, 'width': 100 if available else 0, 'height': 30 if available else 0}}
    return {'pageId': page_id, 'stateId': state['id'], 'width': state['width'],
        'scrollWidth': state['width'], 'clientWidth': state['width'],
        'menuOpen': state['menuOpen'], 'skipFocused': state['skipFocused'],
        'observations': [{'pointer': r['pointer'], 'selector': o['selector'], 'extraction': o['extraction'],
            'nodes': [node(o['requiredTag'], o['expectedExtractedText'], o['layoutAvailableByState'][state['id']])]}
            for r in mapping['contexts'] for o in r['occurrences'] if page_id in o['pageIds']],
        'supplemental': [{'pointer': r['pointer'], 'selector': r['selector'],
            'nodes': [node(r['requiredTag'], r['expectedExtractedText'])]}
            for r in mapping['supplementalTechnicalIdentifiers'] if page_id in r['pageIds']]}


class OccurrenceReadbackContracts(unittest.TestCase):
    def test_all_eight_states_on_both_pages_accept_exact_fixture_measurements(self):
        mapping = fixture_mapping()
        for page_id in ('home', 'notFound'):
            for state in cap.OCCURRENCE_STATES:
                metrics = fixture_observations(mapping, page_id, state)
                self.assertEqual(cap.occurrence_issues(metrics, mapping, page_id, state), [])

    def test_missing_duplicate_reordered_and_changed_occurrence_nodes_fail(self):
        mapping = fixture_mapping(); state = cap.OCCURRENCE_STATES[0]
        mutations = [lambda m: m['observations'].clear(),
            lambda m: m['observations'].append(deepcopy(m['observations'][0])),
            lambda m: m['observations'][0].update(pointer='/other'),
            lambda m: m['observations'][0].update(selector='#other'),
            lambda m: m['observations'][0].update(extraction='attribute:alt'),
            lambda m: m['observations'][0].update(nodes=None),
            lambda m: m['observations'][0]['nodes'].clear(),
            lambda m: m['observations'][0]['nodes'].append(deepcopy(m['observations'][0]['nodes'][0]))]
        for field, value in [('tag', 'H2'), ('text', 'Changed'), ('available', False), ('available', 1), ('rect', {})]:
            mutations.append(lambda m, f=field, v=value: m['observations'][0]['nodes'][0].update({f: v}))
        for field, value in [('width', 0), ('height', 0), ('x', 320), ('x', -200), ('width', float('nan'))]:
            mutations.append(lambda m, f=field, v=value: m['observations'][0]['nodes'][0]['rect'].update({f: v}))
        for mutate in mutations:
            metrics = fixture_observations(mapping, 'home', state); mutate(metrics)
            self.assertTrue(cap.occurrence_issues(metrics, mapping, 'home', state))

    def test_viewport_focus_menu_and_supplemental_mutations_fail(self):
        mapping = fixture_mapping(); state = cap.OCCURRENCE_STATES[0]
        mutations = [lambda m: m.update(pageId='wrong'), lambda m: m.update(stateId='wrong'),
            lambda m: m.update(width=390), lambda m: m.update(width=320.0),
            lambda m: m.update(scrollWidth=321), lambda m: m.update(scrollWidth=float('nan')),
            lambda m: m.update(clientWidth=319), lambda m: m.update(menuOpen=True),
            lambda m: m.update(menuOpen=0), lambda m: m.update(skipFocused=True),
            lambda m: m['supplemental'].clear(), lambda m: m['supplemental'].append(deepcopy(m['supplemental'][0])),
            lambda m: m['supplemental'][0]['nodes'][0].update(text='Wrong B201'),
            lambda m: m['supplemental'][0]['nodes'][0].update(available=False)]
        for mutate in mutations:
            metrics = fixture_observations(mapping, 'home', state); mutate(metrics)
            self.assertTrue(cap.occurrence_issues(metrics, mapping, 'home', state))

    def test_evaluator_measures_ancestors_details_inert_aria_and_real_rects(self):
        for token in ["getComputedStyle(e)", "e.hidden", "e.inert", "e.getAttribute('aria-hidden')", "e.tagName==='DETAILS'", "getBoundingClientRect()", "n.closest('head')", 'document.activeElement', 'document.querySelectorAll(selector)']:
            self.assertIn(token, cap.OCCURRENCES_JS)

    def test_both_evaluation_scripts_parse_without_executing_dom_or_browser(self):
        script = "const fs=require('node:fs'),vm=require('node:vm');for(const s of JSON.parse(fs.readFileSync(0,'utf8')))new vm.Script('('+s+')');console.log('PARSED_ONLY_NO_DOM_EXECUTION');"
        result = subprocess.run(['node', '-e', script], input=json.dumps([cap.METRICS_JS, cap.OCCURRENCES_JS]),
            text=True, capture_output=True, env=cap.clean_environment(os.environ), check=True)
        self.assertEqual(result.stdout.strip(), 'PARSED_ONLY_NO_DOM_EXECUTION')

    def test_strengthened_touch_targets_and_product_aspect_ratio_fail(self):
        for mutate in [lambda m: m['products'][0]['links'][0].update(width=43),
            lambda m: m['requiredCtas'][0].update(width=43),
            lambda m: m['chromeVisibleLinks']['footer'][0].update(height=43),
            lambda m: m['chromeVisibleLinks']['mobileBar'][0].update(width=43),
            lambda m: m['images'][-1].update(height=180)]:
            metrics = fixture_metrics(); mutate(metrics)
            self.assertTrue(cap.inspect_metrics(metrics, fixture_page(), fixture_spec(), 390, REVISION))


class OccurrenceCompletionCoverage(unittest.TestCase):
    def fixture(self):
        return {'occurrenceStates': [{'pageId': p, 'stateId': s['id'], 'width': s['width']}
            for p in ('home', 'notFound') for s in cap.OCCURRENCE_STATES]}

    def test_exact_sixteen_states_required_in_any_order(self):
        report = self.fixture(); before = deepcopy(report)
        result = cap.validate_occurrence_coverage(report)
        self.assertEqual(result['expected'], 16); self.assertEqual(result['attempted'], 16)
        self.assertTrue(result['complete']); self.assertEqual(report, before)
        report['occurrenceStates'].reverse(); self.assertTrue(cap.validate_occurrence_coverage(report)['complete'])

    def test_missing_extra_duplicate_wrong_or_malformed_states_reject(self):
        mutations = [lambda r: r.clear(), lambda r: r.update(occurrenceStates=None),
            lambda r: r['occurrenceStates'].pop(),
            lambda r: r['occurrenceStates'].append(deepcopy(r['occurrenceStates'][0])),
            lambda r: r['occurrenceStates'].__setitem__(-1, deepcopy(r['occurrenceStates'][0])),
            lambda r: r['occurrenceStates'].__setitem__(0, None)]
        for field, value in [('pageId', 'other'), ('stateId', 'unknown'), ('width', 320.0), ('width', True), ('width', 390)]:
            mutations.append(lambda r, f=field, v=value: r['occurrenceStates'][0].update({f: v}))
        for mutate in mutations:
            report = self.fixture(); mutate(report)
            result = cap.validate_occurrence_coverage(report)
            self.assertFalse(result['complete']); self.assertTrue(result['issues'])

    def test_inspect_collects_states_and_failures_before_success(self):
        import inspect
        source = inspect.getsource(cap.inspect)
        for token in ["report['occurrenceStates'].extend(capture_occurrence_states", "report['occurrenceCoverage'] = validate_occurrence_coverage(report)", "report['failures'].extend(report['occurrenceCoverage']['issues'])", "('pages', 'flows', 'unknownPath', 'occurrenceStates')", 'scroll_reachability(page)']:
            self.assertIn(token, source)


class OccurrenceOrchestration(unittest.TestCase):
    def run_fixture(self, *, bad_bytes=False):
        import hashlib
        mapping = fixture_mapping(); body = b'fixture only, never a browser response'
        page = MagicMock(); page.goto.return_value.status = 200; page.goto.return_value.body.return_value = body
        page.locator.return_value.count.return_value = 1
        page.evaluate.side_effect = lambda script, args: fixture_observations(mapping, args['pageId'], args['state'])
        expected = {'path': '/', 'id': 'home', 'documentSHA256': '0'*64 if bad_bytes else hashlib.sha256(body).hexdigest()}
        with tempfile.TemporaryDirectory() as tmp, patch.object(cap, 'settle') as settle, patch.object(cap, 'retain_page') as retain:
            rows = cap.capture_occurrence_states(page, 'http://127.0.0.1:43817', expected, {'occurrenceMap': mapping}, 320, tmp)
            self.assertEqual(len(rows), 3); self.assertEqual(retain.call_count, 3)
            self.assertEqual(len(list(Path(tmp).glob('*.json'))), 3)
            if bad_bytes:
                self.assertEqual(settle.call_count, 0); page.evaluate.assert_not_called()
                self.assertTrue(all('bytes_differ' in r['issues'][0] for r in rows))
            else:
                self.assertEqual(settle.call_count, 3); self.assertTrue(all(not r['issues'] for r in rows))
                page.keyboard.press.assert_called_once_with('Tab')
                page.locator.return_value.click.assert_called_once()
            return rows

    def test_all_state_evidence_attempted_without_real_browser(self): self.run_fixture()
    def test_changed_http_bytes_fail_each_state_but_retain_evidence(self): self.run_fixture(bad_bytes=True)


class ActualFrozenGokseongOccurrenceInputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        supplied = os.environ.get('GOKSEONG_CAPTURE_SOURCE_ROOT')
        if not supplied: raise unittest.SkipTest('Explicit frozen source root required; no browser run')
        cls.root = Path(supplied).resolve(); inputs = cls.root / 'inputs/reviewed-copy'
        cls.copy = json.loads((inputs / 'customer-copy.json').read_text())
        cls.mapping = json.loads((inputs / 'output-context-map.json').read_text())
        cls.visible = json.loads((inputs / 'visible-strings.json').read_text())

    def test_exact_original_input_hashes_and_native_contract(self):
        for name, expected in cap.FROZEN_INPUT_SHA256.items():
            self.assertEqual(cap.sha(self.root / 'inputs/reviewed-copy' / name), expected)
        self.assertTrue(cap.validate_occurrence_contract(self.copy, self.mapping, self.visible))

    def test_original_seven_asset_manifest_is_mapped_by_sku_and_rejects_mutations(self):
        manifest = json.loads((self.root / 'inputs/reviewed-copy/asset-manifest.json').read_text())
        self.assertEqual([r['sku'] for r in cap.reviewed_product_assets(manifest)], list(cap.PRODUCTS))
        self.assertEqual(manifest['assets'][0]['sku'], 'B060')
        for mutation in ('missing', 'duplicate', 'wrong-sku', 'wrong-count', 'wrong-schema'):
            changed = deepcopy(manifest)
            if mutation == 'missing': changed['assets'].pop()
            elif mutation == 'duplicate': changed['assets'][1] = deepcopy(changed['assets'][0])
            elif mutation == 'wrong-sku': changed['assets'][0]['sku'] = 'B999'
            elif mutation == 'wrong-count': changed['count'] = 6
            else: changed['schema'] = 'other'
            with self.assertRaises(RuntimeError): cap.reviewed_product_assets(changed)

    def test_all_102_original_strings_143_expanded_occurrences_and_four_skus(self):
        for page_id, count in [('home', 114), ('notFound', 29)]:
            for state in cap.OCCURRENCE_STATES:
                metrics = fixture_observations(self.mapping, page_id, state)
                self.assertEqual(len(metrics['observations']), count)
                self.assertEqual(cap.occurrence_issues(metrics, self.mapping, page_id, state), [])
        # Fixture values exercise the comparison; they are not observed browser geometry.

    def test_original_contract_mutations_fail(self):
        mutations = [lambda m: m['contexts'].pop(), lambda m: m['states'].pop(),
            lambda m: m['contexts'][0].update(text='changed'),
            lambda m: m['contexts'][0]['occurrences'][0].update(expectedDOMMatchesPerPage=True),
            lambda m: m['contexts'][0]['occurrences'][0]['layoutAvailableByState'].update({'320-closed': 0}),
            lambda m: m['contexts'][0]['occurrences'][0].update(pageIds=['home', 'home']),
            lambda m: m['supplementalTechnicalIdentifiers'][0].update(countedIn102=True)]
        for mutate in mutations:
            mapping = deepcopy(self.mapping); mutate(mapping)
            # Keep mirror rows synchronized so validation reaches each malformed field.
            visible = {**self.visible, 'rows': mapping['contexts']}
            with self.assertRaises((RuntimeError, KeyError, TypeError)):
                cap.validate_occurrence_contract(self.copy, mapping, visible)

    def test_retained_production_html_exact_occurrences_if_supplied(self):
        supplied = os.environ.get('GOKSEONG_CAPTURE_INSPECTION_DIST')
        if not supplied: self.skipTest('Production-like retained HTML not supplied')
        # Read/compile only: importing by file loader would write __pycache__ into
        # the immutable shared source directory. Never mutate that source.
        parser = self.root / 'candidate/scripts/html_surface.py'
        module = types.ModuleType('frozen_gokseong_html_surface')
        exec(compile(parser.read_text(), str(parser), 'exec'), module.__dict__)
        doms = {p: module.BeautifulSoup((Path(supplied) / f).read_text()) for p, f in [('home', 'index.html'), ('notFound', '404.html')]}
        checked = 0
        for row in self.mapping['contexts']:
            for occurrence in row['occurrences']:
                for page_id in occurrence['pageIds']:
                    nodes = doms[page_id].select(occurrence['selector'])
                    self.assertEqual(len(nodes), occurrence['expectedDOMMatchesPerPage'], (page_id, row['pointer'], occurrence['selector']))
                    for node in nodes:
                        self.assertEqual(node.name.upper(), occurrence['requiredTag'])
                        text = node.get_text() if occurrence['extraction'] == 'textContent' else node.get(occurrence['extraction'].split(':', 1)[1])
                        self.assertEqual(text, occurrence['expectedExtractedText'])
                    checked += 1
        self.assertEqual(checked, 143)
        for row in self.mapping['supplementalTechnicalIdentifiers']:
            nodes = doms['home'].select(row['selector'])
            self.assertEqual(len(nodes), 1); self.assertEqual(nodes[0].get_text(), row['expectedExtractedText'])


if __name__ == '__main__': unittest.main(verbosity=2)
