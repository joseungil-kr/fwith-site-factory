"""Local synthetic-envelope tests; no approval, API read or artifact provenance claim."""
import copy
import json
from pathlib import Path
import unittest
import shutil
import tempfile
import os
import subprocess
import shlex
from unittest.mock import patch
import recovery_build as q

def env():
    return dict(GITHUB_REPOSITORY=q.REPOSITORY, GITHUB_REF='refs/heads/main',
                GITHUB_ACTOR=q.OWNER, GITHUB_TRIGGERING_ACTOR=q.OWNER,
                GITHUB_RUN_ATTEMPT='1', GITHUB_EVENT_NAME='issues', GITHUB_RUN_ID='123', GITHUB_SHA='a'*40)

def event():
    e=env()
    body=dict(schemaVersion=1, mode='damyang-proof-recovery-build-only', source_branch=q.BRANCH,
              source_revision=q.REVISION, source_tree=q.TREE, expected_control_revision=e['GITHUB_SHA'],
              source_manifest_sha256=q.source_contract()['sourceManifestSha256'], binding_sha256='b'*64)
    return dict(action='opened', repository=dict(full_name=q.REPOSITORY,owner=dict(login=q.OWNER,type='User')),
                issue=dict(title=q.TITLE,user=dict(login=q.OWNER),body=json.dumps(body)))

def manifest():
    return dict(sourceRevision=q.REVISION,sourceTree=q.TREE,runId='123',runAttempt=1,
                controlRevision='a'*40,artifactName='damyang-proof-recovery-build-123-'+'a'*40,
                sourceContract=q.source_contract(),publicationReady=False,independentArtifactReviewRequired=True)

def artifact_inputs():
    m=manifest();raw=b'synthetic archive fixture; never actual artifact'
    run=dict(repository={'full_name':q.REPOSITORY},head_branch='main',head_sha=m['controlRevision'],id=123,
             event='issues',run_attempt=1,actor={'login':q.OWNER},triggering_actor={'login':q.OWNER},
             path=q.WORKFLOW,status='completed',conclusion='success')
    artifact=dict(id=1234,expired=False,name=m['artifactName'],digest='sha256:'+q.sha(raw),
                  workflow_run={'id':123,'head_sha':m['controlRevision']})
    return run,artifact,raw,m

class RecoveryBuildTests(unittest.TestCase):
    def test_source_contract_exact81_and_git_tree(self):
        c=q.source_contract();self.assertEqual((c['sourceFiles'],c['privateFiles'],c['adapterFiles']),(81,65,16));self.assertEqual(c['sourceTree'],q.TREE)

    def test_null_activation_is_not_approval(self):
        with patch.object(q,'read',return_value=b'{"state":"LOCAL_PREPARATION_ONLY"}'):
            with self.assertRaisesRegex(ValueError,'recovery_build_not_activated'):
                q.activation(q.DIRECTORY.parents[1])

    def test_control_checkout_must_be_real(self):
        with patch.object(q,'git',return_value=b'wrong\n'):
            with self.assertRaisesRegex(ValueError,'actual_control_checkout_required'):q.trusted_control(env())

    def test_exact_closed_request(self):
        result=q.request(env(),event(),'b'*64);self.assertEqual(result['source_revision'],q.REVISION)

    def test_request_rejects_field_mutations(self):
        for key in json.loads(event()['issue']['body']):
            with self.subTest(key=key):
                d=event();body=json.loads(d['issue']['body']);body[key]=None;d['issue']['body']=json.dumps(body)
                with self.assertRaises(ValueError):q.request(env(),d,'b'*64)

    def test_request_rejects_extra_field(self):
        d=event();body=json.loads(d['issue']['body']);body['publish']=True;d['issue']['body']=json.dumps(body)
        with self.assertRaises(ValueError):q.request(env(),d,'b'*64)

    def test_request_rejects_duplicate_field(self):
        d=event();d['issue']['body']=d['issue']['body'].replace('"schemaVersion": 1','"schemaVersion": 1, "schemaVersion": 1')
        with self.assertRaisesRegex(ValueError,'duplicate_request_key_forbidden'):q.request(env(),d,'b'*64)

    def test_pending_artifact_review_is_not_acceptance(self):
        raw=q.read(q.DIRECTORY/'artifact-review-pending.json')
        for digest in [None,'',q.sha(raw)]:
            with self.assertRaises((ValueError,KeyError)):
                q.verify_independent_review(raw,digest,manifest(),{'artifactId':1234,'archiveSha256':'e'*64},{'sourceRevision':q.REVISION,'files':{}})

    def test_request_rejects_old_title(self):
        d=event();d['issue']['title']='[DAMYANG-PRODUCTION-BUILD] 20261016'
        with self.assertRaises(ValueError):q.request(env(),d,'b'*64)

    def test_request_rejects_wrong_issue_owner(self):
        d=event();d['issue']['user']['login']='someone'
        with self.assertRaises(ValueError):q.request(env(),d,'b'*64)

    def test_request_rejects_repo_type_or_name(self):
        for kind in ['Organization',None]:
            d=event();d['repository']['owner']['type']=kind
            with self.assertRaises(ValueError):q.request(env(),d,'b'*64)

    def test_closed_environment_mutations(self):
        for key in env():
            with self.subTest(key=key):
                e=env();e[key]='wrong'
                with self.assertRaises(ValueError):q.owner_context(e)

    def test_second_attempt_and_unknown_run_rejected(self):
        for key,value in [('GITHUB_RUN_ATTEMPT','2'),('GITHUB_RUN_ID','0'),('GITHUB_RUN_ID','123.0'),('GITHUB_SHA','local-inspection')]:
            e=env();e[key]=value
            with self.assertRaises(ValueError):q.owner_context(e)

    def test_provider_credential_boundary(self):
        for key in ['CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID','CF_API_KEY','AWS_ACCESS_KEY_ID','AZURE_CLIENT_SECRET','GOOGLE_APPLICATION_CREDENTIALS','PROVIDER_TOKEN']:
            e=env();e[key]='synthetic-not-secret'
            with self.assertRaisesRegex(ValueError,'provider_credentials_forbidden'):q.owner_context(e)

    def test_synthetic_identity_never_approves_publication(self):
        result=q.verify_artifact_identity(*artifact_inputs())
        self.assertFalse(result['publicationReady']);self.assertIn('REVIEW_STILL_REQUIRED',result['state'])

    def test_artifact_metadata_mutations(self):
        for key,value in [('id',None),('id',True),('expired',True),('expired',None),('name','old-artifact'),('digest',None),('digest','sha256:'+'0'*64),('workflow_run',{})]:
            with self.subTest(key=key,value=value):
                r,a,z,m=artifact_inputs();a[key]=value
                with self.assertRaises((ValueError,KeyError)):q.verify_artifact_identity(r,a,z,m)

    def test_run_metadata_mutations(self):
        for key,value in [('repository',{}),('head_branch','source/x'),('head_sha','b'*40),('id',124),('event','workflow_dispatch'),('run_attempt',2),('run_attempt',True),('actor',{}),('triggering_actor',{}),('path','other.yml'),('status','in_progress'),('conclusion','failure')]:
            with self.subTest(key=key):
                r,a,z,m=artifact_inputs();r[key]=value
                with self.assertRaises(ValueError):q.verify_artifact_identity(r,a,z,m)

    def test_manifest_identity_mutations(self):
        for key,value in [('sourceRevision',q.ORIGINAL),('sourceTree','0'*40),('runAttempt',2),('sourceContract',{}),('publicationReady',True),('independentArtifactReviewRequired',False),('artifactName','anything'),('controlRevision',None),('runId','0')]:
            with self.subTest(key=key):
                r,a,z,m=artifact_inputs();m[key]=value
                with self.assertRaises((ValueError,TypeError)):q.verify_artifact_identity(r,a,z,m)

    def test_archive_bytes_changed(self):
        r,a,z,m=artifact_inputs()
        with self.assertRaises(ValueError):q.verify_artifact_identity(r,a,z+b'x',m)

    def test_safe_paths(self):
        for value in ['../escape','/tmp/escape','x/../../escape','x//y','x\\y','.hidden/x']:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):q.regular_under(q.DIRECTORY,value)

    def test_active_payload_only(self):
        p=q.output.indexnow_payload([q.ORIGIN+'/']);self.assertEqual(p['keyLocation'],q.ORIGIN+q.output.PROOF['path'])
        with self.assertRaises(AssertionError):q.output.indexnow_payload([q.ORIGIN+'/'],q.output.LEGACY_PROOF)


class ClosedActivationTests(unittest.TestCase):
    """Synthetic only: git ancestry is mocked; these tests cannot grant approval."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'control'
        realroot = q.DIRECTORY.parents[1]
        self.root.mkdir()
        for name in q.REVIEWED_CONTROL_PATHS:
            target = self.root / name; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(realroot / name, target)
        self.directory = self.root / 'scripts/direct-damyang-recovery'
        auth = self.root / 'docs/direct-damyang/production-authorization-20261016.json'
        auth.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(q.DIRECTORY / 'original-production-authorization.json', auth)
        self.review = dict(schemaVersion=1, verdict='ACCEPT_BUILD_ONLY_RECOVERY_CONTROLS',
                           sourceRevision=q.REVISION, controlFiles=[
            dict(path=name, sha256=q.sha((self.root/name).read_bytes()), bytes=(self.root/name).stat().st_size)
            for name in sorted(q.REVIEWED_CONTROL_PATHS)])
        self.a = json.loads((q.DIRECTORY/'build-activation.json').read_bytes())
        self.a.update(state='INDEPENDENT_CONTROL_REVIEW_ACCEPTED',
                      independentControlReview=dict(path=q.CONTROL_REVIEW_PATH, sha256='0'*64),
                      authorizationRevisions=dict(production='a'*40, recovery='b'*40))
        self.addCleanup(patch.stopall)
        patch.object(q, 'DIRECTORY', self.directory).start()
        def git(root, *args):
            if args[0] == 'show': return (self.root / args[1].split(':',1)[1]).read_bytes()
            if args[0] == 'merge-base': return b''
            raise AssertionError('unexpected synthetic git operation')
        patch.object(q, 'git', side_effect=git).start()

    def write(self):
        raw=q.canonical(self.review); path=self.root/q.CONTROL_REVIEW_PATH
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        self.a['independentControlReview']['sha256']=q.sha(raw)
        (self.directory/'build-activation.json').write_bytes(q.canonical(self.a))

    def test_full_synthetic_inventory_accepted_only_as_structure(self):
        self.write();a=q.activation(self.root)
        self.assertFalse(a['publicationReady']);self.assertIsNone(a['actualControlRevision'])
        self.assertEqual(len(self.review['controlFiles']),30)

    def test_every_missing_reviewed_file_rejected(self):
        original=copy.deepcopy(self.review)
        for i,row in enumerate(original['controlFiles']):
            with self.subTest(path=row['path']):
                self.review=copy.deepcopy(original);self.review['controlFiles'].pop(i);self.write()
                with self.assertRaisesRegex(ValueError,'exact_reviewed_control_scope_required'):q.activation(self.root)

    def test_each_reviewed_file_byte_change_rejected(self):
        for row in self.review['controlFiles']:
            path=self.root/row['path'];raw=path.read_bytes();self.write();path.write_bytes(raw+b' ')
            with self.subTest(path=row['path']),self.assertRaisesRegex(ValueError,'reviewed_control_file_changed'):q.activation(self.root)
            path.write_bytes(raw)

    def test_review_paths_duplicate_extra_alias_rejected(self):
        original=copy.deepcopy(self.review)
        for name in ['../escape','/tmp/escape','scripts//x','scripts/x/../recovery_build.py','unreviewed.py',original['controlFiles'][1]['path']]:
            self.review=copy.deepcopy(original);self.review['controlFiles'][0]['path']=name;self.write()
            with self.subTest(path=name),self.assertRaises(ValueError):q.activation(self.root)
        self.review=copy.deepcopy(original);self.review['controlFiles'].append(copy.deepcopy(original['controlFiles'][0]));self.write()
        with self.assertRaises(ValueError):q.activation(self.root)

    def test_review_rows_closed_types(self):
        original=copy.deepcopy(self.review)
        for key,value in [('path',False),('bytes',True),('bytes',0),('bytes','1'),('sha256',None),('sha256','x'),('extra',True)]:
            self.review=copy.deepcopy(original);self.review['controlFiles'][0][key]=value;self.write()
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):q.activation(self.root)

    def test_closed_activation_schema_and_unobserved_identity(self):
        original=copy.deepcopy(self.a)
        variants=[('schemaVersion',True),('schemaVersion',2),('sourceRevision',q.ORIGINAL),('publicationReady',True),('publicationReady',0),('extra',True),('actualControlRevision','invented'),('actualBuildRunId',999),('actualArtifactId',888),('actualArtifactDigest','sha256:'+'0'*64)]
        for key,value in variants:
            self.a=copy.deepcopy(original);self.a[key]=value;self.write()
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):q.activation(self.root)
        for key in original:
            self.a=copy.deepcopy(original);self.write();obj=json.loads((self.directory/'build-activation.json').read_bytes());obj.pop(key);(self.directory/'build-activation.json').write_bytes(q.canonical(obj))
            with self.subTest(missing=key),self.assertRaises(ValueError):q.activation(self.root)

    def test_closed_review_schema(self):
        original=copy.deepcopy(self.review)
        for key,value in [('schemaVersion',True),('schemaVersion',2),('verdict','PASS'),('sourceRevision',q.ORIGINAL),('controlFiles',{}),('extra',True)]:
            self.review=copy.deepcopy(original);self.review[key]=value;self.write()
            with self.subTest(key=key),self.assertRaises(ValueError):q.activation(self.root)

    def test_closed_review_descriptor_and_exact_path(self):
        self.write();original=copy.deepcopy(self.a)
        for key,value in [('path','docs/other.json'),('sha256','x'),('sha256',None),('extra',True)]:
            self.a=copy.deepcopy(original);self.a['independentControlReview'][key]=value
            (self.directory/'build-activation.json').write_bytes(q.canonical(self.a))
            with self.subTest(key=key),self.assertRaises(ValueError):q.activation(self.root)

    def test_closed_authorization_revisions(self):
        original=copy.deepcopy(self.a)
        for value in [None,{},dict(production='a'*40),dict(production='a'*40,recovery=None),dict(production='a'*40,recovery='b'*40,other='c'*40)]:
            self.a=copy.deepcopy(original);self.a['authorizationRevisions']=value;self.write()
            with self.subTest(value=value),self.assertRaises(ValueError):q.activation(self.root)

    def test_activation_and_review_duplicate_or_nonfinite_json(self):
        self.write();ap=self.directory/'build-activation.json';rp=self.root/q.CONTROL_REVIEW_PATH
        araw=ap.read_bytes();rraw=rp.read_bytes()
        for target,raw in [(ap,araw),(rp,rraw)]:
            for payload in [raw.replace(b'"schemaVersion":1',b'"schemaVersion":0,"schemaVersion":1'),raw.replace(b'"schemaVersion":1',b'"schemaVersion":NaN')]:
                ap.write_bytes(araw);rp.write_bytes(rraw);target.write_bytes(payload)
                if target==rp:
                    obj=json.loads(araw);obj['independentControlReview']['sha256']=q.sha(payload);ap.write_bytes(q.canonical(obj))
                with self.subTest(target=target.name,payload=payload[:20]),self.assertRaises(ValueError):q.activation(self.root)

    def test_intermediate_reviewed_symlink_rejected(self):
        self.write();target=self.root/'docs/direct-damyang-recovery/prior-publication';renamed=self.root/'relocated';target.rename(renamed);target.symlink_to(renamed,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'reviewed_path_unsafe'):q.activation(self.root)


class TrustedWorkflowEnvironmentTests(unittest.TestCase):
    """Real local shell env-i boundary; invented sentinels, no provider/network."""
    COMMON = {'PATH','HOME','LANG','PYTHONDONTWRITEBYTECODE','GITHUB_REPOSITORY','GITHUB_REF',
              'GITHUB_ACTOR','GITHUB_TRIGGERING_ACTOR','GITHUB_RUN_ATTEMPT','GITHUB_EVENT_NAME',
              'GITHUB_RUN_ID','GITHUB_SHA','GITHUB_WORKSPACE'}
    def prefix(self, phase):
        lines=(q.DIRECTORY.parents[1]/q.WORKFLOW).read_text().splitlines(True)
        matches=[i for i,line in enumerate(lines) if 'python3 control/scripts/direct-damyang-recovery/recovery_build.py '+phase+' ' in line]
        self.assertEqual(len(matches),1);end=matches[0];start=end-1
        while start>=0 and lines[start].strip()!='run: |':start-=1
        self.assertGreaterEqual(start,0)
        text=''.join(line[10:] for line in lines[start+1:end]);self.assertTrue(text.startswith('env -i '))
        return text
    def parent(self):
        return {**os.environ,**env(),'PATH':os.environ['PATH'],'HOME':os.environ.get('HOME','/tmp'),
                'GITHUB_WORKSPACE':'/tmp/synthetic workspace with spaces',
                'GITHUB_EVENT_PATH':'/tmp/synthetic event with spaces.json','GITHUB_OUTPUT':'/tmp/synthetic output',
                'NATIVE_GATES_PASSED':'true','AZURE_SYNTHETIC_METADATA':'not-a-credential',
                'AWS_SYNTHETIC_METADATA':'not-a-credential','SYNTHETIC_PROVIDER_LABEL':'not-a-credential',
                'CLOUDFLARE_API_TOKEN':'INVENTED_SENTINEL','GH_TOKEN':'INVENTED_SENTINEL',
                'GITHUB_TOKEN':'INVENTED_SENTINEL','ACTIONS_RUNTIME_TOKEN':'INVENTED_SENTINEL'}
    def run_child(self,phase,parent=None,extra=''):
        code="import os,json,sys;sys.path.insert(0,"+repr(str(q.DIRECTORY))+ ");import recovery_build as q;q.owner_context(os.environ);print(json.dumps(sorted(os.environ)))"
        command=self.prefix(phase)+extra+'python3 -c '+shlex.quote(code)
        return subprocess.run(['/bin/bash','-eu','-c',command],env=parent or self.parent(),text=True,capture_output=True)
    def test_parent_metadata_fixture_reproduces_unchanged_sentinel(self):
        for name in ['AZURE_SYNTHETIC_METADATA','AWS_SYNTHETIC_METADATA','SYNTHETIC_PROVIDER_LABEL']:
            e=env();e[name]='synthetic-noncredential'
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'provider_credentials_forbidden'):q.owner_context(e)
    def test_three_actual_workflow_prefixes_forward_exact_minimum_names(self):
        for phase in ['select','prebuild','postbuild']:
            result=self.run_child(phase);self.assertEqual(result.returncode,0,result.stderr)
            expected=self.COMMON|({'GITHUB_EVENT_PATH','GITHUB_OUTPUT'} if phase=='select' else set())|({'NATIVE_GATES_PASSED'} if phase=='postbuild' else set())
            with self.subTest(phase=phase):self.assertEqual(set(json.loads(result.stdout)),expected)
            self.assertNotIn('INVENTED_SENTINEL',result.stdout+result.stderr)
    def test_child_injected_credentials_still_rejected(self):
        for phase in ['select','prebuild','postbuild']:
            for name in ['CLOUDFLARE_API_TOKEN','CF_API_KEY','AWS_ACCESS_KEY_ID','AZURE_CLIENT_SECRET','GOOGLE_APPLICATION_CREDENTIALS','PROVIDER_TOKEN']:
                result=self.run_child(phase,extra=name+'=INVENTED_SENTINEL ')
                with self.subTest(phase=phase,name=name):self.assertNotEqual(result.returncode,0);self.assertIn('provider_credentials_forbidden',result.stderr);self.assertNotIn('INVENTED_SENTINEL',result.stdout+result.stderr)
    def test_owner_main_attempt_identity_not_bypassed_by_cleaning(self):
        for key in env():
            parent=self.parent();parent[key]='wrong';result=self.run_child('select',parent)
            with self.subTest(key=key):self.assertNotEqual(result.returncode,0)
    def test_shell_quoted_paths_do_not_execute_parent_values(self):
        parent=self.parent();parent['GITHUB_WORKSPACE']='/tmp/space ; $(exit 99) " unicode 경로'
        result=self.run_child('prebuild',parent);self.assertEqual(result.returncode,0,result.stderr)
    def test_unittest_step_only_forwards_four_process_variables(self):
        lines=(q.DIRECTORY.parents[1]/q.WORKFLOW).read_text().splitlines(True)
        matches=[i for i,line in enumerate(lines) if "python3 -m unittest discover -s control/scripts/direct-damyang-recovery -p 'test_recovery_build.py' -v" in line]
        self.assertEqual(len(matches),1);end=matches[0];self.assertEqual(lines[end-2].strip(),'run: |')
        prefix=lines[end-1][10:];self.assertTrue(prefix.startswith('env -i '))
        code='import os,json;print(json.dumps(sorted(os.environ)))'
        result=subprocess.run(['/bin/bash','-eu','-c',prefix+'python3 -c '+shlex.quote(code)],env=self.parent(),capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(set(json.loads(result.stdout)),{'PATH','HOME','LANG','PYTHONDONTWRITEBYTECODE'})

    def test_credential_guard_code_stays_exact_reviewed_bytes(self):
        # Entire runtime module remains R3 byte-identical; only workflow/tests/review binding change.
        self.assertEqual(q.sha(q.read(q.DIRECTORY/'recovery_build.py')),'5a1c4b9d7ec6ca79caf36688c183935af77694d572bf63201d3a028b2beb5da5')

if __name__=='__main__':
    unittest.main()
