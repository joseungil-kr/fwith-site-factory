"""Run output mutations against freshly generated Node fixture. No saved output dependency."""
from pathlib import Path
import shutil,tempfile,unittest
import test_gokseong_release_output as original
from test_gokseong_node_python_parity import synthetic_node_output
from gokseong_test_fixtures import synthetic_production_output

def run_suite(context,klass):
 with context() as (fixture,mode):
  def runner_setup(self):
   self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'dist'
   shutil.copytree(fixture,self.root);self.mode=dict(mode)
  klass.setUp=runner_setup
  result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(klass))
  return 0 if result.wasSuccessful() else 1
def run():
 return max(run_suite(synthetic_node_output,original.OutputTests),run_suite(synthetic_production_output,original.ProductionOutputTests))
if __name__=='__main__':raise SystemExit(run())
