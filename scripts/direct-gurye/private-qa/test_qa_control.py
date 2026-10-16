from pathlib import Path
import copy,json,tempfile,unittest
import qa_control as q
B=json.loads((Path(__file__).parent/'bindings.json').read_text())
class ControlTests(unittest.TestCase):
 def test_bound_source_and_unbound_rejection(self):
  q.validate_binding(B)
  for revision in [None,'a'*40]:
   b=copy.deepcopy(B);b['sourceRevision']=revision
   with self.assertRaisesRegex(ValueError,'not bound'):q.validate_binding(b)
  b=copy.deepcopy(B);b['phase']='UNBOUND_SOURCE_COMMIT__PROJECTION_REVIEW_BOUND'
  with self.assertRaisesRegex(ValueError,'not bound'):q.validate_binding(b)
 def test_boundary_mutations(self):
  mutations=[lambda b:b.update(repository='other/repo'),lambda b:b.update(owner='other'),lambda b:b.update(sourceBranch='main'),lambda b:b.update(sourcePrefix='../escape'),lambda b:b.update(issueTitle='other'),lambda b:b.update(sourceManifestSHA256='0'*64),lambda b:b.update(sourceManifestUTF8=b['sourceManifestUTF8']+' '),lambda b:b.update(sourceZIP_SHA256='0'*64),lambda b:b.update(permissions={'contents':'write'}),lambda b:b.update(providerWrites=True),lambda b:b.update(productionEnabled=True),lambda b:b.update(newCredentials=True),lambda b:b.update(IndexNowEnabled=True),lambda b:b.update(remoteGitWrites=True),lambda b:b.update(historicalImplementationReviewSHA256='0'*64),lambda b:b['expectedDistFiles'].update({'index.html':'0'*64}),lambda b:b['expectedDistFiles'].update({'new-key.txt':'0'*64})]
  for mutate in mutations:
   b=copy.deepcopy(B);mutate(b)
   with self.assertRaises(ValueError):q.validate_binding(b,require_bound=False)
 def test_owner_event_exact(self):
  env={'GITHUB_REPOSITORY':q.REPOSITORY,'GITHUB_ACTOR':q.OWNER,'GITHUB_TRIGGERING_ACTOR':q.OWNER,'GITHUB_REF':'refs/heads/main','GITHUB_EVENT_NAME':'issues','GITHUB_RUN_ATTEMPT':'1'};event={'action':'opened','issue':{'title':q.ISSUE,'user':{'login':q.OWNER,'type':'User'}}};q.validate_owner_event(env,event)
  for key in env:
   bad=dict(env);bad[key]='other'
   with self.assertRaises(ValueError):q.validate_owner_event(bad,event)
  for event2 in [{'action':'edited','issue':event['issue']},{'action':'opened','issue':{'title':'other','user':event['issue']['user']}},{'action':'opened','issue':{'title':q.ISSUE,'user':{'login':'other','type':'User'}}},{'action':'opened','issue':{'title':q.ISSUE,'user':{'login':q.OWNER,'type':'Bot'}}}]:
   with self.assertRaises(ValueError):q.validate_owner_event(env,event2)
 def test_missing_projection_review_fails(self):
  b=copy.deepcopy(B);b.update(independentProjectionReview=None)
  with self.assertRaisesRegex(ValueError,'projection review'):q.validate_binding(b)
 def test_remote_save_proof_mutations(self):
  for key,value in [('resultSHA256','0'*64),('resultUTF8','{}'),('manifestSHA256','0'*64)]:
   b=copy.deepcopy(B);b['remoteSaveVerification'][key]=value
   with self.assertRaisesRegex(ValueError,'save verification'):q.validate_binding(b)
  b=copy.deepcopy(B);b['remoteSaveVerification']=None
  with self.assertRaisesRegex(ValueError,'save verification'):q.validate_binding(b)
 def test_projection_review_mutations(self):
  for key,value in [('accepted',False),('resultSHA256','0'*64),('resultUTF8','{}'),('manifestSHA256','0'*64)]:
   b=copy.deepcopy(B);b['independentProjectionReview'][key]=value
   with self.assertRaisesRegex(ValueError,'projection review'):q.validate_binding(b)
 def test_unsafe_and_symlink_path_rejected(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);(root/'ok.txt').write_text('fixture');q.safe_file(root,'ok.txt');(root/'link.txt').symlink_to(root/'ok.txt')
   for name in ['../ok.txt','/ok.txt','x\\ok.txt','link.txt','missing.txt']:
    with self.assertRaises(ValueError):q.safe_file(root,name)

# Synthetic validator fixtures only. None is a real screenshot, browser run or source artifact.
import struct,zlib,binascii,hashlib
from unittest import mock

def png_fixture(width,height,filter_type=0,raw=None,color=2):
 def chunk(kind,payload):return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',binascii.crc32(kind+payload)&0xffffffff)
 channels=3 if color==2 else 4
 if raw is None:raw=(bytes([filter_type])+b'\0'*(width*channels))*height
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,color,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')

def browser_fixture(candidate):
 f=B['browserExpected'];states=[];images=[];reach=[];interactions=[];touch=[];screens=[];folder=candidate/'evidence/browser';folder.mkdir(parents=True)
 rect={'x':0,'y':0,'width':100,'height':50}
 for width in f['widths']:
  for route in ['/','/404.html']:
   observations=[{'key':e['key'],'text':e['text'],'tag':e['tag'],'href':e.get('href'),'available':True,'rect':dict(rect)}for e in f['occurrences'][route]]
   states.append({'width':width,'route':route,'failures':[],'bodyExact':True,'scrollWidth':width,'clientWidth':width,'observations':observations})
   interactions.append({'width':width,'route':route,'test':'keyboard skip focuses main','pass':True})
  for e in f['images']:images.append({'width':width,**e,'displayWidth':100,'displayHeight':100*e['naturalHeight']/e['naturalWidth'],'objectFit':'contain'})
  reach.extend({'width':width,'key':e['key'],'rect':dict(rect)}for e in f['occurrences']['/']if e['key']!='ui.skipLabel')
  interactions.extend({'width':width,'test':'anchor/back/forward','href':href,'pass':True}for href in f['navigationHrefs'])
  interactions.extend([{'width':width,'test':'404 navigation home anchor','pass':True},{'width':width,'test':'404 recovery CTA','pass':True}])
  touch.extend({'width':width,'text':label,'height':44,'widthPx':100}for label in f['touchLabels'])
 for name,(width,height)in q.screenshot_expectations(f).items():
  data=png_fixture(width,height or 844);(folder/name).write_bytes(data);screens.append({'path':name,'sha256':q.sha(data)})
 paths={'/','/404.html'}|{e['src']for e in f['images']}|{'/'+n for n in B['expectedDistFiles']if n.endswith('.css')}
 return {'status':'PASS_AUTHOR_LOCAL_CHROMIUM_CHECKS','checkedAtUTC':'2026-10-16T12:00:00+00:00','browserVersion':'123.0.0.0','origin':'loopback-only','widths':f['widths'],'pages':2,'states':states,'imageAspectChecks':images,'scrollReachability':reach,'interactions':interactions,'touchTargets':touch,'computedVisibilityMutationDetected':True,'localMissingRouteStatus':404,'responses':[{'path':name,'status':200}for name in sorted(paths)]+[{'path':'/.gurye-private-missing/','status':404}],'externalRequestsBlocked':[],'pageErrors':[],'externalCTAAndPhoneActivated':False,'publicHTTPVerified':False,'independentImplementationReview':False,'screenshots':screens}

class BrowserAndGeneratedPathTests(unittest.TestCase):
 def test_expected_browser_binding_mutation(self):
  b=copy.deepcopy(B);b['browserExpected']['occurrences']['/'][0]['text']='altered'
  with self.assertRaisesRegex(ValueError,'expected observations'):q.validate_binding(b)
 def test_complete_synthetic_browser_fixture_and_observation_mutations(self):
  with tempfile.TemporaryDirectory()as tmp:
   candidate=Path(tmp)/'candidate';report=browser_fixture(candidate);file=candidate/'evidence/browser/browser-report.json'
   # Only parser semantics are exercised here. Actual source51/dist11 checks are separate integration evidence.
   with mock.patch.object(q,'check_source_files'),mock.patch.object(q,'check_dist'):
    file.write_text(json.dumps(report));result=q.verify_browser(candidate,B);self.assertEqual(len(result['decodedScreenshots']),31);self.assertFalse(result['publicationReady'])
    mutations=[
     lambda r:r['states'].__setitem__(1,copy.deepcopy(r['states'][0])),
     lambda r:r['states'][0].update(observations=[]),
     lambda r:r['states'][0]['observations'][0].update(key='wrong'),
     lambda r:r['states'][0]['observations'][0].update(text='wrong'),
     lambda r:r['states'][0]['observations'][0].update(tag='p'),
     lambda r:r['states'][0]['observations'][0].update(href='#wrong'),
     lambda r:r['states'][0]['observations'][0].update(available=False),
     lambda r:r['states'][0]['observations'][0]['rect'].update(width=0),
     lambda r:r['states'][0]['observations'][0]['rect'].update(x=float('nan')),
     lambda r:r['states'][0].update(scrollWidth=0),
     lambda r:r['states'][0].update(clientWidth=321),
     lambda r:r['imageAspectChecks'].__setitem__(0,{}),
     lambda r:r['imageAspectChecks'][0].update(src='/wrong.jpg'),
     lambda r:r['imageAspectChecks'][0].update(naturalWidth=1),
     lambda r:r['imageAspectChecks'][0].update(displayHeight=1),
     lambda r:r['imageAspectChecks'][0].update(objectFit='cover'),
     lambda r:r['scrollReachability'].__setitem__(0,{}),
     lambda r:r['scrollReachability'][0].update(key='wrong'),
     lambda r:r['scrollReachability'][0]['rect'].update(y=844),
     lambda r:r['scrollReachability'][0]['rect'].update(x=-2),
     lambda r:r['interactions'][0].update(**{'pass':False}),
     lambda r:r['interactions'][2].update(href='#wrong'),
     lambda r:r['touchTargets'][0].update(height=0),
     lambda r:r['touchTargets'][0].update(widthPx=43),
     lambda r:r['touchTargets'][0].update(text='wrong'),
     lambda r:r.update(responses=[]),
     lambda r:r['responses'][0].update(path='https://outside.invalid'),
     lambda r:r.update(externalRequestsBlocked=['outside']),
     lambda r:r.update(computedVisibilityMutationDetected=False),
     lambda r:r['screenshots'][0].update(path='wrong-320.png'),
     lambda r:r['screenshots'][0].update(sha256='0'*64),
    ]
    for i,mutate in enumerate(mutations):
     bad=copy.deepcopy(report);mutate(bad);file.write_text(json.dumps(bad))
     with self.subTest(mutation=i),self.assertRaises(ValueError):q.verify_browser(candidate,B)
    row=report['screenshots'][0];png=candidate/'evidence/browser'/row['path'];original=png.read_bytes()
    for data in [b'NOT_A_PNG',png_fixture(319,844)]:
     bad=copy.deepcopy(report);png.write_bytes(data);bad['screenshots'][0]['sha256']=q.sha(data);file.write_text(json.dumps(bad))
     with self.assertRaises(ValueError):q.verify_browser(candidate,B)
    png.write_bytes(original)
 def test_png_filters_and_invalid_streams(self):
  # Reconstruct known 2x2 RGB samples through every PNG filter, checking decoded pixels.
  rows=[bytes([10,20,30,40,50,60]),bytes([70,80,90,100,110,120])]
  for filter_type in range(5):
   raw=b'';previous=bytes(6)
   for row in rows:
    encoded=[]
    for i,x in enumerate(row):
     left=row[i-3]if i>=3 else 0;up=previous[i];ul=previous[i-3]if i>=3 else 0
     if filter_type==0:predictor=0
     elif filter_type==1:predictor=left
     elif filter_type==2:predictor=up
     elif filter_type==3:predictor=(left+up)//2
     else:
      v=left+up-ul;dist=[abs(v-left),abs(v-up),abs(v-ul)];predictor=[left,up,ul][dist.index(min(dist))]
     encoded.append((x-predictor)&255)
    raw+=bytes([filter_type])+bytes(encoded);previous=row
   decoded=q.decode_png(png_fixture(2,2,raw=raw));self.assertEqual(decoded['decodedPixelsSHA256'],q.sha(b''.join(rows)))
  self.assertEqual(q.decode_png(png_fixture(2,2,color=6))['channels'],4)
  valid=png_fixture(2,2)
  for data in [b'NOT_A_PNG',valid[:-1],valid+b'trailing',valid[:20]+b'X'+valid[21:],png_fixture(2,2,filter_type=5),png_fixture(2,2,raw=b'bad'),png_fixture(1281,1),png_fixture(2,2,raw=b'\0'*100)]:
   with self.assertRaises(ValueError):q.decode_png(data)
 def test_postbuild_excludes_only_exact_generated_roots(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);source=root/'candidate/scripts/expected_surface.py';source.parent.mkdir(parents=True);source.write_bytes(b'fixture')
   row={'path':'candidate/scripts/expected_surface.py','bytes':7,'sha256':q.sha(b'fixture'),'gitBlobSHA':hashlib.sha1(b'blob 7\0fixture').hexdigest(),'storageMode':'UTF8_CONTENT'}
   with mock.patch.object(q,'validate_binding',return_value={'files':[row]}):
    q.check_source_files(root,B,True)
    for name in ['candidate/src/evidence/unreviewed.py','candidate/src/node_modules/unreviewed.py','candidate/src/dist/unreviewed.py','candidate/src/.astro/unreviewed.py','candidate/src/__pycache__/unreviewed.py','candidate/scripts/__pycache__/unreviewed.py','candidate/scripts/__pycache__/unknown.cpython-312.pyc']:
     target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('unapproved')
     with self.subTest(path=name),self.assertRaises(ValueError):q.check_source_files(root,B,True)
     target.unlink()
    for name in ['candidate/evidence/report.json','candidate/dist/index.html','candidate/.astro/types.d.ts','candidate/node_modules/fixture.json','candidate/scripts/__pycache__/expected_surface.cpython-312.pyc']:
     target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('generated fixture')
    q.check_source_files(root,B,True)

if __name__=='__main__':unittest.main()
