#!/usr/bin/env python3
"""GET-only Cloudflare identity and collision check. Never prints credentials."""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")
WORKER = "astro-chat-lab-qa"
if not ACCOUNT_ID or not TOKEN:
    raise SystemExit("BLOCKED: Existing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN secret is not available")
BASE = "https://api.cloudflare.com/client/v4/accounts/" + ACCOUNT_ID
HEADERS = {"Authorization": "Bearer " + TOKEN, "Accept": "application/json"}

def get(path):
    req = urllib.request.Request(BASE + path, headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            info = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            info = {}
        return exc.code, info
    except (urllib.error.URLError, TimeoutError) as exc:
        raise SystemExit("BLOCKED: Cloudflare GET network error, no existence conclusion") from exc

status, response = get("/workers/subdomain")
if status in (401, 403):
    raise SystemExit("BLOCKED: Cloudflare workers.dev subdomain GET permission denied: " + str(status))
if status != 200 or response.get("success") is not True:
    raise SystemExit("BLOCKED: Cloudflare workers.dev subdomain GET failed: HTTP " + str(status))
subdomain = response.get("result", {}).get("subdomain")
if not isinstance(subdomain, str) or not subdomain or not subdomain.replace("-", "").isalnum():
    raise SystemExit("BLOCKED: Account workers.dev subdomain is not configured or not verifiable")

status, response = get("/workers/scripts/" + WORKER)
if status in (401, 403):
    raise SystemExit("BLOCKED: Cloudflare worker identity check permission denied: " + str(status))
if status == 200:
    raise SystemExit("BLOCKED: Worker name already exists; refusing to overwrite another Worker")
if status != 404:
    raise SystemExit("BLOCKED: Cloudflare worker collision check uncertain: HTTP " + str(status))
origin = "https://" + WORKER + "." + subdomain + ".workers.dev"
if not origin.startswith("https://astro-chat-lab-qa."):
    raise SystemExit("invalid experiment origin")

for name, value in (("ASTRO_CHAT_SITE_URL", origin + "/"), ("ASTRO_CHAT_ORIGIN", origin)):
    with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as fh:
        fh.write(name + "=" + value + "\n")
Path("site-factory/astro-chat-lab/verified-origin.txt").write_text(origin + "\n", encoding="utf-8")
print("Cloudflare GET-only preflight OK: dedicated Worker name absent, workers.dev configured.")
print("Resolved public origin: " + origin)
