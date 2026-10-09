#!/usr/bin/env python3
"""Derive public/draft QA from the actual source posts; no fixed title/count."""
from datetime import datetime, timedelta, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, urlopen
import json
import os
import re
import sys
import time

MODE = sys.argv[1]
ROOT = Path("site-factory/astro-chat-lab")
DIST = ROOT / "dist"
ORIGIN = os.environ.get("ASTRO_CHAT_ORIGIN", "").rstrip("/")
assert re.fullmatch(r"https://astro-chat-lab-qa\.[a-z0-9-]+\.workers\.dev", ORIGIN)
POST_ROOT = ROOT / "src/content/posts"
assert (POST_ROOT/"webchat-astro-first-post.md").is_file(), "Original test post must be preserved"

def compact(text):
    return re.sub(r"\s+", "", unescape(text))

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical=[]
        self.robots=[]
        self.h1=[]
        self.h2=[]
        self.links=[]
        self.assets=[]
        self.images=[]
        self.article=[]
        self.in_h1=False
        self.in_h2=False
        self.in_article=False
        self.heading=""
        self.subheading=""
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="link" and "canonical" in a.get("rel","").split():
            self.canonical.append(a.get("href",""))
        if tag=="meta" and a.get("name","").lower()=="robots":
            self.robots.append(a.get("content",""))
        if tag=="h1": self.in_h1=True; self.heading=""
        if tag=="h2": self.in_h2=True; self.subheading=""
        if tag=="a" and a.get("href"): self.links.append(a["href"])
        if tag=="article" and a.get("id")=="article": self.in_article=True
        if tag=="img" and self.in_article: self.images.append(a.get("src",""))
        if tag in ("link","script"):
            uri=a.get("href") if tag=="link" else a.get("src")
            if uri and urlsplit(uri).path.startswith("/_astro/"):
                self.assets.append(urlsplit(uri).path)
    def handle_endtag(self,tag):
        if tag=="h1": self.h1.append(self.heading); self.in_h1=False
        if tag=="h2": self.h2.append(self.subheading); self.in_h2=False
        if tag=="article": self.in_article=False
    def handle_data(self,txt):
        if self.in_h1: self.heading+=txt
        if self.in_h2: self.subheading+=txt
        if self.in_article: self.article.append(txt)

def inspect(html,path):
    page=Page();page.feed(html)
    assert len(page.canonical)==1, f"canonical missing/duplicated at {path}"
    canon=urlsplit(page.canonical[0])
    assert canon.scheme=="https" and canon.netloc==urlsplit(ORIGIN).netloc
    assert unquote(canon.path).rstrip("/")==path.rstrip("/"), f"Wrong canonical {page.canonical} for {path}"
    assert len(page.robots)==1
    assert {"noindex","nofollow"}.issubset({v.strip().lower() for v in page.robots[0].split(",")})
    assert page.h1 and page.assets, f"Missing title or compiled assets at {path}"
    return page

def metadata(file):
    txt=file.read_text(encoding="utf-8").replace("\r\n","\n")
    m=re.match(r"\A---\n(.*?)\n---\n(.*)\Z",txt,re.S)
    assert m, "No frontmatter in "+str(file)
    head,body=m.groups()
    def field(name,default=None):
        mm=re.search(r"^"+re.escape(name)+r":\s*(.*?)\s*$",head,re.M)
        if not mm:return default
        val=mm.group(1).strip()
        if val.startswith('"') and val.endswith('"'):
            try: return json.loads(val)
            except ValueError:return val[1:-1]
        if val.startswith("'") and val.endswith("'"):
            return val[1:-1].replace("''","'")
        return val
    title=field("title")
    draft=str(field("draft","false")).lower()
    assert isinstance(title,str) and title.strip() and draft in ("true","false")
    pub=field("pubDatetime")
    assert isinstance(pub,str) and pub
    try: date=datetime.fromisoformat(pub.replace("Z","+00:00"))
    except ValueError as ex: raise AssertionError(f"Invalid publication date: {file}") from ex
    assert date.tzinfo is not None, "Publication dates must include timezone"
    return dict(path="/posts/"+file.stem+"/",title=title,body=body,
                published=(draft!="true" and date<=datetime.now(timezone.utc)+timedelta(minutes=15)))

def load_posts():
    files=sorted(p for p in POST_ROOT.rglob("*") if p.suffix in (".md",".mdx")
        and not any(part.startswith("_") for part in p.relative_to(POST_ROOT).parts))
    assert files and all(p.parent==POST_ROOT for p in files), "Unrecognized CMS post location"
    posts=[metadata(f) for f in files]
    assert len(posts)==len({p["path"] for p in posts}), "Duplicate post routes"
    return posts

def check_post(html,meta):
    page=inspect(html,meta["path"])
    assert len(page.h1)==1 and compact(page.h1[0])==compact(meta["title"]), "H1 title mismatch"
    article=compact("".join(page.article))
    assert article or page.images, "Published article must contain text or image"
    for heading in re.findall(r"^##\s+(.+)$",meta["body"],re.M):
        clean=re.sub(r"[\*_]","",heading)
        assert any(compact(x)==compact(clean) for x in page.h2), "CMS heading missing in HTML"
    candidates=matched=0
    for line in meta["body"].splitlines():
        line=line.strip()
        if not line or line.startswith((chr(96)*3,"~~~","![","|")):
            continue
        # Strip headings and bullets before comparing short Markdown texts.
        line=re.sub(r"^#{1,6}\s+","",line)
        line=re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+)","",line)
        cleaned=re.sub(r"\[([^\]]+)\]\([^)]+\)",r"\1",line)
        cleaned=re.sub(r"[\*_\\]","",cleaned).replace(chr(96),"")
        text=compact(cleaned)
        if len(text)>=2:
            candidates+=1
            if text[:min(24,len(text))] in article:
                matched+=1
    # Short text such as '본문테스트' is a valid CMS article. Empty text
    # remains invalid; image-only content requires an actual image.
    assert (candidates>0 and matched>=max(1,(candidates+1)//2)) or (
        candidates==0 and bool(page.images)
    ), f"Insufficient body parity: {matched}/{candidates} source excerpts"
    uploads=[]
    for raw in page.images:
        uri=urlsplit(raw)
        if uri.netloc or uri.scheme:continue
        img=unquote(uri.path)
        if img.startswith("/uploads/"):
            assert ".." not in img.split("/") and (DIST/img.lstrip("/")).is_file(), "Uploaded image missing"
            uploads.append(img)
    return page,uploads

def check_build(posts):
    assert (DIST/"index.html").is_file() and (DIST/"404.html").is_file()
    home=(DIST/"index.html").read_text(encoding="utf-8")
    hp=inspect(home,"/")
    assert "웹채팅 Astro 블로그 실험실" in home
    expected={p["path"] for p in posts if p["published"]}
    assert expected, "No public article; original post should remain available"
    real=set()
    for f in (DIST/"posts").rglob("index.html"):
        parent=f.parent.relative_to(DIST).as_posix()
        if parent=="posts" or re.fullmatch(r"posts/\d+",parent):continue
        real.add("/"+parent+"/")
    assert real==expected, f"Draft/unexpected routes in dist: {real ^ expected}"
    listings=[home]
    for f in (DIST/"posts").rglob("index.html"):
        parent=f.parent.relative_to(DIST).as_posix()
        if parent=="posts" or re.fullmatch(r"posts/\d+",parent):
            listings.append(f.read_text(encoding="utf-8"))
    hrefs=set()
    for html in listings:
        page=Page();page.feed(html)
        hrefs.update(unquote(urlsplit(x).path).rstrip("/") for x in page.links)
    assets=set(hp.assets)
    images=set()
    for p in posts:
        path=DIST/p["path"].lstrip("/")/"index.html"
        if p["published"]:
            assert path.is_file() and p["path"].rstrip("/") in hrefs, "Article absent from listing"
            page,uploaded=check_post(path.read_text(encoding="utf-8"),p)
            assets.update(page.assets);images.update(uploaded)
        else:
            assert not path.exists(), "Draft/future post incorrectly emitted"
    for asset in assets:
        assert (DIST/asset.lstrip("/")).is_file(), "Missing asset "+asset
    # Verify every uploaded image is copied into dist, including draft media.
    uploads=[]
    upload_dir=ROOT/"public/uploads"
    for f in sorted(upload_dir.rglob("*")):
        if not f.is_file() or f.name.startswith("."):
            continue
        rel=f.relative_to(upload_dir)
        dest=DIST/"uploads"/rel
        assert dest.is_file() and dest.stat().st_size==f.stat().st_size, "CMS media missing or mismatched: "+str(rel)
        uploads.append("/uploads/"+rel.as_posix())
    robots=(DIST/"robots.txt").read_text(encoding="utf-8")
    assert "Disallow: /" in robots and "Allow: /" not in robots
    admin=(DIST/"admin/index.html")
    config=(DIST/"admin/config.yml")
    assert admin.is_file() and config.is_file(), "Admin files not copied to static dist"
    admin_html=admin.read_text(encoding="utf-8")
    cfg=config.read_text(encoding="utf-8")
    for marker in ["decap-cms@3.16.3/dist/decap-cms.js",
                    'name="robots" content="noindex, nofollow"']:
        assert marker in admin_html, "Admin HTML safety marker missing: "+marker
    for marker in ["name: github","repo: joseungil-kr/fwith-site-factory",
        "branch: astro-chat-lab","auth_scope: public_repo",
        'folder: "site-factory/astro-chat-lab/src/content/posts"',
        'media_folder: "site-factory/astro-chat-lab/public/uploads"',
        'public_folder: "/uploads"']:
        assert marker in cfg, "CMS config missing: "+marker
    assert re.search(r'(?m)^\s*name: "body"\s*\n\s*widget: "richtext"\s*$',cfg), "Decap Rich Text body widget not active"
    gated="CMS_MANUAL_INIT = true" in admin_html
    assert not gated, "Decap CMS still gated after verified OAuth configuration"
    assert "oauth-approval-pending" not in admin_html, "Old pre-auth placeholder still deployed"
    assert re.search(r"^\s*base_url: https://astro-chat-lab-oauth-qa\.joseungil\.workers\.dev\s*$",cfg,re.M), "Incorrect auth Worker base_url"
    assert re.search(r"^\s*auth_endpoint: auth\s*$",cfg,re.M), "Incorrect OAuth endpoint"
    return dict(published=sorted(expected),unpublished=sorted(p["path"] for p in posts if not p["published"]),
        assets=sorted(assets),images=sorted(images),uploads=sorted(uploads),adminGated=gated)

def http(path,binary=False):
    req=Request(ORIGIN+quote(path,safe="/-._~%"),headers={"User-Agent":"AstroChatLab-CMS-QA/2.0"})
    try:
        with urlopen(req,timeout=20) as resp:
            return resp.status, resp.read() if binary else resp.read().decode("utf-8",errors="replace")
    except HTTPError as e:
        return e.code, e.read() if binary else e.read().decode("utf-8",errors="replace")

def check_live(posts,inventory):
    status,home=http("/")
    assert status==200
    inspect(home,"/")
    for p in posts:
        status,body=http(p["path"])
        if p["published"]:
            assert status==200, "Public article HTTP error "+p["path"]+" "+str(status)
            check_post(body,p)
        else:
            assert status==404, "Draft article leaked publicly: "+p["path"]
    for file in inventory["assets"]+inventory["images"]+inventory["uploads"]:
        status,_=http(file,binary=True)
        assert status==200, "Public asset HTTP error "+file
    for file in ("/admin/","/admin/config.yml"):
        status,body=http(file)
        assert status==200, "Admin static asset HTTP error "+file
        if file=="/admin/":
            assert "decap-cms@3.16.3/dist/decap-cms.js" in body, "Pinned Decap script absent in live HTML"
            assert "CMS_MANUAL_INIT" not in body, "CMS not active in live HTML"
            assert 'name="robots" content="noindex, nofollow"' in body, "Admin noindex missing"
        else:
            assert "base_url: https://astro-chat-lab-oauth-qa.joseungil.workers.dev" in body, "Live config has wrong auth base_url"
            assert "auth_endpoint: auth" in body and "auth_scope: public_repo" in body, "Live OAuth config incomplete"
    status,robots=http("/robots.txt")
    assert status==200 and "Disallow: /" in robots
    status,_=http("/missing-cms-test-20261009/")
    assert status==404, "Unknown route must return HTTP 404"
    print(json.dumps({"phase":"public-http","result":"PASS","origin":ORIGIN,**inventory,
          "robots":200,"unknown":404},ensure_ascii=False))

posts=load_posts()
inventory=check_build(posts)
if MODE=="build":
    print(json.dumps({"phase":"build","result":"PASS",**inventory},ensure_ascii=False))
elif MODE=="live":
    for attempt in range(1,7):
        try:
            check_live(posts,inventory);break
        except (AssertionError,URLError,TimeoutError) as e:
            if attempt==6: raise SystemExit("Public QA failed: "+str(e))
            time.sleep(8)
else:raise SystemExit("Usage: qa.py build|live")
