"""Fixed-target GET-only current baseline. Observation is never acceptance or publication."""
import argparse,datetime,hashlib,json,os,re,subprocess,sys
from pathlib import Path
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.parse import urlsplit
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
REPO='joseungil-kr/fwith-site-factory';OWNER='joseungil-kr';HOST='gwangju-gwangsan.fwith.kr';WORKER='gwangju-gwangsan-flower-guide'
PREVIOUS='654dafd7cafa4c6a158684ac4b304ceb7a5996b5';CURRENT='0da9982f8ea294c6fb38729d17e9043d45f7ca72'
ACCOUNT_SHA='d5bbfc5383872f2c9e36138452e0c880f46b03bbd4aaffa278490c2ad6d7bcbf'
TITLE='[GWANGJU-GWANGSAN-POLICY-BASELINE-INSPECT] 20261016'
POLICY_SHA='a7db2c79c77e57628ea04dba761caa969fac41f12600e9c7c72fe7c43ae5fac3'
UUID=r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
def require(ok,code):
 if not ok:raise ValueError(code)
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def digest(v):return sha(canonical(v))
def save(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+'\n')
def read(p):
 p=Path(p);require(p.is_file() and not p.is_symlink(),'regular_file_required');return p.read_bytes()
def timestamp(s):
 # Explicit project RFC3339 subset. Preserve the raw value in state and digests.
 require(type(s) is str,'invalid_provider_timestamp')
 match=re.fullmatch(r'([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]{1,9}))?(Z|[+-][0-9]{2}:[0-9]{2})',s)
 require(match is not None,'invalid_provider_timestamp')
 try:
  year,month,day,hour,minute,second=(int(v) for v in match.group(1,2,3,4,5,6));fraction=match.group(7) or '';zone=match.group(8)
  offset=datetime.timedelta(0)
  if zone!='Z':
   hours=int(zone[1:3]);minutes=int(zone[4:6]);require(hours<=23 and minutes<=59 and zone!='-00:00','invalid_provider_timestamp');offset=datetime.timedelta(hours=hours,minutes=minutes)
   if zone[0]=='-':offset=-offset
  # Provider 7-9 digit fractions floor only for comparisons; never rewrite state.
  microsecond=int(fraction.ljust(6,'0')[:6]);d=datetime.datetime(year,month,day,hour,minute,second,microsecond,tzinfo=datetime.timezone(offset))
  d.astimezone(datetime.timezone.utc) # Reject UTC conversion overflow too.
  return d
 except (ValueError,TypeError,OverflowError):raise ValueError('invalid_provider_timestamp') from None
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*a,**k):return None

def load_policy():
 raw=read(D/'provider-baseline-policy.json');require(sha(raw)==POLICY_SHA,'baseline_policy_bytes_changed');p=json.loads(raw)
 require(p['repository']==REPO and p['hostname']==HOST and p['worker']==WORKER and p['previousSourceRevision']==PREVIOUS and p['correctionSourceRevision']==CURRENT and p['acceptedAccountSHA256']==ACCOUNT_SHA,'fixed_baseline_policy_required')
 require(p['historicalProviderVersionId'] is None and p['historicalProviderDeploymentId'] is None and p['historicalVersionKnown'] is False,'historical_provider_id_invention_forbidden')
 for row in p['evidence']:
  name=row['path'];require(name.startswith('docs/direct-gwangju-gwangsan-policy-correction/prior-publication/') and '..' not in Path(name).parts and '\\' not in name,'unsafe_prior_evidence_path');b=read(ROOT/name);require(len(b)==row['bytes'] and sha(b)==row['sha256'],'prior_evidence_bytes_changed')
 for name,digest_ in p['helpersSHA256'].items():require(name in {'existing_provider.py','assets_only.py'} and sha(read(D/name))==digest_,'pinned_existing_helper_changed')
 require(sha(read(D/'managed_robots.py'))==p['strictManagedRobotsSHA256'],'strict_managed_robots_changed')
 return p

def authorize(env,event):
 require(env.get('GITHUB_REPOSITORY')==REPO and env.get('GITHUB_REF')=='refs/heads/main','owner_main_required')
 require(env.get('GITHUB_ACTOR')==OWNER and env.get('GITHUB_TRIGGERING_ACTOR')==OWNER and env.get('GITHUB_RUN_ATTEMPT')=='1','owner_first_attempt_required')
 require(env.get('GITHUB_EVENT_NAME')=='issues' and event.get('action')=='opened','opened_issue_required')
 revision=env.get('GITHUB_SHA','');require(re.fullmatch('[0-9a-f]{40}',revision),'control_revision_required')
 repo=event.get('repository',{});issue=event.get('issue',{});require(repo.get('full_name')==REPO and repo.get('owner',{}).get('login')==OWNER and repo.get('owner',{}).get('type')=='User','repository_owner_mismatch');require(issue.get('title')==TITLE and issue.get('user',{}).get('login')==OWNER and type(issue.get('number')) is int and issue['number']>0,'exact_issue_required')
 raw=issue.get('body');require(isinstance(raw,str) and len(raw)<2048,'invalid_request_body');body=json.loads(raw)
 expected={'schemaVersion':1,'mode':'read-only-existing-provider-baseline','previous_source_revision':PREVIOUS,'correction_source_revision':CURRENT,'expected_control_revision':revision,'baseline_policy_sha256':POLICY_SHA}
 require(type(body) is dict and canonical(body)==canonical(expected),'exact_baseline_request_required')
 require(re.fullmatch('[1-9][0-9]*',env.get('GITHUB_RUN_ID','')),'actual_run_id_required')
 return {'controlRevision':revision,'runId':env['GITHUB_RUN_ID'],'runAttempt':1,'issue':issue['number'],'repository':REPO,'providerMethods':['GET'],'providerMutationsPerformed':False}

def trusted_control(env):
 head=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD']).decode().strip();require(head==env.get('GITHUB_SHA'),'actual_control_revision_mismatch')
 scopes=['scripts/direct-gwangju-gwangsan-policy-correction','docs/direct-gwangju-gwangsan-policy-correction','.github/workflows/gwangju-gwangsan-policy-baseline-inspect.yml']
 require(not subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain','--untracked-files=all','--',*scopes]).strip(),'baseline_control_checkout_changed')
 for scope in scopes:
  entries=[r for r in subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r','-z','HEAD','--',scope]).split(b'\0') if r];require(entries,'tracked_baseline_scope_missing')
  for row in entries:
   meta,name=row.split(b'\t');mode,kind,blob=meta.decode().split();require(mode=='100644' and kind=='blob','baseline_tracked_entry_invalid');b=read(ROOT/name.decode());require(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==blob,'baseline_control_bytes_changed')
 return head

def allowed_path(account,path,selected=None):
 require(isinstance(path,str) and path and not any(ord(c)<=32 or ord(c)==127 for c in path),'invalid_provider_path');u=urlsplit(path);base='/accounts/'+account;script=base+'/workers/scripts/'+WORKER
 require(path==u.path+('?' +u.query if u.query else ''),'provider_path_normalization_forbidden')
 require(not u.scheme and not u.netloc and not u.fragment and '%' not in path and '\\' not in path,'provider_url_forbidden')
 fixed={base,base+'/workers/scripts',base+'/workers/domains',script+'/settings',script+'/subdomain'}
 if u.path in fixed:return not u.query
 if u.path==script+'/deployments':return u.query=='page=1&per_page=1'
 selected=selected or {}
 if type(selected.get('versions')) is str and re.fullmatch(UUID,selected['versions']) and u.path==base+'/workers/workers/'+WORKER+'/versions/'+selected['versions']:return u.query=='include=modules'
 return not u.query and any(type(selected.get(kind)) is str and re.fullmatch(UUID,selected[kind]) and u.path==script+'/'+kind+'/'+selected[kind] for kind in ('deployments','versions'))

class ProviderEnvelopeError(ValueError):
 def __init__(self,diagnostic):
  super().__init__('provider_response_unverified');self.diagnostic=diagnostic

def envelope_diagnostic(account,path,obj):
 # Only fixed labels, expected-field presence/types and booleans leave this function.
 # Response values, unknown field names, identifiers and provider messages are never retained.
 base='/accounts/'+account;script=base+'/workers/scripts/'+WORKER
 fixed={base:'account',base+'/workers/scripts':'scripts-list',base+'/workers/domains':'domains-list',script+'/settings':'script-settings',script+'/subdomain':'script-exposure',script+'/deployments?page=1&per_page=1':'active-deployment-list'}
 label=fixed.get(path)
 if label is None:
  for kind,name in [('deployments','selected-deployment'),('versions','selected-version')]:
   if re.fullmatch(re.escape(script+'/'+kind+'/')+UUID,path):label=name
 require(label is not None,'diagnostic_endpoint_label_unavailable')
 types={dict:'object',list:'array',str:'string',bool:'boolean',int:'number',float:'number',type(None):'null'}
 is_object=type(obj) is dict;fields={}
 for name in ('success','errors','messages','result','result_info'):
  present=is_object and name in obj;fields[name]={'present':present,'type':types.get(type(obj[name]),'other') if present else 'absent'}
 checks={'object':is_object,'onlyAllowedTopLevelKeys':is_object and set(obj)<={'success','errors','messages','result','result_info'},'successIsTrue':is_object and obj.get('success') is True,'errorsIsEmptyArray':is_object and obj.get('errors')==[],'resultPresent':is_object and 'result' in obj,'messagesAbsentOrArray':is_object and ('messages' not in obj or type(obj['messages']) is list)}
 return {'schema':'gwangsan-provider-envelope-diagnostic/v1','endpoint':label,'responseType':types.get(type(obj),'other'),'expectedFields':fields,'checks':checks}

def domain_null_envelope(account,path,obj):
 # Exact observed domains-list representation only; retain original nulls in memory.
 # This is not an API permission change or a general nullable-error fallback.
 return (path=='/accounts/'+account+'/workers/domains' and type(obj) is dict
  and set(obj)=={'success','errors','messages','result','result_info'}
  and obj['success'] is True and obj['errors'] is None and obj['messages'] is None
  and type(obj['result']) is list and type(obj['result_info']) is dict)

def diagnostic_type(value):
 return {dict:'object',list:'array',str:'string',bool:'boolean',int:'number',float:'number',type(None):'null'}.get(type(value),'other')

def diagnostic_fields(value,names):
 obj=type(value) is dict
 return {name:{'present':obj and name in value,'type':diagnostic_type(value[name]) if obj and name in value else 'absent'} for name in names.split()}

def diagnostic_predicate(fn):
 try:return bool(fn())
 except Exception:return False

def diagnostic_string(value):
 string=type(value) is str
 return {'nonemptyString':string and bool(value),'hex32':string and bool(re.fullmatch('[0-9a-fA-F]{32}',value)),'hex64':string and bool(re.fullmatch('[0-9a-fA-F]{64}',value)),'lowercaseUUID':string and bool(re.fullmatch(UUID,value)),'caseInsensitiveUUID':string and bool(re.fullmatch(UUID,value,re.I)),'asciiGraphic1To128':string and 1<=len(value)<=128 and all(33<=ord(c)<=126 for c in value),'currentOpaquePattern':string and bool(re.fullmatch(r'(?:[0-9a-fA-F]{32}|'+UUID+r')',value))}

def diagnostic_evaluated(report,contexts):
 # Only fixed predicate names produced by trusted projections are considered.
 report['checkEvaluated']={name:bool(contexts.get(name,True)) for name in report['checks']}
 for name,evaluated in report['checkEvaluated'].items():
  if not evaluated:report['checks'].pop(name)
 return report

# Fixed diagnostic vocabulary only. Cross-endpoint names do not establish version
# semantics or relax any normal guard. Sources are pinned in the R11 review binding.
R11_EXPLORATORY_FIELDS='annotations assets bindings body_part cache_options compatibility_date compatibility_flags containers created_on etag exports exports_reconciliation handlers has_assets has_modules id keep_assets keep_bindings last_deployed_from limits logpush main_module migration_tag migrations modified_on named_handlers observability package_dependencies placement placement_mode placement_status routes tag tags tail_consumers usage_model'
R11_VERSION_RUNTIME_FIELDS='compatibility_date compatibility_flags containers exports limits migration_tag usage_model'
R11_METADATA_FIELDS='author_email author_id created_on modified_on source hasPreview'
R11_SETTINGS_EQUALITY_FIELDS='logpush observability placement bindings compatibility_date compatibility_flags usage_model limits cache_options tail_consumers tags'
R11_NESTED_FIELDS={
 'observability':'enabled head_sampling_rate issues logs redact_query_string traces',
 'issues':'enabled','logs':'enabled invocation_logs destinations head_sampling_rate persist',
 'traces':'destinations enabled head_sampling_rate persist propagation_policy',
 'placement':'mode region hostname host target','assets':'config',
 'config':'_headers _redirects base_path html_handling not_found_handling run_worker_first serve_directly',
 'cache_options':'enabled cross_version_cache','limits':'cpu_ms subrequests'}

def diagnostic_r11_status(evaluated,value=False):
 return ('evaluated_true' if value else 'evaluated_false') if evaluated else 'not_evaluated'

def diagnostic_r11_fact(value,kind):
 # No formatting, hashing, item traversal or general serialization of values.
 if kind=='exactFalse':return value is False
 if kind=='exactTrue':return value is True
 if kind=='exactNull':return value is None
 if kind=='exactEmptyArray':return type(value) is list and not value
 if kind=='exactFetchOnly':return type(value) is list and len(value)==1 and type(value[0]) is str and value[0]=='fetch'
 if kind=='exactEmptyObject':return type(value) is dict and not value
 if kind=='exactString':return type(value) is str
 if kind=='exactEmptyString':return type(value) is str and not value
 if kind=='exactNonemptyString':return type(value) is str and bool(value)
 if kind=='exactRoot':return type(value) is str and value=='/'
 if kind=='finiteUnitInterval':return type(value) in (int,float) and 0<=value<=1
 if kind=='finiteNonnegative':return type(value) in (int,float) and 0<=value<float('inf')
 raise ValueError('diagnostic_fixed_predicate_required')

def diagnostic_r11_node(parent,key,names):
 if type(parent) is not dict:return {'state':'parent_wrong_type','fields':{},'predicates':{}},None
 if key not in parent:return {'state':'parent_absent','fields':{},'predicates':{}},None
 value=parent[key]
 if type(value) is not dict:return {'state':'parent_wrong_type','fields':{},'predicates':{}},None
 return {'state':'object','fields':diagnostic_fields(value,names),'predicates':{}},value

def diagnostic_r11_fields_facts(node,value,spec):
 for field,kinds in spec.items():
  present=type(value) is dict and field in value
  node['predicates'][field]={kind:diagnostic_r11_status(present,diagnostic_r11_fact(value[field],kind) if present else False) for kind in kinds.split()}

def diagnostic_r11_nested(parent,key):
 node,value=diagnostic_r11_node(parent,key,R11_NESTED_FIELDS[key]);valid=type(value) is dict
 allowed=set(R11_NESTED_FIELDS[key].split())|({'jwt'} if key=='assets' else set())
 node['predicates']['remainingUnknownObjectKeysPresent']=diagnostic_r11_status(valid,bool(set(value)-allowed) if valid else False)
 node['predicates']['exactEmptyObject']=diagnostic_r11_status(valid,not value if valid else False)
 spec={}
 if key in ('observability','issues','logs','traces','cache_options'):spec['enabled']='exactFalse exactTrue'
 if key in ('observability','logs','traces'):spec['head_sampling_rate']='finiteUnitInterval'
 if key in ('logs','traces'):spec.update(destinations='exactEmptyArray',persist='exactFalse')
 if key=='logs':spec['invocation_logs']='exactFalse'
 if key=='observability':
  node['predicates']['exactDisabledObject']=diagnostic_r11_status(valid,set(value)=={'enabled'} and value['enabled'] is False if valid else False)
  node['children']={name:diagnostic_r11_nested(value,name) for name in ('issues','logs','traces')}
 if key=='assets':
  # Membership only: never retrieve even the type of the credential value.
  node['predicates']['credentialFieldPresent']=diagnostic_r11_status(valid,'jwt' in value if valid else False)
  node['predicates']['configObject']=diagnostic_r11_status(valid and 'config' in value,type(value['config']) is dict if valid and 'config' in value else False)
  node['children']={'config':diagnostic_r11_nested(value,'config')}
 if key=='config':spec.update(run_worker_first='exactFalse exactTrue exactEmptyArray',serve_directly='exactTrue',_headers='exactEmptyString',_redirects='exactEmptyString',base_path='exactRoot')
 diagnostic_r11_fields_facts(node,value,spec)
 return node

def diagnostic_r11_exploratory(parent,key):
 node,value=diagnostic_r11_node(parent,key,R11_EXPLORATORY_FIELDS);valid=type(value) is dict
 additional=R11_METADATA_FIELDS if key=='metadata' else R11_VERSION_RUNTIME_FIELDS
 coverage=set((R11_EXPLORATORY_FIELDS+' '+additional).split())
 name='outsideExploratoryMetadataInventoryKeysPresent' if key=='metadata' else 'outsideExploratoryRuntimeInventoryKeysPresent'
 node['predicates'][name]=diagnostic_r11_status(valid,bool(set(value)-coverage) if valid else False)
 if key=='script_runtime':
  documented=valid and set(value)<=set(R11_VERSION_RUNTIME_FIELDS.split())
  node['predicates']['onlyVersionDocumentedRuntimeKeys']=diagnostic_r11_status(valid,documented)
  node['predicates']['versionSemanticUnverifiedRuntimeKeysPresent']=diagnostic_r11_status(valid,not documented)
 else:
  node['predicates']['onlyDocumentedMetadataKeys']=diagnostic_r11_status(valid,set(value)<=set(R11_METADATA_FIELDS.split()) if valid else False)
 spec={name:'exactFalse exactTrue' for name in ('logpush','keep_assets','has_assets','has_modules')}
 spec.update({name:'exactEmptyArray' for name in ('bindings','keep_bindings','compatibility_flags','containers','tail_consumers','tags','package_dependencies')})
 spec.update({name:'exactEmptyObject' for name in ('exports','exports_reconciliation','migrations','cache_options','limits','placement')})
 spec.update({name:'exactEmptyString exactNonemptyString' for name in ('body_part','main_module')})
 diagnostic_r11_fields_facts(node,value,spec)
 node['nested']={name:diagnostic_r11_nested(value,name) for name in ('observability','placement','assets','cache_options','limits')}
 return node

def diagnostic_r11_version(version):
 # Called only after the existing selected-version identity gate.
 out={'schema':'gwangsan-fixed-version-diagnostic/v1','versionMeaningEstablished':False,'baselineAccepted':False}
 out['outer']={'state':'object','fields':diagnostic_fields(version,'id metadata number resources annotations startup_time_ms'),'predicates':{'onlyDocumentedOuterUnionKeys':diagnostic_r11_status(True,set(version)<={'id','metadata','number','resources','annotations','startup_time_ms'})}}
 diagnostic_r11_fields_facts(out['outer'],version,{'startup_time_ms':'finiteNonnegative'})
 annotations,value=diagnostic_r11_node(version,'annotations','workers/triggered_by workers/message workers/tag');out['annotations']=annotations
 annotations['predicates']['knownPresentAnnotationValuesAreStrings']=diagnostic_r11_status(type(value) is dict,all(type(value[name]) is str for name in ('workers/triggered_by','workers/message','workers/tag') if name in value) if type(value) is dict else False)
 out['metadata']=diagnostic_r11_exploratory(version,'metadata')
 metadata=version.get('metadata');out['metadata']['versionFields']=diagnostic_fields(metadata,R11_METADATA_FIELDS)
 diagnostic_r11_fields_facts(out['metadata'],metadata,{'hasPreview':'exactTrue exactFalse'})
 resources,res=diagnostic_r11_node(version,'resources','bindings script script_runtime');out['resources']=resources
 resources['predicates']['onlyDocumentedResourceKeys']=diagnostic_r11_status(type(res) is dict,set(res)<={'bindings','script','script_runtime'} if type(res) is dict else False)
 diagnostic_r11_fields_facts(resources,res,{'bindings':'exactEmptyArray'})
 script,value=diagnostic_r11_node(res,'script','etag handlers last_deployed_from named_handlers placement_mode');out['script']=script
 script['predicates']['onlyDocumentedScriptUnionKeys']=diagnostic_r11_status(type(value) is dict,set(value)<={'etag','handlers','last_deployed_from','named_handlers','placement_mode'} if type(value) is dict else False)
 diagnostic_r11_fields_facts(script,value,{'etag':'exactString exactEmptyString','last_deployed_from':'exactString exactEmptyString','handlers':'exactNull exactEmptyArray exactFetchOnly','named_handlers':'exactEmptyArray'})
 out['runtime']=diagnostic_r11_exploratory(res,'script_runtime')
 return out

def diagnostic_r11_target(row):
 out={'state':'unique_target_after_inventory_gate','fields':diagnostic_fields(row,'id has_assets has_modules handlers named_handlers exports etag last_deployed_from compatibility_date compatibility_flags usage_model migration_tag placement placement_mode cache_options'),'predicates':{}}
 diagnostic_r11_fields_facts(out,row,{'has_assets':'exactTrue exactFalse','has_modules':'exactTrue exactFalse','handlers':'exactEmptyArray exactFetchOnly','named_handlers':'exactEmptyArray','exports':'exactEmptyObject','etag':'exactEmptyString','migration_tag':'exactEmptyString','placement':'exactEmptyObject'})
 return out

def diagnostic_r11_equality(left,right,kind):
 # Compare only bounded known shapes. Nonempty arrays are deliberately not visited.
 if type(left) is not type(right):return 'evaluated_false'
 if type(left) in (str,bool,int,float,type(None)):
  if type(left) is float and not (-float('inf')<left<float('inf') and -float('inf')<right<float('inf')):return 'not_evaluated'
  return diagnostic_r11_status(True,left==right)
 if type(left) is list:return diagnostic_r11_status(True,True) if not left and not right else 'not_evaluated'
 if type(left) is not dict:return 'not_evaluated'
 if not left and not right:return 'evaluated_true'
 if kind not in R11_NESTED_FIELDS:return 'not_evaluated'
 names=R11_NESTED_FIELDS[kind].split()
 if not set(left)<=set(names) or not set(right)<=set(names):return 'not_evaluated'
 if set(left)!=set(right):return 'evaluated_false'
 results=[diagnostic_r11_equality(left[name],right[name],name) for name in names if name in left]
 if 'not_evaluated' in results:return 'not_evaluated'
 return diagnostic_r11_status(True,all(result=='evaluated_true' for result in results))

def diagnostic_r11_settings_comparison(version,settings,settings_shape):
 # Earlier endpoint in this sweep; neither an atomic snapshot nor normal-response equality.
 checks=settings_shape['checks'];evaluated=settings_shape['checkEvaluated']
 required=('onlyPriorAllowedSettingsKeys','logpushExplicitFalse','observabilityAbsentOrExactDisabled','existingSettingsProjectionExactlyExpected')
 out={'comparisonContext':'earlier_separate_settings_response_in_same_sweep','earlierSettingsOriginalGuardsPassed':all(evaluated.get(key) is True and checks.get(key) is True for key in required),'fields':{}}
 resources=version.get('resources');parents={'metadata':version.get('metadata'),'runtime':resources.get('script_runtime') if type(resources) is dict else None}
 for name,parent in parents.items():
  out['fields'][name]={key:diagnostic_r11_equality(parent[key],settings[key],key) if type(parent) is dict and type(settings) is dict and key in parent and key in settings else 'not_evaluated' for key in R11_SETTINGS_EQUALITY_FIELDS.split()}
 return out


def provider_shape_diagnostic(account,path,obj):
 # The result has only predetermined keys, fixed type labels and booleans.
 # Never retain values, unknown key names, counts, identifiers or identifier digests.
 envelope=envelope_diagnostic(account,path,obj);label=envelope['endpoint'];result=obj.get('result') if type(obj) is dict else None
 out={'endpoint':label,'resultType':diagnostic_type(result),'envelope':envelope,'fields':{},'checks':{}}
 fields=out['fields'];checks=out['checks'];contexts={};mapping=result if type(result) is dict else {};info=obj.get('result_info') if type(obj) is dict else None
 fields['pagination']=diagnostic_fields(info,'page total_pages count total_count per_page')
 checks['paginationStrictlyValid']=diagnostic_predicate(lambda:pagination(obj,single=label!='active-deployment-list') is not None)
 if label=='account':
  fields['result']=diagnostic_fields(result,'id');checks['exactAccountIdentity']=type(result) is dict and result.get('id')==account;contexts['exactAccountIdentity']=type(result) is dict
 elif label=='scripts-list':
  rows=result if type(result) is list else [];names=[r.get('id') if type(r) is dict else None for r in rows]
  checks.update(rowsArray=type(result) is list,rowsNonempty=type(result) is list and bool(result),singlePageComplete=diagnostic_predicate(lambda:single_page(obj) is not None),allRowsNonemptyStringId=all(type(n) is str and bool(n) for n in names),idsUnique=diagnostic_predicate(lambda:len(names)==len(set(names))),fixedWorkerExactlyOnce=names.count(WORKER)==1)
  contexts.update({key:type(result) is list for key in ('allRowsNonemptyStringId','idsUnique','fixedWorkerExactlyOnce')})
 elif label=='domains-list':
  rows=result if type(result) is list else [];checks['rowsArray']=type(result) is list;checks['rowsNonempty']=type(result) is list and bool(result);checks['singlePageComplete']=diagnostic_predicate(lambda:single_page(obj) is not None);checks['inventoryRequiredStrings']=all(type(r) is dict and all(type(r.get(k)) is str and bool(r[k]) for k in ('id','hostname','service','zone_id')) for r in rows)
  matches=[r for r in rows if type(r) is dict and ((type(r.get('hostname')) is str and r['hostname'].lower()==HOST) or r.get('service')==WORKER)];checks['oneRelevantRow']=len(matches)==1;row=matches[0] if len(matches)==1 else {};fields['selectedDomain']=diagnostic_fields(row,'id hostname service zone_id zone_name environment enabled previews_enabled cert_id');fields['domainIdPattern']=diagnostic_string(row.get('id'));fields['zoneIdPattern']=diagnostic_string(row.get('zone_id'));checks['selectedDomainChecksEvaluated']=len(matches)==1
  if len(matches)!=1:
   contexts.update({key:type(result) is list for key in ('inventoryRequiredStrings','oneRelevantRow')});return diagnostic_evaluated(out,contexts)
  checks.update(exactHostWorker=row.get('hostname')==HOST and row.get('service')==WORKER,onlyAllowedDomainKeys=set(row)<={'id','hostname','service','zone_id','zone_name','environment','enabled','previews_enabled','cert_id'},exactZoneName=row.get('zone_name')=='fwith.kr',environmentAllowed=row.get('environment') in (None,'production'),enabledAllowed='enabled' not in row or row['enabled'] is True,previewsAllowed='previews_enabled' not in row or row['previews_enabled'] is False,certificatePatternAllowed='cert_id' not in row or (type(row['cert_id']) is str and bool(re.fullmatch(r'[A-Za-z0-9_-]{1,128}',row['cert_id']))))
  contexts.update({key:type(result) is list for key in ('inventoryRequiredStrings','oneRelevantRow')})
 elif label=='script-settings':
  names='bindings compatibility_date compatibility_flags usage_model limits logpush observability placement tail_consumers tags cache_options annotations migrations exports exports_reconciliation';fields['settings']=diagnostic_fields(result,names);fields['observability']=diagnostic_fields(mapping.get('observability'),'enabled');checks['onlyPriorAllowedSettingsKeys']=type(result) is dict and set(result)<={'bindings','compatibility_date','compatibility_flags','usage_model','limits','logpush','observability','placement','tail_consumers','tags','cache_options','annotations','migrations'}
  for key in ('bindings','compatibility_flags','tail_consumers','tags'):checks[key+'EmptyArray']=type(mapping.get(key)) is list and not mapping[key]
  checks.update(exactCompatibilityDate=mapping.get('compatibility_date')=='2026-10-09',logpushExplicitFalse=mapping.get('logpush') is False,observabilityAbsentOrExactDisabled='observability' not in mapping or canonical(mapping['observability'])==canonical({'enabled':False}),placementEmptyObject=type(mapping.get('placement')) is dict and not mapping['placement'],usageModelStandard=mapping.get('usage_model')=='standard',migrationsAbsentOrEmpty=not mapping.get('migrations'))
  import existing_provider as pc
  checks['existingSettingsProjectionExactlyExpected']=diagnostic_predicate(lambda:canonical(pc.settings(result))==canonical({'bindings':[],'compatibility_date':'2026-10-09','compatibility_flags':[],'logpush':False,'placement':{},'tags':[],'tail_consumers':[],'usage_model':'standard'}))
  contexts.update({key:type(result) is dict for key in checks if key not in ('paginationStrictlyValid','onlyPriorAllowedSettingsKeys','existingSettingsProjectionExactlyExpected')})
 elif label=='script-exposure':
  fields['exposure']=diagnostic_fields(result,'enabled previews_enabled');checks.update(exactExposureKeys=type(result) is dict and set(result)=={'enabled','previews_enabled'},bothFlagsTypedBoolean=type(result) is dict and all(type(result.get(k)) is bool for k in ('enabled','previews_enabled')),workersDevDisabled=mapping.get('enabled') is False,previewsDisabled=mapping.get('previews_enabled') is False)
  contexts.update({key:type(result) is dict for key in ('workersDevDisabled','previewsDisabled')})
 elif label in ('active-deployment-list','selected-deployment'):
  active=result
  if label=='active-deployment-list':
   fields['result']=diagnostic_fields(result,'deployments');rows=mapping.get('deployments');checks['exactlyOneDeployment']=type(rows) is list and len(rows)==1;active=rows[0] if checks['exactlyOneDeployment'] else None;checks['unchangedActiveIdentityPasses']=diagnostic_predicate(lambda:active_identity(obj) is not None)
  row=active if type(active) is dict else {};fields['deployment']=diagnostic_fields(active,'id created_on source strategy versions');fields['deploymentIdPattern']=diagnostic_string(row.get('id'));checks.update(deploymentAllowedKeys=type(active) is dict and set(active)<={'id','created_on','source','strategy','versions','annotations','author_email'},deploymentRequiredKeys=type(active) is dict and {'id','created_on','source','strategy','versions'}<=set(active),deploymentTimestampValid=diagnostic_predicate(lambda:timestamp(row.get('created_on')) is not None),percentageStrategy=row.get('strategy')=='percentage')
  versions=row.get('versions');checks['exactlyOneVersion']=type(versions) is list and len(versions)==1;version=versions[0] if checks['exactlyOneVersion'] and type(versions[0]) is dict else {};fields['selectedVersionEntry']=diagnostic_fields(version,'version_id percentage');fields['selectedVersionIdPattern']=diagnostic_string(version.get('version_id'));checks.update(exactVersionEntryKeys=set(version)=={'version_id','percentage'},typedFullTraffic=type(version.get('percentage')) in (int,float) and version['percentage']==100)
  contexts.update({key:type(active) is dict for key in ('deploymentTimestampValid','percentageStrategy')});contexts.update({key:type(versions) is list and len(versions)==1 and type(versions[0]) is dict for key in ('exactVersionEntryKeys','typedFullTraffic')})
 elif label=='selected-version':
  fields['version']=diagnostic_fields(result,'id metadata number resources annotations startup_time_ms');fields['versionIdPattern']=diagnostic_string(mapping.get('id'));checks.update(onlyPriorVersionKeys=type(result) is dict and set(result)<={'id','metadata','number','resources'},versionNumberPositiveInteger=type(mapping.get('number')) is int and mapping['number']>0,versionIdMatchesRequested=type(result) is dict and mapping.get('id')==path.rsplit('/',1)[-1])
  if not checks['versionIdMatchesRequested']:return diagnostic_evaluated(out,contexts)
  out['expandedVersion']=diagnostic_r11_version(mapping)
  meta=mapping.get('metadata');fields['metadata']=diagnostic_fields(meta,'created_on modified_on source hasPreview');metadata=meta if type(meta) is dict else {};checks.update(onlyPriorMetadataKeys=type(meta) is dict and set(meta)<={'author_email','author_id','created_on','hasPreview','modified_on','source'},versionTimestampValid=diagnostic_predicate(lambda:timestamp(metadata.get('created_on')) is not None),knownVersionSource=type(metadata.get('source')) is str and metadata['source'] in {'unknown','api','wrangler','terraform','dash','cf_cli','dash_template','integration','quick_editor','playground','workersci'})
  resources=mapping.get('resources');res=resources if type(resources) is dict else {};fields['resources']=diagnostic_fields(resources,'bindings script script_runtime');checks.update(onlyPriorResourceKeys=type(resources) is dict and set(resources)<={'bindings','script','script_runtime'},bindingsEmptyArray=type(res.get('bindings')) is list and not res['bindings'])
  script=res.get('script',{});runtime=res.get('script_runtime',{});sm=script if type(script) is dict else {};rt=runtime if type(runtime) is dict else {};fields['script']=diagnostic_fields(script,'etag handlers last_deployed_from named_handlers placement_mode');fields['runtime']=diagnostic_fields(runtime,'compatibility_date compatibility_flags exports limits migration_tag usage_model containers');checks.update(onlyPriorScriptKeys=type(script) is dict and set(script)<={'etag','handlers','last_deployed_from','named_handlers'},onlyPriorRuntimeKeys=type(runtime) is dict and set(runtime)<={'compatibility_date','compatibility_flags','exports','limits','migration_tag','usage_model'},staticHandlersAllowed='handlers' not in sm or (type(sm['handlers']) is list and sm['handlers'] in ([],['fetch'])),namedHandlersAllowed='named_handlers' not in sm or (type(sm['named_handlers']) is list and not sm['named_handlers']))
  for key,empty in [('exports',{}),('limits',{}),('migration_tag','')]:checks[key+'AbsentOrExactEmpty']=key not in rt or canonical(rt[key])==canonical(empty)
  for key,pattern in [('etag',r'[A-Za-z0-9_.:"-]{1,128}'),('last_deployed_from',r'[A-Za-z0-9_.-]{1,64}')]:checks[key+'AbsentOrAllowedPattern']=key not in sm or (type(sm[key]) is str and bool(re.fullmatch(pattern,sm[key])))
  resources_ok=type(resources) is dict;script_ok=resources_ok and ('script' not in resources or type(resources['script']) is dict);runtime_ok=resources_ok and ('script_runtime' not in resources or type(resources['script_runtime']) is dict)
  checks.update(resourcesObject=resources_ok,scriptDefaultUsed=resources_ok and 'script' not in resources,runtimeDefaultUsed=resources_ok and 'script_runtime' not in resources,scriptContextAvailable=script_ok,runtimeContextAvailable=runtime_ok)
  contexts.update({key:type(meta) is dict for key in ('versionTimestampValid','knownVersionSource')});contexts['bindingsEmptyArray']=resources_ok
  contexts.update({key:script_ok for key in ('onlyPriorScriptKeys','staticHandlersAllowed','namedHandlersAllowed','etagAbsentOrAllowedPattern','last_deployed_fromAbsentOrAllowedPattern')})
  contexts.update({key:runtime_ok for key in ('onlyPriorRuntimeKeys','exportsAbsentOrExactEmpty','limitsAbsentOrExactEmpty','migration_tagAbsentOrExactEmpty')})
 return diagnostic_evaluated(out,contexts)


def provider_get(env,opener=None,diagnostic=False):
 require(type(diagnostic) is bool,'diagnostic_mode_type_required')
 account=env.get('CLOUDFLARE_ACCOUNT_ID','');token=env.get('CLOUDFLARE_API_TOKEN','')
 require(re.fullmatch('[0-9a-fA-F]{32}',account) and sha(account.encode())==ACCOUNT_SHA,'accepted_account_configuration_required')
 require(isinstance(token,str) and token and token==token.strip() and not any(c in token for c in '\r\n'),'existing_provider_configuration_required')
 opener=opener or build_opener(NoRedirect());selected={};active_path='/accounts/'+account+'/workers/scripts/'+WORKER+'/deployments?page=1&per_page=1'
 def get(path):
  if diagnostic:get.shape_snapshot=None;get.diagnostic_transport_passed=False
  require(allowed_path(account,path,selected),'provider_get_endpoint_forbidden')
  req=Request('https://api.cloudflare.com/client/v4'+path,method='GET',headers={'Authorization':'Bearer '+token,'Accept':'application/json'})
  try:
   with opener.open(req,timeout=30) as response:
    require(response.status==200,'provider_get_http_status')
    types=response.headers.get_all('Content-Type',[]);require(len(types)==1 and types[0].split(';',1)[0].strip().lower()=='application/json','provider_json_media_type_required')
    require(response.headers.get('Content-Encoding','identity').lower()=='identity','provider_content_encoding_unsupported');raw=response.read(1024*1024+1)
  except ValueError:raise
  except Exception:raise ValueError('provider_get_failed_no_response_disclosed') from None
  require(len(raw)<=1024*1024,'provider_response_limit')
  try:
   def unique(pairs):
    out={}
    for k,v in pairs:
     require(k not in out,'provider_duplicate_json_key');out[k]=v
    return out
   obj=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda value:require(False,'provider_nonfinite_json'))
  except ValueError:raise ValueError('provider_json_invalid') from None
  except Exception:raise ValueError('provider_json_invalid') from None
  nullable_domain=domain_null_envelope(account,path,obj)
  try:
   require((type(obj) is dict and set(obj)<={'success','errors','messages','result','result_info'} and obj.get('success') is True and obj.get('errors')==[] and 'result' in obj and ('messages' not in obj or type(obj['messages']) is list)) or nullable_domain,'provider_response_unverified')
  except ValueError:raise ProviderEnvelopeError(envelope_diagnostic(account,path,obj)) from None
  if nullable_domain:get.envelope_compatibility['domainsListNullPairObserved']=True
  if diagnostic:
   try:get.shape_snapshot=json.loads(canonical(provider_shape_diagnostic(account,path,obj)))
   except Exception:raise ValueError('diagnostic_projection_failed') from None
   get.diagnostic_transport_passed=True
  if path==active_path:
   active=active_identity(obj);new={'deployments':active['id'],'versions':active['versions'][0]['version_id']}
   require(not selected or selected==new,'active_identity_changed_during_transport');selected.update(new)
  return obj
 get.envelope_compatibility={'domainsListNullPairObserved':False}
 if diagnostic:get.shape_snapshot=None;get.diagnostic_transport_passed=False
 return account,get

def pagination(obj,single=True):
 require(type(obj) is dict and set(obj)<={'success','errors','messages','result','result_info'},'provider_envelope_schema')
 if 'result_info' not in obj:return {}
 info=obj['result_info'];keys={'page','total_pages','count','total_count','per_page'}
 require(type(info) is dict and set(info)<=keys and all(type(v) is int and v>=0 for v in info.values()),'provider_pagination_schema')
 require(info.get('page',1)==1,'provider_page_identity')
 if single:require(info.get('total_pages',1)<=1,'provider_list_completeness_unverified')
 return info

def single_page(obj):
 rows=obj.get('result');require(type(rows) is list,'provider_list_schema');info=pagination(obj)
 require(info.get('total_pages',1) in ({0,1} if not rows else {1}) and info.get('count',len(rows))==len(rows) and info.get('total_count',len(rows))==len(rows) and info.get('per_page',len(rows))>=len(rows),'provider_list_completeness_unverified')
 return rows

def active_identity(obj):
 value=obj.get('result');require(type(value) is dict and set(value)=={'deployments'},'deployment_list_schema');rows=value['deployments'];require(type(rows) is list and len(rows)==1,'active_deployment_ambiguous_or_missing');active=rows[0]
 allowed={'id','created_on','source','strategy','versions','annotations','author_email'};require(type(active) is dict and set(active)<=allowed and {'id','created_on','source','strategy','versions'}<=set(active),'active_deployment_schema')
 require(type(active['id']) is str and re.fullmatch(UUID,active['id']) and active['strategy']=='percentage','active_deployment_identity');timestamp(active['created_on'])
 versions=active['versions'];require(type(versions) is list and len(versions)==1 and type(versions[0]) is dict and set(versions[0])=={'version_id','percentage'} and type(versions[0]['percentage']) in (int,float) and versions[0]['percentage']==100 and type(versions[0]['version_id']) is str and re.fullmatch(UUID,versions[0]['version_id']),'single_full_traffic_version_required')
 info=pagination(obj,single=False);require(info.get('count',1)==1 and info.get('per_page',1)==1 and info.get('total_count',1)>=1 and info.get('total_pages',1)>=1,'deployment_page_identity')
 return active

def selected_assets_preservation(get,account,vid,number,created_on):
 # The beta Version API names the same immutable selected version. include=modules
 # returns all modules; only the two fixed asset-config names are consumed here.
 # No legacy runtime.assets internals, JWT values, other module content or code
 # absence are inspected or asserted. No fallback, retry or extra diagnostic GET.
 path='/accounts/'+account+'/workers/workers/'+WORKER+'/versions/'+vid+'?include=modules'
 try:obj=get(path)
 except Exception:raise ValueError('selected_assets_transport_unverified') from None
 v=obj.get('result') if type(obj) is dict else None
 require(type(v) is dict and type(v.get('id')) is str and v['id']==vid,'selected_assets_version_identity')
 require(type(v.get('number')) is int and v['number']>0 and v['number']==number,'selected_assets_version_number')
 try:timestamp(v.get('created_on'));timestamp(created_on)
 except ValueError:raise ValueError('selected_assets_version_time') from None
 require(v['created_on']==created_on,'selected_assets_version_time')
 assets=v.get('assets');require(type(assets) is dict and set(assets)<={'config','jwt'},'selected_assets_schema')
 # 'jwt' is allowed by membership only. Never retrieve its value, even its type.
 config=assets.get('config');require(type(config) is dict and set(config)<={'base_path','html_handling','not_found_handling','run_worker_first'},'selected_assets_config_schema')
 fields={}
 for key,expected in [('html_handling','auto-trailing-slash'),('not_found_handling','404-page')]:
  require(type(config.get(key)) is str and config[key]==expected,'selected_assets_'+key);fields[key]=expected
 if 'base_path' in config:
  require(type(config['base_path']) is str and config['base_path']=='/','selected_assets_base_path');fields['base_path']='/'
 if 'run_worker_first' in config:
  require(config['run_worker_first'] is False,'selected_assets_run_worker_first');fields['run_worker_first']=False
 # Absence is retained as absence; do not coerce absent/null/[] to '/' or false.
 modules=v.get('modules');require(type(modules) is list,'selected_assets_modules_inventory_required')
 headers='absent_source_noop_equivalent'
 for module in modules:
  require(type(module) is dict and type(module.get('name')) is str and bool(module['name']),'selected_assets_module_name_required')
  name=module['name']
  require(name!='_redirects','selected_assets_redirects_present')
  if name=='_headers':
   require(headers=='absent_source_noop_equivalent','selected_assets_duplicate_headers')
   require(set(module)=={'name','content_type','content_base64'} and type(module['content_type']) is str and module['content_type']=='text/plain' and type(module['content_base64']) is str and module['content_base64']=='LyoK','selected_assets_headers_bytes')
   headers='present_exact_source_bytes'
 # Only constants and presence of approved values leave the projection. Unknown
 # top-level beta fields and non-config modules are intentionally unconsumed.
 projection={'schema':'gwangsan-selected-version-assets-preservation/v1','configFields':fields,'headers':headers,'redirects':'absent','modulesInventoryProvided':True,'legacyRuntimeAssetsInternalsInspected':False,'otherModuleContentInspected':False,'workerCodeAbsenceProven':False}
 return projection,v['created_on']

def deployed_version(get,account,settings=None):
 script='/accounts/'+account+'/workers/scripts/'+WORKER
 obj=get(script+'/deployments?page=1&per_page=1');active=active_identity(obj);value=obj['result'];versions=active['versions']
 detail=get(script+'/deployments/'+active['id']).get('result');require(detail==active,'active_deployment_detail_changed')
 vid=versions[0]['version_id'];v=get(script+'/versions/'+vid).get('result');require(type(v) is dict and set(v)<={'id','metadata','number','resources','annotations','startup_time_ms'} and v.get('id')==vid,'version_identity_or_schema')
 meta=v.get('metadata');require(type(meta) is dict and isinstance(meta.get('source'),str),'version_metadata_schema');require(meta['source'] in {'unknown','api','wrangler','terraform','dash','cf_cli','dash_template','integration','quick_editor','playground','workersci'},'unreviewed_version_source');timestamp(meta.get('created_on'));require(type(v.get('number')) is int and v['number']>0,'version_number_required')
 # Metadata extras and unknown annotation values are outside this policy's consumed
 # fields. They are not declared harmless, validated, retained or hashed.
 if 'annotations' in v:
  annotations=v['annotations'];require(type(annotations) is dict and all(type(annotations[key]) is str for key in ('workers/message','workers/tag','workers/triggered_by') if key in annotations),'version_annotations_type_required')
 if 'startup_time_ms' in v:require(type(v['startup_time_ms']) in (int,float) and 0<=v['startup_time_ms']<float('inf'),'version_startup_metric_required')
 resources=v.get('resources');require(type(resources) is dict and set(resources)<={'bindings','script','script_runtime'} and resources.get('bindings')==[],'version_resource_schema_requires_review')
 # Do not expose script body, binding values, author identity or annotations. Version ID is not an asset digest or Git-source proof.
 scriptmeta=resources.get('script',{});runtime=resources.get('script_runtime',{});require(type(scriptmeta) is dict and set(scriptmeta)<={'etag','handlers','last_deployed_from','named_handlers'},'version_script_schema_requires_review');require(type(runtime) is dict and set(runtime)<={'compatibility_date','compatibility_flags','exports','limits','migration_tag','usage_model','assets'},'version_runtime_schema_requires_review')
 require(not scriptmeta.get('named_handlers') and not runtime.get('exports') and not runtime.get('migration_tag') and not runtime.get('limits'),'unexpected_version_capability')
 selected={'deploymentIdSHA256':sha(active['id'].encode()),'deploymentCreatedOn':active['created_on'],'strategy':'percentage','versionIdSHA256':sha(vid.encode()),'trafficPercentage':100,'versionNumber':v['number'],'versionCreatedOn':meta['created_on'],'versionSource':meta['source'],'versionResourceCoverage':{'resourceContainerAndBindingsChecked':True,'knownRuntimeCapabilityGuardsChecked':True,'legacyAssetsInternalsInspected':False,'selectedAssetsConfigCompared':'assets' in runtime,'workerCodeInspected':False},'versionIdentityIsAssetDigest':False}
 runtime_projection={'present': 'script_runtime' in resources,'fields':{}}
 for key in ('compatibility_date','compatibility_flags','usage_model'):
  if key in runtime:
   require(settings is not None and key in settings and canonical(runtime[key])==canonical(settings[key]),'active_version_runtime_settings_disagree')
   runtime_projection['fields'][key]=runtime[key]
 for key,empty in [('exports',{}),('limits',{}),('migration_tag','')]:
  if key in runtime:require(canonical(runtime[key])==canonical(empty),'unexpected_version_capability');runtime_projection['fields'][key]=runtime[key]
 script_projection={'present':'script' in resources,'fields':{}}
 if 'handlers' in scriptmeta:
  handlers=scriptmeta['handlers'];require(handlers is None or (type(handlers) is list and all(type(v) is str for v in handlers) and handlers in ([],['fetch'])),'static_only_version_handlers_required');script_projection['fields']['handlers']=handlers
 if 'named_handlers' in scriptmeta:
  require(type(scriptmeta['named_handlers']) is list and not scriptmeta['named_handlers'],'static_only_named_handlers_required');script_projection['fields']['named_handlers']=[]
 for key in ('etag','last_deployed_from'):
  if key in scriptmeta:require(type(scriptmeta[key]) is str,'version_script_metadata_type_required')
  script_projection['fields'][key+'Present']=key in scriptmeta
 if 'assets' in runtime:
  require(type(runtime['assets']) is dict,'version_assets_object_required')
  preservation,beta_created=selected_assets_preservation(get,account,vid,v['number'],meta['created_on'])
  runtime_projection['fields']['assetsPreservation']=preservation
  selected['assetsVersionCreatedOn']=beta_created # Raw timestamp remains digest-bound.
 selected['versionScript']=script_projection
 selected['versionRuntime']=runtime_projection
 repeat=get(script+'/deployments?page=1&per_page=1');active_identity(repeat);require(repeat==obj,'active_deployment_changed_during_observation')
 return selected

def current_state(account,get):
 require(sha(account.encode())==ACCOUNT_SHA,'historical_account_digest_mismatch');base='/accounts/'+account;script=base+'/workers/scripts/'+WORKER
 acct=get(base).get('result');require(type(acct) is dict and acct.get('id')==account,'account_identity_mismatch')
 scripts=single_page(get(base+'/workers/scripts'));names=[r.get('id') if isinstance(r,dict) else None for r in scripts];require(all(isinstance(n,str) and n for n in names) and len(names)==len(set(names)) and names.count(WORKER)==1,'existing_worker_missing_or_ambiguous')
 domains=single_page(get(base+'/workers/domains'));require(all(type(r) is dict and all(isinstance(r.get(k),str) and r[k] for k in ['id','hostname','service','zone_id']) for r in domains),'domain_inventory_schema');matches=[r for r in domains if r['hostname'].lower()==HOST or r['service']==WORKER];require(len(matches)==1 and matches[0]['hostname']==HOST and matches[0]['service']==WORKER,'exact_existing_binding_required');row=matches[0]
 require(set(row)<={'id','hostname','service','zone_id','zone_name','environment','enabled','previews_enabled','cert_id'} and row.get('zone_name')=='fwith.kr' and row.get('environment') in (None,'production') and ('enabled' not in row or row['enabled'] is True) and ('previews_enabled' not in row or row['previews_enabled'] is False),'binding_configuration_requires_review')
 require(type(row['id']) is str and 1<=len(row['id'])<=128 and all(33<=ord(c)<=126 for c in row['id']) and bool(re.fullmatch(r'(?:[0-9a-fA-F]{32}|'+UUID+r')',row['zone_id'])),'opaque_domain_zone_identity_required')
 require('cert_id' not in row or (type(row['cert_id']) is str and bool(re.fullmatch(r'[A-Za-z0-9_-]{1,128}',row['cert_id']))),'invalid_optional_certificate_identity')
 import existing_provider as pc
 raw_settings=get(script+'/settings').get('result');require(type(raw_settings) is dict and type(raw_settings.get('logpush')) is bool,'explicit_typed_logpush_required')
 require('observability' not in raw_settings or canonical(raw_settings['observability'])==canonical({'enabled':False}),'typed_disabled_observability_required')
 settings=pc.settings(raw_settings);require(canonical(settings)==canonical({'bindings':[],'compatibility_date':'2026-10-09','compatibility_flags':[],'logpush':False,'placement':{},'tags':[],'tail_consumers':[],'usage_model':'standard'}),'nondefault_provider_settings_require_review');sub=get(script+'/subdomain').get('result');require(type(sub) is dict and set(sub)=={'enabled','previews_enabled'} and all(type(v) is bool for v in sub.values()),'explicit_exposure_flags_required')
 require(sub['enabled'] is False,'historical_workers_dev_exposure_changed')
 # Keep opaque provider identifiers only as digests; no account ID, token, email, raw response or annotation is serialized.
 binding={'domainIdSHA256':sha(row['id'].encode()),'zoneIdSHA256':sha(row['zone_id'].encode()),'hostname':HOST,'worker':WORKER,'zoneName':'fwith.kr','optionalObservedFields':{k:row[k] for k in ('environment','enabled','previews_enabled') if k in row}}
 active=deployed_version(get,account,settings)
 return {'accountSHA256':ACCOUNT_SHA,'hostname':HOST,'worker':WORKER,'settings':settings,'workersDev':sub,'hostnameBinding':binding,'activeDeployment':active,'legacyRoutes':'not_read_not_modified'}

def old_public(p):
 import previous_public as prior
 contract=json.loads(read(ROOT/p['previousPublicContractPath']));require(contract['revision']==PREVIOUS and len(contract['files'])==18,'prior_public_inventory_mismatch');report=prior.http_once(contract);require(report['checkedPaths']==17 and report['unknownHttpStatus']==404,'complete_prior_public_http_required');return report

class ProviderStateDiagnosticError(ValueError):
 def __init__(self,code,diagnostic):
  super().__init__(code);self.original_code=code;self.diagnostic=diagnostic

STATE_DIAGNOSTIC_CODES=frozenset({
 'historical_account_digest_mismatch','account_identity_mismatch','existing_worker_missing_or_ambiguous','domain_inventory_schema','exact_existing_binding_required','binding_configuration_requires_review','opaque_domain_zone_identity_required','invalid_optional_certificate_identity','explicit_typed_logpush_required','typed_disabled_observability_required','nondefault_provider_settings_require_review','explicit_exposure_flags_required','historical_workers_dev_exposure_changed','provider_envelope_schema','provider_pagination_schema','provider_page_identity','provider_list_completeness_unverified','provider_list_schema','deployment_list_schema','active_deployment_ambiguous_or_missing','active_deployment_schema','active_deployment_identity','single_full_traffic_version_required','deployment_page_identity','invalid_provider_timestamp','provider_timestamp_timezone_required','active_deployment_detail_changed','version_identity_or_schema','version_metadata_schema','unreviewed_version_source','version_number_required','version_resource_schema_requires_review','version_script_schema_requires_review','version_runtime_schema_requires_review','unexpected_version_capability','active_version_runtime_settings_disagree','static_only_version_handlers_required','static_only_named_handlers_required','version_script_metadata_type_required','active_deployment_changed_during_observation','active_identity_changed_during_transport',
 'Missing Worker settings','Unexpected runtime bindings: stop without exposing values','Unexpected runtime resource capability','Unreviewed provider settings shape','Missing compatibility date'})

def state_diagnostic_sweep(env,opener=None):
 # Bounded fresh GET-only diagnostic transport. This function never accepts a state.
 labels=('account','scripts-list','domains-list','script-settings','script-exposure','active-deployment-list','selected-deployment','selected-version')
 report={'schema':'gwangsan-safe-state-shape-diagnostic/v1','state':'DIAGNOSTIC_ONLY_NOT_A_BASELINE','endpoints':{label:{'status':'not_requested'} for label in labels},'checks':{},'baselineAccepted':False,'publicationEligible':False,'providerMutationsPerformed':False};evaluation={}
 try:account,get=provider_get(env,opener=opener,diagnostic=True)
 except Exception:report['state']='configuration_gate_failed';return diagnostic_evaluated(report,evaluation)
 base='/accounts/'+account;script=base+'/workers/scripts/'+WORKER
 class StopSweep(Exception):pass
 def request(label,path):
  try:obj=get(path)
  except Exception as exc:
   row={'status':'request_failed_stop'}
   if type(exc) is ProviderEnvelopeError:row={'status':'envelope_rejected_stop','envelope':exc.diagnostic}
   elif get.diagnostic_transport_passed and get.shape_snapshot is not None:row={'status':'selection_rejected_stop','shape':get.shape_snapshot}
   report['endpoints'][label]=row;report['state']='request_or_selection_gate_failed';raise StopSweep() from None
  report['endpoints'][label]={'status':'observed_shape_only','shape':get.shape_snapshot};return obj
 try:
  acct=request('account',base).get('result');account_ok=type(acct) is dict and acct.get('id')==account;report['checks']['accountIdentityGate']=account_ok
  if not account_ok:report['state']='account_identity_gate_failed';return diagnostic_evaluated(report,evaluation)
  scripts_obj=request('scripts-list',base+'/workers/scripts')
  try:
   scripts=single_page(scripts_obj);names=[r.get('id') if isinstance(r,dict) else None for r in scripts];worker_ok=all(isinstance(n,str) and n for n in names) and len(names)==len(set(names)) and names.count(WORKER)==1
  except Exception:worker_ok=False
  report['checks']['fixedWorkerInventoryGate']=bool(worker_ok)
  if not worker_ok:report['state']='worker_inventory_gate_failed';return diagnostic_evaluated(report,evaluation)
  report['endpoints']['scripts-list']['shape']['selectedTarget']=diagnostic_r11_target(next(row for row in scripts if row['id']==WORKER))
  domains_obj=request('domains-list',base+'/workers/domains')
  try:
   domains=single_page(domains_obj);schema_ok=all(type(r) is dict and all(isinstance(r.get(k),str) and r[k] for k in ['id','hostname','service','zone_id']) for r in domains);matches=[r for r in domains if r['hostname'].lower()==HOST or r['service']==WORKER] if schema_ok else [];bound=len(matches)==1 and matches[0]['hostname']==HOST and matches[0]['service']==WORKER;row=matches[0] if bound else {};prefix_ok=bound and set(row)<={'id','hostname','service','zone_id','zone_name','environment','enabled','previews_enabled','cert_id'} and row.get('zone_name')=='fwith.kr' and row.get('environment') in (None,'production') and ('enabled' not in row or row['enabled'] is True) and ('previews_enabled' not in row or row['previews_enabled'] is False)
  except Exception:prefix_ok=False
  report['checks']['exactHostWorkerZonePrefixGate']=bool(prefix_ok)
  if not prefix_ok:report['state']='existing_binding_prefix_gate_failed';return diagnostic_evaluated(report,evaluation)
  settings_obj=request('script-settings',script+'/settings');raw_settings=settings_obj.get('result')
  request('script-exposure',script+'/subdomain')
  active_obj=request('active-deployment-list',script+'/deployments?page=1&per_page=1')
  # provider_get already applied this exact validator before assigning selected IDs.
  active=active_identity(active_obj);vid=active['versions'][0]['version_id']
  detail=request('selected-deployment',script+'/deployments/'+active['id']).get('result');report['checks']['selectedDetailMatchesActive']=detail==active
  if detail!=active:report['endpoints']['selected-deployment']['status']='identity_mismatch_stop';report['state']='selected_deployment_identity_gate_failed';return diagnostic_evaluated(report,evaluation)
  version=request('selected-version',script+'/versions/'+vid).get('result');report['checks']['selectedVersionIdMatchesActive']=type(version) is dict and version.get('id')==vid
  if not report['checks']['selectedVersionIdMatchesActive']:report['endpoints']['selected-version']['status']='identity_mismatch_stop';report['state']='selected_version_identity_gate_failed';return diagnostic_evaluated(report,evaluation)
  resources=version.get('resources') if type(version) is dict else None;runtime=resources.get('script_runtime',{}) if type(resources) is dict else None
  runtime_context=type(resources) is dict and ('script_runtime' not in resources or type(resources['script_runtime']) is dict)
  for key in ('compatibility_date','compatibility_flags','usage_model'):
   name='runtime_'+key+'_AbsentOrMatchesSettings';evaluation[name]=runtime_context and (key not in runtime or type(raw_settings) is dict);report['checks'][name]=runtime_context and (key not in runtime or (type(raw_settings) is dict and key in raw_settings and canonical(runtime[key])==canonical(raw_settings[key])))
  report['earlierSettingsComparison']=diagnostic_r11_settings_comparison(version,raw_settings,report['endpoints']['script-settings']['shape'])
  report['state']='BOUNDED_DIAGNOSTIC_SWEEP_FINISHED_NOT_A_BASELINE'
 except StopSweep:pass
 except Exception:report['state']='diagnostic_local_check_failed'
 return diagnostic_evaluated(report,evaluation)

def state_with_diagnostics(env,account,get):
 try:return current_state(account,get)
 except ValueError as exc:
  # Exact local validation codes only. Never retry a transport/envelope/access failure.
  if type(exc) is not ValueError or str(exc) not in STATE_DIAGNOSTIC_CODES:raise
  try:diagnostic=state_diagnostic_sweep(env)
  except Exception:diagnostic={'schema':'gwangsan-safe-state-shape-diagnostic/v1','state':'diagnostic_unexpected_failure','baselineAccepted':False,'publicationEligible':False,'providerMutationsPerformed':False}
  code=str(exc) if re.fullmatch('[a-z0-9_]+',str(exc)) else 'ValueError'
  raise ProviderStateDiagnosticError(code,diagnostic) from None


def observe(env,event):
 p=load_policy();identity=authorize(env,event);trusted_control(env);account,get=provider_get(env);first=state_with_diagnostics(env,account,get);public=old_public(p);second=state_with_diagnostics(env,account,get);require(first==second,'provider_changed_across_full_public_check')
 result={'schema':'gwangsan-current-provider-baseline-observation/v1','state':'OBSERVED_NOT_ACCEPTED_FOR_MUTATION','observedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'identity':identity,'policySHA256':POLICY_SHA,'previousSourceRevision':PREVIOUS,'correctionSourceRevision':CURRENT,'previousPublicationRunId':38843104514,'historicalProviderVersionKnown':False,'currentProviderState':first,'currentProviderStateSHA256':digest(first),'previousPublicHTTP':public,'providerMethods':['GET'],'providerMutationsPerformed':False,'IndexNowSubmitted':False,'baselineAccepted':False,'publicationEligible':False,'providerEnvelopeCompatibility':dict(get.envelope_compatibility)}
 save('previous-public-http.json',public);return result

def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['authorize','observe']);p.add_argument('--report',required=True);a=p.parse_args()
 try:
  load_policy();event=json.loads(read(os.environ['GITHUB_EVENT_PATH']));result=authorize(os.environ,event) if a.mode=='authorize' else observe(os.environ,event);save(a.report,result);print(json.dumps({'state':result.get('state','READ_ONLY_REQUEST_SELECTED'),'providerMutationsPerformed':False}));return 0
 except Exception as e:
  code=str(e) if type(e) in (ValueError,ProviderEnvelopeError) and re.fullmatch('[a-z0-9_]+',str(e)) else type(e).__name__;report={'state':'BLOCKED_WITH_NO_PROVIDER_MUTATION','code':code,'providerMutationsPerformed':False,'baselineAccepted':False}
  if type(e) is ProviderStateDiagnosticError:report['code']=e.original_code;code=e.original_code;report['stateDiagnostics']=e.diagnostic
  if type(e) is ProviderEnvelopeError:report['diagnostic']=e.diagnostic
  save(a.report,report);print('Read-only baseline blocked: '+code);return 1
if __name__=='__main__':sys.exit(main())
