export function splitBannerContent(html) {
  const boundaries=[]; const stack=[];
  const voidTags=new Set(['area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr']);
  const tokens=/<!--[\s\S]*?-->|<(\/?)([a-zA-Z][\w:-]*)\b(?:"[^"]*"|'[^']*'|[^'">])*?>/g;
  for (const match of html.matchAll(tokens)) {
    if (!match[2]) continue;
    const tag=match[2].toLowerCase();
    if (match[1]) {
      const position=stack.lastIndexOf(tag);
      if (position>=0) stack.length=position;
      if (!stack.length && ['p','ul','ol','blockquote','section','div','table','figure'].includes(tag)) boundaries.push(match.index+match[0].length);
    } else if (!voidTags.has(tag) && !/\/\s*>$/.test(match[0])) stack.push(tag);
  }
  const interior=boundaries.filter(n=>n<html.trimEnd().length);
  if (!interior.length) throw new Error('Shared banners require at least two balanced article blocks');
  const middle=interior.reduce((best,n)=>Math.abs(n-html.length/2)<Math.abs(best-html.length/2)?n:best,interior[0]);
  return [html.slice(0,middle),html.slice(middle)];
}

// Shared artwork captions are not editorial body copy or order-CTA quota input.
export function stripSharedFlowerBanners(html) {
  return html.replace(/<figure\b[^>]*\bdata-shared-flower-banner=["'][^"']+["'][^>]*>[\s\S]*?<\/figure>/gi, ' ');
}

// Keep the original order CTA injector's distances in its original body coordinate
// space. Shared artwork must not shift pre-existing editorial block boundaries.
export function originalOrderBannerPositions(html, fractions) {
  const shared=/<figure\b[^>]*\bdata-shared-flower-banner=["'][^"']+["'][^>]*>[\s\S]*?<\/figure>/gi;
  const removed=[...html.matchAll(shared)].map(m=>({start:m.index,end:m.index+m[0].length}));
  const cleanOffset=offset=>offset-removed.filter(r=>r.end<=offset).reduce((n,r)=>n+r.end-r.start,0);
  const boundaries=[...html.matchAll(/<\/(?:p|ul|ol|blockquote)>/gi)]
    .map(m=>m.index+m[0].length).filter(pos=>!removed.some(r=>r.start<pos&&pos<=r.end));
  if(!boundaries.length)return [];
  const length=html.length-removed.reduce((n,r)=>n+r.end-r.start,0);
  return fractions.map(fraction=>{
    const target=Math.floor(length*fraction);
    return boundaries.reduce((best,pos)=>Math.abs(cleanOffset(pos)-target)<Math.abs(cleanOffset(best)-target)?pos:best,boundaries[0]);
  });
}
