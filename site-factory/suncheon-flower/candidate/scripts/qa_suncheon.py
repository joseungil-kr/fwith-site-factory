#!/usr/bin/env python3
"""Separate JSON-to-HTML projection and static checks; not a browser or CSS cascade engine."""
from pathlib import Path
from html_surface import BeautifulSoup
import hashlib,json,re,sys,xml.etree.ElementTree as ET
from urllib.parse import urlsplit,unquote
C=Path(__file__).resolve().parents[1];B=C.parent;I=B/'inputs/reviewed-copy'
sha=lambda b:hashlib.sha256(b).hexdigest()
norm=lambda t:re.sub(r'\s+',' ',t).strip()
class QAError(AssertionError):pass
def must(v,code,detail=''):
 if not v:raise QAError(f'{code}: {detail}')
def htmlpath(path):return 'index.html' if path=='/' else '404.html' if path=='/404.html' else path.strip('/')+'/index.html'
def load(name):return json.loads((I/name).read_text())
ARTICLE='/regions/suncheon-stcarollo-funeral-wreath/'
def map_href(href):
 return {'suncheon-stcarollo-funeral.ko.md':ARTICLE,'suncheon-stcarollo-funeral.ko.md#출처-및-확인-정보':ARTICLE+'#sources'}[href]
def projection(id,home,detail,products):
 blocks=[];links=[]
 def a(text,href,required=False):blocks.append(('a',text));links.append((href,text));return (href,text) if required else None
 c=home if id=='home' else detail
 blocks.append(('h1',c['h1']));blocks.extend(('p',t) for t in ([c['lead']] if isinstance(c['lead'],str) else c['lead']))
 for s in c['sections']:
  blocks.append(('h2',s['h2']));blocks.extend(('p',t) for t in ([s['text']] if id=='home' else s['paragraphs']))
  if id=='home' and s.get('card'):
   card=s['card'];blocks.extend([('h3',card['title']),('p',card['summary'])]);a(card['ctaLabel'],map_href(card['localHref']))
  if id=='article' and s['id']=='products':
   for p in products:blocks.extend([('h3',p['name']+' '+p['sku']),('p',p['priceLabel'])]);a(p['ctaLabel'],p['ctaHref'])
  blocks.extend(('li',t) for t in s.get('list',[]));blocks.extend(('p',t) for t in s.get('afterList',[]))
 if id=='article':
  blocks.append(('h2',detail['faqHeading']))
  for f in detail['faq']:blocks.extend([('h3',f['question']),('p',f['answer'])])
  blocks.append(('p',detail['closing']))
 a(c['cta']['label'],c['cta']['href']);blocks.append(('h2',c['sourceHeading']));blocks.append(('p',c['sourcesText'] if id=='home' else c['sourceIntro']))
 if id=='home':a(home['sourceLink']['label'],map_href(home['sourceLink']['localHref']))
 else:
  for src in detail['sources']:a(src['label'],src['url'])
 return blocks,links
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
 root=Path(root)
 manifest=(B/'inputs/required-originals.json').read_bytes();must(sha(manifest)=='b4eb7bda5f666334286172fc1f8e95dbf72f7877b58a972813819d058d68add0','INPUT_MANIFEST_HASH')
 for row in json.loads(manifest):
  data=(B/row['path']).read_bytes();must(len(data)==row['bytes'] and sha(data)==row['sha256'],'REQUIRED_INPUT_HASH',row['path'])
 home=load('home-copy.json');detail=load('detail-copy.json');products=load('product-cards.json');plan=load('render-plan.json');meta=load('customer-copy-metadata.json');ui=json.loads((C/'src/data/ui-copy.json').read_text())
 scoped=(B/'inputs/ui-copy-review.json').read_bytes();must(sha(scoped)=='3c033aa31df1793247324d4b31e58b7276659936fbb65f8529e0ea25f9fa3339','UI_REVIEW_HASH');must(json.loads(scoped)['uiCopySHA256']==sha((C/'src/data/ui-copy.json').read_bytes()),'UI_COPY_HASH')
 pm=page_map or json.loads((C/'src/data/page-map.json').read_text())
 for k,v in {'mode':'private-local-preview','origin':None,'domain':None,'canonical':None,'productionEnabled':False,'coreHubLaunchStatus':'NOT_ASSESSED','fullLaunchStatus':'NOT_ASSESSED','articleCount':1,'primaryCount':2,'supportCount':1,'contentHtmlCount':3,'technicalHtmlCount':1,'allHtmlCount':4,'previewIndexableCount':0,'previewSitemapUrlCount':0}.items():must(pm[k]==v,'BOUNDARY',k)
 must(pm['launchOrder']=={'Mokpo':26,'Yeosu':27,'Suncheon':28,'MokpoStillPending':True,'YeosuStillPending':True,'SuncheonIndependentPreparationOnly':True},'ORDER_UNCHANGED')
 expected=[('home','/','primary-home'),('article',ARTICLE,'primary-article'),('support','/regions/','support-navigation'),('not-found','/404.html','technical-404')]
 must([(p['id'],p['path'],p['role']) for p in pm['pages']]==expected,'MAP_PATHS')
 must({str(p.relative_to(root)) for p in root.rglob('*.html')}=={htmlpath(p[1]) for p in expected},'HTML_DENOMINATOR')
 must((root/'robots.txt').read_text()=='User-agent: *\nAllow: /\n','ROBOTS_READABLE')
 must({str(p.relative_to(root)) for p in root.rglob('*.xml')}=={'sitemap.xml'} and len(ET.parse(root/'sitemap.xml').getroot())==0,'EMPTY_PREVIEW_SITEMAP')
 must((root/'_headers').read_text()=='/*\n  X-Robots-Tag: noindex, follow\n','HEADERS_NOINDEX')
 must(not any((root/n).exists() for n in ['_worker.js','_redirects','_routes.json']),'NO_ROUTING_ADAPTER')
 results=[];titles=[];descs=[]
 for id,path,role in expected:
  p=next(p for p in pm['pages'] if p['id']==id);primary=id in ['home','article'];text=(root/htmlpath(path)).read_text();dom=BeautifulSoup(text);body=dom.find('body');surface=norm(body.get_text());article=dom.select_one('[data-page-id]')
  must(article and article.get('data-page-id')==id and article.get('data-page-role')==role,'HTML_BINDING')
  must(p['robots']=='noindex,follow' and p['canonical'] is None and not p['sitemapIncluded'] and not p['coreHub'] and p['marketingBannerCount']==(3 if primary else 0) and p['mainMenuIncluded']==primary and p['actualChildCount']==(1 if id=='support' else 0),'MAP_BOUNDARY')
  c=home if id=='home' else detail if id=='article' else ui['support' if id=='support' else 'notFound'];m=meta['home' if id=='home' else 'detail'] if primary else c
  must([h.get_text() for h in dom.find_all('h1')]==[c['h1']],'H1')
  title=dom.find('title').get_text();desc=dom.select_one('meta[name="description"]')['content'];titles.append(title);descs.append(desc);must(title==m['title'] and desc==m['description'],'METADATA')
  must([x.get('content') for x in dom.select('meta[name="robots"]')]==['noindex,follow'],'ROBOTS_META')
  must(not dom.select('link[rel="canonical"]') and not dom.select('meta[property="og:url"]') and not dom.select('meta[property="og:image"]'),'NO_ABSOLUTE_METADATA')
  must(not dom.find_all('script') and not dom.find_all('form') and not dom.find_all('iframe'),'NO_ACTIVE_TRANSMISSION')
  must(len(dom.find_all('main'))==1 and dom.find('main').get('id')=='main-content' and dom.find('main').get('tabindex')=='-1','MAIN_FOCUS_TARGET');must(dom.select_one('.skip-link').get('href')=='#main-content','SKIP_LINK')
  ids=[n.get('id') for n in dom.select('[id]')];must(len(ids)==len(set(ids)),'DUPLICATE_ID')
  css='\n'.join((root/x['href'].lstrip('/')).read_text() for x in dom.select('link[rel="stylesheet"]'))+'\n'+'\n'.join(x.get_text() for x in dom.find_all('style'))
  level=0
  for h in dom.find_all(['h1','h2','h3','h4','h5','h6']):n=int(h.name[1]);must(n<=level+1 if level else n==1,'HEADING_ORDER');level=n
  for a in dom.find_all('a'):
   href=a.get('href','');must(href and href!='#' and not href.startswith(('javascript:','data:','//')),'LINK_SAFETY')
   parsed=urlsplit(href)
   if href.startswith('/') or href.startswith('#'):
    target=htmlpath(parsed.path or path);must((root/target).is_file() or (root/parsed.path.lstrip('/')).is_file(),'INTERNAL_LINK',href)
    if parsed.fragment:targetdom=dom if not parsed.path else BeautifulSoup((root/target).read_text());must(any(x.get('id')==unquote(parsed.fragment) for x in targetdom.select('[id]')),'ANCHOR_TARGET',href)
   elif href.startswith('tel:'):must(href=='tel:18440644','ONLY_SALES_PHONE_CTA')
   else:must(href.startswith('https://'),'LINK_SAFETY')
  for nav in dom.select('header nav'):must([a.get('href') for a in nav.find_all('a')]==['/',ARTICLE],'MAIN_MENU')
  for img in dom.find_all('img'):must(img.get('alt') and img.get('width') and img.get('height') and img.get('loading')=='lazy' and img.get('decoding')=='async' and img.get('src','').startswith('/') and (root/img['src'].lstrip('/')).is_file(),'IMAGE_ATTRIBUTES')
  banners=dom.select('[data-shared-flower-banner]');must([b.get('data-shared-flower-banner') for b in banners]==(['message','budget','consultation'] if primary else []),'BANNER_SET')
  must(len([im for im in dom.find_all('img') if '/shared-banners/' in im.get('src','')])==(3 if primary else 0),'BANNER_IMAGE_COUNT')
  next_ids=['section-1','section-2',None] if id=='home' else ['ribbon','facility',None]
  for i,(b,e) in enumerate(zip(banners,plan['commonBanners'])):
   img=b.find('img');must(b.name=='figure' and not b.find('figcaption') and len(b.find_all('img'))==1,'BANNER_WRAPPER');must(img.get('src')=='/images/shared-banners/'+e['assetName'] and img.get('alt')==e['alt'] and img['alt'].count('1844-0644')==1,'BANNER_ALT_SRC');must(img['width']=='1774' and img['height']=='887','BANNER_DIMENSIONS');must(sha((root/img['src'].lstrip('/')).read_bytes())==e['sha256'],'BANNER_BYTES')
   nxt=b.find_next_sibling();must(nxt is not None and (nxt.get('id')==next_ids[i] if i<2 else ('final-action' in nxt.get('class','') if id=='home' else 'directory-closing' in nxt.get('class',''))),'BANNER_PLACEMENT');static_visible(img,dom,css,'BANNER_VISIBLE_STATIC')
  cards=dom.select('[data-product-sku]');must(len(cards)==(4 if id=='article' else 0),'PRODUCT_COUNT');must(len([im for im in dom.find_all('img') if '/images/products/' in im.get('src','')])==len(cards),'PRODUCT_IMAGE_COUNT')
  for card,e in zip(cards,products):
   must(card.get('data-product-sku')==e['sku'] and card.find('h3').get_text()==e['name']+' '+e['sku'] and card.find('p').get_text()==e['priceLabel'],'PRODUCT_COPY');img=card.find('img');must(img.get('alt')==e['photoAlt'] and img.get('width')=='500' and img.get('height')=='500','PRODUCT_IMAGE_ATTRIBUTES');must(sha((root/img['src'].lstrip('/')).read_bytes())==e['photoSHA256'],'PRODUCT_IMAGE_BYTES');a=card.select_one('[data-order-product-sku]');must(a and a.get('href')==e['ctaHref'] and a.get_text()==e['ctaLabel'],'PRODUCT_CTA');static_visible(a,dom,css,'PRODUCT_CTA_VISIBLE')
  required=article.select('[data-required-cta]')
  for a in required:static_visible(a,dom,css,'REQUIRED_CTA_VISIBLE')
  card=home['sections'][0]['card'];expected_ctas=([(map_href(card['localHref']),card['ctaLabel']),(home['cta']['href'],home['cta']['label'])] if id=='home' else [(p['ctaHref'],p['ctaLabel']) for p in products]+[(detail['cta']['href'],detail['cta']['label'])] if id=='article' else [(map_href(card['localHref']),card['ctaLabel'])] if id=='support' else [('/',ui['notFound']['ctaLabel'])])
  must([(a['href'],a.get_text()) for a in required]==expected_ctas,'REQUIRED_CTA_SET')
  qs=dom.select('[data-faq-question]');ans=dom.select('[data-faq-answer]');must(len(qs)==len(ans)==(3 if id=='article' else 0),'FAQ_COUNT')
  for q,a,e in zip(qs,ans,detail['faq']):
   must(q.name=='h3' and q.get_text()==e['question'] and a.name=='p' and a.get_text()==e['answer'],'FAQ_COPY');must(q.find_next_sibling() is a,'FAQ_IMMEDIATE_ANSWER');must(surface.count(norm(q.get_text()))==surface.count(norm(a.get_text()))==1,'FAQ_ONCE');static_visible(q,dom,css,'FAQ_VISIBLE_STATIC');static_visible(a,dom,css,'FAQ_VISIBLE_STATIC')
  if primary:
   source='home-copy.json' if id=='home' else 'detail-copy.json';must(article.get('data-copy-sha')==sha((I/source).read_bytes()),'JSON_BYTE_BINDING');render=dom.select_one('[data-reviewed-body]');must(render is not None,'REVIEWED_BODY');blocks,links=projection(id,home,detail,products);must([(n.name,norm(n.get_text())) for n in render.select('[data-reviewed-block]')]==[(t,norm(v)) for t,v in blocks],'BODY_BLOCK_SEQUENCE');must([(a.get('href'),a.get_text()) for a in render.find_all('a')]==links,'BODY_LINK_PARITY')
   must(all(not isinstance(child,str) or not child.strip() or any(n.has_attr('data-reviewed-block') for n in [node,*node.parents]) for node in [render,*render.descendants()] for child in node.children),'BODY_TEXT_PARITY')
   must(all(surface.count(norm(v))==1 for t,v in blocks if t in ['p','li']),'PARAGRAPH_ONCE');must(len(dom.select('[data-first-answer]'))==1 and dom.select_one('[data-first-answer]').get_text()==(c['lead'] if id=='home' else c['lead'][0]),'FIRST_ANSWER_ONCE');must(len(dom.select('[data-source-references]'))==1 and sum(h.get_text()==c['sourceHeading'] for h in dom.find_all('h2'))==1,'SOURCE_SECTION_ONCE')
  if id=='support':
   cs=dom.select('[data-content-card]');must(len(cs)==1 and cs[0].find('h2').get_text()==card['title'] and cs[0].find('p').get_text()==card['summary'],'SUPPORT_ONE_CHILD')
  if id=='not-found':must(dom.select_one('#opening p').get_text()==ui['notFound']['body'],'NOT_FOUND_BODY')
  # All rendered body text, including neutral chrome/support/404, has an approved source.
  chrome_start=[ui['skipLink'],'✿',ui['brand'],home['h1'],detail['h1'],ui['menuOpen'],ui['menuClose'],home['h1'],detail['h1']]
  main_text=[v for t,v in projection(id,home,detail,products)[0]] if primary else [ui['support']['h1'],card['title'],card['summary'],card['ctaLabel']] if id=='support' else [ui['notFound']['h1'],ui['notFound']['body'],ui['notFound']['ctaLabel']]
  chrome_end=[ui['brand'],ui['phoneLink'],ui['homeLink'],ui['homeLink'],ui['phoneLink']]
  must(norm(body.get_text(' ',True))==norm(' '.join(chrome_start+main_text+chrome_end)),'ALL_BODY_TEXT_PARITY')
  static_visible(dom.find('main'),dom,css,'MAIN_VISIBLE_STATIC')
  for forbidden in ['목포','여수','강동','순천향','무료배송','100% 환불','당일배송','AI 생성 이미지','원격 저장','Launch Gate']:must(forbidden not in surface,'UNAPPROVED_COPY',forbidden)
  results.append({'id':id,'path':path,'sha256':sha(text.encode()),'products':len(cards),'faqPairsInStaticHTML':len(qs),'banners':len(banners),'requiredCTAs':len(required),'robots':'noindex,follow','canonical':None,'mainTabindex':'-1'})
 must(len(set(titles))==len(set(descs))==4,'UNIQUE_METADATA')
 return {'status':'PASS_PRIVATE_STATIC_ONLY','renderSource':'REVIEWED_JSON_ONLY','pages':results,'origin':None,'productionEnabled':False,'launchOrder':pm['launchOrder'],'limitations':['Static HTML and straightforward hiding-style checks only; not browser/computed CSS/mobile verification','No HTTP404, public HTTP, telephone, checkout, deployment or indexing checks']}
if __name__=='__main__':
 try:
  result=check(Path(sys.argv[1]) if len(sys.argv)>1 else C/'dist');(C/'evidence/static-qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
