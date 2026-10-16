"""Real source51/private11 tests; no mocked source or output validator."""
from pathlib import Path
import copy,json,os,shutil,subprocess,sys,tempfile,unittest
sys.dont_write_bytecode=True
import production_adapter as a
REV='45b0062549772dcd64a20eb975a5c05868487fe4' # Existing source60 used as explicit local test input, not an unsaved successor claim.
class ProductionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=Path(os.environ['GURYE_ACCEPTED_SOURCE_DIR']).resolve();a.verify_inputs(cls.original)
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='gurye-production-test-');self.root=Path(self.tmp.name);self.source=self.root/'source';self.source.mkdir()
  _,binding=a.base.contract()
  for row in json.loads(binding['sourceManifestUTF8'])['files']:
   p=self.source/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((self.original/row['path']).read_bytes())
  shutil.copytree(self.original/'candidate/dist',self.source/'candidate/dist');self.output=self.root/'production'
 def tearDown(self):self.tmp.cleanup()
 def cli(self,adapter,*args):
  return subprocess.run([sys.executable,str(adapter/'production_adapter.py'),*args],capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 def test_real_positive_exact15_and_body8asset_parity(self):
  r=a.build(self.source,self.output,REV);self.assertEqual(r,a.validate(self.source,self.output,REV));self.assertEqual(r['productionFilesVerified'],15);self.assertEqual(r['sourceFilesVerified'],51);self.assertEqual(r['htmlBodiesByteIdentical'],2);self.assertEqual(r['staticAssetsByteIdentical'],8);self.assertFalse(r['publicationReady']);self.assertFalse(r['assemblyCommitExternallyVerified'])
  c=a.read_contract();row,proof=a.proof(c);self.assertEqual((self.output/row['path'][1:]).read_bytes(),proof)
  for n in a.base.FILES:
   doc=a.base.Metadata((self.output/n).read_text());self.assertEqual(doc.meta['site-factory-revision'],REV);self.assertEqual(doc.meta['site-factory-private-source-revision'],a.SOURCE);self.assertNotIn('site-factory-release-revision',doc.meta)
  for n in a.base.FILES:self.assertEqual((self.source/'candidate/dist'/n).read_bytes().split(b'<body',1)[1],(self.output/n).read_bytes().split(b'<body',1)[1])
 def test_metadata_proof_body_and_asset_mutations_rejected(self):
  a.build(self.source,self.output,REV);baseline=a.base.inventory(self.output);proof=a.read_contract()['dedicatedPublicProof']['path'][1:]
  changes=[('index.html',b'index,follow',b'noindex,nofollow'),('index.html',REV.encode(),b'0'*40),('index.html',a.SOURCE.encode(),b'1'*40),('index.html',b'production-candidate',b'offline-inspection-only'),('index.html',b'https://gurye.fwith.kr/',b'https://gokseong.fwith.kr/'),('index.html',b'rel="canonical"',b'rel="alternate"'),('index.html',b'</head>',b'<script>bad</script></head>'),('index.html','20,000'.encode(),'10,000'.encode()),('404.html',b'noindex,follow',b'index,follow'),('404.html',b'</head>',b'<link rel="canonical" href="/"></head>'),('robots.txt',b'Allow: /',b'Disallow: /'),('sitemap-index.xml',b'sitemap-0.xml',b'sitemap-orphan.xml'),('sitemap-0.xml',b'https://gurye.fwith.kr/',b'https://gurye.fwith.kr/facility/'),(proof,b'\n',b''),('images/products/B201.jpg',b'',b'bad')]
  for n,old,new in changes:
   with self.subTest(file=n,old=old):
    changed=baseline[n].replace(old,new,1);self.assertNotEqual(changed,baseline[n]);(self.output/n).write_bytes(changed)
    with self.assertRaises(ValueError):a.validate(self.source,self.output,REV)
    (self.output/n).write_bytes(baseline[n])
 def test_extra_and_missing_output_files_rejected(self):
  a.build(self.source,self.output,REV)
  for n in ['foreign-proof.txt','facility/index.html','sitemap-hidden.xml','_worker.js','.hidden','package.json','evidence/report.json']:
   with self.subTest(n=n):
    p=self.output/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('bad')
    with self.assertRaises(ValueError):a.validate(self.source,self.output,REV)
    p.unlink()
  p=self.output/'robots.txt';p.unlink()
  with self.assertRaises(ValueError):a.validate(self.source,self.output,REV)
 def test_original_source_and_private_dist_mutations_rejected(self):
  for n in ['candidate/src/layouts/BaseLayout.astro','candidate/dist/index.html']:
   p=self.source/n;before=p.read_bytes();p.write_bytes(before+b'\n')
   with self.assertRaises(ValueError):a.build(self.source,self.output,REV)
   p.write_bytes(before);self.assertFalse(self.output.exists())
  for n in ['candidate/src/evidence/extra.py','candidate/src/dist/extra.py','inputs/unreviewed.txt']:
   p=self.source/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('bad')
   with self.assertRaises(ValueError):a.build(self.source,self.output,REV)
   p.unlink()
 def test_foreign_env_and_invalid_revision(self):
  for k in a.base.FORBIDDEN_ENV:
   with self.subTest(k=k),self.assertRaises(ValueError):a.base.private_environment({k:'set'})
  for v in ['',None,'short','A'*40,'1'*39,'../'+'f'*40]:
   with self.assertRaises(ValueError):a.build(self.source,self.output,v)
  self.assertFalse(self.output.exists())
 def test_revision_must_match_both_output_documents(self):
  a.build(self.source,self.output,REV)
  with self.assertRaises(ValueError):a.validate(self.source,self.output,'f'*40)
 def test_output_paths_and_existing_output_rejected(self):
  for output in [self.source,self.source/'out',a.ROOT/'out',a.KEYLESS/'out',self.source.parent]:
   with self.assertRaises(ValueError):a.build(self.source,output,REV)
  a.build(self.source,self.output,REV)
  with self.assertRaises(ValueError):a.build(self.source,self.output,REV)
 def test_source_output_and_proof_symlinks_rejected(self):
  link=self.root/'source-link';link.symlink_to(self.source,target_is_directory=True)
  with self.assertRaises(ValueError):a.build(link,self.output,REV)
  link=self.root/'output-link';link.symlink_to(self.root/'absent',target_is_directory=True)
  with self.assertRaises(ValueError):a.build(self.source,link,REV)
  a.build(self.source,self.output,REV);p=self.output/'index.html';p.unlink();p.symlink_to(self.source/'candidate/dist/index.html')
  with self.assertRaises(ValueError):a.validate(self.source,self.output,REV)
 def test_dependency_and_proof_tamper_rejected_by_real_cli(self):
  for n in ['keyless-release/gurye_adapter.py','keyless-release/private_qa/qa_control.py','keyless-release/bounded-contract.json','production-release/production-contract.json','production-release/gurye-indexnow-proof.txt']:
   target=self.root/('clone-'+n.replace('/','-'));shutil.copytree(a.ROOT.parent,target,ignore=shutil.ignore_patterns('__pycache__'))
   p=target/n;p.write_bytes(p.read_bytes()+b'\n');r=self.cli(target/'production-release','build','--source',str(self.source),'--output',str(self.output),'--assembly-revision',REV)
   self.assertNotEqual(r.returncode,0);self.assertFalse(self.output.exists())
 def test_nested_source_rejected_before_native_commands(self):
  target=self.root/'nested';shutil.copytree(a.ROOT.parent,target,ignore=shutil.ignore_patterns('__pycache__'))
  nested=target/'production-release/nested-source';shutil.copytree(self.source,nested,ignore=shutil.ignore_patterns('dist'))
  logs=self.root/'no-logs';r=self.cli(target/'production-release','build-native','--source',str(nested),'--output',str(self.output),'--evidence',str(logs),'--assembly-revision',REV)
  self.assertNotEqual(r.returncode,0);self.assertIn('must be separate',r.stderr);self.assertFalse(logs.exists());self.assertFalse(self.output.exists());self.assertFalse((nested/'candidate/dist').exists());self.assertFalse((nested/'candidate/evidence').exists())
 def test_unreviewed_dependency_path_rejected(self):
  target=self.root/'extra';shutil.copytree(a.ROOT.parent,target,ignore=shutil.ignore_patterns('__pycache__'));p=target/'keyless-release/nested/__pycache__/unexpected.py';p.parent.mkdir(parents=True);p.write_text('bad')
  r=self.cli(target/'production-release','verify-inputs','--source',str(self.source));self.assertNotEqual(r.returncode,0);self.assertIn('Unexpected keyless dependency',r.stderr)
 def test_network_modes_remain_absent(self):
  for mode in ['publish','indexnow-submit']:
   r=self.cli(a.ROOT,mode);self.assertNotEqual(r.returncode,0);self.assertIn('Network publication/submission absent',r.stderr)
 def test_invalid_evidence_path_prevents_commands(self):
  for logs in [self.source/'logs',a.ROOT/'logs',self.output/'logs']:
   with self.assertRaises(ValueError):a.build_native(self.source,self.output,logs,REV)
  self.assertFalse(self.output.exists())
 def test_exact_social14_existing_titles_image_and_404_absence(self):
  a.build(self.source,self.output,REV);c=a.read_contract();_,_,_,_,private,_=a.verify_inputs(self.source);expected=a.social_values(c,private);doc=a.SocialMetadata((self.output/'index.html').read_text());self.assertEqual(doc.social,expected);self.assertEqual(len(expected),14);self.assertEqual(a.SocialMetadata((self.output/'404.html').read_text()).social,[])
  self.assertEqual(dict((key,value)for _,key,value in expected)['og:url'],'https://gurye.fwith.kr/');self.assertEqual(dict((key,value)for _,key,value in expected)['og:image'],dict((key,value)for _,key,value in expected)['twitter:image']);self.assertEqual(c['socialMetadata']['imageWidth'],500);self.assertEqual(c['socialMetadata']['imageHeight'],500)
  p=self.output/'index.html';original=p.read_bytes()
  for kind,key,value in expected:
   tag=('<meta '+kind+'="'+key+'" content="'+a.html.escape(value,quote=True)+'">').encode();self.assertEqual(original.count(tag),1)
   for changed in [original.replace(tag,b'',1),original.replace(tag,tag+tag,1),original.replace(tag,tag.replace(b'content="',b'content="wrong-',1),1)]:
    p.write_bytes(changed)
    with self.assertRaises(ValueError):a.validate(self.source,self.output,REV)
   p.write_bytes(original)
  p=self.output/'404.html';original=p.read_bytes();p.write_bytes(original.replace(b'</head>',b'<meta property="og:url" content="https://gurye.fwith.kr/"></head>'))
  with self.assertRaises(ValueError):a.validate(self.source,self.output,REV)
 def test_empty_headers_has_no_added_rules(self):
  a.build(self.source,self.output,REV);p=self.output/'_headers';self.assertEqual(p.read_bytes(),b'/*\n')
  for data in [b'',b'/*\n  X-Robots-Tag: noindex\n',b'/*\n  Access-Control-Allow-Origin: *\n',b'/*\r\n']:
   p.write_bytes(data)
   with self.assertRaises(ValueError):a.validate(self.source,self.output,REV)
 def test_reused_release_manifest_exact_schema_and_actual_identifiers(self):
  result=a.build(self.source,self.output,REV);files=result['files'];control='c'*40;run='123456789';binding='d'*64;m=a.release_manifest(files,REV,control,run,binding);self.assertEqual(set(m),a.RELEASE_KEYS);self.assertEqual(m['sourceContractSha256'],a.CONTRACT_SHA);self.assertEqual(m['sourceBranch'],'source/gurye-production-metadata-preparation-20261016');self.assertEqual(a.validate_release_manifest(m,files,REV,control,run,binding),m)
  raw=a.release_manifest_bytes(m);self.assertEqual(raw,(json.dumps(m,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode());self.assertEqual(json.loads(raw),m)
  for key in m:
   for mode in ['delete','wrong']:
    changed=copy.deepcopy(m)
    if mode=='delete':changed.pop(key)
    else:changed[key]='wrong'
    with self.assertRaises(ValueError):a.validate_release_manifest(changed,files,REV,control,run,binding)
  changed=copy.deepcopy(m);changed['extra']=True
  with self.assertRaises(ValueError):a.validate_release_manifest(changed,files,REV,control,run,binding)
  for args in [(files,'local-inspection',control,run,binding),(files,REV,'short',run,binding),(files,REV,control,'0',binding),(files,REV,control,123,binding),(files,REV,control,run,'short'),({},REV,control,run,binding)]:
   with self.assertRaises(ValueError):a.release_manifest(*args)
if __name__=='__main__':unittest.main()
