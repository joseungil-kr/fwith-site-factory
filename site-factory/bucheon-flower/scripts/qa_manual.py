"""Same rendered quality checks as frozen static QA, across a manually combined graph."""
import json,os,hashlib,re,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse,urljoin,unquote
from qa_static import Document,check_customer_output,check_customer_journey,check_rendered_intent,check_rendered_catalog
root=Path('.');data=root/'src/data';dist=root/'dist'
read=lambda name:json.loads((data/(name+'.json')).read_text())
original=read('pages');manual=read('manual-pages');pages=original+manual;arch=read('architecture');truth=read('business-truth');products=read('products');prov=read('manual-provenance')
base=(os.environ.get('SITE_URL') or read('site-config')['previewUrl']).rstrip('/');indexable=os.environ.get('SITE_INDEXABLE')=='true'
counts={h['category']:sum(p['category']==h['category'] for p in pages) for h in arch['hubs']}
expected={'/'}|{p['url'] for p in pages}|{h['url'] for h in arch['hubs'] if counts[h['category']]}
thin={h['url'] for h in arch['hubs'] if counts[h['category']]<3};docs={};incoming={u:set() for u in expected};titles=set();descriptions=set()
for url in expected:
 file=dist/url.strip('/')/'index.html';assert file.exists(),url;d=Document(file.read_text());docs[url]=d
 assert d.h1==1 and d.title and d.title not in titles,url;titles.add(d.title)
 description=d.meta.get('description','');assert description and description not in descriptions,url;descriptions.add(description)
 assert d.canonical==[base+url],url
 robots=('noindex,follow' if url in thin else 'index,follow') if indexable else 'noindex,nofollow,noarchive';assert d.meta.get('robots')==robots,(url,d.meta.get('robots'))
 for f in ['og:title','og:description','og:url','twitter:card']:assert d.meta.get(f),(url,f)
 assert truth['phoneHref'] in d.links and any(x.startswith(truth['onlineOrderUrl']) for x in d.links),url
 for img in d.images:assert img.get('alt') and img['src'].startswith('/') and (root/'public'/img['src'].lstrip('/')).is_file(),(url,img)
 check_customer_output(d,url);check_rendered_catalog(d,url,products)
 for href in d.links:
  if href.startswith(('tel:','mailto:','#')):continue
  target=urlparse(urljoin(base+url,href))
  if target.netloc==urlparse(base).netloc:
   path=unquote(target.path);assert path in expected,(url,path)
   if path!=url:incoming[path].add(url)
for p in pages:
 d=docs[p['url']];check_customer_journey(d,p,pages);check_rendered_intent(d,p,products)
 assert d.images[0]['src'].startswith('/images/products/'),p['url']
 if p in original:assert d.snapshots==[p['snapshotId']],p['url']
 else:
  t=(dist/p['url'].strip('/')/'index.html').read_text();assert not d.snapshots and 'data-publication-mode="manual-user-request"' in t and ('data-manual-release-id="'+prov['manualReleaseId']+'"') in t,p['url']
  assert ' '.join(d.first_answer)==p['firstAnswer'],p['url']
for url in expected-{'/'}:assert incoming[url],url
locations=set()
for file in dist.glob('sitemap-*.xml'):
 for loc in ET.parse(file).iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
  if not (loc.text or '').endswith('.xml'):locations.add(unquote(loc.text or ''))
assert locations=={base+u for u in expected-thin},locations^{base+u for u in expected-thin}
assert 'noindex' in Document((dist/'404.html').read_text()).meta.get('robots','')
report={'status':'PASS','details':len(pages),'manualCandidates':len(manual),'htmlRoutes':len(expected),'sitemapRoutes':len(locations),'allHaveInbound':True,'contentHash':prov['contentHash'],'independentReview':prov['independentReview']['status'],'candidateValidationOnly':True}
Path('../evidence/manual-rendered-qa.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
headers=(dist/'_headers').read_text();robots=(dist/'robots.txt').read_text()
assert ('X-Robots-Tag: noindex, nofollow, noarchive' not in headers) if indexable else ('X-Robots-Tag: noindex, nofollow, noarchive' in headers)
assert ('Allow: /' in robots and 'Disallow: /' not in robots) if indexable else 'Disallow: /' in robots
