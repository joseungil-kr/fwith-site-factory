from pathlib import Path
from hashlib import sha256
from difflib import SequenceMatcher
import itertools,json,re,datetime
B=Path('/workspace/shared/gangnam-plan-copy-20261013'); D=B/'independent-copy-review'; S=D/'reviewed-inputs.rev3'
a=json.loads((S/'copy/article-copy.final.json').read_text())
c=json.loads((S/'copy/common-visible-copy.final.json').read_text())
text=(S/'copy/article-copy.final.txt').read_text()
mat=json.loads((S/'copy/intent-completion-matrix.json').read_text())
claims=json.loads((S/'copy/claim-evidence-map.json').read_text())
seo=Path('/workspace/shared/seocho-plan-copy-20261013/copy/article-copy.rev4.json'); sx=json.loads(seo.read_text())
def body(x): return '\n'.join([x['firstAnswer']]+[p for s in x['sections'] for p in s['paragraphs']])
def norm(t): return re.sub(r'\s+',' ',t).strip()
def cmp(x,y):
 tx,ty=norm(body(x)),norm(body(y)); nx={tx[i:i+30] for i in range(len(tx)-29)};ny={ty[i:i+30] for i in range(len(ty)-29)}
 z=SequenceMatcher(None,tx,ty,autojunk=False).find_longest_match(0,len(tx),0,len(ty))
 ps=lambda q:[p for s in q['sections'] for p in s['paragraphs']]
 return {'a':x['id'],'b':y['id'],'char30GramJaccard':len(nx&ny)/len(nx|ny),'longestExactRunChars':z.size,'longestExactRun':tx[z.a:z.a+z.size],'exactParagraphOverlap':sorted(set(ps(x))&set(ps(y)))}
checks={'reviewedRevision':a['revision'],'frozenPlanSha256':sha256((S/'plan/fixed-plan.json').read_bytes()).hexdigest(),'counts':[], 'claimMapExactParagraphMismatches':[], 'intentMatrixNonexactAnswers':[], 'textProjectionMissingStrings':[],'withinGangnam':[],'seocho':[]}
arts={x['id']:x for x in a['articles']}
for x in a['articles']:
 ps=[p for s in x['sections'] for p in s['paragraphs']]; uniq=''.join([x['firstAnswer']]+ps)
 checks['counts'].append({'id':x['id'],'bodyCharsWithoutSeparators':len(uniq),'noWhitespaceChars':len(re.sub(r'\s','',uniq)),'bodyCharsWithParagraphSeparators':len(body(x)),'authorCount':x['uniqueBodyCharsIncludingFirstAnswer'],'countMatches':len(body(x))==x['uniqueBodyCharsIncludingFirstAnswer'],'sections':len(x['sections']),'paragraphs':len(ps),'faqCount':len(x['faq'])})
 for st in [x[k] for k in ['title','h1','metaDescription','cardSummary','firstAnswer','sourceNote']]+ps+[s['heading'] for s in x['sections']]:
  if st not in text:checks['textProjectionMissingStrings'].append({'article':x['id'],'text':st})
 for y in sx['articles']: checks['seocho'].append(cmp(x,y))
for x,y in itertools.combinations(a['articles'],2): checks['withinGangnam'].append(cmp(x,y))
for q in claims:
 sec=next(s for s in arts[q['article']]['sections'] if s['id']==q['sectionId'])
 if sec['paragraphs']!=q['exactParagraphs']:checks['claimMapExactParagraphMismatches'].append([q['article'],q['sectionId']])
for q in mat:
 ps=[p for s in arts[q['article']]['sections'] for p in s['paragraphs']]
 for p in q['answer']:
  if p not in ps:checks['intentMatrixNonexactAnswers'].append({'article':q['article'],'question':q['question'],'answer':p})
inputs=[]
for p in [S/'copy/article-copy.final.json',S/'copy/article-copy.final.txt',S/'copy/common-visible-copy.final.json',S/'plan/fixed-plan.json',S/'copy/intent-completion-matrix.json',S/'copy/claim-evidence-map.json',S/'validation/duplicate-comparison.json',S/'copy/review-input-manifest.rev3.json',seo,seo.with_suffix('.txt'),Path('/workspace/shared/gangnam-research-20261013/repo/SALES_COPY_ACCEPTANCE.md'),Path('/workspace/shared/gangnam-research-20261013/repo/SEARCH_CONTENT_STRATEGY.md')]:
 inputs.append({'path':str(p),'sha256':sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
checks['inputHashes']=inputs
(D/'independent-checks.rev3.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in checks.items() if k not in ['inputHashes','seocho','withinGangnam']},ensure_ascii=False,indent=2))
