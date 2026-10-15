#!/usr/bin/env python3
"""Independent original-Markdown -> built HTML comparison; static checks, not browser QA."""
from pathlib import Path
from html_surface import BeautifulSoup
import hashlib,json,re,sys,xml.etree.ElementTree as ET
from urllib.parse import urlsplit
C=Path(__file__).resolve().parents[1];W=C.parent.parent;INPUT=W/'yeosu-customer-copy-20261014';SPECFILE=W/'yeosu-page-spec-addendum-20261015/page-spec-addendum.ko.json'
SPEC_SHA='b7fd276f969d473b60619cafca6ed160a442fdf5feb36b1bb1addccdaeb96b1f'
sha=lambda b:hashlib.sha256(b).hexdigest()
norm=lambda t:re.sub(r'\s+',' ',t).strip()
class QAError(AssertionError):pass
def must(v,code,detail=''):
 if not v:raise QAError(f'{code}: {detail}')
def htmlpath(path):return 'index.html' if path=='/' else '404.html' if path=='/404.html' else path.strip('/')+'/index.html'
def map_href(href):return '/regions/yeosu-jeonnam-hospital-funeral-wreath/' if href=='yeosu-jeonnam-hospital-funeral.ko.md' else href
def plain(text):return re.sub(r'\[([^\]]+)\]\([^)]+\)',lambda m:m[1],text)
def original_projection(markdown,spec):
 # Separate line-based parser: does not import or execute the renderer/parser.
 blocks=[];links=[];images=[];lines=markdown.strip().splitlines();i=0
 while i<len(lines):
  text=lines[i];i+=1
  if not text.strip() or text.startswith('<!--'):continue
  image=re.fullmatch(r'!\[([^\]]+)\]\(([^)]+)\)',text)
  if image:images.append((spec['productBinding']['imageMappings'][image[2]],image[1]));continue
  heading=re.match(r'^(#{1,3}) (.+)$',text)
  if heading:tag='h'+str(len(heading[1]));text=heading[2]
  elif text.startswith('- '):tag='li';text=text[2:]
  else:
   while i<len(lines) and lines[i].strip() and not re.match(r'^(#|<!--|- |!\[)',lines[i]):text+='\n'+lines[i];i+=1
   tag='a' if re.fullmatch(r'\[[^\]]+\]\([^)]+\)',text) else 'p'
  links.extend((map_href(m[2]),m[1]) for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)',text))
  blocks.append((tag,norm(plain(text))))
 return blocks,links,images
HIDDEN=re.compile(r'(?:^|;)\s*(?:display\s*:\s*none\b|visibility\s*:\s*(?:hidden|collapse)\b|content-visibility\s*:\s*hidden\b|opacity\s*:\s*[-+]?(?:0+(?:\.0*)?|\.0+)(?:e[-+]?\d+)?%?(?:\s*!important)?\s*(?:;|$)|font-size\s*:\s*0(?:px|rem|em)?\s*(?:;|$)|(?:width|max-width|height|max-height)\s*:\s*0(?:px|rem|em)?\s*(?:;|$)|clip(?:-path)?\s*:|transform\s*:\s*scale(?:X|Y)?\(\s*0\s*\))',re.I)
def static_visible(node,dom,css,code):
 must(node is not None,code,'Missing required node')
 chain=[node,*node.parents,*node.descendants()]
 for n in chain:
  must(not any(n.has_attr(k) for k in ['hidden','inert']) and n.get('aria-hidden','').lower()!='true' and n.name not in ['template','details'] and not HIDDEN.search(n.get('style','')),code,n.name+str(n.attrs))
 # Detect straightforward stylesheet hiding on required nodes or ancestors. This is not a CSS cascade engine.
 for selector,decl in re.findall(r'([^{}]+)\{([^{}]*)\}',css):
  if not HIDDEN.search(decl):continue
  for branch in selector.split(','):
   branch=branch.strip()
   if branch.startswith('@'):continue
   must(':' not in branch,code,'Unsupported hiding pseudo-selector needs browser verification: '+branch)
   try:matched=dom.select(branch)
   except Exception:continue
   must(not any(n in matched for n in chain),code,'Hiding CSS: '+branch)
def check(root=C/'dist',page_map=None):
 root=Path(root);raw=SPECFILE.read_bytes();must(sha(raw)==SPEC_SHA,'SPEC_HASH');spec=json.loads(raw)
 for b in spec['sourceBindings']:data=(INPUT/b['file']).read_bytes();must(len(data)==b['bytes'] and sha(data)==b['sha256'],'SOURCE_HASH',b['file'])
 page_map=page_map or json.loads((C/'src/data/page-map.json').read_text())
 must(page_map['origin'] is None and page_map['domain'] is None and page_map['canonical'] is None and page_map['productionEnabled'] is False and page_map['mode']=='private-local-preview','BOUNDARY')
 must(page_map['coreHubLaunchStatus']==page_map['fullLaunchStatus']=='NOT_ASSESSED','LAUNCH_SCOPE')
 for field,count in {'articleCount':1,'primaryCount':2,'supportCount':1,'contentHtmlCount':3,'technicalHtmlCount':1,'allHtmlCount':4,'previewIndexableCount':0,'previewSitemapUrlCount':0}.items():must(page_map[field]==count,'MAP_DENOMINATOR',field)
 must(page_map['launchOrder']==spec['launchOrder'] and page_map['launchOrder']['MokpoStillPending'],'ORDER_UNCHANGED')
 expected={htmlpath(p['path']) for p in spec['pages']};actual={str(p.relative_to(root)) for p in root.rglob('*.html')};must(actual==expected and len(actual)==4,'HTML_DENOMINATOR',str(actual))
 must([p['path'] for p in page_map['pages']]==[p['path'] for p in spec['pages']],'MAP_PATHS')
 for p in page_map['pages']:must(p['robots']=='noindex,follow' and p['canonical'] is None and p['sitemapIncluded'] is False and p['coreHub'] is False,'MAP_BOUNDARY')
 support=next(p for p in page_map['pages'] if p['id']=='support');must(support['actualChildCount']==1 and support['mainMenuIncluded'] is False and support['marketingBannerCount']==0,'SUPPORT_MAP')
 must((root/'robots.txt').read_text()=='User-agent: *\nAllow: /\n','ROBOTS_READABLE')
 must({p.name for p in root.rglob('*.xml')}=={'sitemap.xml'} and len(ET.parse(root/'sitemap.xml').getroot())==0,'EMPTY_PREVIEW_SITEMAP')
 must('X-Robots-Tag: noindex, follow' in (root/'_headers').read_text(),'HEADERS_NOINDEX')
 must(not any((root/n).exists() for n in ['_worker.js','_redirects','_routes.json']),'NO_ROUTING_ADAPTER')
 products=json.loads((INPUT/'product-cards.json').read_text());results=[];titles=[];descriptions=[]
 for page in spec['pages']:
  path=htmlpath(page['path']);text=(root/path).read_text();dom=BeautifulSoup(text);body=dom.find('body');article=dom.select_one('[data-page-id]');surface=norm(body.get_text())
  copy=spec['newCopyRequiringIndependentReview']['support' if page['id']=='support' else 'notFound'] if page['id'] in ['support','not-found'] else page
  must(article and article.get('data-page-id')==page['id'] and article.get('data-page-role')==page['role'] and article.get('data-copy-sha')==SPEC_SHA,'HTML_BINDING',path)
  must([h.get_text() for h in dom.find_all('h1')]==[copy['h1']],'H1',path)
  title=dom.find('title').get_text();desc=dom.select_one('meta[name="description"]').get('content');titles.append(title);descriptions.append(desc);must(title==copy['title'] and desc==copy['metaDescription'],'METADATA',path)
  must([m.get('content') for m in dom.select('meta[name="robots"]')]==['noindex,follow'],'ROBOTS_META',path)
  must(not dom.select('link[rel="canonical"]') and not dom.select('meta[property="og:url"]') and not dom.select('meta[property="og:image"]'),'NO_ABSOLUTE_METADATA',path)
  must(not dom.find_all('script') and not dom.find_all('form') and not dom.find_all('iframe'),'NO_ACTIVE_TRANSMISSION',path)
  must(len(dom.find_all('main'))==1 and dom.find('main').get('id')=='main-content' and dom.find('main').get('tabindex')=='-1','MAIN_FOCUS_TARGET',path)
  must(dom.select_one('.skip-link').get('href')=='#main-content','SKIP_LINK')
  css='\n'.join((root/l['href'].lstrip('/')).read_text() for l in dom.select('link[rel="stylesheet"]'))+'\n'+'\n'.join(s.get_text() for s in dom.find_all('style'))
  previous=0
  for h in dom.find_all(['h1','h2','h3','h4','h5','h6']):level=int(h.name[1]);must(level<=previous+1 if previous else level==1,'HEADING_ORDER',h.get_text());previous=level
  for a in dom.find_all('a'):
   href=a.get('href','');must(href and href!='#' and not href.startswith(('javascript:','data:','//')),'LINK_SAFETY',href)
   if href.startswith('/'):must((root/htmlpath(urlsplit(href).path)).is_file() or (root/href.lstrip('/')).is_file(),'INTERNAL_LINK',href)
   if href.startswith('#'):must(dom.select_one('[id="'+href[1:]+'"]') is not None,'ANCHOR_TARGET')
  for nav in dom.select('header nav'):must([a.get('href') for a in nav.find_all('a')]==spec['architecture']['mainMenuPaths'],'MAIN_MENU',path)
  if page.get('breadcrumbs'):
   crumb=dom.select_one('.breadcrumb');must(crumb is not None,'BREADCRUMB')
   must([a.get('href') for a in crumb.find_all('a')]==[b['href'] for b in page['breadcrumbs'] if b.get('href')],'BREADCRUMB_LINKS')
   must(len(crumb.select('[aria-current="page"]'))==1,'BREADCRUMB_CURRENT')
  for img in dom.find_all('img'):must(img.get('alt') and img.get('width') and img.get('height') and img.get('loading')=='lazy' and img.get('decoding')=='async' and img.get('src','').startswith('/') and (root/img['src'].lstrip('/')).is_file(),'IMAGE_ATTRIBUTES',path)
  banners=dom.select('[data-shared-flower-banner]');independent_images=[img for img in dom.find_all('img') if '/shared-banners/' in img.get('src','')]
  must(len(independent_images)==(3 if page.get('sourceFile') else 0),'BANNER_IMAGE_COUNT',path)
  must([b.get('data-shared-flower-banner') for b in banners]==(spec['sharedBannerBinding']['order'] if page.get('sourceFile') else []),'BANNER_SET',path)
  for b,expected_banner in zip(banners,spec['sharedBannerBinding']['assets']):
   img=b.find('img');must(b.name=='figure' and not b.find('figcaption') and len(b.find_all('img'))==1 and img in independent_images,'BANNER_WRAPPER')
   must(img.get('src')==expected_banner['renderSrc'] and img.get('alt')==expected_banner['alt'] and img['alt'].count('1844-0644')==1,'BANNER_ALT_SRC')
   must(img.get('width')=='1774' and img.get('height')=='887','BANNER_DIMENSIONS')
   must(sha((root/img['src'].lstrip('/')).read_bytes())==expected_banner['sha256'],'BANNER_BYTES')
   nxt=b.find_next_sibling();must(nxt is not None and nxt.name=='section' and nxt.find('h2').get_text()==page['bannersBeforeH2'][expected_banner['variant']],'BANNER_PLACEMENT')
   static_visible(img,dom,css,'BANNER_VISIBLE_STATIC')
  cards=dom.select('[data-product-sku]');must(len(cards)==page['productCardCount'],'PRODUCT_COUNT',path)
  product_images=[img for img in dom.find_all('img') if '/images/products/' in img.get('src','')];must(len(product_images)==page['productCardCount'],'PRODUCT_IMAGE_COUNT',path)
  for card,p in zip(cards,products):
   must(card.get('data-product-sku')==p['sku'] and card.find('h3').get_text()==p['name']+' '+p['sku'] and card.find('p').get_text()==p['priceLabel'],'PRODUCT_COPY')
   img=card.find('img');must(sha((root/img['src'].lstrip('/')).read_bytes())==p['photoSHA256'],'PRODUCT_IMAGE_BYTES')
   link=card.select_one('[data-order-product-sku]');must(link and link.get('href')==p['ctaHref'] and link.get_text()==p['ctaLabel'],'PRODUCT_CTA')
   static_visible(link,dom,css,'PRODUCT_CTA_VISIBLE')
  required=article.select('[data-required-cta]')
  for cta in required:static_visible(cta,dom,css,'REQUIRED_CTA_VISIBLE')
  expected_ctas=[(c.get('href',c.get('renderHref')),c['label']) for c in page.get('ctas',[])]
  if page['id']=='article':expected_ctas=[(p['ctaHref'],p['ctaLabel']) for p in products]+expected_ctas
  if page['id']=='support':expected_ctas=[(page['cta']['href'],page['cta']['label'])]
  if page['id']=='not-found':expected_ctas=[('/',copy['ctaLabel'])]
  must([(a['href'],a.get_text()) for a in required]==expected_ctas,'REQUIRED_CTA_SET',path)
  faqs=dom.select('[data-faq-question]');answers=dom.select('[data-faq-answer]');must(len(faqs)==len(answers)==page['faqCount'],'FAQ_COUNT',path)
  for question,answer,expected_faq in zip(faqs,answers,spec['faqBinding']['items']):
   must(question.name=='h3' and question.get_text()==expected_faq['question'] and answer.name=='p' and sha(answer.get_text().encode())==expected_faq['answerUTF8SHA256'],'FAQ_COPY')
   must(question.find_next_sibling() is answer,'FAQ_IMMEDIATE_ANSWER')
   must(surface.count(norm(question.get_text()))==surface.count(norm(answer.get_text()))==1,'FAQ_ONCE')
   static_visible(question,dom,css,'FAQ_VISIBLE_STATIC');static_visible(answer,dom,css,'FAQ_VISIBLE_STATIC')
  if page.get('sourceFile'):
   raw=(INPUT/page['sourceFile']).read_bytes();must(article.get('data-original-draft-sha')==sha(raw),'ORIGINAL_BYTE_BINDING')
   blocks,links,images=original_projection(raw.decode(),spec);render=dom.select_one('[data-reviewed-body]');must(render is not None,'REVIEWED_BODY')
   must([(n.name,norm(n.get_text())) for n in render.select('[data-reviewed-block]')]==blocks,'BODY_BLOCK_SEQUENCE',path)
   must(all(not isinstance(child,str) or not child.strip() or any(n.has_attr('data-reviewed-block') for n in [node,*node.parents]) for node in [render,*render.descendants()] for child in node.children),'BODY_TEXT_PARITY',path)
   must([(a.get('href'),a.get_text()) for a in render.find_all('a')]==links,'BODY_LINK_PARITY',path)
   must([(i['src'],i['alt']) for i in render.select('[data-reviewed-image]')]==images,'BODY_IMAGE_PARITY')
   must([h.get_text() for h in render.find_all('h2')]==page['h2Order'],'H2_ORDER')
   must(all(surface.count(value)==1 for tag,value in blocks if tag in ['p','li']),'PARAGRAPH_ONCE')
   must(len(dom.select('[data-first-answer]'))==1 and dom.select_one('[data-first-answer]').get_text()==next(v for t,v in blocks if t=='p'),'FIRST_ANSWER_ONCE')
   must(len(dom.select('[data-source-references]'))==1 and sum(h.get_text()=='출처 및 확인 정보' for h in dom.find_all('h2'))==1,'SOURCE_SECTION_ONCE')
  if page['id']=='support':
   card=dom.select('[data-content-card]');must(len(card)==1 and card[0].find('h2').get_text()==page['cardHeading'],'SUPPORT_ONE_CHILD')
   home_blocks,_,_=original_projection((INPUT/'drafts/home.ko.md').read_text(),spec);summary=next(v for t,v in home_blocks[home_blocks.index(('h2',page['cardHeading']))+1:] if t=='p');must(card[0].find('p').get_text()==summary,'SUPPORT_SUMMARY')
  if page['id']=='not-found':must(dom.select_one('#opening p').get_text()==copy['body'],'NOT_FOUND_BODY')
  for forbidden in ['목포','강동','유캐슬','예울마루','여천전남병원','무료배송','100% 환불','당일배송','AI 생성 이미지','원격 저장','Launch Gate']:must(forbidden not in surface,'UNAPPROVED_COPY',forbidden)
  results.append({'path':page['path'],'sha256':sha(text.encode()),'role':page['role'],'products':len(cards),'faqPairsInStaticHTML':len(faqs),'banners':len(banners),'requiredCTAs':len(required),'originalDraftSHA256':article.get('data-original-draft-sha'),'mainTabindex':'-1','robots':'noindex,follow','canonical':None})
 must(len(set(titles))==len(set(descriptions))==4,'UNIQUE_METADATA')
 return {'status':'PASS_PRIVATE_STATIC_ONLY','specSHA256':SPEC_SHA,'pages':results,'origin':None,'productionEnabled':False,'MokpoOrder26StillPending':True,'YeosuOrder27IndependentPreparationOnly':True,'limitations':['No browser/computed-layout verification','No loopback HTTP or unknown-path 404 response verification','No live product, telephone, checkout, delivery, public HTTP, deployment or indexing verification']}
if __name__=='__main__':
 try:result=check(Path(sys.argv[1]) if len(sys.argv)>1 else C/'dist');(C/'evidence/static-qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
