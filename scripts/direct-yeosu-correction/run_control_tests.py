"""Never allow missing or zero-discovered correction controls to pass CI."""
import os,sys,unittest
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root))
for name in ('test_production_build.py','test_capture_contract.py','test_layout_evidence.py'):
 if not (root/name).is_file():raise SystemExit('required_control_tests_missing:'+name)
suite=unittest.defaultTestLoader.discover(str(root),pattern='test_*.py')
if suite.countTestCases()<40:raise SystemExit('minimum40_correction_control_tests_required:'+str(suite.countTestCases()))
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
