#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import hashlib, html, json, re, time

UA="SiteFactory-ProductAudit/1.0"
ROOT=Path(__file__).resolve().parents[1]

class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.text=[];self.images=[]
    def handle_data(self,data):
        if data.strip():self.text.append(data.strip())
    def handle_starttag(self,tag,attrs):
        if tag=="img":
            a=dict(attrs);src=a.get("src")
            if src:self.images.append(src)

def fetch(url,attempts=3):
    last=None
    for i in range(attempts):
        try:
            req=Request(url,headers={"User-Agent":UA,"Accept":"text/html,image/*,*/*;q=0.8"})
            with urlopen(req,timeout=25) as r:
                return r.status,r.headers,r.read()
        except Exception as e:
            last=e
            if i+1<attempts:time.sleep(2*(i+1))
    raise last

def norm(s):
    return re.sub(r"\s+"," ",html.unescape(s)).strip()

def main():
    products=json.loads((ROOT/"src/data/product-sources.json").read_text())
    report={"schemaVersion":1,"products":[]}
    for p in products:
        status,headers,body=fetch(p["sourceUrl"])
        assert status==200,f'{p["code"]} product HTTP {status}'
        parser=P();parser.feed(body.decode("utf-8","replace"))
        text=norm(" ".join(parser.text))
        expected_price=f'{p["price"]:,}원'
        assert p["code"] in text,f'{p["code"]} code missing from source'
        assert p["name"] in text,f'{p["code"]} name missing from source'
        assert expected_price in text,f'{p["code"]} current price mismatch: expected {expected_price}'
        image=p["imageUrl"]
        if image.startswith("/"):
            local=ROOT/"public"/image.lstrip("/")
            assert local.is_file(),f'{p["code"]} local image missing {local}'
            data=local.read_bytes();ctype="local/"+local.suffix.lstrip(".")
        else:
            u=urlparse(image)
            assert u.scheme=="https" and u.hostname=="fwith.co.kr",f'{p["code"]} untrusted image host'
            assert p["code"] in u.path,f'{p["code"]} image URL is not code-bound'
            istatus,iheaders,data=fetch(image)
            assert istatus==200,f'{p["code"]} image HTTP {istatus}'
            ctype=(iheaders.get("Content-Type") or "").split(";",1)[0].lower()
            assert ctype.startswith("image/"),f'{p["code"]} image content-type {ctype}'
        assert len(data)>1000,f'{p["code"]} image too small'
        report["products"].append({
            "code":p["code"],"name":p["name"],"price":p["price"],"priceVerifiedAt":p["priceVerifiedAt"],
            "sourceUrl":p["sourceUrl"],"imageUrl":image,"imageContentType":ctype,
            "imageBytes":len(data),"imageSha256":hashlib.sha256(data).hexdigest()
        })
    out=ROOT/"product-source-verification.json"
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("PRODUCT SOURCE QA PASSED: "+", ".join(x["code"] for x in report["products"]))

if __name__=="__main__":main()
