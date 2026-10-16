"""GET-only prior public-byte verifier, bounded reuse of the published Gwangsan verifier."""
import hashlib,json,re
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote,unquote,urlsplit
from urllib.request import Request,build_opener,HTTPRedirectHandler
import managed_robots
HOSTNAME='gwangju-gwangsan.fwith.kr';ORIGIN='https://'+HOSTNAME
PREVIOUS='654dafd7cafa4c6a158684ac4b304ceb7a5996b5'
REGION_ROUTES={'/regions/suwan-funeral-wreath/'};ARTICLE_ROUTES=REGION_ROUTES
THIN_HUB_ROUTES={'/regions/'};SITEMAP_ROUTES={'/'}|ARTICLE_ROUTES;ROUTES=SITEMAP_ROUTES|THIN_HUB_ROUTES
DEFERRED=[];LIMIT=20*1024*1024
PROOF_PATH='39c4ed924bc6084c670a963c26d9f018.txt'
def revision():return PREVIOUS


def expected_robots(route):
    if route == '/404.html':
        return {'noindex', 'follow'}
    return {'noindex', 'follow'} if route in THIN_HUB_ROUTES else {'index', 'follow'}


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def purchase_ctas_valid(page, route):
    if 'tel:18440644' not in page.links: return False
    if route in ('/','/regions/'): return '/regions/suwan-funeral-wreath/' in page.links
    if route in ARTICLE_ROUTES: return all('https://fwith.co.kr/shop/item.php?it_id='+sku in page.links for sku in ('B201','B203','B205','B060'))
    return False


def local_path(url):
    u = urlsplit(url)
    require(u.scheme == 'https' and u.netloc == HOSTNAME and not u.query and not u.fragment, 'foreign_canonical_or_asset')
    path = unquote(u.path)
    require(path.startswith('/') and not any(x in ('.', '..') for x in path.split('/'))
            and '//' not in path and '\\' not in path and not any(ord(c) < 32 for c in path), 'unsafe_path')
    return path


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.meta, self.canon, self.links, self.assets, self.images, self.og_urls = {}, [], [], set(), [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('name'):
            key = a['name'].lower()
            require(key not in self.meta, 'duplicate_metadata')
            self.meta[key] = a.get('content', '')
        if tag == 'meta' and a.get('property') == 'og:url':
            self.og_urls.append(a.get('content', ''))
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split():
            self.canon.append(a.get('href', ''))
        if tag == 'a':
            self.links.append(a.get('href', ''))
        if tag == 'img':
            self.images.append(a)
        if tag in ('img', 'script', 'source') and a.get('src'):
            self.assets.add(a['src'])
        if tag == 'link' and any(r in a.get('rel', '').split() for r in ('stylesheet', 'icon', 'preload', 'modulepreload')) and a.get('href'):
            self.assets.add(a['href'])


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def get(path, status=200):
    req = Request(ORIGIN + quote(path, safe='/%-._~'), headers={'User-Agent': 'Gwangsan-Direct-Release-QA/1.0',
                  'Accept-Encoding': 'identity', 'Cache-Control': 'no-cache'})
    try:
        response = build_opener(NoRedirect()).open(req, timeout=20)
    except HTTPError as error:
        response = error
    with response:
        require(response.code == status, 'http_status_' + str(response.code))
        body = response.read(LIMIT + 1)
        require(len(body) <= LIMIT, 'http_response_limit')
        return body, response.headers


def media_type(headers,file):
    allowed={'.html':{'text/html'},'.css':{'text/css'},'.svg':{'image/svg+xml'},'.jpg':{'image/jpeg'},'.jpeg':{'image/jpeg'},'.webp':{'image/webp'},'.xml':{'application/xml','text/xml'},'.txt':{'text/plain'}}
    values=headers.get_all('Content-Type',[]);require(len(values)==1,'single_public_media_type_required')
    raw=values[0];require(type(raw) is str and not any(ord(c)<32 or ord(c)==127 for c in raw),'public_media_type_control_bytes')
    value=raw.split(';',1)[0].strip().lower();require(value in allowed.get(Path(file).suffix,set()),'public_file_media_type_mismatch')
    require(bool(re.fullmatch(re.escape(value)+r'(?:; *charset=(?:utf-8|"utf-8"))?',raw.strip(),re.I)),'public_media_type_parameters_unsupported')
    require(headers.get('Content-Encoding','identity').lower()=='identity','public_content_encoding_unsupported')
    return value


def http_once(contract):
    checked = 0; normalized = 0; robots_evidence = None; observations=[]
    require(contract.get('origin') == ORIGIN and contract.get('revision') == revision() and contract.get('ownershipFile') == PROOF_PATH, 'http_contract_identity_mismatch')
    require(len(contract['pages']) == len(ROUTES) and {item['path'] for item in contract['pages']} == ROUTES,
            'http_contract_routes_mismatch')
    require(len(contract['sitemapUrls']) == len(SITEMAP_ROUTES) and
            {local_path(url) for url in contract['sitemapUrls']} == SITEMAP_ROUTES, 'http_contract_sitemap_mismatch')
    for item in contract['pages']:
        body, headers = get(item['path'])
        mime=media_type(headers,item['file']);raw_sha=sha(body)
        p = Page(body.decode('utf-8'))
        require(p.meta.get('site-factory-revision') == revision() and p.canon == [item['url']], 'live_revision_or_canonical_mismatch')
        require(p.og_urls == [item['url']], 'live_og_url_mismatch')
        require(set(item['robots']) == expected_robots(item['path']) and
                set(re.split(r'\s*,\s*', p.meta.get('robots', '').lower())) == expected_robots(item['path']), 'live_meta_robots_mismatch')
        require(not re.search(r'\b(noindex|nofollow|none)\b', ','.join(headers.get_all('X-Robots-Tag', [])), re.I), 'live_header_not_indexable')
        require(purchase_ctas_valid(p,item['path']), 'live_cta_mismatch')
        if sha(body) != contract['files'][item['file']]:
            body = strip_one_cf_beacon(body, contract['files'][item['file']]); normalized += 1
        require(sha(body) == contract['files'][item['file']], 'live_html_digest_mismatch')
        observations.append({'path':item['path'],'status':200,'mediaType':mime,'bodySHA256':raw_sha,'normalizedBodySHA256':sha(body)})
        checked += 1
    for path in sorted('/' + name for name in contract['files'] if not name.endswith('.html') and name != '_headers'):
        body, headers = get(path)
        mime=media_type(headers,path)
        if path == '/robots.txt':
            managed_robots.verify_headers(headers)
            robots_evidence = managed_robots.verify(body, contract['files']['robots.txt'], ORIGIN, contract['sitemapUrls'])
            Path('public-robots.txt').write_bytes(body)
            save(Path('public-robots-headers.json'), {k:v for k,v in headers.items() if k.lower() in ('content-type','x-robots-tag','cf-mitigated','content-length')})
        else:
            require(sha(body) == contract['files'][path.lstrip('/')], 'live_asset_digest_mismatch')
        observations.append({'path':path,'status':200,'mediaType':mime,'bodySHA256':sha(body)})
        checked += 1
    for path in [*DEFERRED, '/.gwangsan-release-missing-' + revision() + '/']:
        body, headers = get(path, 404)
        mime=media_type(headers,'404.html');raw_sha=sha(body)
        p = Page(body.decode('utf-8'))
        require(p.meta.get('site-factory-revision') == revision() and p.canon == [] and p.og_urls == [] and set(re.split(r'\s*,\s*', p.meta.get('robots','').lower())) == expected_robots('/404.html'), 'live_404_metadata_mismatch')
        if sha(body) != contract['files']['404.html']:
            body = strip_one_cf_beacon(body, contract['files']['404.html']); normalized += 1
        require(sha(body) == contract['files']['404.html'], 'live_404_digest_mismatch')
        observations.append({'path':path,'status':404,'mediaType':mime,'bodySHA256':raw_sha,'normalizedBodySHA256':sha(body)})
        checked += 1
    return dict(state='public_release_verified', revision=revision(), regionCount=len(REGION_ROUTES), articleCount=len(ARTICLE_ROUTES), htmlRoutes=len(ROUTES),
                noindexHubs=len(THIN_HUB_ROUTES), sitemapUrls=len(SITEMAP_ROUTES),
                checkedPaths=checked, normalizedCloudflareBeacons=normalized, unknownHttpStatus=404, robotsVerification=robots_evidence,observations=observations)


def strip_one_cf_beacon(body,expected_sha):
    # Latin-1 is lossless here: parser offsets remain exact byte offsets.
    text=body.decode('latin-1'); starts=[0]+[m.end() for m in re.finditer('\n',text)]
    class Beacon(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False); self.pending=None; self.spans=[]; self.markers=0
        def source_offset(self):
            line,column=self.getpos(); return starts[line-1]+column
        def handle_starttag(self,tag,attrs):
            if tag!='script': return
            values=dict(attrs); src=values.get('src') or ''; u=urlsplit(src)
            marker='data-cf-beacon' in values or u.hostname=='static.cloudflareinsights.com'
            if not marker: return
            self.markers+=1
            assert self.markers==1 and self.pending is None, 'multiple_404_beacon_markers'
            assert len(values)==len(attrs), 'duplicate_404_beacon_attributes'
            assert set(values)<={'src','defer','async','integrity','crossorigin','data-cf-beacon','type'}, 'unexpected_404_beacon_attribute'
            assert values.get('type') in (None,'','module'), 'wrong_404_beacon_type'
            assert 'data-cf-beacon' in values and u.scheme=='https' and u.netloc=='static.cloudflareinsights.com', 'wrong_404_beacon_identity'
            assert re.fullmatch(r'/beacon[.]min[.]js(?:/[A-Za-z0-9]+)?',u.path) and not u.query and not u.fragment, 'wrong_404_beacon_path'
            start=self.source_offset(); self.pending=(start,start+len(self.get_starttag_text()))
        def handle_startendtag(self,tag,attrs):
            self.handle_starttag(tag,attrs)
            assert self.pending is None, 'self_closing_404_beacon'
        def handle_endtag(self,tag):
            if tag!='script' or self.pending is None: return
            start,content_start=self.pending; end_start=self.source_offset()
            closing=re.match(r'</script\s*>',text[end_start:],re.I)
            assert closing and not text[content_start:end_start].strip(), 'nonempty_or_malformed_404_beacon'
            self.spans.append((start,end_start+closing.end())); self.pending=None
    parser=Beacon(); parser.feed(text); parser.close()
    assert parser.markers==1 and len(parser.spans)==1 and parser.pending is None, 'unverified_404_beacon'
    start,end=parser.spans[0]
    candidate=body[:start]+body[end:]
    if hashlib.sha256(candidate).hexdigest()==expected_sha: return candidate
    if body[end:end+1]==b'\n': candidate=body[:start]+body[end+1:]
    assert hashlib.sha256(candidate).hexdigest()==expected_sha, 'wrong_404_body'
    return candidate

