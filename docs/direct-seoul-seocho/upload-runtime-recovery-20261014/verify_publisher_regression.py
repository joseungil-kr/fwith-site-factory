"""Offline: feed real pinned-function filesystem results into unchanged publisher."""
from pathlib import Path
import hashlib, json, os, sys

OUT=Path(__file__).resolve().parent
TASK=OUT.parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(TASK/'release-execution-20261014/scripts/direct-seoul-seocho'))
import publish as p

load=lambda x:json.loads(Path(x).read_text(encoding='utf-8'))
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
repro=load(OUT/'tmp-reproduction.json')
scratch=Path(repro['scratchDirectory']).resolve()
assert scratch.is_relative_to(OUT)
before_source=sha(p.__file__)
manifest=load(TASK/'seocho-production-runtime-20261014/build/release.json')
os.environ['REVISION']=manifest['revision']
initial=Path.cwd()
rows=[]
try:
    for name,expected in [('old','unexpected_release_files'),('fixed',None)]:
        os.chdir(scratch/name)
        try:
            actual=p.artifact()
            assert expected is None, 'Dirty artifact accepted'
            rows.append({'case':name,'state':actual['state'],'all23DistHashesMatch':p.gate.inventory(Path('release/dist'))==manifest['files']})
        except ValueError as error:
            assert str(error)==expected
            rows.append({'case':name,'error':str(error),'rejected':True})
    # A fresh unrelated file must still be rejected, even after the isolated fix.
    os.chdir(scratch/'fixed')
    rogue=Path('release/UNEXPECTED.txt');rogue.write_text('offline regression only',encoding='utf-8')
    try:
        try:p.artifact();raise AssertionError('Unexpected file accepted')
        except ValueError as error:
            assert str(error)=='unexpected_release_files'
            rows.append({'case':'unexpected_file_after_fix','error':str(error),'rejected':True})
    finally:rogue.unlink()
    assert p.gate.inventory(Path('release/dist'))==manifest['files']
    p.artifact()
finally:os.chdir(initial)
assert sha(p.__file__)==before_source
report={'schemaVersion':1,'state':'PASS_UNCHANGED_PUBLISHER_REGRESSION','publisherPath':str(Path(p.__file__).relative_to(TASK)),
        'publisherSha256':before_source,'releaseReviewPatched':False,'gatePatched':False,'actualProductionManifestSha256':sha(TASK/'seocho-production-runtime-20261014/build/release.json'),
        'pinnedFunctionReproductionSha256':sha(OUT/'tmp-reproduction.json'),'cases':rows,'distFileCount':23,
        'artifactAllowlistUnchanged':True,'sourceModified':False,'networkCalls':0,'liveDeployment':False}
(OUT/'publisher-regression.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
