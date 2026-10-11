from pathlib import Path
import importlib.util,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qa_static',ROOT/'scripts/qa_static.py');qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
class NotFoundSeoTests(unittest.TestCase):
    page='<meta name="robots" content="noindex,nofollow,noarchive"><h1>페이지를 찾을 수 없습니다</h1>'
    def test_clean404_passes(self):qa.check_not_found_seo(self.page)
    def test_home_canonical_rejected(self):
        with self.assertRaisesRegex(AssertionError,'canonical'):qa.check_not_found_seo(self.page+'<link rel="canonical" href="https://suwon.fwith.kr/">')
    def test_home_social_url_rejected(self):
        with self.assertRaisesRegex(AssertionError,'Open Graph'):qa.check_not_found_seo(self.page+'<meta property="og:url" content="https://suwon.fwith.kr/">')
    def test_florist_schema_rejected(self):
        with self.assertRaisesRegex(AssertionError,'schema'):qa.check_not_found_seo(self.page+'<script type="application/ld+json">{"@type":"Florist"}</script>')
    def test_indexing_rejected(self):
        with self.assertRaisesRegex(AssertionError,'noindex'):qa.check_not_found_seo(self.page.replace('noindex,nofollow,noarchive','index,follow'))
