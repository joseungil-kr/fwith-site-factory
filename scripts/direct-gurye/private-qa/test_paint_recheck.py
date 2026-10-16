"""Synthetic-only tests of the limited paint supplement; no browser execution."""
from pathlib import Path
import copy,hashlib,json,struct,tempfile,unittest,zlib,binascii
from unittest import mock
import paint_recheck as p
B=json.loads((Path(__file__).parent/'bindings.json').read_text())

def png(width,height,pixels,filter_type=0):
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',binascii.crc32(kind+data)&0xffffffff)
 stride=width*3;raw=[];previous=bytes(stride)
 for y in range(height):
  row=pixels[y*stride:(y+1)*stride];values=[]
  for x,value in enumerate(row):
   left=row[x-3]if x>=3 else 0;up=previous[x];ul=previous[x-3]if x>=3 else 0
   if filter_type==0:predictor=0
   elif filter_type==1:predictor=left
   elif filter_type==2:predictor=up
   elif filter_type==3:predictor=(left+up)//2
   else:
    estimate=left+up-ul;dist=[abs(estimate-left),abs(estimate-up),abs(estimate-ul)];predictor=[left,up,ul][dist.index(min(dist))]
   values.append((value-predictor)&255)
  raw.append(bytes([filter_type])+bytes(values));previous=row
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(raw)))+chunk(b'IEND',b'')

def fixture(root):
 full_pixels=b''.join(bytes([y%251,(y*3)%251,(y*7)%251])*390 for y in range(1000));full=png(390,1000,full_pixels);view=png(390,844,full_pixels[50*390*3:894*390*3]);root.mkdir();(root/'home390-full-reference.png').write_bytes(full)
 def geometry(y):return {'scrollX':0,'scrollY':y,'width':390,'height':844,'documentHeight':1000,'fontStatus':'loaded','rect':{'x':14,'y':140-y,'width':362,'height':800}}
 def settled(g):return {'stableTransitions':5,'samples':[copy.deepcopy(g)for _ in range(6)]}
 flows=[];wanted=[x for x in B['browserExpected']['occurrences']['/']if x['key'].startswith('section.ribbon-and-order.')]
 for name,neighbor,direction,neighbor_y in [('from-facility','#receiving-place','down',0),('from-timing','#order-timing','up',100)]:
  frames=[]
  for number in [1,2]:
   filename=f'ribbon390-{name}-frame{number}.png';(root/filename).write_bytes(view);g=geometry(50);observations=[{**x,'href':x.get('href'),'available':True,'rect':{'x':20,'y':100,'width':300,'height':50}}for x in wanted];frames.append({'number':number,'path':filename,'sha256':p.q.sha(view),'settle':settled(g),'before':g,'after':copy.deepcopy(g),'observations':observations})
  flows.append({'name':name,'neighbor':neighbor,'direction':direction,'neighborState':geometry(neighbor_y),'frames':frames})
 paths={'/'}|{x['src']for x in B['browserExpected']['images']}|{'/'+x for x in B['expectedDistFiles']if x.endswith('.css')};g=geometry(0)
 report={'status':'CAPTURED_PENDING_PIXEL_VERIFICATION','sourceRevision':p.SOURCE,'originalRun':p.ORIGINAL_RUN,'originalArtifact':p.ORIGINAL_ARTIFACT,'originalArchiveSHA256':p.ORIGINAL_ARCHIVE_SHA,'originalProblemPNGSHA256':p.ORIGINAL_BAD_SHA,'width':390,'height':844,'originalEvidenceReplaced':False,'layoutOrCopyChanged':False,'flows':flows,'externalRequestsBlocked':[],'pageErrors':[],'responses':[{'path':x,'status':200}for x in sorted(paths)],'publicHTTPVerified':False,'publicationReady':False,'fullReference':{'path':'home390-full-reference.png','sha256':p.q.sha(full),'before':g,'after':copy.deepcopy(g),'settle':settled(g)}}
 (root/'capture-report.json').write_text(json.dumps(report));return report,full,view

class PaintRecheckTests(unittest.TestCase):
 def test_same_source_dependency_binding(self):
  self.assertEqual(p.binding()['sourceRevision'],p.SOURCE)
 def test_decoder_returns_exact_known_pixels_for_all_filters(self):
  pixels=bytes(range(36))
  for mode in range(5):
   info,decoded=p.decoded_pixels(png(3,4,pixels,mode));self.assertEqual(decoded,pixels);self.assertEqual(info['decodedPixelsSHA256'],hashlib.sha256(pixels).hexdigest())
 def test_complete_synthetic_two_direction_pairs(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)/'synthetic';fixture(root);result=p.verify_capture(root,B);self.assertEqual(result['actualNewScreenshots'],5);self.assertTrue(all(x['matchingRows']==844 for x in result['pixelComparisons']));self.assertFalse(result['publicationReady'])
 def test_old_partial_blank_raster_shape_is_rejected_even_with_updated_sha(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)/'synthetic';report,full,view=fixture(root);info,pixels=p.decoded_pixels(view);bad=pixels[:420*390*3]+bytes([248,245,250])*390*424;data=png(390,844,bad);f=report['flows'][0]['frames'][0];(root/f['path']).write_bytes(data);f['sha256']=p.q.sha(data);(root/'capture-report.json').write_text(json.dumps(report))
   with self.assertRaisesRegex(ValueError,'424 rows'):p.verify_capture(root,B)
 def test_report_mutations_rejected(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)/'synthetic';report,_,_=fixture(root);mutations=[lambda r:r.update(sourceRevision='a'*40),lambda r:r.update(originalEvidenceReplaced=True),lambda r:r.update(layoutOrCopyChanged=True),lambda r:r.update(publicationReady=True),lambda r:r.update(flows=r['flows'][:1]),lambda r:r['flows'][0].update(direction='up'),lambda r:r['flows'][0]['neighborState'].update(scrollY=100),lambda r:r['flows'][0]['frames'][0]['after'].update(scrollY=51),lambda r:r['flows'][0]['frames'][0]['before'].update(fontStatus='loading'),lambda r:r['flows'][0]['frames'][0]['settle'].update(stableTransitions=4),lambda r:r['flows'][0]['frames'][0]['settle']['samples'][-1].update(scrollY=51),lambda r:r['flows'][0]['frames'][0]['observations'][0].update(text='changed'),lambda r:r['flows'][0]['frames'][0]['observations'][0].update(available=False),lambda r:r['flows'][0]['frames'][0].update(path='wrong.png'),lambda r:r['flows'][0]['frames'][0].update(sha256='0'*64),lambda r:r['fullReference'].update(sha256='0'*64),lambda r:r.update(responses=[]),lambda r:r.update(externalRequestsBlocked=['outside']),lambda r:r.update(pageErrors=['error'])]
   for i,change in enumerate(mutations):
    r=copy.deepcopy(report);change(r);(root/'capture-report.json').write_text(json.dumps(r))
    with self.subTest(mutation=i),self.assertRaises(ValueError):p.verify_capture(root,B)
 def test_comparison_bad_offset_and_png_rejected(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)/'synthetic';_,full,view=fixture(root)
   for offset in [-1,True,50.5,999,float('nan')]:
    with self.assertRaises(ValueError):p.compare_viewport_to_full(view,full,offset)
   with self.assertRaises(ValueError):p.compare_viewport_to_full(b'not png',full,50)
if __name__=='__main__':unittest.main()
