import json,pathlib,hashlib,datetime
B=pathlib.Path('/workspace/shared/gangnam-a04-addendum-20261013');P=B/'revised-input/acceptance.rev4.json'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text())
a=read(P);c=[];refs=[]
def ck(n,p,d=None):c.append({'check':n,'pass':bool(p),'detail':d})
def walk(x,q):
 if isinstance(x,dict):
  if {'path','bytes','sha256'}<=x.keys():
   p=pathlib.Path(x['path']);ck(q+' file',p.is_file())
   if p.is_file():ck(q+' bytes',p.stat().st_size==x['bytes']);ck(q+' SHA',sha(p)==x['sha256']);refs.append(str(p))
  for k,v in x.items():walk(v,q+'/'+str(k))
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,q+'/'+str(i))
ck('expected acceptance SHA',sha(P)=='63d3244d9d060b3a96f8cdb35cc383453edda00e3d3fa2c7350648baa1d4176c');walk(a,'acceptance')
m=read(a['keywordMapping']['path']);r1=read(a['reviews'][0]['path']);r2=read(a['reviews'][1]['path']);mf=read(a['inputManifest']['path'])
ck('six designated independent and comparison reviews',len(a['reviews'])==6)
for i,r in enumerate(a['primaryResults']):
 for label,x in [('mapping',m['records'][i]),('firstAssessment',r1['records'][i]),('secondAssessment',r2['scoredPages'][i])]:
  ck(r['id']+' '+label+' identity',r['id']==x['id'])
  cal=x.get('calculation',{'raw_score':x.get('title_alignment_raw_score'),'effective_score':x.get('title_alignment_score'),'gates':x.get('title_alignment_gates'),'verdict':x.get('title_alignment_status')})
  ck(r['id']+' '+label+' raw score',r['rawScore']==cal['raw_score']);ck(r['id']+' '+label+' effective score',r['effectiveScore']==cal['effective_score']);ck(r['id']+' '+label+' mandatory gates',r['mandatoryGates']==cal['gates']);ck(r['id']+' '+label+' alignment',r['alignment']==cal['verdict'])
for key,side in [('article',mf['logicalInputOverrides']['copy/article-copy.final.json']),('runtime',mf['logicalInputOverrides']['handoff/runtime-input.json']),('keywordMapping',mf['newSidecars']['a04-keyword-mapping.json']),('claimEvidence',mf['newSidecars']['claim-evidence-addendum.rev4.json'])]:ck('acceptance and manifest '+key+' same binding',a[key]==side)
ck('rubric same frozen input',a['frozenRubric']==mf['frozenRubric']);ck('targets same frozen input',a['frozenTargets']==mf['frozenTargets'])
old=read(a['originalFailurePreserved']['originalMapping']['path'])['records'][3];f=a['originalFailurePreserved']['eventResult'];ck('prior failure exactly preserved',old['title_alignment_raw_score']==f['rawScore']==95 and old['title_alignment_score']==f['effectiveScore']==89 and old['title_alignment_gates']==f['gates']==['G4'])
for k,v in {'articleRevision':4,'commonRevision':2,'originalPlanN':3,'routeDenominator':6,'scoredPrimaryCount':4,'notApplicableCount':2,'implementationPending':True,'sourceModifiedByThisTask':False,'remoteActionsPerformed':[],'productionApprovedByThisDocument':False,'publicUrl':None,'sourceCommit':None,'indexNowSubmitted':False}.items():ck('boundary '+k,a[k]==v)
ck('explicit draft input only status',a['status']=='LOCAL_REV4_EXACT_COPY_AND_A04_INPUT_REVIEWED_ONLY');ck('score not production SEO outcome','not search volume, rank, SEO performance or Production PASS' in a['scoreLimit']);ck('unverified actual revised output and binding','Revised HTML/rendered screen, new implementation metadata binding' in a['classification']['unverified'])
for i in [4,5]:
 z=read(a['reviews'][i]['path']);ck('review '+str(i)+' all enumerated checks pass',z['totals']['failed']==0 and all(c['pass'] for c in z['checks']) and z['totals']['checks']==len(z['checks']))
ck('own assessment raw checks all pass',r2['directChecks']['failed']==[] and all(x['pass'] for x in r2['directChecks']['checks']))
report={'reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'second independent input/copy auditor','acceptance':{'file':str(P),'sha256':sha(P)},'scope':'Exact acceptance bytes, transitive listed file bytes/SHA, independent score/content identifiers and pending implementation boundaries. No implementation operation.','checks':c,'totals':{'checks':len(c),'passed':sum(v['pass'] for v in c),'failed':sum(not v['pass'] for v in c)},'referencedFiles':refs,'verdict':'PASS_LOCAL_REV4_INPUT_ACCEPTANCE_ONLY','judgment':'The acceptance faithfully binds separate original REVISE and revised draft-input scores with no production or implemented-output claim. Each 100 remains a bounded frozen-rubric judgment, not measured SEO quality.','unverified':['Revised source, HTML/browser, metadata runtime binding, public HTTP, remote Git/provider/ownership/indexing, live business fulfillment.'],'modifiedReviewedInputs':False,'checkerCorrection':'Initial local checker compared directChecks.failed (an empty list) with numeric 0. Corrected to schema-exact [] and independently inspected all enumerated check booleans; no input failure or reviewed-input change occurred.'}
O=B/'revised-input/review/acceptance-readback.rev4.json';O.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'file':str(O),'sha256':sha(O),'totals':report['totals'],'failures':[x for x in c if not x['pass']]},indent=2));raise SystemExit(bool(report['totals']['failed']))
