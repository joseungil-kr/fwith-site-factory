"""Synthetic existing-target gates; no provider request, GitHub write or upload."""
import contextlib,copy,datetime,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import existing_update as u
import provider_baseline as b
import test_provider_baseline as f

class UpdateTests(unittest.TestCase):
 def setUp(self):
  self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close);self.root=Path(self.stack.enter_context(tempfile.TemporaryDirectory()));self.d=self.root/'scripts/direct-damyang-recovery';self.d.mkdir(parents=True);self.docs=self.root/'docs/direct-damyang-recovery';self.docs.mkdir(parents=True)
  self.stack.enter_context(patch.object(u,'D',self.d));self.stack.enter_context(patch.object(u,'ROOT',self.root));old=Path.cwd();os.chdir(self.root);self.addCleanup(os.chdir,old)
  self.env={'GITHUB_RUN_ATTEMPT':'1','GITHUB_RUN_ID':'987654','GITHUB_SHA':'a'*40}
  with patch.object(b,'ACCOUNT_SHA',f.SHA):self.state=b.current_state(f.ACCOUNT,f.get_for(f.fixtures()))
  self.state['accountSHA256']=b.ACCOUNT_SHA
  self.obs={'schema':'damyang-recovery-current-provider-baseline-observation/v1','state':'OBSERVED_NOT_ACCEPTED_FOR_MUTATION','policySHA256':b.POLICY_SHA,'previousSourceRevision':u.PREVIOUS,'correctionSourceRevision':u.CURRENT,'previousPublicationRunId':38861200090,'historicalProviderVersionKnown':False,'providerMethods':['GET'],'providerMutationsPerformed':False,'IndexNowSubmitted':False,'baselineAccepted':False,'publicationEligible':False,'identity':{'repository':b.REPO,'controlRevision':'b'*40,'runId':'987650','runAttempt':1,'providerMethods':['GET'],'providerMutationsPerformed':False},'currentProviderState':self.state,'currentProviderStateSHA256':b.digest(self.state),'previousPublicHTTP':{'state':'public_release_verified','revision':u.PREVIOUS,'checkedPaths':15,'unknownHttpStatus':404}}
  self.desc={'schema':'damyang-recovery-accepted-provider-baseline-binding/v1','state':'INDEPENDENTLY_ACCEPTED_CURRENT_BASELINE','path':'docs/direct-damyang-recovery/fixture-observation.json','sha256':None,'reviewPath':'docs/direct-damyang-recovery/fixture-review.json','reviewSHA256':None,'observationRunId':987650,'observationControlRevision':'b'*40,'observationArtifactId':987651,'observationArtifactDigest':'sha256:'+'c'*64}
  self.review={'schema':'damyang-recovery-current-provider-baseline-independent-review/v1','verdict':'ACCEPT_CURRENT_GET_ONLY_BASELINE_FOR_DAMYANG_PROOF_RECOVERY','previousSourceRevision':u.PREVIOUS,'correctionSourceRevision':u.CURRENT,'observationSHA256':None,'currentProviderStateSHA256':self.obs['currentProviderStateSHA256'],'observationRunId':self.desc['observationRunId'],'observationControlRevision':self.desc['observationControlRevision'],'observationArtifactId':self.desc['observationArtifactId'],'observationArtifactDigest':self.desc['observationArtifactDigest'],'actualLiveGETVerified':True,'priorPublic15Verified':True,'singleVersion100Verified':True,'settingsAndBindingReviewed':True,'noRawSecretValuesPublished':True,'historicalProviderVersionKnown':False,'publicationApproved':False,'reviewer':'SYNTHETIC_TEST_ONLY'}
  self.seal();self.release={'buildRunId':'987652','artifactId':'987653','artifactDigest':'sha256:'+'d'*64,'outputFilesSha256':'e'*64,'releaseManifestSha256':'f'*64}
  self.source={'name':u.WORKER,'compatibility_date':'2026-10-09','workers_dev':False,'assets':{'directory':'./dist/','not_found_handling':'404-page','html_handling':'auto-trailing-slash'}};(self.root/'release').mkdir();b.save('release/wrangler.publish.json',self.source)
 def seal(self):
  b.save(self.root/self.desc['path'],self.obs);self.desc['sha256']=b.sha((self.root/self.desc['path']).read_bytes());self.review['observationSHA256']=self.desc['sha256'];b.save(self.root/self.desc['reviewPath'],self.review);self.desc['reviewSHA256']=b.sha((self.root/self.desc['reviewPath']).read_bytes());b.save(self.d/'accepted-provider-baseline-binding.json',self.desc)
 def comment(self,record,id,marker=None):
  import indexnow_recovery as receipt
  return {'id':id,'user':{'login':'github-actions[bot]','id':41898282,'type':'Bot'},'body':(receipt.MARKER if marker is None else marker)+json.dumps(record),'url':receipt.API_BASE+'/issues/comments/'+str(id),'issue_url':receipt.ISSUE_URL,'html_url':receipt.WEB_ISSUE+'#issuecomment-'+str(id)}
 def history(self):
  import indexnow_recovery as receipt
  return [receipt.AuditPage(receipt.page_url(1),200,[self.comment(receipt.original_record('started'),6209522619),self.comment(receipt.original_record('rejected'),6209523005)],None,True)]
 def claim(self):
  identity=u.attempt_identity(self.release,self.env);r=u.select_claim(self.history(),identity);r['commentId']=987655;b.save('deployment-attempt-claim.json',r);return r
 def staged(self):
  b.save('update-source-config.json',self.source);b.save('provider-state-before.json',self.state);b.save('release/wrangler.publish.json',u.exact_assets_config(self.source,self.state))
 def test_exact_synthetic_accepted_chain(self):self.assertEqual(u.accepted_baseline()[1]['currentProviderStateSHA256'],b.digest(self.state))
 def test_pending_baseline_blocks_before_provider(self):
  b.save(self.d/'accepted-provider-baseline-binding.json',{**self.desc,'state':'PENDING'})
  with patch.object(u,'observe_current') as get,self.assertRaises(ValueError):u.preflight()
  get.assert_not_called()
 def test_descriptor_identity_and_types(self):
  for key,value in [('state','OBSERVED_NOT_ACCEPTED_FOR_MUTATION'),('observationRunId',True),('observationArtifactId',None),('observationControlRevision','c'*40),('observationArtifactDigest','sha256:'+'e'*64),('sha256','0'*64),('reviewSHA256','0'*64),('path','../escape')]:
   b.save(self.d/'accepted-provider-baseline-binding.json',{**self.desc,key:value})
   with self.subTest(key=key),self.assertRaises(ValueError):u.accepted_baseline()
  b.save(self.d/'accepted-provider-baseline-binding.json',self.desc)
 def test_observation_truth_flags_never_promoted(self):
  for key,value in [('baselineAccepted',True),('publicationEligible',True),('providerMethods',['GET','PUT']),('historicalProviderVersionKnown',True),('previousSourceRevision',u.CURRENT),('correctionSourceRevision',u.PREVIOUS),('providerMutationsPerformed',True)]:
   old=copy.deepcopy(self.obs);self.obs[key]=value;self.seal()
   with self.subTest(key=key),self.assertRaises(ValueError):u.accepted_baseline()
   self.obs=old;self.seal()
 def test_independent_review_flags_required(self):
  for key,value in [('actualLiveGETVerified',False),('priorPublic15Verified',False),('singleVersion100Verified',False),('settingsAndBindingReviewed',False),('noRawSecretValuesPublished',False),('historicalProviderVersionKnown',True),('publicationApproved',True),('reviewer','')]:
   old=copy.deepcopy(self.review);self.review[key]=value;self.seal()
   with self.subTest(key=key),self.assertRaises(ValueError):u.accepted_baseline()
   self.review=old;self.seal()
 def test_baseline_projection_digest_required(self):
  self.obs['currentProviderState']['worker']='other';self.seal()
  with self.assertRaises(ValueError):u.accepted_baseline()
 def test_exact_route_less_configuration_preserves_flags(self):
  x=u.exact_assets_config(self.source,self.state);self.assertFalse(x['workers_dev']);self.assertFalse(x['preview_urls']);self.assertNotIn('routes',x);self.assertNotIn('main',x)
  for key,value in [('routes',[]),('main','x.js'),('name','other'),('workers_dev',True),('workers_dev',0)]:
   b.save('release/wrangler.publish.json',{**self.source,key:value})
   with self.subTest(key=key),self.assertRaises(ValueError):u.source_config()
 def test_exact_preflight_observes_before_and_after_public(self):
  with patch.object(u,'observe_current',side_effect=[self.state,copy.deepcopy(self.state)]) as get,patch.object(b,'old_public',return_value={'checkedPaths':15}) as public,patch.object(b,'load_policy',return_value={}):r=u.preflight()
  self.assertEqual(get.call_count,2);public.assert_called_once();self.assertFalse(r['hostnameAttachAllowed']);self.assertNotIn('routes',json.loads(Path('release/wrangler.publish.json').read_text()))
 def test_preflight_drift_stops_before_public(self):
  changed=copy.deepcopy(self.state);changed['accountSHA256']='0'*64
  with patch.object(u,'observe_current',return_value=changed),patch.object(b,'old_public') as public,self.assertRaises(ValueError):u.preflight()
  public.assert_not_called()
 def test_preflight_race_stops_before_configuration(self):
  changed=copy.deepcopy(self.state);changed['activeDeployment']['versionIdSHA256']='0'*64
  with patch.object(u,'observe_current',side_effect=[self.state,changed]),patch.object(b,'old_public',return_value={'checkedPaths':15}),patch.object(b,'load_policy',return_value={}),self.assertRaises(ValueError):u.preflight()
  self.assertEqual(json.loads(Path('release/wrangler.publish.json').read_text()),self.source)
 def test_exact_claim_has_all_run_artifact_baseline_ids(self):
  r=self.claim();self.assertEqual(u.verify_claim(self.release,self.env),r);self.assertEqual(r['sourceRevision'],u.CURRENT);self.assertEqual(r['artifactDigest'],self.release['artifactDigest']);self.assertEqual(r['providerStateSHA256'],b.digest(self.state))
 def test_any_prior_target_claim_blocks_even_unknown_or_foreign_source(self):
  for status in ['STARTED_NO_AUTOMATIC_REUPLOAD','FAILED','UNKNOWN','SUCCESS']:
   for source in [u.CURRENT,'f'*40]:
    pages=self.history();pages[0].comments.append(self.comment({'sourceRevision':source,'hostname':u.HOST,'state':status},6209524000,u.MARKER))
    with self.subTest(status=status,source=source),self.assertRaisesRegex(ValueError,'prior_damyang_update_attempt'):u.select_claim(pages,u.attempt_identity(self.release,self.env))
 def test_original_exact_rejected_pair_and_full_pages_required(self):
  for kind in ['no-record','wrong-user','wrong-bot-id','bad-json','wrong-revision','http200','wrong-comment-id','truncated','wrong-page','extra-page']:
   import indexnow_recovery as receipt
   pages=self.history();comments=pages[0].comments
   if kind=='no-record':comments.clear()
   elif kind=='wrong-user':comments[0]['user']['login']='other'
   elif kind=='wrong-bot-id':comments[0]['user']['id']=1
   elif kind=='bad-json':comments[0]['body']=receipt.MARKER+'invalid'
   elif kind=='wrong-revision':comments[0]['body']=comments[0]['body'].replace(u.PREVIOUS,u.CURRENT)
   elif kind=='http200':comments[1]['body']=comments[1]['body'].replace('422','200')
   elif kind=='wrong-comment-id':comments[0]['id']=42
   elif kind=='truncated':pages[0]=receipt.AuditPage(receipt.page_url(1),200,comments,None,False)
   elif kind=='wrong-page':pages[0]=receipt.AuditPage(receipt.page_url(2),200,comments,None,True)
   else:pages.append(receipt.AuditPage(receipt.page_url(2),200,[],None,True))
   with self.subTest(kind=kind),self.assertRaises(ValueError):u.select_claim(pages,u.attempt_identity(self.release,self.env))
 def test_claim_echo_and_exclusive_full_readback_required(self):
  record=u.select_claim(self.history(),u.attempt_identity(self.release,self.env));comment=self.comment(record,6209524000,u.MARKER);pages=self.history();pages[0].comments.append(comment)
  self.assertEqual(u.validate_claim_echo(record,comment,pages)['commentId'],6209524000)
  for kind in ['missing','extra','wrong-bot','wrong-echo']:
   pp=copy.deepcopy(pages);cc=copy.deepcopy(comment)
   if kind=='missing':pp[0].comments.pop()
   elif kind=='extra':pp[0].comments.append(self.comment(record,6209524001,u.MARKER))
   elif kind=='wrong-bot':cc['user']['id']=1
   else:cc['body']=cc['body'].replace(u.CURRENT,u.PREVIOUS)
   with self.subTest(kind=kind),self.assertRaises(ValueError):u.validate_claim_echo(record,cc,pp)
 def test_claim_mutation_run_artifact_or_comment_blocks(self):
  r=self.claim()
  for key,value in [('runId','another'),('artifactDigest','sha256:'+'0'*64),('controlRevision','0'*40),('commentId',True),('state','RETRY'),('providerStateSHA256','0'*64),('recordedAtUTC','yesterday')]:
   b.save('deployment-attempt-claim.json',{**r,key:value})
   with self.subTest(key=key),self.assertRaises(ValueError):u.verify_claim(self.release,self.env)
 def test_recheck_requires_claim_before_provider(self):
  with patch.object(u,'observe_current') as get,self.assertRaises(ValueError):u.recheck(self.release,self.env)
  get.assert_not_called()
 def test_exact_recheck_requires_prior_public_again(self):
  self.claim();self.staged()
  with patch.object(u,'observe_current',return_value=self.state) as get,patch.object(b,'old_public',return_value={'checkedPaths':15}) as public,patch.object(b,'load_policy',return_value={}):r=u.recheck(self.release,self.env)
  self.assertEqual(get.call_count,2);public.assert_called_once();self.assertEqual(r['state'],'READY_FOR_ONE_CLAIMED_STATIC_UPLOAD')
 def test_recheck_rejects_tampered_config(self):
  self.claim();self.staged();x=json.loads(Path('release/wrangler.publish.json').read_text());x['routes']=[];b.save('release/wrangler.publish.json',x)
  with patch.object(u,'observe_current',return_value=self.state),patch.object(b,'old_public',return_value={}),patch.object(b,'load_policy',return_value={}),self.assertRaises(ValueError):u.recheck(self.release,self.env)
 def uploaded(self):
  self.claim();self.staged();new=copy.deepcopy(self.state);new['activeDeployment'].update(versionIdSHA256='a'*64,deploymentIdSHA256='b'*64,deploymentCreatedOn=datetime.datetime.now(datetime.timezone.utc).isoformat());b.save('upload-version.json',{'state':'ONE_UPLOAD_SUCCEEDED_VERSION_PARSED','versionIdSHA256':'a'*64,'runId':self.env['GITHUB_RUN_ID'],'sourceRevision':u.CURRENT});return new
 def test_exact_new_version_and_unchanged_binding(self):
  new=self.uploaded()
  with patch.object(u,'observe_current',return_value=new):r=u.readback(self.release,self.env)
  self.assertEqual(r['versionIdSHA256'],'a'*64);self.assertFalse(r['hostnameAttached']);self.assertFalse(r['publicHTTPVerified']);self.assertNotIn('versionId',r)
 def test_readback_wrong_version_old_version_binding_or_timestamp_blocks(self):
  for kind in ['wrong-version','old-deployment','changed-binding','changed-script','changed-runtime','old-time']:
   new=self.uploaded()
   if kind=='wrong-version':new['activeDeployment']['versionIdSHA256']='0'*64
   elif kind=='old-deployment':new['activeDeployment']['deploymentIdSHA256']=self.state['activeDeployment']['deploymentIdSHA256']
   elif kind=='changed-binding':new['hostname']='foreign.test'
   elif kind=='changed-script':new['activeDeployment']['versionScript']['present']=False
   elif kind=='changed-runtime':new['activeDeployment']['versionRuntime']['present']=False
   else:new['activeDeployment']['deploymentCreatedOn']='2000-01-01T00:00:00Z'
   with self.subTest(kind=kind),patch.object(u,'observe_current',return_value=new),self.assertRaises(ValueError):u.readback(self.release,self.env)
   self.assertTrue(Path('provider-state-after-observed.json').exists())
 def test_uncertain_upload_still_saves_get_observation_and_blocks(self):
  self.claim();self.staged()
  with patch.object(u,'observe_current',return_value=self.state),self.assertRaises(ValueError):u.readback(self.release,self.env)
  self.assertEqual(json.loads(Path('provider-state-after-observed.json').read_text()),self.state)
 def test_upload_log_only_one_uuid_digest_retained(self):
  Path('private-upload.log').write_text('private ignored log\nCurrent Version ID: '+f.VID+'\n');r=u.extract_upload_version('private-upload.log',self.env);self.assertEqual(r['versionIdSHA256'],b.sha(f.VID.encode()));self.assertNotIn(f.VID,json.dumps(r))
  for raw in ['', 'Current Version ID: wrong', ('Current Version ID: '+f.VID+'\n')*2]:
   Path('private-upload.log').write_text(raw)
   with self.subTest(raw=raw),self.assertRaises(ValueError):u.extract_upload_version('private-upload.log',self.env)
 def test_exact_upper_bound_timestamp_keeps_nanoseconds_and_offsets(self):
  base='2026-10-16T00:00:30.123456Z';n=u.exact_provider_instant_ns(base)
  for value,delta in [('2026-10-16T00:00:30.123455999Z',-1),('2026-10-16T00:00:30.123456000Z',0),('2026-10-16T00:00:30.123456001Z',1),('2026-10-16T09:00:30.123456001+09:00',1),('2026-10-15T18:30:30.123456001-05:30',1)]:
   with self.subTest(value=value):self.assertEqual(u.exact_provider_instant_ns(value),n+delta)
 def test_far_future_active_deployment_is_rejected(self):
  new=self.uploaded();new['activeDeployment']['deploymentCreatedOn']='2099-01-01T00:00:00.000000001Z'
  with patch.object(u,'observe_current',return_value=new),self.assertRaisesRegex(ValueError,'future_dated'):u.readback(self.release,self.env)
 def test_repeat_attempt_forbidden(self):
  with self.assertRaises(ValueError):u.attempt_identity(self.release,{**self.env,'GITHUB_RUN_ATTEMPT':'2'})
 def test_claim_timestamp_accepts_only_utc_zero_to_six_fraction_digits(self):
  original=self.claim()
  for digits in range(7):
   fraction='' if digits==0 else '.'+'123456'[:digits]
   for zone in ['Z','+00:00']:
    value='2026-10-16T00:00:30'+fraction+zone;b.save('deployment-attempt-claim.json',{**original,'recordedAtUTC':value})
    with self.subTest(value=value):self.assertEqual(u.verify_claim(self.release,self.env)['recordedAtUTC'],value);self.assertEqual(u.claim_timestamp(value),b.timestamp(value))
 def test_claim_invalid_profile_blocks_before_any_provider_read(self):
  original=self.claim();values=[None,True,1,[],{},'', '2026-10-16T00:00:30.1234567Z','2026-10-16T00:00:30.12345678Z','2026-10-16T00:00:30.123456789Z','2026-10-16T00:00:30+09:00','2026-10-16T00:00:30-01:00','2026-10-16T00:00:30-00:00','2026-10-16T00:00:30','2026-10-16 00:00:30Z','2026-10-16T00:00:30.Z','2026-02-29T00:00:30Z','2026-10-16T00:00:30Z\n','2026-10-16T00:00:30.١Z']
  for value in values:
   b.save('deployment-attempt-claim.json',{**original,'recordedAtUTC':value})
   for action in [u.recheck,u.readback]:
    with self.subTest(value=value,action=action.__name__),patch.object(u,'observe_current') as get,self.assertRaises(ValueError):action(self.release,self.env)
    get.assert_not_called()
 def test_claim_generator_still_emits_verified_utc_microsecond_contract(self):
  for i in range(10):
   record=self.claim();parsed=u.claim_timestamp(record['recordedAtUTC']);self.assertEqual(parsed.utcoffset(),datetime.timedelta(0));self.assertEqual(u.verify_claim(self.release,self.env),record)
 def test_readback_freshness_exact_nanosecond_boundaries_and_offsets(self):
  for claim in ['2026-10-16T00:00:30.123456+00:00','2026-01-01T00:00:30.123456Z','2024-03-01T00:00:30Z']:
   threshold=u.claim_timestamp(claim)-datetime.timedelta(seconds=60)
   for delta in [-1000,-1,0,1,1000]:
    for offset in [0,540,-330]:
     new=self.uploaded();record=json.loads(Path('deployment-attempt-claim.json').read_text());record['recordedAtUTC']=claim;b.save('deployment-attempt-claim.json',record)
     seconds,nanos=divmod(threshold.microsecond*1000+delta,1000000000);wall=threshold.replace(microsecond=0)+datetime.timedelta(seconds=seconds,minutes=offset);zone='Z' if offset==0 else ('+' if offset>0 else '-')+f'{abs(offset)//60:02d}:{abs(offset)%60:02d}';provider=wall.strftime('%Y-%m-%dT%H:%M:%S')+f'.{nanos:09d}'+zone;new['activeDeployment']['deploymentCreatedOn']=provider
     with self.subTest(claim=claim,delta_ns=delta,offset=offset),patch.object(u,'observe_current',return_value=new):
      if delta<0:
       with self.assertRaisesRegex(ValueError,'^active_deployment_predates_claim$'):u.readback(self.release,self.env)
      else:self.assertEqual(u.readback(self.release,self.env)['state'],'EXACT_NEW_VERSION_AND_UNCHANGED_BINDING_VERIFIED')
     self.assertEqual(json.loads(Path('provider-state-after-observed.json').read_text())['activeDeployment']['deploymentCreatedOn'],provider)
 def test_nanosecond_claim_counterexample_is_rejected_before_flooring(self):
  # A 9-digit claim would incorrectly admit a provider time 289ns too early if both floor.
  claim='2026-10-16T00:00:30.123456789Z';provider='2026-10-15T23:59:30.123456500Z';self.assertGreaterEqual(b.timestamp(provider),b.timestamp(claim)-datetime.timedelta(seconds=60))
  with self.assertRaisesRegex(ValueError,'^invalid_claim_timestamp$'):u.claim_timestamp(claim)
 def test_nanosecond_raw_change_still_blocks_accepted_state_and_recheck(self):
  for key in ['deploymentCreatedOn','versionCreatedOn']:
   for left,right in [('2026-10-16T02:58:20.123456001Z','2026-10-16T02:58:20.123456999Z'),('2026-10-16T02:58:20.123456789Z','2026-10-16T11:58:20.123456789+09:00')]:
    with self.subTest(key=key,right=right):
     self.assertEqual(b.timestamp(left),b.timestamp(right));self.state['activeDeployment'][key]=left;self.obs['currentProviderState']=self.state;self.obs['currentProviderStateSHA256']=b.digest(self.state);self.review['currentProviderStateSHA256']=b.digest(self.state);self.seal();new=copy.deepcopy(self.state);new['activeDeployment'][key]=right;self.assertNotEqual(b.digest(self.state),b.digest(new))
     with patch.object(u,'observe_current',return_value=new),patch.object(b,'old_public') as public,self.assertRaisesRegex(ValueError,'^accepted_provider_baseline_changed$'):u.preflight()
     public.assert_not_called();self.claim();self.staged()
     with patch.object(u,'observe_current',return_value=new),patch.object(b,'old_public') as public,self.assertRaisesRegex(ValueError,'^provider_changed_before_single_upload$'):u.recheck(self.release,self.env)
     public.assert_not_called()

if __name__=='__main__':unittest.main(verbosity=2)
