"""Exact one-revision existing-host update gates. Provider transport is GET-only."""
import datetime,json,os,re
from pathlib import Path
import provider_baseline as baseline
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
require=baseline.require;sha=baseline.sha;digest=baseline.digest;read=baseline.read;save=baseline.save
PREVIOUS=baseline.PREVIOUS;CURRENT=baseline.CURRENT;HOST=baseline.HOST;WORKER=baseline.WORKER
MARKER='<!-- gwangsan-policy-correction-attempt-v1 -->\n'

def doc(path,expected):
 require(isinstance(path,str) and path.startswith('docs/direct-gwangju-gwangsan-policy-correction/') and '..' not in Path(path).parts and '\\' not in path,'correction_document_path_invalid');require(re.fullmatch('[0-9a-f]{64}',expected or ''),'correction_document_digest_required');raw=read(ROOT/path);require(sha(raw)==expected,'correction_document_digest_mismatch');return json.loads(raw)

def accepted_baseline():
 desc=json.loads(read(D/'accepted-provider-baseline-binding.json'))
 keys={'schema','state','path','sha256','reviewPath','reviewSHA256','observationRunId','observationControlRevision','observationArtifactId','observationArtifactDigest'}
 require(type(desc) is dict and set(desc)==keys and desc['schema']=='gwangsan-accepted-provider-baseline-binding/v1' and desc['state']=='INDEPENDENTLY_ACCEPTED_CURRENT_BASELINE','independent_current_baseline_acceptance_required')
 for k in ['observationRunId','observationArtifactId']:require(type(desc[k]) is int and desc[k]>0,'actual_baseline_run_artifact_required')
 require(re.fullmatch('[0-9a-f]{40}',desc['observationControlRevision'] or '') and re.fullmatch('sha256:[0-9a-f]{64}',desc['observationArtifactDigest'] or ''),'actual_baseline_archive_identity_required')
 obs=doc(desc['path'],desc['sha256']);review=doc(desc['reviewPath'],desc['reviewSHA256'])
 expected={'schema':'gwangsan-current-provider-baseline-observation/v1','state':'OBSERVED_NOT_ACCEPTED_FOR_MUTATION','policySHA256':baseline.POLICY_SHA,'previousSourceRevision':PREVIOUS,'correctionSourceRevision':CURRENT,'previousPublicationRunId':38843104514,'historicalProviderVersionKnown':False,'providerMethods':['GET'],'providerMutationsPerformed':False,'IndexNowSubmitted':False,'baselineAccepted':False,'publicationEligible':False}
 require(type(obs) is dict and all(baseline.canonical(obs.get(k))==baseline.canonical(v) for k,v in expected.items()),'observed_baseline_identity_mismatch')
 identity=obs['identity'];require(identity['repository']==baseline.REPO and identity['controlRevision']==desc['observationControlRevision'] and identity['runId']==str(desc['observationRunId']) and identity['runAttempt']==1 and identity['providerMethods']==['GET'] and identity['providerMutationsPerformed'] is False,'baseline_run_identity_mismatch')
 state=obs['currentProviderState'];require(digest(state)==obs['currentProviderStateSHA256'] and state['accountSHA256']==baseline.ACCOUNT_SHA and state['hostname']==HOST and state['worker']==WORKER,'baseline_state_digest_mismatch')
 p=obs['previousPublicHTTP'];require(p['state']=='public_release_verified' and p['revision']==PREVIOUS and p['checkedPaths']==17 and p['unknownHttpStatus']==404,'full_previous_public_verification_required')
 expectedReview={'schema':'gwangsan-current-provider-baseline-independent-review/v1','verdict':'ACCEPT_CURRENT_GET_ONLY_BASELINE_FOR_EXACT_CORRECTION','previousSourceRevision':PREVIOUS,'correctionSourceRevision':CURRENT,'observationSHA256':desc['sha256'],'currentProviderStateSHA256':obs['currentProviderStateSHA256'],'observationRunId':desc['observationRunId'],'observationControlRevision':desc['observationControlRevision'],'observationArtifactId':desc['observationArtifactId'],'observationArtifactDigest':desc['observationArtifactDigest'],'actualLiveGETVerified':True,'priorPublic17Verified':True,'singleVersion100Verified':True,'settingsAndBindingReviewed':True,'noRawSecretValuesPublished':True,'historicalProviderVersionKnown':False,'publicationApproved':False}
 require(type(review) is dict and all(baseline.canonical(review.get(k))==baseline.canonical(v) for k,v in expectedReview.items()) and isinstance(review.get('reviewer'),str) and review['reviewer'].strip(),'independent_baseline_review_required')
 return desc,obs,review

def observe_current():
 baseline.load_policy();account,get=baseline.provider_get(os.environ);return baseline.current_state(account,get)

def source_config():
 expected={'name':WORKER,'compatibility_date':'2026-10-09','workers_dev':False,'assets':{'directory':'./dist/','not_found_handling':'404-page','html_handling':'auto-trailing-slash'}}
 source=json.loads(read(Path('update-source-config.json') if Path('update-source-config.json').exists() else Path('release/wrangler.publish.json')));require(baseline.canonical(source)==baseline.canonical(expected),'exact_static_source_configuration_required');return source

def exact_assets_config(source,state):
 import assets_only
 policy={'worker':WORKER,'productionOrigin':'https://'+HOST,'providerBaselineSha256':{'production':digest(state)}}
 config=assets_only.configuration(policy,'production',source,state)
 require(set(config)=={'name','compatibility_date','workers_dev','assets','preview_urls','compatibility_flags','logpush','observability'} and 'routes' not in config and 'route' not in config and 'main' not in config,'route_less_static_configuration_required');return config

def preflight():
 desc,obs,_=accepted_baseline();first=observe_current();require(baseline.canonical(first)==baseline.canonical(obs['currentProviderState']),'accepted_provider_baseline_changed')
 public=baseline.old_public(baseline.load_policy());save('previous-public-http.json',public);second=observe_current();require(baseline.canonical(first)==baseline.canonical(second),'provider_changed_during_preflight')
 source=source_config();config=exact_assets_config(source,first);save('update-source-config.json',source);save('provider-state-before.json',first);save('release/wrangler.publish.json',config)
 return {'state':'EXACT_ACCEPTED_EXISTING_TARGET_RECHECKED','sourceRevision':CURRENT,'previousSourceRevision':PREVIOUS,'providerBaselineBindingSHA256':sha(read(D/'accepted-provider-baseline-binding.json')),'acceptedObservationSHA256':desc['sha256'],'providerStateSHA256':digest(first),'previousPublicPaths':public['checkedPaths'],'providerMethods':['GET'],'providerMutationsPerformed':False,'hostnameAttachAllowed':False,'startedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}

def attempt_identity(review,env):
 require(env.get('GITHUB_RUN_ATTEMPT')=='1' and re.fullmatch('[1-9][0-9]*',env.get('GITHUB_RUN_ID','')) and re.fullmatch('[0-9a-f]{40}',env.get('GITHUB_SHA','')),'exact_correction_run_required')
 desc,obs,_=accepted_baseline();return {'schema':'gwangsan-policy-correction-deployment-attempt/v1','repository':baseline.REPO,'hostname':HOST,'worker':WORKER,'previousSourceRevision':PREVIOUS,'sourceRevision':CURRENT,'providerBaselineBindingSHA256':sha(read(D/'accepted-provider-baseline-binding.json')),'providerStateSHA256':obs['currentProviderStateSHA256'],'buildRunId':review['buildRunId'],'artifactId':review['artifactId'],'artifactDigest':review['artifactDigest'],'outputFilesSha256':review['outputFilesSha256'],'releaseManifestSha256':review['releaseManifestSha256'],'runId':env['GITHUB_RUN_ID'],'controlRevision':env['GITHUB_SHA'],'runAttempt':1}

def select_claim(comments,identity):
 require(type(comments) is list,'complete_journal_comments_required');prior_receipt=False
 for comment in comments:
  require(type(comment) is dict,'malformed_journal_comment');login=comment.get('user',{}).get('login');body=comment.get('body','');require(isinstance(body,str),'malformed_journal_comment_body')
  if login!='github-actions[bot]':continue
  if body.startswith(MARKER):
   try:r=json.loads(body[len(MARKER):])
   except Exception:raise ValueError('malformed_durable_attempt_record') from None
   require(type(r) is dict,'malformed_durable_attempt_record')
   # Any prior attempt for this correction revision blocks another upload, including unknown/failed runs.
   require(r.get('sourceRevision')!=CURRENT,'prior_correction_attempt_requires_manual_reconciliation')
  if body.startswith('SITE_FACTORY_INDEXNOW_V1 '):
   try:r=json.loads(body[len('SITE_FACTORY_INDEXNOW_V1 '):])
   except Exception:raise ValueError('malformed_historical_receipt_record') from None
   require(type(r) is dict,'malformed_historical_receipt_record')
   if r.get('fingerprint')=='65f8222e699c20936e0db849128cedc817d033c34b1056f5e40ac06464ef3c75' and r.get('revision')==PREVIOUS and r.get('state')=='received' and type(r.get('httpStatus')) is int and r['httpStatus']==200:prior_receipt=True
 require(prior_receipt,'original_received_journal_record_required')
 return dict(identity,state='STARTED_NO_AUTOMATIC_REUPLOAD',recordedAtUTC=datetime.datetime.now(datetime.timezone.utc).isoformat())

def claim_timestamp(value):
 # Claims are generated in UTC at microsecond precision. Do not floor a claim.
 require(type(value) is str and bool(re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|\+00:00)',value)),'invalid_claim_timestamp')
 return baseline.timestamp(value)

def verify_claim(review,env):
 record=json.loads(read('deployment-attempt-claim.json'));expected=attempt_identity(review,env)
 require(type(record) is dict and set(record)==set(expected)|{'state','recordedAtUTC','commentId'} and all(baseline.canonical(record[k])==baseline.canonical(v) for k,v in expected.items()) and record['state']=='STARTED_NO_AUTOMATIC_REUPLOAD' and type(record['commentId']) is int and record['commentId']>0,'durable_exact_attempt_claim_required');claim_timestamp(record['recordedAtUTC']);return record

def recheck(review,env):
 record=verify_claim(review,env);desc,obs,_=accepted_baseline();current=observe_current();require(baseline.canonical(current)==baseline.canonical(obs['currentProviderState'])==baseline.canonical(json.loads(read('provider-state-before.json'))),'provider_changed_before_single_upload');baseline.old_public(baseline.load_policy());require(baseline.canonical(observe_current())==baseline.canonical(current),'provider_changed_after_final_public_check');require(baseline.canonical(json.loads(read('release/wrangler.publish.json')))==baseline.canonical(exact_assets_config(source_config(),current)),'static_configuration_changed_before_upload');return {'state':'READY_FOR_ONE_CLAIMED_STATIC_UPLOAD','sourceRevision':CURRENT,'commentId':record['commentId'],'providerMethods':['GET'],'providerMutationsPerformed':False}

def readback(review,env):
 record=verify_claim(review,env);desc,obs,_=accepted_baseline();current=observe_current();save('provider-state-after-observed.json',current);old=obs['currentProviderState'];require(baseline.canonical({k:v for k,v in current.items() if k!='activeDeployment'})==baseline.canonical({k:v for k,v in old.items() if k!='activeDeployment'}),'existing_settings_account_binding_or_exposure_changed')
 upload=json.loads(read('upload-version.json'));require(type(upload) is dict and set(upload)=={'state','versionIdSHA256','runId','sourceRevision'} and upload['state']=='ONE_UPLOAD_SUCCEEDED_VERSION_PARSED' and upload['runId']==env['GITHUB_RUN_ID'] and upload['sourceRevision']==CURRENT,'actual_upload_version_required')
 active=current['activeDeployment'];require(all(baseline.canonical(active[k])==baseline.canonical(old['activeDeployment'][k]) for k in ('versionRuntime','versionScript')),'version_static_capabilities_changed');require(active['versionIdSHA256']==upload['versionIdSHA256'] and active['versionIdSHA256']!=old['activeDeployment']['versionIdSHA256'] and active['deploymentIdSHA256']!=old['activeDeployment']['deploymentIdSHA256'],'new_exact_uploaded_version_not_active')
 require(baseline.timestamp(active['deploymentCreatedOn'])>=claim_timestamp(record['recordedAtUTC'])-datetime.timedelta(seconds=60),'active_deployment_predates_claim')
 require(baseline.canonical(json.loads(read('release/wrangler.publish.json')))==baseline.canonical(exact_assets_config(source_config(),old)),'static_configuration_changed_after_upload')
 return {'state':'EXACT_NEW_VERSION_AND_UNCHANGED_BINDING_VERIFIED','sourceRevision':CURRENT,'previousSourceRevision':PREVIOUS,'accountSHA256':baseline.ACCOUNT_SHA,'hostname':HOST,'worker':WORKER,'currentProviderStateSHA256':digest(current),'deploymentIdSHA256':active['deploymentIdSHA256'],'versionIdSHA256':active['versionIdSHA256'],'providerMethods':['GET'],'providerMutationsPerformed':False,'hostnameAttached':False,'publicHTTPVerified':False}

def extract_upload_version(log,env):
 require(env.get('GITHUB_RUN_ATTEMPT')=='1','first_attempt_required');text=re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',read(log).decode('utf-8','replace'));ids=re.findall(r'(?m)^\s*Current Version ID:\s*('+baseline.UUID+r')\s*$',text);require(len(ids)==1,'single_uploaded_version_id_required');return {'state':'ONE_UPLOAD_SUCCEEDED_VERSION_PARSED','versionIdSHA256':sha(ids[0].encode()),'runId':env['GITHUB_RUN_ID'],'sourceRevision':CURRENT}
