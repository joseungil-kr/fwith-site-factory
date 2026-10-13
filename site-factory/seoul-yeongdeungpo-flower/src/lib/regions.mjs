/** Explicit Guro, Geumcheon and Yeongdeungpo additive dispatcher; legacy remains byte-preserved. */
import * as legacy from './regions-legacy.mjs';
import * as guro from './guro-regions.mjs';
import * as geumcheon from './geumcheon-regions.mjs';
import * as yeongdeungpo from './yeongdeungpo-regions.mjs';
export {isRegional,hubState,regionalCustomerClaims} from './regions-legacy.mjs';
export const regionalMetadataFields=legacy.regionalMetadataFields;
const adapter=(c,p)=>{
 const g=guro.isGuroMode(c,p),k=geumcheon.isGeumcheonMode(c,p),y=yeongdeungpo.isYeongdeungpoMode(c,p);
 if([g,k,y].filter(Boolean).length>1)throw new Error('Regional adapter cross-site opt-in mismatch');
 return y?yeongdeungpo:k?geumcheon:g?guro:legacy;
};
export const validateDefinition=(c,p)=>adapter(c,p).validateDefinition(c,p);
export const regionalRows=(rows,a,c,p)=>adapter(c,p).regionalRows(rows,a,c,p);
export const directoryGroups=(rows,a,c,p)=>adapter(c,p).directoryGroups(rows,a,c,p);
export const aliasTargets=(name,rows,a,c,p)=>adapter(c,p).aliasTargets(name,rows,a,c,p);
export const regionalMetadata=(c,p,products,key)=>adapter(c,p).regionalMetadata(c,p,products,key);
export const assertRegionalMetadata=(record,c,p,products)=>adapter(c,p).assertRegionalMetadata(record,c,p,products);
export function validateRegionalPurchase(page,products,text='') {
 legacy.validateRegionalPurchase(page,products,text);
 if(page.scopeKey===guro.scopeKey)guro.validatePurchaseIntent(page);
 if(page.scopeKey===geumcheon.scopeKey)geumcheon.validatePurchaseIntent(page);
 if(page.scopeKey===yeongdeungpo.scopeKey)yeongdeungpo.validatePurchaseIntent(page);
}
