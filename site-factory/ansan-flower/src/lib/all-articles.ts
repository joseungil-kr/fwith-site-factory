import {getCollection,type CollectionEntry} from 'astro:content';
import {manualPages} from './manual-runtime.mjs';
export type SiteArticle=CollectionEntry<'articles'>|CollectionEntry<'manualArticles'>;
export function isArticleVisible(data: SiteArticle['data']): boolean {
 return 'publicationMode' in data ? data.publicationMode==='manual-user-request' : ['approved','published'].includes(data.draftStatus);
}
export async function getVisibleArticles(_name:'articles',filter?:(entry:SiteArticle)=>boolean):Promise<SiteArticle[]> {
 const frozen=await getCollection('articles');
 const manual=await getCollection('manualArticles');
 const bound=new Set(manualPages.map((p:{pageKey:string})=>p.pageKey));
 if(manual.length!==bound.size||manual.some(p=>!bound.has(p.data.pageKey)))throw new Error('Manual collection/route binding mismatch');
 const all:SiteArticle[]=[...frozen,...manual];
 return filter?all.filter(filter):all;
}
