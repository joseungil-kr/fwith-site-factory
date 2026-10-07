"""All rendered bytes plus parsed robots, response-header rules and real 404."""
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
 p=json.loads(Path(sys.argv[1]).read_text());phase=sys.argv[2];dist=Path(sys.argv[3]);revision=sys.argv[4];origin=p['previewOrigin' if phase=='preview' else 'productionOrigin'];headers=rules(dist/'_headers')
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
  data,response=fetch(route,200);assert data==f.read_bytes(),('artifact bytes',route)
  if f.suffix=='.html':
   meta=Meta();meta.feed(data.decode());assert meta.revisions==[revision],('revision',route)
   robotset=set().union(*(directives(x) for x in meta.robots),directives(response.get('X-Robots-Tag','')))
   if phase=='preview':assert 'noindex' in robotset,('preview indexable',route)
   # Production thin-hub noindex is permitted only as reviewed local bytes/native QA specify.
 missing='/__manual_release_missing_20261007__';data,response=fetch(missing,404)
 assert data==(dist/'404.html').read_bytes(),'Wrong 404 artifact'
 meta=Meta();meta.feed(data.decode());assert 'noindex' in set().union(*(directives(x) for x in meta.robots),directives(response.get('X-Robots-Tag',''))),'404 indexing mismatch'
 print('Every artifact, meta revision, headers, preview noindex and exact 404 verified')
if __name__=='__main__':main()
