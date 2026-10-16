"""Run output mutations against freshly generated Node fixture. No saved output dependency."""
from pathlib import Path
import shutil,tempfile,unittest
import test_gokseong_release_output as original
from test_gokseong_node_python_parity import synthetic_node_output

def run():
 with synthetic_node_output() as (fixture,mode):
  def runner_setup(self):
   self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'dist'
   shutil.copytree(fixture,self.root);self.mode=dict(mode)
  original.OutputTests.setUp=runner_setup
  result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(original.OutputTests))
  return 0 if result.wasSuccessful() else 1
if __name__=='__main__':raise SystemExit(run())
