/** Decision help stays category-specific; it does not prescribe detail structure. */
/** @type {Record<string, {intro:string, decision:string[], families:string[], heading:string, cta:string}>} */
export const hubGuides = {
  funeral: {
    intro: '좋은 기억으로 남은 인연을 떠올리며 유가족께 위로의 마음을 전해 보세요. 근조화환 사진의 꽃 배치와 상품 기본가격을 비교하며 조문에 어울릴 꽃을 고르실 수 있습니다.',
    decision: ['흰 꽃과 노란 꽃의 배치를 사진에서 살펴보세요', '개인과 모임의 예산에 맞는 상품을 상담하세요', '빈소와 발인 일정에 맞춰 전할 시간을 함께 정해 보세요'],
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
    intro: '결혼하는 두 분이 오래도록 서로의 기쁨이 되기를 바라는 마음, 축하화환에 담아 전해 보세요. 부천의 예식장으로 보낼 꽃을 사진의 색감과 준비하신 예산에 맞춰 살펴보실 수 있습니다.',
    decision: ['분홍빛과 노란빛 꽃 사진에서 마음에 드는 느낌을 골라 보세요', '친구와 가족의 축복을 담을 인사를 상담하세요', '화환 수령 의사와 예식장 반입 조건에 맞는 전달을 준비하세요'],
    families: ['congrats'], heading: '결혼식 축하화환 상품 비교', cta: '축하화환 상품 확인'
  },
  gift: {
    intro: '만나서 건넬 때는 꽃다발, 한곳에 두고 감상할 때는 꽃바구니를 비교해 보세요. 병문안은 병동의 생화 반입 가능 여부를 먼저 확인해야 합니다.',
    decision: ['꽃다발의 휴대성과 꽃바구니의 진열 용도 비교', '받는 분의 색감 취향과 보관할 공간 고려', '집·사무실·병동의 정확한 수령 지점 확인'],
    families: ['bouquet', 'basket'], heading: '기념일·약속·병문안 꽃선물', cta: '꽃선물 상품 확인'
  },
  order: {
    intro: '꽃선물을 처음 고르는 날에도 받는 분과 어떤 시간을 축하하고 싶은지부터 이야기해 주세요. 손에 건넬 꽃다발, 곁에 두고 볼 꽃바구니, 행사장의 화환을 목적과 예산에 맞춰 상담하실 수 있습니다.',
    decision: ['받는 분께 건넬 장면을 떠올리며 꽃의 형태를 살펴보세요', '사진과 상품 기본가격으로 선물 예산을 정해 보세요', '배송비를 포함한 금액과 가능한 일정을 편하게 상담하세요'],
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
    ? ` 온라인 주문은 ${site.onlineOrderHours} 접수하며, 가능한 전달일정은 상담으로 안내합니다.`
    : prices ? ` 현재 상품: ${prices}.` : '';
  return {...guide,intro:guide.intro+extra};
}
