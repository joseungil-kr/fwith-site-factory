import { existsSync } from 'node:fs';

const siteUrl = import.meta.env.SITE_URL || 'https://yongin.fwith.kr';
const indexableFlag = import.meta.env.SITE_INDEXABLE;
const productionMarker = existsSync('production-indexing.enabled');
const indexable =
  indexableFlag === 'true' ||
  (indexableFlag !== 'false' && productionMarker);

export const siteConfig = {
  siteKey: 'yongin-flower-v2',
  brandKey: 'flower-fwith',
  businessTruthKey: 'flower-fwith-v1',
  brandBase: '꽃이랑',
  brand: '꽃이랑 용인',
  region: '용인',
  industry: '꽃배달·꽃집',
  deploymentMode: 'subdomain',
  rootDomain: 'fwith.kr',
  canonicalDomain: 'yongin.fwith.kr',
  naverSiteVerification: '',
  siteUrl,
  indexable,
  defaultOgImage: '/images/yongin/hero-B-original.png',
  defaultOgImageAlt: '밝은 핑크 플라워 부케를 담은 꽃이랑 용인 꽃배달 대표 이미지',
  description:
    '용인에서 전하는 위로와 축하, 소중한 날의 꽃 선물을 준비하세요. 화환의 사진과 기본가격을 비교하고 받는 분과 예산에 맞춰 편하게 상담할 수 있습니다.',
  operator: {
    label: 'Powered by INTERPIAD',
    href: 'https://interpiad.com',
    rel: 'nofollow',
    email: 'webmaster@interpiad.com',
  },
  nav: [
    { href: '/regions/', label: '지역별', category: 'regions', menuMinChildren: 5 },
    { href: '/funeral/', label: '근조·장례', category: 'funeral', menuMinChildren: 5 },
    { href: '/business/', label: '개업·이전', category: 'business', menuMinChildren: 5 },
    { href: '/school/', label: '졸업·입학', category: 'school', menuMinChildren: 5 },
    { href: '/event/', label: '공연·행사', category: 'event', menuMinChildren: 5 },
    { href: '/gift/', label: '선물·병문안', category: 'gift', menuMinChildren: 5 },
    { href: '/order/', label: '주문 안내', category: 'order', menuMinChildren: 5 },
  ],
} as const;
