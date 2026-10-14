from pathlib import Path
from html_surface import BeautifulSoup
from urllib.parse import urljoin,urlsplit
from collections import Counter
import json,hashlib,sys,re
ROOT=Path(__file__).resolve().parents[1]

def inspect(dist=None,root=ROOT):
 dist=Path(dist or root/'dist');r=json.loads((root/'src/data/gangdong-runtime.json').read_text());errors=[];checks=[];extract=[];docs={};rolemap=[]
 def ok(value,label):
  checks.append({'check':label,'passed':bool(value)})
  if not value:errors.append(label)
 def txt(n):return n.get_text(' ',strip=True) if n else ''
 def exact(n,s):return n is not None and txt(n)==s
 def readable(n):
  return n is not None and not any(x.name in ['script','style','template','details'] or x.has_attr('inert') or any(c in x.get('class','').split() for c in ['hidden','sr-only','visually-hidden']) or x.has_attr('hidden') or x.get('aria-hidden')=='true' or any(v in x.get('style','').replace(' ','').lower() for v in ['display:none','visibility:hidden','opacity:0']) for x in [n,*n.parents] if getattr(x,'attrs',None) is not None)
 def output(p):return '404.html' if p=='/404.html' else p.lstrip('/')+'index.html'
 expected={output(p['path']) for p in r['pages']}
 inventory=json.loads((root/'src/data/frozen/all-strings-inventory.json').read_text())['strings']
 allowed=[row['text'] for row in inventory]+[r['common']['productLabels']['sku']+' '+prod['sku'] for prod in r['products']]
 ok({str(p.relative_to(dist)) for p in dist.rglob('*.html')}==expected,'exact 5 HTML routes')
 for p in r['pages']:
  htmlfile=dist/output(p['path']);s=BeautifulSoup(htmlfile.read_text(),'html.parser');docs[p['path']]=s;article=s.select_one(f'article[data-page-id="{p["id"]}"]');h1=article.find('h1')
  ok(len(s.find_all('h1'))==1 and exact(h1,p['h1']),p['id']+' one exact H1')
  ok(exact(s.title,p['title']),p['id']+' exact title')
  ok(s.select_one('meta[name=description]')['content']==p['metaDescription'],p['id']+' exact meta description')
  ok(s.select_one('meta[name=robots]')['content']=='noindex,nofollow,noarchive',p['id']+' local robots')
  ok((not s.select('link[rel=canonical]') and not any(n.get('property','').startswith('og:') for n in s.find_all('meta'))) if p['id']=='404' else s.select_one('link[rel=canonical]')['href']==urljoin(r['origin'],p['path']),p['id']+' local canonical / utility404 exclusion')
  first=h1.find_next_sibling();ok(exact(first,p['firstAnswer']) and first.name=='p' and readable(first),p['id']+' first answer immediately after H1')
  ok(sum(txt(x)==p['firstAnswer'] for x in article.find_all('p'))==1,p['id']+' first answer single rendering')
  ok(not s.select('meta[name=naver-site-verification],script[type="application/ld+json"]'),p['id']+' no ownership or unsupported schema')
  for v in ['gwanak','gangnam','geumcheon','seocho','songpa','관악','강남','금천','서초','송파']:
   ok(v not in txt(article).lower() and v not in ' '.join(a.get('href','') for a in s.find_all('a')),p['id']+' no region leak '+v)
  for node in s.descendants():
   ok(not any(k.lower().startswith('on') for k in node.attrs) and node.name not in ['script','iframe','object','embed','form','base'],p['id']+' passive HTML node '+node.name)
  body=s.find('body')
  for node in [body,*body.descendants()]:
   for segment in node.children:
    if isinstance(segment,str) and re.search(r'[A-Za-z0-9가-힣]',segment):
     value=' '.join(segment.split());ok(any(value in approved for approved in allowed),p['id']+' approved text only '+value[:70])
  # Every reviewed body field is inspected at its actual semantic container in exact reading order.
  ok([txt(x) for x in s.select('#opening>p')]==[p['firstAnswer'],*p.get('openingParagraphs',[])],p['id']+' exact opening sequence')
  sections=s.select('[data-copy-section]');ok([x['id'] for x in sections]==[x['id'] for x in p.get('sections',[])],p['id']+' section sequence')
  for src,node in zip(p.get('sections',[]),sections):
   name=p['id']+'/'+src['id'];ok(exact(node.find('h2',recursive=False),src['heading']),name+' H2')
   ok([txt(x) for x in node.find_all('p',recursive=False)]==src.get('paragraphs',[])+src.get('closingParagraphs',[]),name+' exact paragraphs')
   subs=node.select(':scope>.copy-subsection');ok(len(subs)==len(src.get('subsections',[])),name+' subsections')
   for sub,subnode in zip(src.get('subsections',[]),subs):
    ok(exact(subnode.find('h3'),sub['heading']) and [txt(x) for x in subnode.find_all('p',recursive=False)]==sub['paragraphs'],name+'/'+sub['heading']+' exact subsection')
   ok([txt(x) for x in node.select(':scope>ul>li')]==src.get('listItems',[]),name+' list')
   actualCards=node.select('[data-purchase-cards]>.page-card')
   ok(len(actualCards)==len(src.get('cards',[])),name+' purpose card count')
   for card,cardnode in zip(src.get('cards',[]),actualCards):ok(exact(cardnode.find('h3'),card['heading']) and exact(cardnode.find('p'),card['summary']),name+' exact purpose card')
  faq=s.select('[data-faq-entry]');ok(len(faq)==len(p.get('faqs',[])),p['id']+' FAQ count')
  for f,node in zip(p.get('faqs',[]),faq):
   q=node.select_one('[data-faq-question]');a=node.select_one('[data-faq-answer]');ok(exact(q,f['question']) and exact(a,f['answer']) and readable(q) and readable(a),p['id']+' visible exact FAQ '+f['question'])
  src=s.select_one('[data-source-references]')
  ok(len(s.select('[data-source-references] h2'))==(1 if p.get('sourcesHeading') else 0),p['id']+' one grouped source H2')
  if p.get('sourcesHeading'):
   ok(exact(src.find('h2'),p['sourcesHeading']) and exact(src.find('p'),p['sourceNote']),p['id']+' source heading/note')
   ok([(txt(a),a['href']) for a in src.select('a')]==[(a['label'],a['href']) for a in p['officialSources']],p['id']+' exact official sources')
  # Validate every exact approved label/href (including per-FAQ links), not merely a source-domain count.
  links=[]
  def walk(v):
   if isinstance(v,list):
    for x in v:walk(x)
   elif isinstance(v,dict):
    if 'href'in v:links.append((v.get('label',v.get('ctaLabel')),v['href']))
    for k,x in v.items():
     if k!='href':walk(x)
  walk(p)
  available=Counter((txt(a),a.get('href')) for a in article.select('a'))
  for pair,count in Counter(links).items():ok(available[pair]>=count,p['id']+' exact link '+str(pair))
  banners=s.select('[data-shared-flower-banner]');ok([b['data-shared-flower-banner'] for b in banners]==[b['banner'] for b in p['bannerPlacement']],p['id']+' banner eligibility/order')
  for placement,b in zip(p['bannerPlacement'],banners):
   source=next(x for x in r['common']['banners'] if x['id']==placement['banner']);im=b.find('img');ok(im['alt']==source['alt'] and im['src']==f'/images/shared-banners/{source["assetName"]}' and im['width']=='1774' and im['height']=='887' and im.get('loading')=='lazy' and not b.find('figcaption'),p['id']+' exact banner '+placement['banner'])
   prev=b.find_previous_sibling();expectedId='opening' if placement['after']=='openingParagraphs' else placement['after'];ok(prev is not None and prev.get('id')==expectedId,p['id']+' banner real-content spacing '+placement['banner'])
  skus=[x['sku'] for x in r['products']] if p['id']=='home' else [x for sec in p.get('sections',[]) for x in sec.get('productSKUs',[])]
  cards=s.select('[data-product-sku]');ok([n['data-product-sku'] for n in cards]==skus,p['id']+' exact product order/count')
  for sku,n in zip(skus,cards):
   prod=next(x for x in r['products'] if x['sku']==sku);ok(n.get('data-product-family')==prod['family'],p['id']+' product family '+sku);im=n.find('img');a=n.select_one('[data-order-product-sku]');heading=n.find(['h3','h4']);ok(exact(heading,prod['name']) and txt(n.find('strong'))==prod['priceText'] and prod['description'] in [txt(x) for x in n.find_all('p')] and a['href']==prod['cta']['href'] and txt(a)==prod['cta']['label'] and im['src']==prod['img'] and im['alt']==prod['alt'] and im['width']=='500' and im['height']=='500' and im.get('loading')=='lazy',p['id']+' product '+sku)
  headings=s.select('main h1,main h2,main h3,main h4');levels=[int(x.name[1]) for x in headings];ok(all(b<=a+1 for a,b in zip(levels,levels[1:])),p['id']+' no skipped heading levels')
  ids=[x['id'] for x in s.select('[id]')];ok(len(ids)==len(set(ids)),p['id']+' unique IDs')
  for anchor in r['presentation']['requiredAnchors'].get(p['path'],[]):ok(anchor in ids,p['id']+' planned anchor '+anchor)
  if p['id']=='directory':ok(len(s.select('[data-purchase-cards]>.page-card'))==2 and not banners,p['id']+' actual 2-card no-banner exception')
  ok(all(a.get('href')!='/regions/' for a in s.select('.site-header nav a')),p['id']+' directory absent primary menu')
  ok(bool(s.select('a[href="tel:18440644"]')),p['id']+' real phone CTA')
  ok(all(im.get('alt') and im.get('width') and im.get('height') for im in s.find_all('img')),p['id']+' image accessibility/dimensions')
  extract.append({'id':p['id'],'path':p['path'],'htmlSHA256':hashlib.sha256(htmlfile.read_bytes()).hexdigest(),'title':txt(s.title),'metaDescription':s.select_one('meta[name=description]')['content'],'h1':txt(h1),'firstProseAfterH1':txt(first),'first100Characters':txt(first)[:100],'headingOutline':[{'level':x.name,'text':txt(x)} for x in headings],'faqs':[{'question':txt(n.select_one('[data-faq-question]')),'answer':txt(n.select_one('[data-faq-answer]'))} for n in faq],'articleText':txt(article),'A04Score':'UNASSESSED_IMPLEMENTER_NOT_INDEPENDENT_REVIEWER'})
 # Full frozen inventory accounting. Copy leaves remain immutable; classify the actual output role.
 for row in inventory:
  if not row['customerText']:continue
  name=row['file'];pointer=row['pointer'];value=row['text'];targets=[];state='';reason=''
  if row['surface']=='existing_banner_pixel_text':
   index=int(pointer.split('/')[2]);b=r['common']['banners'][index];asset=next(a for a in r['assets'] if a['path'].endswith('/'+b['assetName']));targets=[asset['path']];state='approved_unchanged_image_pixels';reason='Frozen approved image bytes verified separately; no duplicate HTML caption.'
  elif name=='home-copy.json' and pointer=='/cardSummary':
   state='preserved_unrendered_no_home_card_slot';reason='Home has no self-card in this five-route design. The exact reviewed field remains in frozen copy/runtime, without injecting redundant customer prose.'
  else:
   subset=docs if name in ['common-copy.json','product-copy.json'] or pointer=='/cardSummary' else {page['path']:docs[page['path']] for page in r['pages'] if name==page['id']+'-copy.json'}
   if row['surface']=='head_metadata':
    for path,doc in subset.items():
     node=doc.title if pointer=='/title' else doc.select_one('meta[name=description]')
     if (txt(node) if pointer=='/title' else node['content'])==value:targets.append(path+(' <title>' if pointer=='/title' else ' meta[name=description]'))
    state='head_metadata'
   elif row['surface']=='accessibility_text' or (name=='common-copy.json' and pointer in ['/mobileMenu/label','/faqLabel']):
    for path,doc in subset.items():
     if any(n.get('alt')==value or n.get('aria-label')==value for n in doc.descendants()):targets.append(path+' exact alt/aria-label')
    state='accessibility_attribute'
   else:
    for path,doc in subset.items():
     for n in doc.find('body').descendants():
      if txt(n)==value and (readable(n) or (name=='common-copy.json' and pointer.startswith('/mobileMenu/'))):targets.append(path+' '+n.name);break
     if not any(t.startswith(path+' ') for t in targets) and (row['surface']=='visible_catalog_identifier' or (name=='common-copy.json' and pointer in ['/phone/display','/productLabels/sku'])) and value in txt(doc.find('body')):targets.append(path+' within exact bound label')
    state='conditional_mobile_control' if name=='common-copy.json' and pointer.startswith('/mobileMenu/') else 'customer_HTML_text'
   ok(bool(targets),'inventory exact output role '+name+pointer)
  rolemap.append({**row,'outputRole':state,'targets':targets,'reason':reason})
 ok(len(rolemap)==249,'all249customer inventory roles accounted')
 # Resolve all local links/fragments against actual HTML outputs; no invented alias URLs.
 inbound=Counter()
 for page,s in docs.items():
  for a in s.select('a[href]'):
   href=a['href'];u=urlsplit(urljoin(r['origin']+page,href))
   if u.netloc!=urlsplit(r['origin']).netloc:continue
   target=docs.get(u.path);ok(target is not None,page+' internal route '+href)
   if target is not None and u.fragment:ok(target.find(id=u.fragment) is not None,page+' internal anchor '+href)
   if u.path!=page:inbound[u.path]+=1
 for p in ['/','/regions/','/regions/gangdong-condolence-wreath/','/regions/gangdong-wedding-wreath/']:ok(inbound[p]>0,'inbound '+p)
 ok(len({txt(s.title) for s in docs.values()})==5,'unique titles');ok(len({s.select_one('meta[name=description]')['content'] for s in docs.values()})==5,'unique descriptions')
 ok((dist/'robots.txt').read_text()=='User-agent: *\nDisallow: /\n','robots disallow all')
 ok(not BeautifulSoup((dist/'sitemap.xml').read_text(),'xml').find_all('loc'),'empty sitemap')
 ok('X-Robots-Tag: noindex, nofollow, noarchive' in (dist/'_headers').read_text(),'static response noindex contract')
 expected_assets={a['path'].removeprefix('public/') for a in r['assets']}
 for a in r['assets']:
  f=dist/a['path'].removeprefix('public/');ok(f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==a['sha256'],'output asset bytes '+a['path'])
 ok({str(p.relative_to(dist)) for p in (dist/'images').rglob('*') if p.is_file()}==expected_assets,'only 11 approved images')
 ok(not any(p.name.startswith(('google','naver')) or (p.suffix=='.txt' and p.name!='robots.txt') for p in dist.iterdir() if p.is_file()),'no ownership files')
 css='\n'.join(p.read_text() for p in (dist/'_astro').glob('*.css'))
 ok('object-fit:contain' in css and re.search(r'aspect-ratio:1(?:/1)?[;}]',css) and re.search(r'aspect-ratio:2(?:/1)?[;}]',css),'responsive uncropped image CSS source')
 hidden_rules=[]
 for selector,decl in re.findall(r'([^{}]+)\{([^{}]*)\}',css):
  if re.search(r'(?:display:none|visibility:hidden|content-visibility:hidden|opacity:0(?:[;} ]|$)|font-size:0(?:px)?[;}]|color:transparent)',decl):
   if not all(any(token in part for token in ['.site-header nav','.phone','.mobile-bar','.mobile-menu','.menu-open','.menu-close']) for part in selector.split(',')):hidden_rules.append(selector)
 ok(not hidden_rules,'no static CSS hiding approved body/FAQ')
 return {'status':'PASS_STATIC_HTML' if not errors else 'FAIL','scope':'Compiled HTML/asset inspection only; no browser/computed-layout/public HTTP verification.','checks':len(checks),'failures':errors,'checkDetails':checks,'extraction':extract,'inventoryRoleMap':rolemap}
if __name__=='__main__':
 result=inspect(sys.argv[1] if len(sys.argv)>1 else None)
 (ROOT/'gangdong-static-qa.json').write_text(json.dumps({k:v for k,v in result.items() if k not in ['extraction','inventoryRoleMap']},ensure_ascii=False,indent=2)+'\n')
 (ROOT/'customer-string-output-role-map.json').write_text(json.dumps({'scope':'Exact frozen249customer strings classified against static output; no computed visual visibility claim.','rows':result['inventoryRoleMap']},ensure_ascii=False,indent=2)+'\n')
 (ROOT/'rendered-copy-extraction.json').write_text(json.dumps(result['extraction'],ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'checks':result['checks'],'failures':result['failures']},ensure_ascii=False,indent=2));sys.exit(bool(result['failures']))
