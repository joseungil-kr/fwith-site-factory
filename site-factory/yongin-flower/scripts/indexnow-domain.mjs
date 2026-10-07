export const canonicalOrigin='https://yongin.fwith.kr';
export function validateIndexNowDomain(origin,urls=[]){
 if(origin!==canonicalOrigin)throw Error('INDEXNOW_WRONG_ORIGIN');
 if(!Array.isArray(urls))throw Error('INDEXNOW_INVALID_URLS');
 for(const raw of urls){const u=new URL(raw);if(u.origin!==canonicalOrigin||u.username||u.password)throw Error('INDEXNOW_WRONG_URL_HOST');}
 return true;
}
