"""Offline tests for Goheung's explicit publish/public-check-only phase."""
import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
import publish as p
import test_publish


class PublicationPhaseTests(unittest.TestCase):
    def setUp(self):
        self.fixture=test_publish.PublisherTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)

    def test_submission_client_is_absent_and_cli_rejects_submission_modes(self):
        names={n.name for n in ast.walk(ast.parse((self.fixture.original/'publish.py').read_text()))if isinstance(n,ast.FunctionDef)}
        self.assertFalse(names & {'indexnow','indexnow_probe','indexnow_site','observed_indexnow_request'})
        for mode in ['indexnow','indexnow-probe','submit']:
            result=subprocess.run(['python3','-B',str(self.fixture.original/'publish.py'),mode,'--report',str(self.fixture.root/'forbidden.json')],capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertFalse((self.fixture.root/'forbidden.json').exists())

    def test_publication_configuration_cannot_enable_receipts_or_change_phase(self):
        good=copy.deepcopy(self.fixture.config)
        for key,value in [('indexNowSubmissionEnabled',True),('indexNowSubmissionEnabled',0),('mode','publish'),('receiptIssue',409),('receiptIssueTitle','forged')]:
            p.save(self.fixture.d/'production-publication.json',{**good,key:value})
            with self.subTest(key=key),patch.object(p,'provider_transport') as t,self.assertRaises(ValueError):p.provider('preflight')
            t.assert_not_called()
        p.save(self.fixture.d/'production-publication.json',good)
        self.assertFalse(p.publication_config()['indexNowSubmissionEnabled'])

    def test_native_actual_verdict_cannot_be_substituted_or_softened(self):
        f=self.fixture
        row=next(r for r in f.review['evidence']if r['kind']=='native-actual-verdict');path=f.root/row['path'];raw=path.read_bytes();native=json.loads(raw)
        for field,value in [('status','ACCEPTED_LOCAL_CONTROL6_ONLY'),('accepted',False),('blockingFindings',True),('source50Revision','f'*40),('artifactId',999990),('artifactSHA256','e'*64),('actualReleaseManifestSHA256','a'*64),('actualPNGsVisuallyReviewed',3),('independentWholeViewportPixelComparisons',3),('fullPageCoverageComplete',False),('publicHTTPVerified',True)]:
            bad=copy.deepcopy(native);bad[field]=value;p.save(path,bad);row['sha256']=p.sha(path.read_bytes())
            reviewpath=f.docs/'production-release-review-20261016.json';p.save(reviewpath,f.review);p.save(f.d/'production-release-review-binding.json',dict(schemaVersion=1,path=reviewpath.relative_to(f.root).as_posix(),sha256=p.sha(reviewpath.read_bytes())))
            with self.subTest(field=field),patch.object(p,'provider_transport') as transport,self.assertRaisesRegex(ValueError,'native_actual_verdict_mismatch'):p.release_review()
            transport.assert_not_called()
        path.write_bytes(raw)

    def test_native_verdict_evidence_is_mandatory(self):
        f=self.fixture;f.review['evidence']=[r for r in f.review['evidence']if r['kind']!='native-actual-verdict']
        path=f.docs/'production-release-review-20261016.json';p.save(path,f.review);p.save(f.d/'production-release-review-binding.json',dict(schemaVersion=1,path=path.relative_to(f.root).as_posix(),sha256=p.sha(path.read_bytes())))
        with self.assertRaisesRegex(ValueError,'native_actual_verdict_required'):p.release_review()

    def test_full_actual_404_body_preserved_with_nofollow(self):
        _,dist=self.fixture.fixture_release();raw=(dist/'404.html').read_bytes()
        self.assertIn(b'content="noindex,nofollow"',raw);self.assertNotIn(b'content="noindex,follow"',raw)
        self.assertEqual(p.expected_robots('/404.html'),{'noindex','nofollow'})
        (dist/'404.html').write_bytes(raw.replace(b'noindex,nofollow',b'noindex,follow'))
        with self.assertRaises(AssertionError):p.output.inspect_dist(dist,dict(mode='production',indexable=True,origin=p.ORIGIN,revision=p.gate.SOURCE))

    def test_goheung_two_questions_four_paragraphs_and_copy87_14(self):
        _,dist=self.fixture.fixture_release();home=p.output.Metadata((dist/'index.html').read_text());missing=p.output.Metadata((dist/'404.html').read_text())
        self.assertEqual((len(home.copy_keys),len(missing.copy_keys)),(87,14));self.assertEqual(len(home.faq_questions),2)
        self.assertEqual([a['data-copy-key']for a in home.faq_answers],['question-1.answer.0','question-1.answer.1','question-1.answer.2','question-2.answer.0'])
        self.assertEqual(home.product_skus,['B201','B203','B205','B060']);self.assertEqual(len(home.images),7)

    def test_workflow_publish_only_has_no_journal_permission_or_submission_step(self):
        text=(self.fixture.original.parents[1]/'.github/workflows/goheung-production-publish.yml').read_text()
        self.assertIn('if: github.repository',text)
        self.assertNotIn('issues: write',text);self.assertNotIn('GH_TOKEN:',text);self.assertNotIn('receiptIssue',text)
        self.assertNotIn('indexnow --report',text);self.assertNotIn('INDEXNOW:',text)
        self.assertIn('wrangler@4.148.0 deploy',text);self.assertEqual(text.count('wrangler@4.148.0 deploy'),1)
        self.assertIn('including after an uncertain upload',text);self.assertIn('public-http.json',text)


if __name__=='__main__':unittest.main(verbosity=2)
