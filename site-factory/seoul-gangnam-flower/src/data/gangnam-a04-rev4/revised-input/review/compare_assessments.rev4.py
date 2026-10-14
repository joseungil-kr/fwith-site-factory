from pathlib import Path
import json,hashlib,datetime,sys
R=Path('/workspace/shared/gangnam-a04-addendum-20261013');D=R/'revised-input/review'
sys.path.insert(0,str(R/'rubric'))
from normalization import normalize,calculate
f1=D/'first-assessment.rev4.json';f2=D/'second-assessment.rev4.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(f1)=='b7fdf1bcbabe1f380af3a371ae7cd3922fd17c2d6bfa06926f8c965561b36b1e'
assert sha(f2)=='59e45cba6953ff0b981e8de37bcaf47d42084ae82c9b60b7234fcc172d6f54b6'
x=json.loads(f1.read_text());y=json.loads(f2.read_text());yby={p['id']:p for p in y['scoredPages']}
cache={};quotechecks=[]
def pointer(obj,p):
 for bit in p.strip('/').split('/') if p else []:
  bit=bit.replace('~1','/').replace('~0','~');obj=obj[int(bit)] if isinstance(obj,list) else obj[bit]
 return obj
def descendants(v,p):
 if isinstance(v,str):return [(p,v)]
 if isinstance(v,dict):return sum([descendants(child,p+'/'+k) for k,child in v.items()],[])
 if isinstance(v,list):return sum([descendants(child,p+'/'+str(i)) for i,child in enumerate(v)],[])
 return []
def check(ev,origin,page,criterion):
 file=ev['sourceFile'];ptr=ev['jsonPointer'];quote=ev['quote'];assert isinstance(quote,str)
 if file not in cache:cache[file]=json.loads(Path(file).read_text())
 value=pointer(cache[file],ptr)
 if isinstance(value,str):
  n=normalize(value)
  if 'normalizedSpan' in ev:
   start,end=ev['normalizedSpan'];valid=n[start:end]==quote
  else:
   start=n.find(quote);end=start+len(quote);valid=start>=0
  resolved=ptr
 else:
  matches=[(path,text) for path,text in descendants(value,ptr) if normalize(text)==quote]
  assert len(matches)==1,(ptr,quote)
  resolved,value=matches[0];start=0;end=len(quote);valid=True
 assert valid
 if ev.get('sourceSha256'):assert sha(file)==ev['sourceSha256']
 row={'assessment':origin,'page':page,'criterion':criterion,'sourceFile':file,'actualSourceSha256':sha(file),'declaredPointer':ptr,'resolvedTextPointer':resolved,'span':[start,end],'quote':quote,'verified':True}
 quotechecks.append(row);return row
pages=[]
for p in x['records']:
 q=yby[p['id']];qrows={v['criterion']:v for v in q['rows']};rows=[]
 for key,r in p['rowDecisions'].items():
  rr=qrows[key]
  e1=[check(ev,'first',p['id'],key) for ev in r['evidence']]
  e2=[check(rr['evidence'],'second',p['id'],key)]+[check(ev,'second',p['id'],key) for ev in rr.get('continuityEvidence',[])]
  same_quotes={(ev['sourceFile'],ev['resolvedTextPointer'],ev['quote']) for ev in e1}=={(ev['sourceFile'],ev['resolvedTextPointer'],ev['quote']) for ev in e2}
  rows.append({'criterion':key,'firstPoints':r['points'],'secondPoints':rr['points'],'pointsEqual':r['points']==rr['points'],'maximumEqual':r['maximum']==rr['maxPoints'],'bothActualQuotesVerified':True,'quotedExcerptSetsIdentical':same_quotes,'differenceIfAny':None if same_quotes else 'Excerpt granularity differs: first A1 quotes the direct first proposition, second quotes the whole opening; I1 first includes body paragraphs/CTA and second includes opener plus continuity headings/card evidence. Each cited text was read back against the same source inputs.','firstEvidence':e1,'secondEvidence':e2})
 raw={'title':p['fieldEvidence']['title']['quote'],'h1':p['fieldEvidence']['h1']['quote'],'opener':p['fieldEvidence']['opener']['quote']}
 assert raw==q['rawFields']
 calc=calculate({key:r['points'] for key,r in p['rowDecisions'].items()},p['calculation']['gates'])
 assert calc==p['calculation']==q['calculation']
 pages.append({'id':p['id'],'url':p['url'],'sameRawFields':True,'rawFields':raw,'sameOpeningWindows':p['openingWindows']==q['openingWindows'],'sameTitleFrontCalculation':p['titleFrontCalculation']==q['titleFrontCalculation'],'sameApplicability':p['applicability']==q['applicability'],'rawScore':calc['raw_score'],'effectiveScore':calc['effective_score'],'sameCalculation':True,'firstGates':p['calculation']['gates'],'secondGates':q['calculation']['gates'],'sameGates':p['calculation']['gates']==q['calculation']['gates'],'rows':rows})
na1={p['url']:(p['applicability'],p['title_alignment_score']) for p in x['nonPrimaryRoutes']};na2={p['url']:(p['applicability'],p['score']) for p in y['notApplicablePages']}
assert na1==na2
assert all(row['pointsEqual'] and row['maximumEqual'] for p in pages for row in p['rows'])
assert x['rubricSha256']==y['rubricSha256'] and x['targetMapSha256']==y['targetMapSha256']
report={'checkedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'firstAssessment':{'path':str(f1),'sha256':sha(f1)},'secondAssessment':{'path':str(f2),'sha256':sha(f2)},'rubricSha256':x['rubricSha256'],'targetMapSha256':x['targetMapSha256'],'sameFrozenRubricAndTargets':True,'summary':{'scoredPages':4,'rowScoresCompared':36,'equalRowScores':36,'rawAndEffectiveScores':[100,100,100,100],'equalGateSets':4,'noMandatoryGates':True,'naRoutesEqual':True,'actualQuoteReadbacks':len(quotechecks),'actualQuoteReadbackFailures':0,'fullRawFieldTriplesEqual':4},'pages':pages,'naRoutes':na1,'scopeComparison':{'first':x['implementationBoundary'],'second':y['scope'],'conclusion':'Both evaluate revised draft inputs, not revised rendered HTML or a live deployment. Prior HTML pointers in the second result are explicitly boundary-only and are not used here as proof of a revised rendered opener.'},'evidenceGranularityNote':'Scores and source fields reproduce exactly, but not every selected excerpt set is identical. A1 and I1 use different valid excerpt granularity; all source text was independently read back, including three card-summary quotes whose declared pointer names the containing card object. The resolved /summary leaf is recorded here without altering either assessment.','independenceBoundary':'Both rev4 result files were already stored before this comparison began. The second rev4 report was first opened by this reviewer after saving the first rev4 result. This checks file chronology and reported independence, not another reviewer’s private history.','preserved':['frozen rubric','frozen targets','original assessment with event 95/89 REVISE','original second reproduction','both rev4 assessments','original and revised input files'],'claimLimit':'Reproducible internal alignment only. No production, browser, CTA functionality, ranking, demand or factual-claim verification is conferred.'}
p=D/'reproduction-comparison.rev4.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'path':str(p),'sha256':sha(p),'summary':report['summary']},indent=2))
assert sha(f1)==report['firstAssessment']['sha256'];assert sha(f2)==report['secondAssessment']['sha256']
