"""GET-only exact deployed-source baseline; never deploy or submit IndexNow."""
import argparse, hashlib, importlib.util, json, mimetypes, os, re, stat, subprocess
from pathlib import Path
from urllib.parse import quote, urlsplit, unquote
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
SOURCE='aeb04a9ed1f9f36692fd3e679e6e71c5c065224d'
CONTROL='69a7fee6a64a21443be19eca50d734d9652a968c'
ORIGIN='https://ansan.fwith.kr'
REPO='joseungil-kr/fwith-site-factory'
KEY='92c88bd5983202f9f0f07ce422cfc19de89603d8bf1e14d3685724b3b5193c98'
M4_SHA256='ad1b8ba2667f992e39875bbfc4b819578e9f25770ecbf4d20848af6312d59e39'
# Exact aeb source build regular-file inventory; excludes directories.
EXPECTED_FILES=66
EXPECTED_HTML=42
EXPECTED_SITEMAP=38
CANDIDATE_ROUTES=['/regions/sangnok-sa/', '/regions/sangnok-banwol/', '/places/seonbu-home-shop-flower-delivery/', '/order-help/daebu-flower-delivery-conditions/']
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
OPENER=build_opener(NoRedirect())
def require(ok,message):
 if not ok:raise ValueError(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':')).encode()
def save(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,indent=2)+'\n')
def mime(value):return value.split(';',1)[0].strip().lower()
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def check_source(out,label):
 url=f'https://api.github.com/repos/{REPO}/git/ref/heads/site-factory-ansan-v1'
 req=Request(url,headers={'User-Agent':'SiteFactory-LiveQA/3.0'})
 with OPENER.open(req,timeout=30) as r:
  require(r.status==200 and r.url==url,'source_read_failed');data=json.loads(r.read())
 save(out/f'source-ref-{label}.json',data)
 require(data['object']['sha']==SOURCE,'production_source_changed')
def route_for(relative):
 require(not relative.startswith('/') and '..' not in relative.split('/'),'unsafe_artifact_path')
 if relative=='index.html':return '/'
 if relative.endswith('/index.html'):return '/'+relative[:-10]
 return '/'+relative
class Page(HTMLParser):
 def __init__(self,raw):super().__init__();self.canonical=[];self.revisions=[];self.robots=[];self.feed(raw.decode())
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='link' and 'canonical' in a.get('rel','').split():self.canonical.append(a.get('href'))
  if tag=='meta' and a.get('name')=='site-factory-revision':self.revisions.append(a.get('content'))
  if tag=='meta' and a.get('name')=='robots':self.robots.append(a.get('content',''))
def validate_type(path,value):
 actual=mime(value);suffix=path.suffix.lower()
 choices={'.html':{'text/html'},'.xml':{'application/xml','text/xml'},'.txt':{'text/plain'},'.js':{'application/javascript','text/javascript'},'.mjs':{'application/javascript','text/javascript'},'.ico':{'image/x-icon','image/vnd.microsoft.icon'}}
 expected=choices.get(suffix,{mimetypes.guess_type(str(path))[0]})
 require(actual and actual in expected,'unexpected_content_type')
def collect(target,control,out):
 require(git(target,'rev-parse','HEAD')==SOURCE,'wrong_source_checkout')
 require(git(control,'rev-parse','HEAD')==CONTROL,'wrong_control_checkout')
 verifier=control/'scripts/manual-release-20261007/verify_http.py'
 require(digest(verifier.read_bytes())==M4_SHA256,'wrong_m4_bytes')
 spec=importlib.util.spec_from_file_location('m4',verifier);m4=importlib.util.module_from_spec(spec);spec.loader.exec_module(m4)
 dist=target/'site-factory/ansan-flower/dist';require(dist.is_dir(),'missing_dist')
 files={str(p.relative_to(dist)):p for p in sorted(dist.rglob('*')) if p.is_file()}
 manifest={name:digest(p.read_bytes()) for name,p in files.items()};save(out/'artifact-manifest.json',manifest)
 inventory={'sourceRevision':SOURCE,'expectedTotalFiles':EXPECTED_FILES,'actualTotalFiles':len(files),'htmlFiles':sum(p.suffix=='.html' for p in files.values()),'unservedControls':[name for name in ('_headers','_redirects') if name in files],'artifactManifestFileSha256':digest((out/'artifact-manifest.json').read_bytes())}
 save(out/'artifact-inventory-status.json',inventory);print(json.dumps(inventory),flush=True)
 require(len(files)==EXPECTED_FILES,'unexpected_artifact_count')
 headers=m4.rules(dist/'_headers');rows=[];html_map={};cached={}
 check_source(out,"before")
 def fetch(path,route,status):
  url=ORIGIN+quote(route,safe='/');req=Request(url,headers={'User-Agent':m4.CLIENT_IDENTITIES['production'],'Cache-Control':'no-cache'})
  try:r=OPENER.open(req,timeout=40)
  except HTTPError as error:r=error
  with r:
   m4.assert_response_status(r,url,route,status)
   raw=r.read(16*1024*1024+1);require(len(raw)<=16*1024*1024,'response_too_large')
   response_headers={}
   for name,value in r.headers.items():
    key=name.lower();response_headers[key]=response_headers.get(key,'')+(',' if key in response_headers else '')+value
   m4.verify_headers(route,response_headers,headers);validate_type(path,response_headers.get('content-type',''))
   comparison=m4.verify_artifact(raw,path.read_bytes(),'production',path.suffix=='.html',route)
   row={'url':url,'status':status,'expectedStatus':status,'exactFinalUrl':r.url==url,'headers':response_headers,'expectedSha256':digest(path.read_bytes()),'bodySha256':digest(raw),'comparison':comparison}
   rows.append(row);cached[url]=raw
   saved=out/'responses'/((route.strip('/')+'/index.html') if status==404 else str(path.relative_to(dist)))
   saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(raw)
   if path.suffix=='.html':
    page=Page(raw);require(page.revisions==[SOURCE],'wrong_live_revision')
    if status==200:
     expected_page=Page(path.read_bytes());require(page.canonical==expected_page.canonical and len(page.canonical)==1 and (unquote(page.canonical[0])==unquote(url) or (url==ORIGIN+'/places/hanyang-erica-entry-graduation-flowers/' and page.canonical==[ORIGIN+'/places/hanyang-erica-graduation-flowers/'] and any('noindex' in v.split(',') for v in page.robots))),'wrong_canonical');require(page.robots==expected_page.robots and len(page.robots)==1,'wrong_robots');html_map[url]=row['expectedSha256']
    else:require(any('noindex' in item.lower().split(',') for item in page.robots),'missing_404_noindex')
 for name,path in files.items():
  if name in ('_headers','_redirects','404.html'):continue
  fetch(path,route_for(name),200)
 fetch(dist/'404.html','/__manual_release_missing_20261007__',404)
 for route in CANDIDATE_ROUTES:
  require(ORIGIN+quote(route,safe='/') not in html_map,'candidate_already_exists_in_source')
  fetch(dist/'404.html',route,404)
 require(len(html_map)==EXPECTED_HTML,'incomplete_html_map')
 if ORIGIN+'/places/hanyang-erica-entry-graduation-flowers/' in html_map:require(ORIGIN+'/places/hanyang-erica-graduation-flowers/' in html_map,'canonical_alias_target_missing')
 def locations(url):
  raw=cached[url];require(b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(),'unsafe_xml')
  return [x.text for x in ET.fromstring(raw).iter() if x.tag.rsplit('}',1)[-1]=='loc']
 require(locations(ORIGIN+'/sitemap-index.xml')==[ORIGIN+'/sitemap-0.xml'],'unexpected_sitemap_index')
 urls=locations(ORIGIN+'/sitemap-0.xml');expected_urls=[x.text for x in ET.fromstring((dist/'sitemap-0.xml').read_bytes()).iter() if x.tag.rsplit('}',1)[-1]=='loc'];require(len(urls)==len(set(urls))==EXPECTED_SITEMAP and urls==expected_urls and set(urls).issubset(html_map),'incomplete_sitemap')
 for url in urls:
  page=Page(cached[url]);require(all(not re.search(r'\b(noindex|nofollow|none)\b',v,re.I) for v in page.robots),'sitemap_noindex')
 require(cached[ORIGIN+'/'+KEY+'.txt'].decode().strip()==KEY,'wrong_existing_key')
 robots=cached[ORIGIN+'/robots.txt'].decode();require('Allow: /' in robots and 'Disallow: /' not in robots and ORIGIN+'/sitemap-index.xml' in robots,'wrong_robots')
 check_source(out,"after")
 report={'passed':True,'phase':'production','siteKey':'ansan-flower-test','sourceRevision':SOURCE,'executionRevision':os.environ['GITHUB_SHA'],'controlRevision':CONTROL,'origin':ORIGIN,'runId':os.environ['GITHUB_RUN_ID'],'runAttempt':os.environ['GITHUB_RUN_ATTEMPT'],'artifactManifestSha256':digest(canonical(manifest)),'artifactManifestDigestMode':'canonical-json-object','artifactManifestFileSha256':digest((out/'artifact-manifest.json').read_bytes()),'responses':rows,'purpose':'historical-source baseline only; no new release or visual approval','pixelsReviewed':False}
 save(out/'http-receipts.json',report)
 save(out/'baseline-manifest.json',{'sourceRevision':SOURCE,'origin':ORIGIN,'complete':True,'htmlUrls':html_map,'publicHttp':{'path':'http-receipts.json','sha256':digest((out/'http-receipts.json').read_bytes())}})
 print(json.dumps({'passed':True,'sourceRevision':SOURCE,'httpCount':len(rows),'htmlCount':len(html_map),'httpReceiptsSha256':digest((out/'http-receipts.json').read_bytes())}))
MAX_EVIDENCE_BYTES=32*1024*1024
MAX_EVIDENCE_FILE_BYTES=16*1024*1024
MAX_EVIDENCE_FILES=128
MAX_EVIDENCE_ENTRIES=512
EVIDENCE_ROOT_FILES={'source-tree.txt','dependencies.json','build.log','artifact-manifest.json','artifact-inventory-status.json','source-ref-before.json','source-ref-after.json','http-receipts.json','baseline-manifest.json','failure.json'}
def bound_evidence(out):
 require(out.is_dir() and not out.is_symlink(),'invalid_evidence_root')
 total=count=entries=0
 for directory,dirs,files in os.walk(out,followlinks=False):
  for name in dirs+files:
   p=Path(directory)/name;relative=p.relative_to(out);parts=relative.parts;st=p.lstat();entries+=1
   require(entries<=MAX_EVIDENCE_ENTRIES,'too_many_evidence_entries')
   require(all(x not in ('.','..') and not x.startswith('.') and not any(ord(ch)<32 or ch in '\\:' for ch in x) for x in parts),'invalid_evidence_path')
   require(not stat.S_ISLNK(st.st_mode),'evidence_symlink')
   require(stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode),'evidence_not_regular')
   if stat.S_ISDIR(st.st_mode):
    require(parts[0] in ('responses','expected-html'),'unexpected_evidence_directory');continue
   require(st.st_nlink==1,'evidence_hardlink')
   require((len(parts)==1 and name in EVIDENCE_ROOT_FILES) or (len(parts)>1 and parts[0]=='responses') or (len(parts)>1 and parts[0]=='expected-html' and p.suffix=='.html'),'unexpected_evidence_path')
   count+=1;total+=st.st_size
   require(count<=MAX_EVIDENCE_FILES,'too_many_evidence_files')
   require(st.st_size<=MAX_EVIDENCE_FILE_BYTES,'evidence_file_too_large')
   require(total<=MAX_EVIDENCE_BYTES,'evidence_total_too_large')
 require(count>0,'empty_evidence')
 return {'passed':True,'files':count,'entries':entries,'totalBytes':total,'maxFiles':MAX_EVIDENCE_FILES,'maxTotalBytes':MAX_EVIDENCE_BYTES,'maxFileBytes':MAX_EVIDENCE_FILE_BYTES}
def main():
 p=argparse.ArgumentParser();p.add_argument('--target',type=Path);p.add_argument('--control',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--bound-only',action='store_true');args=p.parse_args()
 if args.bound_only:
  print(json.dumps(bound_evidence(args.out)));return
 require(args.target is not None and args.control is not None,'missing_checkout_arguments')
 args.out.mkdir(parents=True,exist_ok=True)
 try:collect(args.target,args.control,args.out)
 except Exception as error:
  failure={'passed':False,'exceptionClass':type(error).__name__,'reason':str(error) if isinstance(error,ValueError) and re.fullmatch('[a-z0-9_]+',str(error)) else 'verification_failed','sourceRevision':SOURCE};save(args.out/'failure.json',failure);print(json.dumps(failure),flush=True);raise SystemExit(1)
if __name__=='__main__':main()
