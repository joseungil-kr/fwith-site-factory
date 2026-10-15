// Modifies generated heads/control files only after unchanged private QA; every body byte stays identical.
import fs from 'node:fs';
import path from 'node:path';
import {resolveYeosuRelease,ROOT,ADAPTER_ROOT,ROUTES,HTML_ROUTES,PROOF,require,robotsForRoute} from './yeosu_release.mjs';
const release=resolveYeosuRelease();require(release.mode==='production','production_only_output_transform');
const dist=path.join(ROOT,'dist'),htmlpath=r=>r==='/'?'index.html':r==='/404.html'?'404.html':r.slice(1)+'index.html';
for(const route of HTML_ROUTES){
 const file=path.join(dist,htmlpath(route)),before=fs.readFileSync(file,'utf8');
 require(before.split('<meta name="robots" content="noindex,follow">').length===2&&!before.includes('rel="canonical"')&&!before.includes('site-factory-revision'),'pristine_private_metadata_required');
 let after=before.replace('<meta name="robots" content="noindex,follow">',`<meta name="robots" content="${robotsForRoute(route)}"><meta name="site-factory-revision" content="${release.revision}">`);
 if(route==='/404.html')after=after.replace(/<meta property="og:[^"]+" content="[^"]*">/g,'');
 else {
  const exact=(name)=>{const hits=[...before.matchAll(new RegExp('<meta property="'+name+'" content="([^"]*)">','g'))];require(hits.length===1&&hits[0][1].length>0,'exact_frozen_social_'+name+'_required');return hits[0][1];};
  require(!before.includes('twitter:')&&!before.includes('property="og:image'),'pristine_social_metadata_required');
  const title=exact('og:title'),description=exact('og:description');
  const image=release.origin+'/images/products/B201.jpg',alt='근조 3단 화환 B201 샘플의 흰 꽃과 노란 꽃';
  after=after.replace('</head>',`<link rel="canonical" href="${release.origin+route}"><meta property="og:url" content="${release.origin+route}"><meta property="og:image" content="${image}"><meta property="og:image:alt" content="${alt}"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="${title}"><meta name="twitter:description" content="${description}"><meta name="twitter:image" content="${image}"><meta name="twitter:image:alt" content="${alt}"></head>`);
 }
 require(before.split('<main id="main-content" tabindex="-1">').length===2,'exact_existing_focus_target_required');
 require(after.slice(after.indexOf('<body'))===before.slice(before.indexOf('<body')),'customer_body_changed');
 fs.writeFileSync(file,after);
}
fs.writeFileSync(path.join(dist,'robots.txt'),`User-agent: *\nAllow: /\nSitemap: ${release.origin}/sitemap-index.xml\n`);
fs.writeFileSync(path.join(dist,'_headers'),'/*\n');
fs.rmSync(path.join(dist,'sitemap.xml'));
fs.writeFileSync(path.join(dist,'sitemap-index.xml'),`<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>${release.origin}/sitemap-0.xml</loc></sitemap></sitemapindex>\n`);
fs.writeFileSync(path.join(dist,'sitemap-0.xml'),`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${ROUTES.map(r=>`<url><loc>${release.origin+r}</loc></url>`).join('')}</urlset>\n`);
fs.copyFileSync(path.join(ADAPTER_ROOT,'release/existing-indexnow-proof.txt'),path.join(dist,PROOF.path.slice(1)));
console.log('Generated four route-aware metadata heads, exact two-URL sitemap and existing public proof; no network calls.');
