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


def apply_layout(files,spec):
 layout=spec['layoutCorrection']
 keys={'scope','sourceCSS','sourceCSSSha256','appendCSS','resultCSS','resultCSSSha256','htmlFiles','stylesheetReferencesPerHTML','resultNormalizedFilesSha256'}
 if type(layout) is not dict or set(layout)!=keys:raise ValueError('exact_layout_contract_required')
 old='_astro/CopyPage.BgCFg6FO.css';rule='.copy-section h2{overflow-wrap:anywhere}\n'
 if layout['scope']!='existing-copy-section-h2-wrap-only' or layout['sourceCSS']!=old or layout['appendCSS']!=rule:raise ValueError('exact_scoped_wrap_rule_required')
 if sha(files[old])!=layout['sourceCSSSha256']:raise ValueError('original_css_digest_mismatch')
 css=files[old]+rule.encode();new='_astro/CopyPage.yeosu-wrap-'+sha(css)[:16]+'.css'
 if layout['resultCSS']!=new or layout['resultCSSSha256']!=sha(css) or new in files:raise ValueError('deterministic_new_css_identity_required')
 html=sorted(p for p in files if p.endswith('.html'))
 if layout['htmlFiles']!=html or len(html)!=4 or type(layout['stylesheetReferencesPerHTML']) is not int or layout['stylesheetReferencesPerHTML']!=1:raise ValueError('exact_four_stylesheet_references_required')
 out=dict(files)
 for name in html:
  before=('<link rel="stylesheet" href="/'+old+'">').encode();after=('<link rel="stylesheet" href="/'+new+'">').encode()
  if out[name].count(before)!=1:raise ValueError('original_stylesheet_reference_mismatch:'+name)
  out[name]=out[name].replace(before,after)
 del out[old];out[new]=css
 if {p:sha(b) for p,b in out.items()}!=layout['resultNormalizedFilesSha256']:raise ValueError('exact_layout_result_hashes_required')
 if len(out)!=18:raise ValueError('exact_layout_output18_required')
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
 final=apply_layout(corrected,spec)
 for name in html_files:
  final[name]=final[name].replace(('<meta name="site-factory-revision" content="'+old+'">').encode(),('<meta name="site-factory-revision" content="'+revision+'">').encode())
 for name,data in final.items():
  if name not in actual or data!=actual[name]:(dist/name).write_bytes(data)
 # Replace exactly the obsolete local build CSS; historical source/artifacts stay untouched.
 removed=set(actual)-set(final)
 if removed!={spec['layoutCorrection']['sourceCSS']}:raise ValueError('exact_old_css_removal_required')
 for name in removed:(dist/name).unlink()
 # Re-read files, not only in-memory results, before reporting.
 reread={p.relative_to(dist).as_posix():p.read_bytes() for p in dist.rglob('*') if p.is_file()}
 if reread!=final:raise ValueError('corrected_output_disk_readback_failed')
 changes=sorted(p for p in set(actual)&set(final) if actual[p]!=final[p])
 if changes!=sorted(html_files):raise ValueError('exact_four_html_with_stylesheet_change_required')
 return {'state':'LOCAL_BUILD_CONTENT_CORRECTION_VERIFIED','revision':revision,'baselineSourceRevision':old,'correctionSpecSha256':sha((HERE/'patch-spec.json').read_bytes()),'contentChangedFiles':spec['allowedChangedFiles'],'stylesheetReferenceChangedFiles':changes,'historical404ContentPreserved':True,'historical404AdditionalChanges':['stylesheetReference']+(['revisionMeta'] if revision!=old else []),'removedOutputFiles':sorted(removed),'addedOutputFiles':sorted(set(final)-set(actual)),'unchangedNonHtmlFiles':13,'imageFilesPreserved':7,'files':{p:sha(b) for p,b in final.items()},'publicationPerformed':False,'indexNowSubmitted':False,'deploymentAuthorityGranted':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dist',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
 print(json.dumps(correct_dist(Path(a.dist),a.revision),ensure_ascii=False,sort_keys=True))
