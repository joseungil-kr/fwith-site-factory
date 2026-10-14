import json,hashlib,datetime
from pathlib import Path
O=Path(__file__).parent;R=Path('/workspace/shared/gangnam-research-20261013');S=Path('/workspace/shared/seocho-plan-copy-20261013')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
a=read(O/'copy/article-copy.final.json');cat=read(O/'plan/catalog-policy-evidence.json');plan=read(O/'plan/fixed-plan.json');banners=read(S/'copy/common-visible-copy.rev2.json')['common']['banners']
descriptions={
'B201':'흰색 바탕의 꽃 배열에 노란색과 검정·흰색 상단 장식이 보이는 사진입니다.',
'B203':'흰색·노란색 꽃 사이에 연분홍색이 보이고, 상단에는 밝은색 장식이 있습니다.',
'B205':'흰색 꽃 배열과 노란색 포인트, 노란 바탕의 상단 장식을 담은 상품사진입니다.',
'B060':'흰색·노란색·연분홍색 꽃과 길게 뻗은 초록색 소재가 보이는 사진입니다.',
'C200':'분홍색 상단 장식 아래 분홍·노랑·빨강·흰색이 어우러진 상품사진입니다.',
'C203':'크림색 상단 장식과 가운데 노란색 꽃, 여러 색의 꽃 배열이 보입니다.',
'C204':'분홍색 장식 아래 노란색·분홍색·흰색 꽃이 배치된 모습을 담았습니다.',
'C205':'분홍색 상단 장식과 노랑·분홍·흰색을 비롯한 다채로운 배열의 사진입니다.'}
cards=[]
for p in cat['products']:
 cards.append({'sku':p['sku'],'name':p['name'],'basicPriceKRW':p['priceKRW'],'priceLabel':f"기본가격 {p['priceKRW']:,}원",'description':descriptions[p['sku']],'imageUrl':p['photo']['url'],'imageAlt':f"{p['name']} {p['sku']} 판매상품 예시사진",'imageSha256':p['photo']['sha256'],'cta':{'label':'이 상품 보기·주문','href':p['source']['url']},'photoCaption':'판매상품 예시사진입니다. 계절·지역에 따라 소재와 형태가 달라질 수 있습니다.'})
common={
'brand':'꽃이랑','siteName':'꽃이랑 강남구 화환 안내',
'home':{'primaryKeyword':'강남구 화환','title':'강남구 화환 | 근조·결혼·행사 상품과 상담 | 꽃이랑','h1':'강남구 화환, 조의와 축하에 맞춰 준비하는 꽃','metaDescription':'근조와 결혼·행사에 전할 꽃이랑 화환 8종을 실제 사진과 기본가격으로 안내합니다. 삼성서울·연세 강남장례식장, 그랜드힐, 코엑스·SETEC의 장소 정보와 주문 상담을 담았습니다.','intro':'강남구에 보낼 근조·축하화환을 기본가격 59,000원부터 소개합니다. 빈소에 전하는 위로, 결혼하는 두 분의 축하, 전시와 기업행사의 응원에 맞춰 꽃이랑의 여덟 상품과 리본 문구를 상담합니다.','shortTalk':'전할 인사는 정했는데 꽃이 고민되시나요? 생각하신 예산과 보내는 뜻으로 상품 선택을 도와드립니다.','productHeading':'사진과 기본가격으로 만나는 여덟 상품','funeralProductHeading':'조의를 전할 근조상품','celebrationProductHeading':'결혼·행사를 축하할 상품','articleHeading':'이번에 전할 인사에 맞는 안내','placeHeading':'강남구 시설과 지역 이름','phoneCta':{'label':'1844-0644로 상품·주문 상담','href':'tel:1844-0644'},'shopCta':{'label':'꽃이랑 공식몰 방문','href':'https://fwith.co.kr/'},'priceNote':'표시가격은 상품 기본가격입니다. 배송비는 주문 시 결제하며 배송지에 따라 추가 배송비가 생길 수 있습니다. 최종 주문금액은 상담에서 안내합니다.','placeIntro':'장례식장의 빈소 진열 제한, 예식장의 홀, 전시장의 행사 후 반출처럼 보내는 곳에 따라 필요한 안내가 다릅니다. 장소별 설명에서 이번 인사와 관련된 내용을 보실 수 있습니다.','placeLinkLabel':'시설·지역 안내 보기','placeLinkHref':'/regions/'},
'navigation':{'home':'처음으로','regions':'강남구 시설·지역 안내','funeral':'근조화환','wedding':'결혼식 축하화환','event':'전시·기업행사 화환','phone':'상품·주문 상담'},
'articleCards':[{'id':x['id'],'title':x['h1'],'summary':x['cardSummary'],'href':x['url'],'ctaLabel':{'funeral':'근조상품과 빈소 안내','wedding':'결혼 축하상품과 홀 안내','event':'행사상품과 반출 안내'}[x['id']]} for x in a['articles']],
'productCards':cards,
'directory':{'title':'강남구 시설·지역별 화환 안내 | 꽃이랑','h1':'강남구 시설·지역 안내','metaDescription':'강남구의 근조·결혼·행사 화환 안내를 연결합니다. 삼성서울·연세 강남장례식장, 그랜드힐, 코엑스·SETEC 정보와 법정동·행정동 관계를 함께 담았습니다.','intro':'어느 자리로 전할 꽃인지에 따라 근조, 결혼, 전시·기업행사 안내를 보실 수 있습니다. 각 글에는 상품 선택과 함께 빈소·홀·행사의 조건을 설명합니다.','purchaseHeading':'목적에 맞는 상품과 주문 안내','legalHeading':'강남구 법정동과 행정동','legalColumn':'법정동','administrativeColumn':'관련 행정동','relationNote':'법정동과 행정동은 이름이 같아도 범위가 다를 수 있습니다. 아래 표는 동 이름의 관계를 보여주며, 개별 건물의 행정동을 지정하지 않습니다.','facilityHeading':'안내에 담은 다섯 장소','facilityScopeNote':'시설명은 해당 글의 장소 설명으로 연결됩니다. 외부 화환의 수령·진열·반출은 시설과 행사별 조건에 따릅니다.','generalLinkLabels':{'funeral':'근조화환 안내','wedding':'결혼식 화환 안내','event':'전시·기업행사 안내'},'districtGuideNote':'동 이름 아래의 상품 안내는 강남구의 세 구매 안내로 연결됩니다. 동별 시설이나 실제 배송 이력을 뜻하지 않습니다.','ungroupedFacilityHeading':'도로명주소로 안내하는 장소','ungroupedFacilityNote':'삼성서울병원 장례식장과 SETEC은 도로명주소로 안내합니다. 아래 시설 링크에 법정동을 임의로 붙이지 않았습니다.','bannerCount':3,'actualRichCardCount':3},
'faqHeading':'주문 전에 궁금하실 수 있는 내용','sourceHeading':'출처 및 확인 정보',
'sharedNotices':{'price':'상품 기본가격이며 배송지에 따라 추가 배송비가 생길 수 있습니다.','materials':'생화와 조화를 혼합한 상품입니다. 계절·지역에 따라 사진과 소재·형태가 일부 달라질 수 있습니다.','collection':'꽃이랑은 화환을 별도로 수거하지 않습니다.','orderTiming':'실제 전달 가능 일정과 최종금액은 주문 상담에서 안내합니다.','changeContact':'변경이나 상품 문의는 주문 정보와 함께 1844-0644로 알려주세요.','renderRule':'Home: priceNote once; materials and collection once after products. Articles: policy only at authored sections, no duplicate warning box/FAQ/footer. Exact product captions remain part of cards.'},
'banners':banners,
'footer':{'brandLine':'꽃이랑 · 강남구 근조·결혼·행사 화환 안내','phoneLabel':'상품·주문 상담 1844-0644','phoneHref':'tel:1844-0644','shopLabel':'꽃이랑 공식몰','shopHref':'https://fwith.co.kr/','homeLinkLabel':'강남구 화환 안내 처음으로'},
'notFound':{'title':'페이지를 찾을 수 없습니다 | 꽃이랑','h1':'찾으시는 페이지가 보이지 않아요','text':'처음 화면에서 근조·결혼·행사 상품과 강남구 장소 안내로 이어가실 수 있습니다.','homeLabel':'강남구 화환 안내로','homeHref':'/'},
'accessibility':{'skip':'본문 바로가기','navigation':'주요 메뉴','breadcrumb':'현재 위치'},
'articleUi':{'consultationHeading':'상품 선택과 주문 상담','catalogLinkLabel':'꽃이랑 공식몰 보기','relatedHeading':'다른 자리로 전할 꽃','directoryLinkLabel':'강남구 시설·지역 안내 보기','productPhotoGroupLabel':'실제 판매상품 사진','tocHeading':'이 글의 안내'},
'visibilityContract':'Only customer text fields are visible. Bindings/evidence/metadata/renderRule/visibilityContract are not customer text. Do not inherit unrelated region/place/business/service strings. Exact copied banners stay unchanged. Review any newly added runtime text.'}
doc={'schemaVersion':1,'revision':1,'status':'DRAFT_AWAITING_INDEPENDENT_EXACT_COPY_REVIEW','createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bindings':a['bindings'],'common':common}
write(O/'copy/common-visible-copy.rev1.json',doc);write(O/'copy/common-visible-copy.final.json',doc)
# exact asset handoff, actual photos from new Gangnam captured bytes
assets=[]
for prod,card in zip(cat['products'],cards):
 p=O/'handoff/assets/products'/f"{prod['sku']}.jpg"
 assets.append({'kind':'actual-sale-product','sku':prod['sku'],'sourceFile':str(R/prod['photo']['file']),'sourceUrl':prod['photo']['url'],'file':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size,'dimensions':[500,500],'proposedRuntimePath':f"public/images/products/{prod['sku']}.jpg",'copy':card})
for b in read(R/'reuse/shared-banner-manifest.json'):
 p=O/'handoff/assets/banners'/f"{b['name']}.webp";assets.append({'kind':'AI-common-banner','variant':b['name'].replace('flower-',''),'sourceFile':str(R/'reuse/banners'/p.name),'file':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size,'dimensions':[1774,887],'proposedRuntimePath':f'public/images/shared-banners/{p.name}'})
write(O/'handoff/approved-assets.json',{'classification':'Directly inspected local bytes and actual image pixels, not a public response','assetCount':11,'assets':assets,'bannersCopy':banners})
m=read(O/'plan/membership.json')
directory={'classification':'Planned data; no rendered or public links yet','regionCode':'11680','legalUnits':m['legalUnits'],'administrativeUnits':m['administrativeUnits'],'relations':m['relations'],'physicalAnchors':plan['facilityAnchors'],'occasions':[],'directoryArticleCards':common['articleCards'],'unlistedLegalDongs':[x['name'] for x in m['legalUnits'] if x['name'] not in [f['legalDong'] for f in plan['facilityAnchors']]],'facilityAdministrativeAssignment':None,'nullLegalDongAnchors':['samsung-seoul-funeral','setec'],'facilityAnchorProof':'Use source-published legal dong only; Samsung/SETEC remain road-address-only, not distributed among legal dongs. 3 article cards once, never inflate with facility anchors.'}
write(O/'handoff/directory-input.json',directory)
print('common and assets written')
