"""Exact source-amendment fixtures only, never real code/content approvals."""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch
import test_reviewed_initial_bindings as fixtures
import test_whole_initial as existing
import whole_initial as whole
import batch_barrier as barrier


def amended_fixture():
    site='pyeongtaek-flower-v2'
    batch,evidence,git,profile,binding=fixtures.regional_fixture(site,runtime_files=True)
    root='site-factory/pyeongtaek-flower'
    files={}
    for path in sorted(whole.RUNTIME_RECONCILIATION_PATHS):
        original=git.documents[(existing.BOOTSTRAP,root+'/'+path)]
        amended=original+b'\n'
        files[path]={'beforeSha256':hashlib.sha256(original).hexdigest(),
                     'afterSha256':hashlib.sha256(amended).hexdigest()}
        for (revision,name) in list(git.documents):
            if name==root+'/'+path and revision!=existing.BOOTSTRAP:
                git.documents[(revision,name)]=amended
    binding['runtimeAmendment']={'files':files,
        'reviewEvidenceUrl':'https://github.com/joseungil-kr/fwith-site-factory/issues/999997'}
    registry_path=(existing.BASE,'.github/site-factory-sites.json')
    registry=json.loads(git.documents[registry_path]);target=registry['sites'][site]
    target['initialRuntimeAmendmentSha256']=barrier.digest(binding['runtimeAmendment'])
    git.documents[registry_path]=existing.encode(registry)
    batch['productsSha256']=hashlib.sha256(git.documents[(existing.BASE,root+'/src/data/products.json')]).hexdigest()
    batch['membershipHash']=barrier.identity(batch);evidence['membershipHash']=batch['membershipHash']
    for item in evidence['items']:item['reviewerApproval']['membershipHash']=batch['membershipHash']
    return batch,evidence,git,profile,binding,target


class ReviewedRuntimeAmendmentTests(unittest.TestCase):
    def check(self,data):
        batch,evidence,git,profile,binding,target=data
        with patch.dict(whole.ALL_INITIAL_SOURCE_PROFILES,{'pyeongtaek-flower-v2':profile}), \
                patch.dict(whole.ADDITIONAL_REVIEWED_RELEASES,{'pyeongtaek-flower-v2':binding}):
            return barrier.check(batch,evidence,git)

    def test_only_exact_bound_five_file_amendment_passes_without_changing_bootstrap(self):
        data=amended_fixture();git=data[2]
        before={k:v for k,v in git.documents.items() if k[0]==existing.BOOTSTRAP}
        self.assertEqual(self.check(data)['state'],'staging_complete')
        self.assertEqual(before,{k:v for k,v in git.documents.items() if k[0]==existing.BOOTSTRAP})

    def test_missing_or_wrong_binding_evidence_paths_and_hashes_fail(self):
        for change in ('unbound','null','review_url','missing_path','extra_path','wrong_before','wrong_after','registry'):
            data=amended_fixture();binding=data[4];amendment=binding['runtimeAmendment']
            if change=='unbound':binding.pop('runtimeAmendment')
            elif change=='null':binding['runtimeAmendment']=None
            elif change=='review_url':amendment['reviewEvidenceUrl']='https://example.com/'
            elif change=='missing_path':amendment['files'].pop('src/lib/catalog.mjs')
            elif change=='extra_path':amendment['files']['src/lib/fixture.mjs']=copy.deepcopy(amendment['files']['src/lib/catalog.mjs'])
            elif change=='wrong_before':amendment['files']['src/lib/catalog.mjs']['beforeSha256']='0'*64
            elif change=='wrong_after':amendment['files']['src/lib/catalog.mjs']['afterSha256']='0'*64
            else:data[5]['initialRuntimeAmendmentSha256']='0'*64
            # Keep the registry mirror consistent except for the explicit
            # mismatch case, so each deeper allowlist/hash gate is exercised.
            if change!='registry' and binding.get('runtimeAmendment') is not None:
                data[5]['initialRuntimeAmendmentSha256']=barrier.digest(binding['runtimeAmendment'])
            registry=json.loads(data[2].documents[(existing.BASE,'.github/site-factory-sites.json')])
            registry['sites']['pyeongtaek-flower-v2']=data[5]
            data[2].documents[(existing.BASE,'.github/site-factory-sites.json')]=existing.encode(registry)
            with self.subTest(change=change),self.assertRaises(ValueError):self.check(data)

    def test_unbound_assets_code_catalog_and_bootstrap_changes_fail(self):
        for revision,path in [(existing.FINAL,'src/lib/fixture.mjs'),(existing.FINAL,'public/images/fixture.png'),
                (existing.FINAL,'src/data/products.json'),(existing.BASE,'src/lib/catalog.mjs'),
                (existing.FINAL,'scripts/qa_static.py'),(existing.FINAL,'src/data/social-image-provenance.json'),
                (existing.BOOTSTRAP,'src/lib/catalog.mjs')]:
            data=amended_fixture();key=(revision,'site-factory/pyeongtaek-flower/'+path)
            data[2].documents[key]+=b'changed'
            with self.subTest(revision=revision,path=path),self.assertRaises(ValueError):self.check(data)

if __name__=='__main__':unittest.main()
