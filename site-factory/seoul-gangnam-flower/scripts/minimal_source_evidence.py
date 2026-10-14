"""Bounded extract-only evidence projection; never validates an absent full PDF.
The historical full-document validator and its seals remain unchanged.
"""
from pathlib import Path
import copy,hashlib,json,re
from source_link_amendment import OLD,NEW,AMENDMENT_SHA256,SELECTION_SHA256
MINIMAL_AMENDMENT_SHA256='035c8a4aef367f85a125869856cc016c7fb342bee46e182e5d41336561bc6dfc'
EXTRACT_SELECTION_SHA256='ca292b815888b3c360183941548806725f7055aba6f78f57931f0b7021d8d09d'
PDF_SHA256='91745c11ecd4ca6e6964cf823be8e7325499ed585ba09017ae3fc222d56f476a'
TEXT_SHA256='befe8c7000e0003599519422d4d347e856b7523ff41e447560d53b801229af11'
EXCLUDED=['raw/setec-current-linked-operations.pdf','text/setec-current-linked-operations.txt']
RANGES={'extracts/cover-page1.txt':(1,[0,100],[1,11]),'extracts/revision-page2.txt':(2,[100,1271],[12,26]),'extracts/article43-page13.txt':(13,[34180,35010],[474,480])}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def pinned(p,h):
 assert p.is_file() and not p.is_symlink() and sha(p)==h,'Minimal evidence pin missing or byte drift: '+p.name
 return read(p)
def load_amendment(root):
 root=Path(root);data=root/'src/data';e=data/'gangnam-current-facts'
 # These historical seals identify the predecessor; their full-document validator is NOT called or bypassed.
 a=pinned(data/'gangnam-source-link-amendment.json',AMENDMENT_SHA256)
 historical=pinned(e/'SELECTION-MANIFEST.json',SELECTION_SHA256)
 m=pinned(data/'gangnam-minimal-evidence-amendment.json',MINIMAL_AMENDMENT_SHA256)
 selection=pinned(e/'EXTRACT-SELECTION-MANIFEST.json',EXTRACT_SELECTION_SHA256)
 assert a['effectiveCopyJsonPointer']=='/articles/2/sourceLinks/3/url' and a['oldUrl']==OLD and a['newUrl']==NEW
 assert a['bodySentencesChanged']==0 and a['dateTextChanged'] is False and a['originalApprovalSealsChanged'] is False and a['originalResearch331Recovered'] is False and a['publicationAuthorized'] is False
 assert [a['publishedCoverDate'],a['publishedRevisionDate']]==['2024.10','2024.10.04']
 assert m['historicalSourceLinkAmendment']=={'path':'src/data/gangnam-source-link-amendment.json','sha256':AMENDMENT_SHA256}
 assert m['historicalEvidenceSelection']=={'path':'src/data/gangnam-current-facts/SELECTION-MANIFEST.json','sha256':SELECTION_SHA256}
 assert m['evidenceSelection']=={'path':'src/data/gangnam-current-facts/EXTRACT-SELECTION-MANIFEST.json','sha256':EXTRACT_SELECTION_SHA256}
 assert m['baselineSourceContentSha256']=='a25def8e1ee19991596762f4299c9dec7c2c695f12c9b861548675a9fbb762aa'
 assert m['baselineCustomerCopySha256']=='b442c6ab713453dc4651ea27f1586f777cd5f9915c5b9dd932d6f09da761990b'
 assert m['customerUrlChangesFromBaseline']==m['bodySentencesChanged']==0
 for obj in [m,selection]:
  assert obj['evidenceMode']=='bounded-extracts-no-full-document'
  assert obj['fullDocumentIncluded'] is False and obj['fullDocumentBytesVerifiedByCandidate'] is False and obj['publicationAuthorized'] is False
 assert m['originalApprovalSealsChanged'] is False and m['originalResearch331Recovered'] is False and m['dateTextChanged'] is False
 assert selection['excludedFiles']==EXCLUDED and selection['selectedPdfPages']==[1,2,13]
 assert selection['originalPdfUrl']==NEW and selection['originalPdfSha256']==PDF_SHA256==a['newPdfSha256']
 assert selection['originalTextSha256']==TEXT_SHA256 and selection['historicalSelectionSha256']==SELECTION_SHA256
 assert selection['historicalSnapshotRecovered'] is False and selection['fileCount']==len(selection['files'])==11
 assert historical['fileCount']==len(historical['files'])==10
 expected={row['path'] for row in selection['files']}|{'SELECTION-MANIFEST.json','EXTRACT-SELECTION-MANIFEST.json'}
 actual={p.relative_to(e).as_posix() for p in e.rglob('*') if p.is_file() or p.is_symlink()}
 assert actual==expected,'Unexpected or missing evidence file, including forbidden full source'
 old={r['path']:r for r in historical['files']}
 for row in selection['files']:
  rel=Path(row['path']);assert not rel.is_absolute() and '..' not in rel.parts
  f=e/rel;assert f.is_file() and not f.is_symlink() and f.stat().st_size==row['bytes'] and sha(f)==row['sha256'],'Selected evidence missing/byte drift: '+row['path']
  if row['path'] in RANGES:
   page,bytes_,lines=RANGES[row['path']];assert [row['sourcePdfPage'],row['sourceTextByteRange'],row['sourceTextNewlineRangeInclusive']]==[page,bytes_,lines]
   assert not re.search(r'01[016789][- ]?\d{3,4}[- ]?\d{4}',f.read_text()),'Mobile pattern in selected text'
  else:assert row==old[row['path']],'Retained historical evidence entry drift'
 assert set(old)-{r['path'] for r in selection['files']}==set(EXCLUDED)
 assert not any((e/p).exists() for p in EXCLUDED),'Full document must not be included'
 fetch=read(e/'current-linked-setec-fetch.json')
 assert fetch['url']==fetch['finalUrl']==NEW and fetch['httpStatus']==200 and fetch['sha256']==PDF_SHA256 and fetch['textSha256']==TEXT_SHA256 and fetch['fetchedAtUTC']==a['sourceAcquiredAtUTC']
 # Acquisition metadata is retained provenance, not a current fetch or full-document check.
 text=lambda name:re.sub(r'\s+','',(e/'extracts'/name).read_text())
 assert '2024.10.' in text('cover-page1.txt') and '2024.10.04.' in text('revision-page2.txt')
 assert '제43조(전시장관리)' in text('article43-page13.txt') and '사용기간이끝난후모든물품을수거' in text('article43-page13.txt')
 assert 'href="/resources/front/files/2025_SETEC.pdf"' in (e/'raw/setec-rental-procedure.html').read_text()
 comparison=read(e/'setec-version-comparison.json')
 assert comparison['currentLinkedURL']==NEW and comparison['newRawSha256']==PDF_SHA256 and comparison['currentLinkedCoverDate']=='2024.10' and comparison['currentLinkedRevisionDate']=='2024.10.04'
 assert comparison['customerProseRevisionRequired'] is False and comparison['article43WhitespaceNormalizedEqual'] is True
 verdict=read(e/'CURRENT-FACTS-VERDICT.json');assert verdict['candidateSourceContentSha256']==a['baselineSourceContentSha256'] and verdict['candidateCopySha256']==a['baselineCopySha256']
 assert verdict['requiredCustomerProseCorrections']==[] and len(verdict['requiredSourceLinkCorrections'])==1 and verdict['historicalSnapshotRecovered'] is False
 v=verdict['requiredSourceLinkCorrections'][0];assert [v['jsonPointer'],v['old'],v['new']]==[a['effectiveCopyJsonPointer'],OLD,NEW]
 return a

def effective_articles(root,original_articles):
 a=load_amendment(root);articles=copy.deepcopy(original_articles)
 assert len(articles)==3 and articles[2]['id']=='event' and articles[2]['url']==a['articleUrl']
 assert articles[2]['sourceLinks'][3]['url']==OLD,'Historical source preimage drift'
 articles[2]['sourceLinks'][3]['url']=NEW
 return articles
