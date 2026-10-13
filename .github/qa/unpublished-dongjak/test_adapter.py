"""Network-free unit/mutation tests. No browser, sockets, Git writes or commits."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from html.parser import HTMLParser
import copy, json, os, unittest
import adapter
from adapter import controls
import run_bound_capture

SOURCE=Path(os.environ.get('SOURCE_ROOT',str(Path(__file__).resolve().parents[4]/'source')))

class Node:
    def __init__(self,tag='',attrs=()):self.tag=tag;self.attrs=dict(attrs);self.children=[]
    def all(self,predicate):
        out=[]
        for x in self.children:
            if isinstance(x,Node):
                if predicate(x):out.append(x)
                out.extend(x.all(predicate))
        return out
    def text(self):return ''.join(x.text() if isinstance(x,Node) else x for x in self.children).strip()
    def first(self,p):return self.all(p)[0]

class DOM(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True);self.root=Node();self.stack=[self.root];self.feed(text)
    def handle_starttag(self,tag,attrs):
        n=Node(tag,attrs);self.stack[-1].children.append(n)
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):self.stack.append(n)
    def handle_startendtag(self,tag,attrs):self.stack[-1].children.append(Node(tag,attrs))
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:self.stack=self.stack[:i];break
    def handle_data(self,data):self.stack[-1].children.append(data)

def has(a):return lambda n:a in n.attrs
def cls(c):return lambda n:c in n.attrs.get('class','').split()

def static_facts(route):
    rel='404.html' if route=='/404.html' else route.lstrip('/')+'index.html'
    root=DOM((SOURCE/adapter.SITE_PATH/'dist'/rel).read_text()).root
    banners=[]
    for n in root.all(has('data-shared-flower-banner')):
        i=n.first(lambda x:x.tag=='img')
        banners.append({'variant':n.attrs['data-shared-flower-banner'],'src':i.attrs['src'],'naturalWidth':int(i.attrs['width']),'naturalHeight':int(i.attrs['height']),'width':1774,'height':887,'alt':i.attrs['alt'],'caption':n.first(lambda x:x.tag=='figcaption').text()})
    faq=[{'question':n.first(has('data-faq-question')).text(),'answer':n.first(has('data-faq-answer')).text()}for n in root.all(has('data-faq-entry'))]
    products=[{'key':n.attrs['data-product-key'],'href':n.first(has('data-order-product-key')).attrs['href'],'priceLabel':n.first(lambda x:x.tag=='strong').text()}for n in root.all(cls('product-card'))]
    ids=['cau-hospital','boramae-hospital']
    facilities=[{'id':n.attrs['id'],'heading':n.text(),'tag':n.tag.upper()}for n in root.all(lambda n:n.tag in ('h2','h3') and n.attrs.get('id')in ids)]
    guides=[n.attrs['href'] for section in root.all(has('data-region-district'))for n in section.all(cls('page-card'))]
    legal=root.all(has('data-legal-unit'));admins=root.all(has('data-administrative-unit'))
    return {'banners':banners,'faq':faq,'products':products,'facilities':facilities,'guideLinks':guides,
        'legalUnits':[n.attrs['data-legal-unit']for n in legal],
        'legalLinks':[{'unitKey':n.attrs['data-legal-unit'],'href':a.attrs['href'],'candidateId':a.attrs['data-candidate-id']}for n in legal for a in n.all(has('data-candidate-id'))],
        'adminRows':[{'key':n.attrs['data-administrative-unit'],'relations':[s.text()for s in n.all(lambda x:x.tag=='span')]}for n in admins],
        'adminFacilityLinks':[a.attrs['href']for n in admins for a in n.all(lambda x:x.tag=='a')]}

class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.expected=adapter.expectations(SOURCE/adapter.SITE_PATH)
    def spec(self):return {'sourceSha':adapter.SOURCE_SHA,'sourceTree':adapter.SOURCE_TREE,'repositoryTree':adapter.REPOSITORY_TREE,'path':adapter.SITE_PATH,'siteUrl':adapter.SITE_URL,'productionApproved':False,'indexable':False,'routes':adapter.ROUTES,'sitemapRoutes':[],'frozenManifestSha256':adapter.MANIFEST_SHA}
    def focus(self):return {'visible':True,'width':250,'height':200,'left':14,'right':264,'top':100,'bottom':300,'safeTop':62,'safeBottom':682,'viewportWidth':320,'hitTests':[True]*9}
    def test_upstream_bytes_identical(self):adapter.verify_upstream()
    def test_frozen_629_source_bytes(self):self.assertEqual(adapter.verify_frozen_bytes(SOURCE,allow_generated=True)['files'],629)
    def test_expected_scope(self):
        self.assertEqual(self.expected['captureCount'],12);self.assertEqual(self.expected['customerCaptureCount'],9)
        self.assertEqual(sum(len(adapter.focus_labels(self.expected,r))for r in adapter.ROUTES)*3,150)
    def test_local_static_html_matches_adapter_assertions(self):
        for route in adapter.ROUTES:
            with self.subTest(route=route):adapter.validate_extra_facts(static_facts(route),self.expected,route)
    def test_current_build_has_native_unpublished_boundary(self):
        # Reads current generated revision only for STATIC output validation.
        # This does not allow the value into the exact-saved-source binding.
        site=SOURCE/adapter.SITE_PATH
        revision=adapter.SOURCE_SHA
        spec={**self.spec(),'sourceSha':revision}
        result=controls.validate_build(site,spec)
        self.assertEqual(sum(x.endswith('.html') for x in result),4)
    def test_real_banner_asset_hashes(self):
        for b in self.expected['banners']:
            self.assertEqual(adapter.sha((SOURCE/adapter.SITE_PATH/'public'/b['src'].lstrip('/')).read_bytes()),b['sha256'])
    def test_exact_spec_schema(self):adapter.validate_spec(self.spec())
    def test_pending_sha_rejected(self):
        for key in ('sourceSha','sourceTree','repositoryTree'):
            for value in (None,'local','main','a12c406','0'*40):
                with self.subTest(key=key,value=value),self.assertRaises(AssertionError):adapter.validate_spec({**self.spec(),key:value})
    def test_indexable_mutation_rejected(self):
        with self.assertRaises(AssertionError):adapter.validate_spec({**self.spec(),'indexable':True})
    def test_production_approval_mutation_rejected(self):
        with self.assertRaises(AssertionError):adapter.validate_spec({**self.spec(),'productionApproved':True})
    def test_sitemap_mutation_rejected(self):
        with self.assertRaises(AssertionError):adapter.validate_spec({**self.spec(),'sitemapRoutes':['/']})
    def test_routes_mutation_rejected(self):
        with self.assertRaises(AssertionError):adapter.validate_spec({**self.spec(),'routes':['/']})
    def test_review_binding_mutation_rejected(self):
        with self.assertRaises(AssertionError):adapter.validate_spec({**self.spec(),'frozenManifestSha256':'0'*64})
    def test_wrong_site_scope_rejected(self):
        for k,v in [('siteUrl','https://example.invalid'),('path','site-factory/seoul-guro-flower')]:
            with self.assertRaises(AssertionError):adapter.validate_spec({**self.spec(),k:v})
    def test_fake_sha_bind_rejected(self):
        for sha in (None,'main','local','0'*40):
            with self.assertRaises(AssertionError):adapter.make_binding(SOURCE,sha)
    def test_actual_source_binding_requires_exact_saved_tree(self):
        head=controls.git(SOURCE,'rev-parse','HEAD')
        paths=controls.git(SOURCE,'ls-tree','-r','--name-only',head,'--',adapter.SITE_PATH).splitlines()
        expected=[e['path'] for e in adapter.frozen_entries()]
        self.assertEqual(paths,expected)
        changed=controls.git(SOURCE,'diff','--name-only','HEAD','--',adapter.SITE_PATH).splitlines()
        if changed:
            self.assertEqual(changed,[adapter.GENERATED_REVISION])
            controls.verify_source(SOURCE,self.spec())
            adapter.verify_frozen_bytes(SOURCE,allow_generated=True)
            with self.assertRaisesRegex(AssertionError,'Frozen source changed'):adapter.make_binding(SOURCE,head)
        else:self.assertEqual(adapter.make_binding(SOURCE,head)['sourceSha'],head)
    def test_frozen_byte_mutation_rejected_without_source_edit(self):
        e=copy.deepcopy(adapter.frozen_entries());e[0]['sha256']='0'*64
        with patch.object(adapter,'frozen_entries',return_value=e),self.assertRaisesRegex(AssertionError,'Frozen source changed'):adapter.verify_frozen_bytes(SOURCE)
    def test_frozen_blob_mutation_rejected_without_source_edit(self):
        e=copy.deepcopy(adapter.frozen_entries());e[0]['gitBlobSha']='0'*40
        with patch.object(adapter,'frozen_entries',return_value=e),self.assertRaisesRegex(AssertionError,'Frozen blob mismatch'):adapter.verify_frozen_bytes(SOURCE)
    def test_missing_banner_rejected(self):
        f=static_facts('/');f['banners'].pop()
        with self.assertRaises(AssertionError):adapter.validate_extra_facts(f,self.expected,'/')
    def test_banner_wrong_order_rejected(self):
        f=static_facts('/');f['banners'].reverse()
        with self.assertRaises(AssertionError):adapter.validate_extra_facts(f,self.expected,'/')
    def test_banner_crop_and_src_mutations_rejected(self):
        for key,val in [('src','/wrong.webp'),('naturalWidth',500),('width',1000),('height',0.1),('alt',''),('caption','실제 상품')]:
            f=static_facts('/');f['banners'][0][key]=val
            with self.subTest(key=key),self.assertRaises(AssertionError):adapter.validate_extra_facts(f,self.expected,'/')
    def test_directory_banner_rejected(self):
        f=static_facts('/regions/');f['banners']=static_facts('/')['banners']
        with self.assertRaises(AssertionError):adapter.validate_extra_facts(f,self.expected,'/regions/')
    def test_faq_exact_copy_rejected(self):
        route=adapter.ROUTES[2];f=static_facts(route);f['faq'][0]['answer']='changed'
        with self.assertRaises(AssertionError):adapter.validate_extra_facts(f,self.expected,route)
    def test_product_price_link_count_rejected(self):
        route=adapter.ROUTES[2]
        for key,val in [('priceLabel','상품 기본가격 1원'),('href','https://evil.invalid'),('key','wrong')]:
            f=static_facts(route);f['products'][0][key]=val
            with self.subTest(key=key),self.assertRaises(AssertionError):adapter.validate_extra_facts(f,self.expected,route)
        f=static_facts(route);f['products'].pop()
        with self.assertRaises(AssertionError):adapter.validate_extra_facts(f,self.expected,route)
    def test_facility_hierarchy_rejected(self):
        route=adapter.ROUTES[2];f=static_facts(route);f['facilities'][0]['tag']='H2'
        with self.assertRaises(AssertionError):adapter.validate_extra_facts(f,self.expected,route)
    def test_directory_extra_card_rejected(self):
        f=static_facts('/regions/');f['guideLinks'].append('/new/')
        with self.assertRaises(AssertionError):adapter.validate_extra_facts(f,self.expected,'/regions/')
    def test_legal_to_wrong_anchor_rejected(self):
        f=static_facts('/regions/');f['legalLinks'][0]['href']+='_wrong'
        with self.assertRaises(AssertionError):adapter.validate_extra_facts(f,self.expected,'/regions/')
    def test_legal_unit_missing_rejected(self):
        f=static_facts('/regions/');f['legalUnits'].pop()
        with self.assertRaises(AssertionError):adapter.validate_extra_facts(f,self.expected,'/regions/')
    def test_administrative_facility_link_rejected(self):
        f=static_facts('/regions/');f['adminFacilityLinks']=['/regions/dongjak-funeral-wreath/#yeouido-stmary']
        with self.assertRaises(AssertionError):adapter.validate_extra_facts(f,self.expected,'/regions/')
    def test_administrative_relation_mutation_rejected(self):
        f=static_facts('/regions/');f['adminRows'][0]['relations'].pop()
        with self.assertRaises(AssertionError):adapter.validate_extra_facts(f,self.expected,'/regions/')
    def test_unoccluded_focus(self):adapter.assert_focus(self.focus())
    def test_sticky_header_and_cta_occlusion_rejected(self):
        for key,val in [('top',20),('bottom',740),('hitTests',[True,False]),('left',-5),('right',340),('visible',False)]:
            with self.subTest(key=key),self.assertRaises(AssertionError):adapter.assert_focus({**self.focus(),key:val})
    def test_missing_supplemental_grid_rejected(self):
        with self.assertRaises(AssertionError):adapter.validate_supplemental_evidence([],[],self.expected,Path('/tmp'))
    def make_synthetic_screenshots(self,root):
        rows=[];flows=[]
        for w,h in controls.VIEWPORTS:
            for route in adapter.ROUTES:
                name='home' if route=='/' else route.strip('/').replace('/','--')
                for label in adapter.focus_labels(self.expected,route):
                    facts={**self.focus(),'width':w-28,'viewportWidth':w,'right':w-14,'renderSignature':label}
                    if label in ('legal-1','admin-1'):facts['height']=250;facts['bottom']=350
                    rows.append({'width':w,'height':h,'route':route,'label':label,'facts':facts,'issues':[]})
            flows.append({'width':w,'flow':'admin-open-close-reopen','passed':True})
            flows += [{'width':w,'flow':'legal-facility-anchor-first-landing','href':x['href'],'screenshot':f'supplemental/{w}/anchor/{x["candidateId"]}.jpg'}for x in self.expected['legalLinks']]
        selection=adapter.screenshot_selection(rows)
        for row in rows:
            key=(row['width'],row['route'],row['label']);row['screenshotReasons']=selection.get(key,[])
            if key in selection:
                name='home' if row['route']=='/' else row['route'].strip('/').replace('/','--')
                row['screenshot']=f'supplemental/{row["width"]}/{name}/{row["label"]}.jpg'
        for row in [r for r in rows if 'screenshot' in r]+[f for f in flows if 'screenshot' in f]:
            w=row['width'];h=dict(controls.VIEWPORTS)[w]
            # Minimal metadata fixture; deliberately NOT claimed to be viewable pixels.
            data=b'\xff\xd8\xff\xc0\x00\x11\x08'+h.to_bytes(2,'big')+w.to_bytes(2,'big')+b'\x03'
            file=root/row['screenshot'];file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(data)
            row.update({'screenshotSha256':adapter.sha(data),'dimensions':{'width':w,'height':h}})
        return rows,flows
    def test_supplemental_integrity_positive(self):
        with TemporaryDirectory() as temp:
            root=Path(temp);rows,flows=self.make_synthetic_screenshots(root)
            result=adapter.validate_supplemental_evidence(rows,flows,self.expected,root)
            self.assertEqual(result,{'geometryChecks':150,'focusScreenshots':33,'anchorFirstLandingScreenshots':6,'interactions':9})
    def test_supplemental_integrity_mutations_rejected(self):
        with TemporaryDirectory() as temp:
            root=Path(temp);rows,flows=self.make_synthetic_screenshots(root)
            cases=[(rows[:-1],flows),(rows[::-1],flows),(rows,flows[:-1]),(rows,[flows[0]]+flows[:-1])]
            for r,f in cases:
                with self.assertRaises(AssertionError):adapter.validate_supplemental_evidence(r,f,self.expected,root)
            missing_anchor=copy.deepcopy(flows);missing_anchor[1].pop('screenshot')
            with self.assertRaisesRegex(AssertionError,'Missing initial anchor'):adapter.validate_supplemental_evidence(rows,missing_anchor,self.expected,root)
            first=next(i for i,r in enumerate(rows) if 'screenshot' in r)
            for key,val in [('screenshotSha256','0'*64),('dimensions',{'width':1,'height':1}),('screenshot','../escape.jpg')]:
                mutated=copy.deepcopy(rows);mutated[first][key]=val
                with self.subTest(key=key),self.assertRaises(AssertionError):adapter.validate_supplemental_evidence(mutated,flows,self.expected,root)
            (root/rows[first]['screenshot']).unlink()
            with self.assertRaises(AssertionError):adapter.validate_supplemental_evidence(rows,flows,self.expected,root)
    def test_screenshot_selection_keeps_new_rendering_and_failure(self):
        with TemporaryDirectory() as temp:
            rows,flows=self.make_synthetic_screenshots(Path(temp))
            selected=adapter.screenshot_selection(rows);self.assertEqual(len(selected),33)
            banner=next(r for r in rows if r['width']==320 and r['route']==adapter.ROUTES[2] and r['label']=='banner-message')
            banner['facts']['renderSignature']='different-font-or-image-rendering'
            self.assertEqual(len(adapter.screenshot_selection(rows)),34)
            ordinary=next(r for r in rows if r['width']==320 and r['label']=='legal-2')
            ordinary['issues']=['Synthetic obstruction']
            self.assertEqual(len(adapter.screenshot_selection(rows)),35)
    def test_execution_blocked_outside_deferred_runner(self):
        with patch.object(sys_module(),'argv',['run_bound_capture.py','--binding','not-present.json']),patch.dict(os.environ,{},clear=True),self.assertRaisesRegex(AssertionError,'Deferred authorized GitHub runner only'):run_bound_capture.main()
    def test_javascript_sources_are_defined_without_launch(self):
        self.assertIn('elementFromPoint',run_bound_capture.FOCUS_FACTS)
        self.assertIn('adminFacilityLinks',run_bound_capture.EXTRA_FACTS)

def sys_module():
    import sys
    return sys

if __name__=='__main__':unittest.main()
