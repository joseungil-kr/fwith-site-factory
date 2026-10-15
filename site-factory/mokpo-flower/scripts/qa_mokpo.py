#!/usr/bin/env python3
"""Targeted private-preview checks. This does not replace Core/Production Launch Gates."""
from pathlib import Path
from html_surface import BeautifulSoup
import json,hashlib,re,sys,xml.etree.ElementTree as ET
from urllib.parse import urlsplit
C=Path(__file__).resolve().parents[1]
SPEC_SHA='90f43c2fb14ca8756453f1b2af1339f68e1ec24d3b38cb06f09a4cf73fd12f44'
BANNERS={
 'message':('a5ecdeb1914566a32d45b084351e2782fc8b234e9a4fbb8635a60a9921cac5f5','흰 장미와 잎을 배경으로 꽃으로 전하는 마음을 안내하는 꽃이랑 배너. 전화 1844-0644.'),
 'budget':('081198095eb005603721be7c778f4d477f4dd93dcf96f0c261f18bf06bb91421','겹겹의 흰 꽃을 배경으로 상품 사진과 가격 비교를 안내하는 꽃이랑 배너. 전화 1844-0644.'),
 'consultation':('d6654aa44c365f64e330d0be2042972d3320fad54231425aaffca1dfdcd25ebc','흰 꽃과 봉오리를 배경으로 상품 선택과 리본 문구 상담을 안내하는 꽃이랑 배너. 전화 1844-0644.')}
sha=lambda b:hashlib.sha256(b).hexdigest()
norm=lambda t:re.sub(r'\s+',' ',t).strip()
def htmlpath(path):return 'index.html' if path=='/' else '404.html' if path=='/404.html' else path.strip('/')+'/index.html'
class QAError(AssertionError):pass
def must(condition,code,detail=''):
 if not condition:raise QAError(f'{code}: {detail}')
def check(root=C/'dist',spec=None,page_map=None):
 root=Path(root);raw=(C/'src/data/frozen/content-spec.ko.json').read_bytes()
 must(sha(raw)==SPEC_SHA,'INPUT_HASH')
 spec=spec or json.loads(raw);page_map=page_map or json.loads((C/'src/data/page-map.json').read_text())
 expected={htmlpath(p['path']) for p in spec['pages']};actual={str(p.relative_to(root)) for p in root.rglob('*.html')}
 must(actual==expected and len(actual)==4,'HTML_DENOMINATOR',str(actual))
 must(page_map['origin'] is None and page_map['productionEnabled'] is False and page_map['mode']=='private-local-preview','BOUNDARY')
 must(page_map['coreHubLaunchStatus']=='NOT_ASSESSED' and page_map['fullLaunchStatus']=='NOT_ASSESSED','LAUNCH_SCOPE')
 for field,count in {'articleCount':1,'primaryCount':2,'supportCount':1,'contentHtmlCount':3,'technicalHtmlCount':1,'allHtmlCount':4,'previewIndexableCount':0,'previewSitemapUrlCount':0}.items():must(page_map[field]==count,'MAP_DENOMINATOR',field)
 must(page_map['productionProposal']['active'] is False and page_map['productionProposal']['origin'] is None,'PRODUCTION_DISABLED')
 must(page_map['productionProposal']['paths']==['/','/regions/hankook-hospital-funeral-wreath/'],'PROPOSAL_PATHS')
 must([p['path'] for p in page_map['pages']]==[p['path'] for p in spec['pages']],'MAP_PATHS')
 for p in page_map['pages']:
  must(p['robots']=='noindex,follow' and p['canonical'] is None and p['sitemapIncluded'] is False and p['coreHub'] is False,'MAP_BOUNDARY',p['path'])
 support=next(p for p in page_map['pages'] if p['role']=='support-navigation')
 must(support['actualChildCount']==1 and support['mainMenuIncluded'] is False and support['marketingBannerCount']==0,'SUPPORT_ROLE')
 must('Disallow:' not in (root/'robots.txt').read_text() and 'Allow: /' in (root/'robots.txt').read_text(),'ROBOTS_READABLE')
 must(len(ET.parse(root/'sitemap.xml').getroot())==0,'EMPTY_PREVIEW_SITEMAP')
 must('X-Robots-Tag: noindex, follow' in (root/'_headers').read_text(),'HEADERS_NOINDEX')
 results=[];titles=[];metas=[]
 for page in spec['pages']:
  path=htmlpath(page['path']);text=(root/path).read_text();dom=BeautifulSoup(text);article=dom.select_one('[data-page-id]');visible=norm(dom.find('body').get_text(' ',strip=True))
  must(article is not None and article.get('data-page-id')==page['id'] and article.get('data-page-role')==page['role'] and article.get('data-copy-sha')==SPEC_SHA,'HTML_BINDING',path)
  title=dom.find('title').get_text();meta=dom.select_one('meta[name="description"]').get('content');titles.append(title);metas.append(meta)
  must(title==page['content']['title'] and meta==page['content']['metaDescription'],'METADATA',path)
  must([n.get_text() for n in dom.find_all('h1')]==[page['content']['h1']],'H1',path)
  must(len(dom.select('[data-first-answer]'))==1 and dom.select_one('[data-first-answer]').get_text()==page['content']['firstAnswer'],'FIRST_ANSWER',path)
  must(norm(dom.find('body').get_text(' ',strip=True)).count(norm(page['content']['firstAnswer']))==1,'FIRST_ANSWER_ONCE',path)
  must(dom.select_one('meta[name="robots"]').get('content')=='noindex,follow','ROBOTS_META',path)
  must(not dom.select('link[rel="canonical"]') and not dom.select('meta[property="og:url"]'),'NO_CANONICAL_ORIGIN',path)
  must(not dom.find_all('script') and not dom.find_all('form') and not dom.find_all('iframe'),'NO_ACTIVE_TRANSMISSION',path)
  previous=0
  for h in dom.find_all(['h1','h2','h3','h4','h5','h6']):
   level=int(h.name[1]);must(level<=previous+1 if previous else level==1,'HEADING_ORDER',h.get_text());previous=level
  for a in dom.find_all('a'):
   href=a.get('href','');must(bool(href) and href!='#' and not href.startswith(('javascript:','data:','//')),'LINK_SAFETY',href)
   if href.startswith('/'):
    target=urlsplit(href);must((root/htmlpath(target.path)).exists() or (root/target.path.lstrip('/')).exists(),'INTERNAL_LINK',href)
   if href.startswith('#'):must(dom.select_one('[id="'+href[1:]+'"]') is not None,'ANCHOR',href)
  for nav in dom.select('header nav'):
   must('/regions/' not in [a.get('href') for a in nav.find_all('a')],'SUPPORT_MENU',path)
  if page['breadcrumbVisible']:
   crumb=dom.select_one('.breadcrumb');must(crumb is not None,'BREADCRUMB',path)
   must([a.get('href') for a in crumb.find_all('a')]==[b['href'] for b in page['breadcrumbs'] if b['href']],'BREADCRUMB_LINKS',path)
  for img in dom.find_all('img'):
   must(bool(img.get('alt')) and img.get('width') and img.get('height'),'IMAGE_ALT_DIMENSIONS',path)
   must(img.get('src','').startswith('/') and (root/img['src'].lstrip('/')).is_file(),'LOCAL_IMAGE',path)
   must(not any(x in img['alt'] for x in ['AI 생성 이미지','실제 판매상품 사진이 아닌','공통 안내 이미지']),'REMOVED_CAPTION_ALT')
  banners=dom.select('[data-shared-flower-banner]')
  independent_banner_images=[img for img in dom.find_all('img') if '/shared-banners/' in img.get('src','')]
  must(len(independent_banner_images)==(3 if page['sourceDraft'] else 0),'BANNER_IMAGE_COUNT',path)
  must(all(img.parent in banners for img in independent_banner_images),'BANNER_WRAPPERS',path)
  must([b.get('data-shared-flower-banner') for b in banners]==(['message','budget','consultation'] if page['sourceDraft'] else []),'BANNER_SET',path)
  for b in banners:
   key=b.get('data-shared-flower-banner');img=b.find('img');digest,alt=BANNERS[key];asset=root/'images/shared-banners'/('flower-'+key+'.webp')
   must(img.get('src')==f'/images/shared-banners/flower-{key}.webp','BANNER_SRC',path)
   must(img.get('alt')==alt and img['alt'].count('1844-0644')==1,'BANNER_ALT',path)
   must(img.get('width')=='1774' and img.get('height')=='887' and img.get('loading')=='lazy' and img.get('decoding')=='async','BANNER_ATTRIBUTES',path)
   must(sha(asset.read_bytes())==digest,'BANNER_BYTES',str(asset))
   must(b.name=='figure' and not b.find('figcaption'),'BANNER_CAPTION',path)
  for left,right in zip(banners,banners[1:]):
   n=left.find_next_sibling();substantial=False
   while n is not None and n is not right:
    if n.name=='section' and n.find('p') and len(n.get_text())>60:substantial=True
    n=n.find_next_sibling()
   must(substantial,'BANNER_SPACING',path)
  cards=dom.select('[data-product-sku]')
  independent_product_images=[img for img in dom.find_all('img') if '/images/products/' in img.get('src','')]
  must(len(independent_product_images)==len(page['productCardIds']),'PRODUCT_IMAGE_COUNT',path)
  must([c.get('data-product-sku') for c in cards]==page['productCardIds'],'PRODUCT_SET',path)
  for c,p in zip(cards,spec['productCards']):
   must(c.find('h3').get_text()==p['name'] and c.find('strong').get_text()==p['priceText'],'PRODUCT_COPY',p['sku'])
   must(c.find('img').get('alt')==p['alt'] and sha((root/c.find('img')['src'].lstrip('/')).read_bytes())==p['photoSHA256'],'PRODUCT_IMAGE',p['sku'])
   cta=c.select_one('[data-order-product-sku]');must(cta.get('href')==p['cta']['href']==f"https://fwith.co.kr/shop/item.php?it_id={p['sku']}" and cta.get('aria-label')==p['cta']['accessibleLabel'],'PRODUCT_CTA',p['sku'])
   must(norm(p['description']) in norm(c.get_text()),'PRODUCT_DESCRIPTION',p['sku'])
  faq=dom.select('[data-faq-entry]')
  must(len(faq)==len(page['faqIds']),'FAQ_COUNT',path)
  for f,data in zip(faq,spec['faqs']):
   must(f.select_one('[data-faq-question]').get_text()==data['question'] and f.select_one('[data-faq-answer]').get_text()==data['answer'],'FAQ_COPY',data['id'])
   must(norm(dom.find('body').get_text(' ',strip=True)).count(norm(data['question']))==1 and norm(dom.find('body').get_text(' ',strip=True)).count(norm(data['answer']))==1,'FAQ_ONCE',data['id'])
   for n in [f,*f.parents]:must(not n.has_attr('hidden') and n.get('aria-hidden')!='true' and n.name not in ['details','template'] and not re.search(r'display\s*:\s*none|visibility\s*:\s*hidden',n.get('style','')),'FAQ_VISIBLE',path)
  if page['sourceDraft']:
   draft=page['sourceDraft'];must(sha(draft['fullDocumentMarkdown'].encode())==draft['sha256'],'DRAFT_EMBED_HASH',path)
   original=(C/'src/data/frozen'/('home.ko.md' if page['id']=='home' else 'condolence.ko.md')).read_bytes();must(sha(original)==draft['sha256'],'DRAFT_FILE_HASH',path)
   rendered=[norm(p.get_text()) for p in dom.select('[data-reviewed-paragraph]')]
   paragraphs=[norm(p) for p in draft['fullDocumentMarkdown'].strip().split('\n\n') if not p.startswith(('#','버튼:','목적지:')) and p!='목포한국병원 장례식장 근조화환 상담: 1844-0644']
   must(rendered==paragraphs,'DRAFT_PARAGRAPH_SEQUENCE',path)
   must(all(norm(dom.find('body').get_text(' ',strip=True)).count(paragraph)==1 for paragraph in paragraphs),'DRAFT_PARAGRAPH_ONCE',path)
   must(len(dom.select('[data-source-references]'))==1 and sum(h.get_text()=='출처 및 확인 정보' for h in dom.find_all('h2'))==1,'SOURCE_SECTION',path)
  if page['id']=='regions-support':must(len(dom.select('[data-content-card]'))==1 and dom.select_one('[data-content-card] a').get('href')==page['childPaths'][0],'ONE_REAL_CHILD')
  if page['id']=='home':must(any(a.get('href')=='/regions/hankook-hospital-funeral-wreath/' for a in article.find_all('a')),'HOME_DIRECT_ARTICLE')
  for phrase in ['19시','21시','주말','공휴일','무료배송','당일배송','100% 환불','AI 생성 이미지','공통 안내 이미지','원격 저장','Launch Gate']:
   must(phrase not in visible,'UNAPPROVED_COPY',phrase)
  results.append({'path':page['path'],'html':path,'sha256':sha(text.encode()),'role':page['role'],'banners':len(banners),'products':len(cards),'visibleFaqPairs':len(faq),'robots':'noindex,follow','canonical':None})
 must(len(set(titles))==4 and len(set(metas))==4,'UNIQUE_METADATA')
 return {'status':'PASS_PRIVATE_STATIC_ONLY','coreHubLaunchStatus':'NOT_ASSESSED','fullLaunchStatus':'NOT_ASSESSED','productionStatus':'NOT_ASSESSED','pages':results,'boundSpecSHA256':SPEC_SHA,'boundary':'Static output inspection; not browser visibility, provider routing, deployment, phone call or checkout verification.'}
if __name__=='__main__':
 try:
  result=check(Path(sys.argv[1]) if len(sys.argv)>1 else C/'dist');(C/'evidence/static-qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
