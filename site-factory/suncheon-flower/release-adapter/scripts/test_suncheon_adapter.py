"""Independent negative contracts; no fixture authorizes production or publishing."""
import unittest,tempfile,shutil,subprocess,os
from pathlib import Path
import suncheon_adapter as a
class AdapterTests(unittest.TestCase):
 def test_exact_saved_source(self):self.assertEqual(len(a.frozen_source()),55)
 def test_original_build_env_allowed(self):self.assertEqual(a.private_environment({})['ASTRO_TELEMETRY_DISABLED'],'1')
 def test_private_dist_exact(self):self.assertTrue(a.verify_private_dist(a.CANDIDATE/'dist'))
 def test_production_command_is_fail_closed(self):
  r=subprocess.run(['python3',str(Path(a.__file__)),'production'],capture_output=True,text=True);self.assertNotEqual(r.returncode,0);self.assertIn('BLOCKED',r.stderr)
 def test_source_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   for row in a.frozen_source():
    p=root/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((a.SOURCE/row['path']).read_bytes())
   p=root/'candidate/src/pages/index.astro';p.write_bytes(p.read_bytes()+b'changed')
   with self.assertRaisesRegex(ValueError,'frozen_file_changed'):a.frozen_source(root)
 def test_source_symlink(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   for row in a.frozen_source():
    p=root/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((a.SOURCE/row['path']).read_bytes())
   p=root/'candidate/src/pages/index.astro';p.unlink();p.symlink_to(root/'candidate/README.md')
   with self.assertRaisesRegex(ValueError,'regular_file_required'):a.frozen_source(root)
 def test_no_existing_destination_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(ValueError,'already_exists'):a.inspect_output(a.CANDIDATE/'dist',d)
 def test_no_source_internal_destination(self):
  with self.assertRaisesRegex(ValueError,'outside_source'):a.inspect_output(a.CANDIDATE/'dist',a.SOURCE/'uncreated-inspection')
 def test_no_actual_public_claims(self):
  import json
  r=json.loads((a.SOURCE.parent/'evidence/inspection-result.json').read_text())
  for k in ['publicHTTPVerified','productionBindingUsed','productionRunnerExecuted','publishableArtifact','releaseManifestCreated','providerCredentialsUsed','publicationExecuted','indexNowSubmitted']:self.assertIs(r[k],False,k)
for name in a.BOUNDARY:
 def test(self,key=name):
  with self.assertRaisesRegex(ValueError,'unexpected_release_or_provider_environment'):a.private_environment({key:'TEST_VALUE_NOT_A_CREDENTIAL'})
 setattr(AdapterTests,'test_reject_environment_'+name,test)
if __name__=='__main__':unittest.main(verbosity=2)
