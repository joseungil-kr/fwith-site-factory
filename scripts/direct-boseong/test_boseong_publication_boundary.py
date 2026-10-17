import json
import os
from pathlib import Path
import shutil
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import publication_gate as gate
import publish
import production_output as output

class BoseongBoundaryTests(unittest.TestCase):
    def test_actual_workflow_artifact_check_javascript_with_stubbed_github(self):
        workflow=(HERE.parents[1]/'.github/workflows/boseong-production-publish.yml').read_text()
        lines=workflow.splitlines()
        step=next(i for i,line in enumerate(lines) if line.strip()=='- name: Verify actual successful build and exact retained artifact metadata')
        script_line=next(i for i in range(step,len(lines)) if lines[i].strip()=='script: |')
        js=[]
        for line in lines[script_line+1:]:
            if line.strip() and not line.startswith('            '): break
            js.append(line[12:] if line.startswith('            ') else '')
        script='\n'.join(js).rstrip()
        self.assertIn('Number(desc.buildRunId)',script)
        self.assertIn('Number(desc.artifactId)',script)
        self.assertIn('desc.artifactDigest',script)
        self.assertNotIn('desc.path',script)
        self.assertNotIn('review.qaRunId',script)
        job_if=next(line.strip() for line in lines if line.strip().startswith('if:'))
        self.assertTrue(job_if.startswith('if: github.repository =='))
        self.assertNotIn('false &&',job_if)
        activation=json.loads((HERE/'authorization-binding.json').read_text())
        self.assertEqual(activation['revision'],'9b6ebbdfc44aec9c49058a68df59afa9205460fb')
        descriptor=(HERE/'production-release-review-binding.json').read_text()
        harness=r"""
const fs=require('fs'),assert=require('assert');
const descriptorText=process.env.TEST_DESCRIPTOR;
const script=JSON.parse(process.env.TEST_SCRIPT);
const CONTROL_DIR='control/scripts/direct-boseong';
const originalRead=fs.readFileSync.bind(fs);
fs.readFileSync=(p,...args)=>String(p)===CONTROL_DIR+'/production-release-review-binding.json'?descriptorText:originalRead(p,...args);
const desc=JSON.parse(descriptorText);
const run={id:Number(desc.buildRunId),run_attempt:1,status:'completed',conclusion:'success',event:'issues',head_branch:'main',head_sha:desc.buildControlSha,path:'.github/workflows/boseong-production-build-only.yml',repository:{full_name:'joseungil-kr/fwith-site-factory'},actor:{login:'joseungil-kr'},triggering_actor:{login:'joseungil-kr'}};
function provider(artifact){const calls=[];return {calls,github:{rest:{actions:{getWorkflowRun:async p=>{calls.push(['run',p]);return {data:run}},getArtifact:async p=>{calls.push(['artifact',p]);return {data:artifact}}}}}}}
const processStub={env:{CONTROL_DIR,BUILD_RUN_ID:String(desc.buildRunId),BUILD_ARTIFACT_ID:String(desc.artifactId),REGION:'boseong'}};
const context={repo:{owner:'joseungil-kr',repo:'fwith-site-factory'}};
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
async function execute(artifact){const p=provider(artifact);await new AsyncFunction('process','github','context','require',script)(processStub,p.github,context,require);assert.deepStrictEqual(p.calls,[['run',{owner:'joseungil-kr',repo:'fwith-site-factory',run_id:Number(desc.buildRunId)}],['artifact',{owner:'joseungil-kr',repo:'fwith-site-factory',artifact_id:Number(desc.artifactId)}]]);}
const good={id:Number(desc.artifactId),expired:false,name:'boseong-production-build-'+desc.buildRunId+'-'+desc.buildControlSha,digest:desc.artifactDigest,workflow_run:{id:run.id,head_sha:run.head_sha,head_branch:'main'}};
(async()=>{await execute(good);await assert.rejects(()=>execute({...good,digest:'sha256:wrong'}),/Boseong archive digest mismatch/);console.log('workflow JS descriptor contract passed');})().catch(e=>{console.error(e);process.exitCode=1});
"""
        env=os.environ.copy()
        env.update(TEST_DESCRIPTOR=descriptor,TEST_SCRIPT=json.dumps(script))
        result=subprocess.run(['node','-e',harness],check=True,capture_output=True,text=True,env=env)
        self.assertIn('workflow JS descriptor contract passed',result.stdout)
    def test_fixed_source_and_approved_proof_are_exact(self):
        contract,binding,binding_sha=gate.load()
        self.assertEqual(contract['sourceRevision'],'eb4f931242e7b8f7598cd2fec957b0d988740e7a')
        self.assertEqual(contract['sourceBranch'],'source/boseong-production-preparation-20261017')
        self.assertEqual(binding_sha,'f7c8fd6d4f94bdfe70aaf70822e871219166ed75230bff94eaf940110ec25f9d')
        self.assertEqual(binding['proof']['path'],'/31d1075dc9b5ec84419992fe7a70c660.txt')
        self.assertFalse(json.loads(gate.read(HERE/'production-release/production-contract.json'))['approval']['indexNowSubmissionAuthorized'])

    def test_recovered_review_is_bound_and_limits_are_explicit(self):
        review=publish.release_review()
        self.assertEqual(review['buildRunId'],'38994862258')
        self.assertEqual(review['artifactId'],'12086568586')
        self.assertEqual(review['artifactDigest'],gate.ARTIFACT_DIGEST)
        self.assertFalse(review['publicHttpVerified'])
        self.assertFalse(review['publicationReady'])
        self.assertIn('unavailable',review['recoveryProvenance'])

    def test_recovered_verdict_tamper_fails_closed(self):
        original=gate.read
        def altered(path):
            if Path(path).name=='bounded-VERDICT.json': return b'{}'
            return original(path)
        with patch.object(gate,'read',side_effect=altered),self.assertRaisesRegex(ValueError,'recovered_bounded_verdict_hash_mismatch'):
            publish.release_review()

    def test_authorization_requires_readback_commit_binding(self):
        contract,_,_=gate.load()
        with tempfile.TemporaryDirectory(prefix='boseong-auth-binding-') as tmp:
            root=Path(tmp);scripts=root/'scripts/direct-boseong';docs=root/'docs/direct-boseong'
            scripts.mkdir(parents=True);docs.mkdir(parents=True)
            subprocess.run(['git','init','-q',str(root)],check=True)
            subprocess.run(['git','-C',str(root),'config','user.name','Local Test'],check=True)
            subprocess.run(['git','-C',str(root),'config','user.email','local-test@example.invalid'],check=True)
            auth_path=docs/'production-authorization-20261017.json'
            auth_raw=(json.dumps(gate.authorization_template(contract),ensure_ascii=False,
                sort_keys=True,separators=(',',':'))+'\n').encode()
            auth_path.write_bytes(auth_raw)
            descriptor={'schemaVersion':1,'path':gate.AUTHORIZATION_PATH,'sha256':gate.sha(auth_raw),
                'revision':'0'*40,'publicIssuesApproved':True}
            binding_path=scripts/gate.AUTHORIZATION_BINDING_PATH
            binding_path.write_text(json.dumps(descriptor,sort_keys=True)+'\n')
            subprocess.run(['git','-C',str(root),'add','.'],check=True)
            subprocess.run(['git','-C',str(root),'commit','-qm','save inactive authorization record'],check=True)
            saved_revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
            # The zero placeholder cannot activate; the exact authorization commit must be read back first.
            with patch.object(gate,'DIRECTORY',scripts),self.assertRaisesRegex(ValueError,'publication_authorization_revision_commit_missing'):
                gate.authorization(contract)
            descriptor['revision']=saved_revision
            binding_path.write_text(json.dumps(descriptor,sort_keys=True)+'\n')
            subprocess.run(['git','-C',str(root),'add','.'],check=True)
            subprocess.run(['git','-C',str(root),'commit','-qm','pin read-back authorization commit'],check=True)
            with patch.object(gate,'DIRECTORY',scripts):
                accepted=gate.authorization(contract)
            self.assertEqual(accepted['revision'],saved_revision)
            self.assertTrue(accepted['publicIssuesApproved'])

    def test_other_region_and_nonfixed_targets_rejected(self):
        with self.assertRaisesRegex(ValueError,'fixed_boseong_target_required'):
            with patch.object(publish,'WORKER','other-worker'):
                publish.validate_fixed_target()
        with self.assertRaisesRegex(ValueError,'publication_config_identity'):
            with patch.object(gate,'read',return_value=b'{"mode":"publish-and-verify-only"}'):
                publish.publication_config()

    def test_provider_transport_allows_only_read_methods_before_attach(self):
        with patch.dict(os.environ,{'CLOUDFLARE_ACCOUNT_ID':'a'*32,'CLOUDFLARE_API_TOKEN':'dummy-test-token'}):
            account,transport=publish.provider_transport()
            prefix='/accounts/'+account
            for method,path,body in [('POST',prefix,None),('GET',prefix+'/workers/scripts/extra',None),('PUT',prefix+'/workers/scripts/other/domains/records',{})]:
                with self.subTest(method=method,path=path),self.assertRaisesRegex(ValueError,'provider_operation_forbidden'):
                    transport(method,path,body)

    def test_output_projection_uses_pinned_source_adapter(self):
        from unittest.mock import patch
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            source_checkout=Path(tmp)/'source'
            fake={'files':{'index.html':'a'*64,'404.html':'b'*64}}
            with patch.dict(os.environ,{'BOSEONG_SOURCE_CHECKOUT':str(source_checkout)}), patch.object(output.adapter,'validate',return_value=fake) as validate:
                result=output.inspect_dist(Path(tmp)/'dist',dict(mode='production',indexable=True,origin=output.ORIGIN,revision=gate.SOURCE),output.PROOF)
            validate.assert_called_once_with(source_checkout/'site-factory/boseong-flower',Path(tmp)/'dist',gate.SOURCE)
            self.assertEqual(result['sitemapUrls'],[output.ORIGIN+'/'])
            self.assertEqual(result['files'],fake['files'])

    def test_workflow_disallows_reruns_and_indexnow_submission(self):
        workflow=(HERE.parents[1]/'.github/workflows/boseong-production-publish.yml').read_text()
        self.assertIn('github.run_attempt == 1',workflow)
        self.assertIn('cancel-in-progress: false',workflow)
        group_line=next(line for line in workflow.splitlines() if line.strip().startswith('group:'))
        for predicate in ["github.event_name == 'issues'", "github.event.action == 'opened'",
            "github.repository == 'joseungil-kr/fwith-site-factory'", "github.ref == 'refs/heads/main'",
            "github.event.issue.title == '[BOSEONG-PRODUCTION-PUBLISH] 20261017'",
            "github.event.issue.user.login == 'joseungil-kr'", "github.actor == 'joseungil-kr'",
            "github.triggering_actor == 'joseungil-kr'"]:
            self.assertIn(predicate,group_line)
        self.assertIn("'boseong-direct-public-release'",group_line)
        self.assertIn("format('boseong-irrelevant-run-{0}', github.run_id)",group_line)
        def modeled_group(event):
            eligible=(event.get('event_name')=='issues' and event.get('action')=='opened'
                and event.get('repository')=='joseungil-kr/fwith-site-factory' and event.get('ref')=='refs/heads/main'
                and event.get('issue_title')=='[BOSEONG-PRODUCTION-PUBLISH] 20261017'
                and event.get('issue_user')=='joseungil-kr' and event.get('actor')=='joseungil-kr'
                and event.get('triggering_actor')=='joseungil-kr')
            return 'boseong-direct-public-release' if eligible else 'boseong-irrelevant-run-'+str(event['run_id'])
        eligible=dict(event_name='issues',action='opened',repository='joseungil-kr/fwith-site-factory',
            ref='refs/heads/main',issue_title='[BOSEONG-PRODUCTION-PUBLISH] 20261017',issue_user='joseungil-kr',
            actor='joseungil-kr',triggering_actor='joseungil-kr')
        first=dict(eligible,issue_number=41,run_id=101);second=dict(eligible,issue_number=42,run_id=102)
        unrelated_a=dict(event_name='push',run_id=201);unrelated_b=dict(event_name='schedule',run_id=202)
        self.assertEqual(modeled_group(first),modeled_group(second))
        self.assertNotEqual(modeled_group(unrelated_a),modeled_group(unrelated_b))
        publish_block=workflow.split('\njobs:\n  publish:\n',1)[1].split('\n    runs-on:',1)[0]
        publish_condition=next(line.strip() for line in publish_block.splitlines() if line.strip().startswith('if:'))
        for guard in ["github.repository == 'joseungil-kr/fwith-site-factory'","github.ref == 'refs/heads/main'",
            "github.event.issue.title == '[BOSEONG-PRODUCTION-PUBLISH] 20261017'","github.actor == 'joseungil-kr'",
            "github.triggering_actor == 'joseungil-kr'",'github.run_attempt == 1',"github.event.issue.user.login == 'joseungil-kr'"]:
            self.assertIn(guard,publish_condition)
        self.assertNotIn('false &&',publish_condition)
        saved=json.loads((HERE/'authorization-binding.json').read_text())
        self.assertEqual(saved['revision'],'9b6ebbdfc44aec9c49058a68df59afa9205460fb')
        self.assertTrue(saved['publicIssuesApproved'])
        self.assertNotIn('indexnow-submit',workflow)
        self.assertIn('override_existing_dns_record=False', (HERE/'publish.py').read_text())

    def test_fake_credentialed_workflow_runtime_never_runs_source_adapter(self):
        """Exercise preflight, one fixed attach, and readback with an in-memory provider."""
        original_cwd=Path.cwd()
        source_dist=Path(os.environ.get('BOSEONG_TEST_DIST',''))
        workspace=original_cwd
        report_path=workspace/'artifact-check.json'
        release_source=source_dist.parent if source_dist else workspace/'release'
        if not report_path.is_file() or not (release_source/'release.json').is_file() or not (release_source/'dist').is_dir():
            self.skipTest('workflow artifact attestation and retained release are not staged')

        attestation=json.loads(report_path.read_text())
        expected_revision='eb4f931242e7b8f7598cd2fec957b0d988740e7a'
        self.assertEqual(attestation['sourceRevision'],expected_revision)
        with tempfile.TemporaryDirectory(prefix='boseong-mocked-provider-') as tmp:
            root=Path(tmp)
            shutil.copytree(release_source,root/'release')
            shutil.copy2(report_path,root/'artifact-check.json')
            (root/'event.json').write_text('{}')
            account='a'*32
            state={'worker':False,'domains':[]}
            calls=[]

            class Response:
                status=200
                def __init__(self,value): self.raw=json.dumps(value).encode()
                def __enter__(self): return self
                def __exit__(self,*args): return False
                def read(self,limit=-1): return self.raw if limit<0 else self.raw[:limit]

            class Opener:
                def open(self,request,timeout=None):
                    method=request.get_method()
                    from urllib.parse import urlsplit
                    path=urlsplit(request.full_url).path
                    calls.append((method,path,request.data))
                    if method=='GET' and path.endswith('/workers/scripts'):
                        result=[{'id':publish.WORKER}] if state['worker'] else []
                    elif method=='GET' and path.endswith('/workers/domains'):
                        result=list(state['domains'])
                    elif method=='GET' and path=='/client/v4/accounts/'+account:
                        result={'id':account}
                    elif method=='PUT':
                        body=json.loads(request.data)
                        self_body=dict(override_scope=False,override_existing_origin=False,
                            override_existing_dns_record=False,
                            origins=[dict(hostname=publish.HOSTNAME,zone_name='fwith.kr')])
                        if body != self_body: raise AssertionError('unexpected provider write body')
                        state['domains']=[dict(hostname=publish.HOSTNAME,service=publish.WORKER,
                            environment='production',zone_name='fwith.kr',enabled=True,previews_enabled=False)]
                        result={'hostname':publish.HOSTNAME,'service':publish.WORKER}
                    else:
                        raise AssertionError('unexpected provider request: '+method+' '+path)
                    return Response(dict(success=True,errors=[],result=result))

            class Native:
                def attach(self,transport,account_id):
                    return transport('PUT','/accounts/'+account_id+'/workers/scripts/'+publish.WORKER+'/domains/records',
                        dict(override_scope=False,override_existing_origin=False,override_existing_dns_record=False,
                             origins=[dict(hostname=publish.HOSTNAME,zone_name='fwith.kr')]))

            def single_page(transport,path): return transport('GET',path)['result']
            env={'REVISION':expected_revision,'GITHUB_EVENT_PATH':str(root/'event.json'),
                'CLOUDFLARE_ACCOUNT_ID':account,'CLOUDFLARE_API_TOKEN':'dummy-test-token'}
            if attestation.get('publisherControlRevision') is not None:
                env['GITHUB_SHA']=attestation['publisherControlRevision']
            if attestation.get('publisherRunId') is not None:
                env['GITHUB_RUN_ID']=str(attestation['publisherRunId'])

            old_argv=sys.argv[:]
            try:
                os.chdir(root)
                with patch.dict(os.environ,env,clear=True), \
                     patch.object(publish.gate,'trusted_control',return_value={'controlCheckoutVerified':True}), \
                     patch.object(publish,'authorize',return_value={'state':'exact_test_request'}), \
                     patch.object(publish,'helpers',return_value=(Native(),single_page)), \
                     patch.object(publish,'build_opener',return_value=Opener()), \
                     patch.object(publish.output.adapter,'validate',side_effect=AssertionError('source adapter must not run with provider credentials')) as source_validate:
                    def run(mode,report):
                        sys.argv=['publish.py',mode,'--report',report]
                        self.assertEqual(publish.main(),0)
                        return json.loads(Path(report).read_text())

                    preflight=run('preflight','binding-before.json')
                    self.assertEqual(preflight['state'],'target_absent_verified')
                    self.assertFalse(preflight['mutationsPerformed'])
                    state['worker']=True  # Represents the separately successful, one-time retained asset upload.
                    attached=run('attach','domain-attach.json')
                    self.assertEqual(attached['state'],'attach_request_accepted')
                    self.assertTrue(attached['mutationsPerformed'])
                    readback=run('readback','binding-after.json')
                    self.assertEqual(readback['state'],'binding_verified')
                    self.assertTrue(readback['hostnameBindingExists'])
                    self.assertEqual(readback['dnsState'],'dns_records_not_checked')
                    puts=[call for call in calls if call[0]=='PUT']
                    self.assertEqual(len(puts),1)
                    self.assertTrue(all(call[0]=='GET' for call in calls[:calls.index(puts[0])]))
                    self.assertFalse(json.loads(puts[0][2])['override_existing_dns_record'])
                    source_validate.assert_not_called()
            finally:
                sys.argv=old_argv
                os.chdir(original_cwd)

    def test_cold_checkout_restores_private11_before_artifact_validation(self):
        """Recreate the ignored private dist from retained bytes on a checkout with no dist."""
        original_cwd=Path.cwd()
        source_checkout=Path(os.environ.get('BOSEONG_SOURCE_CHECKOUT',''))
        source_root=source_checkout/'site-factory/boseong-flower'
        source_dist=Path(os.environ.get('BOSEONG_TEST_DIST',''))
        release_source=source_dist.parent if source_dist else Path.cwd()/'release'
        if not source_root.is_dir() or not release_source.joinpath('release.json').is_file():
            self.skipTest('source checkout and retained release are not staged')
        contract=output.adapter.read_contract()
        with tempfile.TemporaryDirectory(prefix='boseong-cold-checkout-') as tmp:
            root=Path(tmp)
            cold_checkout=root/'checkout'
            cold_source=cold_checkout/'site-factory/boseong-flower'
            def ignore(path,names):
                return {name for name in names if Path(path).name=='candidate' and name in {'dist','node_modules','.astro','evidence'}}
            shutil.copytree(source_root,cold_source,ignore=ignore)
            self.assertFalse((cold_source/'candidate/dist').exists())
            retained=root/'release'
            shutil.copytree(release_source,retained)
            event_path=root/'event.json';event_path.write_text('{}')
            env={'REVISION':'eb4f931242e7b8f7598cd2fec957b0d988740e7a',
                'BOSEONG_SOURCE_CHECKOUT':str(cold_checkout),'GITHUB_EVENT_PATH':str(event_path)}
            old_argv=sys.argv[:]
            try:
                os.chdir(root)
                with patch.dict(os.environ,env,clear=True), \
                     patch.object(publish.gate,'trusted_control',return_value={'controlCheckoutVerified':True}), \
                     patch.object(publish,'authorize',return_value={'state':'exact_test_request'}), \
                     patch.object(publish.output.adapter,'validate',side_effect=AssertionError('no source build/validator execution during restore')) as validate:
                    sys.argv=['publish.py','restore-input','--report','private-input-check.json']
                    self.assertEqual(publish.main(),0)
                    result=json.loads(Path('private-input-check.json').read_text())
                    self.assertEqual(result['state'],'exact_private_inputs_restored_from_retained_artifact')
                    self.assertEqual(result['sourceFilesVerified'],46)
                    self.assertEqual(result['privateFilesVerified'],11)
                    self.assertFalse(result['sourceCodeExecuted'])
                    observed=output.adapter.inventory(cold_source/'candidate/dist')
                    self.assertEqual({name:{'bytes':len(raw),'sha256':publish.sha(raw)} for name,raw in observed.items()},contract['privateOutputs'])
                    validate.assert_not_called()
            finally:
                sys.argv=old_argv
                os.chdir(original_cwd)
            old_cwd=Path.cwd()
            try:
                os.chdir(root)
                with patch.dict(os.environ,{'REVISION':'eb4f931242e7b8f7598cd2fec957b0d988740e7a',
                    'BOSEONG_SOURCE_CHECKOUT':str(cold_checkout)},clear=True):
                    attestation=publish.artifact()
                    publish.save(root/'artifact-check.json',attestation)
                credentialed_env={'REVISION':'eb4f931242e7b8f7598cd2fec957b0d988740e7a',
                    'BOSEONG_SOURCE_CHECKOUT':str(cold_checkout),'CLOUDFLARE_ACCOUNT_ID':'a'*32,
                    'CLOUDFLARE_API_TOKEN':'dummy-test-token'}
                with patch.dict(os.environ,credentialed_env,clear=True), \
                     patch.object(publish.output.adapter,'validate',side_effect=AssertionError('credentialed phase must reuse attestation')) as credentialed_validate:
                    reused=publish.require_artifact_validation()
                self.assertEqual(reused['state'],'secret_free_artifact_validation_reused')
                credentialed_validate.assert_not_called()
            finally:
                os.chdir(old_cwd)

if __name__=='__main__': unittest.main()
