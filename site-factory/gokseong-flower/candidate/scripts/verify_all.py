"""ZIP-contained aggregate runner; evidence must be outside the immutable source tree."""
from pathlib import Path
import os,subprocess,json,sys,argparse,importlib.util
S=Path(__file__).resolve().parents[2];C=S/'candidate';A=S/'release-adapter'
p=argparse.ArgumentParser();p.add_argument('--evidence',required=True);args=p.parse_args();E=Path(args.evidence).resolve();assert not E.is_relative_to(S),'Evidence must remain separate';E.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(A/'scripts'));import gokseong_adapter as a
env=a.private_environment();env.update(ASTRO_TELEMETRY_DISABLED='1',PYTHONDONTWRITEBYTECODE='1');results=[]
commands=[('verify-inputs',['node','scripts/verify_inputs.mjs']),('typecheck',['node','node_modules/astro/bin/astro.mjs','check']),('build-and-private-qa',['npm','run','build']),('private-node-tests',['node','--test','tests/gokseong-runtime.test.mjs']),('private-python-tests',['python3','scripts/test_gokseong.py']),('adapter-node-tests',['node','--test','../release-adapter/release-tests/gokseong-release.test.mjs']),('build-order-tests',['node','--test','../release-adapter/release-tests/gokseong-build-order.test.mjs']),('adapter-python-tests',['python3','../release-adapter/scripts/test_gokseong_adapter.py']),('output-python-tests',['python3','../release-adapter/scripts/test_gokseong_release_output.py']),('node-python-parity',['python3','../release-adapter/scripts/test_gokseong_node_python_parity.py']),('runner-output-tests',['python3','../release-adapter/scripts/test_gokseong_runner_output.py']),('exact-occurrence-tests',['python3','../release-adapter/scripts/test_gokseong_occurrences.py'])]
for name,command in commands:
 with (E/(name+'-final.log')).open('wb') as f:r=subprocess.run(command,cwd=C,env=env,stdout=f,stderr=subprocess.STDOUT)
 results.append({'name':name,'command':command,'cwd':'source/candidate','exitCode':r.returncode,'log':name+'-final.log'});print(name,r.returncode,flush=True)
 if r.returncode:print((E/(name+'-final.log')).read_text()[-6000:]);break
(E/'final-command-results.json').write_text(json.dumps(results,indent=2)+'\n');assert len(results)==len(commands) and all(r['exitCode']==0 for r in results)
r=a.inspect_output(C/'dist',E/'final-inspection-dist');a.save(E/'final-inspection-result.json',r)
sys.path.insert(0,str(C/'scripts'));import qa_occurrences as q
for name,mode,dist in [('private','private',C/'dist'),('production-like','production-like',E/'final-inspection-dist')]:a.save(E/(name+'-exact-occurrences.json'),q.check(dist,mode))
a.save(E/'environment-boundary.json',{'releaseProviderKeysAbsent':list(a.BOUNDARY),'allAbsent':all(not env.get(k) for k in a.BOUNDARY),'privateSuitesBeforeOutputTransform':True,'productionLikeOutputSeparate':True,'sourceRevision':None,'providerNetworkCalls':0})
print('Twelve source-contained commands and new offline production-like output passed. Browser/public release remain unverified.')
