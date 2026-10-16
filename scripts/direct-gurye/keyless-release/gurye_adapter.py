"""Keyless offline metadata inspection, reusing reviewed private QA and Gokseong's bounded-copy pattern.

No network client, publisher, proof generator or IndexNow payload is present.
The accepted source51 and private dist11 remain inputs, never edited by this adapter.
"""
from pathlib import Path
from html.parser import HTMLParser
import argparse,datetime,hashlib,json,os,subprocess,sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
SOURCE='557324cfdea14a5dec3354f2124cc887e2ff7555'
ORIGIN='https://gurye.fwith.kr'
CONTRACT_SHA='a1effa3234cbf8fd900ec086cffb4de09fac7cf85ce0537826f9559769f779b7'
DEPENDENCIES={'qa_control.py':'04aad69ab531a987e0de1b87981dfde328b5783986f1452706fe4b7add1b2e7e','bindings.json':'34b2e8e415e27937681d280a88e9ff8cc4c2a68001243e0bdd6d9b6d6c1e7039'}
for _name,_digest in DEPENDENCIES.items():
 _path=ROOT/'private_qa'/_name
 if _path.is_symlink()or hashlib.sha256(_path.read_bytes()).hexdigest()!=_digest:raise ValueError('Reviewed dependency changed before import: '+_name)
sys.path.insert(0,str(ROOT/'private_qa'))
import qa_control as q
FILES={'index.html':'/','404.html':'/404.html'}
FORBIDDEN_ENV=('SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION','SITE_RELEASE_MODE','SITE_INDEXABLE','SITE_RELEASE_BINDING_PATH','SITE_RELEASE_BINDING_SHA256','CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID','PRODUCTION_APPROVED','OWNERSHIP_VERIFIED','INDEXNOW_ENABLED','INDEXNOW_KEY','PUBLIC_APPROVED')
def require(ok,message):
 if not ok:raise ValueError(message)
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
 for key in FORBIDDEN_ENV:require(not env.get(key),'Offline boundary rejects environment: '+key)
 if env.get('SITE_FACTORY_REVISION'):require(env['SITE_FACTORY_REVISION']==SOURCE,'Foreign source revision environment')
 env['ASTRO_TELEMETRY_DISABLED']='1';env['PYTHONDONTWRITEBYTECODE']='1';return env
def contract():
 for name,digest in DEPENDENCIES.items():require(q.sha((ROOT/'private_qa'/name).read_bytes())==digest,'Reviewed QA dependency changed: '+name)
 raw=(ROOT/'bounded-contract.json').read_bytes();require(q.sha(raw)==CONTRACT_SHA,'Bounded contract changed');c=json.loads(raw)
 b=q.read(ROOT/'private_qa/bindings.json');q.validate_binding(b)
 require(c['sourceRevision']==b['sourceRevision']==SOURCE and c['sourceManifestSHA256']==b['sourceManifestSHA256'],'Frozen source identity mismatch')
 require(c['indexNowProof']is None and c['productionEnabled']is False and c['publicationReady']is False,'Keyless preparation boundary changed')
 require(c['origin']==ORIGIN and c['indexRoutes']==['/'] and c['allowedGeneratedBodyChanges']==[],'Single-home immutable body contract changed')
 v=c['privateVisualReview'];require(q.sha(v['resultUTF8'].encode())==v['resultSHA256']=='7c969ae92547113303d54d1a14d9cb6931857fa63cd5652d220e769cf592373b','Independent visual review changed')
 r=json.loads(v['resultUTF8']);require(r['sourceCommit']==SOURCE and r['combinedPrivateSourceVisualEvidenceAccepted']is True and r['originalBadScreenshotStillFailed']is True and r['publicationReady']is False,'Private visual scope changed')
 require(set(c['htmlBaseline'])==set(FILES) and len(c['staticAssets'])==8,'Baseline denominator changed')
 for name,row in c['htmlBaseline'].items():require(row['privateFileSHA256']==b['expectedDistFiles'][name],'Private HTML baseline mismatch')
 require(c['staticAssets']=={k:v for k,v in b['expectedDistFiles'].items()if k not in {*FILES,'robots.txt'}},'Static baseline mismatch')
 return c,b
def verify_source(source):
 private_environment();source=safe_path(source);c,b=contract()
 require(not source.is_relative_to(ROOT) and not ROOT.is_relative_to(source),'Source and adapter roots must be separate')
 result=q.check_source_files(source,b,True);dist=safe_path(source/'candidate/dist');q.check_dist(dist,b)
 raw=inventory(dist)
 for name,row in c['htmlBaseline'].items():
  prefix,body=raw[name].split(b'<body',1);body=b'<body'+body
  require(prefix.decode()==row['prefixUTF8'] and q.sha(body)==row['bodySHA256'],'HTML prefix/body baseline changed')
 return source,c,b,raw,result
def transformed_head(prefix,route):
 require(route in FILES.values(),'Unknown route');old='<meta name="robots" content="noindex,nofollow">'
 require(prefix.count(old)==1 and prefix.count('</head>')==1 and 'rel="canonical"'not in prefix and 'site-factory-'not in prefix,'Unexpected private head')
 robots='index,follow'if route=='/'else'noindex,follow'
 after=prefix.replace(old,f'<meta name="robots" content="{robots}">',1)
 extra=f'<meta name="site-factory-revision" content="{SOURCE}"><meta name="site-factory-release-state" content="offline-inspection-only">'
 if route=='/':extra+=f'<link rel="canonical" href="{ORIGIN}/">'
 return after.replace('</head>',extra+'</head>',1)
def expected_output(c,private):
 output=dict(private)
 for name,route in FILES.items():
  prefix,body=private[name].split(b'<body',1);output[name]=transformed_head(prefix.decode(),route).encode()+b'<body'+body
 output['robots.txt']=f'User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap-index.xml\n'.encode()
 output['sitemap-index.xml']=f'<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>{ORIGIN}/sitemap-0.xml</loc></sitemap></sitemapindex>\n'.encode()
 output['sitemap-0.xml']=f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{ORIGIN}/</loc></url></urlset>\n'.encode()
 require(len(output)==c['offlineFiles']==13,'Offline output denominator changed');return output
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
def validate_output(source,output):
 source,c,b,private,source_result=verify_source(source);output=safe_path(output);actual=inventory(output);expected=expected_output(c,private)
 require(actual==expected,'Output differs from exact allowed metadata projection')
 bodies={}
 for name,route in FILES.items():
  document=Metadata(actual[name].decode());want='index,follow'if route=='/'else'noindex,follow'
  require(document.meta.get('robots')==want and document.meta.get('site-factory-revision')==SOURCE and document.meta.get('site-factory-release-state')=='offline-inspection-only','Robots/revision/offline marker mismatch')
  require(document.canonical==([ORIGIN+'/']if route=='/'else[]) and document.h1==1 and document.scripts==0,'Canonical/H1/script contract mismatch')
  body=b'<body'+actual[name].split(b'<body',1)[1];require(q.sha(body)==c['htmlBaseline'][name]['bodySHA256'],'Customer body changed');bodies[name]=q.sha(body)
 ns='{http://www.sitemaps.org/schemas/sitemap/0.9}';index=ET.fromstring(actual['sitemap-index.xml']);child=ET.fromstring(actual['sitemap-0.xml'])
 require(index.tag==ns+'sitemapindex' and [x.text for x in index.findall(ns+'sitemap/'+ns+'loc')]==[ORIGIN+'/sitemap-0.xml'],'Sitemap index graph changed')
 require(child.tag==ns+'urlset' and [x.text for x in child.findall(ns+'url/'+ns+'loc')]==[ORIGIN+'/'],'Only home may be indexed')
 return {'state':'KEYLESS_OFFLINE_METADATA_INSPECTION_VERIFIED','sourceRevision':SOURCE,'sourceFilesVerified':source_result['verifiedSourceFiles'],'historicalOriginal132Reverified':False,'privateFilesVerified':11,'offlineFilesVerified':13,'htmlBodiesByteIdentical':bodies,'staticAssetsByteIdentical':8,'sourceBytesUnchanged':True,'indexRoutes':['/'],'origin':ORIGIN,'originOwnershipVerified':False,'canonicalHome':ORIGIN+'/','notFoundCanonical':None,'notFoundRobots':'noindex,follow','revisionRole':'frozen source only; not deployment proof','offlineMarker':'offline-inspection-only','indexNowProof':None,'indexNowPayloadCreated':False,'IndexNowSubmitted':False,'providerWrites':0,'productionEnabled':False,'publicationReady':False,'publicHTTPVerified':False,'facilityPages':'HOLD','offlineBrowserVerified':False,'privateVisualReviewSHA256':c['privateVisualReview']['resultSHA256'],'files':{name:q.sha(data)for name,data in sorted(actual.items())}}
def prepare_paths(source,output):
 source=safe_path(source);output=safe_path(output)
 require(not source.is_relative_to(ROOT) and not ROOT.is_relative_to(source),'Source and adapter roots must be separate')
 require(not output.exists(),'Destination already exists')
 for root in [source,ROOT]:require(not output.is_relative_to(root) and not root.is_relative_to(output),'Output must be outside source and adapter')
 return source,output
def inspect(source,output):
 private_environment();source,output=prepare_paths(source,output);source,c,b,private,_=verify_source(source);expected=expected_output(c,private)
 output.mkdir(parents=True)
 for name,data in expected.items():target=output/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 result=validate_output(source,output);q.check_source_files(source,b,True);return result
def production():raise ValueError('Production disabled: dedicated proof approval and separately reviewed source/control/provider gates are pending')
def indexnow_payload():raise ValueError('No dedicated proof: payload generation and submission are disabled')
def build_inspection(source,output,evidence):
 env=private_environment();source,output=prepare_paths(source,output);evidence=safe_path(evidence)
 require(not evidence.exists(),'Evidence directory already exists')
 for root in [source,output,ROOT]:require(not evidence.is_relative_to(root) and not root.is_relative_to(evidence),'Evidence must be a separate directory')
 c,b=contract();q.check_source_files(source,b,True);evidence.mkdir(parents=True);runs=[]
 for command,name in [(['npm','run','build'],'private-build.log'),(['npm','test'],'private-test.log')]:
  with(evidence/name).open('wb')as log:r=subprocess.run(command,cwd=source/'candidate',env=env,stdout=log,stderr=subprocess.STDOUT)
  runs.append({'command':command,'exitCode':r.returncode,'log':name});require(r.returncode==0,'Private regression failed: '+name)
 result=inspect(source,output);result['privateBuildCommands']=runs;result['checkedAtUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();q.save(evidence/'inspection-result.json',result);return result
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['verify-source','inspect','validate','build-inspection','production','indexnow-payload']);p.add_argument('--source');p.add_argument('--output');p.add_argument('--evidence');args=p.parse_args()
 if args.mode=='production':production()
 if args.mode=='indexnow-payload':indexnow_payload()
 require(args.source,'--source required')
 if args.mode=='verify-source':result=verify_source(args.source)[4]
 else:
  require(args.output,'--output required')
  if args.mode=='build-inspection':require(args.evidence,'--evidence required');result=build_inspection(args.source,args.output,args.evidence)
  else:result=inspect(args.source,args.output)if args.mode=='inspect'else validate_output(args.source,args.output)
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
