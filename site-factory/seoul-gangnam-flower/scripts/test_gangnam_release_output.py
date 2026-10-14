"""Mutation tests of actual Gangnam production output; no network/provider calls."""
import builtins
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import gangnam_release_output as output

ROOT=Path(__file__).resolve().parents[1]

class ProductionOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mode=json.loads(subprocess.check_output(['node',str(ROOT/'scripts/gangnam_release.mjs'),'--json'],cwd=ROOT,text=True))
        assert cls.mode['mode']=='production','Build actual production output before these mutation tests'
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.dist=Path(self.temp.name)/'dist';shutil.copytree(ROOT/'dist',self.dist)
        self.addCleanup(self.temp.cleanup)
    def inspect(self):return output.inspect_dist(self.dist,self.mode)
    def replace(self,file,old,new):
        p=self.dist/file;raw=p.read_text();assert old in raw; p.write_text(raw.replace(old,new))
        with self.assertRaises(AssertionError):self.inspect()
    def test_actual_production_contract(self):self.assertEqual(len(self.inspect()['sitemapUrls']),5)
    def test_gwanak_canonical(self):self.replace('index.html',output.ORIGIN,'https://seoul-gwanak.fwith.kr')
    def test_wrong_revision(self):self.replace('index.html',self.mode['revision'],'0'*40)
    def test_home_noindex(self):self.replace('index.html','content="index,follow"','content="noindex,nofollow,noarchive"')
    def test_directory_must_be_indexable(self):self.replace('regions/index.html','content="index,follow"','content="noindex,follow"')
    def test_404_must_be_noindex(self):self.replace('404.html','content="noindex,nofollow,noarchive"','content="index,follow"')
    def test_gwanak_sitemap(self):self.replace('sitemap-0.xml',output.ORIGIN,'https://seoul-gwanak.fwith.kr')
    def test_missing_directory_sitemap(self):self.replace('sitemap-0.xml',output.ORIGIN+'/regions/</loc>',output.ORIGIN+'/foreign/</loc>')
    def test_sitemap_self_reference(self):self.replace('sitemap-index.xml','sitemap-0.xml','sitemap-index.xml')
    def test_orphan_sitemap(self):
        (self.dist/'orphan.xml').write_text('<urlset/>')
        with self.assertRaises(AssertionError):self.inspect()
    def test_wrong_robots(self):self.replace('robots.txt','Allow: /','Disallow: /')
    def test_global_noindex_header(self):
        with (self.dist/'_headers').open('a') as f:f.write('  X-Robots-Tag: noindex\n')
        with self.assertRaises(AssertionError):self.inspect()
    def test_proof_bytes_changed(self):self.replace(output.PROOF['path'].lstrip('/'),'39c4ed924bc6084c670a963c26d9f018','wrong-proof')
    def test_gwanak_proof_origin(self):
        with self.assertRaises(AssertionError):output.inspect_dist(self.dist,self.mode,{**output.PROOF,'origin':'https://seoul-gwanak.fwith.kr'})
    def test_executable_artifact(self):
        (self.dist/'_worker.js').write_text('INVALID TEST')
        with self.assertRaises(AssertionError):self.inspect()
    def test_production_qa_never_imports_historical_release(self):
        original=builtins.__import__
        def checked(name,*args,**kwargs):
            if name.split('.')[0] in {'qa_gwanak','release_mode'}:raise AssertionError('Historical release import forbidden: '+name)
            return original(name,*args,**kwargs)
        with patch('builtins.__import__',checked):
            import qa_gangnam, qa_directory_spacing, qa_source_link_amendment
            qa_gangnam.inspect(ROOT,False)
            qa_directory_spacing.inspect(ROOT)
            qa_source_link_amendment.inspect(ROOT)
    def test_missing_article(self):
        (self.dist/'regions/gangnam-event-wreath/index.html').unlink()
        with self.assertRaises(AssertionError):self.inspect()

if __name__=='__main__':unittest.main()
