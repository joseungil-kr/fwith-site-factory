// Historical source pins remain unchanged. Only the exact reviewed banner amendment
// may be reversed for historical assertions; current bytes are checked independently.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
export const fixturePath=new URL('./fixtures/shared-banner-amendment.json',import.meta.url);
const fixture=JSON.parse(fs.readFileSync(fixturePath,'utf8'));
export const historicalImport="import {readHistoricalBannerSource} from './shared-banner-amendment.mjs';\n";
function once(source,old,replacement){assert.equal(source.split(old).length-1,1,'Unexpected amendment boundary: '+old);return source.replace(old,replacement);}
function imported(source,prefix){assert(source.startsWith('---\n'));return source.replace('---\n',`---\nimport SharedFlowerBanner from '${prefix}components/SharedFlowerBanner.astro';\n`);}
export function applyReviewedAmendment(file,original){
 if(file.startsWith('tests/') && file.endsWith('.test.mjs'))return historicalImport+original.replaceAll('fs.readFileSync','readHistoricalBannerSource');
 if(file==='package.json'){
  const data=JSON.parse(original);
  const allowed=new Set([' && python3 scripts/qa_shared_banners.py',' && python3 scripts/test_shared_banners.py',' && python3 scripts/qa_shared_banners.py && python3 scripts/test_shared_banners.py']);
  for(const [name,suffix] of Object.entries(fixture.packageScriptSuffixes||{})){assert(['build','qa'].includes(name)&&allowed.has(suffix),'Unreviewed package script change');data.scripts[name]+=suffix;}
  return JSON.stringify(data,null,2)+'\n';
 }
 let s=original;
 if(file==='src/pages/index.astro'){
  s=imported(s,'../');s=s.replace('</section>\n','</section>\n<SharedFlowerBanner variant="message"/>\n');
  s=once(s,'<section class="product-section" data-home-selection>','<SharedFlowerBanner variant="budget"/>\n<section class="product-section" data-home-selection>');
  return once(s,'<InlineOrderBanner/>','<SharedFlowerBanner variant="consultation"/>\n<InlineOrderBanner/>');
 }
 if(file==='src/pages/[category]/[slug].astro'){
  s=imported(s,'../../');s=once(s,'{page.contentMarkdown ?','<SharedFlowerBanner variant="message"/>\n{page.contentMarkdown ?');
  s=once(s,'<InlineOrderBanner/>','<SharedFlowerBanner variant="budget"/>\n<InlineOrderBanner/>');
  const start='{sources.map(source => <section class="source-card"';
  s=once(s,start,'{sources.length>0 && <section class="source-references" aria-labelledby="source-references-title"><h2 id="source-references-title">출처 및 확인 정보</h2>\n'+start);
  s=once(s,'<h2>{source.name}</h2>','<h3>{source.name}</h3>');
  const end='<time datetime={source.verifiedAt}>{source.verifiedAt}</time></small></section>)}';
  s=once(s,end,end+'\n</section>}');
  return once(s,'<section class="conversion-panel">','<SharedFlowerBanner variant="consultation"/>\n<section class="conversion-panel">');
 }
 if(file==='src/components/RegionDirectory.astro'){
  s=imported(s,'../').replace("'../components/SharedFlowerBanner.astro'","'./SharedFlowerBanner.astro'");
  s=once(s,'const {pages}=Astro.props;','const {pages,showBanners=true}=Astro.props;');
  s=s.replace('</section>\n','</section>\n{showBanners && <SharedFlowerBanner variant="message"/>}\n');
  s=once(s,'<InlineOrderBanner/>','<><InlineOrderBanner/>{showBanners && <SharedFlowerBanner variant="budget"/>}</>');
  return s+'\n{showBanners && <SharedFlowerBanner variant="consultation"/>}\n';
 }
 if(file==='src/pages/[category]/index.astro'){
  s=imported(s,'../../');s=once(s,'<RegionDirectory pages={items}/>','<RegionDirectory pages={items} showBanners={items.length>=3}/>');
  s=once(s,'<section class="product-section">','{items.length>=3 && <SharedFlowerBanner variant="message"/>}\n<section class="product-section">');
  s=once(s,'<InlineOrderBanner/>','{items.length>=3 && <SharedFlowerBanner variant="budget"/>}\n<InlineOrderBanner/>');
  return once(s,'{addressPage &&','{items.length>=3 && <SharedFlowerBanner variant="consultation"/>}\n{addressPage &&');
 }
 throw new Error('File is outside reviewed banner amendment: '+file);
}
export function assertAmendedBytes(file,bytes,record=fixture.files[file]){
 assert(record,'Missing banner amendment record: '+file);
 assert.equal(sha(record.beforeUtf8),record.beforeSha256,'Historical archived source changed: '+file);
 assert.equal(sha(bytes),record.afterSha256,'Current amended source changed: '+file);
 assert.equal(bytes.toString('utf8'),applyReviewedAmendment(file,record.beforeUtf8),'Non-banner changes are forbidden: '+file);
 return true;
}
export function readHistoricalBannerSource(file,options){
 const absolute=file instanceof URL?fileURLToPath(file):path.resolve(String(file));
 const relative=path.relative(root,absolute).split(path.sep).join('/');
 assert(!relative.startsWith('../')&&!path.isAbsolute(relative),'Historical read escapes package root');
 const bytes=fs.readFileSync(absolute);const record=fixture.files[relative];
 if(!record)return fs.readFileSync(absolute,options);
 assertAmendedBytes(relative,bytes,record);
 const buffer=Buffer.from(record.beforeUtf8,'utf8');const encoding=typeof options==='string'?options:options?.encoding;
 return encoding?buffer.toString(encoding):buffer;
}
export function assertCurrentBannerAmendment(){
 for(const [file,record] of Object.entries(fixture.files))assertAmendedBytes(file,fs.readFileSync(path.join(root,file)),record);
 for(const [file,expected] of Object.entries(fixture.additions))assert.equal(sha(fs.readFileSync(path.join(root,file))),expected,'New reviewed banner artifact changed: '+file);
 return fixture;
}
