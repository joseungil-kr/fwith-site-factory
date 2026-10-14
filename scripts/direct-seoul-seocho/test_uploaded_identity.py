import copy
import json
import unittest
from unittest.mock import patch

import uploaded_identity as m

ACCOUNT = 'a' * 32
REVISION = 'b' * 40
VERSION = '023e105f-2a42-4f8b-a1c1-73f6a2a30c0f'
DEPLOYMENT = '182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e'
ETAG = 'c' * 64
STAMP = '2026-10-14T08:02:30.123Z'
PREFIX = '/accounts/' + ACCOUNT
WORKER_PATH = PREFIX + '/workers/scripts/' + m.WORKER
DEPLOYMENTS_PATH = WORKER_PATH + '/deployments?page=1&per_page=1'
VERSION_PATH = WORKER_PATH + '/versions/' + VERSION
MARKER = 'DO-NOT-PRINT-PRIVATE-VALUES'


def payload(value):
    return {'success': True, 'errors': [], 'result': value}


def fixtures():
    assets = {'config': {'html_handling': 'auto-trailing-slash', 'not_found_handling': '404-page', 'run_worker_first': False},
              'jwt': MARKER, 'opaque': MARKER}
    return {
        PREFIX: payload({'id': ACCOUNT, 'name': MARKER}),
        PREFIX + '/workers/scripts': payload([{'id': m.WORKER, 'etag': ETAG, 'created_on': STAMP,
                                               'modified_on': STAMP, 'has_assets': True, 'author': MARKER}]),
        PREFIX + '/workers/domains': payload([]),
        DEPLOYMENTS_PATH: payload({'deployments': [{'id': DEPLOYMENT, 'created_on': STAMP, 'source': 'api',
            'strategy': 'percentage', 'versions': [{'version_id': VERSION, 'percentage': 100}], 'author_email': MARKER, 'annotations': {'workers/message': MARKER}}]}),
        VERSION_PATH: payload({'id': VERSION, 'number': 1, 'metadata': {'created_on': STAMP, 'source': 'api', 'author_email': MARKER},
            'resources': {'script': {'etag': ETAG, 'handlers': ['fetch'], 'content': MARKER},
                          'assets': assets, 'bindings': [{'type': 'secret_text', 'name': MARKER, 'text': MARKER}]}}),
        WORKER_PATH + '/settings': payload({'assets': assets, 'bindings': [{'type': 'assets', 'name': MARKER}], 'secret': MARKER}),
        WORKER_PATH + '/subdomain': payload({'enabled': False, 'previews_enabled': False, 'secret': MARKER})}


def transport_for(data, calls):
    def transport(method, path, body=None):
        calls.append((method, path, body))
        if isinstance(data[path], Exception):
            raise data[path]
        return copy.deepcopy(data[path])
    return transport


def authorized_request():
    env = {'GITHUB_REPOSITORY': m.base.REPOSITORY, 'GITHUB_REF': 'refs/heads/main', 'GITHUB_ACTOR': m.base.OWNER,
           'GITHUB_RUN_ATTEMPT': '1', 'GITHUB_EVENT_NAME': 'issues', 'GITHUB_SHA': REVISION, 'GITHUB_RUN_ID': '38533055575'}
    body = {'schemaVersion': 1, 'expected_control_revision': REVISION, 'hostname': m.HOSTNAME, 'worker': m.WORKER,
            'read_only': True, 'expected_source_revision': m.SOURCE_SHA, 'prior_upload_run_id': m.PRIOR_RUN_ID}
    event = {'action': 'opened', 'repository': {'full_name': m.base.REPOSITORY, 'owner': {'login': m.base.OWNER, 'type': 'User'}},
             'issue': {'title': m.TITLE, 'user': {'login': m.base.OWNER}, 'body': json.dumps(body)}}
    return env, event


class FakeResponse:
    status = 200
    def __init__(self, value): self.raw = json.dumps(value).encode()
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, limit): return self.raw[:limit]


class InspectorTests(unittest.TestCase):
    def test_exact_authorization(self):
        self.assertEqual(m.authorize(*authorized_request()), REVISION)

    def test_environment_guards(self):
        for key, value in [('GITHUB_REPOSITORY','evil/repo'),('GITHUB_REF','refs/heads/other'),('GITHUB_ACTOR','other'),
                           ('GITHUB_RUN_ATTEMPT','2'),('GITHUB_EVENT_NAME','workflow_dispatch'),('GITHUB_SHA','bad'),('GITHUB_RUN_ID','bad')]:
            with self.subTest(key=key):
                env,event=authorized_request(); env[key]=value
                with self.assertRaises(m.Rejected): m.authorize(env,event)

    def test_issue_and_repository_owner(self):
        for part,key,value in [('issue','title','other'),('issue','user',{'login':'other'}),('repository','owner',{'login':m.base.OWNER,'type':'Organization'}),('event','action','edited')]:
            with self.subTest(part=part,key=key):
                env,event=authorized_request(); (event if part=='event' else event[part])[key]=value
                with self.assertRaises(m.Rejected): m.authorize(env,event)

    def test_exact_body(self):
        for key,value in [('hostname','other'),('worker','other'),('read_only',False),('schemaVersion',True),
                          ('expected_source_revision','c'*40),('expected_control_revision','c'*40),('prior_upload_run_id','1'),('extra',True)]:
            with self.subTest(key=key):
                env,event=authorized_request(); body=json.loads(event['issue']['body']); body[key]=value; event['issue']['body']=json.dumps(body)
                with self.assertRaises(m.Rejected): m.authorize(env,event)

    def test_seven_exact_gets_and_whitelist(self):
        calls=[]; r=m.inspect(ACCOUNT,transport_for(fixtures(),calls))
        self.assertEqual(calls,[('GET',p,None) for p in [PREFIX,PREFIX+'/workers/scripts',PREFIX+'/workers/domains',WORKER_PATH+'/settings',WORKER_PATH+'/subdomain',DEPLOYMENTS_PATH,VERSION_PATH]])
        self.assertEqual(r['state'],'uploaded_worker_identity_observed')
        self.assertEqual(r['version']['id'],VERSION); self.assertEqual(r['version']['script']['etag'],m.opaque_field({'etag':ETAG},'etag'))
        self.assertEqual(r['version']['bindingTypes'],['secret_text'])
        self.assertEqual(r['settings']['bindingTypes'],['assets'])
        self.assertEqual(r['settings']['assets']['hashes'],{})
        for forbidden in [ACCOUNT,MARKER,'author_email','jwt','content','annotations']:
            self.assertNotIn(forbidden,json.dumps(r))
        self.assertFalse(r['uploadedContentMatchesExpectedSource']); self.assertFalse(r['publicHTTPVerified'])

    def test_partial_retained_when_deployments_unsupported(self):
        data=fixtures(); data[DEPLOYMENTS_PATH]=m.Rejected('provider_http_unverified'); r={}; calls=[]
        with self.assertRaisesRegex(m.Rejected,'uploaded_identity_incomplete'): m.inspect(ACCOUNT,transport_for(data,calls),r)
        self.assertEqual(r['state'],'uploaded_worker_identity_partial'); self.assertTrue(r['script']['has_assets'])
        self.assertIn('settings',r); self.assertIn('subdomain',r); self.assertNotIn('version',r)
        self.assertEqual(len(calls),6)

    def test_independent_failure_does_not_claim_pass(self):
        data=fixtures(); data[WORKER_PATH+'/settings']=m.Rejected('provider_http_unverified'); r={}
        with self.assertRaises(m.Rejected): m.inspect(ACCOUNT,transport_for(data,[]),r)
        self.assertIn('version',r); self.assertIn('subdomain',r); self.assertNotIn('settings',r)
        self.assertEqual(r['inspectionErrors'],{'settings':'provider_http_unverified'})

    def test_wrong_version_identity_still_rejected(self):
        for key,value in [('id',DEPLOYMENT),('number',True),('number',0)]:
            data=fixtures(); data[VERSION_PATH]['result'][key]=value
            with self.subTest(key=key),self.assertRaises(m.Rejected): m.inspect(ACCOUNT,transport_for(data,[]))

    def test_opaque_empty_null_missing_etags_do_not_block_exact_reads(self):
        for value in [MARKER, 'W/"opaque-version-42"', '', None, 7, {'private':MARKER}]:
            with self.subTest(valueType=type(value).__name__):
                data=fixtures(); data[PREFIX+'/workers/scripts']['result'][0]['etag']=value
                data[VERSION_PATH]['result']['resources']['script']['etag']=value
                calls=[];r=m.inspect(ACCOUNT,transport_for(data,calls))
                self.assertEqual(len(calls),7);self.assertEqual(r['state'],'uploaded_worker_identity_observed')
                self.assertEqual(r['script']['etag'],m.opaque_field({'etag':value},'etag'))
                self.assertNotIn(MARKER,json.dumps(r));self.assertNotIn('opaque-version-42',json.dumps(r))
        data=fixtures();del data[PREFIX+'/workers/scripts']['result'][0]['etag'];del data[VERSION_PATH]['result']['resources']['script']
        r=m.inspect(ACCOUNT,transport_for(data,[]))
        self.assertFalse(r['script']['etag']['present']);self.assertFalse(r['version']['script']['etag']['present'])

    def test_different_etags_are_observed_not_misrepresented_as_source_proof(self):
        data=fixtures();data[VERSION_PATH]['result']['resources']['script']['etag']='different-opaque-tag'
        r=m.inspect(ACCOUNT,transport_for(data,[]))
        self.assertNotEqual(r['script']['etag']['sha256'],r['version']['script']['etag']['sha256'])
        self.assertFalse(r['uploadedContentMatchesExpectedSource'])

    def test_inventory_survives_bad_optional_metadata_and_reads_continue(self):
        data=fixtures();data[PREFIX+'/workers/scripts']['result'][0]['created_on']=None
        calls=[];r=m.inspect(ACCOUNT,transport_for(data,calls))
        self.assertTrue(r['workerExists']);self.assertTrue(r['script']['has_assets'])
        self.assertEqual(r['scriptMetadataErrors'],{'created_on':'identity_timestamp_invalid'})
        self.assertIn('settings',r);self.assertIn('version',r);self.assertEqual(len(calls),7)

    def test_deployment_shape_and_traffic(self):
        for rows in [[],[{},{}],[{'id':DEPLOYMENT,'created_on':STAMP,'strategy':'percentage','versions':[]}]]:
            with self.assertRaises(m.Rejected): m.active_deployment(payload({'deployments':rows}))
        for key,value in [('version_id','../settings'),('percentage',True),('percentage',99),('percentage',float('nan'))]:
            data=fixtures()[DEPLOYMENTS_PATH]; data['result']['deployments'][0]['versions'][0][key]=value
            with self.subTest(key=key),self.assertRaises(m.Rejected): m.active_deployment(data)
        with self.assertRaises(m.Rejected): m.active_deployment(payload([{}]))

    def test_deployment_pagination(self):
        for info in [{'page':2},{'per_page':2},{'count':0},{'count':True},{'total_count':0},{'total_pages':0},[]]:
            data=fixtures()[DEPLOYMENTS_PATH];data['result_info']=info
            with self.subTest(info=info),self.assertRaises(m.Rejected): m.active_deployment(data)
        data=fixtures()[DEPLOYMENTS_PATH]; data['result_info']={'page':1,'per_page':1,'count':1,'total_count':3,'total_pages':3}
        self.assertEqual(m.active_deployment(data)['versions'][0]['version_id'],VERSION)

    def test_raw_settings_hash_binds_unknown_values_without_emitting_them(self):
        data=fixtures(); before=m.inspect(ACCOUNT,transport_for(data,[]))
        data[WORKER_PATH+'/settings']['result']['secret']='different-private-value'
        after=m.inspect(ACCOUNT,transport_for(data,[]))
        self.assertNotEqual(before['rawSettingsSha256'],after['rawSettingsSha256'])
        self.assertNotIn('different-private-value',json.dumps(after))

    def test_optional_domain_fields_are_not_invented(self):
        data=fixtures(); data[PREFIX+'/workers/domains']['result']=[{'hostname':m.HOSTNAME,'service':m.WORKER}]
        r=m.inspect(ACCOUNT,transport_for(data,[]))
        self.assertFalse(r['hostnameBindingDetails']['allOptionalFieldsPresent'])
        self.assertEqual(r['hostnameBindingDetails']['observedFields'],{})

    def test_assets_hash_optional_and_values_restricted(self):
        self.assertEqual(m.assets(None)['present'],False)
        self.assertEqual(m.assets({'hash':'a'*64})['hashes'],{'hash':m.opaque_field({'hash':'a'*64},'hash')})
        for value in [None, '', MARKER, 'W/"opaque"']:
            result=m.assets({'hash':value,'etag':value})
            self.assertEqual(result['hashes']['hash'],m.opaque_field({'hash':value},'hash'))
            self.assertNotIn(MARKER,json.dumps(result))
        self.assertEqual(m.assets({'config':{'run_worker_first':['/private']}})['configuration'],{})
        for value in [{'config':{'html_handling':MARKER}},{'config':{'run_worker_first':MARKER}},MARKER]:
            with self.assertRaises(m.Rejected): m.assets(value)

    def test_inventory_collision_absence_and_pagination(self):
        for domain in [{'hostname':m.HOSTNAME,'service':'other'}, {'hostname':'other','service':m.WORKER},
                       {'hostname':m.HOSTNAME,'service':m.WORKER,'environment':'staging'},
                       {'hostname':m.HOSTNAME,'service':m.WORKER,'zone_name':'other'},
                       {'hostname':m.HOSTNAME,'service':m.WORKER,'enabled':False},
                       {'hostname':m.HOSTNAME,'service':m.WORKER,'previews_enabled':True}]:
            data=fixtures();data[PREFIX+'/workers/domains']['result']=[domain]
            with self.subTest(domain=domain),self.assertRaises(m.Rejected): m.inspect(ACCOUNT,transport_for(data,[]))
        data=fixtures();data[PREFIX+'/workers/scripts']['result']=[]
        with self.assertRaises(m.Rejected): m.inspect(ACCOUNT,transport_for(data,[]))
        data=fixtures();data[PREFIX+'/workers/scripts']['result_info']={'total_pages':2}
        with self.assertRaises(m.Rejected): m.inspect(ACCOUNT,transport_for(data,[]))

    def test_transport_blocks_every_unapproved_operation_before_network(self):
        with patch.object(m,'build_opener') as factory:
            transport=m.make_transport(ACCOUNT,'TEST-ONLY',{})
            for method,path,body in [('POST',DEPLOYMENTS_PATH,None),('PUT',WORKER_PATH+'/settings',{}),('DELETE',WORKER_PATH,None),
                ('GET',WORKER_PATH,None),('GET','/zones',None),('GET',VERSION_PATH,None),('GET',DEPLOYMENTS_PATH+'&x=1',None),
                ('GET',WORKER_PATH+'/content',None),('GET',PREFIX,{})]:
                with self.subTest(method=method,path=path),self.assertRaises(m.Rejected): transport(method,path,body)
            factory.return_value.open.assert_not_called()

    def test_version_transport_enabled_only_from_exact_deployment(self):
        with patch.object(m,'build_opener') as factory:
            factory.return_value.open.side_effect=[FakeResponse(fixtures()[DEPLOYMENTS_PATH]),FakeResponse(fixtures()[VERSION_PATH])]
            transport=m.make_transport(ACCOUNT,'TEST-ONLY',{})
            transport('GET',DEPLOYMENTS_PATH); transport('GET',VERSION_PATH)
            with self.assertRaises(m.Rejected): transport('GET',WORKER_PATH+'/versions/'+DEPLOYMENT)
            requests=[c.args[0] for c in factory.return_value.open.call_args_list]
            self.assertTrue(all(r.get_method()=='GET' and r.data is None for r in requests))

    def test_provider_errors_and_redirects_redacted(self):
        with patch.object(m,'build_opener') as factory:
            factory.return_value.open.side_effect=RuntimeError(MARKER)
            with self.assertRaisesRegex(m.Rejected,'^provider_transport_unverified$'): m.make_transport(ACCOUNT,'TEST-ONLY',{})('GET',PREFIX)
        with self.assertRaisesRegex(m.Rejected,'provider_redirect_forbidden'): m.base.NoRedirect().redirect_request(None,None,None,None,None,None)


if __name__ == '__main__':
    unittest.main()
