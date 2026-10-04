"""Synthetic HTTP and journal fixtures only; no live submissions."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import indexnow_finalize as mod

ORIGIN = 'https://test.example'
REVISION = 'a' * 40
KEY = 'test-public-ownership-key'


def html(url=ORIGIN+'/', robots='index,follow', revision=REVISION, extra=''):
    return f'<meta name="site-factory-revision" content="{revision}"><meta name="robots" content="{robots}"><link rel="canonical" href="{url}">{extra}<h1>Fixture</h1>'


class MemoryJournal:
    def __init__(self): self.items=[]; self.fail=False
    def records(self): return list(self.items)
    def write(self, item):
        if self.fail: raise RuntimeError('unavailable')
        self.items.append(item)


class FinalizationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.dist=self.root/'dist'; self.dist.mkdir()
        self.site={'siteKey':'test','siteUrl':ORIGIN,'productionEnabled':True,'launchMode':'live','indexnowKey':KEY}
        self.rows={ORIGIN+'/':(200,html(),{}), ORIGIN+'/detail/':(200,html(ORIGIN+'/detail/'),{}),
            ORIGIN+'/robots.txt':(200,'User-agent: *\nAllow: /\n',{}),
            ORIGIN+'/sitemap-index.xml':(200,f'<sitemapindex><sitemap><loc>{ORIGIN}/sitemap-0.xml</loc></sitemap></sitemapindex>',{}),
            ORIGIN+'/sitemap-0.xml':(200,f'<urlset><url><loc>{ORIGIN}/</loc></url><url><loc>{ORIGIN}/detail/</loc></url></urlset>',{}),
            ORIGIN+'/'+KEY+'.txt':(200,KEY,{})}
        for url,(_,body,_) in self.rows.items():
            rel=url[len(ORIGIN):].lstrip('/'); p=self.dist/(rel+'index.html' if url.endswith('/') else rel)
            p.parent.mkdir(parents=True,exist_ok=True); p.write_text(body)
        self.journal=MemoryJournal(); self.posts=[]; self.statuses=[200]; self.sleeps=[]
    def transport(self,method,url,payload=None):
        if method=='GET': return self.rows[url]
        self.posts.append(payload)
        status=self.statuses.pop(0)
        if isinstance(status,Exception): raise status
        return status,'',{}
    def run_it(self):return mod.finalize(self.site,REVISION,self.root,self.journal,self.transport,sleep=self.sleeps.append)
    def mutate(self,url,body=None,status=None,headers=None):
        old=self.rows[url];self.rows[url]=(old[0] if status is None else status,old[1] if body is None else body,old[2] if headers is None else headers)
    def blocked(self,reason=None):
        with self.assertRaisesRegex(ValueError,reason or '.') : self.run_it()
        self.assertEqual(self.posts,[])
    def test_received_and_exact_urls(self):
        result=self.run_it(); self.assertEqual(result['state'],'received'); self.assertEqual(result['urlCount'],2)
        self.assertEqual(self.posts[0]['urlList'],[ORIGIN+'/',ORIGIN+'/detail/'])
        self.assertEqual([r['state'] for r in self.journal.items],['started','received'])
        self.assertNotIn(KEY,json.dumps(self.journal.items))
    def test_202_is_pending_validation(self):
        self.statuses=[202];self.assertEqual(self.run_it()['state'],'received_key_validation_pending')
    def test_duplicate_across_requests_uses_previous_receipt(self):
        self.run_it(); self.assertEqual(self.run_it()['state'],'already_received');self.assertEqual(len(self.posts),1)
    def test_prior_started_blocks_cross_run_retry(self):
        self.run_it();self.journal.items=self.journal.items[:1];self.posts=[]
        self.blocked('prior_submission_outcome_uncertain')
    def test_missing_or_invalid_key(self):
        for key in ('','bad/../key'):
            self.site['indexnowKey']=key;self.blocked('ownership_key_not_configured')
    def test_key_missing_mismatch_and_redirect(self):
        for status,body in ((404,''),(200,'wrong'),(301,KEY)):
            self.mutate(ORIGIN+'/'+KEY+'.txt',body,status);self.blocked('ownership_file_not_verified')
    def test_closed_gate(self):
        self.site['productionEnabled']=False;self.blocked('production_gate_closed')
    def test_mixed_or_duplicate_revision(self):
        for body in (html(ORIGIN+'/detail/',revision='b'*40),html(ORIGIN+'/detail/',extra=f'<meta name="site-factory-revision" content="{REVISION}">')):
            self.mutate(ORIGIN+'/detail/',body);self.blocked('page_revision_mismatch')
    def test_page_404_or_redirect(self):
        for status in (404,301,403):
            self.mutate(ORIGIN+'/detail/',status=status);self.blocked('page_not_http200')
    def test_noindex_and_hidden_duplicate(self):
        for body in (html(ORIGIN+'/detail/',robots='noindex,follow'),html(ORIGIN+'/detail/',extra='<meta name="robots" content="noindex">'),html(ORIGIN+'/detail/',extra='<meta name="yeti" content="none">')):
            self.mutate(ORIGIN+'/detail/',body);self.blocked()
    def test_blocking_headers(self):
        for value in ('noindex','none','Yeti: noindex'):
            self.mutate(ORIGIN+'/detail/',headers={'x-robots-tag':value});self.blocked('page_header_not_indexable')
    def test_foreign_duplicate_and_wrong_canonical(self):
        for body in (html('https://evil.example/detail/'),html(ORIGIN+'/wrong/'),html(ORIGIN+'/detail/',extra=f'<link rel="canonical" href="{ORIGIN}/detail/">')):
            self.mutate(ORIGIN+'/detail/',body);self.blocked()
    def test_robots_yeti_disallow(self):
        self.mutate(ORIGIN+'/robots.txt','User-agent: Yeti\nDisallow: /detail/\n\nUser-agent: *\nAllow: /\n');self.blocked('robots_disallows_sitemap_url')
    def test_more_specific_disallow_beats_root_allow(self):
        self.mutate(ORIGIN+'/robots.txt','User-agent: *\nAllow: /\nDisallow: /detail/\n')
        self.blocked('robots_disallows_sitemap_url')
    def test_longer_allow_and_equal_allow_tie(self):
        self.assertTrue(mod.robots_allows('User-agent: *\nDisallow: /\nAllow: /detail/\n','Yeti',ORIGIN+'/detail/'))
        self.assertTrue(mod.robots_allows('User-agent: *\nDisallow: /detail/\nAllow: /detail/\n','Yeti',ORIGIN+'/detail/'))
    def test_real_article_snapshot_mismatch(self):
        (self.dist/'detail/index.html').write_text(html(ORIGIN+'/detail/',extra='<article data-snapshot-id="approved" data-page-key="detail"></article>'))
        self.mutate(ORIGIN+'/detail/',html(ORIGIN+'/detail/',extra='<article data-snapshot-id="wrong" data-page-key="detail"></article>'))
        self.blocked('page_snapshot_mismatch')
    def test_repeated_response_headers_preserve_noindex(self):
        from email.message import Message
        h=Message();h.add_header('X-Robots-Tag','noindex');h.add_header('X-Robots-Tag','index,follow')
        class Response:
            code=200;headers=h
            def read(self,*args):return b'ok'
            def __enter__(self):return self
            def __exit__(self,*args):pass
        with patch.object(mod,'build_opener') as opener:
            opener.return_value.open.return_value=Response()
            status,body,headers=mod.request('GET',ORIGIN+'/')
        self.assertEqual(headers['x-robots-tag'],'noindex, index,follow')
        self.assertTrue(mod.blocking(headers['x-robots-tag']))
    def test_cross_host_sitemap(self):
        self.mutate(ORIGIN+'/sitemap-index.xml','<sitemapindex><sitemap><loc>https://evil.example/sitemap.xml</loc></sitemap></sitemapindex>');self.blocked('foreign_or_unsafe_url')
    def test_extra_live_url(self):
        self.mutate(ORIGIN+'/sitemap-0.xml',self.rows[ORIGIN+'/sitemap-0.xml'][1].replace('</urlset>',f'<url><loc>{ORIGIN}/extra/</loc></url></urlset>'));self.blocked('live_sitemap_differs_from_exact_source')
    def test_duplicate_sitemap_url(self):
        self.mutate(ORIGIN+'/sitemap-0.xml',self.rows[ORIGIN+'/sitemap-0.xml'][1].replace('</urlset>',f'<url><loc>{ORIGIN}/</loc></url></urlset>'));self.blocked('duplicate_sitemap_url')
    def test_xml_entities_rejected(self):
        self.mutate(ORIGIN+'/sitemap-0.xml','<!DOCTYPE x [<!ENTITY evil SYSTEM "file:///etc/passwd">]><urlset/>');self.blocked('unsafe_sitemap_xml')
    def test_uncertain_and_5xx_not_retried(self):
        for status in (500,503,TimeoutError('private url or key')):
            with self.subTest(status=status):
                self.journal=MemoryJournal();self.posts=[];self.statuses=[status]
                with self.assertRaises(ValueError):self.run_it()
                self.assertEqual(len(self.posts),1);self.assertEqual(self.journal.items[-1]['state'],'unknown')
                self.posts=[];self.blocked('prior_submission_outcome_uncertain')
    def test_400_403_422_not_retried(self):
        for status in (400,403,422):
            self.journal=MemoryJournal();self.posts=[];self.statuses=[status]
            with self.assertRaisesRegex(ValueError,'indexnow_rejected'):self.run_it()
            self.assertEqual(len(self.posts),1);self.assertEqual(self.journal.items[-1]['state'],'rejected')
    def test_429_bounded_retry(self):
        self.statuses=[429,429,200];self.assertEqual(self.run_it()['state'],'received')
        self.assertEqual(len(self.posts),3);self.assertEqual(self.sleeps,[10,20])
    def test_429_max_attempts(self):
        self.statuses=[429,429,429]
        with self.assertRaisesRegex(ValueError,'429'):self.run_it()
        self.assertEqual(len(self.posts),3)
    def test_journal_failure_before_post(self):
        self.journal.fail=True
        with self.assertRaises(RuntimeError):self.run_it()
        self.assertFalse(self.posts)
    def test_public_change_between_validations(self):
        real=mod.verify_public; count=0
        def verify(*args):
            nonlocal count
            count+=1
            if count==2:self.mutate(ORIGIN+'/',html(revision='b'*40))
            return real(*args)
        with patch.object(mod,'verify_public',verify):self.blocked('page_revision_mismatch')
    def test_snapshot_mismatch(self):
        p=self.dist/'detail/index.html';p.write_text(html(ORIGIN+'/detail/',extra='<meta name="site-factory-snapshot-id" content="approved">'))
        self.blocked('page_snapshot_mismatch')


class WorkflowTests(unittest.TestCase):
    def test_no_silent_skip_or_extra_privileges(self):
        import yaml
        root=Path(__file__).resolve().parents[3]
        raw=(root/'.github/workflows/site-production-deploy.yml').read_text(); doc=yaml.safe_load(raw)
        self.assertNotIn('Record skipped IndexNow',raw)
        self.assertNotIn("if: steps.target.outputs.indexnow != ''",raw)
        for job in doc['jobs'].values():self.assertEqual(job['permissions'],{'contents':'read','issues':'write'})
        steps=doc['jobs']['finalize-existing-public']['steps']
        self.assertFalse(any('CLOUDFLARE' in json.dumps(x) or 'wrangler' in json.dumps(x) for x in steps))
        self.assertIn('live_verified_indexnow_received',raw)
    def test_receipts_read_across_existing_issues_only(self):
        j=mod.Journal('owner/repo',12)
        self.assertEqual(j.read_path,'repos/owner/repo/issues/comments')
        self.assertEqual(j.path,'repos/owner/repo/issues/12/comments')


if __name__=='__main__':unittest.main()
