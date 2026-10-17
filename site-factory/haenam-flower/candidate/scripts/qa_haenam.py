"""Static output verification, not browser visibility or public HTTP evidence."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,sys
from urllib.parse import urlsplit
from html_surface import BeautifulSoup,Node
ROOT=Path(__file__).resolve().parents[1]
COPY=json.loads((ROOT.parent/'inputs/author/customer-copy.json').read_text())
D=json.loads((ROOT.parent/'inputs/author/display-copy.json').read_text());U=D['siteUI']
FAQ=[dict(f,id=f'question-{i+1}')for i,f in enumerate(COPY['faq'])]

def norm(s):return re.sub(r'\s+',' ',s).strip()
def blocks(text):
 result=[];p=[];li=[]
 def flush():
  if p:result.append(('p','\n'.join(p)));p.clear()
  if li:result.append(('ul',li.copy()));li.clear()
 for line in text.splitlines():
  if not line.strip():flush()
  elif line.startswith('- '):
   if p:result.append(('p','\n'.join(p)));p.clear()
   li.append(line[2:])
  else:
   if li:result.append(('ul',li.copy()));li.clear()
   p.append(line)
 flush();return result

def expected(route):
 rows=[]
 def add(key,text,tag=None,href=None):rows.append(dict(key=key,text=text,tag=tag,href=href))
 def parsed(prefix,text):
  for i,(tag,val)in enumerate(blocks(text)):
   if tag=='p':add(f'{prefix}.{i}',val,'p')
   else:
    for j,t in enumerate(val):add(f'{prefix}.{i}.{j}',t,'li')
 add('ui.skipLabel',U['skipLabel'],'a',U['skipHref']);add('ui.brandLabel',U['brandLabel'],'b');add('ui.regionLabel',U['regionLabel'],'small')
 for i,a in enumerate(U['navigation']):add(f'ui.navigation.{i}',a['label'],'a',('/'if route!='/' else '')+a['href'])
 if route=='/':
  add('page.h1',D['page']['h1'],'h1')
  for i,p in enumerate(COPY['intro'].split('\n\n')):add(f'intro.{i}',p,'p')
  for i,a in enumerate(U['heroActions']):add(f'ui.heroActions.{i}',a['label'],'a',a['href'])
  for s in COPY['sections']:
   add(f'section.{s["id"]}.heading',s['heading'],'h2')
   if s['id']=='questions':
    for f in FAQ:add(f['id']+'.question',f['question'],'h3');parsed(f['id']+'.answer',f['answer'])
   else:parsed(f'section.{s["id"]}.body',s['markdown'])
   if s['id']=='products-cost':
    for p in D['products']:
     for f in ['heading','priceLabel','shippingLabel','description','ctaLabel']:add(f'product.{p["sku"]}.{f}',p[f],'h3'if f=='heading'else'a'if f=='ctaLabel'else'p',p['ctaHref']if f=='ctaLabel'else None)
    add('ui.productNotice',U['productNotice'],'p');add('ui.amountNotice',U['amountNotice'],'p')
   if s['id']=='ribbon-order':
    add('ui.inlineOrderHeading',U['inlineOrderHeading'],'h3');add('ui.inlineOrderText',U['inlineOrderText'],'p');add('ui.inlineOrderAction',U['inlineOrderAction']['label'],'a',U['inlineOrderAction']['href'])
  add('sources.heading',D['sourceArea']['heading'],'h2');add('sources.checkedLabel',D['sourceArea']['checkedLabel'],'p')
  for i,a in enumerate(D['sourceArea']['items']):add(f'sources.{i}',a['label'],'a',a['href'])
  add('ui.closingAction',U['closingAction']['label'],'a',U['closingAction']['href'])
 else:
  for k in ['h1','body','ctaLabel']:add('404.'+k,D['notFoundCopyPlan'][k],{'h1':'h1','body':'p','ctaLabel':'a'}[k],D['notFoundCopyPlan']['ctaHref']if k=='ctaLabel'else None)
 add('ui.footerBrand',U['footerBrand'],'strong')
 for i,a in enumerate(U['footerLinks']):add(f'ui.footerLinks.{i}',a['label'],'a',('/'if route!='/'and a['href'].startswith('#')else'')+a['href'])
 add('ui.copyright',U['copyright'],'small')
 return rows

def verify(dist=ROOT/'dist'):
 dist=Path(dist);checks=[];docs={}
 def check(ok,label):
  if not ok:raise AssertionError(label)
  checks.append(label)
 files={p.relative_to(dist).as_posix():p.read_bytes()for p in sorted(dist.rglob('*'))if p.is_file()}
 css=[p for p in files if p.startswith('_astro/')and p.endswith('.css')]
 assets=json.loads((ROOT/'asset-render-binding.json').read_text())['assets']
 expected_paths={'index.html','404.html','robots.txt',*[a['renderSrc'][1:]for a in assets],*css}
 check(len(css)==1 and set(files)==expected_paths and len(files)==11,'exact eleven preview output files; no sitemap, key, headers or extra route')
 check(files['robots.txt']==b'User-agent: *\nDisallow: /\n','robots blocks all preview routes')
 for route,name in [('/','index.html'),('/404.html','404.html')]:
  raw=files[name].decode();doc=BeautifulSoup(raw);docs[route]=doc;head=doc.find('head');body=doc.find('body');rows=expected(route)
  nodes=doc.select('[data-copy-key]')
  check([n.get('data-copy-key')for n in nodes]==[r['key']for r in rows],route+' complete ordered copy-key inventory')
  for n,r in zip(nodes,rows):
   check(n.get_text()==r['text']and n.name==r['tag'],route+' exact text/tag '+r['key'])
   if r['href']is not None:check(n.get('href')==r['href'],route+' href '+r['key'])
  check(norm(body.get_text(' ',strip=True))==norm(' '.join(r['text']for r in rows)),route+' entire body has no extra, missing or duplicate customer text')
  ids=[n.get('id')for n in doc.select('[id]')];check(len(ids)==len(set(ids)),route+' unique IDs')
  check(len(doc.find_all('h1'))==1,route+' exactly one H1')
  check(len(doc.find_all('main'))==1,route+' exactly one main landmark')
  mainrows=[r for r in rows if not r['key'].startswith('ui.navigation.') and r['key'] not in ['ui.skipLabel','ui.brandLabel','ui.regionLabel','ui.footerBrand','ui.copyright'] and not r['key'].startswith('ui.footerLinks.')]
  check(norm(doc.find('main').get_text(' ',strip=True))==norm(' '.join(r['text']for r in mainrows)),route+' entire main exact accepted copy')
  check(doc.select_one('[data-page-id]').get('data-source-manuscript-sha')==COPY['sourceSHA256']['draft-home.ko.md'],route+' exact reviewed manuscript SHA attribute')
  check(all(x not in raw for x in ['고흥','구례','보성','화순','장흥','강진','마량','20,000원','배송비 0원','합산 참고금액']),route+' no prior-region text or incorrect shipping amount')
  check([(n.name,n.get_text())for n in doc.find_all(['h1','h2','h3'])]==[(r['tag'],r['text'])for r in rows if r['tag']in ['h1','h2','h3']],route+' exact H1/H2/H3 order')
  check(not doc.find_all(['h4','h5','h6','script','iframe','form','details','summary']),route+' no extra headings, scripts, form or folded content')
  check(not any(n.has_attr('hidden') or n.get('aria-hidden')=='true' or n.has_attr('inert') or n.get('style') for n in doc.descendants()),route+' no inline hiding or unreviewed styles')
  check(not any(n.find_all(['section','figure','div','ul','p','h1','h2','h3'])for n in doc.find_all('p')),route+' no block nested inside paragraph')
  page=D['page']if route=='/'else D['notFoundCopyPlan'];desc=page['description']if route=='/'else page['body']
  check(len(doc.find_all('title'))==1 and doc.title.get_text()==page['title'],route+' exact title')
  for key,value in [('description',desc),('robots','noindex,nofollow'),('viewport','width=device-width,initial-scale=1')]:
   n=[x for x in head.find_all('meta')if x.get('name')==key];check(len(n)==1 and n[0].get('content')==value,route+' exact '+key)
  check(not [n for n in head.find_all('link')if n.get('rel')=='canonical'],route+' no unapproved canonical')
  check(not[n for n in head.find_all('meta')if n.get('property','').startswith('og:')or n.get('name','').startswith('twitter:')],route+' no unapproved production social metadata')
  check('https://haenam.fwith.kr'not in raw,route+' no production host claim')
  check(doc.find('html').get('lang')=='ko'and doc.find('main').get('id')=='main-content'and doc.find('main').get('tabindex')=='-1',route+' Korean language and keyboard main target')
  check(doc.find('nav').get('aria-label')==U['navAriaLabel'],route+' exact navigation accessible label')
  check(doc.select_one('a.brand').get('href')==U['brandHref'],route+' brand target')
  check(len(doc.find_all('a'))==sum(r['tag']=='a'for r in rows)+1+(4 if route=='/'else 0),route+' exact link count')
  for link in doc.find_all('link'):
   if link.get('rel')=='stylesheet':check(link.get('href','').lstrip('/')in files,route+' stylesheet exists')
  if route=='/':
   check(len(doc.select('[data-product-sku]'))==4 and len(doc.select('.faq-pair'))==4 and len(doc.find_all('img'))==7,'four actual product cards, four expanded FAQs, seven images')
   check(doc.select_one('[data-purchase-cards]').get('aria-label')==U['productGroupAriaLabel'],'exact product-group accessible label')
   check(doc.select_one('[data-copy-key="ui.closingAction"]').get('aria-label')==U['closingAction']['ariaLabel'],'exact closing accessible label')
   check(D['region']['code']=='12790'and D['region']['order']==44 and D['facilityPages']=='HOLD_6' and D['historicalFacilityCandidate']=='HOLD_1_SEPARATE_NOT_MERGED','official Haenam identity and facility HOLD')
   for f in FAQ:
    n=doc.select_one('#'+f['id']);answer=' '.join(norm(x.get_text()) for x in n.find_all(['p','li']));check(answer==norm(f['answer'])and not n.find_all(['details','summary']),f['id']+' complete expanded answer')
   check('제작 완료된 꽃 상품은 교환·환불이 불가하다는 내용과,'in raw and '출고 후 취소 시 배송비를 제외한 금액을 환불한다는 내용이 함께 있습니다.'in raw,'both qualified refund clauses retained in actual HTML')
   for p in D['products']:
    card=doc.select_one('#product-'+p['sku']);im=card.find('img');check(im.get('src')==f'/images/products/{p["sku"]}.jpg'and im.get('alt')==p['photoAlt'],'exact photo and alt '+p['sku'])
    check(p['referenceSumKRW']is None and p['postedHaenamCountyRowKRW']==10000 and p['postedHaenamSpecificTownRowsKRW']=={'문내면':15000,'송지면':15000} and p['sumLabel']is None and p['shippingAmountStatus']=='DISTINCT_POSTED_COUNTY_AND_SPECIFIC_TOWN_ROWS_FINAL_TOTAL_UNCONFIRMED','separate county and town fee rows; total remains null '+p['sku'])
    check(not[n for n in card.select('[data-copy-key]')if n.get('data-copy-key').endswith('.sumLabel')] and not card.select('.product-reference'),'no invented sum element '+p['sku'])
    photo=card.select_one('a.product-photo-link');check(photo is not None and photo.get('href')==p['ctaHref']and photo.get('aria-label')==p['ctaLabel']and photo.find('img') is im,'photo opens exact general SKU detail '+p['sku'])
   article=doc.select_one('[data-page-id="home"]');children=[n for n in article.children if isinstance(n,Node)]
   seq=[n.get('data-shared-flower-banner')or n.get('id')or('inline-order'if 'inline-order'in n.get('class','')else'final-action')for n in children]
   check(seq==['opening','message','products-cost','delivery-cost','budget','locations','order-timing','ribbon-order','consultation','questions','sources','final-action'],'exact reviewed structural sequence')
   check(D['restrictionNotice'] is None and U['productEligibilityNotice'] is None and not doc.select('.maryang-restriction') and not doc.select('.product-eligibility'),'no inherited neighboring-facility restriction or false eligibility')
   check('해남군이 포함된 10,000원 항목' in raw and '해남군 문내면·송지면을 따로 적은 15,000원 항목' in raw and '15,000원이 해남군 모든 읍·면의 일괄 배송비라는 뜻은 아닙니다.' in raw,'county and specific town rows stay distinct without summed total')
   check('해남종합병원장례식장은 해남읍 해남로 45, 해남우리병원장례식장은 옥천면 해남로 597' in raw and '서로 다른 장례식장' in raw,'two hospital addresses stay distinct')
   check('관광레저로 534-5' in raw and '그 자체가 해당 빈소의 화환 반입 허용을 뜻하지는 않습니다.' in raw,'Usuyeong location does not imply facility acceptance')
   check('061-533-4444' in raw and not doc.select('a[href="tel:0615334444"]') and '꽃이랑 상품·주문 상담번호 1844-0644와 구분' in raw,'facility informational phone separate from merchant CTA')
   check(not any(x in raw for x in ['HOLD','LOCAL_AUTHOR','검수','2874','2873','12790','noindex는']),'internal workflow and counting labels not exposed')
   section=doc.select_one('#products-cost');direct=[n for n in section.children if isinstance(n,Node)];check(direct[-1].has_attr('data-purchase-cards') and direct[-2].name=='p','approved product prose precedes all four cards')
   check(not doc.select('[itemscope]')and not doc.select('[itemtype]')and not doc.select('[itemprop]')and not doc.select('[data-selected-hospital]'),'no structured product hospital recommendation or selected hospital')
   check([p['priceKRW']for p in D['products']]==[59000,79000,109000,149000],'four exact approved base prices only')
   check(all(x in raw for x in ['19시 이후','21시 이후','주말·공휴일','다음 날 13시 전후','최소 3시간 전','생화와 조화','별도 화환 수거는 하지 않습니다.']),'all timing material and collection qualifiers retained')
   bs=doc.select('[data-shared-flower-banner]');check([n.get('data-shared-flower-banner')for n in bs]==['message','budget','consultation'],'three approved banner variants')
   for b,n in zip(D['sharedBanners'],bs):
    im=n.find('img');check(im.get('src')=='/images/shared-banners/'+b['filename']and im.get('alt')==b['alt']and im.get('alt').count('1844-0644')==1,'exact banner alt and src '+b['id']);check(n.name=='figure'and not n.find('figcaption'),'banner figure without removed caption '+b['id'])
   for a in assets:
    ns=[im for im in doc.find_all('img')if im.get('src')==a['renderSrc']];check(len(ns)==1,'one asset occurrence '+a['id']);im=ns[0]
    check([int(im.get('width')),int(im.get('height'))]==a['dimensions']and im.get('loading')=='lazy'and im.get('decoding')=='async','image dimensions/loading '+a['id'])
  else:check(not doc.find_all('img')and not doc.select('[data-purchase-cards]')and not doc.select('[data-visible-faq]'),'404 no marketing, products or FAQ')
 for route,doc in docs.items():
  for a in doc.find_all('a'):
   href=a.get('href','');u=urlsplit(href)
   if u.scheme:check(u.scheme in ['https','tel']and (u.scheme!='tel'or href=='tel:18440644'),route+' bounded external protocol '+href);continue
   target=docs['/'if u.path=='/'else route]if u.path in ['', '/']else None;check(target is not None,route+' internal page exists '+href)
   if u.fragment:check(len([x for x in target.select('[id]')if x.get('id')==u.fragment])==1,route+' fragment target exists '+href)
 for a in assets:
  b=files[a['renderSrc'][1:]];check(len(b)==a['bytes']and hashlib.sha256(b).hexdigest()==a['sha256'],'output asset exact SHA '+a['id'])
  check(hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()==a['existingGitBlobSHA'],'existing binary Git SHA '+a['id'])
  check(b.startswith(b'\xff\xd8\xff')if a['mime']=='image/jpeg'else b[:4]==b'RIFF'and b[8:12]==b'WEBP','file format signature '+a['id'])
 css_text=files[css[0]].decode();check(not re.search(r'(?:#questions|\.faq|\.product-card|\.product-grid|\[data-visible-faq\]|\.maryang-restriction|#maryang-restriction|\.product-eligibility)[^{}]*\{[^{}]*(?:display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0(?:[;}]))',css_text),'no compiled stylesheet rules hiding FAQ or products');check('object-fit:contain'in css_text and '@media'in css_text and 'min-height:44px'in css_text,'responsive and touch-target CSS source present; computed layout unverified')
 nav_rules=re.findall(r'\.site-header \.desktop-navigation a\{([^{}]*)\}',css_text)
 check(bool(nav_rules) and 'min-width:44px' in nav_rules[-1] and 'min-height:44px' in nav_rules[-1],'explicit final nav CSS minimum 44 by 44; computed sizes still unverified')
 nav_container=re.findall(r'\.site-header \.desktop-navigation\{([^{}]*)\}',css_text)
 check(bool(nav_container) and 'flex-wrap:wrap' in nav_container[-1] and 'min-width:0' in nav_container[-1],'navigation may wrap within available width; computed overflow unverified')
 draft=(ROOT.parent/'inputs/author/draft-home.ko.md').read_text();body='\n'.join(l for l in draft.splitlines() if not l.startswith('#'));check(len(body)==2874,'accepted unique body 2874 characters excluding headings including final LF')
 return {'status':'STATIC_OUTPUT_VERIFIED_NOT_VISUAL_OR_HTTP','checks':len(checks),'checkNames':checks,'files':[{'path':k,'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()}for k,v in files.items()],'copySHA256':hashlib.sha256((ROOT.parent/'inputs/author/customer-copy.json').read_bytes()).hexdigest(),'pageCount':2,'productCount':4,'FAQCount':4,'bannerCount':3,'browserExecuted':False,'publicHTTPVerified':False,'publicationReady':False}
if __name__=='__main__':
 result=verify();(ROOT/'evidence').mkdir(exist_ok=True);(ROOT/'evidence/html-qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(ROOT/'evidence/expected-occurrences.json').write_text(json.dumps({p:expected(p)for p in ['/','/404.html']},ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['files','checkNames']},ensure_ascii=False))
