import fs from 'node:fs';
import crypto from 'node:crypto';
import spec from '../data/frozen/content-spec.ko.json' with {type:'json'};
import {planDirectoryBannerSplit} from './directory-banner-split.mjs';

export const REVIEWED_SPEC_SHA256='90f43c2fb14ca8756453f1b2af1339f68e1ec24d3b38cb06f09a4cf73fd12f44';
export const previewConfig=Object.freeze({mode:'private-local-preview',origin:null,productionEnabled:false,coreHubLaunchStatus:'NOT_ASSESSED',fullLaunchStatus:'NOT_ASSESSED'});
export function assertBoundary(config=previewConfig,env=process.env){
 if(config.mode!=='private-local-preview'||config.origin!==null||config.productionEnabled!==false||config.coreHubLaunchStatus!=='NOT_ASSESSED'||config.fullLaunchStatus!=='NOT_ASSESSED') throw new Error('Mokpo preview boundary: production/origin/launch promotion is not supported');
 for(const key of ['SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION']) if(env[key]) throw new Error(`Mokpo preview boundary: ${key} must not be set`);
 return true;
}
export const sha256=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
export function verifyFrozenInputs(){
 const bytes=fs.readFileSync(new URL('../data/frozen/content-spec.ko.json',import.meta.url));
 if(sha256(bytes)!==REVIEWED_SPEC_SHA256)throw new Error('Reviewed specification digest mismatch');
 for(const page of spec.pages){if(!page.sourceDraft)continue;const raw=page.sourceDraft.fullDocumentMarkdown;
  const file=fs.readFileSync(new URL(`../data/frozen/${page.id==='home'?'home':'condolence'}.ko.md`,import.meta.url));
  if(sha256(file)!==page.sourceDraft.sha256||file.toString('utf8')!==raw)throw new Error('Original draft bytes changed');
 }
 return true;
}
// Only the reviewed draft grammar is accepted. No generic markdown or untrusted HTML is injected.
export function parseDraft(markdown){
 const chunks=markdown.trim().split(/\n\n+/);const first=chunks.shift();
 if(!first?.startsWith('# '))throw new Error('Draft needs one H1');
 const result={h1:first.slice(2),opening:[],sections:[]};let section=null;
 for(const chunk of chunks){
  if(chunk.startsWith('## ')){section={heading:chunk.slice(3),blocks:[]};result.sections.push(section);continue;}
  const list=section?section.blocks:result.opening;
  if(chunk.startsWith('### ')){list.push({kind:'h3',text:chunk.slice(4)});continue;}
  if(/^#/.test(chunk))throw new Error('Unsupported draft heading');
  if(chunk==='버튼: 근조 상품과 주문 안내\n목적지: /regions/hankook-hospital-funeral-wreath/')list.push({kind:'action',label:'근조 상품과 주문 안내',href:'/regions/hankook-hospital-funeral-wreath/'});
  else if(chunk==='버튼: 전화로 주문 상담 / tel:18440644')list.push({kind:'action',label:'전화로 주문 상담',href:'tel:18440644'});
  else if(chunk==='목포한국병원 장례식장 근조화환 상담: 1844-0644')list.push({kind:'action',label:chunk,href:'tel:18440644'});
  else if(chunk.startsWith('버튼:')||chunk.startsWith('목적지:'))throw new Error('Unknown draft control');
  else list.push({kind:'paragraph',text:chunk});
 }
 return result;
}
export const banners=[
 {id:'message',assetName:'flower-message.webp',alt:'흰 장미와 잎을 배경으로 꽃으로 전하는 마음을 안내하는 꽃이랑 배너. 전화 1844-0644.',sha256:'a5ecdeb1914566a32d45b084351e2782fc8b234e9a4fbb8635a60a9921cac5f5'},
 {id:'budget',assetName:'flower-budget.webp',alt:'겹겹의 흰 꽃을 배경으로 상품 사진과 가격 비교를 안내하는 꽃이랑 배너. 전화 1844-0644.',sha256:'081198095eb005603721be7c778f4d477f4dd93dcf96f0c261f18bf06bb91421'},
 {id:'consultation',assetName:'flower-consultation.webp',alt:'흰 꽃과 봉오리를 배경으로 상품 선택과 리본 문구 상담을 안내하는 꽃이랑 배너. 전화 1844-0644.',sha256:'d6654aa44c365f64e330d0be2042972d3320fad54231425aaffca1dfdcd25ebc'},
];
export const products=spec.productCards.map(p=>({...p,img:`/images/products/${p.sku}.jpg`,width:500,height:500}));
export const pages=spec.pages.map(p=>({...p,draft:p.sourceDraft?parseDraft(p.sourceDraft.fullDocumentMarkdown):null}));
export const supportBannerPlan=planDirectoryBannerSplit([1],false);
export const pageMap={
 ...previewConfig,articleCount:1,primaryCount:2,supportCount:1,contentHtmlCount:3,technicalHtmlCount:1,allHtmlCount:4,previewIndexableCount:0,previewSitemapUrlCount:0,
 pages:pages.map(p=>({id:p.id,path:p.path,role:p.role,parentPath:p.parentPath,article:p.article,coreHub:false,robots:'noindex,follow',canonical:null,sitemapIncluded:false,mainMenuIncluded:p.id==='home'||p.article,actualChildCount:p.id==='regions-support'?1:0,marketingBannerCount:p.sourceDraft?3:0})),
 productionProposal:{active:false,origin:null,paths:['/','/regions/hankook-hospital-funeral-wreath/'],indexTargetCount:2,sitemapTargetCount:2},
};
export function validateRuntime(){
 assertBoundary();verifyFrozenInputs();
 if(pages.length!==4||pages.filter(p=>p.article).length!==1)throw new Error('Mokpo denominator changed');
 if(spec.origin!==null||spec.architecture.coreHubLaunchStatus!=='not_assessed'||spec.architecture.fullLaunchStatus!=='not_assessed')throw new Error('Unapproved origin or launch status');
 if(products.map(p=>p.sku).join(',')!=='B201,B203,B205,B060')throw new Error('Product set changed');
 for(const p of products){if(p.cta.href!==`https://fwith.co.kr/shop/item.php?it_id=${p.sku}`)throw new Error('Product destination mismatch');}
 if(pages.find(p=>p.id==='regions-support').contentCards.length!==1||supportBannerPlan.enabled)throw new Error('Support navigation must have one real child and no banners');
 const article=pages.find(p=>p.article);const faq=article.draft.sections.find(s=>s.heading==='자주 묻는 질문');
 for(const item of spec.faqs){if(faq.blocks.filter(b=>b.kind==='h3'&&b.text===item.question).length!==1||faq.blocks.filter(b=>b.kind==='paragraph'&&b.text===item.answer).length!==1)throw new Error('FAQ projection mismatch');}
 return true;
}
export {spec};
