from pathlib import Path
import json,hashlib,datetime
O=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
a=read(O/'copy/article-copy.final.json');c=read(O/'copy/common-visible-copy.final.json');plan=read(O/'plan/fixed-plan.json');assets=read(O/'handoff/approved-assets.json');directory=read(O/'handoff/directory-input.json')
# Rebuild derived projections from the latest authoritative exact copy only.
for f in assets['assets']:
 if f['kind']=='actual-sale-product':f['copy']=next(x for x in c['common']['productCards'] if x['sku']==f['sku'])
assets['bannersCopy']=c['common']['banners'];write(O/'handoff/approved-assets.json',assets)
directory['directoryArticleCards']=c['common']['articleCards'];write(O/'handoff/directory-input.json',directory)
files=['plan/fixed-plan.json','copy/article-copy.final.json','copy/common-visible-copy.final.json','handoff/approved-assets.json','handoff/directory-input.json']
bindings={p:{'sha256':sha(O/p),'bytes':(O/p).stat().st_size} for p in files}
write(O/'handoff/input-bindings.json',{'type':'LOCAL_EXACT_COPY_BINDING_NOT_A_GIT_COMMIT','createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':bindings})
runtime={'schemaVersion':1,'region':{'name':'서울특별시 강남구','key':'gangnam','officialCode':'11680','nationalOrder':23},'originalPlanN':3,'articles':a['articles'],'common':c['common'],'directory':directory,'assets':assets,'expectedPaths':plan['routeDenominator'],'inputBindings':bindings,'status':'LOCAL_DATA_HANDOFF_NOT_IMPLEMENTED','publication':{'sourceCommit':None,'canonicalHostname':None,'productionApproved':False,'hostnameOwnershipVerified':False,'publicHttpVerified':False,'indexNowSubmitted':False},'visibilityContract':'Exact approved customer strings only; sections are the body. Do not emit contentMarkdown and sections together. FAQ is independent of body render mode. Metadata/evidence/bindings/proof paths not customer output.'}
write(O/'handoff/runtime-input.json',runtime)
visible=[];functional=[];dataReferences=[]
# Whitelist data-driven exact UI strings for later rendering comparison.
exclude={'id','slug','url','href','imageUrl','imageSha256','sku','primaryKeyword','intentKey','evidence','productSkus','productCardSkus','facilityAnchors','sourceFile','renderRule','visibilityContract','file','primaryKeywordDirection'}
def collect(v,path):
 if isinstance(v,dict):
  for k,z in v.items():
   if k == 'productCardSkus':dataReferences.append({'path':path+'.'+k,'values':z});continue
   if k in ['href','url','imageUrl'] or k.lower().endswith('href'):functional.append({'path':path+'.'+k,'value':z});continue
   if k in exclude:continue
   collect(z,path+'.'+k)
 elif isinstance(v,list):
  for i,z in enumerate(v):collect(z,f'{path}[{i}]')
 elif isinstance(v,str):visible.append({'path':path,'text':v})
for i,art in enumerate(a['articles']):
 for key in ['title','h1','metaDescription','cardSummary','firstAnswer','sections','faq','sourceNote','sourceLinks','primaryCta','relatedLink']:collect(art[key],f'articles[{i}].{key}')
collect(c['common'],'common')
write(O/'handoff/visible-copy-inventory.json',{'scope':'Exact fields, not proof they are rendered; sharedNotices follow renderRule and title/meta are document metadata. Context-dependent duplicates are deliberate projections.','visibleTextFields':visible,'functionalTargets':functional,'dataReferences':dataReferences,'articleHash':sha(O/'copy/article-copy.final.json'),'commonHash':sha(O/'copy/common-visible-copy.final.json')})
checks=[{'check':'runtimeArticleProjection','pass':runtime['articles']==a['articles']},{'check':'runtimeCommonProjection','pass':runtime['common']==c['common']},{'check':'runtimeDirectoryProjection','pass':runtime['directory']==directory},{'check':'runtimeAssetsProjection','pass':runtime['assets']==assets},{'check':'sixUniqueExpectedPaths','pass':len(set(runtime['expectedPaths']))==6},{'check':'noSourceOrHostname','pass':runtime['publication']['sourceCommit'] is None and runtime['publication']['canonicalHostname'] is None},{'check':'allAssetReadbacks','pass':all(sha(O/f['file'])==f['sha256'] for f in assets['assets'])}]
write(O/'handoff/projection-validation.json',{'status':'PASS' if all(x['pass'] for x in checks) else 'FAIL','scope':'Local exact projection and file readback only, not a renderer or public-site test.','checks':checks,'runtimeInputSha256':sha(O/'handoff/runtime-input.json')})
print('Handoff input and exact projection prepared',len(visible),'text fields',len(functional),'functional references')
