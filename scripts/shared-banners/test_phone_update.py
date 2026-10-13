#!/usr/bin/env python3
"""Narrow regression gates; synthetic proofs never authorize a real release."""
import copy,hashlib,importlib.util,json,os,re,shutil,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import phone_update as phone
import verify_update as legacy
ROOT=Path(__file__).resolve().parents[2]
class PhoneSourceBoundary(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);shutil.copytree(ROOT/phone.DIRECTORY,self.root/phone.DIRECTORY)
  for region in ['anseong','seoul-guro']:
   p=self.root/f'scripts/direct-{region}/publish.py';p.parent.mkdir(parents=True);shutil.copyfile(ROOT/f'scripts/direct-{region}/publish.py',p)
  self.catalogPath=self.root/phone.DIRECTORY/'targets.json';self.data=json.loads(self.catalogPath.read_text());self.target=self.data['targets']['anseong'];self.revision=self.target['revision'];self.env=patch.dict(os.environ,REVISION=self.revision,GITHUB_REPOSITORY='joseungil-kr/fwith-site-factory',GITHUB_RUN_ATTEMPT='1');self.env.start()
 def tearDown(self):self.env.stop();self.temp.cleanup()
 def save(self):self.catalogPath.write_text(json.dumps(self.data))
 def reject(self,code):
  self.save()
  with self.assertRaisesRegex(ValueError,code):phone.load(self.root,'anseong')
 def mutate_readback(self,fn):
  p=self.root/self.target['sourceReadback'];d=json.loads(p.read_text());fn(d);p.write_text(json.dumps(d));self.target['sourceReadbackSha256']=phone.sha(p.read_bytes())
 def test_exact_seven_file_successor_accepted_for_build_only(self):self.assertEqual(phone.load(self.root,'anseong')[0]['changedFileCount'],7)
 def test_exact_twelve_file_guro_successor_accepted_for_build_only(self):
  with patch.dict(os.environ,REVISION=self.data['targets']['seoul-guro']['revision']):self.assertEqual(phone.load(self.root,'seoul-guro')[0]['changedFileCount'],12)
 def test_null_revision_rejected(self):self.target['revision']=None;self.reject('phone_new_revision_mismatch')
 def test_pending_source_rejected(self):self.target['status']='pending';self.reject('phone_source_review_required')
 def test_wrong_parent_rejected(self):self.target['previousRevision']='a'*40;self.reject('phone_parent_revision_mismatch')
 def test_wrong_new_revision_rejected(self):self.target['revision']='b'*40;self.reject('phone_new_revision_mismatch')
 def test_wrong_version_rejected(self):self.target['version']='other';self.reject('phone_target_version_mismatch')
 def test_wrong_catalog_version_rejected(self):self.data['version']='other';self.reject('phone_catalog_version_or_allowlist_mismatch')
 def test_fifteen_excluded_and_other_owner_regions_rejected(self):
  for region in ['anyang','gwangmyeong','pyeongtaek','yeoju','seoul-eunpyeong','seoul-seodaemun','seoul-mapo','ansan','bucheon','goyang','hwaseong','namyangju','seongnam','suwon','yongin','seoul-geumcheon','seoul-yeongdeungpo','seoul-dongjak','seoul-gwanak']:
   with self.subTest(region=region),self.assertRaisesRegex(ValueError,'unknown_phone_update_target'):phone.load(self.root,region)
 def test_extra_allowlist_target_rejected(self):self.data['targets']['other']={};self.reject('phone_catalog_version_or_allowlist_mismatch')
 def test_missing_allowlist_target_rejected(self):self.data['targets'].pop('yangju');self.reject('phone_catalog_version_or_allowlist_mismatch')
 def test_changed_count_cannot_use_old_thirteen_floor(self):self.target['changedFileCount']=13;self.reject('phone_exact_change_scope_required')
 def test_extra_path_rejected(self):self.target['exactChangedPaths'].append(self.target['root']+'/src/data/products.json');self.reject('phone_exact_change_scope_required')
 def test_duplicate_path_rejected(self):self.target['exactChangedPaths'][1]=self.target['exactChangedPaths'][0];self.reject('phone_exact_change_scope_required')
 def test_foreign_hostname_rejected(self):self.target['hostname']='other.fwith.kr';self.reject('phone_fixed_identity_mismatch')
 def test_wrong_worker_rejected(self):self.target['worker']='other';self.reject('phone_fixed_identity_mismatch')
 def test_wrong_branch_rejected(self):self.target['branch']='main';self.reject('phone_fixed_identity_mismatch')
 def test_wrong_root_rejected(self):self.target['root']='site-factory/other';self.reject('phone_fixed_identity_mismatch')
 def test_plan_hash_drift_rejected(self):
  p=self.root/phone.DIRECTORY/'source-plans.json';p.write_text(p.read_text()+' ');self.reject('phone_evidence_digest_mismatch')
 def test_historical_review_drift_rejected(self):
  p=self.root/phone.DIRECTORY/'source-review.md';p.write_text('PASS');self.reject('phone_evidence_digest_mismatch')
 def test_asset_manifest_drift_rejected(self):
  p=self.root/phone.DIRECTORY/'approved-assets.json';p.write_text('[]');self.reject('phone_evidence_digest_mismatch')
 def test_remote_unverified_bytes_rejected(self):self.mutate_readback(lambda d:d['remoteChangedFiles'][0].update(remoteBytesMatch=False));self.reject('phone_readback_exact_hash_mismatch')
 def test_remote_changed_hash_rejected(self):self.mutate_readback(lambda d:d['remoteChangedFiles'][0].update(sha256='0'*64));self.reject('phone_readback_exact_hash_mismatch')
 def test_remote_changed_blob_rejected(self):self.mutate_readback(lambda d:d['remoteChangedFiles'][0].update(gitBlob='0'*40));self.reject('phone_readback_exact_hash_mismatch')
 def test_remote_duplicate_path_rejected(self):self.mutate_readback(lambda d:d['remoteChangedFiles'].__setitem__(1,d['remoteChangedFiles'][0]));self.reject('phone_readback_path_set_mismatch')
 def test_remote_foreign_path_rejected(self):self.mutate_readback(lambda d:d['remoteChangedFiles'][0].update(path='other'));self.reject('phone_readback_exact_hash_mismatch')
 def test_remote_parent_rejected(self):self.mutate_readback(lambda d:d.update(parentCommit='0'*40));self.reject('phone_remote_readback_identity_mismatch')
 def test_remote_all_files_false_rejected(self):self.mutate_readback(lambda d:d.update(allFilesMatch=False));self.reject('phone_remote_readback_identity_mismatch')
 def test_evidence_traversal_rejected(self):self.target['sourceReadback']=phone.DIRECTORY+'/../outside';self.reject('phone_evidence_path_invalid')
 def test_missing_evidence_rejected(self):self.target['sourceReadback']=phone.DIRECTORY+'/missing.json';self.reject('phone_evidence_missing')
 def test_rerun_rejected(self):
  with patch.dict(os.environ,GITHUB_RUN_ATTEMPT='2'),self.assertRaisesRegex(ValueError,'update_rerun_forbidden'):phone.load(self.root,'anseong')
 def test_foreign_repository_rejected(self):
  with patch.dict(os.environ,GITHUB_REPOSITORY='other/repo'),self.assertRaisesRegex(ValueError,'repository_mismatch'):phone.load(self.root,'anseong')
 def test_real_catalog_cannot_authorize_publication_before_build_review(self):
  with self.assertRaisesRegex(ValueError,'phone_evidence_path_invalid'):phone.load(self.root,'anseong',require_release=True)
 def test_new_source_cannot_use_ordinary_mutation(self):
  with patch.object(legacy,'ROOT',self.root),patch.dict(os.environ,EXISTING_UPDATE='false'),self.assertRaisesRegex(ValueError,'reviewed_banner_revision_requires_existing_update'):legacy.authorize_mutation('anseong')
 def test_existing_update_still_requires_actual_release_review(self):
  with patch.object(legacy,'ROOT',self.root),patch.dict(os.environ,EXISTING_UPDATE='true'),self.assertRaisesRegex(ValueError,'phone_evidence_path_invalid'):legacy.authorize_mutation('anseong')
 def fake_release(self):
  proofs=[]
  for kind in ['all-route-output','mobile-pixels','desktop-pixels']:
   path=phone.DIRECTORY+'/'+kind+'.json';p=self.root/path;p.write_text('synthetic unit fixture only');proofs.append(dict(kind=kind,path=path,sha256=phone.sha(p.read_bytes())))
  value=dict(verdict='PASS_PUBLIC_UPDATE',sourceCommit=self.revision,previousRevision=self.target['previousRevision'],sourcePlanSha256=phone.PLAN_SHA256,allRouteOutputVerified=True,nativeTestsPassed=True,mobileAndDesktopPixelsVerified=True,buildRunId='123',artifactId='456',outputFilesSha256='a'*64,evidence=proofs)
  self.releasePath=self.root/phone.DIRECTORY/'synthetic-release-review.json';self.set_release(value);return value
 def set_release(self,value):
  self.releasePath.write_text(json.dumps(value));self.target.update(releaseReview=self.releasePath.relative_to(self.root).as_posix(),releaseReviewSha256=phone.sha(self.releasePath.read_bytes()));self.save()
 def test_complete_synthetic_release_record_parses(self):self.fake_release();self.assertEqual(phone.load(self.root,'anseong',require_release=True)[0]['revision'],self.revision)
 def test_missing_pixel_or_route_gate_rejected(self):
  value=self.fake_release()
  for key in ['allRouteOutputVerified','nativeTestsPassed','mobileAndDesktopPixelsVerified']:
   with self.subTest(key=key):
    changed=copy.deepcopy(value);changed[key]=False;self.set_release(changed)
    with self.assertRaisesRegex(ValueError,'phone_actual_build_and_pixel_review_required'):phone.load(self.root,'anseong',require_release=True)
 def test_missing_artifact_run_or_output_digest_rejected(self):
  value=self.fake_release()
  for key in ['buildRunId','artifactId','outputFilesSha256']:
   with self.subTest(key=key):
    changed=copy.deepcopy(value);changed.pop(key);self.set_release(changed)
    with self.assertRaisesRegex(ValueError,'phone_actual_build_binding_required'):phone.load(self.root,'anseong',require_release=True)
 def test_different_release_source_rejected(self):
  value=self.fake_release();value['sourceCommit']='0'*40;self.set_release(value)
  with self.assertRaisesRegex(ValueError,'phone_release_review_identity_mismatch'):phone.load(self.root,'anseong',require_release=True)
 def test_changed_proof_bytes_rejected(self):
  value=self.fake_release();(self.root/value['evidence'][0]['path']).write_text('changed')
  with self.assertRaisesRegex(ValueError,'phone_evidence_digest_mismatch'):phone.load(self.root,'anseong',require_release=True)
class GitSourceBoundary(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.target={'revision':'b'*40,'previousRevision':'a'*40};self.path='site-factory/fixture/file.txt';p=self.root/self.path;p.parent.mkdir(parents=True);p.write_text('exact fixture bytes');self.row={'path':self.path,'newSha256':phone.sha(p.read_bytes()),'newGitBlob':'c'*40};self.plan={'changedFiles':[self.row]};self.case='clean'
 def tearDown(self):self.temp.cleanup()
 def git(self,args,**kwargs):
  command=args[3:]
  if command==['rev-parse','HEAD']:return (('d'if self.case=='head'else'b')*40+'\n').encode()
  if command==['rev-list','--parents','-n','1','HEAD']:return ('b'*40+' '+'a'*40+(' '+'d'*40 if self.case=='merge'else'')+'\n').encode()
  if command==['status','--porcelain','--untracked-files=all']:return b' M private.txt'if self.case=='dirty'else b''
  if command[0]=='diff':return (self.path+'\0'+('unreviewed.txt\0'if self.case=='extra'else'')).encode()if self.case!='missing'else b''
  if command==['rev-parse','HEAD:'+self.path]:return (('d'if self.case=='blob'else'c')*40+'\n').encode()
  raise AssertionError(command)
 def run_source(self):
  with patch.object(phone,'load',return_value=(self.target,None)),patch.object(phone,'plans',return_value={'fixture':self.plan}),patch.object(phone.subprocess,'check_output',side_effect=self.git):return phone.source(ROOT,'fixture',self.root)
 def test_exact_clean_single_parent_delta_passes(self):self.assertEqual(self.run_source()['changedFiles'],1)
 def test_git_scope_failures_reject(self):
  for case in ['head','merge','dirty','extra','missing','blob']:
   with self.subTest(case=case):
    self.case=case
    with self.assertRaises(ValueError):self.run_source()
 def test_actual_changed_bytes_reject(self):
  (self.root/self.path).write_text('unreviewed bytes')
  with self.assertRaisesRegex(ValueError,'phone_source_bytes_mismatch'):self.run_source()
 def test_symlink_source_rejects(self):
  p=self.root/self.path;p.unlink();p.symlink_to('elsewhere')
  with self.assertRaisesRegex(ValueError,'phone_source_bytes_mismatch'):self.run_source()
class PhoneArtifactBoundary(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.old=Path.cwd();self.root=Path(self.temp.name);os.chdir(self.root);self.dist=Path('release/dist');(self.dist/'images/shared-banners').mkdir(parents=True)
  source=Path(os.environ['DIRECT_SOURCE_ROOT'])/'public/images/shared-banners'
  for name in ['message','budget','consultation']:shutil.copyfile(source/f'flower-{name}.webp',self.dist/'images/shared-banners'/f'flower-{name}.webp')
  spec=importlib.util.spec_from_file_location('fixture_phone_qa',ROOT/'scripts/shared-banners/qa_phone_banners.py');self.qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.qa)
  banners=''.join('<h2>Fixture section</h2><figure data-shared-flower-banner="'+v+'"><img src="/images/shared-banners/flower-'+v+'.webp" alt="'+alt+'" width="1774" height="887" loading="lazy" decoding="async"></figure>'for v,alt in self.qa.APPROVED_BANNER_ALTS.items())
  self.html='<html><head><title>Fixture</title><meta name="description" content="Fixture"><meta name="robots" content="index,follow"><link rel="canonical" href="https://anseong.fwith.kr/"></head><body><main><h1>Fixture</h1>'+banners+'</main></body></html>';(self.dist/'index.html').write_text(self.html)
  (self.dist/'404.html').write_text('<html><head><title>Error</title><meta name="description" content="Fixture error"><meta name="robots" content="noindex,nofollow"></head><body><h1>Error</h1></body></html>')
  self.target={'revision':'b'*40};self.pub=types.SimpleNamespace(WORKER='anseong-flower-guide',ORIGIN='https://anseong.fwith.kr',inventory=lambda root:{p.relative_to(root).as_posix():phone.sha(p.read_bytes())for p in root.rglob('*')if p.is_file()});self.record()
 def tearDown(self):os.chdir(self.old);self.temp.cleanup()
 def record(self):
  files=self.pub.inventory(self.dist);Path('release/release.json').write_text(json.dumps({'revision':'b'*40,'worker':self.pub.WORKER,'origin':self.pub.ORIGIN,'files':files}));self.digest=phone.sha(phone.json_bytes(files))
 def test_actual_exact_phone_fixture_passes_and_moves_report_outside_release(self):
  report=phone.artifact(ROOT,self.target,self.pub);self.assertEqual(report['banners'],3);self.assertEqual(report['outputFilesSha256'],self.digest);self.assertTrue(Path('phone-shared-banner-qa.json').is_file());self.assertFalse(Path('release/shared-banner-qa.json').exists())
 def test_wrong_alt_caption_and_missing_phone_reject_even_with_rehashed_manifest(self):
  for value in ['전화 1844-0645.','전화 1844-0644.','꽃이랑 공통 안내 이미지 · 실제 판매상품 사진이 아닌 AI 생성 이미지입니다. 전화 1844-0644.']:
   with self.subTest(value=value):
    (self.dist/'index.html').write_text(re.sub('alt="[^"]*"','alt="'+value+'"',self.html));self.record()
    with self.assertRaises(AssertionError):phone.artifact(ROOT,self.target,self.pub)
 def test_caption_node_reintroduction_rejects(self):
  (self.dist/'index.html').write_text(self.html.replace('</figure>','<figcaption>revived</figcaption></figure>',1));self.record()
  with self.assertRaises(AssertionError):phone.artifact(ROOT,self.target,self.pub)
 def test_byte_drift_after_packaging_rejects(self):
  (self.dist/'index.html').write_text(self.html+'drift')
  with self.assertRaisesRegex(ValueError,'phone_artifact_files_mismatch'):phone.artifact(ROOT,self.target,self.pub)
 def test_rebuilt_files_must_match_independently_reviewed_output(self):
  with patch.object(phone,'release_review',return_value={'outputFilesSha256':'0'*64}),self.assertRaisesRegex(ValueError,'phone_rebuilt_output_differs_from_reviewed_build'):phone.artifact(ROOT,self.target,self.pub,for_public=True)
 def test_exact_reviewed_output_map_passes(self):
  with patch.object(phone,'release_review',return_value={'outputFilesSha256':self.digest}):self.assertEqual(phone.artifact(ROOT,self.target,self.pub,for_public=True)['outputFilesSha256'],self.digest)
 def test_changed_banner_bytes_rejected_even_with_rehashed_manifest(self):
  (self.dist/'images/shared-banners/flower-message.webp').write_bytes(b'not the reviewed image');self.record()
  with self.assertRaises(AssertionError):phone.artifact(ROOT,self.target,self.pub)
 def test_public_assets_use_exact_new_hashes_and_webp_mime(self):
  self.pub.sha=phone.sha;self.pub.get=lambda path:((self.dist/path.lstrip('/')).read_bytes(),{'Content-Type':'image/webp'})
  report=legacy.public_assets({**self.target,'version':'phone-20261013'},self.pub);self.assertEqual(len(report['assets']),3)
 def test_public_wrong_mime_rejected(self):
  self.pub.sha=phone.sha;self.pub.get=lambda path:((self.dist/path.lstrip('/')).read_bytes(),{'Content-Type':'text/html'})
  with self.assertRaisesRegex(ValueError,'shared_banner_mime_mismatch'):legacy.public_assets({**self.target,'version':'phone-20261013'},self.pub)
 def test_public_wrong_bytes_rejected(self):
  self.pub.sha=phone.sha;self.pub.get=lambda path:(b'wrong',{'Content-Type':'image/webp'})
  with self.assertRaisesRegex(ValueError,'shared_banner_live_digest_mismatch'):legacy.public_assets({**self.target,'version':'phone-20261013'},self.pub)
class WorkflowBoundary(unittest.TestCase):
 def test_build_only_has_no_provider_or_publish_capability(self):
  s=(ROOT/'.github/workflows/shared-banner-phone-build-only.yml').read_text()
  for forbidden in ['secrets.','CLOUDFLARE','wrangler@',' deploy ',' attach ','publish:\n','issues: write','  push:','  schedule:','  workflow_run:']:self.assertNotIn(forbidden,s)
  for required in ['contents: read','phone_update.py source','phone_update.py build-artifact','npm ci','npm test','npm run build','persist-credentials: false','cancel-in-progress: false','-direct-public-release','[REGIONAL-BANNER-BUILD]','phone_update.py select']:self.assertIn(required,s)
 def test_two_fixed_workflows_reuse_no_attach_existing_mode(self):
  for region in ['seoul-gangseo','seoul-guro']:
   s=(ROOT/f'.github/workflows/{region}-direct-publish.yml').read_text();pub=(ROOT/f'scripts/direct-{region}/publish.py').read_text()
   for mode in ['authorize-mutation','artifact','preflight','provider-after','public-assets']:self.assertIn(f'verify_update.py {mode} --region {region}',s)
   self.assertIn("require(not matches and not exists, 'initial_target_must_be_absent')",pub);self.assertIn("if: steps.deploy.outcome == 'success' && !(inputs.existing_update",s);self.assertEqual(s.count('npx --yes "$WRANGLER_PACKAGE" deploy'),1)
   build=s.split('  publish:\n')[0];self.assertNotIn('secrets.',build);self.assertIn('group: '+region+'-direct-public-release',s)
 def test_guro_existing_full_source_gate_retained(self):
  s=(ROOT/'.github/workflows/seoul-guro-direct-publish.yml').read_text();self.assertIn('publish.py source --source target/site-factory/seoul-guro-flower',s);self.assertIn('DIRECT_SOURCE_ROOT:',s)
if __name__=='__main__':unittest.main()
