export const SESSION_SHORT_SECONDS = 8 * 60 * 60;
export const SESSION_REMEMBER_SECONDS = 30 * 24 * 60 * 60;
export const sessionDurationSeconds = remember => remember === true ? SESSION_REMEMBER_SECONDS : SESSION_SHORT_SECONDS;
export const DEFAULT_PRODUCTS = [
  ['잉어반죽',6850,11000],['팥앙금',5150,9000],['슈크림',5150,9000],
  ['어묵',4500,7000],['주전자',9000,10000],['갈고리',1500,2000]
];
export const onlyInt = (v, name='수량', min=0, max=1000000) => {
  if (typeof v !== 'number' || !Number.isSafeInteger(v) || v < min || v > max) throw new Error(`${name}: ${min}~${max} 정수를 입력하세요`);
  return v;
};
export const safeText = (v, name, required=false, max=180) => {
  const s=String(v??'').trim();
  if ((required&&!s)||s.length>max) throw new Error(`${name}: 필수 입력 또는 길이 오류`);
  return s;
};
export const dateCheck=(v)=>{const s=String(v||'');if(!/^\d{4}-\d{2}-\d{2}$/.test(s)||new Date(s+'T00:00:00Z').toISOString().slice(0,10)!==s)throw new Error('날짜 형식 오류');return s};
export const calcTotals = (items, vat) => {
  if(!['tax','none'].includes(vat))throw new Error('부가세 선택 오류');
  const supply=items.reduce((s,i)=>s+onlyInt(i.qty,'수량',1,999999)*onlyInt(i.unit_price,'단가',0,100000000),0);
  if(!Number.isSafeInteger(supply)||supply>2_000_000_000)throw new Error('거래금액 한도 초과');
  const tax=vat==='tax'?Math.round(supply*.1):0;
  return {supply,tax,total:supply+tax};
};
export const calculatePayable=(saleTotal,previousBalance=0)=>{
  const sale=onlyInt(saleTotal,'출고금액',0,2_000_000_000);
  const balance=onlyInt(previousBalance,'전 잔고',0,2_000_000_000);
  if(sale+balance>2_000_000_000)throw new Error('최종 청구금액 한도 초과');
  return sale+balance;
};
export const stockRemaining=(opening,entries)=>entries.reduce((n,e)=>n+e.delta,opening);
