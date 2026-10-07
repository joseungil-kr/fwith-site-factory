import {getCollection} from 'astro:content';
export async function getArticleCollection(_name:string, filter?: (entry:any)=>boolean) { const all=[...await getCollection('articles'),...await getCollection('manualArticles')];return filter?all.filter(filter):all; }
