#!/usr/bin/env python3
"""GET-only identity and collision preflight; never prints Cloudflare credentials."""
import json
import os
import urllib.error
import urllib.request

account=os.environ.get("CLOUDFLARE_ACCOUNT_ID")
token=os.environ.get("CLOUDFLARE_API_TOKEN")
if not account or not token:
    raise SystemExit("BLOCKED: missing existing Cloudflare deploy credentials")
base="https://api.cloudflare.com/client/v4/accounts/"+account
headers={"Authorization":"Bearer "+token,"Accept":"application/json"}
worker="astro-chat-lab-oauth-qa"
origin="https://"+worker+".joseungil.workers.dev"

def get(path):
    try:
        req=urllib.request.Request(base+path,method="GET",headers=headers)
        with urllib.request.urlopen(req,timeout=25) as response:
            data=response.read()
            return response.status,json.loads(data) if data else None
    except urllib.error.HTTPError as exc:
        return exc.code,None
    except (urllib.error.URLError,TimeoutError) as exc:
        raise SystemExit("BLOCKED: Cloudflare GET network failure, Worker existence unknown") from exc

status,data=get("/workers/subdomain")
if status!=200 or not data or data.get("success") is not True:
    raise SystemExit("BLOCKED: Cloudflare account subdomain lookup failed HTTP "+str(status))
if data.get("result",{}).get("subdomain")!="joseungil":
    raise SystemExit("BLOCKED: Wrong Cloudflare account subdomain, no deployment")
status,_=get("/workers/scripts/"+worker)
if status==404:
    print("GET-only verified: dedicated OAuth Worker does not exist; safe to create")
elif status in (200,204):
    # Existing target may only be modified if a GET response independently
    # proves it is already OUR dedicated OAuth service.
    try:
        req=urllib.request.Request(origin+"/health",
            headers={"User-Agent":"AstroChatLab-OAuth-Gate/1"})
        try:
            with urllib.request.urlopen(req,timeout=20) as response:
                http_status=response.status
                body=response.read()
        except urllib.error.HTTPError as err:
            http_status=err.code
            body=err.read()
        print("Existing OAuth Worker health HTTP status: "+str(http_status))
        if http_status not in (200,503):
            raise ValueError("Unexpected health HTTP status")
        parsed=json.loads(body)
        if parsed.get("service")!=worker or parsed.get("callback")!=origin+"/callback":
            raise ValueError("Service identity marker mismatch")
    except (ValueError,urllib.error.URLError,TimeoutError) as exc:
        raise SystemExit("BLOCKED: Existing Worker identity was NOT verified; refusing overwrite") from exc
    print("GET-only verified: the existing dedicated OAuth Worker is ours")
elif status in (401,403):
    raise SystemExit("BLOCKED: Cloudflare Worker lookup permission denied HTTP "+str(status))
else:
    raise SystemExit("BLOCKED: Cloudflare Worker existence unknown HTTP "+str(status))
print("Approved isolated OAuth target: "+origin)
