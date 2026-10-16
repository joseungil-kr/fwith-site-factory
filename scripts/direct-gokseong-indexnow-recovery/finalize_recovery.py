"""Dormant Gokseong same-proof finalizer. No provider operation or source execution.

Reuses the saved Damyang bounded transport and full journal reader, the unchanged
shared IndexNow helper, and Gokseong's actual-successful artifact/public checker.
Operational activation requires a separate exact independent review and lease.
"""
import argparse, hashlib, json, os, re, shutil, sys, time, unicodedata
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPRedirectHandler
import indexnow_recovery as guard
DIRECTORY=Path(__file__).resolve().parent
CONTROL=DIRECTORY.parents[1]
sys.path.insert(0,str(DIRECTORY.parent/'direct-gokseong'))
import publish
OWNER='joseungil-kr'
SOURCE='7e6573e2eb97ac5473622d37478729ee43b565f1'
BRANCH='source/gokseong-dedicated-proof-production-20261016'
SOURCE_ROOT_TREE='eadaedcdc4d9df1144fd9b3ecb651dfaf2526f80'
WORKFLOW='.github/workflows/gokseong-indexnow-recovery.yml'
JOB='finalize_indexnow'
TITLE='[GOKSEONG-INDEXNOW-RECOVERY] 20261016'
CONCURRENCY='gokseong-direct-public-release'
OPERATIONAL_CONTROLS_ENABLED=False
require=guard.require
sha=guard.sha
positive=lambda value:type(value) is int and value>0
TRUSTED_ENV_KEYS=frozenset(['PATH','HOME','LANG','LC_CTYPE','PYTHONDONTWRITEBYTECODE','GH_TOKEN','GITHUB_REPOSITORY','GITHUB_REF','GITHUB_ACTOR','GITHUB_TRIGGERING_ACTOR','GITHUB_RUN_ATTEMPT','GITHUB_EVENT_NAME','GITHUB_JOB','RUNNER_ENVIRONMENT','GITHUB_SHA','GITHUB_RUN_ID','GITHUB_EVENT_PATH','GITHUB_OUTPUT','GITHUB_WORKSPACE','REVISION'])


def json_raw(raw):
    def pairs(values):
        out = {}
        for key, value in values:
            require(key not in out, 'duplicate_json_key')
            out[key] = value
        return out
    def constant(_): raise guard.RecoveryBlocked('nonfinite_json')
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except guard.RecoveryBlocked: raise
    except Exception: raise guard.RecoveryBlocked('invalid_json') from None

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None

class BoundedHTTP:
    """No redirect, no retry, fixed destinations, bounded bytes/headers/time.

    The sole token is injected by the reviewed workflow. It is sent only to the
    exact repository GitHub API URLs admitted by GitHubClient, never public URLs.
    """
    def __init__(self, token, api_urls, public_urls, *, opener=None, clock=time.monotonic):
        require(type(token) is str and bool(token) and '\r' not in token and '\n' not in token,
                'workflow_github_token_required')
        self._token = token
        self.api_urls = frozenset(api_urls); self.public_urls = frozenset(public_urls)
        self.opener = opener if opener is not None else build_opener(NoRedirect())
        self.clock = clock; self.post_reserved = False
        self.request_evidence_state = 'not_observed'; self.response_evidence_state = 'not_observed'

    def call(self, method, url, payload=None):
        comment_page = re.fullmatch(
            re.escape(guard.API_BASE) + r'/issues/comments\?per_page=100&page=([1-9][0-9]{0,4})', url)
        api = url in self.api_urls or (comment_page is not None and int(comment_page[1]) <= guard.MAX_PAGES)
        comment_write = url == guard.ISSUE_URL + '/comments'
        require((method == 'GET' and payload is None and (api or url in self.public_urls))
                or (method == 'POST' and type(payload) is bytes and len(payload) <= 65536
                    and (comment_write or url == guard.ENDPOINT)), 'fixed_http_scope_required')
        if method == 'POST' and url == guard.ENDPOINT:
            require(not self.post_reserved, 'caller_single_post_only')
            self.post_reserved = True
        headers = {'User-Agent': 'Gokseong-Reviewed-Recovery/1.0', 'Accept-Encoding': 'identity',
                   'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        if api or comment_write:
            headers.update({'Authorization': 'Bearer ' + self._token,
                            'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
        if method == 'POST': headers['Content-Type'] = 'application/json; charset=utf-8'
        req = Request(url, method=method, data=payload, headers=headers)
        if method == 'POST' and url == guard.ENDPOINT: self.observe_request(req)
        start = self.clock()
        try:
            response = self.opener.open(req, timeout=20)
        except HTTPError as error:
            response = error
        except Exception:
            raise guard.RecoveryBlocked('http_outcome_unconfirmed') from None
        response_started = False; body_complete = False
        body = bytearray(); pairs = []; lengths = []
        try:
            with response:
                require(response.geturl() == url, 'unexpected_response_url')
                require(type(response.code) is int and not 300 <= response.code < 400, 'redirect_forbidden')
                response_started = True
                pairs = list(response.headers.items())
                require(len(pairs) <= 100 and all(len(k) <= 128 and len(v) <= 4096 for k, v in pairs),
                        'http_header_limit')
                lengths = [v for k, v in pairs if k.lower() == 'content-length']
                require(len(lengths) <= 1 and (not lengths or (lengths[0].isdigit()
                        and int(lengths[0]) <= guard.MAX_RESPONSE)), 'http_length_limit')
                encodings = [v for k, v in pairs if k.lower() == 'content-encoding']
                require(len(encodings) <= 1 and (not encodings or encodings[0].lower() == 'identity'),
                        'compressed_response_forbidden')
                body = bytearray()
                reader = getattr(response, 'read1', response.read)
                while True:
                    require(self.clock() - start <= 60, 'http_deadline_exceeded')
                    part = reader(min(65536, guard.MAX_RESPONSE + 1 - len(body)))
                    if not part: break
                    body.extend(part)
                    require(len(body) <= guard.MAX_RESPONSE, 'http_body_limit')
                require(not lengths or len(body) == int(lengths[0]), 'truncated_http_body')
                body_complete = True
                result = guard.RawResponse(response.code, bytes(body), pairs)
                if method == 'POST' and url == guard.ENDPOINT: self.observe_response(result)
                return result
        except guard.RecoveryBlocked as error:
            if method == 'POST' and url == guard.ENDPOINT and response_started:
                self.observe_response_failure(response.code, bytes(body), lengths, str(error), body_complete)
            raise
        except Exception as error:
            # HTTPError is handled above as a response. IncompleteRead.partial
            # contains additional bytes from the failed read, not prior chunks.
            extra = getattr(error, 'partial', None)
            omitted = 0
            if type(extra) is bytes:
                available = max(0, guard.MAX_RESPONSE + 1 - len(body))
                body.extend(extra[:available]); omitted = max(0, len(extra)-available)
            if method == 'POST' and url == guard.ENDPOINT and response_started:
                self.observe_response_failure(response.code, bytes(body), lengths,
                    'response_capture_failed' if body_complete else 'http_read_incomplete_or_unconfirmed',
                    body_complete, omitted)
            raise guard.RecoveryBlocked('http_outcome_unconfirmed') from None

    def observe_response_failure(self, status, captured, lengths, reason, body_complete, omitted=0):
        # Best-effort evidence cannot spend another HTTP attempt or promote an
        # incomplete body to a completed response. Failure to save is still an
        # unknown, already-spent outcome under the durable started journal.
        self.response_evidence_state = 'failed_response_capture_unconfirmed'
        try:
            safe = safe_raw_body(guard.RawResponse(status,captured,[]),self.contract)
            declared = int(lengths[0]) if len(lengths)==1 and lengths[0].isdigit() and len(lengths[0])<16 else None
            value=dict(state='response_failed_or_capture_incomplete',httpStatusObserved=status,
                responseBodyReadComplete=body_complete,submissionOutcomeConfirmed=False,
                declaredContentLength=declared,capturedPrefixBytes=len(captured),
                capturedPrefixSha256=sha(captured),additionalExceptionBytesOmitted=omitted,
                rawPrefixRetained=safe is not None,rawPrefixFile='response-body.failed-prefix.txt' if safe is not None else None,
                prefixOmissionReason=None if safe is not None else 'bounded_public_safety_check_not_satisfied',
                reason=reason,postBudgetSpent=self.post_reserved,retryAllowed=False)
            self.evidence.mkdir(parents=True,exist_ok=True)
            if safe is not None:
                require(safe==captured,'response_prefix_bytes_changed')
                (self.evidence/'response-body.failed-prefix.txt').write_bytes(safe)
            save(self.evidence/'response-failure-observation.json',value)
            self.response_evidence_state = 'failed_response_prefix_retained' if safe is not None else 'failed_response_prefix_withheld'
        except Exception:
            return False
        return True

    def observe_request(self, request):
        self.request_evidence_state = 'request_capture_unconfirmed'
        require(request.data == json.dumps(guard._payload(self.contract)).encode(), 'actual_request_bytes_mismatch')
        require(request.get_header('Authorization') is None, 'public_request_credential_forbidden')
        require(len(request.data)==196 and sha(request.data)=='247e3f4628205514f3c1faf995ad9bd5fbf2f5f71629deac0993c3f1261ce719', 'pinned_request_serialization_mismatch')
        self.evidence.mkdir(parents=True,exist_ok=True)
        (self.evidence/'request-body.json').write_bytes(request.data)
        save(self.evidence/'request-observation.json',dict(method=request.get_method(),url=request.full_url,bodyBytes=len(request.data),bodySha256=sha(request.data),provenance='Actual urllib Request.data immediately before opener.open; no claim of a packet-level capture',authorizationHeaderPresent=False))
        self.request_evidence_state = 'actual_request_data_retained'

    def observe_response(self, response):
        self.response_evidence_state = 'complete_response_capture_unconfirmed'
        safe=safe_raw_body(response,self.contract)
        evidence=dict(responseBodyReadComplete=True,httpStatus=response.status,rawBodyBytes=len(response.body),rawBodySha256=sha(response.body),rawBodyRetained=safe is not None,rawBodyFile='response-body.txt' if safe is not None else None,bodyOmissionReason=None if safe is not None else 'bounded_public_safety_check_not_satisfied',diagnostics=guard.diagnostics(response,self.contract))
        if safe is not None:
            require(safe==response.body,'response_raw_bytes_changed')
            (self.evidence/'response-body.txt').write_bytes(safe)
        save(self.evidence/'response-observation.json',evidence)
        self.response_evidence_state = 'complete_response_retained' if safe is not None else 'complete_response_withheld'


class GitHubClient:
    def __init__(self, http): self.http = http

    def get(self, url):
        response = self.http.call('GET', url)
        require(response.status == 200, 'github_get_not_http200')
        ctypes = [v for k, v in response.headers if k.lower() == 'content-type']
        require(len(ctypes) == 1 and ctypes[0].lower().startswith('application/json'), 'github_json_content_type_required')
        return json_raw(response.body), response

    def read_page(self, number):
        require(type(number) is int and 1 <= number <= guard.MAX_PAGES, 'journal_page_number_invalid')
        url = guard.page_url(number); comments, response = self.get(url)
        require(type(comments) is list and len(comments) <= 100, 'github_full_comment_page_required')
        links = [v for k, v in response.headers if k.lower() == 'link']
        require(len(links) <= 1, 'ambiguous_github_link_header')
        next_url = None; rels = set()
        if links:
            require(len(links[0]) <= 4096, 'github_link_header_limit')
            for link in links[0].split(','):
                match = re.fullmatch(r'\s*<([^<>]+)>;\s*rel="(next|prev|first|last)"\s*', link)
                require(match is not None, 'unrecognized_github_pagination')
                dest, rel = match.groups()
                require(rel not in rels, 'duplicate_github_pagination_relation'); rels.add(rel)
                # GitHub's Link may identify this exact repository by immutable ID.
                # Normalize only the Link; HTTP still uses the original name URL.
                page_match = re.fullmatch(r'(?:' + re.escape(guard.API_BASE)
                    + r'|https://api\.github\.com/repositories/1360554691)'
                    + r'/issues/comments\?per_page=100&page=([1-9][0-9]*)', dest)
                require(page_match is not None and int(page_match[1]) <= guard.MAX_PAGES,
                        'foreign_or_noncanonical_github_pagination')
                dest = guard.page_url(int(page_match[1]))
                if rel == 'next':
                    require(dest == guard.page_url(number + 1), 'github_next_page_mismatch'); next_url = dest
                if rel == 'prev': require(number > 1 and dest == guard.page_url(number - 1), 'github_prev_page_mismatch')
                if rel == 'first': require(dest == guard.page_url(1), 'github_first_page_mismatch')
        return guard.AuditPage(url, response.status, comments, next_url, True)

    def write_record(self, record):
        payload = json.dumps({'body': guard.MARKER + json.dumps(record, ensure_ascii=False, sort_keys=True)}).encode()
        response = self.http.call('POST', guard.ISSUE_URL + '/comments', payload)
        require(response.status == 201, 'journal_comment_creation_unconfirmed')
        value = json_raw(response.body)
        guard._trusted_comment(value)
        return value

def verify_run(row, data, path, *, current=False):
    require(type(data) is dict and data.get('id') == row['runId'] and type(data.get('id')) is int
            and type(data.get('run_attempt')) is int and data.get('run_attempt') == 1 and data.get('event') == 'issues'
            and data.get('head_branch') == 'main' and data.get('head_sha') == row['controlRevision']
            and data.get('path') == path and data.get('repository', {}).get('full_name') == guard.REPOSITORY
            and data.get('actor', {}).get('login') == OWNER and data.get('triggering_actor', {}).get('login') == OWNER,
            'actual_workflow_run_identity_mismatch')
    require((data.get('status') == 'in_progress' and data.get('conclusion') is None) if current else
            (data.get('status') == 'completed' and data.get('conclusion') == row.get('expectedConclusion','success')),
            'workflow_run_not_successful_or_current')

def verify_artifact_meta(row, data):
    require(type(data) is dict and data.get('id') == row['artifactId'] and type(data.get('id')) is int
            and data.get('expired') is False and data.get('name') == row['artifactName']
            and data.get('digest') == row['artifactDigest'] and positive(data.get('size_in_bytes'))
            and positive(row.get('artifactBytes')) and data['size_in_bytes'] == row['artifactBytes']
            and data['size_in_bytes'] <= 32 * 1024 * 1024
            and type(data.get('workflow_run', {}).get('id')) is int
            and data.get('workflow_run', {}).get('id') == row['runId']
            and data.get('workflow_run', {}).get('head_sha') == row['controlRevision']
            and data.get('workflow_run', {}).get('head_branch') == 'main',
            'actual_artifact_metadata_mismatch')


DOWNLOAD_NAMES={'build':'gokseong-recovery-build','publication':'gokseong-recovery-publication'}
BINDING_PATH='scripts/direct-gokseong-indexnow-recovery/recovery-binding.json'

def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')

def read(path):
    path=Path(path)
    require(path.is_file() and not any(p.is_symlink() for p in (path,*path.parents)), 'regular_file_required')
    require(path.stat().st_size<=32*1024*1024,'local_file_limit')
    return path.read_bytes()

def read_json(path): return json_raw(read(path))

def inventory(root):
    root=Path(root)
    require(root.is_dir() and not any(p.is_symlink() for p in (root,*root.parents)), 'regular_artifact_root_required')
    out={}
    for p in sorted(root.rglob('*')):
        require(not p.is_symlink(), 'artifact_symlink_forbidden')
        if p.is_dir(): continue
        require(p.is_file(), 'artifact_nonregular_file_forbidden')
        out[p.relative_to(root).as_posix()]=sha(read(p))
    return out

def safe_raw_body(response,contract):
    """Retain exact small public diagnostic text only, otherwise hash and length.

    This is deliberately conservative. It is not a redaction routine: any body
    needing transformation is withheld rather than labeled a raw retained body.
    """
    if type(response.body) is not bytes or len(response.body)>4096: return None
    try: text=response.body.decode('utf-8')
    except UnicodeDecodeError: return None
    if any(ord(c)<32 and c not in '\t\r\n' for c in text): return None
    # Escaped JSON or text may conceal sensitive labels. Never transform it and
    # then call it raw: retain only its digest/length with an explicit omission.
    if '\\' in text: return None
    # Only closed, scalar diagnostic JSON may be uploaded as raw text. Reject
    # malformed/truncated, nested, array, and arbitrary-field JSON conservatively.
    # This check does not rewrite or reserialize retained bytes.
    if any(character in text for character in '{}[]"'):
        try: parsed=json_raw(text)
        except Exception: return None
        if type(parsed) is not dict or not set(parsed)<={'error','message','code','status','title','detail','reason'}: return None
        if not all(value is None or type(value) in (str,int,bool) for value in parsed.values()): return None
    # Validation-only normalization catches compatibility-letter labels; stored
    # bytes remain untouched. Unexpected letter scripts are conservatively withheld.
    scrub=unicodedata.normalize('NFKC',text).replace(contract.active_key,'PUBLIC_PROOF')
    if any(c.isalpha() and not (c.isascii() or '\uac00'<=c<='\ud7a3' or '\u1100'<=c<='\u11ff' or '\u3130'<=c<='\u318f') for c in scrub): return None
    if re.search(r'(?i)(bearer|authorization|password|api[-_ ]?key|pwd|passwd|secret|token|cookie|private|credential|https?://|@|/home/|/tmp/|/root/|BEGIN [A-Z ]*KEY)',scrub): return None
    if re.search(r'[A-Za-z0-9_+-]{32,}',scrub): return None
    if not re.fullmatch(r'[\w\s.,:;!?\-{}\[\]"\x27()/=\\]*',scrub): return None
    return response.body

def approved_pins(path):
    # First guard precedes environment, credentials, files, and network access.
    require(OPERATIONAL_CONTROLS_ENABLED is True,'operational_review_seal_missing')
    pins=read_json(path)
    require(type(pins) is dict and type(pins.get('independentOperationalReview')) is dict,
            'independent_operational_review_required')
    return pins

def authorize(pins,env,event):
    require(sys.flags.optimize==0,'optimized_python_forbidden')
    require(env.get('GITHUB_REPOSITORY')==guard.REPOSITORY and env.get('GITHUB_REF')=='refs/heads/main'
        and env.get('GITHUB_ACTOR')==OWNER and env.get('GITHUB_TRIGGERING_ACTOR')==OWNER
        and env.get('GITHUB_RUN_ATTEMPT')=='1' and env.get('GITHUB_EVENT_NAME')=='issues'
        and env.get('GITHUB_JOB')==JOB and env.get('RUNNER_ENVIRONMENT')=='github-hosted'
        and env.get('REVISION')==SOURCE,'exact_owner_main_first_hosted_job_required')
    require(set(env)<=TRUSTED_ENV_KEYS,'trusted_finalizer_environment_required')
    require(guard._valid_sha(env.get('GITHUB_SHA'),40) and re.fullmatch('[1-9][0-9]*',env.get('GITHUB_RUN_ID','')) is not None,'actual_execution_identity_required')
    repo=event.get('repository',{}); issue=event.get('issue',{})
    require(event.get('action')=='opened' and repo.get('full_name')==guard.REPOSITORY
        and repo.get('owner',{}).get('login')==OWNER and repo.get('owner',{}).get('type')=='User'
        and event.get('sender',{}).get('login')==OWNER and event.get('sender',{}).get('type')=='User','exact_event_identity_required')
    require(issue.get('title')==TITLE and issue.get('user',{}).get('login')==OWNER
        and issue.get('user',{}).get('type')=='User' and issue.get('state')=='open'
        and positive(issue.get('number')) and issue['number']!=399 and 'pull_request' not in issue,'exact_recovery_issue_required')
    raw=issue.get('body');require(type(raw) is str and len(raw.encode())<=4096,'bounded_request_body_required')
    expected=dict(schemaVersion=1,mode='no-deploy-indexnow-recovery',source_branch=BRANCH,source_revision=SOURCE,
        expected_control_revision=env['GITHUB_SHA'],receipt_issue=399,operational_binding_sha256=guard.digest(pins))
    require(guard.exact(json_raw(raw),expected),'closed_exact_request_required')
    require(pins.get('schemaVersion')==1 and type(pins.get('schemaVersion')) is int
        and pins.get('status')=='INDEPENDENTLY_REVIEWED_ACTUAL_RECOVERY'
        and pins.get('sourceRevision')==SOURCE and pins.get('sourceBranch')==BRANCH
        and pins.get('receiptIssue')==399 and type(pins.get('receiptIssue')) is int
        and pins.get('maximumAdditionalPOSTs')==1 and type(pins.get('maximumAdditionalPOSTs')) is int
        and pins.get('originalFingerprint')==guard.CHAIN['originalFingerprint'],'fixed_same_proof_binding_required')
    require(set(pins)=={'schemaVersion','status','sourceRevision','sourceBranch','receiptIssue','maximumAdditionalPOSTs','originalFingerprint','build','publication','independentOperationalReview','controlFiles','workflowFiles'},'closed_operational_binding_required')
    for name in ('build','publication','independentOperationalReview','controlFiles','workflowFiles'):
        require(type(pins.get(name)) is dict and bool(pins[name]),'actual_binding_missing')
    require(pins['build'].get('runId')==38923430470 and pins['build'].get('artifactId')==12055617902
        and pins['build'].get('artifactDigest')=='sha256:deac983235eadbacb1fecee2b4f4249f738af94a609f4a544463977a9f124316'
        and pins['build'].get('controlRevision')=='64be198af7b57a0ff64fa1ae8b049947f066aff3'
        and pins['build'].get('expectedConclusion')=='success'
        and pins['build'].get('workflowPath')=='.github/workflows/gokseong-production-build-only.yml','fixed_actual_build_required')
    require(pins['publication'].get('runId')==38928433446 and pins['publication'].get('artifactId')==12058026462
        and pins['publication'].get('artifactDigest')=='sha256:f37ee7c35336138262b8d6fd18ed28e2234428227fd0ac59e8e6089b2b30f633'
        and pins['publication'].get('controlRevision')=='8379c174156518f2435481cc767c14b64f50b3ef'
        and pins['publication'].get('expectedConclusion')=='failure'
        and pins['publication'].get('workflowPath')=='.github/workflows/gokseong-production-publish.yml','original_failed_publication_required')
    return expected

def api_urls(pins,run_id):
    urls={guard.ISSUE_URL,guard.API_BASE+'/git/ref/heads/main',guard.API_BASE+'/actions/runs/'+run_id,
        guard.API_BASE+'/git/ref/heads/'+BRANCH,guard.API_BASE+'/git/commits/'+SOURCE}
    for role in DOWNLOAD_NAMES:
        row=pins[role];urls.update({guard.API_BASE+'/actions/runs/'+str(row['runId']),guard.API_BASE+'/actions/artifacts/'+str(row['artifactId'])})
    return urls

def verify_roots(workspace,roots,preparing):
    require(type(workspace) is str and Path(workspace).is_absolute() and set(roots)==set(DOWNLOAD_NAMES),'fixed_workspace_required')
    base=Path(workspace)
    require(base.is_dir() and not any(p.is_symlink() for p in (base,*base.parents)),'regular_workspace_required')
    for role,name in DOWNLOAD_NAMES.items():
        root=Path(roots[role]);require(root.absolute()==base/name and not any(p.is_symlink() for p in (root,*root.parents)),'fixed_download_root_required')
        require(not root.exists() if preparing else root.is_dir(),'fresh_or_downloaded_root_required')

def verify_local_control(root,pins,env):
    root=Path(root)
    require(root.resolve()==CONTROL.resolve(),'fixed_control_checkout_required')
    publish.gate.trusted_control(env)
    require(not publish.gate.git(root,'status','--porcelain','--untracked-files=all','--','scripts/direct-gokseong-indexnow-recovery','.github/workflows').strip(),'recovery_control_checkout_changed')
    required={BINDING_PATH.replace('recovery-binding.json','finalize_recovery.py'),BINDING_PATH.replace('recovery-binding.json','indexnow_recovery.py'),WORKFLOW,'site-factory/engine/indexnow_finalize.py','scripts/direct-gokseong/publish.py','.github/site-factory-sites.json'}
    required.update(p.relative_to(root).as_posix() for p in (root/'scripts/direct-gokseong').rglob('*') if p.is_file())
    required.update(p.relative_to(root).as_posix() for p in (root/'docs/direct-gokseong').rglob('*') if p.is_file() and p.relative_to(root).as_posix()!=pins['independentOperationalReview']['path'])
    require(required<=set(pins['controlFiles']),'complete_reviewed_control_inventory_required')
    require(BINDING_PATH not in pins['controlFiles'] and pins['independentOperationalReview']['path'] not in pins['controlFiles'],'noncircular_review_binding_required')
    for name,digest in pins['controlFiles'].items():
        require(type(name) is str and re.fullmatch('[A-Za-z0-9_./-]+',name) is not None and not name.startswith('/') and '..' not in name.split('/'),'unsafe_control_path')
        require(sha(read(root/name))==digest,'reviewed_control_file_changed')
    require(pins['controlFiles']['site-factory/engine/indexnow_finalize.py']==guard.HELPER_SHA256
        and pins['controlFiles']['scripts/direct-gokseong/publish.py']=='33c6b65330ec4fd0b1b85e10445b78832df4dde0ae27a2349a23153b762b8001','unchanged_shared_and_public_helpers_required')
    registry=read_json(root/'.github/site-factory-sites.json')
    require(type(registry.get('sites')) is dict and not any('gokseong' in (name+guard.canonical(value)).lower() for name,value in registry['sites'].items()),'gokseong_must_remain_outside_generic_registry')
    actual={p.relative_to(root).as_posix():sha(read(p)) for p in (root/'.github/workflows').iterdir() if p.suffix in ('.yml','.yaml')}
    require(actual==pins['workflowFiles'],'complete_workflow_inventory_changed')
    raw=read(root/WORKFLOW).decode()
    require(raw.count('\nconcurrency:\n  group: '+CONCURRENCY+'\n  cancel-in-progress: false\n')==1,'shared_concurrency_required')
    require(raw.count('\n  '+JOB+':\n')==1,'exact_finalizer_job_required')
    job=raw.split('\n  '+JOB+':\n')[1]
    require(not re.search(r'\n  [A-Za-z0-9_-]+:\n',job),'one_finalizer_job_required')
    require(not re.search(r'(CLOUDFLARE_|\bnpx\b|\bnpm\b|setup-node|wrangler|\bnode\s|\bdeploy\s|\battach\s)',job),'provider_or_source_execution_forbidden')
    review=pins['independentOperationalReview'];name=review.get('path')
    require(type(name) is str and name.startswith('docs/direct-gokseong/') and '..' not in Path(name).parts,'review_path_invalid')
    data=read(root/name);require(sha(data)==review.get('sha256'),'independent_review_digest_mismatch')
    value=json_raw(data)
    expected=dict(verdict='APPROVED_ACTUAL_GOKSEONG_NO_DEPLOY_RECOVERY',sourceRevision=SOURCE,
        originalFingerprint=guard.CHAIN['originalFingerprint'],maximumAdditionalPOSTs=1,
        controlFilesSha256=guard.digest(pins['controlFiles']),workflowFilesSha256=guard.digest(pins['workflowFiles']),
        buildBindingSha256=guard.digest(pins['build']),publicationBindingSha256=guard.digest(pins['publication']),
        allKnownGokseongPublishersUseSharedConcurrency=True,freshLiveBrowserPixelsClaimed=False)
    require(all(guard.exact(value.get(k),v) for k,v in expected.items()),'complete_independent_review_required')
    return True

def public_paths(files):
    return ['/',*sorted('/'+name for name in files if not name.endswith('.html') and name!='_headers'),'/.gokseong-release-missing-'+SOURCE+'/']

def checked_headers(response):
    require(type(response) is guard.RawResponse and type(response.status) is int and type(response.body) is bytes
        and len(response.body)<=guard.MAX_RESPONSE and type(response.headers) is list and len(response.headers)<=100,'bounded_public_response_required')
    msg=Message();seen=set()
    for row in response.headers:
        require(type(row) is tuple and len(row)==2 and all(type(x) is str for x in row),'public_header_shape_invalid')
        name,value=row;lower=name.lower()
        require(re.fullmatch('[a-z0-9-]{1,128}',lower) is not None and len(value)<=4096 and '\r' not in value and '\n' not in value,'public_header_value_invalid')
        require(lower not in seen or lower=='server-timing','ambiguous_public_header')
        if lower not in seen: msg[name]=value
        seen.add(lower)
    require('content-type' in seen,'public_content_type_required')
    return msg

def verify_response(path,status,response,files):
    headers=checked_headers(response)
    require(response.status==status,'public_http_status_mismatch')
    body=response.body
    file='index.html' if path=='/' else ('404.html' if status==404 else path.lstrip('/'))
    require(file in files,'fixed_public_file_required')
    if file=='robots.txt':
        publish.managed_robots.verify_headers(headers)
        publish.managed_robots.verify(body,files[file],guard.ORIGIN,[guard.HOME])
    else:
        if file.endswith('.html') and sha(body)!=files[file]: body=publish.strip_one_cf_beacon(body,files[file])
        require(sha(body)==files[file],'public_file_digest_mismatch')
    return headers

class Runtime:
    def __init__(self,*,pins,env,control_root,roots,github,http,evidence):
        self.pins=pins;self.env=env;self.control_root=Path(control_root);self.roots={k:Path(v) for k,v in roots.items()}
        self.github=github;self.http=http;self.evidence=Path(evidence);self.adapter=None;self.public_observations=[]
        self.binding=guard.Binding(SOURCE,env['GITHUB_SHA'],pins['build']['artifactDigest'][7:],
            'https://github.com/'+guard.REPOSITORY+'/actions/runs/'+env['GITHUB_RUN_ID'])
        self.release=self.roots['build']/'release'
        self.files=read_json(self.release/'release.json')['files'] if self.release.is_dir() else None

    def serialized(self):
        verify_local_control(self.control_root,self.pins,self.env)
        main,_=self.github.get(guard.API_BASE+'/git/ref/heads/main')
        require(main.get('object',{}).get('type')=='commit' and main.get('object',{}).get('sha')==self.env['GITHUB_SHA'],'main_moved_since_exact_request')
        run,_=self.github.get(guard.API_BASE+'/actions/runs/'+self.env['GITHUB_RUN_ID'])
        verify_run(dict(runId=int(self.env['GITHUB_RUN_ID']),controlRevision=self.env['GITHUB_SHA']),run,WORKFLOW,current=True)
        return True

    def metadata(self):
        branch,_=self.github.get(guard.API_BASE+'/git/ref/heads/'+BRANCH)
        require(branch.get('ref')=='refs/heads/'+BRANCH and branch.get('object',{}).get('type')=='commit' and branch.get('object',{}).get('sha')==SOURCE,'source_branch_moved')
        commit,_=self.github.get(guard.API_BASE+'/git/commits/'+SOURCE)
        require(commit.get('sha')==SOURCE and commit.get('tree',{}).get('sha')==SOURCE_ROOT_TREE,'original_source_commit_mismatch')
        for role in DOWNLOAD_NAMES:
            row=self.pins[role];run,_=self.github.get(guard.API_BASE+'/actions/runs/'+str(row['runId']));verify_run(row,run,row['workflowPath'])
            art,_=self.github.get(guard.API_BASE+'/actions/artifacts/'+str(row['artifactId']));verify_artifact_meta(row,art)
        journal,_=self.github.get(guard.ISSUE_URL)
        require(journal.get('number')==399 and type(journal.get('number')) is int and journal.get('state')=='open'
            and journal.get('title')=='[GOKSEONG-INDEXNOW-RECEIPTS] 20261016' and journal.get('user',{}).get('login')==OWNER
            and 'pull_request' not in journal and journal.get('repository_url')==guard.API_BASE,'original_receipt_issue_required')

    def validate_binding(self,binding):
        require(binding==self.binding,'runtime_binding_changed');self.metadata()
        for role in DOWNLOAD_NAMES:
            require(inventory(self.roots[role])==self.pins[role]['files'],'complete_actual_artifact_changed')
        require(inventory(Path('release')/'dist')==self.files,'staged_release_changed')
        require(read(Path('release')/'release.json')==read(self.release/'release.json'),'staged_manifest_changed')
        return True

    def public_get(self,path,status=200):
        require(path in public_paths(self.files),'fixed_public_path_required')
        response=self.http.call('GET',guard.ORIGIN+path)
        headers=verify_response(path,status,response,self.files)
        row=dict(path=path,httpStatus=response.status,bodyBytes=len(response.body),rawBodySha256=sha(response.body))
        self.public_observations.append(row)
        # Full HTML/image/proof response bodies are already public; save these
        # exact response bytes separately from filtered HTTP metadata.
        self.evidence.mkdir(parents=True,exist_ok=True)
        (self.evidence/('public-'+str(len(self.public_observations)).zfill(3)+'.body')).write_bytes(response.body)
        save(self.evidence/'public-observations.json',self.public_observations)
        return response.body,headers

    def validate_public(self,binding):
        require(binding==self.binding,'runtime_binding_changed')
        previous=publish.get
        try:
            publish.get=self.public_get
            result=publish.http_once(read_json('http-contract.json'))
        finally: publish.get=previous
        require(result['checkedPaths']==15 and result['state']=='public_release_verified','full_public15_required')
        save(self.evidence/'public-release.json',result)
        return True

    def transport(self,method,url,payload=None):
        response=self.http.call(method,url,payload)
        if method=='GET':
            require(url.startswith(guard.ORIGIN+'/'),'fixed_public_origin_required')
            path=url[len(guard.ORIGIN):];require(path in public_paths(self.files),'fixed_public_probe_required')
            verify_response(path,200,response,self.files)
        return response

    def run(self):
        require(OPERATIONAL_CONTROLS_ENABLED is True,'operational_review_seal_missing')
        self.serialized();self.metadata()
        for role in DOWNLOAD_NAMES:
            require(inventory(self.roots[role])==self.pins[role]['files'],'complete_actual_artifact_changed')
        require(not Path('release').exists(),'fresh_staging_required')
        shutil.copytree(self.release,'release',symlinks=True)
        artifact=publish.artifact();save(self.evidence/'retained-artifact-verification.json',artifact)
        require(artifact['files']==16 and artifact['revision']==SOURCE,'exact_retained_release_required')
        contract=guard.load_contract('release');self.http.contract=contract;self.http.evidence=self.evidence
        adapter=guard.RecoveryAdapter(contract=contract,binding=self.binding,
            helper_path=self.control_root/'site-factory/engine/indexnow_finalize.py',read_page=self.github.read_page,
            write_record=self.github.write_record,transport=self.transport,validate_binding=self.validate_binding,
            assert_serialized=self.serialized,validate_full_public_release=self.validate_public)
        self.adapter=adapter
        return adapter.run(Path('release'),dict(siteKey=guard.SITE_KEY,siteUrl=guard.ORIGIN,indexnowKey=contract.active_key,productionEnabled=True,launchMode='live'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','finalize'])
    parser.add_argument('--control-root',type=Path,default=Path('control'))
    parser.add_argument('--build-root',type=Path,default=Path(DOWNLOAD_NAMES['build']))
    parser.add_argument('--publication-root',type=Path,default=Path(DOWNLOAD_NAMES['publication']))
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();runtime=None
    try:
        pins=approved_pins(args.control_root/BINDING_PATH)
        env=dict(os.environ);event=read_json(env.get('GITHUB_EVENT_PATH',''));authorize(pins,env,event)
        roots={'build':args.build_root,'publication':args.publication_root}
        verify_roots(env.get('GITHUB_WORKSPACE'),roots,args.mode=='prepare')
        # Only exact, independently bound artifact file names enter this list.
        files={name.removeprefix('release/dist/'):digest for name,digest in pins['build']['files'].items() if name.startswith('release/dist/')}
        require(len(files)==16,'exact_sixteen_static_files_required')
        http=BoundedHTTP(env.get('GH_TOKEN',''),api_urls(pins,env['GITHUB_RUN_ID']),[guard.ORIGIN+path for path in public_paths(files)])
        runtime=Runtime(pins=pins,env=env,control_root=args.control_root,roots=roots,github=GitHubClient(http),http=http,evidence=args.report.parent/'evidence')
        if args.mode=='prepare':
            runtime.serialized();runtime.metadata()
            out=Path(env['GITHUB_OUTPUT'])
            with out.open('a') as stream:
                for role in DOWNLOAD_NAMES:
                    stream.write(role+'_run_id='+str(pins[role]['runId'])+'\n'+role+'_artifact_id='+str(pins[role]['artifactId'])+'\n')
            result=dict(state='actual_artifact_metadata_selected',mutationsPerformed=False)
        else: result=runtime.run()
        save(args.report,result);print(json.dumps(dict(state=result['state'],searchIndexing='not_verified')));return 0
    except Exception as error:
        code=str(error) if isinstance(error,guard.RecoveryBlocked) and re.fullmatch('[a-zA-Z0-9_]+',str(error)) else 'finalizer_blocked_or_outcome_uncertain'
        result=dict(state='blocked_or_outcome_uncertain',reason=code,searchIndexing='not_verified',liveBrowserPixelsVerified=False,retryAllowed=False)
        if runtime is not None and runtime.adapter is not None:
            a=runtime.adapter;result['executionObservation']=dict(postReservations=a.post_calls,startedWriteReservations=a.start_writes,
                durableStartedCommentId=a.started[0] if a.started else None,responseDiagnostics=a.last_diagnostics,
                requestEvidenceState=runtime.http.request_evidence_state,responseEvidenceState=runtime.http.response_evidence_state)
        save(args.report,result);print(json.dumps(result,sort_keys=True));return 1

if __name__=='__main__': raise SystemExit(main())
