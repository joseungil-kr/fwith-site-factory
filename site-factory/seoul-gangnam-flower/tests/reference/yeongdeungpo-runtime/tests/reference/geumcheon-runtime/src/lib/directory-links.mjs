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

/** Named destinations preserve distinct fragments on a shared canonical article. */
export function publishedDestinationsByUnit(groups) {
 const result=new Map();
 for(const d of groups)for(const entry of d.items){
  const anchors=entry.representative.facilityAnchors;
  if(anchors!=null&&!Array.isArray(anchors))throw new Error('Invalid reviewed facility anchors');
  const destinations=anchors||entry.representative.unitKeys.map(unitKey=>({unitKey,href:entry.page.url,heading:entry.page.primaryKeyword,candidateId:entry.page.pageKey}));
  for(const a of destinations){
   if(!entry.representative.unitKeys.includes(a.unitKey)||!a.href||!a.heading)throw new Error('Destination/unit binding mismatch');
   const list=result.get(a.unitKey)||[];
   if(!list.some(x=>x.href===a.href))list.push({href:a.href,name:a.heading,candidateId:a.candidateId});
   result.set(a.unitKey,list);
  }
 }
 return result;
}
