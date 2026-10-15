from pathlib import Path
from html.parser import HTMLParser
from collections import Counter
import json,hashlib,html,re,unicodedata,datetime,copy,difflib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
P=ROOT/'yeosu-production-preparation-20261015'
PORT=P/'source/portable/yeosu-portable-build-inputs-20261015'
C=PORT/'yeosu-local-implementation-20261015/candidate'
D=C/'dist'; PRE=P/'evidence/final-preview-dist'
COPY=ROOT/'yeosu-customer-copy-20261014'; R=ROOT/'yeosu-research-preparation-20261014'
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def norm(s): return re.sub(r'\s+',' ',unicodedata.normalize('NFC',html.unescape(s))).strip()
def load(p): return json.loads(Path(p).read_text())
def save(n,j): (OUT/n).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def rel(p): return str(p.relative_to(ROOT))
def bind(p):
 b=p.read_bytes();return dict(path=rel(p),bytes=len(b),sha256=sha(b))
def tree(rows):return sha(''.join(r['sha256']+'  '+r['path']+'\n' for r in sorted(rows,key=lambda r:r['path'])).encode())
class Node:
 def __init__(self,t='',a=(),p=None):self.tag=t;self.attrs=dict(a);self.parent=p;self.children=[]
 def text(self):return ''.join(x.text() if isinstance(x,Node) else x for x in self.children)
 def all(self,pred=lambda n:True):
  result=[]
  for x in self.children:
   if isinstance(x,Node):
    if pred(x): result.append(x)
    result.extend(x.all(pred))
  return result
 def has(self,k):return k in self.attrs
class Parser(HTMLParser):
 def __init__(self,s):super().__init__(convert_charrefs=True);self.root=Node();self.cur=self.root;self.feed(s)
 def handle_starttag(self,t,a):
  n=Node(t,a,self.cur);self.cur.children.append(n)
  if t not in ['meta','link','img','input','br','hr','source','wbr','area','base','embed','param','track','col']:self.cur=n
 def handle_startendtag(self,t,a):self.handle_starttag(t,a);self.handle_endtag(t)
 def handle_endtag(self,t):
  n=self.cur
  while n.parent is not None:
   if n.tag==t:self.cur=n.parent;return
   n=n.parent
 def handle_data(self,s):self.cur.children.append(s)
def get(n,t):return n.all(lambda x:x.tag==t)
def attr(n,a):return n.all(lambda x:a in x.attrs)
def mdblocks(s):
 out=[]
 s=re.sub(r'<!--.*?-->','',s,flags=re.S)
 for p in re.split(r'\n\s*\n',s.strip()):
  if p.startswith('<!--') or p.startswith('!['):continue
  for line in p.splitlines() if p.startswith('- ') else [p]:
   text=re.sub(r'^#{1,3} |^- ','',line);text=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',text);out.append(norm(text))
 return out
checks=[]
def chk(id,ok,evidence):checks.append(dict(id=id,status='PASS' if ok else 'FAIL',evidence=evidence));return ok
# Independent binding of all declared inputs and current generated outputs.
manifests={}
for name,base,mf in [('source',P/'source',P/'evidence/source-manifest.json'),('control',P/'control',P/'evidence/control-manifest.json'),('original40',C,ROOT/'yeosu-local-implementation-20261015/evidence/source-manifest.json')]:
 j=load(mf);rows=[]
 for expected in j['files']:
  b=(base/expected['path']).read_bytes();actual=dict(path=expected['path'],bytes=len(b),sha256=sha(b));actual['matches']=actual['sha256']==expected['sha256'] and len(b)==expected['bytes'];rows.append(actual)
 manifests[name]=dict(manifest=bind(mf),fileCount=len(rows),treeSHA256=tree(rows),expectedTreeSHA256=j['treeSHA256'],matches=all(r['matches'] for r in rows) and tree(rows)==j['treeSHA256'],files=rows)
 chk(name+'-manifest',manifests[name]['matches'],{'count':len(rows),'treeSHA256':tree(rows)})
frozen75=[]
for expected in load(P/'control/scripts/direct-yeosu/preview-source-manifest.json'):
 b=(P/'source'/expected['path']).read_bytes();frozen75.append(dict(**expected,currentSHA256=sha(b),matches=len(b)==expected['bytes'] and sha(b)==expected['sha256']))
chk('frozen-portable75',len(frozen75)==75 and all(r['matches'] for r in frozen75),{'count':len(frozen75)})
original26=[]
for expected in load(PORT/'yeosu-local-implementation-20261015/evidence/original-input-baseline.json'):
 b=(PORT/expected['path']).read_bytes();original26.append(dict(**expected,currentSHA256=sha(b),matches=len(b)==expected['bytes'] and sha(b)==expected['sha256']))
chk('original26-inputs',len(original26)==26 and all(r['matches'] for r in original26),{'count':len(original26)})
outputRows=[dict(path=str(p.relative_to(D)),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(D.rglob('*')) if p.is_file()]
spec=load(ROOT/'yeosu-page-spec-addendum-20261015/page-spec-addendum.ko.json')
metadata=load(COPY/'customer-copy-metadata.json');products=load(COPY/'product-cards.json')
pages=[]
headComparisons=[]
for conf in spec['pages']:
 path=conf['path'];f=D/('index.html' if path=='/' else path.lstrip('/') if path.endswith('.html') else path.strip('/')+'/index.html');raw=f.read_bytes();s=raw.decode();dom=Parser(s).root;main=get(dom,'main')[0];opening=next(n for n in main.all() if n.attrs.get('id')=='opening');maintext=norm(main.text())
 meta={n.attrs.get('name',n.attrs.get('property','')):n.attrs.get('content') for n in get(dom,'meta')};head=s.split('</head>')[0]+'</head>';body=s[s.index('<body'):];canonical=[n.attrs.get('href') for n in get(dom,'link') if n.attrs.get('rel')=='canonical'];ps=get(opening,'p');first=norm(ps[0].text()) if ps else None
 obs=dict(id=conf['id'],path=path,role=conf['role'],file=bind(f),title=norm(get(dom,'title')[0].text()),meta=meta,canonical=canonical,h1=[norm(n.text()) for n in get(main,'h1')],headSHA256=sha(head.encode()),bodySHA256=sha(body.encode()),firstParagraph=first,first120=(first or '')[:120],first180=(first or '')[:180],firstParagraphCodepoints=len(first or ''),firstParagraphSHA256=sha((first or '').encode()),headings=[dict(level=n.tag,text=norm(n.text())) for n in main.all(lambda n:n.tag in ['h1','h2','h3'])],links=[dict(href=n.attrs.get('href'),text=norm(n.text()),required=n.has('data-required-cta')) for n in get(main,'a')],images=[n.attrs for n in get(main,'img')],faqQuestions=[norm(n.text()) for n in attr(main,'data-faq-question')],faqAnswers=[norm(n.text()) for n in attr(main,'data-faq-answer')],mainText=maintext,fullBodyText=norm(get(dom,'body')[0].text()),sourceHeadingCount=sum(norm(n.text())=='출처 및 확인 정보' for n in get(main,'h2')),staticHiddenElements=[dict(tag=n.tag,attrs=n.attrs,text=norm(n.text())) for n in main.all(lambda n:n.has('hidden') or n.attrs.get('aria-hidden')=='true' or re.search(r'display\s*:\s*none|visibility\s*:\s*hidden',n.attrs.get('style','')))],bannerSources=[n.attrs['src'] for n in get(main,'img') if '/shared-banners/' in n.attrs.get('src','')],breadcrumbs=[dict(text=norm(n.text()),href=n.attrs.get('href')) for nav in main.all(lambda n:n.tag=='nav' and n.attrs.get('aria-label')=='현재 위치') for n in nav.all(lambda n:n.tag in ['a','span'])],cardSummaries=[norm(p.text()) for n in attr(main,'data-content-card') for p in get(n,'p')],productSKUs=[n.attrs['data-product-sku'] for n in attr(main,'data-product-sku')])
 chk(conf['id']+'-h1',len(obs['h1'])==1,obs['h1'])
 chk(conf['id']+'-sourceHeadingCount',obs['sourceHeadingCount']==conf['sourceHeadingCount'],obs['sourceHeadingCount'])
 chk(conf['id']+'-product-count',len(obs['productSKUs'])==conf['productCardCount'],obs['productSKUs'])
 chk(conf['id']+'-faq-count',len(obs['faqQuestions'])==conf['faqCount'] and len(obs['faqAnswers'])==conf['faqCount'],obs['faqQuestions'])
 chk(conf['id']+'-banner-count',len(obs['bannerSources'])==(3 if conf['id'] in ['home','article'] else 0),obs['bannerSources'])
 if conf.get('sourceFile'):
  md=(COPY/conf['sourceFile']).read_text();expected=mdblocks(md);actual=[norm(n.text()) for n in attr(main,'data-reviewed-block')]
  obs['reviewedBlockParity']=dict(expected=expected,actual=actual,match=expected==actual)
  chk(conf['id']+'-all-copy-blocks-exact',expected==actual,{'expectedCount':len(expected),'actualCount':len(actual)})
  chk(conf['id']+'-h2-order',[h['text'] for h in obs['headings'] if h['level']=='h2']==conf['h2Order'],conf['h2Order'])
  chk(conf['id']+'-title',obs['title']==conf['title'],obs['title']);chk(conf['id']+'-description',meta['description']==conf['metaDescription'],meta['description']);chk(conf['id']+'-h1-exact',obs['h1']==[conf['h1']],obs['h1'])
  sourceFirst=norm(re.split(r'\n\s*\n',md.strip())[1]);chk(conf['id']+'-first-answer-is-first-actual-paragraph',first==sourceFirst and len(ps)>0,{'first':first,'noEarlierMainParagraph':get(main,'p')[0] is ps[0]})
  chk(conf['id']+'-no-earlier-lead',get(main,'p')[0] is ps[0], 'No earlier main paragraph; breadcrumb/nav labels are not article answer prose.')
  for faq in spec['faqBinding']['items'] if conf['id']=='article' else []:
   q=faq['question'];ans=md.split('### '+q+'\n\n')[1].split('\n\n')[0];chk('faq-'+q,obs['faqQuestions'].count(q)==1 and obs['faqAnswers'].count(norm(ans))==1 and sha(ans.encode())==faq['answerUTF8SHA256'],{'answer':ans,'answerSHA256':sha(ans.encode())})
  stripped=md.split('## 출처 및 확인 정보')[0];stripped=re.sub(r'<!-- PRODUCT_CARDS_START -->[\s\S]*?<!-- PRODUCT_CARDS_END -->','',stripped);v=norm(' '.join(mdblocks(stripped)));prose=norm(' '.join(mdblocks('\n'.join(l for l in stripped.splitlines() if not l.startswith('#')))));obs['uniqueBodyMetrics']=dict(codepointsWithHeadings=len(v),codepointsWithoutHeadings=len(prose),withoutWhitespace=len(re.sub(r'\s','',v)),notRankingFormula=True)
 old=(PRE/f.relative_to(D)).read_text();oldhead=old.split('</head>')[0]+'</head>'
 headComparisons.append(dict(id=conf['id'],previewHeadSHA256=sha(oldhead.encode()),productionHeadSHA256=sha(head.encode()),previewHead=oldhead,productionHead=head,fullHeadDiff='\n'.join(difflib.unified_diff(oldhead.replace('><','>\n<').splitlines(),head.replace('><','>\n<').splitlines(),fromfile='frozen-preview-head',tofile='local-production-head'))))
 oldbody=old[old.index('<body'):];obs['previewBodySHA256']=sha(oldbody.encode());chk(conf['id']+'-body-immutable-preview-to-production',body==oldbody,obs['bodySHA256'])
 chk(conf['id']+'-no-unsupported-main-building','본관' not in maintext, 'Exact main text scanned; historical research planning word is not customer copy.')
 chk(conf['id']+'-no-internal-workflow-copy',not any(w in maintext for w in ['SEO','Business Truth','Production','Shadow','QA','검수','클러스터','검색의도']), 'Main customer text scanned and independently read.')
 ordered=main.all(lambda n:n.tag in ['h2','img'])
 if conf['id'] in ['home','article']:
  bannerNext=[]
  for i,n in enumerate(ordered):
   if n.tag=='img' and '/shared-banners/' in n.attrs.get('src',''):
    nxt=next((x for x in ordered[i+1:] if x.tag=='h2'),None);bannerNext.append(dict(src=n.attrs['src'],nextHeading=norm(nxt.text()) if nxt else None))
  expectedOrder=['/images/shared-banners/flower-'+v+'.webp' for v in ['message','budget','consultation']]
  chk(conf['id']+'-banner-order-and-section-boundaries',[b['src'] for b in bannerNext]==expectedOrder and [b['nextHeading'] for b in bannerNext]==[conf['bannersBeforeH2'][v] for v in ['message','budget','consultation']],bannerNext)
 metaTags=re.findall(r'<meta\b[^>]*>',head)
 for index,tag in enumerate(metaTags):
  names=re.findall(r'\s([a-zA-Z][a-zA-Z0-9:_-]*)=',tag)
  chk(conf['id']+'-meta-attrs-'+str(index),len(names)==len(set(names)) and not ('name' in names and 'property' in names),tag)
 pages.append(obs)
by={p['id']:p for p in pages}
chk('unique-four-titles',len({p['title'] for p in pages})==4,[p['title'] for p in pages])
chk('unique-four-h1',len({p['h1'][0] for p in pages})==4,[p['h1'][0] for p in pages])
chk('unique-four-meta',len({p['meta']['description'] for p in pages})==4,[p['meta']['description'] for p in pages])
save('head-change-comparison.json',dict(scope='Exact generated head comparison only. Planned host and synthetic revision; not public evidence.',pages=headComparisons))
# Inspect exact product content and file identity; extract source facts, rather than importing another review's claims.
productEvidence=[]
for prod in products:
 sku=prod['sku'];f=COPY/'evidence'/f'{sku}-selected.html';dom=Parser(f.read_text()).root;text=norm(dom.text());facts={}
 for row in get(dom,'tr'):
  th=get(row,'th');td=get(row,'td')
  if th and td:facts[norm(th[0].text())]=norm(td[0].text())
 imageFile=D/f'images/products/{sku}.jpg';original=COPY/prod['localPhoto'];im=next(n for n in by['article']['images'] if n['src']==f'/images/products/{sku}.jpg');cta=[l for l in by['article']['links'] if l['href']==prod['ctaHref']]
 checksHere=dict(price=facts.get('판매가격')==f'{prod["basePriceKRW"]:,}원',phone=facts.get('소비자상담 관련 전화번호')=='1844-0644',imageBytes=sha(imageFile.read_bytes())==prod['photoSHA256']==sha(original.read_bytes()),oneProductCTA=len(cta)==1,oneCard=by['article']['productSKUs'].count(sku)==1,meaningfulAlt=im['alt'] and '샘플' in im['alt'])
 for k,ok in checksHere.items():chk(sku+'-'+k,ok,facts if k in ['price','phone'] else {'image':str(imageFile.relative_to(D)),'cta':cta,'alt':im['alt']})
 productEvidence.append(dict(sku=sku,source=bind(f),sourceURL=prod['ctaHref'],originalObservedUTC=prod['priceObservedUTC'],observedAgeHours=round((datetime.datetime.fromisoformat(now)-datetime.datetime.fromisoformat(prod['priceObservedUTC'])).total_seconds()/3600,2),fields=facts,sourceExcerpt=text[:500],photo=bind(original),localOutput=bind(imageFile),imageAttributes=im,checks=checksHere,currentPriceStockOrHTTPVerified=False))
assets=[]
for f in sorted(PRE.rglob('*')):
 if f.is_file() and (f.suffix in ['.jpg','.webp','.css','.svg']):
  target=D/f.relative_to(PRE);same=target.exists() and f.read_bytes()==target.read_bytes();assets.append(dict(path=str(f.relative_to(PRE)),sha256=sha(f.read_bytes()),unchanged=same));chk('immutable-asset-'+str(f.relative_to(PRE)),same,assets[-1])
for b in spec['sharedBannerBinding']['assets']:
 f=D/b['renderSrc'].lstrip('/');chk('banner-sha-'+b['variant'],sha(f.read_bytes())==b['sha256'],bind(f))
 for page in ['home','article']:
  im=next(n for n in by[page]['images'] if n['src']==b['renderSrc']);chk(page+'-banner-attrs-'+b['variant'],im.get('alt')==b['alt'] and im.get('width')=='1774' and im.get('height')=='887' and im.get('loading')=='lazy' and im.get('decoding')=='async',im)
# Graph/meta observations (planned origin only, never proof of published indexability).
routeSet={p['path'] for p in pages};inbound={p:[] for p in routeSet}
for page in pages:
 for l in page['links']:
  target=l['href']
  if target.startswith('/') and not target.startswith('//'):
   chk(page['id']+'-target-'+target,target.split('#')[0] in routeSet,l)
   if target in inbound and target!=page['path']:inbound[target].append(page['path'])
for path,src in inbound.items():
 if path not in ['/','/404.html']:chk('inbound-'+path,len(src)>0,sorted(set(src)))
sm=[]
for f in sorted(D.glob('sitemap*.xml')):
 sm+= [x.text for x in ET.parse(f).getroot().iter() if x.tag.endswith('}loc') and '/sitemap' not in (x.text or '')]
expectedURLs=['https://yeosu.fwith.kr/','https://yeosu.fwith.kr/regions/yeosu-jeonnam-hospital-funeral-wreath/']
chk('sitemap-exact2',sorted(sm)==sorted(expectedURLs),sm)
for page in pages:
 id=page['id'];meta=page['meta'];canon=page['canonical'];url='https://yeosu.fwith.kr'+page['path']
 expectedRobots='index,follow' if id in ['home','article'] else 'noindex,follow'
 chk(id+'-robots',meta['robots']==expectedRobots,meta['robots'])
 chk(id+'-canonical',canon==([] if id=='not-found' else [url]),canon)
 if id!='not-found':
  chk(id+'-og-same-content',all(meta.get(k)==v for k,v in {'og:title':page['title'],'og:description':meta['description'],'og:url':url,'og:type':'website','og:locale':'ko_KR'}.items()),{k:v for k,v in meta.items() if k.startswith('og:')})
 if id!='not-found':
  socialExpected={'og:type':'website','og:title':page['title'],'og:description':meta['description'],'og:locale':'ko_KR','og:url':url,'og:image':'https://yeosu.fwith.kr/images/products/B201.jpg','og:image:alt':'근조 3단 화환 B201 샘플의 흰 꽃과 노란 꽃','twitter:card':'summary','twitter:title':page['title'],'twitter:description':meta['description'],'twitter:image':'https://yeosu.fwith.kr/images/products/B201.jpg','twitter:image:alt':'근조 3단 화환 B201 샘플의 흰 꽃과 노란 꽃'}
  chk(id+'-social-exact12',all(meta.get(k)==v for k,v in socialExpected.items()) and len([k for k in meta if k.startswith(('og:','twitter:'))])==12,socialExpected)
 if id in ['home','article']:
  twitterOK=meta.get('twitter:card') in ['summary','summary_large_image'] and meta.get('twitter:title')==page['title'] and meta.get('twitter:description')==meta['description']
  chk(id+'-twitter-required',twitterOK,{k:v for k,v in meta.items() if k.startswith('twitter:')})
  page['staticMetadataPass']=twitterOK and canon==[url] and meta.get('og:url')==url and meta['robots']==expectedRobots and sorted(sm)==sorted(expectedURLs)
# card gate only for a card summary actually used, associated with article; metadata is not silently invented as a card.
def lcs(a,b):
 prev=[0]*(len(b)+1)
 for x in a:
  nxt=[0]
  for j,y in enumerate(b):nxt.append(prev[j]+1 if x==y else max(prev[j+1],nxt[-1]))
  prev=nxt
 return prev[-1]
summary=by['support']['cardSummaries'][0];article=by['article'];common=0
for a,b in zip(summary,article['title']):
 if a!=b:break
 common+=1
ll=lcs(summary,article['firstParagraph']);ratio=2*ll/(len(summary)+len(article['firstParagraph']))
summaryObs=dict(actualUsedAt='/regions/ → article card',text=summary,title=article['title'],firstAnswer=article['firstParagraph'],commonPrefixCodepoints=common,lcsCodepoints=ll,lcsSimilarityFormula='2*LCS/(len(summary)+len(firstAnswer))',similarity=ratio,primaryPrefix=False,oneActualSibling=True,homeCardSummary='NOT_USED_NOT_FABRICATED')
chk('used-card-summary-separation',not summary.startswith('여수전남병원장례식장 근조화환') and common<=8 and ratio<.7,summaryObs)
# Current readback bind of contracts against preserved GitHub response bytes.
contractRoot=ROOT/'mokpo-release-readiness-20261014/inputs';contract=load(contractRoot/'current-contract-readback.json');integrity=[]
for ent in contract['entries']:
 p=contractRoot/ent['path'].replace('/','__')
 if not p.exists():continue
 b=p.read_bytes();raw=ent['content'].encode();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();integrity.append(dict(**bind(p),contentMatch=b==raw,gitBlobSHA1=blob,reportedBlobSHA1=ent.get('sha'),blobMatch=blob==ent.get('sha')))
for row in integrity:chk('contract-'+row['path'],row['contentMatch'] and row['blobMatch'],row)
rawContractFiles=[contractRoot/'site_factory_rules_v1.md',contractRoot/'site_factory_query_first_v1_1_test.md',contractRoot/'site_factory_rules_v1_2.md']
contractSourceManifest=load(contractRoot/'site-factory__contracts__rules__source-manifest.json')
rawOriginalChecks=[]
for row in contractSourceManifest['sources']:
 p=contractRoot/Path(row['path']).name;b=(p.read_text().replace('\r\n','\n').replace('\r','\n').rstrip('\n')+'\n').encode();check=dict(source=bind(p),normalizedSHA256=sha(b),expectedSHA256=row['sha256'],match=sha(b)==row['sha256'] and len(b)==row['bytes']);rawOriginalChecks.append(check);chk('master-original-'+p.name,check['match'],check)
save('contract-integrity.json',dict(sourceRef=contract['sourceRef'],retainedResponsesOnly=True,noFreshRemoteRead=True,checks=integrity,rawOriginals=rawOriginalChecks,sourceManifest=contractSourceManifest,policyCopies=[dict(name=n,copyMatchesResearch=(COPY/'evidence'/n).read_bytes()==(R/'inputs'/n).read_bytes(),source=bind(R/'inputs'/n),copy=bind(COPY/'evidence'/n)) for n in ['SALES_COPY_ACCEPTANCE.md','SEARCH_CONTENT_STRATEGY.md']],sharedBannerStandard=bind(ROOT/'mokpo-content-preparation-20261014/inputs/SHARED_BANNER_STANDARD.md')))
inputs=set()
for root in [COPY,ROOT/'yeosu-page-spec-addendum-20261015',R]:inputs.update(p for p in root.rglob('*') if p.is_file() and p.suffix not in ['.pyc'])
inputs.update(contractRoot/n for n in [p.name for p in contractRoot.glob('site*.md')]+['current-contract-readback.json','site-factory__contracts__rules__source-manifest.json'])
inputs.add(ROOT/'mokpo-content-preparation-20261014/inputs/SHARED_BANNER_STANDARD.md');inputs.add(ROOT/'mokpo-content-release-review-20261015/rubric.json')
rows=[bind(p) for p in sorted(inputs)];binding=dict(schema='yeosu-release-content-binding/v1',reviewedUTC=now,scope='local retained originals and production fixture only',frozenRemotePredecessor='708611e4bca85ae66931ca0ab5fc2ad49e8b55d1',plannedOrigin='https://yeosu.fwith.kr',regionCode='12130',launchOrder=27,actualRemoteSuccessor=None,runnerArtifact=None,sourceManifest=manifests['source'],controlManifest=manifests['control'],original40=manifests['original40'],frozen75=frozen75,original26=original26,originalInputsMatch=all(x['matches'] for x in original26),reviewInputFiles=rows,inputSetSHA256=tree(rows),outputFiles=outputRows,outputTreeSHA256=tree(outputRows),compiledOutputClassification='LOCAL_PRODUCTION_FIXTURE_NOT_REAL_RUNNER_ARTIFACT',spec=bind(ROOT/'yeosu-page-spec-addendum-20261015/page-spec-addendum.ko.json'))
save('input-binding.json',binding);save('output-manifest.json',dict(treeSHA256=tree(outputRows),files=outputRows));save('original-preservation.json',dict(original40=manifests['original40'],frozen75=frozen75,original26=original26,customerBodyCount=len(pages),customerBodies=[dict(id=p['id'],productionBodySHA256=p['bodySHA256'],previewBodySHA256=p['previewBodySHA256'],same=p['bodySHA256']==p['previewBodySHA256']) for p in pages],staticAssetCount=len(assets),staticAssets=assets,originalMetadataIntentionallyUnchanged=metadata['domain'] is None and metadata['canonical'] is None and metadata['robots'] is None,productionHeadChangesAreSeparate=True))
save('static-observations.json',dict(reviewedUTC=now,normalization='HTML entity decode; NFC; collapse whitespace; Unicode codepoints, no punctuation removal',pages=pages,sourceProductEvidence=productEvidence,summaryGate=summaryObs,sitemapURLs=sm,robotsText=(D/'robots.txt').read_text(),responseHeadersFile=(D/'_headers').read_text(),inbound={k:sorted(set(v)) for k,v in inbound.items()},checks=checks,counts=dict(total=len(checks),passCount=sum(c['status']=='PASS' for c in checks),failCount=sum(c['status']=='FAIL' for c in checks)),browserComputedVisibility='PENDING_NO_BROWSER',publicHTTP='PENDING_NO_NETWORK'))
print(json.dumps({'source':manifests['source']['treeSHA256'],'control':manifests['control']['treeSHA256'],'checks':len(checks),'failures':[x for x in checks if x['status']=='FAIL'],'first':[dict(id=p['id'],first120=p['first120'],first180=p['first180']) for p in pages[:]]},ensure_ascii=False,indent=2))
