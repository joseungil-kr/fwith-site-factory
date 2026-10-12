from pathlib import Path
import json, hashlib, re, sys, datetime
from lxml import html, etree
from PIL import Image
R=Path('/workspace/shared/geumcheon-factory/site-factory/seoul-geumcheon-flower')
O=Path('/workspace/shared/geumcheon-runtime-reference/site-factory/seoul-guro-flower')
E=Path('/workspace/shared/geumcheon-evidence/technical-review')
D=Path('/workspace/shared/geumcheon-factory/docs/direct-regional-release/seoul-geumcheon')
checks=[]
def check(name,ok,detail=None):
 checks.append({'name':name,'pass':bool(ok),'detail':detail})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def data(n):return json.loads((R/'src/data'/f'{n}.json').read_text())
def norm(s):return re.sub(r'\s+',' ',s).strip()
def txt(n):return norm(' '.join(n.itertext()))
def contains(h,s):return norm(s) in txt(h)
def run():
 h=json.loads(Path('/workspace/shared/geumcheon-evidence/implementation-handoff.rev3.json').read_text())
 for k in ['fixedPlan','candidatePlan','planReview','copy','copyReview']:
  p=D/h['approvedInputs'][k];check('Approved input digest: '+k,sha(p)==h['approvedInputs'][k+'Sha256'],sha(p))
 copyPath=D/'copy/geumcheon-copy.rev3.json'
 check('Approved revision-3 copy digest',sha(copyPath)=='01f9e71d13ad3a11122b832d649f60b6da976c85513ee90b6ccb531737fb7455')
 reviewPath=D/'copy/independent-copy-review.rev3.json'
 check('Independent revision-3 review digest',sha(reviewPath)=='fd1a09b38acb21c708d5f418e6a293aac8b9dbb37cfeb49191595e807b87acc9')
 runtimeBinding=data('copy-review-bindings')
 check('Runtime revision-3 copy digest binding',runtimeBinding['approvedCopySha256']==sha(copyPath))
 check('Runtime revision-3 independent review digest binding',runtimeBinding['independentCopyReviewSha256']==sha(reviewPath))
 copy=json.loads(copyPath.read_text());a=copy['article'];c=copy['common']
 fixed=json.loads((D/'fixed-plan.json').read_text());membership=json.loads((D/'research/membership.json').read_text())
 for p in ['src/lib/regions-legacy.mjs','src/lib/guro-regions.mjs','src/data/guro-plan-binding.json','src/lib/directory-banner-split.mjs','src/components/SharedFlowerBanner.astro']:
  check('Exact Guro preservation: '+p,sha(R/p)==sha(O/p),{'actual':sha(R/p),'reference':sha(O/p)})
 lock=json.loads((R/'package-lock.json').read_text());originalLock=json.loads((O/'package-lock.json').read_text())
 for x in [lock,originalLock]:x.pop('name');x['packages'][''].pop('name')
 check('Original resolved dependency lock retained; only package identity renamed',lock==originalLock)
 check('Approved copy full byte digest',sha(R/'src/data/geumcheon-copy.json')==sha(copyPath))
 pages=data('pages');cov=data('region-coverage');policy=data('region-policy');arch=data('architecture');manifest=data('publish-manifest');config=data('site-config')
 check('N1 customer source',len(pages)==1 and len(cov['representatives'])==1)
 check('Two physical facilities, zero areas',len(cov['facilities'])==2 and cov['areaContexts']==[])
 check('Exact physical facility identities',set(f['facilityKey'] for f in cov['facilities'])==set(a['candidateIds']))
 check('Legal membership preserved exactly',[(u['legalCode'],u['name']) for u in cov['units']]==[(u['code'],u['name']) for u in membership['legalDongs']])
 check('Administrative membership preserved exactly',[(u['administrativeCode'],u['name']) for u in cov['administrativeCrosswalk']]==[(u['code'],u['name']) for u in membership['administrativeDongs']])
 unitcode={u['unitKey']:u['legalCode'] for u in cov['units']}
 pairs=[(u['administrativeCode'],unitcode[r['unitKey']]) for u in cov['administrativeCrosswalk'] for r in u['relations']]
 check('All 10 legal/admin relations exact',pairs==[(p['administrativeCode'],p['legalCode']) for p in membership['membershipPairs']],pairs)
 p=pages[0]
 for k in ['pageKey','slug','url','title','h1','description','primaryKeyword','cardSummary','firstAnswer','contentMarkdown','faq','candidateIds']:
  check('Exact approved article '+k,p.get(k)==a[k])
 for anchor,approved in zip(p['facilityAnchors'],a['facilityAnchors']):
  check('Exact anchor '+approved['anchor'],all(anchor.get(k)==v for k,v in approved.items()))
 check('Exact active unit union',p['regionUnitKeys']==[cov['facilities'][i]['unitKey'] for i in range(2)])
 held=[r['candidateId'] for r in fixed['candidateToArticleTrace'] if r['status']=='preplan-hold']
 check('No held customer context leakage',not any(x in json.dumps([cov,pages],ensure_ascii=False) for x in held))
 check('No prior customer region prose',not any(x in json.dumps(pages,ensure_ascii=False) for x in ['구로구','강서구','고려대학교','라마다','웨딩시티','서울창업허브']))
 check('Publication false',config['productionApproved'] is False and manifest['directRelease']['publicationAuthorized'] is False)
 check('Approved counts are source-only coverage',manifest['directRelease']['publishedCoverage']=={'numerator':0,'denominator':1,'percent':0})
 omit={'approvalVerified','status','file','order','sourceMode','snapshotId','snapshotHash'}
 calculatedSnapshot=hashlib.sha256(json.dumps({k:v for k,v in p.items() if k not in omit},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 check('Independently recomputed snapshot digest',p['snapshotHash']==calculatedSnapshot,calculatedSnapshot)
 check('Snapshot ID exact digest prefix',p['snapshotId']==f"direct-content-{p['slug']}-{calculatedSnapshot[:16]}")
 check('Approved rev3 body digest',hashlib.sha256(p['contentMarkdown'].encode()).hexdigest()=='6711f0804e2d52c018834cd6bdfd8c1cca6b858171a5f39391d1948455c3e585')
 for collection in ['publish-manifest','page-map','architecture']:
  pp=data(collection)['pages'];check(collection+' N1',len(pp)==1)
  for k in ['snapshotId','snapshotHash','candidateIds','facilityAnchors','contextKey','purchaseIntentKey','regionUnitKeys']:
   check(collection+' exact '+k,pp[0].get(k)==p.get(k))
 products=data('products')
 check('Four funeral-only products',len(products)==4 and all(x['family']=='funeral' for x in products))
 for approved in c['productCards']:
  matches=[x for x in products if x['officialSku']==approved['sku']];check('SKU unique '+approved['sku'],len(matches)==1)
  if not matches:continue
  pp=matches[0];img=R/'public'/pp['img'].lstrip('/')
  check('SKU basic price '+approved['sku'],pp['price']==approved['basicPriceKRW'])
  check('SKU exact URL '+approved['sku'],pp['orderUrl']==approved['officialUrl'])
  check('SKU actual image '+approved['sku'],sha(img)==approved['imageSha256'],sha(img))
  with Image.open(img) as image:check('SKU image decodable '+approved['sku'],image.width>0 and image.height>0,{'size':image.size,'format':image.format})
 dist=R/'dist';expected=['404.html','index.html','regions/geumcheon-funeral-wreath/index.html','regions/index.html']
 actual=sorted(str(x.relative_to(dist)) for x in dist.rglob('*.html'));check('Exact four HTML routes',actual==expected,actual)
 routefiles={'home':dist/'index.html','directory':dist/'regions/index.html','article':dist/'regions/geumcheon-funeral-wreath/index.html','errorPage':dist/'404.html'}
 trees={k:html.fromstring(f.read_bytes()) for k,f in routefiles.items()}
 for route,tree in trees.items():
  check(route+' one H1',len(tree.xpath('//h1'))==1)
  robots=tree.xpath('//meta[@name="robots"]/@content');check(route+' noindex robots',len(robots)==1 and 'noindex' in robots[0],robots)
  canonical=tree.xpath('//link[@rel="canonical"]/@href')
  path={'home':'/','directory':'/regions/','article':a['url'],'errorPage':None}[route]
  check(route+' canonical',canonical==([] if path is None else [config['previewUrl'].rstrip('/')+path]),canonical)
  check(route+' no duplicate IDs',len(tree.xpath('//*[@id]/@id'))==len(set(tree.xpath('//*[@id]/@id'))))
  expectedH1=a['h1'] if route=='article' else c[route]['h1'];check(route+' approved H1',txt(tree.xpath('//h1')[0])==expectedH1)
  for k in ['title','description']:
   if route=='errorPage' and k=='description':continue
   value=a[k] if route=='article' else c[route][k]
   actual=tree.xpath('//title/text()') if k=='title' else tree.xpath('//meta[@name="description"]/@content')
   check(route+' approved '+k,actual==[value],actual)
  banners=tree.xpath('//*[@data-shared-flower-banner]');expectedB=c['sharedBanners']['assets'] if route in ['home','article'] else []
  check(route+' exact banner count',len(banners)==len(expectedB),len(banners))
  for b,bc in zip(banners,expectedB):
   check(route+' banner variant '+bc['variant'],b.get('data-shared-flower-banner')==bc['variant'])
   check(route+' banner alt '+bc['variant'],b.xpath('.//img/@alt')==[bc['alt']])
   check(route+' banner caption '+bc['variant'],len(b.xpath('.//figcaption'))==1 and txt(b.xpath('.//figcaption')[0])==c['sharedBanners']['caption'])
  inline=tree.xpath('//*[@data-order-banner="inline"]');check(route+' inline count',len(inline)==(0 if route=='errorPage' else 1))
  if inline:
   expect=c['inlineOrder']['text' if route=='home' else 'compactText'];check(route+' correct inline text',contains(inline[0],expect))
   other=c['inlineOrder']['compactText' if route=='home' else 'text'];check(route+' alternative inline absent',not contains(inline[0],other))
   for k in ['heading','hours','phoneLabel','onlineLabel']:check(route+' inline '+k,contains(inline[0],c['inlineOrder'][k]))
  check(route+' notice placement',contains(tree,c['productSharedNotice'])==(route=='home'))
  if route in ['home','article']:
   cards=tree.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," product-card ")]')
   check(route+' four actual product cards',len(cards)==4)
   for card,pc in zip(cards,c['productCards']):
    check(route+' product card key '+pc['sku'],card.get('data-product-key')==pc['key'])
    for key in ['name','description','priceLabel','ctaLabel']:check(route+' product '+pc['sku']+' '+key,contains(card,pc[key]))
    check(route+' product '+pc['sku']+' image alt',card.xpath('.//img/@alt')==[pc['imageAlt']])
    check(route+' product '+pc['sku']+' exact link',card.xpath('.//a/@href')==[pc['ctaUrl']])
  check(route+' no wrong funeral navigation',not any(x in txt(tree) for x in ['축하화환','구로구','강서구','예식장','사무실 화환','개업 화환']))
  for k in ['brand','description','affiliationNotice','phoneLabel','hours']:check(route+' footer '+k,any(contains(el,c['footer'][k]) for el in tree.xpath('//footer')))
  for link in c['footer']['links']:check(route+' footer link '+link['label'],any(txt(el)==link['label'] and el.get('href')==link['href'] for el in tree.xpath('//footer//a')))
 tree=trees['article']
 bodyText=re.sub(r'\s+','',''.join(tree.itertext()))
 for i,block in enumerate(a['contentMarkdown'].split('\n\n')):
  rendered=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',block).replace('**','')
  rendered=re.sub(r'(?m)^(?:## |[-*] )','',rendered)
  check('Actual body block '+str(i)+' rendered completely',re.sub(r'\s+','',rendered) in bodyText)
 check('Article first answer rendered completely',re.sub(r'\s+','',a['firstAnswer']) in bodyText)
 expectedHeadings=[line[3:] for line in a['contentMarkdown'].splitlines() if line.startswith('## ')]
 check('All body H2 order preserved',[txt(x) for x in tree.xpath('//h2')][:len(expectedHeadings)]==expectedHeadings)
 for fa in a['facilityAnchors']:
  els=tree.xpath('//*[@id=$id]',id=fa['anchor']);check('Actual H2 anchor '+fa['anchor'],len(els)==1 and els[0].tag=='h2' and txt(els[0])==fa['heading'])
 for faq in a['faq']:
  check('Visible FAQ question: '+faq['question'],contains(tree,faq['question']))
  check('Visible FAQ answer: '+faq['question'],contains(tree,faq['answer']))
 check('Source note visible',contains(tree,a['sourceNote']))
 for link in a['sourceLinks']:check('Source link '+link['label'],any(txt(el)==link['label'] and el.get('href')==link['url'] for el in tree.xpath('//a')))
 tree=trees['directory'];cards=tree.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," page-card ")]')
 check('N1 actual directory cards',len(cards)==1)
 check('Exact directory card',len(cards)==1 and cards[0].get('href')==c['directory']['cardHref'] and contains(cards[0],c['directory']['cardTitle']) and contains(cards[0],c['directory']['cardSummary']))
 check('All three legal units rendered',len(tree.xpath('//*[@data-legal-unit]'))==3)
 check('All 10 administrative units rendered',len(tree.xpath('//*[@data-administrative-unit]'))==10)
 for fa in a['facilityAnchors']:
  check('Legal inverse destination exactly once '+fa['anchor'],len(tree.xpath('//*[@data-legal-unit]//a[@href=$href]',href=fa['href']))==1)
 for k in ['intro','districtHeading','districtIntro','legalHeading','administrativeSummary','administrativeNote','emptyUnitLabel','officialAreaLinkLabel']:check('Directory approved '+k,contains(tree,c['directory'][k]))
 tree=trees['home']
 for k in ['eyebrow','intro']:check('Home approved '+k,contains(tree,c['home'][k]))
 for fact in c['home']['facts']:check('Home fact '+fact,contains(tree,fact))
 for sect in ['venueSection','productSection']:
  for k in ['heading','text']:check('Home '+sect+' '+k,contains(tree,c['home'][sect][k]))
 for k in ['cardTitle','cardText']:check('Home venue '+k,contains(tree,c['home']['venueSection'][k]))
 locations=[]
 for f in dist.glob('sitemap*.xml'):
  locs=etree.fromstring(f.read_bytes()).xpath('//*[local-name()="loc"]/text()');locations.extend(locs)
 check('No noindex,fragment,held,404 sitemap URLs',all(x.endswith('.xml') for x in locations),locations)
 robots=(dist/'robots.txt').read_text();check('Preview robots disallow all','Disallow: /' in robots,robots)
 for route in fixed['routeAndBannerContract']['expectedMissingCustomerRoutes']:
  check('Held/empty route absent '+route,not (dist/route.strip('/')/'index.html').exists())
 check('Directory count predicates remain exact','noindex={items.length < 3}' in (R/'src/pages/[category]/index.astro').read_text() and 'showBanners={items.length>=3}' in (R/'src/pages/[category]/index.astro').read_text())
 (E/'rendered-visible-text.json').write_text(json.dumps({k:txt(v.xpath('//body')[0]) for k,v in trees.items()},ensure_ascii=False,indent=2))
try:run()
except Exception as e:check('Audit completed without exception',False,repr(e))
report={'reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(R),'referenceCommit':'500d82d01c1cdaed3ebde047bb3ce056705daac1','scope':'Independent local source and actual built HTML review. No public HTTP or visual browser attestation.','pass':all(c['pass'] for c in checks),'counts':{'total':len(checks),'pass':sum(c['pass'] for c in checks),'fail':sum(not c['pass'] for c in checks)},'checks':checks}
(E/'independent-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
for c in checks:
 if not c['pass']:print('FAIL',c['name'],json.dumps(c['detail'],ensure_ascii=False))
sys.exit(0 if report['pass'] else 1)
