"""Operational preparation profile; never production approval."""
import json
from pathlib import Path
import unittest
import whole_initial as whole

class RegisteredPyeongtaekTests(unittest.TestCase):
    def test_exact35_profile_is_registered_without_production(self):
        self.assertEqual(set(whole.ADDITIONAL_REVIEWED_RELEASES),{'pyeongtaek-flower-v2'})
        binding=whole.reviewed_release_binding('pyeongtaek-flower-v2')
        registry=json.loads((Path(__file__).resolve().parents[3]/'.github/site-factory-sites.json').read_text())
        site=registry['sites']['pyeongtaek-flower-v2']
        whole.validate_reviewed_membership('pyeongtaek-flower-v2',site)
        self.assertEqual(binding['bootstrapSourceSha'],'b5ddfad37e00216bc7eea5b200b2ed2725d971ed')
        self.assertEqual(binding['initialLaunch']['officialUnitCount'],37)
        self.assertEqual(set(binding['runtimeAmendment']['files']),whole.RUNTIME_PARTIAL_GRAPH_PATHS)
        self.assertEqual(site['initialPreviewBaselineRevision'],'30644a3a832cb8924e380e3a94f1e50ce5c2d1ea')
        subset=binding['releaseSubset']
        self.assertEqual(len(subset['releasedPageKeys']),35)
        self.assertEqual(subset['deferredPageKeys'],['pyeongtaek-flower-v2-region-chilwon-dong','pyeongtaek-flower-v2-region-wolgok-dong'])
        self.assertTrue(site['regionalService']['enabled'])
        self.assertFalse(site['productionEnabled']);self.assertEqual(site['launchMode'],'staging')
        self.assertTrue(site['growthPaused']);self.assertFalse(site['autoDeploySnapshots'])
        self.assertEqual(site['approvedRevision'],'');self.assertEqual(site['approvalEvidenceUrl'],'')
        for name in ('requireSnapshotApproval','requireRevisionApproval','stagingBuildIsolation'):
            self.assertTrue(site[name])
        self.assertFalse(whole.is_reviewed_initial_site('anyang-flower-v2'))
        self.assertEqual(whole.reviewed_release_binding('namyangju-flower-v2')['initialLaunch']['officialUnitCount'],20)

if __name__=='__main__':unittest.main()
