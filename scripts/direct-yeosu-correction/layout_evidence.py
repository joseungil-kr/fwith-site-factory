"""Read actual heading geometry and retain natural-scroll evidence. No DOM/CSS edits.
Range rectangles are browser text-layout evidence, not proof of exact painted ink;
independent screenshots remain required for Korean glyph readability acceptance.
"""
import hashlib,json,math
from pathlib import Path
HEADING_METRICS_JS=r'''() => {
 const rect=r=>({left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height});
 return [...document.querySelectorAll('.copy-section h2')].map(h=>{
  const card=h.closest('.copy-section'),c=card.getBoundingClientRect(),cs=getComputedStyle(card),hs=getComputedStyle(h);
  const content={left:c.left+parseFloat(cs.borderLeftWidth)+parseFloat(cs.paddingLeft),right:c.right-parseFloat(cs.borderRightWidth)-parseFloat(cs.paddingRight)};
  const walker=document.createTreeWalker(h,NodeFilter.SHOW_TEXT);let node;const glyphs=[];
  while(node=walker.nextNode()){
   let offset=0;
   for(const char of node.textContent){const start=offset;offset+=char.length;if(!char.trim())continue;
    const range=document.createRange();range.setStart(node,start);range.setEnd(node,offset);
    const boxes=[...range.getClientRects()].filter(r=>r.width>0&&r.height>0);
    glyphs.push({char,rects:boxes.map(rect)});
   }
  }
  const clips=[];
  for(let a=h.parentElement;a;a=a.parentElement){const s=getComputedStyle(a);if(['hidden','clip'].includes(s.overflowX)||['hidden','clip'].includes(s.overflowY))clips.push({tag:a.tagName,id:a.id,overflowX:s.overflowX,overflowY:s.overflowY,rect:rect(a.getBoundingClientRect())});}
  return {text:h.textContent.trim(),sectionId:card.id||null,visible:h.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}),headingBox:rect(h.getBoundingClientRect()),contentBox:content,glyphs,clips,overflowWrap:hs.overflowWrap,whiteSpace:hs.whiteSpace,fontSize:parseFloat(hs.fontSize),lineHeight:parseFloat(hs.lineHeight),fontFamily:hs.fontFamily};
 });
}'''

def heading_issues(measured,expected,width,tolerance=1):
 issues=[]
 if not isinstance(measured,list) or len(measured)!=len(expected):return ['Exact copy-section H2 denominator mismatch']
 for i,(row,want) in enumerate(zip(measured,expected)):
  prefix='H2 '+str(i)+': '
  if {k:row.get(k) for k in ('text','sectionId')}!=want:issues.append(prefix+'frozen heading text/section mismatch')
  if row.get('visible') is not True or row.get('overflowWrap')!='anywhere' or row.get('whiteSpace') in ('nowrap','pre'):issues.append(prefix+'heading invisible or narrow wrapping unavailable')
  if not isinstance(row.get('fontSize'),(float,int)) or not math.isfinite(row['fontSize']) or row['fontSize']<18 or not isinstance(row.get('lineHeight'),(float,int)) or not math.isfinite(row['lineHeight']) or row['lineHeight']<row['fontSize']:issues.append(prefix+'unreadable heading size/line-height')
  glyphs=row.get('glyphs',[]);text=''.join(c for c in want['text'] if not c.isspace())
  if ''.join(g.get('char','') for g in glyphs)!=text:issues.append(prefix+'missing or changed per-character Range evidence')
  content=row.get('contentBox',{});left,right=content.get('left'),content.get('right')
  if not all(isinstance(n,(float,int)) and math.isfinite(n) for n in (left,right)) or right<=left:issues.append(prefix+'invalid card content-box');continue
  for glyph in glyphs:
   boxes=glyph.get('rects',[])
   if not boxes:issues.append(prefix+'glyph has no rendered Range');continue
   for r in boxes:
    if any(not isinstance(r.get(k),(float,int)) or not math.isfinite(r[k]) for k in ('left','right','top','bottom','width','height')) or r['width']<=0 or r['height']<=0:issues.append(prefix+'invalid glyph geometry');continue
    if r['left']<left-tolerance or r['right']>right+tolerance:issues.append(prefix+'glyph Range overflows card inner padding')
    if r['left']<-.5 or r['right']>width+.5:issues.append(prefix+'glyph Range overflows viewport')
    for clip in row.get('clips',[]):
     box=clip['rect']
     if clip['overflowX'] in ('hidden','clip') and (r['left']<box['left']-tolerance or r['right']>box['right']+tolerance):issues.append(prefix+'glyph Range horizontally clipped')
     if clip['overflowY'] in ('hidden','clip') and (r['top']<box['top']-tolerance or r['bottom']>box['bottom']+tolerance):issues.append(prefix+'glyph Range vertically clipped')
 return sorted(set(issues))

# Geometry only: records document text-line coordinates plus actual fixed/sticky UI.
READABLE_TARGET_JS=r'''({selector,index,includeAnswer})=>{
 const root=document.querySelectorAll(selector)[index];if(!root)throw Error('supplemental target missing');
 const nodes=[root];if(includeAnswer){const a=root.nextElementSibling;if(!a?.matches('[data-faq-answer]'))throw Error('FAQ answer sibling missing');nodes.push(a);}
 const shown=e=>e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true});
 const blockers=[...document.querySelectorAll('.site-header,.mobile-bar')].filter(shown).map(e=>{const r=e.getBoundingClientRect();return {selector:e.className,position:getComputedStyle(e).position,top:r.top,bottom:r.bottom,left:r.left,right:r.right};});
 let safeTop=16,safeBottom=innerHeight-16;
 for(const b of blockers){if(!['fixed','sticky'].includes(b.position))continue;if(b.top<=1&&b.bottom>0)safeTop=Math.max(safeTop,b.bottom+16);if(b.bottom>=innerHeight-1&&b.top<innerHeight)safeBottom=Math.min(safeBottom,b.top-16);}
 const lines=[];
 for(const element of nodes){const walker=document.createTreeWalker(element,NodeFilter.SHOW_TEXT);let n;while(n=walker.nextNode()){
  if(!n.textContent.trim())continue;const range=document.createRange();range.selectNodeContents(n);
  for(const r of range.getClientRects()){
   if(r.width<=0||r.height<=0)continue;const y=(r.top+r.bottom)/2;
   const inSafe=r.top>=safeTop&&r.bottom<=safeBottom&&r.left>=0&&r.right<=innerWidth;
   const xs=[r.left+Math.min(1,r.width/2),(r.left+r.right)/2,r.right-Math.min(1,r.width/2)];
   const unobscured=inSafe&&xs.every(x=>{const hit=document.elementFromPoint(x,y),owner=n.parentElement;return !!hit&&(owner===hit||owner.contains(hit));});
   lines.push({index:lines.length,top:r.top,bottom:r.bottom,documentTop:r.top+scrollY,documentBottom:r.bottom+scrollY,left:r.left,right:r.right,inSafe,unobscured});
  }
 }}
 return {text:nodes.map(e=>e.textContent.trim()).join('\n'),scrollX,scrollY,viewportWidth:innerWidth,viewportHeight:innerHeight,safeTop,safeBottom,blockers,lines};
}'''

def _artifact(path):return {'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
def _json(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n')

def retain_readable_target(page,out,stem,selector,index,include_answer,record):
 """Natural scroll only; every actual text line must appear clear in at least one viewport."""
 args={'selector':selector,'index':index,'includeAnswer':include_answer};out=Path(out)
 before=hashlib.sha256(page.content().encode()).hexdigest();initial=page.evaluate(READABLE_TARGET_JS,args)
 result={'selector':selector,'index':index,'includeAnswer':include_answer,'text':initial['text'],'method':'natural window scroll, unmodified DOM/CSS, full viewport screenshots','frames':[],'coverageComplete':False,'issues':[]}
 lines=initial['lines'];needed=set(range(len(lines)));covered=set()
 if not lines:raise RuntimeError('supplemental_no_text_ranges')
 for attempt in range(len(lines)+1):
  current=page.evaluate(READABLE_TARGET_JS,args)
  if len(current['lines'])!=len(lines) or current['text']!=initial['text']:raise RuntimeError('supplemental_text_layout_changed')
  missing=sorted(needed-covered)
  if not missing:break
  target=current['lines'][missing[0]]
  if current['safeBottom']<=current['safeTop']:raise RuntimeError('no_readable_viewport_between_fixed_UI')
  page.evaluate('(y)=>window.scrollTo(0,y)',max(0,target['documentTop']-current['safeTop']-2))
  page.wait_for_timeout(60)
  frame=page.evaluate(READABLE_TARGET_JS,args)
  visible={l['index'] for l in frame['lines'] if l['unobscured']}
  file=out/(stem+'-readable-'+str(attempt)+'.png');page.screenshot(path=str(file))
  frame['file']=file.name;frame['coveredLineIndexes']=sorted(visible);result['frames'].append(frame)
  record.setdefault('artifacts',[]).append(_artifact(file))
  if not visible-covered:
   result['issues'].append('Natural scrolling could not expose remaining target lines clear of fixed UI');break
  covered|=visible
 result.update(coveredLineIndexes=sorted(covered),expectedLineCount=len(lines),coverageComplete=covered==needed,domUnmodified=hashlib.sha256(page.content().encode()).hexdigest()==before)
 if not result['coverageComplete']:result['issues'].append('Supplemental text-line coverage incomplete')
 if not result['domUnmodified']:result['issues'].append('DOM changed during supplemental read-only scroll')
 report=out/(stem+'-readable.json');_json(report,result);record.setdefault('artifacts',[]).append(_artifact(report))
 record.setdefault('supplementalReadable',[]).append(result)
 record.setdefault('issues',[]).extend(result['issues'])
 return result

def supplemental_evidence(page,out,stem,expected,record,width):
 """Retain H2 and FAQ content with valid header/sticky CTA still present."""
 for i,_ in enumerate(expected['h2Headings']):retain_readable_target(page,out,stem+'-heading-'+str(i),'.copy-section h2',i,False,record)
 for i,_ in enumerate(expected['faqIds']):retain_readable_target(page,out,stem+'-faq-'+str(i),'[data-faq-question]',i,True,record)
 page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(60)
 if width<860:
  menu=page.locator('.mobile-menu');summary=menu.locator('summary')
  if menu.get_attribute('open') is not None:raise RuntimeError('mobile_menu_must_start_closed')
  summary.click()
  try:
   if menu.get_attribute('open') is None:raise RuntimeError('mobile_menu_did_not_open')
   actual=menu.locator('nav a').evaluate_all('(a)=>a.map(e=>({label:e.textContent.trim(),href:e.getAttribute("href"),visible:e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})}))')
   if [{k:v[k] for k in ('label','href')} for v in actual]!=expected['navigation'] or not all(v['visible'] for v in actual):raise RuntimeError('menu_open_links_mismatch_or_hidden')
   file=Path(out)/(stem+'-menu-open.png');page.screenshot(path=str(file));record.setdefault('artifacts',[]).append(_artifact(file));record['menuOpenEvidence']={'file':file.name,'links':actual,'uiUnmodified':True}
  finally:summary.click()
  if menu.get_attribute('open') is not None:raise RuntimeError('mobile_menu_failed_to_restore_closed')
 else:record['menuOpenEvidence']={'applicable':False,'reason':'Desktop viewport; existing desktop menu flow still checked'}
 page.evaluate('window.scrollTo(0,0)')
