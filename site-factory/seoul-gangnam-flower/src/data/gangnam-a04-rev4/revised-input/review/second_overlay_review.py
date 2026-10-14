import pathlib,json,hashlib,datetime
B=pathlib.Path('/workspace/shared/gangnam-a04-addendum-20261013');BASE=pathlib.Path('/workspace/shared/gangnam-plan-copy-20261013');O=B/'revised-input/review'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text())
checks=[]
def ck(n,v,d=None):checks.append({'check':n,'pass':bool(v),'detail':d})
def rec(x,where):
 if isinstance(x,dict):
  if {'path','bytes','sha256'}<=x.keys():
   p=pathlib.Path(x['path']);ck(where+' exists',p.is_file())
   if p.is_file():ck(where+' bytes',p.stat().st_size==x['bytes']);ck(where+' SHA',sha(p)==x['sha256'])
  for k,v in x.items():rec(v,where+'/'+str(k))
 elif isinstance(x,list):
  for i,v in enumerate(x):rec(v,where+'/'+str(i))
p=B/'revised-input/input-manifest.rev4.json';m=read(p);ck('overlay manifest advertised SHA',sha(p)=='ecae498ef320e9122f665f3db1787f6084a4084042fce0d5e03114216ae790ca');rec(m,'overlay')
bm=read(BASE/'delivery-manifest.json');ck('base inventory count',bm['fileCount']==len(bm['files'])==162)
for f in bm['files']:
 rec({**f,'path':str(BASE/f['path'])},'unchanged-base/'+f['path'])
ck('only three logical file overrides',set(m['logicalInputOverrides'])=={'copy/article-copy.final.json','copy/article-copy.final.txt','handoff/runtime-input.json'})
ck('two explicit sidecars',set(m['newSidecars'])=={'a04-keyword-mapping.json','claim-evidence-addendum.rev4.json'})
ck('denominators distinctly correct',[m[k] for k in ['originalPlanN','routeDenominator','a04PrimaryDenominator','a04NonPrimaryDenominator']]==[3,6,4,2])
r=read(m['logicalInputOverrides']['handoff/runtime-input.json']['path']);a=read(m['logicalInputOverrides']['copy/article-copy.final.json']['path']);old=read(BASE/'handoff/runtime-input.json')
ck('new runtime articles exact revision4 projection',r['articles']==a['articles'])
for k in ['common','directory','approvedAssets','publication']:
 if k in old:ck('runtime '+k+' unchanged',r[k]==old[k])
ck('no supplement overwrite of base paths',all(not str(v['path']).startswith(str(BASE)+'/') for v in m['logicalInputOverrides'].values()))
h=B/'IMPLEMENTATION-HANDOFF.txt';text=h.read_text();ck('handoff original and new results distinct','raw95/effective89 REVISE' in text and '각각100' in text);ck('handoff states source unmodified and pending rendering','source를 수정하지 않았다' in text and 'render/build/browser/public HTTP 검증 전' in text);ck('handoff excludes customer metadata display','고객화면에 표시하지 않는다' in text);ck('handoff not production/public authority','공개 배포 권한을 추가하지 않는다' in text);ck('handoff no invented demand','실제 수요 우선순위가 아니며' in text);ck('handoff old output not reused for new input','기존 화면 PASS를 새 문구 반영 PASS로 재사용하지 않는다' in text)
report={'reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Independent supplemental overlay input/handoff review; no implementation changes or deployment claim.','manifest':{'path':str(p),'sha256':sha(p)},'handoff':{'path':str(h),'sha256':sha(h)},'checks':checks,'totals':{'checks':len(checks),'passed':sum(c['pass'] for c in checks),'failed':sum(not c['pass'] for c in checks)},'verdict':'PASS_INPUT_OVERLAY_ONLY','judgments':['Base bundle bytes remain unchanged and all 162 listed original files match.','Only article JSON/TXT and runtime projection are overrides, with A04 and regional claim sidecars. N3 and 6 routes remain distinct from 4 scored primary documents.','No blocking provenance or current-versus-future rendered boundary omission found. Final acceptance should additionally bind the independent metadata readback and this overlay review.'],'unverified':['Revised implementation source or output, browser layout, live/public HTTP, deployment and overall production gates.'],'pathResolutionNote':'Initial guessed revised-input/IMPLEMENTATION-HANDOFF.txt was absent; found and directly read existing bundle-root IMPLEMENTATION-HANDOFF.txt. No access denial occurred.'}
o=O/'second-overlay-review.rev4.json';o.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'file':str(o),'sha256':sha(o),'totals':report['totals'],'failures':[c for c in checks if not c['pass']]},ensure_ascii=False,indent=2));raise SystemExit(bool(report['totals']['failed']))
