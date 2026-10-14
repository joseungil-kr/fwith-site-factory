"""Gangdong-specific regression checks; synthetic fixtures are not browser evidence."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import capture
import capture_checks
import production_output
import publish
import preview_qa


class GangdongCaptureInputTests(unittest.TestCase):
    def fixture(self, root):
        assets=[]
        for prefix,names in [('products',[s+'.jpg' for s in ['B060','B201','B203','B205','C200','C203','C204','C205']]),('shared-banners',['flower-'+k+'.webp' for k in ['message','budget','consultation']])]:
            for name in names:
                data=('OFFLINE_FIXTURE_'+name).encode();path='public/images/'+prefix+'/'+name
                file=root/'dist'/path.removeprefix('public/');file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(data)
                assets.append(dict(path=path,sha256=hashlib.sha256(data).hexdigest(),width=500 if prefix=='products' else 1774,height=500 if prefix=='products' else 887))
        routes={'home':'/','directory':'/regions/','condolence':'/regions/gangdong-condolence-wreath/','wedding':'/regions/gangdong-wedding-wreath/','404':'/404.html'}
        counts={'home':2,'directory':0,'condolence':4,'wedding':4,'404':0}
        runtime=dict(pages=[dict(id=k,path=v,faqs=[dict(question='Q',answer='A')]*counts[k]) for k,v in routes.items()],assets=assets,products=[dict(sku=str(n)) for n in range(8)],common=dict(banners=[dict(id=k,assetName='flower-'+k+'.webp',alt='꽃 전화 1844-0644') for k in ['message','budget','consultation']]))
        (root/'src/data').mkdir(parents=True)
        def save():(root/'src/data/gangdong-runtime.json').write_text(json.dumps(runtime))
        save();return runtime,save

    def test_actual_gangdong_shape_no_asset_id_or_duplicate_extension(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);runtime,save=self.fixture(root);pages,spec=capture.capture_inputs(root)
            self.assertEqual([p['path'] for p in pages],preview_qa.ROUTE_ORDER)
            self.assertEqual({b['file'] for b in spec['banners'].values()},{'flower-'+k+'.webp' for k in ['message','budget','consultation']})

    def test_wrong_faq_denominator_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);runtime,save=self.fixture(root);runtime['pages'][0]['faqs'].pop();save()
            with self.assertRaisesRegex(ValueError,'gangdong_faq_denominator'):capture.capture_inputs(root)

    def test_missing_product_or_banner_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);runtime,save=self.fixture(root);runtime['products'].pop();save()
            with self.assertRaisesRegex(ValueError,'gangdong_image_denominator'):capture.capture_inputs(root)

    def test_changed_banner_geometry_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);runtime,save=self.fixture(root);runtime['assets'][-1]['width']=100;save()
            with self.assertRaisesRegex(ValueError,'banner_asset_dimensions'):capture.capture_inputs(root)

    def test_asset_bytes_still_bound(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);runtime,save=self.fixture(root);(root/'dist/images/products/B060.jpg').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'image_asset_changed'):capture.capture_inputs(root)


class Gangdong404Tests(unittest.TestCase):
    def test_public_404_contract_is_noindex_follow(self):
        self.assertEqual(publish.expected_robots('/404.html'),{'noindex','follow'})
        f=dict(url='http://127.0.0.1:1/404.html',viewport=320,scrollWidth=320,revisions=['a'*40],canonical=[],robots=['noindex,follow'],h1=['없는 페이지'],title='없는 페이지',descriptions=['다시 찾기'],banners=[],sharedImageCount=0,removedCaptionOccurrences=0,fontStatus='loaded',images=[])
        capture_checks.assert_facts(f,'/404.html',320,'http://127.0.0.1:1','a'*40,{'releaseMode':'production'})
        for robots in ['index,follow','noindex,nofollow,noarchive','noindex']:
            with self.subTest(robots=robots),self.assertRaisesRegex(ValueError,'rendered robots'):
                capture_checks.assert_facts({**f,'robots':[robots]},'/404.html',320,'http://127.0.0.1:1','a'*40,{'releaseMode':'production'})

    def test_generated_customer_role_map_allowed_but_arbitrary_json_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'package.json').write_text('{}');(root/'customer-string-output-role-map.json').write_text('{}')
            preview_qa.source_inventory(root,['package.json'])
            (root/'unreviewed-customer.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'untracked_or_missing_source_file'):preview_qa.source_inventory(root,['package.json'])

    def test_no_standalone_preview_workflow_is_installed(self):
        root=Path(__file__).resolve().parents[2]
        self.assertFalse((root/'.github/workflows/seoul-gangdong-preview-qa.yml').exists())
        self.assertIn('chromium_sandbox=True',(Path(__file__).parent/'browser_rendering.py').read_text())

if __name__=='__main__':unittest.main()
