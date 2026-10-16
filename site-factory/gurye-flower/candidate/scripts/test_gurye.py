import json,tempfile,shutil
from pathlib import Path
from qa_gurye import check,validate_output_paths
from expected_surface import C
(C/'evidence').mkdir(parents=True,exist_ok=True)
html=(C/'dist/index.html').read_text()
mutations={
 'wrong_gurye_fee':lambda h:h.replace('구례 추가배송비 20,000원','구례 추가배송비 10,000원',1),
 'wrong_price':lambda h:h.replace('상품가 59,000원','상품가 49,000원',1),
 'b060_19_instead_of_21':lambda h:h.replace('B060 상세 하단은 21시','B060 상세 하단은 19시',1),
 'missing_upper_weekend_context':lambda h:h.replace('주말·공휴일 19시 이후 주문을 다음 날 13시 전후로 안내합니다.','',1),
 'missing_facility_limit':lambda h:h.replace('현재 빈소 운영과 외부 화환의 반입 여부·수령 시간·설치 위치는 시설의 안내가 필요합니다.','',1),
 'hidden_faq':lambda h:h.replace('id="questions"','hidden id="questions"',1),
 'wrong_product_destination':lambda h:h.replace('href="https://fwith.co.kr/shop/item.php?it_id=B201"','href="https://fwith.co.kr/shop/item.php?it_id=B203"',1),
 'broken_anchor':lambda h:h.replace('href="#products-and-cost"','href="#broken"',1),
 'extra_unreviewed_sentence':lambda h:h.replace('</body>','<p>구례 당일 배송을 보장합니다.</p></body>',1),
 'indexable_preview':lambda h:h.replace('noindex,nofollow','index,follow',1),
 'production_canonical':lambda h:h.replace('</head>','<link rel="canonical" href="https://gurye.fwith.kr/"></head>',1),
 'wrong_banner':lambda h:h.replace('flower-message.webp','flower-budget.webp',1),
 'faq_answer_changed':lambda h:h.replace('별도 화환 수거 서비스를 제공하지 않습니다.','화환을 무료로 수거해 드립니다.',1),
}
results=[]
for name,mutate in mutations.items():
 changed=mutate(html);assert changed!=html,name
 try:check(changed)
 except (AssertionError,ValueError):results.append({'test':name,'rejected':True})
 else:raise AssertionError('Mutation escaped: '+name)
check(html)
(C/'evidence/negative-tests.json').write_text(json.dumps({'baselinePass':True,'mutations':results},ensure_ascii=False,indent=2)+'\n');print('13/13 harmful HTML mutations rejected; untouched baseline passed')

with tempfile.TemporaryDirectory(prefix='gurye-output-test-') as temp:
 target=Path(temp)/'dist';shutil.copytree(C/'dist',target)
 (target/'indexnow-fixture.txt').write_text('non-secret test fixture')
 try:validate_output_paths(target)
 except AssertionError:pass
 else:raise AssertionError('Unexpected key-shaped output escaped')
print('Unexpected extra key-shaped artifact rejected; no secret key generated')
