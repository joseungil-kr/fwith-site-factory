/** Decision help stays category-specific; it does not prescribe detail structure. */
/** @type {Record<string, {intro:string, decision:string[], families:string[], heading:string, cta:string}>} */
export const hubGuides = {
  funeral: {
    intro: '고인을 기억하는 마음과 유가족을 향한 위로를 꽃으로 전해 보세요. 실제 사진과 예산을 함께 보며 조의의 뜻에 맞는 근조화환을 상담하실 수 있습니다.',
    decision: ['실제 상품 사진과 전체 예산으로 선택', '개인과 가족, 동료들의 조의에 맞는 인사', '유가족의 수령 의사에 맞춘 전달 상담'],
    families: ['funeral'], heading: '조의를 전하는 근조화환', cta: '근조화환 상품 확인'
  },
  business: {
    intro: '새 가게와 일터의 시작에 좋은 만남이 이어지기를 응원해 보세요. 개업식의 축하와 이전 후 방문에 어울리는 꽃을 함께 고르실 수 있습니다.',
    decision: ['매장 개업식과 사무실 이전의 축하꽃', '받는 곳의 공간에 맞춘 실제 규격 상담', '새 출발에 힘이 될 응원의 인사'],
    families: ['congrats'], heading: '개업·이전 축하화환 비교', cta: '축하화환 상품 확인'
  },
  school: {
    intro: '오랫동안 노력한 졸업생의 환한 미소에 꽃을 더해 보세요. 함께 찍을 사진과 이후의 약속을 떠올리며 색감과 포장을 상담하실 수 있습니다.',
    decision: ['주인공의 취향에 맞는 사진 속 색감', '촬영과 이동에 어울릴 규격·포장 상담', '함께 꽃을 건넬 순간에 맞춘 일정 상담'],
    families: ['bouquet'], heading: '졸업생에게 건네는 꽃다발', cta: '졸업 꽃다발 상품 확인'
  },
  event: {
    intro: '두 분의 앞날을 축복하는 예식, 무대를 마친 분께 보내는 박수에 꽃을 더해 보세요. 손에 건넬 꽃과 행사장의 축하화환을 준비할 장면에 맞춰 고르실 수 있습니다.',
    decision: ['직접 건네는 꽃다발과 행사장 축하화환', '출연자와 주인공의 취향을 담은 꽃선물', '행사 담당자의 수령 조건에 맞춘 일정 상담'],
    families: ['bouquet', 'congrats', 'basket'], heading: '공연 전달용과 행사 설치용 비교', cta: '공연 꽃다발 상품 확인'
  },
  gift: {
    intro: '생일의 설렘과 평소 전하지 못한 고마움을 꽃으로 나누어 보세요. 직접 만나 건네는 꽃다발과 곁에 두고 감상할 바구니를 받는 분의 취향에 맞춰 비교하실 수 있습니다.',
    decision: ['만나서 건넬 다발과 곁에서 감상할 바구니', '좋아하는 색과 감상할 자리에 맞춘 선물', '받는 분의 일정에 맞춰 전하는 감사'],
    families: ['bouquet', 'basket'], heading: '기념일·약속·병문안 꽃선물', cta: '꽃선물 상품 확인'
  },
  order: {
    intro: '어떤 꽃을 고를지 고민되신다면 받는 분과 선물할 날부터 이야기해 주세요. 전하고 싶은 마음과 예산에 맞춰 상품을 함께 고르실 수 있습니다.',
    decision: ['사진과 예산으로 고르는 꽃다발·바구니·화환', '좋아하는 색과 형태를 편하게 상담', '가능한 일정과 배송비를 포함한 금액 상담'],
    families: ['bouquet', 'basket', 'funeral', 'congrats'], heading: '목적에 맞는 상품부터 선택', cta: '꽃다발 상품 확인'
  }
};
export function hubProducts(category, products, limit = 3) {
  const families = hubGuides[category]?.families || [];
  const first = families.map(family => products.find(p => p.family === family)).filter(Boolean);
  const rest = families.flatMap(family => products.filter(p => p.family === family && !first.includes(p)));
  return [...first, ...rest].slice(0, limit);
}
