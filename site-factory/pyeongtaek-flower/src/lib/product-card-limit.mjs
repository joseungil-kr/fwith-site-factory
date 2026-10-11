import {productFamilies} from './catalog.mjs';

const JINWI = Object.freeze({
  pageKey: 'pyeongtaek-flower-v2-region-jinwi-myeon',
  slug: 'jinwi-myeon',
  url: '/regions/jinwi-myeon/',
  category: 'regions',
  pageType: 'regional-service',
  regionalPurchaseMode: 'catalog',
});
const FAMILIES = Object.freeze(['congrats', 'funeral']);
const REGIONAL_KEYS = Object.freeze([
  'congrats-basic', 'congrats-premium', 'congrats-large', 'congrats-xl',
  'funeral-basic', 'funeral-premium', 'funeral-large', 'funeral-xl',
]);
const CARD_KEYS = Object.freeze([
  'congrats-basic', 'funeral-basic', 'congrats-premium', 'congrats-large',
  'congrats-xl', 'funeral-premium', 'funeral-large', 'funeral-xl',
]);
const sameArray = (actual, expected) => Array.isArray(actual)
  && actual.length === expected.length
  && actual.every((value, i) => value === expected[i]);

/** Only the reviewed Jinwi comparison may opt in to eight real product cards. */
export function resolveProductCardLimit(page, products) {
  if (page.productCardLimit === '8') throw new Error('Eight-card limit must be numeric');
  if (page.productCardLimit !== 8) {
    // Preserve the previous ordinary-page expression exactly.
    return page.productCardLimit === 4 || productFamilies(page).length > 3 ? 4 : 3;
  }
  if (Object.entries(JINWI).some(([field, expected]) => page[field] !== expected)
      || !sameArray(page.regionalProductFamilies, FAMILIES)
      || !sameArray(page.regionalProductKeys, REGIONAL_KEYS)
      || !sameArray(page.productCardKeys, CARD_KEYS)) {
    throw new Error('Eight-card opt-in is restricted to the exact reviewed Jinwi tuple');
  }
  if (!Array.isArray(products)) throw new Error('Eight-card opt-in requires the real catalog');
  for (const key of CARD_KEYS) {
    const matches = products.filter(product => product.key === key);
    const family = key.startsWith('congrats-') ? 'congrats' : 'funeral';
    if (matches.length !== 1 || matches[0].family !== family) {
      throw new Error(`Eight-card catalog binding is invalid: ${key}`);
    }
  }
  return 8;
}
