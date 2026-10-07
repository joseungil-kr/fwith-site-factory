"""Retain exact public-response bytes using immutable reviewed M3 verifier and its declared QA client."""
import datetime,hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
from urllib.parse import quote,urlsplit,urlunsplit
SOURCE='d02e86ed7fc39131431a0332a84002906be2f88b'
CONTROL='41ab5fd749d3e6f755788022158fefe06c523048'
DEPLOYMENT_CONTROL='657b9ce62b1a519ba606f9fb0110aa3679d0931c'
ORIGIN='https://namyangju.fwith.kr'
ROOT=Path.cwd();DIST=ROOT/'target/site-factory/namyangju-flower/dist';OUT=ROOT/'namyangju-hosted-http';OUT.mkdir(exist_ok=True)
assert os.environ['GITHUB_REF']=='refs/heads/manual-namyangju-production-check-20261007'
assert subprocess.check_output(['git','-C','target','rev-parse','HEAD']).decode().strip()==SOURCE
assert subprocess.check_output(['git','-C','control','rev-parse','HEAD']).decode().strip()==CONTROL
helper=ROOT/'control/scripts/manual-release-20261007/verify_http.py'
assert hashlib.sha256(helper.read_bytes()).hexdigest()=='ceda678e546014bcf80704a5cc7f095ab7ce13594bc9f2583f9849db85ce0ddf'
spec=importlib.util.spec_from_file_location('reviewed_M3_http',helper);qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
manifest={str(f.relative_to(DIST)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(DIST.rglob('*')) if f.is_file()}
assert len(manifest)==58
assert hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()=='1ebb3ee499491d11d3aa2e98a4e1154df169cc1faa78a6d8edc87a976403a7eb'
header_rules=qa.rules(DIST/'_headers');rows=[];active_route=None
report={'startedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'executionRevision':os.environ['GITHUB_SHA'],'executionRef':os.environ['GITHUB_REF'],'sourceRevision':SOURCE,'controlRevision':CONTROL,'verificationControlRevision':CONTROL,'deploymentControlRevision':DEPLOYMENT_CONTROL,'deploymentRunId':'37649348646','deploymentOutcome':'failure-at-M2-HTTP-postcheck','verificationHelperSha256':hashlib.sha256(helper.read_bytes()).hexdigest(),'phase':'production','artifactManifestSha256':'1ebb3ee499491d11d3aa2e98a4e1154df169cc1faa78a6d8edc87a976403a7eb','runId':os.environ['GITHUB_RUN_ID'],'origin':ORIGIN,'requestIdentity':qa.CLIENT_IDENTITIES['production'],'passed':False,'responses':rows}
def safe_final_url(value):
 parsed=urlsplit(value);host=parsed.hostname or ''
 if parsed.port is not None:host+=':'+str(parsed.port)
 return urlunsplit((parsed.scheme,host,parsed.path,'[redacted]' if parsed.query else '', ''))
def fetch(route,file,status,storage):
 global active_route
 active_route=route
 url=ORIGIN+quote(route,safe='/');row={'route':route,'url':url,'expectedStatus':status,'expectedSha256':hashlib.sha256(file.read_bytes()).hexdigest()};rows.append(row)
 response=qa.request_response(url,'production')
 with response:
  row.update(status=response.status,finalUrl=safe_final_url(response.url),exactFinalUrl=response.url==url,headers={k:response.headers.get(k) for k in ['content-type','cf-ray','cf-cache-status','x-robots-tag','cache-control','x-content-type-options','x-frame-options','referrer-policy'] if response.headers.get(k) is not None})
  qa.assert_response_status(response,url,route,status)
  data=response.read();row.update(receivedAtUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),bodyBytes=len(data),bodySha256=hashlib.sha256(data).hexdigest());body=OUT/'responses'/storage;body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(data)
  qa.verify_headers(route,response.headers,header_rules);row['comparison']=qa.verify_artifact(data,file.read_bytes(),'production',file.suffix=='.html',route)
  if file.suffix=='.html':
   meta=qa.Meta();meta.feed(data.decode());assert meta.revisions==[SOURCE],('revision',route)
   robots=set().union(*(qa.directives(x) for x in meta.robots),qa.directives(response.headers.get('X-Robots-Tag','')));expected_meta=qa.Meta();expected_meta.feed(file.read_text());assert meta.robots==expected_meta.robots,('production robots differ from reviewed artifact',route);row.update(revisions=meta.revisions,robots=sorted(robots))
try:
 for file in sorted(DIST.rglob('*')):
  if not file.is_file() or file.name in ('_headers','_redirects','404.html'):continue
  relative=str(file.relative_to(DIST));route='/'+relative
  if relative=='index.html':route='/'
  elif relative.endswith('/index.html'):route='/'+relative[:-10]
  fetch(route,file,200,relative)
 fetch('/__manual_release_missing_20261007__',DIST/'404.html',404,'__verified_missing__/index.html')
 assert len(rows)==57;report['passed']=True
except Exception as error:
 failure={'exceptionClass':type(error).__name__,'routeSha256':hashlib.sha256(active_route.encode()).hexdigest() if active_route is not None else None}
 report['failure']=failure
 (OUT/'private-failure.txt').write_text(repr(error)+'\n')
 print(json.dumps({'passed':False,'failure':failure}),file=sys.stderr)
 raise SystemExit(1) from None
finally:
 report['completedAtUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (OUT/'http-receipts.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'sourceRevision':SOURCE,'executionRevision':os.environ['GITHUB_SHA'],'passed':report['passed'],'responses':len(rows)}))
