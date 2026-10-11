/** Decision help stays category-specific; it does not prescribe detail structure. */
/** @type {Record<string, {intro:string, decision:string[], families:string[], heading:string, cta:string}>} */
export const hubGuides = {
  funeral: {
    intro: '갑작스러운 부고에 어떤 말부터 전할지 망설여질 때가 있습니다. 근조화환의 사진과 예산을 살펴보고, 전하고 싶은 조의를 차분히 준비하세요.',
    decision: ['사진 속 꽃과 윗장식, 기본가격을 함께 비교', '짧은 위로의 말과 보내는 분 이름 준비', '빈소와 발인 일정에 맞춰 전달 상담'],
    families: ['funeral'], heading: '조의를 전하는 근조화환', cta: '근조화환 상품 확인'
  },
  business: {
    intro: '개업과 이전을 축하하는 화환은 매장 앞에 둘 공간과 받는 곳의 상호명이 중요합니다.',
    decision: ['매장·사무실의 상호명과 층·호수 확인', '입구 설치 가능 여부와 수령 담당자 확인', '개업·이전에 맞는 짧은 축하 문구 선택'],
    families: ['congrats'], heading: '개업·이전 축하화환 비교', cta: '축하화환 상품 확인'
  },
  school: {
    intro: '졸업생에게 직접 건넬 꽃은 이동과 사진촬영을 고려해 고르세요.',
    decision: ['휴대할 크기와 원하는 색감 선택', '캠퍼스·행사 건물·만날 장소를 구분', '졸업식 시작시간과 실제 수령시간을 따로 확인'],
    families: ['bouquet'], heading: '졸업생에게 건네는 꽃다발', cta: '졸업 꽃다발 상품 확인'
  },
  event: {
    intro: '오래 함께한 사람의 결혼 소식과 정성껏 준비한 기쁜 행사에 축하를 보태보세요. 직접 건넬 꽃다발·꽃바구니와 행사장에 보낼 축하화환을 살펴볼 수 있습니다.',
    decision: ['직접 건넬 꽃 선물과 행사장에 보낼 화환 비교', '받는 분의 취향과 준비한 예산으로 사진 선택', '주최 측의 꽃 반입 조건과 전달 일정 상담'],
    families: ['bouquet', 'congrats', 'basket'], heading: '축하할 날의 꽃다발·화환·바구니', cta: '축하 꽃 상품 보기'
  },
  gift: {
    intro: '만나서 건넬 때는 꽃다발, 한곳에 두고 감상할 때는 꽃바구니를 비교해 보세요. 병문안은 병동의 생화 반입 가능 여부를 먼저 확인해야 합니다.',
    decision: ['꽃다발의 휴대성과 꽃바구니의 진열 용도 비교', '받는 분의 색감 취향과 보관할 공간 고려', '집·사무실·병동의 정확한 수령 지점 확인'],
    families: ['bouquet', 'basket'], heading: '기념일·약속·병문안 꽃선물', cta: '꽃선물 상품 확인'
  },
  order: {
    intro: '전하고 싶은 마음은 정했는데 상품 선택이 고민되시나요? 선물할 날과 예산을 들려주시면 꽃다발·꽃바구니·화환을 함께 살펴보며 상담할 수 있습니다.',
    decision: ['직접 건넬 선물과 축하·조의용 화환 중 선택', '전하고 싶은 짧은 인사와 상품 예산 준비', '전달 장소·희망 일정·최종금액 함께 상담'],
    families: ['bouquet', 'basket', 'funeral', 'congrats'], heading: '목적에 맞는 상품부터 선택', cta: '꽃다발 상품 확인'
  }
};
export function hubProducts(category, products, limit = 3) {
  const families = hubGuides[category]?.families || [];
  const first = families.map(family => products.find(p => p.family === family)).filter(Boolean);
  const rest = families.flatMap(family => products.filter(p => p.family === family && !first.includes(p)));
  return [...first, ...rest].slice(0, limit);
}

/** Display copy follows the current frozen Catalog and Business Truth. */
export function hubGuide(category, products, site) {
  const guide=hubGuides[category];
  if (!guide) throw new Error('Unknown hub category: '+category);
  const selected=hubProducts(category,products,category==='school'?2:guide.families.length);
  const prices=selected.map(p=>`${p.name} ${p.price.toLocaleString('ko-KR')}원`).join(', ');
  const extra=category==='order'
    ? ` 온라인 ${site.onlineOrderHours} 접수하며 희망 전달 일정은 상담할 수 있습니다.`
    : prices ? ` 상품 사진과 기본가격을 아래에서 함께 살펴보세요.` : '';
  return {...guide,intro:guide.intro+extra};
}
