"""Gwanak sealed-input → runtime → static-HTML contract.

This is LOCAL inspection only. It never launches a browser, contacts a site, or
claims screen, accessibility, deployment, ownership, search or fulfilment proof.
Inherited regional gates are intentionally unchanged.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
from collections import Counter
import hashlib, json, os, re, xml.etree.ElementTree as ET
from release_mode import resolve_mode, expected_robots, validate_search_output
from banner_phone_amendment import load_amendment, effective_assets

PINS = {
 'acceptance.json': '60a27c02c52321f0bec102f3c2a8dc0a4f97f039ecdadf1917b56a88ca78d2f9',
 'approved-visible-surface.json': 'f9d0adaacd2601d4c97d0f45195f14b8b327ae4d1763764f07c994b897029f0e',
 'approved-assets.json': 'ccbfc6062dbdfb0649e86ea1200f64fa9f13f8df37f652d5c3cc4920cb7725a8',
 'runtime-input-bindings.json': 'f3b7a1b40d56145c4e0b8ad293041b1b5b9a05847fef752ecd072bdc69ee7419',
 'interface-copy-addendum.json': 'b1f0d37532998454a6098f8118b5f9b4d8b7069f6d089580756eb7569449fcca',
 'inputs/copy/article-copy.rev4.json': 'e51f8afdf54145750ce88e3f9c35924ec11671a047090f9d457e23eeacdd5969',
 'inputs/copy/common-visible-copy.rev3.json': 'a433bc613087ad61ce4f2a044e6a06e827b5fc726db141c3b9a31ea19c9ee96b',
 'inputs/plan/fixed-plan.json': 'e68fa31eee4b3d375fb5a73cf8652828ef01e8c34ab6648bc0d6c44e8786a522',
 'inputs/plan/candidate-inventory.json': '21c65e56b849cb9c7f09be8676e8673111bfd69c9f83709607d94f6b2ce64634',
 'inputs/plan/membership.json': '5327b48e818dd13094d3cd9ee1b6e343c810c18d9f91567d80c114caed5f21a8',
}
SITE='seoul-gwanak-flower-direct'
SCOPE='seoul-gwanak-direct-independent-preparation-20261013'
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

def norm(value): return ' '.join(value.split())
def sha(value): return hashlib.sha256(value).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def descendants(node):
 for child in node['children']:
  yield child
  yield from descendants(child)
def strings(value):
 if isinstance(value,str): yield value
 elif isinstance(value,list):
  for child in value: yield from strings(child)
 elif isinstance(value,dict):
  for child in value.values(): yield from strings(child)

def matches(node,tag=None,key=None,value=None):
 return (tag is None or node['tag']==tag) and (key is None or key in node['attrs'] and (value is None or node['attrs'][key]==value))

def within(node,tag=None,key=None,value=None): return [n for n in descendants(node) if matches(n,tag,key,value)]
def hidden(node):
 while node:
  a=node['attrs'];classes=a.get('class','').split()
  if node['tag'] in ('details','template','script','style') or 'hidden' in a or 'inert' in a or a.get('aria-hidden')=='true' or any(c in classes for c in ('hidden','sr-only','visually-hidden')) or re.search(r'(display\s*:\s*none|visibility\s*:\s*hidden|content-visibility\s*:\s*hidden)',a.get('style','')): return True
  node=node['parent']
 return False

class Surface(HTMLParser):
 def __init__(self,html):
  super().__init__(convert_charrefs=True);self.nodes=[];self.stack=[];self.text_events=[];self.feed(html)
 def handle_starttag(self,tag,attrs):
  assert len(attrs)==len(dict(attrs)),f'Duplicate HTML attribute: {tag}'
  node={'tag':tag,'attrs':dict(attrs),'text':'','children':[],'parent':self.stack[-1] if self.stack else None,'i':len(self.nodes)};self.nodes.append(node)
  if self.stack:self.stack[-1]['children'].append(node)
  if tag not in VOID:self.stack.append(node)
 def handle_startendtag(self,tag,attrs): self.handle_starttag(tag,attrs);self.handle_endtag(tag)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,-1,-1):
   if self.stack[i]['tag']==tag:del self.stack[i:];break
 def handle_data(self,text):
  for node in self.stack: node['text']+=text
  if self.stack and norm(text):self.text_events.append((self.stack[-1],norm(text)))
 def where(self,tag=None,key=None,value=None):return [n for n in self.nodes if matches(n,tag,key,value)]
 def cls(self,cls):return [n for n in self.nodes if cls in n['attrs'].get('class','').split()]
 def text(self,tag):return [norm(n['text']) for n in self.where(tag)]

def exactly(doc,tag,text,count=1):
 nodes=[n for n in doc.where(tag) if norm(n['text'])==norm(text)]
 assert len(nodes)==count,f'Exact {tag} missing/duplicated: {text[:90]}'
 assert not any(hidden(n) for n in nodes),f'Approved {tag} is hidden: {text[:90]}'
 return nodes

def link_exact(doc,label,href,count=None,scope=None):
 nodes=within(scope,'a') if scope else doc.where('a')
 found=[n for n in nodes if norm(n['text'])==norm(label) and n['attrs'].get('href')==href]
 assert len(found)==count if count is not None else bool(found),f'Approved CTA/source missing/duplicated: {label} -> {href}'
 assert not any(hidden(n) for n in found),f'Approved link hidden: {label}'
 return found

def check_metadata(doc,title,h1,description,route,base,indexable=False):
 assert doc.text('title')==[title],f'SEO title drift: {route}'
 assert doc.text('h1')==[h1],f'H1 drift: {route}'
 meta={n['attrs'].get('name',n['attrs'].get('property')):n['attrs'].get('content') for n in doc.where('meta')}
 assert meta.get('description')==description,f'Meta description drift: {route}'
 assert meta.get('robots')==expected_robots(route,indexable),f'Mode-specific robots drift: {route}'
 canon=doc.where('link','rel','canonical')
 if route=='/404.html':
  assert not canon,'404 canonical forbidden'
  assert not any(k and k.startswith(('og:','twitter:')) for k in meta),'404 social tags forbidden'
  assert not doc.where('script','type','application/ld+json'),'404 schema forbidden'
 else:
  assert [n['attrs'].get('href') for n in canon]==[base+route],f'Canonical drift: {route}'
  for key,value in [('og:title',title),('og:description',description),('og:url',base+route),('twitter:title',title),('twitter:description',description)]:
   assert meta.get(key)==value,f'Social metadata drift: {route} {key}'
 return meta

def inspect(root=Path('.'),write=True,quiet=False):
 root=Path(root);data=root/'src/data';dist=root/'dist';sealed=data/'gwanak-approved'
 for path,digest in PINS.items():
  f=sealed/path;assert f.is_file(),f'Sealed approval missing: {path}'
  assert sha(f.read_bytes())==digest,f'Sealed approval byte drift: {path}'
 surface=read(sealed/'approved-visible-surface.json');binding=read(sealed/'runtime-input-bindings.json')
 original=read(sealed/'inputs/copy/article-copy.rev4.json')['articles'];common=read(sealed/'inputs/copy/common-visible-copy.rev3.json')['common'];assets=read(sealed/'approved-assets.json')['assets']
 amendment=load_amendment(root);assets=effective_assets(root,assets)
 copy=read(data/'gwanak-copy.json');pages=read(data/'pages.json');products=read(data/'products.json');coverage=read(data/'region-coverage.json');config=read(data/'site-config.json');architecture=read(data/'architecture.json')
 assert copy['articles']==original,'Runtime approved articles drift'
 assert copy['common']==common,'Runtime approved common copy drift'
 assert len(pages)==2 and [p['url'] for p in pages]==[x['url'] for x in original],'Runtime N2 route/card denominator drift'
 assert config['siteKey']==SITE and architecture['siteKey']==SITE and coverage['siteKey']==SITE,'Runtime siteKey drift'
 assert coverage['scopeKey']==SCOPE,'Runtime scope drift'
 for name in ['region-policy','publish-manifest','page-map','direct-checkpoint']:
  obj=read(data/(name+'.json'));assert obj['siteKey']==SITE,f'Active technical siteKey drift: {name}'
  if 'scopeKey' in obj:assert obj['scopeKey']==SCOPE,f'Active technical scope drift: {name}'
 mode=resolve_mode(root);indexable=mode['indexable']
 hub=next(h for h in architecture['hubs'] if h['category']=='regions')
 assert hub['children']==2 and hub['indexable'] is False and hub['menuVisible'] is False,'Thin directory N/eligibility drift'
 assert [p['officialSku'] for p in products]==[p['sku'] for p in common['productCards']],'Catalog SKU/order drift'
 bysku={p['officialSku']:p for p in products};bykey={p['key']:p for p in products};approvedsku={p['sku']:p for p in common['productCards']}
 assert len(bykey)==8,'Duplicate product key'
 for sku,approved in approvedsku.items():
  p=bysku[sku]
  for key,expected in [('name',approved['name']),('price',approved['basicPriceKRW']),('priceLabel',approved['priceLabel']),('desc',approved['description']),('imageAlt',approved['imageAlt']),('ctaLabel',approved['cta']['label']),('orderUrl',approved['cta']['href']),('sourceUrl',approved['cta']['href'])]:
   assert p.get(key)==expected,f'Runtime SKU {sku} {key} drift'
 for approved,page,b in zip(original,pages,binding['articles']):
  assert page['scopeKey']==SCOPE,'Page scope drift'
  for key in ['title','h1','firstAnswer','cardSummary','faq','sourceNote','sections','sourceLinks','primaryCta','relatedLink','contentMarkdown']:
   assert page.get(key)==approved[key],f'Runtime article {key} drift: {approved["id"]}'
  assert page['description']==approved['metaDescription'],'Runtime description drift'
  assert page['candidateIds']==b['candidateIds'],'Runtime candidate assignment drift'
  assert [bykey[k]['officialSku'] for k in page['productCardKeys']]==b['productSkus'],'Runtime article SKU binding drift'
  assert page['intentKey']==b['intentKey'],'Runtime article intent drift'
  expected_facilities=[a for a in binding['facilityDestinations'] if a['articleId']==approved['id']]
  assert [a['candidateId'] for a in page['facilityAnchors']]==[a['candidateId'] for a in expected_facilities],'Runtime facility/occasion classification drift'
  for actual,expected in zip(page['facilityAnchors'],expected_facilities):
   assert actual['unitKey']==('관악구/법정동/'+expected['legalDong'] if expected['legalDong'] else None),'Runtime facility unit drift'
   for key in ['anchor','heading','href']: assert actual[key]==expected[key],f'Runtime facility {key} drift'
 geography=binding['geography'];units=coverage['units'];admins=coverage['administrativeCrosswalk']
 assert [(u['legalCode'],u['name']) for u in units]==[(u['code'],u['name']) for u in geography['legal']],'Legal geography drift'
 assert [(a['administrativeCode'],a['name']) for a in admins]==[(a['code'],a['name']) for a in geography['administrative']],'Administrative geography drift'
 expected_relations=[(r['administrativeCode'],'관악구/법정동/'+r['legalName']) for r in geography['relationships']]
 assert [(a['administrativeCode'],r['unitKey']) for a in admins for r in a['relations']]==expected_relations,'Administrative relationships drift'
 assert len(coverage['facilities'])==4 and len(coverage['buyerOccasions'])==1,'Physical facility/buyer occasion count drift'
 for f,expected in zip(coverage['facilities'],binding['facilityDestinations']):
  assert f['facilityKey']==expected['candidateId'] and f['address']==expected['address'],'Facility candidate/address drift'
  assert f['unitKey']==('관악구/법정동/'+expected['legalDong'] if expected['legalDong'] else None),'Facility legal unit drift (professor must stay unassigned)'
  assert f.get('administrativeCode') is None and f.get('administrativeDong') is None,'Administrative facility assignment forbidden'
 occasion=coverage['buyerOccasions'][0]
 assert occasion['contextKey']=='gwanak-opening-occasion' and occasion['contextType']=='buyer-occasion','Buyer occasion misclassified'
 assert all(occasion.get(k) is None for k in ['unitKey','legalCode','administrativeCode','physicalAddress']),'Buyer occasion fabricated geography'
 expected={'index.html','regions/index.html','404.html'}|{p['url'].strip('/')+'/index.html' for p in original}
 actual={p.relative_to(dist).as_posix() for p in dist.rglob('*.html')}
 assert actual==expected,'Unexpected standalone or missing HTML route'
 docs={rel:Surface((dist/rel).read_text()) for rel in sorted(expected)};base=mode['origin']
 asset_map={a['proposedRuntimePath'].removeprefix('public'):a for a in assets}
 for a in assets:
  path=a['proposedRuntimePath'].removeprefix('public/')
  for basepath in [root/'public',dist]:
   f=basepath/path;assert f.is_file(),f'Missing approved asset: {f}'
   assert sha(f.read_bytes())==a['snapshot']['sha256'] and f.stat().st_size==a['snapshot']['bytes'],f'Actual approved image byte/hash drift: {f}'
 allowed_strings=list(strings(surface['common']))+list(strings(surface['articles']))+list(strings(read(sealed/'interface-copy-addendum.json')['customerLabels']))+[r['name'] for r in geography['legal']+geography['administrative']]+['관악구']
 allowed_strings=[norm(s) for s in allowed_strings]
 ids={};reports=[]
 for rel,doc in docs.items():
  assert len(doc.where('body'))==1,'Exactly one document body required'
  for node in doc.nodes:
   assert not any(k.lower().startswith('on') for k in node['attrs']),'Inline event handler forbidden'
   assert node['tag'] not in ['iframe','object','embed','frame','frameset','form','base'],'Unapproved executable/embedded element'
   if node['tag']=='script':assert node['attrs']=={'type':'application/ld+json'},'Executable script forbidden'
   for key in ['href','src','action','formaction','poster','xlink:href']:
    if key in node['attrs']:
     value=node['attrs'][key] or '';assert not re.search(r'[\x00-\x20]',value),'Control/whitespace in URL forbidden'
     parsed=urlsplit(value);assert parsed.scheme in ('','https','tel') and not value.startswith('//'),'Unsafe URL protocol forbidden'
  visible_body=norm(doc.where('body')[0]['text'])
  assert norm(amendment['removedVisibleCaption']) not in visible_body,'Removed common-banner caption reintroduced'
  ids[rel]=[n['attrs']['id'] for n in doc.where(key='id')]
  assert len(ids[rel])==len(set(ids[rel])),f'Duplicate HTML id: {rel}'
  for node,text in doc.text_events:
   if node['tag'] in ['script','style','title'] or any(n['tag']=='head' for n in ancestor_nodes(node)):continue
   if not re.search(r'[\w가-힣]',text):continue
   assert any(text in allowed for allowed in allowed_strings),f'Unapproved visible text: {rel}: {text[:120]}'
   assert not re.search(r'영등포|동작구|금천구|구로구|yeongdeungpo|dongjak|geumcheon|guro',text,re.I),f'Old region visible text: {rel}'
  for img in doc.where('img'):
   a=img['attrs'];assert not hidden(img),f'Rendered approved image hidden: {rel}'
   assert a.get('src') in asset_map,f'Unapproved image source: {rel}: {a.get("src")}'
   approved=asset_map[a['src']]
   assert a.get('alt')==approved['alt'],f'Image alt drift: {rel}: {a["src"]}'
   assert (a.get('width'),a.get('height'))==tuple(map(str,approved['dimensions'])),f'Image dimensions drift: {rel}'
  for link in doc.where('a'):
   href=link['attrs'].get('href','');assert href,'Empty href'
   u=urlsplit(href)
   assert u.scheme in ('','https','tel'),'Unexpected unsafe/unsupported link scheme'
  accessibility=read(sealed/'interface-copy-addendum.json')['customerLabels']['accessibility']
  link_exact(doc,accessibility['skip'],'#main-content',1)
  headers=doc.where('header');assert len(headers)==1,'Single header required'
  nav=within(headers[0],'nav');assert len(nav)==1 and nav[0]['attrs'].get('aria-label')==accessibility['navigation'],'Approved navigation aria label drift'
  for key,href in [('home','/'),('funeral',original[0]['url']),('celebration',original[1]['url']),('regions','/regions/')]:link_exact(doc,common['navigation'][key],href,1,nav[0])
  link_exact(doc,common['navigation']['phone'],common['footer']['phoneHref'],1,headers[0])
  footers=doc.where('footer');assert len(footers)==1,'Single footer required'
  footer=footers[0];f=common['footer']
  assert norm(f['brandLine']) in norm(footer['text']),'Footer brand line drift'
  for label,href in [(f['phoneLabel'],f['phoneHref']),(f['shopLabel'],f['shopHref']),(f['homeLinkLabel'],'/')]:link_exact(doc,label,href,1,footer)
  banners=doc.where(key='data-shared-flower-banner');variants=[n['attrs']['data-shared-flower-banner'] for n in banners]
  expected_banners=[] if rel in ('404.html','regions/index.html') else ['message','budget','consultation']
  assert variants==expected_banners,f'Banner sequence/count drift: {rel}'
  for banner in banners:
   imgs=within(banner,'img');variant=banner['attrs']['data-shared-flower-banner']
   assert len(imgs)==1 and imgs[0]['attrs']['src']=='/images/shared-banners/flower-'+variant+'.webp','Banner exact variant image drift'
   assert imgs[0]['attrs'].get('loading')=='lazy' and imgs[0]['attrs'].get('decoding')=='async','Banner lazy/async drift'
   assert not within(banner,'figcaption'),'Common banner caption must be absent under explicit amendment'
  assert sum('/images/shared-banners/' in n['attrs'].get('src','') for n in doc.where('img'))==len(banners),'Extra banner image outside figure'
  for left,right in zip(banners,banners[1:]):
   between=[n for n in doc.nodes if left['i']<n['i']<right['i'] and (n['tag']=='p' or 'page-card' in n['attrs'].get('class','').split()) and len(norm(n['text']))>=30 and not any('data-shared-flower-banner' in a['attrs'] for a in ancestor_nodes(n))]
   assert between,f'Adjacent banners lack substantive content: {rel}'
  cards=doc.cls('product-card');want=8 if rel=='index.html' else 0 if rel in ('404.html','regions/index.html') else 4
  assert len(cards)==want,f'Actual product card count drift: {rel}'
  expected_skus=list(approvedsku) if rel=='index.html' else next((b['productSkus'] for b in binding['articles'] if rel==b['url'].strip('/')+'/index.html'),[])
  assert [bykey.get(n['attrs'].get('data-product-key'),{}).get('officialSku') for n in cards]==expected_skus,f'Rendered product SKU/order drift: {rel}'
  for card in cards:
   assert not hidden(card),'Product card hidden'
   p=bykey[card['attrs']['data-product-key']];approved=approvedsku[p['officialSku']]
   assert [norm(n['text']) for n in within(card,'h3')]==[approved['name']],'Product name drift'
   assert [norm(n['text']) for n in within(card,'strong')]==[approved['priceLabel']],'Product per-SKU price drift'
   ptexts=[norm(n['text']) for n in within(card,'p')]
   assert ptexts.count(approved['description'])==1 and norm(card['text']).count(approved['photoCaption'])==1,'Product description/photoCaption missing or duplicated'
   assert len(within(card,'img'))==1 and within(card,'img')[0]['attrs']['src']==p['img'],'Product card image missing/duplicated/wrong SKU'
   link_exact(doc,approved['cta']['label'],approved['cta']['href'],1,card)
  heroes=doc.cls('hero-product')+doc.cls('detail-product')
  want_heroes=['B201','C200'] if rel=='index.html' else [] if rel in ('404.html','regions/index.html') else [next(b['productHeroSku'] for b in binding['articles'] if rel==b['url'].strip('/')+'/index.html')]
  assert [bykey.get(n['attrs'].get('data-product-key'),{}).get('officialSku') for n in heroes]==want_heroes,f'Hero/card separation or SKU drift: {rel}'
  actual_product_images=Counter(n['attrs']['src'] for n in doc.where('img') if n['attrs']['src'].startswith('/images/products/'))
  assert actual_product_images==Counter(bysku[sku]['img'] for sku in expected_skus+want_heroes),'Product image outside approved cards/heroes or image count drift'
  assert visible_body.count(common['productCards'][0]['photoCaption'])==want,'Photo caption outside approved product cards or count drift'
  for sku in expected_skus:assert visible_body.count(approvedsku[sku]['description'])==1,'Duplicate/missing product description anywhere in body'
  for hero in heroes:
   p=bykey[hero['attrs']['data-product-key']];assert len(within(hero,'img'))==1 and within(hero,'img')[0]['attrs']['src']==p['img'],'Hero product image drift'
   assert p['priceLabel'] in norm(hero['text']),'Hero price drift'
  if rel!='404.html':
   social_sku=want_heroes[0] if want_heroes else 'B201';social=bysku[social_sku]
   social_meta={n['attrs'].get('name',n['attrs'].get('property')):n['attrs'].get('content') for n in doc.where('meta')}
   for key in ['og:image:alt','twitter:image:alt']:assert social_meta.get(key)==social['imageAlt'],f'Reviewed social image alt drift: {key}'
   for key in ['og:image','og:image:secure_url','twitter:image']:assert social_meta.get(key)==base+social['img'],f'Social image exact URL drift: {key}'
  reports.append({'file':rel,'sha256':sha((dist/rel).read_bytes()),'productCards':len(cards),'heroProducts':len(heroes),'sharedBanners':variants})
 # Internal links and anchors are checked after all five document IDs exist.
 for rel,doc in docs.items():
  for link in doc.where('a'):
   u=urlsplit(link['attrs']['href'])
   if u.scheme or u.netloc:continue
   path=u.path or ('/'+rel.removesuffix('index.html') if rel!='index.html' else '/')
   target='index.html' if path=='/' else path.lstrip('/')+'index.html' if path.endswith('/') else path.lstrip('/')
   assert target in docs,f'Broken static internal route: {rel}: {u.geturl()}'
   if u.fragment:assert u.fragment in ids[target],f'Broken static anchor: {rel}: {u.geturl()}'
 home=docs['index.html'];h=common['home'];check_metadata(home,h['title'],h['h1'],h['metaDescription'],'/',base,indexable)
 for text in [h['intro'],h['shortTalk'],h['priceNote']]:exactly(home,'p',text)
 for text in [h['productHeading'],h['articleHeading'],h['placeHeading']]:exactly(home,'h2',text)
 for cta in [h['phoneCta'],h['shopCta']]:link_exact(home,cta['label'],cta['href'],1)
 for rel in ['index.html','regions/index.html']:
  doc=docs[rel];cards=doc.cls('page-card');assert len(cards)==2,f'Actual rich guide card N2 drift: {rel}'
  assert [c['attrs'].get('href') for c in cards]==[a['href'] for a in common['articleCards']],'Guide-card route/order drift'
  for card,approved in zip(cards,common['articleCards']):
   assert all(norm(card['text']).count(approved[k])==1 for k in ['title','summary','ctaLabel']),'Guide-card approved text missing/duplicated'
 for approved,page in zip(original,pages):
  rel=page['url'].strip('/')+'/index.html';doc=docs[rel];meta=check_metadata(doc,approved['title'],approved['h1'],approved['metaDescription'],page['url'],base,indexable)
  breadcrumb=doc.cls('breadcrumb');assert len(breadcrumb)==1 and breadcrumb[0]['attrs'].get('aria-label')==read(sealed/'interface-copy-addendum.json')['customerLabels']['accessibility']['breadcrumb'],'Approved breadcrumb aria label drift'
  assert meta.get('og:image:alt')==bysku[approved['productSkus'][0]]['imageAlt'],'Article OG image alt drift'
  exactly(doc,'p',approved['firstAnswer']);assert sum(t.count(approved['firstAnswer']) for _,t in doc.text_events)==1,'FirstAnswer duplication'
  headings=[]
  for section in approved['sections']:
   nodes=doc.where('h2','id',section['id']);assert len(nodes)==1 and norm(nodes[0]['text'])==section['heading'],'Section heading/order/anchor drift'
   headings.append(nodes[0]['i'])
   for paragraph in section['paragraphs']:
    exactly(doc,'p',paragraph)
    assert norm(doc.where('body')[0]['text']).count(norm(paragraph))==1,'Approved paragraph missing/duplicated anywhere in body'
  assert headings==sorted(headings),'Section order drift'
  # Every approved paragraph must follow its own heading before the next section.
  for i,section in enumerate(approved['sections']):
   last=headings[i];end=headings[i+1] if i+1<len(headings) else len(doc.nodes)
   for text in section['paragraphs']:
    node=exactly(doc,'p',text)[0];assert last<node['i']<end,'Paragraph ordering/section drift';last=node['i']
  for label in [common['faqHeading'],common['sourceHeading']]:exactly(doc,'h2',label)
  qnodes=doc.where(key='data-faq-question');anodes=doc.where(key='data-faq-answer')
  assert [norm(n['text']) for n in qnodes]==[q['question'] for q in approved['faq']],'FAQ questions missing/duplicated/drift'
  assert [norm(n['text']) for n in anodes]==[q['answer'] for q in approved['faq']],'FAQ answers missing/duplicated/drift'
  assert not any(hidden(n) for n in qnodes+anodes),'FAQ hidden/collapsed'
  for faq in approved['faq']:
   for value in [faq['question'],faq['answer']]:assert norm(doc.where('body')[0]['text']).count(norm(value))==1,'FAQ text duplicated outside FAQ markers'
  exactly(doc,'p',approved['sourceNote'])
  source_containers=doc.cls('source-references');assert len(source_containers)==1,'Single source section required'
  actual_sources=within(source_containers[0],'a')
  assert [(norm(n['text']),n['attrs'].get('href')) for n in actual_sources]==[(s['name'],s['url']) for s in approved['sourceLinks']],'Source section exact count/order/content drift'
  source_cards=doc.cls('source-card')
  assert len(source_cards)==len(approved['sourceLinks']),'Source-card count drift'
  for source_card,source in zip(source_cards,approved['sourceLinks']):
   assert [norm(n['text']) for n in within(source_card,'h3')]==[source['name']],'Source H3 hierarchy drift'
   assert not within(source_card,'h2'),'Source card must not duplicate H2'
   expected_type='business' if urlsplit(source['url']).hostname=='fwith.co.kr' else 'official'
   for key,value in [('data-source-name',source['name']),('data-source-type',expected_type),('data-source-verified-at','2026-10-13')]:assert source_card['attrs'].get(key)==value,f'Source metadata attribute drift: {key}'
   source_anchor=within(source_card,'a');assert len(source_anchor)==1 and source_anchor[0]['attrs'].get('aria-label')==source['name'],'Source aria-label drift'
   assert source_anchor[0]['children']==[],'Source link raw HTML/markup injection forbidden'
  source_nodes=[]
  for source in approved['sourceLinks']:source_nodes+=link_exact(doc,source['name'],source['url'],1)
  assert [n['i'] for n in source_nodes]==sorted(n['i'] for n in source_nodes),'Source order drift'
  link_exact(doc,approved['primaryCta']['label'],approved['primaryCta']['href'],1)
  link_exact(doc,approved['relatedLink']['label'],approved['relatedLink']['href'],1)
  exactly(doc,'p',approved['relatedLink']['intro'])
  for key,value in common['sharedNotices'].items():
   if key!='renderRule': assert not any(norm(n['text'])==value for n in doc.where('p')),'Seller policy duplicated outside approved article body'
 directory=docs['regions/index.html'];d=common['directory'];check_metadata(directory,d['title'],d['h1'],d['intro'],'/regions/',base,indexable)
 for key in ['intro','relationNote','facilityScopeNote']:exactly(directory,'p',d[key])
 for key in ['purchaseHeading','legalHeading','facilityHeading']:exactly(directory,'h2',d[key])
 exactly(directory,'h3',d['unassignedFacilityHeading'])
 general=directory.where(key='data-general-purchase-links');assert len(general)==1,'General purchase link group missing/duplicate'
 for i,key in enumerate(['funeral','celebration']):link_exact(directory,d['generalLinkLabels'][key],original[i]['url'],1,general[0])
 legal_nodes=directory.where(key='data-legal-unit');admin_nodes=directory.where(key='data-administrative-unit')
 assert len(legal_nodes)==3 and len(admin_nodes)==21,'Directory legal3/admin21 denominator drift'
 legal_links=[]
 for unit in units:
  nodes=directory.where(key='data-legal-unit',value=unit['unitKey']);assert len(nodes)==1,'Legal unit HTML missing/duplicate'
  expected_links=[f for f in binding['facilityDestinations'] if f['legalCode']==unit['legalCode']]
  facility_nodes=directory.where(key='data-facility-legal-unit',value=unit['unitKey'])
  assert len(facility_nodes)==(1 if expected_links else 0),'Facility legal group missing/extra'
  links=[a for fnode in facility_nodes for a in within(fnode,'a')]
  assert [(a['attrs']['href'],norm(a['text'])) for a in links]==[(f['href'],f['heading']) for f in expected_links],'Directory legal facility assignment drift'
  for link,expected_link in zip(links,expected_links):assert link['attrs'].get('data-candidate-id')==expected_link['candidateId'],'Rendered facility candidate id drift'
  legal_links+=links
 assert len(legal_links)==3,'Exactly three legal facility links required'
 for admin in admins:
  nodes=directory.where(key='data-administrative-unit',value=admin['aliasKey']);assert len(nodes)==1,'Administrative unit HTML missing/duplicate'
  assert admin['name'] in norm(nodes[0]['text']),'Administrative name output drift'
  assert not within(nodes[0],'a'),'Administrative rows must not imply facility assignment'
  legal_parent=next((a for a in ancestor_nodes(nodes[0]) if 'data-legal-unit' in a['attrs']),None)
  assert legal_parent and legal_parent['attrs']['data-legal-unit']==admin['relations'][0]['unitKey'],'Rendered administrative/legal relationship drift'
 faculty=[n for n in directory.where('a') if n['attrs'].get('href')==binding['facilityDestinations'][1]['href']]
 assert len(faculty)==1,'District-level unassigned faculty link missing/duplicate'
 assert faculty[0]['attrs'].get('data-candidate-id')=='snu-faculty','Unassigned professor candidate id drift'
 assert not any('data-legal-unit' in a['attrs'] or 'data-administrative-unit' in a['attrs'] or 'data-facility-legal-unit' in a['attrs'] for a in ancestor_nodes(faculty[0])),'Professor forced legal/administrative assignment'
 notfound=docs['404.html'];n=common['notFound'];check_metadata(notfound,n['title'],n['h1'],n['text'],'/404.html',base,indexable)
 assert n['title']!=n['h1'],'404 approved title must differ from H1'
 exactly(notfound,'p',n['text']);link_exact(notfound,n['homeLabel'],n['homeHref'],1)
 for rel,doc in docs.items():
  for node in doc.where('script','type','application/ld+json'):
   schema=json.loads(node['text']);assert schema=={'@context':'https://schema.org','@type':'Florist','name':common['brand'],'url':base,'telephone':'1844-0644','areaServed':'서울특별시 관악구'},'Seller schema invented facility address/phone or metadata'
 sitemap_count=validate_search_output(dist,base,indexable)
 report={'status':'LOCAL_STATIC_VERIFIED','scope':'Sealed inputs, runtime data, and generated HTML/assets only. Browser screens, responsive layout, focus, live HTTP, deploy and search are UNVERIFIED.','approvalPins':PINS,'htmlFiles':len(docs),'details':len(pages),'articleParagraphs':[sum(len(s['paragraphs']) for s in a['sections']) for a in original],'articleFaqs':[len(a['faq']) for a in original],'articleSources':[len(a['sourceLinks']) for a in original],'directoryCards':2,'productCards':{'home':8,'eachDetail':4},'physicalFacilities':4,'buyerOccasions':1,'legalUnits':3,'administrativeUnits':21,'officialRelations':21,'legalFacilityLinks':3,'districtUnassignedFacilityLinks':1,'administrativeFacilityLinks':0,'assets':11,'previewNoindex':not indexable,'sitemapCustomerUrls':sitemap_count,'files':reports}
 if write:
  output=Path(os.environ.get('GWANAK_QA_REPORT_PATH',root/'gwanak-static-qa.json'));output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 if not quiet:print('GWANAK STATIC QA: '+json.dumps(report,ensure_ascii=False))
 return report

def ancestor_nodes(node):
 node=node['parent']
 while node:
  yield node;node=node['parent']

if __name__=='__main__':inspect()
