from pathlib import Path
import importlib.util, unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('source_static_test',ROOT/'tests/source_static_test.py')
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
class SharedSourceHeadingTests(unittest.TestCase):
    def test_grouped_h3_preserves_all_source_metadata(self):
        cards=legacy.cards(legacy.sources).replace('<h2>','<h3>').replace('</h2>','</h3>')
        html='<section class="source-references"><h2>출처 및 확인 정보</h2>'+cards+'</section>'
        legacy.qa.check_rendered_sources(legacy.qa.Document(html),legacy.page)
        with self.assertRaises(AssertionError):
            legacy.qa.check_rendered_sources(legacy.qa.Document(html.replace('시설 &lt;안내&gt;','변조')),legacy.page)
    def test_rendered_sources_use_one_h2_group_and_h3_cards(self):
        for path in (ROOT/'dist').rglob('index.html'):
            html=path.read_text()
            if 'class="source-card"' not in html:continue
            self.assertEqual(html.count('id="source-references-title"'),1,str(path))
            self.assertIn('출처 및 확인 정보</h2>',html)
            self.assertNotRegex(html,r'<section class="source-card"[^>]*>\s*<h2>')
if __name__=='__main__':unittest.main()
