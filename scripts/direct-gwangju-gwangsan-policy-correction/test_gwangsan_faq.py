"""Gwangsan four-FAQ count/geometry regression. Policy-correction control fixtures; no browser claim."""
import unittest
from copy import deepcopy
import production_capture as cap
from test_capture_contract import fixture_spec,fixture_page,fixture_metrics,REVISION
class GwangsanFourFAQ(unittest.TestCase):
 def test_exact_four_questions_and_answers_accept(self):
  p=fixture_page(cap.ARTICLE);s=fixture_spec();m=fixture_metrics(cap.ARTICLE)
  self.assertEqual(len(s['faqs']),4);self.assertEqual(len(p['faqIds']),4)
  self.assertEqual(cap.inspect_metrics(m,p,s,390,REVISION),[])
 def test_four_faqs_and_seven_images_remain_exact_at_all_twelve_views(self):
  for route in cap.ROUTES:
   for width in cap.WIDTHS:
    p=fixture_page(route);s=fixture_spec();m=fixture_metrics(route,width)
    self.assertEqual(len(p['faqIds']),4 if route==cap.ARTICLE else 0)
    self.assertEqual(len(m['images']),7 if route==cap.ARTICLE else 3 if route=='/' else 0)
    self.assertEqual(cap.inspect_metrics(m,p,s,width,REVISION),[])
 def test_counts_other_than_four_rejected(self):
  for count in (0,1,2,3,5,True,None):
   for key in ['faqQuestionCount','faqAnswerCount']:
    m=fixture_metrics(cap.ARTICLE);m[key]=count
    self.assertIn('Exact FAQ question and answer node counts mismatch',cap.inspect_metrics(m,fixture_page(cap.ARTICLE),fixture_spec(),390,REVISION))
 def test_fourth_question_and_answer_visibility_and_text_required(self):
  for key,value in [('questionVisible',False),('answerVisible',False),('collapsed',True),('visible',False),('question','Changed'),('answer','Changed')]:
   m=fixture_metrics(cap.ARTICLE);m['faq'][3][key]=value
   self.assertTrue(cap.inspect_metrics(m,fixture_page(cap.ARTICLE),fixture_spec(),390,REVISION))
 def test_no_faq_on_other_routes(self):
  for route in ('/','/regions/','/404.html'):
   m=fixture_metrics(route);m['faqQuestionCount']=1
   self.assertIn('Exact FAQ question and answer node counts mismatch',cap.inspect_metrics(m,fixture_page(route),fixture_spec(),390,REVISION))
if __name__=='__main__':unittest.main()
