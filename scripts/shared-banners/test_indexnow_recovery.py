#!/usr/bin/env python3
"""Keep the seven-site IndexNow recovery on existing read-only finalization jobs."""
from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[2]
REGIONS=('gwacheon','gwangju','jongno','seoul-yongsan','seoul-jungnang','yangju','yangpyeong')
TITLE='[REGIONAL-INDEXNOW-ONLY] batch'
def recovery_selection(r):
 title=f"github.event.issue.title == '{TITLE}'"
 if r=='seoul-jungnang':title=f"(github.event.issue.title == '[REGIONAL-INDEXNOW-ONLY] seoul-jungnang' || {title})"
 return "github.event_name == 'issues' && "+title

class RecoveryBoundary(unittest.TestCase):
 def workflow(self,r):return (ROOT/f'.github/workflows/{r}-direct-publish.yml').read_text()
 def test_all_and_only_seven_workflows_select_recovery_batch(self):
  actual={p.name.removesuffix('-direct-publish.yml') for p in (ROOT/'.github/workflows').glob('*-direct-publish.yml') if TITLE in p.read_text()}
  self.assertEqual(actual,set(REGIONS))
 def test_existing_owner_main_exact_branch_first_attempt_gates_remain(self):
  for r in REGIONS:
   with self.subTest(region=r):
    w=self.workflow(r);build=w.split('  publish:',1)[0]
    for guard in ("github.repository == 'joseungil-kr/fwith-site-factory'","github.ref == 'refs/heads/main'","github.actor == 'joseungil-kr'","github.event.issue.user.login == 'joseungil-kr'",f"contains(github.event.issue.body, '\"{r}\"')",f"ref: 'heads/site-factory-{r}-direct'","process.env.GITHUB_RUN_ATTEMPT !== '1'","data.object.sha !== process.env.REVISION"):
     self.assertIn(guard,build)
    self.assertIn(f"fromJSON(github.event.issue.body).revisions['{r}']",build)
    self.assertIn("/^[0-9a-f]{40}$/",build)
 def test_recovery_title_cannot_select_provider_mutation_job(self):
  for r in REGIONS:
   with self.subTest(region=r):
    w=self.workflow(r);publish=w.split('  publish:\n',1)[1].split('  finalize_indexnow:',1)[0]
    self.assertTrue(publish.startswith(f"    if: inputs.indexnow_only != true && !({recovery_selection(r)})\n"))
    self.assertIn('verify_update.py authorize-mutation --region '+r,publish)
 def test_recovery_keeps_existing_exact_finalizer_and_no_provider_credentials(self):
  for r in REGIONS:
   with self.subTest(region=r):
    final=self.workflow(r).split('  finalize_indexnow:\n',1)[1]
    self.assertTrue(final.startswith(f"    if: inputs.indexnow_only == true || ({recovery_selection(r)})\n"))
    for forbidden in ('CLOUDFLARE','secrets.','npx ','wrangler','provider-after',' preflight ',' attach ','authorize-mutation'):
     self.assertNotIn(forbidden,final)
    for mode in ('artifact','http','indexnow-probe','indexnow'):
     self.assertIn(f'control/scripts/direct-{r}/publish.py {mode} --report ',final)
    self.assertIn(f'verify_update.py artifact --region {r}',final)
    self.assertIn('data.object.sha !== process.env.REVISION',final)
    self.assertIn('test "$GITHUB_RUN_ATTEMPT" = 1',final)
    self.assertIn('banner-artifact.json',final)
 def test_concurrency_and_dispatch_only_option_preserved(self):
  for r in REGIONS:
   with self.subTest(region=r):
    w=self.workflow(r)
    self.assertIn('group: '+r+'-direct-public-release',w)
    self.assertIn('cancel-in-progress: false',w)
    self.assertIn('  workflow_dispatch:',w)
    self.assertIn('      indexnow_only:',w)

if __name__=='__main__':unittest.main()
