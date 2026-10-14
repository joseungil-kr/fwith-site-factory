"""Linux runner entry point: validate, extract sealed artifact, capture, seal evidence."""
from pathlib import Path
from importlib.metadata import version
import argparse,json,os,sys,traceback
from artifact_bind import (HERE,require,verify_runner,verify_checkout,load_json,validate_bindings,read_control_inputs,
 validate_metadata,extract_bound_archive,inspect_release,summarize_run,summarize_artifact)
from reused import digest,manifest,write_json

def seal(output):
    files={p.relative_to(output).as_posix():digest(p.read_bytes()) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='evidence-manifest.json'}
    write_json(output/'evidence-manifest.json',{'qaControlSha':os.environ.get('GITHUB_SHA'),'qaRunId':os.environ.get('GITHUB_RUN_ID'),
       'qaRunAttempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'files':files,'pixelReview':'pending','publicationAuthorized':False,'publicHTTPVerified':False})

def main():
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--seal',action='store_true');a=p.parse_args()
    output=a.output.resolve();output.mkdir(parents=True,exist_ok=True)
    if a.seal:seal(output);return 0
    result={'state':'machine-qa-failed','pixelReview':'pending','publicHTTPVerified':False,'publicationAuthorized':False}
    try:
        require(sys.platform=='linux','Linux runner only');verify_runner();verify_checkout(HERE.parents[2],os.environ['GITHUB_SHA'])
        require(version('playwright')=='1.63.0','pinned Playwright required')
        b=validate_bindings(load_json(HERE/'bindings.json'));spec,production_binding,source_contract=read_control_inputs(b)
        run=load_json(a.inputs/'run.json');artifact=load_json(a.inputs/'artifact.json');validate_metadata(b,run,artifact)
        require((a.inputs/'artifact.zip').stat().st_size==artifact['size_in_bytes'],'archive exact size')
        release=extract_bound_archive(a.inputs/'artifact.zip',output/'release',b['archiveSha256'])
        proof=inspect_release(b,release,spec,production_binding,source_contract)
        proof.update(qaControlSha=os.environ['GITHUB_SHA'],qaRunId=os.environ['GITHUB_RUN_ID'],qaRunAttempt=os.environ['GITHUB_RUN_ATTEMPT'],
          bindingsSha256=digest((HERE/'bindings.json').read_bytes()),runnerFiles={p.name:digest(p.read_bytes()) for p in sorted(HERE.iterdir()) if p.is_file()})
        write_json(output/'artifact-binding.json',proof);write_json(output/'build-run-api.json',summarize_run(run));write_json(output/'build-artifact-api.json',summarize_artifact(artifact))
        from browser_rendering import inspect
        report=inspect(release/'dist',output/'rendering',spec['pages'],b['sourceSha'],spec)
        require(manifest(release/'dist')==proof['files'],'dist changed during capture')
        require(digest((release/'release.json').read_bytes())==b['releaseManifestSha256'],'release manifest changed')
        verify_checkout(HERE.parents[2],os.environ['GITHUB_SHA'])
        result.update(state='captured-awaiting-independent-pixel-review',machineChecksPassed=True,artifactBinding=proof,
          coverage=report['coverage'],playwrightVersion=version('playwright'),browserVersion=report['browserVersion'],scope='exact sealed production artifact, loopback only')
    except Exception:result.update(machineChecksPassed=False,error=traceback.format_exc())
    write_json(output/'capture-results.json',result);seal(output)
    print(json.dumps({k:v for k,v in result.items() if k not in ('artifactBinding','error')},ensure_ascii=False))
    return 0 if result.get('machineChecksPassed') else 1

if __name__=='__main__':sys.exit(main())
