"""Exact production output contract. This does not contact a public host."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET

ORIGIN = 'https://yeosu.fwith.kr'
ROUTES = ['/', '/regions/yeosu-jeonnam-hospital-funeral-wreath/']
FILES = {'index.html':'/', 'regions/index.html':'/regions/', '404.html':'/404.html', **{route.strip('/')+'/index.html':route for route in ROUTES[1:]}}
PROOF = {'origin':ORIGIN,'path':'/39c4ed924bc6084c670a963c26d9f018.txt','sha256':'5da3864d5327c6e4e41e6eef12510004b2302f55c3bc61593d7d49c1797739b5'}


class Metadata(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.robots, self.revisions, self.canonical, self.social, self.schemas = [], [], [], [], []
        self.titles, self.descriptions = [], []
        self.in_title = False
        self.title_parts = []
        self.h1 = 0
        self.main_targets = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        assert len(values) == len(attrs), 'Duplicate HTML attribute'
        if tag == 'title':
            assert not self.in_title, 'Nested title forbidden'
            self.in_title = True
            self.title_parts = []
        if tag == 'meta':
            if values.get('name') == 'description': self.descriptions.append(values.get('content'))
            if values.get('name') == 'robots': self.robots.append(values.get('content'))
            if values.get('name') == 'site-factory-revision': self.revisions.append(values.get('content'))
            if any(values.get(attr, '').startswith(('og:', 'twitter:')) for attr in ('property','name')): self.social.append(values)
        if tag == 'link' and values.get('rel') == 'canonical': self.canonical.append(values.get('href'))
        if tag == 'script' and values.get('type') == 'application/ld+json': self.schemas.append(values)
        if tag == 'h1': self.h1 += 1
        if tag == 'main': self.main_targets.append(values)

    def handle_data(self, data):
        if self.in_title: self.title_parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'title' and self.in_title:
            self.titles.append(''.join(self.title_parts))
            self.in_title = False


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


def inspect_dist(dist, mode, proof=PROOF):
    dist = Path(dist)
    assert mode['mode'] == 'production' and mode['indexable'] is True and mode['origin'] == ORIGIN
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
            assert len(doc.titles) == 1 and bool(doc.titles[0]) and len(doc.descriptions) == 1 and bool(doc.descriptions[0]), 'Exact nonempty title/description required'
            expected = {'og:type':'website','og:title':doc.titles[0],'og:description':doc.descriptions[0],'og:locale':'ko_KR','og:url':ORIGIN+route,'og:image':ORIGIN+'/images/products/B201.jpg','og:image:alt':'근조 3단 화환 B201 샘플의 흰 꽃과 노란 꽃','twitter:card':'summary','twitter:title':doc.titles[0],'twitter:description':doc.descriptions[0],'twitter:image':ORIGIN+'/images/products/B201.jpg','twitter:image:alt':'근조 3단 화환 B201 샘플의 흰 꽃과 노란 꽃'}
            actual = {}
            for meta in doc.social:
                key = meta.get('property', meta.get('name', ''))
                assert key not in actual, 'Duplicate social metadata forbidden'
                assert set(meta) == {('property' if key.startswith('og:') else 'name'),'content'}, 'Exact social metadata attributes required'
                actual[key] = meta.get('content')
            assert actual == expected, 'Exact complete OG/Twitter metadata required'
            assert 'images/products/B201.jpg' in inventory, 'Existing local social image required; exact bytes are enforced by mandatory postbuild static equivalence'
    urls = reachable_sitemap_urls(dist, inventory)
    assert (dist / 'robots.txt').read_text(encoding='utf-8') == 'User-agent: *\nAllow: /\nSitemap: ' + ORIGIN + '/sitemap-index.xml\n'
    assert (dist / '_headers').read_bytes() == b'/*\n', 'Exact declared response headers required'
    assert proof == PROOF, 'Exact Yeosu existing proof binding required'
    name = proof['path'].lstrip('/')
    assert name in inventory and inventory[name] == proof['sha256'], 'Copied proof missing or changed'
    assert (dist / name).read_bytes() == (Path(name).stem + '\n').encode('utf-8'), 'Copied proof body mismatch'
    return {'state': 'production_artifact_contract_verified', 'publicHTTPVerified': False,
            'origin': ORIGIN, 'revision': mode['revision'], 'htmlFiles': 4, 'sitemapUrls': sorted(urls),
            'directory': {'path': '/regions/', 'robots': 'noindex,follow', 'sitemapIncluded': False},
            'notFoundProbe': {'path': '/.yeosu-release-missing-' + mode['revision'] + '/', 'expectedStatus': 404, 'bodySha256': inventory['404.html']},
            'files': inventory}



if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--dist',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    assert re.fullmatch('[0-9a-f]{40}',a.revision), 'Full source revision required'
    result=inspect_dist(a.dist,dict(mode='production',indexable=True,origin=ORIGIN,revision=a.revision))
    print(json.dumps(result,sort_keys=True))
