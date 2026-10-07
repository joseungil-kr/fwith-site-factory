"""Fail-closed evidence gate, scoped only to the six-site 2026-10-07 release."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path

def require(ok,message):
    if not ok:raise ValueError(message)
def digest(b):return hashlib.sha256(b).hexdigest()
def compact(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def git(checkout,*args):return subprocess.check_output(['git','-C',str(checkout),*args])
def normalized(v):return v.strip().casefold() if isinstance(v,str) else ''
def check(p,a,phase,revision,branch,root,files):
    require(p['enabled'] is True,'Release inactive')
    require(not p.get('unresolvedBlockers'),'Unresolved independent-review blockers')
    require(phase in ('preview','production'),'Invalid phase')
    require(re.fullmatch('[0-9a-f]{40}',revision) is not None,'Full source SHA required')
    require(branch==p['previewBranch' if phase=='preview' else 'branch'],'Wrong branch')
    require(root==p['root'],'Wrong source root')
    require(a['revision']==revision,'Wrong source revision')
    for k in ('siteKey','productionOrigin','worker'):require(a[k]==p[k],'Wrong identity/hostname: '+k)
    require(a['sourceFiles']==files and bool(files),'Source bundle mismatch')
    require(a.get('providerBaselineSha256',{}).get(phase)==p.get('providerBaselineSha256',{}).get(phase) and re.fullmatch('[0-9a-f]{64}',p.get('providerBaselineSha256',{}).get(phase,'')) is not None,'Missing reviewed provider-state digest')
    proof=a[phase]
    require(proof['status']=='passed','Pending independent proof')
    author,reviewer=normalized(a['author']),normalized(proof['reviewer'])
    require(bool(author) and bool(reviewer) and author!=reviewer,'Independent author/reviewer missing')
    require(author==normalized(p.get('assignedAuthorId')) and reviewer==normalized(p.get('assignedReviewerId')),'Unassigned author/reviewer')
    require(re.fullmatch('[0-9a-f]{64}',proof['artifactManifestSha256'] or '') is not None,'Artifact bundle not reviewed')
    for key in ('sourceReview','immutableBaseline','nativeGates','routes','assets','cta','catalog','canonicalGraph'):
        require(proof['checks'].get(key) is True,'Unverified '+key)
    if phase=='preview':require(p['previewWorker'] and p['previewOrigin'],'No verified isolated preview target')
    else:
        require(proof.get('pixelEvidenceMode')==p.get('pixelReviewMode'),'Wrong or missing pixel evidence mode')
        for key in ('pixelQA','productionIndexableBuild','productionArtifactReview','unreleasedDeltaReconciled'):
            require(proof['checks'].get(key) is True,'Unverified '+key)
    return proof

def tracked_files(checkout,root,revision='HEAD'):
    out={}
    for row in git(checkout,'ls-tree','-rz',revision,'--',root).split(b'\0'):
        if not row:continue
        meta,path=row.split(b'\t');mode,kind,blob=meta.split()
        require(kind==b'blob' and mode in (b'100644',b'100755'),'Nonregular source entry')
        out[path.decode()]=digest(git(checkout,'cat-file','blob',blob.decode()))
    return out

def worktree(checkout,files,root,revision,after,revision_key="revision"):
    generated=root+'/src/data/build-revision.json'
    if after:require(json.loads((checkout/generated).read_text())=={revision_key:revision},'Incorrect generated build revision')
    for name,h in files.items():
        f=checkout/name;require(f.is_file() and not f.is_symlink(),'Missing/symlink source '+name)
        if after and name==generated:
            require(json.loads(f.read_text())=={revision_key:revision},'Incorrect generated build revision')
        else:require(digest(f.read_bytes())==h,'Source worktree mutated '+name)

def artifacts(root):return {str(f.relative_to(root)):digest(f.read_bytes()) for f in sorted(root.rglob('*')) if f.is_file()}

def evidence(authority,p,a,phase,proof):
    rel=proof.get('evidenceFile','');require(rel.startswith('.github/manual-release-20261007/evidence/') and '..' not in Path(rel).parts,'Invalid evidence path')
    candidate=authority/rel
    require(all(not (authority/Path(*Path(rel).parts[:i])).is_symlink() for i in range(1,len(Path(rel).parts)+1)),'Evidence symlink forbidden')
    raw=candidate.read_bytes();require(digest(raw)==proof.get('evidenceSha256'),'Evidence bytes mismatch')
    doc=json.loads(raw)
    expected={'siteKey':p['siteKey'],'revision':a['revision'],'phase':phase,'author':a['author'],'reviewer':proof['reviewer'],'sourceManifestSha256':digest(compact(a['sourceFiles'])),'artifactManifestSha256':proof['artifactManifestSha256'],'checks':proof['checks'],'environment':p['environments'][phase],'baselineRevision':a['baselineRevision'],'deltaSha256':a['deltaSha256'],'controlRevision':a['controlRevision'],'providerBaselineSha256':p['providerBaselineSha256'][phase],'pixelEvidenceMode':proof.get('pixelEvidenceMode')}
    require(doc==expected,'Evidence document does not attest exact release')

def lineage(checkout,p,a,phase):
    branch=p['previewBranch' if phase=='preview' else 'branch'];head=git(checkout,'ls-remote','--heads','origin','refs/heads/'+branch).decode().split()
    require(len(head)==2 and head[0]==a['revision'],'Remote branch moved or absent')
    require(re.fullmatch('[0-9a-f]{40}',a['baselineRevision'] or '') is not None,'Missing reviewed baseline')
    subprocess.run(['git','-C',str(checkout),'merge-base','--is-ancestor',a['baselineRevision'],a['revision']],check=True)
    delta=git(checkout,'diff','--binary','--full-index',a['baselineRevision'],a['revision'],'--',p['root'])
    require(digest(delta)==a['deltaSha256'],'Unreviewed baseline delta')

def main():
    policy_path=Path(sys.argv[1]);p=json.loads(policy_path.read_text());a=json.loads(Path(sys.argv[2]).read_text());checkout=Path(sys.argv[3]);phase=sys.argv[4];after=len(sys.argv)>5 and sys.argv[5]=='artifact';authority=policy_path.parents[2];control=Path(__file__).resolve().parents[2]
    revision=git(checkout,'rev-parse','HEAD').decode().strip();files=tracked_files(checkout,p['root'],revision)
    proof=check(p,a,phase,revision,os.environ['GITHUB_REF_NAME'],p['root'],files)
    require(git(control,'rev-parse','HEAD').decode().strip()==a['controlRevision'],'Unreviewed control revision')
    require(tracked_files(control,'scripts/manual-release-20261007')==a['controlFiles'],'Unreviewed helper bytes')
    workflow=p['workflowPath'];require(digest(git(checkout,'show',revision+':'+workflow))==a['workflowSha256'],'Unreviewed workflow bytes')
    authority_sha=git(authority,'rev-parse','HEAD').decode().strip()
    main_head=git(authority,'ls-remote','--heads','origin','refs/heads/main').decode().split()
    require(len(main_head)==2 and main_head[0]==authority_sha,'Trusted approval main changed; restart review gate')
    evidence(authority,p,a,phase,proof);lineage(checkout,p,a,phase);worktree(checkout,files,p['root'],revision,after,p['generatedRevisionKey'])
    config=json.loads((checkout/p['root']/p['previewConfig' if phase=='preview' else 'productionConfig']).read_text())
    require(config['name']==p['previewWorker' if phase=='preview' else 'worker'],'Wrong config Worker')
    require(config['assets']['directory'] in ('./dist/','./dist','dist'),'Wrong assets')
    require(set(config)<=set(('$schema','assets','compatibility_date','name','workers_dev','routes')),'Unreviewed config capability')
    if phase=='preview':require(not config.get('routes') and config.get('workers_dev') is True,'Preview domain capability forbidden')
    else:
        require(all(r=={'pattern':p['productionOrigin'].removeprefix('https://'),'custom_domain':True} for r in config.get('routes',[])),'Wrong domain')
        registry=json.loads((authority/'.github/site-factory-sites.json').read_text())['sites'][p['siteKey']]
        require(registry['approvedRevision']==revision and registry['approvalEvidenceUrl']==proof['evidenceUrl'],'Trusted production approval mismatch')
    if after:require(digest(compact(artifacts(checkout/p['root']/'dist')))==proof['artifactManifestSha256'],'Unreviewed artifact bytes')
    print('Exact source, independent evidence, lineage, control and artifact verified; authority='+git(authority,'rev-parse','HEAD').decode().strip())
if __name__=='__main__':main()
