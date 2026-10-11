import {getCollection} from 'astro:content';
import {manual} from './manual-source.mjs';
/** @param {string} _name @param {((entry: {data: Record<string, any>}) => boolean)=} filter */
export async function getDisplayArticles(_name,filter){
 const old=await getCollection('articles');
 const authored=await getCollection('manualArticles');
 const replaced=new Set(manual.pages.map(p=>p.pageKey));
 const rows=[...old.filter(a=>!replaced.has(a.data.pageKey)),...authored];
 return filter?rows.filter(filter):rows;
}
