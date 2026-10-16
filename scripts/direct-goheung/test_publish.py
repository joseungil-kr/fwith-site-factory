"""Offline publisher tests. Fixture IDs and responses are never live evidence."""
import contextlib
import copy
from email.message import Message
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import publish as p
import shutil


@contextlib.contextmanager
def working(path):
    previous=Path.cwd();os.chdir(path)
    try: yield
    finally: os.chdir(previous)


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        # Actual saved production15 is read-only input. Review/run IDs below are synthetic.
        self.original=p.DIRECTORY
        self.input_dist=Path(os.environ['GOHEUNG_TEST_DIST']).resolve()
        self.stack.enter_context(patch.object(socket,'create_connection',side_effect=AssertionError('network_forbidden_in_unit_tests')))
        self.stack.enter_context(patch.dict(os.environ,{'REVISION':p.gate.SOURCE}))
        self.root=Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.d=self.root/'scripts/direct-goheung';self.d.mkdir(parents=True)
        for name in ['production-source-contract.json']:(self.d/name).write_bytes((self.original/name).read_bytes())
        shutil.copytree(self.original/'production-qa',self.d/'production-qa')
        self.stack.enter_context(patch.object(p,'DIRECTORY',self.d))
        self.stack.enter_context(patch.object(p.gate,'DIRECTORY',self.d))
        self.c,self.b,_=p.gate.inputs()
        self.docs=self.root/'docs/direct-goheung';self.docs.mkdir(parents=True,exist_ok=True)
        auth=self.docs/'production-authorization-20261016.json';p.save(auth,p.gate.authorization_template(self.c))
        p.save(self.d/'authorization-binding.json',dict(schemaVersion=1,path=auth.relative_to(self.root).as_posix(),sha256=p.sha(auth.read_bytes()),revision='a'*40,publicIssuesApproved=True))
        self.config=dict(schemaVersion=1,repository=p.REPOSITORY,hostname=p.HOSTNAME,worker=p.WORKER,
                         mode='publish-and-verify-only',indexNowSubmissionEnabled=False)
        p.save(self.d/'production-publication.json',self.config)
        self.docs=self.root/'docs/direct-goheung';self.docs.mkdir(parents=True,exist_ok=True)
        self.review=dict(schemaVersion=1,region='goheung',sourceCommit=self.c['sourceRevision'],
            bindingSha256=p.gate.load()[2],sourceContractSha256=self.b['sourceContractSha256'],
            allRouteOutputVerified=True,nativeTestsPassed=True,mobileAndDesktopPixelsVerified=True,
            actualBrowserCaptureVerified=True,unknownPathHttp404Verified=True,
            reviewedRoutes=sorted(p.output.FILES.values()),reviewedViewports=[320,390,1280],
            publicHttpVerified=False,assessmentScope='bounded-launch',coreHubLaunchStatus='NOT_ASSESSED',
            fullLaunchStatus='NOT_ASSESSED',verdict='PASS_GOHEUNG_PRODUCTION_ARTIFACT_REVIEW',reviewer='UNIT_TEST_FIXTURE',
            buildRunId='999998',artifactId='999997',qaRunId='999998',buildControlSha='c'*40,
            artifactDigest='sha256:'+'d'*64,outputFilesSha256='e'*64,releaseManifestSha256='f'*64,evidence=[])
        for kind in ['all-route-output','mobile-pixels','desktop-pixels']:
            path=self.docs/(kind+'.json');p.save(path,{'fixture':True,'kind':kind})
            self.review['evidence'].append(dict(kind=kind,path=path.relative_to(self.root).as_posix(),sha256=p.sha(path.read_bytes())))
        self.seal_review()

    def seal_review(self):
        # Synthetic fixtures exercise the gate, never constitute a real review.
        detail=self.docs/'bounded-launch-detail.json'
        p.save(detail,dict(fixture=True,sourceCommit=self.review['sourceCommit']))
        ref=dict(status='PASS',path=detail.relative_to(self.root).as_posix(),sha256=p.sha(detail.read_bytes()))
        if not hasattr(self,'assessment'):
            self.assessment=dict(schemaVersion=1,region='goheung',assessmentScope='bounded-launch',
                verdict='PASS_GOHEUNG_BOUNDED_LAUNCH_GATE',coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED',
                sitemapRoutes=sorted(p.SITEMAP_ROUTES),htmlFiles=2,primaryCount=1,purchaseHomeCount=1,articleCount=0,supportCount=0,
                support=None,
                publicHttpVerified=False,reviewer='UNIT_TEST_FIXTURE',
                checks={name:copy.deepcopy(ref) for name in p.BOUNDED_GATE_CHECKS},
                primaryQuality=[dict(path=path,seo=90,geo=85,aeo=90,assessmentPath=ref['path'],assessmentSha256=ref['sha256']) for path in sorted(p.SITEMAP_ROUTES)])
            for name in ['sourceCommit','bindingSha256','sourceContractSha256','buildRunId','artifactId','artifactDigest','buildControlSha']:
                self.assessment[name]=self.review[name]
        path=self.docs/'bounded-launch-assessment.json';p.save(path,self.assessment)
        self.review['evidence']=[r for r in self.review['evidence'] if r['kind']!='bounded-launch-gate']
        self.review['evidence'].append(dict(kind='bounded-launch-gate',path=path.relative_to(self.root).as_posix(),sha256=p.sha(path.read_bytes())))
        native=dict(status='ACCEPTED_ACTUAL_ACTIONS_ARTIFACT_AND_VISUAL_ONLY',accepted=True,blockingFindings=0,
            source50Revision=self.review['sourceCommit'],controlRevision=self.review['buildControlSha'],runId=int(self.review['buildRunId'] or 999998),
            runAttempt=1,artifactId=int(self.review['artifactId'] or 999997),artifactSHA256=(self.review.get('artifactDigest')or'').removeprefix('sha256:'),
            actualReleaseManifestSHA256=self.review['releaseManifestSha256'],output15ByteIdenticalToAcceptedSource50=True,
            release13FieldIdentityVerified=True,actualBrowserReportsAndPNGReplayed=True,
            independentWholeViewportPixelComparisons=24,actualPNGsVisuallyReviewed=38,fullPageCoverageComplete=True,
            independentScreenshotReview='ACCEPTED_CAPTURED_THREE_WIDTHS',visualBlockingFindings=0,
            publicHTTPVerified=False,deploymentVerified=False,IndexNowSubmitted=False,publicationReady=False)
        native_path=self.docs/'native-actual-verdict.json';p.save(native_path,native)
        self.review['evidence']=[r for r in self.review['evidence']if r['kind']!='native-actual-verdict']
        self.review['evidence'].append(dict(kind='native-actual-verdict',path=native_path.relative_to(self.root).as_posix(),sha256=p.sha(native_path.read_bytes())))
        path=self.docs/'production-release-review-20261016.json';p.save(path,self.review)
        p.save(self.d/'production-release-review-binding.json',dict(schemaVersion=1,path=path.relative_to(self.root).as_posix(),sha256=p.sha(path.read_bytes())))

    def request(self):
        env=dict(GITHUB_REPOSITORY=p.REPOSITORY,GITHUB_REF='refs/heads/main',GITHUB_ACTOR=p.gate.OWNER,
            GITHUB_TRIGGERING_ACTOR=p.gate.OWNER,GITHUB_RUN_ATTEMPT='1',GITHUB_EVENT_NAME='issues',GITHUB_SHA='9'*40)
        body=dict(schemaVersion=1,mode='publish-and-verify-only',source_branch=p.BRANCH,source_revision=self.c['sourceRevision'],
            expected_control_revision=env['GITHUB_SHA'],binding_sha256=p.gate.load()[2],
            release_review_sha256=p.sha((self.d/'production-release-review-binding.json').read_bytes()))
        event=dict(action='opened',repository=dict(full_name=p.REPOSITORY,owner=dict(login=p.gate.OWNER,type='User')),
            issue=dict(title=p.TITLE,user=dict(login=p.gate.OWNER),body=json.dumps(body)))
        return env,event

    def authorize(self,env,event):return p.authorize(self.c,p.gate.load()[2],env,event)

    def fixture_release(self):
        release=self.root/'release';dist=release/'dist';shutil.copytree(self.input_dist,dist)
        facts=p.output.inspect_dist(dist,dict(mode='production',indexable=True,origin=p.ORIGIN,revision=self.c['sourceRevision']))
        manifest=dict(schemaVersion=1,repository=p.REPOSITORY,sourceBranch=p.BRANCH,sourceRoot=p.SOURCE_ROOT,
            revision=self.c['sourceRevision'],controlRevision=self.review['buildControlSha'],runId=self.review['buildRunId'],
            origin=p.ORIGIN,worker=p.WORKER,indexable=True,bindingSha256=p.gate.load()[2],
            sourceContractSha256=self.b['sourceContractSha256'],files=facts['files'])
        p.save(release/'release.json',manifest)
        self.review.update(releaseManifestSha256=p.sha((release/'release.json').read_bytes()),
            outputFilesSha256=p.sha(json.dumps(facts['files'],sort_keys=True,separators=(',',':')).encode()))
        self.seal_review()
        return release,dist

    def test_trusted_inputs_pin_main_parser_and_source_contract_bytes(self):
        for name,code in [('production-qa/production_qa.py','reviewed_main_qa_code_changed'),('production-qa/bindings.json',None),('production-source-contract.json','production_contract_changed')]:
            path=self.d/name;original=path.read_bytes();path.write_bytes(original+b'\n')
            with self.subTest(name=name),self.assertRaises(ValueError) as raised:p.gate.inputs()
            if code:self.assertIn(code,str(raised.exception))
            path.write_bytes(original)
        self.assertEqual(p.gate.inputs()[0]['sourceRevision'],p.gate.SOURCE)

    def test_trusted_input_symlinks_and_unsafe_paths_rejected(self):
        path=self.d/'production-source-contract.json';raw=path.read_bytes();target=self.root/'outside.json';target.write_bytes(raw);path.unlink();path.symlink_to(target)
        with self.assertRaisesRegex(ValueError,'regular_file_required'):p.gate.inputs()
        path.unlink();path.write_bytes(raw)
        parent=self.root/'alias';parent.symlink_to(self.d,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'parent_symlink_forbidden'):p.gate.read(parent/'production-source-contract.json')
        for name in ['../outside.json','/outside.json']:
            with self.assertRaisesRegex(ValueError,'unsafe_control_path'):p.gate.regular_under(self.d,name)

    def test_unpinned_authorization_stays_inactive(self):
        path=self.d/'authorization-binding.json';original=json.loads(path.read_text())
        for key in ['sha256','revision']:
            bad=copy.deepcopy(original);bad[key]=None;p.save(path,bad)
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'pinned_authorization_required'):p.gate.load()
        p.save(path,original)
        for key,value in [('schemaVersion',True),('publicIssuesApproved',False),('path','docs/other.json')]:
            bad=copy.deepcopy(original);bad[key]=value;p.save(path,bad)
            with self.subTest(key=key),self.assertRaises(ValueError):p.gate.load()
        p.save(path,original)

    def test_trusted_control_rejects_nonowner_before_any_git_or_provider(self):
        env=dict(GITHUB_REPOSITORY=p.REPOSITORY,GITHUB_REF='refs/heads/main',GITHUB_ACTOR=p.gate.OWNER,GITHUB_TRIGGERING_ACTOR=p.gate.OWNER,GITHUB_RUN_ATTEMPT='1',GITHUB_EVENT_NAME='issues',GITHUB_RUN_ID='999998',GITHUB_SHA='c'*40)
        for key in env:
            bad=dict(env);bad[key]='invalid'
            with self.subTest(key=key),patch.object(p.gate,'git') as git,patch.object(p,'provider_transport') as provider,self.assertRaises(ValueError):p.gate.trusted_control(bad)
            git.assert_not_called();provider.assert_not_called()

    def test_trusted_control_requires_real_git_before_source_or_provider(self):
        env=dict(GITHUB_REPOSITORY=p.REPOSITORY,GITHUB_REF='refs/heads/main',GITHUB_ACTOR=p.gate.OWNER,GITHUB_TRIGGERING_ACTOR=p.gate.OWNER,GITHUB_RUN_ATTEMPT='1',GITHUB_EVENT_NAME='issues',GITHUB_RUN_ID='999998',GITHUB_SHA='c'*40)
        import subprocess
        with patch.object(p,'provider_transport') as provider,self.assertRaises(subprocess.CalledProcessError):p.gate.trusted_control(env)
        provider.assert_not_called()

    def test_release_does_not_require_other_region_records(self):
        self.assertFalse((self.d/'prior-launch-binding.json').exists())
        self.assertFalse((self.docs/'prior-yeosu-launch').exists())
        self.assertFalse(hasattr(p,'prior_launch'))
        self.assertEqual(self.authorize(*self.request())['sourceRevision'],self.c['sourceRevision'])
        self.assertEqual(p.release_review()['buildRunId'],self.review['buildRunId'])

    def test_obsolete_order_digest_is_rejected_as_extra_payload(self):
        env,event=self.request();body=json.loads(event['issue']['body']);body['prior_launch_sha256']='a'*64;event['issue']['body']=json.dumps(body)
        with self.assertRaisesRegex(ValueError,'exact_request_required'):self.authorize(env,event)

    def test_no_order_record_does_not_bypass_own_approval(self):
        path=self.docs/'production-authorization-20261016.json';data=json.loads(path.read_text());data['ownQualityAndSafetyGatesRequired']=False;p.save(path,data)
        descriptor=json.loads((self.d/'authorization-binding.json').read_text());descriptor['sha256']=p.sha(path.read_bytes());p.save(self.d/'authorization-binding.json',descriptor)
        with patch.object(p,'provider_transport') as provider,self.assertRaisesRegex(ValueError,'exact_goheung_authorization_required'):p.gate.load()
        provider.assert_not_called()

    def test_no_order_record_does_not_bypass_owner_or_exact_control(self):
        for field,value in [('GITHUB_ACTOR','other'),('GITHUB_TRIGGERING_ACTOR','other'),('GITHUB_RUN_ATTEMPT','2')]:
            env,event=self.request();env[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.authorize(env,event)
        env,event=self.request();body=json.loads(event['issue']['body']);body['expected_control_revision']='0'*40;event['issue']['body']=json.dumps(body)
        with self.assertRaisesRegex(ValueError,'exact_request_required'):self.authorize(env,event)

    def test_no_order_record_does_not_bypass_own_run_pixels_or_artifact(self):
        for field,value in [('buildRunId',None),('artifactId',None),('qaRunId','999990'),('artifactDigest',None),('allRouteOutputVerified',False),('nativeTestsPassed',False),('mobileAndDesktopPixelsVerified',False),('actualBrowserCaptureVerified',False),('unknownPathHttp404Verified',False)]:
            original=copy.deepcopy(self.review);self.review[field]=value;self.seal_review()
            with self.subTest(field=field),patch.object(p,'provider_transport') as provider,self.assertRaises((ValueError,TypeError)):p.release_review()
            provider.assert_not_called();self.review=original;self.seal_review()

    def test_exact_authorized_request_and_review(self):
        self.assertEqual(self.authorize(*self.request())['sourceBranch'],p.BRANCH)
        self.assertEqual(p.release_review()['qaRunId'],self.review['buildRunId'])

    def test_static_assessment_cannot_replace_actual_artifact_review(self):
        path='docs/direct-goheung/proof-successor-review/acceptance-binding.json'
        (self.root/path).parent.mkdir(parents=True,exist_ok=True)
        p.save(self.root/path,{'verdict':'ACCEPT_LOCAL_METADATA_ONLY'})
        raw=(self.root/path).read_bytes()
        p.save(self.d/'production-release-review-binding.json',dict(schemaVersion=1,path=path,sha256=p.sha(raw)))
        with self.assertRaisesRegex(ValueError,'review_identity_or_required_checks_mismatch'):p.release_review()

    def test_pending_real_review_blocks_before_evidence(self):
        p.save(self.d/'production-release-review-binding.json',dict(schemaVersion=1,path=None,sha256=None))
        with self.assertRaisesRegex(ValueError,'review_path_invalid'):p.release_review()

    def test_generic_or_core_launch_pass_cannot_replace_bounded_review(self):
        for field,value in [('assessmentScope','full-launch'),('coreHubLaunchStatus','PASS'),('fullLaunchStatus','PASS'),
                            ('actualBrowserCaptureVerified',False),('unknownPathHttp404Verified',False),
                            ('reviewedRoutes',sorted(p.SITEMAP_ROUTES)),('reviewedViewports',[390,1280]),
                            ('verdict','PASS_GANGDONG_PRODUCTION_ARTIFACT_REVIEW')]:
            old=copy.deepcopy(self.review);self.review[field]=value;self.seal_review()
            with self.subTest(field=field),self.assertRaises(ValueError):p.release_review()
            self.review=old;self.seal_review()

    def test_bounded_launch_gate_cannot_be_skipped_or_relabelled(self):
        changes=[('verdict','PASS_GOHEUNG_PRODUCTION_ARTIFACT_REVIEW'),('fullLaunchStatus','PASS'),
                 ('coreHubLaunchStatus','PASS'),('sourceCommit','b'*40),('buildRunId','999996'),
                 ('artifactDigest','sha256:'+'f'*64),('primaryCount',3),('articleCount',2),
                 ('sitemapRoutes',['/','/regions/']),('publicHttpVerified',True),('checks',{}),('primaryQuality',[])]
        for field,value in changes:
            old=copy.deepcopy(self.assessment);self.assessment[field]=value;self.seal_review()
            with self.subTest(field=field),self.assertRaises(ValueError):p.release_review()
            self.assessment=old;self.seal_review()

    def test_artifact_pass_without_bound_launch_document_is_rejected(self):
        self.review['evidence']=[row for row in self.review['evidence'] if row['kind']!='bounded-launch-gate']
        path=self.docs/'production-release-review-20261016.json';p.save(path,self.review)
        p.save(self.d/'production-release-review-binding.json',dict(schemaVersion=1,path=path.relative_to(self.root).as_posix(),sha256=p.sha(path.read_bytes())))
        with self.assertRaisesRegex(ValueError,'manual_review_evidence_missing'):p.release_review()

    def test_bounded_launch_gate_requires_every_real_check_evidence(self):
        for value in ['PENDING','NOT_ASSESSED','NOT_APPLICABLE',True]:
            old=copy.deepcopy(self.assessment)
            self.assessment['checks']['business_truth']['status']=value;self.seal_review()
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'bounded_launch_check_not_passed'):p.release_review()
            self.assessment=old;self.seal_review()
        self.assessment['checks']['business_truth']['sha256']='0'*64;self.seal_review()
        with self.assertRaisesRegex(ValueError,'review_digest_mismatch'):p.release_review()

    def test_bounded_launch_gate_quality_scores_and_support_scope_enforced(self):
        for field,value in [('seo',89),('geo',84),('aeo',89),('seo',True),('seo',101),('seo',float('nan'))]:
            old=copy.deepcopy(self.assessment);self.assessment['primaryQuality'][0][field]=value;self.seal_review()
            with self.subTest(field=field,value=value),self.assertRaisesRegex(ValueError,'primary_quality_threshold_not_met'):p.release_review()
            self.assessment=old;self.seal_review()
        for field,value in [('support',{'path':'/regions/'}),('supportCount',1),('purchaseHomeCount',0),('htmlFiles',4),('primaryCount',2),('articleCount',1)]:
            old=copy.deepcopy(self.assessment);self.assessment[field]=value;self.seal_review()
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'bounded_launch_identity_or_scope_mismatch'):p.release_review()
            self.assessment=old;self.seal_review()


    def test_gwanak_seocho_config_and_constants_rejected(self):
        for region in ['gwanak','seocho']:
            for field,value in [('hostname','seoul-'+region+'.fwith.kr'),('worker','seoul-'+region+'-flower-guide')]:
                with self.subTest(region=region,field=field):
                    p.save(self.d/'production-publication.json',{**self.config,field:value})
                    with self.assertRaises(ValueError):p.publication_config()
                    with patch.object(p,field.upper(),value),patch.object(p,'build_opener') as opener,self.assertRaises(ValueError):p.provider_transport()
                    opener.assert_not_called()

    def test_authorization_environment_mutations(self):
        for field,value in [('GITHUB_REPOSITORY','other/repo'),('GITHUB_REF','refs/heads/test'),('GITHUB_ACTOR','other'),('GITHUB_TRIGGERING_ACTOR','other'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_EVENT_NAME','push'),('GITHUB_SHA','short')]:
            env,event=self.request();env[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.authorize(env,event)

    def test_authorization_payload_mutations(self):
        for field,value in [('schemaVersion',True),('mode','build'),('source_revision','b'*40),('source_branch','source/seoul-seocho-production-successor-20261016'),('expected_control_revision','a'*40),('binding_sha256','a'*64),('receipt_issue',999996),('release_review_sha256','a'*64),('worker','seoul-gwanak-flower-guide')]:
            env,event=self.request();body=json.loads(event['issue']['body']);body[field]=value;event['issue']['body']=json.dumps(body)
            with self.subTest(field=field),self.assertRaises(ValueError):self.authorize(env,event)

    def test_authorization_event_and_owner_identity_mutations(self):
        cases=[('action','edited'),('repository_owner','other'),('repository_type','Organization'),
               ('issue_author','other'),('issue_title','[GOHEUNG-PRODUCTION-PUBLISH] old'),('body',[])]
        for kind,value in cases:
            env,event=self.request()
            if kind=='action':event['action']=value
            elif kind=='repository_owner':event['repository']['owner']['login']=value
            elif kind=='repository_type':event['repository']['owner']['type']=value
            elif kind=='issue_author':event['issue']['user']['login']=value
            elif kind=='issue_title':event['issue']['title']=value
            else:event['issue']['body']=json.dumps(value)
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.authorize(env,event)

    def test_review_identity_mutations(self):
        for field,value in [('region','seoul-seocho'),('sourceCommit','b'*40),('allRouteOutputVerified',1),('nativeTestsPassed',False),('mobileAndDesktopPixelsVerified',False),('publicHttpVerified',True),('buildRunId',None),('artifactId',None),('qaRunId','999996'),('artifactDigest','pending'),('buildControlSha','short'),('verdict','PASS_SEOCHO_PRODUCTION_ARTIFACT_REVIEW')]:
            old=copy.deepcopy(self.review);self.review[field]=value;self.seal_review()
            with self.subTest(field=field),self.assertRaises((ValueError,TypeError)):p.release_review()
            self.review=old;self.seal_review()

    def test_review_evidence_bytes_and_path(self):
        path=self.root/self.review['evidence'][0]['path'];path.write_text('{}')
        with self.assertRaisesRegex(ValueError,'review_digest_mismatch'):p.release_review()
        self.review['evidence'][0].update(path='docs/direct-goheung/../../outside.json',sha256='a'*64);self.seal_review()
        with self.assertRaisesRegex(ValueError,'review_path_invalid'):p.release_review()

    def test_exact_15_file_two_html_one_url_artifact(self):
        release,dist=self.fixture_release()
        with working(self.root):result=p.artifact()
        self.assertEqual((result['htmlFiles'],result['sitemapUrls'],result['noindexHubs'],result['files']),(2,1,0,15))
        config=json.loads((release/'wrangler.publish.json').read_text())
        self.assertEqual(set(config),{'name','compatibility_date','workers_dev','assets'})
        self.assertFalse(config['workers_dev']);self.assertEqual(config['name'],p.WORKER)
        self.assertEqual(config['assets']['not_found_handling'],'404-page')

    def test_manifest_foreign_worker_rejected(self):
        release,dist=self.fixture_release();m=json.loads((release/'release.json').read_text());m['worker']='seoul-seocho-flower-guide';p.save(release/'release.json',m)
        self.review['releaseManifestSha256']=p.sha((release/'release.json').read_bytes());self.seal_review()
        with working(self.root),self.assertRaisesRegex(ValueError,'artifact_identity_or_files_mismatch'):p.artifact()

    def test_manifest_boolean_integer_rejected(self):
        release,dist=self.fixture_release();m=json.loads((release/'release.json').read_text());m['indexable']=1;p.save(release/'release.json',m)
        self.review['releaseManifestSha256']=p.sha((release/'release.json').read_bytes());self.seal_review()
        with working(self.root),self.assertRaisesRegex(ValueError,'artifact_identity_or_files_mismatch'):p.artifact()

    def test_changed_artifact_and_404_indexing_rejected(self):
        release,dist=self.fixture_release();file=dist/'404.html';file.write_text(file.read_text().replace('noindex,nofollow','index,follow'))
        with working(self.root),self.assertRaises(AssertionError):p.artifact()

    def test_each_route_requires_focusable_main_skip_target(self):
        release,dist=self.fixture_release()
        for name in p.output.FILES:
            file=dist/name;original=file.read_text()
            for changed in [original.replace(' tabindex="-1"',''),original.replace('tabindex="-1"','tabindex="0"'),
                            original.replace('id="main-content"','id="wrong-target"')]:
                with self.subTest(file=name):
                    file.write_text(changed)
                    with self.assertRaises(AssertionError):
                        p.output.inspect_dist(dist,dict(mode='production',indexable=True,origin=p.ORIGIN,revision=self.c['sourceRevision']))
                    file.write_text(original)

    def test_symlink_release_rejected(self):
        release,dist=self.fixture_release();release.rename(self.root/'other');release.symlink_to(self.root/'other',target_is_directory=True)
        with working(self.root),self.assertRaisesRegex(ValueError,'regular_release_directories_required'):p.artifact()

    def provider_fixture(self,scripts=(),domains=()):
        account='a'*32;calls=[]
        def transport(method,path,body=None):
            calls.append((method,path,body));self.assertEqual(method,'GET')
            data={'/accounts/'+account:{'id':account},'/accounts/'+account+'/workers/scripts':[{'id':s} for s in scripts],'/accounts/'+account+'/workers/domains':list(domains)}
            return {'success':True,'errors':None,'result':data[path]}
        return account,transport,calls

    def test_provider_absence_and_exact_binding_readback(self):
        account,t,calls=self.provider_fixture()
        self.assertEqual(p.inspect_provider(account,t,'preflight')['state'],'target_absent_verified');self.assertEqual(len(calls),3)
        account,t,calls=self.provider_fixture([p.WORKER],[{'hostname':p.HOSTNAME,'service':p.WORKER}])
        self.assertEqual(p.inspect_provider(account,t,'readback')['state'],'binding_verified')

    def test_foreign_hostname_and_worker_collision_before_attach(self):
        for region in ['gwanak','seocho']:
            for row in [{'hostname':p.HOSTNAME,'service':'seoul-'+region+'-flower-guide'},{'hostname':'seoul-'+region+'.fwith.kr','service':p.WORKER}]:
                account,t,calls=self.provider_fixture([p.WORKER],[row])
                with self.subTest(row=row),patch.object(p,'provider_transport',return_value=(account,t)),self.assertRaisesRegex(ValueError,'hostname_or_worker_collision'):p.provider('attach')
                self.assertTrue(all(c[0]=='GET' for c in calls))

    def test_existing_unbound_worker_requires_review(self):
        a,t,_=self.provider_fixture([p.WORKER])
        with self.assertRaisesRegex(ValueError,'unbound_existing_worker_requires_review'):p.inspect_provider(a,t,'preflight')

    def test_first_publication_rejects_even_exact_existing_binding(self):
        a,t,calls=self.provider_fixture([p.WORKER],[{'hostname':p.HOSTNAME,'service':p.WORKER}])
        with self.assertRaisesRegex(ValueError,'first_publication_target_must_be_absent'):
            p.inspect_provider(a,t,'preflight')
        self.assertEqual(len(calls),3)
        self.assertTrue(all(call[0]=='GET' for call in calls))

    def test_provider_partial_inventory_and_duplicate_identity_block_mutations(self):
        a,t,calls=self.provider_fixture([p.WORKER,p.WORKER])
        with self.assertRaisesRegex(ValueError,'script_inventory_unverified'):p.inspect_provider(a,t,'preflight')
        a,t,calls=self.provider_fixture([p.WORKER],[dict(hostname=p.HOSTNAME,service=p.WORKER)]*2)
        with self.assertRaisesRegex(ValueError,'hostname_or_worker_collision'):p.inspect_provider(a,t,'readback')
        a,original,calls=self.provider_fixture()
        def partial(method,path,body=None):
            response=original(method,path,body)
            if path.endswith('/workers/domains'):response['result_info']={'count':0,'total_count':1,'total_pages':2}
            return response
        with self.assertRaisesRegex(RuntimeError,'incomplete_single_page'):p.inspect_provider(a,partial,'preflight')
        self.assertTrue(all(call[0]=='GET' for call in calls))

    def test_exact_binding_recovery_is_read_only(self):
        a,t,calls=self.provider_fixture([p.WORKER],[{'hostname':p.HOSTNAME,'service':p.WORKER}])
        with patch.object(p,'provider_transport',return_value=(a,t)):
            result=p.provider('readback')
        self.assertEqual(result['state'],'binding_verified')
        self.assertFalse(result['mutationsPerformed'])
        self.assertTrue(all(call[0]=='GET' for call in calls))

    def test_binding_configuration_mismatch(self):
        for field,value in [('environment','preview'),('zone_name','other.kr'),('enabled',False),('previews_enabled',True)]:
            a,t,_=self.provider_fixture([p.WORKER],[{'hostname':p.HOSTNAME,'service':p.WORKER,field:value}])
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'binding_configuration_mismatch'):p.inspect_provider(a,t,'readback')

    def test_transport_forbids_foreign_operations_and_all_overrides(self):
        with patch.dict(os.environ,{'CLOUDFLARE_ACCOUNT_ID':'a'*32,'CLOUDFLARE_API_TOKEN':'OFFLINE_TEST_ONLY'}),patch.object(p,'build_opener') as opener:
            account,transport=p.provider_transport();endpoint='/accounts/'+account+'/workers/scripts/'+p.WORKER+'/domains/records'
            body=dict(override_scope=False,override_existing_origin=False,override_existing_dns_record=False,origins=[dict(hostname=p.HOSTNAME,zone_name='fwith.kr')])
            cases=[('GET','/zones',None),('DELETE',endpoint,None),('PUT',endpoint.replace('goheung','gwanak'),body),('PUT',endpoint.replace('goheung','seocho'),body)]
            for field in ['override_scope','override_existing_origin','override_existing_dns_record']:
                for value in [True,0]:cases.append(('PUT',endpoint,{**body,field:value}))
            for region in ['gwanak','seocho']:cases.append(('PUT',endpoint,{**body,'origins':[dict(hostname='seoul-'+region+'.fwith.kr',zone_name='fwith.kr')]}))
            for method,path,data in cases:
                with self.subTest(method=method,path=path,data=data),self.assertRaises(ValueError):transport(method,path,data)
            opener.return_value.open.assert_not_called()

    def test_native_attach_exact_no_override_once(self):
        native,_=p.helpers();calls=[]
        def transport(method,path,body):calls.append((method,path,body));return {'success':True,'errors':[],'result':[]}
        native.attach(transport,'a'*32)
        self.assertEqual(len(calls),1);self.assertEqual(calls[0][0],'PUT');self.assertIn('/'+p.WORKER+'/',calls[0][1])
        self.assertEqual(calls[0][2],dict(override_scope=False,override_existing_origin=False,override_existing_dns_record=False,origins=[dict(hostname=p.HOSTNAME,zone_name='fwith.kr')]))

    def test_attach_uncertain_not_retried(self):
        native,_=p.helpers();transport=MagicMock(side_effect=TimeoutError('offline timeout'))
        with self.assertRaisesRegex(RuntimeError,'attach_result_uncertain'):native.attach(transport,'a'*32)
        self.assertEqual(transport.call_count,1)

    def test_attach_foreign_prior_preflight_prevents_put(self):
        a,t,calls=self.provider_fixture([p.WORKER]);p.save(self.root/'binding-before.json',dict(state='target_absent_verified',hostname='seoul-seocho.fwith.kr',worker=p.WORKER))
        with working(self.root),patch.object(p,'provider_transport',return_value=(a,t)),self.assertRaisesRegex(ValueError,'initial_preflight_required'):p.provider('attach')
        self.assertTrue(all(c[0]=='GET' for c in calls))

    def test_public_bytes_and_real_404_contract(self):
        release,dist=self.fixture_release()
        with working(self.root):p.artifact()
        contract=json.loads((self.root/'http-contract.json').read_text());calls=[]
        def get(path,status=200):
            calls.append((path,status));headers=Message()
            if status==404:name='404.html'
            elif path.endswith('/'):name=path.lstrip('/')+'index.html'
            else:name=path.lstrip('/')
            headers['Content-Type']='image/webp' if name.endswith('.webp') else 'image/jpeg' if name.endswith('.jpg') else 'text/html' if name.endswith('.html') else 'text/plain'
            return (dist/name).read_bytes(),headers
        with patch.object(p,'get',side_effect=get):result=p.http_once(contract)
        self.assertEqual(result['htmlRoutes'],1);self.assertEqual(result['sitemapUrls'],1);self.assertEqual(result['unknownHttpStatus'],404)
        self.assertEqual(calls[-1][1],404);self.assertEqual(len(calls),14)

    def test_soft_404_status_rejected(self):
        response=MagicMock();response.__enter__.return_value=response;response.code=200
        with patch.object(p,'build_opener') as opener:
            opener.return_value.open.return_value=response
            with self.assertRaisesRegex(ValueError,'http_status_200'):p.get('/.missing/',404)





    def test_goheung_contract_has_only_one_indexable_url(self):
        self.assertEqual(p.SITEMAP_ROUTES, {'/'})
        self.assertEqual(p.ROUTES, {'/'})
        self.assertEqual(p.ARTICLE_ROUTES, set());self.assertEqual(p.THIN_HUB_ROUTES,set())
        self.assertEqual(p.expected_robots('/404.html'), {'noindex', 'nofollow'})
        self.assertEqual(len(p.output.FILES), 2)

    def test_home_noindex_and_missing_canonical_rejected(self):
        for old,new in [('index,follow','noindex,follow'), ('<link rel="canonical" href="'+p.ORIGIN+'/">','')]:
            with self.subTest(mutation=old):
                release,dist=self.fixture_release()
                page=dist/'index.html';page.write_text(page.read_text().replace(old,new))
                with working(self.root),self.assertRaises(AssertionError):p.artifact()
                import shutil;shutil.rmtree(release)

    def test_noncanonical_phone_cta_rejected(self):
        release,dist=self.fixture_release();page=dist/'index.html';page.write_text(page.read_text().replace('tel:18440644','tel:1844-0644'))
        with working(self.root),self.assertRaisesRegex(AssertionError,'production15 bytes'):p.artifact()

    def test_directory_sitemap_entry_rejected(self):
        release,dist=self.fixture_release();file=dist/'sitemap-0.xml'
        file.write_text(file.read_text().replace('</urlset>','<url><loc>'+p.ORIGIN+'/regions/</loc></url></urlset>'))
        with working(self.root),self.assertRaisesRegex(AssertionError,'Exact one reachable home sitemap URL'):p.artifact()

    def test_unreviewed_asset_byte_change_rejected(self):
        release,dist=self.fixture_release();(dist/'_astro/CopyPage.DAvwNfjt.css').write_text('/* changed */')
        with working(self.root),self.assertRaisesRegex(AssertionError,'production15 bytes'):p.artifact()

    def test_extra_release_and_executable_output_rejected(self):
        release,dist=self.fixture_release();(release/'package.json').write_text('{}')
        with working(self.root),self.assertRaisesRegex(ValueError,'unexpected_release_files'):p.artifact()
        (release/'package.json').unlink();(dist/'_astro/CopyPage.DAvwNfjt.css').rename(dist/'_worker.js')
        with working(self.root),self.assertRaisesRegex(AssertionError,'Exact production output inventory required'):p.artifact()

    def test_missing_or_changed_copied_ownership_proof_rejected(self):
        release,dist=self.fixture_release();proof=dist/p.output.PROOF['path'].lstrip('/');proof.write_text('changed\n')
        with working(self.root),self.assertRaisesRegex(AssertionError,'Dedicated proof bytes changed'):p.artifact()

    def test_artifact_revision_cannot_change(self):
        self.fixture_release()
        with working(self.root),patch.dict(os.environ,{'REVISION':'b'*40}),self.assertRaisesRegex(ValueError,'source_revision_mismatch'):p.artifact()

    def test_attach_bound_target_has_no_second_put(self):
        a,t,calls=self.provider_fixture([p.WORKER],[dict(hostname=p.HOSTNAME,service=p.WORKER)])
        with patch.object(p,'provider_transport',return_value=(a,t)):
            self.assertFalse(p.provider('attach')['mutationsPerformed'])
        self.assertEqual(len(calls),3);self.assertTrue(all(row[0]=='GET' for row in calls))

    def test_exact_initial_preflight_allows_one_attach_put(self):
        a,t,calls=self.provider_fixture();before=p.inspect_provider(a,t,'preflight')
        p.save(self.root/'binding-before.json',before)
        a,t,calls=self.provider_fixture([p.WORKER]);native,_=p.helpers()
        with working(self.root),patch.object(p,'provider_transport',return_value=(a,t)),patch.object(native,'attach',return_value='request_accepted') as attach:
            result=p.provider('attach')
        self.assertEqual(result['state'],'attach_request_accepted');attach.assert_called_once_with(t,a)
        self.assertEqual(result['liveVerification'],'pending')

    def test_stale_preflight_identity_never_attaches(self):
        a,t,_=self.provider_fixture();baseline=p.inspect_provider(a,t,'preflight');native,_=p.helpers()
        for field,value in [('accountSha256','b'*64),('revision','b'*40),('workerExists',True),('mutationsPerformed',True)]:
            a,t,calls=self.provider_fixture([p.WORKER]);p.save(self.root/'binding-before.json',{**baseline,field:value})
            with self.subTest(field=field),working(self.root),patch.object(p,'provider_transport',return_value=(a,t)),patch.object(native,'attach') as attach,self.assertRaisesRegex(ValueError,'initial_preflight_required'):p.provider('attach')
            attach.assert_not_called()

    def test_readback_requires_exact_binding(self):
        a,t,_=self.provider_fixture([p.WORKER])
        with self.assertRaisesRegex(ValueError,'exact_binding_not_observed'):p.inspect_provider(a,t,'readback')





    def test_cloudflare_beacon_normalization_cannot_hide_other_changes(self):
        body=b'<html><body>Exact fixture</body></html>'
        beacon=b'<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon="{}"></script>'
        amended=body.replace(b'</body>',beacon+b'</body>')
        self.assertEqual(p.strip_one_cf_beacon(amended,p.sha(body)),body)
        for changed in [amended.replace(b'Exact',b'Changed'),amended.replace(beacon,beacon+beacon),amended.replace(b'beacon.min.js',b'other.js')]:
            with self.subTest(body=changed),self.assertRaises(AssertionError):p.strip_one_cf_beacon(changed,p.sha(body))

    def test_workflow_is_fixed_retained_artifact_publication_only(self):
        workflow=Path(__file__).resolve().parents[2]/'.github/workflows/goheung-production-publish.yml'
        s=workflow.read_text()
        self.assertEqual(s.count('wrangler@4.148.0 deploy'),1)
        self.assertEqual(s.count('actions/checkout@'),1)
        self.assertIn("github.run_attempt == 1",s)
        self.assertIn("github.triggering_actor == 'joseungil-kr'",s)
        self.assertIn("run.path !== '.github/workflows/goheung-production-build-only.yml'",s)
        self.assertNotIn("run.path !== '.github/workflows/' + process.env.REGION + '-production-build-only.yml'",s)
        self.assertIn("github.event.issue.title == '[GOHEUNG-PRODUCTION-PUBLISH] 20261016'",s)
        self.assertIn('artifact.digest !== review.artifactDigest',s)
        self.assertIn("run.actor?.login !== 'joseungil-kr'",s)
        self.assertIn("run.triggering_actor?.login !== 'joseungil-kr'",s)
        self.assertIn('artifact.id !== Number(review.artifactId)',s)
        self.assertIn("artifact.workflow_run.head_branch !== 'main'",s)
        self.assertNotIn('receiptIssue',s);self.assertNotIn('issues: write',s);self.assertNotIn('indexnow --report',s)
        self.assertIn('CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}',s)
        self.assertIn('CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}',s)
        for forbidden in ['npm ci','npm run build','workflow_dispatch:','push:','pull_request:', 'id-token:', 'contents: write', 'seoul-gangnam','seoul-gwanak','seoul-seocho']:
            self.assertNotIn(forbidden,s)


if __name__=='__main__':unittest.main()


