"""Only reviewed reusable safety/capture primitives; unchanged extracted bodies.
See reuse-provenance.json. No historical source/build engines are copied.
"""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote
import hashlib, json

def digest(data): return hashlib.sha256(data).hexdigest()


def compact(value): return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def write_json(file, value):
    file = Path(file); file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


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


def settle(page):
    page.evaluate('() => document.fonts.ready')
    for image in page.locator('img').all(): image.scroll_into_view_if_needed()
    page.wait_for_function('() => [...document.images].every(i => i.complete && i.naturalWidth > 0)')
    page.evaluate('''async () => {
      await Promise.all([...document.images].map(i => i.decode()));
      window.scrollTo({top:0,left:0,behavior:'instant'});
      await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
    }''')
    page.wait_for_function('() => scrollX === 0 && scrollY === 0')


def center_in_safe_area(page, locator):
    # Scroll only. Never hide the native sticky header or CTA, rewrite CSS, or edit DOM.
    locator.evaluate(r'''el => {
      const r=el.getBoundingClientRect(),h=document.querySelector('.site-header'),b=document.querySelector('.mobile-bar');
      const visible=e=>!!e&&getComputedStyle(e).display!=='none';
      const top=visible(h)?h.getBoundingClientRect().height:0;
      const bottom=visible(b)?b.getBoundingClientRect().height:0;
      const room=innerHeight-top-bottom;
      window.scrollTo({top:scrollY+r.top-top-Math.max(8,(room-r.height)/2),behavior:'instant'});
    }''')
    page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')


