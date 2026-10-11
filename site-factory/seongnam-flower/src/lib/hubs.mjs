import {productFamilies} from './catalog.mjs';
/** Decision help stays category-specific; it does not prescribe detail structure. */
/** @type {Record<string, {intro:string, decision:string[], families:string[], heading:string, cta:string}>} */
export const hubGuides = {
  funeral: {
    intro: '함께한 인연을 기억하며 유가족께 조용한 위로를 전해 보세요. 근조화환의 사진과 상품 기본가격을 살펴보고 마음에 맞는 꽃을 상담하실 수 있습니다.',
    decision: ['사진의 꽃 배치와 예산을 함께 비교해 보세요', '개인과 모임의 조의를 담아 전하실 수 있습니다', '빈소와 발인 일정에 맞는 전달시간을 상담하세요'],
    families: ['funeral'], heading: '조의를 전하는 근조화환', cta: '근조화환 상품 확인'
  },
  business: {
    intro: '새 간판을 달고 문을 여는 가게와 새로운 사무실의 출발을 응원해 보세요. 받는 분의 취향과 준비하신 예산을 떠올리며 축하화환을 고르실 수 있습니다.',
    decision: ['첫 출근과 개업 행사를 응원하는 꽃을 살펴보세요', '매장 분위기에 어울릴 사진과 실제 규격을 상담하세요', '새로운 시작을 축하하는 인사를 리본에 담아 보세요'],
    families: ['congrats'], heading: '개업·이전 축하화환 비교', cta: '축하화환 상품 확인'
  },
  school: {
    intro: '졸업생에게 직접 건넬 꽃은 이동과 사진촬영을 고려해 고르세요. 꽃다발 소소한 행복은 50,000원, 블루톤 시즌플라워는 55,000원입니다.',
    decision: ['휴대할 크기와 원하는 색감 선택', '캠퍼스·행사 건물·만날 장소를 구분', '졸업식 시작시간과 실제 수령시간을 따로 확인'],
    families: ['bouquet'], heading: '졸업생에게 건네는 꽃다발', cta: '졸업 꽃다발 상품 확인'
  },
  event: {
    intro: '출연자에게 건네는 꽃다발과 행사장에 설치하는 축하화환은 준비할 정보가 다릅니다. 꽃다발은 50,000원부터, 축하 기본 3단 화환은 59,000원입니다.',
    decision: ['직접 전달할 꽃다발인지 설치할 화환인지 선택', '공연명·홀 또는 전시장·받는 담당자 확인', '꽃 반입·설치 가능 여부와 전달시간을 주최 측에 확인'],
    families: ['bouquet', 'congrats', 'basket'], heading: '공연 전달용과 행사 설치용 비교', cta: '공연 꽃다발 상품 확인'
  },
  gift: {
    intro: '만나서 건넬 때는 꽃다발, 한곳에 두고 감상할 때는 꽃바구니를 비교해 보세요. 병문안은 병동의 생화 반입 가능 여부를 먼저 확인해야 합니다.',
    decision: ['꽃다발의 휴대성과 꽃바구니의 진열 용도 비교', '받는 분의 색감 취향과 보관할 공간 고려', '집·사무실·병동의 정확한 수령 지점 확인'],
    families: ['bouquet', 'basket'], heading: '기념일·약속·병문안 꽃선물', cta: '꽃선물 상품 확인'
  },
  order: {
    intro: '어떤 꽃을 골라야 할지 고민될 때에는 전하고 싶은 마음부터 이야기해 주세요. 사진과 상품 기본가격을 살펴보며 예산과 가능한 전달일정을 상담하실 수 있습니다.',
    decision: ['축하와 위로에 어울리는 상품사진을 비교해 보세요', '선물 예산에 배송비를 포함한 금액을 상담하세요', '희망하는 날짜와 시간에 맞춰 가능한 일정을 물어보세요'],
    families: ['funeral', 'congrats'], heading: '목적에 맞는 화환부터 선택', cta: '화환 상품 확인'
  }
};
/** A wreath-only event collection must not promise unrelated gift families. */
export function hubGuide(category, pages = []) {
  const children = pages.filter(page => page.category === category);
  if (category === 'event' && children.length > 0 && children.every(page => {
    const families = productFamilies(page);
    return families.length === 1 && families[0] === 'congrats';
  })) return {
    intro: '결혼하는 두 분의 앞날과 함께 애쓴 동료의 결실을 축하해 보세요. 예식과 기업행사의 주인공에게 보낼 축하화환을 실제 사진과 예산에 맞춰 고르실 수 있습니다.',
    decision: ['주인공에게 전할 축복과 응원을 떠올려 보세요', '사진의 꽃 배치와 준비하신 예산으로 선택하세요', '행사에서 화환을 받을 수 있는 시간과 장소를 함께 상담하세요'],
    families: ['congrats'], heading: '기쁜 날을 함께하는 축하화환', cta: '행사 축하화환 상품 확인'
  };
  return hubGuides[category];
}
export function hubProducts(category, products, limit = 3, pages = []) {
  const families = hubGuide(category, pages)?.families || [];
  if (families.some(family => !products.some(p => p.family === family))) throw new Error(`Seongnam catalog missing hub family: ${category}`);
  const first = families.map(family => products.find(p => p.family === family)).filter(Boolean);
  const rest = families.flatMap(family => products.filter(p => p.family === family && !first.includes(p)));
  return [...first, ...rest].slice(0, limit);
}
