#!/usr/bin/env python3
"""Socket-blocked local preparation regressions, no Git commits or browser."""
import json,os,socket,sys,unittest
from pathlib import Path
from unittest.mock import patch
import adapter,test_successor
sys.path.insert(0,str(Path(__file__).resolve().parent/'upstream'))
import test_controls
suite=unittest.TestSuite()
for cls in (test_controls.ControlsTest,test_controls.BrowserAssertionsTest,test_successor.SuccessorTests):suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
with patch.object(socket,'socket',side_effect=AssertionError('Offline sockets prohibited')):result=unittest.TextTestRunner(verbosity=2).run(suite)
summary={'status':'PASS_OFFLINE_PREPARATION_ONLY'if result.wasSuccessful()else 'FAIL','testsRun':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'socketCreationBlocked':True,'browserLaunched':False,'gitCommitsCreated':False,'staticFixtureKind':'explicitly transformed historical output; not fresh build'if os.environ.get('SYNTHETIC_DIST_ROOT')else 'current GitHub exact-SHA build','upstreamGitCommitFixtureClassExcluded':'SourceTest'}
Path(os.environ['OFFLINE_TEST_REPORT']).write_text(json.dumps(summary,indent=2)+'\n')
sys.exit(0 if result.wasSuccessful()else 1)
