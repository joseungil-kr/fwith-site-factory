"""Upload receipts remain tool reports until independent download/hash/pixel review."""
import os,re,json
from adapter import *
from prepare_artifacts import EXPECTED_GROUPS,LIMIT

def receipt(env):
    for k in ['ARTIFACT_ID','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT']:
        require(bool(re.fullmatch('[1-9][0-9]*',env.get(k,''))),'Invalid receipt integer')
    require(env['GITHUB_RUN_ATTEMPT']=='1','Unexpected rerun')
    require(bool(re.fullmatch('[0-9a-f]{64}',env.get('ARTIFACT_DIGEST',''))),'Missing artifact digest')
    url=f"https://github.com/joseungil-kr/fwith-site-factory/actions/runs/{env['GITHUB_RUN_ID']}/artifacts/{env['ARTIFACT_ID']}"
    require(env.get('ARTIFACT_URL')==url,'Wrong artifact URL')
    require(bool(re.fullmatch('[0-9a-f]{40}',env.get('GITHUB_SHA',''))),'Wrong control SHA')
    return {'artifactId':env['ARTIFACT_ID'],'artifactURL':url,'artifactArchiveSha256':env['ARTIFACT_DIGEST'],'evidenceLevel':'tool-reported-upload-receipt','independentArtifactDownloadVerified':False}

def collect(index,reported,env):
    require(index['schema']=='gangdong-artifact-index-v1','Unknown artifact index')
    require(index['sourceSha']==SOURCE_SHA and index['controlSha']==env['GITHUB_SHA'] and index['runId']==env['GITHUB_RUN_ID'] and index['runAttempt']==env['GITHUB_RUN_ATTEMPT']=='1','Artifact index/run binding')
    require(set(index['expectedGroups'])==EXPECTED_GROUPS and len(index['expectedGroups'])==17,'Expected artifact groups changed')
    require(set(g['key']for g in index['groups'])<=EXPECTED_GROUPS,'Unknown index group')
    require(set(index['missingGroups'])==EXPECTED_GROUPS-set(g['key']for g in index['groups']),'Incorrect missing group list')
    require(type(reported)is dict and set(reported)==set(index['expectedGroups']),'Receipt group schema')
    require(len({g['key']for g in index['groups']})==len(index['groups']),'Duplicate index group')
    rows=[];missing=[]
    for group in index['groups']:
        require(type(group['totalBytes'])is int and 0<=group['totalBytes']<LIMIT and group['maxUncompressedBytes']==LIMIT,'Artifact group size contract')
        key=group['key'];data=reported[key]
        require(type(data)is dict and set(data)=={'id','url','digest'} and all(type(v)is str for v in data.values()),'Malformed group receipt')
        if not all(data.values()):missing.append(key);continue
        fact=receipt({**env,'ARTIFACT_ID':data['id'],'ARTIFACT_URL':data['url'],'ARTIFACT_DIGEST':data['digest']})
        rows.append({'group':key,'artifactName':'gangdong-'+key+'-'+env['GITHUB_SHA']+'-'+env['GITHUB_RUN_ATTEMPT'],**fact,'uncompressedBytes':group['totalBytes'],'fileCount':len(group['files'])})
    require(len({r['artifactId']for r in rows})==len(rows) and len({r['artifactURL']for r in rows})==len(rows),'Duplicate artifact ID/URL')
    return rows,missing

if __name__=='__main__':
    validate_environment(validate_spec(load(SPEC_PATH)))
    root=Path(os.environ['GITHUB_WORKSPACE'])/'evidence/gangdong-artifact-metadata'
    index=load(root/'artifact-index.json');reported=json.loads(os.environ['EVIDENCE_ARTIFACTS_JSON']);rows,missing=collect(index,reported,os.environ)
    write(root/'artifact-receipts.json',{'schema':'gangdong-actions-artifact-receipts-v1','sourceSha':SOURCE_SHA,'controlSha':os.environ['GITHUB_SHA'],'runId':os.environ['GITHUB_RUN_ID'],'runAttempt':os.environ['GITHUB_RUN_ATTEMPT'],'actor':os.environ['GITHUB_ACTOR'],'indexSha256':digest((root/'artifact-index.json').read_bytes()),'groups':rows,'failedOrMissingUploads':missing,'missingEvidenceGroups':index['missingGroups'],'independentArtifactDownloadVerified':False,'pixelReview':'pending','publicHttpVerified':False})
    require(not missing,'Artifact uploads missing: '+str(missing))
