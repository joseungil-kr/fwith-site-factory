/** Only reviewed exact H2 headings can become destination fragments. */
export function reviewedHeadingAnchors(blocks,specs){
 if(specs==null)return new Map();
 if(!Array.isArray(specs))throw new Error('Facility anchors must be an array');
 const result=new Map(),ids=new Set();
 for(const spec of specs){
  if(!spec||!/^[-a-z0-9]+$/.test(spec.anchor)||!spec.heading||ids.has(spec.anchor)||result.has(spec.heading))throw new Error('Invalid/duplicate reviewed heading anchor');
  if(blocks.filter(b=>b.type==='h2'&&b.text===spec.heading).length!==1)throw new Error('Reviewed facility H2 missing or duplicated: '+spec.heading);
  ids.add(spec.anchor);result.set(spec.heading,spec.anchor);
 }
 return result;
}
