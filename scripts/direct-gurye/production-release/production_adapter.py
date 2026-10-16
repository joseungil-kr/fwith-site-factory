"""Exact Gurye production candidate projection; no provider or submission client.

The original source51 and keyless5 stay immutable. Actual commit ownership,
Actions evidence, provider state and public HTTP remain separate release gates.
"""
from pathlib import Path
import argparse, datetime, hashlib, html, json, re, sys
from html.parser import HTMLParser
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
KEYLESS=ROOT.parent/'keyless-release'
CONTRACT_SHA='0f6c1c070405afbf7cc5d6a51191caf8664c868f9c87f07ac1167efac40e33a2'
SOURCE='557324cfdea14a5dec3354f2124cc887e2ff7555'
ASSEMBLY56='faad1dcf40b879bf03075967d1a6e482a87d54ea'
ORIGIN='https://gurye.fwith.kr'
HOST='gurye.fwith.kr'
def require(ok,message):
 if not ok:raise ValueError(message)
def digest(data):return hashlib.sha256(data).hexdigest()
def regular(path):
 p=Path(path).absolute()
 for entry in [p,*p.parents]:require(not entry.is_symlink(),'Symlink path forbidden')
 require(p.is_file(),'Regular file required');return p.read_bytes()
def read_contract():
 raw=regular(ROOT/'production-contract.json');require(digest(raw)==CONTRACT_SHA,'Production contract changed');c=json.loads(raw)
 require(c['repository']=='joseungil-kr/fwith-site-factory' and c['hostname']==HOST and c['origin']==ORIGIN,'Foreign fixed target')
 require(c['privateSourceRevision']==SOURCE and c['keylessAssemblyRevision']==ASSEMBLY56,'Frozen source identity changed')
 require(c['sourceRoot']=='site-factory/gurye-flower' and c['keylessRoot']=='scripts/direct-gurye/keyless-release' and c['productionRoot']=='scripts/direct-gurye/production-release','Root contract changed')
 require(c['indexRoutes']==['/'] and c['productionOutputFiles']==15 and c['bodyChangesAllowed']==[] and c['facilityPages']=='HOLD','Bounded home scope changed')
 require(c['approval']['dedicatedPublicProofGenerationAndApplication']is True and c['approval']['submitHomeOnlyAfterDeploymentVerification']is True,'Dedicated approval absent')
 require(c['successorBranch']=='source/gurye-production-metadata-preparation-20261016' and c['priorProductionAssemblyRevision']=='45b0062549772dcd64a20eb975a5c05868487fe4' and c['emptyHeaders']=='/*\n','Successor/empty header contract changed')
 require(c['socialMetadata']['canonicalURL']==ORIGIN+'/' and c['socialMetadata']['imagePath']=='/images/products/B201.jpg' and c['socialMetadata']['expectedTagCount']==14 and c['socialMetadata']['notFoundSocialTags']==0,'Social scope changed')
 require(c['productionBuildEnabled']is True and c['providerNetworkOperationsImplemented']is False and c['indexNowPostImplemented']is False,'Build/network boundary changed')
 require(len(c['keylessFiles'])==5 and len({r['path']for r in c['keylessFiles']})==5,'Keyless inventory changed')
 for row in c['keylessFiles']:
  rel=Path(row['path']);require(not rel.is_absolute() and '..'not in rel.parts,'Dependency path escape')
  raw=regular(KEYLESS/rel);require(len(raw)==row['bytes'] and digest(raw)==row['sha256'],'Reviewed keyless dependency changed: '+row['path'])
 for p in KEYLESS.rglob('*'):
  require(not p.is_symlink() and (p.is_file()or p.is_dir()),'Nonregular keyless dependency')
 actual={p.relative_to(KEYLESS).as_posix()for p in KEYLESS.rglob('*')if p.is_file()}
 require(actual=={r['path']for r in c['keylessFiles']},'Unexpected keyless dependency')
 return c
# Verify the complete five-file dependency before executing its code.
read_contract()
sys.path.insert(0,str(KEYLESS))
import gurye_adapter as base

def proof(c):
 row=c['dedicatedPublicProof'];raw=regular(ROOT/row['inputFile'])
 require(row['inputFile']=='gurye-indexnow-proof.txt' and len(raw)==row['bytes']==33 and digest(raw)==row['sha256'],'Dedicated public proof bytes changed')
 require(re.fullmatch(rb'[0-9a-f]{32}\n',raw)is not None,'Dedicated proof format changed')
 key=raw[:-1].decode();require(row['path']=='/'+key+'.txt','Proof path/key mismatch')
 return row,raw

def revision(value):
 require(type(value)is str and re.fullmatch('[0-9a-f]{40}',value)is not None,'Full assembly revision required');return value

def paths(source,output=None,new=False,evidence=None):
 source=base.safe_path(source)
 for root in [ROOT,KEYLESS]:require(not source.is_relative_to(root) and not root.is_relative_to(source),'Source and all adapters must be separate')
 if output is not None:
  output=base.safe_path(output)
  for root in [source,ROOT,KEYLESS]:require(not output.is_relative_to(root) and not root.is_relative_to(output),'Output must be outside source and all adapters')
  if new:require(not output.exists(),'Destination already exists')
 if evidence is not None:
  evidence=base.safe_path(evidence);require(not evidence.exists(),'Evidence directory already exists')
  for root in [source,ROOT,KEYLESS,output]:
   if root is not None:require(not evidence.is_relative_to(root) and not root.is_relative_to(evidence),'Evidence must be separate')
 return source,output,evidence

def verify_inputs(source):
 base.private_environment();c=read_contract();proof(c);source,_,_=paths(source)
 source,k,b,private,result=base.verify_source(source)
 require(c['privateVisualReviewSHA256']==k['privateVisualReview']['resultSHA256'],'Private visual review changed')
 return source,c,k,b,private,result

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

def expected_output(c,k,private,assembly_revision):
 revision(assembly_revision);output=base.expected_output(k,private)
 for name in base.FILES:
  before,body=output[name].split(b'<body',1)
  old=b'<meta name="site-factory-release-state" content="offline-inspection-only">'
  old_revision=('<meta name="site-factory-revision" content="'+SOURCE+'">').encode()
  require(before.count(old)==1 and before.count(old_revision)==1 and b'site-factory-private-source-revision'not in before,'Unexpected offline head')
  new=('<meta name="site-factory-release-state" content="production-candidate"><meta name="site-factory-private-source-revision" content="'+SOURCE+'">').encode()
  new_revision=('<meta name="site-factory-revision" content="'+assembly_revision+'">').encode()
  head=before.replace(old,new,1).replace(old_revision,new_revision,1)
  if name=='index.html':
   require(head.count(b'</head>')==1,'Exact head closing required')
   social=''.join('<meta '+kind+'="'+key+'" content="'+html.escape(value,quote=True)+'">'for kind,key,value in social_values(c,private)).encode()
   head=head.replace(b'</head>',social+b'</head>',1)
  output[name]=head+b'<body'+body
 row,raw=proof(c);output[row['path'][1:]]=raw;output['_headers']=c['emptyHeaders'].encode()
 require(len(output)==15 and sorted(output)==c['productionOutputPaths'],'Exact production output15 required');return output

def validate(source,output,assembly_revision):
 revision(assembly_revision);source,output,_=paths(source,output)
 source,c,k,b,private,source_check=verify_inputs(source)
 actual=base.inventory(output);expected=expected_output(c,k,private,assembly_revision)
 require(actual==expected,'Production output differs from exact allowed projection')
 for name,route in base.FILES.items():
  doc=base.Metadata(actual[name].decode())
  require(doc.meta.get('site-factory-revision')==assembly_revision and doc.meta.get('site-factory-private-source-revision')==SOURCE and doc.meta.get('site-factory-release-state')=='production-candidate','Source/assembly revision mismatch')
  require(doc.meta.get('robots')==('index,follow'if route=='/'else'noindex,follow')and doc.canonical==([ORIGIN+'/']if route=='/'else[]),'Canonical/robots mismatch')
  require(doc.h1==1 and doc.scripts==0,'Unexpected H1 or executable script')
  require(SocialMetadata(actual[name].decode()).social==(social_values(c,private)if route=='/'else[]),'Exact home social14/404 social0 required')
  require(digest(b'<body'+actual[name].split(b'<body',1)[1])==k['htmlBaseline'][name]['bodySHA256'],'Customer body changed')
 row,raw=proof(c)
 return {'state':'PRODUCTION_CANDIDATE_EXACT_OUTPUT_VERIFIED','privateSourceRevision':SOURCE,'keylessAssemblyRevision':ASSEMBLY56,'assemblyRevision':assembly_revision,'assemblyCommitExternallyVerified':False,'sourceFilesVerified':source_check['verifiedSourceFiles'],'keylessFilesVerified':5,'privateFilesVerified':11,'productionFilesVerified':15,'homeSocialMetadataTagsVerified':14,'notFoundSocialTags':0,'emptyHeadersBytesVerified':3,'htmlBodiesByteIdentical':2,'staticAssetsByteIdentical':8,'indexRoutes':['/'],'origin':ORIGIN,'proof':{'path':row['path'],'sha256':row['sha256'],'bytes':len(raw)},'dedicatedPublicProofApprovalVerifiedAtUTC':c['approval']['verifiedAtUTC'],'privateVisualReviewSHA256':c['privateVisualReviewSHA256'],'productionBrowserVerified':False,'publicHTTPVerified':False,'providerOwnershipVerified':False,'providerWrites':0,'IndexNowSubmitted':False,'publicationReady':False,'facilityPages':'HOLD','files':{n:digest(d)for n,d in sorted(actual.items())}}

def build(source,output,assembly_revision):
 revision(assembly_revision);base.private_environment();source,output,_=paths(source,output,new=True)
 source,c,k,b,private,_=verify_inputs(source);expected=expected_output(c,k,private,assembly_revision)
 output.mkdir(parents=True)
 for name,data in expected.items():
  p=output/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 result=validate(source,output,assembly_revision);base.q.check_source_files(source,b,True);return result

def build_native(source,output,evidence,assembly_revision):
 import subprocess
 revision(assembly_revision);env=base.private_environment();source,output,evidence=paths(source,output,new=True,evidence=evidence)
 c=read_contract();proof(c);_,b=base.contract();base.q.check_source_files(source,b,True)
 evidence.mkdir(parents=True);runs=[]
 for command,name in [(['npm','run','build'],'private-build.log'),(['npm','test'],'private-test.log')]:
  with(evidence/name).open('wb')as log:r=subprocess.run(command,cwd=source/'candidate',env=env,stdout=log,stderr=subprocess.STDOUT)
  runs.append({'command':command,'exitCode':r.returncode,'log':name});require(r.returncode==0,'Private regression failed: '+name)
 result=build(source,output,assembly_revision);result['nativeBuildCommands']=runs
 result['checkedAtUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();base.q.save(evidence/'production-result.json',result);return result

def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['verify-inputs','build','validate','build-native','publish','indexnow-submit']);p.add_argument('--source');p.add_argument('--output');p.add_argument('--evidence');p.add_argument('--assembly-revision');a=p.parse_args()
 require(a.mode not in ['publish','indexnow-submit'],'Network publication/submission absent; separate reviewed actual-QA/provider/public-HTTP gates required')
 require(a.source,'--source required')
 if a.mode=='verify-inputs':result=verify_inputs(a.source)[5]
 else:
  require(a.output and a.assembly_revision,'--output and --assembly-revision required')
  if a.mode=='build-native':require(a.evidence,'--evidence required');result=build_native(a.source,a.output,a.evidence,a.assembly_revision)
  else:result=build(a.source,a.output,a.assembly_revision)if a.mode=='build'else validate(a.source,a.output,a.assembly_revision)
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
