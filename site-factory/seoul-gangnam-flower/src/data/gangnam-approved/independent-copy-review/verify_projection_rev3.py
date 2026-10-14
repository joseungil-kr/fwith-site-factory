from pathlib import Path
import json,hashlib,datetime,re
B=Path('/workspace/shared/gangnam-plan-copy-20261013');D=B/'independent-copy-review'
read=lambda p:json.loads((B/p).read_text())
a=read('copy/article-copy.final.json');c=read('copy/common-visible-copy.final.json');p=read('plan/fixed-plan.json');d=read('handoff/directory-input.json');assets=read('handoff/approved-assets.json');r=read('handoff/runtime-input.json');inv=read('handoff/visible-copy-inventory.json')
checks=[]
def ck(n,v,detail=None):checks.append({'check':n,'pass':bool(v),**({'detail':detail} if detail is not None else {})})
ck('wholeArticleObjectsExactlyMatch',r['articles']==a['articles'])
ck('wholeCommonObjectExactlyMatches',r['common']==c['common'])
ck('wholeDirectoryObjectExactlyMatches',r['directory']==d)
ck('wholeAssetsObjectExactlyMatches',r['assets']==assets)
ck('frozenOriginalNAndSixRoutes',r['originalPlanN']==3 and r['expectedPaths']==p['routeDenominator'] and len(r['expectedPaths'])==len(set(r['expectedPaths']))==6)
ck('noCommitOrPublicVerificationClaim',r['publication']=={'sourceCommit':None,'canonicalHostname':None,'productionApproved':False,'hostnameOwnershipVerified':False,'publicHttpVerified':False,'indexNowSubmitted':False})
root={'articles':a['articles'],'common':c['common']};expected={}; targets={}
ignore={'id','slug','primaryKeyword','intentKey','sku','imageSha256','file','renderRule','visibilityContract','productSkus','productCardSkus','facilityAnchors','evidence','url'}
def walk(x,path='',key=''):
 if key in {'evidence','productSkus','productCardSkus','facilityAnchors'}:return
 if isinstance(x,dict):
  for k,v in x.items():walk(v,path+'.'+k if path else k,k)
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,path+f'[{i}]',key)
 elif isinstance(x,str):
  if key in {'url','href','imageUrl'} or key.endswith('Href'):
   # Article url is its canonical planned identity, not a consumer clickable field.
   if not re.fullmatch(r'articles\[\d+\]\.url',path):targets[path]=x
  elif key not in ignore:expected[path]=x
walk(root)
actual={x['path']:x['text'] for x in inv['visibleTextFields']}; actt={x['path']:x['value'] for x in inv['functionalTargets']}
ck('visibleFieldsHaveUniquePaths',len(actual)==len(inv['visibleTextFields']))
ck('allCustomerProseFieldsExactlyInventoried',expected==actual,{'independentCount':len(expected),'inventoryCount':len(actual),'missing':sorted(set(expected)-set(actual)),'extra':sorted(set(actual)-set(expected)),'changed':[x for x in set(actual)&set(expected) if actual[x]!=expected[x]]})
ck('allFunctionalTargetsExactlyInventoried',targets==actt,{'independentCount':len(targets),'inventoryCount':len(actt),'missing':sorted(set(targets)-set(actt)),'extra':sorted(set(actt)-set(targets)),'changed':[x for x in set(actt)&set(targets) if actt[x]!=targets[x]]})
refs={f'articles[{ai}].sections[{si}].productCardSkus[{ki}]':sku for ai,x in enumerate(a['articles']) for si,sec in enumerate(x['sections']) for ki,sku in enumerate(sec.get('productCardSkus',[]))}
actualrefs={x['path']+f'[{i}]':value for x in inv.get('dataReferences',[]) for i,value in enumerate(x['values'])}
ck('all12ProductCardDataReferencesExactlyInventoried',len(refs)==12 and refs==actualrefs)
ck('inventoryHashesBindCurrentArticleAndCommon',inv['articleHash']==hashlib.sha256((B/'copy/article-copy.final.json').read_bytes()).hexdigest() and inv['commonHash']==hashlib.sha256((B/'copy/common-visible-copy.final.json').read_bytes()).hexdigest())
assetResults=[]
for x in assets['assets']:
 q=B/x['file'];h=hashlib.sha256(q.read_bytes()).hexdigest();assetResults.append({'path':x['file'],'matches':h==x['sha256'],'sha256':h})
ck('all11PackagedImageHashesMatch',len(assetResults)==11 and all(x['matches'] for x in assetResults))
ck('threeApprovedBannersPreserved',len([x for x in assets['assets'] if x['kind']=='AI-common-banner'])==3)
ck('planPhysicalAnchorsExactlyPreserved',d['physicalAnchors']==p['facilityAnchors'])
ck('directoryArticleCardsMatchCommon',d['directoryArticleCards']==c['common']['articleCards'])
# Input bindings cover exact local bytes, not a Git commit.
ib=read('handoff/input-bindings.json')
ck('allHandoffBindingsMatchExactLocalFiles',all(hashlib.sha256((B/f).read_bytes()).hexdigest()==v['sha256'] and (B/f).stat().st_size==v['bytes'] for f,v in ib['files'].items()))
ck('runtimeBindingsMatchHandoff',r['inputBindings']==ib['files'])
files=['copy/article-copy.final.json','copy/common-visible-copy.final.json','plan/fixed-plan.json','handoff/runtime-input.json','handoff/visible-copy-inventory.json','handoff/directory-input.json','handoff/approved-assets.json','handoff/input-bindings.json','handoff/IMPLEMENTATION-HANDOFF.txt']
manifest=[{'path':x,'sha256':hashlib.sha256((B/x).read_bytes()).hexdigest(),'bytes':(B/x).stat().st_size} for x in files]
out={'reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'independent copy reviewer','verdict':'PASS_LOCAL_EXACT_PROJECTION' if all(x['pass'] for x in checks) else 'REVISION_REQUIRED','scope':'Independent local data/object/field/asset readback only. No renderer, generated HTML, build, public HTTP, provider, IndexNow, or live CTA action tested. Human-read handoff instructions do not authorize unreviewed customer text.','checks':checks,'assetResults':assetResults,'inputs':manifest,'unverified':['Future renderer selects only visible fields and no internal metadata','Actual DOM FAQ/card/button/banner rendering and navigation','Canonical/robots/sitemap/404 behavior','Public delivery and indexing'],'proseInventoryBoundary':'Article and common authored prose only. Geographic unit names and physical addresses are preserved in separately equal directory objects; not counted as 246 authored prose fields.'}
(D/'handoff-projection-verdict.rev3.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
