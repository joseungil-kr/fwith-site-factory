#!/usr/bin/env python3
"""Static contract for preview and indexable blog builds."""
from pathlib import Path
import os, re
root=Path('dist'); revision=os.environ.get('SITE_FACTORY_REVISION',''); origin=os.environ.get('SITE_URL','').rstrip('/'); indexable=os.environ.get('SITE_INDEXABLE')=='true'
def require(c,m):
 if not c: raise SystemExit(m)
def read(p):
 f=root/p; require(f.is_file(),f'missing artifact: {p}'); return f.read_text(encoding='utf-8')
pages=sorted(root.glob('**/*.html')); require(pages,'no_html_routes'); home=read('index.html'); robots=read('robots.txt'); read('rss.xml'); read('sitemap-index.xml')
require('https://fwith.co.kr' in home,'brand_cta_missing'); require(origin.startswith('https://'),'site_url_missing')
posts=[p for p in pages if p.as_posix().startswith('dist/posts/') and p.name=='index.html' and p.parent.name!='posts']; require(posts,'no_published_posts')
if indexable:
 require('Allow: /' in robots,'robots_allow_missing'); require(not (root/'_headers').exists(),'indexable_noindex_header_present')
else:
 require('Disallow: /' in robots,'robots_block_missing'); require('noindex' in read('_headers'),'noindex_header_missing')
for p in pages:
 h=p.read_text(encoding='utf-8'); rel=p.relative_to(root).as_posix(); forced=rel in {'404.html','search/index.html'}; expected='index,follow' if indexable and not forced else 'noindex,nofollow'
 require(f'name="robots" content="{expected}"' in h,f'robots_meta_mismatch:{rel}'); require(f'name="site-factory-revision" content="{revision}"' in h,f'revision_meta_missing:{rel}')
 c=re.search(r'<link rel="canonical" href="([^"]+)"',h); require(c and c.group(1).startswith(origin+'/'),f'canonical_origin_mismatch:{rel}')
 for a in re.findall(r'(?:src|href)="(/[^\"]+)"',h):
  if a.startswith('/_astro/') or a=='/favicon.svg': require((root/a.lstrip('/')).is_file(),f'asset_missing:{rel}:{a}')
sitemap=read('sitemap-0.xml'); require(set(re.findall(r'<loc>(https?://[^/]+)',sitemap))=={origin},'sitemap_origin_mismatch')
if indexable: require('/search/' not in sitemap and '/404' not in sitemap,'nonindex_route_in_sitemap')
print('static QA passed')
