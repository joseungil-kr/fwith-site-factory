"""Exact Gurye production candidate projection; no provider or submission client.

The original source51 and keyless5 stay immutable. Actual commit ownership,
Actions evidence, provider state and public HTTP remain separate release gates.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, re, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
KEYLESS=ROOT.parent/'keyless-release'
CONTRACT_SHA='539a58756cae4fa7f5e4a5c7ccf57fb8bd1879a8956f46b9dc1ef44b2f0d37e9'
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
 require(c['indexRoutes']==['/'] and c['productionOutputFiles']==14 and c['bodyChangesAllowed']==[] and c['facilityPages']=='HOLD','Bounded home scope changed')
 require(c['approval']['dedicatedPublicProofGenerationAndApplication']is True and c['approval']['submitHomeOnlyAfterDeploymentVerification']is True,'Dedicated approval absent')
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

def expected_output(c,k,private,assembly_revision):
 revision(assembly_revision);output=base.expected_output(k,private)
 for name in base.FILES:
  before,body=output[name].split(b'<body',1)
  old=b'<meta name="site-factory-release-state" content="offline-inspection-only">'
  old_revision=('<meta name="site-factory-revision" content="'+SOURCE+'">').encode()
  require(before.count(old)==1 and before.count(old_revision)==1 and b'site-factory-private-source-revision'not in before,'Unexpected offline head')
  new=('<meta name="site-factory-release-state" content="production-candidate"><meta name="site-factory-private-source-revision" content="'+SOURCE+'">').encode()
  new_revision=('<meta name="site-factory-revision" content="'+assembly_revision+'">').encode()
  output[name]=before.replace(old,new,1).replace(old_revision,new_revision,1)+b'<body'+body
 row,raw=proof(c);output[row['path'][1:]]=raw
 require(len(output)==14,'Exact production output14 required');return output

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
  require(digest(b'<body'+actual[name].split(b'<body',1)[1])==k['htmlBaseline'][name]['bodySHA256'],'Customer body changed')
 row,raw=proof(c)
 return {'state':'PRODUCTION_CANDIDATE_EXACT_OUTPUT_VERIFIED','privateSourceRevision':SOURCE,'keylessAssemblyRevision':ASSEMBLY56,'assemblyRevision':assembly_revision,'assemblyCommitExternallyVerified':False,'sourceFilesVerified':source_check['verifiedSourceFiles'],'keylessFilesVerified':5,'privateFilesVerified':11,'productionFilesVerified':14,'htmlBodiesByteIdentical':2,'staticAssetsByteIdentical':8,'indexRoutes':['/'],'origin':ORIGIN,'proof':{'path':row['path'],'sha256':row['sha256'],'bytes':len(raw)},'dedicatedPublicProofApprovalVerifiedAtUTC':c['approval']['verifiedAtUTC'],'privateVisualReviewSHA256':c['privateVisualReviewSHA256'],'productionBrowserVerified':False,'publicHTTPVerified':False,'providerOwnershipVerified':False,'providerWrites':0,'IndexNowSubmitted':False,'publicationReady':False,'facilityPages':'HOLD','files':{n:digest(d)for n,d in sorted(actual.items())}}

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
