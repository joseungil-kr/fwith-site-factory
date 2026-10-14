"""Partition actual evidence without omitting files; 24 MiB pre-compression ceiling per upload."""
from pathlib import Path
import os,shutil
from adapter import *
LIMIT=24*1024*1024
EXPECTED_GROUPS={'reports','dist'}|{'screen_'+str(w)+'_'+slug for w,h in VIEWPORTS for slug in ['home','regions__gangdong_condolence_wreath','regions__gangdong_wedding_wreath','regions','404_html']}

def group_for(rel):
    if rel.startswith('screenshots/'):
        parts=rel.split('/');require(len(parts)==4 and parts[1] in {'320','390','1280'},'Unexpected screenshot group path')
        slugs={'home','regions--gangdong-condolence-wreath','regions--gangdong-wedding-wreath','regions','404-html'}
        require(parts[2]in slugs,'Unknown screenshot route group')
        return 'screen_'+parts[1]+'_'+parts[2].replace('-','_')
    if rel.startswith('dist/'):return 'dist'
    require('/'not in rel or rel.startswith('logs/'),'Unexpected report artifact path')
    return 'reports'

def prepare(evidence,staging):
    require(not staging.exists(),'Artifact staging already exists')
    staging.mkdir(parents=True);groups={};seen=[]
    for p in sorted(evidence.rglob('*')):
        require(not p.is_symlink(),'Evidence symlink')
        if not p.is_file():continue
        rel=p.relative_to(evidence).as_posix();key=group_for(rel);row=artifact_file_fact(p,evidence)
        group=groups.setdefault(key,{'key':key,'files':[],'totalBytes':0,'maxUncompressedBytes':LIMIT})
        group['files'].append(row);group['totalBytes']+=row['bytes'];seen.append(rel)
        dest=staging/key/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    require(bool(groups) and len(seen)==len(set(seen)),'Empty/duplicate artifact coverage')
    for group in groups.values():
        # Reserve 1 MiB for per-entry archive metadata. upload-artifact compression cannot exceed the limit by ordinary ZIP overhead.
        require(group['totalBytes']+len(group['files'])*1024<LIMIT,'Artifact group exceeds safe download ceiling: '+group['key'])
        require(len(group['files'])<1000,'Artifact group entry ceiling')
    expected=EXPECTED_GROUPS
    require(set(groups)<=expected,'Unknown group')
    return {'schema':'gangdong-artifact-index-v1','sourceSha':SOURCE_SHA,'controlSha':os.environ.get('GITHUB_SHA'),'runId':os.environ.get('GITHUB_RUN_ID'),'runAttempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'groups':list(groups.values()),'expectedGroups':sorted(expected),'missingGroups':sorted(expected-set(groups)),'completeExpectedGroups':set(groups)==expected,'allEvidencePathsCoveredOnce':True,'coveragePathCount':len(seen),'downloadCeilingBytes':LIMIT,'pixelReview':'pending','publicHttpVerified':False}

if __name__=='__main__':
    source,evidence=validate_environment(validate_spec(load(SPEC_PATH)))
    root=Path(os.environ['GITHUB_WORKSPACE'])/'evidence';index=prepare(evidence,root/'gangdong-artifact-groups')
    write(root/'gangdong-artifact-metadata/artifact-index.json',index)
    with open(os.environ['GITHUB_OUTPUT'],'a')as f:
        for group in index['groups']:f.write(group['key']+'=true\n')
