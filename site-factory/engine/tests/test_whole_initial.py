"""Synthetic whole-initial lineage fixtures, never geographic or content approval."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import batch_barrier as barrier
import render_snapshot as renderer
import provision_goyang as provision
import whole_initial as whole
from test_goyang_batch_barrier import MemoryGit, make_body, BASE, FINAL
from test_bucheon_batch_barrier import PNG, FILES, encode

SITE='namyangju-flower-v2'; SCOPE=SITE+'-dong-coverage-20261005'; ROOT='site-factory/namyangju-flower'
BOOTSTRAP='b'*40
MEMBERSHIP=hashlib.sha256(b'synthetic-only').hexdigest()


def fixture(count=3):
    source=b'// Synthetic source fixture; never a real source approval.\n'
    profile={'registryKey':'synthetic-only','sourceRevision':BASE,'sourceTree':'1'*40,'sourceCount':1}
    members=[{'unit_key':f'남양주시/법정동/합성{i}동','name':f'합성{i}동','district_key':'namyangju',
              'page_key':f'{SITE}-region-dong-{i}','intent_key':f'namyangju|flower-delivery|local-order|dong-{i}',
              'slug':f'dong-{i}','route':f'/regions/dong-{i}/'} for i in range(1,count+1)]
    initial={'mode':'whole-dong-initial','scopeKey':SCOPE,'membershipSourceSha256':MEMBERSHIP,
             'coverageSha256':'2'*64,'memberIdentitySha256':barrier.digest(members),'officialUnitCount':count,'members':members}
    target={**provision.site_entry(SITE,initial),'regionalService':{'enabled':True,'scopeKey':SCOPE,
            'definitionFile':'src/data/region-coverage.json','policyFile':'src/data/region-policy.json'}}
    registry={'sites':{SITE:target}}
    url='https://www.nyj.go.kr/'
    units=[{'unitKey':m['unit_key'],'name':m['name'],'unitType':'legal-dong','districtKeys':['namyangju'],'legalRi':[]} for m in members]
    reps=[{'pageKey':m['page_key'],'slug':m['slug'],'url':m['route'],'unitKeys':[m['unit_key']],
           'intentKey':m['intent_key'],'primaryKeyword':m['name']+' 꽃배달','status':'approved','routeMode':'regional',
           'queryEvidence':'Synthetic fixture only'} for m in members]
    coverage={'schemaVersion':2,'siteKey':SITE,'scopeKey':SCOPE,'membershipSourceSha256':MEMBERSHIP,
      'unitBasis':'legal-dong-plus-eup-myeon','countIsPageQuota':False,'officialSourceUrls':[url],
      'verifiedAt':'2026-10-04','sourceBasisDate':'2026-10-04',
      'districts':[{'key':'namyangju','name':'남양주시','sourceUrl':url}],'units':units,'representatives':reps,
      'administrativeCrosswalk':[{'aliasKey':'admin-'+m['slug'],'name':'행정'+m['name'],'districtKey':'namyangju',
          'relations':[{'unitKey':m['unit_key'],'scope':'whole'}]} for m in members]}
    policy={'schemaVersion':1,'siteKey':SITE,'scopeKey':SCOPE,'enabled':True,'unitTypes':['legal-dong'],
      'membershipSourceSha256':MEMBERSHIP,'officialHosts':['www.nyj.go.kr'],
      'visualBindings':[{'pageKey':m['page_key'],'image':'/images/fixture.png','alt':'Synthetic fixture',
        'sha256':hashlib.sha256(PNG).hexdigest(),'sourceUrl':'https://fwith.co.kr/','status':'approved',
        'purchaseMode':'catalog','productKeys':['fixture-product'],'assetType':'brand',
        'verifiedAt':'2026-10-04','width':1,'height':1,'type':'image/png'} for m in members]}
    policy={**provision.initial_policy(coverage,BASE),'enabled':True,'state':'approved-for-frozen-publisher','visualBindings':policy['visualBindings']}
    products=[{'key':'fixture-product','family':'bouquet','sourceUrl':'https://fwith.co.kr/'}]
    provenance={'siteKey':SITE,'branch':target['branch'],'root':ROOT,'customerPages':0,
       'sourceRevision':BASE,'sourceTree':profile['sourceTree'],'sourceTemplateRegistryKey':profile['registryKey'],
       'sourceRoot':provision.INITIAL_SOURCE_ROOT,'initialScope':initial,'adaptedFiles':sorted(provision.INITIAL_ADAPTATIONS),
       'sourceManifest':[{'path':'src/lib/fixture.mjs','sha256':hashlib.sha256(source).hexdigest()}]}
    provenance['bootstrapId']=provision.sha256(provision.encode(provenance))
    provenance_path=provision.target_contract(SITE)['provenancePath']
    docs={(BASE,'.github/site-factory-sites.json'):encode(registry),
          (BASE,'site-factory/engine/render_snapshot.py'):Path(renderer.__file__).read_bytes(),
          (BASE,provision.INITIAL_SOURCE_ROOT+'/src/lib/fixture.mjs'):source}
    deps={'src/data/region-coverage.json':encode(coverage),'src/data/region-policy.json':encode(policy),
          'src/data/products.json':encode(products),'public/images/fixture.png':PNG,'src/lib/fixture.mjs':source}
    history=[BASE]
    with tempfile.TemporaryDirectory() as directory:
        workspace=Path(directory); data=workspace/ROOT/'src/data';data.mkdir(parents=True)
        for path,raw in deps.items():
            file=workspace/ROOT/path;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(raw)
        for name in FILES:
            value=[] if name=='pages' else {'siteKey':SITE,'pages':[]}
            if name=='publish-manifest':value['snapshotLedger']={}
            if name=='architecture':value['hubs']=[{'category':c,'url':f'/{c}/','children':0,'indexable':False,'menuVisible':False} for c in ('regions','gift')]
            (data/(name+'.json')).write_bytes(encode(value))
        def checkpoint(revision):
            for name in FILES:docs[(revision,ROOT+'/src/data/'+name+'.json')]=(data/(name+'.json')).read_bytes()
            docs.update({(revision,ROOT+'/'+p):raw for p,raw in deps.items()})
            docs[(revision,provenance_path)]=provision.encode(provenance)
        checkpoint(BASE)
        batch={'schemaVersion':2,'contractType':'whole-region-initial','batchId':'synthetic-initial','siteKey':SITE,'scopeKey':SCOPE,
          'bootstrapSourceSha':BOOTSTRAP,'baselineSourceSha':BASE,'baselineManifestSha256':hashlib.sha256(docs[(BASE,ROOT+'/src/data/publish-manifest.json')]).hexdigest(),
          'coverageSha256':hashlib.sha256(deps['src/data/region-coverage.json']).hexdigest(),
          'policySha256':hashlib.sha256(deps['src/data/region-policy.json']).hexdigest(),
          'productsSha256':hashlib.sha256(deps['src/data/products.json']).hexdigest(),'membershipSourceSha256':MEMBERSHIP,
          'ruleRevision':whole.RULE_REVISION,'templateRevision':BASE,'registryRevision':BASE,
          'members':[{'pageKey':m['page_key'],'intentKey':m['intent_key']} for m in members]}
        batch['membershipHash']=barrier.identity(batch);items=[]
        for i,m in enumerate(members,1):
            body=make_body(i,SITE_KEY=SITE,PAGE_KEY=m['page_key'],INTENT_KEY=m['intent_key'],TARGET_REPO=target['repo'],
                 TARGET_BRANCH=target['branch'],TARGET_ROOT=ROOT,REGION='남양주',SOURCES=url,**{'SOURCE-TYPES':'official'})
            parsed=renderer.validate_content(renderer.parse_payload(body));storage,reviewed=renderer.frozen_hashes(parsed)
            renderer.render(body,registry,workspace);commit=f'{i:040x}';history.append(commit);checkpoint(commit)
            items.append({**batch['members'][i-1],**{k:batch[k] for k in barrier.REVISIONS},
              'draftRevision':'synthetic-r1','writerRunId':'synthetic-writer','payload':body,'reviewDigest':reviewed,
              'snapshotHash':storage,'queueRecordId':parsed['PUBLISH_QUEUE_RECORD_ID'],
              'issueUrl':f'https://github.com/{target["repo"]}/issues/{i}','snapshotId':parsed['SNAPSHOT_ID'],
              'commitSha':commit,'reviewSourceSha':BASE,'reviewerApproval':{'status':'approved','reviewer':'synthetic-reviewer',
              'evidenceUrl':'https://example.com/synthetic','draftRevision':'synthetic-r1','reviewDigest':reviewed,'membershipHash':batch['membershipHash']}})
        history.append(FINAL);checkpoint(FINAL)
    qa={'sourceSha':FINAL,'manifestSha256':hashlib.sha256(docs[(FINAL,ROOT+'/src/data/publish-manifest.json')]).hexdigest(),
       'state':'passed','environment':'staging','noindex':True,'reviewer':'synthetic-qa','evidenceUrl':'https://example.com/synthetic-qa',
       'gates':sorted(barrier.GOYANG_GATES),'routes':[{'url':u,'state':'passed','noindex':True} for u in ['/','/regions/']+[m['route'] for m in members]],
       'notFoundRoutes':[{'url':u,'state':'passed','status':404,'canonicalAbsent':True} for u in ['/gift/','/site-factory-live-qa-definitely-not-found/']],
       'aliasCoverageSha256':batch['coverageSha256'],'discoverableNames':sorted({u['name'] for u in units+coverage['administrativeCrosswalk']})}
    evidence={'batchId':batch['batchId'],'membershipHash':batch['membershipHash'],'finalSourceSha':FINAL,'items':items,'qa':qa}
    # Separate immutable bootstrap from the later reviewed-empty baseline.
    config=encode({'siteKey':SITE,'region':'남양주','productionApproved':False,'naverVerification':''})
    wrangler=encode({'name':target['worker'],'workers_dev':True,'assets':{'directory':'./dist/'}})
    staging=encode({'name':target['stagingWorker'],'workers_dev':True,'assets':{'directory':'./dist/'}})
    for revision in history:
        docs[(revision,ROOT+'/src/data/site-config.json')]=config
        docs[(revision,ROOT+'/wrangler.jsonc')]=wrangler
        docs[(revision,ROOT+'/wrangler.staging.jsonc')]=staging
    for (revision,path),raw in list(docs.items()):
        if revision==BASE and path.startswith(ROOT+'/'):docs[(BOOTSTRAP,path)]=raw
    candidate=copy.deepcopy(coverage)
    for row in candidate['representatives']:row['status']='candidate'
    candidate_raw=encode(candidate);docs[(BOOTSTRAP,ROOT+'/src/data/region-coverage.json')]=candidate_raw
    initial['coverageSha256']=hashlib.sha256(candidate_raw).hexdigest()
    target['initialLaunch']={k:initial[k] for k in whole.INITIAL_FIELDS}
    docs[(BASE,'.github/site-factory-sites.json')]=encode(registry)
    # Reconstruct a neutral synthetic template through the actual eight adapters.
    target_files={path[len(ROOT)+1:]:raw for (rev,path),raw in docs.items() if rev==BOOTSTRAP and path.startswith(ROOT+'/')}
    source_files=dict(target_files)
    hubs=[{'category':c,'url':f'/{c}/','label':c,'children':0,'indexable':False,'menuVisible':False} for c in [*provision.CATEGORY_TYPES,'regions']]
    source_files['src/data/site-config.json']=provision.encode({'siteKey':'template-only','region':'신규 지역','previewUrl':'https://template.invalid','stagingWorker':'template-qa','productionApproved':False,'naverVerification':''})
    source_files['src/data/architecture.json']=provision.encode({'siteKey':'template-only','home':{'url':'/','pageRole':'REGION_SERVICE_LANDING','primaryKeyword':''},'hubs':hubs,'pages':[]})
    source_files['src/data/publish-manifest.json']=provision.encode({'siteKey':'template-only','pages':[],'snapshotLedger':{}})
    source_files['src/data/page-map.json']=provision.encode({'siteKey':'template-only','pages':[]})
    source_files['src/data/region-coverage.json']=provision.encode(provision.initial_coverage_template())
    source_files['src/data/region-policy.json']=provision.encode(provision.initial_policy_template())
    source_files['wrangler.jsonc']=provision.encode({'name':'template-prod-disabled','workers_dev':True,'assets':{'directory':'./dist/'}})
    source_files['wrangler.staging.jsonc']=provision.encode({'name':'template-qa','workers_dev':True,'assets':{'directory':'./dist/'}})
    adapted=provision.adapt_initial(source_files,SITE,initial,candidate_raw,BASE)
    for path,raw in adapted.items():docs[(BOOTSTRAP,ROOT+'/'+path)]=raw
    for revision in history:
        for name in ['src/data/site-config.json','wrangler.jsonc','wrangler.staging.jsonc']:
            docs[(revision,ROOT+'/'+name)]=adapted[name]
        path=ROOT+'/src/data/architecture.json';arch=json.loads(docs[(revision,path)])
        old={h['category']:h for h in arch['hubs']}
        arch['hubs']=[{**h,**old.get(h['category'],{}),'label':h['label']} for h in hubs]
        arch['home']={'url':'/','pageRole':'REGION_SERVICE_LANDING','primaryKeyword':'남양주 꽃배달'}
        docs[(revision,path)]=encode(arch)
    profile['sourceCount']=len(source_files)
    provenance['sourceManifest']=[{'path':path,'sha256':hashlib.sha256(raw).hexdigest()} for path,raw in sorted(source_files.items())]
    provenance['targetManifest']=[{'path':path,'sha256':hashlib.sha256(raw).hexdigest()} for path,raw in sorted(adapted.items())]
    for path,raw in source_files.items():docs[(BASE,provision.INITIAL_SOURCE_ROOT+'/'+path)]=raw
    provenance.pop('bootstrapId');provenance['bootstrapId']=provision.sha256(provision.encode(provenance))
    for revision in [BOOTSTRAP]+history:docs[(revision,provenance_path)]=provision.encode(provenance)
    qa['notFoundRoutes']=[{'url':u,'state':'passed','status':404,'canonicalAbsent':True} for u in
        [f'/{c}/' for c in provision.CATEGORY_TYPES]+['/site-factory-live-qa-definitely-not-found/']]
    return batch,evidence,MemoryGit(docs,[BOOTSTRAP]+history),profile


class WholeInitialTests(unittest.TestCase):
    def setUp(self):
        self.batch,self.evidence,self.git,self.profile=fixture()
        z=patch.object(whole,'REVIEWED_BOOTSTRAP_REVISION',BOOTSTRAP);z.start();self.addCleanup(z.stop)
        p=patch.dict(whole.INITIAL_SOURCE_PROFILES,{SITE:self.profile});p.start();self.addCleanup(p.stop)
        q=patch.dict(whole.REVIEWED_INITIAL,json.loads(self.git.documents[(BASE,'.github/site-factory-sites.json')])['sites'][SITE]['initialLaunch'],clear=True);q.start();self.addCleanup(q.stop)
    def check(self):return barrier.check(self.batch,self.evidence,self.git)
    def test_empty_baseline_full_membership_and_exact_replay(self):
        before=copy.deepcopy((self.batch,self.evidence,self.git.documents))
        result=self.check();self.assertEqual(result,self.check())
        self.assertEqual((result['baselineDetailCount'],result['newDetailCount'],result['detailCount']),(0,3,3))
        self.assertEqual(before,(self.batch,self.evidence,self.git.documents))
    def test_51_members_have_no_50_ceiling(self):
        b,e,g,p=fixture(51)
        with patch.dict(whole.INITIAL_SOURCE_PROFILES,{SITE:p}), patch.dict(whole.REVIEWED_INITIAL,json.loads(g.documents[(BASE,'.github/site-factory-sites.json')])['sites'][SITE]['initialLaunch'],clear=True):self.assertEqual(barrier.check(b,e,g)['detailCount'],51)
    def test_unknown_site_and_rule_template_drift_fail(self):
        for key,value in [('siteKey','unknown'),('scopeKey','bad'),('ruleRevision','3'*40),('templateRevision','4'*40)]:
            b=copy.deepcopy(self.batch);b[key]=value
            with self.subTest(field=key),self.assertRaises((ValueError,KeyError)):barrier.check(b,self.evidence,self.git)
    def test_bootstrap_provenance_change_fails(self):
        path=provision.target_contract(SITE)['provenancePath'];self.git.documents[(FINAL,path)]+=b'\n'
        with self.assertRaisesRegex(ValueError,'provenance changed'):self.check()
    def test_reviewed_runtime_change_fails(self):
        self.git.documents[(FINAL,ROOT+'/src/lib/fixture.mjs')]=b'changed'
        with self.assertRaisesRegex(ValueError,'runtime/Truth/catalog'):self.check()
    def test_partial_missing_member_does_not_shrink_initial(self):
        self.batch['members'].pop();self.batch['membershipHash']=barrier.identity(self.batch)
        self.evidence['membershipHash']=self.batch['membershipHash']
        with self.assertRaises(ValueError):self.check()
    def test_self_approval_and_stale_hub_flags_fail(self):
        self.evidence['items'][0]['reviewerApproval']['reviewer']='synthetic-writer'
        with self.assertRaisesRegex(ValueError,'independent'):self.check()



class InitialGateTests(unittest.TestCase):
    def setUp(self):
        batch,evidence,git,profile=fixture()
        z=patch.object(whole,'REVIEWED_BOOTSTRAP_REVISION',BOOTSTRAP);z.start();self.addCleanup(z.stop)
        patcher=patch.dict(whole.INITIAL_SOURCE_PROFILES,{SITE:profile});patcher.start();self.addCleanup(patcher.stop)
        self.site=json.loads(git.documents[(BASE,'.github/site-factory-sites.json')])['sites'][SITE]
        q=patch.dict(whole.REVIEWED_INITIAL,self.site['initialLaunch'].copy(),clear=True);q.start();self.addCleanup(q.stop)
        self.site.update(productionEnabled=True,launchMode='live',approvedRevision=FINAL,
            approvalEvidenceUrl='https://github.com/joseungil-kr/fwith-site-factory/issues/220',indexnowKey='a'*64,
            initialPreviewRevision=FINAL,initialPreviewManifestSha256=evidence['qa']['manifestSha256'],
            initialBootstrapRevision=BOOTSTRAP,initialPreviewBaselineRevision=BASE)
        self.launch=SITE+'-initial-20261005'
        self.site['initialDeployment']={'enabled':True,'siteKey':SITE,'scopeKey':SCOPE,'launchKey':self.launch,
            'bootstrapSourceSha':BOOTSTRAP,'baselineSourceSha':BASE,'batchPath':'site-factory/releases/'+self.launch+'/batch.json',
            'batchEvidencePath':'site-factory/releases/'+self.launch+'/evidence.json',
            **{k:'0'*64 for k in ['batchSha256','batchEvidenceSha256','productionManifestSha256','coverageSha256','regionPolicySha256']}}
        self.git=git;self.evidence=evidence
    def resolve(self):return whole.resolve(self.site,self.site['repo'],FINAL,self.launch,SCOPE)
    def test_exact_public_and_preview_gates_are_separate(self):
        result=self.resolve();self.assertEqual(result['initial_coverage'],'true')
        self.site.update(productionEnabled=False,launchMode='staging',approvedRevision='',approvalEvidenceUrl='')
        with self.assertRaisesRegex(ValueError,'closed'):self.resolve()
        preview=whole.resolve_preview(self.site,self.site['repo'],SITE,FINAL,self.launch,SCOPE)
        self.assertEqual(preview['initial_coverage'],'true');self.assertEqual(preview['isolated'],'true')
    def test_public_gate_rejects_identity_permission_scope_or_evidence_changes(self):
        original=copy.deepcopy(self.site)
        for key,value in [('worker','other'),('branch','other'),('root','other'),('siteUrl','https://other.example'),
                          ('growthPaused',False),('autoDeploySnapshots',True),('requireSnapshotApproval',False),
                          ('requireRevisionApproval',False),('hubPolicy','other'),('approvedRevision',BASE),
                          ('approvalEvidenceUrl','https://example.com/'),('indexnowKey','')]:
            self.site=copy.deepcopy(original);self.site[key]=value
            with self.subTest(field=key),self.assertRaises(ValueError):self.resolve()
    def test_public_gate_does_not_accept_registry_declaration_without_batch_digests(self):
        for key in ['batchSha256','batchEvidenceSha256','productionManifestSha256','coverageSha256','regionPolicySha256']:
            original=self.site['initialDeployment'][key];self.site['initialDeployment'][key]=''
            with self.subTest(field=key),self.assertRaises(ValueError):self.resolve()
            self.site['initialDeployment'][key]=original
    def test_preview_requires_exact_review_target_and_complete_frozen_members(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for (revision,path),raw in self.git.documents.items():
                if revision==FINAL and path.startswith(ROOT+'/'):
                    dest=root/path[len(ROOT)+1:];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
            result=whole.validate_preview_source(self.site,SITE,FINAL,root,git=self.git);self.assertEqual(result['details'],3)
            self.site['initialLaunch']['officialUnitCount']=2
            with self.assertRaisesRegex(ValueError,'complete|membership'):whole.validate_preview_source(self.site,SITE,FINAL,root,git=self.git)
    def test_preview_does_not_accept_unpinned_revision(self):
        with self.assertRaises(ValueError):whole.resolve_preview(self.site,self.site['repo'],SITE,BASE,self.launch,SCOPE)
    def test_existing_workflows_keep_permissions_schedule_and_order(self):
        import yaml
        repo=Path(__file__).resolve().parents[3]
        prod=yaml.safe_load((repo/'.github/workflows/site-production-deploy.yml').read_text())
        preview=yaml.safe_load((repo/'.github/workflows/site-staging-deploy.yml').read_text())
        for doc in [prod,preview]:
            self.assertEqual(doc['permissions'],{})
            self.assertNotIn('schedule',doc.get('on',doc.get(True,{})))
            for job in doc['jobs'].values():self.assertEqual(job['permissions'],{'contents':'read','issues':'write'})
        steps=prod['jobs']['deploy-and-verify']['steps'];names=[x.get('name','') for x in steps]
        self.assertLess(names.index('Validate exact initial whole-batch and independent hosted evidence'),names.index('Deploy approved artifact'))
        self.assertLess(names.index('Verify initial production Worker and hostname are unassigned'),names.index('Deploy approved artifact'))
        self.assertLess(names.index('Record one exact initial domain request before mutation'),names.index('Bind exact reviewed initial hostname without overrides'))
        self.assertLess(names.index('Bind exact reviewed initial hostname without overrides'),names.index('Verify exact live revision and every published route'))
        self.assertLess(names.index('Verify exact live revision and every published route'),names.index('Submit verified URLs to IndexNow'))

if __name__=='__main__':unittest.main()
