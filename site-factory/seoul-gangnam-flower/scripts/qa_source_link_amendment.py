"""Source-link-only effective-copy and rendered snapshot assertions, offline."""
from pathlib import Path
import json
from html_surface import Surface
from minimal_source_evidence import load_amendment, effective_articles, AMENDMENT_SHA256, MINIMAL_AMENDMENT_SHA256, EXTRACT_SELECTION_SHA256, NEW, OLD

def read(p):return json.loads(p.read_text())
def diff(left,right,path=''):
 if type(left)!=type(right):return [path]
 if isinstance(left,dict):
  out=[]
  for key in sorted(set(left)|set(right)):
   out.extend([path+'/'+key] if key not in left or key not in right else diff(left[key],right[key],path+'/'+key))
  return out
 if isinstance(left,list):
  if len(left)!=len(right):return [path]
  return [d for i,(a,b) in enumerate(zip(left,right)) for d in diff(a,b,path+'/'+str(i))]
 return [] if left==right else [path]
def inspect(root=Path('.'),write_report=True):
 root=Path(root);a=load_amendment(root);data=root/'src/data';original={'articles':read(data/'gangnam-a04-rev4/revised-input/copy/article-copy.rev4.json')['articles'],'common':read(data/'gangnam-approved/copy/common-visible-copy.final.json')['common']};effective=read(data/'gangnam-copy.json')
 assert diff(original,effective)==['/articles/2/sourceLinks/3/url'],'Customer delta is not exactly one approved source URL'
 assert effective['articles']==effective_articles(root,original['articles'])
 pages=read(data/'pages.json');event=pages[2];assert event['url']==a['articleUrl'] and event['sourceLinks'][3]['url']==event['sources'][3]['url']==NEW
 assert event['currentSourceBinding']['amendmentSha256']==MINIMAL_AMENDMENT_SHA256
 assert event['currentSourceBinding']['evidenceSelectionSha256']==EXTRACT_SELECTION_SHA256
 assert event['currentSourceBinding']['evidenceMode']=='bounded-extracts-no-full-document'
 assert event['currentSourceBinding']['fullDocumentIncluded'] is False and event['currentSourceBinding']['fullDocumentBytesVerifiedByCandidate'] is False
 html=(root/'dist/regions/gangnam-event-wreath/index.html').read_text();d=Surface(html);articles=d.where('article','data-page-key','gangnam-event-wreath');assert len(articles)==1
 assert articles[0]['attrs'].get('data-snapshot-id')==event['snapshotId'],'Rendered event snapshot is stale'
 links=[n for n in d.where('a') if n['attrs'].get('href')==NEW];assert len(links)==1,'Current SETEC source must appear exactly once'
 assert OLD not in html and NEW in html,'Old active source remains in event HTML'
 assert '2024년 10월' in html and '2025년 10월' not in html,'File-name year incorrectly changed customer date'
 for other in root.joinpath('dist').rglob('*.html'):
  if other.name=='index.html' and other.parent.name=='gangnam-event-wreath':continue
  assert OLD not in other.read_text() and NEW not in other.read_text(),'Source-link amendment leaked onto another page'
 result={'status':'PASS_EXACT_ONE_CUSTOMER_SOURCE_URL_LOCAL_ONLY','amendmentSha256':AMENDMENT_SHA256,'customerDiffPointers':diff(original,effective),'bodySentencesChanged':0,'publishedDateTextChanged':False,'eventSnapshotId':event['snapshotId'],'eventSnapshotHash':event['snapshotHash'],'newSourceUrl':NEW,'oldSourceUrlPreservedInHistoricalInputs':True,'selectedEvidenceFiles':11,'minimalEvidenceAmendmentSha256':MINIMAL_AMENDMENT_SHA256,'extractSelectionSha256':EXTRACT_SELECTION_SHA256,'fullDocumentIncluded':False,'fullDocumentBytesVerifiedByCandidate':False,'customerChangesFrom1040':0,'originalResearch331Recovered':False,'browserQa':'UNVERIFIED','publicHttp':'NOT_RUN','publicationAuthorized':False}
 if write_report:(root/'source-link-amendment-qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('SETEC source-link QA: exactly one customer URL, unchanged body/date, current event snapshot, bounded evidence')
 return result
if __name__=='__main__':inspect()
