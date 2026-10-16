"""Exact semantic occurrence readback. Metadata additions are tested in offline production output.
This is a static DOM projection, never a computed-CSS/browser claim.
"""
from pathlib import Path
import json,hashlib
from html_surface import BeautifulSoup
C=Path(__file__).resolve().parents[1];I=C.parent/'inputs/reviewed-copy'
DEFERRED={'meta[name="twitter:title"]','meta[name="twitter:description"]','meta[property="og:image:alt"]','meta[name="twitter:image:alt"]'}
def check(root,mode='production-like'):
 assert mode in ['private','production-like']
 m=json.loads((I/'output-context-map.json').read_text());copy=json.loads((I/'customer-copy.json').read_text())
 assert m['authoredLeafCount']==len(m['contexts'])==102
 assert sum(len(r['occurrences']) for r in m['contexts'])==119
 doms={k:BeautifulSoup((Path(root)/n).read_text()) for k,n in [('home','index.html'),('notFound','404.html')]}
 observed=[];deferred=[];unique=set()
 for row in m['contexts']:
  value=copy
  for part in row['pointer'].strip('/').split('/'):value=value[int(part)] if isinstance(value,list) else value[part]
  assert value==row['text'],row['pointer']
  for occurrence in row['occurrences']:
   for page in occurrence['pageIds']:
    ident=(row['pointer'],occurrence['selector'],occurrence['extraction'],page);assert ident not in unique;unique.add(ident)
    nodes=doms[page].select(occurrence['selector'])
    if mode=='private' and occurrence['selector'] in DEFERRED:
     assert not nodes,('private deferred metadata must be absent',ident);deferred.append({'pointer':row['pointer'],'pageId':page,'selector':occurrence['selector'],'reason':'Absolute-image/Twitter production metadata belongs to separate head transform'});continue
    assert len(nodes)==occurrence['expectedDOMMatchesPerPage'],('exact DOM matches',ident,len(nodes))
    for node in nodes:
     assert node.name.upper()==occurrence['requiredTag'],('semantic tag',ident,node.name)
     extraction=occurrence['extraction'];text=node.get_text() if extraction=='textContent' else node.get(extraction.split(':',1)[1])
     assert text==occurrence['expectedExtractedText'],('exact extracted text',ident,text)
    observed.append({'pointer':row['pointer'],'pageId':page,'selector':occurrence['selector'],'tag':occurrence['requiredTag'],'extraction':occurrence['extraction'],'text':text,'exactMatches':len(nodes)})
 for item in m['supplementalTechnicalIdentifiers']:
  for page in item['pageIds']:
   nodes=doms[page].select(item['selector']);assert len(nodes)==1 and nodes[0].name.upper()==item['requiredTag'] and nodes[0].get_text()==item['expectedExtractedText']
 return {'status':'EXACT_SEMANTIC_CONTEXTS_VERIFIED','mode':mode,'authoredLeaves':102,'logicalOccurrences':119,'checkedLogicalOccurrences':119-len(deferred),'pageExpandedOccurrencesChecked':len(observed),'deferredProductionOnlyOccurrences':deferred,'supplementalTechnicalSKUs':4,'copySHA256':hashlib.sha256((I/'customer-copy.json').read_bytes()).hexdigest(),'contextMapSHA256':hashlib.sha256((I/'output-context-map.json').read_bytes()).hexdigest(),'observed':observed,'actualComputedCSSChecked':False}
if __name__=='__main__':
 import sys
 r=check(Path(sys.argv[1]),sys.argv[2] if len(sys.argv)>2 else 'production-like');print(json.dumps(r,ensure_ascii=False,indent=2))
