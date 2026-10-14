"""Mutation tests of actual Songpa production output; no network/provider calls."""
import builtins
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import songpa_release_output as output

ROOT=Path(__file__).resolve().parents[1]

class ProductionOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mode=json.loads(subprocess.check_output(['node',str(ROOT/'scripts/songpa_release.mjs'),'--json'],cwd=ROOT,text=True))
        assert cls.mode['mode']=='production','Build actual production output before these mutation tests'
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.dist=Path(self.temp.name)/'dist';shutil.copytree(ROOT/'dist',self.dist)
        self.addCleanup(self.temp.cleanup)
    def inspect(self):return output.inspect_dist(self.dist,self.mode)
    def replace(self,file,old,new):
        p=self.dist/file;raw=p.read_text();assert old in raw; p.write_text(raw.replace(old,new))
        with self.assertRaises(AssertionError):self.inspect()
    def test_actual_production_contract(self):self.assertEqual(len(self.inspect()['sitemapUrls']),3)
    def test_gwanak_canonical(self):self.replace('index.html',output.ORIGIN,'https://seoul-gwanak.fwith.kr')
    def test_wrong_revision(self):self.replace('index.html',self.mode['revision'],'0'*40)
    def test_home_noindex(self):self.replace('index.html','content="index,follow"','content="noindex,nofollow,noarchive"')
    def test_directory_must_be_noindex_follow(self):self.replace('regions/index.html','content="noindex,follow"','content="index,follow"')
    def test_404_must_be_noindex(self):self.replace('404.html','content="noindex,nofollow,noarchive"','content="index,follow"')
    def test_gwanak_sitemap(self):self.replace('sitemap-0.xml',output.ORIGIN,'https://seoul-gwanak.fwith.kr')
    def test_directory_in_sitemap(self):self.replace('sitemap-0.xml',output.ORIGIN+'/regions/songpa-condolence-wreath/</loc>',output.ORIGIN+'/regions/</loc>')
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
    def test_404_canonical_forbidden(self):self.replace('404.html','</head>','<link rel="canonical" href="'+output.ORIGIN+'/404.html"/></head>')
    def test_404_social_forbidden(self):self.replace('404.html','</head>','<meta property="og:url" content="'+output.ORIGIN+'/404.html"/></head>')
    def test_duplicate_robots_forbidden(self):self.replace('index.html','</head>','<meta name="robots" content="index,follow"/></head>')
    def test_missing_article(self):
        (self.dist/'regions/songpa-condolence-wreath/index.html').unlink()
        with self.assertRaises(AssertionError):self.inspect()

if __name__=='__main__':unittest.main()
