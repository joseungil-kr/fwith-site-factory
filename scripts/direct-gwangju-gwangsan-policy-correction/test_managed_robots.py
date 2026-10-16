"""Offline byte-exact policy composition tests, not public deployment evidence."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from email.message import Message
import managed_robots as m
import publish as p
import test_publish_correction as test_publish

class ManagedRobotsTests(unittest.TestCase):
    def source(self,origin):
        return ('User-agent: *\nAllow: /\nSitemap: '+origin+'/sitemap-index.xml\n').encode()
    def check(self,body=None,origin=None,expected=None,urls=None):
        origin=origin or p.ORIGIN;source=self.source(origin)
        return m.verify(body if body is not None else m.MANAGED_PREFIX+source,expected or m.digest(source),origin,urls or [origin+'/'])
    def test_pinned_prefix_identity(self):
        self.assertEqual(len(m.MANAGED_PREFIX),2676)
        self.assertEqual(m.digest(m.MANAGED_PREFIX),'3073d1e371afb3271c7666148766fedc5145f7d8440f7114062db79b7bd58add')
        self.assertEqual(m.MANAGED_PREFIX.count(m.BEGIN),1);self.assertEqual(m.MANAGED_PREFIX.count(m.END),1)
    def test_original_and_exact_composite_only_for_each_separate_source(self):
        for origin in ['https://gwangyang.fwith.kr','https://naju.fwith.kr','https://gwangju-gwangsan.fwith.kr']:
            with self.subTest(origin=origin):
                source=self.source(origin);plain=self.check(source,origin);composite=self.check(origin=origin)
                self.assertEqual(plain['managedComposites'],0);self.assertEqual(composite['managedComposites'],1)
                self.assertNotEqual(composite['rawBodySha256'],composite['sourceSuffixSha256'])
                self.assertEqual(plain['rawBodySha256'],composite['sourceSuffixSha256'])
                self.assertTrue(composite['rawBodyUnmodified'])
    def test_every_prefix_byte_mutation_rejected(self):
        raw=m.MANAGED_PREFIX+self.source(p.ORIGIN)
        for i in range(len(m.MANAGED_PREFIX)):
            with self.subTest(offset=i),self.assertRaises(ValueError):self.check(raw[:i]+bytes([raw[i]^1])+raw[i+1:])
    def test_every_source_suffix_byte_mutation_rejected(self):
        source=self.source(p.ORIGIN)
        for i in range(len(source)):
            with self.subTest(offset=i),self.assertRaises(ValueError):self.check(m.MANAGED_PREFIX+source[:i]+bytes([source[i]^1])+source[i+1:])
    def test_policy_marker_sitemap_and_extra_content_mutations_rejected(self):
        raw=m.MANAGED_PREFIX+self.source(p.ORIGIN)
        mutations=[b'x'+raw,raw+b'x',raw+b'\n',raw[:-1],raw.replace(b'\n',b'\r\n'),raw.replace(m.BEGIN,b'',1),raw.replace(m.END,b'',1),m.MANAGED_PREFIX+raw,raw+m.BEGIN,raw+m.END,raw.replace(m.BEGIN,m.END,1),raw.replace(b'search=yes',b'search=no'),raw.replace(b'ai-train=no',b'ai-train=yes'),raw.replace(b'use=reference',b'use=full'),raw.replace(b'User-agent: GPTBot',b'User-agent: Yeti'),raw.replace(b'User-agent: GoogleOther',b'User-agent: Googlebot'),raw+b'User-agent: Googlebot\nDisallow: /\n',raw+b'User-agent: Yeti\nDisallow: /\n',raw.replace(b'Sitemap: ',b'Sitemap: https://other.example/\nSitemap: '),raw.replace(b'/sitemap-index.xml',b'/other-sitemap.xml'),raw+b'Allow: /private/\n',raw+b'Disallow: /private/\n',raw.replace(p.HOSTNAME.encode('ascii'),b'naju.fwith.kr'),raw.replace(b'User-agent: *\nAllow: /\nSitemap:',b'User-agent: *\nDisallow: /\nSitemap:')]
        for i,b in enumerate(mutations):
            with self.subTest(case=i),self.assertRaises(ValueError):self.check(b)
    def test_contract_origin_hash_and_scope_mutations_rejected(self):
        for expected in ['0'*64,'a'*63,True,None]:
            with self.subTest(expected=expected),self.assertRaises(ValueError):m.verify(m.MANAGED_PREFIX+self.source(p.ORIGIN),expected,p.ORIGIN,[p.ORIGIN+'/'])
        for origin in ['http://gwangyang.fwith.kr','https://gwangyang.fwith.kr/','https://evil.example','https://gwangyang.fwith.kr@evil.example']:
            with self.subTest(origin=origin),self.assertRaises(ValueError):m.verify(b'',m.digest(self.source(p.ORIGIN)),origin,[origin+'/'])
        for urls in [[],[p.ORIGIN+'/']*2,['https://evil.example/'],[p.ORIGIN+'/other/'],[p.ORIGIN+'/?x=1'],[p.ORIGIN+'/#x']]:
            with self.subTest(urls=urls),self.assertRaises(ValueError):m.verify(m.MANAGED_PREFIX+self.source(p.ORIGIN),m.digest(self.source(p.ORIGIN)),p.ORIGIN,urls)
    def test_headers_require_plain_text_and_search_indexability(self):
        for headers in [{'content-type':'text/html'},{'content-type':'text/plain; charset=utf-8, text/html'},{'content-type':'text/plain; charset=utf-16'},{'content-type':'text/plain; charset=utf-8; charset=utf-8'},{'content-type':'text/plain; boundary=abc'},{'content-type':'text/plain\r\n'},{'content-type':'text/plain','cf-mitigated':'challenge'},{'content-type':'text/plain','x-robots-tag':'noindex'},{'content-type':'text/plain','x-robots-tag':'googlebot: none'},{}]:
            with self.subTest(headers=headers),self.assertRaises(ValueError):m.verify_headers(headers)
        m.verify_headers({'content-type':'text/plain; charset=utf-8'})
        duplicate=Message();duplicate['Content-Type']='text/plain';duplicate['X-Robots-Tag']='index';duplicate['X-Robots-Tag']='noindex'
        with self.assertRaises(ValueError):m.verify_headers(duplicate)
    def test_raw_composite_retained_for_indexnow_semantics(self):
        fixture=test_publish.PublisherTests();fixture.setUp();self.addCleanup(fixture.doCleanups);fixture.fixture_release();p.helpers();import indexnow_finalize as n
        with test_publish.working(fixture.root):
            p.artifact(write_config=True);raw=m.MANAGED_PREFIX+self.source(p.ORIGIN)
            with patch.object(n,'request',return_value=(200,raw.decode(),{'content-type':'text/plain'})):
                status,body,_=p.observed_indexnow_request('GET',p.ORIGIN+'/robots.txt')
            self.assertEqual(body.encode(),raw)
            row=json.loads(Path('indexnow-http-observations.json').read_text())[-1]
            self.assertEqual(row['bodySha256'],m.digest(raw));self.assertEqual(row['robotsVerification']['managedComposites'],1)
            for agent in ('Googlebot','Yeti','bingbot','IndexNow'):self.assertTrue(n.robots_allows(body,agent,p.ORIGIN+'/'))
            for agent in ('GPTBot','Baiduspider','PetalBot'):self.assertFalse(n.robots_allows(body,agent,p.ORIGIN+'/'))
    def test_nonrobots_static_indexnow_mutation_still_rejected(self):
        fixture=test_publish.PublisherTests();fixture.setUp();self.addCleanup(fixture.doCleanups);fixture.fixture_release();p.helpers();import indexnow_finalize as n
        with test_publish.working(fixture.root):
            p.artifact(write_config=True)
            for path in [p.output.PROOF['path'],'/sitemap-index.xml','/sitemap-0.xml']:
                raw=(Path('release/dist')/path.lstrip('/')).read_text()
                with self.subTest(path=path),patch.object(n,'request',return_value=(200,raw+'\n',{})),self.assertRaisesRegex(ValueError,'indexnow_static_digest_mismatch'):p.observed_indexnow_request('GET',p.ORIGIN+path)

if __name__=='__main__':unittest.main()
