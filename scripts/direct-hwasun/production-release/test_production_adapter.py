"""Real source47/private11 tests; no mocked source or output validator."""
from pathlib import Path
import copy,json,os,shutil,subprocess,sys,tempfile,unittest
sys.dont_write_bytecode=True
import production_adapter as a
REV='17703e6e4c8a82f3271088a76b8cf7d76bf1ff08' # Actual private source47 used only as a local fixture; not a saved production51 claim.
class ProductionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=Path(os.environ['HWASUN_ACCEPTED_SOURCE_DIR']).resolve();a.verify_inputs(cls.original)
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='hwasun-production-test-');self.root=Path(self.tmp.name);self.source=self.root/'source';self.source.mkdir()
  for row in a.read_contract()['sourceFiles']:
   p=self.source/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((self.original/row['path']).read_bytes())
  shutil.copytree(self.original/'candidate/dist',self.source/'candidate/dist');self.output=self.root/'production'
 def tearDown(self):self.tmp.cleanup()
 def cli(self,adapter,*args):
  return subprocess.run([sys.executable,str(adapter/'production_adapter.py'),*args],capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 def test_real_positive_exact15_and_body8asset_parity(self):
  r=a.build(self.source,self.output,REV);self.assertEqual(r,a.validate(self.source,self.output,REV));self.assertEqual(r['productionFilesVerified'],15);self.assertEqual(r['sourceFilesVerified'],47);self.assertEqual(r['htmlBodiesByteIdentical'],2);self.assertEqual(r['staticAssetsByteIdentical'],8);self.assertFalse(r['publicationReady']);self.assertFalse(r['assemblyCommitExternallyVerified'])
  c=a.read_contract();row,proof=a.proof(c);self.assertEqual((self.output/row['path'][1:]).read_bytes(),proof)
  for n in a.FILES:
   doc=a.Metadata((self.output/n).read_text());self.assertEqual(doc.meta['site-factory-revision'],REV);self.assertEqual(doc.meta['site-factory-private-source-revision'],a.SOURCE);self.assertNotIn('site-factory-release-revision',doc.meta)
  for n in a.FILES:self.assertEqual((self.source/'candidate/dist'/n).read_bytes().split(b'<body',1)[1],(self.output/n).read_bytes().split(b'<body',1)[1])
 def test_metadata_proof_body_and_asset_mutations_rejected(self):
  a.build(self.source,self.output,REV);baseline=a.inventory(self.output);proof=a.read_contract()['dedicatedPublicProof']['path'][1:]
  changes=[('index.html',b'index,follow',b'noindex,nofollow'),('index.html',REV.encode(),b'0'*40),('index.html',a.SOURCE.encode(),b'1'*40),('index.html',b'production-candidate',b'offline-inspection-only'),('index.html',b'https://hwasun.fwith.kr/',b'https://gokseong.fwith.kr/'),('index.html',b'rel="canonical"',b'rel="alternate"'),('index.html',b'</head>',b'<script>bad</script></head>'),('index.html','59,000'.encode(),'58,000'.encode()),('404.html',b'noindex,nofollow',b'index,follow'),('404.html',b'</head>',b'<link rel="canonical" href="/"></head>'),('robots.txt',b'Allow: /',b'Disallow: /'),('sitemap-index.xml',b'sitemap-0.xml',b'sitemap-orphan.xml'),('sitemap-0.xml',b'https://hwasun.fwith.kr/',b'https://hwasun.fwith.kr/facility/'),(proof,b'\n',b''),('images/products/B201.jpg',b'',b'bad')]
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
  for k in a.FORBIDDEN_ENV:
   with self.subTest(k=k),self.assertRaises(ValueError):a.private_environment({k:'set'})
  for v in ['',None,'short','A'*40,'1'*39,'../'+'f'*40]:
   with self.assertRaises(ValueError):a.build(self.source,self.output,v)
  self.assertFalse(self.output.exists())
 def test_revision_must_match_both_output_documents(self):
  a.build(self.source,self.output,REV)
  with self.assertRaises(ValueError):a.validate(self.source,self.output,'f'*40)
 def test_output_paths_and_existing_output_rejected(self):
  for output in [self.source,self.source/'out',a.ROOT/'out',self.source.parent]:
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
  for n in ['production-release/production-contract.json','production-release/hwasun-indexnow-proof.txt']:
   target=self.root/('clone-'+n.replace('/','-'));shutil.copytree(a.ROOT.parent,target,ignore=shutil.ignore_patterns('__pycache__'))
   p=target/n;p.write_bytes(p.read_bytes()+b'\n');r=self.cli(target/'production-release','build','--source',str(self.source),'--output',str(self.output),'--assembly-revision',REV)
   self.assertNotEqual(r.returncode,0);self.assertFalse(self.output.exists())
 def test_nested_source_rejected_before_native_commands(self):
  target=self.root/'nested';shutil.copytree(a.ROOT.parent,target,ignore=shutil.ignore_patterns('__pycache__'))
  nested=target/'production-release/nested-source';shutil.copytree(self.source,nested,ignore=shutil.ignore_patterns('dist'))
  logs=self.root/'no-logs';r=self.cli(target/'production-release','build-native','--source',str(nested),'--output',str(self.output),'--evidence',str(logs),'--assembly-revision',REV)
  self.assertNotEqual(r.returncode,0);self.assertIn('must be separate',r.stderr);self.assertFalse(logs.exists());self.assertFalse(self.output.exists());self.assertFalse((nested/'candidate/dist').exists());self.assertFalse((nested/'candidate/evidence').exists())
 def test_empty_environment_values_rejected(self):
  for k in (*a.FORBIDDEN_ENV,'SITE_FACTORY_REVISION'):
   with self.subTest(k=k),self.assertRaises(ValueError):a.private_environment({k:''})
 def test_network_modes_remain_absent(self):
  for mode in ['publish','indexnow-submit']:
   r=self.cli(a.ROOT,mode);self.assertNotEqual(r.returncode,0);self.assertIn('Network publication/submission absent',r.stderr)
 def test_invalid_evidence_path_prevents_commands(self):
  for logs in [self.source/'logs',a.ROOT/'logs',self.output/'logs']:
   with self.assertRaises(ValueError):a.build_native(self.source,self.output,logs,REV)
  self.assertFalse(self.output.exists())
 def test_exact_social14_existing_titles_image_and_404_absence(self):
  a.build(self.source,self.output,REV);c=a.read_contract();_,_,private,_=a.verify_inputs(self.source);expected=a.social_values(c,private);doc=a.SocialMetadata((self.output/'index.html').read_text());self.assertEqual(doc.social,expected);self.assertEqual(len(expected),14);self.assertEqual(a.SocialMetadata((self.output/'404.html').read_text()).social,[])
  self.assertEqual(dict((key,value)for _,key,value in expected)['og:url'],'https://hwasun.fwith.kr/');self.assertEqual(dict((key,value)for _,key,value in expected)['og:image'],dict((key,value)for _,key,value in expected)['twitter:image']);self.assertEqual(c['socialMetadata']['imageWidth'],500);self.assertEqual(c['socialMetadata']['imageHeight'],500)
  p=self.output/'index.html';original=p.read_bytes()
  for kind,key,value in expected:
   tag=('<meta '+kind+'="'+key+'" content="'+a.html.escape(value,quote=True)+'">').encode();self.assertEqual(original.count(tag),1)
   for changed in [original.replace(tag,b'',1),original.replace(tag,tag+tag,1),original.replace(tag,tag.replace(b'content="',b'content="wrong-',1),1)]:
    p.write_bytes(changed)
    with self.assertRaises(ValueError):a.validate(self.source,self.output,REV)
   p.write_bytes(original)
  p=self.output/'404.html';original=p.read_bytes();p.write_bytes(original.replace(b'</head>',b'<meta property="og:url" content="https://hwasun.fwith.kr/"></head>'))
  with self.assertRaises(ValueError):a.validate(self.source,self.output,REV)
 def test_empty_headers_has_no_added_rules(self):
  a.build(self.source,self.output,REV);p=self.output/'_headers';self.assertEqual(p.read_bytes(),b'/*\n')
  for data in [b'',b'/*\n  X-Robots-Tag: noindex\n',b'/*\n  Access-Control-Allow-Origin: *\n',b'/*\r\n']:
   p.write_bytes(data)
   with self.assertRaises(ValueError):a.validate(self.source,self.output,REV)
 def test_reused_release_manifest_exact_schema_and_actual_identifiers(self):
  result=a.build(self.source,self.output,REV);files=result['files'];control='c'*40;run='123456789';binding='d'*64;m=a.release_manifest(files,REV,control,run,binding);self.assertEqual(set(m),a.RELEASE_KEYS);self.assertEqual(m['sourceContractSha256'],a.CONTRACT_SHA);self.assertEqual(m['sourceBranch'],'source/hwasun-production-preparation-20261017');self.assertEqual(a.validate_release_manifest(m,files,REV,control,run,binding),m)
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
 def test_hwasun_restricted_hospital_notices_and_metadata_preserved(self):
  a.build(self.source,self.output,REV);d=json.loads((self.source/'inputs/author/display-copy.json').read_text());text=(self.output/'index.html').read_text();private=(self.source/'candidate/dist/index.html').read_text()
  for warning in [d['restrictionNotice']['text'],d['siteUI']['productEligibilityNotice']]:self.assertEqual(text.count(warning),1)
  self.assertEqual(text.split('<body',1)[1],private.split('<body',1)[1]);self.assertIn(d['siteUI']['productGroupAriaLabel'],text)
  metadata=a.Metadata(text).meta
  for name in ['description','og:description','twitter:description']:self.assertEqual(metadata[name],d['page']['description']);self.assertIn('2단 이상',metadata[name])
  self.assertEqual(metadata['og:title'],d['page']['title']);self.assertEqual(metadata['twitter:title'],d['page']['title'])
  for item in d['products']:
   self.assertIsNone(item['referenceSumKRW']);self.assertIsNone(item['sumLabel']);self.assertIsNone(item['postedHwasunAdditionalDeliveryKRW']);self.assertEqual(item['shippingAmountStatus'],'NOT_LISTED_NOT_ZERO');self.assertIn(item['ctaHref'],text)
  self.assertEqual([p['priceKRW']for p in d['products']],[59000,79000,109000,149000]);self.assertEqual(a.read_contract()['facilityPages'],'HOLD_4')
 def test_hwasun_warning_fee_and_social_restriction_mutations_rejected(self):
  a.build(self.source,self.output,REV);p=self.output/'index.html';original=p.read_text();d=json.loads((self.source/'inputs/author/display-copy.json').read_text());notices=[d['restrictionNotice']['text'],d['siteUI']['productEligibilityNotice']]
  changes=[]
  for warning in notices:changes.extend([original.replace(warning,'',1),original.replace(warning,'<span hidden>'+warning+'</span>',1)])
  changes.extend([original.replace('해당 제한은 이 장례식장의 안내이며','해당 제한은 화순군 모든 시설의 안내이며',1),original.replace(d['siteUI']['amountNotice'],'배송비는 0원이고 최종합계는 59,000원입니다.',1),original.replace(d['products'][0]['ctaHref'],'https://fwith.co.kr/shop/item.php?it_id=B203',1)])
  for kind,key,value in a.social_values(a.read_contract(),a.inventory(self.source/'candidate/dist')):
   if key in ['og:description','twitter:description']:
    tag='<meta '+kind+'="'+key+'" content="'+a.html.escape(value,quote=True)+'">';changes.append(original.replace(tag,tag.replace('2단 이상 화환 반입 금지','반입 가능'),1))
  for changed in changes:
   self.assertNotEqual(changed,original);p.write_text(changed)
   with self.assertRaises(ValueError):a.validate(self.source,self.output,REV)
  p.write_text(original);a.validate(self.source,self.output,REV)
 def test_hwasun_unknown_fee_source_and_submission_boundary(self):
  p=self.source/'inputs/author/display-copy.json';original=p.read_bytes();d=json.loads(original);d['products'][0]['postedHwasunAdditionalDeliveryKRW']=0;p.write_text(json.dumps(d,ensure_ascii=False))
  with self.assertRaises(ValueError):a.build(self.source,self.output,REV)
  p.write_bytes(original);self.assertFalse(self.output.exists());c=a.read_contract();self.assertFalse(c['approval']['submitHomeOnlyAfterDeploymentVerification']);self.assertTrue(c['approval']['submissionStageSeparate']);self.assertFalse(c['releaseManifest']['publicDeploymentAuthorization']);self.assertFalse(c['providerNetworkOperationsImplemented']);self.assertFalse(c['indexNowPostImplemented'])
if __name__=='__main__':unittest.main()
