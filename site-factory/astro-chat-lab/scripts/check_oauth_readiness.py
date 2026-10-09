#!/usr/bin/env python3
"""Fail closed before activating static Decap: test REAL deployed auth Worker.

No credentials are read here. This only checks public, non-sensitive OAuth
endpoints and rejects broad scopes. Never follows the GitHub authorization
redirect or prints OAuth cookie, code or Client ID.
"""
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, parse_qs
from urllib.request import Request, build_opener, HTTPRedirectHandler

BASE="https://astro-chat-lab-oauth-qa.joseungil.workers.dev"
ADMIN="https://astro-chat-lab-qa.joseungil.workers.dev"
CALLBACK=BASE+"/callback"

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None
opener=build_opener(NoRedirect())

def fetch(path, referer=None):
    headers={"User-Agent":"AstroChatLab-CMS-Readiness/1.0"}
    if referer: headers["Referer"]=referer
    req=Request(BASE+path,headers=headers,method="GET")
    try:
        with opener.open(req,timeout=25) as response:
            return response.status,dict(response.headers),response.read()
    except HTTPError as exc:
        return exc.code,dict(exc.headers),exc.read()

try:
    code,headers,body=fetch("/health")
    assert code==200, "Auth Worker must be configured (health HTTP 200 required)"
    data=json.loads(body)
    assert data.get("configured") is True
    assert data.get("service")=="astro-chat-lab-oauth-qa"
    assert data.get("callback")==CALLBACK
    assert "no-store" in headers.get("Cache-Control","")
    assert "Access-Control-Allow-Origin" not in headers
    wrong_scope,_,_=fetch("/auth?provider=github&site_id=astro-chat-lab-qa.joseungil.workers.dev&scope=repo",ADMIN+"/admin/")
    assert wrong_scope==400, "Broad repo OAuth scope was not rejected"
    wrong_site,_,_=fetch("/auth?provider=github&site_id=someone-else.invalid&scope=public_repo",ADMIN+"/admin/")
    assert wrong_site==400, "Different site was not rejected"
    unauth_cb,_,_=fetch("/callback?state=invalid&code=not-real")
    assert unauth_cb==400, "Callback without state/cookie was not rejected"
    good_start,auth_headers,_=fetch("/auth?provider=github&site_id=astro-chat-lab-qa.joseungil.workers.dev&scope=public_repo",ADMIN+"/admin/")
    assert good_start==302, "OAuth start did not issue GitHub redirect"
    target=urlsplit(auth_headers.get("Location",""))
    assert target.scheme=="https" and target.netloc=="github.com"
    assert target.path=="/login/oauth/authorize"
    params=parse_qs(target.query)
    assert params.get("redirect_uri")==[CALLBACK]
    assert params.get("scope")==["public_repo"]
    assert len(params.get("state",[]))==1 and len(params["state"][0])==43
    cookie=auth_headers.get("Set-Cookie","")
    assert "__Host-astro_lab_oauth=" in cookie
    assert "Secure" in cookie and "HttpOnly" in cookie and "SameSite=Lax" in cookie
except (AssertionError,URLError,TimeoutError,ValueError) as exc:
    raise SystemExit("BLOCKED: OAuth readiness preflight failed: "+str(exc)) from None

print(json.dumps({
    "result":"PASS",
    "health":200,
    "configured":True,
    "broadScopeDenied":True,
    "wrongSiteDenied":True,
    "missingStateDenied":True,
    "start":"GitHub OAuth 302 verified; user login and content write NOT tested",
    "callback":CALLBACK
},sort_keys=True))
