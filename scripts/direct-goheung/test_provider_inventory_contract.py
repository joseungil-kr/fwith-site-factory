"""GET-only fixtures for first-host absence; no existing-host update contract."""
import copy
import os
import unittest
from unittest.mock import patch
import publish as p


class FirstPublicationInventory(unittest.TestCase):
    def inspect(self, info, scripts=(), domains=(), stage='preflight'):
        account='a'*32
        calls=[]
        def transport(method,path,body=None):
            calls.append((method,path,body))
            self.assertEqual((method,body),('GET',None))
            if path=='/accounts/'+account:
                return dict(success=True,result=dict(id=account))
            rows=[dict(id=name) for name in scripts] if path.endswith('/scripts') else list(domains)
            response=dict(success=True,result=rows)
            if info is not None:response['result_info']=copy.deepcopy(info)
            return response
        with patch.dict(os.environ,{'REVISION':'a'*40}):
            result=p.inspect_provider(account,transport,stage)
        self.assertEqual(len(calls),3)
        self.assertFalse(result['mutationsPerformed'])
        return result

    def test_unfiltered_single_page_allows_absent_empty_and_consistent_partial_metadata(self):
        for info in [None,{},dict(page=1),dict(count=0),dict(total_count=0),dict(total_pages=0),dict(total_pages=1),dict(per_page=0),dict(page=1,count=0,total_count=0,total_pages=1,per_page=100)]:
            with self.subTest(info=info):
                self.assertEqual(self.inspect(info)['state'],'target_absent_verified')
        domains=[dict(hostname='unrelated.example.invalid',service='unrelated-worker')]
        for info in [None,{},dict(page=1),dict(count=1),dict(total_count=1),dict(total_pages=1),dict(per_page=100)]:
            with self.subTest(info=info):
                self.assertEqual(self.inspect(info,['unrelated-worker'],domains)['state'],'target_absent_verified')

    def test_present_metadata_types_or_contradictions_fail_closed(self):
        bad=[dict(page=0),dict(page=2),dict(count=1),dict(total_count=1),dict(total_pages=2),[],False,'1']
        for field in ['page','per_page','count','total_count','total_pages']:
            for value in [True,False,1.0,'1',-1,None]:bad.append({field:value})
        for info in bad:
            with self.subTest(info=info),self.assertRaises((RuntimeError,ValueError)):
                self.inspect(info)

    def test_first_publish_requires_absence_even_when_existing_host_matches(self):
        with self.assertRaisesRegex(ValueError,'first_publication_target_must_be_absent'):
            self.inspect(None,[p.WORKER],[dict(hostname=p.HOSTNAME,service=p.WORKER)])
        for row in [dict(hostname=p.HOSTNAME,service='other'),dict(hostname='other.example.invalid',service=p.WORKER)]:
            with self.subTest(row=row),self.assertRaisesRegex(ValueError,'hostname_or_worker_collision'):
                self.inspect(None,[p.WORKER],[row])


if __name__=='__main__':unittest.main(verbosity=2)
