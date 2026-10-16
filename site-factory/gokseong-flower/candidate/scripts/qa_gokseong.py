#!/usr/bin/env python3
"""Independent Python JSON-to-HTML projection; static QA does not claim browser visibility."""
from pathlib import Path
from html_surface import BeautifulSoup
import hashlib,json,re,sys,xml.etree.ElementTree as ET
from urllib.parse import urlsplit,unquote
C=Path(__file__).resolve().parents[1]; B=C.parent; I=B/'inputs/reviewed-copy'
sha=lambda b:hashlib.sha256(b).hexdigest()
norm=lambda t:re.sub(r'\s+',' ',t).strip()
class QAError(AssertionError):pass
def must(v,code,detail=''):
 if not v:raise QAError(f'{code}: {detail}')
def htmlpath(p):return 'index.html' if p=='/' else '404.html' if p=='/404.html' else p.strip('/')+'/index.html'
def load(name):return json.loads((I/name).read_text())
routes={x['id']:x['proposedPath'] for x in load('render-plan.json')['pages']}
def target(c,v):return v['href']
def validate_copy_schema(c):
 must(list(c)==['home','productCards','notFound','sharedUI','sharedBannerAlt'],'COPY_FIVE_KEYS')
 must([s['id'] for s in c['home']['sections']]==['products','budget','ribbon','destinations','order'] and all('card' not in s for s in c['home']['sections']),'HOME_REVIEWED_ORDER')
 must(c['home']['sections'][0]['productCardIds']==['B201','B203','B205','B060'],'HOME_SKU_ORDER')
 must(len(c['home']['faq'])==3 and len({f['question'] for f in c['home']['faq']})==3,'HOME_FAQ_CONTRACT')
 for i,p in enumerate(c['productCards']):
  must(p['basePriceKRW']==[59000,79000,109000,149000][i] and p['additionalShippingKRW']==10000 and p['referenceTotalKRW']==p['basePriceKRW']+p['additionalShippingKRW'] and p['finalPriceKRW'] is None,'PRICE_ARITHMETIC')
  must(p['priceLabel']==f"상품 기본가 {p['basePriceKRW']:,}원" and p['shippingLabel']=='곡성 게시 추가배송비 10,000원' and p['referenceTotalLabel']==f"게시금액 합산 참고예산 {p['referenceTotalKRW']:,}원",'PRICE_LABELS')
 must(c==load('customer-copy.json'),'EXACT_REVIEWED_COPY')
 return True

def projection(key,c):
 validate_copy_schema(c);p=c[key];blocks=[];links=[]
 def t(tag,value):blocks.append((tag,value))
 def a(label,href):t('a',label);links.append((href,label))
 t('h1',p['h1'])
 if key=='home':
  for v in p['lead']:t('p',v)
  for s in p['sections']:
   t('h2',s['h2'])
   for v in s['paragraphs']:t('p',v)
   if s['id']=='products':
    for product in c['productCards']:
     t('h3',product['name']+' '+product['sku'])
     for field in ['priceLabel','shippingLabel','referenceTotalLabel','description']:t('p',product[field])
     a(product['ctaLabel'],product['ctaHref'])
    t('p',c['sharedUI']['productSampleNotice'])
   for v in s.get('list',[]):t('li',v)
   for v in s.get('afterList',[]):t('p',v)
  t('h2',p['faqHeading'])
  for faq in p['faq']:t('h3',faq['question']);t('p',faq['answer'])
  t('p',p['closing']);a(p['cta']['label'],p['cta']['href']);t('h2',p['sourceHeading']);t('p',p['sourceIntro'])
  for v in p['sources']:a(v['label'],v['url'])
 else:t('p',p['body']);a(p['cta']['label'],p['cta']['href'])
 return blocks,links
HIDDEN=re.compile(r'(?:^|;)\s*(?:display\s*:\s*none\b|visibility\s*:\s*(?:hidden|collapse)\b|content-visibility\s*:\s*hidden\b|opacity\s*:\s*[-+]?(?:0+(?:\.0*)?|\.0+)(?:e[-+]?\d+)?%?(?:\s*!important)?\s*(?:;|$)|font-size\s*:\s*0(?:px|rem|em)?\s*(?:;|$)|(?:width|max-width|height|max-height)\s*:\s*0(?:px|rem|em)?\s*(?:;|$)|clip(?:-path)?\s*:|transform\s*:\s*scale(?:X|Y)?\(\s*0\s*\))',re.I)
def visible(node,dom,css,code):
 must(node is not None,code,'Missing node')
 chain=[node,*node.parents,*node.descendants()]
 for n in chain:
  decorative=code=='MAIN_VISIBLE_STATIC' and n.name=='span' and n.get('aria-hidden')=='true' and n.get_text()=='›' and n.parent.name=='nav' and n.parent.get('class')=='breadcrumb'
  must(not any(n.has_attr(k) for k in ['hidden','inert']) and (n.get('aria-hidden','').lower()!='true' or decorative) and n.name not in ['template','details'] and not HIDDEN.search(n.get('style','')),code,str(n.attrs))
 for selector,decl in re.findall(r'([^{}]+)\{([^{}]*)\}',css):
  if not HIDDEN.search(decl):continue
  for branch in selector.split(','):
   branch=branch.strip()
   if branch.startswith('@'):continue
   must(':' not in branch,code,'Unsupported hiding selector: '+branch)
   must(not any(n in dom.select(branch) for n in chain),code,branch)
def footer_touch_css_contract(css):
 # Source/output declaration guard only. A browser must still verify actual hit boxes.
 declarations={}
 for selector,body in re.findall(r'([^{}]+)\{([^{}]*)\}',css):
  if 'footer a' not in [branch.strip() for branch in selector.split(',')]:continue
  for prop,value in re.findall(r'([\w-]+)\s*:\s*([^;]+)',body):declarations[prop.strip()]=value.strip()
 for prop,value in {'display':'inline-flex','align-items':'center','min-height':'44px','min-width':'44px'}.items():
  must(declarations.get(prop)==value,'FOOTER_TOUCH_CSS_CONTRACT',prop)
 return True

def input_contract():
 manifest=(B/'inputs/required-originals.json').read_bytes();pin=(C/'src/data/input-binding.json').read_bytes();binding=json.loads(pin)
 must(sha(manifest)==binding['requiredOriginalsSHA256']=='d9e4e75f99370c51201bf411f613b58ef1af6aa3be182a10a043741c0fcfb3dd','INPUT_MANIFEST_HASH')
 for row in json.loads(manifest):
  raw=(B/row['path']).read_bytes();must(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'REQUIRED_INPUT_HASH',row['path'])
 return binding


def check(root=None):
 root=Path(root or C/'dist');binding=input_contract();c=load('customer-copy.json');plan=load('render-plan.json');ui=c['sharedUI'];pm=json.loads((C/'src/data/page-map.json').read_text())
 validate_copy_schema(c)
 must(sha((I/'customer-copy.json').read_bytes())==binding['customerCopySHA256']=='3829721f442682c7b07f02b043b5ba80a0e1e0d5264babb7c96a7b2eadd0332e','CANONICAL_COPY_PIN')
 expected=[('home','home','primary-home'),('not-found','notFound','technical-404')]
 must(plan['region']=={'name':'곡성군','officialCode':'12720','legalCode':'1272000000','officialParent':'전남광주통합특별시','nationalOrder':37},'REGION_FACTS')
 must(plan['origin'] is None and plan['domain'] is None and plan['productionEnabled'] is False,'COPY_PRIVATE_SCOPE')
 must(pm['origin'] is None and pm['domain'] is None and pm['productionEnabled'] is False and pm['crossRegionPublicationPrerequisites'] is False,'PRIVATE_MAP_BOUNDARY')
 must(len(pm['pages'])==2 and {str(p.relative_to(root)) for p in root.rglob('*.html')}=={'index.html','404.html'},'HTML_DENOMINATOR')
 must(not (root/'regions').exists(),'NO_REGIONS_OUTPUT')
 must((root/'robots.txt').read_text()=='User-agent: *\nDisallow: /\n','ROBOTS_READABLE')
 must({str(p.relative_to(root)) for p in root.rglob('*.xml')}=={'sitemap.xml'} and len(ET.parse(root/'sitemap.xml').getroot())==0,'EMPTY_PREVIEW_SITEMAP')
 must((root/'_headers').read_text()=='/*\n  X-Robots-Tag: noindex, nofollow, noarchive\n','HEADERS_NOINDEX')
 must(not any((root/n).exists() for n in ['_worker.js','_redirects','_routes.json']),'NO_ROUTING_ADAPTER')
 static=['favicon.svg','robots.txt','sitemap.xml','_headers']+[x['publicPath'].lstrip('/') for x in load('asset-manifest.json')['assets']]
 cssfiles=[str(x.relative_to(root)) for x in root.glob('_astro/*.css')];must(len(cssfiles)==1,'CSS_ONE_FILE')
 files=[str(x.relative_to(root)) for x in root.rglob('*') if x.is_file()];must(set(files)==set(['index.html','404.html',*static,*cssfiles]),'EXACT_PRIVATE_INVENTORY')
 results=[];titles=[];descs=[];doms={};menu=[(x['href'],ui[x['labelSource'].split('.')[1]]) for x in plan['navigation']['mainMenu']]
 for id,key,role in expected:
  p=c[key];route=routes[key];entry=pm['pages'][expected.index((id,key,role))];must(entry=={'id':id,'copyKey':key,'path':route,'role':role,'title':p['title'],'description':p['description'],'h1':p['h1'],'robots':'noindex,nofollow,noarchive','canonical':None,'sitemapIncluded':False,'mainMenuIncluded':key=='home','actualChildCount':0,'marketingBannerCount':3 if key=='home' else 0,'coreHub':False},'MAP_EXACT_PAGE')
  primary=key=='home';text=(root/htmlpath(route)).read_text();dom=BeautifulSoup(text);doms[key]=dom;body=dom.find('body');article=dom.select_one('[data-page-id]');surface=norm(body.get_text(' ',True));blocks,links=projection(key,c)
  must(article and article.get('data-page-id')==id and article.get('data-page-role')==role and article.get('data-copy-sha')==binding['customerCopySHA256'],'HTML_BINDING')
  must([h.get_text() for h in dom.find_all('h1')]==[p['h1']],'H1')
  must(len(dom.find_all('title'))==1 and len(dom.select('meta[name="description"]'))==1 and len(dom.select('meta[property="og:title"]'))==(1 if primary else 0) and len(dom.select('meta[property="og:description"]'))==(1 if primary else 0),'METADATA_DENOMINATOR')
  title=dom.find('title').get_text();desc=dom.select_one('meta[name="description"]')['content'];titles.append(title);descs.append(desc);must(title==p['title'] and desc==p['description'],'METADATA')
  must([x.get('content') for x in dom.select('meta[name="robots"]')]==['noindex,nofollow,noarchive'],'ROBOTS_META')
  must(not dom.select('link[rel="canonical"]') and not dom.select('meta[property="og:url"]') and not dom.select('meta[property="og:image"]'),'NO_ABSOLUTE_METADATA')
  if not primary:must(not any(n.get('property','').startswith('og:') or n.get('name','').startswith('twitter:') for n in dom.find_all('meta')),'404_NO_SOCIAL')
  else:must(dom.select_one('meta[property="og:title"]')['content']==title and dom.select_one('meta[property="og:description"]')['content']==desc,'OG_REVIEWED_COPY')
  must(not any(k.lower().startswith('on') or k.lower()=='srcdoc' for n in dom.descendants() for k in n.attrs),'NO_EXECUTABLE_ATTRIBUTES')
  must(not dom.find_all('script') and not dom.find_all('form') and not dom.find_all('iframe') and not dom.select('meta[name="keywords"]'),'NO_UNREQUESTED_CONTENT_OR_TRANSMISSION')
  must(len(dom.find_all('main'))==1 and dom.find('main').get('id')=='main-content' and dom.find('main').get('tabindex')=='-1','MAIN_FOCUS_TARGET');must(dom.select_one('.skip-link').get('href')=='#main-content','SKIP_LINK')
  ids=[n.get('id') for n in dom.select('[id]')];must(len(ids)==len(set(ids)),'DUPLICATE_ID')
  css='\n'.join((root/x['href'].lstrip('/')).read_text() for x in dom.select('link[rel="stylesheet"]'))+'\n'+'\n'.join(x.get_text() for x in dom.find_all('style'))
  footer_touch_css_contract(css)
  level=0
  for h in dom.find_all(['h1','h2','h3','h4','h5','h6']):n=int(h.name[1]);must(n<=level+1 if level else n==1,'HEADING_ORDER');level=n
  for a in dom.find_all('a'):
   href=a.get('href','');must(href and href!='#' and not href.startswith(('javascript:','data:','//')),'LINK_SAFETY');parsed=urlsplit(href)
   must('/regions/' not in href,'NO_REGIONS_LINK')
   if href.startswith(('/','#')):
    file=htmlpath(parsed.path or route);must((root/file).is_file(),'INTERNAL_LINK',href)
    if parsed.fragment:targetdom=dom if not parsed.path else BeautifulSoup((root/file).read_text());must(any(x.get('id')==unquote(parsed.fragment) for x in targetdom.select('[id]')),'ANCHOR_TARGET',href)
   elif href.startswith('tel:'):must(href=='tel:18440644','ONLY_SALES_PHONE_CTA')
   else:must(href.startswith('https://'),'LINK_SAFETY')
  for nav in dom.select('header nav'):must([(a.get('href'),a.get_text()) for a in nav.find_all('a')]==menu and nav.get('aria-label')==ui['menuLabel'],'MAIN_MENU')
  must(not dom.select('nav.breadcrumb'),'NO_FAKE_BREADCRUMB')
  must(dom.select_one('.brand').get('href')=='/','BRAND_HOME_TARGET')
  must([(a.get('href'),a.get_text()) for a in dom.find('footer').find_all('a')]==[('tel:18440644',ui['phoneLink']),('/',ui['homeLink'])],'FOOTER_LINK_PARITY')
  must([(a.get('href'),a.get_text()) for a in dom.select_one('.mobile-bar').find_all('a')]==[('/',ui['homeLink']),('tel:18440644',ui['phoneLink'])],'MOBILE_BAR_LINK_PARITY')
  must(len(dom.select('header nav'))==2 and len(dom.select('details.mobile-menu'))==1 and len(dom.select('details.mobile-menu summary'))==1,'NATIVE_MENU_STRUCTURE')
  for img in dom.find_all('img'):must(img.get('alt') and img.get('width') and img.get('height') and img.get('loading')=='lazy' and img.get('decoding')=='async' and img.get('src','').startswith('/') and (root/img['src'].lstrip('/')).is_file(),'IMAGE_ATTRIBUTES')
  must(len(dom.find_all('img'))==(7 if primary else 0),'IMAGE_DENOMINATOR')
  banners=dom.select('[data-shared-flower-banner]');must([b.get('data-shared-flower-banner') for b in banners]==(['message','budget','consultation'] if primary else []),'BANNER_SET')
  for i,(b,e) in enumerate(zip(banners,plan['commonBanners'])):
   img=b.find('img');must(b.name=='figure' and not b.find('figcaption') and len(b.find_all('img'))==1,'BANNER_WRAPPER');must(img.get('src')==e['publicPath'] and img.get('alt')==c['sharedBannerAlt'][e['variant']],'BANNER_ALT_SRC');must(img['width']=='1774' and img['height']=='887','BANNER_DIMENSIONS');must(sha((root/img['src'].lstrip('/')).read_bytes())==e['sha256'],'BANNER_BYTES')
   prev=b.find_previous_sibling();nxt=b.find_next_sibling();must(prev and nxt,'BANNER_SIBLINGS')
   must((prev.get('id'),nxt.get('id'))==[('opening','products'),('budget','ribbon')][i] if i<2 else prev.get('id')=='faq' and 'directory-closing' in nxt.get('class',''),'BANNER_PLACEMENT');visible(img,dom,css,'BANNER_VISIBLE_STATIC')
  cards=dom.select('[data-product-sku]');must(len(cards)==(4 if primary else 0),'PRODUCT_COUNT')
  for card,e in zip(cards,c['productCards']):
   must(card.get('data-product-sku')==e['sku'] and card.get('id')=='product-'+e['sku'] and card.find('h3').get_text()==e['name']+' '+e['sku'],'PRODUCT_COPY')
   must([x.get_text() for x in card.find_all('p')]==[e[k] for k in ['priceLabel','shippingLabel','referenceTotalLabel','description']],'PRODUCT_ALL_COPY')
   reference=card.select_one('[data-reference-total-krw]');must(reference is not None and reference.get('data-reference-total-krw')==str(e['referenceTotalKRW']) and reference.get_text()==e['referenceTotalLabel'],'REFERENCE_TOTAL_VISIBLE');visible(reference,dom,css,'REFERENCE_VISIBLE_STATIC')
   img=card.find('img');must(img.get('src')==f"/images/products/{e['sku']}.jpg" and img.get('alt')==e['photoAlt'] and img.get('width')=='500' and img.get('height')=='500','PRODUCT_IMAGE_ATTRIBUTES');must(sha((root/img['src'].lstrip('/')).read_bytes())==next(a['sha256'] for a in [a for a in load('asset-manifest.json')['assets'] if a.get('sku')] if a['sku']==e['sku']),'PRODUCT_IMAGE_BYTES');a=card.select_one('[data-order-product-sku]');must(a and a.get('href')==e['ctaHref'] and a.get_text()==e['ctaLabel'],'PRODUCT_CTA');visible(a,dom,css,'PRODUCT_CTA_VISIBLE')
  for a in article.select('[data-required-cta]'):visible(a,dom,css,'REQUIRED_CTA_VISIBLE')
  qs=dom.select('[data-faq-question]');ans=dom.select('[data-faq-answer]');must(len(qs)==len(ans)==(3 if primary else 0),'FAQ_COUNT')
  for i,(q,a,e) in enumerate(zip(qs,ans,c['home']['faq'])):
   must(q.name=='h3' and q.get_text()==e['question'] and a.name=='p' and a.get_text()==e['answer'] and q.parent.get('id')==f'faq-{i+1}','FAQ_COPY');must(q.find_next_sibling() is a,'FAQ_IMMEDIATE_ANSWER');must(surface.count(norm(q.get_text()))==surface.count(norm(a.get_text()))==1,'FAQ_ONCE');visible(q,dom,css,'FAQ_VISIBLE_STATIC');visible(a,dom,css,'FAQ_VISIBLE_STATIC')
  render=dom.select_one('[data-reviewed-body]');must(render is not None,'REVIEWED_BODY')
  must([(n.name,norm(n.get_text())) for n in render.select('[data-reviewed-block]')]==[(t,norm(v)) for t,v in blocks],'BODY_BLOCK_SEQUENCE')
  must([(a.get('href'),a.get_text()) for a in render.find_all('a')]==links,'BODY_LINK_PARITY')
  must(all(not isinstance(child,str) or not child.strip() or any(n.has_attr('data-reviewed-block') for n in [node,*node.parents]) for node in [render,*render.descendants()] for child in node.children),'BODY_TEXT_PARITY')
  chrome_start=[ui['skipLink'],'✿',ui['brand'],*[label for _,label in menu],ui['menuOpen'],ui['menuClose'],*[label for _,label in menu]]
  chrome_end=[ui['brand'],ui['footerLabel'],ui['phoneLink'],ui['homeLink'],ui['homeLink'],ui['phoneLink']]
  must(surface==norm(' '.join(chrome_start+[v for _,v in blocks]+chrome_end)),'ALL_BODY_TEXT_PARITY')
  must(dom.find('footer').get('aria-label')==ui['footerLabel'] and dom.select_one('.brand').get('aria-label')==ui['homeLink'],'CHROME_ACCESSIBLE_LABELS')
  must(len(dom.select('[data-source-references]'))==(1 if primary else 0),'SOURCES_ONCE')
  visible(dom.find('main'),dom,css,'MAIN_VISIBLE_STATIC')
  for forbidden in ['광산구','북구','그린장례','남구','남문장례','서구','국빈장례','풍서좌로','동구','조선대학교','필문대로','광양','나주','전남대학교','전남대병원','순천','성가롤로','여수','목포','강동','061-720','061-640','무료배송','100% 환불','당일배송','AI 생성 이미지','Launch Gate']:must(forbidden not in surface+title+desc,'REGIONAL_COPY_REGRESSION',forbidden)
  results.append({'id':id,'copyKey':key,'path':route,'sha256':sha(text.encode()),'products':len(cards),'faqPairsInStaticHTML':len(qs),'banners':len(banners),'images':len(dom.find_all('img')),'requiredCTAs':len(article.select('[data-required-cta]')),'robots':'noindex,nofollow,noarchive','canonical':None})
 must(len(set(titles))==len(set(descs))==2,'UNIQUE_METADATA')
 from qa_occurrences import check as occurrences
 contexts=occurrences(root,'private')
 return {'status':'PASS_PRIVATE_STATIC_ONLY','renderSource':'REVIEWED_SINGLE_JSON_ONLY','customerCopySHA256':binding['customerCopySHA256'],'pages':results,'htmlFiles':len(results),'outputFiles':len(files),'outputInventory':sorted(files),'authoredContexts':contexts,'referenceTotalsKRW':[p['referenceTotalKRW'] for p in c['productCards']],'facilityDetailCount':0,'supportCount':0,'breadcrumbPages':[],'origin':None,'productionEnabled':False,'limitations':['Static HTML and simple hiding styles only; browser/computed CSS/mobile not verified','Private title and OG text checked; production Twitter/absolute metadata delegated to release adapter','No public HTTP/real404/provider/IndexNow/checkout/telephone execution']}

def context_coverage(c,doms):
 from qa_occurrences import check as occurrences
 return occurrences(C/'dist','private')
if __name__=='__main__':
 try:
  result=check(Path(sys.argv[1]) if len(sys.argv)>1 else None);(C/'evidence').mkdir(exist_ok=True);(C/'evidence/static-qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
