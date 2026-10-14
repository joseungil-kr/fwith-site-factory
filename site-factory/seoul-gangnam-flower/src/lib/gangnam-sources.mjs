/** Exact public HTTP sources reviewed for Gangnam only. The shared HTTPS validator is unchanged. */
import {pageSources as httpsSources} from './sources.mjs';
const exactHttp=new Set([
 'http://www.samsunghospital.com/home/funerals/guide.do?view=procedure',
 'http://www.samsunghospital.com/home/funerals/service.do?view=flower'
]);
export function pageSources(page){
 const values=page.sources==null?(page.source?[page.source]:[]):page.sources;
 if(!Array.isArray(values))throw new Error('Page sources must be an array');
 for(const source of values){
  if(exactHttp.has(source?.url)){
   // The equivalent HTTPS string is syntax validation only, never an output URL or a network request.
   httpsSources({sources:[{...source,url:'https:'+source.url.slice(5)}]});
   if(source.type!=='official'||source.verifiedAt!=='2026-10-13')throw new Error('Unreviewed HTTP provenance');
  }else httpsSources({sources:[source]});
 }
 return values;
}
export const isExactReviewedHttp=value=>exactHttp.has(value);
