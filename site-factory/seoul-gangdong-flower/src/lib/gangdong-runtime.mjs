import {readFileSync,lstatSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {normalizeFaq} from '../components/faq.mjs';
import {planDirectoryBannerSplit} from './directory-banner-split.mjs';
export const INPUT_PIN='f398b65dca60d9ae08ed358c7c97906f4bced1faa6f024f1ef3e1fa275c7a9e7';
export const ORIGIN='https://seoul-gangdong.local.invalid';
export const LOCAL_PREVIEW={mode:'LOCAL_PREVIEW',approvalScope:'Assigned local implementation only',publicPresentationContract:'preserved unchanged as future intended public semantics',override:'all 5 routes noindex,nofollow,noarchive; empty sitemap; reserved invalid origin; utility404 omits canonical/social tags',futurePublicMode:'not implemented; separate exact source, hostname authorization and public QA required'};
export const hash=b=>createHash('sha256').update(b).digest('hex');
export const canonical=value=>JSON.stringify(value,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.entries(v).sort(([a],[b])=>a.localeCompare(b,'en'))):v);
const rootDefault=new URL('../../',import.meta.url);
export function assertBoundary(env=process.env){
 if(env.SITE_INDEXABLE!=null && env.SITE_INDEXABLE!=='false') throw new Error('LOCAL-only: SITE_INDEXABLE must remain false');
 if(env.SITE_URL!=null && env.SITE_URL!==ORIGIN)throw new Error('LOCAL-only: public hostname is not authorized');
 for(const name of ['PRODUCTION_APPROVED','OWNERSHIP_VERIFIED','INDEXNOW_ENABLED','PUBLIC_APPROVED'])if(env[name]!=null && env[name]!=='false')throw new Error(`LOCAL-only: ${name} is not authorized`);
}
export function verifyInputs(root=rootDefault){
 const base=root instanceof URL?root:new URL(`file://${resolve(root)}/`);
 const read=p=>readFileSync(new URL(p,base));
 const bytes=read('src/data/input-manifest.json');if(hash(bytes)!==INPUT_PIN)throw new Error('Frozen input manifest changed');
 const manifest=JSON.parse(bytes);
 for(const f of manifest.files){
  if(f.path.includes('..')||f.path.startsWith('/'))throw new Error('Unsafe input path');
  const p=new URL(f.path,base);if(!lstatSync(p).isFile()||hash(read(f.path))!==f.sha256)throw new Error(`Frozen input differs: ${f.path}`);
 }
 const expected=manifest.files.filter(f=>f.path.startsWith('src/data/frozen/')).map(f=>f.path.split('/').at(-1)).sort();
 if(JSON.stringify(readdirSync(new URL('src/data/frozen/',base)).sort())!==JSON.stringify(expected))throw new Error('Unexpected frozen input file');
 return name=>JSON.parse(read(`src/data/frozen/${name}.json`));
}
const paths=['/','/regions/gangdong-condolence-wreath/','/regions/gangdong-wedding-wreath/','/regions/','/404.html'];
export function generateRuntime(root=rootDefault){
 const input=verifyInputs(root);
 const pages=['home','condolence','wedding','directory','404'].map(id=>input(`${id}-copy`));
 const presentation=input('presentation-contract'), geography=input('geography'), common=input('common-copy'),plan=input('plan.projection');
 const classMap={'core-commercial':'core-commercial','work-commercial':'local-commercial'};
 const pageContracts=plan.pages.map(p=>{if(!(p.query_class in classMap))throw new Error('Unmapped editorial query class');return {...p,title_alignment_score:null,alignmentStatus:'awaiting independent compiled HTML assessment; source-copy score is not inherited',editorial_query_class:p.query_class,runtime_query_class:classMap[p.query_class],query_class_mapping:{source:p.query_class,target:classMap[p.query_class],reason:p.query_class==='work-commercial'?'Explicit compatibility mapping to existing regional-service adapter local-commercial; editorial work-commercial preserved':'No conversion needed'},metadataContract:{...p.metadataContract,status:'local-preview',index_status:'noindex-local-preview'}};});
 const runtime={schema:'gangdong-local-static-v1',mode:LOCAL_PREVIEW,district:'서울특별시 강동구',districtCode:'11740',origin:ORIGIN,N:2,primaryCount:3,contentRouteCount:4,htmlCount:5,ownershipVerified:false,productionApproved:false,publicApproved:false,indexNowEnabled:false,indexable:false,robots:'noindex,nofollow,noarchive',sitemap:[],pages,common,products:input('product-copy').map(p=>({...p,img:`/images/products/${p.sku}.jpg`,width:500,height:500,assetType:'real_product_sample'})),assets:input('assets'),presentation,futurePublicContract:input('public-preview-contract'),pageContracts,geography,facilities:input('facilities.projection').facilities.map(f=>({...f,legalDongStatus:f.legalDong===null?'unassigned':'retained_official_fact',administrativeDongStatus:'unassigned'})),heldFacilities:input('facilities.projection').holds,inputSHA256:INPUT_PIN};
 validateSemantics(runtime);return runtime;
}
export function validateSemantics(r){
 if(r.schema!=='gangdong-local-static-v1'||r.districtCode!=='11740'||r.district!=='서울특별시 강동구')throw new Error('Wrong region');
 for(const k of ['ownershipVerified','productionApproved','publicApproved','indexNowEnabled','indexable'])if(r[k]!==false)throw new Error(`Unsafe flag ${k}`);
 if(r.origin!==ORIGIN||r.robots!=='noindex,nofollow,noarchive'||r.sitemap.length)throw new Error('Publication boundary');
 if(r.N!==2||r.primaryCount!==3||r.contentRouteCount!==4||r.htmlCount!==5||JSON.stringify(r.pages.map(p=>p.path))!==JSON.stringify(paths))throw new Error('N/route contract');
 const g=r.geography;
 if(g.officialCode!=='11740'||g.parsed.legal.length!==9||g.parsed.administrative.length!==19||g.parsed.relationships.length!==19)throw new Error('Geography denominator');
 if(new Set(g.parsed.legal.map(x=>x.code)).size!==9||new Set(g.parsed.administrative.map(x=>x.code)).size!==19)throw new Error('Duplicate geography');
 const lg=new Set(g.parsed.legal.map(x=>x.code)),ad=new Set(g.parsed.administrative.map(x=>x.code));
 if(new Set(g.parsed.relationships.map(x=>x.administrativeCode+':'+x.legalCode)).size!==19||g.parsed.relationships.some(x=>!lg.has(x.legalCode)||!ad.has(x.administrativeCode)))throw new Error('Geography relation target');
 if(r.facilities.length!==4||r.facilities.some(f=>f.administrativeDong!==null||f.administrativeDongStatus!=='unassigned'||f.externalWreathAcceptanceVerified!==false||(f.legalDong===null)!==(f.legalDongStatus==='unassigned')))throw new Error('Facility assignment');
 if(r.pageContracts.length!==3||r.pageContracts.some(p=>p.editorial_query_class!==p.query_class||p.runtime_query_class!==(p.query_class==='work-commercial'?'local-commercial':'core-commercial')))throw new Error('Query class adapter mapping');
 if(r.heldFacilities.length!==7)throw new Error('Held facility boundary');
 if(r.futurePublicContract.verifiedProductionOrigin!==null||r.futurePublicContract.routes.length!==5)throw new Error('Future public contract');
 const skus=['B201','B203','B205','B060','C200','C203','C204','C205'];const prices=[59000,79000,109000,149000,59000,79000,99000,149000];
 if(JSON.stringify(r.products.map(p=>p.sku))!==JSON.stringify(skus))throw new Error('SKU set');
 r.products.forEach((p,i)=>{if(p.basePriceKRW!==prices[i]||p.cta.href!==`https://fwith.co.kr/shop/item.php?it_id=${p.sku}`||p.img!==`/images/products/${p.sku}.jpg`||p.width!==500||p.height!==500||p.family!==(i<4?'condolence':'wedding')||!p.alt)throw new Error('Product binding');});
 if(r.common.phone.href!=='tel:18440644'||r.common.phone.display!=='1844-0644'||r.common.banners.length!==3||r.common.banners.some(b=>b.caption!==null))throw new Error('Phone/banner binding');
 for(const p of r.pages){
  if(!p.firstAnswer||!p.title||!p.h1)throw new Error('Missing title/first answer');normalizeFaq(p.faqs);
  const placements=p.bannerPlacement;if(['directory','404'].includes(p.id)){if(placements.length)throw new Error('Support banner exception');}else if(JSON.stringify(placements.map(b=>b.banner))!==JSON.stringify(['message','budget','consultation']))throw new Error('Banner order');
 }
 if(planDirectoryBannerSplit([r.pages[3].cards.length],false).enabled||r.pages[3].cards.length!==2)throw new Error('Two-child directory');
 const links=[];function walk(v){if(Array.isArray(v))v.forEach(walk);else if(v&&typeof v==='object'){for(const [k,val]of Object.entries(v)){if(k==='href')links.push(val);else walk(val);}}}walk(r.pages);walk(r.common);walk(r.products);
 const httpAllowed=new Set();
 for(const href of links){if(href.startsWith('#')||href.startsWith('/')){if(href.startsWith('//'))throw new Error('Unsafe link');continue;}if(href==='tel:18440644')continue;const u=new URL(href);if(u.username||u.password||(u.protocol!=='https:'&&!httpAllowed.has(href)))throw new Error('Source link boundary');}
 return true;
}
export function validateRuntime(runtime,root=rootDefault){validateSemantics(runtime);const exact=generateRuntime(root);if(canonical(runtime)!==canonical(exact))throw new Error('Runtime differs from frozen Gangdong projection');return true;}
