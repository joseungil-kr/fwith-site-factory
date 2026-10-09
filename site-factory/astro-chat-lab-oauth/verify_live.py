#!/usr/bin/env python3
"""Live OAuth Worker smoke test; no GitHub OAuth credentials are read or logged."""
import json
import urllib.error
import urllib.request

base="https://astro-chat-lab-oauth-qa.joseungil.workers.dev"
expected=base+"/callback"

def get(path,method="GET"):
    req=urllib.request.Request(base+path,method=method,
        headers={"User-Agent":"AstroChatLab-OAuth-Smoke/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            return r.status,dict(r.headers),r.read()
    except urllib.error.HTTPError as e:
        return e.code,dict(e.headers),e.read()

import time

for attempt in range(1,13):
    status,headers,body=get("/health")
    print("OAuth public health attempt "+str(attempt)+": HTTP "+str(status))
    if status==200:
        try:
            data=json.loads(body)
            if data.get("service")=="astro-chat-lab-oauth-qa":
                break
        except ValueError:
            pass
    if attempt==12:
        raise SystemExit("OAuth credentials or Worker health not ready after deployment; last HTTP "+str(status))
    time.sleep(8)
assert data.get("service")=="astro-chat-lab-oauth-qa"
assert data.get("callback")==expected
assert status==200 and data.get("configured") is True, "OAuth secrets and Dashboard variables must be preserved on deploy"
assert "no-store" in headers.get("Cache-Control","")
assert "noindex" in headers.get("X-Robots-Tag","")
assert "Access-Control-Allow-Origin" not in headers
unknown,_,_=get("/nonexistent-auth-worker-path")
assert unknown==404
wrongmethod,_,_=get("/auth",method="POST")
assert wrongmethod==405
if not data.get("configured"):
    unconfigured,_,_=get("/auth?provider=github&site_id=astro-chat-lab-qa.joseungil.workers.dev&scope=public_repo")
    assert unconfigured==503, "Missing secrets must fail closed"
    unauthcallback,_,_=get("/callback?provider=github&code=fakecode&state=fakestate")
    assert unauthcallback==503, "Missing secrets must fail closed"
else:
    missing,_,_=get("/callback?code=fake&state=invalid")
    assert missing==400
print(json.dumps({"result":"PASS","service":data["service"],"health":status,
    "configured":data["configured"],"unknownRoute":unknown,"nonGet":wrongmethod,
    "callback":expected,"oauthLogin":"not tested; requires GitHub OAuth App and real browser"}))
