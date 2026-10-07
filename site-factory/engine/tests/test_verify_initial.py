"""Synthetic local HTTP responses test parity, never real hosted QA."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verify_initial as qa

SITE='namyangju-flower-v2'; REV='a'*40


class InitialHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.phase='production';self.origin='https://namyangju.fwith.kr';self.make()
    def write(self,path,data):
        p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(data if isinstance(data,bytes) else data.encode())
    def make(self):
        rows=[{'pageKey':f'p{i}','snapshotId':f's{i}','url':f'/regions/dong-{i}/','category':'regions','status':'approved','approvalVerified':True} for i in range(3)]
        self.routes=['/','/regions/']+[r['url'] for r in rows]
        self.write('src/data/publish-manifest.json',json.dumps({'siteKey':SITE,'pages':rows}))
        self.write('src/data/architecture.json',json.dumps({'siteKey':SITE,'hubs':[{'category':'regions','url':'/regions/','children':3,'indexable':True,'menuVisible':False},{'category':'gift','url':'/gift/','children':0,'indexable':False,'menuVisible':False}]}))
        for route in self.routes:
            row=next((r for r in rows if r['url']==route),None)
            robots='index,follow' if self.phase=='production' else 'noindex,nofollow,noarchive'
            snapshot=f' data-snapshot-id="{row["snapshotId"]}"' if row else ''
            html=f'<!doctype html><html><head><meta name="site-factory-revision" content="{REV}"><meta name="robots" content="{robots}"><link rel="canonical" href="{self.origin}{route}"><script type="application/ld+json">{{}}</script></head><body><article{snapshot}><h1>frozen</h1><p>Exact body</p></article></body></html>'
            self.write('dist/'+route.lstrip('/')+'index.html',html)
        self.write('dist/404.html',f'<html><head><meta name="robots" content="noindex,nofollow,noarchive"><meta name="site-factory-revision" content="{REV}"></head><body><h1>페이지를 찾을 수 없습니다</h1></body></html>')
        self.write('dist/style.css','body{color:black}')
        self.write('dist/image.png',b'synthetic asset bytes')
        robots='User-agent: *\nAllow: /\nSitemap: '+self.origin+'/sitemap-index.xml\n' if self.phase=='production' else 'User-agent: *\nDisallow: /\n'
        self.write('dist/robots.txt',robots)
        ns='http://www.sitemaps.org/schemas/sitemap/0.9'
        self.write('dist/sitemap-index.xml',f'<sitemapindex xmlns="{ns}"><sitemap><loc>{self.origin}/sitemap-0.xml</loc></sitemap></sitemapindex>')
        self.write('dist/sitemap-0.xml',f'<urlset xmlns="{ns}">'+''.join('<url><loc>'+self.origin+r+'</loc></url>' for r in self.routes)+'</urlset>')
    def fetch(self,route):
        p=self.root/'dist'/route.lstrip('/')
        if p.is_dir():p=p/'index.html'
        status=200
        if not p.is_file():p=self.root/'dist/404.html';status=404
        mime={'.html':'text/html','.css':'text/css','.png':'image/png','.txt':'text/plain','.xml':'application/xml'}[p.suffix]
        headers={'content-type':mime}
        if self.phase=='preview':headers['x-robots-tag']='noindex, nofollow, noarchive'
        return status,p.read_bytes(),headers
    def check(self,fetch=None):return qa.verify(self.root,SITE,self.origin,REV,self.phase,fetch or self.fetch)
    def test_all_actual_route_and_asset_bytes_are_required(self):
        result=self.check();self.assertEqual(result['pipelineState'],'live_verified');self.assertTrue(result['artifactParity'])
        self.assertEqual(result['routes'],5);self.assertEqual(result['assets'],5)
    def test_preview_full_parity_uses_noindex_headers(self):
        self.phase='preview';self.origin='https://namyangju-flower-guide-qa.joseungil.workers.dev';self.make()
        self.assertEqual(self.check()['pipelineState'],'preview_verified')
    def test_changed_body_schema_and_appended_script_fail(self):
        for kind in ['body','schema','script']:
            def fetch(route):
                status,raw,headers=self.fetch(route)
                if route=='/':
                    raw=raw.replace(b'Exact body',b'Changed body') if kind=='body' else raw.replace(b'>{}</script>',b'>{"changed":true}</script>') if kind=='schema' else raw.replace(b'</body>',b'<script>arbitrary()</script></body>')
                return status,raw,headers
            with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'HTML'):self.check(fetch)
    def test_missing_detail_hub_and_asset_fail(self):
        for missing in ['/regions/dong-0/','/regions/','/image.png']:
            def fetch(route):
                if route==missing:return 404,b'missing',{'content-type':'text/plain'}
                return self.fetch(route)
            with self.subTest(route=missing),self.assertRaises((ValueError,AssertionError)):self.check(fetch)
    def test_extra_unreviewed_public_html_cannot_deploy(self):
        self.write('dist/unreviewed.html','unapproved')
        with self.assertRaisesRegex(ValueError,'inventory'):self.check()
    def test_wrong_mime_noindex_and_forbidden_are_not_success(self):
        for mutation in ['mime','noindex','403']:
            def fetch(route):
                status,raw,headers=self.fetch(route)
                if route=='/':
                    if mutation=='mime':headers['content-type']='text/plain'
                    elif mutation=='noindex':headers['x-robots-tag']='noindex'
                    else:status=403
                return status,raw,headers
            with self.subTest(mutation=mutation),self.assertRaises((ValueError,PermissionError)):self.check(fetch)
    def test_empty_hub_must_return_exact_404_without_canonical(self):
        def fetch(route):
            if route=='/gift/':return self.fetch('/')
            return self.fetch(route)
        with self.assertRaises(ValueError):self.check(fetch)
    def test_generic_metadata_verifier_cannot_claim_initial_completion(self):
        from verify_live import verify as generic
        with self.assertRaisesRegex(ValueError,'verify_initial.py'):
            generic(self.root,self.origin,REV,self.fetch,site_key=SITE)
    def test_wrong_origin_is_blocked_before_http(self):
        self.origin='https://other.example'
        with self.assertRaisesRegex(ValueError,'origin'):self.check(lambda _:self.fail('must not fetch'))


if __name__=='__main__':unittest.main()
