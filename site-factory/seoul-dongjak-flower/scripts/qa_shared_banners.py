#!/usr/bin/env python3
"""Inspect rendered production HTML; source template assertions alone are insufficient."""
from pathlib import Path
from html.parser import HTMLParser
import os,json,hashlib
from urllib.parse import urlsplit,unquote
class Page(HTMLParser):
 def __init__(self):super().__init__();self.headings=[];self.images=[];self.meta={};self.links=[];self.canonical=[];self.title=[];self.in_title=False;self.banner_kinds=[];self.banner_images=[];self.current_banner=None;self.figure_depth=0;self.banner_captions=0;self.visible_text=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag in ['h1','h2','h3','h4','h5','h6']:self.headings.append(int(tag[1]))
  if tag=='figure':self.figure_depth+=1
  if 'data-shared-flower-banner' in a:self.current_banner=a['data-shared-flower-banner']
  if tag=='figcaption' and self.current_banner is not None:self.banner_captions+=1
  if tag=='img':
   self.images.append(a)
   if self.current_banner is not None:self.banner_images.append((self.current_banner,a))
  if tag=='meta':self.meta[a.get('name','')]=a.get('content','')
  if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href',''))
  if tag=='a':self.links.append(a.get('href',''))
  if tag=='title':self.in_title=True
  if 'data-shared-flower-banner' in a:self.banner_kinds.append(a['data-shared-flower-banner'])
 def handle_endtag(self,tag):
  if tag=='title':self.in_title=False
  if tag=='figure':
   self.figure_depth-=1
   if self.figure_depth==0:self.current_banner=None
 def handle_data(self,s):
  self.visible_text.append(s)
  if self.in_title:self.title.append(s)
def inspect(root=Path('.'),manifest_path=None):
 dist=root/'dist';manifest=json.loads((manifest_path or root/'src/data/shared-banner-manifest.json').read_text());rows=[];errors=[]
 global_indexable=os.environ.get('SITE_INDEXABLE')=='true'
 architecture_path=root/'src/data/architecture.json'
 thin_hubs={h['url'] for h in json.loads(architecture_path.read_text())['hubs'] if h['children']<3} if architecture_path.exists() else set()
 expected_origin=os.environ.get('SITE_URL','').rstrip('/')
 assert not global_indexable or expected_origin.startswith('https://'),'Production SITE_URL is required'
 golden={'flower-message':'a5ecdeb1914566a32d45b084351e2782fc8b234e9a4fbb8635a60a9921cac5f5','flower-budget':'081198095eb005603721be7c778f4d477f4dd93dcf96f0c261f18bf06bb91421','flower-consultation':'d6654aa44c365f64e330d0be2042972d3320fad54231425aaffca1dfdcd25ebc'}
 assert {r['name']:r['sha256'] for r in manifest}==golden,'Reviewed banner asset pins changed'
 for row in manifest:
  p=dist/'images/shared-banners'/f"{row['name']}.webp"
  assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],f'Asset hash mismatch: {p}'
  assert p.stat().st_size==row['bytes'] and (row['width'],row['height'])==(1774,887),'Banner metadata drift'
 for path in sorted(dist.rglob('*.html')):
  rel=path.relative_to(dist).as_posix();doc=Page();doc.feed(path.read_text());url='/' if rel=='index.html' else '/'+rel.removesuffix('index.html')
  is_error=rel=='404.html';noindex='noindex' in doc.meta.get('robots','')
  expected=[] if is_error or url in thin_hubs or (global_indexable and noindex) else ['message','budget','consultation']
  issues=[]
  if doc.banner_captions:issues.append('shared banner caption reintroduced')
  if '꽃이랑 공통 안내 이미지 · 실제 판매상품 사진이 아닌 AI 생성 이미지입니다.' in ''.join(doc.visible_text):issues.append('removed shared banner disclosure reintroduced')
  if doc.banner_kinds!=expected:issues.append(f'banner set {doc.banner_kinds}; expected {expected}')
  if doc.headings.count(1)!=1:issues.append('expected exactly one H1')
  for previous,current in zip(doc.headings,doc.headings[1:]):
   if current>previous+1:issues.append(f'heading level jumps from H{previous} to H{current}')
  if not ''.join(doc.title).strip() or not doc.meta.get('description','').strip():issues.append('missing title or description')
  if not is_error and len(doc.canonical)!=1:issues.append('missing or duplicate canonical')
  if not is_error and expected_origin and doc.canonical!=[expected_origin+url]:issues.append('canonical must match exact origin and route')
  if len(doc.banner_images)!=len(expected):issues.append('each banner must contain exactly one image')
  if [kind for kind,img in doc.banner_images]!=expected:issues.append('each named banner must contain one image in order')
  if sum('/images/shared-banners/' in img.get('src','') for img in doc.images)!=len(expected):issues.append('unexpected shared banner image outside a banner figure')
  for variant,img in doc.banner_images:
   target=f'/images/shared-banners/flower-{variant}.webp'
   if img.get('src')!=target:issues.append(f'variant {variant} image must use {target}')
   if not img.get('alt','').endswith(' 전화 1844-0644.'):issues.append('shared banner alt phone missing or changed')
   if '실제 판매상품 사진이 아닌 AI 생성 이미지' in img.get('alt',''):issues.append('removed shared disclosure reintroduced in alt')
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
 report={'customerHtml':sum(not x['errorPage'] for x in rows),'errorHtml':sum(x['errorPage'] for x in rows),'banners':sum(len(x['bannerKinds']) for x in rows),'files':rows,'errors':errors,'assetSha256':{x['name']:x['sha256'] for x in manifest}}
 (root/'shared-banner-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 assert not errors,json.dumps(errors,ensure_ascii=False)
 print(f'SHARED BANNER QA: {report["customerHtml"]} customer pages, {report["banners"]} banners; headings, alt, exact assets and links checked')
 return report
if __name__=='__main__':inspect()
