import coverage from '../data/region-coverage.json' with {type:'json'};
import policy from '../data/region-policy.json' with {type:'json'};
import manifest from '../data/publish-manifest.json' with {type:'json'};
import architecture from '../data/architecture.json' with {type:'json'};
import {regionalRows,directoryGroups,regionalMetadataFields} from './regions.mjs';
export {coverage,policy,architecture};
const emptyCoverage={schemaVersion:2,siteKey:'template-only',scopeKey:'',unitBasis:'legal-dong-plus-eup-myeon',countIsPageQuota:false,verifiedAt:'',sourceBasisDate:'',officialSourceUrls:[],membershipSourceSha256:'',districts:[],units:[],administrativeCrosswalk:[],representatives:[]};
const emptyPolicy={schemaVersion:1,siteKey:'template-only',scopeKey:'',enabled:false,officialHosts:[],unitTypes:[],rulesRevision:'',definitionFile:'src/data/region-coverage.json',state:'unbound-template',membershipSourceSha256:'',visualBindings:[]};
const canonical=value=>JSON.stringify(value,(_,item)=>item&&typeof item==='object'&&!Array.isArray(item)?Object.fromEntries(Object.keys(item).sort().map(key=>[key,item[key]])):item);
/** Only the exact unbound zero-content template skips geography validation.
 * Bound candidate sources always use the unchanged shared schema-2 adapter.
 */
export function isUnboundTemplate(c,p,a,m){
 if(c?.siteKey!=='template-only'&&p?.siteKey!=='template-only'&&c?.scopeKey&&p?.scopeKey)return false;
 if(canonical(c)!==canonical(emptyCoverage)||canonical(p)!==canonical(emptyPolicy)||a?.siteKey!=='template-only'||m?.siteKey!=='template-only'||!Array.isArray(a.pages)||a.pages.length||!Array.isArray(m.pages)||m.pages.length||canonical(m.snapshotLedger)!=='{}')throw new Error('Invalid unbound regions template');
 return true;
}
const unbound=isUnboundTemplate(coverage,policy,architecture,manifest);
export const regionalPages=unbound?[]:regionalRows(manifest.pages,architecture,coverage,policy);
export function groupsFor(pages){
 if(unbound){if(pages.length)throw new Error('Unbound template cannot contain customer pages');return [];}
 return directoryGroups(pages,architecture,coverage,policy);
}
export function assertRegionalInput(pages){
 if(unbound&&pages.length)throw new Error('Unbound template cannot contain customer pages');
 const regional=pages.filter(p=>p.category==='regions'||p.pageType==='regional-service');
 if(regional.length!==regionalPages.length)throw new Error('Regional input/manifest count mismatch');
 for(const page of regional){const frozen=regionalPages.find(p=>p.pageKey===page.pageKey);
  for(const field of ['pageKey','snapshotId','slug','category','pageType',...regionalMetadataFields])if(JSON.stringify(page[field])!==JSON.stringify(frozen?.[field]))throw new Error('Regional input/manifest mismatch '+field);
 }
 return regionalPages;
}
