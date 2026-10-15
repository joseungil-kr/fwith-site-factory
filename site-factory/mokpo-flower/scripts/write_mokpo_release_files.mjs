// Modifies generated heads/control files and one declared main focus attribute after unchanged private QA.
import fs from 'node:fs';
import path from 'node:path';
import {resolveMokpoRelease,ROOT,ROUTES,HTML_ROUTES,PROOF,require,robotsForRoute} from './mokpo_release.mjs';
const release=resolveMokpoRelease();require(release.mode==='production','production_only_output_transform');
const dist=path.join(ROOT,'dist'),htmlpath=r=>r==='/'?'index.html':r==='/404.html'?'404.html':r.slice(1)+'index.html';
for(const route of HTML_ROUTES){
 const file=path.join(dist,htmlpath(route)),before=fs.readFileSync(file,'utf8');
 require(before.split('<meta name="robots" content="noindex,follow">').length===2&&!before.includes('rel="canonical"')&&!before.includes('site-factory-revision'),'pristine_private_metadata_required');
 let after=before.replace('<meta name="robots" content="noindex,follow">',`<meta name="robots" content="${robotsForRoute(route)}"><meta name="site-factory-revision" content="${release.revision}">`);
 if(route==='/404.html')after=after.replace(/<meta property="og:[^"]+" content="[^"]*">/g,'');
 else after=after.replace('</head>',`<link rel="canonical" href="${release.origin+route}"><meta property="og:url" content="${release.origin+route}"></head>`);
 require(before.split('<main id="main-content">').length===2,'exact_private_main_target_required');
 after=after.replace('<main id="main-content">','<main id="main-content" tabindex="-1">');
 const normalized=after.replace('<main id="main-content" tabindex="-1">','<main id="main-content">');
 require(normalized.slice(normalized.indexOf('<body'))===before.slice(before.indexOf('<body')),'customer_body_changed_beyond_declared_focus_attribute');
 fs.writeFileSync(file,after);
}
fs.writeFileSync(path.join(dist,'robots.txt'),`User-agent: *\nAllow: /\nSitemap: ${release.origin}/sitemap-index.xml\n`);
fs.writeFileSync(path.join(dist,'_headers'),'/*\n');
fs.rmSync(path.join(dist,'sitemap.xml'));
fs.writeFileSync(path.join(dist,'sitemap-index.xml'),`<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>${release.origin}/sitemap-0.xml</loc></sitemap></sitemapindex>\n`);
fs.writeFileSync(path.join(dist,'sitemap-0.xml'),`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${ROUTES.map(r=>`<url><loc>${release.origin+r}</loc></url>`).join('')}</urlset>\n`);
fs.copyFileSync(path.join(ROOT,'release/existing-indexnow-proof.txt'),path.join(dist,PROOF.path.slice(1)));
console.log('Generated four route-aware metadata heads, exact two-URL sitemap and existing public proof; no network calls.');
