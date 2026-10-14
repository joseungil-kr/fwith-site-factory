"""Seocho sealed-input → runtime → static-HTML contract.

This is LOCAL inspection only. It never launches a browser, contacts a site, or
claims screen, accessibility, deployment, ownership, search or fulfilment proof.
Inherited regional gates are intentionally unchanged.
"""
from pathlib import Path
from banner_phone_amendment import load_amendment, effective_assets
from seocho_floor_correction import effective_copy, AMENDMENT_PATH, AMENDMENT_SHA256
from html.parser import HTMLParser
from urllib.parse import urlsplit
from collections import Counter
import hashlib, json, os, re, xml.etree.ElementTree as ET

PINS = {'independent-plan-review/verdict.fixed.json': 'a8120fb0b5628cc09be1b3a1998701d49afb596b83a1528049ebb8ad5fbcecaa', 'independent-plan-review/recomputed-checks.json': '31f3a6c06ada23637847fe62a25fd85e33c208fda7d62d699a743838e410e715', 'independent-plan-review/plan-review-verdict.json': '6fc6c8c19a5093a93497a7b08b22c727a74ccda350bd06c7a6bee0f408fe3df4', 'independent-plan-review/write_verdict.py': 'dcf5fed16667f27caa4f97195f727e99119ce83d7167d048da1755feb403e8c5', 'independent-copy-review/recompute.py': '497df3438c9e9a73c7ed6307144607d1956931c8fba9aacc0da80ab7752ebe34', 'independent-copy-review/finalize_rev3.py': '1ebde6a618ec82bdb92b12aa5103c36c5c57cf85ded152e27fb53235667ebb0d', 'independent-copy-review/handoff-projection-verdict.rev4.json': 'aaaeaf580f4097dd942b6b59db353589dba7f876990472ecd58968f52a1ad696', 'independent-copy-review/exact-delta-checks.rev4.json': 'fc3cde48c90f2127492b1e9aa972b786ef933c8d49a77bb5647ff0589634f6d8', 'independent-copy-review/visual-original-inspection.json': '2fcd9d1cc6bf0920e2ca431979e8bbfa7cccdc8e8c58934da0f2c3778cfdf7d9', 'independent-copy-review/write_review.py': 'e4cb734b076d60395e34a0cf85d41eff7106cdbe631be19542ac2f47555dea9f', 'independent-copy-review/verdict.rev3.json': 'f1cac8693c2b34a7202bbc34efbbd164126c25b0ab711e8b0ba37b4d81e539fb', 'independent-copy-review/recomputed-checks.rev2.json': 'befb3f74426ddcaaded8a3d4cb387547ffa64ca98b2750fa38648c94511aecc5', 'independent-copy-review/finalize_rev4.py': '589ce80c831b4f3a091ce5424223f83e95cac5e55afebee3ccf0621eb9b1ab66', 'independent-copy-review/handoff-projection-verdict.json': 'c94396f057e10af0a12e4e85251d4fb4eb364c5ce5ff1f7c8fd1aa152a88494a', 'independent-copy-review/recomputed-checks.rev4.json': '257e33bdc4ec84e2c695e0c3db88801cb0d153541b80f4cf33888b1524c2bb0f', 'independent-copy-review/verdict.rev4.json': '1c453653be429299e2b7285b4499f6dfa65031f51ce03ddf46d516dc6dacda7d', 'independent-copy-review/verdict.rev2.json': '0ec014fda54138d4184749e3f1db78c03f9eabe2eccba88b18e8c445edbdae34', 'independent-copy-review/README.txt': 'bc14b77867b91f158481b1335ca06b9be556fc2db89dd7b3f5450c5c10c535ee', 'independent-copy-review/review_projection_rev4.py': '1efa56408a27b09a1a3b2e771d4c1ca8bf1c95d62564002f189c06ecba8dcb03', 'independent-copy-review/recomputed-checks.rev3.json': '76196d5935abcc50dda97b67554437ac29d53dc420e0bbd62cd818faa38d4ab7', 'handoff/approved-assets.json': '0437ec40f9f56fe08596c06a4084cbb8b2dcd59b6e3b15372b4c7a427d718e82', 'handoff/final-validation.json': '92a09d61537a50e4b668dac1eedf4cf0095a8cd459cf599d9b4ccf2fad8bf6f7', 'handoff/final-readback.json': 'e60b8312d1dc4cc05021671a95c550dd60722618666b9cb040f2f82102adb4ff', 'handoff/runtime-input.json': '4c745c0e299f22c7f978ff14d364b881fafdb53bdfbb36521f50aaa1fea79383', 'handoff/IMPLEMENTATION-HANDOFF.txt': 'd7e000f434ee8f2adeb157ff3045cff9775d58d84eb8bc40c8b2778215468682', 'handoff/package-verification.json': '0966b78d7f7413551297ed25184e10decced4f1d05fec5d057feeb6979f85d78', 'handoff/input-bindings.json': 'a67cbb85772831d4f141661e1a735db4b9d271f67bc437cd82da27cc3fbe125d', 'handoff/directory-input.json': '6ad12465e97664aa1ddb79a701bfb0344d8fdae3905fb7b2cbc09fe1b0c73904', 'handoff/package-manifest.json': '7ab26d2d4a569435d7849e8088c8c10d4825975fef3e609e95e5a29998dbec77', 'handoff/acceptance.json': '057f521f7ebe601fc30195c407efe8634f40dfa35e793da87cc05e75088e78b7', 'plan/fixed-plan.json': '5675a7cc1cf5b142458133cb2fc55ce7224ca5e819b2e11f6684bc2d59728318', 'plan/candidate-plan.json': '42e80f9b020cdba3eb451d939c30cace578925ff1a402344edbc464b2a4f1559', 'plan/freeze.diff': '40cc6ad44db93e57f7bf5e491ed2632c367ceb40cab4dc32e9e9869829164c66', 'plan/product-contact-sheet.jpg': 'd43df3c927f1406efb66eff0ecc529aeba5d554bccaecf056a1938db95e1777f', 'plan/candidate-inventory.json': 'a74aa6096791b6150552346acc3c635d892c58c52dddf04ad79695f7109df922', 'plan/membership.json': '0eef2c53aa192db28fbc968b2ba4dc4218ea82b28c663c56c826624ac9ce15ac', 'plan/input-bindings.json': '5cc84feb655165f81e1540fe449732a07eec1328474c8ba2d68bdd10f5aa63bf', 'plan/catalog-policy-evidence.json': 'b29c98b57f3850e410cf4e4c10b2ddf88a58932736309d906db61d10c99a800a', 'plan/author-original-inspection.json': '8eb2924cf5679085c5c007292d097d12b5eb2b9a6eaa9a107024652c7cfab048', 'plan/product-card-reuse-validation.json': '9dba05dd8f8390a9ac18f3f55fb14afb7be080194bd5a8c8af90c9e30d9992ba', 'plan/evidence-registry.json': '710a20c75e9f4541e85d64160bc33703f64cdc2fd64d55b0191bc455b0bd7ce2', 'copy/intent-completion-matrix.rev3.json': '9bd9ce2cc28503ab646772cbc2bb70a38d0b086a7e75f97913c7a8f44326f19e', 'copy/reviewer-edit.rev2-to-rev3.diff': 'a5e1ca43cdec2b8f5e45bc4b26b8eb552761da23636f4bc58601c40b6deb8eed', 'copy/copy-validation.rev4.json': 'f43096b443cefa07ba11774c712733ca603995fe96d13edb1d2ae68a866cef44', 'copy/review-input-manifest.rev3.json': '0b422fb6200c81d0923920fe6dba018cb525c78e297cc4c37e7bfe7bf62cc8bb', 'copy/article-copy.rev4.txt': '0cdcb4bc1753d91f55db85ccfa906d55f285d8a968300b6ea1392242e9b87cfe', 'copy/article-copy.self-edit.diff': '2f0dbef5709672a488bad919e85583d093fedb0a007062a5be0fe96a65568ca4', 'copy/article-copy.rev4.json': '78bc5af47bf4d1b8bd4c17e4cedd34ecd857c763e79c90df53607d1849c1623f', 'copy/article-copy.rev1.txt': '8f3360937439e2757f85001e8b73d7fc421432a708d7678d0777626e2a6f2be0', 'copy/counts.rev4.json': '06403aaba8fcf9874fe128edab4ef30325bac0a2b3f7973d66a0ee121b534ab3', 'copy/article-copy.rev2.json': '3c458a536749f6ff37c54cd7f7b78ed20ecd238c65e9ba80471da1a15637aaa6', 'copy/counts.rev3.json': '69d805319904bfb972a6eeed3b383ed3282d93fcaffcb9d97673669bafa62736', 'copy/root-tone-edit.rev4.json': '11024f7770266db5100c76d8e7218f92625488c13b0c8d9250f73125c62053ce', 'copy/cross-region-copy-comparison.rev4.json': '5420c22480613537a65842fa0f9c721fb364dccdb1e9322f549e7534a7341ce2', 'copy/article-copy.rev3.json': 'cd0d68f391c97d8eceb407390aebb90f6f84aeeab99fec47971c478512af28b0', 'copy/rev4-lineage-validation.json': 'e56e0c181674d566048938973eff9d3e3d6f78eaed196c9860610a07dda30295', 'copy/cross-region-copy-comparison.rev3.json': '8cb3d7fc0eeeb12db8c82d5b003d3f74358b48deb644a36aabc8a5c36f51c74a', 'copy/review-input-manifest.rev2.json': '868192f7d1b3314047de7aeeeadb2c7802e67b84602f5ed9248da54e918f8fe7', 'copy/cross-region-copy-comparison.rev2.json': '8cb3d7fc0eeeb12db8c82d5b003d3f74358b48deb644a36aabc8a5c36f51c74a', 'copy/root-tone-edit.rev3-to-rev4.diff': '5c073ecdd9d580245da03db18891766806b1fc6580acac9afd63fc42dd9f3fb5', 'copy/claim-evidence-map.rev4.json': '0db2f776b02fd9c078188808f67e20be428b81ecfb2e9acd8765eed83aefd6b0', 'copy/copy-validation.rev2.json': 'd3ac6a863bd6f34cb2da1f3321cce14d9a14de161ff5ed2dc895ae48ba724bdf', 'copy/counts.rev2.json': '3bf25e9a1482a92fc9eb6f45b236f5b9a17ae186c9602a80bdad11e445788e3b', 'copy/article-copy.rev3.txt': '0ba3bdb6be0c778fae130d010177ea510f408ac9f35506168c622a18cf976427', 'copy/article-copy.rev2.txt': 'fe602163cd34c44b8ea7b56e6c9cd95c146645c93f38f419b062fdbca49c2aa4', 'copy/intent-completion-matrix.rev4.json': '21e9c5e867cd707e82cef5d37a9a76f5fe872e3d06e2a65c04b7e47e27a5fe86', 'copy/article-copy.rev1.json': '4aedcad9a06ead16453b2cba6906f81b1ba92c116e6698f0aa8ab81b00531141', 'copy/common-visible-copy.self-edit.diff': 'f22c8351b4b778efb8c59bc4e1c59b15f867c00e5060d35c621ffee9f4fb4e3d', 'copy/copy-validation.rev3.json': '04a920c39166b7dcc155cf01b4d91db77458990d46f8c572d85f8e54fd6dd57e', 'copy/claim-evidence-map.rev3.json': '0db2f776b02fd9c078188808f67e20be428b81ecfb2e9acd8765eed83aefd6b0', 'copy/common-visible-copy.rev1.json': '7ad82849e24c655d5d1ec11fb19467298aec8190cac543ee1a2489c34caba10e', 'copy/intent-completion-matrix.rev2.json': '7c0b617916d1f40cfb1a6fd3ad0676f9406df460590c6c1f8cbebcb72404b42c', 'copy/counts.rev1.json': 'f18d0030628584ae169ce0b63a8fa352f3735a832a24357fb2ff6693e5f6adea', 'copy/common-visible-copy.rev2.json': '22b4b6d12142767cee9dbba40c31db290675f942000a6b86338fbf29b4a3b4cb', 'copy/claim-evidence-map.rev2.json': '5e3f34195a68cef57cb547af53ac8ac64a2b8cc2ef7544878ac0b111a215281f', 'copy/review-input-manifest.rev4.json': '165ca677fe88d0acbcdca672152dd97b946f29fac54aad4445f0f25429318c9d', 'handoff/history-rev3/final-validation.json': '8ecd4d878233e98f3272eafd33dceadc7193768390d6131582662ec9c42d847f', 'handoff/history-rev3/final-readback.json': 'ec2b4ae7f224fa6cdc74bb6dd805ef3305119131e5d83f0488c1bc19baf82b97', 'handoff/history-rev3/runtime-input.json': '4b19af806098c2cd89ce661a975693adbe5d05a6ed99ea1faacddd77608c32db', 'handoff/history-rev3/IMPLEMENTATION-HANDOFF.txt': '46b7ce7af515cf78c7673536cf431af5804763677e7039e81b11f441c6948d2e', 'handoff/history-rev3/package-verification.json': '7070c5cdfc37252e04c8468e47a9db613fbde9a270aa1748f1c15facd1035fff', 'handoff/history-rev3/input-bindings.json': 'eee9f5c04630e9b62e5bf5fcfa47659e101dd35cc61fa1842ac15ac21868cca1', 'handoff/history-rev3/seocho-local-plan-copy-handoff-20261013.zip': '1577f3158fbc46d1fffb1b2daeb1229a4dd6a71b038421822329e2cf37464d08', 'handoff/history-rev3/package-manifest.json': 'c2c25311c8fd43712866ed51d1a080ec4eea6f3160c2375025eeacb3a30b4ffc', 'handoff/history-rev3/README.txt': '006f4ab2c92f4f0137e79a6a017c0e385839ea8825fea5d1a55319ecb0c857be', 'handoff/history-rev3/acceptance.json': '28ec50c993c7acdd18409fc5e4564b452585253755faeebe5e5f8d4029184e80', 'handoff/history-rev3/file-manifest.json': 'b96f62ed65a83c178c0fff931858b977258717a9537b16d066cbe091a647eb18', 'handoff/assets/products/C200.jpg': '0e5c0e37f5a02b0448a0dd9b3aa48c4bd1ebe38862a9dde662ef2e1c14eee905', 'handoff/assets/products/C205.jpg': 'b0fa2c913adf258617e34ce0175cbdc282b83e6b47db556234380353c047d5e9', 'handoff/assets/products/B205.jpg': '1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e', 'handoff/assets/products/B201.jpg': '7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3', 'handoff/assets/products/B060.jpg': 'a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3', 'handoff/assets/products/C203.jpg': 'd3bd30015f4465f6db3d43c37a3088d383173e1bc0b46ff429ed24b9c251625a', 'handoff/assets/products/C204.jpg': '05a71d0a3a624c7e27e0575baab02c21f87cc409a1de5389bd4c42b2789dc16d', 'handoff/assets/products/B203.jpg': '0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114', 'handoff/assets/banners/flower-message.webp': 'b8d973861fe81839ec7765d9dd506deb9d1055614c200479aa72a632cf0c5253', 'handoff/assets/banners/flower-consultation.webp': '4cae6c69e4c6549ed277fd3b2acc32c9a797a570de194bc48a6045b50f28283b', 'handoff/assets/banners/flower-budget.webp': 'bc782e91dadd7d07840ea9cbe6154fb21941dd7f9bf32c53bb2991bc301439df'}
HTTP_SOURCES={'http://kfh.catholicfuneral.co.kr/phgrp/cnts/CntsFrntView.do?cntsId=CFV_1040000&menuNo=1040000','http://kfh.catholicfuneral.co.kr/phgrp/cnts/CntsFrntView.do?cntsId=CFV_2030000&menuNo=2030000'}
SITE='seoul-seocho-flower-direct'
SCOPE='seoul-seocho-direct-local-preparation-20261013'
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

def norm(value): return ' '.join(value.split())
def sha(value): return hashlib.sha256(value).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def descendants(node):
 for child in node['children']:
  yield child
  yield from descendants(child)
def strings(value):
 if isinstance(value,str): yield value
 elif isinstance(value,list):
  for child in value: yield from strings(child)
 elif isinstance(value,dict):
  for child in value.values(): yield from strings(child)

def matches(node,tag=None,key=None,value=None):
 return (tag is None or node['tag']==tag) and (key is None or key in node['attrs'] and (value is None or node['attrs'][key]==value))

def within(node,tag=None,key=None,value=None): return [n for n in descendants(node) if matches(n,tag,key,value)]
def hidden(node):
 while node:
  a=node['attrs'];classes=a.get('class','').split()
  if node['tag'] in ('details','template','script','style') or 'hidden' in a or 'inert' in a or a.get('aria-hidden')=='true' or any(c in classes for c in ('hidden','sr-only','visually-hidden')) or re.search(r'(display\s*:\s*none|visibility\s*:\s*hidden|content-visibility\s*:\s*hidden)',a.get('style','')): return True
  node=node['parent']
 return False

class Surface(HTMLParser):
 def __init__(self,html):
  super().__init__(convert_charrefs=True);self.nodes=[];self.stack=[];self.text_events=[];self.feed(html)
 def handle_starttag(self,tag,attrs):
  assert len(attrs)==len(dict(attrs)),f'Duplicate HTML attribute: {tag}'
  node={'tag':tag,'attrs':dict(attrs),'text':'','children':[],'parent':self.stack[-1] if self.stack else None,'i':len(self.nodes)};self.nodes.append(node)
  if self.stack:self.stack[-1]['children'].append(node)
  if tag not in VOID:self.stack.append(node)
 def handle_startendtag(self,tag,attrs): self.handle_starttag(tag,attrs);self.handle_endtag(tag)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,-1,-1):
   if self.stack[i]['tag']==tag:del self.stack[i:];break
 def handle_data(self,text):
  for node in self.stack: node['text']+=text
  if self.stack and norm(text):self.text_events.append((self.stack[-1],norm(text)))
 def where(self,tag=None,key=None,value=None):return [n for n in self.nodes if matches(n,tag,key,value)]
 def cls(self,cls):return [n for n in self.nodes if cls in n['attrs'].get('class','').split()]
 def text(self,tag):return [norm(n['text']) for n in self.where(tag)]

def exactly(doc,tag,text,count=1):
 nodes=[n for n in doc.where(tag) if norm(n['text'])==norm(text)]
 assert len(nodes)==count,f'Exact {tag} missing/duplicated: {text[:90]}'
 assert not any(hidden(n) for n in nodes),f'Approved {tag} is hidden: {text[:90]}'
 return nodes

def link_exact(doc,label,href,count=None,scope=None):
 nodes=within(scope,'a') if scope else doc.where('a')
 found=[n for n in nodes if norm(n['text'])==norm(label) and n['attrs'].get('href')==href]
 assert len(found)==count if count is not None else bool(found),f'Approved CTA/source missing/duplicated: {label} -> {href}'
 assert not any(hidden(n) for n in found),f'Approved link hidden: {label}'
 return found

def check_metadata(doc,title,h1,description,route,base):
 assert doc.text('title')==[title],f'SEO title drift: {route}'
 assert doc.text('h1')==[h1],f'H1 drift: {route}'
 meta={n['attrs'].get('name',n['attrs'].get('property')):n['attrs'].get('content') for n in doc.where('meta')}
 assert meta.get('description')==description,f'Meta description drift: {route}'
 assert meta.get('robots')=='noindex,nofollow,noarchive',f'Preview robots drift: {route}'
 canon=doc.where('link','rel','canonical')
 if route=='/404.html':
  assert not canon,'404 canonical forbidden'
  assert not any(k and k.startswith(('og:','twitter:')) for k in meta),'404 social tags forbidden'
  assert not doc.where('script','type','application/ld+json'),'404 schema forbidden'
 else:
  assert [n['attrs'].get('href') for n in canon]==[base+route],f'Canonical drift: {route}'
  for key,value in [('og:title',title),('og:description',description),('og:url',base+route),('twitter:title',title),('twitter:description',description)]:
   assert meta.get(key)==value,f'Social metadata drift: {route} {key}'
 return meta

def inspect(root=Path('.'),write=True,quiet=False):
 root=Path(root);data=root/'src/data';dist=root/'dist';sealed=data/'seocho-approved'
 for path,digest in PINS.items():
  f=sealed/path;assert f.is_file(),f'Sealed approval missing: {path}'
  assert sha(f.read_bytes())==digest,f'Sealed approval byte drift: {path}'
 acceptance=read(sealed/'handoff/acceptance.json')
 assert acceptance['status']=='LOCAL_PLAN_AND_CUSTOMER_COPY_ACCEPTED','Copy not accepted'
 original=read(sealed/acceptance['currentArticles']['file'])['articles'];common=read(sealed/acceptance['currentCommon']['file'])['common'];assets=read(sealed/'handoff/approved-assets.json')['assets']
 # Keep every historical PINS check; only the explicitly sealed two-field correction is applied.
 original=effective_copy(root)['articles']
 plan=read(sealed/'plan/fixed-plan.json');candidate=read(sealed/'plan/candidate-inventory.json');geography=read(sealed/'plan/membership.json');directory_input=read(sealed/'handoff/directory-input.json')
 assert plan['originalPlanN']==2 and plan['frozen'] is True and len(plan['pages'])==2,'Plan N changed'
 assert len(plan['candidateLedger'])==8 and plan['candidateLedger']==candidate['candidateLedger'],'Eight candidate groups must be retained'
 assert len(plan['heldPageDecisions'])==7 and plan['heldPageDecisions']==candidate['heldPageDecisions'],'Seven separate-URL holds must be retained'
 copy=read(data/'seocho-copy.json');pages=read(data/'pages.json');products=read(data/'products.json');coverage=read(data/'region-coverage.json');config=read(data/'site-config.json');architecture=read(data/'architecture.json');frozen=read(data/'seocho-plan-binding.json')
 assert copy=={'articles':original,'common':common},'Runtime exact approved copy drift'
 correction=read(root/AMENDMENT_PATH);release=read(data/'publish-manifest.json')['directRelease']
 assert release['reviewStatus']=='COPY_CORRECTION_PENDING_INDEPENDENT_REVIEW','Correction review status falsely promoted'
 assert release['copyCorrection']=={'id':correction['id'],'amendmentSha256':AMENDMENT_SHA256,'runtimeCopySha256':correction['correctedRuntimeCopySha256'],'status':correction['status']},'Runtime correction binding drift'
 assert frozen['candidateLedger']==candidate['candidateLedger'] and frozen['heldPageDecisions']==candidate['heldPageDecisions'],'Runtime held inventory drift'
 assert len(pages)==2 and [p['url'] for p in pages]==[x['url'] for x in original],'Runtime N2 route/card denominator drift'
 assert config['siteKey']==SITE and architecture['siteKey']==SITE and coverage['siteKey']==SITE,'Runtime siteKey drift'
 assert coverage['scopeKey']==SCOPE,'Runtime scope drift'
 for name in ['region-policy','publish-manifest','page-map','direct-checkpoint']:
  obj=read(data/(name+'.json'));assert obj['siteKey']==SITE,f'Active technical siteKey drift: {name}'
  if 'scopeKey' in obj:assert obj['scopeKey']==SCOPE,f'Active technical scope drift: {name}'
 assert config['productionApproved'] is False and config['hostnameOwnershipVerified'] is False,'Unapproved publication/hostname state'
 assert config['previewUrl']=='https://seoul-seocho.local.invalid','Unverified host must remain reserved preview'
 hub=next(h for h in architecture['hubs'] if h['category']=='regions')
 assert hub['children']==2 and hub['indexable'] is False and hub['menuVisible'] is False,'Thin directory N/eligibility drift'
 assert [p['officialSku'] for p in products]==[p['sku'] for p in common['productCards']],'Catalog SKU/order drift'
 bysku={p['officialSku']:p for p in products};bykey={p['key']:p for p in products};approvedsku={p['sku']:p for p in common['productCards']};assert len(bykey)==8,'Duplicate product key'
 for sku,approved in approvedsku.items():
  p=bysku[sku]
  for key,expected in [('name',approved['name']),('price',approved['basicPriceKRW']),('priceLabel',approved['priceLabel']),('desc',approved['description']),('imageAlt',approved['imageAlt']),('imageSha256',approved['imageSha256']),('photoCaption',approved['photoCaption']),('ctaLabel',approved['cta']['label']),('orderUrl',approved['cta']['href']),('sourceUrl',approved['cta']['href'])]:assert p.get(key)==expected,f'Runtime SKU {sku} {key} drift'
 facilities=[]
 for expected in directory_input['physicalAnchors']:
  approved=next(a for a in original if a['id']==expected['article']);section=next(s for s in approved['sections'] if s['id']==expected['id'])
  facilities.append({**expected,'candidateId':expected['id'],'anchor':expected['id'],'heading':section['heading'],'articleId':approved['id']})
 binding={'articles':[{**a,'productHeroSku':a['productSkus'][0]} for a in original],'facilityDestinations':facilities}
 for approved,page in zip(original,pages):
  planned=next(p for p in plan['pages'] if p['id']==approved['id'])
  assert page['scopeKey']==SCOPE,'Page scope drift'
  for key in ['title','h1','firstAnswer','cardSummary','faq','sourceNote','sections','sourceLinks','primaryCta','relatedLink','contentMarkdown']:assert page.get(key)==approved[key],f'Runtime article {key} drift'
  assert page['description']==approved['metaDescription'],'Runtime description drift'
  assert page['candidateIds']==planned['candidateIds'],'Runtime candidate assignment drift'
  assert [bykey[k]['officialSku'] for k in page['productCardKeys']]==approved['productSkus'],'Runtime article SKU binding drift'
  assert page['intentKey']==approved['intentKey'],'Runtime article intent drift'
  expected=[f for f in facilities if f['articleId']==approved['id']]
  assert [a['candidateId'] for a in page['facilityAnchors']]==[a['candidateId'] for a in expected],'Runtime facility classification drift'
  for actual,want in zip(page['facilityAnchors'],expected):
   assert actual['unitKey']=='서초구/법정동/'+want['legalDong'],'Facility unit drift'
   for key in ['anchor','heading','href']:assert actual[key]==want[key],f'Facility {key} drift'
 units=coverage['units'];admins=coverage['administrativeCrosswalk']
 assert [(u['legalCode'],u['name']) for u in units]==[(u['code'],u['name']) for u in geography['legalUnits']],'Legal geography drift'
 assert [(a['administrativeCode'],a['name']) for a in admins]==[(a['code'],a['name']) for a in geography['administrativeUnits']],'Administrative geography drift'
 assert [(a['administrativeCode'],r['unitKey']) for a in admins for r in a['relations']]==[(r['administrativeCode'],'서초구/법정동/'+r['legalName']) for r in geography['relations']],'Official relationship drift'
 assert len(units)==10 and len(admins)==18 and sum(len(a['relations']) for a in admins)==23,'Geography count drift'
 assert len(coverage['facilities'])==3 and len(coverage['buyerOccasions'])==1,'Physical/occasion count drift'
 expected_addresses={'seoul-st-mary-funeral':'서울특별시 서초구 반포대로 222 (반포동 505)','eltower':'서울특별시 서초구 강남대로 213 (양재동 24)','at-center-exhibition':'서울특별시 서초구 강남대로 27 (양재동 232)'}
 for f,expected in zip(coverage['facilities'],facilities):
  assert f['facilityKey']==expected['candidateId'] and f['address']==expected_addresses[f['facilityKey']],'Facility candidate/address drift'
  assert f['unitKey']=='서초구/법정동/'+expected['legalDong'],'Facility legal unit drift'
  assert f.get('administrativeCode') is None and f.get('administrativeDong') is None,'Administrative facility inference forbidden'
 occasion=coverage['buyerOccasions'][0]
 assert occasion['contextKey']=='opening-relocation-occasion' and occasion['contextType']=='buyer-occasion','Buyer occasion misclassified'
 assert all(occasion.get(k) is None for k in ['unitKey','legalCode','administrativeCode','physicalAddress']),'Buyer occasion fabricated geography'
 assert coverage['administrativeFacilityAssignments']==[],'Administrative assignments forbidden'
 surface={'articles':original,'common':common}
 assets=[{**a,'alt':a['copy']['imageAlt'] if 'copy' in a else common['banners'][a['variant']]['alt'],'snapshot':{'sha256':a['sha256'],'bytes':a['bytes']}} for a in assets]
 amendment=load_amendment(root);assets=effective_assets(root,assets)
 expected={'index.html','regions/index.html','404.html'}|{p['url'].strip('/')+'/index.html' for p in original}
 actual={p.relative_to(dist).as_posix() for p in dist.rglob('*.html')}
 assert actual==expected,'Unexpected standalone or missing HTML route'
 docs={rel:Surface((dist/rel).read_text()) for rel in sorted(expected)};base=(os.environ.get('SITE_URL') or config['previewUrl']).rstrip('/')
 asset_map={a['proposedRuntimePath'].removeprefix('public'):a for a in assets}
 for a in assets:
  path=a['proposedRuntimePath'].removeprefix('public/')
  for basepath in [root/'public',dist]:
   f=basepath/path;assert f.is_file(),f'Missing approved asset: {f}'
   assert sha(f.read_bytes())==a['snapshot']['sha256'] and f.stat().st_size==a['snapshot']['bytes'],f'Actual approved image byte/hash drift: {f}'
 allowed_strings=list(strings(surface['common']))+list(strings(surface['articles']))+[r['name'] for r in geography['legalUnits']+geography['administrativeUnits']]+['서초구']
 allowed_strings=[norm(s) for s in allowed_strings]
 ids={};reports=[]
 for rel,doc in docs.items():
  assert len(doc.where('body'))==1,'Exactly one document body required'
  for node in doc.nodes:
   assert not any(k.lower().startswith('on') for k in node['attrs']),'Inline event handler forbidden'
   assert node['tag'] not in ['iframe','object','embed','frame','frameset','form','base'],'Unapproved executable/embedded element'
   if node['tag']=='script':assert node['attrs']=={'type':'application/ld+json'},'Executable script forbidden'
   for key in ['href','src','action','formaction','poster','xlink:href']:
    if key in node['attrs']:
     value=node['attrs'][key] or '';assert not re.search(r'[\x00-\x20]',value),'Control/whitespace in URL forbidden'
     parsed=urlsplit(value);assert (parsed.scheme in ('','https','tel') or value in HTTP_SOURCES) and not value.startswith('//'),'Unsafe URL protocol forbidden'
  visible_body=norm(doc.where('body')[0]['text'])
  assert norm(amendment['removedVisibleCaption']) not in visible_body,'Removed common-banner caption reintroduced'
  ids[rel]=[n['attrs']['id'] for n in doc.where(key='id')]
  assert len(ids[rel])==len(set(ids[rel])),f'Duplicate HTML id: {rel}'
  for node,text in doc.text_events:
   if node['tag'] in ['script','style','title'] or any(n['tag']=='head' for n in ancestor_nodes(node)):continue
   if not re.search(r'[\w가-힣]',text):continue
   assert any(text in allowed for allowed in allowed_strings),f'Unapproved visible text: {rel}: {text[:120]}'
   assert not re.search(r'관악구|영등포|동작구|금천구|구로구|gwanak|yeongdeungpo|dongjak|geumcheon|guro',text,re.I),f'Old region visible text: {rel}'
  for img in doc.where('img'):
   a=img['attrs'];assert not hidden(img),f'Rendered approved image hidden: {rel}'
   assert a.get('src') in asset_map,f'Unapproved image source: {rel}: {a.get("src")}'
   approved=asset_map[a['src']]
   assert a.get('alt')==approved['alt'],f'Image alt drift: {rel}: {a["src"]}'
   assert (a.get('width'),a.get('height'))==tuple(map(str,approved['dimensions'])),f'Image dimensions drift: {rel}'
  for link in doc.where('a'):
   href=link['attrs'].get('href','');assert href,'Empty href'
   u=urlsplit(href)
   assert u.scheme in ('','https','tel') or href in HTTP_SOURCES,'Unexpected unsafe/unsupported link scheme'
  accessibility=common['accessibility']
  link_exact(doc,accessibility['skip'],'#main-content',1)
  headers=doc.where('header');assert len(headers)==1,'Single header required'
  nav=within(headers[0],'nav');assert len(nav)==1 and nav[0]['attrs'].get('aria-label')==accessibility['navigation'],'Approved navigation aria label drift'
  for key,href in [('home','/'),('funeral',original[0]['url']),('celebration',original[1]['url']),('regions','/regions/')]:link_exact(doc,common['navigation'][key],href,1,nav[0])
  link_exact(doc,common['navigation']['phone'],common['footer']['phoneHref'],1,headers[0])
  footers=doc.where('footer');assert len(footers)==1,'Single footer required'
  footer=footers[0];f=common['footer']
  assert norm(f['brandLine']) in norm(footer['text']),'Footer brand line drift'
  for label,href in [(f['phoneLabel'],f['phoneHref']),(f['shopLabel'],f['shopHref']),(f['homeLinkLabel'],'/')]:link_exact(doc,label,href,1,footer)
  banners=doc.where(key='data-shared-flower-banner');variants=[n['attrs']['data-shared-flower-banner'] for n in banners]
  expected_banners=[] if rel in ('404.html','regions/index.html') else ['message','budget','consultation']
  assert variants==expected_banners,f'Banner sequence/count drift: {rel}'
  for banner in banners:
   imgs=within(banner,'img');variant=banner['attrs']['data-shared-flower-banner']
   assert len(imgs)==1 and imgs[0]['attrs']['src']=='/images/shared-banners/flower-'+variant+'.webp','Banner exact variant image drift'
   assert imgs[0]['attrs'].get('loading')=='lazy' and imgs[0]['attrs'].get('decoding')=='async','Banner lazy/async drift'
   assert not within(banner,'figcaption'),'Common banner caption must be absent under explicit amendment'
  assert sum('/images/shared-banners/' in n['attrs'].get('src','') for n in doc.where('img'))==len(banners),'Extra banner image outside figure'
  for left,right in zip(banners,banners[1:]):
   between=[n for n in doc.nodes if left['i']<n['i']<right['i'] and (n['tag']=='p' or 'page-card' in n['attrs'].get('class','').split()) and len(norm(n['text']))>=30 and not any('data-shared-flower-banner' in a['attrs'] for a in ancestor_nodes(n))]
   assert between,f'Adjacent banners lack substantive content: {rel}'
  cards=doc.cls('product-card');want=8 if rel=='index.html' else 0 if rel in ('404.html','regions/index.html') else 4
  assert len(cards)==want,f'Actual product card count drift: {rel}'
  expected_skus=list(approvedsku) if rel=='index.html' else next((b['productSkus'] for b in binding['articles'] if rel==b['url'].strip('/')+'/index.html'),[])
  assert [bykey.get(n['attrs'].get('data-product-key'),{}).get('officialSku') for n in cards]==expected_skus,f'Rendered product SKU/order drift: {rel}'
  for card in cards:
   assert not hidden(card),'Product card hidden'
   p=bykey[card['attrs']['data-product-key']];approved=approvedsku[p['officialSku']]
   assert [norm(n['text']) for n in within(card,'h3')]==[approved['name']],'Product name drift'
   assert [norm(n['text']) for n in within(card,'strong')]==[approved['priceLabel']],'Product per-SKU price drift'
   ptexts=[norm(n['text']) for n in within(card,'p')]
   assert ptexts.count(approved['description'])==1 and norm(card['text']).count(approved['photoCaption'])==1,'Product description/photoCaption missing or duplicated'
   assert len(within(card,'img'))==1 and within(card,'img')[0]['attrs']['src']==p['img'],'Product card image missing/duplicated/wrong SKU'
   link_exact(doc,approved['cta']['label'],approved['cta']['href'],1,card)
  heroes=doc.cls('hero-product')+doc.cls('detail-product')
  want_heroes=['B201','C200'] if rel=='index.html' else [] if rel in ('404.html','regions/index.html') else [next(b['productHeroSku'] for b in binding['articles'] if rel==b['url'].strip('/')+'/index.html')]
  assert [bykey.get(n['attrs'].get('data-product-key'),{}).get('officialSku') for n in heroes]==want_heroes,f'Hero/card separation or SKU drift: {rel}'
  actual_product_images=Counter(n['attrs']['src'] for n in doc.where('img') if n['attrs']['src'].startswith('/images/products/'))
  assert actual_product_images==Counter(bysku[sku]['img'] for sku in expected_skus+want_heroes),'Product image outside approved cards/heroes or image count drift'
  assert visible_body.count(common['productCards'][0]['photoCaption'])==want,'Photo caption outside approved product cards or count drift'
  for sku in expected_skus:assert visible_body.count(approvedsku[sku]['description'])==1,'Duplicate/missing product description anywhere in body'
  for hero in heroes:
   p=bykey[hero['attrs']['data-product-key']];assert len(within(hero,'img'))==1 and within(hero,'img')[0]['attrs']['src']==p['img'],'Hero product image drift'
   assert p['priceLabel'] in norm(hero['text']),'Hero price drift'
  if rel!='404.html':
   social_sku=want_heroes[0] if want_heroes else 'B201';social=bysku[social_sku]
   social_meta={n['attrs'].get('name',n['attrs'].get('property')):n['attrs'].get('content') for n in doc.where('meta')}
   for key in ['og:image:alt','twitter:image:alt']:assert social_meta.get(key)==social['imageAlt'],f'Reviewed social image alt drift: {key}'
   for key in ['og:image','og:image:secure_url','twitter:image']:assert social_meta.get(key)==base+social['img'],f'Social image exact URL drift: {key}'
  reports.append({'file':rel,'sha256':sha((dist/rel).read_bytes()),'productCards':len(cards),'heroProducts':len(heroes),'sharedBanners':variants})
  levels=[int(n['tag'][1]) for n in doc.nodes if n['tag'] in ('h1','h2','h3')]
  assert levels and levels[0]==1 and all(b<=a+1 for a,b in zip(levels,levels[1:])),'Heading hierarchy skips a level'
  mains=doc.where('main','id','main-content');assert len(mains)==1 and mains[0]['attrs'].get('tabindex')=='-1','Skip target must be focusable'
  if banners:
   positions={n['attrs']['data-shared-flower-banner']:n['i'] for n in banners}
   if rel=='index.html':
    assert max(n['i'] for n in doc.cls('page-card'))<positions['message']<min(n['i'] for n in cards)<max(n['i'] for n in cards)<positions['budget']<doc.where(key='data-home-place')[0]['i']<positions['consultation'],'Home approved banner placement drift'
   else:
    assert positions['message']<min(n['i'] for n in cards)<max(n['i'] for n in cards)<positions['budget']<positions['consultation']<doc.cls('source-references')[0]['i'],'Article approved banner placement drift'
  for forbidden in [common['visibilityContract'],common['sharedNotices']['renderRule']]:assert forbidden not in visible_body,'Internal metadata leaked'
 # Internal links and anchors are checked after all five document IDs exist.
 for rel,doc in docs.items():
  for link in doc.where('a'):
   u=urlsplit(link['attrs']['href'])
   if u.scheme or u.netloc:continue
   path=u.path or ('/'+rel.removesuffix('index.html') if rel!='index.html' else '/')
   target='index.html' if path=='/' else path.lstrip('/')+'index.html' if path.endswith('/') else path.lstrip('/')
   assert target in docs,f'Broken static internal route: {rel}: {u.geturl()}'
   if u.fragment:assert u.fragment in ids[target],f'Broken static anchor: {rel}: {u.geturl()}'
 home=docs['index.html'];h=common['home'];check_metadata(home,h['title'],h['h1'],h['metaDescription'],'/',base)
 for text in [h['intro'],h['shortTalk'],h['priceNote'],common['sharedNotices']['materials'],common['sharedNotices']['collection']]:exactly(home,'p',text)
 for text in [h['productHeading'],h['articleHeading'],h['placeHeading']]:exactly(home,'h2',text)
 for cta in [h['phoneCta'],h['shopCta']]:link_exact(home,cta['label'],cta['href'],1)
 for rel in ['index.html','regions/index.html']:
  doc=docs[rel];cards=doc.cls('page-card');assert len(cards)==2,f'Actual rich guide card N2 drift: {rel}'
  assert [c['attrs'].get('href') for c in cards]==[a['href'] for a in common['articleCards']],'Guide-card route/order drift'
  for card,approved in zip(cards,common['articleCards']):
   assert all(norm(card['text']).count(approved[k])==1 for k in ['title','summary','ctaLabel']),'Guide-card approved text missing/duplicated'
 for approved,page in zip(original,pages):
  rel=page['url'].strip('/')+'/index.html';doc=docs[rel];meta=check_metadata(doc,approved['title'],approved['h1'],approved['metaDescription'],page['url'],base)
  breadcrumb=doc.cls('breadcrumb');assert len(breadcrumb)==1 and breadcrumb[0]['attrs'].get('aria-label')==common['accessibility']['breadcrumb'],'Approved breadcrumb aria label drift'
  assert meta.get('og:image:alt')==bysku[approved['productSkus'][0]]['imageAlt'],'Article OG image alt drift'
  exactly(doc,'p',approved['firstAnswer']);assert sum(t.count(approved['firstAnswer']) for _,t in doc.text_events)==1,'FirstAnswer duplication'
  headings=[]
  for section in approved['sections']:
   nodes=doc.where('h2','id',section['id']);assert len(nodes)==1 and norm(nodes[0]['text'])==section['heading'],'Section heading/order/anchor drift'
   headings.append(nodes[0]['i'])
   for paragraph in section['paragraphs']:
    exactly(doc,'p',paragraph)
    assert norm(doc.where('body')[0]['text']).count(norm(paragraph))==1,'Approved paragraph missing/duplicated anywhere in body'
  assert headings==sorted(headings),'Section order drift'
  # Every approved paragraph must follow its own heading before the next section.
  for i,section in enumerate(approved['sections']):
   last=headings[i];end=headings[i+1] if i+1<len(headings) else len(doc.nodes)
   for text in section['paragraphs']:
    node=exactly(doc,'p',text)[0];assert last<node['i']<end,'Paragraph ordering/section drift';last=node['i']
  for label in [common['faqHeading'],common['sourceHeading']]:exactly(doc,'h2',label)
  qnodes=doc.where(key='data-faq-question');anodes=doc.where(key='data-faq-answer')
  assert [norm(n['text']) for n in qnodes]==[q['question'] for q in approved['faq']],'FAQ questions missing/duplicated/drift'
  assert [norm(n['text']) for n in anodes]==[q['answer'] for q in approved['faq']],'FAQ answers missing/duplicated/drift'
  assert not any(hidden(n) for n in qnodes+anodes),'FAQ hidden/collapsed'
  for faq in approved['faq']:
   for value in [faq['question'],faq['answer']]:assert norm(doc.where('body')[0]['text']).count(norm(value))==1,'FAQ text duplicated outside FAQ markers'
  exactly(doc,'p',approved['sourceNote'])
  source_containers=doc.cls('source-references');assert len(source_containers)==1,'Single source section required'
  actual_sources=within(source_containers[0],'a')
  assert [(norm(n['text']),n['attrs'].get('href')) for n in actual_sources]==[(s['name'],s['url']) for s in approved['sourceLinks']],'Source section exact count/order/content drift'
  source_cards=doc.cls('source-card')
  assert len(source_cards)==len(approved['sourceLinks']),'Source-card count drift'
  for source_card,source in zip(source_cards,approved['sourceLinks']):
   assert [norm(n['text']) for n in within(source_card,'h3')]==[source['name']],'Source H3 hierarchy drift'
   assert not within(source_card,'h2'),'Source card must not duplicate H2'
   expected_type='business' if urlsplit(source['url']).hostname=='fwith.co.kr' else 'official'
   for key,value in [('data-source-name',source['name']),('data-source-type',expected_type),('data-source-verified-at','2026-10-13')]:assert source_card['attrs'].get(key)==value,f'Source metadata attribute drift: {key}'
   source_anchor=within(source_card,'a');assert len(source_anchor)==1 and source_anchor[0]['attrs'].get('aria-label')==source['name'],'Source aria-label drift'
   assert source_anchor[0]['children']==[],'Source link raw HTML/markup injection forbidden'
  source_nodes=[]
  for source in approved['sourceLinks']:source_nodes+=link_exact(doc,source['name'],source['url'],1)
  assert [n['i'] for n in source_nodes]==sorted(n['i'] for n in source_nodes),'Source order drift'
  link_exact(doc,approved['primaryCta']['label'],approved['primaryCta']['href'],1)
  link_exact(doc,approved['relatedLink']['label'],approved['relatedLink']['href'],1)
  exactly(doc,'p',approved['relatedLink']['intro'])
  for key,value in common['sharedNotices'].items():
   if key!='renderRule': assert not any(norm(n['text'])==value for n in doc.where('p')),'Seller policy duplicated outside approved article body'
 directory=docs['regions/index.html'];d=common['directory'];check_metadata(directory,d['title'],d['h1'],d['metaDescription'],'/regions/',base)
 for key in ['intro','relationNote','facilityScopeNote','districtGuideNote']:exactly(directory,'p',d[key])
 for key in ['purchaseHeading','legalHeading','facilityHeading']:exactly(directory,'h2',d[key])
 general=directory.where(key='data-general-purchase-links');assert len(general)==1,'General purchase link group missing/duplicate'
 for i,key in enumerate(['funeral','celebration']):link_exact(directory,d['generalLinkLabels'][key],original[i]['url'],1,general[0])
 legal_nodes=directory.where(key='data-legal-unit');admin_nodes=directory.where(key='data-administrative-unit')
 assert len(legal_nodes)==10 and len(admin_nodes)==23,'Directory 10 legal rows and 23 relationship occurrences required'
 legal_links=[]
 for unit in units:
  nodes=directory.where(key='data-legal-unit',value=unit['unitKey']);assert len(nodes)==1,'Legal unit HTML missing/duplicate'
  expected_links=[f for f in binding['facilityDestinations'] if f['legalCode']==unit['legalCode']]
  facility_nodes=directory.where(key='data-facility-legal-unit',value=unit['unitKey'])
  assert len(facility_nodes)==(1 if expected_links else 0),'Facility legal group missing/extra'
  links=[a for fnode in facility_nodes for a in within(fnode,'a')]
  assert [(a['attrs']['href'],norm(a['text'])) for a in links]==[(f['href'],f['heading']) for f in expected_links],'Directory legal facility assignment drift'
  for link,expected_link in zip(links,expected_links):assert link['attrs'].get('data-candidate-id')==expected_link['candidateId'],'Rendered facility candidate id drift'
  legal_links+=links
 assert len(legal_links)==3,'Exactly three legal facility links required'
 for admin in admins:
  nodes=directory.where(key='data-administrative-unit',value=admin['aliasKey']);assert len(nodes)==len(admin['relations']),'Each official relationship must appear once'
  actual=[]
  for node in nodes:
   assert norm(node['text'])==admin['name'] and node['attrs']['data-administrative-code']==admin['administrativeCode'],'Administrative code/name drift'
   assert not within(node,'a'),'Administrative rows must not imply facility assignment'
   parent=next((a for a in ancestor_nodes(node) if 'data-legal-unit' in a['attrs']),None);assert parent,'Missing legal parent'
   actual.append(parent['attrs']['data-legal-unit'])
  assert actual==[r['unitKey'] for r in admin['relations']],'Exact administrative/legal relationship drift'
 assert not directory.where(key='data-district-unassigned'),'No unassigned facility section is approved for Seocho'
 assert not any('opening-relocation' in n['attrs'].get('href','') for n in directory.where('a')),'Buyer occasion cannot become directory facility'
 notfound=docs['404.html'];n=common['notFound'];check_metadata(notfound,n['title'],n['h1'],n['text'],'/404.html',base)
 assert n['title']!=n['h1'],'404 approved title must differ from H1'
 exactly(notfound,'p',n['text']);link_exact(notfound,n['homeLabel'],n['homeHref'],1)
 for rel,doc in docs.items():
  for node in doc.where('script','type','application/ld+json'):
   schema=json.loads(node['text']);assert schema=={'@context':'https://schema.org','@type':'Florist','name':common['brand'],'url':base,'telephone':'1844-0644','areaServed':'서울특별시 서초구'},'Seller schema invented facility address/phone or metadata'
 for path in dist.glob('sitemap*.xml'):
  tree=ET.parse(path)
  assert not any((el.text or '').strip() and not (el.text or '').endswith('.xml') for el in tree.iter() if el.tag.endswith('}loc')),'Preview sitemap contains indexable URL'
 assert 'Disallow: /' in (dist/'robots.txt').read_text(),'Preview robots.txt not disallowed'
 assert 'X-Robots-Tag: noindex, nofollow, noarchive' in (dist/'_headers').read_text(),'Preview response header noindex missing'
 report={'status':'LOCAL_STATIC_VERIFIED','scope':'Sealed inputs, runtime data, and generated HTML/assets only. Browser screens, responsive layout, focus, live HTTP, deploy and search are UNVERIFIED.','approvalPins':PINS,'copyCorrection':release['copyCorrection'],'htmlFiles':len(docs),'details':len(pages),'articleParagraphs':[sum(len(s['paragraphs']) for s in a['sections']) for a in original],'articleFaqs':[len(a['faq']) for a in original],'articleSources':[len(a['sourceLinks']) for a in original],'directoryCards':2,'productCards':{'home':8,'eachDetail':4},'physicalFacilities':3,'buyerOccasions':1,'legalUnits':10,'administrativeUnits':18,'officialRelations':23,'legalFacilityLinks':3,'districtUnassignedFacilityLinks':0,'administrativeFacilityLinks':0,'assets':11,'previewNoindex':True,'sitemapCustomerUrls':0,'files':reports}
 if write:
  output=Path(os.environ.get('SEOCHO_QA_REPORT_PATH',root/'seocho-static-qa.json'));output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 if not quiet:print('SEOCHO STATIC QA: '+json.dumps(report,ensure_ascii=False))
 return report

def ancestor_nodes(node):
 node=node['parent']
 while node:
  yield node;node=node['parent']

if __name__=='__main__':inspect()
