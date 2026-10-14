from pathlib import Path
import json,hashlib,re,itertools,difflib
from collections import Counter
from PIL import Image
O=Path(__file__).parent;R=Path('/workspace/shared/gangnam-research-20261013');S=Path('/workspace/shared/seocho-plan-copy-20261013')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
a=read(O/'copy/article-copy.final.json');c=read(O/'copy/common-visible-copy.final.json');p=read(O/'plan/fixed-plan.json');cat=read(O/'plan/catalog-policy-evidence.json');reg=read(O/'plan/evidence-registry.json')
checks=[]
def ck(name,ok,detail=None):checks.append({'check':name,'pass':bool(ok),'detail':detail})
ck('frozenBeforeAuthorship',p['frozenAt']<a['createdAt']);ck('3FrozenUrlsPreserved',[x['url'] for x in a['articles']]==[x['url'] for x in p['pages']]);ck('14_22_31',[len(read(O/'plan/membership.json')[x]) for x in ['legalUnits','administrativeUnits','relations']]==[14,22,31]);ck('all12Candidates',len(read(O/'plan/candidate-ledger.json')['groups'])==12)
for q in p['facilityAnchors']:ck('noAdminInference:'+q['id'],q['administrativeDong'] is None)
cc=c['common'];ck('3realCards',len(cc['articleCards'])==3 and len(set(x['href'] for x in cc['articleCards']))==3)
for card,prod in zip(cc['productCards'],cat['products']):
 ck('product:'+prod['sku'],card['sku']==prod['sku'] and card['name']==prod['name'] and card['basicPriceKRW']==prod['priceKRW'] and card['cta']['href']==prod['source']['url'] and card['imageSha256']==prod['photo']['sha256'])
 img=O/'handoff/assets/products'/f"{prod['sku']}.jpg";ck('image:'+prod['sku'],sha(img)==prod['photo']['sha256'] and Image.open(img).size==(500,500))
counts=[];corpora={}
for art in a['articles']:
 texts=[art['firstAnswer']]+[para for s in art['sections'] for para in s['paragraphs']]
 body='\n'.join(texts);corpora[art['id']]=body;freq=Counter(texts)
 counts.append({'id':art['id'],'uniqueBodyChars':len(body),'bodyNoWhitespaceChars':len(re.sub(r'\s','',body)),'faqChars':sum(len(f['question'])+len(f['answer']) for f in art['faq']),'target2500to3000':2500<=len(body)<=3000,'hardGate':False,'repeatedParagraphs':[t for t,n in freq.items() if n>1]})
 ck('noExactRepeatedParagraph:'+art['id'],len(texts)==len(set(texts)))
 ck('productCardsMatch:'+art['id'],[sku for sec in art['sections'] for sku in sec.get('productCardSkus',[])]==art['productSkus'])
 ck('anchorsPresent:'+art['id'],all(x in [s['id'] for s in art['sections']] for x in art['facilityAnchors']))
 ck('evidenceResolved:'+art['id'],all(e in reg for s in art['sections'] for e in s['evidence']))
 ck('FAQNotEmpty:'+art['id'],all(f.get('question') and f.get('answer') for f in art['faq']))
 for bad in ['하시기 바랍니다','무료배송','정시 도착','100%','3시간 내','24시간 상담','146-92','146-2']:
  ck('forbidden:'+art['id']+':'+bad,bad not in body)
 ck('noRegionSwap:'+art['id'],not any(s in body for s in ['서초구','관악구','서울성모','엘타워','aT센터']))
 ck('relatedTarget:'+art['id'],art['relatedLink']['href'] in [x['url'] for x in p['pages']] and art['relatedLink']['href']!=art['url'])
# shared-region comparisons measure unique bodies only, exclude exact common product cards/UI
others={x['id']:'\n'.join([x['firstAnswer']]+[z for s in x['sections'] for z in s['paragraphs']]) for x in read(S/'copy/article-copy.rev4.json')['articles']}
def grams(s,n=30):s=re.sub(r'\s+',' ',s);return {s[i:i+n] for i in range(max(0,len(s)-n+1))}
def compare(x,y):
 g,h=grams(x),grams(y);m=difflib.SequenceMatcher(None,x,y,autojunk=False).find_longest_match(0,len(x),0,len(y));return {'30charGramJaccard':len(g&h)/max(1,len(g|h)),'longestExactRunChars':m.size,'longestRun':x[m.a:m.a+m.size],'exactParagraphOverlap':sorted(set(x.splitlines())&set(y.splitlines()))}
comparison={'method':'Whitespace-normalized 30-character ngrams and longest exact run, exact paragraph overlap. Mechanical diagnostics only; human review decides facility/intent template duplication. Common cards/banners/UI deliberately excluded.','withinGangnam':[{'a':x,'b':y,**compare(corpora[x],corpora[y])} for x,y in itertools.combinations(corpora,2)],'seocho':[{'gangnam':x,'seocho':y,**compare(corpora[x],others[y])} for x in corpora for y in others]}
# scan original competitor corpus sentence overlap without republishing full originals
comp=[]
for f in (R/'purchase/raw').glob('*.txt'):
 for key,text in corpora.items():
  cmp=compare(text,f.read_text());
  if cmp['longestExactRunChars']>=35:comp.append({'article':key,'sourceFile':str(f),'longestExactRunChars':cmp['longestExactRunChars'],'longestRun':cmp['longestRun']})
comparison['competitorMatchesAtLeast35Chars']=comp
for banner in read(R/'reuse/shared-banner-manifest.json'):
 f=O/'handoff/assets/banners'/f"{banner['name']}.webp";ck('banner:'+banner['name'],sha(f)==banner['sha256'] and Image.open(f).size==(1774,887))
write(O/'validation/counts.json',counts);write(O/'validation/duplicate-comparison.json',comparison);write(O/'validation/copy-validation.json',{'status':'PASS' if all(x['pass'] for x in checks) else 'FAIL','scope':'Data/files only; no build/HTML/browser/public verification. Human full-text review required.','checks':checks,'failures':[x for x in checks if not x['pass']],'inputHashes':{'articles':sha(O/'copy/article-copy.final.json'),'common':sha(O/'copy/common-visible-copy.final.json'),'plan':sha(O/'plan/fixed-plan.json')}})
print(json.dumps({'counts':counts,'checks':len(checks),'failures':[x for x in checks if not x['pass']]},ensure_ascii=False,indent=2))
