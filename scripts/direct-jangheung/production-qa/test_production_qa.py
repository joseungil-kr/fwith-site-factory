"""Real source58/output15 plus explicitly synthetic browser-report fixtures.

These are validator tests, not a production browser run or screenshot acceptance.
"""
from pathlib import Path
import copy,hashlib,json,mimetypes,os,shutil,struct,tempfile,unittest,zlib
import production_qa as g
import browser_evidence as q
from unittest.mock import patch,Mock

def png_rows(width,values):
 def chunk(k,b):return struct.pack('>I',len(b))+k+b+struct.pack('>I',zlib.crc32(k+b)&0xffffffff)
 raw=b''.join(b'\0'+bytes([value])*(width*3)for value in values)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,len(values),8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
def png(width,height,value=0):return png_rows(width,[value]*height)

def chunk(kind, payload):
    return (struct.pack('>I', len(payload)) + kind + payload
            + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff))

def encoded_png(width, height, raw, color=2, depth=8, interlace=0):
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, depth,
                                        color, 0, 0, interlace))
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))

def synthetic_purchase(expected,width,scope):
    """Synthetic purchase geometry, never actual screenshot or DOM evidence."""
    style=dict(display='block',visibility='visible',opacity='1',hidden=False,inert=False,ariaHidden=None)
    def node(text,tag,y,height):
        return dict(text=text,tag=tag,href=None,available=True,rect=dict(x=16,y=y,width=width-32,height=height),ancestors=[dict(style)])
    return dict(fragment='#products-cost',productHeading=node(expected['productHeading'],'h2',-400,50),
                productNotice=node(expected['productText'],'p',90,150),productCards=node('synthetic cards','div',250,500),
                productAdjacent=True,hospitalRestrictionElements=0,selectedHospitalElements=0,
                products=[dict(p,ctaHref=p['href'],ctaLabel=p['label'],sumElements=0)for p in expected['products']])

def synthetic_reports(source, dist, binding,module,qb):
    """Create deliberately synthetic unit inputs, strictly inside a temp tree."""
    fixture = binding['browserExpected']
    folder = source / 'candidate/evidence/browser'
    folder.mkdir(parents=True)
    states, images, reach, interactions, touch = [], [], [], [], []
    screenshots, captures, metadata = [], [], []
    rect = {'x': 0, 'y': 0, 'width': 100, 'height': 50}
    for width in fixture['widths']:
        for route in ['/', '/404.html']:
            observations = [dict(key=e['key'], text=e['text'], tag=e['tag'],
                                 href=e.get('href'), available=True, rect=dict(rect))
                            for e in fixture['occurrences'][route]]
            states.append(dict(width=width, route=route, failures=[], bodyExact=True,
                               scrollWidth=width, clientWidth=width, observations=observations,
                               links=copy.deepcopy(fixture['allLinks'][route]),manuscriptSHA256=fixture['copyBinding']['manuscriptSHA256'],
                               structure=copy.deepcopy(fixture['structure'])if route=='/'else None))
            interactions.append(dict(width=width, route=route,
                                     test='keyboard skip focuses main', **{'pass': True}))
            metadata.append({'width':width,'route':route,'robots':'index,follow'if route=='/'else'noindex,nofollow','canonical':['https://jangheung.fwith.kr/']if route=='/'else[],'source':binding['assemblyRevision'],'privateSource':g.SOURCE,'releaseState':'production-candidate','social':[list(x)for x in module.social_values(module.read_contract(),module.verify_inputs(source)[2])]if route=='/'else[]})
        images.extend(dict(width=width, **e, displayWidth=100,
                           displayHeight=100 * e['naturalHeight'] / e['naturalWidth'],
                           objectFit='contain') for e in fixture['images'])
        reach.extend(dict(width=width, key=e['key'], rect=dict(rect))
                     for e in fixture['occurrences']['/'] if e['key'] != 'ui.skipLabel')
        interactions.extend(dict(width=width, test='anchor/back/forward', href=href,
                                 **{'pass': True}) for href in fixture['navigationHrefs'])
        interactions.extend(dict(width=width, test=test, **{'pass': True})
                            for test in ['404 navigation home anchor', '404 recovery CTA'])
        touch.extend(dict(width=width, **entry, height=44, widthPx=100)
                     for entry in fixture['touchLinks'])
    for name, (width, _) in q.screenshot_expectations(fixture).items():
        home, full = name.startswith('home-'), name.endswith('-full.png')
        section = home and not full and not name.endswith('-top.png')
        scroll, document_height = (100 if section else 0), (2000 if home else 844)
        values = [y % 211 for y in range(document_height)]
        raster = values if full else values[scroll:scroll + 844]
        if name in g.sticky_names():
            raster = [237] * 71 + raster[71:]
        raw = png_rows(width, raster)
        (folder / name).write_bytes(raw)
        screenshots.append({'path': name, 'sha256': g.sha(raw)})
        geometry = dict(scrollX=0, scrollY=scroll, width=width, height=844,
                        documentHeight=document_height, fontStatus='loaded')
        cap = dict(path=name, fullPage=full, before=geometry, after=dict(geometry),
                   settle={'stableTransitions': 5,
                           'samples': [dict(geometry) for _ in range(6)]})
        if name in g.sticky_names():
            expected = [e for e in fixture['occurrences']['/']
                        if e['key'] in ['ui.brandLabel', 'ui.regionLabel',
                                        'ui.navigation.0', 'ui.navigation.1',
                                        'ui.navigation.2', 'ui.navigation.3']]
            header = dict(rect={'x': 0, 'y': 0, 'width': 1280, 'height': 71},
                          position='sticky', top='0px', zIndex='20',
                          backgroundColor='rgba(255, 255, 255, 0.96)',
                          backdropFilter='blur(10px)', borderBottomWidth='1px',
                          observations=[dict(key=e['key'], text=e['text'], tag=e['tag'],
                                             href=e.get('href'), available=True,
                                             rect={'x': i * 180, 'y': 15, 'width': 100, 'height': 40})
                                        for i, e in enumerate(expected)])
            raw = png(1280, 71, 237)
            path = 'sticky-headers/' + name
            (folder / path).parent.mkdir(exist_ok=True)
            (folder / path).write_bytes(raw)
            cap['stickyHeader'] = dict(path=path, sha256=g.sha(raw), before=header,
                                       after=copy.deepcopy(header), geometryAfter=dict(geometry))
        scope='eligibility'if name.endswith('-eligibility.png')else None
        if scope:
            observed=synthetic_purchase(fixture['purchase'],width,scope)
            cap['purchaseSnapshot']=dict(scope=scope,before=observed,after=copy.deepcopy(observed),screenshotSHA256=g.sha((folder/name).read_bytes()))
        captures.append(cap)
    paths = {'/', '/404.html'} | {e['src'] for e in fixture['images']}
    paths |= {'/' + n for n in binding['expectedDistFiles'] if n.endswith('.css')}
    report = dict(unitFixture=True, fixturePurpose='SYNTHETIC_UNIT_TEST_NOT_ACTUAL_QA_EVIDENCE',
                  status='PASS_AUTHOR_LOCAL_CHROMIUM_CHECKS',
                  checkedAtUTC='2026-10-16T14:00:00+00:00', browserVersion='123.0.0.0',
                  origin='loopback-only', widths=fixture['widths'], pages=2,
                  states=states, imageAspectChecks=images, scrollReachability=reach,
                  interactions=interactions, touchTargets=touch,
                  computedVisibilityMutationDetected=True,
                  purchaseVisibilityMutations=[{'selector':selector,'rule':rule,'detected':True}for selector in ['.product-eligibility']for rule in ['display:none','visibility:hidden','opacity:0']],
                  localMissingRouteStatus=404,
                  responses=[dict(path=n, status=200) for n in sorted(paths)]
                            + [dict(path='/.jangheung-private-missing/', status=404)],
                  externalRequestsBlocked=[], pageErrors=[], externalCTAAndPhoneActivated=False,
                  publicHTTPVerified=False, independentImplementationReview=False,
                  screenshots=screenshots)
    http_rows = []
    for name, raw in sorted(module.inventory(dist).items()):
        path = '/' if name == 'index.html' else '/' + name
        mime = 'application/octet-stream'if name=='_headers'else mimetypes.guess_type(name)[0]
        http_rows.append(dict(path=path, status=200, sha256=g.sha(raw), bytes=len(raw),
                              contentType=mime, finalURLPath=path))
    missing = (dist / '404.html').read_bytes()
    capture = dict(unitFixture=True, fixturePurpose='SYNTHETIC_UNIT_TEST_NOT_ACTUAL_QA_EVIDENCE',
                   privateSourceRevision=g.SOURCE,assemblyRevision=binding['assemblyRevision'], origin='loopback-only',
                   captures=captures, metadata=metadata, httpFiles=http_rows,
                   missingRoute=dict(path='/.jangheung-private-missing/', status=404,
                                     sha256=g.sha(missing), bytes=len(missing),
                                     robots='noindex,nofollow', canonicalCount=0),
                   publicHTTPVerified=False, publicationReady=False)
    g.save(folder / 'browser-report.json', report)
    g.save(folder / 'production-capture.json', capture)
    return report, capture

class ControlTests(unittest.TestCase):
 def test_bound_identity_and_fail_closed_review_semantics(self):
  from unittest.mock import patch,Mock
  valid=g.binding();self.assertEqual(valid['sourceFiles'],58);self.assertNotEqual(valid['assemblyRevision'],g.SOURCE)
  original_safe=g.safe
  mutations=[lambda b:b.update(phase='UNBOUND_REVIEW_AND_REMOTE_SAVE_PENDING'),lambda b:b.update(assemblyRevision=g.SOURCE),lambda b:b.update(sourceFiles=57),lambda b:b.update(permissions={'contents':'write'}),lambda b:b.update(providerWrites=True),lambda b:b.update(publicationReady=True),lambda b:b.update(browserExpectedSHA256='0'*64),lambda b:b.update(captureSHA256='0'*64),lambda b:b.update(browserEvidenceSHA256='0'*64),lambda b:b['production4Review'].update(sha256='0'*64),lambda b:b['source58Readback'].update(sha256='0'*64),lambda b:b['files'].pop()]
  for mutate in mutations:
   changed=copy.deepcopy(valid);mutate(changed);raw=json.dumps(changed,ensure_ascii=False,indent=2).encode();file=Mock();file.read_bytes.return_value=raw
   with patch.object(g,'safe',side_effect=lambda root,rel:file if root==g.ROOT and rel=='bindings.json'else original_safe(root,rel)),patch.object(g,'BINDING_SHA',g.sha(raw)):
    with self.assertRaises(ValueError):g.binding()
 def test_owner_boundary(self):
  env={'GITHUB_REPOSITORY':g.REPO,'GITHUB_REF':'refs/heads/main','GITHUB_ACTOR':g.OWNER,'GITHUB_TRIGGERING_ACTOR':g.OWNER,'GITHUB_RUN_ATTEMPT':'1','GITHUB_EVENT_NAME':'issues','GITHUB_SHA':'1'*40,'GITHUB_RUN_ID':'123'};event={'action':'opened','issue':{'title':g.TITLE,'number':1,'user':{'login':g.OWNER,'type':'User'}}};g.owner(env,event)
  for k in env:
   bad=dict(env);bad[k]='wrong'
   with self.assertRaises(ValueError):g.owner(bad,event)
  for mutate in [lambda e:e.update(action='edited'),lambda e:e['issue'].update(title='wrong'),lambda e:e['issue']['user'].update(login='other'),lambda e:e['issue']['user'].update(type='Bot')]:
   bad=copy.deepcopy(event);mutate(bad)
   with self.assertRaises(ValueError):g.owner(env,bad)
 def test_geometry_and_path_guards(self):
  good={'scrollX':0,'scrollY':0,'width':390,'height':844,'documentHeight':1000,'fontStatus':'loaded'};g.verify_geometry(good,390,844)
  for k,v in [('scrollX',1),('scrollY',float('nan')),('scrollY',True),('scrollY',.5),('width',320),('height',600),('documentHeight',500),('fontStatus','loading')]:
   bad=dict(good);bad[k]=v
   with self.assertRaises(ValueError):g.verify_geometry(bad,390,844)
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);(root/'x').write_text('x');(root/'link').symlink_to(root/'x')
   for rel in ['../x','/x','link','missing']:
    with self.assertRaises(ValueError):g.safe(root,rel)

 def test_actual_control_head_comparison_and_checkout_location(self):
     env = {'GITHUB_SHA': '1' * 40}
     with patch.object(g.subprocess, 'run', return_value=Mock(returncode=0, stdout='1' * 40 + '\n')) as run:
         self.assertEqual(g.control_identity(env), env['GITHUB_SHA'])
         self.assertEqual(run.call_args.args[0], ['git', 'rev-parse', 'HEAD'])
         self.assertEqual(run.call_args.kwargs['cwd'], g.ROOT.parents[2])
     for code, stdout in [(1, ''), (0, '2' * 40), (0, '')]:
         with self.subTest(returncode=code, stdout=stdout), \
              patch.object(g.subprocess, 'run', return_value=Mock(returncode=code, stdout=stdout)):
             with self.assertRaisesRegex(ValueError, 'control checkout HEAD'):
                 g.control_identity(env)
 def test_png_decoder_rejects_corruption_and_stream_ambiguity(self):
     valid = png(2, 2, 17)
     info, pixels = q.decoded_pixels(valid)
     self.assertEqual((info['width'], info['height'], info['channels']), (2, 2, 3))
     self.assertEqual(pixels, bytes([17]) * 12)
     header = chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, 2, 0, 0, 0))
     signature = b'\x89PNG\r\n\x1a\n'
     stream = zlib.compress(b'\0' + b'\x11' * 6 + b'\0' + b'\x11' * 6)
     corruptions = [b'not png', valid[:-1], valid + b'extra',
                    valid[:29] + bytes([valid[29] ^ 1]) + valid[30:],
                    encoded_png(1281, 1, b'\0'), encoded_png(0, 1, b'\0'),
                    encoded_png(1, 50001, b'\0'), encoded_png(2, 2, b'\0'),
                    encoded_png(2, 2, b'\0' * 15),
                    encoded_png(2, 2, b'\x05' + b'\0' * 6 + b'\0' * 7),
                    encoded_png(2, 2, b'\0' * 14, depth=16),
                    encoded_png(2, 2, b'\0' * 14, color=0),
                    encoded_png(2, 2, b'\0' * 14, interlace=1),
                    signature + header + header + chunk(b'IDAT', stream) + chunk(b'IEND', b''),
                    signature + header + chunk(b'ABCD', b'') + chunk(b'IDAT', stream) + chunk(b'IEND', b''),
                    signature + header + chunk(b'IDAT', stream + zlib.compress(b'x')) + chunk(b'IEND', b''),
                    signature + header + chunk(b'IDAT', b'not-zlib') + chunk(b'IEND', b''),
                    signature + header + chunk(b'IDAT', stream[:3]) + chunk(b'tEXt', b'a')
                    + chunk(b'IDAT', stream[3:]) + chunk(b'IEND', b'')]
     for i, raw in enumerate(corruptions):
         with self.subTest(png_corruption=i):
             with self.assertRaises(ValueError):
                 q.decode_png(raw)
 def test_rgb_rgba_all_png_filters_have_independent_pixel_parity(self):
     for channels in [3, 4]:
         width, height = 3, 5
         rows = [bytes((x * 17 + y * 13) % 256 for x in range(width * channels))
                 for y in range(height)]
         for filter_type in range(5):
             raw, previous = [], bytes(width * channels)
             for row in rows:
                 encoded = []
                 for x, value in enumerate(row):
                     left = row[x - channels] if x >= channels else 0
                     up = previous[x]
                     upper_left = previous[x - channels] if x >= channels else 0
                     estimate = left + up - upper_left
                     distances = [abs(estimate - left), abs(estimate - up), abs(estimate - upper_left)]
                     paeth = [left, up, upper_left][distances.index(min(distances))]
                     predictor = [0, left, up, (left + up) // 2, paeth][filter_type]
                     encoded.append((value - predictor) & 255)
                 raw.append(bytes([filter_type]) + bytes(encoded))
                 previous = row
             with self.subTest(channels=channels, filter=filter_type):
                 info, pixels = q.decoded_pixels(encoded_png(width, height, b''.join(raw),
                                                            color=2 if channels == 3 else 6))
                 self.assertEqual(pixels, b''.join(rows))
                 self.assertEqual(info['decodedPixelsSHA256'], hashlib.sha256(pixels).hexdigest())

class RealInputAndSyntheticObservationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.b=g.binding()
  cls.original=Path(os.environ['JANGHEUNG_PRODUCTION_CHECKOUT']).resolve();cls.dist=Path(os.environ['JANGHEUNG_PRODUCTION_DIST']).resolve()
  if os.environ.get('JANGHEUNG_UNIT_REMOTE_READBACK_ONLY')=='1':
   # Local downloaded-only fixture has no fabricated .git; CLI/Actions always verifies HEAD.
   module,source,_=g.check_files(cls.original,cls.b,False);module.validate(source,cls.dist,cls.b['assemblyRevision'])
  else:g.postbuild(cls.original,cls.dist,cls.b)
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='jangheung-control60-test-');self.root=Path(self.tmp.name);self.checkout=self.root/'target';self.checkout.mkdir()
  for row in self.b['files']:
   p=self.checkout/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((self.original/row['path']).read_bytes())
  self.source=self.checkout/'site-factory/jangheung-flower';shutil.copytree(self.original/'site-factory/jangheung-flower/candidate/dist',self.source/'candidate/dist');self.output=self.root/'release15';shutil.copytree(self.dist,self.output)
 def tearDown(self):self.tmp.cleanup()
 def test_real_source58_and_output15_positive(self):
  module,source,qb=g.check_files(self.checkout,self.b,git_required=False);self.assertEqual(module.validate(source,self.output,self.b['assemblyRevision'])['productionFilesVerified'],15)
 def test_actual_head_is_required_by_default(self):
  with self.assertRaisesRegex(ValueError,'checkout HEAD'):g.check_files(self.checkout,self.b)
 def test_source_mutations_and_nested_generated_name_rejected(self):
  p=self.source/'candidate/src/layouts/BaseLayout.astro';before=p.read_bytes();p.write_bytes(before+b'\n')
  with self.assertRaises(ValueError):g.check_files(self.checkout,self.b,False)
  p.write_bytes(before)
  for name in ['site-factory/jangheung-flower/candidate/src/evidence/unreviewed.py','scripts/direct-jangheung/production-release/extra.py']:
   p=self.checkout/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('bad')
   with self.assertRaises(ValueError):g.check_files(self.checkout,self.b,False)
   p.unlink()
 def test_synthetic_complete_contract_and_negative_metadata_http_frames(self):
  module,source,qb=g.check_files(self.checkout,self.b,False);report,capture=synthetic_reports(source,self.output,self.b,module,qb);folder=source/'candidate/evidence/browser'
  result=g.verify_browser(self.checkout,self.output,self.b,git_required=False,allow_unit_fixture=True);self.assertEqual(result['syntheticChecks']['stableCapturesEvaluated'],34);self.assertEqual(len(result['syntheticChecks']['homeViewportFullPixelComparisons']),27);self.assertFalse(result['publicationReady']);self.assertEqual(result['syntheticChecks']['stickyHeaderReferencesEvaluated'],8);self.assertEqual(sum(x['stickyReferenceRows']for x in result['syntheticChecks']['homeViewportFullPixelComparisons']),8*71)
  mutations=[lambda r:r.update(assemblyRevision='f'*40),lambda r:r['metadata'][0].update(robots='noindex,nofollow'),lambda r:r['metadata'][0].update(canonical=['https://gokseong.fwith.kr/']),lambda r:r['metadata'][0].update(source='0'*40),lambda r:r['metadata'][0].update(width=390),lambda r:r['httpFiles'].pop(),lambda r:r['httpFiles'][0].update(status=404),lambda r:r['httpFiles'][0].update(sha256='0'*64),lambda r:r['httpFiles'][0].update(contentType='wrong/type'),lambda r:r['httpFiles'][0].update(finalURLPath='/other'),lambda r:r['captures'][0]['settle'].update(samples=[]),lambda r:r['captures'][0]['settle']['samples'][0].update(scrollY=1),lambda r:r['captures'][0]['before'].update(fontStatus='loading'),lambda r:r['captures'][0].update(path='wrong.png'),lambda r:r['captures'][0].update(fullPage=True)]
  for mutate in mutations:
   bad=copy.deepcopy(capture);mutate(bad);g.save(folder/'production-capture.json',bad)
   with self.assertRaises(ValueError):g.verify_browser(self.checkout,self.output,self.b,git_required=False,allow_unit_fixture=True)
  g.save(folder/'production-capture.json',capture)
  # A real PNG with the right dimensions/hash but different raster must fail full comparison.
  name='home-390-ribbon.png';data=png(390,844,1);(folder/name).write_bytes(data)
  for row in report['screenshots']:
   if row['path']==name:row['sha256']=g.sha(data)
  g.save(folder/'browser-report.json',report)
  with self.assertRaisesRegex(ValueError,'raster'):g.verify_browser(self.checkout,self.output,self.b,git_required=False,allow_unit_fixture=True)
 def test_declared_fixture_rejected_by_both_default_actual_paths(self):
  import browser_evidence as q
  from unittest.mock import patch,Mock
  module,source,qb=g.check_files(self.checkout,self.b,False);report,capture=synthetic_reports(source,self.output,self.b,module,qb);folder=source/'candidate/evidence/browser'
  with self.assertRaisesRegex(ValueError,'Synthetic fixture'):g.verify_browser(self.checkout,self.output,self.b,git_required=False)
  with patch.object(g.subprocess,'run',return_value=Mock(returncode=0,stdout=self.b['assemblyRevision']+'\n')):
   with self.assertRaisesRegex(ValueError,'Synthetic fixture'):g.verify_browser(self.checkout,self.output,self.b)
  with self.assertRaisesRegex(ValueError,'Synthetic fixture'):q.verify_browser(source/'candidate',qb)
  for filename,original in [('browser-report.json',report),('production-capture.json',capture)]:
   for marker,value in [('unitFixture',False),('unitFixture',None),('fixturePurpose',''),('fixturePurpose',None)]:
    clean_report={k:v for k,v in report.items()if k not in ['unitFixture','fixturePurpose']};clean_capture={k:v for k,v in capture.items()if k not in ['unitFixture','fixturePurpose']}
    g.save(folder/'browser-report.json',clean_report);g.save(folder/'production-capture.json',clean_capture);changed=clean_report if filename=='browser-report.json'else clean_capture;changed[marker]=value;g.save(folder/filename,changed)
    with self.assertRaisesRegex(ValueError,'Synthetic fixture'):g.verify_browser(self.checkout,self.output,self.b,git_required=False)
    with self.assertRaisesRegex(ValueError,'Synthetic fixture'):q.verify_browser(source/'candidate',qb)
  g.save(folder/'browser-report.json',report);g.save(folder/'production-capture.json',capture)
  result=g.verify_browser(self.checkout,self.output,self.b,git_required=False,allow_unit_fixture=True)
  self.assertTrue(result['unitFixtureValidationPassed']);self.assertTrue(result['unitFixture']);self.assertFalse(result['automatedBrowserChecksPassed']);self.assertFalse(result['actualBrowserVerified']);self.assertNotIn('totalPNGFilesVerified',result);self.assertEqual(result['syntheticChecks']['totalPNGFilesEvaluated'],42)
  for value in [1,None,'true']:
   with self.assertRaises(ValueError):g.verify_browser(self.checkout,self.output,self.b,git_required=False,allow_unit_fixture=value)
  g.save(folder/'production-capture.json',{k:v for k,v in capture.items()if k not in ['unitFixture','fixturePurpose']})
  with self.assertRaisesRegex(ValueError,'canonical synthetic'):g.verify_browser(self.checkout,self.output,self.b,git_required=False,allow_unit_fixture=True)
 def test_sticky_overlay_observations_and_pixels_are_bounded(self):
  module,source,qb=g.check_files(self.checkout,self.b,False);report,capture=synthetic_reports(source,self.output,self.b,module,qb);folder=source/'candidate/evidence/browser';target=next(i for i,x in enumerate(capture['captures'])if x['path']=='home-1280-ribbon.png')
  mutations=[lambda h:h['before'].update(position='relative'),lambda h:h['before']['rect'].update(height=400),lambda h:h['before']['observations'][0].update(available=False),lambda h:h['before']['observations'][0].update(text='wrong'),lambda h:h['before']['observations'][0]['rect'].update(y=100),lambda h:h['after'].update(top='1px'),lambda h:h['geometryAfter'].update(scrollY=101),lambda h:h.update(path='../wrong.png'),lambda h:h.update(sha256='0'*64)]
  for mutate in mutations:
   bad=copy.deepcopy(capture);mutate(bad['captures'][target]['stickyHeader']);g.save(folder/'production-capture.json',bad)
   with self.assertRaises(ValueError):g.verify_browser(self.checkout,self.output,self.b,False,allow_unit_fixture=True)
  original_view=(folder/'home-1280-ribbon.png').read_bytes()
  for values,error in [([238]*71+[y%211 for y in range(171,944)],'Sticky header raster'),([237]*71+[0]*773,'body raster')]:
   data=png_rows(1280,values);name='home-1280-ribbon.png';(folder/name).write_bytes(data);changed=copy.deepcopy(report)
   for row in changed['screenshots']:
    if row['path']==name:row['sha256']=g.sha(data)
   g.save(folder/'browser-report.json',changed);g.save(folder/'production-capture.json',capture)
   with self.assertRaisesRegex(ValueError,error):g.verify_browser(self.checkout,self.output,self.b,False,allow_unit_fixture=True)
  (folder/'home-1280-ribbon.png').write_bytes(original_view);g.save(folder/'browser-report.json',report)
  bad=copy.deepcopy(capture);h=bad['captures'][target]['stickyHeader'];raw=png(1280,70,237);(folder/h['path']).write_bytes(raw);h['sha256']=g.sha(raw);g.save(folder/'production-capture.json',bad)
  with self.assertRaisesRegex(ValueError,'dimensions'):g.verify_browser(self.checkout,self.output,self.b,False,allow_unit_fixture=True)
  raw=png(1280,71,237);(folder/h['path']).write_bytes(raw);g.save(folder/'production-capture.json',capture);(folder/'unreviewed.png').write_text('bad')
  with self.assertRaisesRegex(ValueError,'inventory'):g.verify_browser(self.checkout,self.output,self.b,False,allow_unit_fixture=True)
 def test_social_dom_and_empty_headers_are_verified(self):
  module,source,qb=g.check_files(self.checkout,self.b,False);report,capture=synthetic_reports(source,self.output,self.b,module,qb);folder=source/'candidate/evidence/browser'
  for index in range(14):
   for change in ['missing','duplicate','value']:
    bad=copy.deepcopy(capture);social=bad['metadata'][0]['social']
    if change=='missing':social.pop(index)
    elif change=='duplicate':social.append(social[index])
    else:social[index][2]='unreviewed'
    g.save(folder/'production-capture.json',bad)
    with self.assertRaisesRegex(ValueError,'DOM metadata'):g.verify_browser(self.checkout,self.output,self.b,False,allow_unit_fixture=True)
  bad=copy.deepcopy(capture);bad['metadata'][1]['social']=capture['metadata'][0]['social'];g.save(folder/'production-capture.json',bad)
  with self.assertRaises(ValueError):g.verify_browser(self.checkout,self.output,self.b,False,allow_unit_fixture=True)
  g.save(folder/'production-capture.json',capture);headers=self.output/'_headers';headers.write_text('/*\n  X-Robots-Tag: noindex\n')
  with self.assertRaises(ValueError):g.verify_browser(self.checkout,self.output,self.b,False,allow_unit_fixture=True)
 def test_actual_package_requires_control_head_and_native_gates(self):
  env={'GITHUB_REPOSITORY':g.REPO,'GITHUB_REF':'refs/heads/main','GITHUB_ACTOR':g.OWNER,'GITHUB_TRIGGERING_ACTOR':g.OWNER,'GITHUB_RUN_ATTEMPT':'1','GITHUB_EVENT_NAME':'issues','GITHUB_SHA':'1'*40,'GITHUB_RUN_ID':'123'};event={'action':'opened','issue':{'title':g.TITLE,'number':1,'user':{'login':g.OWNER,'type':'User'}}}
  with self.assertRaisesRegex(ValueError,'native gates'):g.package_release(self.checkout,self.output,self.b,env,event)
  env['NATIVE_GATES_PASSED']='true'
  with self.assertRaisesRegex(ValueError,'control checkout HEAD'):g.package_release(self.checkout,self.output,self.b,env,event)
  self.assertFalse((self.output.parent/'release.json').exists())
 def test_real_output15_release_manifest_pure_contract(self):
  module,source,qb=g.check_files(self.checkout,self.b,False);facts=module.validate(source,self.output,self.b['assemblyRevision']);control='1'*40;run='123';manifest=module.release_manifest(facts['files'],self.b['assemblyRevision'],control,run,g.BINDING_SHA)
  module.validate_release_manifest(manifest,facts['files'],self.b['assemblyRevision'],control,run,g.BINDING_SHA);raw=module.release_manifest_bytes(manifest)
  self.assertEqual(raw,(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode());self.assertEqual(manifest['sourceBranch'],self.b['sourceBranch']);self.assertEqual(manifest['sourceContractSha256'],module.CONTRACT_SHA);self.assertEqual(manifest['revision'],self.b['assemblyRevision'])
  for key in manifest:
   bad=copy.deepcopy(manifest);bad[key]=None
   with self.assertRaises(ValueError):module.validate_release_manifest(bad,facts['files'],self.b['assemblyRevision'],control,run,g.BINDING_SHA)
 def test_real_capture_startup_reaches_socket_boundary_without_module_shadowing(self):
  # Execute the unchanged capture startup and real Handler construction. No socket or browser starts.
  import importlib.util,sys,types
  from unittest.mock import patch,Mock
  class StopBeforeSocket(RuntimeError):pass
  api=types.ModuleType('playwright.sync_api');api.sync_playwright=Mock(side_effect=AssertionError('browser_must_not_start'))
  parent=types.ModuleType('playwright');parent.sync_api=api
  with patch.dict(sys.modules,{'playwright':parent,'playwright.sync_api':api}):
   sys.modules.pop('qa_jangheung',None)
   spec=importlib.util.spec_from_file_location('jangheung_capture_startup',g.ROOT/'capture_production.py');capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)
   with patch.object(capture.socketserver,'ThreadingTCPServer',side_effect=StopBeforeSocket('socket boundary reached'))as server:
    with self.assertRaisesRegex(StopBeforeSocket,'socket boundary reached'):capture.run(self.source,self.output,self.b['assemblyRevision'])
    server.assert_called_once();self.assertEqual(server.call_args.args[0],('127.0.0.1',0));self.assertTrue(issubclass(server.call_args.args[1],capture.http.server.SimpleHTTPRequestHandler))
   api.sync_playwright.assert_not_called()
 def test_declared_fixtures_rejected_by_both_default_actual_entrypoints(self):
     report, capture = synthetic_reports(self.source,self.output,self.b,g.check_files(self.checkout,self.b,False)[0],self.b)
     originals = {'browser-report.json': report, 'production-capture.json': capture}
     clean = {name: {k: v for k, v in data.items() if k not in ['unitFixture', 'fixturePurpose']}
              for name, data in originals.items()}
     for filename in originals:
         for marker in ['unitFixture', 'fixturePurpose']:
             for value in [True, False, None, 0, 1, '', 'false', q.FIXTURE_PURPOSE, [], {}]:
                 with self.subTest(report=filename, marker=marker, value=value):
                     for name, data in clean.items():
                         g.save((self.source/'candidate/evidence/browser') / name, {**data, **({marker: value} if name == filename else {})})
                     with patch.object(g.subprocess, 'run', return_value=Mock(returncode=0, stdout=self.b['assemblyRevision']+'\n')):
                         with self.assertRaisesRegex(ValueError, 'fixture markers forbidden'):
                             g.verify_browser(self.checkout, self.output, self.b)
                     with self.assertRaisesRegex(ValueError, 'fixture markers forbidden'):
                         q.verify_browser(self.source / 'candidate', self.b)
 def test_fixture_mode_requires_explicit_boolean_and_canonical_pair(self):
     report, capture = synthetic_reports(self.source,self.output,self.b,g.check_files(self.checkout,self.b,False)[0],self.b)
     originals = {'browser-report.json': report, 'production-capture.json': capture}
     for value in [None, 0, 1, 'true', [], {}]:
         with self.subTest(argument=value):
             with self.assertRaisesRegex(ValueError, 'boolean test-only'):
                 g.verify_browser(self.checkout, self.output, self.b, False, allow_unit_fixture=value)
             with self.assertRaisesRegex(ValueError, 'boolean test-only'):
                 q.verify_browser(self.source / 'candidate', self.b, allow_unit_fixture=value)
     for filename in originals:
         for key, value in [('unitFixture', False), ('unitFixture', 1), ('unitFixture', None),
                            ('fixturePurpose', ''), ('fixturePurpose', None), ('fixturePurpose', 'actual')]:
             for name, data in originals.items():
                 g.save((self.source/'candidate/evidence/browser') / name, {**data, **({key: value} if name == filename else {})})
             with self.subTest(report=filename, key=key, value=value):
                 with self.assertRaisesRegex(ValueError, 'canonical synthetic markers'):
                     g.verify_browser(self.checkout, self.output, self.b, False, allow_unit_fixture=True)
                 with self.assertRaisesRegex(ValueError, 'canonical synthetic markers'):
                     q.verify_browser(self.source / 'candidate', self.b, allow_unit_fixture=True)
     for name, data in originals.items():
         g.save((self.source/'candidate/evidence/browser') / name, data)
     result = q.verify_browser(self.source / 'candidate', self.b, allow_unit_fixture=True)
     self.assertTrue(result['unitFixtureValidationPassed'])
     self.assertFalse(result['automatedBrowserChecksPassed'])
     self.assertFalse(result['actualBrowserVerified'])
     self.assertNotIn('localMissingRouteHTTPStatus', result)
     self.assertEqual(result['syntheticChecks']['screenshots'], 34)
 def test_synthetic_report_negative_dom_images_interactions_http_and_boundaries(self):
     report, _ = synthetic_reports(self.source,self.output,self.b,g.check_files(self.checkout,self.b,False)[0],self.b)
     mutations = [
         lambda r: r.update(status='PASS'), lambda r: r.update(origin='public'),
         lambda r: r.update(widths=[390]), lambda r: r.update(pages=1),
         lambda r: r.update(browserVersion='unknown'), lambda r: r.update(checkedAtUTC='2026-10-16'),
         lambda r: r['states'].pop(), lambda r: r['states'][0].update(route='/wrong'),
         lambda r: r['states'][0].update(failures=['hidden']),
         lambda r: r['states'][0].update(bodyExact=False),
         lambda r: r['states'][0].update(scrollWidth=321),
         lambda r: r['states'][0]['observations'].pop(),
         lambda r: r['states'][0]['links'].pop(),
         lambda r: r['states'][0].update(manuscriptSHA256='0'*64),
         lambda r: r['states'][0]['structure']['sectionIDs'].reverse(),
         lambda r: r['states'][0]['structure']['bannerPlacements'][0].update(previousSection='locations'),
         lambda r: r['states'][1].update(structure={}),
         lambda r: r['states'][0]['links'][0].update(href='https://wrong.invalid'),
         lambda r: r['states'][0]['links'][0].update(ariaLabel='wrong'),
         lambda r: r['states'][0]['observations'][0].update(text='changed'),
         lambda r: r['states'][0]['observations'][0].update(tag='div'),
         lambda r: r['states'][0]['observations'][0].update(href='https://example.invalid/'),
         lambda r: r['states'][0]['observations'][0].update(available=False),
         lambda r: r['states'][0]['observations'][0]['rect'].update(width=0),
         lambda r: r['imageAspectChecks'].pop(),
         lambda r: r['imageAspectChecks'][0].update(objectFit='cover'),
         lambda r: r['imageAspectChecks'][0].update(naturalWidth=1),
         lambda r: r['imageAspectChecks'][0].update(displayWidth=500),
         lambda r: r['imageAspectChecks'][0].update(displayHeight=1),
         lambda r: r['scrollReachability'][0]['rect'].update(y=844),
         lambda r: r['scrollReachability'][0]['rect'].update(x=-2),
         lambda r: r['interactions'][0].update(**{'pass': False}),
         lambda r: r['touchTargets'][0].update(height=43),
         lambda r: r['touchTargets'][0].update(href='wrong'),
         lambda r: r['touchTargets'][0].update(ariaLabel='wrong'),
         lambda r: r.update(purchaseVisibilityMutations=[]),
         lambda r: r['touchTargets'][0].update(widthPx=43),
         lambda r: r.update(computedVisibilityMutationDetected=False),
         lambda r: r.update(localMissingRouteStatus=200),
         lambda r: r.update(externalRequestsBlocked=['https://example.invalid/']),
         lambda r: r.update(pageErrors=['error']),
         lambda r: r.update(externalCTAAndPhoneActivated=True),
         lambda r: r.update(publicHTTPVerified=True),
         lambda r: r.update(independentImplementationReview=True),
         lambda r: r.update(responses=[]),
         lambda r: r['responses'][0].update(path='//remote.invalid/file'),
         lambda r: r['responses'][0].update(status=500),
         lambda r: r['screenshots'].pop(),
         lambda r: r['screenshots'][0].update(path='../wrong.png'),
         lambda r: r['screenshots'][0].update(sha256='0' * 64),
     ]
     for i, mutate in enumerate(mutations):
         with self.subTest(report_mutation=i):
             bad = copy.deepcopy(report)
             mutate(bad)
             g.save((self.source/'candidate/evidence/browser') / 'browser-report.json', bad)
             with self.assertRaises(ValueError):
                 q.verify_browser(self.source / 'candidate', self.b, allow_unit_fixture=True)
 def test_general_eligibility_viewport_and_two_fee_contract(self):
     report,capture=synthetic_reports(self.source,self.output,self.b,g.check_files(self.checkout,self.b,False)[0],self.b)
     target=next(i for i,c in enumerate(capture['captures'])if c['path']=='home-320-eligibility.png')
     mutations=[lambda o:o.update(scope='hospital'),lambda o:o.update(screenshotSHA256='0'*64),
                lambda o:o['after'].update(fragment=''),lambda o:o['before'].update(productAdjacent=False),
                lambda o:o['before'].update(fragment=''),lambda o:o['before'].update(hospitalRestrictionElements=1),
                lambda o:o['before'].update(selectedHospitalElements=1),lambda o:o['before']['products'][0].update(sumElements=1),
                lambda o:o['before']['products'][0].update(href='wrong'),lambda o:o['before']['products'][0].update(ctaHref='wrong'),
                lambda o:o['before']['products'][0].update(shippingLabel='배송비 없음'),
                lambda o:o['before']['productNotice'].update(text='모든 시설 반입 금지'),lambda o:o['before']['productNotice'].update(available=False),
                lambda o:o['before']['productNotice']['ancestors'][0].update(display='none'),lambda o:o['before']['productNotice']['ancestors'][0].update(visibility='hidden'),
                lambda o:o['before']['productNotice']['ancestors'][0].update(opacity='0'),lambda o:o['before']['productNotice']['ancestors'][0].update(hidden=True),
                lambda o:o['before']['productNotice']['ancestors'][0].update(inert=True),lambda o:o['before']['productNotice']['ancestors'][0].update(ariaHidden='true'),
                lambda o:o['before']['productNotice'].update(ancestors=[]),lambda o:o['before']['productNotice']['rect'].update(height=900),
                lambda o:o['before']['productNotice']['rect'].update(y=-1.1),lambda o:o['before']['productNotice']['rect'].update(x=-2),
                lambda o:o['before']['productHeading']['rect'].update(y=400),lambda o:o['before']['productCards']['rect'].update(y=200)]
     for i,mutate in enumerate(mutations):
         with self.subTest(purchase_mutation=i):
             bad=copy.deepcopy(capture);o=bad['captures'][target]['purchaseSnapshot'];mutate(o)
             if i!=2:o['after']=copy.deepcopy(o['before'])
             g.save((self.source/'candidate/evidence/browser')/'production-capture.json',bad)
             with self.assertRaises(ValueError):g.verify_browser(self.checkout,self.output,self.b,False,allow_unit_fixture=True)
     g.save((self.source/'candidate/evidence/browser')/'production-capture.json',capture)
     result=g.verify_browser(self.checkout,self.output,self.b,False,allow_unit_fixture=True)
     self.assertEqual(result['syntheticChecks']['purchaseViewportSnapshotsEvaluated'],3)
     for width in [320,390,1280]:
         good=synthetic_purchase(self.b['browserExpected']['purchase'],width,'eligibility')
         self.assertTrue(q.verify_purchase(good,self.b['browserExpected']['purchase'],width,'eligibility')['completeNoticeInViewport'])
         for field,value in [('y',69 if width==1280 else -2),('height',900)]:
             bad=copy.deepcopy(good);bad['productNotice']['rect'][field]=value
             with self.assertRaises(ValueError):q.verify_purchase(bad,self.b['browserExpected']['purchase'],width,'eligibility')
 def test_all58_source_bytes_frozen(self):
  for row in self.b['files']:
   p=self.checkout/row['path'];raw=p.read_bytes();p.write_bytes(raw+b'\n')
   with self.subTest(path=row['path']),self.assertRaises(ValueError):g.check_files(self.checkout,self.b,False)
   p.write_bytes(raw)
 def test_all15_output_bytes_frozen(self):
  module,source,_=g.check_files(self.checkout,self.b,False)
  for p in sorted(self.output.rglob('*')):
   if not p.is_file():continue
   raw=p.read_bytes();p.write_bytes(raw+b'\n')
   with self.subTest(path=p.relative_to(self.output)),self.assertRaises(ValueError):module.validate(source,self.output,self.b['assemblyRevision'])
   p.write_bytes(raw)
 def test_workflow_exact_owner_and_nonmatching_concurrency(self):
  workflow=(g.ROOT.parents[2]/'.github/workflows/jangheung-production-build-only.yml').read_text()
  self.assertIn("format('jangheung-production-nonmatching-{0}', github.run_id)",workflow)
  self.assertEqual(workflow.count("github.event.issue.title == '[JANGHEUNG-PRODUCTION-BUILD] source58-20261017'"),2)
  self.assertIn('cancel-in-progress: false',workflow);self.assertIn('contents: read',workflow)
  self.assertEqual(workflow.count('github.rest.git.getRef'),2);self.assertEqual(workflow.count("['source/jangheung-private-qa-20261016',b.privateSourceRevision]"),2)
  self.assertIn('ref: ${{ github.sha }}',workflow);self.assertIn('all27 home viewport pixel comparisons',workflow)
  for forbidden in ['CLOUDFLARE_API_TOKEN','INDEXNOW_KEY','contents: write','pull_request_target','workflow_dispatch','curl ','wrangler']:self.assertNotIn(forbidden,workflow)


 def test_capture_locators_faq_predicate_and_404_bind_actual_output(self):
  import ast
  from html.parser import HTMLParser
  from types import SimpleNamespace
  class Surface(HTMLParser):
   def __init__(self,raw):super().__init__();self.nodes=[];self.stack=[];self.faq=[];self.nav=[];self.feed(raw)
   def handle_starttag(self,tag,attrs):
    d=dict(attrs);inside=any(x[1]for x in self.stack)or d.get('id')=='questions';nav=any(x[0]=='nav'for x in self.stack);self.nodes.append((tag,d))
    if inside and 'data-copy-key'in d:self.faq.append(d['data-copy-key'])
    if tag=='a'and nav:self.nav.append(d.get('href'))
    if tag not in ['meta','link','img','br','hr','input','source','wbr']:self.stack.append((tag,inside))
   def handle_endtag(self,tag):
    for i in range(len(self.stack)-1,-1,-1):
     if self.stack[i][0]==tag:del self.stack[i:];break
  home=Surface((self.output/'index.html').read_text());notfound=Surface((self.output/'404.html').read_text());code=(g.ROOT/'capture_production.py').read_text();tree=ast.parse(code)
  node=next(n for n in ast.walk(tree)if isinstance(n,ast.For)and isinstance(n.target,ast.Tuple)and [x.id for x in n.target.elts if isinstance(x,ast.Name)]==['label','selector'])
  selectors=ast.literal_eval(node.iter);self.assertEqual([x[0]for x in selectors],list(g.STICKY_SECTIONS))
  for label,selector in selectors:
   matched=[d for tag,d in home.nodes if d.get('id')==selector[1:]]if selector.startswith('#')else[d for tag,d in home.nodes if selector[1:]in d.get('class','').split()]
   self.assertEqual(len(matched),1,(label,selector))
  expected=lambda route:self.b['browserExpected']['occurrences'][route]
  want=[x['key']for x in expected('/')if x['key']=='section.questions.heading'or x['key'].startswith('question-')];self.assertEqual(home.faq,want)
  assertion=next(n for n in ast.walk(tree)if isinstance(n,ast.Assert)and "set(bad['failures'])"in ast.unparse(n.test))
  expr=compile(ast.Expression(assertion.test),'<capture-faq-bound-predicate>','eval')
  self.assertTrue(eval(expr,{},dict(bad={'failures':home.faq},expected=expected)))
  for keys in [home.faq[:-1],home.faq+['unreviewed']]:self.assertFalse(eval(expr,{},dict(bad={'failures':keys},expected=expected)))
  ui=json.loads((self.source/'inputs/author/display-copy.json').read_text())['siteUI'];origin='http://127.0.0.1:12345'
  self.assertEqual(notfound.nav[0],'/'+ui['navigation'][0]['href']);self.assertEqual(notfound.nav[0],'/#products-cost')
  assertion=next(n for n in ast.walk(tree)if isinstance(n,ast.Assert)and "page.url"in ast.unparse(n.test)and "U['navigation'][0]['href']"in ast.unparse(n.test));expr=compile(ast.Expression(assertion.test),'<capture-404-bound-anchor>','eval')
  self.assertTrue(eval(expr,{},dict(page=SimpleNamespace(url=origin+notfound.nav[0]),origin=origin,U=ui)))
  self.assertFalse(eval(expr,{},dict(page=SimpleNamespace(url=origin+'/#budget'),origin=origin,U=ui)))

if __name__=='__main__':unittest.main()
