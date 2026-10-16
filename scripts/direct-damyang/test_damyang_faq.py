"""Damyang four-FAQ count/geometry regression. Pure fixtures; no browser claim."""
import unittest
from copy import deepcopy
import production_capture as cap
from test_capture_contract import fixture_spec,fixture_page,fixture_metrics,REVISION
class DamyangFourFAQ(unittest.TestCase):
 def test_exact_four_questions_and_answers_accept(self):
  p=fixture_page('/');s=fixture_spec();m=fixture_metrics('/')
  self.assertEqual(len(s['faqs']),4);self.assertEqual(len(p['faqIds']),4)
  self.assertEqual(cap.inspect_metrics(m,p,s,390,REVISION),[])
 def test_counts_other_than_four_rejected(self):
  for count in (0,1,2,3,5,True,None):
   for key in ['faqQuestionCount','faqAnswerCount']:
    m=fixture_metrics('/');m[key]=count
    self.assertIn('Exact FAQ question and answer node counts mismatch',cap.inspect_metrics(m,fixture_page('/'),fixture_spec(),390,REVISION))
 def test_fourth_question_and_answer_visibility_and_text_required(self):
  for key,value in [('questionVisible',False),('answerVisible',False),('collapsed',True),('visible',False),('question','Changed'),('answer','Changed')]:
   m=fixture_metrics('/');m['faq'][3][key]=value
   self.assertTrue(cap.inspect_metrics(m,fixture_page('/'),fixture_spec(),390,REVISION))
 def test_no_faq_on_other_routes(self):
  for route in ('/404.html',):
   m=fixture_metrics(route);m['faqQuestionCount']=1
   self.assertIn('Exact FAQ question and answer node counts mismatch',cap.inspect_metrics(m,fixture_page(route),fixture_spec(),390,REVISION))
if __name__=='__main__':unittest.main()
