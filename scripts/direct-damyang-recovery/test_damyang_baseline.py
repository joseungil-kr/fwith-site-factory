"""Damyang-only local regression cases. Fixtures are never live baseline acceptance."""
import ast,copy,datetime,hashlib,io,json,os,re,tempfile,unittest
from pathlib import Path
from email.message import Message
from unittest.mock import patch
import provider_baseline as b
import previous_public as p
import test_provider_baseline as inherited
from test_provider_baseline import ACCOUNT,DEP,VID,SHA,SCRIPT,SETTINGS,fixtures,get_for

class DamyangBaselineContract(unittest.TestCase):
 def state(self,f=None):
  with patch.object(b,'ACCOUNT_SHA',SHA):return b.current_state(ACCOUNT,get_for(f or fixtures()))
 def test_fixed_native_target_not_gwangsan(self):
  self.assertEqual((b.REPO,b.HOST,b.WORKER,b.PREVIOUS,b.CURRENT,b.ACCOUNT_SHA),('joseungil-kr/fwith-site-factory','damyang.fwith.kr','damyang-flower-guide','89c92dff3dca6456c1b0a3f7ee0587efe0361bed','063e9eda9d33cb2f8b4dfd847bea966ff9443eb5','d5bbfc5383872f2c9e36138452e0c880f46b03bbd4aaffa278490c2ad6d7bcbf'))
  policy=b.load_policy();self.assertEqual((policy['expectedOutputFiles'],policy['expectedPublicPaths'],policy['previousPublicationRunId']),(16,15,38861200090));self.assertFalse(policy['historicalVersionKnown']);self.assertIsNone(policy['historicalProviderDeploymentId']);self.assertIsNone(policy['historicalProviderVersionId']);self.assertFalse(policy['baselineAccepted']);self.assertFalse(policy['publicationEligible'])
  self.assertEqual(p.HOSTNAME,b.HOST);self.assertEqual(p.revision(),b.PREVIOUS);self.assertEqual(set(p.PUBLIC_PATH_STATUS),{'/','/.damyang-release-missing-'+b.PREVIOUS+'/',*['/'+n for n in json.loads(b.read(b.ROOT/policy['previousPublicContractPath']))['files'] if not n.endswith('.html') and n!='_headers']})
 def test_original_release_and_binding_evidence_rechecked_before_public(self):
  policy=b.load_policy();real_read=b.read
  paths=[b.ROOT/'docs/direct-damyang-recovery/prior-publication/release-manifest.json',b.ROOT/'docs/direct-damyang-recovery/prior-publication/binding-after.json']
  for target in paths:
   for field,value in [('revision',b.CURRENT),('worker','gwangju-gwangsan-flower-guide')]:
    obj=json.loads(real_read(target));obj[field]=value
    def read(path):return b.canonical(obj) if Path(path)==target else real_read(path)
    with self.subTest(path=target.name,field=field),patch.object(b,'read',side_effect=read),patch.object(p,'http_once') as http,self.assertRaises(ValueError):b.old_public(policy)
    http.assert_not_called()
 def test_every_missing_pagination_field_is_rejected(self):
  paths=['/accounts/'+ACCOUNT+'/workers/scripts','/accounts/'+ACCOUNT+'/workers/domains',SCRIPT+'/deployments?page=1&per_page=1']
  for path in paths:
   for key in [None,'page','per_page','count','total_count','total_pages']:
    with self.subTest(path=path,key=key):
     f=fixtures()
     if key is None:del f[path]['result_info']
     else:del f[path]['result_info'][key]
     with self.assertRaisesRegex(ValueError,'complete_provider_pagination_required'):self.state(f)
 def test_nullable_domain_does_not_allow_empty_pagination(self):
  for info in [{},None,[],False]:
   f=fixtures();f['/accounts/'+ACCOUNT+'/workers/domains'].update(errors=None,messages=None,result_info=info)
   with self.subTest(info=info),self.assertRaises(ValueError):self.state(f)
 def test_both_exposure_flags_must_be_false(self):
  for enabled,preview in [(True,False),(False,True),(True,True)]:
   f=fixtures();f[SCRIPT+'/subdomain']['result'].update(enabled=enabled,previews_enabled=preview)
   with self.subTest(enabled=enabled,preview=preview),self.assertRaisesRegex(ValueError,'historical_workers_dev_exposure_changed'):self.state(f)
 def test_original_public_and_provider_reread_order(self):
  env,event=inherited.Authorization().case();state=self.state();seen=[]
  def current(*args):seen.append('provider');return state
  def public(policy):seen.append('public15');return {'checkedPaths':15,'unknownHttpStatus':404}
  class Getter:envelope_compatibility={'domainsListNullPairObserved':False}
  with patch.object(b,'trusted_control'),patch.object(b,'provider_get',return_value=(ACCOUNT,Getter())),patch.object(b,'state_with_diagnostics',side_effect=current),patch.object(b,'old_public',side_effect=public),patch.object(b,'save'):
   report=b.observe(env,event)
  self.assertEqual(seen,['provider','public15','provider']);self.assertEqual(report['schema'],'damyang-recovery-current-provider-baseline-observation/v1');self.assertEqual(report['identity']['controlRevision'],env['GITHUB_SHA']);self.assertEqual(report['identity']['repository'],b.REPO);self.assertEqual(report['identity']['runAttempt'],1);self.assertEqual(report['identity']['runId'],env['GITHUB_RUN_ID']);self.assertLessEqual(b.timestamp(report['observationStartedAtUTC']),b.timestamp(report['observedAtUTC']));self.assertEqual(report['currentProviderStateSHA256'],b.digest(state))
  for key in ['baselineAccepted','publicationEligible','providerMutationsPerformed','IndexNowSubmitted']:self.assertIs(report[key],False)
 def test_every_material_projected_state_drift_rejected_after_public(self):
  original=self.state();env,event=inherited.Authorization().case()
  variants=[]
  for path,value in [(('accountSHA256',),'f'*64),(('hostname',),'gwangju-gwangsan.fwith.kr'),(('worker',),'gwangju-gwangsan-flower-guide'),(('settings','compatibility_date'),'2026-10-10'),(('workersDev','enabled'),True),(('workersDev','previews_enabled'),True),(('hostnameBinding','domainIdSHA256'),'f'*64),(('hostnameBinding','zoneIdSHA256'),'f'*64),(('activeDeployment','deploymentIdSHA256'),'f'*64),(('activeDeployment','versionIdSHA256'),'f'*64),(('activeDeployment','deploymentCreatedOn'),'2026-10-16T02:58:20.000000001Z')]:
   other=copy.deepcopy(original);target=other
   for key in path[:-1]:target=target[key]
   target[path[-1]]=value;variants.append(other)
  for other in variants:
   with self.subTest(field=list(other)),patch.object(b,'trusted_control'),patch.object(b,'provider_get',return_value=(ACCOUNT,None)),patch.object(b,'state_with_diagnostics',side_effect=[original,other]),patch.object(b,'old_public',return_value={}),patch.object(b,'save') as save,self.assertRaisesRegex(ValueError,'provider_changed_across_full_public_check'):b.observe(env,event)
   save.assert_not_called()
 def test_nonnull_errors_and_missing_selection_never_reach_details(self):
  for errors in [[{'code':999,'message':'secret-canary'}],False,0,'',{},None]:
   obj=fixtures()[SCRIPT+'/deployments?page=1&per_page=1'];obj['errors']=errors;op=inherited.R2Regressions().opener([obj]);get=inherited.R2Regressions().transport(op)
   with self.subTest(errors=type(errors).__name__),self.assertRaises(b.ProviderEnvelopeError) as caught:get(SCRIPT+'/deployments?page=1&per_page=1')
   self.assertNotIn('secret-canary',json.dumps(caught.exception.diagnostic))
   for suffix in ['/deployments/'+DEP,'/versions/'+VID]:
    with self.assertRaises(ValueError):get(SCRIPT+suffix)
   self.assertEqual(len(op.requests),1)
 def test_original_first_publish_job_preserved_and_new_job_get_only(self):
  wf=(b.ROOT/'.github/workflows/damyang-production-publish.yml').read_text();parts=wf.split('  inspect_existing_baseline:\n');self.assertEqual(len(parts),2);job=parts[1]
  self.assertIn('  group: damyang-direct-public-release\n  cancel-in-progress: false',parts[0]);self.assertIn('    permissions:\n      contents: read\n    env:',job);self.assertIn('github.run_attempt == 1',job);self.assertIn(b.TITLE,job)
  self.assertEqual(job.count('CLOUDFLARE_API_TOKEN:'),1);self.assertEqual(job.count('CLOUDFLARE_ACCOUNT_ID:'),1)
  self.assertLess(job.index(' authorize '),job.index('unittest'));self.assertLess(job.index('unittest'),job.index('CLOUDFLARE_API_TOKEN:'));self.assertLess(job.index('CLOUDFLARE_API_TOKEN:'),job.index(' observe '))
  for forbidden in ['workflow_dispatch','wrangler','upload_command','PUT','POST','attach','source/damyang','npm ','issues: write','continue-on-error']:self.assertNotIn(forbidden,job)
 def test_runtime_files_have_no_write_provider_or_dynamic_target_path(self):
  tree=ast.parse(b.read(b.D/'provider_baseline.py'))
  methods=[]
  for node in ast.walk(tree):
   if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='Request':
    methods += [k.value.value for k in node.keywords if k.arg=='method' and isinstance(k.value,ast.Constant)]
  self.assertEqual(methods,['GET']);self.assertNotIn('subprocess.run(',b.read(b.D/'provider_baseline.py').decode())
  forbidden=['/zones','/workers/domains/'+DEP,'/workers/subdomain','/workers/scripts/other/settings']
  for suffix in forbidden:
   with self.subTest(suffix=suffix):
    try:allowed=b.allowed_path(ACCOUNT,'/accounts/'+ACCOUNT+suffix,{'deployments':DEP,'versions':VID})
    except ValueError:allowed=False
    self.assertFalse(allowed)

class StrictRequestJSON(unittest.TestCase):
 def test_every_duplicate_request_key_rejected(self):
  env,event=inherited.Authorization().case();raw=event['issue']['body']
  for key in json.loads(raw):
   for first in ['null','false','0','"wrong"']:
    altered=copy.deepcopy(event);altered['issue']['body']=raw.replace('"'+key+'":','"'+key+'":'+first+',"'+key+'":',1)
    with self.subTest(key=key,first=first),self.assertRaisesRegex(ValueError,'duplicate_json_key_forbidden'):b.authorize(env,altered)
 def test_duplicate_nested_and_nonfinite_event_parser_rejected(self):
  for raw in ['{"issue":{"body":0,"body":1}}','{"issue":{"user":{"login":"other","login":"joseungil-kr"}}}','{"x":NaN}','{"x":Infinity}','{"x":-Infinity}']:
   with self.subTest(raw=raw),self.assertRaises(ValueError):b.strict_json(raw)
 def test_unused_asset_helper_not_in_phase1_policy(self):
  self.assertEqual(set(b.load_policy()['helpersSHA256']),{'existing_provider.py'});self.assertFalse((b.D/'assets_only.py').exists())

class PreviouslyObservedVersionShape(unittest.TestCase):
 # Values and unknown-key names below are invented canaries, never captured provider data.
 # Only field types and failed prior predicates are inherited from Gwangsan run38880772610.
 def case(self):
  f=fixtures();v=f[SCRIPT+'/versions/'+VID]['result'];v['annotations']={};v['metadata']['synthetic_unknown_metadata']='CANARY_NOT_PROVIDER_VALUE'
  script=v['resources']['script'];script['handlers']=None;script['etag']='synthetic/invalid';script['last_deployed_from']='synthetic/invalid'
  v['resources']['script_runtime']['synthetic_unknown_runtime']=None
  return f
 def test_observed_shape_class_rejected_without_baseline_acceptance(self):
  with patch.object(b,'ACCOUNT_SHA',SHA),self.assertRaisesRegex(ValueError,'version_identity_or_schema'):b.current_state(ACCOUNT,get_for(self.case()))
 def test_diagnostic_has_same_known_failure_predicates_no_raw_values(self):
  report=b.provider_shape_diagnostic(ACCOUNT,SCRIPT+'/versions/'+VID,self.case()[SCRIPT+'/versions/'+VID])
  for key in ['onlyPriorVersionKeys','onlyPriorMetadataKeys','onlyPriorRuntimeKeys','staticHandlersAllowed','etagAbsentOrAllowedPattern','last_deployed_fromAbsentOrAllowedPattern']:
   with self.subTest(key=key):self.assertTrue(report['checkEvaluated'][key]);self.assertIs(report['checks'][key],False)
  self.assertEqual(report['fields']['version']['annotations'],{'present':True,'type':'object'});self.assertEqual(report['fields']['script']['handlers'],{'present':True,'type':'null'})
  raw=json.dumps(report)
  for canary in ['CANARY_NOT_PROVIDER_VALUE','synthetic_unknown_metadata','synthetic_unknown_runtime','synthetic/invalid',VID]:self.assertNotIn(canary,raw)
 def test_null_handlers_is_not_normalized_to_empty_array(self):
  f=fixtures();f[SCRIPT+'/versions/'+VID]['result']['resources']['script']['handlers']=None
  with patch.object(b,'ACCOUNT_SHA',SHA),self.assertRaisesRegex(ValueError,'static_only_version_handlers_required'):b.current_state(ACCOUNT,get_for(f))
 def test_unknown_runtime_or_metadata_remains_blocking(self):
  for section,code in [('metadata','version_metadata_schema'),('script_runtime','version_runtime_schema_requires_review')]:
   f=fixtures();v=f[SCRIPT+'/versions/'+VID]['result'];target=v['metadata'] if section=='metadata' else v['resources']['script_runtime'];target['synthetic_unknown']=None
   with self.subTest(section=section),patch.object(b,'ACCOUNT_SHA',SHA),self.assertRaisesRegex(ValueError,code):b.current_state(ACCOUNT,get_for(f))

class StrictTimeBoundary(unittest.TestCase):
 def test_six_digit_claim_boundary_with_nine_digit_provider_floor(self):
  # This checks the comparison contract only; updater consumer integration is separate.
  for claim in ['2026-10-16T00:00:00Z','2026-10-16T00:00:00.123456Z','2024-03-01T00:00:00.000001+00:00','2026-01-01T00:00:00.999999Z']:
   c=b.timestamp(claim);threshold=c-datetime.timedelta(seconds=60)
   base=threshold.replace(microsecond=0)
   ns=threshold.microsecond*1000
   for delta in [-1000,-1,0,1,999,1000]:
    full=ns+delta;seconds,nano=divmod(full,10**9);date=base+datetime.timedelta(seconds=seconds)
    raw=date.strftime('%Y-%m-%dT%H:%M:%S')+'.'+str(nano).zfill(9)+'Z'
    with self.subTest(claim=claim,delta=delta):self.assertEqual(b.timestamp(raw)>=threshold,delta>=0)
 def test_nine_digit_claim_counterexample_documented_not_accepted(self):
  claim='2026-10-16T02:59:20.123456999Z';provider='2026-10-16T02:58:20.123456710Z'
  self.assertTrue(b.timestamp(provider)>=b.timestamp(claim)-datetime.timedelta(seconds=60))
  self.assertFalse(bool(re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|\+00:00)',claim)))
 def test_timezone_and_precision_no_raw_equivalence(self):
  pairs=[('2026-10-16T00:00:00.000000001Z','2026-10-16T00:00:00.000000999Z'),('2026-10-16T00:00:00.123456789Z','2026-10-16T09:00:00.123456789+09:00')]
  for left,right in pairs:
   with self.subTest(pair=left):self.assertEqual(b.timestamp(left),b.timestamp(right));self.assertNotEqual(b.digest({'raw':left}),b.digest({'raw':right}))

class FixedPublicGET(unittest.TestCase):
 def test_fixed_public_status_and_path_before_any_transport(self):
  with patch.object(p,'build_opener',side_effect=AssertionError('transport forbidden')):
   for path,status in [('/_headers',200),('/index.html',200),('/404.html',404),('//other.test/',200),('/../',200),('/new-proof.txt',200),('/',404),('/',True),('https://damyang.fwith.kr/',200)]:
    with self.subTest(path=path,status=status),self.assertRaisesRegex(ValueError,'fixed_public_get_path_required'):p.get(path,status)
 def test_mime_negative_matrix_and_no_general_normalization(self):
  for name in json.loads(b.read(b.ROOT/b.load_policy()['previousPublicContractPath']))['files']:
   if name=='_headers':continue
   headers=Message();headers['Content-Type']='application/octet-stream'
   with self.subTest(name=name),self.assertRaises(ValueError):p.media_type(headers,name)
  body=b'<html><body>known</body></html>'
  for changed in [body+b' ',body.replace(b'known',b'changed'),b'<!-- unknown injection -->'+body]:
   with self.subTest(body=changed),self.assertRaises(AssertionError):p.strip_one_cf_beacon(changed,b.sha(body))
