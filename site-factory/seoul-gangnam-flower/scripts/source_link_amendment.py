"""Exact bounded SETEC source-link amendment; immutable historical seals remain required."""
from pathlib import Path
import copy,hashlib,json,re
AMENDMENT_SHA256='16d302af3ae83e16482b52b338ecc834dbdd755bae673c9d701d940607cc01bb'
SELECTION_SHA256='b189f8127d5424d696814f226b17f4334f66c0e0fda61d0ffa989f3979262284'
OLD='https://setec.or.kr/resources/front/files/01_SETEC.pdf'
NEW='https://www.setec.or.kr/resources/front/files/2025_SETEC.pdf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def load_amendment(root):
 root=Path(root);p=root/'src/data/gangnam-source-link-amendment.json'
 assert p.is_file() and not p.is_symlink() and sha(p)==AMENDMENT_SHA256,'Source-link amendment missing or byte drift'
 a=read(p);assert a['effectiveCopyJsonPointer']=='/articles/2/sourceLinks/3/url' and a['oldUrl']==OLD and a['newUrl']==NEW
 assert a['bodySentencesChanged']==0 and a['dateTextChanged'] is False and a['originalApprovalSealsChanged'] is False and a['originalResearch331Recovered'] is False and a['publicationAuthorized'] is False
 assert [a['publishedCoverDate'],a['publishedRevisionDate']]==['2024.10','2024.10.04']
 e=root/a['evidenceSelection']['path'];assert sha(e)==SELECTION_SHA256==a['evidenceSelection']['sha256'],'Current evidence selection drift'
 selection=read(e);assert selection['fileCount']==len(selection['files'])==10 and selection['historicalSnapshotRecovered'] is False
 for r in selection['files']:
  rel=Path(r['path']);assert not rel.is_absolute() and '..' not in rel.parts
  f=e.parent/rel;assert f.is_file() and not f.is_symlink() and f.stat().st_size==r['bytes'] and sha(f)==r['sha256'],'Current evidence missing/byte drift: '+r['path']
 verdict=read(e.parent/'CURRENT-FACTS-VERDICT.json');assert verdict['candidateSourceContentSha256']==a['baselineSourceContentSha256'] and verdict['candidateCopySha256']==a['baselineCopySha256']
 assert verdict['requiredCustomerProseCorrections']==[] and len(verdict['requiredSourceLinkCorrections'])==1 and verdict['historicalSnapshotRecovered'] is False
 v=verdict['requiredSourceLinkCorrections'][0];assert [v['jsonPointer'],v['old'],v['new']]==[a['effectiveCopyJsonPointer'],OLD,NEW]
 pdf=e.parent/'raw/setec-current-linked-operations.pdf';assert pdf.read_bytes().startswith(b'%PDF-') and sha(pdf)==a['newPdfSha256']
 fetch=read(e.parent/'current-linked-setec-fetch.json');assert fetch['httpStatus']==200 and fetch['url']==fetch['finalUrl']==NEW and fetch['sha256']==a['newPdfSha256'] and fetch['fetchedAtUTC']==a['sourceAcquiredAtUTC']
 html=(e.parent/'raw/setec-rental-procedure.html').read_text();assert '/resources/front/files/2025_SETEC.pdf' in html
 text=re.sub(r'\s+','',(e.parent/'text/setec-current-linked-operations.txt').read_text());assert '2024.10' in text and '2024.10.04' in text and '제43조' in text
 return a

def effective_articles(root,original_articles):
 a=load_amendment(root);articles=copy.deepcopy(original_articles)
 assert len(articles)==3 and articles[2]['id']=='event' and articles[2]['url']==a['articleUrl']
 assert articles[2]['sourceLinks'][3]['url']==OLD,'Historical source preimage drift'
 articles[2]['sourceLinks'][3]['url']=NEW
 return articles
