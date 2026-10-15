// Modifies generated heads/control files only after unchanged private QA; every body byte stays identical.
import fs from 'node:fs';
import path from 'node:path';
import {resolveNamguRelease,ROOT,ADAPTER_ROOT,ROUTES,HTML_ROUTES,PROOF,require,robotsForRoute} from './namgu_release.mjs';
const release=resolveNamguRelease();require(release.mode==='production','production_only_output_transform');
const copy=JSON.parse(fs.readFileSync(path.join(ROOT,'../inputs/reviewed-copy/customer-copy.json'),'utf8'));const asset=JSON.parse(fs.readFileSync(path.join(ROOT,'../inputs/reviewed-copy/asset-manifest.json'),'utf8')).productPhotos.find(p=>p.sku==='B201');const socialImage={path:asset.publicPath,alt:copy.productCards[0].photoAlt};
require(socialImage.path==='/images/products/B201.jpg'&&typeof socialImage.alt==='string','reviewed_social_product_required');
const escapeAttribute=s=>s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#x27;'}[c]));
const dist=path.join(ROOT,'dist'),htmlpath=r=>r==='/'?'index.html':r==='/404.html'?'404.html':r.slice(1)+'index.html';
for(const route of HTML_ROUTES){
 const file=path.join(dist,htmlpath(route)),before=fs.readFileSync(file,'utf8');
 require(before.split('<meta name="robots" content="noindex,nofollow,noarchive">').length===2&&!before.includes('rel="canonical"')&&!before.includes('site-factory-revision'),'pristine_private_metadata_required');
 let after=before.replace('<meta name="robots" content="noindex,nofollow,noarchive">',`<meta name="robots" content="${robotsForRoute(route)}"><meta name="site-factory-revision" content="${release.revision}">`);
 if(route==='/404.html')after=after.replace(/<meta property="og:[^"]+" content="[^"]*">/g,'');
 else {
  const titles=[...before.matchAll(/<meta property="og:title" content="([^"]*)">/g)],descriptions=[...before.matchAll(/<meta property="og:description" content="([^"]*)">/g)];
  require(titles.length===1&&descriptions.length===1&&before.split('</head>').length===2,'exact_reviewed_social_source_required');
  const image=release.origin+socialImage.path,alt=escapeAttribute(socialImage.alt);
  const social=`<meta property="og:image" content="${image}"><meta property="og:image:width" content="500"><meta property="og:image:height" content="500"><meta property="og:image:alt" content="${alt}"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="${titles[0][1]}"><meta name="twitter:description" content="${descriptions[0][1]}"><meta name="twitter:image" content="${image}"><meta name="twitter:image:alt" content="${alt}">`;
  after=after.replace('</head>',`<link rel="canonical" href="${release.origin+route}"><meta property="og:url" content="${release.origin+route}">${social}</head>`);
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
