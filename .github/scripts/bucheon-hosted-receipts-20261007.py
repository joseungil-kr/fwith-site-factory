"""Retain exact public-response bytes using immutable M2's declared QA client."""
import hashlib,importlib.util,json,os,subprocess
from pathlib import Path
from urllib.parse import quote,urlsplit,urlunsplit
SOURCE='1f00f46ef2afad7dcc0ca814d98ec31cf7abc73e'
CONTROL='657b9ce62b1a519ba606f9fb0110aa3679d0931c'
ORIGIN='https://bucheon-flower-guide-qa.joseungil.workers.dev'
ROOT=Path.cwd();DIST=ROOT/'target/site-factory/bucheon-flower/dist';OUT=ROOT/'bucheon-hosted-http';OUT.mkdir(exist_ok=True)
assert os.environ['GITHUB_REF']=='refs/heads/manual-bucheon-hosted-check-20261007'
assert subprocess.check_output(['git','-C','target','rev-parse','HEAD']).decode().strip()==SOURCE
assert subprocess.check_output(['git','-C','control','rev-parse','HEAD']).decode().strip()==CONTROL
helper=ROOT/'control/scripts/manual-release-20261007/verify_http.py'
assert hashlib.sha256(helper.read_bytes()).hexdigest()=='843e24e59186d7ef01bfcef4c19b6fc9976548c0768f9ccd01b9f5191555e76a'
spec=importlib.util.spec_from_file_location('reviewed_M2_http',helper);qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
manifest={str(f.relative_to(DIST)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(DIST.rglob('*')) if f.is_file()}
assert len(manifest)==64
assert hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()=='c435ef1cb980e363ba67862fb9877deaae558ecf63b5cb7780c71dc50521b291'
header_rules=qa.rules(DIST/'_headers');rows=[]
report={'executionRevision':os.environ['GITHUB_SHA'],'executionRef':os.environ['GITHUB_REF'],'sourceRevision':SOURCE,'controlRevision':CONTROL,'runId':os.environ['GITHUB_RUN_ID'],'origin':ORIGIN,'requestIdentity':qa.CLIENT_IDENTITIES['preview'],'passed':False,'responses':rows}
def safe_final_url(value):
 parsed=urlsplit(value);host=parsed.hostname or ''
 if parsed.port is not None:host+=':'+str(parsed.port)
 return urlunsplit((parsed.scheme,host,parsed.path,'[redacted]' if parsed.query else '', ''))
def fetch(route,file,status,storage):
 url=ORIGIN+quote(route,safe='/');row={'route':route,'url':url,'expectedStatus':status,'expectedSha256':hashlib.sha256(file.read_bytes()).hexdigest()};rows.append(row)
 response=qa.request_response(url,'preview')
 with response:
  row.update(status=response.status,finalUrl=safe_final_url(response.url),exactFinalUrl=response.url==url,headers={k:response.headers.get(k) for k in ['content-type','cf-ray','cf-cache-status','x-robots-tag','cache-control'] if response.headers.get(k) is not None})
  qa.assert_response_status(response,url,route,status)
  data=response.read();row.update(bodyBytes=len(data),bodySha256=hashlib.sha256(data).hexdigest());body=OUT/'responses'/storage;body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(data)
  qa.verify_headers(route,response.headers,header_rules);assert data==file.read_bytes(),('artifact bytes',route)
  if file.suffix=='.html':
   meta=qa.Meta();meta.feed(data.decode());assert meta.revisions==[SOURCE],('revision',route)
   robots=set().union(*(qa.directives(x) for x in meta.robots),qa.directives(response.headers.get('X-Robots-Tag','')));assert 'noindex' in robots,('preview indexable',route);row.update(revisions=meta.revisions,robots=sorted(robots))
try:
 for file in sorted(DIST.rglob('*')):
  if not file.is_file() or file.name in ('_headers','_redirects','404.html'):continue
  relative=str(file.relative_to(DIST));route='/'+relative
  if relative=='index.html':route='/'
  elif relative.endswith('/index.html'):route='/'+relative[:-10]
  fetch(route,file,200,relative)
 fetch('/__manual_release_missing_20261007__',DIST/'404.html',404,'__verified_missing__/index.html')
 assert len(rows)==63;report['passed']=True
finally:
 (OUT/'http-receipts.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'sourceRevision':SOURCE,'executionRevision':os.environ['GITHUB_SHA'],'passed':report['passed'],'responses':len(rows)}))
