#!/usr/bin/env python3
"""Fail-closed Cloudflare publish verifier for the reviewed flower matrix A/B sites.

This script deliberately excludes IndexNow and search-engine submission.
It only supports the two fixed approved host/Worker identities below.
"""
import argparse, hashlib, json, os, re, time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urljoin, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
import xml.etree.ElementTree as ET

REPOSITORY="joseungil-kr/fwith-site-factory"
ZONE_NAME="fwith.kr"
TARGETS={
  "flower-a":{"hostname":"flower-a.fwith.kr","worker":"flower-matrix-a-prod","instance":"flower-a"},
  "flower-b":{"hostname":"flower-b.fwith.kr","worker":"flower-matrix-b-prod","instance":"flower-b"},
}
LIMIT=20*1024*1024

def require(v,code):
    if not v: raise ValueError(code)

def sha(data): return hashlib.sha256(data).hexdigest()

def save(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n")

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

class Page(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True)
        self.meta={};self.canonical=[];self.links=[];self.images=[];self.h1=0
        self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="meta":
            key=(a.get("name") or a.get("property") or "").lower()
            if key:self.meta[key]=a.get("content","")
        if tag=="link" and "canonical" in (a.get("rel") or "").lower().split():
            self.canonical.append(a.get("href",""))
        if tag=="a": self.links.append(a.get("href",""))
        if tag=="img": self.images.append(a)
        if tag=="h1": self.h1+=1

def target(key):
    require(key in TARGETS,"unknown_target")
    return TARGETS[key]

def transport_for(t):
    account=os.environ.get("CLOUDFLARE_ACCOUNT_ID","")
    token=os.environ.get("CLOUDFLARE_API_TOKEN","")
    require(re.fullmatch(r"[0-9A-Fa-f]{32}",account or ""),"invalid_account_configuration")
    require(bool(token),"missing_cloudflare_token")
    prefix=f"/accounts/{account}"
    reads={prefix,prefix+"/workers/scripts",prefix+"/workers/domains"}
    write=prefix+f"/workers/scripts/{t['worker']}/domains/records"
    opener=build_opener(NoRedirect())
    def transport(method,path,body=None):
        allowed=(method=="GET" and path in reads and body is None) or (
            method=="PUT" and path==write and body=={
              "override_scope":False,
              "override_existing_origin":False,
              "override_existing_dns_record":False,
              "origins":[{"hostname":t["hostname"],"zone_name":ZONE_NAME}],
            })
        require(allowed,"provider_operation_forbidden")
        req=Request("https://api.cloudflare.com/client/v4"+path,method=method,
                    data=None if body is None else json.dumps(body).encode(),
                    headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
        with opener.open(req,timeout=25) as response:
            status=response.status; raw=response.read(1024*1024+1)
        require(len(raw)<=1024*1024,"provider_response_limit")
        value=json.loads(raw)
        require(status==200 and isinstance(value,dict) and value.get("success") is True
                and value.get("errors") in ([],None),"provider_response_unverified")
        return value
    return account,transport

def list_result(transport,path):
    value=transport("GET",path)
    result=value.get("result")
    require(isinstance(result,list),"provider_inventory_not_list")
    # Existing account inventories are expected to fit the provider response used by
    # the established Site Factory direct publishers. Refuse ambiguous pagination.
    info=value.get("result_info")
    if isinstance(info,dict):
        require(info.get("total_pages",1) in (0,1,None),"provider_inventory_paginated")
    return result

def inspect_provider(key,stage):
    t=target(key); account,transport=transport_for(t); prefix=f"/accounts/{account}"
    acc=transport("GET",prefix)
    require(isinstance(acc.get("result"),dict) and acc["result"].get("id")==account,"account_identity_mismatch")
    scripts=list_result(transport,prefix+"/workers/scripts")
    script_names=[x.get("id") for x in scripts]
    require(all(isinstance(x,str) and x for x in script_names),"script_inventory_unverified")
    domains=list_result(transport,prefix+"/workers/domains")
    require(all(isinstance(x.get("hostname"),str) and isinstance(x.get("service"),str) for x in domains),"domain_inventory_unverified")
    relevant=[x for x in domains if x["hostname"].lower()==t["hostname"] or x["service"]==t["worker"]]
    exact=[x for x in relevant if x["hostname"].lower()==t["hostname"] and x["service"]==t["worker"]]
    require(not relevant or len(exact)==1 and len(relevant)==1,"hostname_or_worker_collision")
    worker_exists=t["worker"] in script_names
    bound=len(exact)==1
    if stage=="preflight":
        require(bound or not worker_exists,"unbound_existing_worker_requires_review")
    elif stage=="readback":
        require(worker_exists and bound,"exact_worker_hostname_binding_not_observed")
    return {"target":key,"state":"binding_verified" if bound else "target_absent_verified",
            "hostname":t["hostname"],"worker":t["worker"],"workerExists":worker_exists,
            "hostnameBindingExists":bound,"mutationsPerformed":False,"dnsState":"not_observed"}

def attach(key,before_path):
    t=target(key)
    before=json.loads(Path(before_path).read_text())
    require(before.get("target")==key and before.get("state")=="target_absent_verified"
            and before.get("workerExists") is False and before.get("hostnameBindingExists") is False,
            "exact_absent_preflight_required")
    account,transport=transport_for(t)
    path=f"/accounts/{account}/workers/scripts/{t['worker']}/domains/records"
    body={"override_scope":False,"override_existing_origin":False,"override_existing_dns_record":False,
          "origins":[{"hostname":t["hostname"],"zone_name":ZONE_NAME}]}
    try:
        value=transport("PUT",path,body)
    except HTTPError as e:
        if e.code==408 or e.code>=500: raise ValueError("attach_result_uncertain")
        raise ValueError("attach_http_error")
    require(value.get("success") is True,"attach_api_failure")
    return {"target":key,"state":"attach_request_accepted","hostname":t["hostname"],
            "worker":t["worker"],"mutationsPerformed":True,"liveVerification":"pending"}

def local_path(origin,url):
    u=urlsplit(urljoin(origin+"/",url))
    require(u.scheme=="https" and u.netloc==urlsplit(origin).netloc and not u.query and not u.fragment,"foreign_or_unsafe_url")
    p=unquote(u.path)
    require(p.startswith("/") and "//" not in p and "\\" not in p and not any(x in (".","..") for x in p.split("/")),"unsafe_path")
    return p

def expected_routes(root,origin):
    idx=ET.fromstring((root/"sitemap-index.xml").read_bytes())
    ns="{http://www.sitemaps.org/schemas/sitemap/0.9}"
    require(idx.tag==ns+"sitemapindex","wrong_sitemap_index")
    children=[x.text or "" for x in idx.findall(ns+"sitemap/"+ns+"loc")]
    require(children and len(children)==len(set(children)),"sitemap_children_invalid")
    urls=[]
    for u in children:
        p=local_path(origin,u).lstrip("/")
        require((root/p).is_file(),"missing_sitemap_child")
        doc=ET.fromstring((root/p).read_bytes())
        require(doc.tag==ns+"urlset","wrong_sitemap_child")
        urls += [x.text or "" for x in doc.findall(ns+"url/"+ns+"loc")]
    require(len(urls)==165 and len(set(urls))==165,"sitemap_url_count_not_165")
    return sorted(local_path(origin,u) for u in urls),sorted(local_path(origin,u) for u in children)

def get(origin,path,expected=None):
    req=Request(origin+quote(path,safe="/%-._~"),headers={"User-Agent":"SiteFactory-Flower-Matrix-Live-QA/1.0",
                                                         "Accept-Encoding":"identity","Cache-Control":"no-cache"})
    try: response=build_opener(NoRedirect()).open(req,timeout=25)
    except HTTPError as e: response=e
    with response:
        status=response.code; body=response.read(LIMIT+1); headers=response.headers
    require(len(body)<=LIMIT,"live_response_limit")
    if expected is not None: require(status==expected,"http_status_"+str(status))
    return status,body,headers

def verify_live(key,root_path,revision):
    t=target(key); origin="https://"+t["hostname"]; root=Path(root_path)
    require(re.fullmatch(r"[0-9a-f]{40}",revision or ""),"full_revision_required")
    require(root.is_dir(),"dist_missing")
    routes,sitemaps=expected_routes(root,origin)
    checked=0
    for route in routes:
        status,body,headers=get(origin,route,200)
        require((headers.get("Content-Type") or "").lower().startswith("text/html"),"html_content_type")
        doc=Page(body.decode("utf-8"))
        require(doc.h1==1,"live_h1_count")
        require(doc.canonical==[origin+route],"live_canonical_mismatch")
        require(doc.meta.get("og:url")==origin+route,"live_og_url_mismatch")
        require(doc.meta.get("robots")=="index,follow","live_meta_not_indexable")
        require(doc.meta.get("site-factory-revision")==revision,"live_revision_mismatch")
        require("tel:18440644" in doc.links and "https://fwith.co.kr" in doc.links,"live_cta_mismatch")
        require(not re.search(r"\b(noindex|nofollow|none)\b",",".join(headers.get_all("X-Robots-Tag",[])),re.I),"live_header_blocks_indexing")
        for img in doc.images:
            src=img.get("src","");require(src.startswith("/images/products/"),"live_nonlocal_product_image")
            require(img.get("alt","").strip() and img.get("width") and img.get("height"),"live_image_metadata_missing")
        checked+=1
    # Exact robots and sitemap public bytes.
    status,robots,_=get(origin,"/robots.txt",200)
    text=robots.decode("utf-8").replace("\\r\\n","\\n").strip()
    # Cloudflare may prepend its Managed Content Signals block at the edge.
    # Preserve a fail-closed search boundary: our exact production block must remain
    # intact, wildcard crawlers must never be denied, and the exact host sitemap
    # must be advertised. Provider-added rules for named AI/training bots are allowed.
    required_block="User-agent: *\\nAllow: /\\nSitemap: "+origin+"/sitemap-index.xml"
    require(required_block in text,"live_robots_required_block_missing")
    current_agents=[]
    for raw in text.splitlines():
        line=raw.split("#",1)[0].strip()
        if not line: continue
        name,sep,value=line.partition(":")
        if not sep: continue
        name=name.strip().lower();value=value.strip()
        if name=="user-agent":
            if not current_agents or any(a=="*" for a in current_agents):
                current_agents=[]
            current_agents.append(value.lower())
        elif name=="disallow" and "*" in current_agents:
            require(value not in ("/","/*"),"live_robots_wildcard_disallow")
    checked+=1
    for sm in ["/sitemap-index.xml",*sitemaps]:
        get(origin,sm,200); checked+=1
    # Verify all six local WebP assets actually load.
    for code in ["B205","C206","E008","F055","G067","G073"]:
        status,body,headers=get(origin,f"/images/products/{code}.webp",200)
        require((headers.get("Content-Type") or "").lower().startswith("image/webp"),"live_image_content_type")
        require(len(body)>1000,"live_image_too_small");checked+=1
    # Real unknown route must be a 404 using the non-indexable artifact.
    missing=f"/.flower-matrix-live-qa-missing-{revision}/"
    status,body,headers=get(origin,missing,404)
    doc=Page(body.decode("utf-8"))
    require(doc.h1==1 and "noindex" in doc.meta.get("robots","") and not doc.canonical,"live_404_contract")
    require(doc.meta.get("site-factory-revision")==revision,"live_404_revision")
    checked+=1
    return {"target":key,"state":"public_release_verified","origin":origin,"revision":revision,
            "sitemapUrl":origin+"/sitemap-index.xml","routes":len(routes),"checkedPaths":checked,
            "unknownStatus":404,"searchSubmissionPerformed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["preflight","attach","readback","http"])
    p.add_argument("--target",required=True,choices=sorted(TARGETS))
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--before")
    p.add_argument("--root")
    p.add_argument("--revision")
    a=p.parse_args()
    try:
        if a.mode=="preflight": result=inspect_provider(a.target,"preflight")
        elif a.mode=="attach": result=attach(a.target,a.before)
        elif a.mode=="readback": result=inspect_provider(a.target,"readback")
        else: result=verify_live(a.target,a.root,a.revision)
        save(a.report,result);print(json.dumps(result,ensure_ascii=False,sort_keys=True));return 0
    except Exception as e:
        code=str(e) if type(e) is ValueError and re.fullmatch(r"[A-Za-z0-9_]+",str(e)) else type(e).__name__
        result={"target":a.target,"state":"blocked_or_failed","mode":a.mode,"code":code}
        save(a.report,result);print(json.dumps(result,sort_keys=True));return 1
if __name__=="__main__": raise SystemExit(main())
