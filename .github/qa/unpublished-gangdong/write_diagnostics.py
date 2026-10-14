"""Small failure receipt; never copies environment variables, tokens or entire logs."""
from adapter import *
import os

def diagnostics(workspace):
    root=workspace/'evidence';rows=[]
    paths=['gangdong-grouping.log','gangdong/logs/browser-capture.log','gangdong/logs/native-build-first.log','gangdong/logs/native-tests-first.log','gangdong/logs/control-tests.log']
    for rel in paths:
        p=root/rel
        if p.is_file():
            safe_file(root,rel)
            with p.open('rb')as f:
                size=p.stat().st_size;f.seek(max(0,size-8192));tail=f.read(8192).decode('utf-8',errors='replace')
            rows.append({'path':rel,'totalBytes':size,'tailByteLimit':8192,'tail':tail})
    return {'schema':'gangdong-bounded-diagnostics-v1','sourceSha':SOURCE_SHA,'controlSha':os.environ['GITHUB_SHA'],'runId':os.environ['GITHUB_RUN_ID'],'runAttempt':os.environ['GITHUB_RUN_ATTEMPT'],'groupingOutcome':os.environ.get('GROUPING_OUTCOME'),'status':'diagnostic-only-no-success-claim','logs':rows,'pixelReview':'pending','publicHttpVerified':False}

if __name__=='__main__':
    validate_environment(validate_spec(load(SPEC_PATH)))
    root=Path(os.environ['GITHUB_WORKSPACE']);result=diagnostics(root)
    data=compact(result);require(len(data)<128*1024,'Diagnostic size ceiling')
    write(root/'evidence/gangdong-artifact-metadata/diagnostics.json',result)
