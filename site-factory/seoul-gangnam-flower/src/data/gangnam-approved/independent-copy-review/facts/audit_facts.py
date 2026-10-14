import json,hashlib,re,zipfile,struct
from pathlib import Path
from html.parser import HTMLParser
from datetime import datetime,timezone
P=Path('/workspace/shared/gangnam-plan-copy-20261013'); R=Path('/workspace/shared/gangnam-research-20261013'); O=P/'independent-copy-review/facts'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,d):(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
checks=[]
def ck(name,condition,details=None):
 checks.append({'check':name,'pass':bool(condition),'details':details});return bool(condition)
class HTML(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.attrs=[];self.skip=0
 def handle_starttag(self,t,a):
  if t in ['script','style']:self.skip+=1
  self.attrs.extend((t,k,v) for k,v in a)
 def handle_endtag(self,t):
  if t in ['script','style']:self.skip=max(0,self.skip-1)
 def handle_data(self,d):
  if not self.skip and d.strip():self.parts.extend(d.strip().splitlines())
def html(p):
 h=HTML();h.feed(Path(p).read_text());return h,'\n'.join(h.parts)
A=read(P/'copy/article-copy.final.json'); C=read(P/'copy/common-visible-copy.final.json')['common']; D=read(P/'handoff/directory-input.json'); G=read(P/'plan/evidence-registry.json'); F=read(P/'plan/fixed-plan.json'); assets=read(P/'handoff/approved-assets.json')['assets']
manifest=read(R/'delivery-manifest.json'); rm=read(P/'copy/review-input-manifest.json')
hashes=[]
for base,m,name in [(R,manifest,'research-delivery'),(P,rm,'copy-review')]:
 for x in m['files']:
  p=base/x['path'];actual=sha(p) if p.is_file() else None
  hashes.append({'manifest':name,'path':str(p),'sha256':actual,'bytes':p.stat().st_size if p.is_file() else None,'matches':actual==x['sha256'] and p.stat().st_size==x['bytes']})
ck('research_manifest_expected_hash',sha(R/'delivery-manifest.json')=='c6dd49cd8ef6f70e4cab38f49aaf4df4d839545528d5ffc10bff6b51c671863a')
ck('all_manifest_files_byte_verified',all(x['matches'] for x in hashes),{'counts':{'research':len(manifest['files']),'copy':len(rm['files'])},'mismatches':[x for x in hashes if not x['matches']]})
ck('frozen_plan_expected_hash',sha(P/'plan/fixed-plan.json')=='82bf53fb58d01c65d7fe87e730fcaf39ec60620603f671696074ba41510e68c3')
write('input-hash-audit.json',hashes)
# Independently parse the official original archive, not authored membership.
z=zipfile.ZipFile(R/'raw/mois-20261012.zip'); units=[]
for filename,kind in [('KIKcd_B.20261012','legalUnits'),('KIKcd_H.20261012','administrativeUnits'),('KIKmix.20261012','relations')]:
 lines=[l.split() for l in z.read('jscode20261012/'+filename).decode('cp949').splitlines() if l.startswith('11680') and not l.startswith('1168000000')]
 if kind=='relations':actual=[{'administrativeCode':x[0],'administrativeName':x[3],'legalCode':x[4],'legalName':x[5],'created':x[6],'source':filename} for x in lines]
 else:actual=[{'code':x[0],'name':x[3],'created':x[4],'source':filename} for x in lines]
 ck('archive_exact_'+kind,actual==D[kind],{'count':len(actual)})
 units.append({'kind':kind,'originalArchiveMember':filename,'values':actual})
ck('membership_counts',list(map(len,[D['legalUnits'],D['administrativeUnits'],D['relations']]))==[14,22,31])
write('membership-archive-readback.json',units)
anchors=D['physicalAnchors'];ck('five_physical_anchors',len(anchors)==5)
ck('all_facility_admin_assignments_null',all(x['administrativeDong'] is None for x in anchors))
ck('samsung_setec_legal_codes_null',all(x['legalDong'] is None and x['legalDongCode'] is None for x in anchors if x['id'] in ['samsung-seoul-funeral','setec']))
ck('no_lot_number_conflict_in_customer_copy',all(s not in json.dumps([A,C,D],ensure_ascii=False) for s in ['146-92','146-2']))
# Preserved discovery inventory, including all nonlocal/held groups.
original=read(R/'facilities/facility-evidence.json');inventory=read(P/'plan/candidate-inventory.json');ledger=read(P/'plan/candidate-ledger.json')['groups']
ck('original_inventory_exact_preservation',inventory==original)
ck('all_12_candidate_groups_preserved',len(ledger)==len(original['facilities'])+len(original['nonlocalExclusions'])+len(original['heldDiscoveries'])==12)
ck('seven_facility_candidates_preserved',all(next(x for x in ledger if x['id']==y['id'])['roadAddress']==y['roadAddress'] for y in original['facilities']))
ck('three_nonlocal_exclusions_exact', [x['original'] for x in ledger if x['status']=='excluded_nonlocal']==original['nonlocalExclusions'])
ck('two_unresolved_groups_exact',[x['original'] for x in ledger if x['status']=='hold_original_access_or_address']==original['heldDiscoveries'])
ck('all_candidate_admin_null',all(x.get('administrativeDong') is None for x in ledger))
ck('no_facility_standalone_urls',all(x['newStandaloneFacilityUrl'] is None for x in ledger))
write('candidate-preservation-audit.json',{'groups':ledger,'preservationCheckedAgainst':str(R/'facilities/facility-evidence.json')})
# Reparse original 8 product HTML, exact SKU, official heading, sale price, image URL and CTAs.
prod=[]
for c in C['productCards']:
 sku=c['sku']; h,t=html(R/'raw'/f'fwith-{sku}.html'); src=next(x for x in read(R/'source-index.json')['sources'] if x['id']=='fwith-'+sku)
 # Sale price occurs immediately after 요약정보 및 구매, not a related product price.
 match=re.search(r'요약정보 및 구매.*?판매가격\s*([\d,]+)원\s*배송비결제\s*주문시 결제',t,re.S)
 ok=match is not None and int(match.group(1).replace(',',''))==c['basicPriceKRW']
 title_before_sku=c['name']+'\n['+sku+']'
 checks_for={'exact_name_next_to_sku':title_before_sku in t,'own_sale_price':ok,'detail_url':c['cta']['href']==src['url']==src['finalUrl'],'image_url_in_html':any(v==c['imageUrl'] for _,_,v in h.attrs),'photo_sha':sha(R/'raw'/f'{sku}-photo.jpg')==c['imageSha256'],'shipping_additional_notice':'추가 배송비가 발생할 수 있습니다.' in t,'seller_phone':'1844-0644' in t}
 prod.append({'sku':sku,'name':c['name'],'priceKRW':c['basicPriceKRW'],'checks':checks_for,'htmlSha256':sha(R/'raw'/f'fwith-{sku}.html'),'photoSha256':c['imageSha256'],'sourceUrl':src['url']})
 ck('product_'+sku,all(checks_for.values()),checks_for)
ck('eight_exact_products',len(prod)==8 and len({x['sku'] for x in prod})==8)
write('product-readback.json',prod)
# Verify all copied bytes against source and pre-approved banner manifest.
bm=read(R/'reuse/shared-banner-manifest.json');assetchecks=[]
for a in assets:
 source=Path(a['sourceFile']);target=P/a['file'];actual=sha(target)
 ac={'file':a['file'],'sha256':actual,'sourceSha256':sha(source),'declaredSha256':a['sha256'],'exactBytes':target.read_bytes()==source.read_bytes(),'byteCount':target.stat().st_size,'matches':actual==a['sha256']==sha(source) and a['bytes']==target.stat().st_size}
 if a['kind']!='actual-sale-product':
  b=next(x for x in bm if source.stem==x['name']);ac['approvedManifestMatches']=actual==b['sha256']
 else:ac['cardExact']=a['copy']==next(c for c in C['productCards'] if c['sku']==a['sku'])
 assetchecks.append(ac)
ck('eleven_assets_exact',len(assets)==11 and all(a['matches'] and a['exactBytes'] and a.get('approvedManifestMatches',True) and a.get('cardExact',True) for a in assetchecks))
write('asset-byte-audit.json',assetchecks)
# Exact source URLs are observed URLs, not guessed routes.
fi=read(R/'facilities/source-index.json');rootidx=read(R/'source-index.json')['sources'];urls={x.get('finalUrl',x.get('requestedUrl')) for x in fi}|{x.get('finalUrl',x.get('url')) for x in rootidx}
links=[]
for article in A['articles']:
 for l in article['sourceLinks']:
  links.append({'article':article['id'],**l,'exactObservedUrl':l['url'] in urls})
ck('all_13_source_links_exact_observed_urls',len(links)==13 and all(x['exactObservedUrl'] for x in links))
write('source-link-audit.json',links)
# Independent original HTML excerpts for facts rather than trusting registry text.
assertions={
'samsung-procedure':['당 장례식장에서는 조화진열이 빈소 內에만 가능하오니','일원로 81','02-3410-3151~3'],
'samsung-flower':['조화진열을 10개 이내로 제한'],
'yonsei-route':['언주로 211','도곡동 146-92','도곡동 146-2','02-2019-4000'],
'yonsei-use':['강남세브란스병원에서 임종하신 경우','본원(강남세브란스병원)'],
'yonsei-floors':['지하2층','1호실','2호실','3호실','5호실'],
'grandhill-route':['강남구 역삼로 607(대치동)'],
'grandhill-floor3':['3F GRAND BALLROOM','그랜드볼룸 홀','2F SABRINA','사브리나 홀','1F FLORIA','플로리아 홀'],
'coex-navigation':['강남구 영동대로 513','(삼성동, 코엑스)'],
'coex-meeting-guide-list':['행사 준비 가이드','2026.03.18','이벤트준비가이드-V02.pdf'],
'setec-parking':['강남구 남부순환로 3104'],
'gs-hospital-about':['강남구 언주로 211(도곡동)']}
sourcechecks=[]
for id,claims in assertions.items():
 h,t=html(R/'facilities/raw'/f'{id}.html'); source=next(x for x in fi if x['id']==id)
 results=[{'phrase':c,'found':c in t} for c in claims]
 sourcechecks.append({'id':id,'savedHtmlSha256':sha(R/'facilities/raw'/f'{id}.html'),'matchesSavedSourceIndex':sha(R/'facilities/raw'/f'{id}.html')==source['storedSha256'],'url':source['finalUrl'],'claims':results,'excerpts':[t[max(0,t.find(c)-60):t.find(c)+len(c)+100] for c in claims]})
 ck('original_html_'+id,all(x['found'] for x in results) and sourcechecks[-1]['matchesSavedSourceIndex'])
write('original-html-fact-audit.json',sourcechecks)
# Matrix/map bind exact authored sections; no stale revision or invented answer anchors.
sections={(a['id'],s['id']):s for a in A['articles'] for s in a['sections']};cm=read(P/'copy/claim-evidence-map.json');mx=read(P/'copy/intent-completion-matrix.json')
ck('map_covers_every_section',set(sections)=={(x['article'],x['sectionId']) for x in cm})
ck('map_paragraphs_and_evidence_exact',all(x['exactParagraphs']==sections[(x['article'],x['sectionId'])]['paragraphs'] and x['evidence']==[{'id':id,**G[id]} for id in sections[(x['article'],x['sectionId'])]['evidence']] for x in cm))
mxa=[]
for x in mx:
 a=next(a for a in A['articles'] if a['id']==x['article']);ids=[loc.split('#')[1] for loc in x['answerLocations']]; pars=[p for id in ids for p in sections[(a['id'],id)]['paragraphs']]
 ok=x['answer']==pars and all(loc==a['url']+'#'+id for loc,id in zip(x['answerLocations'],ids)) and all(e in G for e in x['evidenceIds'])
 mxa.append({'article':x['article'],'question':x['question'],'exactAnswerAndAnchors':ok})
ck('all_19_matrix_answers_exact',len(mxa)==19 and all(x['exactAnswerAndAnchors'] for x in mxa))
ck('article_cards_exact',all(c['summary']==a['cardSummary'] and c['title']==a['h1'] and c['href']==a['url'] for c,a in zip(C['articleCards'],A['articles'])))
ck('directory_cards_exact',D['directoryArticleCards']==C['articleCards'])
ck('article_product_lists_match_frozen_plan',all(a['productSkus']==p['products'] for a,p in zip(A['articles'],F['pages'])))
ck('all_facility_anchors_resolve_in_copy',all(x['href']==next(a for a in A['articles'] if a['id']==x['articleId'])['url']+'#'+x['id'] and (x['articleId'],x['id']) in sections for x in anchors))
write('map-matrix-audit.json',mxa)
write('automated-checks.json',{'checkedAt':datetime.now(timezone.utc).isoformat(),'checkCount':len(checks),'passes':sum(x['pass'] for x in checks),'failures':[x for x in checks if not x['pass']],'checks':checks})
print(json.dumps({'checkCount':len(checks),'passes':sum(x['pass'] for x in checks),'failures':[x for x in checks if not x['pass']]},ensure_ascii=False,indent=2))
