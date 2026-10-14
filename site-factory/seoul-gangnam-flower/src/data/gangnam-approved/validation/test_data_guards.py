from pathlib import Path
from copy import deepcopy
import json,hashlib
O=Path(__file__).parents[1]
read=lambda p:json.loads(p.read_text())
base={'runtime':read(O/'handoff/runtime-input.json'),'plan':read(O/'plan/fixed-plan.json'),'catalog':read(O/'plan/catalog-policy-evidence.json'),'directory':read(O/'handoff/directory-input.json')}
def invariant(d):
 r=d['runtime'];p=d['plan'];cat=d['catalog'];dr=d['directory']
 assert r['originalPlanN']==p['originalPlanN']==3
 assert [a['url'] for a in r['articles']]==[a['url'] for a in p['pages']]
 assert len(r['expectedPaths'])==len(set(r['expectedPaths']))==6
 assert len(r['common']['articleCards'])==3 and len({c['href'] for c in r['common']['articleCards']})==3
 assert [c['href'] for c in r['common']['articleCards']]==[a['url'] for a in r['articles']]
 assert [len(dr[k]) for k in ['legalUnits','administrativeUnits','relations']]==[14,22,31]
 assert all(a['administrativeDong'] is None for a in dr['physicalAnchors'])
 assert all(a['legalDong'] is None for a in dr['physicalAnchors'] if a['id'] in ['samsung-seoul-funeral','setec'])
 assert r['publication']['sourceCommit'] is None and r['publication']['canonicalHostname'] is None
 for c,v in zip(r['common']['productCards'],cat['products']):
  assert c['sku']==v['sku'] and c['basicPriceKRW']==v['priceKRW'] and c['cta']['href']==v['source']['url'] and c['imageSha256']==v['photo']['sha256']
 for a in r['articles']:
  assert a['faq'] and all(f['question'] and f['answer'] for f in a['faq'])
  assert [s for sec in a['sections'] for s in sec.get('productCardSkus',[])]==a['productSkus']
  text='\n'.join(z for s in a['sections'] for z in s['paragraphs'])
  assert '하루 이상' in text and '별도로 수거하지 않습니다' in text or (a['id']=='wedding' and '하루 이상' in text and '수거를 별도로 제공하지 않습니다' in text)
 return True
mutations=[
 ('wrongSKUPrice',lambda d:d['runtime']['common']['productCards'][0].update(basicPriceKRW=0)),
 ('productCTAChangedToHome',lambda d:d['runtime']['common']['productCards'][0]['cta'].update(href='https://fwith.co.kr/')),
 ('wrongPhotoSHA',lambda d:d['runtime']['common']['productCards'][0].update(imageSha256='0'*64)),
 ('duplicateArticleURL',lambda d:d['runtime']['articles'][1].update(url=d['runtime']['articles'][0]['url'])),
 ('FAQDropped',lambda d:d['runtime']['articles'][2].update(faq=[])),
 ('fourthProductCardDropped',lambda d:d['runtime']['articles'][0]['sections'][1]['productCardSkus'].pop()),
 ('adminDongGuessed',lambda d:d['directory']['physicalAnchors'][0].update(administrativeDong='일원본동')),
 ('legalDongGuessed',lambda d:d['directory']['physicalAnchors'][0].update(legalDong='일원동')),
 ('routeDenominatorShrunk',lambda d:d['runtime']['expectedPaths'].pop()),
 ('fakeCanonicalHostname',lambda d:d['runtime']['publication'].update(canonicalHostname='unverified.invalid')),
 ('articleCardCountInflated',lambda d:d['runtime']['common']['articleCards'].append(d['runtime']['common']['articleCards'][0])),
 ('membershipRelationRemoved',lambda d:d['directory']['relations'].pop())]
results=[];invariant(base)
for name,mutate in mutations:
 d=deepcopy(base);mutate(d)
 try:invariant(d);rejected=False
 except AssertionError:rejected=True
 results.append({'mutation':name,'rejected':rejected})
assert all(r['rejected'] for r in results)
out={'scope':'In-memory local handoff data invariants only; not production code, rendered HTML, provider, browser or deployment tests. Mutated fixtures are not persisted.','baselinePass':True,'mutations':results,'runtimeInputSha256':hashlib.sha256((O/'handoff/runtime-input.json').read_bytes()).hexdigest()}
(O/'validation/data-guard-selftests.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
