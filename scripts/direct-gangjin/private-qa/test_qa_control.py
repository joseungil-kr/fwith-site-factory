"""Local-only controller tests: actual source48/output11; synthetic browser fixtures.

Every browser report and PNG constructed here is a UNIT FIXTURE, never actual
browser, HTTP, screenshot-review or deployment evidence. No socket is opened,
no browser starts, and no remote service is called. Production packaging and
source50/output15 contracts intentionally do not apply to this private control.

GANGJIN_PRIVATE_CHECKOUT names the checkout (or, for local-only testing, its
source prefix). GANGJIN_UNIT_LOCAL_ONLY=1 permits a downloaded local source tree
without git. It does not weaken the controller CLI's default git requirement.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import types
import unittest
import zlib
from unittest.mock import Mock, patch

import qa_control as g
import browser_evidence as q


def chunk(kind, payload):
    return (struct.pack('>I', len(payload)) + kind + payload
            + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff))


def encoded_png(width, height, raw, color=2, depth=8, interlace=0):
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, depth,
                                        color, 0, 0, interlace))
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def png_rows(width, values):
    return encoded_png(width, len(values),
                       b''.join(b'\0' + bytes([v]) * (width * 3) for v in values))


def png(width, height, value=0):
    return png_rows(width, [value] * height)


def synthetic_restriction(expected,width,scope):
    """Deliberately synthetic DOM/style geometry, never an actual observation."""
    style=dict(display='block',visibility='visible',opacity='1',hidden=False,inert=False,ariaHidden=None)
    def node(text,tag,y,height,href=None):
        return dict(text=text,tag=tag,href=href,available=True,
                    rect=dict(x=16,y=y,width=width-32,height=height),ancestors=[dict(style)])
    return dict(fragment=''if scope=='restriction'else'#products-cost',
                hero=node(expected['heroText']+expected['heroSourceLabel'],'div',90,150),
                heroText=node(expected['heroText'],'p',90,80),
                heroSource=node(expected['heroSourceLabel'],'a',180,44,expected['heroSourceHref']),
                heroActions=copy.deepcopy(expected['heroActions']),heroBeforeActions=True,productProse=copy.deepcopy(expected['productProse']),
                productHeading=node(expected['productHeading'],'h2',90,50),
                productNotice=node(expected['productText'],'p',150,150),
                productCards=node('synthetic cards','div',310,500),productAdjacent=True,
                products=[dict(p,ctaHref=p['href'],ctaLabel=p['label'],sumElements=0)for p in expected['products']],
                selectedHospitalElements=0)


def synthetic_reports(source, dist, binding):
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
                               links=copy.deepcopy(fixture['allLinks'][route]),manuscriptSHA256=fixture['copyBinding']['manuscriptSHA256'],structure=copy.deepcopy(fixture['structure'])if route=='/'else None))
            interactions.append(dict(width=width, route=route,
                                     test='keyboard skip focuses main', **{'pass': True}))
            metadata.append(dict(width=width, route=route, robots='noindex,nofollow',
                                 canonical=[], productionMetadata=[], social=[]))
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
        scope='restriction'if name.endswith('-restriction.png')else'products'if name.endswith('-products.png')else None
        if scope:
            observed=synthetic_restriction(fixture['restriction'],width,scope)
            cap['restrictionSnapshot']=dict(scope=scope,before=observed,after=copy.deepcopy(observed),screenshotSHA256=g.sha((folder/name).read_bytes()))
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
                  restrictionVisibilityMutations=[{'selector':selector,'rule':rule,'detected':True}for selector in ['#maryang-restriction','.product-eligibility']for rule in ['display:none','visibility:hidden','opacity:0']],
                  localMissingRouteStatus=404,
                  responses=[dict(path=n, status=200) for n in sorted(paths)]
                            + [dict(path='/.gangjin-private-missing/', status=404)],
                  externalRequestsBlocked=[], pageErrors=[], externalCTAAndPhoneActivated=False,
                  publicHTTPVerified=False, independentImplementationReview=False,
                  screenshots=screenshots)
    http_rows = []
    for name, raw in sorted(g.inventory(dist).items()):
        path = '/' if name == 'index.html' else '/' + name
        mime = ('text/html' if name.endswith('.html') else 'text/css' if name.endswith('.css')
                else 'text/plain' if name.endswith('.txt') else 'image/jpeg'
                if name.endswith('.jpg') else 'image/webp')
        http_rows.append(dict(path=path, status=200, sha256=g.sha(raw), bytes=len(raw),
                              contentType=mime, finalURLPath=path))
    missing = (dist / '404.html').read_bytes()
    capture = dict(unitFixture=True, fixturePurpose='SYNTHETIC_UNIT_TEST_NOT_ACTUAL_QA_EVIDENCE',
                   sourceRevision=binding['sourceRevision'], origin='loopback-only',
                   captures=captures, metadata=metadata, httpFiles=http_rows,
                   missingRoute=dict(path='/.gangjin-private-missing/', status=404,
                                     sha256=g.sha(missing), bytes=len(missing),
                                     robots='noindex,nofollow', canonicalCount=0),
                   publicHTTPVerified=False, publicationReady=False)
    g.save(folder / 'browser-report.json', report)
    g.save(folder / 'private-capture.json', capture)
    return report, capture


class ControlTests(unittest.TestCase):
    def test_bound_identity_and_fail_closed_binding(self):
        valid = g.binding()
        self.assertEqual(valid['sourceFiles'], 48)
        self.assertEqual(len(valid['expectedDistFiles']), 11)
        self.assertEqual(valid['facilityPages'], 'HOLD')
        self.assertEqual(valid['phase'], 'BOUND_REMOTE_SOURCE48')
        self.assertEqual(valid['sourceRevision'], g.SOURCE_REVISION)
        mutations = [
            lambda b: b.update(repository='other/repo'), lambda b: b.update(owner='other'),
            lambda b: b.update(sourceBranch='main'), lambda b: b.update(sourcePrefix='../other'),
            lambda b: b.update(sourceFiles=45), lambda b: b['files'].pop(),
            lambda b: b['files'][0].update(bytes=0),
            lambda b: b['files'][0].update(sha256='0' * 64),
            lambda b: b['files'][0].update(gitBlobSHA='not-a-git-blob'),
            lambda b: b.update(sourceManifestSHA256='0' * 64),
            lambda b: b.update(sourceManifestUTF8=b['sourceManifestUTF8'] + ' '),
            lambda b: b.update(sourceZIP_SHA256='0' * 64),
            lambda b: b.update(permissions={'contents': 'write'}),
            lambda b: b.update(facilityPages='PUBLISH'), lambda b: b.update(facilityPageCount=8),
            lambda b: b.update(copyCharacters=2824), lambda b: b.update(shippingKRW=20000),
            lambda b: b.update(browserExpectedSHA256='0' * 64),
            lambda b: b['browserExpected']['widths'].append(1920),
            lambda b: b.update(expectedDistFilesSHA256='0' * 64),
            lambda b: b['expectedDistFiles'].pop('robots.txt'),
            lambda b: b['staticReview'].update(sha256='0' * 64),
            lambda b: b['staticReview'].update(manifestSHA256='0' * 64),
            lambda b: b.update(captureSHA256='0' * 64),
            lambda b: b.update(browserEvidenceSHA256='0' * 64),
        ]
        mutations.extend(lambda b, k=k: b.update({k: True}) for k in [
            'providerWrites', 'productionEnabled', 'indexNowEnabled',
            'newCredentials', 'remoteGitWrites', 'publicationReady'])
        original_safe = g.safe_file
        for i, mutate in enumerate(mutations):
            with self.subTest(mutation=i):
                bad = copy.deepcopy(valid)
                mutate(bad)
                raw = json.dumps(bad, ensure_ascii=False).encode()
                file = Mock()
                file.read_bytes.return_value = raw
                with patch.object(g, 'safe_file', side_effect=lambda root, rel:
                                  file if root == g.ROOT and rel == 'bindings.json'
                                  else original_safe(root, rel)), patch.object(g, 'BINDING_SHA', g.sha(raw)):
                    with self.assertRaises(ValueError):
                        g.binding(False)
        with patch.object(g, 'BINDING_SHA', '0' * 64):
            with self.assertRaisesRegex(ValueError, 'binding'):
                g.binding(False)

    def test_bound_remote_receipt_and_byte_readback_semantics(self):
        valid = g.binding()
        for key, value in [('phase', 'UNBOUND_REMOTE_SAVE_PENDING'),
                           ('sourceRevision', 'f' * 40)]:
            bad = copy.deepcopy(valid)
            bad[key] = value
            with self.subTest(binding=key), self.assertRaises(ValueError):
                g.validate_binding(bad)
        for name in ['remoteSaveVerification', 'remoteSourceReadback', 'independentRemoteSourceReview']:
            bad = copy.deepcopy(valid)
            bad[name]['sha256'] = '0' * 64
            with self.subTest(reference=name), self.assertRaises(ValueError):
                g.validate_binding(bad)
        for key, value in [('manifestSHA256', '0' * 64), ('rawUTF8', '{}')]:
            bad = copy.deepcopy(valid)
            bad['independentRemoteSourceReview'][key] = value
            with self.subTest(independentReview=key), self.assertRaises(ValueError):
                g.validate_binding(bad)
        for key, value in [('commit', 'f' * 40), ('branch', 'main'),
                           ('sourceManifestSHA256', '0' * 64), ('sourceFiles', 45),
                           ('source48UnchangedAfterBuild', False), ('acceptedOutput11DirectByteParity', False),
                           ('mainWrites', 1), ('providerWrites', 1), ('publicationReady', True),
                           ('readbackManifestSHA256', '0' * 64)]:
            bad = copy.deepcopy(valid)
            receipt = json.loads(bad['remoteSaveVerification']['rawUTF8'])
            receipt[key] = value
            raw = json.dumps(receipt, ensure_ascii=False)
            bad['remoteSaveVerification'].update(rawUTF8=raw, sha256=g.sha(raw.encode()))
            with self.subTest(receipt=key), self.assertRaises(ValueError):
                g.validate_binding(bad)
        mutations = [lambda r: r.update(commit='f' * 40),
                     lambda r: r.update(branch='main'), lambda r: r.update(fileCount=46),
                     lambda r: r.update(allFilesMatchAcceptedSource=False),
                     lambda r: r['files'].pop(),
                     lambda r: r['files'][0].update(sha256='0' * 64),
                     lambda r: r['files'][0].update(bytes=0),
                     lambda r: r['files'][0].update(path='../outside')]
        for i, mutate in enumerate(mutations):
            bad = copy.deepcopy(valid)
            back = json.loads(bad['remoteSourceReadback']['rawUTF8'])
            mutate(back)
            raw = json.dumps(back, ensure_ascii=False)
            digest = g.sha(raw.encode())
            bad['remoteSourceReadback'].update(rawUTF8=raw, sha256=digest)
            receipt = json.loads(bad['remoteSaveVerification']['rawUTF8'])
            receipt['readbackManifestSHA256'] = digest
            raw = json.dumps(receipt, ensure_ascii=False)
            bad['remoteSaveVerification'].update(rawUTF8=raw, sha256=g.sha(raw.encode()))
            with self.subTest(readback=i), self.assertRaises(ValueError):
                g.validate_binding(bad)

    def test_owner_boundary(self):
        env = dict(GITHUB_REPOSITORY=g.REPO, GITHUB_REF='refs/heads/main',
                   GITHUB_ACTOR=g.OWNER, GITHUB_TRIGGERING_ACTOR=g.OWNER,
                   GITHUB_RUN_ATTEMPT='1', GITHUB_EVENT_NAME='issues',
                   GITHUB_SHA='1' * 40, GITHUB_RUN_ID='123')
        event = {'action': 'opened', 'issue': {'title': g.TITLE, 'number': 1,
                                             'user': {'login': g.OWNER, 'type': 'User'}}}
        self.assertEqual(g.owner(env, event)['issueNumber'], 1)
        for key in env:
            for value in ['', 'wrong']:
                with self.subTest(environment=key, value=value):
                    bad = dict(env)
                    bad[key] = value
                    with self.assertRaises(ValueError):
                        g.owner(bad, event)
        mutations = [lambda e: e.update(action='edited'),
                     lambda e: e['issue'].update(title='wrong'),
                     lambda e: e['issue']['user'].update(login='other'),
                     lambda e: e['issue']['user'].update(type='Bot'),
                     lambda e: e['issue'].pop('number')]
        mutations.extend(lambda e, n=n: e['issue'].update(number=n)
                         for n in [0, -1, True, '1', None])
        for i, mutate in enumerate(mutations):
            with self.subTest(event_mutation=i):
                bad = copy.deepcopy(event)
                mutate(bad)
                with self.assertRaises(ValueError):
                    g.owner(env, bad)

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

    def test_path_guards(self):
        with tempfile.TemporaryDirectory(prefix='gangjin-unit-path-') as tmp:
            root = Path(tmp)
            (root / 'file').write_bytes(b'fixture')
            (root / 'link').symlink_to(root / 'file')
            (root / 'linked-dir').symlink_to(root, target_is_directory=True)
            for safe in [g.safe_file, q.safe_file]:
                self.assertEqual(safe(root, 'file').read_bytes(), b'fixture')
                for rel in ['', '../file', '/file', 'a/../../file', 'a\\file',
                            'link', 'linked-dir/file', 'missing', '.']:
                    with self.subTest(guard=safe.__module__, path=rel):
                        with self.assertRaises(ValueError):
                            safe(root, rel)
                with self.assertRaises(ValueError):
                    safe(root / 'linked-dir', 'file')

    def test_geometry_guards(self):
        good = dict(scrollX=0, scrollY=0, width=390, height=844,
                    documentHeight=1000, fontStatus='loaded')
        self.assertEqual(g.verify_geometry(good, 390, 844), good)
        for key, value in [('scrollX', 1), ('scrollX', True), ('scrollY', float('nan')),
                           ('scrollY', float('inf')), ('scrollY', True), ('scrollY', -.5),
                           ('scrollY', .5), ('width', 320), ('height', 600),
                           ('documentHeight', 500), ('documentHeight', False),
                           ('fontStatus', 'loading')]:
            with self.subTest(field=key, value=value):
                bad = dict(good)
                bad[key] = value
                with self.assertRaises(ValueError):
                    g.verify_geometry(bad, 390, 844)
        with self.assertRaises(ValueError):
            g.verify_geometry({**good, 'extra': 1}, 390, 844)

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


class RealSourceAndSyntheticObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b = g.binding()
        if 'GANGJIN_PRIVATE_CHECKOUT' not in os.environ:
            raise unittest.SkipTest('Source stage requires explicit GANGJIN_PRIVATE_CHECKOUT; controller tests still ran')
        checkout = Path(os.environ['GANGJIN_PRIVATE_CHECKOUT']).resolve()
        cls.original = checkout / g.PREFIX if (checkout / g.PREFIX).is_dir() else checkout
        cls.original_dist = cls.original / 'candidate/dist'
        if os.environ.get('GANGJIN_UNIT_LOCAL_ONLY') == '1':
            # No fabricated .git: this opt-in applies only to unit fixtures.
            g.check_source_files(cls.original, cls.b, postbuild=True)
        else:
            g.binding()
            g.check_files(checkout, cls.b, postbuild=True)
        g.check_dist(cls.original_dist, cls.b)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='gangjin-synthetic-unit-only-')
        self.root = Path(self.tmp.name)
        self.checkout = self.root / 'checkout'
        self.source = self.checkout / g.PREFIX
        for row in self.b['files']:
            path = self.source / row['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((self.original / row['path']).read_bytes())
        self.dist = self.source / 'candidate/dist'
        shutil.copytree(self.original_dist, self.dist)
        self.folder = self.source / 'candidate/evidence/browser'

    def tearDown(self):
        self.tmp.cleanup()

    def test_real_source48_output11_and_static_gate(self):
        result = g.check_files(self.checkout, self.b, git_required=False, postbuild=True)
        self.assertEqual(result['verifiedSourceFiles'], 48)
        self.assertTrue(result['sourceBytesUnchanged'])
        self.assertEqual(g.check_dist(self.dist, self.b)['distFiles'], 11)
        original_path = sys.path[:]
        try:
            sys.path.insert(0, str(self.source / 'candidate/scripts'))
            with patch.dict(sys.modules):
                sys.modules.pop('html_surface', None)
                spec = importlib.util.spec_from_file_location('gangjin_unit_static',
                                                              self.source / 'candidate/scripts/qa_gangjin.py')
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                facts = module.verify(self.dist)
                self.assertEqual(facts['checks'], 322)
                self.assertEqual(len(facts['files']), 11)
                self.assertFalse(facts['browserExecuted'])
                self.assertFalse(facts['publicHTTPVerified'])
                self.assertFalse(facts['publicationReady'])
                self.assertEqual(module.expected('/'), self.b['browserExpected']['occurrences']['/'])
                self.assertEqual(module.expected('/404.html'), self.b['browserExpected']['occurrences']['/404.html'])
                faq_keys = [row['key'] for row in module.expected('/')
                            if row['key'] == 'section.questions.heading'
                            or row['key'].startswith('question-')]
                self.assertEqual(len(faq_keys), 10)
        finally:
            sys.path[:] = original_path

    def test_default_git_head_and_prebuild_inventory_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'checkout HEAD'):
            g.check_files(self.checkout, self.b)
        process = subprocess.run([sys.executable, '-B', str(g.ROOT / 'qa_control.py'),
                                  'prebuild', '--checkout', str(self.checkout)],
                                 capture_output=True, text=True)
        self.assertNotEqual(process.returncode, 0)
        self.assertIn('Actual checkout HEAD mismatch', process.stderr)
        with self.assertRaisesRegex(ValueError, 'inventory'):
            g.check_files(self.checkout, self.b, git_required=False)
        shutil.rmtree(self.dist)
        self.assertEqual(g.check_files(self.checkout, self.b, False)['verifiedSourceFiles'], 48)

    def test_every_source_file_bytes_are_frozen(self):
        for row in self.b['files']:
            path = self.source / row['path']
            original = path.read_bytes()
            with self.subTest(source=row['path']):
                path.write_bytes(original + b'\n')
                with self.assertRaisesRegex(ValueError, 'Source byte mismatch'):
                    g.check_files(self.checkout, self.b, False, postbuild=True)
            path.write_bytes(original)

    def test_source_inventory_nested_generated_names_and_symlinks(self):
        for name in ['extra.py', 'candidate/src/evidence/unreviewed.py',
                     'candidate/src/dist/unreviewed.py', 'inputs/node_modules/unreviewed.py',
                     'candidate/scripts/__pycache__/unreviewed.cpython-311.pyc']:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'unreviewed unit fixture')
            with self.subTest(extra=name):
                with self.assertRaises(ValueError):
                    g.check_files(self.checkout, self.b, False, postbuild=True)
            path.unlink()
        path = self.source / self.b['files'][0]['path']
        original = path.read_bytes()
        path.unlink()
        with self.assertRaises(ValueError):
            g.check_files(self.checkout, self.b, False, postbuild=True)
        outside = self.root / 'same-bytes'
        outside.write_bytes(original)
        path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            g.check_files(self.checkout, self.b, False, postbuild=True)

    def test_source_and_output_root_symlinks_fail_closed(self):
        source_link = self.root / 'source-link'
        source_link.symlink_to(self.source, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink root'):
            g.check_source_files(source_link, self.b, postbuild=True)
        dist_link = self.root / 'dist-link'
        dist_link.symlink_to(self.dist, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Regular output directory required'):
            g.check_dist(dist_link, self.b)

    def test_output11_rejects_all_byte_changes_missing_extra_and_symlink(self):
        for name in self.b['expectedDistFiles']:
            path = self.dist / name
            raw = path.read_bytes()
            with self.subTest(output=name):
                path.write_bytes(raw + b'\n')
                with self.assertRaises(ValueError):
                    g.check_dist(self.dist, self.b)
            path.write_bytes(raw)
        path = self.dist / 'robots.txt'
        raw = path.read_bytes()
        path.unlink()
        with self.assertRaises(ValueError):
            g.check_dist(self.dist, self.b)
        path.write_bytes(raw)
        for name in ['sitemap.xml', '_headers', 'extra-route/index.html']:
            extra = self.dist / name
            extra.parent.mkdir(parents=True, exist_ok=True)
            extra.write_bytes(b'unreviewed')
            with self.assertRaises(ValueError):
                g.check_dist(self.dist, self.b)
            extra.unlink()
        path.unlink()
        outside = self.root / 'same-robots'
        outside.write_bytes(raw)
        path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            g.check_dist(self.dist, self.b)

    def test_synthetic_complete_contract_is_not_actual_browser_acceptance(self):
        report, capture = synthetic_reports(self.source, self.dist, self.b)
        self.assertTrue(report['unitFixture'] and capture['unitFixture'])
        result = g.verify_browser(self.checkout, self.dist, self.b, git_required=False, allow_unit_fixture=True)
        self.assertTrue(result['unitFixture'])
        self.assertEqual(result['fixturePurpose'], q.FIXTURE_PURPOSE)
        self.assertTrue(result['unitFixtureValidationPassed'])
        self.assertFalse(result['automatedBrowserChecksPassed'])
        self.assertFalse(result['actualBrowserVerified'])
        self.assertFalse(result['publicHTTPVerified'])
        self.assertFalse(result['publicationReady'])
        self.assertEqual(result['independentScreenshotReview'], 'NOT_APPLICABLE_SYNTHETIC_UNIT_FIXTURE')
        self.assertNotIn('privateHTTPFilesVerified', result)
        self.assertNotIn('totalPNGFilesVerified', result)
        synthetic = result['syntheticChecks']
        self.assertEqual(synthetic['stableCapturesEvaluated'], 34)
        self.assertEqual(synthetic['stickyHeaderReferencesEvaluated'], 8)
        self.assertEqual(synthetic['totalPNGFilesEvaluated'], 42)
        self.assertEqual(synthetic['privateHTTPFilesEvaluated'], 11)
        self.assertEqual(synthetic['privateMetadataStatesEvaluated'], 6)
        self.assertEqual(len(synthetic['homeViewportFullPixelComparisons']), 27)
        self.assertEqual(sum(x['stickyReferenceRows'] for x in synthetic['homeViewportFullPixelComparisons']), 8 * 71)

    def test_declared_fixtures_rejected_by_both_default_actual_entrypoints(self):
        report, capture = synthetic_reports(self.source, self.dist, self.b)
        originals = {'browser-report.json': report, 'private-capture.json': capture}
        clean = {name: {k: v for k, v in data.items() if k not in ['unitFixture', 'fixturePurpose']}
                 for name, data in originals.items()}
        for filename in originals:
            for marker in ['unitFixture', 'fixturePurpose']:
                for value in [True, False, None, 0, 1, '', 'false', q.FIXTURE_PURPOSE, [], {}]:
                    with self.subTest(report=filename, marker=marker, value=value):
                        for name, data in clean.items():
                            g.save(self.folder / name, {**data, **({marker: value} if name == filename else {})})
                        with patch.object(g.subprocess, 'run', return_value=Mock(returncode=0, stdout=self.b['sourceRevision']+'\n')):
                            with self.assertRaisesRegex(ValueError, 'fixture markers forbidden'):
                                g.verify_browser(self.checkout, self.dist, self.b)
                        with self.assertRaisesRegex(ValueError, 'fixture markers forbidden'):
                            q.verify_browser(self.source / 'candidate', self.b)

    def test_fixture_mode_requires_explicit_boolean_and_canonical_pair(self):
        report, capture = synthetic_reports(self.source, self.dist, self.b)
        originals = {'browser-report.json': report, 'private-capture.json': capture}
        for value in [None, 0, 1, 'true', [], {}]:
            with self.subTest(argument=value):
                with self.assertRaisesRegex(ValueError, 'boolean test-only'):
                    g.verify_browser(self.checkout, self.dist, self.b, False, allow_unit_fixture=value)
                with self.assertRaisesRegex(ValueError, 'boolean test-only'):
                    q.verify_browser(self.source / 'candidate', self.b, allow_unit_fixture=value)
        for filename in originals:
            for key, value in [('unitFixture', False), ('unitFixture', 1), ('unitFixture', None),
                               ('fixturePurpose', ''), ('fixturePurpose', None), ('fixturePurpose', 'actual')]:
                for name, data in originals.items():
                    g.save(self.folder / name, {**data, **({key: value} if name == filename else {})})
                with self.subTest(report=filename, key=key, value=value):
                    with self.assertRaisesRegex(ValueError, 'canonical synthetic markers'):
                        g.verify_browser(self.checkout, self.dist, self.b, False, allow_unit_fixture=True)
                    with self.assertRaisesRegex(ValueError, 'canonical synthetic markers'):
                        q.verify_browser(self.source / 'candidate', self.b, allow_unit_fixture=True)
        for name, data in originals.items():
            g.save(self.folder / name, data)
        result = q.verify_browser(self.source / 'candidate', self.b, allow_unit_fixture=True)
        self.assertTrue(result['unitFixtureValidationPassed'])
        self.assertFalse(result['automatedBrowserChecksPassed'])
        self.assertFalse(result['actualBrowserVerified'])
        self.assertNotIn('localMissingRouteHTTPStatus', result)
        self.assertEqual(result['syntheticChecks']['screenshots'], 34)

    def test_synthetic_report_negative_dom_images_interactions_http_and_boundaries(self):
        report, _ = synthetic_reports(self.source, self.dist, self.b)
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
            lambda r: r.update(restrictionVisibilityMutations=[]),
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
                g.save(self.folder / 'browser-report.json', bad)
                with self.assertRaises(ValueError):
                    q.verify_browser(self.source / 'candidate', self.b, allow_unit_fixture=True)

    def test_synthetic_private_metadata_http_and_stable_capture_corruptions(self):
        _, capture = synthetic_reports(self.source, self.dist, self.b)
        mutations = [
            lambda c: c.update(sourceRevision='f' * 40), lambda c: c.update(origin='public'),
            lambda c: c.update(publicHTTPVerified=True), lambda c: c.update(publicationReady=True),
            lambda c: c['metadata'][0].update(robots='index,follow'),
            lambda c: c['metadata'][0].update(canonical=['https://gangjin.fwith.kr/']),
            lambda c: c['metadata'][0].update(productionMetadata=[['site-factory-source', 'x']]),
            lambda c: c['metadata'][0].update(social=[['property', 'og:title', 'unreviewed']]),
            lambda c: c['metadata'][0].update(width=390), lambda c: c['metadata'].pop(),
            lambda c: c['missingRoute'].update(status=200),
            lambda c: c['missingRoute'].update(sha256='0' * 64),
            lambda c: c['missingRoute'].update(canonicalCount=1),
            lambda c: c['httpFiles'].pop(),
            lambda c: c['httpFiles'].reverse(),
            lambda c: c['httpFiles'][0].update(status=404),
            lambda c: c['httpFiles'][0].update(sha256='0' * 64),
            lambda c: c['httpFiles'][0].update(bytes=0),
            lambda c: c['httpFiles'][0].update(contentType='wrong/type'),
            lambda c: c['httpFiles'][0].update(finalURLPath='/other'),
            lambda c: c['captures'].pop(), lambda c: c['captures'][0].update(path='wrong.png'),
            lambda c: c['captures'][0].update(fullPage=True),
            lambda c: c['captures'][0]['settle'].update(samples=[]),
            lambda c: c['captures'][0]['settle'].update(stableTransitions=4),
            lambda c: c['captures'][0]['settle']['samples'][0].update(scrollY=1),
            lambda c: c['captures'][0]['before'].update(fontStatus='loading'),
            lambda c: c['captures'][0]['after'].update(scrollY=1),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(capture_mutation=i):
                bad = copy.deepcopy(capture)
                mutate(bad)
                g.save(self.folder / 'private-capture.json', bad)
                with self.assertRaises(ValueError):
                    g.verify_browser(self.checkout, self.dist, self.b, git_required=False, allow_unit_fixture=True)

    def test_synthetic_sticky_header_bounds_pixels_and_evidence_inventory(self):
        report, capture = synthetic_reports(self.source, self.dist, self.b)
        target = next(i for i, cap in enumerate(capture['captures'])
                      if cap['path'] == 'home-1280-ribbon.png')
        mutations = [lambda h: h['before'].update(position='relative'),
                     lambda h: h['before']['rect'].update(height=400),
                     lambda h: h['before']['observations'][0].update(available=False),
                     lambda h: h['before']['observations'][0].update(text='wrong'),
                     lambda h: h['before']['observations'][0]['rect'].update(y=100),
                     lambda h: h['after'].update(top='1px'),
                     lambda h: h['geometryAfter'].update(scrollY=101),
                     lambda h: h.update(path='../wrong.png'),
                     lambda h: h.update(sha256='0' * 64)]
        for i, mutate in enumerate(mutations):
            with self.subTest(sticky_mutation=i):
                bad = copy.deepcopy(capture)
                mutate(bad['captures'][target]['stickyHeader'])
                g.save(self.folder / 'private-capture.json', bad)
                with self.assertRaises(ValueError):
                    g.verify_browser(self.checkout, self.dist, self.b, False, allow_unit_fixture=True)
        for name, values, error in [
                ('home-390-ribbon.png', [1] * 844, 'body raster'),
                ('home-1280-ribbon.png', [238] * 71 + [y % 211 for y in range(171, 944)], 'Sticky header raster'),
                ('home-1280-ribbon.png', [237] * 71 + [0] * 773, 'body raster')]:
            with self.subTest(pixel_corruption=name, reason=error):
                original = (self.folder / name).read_bytes()
                width = int(name.split('-')[1])
                raw = png_rows(width, values)
                (self.folder / name).write_bytes(raw)
                changed = copy.deepcopy(report)
                next(row for row in changed['screenshots'] if row['path'] == name)['sha256'] = g.sha(raw)
                g.save(self.folder / 'browser-report.json', changed)
                g.save(self.folder / 'private-capture.json', capture)
                with self.assertRaisesRegex(ValueError, error):
                    g.verify_browser(self.checkout, self.dist, self.b, False, allow_unit_fixture=True)
                (self.folder / name).write_bytes(original)
        g.save(self.folder / 'browser-report.json', report)
        bad = copy.deepcopy(capture)
        header = bad['captures'][target]['stickyHeader']
        original = (self.folder / header['path']).read_bytes()
        raw = png(1280, 70, 237)
        (self.folder / header['path']).write_bytes(raw)
        header['sha256'] = g.sha(raw)
        g.save(self.folder / 'private-capture.json', bad)
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            g.verify_browser(self.checkout, self.dist, self.b, False, allow_unit_fixture=True)
        (self.folder / header['path']).write_bytes(original)
        g.save(self.folder / 'private-capture.json', capture)
        (self.folder / 'unreviewed.png').write_bytes(b'not accepted')
        with self.assertRaisesRegex(ValueError, 'inventory'):
            g.verify_browser(self.checkout, self.dist, self.b, False, allow_unit_fixture=True)
        (self.folder / 'unreviewed.png').unlink()
        outside = self.root / 'duplicate.png'
        outside.write_bytes(original)
        (self.folder / header['path']).unlink()
        (self.folder / header['path']).symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            g.verify_browser(self.checkout, self.dist, self.b, False, allow_unit_fixture=True)


    def test_restriction_dom_viewport_and_screenshot_contract(self):
        report,capture=synthetic_reports(self.source,self.dist,self.b)
        target=next(i for i,c in enumerate(capture['captures'])if c['path']=='home-320-products.png')
        original=capture['captures'][target]['restrictionSnapshot']
        mutations=[lambda o:o.update(scope='restriction'),
                   lambda o:o.update(screenshotSHA256='0'*64),
                   lambda o:o['after'].update(fragment=''),
                   lambda o:o['before'].update(heroBeforeActions=False),
                   lambda o:o['before'].update(productAdjacent=False),
                   lambda o:o['before'].update(fragment=''),
                   lambda o:o['before'].update(selectedHospitalElements=1),
                   lambda o:o['before']['products'][0].update(sumElements=1),
                   lambda o:o['before']['products'][0].update(href='wrong'),
                   lambda o:o['before']['products'][0].update(ctaHref='wrong'),
                   lambda o:o['before']['productNotice'].update(text='화순의 모든 시설 반입 금지'),
                   lambda o:o['before']['productNotice'].update(available=False),
                   lambda o:o['before']['productNotice']['ancestors'][0].update(display='none'),
                   lambda o:o['before']['productNotice']['ancestors'][0].update(visibility='hidden'),
                   lambda o:o['before']['productNotice']['ancestors'][0].update(opacity='0'),
                   lambda o:o['before']['productNotice']['ancestors'][0].update(hidden=True),
                   lambda o:o['before']['productNotice']['ancestors'][0].update(inert=True),
                   lambda o:o['before']['productNotice']['ancestors'][0].update(ariaHidden='true'),
                   lambda o:o['before']['productNotice'].update(ancestors=[]),
                   lambda o:o['before']['productNotice']['rect'].update(height=900),
                   lambda o:o['before']['productNotice']['rect'].update(y=-1.1),
                   lambda o:o['before']['productNotice']['rect'].update(x=-2),
                   lambda o:o['before']['productHeading']['rect'].update(y=400),
                   lambda o:o['before']['productCards']['rect'].update(y=299-1.1)]
        for i,mutate in enumerate(mutations):
            with self.subTest(restriction_mutation=i):
                bad=copy.deepcopy(capture);observation=bad['captures'][target]['restrictionSnapshot'];mutate(observation)
                if i!=2:observation['after']=copy.deepcopy(observation['before'])
                g.save(self.folder/'private-capture.json',bad)
                with self.assertRaises(ValueError):g.verify_browser(self.checkout,self.dist,self.b,False,allow_unit_fixture=True)
        g.save(self.folder/'private-capture.json',capture)
        result=g.verify_browser(self.checkout,self.dist,self.b,False,allow_unit_fixture=True)
        self.assertEqual(result['syntheticChecks']['restrictionViewportSnapshotsEvaluated'],6)
        for width in [320,390,1280]:
            for scope in ['restriction','products']:
                good=synthetic_restriction(self.b['browserExpected']['restriction'],width,scope)
                self.assertTrue(q.verify_restriction(good,self.b['browserExpected']['restriction'],width,scope)['completeNoticeInViewport'])
                for key in ['hero','heroText','heroSource']if scope=='restriction'else['productNotice']:
                    bad=copy.deepcopy(good);bad[key]['rect']['y']=70 if width==1280 else -2
                    # Desktop top 70 is within the explicit 1px rounding tolerance; choose 69.
                    if width==1280:bad[key]['rect']['y']=69
                    with self.assertRaises(ValueError):q.verify_restriction(bad,self.b['browserExpected']['restriction'],width,scope)


    def test_gangjin_manuscript_structure_and_merchant_prose_contract(self):
        report,capture=synthetic_reports(self.source,self.dist,self.b)
        for key,value in [('manuscriptSHA256','0'*64),('structure',None),('structure',{})]:
            bad=copy.deepcopy(report);bad['states'][0][key]=value
            g.save(self.folder/'browser-report.json',bad)
            with self.assertRaises(ValueError):q.verify_browser(self.source/'candidate',self.b,allow_unit_fixture=True)
        for key in ['sectionIDs','bannerPlacements']:
            bad=copy.deepcopy(report);bad['states'][0]['structure'][key].reverse()
            g.save(self.folder/'browser-report.json',bad)
            with self.assertRaises(ValueError):q.verify_browser(self.source/'candidate',self.b,allow_unit_fixture=True)
        g.save(self.folder/'browser-report.json',report)
        expected=self.b['browserExpected']['restriction']
        for value in [None,[],expected['productProse'][::-1],[expected['productProse'][0]]]:
            bad=synthetic_restriction(expected,320,'products');bad['productProse']=value
            with self.assertRaises(ValueError):q.verify_restriction(bad,expected,320,'products')
        for value in [None,'FACILITY_OPERATOR_POLICY','MERCHANT_NOTICE']:
            altered=copy.deepcopy(expected);altered['sourceAuthority']=value
            with self.assertRaises(ValueError):q.verify_restriction(synthetic_restriction(expected,320,'products'),altered,320,'products')
        # Accepted three prose paragraphs place the heading above this dedicated notice view.
        # The heading remains visible-in-document and ordered, but is not claimed within viewport.
        valid=synthetic_restriction(expected,320,'products');valid['productHeading']['rect']['y']=-300
        self.assertTrue(q.verify_restriction(valid,expected,320,'products')['completeNoticeInViewport'])

    def test_capture_startup_reaches_mocked_server_without_browser_or_socket(self):
        class StopBeforeSocket(RuntimeError):
            pass

        api = types.ModuleType('playwright.sync_api')
        api.sync_playwright = Mock(side_effect=AssertionError('browser must not start'))
        parent = types.ModuleType('playwright')
        parent.sync_api = api
        original_path = sys.path[:]
        try:
            with patch.dict(sys.modules, {'playwright': parent, 'playwright.sync_api': api}):
                sys.modules.pop('qa_gangjin', None)
                sys.modules.pop('html_surface', None)
                spec = importlib.util.spec_from_file_location('gangjin_capture_unit_startup',
                                                              g.ROOT / 'capture_private.py')
                capture = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(capture)
                with patch.object(capture.socketserver, 'ThreadingTCPServer',
                                  side_effect=StopBeforeSocket('socket boundary reached')) as server, \
                     patch('socket.socket', side_effect=AssertionError('real socket forbidden')) as socket_guard:
                    with self.assertRaisesRegex(StopBeforeSocket, 'socket boundary reached'):
                        capture.run(self.source, self.dist, self.b['sourceRevision'])
                    server.assert_called_once()
                    self.assertEqual(server.call_args.args[0], ('127.0.0.1', 0))
                    self.assertTrue(issubclass(server.call_args.args[1],
                                               capture.http.server.SimpleHTTPRequestHandler))
                    socket_guard.assert_not_called()
                api.sync_playwright.assert_not_called()
                self.assertEqual(capture.C, self.source / 'candidate')
        finally:
            sys.path[:] = original_path


if __name__ == '__main__':
    unittest.main()
