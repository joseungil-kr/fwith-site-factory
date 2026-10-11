import coverage from '../data/region-coverage.json' with {type:'json'};
import policy from '../data/region-policy.json' with {type:'json'};
import manifest from '../data/publish-manifest.json' with {type:'json'};
import architecture from '../data/architecture.json' with {type:'json'};
import {regionalRows,directoryGroups,regionalMetadataFields} from './regions.mjs';
import {manualPages} from './manual-runtime.mjs';
import {manualDirectoryGroups,assertRegionalKeySet} from './manual-regions.mjs';
export {coverage,policy,architecture};
const frozenRegionalPages=regionalRows(manifest.pages,architecture,coverage,policy);
const manualRegionalPages=manualPages.filter(p=>p.category==='regions');
export const regionalPages=[...frozenRegionalPages,...manualRegionalPages];
export function groupsFor(pages){const groups=directoryGroups(pages.filter(p=>p.publicationMode!=='manual-user-request'),architecture,coverage,policy);for(const group of manualDirectoryGroups(pages,coverage)){const existing=groups.find(g=>g.key===group.key);if(existing)existing.items.push(...group.items);else groups.push(group);}return groups;}
export function assertRegionalInput(pages){
 const regional=pages.filter(p=>p.category==='regions'||p.pageType==='regional-service');
 assertRegionalKeySet(regional,regionalPages);
 if(regional.length!==regionalPages.length)throw new Error('Regional input/manifest count mismatch');
 for(const page of regional){const frozen=regionalPages.find(p=>p.pageKey===page.pageKey);
  for(const field of ['pageKey',...('publicationMode' in page?['manualPageId','publicationMode']:['snapshotId']),'slug','category','pageType',...regionalMetadataFields])if(JSON.stringify(page[field])!==JSON.stringify(frozen?.[field]))throw new Error('Regional input/manifest mismatch '+field);
 }
 return regionalPages;
}
