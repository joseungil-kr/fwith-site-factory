from pathlib import Path
from html.parser import HTMLParser
import json,hashlib,datetime,re
O=Path(__file__).parent;S=Path('/workspace/shared/gangnam-factory/site-factory/seoul-gangnam-flower')
M=json.loads((O/'mapping/keyword-mapping.draft.json').read_text());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Reader(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.active=[];self.nodes=[];self.robots=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='meta' and a.get('name')=='robots':self.robots=a.get('content')
  if tag in ['p','h1','title']:self.active.append({'tag':tag,'attributes':a,'parts':[]})
 def handle_data(self,data):
  for a in self.active:a['parts'].append(data)
 def handle_endtag(self,tag):
  for i in range(len(self.active)-1,-1,-1):
   a=self.active[i]
   if a['tag']==tag:
    self.active.pop(i);a['text']=''.join(a.pop('parts'));self.nodes.append(a);break
 def texts(self,tag):return [n['text'] for n in self.nodes if n['tag']==tag]
records=[]
for x in M['records']:
 rel='index.html' if x['url']=='/' else x['url'].strip('/')+'/index.html';p=S/'dist'/rel
 assert p.exists(),str(p)
 reader=Reader();reader.feed(p.read_text());title=reader.texts('title')[0];h1s=reader.texts('h1');target=x['actualTextEvidence']['firstAnswer']['text'];matches=[n for n in reader.nodes if n['tag']=='p' and n['text']==target]
 rec={'id':x['id'],'route':x['url'],'htmlFile':str(p),'htmlSha256':h(p),'title':title,'h1s':h1s,'firstAnswerMatches':matches,'robots':reader.robots,'titleExact':title==x['actualTextEvidence']['title']['text'],'h1Exact':h1s==[x['actualTextEvidence']['h1']['text']],'firstAnswerExactlyOnce':len(matches)==1,'firstAnswerWithin180':target[:180]}
 assert rec['titleExact'] and rec['h1Exact'] and rec['firstAnswerExactlyOnce'],rec;records.append(rec)
for route,rel in [('/regions/','regions/index.html'),('/404.html','404.html')]:
 p=S/'dist'/rel;reader=Reader();reader.feed(p.read_text());records.append({'id':'directory' if route=='/regions/' else '404','route':route,'htmlFile':str(p),'htmlSha256':h(p),'title':reader.texts('title')[0],'h1s':reader.texts('h1'),'robots':reader.robots,'roleEvidence':'Directory collects actual article and facility links;404 is an error recovery document. Numeric A04 applicability left to frozen independent rubric.'})
(O/'evidence/rendered-text-bindings.json').write_text(json.dumps({'observedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':'직접 확인: local emitted HTML bytes parsed, not browser or public HTTP','records':records,'sourceWritingPerformed':False,'networkCallsPerformed':False,'toolLimitation':'bs4 was unavailable; no install attempted. Retried with Python standard-library HTMLParser and exact source-text comparison.'},ensure_ascii=False,indent=2)+'\n')
print('Actual local emitted HTML bound',len(records),'routes; primary title/H1/opening all exact')
