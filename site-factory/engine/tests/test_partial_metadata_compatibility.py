"""Synthetic metadata compatibility; never content approval or real publication."""
import copy,hashlib,json,re,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_whole_initial as old
import test_reviewed_partial_initial as partial
import whole_initial as whole
import render_snapshot as renderer
import batch_barrier as barrier


def use_freeform_metadata(batch,evidence,git):
    registry=json.loads(git.read(old.BASE,'.github/site-factory-sites.json'))
    root=registry['sites'][batch['siteKey']]['root']
    base_paths=[path for (revision,path) in git.documents if revision==old.BASE and path.startswith(root+'/')]
    with tempfile.TemporaryDirectory() as d:
        workspace=Path(d)
        for path in base_paths:
            p=workspace/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(git.read(old.BASE,path))
        for index,item in enumerate(evidence['items']):
            body=re.sub(r'^STRUCTURE_TYPE:.*$',f'STRUCTURE_TYPE: regional-venue-fixture-{index}',item['payload'],flags=re.M)
            body=re.sub(r'^VISUAL_INTENT:.*$','VISUAL_INTENT: 공식 상품 사진과 가격을 비교하는 합성 테스트',body,flags=re.M)
            parsed=renderer.validate_content(renderer.parse_payload(body));storage,reviewed=renderer.frozen_hashes(parsed)
            body=re.sub(r'^APPROVED_SNAPSHOT_HASH:.*$','APPROVED_SNAPSHOT_HASH: '+reviewed,body,flags=re.M)
            renderer.render(body,registry,workspace)
            item.update(payload=body,reviewDigest=reviewed,snapshotHash=storage)
            item['reviewerApproval']['reviewDigest']=reviewed
            for name in ('pages','page-map','publish-manifest','architecture'):
                path=root+'/src/data/'+name+'.json';git.documents[(item['commitSha'],path)]=(workspace/path).read_bytes()
        for name in ('pages','page-map','publish-manifest','architecture'):
            path=root+'/src/data/'+name+'.json';git.documents[(old.FINAL,path)]=(workspace/path).read_bytes()
        evidence['qa']['manifestSha256']=hashlib.sha256(git.read(old.FINAL,root+'/src/data/publish-manifest.json')).hexdigest()


class PartialMetadataCompatibilityTests(unittest.TestCase):
    def test_exact_partial_uses_renderer_metadata_and_frozen_approval(self):
        batch,evidence,git,profile,binding=partial.fixture()
        with patch.dict(whole.ADDITIONAL_REVIEWED_RELEASES,{partial.SITE:binding}),patch.dict(whole.ALL_INITIAL_SOURCE_PROFILES,{partial.SITE:profile}):
            use_freeform_metadata(batch,evidence,git)
            self.assertEqual(barrier.check(batch,evidence,git)['detailCount'],35)
            for field in ('STRUCTURE_TYPE','VISUAL_INTENT'):
                changed=copy.deepcopy(evidence)
                changed['items'][0]['payload']=re.sub('^'+field+':.*$',field+': modified-after-review',changed['items'][0]['payload'],flags=re.M)
                with self.subTest(field=field),self.assertRaisesRegex(ValueError,'frozen approval mismatch'):
                    barrier.check(batch,changed,git)

    def test_sixth_qa_path_is_partial_pyeongtaek_only(self):
        _,_,_,_,binding=partial.fixture()
        amendment={'files':{path:{'beforeSha256':'a'*64,'afterSha256':'b'*64} for path in whole.RUNTIME_RECONCILIATION_PATHS},
            'reviewEvidenceUrl':'https://github.com/joseungil-kr/fwith-site-factory/issues/999999'}
        binding['runtimeAmendment']=amendment
        self.assertIs(whole.reviewed_runtime_amendment(binding),amendment)
        amendment['files']['scripts/qa_graph.mjs']={'beforeSha256':'a'*64,'afterSha256':'b'*64}
        self.assertIs(whole.reviewed_runtime_amendment(binding),amendment)
        for case in ('other-site','whole-mode','no-subset','null-subset','extra-path'):
            changed=copy.deepcopy(binding)
            if case=='other-site':changed['releaseSubset']['siteKey']='anyang-flower-v2'
            elif case=='whole-mode':changed['releaseSubset']['mode']='whole-dong-initial'
            elif case=='no-subset':changed.pop('releaseSubset')
            elif case=='null-subset':changed['releaseSubset']=None
            else:changed['runtimeAmendment']['files']['src/config/site.ts']={'beforeSha256':'a'*64,'afterSha256':'b'*64}
            with self.subTest(case=case),self.assertRaises(ValueError):whole.reviewed_runtime_amendment(changed)

    def test_namyangju_full_initial_metadata_stays_strict(self):
        batch,evidence,git,profile=old.fixture()
        initial=json.loads(git.read(old.BASE,'.github/site-factory-sites.json'))['sites'][old.SITE]['initialLaunch']
        with patch.object(whole,'REVIEWED_BOOTSTRAP_REVISION',old.BOOTSTRAP),patch.dict(whole.REVIEWED_INITIAL,initial,clear=True),patch.dict(whole.INITIAL_SOURCE_PROFILES,{old.SITE:profile}):
            use_freeform_metadata(batch,evidence,git)
            with self.assertRaisesRegex(ValueError,'regional frozen payload mismatch'):
                barrier.check(batch,evidence,git)

if __name__=='__main__':unittest.main()
