"""Read-only synthetic tests. All IndexNow HTTP and journal writes are fixtures."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import blog_indexnow_finalize as blog
import indexnow_finalize as shared
from test_indexnow_finalize import MemoryJournal

ORIGIN = 'https://blog.fwith.kr'
REVISION = 'a' * 40
KEY = 'fixture-blog-public-ownership'
BASE = Path(__file__).resolve().parents[3]


def html(url):
    return f'<meta name="site-factory-revision" content="{REVISION}"><meta name="robots" content="index,follow"><link rel="canonical" href="{url}"><h1>Fixture</h1>'


class BlogAdapterTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name); self.dist = self.root/'dist'; self.dist.mkdir()
        self.registry = {'sites': {'blog-fwith': {
            'repo':'joseungil-kr/fwith-site-factory', 'branch':'site-factory-blog-fwith',
            'root':'site-factory/blog-fwith', 'siteUrl':ORIGIN,
            'worker':'blog-fwith-prod-disabled', 'wranglerConfig':'wrangler.jsonc',
            'launchMode':'staging', 'productionEnabled':False, 'growthPaused':True,
            'autoDeploySnapshots':False, 'stagingBuildIsolation':False,
            'stagingWorker':'blog-fwith-guide-qa',
            'stagingUrl':'https://blog-fwith-guide-qa.joseungil.workers.dev'}}}
        self.site = self.registry['sites']['blog-fwith']
        self.site.update(blogIndexnowEnabled=True, indexnowKey=KEY)
        self.path = self.root/'registry.json'; self.save()
        self.rows = {
            ORIGIN+'/': (200, html(ORIGIN+'/'), {}),
            ORIGIN+'/posts/fixture/': (200, html(ORIGIN+'/posts/fixture/'), {}),
            ORIGIN+'/robots.txt': (200, 'User-agent: *\nAllow: /\n', {}),
            ORIGIN+'/sitemap-index.xml': (200, f'<sitemapindex><sitemap><loc>{ORIGIN}/sitemap-0.xml</loc></sitemap></sitemapindex>', {}),
            ORIGIN+'/sitemap-0.xml': (200, f'<urlset><url><loc>{ORIGIN}/</loc></url><url><loc>{ORIGIN}/posts/fixture/</loc></url></urlset>', {}),
            ORIGIN+'/'+KEY+'.txt': (200, KEY+'\n', {})}
        for url, (_, body, _) in self.rows.items():
            rel = url[len(ORIGIN):].lstrip('/')
            dest = self.dist/(rel+'index.html' if url.endswith('/') else rel)
            dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text(body)
        self.journal = MemoryJournal(); self.posts = []; self.statuses = [200]; self.sleeps = []
    def save(self): self.path.write_text(json.dumps(self.registry))
    def transport(self, method, url, payload=None):
        if method == 'GET': return self.rows[url]
        self.assertEqual(method, 'POST'); self.assertEqual(url, shared.ENDPOINT)
        self.posts.append(payload)
        status = self.statuses.pop(0)
        if isinstance(status, Exception): raise status
        return status, '', {}
    def run_it(self):
        return blog.submit(self.path, REVISION, self.root, self.journal, self.transport,
                           'https://github.com/example/run', self.sleeps.append)
    def blocked(self, reason):
        with self.assertRaisesRegex(ValueError, reason): self.run_it()
        self.assertEqual(self.posts, [])
    def test_receipt_uses_shared_guards_and_keeps_registry_unchanged(self):
        before = self.path.read_bytes(); result = self.run_it()
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(self.site['productionEnabled']); self.assertEqual(self.site['launchMode'], 'staging')
        self.assertEqual(result['state'], 'received'); self.assertEqual(result['searchIndexing'], 'not_verified')
        self.assertEqual(self.posts[0]['host'], 'blog.fwith.kr')
        self.assertEqual(self.posts[0]['keyLocation'], ORIGIN+'/'+KEY+'.txt')
        self.assertEqual([r['state'] for r in self.journal.items], ['started', 'received'])
        self.assertNotIn(KEY, json.dumps(self.journal.items))
    def test_missing_explicit_approval_is_blocked(self):
        del self.site['blogIndexnowEnabled']; self.save(); self.blocked('blog_indexnow_not_approved')
    def test_nonboolean_approval_is_blocked(self):
        self.site['blogIndexnowEnabled'] = 'true'; self.save(); self.blocked('blog_indexnow_not_approved')
    def test_generic_gate_changes_are_blocked(self):
        for name, value in [('productionEnabled',True), ('launchMode','live'), ('growthPaused',False), ('autoDeploySnapshots',True)]:
            with self.subTest(name=name):
                old = self.site[name]; self.site[name] = value; self.save()
                self.blocked('blog_registry_identity_mismatch')
                self.site[name] = old; self.save()
    def test_wrong_host_worker_branch_and_repo_blocked(self):
        for name in ['siteUrl','worker','branch','repo','root']:
            with self.subTest(name=name):
                old = self.site[name]; self.site[name] = 'wrong'; self.save()
                self.blocked('blog_registry_identity_mismatch')
                self.site[name] = old; self.save()
    def test_other_host_key_reuse_is_blocked(self):
        self.registry['sites']['other'] = {'indexnowKey':KEY}; self.save()
        self.blocked('blog_ownership_key_reused_from_other_site')
    def test_missing_key_is_blocked(self):
        del self.site['indexnowKey']; self.save(); self.blocked('ownership_key_not_configured')
    def test_invalid_key_is_blocked(self):
        self.site['indexnowKey'] = '../../other'; self.save(); self.blocked('ownership_key_not_configured')
    def test_built_proof_missing_is_blocked(self):
        (self.dist/(KEY+'.txt')).unlink(); self.blocked('blog_built_ownership_file_missing')
    def test_built_proof_wrong_is_blocked(self):
        (self.dist/(KEY+'.txt')).write_text('wrong\n'); self.blocked('blog_built_ownership_file_mismatch')
    def test_built_proof_symlink_is_blocked(self):
        p = self.dist/(KEY+'.txt'); p.unlink(); other = self.root/'proof'; other.write_text(KEY+'\n'); p.symlink_to(other)
        self.blocked('blog_built_ownership_file_missing')
    def test_public_proof_wrong_is_blocked(self):
        self.rows[ORIGIN+'/'+KEY+'.txt'] = (200, 'wrong', {}); self.blocked('ownership_file_not_verified')
    def test_public_redirect_is_blocked(self):
        self.rows[ORIGIN+'/'] = (301, '', {}); self.blocked('page_not_http200')
    def test_stale_public_revision_is_blocked(self):
        self.rows[ORIGIN+'/'] = (200, html(ORIGIN+'/').replace(REVISION,'b'*40), {})
        self.blocked('page_revision_mismatch')
    def test_public_noindex_is_blocked(self):
        self.rows[ORIGIN+'/'] = (200, html(ORIGIN+'/').replace('index,follow','noindex,follow'), {})
        self.blocked('page_meta_not_indexable')
    def test_verify_mode_never_posts(self):
        result = blog.verify(self.path,REVISION,self.root,self.transport)
        self.assertEqual(result['urlCount'],2); self.assertFalse(self.posts); self.assertFalse(self.journal.items)
    def test_resolve_exact_branch_without_opening_gates(self):
        output = blog.resolved_target(self.path, REVISION)
        self.assertEqual(output['branch'], 'site-factory-blog-fwith'); self.assertEqual(output['revision'],REVISION)
        self.assertNotIn(KEY,json.dumps(output))
        with self.assertRaisesRegex(ValueError,'full_revision_required'): blog.resolved_target(self.path,'main')
    def test_repeat_uses_existing_receipt(self):
        self.run_it(); result=self.run_it()
        self.assertEqual(result['state'],'already_received'); self.assertEqual(len(self.posts),1)
    def test_unknown_timeout_blocks_new_request(self):
        self.statuses=[TimeoutError('private')]
        with self.assertRaisesRegex(ValueError,'submission_outcome_uncertain'): self.run_it()
        self.posts=[]; self.blocked('prior_submission_outcome_uncertain')
    def test_started_without_receipt_blocks_new_request(self):
        self.run_it(); self.posts=[]; self.journal.items=self.journal.items[:1]
        self.blocked('prior_submission_outcome_uncertain')
    def test_202_is_pending_and_429_uses_existing_bounds(self):
        self.statuses=[429,202]; result=self.run_it()
        self.assertEqual(result['state'],'received_key_validation_pending'); self.assertEqual(self.sleeps,[10])
    def test_journal_failure_stops_before_post(self):
        self.journal.fail=True
        with self.assertRaises(RuntimeError): self.run_it()
        self.assertFalse(self.posts)


if __name__=='__main__': unittest.main()
