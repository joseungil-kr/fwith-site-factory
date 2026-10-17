"""No browser: test glyph-bound rejection and natural-scroll capture policy."""
import ast,copy,json,tempfile,unittest
from pathlib import Path
import layout_evidence as L
class GlyphRangeTests(unittest.TestCase):
 def row(self):return {'text':'여수전남병원장례식장','sectionId':'section-2','visible':True,'overflowWrap':'anywhere','whiteSpace':'normal','fontSize':23,'lineHeight':34.5,'contentBox':{'left':18,'right':302},'glyphs':[{'char':c,'rects':[{'left':20,'right':43,'top':100,'bottom':123,'width':23,'height':23}]} for c in '여수전남병원장례식장'],'clips':[]}
 def check(self,r):return L.heading_issues([r],[{'text':'여수전남병원장례식장','sectionId':'section-2'}],320)
 def test_valid_fixture_is_not_browser_evidence(self):self.assertEqual(self.check(self.row()),[])
 def test_card_padding_overflow_even_without_page_overflow_fails(self):
  r=self.row();r['glyphs'][-1]['rects'][0].update(left=290,right=312);self.assertTrue(any('card inner padding' in x for x in self.check(r)))
 def test_glyph_viewport_overflow_fails(self):
  r=self.row();r['glyphs'][-1]['rects'][0]['right']=340;self.assertTrue(any('viewport' in x for x in self.check(r)))
 def test_heading_glyph_wrap_and_readability_mutations_fail(self):
  for key,value in [('visible',False),('overflowWrap','normal'),('whiteSpace','nowrap'),('fontSize',9),('fontSize',float('nan')),('lineHeight',12),('text','wrong'),('sectionId','wrong'),('glyphs',[])]:
   r=self.row();r[key]=value
   with self.subTest(key=key):self.assertTrue(self.check(r))
 def test_clipped_text_fails(self):
  r=self.row();r['clips']=[{'overflowX':'hidden','overflowY':'visible','rect':{'left':18,'right':40,'top':0,'bottom':200}}];self.assertTrue(any('clipped' in x for x in self.check(r)))
 def test_missing_nonrendered_glyph_fails(self):
  r=self.row();r['glyphs'][0]['rects']=[];self.assertTrue(any('no rendered Range' in x for x in self.check(r)))
 def test_empty_routes_require_exact_empty_array(self):self.assertEqual(L.heading_issues([],[],320),[]);self.assertTrue(L.heading_issues(None,[],320))
 def test_new_metric_does_not_remove_old_overflow_guard(self):
  s=(Path(__file__).parent/'production_capture.py').read_text();self.assertIn("metrics['scrollWidth'] > width or metrics['overflow']",s);self.assertIn("record['metrics']['headingGlyphs'] = page.evaluate(HEADING_METRICS_JS)",s)
 def test_no_page_modification_or_hidden_fixed_ui(self):
  s=Path(L.__file__).read_text()
  for bad in ['add_style_tag','add_script_tag','.remove()','style.display','style.visibility','setAttribute(','innerHTML =','outerHTML =','chromium.launch','subprocess']:self.assertNotIn(bad,s)
  self.assertIn('window.scrollTo(0,y)',s);self.assertIn("page.screenshot(path=str(file))",s);self.assertIn('document.elementFromPoint',s);self.assertIn('domUnmodified',s);self.assertIn('menu-open.png',s)
 def test_frozen_heading_denominators_cover_four_routes(self):
  u=json.loads((Path(__file__).parent/'ui-expectations.json').read_text());self.assertEqual([len(p['h2Headings']) for p in u['pages']],[2,0,5,0])
  self.assertIn('createRange()',L.HEADING_METRICS_JS);self.assertIn('getClientRects()',L.HEADING_METRICS_JS)
class FakeScrollPage:
 """Deterministic geometry fixture only. Never a browser or visual QA result."""
 def __init__(self,stalled=False,changed=False,blocked=False,layout_changed=False):
  self.y=0;self.stalled=stalled;self.changed=changed;self.blocked=blocked;self.layout_changed=layout_changed;self.calls=0;self.screens=[]
 def content(self):return 'changed fixture DOM' if self.changed and self.y else 'unchanged fixture DOM'
 def wait_for_timeout(self,ms):pass
 def evaluate(self,expression,args):
  if expression=='(y)=>window.scrollTo(0,y)':
   if not self.stalled:self.y=args
   return
  if expression!=L.READABLE_TARGET_JS:raise AssertionError('Unexpected page evaluation')
  self.calls+=1
  return {'text':'fixture question and answer' if not self.layout_changed or self.calls==1 else 'changed', 'safeTop':100,'safeBottom':90 if self.blocked else 600,'scrollY':self.y,'lines':[{'index':i,'documentTop':top,'top':top-self.y,'bottom':top-self.y+24,'unobscured':100<=top-self.y and top-self.y+24<=600} for i,top in enumerate([650,700,1400])]}
 def screenshot(self,**kwargs):
  if set(kwargs)!={'path'}:raise AssertionError('Screenshots must keep the entire viewport')
  self.screens.append(kwargs['path']);Path(kwargs['path']).write_bytes(b'NOT_A_REAL_SCREENSHOT_UNIT_FIXTURE')

class NaturalScrollTests(unittest.TestCase):
 def run_fixture(self,page):
  with tempfile.TemporaryDirectory() as t:
   record={};result=L.retain_readable_target(page,t,'fixture','.copy-section h2',0,False,record)
   self.assertTrue(all((Path(t)/a['file']).is_file() for a in record['artifacts']))
   return result,record
 def test_split_line_coverage_requires_multiple_full_viewports(self):
  page=FakeScrollPage();r,record=self.run_fixture(page);self.assertTrue(r['coverageComplete']);self.assertTrue(r['domUnmodified']);self.assertEqual(r['coveredLineIndexes'],[0,1,2]);self.assertEqual(len(page.screens),2);self.assertEqual(record['issues'],[])
 def test_stalled_scroll_retains_failure_and_never_passes(self):
  r,record=self.run_fixture(FakeScrollPage(stalled=True));self.assertFalse(r['coverageComplete']);self.assertTrue(record['issues']);self.assertEqual(len(r['frames']),1)
 def test_dom_mutation_is_failure_even_with_complete_line_coverage(self):
  r,record=self.run_fixture(FakeScrollPage(changed=True));self.assertTrue(r['coverageComplete']);self.assertFalse(r['domUnmodified']);self.assertIn('DOM changed during supplemental read-only scroll',record['issues'])
 def test_fixed_ui_leaves_no_safe_viewport_rejected(self):
  with self.assertRaisesRegex(RuntimeError,'no_readable_viewport'):self.run_fixture(FakeScrollPage(blocked=True))
 def test_text_or_layout_changes_are_rejected(self):
  with self.assertRaisesRegex(RuntimeError,'text_layout_changed'):self.run_fixture(FakeScrollPage(layout_changed=True))
 def test_hit_test_never_accepts_ancestor_overlay(self):
  self.assertNotIn('hit.contains(owner)',L.READABLE_TARGET_JS);self.assertIn('owner===hit||owner.contains(hit)',L.READABLE_TARGET_JS)

if __name__=='__main__':unittest.main(verbosity=2)
