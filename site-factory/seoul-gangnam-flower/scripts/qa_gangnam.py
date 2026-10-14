"""Gangnam successor: sealed approved bytes -> runtime -> six local rendered pages.
Offline only. Original-source recovery, fresh factual research, visual/public QA are NOT asserted.
"""
from pathlib import Path
from urllib.parse import urlsplit,unquote
import hashlib,json,re,xml.etree.ElementTree as ET
from qa_gwanak import Surface,norm,within,hidden,exactly,link_exact
from qa_faq_products import Output,normalize_faq
from banner_phone_amendment import load_amendment
from minimal_source_evidence import effective_articles, AMENDMENT_SHA256 as SOURCE_LINK_AMENDMENT_SHA256
PINS={'gangnam-approved/delivery-manifest.json':'2af6d2b07e668177bd271b9b4cfc6cb751ffdedfd96ae8d975e5d3dd83979214','gangnam-a04-rev4/delivery-manifest.json':'9c7825e73cc6d8f716b81b3ff4e5a4af14162d885f57caac525d3810d5daf88b','gangnam-approved/plan/fixed-plan.json':'82bf53fb58d01c65d7fe87e730fcaf39ec60620603f671696074ba41510e68c3','gangnam-approved/copy/common-visible-copy.final.json':'da15580bb4f05ae39a60a51d6bdc3fe9fcc65d9e2d738dcd573ebc483aa70cdd','gangnam-a04-rev4/revised-input/copy/article-copy.rev4.json':'ca721a7a712c7814b21599d7a16d49e9476465527213c8496a1c2d2bb61b3e0f','gangnam-a04-rev4/mapping/keyword-mapping.rev4.final.json':'fd4f54ac139055fabe6694c316286afcb7b22792cb77133cf8c56f54b9f0c5e4'}
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify_inputs(root):
 data=root/'src/data';checks=0
 for n,h in PINS.items():assert sha(data/n)==h,'Sealed input drift: '+n;checks+=1
 for n,count in [('gangnam-approved',162),('gangnam-a04-rev4',70)]:
  m=read(data/n/'delivery-manifest.json');assert len(m['files'])==count
  for row in m['files']:
   f=data/n/row['path'];assert f.is_file() and not f.is_symlink() and f.stat().st_size==row['bytes'] and sha(f)==row['sha256'],'Sealed delivery member drift: '+row['path'];checks+=1
 approved=read(data/'gangnam-a04-rev4/revised-input/copy/article-copy.rev4.json')['articles'];common=read(data/'gangnam-approved/copy/common-visible-copy.final.json')['common']
 approved=effective_articles(root,approved)
 copy=read(data/'gangnam-copy.json');assert copy=={'articles':approved,'common':common},'Runtime customer copy differs beyond approved SETEC URL amendment'
 coverage=read(data/'region-coverage.json');binding=read(data/'gangnam-plan-binding.json')
 assert binding['coverage']==coverage and binding['policy']==read(data/'region-policy.json'),'Frozen geography/policy drift'
 assert [len(coverage['units']),len(coverage['administrativeCrosswalk']),sum(len(x['relations']) for x in coverage['administrativeCrosswalk']),len(coverage['facilities']),len(coverage['buyerOccasions'])]==[14,22,31,5,0]
 assert all(f['administrativeCode'] is None for f in coverage['facilities'])
 assert {f['facilityKey'] for f in coverage['facilities'] if f['unitKey'] is None}=={'samsung-seoul-funeral','setec'}
 c=read(data/'site-config.json');assert c['siteKey']=='seoul-gangnam-flower-direct' and c['sourceMode']=='local-preparation'
 for key in ['productionApproved','hostnameOwnershipVerified','publicHttpVerified','indexNowSubmitted']:assert c[key] is False,'Publication boundary drift: '+key
 for key in ['worker','canonicalHostname','sourceCommit']:assert c[key] is None,'Unverified production identity: '+key
 assert c['previewUrl']=='https://seoul-gangnam.local.invalid'
 pages=read(data/'pages.json');assert len(pages)==3
 for a,p in zip(approved,pages):
  for key,value in a.items():
   actual=[x['anchor'] for x in p[key]] if key=='facilityAnchors' else p[key]
   assert actual==value,'Exact article field drift: '+a['slug']+'/'+key
 return approved,common,coverage,pages,checks

def inspect(root=Path('.'),write_report=True):
 root=Path(root);data=root/'src/data';dist=root/'dist';approved,common,coverage,pages,input_checks=verify_inputs(root)
 products=read(data/'products.json');assert len(products)==8
 assets=read(data/'gangnam-approved/handoff/approved-assets.json')['assets']
 for asset in assets:
  if asset['kind']=='actual-sale-product':
   for prefix in ['public','dist']:assert sha(root/prefix/asset['proposedRuntimePath'].removeprefix('public/'))==asset['sha256'],'Product photo drift'
 amendment=load_amendment(root)
 for variant,b in amendment['assets'].items():
  for prefix in ['public','dist']:assert sha(root/prefix/'images/shared-banners'/b['file'])==b['sha256'],'Banner byte drift'
 routes=['/','/regions/']+[a['url'] for a in approved]+['/404.html'];paths=[dist/'index.html',dist/'regions/index.html']+[dist/a['url'].strip('/')/'index.html' for a in approved]+[dist/'404.html']
 assert {str(p.relative_to(dist)) for p in dist.rglob('*.html')}=={str(p.relative_to(dist)) for p in paths},'Exact HTML6 denominator mismatch'
 docs={};report=[]
 for route,path in zip(routes,paths):
  html=path.read_text();doc=Surface(html);docs[route]=doc
  assert len(doc.where('h1'))==1,'Single H1 required '+route
  metas={n['attrs'].get('name',n['attrs'].get('property')):n['attrs'].get('content') for n in doc.where('meta')}
  assert metas.get('robots')=='noindex,nofollow,noarchive','Local noindex boundary failed '+route
  meta_copy=(common['home'] if route=='/' else common['directory'] if route=='/regions/' else common['notFound'] if route=='/404.html' else next(a for a in approved if a['url']==route))
  expected_description=meta_copy.get('metaDescription',meta_copy.get('text'))
  assert metas.get('description')==expected_description,'Exact meta description drift '+route
  if route!='/404.html':
   for key in ['og:description','twitter:description']:assert metas.get(key)==expected_description,'Social description drift '+route
   for key in ['og:title','twitter:title']:assert metas.get(key)==meta_copy['title'],'Social title drift '+route
  banners=doc.where('figure','data-shared-flower-banner');expected=[] if route=='/404.html' else ['message','budget','consultation']
  assert [b['attrs']['data-shared-flower-banner'] for b in banners]==expected,'Exact banner set/order failed '+route
  assert not any('/images/shared-banners/' in n['attrs'].get('src','') for n in doc.where('img') if not any(n in within(b,'img') for b in banners)),'Banner outside contract'
  for b in banners:
   v=b['attrs']['data-shared-flower-banner'];imgs=within(b,'img');assert len(imgs)==1
   img=imgs[0]['attrs'];assert img['src']=='/images/shared-banners/'+amendment['assets'][v]['file'] and img['alt']==amendment['assets'][v]['alt'],'Banner src/alt drift'
   assert (img.get('width'),img.get('height'),img.get('loading'),img.get('decoding'))==('1774','887','lazy','async') and not within(b,'figcaption'),'Banner dimensions/caption drift'
  visible=' '.join(t for n,t in doc.text_events if not hidden(n))
  for token in ['관악구','서초구','A04','LOCAL_','/workspace/','REV4','REVIEW_PENDING','도구 보고','실제 판매상품 사진이 아닌 AI 생성 이미지']:
   assert token not in visible,'Internal/foreign/old caption text leaked '+token
  canonical=[n['attrs']['href'] for n in doc.where('link','rel','canonical')];assert canonical==([] if route=='/404.html' else ['https://seoul-gangnam.local.invalid'+route]),'Canonical drift '+route
  levels=[int(n['tag'][1]) for n in doc.nodes if re.fullmatch('h[1-6]',n['tag'])];assert all(b<=a+1 for a,b in zip(levels,levels[1:])),'Heading level jump'
  for link in doc.where('a'):
   href=link['attrs'].get('href','');u=urlsplit(href)
   if href.startswith('/') or href.startswith('#'):
    target=dist/unquote(u.path).lstrip('/') if u.path else path
    if target.is_dir():target=target/'index.html'
    assert target.is_file(),'Broken local link '+href
    if u.fragment:assert u.fragment in [n['attrs'].get('id') for n in Surface(target.read_text()).nodes],'Missing fragment '+href
  schemas=[]
  for n in doc.where('script','type','application/ld+json'):schemas.append(json.loads(n['text']))
  if route!='/404.html':
   assert len(schemas)==1 and schemas[0]['@type']=='Florist' and schemas[0]['telephone']=='1844-0644' and schemas[0]['areaServed']=='서울특별시 강남구' and 'address' not in schemas[0],'Schema must not invent branch address'
  else:assert not schemas
  report.append({'route':route,'sha256':sha(path),'bytes':path.stat().st_size,'banners':expected,'robots':metas['robots'],'canonical':canonical,'schemaTypes':[s['@type'] for s in schemas]})
 for a,p in zip(approved,pages):
  d=docs[a['url']];assert d.text('title')==[a['title']] and d.text('h1')==[a['h1']],'Detail title/H1 drift'
  assert [n['attrs'].get('content') for n in d.where('meta','name','description')]==[a['metaDescription']]
  exactly(d,'p',a['firstAnswer']);sections=d.where('section','data-approved-section');assert [s['attrs']['data-approved-section'] for s in sections]==[s['id'] for s in a['sections']],'Section order/duplication drift'
  for expected,actual in zip(a['sections'],sections):
   assert [norm(n['text']) for n in within(actual,'h2')]==[expected['heading']]
   assert [norm(n['text']) for n in within(actual,'p') if 'product-notice' not in n['attrs'].get('class','')][:len(expected['paragraphs'])]==list(map(norm,expected['paragraphs'])),'Body paragraph drift'
   for paragraph in expected['paragraphs']:exactly(d,'p',paragraph)
  out=Output((dist/a['url'].strip('/')/'index.html').read_text());assert all(href==next(v['sourceUrl'] for v in products if v['key']==key) for key,href in out.order_ctas),'Hero product CTA drift'
  assert out.visible_faq()==normalize_faq(a['faq']) and not out.hidden_faq,'FAQ missing/hidden/drift'
  cards=d.cls('product-card');assert len(cards)==4
  assert [n['attrs']['data-product-key'] for n in cards]==p['productCardKeys']
  for product in products:
   for node in [n for n in cards if n['attrs']['data-product-key']==product['key']]:
    assert [x['attrs']['href'] for x in within(node,'a')]==[product['sourceUrl']],'Product CTA drift'
  link_exact(d,a['primaryCta']['label'],a['primaryCta']['href']);link_exact(d,a['relatedLink']['label'],a['relatedLink']['href']);link_exact(d,common['articleUi']['directoryLinkLabel'],'/regions/')
  for source in a['sourceLinks']:link_exact(d,source['name'],source['url'],count=1)
  banners=d.where('figure','data-shared-flower-banner');assert sections[0]['i']<banners[0]['i']<sections[1]['i']
  anchor=next(n for n in sections if n['attrs']['data-approved-section']==a['facilityAnchors'][-1]);nextsection=sections[sections.index(anchor)+1]
  assert anchor['i']<banners[1]['i']<nextsection['i'],'Budget not after venue content'
  assert sections[-1]['i']<banners[2]['i']<d.cls('source-references')[0]['i'],'Consultation placement drift'
  first_and_body='\n'.join([a['firstAnswer']]+[paragraph for section in a['sections'] for paragraph in section['paragraphs']])
  assert len(first_and_body)==a['uniqueBodyCharsIncludingFirstAnswer'],'Approved authored-length metadata drift'
  # 2,500–3,000 is an editorial aim, not a minimum, quality score, or acceptance gate.
 d=docs['/'];c=common['home'];assert d.text('title')==[c['title']] and d.text('h1')==[c['h1']]
 for field in ['intro','shortTalk','priceNote','placeIntro']:exactly(d,'p',c[field])
 for field in ['materials','collection']:exactly(d,'p',common['sharedNotices'][field])
 assert len(d.cls('product-card'))==8 and len(d.cls('purpose-card'))==3
 for key in ['phoneCta','shopCta']:link_exact(d,c[key]['label'],c[key]['href'])
 for group,family in zip(d.where('section','data-home-product-group'),['funeral','congrats']):assert len(within(group,'article','data-product-family',family))==4
 banner=d.where('figure','data-shared-flower-banner');groups=d.where('section','data-home-product-group');assert groups[0]['i']<banner[1]['i']<groups[1]['i'],'Home budget placement'
 d=docs['/regions/'];c=common['directory'];assert d.text('title')==[c['title']] and d.text('h1')==[c['h1']]
 cards=d.cls('page-card');assert len(cards)==3 and [n['attrs']['href'] for n in cards]==[a['url'] for a in approved]
 banners=d.where('figure','data-shared-flower-banner');assert banners[0]['i']<cards[0]['i']<cards[1]['i']<banners[1]['i']<cards[2]['i']<banners[2]['i'],'Directory actual-card banner split failed'
 assert len(d.where('section','data-legal-unit'))==14 and len(d.where('li','data-administrative-unit'))==31
 assert len(d.where('div','data-general-purchase-links'))==14
 assert len(d.where('a','data-candidate-id'))==5 and len(within(d.where('section','data-unassigned-facilities')[0],'a'))==2
 for legal in d.where('section','data-legal-unit'):
  links=within(legal,'div','data-general-purchase-links');assert len(links)==1 and [n['attrs']['href'] for n in within(links[0],'a')]==[a['url'] for a in approved]
 d=docs['/404.html'];assert d.text('title')==[common['notFound']['title']] and d.text('h1')==[common['notFound']['h1']]
 assert 'Disallow: /' in (dist/'robots.txt').read_text() and 'Sitemap:' not in (dist/'robots.txt').read_text()
 assert 'X-Robots-Tag: noindex, nofollow, noarchive' in (dist/'_headers').read_text()
 for sitemap in dist.glob('sitemap*.xml'):
  e=ET.fromstring(sitemap.read_text());assert not [x for x in e.iter() if x.tag.split('}')[-1] in ['url','sitemap']],'Local sitemap must be empty'
 result={'status':'PASS_LOCAL_STATIC_ONLY','sealedReferenceChecks':input_checks,'routes':report,'articleN':3,'htmlN':6,'observedBodyCodePoints':{a['id']:a['uniqueBodyCharsIncludingFirstAnswer'] for a in approved},'lengthInterpretation':'2500-3000 aim only; exact approved copy retained, no minimum or quality gate','visibleFaqCount':sum(len(a['faq']) for a in approved),'bannerCount':15,'originalSourceRecovered':False,'source1474':'unverified_not_recovered','sourceLinkAmendmentSha256':SOURCE_LINK_AMENDMENT_SHA256,'customerBodySentencesChanged':0,'customerSourceUrlsChanged':1,'research331':'not_recovered','buildEvidence':'separate executable build log required','browserVisualQa':'unverified','publicHttp':'not_run','ownership':'unverified','publication':'not_authorized','indexNow':'not_run'}
 if write_report:(root/'gangnam-static-qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('Gangnam LOCAL static QA: exact copy, 6 routes, 15 banners, sealed inputs, FAQ/CTA/geography/SEO passed')
 return result
if __name__=='__main__':inspect()
