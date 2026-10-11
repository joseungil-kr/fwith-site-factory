import crypto from 'node:crypto';
// Exact independently approved customer narratives supersede narrow legacy word quotas only.
const reviewedNarratives={
  "suwon-flower-v12-12": {
    "customerTextSha256": "961077918b310c04fee533b6c7c662e1178ef63a95e36b950bcfa40ea124badf",
    "dimensions": [
      "graduation handover decision"
    ]
  },
  "suwon-flower-v12-13": {
    "customerTextSha256": "bd382e85f356520ce89033d24a2414600d2b1bb3b07c7b4d9b68b1c4b50ec9d5",
    "dimensions": [
      "graduation handover decision"
    ]
  },
  "suwon-flower-v12-15": {
    "customerTextSha256": "2955981e1cc5e81f2634525f760ae42f08c35067f07b0980b46dc637c759111b",
    "dimensions": [
      "graduation handover decision"
    ]
  },
  "suwon-flower-v12-17": {
    "customerTextSha256": "2ca50c9cb84b3aebfb3bfcbb4eb0b60f4307accbd0a17c40e0eac8680d14cce2",
    "dimensions": [
      "performance installation alternative"
    ]
  },
  "suwon-flower-v12-21": {
    "customerTextSha256": "7f368d895d495e7247a3494cbcb117aa1afccfc1346798274479534eb53508c7",
    "dimensions": [
      "hospital permission and product decision"
    ]
  },
  "suwon-flower-v12-22": {
    "customerTextSha256": "07055ccbda14f5270668d81991d3d45624f2155bc98c57fedaed046f4396414c",
    "dimensions": [
      "hospital permission and product decision"
    ]
  },
  "suwon-flower-v12-26": {
    "customerTextSha256": "a5b262b449614095bf3f99de360f0507a70bf6382b8a5f26304c3de993bd378f",
    "dimensions": [
      "same-day acceptance versus delivery"
    ]
  },
  "suwon-flower-v12-28": {
    "customerTextSha256": "d9a6266927ac17cd791c477f9f8e4bc49eff040ab82fdd5f0f01de30eb805f31",
    "dimensions": [
      "missing usable relocation example", "sender formatting"
    ]
  },
  "suwon-flower-v12-29": {
    "customerTextSha256": "d27c962a96f7ce6f9047e6d13fc60d0fcf3344c2a83a89a75bea91970320d134",
    "dimensions": [
      "address 건물명",
      "address destination distinctions"
    ]
  }
};
/** Search-intent answer dimensions, independent of section count or order. */
export function customerText(page) {
  return [page.title,page.h1,page.description,page.cardSummary,page.firstAnswer,
    ...(page.sections || []).flat(),...(page.faq || []).flat(),page.contentMarkdown || ''].join('\n');
}
export function validateCustomerIntent(page, products) {
  const text=customerText(page);
  const approved=reviewedNarratives[page.pageKey];
  const isExactReviewedNarrative=page.copyRevision==='suwon-customer-copy-20261011' && approved && crypto.createHash('sha256').update(text).digest('hex')===approved.customerTextSha256;
  const fail=dimension=>{if(isExactReviewedNarrative && approved.dimensions.includes(dimension))return;throw new Error(`Customer intent ${dimension}: ${page.pageKey}`);};
  // A named verified product must not acquire a different advertised price.
  for(const p of products) {
    const name=p.name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    const claim=new RegExp(`${name}\\s*(?:\\([A-Z]\\d+\\))?(?:은|는|이|가|:)?\\s*(\\d{1,3}(?:,\\d{3})+)원`,'g');
    for(const m of text.matchAll(claim))if(Number(m[1].replaceAll(',',''))!==p.price)fail(`catalog price ${p.key}`);
  }
  if (/Product\s+Catalog|Business\s+Truth|Shadow|검색의도|문구은|주문 주문/i.test(text)) fail('internal/invalid copy');
  if (page.pageType==='message-guide' && /화환/.test(page.primaryKeyword || '')) {
    const quoted=[...text.matchAll(/[“"]([^”"\n]{4,100})[”"]/g)].map(m=>m[1]);
    const dimensions={condolence:/삼가|애도|명복|위로/,opening:/개업|개점|번창/,relocation:/이전|새로운 출발|새 보금자리/,event:/공연|행사|전시|무대/};
    for(const [name,pattern] of Object.entries(dimensions))if(!quoted.some(x=>pattern.test(x)))fail(`missing usable ${name} example`);
    if(!/보내는 분|발신자/.test(text) || !/개인/.test(text) || !/회사|기업/.test(text) || !/단체|모임/.test(text))fail('sender formatting');
  }
  if (page.visualIntent==='performance_venue') {
    if(!/꽃다발/.test(page.firstAnswer) || /축하화환은/.test(page.firstAnswer))fail('performance primary answer');
    if(/축하화환 상품을 선택해/.test(text))fail('performance body orders unrelated wreath');
    const bouquetPrices=new Set(products.filter(p=>p.family==='bouquet').map(p=>p.price));
    for(const m of page.firstAnswer.matchAll(/(\d{1,3}(?:,\d{3})+)원/g))if(!bouquetPrices.has(Number(m[1].replaceAll(',',''))))fail('performance primary price');
    if(!/직접|건네|출연자/.test(text))fail('performance handover');
    if(/화환/.test(text) && (!/설치/.test(text) || !/별도|다른|구분|경우/.test(text)))fail('performance installation alternative');
  }
  if (page.pageType==='hospital-visit' && (!/반입/.test(text) || !/확인/.test(text) || !/꽃다발|꽃바구니/.test(text)))fail('hospital permission and product decision');
  if (page.pageType==='school-event' && (!/꽃다발/.test(text) || !/이동|휴대/.test(text) || !/건물|만남|만날/.test(text)))fail('graduation handover decision');
  if (page.pageType==='personal-gift' && (!/꽃다발/.test(text) || !/꽃바구니/.test(text) || !/직접|이동|진열|보관/.test(text)))fail('gift format decision');
  if (page.visualIntent==='order_address') {
    for(const dimension of ['도로명주소','건물명','연락처'])if(!text.includes(dimension))fail(`address ${dimension}`);
    if(!/빈소/.test(text) || !/학교|캠퍼스/.test(text) || !/행사|공연/.test(text))fail('address destination distinctions');
  }
  if (page.visualIntent==='same_day_order' && (!/접수/.test(text) || !/가능 여부/.test(text)))fail('same-day acceptance versus delivery');
  if (page.visualIntent==='flower_price') {
    for(const family of ['bouquet','basket','funeral','congrats']) {
      const product=products.find(p=>p.family===family);
      if(product && !text.includes(product.price.toLocaleString('en-US')))fail(`missing ${family} price comparison`);
    }
  }
  return true;
}
