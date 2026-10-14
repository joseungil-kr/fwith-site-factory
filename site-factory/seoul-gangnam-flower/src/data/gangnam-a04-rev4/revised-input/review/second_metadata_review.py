#!/usr/bin/env python3
"""Independent source/pointer/value readback; never writes reviewed inputs."""
import json, pathlib, hashlib, datetime, html, re, unicodedata
B=pathlib.Path('/workspace/shared/gangnam-a04-addendum-20261013')
O=B/'revised-input/review'
checks=[]; bindings=[]
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(pathlib.Path(p).read_text())
def test(name, ok, detail=None): checks.append({'check':name,'pass':bool(ok),'detail':detail})
def norm(t): return re.sub(r'\s+', ' ',unicodedata.normalize('NFC',html.unescape(t))).strip()
def ptr(x,p):
 for c in p.lstrip('/').split('/') if p else []:
  c=c.replace('~1','/').replace('~0','~');x=x[int(c)] if isinstance(x,list) else x[c]
 return x
expected={
 'mapping/keyword-mapping.draft.json':'ba60da475ed97875da868fa0f3d656edd94fddedefdad485307fd6bd4d9ac637',
 'mapping/keyword-mapping.metadata-refined.json':'41c1cbafeae08c228b4c46060ba45f0c607feb8f28f2dc87a9b2923d2a8c6bf9',
 'mapping/keyword-mapping.rev4.final.json':'fd4f54ac139055fabe6694c316286afcb7b22792cb77133cf8c56f54b9f0c5e4',
 'mapping/keyword-mapping.original-assessed.json':'bb69d4676fbed539a168358b30404fea4e62a58878d1341134e4f1786fdd3fc3',
 'revised-input/copy/claim-evidence-addendum.rev4.json':'1454b0dabd1bc3805e8ad0c1f4fde7837ba7cea0a8308772ec7bdd522619dd0d',
 'revised-input/review/first-assessment.rev4.json':'b7fdf1bcbabe1f380af3a371ae7cd3922fd17c2d6bfa06926f8c965561b36b1e',
 'revised-input/review/second-assessment.rev4.json':'59e45cba6953ff0b981e8de37bcaf47d42084ae82c9b60b7234fcc172d6f54b6',
 'rubric/A04_RUBRIC_v1.md':'bbc7d957dc1336a555ecc5a3775b326ec0d0b1bc8d70336ac9d040314941c5fa',
 'assessment/targets.frozen.json':'4611ebfbf5515a22dc264e3b2b9a86a23f75caec615d0e1bcf6e5fba324b5f8e',
 'revised-input/copy/article-copy.rev4.json':'ca721a7a712c7814b21599d7a16d49e9476465527213c8496a1c2d2bb61b3e0f',
 'revised-input/review/second-exact-copy-review.rev4.json':'aeff41475f5872e9e1c2072bbafe908080f3aa9d848e0e2c54ffb776bd889463',
}
for p,h in expected.items():test('pinned hash '+p,sha(B/p)==h)
D=read(B/'mapping/keyword-mapping.draft.json');M=read(B/'mapping/keyword-mapping.metadata-refined.json');F=read(B/'mapping/keyword-mapping.rev4.final.json');G=read(B/'mapping/keyword-mapping.original-assessed.json');T=read(B/'assessment/targets.frozen.json');C=read(B/'revised-input/copy/claim-evidence-addendum.rev4.json');A=read(B/'revised-input/review/first-assessment.rev4.json');S=read(B/'revised-input/review/second-assessment.rev4.json')

def references(x,loc):
 if isinstance(x,dict):
  pairs=[('file','sha256'),('sourceFile','sourceSha256'),('rawFile','rawSha256')]
  for fk,hk in pairs:
   if fk in x and hk in x and isinstance(x[fk],str) and x[fk].startswith('/workspace/'):
    p=pathlib.Path(x[fk]);test(loc+' reference exists '+fk,p.is_file())
    if not p.is_file():continue
    actual=sha(p);test(loc+' reference SHA '+fk,actual==x[hk]);bindings.append({'path':str(p),'sha256':actual})
    if x.get('jsonPointer') is not None and fk in ['file','sourceFile']:
     try:v=ptr(read(p),x['jsonPointer']); test(loc+' JSON pointer exists',True)
     except Exception as e:test(loc+' JSON pointer exists',False,str(e));continue
     for k in ['text','exactQuery']:
      if k in x and isinstance(v,str):test(loc+' pointer '+k,v==x[k])
     if isinstance(v,str) and 'quote' in x:
      n=norm(v);sp=x.get('normalizedSpan');test(loc+' quote at normalized span',n[slice(*sp)]==x['quote'] if sp else x['quote'] in n)
     if 'exactQuery' in x and isinstance(v,dict):test(loc+' exact query entry',x['exactQuery']==v.get('query',v.get('exactQuery')))
    if 'lines' in x:
     lines=p.read_text().splitlines();lo,hi=x['lines'];test(loc+' line range',1<=lo<=hi<=len(lines));bindings[-1]['citedLines']=lines[lo-1:hi]
    if 'exactQuote' in x and 'line' in x:
     line=p.read_text().splitlines()[x['line']-1];test(loc+' exact original line quote',line==x['exactQuote'],{'actual':line})
  for k,v in x.items():references(v,loc+'/'+str(k))
 elif isinstance(x,list):
  for i,v in enumerate(x):references(v,loc+'/'+str(i))
for name,x in [('refined',M),('final',F),('original-assessed',G),('claim',C)]:references(x,name)

stable=['id','url','primary_keyword','primary_keyword_origin','secondary_keywords','secondary_keyword_support','keyword_cluster','keyword_cluster_origin','query_class','query_priority','title_alignment_score','title_alignment_status','actualTextEvidence','countsTowardFrozenArticleN','frozenPageDenominator']
for i,(d,m,t) in enumerate(zip(D['records'],M['records'],T['records'])):
 for k in stable:test(f'{d["id"]} refinement leaves {k}',d[k]==m[k])
 for k,v in d['query_priority_semantics'].items():test(f'{d["id"]} priority meaning {k} unchanged',m['query_priority_semantics'][k]==v)
 for k,v in m['keyword_cluster_definition'].items():
  if k!='source':test(f'{d["id"]} frozen cluster target {k}',v==t['evaluationTarget'][k])
 test(f'{d["id"]} alias contract unchanged',t['evaluationTarget']['lexicalAliases']==[])
 test(f'{d["id"]} intermediate score is null',m['title_alignment_score'] is None)
 if i:
  origin=m['query_class_origin'];test(f'{d["id"]} query class exact value',ptr(read(origin['source']['file']),origin['source']['jsonPointer'])==m['query_class']==origin['value'])
 else:
  ed=next(e for e in m['query_evidence'] if e['type']=='accepted-intent-decision')
  test('home accepted intent source corrected',ed['file'].endswith('/common-visible-copy.final.json') and ed['jsonPointer']=='/common/home')
 for e in m['query_evidence']:
  if e['type']=='official-facility-evidence':
   origin=e['factsOrigin'];v=ptr(read(origin['file']),origin['jsonPointer'])
   if i!=3:test(f'{d["id"]} facility facts exact prior proposal',e['facts']==v)
   else:
    test('event fact[1] unchanged',e['facts'][1]==v[1]);test('event fact scope/source unchanged',e['facts'][0]['scope']==v[0]['scope'] and e['facts'][0]['sources']==v[0]['sources'])
    clarification=ptr(read(e['dateClarification']['file']),e['dateClarification']['jsonPointer'])
    test('Coex clarification is original final distinction',bool(clarification));test('Coex metadata no false edition', '2026.03' not in e['facts'][0]['fact'])

comparison=[]
for i,(a,s) in enumerate(zip(A['records'],S['scoredPages'])):
 test(f'rev4 {i} same assessed ID',a['id']==s['id']);rows={r['criterion']:r['points'] for r in s['rows']};arows={k:r['points'] for k,r in a['rowDecisions'].items()}
 test(f'rev4 {i} all nine rows agree',rows==arows and len(rows)==9)
 test(f'rev4 {i} calculation agrees',a['calculation']==s['calculation'])
 test(f'rev4 {i} independent subtotal',sum(rows.values())==s['calculation']['raw_score'])
 test(f'rev4 {i} effective score and no gate',s['calculation']['effective_score']==100 and s['calculation']['gates']==[])
 comparison.append({'id':a['id'],'firstRows':arows,'secondRows':rows,'firstCalculation':a['calculation'],'secondCalculation':s['calculation']})
 for mapping,rev in [(F,4),(G,3)]:
  r=mapping['records'][i];test(f'map rev{rev} {i} mandatory fields',all(k in r and r[k] is not None for k in ['primary_keyword','secondary_keywords','keyword_cluster','query_class','query_priority','query_evidence','title_alignment_score']))
  for k in ['id','url','primary_keyword','secondary_keywords','keyword_cluster','query_class','query_priority','countsTowardFrozenArticleN','frozenPageDenominator']:
   test(f'map rev{rev} {i} frozen {k}',r[k]==M['records'][i][k])
  ev=r['actualTextEvidence'];source=read(ev['sourceFile'])
  for k in ['title','h1','firstAnswer']:test(f'map rev{rev} {i} exact source {k}',ptr(source,ev[k]['jsonPointer'])==ev[k]['text'])
  op=ev['firstAnswer'];test(f'map rev{rev} {i} opener count',len(op['text'])==op['charactersIncludingSpaces']);test(f'map rev{rev} {i} opener180',op['text'][:180]==op['first180Characters'])
  provenance=r['alignment_provenance']
  for n in ['independentAssessment','independentReproduction']:
   z=provenance[n];rec=ptr(read(z['file']),z['jsonPointer']);test(f'map rev{rev} {i} evaluator identity {n}',rec['id']==r['id']);test(f'map rev{rev} {i} evaluator score {n}',rec['calculation']['effective_score']==r['title_alignment_score']);test(f'map rev{rev} {i} evaluator raw {n}',rec['calculation']['raw_score']==r['title_alignment_raw_score']);test(f'map rev{rev} {i} evaluator gates {n}',rec['calculation']['gates']==r['title_alignment_gates'])
 test(f'rev4 {i} actual aligned text matches own assessment',F['records'][i]['actualTextEvidence']['title']['text']==s['rawFields']['title'] and F['records'][i]['actualTextEvidence']['h1']['text']==s['rawFields']['h1'] and F['records'][i]['actualTextEvidence']['firstAnswer']['text']==s['rawFields']['opener'])

test('original event REVISE retained',G['records'][3]['title_alignment_score']==89 and G['records'][3]['title_alignment_raw_score']==95 and G['records'][3]['title_alignment_gates']==['G4'])
for name,m in [('final',F),('original',G)]:
 test(name+' N3 invariant',sum(r['countsTowardFrozenArticleN'] for r in m['records'])==3)
 test(name+' nonprimary roles explicit NA',[(r['id'],r['applicability'],r['title_alignment_score']) for r in m['nonPrimaryRoutes']]==[('directory','NOT_APPLICABLE',None),('notFound','NOT_APPLICABLE',None)])
claimArticle=read(C['articleInput']['file']);test('claim exact changed firstAnswer',ptr(claimArticle,C['jsonPointer'])==C['exactFirstAnswer']);test('claim prefix exactly at start',C['exactFirstAnswer'].startswith(C['newPhrase']));test('claim exact frozen regional target',ptr(read(C['frozenTarget']['file']),C['frozenTarget']['jsonPointer'])['region']=='강남구')
test('claim only relevant cached venues',[(e['id']) for e in C['regionalEvidence']]==['coex-navigation','setec-parking'])
test('both quoted source addresses name Gangnam',all('강남구' in e['exactQuote'] for e in C['regionalEvidence']))

# Actual local site boundary: new changed opener is NOT claimed as currently emitted.
orig=read('/workspace/shared/gangnam-plan-copy-20261013/copy/article-copy.final.json')['articles'][2]['firstAnswer'];new=claimArticle['articles'][2]['firstAnswer']
page=pathlib.Path('/workspace/shared/gangnam-factory/site-factory/seoul-gangnam-flower/dist/regions/gangnam-event-wreath/index.html')
htmltext=html.unescape(page.read_text());test('existing HTML still contains original opener',orig in htmltext);test('existing HTML does not contain revised opener',new not in htmltext)

report={
 'reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reviewer':'independent input/copy auditor',
 'scope':'Second independent metadata provenance and final mapping readback, after own rev4 assessment was saved; draft input only, no rendered revision4 claim.',
 'inputs':[{'file':str(B/p),'sha256':sha(B/p)} for p in expected],
 'judgment':{'metadataProvenance':'PASS: precise source pointers now match existing home/plan/frozen targets; original draft is preserved as history.', 'mapping':'PASS: mandatory explicit A04 fields with labeled newly derived classifications; exact rev4 text and both assessment SHA/score/row results bound.', 'claim':'PASS: the changed region phrase restates the frozen scope and two cached official venue addresses; no new facility reception or delivery policy is established.', 'language':'Minimal region-attributive phrase remains natural provider consultation copy. Product/price/policy/conditions unchanged, supported separately by exact-copy review.', 'production':'NOT_ASSESSED: four 100 internal alignment results do not establish production readiness, public HTTP, actual revised HTML, browser output or search performance.'},
 'comparison':comparison,
 'independence':{'secondStoredAt':S['reviewedAt'],'firstStoredAt':A['createdAtUtc'],'secondResultStoredBeforeFirstWasOpened':True,'otherEvaluatorPermittedAfterStorage':'worker message supplied first-assessment SHA after own immutable result had been saved','priorCopyFamiliarityDisclosed':True},
 'checks':checks,'totals':{'checks':len(checks),'passed':sum(c['pass'] for c in checks),'failed':sum(not c['pass'] for c in checks)},
 'resolvedReferenceCount':len(bindings),'uniqueReferenceFiles':sorted({x['path'] for x in bindings}),
 'oldHTMLBoundary':{'file':str(page),'sha256':sha(page),'revisedOpenerRendered':False},
 'toolsReportedOnly':['Other review initial creation/blindness chronology is recorded as disclosed provenance, not independent proof of reviewer cognition.'],
 'unverified':['New revision4 rendered output, browser appearance, live/public responses, SEO outcomes and broad production gate.'],
 'noWritesToReviewedInputs':True,
}
output=O/'second-metadata-review.rev4.json';output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'file':str(output),'sha256':sha(output),'totals':report['totals'],'failed':[c for c in checks if not c['pass']]},ensure_ascii=False,indent=2))
raise SystemExit(bool(report['totals']['failed']))
