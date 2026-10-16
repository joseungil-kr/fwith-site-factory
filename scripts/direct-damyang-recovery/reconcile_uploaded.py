#!/usr/bin/env python3
"""GET-only reconciliation of the one retained Damyang upload38927541164.

Current execution identity is always the current workflow run. The historical
failed upload, claim and after projection are separate immutable input evidence.
This caller cannot POST, claim, deploy, attach, execute site code or IndexNow.
"""
from pathlib import Path
import argparse, collections, datetime, hashlib, json, os, re, sys
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
CALLER_SHA256='930d306c99fbd6be3fd453d33cb78b36af0afebaee814998325783a2a7627e4f'
if hashlib.sha256((D/'publish_existing_update.py').read_bytes()).hexdigest()!=CALLER_SHA256:
    raise ValueError('immutable_existing_update_caller_required')
import publish_existing_update as c
require=c.require;sha=c.sha;exact=c.exact;read_json=c.read_json
OPERATIONAL_CONTROLS_ENABLED=True
TITLE='[DAMYANG-UPLOADED-GET-RECONCILE] 20261017'
MODES=('prepare','artifact','observe')
PENDING_UPDATE_SHA256='1774b87aefcc9ffb3636220408e8d465ad42e26e95c891cc6495f3cd211d914a'
ACTUAL_FAILURE_REVIEW={'path':'docs/direct-damyang-recovery/uploaded-failure-review-38927541164.json',
 'sha256':'ddce842b61509c8a0a4951c4dba060d59bd64e555215711380b2b65c179b2d09'}
ENV_KEYS=c.ENV_KEYS
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()


def approved_pins(path):
    require(OPERATIONAL_CONTROLS_ENABLED is True,'reconciliation_code_seal_missing')
    pins=read_json(path)
    require(type(pins)is dict and pins.get('status')=='INDEPENDENTLY_REVIEWED_GET_ONLY_UPLOADED_RECONCILIATION'
        and pins.get('operationalActivationAllowed')is True and pins.get('providerBaselineAccepted')is True,
        'independent_get_only_reconciliation_acceptance_required')
    require(all(type(pins.get(k))is dict and pins[k] for k in ('review','controlFiles','workflowFiles'))
        and c.journal._valid_sha(pins.get('reviewedControlRevision'),40),'complete_reconciliation_control_binding_required')
    return pins


def authorize(pins,env,event,mode):
    require(sys.flags.optimize==0 and mode in MODES,'fixed_unoptimized_get_only_mode_required')
    allowed=ENV_KEYS | (c.PROVIDER_KEYS if mode=='observe' else set())
    require(set(env)<=allowed,'clean_reconciliation_environment_required')
    if mode=='observe':require(all(type(env.get(k))is str and env[k] for k in c.PROVIDER_KEYS),'provider_get_credentials_required')
    else:require(not any(k.startswith(('CLOUDFLARE_','CF_','WRANGLER_'))for k in env),'provider_environment_forbidden')
    require(env.get('GITHUB_REPOSITORY')==c.journal.REPOSITORY and env.get('GITHUB_REF')=='refs/heads/main'
        and env.get('GITHUB_ACTOR')==c.reader.OWNER and env.get('GITHUB_TRIGGERING_ACTOR')==c.reader.OWNER
        and env.get('GITHUB_RUN_ATTEMPT')=='1' and env.get('GITHUB_EVENT_NAME')=='issues'
        and env.get('GITHUB_JOB')==c.JOB and env.get('RUNNER_ENVIRONMENT')=='github-hosted'
        and c.journal._valid_sha(env.get('GITHUB_SHA'),40)
        and re.fullmatch('[1-9][0-9]*',env.get('GITHUB_RUN_ID',''))
        and env['GITHUB_RUN_ID']!=str(c.reader.EXACT_FAILED_UPDATE['runId']),
        'separate_current_owner_main_first_hosted_identity_required')
    repo=event.get('repository',{});issue=event.get('issue',{})
    require(event.get('action')=='opened' and repo.get('full_name')==c.journal.REPOSITORY
        and repo.get('owner',{}).get('login')==c.reader.OWNER and repo.get('owner',{}).get('type')=='User'
        and event.get('sender',{}).get('login')==c.reader.OWNER and event.get('sender',{}).get('type')=='User',
        'exact_reconciliation_event_required')
    require(issue.get('title')==TITLE and issue.get('user',{}).get('login')==c.reader.OWNER
        and issue.get('user',{}).get('type')=='User' and issue.get('state')=='open'
        and c.reader.positive(issue.get('number')) and issue['number']!=377 and 'pull_request'not in issue,
        'exact_get_only_reconciliation_issue_required')
    raw=issue.get('body');require(type(raw)is str and len(raw.encode())<=4096,'bounded_reconciliation_body_required')
    expected={'schemaVersion':1,'mode':'uploaded-proof-get-only-reconciliation',
        'source_branch':c.reader.SOURCE_BRANCH,'source_revision':c.SOURCE,
        'expected_control_revision':env['GITHUB_SHA'],'receipt_issue':377,
        'original_update_run_id':38927541164,'original_update_artifact_id':12056828086,
        'original_claim_comment_id':6219311010,'reconciliation_binding_sha256':c.journal.digest(pins)}
    require(exact(c.reader.json_raw(raw),expected),'closed_exact_reconciliation_request_required')
    require(pins.get('schemaVersion')==1 and pins.get('sourceRevision')==c.SOURCE
        and pins.get('sourceBranch')==c.reader.SOURCE_BRANCH and pins.get('sourceTree')==c.reader.SOURCE_TREE
        and exact(pins.get('build'),c.reader.ACTUAL_BUILD)
        and exact(pins.get('acceptedBuildReview'),c.reader.ACCEPTED_BUILD_REVIEW)
        and exact(pins.get('failedUpdate'),c.reader.EXACT_FAILED_UPDATE)
        and exact(pins.get('actualFailureReview'),ACTUAL_FAILURE_REVIEW),
        'fixed_build_source_historical_upload_review_required')
    return expected


def verify_controls(root,pins):
    c.verify_controls(root,pins)
    files=pins['controlFiles']
    required={'scripts/direct-damyang-recovery/reconcile_uploaded.py',
        'scripts/direct-damyang-recovery/test_reconcile_uploaded.py',ACTUAL_FAILURE_REVIEW['path']}
    require(required<=set(files),'complete_get_only_reconciliation_inventory_required')
    require(sha(c.public_release.read_file(Path(root)/'docs/direct-damyang-recovery/update-caller-binding.json'))==PENDING_UPDATE_SHA256
        and c.reader.OPERATIONAL_CONTROLS_ENABLED is False,'update_and_finalizer_must_remain_inactive')
    raw=c.public_release.read_file(Path(root)/ACTUAL_FAILURE_REVIEW['path'])
    require(sha(raw)==ACTUAL_FAILURE_REVIEW['sha256'],'actual_failed_upload_review_digest_required')
    review=read_json(Path(root)/pins['review']['path'])
    requiredReview={'readOnlyReconciliationAllowed':True,'originalUpdateRunId':38927541164,
        'originalUpdateArtifactDigest':c.reader.EXACT_FAILED_UPDATE['artifactDigest'],
        'originalClaimCommentId':6219311010,'originalUpdateConclusion':'failure',
        'newClaimAllowed':False,'newProviderMutationAllowed':False,'IndexNowAllowed':False,
        'originalFailedArtifactFilesSHA256':c.journal.digest(c.reader.EXACT_FAILED_UPDATE_FILES),
        'actualFailureReviewSHA256':ACTUAL_FAILURE_REVIEW['sha256']}
    require(all(exact(review.get(k),v)for k,v in requiredReview.items()),'independent_exact_get_only_scope_required')
    return True


class ReadOnlyHTTP(c.UpdateHTTP):
    def call(self,method,url,payload=None):
        require(method=='GET' and payload is None,'reconciliation_get_only_no_payload')
        return super().call(method,url,payload)


def api_urls(pins,run_id):
    urls=c.api_urls(pins,run_id)
    urls|={c.journal.API_BASE+'/actions/runs/38927541164',
           c.journal.API_BASE+'/actions/jobs/117062829774',
           c.journal.API_BASE+'/actions/artifacts/12056828086',
           c.journal.API_BASE+'/issues/comments/6219311010'}
    return urls


def validated_header_projection(response):
    c.public_release.checked_headers(response)
    counts=collections.Counter(name.lower()for name,value in response.headers)
    consumed={'content-type','content-length','content-encoding','x-robots-tag','cf-mitigated','location','content-security-policy','cache-control'}
    rows=[]
    for name,value in response.headers:
        row={'name':name,'valueType':'str','valueCharacters':len(value),'valueUTF8Bytes':len(value.encode()),
            'valueSHA256':sha(value.encode()),'namePatternValid':True,'lengthWithin4096':True,'noCRorLF':True}
        if name.lower()in consumed:row['value']=value
        else:row['valueOmitted']=True
        rows.append(row)
    return {'state':'ALL_ORIGINAL_ROWS_VALIDATED_BEFORE_VALUE_PROJECTION',
        'checkerSHA256':c.IMPORT_PINS['public_release.py'],'rawRowCount':len(response.headers),
        'rawPairsCanonicalSHA256':c.journal.digest(response.headers),'allRowsTuple2Strings':True,
        'responseAndBodyBoundsChecked':True,'duplicates':{k:v for k,v in counts.items()if v>1},'rows':rows}


class Runtime(c.Runtime):
    def __init__(self,pins,env,control_root,build_root,baseline_root,update_root,github,http):
        super().__init__(pins,env,control_root,build_root,baseline_root,github,http)
        self.update_root=Path(update_root)
    def metadata(self):
        super().metadata()
        run,_=self.github.get(c.journal.API_BASE+'/actions/runs/38927541164')
        job,_=self.github.get(c.journal.API_BASE+'/actions/jobs/117062829774')
        history=c.reader.verify_exact_uploaded_failure(run,job)
        meta,_=self.github.get(c.journal.API_BASE+'/actions/artifacts/12056828086')
        c.reader.verify_artifact_meta(c.reader.EXACT_FAILED_UPDATE,meta)
        return history
    def artifact(self):
        baseline=super().artifact()
        return c.reader.validate_failed_uploaded_artifact(self.update_root,self.pins,baseline)
    def original_claim(self,history):
        comment,_=self.github.get(c.journal.API_BASE+'/issues/comments/6219311010')
        c.journal._trusted_comment(comment);claim=history['claim']
        require(comment['id']==c.reader.EXACT_UPLOAD_CLAIM_ID and comment['body'].startswith(c.update.MARKER)
            and exact(c.reader.json_raw(comment['body'][len(c.update.MARKER):]),{k:v for k,v in claim.items()if k!='commentId'}),
            'original_claim_direct_readback_required')
        c.update.inspect_full_journal(self.github.pages(),own_claim=claim)
        return claim
    def observe(self,history):
        names=('reconciliation-provider-before.json','reconciliation-provider-after.json',
            'reconciliation-public-http.json','reconciliation-public-observations.json','reconciliation-public-bodies')
        require(all(not Path(n).exists()for n in names),'fresh_reconciliation_outputs_required')
        claim=self.original_claim(history);expected=history['providerAfter'];started=utc()
        first=c.update.observe_current()
        c.baseline.save('reconciliation-provider-before.json',first)
        require(exact(first,expected),'uploaded_provider_projection_no_longer_current')
        observations=[];checks=[]
        try:
            for path,name,status in c.public_release.inventory():
                began=utc();response=self.http.call('GET',c.journal.ORIGIN+path)
                target=Path('reconciliation-public-bodies')/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(response.body)
                row={'path':path,'file':name,'url':c.journal.ORIGIN+path,'startedAtUTC':began,'responseAtUTC':utc(),
                    'httpStatus':response.status,'bodySHA256':sha(response.body),'bodyBytes':len(response.body)}
                observations.append(row);row['headerValidation']=validated_header_projection(response)
                check=c.public_release.verify_public_response(path,name,status,response,self.pins['releaseFiles'])
                row['publicCheck']=check;checks.append(check)
        finally:
            c.baseline.save('reconciliation-public-observations.json',{'schema':'damyang-reconciliation-public-raw-observations/v1',
                'currentRunId':self.env['GITHUB_RUN_ID'],'currentControlRevision':self.env['GITHUB_SHA'],
                'originalUpdateRunId':38927541164,'sourceRevision':c.SOURCE,'observations':observations,
                'state':'OBSERVATIONS_ONLY_NOT_INDEPENDENT_ACCEPTANCE','originalFailureHeadersRetained':False})
        public={'state':'current_full_successor_public_verified','revision':c.SOURCE,'checkedPaths':16,
            'status200':15,'status404':1,'checks':checks,'liveBrowserPixelsVerified':False}
        c.baseline.save('reconciliation-public-http.json',public)
        second=c.update.observe_current();c.baseline.save('reconciliation-provider-after.json',second)
        require(exact(first,second)and exact(second,expected),'provider_projection_changed_during_public16')
        self.metadata();self.original_claim(history)
        require(c.public_release.file_inventory('reconciliation-public-bodies')=={r['file']:r['rawBodySha256']for r in checks},
            'exact_reconciled_public_body_inventory_required')
        return {'schema':'damyang-uploaded-get-only-reconciliation/v1',
            'state':'EXACT_UPLOADED_PROVIDER_AND_PUBLIC16_REVERIFIED_PENDING_INDEPENDENT_ACCEPTANCE',
            'currentRunId':self.env['GITHUB_RUN_ID'],'currentControlRevision':self.env['GITHUB_SHA'],
            'currentRunAttempt':1,'sourceRevision':c.SOURCE,'originalUpdate':c.reader.EXACT_FAILED_UPDATE,
            'originalUpdateConclusion':'failure','originalArtifactFilesSHA256':c.journal.digest(c.reader.EXACT_FAILED_UPDATE_FILES),
            'originalClaimCommentId':claim['commentId'],'startedAtUTC':started,'completedAtUTC':utc(),
            'providerStateSHA256':c.journal.digest(second),'providerSnapshots':2,'publicPaths':16,
            'providerMethods':['GET'],'githubMethods':['GET'],'publicMethods':['GET'],
            'newClaimCreated':False,'providerMutationsPerformed':False,'IndexNowSubmitted':False,
            'originalFailureHeadersRetained':False,'independentAcceptance':False,'liveBrowserPixelsVerified':False}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=MODES)
    parser.add_argument('--control-root',type=Path,default=Path('control'))
    parser.add_argument('--build-root',type=Path,default=Path('damyang-recovery-build'))
    parser.add_argument('--baseline-root',type=Path,default=Path('damyang-recovery-baseline'))
    parser.add_argument('--update-root',type=Path,default=Path('damyang-recovery-update'))
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    try:
        pins=approved_pins(args.control_root/'docs/direct-damyang-recovery/reconciliation-binding.json')
        env=dict(os.environ);event=read_json(env.get('GITHUB_EVENT_PATH',''));authorize(pins,env,event,args.mode)
        require(args.control_root.resolve()==ROOT and Path.cwd()==Path(env.get('GITHUB_WORKSPACE','')),
            'executing_reconciliation_root_required')
        roots={'build':args.build_root,'baseline':args.baseline_root,'update':args.update_root}
        c.reader.verify_download_roots(env.get('GITHUB_WORKSPACE'),roots,preparing=args.mode=='prepare')
        verify_controls(args.control_root,pins);c.update.accepted_baseline()
        http=ReadOnlyHTTP(env.get('GH_TOKEN',''),api_urls(pins,env['GITHUB_RUN_ID']),
            [c.journal.ORIGIN+path for path,_,_ in c.public_release.inventory()])
        runtime=Runtime(pins,env,args.control_root,args.build_root,args.baseline_root,args.update_root,c.GitHubClient(http),http)
        metadata=runtime.metadata()
        if args.mode=='prepare':
            with Path(env['GITHUB_OUTPUT']).open('a')as stream:
                for role,key in (('build','build'),('baseline','baseline'),('update','failedUpdate')):
                    stream.write(role+'_run_id='+str(pins[key]['runId'])+'\n')
                    stream.write(role+'_artifact_id='+str(pins[key]['artifactId'])+'\n')
            result={'state':'EXACT_GET_ONLY_RECONCILIATION_INPUTS_SELECTED','sourceRevision':c.SOURCE,
                'currentRunId':env['GITHUB_RUN_ID'],'currentControlRevision':env['GITHUB_SHA'],
                'historicalUpload':metadata,'providerMutationsPerformed':False,'IndexNowSubmitted':False}
        else:
            history=runtime.artifact()
            if args.mode=='artifact':
                runtime.original_claim(history)
                result={'state':'EXACT_BUILD24_BASELINE3_FAILED_UPDATE17_CONSUMED',
                'sourceRevision':c.SOURCE,'currentRunId':env['GITHUB_RUN_ID'],'currentControlRevision':env['GITHUB_SHA'],
                'originalUpdateRunId':38927541164,'originalClaimCommentId':history['claim']['commentId'],
                'originalConclusion':'failure','sourceCodeExecuted':False,'artifactCodeExecuted':False}
            else:result=runtime.observe(history)
        c.baseline.save(args.report,result);print(json.dumps({'state':result['state'],'sourceRevision':c.SOURCE,
            'providerMutationsPerformed':False,'IndexNowSubmitted':False}));return 0
    except Exception as error:
        code=str(error)if isinstance(error,(ValueError,c.journal.RecoveryBlocked))and re.fullmatch('[A-Za-z0-9_]+',str(error))else 'reconciliation_blocked_or_outcome_uncertain'
        c.baseline.save(args.report,{'state':'GET_ONLY_RECONCILIATION_BLOCKED','mode':args.mode,
            'reason':code,'sourceRevision':c.SOURCE,'providerMutationsPerformed':False,
            'IndexNowSubmitted':False,'automaticReuploadAllowed':False})
        print('GET-only reconciliation blocked; original upload is not retried.');return 1

if __name__=='__main__':raise SystemExit(main())
