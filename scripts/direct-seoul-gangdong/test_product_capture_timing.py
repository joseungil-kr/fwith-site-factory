"""Offline regressions for lazy-image inspection timing; not browser evidence.

Execute the controller's actual product-check statements with a page double.
Extracting the statements avoids importing or launching browser tooling.
"""
import ast
import copy
from pathlib import Path
import unittest


def check_key(node, key):
    return (isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Subscript) and
        isinstance(target.value, ast.Name) and target.value.id == 'checks' and
        isinstance(target.slice, ast.Constant) and target.slice.value == key
        for target in node.targets))


def product_check_block():
    path = Path(__file__).with_name('browser_rendering.py')
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        starts = [i for i, item in enumerate(node.body) if check_key(item, 'productLinks')]
        if not starts:
            continue
        start = starts[0] - 1
        while start >= 0:
            item = node.body[start]
            if (isinstance(item, ast.Expr) and isinstance(item.value, ast.Call)
                    and isinstance(item.value.func, ast.Attribute)
                    and item.value.func.attr == 'goto'):
                break
            start -= 1
        end = next(i for i, item in enumerate(node.body) if check_key(item, 'mobileMenu'))
        if start < 0:
            raise AssertionError('Product inspection must follow explicit route navigation')
        return node.body[start:end]
    raise AssertionError('Actual controller product-check block missing')


class PageDouble:
    def __init__(self, rows):
        self.rows = rows
        self.ready = True
        self.events = []

    def goto(self, url, **kwargs):
        self.ready = False
        self.events.append('navigate')

    def locator(self, selector):
        assert selector == '[data-product-sku]'
        return self

    def evaluate_all(self, expression):
        self.events.append('measure')
        rows = copy.deepcopy(self.rows)
        if not self.ready:
            for row in rows:
                row.update(naturalWidth=0, naturalHeight=0)
        return rows


class ProductCaptureTimingTests(unittest.TestCase):
    def run_block(self, mutate=None, omit_settle=False, broken_image=False):
        sku = 'C205'
        product = dict(sku=sku, img='/images/products/C205.jpg',
                       cta=dict(href='https://fwith.co.kr/shop/item.php?it_id=C205', label='이 상품 상세 보기'))
        row = dict(sku=sku, links=[dict(sku=sku, **product['cta'])],
                   image=product['img'], fit='contain', naturalWidth=500, naturalHeight=500)
        if mutate:
            mutate(row)
        page = PageDouble([row])

        def settle(actual_page):
            self.assertIs(actual_page, page)
            page.events.append('settle')
            if broken_image:
                raise TimeoutError('Image failed to load or decode')
            page.ready = True

        statements = product_check_block()
        if omit_settle:
            statements = [node for node in statements if not (
                isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name) and node.value.func.id == 'settle')]
        block = ast.fix_missing_locations(ast.Module(body=statements, type_ignores=[]))
        values = dict(page=page, settle=settle, origin='http://127.0.0.1:1234', route='/',
                      checks={}, expected={'sections': [{'productSKUs': [sku]}]},
                      spec={'products': [product]}, issue=[])
        exec(compile(block, 'actual-controller-product-check', 'exec'), values)
        return page, values

    def test_measurement_waits_after_fresh_navigation(self):
        page, values = self.run_block()
        self.assertEqual(page.events, ['navigate', 'settle', 'measure'])
        self.assertEqual(values['issue'], [])
        self.assertEqual(values['checks']['productLinks'][0]['naturalWidth'], 500)

    def test_original_missing_settle_reproduces_failure(self):
        page, values = self.run_block(omit_settle=True)
        self.assertEqual(page.events, ['navigate', 'measure'])
        self.assertEqual(values['checks']['productLinks'][0]['naturalWidth'], 0)
        self.assertEqual(values['issue'], ['Product CTA/image containment differs from exact source: C205'])

    def test_failed_loading_remains_fatal(self):
        with self.assertRaisesRegex(TimeoutError, 'failed to load or decode'):
            self.run_block(broken_image=True)

    def test_bad_dimensions_still_fail(self):
        for key, value in [('naturalWidth', 0), ('naturalHeight', 499)]:
            with self.subTest(key=key):
                _, values = self.run_block(lambda row: row.update({key: value}))
                self.assertTrue(values['issue'])

    def test_wrong_image_or_fit_still_fails(self):
        for key, value in [('image', '/wrong.jpg'), ('fit', 'cover')]:
            with self.subTest(key=key):
                _, values = self.run_block(lambda row: row.update({key: value}))
                self.assertTrue(values['issue'])

    def test_wrong_cta_and_missing_cta_still_fail(self):
        mutations = [lambda row: row.update(links=[]),
                     lambda row: row['links'][0].update(label='Wrong label'),
                     lambda row: row['links'][0].update(href='https://example.invalid/')]
        for number, mutate in enumerate(mutations):
            with self.subTest(number=number):
                _, values = self.run_block(mutate)
                self.assertTrue(values['issue'])


if __name__ == '__main__':
    unittest.main()
