"""Exact production output contract. This does not contact a public host."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import html
import json
import os
import re
import xml.etree.ElementTree as ET

EQUIVALENCE_SHA='c670a86adbefd94df63e51b5572be1a467be09dd642659832e9f1116a83efdb7'
EQUIVALENCE_PATH=Path(__file__).resolve().parents[1]/'release/preview-equivalence.json'

ORIGIN = 'https://gwangju-gwangsan.fwith.kr'
SOCIAL_IMAGE_PATH='/images/products/B201.jpg'
SOCIAL_IMAGE_ALT='흰색과 노란색 꽃 위로 노란 장식이 놓인 B201 근조 3단 화환 상품사진'
SOCIAL_IMAGE_SHA256='7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3'
ROUTES = ['/', '/regions/suwan-funeral-wreath/']
FILES = {'index.html':'/', 'regions/index.html':'/regions/', '404.html':'/404.html', **{route.strip('/')+'/index.html':route for route in ROUTES[1:]}}
PROOF = {'origin':ORIGIN,'path':'/39c4ed924bc6084c670a963c26d9f018.txt','sha256':'5da3864d5327c6e4e41e6eef12510004b2302f55c3bc61593d7d49c1797739b5'}


class Metadata(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.robots, self.revisions, self.canonical, self.social, self.schemas = [], [], [], [], []
        self.h1 = 0
        self.main_targets = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        assert len(values) == len(attrs), 'Duplicate HTML attribute'
        if tag == 'meta':
            if values.get('name') == 'robots': self.robots.append(values.get('content'))
            if values.get('name') == 'site-factory-revision': self.revisions.append(values.get('content'))
            if values.get('property', values.get('name', '')).startswith(('og:', 'twitter:')): self.social.append(values)
        if tag == 'link' and values.get('rel') == 'canonical': self.canonical.append(values.get('href'))
        if tag == 'script' and values.get('type') == 'application/ld+json': self.schemas.append(values)
        if tag == 'h1': self.h1 += 1
        if tag == 'main': self.main_targets.append(values)


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
    assert len(urls) == 2 and set(urls) == {ORIGIN + path for path in ROUTES}, 'Exact two reachable sitemap URLs required'
    return urls


def baseline():
    raw=EQUIVALENCE_PATH.read_bytes()
    assert sha(raw)==EQUIVALENCE_SHA, 'Pinned equivalence baseline changed'
    result=json.loads(raw)
    assert result['allowedGeneratedBodyChanges']==[] and len(result['htmlBodies'])==4 and len(result['staticAssets'])==9
    assert set(result['htmlBodies'])==set(FILES)==set(result['htmlPrefixes'])
    return result


def transformed_prefix(before, route, revision):
    assert re.fullmatch('[0-9a-f]{40}',revision) or revision=='local-inspection', 'Actual source revision or explicit offline marker required'
    old='<meta name="robots" content="noindex,nofollow,noarchive">'
    assert before.count(old)==1 and 'rel="canonical"' not in before and 'site-factory-revision' not in before
    robots='index,follow' if route in ROUTES else 'noindex,follow'
    after=before.replace(old,f'<meta name="robots" content="{robots}"><meta name="site-factory-revision" content="{revision}">',1)
    if route=='/404.html': after=re.sub(r'<meta property="og:[^"]+" content="[^"]*">','',after)
    else:
        assert after.count('</head>')==1
        title=re.findall(r'<meta property="og:title" content="([^"]*)">',before)
        description=re.findall(r'<meta property="og:description" content="([^"]*)">',before)
        assert len(title)==len(description)==1, 'Exact reviewed OG title/description required'
        image=ORIGIN+SOCIAL_IMAGE_PATH
        alt=html.escape(SOCIAL_IMAGE_ALT,quote=True)
        social=(f'<meta property="og:image" content="{image}">'
                '<meta property="og:image:width" content="500">'
                '<meta property="og:image:height" content="500">'
                f'<meta property="og:image:alt" content="{alt}">'
                '<meta name="twitter:card" content="summary">'
                f'<meta name="twitter:title" content="{title[0]}">'
                f'<meta name="twitter:description" content="{description[0]}">'
                f'<meta name="twitter:image" content="{image}">'
                f'<meta name="twitter:image:alt" content="{alt}">')
        after=after.replace('</head>',f'<link rel="canonical" href="{ORIGIN+route}"><meta property="og:url" content="{ORIGIN+route}">'+social+'</head>',1)
    return after


def equivalence(dist,revision):
    expected=baseline();dist=Path(dist)
    for filename,route in FILES.items():
        raw=(dist/filename).read_bytes();start=raw.find(b'<body')
        assert start>=0 and sha(raw[start:])==expected['htmlBodies'][filename], 'Customer body changed: '+filename
        assert raw[:start].decode()==transformed_prefix(expected['htmlPrefixes'][filename],route,revision), 'Non-allowed head change: '+filename
    for name,digest in expected['staticAssets'].items():
        assert sha((dist/name).read_bytes())==digest, 'Static asset changed: '+name
    return {'htmlBodiesByteIdentical':4,'staticAssetsByteIdentical':9,'headChangesExactlyAllowed':4}


def inspect_dist(dist, mode, proof=PROOF):
    dist = Path(dist)
    assert mode['mode'] in {'production','offline-inspection'} and mode['indexable'] is True and mode['origin'] == ORIGIN
    assert (re.fullmatch('[0-9a-f]{40}',mode['revision']) if mode['mode']=='production' else mode['revision']=='local-inspection'), 'Offline marker cannot authorize production'
    paths = [p for p in dist.rglob('*') if p.is_file()]
    assert not any(p.is_symlink() for p in dist.rglob('*')), 'Artifact symlink forbidden'
    inventory = {p.relative_to(dist).as_posix(): sha(p.read_bytes()) for p in paths}
    assert {name for name in inventory if name.endswith('.html')} == set(FILES), 'Exact four HTML files required'
    assert len(inventory)==18, 'Exact 18 output files required'
    assert not any(Path(name).name in {'_worker.js', '_routes.json', '_redirects', 'package.json', 'package-lock.json'} for name in inventory), 'Executable or routing artifact forbidden'
    for filename, route in FILES.items():
        doc = Metadata((dist / filename).read_text(encoding='utf-8'))
        robots = 'noindex,follow' if route in {'/404.html','/regions/'} else 'index,follow'
        assert doc.h1 == 1 and doc.revisions == [mode['revision']], 'Exact H1/revision required'
        assert doc.main_targets == [{'id':'main-content','tabindex':'-1'}], 'Exact keyboard-focus main target required'
        assert doc.robots == [robots], 'Exact single robots meta required'
        assert doc.canonical == ([] if route == '/404.html' else [ORIGIN + route]), 'Exact single canonical required'
        if route == '/404.html': assert not doc.schemas and not doc.social, '404 schema/social forbidden'
        else:
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
    assert (dist / 'robots.txt').read_text(encoding='utf-8') == 'User-agent: *\nAllow: /\nSitemap: ' + ORIGIN + '/sitemap-index.xml\n'
    assert (dist / '_headers').read_bytes() == b'/*\n', 'Exact empty response-header rules required'
    assert proof == PROOF, 'Exact Gwangsan existing proof binding required'
    name = proof['path'].lstrip('/')
    assert name in inventory and inventory[name] == proof['sha256'], 'Copied proof missing or changed'
    assert (dist / name).read_bytes() == (Path(name).stem + '\n').encode('utf-8'), 'Copied proof body mismatch'
    parity=equivalence(dist,mode['revision'])
    return {'state': 'production_artifact_contract_verified' if mode['mode']=='production' else 'offline_metadata_contract_verified', 'previewEquivalence':parity, 'publicHTTPVerified': False,
            'origin': ORIGIN, 'revision': mode['revision'], 'htmlFiles': 4, 'sitemapUrls': sorted(urls),
            'directory': {'path': '/regions/', 'robots': 'noindex,follow', 'sitemapIncluded': False},
            'notFoundProbe': {'path': '/.gwangsan-release-missing-' + mode['revision'] + '/', 'expectedStatus': 404, 'bodySha256': inventory['404.html']},
            'files': inventory}



if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--dist',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    assert re.fullmatch('[0-9a-f]{40}',a.revision), 'Full source revision required'
    result=inspect_dist(a.dist,dict(mode='production',indexable=True,origin=ORIGIN,revision=a.revision))
    print(json.dumps(result,sort_keys=True))
