"""Synthetic offline contract regressions; these do not claim rendered pixels."""
import copy,tempfile,unittest
from pathlib import Path
from capture_checks import assert_facts,assert_capture_coverage,banner_kinds
from preview_qa import ROUTE_ORDER,VIEWPORTS,ORIGIN
from reused import digest

class RenderedFactTests(unittest.TestCase):
    def facts(self,route):
        return {'url':'http://127.0.0.1:1234'+route,'viewport':320,'scrollWidth':320,'revisions':[],
                'canonical':[] if route=='/404.html' else [ORIGIN+route],'robots':['noindex,nofollow,noarchive'],
                'h1':['송파'],'title':'송파','descriptions':['안내'],'banners':[],'sharedImageCount':0,
                'removedCaptionOccurrences':0,'fontStatus':'loaded','images':[]}
    def check(self,facts,route='/regions/'):
        assert_facts(facts,route,320,'http://127.0.0.1:1234','unrendered-source-pin',{'banners':{}})
    def test_support_routes_without_banners_or_revision_meta(self):
        for route in ['/regions/','/404.html']:self.check(self.facts(route),route)
    def test_missing_home_banners_rejected(self):
        with self.assertRaises(ValueError):self.check(self.facts('/'),'/')
    def test_unwanted_revision_meta_rejected(self):
        facts=self.facts('/regions/');facts['revisions']=['anything']
        with self.assertRaises(ValueError):self.check(facts)
    def test_indexability_overflow_unsettled_images_rejected(self):
        for key,value in [('robots',['index,follow']),('scrollWidth',322),('fontStatus','loading'),('removedCaptionOccurrences',1),('sharedImageCount',3),('images',[{'complete':False,'width':0,'height':0,'alt':'image'}])]:
            facts=self.facts('/regions/');facts[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.check(facts)

class CoverageTests(unittest.TestCase):
    def fixture(self,root):
        rows=[]
        for width,height in VIEWPORTS:
            for index,route in enumerate(ROUTE_ORDER):
                # Minimal JPEG marker fixture exercises byte/hash/dimension gates only.
                data=b'\xff\xd8\xff\xc0'+(8).to_bytes(2,'big')+b'\x08'+height.to_bytes(2,'big')+width.to_bytes(2,'big')+b'\x00'
                def shot(kind):
                    name=f'screenshots/{width}/{index}-{kind}.jpg';p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
                    return {'screenshot':name,'screenshotSha256':digest(data),'dimensions':{'width':width,'height':height}}
                rows.append({'route':route,'width':width,'height':height,'fullPage':shot('full'),'banners':[{'kind':kind,**shot(kind)} for kind in banner_kinds(route)]})
        return rows
    def test_exact_15_pairs_42_artifact_files(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);rows=self.fixture(p);r=assert_capture_coverage(rows,ROUTE_ORDER,p)
            self.assertEqual(r,{'routeViewportPairs':15,'fullPageScreenshots':15,'focusedBannerScreenshots':27,'requiredFullAndFocusedScreenshots':42})
    def test_missing_pair_and_duplicate_pair_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);rows=self.fixture(p)
            for damaged in [rows[:-1],rows+[rows[0]]]:
                with self.assertRaises(ValueError):assert_capture_coverage(damaged,ROUTE_ORDER,p)
    def test_mutated_screenshot_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);rows=self.fixture(p);(p/rows[0]['fullPage']['screenshot']).write_bytes(b'not captured bytes')
            with self.assertRaises(ValueError):assert_capture_coverage(rows,ROUTE_ORDER,p)
    def test_support_route_banner_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);rows=self.fixture(p);rows[1]['banners']=[rows[0]['banners'][0]]
            with self.assertRaises(ValueError):assert_capture_coverage(rows,ROUTE_ORDER,p)

if __name__=='__main__':unittest.main()
