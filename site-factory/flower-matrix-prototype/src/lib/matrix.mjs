export function selectInstance(instances,key){
  const found=instances.find(x=>x.key===key);
  if(!found) throw new Error('Unknown SITE_INSTANCE: '+key);
  return found;
}
export function enabledRows(instance,regions,groups){
  const regionMap=new Map(regions.map(x=>[x.key,x]));
  const groupMap=new Map(groups.map(x=>[x.key,x]));
  const enabledRegions=instance.enabledRegions.map(k=>regionMap.get(k));
  const enabledGroups=instance.enabledProductGroups.map(k=>groupMap.get(k));
  if(enabledRegions.some(x=>!x)||enabledGroups.some(x=>!x)) throw new Error('Instance references unknown region/product group');
  return {regions:enabledRegions,groups:enabledGroups};
}
export function matrixPages(instance,regions,groups){
  const enabled=enabledRows(instance,regions,groups);
  const rows=[];
  for(const region of enabled.regions) for(const group of enabled.groups){
    const url=`/${region.slug}/${group.slug}/`;
    rows.push({
      key:`${region.key}|${group.key}`,url,region,group,
      title:`${region.name} ${group.label} | ${instance.brand}`,
      h1:`${region.name} ${group.label} 주문 안내`,
      description:`${region.name}에서 ${group.label}을 준비할 때 실제 상품 원문과 주문에 필요한 수령정보를 확인하세요. 주소별 추가 배송비와 도착 가능시간은 주문 전에 확인합니다.`
    });
  }
  const urls=rows.map(x=>x.url),keys=rows.map(x=>x.key);
  if(new Set(urls).size!==urls.length||new Set(keys).size!==keys.length) throw new Error('Duplicate matrix page identity');
  return rows;
}
export function productsFor(group,products){
  const byCode=new Map(products.map(x=>[x.code,x]));
  const rows=group.sourceProductCodes.map(code=>byCode.get(code));
  if(rows.some(x=>!x)) throw new Error('Missing product source for '+group.key);
  return rows;
}
