"""Reject source-correction scope/provenance expansion; no source edits or sockets."""
import copy,unittest
import adapter

class SourceLineageTests(unittest.TestCase):
    def inputs(self):
        return (adapter.load(adapter.HERE/'frozen-inputs/source-file-manifest.final.json'),
                adapter.load(adapter.HERE/'frozen-inputs/source-file-manifest.visual-fix.json'),
                adapter.load(adapter.HERE/'source-fix-lineage.json'))
    def mutate(self,fn):
        values=copy.deepcopy(self.inputs());fn(*values)
        with self.assertRaises((AssertionError,KeyError)):adapter.validate_snapshot_lineage(*values)
    def test_exact_independent_lineage(self):self.assertTrue(adapter.validate_snapshot_lineage(*self.inputs()))
    def test_no_correction_rejected(self):self.mutate(lambda old,new,lineage:new.__setitem__(slice(None),old))
    def test_second_source_change_rejected(self):self.mutate(lambda old,new,lineage:new[0].update(sha256='0'*64))
    def test_added_source_path_rejected(self):self.mutate(lambda old,new,lineage:new.append(copy.deepcopy(new[0])))
    def test_reordered_source_paths_rejected(self):self.mutate(lambda old,new,lineage:new.reverse())
    def test_wrong_css_scope_rejected(self):self.mutate(lambda old,new,lineage:lineage.update(changedPath=adapter.SITE_PATH+'/src/data/yeongdeungpo-copy.json'))
    def test_wrong_old_css_hash_rejected(self):self.mutate(lambda old,new,lineage:lineage.update(originalCssSha256='0'*64))
    def test_wrong_new_css_hash_rejected(self):self.mutate(lambda old,new,lineage:lineage.update(correctedCssSha256='0'*64))
    def test_wrong_original_snapshot_rejected(self):self.mutate(lambda old,new,lineage:lineage.update(originalManifestSha256='0'*64))
    def test_stale_reused_blob_hint_rejected(self):
        self.mutate(lambda old,new,lineage:next(e for e in new if e['path']==lineage['changedPath']).update(existingBlob={'commit':lineage['originalSourceCommit']}))
    def test_wrong_predecessor_provenance_rejected(self):
        self.mutate(lambda old,new,lineage:next(e for e in new if e['path']==lineage['changedPath'])['previousSnapshot'].update(sourceSha='0'*40))
    def test_count_drift_rejected(self):self.mutate(lambda old,new,lineage:lineage.update(unchangedSourceFiles=306))
    def test_copy_preservation_removed_rejected(self):self.mutate(lambda old,new,lineage:lineage.update(originalCopyAndApprovalRecordsPreserved=False))
    def test_source_review_cannot_grant_publication(self):self.mutate(lambda old,new,lineage:lineage.update(publicationAuthorization='granted'))
    def test_source_review_cannot_claim_browser_pass(self):self.mutate(lambda old,new,lineage:lineage.update(browserCorrectionVerified=True))
