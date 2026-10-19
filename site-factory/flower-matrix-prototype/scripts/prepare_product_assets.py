#!/usr/bin/env python3
"""Fetch authorized fwith product images, preserve originals' SHA-256, and make local WebP assets."""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import hashlib, json, time
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parents[1]
UA="SiteFactory-ProductAssetBuilder/1.0"
ALLOWED_HOST="fwith.co.kr"

def fetch(url):
    parsed=urlparse(url)
    if parsed.scheme!="https" or parsed.hostname!=ALLOWED_HOST:
        raise ValueError("untrusted product image origin: "+url)
    last=None
    for attempt in range(3):
        try:
            req=Request(url,headers={"User-Agent":UA,"Accept":"image/*"})
            with urlopen(req,timeout=30) as response:
                status=response.status
                content_type=(response.headers.get("Content-Type") or "").split(";",1)[0].lower()
                data=response.read()
            if status!=200: raise RuntimeError("HTTP "+str(status)+" for "+url)
            if not content_type.startswith("image/"): raise RuntimeError("non-image response "+content_type+" for "+url)
            if len(data)<1000: raise RuntimeError("image response too small for "+url)
            return data,content_type
        except Exception as exc:
            last=exc
            if attempt<2: time.sleep(2*(attempt+1))
    raise last

def main():
    products=json.loads((ROOT/"src/data/product-sources.json").read_text())
    outdir=ROOT/"public/images/products"
    outdir.mkdir(parents=True,exist_ok=True)
    provenance={"schemaVersion":1,"assetPolicy":"authorized fwith source; no crop; max 1200px; WebP quality 86","products":[]}
    for p in products:
        url=p.get("sourceImageUrl","")
        if p.get("imageUrl")!=f'/images/products/{p["code"]}.webp':
            raise ValueError("local image path mismatch for "+p["code"])
        original,ctype=fetch(url)
        source_sha=hashlib.sha256(original).hexdigest()
        from io import BytesIO
        with Image.open(BytesIO(original)) as im:
            im.verify()
        with Image.open(BytesIO(original)) as im:
            im=ImageOps.exif_transpose(im)
            original_size=list(im.size)
            if im.width>1200 or im.height>1200:
                im.thumbnail((1200,1200),Image.Resampling.LANCZOS)
            if im.mode not in ("RGB","RGBA"):
                im=im.convert("RGBA" if "transparency" in im.info else "RGB")
            dest=outdir/(p["code"]+".webp")
            im.save(dest,"WEBP",quality=86,method=6)
            local_size=list(im.size)
        local=dest.read_bytes()
        provenance["products"].append({
            "code":p["code"],"name":p["name"],"sourceProductUrl":p["sourceUrl"],
            "sourceImageUrl":url,"sourceContentType":ctype,"sourceBytes":len(original),
            "sourceSha256":source_sha,"sourceDimensions":original_size,
            "localPath":"/images/products/"+p["code"]+".webp","localContentType":"image/webp",
            "localBytes":len(local),"localSha256":hashlib.sha256(local).hexdigest(),
            "localDimensions":local_size,"cropped":False,"webpQuality":86
        })
        print(f'ASSET {p["code"]}: source={len(original)}B sha256={source_sha} {original_size} -> local={len(local)}B sha256={hashlib.sha256(local).hexdigest()} {local_size}')
    report=ROOT/"product-image-provenance.json"
    report.write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+"\n")
    print("LOCAL PRODUCT ASSET PREPARATION PASSED: "+str(len(provenance["products"]))+" assets")

if __name__=="__main__":main()
