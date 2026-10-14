// A legal dong can host several distinct reviewed facility/purchase contexts.
export function publishedEntriesByUnit(groups) {
  const result=new Map();
  for(const district of groups) for(const entry of district.items) {
    for(const key of entry.representative.unitKeys) {
      const entries=result.get(key)||[];
      if(!entries.some(item=>item.page.url===entry.page.url)) entries.push(entry);
      result.set(key,entries);
    }
  }
  return result;
}

// Null is permitted only for the explicitly reviewed Gwanak faculty destination.
// Legacy adapters retain their original non-null legal-unit requirement.
const unassignedGwanakFaculty=(district,entry,anchor)=>
 district.key==='seoul-gwanak-gu'&&
 entry.page.scopeKey==='seoul-gwanak-direct-independent-preparation-20261013'&&
 entry.page.url==='/regions/gwanak-celebration-wreath/'&&
 entry.representative.contextKey==='gwanak|celebration-congratulation-wreath'&&
 anchor.candidateId==='snu-faculty'&&anchor.anchor==='snu-faculty'&&
 anchor.href==='/regions/gwanak-celebration-wreath/#snu-faculty'&&
 anchor.heading==='서울대학교 교수회관 65동'&&anchor.unitKey===null;

/** Named destinations preserve distinct fragments on a shared canonical article. */
export function publishedDestinationsByUnit(groups) {
 const result=new Map();
 for(const d of groups)for(const entry of d.items){
  const anchors=entry.representative.facilityAnchors;
  if(anchors!=null&&!Array.isArray(anchors))throw new Error('Invalid reviewed facility anchors');
  const destinations=anchors||entry.representative.unitKeys.map(unitKey=>({unitKey,href:entry.page.url,heading:entry.page.primaryKeyword,candidateId:entry.page.pageKey}));
  for(const a of destinations){
   // Explicit null geography is retained by the separate district-level accessor.
   if(a.unitKey===null){if(!unassignedGwanakFaculty(d,entry,a))throw new Error('Unreviewed null physical destination');continue;}
   if(!entry.representative.unitKeys.includes(a.unitKey)||!a.href||!a.heading)throw new Error('Destination/unit binding mismatch');
   const list=result.get(a.unitKey)||[];
   if(!list.some(x=>x.href===a.href))list.push({href:a.href,name:a.heading,candidateId:a.candidateId});
   result.set(a.unitKey,list);
  }
 }
 return result;
}

/** Physical destinations without a verified legal unit stay at district level.
 * Buyer occasions have their own field and are never promoted to facilities.
 */
export function publishedUnassignedDistrictDestinations(groups) {
 const result=new Map();
 for(const district of groups)for(const entry of district.items){
  const anchors=entry.representative.facilityAnchors;
  if(anchors!=null&&!Array.isArray(anchors))throw new Error('Invalid reviewed facility anchors');
  for(const anchor of anchors||[]){
   if(anchor.unitKey!==null)continue;
   if(!unassignedGwanakFaculty(district,entry,anchor)||anchor.contextType==='buyer-occasion')throw new Error('Invalid district-level physical destination');
   const list=result.get(district.key)||[];
   if(!list.some(item=>item.href===anchor.href))list.push({href:anchor.href,name:anchor.heading,candidateId:anchor.candidateId});
   result.set(district.key,list);
  }
 }
 return result;
}
