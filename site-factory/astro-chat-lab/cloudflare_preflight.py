#!/usr/bin/env python3
"""GET-only Cloudflare preflight for the already deployed isolated lab Worker."""
import json
import os
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser

ACCOUNT_ID=os.environ.get("CLOUDFLARE_ACCOUNT_ID","")
TOKEN=os.environ.get("CLOUDFLARE_API_TOKEN","")
WORKER="astro-chat-lab-qa"
assert ACCOUNT_ID and TOKEN, "Existing Cloudflare deploy secrets not configured"
BASE="https://api.cloudflare.com/client/v4/accounts/"+ACCOUNT_ID
HEADERS={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"}

def cloudflare(path, read_json=False):
    req=urllib.request.Request(BASE+path,headers=HEADERS,method="GET")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            if not read_json:
                return r.status, None
            return r.status,json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code,None
    except (urllib.error.URLError,TimeoutError) as e:
        raise SystemExit("BLOCKED: Cloudflare GET-only preflight network error") from e

status,response=cloudflare("/workers/subdomain",True)
if status!=200 or not response or response.get("success") is not True:
    raise SystemExit("BLOCKED: Cloudflare workers.dev subdomain GET failed HTTP "+str(status))
subdomain=response.get("result",{}).get("subdomain","")
assert re.fullmatch(r"[a-z0-9-]+",subdomain), "Invalid Cloudflare subdomain"
origin="https://"+WORKER+"."+subdomain+".workers.dev"
if origin!="https://astro-chat-lab-qa.joseungil.workers.dev":
    raise SystemExit("BLOCKED: Cloudflare account is not the proven experiment account")

status,_=cloudflare("/workers/scripts/"+WORKER)
if status not in (200,204):
    raise SystemExit("BLOCKED: Previously verified test Worker could not be read, HTTP "+str(status))

class Marker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="link" and a.get("rel")=="canonical":
            self.canonical.append(a.get("href",""))

try:
    req=urllib.request.Request(origin+"/",headers={"User-Agent":"AstroChatLab-BindingQA/2.0"})
    with urllib.request.urlopen(req,timeout=20) as response:
        assert response.status==200, "Unexpected target HTTP status"
        html=response.read().decode("utf-8",errors="replace")
except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
    raise SystemExit("BLOCKED: Public Worker binding cannot be independently verified") from e
page=Marker()
page.feed(html)
assert page.canonical==[origin+"/"], "BLOCKED: Existing Worker is not the proven lab identity"
assert "웹채팅 Astro 블로그 실험실" in html, "BLOCKED: Existing Worker identity marker mismatch"
assert "noindex" in html.lower(), "BLOCKED: Lab noindex missing"
for key,val in (("ASTRO_CHAT_SITE_URL",origin+"/"),("ASTRO_CHAT_ORIGIN",origin)):
    with open(os.environ["GITHUB_ENV"],"a",encoding="utf-8") as f:
        f.write(key+"="+val+"\n")
print("Existing isolated lab Worker binding independently verified by GET and public HTML")
print("Resolved public origin: "+origin)
