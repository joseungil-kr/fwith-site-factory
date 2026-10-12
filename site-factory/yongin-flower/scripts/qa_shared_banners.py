#!/usr/bin/env python3
"""Inspect rendered production HTML; source template assertions alone are insufficient."""
from pathlib import Path
from html.parser import HTMLParser
import os,json,hashlib
from urllib.parse import urlsplit,unquote
class Page(HTMLParser):
 def __init__(self):super().__init__();self.headings=[];self.images=[];self.meta={};self.robots_values=[];self.links=[];self.canonical=[];self.title=[];self.in_title=False;self.banner_kinds=[];self.banner_images=[];self.current_banner=None;self.figure_depth=0
 def handle_starttag(self,tag,attrs):
  names=[name for name,value in attrs]
  assert len(names)==len(set(names)),'Duplicate HTML attributes forbidden'
  a=dict(attrs)
  if tag in ['h1','h2','h3','h4','h5','h6']:self.headings.append(int(tag[1]))
  if tag=='figure':self.figure_depth+=1
  if 'data-shared-flower-banner' in a:self.current_banner=a['data-shared-flower-banner']
  if tag=='img':
   self.images.append(a)
   if self.current_banner is not None:self.banner_images.append((self.current_banner,a))
  if tag=='meta':
   self.meta[a.get('name','')]=a.get('content','')
   if a.get('name','').casefold()=='robots':self.robots_values.append(a.get('content',''))
  if tag=='link' and 'canonical' in __import__('re').split(r'[\t\n\f\r ]+',a.get('rel','').translate(str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')).strip('\t\n\f\r ')):self.canonical.append(a.get('href',''))
  if tag=='a':self.links.append(a.get('href',''))
  if tag=='title':self.in_title=True
  if 'data-shared-flower-banner' in a:self.banner_kinds.append(a['data-shared-flower-banner'])
 def handle_endtag(self,tag):
  if tag=='title':self.in_title=False
  if tag=='figure':
   self.figure_depth-=1
   if self.figure_depth==0:self.current_banner=None
 def handle_data(self,s):
  if self.in_title:self.title.append(s)

def compact(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def url_identity(value):
 assert isinstance(value,str) and not any(ord(ch)<=32 or ord(ch)==127 for ch in value),'Raw URL whitespace/control characters forbidden'
 assert not __import__('re').search(r'%(?![0-9a-fA-F]{2})',value),'Malformed percent encoding'
 parts=urlsplit(value)
 assert not __import__('re').search(r'%(?:2f|5c|00)',parts.path,__import__('re').I),'Encoded separator or NUL is not URL-equivalent'
 assert not parts.username and not parts.password,'URL credentials forbidden'
 decoded=unquote(parts.path,errors='strict')
 assert not any(ord(ch)<32 or ord(ch)==127 for ch in decoded),'Decoded URL control characters forbidden'
 assert '\\' not in decoded and '\x00' not in decoded,'Backslash or NUL forbidden'
 assert not __import__('re').search(r'%[0-9a-fA-F]{2}',decoded),'Double-encoded path forbidden'
 return (parts.scheme,parts.netloc,decoded,parts.query,parts.fragment)
def regular_manifest(directory):
 assert directory.is_dir() and not directory.is_symlink(),'Artifact directory missing or symlinked'
 rows={}
 for path in sorted(directory.rglob('*')):
  assert not path.is_symlink(),'Artifact symlink forbidden'
  if path.is_dir():continue
  assert path.is_file(),'Nonregular artifact entry'
  rows[path.relative_to(directory).as_posix()]=sha(path.read_bytes())
 assert rows,'Empty artifact reference'
 return rows
def production_reference():
 # These fixed values must be supplied by the independently reviewed workflow/authority,
 # never recomputed from candidate bytes or a candidate-provided exclusion list.
 payload=Path(os.environ['SHARED_BANNER_REFERENCE_MANIFEST']).read_bytes()
 expected_manifest=os.environ['SHARED_BANNER_REFERENCE_MANIFEST_SHA256']
 expected_artifact=os.environ['SHARED_BANNER_REFERENCE_ARTIFACT_SHA256']
 expected_revision=os.environ['SHARED_BANNER_REFERENCE_REVISION']
 expected_origin=os.environ['SHARED_BANNER_REFERENCE_ORIGIN']
 assert sha(payload)==expected_manifest,'Production reference manifest hash mismatch'
 data=json.loads(payload)
 assert set(data)=={'schemaVersion','baselineRevision','productionOrigin','artifactManifestSha256','files'},'Reference schema mismatch'
 assert data['schemaVersion']==1 and __import__('re').fullmatch('[0-9a-f]{40}',expected_revision),'Reference identity missing'
 assert data['baselineRevision']==expected_revision and data['productionOrigin']==expected_origin,'Reference identity changed'
 assert url_identity(expected_origin)==('https',urlsplit(expected_origin).netloc,'','',''),'Reference must be an HTTPS origin'
 assert data['artifactManifestSha256']==expected_artifact==sha(compact(data['files'])),'Unreviewed production artifact manifest'
 directory=Path(os.environ['SHARED_BANNER_REFERENCE_DIST'])
 actual=regular_manifest(directory)
 assert actual==data['files'],'Reviewed production artifact bytes changed'
 rows={}
 for rel in sorted(actual):
  if not rel.endswith('.html'):continue
  assert rel=='404.html' or rel=='index.html' or rel.endswith('/index.html'),'Unrecognized reference HTML route'
  doc=Page();doc.feed((directory/rel).read_text())
  assert len(doc.robots_values)==1,'Reference must have one robots declaration'
  robots=doc.robots_values[0]
  tokens={token.strip().casefold() for token in robots.split(',')}
  assert ('index' in tokens)!=('noindex' in tokens),'Reference has ambiguous indexability'
  error=rel=='404.html';url='/' if rel=='index.html' else '/'+rel.removesuffix('index.html')
  if error:
   assert 'noindex' in tokens and len(doc.canonical)<=1,'404 reference metadata mismatch'
   for value in doc.canonical:
    identity=url_identity(value);origin=url_identity(expected_origin)
    assert identity[:2]==origin[:2] and not identity[3] and not identity[4],'404 reference canonical origin/query/fragment mismatch'
  else:
   assert len(doc.canonical)==1,'Reference must have one canonical'
   canonical=url_identity(doc.canonical[0]);origin=url_identity(expected_origin)
   assert canonical[:2]==origin[:2] and not canonical[3] and not canonical[4],'Reference canonical origin/query/fragment mismatch'
   if canonical!=url_identity(expected_origin+url):
    # A merged, intrinsically noindex original may point at its actual same-origin target.
    # Both its bytes and the complete target map are bound by the immutable full artifact.
    assert 'noindex' in tokens,'Indexable reference canonical mismatch'
    route_map={url_identity(expected_origin+('/' if name=='index.html' else '/'+name.removesuffix('index.html'))):name for name in actual if name=='index.html' or name.endswith('/index.html')}
    assert canonical in route_map,'Original merged canonical target absent from full artifact'
  rows[rel]={'robots':robots,'canonical':doc.canonical,'excludeBanners':error or 'noindex' in tokens}
 assert 'index.html' in rows and '404.html' in rows,'Incomplete production reference'
 binding={'revision':expected_revision,'origin':expected_origin,'manifestSha256':expected_manifest,'artifactManifestSha256':expected_artifact,'routeIndexabilitySha256':sha(compact(rows)),'excludedHtml':[rel for rel,row in rows.items() if row['excludeBanners']]}
 return rows,binding

def preview_reference(production,binding):
 # Preview metadata is not inferred from a permissive robots allow-list. Authenticate
 # the unchanged original source's entire same-phase artifact using separate fixed pins.
 payload=Path(os.environ['SHARED_BANNER_PREVIEW_REFERENCE_MANIFEST']).read_bytes()
 assert sha(payload)==os.environ['SHARED_BANNER_PREVIEW_REFERENCE_MANIFEST_SHA256'],'Preview reference manifest hash mismatch'
 data=json.loads(payload)
 assert set(data)=={'schemaVersion','baselineRevision','previewOrigin','productionArtifactManifestSha256','artifactManifestSha256','files'},'Preview reference schema mismatch'
 assert data['schemaVersion']==1 and data['baselineRevision']==binding['revision'],'Preview reference revision changed'
 assert data['productionArtifactManifestSha256']==binding['artifactManifestSha256'],'Preview reference production binding changed'
 origin=os.environ['SHARED_BANNER_PREVIEW_REFERENCE_ORIGIN'];identity=url_identity(origin)
 assert identity[0] in ('http','https') and identity[1] and identity[2:]==('','',''),'Preview reference must be an origin'
 assert data['previewOrigin']==origin,'Preview reference origin changed'
 assert data['artifactManifestSha256']==os.environ['SHARED_BANNER_PREVIEW_REFERENCE_ARTIFACT_SHA256']==sha(compact(data['files'])),'Unbound preview full artifact'
 directory=Path(os.environ['SHARED_BANNER_PREVIEW_REFERENCE_DIST'])
 actual=regular_manifest(directory);assert actual==data['files'],'Original preview artifact bytes changed'
 assert {name for name in actual if name.endswith('.html')}==set(production),'Original preview route set changed'
 rows={}
 for rel,source in production.items():
  doc=Page();doc.feed((directory/rel).read_text())
  assert len(doc.robots_values)==1,'Preview reference robots must be singular'
  tokens={token.strip().casefold() for token in doc.robots_values[0].split(',')}
  assert 'noindex' in tokens and 'index' not in tokens,'Original preview must remain noindex'
  expected=[origin+value[len(binding['origin']):] for value in source['canonical']]
  assert [url_identity(x) for x in doc.canonical]==[url_identity(x) for x in expected],'Original preview canonical differs from bound production path'
  rows[rel]={'robots':doc.robots_values[0],'canonical':doc.canonical}
 return rows,{'manifestSha256':sha(payload),'artifactManifestSha256':data['artifactManifestSha256'],'revision':data['baselineRevision'],'origin':origin}

def inspect(root=Path('.'),manifest_path=None):
 dist=root/'dist';manifest=json.loads((manifest_path or root/'src/data/shared-banner-manifest.json').read_text());rows=[];errors=[]
 assert os.environ.get('SITE_INDEXABLE') in ('true','false'),'Explicit production/preview phase required'
 global_indexable=os.environ['SITE_INDEXABLE']=='true'
 baseline,binding=production_reference()
 preview,preview_binding=preview_reference(baseline,binding) if not global_indexable else (None,None)
 candidate_files=regular_manifest(dist)
 assert {name for name in candidate_files if name.endswith('.html')}==set(baseline),'Candidate route set changed'
 expected_origin=os.environ.get('SITE_URL','').rstrip('/')
 assert expected_origin and urlsplit(expected_origin).scheme in ('http','https'),'Explicit SITE_URL required'
 assert not global_indexable or expected_origin==binding['origin'],'Production origin changed'
 assert global_indexable or expected_origin==preview_binding['origin'],'Preview origin changed from exact original-phase reference'
 golden={'flower-message':'b8d973861fe81839ec7765d9dd506deb9d1055614c200479aa72a632cf0c5253','flower-budget':'bc782e91dadd7d07840ea9cbe6154fb21941dd7f9bf32c53bb2991bc301439df','flower-consultation':'4cae6c69e4c6549ed277fd3b2acc32c9a797a570de194bc48a6045b50f28283b'}
 assert {r['name']:r['sha256'] for r in manifest}==golden,'Reviewed banner asset pins changed'
 for row in manifest:
  p=dist/'images/shared-banners'/f"{row['name']}.webp"
  assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],f'Asset hash mismatch: {p}'
 for path in sorted(dist.rglob('*.html')):
  rel=path.relative_to(dist).as_posix();doc=Page();doc.feed(path.read_text());url='/' if rel=='index.html' else '/'+rel.removesuffix('index.html')
  is_error=rel=='404.html';noindex='noindex' in doc.meta.get('robots','')
  source=baseline[rel]
  expected=[] if source['excludeBanners'] else ['message','budget','consultation']
  issues=[]
  expected_robots=source['robots'] if global_indexable else preview[rel]['robots']
  if doc.robots_values!=[expected_robots]:issues.append('robots changed from bound production or explicit preview policy')
  if doc.banner_kinds!=expected:issues.append(f'banner set {doc.banner_kinds}; expected {expected}')
  if doc.headings.count(1)!=1:issues.append('expected exactly one H1')
  for previous,current in zip(doc.headings,doc.headings[1:]):
   if current>previous+1:issues.append(f'heading level jumps from H{previous} to H{current}')
  if not ''.join(doc.title).strip() or not doc.meta.get('description','').strip():issues.append('missing title or description')
  if not is_error and len(doc.canonical)!=1:issues.append('missing or duplicate canonical')
  expected_canonical=[expected_origin+value[len(binding['origin']):] for value in source['canonical']]
  if [url_identity(x) for x in doc.canonical]!=[url_identity(x) for x in expected_canonical]:issues.append('canonical differs from exact bound original origin/path/query/fragment')
  if len(doc.banner_images)!=len(expected):issues.append('each banner must contain exactly one image')
  if [kind for kind,img in doc.banner_images]!=expected:issues.append('each named banner must contain one image in order')
  if sum('/images/shared-banners/' in img.get('src','') for img in doc.images)!=len(expected):issues.append('unexpected shared banner image outside a banner figure')
  for variant,img in doc.banner_images:
   target=f'/images/shared-banners/flower-{variant}.webp'
   if img.get('src')!=target:issues.append(f'variant {variant} image must use {target}')
   if not (dist/target.lstrip('/')).is_file():issues.append(f'rendered image does not exist: {target}')
  for img in doc.images:
   if not img.get('alt','').strip():issues.append(f'missing image alt: {img.get("src")}')
   if '/images/shared-banners/' in img.get('src',''):
    if (img.get('width'),img.get('height'))!=('1774','887'):issues.append('wrong shared banner intrinsic ratio')
    if img.get('loading')!='lazy' or img.get('decoding')!='async':issues.append('shared banner loading attributes')
  for link in doc.links:
   if link.startswith('/') and not link.startswith('//'):
    p=unquote(urlsplit(link).path).lstrip('/');candidate=dist/p
    if not (candidate.is_file() or (candidate/'index.html').is_file()):issues.append(f'broken local link: {link}')
  if issues:errors.append({'path':url,'issues':issues})
  rows.append({'path':url,'errorPage':is_error,'noindex':noindex,'bannerKinds':doc.banner_kinds,'h1':doc.headings.count(1),'h2':doc.headings.count(2),'h3':doc.headings.count(3),'headings':doc.headings,'images':len(doc.images),'canonical':doc.canonical,'issues':issues})
 report={'productionReference':binding,'previewReference':preview_binding,'customerHtml':sum(not x['errorPage'] for x in rows),'errorHtml':sum(x['errorPage'] for x in rows),'banners':sum(len(x['bannerKinds']) for x in rows),'files':rows,'errors':errors,'assetSha256':{x['name']:x['sha256'] for x in manifest}}
 (root/'shared-banner-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 assert not errors,json.dumps(errors,ensure_ascii=False)
 print(f'SHARED BANNER QA: {report["customerHtml"]} customer pages, {report["banners"]} banners; headings, alt, exact assets and links checked')
 return report
if __name__=='__main__':inspect()
