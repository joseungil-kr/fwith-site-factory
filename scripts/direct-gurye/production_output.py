"""Exact production output contract. This does not contact a public host."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import html
import json
import os
import re
import xml.etree.ElementTree as ET

EQUIVALENCE_SHA='79980f8672a9147028a130d38c39826b52cc01c2d11fee901e4e03b341df0dca'
EQUIVALENCE_PATH=Path(__file__).resolve().parent/'production-equivalence.json'

ORIGIN = 'https://gurye.fwith.kr'
SOCIAL_IMAGE_PATH='/images/products/B201.jpg'
SOCIAL_IMAGE_ALT='흰 꽃과 노란 꽃 장식, 흰 리본이 보이는 근조 3단 화환 B201의 판매용 상품 사진'
SOCIAL_IMAGE_SHA256='7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3'
ROUTES = ['/']
FILES = {'index.html':'/', '404.html':'/404.html'}
PROOF = {'origin': 'https://gurye.fwith.kr', 'path': '/cc583d309cec4f73ff7832d6a7d7b36f.txt', 'sha256': '3e26b5fd0f182a58af4f4905ba49b397f0f99d4dde26fc5b50e9839bb73ecb72'} # Dedicated public proof; this validator never submits.


class Metadata(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.robots, self.revisions, self.canonical, self.social, self.schemas = [], [], [], [], []
        self.h1 = 0
        self.main_targets = []
        self.images,self.product_skus,self.faq_questions,self.faq_answers,self.banners,self.reference_totals,self.internal_links = [],[],[],[],[],[],[]
        self.copy_keys=[];self.copy_text={};self._copy_stack=[]
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        assert len(values) == len(attrs), 'Duplicate HTML attribute'
        self._copy_stack.append((tag,values.get('data-copy-key')))
        if 'data-copy-key'in values:self.copy_keys.append(values['data-copy-key']);self.copy_text[values['data-copy-key']]=''
        if tag == 'meta':
            if values.get('name') == 'robots': self.robots.append(values.get('content'))
            if values.get('name') == 'site-factory-revision': self.revisions.append(values.get('content'))
            if values.get('property', values.get('name', '')).startswith(('og:', 'twitter:')): self.social.append(values)
        if tag == 'link' and values.get('rel') == 'canonical': self.canonical.append(values.get('href'))
        if tag == 'script' and values.get('type') == 'application/ld+json': self.schemas.append(values)
        if tag == 'img': self.images.append(values)
        if 'data-order-product-sku' in values:self.product_skus.append(values['data-order-product-sku'])
        if re.fullmatch(r'faq-[1-3]\.question',values.get('data-copy-key','')):self.faq_questions.append(values)
        if re.fullmatch(r'faq-[1-3]\.answer',values.get('data-copy-key','')):self.faq_answers.append(values)
        if tag=='img'and values.get('src','').startswith('/images/shared-banners/flower-'):self.banners.append(Path(values['src']).stem.removeprefix('flower-'))
        if 'data-reference-total-krw' in values:self.reference_totals.append(values['data-reference-total-krw'])
        if tag=='a' and values.get('href','').startswith('/'):
            self.internal_links.append(values['href'])
        if tag == 'h1': self.h1 += 1
        if tag == 'main': self.main_targets.append(values)


    def handle_data(self,data):
        for _,key in self._copy_stack:
            if key:self.copy_text[key]+=data

    def handle_endtag(self,tag):
        for i in range(len(self._copy_stack)-1,-1,-1):
            if self._copy_stack[i][0]==tag:
                del self._copy_stack[i:];break


def sha(data):
    return hashlib.sha256(data).hexdigest()


def reachable_sitemap_urls(dist, inventory):
    """Accept only the declared index -> urlset graph, with no orphan XML.

    Nested indexes are outside this fixed site's contract. Requiring urlset
    children also rejects self references and longer index cycles by role.
    """
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    root_name = 'sitemap-index.xml'
    assert root_name in inventory, 'Sitemap index missing'
    index = ET.parse(dist / root_name).getroot()
    assert index.tag == ns + 'sitemapindex' and len(index) > 0, 'Nonempty sitemapindex root required'
    assert all(child.tag == ns + 'sitemap' for child in index), 'Invalid sitemap index child role'
    children = []
    for entry in index:
        assert all(child.tag in {ns + 'loc', ns + 'lastmod'} for child in entry), 'Invalid sitemap index entry'
        locations = entry.findall(ns + 'loc')
        assert len(locations) == 1 and len(locations[0]) == 0, 'Exactly one child sitemap location required'
        assert len(entry.findall(ns + 'lastmod')) <= 1, 'Duplicate sitemap lastmod'
        value = locations[0].text or ''
        assert value.startswith(ORIGIN + '/'), 'Foreign sitemap child'
        name = value[len(ORIGIN) + 1:]
        assert re.fullmatch(r'sitemap-[A-Za-z0-9_-]+\.xml', name), 'Invalid sitemap child path'
        assert name != root_name and name in inventory, 'Self reference or missing sitemap child'
        assert name not in children, 'Duplicate sitemap child reference'
        children.append(name)
    assert {name for name in inventory if name.lower().endswith('.xml')} == {root_name, *children}, 'Orphan or undeclared XML artifact'
    urls = []
    for name in children:
        child = ET.parse(dist / name).getroot()
        assert child.tag == ns + 'urlset' and len(child) > 0, 'Nonempty child urlset required; nested indexes forbidden'
        assert all(entry.tag == ns + 'url' for entry in child), 'Invalid urlset child role'
        for entry in child:
            allowed = {ns + 'loc', ns + 'lastmod', ns + 'changefreq', ns + 'priority'}
            assert all(field.tag in allowed for field in entry), 'Invalid sitemap URL entry'
            assert len({field.tag for field in entry}) == len(entry), 'Duplicate sitemap URL field'
            locations = entry.findall(ns + 'loc')
            assert len(locations) == 1 and len(locations[0]) == 0, 'Exactly one page URL required'
            urls.append(locations[0].text or '')
    assert len(urls) == 1 and set(urls) == {ORIGIN + path for path in ROUTES}, 'Exact one reachable home sitemap URL required'
    return urls


def indexnow_payload(urls, proof=PROOF):
    """Pure local payload construction. It never submits or grants release approval."""
    assert isinstance(urls,list) and urls==[ORIGIN+'/'], 'IndexNow requires exactly the canonical home URL'
    assert proof==PROOF, 'Exact dedicated Gurye public proof required'
    return {'host': ORIGIN.removeprefix('https://'), 'key':Path(PROOF['path']).stem,
            'keyLocation':ORIGIN+PROOF['path'], 'urlList':list(urls)}


def baseline():
    raw=EQUIVALENCE_PATH.read_bytes()
    assert sha(raw)==EQUIVALENCE_SHA, 'Pinned equivalence baseline changed'
    result=json.loads(raw)
    assert result['allowedGeneratedBodyChanges']==[] and len(result['htmlBodies'])==2 and len(result['staticAssets'])==8
    assert set(result['htmlBodies'])==set(FILES)==set(result['htmlPrefixes'])
    return result


def equivalence(dist,revision):
    expected=baseline();dist=Path(dist)
    assert revision==expected['sourceRevision']=='de6147d063dc563a6ef0f82e6ebf0e6e4ca3d10f', 'Exact saved metadata successor required'
    for filename in FILES:
        raw=(dist/filename).read_bytes();start=raw.find(b'<body')
        assert start>=0 and sha(raw[start:])==expected['htmlBodies'][filename], 'Customer body changed: '+filename
        assert raw[:start].decode()==expected['htmlPrefixes'][filename], 'Non-reviewed head change: '+filename
    for name,digest in expected['staticAssets'].items():assert sha((dist/name).read_bytes())==digest, 'Static asset changed: '+name
    return {'htmlBodiesByteIdentical':2,'staticAssetsByteIdentical':8,'headChangesExactlyAllowed':2}


def inspect_dist(dist, mode, proof=None):
    dist = Path(dist)
    assert mode['mode'] == 'production' and mode['indexable'] is True and mode['origin'] == ORIGIN
    if mode['mode']=='production' and proof is None:proof=PROOF
    assert (re.fullmatch('[0-9a-f]{40}',mode['revision']) if mode['mode']=='production' else mode['revision']=='local-inspection'), 'Offline marker cannot authorize production'
    paths = [p for p in dist.rglob('*') if p.is_file()]
    assert not any(p.is_symlink() for p in dist.rglob('*')), 'Artifact symlink forbidden'
    inventory = {p.relative_to(dist).as_posix(): sha(p.read_bytes()) for p in paths}
    assert {name for name in inventory if name.endswith('.html')} == set(FILES), 'Exact index.html and 404.html required'
    expected=set(FILES)|set(baseline()['staticAssets'])|{'robots.txt','_headers','sitemap-index.xml','sitemap-0.xml'}
    if mode['mode']=='production':expected.add(PROOF['path'].lstrip('/'))
    assert set(inventory)==expected, 'Exact production output inventory required'
    assert not any(Path(name).name in {'_worker.js', '_routes.json', '_redirects', 'package.json', 'package-lock.json'} for name in inventory), 'Executable or routing artifact forbidden'
    for filename, route in FILES.items():
        doc = Metadata((dist / filename).read_text(encoding='utf-8'))
        robots = 'noindex,follow' if route == '/404.html' else 'index,follow'
        assert doc.h1 == 1 and doc.revisions == [mode['revision']], 'Exact H1/revision required'
        assert doc.main_targets == [{'id':'main-content','tabindex':'-1'}], 'Exact keyboard-focus main target required'
        assert doc.robots == [robots], 'Exact single robots meta required'
        assert doc.canonical == ([] if route == '/404.html' else [ORIGIN + route]), 'Exact single canonical required'
        assert all(href=='/' or re.fullmatch(r'/#[A-Za-z][A-Za-z0-9-]*',href) for href in doc.internal_links), 'Only reviewed home anchor links permitted'
        if route == '/404.html':
            assert not doc.schemas and not doc.social, '404 schema/social forbidden'
            assert len(doc.copy_keys)==15 and len(set(doc.copy_keys))==15, 'Exact 404 occurrences required'
            assert not doc.images and not doc.product_skus and not doc.faq_questions and not doc.faq_answers and not doc.banners and not doc.reference_totals, 'Technical 404 must not contain purchase content'
        else:
            assert doc.product_skus==['B201','B203','B205','B060'], 'Exact ordered four home products required'
            assert len(doc.faq_questions)==len(doc.faq_answers)==3, 'Three complete home FAQ pairs required'
            assert doc.banners==['message','budget','consultation'] and len(doc.images)==7, 'Three banners and seven home images required'
            assert [re.sub(r'[^0-9]','',doc.copy_text.get('product.'+sku+'.sumLabel',''))for sku in ['B201','B203','B205','B060']]==['79000','99000','129000','169000'], 'Exact Gurye reference budgets required'
            assert all(re.sub(r'[^0-9]','',doc.copy_text.get('product.'+sku+'.shippingLabel',''))=='20000' for sku in ['B201','B203','B205','B060']), 'Exact Gurye additional shipping required'
            assert len(doc.copy_keys)==88 and len(set(doc.copy_keys))==88, 'Exact home occurrences required'
            assert not any('hidden' in a or a.get('aria-hidden')=='true' for a in doc.faq_questions+doc.faq_answers+doc.images), 'Hidden FAQ or image forbidden'
            assert [m.get('content') for m in doc.social if m.get('property')=='og:url'] == [ORIGIN+route], 'Exact og:url required'
            social={}
            for m in doc.social:
                key=m.get('property',m.get('name'));assert key not in social, 'Duplicate social metadata';social[key]=m.get('content')
            assert set(social)=={'og:type','og:locale','og:title','og:description','og:url','og:image','og:image:width','og:image:height','og:image:alt','twitter:card','twitter:title','twitter:description','twitter:image','twitter:image:alt'}, 'Exact social tag inventory required'
            assert social['og:type']=='website' and social['og:locale']=='ko_KR', 'Exact social type/locale required'
            assert social.get('og:image')==social.get('twitter:image')==ORIGIN+SOCIAL_IMAGE_PATH, 'Exact approved social image required'
            assert social.get('og:image:width')=='500' and social.get('og:image:height')=='500', 'Exact social image dimensions required'
            assert social.get('og:image:alt')==social.get('twitter:image:alt')==SOCIAL_IMAGE_ALT, 'Exact approved social alt required'
            assert social.get('twitter:card')=='summary', 'Twitter card required'
            assert social.get('twitter:title')==social.get('og:title') and social.get('twitter:description')==social.get('og:description'), 'Twitter reviewed title/description mismatch'
    assert inventory.get(SOCIAL_IMAGE_PATH.lstrip('/'))==SOCIAL_IMAGE_SHA256, 'Approved social image bytes changed'
    urls = reachable_sitemap_urls(dist, inventory)
    if mode['mode']=='production':
        assert proof==PROOF and proof['origin']==ORIGIN and re.fullmatch(r'/[0-9a-f]{32}\.txt',proof['path']), 'Exact dedicated Gurye proof required'
        name=proof['path'].lstrip('/')
        assert inventory[name]==proof['sha256'] and (dist/name).read_bytes()==(Path(name).stem+'\n').encode(), 'Dedicated proof bytes changed'
        assert indexnow_payload(urls,proof)['urlList']==urls, 'Sitemap and IndexNow URL set mismatch'
    else:assert proof is None, 'Offline inspection must contain no proof'
    assert (dist / 'robots.txt').read_text(encoding='utf-8') == 'User-agent: *\nAllow: /\nSitemap: ' + ORIGIN + '/sitemap-index.xml\n'
    assert (dist / '_headers').read_bytes() == b'/*\n', 'Exact empty response-header rules required'
    assert inventory==baseline()['files'], 'Exact independently rebuilt production15 bytes required'
    parity=equivalence(dist,mode['revision'])
    return {'state': 'production_artifact_contract_verified' if mode['mode']=='production' else 'offline_metadata_contract_verified', 'previewEquivalence':parity, 'publicHTTPVerified': False,
            'origin': ORIGIN, 'revision': mode['revision'], 'htmlFiles': 2, 'sitemapUrls': sorted(urls),
            'purchaseHomeCount': 1, 'facilityDetailCount': 0, 'supportCount': 0,
            'notFoundProbe': {'path': '/.gurye-release-missing-' + mode['revision'] + '/', 'expectedStatus': 404, 'bodySha256': inventory['404.html']},
            'files': inventory, 'indexNowProof':proof, 'indexNowStatus':'NOT_SUBMITTED', 'publishableArtifact':False}



if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--dist',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    assert re.fullmatch('[0-9a-f]{40}',a.revision), 'Full source revision required'
    result=inspect_dist(a.dist,dict(mode='production',indexable=True,origin=ORIGIN,revision=a.revision))
    print(json.dumps(result,sort_keys=True))
