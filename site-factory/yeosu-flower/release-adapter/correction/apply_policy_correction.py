"""Mandatory deterministic correction after the frozen Yeosu baseline build.
This is a local build transform only. It grants no deployment authority.
It uses no network, provider credentials, git or IndexNow calls.
"""
from pathlib import Path
import hashlib,json,argparse,re
HERE=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def patch_bytes(files,spec,baseline):
 if set(files)!=set(baseline['files']):raise ValueError('baseline_file_inventory_mismatch')
 for name,want in baseline['files'].items():
  if sha(files[name])!=want:raise ValueError('baseline_bytes_mismatch:'+name)
 allowed=set(spec['allowedChangedFiles']);out=dict(files)
 for op in spec['operations']:
  if op['file'] not in allowed:raise ValueError('out_of_scope_operation')
  raw=out[op['file']].decode();n=raw.count(op['before'])
  if n!=op['expectedOccurrences']:raise ValueError('exact_replacement_count_mismatch:'+op['file'])
  out[op['file']]=raw.replace(op['before'],op['after']).encode()
 changed={p for p in files if files[p]!=out[p]}
 if changed!=allowed:raise ValueError('exact_changed_files_mismatch')
 for p,want in spec['resultHtmlSha256'].items():
  if sha(out[p])!=want:raise ValueError('corrected_output_hash_mismatch:'+p)
 return out

def correct_dist(dist,revision):
 if not re.fullmatch(r'[0-9a-f]{40}',revision):raise ValueError('full_build_revision_required')
 spec=json.loads((HERE/'patch-spec.json').read_text());raw=(HERE/'baseline-output-manifest.json').read_bytes()
 if sha(raw)!=spec['baselineOutputManifestSha256']:raise ValueError('baseline_manifest_digest_mismatch')
 baseline=json.loads(raw);old=baseline['revision']
 if any(p.is_symlink() for p in dist.rglob('*')):raise ValueError('output_symlink_forbidden')
 actual={p.relative_to(dist).as_posix():p.read_bytes() for p in dist.rglob('*') if p.is_file()}
 normalized=dict(actual);html_files=[p for p in actual if p.endswith('.html')]
 if len(html_files)!=4:raise ValueError('exact_four_html_required')
 for name in html_files:
  text=actual[name].decode();needle='<meta name="site-factory-revision" content="'+revision+'">'
  if text.count(needle)!=1:raise ValueError('exact_revision_meta_required:'+name)
  normalized[name]=text.replace(needle,'<meta name="site-factory-revision" content="'+old+'">').encode()
 corrected=patch_bytes(normalized,spec,baseline)
 final=dict(corrected)
 for name in html_files:
  final[name]=corrected[name].replace(('<meta name="site-factory-revision" content="'+old+'">').encode(),('<meta name="site-factory-revision" content="'+revision+'">').encode())
 for name,data in final.items():
  if data!=actual[name]:(dist/name).write_bytes(data)
 # Re-read files, not only in-memory results, before reporting.
 reread={p.relative_to(dist).as_posix():p.read_bytes() for p in dist.rglob('*') if p.is_file()}
 if reread!=final:raise ValueError('corrected_output_disk_readback_failed')
 changes=sorted(p for p in actual if actual[p]!=final[p])
 if changes!=sorted(spec['allowedChangedFiles']):raise ValueError('exact_three_corrected_html_required')
 return {'state':'LOCAL_BUILD_CONTENT_CORRECTION_VERIFIED','revision':revision,'baselineSourceRevision':old,'correctionSpecSha256':sha((HERE/'patch-spec.json').read_bytes()),'contentChangedFiles':changes,'historicalOutputRevisionOnlyChange':['404.html'] if revision!=old else [],'unchangedNonHtmlFiles':14,'files':{p:sha(b) for p,b in final.items()},'publicationPerformed':False,'indexNowSubmitted':False,'deploymentAuthorityGranted':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dist',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
 print(json.dumps(correct_dist(Path(a.dist),a.revision),ensure_ascii=False,sort_keys=True))
