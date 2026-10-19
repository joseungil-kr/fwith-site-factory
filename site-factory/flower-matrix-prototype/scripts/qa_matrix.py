from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse,unquote,urljoin
import json,os,re,xml.etree.ElementTree as ET

class Doc(HTMLParser):
 def __init__(self,text):
  super().__init__(convert_charrefs=True);self.h1=0;self.headings=[];self.meta={};self.canonical=[];self.links=[];self.images=[];self.in_title=False;self.title='';self.visible=[];self.ignored=0;self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag in ('script','style'):self.ignored+=1
  if re.fullmatch(r'h[1-6]',tag):
   level=int(tag[1]);self.headings.append(level)
   if level==1:self.h1+=1
  if tag=='title':self.in_title=True
  if tag=='meta':self.meta[a.get('name',a.get('property'))]=a.get('content','')
  if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href'))
  if tag=='a':self.links.append(a.get('href',''))
  if tag=='img':self.images.append(a)
 def handle_endtag(self,tag):
  if tag=='title':self.in_title=False
  if tag in ('script','style'):self.ignored=max(0,self.ignored-1)
 def handle_data(self,data):
  if self.in_title:self.title+=data
  if not self.ignored and data.strip():self.visible.append(re.sub(r'\s+',' ',data.strip()))

def read(root,p):return json.loads((root/p).read_text())
def main(root=Path('.')):
 instances=read(root,'src/data/site-instances.json');regions=read(root,'src/data/regions-matrix.json');groups=read(root,'src/data/product-groups.json');products=read(root,'src/data/product-sources.json');config=read(root,'src/data/site-config.json')
 key=os.environ.get('SITE_INSTANCE') or config['defaultInstance'];instance=next((x for x in instances if x['key']==key),None);assert instance,'Unknown SITE_INSTANCE'
 base=(os.environ.get('SITE_URL') or instance['domain']).rstrip('/');parsed_base=urlparse(base);assert parsed_base.scheme=='https' and parsed_base.netloc
 if os.environ.get('SITE_INDEXABLE')=='true':assert instance['deployable'] is True and config['productionApproved'] is True,'Prototype cannot become indexable before explicit promotion'
 rmap={x['key']:x for x in regions};gmap={x['key']:x for x in groups};enabled_regions=[rmap[x] for x in instance['enabledRegions']];enabled_groups=[gmap[x] for x in instance['enabledProductGroups']]
 detail=[f"/{r['slug']}/{g['slug']}/" for r in enabled_regions for g in enabled_groups];region_hubs=[f"/{r['slug']}/" for r in enabled_regions];product_hubs=[f"/products/{g['slug']}/" for g in enabled_groups];expected={'/',*detail,*region_hubs,*product_hubs}
 assert len(detail)==len(enabled_regions)*len(enabled_groups)
 assert len(expected)==1+len(detail)+len(region_hubs)+len(product_hubs)
 dist=root/'dist';docs={};titles=set();descriptions=set()
 for url in sorted(expected):
  file=dist/'index.html' if url=='/' else dist/url.strip('/')/'index.html'
  assert file.is_file(),f'Missing matrix route {url}'
  doc=Doc(file.read_text());docs[url]=doc
  visible=' '.join(doc.visible)
  assert doc.h1==1,f'Expected one H1 {url}'
  assert doc.title.strip() and doc.title not in titles,f'Duplicate/missing title {url}';titles.add(doc.title)
  desc=doc.meta.get('description','').strip();assert desc and desc not in descriptions,f'Duplicate/missing description {url}';descriptions.add(desc)
  assert doc.canonical==[base+url],f'Canonical mismatch {url}: {doc.canonical}'
  assert 'noindex' in doc.meta.get('robots',''),f'Prototype must remain noindex {url}'
  assert doc.meta.get('og:url')==base+url,f'OG URL mismatch {url}'
  assert doc.meta.get('og:image'),f'Missing OG image {url}'
  og_host=urlparse(doc.meta['og:image']).hostname
  assert og_host in {parsed_base.hostname,'fwith.co.kr'},f'Untrusted OG image host {url}: {og_host}'
  assert '자주 묻는 질문' in visible,f'Missing visible FAQ {url}'
  assert '1844-0644' in visible,f'Missing visible phone CTA {url}'
  assert re.search(r'\d{1,3}(?:,\d{3})원',visible),f'Missing visible verified price {url}'
  assert '추가배송비' in visible or '추가 배송비' in visible,f'Missing delivery condition {url}'
  assert 'example.invalid' not in visible and 'prototype-a' not in visible and 'prototype-b' not in visible,f'Test label leaked into customer copy {url}'
  for previous,current in zip(doc.headings,doc.headings[1:]):assert current<=previous+1,f'Heading jump H{previous}->H{current}: {url}'
  assert doc.images,f'Missing product image {url}'
  for img in doc.images:
   assert img.get('alt','').strip(),f'Empty image alt {url}'
   src=img.get('src','');u=urlparse(src)
   if u.scheme:
    assert u.scheme=='https' and u.hostname=='fwith.co.kr',f'Unexpected remote image {url}: {src}'
   else:
    assert src.startswith('/'),f'Unexpected relative image {url}: {src}'
    assert (root/'public'/src.lstrip('/')).is_file(),f'Missing local asset {src}'
  for href in doc.links:
   if not href or href.startswith(('tel:','mailto:','#')):continue
   target=urlparse(urljoin(base+url,href))
   if target.netloc!=parsed_base.netloc:continue
   path=unquote(target.path)
   assert path in expected,f'Broken/internal cross-instance route {url}->{path}'
 for instance2 in instances:
  if instance2['key']!=key:
   forbidden=instance2['domain'].rstrip('/')
   for url,doc in docs.items():
    assert forbidden not in ''.join(doc.canonical+doc.links+[doc.meta.get('og:url',''),doc.meta.get('og:image','')]),f'Clone origin leaked into {url}'
 for p in products:
  assert p['sourceUrl']==f"https://fwith.co.kr/shop/item.php?it_id={p['code']}"
  assert p['priceVerifiedAt']=='2026-10-20'
 sitemap=set()
 for file in dist.glob('sitemap-*.xml'):
  tree=ET.parse(file)
  for loc in tree.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
   if loc.text and not loc.text.endswith('.xml'):sitemap.add(unquote(loc.text))
 assert sitemap=={base+u for u in expected},f'Sitemap matrix mismatch: {sitemap ^ {base+u for u in expected}}'
 report={'schemaVersion':1,'instance':key,'origin':base,'regions':len(enabled_regions),'productGroups':len(enabled_groups),'detailPages':len(detail),'totalRoutes':len(expected),'titlesUnique':True,'descriptionsUnique':True,'noindex':True,'crossInstanceLeak':False}
 (root/'matrix-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('MATRIX QA PASSED: '+json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
