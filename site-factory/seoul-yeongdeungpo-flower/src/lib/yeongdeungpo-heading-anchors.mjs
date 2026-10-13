/** The frozen Yeongdeungpo N2 copy has funeral H3 and wedding H2 anchors.
 * Original H2-only helper remains byte-preserved for its inherited modes.
 */
import plan from '../data/yeongdeungpo-plan-binding.json' with {type:'json'};
import copy from '../data/yeongdeungpo-copy.json' with {type:'json'};
import {markdownBlocks} from './content.mjs';
export function reviewedHeadingAnchors(blocks,specs){
 const representative=plan.representatives.find(r=>JSON.stringify(r.facilityAnchors)===JSON.stringify(specs));
 if(!representative)throw new Error('Yeongdeungpo heading anchors require exact frozen member binding');
 const article=copy.articles.find(a=>a.slug===representative.slug);
 const approvedBlocks=markdownBlocks(article.contentMarkdown);
 const result=new Map(),ids=new Set();
 for(const spec of specs){
  const original=approvedBlocks.filter(b=>['h2','h3'].includes(b.type)&&b.text===spec.heading);
  const actual=blocks.filter(b=>['h2','h3'].includes(b.type)&&b.text===spec.heading);
  if(original.length!==1||actual.length!==1||actual[0].type!==original[0].type||ids.has(spec.anchor)||result.has(spec.heading))throw new Error('Yeongdeungpo reviewed heading missing, duplicated or level changed: '+spec.heading);
  ids.add(spec.anchor);result.set(spec.heading,spec.anchor);
 }
 return result;
}
