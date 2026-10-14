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
import test_production_build as build_tests


@contextlib.contextmanager
def working(path):
    previous=Path.cwd();os.chdir(path)
    try: yield
    finally: os.chdir(previous)


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(socket,'create_connection',side_effect=AssertionError('network_forbidden_in_unit_tests')))
        self.stack.enter_context(patch.dict(os.environ,{'REVISION':'a'*40}))
        self.root=Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.d=self.root/'scripts/direct-seoul-songpa';self.d.mkdir(parents=True)
        self.stack.enter_context(patch.object(p,'DIRECTORY',self.d))
        self.stack.enter_context(patch.object(p.gate,'DIRECTORY',self.d))
        self.c,self.b,self.save_build=build_tests.ProductionTests().fixture(self.d)
        self.config=dict(schemaVersion=1,repository=p.REPOSITORY,hostname=p.HOSTNAME,worker=p.WORKER,
                         receiptIssueTitle=p.RECEIPT_TITLE,receiptIssue=999999)
        p.save(self.d/'production-publication.json',self.config)
        self.docs=self.root/'docs/direct-seoul-songpa';self.docs.mkdir(parents=True)
        self.review=dict(region='seoul-songpa',sourceCommit=self.c['sourceRevision'],
            bindingSha256=p.gate.load()[2],sourceContractSha256=self.b['sourceContractSha256'],
            allRouteOutputVerified=True,nativeTestsPassed=True,mobileAndDesktopPixelsVerified=True,
            publicHttpVerified=False,verdict='PASS_SONGPA_PRODUCTION_ARTIFACT_REVIEW',reviewer='UNIT_TEST_FIXTURE',
            buildRunId='999998',artifactId='999997',qaRunId='999998',buildControlSha='c'*40,
            artifactDigest='sha256:'+'d'*64,outputFilesSha256='e'*64,releaseManifestSha256='f'*64,evidence=[])
        for kind in ['all-route-output','mobile-pixels','desktop-pixels']:
            path=self.docs/(kind+'.json');p.save(path,{'fixture':True,'kind':kind})
            self.review['evidence'].append(dict(kind=kind,path=path.relative_to(self.root).as_posix(),sha256=p.sha(path.read_bytes())))
        self.seal_review()

    def seal_review(self):
        path=self.docs/'production-release-review-20261014.json';p.save(path,self.review)
        p.save(self.d/'production-release-review-binding.json',dict(schemaVersion=1,path=path.relative_to(self.root).as_posix(),sha256=p.sha(path.read_bytes())))

    def request(self):
        env=dict(GITHUB_REPOSITORY=p.REPOSITORY,GITHUB_REF='refs/heads/main',GITHUB_ACTOR=p.gate.OWNER,
            GITHUB_TRIGGERING_ACTOR=p.gate.OWNER,GITHUB_RUN_ATTEMPT='1',GITHUB_EVENT_NAME='issues',GITHUB_SHA='9'*40)
        body=dict(schemaVersion=1,mode='publish',source_branch=p.BRANCH,source_revision=self.c['sourceRevision'],
            expected_control_revision=env['GITHUB_SHA'],binding_sha256=p.gate.load()[2],receipt_issue=999999,
            release_review_sha256=p.sha((self.d/'production-release-review-binding.json').read_bytes()))
        event=dict(action='opened',repository=dict(full_name=p.REPOSITORY,owner=dict(login=p.gate.OWNER,type='User')),
            issue=dict(title=p.TITLE,user=dict(login=p.gate.OWNER),body=json.dumps(body)))
        return env,event

    def authorize(self,env,event):return p.authorize(self.c,p.gate.load()[2],env,event)

    def fixture_release(self):
        release=self.root/'release';dist=release/'dist';dist.mkdir(parents=True)
        for name,route in p.output.FILES.items():
            notfound=route=='/404.html'
            text='<html><head><meta name="site-factory-revision" content="'+self.c['sourceRevision']+'"><meta name="robots" content="'+('noindex,nofollow,noarchive' if notfound else 'noindex,follow' if route == '/regions/' else 'index,follow')+'">'
            if not notfound:text+='<link rel="canonical" href="'+p.ORIGIN+route+'">'
            text+='</head><body><h1>Fixture</h1><a href="tel:18440644">전화</a><a href="https://fwith.co.kr/">주문</a></body></html>'
            file=dist/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_text(text)
        (dist/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+p.ORIGIN+'/sitemap-index.xml\n')
        (dist/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n')
        ns='http://www.sitemaps.org/schemas/sitemap/0.9'
        (dist/'sitemap-index.xml').write_text('<sitemapindex xmlns="'+ns+'"><sitemap><loc>'+p.ORIGIN+'/sitemap-0.xml</loc></sitemap></sitemapindex>')
        (dist/'sitemap-0.xml').write_text('<urlset xmlns="'+ns+'">'+''.join('<url><loc>'+p.ORIGIN+r+'</loc></url>' for r in p.output.ROUTES)+'</urlset>')
        proof=dist/p.output.PROOF['path'].lstrip('/');proof.write_text(proof.stem+'\n')
        for i in range(13):(dist/('fixture-asset-'+str(i)+'.css')).write_text('/* fixture */')
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

    def test_exact_authorized_request_and_review(self):
        self.assertEqual(self.authorize(*self.request())['sourceBranch'],p.BRANCH)
        self.assertEqual(p.release_review()['qaRunId'],self.review['buildRunId'])

    def test_pending_receipt_blocks_before_credentials(self):
        for value in [None,True,0,-1,'266']:
            with self.subTest(value=value):
                p.save(self.d/'production-publication.json',{**self.config,'receiptIssue':value})
                with patch.object(p,'provider_transport') as transport,self.assertRaises(ValueError):p.provider('preflight')
                transport.assert_not_called()

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
        for field,value in [('schemaVersion',True),('mode','build'),('source_revision','b'*40),('source_branch','source/seoul-seocho-production-successor-20261014'),('expected_control_revision','a'*40),('binding_sha256','a'*64),('receipt_issue',266),('release_review_sha256','a'*64),('worker','seoul-gwanak-flower-guide')]:
            env,event=self.request();body=json.loads(event['issue']['body']);body[field]=value;event['issue']['body']=json.dumps(body)
            with self.subTest(field=field),self.assertRaises(ValueError):self.authorize(env,event)

    def test_review_identity_mutations(self):
        for field,value in [('region','seoul-seocho'),('sourceCommit','b'*40),('allRouteOutputVerified',1),('nativeTestsPassed',False),('mobileAndDesktopPixelsVerified',False),('publicHttpVerified',True),('buildRunId',None),('artifactId',None),('qaRunId','999996'),('artifactDigest','pending'),('buildControlSha','short'),('verdict','PASS_SEOCHO_PRODUCTION_ARTIFACT_REVIEW')]:
            old=copy.deepcopy(self.review);self.review[field]=value;self.seal_review()
            with self.subTest(field=field),self.assertRaises((ValueError,TypeError)):p.release_review()
            self.review=old;self.seal_review()

    def test_review_evidence_bytes_and_path(self):
        path=self.root/self.review['evidence'][0]['path'];path.write_text('{}')
        with self.assertRaisesRegex(ValueError,'review_digest_mismatch'):p.release_review()
        self.review['evidence'][0].update(path='docs/direct-seoul-songpa/../../outside.json',sha256='a'*64);self.seal_review()
        with self.assertRaisesRegex(ValueError,'review_path_invalid'):p.release_review()

    def test_exact_23_file_five_html_three_url_artifact(self):
        release,dist=self.fixture_release()
        with working(self.root):result=p.artifact()
        self.assertEqual((result['htmlFiles'],result['sitemapUrls'],result['noindexHubs'],result['files']),(5,3,1,23))
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
        release,dist=self.fixture_release();file=dist/'404.html';file.write_text(file.read_text().replace('noindex,nofollow,noarchive','index,follow'))
        with working(self.root),self.assertRaises(AssertionError):p.artifact()

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

    def test_binding_configuration_mismatch(self):
        for field,value in [('environment','preview'),('zone_name','other.kr'),('enabled',False),('previews_enabled',True)]:
            a,t,_=self.provider_fixture([p.WORKER],[{'hostname':p.HOSTNAME,'service':p.WORKER,field:value}])
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'binding_configuration_mismatch'):p.inspect_provider(a,t,'readback')

    def test_transport_forbids_foreign_operations_and_all_overrides(self):
        with patch.dict(os.environ,{'CLOUDFLARE_ACCOUNT_ID':'a'*32,'CLOUDFLARE_API_TOKEN':'OFFLINE_TEST_ONLY'}),patch.object(p,'build_opener') as opener:
            account,transport=p.provider_transport();endpoint='/accounts/'+account+'/workers/scripts/'+p.WORKER+'/domains/records'
            body=dict(override_scope=False,override_existing_origin=False,override_existing_dns_record=False,origins=[dict(hostname=p.HOSTNAME,zone_name='fwith.kr')])
            cases=[('GET','/zones',None),('DELETE',endpoint,None),('PUT',endpoint.replace('songpa','gwanak'),body),('PUT',endpoint.replace('songpa','seocho'),body)]
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
            headers['Content-Type']='text/html' if name.endswith('.html') else 'text/plain'
            return (dist/name).read_bytes(),headers
        with patch.object(p,'get',side_effect=get):result=p.http_once(contract)
        self.assertEqual(result['htmlRoutes'],4);self.assertEqual(result['sitemapUrls'],3);self.assertEqual(result['unknownHttpStatus'],404)
        self.assertEqual(calls[-1][1],404);self.assertEqual(len(calls),22)

    def test_soft_404_status_rejected(self):
        response=MagicMock();response.__enter__.return_value=response;response.code=200
        with patch.object(p,'build_opener') as opener:
            opener.return_value.open.return_value=response
            with self.assertRaisesRegex(ValueError,'http_status_200'):p.get('/.missing/',404)

    def test_indexnow_wrong_host_or_url_list_rejected(self):
        self.fixture_release();p.helpers()
        import indexnow_finalize as indexnow
        with working(self.root):p.artifact()
        for region in ['gwanak','seocho']:
            with working(self.root),patch.object(indexnow,'request') as request:
                with self.assertRaises(ValueError):p.observed_indexnow_request('GET','https://seoul-'+region+'.fwith.kr/')
                with self.assertRaises(ValueError):p.observed_indexnow_request('POST',indexnow.ENDPOINT,{'host':'seoul-'+region+'.fwith.kr'})
                request.assert_not_called()

    def test_indexnow_unknown_journal_blocks_post(self):
        self.fixture_release();p.helpers();import indexnow_finalize as n
        site={'siteKey':'seoul-songpa-flower-direct','siteUrl':p.ORIGIN,'productionEnabled':True,'launchMode':'live','indexnowKey':'OFFLINE_FIXTURE_KEY'}
        urls=sorted(p.ORIGIN+r for r in p.SITEMAP_ROUTES)
        identity=dict(siteKey=site['siteKey'],origin=p.ORIGIN,revision='a'*40,endpoint=n.ENDPOINT,urlSetSha256=n.digest(urls),urlCount=3)
        fingerprint=n.digest({**identity,'keySha256':n.digest(site['indexnowKey'])})
        journal=MagicMock();journal.records.return_value=[dict(fingerprint=fingerprint,state='unknown')];transport=MagicMock()
        with patch.object(n,'verify_public',return_value=urls),self.assertRaisesRegex(ValueError,'prior_submission_outcome_uncertain'):n.finalize(site,'a'*40,'release',journal,transport=transport)
        transport.assert_not_called();journal.write.assert_not_called()

    def test_indexnow_accepted_journal_prevents_replay(self):
        p.helpers();import indexnow_finalize as n
        site={'siteKey':'seoul-songpa-flower-direct','siteUrl':p.ORIGIN,'productionEnabled':True,'launchMode':'live','indexnowKey':'OFFLINE_FIXTURE_KEY'};urls=sorted(p.ORIGIN+r for r in p.SITEMAP_ROUTES)
        identity=dict(siteKey=site['siteKey'],origin=p.ORIGIN,revision='a'*40,endpoint=n.ENDPOINT,urlSetSha256=n.digest(urls),urlCount=3)
        fingerprint=n.digest({**identity,'keySha256':n.digest(site['indexnowKey'])});journal=MagicMock();journal.records.return_value=[dict(fingerprint=fingerprint,state='received',httpStatus=200)];transport=MagicMock()
        with patch.object(n,'verify_public',return_value=urls):self.assertEqual(n.finalize(site,'a'*40,'release',journal,transport=transport)['state'],'already_received')
        transport.assert_not_called();journal.write.assert_not_called()


    def test_songpa_contract_has_only_three_indexable_urls(self):
        self.assertEqual(p.SITEMAP_ROUTES, {'/', '/regions/songpa-condolence-wreath/', '/regions/songpa-wedding-wreath/'})
        self.assertEqual(p.ROUTES, p.SITEMAP_ROUTES | {'/regions/'})
        self.assertEqual(p.expected_robots('/regions/'), {'noindex', 'follow'})
        self.assertEqual(p.expected_robots('/404.html'), {'noindex', 'nofollow', 'noarchive'})
        self.assertEqual(len(p.output.FILES), 5)

    def test_directory_indexing_and_missing_canonical_rejected(self):
        for old,new in [('noindex,follow','index,follow'), ('<link rel="canonical" href="'+p.ORIGIN+'/regions/">','')]:
            with self.subTest(mutation=old):
                release,dist=self.fixture_release()
                page=dist/'regions/index.html';page.write_text(page.read_text().replace(old,new))
                with working(self.root),self.assertRaises(AssertionError):p.artifact()
                import shutil;shutil.rmtree(release)

    def test_noncanonical_phone_cta_rejected(self):
        release,dist=self.fixture_release();page=dist/'index.html'
        page.write_text(page.read_text().replace('tel:18440644','tel:1844-0644'))
        facts=p.output.inspect_dist(dist,dict(mode='production',indexable=True,origin=p.ORIGIN,revision=self.c['sourceRevision']))
        manifest=json.loads((release/'release.json').read_text());manifest['files']=facts['files'];p.save(release/'release.json',manifest)
        self.review.update(releaseManifestSha256=p.sha((release/'release.json').read_bytes()),outputFilesSha256=p.sha(json.dumps(facts['files'],sort_keys=True,separators=(',',':')).encode()));self.seal_review()
        with working(self.root),self.assertRaisesRegex(ValueError,'cta_mismatch'):p.artifact()

    def test_directory_sitemap_entry_rejected(self):
        release,dist=self.fixture_release();file=dist/'sitemap-0.xml'
        file.write_text(file.read_text().replace('</urlset>','<url><loc>'+p.ORIGIN+'/regions/</loc></url></urlset>'))
        with working(self.root),self.assertRaisesRegex(AssertionError,'Exact three reachable sitemap URLs'):p.artifact()

    def test_unreviewed_asset_byte_change_rejected(self):
        release,dist=self.fixture_release();(dist/'fixture-asset-0.css').write_text('/* changed */')
        with working(self.root),self.assertRaisesRegex(ValueError,'artifact_identity_or_files_mismatch'):p.artifact()

    def test_extra_release_and_executable_output_rejected(self):
        release,dist=self.fixture_release();(release/'package.json').write_text('{}')
        with working(self.root),self.assertRaisesRegex(ValueError,'unexpected_release_files'):p.artifact()
        (release/'package.json').unlink();(dist/'fixture-asset-0.css').rename(dist/'_worker.js')
        with working(self.root),self.assertRaisesRegex(AssertionError,'Executable or routing artifact forbidden'):p.artifact()

    def test_missing_or_changed_copied_ownership_proof_rejected(self):
        release,dist=self.fixture_release();proof=dist/p.output.PROOF['path'].lstrip('/');proof.write_text('changed\n')
        with working(self.root),self.assertRaisesRegex(AssertionError,'Copied proof missing or changed'):p.artifact()

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

    def test_indexnow_accepts_only_exact_three_url_payload(self):
        self.fixture_release();p.helpers();import indexnow_finalize as n
        with working(self.root):
            p.artifact();site=p.indexnow_site()
            payload=dict(host=p.HOSTNAME,key=site['indexnowKey'],keyLocation=p.ORIGIN+p.output.PROOF['path'],urlList=sorted(p.ORIGIN+r for r in p.SITEMAP_ROUTES))
            with patch.object(n,'request',return_value=(200,'',{})) as request:
                self.assertEqual(p.observed_indexnow_request('POST',n.ENDPOINT,payload)[0],200)
                request.assert_called_once_with('POST',n.ENDPOINT,payload)
            for urls in [payload['urlList']+[p.ORIGIN+'/regions/'],payload['urlList'][:-1],list(reversed(payload['urlList']))]:
                with self.subTest(urls=urls),patch.object(n,'request') as request,self.assertRaisesRegex(ValueError,'indexnow_observation_scope_mismatch'):p.observed_indexnow_request('POST',n.ENDPOINT,{**payload,'urlList':urls})
                request.assert_not_called()

    def test_indexnow_journal_failure_prevents_submission(self):
        p.helpers();import indexnow_finalize as n
        site=dict(siteKey='seoul-songpa-flower-direct',siteUrl=p.ORIGIN,productionEnabled=True,launchMode='live',indexnowKey='OFFLINE_FIXTURE_KEY')
        urls=sorted(p.ORIGIN+r for r in p.SITEMAP_ROUTES);journal=MagicMock();journal.records.return_value=[]
        journal.write.side_effect=RuntimeError('offline journal failure');transport=MagicMock()
        with patch.object(n,'verify_public',return_value=urls),self.assertRaisesRegex(RuntimeError,'offline journal failure'):n.finalize(site,'a'*40,'release',journal,transport=transport)
        transport.assert_not_called()

    def test_indexnow_unknown_post_is_not_retried(self):
        p.helpers();import indexnow_finalize as n
        site=dict(siteKey='seoul-songpa-flower-direct',siteUrl=p.ORIGIN,productionEnabled=True,launchMode='live',indexnowKey='OFFLINE_FIXTURE_KEY')
        urls=sorted(p.ORIGIN+r for r in p.SITEMAP_ROUTES);journal=MagicMock();journal.records.return_value=[];transport=MagicMock(side_effect=TimeoutError('offline timeout'))
        with patch.object(n,'verify_public',return_value=urls),self.assertRaisesRegex(ValueError,'submission_outcome_uncertain'):n.finalize(site,'a'*40,'release',journal,transport=transport)
        self.assertEqual(transport.call_count,1)
        self.assertEqual([call.args[0]['state'] for call in journal.write.call_args_list],['started','unknown'])

    def test_cloudflare_beacon_normalization_cannot_hide_other_changes(self):
        body=b'<html><body>Exact fixture</body></html>'
        beacon=b'<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon="{}"></script>'
        amended=body.replace(b'</body>',beacon+b'</body>')
        self.assertEqual(p.strip_one_cf_beacon(amended,p.sha(body)),body)
        for changed in [amended.replace(b'Exact',b'Changed'),amended.replace(beacon,beacon+beacon),amended.replace(b'beacon.min.js',b'other.js')]:
            with self.subTest(body=changed),self.assertRaises(AssertionError):p.strip_one_cf_beacon(changed,p.sha(body))

    def test_workflow_is_fixed_retained_artifact_publication_only(self):
        workflow=Path(__file__).resolve().parents[2]/'.github/workflows/seoul-songpa-production-publish.yml'
        s=workflow.read_text()
        self.assertEqual(s.count('wrangler@4.148.0 deploy'),1)
        self.assertEqual(s.count('actions/checkout@'),1)
        self.assertIn("github.run_attempt == 1",s)
        self.assertIn("github.triggering_actor == 'joseungil-kr'",s)
        self.assertIn("github.event.issue.title == '[SONGPA-PRODUCTION-PUBLISH] 20261014'",s)
        self.assertIn('artifact.digest !== review.artifactDigest',s)
        self.assertIn("journal.title !== '[SONGPA-INDEXNOW-RECEIPTS] 20261014'",s)
        self.assertIn('CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}',s)
        self.assertIn('CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}',s)
        for forbidden in ['npm ci','npm run build','workflow_dispatch:','push:','pull_request:', 'id-token:', 'contents: write', 'seoul-gangnam','seoul-gwanak','seoul-seocho']:
            self.assertNotIn(forbidden,s)


if __name__=='__main__':unittest.main()

