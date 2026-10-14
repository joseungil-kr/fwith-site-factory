from pathlib import Path
import json,hashlib,sys,datetime
O=Path(__file__).parent;B=Path('/workspace/shared/gangnam-plan-copy-20261013');R=O/'revised-input';sys.path.insert(0,str(O/'rubric'))
from normalization import normalize,calculate,opening_windows
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
checks=[]
def ck(name,ok,details=None):checks.append({'check':name,'ok':bool(ok),'details':details})
def ptr(obj,p):
 for k in p.lstrip('/').split('/') if p else []:obj=obj[int(k)] if isinstance(obj,list) else obj[k.replace('~1','/').replace('~0','~')]
 return obj
def walk(x,path=''):
 yield path,x
 if isinstance(x,dict):
  for k,v in x.items():yield from walk(v,path+'/'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):yield from walk(v,path+'/'+str(i))
def diffs(a,b,p=''):
 if type(a)!=type(b):return [(p,a,b)]
 if isinstance(a,dict):return sum((diffs(a.get(k),b.get(k),p+'/'+k) for k in sorted(set(a)|set(b))),[])
 if isinstance(a,list):
  if len(a)!=len(b):return [(p,a,b)]
  return sum((diffs(u,v,p+'/'+str(i)) for i,(u,v) in enumerate(zip(a,b))),[])
 return [] if a==b else [(p,a,b)]
manifest=read(B/'delivery-manifest.json')
for q in manifest['files']:ck('immutable-original:'+q['path'],sha(B/q['path'])==q['sha256'])
baseline=read(O/'evidence/immutable-input-baseline.json')
ck('original-manifest',sha(B/'delivery-manifest.json')==baseline['deliveryManifestSha256'])
for q in baseline['implementationReadOnlyFiles']:ck('untouched-source:'+q['path'],sha(Path(q['path']))==q['sha256'])
ck('frozen-rubric',sha(O/'rubric/A04_RUBRIC_v1.md')=='bbc7d957dc1336a555ecc5a3775b326ec0d0b1bc8d70336ac9d040314941c5fa')
ck('frozen-target',sha(O/'assessment/targets.frozen.json')=='4611ebfbf5515a22dc264e3b2b9a86a23f75caec615d0e1bcf6e5fba324b5f8e')
for fp in ['assessment/a04-independent-assessment.v1.json','independent-review/independent-assessment.json','revised-input/review/first-assessment.rev4.json','revised-input/review/second-assessment.rev4.json']:
 a=read(O/fp);records=a.get('records',a.get('scoredPages'))
 for r in records:
  rows={k:v['points'] for k,v in r['rowDecisions'].items()} if 'rowDecisions' in r else {v['criterion']:v['points'] for v in r['rows']}
  ck(fp+':recalculate:'+r['id'],calculate(rows,r['calculation']['gates'])==r['calculation'])
 for p,v in walk(a):
  if isinstance(v,dict) and all(k in v for k in ['sourceFile','sourceSha256','jsonPointer','quote','normalizedSpan']):
   source=Path(v['sourceFile']);q=ptr(read(source),v['jsonPointer']);span=v['normalizedSpan'];ck(fp+':quote'+p,sha(source)==v['sourceSha256'] and normalize(q)[span[0]:span[1]]==v['quote'])
for first,second in [('assessment/a04-independent-assessment.v1.json','independent-review/independent-assessment.json'),('revised-input/review/first-assessment.rev4.json','revised-input/review/second-assessment.rev4.json')]:
 a=read(O/first);b=read(O/second)
 for r,s in zip(a['records'],b['scoredPages']):
  ck(first+':independent-match:'+r['id'],r['id']==s['id'] and r['calculation']==s['calculation'] and {k:v['points'] for k,v in r['rowDecisions'].items()}=={v['criterion']:v['points'] for v in s['rows']})
old=read(B/'copy/article-copy.final.json');new=read(R/'copy/article-copy.rev4.json');runtime=read(R/'handoff/runtime-input.rev4.json');rtold=read(B/'handoff/runtime-input.json')
d=diffs(old['articles'],new['articles']);expected={'/2/firstAnswer','/2/uniqueBodyCharsIncludingFirstAnswer','/2/bodyAndFaqChars'};ck('exact-article-diff',set(q[0] for q in d)==expected,d)
ck('runtime-article-projection',runtime['articles']==new['articles'])
for k in ['common','directory','assets','expectedPaths','publication','region','originalPlanN','visibilityContract']:ck('runtime-unchanged:'+k,runtime[k]==rtold[k])
oldtxt=(B/'copy/article-copy.final.txt').read_text();newtxt=(R/'copy/article-copy.rev4.txt').read_text();ck('exact-text-projection',newtxt==oldtxt.replace(old['articles'][2]['firstAnswer'],new['articles'][2]['firstAnswer']))
for fp in ['mapping/keyword-mapping.metadata-refined.json','mapping/keyword-mapping.original-assessed.json','mapping/keyword-mapping.rev4.final.json']:
 a=read(O/fp)
 for p,v in walk(a):
  if isinstance(v,dict):
   for pk,hk in [('file','sha256'),('sourceFile','sourceSha256'),('rawFile','rawSha256')]:
    if pk in v and hk in v and isinstance(v[pk],str) and v[pk].startswith('/'):
     ck(fp+':hash'+p+'/'+pk,sha(Path(v[pk]))==v[hk])
   if 'file' in v and 'jsonPointer' in v and v['jsonPointer'] is not None and str(v['file']).endswith('.json'):
    try:ptr(read(Path(v['file'])),v['jsonPointer']);ok=True
    except Exception as e:ok=False
    ck(fp+':pointer'+p,ok)
 for i,rec in enumerate(a['records']):
  ev=rec['actualTextEvidence'];src=read(Path(ev['sourceFile']))
  for k in ['title','h1','firstAnswer']:ck(fp+':actual-text:'+rec['id']+':'+k,ptr(src,ev[k]['jsonPointer'])==ev[k]['text'])
  for ev in rec['query_evidence']:
   if ev['type']=='observed-query':
    v=ev['value'];saved=ptr(read(Path(v['sourceFile'])),v['jsonPointer']);ck(fp+':saved-query:'+v['queryId'],saved['id']==v['queryId'] and saved['query']==v['exactQuery'])
  for k in ['primary_keyword','secondary_keywords','keyword_cluster','query_class','query_priority']:ck(fp+':target-unchanged:'+rec['id']+':'+k,rec[k]==read(O/'mapping/keyword-mapping.draft.json')['records'][i][k])
result={'checkedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':'직접 확인: supplement owner reopened local files and independently recalculated/reference-checked reviewer output','checkCount':len(checks),'passed':sum(x['ok'] for x in checks),'failed':sum(not x['ok'] for x in checks),'checks':checks,'boundary':'Hash/quote/projection/arithmetic checks are not independent semantic grading or actual browser/public deployment verification. Numeric grades are separately provided by two reviewers.'}
(O/'evidence/owner-readback-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False,indent=2));print('FAILURES',json.dumps([x for x in checks if not x['ok']],ensure_ascii=False))
if result['failed']:raise SystemExit(1)
