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

status,headers,body=get("/health")
assert status in (200,503), "Unexpected OAuth health HTTP status"
data=json.loads(body)
assert data.get("service")=="astro-chat-lab-oauth-qa"
assert data.get("callback")==expected
assert data.get("configured") is (status==200)
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
