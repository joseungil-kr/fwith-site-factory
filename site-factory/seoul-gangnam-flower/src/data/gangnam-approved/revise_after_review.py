from pathlib import Path
import json,hashlib,datetime,difflib,shutil
O=Path(__file__).parent
p=O/'copy/article-copy.final.json';before=p.read_text();doc=json.loads(before);assert doc['revision']==2
arts={a['id']:a for a in doc['articles']}
def sec(a,s):return next(x for x in arts[a]['sections'] if x['id']==s)
sec('funeral','samsung-seoul-funeral')['paragraphs'][1]='꽃이랑 화환은 생화와 조화를 혼합하며, 반입은 받는 빈소의 수령 조건에 따릅니다. 수령 여건이 정해지지 않은 경우에는 결제보다 주문 가능 여부를 먼저 상담합니다.'
s=sec('funeral','order');s['paragraphs'][1]=s['paragraphs'][1].replace('희망하신 시각을 모든 주문의 도착 확약으로 받지는 않습니다.','희망하신 시각을 바탕으로 실제 가능한 전달 일정을 상담합니다.')
s=sec('funeral','changes');s['paragraphs'][0]=s['paragraphs'][0].replace('공식몰은 제작이 끝난 꽃상품과 배송지 기재 오류·수취 거부의 교환·환불 제한을 안내하고 있습니다.','공식몰은 제작이 끝난 꽃상품, 배송 완료 후 하루 이상 지난 경우, 배송지 기재 오류·수취 거부의 교환·환불 제한을 안내하고 있습니다.')
sec('wedding','grandhill-convention')['paragraphs'][1]='예식장 이름이 같아도 전달받으신 청첩장의 날짜·시간·홀이 이번 주문의 기준입니다. 외부 화환의 소재·크기와 반입 시간·진열 위치는 예식별 운영에 따릅니다. 이번 예식의 수령 안내를 바탕으로 주문 가능 여부를 상담합니다.'
s=sec('wedding','ribbon');s['paragraphs'][1]=s['paragraphs'][1].replace(' 두 분께 전할 축하와 보내는 이름이 정리되면, 리본 문구 상담이 한결 간단해집니다.','');s['paragraphs'][2]='친한 사이의 별명이나 농담을 넣고 싶으시면, 전하려는 뜻을 바탕으로 문구를 상담합니다.'
s=sec('wedding','materials');s['paragraphs'][0]=s['paragraphs'][0].replace(' 계절별 소재 차이도 상품을 정할 때 함께 안내합니다.','')
s=sec('wedding','changes');s['paragraphs'][0]=s['paragraphs'][0].replace('제작 완료 꽃상품, 배송지 기재 오류 또는 수취 거부에는 공식몰의 교환·환불 제한이 있습니다.','공식몰은 제작 완료 꽃상품과 배송지 기재 오류·수취 거부, 배송 완료 후 하루 이상 지난 경우에 교환·환불 제한을 안내합니다.')
sec('event','coex')['paragraphs'][1]='코엑스의 공식 회의실 행사 준비 가이드는 행사 후 남은 화환 등의 폐기물에 처리비용이 발생한다고 안내합니다. 실제 반출 방식과 비용 부담은 해당 행사의 운영 조건에 따릅니다.'
s=sec('event','setec');s['paragraphs'][1]=s['paragraphs'][1].replace(' 전시품 반출입 절차는 주최자와 참가자의 운영 규정이므로, 모든 화환 배송에 같은 서류가 반드시 필요하다고 안내하지는 않습니다.','')
s=sec('event','changes');s['paragraphs'][0]=s['paragraphs'][0].replace('제작이 끝난 꽃상품과 배송지 기재 오류·수취 거부에는 교환·환불 제한이 있습니다.','공식몰에서는 제작이 끝난 꽃상품, 배송지 기재 오류·수취 거부와 배송 완료 후 하루 이상 경과한 경우에 교환·환불을 제한한다고 안내합니다.')
arts['event']['faq']=[{'question':'행사 취소로 주문을 취소하면 카드 결제는 언제 반영되나요?','answer':'주문 취소 가능 여부는 제작·출고 상태에 따라 상담합니다. 취소 처리 뒤 카드 결제에 반영되기까지는 카드사 처리기간에 따라 일주일 정도 걸릴 수 있다고 공식몰에서 안내합니다.','evidence':['change-policy','seller-contact']}]
arts['event']['sourceNote']=arts['event']['sourceNote'].replace('2026년 3월 회의실 행사 준비 가이드','회의실 행사 준비 가이드')
for a in doc['articles']:
 body='\n'.join([a['firstAnswer']]+[z for s in a['sections'] for z in s['paragraphs']]);a['uniqueBodyCharsIncludingFirstAnswer']=len(body);a['faqChars']=sum(len(f['question'])+len(f['answer']) for f in a['faq']);a['bodyAndFaqChars']=len(body)+a['faqChars']
doc['revision']=3;doc['editedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();doc['priorDraft']={'path':'copy/article-copy.rev2.json','sha256':hashlib.sha256((O/'copy/article-copy.rev2.json').read_bytes()).hexdigest()};doc['revisionReason']='Independent editorial T01/C01/I01 and N01-N03; facts reviewer one-day policy omission and Coex list-date/edition distinction. No N/URL/catalog/asset/venue rule changes.'
after=json.dumps(doc,ensure_ascii=False,indent=2)+'\n';p.write_text(after);(O/'copy/article-copy.rev3.json').write_text(after);(O/'copy/reviewer-edit.rev2-to-rev3.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='rev2',tofile='rev3')))
print([(a['id'],a['uniqueBodyCharsIncludingFirstAnswer']) for a in doc['articles']])
