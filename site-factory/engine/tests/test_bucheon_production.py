"""Synthetic unit fixtures only: never use these values as release evidence."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.error import HTTPError
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bucheon_production as contract
import bucheon_domain_attach as domain

REVISION = 'f' * 40  # Synthetic test-only identity.

def ready_site():
    value = {**contract.IDENTITY, 'growthPaused': True, 'autoDeploySnapshots': False,
        'requireRevisionApproval': True, 'requireSnapshotApproval': True, 'stagingBuildIsolation': True,
        'regionalService': dict(contract.REGIONAL_SERVICE), 'indexnowKey': '', 'naverVerification': '',
        'productionEnabled': True, 'launchMode': 'live', 'approvedRevision': REVISION,
        'approvalEvidenceUrl': 'https://github.com/joseungil-kr/fwith-site-factory/issues/1#unit-test-only'}
    value['coverageDeployment'] = {'enabled': True, 'launchKey': contract.SCOPE, 'scopeKey': contract.SCOPE,
        'canonicalOrigin': contract.ORIGIN, 'worker': contract.WORKER, 'wranglerConfig': 'wrangler.jsonc',
        'baselineSourceSha': contract.BASELINE, 'membershipSha256': contract.MEMBERSHIP_SHA256,
        'batchPath': contract.RELEASE_DIR+'/batch.json', 'batchEvidencePath': contract.RELEASE_DIR+'/evidence.json',
        **{key: '0'*64 for key in contract.DIGEST_FIELDS}}
    return value


class ResolverTests(unittest.TestCase):
    def call(self, value=None, **kwargs):
        return contract.resolve(value or ready_site(), kwargs.get('repository', contract.IDENTITY['repo']),
            kwargs.get('revision', REVISION), kwargs.get('launch', contract.SCOPE), kwargs.get('scope', contract.SCOPE))
    def test_exact_identity_resolves(self):
        self.assertEqual(self.call()['build_root'], 'release-build')
        self.assertEqual(self.call()['worker'], 'bucheon-flower-prod-disabled')
    def test_closed_registry_rejected(self):
        for key, val in [('productionEnabled', False), ('launchMode', 'staging'), ('approvedRevision', ''),
                         ('approvalEvidenceUrl', ''), ('growthPaused', False), ('autoDeploySnapshots', True),
                         ('requireRevisionApproval', False), ('requireSnapshotApproval', False),
                         ('stagingBuildIsolation', False), ('worker','goyang-flower-guide-qa')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                value=ready_site();value[key]=val;self.call(value)
    def test_exact_four_field_region_adapter_required(self):
        for edit in [lambda r:r.pop('definitionFile'),lambda r:r.pop('policyFile'),
                     lambda r:r.update(definitionFile='src/data/elsewhere.json'),
                     lambda r:r.update(policyFile='../region-policy.json'),lambda r:r.update(extra=True),lambda r:r.update(enabled=1)]:
            value=ready_site();edit(value['regionalService'])
            with self.assertRaisesRegex(ValueError,'region opt-in'):self.call(value)
    def test_missing_scopes_and_revision_rejected(self):
        for kwargs in ({'scope':''},{'launch':''},{'revision':'short'},{'scope':contract.SCOPE+'x'}, {'repository':'other/repo'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError): self.call(**kwargs)
    def test_evidence_and_ownership_rejected(self):
        for key,val in [('approvalEvidenceUrl','https://github.com/other/repo/issues/1'),('indexnowKey','new-key'),('naverVerification','new-owner')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                value=ready_site();value[key]=val;self.call(value)
    def test_unreviewed_or_retargeted_coverage_rejected(self):
        for key in contract.DIGEST_FIELDS+('enabled','membershipSha256','worker','batchPath','baselineSourceSha'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                value=ready_site();value['coverageDeployment'][key]='';self.call(value)
    def test_batch_bytes_and_final_revision(self):
        with tempfile.TemporaryDirectory() as d:
            value=ready_site();root=Path(d)
            docs=[{'siteKey':contract.SITE,'scopeKey':contract.SCOPE,'membershipSourceSha256':contract.MEMBERSHIP_SHA256},
                  {'finalSourceSha':REVISION}]
            for pathkey, hashkey, doc in zip(('batchPath','batchEvidencePath'),('batchSha256','batchEvidenceSha256'),docs):
                p=root/value['coverageDeployment'][pathkey];p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text(json.dumps(doc));value['coverageDeployment'][hashkey]=contract.digest(p.read_bytes())
            contract.validate_barrier_inputs(root,value,REVISION)
            with self.assertRaises(ValueError): contract.validate_barrier_inputs(root,value,'e'*40)
            (root/value['coverageDeployment']['batchPath']).write_text('{}')
            with self.assertRaises(ValueError): contract.validate_barrier_inputs(root,value,REVISION)


def write(root, name, data):
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data) if not isinstance(data,str) else data)


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'root';self.old=Path(self.temp.name)/'old';self.site=ready_site()
        old={'pageKey':'historical-facility','snapshotId':'historical-snapshot','snapshotHash':'old-hash','category':'funeral',
             'url':'/funeral/historical/','status':'approved','approvalVerified':True}
        ledger={'historical-snapshot':{'pageKey':old['pageKey'],'snapshotHash':old['snapshotHash']}}
        units=[{'unitKey':f'unit-{i}','name':f'name-{i}'} for i in range(24)]
        aliases=[{'aliasKey':f'alias-{i}','name':f'name-{i if i<12 else i+12}',
                 'relations':[{'unitKey':f'unit-{i%24}'}]+([{'unitKey':f'unit-{(i+1)%24}'}] if i<11 else [])} for i in range(37)]
        reps=[{'pageKey':f'region-{i}','status':'approved','routeMode':'regional','unitKeys':[f'unit-{i}'],
               'slug':f'dong-{i}','url':f'/regions/dong-{i}/','intentKey':f'intent-{i}'} for i in range(24)]
        pages=[old]+[{'pageKey':r['pageKey'],'snapshotId':f'snapshot-{i}','snapshotHash':f'hash-{i}',
                     'category':'regions','pageType':'regional-service','scopeKey':contract.SCOPE,
                     'regionUnitKeys':r['unitKeys'],'url':r['url'],'status':'approved','approvalVerified':True} for i,r in enumerate(reps)]
        nodes=[old]+[dict(p,intentKey=r['intentKey']) for p,r in zip(pages[1:],reps)]
        coverage={'schemaVersion':2,'siteKey':contract.SITE,'scopeKey':contract.SCOPE,'units':units,
                  'administrativeCrosswalk':aliases,'representatives':reps}
        policy={'schemaVersion':1,'siteKey':contract.SITE,'scopeKey':contract.SCOPE,'enabled':True,
                'visualBindings':[{'pageKey':r['pageKey'],'status':'approved'} for r in reps]}
        for root,rs,ns in [(self.old,[old],[old]),(self.root,pages,nodes)]:
            manifest={'siteKey':contract.SITE,'snapshotMode':'git-frozen','pages':rs,'snapshotLedger':ledger}
            for name,doc in [('pages.json',rs),('publish-manifest.json',manifest),('architecture.json',{'siteKey':contract.SITE,'pages':ns}),
                             ('page-map.json',{'pages':rs}),('products.json',[]),('business-truth.json',{})]:write(root,'src/data/'+name,doc)
            write(root,'wrangler.jsonc',{'name':contract.WORKER,'assets':{'directory':'./dist/'}})
            write(root,'wrangler.staging.jsonc',{'name':'bucheon-flower-guide-qa'})
            write(root,'public/images/old.webp','historical-image')
        write(self.root,'src/data/region-coverage.json',coverage);write(self.root,'src/data/region-policy.json',policy)
        write(self.root,'src/data/site-config.json',{'productionApproved':True});write(self.root,'production-indexing.enabled','enabled')
        self.refresh()
    def refresh(self):
        for name,key in [('publish-manifest','productionManifestSha256'),('region-coverage','coverageSha256'),('region-policy','regionPolicySha256')]:
            self.site['coverageDeployment'][key]=contract.digest((self.root/f'src/data/{name}.json').read_bytes())
    def call(self):return contract.validate_source(self.root,self.old,self.site)
    def change(self,name,fn,refresh=True):
        p=self.root/'src/data'/name;data=json.loads(p.read_text());fn(data);p.write_text(json.dumps(data))
        if refresh:self.refresh()
    def test_complete_synthetic_source(self):self.assertEqual(self.call()['manifestPages'],25)
    def test_missing_geographic_unit(self):
        self.change('region-coverage.json',lambda x:x['units'].pop())
        with self.assertRaises(ValueError):self.call()
    def test_pending_content_or_visual(self):
        for name,fn in [('region-coverage.json',lambda x:x['representatives'][0].update(status='candidate')),
                        ('region-policy.json',lambda x:x['visualBindings'][0].update(status='pending'))]:
            with self.subTest(name=name):
                p=self.root/'src/data'/name;original=p.read_bytes();self.change(name,fn)
                with self.assertRaises(ValueError):self.call()
                p.write_bytes(original);self.refresh()
    def test_review_digest_mismatch(self):
        self.change('region-policy.json',lambda x:x.update(enabled=False),refresh=False)
        with self.assertRaises(ValueError):self.call()
    def test_historical_source_protection(self):
        self.change('pages.json',lambda x:x[0].update(title='edited trial'))
        with self.assertRaises(ValueError):self.call()
    def test_historical_asset_protection(self):
        write(self.root,'public/images/old.webp','changed')
        with self.assertRaises(ValueError):self.call()
    def test_routing_configuration_rejected(self):
        write(self.root,'wrangler.jsonc',{'name':'another-worker','routes':['*']})
        with self.assertRaises(ValueError):self.call()
    def test_symlink_frozen_file_and_parent_rejected(self):
        path=self.root/'src/data/region-policy.json'
        original=path.read_bytes();other=self.root/'policy-copy.json';other.write_bytes(original)
        path.unlink();path.symlink_to(other)
        with self.assertRaisesRegex(ValueError,'Symlink'):self.call()
        path.unlink();path.write_bytes(original)
        folder=self.root/'src/data';folder.rename(self.root/'data-copy')
        folder.symlink_to(self.root/'data-copy',target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'Symlink'):self.call()
    def test_false_indexing_gate(self):
        write(self.root,'src/data/site-config.json',{'productionApproved':False})
        with self.assertRaises(ValueError):self.call()


class DomainTests(unittest.TestCase):
    def inventory(self, scripts=None, domains=None):
        prefix='/accounts/'+'a'*32
        rows={prefix:{'success':True,'result':{'id':'a'*32}},
              prefix+'/workers/scripts':{'success':True,'result':[] if scripts is None else scripts},
              prefix+'/workers/domains':{'success':True,'result':[] if domains is None else domains}}
        calls=[]
        def transport(method,path):
            self.assertEqual(method,'GET');calls.append(path);return rows[path]
        return rows,calls,transport
    def test_domain_null_errors_requires_exact_success_complete_http200(self):
        path='/accounts/'+'a'*32+'/workers/domains'
        rows,calls,transport=self.inventory();rows[path]['errors']=None;transport.last_http_status=200
        result=domain.preflight(transport,'a'*32)
        self.assertEqual(result['state'],'bucheon_initial_target_absent_verified')
        self.assertEqual(len(calls),3)
        mutations=[lambda r:r[path].update(success=False),lambda r:r[path].update(result={}),
            lambda r:r[path].update(errors=[{'code':10000}]),lambda r:r[path].update(errors={}),
            lambda r:r[path].update(result_info={'total_count':1}),
            lambda r:r[path].update(result=[{'hostname':'bucheon.fwith.kr','service':'existing'}]),
            lambda r:r[path].update(result=[{'hostname':'other.fwith.kr','service':domain.WORKER}]),
            lambda r:r[path].update(result=[{'hostname':'other.fwith.kr'}])]
        for edit in mutations:
            rows,calls,transport=self.inventory();rows[path]['errors']=None;transport.last_http_status=200;edit(rows)
            with self.assertRaises(domain.PreflightError):domain.preflight(transport,'a'*32)
        for status in (None,201,403,500):
            rows,calls,transport=self.inventory();rows[path]['errors']=None;transport.last_http_status=status
            with self.assertRaises(domain.PreflightError):domain.preflight(transport,'a'*32)
        rows,calls,transport=self.inventory();transport.last_http_status=200
        rows['/accounts/'+'a'*32+'/workers/scripts']['errors']=None
        with self.assertRaises(domain.PreflightError):domain.preflight(transport,'a'*32)
    def test_preflight_diagnostics_preserve_stage_without_sensitive_message(self):
        prefix='/accounts/'+'a'*32
        for stage in ('scripts','domains'):
            rows,calls,original=self.inventory();diagnostics={}
            def transport(method,path):
                if path.endswith('/'+stage):
                    raise json.JSONDecodeError('DO_NOT_PRINT_TOKEN', 'DO_NOT_PRINT_BODY', 0)
                return original(method,path)
            with self.subTest(stage=stage), self.assertRaises(domain.PreflightError):
                domain.preflight(transport,'a'*32,diagnostics)
            self.assertEqual(diagnostics['readStage'],stage)
            self.assertEqual(diagnostics['exceptionType'],'JSONDecodeError')
            self.assertNotIn('DO_NOT_PRINT',json.dumps(diagnostics))
            self.assertTrue(all(path.startswith(prefix) for path in calls))
    def test_preflight_http_diagnostics_are_bounded_and_never_retry(self):
        rows,calls,original=self.inventory();diagnostics={};attempts=[]
        def transport(method,path):
            if path.endswith('/domains'):
                attempts.append(path)
                raise HTTPError('https://private.invalid/?token=secret',403,'SECRET_MESSAGE',{'X-Secret':'secret'},
                    io.BytesIO(b'{"errors":[{"code":10000,"message":"SECRET_BODY"}]}'))
            return original(method,path)
        with self.assertRaises(domain.PreflightError):domain.preflight(transport,'a'*32,diagnostics)
        self.assertEqual(len(attempts),1)
        self.assertEqual(diagnostics,{'readStage':'domains','exceptionType':'HTTPError','observedHttpStatus':403,'cloudflareErrorCodes':[10000]})
        self.assertNotIn('SECRET',json.dumps(diagnostics))
        self.assertNotIn('secret',json.dumps(diagnostics))
    def test_preflight_uncertain_envelope_keeps_failure_and_safe_code(self):
        rows,calls,transport=self.inventory();rows['/accounts/'+'a'*32+'/workers/scripts']['errors']=[{'code':123,'message':'SECRET'}];diagnostics={}
        with self.assertRaisesRegex(domain.PreflightError,'request_failed'):domain.preflight(transport,'a'*32,diagnostics)
        self.assertEqual(diagnostics['diagnosticCode'],'inventory_response_uncertain')
        self.assertEqual(diagnostics['cloudflareErrorCodes'],[123])
        self.assertEqual(diagnostics['readStage'],'scripts')
        self.assertNotIn('SECRET',json.dumps(diagnostics))
        self.assertEqual(diagnostics['errorsShape'],'array')
        self.assertIs(diagnostics['successVerified'],True)
        self.assertIs(diagnostics['resultIsArray'],True)
    def test_initial_target_absence_requires_complete_get_only_observation(self):
        rows,calls,transport=self.inventory()
        result=domain.preflight(transport,'a'*32)
        self.assertEqual(result['state'],'bucheon_initial_target_absent_verified')
        self.assertEqual(len(calls),3);self.assertFalse(result['mutationsPerformed'])
        self.assertEqual(result['dnsState'],'not_observed')
    def test_existing_worker_always_blocks_initial_asset_deploy(self):
        rows,calls,transport=self.inventory(scripts=[{'id':domain.WORKER}])
        with self.assertRaisesRegex(domain.PreflightError,'existing_worker'):domain.preflight(transport,'a'*32)
    def test_existing_hostname_or_worker_reference_blocks(self):
        for row in [{'hostname':domain.HOSTNAME,'service':'different'}, {'hostname':'other.example','service':domain.WORKER}]:
            rows,calls,transport=self.inventory(domains=[row])
            with self.assertRaisesRegex(domain.PreflightError,'existing_hostname_or_worker'):domain.preflight(transport,'a'*32)
    def test_incomplete_or_denied_inventory_never_means_absent(self):
        for path in ['/accounts/'+'a'*32+'/workers/scripts','/accounts/'+'a'*32+'/workers/domains']:
            rows,calls,transport=self.inventory();rows[path]['result_info']={'total_count':1,'count':0}
            with self.assertRaises(domain.PreflightError):domain.preflight(transport,'a'*32)
        def denied(method,path):raise HTTPError('https://api.cloudflare.com/',403,'denied',{},io.BytesIO(b''))
        with self.assertRaises(domain.PreflightError):domain.preflight(denied,'a'*32)
    def test_account_identity_and_malformed_inventory_fail(self):
        for edit in [lambda rows:rows['/accounts/'+'a'*32].update(result={'id':'b'*32}),
                     lambda rows:rows['/accounts/'+'a'*32+'/workers/scripts'].update(result=[{'id':''}]),
                     lambda rows:rows['/accounts/'+'a'*32+'/workers/domains'].update(result=[{}]),
                     lambda rows:rows['/accounts/'+'a'*32+'/workers/domains'].update(errors=[{'code':1}])]:
            rows,calls,transport=self.inventory();edit(rows)
            with self.assertRaises(domain.PreflightError):domain.preflight(transport,'a'*32)
    def test_exact_no_override_request(self):
        calls=[]
        def transport(*args):calls.append(args);return {'success':True}
        self.assertEqual(domain.attach(transport,'a'*32),'request_accepted')
        self.assertEqual(calls,[('PUT','/accounts/'+'a'*32+'/workers/scripts/bucheon-flower-prod-disabled/domains/records',
            {'override_scope':False,'override_existing_origin':False,'override_existing_dns_record':False,
             'origins':[{'hostname':'bucheon.fwith.kr','zone_name':'fwith.kr'}]})])
    def test_invalid_account_no_request(self):
        with self.assertRaises(domain.PreflightError):domain.attach(lambda *args:self.fail('network call'), '../bad')
    def test_denial_and_uncertain_response_never_retried(self):
        for status in (403,408,500):
            calls=[]
            def transport(*args):calls.append(args);raise HTTPError('https://api.cloudflare.com/',status,'error',{},io.BytesIO(b'{"errors":[{"code":10000}]}'))
            with self.subTest(status=status),self.assertRaises(domain.PreflightError):domain.attach(transport,'a'*32)
            self.assertEqual(len(calls),1)
    def test_transport_timeout_never_retried(self):
        calls=[]
        def transport(*args):calls.append(args);raise TimeoutError('uncertain')
        with self.assertRaisesRegex(domain.PreflightError,'attach_result_uncertain'):domain.attach(transport,'a'*32)
        self.assertEqual(len(calls),1)


class WorkflowTests(unittest.TestCase):
    def test_registered_route_uses_guard_before_deploy_and_domain_after(self):
        import yaml
        root=Path(__file__).resolve().parents[3]
        for name in ['site-production-deploy.yml','site-staging-deploy.yml']:
            doc=yaml.safe_load((root/'.github/workflows'/name).read_text())
            self.assertEqual(doc['permissions'],{})
            self.assertNotIn('schedule',doc.get('on',doc.get(True,{})))
            for job in doc['jobs'].values():self.assertEqual(job['permissions'],{'contents':'read','issues':'write'})
        steps=yaml.safe_load((root/'.github/workflows/site-production-deploy.yml').read_text())['jobs']['deploy-and-verify']['steps']
        names=[x.get('name','') for x in steps]
        self.assertLess(names.index('Validate Bucheon approved whole-batch evidence and exact frozen source'),names.index('Deploy approved artifact'))
        self.assertLess(names.index('Verify initial Bucheon Worker and hostname are unassigned before asset deployment'),names.index('Deploy approved artifact'))
        self.assertLess(names.index('Deploy approved artifact'),names.index('Bind exact approved Bucheon hostname without overrides'))
        self.assertLess(names.index('Bind exact approved Bucheon hostname without overrides'),names.index('Verify exact live revision and every published route'))
        marker=steps[names.index('Record one exact Bucheon domain request before mutation')]
        self.assertIn('GITHUB_RUN_ATTEMPT',marker['with']['script'])
        self.assertIn('BUCHEON_DOMAIN_REQUEST_STARTED:',marker['with']['script'])
    def test_exact_scoped_staging_accepts_final_source_noindex(self):
        import os,re,yaml
        from unittest.mock import patch
        root=Path(__file__).resolve().parents[3]
        doc=yaml.safe_load((root/'.github/workflows/site-staging-deploy.yml').read_text())
        step=next(x for x in doc['jobs']['preview']['steps'] if x.get('id')=='target')
        script=re.search("python3 - <<'PYTHON'\n(.*?)\nPYTHON",step['run'],re.S).group(1)
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d);(directory/'control/.github').mkdir(parents=True)
            site=ready_site();site.update(productionEnabled=False,launchMode='staging',approvedRevision='',approvalEvidenceUrl='')
            write(directory,'control/.github/site-factory-sites.json',{'sites':{contract.SITE:site}})
            env={'SITE_KEY':contract.SITE,'REVISION':REVISION,'LAUNCH_KEY':contract.SCOPE,'SCOPE_KEY':contract.SCOPE,
                 'ISSUE_BODY':'','GITHUB_OUTPUT':str(directory/'output'),'GITHUB_REPOSITORY':contract.IDENTITY['repo']}
            cwd=os.getcwd()
            try:
                os.chdir(directory)
                with patch.dict(os.environ,env,clear=True):exec(compile(script,'staging-inline','exec'),{})
                self.assertIn('bucheon_coverage=true',(directory/'output').read_text())
                with patch.dict(os.environ,{**env,'SCOPE_KEY':'wrong'},clear=True), self.assertRaises(SystemExit):exec(script,{})
            finally:os.chdir(cwd)
    @unittest.skipUnless(os.environ.get('BUCHEON_INTEGRATION_REGISTRY'), 'Supply the actual integrated control registry to run this integration fixture')
    def test_actual_integrated_registry_four_field_adapter(self):
        import re,yaml
        from unittest.mock import patch
        source=Path(os.environ['BUCHEON_INTEGRATION_REGISTRY']).resolve()
        raw=source.read_bytes();registry=json.loads(raw);site=registry['sites'][contract.SITE]
        self.assertEqual(site['regionalService'],contract.REGIONAL_SERVICE)
        self.assertIs(site['regionalService']['enabled'],True)
        with self.assertRaisesRegex(ValueError,'Production Launch Gate is closed'):
            contract.resolve(site,contract.IDENTITY['repo'],REVISION,contract.SCOPE,contract.SCOPE)
        # Test actual registry bytes unchanged through the real staging resolver.
        root=Path(__file__).resolve().parents[3]
        doc=yaml.safe_load((root/'.github/workflows/site-staging-deploy.yml').read_text())
        script=re.search("python3 - <<'PYTHON'\n(.*?)\nPYTHON",next(x for x in doc['jobs']['preview']['steps'] if x.get('id')=='target')['run'],re.S).group(1)
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d);(directory/'control/.github').mkdir(parents=True)
            (directory/'control/.github/site-factory-sites.json').write_bytes(raw)
            env={'SITE_KEY':contract.SITE,'REVISION':REVISION,'LAUNCH_KEY':contract.SCOPE,'SCOPE_KEY':contract.SCOPE,
                 'ISSUE_BODY':'','GITHUB_OUTPUT':str(directory/'output'),'GITHUB_REPOSITORY':contract.IDENTITY['repo']}
            cwd=os.getcwd()
            try:
                os.chdir(directory)
                with patch.dict(os.environ,env,clear=True):exec(script,{})
                self.assertIn('bucheon_coverage=true',(directory/'output').read_text())
                for update in ({'enabled':1},{'definitionFile':'src/data/other.json'},{'policyFile':'../policy.json'},{'extra':True}):
                    bad=copy.deepcopy(registry);bad['sites'][contract.SITE]['regionalService'].update(update)
                    write(directory,'control/.github/site-factory-sites.json',bad)
                    with patch.dict(os.environ,env,clear=True),self.assertRaises(SystemExit):exec(script,{})
            finally:os.chdir(cwd)
        proof={'registryFile':str(source),'registrySha256':hashlib.sha256(raw).hexdigest(),
               'actualRegistryBytesUsedWithoutProjection':True,'productionRemainsClosed':True,
               'exactScopeStagingResolved':True,'extraPathBooleanMutationsRejected':True}
        if os.environ.get('BUCHEON_INTEGRATION_PROOF'):
            Path(os.environ['BUCHEON_INTEGRATION_PROOF']).write_text(json.dumps(proof,indent=2)+'\n')
    def test_production_inline_blocks_current_closed_registry(self):
        import os,re,yaml
        from unittest.mock import patch
        root=Path(__file__).resolve().parents[3]
        doc=yaml.safe_load((root/'.github/workflows/site-production-deploy.yml').read_text())
        script=re.search("python3 - <<'PYTHON'\n(.*?)\nPYTHON",next(x for x in doc['jobs']['deploy-and-verify']['steps'] if x.get('id')=='target')['run'],re.S).group(1)
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d);(directory/'control/.github').mkdir(parents=True)
            site=ready_site();site.update(productionEnabled=False,launchMode='staging',approvedRevision='',approvalEvidenceUrl='')
            write(directory,'control/.github/site-factory-sites.json',{'sites':{contract.SITE:site}})
            env={'SITE_KEY':contract.SITE,'REVISION':REVISION,'LAUNCH_KEY':contract.SCOPE,'SCOPE_KEY':contract.SCOPE,
                 'ISSUE_BODY':'','GITHUB_OUTPUT':str(directory/'output'),'GITHUB_REPOSITORY':contract.IDENTITY['repo']}
            cwd=os.getcwd()
            try:
                os.chdir(directory)
                with patch.dict(os.environ,env,clear=True),self.assertRaisesRegex(ValueError,'closed'):exec(script,{})
                self.assertFalse((directory/'output').exists())
            finally:os.chdir(cwd)



class LiveRobotsTests(unittest.TestCase):
    def test_bucheon_thin_meta_does_not_require_response_noindex(self):
        import verify_live as qa
        doc=qa.Document('<meta name="robots" content="noindex,follow">')
        qa.validate_bucheon_response_robots(doc,False,'','/funeral/')
        for header in ('noindex','nofollow','none','googlebot: noindex','noindex,follow'):
            with self.assertRaises(ValueError):qa.validate_bucheon_response_robots(doc,False,header,'/funeral/')
        for meta in ('index,follow','noindex,nofollow','noindex','noindex,follow,noarchive'):
            with self.assertRaises(ValueError):qa.validate_bucheon_response_robots(qa.Document('<meta name="robots" content="'+meta+'">'),False,'','/funeral/')
    def test_seongnam_thin_still_requires_its_noindex_header(self):
        import verify_live as qa
        html='<meta name="site-factory-revision" content="'+REVISION+'"><meta name="robots" content="noindex,follow"><link rel="canonical" href="https://seongnam.fwith.kr/funeral/"><h1>test</h1><script type="application/ld+json">{}</script>'
        with self.assertRaisesRegex(AssertionError,'Missing X-Robots-Tag'):
            qa.validate_html(html,'https://seongnam.fwith.kr','/funeral/',REVISION,indexable=False,strict_seongnam=True)
        qa.validate_html(html,'https://seongnam.fwith.kr','/funeral/',REVISION,indexable=False,robot_header='noindex',strict_seongnam=True)
    @unittest.skipUnless(os.environ.get('BUCHEON_PRODUCTION_FIXTURE_ROOT') and os.environ.get('BUCHEON_HEADER_FIXTURE_DIST'), 'Supply the existing independent production artifacts; do not rebuild')
    def test_actual_production_artifact_and_generated_header_contract(self):
        import fnmatch
        import verify_live as qa
        root=Path(os.environ['BUCHEON_PRODUCTION_FIXTURE_ROOT']).resolve();dist=root/'dist'
        boundary=Path(os.environ['BUCHEON_HEADER_FIXTURE_DIST']).resolve()
        self.assertEqual((dist/'_headers').read_bytes(),(boundary/'_headers').read_bytes())
        raw_headers=(dist/'_headers').read_text();rules=[];current=None
        for line in raw_headers.splitlines():
            if not line.strip():continue
            if not line.startswith(' '):current=(line.strip(),{});rules.append(current)
            else:
                key,value=line.strip().split(':',1);current[1][key]=value.strip()
        def headers(route):
            result={}
            for pattern,values in rules:
                if fnmatch.fnmatchcase(route,pattern):result.update(values)
            return result
        def fetch(route):
            p=dist/route.lstrip('/')
            if p.is_dir():p=p/'index.html'
            status=200
            if not p.is_file():status=404;p=dist/'404.html'
            return status,p.read_text(),headers(route)
        home=qa.Document((dist/'index.html').read_text());revision=home.metas['site-factory-revision']
        result=qa.verify(root,contract.ORIGIN,revision,fetch,site_key=contract.SITE)
        self.assertEqual((result['routes'],result['manifestPages']),(28,25))
        thin=qa.Document((boundary/'funeral/index.html').read_text())
        qa.validate_bucheon_response_robots(thin,False,headers('/funeral/').get('X-Robots-Tag',''),'/funeral/')
        rejected=[]
        for bad in ['noindex','nofollow','none','noindex,nofollow,noarchive']:
            def mutated(route):
                status,body,values=fetch(route);return status,body,{**values,'X-Robots-Tag':bad}
            with self.assertRaises((ValueError,AssertionError)):qa.verify(root,contract.ORIGIN,revision,mutated,site_key=contract.SITE)
            rejected.append(bad)
        proof={'fixtureOnly':True,'rebuildPerformed':False,'productionRoot':str(root),'headerFixtureDist':str(boundary),
               'headerSha256':hashlib.sha256(raw_headers.encode()).hexdigest(),'result':result,
               'actualThinMeta':thin.metas['robots'],'actualThinResponseRobots':headers('/funeral/').get('X-Robots-Tag'),
               'blockingGlobalHeadersRejected':rejected,'seongnamPolicyUnchanged':True,'externalCalls':0}
        if os.environ.get('BUCHEON_ARTIFACT_PROOF'):Path(os.environ['BUCHEON_ARTIFACT_PROOF']).write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':unittest.main()
