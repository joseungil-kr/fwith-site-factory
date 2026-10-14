import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import production_build as b


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.c={'expectedSourceRevision':'a'*40}
        self.digest='b'*64
        self.env=dict(GITHUB_REPOSITORY=b.REPOSITORY,GITHUB_REF='refs/heads/main',GITHUB_ACTOR=b.OWNER,
                      GITHUB_RUN_ATTEMPT='1',GITHUB_EVENT_NAME='issues',GITHUB_SHA='c'*40)
        self.body=dict(schemaVersion=1,mode='build',source_branch=b.BRANCH,source_revision='a'*40,
                       expected_control_revision='c'*40,binding_sha256=self.digest)
        self.event=dict(action='opened',repository=dict(full_name=b.REPOSITORY,owner=dict(login=b.OWNER,type='User')),
                        issue=dict(title='[SEOCHO-PRODUCTION-BUILD] 20261014',user=dict(login=b.OWNER),body=json.dumps(self.body)))
    def call(self): return b.authorize(self.c,self.digest,self.env,self.event,'build')
    def test_exact_request(self): self.assertEqual(self.call()['sourceRevision'],'a'*40)
    def test_environment_guards(self):
        for key,value in [('GITHUB_REPOSITORY','x/y'),('GITHUB_REF','refs/heads/dev'),('GITHUB_ACTOR','other'),
                          ('GITHUB_RUN_ATTEMPT','2'),('GITHUB_EVENT_NAME','workflow_dispatch'),('GITHUB_SHA','short')]:
            with self.subTest(key=key):
                old=self.env[key];self.env[key]=value
                with self.assertRaises(ValueError):self.call()
                self.env[key]=old
    def test_event_guards(self):
        for change in [lambda e:e.update(action='edited'),lambda e:e['repository']['owner'].update(login='other'),
                       lambda e:e['repository']['owner'].update(type='Organization'),lambda e:e['issue']['user'].update(login='other'),
                       lambda e:e['issue'].update(title='[SEOCHO-PRODUCTION-PUBLISH] 20261014')]:
            old=copy.deepcopy(self.event);change(self.event)
            with self.assertRaises(ValueError):self.call()
            self.event=old
    def test_exact_body_and_types(self):
        for key,value in [('schemaVersion',True),('mode','publish'),('source_branch','main'),('source_revision','d'*40),
                          ('expected_control_revision','d'*40),('binding_sha256','0'*64),('extra',True)]:
            with self.subTest(key=key):
                value_body={**self.body,key:value};self.event['issue']['body']=json.dumps(value_body)
                with self.assertRaises(ValueError):self.call()
    def test_build_rejects_provider_credentials(self):
        env=dict(SITE_RELEASE_MODE='production',SITE_INDEXABLE='true',SITE_URL=b.ORIGIN,SITE_FACTORY_REVISION='a'*40,
                 SITE_RELEASE_BINDING_PATH=str(b.DIRECTORY/'production-binding.json'),SITE_RELEASE_BINDING_SHA256=self.digest)
        b.environment(self.c,self.digest,env)
        for key in ['CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID']:
            with self.assertRaises(ValueError):b.environment(self.c,self.digest,{**env,key:'TEST-ONLY'})
    def test_binding_and_contract_required(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(b,'DIRECTORY',Path(tmp)):
            with self.assertRaises((ValueError,FileNotFoundError)):b.load()
    def contract_fixture(self,directory):
        baseline=b.frozen.load_contract();contract=copy.deepcopy(baseline)
        contract['expectedSourceRevision']='a'*40
        contract['protectedFiles'].pop(b.RUNTIME_QA_EXCEPTION)
        contract['allowedModifiedOriginalPaths'].append(b.RUNTIME_QA_EXCEPTION)
        contract['productionRuntimeAmendment']=dict(parentRevision=b.PROOF_SUCCESSOR,path=b.RUNTIME_QA_EXCEPTION,
            beforeSha256='67db7b2298cd4e75fd7c23ec15d52026a20f891c7b1e22c5cadfaf1fedae9824',
            afterSha256='7f66dca9628b58c49ed3168d28091558c622d1bda1e5ca7b61934fb89ca09919')
        contract['proof']=dict(origin=b.ORIGIN,path='/TEST-ONLY-NOT-FOR-PUBLICATION.txt',sha256=b.EXISTING_PROOF_SHA256)
        contract['expectedSourcePaths'].append('public'+contract['proof']['path'])
        contract['sourceFilesSha256']={name:'0'*64 for name in contract['expectedSourcePaths']}
        contract['sourceFilesSha256']['public'+contract['proof']['path']]=b.EXISTING_PROOF_SHA256
        contract['sourceFilesSha256'][b.RUNTIME_QA_EXCEPTION]=contract['productionRuntimeAmendment']['afterSha256']
        binding=dict(schemaVersion=1,state='approved',repository=b.REPOSITORY,sourceRoot=b.SOURCE_ROOT,
            siteKey='seoul-seocho-flower-direct',hostname=b.HOSTNAME,origin=b.ORIGIN,worker=b.WORKER,
            frozenSourceRevision=b.frozen.FROZEN_REVISION,customerCopySha256=b.frozen.COPY_SHA,sourceRevision='a'*40,
            proof=contract['proof'],sitemapRoutes=b.output.ROUTES,notFoundStatus=404,thinDirectoryRobots='noindex,follow',
            approvals=dict(hostBinding=True,indexNowProof=True,publication=True),
            evidenceReferences={k:'https://github.com/'+b.REPOSITORY+'/issues/1' for k in ['hostBinding','indexNowProof','publication']})
        def save():
            raw=json.dumps(contract).encode();(directory/'production-source-contract.json').write_bytes(raw)
            binding['sourceContractSha256']=b.sha(raw)
            (directory/'production-binding.json').write_text(json.dumps(binding))
        save();return contract,binding,save
    def test_explicit_binding_and_amendment_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp);contract,binding,save=self.contract_fixture(directory)
            with patch.object(b,'DIRECTORY',directory):
                self.assertEqual(len(b.load()[0]['protectedFiles']),945)
                for mutate in [lambda:binding['approvals'].update(publication=False),
                               lambda:binding.update(worker='other'),lambda:binding.update(thinDirectoryRobots='index,follow'),
                               lambda:contract['productionRuntimeAmendment'].update(afterSha256='0'*64),
                               lambda:contract['protectedFiles'].pop(next(iter(contract['protectedFiles']))),
                               lambda:contract['sourceFilesSha256'].pop(next(iter(contract['sourceFilesSha256'])))]:
                    oldc,oldb=copy.deepcopy(contract),copy.deepcopy(binding);mutate();save()
                    with self.assertRaises(ValueError):b.load()
                    contract.clear();contract.update(oldc);binding.clear();binding.update(oldb);save()
    def test_fixed_workflow_separates_preview_regression_and_production_output(self):
        text=(Path(__file__).resolve().parents[2]/'.github/workflows/seoul-seocho-production-build-only.yml').read_text()
        self.assertNotIn('secrets.',text);self.assertNotIn('issues: write',text)
        self.assertIn('env SITE_RELEASE_MODE=preview SITE_INDEXABLE=false',text)
        self.assertIn('for script in build qa test:release',text)
        self.assertIn('ref: ${{ github.sha }}',text)
        self.assertIn('ref: ${{ steps.select.outputs.source_revision }}',text)
        self.assertIn('path: release/',text)

if __name__=='__main__':unittest.main()
