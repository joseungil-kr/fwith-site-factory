"""Mutate actual built HTML/binary files; every case must fail the static audit."""
from pathlib import Path
import json,re,tempfile,shutil,unittest
from qa_haenam import ROOT,verify,COPY,D,U
class OutputRegression(unittest.TestCase):
 def test_positive(self):self.assertGreaterEqual(verify()['checks'],270)
 def mutate(self,operation):
  with tempfile.TemporaryDirectory(prefix='haenam-output-')as t:
   d=Path(t)/'dist';shutil.copytree(ROOT/'dist',d);operation(d)
   with self.assertRaises((AssertionError,ValueError,KeyError,TypeError,AttributeError)):verify(d)
 def html(self,old,new,file='index.html'):
  def mutate(d):
   p=d/file;s=p.read_text();self.assertIn(old,s);p.write_text(s.replace(old,new,1))
  self.mutate(mutate)

def html_case(name,old,new,file='index.html'):
 def run(self):self.html(old,new,file)
 setattr(OutputRegression,'test_'+name,run)
for name,old,new in [
 ('timing_19_merged','평일 19시 이후','평일 21시 이후'),
 ('timing_21_merged','21시 이후 주문','19시 이후 주문'),
 ('hospital_card_aria',U['productGroupAriaLabel'],'해남종합병원장례식장 추천 주문상품'),
 ('hospital_meta_hidden',D['page']['description'],'해남종합병원장례식장 3단 화환 주문'),
 ('hospital_order_cta',D['products'][0]['ctaLabel'],'해남종합병원장례식장 주문'),
 ('product_schema','</main>','<div itemscope itemtype="https://schema.org/Product"></div></main>'),
 ('photo_link_wrong','class="product-photo-link" href="https://fwith.co.kr/shop/item.php?it_id=B201"','class="product-photo-link" href="https://fwith.co.kr/"'),
 ('invented_total_element','</main>','<p class="product-reference">최종금액 59,000원</p></main>'),
 ('missing_faq',COPY['faq'][0]['question'],''),
 ('missing_third_faq',COPY['faq'][2]['question'],''),('missing_refund_prohibition','제작 완료된 꽃 상품은 교환·환불이 불가하다는 내용과,','제작 이후에도 환불할 수 있습니다.'),('missing_after_dispatch_clause','출고 후 취소 시 배송비를 제외한 금액을 환불한다는 내용이 함께 있습니다.','출고 후에는 환불하지 않습니다.'),('wrong_manuscript_sha',COPY['sourceSHA256']['draft-home.ko.md'],'0'*64),('leaked_goheung','</main>','고흥</main>'),('faq_answer_changed',COPY['faq'][1]['answer'].split('\n\n')[0],'확인하지 않은 입금 약속'),
 ('wrong_sku','it_id=B201','it_id=B203'),('cta_to_home','https://fwith.co.kr/shop/item.php?it_id=B203','https://fwith.co.kr/'),
 ('wrong_phone','tel:18440644','tel:18440645'),('wrong_delivery_fee',U['amountNotice'],'해남군 추가배송비 0원'),
 ('wrong_amount',D['products'][0]['shippingLabel'],'최종금액 59,000원'),('product_alt',D['products'][0]['photoAlt'],'꽃'),
 ('banner_alt',D['sharedBanners'][0]['alt'],'배너'),('banner_phone_removed','전화 1844-0644.',''),
 ('banner_phone_duplicate',D['sharedBanners'][1]['alt'],D['sharedBanners'][1]['alt']+' 전화 1844-0644.'),
 ('banner_phone_wrong',D['sharedBanners'][2]['alt'],D['sharedBanners'][2]['alt'].replace('0644','0645')),
 ('banner_filename','flower-message.webp','flower-other.webp'),('banner_variant','data-shared-flower-banner="budget"','data-shared-flower-banner="other"'),
 ('removed_caption','</figure>','<figcaption>꽃이랑 공통 안내 이미지 · 실제 판매상품 사진이 아닌 AI 생성 이미지입니다.</figcaption></figure>'),
 ('extra_h1','</h1>','</h1><h1>제목</h1>'),('heading_skip','<h2','<h4'),('duplicate_id','id="products-cost"','id="main-content"'),
 ('missing_anchor','href="#delivery-cost"','href="#missing"'),('facility_route','href="#products-cost"','href="/facility/"'),
 ('alter_title',D['page']['title'],'변경된 제목'),('alter_description',D['page']['description'],'누락 설명'),
 ('robots_promoted','noindex,nofollow','index,follow'),('canonical_claim','</head>','<link rel="canonical" href="https://haenam.fwith.kr/"/></head>'),
 ('og_claim','</head>','<meta property="og:url" content="https://haenam.fwith.kr/"/></head>'),
 ('twitter_claim','</head>','<meta name="twitter:image" content="https://haenam.fwith.kr/images/products/B201.jpg"/></head>'),
 ('inline_hidden_faq','id="questions"','id="questions" hidden="hidden"'),('inert_faq','id="questions"','id="questions" inert'),('aria_hidden_faq','id="questions"','id="questions" aria-hidden="true"'),
 ('inline_css_hidden','id="questions"','id="questions" style="display:none"'),('folded_faq','id="questions"','id="questions"><details><summary>질문</summary></details><section'),
 ('extra_text','</main>','승인되지 않은 본문</main>'),('nested_paragraph','<p data-copy-key="intro.0">','<p data-copy-key="intro.0"><div>'),
 ('phone_link_http','tel:18440644','http://unsafe.test/'),('missing_source',D['sourceArea']['items'][0]['label'],''),
 ('wrong_aria',U['closingAction']['ariaLabel'],'잘못된 목적'),('extra_link','</main>','<a href="/">더 보기</a></main>'),
 ('wrong_image_size','width="1774"','width="1700"'),('banner_loading','loading="lazy"','loading="eager"')]:html_case(name,old,new)
for name,old,new in [('404_robots','noindex,nofollow','index,follow'),('404_missing_body',D['notFoundCopyPlan']['body'],''),('404_marketing','</main>','<img src="/images/products/B201.jpg" alt="상품"/></main>'),('404_bad_home','href="/"','href="/wrong/"')]:html_case(name,old,new,'404.html')
for file in ['robots.txt','images/products/B201.jpg','images/products/B203.jpg','images/products/B205.jpg','images/products/B060.jpg','images/shared-banners/flower-message.webp','images/shared-banners/flower-budget.webp','images/shared-banners/flower-consultation.webp']:
 def run(self,file=file):self.mutate(lambda d:(d/file).write_bytes((d/file).read_bytes()+b'x'))
 setattr(OutputRegression,'test_changed_'+file.replace('/','_').replace('.','_'),run)
for file in ['sitemap.xml','12345678901234567890123456789012.txt','facility/index.html']:
 def run(self,file=file):
  def op(d):p=d/file;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('unapproved')
  self.mutate(op)
 setattr(OutputRegression,'test_extra_'+file.replace('/','_').replace('.','_'),run)
def hidden_css(self):
 def op(d):
  p=next((d/'_astro').glob('*.css'));p.write_text(p.read_text()+'#questions{display:none}')
 self.mutate(op)
OutputRegression.test_hidden_css=hidden_css
# Region-specific regression mutations preserve the accepted wording and fee separation.
for name,old,new in [
 ('county_fee_replaced','해남군이 포함된 10,000원 항목','해남군이 포함된 15,000원 항목'),
 ('town_fee_replaced','해남군 문내면·송지면을 따로 적은 15,000원 항목','해남군 문내면·송지면을 따로 적은 25,000원 항목'),
 ('sum_invented',U['amountNotice'],'해남군 배송비는 25,000원입니다.'),
 ('county_specific_caveat_removed','15,000원이 해남군 모든 읍·면의 일괄 배송비라는 뜻은 아닙니다.',''),
 ('hospitals_collapsed','옥천면 해남로 597','해남읍 해남로 45'),
 ('facility_phone_replaced','061-533-4444','1844-0644'),
 ('facility_acceptance_invented','그 자체가 해당 빈소의 화환 반입 허용을 뜻하지는 않습니다.','해당 빈소는 3단화환을 허용합니다.'),
 ('neighbor_restriction_inserted','</main>','<p>마량장례식장 제한</p></main>'),
 ('internal_hold_leak','</main>','<p>HOLD_6</p></main>')]:html_case(name,old,new)
def nav_width_reduced(self):
 def op(d):
  p=next((d/'_astro').glob('*.css'));s=p.read_text();self.assertIn('min-width:44px',s);p.write_text(s.replace('min-width:44px','min-width:39px'))
 self.mutate(op)
OutputRegression.test_nav_width_reduced=nav_width_reduced
def nav_wrap_removed(self):
 def op(d):
  p=next((d/'_astro').glob('*.css'));s=p.read_text();p.write_text(s.replace('flex-wrap:wrap;min-width:0','flex-wrap:nowrap;min-width:0'))
 self.mutate(op)
OutputRegression.test_nav_wrap_removed=nav_wrap_removed
if __name__=='__main__':unittest.main(verbosity=2)
