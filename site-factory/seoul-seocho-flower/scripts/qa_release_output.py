"""Exact production output contract. This does not contact a public host."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET
from release_mode import release_mode

ORIGIN = 'https://seoul-seocho.fwith.kr'
ROUTES = ['/', '/regions/seocho-celebration-wreath/', '/regions/seocho-funeral-wreath/']
FILES = {'index.html': '/', 'regions/index.html': '/regions/', '404.html': '/404.html',
         'regions/seocho-celebration-wreath/index.html': ROUTES[1],
         'regions/seocho-funeral-wreath/index.html': ROUTES[2]}


class Metadata(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.robots, self.revisions, self.canonical, self.social, self.schemas = [], [], [], [], []
        self.h1 = 0
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
    assert len(urls) == 3 and set(urls) == {ORIGIN + path for path in ROUTES}, 'Exact three reachable sitemap URLs required'
    return urls


def inspect_dist(dist, mode, proof):
    dist = Path(dist)
    assert mode['mode'] == 'production' and mode['indexable'] is True and mode['origin'] == ORIGIN
    paths = [p for p in dist.rglob('*') if p.is_file()]
    assert not any(p.is_symlink() for p in dist.rglob('*')), 'Artifact symlink forbidden'
    inventory = {p.relative_to(dist).as_posix(): sha(p.read_bytes()) for p in paths}
    assert {name for name in inventory if name.endswith('.html')} == set(FILES), 'Exact five HTML files required'
    assert not any(Path(name).name in {'_worker.js', '_routes.json', '_redirects', 'package.json', 'package-lock.json'} for name in inventory), 'Executable or routing artifact forbidden'
    for filename, route in FILES.items():
        doc = Metadata((dist / filename).read_text(encoding='utf-8'))
        robots = 'noindex,nofollow,noarchive' if route == '/404.html' else 'noindex,follow' if route == '/regions/' else 'index,follow'
        assert doc.h1 == 1 and doc.revisions == [mode['revision']], 'Exact H1/revision required'
        assert doc.robots == [robots], 'Exact single robots meta required'
        assert doc.canonical == ([] if route == '/404.html' else [ORIGIN + route]), 'Exact single canonical required'
        if route == '/404.html': assert not doc.schemas and not doc.social, '404 schema/social forbidden'
    urls = reachable_sitemap_urls(dist, inventory)
    assert (dist / 'robots.txt').read_text(encoding='utf-8') == 'User-agent: *\nAllow: /\nSitemap: ' + ORIGIN + '/sitemap-index.xml\n'
    assert 'x-robots-tag:' not in (dist / '_headers').read_text(encoding='utf-8').lower(), 'Global response indexing override forbidden'
    assert proof['origin'] == ORIGIN
    name = proof['path'].lstrip('/')
    assert name in inventory and inventory[name] == proof['sha256'], 'Copied proof missing or changed'
    assert (dist / name).read_text(encoding='utf-8') == Path(name).stem, 'Copied proof body mismatch'
    return {'state': 'production_artifact_contract_verified', 'publicHTTPVerified': False,
            'origin': ORIGIN, 'revision': mode['revision'], 'htmlFiles': 5, 'sitemapUrls': sorted(urls),
            'thinDirectory': {'path': '/regions/', 'robots': 'noindex,follow', 'sitemapIncluded': False},
            'notFoundProbe': {'path': '/.seocho-release-missing-' + mode['revision'] + '/', 'expectedStatus': 404, 'bodySha256': inventory['404.html']},
            'files': inventory}


def main():
    root = Path.cwd()
    mode = release_mode(root)
    if mode['mode'] == 'preview':
        print('PRODUCTION OUTPUT GATE: preview mode; no publication claim')
        return
    binding = json.loads(Path(os.environ['SITE_RELEASE_BINDING_PATH']).read_text(encoding='utf-8'))
    report = inspect_dist(root / 'dist', mode, binding['proof'])
    Path('production-artifact-qa.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PRODUCTION OUTPUT GATE: 5 HTML files; 3 sitemap URLs; thin directory and real-404 expectations bound; public HTTP remains unverified')


if __name__ == '__main__':
    main()
