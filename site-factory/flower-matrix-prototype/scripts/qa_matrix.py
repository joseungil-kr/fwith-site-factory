from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse,unquote,urljoin
import json,os,xml.etree.ElementTree as ET

class Doc(HTMLParser):
 def __init__(self,text):
  super().__init__(convert_charrefs=True);self.h1=0;self.meta={};self.canonical=[];self.links=[];self.images=[];self.in_title=False;self.title='';self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='h1':self.h1+=1
  if tag=='title':self.in_title=True
  if tag=='meta':self.meta[a.get('name',a.get('property'))]=a.get('content','')
  if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href',''))
  if tag=='a':self.links.append(a.get('href',''))
  if tag=='img':self.images.append(a)
 def handle_endtag(self,tag):
  if tag=='title':self.in_title=False
 def handle_data(self,data):
  if self.in_title:self.title+=data

def read(root,p):return json.loads((root/p).read_text())
def main(root=Path('.')):
 instances=read(root,'src/data/site-instances.json');regions=read(root,'src/data/regions-matrix.json');groups=read(root,'src/data/product-groups.json');products=read(root,'src/data/product-sources.json');config=read(root,'src/data/site-config.json')
 key=os.environ.get('SITE_INSTANCE') or config['defaultInstance'];instance=next((x for x in instances if x['key']==key),None);assert instance,'Unknown SITE_INSTANCE'
 base=(os.environ.get('SITE_URL') or instance['domain']).rstrip('/');assert urlparse(base).scheme=='https'
 if os.environ.get('SITE_INDEXABLE')=='true':assert instance['deployable'] is True and config['productionApproved'] is True,'Prototype cannot become indexable before explicit promotion'
 rmap={x['key']:x for x in regions};gmap={x['key']:x for x in groups};enabled_regions=[rmap[x] for x in instance['enabledRegions']];enabled_groups=[gmap[x] for x in instance['enabledProductGroups']]
 detail=[f"/{r['slug']}/{g['slug']}/" for r in enabled_regions for g in enabled_groups];region_hubs=[f"/{r['slug']}/" for r in enabled_regions];product_hubs=[f"/products/{g['slug']}/" for g in enabled_groups];expected={'/',*detail,*region_hubs,*product_hubs}
 assert len(detail)==20 and len(expected)==30
 dist=root/'dist';docs={}
 for url in sorted(expected):
  file=dist/(url.strip('/') or '.')/'index.html'
  if url=='/':file=dist/'index.html'
  assert file.is_file(),f'Missing matrix route {url}'
  doc=Doc(file.read_text());docs[url]=doc
  assert doc.h1==1,f'Expected one H1 {url}'
  assert doc.title.strip(),f'Missing title {url}'
  assert doc.meta.get('description','').strip(),f'Missing description {url}'
  assert doc.canonical==[base+url],f'Canonical mismatch {url}: {doc.canonical}'
  assert 'noindex' in doc.meta.get('robots',''),f'Prototype must remain noindex {url}'
  assert doc.meta.get('og:url')==base+url,f'OG URL mismatch {url}'
  for img in doc.images:
   assert img.get('alt','').strip(),f'Empty image alt {url}'
  for href in doc.links:
   if not href or href.startswith(('tel:','mailto:','#')):continue
   target=urlparse(urljoin(base+url,href))
   if target.netloc!=urlparse(base).netloc:continue
   path=unquote(target.path)
   assert path in expected,f'Broken/internal cross-instance route {url}->{path}'
 for instance2 in instances:
  if instance2['key']!=key:
   forbidden=instance2['domain'].rstrip('/')
   for url,doc in docs.items():
    assert forbidden not in (doc.canonical+doc.links),f'Clone origin leaked into {url}'
 for p in products:
  assert p['sourceUrl']==f"https://fwith.co.kr/shop/item.php?it_id={p['code']}"
  if p['priceVerifiedAt'] is None:assert 'needs-current-price-recheck' in p['verification']
 sitemap=set()
 for file in dist.glob('sitemap-*.xml'):
  tree=ET.parse(file)
  for loc in tree.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
   if loc.text and not loc.text.endswith('.xml'):sitemap.add(unquote(loc.text))
 assert sitemap=={base+u for u in expected},f'Sitemap matrix mismatch: {sitemap ^ {base+u for u in expected}}'
 print(f'MATRIX QA PASSED: instance={key}, detail=20, total_routes=30, origin={base}, noindex=true')
if __name__=='__main__':main()
