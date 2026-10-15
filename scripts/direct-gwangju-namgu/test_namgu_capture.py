"""Offline strict-card and copied-helper tests. No servers, browsers or requests."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
import production_capture as cap
import managed_robots as robots


def specimen():
    return {'home': {'sections': [
        {'id': 'selection'},
        {'id': 'facility-guide', 'card': {'title': 'Fixture title', 'summary': 'Fixture summary',
             'ctaLabel': 'Fixture call to action', 'href': cap.ARTICLE}},
        {'id': 'consultation'},
    ]}}


class StrictFacilityCard(unittest.TestCase):
    def rejects(self, copy, code):
        with self.assertRaisesRegex(RuntimeError, code):
            cap.facility_card(copy)

    def test_facility_is_second_and_order_is_not_rewritten(self):
        copy = specimen()
        before = deepcopy(copy)
        self.assertIs(cap.facility_card(copy), copy['home']['sections'][1]['card'])
        self.assertEqual(copy, before)
        self.assertEqual([x['id'] for x in copy['home']['sections']], ['selection', 'facility-guide', 'consultation'])

    def test_selection_is_by_id_not_index(self):
        for order in ((0, 1, 2), (1, 0, 2), (0, 2, 1)):
            copy = specimen()
            sections = copy['home']['sections']
            copy['home']['sections'] = [sections[i] for i in order]
            self.assertIs(cap.facility_card(copy), sections[1]['card'])

    def test_missing_or_null_home_and_sections_rejected(self):
        for copy in (None, [], {}, {'home': None}, {'home': []}, {'home': {}},
                     {'home': {'sections': None}}, {'home': {'sections': {}}}):
            with self.subTest(copy=copy):
                self.rejects(copy, 'home_(object|sections)_required')

    def test_zero_facility_id_rejected(self):
        copy = specimen()
        copy['home']['sections'].pop(1)
        self.rejects(copy, 'exactly_one_facility_guide_card_required')

    def test_duplicate_facility_id_even_without_second_card_rejected(self):
        for with_card in (False, True):
            copy = specimen()
            copy['home']['sections'].append(deepcopy(copy['home']['sections'][1]) if with_card else {'id': 'facility-guide'})
            self.rejects(copy, 'exactly_one_facility_guide_card_required')

    def test_zero_card_owners_rejected(self):
        copy = specimen()
        del copy['home']['sections'][1]['card']
        self.rejects(copy, 'exactly_one_facility_guide_card_required')

    def test_extra_card_owner_even_null_rejected(self):
        for card in (None, {}, {'title': 'Extra'}, deepcopy(specimen()['home']['sections'][1]['card'])):
            copy = specimen()
            copy['home']['sections'][0]['card'] = card
            self.rejects(copy, 'exactly_one_facility_guide_card_required')

    def test_wrong_id_and_card_on_wrong_section_rejected(self):
        copy = specimen()
        copy['home']['sections'][1]['id'] = 'facility-guides'
        self.rejects(copy, 'exactly_one_facility_guide_card_required')
        copy = specimen()
        copy['home']['sections'][0]['card'] = copy['home']['sections'][1].pop('card')
        self.rejects(copy, 'exactly_one_facility_guide_card_required')

    def test_null_array_and_scalar_card_shapes_rejected(self):
        for value in (None, [], 'card', True, 7):
            copy = specimen()
            copy['home']['sections'][1]['card'] = value
            self.rejects(copy, 'exact_facility_card_keys_required')

    def test_missing_and_extra_card_keys_rejected(self):
        for key in ('title', 'summary', 'ctaLabel', 'href'):
            copy = specimen()
            del copy['home']['sections'][1]['card'][key]
            self.rejects(copy, 'exact_facility_card_keys_required')
        copy = specimen()
        copy['home']['sections'][1]['card']['unexpected'] = 'value'
        self.rejects(copy, 'exact_facility_card_keys_required')

    def test_every_card_value_must_be_nonempty_string(self):
        for key in ('title', 'summary', 'ctaLabel', 'href'):
            for value in (None, False, 1, [], {}, '', ' ', '\t\n'):
                copy = specimen()
                copy['home']['sections'][1]['card'][key] = value
                self.rejects(copy, 'nonempty_facility_card_strings_required')

    def test_href_must_equal_article_exactly(self):
        for href in ('/', '/regions/', cap.ARTICLE.rstrip('/'), cap.ARTICLE + '#sources',
                     cap.ARTICLE + '?x=1', cap.ORIGIN + cap.ARTICLE,
                     '/regions/chosun-hospital-funeral-wreath/', ' ' + cap.ARTICLE):
            copy = specimen()
            copy['home']['sections'][1]['card']['href'] = href
            self.rejects(copy, 'exact_facility_card_article_href_required')

    def test_javascript_and_python_selection_are_no_longer_positional(self):
        source = (HERE / 'production_capture.py').read_text()
        self.assertIn('mapTarget(facilityCard(copy))', source)
        self.assertIn("./src/lib/donggu-runtime.mjs", source)
        self.assertNotIn('home.sections[0].card', source)
        self.assertNotIn("home['sections'][0]['card']", source)
        self.assertIn("['selection', 'facility-guide', 'consultation']", source)

    def test_control_workflow_literal_is_distinct_from_region(self):
        workflow = (HERE.parents[1] / '.github/workflows/gwangju-namgu-production-publish.yml').read_text()
        self.assertIn('REGION: namgu', workflow)
        self.assertIn("run.path !== '.github/workflows/gwangju-namgu-production-build-only.yml'", workflow)
        self.assertNotIn("run.path !== '.github/workflows/' + process.env.REGION", workflow)


class ActualFrozenSourceReadback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        supplied = os.environ.get('NAMGU_CAPTURE_INSPECTION_ROOT')
        if not supplied:
            raise unittest.SkipTest('Actual source readback requires explicit candidate path')
        cls.root = Path(supplied)
        cls.copy = json.loads((cls.root.parent / 'inputs/reviewed-copy/customer-copy.json').read_text())
        cls.pages, cls.spec = cap.capture_inputs(cls.root)

    def test_actual_second_section_card_and_frozen_copy_remain_exact(self):
        copy = self.copy
        self.assertEqual([s['id'] for s in copy['home']['sections']], ['selection', 'facility-guide', 'consultation'])
        self.assertNotIn('card', copy['home']['sections'][0])
        card = cap.facility_card(copy)
        home = next(page for page in self.pages if page['path'] == '/')
        self.assertEqual(home['contentCards'], [{**card, 'headingTag': 'h3'}])
        self.assertEqual(self.spec['sourceSpecSHA256'], cap.sha(self.root.parent / 'inputs/required-originals.json'))

    def test_b201_social_alt_equals_exact_customer_copy_on_all_non404_pages(self):
        self.assertEqual(self.copy['productCards'][0]['sku'], 'B201')
        alt = self.copy['productCards'][0]['photoAlt']
        self.assertEqual(self.spec['productCards'][0]['alt'], alt)
        for page in self.pages:
            alts = [row['content'] for row in page['socialMetadata'] if row['name'] in ('og:image:alt', 'twitter:image:alt')]
            self.assertEqual(alts, [] if page['path'] == '/404.html' else [alt, alt])


class ManagedRobotsCopy(unittest.TestCase):
    def source(self):
        return ('User-agent: *\nAllow: /\nSitemap: ' + cap.ORIGIN + '/sitemap-index.xml\n').encode()

    def test_helper_is_byte_identical_to_observed_main_copy(self):
        self.assertEqual(cap.sha(HERE / 'managed_robots.py'), '51eebc7dc9a405ade4c5f7da6cdb086a8319d2df690b5b9429e20bd764cbdee5')
        self.assertEqual(robots.digest(robots.MANAGED_PREFIX), robots.PREFIX_SHA256)
        self.assertEqual(len(robots.MANAGED_PREFIX), robots.PREFIX_BYTES)

    def test_only_exact_plain_and_managed_composition_accept_namgu_fixture(self):
        source = self.source()
        for body in (source, robots.MANAGED_PREFIX + source):
            result = robots.verify(body, robots.digest(source), cap.ORIGIN, [cap.ORIGIN + '/', cap.ORIGIN + cap.ARTICLE])
            self.assertTrue(result['rawBodyUnmodified'])
            self.assertEqual(result['rawBodySha256'], robots.digest(body))
        for raw in (robots.MANAGED_PREFIX + source + b'\n', robots.MANAGED_PREFIX + source[:-1],
                    robots.MANAGED_PREFIX.replace(b'search=yes', b'search=no') + source):
            with self.assertRaises(ValueError):
                robots.verify(raw, robots.digest(source), cap.ORIGIN, [cap.ORIGIN + '/'])

    def test_all_managed_prefix_and_source_single_byte_mutations_fail(self):
        source = self.source()
        raw = robots.MANAGED_PREFIX + source
        for index in range(len(raw)):
            with self.subTest(offset=index), self.assertRaises(ValueError):
                robots.verify(raw[:index] + bytes([raw[index] ^ 1]) + raw[index + 1:],
                              robots.digest(source), cap.ORIGIN, [cap.ORIGIN + '/'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
