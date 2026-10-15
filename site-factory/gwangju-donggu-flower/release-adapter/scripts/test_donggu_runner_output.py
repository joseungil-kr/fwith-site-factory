"""Run original pinned output mutations against actual runner dist. No browser/network."""
from pathlib import Path
import shutil,tempfile,re,unittest
import test_donggu_release_output as original
import donggu_release_output as output
def runner_setup(self):
 self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'dist'
 shutil.copytree(Path(__file__).resolve().parents[2]/'candidate/dist',self.root)
 text=(self.root/'index.html').read_text();m=re.search(r'<meta name="site-factory-revision" content="([0-9a-f]{40})">',text);self.assertIsNotNone(m,'Build production first')
 self.mode=dict(mode='production',indexable=True,origin=output.ORIGIN,revision=m.group(1))
if __name__=='__main__':
 original.OutputTests.setUp=runner_setup
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(original.OutputTests))
 raise SystemExit(0 if result.wasSuccessful() else 1)
