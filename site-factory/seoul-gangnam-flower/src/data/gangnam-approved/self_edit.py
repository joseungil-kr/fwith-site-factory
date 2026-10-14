from pathlib import Path
import json,hashlib,datetime,difflib
O=Path(__file__).parent
p=O/'copy/article-copy.final.json'; before=p.read_text(); x=json.loads(before)
replacements={
'고급·특대·특특대는 공식 상품명이며, 사진과 가격만으로 정확한 높이나 꽃 수량의 차이를 안내하지는 않습니다.':'고급·특대·특특대는 공식 상품명입니다. 정확한 높이나 꽃 수량이 궁금하신 경우에는 원하시는 상품을 기준으로 상담합니다.',
'현재 수령 가능한 공간과 반입 조건이 없는 상태에서 배송을 확정하지 않으며, 상담에서는 이 제한을 함께 설명합니다.':'받는 빈소의 수령 여건이 정해지지 않은 경우에는 결제보다 주문 가능 여부를 먼저 상담합니다.',
'진행 상태에 따른 안내를 받으실 수 있습니다.':'진행 상태에 맞춰 상담합니다.',
'여기에는 상품의 높이·폭이나 꽃 수량을 수치로 비교한 안내가 없으므로, 진열 공간에 맞는 구체적인 규격이 필요할 때는 해당 상품으로 상담합니다.':'진열 공간에 맞는 구체적인 높이·폭이나 꽃 수량이 필요할 때는 해당 상품을 기준으로 상담합니다.',
'사진의 모든 꽃이 같은 구성으로 확정된 주문을 뜻하지는 않습니다.':'계절별 소재 차이도 상품을 정할 때 함께 안내합니다.',
'상품가격에 회수 서비스가 포함된 것으로 안내하지 않습니다.':'상품가격에 별도 회수 서비스가 포함되어 있지는 않습니다.',
'주문별 제작·출고 상태와 사유에 따라 적용 내용이 달라질 수 있어 언제든 무료 취소된다고 안내하지 않습니다.':'제작·출고 상태와 요청 사유를 바탕으로 해당 주문의 처리 내용을 상담합니다.',
'현장 출입이나 설치·진열을 대신 조율하는 서비스까지 약속하는 안내는 아닙니다.':'현장 출입과 설치·진열 조건은 행사측 운영에 따르는 부분입니다.',
'개막 시각에 맞춰 마음을 전하고 싶으셔도 희망 시각만으로 정시 도착이 확정되지는 않습니다.':'개막에 맞춰 마음을 전하실 수 있을지, 희망 시각과 실제 가능한 일정을 구분해 상담합니다.',
'행사 취소만으로 제작된 상품까지 언제나 전액 환불된다고 안내하지 않습니다.':'행사가 취소되었더라도 이미 제작·출고된 상품에는 진행 상태별 조건이 적용됩니다.'}
for a in x['articles']:
 for s in a['sections']:
  s['paragraphs']=[next((t.replace(k,v) for k,v in replacements.items() if k in t),t) for t in s['paragraphs']]
 body='\n'.join([a['firstAnswer']]+[z for s in a['sections'] for z in s['paragraphs']]);a['uniqueBodyCharsIncludingFirstAnswer']=len(body);a['bodyAndFaqChars']=len(body)+a['faqChars']
x['revision']=2;x['editedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();x['priorDraft']={'path':'copy/article-copy.rev1.json','sha256':hashlib.sha256((O/'copy/article-copy.rev1.json').read_bytes()).hexdigest()}
after=json.dumps(x,ensure_ascii=False,indent=2)+'\n';p.write_text(after);(O/'copy/article-copy.rev2.json').write_text(after);(O/'copy/article-copy.self-edit.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='rev1',tofile='rev2')))
p=O/'copy/common-visible-copy.final.json';before=p.read_text();x=json.loads(before);x['revision']=2;x['editedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();x['common']['directory']['ungroupedFacilityNote']='삼성서울병원 장례식장과 SETEC의 위치는 아래 도로명주소 안내에서 보실 수 있습니다.';after=json.dumps(x,ensure_ascii=False,indent=2)+'\n';p.write_text(after);(O/'copy/common-visible-copy.rev2.json').write_text(after);(O/'copy/common-visible-copy.self-edit.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='rev1',tofile='rev2')))
