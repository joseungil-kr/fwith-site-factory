#!/usr/bin/env python3
from html.parser import HTMLParser
from urllib.parse import urlsplit,urlunsplit,quote,urljoin
from urllib.request import Request,urlopen
import hashlib,json,re

RAW=[
 "https://graduation.m-castle.co.kr/축하화환/2658.html",
 "https://order.m-castle.co.kr/축하화환/2658.html",
 "https://passion.m-castle.co.kr/축하화환/1286.html",
]
def safe_url(raw):
    p=urlsplit(raw);return urlunsplit((p.scheme,p.netloc,quote(p.path),p.query,p.fragment))
class Doc(HTMLParser):
    def __init__(self,text,base):
        super().__init__(convert_charrefs=True);self.base=base;self.title=[];self.in_title=False;self.ignored=0;self.visible=[];self.headings=[];self.capture=None;self.meta={};self.canonical=[];self.images=[];self.links=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ("script","style"):self.ignored+=1
        if tag=="title":self.in_title=True
        if re.fullmatch(r"h[1-6]",tag):self.capture=tag
        if tag=="meta":self.meta[a.get("name",a.get("property"))]=a.get("content","")
        if tag=="link" and a.get("rel")=="canonical":self.canonical.append(a.get("href",""))
        if tag=="img" and a.get("src"):self.images.append(urljoin(self.base,a["src"]))
        if tag=="a" and a.get("href"):self.links.append(urljoin(self.base,a["href"]))
    def handle_endtag(self,tag):
        if tag in ("script","style"):self.ignored=max(0,self.ignored-1)
        if tag=="title":self.in_title=False
        if self.capture==tag:self.capture=None
    def handle_data(self,data):
        s=re.sub(r"\s+"," ",data).strip()
        if not s:return
        if self.in_title:self.title.append(s)
        if self.capture:self.headings.append((self.capture,s))
        if not self.ignored:self.visible.append(s)
def main():
    rows=[]
    for raw in RAW:
        url=safe_url(raw)
        row={"requestedUrl":raw,"fetchUrl":url}
        try:
            req=Request(url,headers={"User-Agent":"SiteFactory-StructureResearch/1.0"})
            with urlopen(req,timeout=25) as r: body=r.read();row["status"]=r.status;row["finalUrl"]=r.geturl()
            d=Doc(body.decode("utf-8","replace"),row["finalUrl"])
            host=urlsplit(row["finalUrl"]).hostname
            internal=[x for x in d.links if urlsplit(x).hostname==host]
            row.update({
              "title":" ".join(d.title),"description":d.meta.get("description",""),"canonical":d.canonical,
              "headingCounts":{f"h{i}":sum(1 for h,_ in d.headings if h==f"h{i}") for i in range(1,7)},
              "imageCount":len(d.images),"imageHosts":sorted(set(filter(None,(urlsplit(x).hostname for x in d.images)))),
              "internalLinkCount":len(internal),"visibleTextLength":len("\n".join(d.visible)),
              "visibleTextSha256":hashlib.sha256("\n".join(d.visible).encode()).hexdigest(),
              "imageListSha256":hashlib.sha256("\n".join(d.images).encode()).hexdigest()
            })
        except Exception as e:row["error"]=type(e).__name__+":"+str(e)
        rows.append(row)
    by={(urlsplit(r.get("finalUrl") or r["fetchUrl"]).hostname,urlsplit(r["fetchUrl"]).path):r for r in rows}
    pair=[r for r in rows if "2658.html" in r["fetchUrl"]]
    comparison={
      "same2658PathAcrossSubdomains":len(pair)==2 and urlsplit(pair[0]["fetchUrl"]).path==urlsplit(pair[1]["fetchUrl"]).path,
      "same2658Title":len(pair)==2 and pair[0].get("title")==pair[1].get("title"),
      "same2658VisibleText":len(pair)==2 and pair[0].get("visibleTextSha256")==pair[1].get("visibleTextSha256"),
      "same2658Images":len(pair)==2 and pair[0].get("imageListSha256")==pair[1].get("imageListSha256")
    }
    out={"schemaVersion":1,"scope":"structure-only-no-copy","rows":rows,"comparison":comparison,"rankingCause":"unproven-hypothesis"}
    open("competitor-structure.json","w").write(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"rows":[{"url":r["requestedUrl"],"status":r.get("status"),"error":r.get("error"),"h1":r.get("headingCounts",{}).get("h1"),"images":r.get("imageCount"),"links":r.get("internalLinkCount")} for r in rows],"comparison":comparison},ensure_ascii=False))
if __name__=="__main__":main()
