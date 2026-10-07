"""GET-only diagnosis for the existing Namyangju QA deployment; no state mutation."""
import hashlib,json,os,subprocess,time,urllib.request,urllib.error
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
SOURCE='65127f7793a7e7f1f5634fc09132da75bf5218c7'
ORIGIN='https://namyangju-flower-guide-qa.joseungil.workers.dev'
BRANCH='refs/heads/manual-namyangju-hosted-check-20261007'
ROOT=Path.cwd();OUTPUT=ROOT/'namyangju-readonly-diagnostic';OUTPUT.mkdir(exist_ok=True)
assert os.environ['GITHUB_REF']==BRANCH
assert subprocess.check_output(['git','-C','target','rev-parse','HEAD']).decode().strip()==SOURCE
DIST=ROOT/'target/site-factory/namyangju-flower/dist'
TARGETS=[('/',DIST/'index.html'),('/_astro/BaseLayout.MRzcX74D.css',DIST/'_astro/BaseLayout.MRzcX74D.css'),('/robots.txt',DIST/'robots.txt')]
HEADERS=('content-type','location','cf-ray','server','cf-cache-status','cf-mitigated','x-robots-tag','cache-control')
def digest(b):return hashlib.sha256(b).hexdigest()
def safe_url(value):
 u=urlsplit(value);return urlunsplit((u.scheme,u.netloc,u.path,'[redacted]' if u.query else '',u.fragment))
def request(route,file,label,user_agent=None):
 url=ORIGIN+route;headers={'Cache-Control':'no-cache'}
 if user_agent:headers['User-Agent']=user_agent
 row={'route':route,'requestUrl':url,'requestIdentity':label,'expectedSha256':digest(file.read_bytes())}
 try:
  try:r=urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30)
  except urllib.error.HTTPError as error:r=error
  with r:
   data=r.read();selected={k:r.headers.get(k) for k in HEADERS if r.headers.get(k) is not None}
   if 'location' in selected:selected['location']=safe_url(selected['location'])
   row.update(status=r.status,finalUrl=safe_url(r.url),exactFinalUrl=r.url==url,headers=selected,bodyBytes=len(data),bodySha256=digest(data),exactExpectedBytes=data==file.read_bytes())
 except Exception as error:row.update(errorType=type(error).__name__,status=None)
 return row
all_attempts=[];ready=False
for attempt in range(1,7):
 rows=[]
 for route,file in TARGETS:
  rows.append(request(route,file,'default-Python-urllib'))
  rows.append(request(route,file,'existing-official-staging-QA','SiteFactory-StagingQA/3.0'))
 all_attempts.append({'attempt':attempt,'utcTime':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'responses':rows})
 default=[r for r in rows if r['requestIdentity']=='default-Python-urllib']
 ready=all(r.get('status')==200 and r.get('exactFinalUrl') is True and r.get('exactExpectedBytes') is True for r in default)
 if ready:break
 # Only temporary 404 responses permit a bounded GET-only propagation recheck.
 # Never turn a 401,403,429,challenge,redirect or access restriction into a retry.
 if any(r.get('status') in (401,403,429) or r.get('headers',{}).get('cf-mitigated') or r.get('exactFinalUrl') is False for r in rows):break
 if not any(r.get('status')==404 for r in rows) or any(r.get('status') not in (200,404) for r in rows):break
 if attempt<6:time.sleep(20)
report={'executionRevision':os.environ['GITHUB_SHA'],'executionRef':os.environ['GITHUB_REF'],'expectedDeployedSourceRevision':SOURCE,'runId':os.environ['GITHUB_RUN_ID'],'origin':ORIGIN,'defaultClientExactReadReady':ready,'continuedUsingAlternateIdentity':False,'attempts':all_attempts}
(OUTPUT/'http-diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('readable='+str(ready).lower()+'\n')
print(json.dumps(report,indent=2))
