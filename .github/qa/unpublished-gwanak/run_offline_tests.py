#!/usr/bin/env python3
"""Offline controls only. Does not import Playwright or launch a browser."""
from pathlib import Path
import json,os,subprocess,sys
here=Path(__file__).resolve().parent
commands=[[sys.executable,str(here/'upstream/test_controls.py')],[sys.executable,str(here/'test_gwanak_contract.py')]]
rows=[]
for cmd in commands:
 result=subprocess.run(cmd,cwd=here,text=True,capture_output=True);print(result.stdout);print(result.stderr,file=sys.stderr)
 rows.append({'command':cmd[-1],'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
out=os.environ.get('OFFLINE_TEST_REPORT')
if out:Path(out).write_text(json.dumps({'scope':'offline synthetic contract/guard tests only; browser unexecuted','passed':all(r['returncode']==0 for r in rows),'runs':rows},ensure_ascii=False,indent=2)+'\n')
sys.exit(0 if all(r['returncode']==0 for r in rows)else 1)
