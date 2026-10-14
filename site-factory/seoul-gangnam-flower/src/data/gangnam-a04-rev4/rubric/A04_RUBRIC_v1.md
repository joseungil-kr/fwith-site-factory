# A04 title and keyword alignment rubric

Version: A04-local-independent-v1
Scope: supplemental, local-only review. This rubric was defined before its author opened any target Gangnam title, H1, first answer, final copy, or page plan. Reading generic examples in the supplied rule originals is permitted and has occurred. No target page has been scored here. Original plans, copy, source, deployment and earlier approvals remain unchanged.

## Status of this method

[직접 확인] The supplied originals require one primary keyword for each indexable primary document; direct expression of the core query combination in the front of the Title; the same region, service and intent in H1; a direct opening answer within the first 120–180 characters; revision on intent drift; and A04 keyword metadata with reproducible evidence. The v1.1 numeric threshold is 90. The combined contract expressly calls this an internal review threshold, not a measured SEO outcome.

[추정·판단] The originals do not prescribe point weights, a character normalization algorithm, an alias dictionary, or a mathematical definition of semantic equivalence. The operational choices below are a preregistered review method, not source quotations, search-engine rules, empirical ranking coefficients, or a guarantee of demand, indexing, traffic, conversion or rank. The method must not be adjusted after seeing target scores to obtain a desired result.

[미확인] This artifact contains no evaluation of the target pages, current search demand, public deployment, rendered screen, working CTA, business claims or SEO performance. A good alignment score does not verify these.

## Authoritative sources

Read in full locally: COMBINED_RULES.md; site_factory_query_first_v1_1_test.md; site_factory_rules_v1_2.md; PRECEDENCE_AND_COVERAGE.md; and the v1 original for the combined contract's O01 provenance requirement. Paths, byte counts, raw SHA-256 and normalized SHA-256 are in rule_source_hashes.json. PRECEDENCE_AND_COVERAGE.md was read from the allowed cached repository because it is absent from rules-at-pinned-main. Its hash and the other three shared files match source-manifest.json in that cache. A path named pinned-main is not independent proof of a Git commit: no commit SHA is asserted by this rubric.

Precedence: v1.2 controls; v1/v1.1 fill nonconflicting omissions only. The combined contract is v1.2+omissions-2026-10-01, not a new v1.3.

Rule anchors:
- COMBINED_RULES.md lines 101–107 and v1.2 lines 95–101: one keyword, Title front, H1 alignment, opening answer, intent drift, no repetition formula.
- COMBINED_RULES.md line 238 (A04), and PRECEDENCE_AND_COVERAGE.md line 35: metadata, >=90 internal threshold, actual field evidence, reproducible rubric, no arbitrary self-awarded PASS.
- v1.1 lines 35–53: metadata, preserving query form when possible, avoiding unnecessary words between region and service, opening answer, 90 threshold.
- v1.1 lines 65–74: synonyms sharing one cluster/URL; provider-search intent may belong on HOME.
- v1.2 lines 111–122: distinct Title, H1, meta, card and first-answer roles. Card-summary rules are separate gates, not alignment-score bonuses.
- v1.2 lines 208–220: all Production Gate requirements; this narrow review cannot establish Production PASS.
- PRECEDENCE_AND_COVERAGE.md lines 45–51: precedence over old examples; Ansan page quota and missing-photo restriction do not generalize; shadow noindex is legitimate.
- PRECEDENCE_AND_COVERAGE.md lines 56–59: source hashes, applied/NA evidence, independent review, and distinction between content, integrity and deployment verification.

## Applicability must be decided before scoring

Freeze one applicability row per page. Identify the source of page role, intended primary status, intended production indexability, intent and current shadow status. A filename or a high score cannot decide applicability. If sources conflict, mark APPLICABILITY_UNVERIFIED and do not claim a completed A04 review.

1. HOME: required when it is the principal query-targeted commercial page, including provider-search intent. The brand/home label is no exemption. It gets one primary query and the full 100-point rubric.
2. Regional purchase articles or commercial/place/service landing pages: required when designated primary search documents. Apply the full rubric even if an article format is used. Distinct region/service/purpose decisions must explain distinct primary intent keys.
3. Directory: NOT_APPLICABLE only when evidence establishes a navigation-only, non-primary directory without an independent search target. Record its purpose and reason, score=null, and no invented commercial keyword. If it is an intended indexable primary document, the full rubric applies to its genuine directory/navigation intent; do not force a purchase intent onto it. If its intent conflicts with HOME, flag the conflict. An undeclared role or missing keyword is not an exemption.
4. 404: NOT_APPLICABLE for a real error/recovery page, with score=null and the declared role as evidence. Correct HTTP error status, noindex behavior and recovery links belong to technical QA; a local plan alone cannot verify production HTTP behavior. If the supposed 404 is actually used as a primary landing page, applicability must be reconsidered before scoring.
5. Shadow/local draft of a future primary page: REQUIRED_SHADOW_DIAGNOSTIC, not exemption. Score alignment against the intended primary role, but explicitly retain non-production status. Do not require removing noindex, publishing or changing robots to perform this review.

Do not score NA pages as 0 or 100, redistribute their points, or include them in a scored mean. Report scored-page count, NA count/reasons and unresolved count. Each applicable page must satisfy its own threshold; a mean cannot hide a deficient page.

## Frozen target map and evidence inputs

Before reading the evaluated Title/H1/opening text, the scorer must obtain or create and hash a target map from the existing plan/query research. This freezes primary_keyword, region/place, service, essential intent modifiers, intentKey, page role, expected customer question and the accepted lexical aliases. If the plan itself embeds final copy, extract only the target metadata first; log the extraction process. Missing target data remains missing. Do not reverse-engineer a query from the title to improve the score.

If new supplemental target metadata is required, label its provenance as ADDENDUM_PROPOSED, list the evidence and analytical rationale, and retain the original plan. This allows conditional diagnostics; it does not retroactively prove Query-first drafting or amend an earlier approval. A full A04 result must disclose which fields were originally present and which were supplied later.

A04 record for every applicable page:
- primary_keyword: exactly one nonempty value.
- secondary_keywords: explicit list, possibly empty with reason; never a fabricated search-frequency list.
- keyword_cluster: stable identifier with its region/service/customer-intent definition.
- query_class: one of core-commercial, commercial-modifier, work-commercial, local-commercial, support-info. A truly different directory intent must be flagged if the given taxonomy does not represent it; do not silently invent a sixth class.
- query_priority: a stated relative editorial priority and rationale, e.g. commercial-first. Do not present this as measured popularity or volume.
- query_evidence: source locator, checked date if known, exact supporting text/query, evidence type, and limitation. Distinguish observed query evidence from business-service evidence and EDITORIAL_CANDIDATE inference. A rule-pattern example is not proof that a target query was searched. Unavailable demand data is explicitly UNKNOWN, not zero.
- title_alignment_score: computed result, rubric version/hash and row-level score evidence.

Metadata completeness is a gate alongside the number, not free points. An empty query_evidence object, unsupported claim of query demand, ambiguous target, missing required field, or unknown applicability blocks A04_REVIEW_COMPLETE. An honestly labeled editorial candidate with its derivation can satisfy recording provenance, while demand remains unverified. Do not call it validated demand.

Freeze candidate aliases in the target map from the query plan, supplied source or explicit language analysis; include provenance. No on-the-fly alias additions after observing failure. Exact primary text requires no alias. Region aliases must preserve the actual geographical scope; a containing city and one of its neighborhoods are not automatically interchangeable. Broad service and a different narrower product are not automatically synonyms. Natural Korean particles and grammatical endings may connect a matched term but cannot invent a missing lexical term.

## Exact extraction and normalization

1. Preserve raw field text, source path, byte hash, JSON pointer/line or HTML selector and extraction time. Score the declared customer-facing HTML title, unique principal H1 and first visible content prose after H1. With local draft-only work, use the draft's corresponding fields and explicitly say rendered HTML was not checked. Do not substitute meta, card summary, navigation or a hidden first_answer field for the actual opener.
2. If the draft first_answer and actual first prose differ, inspect both, score the customer-visible source of truth, and record the mismatch. If the source of truth is unavailable, report provisional draft-only diagnostics. Missing Title/H1/opener is not an assumed match.
3. N(text): HTML-entity decode once; Unicode NFC; collapse every run for which Python str.isspace() is true to one ASCII space; strip leading/trailing spaces. Retain punctuation and accents. If parsing HTML, extract visible text and exclude script/style/template/navigation before N; plain draft fields are not treated as HTML. Do not strip negations, meaningful digits or service modifiers.
4. Character counts and spans use Unicode code points of N(text), including spaces and punctuation. They are not UTF-8 bytes, token counts or Korean syllable-frequency measurements. Spans are zero-based, half-open [start,end).
5. L(text), for lexical candidate discovery only: casefold N; retain only Unicode letters and numbers. Record an index map back to N. It removes whitespace and punctuation to permit formatting/spacing differences. It does not stem, translate, replace synonyms or infer intent. A compact substring match is a candidate, not proof: check lexical boundaries in the original text. Embedded word fragments and punctuation-separated keyword lists cannot earn semantic combination credit.
6. A full query combination contains every mandatory region/place, service and intent-modifier atom from the frozen map in one meaningful phrase. Search candidate occurrences left-to-right; select the earliest that actually expresses that combination in context. Record every selected atom span and the total covering span.
7. Title front test: the full combination's start position is strictly before ceil(len(N(title))/2), and before the first major separator if one exists. Major separators are |, ｜, colon (: or ：), newline in the raw field, spaced hyphen, en dash or em dash. The combination must finish before that separator. A title consisting entirely of the query qualifies because its combination starts at zero. Record the start, length, midpoint and first separator. This interprets front placement by start position so a short exact-query-only title is not penalized for lacking a long suffix. This is an operational choice, not a source-defined equation.
8. Opening windows: record N(opener)[0:120] and [0:180]. A complete directly useful answer proposition must occur by position 180. Finishing earlier than 120 is allowed; no padding, minimum answer length, keyword frequency or density target is imposed. An unfinished proposition at 180 does not count as complete. Additional copy after a valid immediate answer is not penalized merely for length.
9. H1 and opener semantic matching may use a frozen lexical alias. In the opener only, an explicit, singular, unambiguous reference to the immediately preceding H1 or an earlier opener phrase may resolve a region/service; cite both antecedent and referring phrase. A generic statement that could refer to anything is not a reference. Negation and conditions must be retained when judging what the text promises.

The companion normalization.py implements N, lexical candidate maps, opening windows and Title front arithmetic. It cannot certify semantic boundaries, intent, truth or directness. The scorer must record evidence for those decisions.

## Preregistered 100 point score

All deductions are the difference between maximum and awarded points in each row. Use only the listed discrete values. No discretionary bonuses, hidden penalties, reweighting, or page-specific denominator. The raw score is the sum of nine rows. Unknown evidence yields a score interval, never optimistic full points.

Title receives 40 points because A04 specifically tests Title alignment and the rule explicitly distinguishes direct query expression, purchase intent, front placement and preservation of the core phrase. H1 and opening answer each receive 25 points because v1.2 names both as mandatory coequal alignment fields. Cross-field/body intent continuity receives 10 points because v1.2 explicitly requires revision for intent drift. The numerical distribution is an analytical implementation, not prescribed or empirically validated source weights.

T1 Direct core region and service in Title, max 10
- 10: both required region/place and service are directly expressed with frozen forms/aliases in a meaningful phrase; if the independently frozen query is non-local, its declared service/topic is fully expressed and non-local scope is evidenced.
- 5: exactly one required core atom is missing or only inferable.
- 0: both absent, contradictory, or a different service/region is substituted.
Source: v1.2 §6; v1.1 alignment bullets.

T2 Title expresses the intended query purpose, max 10
- 10: all essential modifiers/purpose are expressed. For a core-commercial query without an explicit modifier, the clear region/service phrase itself may express that broad service/provider intent; no gratuitous ordering word is required.
- 5: correct core service but the specific expected question is underspecified.
- 0: a different intent is expressed or the claimed target is unsupported by the title.
Source: v1.2 §§6,8.

T3 Title front placement, max 10
- 10: the full meaningful core query combination passes the exact front test above.
- 0: combination absent or fails either front/separator requirement.
Source: v1.2 §6; v1.1 alignment.

T4 Core phrase integrity, max 10
- 10: the compact primary form, or frozen equivalent phrase preserving all required atoms and intent, occurs as a natural meaningful phrase without unnecessary inserted modifiers between region and service.
- 5: only necessary grammatical connecting material interrupts the exact form, while every atom and intended relation remains explicit; the scorer quotes and explains the connector.
- 0: unrelated/promotional insertion breaks the region/service combination, merely scattered keyword-list matches, or incomplete/different target.
Source: v1.1 lines 49–50, applied under v1.2's semantic alignment and no repetition-formula rules.

H1 Same core target, max 15
- 15: H1 clearly identifies the same complete region/place and service/topic as the frozen target, using direct text or frozen aliases.
- 7: exactly one mandatory core atom is absent or unresolved, without contradiction.
- 0: both absent, or a region/service contradiction.
Source: v1.2 §6; v1.1 line 51.

H2 Same intended purpose in H1, max 10
- 10: same complete query intent as the target; natural expansion is allowed.
- 5: consistent broad service but essential intent modifier is underspecified.
- 0: different intent or meaning cannot be established.
Source: v1.2 §§6,8. H2 is a criterion ID, not an HTML heading requirement.

A1 Direct answer in the first 180 characters, max 15
- 15: a complete proposition directly answers the frozen expected customer question by character 180. It supplies a relevant answer, condition, decision input or next step suited to the role, rather than merely restating the title.
- 5: only a relevant invitation, teaser, restatement or generic instruction appears by 180; a substantive answer occurs later or is absent.
- 0: no relevant response, different intent, or opener unavailable as a field rather than merely unverified.
Source: v1.2 §6, §8; v1.1 line 52. Role-sensitive examples are defined below without target copy.

A2 Opening answer targets the same region and service, max 10
- 10: the first 180 characters identify both core atoms, directly or by the narrowly allowed unambiguous reference procedure; they address the same intent.
- 5: exactly one core atom is unresolved but the other and the intent are consistent.
- 0: both unresolved, contradictory target, or different intent.
Source: v1 §§1,7; v1.2 §§6–8.

I1 Intent continuity in the supplied page, max 10
- 10: Title, H1, opener, substantive sections and stated main next action consistently serve the frozen single primary intent. Relevant supporting decisions and optional secondary links are allowed.
- 5: supplied evidence is incomplete enough to prevent proving continuity, but no contradictory section is observed. This is only a diagnostic value and also marks the required continuity evidence UNVERIFIED.
- 0: another intent replaces or contradicts the promised core purpose, or competing primary intents lack distinct roles.
Source: v1.2 §§2,6,11,17; v1.1 cluster rules.

Arithmetic note: there are nine rows, T1–T4 + H1–H2 + A1–A2 + I1, totaling 100. The score calculator uses exactly these nine IDs.

## Semantic evidence and role sensitive direct answers

The reviewer does not award a number by overall impression. For every row record: awarded permitted value, exact quotation, source pointer, matched atom/intent, inference if any, and why the higher level was or was not met. Mechanical matching alone cannot satisfy a semantic criterion. The independently frozen expected question controls all judgments.

- HOME/core commercial: opener answers what service the provider handles for which target area and gives an actionable customer decision/condition/next step. A generic welcome is not a direct answer.
- Regional service/purchase page: opener explains the relevant service or purchase option and a concrete decision input, condition or next step for the intended customer. An unsupported unconditional delivery/purchase promise is a factual-review issue, not evidence of verified availability.
- Price intent: opener answers price basis, a supported price/range if available, or the specific inputs/conditions that determine a quote. It need not fabricate a number.
- Timing/availability intent: opener explains availability with the conditions and information required to determine it; it does not need to invent a guaranteed delivery time.
- Place-related intent: opener ties the service/customer action to the named place and a relevant practical condition or input.
- Primary directory/navigation intent, if applicable: opener explains what the list helps the customer find and how to choose or navigate. A directory does not need a purchase CTA merely to achieve alignment.
- Informational intent, if genuinely supported: opener directly answers the information question. It cannot be a support-info quota filler.

For each material Title/H1/opening promise, the reviewer records whether later sections deliver that promised decision information. An explicit, independently evidenced contradiction triggers intent drift; not every related service link counts as drift. A related link remains secondary when its label/presentation clearly identifies an optional alternative rather than replacing the target response.

Another reviewer must be able to reconstruct each choice from the quotes, map and formula. Disagreement about an alias, boundary, answer directness or intent is recorded as UNRESOLVED, with both rationales; do not average opinions into a pass. Resolve using the frozen target and existing source evidence. Any necessary rubric change creates a new version/hash and requires rescoring every applicable page, reporting both versions and why the change was needed.

## Non compensable gates and penalties

Mandatory alignment violations cannot be offset by unrelated full points. Record the raw score separately from any ceiling.

- G1 target integrity: exactly one primary query and intent per primary URL. Multiple primary values or a proven duplicate primary cluster/intent conflict requires REVISE irrespective of raw score; effective score is min(raw,89).
- G2 Title core/front: missing/wrong region or service, a missing essential query modifier, T3=0, or unnecessary non-grammatical region/service insertion requires REVISE; effective score is min(raw,89).
- G3 H1 target/intent: absent/wrong required core or essential purpose requires REVISE; effective score is min(raw,89).
- G4 opening directness: no complete direct answer by 180 or a contradictory or verifiably absent required target requires REVISE; effective score is min(raw,89). Score A1/A2 first; the cap simply prevents compensation.
- G5 intent drift: confirmed drift in any core field or substantive customer journey requires REVISE; effective score is min(raw,89).
- G6 evidence/metadata: any required evidence genuinely unavailable, missing metadata or unresolved semantic decision yields UNVERIFIED/INCOMPLETE, not PASS. Unknown row values remain null with a lower/upper score interval. A known missing field is scored by the corresponding absence rule; unavailable-to-inspect content is unknown, not assumed absent.
- G7 external scope: missing business truth, unsupported prices/availability, unverified CTA function, imagery, local facts, summary gates, accessibility, deployment or technical indexability must be reported under their proper separate gate. They never earn alignment points, and a favorable alignment result cannot clear them.

Do not double-subtract numeric penalties. The score is the row sum; multiple mandatory violations only apply the same maximum ceiling once. Every triggering violation remains separately visible.

## Result vocabulary and verification boundary

A04_ALIGNMENT_MEETS_INTERNAL_THRESHOLD: all applicable score rows verified, effective score >=90, no G1–G5 violation and no unresolved semantic evidence. This is a narrow content-alignment finding only.
A04_ALIGNMENT_REVISE: verified score <90 or a verified G1–G5 violation.
A04_UNVERIFIED: missing source/evidence or unresolved semantic decision prevents a conclusive alignment finding. Report known-row subtotal and possible range, not a made-up score.
A04_METADATA_COMPLETE / A04_METADATA_INCOMPLETE: separate from numerical alignment. Original-versus-addendum provenance and search-demand limitations remain visible.
NOT_APPLICABLE: only with the role-specific evidence stated above; score=null.

Even an alignment finding plus complete metadata does not mean Production PASS, SEO success, a working deployment, original Query-first sequence, or full-rule compliance. Report local draft content verification as such. Do not overwrite the sealed plan with the supplemental scores.

## Reproducible evaluation output

When scoring is separately authorized, create new files outside this frozen rubric directory containing:
- Input copies or read-only source locators and SHA-256, extraction date, page IDs, target-map SHA and this rubric SHA.
- Page applicability decision/evidence and seven A04 fields, including original/addendum provenance.
- Raw Title/H1/opener, 120/180-character snippets, exact selected spans, title front calculation and alias provenance.
- Nine row-level decisions, quotes and points, raw/effective total or interval, gates and resulting limited verdicts.
- Pairwise cluster/intent mapping with actual target/section/action evidence for any collision; no collision-free assertion from different strings alone.
- Separate unverified facts and out-of-scope production checks.
- A machine recalculation log and a second readback check that the evidence quotes equal the frozen source fields.

The rubric directory is sealed by FROZEN_SHA256SUMS.txt and freeze_record.json after local synthetic normalization/arithmetic tests. Tests demonstrate method mechanics only; no target copy is present in those tests. Changes after freezing must use a new rubric version, never edit this one in place.
