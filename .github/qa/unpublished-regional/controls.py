"""QA-only immutable source/artifact controls; no publication capability."""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote
import hashlib, json, os, re, subprocess, sys

HERE = Path(__file__).resolve().parent
BRANCH = 'refs/heads/qa/unpublished-regional-visual-20261012'
NATIVE_BLOB = '41ee8a757b7a742b6125ef15b5356e0eca47c01f'
VIEWPORTS = [(320, 740), (390, 844), (1280, 900)]

def digest(data): return hashlib.sha256(data).hexdigest()
def compact(value): return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
def write_json(file, value):
    file = Path(file); file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()
def spec_for(key): return json.loads((HERE/'sites.json').read_text())[key]
def safe_route(route): return bool(re.fullmatch(r'/(?:[a-z0-9-]+/)*|/404\.html', route))
def source_routes(site):
    return ['/', '/regions/'] + [p['url'] for p in json.loads((site/'src/data/pages.json').read_text())] + ['/404.html']

def verify_source(source, spec, pristine=False):
    assert git(source, 'rev-parse', 'HEAD') == spec['sourceSha'], 'Wrong source commit'
    assert git(source, 'rev-parse', 'HEAD^{tree}') == spec['repositoryTree'], 'Wrong repository tree'
    if pristine: assert not git(source, 'ls-files', '--others', '--exclude-standard'), 'Unexpected untracked checkout file'
    assert git(source, 'rev-parse', 'HEAD:'+spec['path']) == spec['sourceTree'], 'Wrong source tree'
    site = source/spec['path']
    assert git(source, 'rev-parse', 'HEAD:'+spec['path']+'/scripts/qa_browser_rendering.py') == NATIVE_BLOB, 'Native QA changed'
    # Check actual checkout bytes, not merely a commit label. Only the native generated
    # revision file may change after building; every guard/content/approval stays exact.
    changed = git(source, 'diff', '--name-only', 'HEAD', '--', spec['path']).splitlines()
    allowed = [] if pristine else [spec['path']+'/src/data/build-revision.json']
    assert all(x in allowed for x in changed), ('Source edits', changed)
    assert not git(source, 'diff', '--cached', '--name-only'), 'Staged source edit'
    for raw in subprocess.check_output(['git','-C',str(source),'ls-tree','-rz','HEAD',spec['path']]).split(b'\0'):
        if not raw: continue
        head, rel = raw.split(b'\t',1); mode, kind, blob = head.decode().split()
        assert kind == 'blob' and mode in ('100644','100755'), 'Source symlink/submodule forbidden'
        rel = rel.decode(); file = source/rel
        assert file.is_file() and not file.is_symlink(), rel
        if not pristine and rel in allowed: continue
        data = file.read_bytes()
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() == blob, rel
    config = json.loads((site/'src/data/site-config.json').read_text())
    assert config['productionApproved'] is spec['productionApproved'], 'Approval state changed'
    assert config['previewUrl'] == spec['siteUrl']
    assert source_routes(site) == spec['routes'], 'Unexpected route scope'
    assert all(safe_route(r) for r in spec['routes'])
    return site

def manifest(root):
    root = Path(root)
    assert root.is_dir() and not root.is_symlink(), 'Unsafe artifact root'
    result = {}
    for file in sorted(root.rglob('*')):
        assert not file.is_symlink(), 'Artifact symlink forbidden'
        if file.is_dir(): continue
        assert file.is_file(), 'Nonregular artifact'
        result[file.relative_to(root).as_posix()] = digest(file.read_bytes())
    assert result, 'Empty artifact'
    return result

def validate_build(site, spec):
    from html.parser import HTMLParser
    class Head(HTMLParser):
        def __init__(self): super().__init__(); self.robots=[]; self.revisions=[]; self.canonicals=[]
        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if tag == 'meta' and a.get('name') == 'robots': self.robots.append(a.get('content'))
            if tag == 'meta' and a.get('name') == 'site-factory-revision': self.revisions.append(a.get('content'))
            if tag == 'link' and a.get('rel') == 'canonical': self.canonicals.append(a.get('href'))
    dist = site/'dist'; files = manifest(dist)
    expected_html = sorted('404.html' if r=='/404.html' else r.lstrip('/')+'index.html' for r in spec['routes'])
    assert sorted(f for f in files if f.endswith('.html')) == expected_html, 'Unexpected HTML routes'
    for route, rel in [(r,'404.html' if r=='/404.html' else r.lstrip('/')+'index.html') for r in spec['routes']]:
        head=Head(); head.feed((dist/rel).read_text())
        assert head.revisions == [spec['sourceSha']], ('Wrong source revision',rel)
        expected_robots = 'index,follow' if spec['indexable'] and route != '/404.html' else 'noindex,nofollow,noarchive'
        assert head.robots == [expected_robots], (rel, head.robots)
        assert head.canonicals == ([] if route=='/404.html' else [spec['siteUrl']+route]), (rel,head.canonicals)
    import xml.etree.ElementTree as ET
    sitemap_urls=set()
    for name in files:
        if re.fullmatch(r'sitemap[^/]*\.xml',name):
            for loc in ET.parse(dist/name).iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
                if not (loc.text or '').endswith('.xml'): sitemap_urls.add(loc.text or '')
    # Preserve native source semantics. Guro deliberately retains its source URL
    # set even under noindex; Geumcheon's later native boundary emits none.
    assert sitemap_urls=={spec['siteUrl']+route for route in spec['sitemapRoutes']}, 'Native sitemap URL set differs'
    robots=(dist/'robots.txt').read_text();headers=(dist/'_headers').read_text()
    if spec['indexable']:
        assert 'Allow: /' in robots and 'Disallow: /' not in robots
        assert 'X-Robots-Tag: noindex, nofollow, noarchive' not in headers
    else:
        assert 'Disallow: /' in robots
        assert 'X-Robots-Tag: noindex, nofollow, noarchive' in headers
    return files

def resolve_request(root, request_path):
    root=Path(root)
    assert not root.is_symlink(), 'Symlink root'
    parsed=urlsplit(request_path)
    if parsed.scheme or parsed.netloc: raise ValueError('Absolute request URL forbidden')
    raw=unquote(parsed.path, errors='strict')
    if not raw.startswith('/') or '\\' in raw or '\x00' in raw: raise ValueError('Unsafe request path')
    parts=raw.split('/')
    if any(p in ('.','..') or p.startswith('.') for p in parts if p): raise ValueError('Dot path forbidden')
    file=root.joinpath(*[p for p in parts if p])
    cursor=root
    for part in file.relative_to(root).parts:
        cursor=cursor/part
        if cursor.is_symlink(): raise ValueError('Symlink forbidden')
    if file.is_dir(): file=file/'index.html'
    if file.is_symlink(): raise ValueError('Symlink index forbidden')
    if not file.is_file(): raise FileNotFoundError(raw)
    if not file.resolve().is_relative_to(root.resolve()): raise ValueError('Escaped root')
    return file

class SafeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        try: file=resolve_request(Path(self.directory),self.path)
        except FileNotFoundError: self.send_error(404); return None
        except (ValueError,AssertionError,UnicodeError): self.send_error(403); return None
        stream=file.open('rb'); self.send_response(200)
        self.send_header('Content-Type',self.guess_type(str(file)))
        self.send_header('Content-Length',str(file.stat().st_size))
        self.send_header('Cache-Control','no-store'); self.end_headers(); return stream
    def __getattr__(self, name):
        if name.startswith('do_'): return lambda: self.send_error(405,'Only GET/HEAD allowed')
        raise AttributeError(name)
    def log_message(self,*args): pass

class SafeServer(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,handler):
        assert address[0]=='127.0.0.1', 'Loopback binding only'
        super().__init__(address,handler)


def allowed_request(url, method, origin):
    try:
        u=urlsplit(url); o=urlsplit(origin)
        return method in ('GET','HEAD') and u.scheme=='http' and u.hostname=='127.0.0.1' and u.port==o.port and not u.username and not u.password and u.netloc==o.netloc
    except ValueError: return False

def jpeg_dimensions(data):
    assert data[:2]==b'\xff\xd8', 'Not JPEG'
    pos=2
    while pos<len(data):
        assert data[pos]==255, 'Malformed JPEG'
        while data[pos]==255: pos+=1
        marker=data[pos];pos+=1
        if marker in (0xd8,0xd9): continue
        length=int.from_bytes(data[pos:pos+2],'big')
        if marker in (0xc0,0xc1,0xc2):
            height=int.from_bytes(data[pos+3:pos+5],'big');width=int.from_bytes(data[pos+5:pos+7],'big')
            assert width>0 and height>0
            return {'width':width,'height':height}
        pos+=length
    raise AssertionError('JPEG dimensions missing')

def validate_branch(value):
    assert value==BRANCH, 'Unexpected QA branch'

def validate_capture_evidence(rows, spec, output):
    expected=[(route,w,h) for w,h in VIEWPORTS for route in spec['routes']]
    assert [(r['route'],r['width'],r['height']) for r in rows]==expected, 'Missing/duplicate/reordered capture grid'
    assert len({r.get('screenshot') for r in rows})==len(expected), 'Duplicate screenshot path'
    for row in rows:
        assert not row['issues'], 'Capture assertion failed'
        rel=row['screenshot']; assert rel.startswith('screenshots/') and '..' not in Path(rel).parts
        file=Path(output)/rel
        assert file.is_file() and not file.is_symlink(), 'Missing screenshot'
        assert digest(file.read_bytes())==row['screenshotSha256'], 'Screenshot hash mismatch'
        dimensions=jpeg_dimensions(file.read_bytes())
        assert dimensions==row['screenshotDimensions'] and dimensions['width']==row['width'] and dimensions['height']>=row['height'], 'Wrong screenshot dimensions'

def run_binding(spec, files):
    return {'sourceSha':spec['sourceSha'],'sourceTree':spec['sourceTree'],'repositoryTree':spec['repositoryTree'],'sitePath':spec['path'],
            'controlSha':os.environ['GITHUB_SHA'],'runId':os.environ['GITHUB_RUN_ID'],'runAttempt':os.environ['GITHUB_RUN_ATTEMPT'],
            'siteUrl':spec['siteUrl'],'indexable':spec['indexable'],'productionApprovedSourceFact':spec['productionApproved'],
            'nativeSitemapRoutes':spec['sitemapRoutes'],'buildManifestSha256':digest(compact(files)),'scope':'runner loopback only; no public site deployment',
            'pixelReview':'pending','publicationAuthorization':'not-issued'}

if __name__=='__main__':
    command,key=sys.argv[1:3]; spec=spec_for(key); source=Path(os.environ['SOURCE_ROOT']).resolve()
    if command=='evidence':
        output=Path(os.environ['EVIDENCE_ROOT'])
        files={f.relative_to(output).as_posix():digest(f.read_bytes()) for f in sorted(output.rglob('*')) if f.is_file() and f.name!='evidence-manifest.json'}
        write_json(output/'evidence-manifest.json',{'sourceSha':spec['sourceSha'],'sourceTree':spec['sourceTree'],'controlSha':os.environ['GITHUB_SHA'],'runId':os.environ['GITHUB_RUN_ID'],'runAttempt':os.environ['GITHUB_RUN_ATTEMPT'],'pixelReview':'pending','files':files})
        sys.exit(0)
    validate_branch(os.environ['GITHUB_REF'])
    assert os.environ['SITE_FACTORY_REVISION']==spec['sourceSha']
    assert os.environ['SITE_URL']==spec['siteUrl'] and os.environ['SITE_ORIGIN']==spec['siteUrl']
    assert os.environ['SITE_INDEXABLE']==str(spec['indexable']).lower()
    site=verify_source(source,spec,pristine=command=='source')
    if command=='source': write_json(Path(os.environ['EVIDENCE_ROOT'])/'source-readback.json', {'spec':spec,'nativeBlob':NATIVE_BLOB,'actualHead':git(source,'rev-parse','HEAD'),'checkoutBytesVerified':True})
    elif command=='manifest':
        files=validate_build(site,spec)
        Path(sys.argv[3]).write_bytes(compact(files))
    else: raise ValueError('Unknown command')
