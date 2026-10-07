"""Artifact bytes (one pinned production HTML insertion allowed), headers and 404."""
import fnmatch,hashlib,json,sys,urllib.request,urllib.error
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote
# Existing repository QA application identities; chosen by declared phase once.
# This is not a fallback identity, a browser impersonation or an access grant.
CLIENT_IDENTITIES={'preview':'SiteFactory-StagingQA/3.0','production':'SiteFactory-LiveQA/3.0'}
def request_response(url,phase,opener=None):
 assert phase in CLIENT_IDENTITIES,'Unsupported verification phase'
 request=urllib.request.Request(url,headers={'User-Agent':CLIENT_IDENTITIES[phase],'Cache-Control':'no-cache'})
 try:return (opener or urllib.request.urlopen)(request,timeout=30)
 except urllib.error.HTTPError as error:return error

def assert_response_status(response,url,route,expected_status):
 # Never retry, rotate identity, or interpret security/rate-limit denial as success.
 assert response.status not in (401,403,429),('access/rate-limit denied',route,response.status)
 assert response.status==expected_status and response.url==url,('status/redirect',route,response.status)

# Matcher based on the existing published helper; M4 adds only a second exact
# whole-insertion/URL pair observed in retained production response evidence.
# Original helper:
# joseungil-kr/fwith-site-factory/site-factory/engine/verify_live.py
# commit 657b9ce62b1a519ba606f9fb0110aa3679d0931c; source SHA-256
# 88f987ce341dca2e607947b2da5ac6698642127bc992cc09d78ac4370b38d9a5.
# This local copy avoids an unbound runtime import outside the control manifest.
GOYANG_CF_BEACON_SRC = b"https://static.cloudflareinsights.com/beacon.min.js/v31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495"
GOYANG_CF_BEACON_SHA256 = "8a5cd48fb3f913d009a128498bef6fadc43d5561daec87e79f6adcd0bcc903f5"
# No URL prefixes, version wildcards, attribute stripping or generic normalization.
PINNED_MANAGED_BEACONS = (
    (GOYANG_CF_BEACON_SRC, GOYANG_CF_BEACON_SHA256),
    (b"https://static.cloudflareinsights.com/beacon.min.js/v4bc70e2c01a94c73b74392e4234840661791215815920", "53ed6266d9ab3cb60b83bb38278a519b4b688707f7254f5ffeeeb8bcaa3a5e4c"),
)

def goyang_artifact_matches(html, artifact, allow_managed_beacon=False):
    live = html.encode("utf-8")
    if live == artifact:
        return True
    closing = b"</body></html>"
    if not allow_managed_beacon or not artifact.endswith(closing) or not live.endswith(closing):
        return False
    prefix = artifact[:-len(closing)]
    if not live.startswith(prefix):
        return False
    inserted = live[len(prefix):-len(closing)]
    return (inserted.endswith(b'</script>\n') and inserted.count(b'<script') == 1
            and any(inserted.startswith(b'<script type="module" src="' + src + b'" ')
                    and hashlib.sha256(inserted).hexdigest() == digest
                    for src, digest in PINNED_MANAGED_BEACONS))

def artifact_comparison(data,artifact,phase,is_html):
 """Return truthful hash evidence, or None. Never normalize either byte string.

 managedBeaconCount counts only a separately accepted provider insertion, not
 scripts already in the expected artifact. No beacon attributes/values are logged.
 """
 assert phase in CLIENT_IDENTITIES,'Unsupported verification phase'
 exact=data==artifact
 if not exact:
  if phase!='production' or not is_html:return None
  try:html=data.decode('utf-8')
  except UnicodeDecodeError:return None
  if not goyang_artifact_matches(html,artifact,allow_managed_beacon=True):return None
 return {'matchMode':'exact' if exact else 'pinned-managed-beacon',
         'rawBodySha256':hashlib.sha256(data).hexdigest(),
         'expectedArtifactSha256':hashlib.sha256(artifact).hexdigest(),
         'rawBodyBytes':len(data),'expectedArtifactBytes':len(artifact),
         'managedBeaconCount':0 if exact else 1,
         'managedBeaconSha256':None if exact else hashlib.sha256(data[len(artifact)-len(b'</body></html>'):-len(b'</body></html>')]).hexdigest()}

def verify_artifact(data,artifact,phase,is_html,route):
 receipt=artifact_comparison(data,artifact,phase,is_html)
 assert receipt is not None,('artifact bytes',route)
 # Bind receipts without printing potentially sensitive verification-file names.
 return {'routeSha256':hashlib.sha256(route.encode()).hexdigest(),**receipt}

class Meta(HTMLParser):
 def __init__(self):super().__init__();self.robots=[];self.revisions=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='meta' and a.get('name','').lower()=='robots':self.robots.append(a.get('content',''))
  if tag=='meta' and a.get('name')=='site-factory-revision':self.revisions.append(a.get('content',''))
def directives(text):return {x.strip().lower() for x in text.split(',') if x.strip()}
def rules(path):
 out=[];current=None
 if not path.exists():return out
 for line in path.read_text().splitlines():
  if not line.strip() or line.lstrip().startswith('#'):continue
  if not line[0].isspace():
   assert line.startswith('/') and ':' not in line,'Unsupported header matcher requires review'
   current=[line,{}];out.append(current)
  else:
   assert current is not None and ':' in line,'Invalid header rule'
   key,value=line.strip().split(':',1);assert key and value.strip(),'Invalid header declaration'
   current[1][key.lower()]=value.strip()
 return out
def verify_headers(route,headers,header_rules):
 expected={}
 for pattern,values in header_rules:
  if fnmatch.fnmatchcase(route,pattern):expected.update(values)
 assert directives(headers.get('x-robots-tag',''))==directives(expected.get('x-robots-tag','')),('Unexpected provider robots header',route)
 for name,value in expected.items():
  actual=headers.get(name,'')
  if name=='x-robots-tag':assert directives(actual)==directives(value),(route,name)
  else:assert actual==value,(route,name)
def main():
 p=json.loads(Path(sys.argv[1]).read_text());phase=sys.argv[2];dist=Path(sys.argv[3]);revision=sys.argv[4];origin=p['previewOrigin' if phase=='preview' else 'productionOrigin'];headers=rules(dist/'_headers');receipts=[]
 def fetch(route,expected_status):
  url=origin+quote(route,safe='/')
  r=request_response(url,phase)
  with r:
   assert_response_status(r,url,route,expected_status)
   body=r.read();verify_headers(route,r.headers,headers);return body,r.headers
 for f in sorted(dist.rglob('*')):
  if not f.is_file() or f.name in ('_headers','_redirects','404.html'):continue
  rel=str(f.relative_to(dist));route='/'+rel
  if rel=='index.html':route='/'
  elif rel.endswith('/index.html'):route='/'+rel[:-10]
  data,response=fetch(route,200);receipts.append(verify_artifact(data,f.read_bytes(),phase,f.suffix=='.html',route))
  if f.suffix=='.html':
   meta=Meta();meta.feed(data.decode());assert meta.revisions==[revision],('revision',route)
   robotset=set().union(*(directives(x) for x in meta.robots),directives(response.get('X-Robots-Tag','')))
   if phase=='preview':assert 'noindex' in robotset,('preview indexable',route)
   # Production thin-hub noindex is permitted only as reviewed local bytes/native QA specify.
 missing='/__manual_release_missing_20261007__';data,response=fetch(missing,404)
 receipts.append(verify_artifact(data,(dist/'404.html').read_bytes(),phase,True,missing))
 meta=Meta();meta.feed(data.decode());assert 'noindex' in set().union(*(directives(x) for x in meta.robots),directives(response.get('X-Robots-Tag',''))),'404 indexing mismatch'
 print('Every artifact (exact or pinned production HTML insertion), meta revision, headers, preview noindex and real 404 verified')
 return receipts
if __name__=='__main__':main()
