import truth from '../data/business-truth.json';
import architecture from '../data/architecture.json';
import pages from '../data/pages.json';
import config from '../data/site-config.json';
import instances from '../data/site-instances.json';
import regions from '../data/regions-matrix.json';
import {selectInstance} from '../lib/matrix.mjs';

const instance = selectInstance(instances, import.meta.env.SITE_INSTANCE || config.defaultInstance);
const domain = (import.meta.env.SITE_URL || instance.domain).replace(/\/$/, '');
const areaServed = regions.filter((r:any)=>instance.enabledRegions.includes(r.key)).map((r:any)=>r.name);
export const site = {
  instanceKey: instance.key,
  siteName: instance.siteName,
  brand: instance.brand || truth.brand,
  region: instance.coverageLabel,
  coverageLabel: instance.coverageLabel,
  areaServed,
  domain,
  themeAccent: instance.design?.accent || '#3a214f',
  indexable: import.meta.env.SITE_INDEXABLE === 'true' && config.productionApproved === true && instance.deployable === true,
  phone: instance.phone || truth.phone,
  phoneHref: instance.phoneHref || truth.phoneHref,
  orderUrl: instance.orderUrl || truth.onlineOrderUrl,
  phoneOrderHours: truth.phoneOrderHours.replace('-', '~'),
  onlineOrderHours: truth.onlineOrderHours,
  orderHours: `전화 ${truth.phoneOrderHours.replace('-', '~')} · 온라인 ${truth.onlineOrderHours} 접수`,
  deliveryNotice: truth.deliveryNotice,
  productVariationNotice: truth.productVariationNotice,
  naverVerification: config.naverVerification || ''
};
const publishedPages = pages as {category:string}[];
export const groups = architecture.hubs.filter(h => publishedPages.some(p => p.category === h.category)).map(h => ({cat: h.category, label: h.label, url: h.url}));
export const serviceGroups = groups.filter(group => group.cat !== 'regions');
export const menuGroups:any[] = [];
