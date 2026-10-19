#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse
import hashlib,json,re,sys

class D(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True);self.canonical=[];self.meta={};self.visible=[];self.ignored=0;self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ("script","style"):self.ignored+=1
        if tag=="link" and a.get("rel")=="canonical":self.canonical.append(a.get("href",""))
        if tag=="meta":self.meta[a.get("name",a.get("property"))]=a.get("content","")
    def handle_endtag(self,tag):
        if tag in ("script","style"):self.ignored=max(0,self.ignored-1)
    def handle_data(self,data):
        if not self.ignored and data.strip():self.visible.append(re.sub(r"\s+"," ",data.strip()))

def files(root):
    return {p.relative_to(root).as_posix():p for p in root.rglob("*") if p.is_file()}

def main():
    a,b=Path(sys.argv[1]),Path(sys.argv[2]);oa=sys.argv[3].rstrip('/');ob=sys.argv[4].rstrip('/')
    fa,fb=files(a),files(b);assert set(fa)==set(fb),"A/B file sets differ"
    pages=[];same_visible=0
    for rel in sorted(x for x in fa if x.endswith(".html")):
        da,db=D(fa[rel].read_text()),D(fb[rel].read_text())
        if rel!="404.html":
            assert da.canonical and db.canonical,f"canonical missing {rel}"
            assert all(x.startswith(oa) for x in da.canonical),f"A canonical leak {rel}"
            assert all(x.startswith(ob) for x in db.canonical),f"B canonical leak {rel}"
            assert da.meta.get("og:url","").startswith(oa),f"A OG leak {rel}"
            assert db.meta.get("og:url","").startswith(ob),f"B OG leak {rel}"
        va="\n".join(da.visible);vb="\n".join(db.visible)
        if va==vb:same_visible+=1
        pages.append({"file":rel,"sameVisibleText":va==vb,"aCanonical":da.canonical,"bCanonical":db.canonical})
    result={"schemaVersion":1,"sameFileSet":True,"fileCount":len(fa),"htmlCount":len(pages),"sameVisibleTextHtml":same_visible,"pages":pages}
    Path("clone-compare.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(f'CLONE QA PASSED: files={len(fa)} html={len(pages)} same-visible={same_visible}')

if __name__=="__main__":main()
