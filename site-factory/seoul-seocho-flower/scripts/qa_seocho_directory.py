"""Exact N2 Seocho directory layout; preserves generic eligible-directory spacing semantics."""
import json,os
from pathlib import Path
from qa_seocho import Surface,read,norm,within,hidden

def inspect(root=Path('.')):
 root=Path(root);data=root/'src/data';pages=read(data/'pages.json');common=read(data/'seocho-copy.json')['common'];doc=Surface((root/'dist/regions/index.html').read_text())
 assert len(pages)==2 and len(common['articleCards'])==2,'Frozen Seocho N2 required'
 cards=doc.cls('page-card');assert len(cards)==2,'Two actual visible purchase cards required'
 for card,approved in zip(cards,common['articleCards']):
  assert card['attrs'].get('href')==approved['href'] and not hidden(card),'Exact visible directory card required'
  assert [norm(n['text']) for n in within(card,'strong')]==[approved['title']],'Card title drift'
  assert [norm(n['text']) for n in within(card,'span')]==[approved['summary']],'Card summary drift'
  assert [norm(n['text']) for n in within(card,'em')]==[approved['ctaLabel']],'Card CTA drift'
 assert doc.where(key='data-shared-flower-banner')==[],'N2 directory banners forbidden'
 assert doc.where(key='data-order-banner')==[],'Unapproved repeated CTA banner forbidden'
 assert len(doc.where(key='data-region-district'))==1,'Single district geography group required'
 assert len(doc.where(key='data-legal-unit'))==10 and len(doc.where(key='data-administrative-unit'))==23,'Full official membership denominator required'
 meta={n['attrs'].get('name'):n['attrs'].get('content') for n in doc.where('meta')}
 assert meta['robots']=='noindex,nofollow,noarchive','Local N2 preview must stay noindex'
 source=(root/'src/pages/[category]/index.astro').read_text()
 assert 'noindex={items.length<3}' in source and 'showBanners={items.length>=3}' in source,'Original threshold must not change to helper capability'
 result={'cards':2,'districts':1,'eligible':False,'bannerKinds':[],'visibleCardsBetweenBanners':[],'orderedCardsPreserved':True,'inlineCtaPositionPreserved':True,'inlineCtaCount':0,'note':'N2 approved grouped layout has no InlineOrderBanner; generic legacy fixtures remain unchanged.'}
 Path(os.environ.get('DIRECTORY_SPACING_REPORT_PATH',str(root/'directory-spacing-qa.json'))).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('SEOCHO DIRECTORY SPACING QA: '+json.dumps(result));return result
