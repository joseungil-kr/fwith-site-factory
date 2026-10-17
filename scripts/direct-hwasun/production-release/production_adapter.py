"""Bounded Hwasun output projection, reusing actual-success Gurye adapter methods.
Accepted source47 and customer bodies remain immutable. No provider or IndexNow client.
"""
from pathlib import Path
from html.parser import HTMLParser
import argparse,datetime,hashlib,html,json,os,re,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
SOURCE='17703e6e4c8a82f3271088a76b8cf7d76bf1ff08'
ORIGIN='https://hwasun.fwith.kr';HOST='hwasun.fwith.kr'
CONTRACT_SHA='6c788995951c7207e19ecc6cd2342cb65bb4aa044f7c430f9df587dd491f1822'
FILES={'index.html':'/','404.html':'/404.html'}
def require(ok,message):
 if not ok:raise ValueError(message)
def digest(data):return hashlib.sha256(data).hexdigest()
def save(path,obj):p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
FORBIDDEN_ENV=('SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION','SITE_RELEASE_MODE','SITE_INDEXABLE','SITE_RELEASE_BINDING_PATH','SITE_RELEASE_BINDING_SHA256','CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID','PRODUCTION_APPROVED','OWNERSHIP_VERIFIED','INDEXNOW_ENABLED','INDEXNOW_KEY','PUBLIC_APPROVED')
def safe_path(path):
 p=Path(path).absolute()
 for x in [p,*p.parents]:require(not x.is_symlink(),'Symlink path forbidden')
 return p.resolve()
def inventory(root):
 root=safe_path(root);require(root.is_dir(),'Regular directory required');result={}
 for p in root.rglob('*'):
  require(not p.is_symlink(),'Symlink file forbidden')
  require(p.is_dir()or p.is_file(),'Nonregular output forbidden')
  if p.is_file():result[p.relative_to(root).as_posix()]=p.read_bytes()
 return result
def private_environment(env=None):
 env=dict(os.environ if env is None else env)
 for key in FORBIDDEN_ENV:require(key not in env,'Private build boundary rejects environment: '+key)
 require('SITE_FACTORY_REVISION'not in env,'Private source rejects revision environment')
 env['ASTRO_TELEMETRY_DISABLED']='1';env['PYTHONDONTWRITEBYTECODE']='1';return env

def regular(path):
 p=safe_path(path);require(p.is_file(),'Regular file required');return p.read_bytes()
def read_contract():
 raw=regular(ROOT/'production-contract.json');require(digest(raw)==CONTRACT_SHA,'Production contract changed');c=json.loads(raw)
 require(c['repository']=='joseungil-kr/fwith-site-factory'and c['hostname']==HOST and c['origin']==ORIGIN and c['privateSourceRevision']==SOURCE,'Fixed target/source changed')
 require(c['sourceRoot']=='site-factory/hwasun-flower'and c['productionRoot']=='scripts/direct-hwasun/production-release'and c['successorBranch']=='source/hwasun-production-preparation-20261017','Fixed roots/branch changed')
 require(c['indexRoutes']==['/']and c['productionOutputFiles']==15 and c['bodyChangesAllowed']==[]and c['facilityPages']=='HOLD_4'and c['emptyHeaders']=='/*\n','Bounded output scope changed')
 require(c['approval']['dedicatedPublicProofGenerationAndApplication']is True and c['approval']['submitHomeOnlyAfterDeploymentVerification']is False and c['approval']['submissionStageSeparate']is True and c['approval']['hostname']==HOST,'Dedicated approval absent')
 require(c['productionBuildEnabled']is True and c['providerNetworkOperationsImplemented']is False and c['indexNowPostImplemented']is False,'Build/network boundary changed')
 require(len(c['sourceFiles'])==47 and len({r['path']for r in c['sourceFiles']})==47 and len(c['privateOutputs'])==11,'Frozen source/output denominator changed')
 for key in ['independentReview','sourceSaveVerification','actualPrivateReview','keylessLocalReview']:
  e=c[key];require(digest(e['rawUTF8'].encode())==e['sha256'],'Embedded reviewed evidence changed')
 review=json.loads(c['independentReview']['rawUTF8']);saved=json.loads(c['sourceSaveVerification']['rawUTF8']);actual=json.loads(c['actualPrivateReview']['rawUTF8']);keyless=json.loads(c['keylessLocalReview']['rawUTF8'])
 require(review['verdict']=='ACCEPTED_LOCAL_STATIC_IMPLEMENTATION_ONLY'and review['mustFix']==[]and review['sourceFiles']==47 and review['sourceManifestSHA256']==c['sourceManifestSHA256']and review['acceptedCopyManifestSHA256']==c['copyManifestSHA256'],'Independent local review scope changed')
 require(saved['sourceCommit']==SOURCE and saved['verdict']=='ACCEPTED_SOURCE47_SAVE_AND_READBACK_ONLY'and saved['mustFix']==[]and saved['freshReadbackFileCount']==47 and saved['allReadbackBytesSHA256GitBlobMatchAccepted']is True and saved['allOutputBytesEqualIndependentAccepted']is True and saved['acceptedStaticManifestSHA256']==c['independentReviewManifestSHA256'],'Source47 independent readback evidence changed')
 require(c['actualPrivateReview']['sha256']=='d7d6ec210e0e36cd6cdeb8d1688e334e8d577de87baeaf44abf17f475bc5e0c3'and c['actualPrivateReview']['manifestSHA256']=='9b3d45e9e8d3447c9d63e6aa303c8e48842d74489785628a234a6d37b7fe98bc'and actual['verdict']=='ACCEPTED_ACTUAL_PRIVATE_QA_ARTIFACT_AND_ALL42_SCREENSHOTS_ONLY'and actual['sourceRevision']==SOURCE and actual['runId']==38966728208 and actual['artifactId']==12074813077 and actual['visualReview']['originalPNGs']==42 and actual['mustFix']==[],'Actual private42 acceptance changed')
 require(c['keylessLocalReview']['sha256']=='7949d79347e897f496dfa12128f930e1da5ecdab87247fd4d0ebf4332265647d'and c['keylessLocalReview']['manifestSHA256']=='7944fd62b23aeb33a37b21eb9e3d2513d3c0f990c7128be12aa05fec90d371c5'and keyless['verdict']=='ACCEPTED_EXACT_ADAPTER5_AND_LOCAL_KEYLESS_OUTPUT13_ONLY'and keyless['sourceRevision']==SOURCE and keyless['mustFix']==[],'Local keyless13 acceptance changed')
 require(c['customerInvariants']['shippingKRW']is None and c['customerInvariants']['referenceSumsKRW']==[None]*4 and c['customerInvariants']['hospitalNoticeLocations']==2 and c['facilityPageCount']==4,'Hospital and unknown-cost boundary changed')
 m=c['socialMetadata'];require(m['canonicalURL']==ORIGIN+'/'and m['imagePath']=='/images/products/B201.jpg'and m['expectedTagCount']==14 and m['notFoundSocialTags']==0,'Social scope changed')
 return c

def check_source(source):
 c=read_contract();source=safe_path(source);expected={r['path']:r for r in c['sourceFiles']};actual=set()
 for p in source.rglob('*'):
  rel=p.relative_to(source)
  if len(rel.parts)>=2 and rel.parts[:2]in [('candidate','node_modules'),('candidate','dist'),('candidate','.astro'),('candidate','evidence')]:continue
  if len(rel.parts)==4 and rel.parts[:3]==('candidate','scripts','__pycache__'):
   modules={Path(name).stem for name in expected if name.startswith('candidate/scripts/')and name.endswith('.py')}
   if any(re.fullmatch(re.escape(module)+r'\.cpython-[0-9]+(?:\.opt-[0-9]+)?\.pyc',rel.name)for module in modules):
    require(not p.is_symlink()and p.is_file(),'Unexpected compiled cache type');continue
  require(not p.is_symlink()and(p.is_dir()or p.is_file()),'Nonregular source input')
  if p.is_file():actual.add(rel.as_posix())
 require(actual==set(expected),'Exact source47 inventory mismatch')
 for name,row in expected.items():
  rel=Path(name);require(not rel.is_absolute()and '..'not in rel.parts and '\\'not in name,'Unsafe source path')
  raw=regular(source/rel);require(len(raw)==row['bytes']and digest(raw)==row['sha256']and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['gitBlobSHA'],'Source47 bytes changed: '+name)
 return {'verifiedSourceFiles':47,'sourceBytesUnchanged':True}

def paths(source,output=None,new=False,evidence=None):
 source=safe_path(source);require(not source.is_relative_to(ROOT)and not ROOT.is_relative_to(source),'Source and adapter must be separate')
 if output is not None:
  output=safe_path(output)
  for root in [source,ROOT]:require(not output.is_relative_to(root)and not root.is_relative_to(output),'Output must be outside source and adapter')
  if new:require(not output.exists(),'Destination already exists')
 if evidence is not None:
  evidence=safe_path(evidence);require(not evidence.exists(),'Evidence directory already exists')
  for root in [source,ROOT,output]:
   if root is not None:require(not evidence.is_relative_to(root)and not root.is_relative_to(evidence),'Evidence must be separate')
 return source,output,evidence

def verify_inputs(source):
 private_environment();c=read_contract();proof(c);source,_,_=paths(source);result=check_source(source);private=inventory(source/'candidate/dist')
 require({n:{'bytes':len(d),'sha256':digest(d)}for n,d in private.items()}==c['privateOutputs'],'Private output differs from accepted exact11')
 for name,row in c['htmlBaseline'].items():
  prefix,body=private[name].split(b'<body',1);require(prefix.decode()==row['prefixUTF8']and digest(b'<body'+body)==row['bodySHA256'],'HTML prefix/body baseline changed')
 return source,c,private,result
def proof(c):
 row=c['dedicatedPublicProof'];raw=regular(ROOT/row['inputFile'])
 require(row['inputFile']=='hwasun-indexnow-proof.txt' and len(raw)==row['bytes']==33 and digest(raw)==row['sha256'],'Dedicated public proof bytes changed')
 require(re.fullmatch(rb'[0-9a-f]{32}\n',raw)is not None,'Dedicated proof format changed')
 key=raw[:-1].decode();require(row['path']=='/'+key+'.txt','Proof path/key mismatch')
 return row,raw

def revision(value):
 require(type(value)is str and re.fullmatch('[0-9a-f]{40}',value)is not None,'Full assembly revision required');return value

class Metadata(HTMLParser):
 def __init__(self,text):
  super().__init__();self.meta={};self.canonical=[];self.h1=0;self.scripts=0;self.feed(text)
 def handle_starttag(self,tag,attrs):
  values=dict(attrs);require(len(values)==len(attrs),'Duplicate HTML attribute')
  if tag=='meta':
   key=values.get('name',values.get('property'))
   if key:require(key not in self.meta,'Duplicate metadata');self.meta[key]=values.get('content')
  if tag=='link'and values.get('rel')=='canonical':self.canonical.append(values.get('href'))
  if tag=='h1':self.h1+=1
  if tag=='script':self.scripts+=1
class SocialMetadata(HTMLParser):
 def __init__(self,text):
  super().__init__();self.social=[];self.descriptions=[];self.titles=[];self.in_title=False;self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);require(len(a)==len(attrs),'Duplicate HTML attributes')
  if tag=='title':self.titles.append('');self.in_title=True
  if tag=='meta':
   if a.get('name')=='description':self.descriptions.append(a.get('content',''))
   key=a.get('property',a.get('name',''))
   if key.startswith(('og:','twitter:')):self.social.append(('property'if 'property'in a else'name',key,a.get('content','')))
 def handle_endtag(self,tag):
  if tag=='title':self.in_title=False
 def handle_data(self,data):
  if self.in_title:self.titles[-1]+=data

def social_values(c,private):
 doc=SocialMetadata(private['index.html'].decode());require(len(doc.titles)==len(doc.descriptions)==1 and not doc.social,'One reviewed title/description and no inherited social tags required')
 m=c['socialMetadata'];require(m['homeOnly']is True and m['type']=='website'and m['locale']=='ko_KR'and m['imageWidth']==m['imageHeight']==500 and m['twitterCard']=='summary','Exact social image/card contract required')
 require(digest(private[m['imagePath'].lstrip('/')])==m['imageSHA256'],'Approved existing social image changed')
 title,description=doc.titles[0],doc.descriptions[0];image=ORIGIN+m['imagePath'];alt=m['imageAlt']
 return [('property','og:type','website'),('property','og:locale','ko_KR'),('property','og:title',title),('property','og:description',description),('property','og:url',ORIGIN+'/'),('property','og:image',image),('property','og:image:width','500'),('property','og:image:height','500'),('property','og:image:alt',alt),('name','twitter:card','summary'),('name','twitter:title',title),('name','twitter:description',description),('name','twitter:image',image),('name','twitter:image:alt',alt)]

RELEASE_KEYS={'schemaVersion','repository','sourceBranch','sourceRoot','revision','controlRevision','runId','origin','worker','indexable','bindingSha256','sourceContractSha256','files'}
def release_manifest(files,assembly_revision,control_revision,run_id,binding_sha):
 c=read_contract();revision(assembly_revision);revision(control_revision)
 require(type(run_id)is str and re.fullmatch('[1-9][0-9]*',run_id),'Actual runId string required')
 require(type(binding_sha)is str and re.fullmatch('[0-9a-f]{64}',binding_sha),'Full QA binding hash required')
 require(type(files)is dict and set(files)==set(c['productionOutputPaths'])and len(files)==15 and all(type(v)is str and re.fullmatch('[0-9a-f]{64}',v)for v in files.values()),'Exact output15 manifest required')
 require(set(c['releaseManifest']['keys'])==RELEASE_KEYS and c['releaseManifest']['publicDeploymentAuthorization']is False,'Exact reused release manifest schema required')
 return dict(schemaVersion=1,repository=c['repository'],sourceBranch=c['successorBranch'],sourceRoot=c['sourceRoot'],revision=assembly_revision,controlRevision=control_revision,runId=run_id,origin=ORIGIN,worker=c['workerCandidate'],indexable=True,bindingSha256=binding_sha,sourceContractSha256=CONTRACT_SHA,files=files)
def validate_release_manifest(value,files,assembly_revision,control_revision,run_id,binding_sha):
 expected=release_manifest(files,assembly_revision,control_revision,run_id,binding_sha)
 require(type(value)is dict and set(value)==RELEASE_KEYS and json.dumps(value,sort_keys=True)==json.dumps(expected,sort_keys=True),'Release manifest identity/schema mismatch');return value
def release_manifest_bytes(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')

def transformed_head(prefix,route,c,private,assembly_revision):
 require(route in FILES.values(),'Unknown route');old='<meta name="robots" content="noindex,nofollow">'
 require(prefix.count(old)==1 and prefix.count('</head>')==1 and 'rel="canonical"'not in prefix and 'site-factory-'not in prefix,'Unexpected private head')
 robots='index,follow'if route=='/'else'noindex,nofollow'
 after=prefix.replace(old,f'<meta name="robots" content="{robots}">',1)
 extra=f'<meta name="site-factory-revision" content="{assembly_revision}"><meta name="site-factory-private-source-revision" content="{SOURCE}"><meta name="site-factory-release-state" content="production-candidate">'
 if route=='/':
  extra+=f'<link rel="canonical" href="{ORIGIN}/">'
  extra+=''.join('<meta '+kind+'="'+key+'" content="'+html.escape(value,quote=True)+'">'for kind,key,value in social_values(c,private))
 return after.replace('</head>',extra+'</head>',1)
def expected_output(c,private,assembly_revision):
 revision(assembly_revision);output=dict(private)
 for name,route in FILES.items():
  prefix,body=private[name].split(b'<body',1);output[name]=transformed_head(prefix.decode(),route,c,private,assembly_revision).encode()+b'<body'+body
 output['robots.txt']=f'User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap-index.xml\n'.encode()
 output['sitemap-index.xml']=f'<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>{ORIGIN}/sitemap-0.xml</loc></sitemap></sitemapindex>\n'.encode()
 output['sitemap-0.xml']=f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{ORIGIN}/</loc></url></urlset>\n'.encode()
 row,raw=proof(c);output[row['path'][1:]]=raw;output['_headers']=c['emptyHeaders'].encode()
 require(len(output)==15 and sorted(output)==c['productionOutputPaths'],'Exact production output15 required');return output

def validate(source,output,assembly_revision):
 revision(assembly_revision);source,output,_=paths(source,output);source,c,private,source_check=verify_inputs(source)
 actual=inventory(output);require(actual==expected_output(c,private,assembly_revision),'Production output differs from exact allowed projection')
 for name,route in FILES.items():
  doc=Metadata(actual[name].decode())
  require(doc.meta.get('site-factory-revision')==assembly_revision and doc.meta.get('site-factory-private-source-revision')==SOURCE and doc.meta.get('site-factory-release-state')=='production-candidate','Source/assembly revision mismatch')
  require(doc.meta.get('robots')==('index,follow'if route=='/'else'noindex,nofollow')and doc.canonical==([ORIGIN+'/']if route=='/'else[]),'Canonical/robots mismatch')
  require(doc.h1==1 and doc.scripts==0,'Unexpected H1 or executable script')
  require(SocialMetadata(actual[name].decode()).social==(social_values(c,private)if route=='/'else[]),'Exact home social14/404 social0 required')
  require(digest(b'<body'+actual[name].split(b'<body',1)[1])==c['htmlBaseline'][name]['bodySHA256'],'Customer body changed')
 row,raw=proof(c)
 return dict(state='PRODUCTION_CANDIDATE_EXACT_OUTPUT_VERIFIED',privateSourceRevision=SOURCE,assemblyRevision=assembly_revision,assemblyCommitExternallyVerified=False,sourceFilesVerified=47,privateFilesVerified=11,productionFilesVerified=15,homeSocialMetadataTagsVerified=14,notFoundSocialTags=0,notFoundRobots='noindex,nofollow',emptyHeadersBytesVerified=3,htmlBodiesByteIdentical=2,staticAssetsByteIdentical=8,indexRoutes=['/'],origin=ORIGIN,proof=dict(path=row['path'],sha256=row['sha256'],bytes=len(raw)),independentLocalReviewManifestSHA256=c['independentReviewManifestSHA256'],productionBrowserVerified=False,publicHTTPVerified=False,providerOwnershipVerified=False,providerWrites=0,IndexNowSubmitted=False,publicationReady=False,facilityPages='HOLD_4',files={n:digest(d)for n,d in sorted(actual.items())})

def build(source,output,assembly_revision):
 revision(assembly_revision);private_environment();source,output,_=paths(source,output,new=True);source,c,private,_=verify_inputs(source);expected=expected_output(c,private,assembly_revision)
 output.mkdir(parents=True)
 for name,data in expected.items():p=output/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 result=validate(source,output,assembly_revision);check_source(source);return result

def build_native(source,output,evidence,assembly_revision):
 import subprocess
 revision(assembly_revision);env=private_environment();source,output,evidence=paths(source,output,new=True,evidence=evidence);read_contract();check_source(source);evidence.mkdir(parents=True);runs=[]
 for command,name in [(['npm','run','build'],'private-build.log'),(['npm','test'],'private-test.log')]:
  with(evidence/name).open('wb')as log:r=subprocess.run(command,cwd=source/'candidate',env=env,stdout=log,stderr=subprocess.STDOUT)
  runs.append({'command':command,'exitCode':r.returncode,'log':name});require(r.returncode==0,'Private regression failed: '+name)
 result=build(source,output,assembly_revision);result['nativeBuildCommands']=runs;result['checkedAtUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();save(evidence/'production-result.json',result);return result
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['verify-inputs','build','validate','build-native','publish','indexnow-submit']);p.add_argument('--source');p.add_argument('--output');p.add_argument('--evidence');p.add_argument('--assembly-revision');a=p.parse_args()
 require(a.mode not in ['publish','indexnow-submit'],'Network publication/submission absent; separate reviewed actual-QA/provider/public-HTTP gates required')
 require(a.source,'--source required')
 if a.mode=='verify-inputs':result=verify_inputs(a.source)[3]
 else:
  require(a.output and a.assembly_revision,'--output and --assembly-revision required')
  if a.mode=='build-native':require(a.evidence,'--evidence required');result=build_native(a.source,a.output,a.evidence,a.assembly_revision)
  else:result=build(a.source,a.output,a.assembly_revision)if a.mode=='build'else validate(a.source,a.output,a.assembly_revision)
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
