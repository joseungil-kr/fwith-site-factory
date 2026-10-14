from pathlib import Path
import json,hashlib,copy,datetime
O=Path(__file__).parent;B=Path('/workspace/shared/gangnam-plan-copy-20261013');R=O/'revised-input'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
def bind(p,ptr=None):
 x={'file':str(p),'sha256':sha(p)}
 if ptr:x['jsonPointer']=ptr
 return x
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
base=read(O/'mapping/keyword-mapping.metadata-refined.json')
rubric=bind(O/'rubric/A04_RUBRIC_v1.md');targets=bind(O/'assessment/targets.frozen.json')
for revision,first,second,out in [(3,O/'assessment/a04-independent-assessment.v1.json',O/'independent-review/independent-assessment.json',O/'mapping/keyword-mapping.original-assessed.json'),(4,R/'review/first-assessment.rev4.json',R/'review/second-assessment.rev4.json',O/'mapping/keyword-mapping.rev4.final.json')]:
 x=copy.deepcopy(base); f=read(first); s=read(second); x['status']='A04_METADATA_AND_DRAFT_ALIGNMENT_REVIEWED' if revision==4 else 'ORIGINAL_ALIGNMENT_REVIEWED_EVENT_REVISE_PRESERVED';x['articleRevision']=revision;x['reviewedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();x['scope']='Separate local addendum. Per-page numeric scores are frozen-rubric internal alignment results, not SEO performance or Production PASS. Original plan/copy/source stay unchanged; revision4 is replacement draft input only.'
 x.pop('pendingRoleApplicability');x['nonPrimaryRoutes']=copy.deepcopy(f['nonPrimaryRoutes']);x['rubric']=rubric;x['frozenTargets']=targets;x['assessment']=bind(first);x['reproduction']=bind(second)
 if revision==4:x['revision4ArticleInput']=bind(R/'copy/article-copy.rev4.json');x['revision4RuntimeInput']=bind(R/'handoff/runtime-input.rev4.json')
 for i,rec in enumerate(x['records']):
  one=next(q for q in f['records'] if q['id']==rec['id']);two=next(q for q in s['scoredPages'] if q['id']==rec['id']);assert one['calculation']==two['calculation']
  rec['title_alignment_score']=one['calculation']['effective_score'];rec['title_alignment_status']=one['calculation']['verdict'];rec['title_alignment_raw_score']=one['calculation']['raw_score'];rec['title_alignment_gates']=one['calculation']['gates'];rec['alignment_provenance']={'rubric':rubric,'frozenTargets':targets,'independentAssessment':bind(first,f'/records/{i}'),'independentReproduction':bind(second,f'/scoredPages/{i}'),'scoreMeaning':'Internal preregistered semantic alignment score only; no claim of demand, rank, impressions, conversion, technical readiness or publication.'};rec['applicability']=one['applicability'];rec['metadata_status']='A04_METADATA_COMPLETE_IN_ADDENDUM_WITH_LABELED_DERIVATIONS'
  if revision==4 and rec['id']!='home':
   src=R/'copy/article-copy.rev4.json';art=read(src)['articles'][i-1];ev=rec['actualTextEvidence'];ev['sourceFile']=str(src);ev['sourceSha256']=sha(src)
   for key in ['title','h1','firstAnswer']:ev[key]['text']=art[key]
   ev['firstAnswer']['charactersIncludingSpaces']=len(art['firstAnswer']);ev['firstAnswer']['first180Characters']=art['firstAnswer'][:180]
   ev['renderScope']='New revision4 JSON draft input. Original HTML is not updated and must be rerendered by implementation owner; no claim of revised screen verification.'
  rec['originalFieldAvailability']={'primary_keyword':'Exact original approved copy field','secondary_keywords':'Articles: prior research proposal fields; home: saved exact query log','keyword_cluster':'Articles: original intentKey; home: newly explicit analytical ID','query_class':'Articles: original frozen queryClass; home: labeled taxonomy inference','query_priority':'New tied editorial commercial-first tier, not historic numeric priority','query_evidence':'New structured source mapping of existing evidence, not new demand observations','title_alignment_score':'New independent rubric-based evaluation and separate reproduction'}
 x['integrationBoundary']='No existing sealed source or original input file is modified by this mapping. Consumer must bind both this mapping and revision4 runtime via the supplemental manifest; the original revision3 HTML event opener still differs until explicitly updated and verified.' if revision==4 else 'This preserves the original revision3 result; do not substitute later revision4 scores for original content.'
 write(out,x);print(out.name,sha(out))
