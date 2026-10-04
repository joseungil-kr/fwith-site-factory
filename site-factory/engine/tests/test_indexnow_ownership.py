"""Synthetic source/build fixtures; no credentials, deployments or submissions."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import indexnow_ownership as mod


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.repo=self.root/'repo';self.repo.mkdir()
        self.git('init','-q');self.git('config','user.email','fixture@example.invalid');self.git('config','user.name','Test fixture')
        (self.repo/'content.txt').write_text('unchanged content');self.git('add','.');self.git('commit','-qm','fixture baseline')
        old=self.git('rev-parse','HEAD').strip();self.key='fixture-public-ownership-value';path='site/public/'+self.key+'.txt'
        p=self.repo/path;p.parent.mkdir(parents=True);p.write_text(self.key+'\n');self.git('add','.');self.git('commit','-qm','fixture key only')
        new=self.git('rev-parse','HEAD').strip()
        self.site={'siteUrl':'https://fixture.example','root':'site','indexnowKey':self.key,'approvedRevision':new,
            'indexnowOwnership':{'approved':True,'previousRevision':old,'revision':new,'origin':'https://fixture.example',
                'path':path,'keySha256':hashlib.sha256(self.key.encode()).hexdigest()}}
    def git(self,*args):return subprocess.check_output(['git','-C',str(self.repo),*args],stderr=subprocess.PIPE).decode()
    def verify(self):return mod.verify_source(self.site,self.site['approvedRevision'],self.repo)
    def test_exact_single_regular_file(self):self.assertEqual(self.verify()['state'],'ownership_source_verified')
    def test_whole_repository_unrelated_change_rejected(self):
        (self.repo/'other.txt').write_text('out of scope');self.git('add','.');self.git('commit','-qm','bad extra')
        new=self.git('rev-parse','HEAD').strip();self.site['approvedRevision']=new;self.site['indexnowOwnership']['revision']=new
        with self.assertRaisesRegex(ValueError,'one_file'):self.verify()
    def test_changed_content_rejected(self):
        (self.repo/'content.txt').write_text('modified');self.git('add','.');self.git('commit','-qm','bad content')
        new=self.git('rev-parse','HEAD').strip();self.site['approvedRevision']=new;self.site['indexnowOwnership']['revision']=new
        with self.assertRaisesRegex(ValueError,'one_file'):self.verify()
    def test_symlink_key_rejected(self):
        p=self.repo/self.site['indexnowOwnership']['path'];p.unlink();p.symlink_to('../../content.txt');self.git('add','.');self.git('commit','-qm','bad symlink')
        new=self.git('rev-parse','HEAD').strip();self.site['approvedRevision']=new;self.site['indexnowOwnership']['revision']=new
        with self.assertRaisesRegex(ValueError,'not_regular'):self.verify()
    def test_missing_approval_digest_origin_path(self):
        for key,value in [('approved',False),('keySha256','bad'),('origin','https://other.example'),('path','other.txt')]:
            original=copy.deepcopy(self.site);self.site['indexnowOwnership'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.verify()
            self.site=original
    def test_current_checkout_and_approved_revision_bound(self):
        self.site['approvedRevision']='f'*40
        with self.assertRaises(ValueError):self.verify()
    def test_future_release_keeps_established_key(self):
        self.site['approvedRevision']='f'*40
        self.assertTrue(mod.key_allowed(self.site))
        with self.assertRaisesRegex(ValueError,'revision_mismatch'):mod.amendment(self.site,'f'*40)
    def builds(self):
        old=self.root/'old';new=self.root/'new'
        for base,revision in [(old,self.site['indexnowOwnership']['previousRevision']),(new,self.site['approvedRevision'])]:
            (base/'dist').mkdir(parents=True)
            (base/'dist/index.html').write_text('<meta name="site-factory-revision" content="'+revision+'"><h1>Same content</h1>')
            (base/'dist/style.css').write_text('identical bytes')
        (new/'dist'/ (self.key+'.txt')).write_text(self.key+'\n')
        return old,new
    def test_rendered_only_key_and_revision_delta(self):
        old,new=self.builds();self.assertEqual(mod.compare_artifacts(self.site,old,new)['preservedFiles'],2)
    def test_rendered_different_content_rejected(self):
        old,new=self.builds();(new/'dist/style.css').write_text('changed')
        with self.assertRaisesRegex(ValueError,'content_changed'):mod.compare_artifacts(self.site,old,new)
    def test_rendered_extra_or_missing_file_rejected(self):
        old,new=self.builds();(new/'dist/extra.txt').write_text('bad')
        with self.assertRaisesRegex(ValueError,'scope_changed'):mod.compare_artifacts(self.site,old,new)

if __name__=='__main__':unittest.main()
