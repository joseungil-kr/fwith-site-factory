"""Static N2 acceptance: exact copy, topology, images and no false administrative attribution.
This gate does not claim browser-screen, network, publication or search verification.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
from collections import Counter
import hashlib,json,re
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
 root=Path(root);data=root/'src/data';dist=root/'dist';read=lambda n:json.loads((data/(n+'.json')).read_text());cp=read('yeongdeungpo-copy');pages=read('pages');c=read('region-coverage');ui=read('yeongdeungpo-ui-copy');products=read('products');config=read('site-config')
 assert hashlib.sha256((data/'yeongdeungpo-copy.json').read_bytes()).hexdigest()=='cdc2fda4970414d2d80c0aae7a939fb2d13f2bfbb210f3c2e663864945c01a1f','Approved copy byte drift'
 expected={'index.html','regions/index.html','404.html'}|{p['url'].strip('/')+'/index.html' for p in pages};files={p.relative_to(dist).as_posix() for p in dist.rglob('*.html')};assert files==expected,'Unexpected standalone or missing HTML route'
 docs={p:Surface((dist/p).read_text()) for p in expected};entries=[];asset_counts=Counter();allids={}
 for rel,doc in docs.items():
  ids=[n['attrs']['id'] for n in doc.where(key='id')];assert len(ids)==len(set(ids)),'Duplicate HTML id: '+rel;allids[rel]=set(ids)
  for img in doc.where('img'):
   a=img['attrs'];assert a.get('alt') and a.get('width') and a.get('height'),'Missing image alt/dimensions: '+rel
   assert (dist/a['src'].lstrip('/')).is_file(),'Missing rendered image';asset_counts[a['src']]+=1
   if a['src'].startswith('/images/products/'):
    product=next(p for p in products if p['img']==a['src']);assert a['alt']==product['imageAlt'],'Unreviewed product alt';assert (a['width'],a['height'])==('500','500'),'Wrong product dimensions'
 for rel,doc in docs.items():
  for link in doc.where('a'):
   href=link['attrs'].get('href','');u=urlsplit(href)
   if u.scheme or u.netloc:continue
   path=u.path or ('/'+rel.removesuffix('index.html') if rel!='index.html' else '/')
   target='index.html' if path=='/' else path.lstrip('/')+'index.html' if path.endswith('/') else path.lstrip('/')
   assert target in docs,'Broken static destination '+href
   if u.fragment:assert u.fragment in allids[target],'Broken fragment '+href
 for approved,page in zip(cp['articles'],pages):
  rel=page['url'].strip('/')+'/index.html';html=(dist/rel).read_text();doc=docs[rel];old=Document(html)
  assert doc.where('h1')[0]['text']==approved['h1'],'H1 copy drift';assert old.title==approved['title'] and old.meta['description']==approved['description'],'Meta copy drift';assert norm(''.join(old.first_answer))==norm(approved['firstAnswer']),'Lead copy drift'
  body=doc.cls('markdown-content');assert len(body)==1,'Missing single article body';body=norm(body[0]['text'])
  for line in approved['contentMarkdown'].splitlines():
   line=re.sub(r'^(?:#{1,6}\s+|[-*]\s+)','',line).strip()
   if line:assert text_content(line) in body,'Missing or changed approved body: '+line[:80]
  for label,href in re.findall(r'\[([^\]]+)\]\(([^)]+)\)',approved['contentMarkdown']):assert any(n['text']==label and n['attrs']['href']==href for n in doc.where('a')),'Inline approved destination drift'
  assert sum(n['text']==approved['sourceHeading'] for n in doc.where('h2'))==1,'Source H2 missing or duplicated'
  for anchor in page['facilityAnchors']:
   nodes=doc.where(key='id',value=anchor['anchor']);expected_level='h3' if approved['id']=='funeral' else 'h2'
   assert len(nodes)==1 and nodes[0]['tag']==expected_level and nodes[0]['text']==anchor['heading'],'Facility anchor level/text drift'
  cards=doc.cls('product-card');assert len(cards)==4,'Four approved product cards required'
  assert [n['attrs']['data-product-key'] for n in cards]==page['productCardKeys'],'SKU card order drift'
  assert any(n['text']==approved['sourceNote'] for n in doc.where('p')),'Source limitation missing'
  for q in approved['faq']:
   assert any(norm(n['text'])==norm(q['question']) for n in doc.where(key='data-faq-question')),'FAQ question drift'
   assert any(norm(n['text'])==norm(q['answer']) for n in doc.where(key='data-faq-answer')),'FAQ answer drift'
  entries.append({'url':page['url'],'anchors':len(page['facilityAnchors']),'productCards':4,'faq':len(approved['faq']),'sourceSectionH2':1,'approvedCopyPreserved':True})
 directory=docs['regions/index.html'];assert len(directory.cls('page-card'))==2,'Actual directory card count drift';assert not directory.where(key='data-shared-flower-banner'),'Thin directory banners forbidden'
 assert len(directory.where('li',key='data-legal-unit'))==34,'Legal inventory drift';assert len(directory.where('li',key='data-administrative-unit'))==18,'Administrative inventory drift'
 candidate_links=[]
 for u in c['units']:
  li=directory.where('li',key='data-legal-unit',value=u['unitKey']);assert len(li)==1
  expected=[a for p in pages for a in p['facilityAnchors'] if a['unitKey']==u['unitKey']];links=[n for n in descendants(li[0]) if n['tag']=='a'];assert [(x['attrs']['href'],x['text']) for x in links]==[(x['href'],x['heading']) for x in expected],'Legal facility destination drift'
  if not expected:assert ui['directory']['emptyUnitLabel'] in li[0]['text'],'Missing empty legal guide label'
  candidate_links.extend(links)
 assert len(candidate_links)==8,'Exactly eight legal facility anchors required'
 for admin in c['administrativeCrosswalk']:
  row=directory.where('li',key='data-administrative-unit',value=admin['aliasKey']);assert len(row)==1
  assert not any(n['tag']=='a' for n in descendants(row[0])),'Administrative rows must not imply venue assignment'
  names=[next(u['name'] for u in c['units'] if u['unitKey']==rel['unitKey'])+(' '+ui['directory']['partialLabel'] if rel['scope']=='partial' else '') for rel in admin['relations']]
  assert norm(row[0]['text'])==admin['name']+': '+' · '.join(names),'Official administrative relation text drift'
 notfound=Document((dist/'404.html').read_text());assert not notfound.canonical,'404 canonical forbidden';assert 'noindex' in notfound.meta['robots'],'404 indexable';assert not docs['404.html'].where(key='data-shared-flower-banner'),'404 banner forbidden'
 for banner in cp['common']['bannerPolicy']['banners']:
  path='/images/shared-banners/'+banner['file'];assert hashlib.sha256((dist/path.lstrip('/')).read_bytes()).hexdigest()==banner['sha256'],'Banner byte drift';assert asset_counts[path]==3,'Banner route count drift'
  for doc in docs.values():
   for n in doc.where('img',key='src',value=path):assert n['attrs']['alt']==banner['alt'],'Banner alt drift'
 report={'scope':'Static HTML only; screen/public HTTP/search unverified','htmlFiles':len(files),'details':entries,'uniqueSku':len(products),'legalEntries':34,'adminEntries':18,'officialRelations':45,'legalFacilityLinks':8,'administrativeFacilityLinks':0,'directoryCards':2,'directoryBanners':0,'directoryIndexable':False,'productionApproved':config['productionApproved']}
 if write:(root/'yeongdeungpo-static-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('YEONGDEUNGPO STATIC QA: '+json.dumps(report,ensure_ascii=False));return report
if __name__=='__main__':inspect()
