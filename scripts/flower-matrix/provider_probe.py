#!/usr/bin/env python3
"""Read-only Cloudflare DNS/Workers inventory for flower-a.fwith.kr and flower-b.fwith.kr."""
import json, os, re, sys
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API="https://api.cloudflare.com/client/v4"
HOSTS=["flower-a.fwith.kr","flower-b.fwith.kr"]
UA="SiteFactory-FlowerMatrix-ReadOnly-Preflight/1.0"

def api_get(path):
    token=os.environ.get("CLOUDFLARE_API_TOKEN","")
    if not token:
        return {"httpStatus":None,"success":False,"error":"CLOUDFLARE_API_TOKEN missing","result":None,"result_info":None}
    req=Request(API+path,headers={"Authorization":"Bearer "+token,"Accept":"application/json","User-Agent":UA})
    try:
        with urlopen(req,timeout=20) as response:
            raw=response.read(2*1024*1024+1)
            status=response.status
    except HTTPError as error:
        raw=error.read(256*1024+1);status=error.code
    except Exception as error:
        return {"httpStatus":None,"success":False,"error":type(error).__name__+":"+str(error),"result":None,"result_info":None}
    if len(raw)>2*1024*1024:
        return {"httpStatus":status,"success":False,"error":"response_limit_exceeded","result":None,"result_info":None}
    try:
        data=json.loads(raw)
    except Exception:
        return {"httpStatus":status,"success":False,"error":"non_json_response","result":None,"result_info":None}
    errors=[{"code":x.get("code"),"message":x.get("message")} for x in (data.get("errors") or [])]
    return {"httpStatus":status,"success":status==200 and data.get("success") is True and not errors,
            "error":errors or None,"result":data.get("result"),"result_info":data.get("result_info")}

def list_all(path):
    rows=[];pages=[];failures=[]
    for page in range(1,21):
        sep="&" if "?" in path else "?"
        r=api_get(path+sep+urlencode({"page":page,"per_page":100}))
        pages.append({"page":page,"httpStatus":r["httpStatus"],"success":r["success"],"error":r["error"]})
        if not r["success"] or not isinstance(r["result"],list):
            failures.append(pages[-1]);break
        rows.extend(r["result"])
        info=r.get("result_info") or {}
        total=info.get("total_pages")
        if total is not None and page>=total:break
        if total is None and len(r["result"])<100:break
    else:
        failures.append({"error":"pagination_limit_exceeded"})
    return rows,{"pages":pages,"complete":not failures,"failures":failures,"count":len(rows)}

def route_covers(pattern,hostname):
    if not isinstance(pattern,str) or "/" not in pattern:return False
    host_pattern=pattern.split("/",1)[0].lower()
    if host_pattern==hostname:return True
    if host_pattern.startswith("*."):
        suffix=host_pattern[1:]
        return hostname.endswith(suffix) and hostname!=suffix[1:]
    return False

def public_dns(host,qtype):
    url="https://dns.google/resolve?"+urlencode({"name":host,"type":qtype})
    req=Request(url,headers={"Accept":"application/dns-json","User-Agent":UA})
    try:
        with urlopen(req,timeout=12) as response:
            status=response.status;raw=response.read(256*1024+1)
        if len(raw)>256*1024:return {"queryType":qtype,"httpStatus":status,"complete":False,"error":"response_limit_exceeded","answers":[]}
        data=json.loads(raw)
        answers=[{"name":x.get("name"),"type":x.get("type"),"data":x.get("data"),"ttl":x.get("TTL")} for x in (data.get("Answer") or [])]
        return {"queryType":qtype,"httpStatus":status,"complete":status==200 and data.get("Status")==0,"dnsStatus":data.get("Status"),"answers":answers}
    except Exception as error:
        return {"queryType":qtype,"httpStatus":None,"complete":False,"error":type(error).__name__+":"+str(error),"answers":[]}

def main():
    account=os.environ.get("CLOUDFLARE_ACCOUNT_ID","")
    token=os.environ.get("CLOUDFLARE_API_TOKEN","")
    report={"schemaVersion":1,"mode":"read-only","mutationsPerformed":False,"targets":{},"checks":{}}
    if not re.fullmatch(r"[0-9a-fA-F]{32}",account) or not token:
        report["status"]="READ_BLOCKED_CONFIGURATION_MISSING"
        report["checks"]["configuration"]={"accountIdPresent":bool(account),"tokenPresent":bool(token)}
        write(report);return
    account_resp=api_get("/accounts/"+account)
    report["checks"]["account"]={"httpStatus":account_resp["httpStatus"],"success":account_resp["success"],"identityMatches":bool(isinstance(account_resp["result"],dict) and account_resp["result"].get("id")==account),"error":account_resp["error"]}
    zones,zone_meta=list_all("/zones?"+urlencode({"name":"fwith.kr","status":"active"}))
    report["checks"]["zoneInventory"]={"complete":zone_meta["complete"],"count":len(zones),"pages":zone_meta["pages"],"failures":zone_meta["failures"]}
    matching_zones=[z for z in zones if z.get("name","").lower()=="fwith.kr"]
    zone=matching_zones[0] if len(matching_zones)==1 else None
    report["checks"]["zoneIdentity"]={"exactZoneCount":len(matching_zones),"accountMatches":bool(zone and (not zone.get("account",{}).get("id") or zone.get("account",{}).get("id")==account)),"status":zone.get("status") if zone else None}
    account_prefix="/accounts/"+account
    scripts,script_meta=list_all(account_prefix+"/workers/scripts")
    domains,domain_meta=list_all(account_prefix+"/workers/domains")
    report["checks"]["workerScripts"]={"complete":script_meta["complete"],"count":script_meta["count"],"pages":script_meta["pages"],"failures":script_meta["failures"]}
    report["checks"]["workerDomains"]={"complete":domain_meta["complete"],"count":domain_meta["count"],"pages":domain_meta["pages"],"failures":domain_meta["failures"]}
    candidate_scripts=[x.get("id") for x in scripts if isinstance(x.get("id"),str) and any(k in x["id"].lower() for k in ("flower-a","flower-b","matrix"))]
    report["checks"]["candidateWorkerNames"]=sorted(set(candidate_scripts))
    relevant_domains=[{"hostname":x.get("hostname"),"service":x.get("service"),"environment":x.get("environment"),"zone_name":x.get("zone_name")} for x in domains if isinstance(x.get("hostname"),str) and (x["hostname"].lower() in HOSTS or any(k in (x.get("service") or "").lower() for k in ("flower-a","flower-b","matrix")))]
    report["checks"]["relevantWorkerDomains"]=relevant_domains
    routes=[];route_meta={"complete":False,"count":0,"pages":[],"failures":[]}
    if zone and zone.get("id"):
        routes,route_meta=list_all("/zones/"+zone["id"]+"/workers/routes")
    report["checks"]["workerRoutes"]={"complete":route_meta["complete"],"count":route_meta["count"],"pages":route_meta["pages"],"failures":route_meta["failures"]}
    relevant_routes=[{"id":x.get("id"),"pattern":x.get("pattern"),"script":x.get("script")} for x in routes if any(route_covers(x.get("pattern"),h) for h in HOSTS)]
    report["checks"]["relevantWorkerRoutes"]=relevant_routes
    for host in HOSTS:
        dns,dns_meta=([],{"complete":False,"count":0,"pages":[],"failures":[{"error":"zone_identity_unverified"}]})
        if zone and zone.get("id"):
            dns,dns_meta=list_all("/zones/"+zone["id"]+"/dns_records?"+urlencode({"name":host}))
        relevant_dns=[{"name":x.get("name"),"type":x.get("type"),"content":x.get("content"),"proxied":x.get("proxied"),"ttl":x.get("ttl")} for x in dns if x.get("name","").lower()==host]
        custom=[x for x in relevant_domains if (x.get("hostname") or "").lower()==host]
        route=[x for x in relevant_routes if route_covers(x.get("pattern"),host)]
        report["targets"][host]={
          "dns":{"complete":dns_meta["complete"],"records":relevant_dns,"pages":dns_meta["pages"],"failures":dns_meta["failures"]},
          "publicDns":[public_dns(host,qtype) for qtype in ("A","AAAA","CNAME")],
          "workerCustomDomainBindings":custom,
          "workerRoutes":route,
          "candidateWorkers":[x for x in candidate_scripts if host.split(".")[0] in x.lower() or "matrix" in x.lower()]
        }
    checks=[report["checks"]["account"]["success"],report["checks"]["zoneInventory"]["complete"],report["checks"]["zoneIdentity"]["exactZoneCount"]==1,report["checks"]["zoneIdentity"]["accountMatches"],script_meta["complete"],domain_meta["complete"],route_meta["complete"]]
    checks.extend(v["dns"]["complete"] for v in report["targets"].values())
    report["status"]="READ_OK" if all(checks) else "READ_INCOMPLETE_OR_PERMISSION_BLOCKED"
    write(report)
    summary={"status":report["status"],"mutationsPerformed":False,"targets":{},"checkStatuses":{k:v.get("success",v.get("complete")) for k,v in report["checks"].items() if isinstance(v,dict)}}
    for host,v in report["targets"].items():
        summary["targets"][host]={"dnsRecords":v["dns"]["records"],"dnsReadComplete":v["dns"]["complete"],"dnsReadFailures":v["dns"]["failures"],"publicDns":v.get("publicDns",[]),"workerCustomDomainBindings":v["workerCustomDomainBindings"],"workerRoutes":v["workerRoutes"],"candidateWorkers":v["candidateWorkers"]}
    print(json.dumps(summary,ensure_ascii=False,indent=2))

def write(report):
    out=os.environ.get("REPORT_PATH","cloudflare-readonly-observation.json")
    with open(out,"w") as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write("\n")

if __name__=="__main__":main()
