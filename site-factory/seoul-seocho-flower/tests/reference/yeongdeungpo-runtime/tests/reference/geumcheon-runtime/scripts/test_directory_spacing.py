"""Negative rendered regressions for the separately scoped directory amendment."""
import unittest,math
from qa_directory_spacing import validate,inspect

def fixture(counts,eligible=True,at=None,robots=None):
 groups=[];n=0
 for i,count in enumerate(counts):
  cards=[]
  for _ in range(count):n+=1;cards.append({'href':f'/card-{n}/','unit':f'unit-{n}','text':[f'Card {n}',f'Summary {n}','주문 안내 보기 →']})
  groups.append({'id':f'g{i}','key':f'g{i}','heading':f'Group {i}','cards':cards})
 contract={'eligible':eligible,'groups':groups};at=math.ceil(n/2) if at is None else at;seen=0
 banner=lambda kind:f'<figure data-shared-flower-banner="{kind}"></figure>'
 html=f'<meta name="robots" content="{robots or ("index,follow" if eligible else "noindex,follow")}"><main>'+(banner('message') if eligible else '')
 for i,g in enumerate(groups):
  html+=f'<section id="{g["id"]}" data-region-district="{g["key"]}"><h2>{g["heading"]}</h2><div class="card-grid big">'
  for c in g['cards']:
   html+=f'<a class="page-card" href="{c["href"]}" data-region-unit="{c["unit"]}"><strong>{c["text"][0]}</strong><span>{c["text"][1]}</span><em>{c["text"][2]}</em></a>';seen+=1
   if eligible and seen==at:html+=banner('budget')
  html+='</div>'
  if i==(len(groups)-1)//2:html+='<aside data-order-banner="inline"></aside>'
  html+='<details><summary>Existing collapsed details</summary></details></section>'
 html+=(banner('consultation') if eligible else '')+'</main>';return html,contract
class SpacingTests(unittest.TestCase):
 def test_actual_built_directory(self):inspect()
 def test_two_three_cards_and_multiple_districts(self):
  for counts in [[2],[1,1],[3],[44],[3,4],[4,3],[1,1,1],[0,1,0,2]]:html,c=fixture(counts);validate(html,c)
 def test_noindex_one_two_three_cards_keep_zero_banners(self):
  for n in [1,2,3]:html,c=fixture([n],False);self.assertEqual(validate(html,c)['bannerKinds'],[])
 def test_eligible_one_card_fails_explicitly(self):
  for n in [1]:html,c=fixture([n]);self.assertRaisesRegex(AssertionError,'fewer than two',validate,html,c)
 def test_old_end_of_district_banner_placement_is_rejected(self):
  for n in [3,44]:html,c=fixture([n],at=n);self.assertRaisesRegex(AssertionError,'visible actual card',validate,html,c)
 def test_reordered_or_missing_card_is_rejected(self):
  html,c=fixture([3]);self.assertRaisesRegex(AssertionError,'Ordered source cards',validate,html.replace('/card-1/','/card-9/'),c)
 def test_duplicate_or_missing_banner_is_rejected(self):
  html,c=fixture([3]);self.assertRaisesRegex(AssertionError,'Banner set',validate,html.replace('data-shared-flower-banner="budget"','data-shared-flower-banner="consultation"'),c)
 def test_noindex_marketing_is_rejected(self):
  html,c=fixture([2],False);self.assertRaisesRegex(AssertionError,'Banner set',validate,html+'<figure data-shared-flower-banner="budget"></figure>',c)
 def test_new_noindex_or_cta_drift_is_rejected(self):
  html,c=fixture([3]);self.assertRaisesRegex(AssertionError,'noindex eligibility',validate,html.replace('index,follow','noindex,follow'),c)
  self.assertRaisesRegex(AssertionError,'InlineOrderBanner',validate,html.replace('data-order-banner="inline"','data-order-banner="changed"'),c)
if __name__=='__main__':unittest.main()
