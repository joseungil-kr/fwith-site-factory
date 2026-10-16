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
 def test_documented_optional_pagination_fields_do_not_change_exact_projection(self):
  paths=['/accounts/'+ACCOUNT+'/workers/scripts','/accounts/'+ACCOUNT+'/workers/domains',SCRIPT+'/deployments?page=1&per_page=1']
  for path in paths:
   for key in [None,'page','per_page','count','total_count','total_pages']:
    with self.subTest(path=path,key=key):
     f=fixtures()
     if key is None:del f[path]['result_info']
     else:del f[path]['result_info'][key]
     self.assertEqual(self.state(f),self.state())
 def test_nullable_domain_empty_metadata_valid_but_bad_containers_still_rejected(self):
  f=fixtures();f['/accounts/'+ACCOUNT+'/workers/domains'].update(errors=None,messages=None,result_info={})
  self.assertEqual(self.state(f),self.state())
  for info in [None,[],False]:
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
  wf=(b.ROOT/'.github/workflows/damyang-production-publish.yml').read_text();parts=wf.split('  inspect_existing_baseline:\n');self.assertEqual(len(parts),2);job=parts[1].split('\n  recovery_static_update:\n',1)[0]
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
 def test_baseline_policy_does_not_consume_update_asset_helper(self):
  self.assertEqual(set(b.load_policy()['helpersSHA256']),{'existing_provider.py'})
  tree=ast.parse(b.read(b.D/'provider_baseline.py'))
  imports=[name.name for node in ast.walk(tree) if isinstance(node,ast.Import) for name in node.names]+[node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
  self.assertNotIn('assets_only',imports)

class PreviouslyObservedVersionShape(unittest.TestCase):
 # Values and unknown-key names below are invented canaries, never captured provider data.
 # Only field types and failed prior predicates are inherited from Gwangsan run38880772610.
 def case(self):
  f=fixtures();v=f[SCRIPT+'/versions/'+VID]['result'];v['annotations']={};v['metadata']['synthetic_unknown_metadata']='CANARY_NOT_PROVIDER_VALUE'
  script=v['resources']['script'];script['handlers']=None;script['etag']='synthetic/invalid';script['last_deployed_from']='synthetic/invalid'
  v['resources']['script_runtime']['synthetic_unknown_runtime']=None
  return f
 def test_unknown_nonassets_runtime_still_rejected_without_baseline_acceptance(self):
  with patch.object(b,'ACCOUNT_SHA',SHA),self.assertRaisesRegex(ValueError,'version_runtime_schema_requires_review'):b.current_state(ACCOUNT,get_for(self.case()))
 def test_diagnostic_has_same_known_failure_predicates_no_raw_values(self):
  report=b.provider_shape_diagnostic(ACCOUNT,SCRIPT+'/versions/'+VID,self.case()[SCRIPT+'/versions/'+VID])
  for key in ['onlyPriorVersionKeys','onlyPriorMetadataKeys','onlyPriorRuntimeKeys','staticHandlersAllowed','etagAbsentOrAllowedPattern','last_deployed_fromAbsentOrAllowedPattern']:
   with self.subTest(key=key):self.assertTrue(report['checkEvaluated'][key]);self.assertIs(report['checks'][key],False)
  self.assertEqual(report['fields']['version']['annotations'],{'present':True,'type':'object'});self.assertEqual(report['fields']['script']['handlers'],{'present':True,'type':'null'})
  raw=json.dumps(report)
  for canary in ['CANARY_NOT_PROVIDER_VALUE','synthetic_unknown_metadata','synthetic_unknown_runtime','synthetic/invalid',VID]:self.assertNotIn(canary,raw)
 def test_null_handlers_is_accepted_but_not_normalized_to_empty_array(self):
  states=[]
  for value in (None,[],['fetch']):
   f=fixtures();f[SCRIPT+'/versions/'+VID]['result']['resources']['script']['handlers']=value
   with patch.object(b,'ACCOUNT_SHA',SHA):state=b.current_state(ACCOUNT,get_for(f))
   self.assertEqual(state['activeDeployment']['versionScript']['fields']['handlers'],value);states.append(state)
  self.assertEqual(len({b.digest(state) for state in states}),3)
 def test_metadata_unknown_is_unconsumed_nonassets_runtime_still_blocks(self):
  f=fixtures();f[SCRIPT+'/versions/'+VID]['result']['metadata']['synthetic_unknown']='CANARY_NOT_PROVIDER_VALUE'
  with patch.object(b,'ACCOUNT_SHA',SHA):state=b.current_state(ACCOUNT,get_for(f))
  self.assertNotIn('synthetic_unknown',json.dumps(state));self.assertNotIn('CANARY_NOT_PROVIDER_VALUE',json.dumps(state))
  for value in (None,{},[],False,'CANARY_NOT_PROVIDER_VALUE'):
   f=fixtures();f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime']['synthetic_unknown']=value
   with self.subTest(value=type(value).__name__),patch.object(b,'ACCOUNT_SHA',SHA),self.assertRaisesRegex(ValueError,'version_runtime_schema_requires_review'):b.current_state(ACCOUNT,get_for(f))
 def test_retained_diagnostic_predicates_are_prior_policy_not_new_acceptance(self):
  # Diagnostic code is deliberately unchanged. A prior-predicate false is not a
  # rejection under the new narrow contract, and never grants baseline acceptance.
  f=self.case();del f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime']['synthetic_unknown_runtime']
  with patch.object(b,'ACCOUNT_SHA',SHA):state=b.current_state(ACCOUNT,get_for(f))
  self.assertIsNone(state['activeDeployment']['versionScript']['fields']['handlers'])
  report=b.provider_shape_diagnostic(ACCOUNT,SCRIPT+'/versions/'+VID,f[SCRIPT+'/versions/'+VID])
  for key in ('onlyPriorVersionKeys','onlyPriorMetadataKeys','staticHandlersAllowed','etagAbsentOrAllowedPattern','last_deployed_fromAbsentOrAllowedPattern'):
   with self.subTest(key=key):self.assertTrue(report['checkEvaluated'][key]);self.assertFalse(report['checks'][key])
  self.assertNotIn('CANARY_NOT_PROVIDER_VALUE',json.dumps(report))

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


class DamyangSelectedAssetsBoundary(unittest.TestCase):
 # Independent Damyang-only boundary additions; synthetic repeated identities only.
 def case(self):return inherited.R12AssetsPreservation.fixtures()
 def state(self,f):
  with patch.object(b,'ACCOUNT_SHA',SHA):return b.current_state(ACCOUNT,get_for(f))
 def test_gwangsan_other_accounts_aliases_and_queries_never_reach_transport(self):
  beta=inherited.R12AssetsPreservation.BETA;selection={'deployments':DEP,'versions':VID}
  variants=[beta.replace(b.WORKER,'gwangju-gwangsan-flower-guide'),beta.replace(ACCOUNT,'b'*32),beta.replace(VID,VID[:8]),beta.replace(VID,'latest'),beta.replace(VID,VID.upper()+'A'),beta+'?x=1',beta+'&include=modules',beta.replace('?include=modules','?include=modules&'),beta.replace('?include=modules','?include=modules%00'),beta.replace('/workers/workers/','/workers/scripts/'),beta.replace('/accounts/','//accounts/'),'https://api.cloudflare.com/client/v4'+beta,beta+'#fragment']
  f=self.case();op=inherited.R2Regressions().opener([f[SCRIPT+'/deployments?page=1&per_page=1']]);get=inherited.R2Regressions().transport(op);get(SCRIPT+'/deployments?page=1&per_page=1')
  for path in variants:
   with self.subTest(path=path):
    try:allowed=b.allowed_path(ACCOUNT,path,selection)
    except ValueError:allowed=False
    self.assertFalse(allowed)
    with self.assertRaises(ValueError):get(path)
  self.assertEqual(len(op.requests),1)
 def test_all_eight_optional_and_header_states_are_distinct(self):
  states=[];beta=inherited.R12AssetsPreservation.BETA
  for base in (False,True):
   for first in (False,True):
    for header in (False,True):
     f=self.case();value=f[beta]['result']
     if base:value['assets']['config']['base_path']='/'
     if first:value['assets']['config']['run_worker_first']=False
     if not header:value['modules']=[]
     state=self.state(f);states.append(state)
     coverage=state['activeDeployment']['versionResourceCoverage'];self.assertEqual(len(coverage),5);self.assertTrue(all(type(v) is bool for v in coverage.values()))
     projection=state['activeDeployment']['versionRuntime']['fields']['assetsPreservation']
     self.assertEqual('base_path' in projection['configFields'],base);self.assertEqual('run_worker_first' in projection['configFields'],first)
     self.assertEqual(projection['headers'],'present_exact_source_bytes' if header else 'absent_source_noop_equivalent')
  self.assertEqual(len({b.digest(s) for s in states}),8)
 def test_same_version_repeat_preserves_raw_identity_time_and_number(self):
  first=self.state(self.case());baseline=first['activeDeployment']['versionRuntime']['fields']['assetsPreservation']
  for field,value in [('id','55555555-5555-5555-5555-555555555555'),('number',2),('created_on','2026-10-16T02:58:19.000000001Z'),('created_on','2026-10-16T11:58:19+09:00')]:
   f=self.case();beta=inherited.R12AssetsPreservation.BETA;v=f[SCRIPT+'/versions/'+VID]['result'];other=f[beta]['result']
   if field=='id':
    v['id']=value;other['id']=value
    for entry in (f[SCRIPT+'/deployments?page=1&per_page=1']['result']['deployments'][0],f[SCRIPT+'/deployments/'+DEP]['result']):entry['versions'][0]['version_id']=value
    f[SCRIPT+'/versions/'+value]=f.pop(SCRIPT+'/versions/'+VID);f[beta.replace(VID,value)]=f.pop(beta)
   elif field=='number':v['number']=value;other['number']=value
   else:v['metadata']['created_on']=value;other['created_on']=value
   second=self.state(f)
   with self.subTest(field=field,value=value):
    self.assertEqual(second['activeDeployment']['versionRuntime']['fields']['assetsPreservation'],baseline)
    self.assertNotEqual(first,second);self.assertNotEqual(b.digest(first),b.digest(second))
    env,event=inherited.Authorization().case()
    with patch.object(b,'trusted_control'),patch.object(b,'provider_get',return_value=(ACCOUNT,None)),patch.object(b,'state_with_diagnostics',side_effect=[first,second]),patch.object(b,'old_public',return_value={}),patch.object(b,'save') as save,self.assertRaisesRegex(ValueError,'provider_changed_across_full_public_check'):b.observe(env,event)
    save.assert_not_called()
 def test_projection_missing_mutated_and_presence_changes_fail_baseline_repeat(self):
  first=self.state(self.case());variants=[]
  for key,value in [('schema','other/v1'),('headers','absent_source_noop_equivalent'),('workerCodeAbsenceProven',True)]:
   second=copy.deepcopy(first);second['activeDeployment']['versionRuntime']['fields']['assetsPreservation'][key]=value;variants.append(second)
  second=copy.deepcopy(first);del second['activeDeployment']['versionRuntime']['fields']['assetsPreservation'];variants.append(second)
  for key,value in [('base_path','/'),('run_worker_first',False)]:
   second=copy.deepcopy(first);second['activeDeployment']['versionRuntime']['fields']['assetsPreservation']['configFields'][key]=value;variants.append(second)
  for second in variants:
   self.assertNotEqual(b.digest(first),b.digest(second));env,event=inherited.Authorization().case()
   with patch.object(b,'trusted_control'),patch.object(b,'provider_get',return_value=(ACCOUNT,None)),patch.object(b,'state_with_diagnostics',side_effect=[first,second]),patch.object(b,'old_public',return_value={}),patch.object(b,'save') as save,self.assertRaisesRegex(ValueError,'provider_changed_across_full_public_check'):b.observe(env,event)
   save.assert_not_called()
 def test_new_validation_codes_do_not_add_legacy_diagnostic_sweep(self):
  beta=inherited.R12AssetsPreservation.BETA;canary=inherited.R12AssetsPreservation.CANARY
  cases=[('version_annotations_type_required',lambda f:f[SCRIPT+'/versions/'+VID]['result'].update(annotations=None)),('version_startup_metric_required',lambda f:f[SCRIPT+'/versions/'+VID]['result'].update(startup_time_ms=True)),('version_assets_object_required',lambda f:f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime'].update(assets=None))]
  for code,mutate in cases:
   f=self.case();mutate(f);seen=[]
   with self.subTest(code=code),patch.object(b,'ACCOUNT_SHA',SHA),patch.object(b,'state_diagnostic_sweep') as sweep,self.assertRaisesRegex(ValueError,'^'+code+'$') as caught:b.state_with_diagnostics({},ACCOUNT,get_for(f,seen))
   self.assertNotIn(code,b.STATE_DIAGNOSTIC_CODES);self.assertNotIn(beta,seen);self.assertNotIn(canary,str(caught.exception));sweep.assert_not_called()
 def test_old_phase1_binding_rejects_baseline_and_additive_workflow(self):
  import recovery_build as q
  review=json.loads(b.read(b.ROOT/'docs/direct-damyang-recovery/phase1-control-review-20261016.json'))
  mismatch={row['path'] for row in review['controlFiles'] if b.sha(b.read(b.ROOT/row['path']))!=row['sha256']}
  self.assertEqual(mismatch,{'scripts/direct-damyang-recovery/'+name for name in ('provider_baseline.py','test_provider_baseline.py','test_damyang_baseline.py')}|{'.github/workflows/damyang-production-publish.yml'})
  with patch.object(q,'git') as git,self.assertRaisesRegex(ValueError,'reviewed_control_file_changed'):q.activation(b.ROOT)
  git.assert_not_called()
 def test_beta_fixed_error_reports_do_not_retain_raw_values(self):
  beta=inherited.R12AssetsPreservation.BETA;f=self.case();f[beta]['result']['modules'][0]['content_base64']=inherited.R12AssetsPreservation.CANARY
  def observe(*args):
   with patch.object(b,'ACCOUNT_SHA',SHA):return b.state_with_diagnostics({},ACCOUNT,get_for(f))
  with patch.object(b,'load_policy',return_value={}),patch.object(b,'read',return_value=b'{}'),patch.object(b,'observe',side_effect=observe),patch.object(b,'save') as save,patch.dict(os.environ,{'GITHUB_EVENT_PATH':'synthetic-event.json'}),patch.object(b.sys,'argv',['provider_baseline.py','observe','--report','fixture-report.json']),patch('sys.stdout',new_callable=io.StringIO) as output,patch.object(b,'state_diagnostic_sweep') as sweep:
   self.assertEqual(b.main(),1)
  report=save.call_args.args[1];self.assertEqual(report,{'state':'BLOCKED_WITH_NO_PROVIDER_MUTATION','code':'selected_assets_headers_bytes','providerMutationsPerformed':False,'baselineAccepted':False});sweep.assert_not_called()
  for raw in (inherited.R12AssetsPreservation.CANARY,ACCOUNT,VID,DEP,'jwt','content_base64'):
   self.assertNotIn(raw,json.dumps(report)+output.getvalue())

class DocumentedOptionalPaginationContract(unittest.TestCase):
 """Shared documented optional metadata; endpoint identity remains exact. All rows synthetic."""
 SCRIPTS='/accounts/'+ACCOUNT+'/workers/scripts'
 DOMAIN='/accounts/'+ACCOUNT+'/workers/domains'
 ACTIVE=SCRIPT+'/deployments?page=1&per_page=1'
 def case(self):
  f=fixtures();del f[self.SCRIPTS]['result_info'];return f
 def state(self,f):
  with patch.object(b,'ACCOUNT_SHA',SHA):return b.current_state(ACCOUNT,get_for(f))
 def test_absent_scripts_info_matches_existing_projection_and_get_bound(self):
  f=self.case();paths=inherited.StateShapeDiagnostics().paths()+[self.ACTIVE]
  op=inherited.R2Regressions().opener([f[path] for path in paths]);get=inherited.R2Regressions().transport(op)
  with patch.object(b,'ACCOUNT_SHA',SHA):actual=b.current_state(ACCOUNT,get)
  self.assertEqual(actual,self.state(fixtures()));self.assertEqual(len(op.requests),9)
  self.assertEqual([r.full_url.removeprefix('https://api.cloudflare.com/client/v4') for r in op.requests],paths)
  for r in op.requests:self.assertEqual(r.get_method(),'GET');self.assertIsNone(r.data)
 def test_shared_single_page_has_no_special_opt_in_or_new_endpoint(self):
  obj=self.case()[self.SCRIPTS];self.assertEqual(b.single_page(obj),obj['result'])
  for flag in [True,False,None,0,1,'true',[],{}]:
   with self.subTest(flag=flag),self.assertRaises(TypeError):b.single_page(obj,nonpaginated=flag)
 def test_all_consistent_optional_metadata_subsets_match_exact_projection(self):
  keys=['page','total_pages','count','total_count','per_page']
  for path in [self.SCRIPTS,self.DOMAIN,self.ACTIVE]:
   for mask in range(32):
    with self.subTest(path=path,mask=mask):
     f=self.case();f[path]['result_info']={k:1 for i,k in enumerate(keys) if mask&(1<<i)}
     self.assertEqual(self.state(f),self.state(fixtures()))
 def test_present_wrong_typed_metadata_values_rejected(self):
  for path in [self.SCRIPTS,self.DOMAIN,self.ACTIVE]:
   for value in [None,True,False,0,1,1.0,'',[],[1]]:
    with self.subTest(path=path,container=value):
     f=self.case();f[path]['result_info']=value
     with self.assertRaisesRegex(ValueError,'provider_pagination_schema'):self.state(f)
   for key in ['page','total_pages','count','total_count','per_page']:
    for value in [None,True,False,-1,1.0,'1',[],{}]:
     with self.subTest(path=path,key=key,value=value):
      f=self.case();f[path]['result_info']={k:1 for k in ['page','total_pages','count','total_count','per_page']};f[path]['result_info'][key]=value
      with self.assertRaisesRegex(ValueError,'provider_pagination_schema'):self.state(f)
 def test_present_metadata_contradictions_unknowns_rejected(self):
  for path in [self.SCRIPTS,self.DOMAIN,self.ACTIVE]:
   for key,value in [('page',0),('page',2),('count',0),('count',2),('per_page',0),('total_count',0),('total_pages',0),('cursor','fixture-pagination-canary')]:
    with self.subTest(path=path,key=key,value=value):
     f=self.case();f[path]['result_info']={k:1 for k in ['page','total_pages','count','total_count','per_page']};f[path]['result_info'][key]=value
     with self.assertRaises(ValueError):self.state(f)
  for path in [self.SCRIPTS,self.DOMAIN]:
   for key,value in [('total_count',2),('total_pages',2)]:
    f=self.case();f[path]['result_info']={k:1 for k in ['page','total_pages','count','total_count','per_page']};f[path]['result_info'][key]=value
    with self.subTest(path=path,key=key),self.assertRaises(ValueError):self.state(f)
 def test_domain_active_optional_metadata_preserves_history_and_first_page_contract(self):
  for path in [self.DOMAIN,self.ACTIVE]:
   f=self.case();del f[path]['result_info']
   with self.subTest(path=path):self.assertEqual(self.state(f),self.state(fixtures()))
  f=self.case();f[self.ACTIVE]['result_info'].update(total_count=12,total_pages=12)
  self.assertEqual(self.state(f),self.state(fixtures()))
 def test_inventory_empty_duplicate_wrong_target_and_typed_ids_stay_blocked(self):
  cases=[[],[{'id':b.WORKER.upper()}],[{'id':'gwangju-gwangsan-flower-guide'}],[{'id':b.WORKER},{'id':b.WORKER}],[{'id':b.WORKER},{'id':'other'},{'id':'other'}]]
  cases += [[{'id':b.WORKER},row] for row in [None,True,0,'fixture-pagination-canary',[],{}, {'id':''},{'id':None},{'id':True},{'id':1},{'id':[]},{'id':{}}]]
  for rows in cases:
   with self.subTest(rows=rows):
    f=self.case();f[self.SCRIPTS]['result']=rows
    with self.assertRaisesRegex(ValueError,'existing_worker_missing_or_ambiguous'):self.state(f)
  f=self.case();f[self.SCRIPTS]['result'].append({'id':'synthetic-other-worker'});self.assertEqual(self.state(f),self.state(fixtures()))
 def test_exact_account_unfiltered_endpoint_and_selected_uuid_guards_stay(self):
  f=self.case();f['/accounts/'+ACCOUNT]['result']['id']='b'*32
  with self.assertRaisesRegex(ValueError,'account_identity_mismatch'):self.state(f)
  with self.assertRaisesRegex(ValueError,'historical_account_digest_mismatch'):b.current_state(ACCOUNT,get_for(self.case()))
  op=inherited.R2Regressions().opener([]);get=inherited.R2Regressions().transport(op)
  for path in [self.SCRIPTS+'?tags=x:yes',self.SCRIPTS+'?page=1',self.SCRIPTS+'/',self.SCRIPTS.replace(ACCOUNT,'b'*32),SCRIPT.replace(b.WORKER,'gwangju-gwangsan-flower-guide')+'/settings',SCRIPT+'/versions/latest',SCRIPT+'/versions/'+VID[:8],SCRIPT+'/versions/'+VID,SCRIPT+'/deployments/'+DEP]:
   with self.subTest(path=path),self.assertRaises(ValueError):get(path)
  self.assertEqual(len(op.requests),0)
 def test_envelope_rejects_bad_success_errors_messages_unknown_key_once(self):
  variants=[]
  for key,values in [('success',[False,1,None]),('errors',[None,False,{},[{'message':'fixture-pagination-canary'}]]),('messages',[None,False,{}])]:
   for value in values:
    obj=self.case()[self.SCRIPTS];obj[key]=value;variants.append(obj)
  obj=self.case()[self.SCRIPTS];obj['fixture-pagination-canary']=True;variants.append(obj)
  for obj in variants:
   with self.subTest(case=len(variants)):
    op=inherited.R2Regressions().opener([obj]);get=inherited.R2Regressions().transport(op)
    with self.assertRaises(b.ProviderEnvelopeError) as error:get(self.SCRIPTS)
    self.assertEqual(len(op.requests),1);self.assertNotIn('fixture-pagination-canary',json.dumps(error.exception.diagnostic))
 def test_fresh_sweep_absent_scripts_shape_and_inventory_gate_agree(self):
  result,op=inherited.StateShapeDiagnostics().run_sweep(self.case())
  self.assertEqual(result['state'],'BOUNDED_DIAGNOSTIC_SWEEP_FINISHED_NOT_A_BASELINE');self.assertEqual(len(op.requests),8)
  self.assertIs(result['checks']['fixedWorkerInventoryGate'],True);shape=result['endpoints']['scripts-list']['shape']
  self.assertIs(shape['checks']['singlePageComplete'],True);self.assertEqual(shape['envelope']['expectedFields']['result_info'],{'present':False,'type':'absent'})
  for flag in ['baselineAccepted','publicationEligible','providerMutationsPerformed']:self.assertIs(result[flag],False)
  for forbidden in [ACCOUNT,DEP,VID,'fixture-token','not-retained','do-not-retain']:self.assertNotIn(forbidden,json.dumps(result))
 def test_fresh_sweep_optional_metadata_consistent_with_normal_validation(self):
  for path in [self.SCRIPTS,self.DOMAIN,self.ACTIVE]:
   f=self.case()
   if path==self.SCRIPTS:f[path]['result_info']={}
   else:del f[path]['result_info']
   with self.subTest(path=path):
    result,op=inherited.StateShapeDiagnostics().run_sweep(f);self.assertEqual(len(op.requests),8);self.assertIs(result['baselineAccepted'],False)
    self.assertEqual(result['state'],'BOUNDED_DIAGNOSTIC_SWEEP_FINISHED_NOT_A_BASELINE')
 def test_repeated_active_response_equality_and_original_error_are_preserved(self):
  f=self.case();seen=[]
  def get(path):
   seen.append(path);obj=copy.deepcopy(f[path])
   if path==self.ACTIVE and seen.count(path)==2:obj['result']['deployments'][0]['annotations']['workers/message']='fixture-pagination-canary'
   return obj
  with patch.object(b,'ACCOUNT_SHA',SHA),self.assertRaisesRegex(ValueError,'active_deployment_changed_during_observation'):b.current_state(ACCOUNT,get)
  self.assertEqual(seen.count(self.ACTIVE),2)
  fresh={'schema':'synthetic-diagnostic','baselineAccepted':False}
  f=self.case();f[self.DOMAIN]['result_info']={'total_pages':2}
  with patch.object(b,'ACCOUNT_SHA',SHA),patch.object(b,'state_diagnostic_sweep',return_value=fresh) as sweep,self.assertRaises(b.ProviderStateDiagnosticError) as caught:b.state_with_diagnostics({},ACCOUNT,get_for(f))
  self.assertEqual(caught.exception.original_code,'provider_list_completeness_unverified');self.assertEqual(caught.exception.diagnostic,fresh);sweep.assert_called_once_with({})

 def test_scripts_absence_does_not_bypass_result_or_later_state_validation(self):
  for value in [None,False,0,'fixture-pagination-canary',{}]:
   f=self.case();f[self.SCRIPTS]['result']=value
   with self.subTest(result=value),self.assertRaisesRegex(ValueError,'provider_list_schema'):self.state(f)
  f=self.case();del f[self.SCRIPTS]['result']
  with self.assertRaisesRegex(ValueError,'provider_list_schema'):self.state(f)
  mutations=[lambda f:f[self.DOMAIN]['result'][0].update(hostname='gwangju-gwangsan.fwith.kr'),lambda f:f[SCRIPT+'/settings']['result'].update(bindings=[{'type':'secret_text','name':'fixture-pagination-canary'}]),lambda f:f[SCRIPT+'/versions/'+VID]['result'].update(id='33333333-3333-3333-3333-333333333333'),lambda f:f[SCRIPT+'/versions/'+VID]['result']['resources'].update(future_capability={}),lambda f:f[SCRIPT+'/versions/'+VID]['result']['resources']['script_runtime'].update(exports={'default':{}})]
  for i,mutate in enumerate(mutations):
   f=self.case();mutate(f)
   with self.subTest(later=i),self.assertRaises(ValueError):self.state(f)

class CompleteEndpointPaginationReuse(unittest.TestCase):
 """Cross-endpoint official optional metadata and preserved Damyang identity."""
 SCRIPTS='/accounts/'+ACCOUNT+'/workers/scripts';DOMAIN='/accounts/'+ACCOUNT+'/workers/domains';ACTIVE=SCRIPT+'/deployments?page=1&per_page=1'
 def state(self,f):
  with patch.object(b,'ACCOUNT_SHA',SHA):return b.current_state(ACCOUNT,get_for(f))
 def observed_shape(self,assets=False):
  f=inherited.R12AssetsPreservation.fixtures() if assets else fixtures()
  del f[self.SCRIPTS]['result_info'];del f[self.DOMAIN]['result_info']['total_pages']
  f[self.DOMAIN].update(errors=None,messages=None)
  return f
 def test_known_cross_region_domain_shape_preserves_full_damyang_projection(self):
  for assets in (False,True):
   f=self.observed_shape(assets);original=inherited.R12AssetsPreservation.fixtures() if assets else fixtures()
   with self.subTest(assets=assets):self.assertEqual(self.state(f),self.state(original))
   seen=[]
   with patch.object(b,'ACCOUNT_SHA',SHA):b.current_state(ACCOUNT,get_for(f,seen))
   self.assertEqual(len(seen),10 if assets else 9);self.assertEqual(seen.count(self.ACTIVE),2)
 def test_observed_nullable_domain_four_fields_diagnostic_advances_without_acceptance(self):
  report,op=inherited.StateShapeDiagnostics().run_sweep(self.observed_shape())
  self.assertEqual(len(op.requests),8);self.assertEqual(report['state'],'BOUNDED_DIAGNOSTIC_SWEEP_FINISHED_NOT_A_BASELINE')
  shape=report['endpoints']['domains-list']['shape'];self.assertIs(shape['checks']['singlePageComplete'],True)
  self.assertEqual(shape['fields']['pagination']['total_pages'],{'present':False,'type':'absent'})
  for key in ['baselineAccepted','publicationEligible','providerMutationsPerformed']:self.assertIs(report[key],False)
 def test_all_endpoint_omission_combinations_keep_exact_fixed_state(self):
  for mask in range(8):
   f=fixtures()
   for i,path in enumerate([self.SCRIPTS,self.DOMAIN,self.ACTIVE]):
    if mask&(1<<i):del f[path]['result_info']
   with self.subTest(mask=mask):self.assertEqual(self.state(f),self.state(fixtures()))
 def test_nullable_domain_absence_still_rejected_by_unchanged_envelope(self):
  f=self.observed_shape();del f[self.DOMAIN]['result_info']
  op=inherited.R2Regressions().opener([f[self.DOMAIN]]);get=inherited.R2Regressions().transport(op)
  with self.assertRaises(b.ProviderEnvelopeError):get(self.DOMAIN)
  self.assertEqual(len(op.requests),1)
 def test_optional_metadata_never_relaxes_exact_damyang_binding_or_both_exposure_flags(self):
  changes=[lambda f:f[self.DOMAIN]['result'][0].update(hostname='gwangju-gwangsan.fwith.kr'),lambda f:f[self.DOMAIN]['result'][0].update(service='gwangju-gwangsan-flower-guide'),lambda f:f[self.DOMAIN]['result'].append(copy.deepcopy(f[self.DOMAIN]['result'][0])),lambda f:f[self.DOMAIN]['result'][0].update(zone_name='other.invalid'),lambda f:f[SCRIPT+'/subdomain']['result'].update(previews_enabled=True),lambda f:f[SCRIPT+'/subdomain']['result'].update(enabled=True)]
  for i,change in enumerate(changes):
   f=self.observed_shape();change(f)
   with self.subTest(change=i),self.assertRaises(ValueError):self.state(f)
 def test_optional_active_metadata_still_requires_one_full_traffic_uuid(self):
  variants=[[],[{'version_id':VID,'percentage':50}],[{'version_id':VID,'percentage':100},{'version_id':VID,'percentage':0}],[{'version_id':'latest','percentage':100}],[{'version_id':VID,'percentage':True}]]
  for row in variants:
   f=self.observed_shape();f[self.ACTIVE]['result_info']={};f[self.ACTIVE]['result']['deployments'][0]['versions']=row
   with self.subTest(versions=row),self.assertRaisesRegex(ValueError,'single_full_traffic_version_required'):self.state(f)
  for deployments in [[],[copy.deepcopy(fixtures()[self.ACTIVE]['result']['deployments'][0])]*2]:
   f=self.observed_shape();f[self.ACTIVE]['result_info']={};f[self.ACTIVE]['result']['deployments']=deployments
   with self.subTest(count=len(deployments)),self.assertRaisesRegex(ValueError,'active_deployment_ambiguous_or_missing'):self.state(f)
 def test_optional_fields_do_not_normalize_contradictory_count_or_later_page(self):
  for path in [self.SCRIPTS,self.DOMAIN,self.ACTIVE]:
   cases=[{'page':2},{'page':0},{'count':0},{'count':2},{'per_page':0},{'total_count':0},{'total_pages':0},{'cursor':'fixture-canary'}]
   if path!=self.ACTIVE:cases += [{'total_pages':2},{'total_count':2}]
   else:cases += [{'per_page':2}]
   for info in cases:
    f=fixtures();f[path]['result_info']=info
    with self.subTest(path=path,info=info),self.assertRaises(ValueError):self.state(f)
 def test_optional_shape_then_detail_version_and_public_guard_errors_remain(self):
  changes=[lambda f:f[SCRIPT+'/deployments/'+DEP]['result'].update(source='changed'),lambda f:f[SCRIPT+'/versions/'+VID]['result'].update(id='33333333-3333-3333-3333-333333333333'),lambda f:f[SCRIPT+'/settings']['result'].update(logpush=True),lambda f:f[SCRIPT+'/settings']['result'].update(bindings=[{'type':'secret_text','name':'fixture-canary'}])]
  for i,change in enumerate(changes):
   f=self.observed_shape();change(f)
   with self.subTest(change=i),self.assertRaises(ValueError):self.state(f)
