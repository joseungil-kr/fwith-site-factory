from pathlib import Path
from html.parser import HTMLParser
import json,hashlib,datetime,sys,importlib.util
P=Path('/workspace/shared/gangnam-a04-addendum-20261013');O=P/'independent-review';B=Path('/workspace/shared/gangnam-plan-copy-20261013');SITE=Path('/workspace/shared/gangnam-factory/site-factory/seoul-gangnam-flower')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P/'rubric/A04_RUBRIC_v1.md')=='bbc7d957dc1336a555ecc5a3775b326ec0d0b1bc8d70336ac9d040314941c5fa'
assert sha(P/'assessment/targets.frozen.json')=='4611ebfbf5515a22dc264e3b2b9a86a23f75caec615d0e1bcf6e5fba324b5f8e'
sys.dont_write_bytecode=True
sp=importlib.util.spec_from_file_location('frozen_a04_normalization',P/'rubric/normalization.py');mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
N=mod.normalize
T=json.loads((P/'assessment/targets.frozen.json').read_text());M=json.loads((P/'mapping/keyword-mapping.draft.json').read_text());A=json.loads((B/'copy/article-copy.final.json').read_text());C=json.loads((B/'copy/common-visible-copy.final.json').read_text())['common'];F=json.loads((B/'plan/fixed-plan.json').read_text());R=json.loads((P/'evidence/rendered-text-bindings.json').read_text())
class Extract(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.stack=[];self.records=[];self.current=[];self.inmain=False
 def handle_starttag(self,t,a):
  if t=='main':self.inmain=True
  if t in ['title','h1','p']:self.current.append({'tag':t,'attrs':dict(a),'parts':[],'inmain':self.inmain})
 def handle_data(self,t):
  for n in self.current:n['parts'].append(t)
 def handle_endtag(self,t):
  if t=='main':self.inmain=False
  for i in range(len(self.current)-1,-1,-1):
   if self.current[i]['tag']==t:
    n=self.current.pop(i);n['text']=N(''.join(n.pop('parts')));self.records.append(n);break
checks=[]
def ck(name,actual,expected):checks.append({'check':name,'actual':actual,'expected':expected,'pass':actual==expected})
def ptr(obj,pointer):
 for part in pointer.strip('/').split('/'):
  part=part.replace('~1','/').replace('~0','~');obj=obj[int(part)] if isinstance(obj,list) else obj[part]
 return obj
freeze=json.loads((P/'rubric/freeze_record.json').read_text())
for f in freeze['files']:ck('rubric hash '+f['path'],sha(P/'rubric'/f['path']),f['sha256'])
for f in json.loads((P/'evidence/immutable-input-baseline.json').read_text())['criticalFiles']+json.loads((P/'evidence/immutable-input-baseline.json').read_text())['implementationReadOnlyFiles']:ck('immutable '+f['path'],sha(Path(f['path'])),f['sha256'])
manifest=json.loads((B/'delivery-manifest.json').read_text())
for f in manifest['files']:ck('accepted package '+f['path'],[Path(B/f['path']).stat().st_size,sha(B/f['path'])],[f['bytes'],f['sha256']])
seen=set()
def references(v):
 if isinstance(v,dict):
  for pk,hk in [('file','sha256'),('sourceFile','sourceSha256'),('rawFile','rawSha256')]:
   if isinstance(v.get(pk),str) and isinstance(v.get(hk),str):
    f=Path(v[pk]);key=(str(f),v[hk])
    if key not in seen:seen.add(key);ck('mapping reference '+str(f),sha(f),v[hk])
  for x in v.values():references(x)
 elif isinstance(v,list):
  for x in v:references(x)
references(M)
for rec in M['records']:
 id=rec['id'];orig=rec['primary_keyword_origin'];ck('primary source mapping '+id,ptr(json.loads(Path(orig['file']).read_text()),orig['jsonPointer']),rec['primary_keyword'])
 if id!='home':
  orig=rec['keyword_cluster_origin'];ck('cluster source mapping '+id,ptr(json.loads(Path(orig['file']).read_text()),orig['jsonPointer']),rec['keyword_cluster']);ck('query class preserved '+id,next(x['queryClass'] for x in F['pages'] if x['id']==id),rec['query_class'])
 for support in rec['secondary_keyword_support']:
  src=support['origin'];j=json.loads(Path(src['file']).read_text())
  if src.get('jsonPointer'):ck('secondary retained editorial candidate '+support['term'],support['term'] in ptr(j,src['jsonPointer']),True)
  qlog=json.loads(Path('/workspace/shared/gangnam-research-20261013/purchase/query-log.json').read_text());exact=[x['id'] for x in qlog['queries'] if x['query']==support['term'] and x['id'] in support['exactQueryIds']]
  ck('secondary exact query truth '+support['term'],[bool(exact),exact],[support['exactlyQueriedInSelectedEvidence'],support['exactQueryIds']])
 for q in rec['query_evidence']:
  if q['type']=='observed-query':
   x=q['value'];src=ptr(json.loads(Path(x['sourceFile']).read_text()),x['jsonPointer']);ck('observed query '+id+'/'+x['queryId'],[src['id'],src['query']],[x['queryId'],x['exactQuery']])
 ck('tier inference explicitly labeled '+id,rec['query_priority']==1 and rec['query_priority_semantics']['relativeRankWithinTier'] is None and 'newly explicit' in rec['query_priority_semantics']['classification'],True)
scored=[]
for rec in T['records']:
 id=rec['id'];target=rec['evaluationTarget'];copy=C['home'] if id=='home' else next(x for x in A['articles'] if x['id']==id)
 source=B/('copy/common-visible-copy.final.json' if id=='home' else 'copy/article-copy.final.json');base='/common/home' if id=='home' else '/articles/'+str(next(i for i,x in enumerate(A['articles']) if x['id']==id));openingKey='intro' if id=='home' else 'firstAnswer'
 fields={'title':N(copy['title']),'h1':N(copy['h1']),'opener':N(copy[openingKey])}
 rendered=next(x for x in R['records'] if x['id']==id);html=Path(rendered['htmlFile']);ck('rendered exact hash '+id,sha(html),rendered['htmlSha256']);parser=Extract();parser.feed(html.read_text());got={k:next(x['text'] for x in parser.records if x['tag']==tag and (k=='title' or x['inmain'])) for k,tag in [('title','title'),('h1','h1'),('opener','p')]};ck('direct HTML fields '+id,got,fields)
 atoms=[target['region'],target['service']]+target['essentialModifiers'];spans={field:{atom:mod.lexical_candidates(text,atom) for atom in atoms} for field,text in fields.items()}
 query=rec['primary_keyword'];span=mod.lexical_candidates(fields['title'],query)[0];front=mod.front_placement(fields['title'],span)
 ck('full exact query meaningful front '+id,front['front_test'],True)
 def ev(field,quote=None):
  q=fields[field] if quote is None else N(quote);start=fields[field].find(q);assert start>=0
  return {'field':field,'quote':q,'normalizedSpan':[start,start+len(q)],'sourceFile':str(source),'sourceSha256':sha(source),'jsonPointer':base+'/'+({'opener':openingKey}.get(field,field)),'htmlFile':str(html),'htmlSha256':sha(html),'htmlSelector':{'title':'head > title','h1':'main h1','opener':'main first content p after principal h1'}[field]}
 full={'T1':10,'T2':10,'T3':10,'T4':10,'H1':15,'H2':10,'A1':15,'A2':10,'I1':10};rows=[]
 reasons={
 'T1':'Title directly contains the complete frozen region and service in its leading natural phrase; no alias used.',
 'T2':'Title expresses the frozen broad commercial purpose or essential wedding/event modifier. Venue/product suffixes support that purpose rather than replacing it.',
 'T3':'The exact full primary query starts at zero and finishes before the first major separator; frozen midpoint and separator arithmetic passes.',
 'T4':'The exact compact primary phrase occurs naturally at the beginning; no unnecessary inserted promotional words separate the required combination.',
 'H1':'The unique emitted H1 directly includes the same complete frozen region/service combination; no alias or inferred geography is used.',
 'H2':'The H1 retains the frozen purpose: broad wreath choice, condolence, wedding, or exhibition/corporate-event encouragement as appropriate.',
 'A1':'The opening has a complete concrete proposition before character180: basic-price/product choice with consultation or venue conditions, directly useful for the frozen customer question.',
 'A2':'The opening directly expresses both region and service and serves the same customer intent. Natural grammatical suffixes do not alter target scope.',
 'I1':'Full approved sections, matching actual product family and primary consultation action consistently deliver the frozen purchase purpose. Clearly labeled optional related links do not replace the primary response.'}
 if id=='home':reasons['A2']='강남구 is directly expressed in 강남구에. 근조·축하화환 explicitly names the two wreath categories; 화환 is the semantic compound head, not an unrelated embedded word fragment or an alias to a different product. The paragraph covers the broad wreath overview rather than only a substituted unrelated service.'
 if id=='wedding':reasons['A2']='강남구 and 축하화환 are direct lexical matches. 결혼하는 두 분께 전할 states the wedding celebration purpose; this is a semantic purpose judgment, not an added lexical alias for a missing core atom.'
 gates=[]
 if id=='event':
  full['A2']=5;gates=['G4'];reasons['A2']='The whole153-character opener directly names 화환 and the exhibition/corporate-event purpose, but never 강남구. It names 코엑스·SETEC without an explicit singular phrase referring back to H1 (e.g. 이 지역). Frozen lexicalAliases is empty. Inferring their region from outside venue knowledge is not the rubric\'s allowed H1 coreference. One required core atom is therefore verifiably absent in the opening window.'
 for key,points in full.items():
  field='title' if key.startswith('T') else 'h1' if key.startswith('H') else 'opener'
  rows.append({'criterion':key,'points':points,'maxPoints':max(mod.VALUES[key]),'evidence':ev(field),'reason':reasons[key],'atomSpans':spans[field],'inference':key in ['T2','H2','A1','A2','I1']})
 continuum=[]
 if id=='home':
  for key in ['productHeading','priceNote','placeIntro']:
   continuum.append({'sourceFile':str(source),'jsonPointer':base+'/'+key,'quote':copy[key]})
  continuum += [{'sourceFile':str(source),'jsonPointer':'/common/articleCards/'+str(i),'quote':x['summary'],'href':x['href']} for i,x in enumerate(C['articleCards'])]
  action={'label':copy['phoneCta']['label'],'href':copy['phoneCta']['href']}
 else:
  for i,s in enumerate(copy['sections']):continuum.append({'sourceFile':str(source),'jsonPointer':base+'/sections/'+str(i)+'/heading','quote':s['heading'],'anchor':s['id']})
  action=copy['primaryCta']
 rows[-1]['continuityEvidence']=continuum;rows[-1]['primaryAction']=action
 calculated=mod.calculate(full,gates)
 # Independent arithmetic readback, not just trusting the provided helper.
 independent_sum=sum(x['points'] for x in rows);ck('score row sum '+id,independent_sum,calculated['raw_score']);ck('effective ceiling '+id,min(independent_sum,89) if gates else independent_sum,calculated['effective_score'])
 scored.append({'id':id,'url':rec['url'],'applicability':'REQUIRED_SHADOW_DIAGNOSTIC','applicabilityReason':'Existing explicit home primaryKeyword plus commercial product/CTA overview' if id=='home' else 'Frozen N3 purchase article with one accepted primaryKeyword and distinct buyerDecision','originalVersusSupplemental':{'primaryKeyword':'original accepted copy','queryClass':'ADDENDUM_PROPOSED classification' if id=='home' else 'original frozen plan','cluster':'ADDENDUM_PROPOSED name for existing overview' if id=='home' else 'exact original intentKey mapping','queryPriority':'ADDENDUM_PROPOSED tied editorial tier, not measured priority','score':'new independent application of frozen rubric'},'target':target,'metadataFields':{k:rec[k] for k in ['primary_keyword','secondary_keywords','keyword_cluster','query_class','query_priority','query_evidence']},'metadataStatusWithThisEvaluation':'A04_METADATA_COMPLETE','rawFields':fields,'openingWindows':mod.opening_windows(fields['opener']),'titleFrontCalculation':front,'rows':rows,'calculation':calculated,'mandatoryGateReason':reasons['A2'] if id=='event' else None,'productionReady':False})
notapp=[{'id':'directory','url':'/regions/','applicability':'NOT_APPLICABLE','score':None,'reason':'Navigation-only route: fixed-plan.directory requires three actual article cards exactly once; accepted directory.intro directs customers into the three existing purchase articles and has no separately assigned primary query. eventualIndexableEligibility is a technical >=3 criterion, not designation as a distinct primary search document.','evidence':[{'sourceFile':str(B/'plan/fixed-plan.json'),'jsonPointer':'/directory','quote':F['directory']},{'sourceFile':str(B/'copy/common-visible-copy.final.json'),'jsonPointer':'/common/directory/intro','quote':C['directory']['intro']},{'sourceFile':str(B/'independent-plan-review/intent-audit.json'),'jsonPointer':'/countBasis','quote':json.loads((B/'independent-plan-review/intent-audit.json').read_text())['countBasis']}]},{'id':'404','url':'/404.html','applicability':'NOT_APPLICABLE','score':None,'reason':'Accepted error/recovery page, no search/purchase primary intent. Actual public HTTP error status not checked here.','evidence':[{'sourceFile':str(B/'copy/common-visible-copy.final.json'),'jsonPointer':'/common/notFound','quote':C['notFound']}]}]
collisions=[{'pair':['home','funeral'],'finding':'Distinct overview versus condolence purchase detail','evidence':'Home offers eight products and routes among three occasions; funeral has four B SKUs, Samsung room limit/Yonsei identity and condolence CTA.'},{'pair':['home','wedding'],'finding':'Distinct overview versus wedding purchase detail','evidence':'Home broad occasion choice; wedding has four C SKUs, Grandhill hall/session and bride/groom ribbon choices with wedding CTA.'},{'pair':['home','event'],'finding':'Distinct overview versus exhibition/corporate-event purchase detail','evidence':'Home overview; event answers hall/booth, receipt and post-event disposal decisions for Coex/SETEC.'},{'pair':['funeral','wedding'],'finding':'Different recipients, purpose, product family and venue decisions','evidence':'Condolence B SKUs/Samsung/Yonsei versus wedding C SKUs/Grandhill.'},{'pair':['funeral','event'],'finding':'Different purpose/product/operational decisions','evidence':'Funeral room and condolences versus event hall/booth and removal responsibility.'},{'pair':['wedding','event'],'finding':'Same C SKU catalog but different primary customer decisions','evidence':'Wedding couples/hall/session/ribbon versus exhibitor/booth/recipient/exit and disposal. Shared catalog does not imply same primary intent.'}]
result={'reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'Independent implementation/input auditor applying the separately frozen A04 rubric','independenceDisclosure':'Reviewer previously read Gangnam copy and HTML for exact-copy audit. This is not a blind review. No other evaluator scores/findings/verdicts were read before saving this result. Same score-free frozen target map was used without alias additions or rubric changes.','rubricFile':str(P/'rubric/A04_RUBRIC_v1.md'),'rubricSha256':sha(P/'rubric/A04_RUBRIC_v1.md'),'targetMapFile':str(P/'assessment/targets.frozen.json'),'targetMapSha256':sha(P/'assessment/targets.frozen.json'),'mappingDraftSha256':sha(P/'mapping/keyword-mapping.draft.json'),'scope':'Supplemental local content alignment and evidence recording only. Not original Query-first chronology, production readiness, search ranking or browser review.','scoredPages':scored,'notApplicablePages':notapp,'counts':{'scored':4,'notApplicable':2,'alignmentMeetsThreshold':3,'alignmentRevise':1,'unverifiedAlignment':0,'originalArticleN':3,'customerHtmlRoutes':6},'pairwiseIntentAssessment':collisions,'directChecks':{'count':len(checks),'failed':[x for x in checks if not x['pass']],'checks':checks},'toolsReportedOnly':['Rubric/target-map authors state they had not seen target copy before their freeze; file/hash consistency and recorded chronology were checked, not their private browsing history.'],'unverified':['Search volume, popularity, rank, impressions, clicks and conversion were not measured.','Browser visuals, keyboard interactions, public HTTP/indexability, hostname ownership and search submissions remain outside this review.'],'noChanges':['Accepted fixed plan/copy/source/customer HTML and earlier implementation evidence untouched.','No newly added alias, forced score90, mean hiding a failure, or prose change.']}
(O/'independent-assessment.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
summary={'rubricSha256':result['rubricSha256'],'targetMapSha256':result['targetMapSha256'],'pages':[{'id':x['id'],**x['calculation']} for x in scored],'checks':len(checks),'failedChecks':result['directChecks']['failed'],'assessmentSha256':sha(O/'independent-assessment.json')}
(O/'independent-recalculation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
