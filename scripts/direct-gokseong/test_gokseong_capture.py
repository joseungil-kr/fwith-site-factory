"""Pure fake-page orchestration regressions; never evidence of browser behavior."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import production_capture as cap
from test_capture_contract import fixture_spec, fixture_page


class FakeLocator:
    def __init__(self, page, selector): self.page, self.selector = page, selector
    def locator(self, selector): return FakeLocator(self.page, selector)
    def count(self): return 1
    def is_visible(self): return self.page.width <= 860
    def get_attribute(self, name):
        if name == 'open': return '' if self.page.open else None
        if name == 'href' and self.selector == ':focus': return '#main-content' if self.page.focus == 'skip' else None
        raise AssertionError((self.selector, name))
    def focus(self): self.page.focus = 'summary'
    def inner_text(self): return self.page.spec['menuClose' if self.page.open else 'menuOpen']
    def evaluate(self, script):
        assert script == '(e)=>document.activeElement===e'
        return self.page.focus == 'summary'
    def evaluate_all(self, script): return len(cap.ANCHORS) if self.page.open else 0
    def click(self):
        if self.selector == 'summary':
            self.page.open = not self.page.open
            self.page.focus = 'summary'
        elif self.selector == '.brand': self.page.goto(self.page.origin + '/')
        elif 'a[href="/#' in self.selector:
            target = self.selector.split('a[href="/#', 1)[1].split('"', 1)[0]
            self.page.navigate(self.page.origin + '/#' + ('wrong' if self.page.break_anchor else target))
            self.page.focus = 'link'
        else: raise AssertionError(self.selector)


class FakeKeyboard:
    def __init__(self, page): self.page = page
    def press(self, key):
        if key == 'Tab': self.page.focus = 'skip'
        elif key == 'Enter' and self.page.focus == 'skip':
            self.page.navigate(self.page.origin + '/#main-content'); self.page.focus = 'main-content'
        elif key in ('Enter', 'Space') and self.page.focus == 'summary': self.page.open = not self.page.open
        elif key == 'Escape':
            self.page.escape_calls += 1
            if self.page.escape_closes: self.page.open = False
            if self.page.break_escape_focus: self.page.focus = 'body'
        else: raise AssertionError((key, self.page.focus))


class FakePage:
    def __init__(self, width, *, escape_closes=False, break_anchor=False, break_escape_focus=False):
        self.width, self.origin, self.spec = width, 'http://127.0.0.1:43817', fixture_spec()
        self.open, self.focus, self.url = False, None, 'about:blank'
        self.history, self.index, self.escape_calls = [], -1, 0
        self.escape_closes, self.break_anchor, self.break_escape_focus = escape_closes, break_anchor, break_escape_focus
        self.keyboard = FakeKeyboard(self)
    def navigate(self, url):
        self.history = self.history[:self.index + 1] + [url]
        self.index += 1; self.url = url
    def goto(self, url, **kwargs):
        self.navigate(url); self.open = False; self.focus = None
        return type('Response', (), {'status':404 if url.endswith(cap.MISSING) else 200})()
    def locator(self, selector): return FakeLocator(self, selector)
    def wait_for_timeout(self, delay): pass
    def go_back(self, **kwargs): self.index -= 1; self.url = self.history[self.index]
    def go_forward(self, **kwargs): self.index += 1; self.url = self.history[self.index]
    def evaluate(self, script, target=None):
        if target is not None:
            return {'target':target,'count':1,'visible':True,'top':90,'bottom':1400,'headerBottom':62,'viewport':900,'hash':self.url.split('#')[-1].join(['#',''])}
        if script == 'location.hash': return '#' + self.url.split('#')[1]
        if script == 'document.activeElement.id': return self.focus
        raise AssertionError(script)


class FakeNativeFlowOrchestration(unittest.TestCase):
    def test_all_three_widths_cover_five_home_and_five_real404_anchor_flows(self):
        for width in cap.WIDTHS:
            page = FakePage(width)
            result = cap.menu_and_history(page, page.origin, width, page.spec)
            self.assertEqual(result['issues'], [])
            self.assertEqual([(r['from'],r['target']) for r in result['anchors']],[(start,target) for start in ('/',cap.MISSING) for target in cap.ANCHORS])
            self.assertEqual([r['startStatus'] for r in result['anchors']], [200]*5+[404]*5)
            self.assertEqual(len(result['steps']), 6 if width <= 860 else 0)
            self.assertEqual(page.escape_calls, 1 if width <= 860 else 0)
            self.assertEqual(result['brandHomeUrl'], page.origin+'/')
            self.assertEqual(result['skipActiveId'], 'main-content')

    def test_escape_close_behavior_is_measured_not_fabricated(self):
        for closes in (False, True):
            page=FakePage(390,escape_closes=closes)
            result=cap.menu_and_history(page,page.origin,390,page.spec)
            self.assertEqual(result['issues'],[])
            self.assertEqual(result['escape']['open'],not closes)
            self.assertTrue(result['escape']['summaryFocused'])
            self.assertEqual(result['dismissal'],{'open':False,'summaryFocused':True})

    def test_bad_anchor_and_escape_focus_fail(self):
        for kwargs, expected in [({'break_anchor':True},'Native anchor navigation/back/forward failure'),
                                 ({'break_escape_focus':True},'Escape unexpectedly changes summary focus or navigation')]:
            page=FakePage(390,**kwargs)
            result=cap.menu_and_history(page,page.origin,390,page.spec)
            self.assertIn(expected,result['issues'])

    def test_evidence_retention_attempts_dom_full_and_viewport_separately(self):
        class Page:
            def content(self): return '<!-- fixture only, not a real capture -->'
            def screenshot(self, **kwargs): raise RuntimeError('fixture screenshot failure')
        with TemporaryDirectory() as tmp:
            record={};cap.retain_page(Page(),Path(tmp),'fixture',record)
            self.assertEqual([r['file'] for r in record['artifacts']],['fixture-dom.html'])
            self.assertEqual([r['artifact'] for r in record['evidenceFailures']],['fixture-full.png','fixture-viewport.png'])
            self.assertEqual(record['artifacts'][0]['sha256'],cap.sha(Path(tmp)/'fixture-dom.html'))


class ExactCaptureCompletionCoverage(unittest.TestCase):
    def fixture(self):
        return {'pages': [{'route': route, 'width': width} for route in cap.ROUTES for width in cap.WIDTHS],
                'flows': [{'width': width} for width in cap.WIDTHS],
                'unknownPath': [{'route': cap.MISSING, 'width': width} for width in cap.WIDTHS]}

    def validate(self, report):
        return cap.validate_capture_coverage(report, [fixture_page(route) for route in cap.ROUTES])

    def test_exact_six_plus_three_plus_three_accept_without_mutation(self):
        report = self.fixture(); before = deepcopy(report)
        result = self.validate(report)
        self.assertEqual(report, before)
        self.assertTrue(result['complete']); self.assertEqual(result['issues'], [])
        self.assertEqual((result['expected'], result['attempted'], result['uniqueAttempted']), (6, 6, 6))
        self.assertEqual({k: v['expected'] for k, v in result['groups'].items()}, {'pages': 6, 'flows': 3, 'unknownPath': 3})
        for rows in report.values(): rows.reverse()
        self.assertTrue(self.validate(report)['complete'])

    def test_missing_extra_duplicate_replacement_and_wrong_page_pairs_reject(self):
        for change in ('missing', 'extra-duplicate', 'duplicate-replacement', 'extra-new', 'wrong-route', 'wrong-width'):
            report = self.fixture(); rows = report['pages']
            if change == 'missing': rows.pop()
            elif change == 'extra-duplicate': rows.append(deepcopy(rows[0]))
            elif change == 'duplicate-replacement': rows[-1] = deepcopy(rows[0])
            elif change == 'extra-new': rows.append({'route': '/regions/', 'width': 390})
            elif change == 'wrong-route': rows[0]['route'] = '/regions/'
            else: rows[0]['width'] = 860
            with self.subTest(change=change):
                result = self.validate(report)
                self.assertFalse(result['complete']); self.assertFalse(result['groups']['pages']['complete'])
                self.assertEqual([x['group'] for x in result['issues']], ['pages'])

    def test_missing_extra_duplicate_replacement_and_wrong_widths_reject_both_groups(self):
        for group in ('flows', 'unknownPath'):
            for change in ('missing', 'extra-duplicate', 'duplicate-replacement', 'extra-new', 'wrong-width'):
                report = self.fixture(); rows = report[group]
                if change == 'missing': rows.pop()
                elif change == 'extra-duplicate': rows.append(deepcopy(rows[0]))
                elif change == 'duplicate-replacement': rows[-1] = deepcopy(rows[0])
                elif change == 'extra-new': rows.append({**rows[0], 'width': 860})
                else: rows[0]['width'] = 860
                with self.subTest(group=group, change=change):
                    result = self.validate(report)
                    self.assertFalse(result['complete']); self.assertFalse(result['groups'][group]['complete'])
                    self.assertEqual([x['group'] for x in result['issues']], [group])

    def test_missing_group_and_malformed_records_fail_closed(self):
        for group in ('pages', 'flows', 'unknownPath'):
            for change in ('absent', 'not-list', 'not-record', 'float-width', 'string-width', 'missing-width'):
                report = self.fixture()
                if change == 'absent': del report[group]
                elif change == 'not-list': report[group] = {}
                elif change == 'not-record': report[group][0] = None
                elif change == 'float-width': report[group][0]['width'] = 320.0
                elif change == 'string-width': report[group][0]['width'] = '320'
                else: del report[group][0]['width']
                with self.subTest(group=group, change=change): self.assertFalse(self.validate(report)['complete'])
        report = self.fixture(); report['unknownPath'][0]['route'] = '/404.html'
        self.assertFalse(self.validate(report)['complete'])

    def test_inspect_uses_exact_completion_validator(self):
        import inspect
        source = inspect.getsource(cap.inspect)
        self.assertIn("report['coverage'] = validate_capture_coverage(report, pages)", source)
        self.assertIn("report['failures'].extend(report['coverage']['issues'])", source)
        self.assertNotIn("coverage = {(row['route'], row['width'])", source)


if __name__ == '__main__': unittest.main(verbosity=2)

