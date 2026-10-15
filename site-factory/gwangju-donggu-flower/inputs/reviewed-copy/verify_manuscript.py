"""Validate manuscript/source/spec data and generate review documents. Does not build application HTML."""
from pathlib import Path
from lxml import html
from PIL import Image
import csv,difflib,hashlib,json,re,unicodedata
B=Path(__file__).resolve().parent;ROOT=B.parent
C=json.loads((B/'customer-copy.json').read_text());P=json.loads((B/'render-plan.json').read_text());A=json.loads((B/'asset-manifest.json').read_text());S=json.loads((B/'evidence/research/source-evidence.json').read_text());SM=json.loads((B/'SOURCE-MAP.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,x):(B/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
checks=[]
def ck(name,result):
 checks.append({'name':name,'passed':bool(result)})
 if not result: raise AssertionError(name)
def walk(x,path=''):
 if isinstance(x,dict):
  for k,v in x.items():yield from walk(v,path+'/'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):yield from walk(v,path+'/'+str(i))
 elif isinstance(x,str):yield path,x
names={'home':'home.ko.md','detail':'chosun-hospital-funeral.ko.md','support':'support.ko.md','notFound':'404.ko.md'}
def link(x):return '['+x.get('label',x.get('ctaLabel',''))+']('+x.get('href','')+')'
def cards():
 o=['<!-- PRODUCT_CARDS_START -->']
 for c in C['productCards']:
  o+=['### '+c['name']+' · '+c['sku'],'!['+c['photoAlt']+'](../'+c['localPhoto']+')',c['priceLabel']+' · '+c['shippingLabel'],c['description'],'['+c['ctaLabel']+']('+c['ctaHref']+')']
 return o+[C['sharedUI']['productSampleNotice'],'<!-- PRODUCT_CARDS_END -->']
for k,fn in names.items():
 p=C[k];out=['# '+p['h1']];lead=p.get('lead',[]);out+=([lead] if isinstance(lead,str) else lead)
 if p.get('body'):out+=[p['body']]
 for s in p.get('sections',[]):
  out+=['## '+s['h2']]+s.get('paragraphs',[])
  if s.get('list'):out+=['\n'.join('- '+v for v in s['list'])]
  out+=s.get('afterList',[])
  if s.get('productCardIds'):out+=cards()
  if s.get('card'):out+=['### '+s['card']['title'],s['card']['summary'],link(s['card'])]
 if p.get('card'):out+=['## '+p['card']['title'],p['card']['summary'],link(p['card'])]
 if p.get('faq'):
  out+=['## '+p['faqHeading']]
  for f in p['faq']:out+=['### '+f['question'],f['answer']]
 if p.get('closing'):out+=[p['closing']]
 if p.get('cta'):out+=[link(p['cta'])]
 if p.get('sourceHeading'):out+=['## '+p['sourceHeading'],p['sourceIntro']]
 if p.get('sourceLink'):out+=[link(p['sourceLink'])]
 if p.get('sources'):out+=['- ['+s['label']+']('+s['url']+')' for s in p['sources']]
 text='\n\n'.join(out)+'\n';(B/'drafts'/fn).write_text(text)
 ck(k+' review Markdown exactly one H1',len(re.findall('^# ',text,re.M))==1)
 ck(k+' unique title/meta nonempty',p['title'] and p['description'])
 ck(k+' all paragraphs included',all(v in text for s in p.get('sections',[]) for v in s.get('paragraphs',[])))
ck('four unique titles',len({C[k]['title'] for k in names})==4);ck('four unique descriptions',len({C[k]['description'] for k in names})==4)
ck('customer data has only render fields',not any(x in C for x in ['status','schema','revision','sourceContext','region']))
for p,h in SM['originalHashes'].items():ck('retained original SHA: '+p,sha(B/p)==h)
for binding in SM['researchReviewedArtifactBindings']:
 p=B/'evidence/research'/binding['path'];ck('audited research byte binding: '+binding['path'],p.exists() and sha(p)==binding['sha256'])
ck('research independent audit exact SHA',sha(B/'evidence/research/independent-audit.json')=='84a3564afb04f78664ce98563c4678e7a28d0a618205841f15ffdc887ad2b219')
for binding in json.loads((B/'evidence/main-guidance/byte-verification.json').read_text()):
 b=(B/'evidence/main-guidance'/binding['file']).read_bytes();actual=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();ck('guidance Git blob '+binding['file'],actual==binding['expected'])
prices=[59000,79000,109000,149000]
for card,a,price in zip(C['productCards'],A['productPhotos'],prices):
 sku=card['sku'];raw=B/f'evidence/originals/{sku}.body';tree=html.fromstring(raw.read_bytes());rows=tree.xpath('//tr');priceRows=[r for r in rows if '판매가격' in ''.join(r.itertext())];text=raw.read_text()
 ck(sku+' official base price in original sale row',any(f'{price:,}원' in ''.join(r.itertext()) for r in priceRows) and card['basePriceKRW']==price)
 ck(sku+' original SHA',sha(raw)==S['httpSources'][sku]['bodySha256'])
 receipt=json.loads((B/f'evidence/originals/{sku}.json').read_text());ck(sku+' retained GET200 exact CTA',receipt['curlSummary'][0]=='200' and receipt['url']==card['ctaHref'])
 # Start at one rowspan group then collect its next 7 shipping rows.
 candidates=[r for r in rows if '전남광주통합특별시' in ''.join(r.itertext()) and len(r.xpath('./td'))<=4]
 ck(sku+' one provincial shipping group',len(candidates)==1)
 first=candidates[0];group=[first]+first.xpath('following-sibling::tr')[:7];grouptext=' '.join(''.join(r.itertext()) for r in group)
 ck(sku+' eight provincial rows without Dong-gu',len(group)==8 and '동구' not in grouptext and '광양시' in grouptext and '나주시' in grouptext)
 ck(sku+' no imported surcharge label',card['shippingLabel']=='배송비 포함 최종금액은 주문 상담')
 ck(sku+' exact item URL',card['ctaHref']=='https://fwith.co.kr/shop/item.php?it_id='+sku)
 ck(sku+' photo source exists in original HTML',a['sourceURL'] in text)
 ck(sku+' reused photo matches fresh research download',sha(B/card['localPhoto'])==a['sha256']==S['httpSources'][sku+'-photo']['bodySha256'])
 with Image.open(B/card['localPhoto']) as im:ck(sku+' actual500squareJPEG',im.size==(500,500) and im.format=='JPEG')
ck('exactly4individualSKUcards',len(C['productCards'])==4 and len({x['ctaHref'] for x in C['productCards']})==4)
rows=list(csv.DictReader((B/'evidence/originals/government-funeral-csv.body').read_text(encoding='cp949').splitlines()));row=rows[225]
ck('government physical227 identity address phone',row['시설명']=='조선대학교병원장례식장' and row['주소']=='광주광역시 동구 필문대로 365 (서석동)' and row['전화번호']=='062-220-3352' and row['팩스번호']=='062-220-3353')
ck('official campus detail identity','조선대학교병원 장례식장' in (B/'evidence/originals/chosun_campus_funeral_detail.html').read_text())
cnuh=html.fromstring((B/'evidence/originals/cnuh-callcenter.body').read_bytes());ck('CNUH official suspension distinct from Chosun','장례식장 한시적 운영중단으로 연결불가' in ''.join(cnuh.itertext()))
ck('hospital source failure retained','Connection refused' in (B/'evidence/originals/chosun-funeral-home.body').read_text())
fullraw=(B/'customer-copy.json').read_text();md=(B/'drafts/chosun-hospital-funeral.ko.md').read_text()
for forbidden in ['광양','나주','10,000원','69,000원','89,000원','119,000원','159,000원','무료배송','배송비 0원','당일배송 가능','즉시배송','상시접수','정상 운영 중','현장 설치','빈소 5','빈소 7','062-220-3353','1844-0645','납품 실적','제휴','2시간','3시간','24시간','확인하세요','전남대학교병원','금호장례식장','남도장례식장','꽃이랑 공통 안내 이미지','실제 판매상품 사진이 아닌 AI 생성']:
 ck('no unsupported/inherited string: '+forbidden,forbidden not in fullraw)
ck('dated official full address appears once',fullraw.count('광주광역시 동구 필문대로 365 (서석동)')==1)
ck('facility phone appears once',fullraw.count('062-220-3352')==1)
ck('conditional entry and schedule present early',all(t in C['detail']['lead'][1] for t in ['전달할 수 있는지','반입·수령 조건','주문 전에 상담']))
ck('current operations not assumed in source disclosure','현재 운영 상태나 화환 반입을 확정하는 안내가 아닙니다' in C['detail']['sourceIntro'])
ck('shipment phase correct', '상품 출고 후 취소' in C['detail']['faq'][1]['answer'] and '제작 완료된 꽃 상품' in C['detail']['faq'][1]['answer'])
ck('refund applicability unresolved', '개별 주문 상담이 필요' in C['detail']['faq'][1]['answer'])
for a in A['sharedBanners']:
 p=B/a['assetPath'];ck(a['variant']+' approved bytes/SHA',sha(p)==a['sha256'] and p.stat().st_size==a['bytes'])
 with Image.open(p) as im:ck(a['variant']+' WEBP1774x887',im.size==(1774,887) and im.format=='WEBP')
 alt=C['sharedBannerAlt'][a['variant']];ck(a['variant']+' exact phone suffix once',alt.endswith('전화 1844-0644.') and alt.count('1844-0644')==1)
 ck(a['variant']+' no caption and responsive',a['caption'] is None and a['decoding']=='async' and a['responsive']=='width:100%;height:auto')
for f in C['detail']['faq']:ck('FAQ in review once '+f['question'],md.count(f['question'])==1 and md.count(f['answer'])==1)
ck('budget has no authoring-process explanation',all(x not in next(s for s in C['detail']['sections'] if s['id']=='budget')['paragraphs'][0] for x in ['표에는','이 페이지에는','표시했습니다']))
ck('order follow-on provider assistance',next(s for s in C['detail']['sections'] if s['id']=='order')['afterList'][0]=='빈소 안내를 기다리는 중이거나 상품을 아직 정하지 못하셨어도, 먼저 상품과 리본 문구 상담을 도와드리겠습니다.')
ck('three visible FAQ planned',len(C['detail']['faq'])==3 and P['faq']['alwaysVisible'] and not P['faq']['actualHTMLVerified'])
ck('one source H2',md.count('## '+C['detail']['sourceHeading'])==1)
ck('production sitemap2 planned',P['productionPolicy']['sitemapPageIds']==['home','detail'] and P['productionPolicy']['sitemapURLCount']==2)
ck('preview noindex all',all(p['previewRobots']=='noindex,nofollow,noarchive' and not p['previewSitemapIncluded'] for p in P['pages']))
support=next(p for p in P['pages'] if p['id']=='support');nf=next(p for p in P['pages'] if p['id']=='notFound')
ck('support noindex1child no menu sitemap banner',support['actualChildCount']==1 and support['productionRobots']=='noindex,follow' and not support['productionSitemapIncluded'] and not support['mainMenuIncluded'] and support['bannerCount']==0)
ck('404 exception canonical social banner',nf['HTTPStatusRequirement']==404 and nf['canonicalAtProduction'] is None and not nf['socialMetadataIncluded'] and nf['bannerCount']==0 and not nf['marketingBanners'])
ck('host unassigned production disabled',P['origin'] is None and P['domain'] is None and not P['productionEnabled'] and all(p['canonical'] is None for p in P['pages']))
ck('detail path match cards',P['pages'][1]['proposedPath']==C['home']['sections'][0]['card']['href']==C['support']['card']['href'])
crumb=P['navigation']['detailBreadcrumb']['items'];ck('visible home support detail breadcrumb planned',[x['pageId'] for x in crumb]==['home','support','detail'] and crumb[1]['href']=='/regions/' and crumb[-1]['ariaCurrent']=='page')
edges=P['navigation']['edges'];inbound={p['id']:sorted({e['from'] for e in edges if e['to']==p['id'] and e['from']!=p['id']}) for p in P['pages']};ck('planned inbound support1 detail2',len(inbound['support'])>=1 and len(inbound['detail'])>=2)
meta=P['socialMetadata'];ck('3content social B201summary500',meta['appliesToPageIds']==['home','detail','support'] and meta['twitter:card']=='summary' and meta['og:image:width']==500 and meta['og:image:height']==500 and 'B201' in meta['og:image'])
ck('new image disabled',not meta['newImageGeneration'] and not A['newImageGeneration'])
ck('H1H2H3 hierarchy explicit',P['headings']['H1ExactlyOneEveryPage'] and P['headings']['homeFacilityGuideCard']=='H3 under facility-guide H2' and P['headings']['productNames']=='H3 below products H2')
# Complete renderable Korean text inventory; source links/structural keys inventoried separately.
visible=[{'pointer':ptr,'text':v} for ptr,v in walk(C) if re.search('[가-힣]',v)]
dump('visible-strings.json',visible)
lines=['# 고객 노출·접근성·메타 문자열 전문','',f'문자열 {len(visible)}개. JSON 포인터별 원문이며 제목·본문·카드·FAQ·버튼·alt·출처명을 모두 포함한다. 렌더 결과 검증은 아니다.']
for i,x in enumerate(visible,1):lines+=['',f"## {i}. {x['pointer']}",x['text']]
(B/'ALL-VISIBLE-STRINGS.ko.md').write_text('\n'.join(lines)+'\n')
ck('all Korean render strings inventoried',len(visible)==sum(bool(re.search('[가-힣]',v)) for _,v in walk(C)))
d=C['detail'];parts=d['lead'][:]
for s in d['sections']:parts+=s.get('paragraphs',[])+s.get('list',[])+s.get('afterList',[])
main='\n'.join(parts);faq='\n'.join(f[k] for f in d['faq'] for k in ['question','answer']);full='\n'.join([main,faq,d['closing']]);home='\n'.join([C['home']['lead']]+[x for s in C['home']['sections'] for x in s['paragraphs']])
entities=['조선대학교병원 장례식장','조선대학교병원장례식장','조선대병원','조대병원','광주 동구','광주광역시 동구','동구','광양장례식장','광양시','광양','나주종합병원장례식장','나주종합병원 장례식장','나주종합병원','나주시','나주','순천 성가롤로병원 장례식장','성가롤로병원 장례식장','성가롤로병원','순천시','순천','목포한국병원 장례식장','목포한국병원','목포시','목포','여수전남병원장례식장','여수전남병원','여수시','여수']
def norm(t,mask=False):
 if mask:
  for e in sorted(entities,key=len,reverse=True):t=t.replace(e,'지역시설')
 return re.sub(r'\s+','',unicodedata.normalize('NFC',t))
def shingles(t):return {t[i:i+20] for i in range(max(0,len(t)-19))}
def clean_md(t):
 t=re.sub(r'<!-- PRODUCT_CARDS_START -->.*?<!-- PRODUCT_CARDS_END -->','',t,flags=re.S).split('## 출처 및 확인 정보')[0];t=re.sub(r'^#{1,6} .*$','',t,flags=re.M);return re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',t).strip()
refs=['gwangyang-customer-copy-20261015/drafts/gwangyang-funeral.ko.md','naju-customer-copy-20261015/drafts/naju-hospital-funeral.ko.md','suncheon-customer-copy-20261015/drafts/suncheon-stcarollo-funeral.ko.md','yeosu-customer-copy-20261014/drafts/yeosu-jeonnam-hospital-funeral.ko.md','mokpo-content-preparation-20261014/drafts/condolence.ko.md'];comparisons=[]
for path in refs:
 p=ROOT/path;ref=clean_md(p.read_text());row={'reference':path,'sha256':sha(p)}
 for mask in [False,True]:
  a,b=norm(full,mask),norm(ref,mask);aa,bb=shingles(a),shingles(b);m=difflib.SequenceMatcher(None,a,b,autojunk=False).find_longest_match();row['entityMasked' if mask else 'literal']={'shared20CharacterShingles':len(aa&bb),'draft20CharacterShingles':len(aa),'overlapRatio':round(len(aa&bb)/len(aa),6),'longestSharedSpanCharacters':m.size,'longestSharedSpan':a[m.a:m.a+m.size]}
 sentence=lambda t:{s.strip() for s in re.split(r'(?<=[.!?])\s+|\n',t) if len(s.strip())>=20};row['exactSharedSentencesAtLeast20Chars']=sorted(sentence(full)&sentence(ref));comparisons.append(row)
cardgates=[]
for k,card in [('home',C['home']['sections'][0]['card']),('support',C['support']['card'])]:
 prefix=0
 for a,b in zip(card['title'],card['summary']):
  if a!=b:break
  prefix+=1
 ratio=difflib.SequenceMatcher(None,card['summary'],d['lead'][0],autojunk=False).ratio();ck(k+' distinct card summary',not card['summary'].startswith('조선대학교병원 장례식장 근조화환') and prefix<=8 and ratio<.7);cardgates.append({'page':k,'commonLeadingChars':prefix,'firstAnswerSimilarity':round(ratio,6)})
metrics={'canonicalCopySHA256':sha(B/'customer-copy.json'),'method':'Unicode code points incl spaces. Excludes headings/cards/sources/CTA/navigation. FAQ/closing separate. Not ranking formula or mechanical minimum.','mainProseChars':len(main),'mainProseNonWhitespaceChars':len(re.sub(r'\s','',main)),'FAQChars':len(faq),'mainPlusFAQAndClosingChars':len(full),'homeProseChars':len(home),'visibleKoreanStringCount':len(visible),'comparisonMethod':'20-character distinct shingles; NFC/no whitespace; literal and entity-masked. Exact sentences >=20 chars. Shared merchant facts and product/policy meaning remain expected.','comparisons':comparisons,'cardGates':cardgates,'authorSemanticReview':'PURCHASE-PLAN.ko.md; independent reviewer pending. Low lexical overlap cannot prove semantically useful difference.'};dump('body-count-and-overlap.json',metrics)
dump('local-verification.json',{'status':'AUTHOR_MANUSCRIPT_SOURCE_AND_SPEC_CHECKS_ONLY_INDEPENDENT_REVIEW_PENDING','canonicalCopySHA256':sha(B/'customer-copy.json'),'renderPlanSHA256':sha(B/'render-plan.json'),'checkedCount':len(checks),'checks':checks,'plannedInbound':inbound,'actualHTMLVerified':False,'actualBrowserVerified':False,'publicHTTPVerified':False,'appCodeCreated':False,'remoteWrite':False,'newImageCreated':False,'noNewSoftwareInstalled':True,'attemptsAndCorrections':['Initial CSV decode as UTF8 failed; reread original CP949 and verified row227.','GitHub apply_patch text adds newline; rebuilt originals from exact tool content and verified Git blobs.']})
print(json.dumps({'checks':len(checks),'mainProseChars':len(main),'withFAQClosing':len(full),'visibleStrings':len(visible),'copySHA256':sha(B/'customer-copy.json'),'renderPlanSHA256':sha(B/'render-plan.json'),'maskedOverlaps':[{x['reference']:x['entityMasked']['overlapRatio']} for x in comparisons],'exactSentences':[{x['reference']:x['exactSharedSentencesAtLeast20Chars']} for x in comparisons]},ensure_ascii=False,indent=2))
