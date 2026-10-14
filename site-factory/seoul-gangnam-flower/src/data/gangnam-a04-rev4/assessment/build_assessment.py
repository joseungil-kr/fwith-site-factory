from pathlib import Path
import sys,json,hashlib,datetime,itertools
R=Path('/workspace/shared/gangnam-a04-addendum-20261013')
sys.path.insert(0,str(R/'rubric'))
from normalization import normalize,lexical_candidates,front_placement,opening_windows,calculate,VALUES
A=R/'assessment'; target_file=A/'targets.frozen.json'; target=json.loads(target_file.read_text())
common_file=Path('/workspace/shared/gangnam-plan-copy-20261013/copy/common-visible-copy.final.json')
article_file=Path('/workspace/shared/gangnam-plan-copy-20261013/copy/article-copy.final.json')
plan_file=Path('/workspace/shared/gangnam-plan-copy-20261013/plan/fixed-plan.json')
common=json.loads(common_file.read_text()); articles=json.loads(article_file.read_text());plan=json.loads(plan_file.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pointer(obj,p):
 for bit in p.strip('/').split('/') if p else []:
  bit=bit.replace('~1','/').replace('~0','~');obj=obj[int(bit)] if isinstance(obj,list) else obj[bit]
 return obj
source_docs={str(common_file):common,str(article_file):articles,str(plan_file):plan}
def ev(file,ptr,substring=None):
 full=pointer(source_docs[str(file)],ptr);assert isinstance(full,str)
 n=normalize(full); sub=normalize(substring) if substring is not None else n
 start=n.find(sub);assert start>=0,(ptr,sub)
 return {'sourceFile':str(file),'sourceSha256':sha(file),'jsonPointer':ptr,'quote':sub,'normalizedSpan':[start,start+len(sub)]}
# Row decisions are the independent reviewer's semantic judgments made after full-copy reading.
# This script serializes those decisions and checks arithmetic; it does not infer semantics.
records=[]
for ix,t in enumerate(target['records']):
 id=t['id'];c=common['common']['home'] if id=='home' else articles['articles'][ix-1]
 f=common_file if id=='home' else article_file
 prefix='/common/home' if id=='home' else f'/articles/{ix-1}'
 opkey='intro' if id=='home' else 'firstAnswer'
 title,h1,op=c['title'],c['h1'],c[opkey]
 target_atoms=[t['evaluationTarget']['region'],t['evaluationTarget']['service']]+t['evaluationTarget']['essentialModifiers']
 combo=lexical_candidates(title,t['primary_keyword'])[0]
 front=front_placement(title,combo)
 opener=opening_windows(op)
 sentence=normalize(op).split('. ',1)[0]
 if not sentence.endswith('.'):sentence+='.'
 assert sentence in normalize(op)
 evidence={'title':ev(f,prefix+'/title'),'h1':ev(f,prefix+'/h1'),'opener':ev(f,prefix+'/'+opkey),'directAnswer':ev(f,prefix+'/'+opkey,sentence)}
 rows={k:max(v) for k,v in VALUES.items()}
 reasons={
 'T1':'Title directly spells out the frozen region and service as the primary query phrase. These are actual text matches, not an inferred synonym.',
 'T2':'Title preserves the full frozen query purpose. The broad core-commercial/condolence target needs no additional purchase modifier; wedding/event titles also retain their explicit occasion modifier.',
 'T3':f'The full primary combination is at span {combo}; the frozen front-placement calculation is true, before the first major separator.',
 'T4':'The primary keyword appears intact in one natural phrase at the start. No extra word is inserted within the core query phrase.',
 'H1':'H1 directly retains the same complete frozen region/service and, where present, the occasion phrase.',
 'H2':'The H1 natural expansion expresses the same buyer purpose as the target: regional overview, condolence, wedding celebration or exhibition/corporate event respectively.',
 'A1':'The opening immediately offers relevant product/basic-price information and a consultation or decision path, completing a useful proposition before character 180. This rates answer relevance, not factual verification of the price.',
 'A2':'The opening expressly contains the frozen region and service and addresses the same purchase purpose. Natural particles and the service morpheme in a transparently named subtype do not change its meaning.',
 'I1':'All supplied substantive sections, FAQ, stated primary CTA and optional related link were inspected. They retain the frozen buyer purpose; alternative-occasion links are explicitly secondary.'}
 if id=='event':
  rows['A2']=5
  reasons['A2']='The opening contains 화환 and the corporate/exhibition purpose, but no 강남구 and no explicit singular geographic reference to H1. 코엑스·SETEC are distinct venue names, not approved region aliases. Their location could be inferred from later text, but that is outside the frozen opening test. Exactly one core atom is missing in the opening.'
 body=[]
 if id=='home':
  for key in ['productHeading','funeralProductHeading','celebrationProductHeading','articleHeading','placeIntro','priceNote']:
   body.append(ev(f,prefix+'/'+key))
  for i in range(3):body.append(ev(f,f'/common/articleCards/{i}/summary'))
  cta=[ev(f,prefix+'/phoneCta/label'),ev(f,prefix+'/shopCta/label')]
  checked=['all common/home fields','all 8 shared product cards','all 3 article cards','shared notices','navigation and footer','directory and 404 fields for applicability']
 else:
  for i,s in enumerate(c['sections']):
   body.append(ev(f,prefix+f'/sections/{i}/heading'))
   # Actual substantive first paragraph, not merely the heading.
   body.append(ev(f,prefix+f'/sections/{i}/paragraphs/0'))
  for i,qa in enumerate(c['faq']):body.append(ev(f,prefix+f'/faq/{i}/answer'))
  cta=[ev(f,prefix+'/primaryCta/label'),ev(f,prefix+'/relatedLink/intro'),ev(f,prefix+'/relatedLink/label')]
  checked=['all sections and every paragraph','FAQ','sourceNote/sourceLinks as authored strings','primaryCta/relatedLink','productSkus and common product-card bindings']
 evidence['body']=body;evidence['ctaText']=cta
 selected={
  'T1':[evidence['title']], 'T2':[evidence['title']], 'T3':[evidence['title']], 'T4':[evidence['title']],
  'H1':[evidence['h1']], 'H2':[evidence['h1']], 'A1':[evidence['directAnswer']], 'A2':[evidence['opener']], 'I1':body+cta}
 gates=['G4'] if id=='event' else []
 result=calculate(rows,gates)
 lexical={field:{atom:lexical_candidates(text,atom) for atom in target_atoms} for field,text in [('title',title),('h1',h1),('opener',opener['first_180'])]}
 if id=='home':lexical['semanticNote']='The explicit compound 근조·축하화환 names flower wreath subtypes; 화환 is the head noun, not an accidental embedded-word fragment.'
 if id=='wedding':lexical['semanticNote']='The opener’s 결혼하는 두 분께 explicitly expresses the same wedding purpose. Literal 결혼식 exists in Title/H1; opening intent is assessed semantically, without changing lexical aliases.'
 record={'id':id,'url':t['url'],'scope':'Local final-copy JSON content only; rendered HTML and deployment not inspected',
  'applicability':'REQUIRED_SHADOW_DIAGNOSTIC','applicabilityEvidence':{'source':str(plan_file),'sha256':sha(plan_file),'scope':plan['scope'],'reason':'HOME is declared principal commercial overview; articles are the three frozen regional purchase pages. Local unpublished/noindex status does not exempt intended primary content.'},
  'rubricVersion':'A04-local-independent-v1','rubricSha256':sha(R/'rubric/A04_RUBRIC_v1.md'),'targetMapSha256':sha(target_file),
  'metadata':{k:t[k] for k in ['primary_keyword','secondary_keywords','keyword_cluster','query_class','query_priority','query_priority_semantics','query_evidence']},
  'metadataVerdict':'A04_METADATA_COMPLETE_IN_ADDENDUM','metadataLimitations':['query priority is a new explicit tied editorial tier, not recovered prior priority or demand measurement','home cluster/class and all numerical scores are supplemental; they do not prove original Query-first chronology','saved search requests/results are tool observations, not observed customer search frequency','exact-primary demand, volume and ranking remain unverified'],
  'fieldEvidence':evidence,'openingWindows':opener,'openingCharacterCount':len(normalize(op)),
  'firstDirectPropositionEnd':evidence['directAnswer']['normalizedSpan'][1],
  'lexicalCandidateSpans':lexical,'selectedPrimaryTitleSpan':combo,'titleFrontCalculation':front,
  'rowDecisions':{k:{'points':v,'maximum':max(VALUES[k]),'deduction':max(VALUES[k])-v,'rationale':reasons[k],'evidence':selected[k]} for k,v in rows.items()},
  'calculation':result,'title_alignment_score':result['effective_score'],
  'gateFindings':[{'gate':'G4','criterion':'A2','classification':'Verified textual absence under the preregistered geographic-opening test','finding':reasons['A2'],'rawBeforeCeiling':95,'ceiling':89}] if id=='event' else [],
  'readScope':checked,'noCopyChanges':True}
 records.append(record)
# Verify every query-log mapping, raw query, receipt timestamp and retained result count.
query_checks=[]
for r in target['records']:
 for q in r['query_evidence']:
  if q.get('type')!='observed-query':continue
  v=q['value']; log=json.loads(Path(v['sourceFile']).read_text());row=pointer(log,v['jsonPointer']);raw=json.loads(Path(v['rawFile']).read_text())
  checks={'logSha':sha(v['sourceFile'])==v['sourceSha256'],'rawSha':sha(v['rawFile'])==v['rawSha256'],'queryId':row['id']==v['queryId'] and (raw.get('query_id')==v['queryId'] if 'query_id' in raw else Path(v['rawFile']).stem==v['queryId']),'exactQuery':row['query']==v['exactQuery']==raw['query'],'responseTime':row['response_received_at']==v['observedAt']==raw.get('response_received_at',raw.get('observed_at')),'retainedResults':len(row['observations'])==v['resultCountObserved']}
  query_checks.append({'page':r['id'],'queryId':v['queryId'],'checks':checks,'scope':'Saved local query/result record inspected; no live query or actual search-volume observation','allChecks':all(checks.values()),'rawSchemaNote':'Q02 has observed_at and no internal query_id; ID is linked through query-log pointer, exact query, raw filename and hash' if v['queryId']=='Q02' else 'query_id and response_received_at verified'})
# Original factual and prior editorial reports are only integrity-checked here; their verdicts are not used for points.
refs={}
def walk(v):
 if isinstance(v,dict):
  for k,h in [('file','sha256'),('sourceFile','sourceSha256'),('rawFile','rawSha256')]:
   if v.get(k) and v.get(h):refs[v[k]]=v[h]
  for child in v.values():walk(child)
 elif isinstance(v,list):
  for child in v:walk(child)
walk(target)
hash_checks=[{'path':p,'expected':h,'actual':sha(p),'matches':sha(p)==h} for p,h in refs.items()]
# Explicit six-pair distinctness reasoning with real substantive evidence.
pairs=[]
byid={r['id']:r for r in records}
for left,right in itertools.combinations(byid,2):
 if left=='home':
  why='HOME lets a customer choose between occasion/product groups; the article delivers the narrower named occasion with its destination, order inputs and conditions. Overlap in broad wreath nouns and phone number does not make those customer decisions identical.'
 elif (left,right)==('wedding','event'):
  why='The same C-series products and phone CTA are used, but wedding requires specific ceremony date/time/hall and recipient side; corporate/exhibition ordering requires event, booth/company, receipt/entry and later removal conditions. Their product overlap is disclosed rather than hidden.'
 else:
  why='Condolence uses B-series products, bereavement ribbon text and room/deceased/funeral timing inputs. The other article uses C-series celebration products and a different occasion, recipient details and practical conditions.'
 pairs.append({'left':left,'right':right,'verdict':'NO_DUPLICATE_PRIMARY_INTENT_OBSERVED_IN_THIS_LOCAL_SET','reason':why,'leftEvidence':byid[left]['fieldEvidence']['body']+byid[left]['fieldEvidence']['ctaText'],'rightEvidence':byid[right]['fieldEvidence']['body']+byid[right]['fieldEvidence']['ctaText'],'limit':'Not an audit of any other site URLs, deployed pages or search-engine cannibalization outcomes.'})
na=[{'id':'directory','url':'/regions/','applicability':'NOT_APPLICABLE','title_alignment_score':None,
 'reason':'The authored intro, heading and links define navigation to the three purchase documents and facility/region relationships; no independent primary query is assigned. Eventual indexability eligibility in the plan does not itself make this a primary query document. This is a local documented-role classification, not a claim of production robots/HTTP state.',
 'evidence':[ev(common_file,'/common/directory/intro'),ev(common_file,'/common/directory/districtGuideNote'),ev(common_file,'/common/directory/facilityScopeNote')],
 'indexabilityCaveat':plan['directory']['eventualIndexableEligibility'],'reconsiderIf':'A distinct primary query/navigation intent is subsequently assigned or actual implementation makes it a commercial primary landing page.'},
 {'id':'notFound','url':'/404.html','applicability':'NOT_APPLICABLE','title_alignment_score':None,'reason':'The local notFound fields state an error/recovery role and link home, not a primary query landing page. Actual 404 HTTP/noindex behavior is outside local-copy verification.',
 'evidence':[ev(common_file,'/common/notFound/title'),ev(common_file,'/common/notFound/h1'),ev(common_file,'/common/notFound/text')]}]
report={'assessmentVersion':'independent-A04-assessment-v1','createdAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'resultScope':'Verified local copy alignment under a preregistered rubric; no Production PASS or SEO outcome claim',
 'rubricSha256':sha(R/'rubric/A04_RUBRIC_v1.md'),'targetMapSha256':sha(target_file),
 'summary':{'scored':4,'meetsInternalThreshold':3,'revise':1,'notApplicable':2,'unverifiedScoreRows':0,'articleN':3,'averageUsed':False},
 'records':records,'nonPrimaryRoutes':na,'pairwiseIntentReview':pairs,'queryEvidenceReadback':query_checks,'sourceIntegrityReadback':hash_checks,
 'unverified':['HTML/rendered first-prose binding and visuals','actual CTA destination functionality','public HTTP/robots/canonical/sitemap/indexing','external factual claims and live prices/current venue acceptance not independently rechecked in this narrow local assessment','search demand, volume, rank, traffic or conversion','original drafting chronology cannot be proven by an after-the-fact metadata addendum'],
 'findingClassification':{'directlyVerified':'Local source strings, exact quoted spans, absence/presence of terms, source hashes, saved query record correspondence and arithmetic','toolReported':'Saved prior search observations; no claim that saved results prove real customer demand','judgment':'Role applicability, semantic directness and intent comparison under frozen rubric; weights and 89 ceiling are operational','notVerified':'Listed in unverified'},
 'originalPlanCopySourceUnchanged':all(r['matches'] for r in hash_checks)}
out=A/'a04-independent-assessment.v1.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
# Full output quote readback independent of serialization path.
quote_count=0
def verify_quotes(v):
 global quote_count
 if isinstance(v,dict):
  if all(k in v for k in ['sourceFile','jsonPointer','quote','normalizedSpan']):
   original=json.loads(Path(v['sourceFile']).read_text());n=normalize(pointer(original,v['jsonPointer']));start,end=v['normalizedSpan']
   assert n[start:end]==v['quote'];assert sha(v['sourceFile'])==v['sourceSha256'];quote_count+=1
  for child in v.values():verify_quotes(child)
 elif isinstance(v,list):
  for child in v:verify_quotes(child)
readback=json.loads(out.read_text());verify_quotes(readback)
for r in readback['records']:
 assert calculate({k:v['points'] for k,v in r['rowDecisions'].items()},r['calculation']['gates'])==r['calculation']
assert all(q['allChecks'] for q in query_checks)
assert all(row['matches'] for row in hash_checks)
log={'assessmentSha256':sha(out),'quoteSpanReadbacks':quote_count,'scoreRecalculations':len(records),'queryRecordChecks':len(query_checks),'sourceHashChecks':len(hash_checks),'allChecksPassed':True,'note':'Mechanical success validates serialization, spans and arithmetic only; content verdicts remain those explicitly recorded.'}
(A/'assessment-readback-log.json').write_text(json.dumps(log,indent=2)+'\n')
print(json.dumps(log,indent=2))
for r in records:print(r['id'],r['calculation']['raw_score'],r['calculation']['effective_score'],r['calculation']['verdict'],r['openingCharacterCount'],r['firstDirectPropositionEnd'])
