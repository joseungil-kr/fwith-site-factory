// Reused Gangnam release-output approach; write generated files only, never frozen inputs.
import fs from 'node:fs';
import path from 'node:path';
import {resolveGangdongRelease,ROOT,PROOF,ROUTES} from './gangdong_release.mjs';
const release=resolveGangdongRelease(),dist=path.join(ROOT,'dist');
if(release.mode==='production'){
 fs.writeFileSync(path.join(dist,'robots.txt'),`User-agent: *\nAllow: /\nSitemap: ${release.origin}/sitemap-index.xml\n`);
 fs.writeFileSync(path.join(dist,'_headers'),'/*\n');
 fs.rmSync(path.join(dist,'sitemap.xml'));
 fs.writeFileSync(path.join(dist,'sitemap-index.xml'),`<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>${release.origin}/sitemap-0.xml</loc></sitemap></sitemapindex>\n`);
 fs.writeFileSync(path.join(dist,'sitemap-0.xml'),`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${ROUTES.map(route=>`<url><loc>${release.origin}${route}</loc></url>`).join('')}</urlset>\n`);
}else{
 // Astro copies public files afresh. Preview keeps the original empty sitemap and deny-all files.
 fs.rmSync(path.join(dist,PROOF.path.slice(1)));
}
console.log('Exact '+release.mode+' generated robots, sitemap and header files written; no network calls');
