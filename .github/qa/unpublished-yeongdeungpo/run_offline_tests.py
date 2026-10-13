#!/usr/bin/env python3
"""Run selected unchanged upstream tests plus adapter tests with sockets blocked.
Upstream SourceTest intentionally excluded: its fixtures would create Git commits.
"""
import json, os, socket, sys, unittest
from pathlib import Path
from unittest.mock import patch
import adapter, test_adapter, test_revision2, test_source_lineage
sys.path.insert(0,str(Path(__file__).resolve().parent/'upstream'))
import test_controls
suite=unittest.TestSuite()
for cls in (test_controls.ControlsTest,test_controls.BrowserAssertionsTest,test_adapter.AdapterTests,test_revision2.Revision2Tests,test_source_lineage.SourceLineageTests):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
with patch.object(socket,'socket',side_effect=AssertionError('Network/socket use prohibited in offline preparation tests')):
    result=unittest.TextTestRunner(verbosity=2).run(suite)
summary={'status':'PASS_OFFLINE_PREPARATION_ONLY' if result.wasSuccessful() else 'FAIL','testsRun':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'socketCreationBlocked':True,'browserLaunched':False,'gitCommitsCreated':False,'upstreamGitCommitFixtureClassExcluded':'SourceTest','nativeBrowserAssertionsUnchanged':True}
Path(os.environ.get('OFFLINE_TEST_REPORT',str(Path(__file__).resolve().parent/'offline-tests.json'))).write_text(json.dumps(summary,indent=2)+'\n')
sys.exit(0 if result.wasSuccessful() else 1)
