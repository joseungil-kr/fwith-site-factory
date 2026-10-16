"""Damyang-only recovery update gates. Local proposal; no deployment or network CLI.

Adapted from the existing Gwangsan updater. Baseline/QA acceptance and durable
GitHub claim transport must be independently reviewed before workflow use."""
import datetime,json,os,re
from pathlib import Path
import provider_baseline as baseline
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
require=baseline.require;sha=baseline.sha;digest=baseline.digest;read=baseline.read;save=baseline.save
PREVIOUS=baseline.PREVIOUS;CURRENT=baseline.CURRENT;HOST=baseline.HOST;WORKER=baseline.WORKER
MARKER='<!-- damyang-proof-recovery-attempt-v1 -->\n'

def doc(path,expected):
 require(isinstance(path,str) and path.startswith('docs/direct-damyang-recovery/') and '..' not in Path(path).parts and '\\' not in path,'correction_document_path_invalid');require(re.fullmatch('[0-9a-f]{64}',expected or ''),'correction_document_digest_required');raw=read(ROOT/path);require(sha(raw)==expected,'correction_document_digest_mismatch');return json.loads(raw)

def accepted_baseline():
 desc=json.loads(read(D/'accepted-provider-baseline-binding.json'))
 keys={'schema','state','path','sha256','reviewPath','reviewSHA256','observationRunId','observationControlRevision','observationArtifactId','observationArtifactDigest'}
 require(type(desc) is dict and set(desc)==keys and desc['schema']=='damyang-recovery-accepted-provider-baseline-binding/v1' and desc['state']=='INDEPENDENTLY_ACCEPTED_CURRENT_BASELINE','independent_current_baseline_acceptance_required')
 for k in ['observationRunId','observationArtifactId']:require(type(desc[k]) is int and desc[k]>0,'actual_baseline_run_artifact_required')
 require(re.fullmatch('[0-9a-f]{40}',desc['observationControlRevision'] or '') and re.fullmatch('sha256:[0-9a-f]{64}',desc['observationArtifactDigest'] or ''),'actual_baseline_archive_identity_required')
 obs=doc(desc['path'],desc['sha256']);review=doc(desc['reviewPath'],desc['reviewSHA256'])
 expected={'schema':'damyang-recovery-current-provider-baseline-observation/v1','state':'OBSERVED_NOT_ACCEPTED_FOR_MUTATION','policySHA256':baseline.POLICY_SHA,'previousSourceRevision':PREVIOUS,'correctionSourceRevision':CURRENT,'previousPublicationRunId':38861200090,'historicalProviderVersionKnown':False,'providerMethods':['GET'],'providerMutationsPerformed':False,'IndexNowSubmitted':False,'baselineAccepted':False,'publicationEligible':False}
 require(type(obs) is dict and all(baseline.canonical(obs.get(k))==baseline.canonical(v) for k,v in expected.items()),'observed_baseline_identity_mismatch')
 identity=obs['identity'];require(identity['repository']==baseline.REPO and identity['controlRevision']==desc['observationControlRevision'] and identity['runId']==str(desc['observationRunId']) and identity['runAttempt']==1 and identity['providerMethods']==['GET'] and identity['providerMutationsPerformed'] is False,'baseline_run_identity_mismatch')
 state=obs['currentProviderState'];require(digest(state)==obs['currentProviderStateSHA256'] and state['accountSHA256']==baseline.ACCOUNT_SHA and state['hostname']==HOST and state['worker']==WORKER,'baseline_state_digest_mismatch')
 p=obs['previousPublicHTTP'];require(p['state']=='public_release_verified' and p['revision']==PREVIOUS and p['checkedPaths']==15 and p['unknownHttpStatus']==404,'full_previous_public_verification_required')
 expectedReview={'schema':'damyang-recovery-current-provider-baseline-independent-review/v1','verdict':'ACCEPT_CURRENT_GET_ONLY_BASELINE_FOR_DAMYANG_PROOF_RECOVERY','previousSourceRevision':PREVIOUS,'correctionSourceRevision':CURRENT,'observationSHA256':desc['sha256'],'currentProviderStateSHA256':obs['currentProviderStateSHA256'],'observationRunId':desc['observationRunId'],'observationControlRevision':desc['observationControlRevision'],'observationArtifactId':desc['observationArtifactId'],'observationArtifactDigest':desc['observationArtifactDigest'],'actualLiveGETVerified':True,'priorPublic15Verified':True,'singleVersion100Verified':True,'settingsAndBindingReviewed':True,'noRawSecretValuesPublished':True,'historicalProviderVersionKnown':False,'publicationApproved':False}
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
 desc,obs,_=accepted_baseline();return {'schema':'damyang-proof-recovery-deployment-attempt/v1','repository':baseline.REPO,'hostname':HOST,'worker':WORKER,'previousSourceRevision':PREVIOUS,'sourceRevision':CURRENT,'providerBaselineBindingSHA256':sha(read(D/'accepted-provider-baseline-binding.json')),'providerStateSHA256':obs['currentProviderStateSHA256'],'buildRunId':review['buildRunId'],'artifactId':review['artifactId'],'artifactDigest':review['artifactDigest'],'outputFilesSha256':review['outputFilesSha256'],'releaseManifestSha256':review['releaseManifestSha256'],'runId':env['GITHUB_RUN_ID'],'controlRevision':env['GITHUB_SHA'],'runAttempt':1}

def _journal_contract():
 import indexnow_recovery as receipt
 contract=receipt.Contract('db5e090bdb87762ce7c7ec5c01f6ab73','39c4ed924bc6084c670a963c26d9f018')
 require(receipt.sha((contract.active_key+'\n').encode())==receipt.ACTIVE_PROOF_SHA256 and receipt.sha((contract.retained_key+'\n').encode())==receipt.RETAINED_PROOF_SHA256,'pinned_public_proofs_required')
 return receipt,contract

def inspect_full_journal(pages,own_claim=None):
 """Use unfiltered authenticated repository pages, never issue-only list/search."""
 receipt,contract=_journal_contract()
 require(type(pages) is list and pages,'complete_repository_journal_pages_required')
 require(all(type(p) is receipt.AuditPage for p in pages),'trusted_repository_journal_pages_required')
 for number,page in enumerate(pages,1):
  require(page.url==receipt.page_url(number),'canonical_repository_page_required')
  if number<len(pages):require(page.next_url==receipt.page_url(number+1) and len(page.comments)==100,'complete_chained_repository_pages_required')
  else:require(page.next_url is None and len(page.comments)<100,'unambiguous_repository_end_required')
 def read_page(number):
  require(1<=number<=len(pages),'repository_journal_page_missing')
  return pages[number-1]
 audit=receipt.audit_chain(read_page,contract)
 require(not audit.successor,'indexnow_recovery_already_started_or_spent')
 require(pages[-1].next_url is None,'last_repository_page_incomplete')
 claims=[]
 for page in pages:
  for comment in page.comments:
   body=comment['body']
   if MARKER not in body:continue
   require(body.startswith(MARKER),'misplaced_update_claim_marker')
   record=receipt.strict_json(body[len(MARKER):]);receipt._trusted_comment(comment)
   # A new source/fingerprint/attempt field cannot erase a previous host claim.
   relevant=(record.get('hostname')==HOST or record.get('sourceRevision')==CURRENT or record.get('previousSourceRevision')==PREVIOUS)
   require(relevant,'unexpected_update_claim_identity')
   claims.append((comment['id'],record))
 if own_claim is None:
  require(not claims,'prior_damyang_update_attempt_requires_reconciliation')
 else:
  expected={k:v for k,v in own_claim.items() if k!='commentId'}
  require(len(claims)==1 and claims[0][0]==own_claim['commentId'] and baseline.canonical(claims[0][1])==baseline.canonical(expected),'durable_claim_not_exclusive_or_readback_mismatch')
 return True

def select_claim(pages,identity):
 inspect_full_journal(pages)
 require(identity.get('hostname')==HOST and identity.get('worker')==WORKER and identity.get('sourceRevision')==CURRENT and identity.get('previousSourceRevision')==PREVIOUS,'fixed_damyang_update_identity_required')
 return dict(identity,state='STARTED_NO_AUTOMATIC_REUPLOAD',recordedAtUTC=datetime.datetime.now(datetime.timezone.utc).isoformat())

def validate_claim_echo(record,comment,pages):
 receipt,_=_journal_contract();receipt._trusted_comment(comment)
 require(comment['body'].startswith(MARKER) and baseline.canonical(receipt.strict_json(comment['body'][len(MARKER):]))==baseline.canonical(record),'claim_write_echo_mismatch')
 claim=dict(record,commentId=comment['id']);claim_timestamp(claim['recordedAtUTC']);inspect_full_journal(pages,own_claim=claim)
 return claim

def claim_timestamp(value):
 # Claims are generated in UTC at microsecond precision. Do not floor a claim.
 require(type(value) is str and bool(re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|\+00:00)',value)),'invalid_claim_timestamp')
 return baseline.timestamp(value)

def exact_provider_instant_ns(value):
 # Extra upper-bound checks must not accept a sub-microsecond future value by flooring.
 parsed=baseline.timestamp(value).astimezone(datetime.timezone.utc)
 fraction=re.fullmatch(r'.*T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.([0-9]{1,9}))?(?:Z|[+-][0-9]{2}:[0-9]{2})',value).group(1) or ''
 delta=parsed-datetime.datetime(1970,1,1,tzinfo=datetime.timezone.utc)
 tail=int(fraction[6:].ljust(3,'0')) if len(fraction)>6 else 0
 return (delta.days*86400+delta.seconds)*1000000000+delta.microseconds*1000+tail

def verify_claim(review,env):
 record=json.loads(read('deployment-attempt-claim.json'));expected=attempt_identity(review,env)
 require(type(record) is dict and set(record)==set(expected)|{'state','recordedAtUTC','commentId'} and all(baseline.canonical(record[k])==baseline.canonical(v) for k,v in expected.items()) and record['state']=='STARTED_NO_AUTOMATIC_REUPLOAD' and type(record['commentId']) is int and record['commentId']>0,'durable_exact_attempt_claim_required');claim_timestamp(record['recordedAtUTC']);return record

def recheck(review,env):
 record=verify_claim(review,env);desc,obs,_=accepted_baseline();current=observe_current();require(baseline.canonical(current)==baseline.canonical(obs['currentProviderState'])==baseline.canonical(json.loads(read('provider-state-before.json'))),'provider_changed_before_single_upload');baseline.old_public(baseline.load_policy());require(baseline.canonical(observe_current())==baseline.canonical(current),'provider_changed_after_final_public_check');require(baseline.canonical(json.loads(read('release/wrangler.publish.json')))==baseline.canonical(exact_assets_config(source_config(),current)),'static_configuration_changed_before_upload');return {'state':'READY_FOR_ONE_CLAIMED_STATIC_UPLOAD','sourceRevision':CURRENT,'commentId':record['commentId'],'providerMethods':['GET'],'providerMutationsPerformed':False}

def readback(review,env):
 record=verify_claim(review,env);desc,obs,_=accepted_baseline();current=observe_current();save('provider-state-after-observed.json',current);old=obs['currentProviderState'];require(baseline.canonical({k:v for k,v in current.items() if k!='activeDeployment'})==baseline.canonical({k:v for k,v in old.items() if k!='activeDeployment'}),'existing_settings_account_binding_or_exposure_changed')
 upload=json.loads(read('upload-version.json'));require(type(upload) is dict and set(upload)=={'state','versionIdSHA256','runId','sourceRevision'} and upload['state']=='ONE_UPLOAD_SUCCEEDED_VERSION_PARSED' and upload['runId']==env['GITHUB_RUN_ID'] and upload['sourceRevision']==CURRENT,'actual_upload_version_required')
 active=current['activeDeployment'];require(all(baseline.canonical(active[k])==baseline.canonical(old['activeDeployment'][k]) for k in ('versionRuntime','versionScript','versionResourceCoverage')),'version_static_capabilities_changed');require(active['versionIdSHA256']==upload['versionIdSHA256'] and active['versionIdSHA256']!=old['activeDeployment']['versionIdSHA256'] and active['deploymentIdSHA256']!=old['activeDeployment']['deploymentIdSHA256'],'new_exact_uploaded_version_not_active')
 require(baseline.timestamp(active['deploymentCreatedOn'])>=claim_timestamp(record['recordedAtUTC'])-datetime.timedelta(seconds=60),'active_deployment_predates_claim')
 require(exact_provider_instant_ns(active['deploymentCreatedOn'])<=exact_provider_instant_ns((datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(seconds=60)).isoformat()),'active_deployment_future_dated')
 require(baseline.canonical(json.loads(read('release/wrangler.publish.json')))==baseline.canonical(exact_assets_config(source_config(),old)),'static_configuration_changed_after_upload')
 return {'state':'EXACT_NEW_VERSION_AND_UNCHANGED_BINDING_VERIFIED','sourceRevision':CURRENT,'previousSourceRevision':PREVIOUS,'accountSHA256':baseline.ACCOUNT_SHA,'hostname':HOST,'worker':WORKER,'currentProviderStateSHA256':digest(current),'deploymentIdSHA256':active['deploymentIdSHA256'],'versionIdSHA256':active['versionIdSHA256'],'providerMethods':['GET'],'providerMutationsPerformed':False,'hostnameAttached':False,'publicHTTPVerified':False}

def extract_upload_version(log,env):
 require(env.get('GITHUB_RUN_ATTEMPT')=='1','first_attempt_required');text=re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',read(log).decode('utf-8','replace'));ids=re.findall(r'(?m)^\s*Current Version ID:\s*('+baseline.UUID+r')\s*$',text);require(len(ids)==1,'single_uploaded_version_id_required');return {'state':'ONE_UPLOAD_SUCCEEDED_VERSION_PARSED','versionIdSHA256':sha(ids[0].encode()),'runId':env['GITHUB_RUN_ID'],'sourceRevision':CURRENT}
