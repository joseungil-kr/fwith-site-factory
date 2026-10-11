import frozen from '../data/publish-manifest.json' with {type:'json'};
import manual from '../data/manual-pages.json' with {type:'json'};
const replacements=new Set(manual.pages.map(p=>p.pageKey));
export const effectiveManifest={...frozen,pages:[...frozen.pages.filter(p=>!replacements.has(p.pageKey)),...manual.pages]};
export {manual};

// Explicit article-level choices; manual/legacy publication identity stays above.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import products from '../data/products.json' with {type:'json'};
import articleSelections from '../data/article-product-selection.json' with {type:'json'};
// Astro prerender relocates this module under dist; npm build runs at the project root.
const contentRoot = process.cwd();
/** @param {string} detail @returns {never} */
const fail = detail => { throw new Error('ARTICLE_PRODUCT_SELECTION_BLOCKED: '+detail); };
const exactKeys = (value, keys) => value && typeof value==='object' && !Array.isArray(value) && Object.keys(value).sort().join('|')===keys.slice().sort().join('|');
export function validateArticleProductSelections(config, pages, catalog, manualKeys, readContent) {
 if (!exactKeys(config,['schemaVersion','siteKey','reviewedArticlesSha256','pages']) || config.schemaVersion!==1 || config.siteKey!=='yongin-flower-v2' || !/^[a-f0-9]{64}$/.test(config.reviewedArticlesSha256)) fail('invalid configuration');
 if (!Array.isArray(config.pages) || !Array.isArray(pages) || !pages.length || config.pages.length!==pages.length) fail('incomplete article coverage');
 const expected = new Map(pages.map(p=>[p.pageKey,p]));
 if (expected.size!==pages.length || new Set(manualKeys).size!==manualKeys.length) fail('duplicate manifest identity');
 const registered = new Map(catalog.map(p=>[p.productKey,p]));
 if (registered.size!==catalog.length) fail('duplicate catalog key');
 const seen=new Set(), files=new Set(), urls=new Set();
 for (const row of config.pages) {
  if (!exactKeys(row,['pageKey','url','category','sourceFile','rendererType','contentSha256','mode','productKeys','verifiedAt'])) fail('unknown or missing field');
  const page=expected.get(row.pageKey);
  if (!page || seen.has(row.pageKey) || files.has(row.sourceFile) || urls.has(row.url)) fail('unknown or duplicate article');
  seen.add(row.pageKey);files.add(row.sourceFile);urls.add(row.url);
  const renderer=manualKeys.includes(row.pageKey)?'manual':'legacy';
  const directory=renderer==='manual'?'manual':'articles';
  if (row.rendererType!==renderer || row.sourceFile!==page.file || row.url!==page.url || row.category!==page.category || row.url!==`/${page.category}/${page.slug}/`) fail('route or renderer mismatch');
  if (!new RegExp('^src/content/'+directory+'/yongin-[a-z0-9-]+\\.md$').test(row.sourceFile)) fail('unsafe source path');
  const content=readContent(row.sourceFile);
  if (!/^[a-f0-9]{64}$/.test(row.contentSha256) || crypto.createHash('sha256').update(content).digest('hex')!==row.contentSha256) fail('article bytes changed');
  if (typeof row.verifiedAt!=='string' || !/^\d{4}-\d{2}-\d{2}$/.test(row.verifiedAt) || Number.isNaN(Date.parse(row.verifiedAt))) fail('invalid existing verification date');
  const originalDate=content.toString().match(/^verifiedAt:\s*["']?(\d{4}-\d{2}-\d{2})["']?\s*$/m)?.[1];
  if (row.verifiedAt!==originalDate) fail('verification date changed');
  if (!Array.isArray(row.productKeys) || new Set(row.productKeys).size!==row.productKeys.length) fail('duplicate or invalid product keys');
  if (!['catalog','consultation'].includes(row.mode) || (row.mode==='catalog')!==(row.productKeys.length>0)) fail('mode/card mismatch');
  if (!['funeral','business','school','event','gift','order'].includes(row.category)) fail('unknown category');
  if (['school','gift'].includes(row.category) && row.mode!=='consultation') fail('direct gift cannot silently become a wreath');
  for (const key of row.productKeys) {
   const product=registered.get(key);
   if (!product) fail('unregistered product');
   if (row.category==='funeral' && product.category!=='funeral_wreath') fail('funeral family mismatch');
   if (['business','event'].includes(row.category) && product.category!=='congrats_wreath') fail('congratulations family mismatch');
   if (!Number.isInteger(product.price) || product.price<=0 || !/^\/images\/products\/[a-z0-9-]+\.(webp|jpg)$/.test(product.image)) fail('invalid catalog asset or price');
  }
 }
 return true;
}
validateArticleProductSelections(articleSelections,effectiveManifest.pages,products,manual.pages.map(p=>p.pageKey),file=>fs.readFileSync(path.resolve(contentRoot,file)));
export function getArticleProductSelection(pageKey, category) {
 const row=articleSelections.pages.find(p=>p.pageKey===pageKey);
 if (!row || row.category!==category) fail('unknown requested article');
 return {...row,productKeys:[...row.productKeys],products:row.productKeys.map(key=>{
  const product=products.find(p=>p.productKey===key);
  if (!product) return fail('unregistered selected product');
  return {...product};
 })};
}
