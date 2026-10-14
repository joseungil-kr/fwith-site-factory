"""Exact Seocho sealed-artifact selection. GET-only downloads occur in the workflow."""
from pathlib import Path, PurePosixPath
import argparse, json, os, re, stat, subprocess, sys, zipfile
from reused import digest, compact, manifest, write_json

HERE=Path(__file__).resolve().parent
REPOSITORY='joseungil-kr/fwith-site-factory'
SOURCE_BRANCH='source/seoul-seocho-production-successor-20261014'
SOURCE_ROOT='site-factory/seoul-seocho-flower'
ORIGIN='https://seoul-seocho.fwith.kr'
WORKER='seoul-seocho-flower-guide'
COPY_SHA='c466be6fd967a690cb008ca74ae35d7dec8e93f522cb0b19c8ae86a375b8b53c'
FROZEN_SHA='2a4de872c85da0b66815c5e5668e0c7de9ce4341'
BUILD_WORKFLOW='.github/workflows/seoul-seocho-production-build-only.yml'
ISSUE_TITLE='[SEOCHO-PRODUCTION-ARTIFACT-QA] 20261014'
ROUTES=['/','/regions/','/regions/seocho-funeral-wreath/','/regions/seocho-celebration-wreath/','/404.html']
VIEWPORTS=[(320,740),(390,844),(1280,900)]

def require(ok,message):
    if not ok:raise ValueError(message)

def load_json(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def validate_bindings(data):
    keys={'schemaVersion','repository','sourceBranch','sourceRoot','sourceSha','buildControlSha','runId','artifactId',
          'archiveSha256','releaseManifestSha256','outputFilesSha256','bindingSha256','sourceContractSha256','uiSpecSha256'}
    require(set(data)==keys,'binding keys')
    require(type(data['schemaVersion']) is int and data['schemaVersion']==1,'binding version')
    require(data['repository']==REPOSITORY and data['sourceBranch']==SOURCE_BRANCH and data['sourceRoot']==SOURCE_ROOT,'fixed source identity')
    require(all(isinstance(data[k],str) and re.fullmatch('[0-9a-f]{40}',data[k]) for k in ['sourceSha','buildControlSha']),'replace exact source/control SHA')
    require(all(isinstance(data[k],str) and re.fullmatch('[1-9][0-9]*',data[k]) for k in ['runId','artifactId']),'replace exact run/artifact IDs')
    require(all(isinstance(data[k],str) and re.fullmatch('[0-9a-f]{64}',data[k]) for k in keys if k.endswith('Sha256')),'replace exact artifact/binding digests')
    return data

def verify_runner(env=None,event=None,bindings_raw=None):
    env=os.environ if env is None else env
    require(env.get('GITHUB_ACTIONS')=='true','GitHub Actions runner required')
    require(env.get('GITHUB_REPOSITORY')==REPOSITORY and env.get('GITHUB_REF')=='refs/heads/main','QA repository/main')
    require(env.get('GITHUB_ACTOR')=='joseungil-kr' and env.get('GITHUB_TRIGGERING_ACTOR')=='joseungil-kr','owner actor')
    require(env.get('GITHUB_RUN_ATTEMPT')=='1','first attempt only')
    require(re.fullmatch('[0-9a-f]{40}',env.get('GITHUB_SHA','')),'QA exact control SHA')
    require(env.get('GITHUB_EVENT_NAME')=='issues','owner issue required')
    event=load_json(env['GITHUB_EVENT_PATH']) if event is None else event
    issue=event.get('issue',{})
    require(event.get('action')=='opened' and issue.get('title')==ISSUE_TITLE,'exact opened issue')
    require(issue.get('user',{}).get('login')=='joseungil-kr' and issue.get('user',{}).get('type')=='User','owner User issue')
    require(event.get('repository',{}).get('full_name')==REPOSITORY,'event repository')
    require(isinstance(issue.get('body'),str) and len(issue['body'])<2048,'bounded JSON request')
    raw=(HERE/'bindings.json').read_bytes() if bindings_raw is None else bindings_raw
    body=json.loads(issue['body'])
    require(type(body.get('schemaVersion')) is int and body=={'schemaVersion':1,'expected_control_revision':env['GITHUB_SHA'],
            'bindings_sha256':digest(raw),'scope':'sealed-production-artifact-loopback-only'},'exact QA request')

def verify_checkout(root,sha):
    def git(*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
    require(git('rev-parse','HEAD')==sha,'QA checkout SHA')
    require(not git('status','--porcelain','--untracked-files=all'),'QA checkout changed')

def validate_metadata(b,run,artifact):
    expected={'id':int(b['runId']),'head_sha':b['buildControlSha'],'head_branch':'main','path':BUILD_WORKFLOW,
              'status':'completed','conclusion':'success','run_attempt':1,'event':'issues'}
    require(all(run.get(k)==v for k,v in expected.items()),'exact successful first-attempt production build')
    require(run.get('repository',{}).get('full_name')==REPOSITORY,'build repository')
    require(run.get('actor',{}).get('login')=='joseungil-kr' and run.get('triggering_actor',{}).get('login')=='joseungil-kr','build owner')
    require(artifact.get('id')==int(b['artifactId']) and artifact.get('name')=='seoul-seocho-production-build-'+b['runId'],'exact production artifact')
    require(artifact.get('expired') is False and artifact.get('digest')=='sha256:'+b['archiveSha256'],'artifact digest/expiry')
    wr=artifact.get('workflow_run',{})
    require(wr.get('id')==int(b['runId']) and wr.get('head_sha')==b['buildControlSha'] and wr.get('head_branch')=='main','artifact build binding')
    require(type(artifact.get('size_in_bytes')) is int and 0<artifact['size_in_bytes']<=32*1024*1024,'archive size')

def extract_bound_archive(archive,destination,expected_sha):
    require(digest(archive.read_bytes())==expected_sha,'downloaded ZIP digest mismatch')
    require(not destination.exists(),'extraction destination must be new')
    with zipfile.ZipFile(archive) as z:
        items=z.infolist();names=[i.filename for i in items]
        require(len(names)==len(set(names)) and len(items)<5000,'duplicate/oversized ZIP listing')
        require(sum(i.file_size for i in items)<=128*1024*1024,'ZIP expansion limit')
        for item in items:
            require(item.orig_filename==item.filename,'normalized ZIP path forbidden')
            p=PurePosixPath(item.filename);mode=item.external_attr>>16
            require(not item.flag_bits&1 and not item.filename.startswith('/') and '\\' not in item.filename and '\x00' not in item.filename,'unsafe ZIP path')
            require(p.parts and all(x not in ('.','..') and not x.startswith('.') for x in p.parts),'ZIP traversal/hidden path')
            require(p.as_posix()==item.filename.rstrip('/'),'noncanonical ZIP path')
            require(stat.S_IFMT(mode) in (0,stat.S_IFREG,stat.S_IFDIR),'ZIP nonregular/symlink')
            require(item.filename=='release.json' or p.parts[0]=='dist','unexpected artifact root')
        destination.mkdir(parents=True)
        for item in items:
            p=destination/item.filename
            if item.is_dir():p.mkdir(parents=True,exist_ok=True)
            else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(item))
    require({p.name for p in destination.iterdir()}=={'dist','release.json'},'exact release root')
    return destination

def inspect_release(b,release,spec,production_binding,source_contract):
    require(spec['schemaVersion']==1 and spec['customerCopySha256']==COPY_SHA,'accepted copy binding')
    require([p['url'] for p in spec['pages']]==ROUTES[2:4],'exact accepted article metadata')
    require(production_binding['sourceRevision']==b['sourceSha'] and production_binding['sourceContractSha256']==b['sourceContractSha256'],'source/prod binding')
    require(source_contract['expectedSourceRevision']==b['sourceSha'] and source_contract['sourceBranch']==SOURCE_BRANCH
            and source_contract['sourceRoot']==SOURCE_ROOT and source_contract['frozenSourceRevision']==FROZEN_SHA
            and source_contract['customerCopySha256']==COPY_SHA and len(source_contract['sealedPins'])==98,'frozen/source contract')
    require(all(source_contract['protectedFiles'].get(k)==v for k,v in spec['sourceFiles'].items()),'accepted UI source bytes')
    raw=(release/'release.json').read_bytes();data=json.loads(raw);files=manifest(release/'dist')
    require(digest(raw)==b['releaseManifestSha256'],'exact release JSON bytes')
    require(digest(compact(files))==b['outputFilesSha256'],'complete dist file-map digest')
    expected={'schemaVersion':1,'repository':REPOSITORY,'sourceBranch':SOURCE_BRANCH,'sourceRoot':SOURCE_ROOT,
        'revision':b['sourceSha'],'controlRevision':b['buildControlSha'],'runId':b['runId'],'origin':ORIGIN,'worker':WORKER,
        'indexable':True,'bindingSha256':b['bindingSha256'],'sourceContractSha256':b['sourceContractSha256'],'files':files}
    require(data==expected,'exact release identity/full inventory')
    # Reviewed control helper, not code from the untrusted downloaded artifact.
    sys.path.insert(0,str(HERE.parent))
    from production_output import inspect_dist
    report=inspect_dist(release/'dist',{'mode':'production','indexable':True,'origin':ORIGIN,'revision':b['sourceSha']},production_binding['proof'])
    require(report['files']==files,'production output contract inventory')
    for kind,item in spec['banners'].items():
        require(files.get('images/shared-banners/'+item['file'])==item['sha256'],'accepted banner pixels: '+kind)
    return {'bindings':b,'files':files,'productionOutputContract':report,'publicHTTPVerified':False,'pixelReview':'pending'}

def read_control_inputs(b):
    paths={'uiSpecSha256':HERE/'ui-spec.json','bindingSha256':HERE.parent/'production-binding.json',
           'sourceContractSha256':HERE.parent/'production-source-contract.json'}
    for key,path in paths.items():require(digest(path.read_bytes())==b[key],'control input digest: '+key)
    return tuple(load_json(paths[k]) for k in paths)

def summarize_run(run):
    return {**{k:run.get(k) for k in ['id','status','conclusion','head_sha','head_branch','path','event','run_attempt','html_url']},
            'actorLogin':run['actor']['login'],'triggeringActorLogin':run['triggering_actor']['login'],'repository':run['repository']['full_name']}

def summarize_artifact(a):
    return {**{k:a.get(k) for k in ['id','name','size_in_bytes','digest','expired','url']},
            'workflow_run':{k:a['workflow_run'].get(k) for k in ['id','head_sha','head_branch']}}

def main():
    require(sys.platform=='linux','Linux runner only')
    verify_runner();verify_checkout(HERE.parents[2],os.environ['GITHUB_SHA'])
    b=validate_bindings(load_json(HERE/'bindings.json'));read_control_inputs(b)
    print(json.dumps({'state':'exact-artifact-selected','runId':b['runId'],'artifactId':b['artifactId'],'sourceSha':b['sourceSha']}))

if __name__=='__main__':main()
