/** Decision help stays category-specific; it does not prescribe detail structure. */
/** @type {Record<string, {intro:string, decision:string[], families:string[], heading:string, cta:string}>} */
export const hubGuides = {
  regions: {intro:'수원에서 전할 축하와 고마움, 위로의 꽃을 지역별로 살펴보세요. 소중한 분과 함께할 순간에 맞춰 꽃 선물을 상담하실 수 있습니다.',decision:['졸업·공연·기념일의 꽃 선물 살펴보기', '개업과 행사에 어울릴 축하화환 고르기', '조의를 담을 근조화환 상담하기'],families:['bouquet','basket','congrats','funeral'],heading:'마음을 전하는 꽃 상품',cta:'꽃 상품 확인'},
  funeral: {
    intro: '고인을 추모하고 유가족의 슬픔을 함께하는 마음을 근조화환에 담아 보세요. 개인과 모임의 예산에 맞춰 정중한 조의의 꽃을 상담하실 수 있습니다.',
    decision: ['개인 또는 모임이 함께 보낼 수량과 예산 정하기', '상품사진을 보며 현재 구성과 실제 규격 상담하기', '부고와 유가족의 수령 안내에 맞춰 희망시간 상담하기'],
    families: ['funeral'], heading: '조의를 전하는 근조화환', cta: '근조화환 상품 확인'
  },
  business: {
    intro: '새 가게의 문을 열거나 새로운 공간으로 나아가는 분께 응원의 꽃을 전해 보세요. 준비해 온 시간이 좋은 만남으로 이어지기를 바라는 축하를 담으실 수 있습니다.',
    decision: ['개업일에 보낼 화환과 방문하며 건넬 선물 선택하기', '매장·사무실의 놓을 공간에 맞는 실제 규격 상담하기', '회사·모임 공동 선물의 수량과 총예산 정하기'],
    families: ['congrats'], heading: '개업·이전 축하화환 비교', cta: '축하화환 상품 확인'
  },
  school: {
    intro: '졸업까지 애쓴 시간과 앞으로의 새로운 걸음을 꽃으로 축하해 보세요. 가족과 친구가 환하게 웃는 사진에 함께할 꽃다발을 만나보실 수 있습니다.',
    decision: ['받는 분이 좋아할 사진의 색감과 현재 구성 살펴보기', '한 사람에게 전할 꽃과 여러 사람의 선물 수량 정하기', '촬영 뒤 이동에 맞는 규격과 포장 상담하기'],
    families: ['bouquet'], heading: '졸업생에게 건네는 꽃다발', cta: '졸업 꽃다발 상품 확인'
  },
  event: {
    intro: '무대를 마친 분의 수고를 기뻐하고 새로운 성과를 선보이는 기업을 응원하는 꽃입니다. 손에 건넬 꽃과 행사에 함께할 꽃을 선물할 장면에 맞춰 골라 보세요.',
    decision: ['출연자 꽃다발과 행사 축하화환의 전달 장면 떠올리기', '여러 출연자에게 각각 전할 수량과 전체 예산 정하기', '주최 측의 수령·설치 안내에 맞는 규격과 시간 상담하기'],
    families: ['bouquet', 'congrats', 'basket'], heading: '공연 전달용과 행사 설치용 비교', cta: '공연 꽃다발 상품 확인'
  },
  gift: {
    intro: '기념일의 설렘과 평소의 고마움을 꽃으로 이야기해 보세요. 받는 분이 좋아할 색감과 함께할 시간을 떠올리며 꽃다발과 바구니를 살펴보실 수 있습니다.',
    decision: ['직접 건넬 꽃다발과 자리에서 감상할 바구니 비교하기', '상품사진에서 마음에 드는 색감과 현재 구성 상담하기', '만난 뒤의 이동이나 감상할 장소에 맞는 규격 살펴보기'],
    families: ['bouquet', 'basket'], heading: '기념일·약속·병문안 꽃선물', cta: '꽃선물 상품 확인'
  },
  order: {
    intro: '누구에게 어떤 마음을 전하고 싶은지부터 편하게 이야기해 주세요. 꽃이랑에서 상품과 예산, 가능한 전달 일정을 상담하실 수 있습니다.',
    decision: ['선물할 장면에 어울릴 꽃다발·바구니·화환 선택하기', '수량과 전체 예산에 맞춰 현재 상품 구성 상담하기', '희망시간과 추가 배송비·선택사항을 포함한 최종금액 상담하기'],
    families: ['bouquet', 'basket', 'funeral', 'congrats'], heading: '목적에 맞는 상품부터 선택', cta: '꽃다발 상품 확인'
  }
};
export function hubProducts(category, products, limit = 3) {
  const families = hubGuides[category]?.families || [];
  const first = families.map(family => products.find(p => p.family === family)).filter(Boolean);
  const rest = families.flatMap(family => products.filter(p => p.family === family && !first.includes(p)));
  return [...first, ...rest].slice(0, limit);
}

