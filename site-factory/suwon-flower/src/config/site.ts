import truth from '../data/business-truth.json';
import architecture from '../data/architecture.json';
import pages from '../lib/all-pages.mjs';
const domain = (import.meta.env.SITE_URL || 'https://suwon.fwith.kr').replace(/\/$/, '');
export const site = {
  brand: truth.brand, region: '수원', domain,
  indexable: import.meta.env.SITE_INDEXABLE === 'true',
  phone: truth.phone, phoneHref: truth.phoneHref, orderUrl: truth.onlineOrderUrl,
  phoneOrderHours: truth.phoneOrderHours.replace('-', '~'),
  onlineOrderHours: truth.onlineOrderHours,
  orderHours: `전화 ${truth.phoneOrderHours.replace('-', '~')} · 온라인 ${truth.onlineOrderHours} 접수`,
  deliveryNotice: truth.deliveryNotice, productVariationNotice: truth.productVariationNotice,
  naverVerification: '80fedf144567fea99fe833d2937731a190854c41'
};
const manualHubs = [{category:"regions",label:"지역별 주문",url:"/regions/"}];
export const groups = [...architecture.hubs,...manualHubs].filter(h => pages.some(p => p.category === h.category)).map(h => ({cat: h.category, label: h.label, url: h.url}));


// Frozen regional inventory keeps its five-page menu threshold. Manual district guides are separately approved.
export const regionalMenuEligible = pages.some(p=>p.category==='regions' && p.publicationMode==='manual-user-request') || (pages as {category:string}[]).filter(p=>p.category==='regions').length>=5;
