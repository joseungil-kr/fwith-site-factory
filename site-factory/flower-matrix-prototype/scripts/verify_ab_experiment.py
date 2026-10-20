#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
import json, re, sys

PREFIX="받는 곳의 정확한 주소와 수령자·희망시간을 먼저 준비해 주세요. "

class Page(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.title="";self.in_title=False;self.in_body=False;self.ignore=0;self.body=[]
        self.meta={};self.canonical=[];self.images=[];self.codes=[]
        self.feed(raw)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="title":self.in_title=True
        if tag=="body":self.in_body=True
        if tag in ("script","style"):self.ignore+=1
        if tag=="meta":self.meta[a.get("name",a.get("property"))]=a.get("content","")
        if tag=="link" and a.get("rel")=="canonical":self.canonical.append(a.get("href",""))
        if tag=="img":self.images.append(a)
        if tag=="article" and a.get("data-source-code"):self.codes.append(a["data-source-code"])
    def handle_endtag(self,tag):
        if tag=="title":self.in_title=False
        if tag=="body":self.in_body=False
        if tag in ("script","style"):self.ignore=max(0,self.ignore-1)
    def handle_data(self,data):
        value=re.sub(r"\s+"," ",data).strip()
        if not value:return
        if self.in_title:self.title+=value
        if self.in_body and not self.ignore:self.body.append(value)

def collect(root):
    return {p.relative_to(root).as_posix():p for p in root.rglob("*") if p.is_file()}

def main():
    if len(sys.argv) not in (5,6):raise SystemExit("usage: verify_ab_experiment.py DIST_A DIST_B ORIGIN_A ORIGIN_B [--indexable]")
    indexable=len(sys.argv)==6 and sys.argv[5]=="--indexable"
    if len(sys.argv)==6 and not indexable:raise SystemExit("unknown mode")
    da,db=Path(sys.argv[1]),Path(sys.argv[2]);oa=sys.argv[3].rstrip("/");ob=sys.argv[4].rstrip("/")
    data=json.loads(Path("src/data/regions-matrix.json").read_text())
    instances=json.loads(Path("src/data/site-instances.json").read_text())
    groups=json.loads(Path("src/data/product-groups.json").read_text())
    a=next(x for x in instances if x["key"]=="flower-a");b=next(x for x in instances if x["key"]=="flower-b")
    assert a["enabledRegions"]==b["enabledRegions"] and len(a["enabledRegions"])==32
    assert a["enabledProductGroups"]==b["enabledProductGroups"] and len(groups)==4
    controls=set(b["controlRegionKeys"]);assert controls==set(a["controlRegionKeys"]) and len(controls)==5
    routes={"/"}
    routes.update("/"+r["slug"]+"/" for r in data if r["key"] in a["enabledRegions"])
    routes.update("/products/"+g["slug"]+"/" for g in groups)
    routes.update("/"+r["slug"]+"/"+g["slug"]+"/" for r in data for g in groups if r["key"] in a["enabledRegions"])
    assert len(routes)==165,len(routes)
    fa,fb=collect(da),collect(db);assert set(fa)==set(fb),"A/B artifact file set differs"
    controls_checked=0;treatments_checked=0
    for route in sorted(routes):
        rel="index.html" if route=="/" else route.strip("/")+"/index.html"
        pa=da/rel;pb=db/rel
        assert pa.is_file() and pb.is_file(),f"missing route {route}"
        A=Page(pa.read_text());B=Page(pb.read_text())
        assert A.canonical==[oa+route],f"A canonical mismatch {route}: {A.canonical}"
        assert B.canonical==[ob+route],f"B canonical mismatch {route}: {B.canonical}"
        assert A.meta.get("og:url")==oa+route and B.meta.get("og:url")==ob+route,f"OG origin mismatch {route}"
        expected_robots="index,follow" if indexable else "noindex,nofollow,noarchive"
        assert A.meta.get("robots")==expected_robots and B.meta.get("robots")==expected_robots,"A/B robots mode mismatch"
        assert A.title==B.title,f"title changed in B variant {route}"
        assert A.meta.get("description")==B.meta.get("description"),f"meta description changed in B variant {route}"
        assert len(A.images)>0 and len(B.images)>0,f"no images {route}"
        for image in A.images+B.images:
            assert image.get("alt","").strip(),f"missing image alt {route}"
            assert image.get("width") and image.get("height"),f"missing image dimensions {route}"
            src=image.get("src","")
            assert src.startswith("/images/products/"),f"not using local product image {route}: {src}"
        textA=" ".join(A.body);textB=" ".join(B.body)
        parts=route.strip("/").split("/") if route!="/" else []
        if len(parts)==2 and parts[0]!="products":
            region=parts[0]
            region_obj=next(x for x in data if x["slug"]==region)
            if region_obj["key"] in controls:
                assert textA==textB,f"control detail changed {route}"
                controls_checked+=1
            else:
                assert PREFIX in textB,f"B treatment prefix missing {route}"
                normalized=textB.replace(PREFIX,"",1).strip()
                assert normalized==textA,f"B changed content outside first answer {route}"
                treatments_checked+=1
        else:
            assert textA==textB,f"non-detail control page differs {route}"
    assert controls_checked==20,controls_checked
    assert treatments_checked==108,treatments_checked
    for root,origin in ((da,oa),(db,ob)):
        robots=(root/"robots.txt").read_text().strip()
        headers=(root/"_headers").read_text()
        if indexable:
            assert robots==f"User-agent: *\nAllow: /\nSitemap: {origin}/sitemap-index.xml",f"Production robots mismatch {root}"
            assert "X-Robots-Tag: noindex" not in headers,f"Production headers block indexing {root}"
        else:
            assert robots=="User-agent: *\nDisallow: /",f"Preview robots mismatch {root}"
            assert "X-Robots-Tag: noindex, nofollow, noarchive" in headers,f"Preview header missing noindex {root}"
    result={"status":"PASS","routes":165,"regions":32,"productGroups":4,"controlDetailPages":controls_checked,"variantDetailPages":treatments_checked,"aOrigin":oa,"bOrigin":ob,"pricingPolicyInvariant":True,"variantScope":"one first-answer prefix only","indexable":indexable,"noindexPreview":not indexable,"fileCount":len(fa)}
    Path("ab-experiment-qa.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
