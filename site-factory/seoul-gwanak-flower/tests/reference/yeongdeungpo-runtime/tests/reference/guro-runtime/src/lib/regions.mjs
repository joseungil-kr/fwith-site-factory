/** Guro-only additive dispatcher. All other modes use the byte-preserved v1 adapter. */
import * as legacy from './regions-legacy.mjs';
import * as guro from './guro-regions.mjs';
export {isRegional,hubState,regionalCustomerClaims} from './regions-legacy.mjs';
export const regionalMetadataFields=legacy.regionalMetadataFields;
const adapter=(c,p)=>guro.isGuroMode(c,p)?guro:legacy;
export const validateDefinition=(c,p)=>adapter(c,p).validateDefinition(c,p);
export const regionalRows=(rows,a,c,p)=>adapter(c,p).regionalRows(rows,a,c,p);
export const directoryGroups=(rows,a,c,p)=>adapter(c,p).directoryGroups(rows,a,c,p);
export const aliasTargets=(name,rows,a,c,p)=>adapter(c,p).aliasTargets(name,rows,a,c,p);
export const regionalMetadata=(c,p,products,key)=>adapter(c,p).regionalMetadata(c,p,products,key);
export const assertRegionalMetadata=(record,c,p,products)=>adapter(c,p).assertRegionalMetadata(record,c,p,products);
export function validateRegionalPurchase(page,products,text='') {
 legacy.validateRegionalPurchase(page,products,text);
 if(page.scopeKey===guro.scopeKey)guro.validatePurchaseIntent(page);
}
