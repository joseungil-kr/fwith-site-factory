"""Validate the bounded floor-claim correction without altering historical seals.

The permitted runtime bytes are reconstructed from the exact historical inputs,
then changed at two named fields and compared byte-for-byte. This is a local
correction candidate, not an assertion that its independent review has passed.
"""
from pathlib import Path
import copy, hashlib, json, re

AMENDMENT_PATH = 'src/data/seocho-corrections/floor-20261013/amendment.json'
AMENDMENT_SHA256 = '81f8431b81a367b94315473ea44926b70ca2693b0fbdf6c4a7c362e2f0aafa20'

def sha(raw): return hashlib.sha256(raw).hexdigest()
def encoded(value): return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def sealed(root, path, digest):
 p=root/path
 assert p.is_file() and not p.is_symlink(),f'Floor correction input missing/unsafe: {path}'
 raw=p.read_bytes();assert sha(raw)==digest,f'Floor correction input byte drift: {path}'
 return raw

def effective_copy(root=Path('.')):
 root=Path(root)
 a=json.loads(sealed(root,AMENDMENT_PATH,AMENDMENT_SHA256))
 assert a['status']=='LOCAL_MINIMAL_CORRECTION_CANDIDATE_PENDING_INDEPENDENT_REVIEW'
 assert a['historicalApprovalSealsChanged'] is False and a['exactOccurrences']==2
 for e in a['evidence']:
  raw=sealed(root,e['path'],e['sha256']);assert len(raw)==e['bytes'],'Correction evidence size drift'
  if e['path'].endswith('-waf.html'):
   assert len(raw)==175 and 'Web Application Firewall page block' in raw.decode('cp949'),'Blocked maps must remain classified as HTML'
 facility=next(e for e in a['evidence'] if e['path'].endswith('/funeral-facilities.html'))
 html=(root/facility['path']).read_text()
 for floor in (1,2,3):assert re.search(r'>지상'+str(floor)+r'층</a>',html),'Required official floor tab absent'
 articles=json.loads(sealed(root,a['originalArticle']['path'],a['originalArticle']['sha256']))['articles']
 common=json.loads(sealed(root,a['originalCommon']['path'],a['originalCommon']['sha256']))['common']
 original={'articles':articles,'common':common};before=encoded(original)
 assert sha(before)==a['previousRuntimeCopySha256'],'Historical projection no longer reproduces frozen runtime bytes'
 expected=copy.deepcopy(original);matches=[x for x in expected['articles'] if x['id']==a['articleId']];assert len(matches)==1
 article=matches[0];sections=[x for x in article['sections'] if x['id']==a['sectionId']];assert len(sections)==1
 section=sections[0];index=a['paragraphIndex'];old=a['oldSentence'];new=a['newSentence']
 assert before.count(old.encode())==2 and new.encode() not in before,'Unexpected correction occurrences'
 for text in (section['paragraphs'][index],article['contentMarkdown']):assert text.count(old)==1 and new not in text,'Correction target does not match'
 section['paragraphs'][index]=section['paragraphs'][index].replace(old,new)
 article['contentMarkdown']=article['contentMarkdown'].replace(old,new)
 after=encoded(expected)
 assert after==before.replace(old.encode(),new.encode()),'Any other copy byte changed'
 assert sha(after)==a['correctedRuntimeCopySha256'],'Corrected projection digest drift'
 actual=sealed(root,'src/data/seocho-copy.json',a['correctedRuntimeCopySha256'])
 assert actual==after and actual.count(new.encode())==2 and old.encode() not in actual,'Runtime correction is not exact'
 return expected

if __name__=='__main__':
 effective_copy()
 print('LOCAL floor correction: two exact occurrences; all other customer-copy bytes and historical inputs unchanged; independent review pending.')
