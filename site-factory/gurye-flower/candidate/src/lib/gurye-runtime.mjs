import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
// Astro relocates server modules into dist/.prerender; builds run from this candidate root.
export const candidate = path.resolve(process.cwd());
if(!fs.existsSync(path.join(candidate,'src/lib/gurye-runtime.mjs')))throw new Error('Run from the Gurye candidate root');
export const author = path.resolve(candidate, '../inputs/author');
export const reviewer = path.resolve(candidate, '../inputs/root-copy-review');
export const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const bound = {
 'AUTHOR-MANIFEST.json':'bc3acbaba602638206261ddba65d1df84a3dcdda558ad317fbfea2f32fcbdcb1',
 'draft-home.ko.md':'9555f3bf4a7e5a09ed9441bc68c0276557bdd8d9b39e7a79e11238d42d747a94',
 'display-copy.json':'4bb1ea3a0089d6dd05367e1d5d4ad36a34a444e8ca1678e01f2374658bcfbe11'
};
export function regularRead(root, relative) {
 if(path.isAbsolute(relative)||relative.split(/[\\/]/).includes('..')) throw new Error('Unsafe input path');
 const target=path.join(root,relative);
 let cursor=root;
 for(const segment of relative.split('/')) {cursor=path.join(cursor,segment);if(fs.lstatSync(cursor).isSymbolicLink())throw new Error('Symlink input forbidden');}
 if(!fs.statSync(target).isFile())throw new Error('Regular file required');
 return fs.readFileSync(target);
}
export const PROJECTION_SHA256="f5b7677ae418658bbbf057a5b4698923e2cd3ceacfd885d85e51a83e0c7360d9";
const PACKAGED_AUTHOR_PATHS=["AUTHOR-MANIFEST.json", "SOURCE-MAP.json", "asset-manifest.json", "customer-copy.json", "display-copy.json", "draft-home.ko.md", "image-observations.json", "render-plan.json", "visible-strings.json"];
const REFERENCE_SCOPE='ARCHIVED_REFERENCE_ONLY_NOT_PACKAGED';
export function validateProjectionData(p,manifest){
 const keys=["schema", "purpose", "historicalManuscript", "historicalImplementation", "packagedAuthorFiles", "packagedHistoricalManifestEntries", "archivedHistoricalEntries", "archivedHistoricalEntryCount", "publicOriginalObservations", "policyImageCoordinates", "referenceMetadataFiles", "buildNetworkRequests", "rawPolicyImagesPackaged", "cropImagesPackaged", "newBinaryBlobs", "customerAssetsExistingBlobs", "customerOutputChangesAllowed", "publicationEligible", "sourceCommit", "proof"];
 if(JSON.stringify(Object.keys(p).sort())!==JSON.stringify(keys.slice().sort()))throw new Error('Projection keys changed');
 if(p.schema!=='gurye-private-qa-source-projection/v1'||p.buildNetworkRequests!==false||p.rawPolicyImagesPackaged!==false||p.cropImagesPackaged!==false||p.newBinaryBlobs!==0||p.customerAssetsExistingBlobs!==7||p.customerOutputChangesAllowed!==false||p.publicationEligible!==false||p.sourceCommit!==null||p.proof!==null)throw new Error('Projection scope promoted');
 if(p.historicalManuscript.authorManifestSHA256!==bound['AUTHOR-MANIFEST.json']||p.historicalManuscript.manifestEntries!==132||p.packagedHistoricalManifestEntries!==8||p.archivedHistoricalEntryCount!==124||manifest.files.length!==132)throw new Error('Historical denominator changed');
 if(p.packagedAuthorFiles.length!==9||JSON.stringify(p.packagedAuthorFiles.map(x=>x.path).sort())!==JSON.stringify(PACKAGED_AUTHOR_PATHS))throw new Error('Packaged author denominator changed');
 const expected=manifest.files.filter(x=>!PACKAGED_AUTHOR_PATHS.includes(x.path)).map(x=>({...x,mode:REFERENCE_SCOPE}));
 if(JSON.stringify(p.archivedHistoricalEntries)!==JSON.stringify(expected))throw new Error('Archived references changed');
 for(const r of p.packagedAuthorFiles){const original=r.path==='AUTHOR-MANIFEST.json'?null:manifest.files.find(x=>x.path===r.path);if(r.historicalManifestMember!==(r.path!=='AUTHOR-MANIFEST.json')||(original&&(original.bytes!==r.bytes||original.sha256!==r.sha256)))throw new Error('Packaged source identity changed');}
 const h=p.historicalImplementation;
 if(h.manifestSHA256!=='bce362cb03ce159162f83d095b89b71f4bcd47683546b34a25acb198f372b6b0'||h.sourceZipSHA256!=='02155415dcf3ed30ef0f45043a917197b9a3af36eaacd3c7be35361701a1a00e'||h.independentReviewResultSHA256!=='d91aefa3aabbbf23ab66aff25e0205c04e80fa5beb0d6c22894af2b1de49abdb'||h.independentReviewManifestSHA256!=='203cc63b8ef1d62a2927807ad449859360c463e3fb9bf156f801dc518a513755'||sha(Buffer.from(h.independentReviewResultUTF8))!==h.independentReviewResultSHA256)throw new Error('Historical independent implementation review changed');
 const r=JSON.parse(h.independentReviewResultUTF8);if(r.verdict!=='ACCEPT_STATIC_IMPLEMENTATION_ONLY__VISUAL_AND_HTTP_BLOCKED'||r.publicationReady!==false||r.browser.screenshots!==0)throw new Error('Historical review scope changed');
 return true;
}
export function validateAuthor(root=author){
 for(const [file,hash] of Object.entries(bound))if(sha(regularRead(root,file))!==hash)throw new Error(`Bound source changed: ${file}`);
 const manifest=JSON.parse(regularRead(root,'AUTHOR-MANIFEST.json'));
 const raw=regularRead(path.dirname(root),'source-projection.json');if(sha(raw)!==PROJECTION_SHA256)throw new Error('Projection bytes changed');const p=JSON.parse(raw);validateProjectionData(p,manifest);
 const actual=fs.readdirSync(root).sort();if(JSON.stringify(actual)!==JSON.stringify(PACKAGED_AUTHOR_PATHS))throw new Error('Only nine author files belong in this reference projection');
 for(const row of p.packagedAuthorFiles){const bytes=regularRead(root,row.path);if(bytes.length!==row.bytes||sha(bytes)!==row.sha256)throw new Error(`Packaged author changed: ${row.path}`);}
 const map=JSON.parse(regularRead(root,'SOURCE-MAP.json')),observations=JSON.parse(regularRead(root,'image-observations.json'));
 const expectedSources=map.freshDirectGETs.map(x=>({id:x.id,url:x.url,archivedAtUTC:x.checkedAtUTC,sha256:x.sha256,bytes:x.bytes,path:x.path,scope:'Historical read-only GET observation; no current fetch during source build'}));
 if(JSON.stringify(p.publicOriginalObservations)!==JSON.stringify(expectedSources)||JSON.stringify(p.policyImageCoordinates)!==JSON.stringify(observations.observations))throw new Error('Original URL/hash/time/coordinate references changed');
 return 9;
}
export function assertBoundary(env=process.env) {
 const prohibited=['SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION','SITE_RELEASE_MODE','SITE_INDEXABLE','SITE_RELEASE_BINDING_PATH','SITE_RELEASE_BINDING_SHA','CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID','PRODUCTION_APPROVED','OWNERSHIP_VERIFIED','INDEXNOW_ENABLED','PUBLIC_APPROVED'];
 for(const name of prohibited)if(env[name]!==undefined)throw new Error(`Private-only build rejects ${name}`);
}
export function validateReview(root=reviewer){
 for(const [file,hash] of Object.entries({'REVIEW.ko.md':'589dd391df57d439574836982a6b1924731cdd6ce521ef5e3d54730b861819bb','R2-RESULT.json':'5559f1453a4b333cfa95926acbc8a510d703b58f9abe3e31a262c125251e8f90'}))if(sha(regularRead(root,file))!==hash)throw new Error('Independent copy review changed');
 const r=JSON.parse(regularRead(root,'R2-RESULT.json'));
 if(r.verdict!=='ACCEPT_MANUSCRIPT_R2_ONLY'||r.sourceManifestSHA256!==bound['AUTHOR-MANIFEST.json']||r.publicationReady!==false)throw new Error('Review binding mismatch');
}
assertBoundary();validateAuthor();validateReview();
export const copy=JSON.parse(regularRead(author,'customer-copy.json'));
export const display=copy.display;
export const ui=display.siteUI;
export const products=display.products;
export const assetBinding=JSON.parse(regularRead(candidate,'asset-render-binding.json'));
export const banners=assetBinding.assets.filter(a=>a.role==='banner').map(a=>({...a,id:a.id.replace('flower-',''),width:a.dimensions[0],height:a.dimensions[1]}));
export function validateAssets(root=candidate){
 const original=JSON.parse(regularRead(author,'asset-manifest.json')).assets;
 if(assetBinding.assets.length!==7)throw new Error('Expected seven approved assets');
 for(const a of assetBinding.assets){const source=original.find(x=>x.id===a.id);if(!source||a.sha256!==source.sha256||a.existingGitBlobSHA!==source.existingGitBlobSHA||a.alt!==source.alt)throw new Error('Asset binding changed');const bytes=regularRead(root,'public'+a.renderSrc);if(sha(bytes)!==source.sha256)throw new Error('Asset bytes changed');const git=createHash('sha1').update(Buffer.from(`blob ${bytes.length}\0`)).update(bytes).digest('hex');if(git!==source.existingGitBlobSHA)throw new Error('Existing Git blob mismatch');}
}
validateAssets();
// Rendering parses only the accepted manuscript's paragraph/list structure; it authors no sentences.
export function blocks(markdown){
 const result=[];let para=[],list=[];
 const flushP=()=>{if(para.length){result.push({type:'p',text:para.join('\n')});para=[];}};
 const flushL=()=>{if(list.length){result.push({type:'ul',items:list});list=[];}};
 for(const line of markdown.split('\n')){if(!line.trim()){flushP();flushL();}else if(line.startsWith('- ')){flushP();list.push(line.slice(2));}else{flushL();if(line.startsWith('#'))throw new Error('Heading not permitted inside plain section renderer');para.push(line);}}
 flushP();flushL();return result;
}
export const sections=copy.sections.filter(s=>s.id!=='questions').map(s=>({...s,blocks:blocks(s.markdown)}));
export const homePage={id:'home',title:display.page.title,description:display.page.description};
export const notFoundPage={id:'not-found',title:display.notFoundCopyPlan.title,description:display.notFoundCopyPlan.body};
