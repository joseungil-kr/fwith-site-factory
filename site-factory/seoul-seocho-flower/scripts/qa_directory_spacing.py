"""Verify regional banner spacing against the existing ordered source cards.

Dedicated to the new directory-spacing amendment. It does not alter shared QA
or treat local global-noindex preview mode as a new page-eligibility policy.
"""
from pathlib import Path
from html.parser import HTMLParser
import json,math,os,subprocess

class Directory(HTMLParser):
 def __init__(self,html):
  super().__init__();self.stack=[];self.groups=[];self.events=[];self.cards=[];self.banners=[];self.inline=[];self.robots='';self.card=None;self.heading=None;self.feed(html)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);group=next((x[2] for x in reversed(self.stack) if x[2] is not None),None)
  if tag=='section' and 'data-region-district' in a:
   group={'id':a.get('id'),'key':a['data-region-district'],'heading':'','cards':[]};self.groups.append(group)
  if tag=='meta' and a.get('name')=='robots':self.robots=a.get('content','')
  if 'data-shared-flower-banner' in a:self.banners.append(a['data-shared-flower-banner']);self.events.append(('banner',a['data-shared-flower-banner']))
  if tag=='a' and 'page-card' in a.get('class','').split() and group is not None:
   assert not any(t=='details' for t,_,_ in self.stack),'Regional card hidden inside details'
   self.card={'href':a.get('href'),'unit':a.get('data-region-unit'),'text':[]};group['cards'].append(self.card);self.cards.append(self.card);self.events.append(('card',self.card))
  if tag=='h2' and group is not None:self.heading=group
  if a.get('data-order-banner')=='inline' and group is not None:self.inline.append({'district':group['key'],'cardsBefore':len(self.cards)})
  if tag not in {'img','meta','link','br','hr','input','source','area','base','embed','param','track','wbr'}:self.stack.append((tag,a,group))
 def handle_endtag(self,tag):
  if tag=='a':self.card=None
  if tag=='h2':self.heading=None
  for i in range(len(self.stack)-1,-1,-1):
   if self.stack[i][0]==tag:self.stack=self.stack[:i];break
 def handle_data(self,text):
  if self.card is not None and text.strip():self.card['text'].append(text.strip())
  if self.heading is not None:self.heading['heading']+=text

def source_contract(root=Path('.')):
 code="""import pages from './src/data/pages.json' with {type:'json'};import {groupsFor} from './src/lib/regional-runtime.mjs';const items=pages.filter(p=>p.category==='regions');const groups=groupsFor(items).map(d=>({id:d.key,key:d.key,heading:d.name,cards:d.items.map(({representative,page})=>({href:page.url,unit:representative.unitKeys.join('|'),text:[page.primaryKeyword,page.cardSummary,'주문 안내 보기 →']}))}));console.log(JSON.stringify({eligible:items.length>=3,groups}));"""
 contract=json.loads(subprocess.check_output(['node','--input-type=module','-e',code],cwd=root,text=True))
 # A separate exact Geumcheon copy binding changes labels, never card count or eligibility.
 copy_path=root/'src/data/geumcheon-copy.json'
 if copy_path.exists():
  copy=json.loads(copy_path.read_text())['common']['directory']
  assert len(contract['groups'])==1 and len(contract['groups'][0]['cards'])==1,'Geumcheon N1 directory drift'
  group=contract['groups'][0];group['heading']=copy['districtHeading']
  group['cards'][0]['text']=[copy['cardTitle'],copy['cardSummary']]
  assert group['cards'][0]['href']==copy['cardHref'],'Approved directory route drift'
 copy_path=root/'src/data/yeongdeungpo-copy.json'
 if copy_path.exists():
  copy=json.loads(copy_path.read_text())['common']['directory'];ui=json.loads((root/'src/data/yeongdeungpo-ui-copy.json').read_text())['directory']
  assert len(contract['groups'])==1 and len(contract['groups'][0]['cards'])==2,'Yeongdeungpo N2 directory drift'
  group=contract['groups'][0];group['heading']=ui['districtHeading']
  for card,approved in zip(group['cards'],copy['cards']):
   assert card['href']==approved['href'],'Approved directory route drift'
   card['text']=[approved['title'],approved['summary'],approved['buttonLabel']]
 return contract

def validate(html,contract,globally_indexable=True):
 doc=Directory(html);expected=contract['groups'];eligible=contract['eligible'];cards=[c for g in expected for c in g['cards']]
 assert doc.groups==expected,'Ordered source cards, district IDs or H2 content changed'
 assert doc.cards==cards,'Actual card order differs from source'
 assert doc.banners==(['message','budget','consultation'] if eligible else []),'Banner set differs from existing page eligibility'
 if globally_indexable:assert ('noindex' in doc.robots)==(not eligible),'Page noindex eligibility drift'
 else:assert 'noindex' in doc.robots,'Local preview unexpectedly indexable'
 expected_inline=[] if not expected else [{'district':expected[(len(expected)-1)//2]['key'],'cardsBefore':sum(len(g['cards']) for g in expected[:(len(expected)-1)//2+1])}]
 assert doc.inline==expected_inline,'Existing InlineOrderBanner moved relative to cards or district'
 spacing=[]
 if eligible:
  assert len(cards)>=2,'Eligible directory cannot disperse banners with fewer than two cards'
  positions={kind:next(i for i,e in enumerate(doc.events) if e==('banner',kind)) for kind in ['message','budget','consultation']}
  spacing=[sum(e[0]=='card' for e in doc.events[positions[a]+1:positions[b]]) for a,b in [('message','budget'),('budget','consultation')]]
  assert all(n>=1 for n in spacing),'Adjacent banners lack a visible actual card'
  assert spacing==[math.ceil(len(cards)/2),len(cards)-math.ceil(len(cards)/2)],'Budget is not at the ordered actual-card midpoint'
 return {'cards':len(cards),'districts':len(expected),'eligible':eligible,'bannerKinds':doc.banners,'visibleCardsBetweenBanners':spacing,'orderedCardsPreserved':True,'inlineCtaPositionPreserved':True}

def inspect(root=Path('.')):
 config_path=root/'src/data/site-config.json'
 if config_path.exists() and json.loads(config_path.read_text()).get('siteKey')=='seoul-seocho-flower-direct':
  from qa_seocho_directory import inspect as inspect_seocho
  return inspect_seocho(root)
 result=validate((root/'dist/regions/index.html').read_text(),source_contract(root),os.environ.get('SITE_INDEXABLE')=='true')
 Path(os.environ.get('DIRECTORY_SPACING_REPORT_PATH',str(root/'directory-spacing-qa.json'))).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('DIRECTORY SPACING QA: '+json.dumps(result,ensure_ascii=False));return result
if __name__=='__main__':inspect()
