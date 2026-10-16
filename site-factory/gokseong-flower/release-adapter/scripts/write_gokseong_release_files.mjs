// Dedicated-proof successor: private bytes checked first; metadata/proof only. No provider or IndexNow calls.
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {resolveGokseongRelease,ROOT,SOURCE_ROOT,ADAPTER_ROOT,ROUTES,HTML_ROUTES,PROOF,EQUIVALENCE_SHA256,sha,read,require,robotsForRoute,ORIGIN} from './gokseong_release.mjs';
function writeOutput(destination,production){
 const release=resolveGokseongRelease();require(release.mode===(production?'production':'preview'),'selected_mode_required');
 const dist=production?path.join(ROOT,'dist'):path.resolve(destination);
 if(!production)require(!fs.existsSync(dist)&&!dist.startsWith(SOURCE_ROOT+path.sep)&&!SOURCE_ROOT.startsWith(dist+path.sep)&&dist!==SOURCE_ROOT,'new_external_inspection_destination_required');
 const rawBaseline=read(path.join(ADAPTER_ROOT,'release/preview-equivalence.json'));require(sha(rawBaseline)===EQUIVALENCE_SHA256,'pinned_equivalence_required');const baseline=JSON.parse(rawBaseline);
 const privateDist=path.join(ROOT,'dist');const names=[];function scan(dir){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){require(!entry.isSymbolicLink(),'private_symlink_forbidden');const f=path.join(dir,entry.name);if(entry.isDirectory())scan(f);else {require(entry.isFile(),'private_regular_file_required');names.push(path.relative(privateDist,f).split(path.sep).join('/'));}}}scan(privateDist);
 const expected=[...Object.keys(baseline.htmlBodies),...Object.keys(baseline.staticAssets),'robots.txt','_headers','sitemap.xml'];require(JSON.stringify(names.sort())===JSON.stringify(expected.sort()),'exact_private_inventory_required');
 for(const [file,digest] of Object.entries(baseline.htmlBodies)){const b=read(path.join(privateDist,file)),i=b.indexOf('<body');require(i>=0&&sha(b.subarray(i))===digest&&b.subarray(0,i).toString()===baseline.htmlPrefixes[file],'exact_private_html_required');}
 for(const [file,digest] of Object.entries(baseline.staticAssets))require(sha(read(path.join(privateDist,file)))===digest,'exact_private_asset_required');
 for(const file of ['robots.txt','_headers','sitemap.xml'])require(read(path.join(privateDist,file)).equals(read(path.join(ROOT,'public',file))),'exact_private_control_required');
 if(!production)fs.cpSync(privateDist,dist,{recursive:true});
 const copy=JSON.parse(read(path.join(ROOT,'../inputs/reviewed-copy/customer-copy.json')));const socialImage={path:'/images/products/B201.jpg',alt:copy.productCards[0].photoAlt};
 const escapeAttribute=s=>s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#x27;'}[c]));
 for(const route of HTML_ROUTES){
  const file=path.join(dist,route==='/'?'index.html':'404.html'),before=fs.readFileSync(file,'utf8');require(before.split('<meta name="robots" content="noindex,nofollow,noarchive">').length===2&&!before.includes('rel="canonical"')&&!before.includes('site-factory-revision'),'pristine_private_metadata_required');
  let after=before.replace('<meta name="robots" content="noindex,nofollow,noarchive">',`<meta name="robots" content="${robotsForRoute(route)}"><meta name="site-factory-revision" content="${production?release.revision:'local-inspection'}">`);
  if(route==='/404.html')after=after.replace(/<meta property="og:[^"]+" content="[^"]*">/g,'');
  else{
   const titles=[...before.matchAll(/<meta property="og:title" content="([^"]*)">/g)],descriptions=[...before.matchAll(/<meta property="og:description" content="([^"]*)">/g)];require(titles.length===1&&descriptions.length===1,'reviewed_social_source_required');const image=ORIGIN+socialImage.path,alt=escapeAttribute(socialImage.alt);
   const social=`<meta property="og:image" content="${image}"><meta property="og:image:width" content="500"><meta property="og:image:height" content="500"><meta property="og:image:alt" content="${alt}"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="${titles[0][1]}"><meta name="twitter:description" content="${descriptions[0][1]}"><meta name="twitter:image" content="${image}"><meta name="twitter:image:alt" content="${alt}">`;
   after=after.replace('</head>',`<link rel="canonical" href="${ORIGIN+route}"><meta property="og:url" content="${ORIGIN+route}">${social}</head>`);
  }
  require(after.slice(after.indexOf('<body'))===before.slice(before.indexOf('<body')),'customer_body_changed');fs.writeFileSync(file,after);
 }
 fs.writeFileSync(path.join(dist,'robots.txt'),`User-agent: *\nAllow: /\nSitemap: ${ORIGIN}/sitemap-index.xml\n`);fs.writeFileSync(path.join(dist,'_headers'),'/*\n');fs.rmSync(path.join(dist,'sitemap.xml'));
 fs.writeFileSync(path.join(dist,'sitemap-index.xml'),`<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>${ORIGIN}/sitemap-0.xml</loc></sitemap></sitemapindex>\n`);
 fs.writeFileSync(path.join(dist,'sitemap-0.xml'),`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${ROUTES.map(r=>`<url><loc>${ORIGIN+r}</loc></url>`).join('')}</urlset>\n`);
 if(production)fs.copyFileSync(path.join(ADAPTER_ROOT,'release/gokseong-indexnow-proof.txt'),path.join(dist,PROOF.path.slice(1)));
 return {mode:production?'production':'offline-inspection',sourceRevision:production?release.revision:null,proof:production?PROOF:null,publishableArtifact:false,networkCalls:0};
}
export function writeOfflineInspection(destination){return writeOutput(destination,false)}
export function writeProduction(){return writeOutput(undefined,true)}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length===2)console.log(JSON.stringify(writeProduction()));
 else{require(process.argv[2]==='--offline-inspection'&&process.argv.length===4,'unknown_writer_arguments');console.log(JSON.stringify(writeOfflineInspection(process.argv[3])));}
}
