"""Credential-free synthetic regressions; actual sockets and child processes forbidden."""
import json,os,socket,subprocess,sys,unittest
from unittest.mock import patch
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent
attempts=[]
def blocked(*args,**kwargs):
 attempts.append('forbidden_external_attempt');raise RuntimeError('synthetic_tests_external_io_forbidden')
def main():
 # Existing credentials are scoped only to the later observation step.
 if any(os.environ.get(k) for k in ('CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID')):raise ValueError('synthetic_tests_provider_credentials_forbidden')
 modules=['test_provider_baseline']
 if (D/'test_yeosu_baseline.py').is_file():modules.append('test_yeosu_baseline')
 class Results(unittest.TextTestResult):
  subtests=0
  def addSubTest(self,test,subtest,outcome):
   self.subtests+=1;super().addSubTest(test,subtest,outcome)
 with patch.object(socket,'create_connection',blocked),patch.object(socket.socket,'connect',blocked),patch.object(socket.socket,'connect_ex',blocked),patch.object(subprocess,'Popen',blocked):
  suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in modules)
  result=unittest.TextTestRunner(verbosity=2,resultclass=Results).run(suite)
 out={'state':'SYNTHETIC_TESTS_PASSED' if result.wasSuccessful() and not attempts else 'SYNTHETIC_TESTS_FAILED','testMethods':result.testsRun,'subtests':result.subtests,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'forbiddenAttempts':attempts,'providerRequests':0,'publicRequests':0,'sourceRevision':__import__('provider_baseline').CURRENT,'python':sys.version.split()[0],'actualProviderStateVerified':False}
 print(json.dumps(out,sort_keys=True));return 0 if result.wasSuccessful() and not attempts else 1
if __name__=='__main__':sys.exit(main())
