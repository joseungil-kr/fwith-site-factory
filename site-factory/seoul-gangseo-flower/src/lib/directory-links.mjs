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
