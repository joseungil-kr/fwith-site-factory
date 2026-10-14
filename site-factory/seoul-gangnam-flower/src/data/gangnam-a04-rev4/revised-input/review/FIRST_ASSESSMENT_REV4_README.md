# rev4 독립 첫 재평가

[직접 확인] 동일 고정 rubric과 동일 frozen target으로 HOME·근조·결혼·행사 네 primary를 재평가했다. 모두 raw/effective 100점이며 이번 입력의 필수 정렬 위반은 없다. 목록과 404는 여전히 NA/null이다.

행사 첫 답변은 153자에서 154자로 바뀌었다. 새 첫 문구는 “강남구 전시와 기업행사를 축하하는 화환은”이다. 강남구는 정규화 span [0,3)에 있고 화환도 직접 표현된다. 직접 답변 첫 문장은 61자 이내에 끝난다. A2는 5에서 10으로 바뀌고 G4 ceiling은 해소된다. 배점·threshold·alias·primary target은 바꾸지 않았다.

실제 새 JSON을 기존 JSON과 재귀 대조했다. 고객 문구 변경은 /articles/2/firstAnswer 한 곳이며 가격·조건을 포함한 나머지 suffix가 동일하다. 두 산출 문자 수가 각각 1 증가했고 나머지는 명시한 metadata 변경이다. 새 runtime 입력의 articles/common도 새 article 및 기존 common과 일치한다.

[미확인] 새 첫 답변은 draft-input이다. 현재 기존 HTML의 수정·렌더·브라우저·배포를 확인한 결과가 아니다. 기존 원문, 과거 행사 raw95/effective89 REVISE, 과거 재현 결과, rubric과 targets는 보존했다. 기존 문구 판정을 새 입력으로 소급 수정하지 않았다.

독립성: 구버전의 두 평가가 저장된 후 구버전 재현 결과는 비교했다. 이 rev4 첫 결과 저장 전에 새로운 두 번째 rev4 결과/점수는 열람하지 않았다.

검증 증거: first-assessment.rev4.json의 실제 문구/span/36개 행별 판단과 입력 diff, first-assessment.rev4-readback-log.json의 399개 인용 span·4개 재계산·11개 저장질의·20개 원본 hash 확인.
