#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from PIL import Image
import hashlib, html, json, re, time

UA="SiteFactory-ProductAudit/1.0"
ROOT=Path(__file__).resolve().parents[1]

class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.text=[]
    def handle_data(self,data):
        if data.strip():self.text.append(data.strip())

def fetch(url,attempts=3):
    last=None
    for i in range(attempts):
        try:
            req=Request(url,headers={"User-Agent":UA,"Accept":"text/html,*/*;q=0.8"})
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
    provenance=json.loads((ROOT/"product-image-provenance.json").read_text())
    by_code={x["code"]:x for x in provenance["products"]}
    assert len(by_code)==len(products),"duplicate/missing product image provenance"
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
        image=p["imageUrl"];local=ROOT/"public"/image.lstrip("/")
        assert image==f'/images/products/{p["code"]}.webp',f'{p["code"]} must use local WebP'
        assert local.is_file(),f'{p["code"]} local image missing {local}'
        with Image.open(local) as im:
            im.verify()
        with Image.open(local) as im:
            width,height=im.size
            assert im.format=="WEBP",f'{p["code"]} is not WebP'
            assert width>0 and height>0 and width<=1200 and height<=1200,f'{p["code"]} invalid dimensions {width}x{height}'
        data=local.read_bytes();local_sha=hashlib.sha256(data).hexdigest()
        record=by_code[p["code"]]
        assert record["sourceImageUrl"]==p["sourceImageUrl"],f'{p["code"]} source URL mismatch'
        assert re.fullmatch(r'[0-9a-f]{64}',record["sourceSha256"]),f'{p["code"]} source SHA-256 missing'
        assert record["localSha256"]==local_sha,f'{p["code"]} local asset hash mismatch'
        assert record["localPath"]==image,f'{p["code"]} provenance local path mismatch'
        report["products"].append({
            "code":p["code"],"name":p["name"],"price":p["price"],"priceVerifiedAt":p["priceVerifiedAt"],
            "sourceUrl":p["sourceUrl"],"sourceImageUrl":p["sourceImageUrl"],
            "sourceImageSha256":record["sourceSha256"],"sourceImageBytes":record["sourceBytes"],
            "localImageUrl":image,"localImageSha256":local_sha,"localImageBytes":len(data),
            "width":width,"height":height,"contentType":"image/webp"
        })
    out=ROOT/"product-source-verification.json"
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("PRODUCT SOURCE QA PASSED: "+", ".join(x["code"] for x in report["products"]))

if __name__=="__main__":main()
