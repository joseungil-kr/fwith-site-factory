"""Real accepted source51/dist11 fixtures; no mocked source, output, or validator."""
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile,unittest
import gurye_adapter as a

class AdapterTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=Path(os.environ['GURYE_ACCEPTED_SOURCE_DIR']).resolve();a.verify_source(cls.original)
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='gurye-keyless-test-');self.root=Path(self.tmp.name);self.source=self.root/'source';self.source.mkdir()
  _,binding=a.contract();manifest=json.loads(binding['sourceManifestUTF8'])
  for row in manifest['files']:
   p=self.source/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((self.original/row['path']).read_bytes())
  shutil.copytree(self.original/'candidate/dist',self.source/'candidate/dist');self.output=self.root/'offline'
 def tearDown(self):self.tmp.cleanup()
 def test_real_positive_output_and_revision(self):
  r=a.inspect(self.source,self.output);self.assertEqual(r['offlineFilesVerified'],13);self.assertEqual(r['sourceFilesVerified'],51);self.assertEqual(r['staticAssetsByteIdentical'],8);self.assertIsNone(r['indexNowProof']);self.assertFalse(r['publicationReady']);self.assertEqual(a.validate_output(self.source,self.output),r)
  for name in a.FILES:self.assertEqual((self.source/'candidate/dist'/name).read_bytes().split(b'<body',1)[1],(self.output/name).read_bytes().split(b'<body',1)[1])
 def test_output_mutations_rejected(self):
  a.inspect(self.source,self.output);baseline=a.inventory(self.output)
  mutations=[('index.html',lambda b:b.replace(b'index,follow',b'noindex,nofollow',1)),('index.html',lambda b:b.replace(a.SOURCE.encode(),b'0'*40,1)),('index.html',lambda b:b.replace(b'offline-inspection-only',b'production',1)),('index.html',lambda b:b.replace(b'<link rel="canonical"',b'<link rel="alternate"',1)),('index.html',lambda b:b.replace(b'https://gurye.fwith.kr/',b'https://gokseong.fwith.kr/',1)),('index.html',lambda b:b.replace(b'</head>',b'<link rel="canonical" href="https://gurye.fwith.kr/"></head>',1)),('index.html',lambda b:b.replace(b'</head>',b'<script>alert(1)</script></head>',1)),('index.html',lambda b:b.replace('20,000'.encode(),'10,000'.encode(),1)),('index.html',lambda b:b.replace(b'</body>',b'<p>Unreviewed promise</p></body>',1)),('404.html',lambda b:b.replace(b'noindex,follow',b'index,follow',1)),('404.html',lambda b:b.replace(b'</head>',b'<link rel="canonical" href="https://gurye.fwith.kr/404.html"></head>',1)),('robots.txt',lambda b:b.replace(b'Allow: /',b'Disallow: /',1)),('sitemap-index.xml',lambda b:b.replace(b'sitemap-0.xml',b'sitemap-1.xml',1)),('sitemap-0.xml',lambda b:b.replace(b'https://gurye.fwith.kr/',b'https://gurye.fwith.kr/facility/',1)),('_astro/CopyPage.Cy0efvqa.css',lambda b:b+b'/* changed */'),('images/products/B201.jpg',lambda b:b+b'bad')]
  for name,change in mutations:
   with self.subTest(name=name,mutation=mutations.index((name,change))):
    (self.output/name).write_bytes(change(baseline[name]))
    with self.assertRaises(ValueError):a.validate_output(self.source,self.output)
    (self.output/name).write_bytes(baseline[name])
  for name in ['proof.txt','sitemap-orphan.xml','facility/index.html','_worker.js','.hidden','evidence/forged.json']:
   with self.subTest(extra=name):
    p=self.output/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('unreviewed')
    with self.assertRaises(ValueError):a.validate_output(self.source,self.output)
    p.unlink()
 def test_source_mutations_rejected(self):
  p=self.source/'candidate/src/layouts/BaseLayout.astro';before=p.read_bytes();p.write_bytes(before+b'\n')
  with self.assertRaises(ValueError):a.inspect(self.source,self.output)
  p.write_bytes(before)
  for name in ['candidate/src/evidence/unreviewed.py','candidate/src/dist/unreviewed.py','inputs/extra.txt','.hidden']:
   p=self.source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('bad')
   with self.assertRaises(ValueError):a.inspect(self.source,self.output)
   p.unlink()
  p=self.source/'candidate/dist/index.html';before=p.read_bytes();p.write_bytes(before+b'\n')
  with self.assertRaises(ValueError):a.inspect(self.source,self.output)
  self.assertFalse(self.output.exists())
 def test_environment_and_production_fail_closed(self):
  for key in a.FORBIDDEN_ENV:
   with self.subTest(key=key),self.assertRaises(ValueError):a.private_environment({key:'set'})
  with self.assertRaises(ValueError):a.private_environment({'SITE_FACTORY_REVISION':'0'*40})
  self.assertEqual(a.private_environment({'SITE_FACTORY_REVISION':a.SOURCE})['SITE_FACTORY_REVISION'],a.SOURCE)
  for mode in ['production','indexnow-payload']:
   result=subprocess.run([sys.executable,str(a.ROOT/'gurye_adapter.py'),mode,'--source',str(self.source),'--output',str(self.output)],capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0);self.assertIn('disabled',result.stderr.lower());self.assertFalse(self.output.exists())
 def test_paths_and_symlinks_rejected(self):
  for output in [self.source/'generated',self.source.parent,a.ROOT/'generated']:
   with self.assertRaises(ValueError):a.inspect(self.source,output)
  link=self.root/'source-link';link.symlink_to(self.source,target_is_directory=True)
  with self.assertRaises(ValueError):a.inspect(link,self.output)
  link=self.root/'output-link';link.symlink_to(self.root/'absent',target_is_directory=True)
  with self.assertRaises(ValueError):a.inspect(self.source,link)
  a.inspect(self.source,self.output)
  with self.assertRaises(ValueError):a.inspect(self.source,self.output)
  target=self.output/'index.html';target.unlink();target.symlink_to(self.source/'candidate/dist/index.html')
  with self.assertRaises(ValueError):a.validate_output(self.source,self.output)
 def test_dependency_and_contract_tamper_before_import(self):
  for name in ['private_qa/qa_control.py','private_qa/bindings.json','bounded-contract.json']:
   copy=self.root/('adapter-'+name.replace('/','-'));shutil.copytree(a.ROOT,copy,ignore=shutil.ignore_patterns('__pycache__'))
   p=copy/name;p.write_bytes(p.read_bytes()+b'\n')
   r=subprocess.run([sys.executable,str(copy/'gurye_adapter.py'),'verify-source','--source',str(self.source)],capture_output=True,text=True);self.assertNotEqual(r.returncode,0);self.assertIn('changed',r.stderr.lower())
 def test_head_and_semantic_guards(self):
  c,_=a.contract();prefix=c['htmlBaseline']['index.html']['prefixUTF8']
  for bad in [prefix.replace('noindex,nofollow','index,follow'),prefix.replace('</head>',''),prefix.replace('</head>','<link rel="canonical" href="/"></head>')]:
   with self.assertRaises(ValueError):a.transformed_head(bad,'/')
  with self.assertRaises(ValueError):a.transformed_head(prefix,'/facility/')
  with self.assertRaises(ValueError):a.Metadata('<meta name="robots" content="index"><meta name="robots" content="noindex">')
  with self.assertRaises(ValueError):a.Metadata('<meta name="robots" name="bad" content="index">')
 def test_build_does_not_start_for_bad_inputs(self):
  evidence=self.root/'logs';evidence.mkdir()
  with self.assertRaises(ValueError):a.build_inspection(self.source,self.output,evidence)
  with self.assertRaises(ValueError):a.build_inspection(self.source,self.output,self.source/'bad-logs')
  self.assertFalse(self.output.exists())
 def test_nested_source_rejected_before_build_or_evidence(self):
  adapter=self.root/'nested-adapter';shutil.copytree(a.ROOT,adapter,ignore=shutil.ignore_patterns('__pycache__'))
  nested=adapter/'nested-source';shutil.copytree(self.source,nested,ignore=shutil.ignore_patterns('dist'))
  evidence=self.root/'must-not-create-evidence';before=a.inventory(nested)
  result=subprocess.run([sys.executable,str(adapter/'gurye_adapter.py'),'build-inspection','--source',str(nested),'--output',str(self.output),'--evidence',str(evidence)],capture_output=True,text=True)
  self.assertNotEqual(result.returncode,0);self.assertIn('Source and adapter roots must be separate',result.stderr)
  self.assertFalse(evidence.exists());self.assertFalse(self.output.exists());self.assertFalse((nested/'candidate/dist').exists());self.assertFalse((nested/'candidate/evidence').exists());self.assertEqual(a.inventory(nested),before)

if __name__=='__main__':unittest.main()
