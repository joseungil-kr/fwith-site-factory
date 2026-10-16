from pathlib import Path
import sys,tempfile,shutil,json,unittest
A=Path(__file__).resolve().parents[1];S=A.parent;C=S/'candidate';sys.path.insert(0,str(C/'scripts'));import qa_occurrences as q
from test_gokseong_node_python_parity import synthetic_node_output
class Occurrences(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.fixture=synthetic_node_output();cls.output,cls.mode=cls.fixture.__enter__()
 @classmethod
 def tearDownClass(cls):cls.fixture.__exit__(None,None,None)
 def test_production_all102_and119(self):
  r=q.check(self.output);self.assertEqual(r['checkedLogicalOccurrences'],119);self.assertEqual(r['deferredProductionOnlyOccurrences'],[])
 def test_private_all102_with_four_metadata_deferred(self):
  r=q.check(C/'dist','private');self.assertEqual(r['checkedLogicalOccurrences'],115);self.assertEqual(len(r['deferredProductionOnlyOccurrences']),4)
 def test_each_authored_leaf_real_output_mutation_rejected(self):
  mapping=json.loads((q.I/'output-context-map.json').read_text())
  from html import escape
  for row in mapping['contexts']:
   with self.subTest(pointer=row['pointer']),tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/'dist';shutil.copytree(self.output,root);page=row['occurrences'][0]['pageIds'][0];p=root/('index.html' if page=='home' else '404.html');s=p.read_text();text=escape(row['occurrences'][0]['expectedExtractedText'],quote=True)
    # Astro uses literal quotes in text nodes, escaped quotes in attributes.
    if text not in s:text=row['occurrences'][0]['expectedExtractedText']
    self.assertIn(text,s);p.write_text(s.replace(text,'MUTATED_CONTEXT',1))
    with self.assertRaises(AssertionError):q.check(root)
 def test_each_exact_occurrence_and_page_mutation_rejected(self):
  from html_surface import BeautifulSoup,Node,VOID
  from html import escape
  def serialize(n):
   if isinstance(n,str):return escape(n,quote=False)
   content=''.join(serialize(c) for c in n.children)
   if n.name=='document':return content
   attrs=''.join(' '+k+('="'+escape(v,quote=True)+'"' if v is not None else '') for k,v in n.attrs.items())
   return '<'+n.name+attrs+'>'+('' if n.name in VOID else content+'</'+n.name+'>')
  m=json.loads((q.I/'output-context-map.json').read_text());checked=0
  for row in m['contexts']:
   for o in row['occurrences']:
    for page in o['pageIds']:
     with self.subTest(pointer=row['pointer'],selector=o['selector'],page=page),tempfile.TemporaryDirectory() as tmp:
      root=Path(tmp)/'dist';shutil.copytree(self.output,root);p=root/('index.html' if page=='home' else '404.html');dom=BeautifulSoup(p.read_text());nodes=dom.select(o['selector']);self.assertEqual(len(nodes),1);node=nodes[0]
      if o['extraction']=='textContent':node.children=['MUTATED_ONE_BOUND_OCCURRENCE']
      else:node.attrs[o['extraction'].split(':')[1]]='MUTATED_ONE_BOUND_OCCURRENCE'
      p.write_text(serialize(dom))
      with self.assertRaises(AssertionError):q.check(root)
      checked+=1
  print('Rejected exact occurrence/page mutations:',checked)
 def test_same_words_moved_to_wrong_location_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'dist';shutil.copytree(self.output,root);p=root/'index.html';s=p.read_text();s=s.replace('id="budget"','id="wrong-location"',1);p.write_text(s)
   with self.assertRaises(AssertionError):q.check(root)
 def test_wrong_heading_tag_same_words_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'dist';shutil.copytree(self.output,root);p=root/'index.html';s=p.read_text();s=s.replace('<h3 data-reviewed-block data-faq-question>','<p data-reviewed-block data-faq-question>',1);p.write_text(s)
   with self.assertRaises(AssertionError):q.check(root)
if __name__=='__main__':unittest.main(verbosity=2)
