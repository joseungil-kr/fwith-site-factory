"""Static Dongjak N1 acceptance: exact copy, topology, images and no false administrative attribution.
This gate does not claim browser-screen, network, publication or search verification.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
from collections import Counter
import hashlib,json,re,os
import xml.etree.ElementTree as ET
from qa_static import Document
from qa_faq_products import text_content
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
class Surface(HTMLParser):
 def __init__(self,html):
  super().__init__(convert_charrefs=True);self.nodes=[];self.stack=[];self.feed(html)
 def handle_starttag(self,tag,attrs):
  node={'tag':tag,'attrs':dict(attrs),'text':'','children':[]};self.nodes.append(node)
  if self.stack:self.stack[-1]['children'].append(node)
  if tag not in VOID:self.stack.append(node)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,-1,-1):
   if self.stack[i]['tag']==tag:del self.stack[i:];break
 def handle_data(self,text):
  for n in self.stack:n['text']+=text
 def where(self,tag=None,key=None,value=None):return [n for n in self.nodes if (tag is None or n['tag']==tag) and (key is None or key in n['attrs'] and (value is None or n['attrs'][key]==value))]
 def cls(self,cls):return [n for n in self.nodes if cls in n['attrs'].get('class','').split()]
def norm(s):return ' '.join(s.split())
def descendants(n):
 for c in n['children']:yield c;yield from descendants(c)
def inspect(root=Path('.'),write=True):
 root=Path(root);data=root/'src/data';dist=root/'dist';read=lambda n:json.loads((data/(n+'.json')).read_text());article=read('dongjak-article-copy');common=read('dongjak-common-copy');pages=read('pages');c=read('region-coverage');ui=read('dongjak-ui-copy');products=read('products');config=read('site-config')
 indexable=os.environ.get('SITE_INDEXABLE')=='true';origin=os.environ.get('SITE_URL') or config['previewUrl']
 for file,expected_hash in [('dongjak-article-copy','428b4c3a66e648c15cf35c3887aee619c1e8eeb724f98ea8cdaa044e55001489'),('dongjak-common-copy','b158fa9b9faa4049f11b94c8023073ab3aee7fa8fdd3088b7e5b6d5a9701649f')]:assert hashlib.sha256((data/(file+'.json')).read_bytes()).hexdigest()==expected_hash,'Approved copy byte drift'
 assert len(pages)==1 and pages[0]['url']=='/regions/dongjak-funeral-wreath/','N1 route drift'
 detail_rel='regions/dongjak-funeral-wreath/index.html';expected={'index.html','regions/index.html','404.html',detail_rel};files={p.relative_to(dist).as_posix() for p in dist.rglob('*.html')};assert files==expected,'Unexpected standalone or missing HTML route'
 docs={p:Surface((dist/p).read_text()) for p in expected};entries=[];asset_counts=Counter();allids={}
 for rel,doc in docs.items():
  ids=[n['attrs']['id'] for n in doc.where(key='id')];assert len(ids)==len(set(ids)),'Duplicate HTML id: '+rel;allids[rel]=set(ids)
  assert len(doc.where('h1'))==1,'H1 count drift'
  for img in doc.where('img'):
   a=img['attrs'];assert a.get('alt') and a.get('width') and a.get('height'),'Missing image alt/dimensions: '+rel
   assert (dist/a['src'].lstrip('/')).is_file(),'Missing rendered image';asset_counts[a['src']]+=1
   if a['src'].startswith('/images/products/'):
    product=next(p for p in products if p['img']==a['src']);assert a['alt']==product['imageAlt'],'Unreviewed product alt';assert (a['width'],a['height'])==('500','500'),'Wrong product dimensions'
  for anchor in doc.where('a'):
   href=anchor['attrs'].get('href','');u=urlsplit(href)
   if u.scheme or u.netloc:continue
   path=u.path or ('/'+rel.removesuffix('index.html') if rel!='index.html' else '/')
   target='index.html' if path=='/' else path.lstrip('/')+'index.html' if path.endswith('/') else path.lstrip('/')
   assert target in docs,'Broken static destination '+href
 # Resolve after collecting IDs from every route.
 for rel,doc in docs.items():
  for link in doc.where('a'):
   u=urlsplit(link['attrs'].get('href',''))
   if u.scheme or u.netloc:continue
   path=u.path or ('/'+rel.removesuffix('index.html') if rel!='index.html' else '/')
   target='index.html' if path=='/' else path.lstrip('/')+'index.html' if path.endswith('/') else path.lstrip('/')
   if u.fragment:assert u.fragment in allids[target],'Broken fragment '+link['attrs']['href']
  old=Document((dist/rel).read_text());expected_robots=('noindex,nofollow,noarchive' if rel=='404.html' else 'noindex,follow' if rel=='regions/index.html' else 'index,follow') if indexable else 'noindex,nofollow,noarchive';assert old.meta['robots']==expected_robots,'Mode robots drift'
  if rel!='404.html':assert old.canonical==[origin+('/' if rel=='index.html' else '/'+rel.removesuffix('index.html'))],'Canonical drift'
  else:assert not old.canonical,'404 canonical forbidden'
  footer=doc.where('footer');assert len(footer)==1
  for text in [common['footer']['brandLine'],common['footer']['phoneLinkText'],common['footer']['homeLinkText']]:assert text in footer[0]['text'],'Footer copy drift'
  assert any(n['text']==common['footer']['homeLinkText'] and n['attrs']['href']==common['footer']['homeHref'] for n in descendants(footer[0]) if n['tag']=='a'),'Footer destination drift'
 for rel,copy in [('index.html',common['home']),('regions/index.html',common['directory']),(detail_rel,article)]:
  doc=docs[rel];old=Document((dist/rel).read_text());assert doc.where('h1')[0]['text']==copy['h1'],'H1 copy drift';assert old.title==copy['title'] and old.meta['description']==copy['description'],'Meta copy drift'
 doc=docs[detail_rel];old=Document((dist/detail_rel).read_text());assert norm(''.join(old.first_answer))==norm(article['firstAnswer']),'Lead copy drift'
 for field in ['title','h1','description','cardSummary','firstAnswer','sections','faq','primaryCta','sourceHeading','sourceNote','sourceLinks','facilityLinks','productCardSkus']:assert pages[0][field]==article[field],'Runtime reviewed field drift '+field
 expected_body=[]
 for section in article['sections']:
  nodes=doc.where('section',key='id',value=section['id']);assert len(nodes)==1,'Missing article section';section_node=nodes[0]
  assert [n['text'] for n in section_node['children'] if n['tag']=='h2']==[section['heading']],'Section heading drift'
  actual_paragraphs=[n['text'] for n in section_node['children'] if n['tag']=='p'];assert actual_paragraphs==section.get('paragraphs',[]),'Missing or changed approved body'
  expected_body+=actual_paragraphs
  for sub in section.get('subsections',[]):
   nodes=doc.where(key='id',value=sub['id']);assert len(nodes)==1 and nodes[0]['tag']=='h3' and nodes[0]['text']==sub['heading'],'Facility anchor level/text drift'
   block=next(n for n in section_node['children'] if n['tag']=='section' and nodes[0] in n['children']);assert [n['text'] for n in block['children'] if n['tag']=='p']==sub['paragraphs'],'Missing or changed approved body';expected_body+=sub['paragraphs']
 assert [n['attrs']['id'] for n in doc.where('section') if n['attrs'].get('id') in [s['id'] for s in article['sections']]]==[s['id'] for s in article['sections']],'Article section order drift'
 assert sum(n['text']==article['sourceHeading'] for n in doc.where('h2'))==1,'Source H2 missing or duplicated'
 source_cards=doc.cls('source-card');assert len(source_cards)==len(article['sourceLinks']),'Source count drift'
 for node,source in zip(source_cards,article['sourceLinks']):
  links=[n for n in descendants(node) if n['tag']=='a'];assert [(n['text'],n['attrs'].get('href')) for n in links]==[(source['label'],source['url'])],'Source label/destination drift';assert node['attrs']['data-source-verified-at']=='2026-10-13','Source date drift'
 assert any(n['text']==article['sourceNote'] for n in doc.where('p')),'Source note missing'
 for q in article['faq']:
  assert any(n['text']==q['question'] for n in doc.where(key='data-faq-question')),'FAQ question drift'
  assert any(n['text']==q['answer'] for n in doc.where(key='data-faq-answer')),'FAQ answer drift'
 for rel in ['index.html',detail_rel]:
  doc=docs[rel];cards=doc.cls('product-card');assert len(cards)==4,'Four approved product cards required'
  assert [n['attrs']['data-product-key'] for n in cards]==[p['key'] for p in products],'SKU card order drift'
  for node,p,approved in zip(cards,products,common['productCards']):
   assert [n['text'] for n in descendants(node) if n['tag']=='h3']==[approved['name']],'Product name drift'
   assert [n['text'] for n in descendants(node) if n['tag']=='strong']==[approved['priceLabel']+' '+format(approved['basicPriceKRW'],',')+'원'],'Exact product price drift'
   assert [n['text'] for n in descendants(node) if n['tag']=='p']==[approved['caption']],'Product caption drift'
   assert [(n['text'],n['attrs']['href']) for n in descendants(node) if n['tag']=='a']==[(approved['buttonLabel'],approved['href'])],'Product CTA drift'
   assert hashlib.sha256((dist/p['img'].lstrip('/')).read_bytes()).hexdigest()==approved['imageSha256'],'Product byte drift'
  banners=doc.where(key='data-shared-flower-banner');assert [n['attrs']['data-shared-flower-banner'] for n in banners]==['message','budget','consultation'],'Banner order drift'
  assert not any(n['tag']=='figcaption' for banner in banners for n in descendants(banner)),'Shared banner caption reintroduced'
  assert '꽃이랑 공통 안내 이미지 · 실제 판매상품 사진이 아닌 AI 생성 이미지입니다.' not in norm((dist/rel).read_text()),'Removed shared caption reintroduced'
  pos=[doc.nodes.index(n) for n in banners];assert pos[0]<doc.nodes.index(cards[0])<doc.nodes.index(cards[-1])<pos[1],'Banner/product spacing drift'
  if rel==detail_rel:
   assert pos[1]<doc.nodes.index(doc.where('section',key='id',value='places')[0])<doc.nodes.index(doc.where(key='data-visible-faq')[0])<pos[2]<doc.nodes.index(doc.cls('source-references')[0]),'Detail banner/FAQ/source order drift'
  else:assert pos[1]<doc.nodes.index(doc.cls('home-consultation')[0])<pos[2],'Home consultation spacing drift'
 home=docs['index.html'];hc=common['home']
 for text in [hc['intro'],hc['consultationText'],hc['priceDeliveryNote'],hc['materialsAndCollectionNote']]:assert any(n['text']==text for n in home.where('p')),'Home approved paragraph drift'
 for heading in [hc['sectionHeading'],hc['productsHeading'],hc['consultationHeading']]:assert sum(n['text']==heading for n in home.where('h2'))==1,'Home heading drift'
 for rel,copy in [('index.html',hc),('regions/index.html',common['directory'])]:
  cards=docs[rel].cls('page-card');assert len(cards)==1 and cards[0]['attrs']['href']==copy['cards'][0]['href'],'Actual directory card count/route drift'
  for key in ['title','summary','buttonLabel']:assert copy['cards'][0][key] in cards[0]['text'],'Card copy drift'
 directory=docs['regions/index.html'];assert not directory.where(key='data-shared-flower-banner'),'Thin directory banners forbidden';assert len(directory.where('li',key='data-legal-unit'))==9,'Legal inventory drift';assert len(directory.where('li',key='data-administrative-unit'))==15,'Administrative inventory drift'
 candidate_links=[]
 for u in c['units']:
  li=directory.where('li',key='data-legal-unit',value=u['unitKey']);assert len(li)==1
  expected=[a for p in pages for a in p['facilityAnchors'] if a['unitKey']==u['unitKey']];links=[n for n in descendants(li[0]) if n['tag']=='a'];assert [(n['attrs']['href'],n['text']) for n in links]==[(x['href'],x['heading']) for x in expected],'Legal facility destination drift';candidate_links.extend(links)
  if not expected:assert ui['directory']['emptyUnitLabel'] in li[0]['text'],'Empty legal label drift'
 assert len(candidate_links)==2,'Exactly two legal facility anchors required'
 for admin in c['administrativeCrosswalk']:
  row=directory.where('li',key='data-administrative-unit',value=admin['aliasKey']);assert len(row)==1;assert not any(n['tag']=='a' for n in descendants(row[0])),'Administrative rows must not imply venue assignment'
  names=[next(u['name'] for u in c['units'] if u['unitKey']==rel['unitKey'])+(' '+ui['directory']['partialLabel'] if rel['scope']=='partial' else '') for rel in admin['relations']];assert norm(row[0]['text'])==admin['name']+': '+' · '.join(names),'Official administrative relation text drift'
 assert sum(len(a['relations']) for a in c['administrativeCrosswalk'])==18,'Official relationship count drift'
 nf=docs['404.html'];assert not nf.where(key='data-shared-flower-banner') and not nf.where(key='data-order-banner'),'404 marketing forbidden';assert nf.where('h1')[0]['text']==common['notFound']['title'],'404 copy drift';assert any(n['text']==common['notFound']['text'] for n in nf.where('p')),'404 paragraph drift'
 approval_bytes=(data/'release-approval.json').read_bytes()
 assert hashlib.sha256(approval_bytes).hexdigest()=='0873b3ffcf00bc7f43c07afaf242c3df1e93e19fbbffff539a55a73eedc047f1','Release approval byte drift'
 approval=json.loads(approval_bytes);overlay_bytes=(root/approval['requestedCustomerContentOverlay']['path']).read_bytes()
 assert hashlib.sha256(overlay_bytes).hexdigest()==approval['requestedCustomerContentOverlay']['sha256'],'Banner overlay byte drift'
 overlay=json.loads(overlay_bytes)
 for banner in common['bannerPolicy']['banners']:
  path='/images/shared-banners/'+banner['file'];replacement=overlay['replacements']['public'+path];assert replacement['beforeSha256']==banner['sha256'],'Historical banner pin drift';assert hashlib.sha256((dist/path.lstrip('/')).read_bytes()).hexdigest()==replacement['afterSha256'],'Banner byte drift';assert asset_counts[path]==2,'Banner route count drift'
  for doc in docs.values():
   for n in doc.where('img',key='src',value=path):assert n['attrs']['alt']==banner['alt']+' 전화 1844-0644.','Banner alt drift'
 assert config['productionApproved'] is True and config['hostnameOwnershipVerified'] is False,'Publication guard drift'
 if not indexable:assert not list(dist.glob('sitemap*.xml')),'Mode sitemap unexpectedly present in preview'
 urls=[]
 for xml in dist.glob('sitemap*.xml'):
  doc=ET.parse(xml)
  if doc.getroot().tag.rsplit('}',1)[-1]=='urlset':urls.extend(n.text for n in doc.iter() if n.tag.rsplit('}',1)[-1]=='loc')
 expected_urls={origin+'/',origin+'/regions/dongjak-funeral-wreath/'} if indexable else set()
 assert len(urls)==len(set(urls)) and set(urls)==expected_urls,'Mode sitemap drift'
 lines=[line.strip() for line in (dist/'robots.txt').read_text().splitlines() if line.strip()]
 assert lines==(['User-agent: *','Allow: /','Sitemap: '+origin+'/sitemap-index.xml'] if indexable else ['User-agent: *','Disallow: /']),'Mode robots text drift'
 report={'scope':'Static HTML only; screen/public HTTP/search unverified','htmlFiles':4,'details':[{'url':pages[0]['url'],'anchors':2,'productCards':4,'faq':2,'sourceSectionH2':1,'approvedCopyPreserved':True}],'uniqueSku':4,'legalEntries':9,'adminEntries':15,'officialRelations':18,'legalFacilityLinks':2,'administrativeFacilityLinks':0,'directoryCards':1,'directoryBanners':0,'directoryIndexable':False,'productionApproved':config['productionApproved'],'canonicalOrigin':origin,'hostnameOwnershipVerified':False,'approvedArticleParagraphs':len(expected_body)}
 if write:(root/'dongjak-static-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('DONGJAK STATIC QA: '+json.dumps(report,ensure_ascii=False));return report
if __name__=='__main__':inspect()
