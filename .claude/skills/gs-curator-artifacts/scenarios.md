---
question: "What end-to-end scenarios should our curated records demonstrate — what stories do they tell?"
created: 2026-05-11
modified: 2026-05-11
context: "Created during the 2026-05-11 overhaul. The catalog says WHAT each record is; this file says WHEN to reach for them — which test or demo each scenario serves."
status: active
audience: [claude, engineers, scholars]
owners: [eric]
related_issues: []
related_skills: [gs-curator-artifacts]
supersedes: null
superseded_by: null
---

# Named scenarios

Each scenario combines several catalog records to demonstrate a property of the system. When a user asks "show me how X works", reach for the matching scenario.

---

## Scenario: simple tablet onboarding

**For**: new engineer's first day, marketing screenshots, "hello world" demo.

**Records**:
- Artifact: P227657 (KTT 188, Sumerian lexical)
- Genre: Lexical
- Period: Old Babylonian
- Search term: "lugal"

**Story**: Open `/tablets/P227657`. See clean ATF, line-aligned translations, simple metadata. Click on the search bar, type "lugal", get a small focused result set.

---

## Scenario: damaged + joined fragments

**For**: testing ATF parser edge cases, UI's handling of `+` in designations.

**Records**:
- Artifact: P229672 (K 03254 + K 03779)
- Sign: any with `[...]` damage in its line context

**Story**: Open `/tablets/P229672`. Header shows the joined fragment list. ATF rendering preserves damage brackets. Lemmatization gracefully degrades over damaged segments.

---

## Scenario: cross-language search (Sumerogram)

**For**: demonstrating the cross-language search story.

**Records**:
- Sign: KA
- Lemma: epsd2/ka (Sumerian "mouth")
- Lemma: oracc/.../pû (Akkadian "mouth", written KA)

**Story**: Search for "KA" → results include Sumerian lemma `ka` AND Akkadian lemma `pû`. Click into either; see the cross-language relationship in the knowledge bar.

---

## Scenario: competing interpretations

**For**: showing the data-model's non-negotiable that two scholars can disagree, both get stored.

**Records**:
- Artifact: P001282 (bilingual, multiple lemmatization runs)
- Annotation run: babylemmatizer-v2.1
- Annotation run: oracc/rinap (or similar human-annotated)

**Story**: Find a token where BabyLemmatizer disagrees with ORACC. Open the Translation Builder. See both interpretations with confidence + source. The UI doesn't pick a winner — the scholar does.

---

## Scenario: high-polysemy lemma

**For**: dictionary UI stress test; demonstrating polysemy.

**Records**:
- Lemma: epsd2/lugal (king)
- Composite: a royal-inscription Q-number where lugal appears with multiple senses

**Story**: Open `/dictionary/epsd2/lugal`. See 20+ sense distinctions. Each sense shows attestations. Click a sense → see example tablets.

---

## Scenario: scholar merge history

**For**: testing scholar deduplication and the `scholar_merge_log` cascade.

**Records**:
- Scholar with > 3 merges (TBD from discovery query)
- Their merged-into scholar
- Publications attributed to both pre-merge

**Story**: Open the scholar page. History panel shows merge events. Publications correctly attributed post-merge. ORCID disambiguation visible.

---

## Scenario: pipeline-coverage transparency

**For**: showing the pipeline-stage UI (planned).

**Records**:
- Stage 5 (translated): P227657
- Stage 4 (lemmatized): P001282 (or similar)
- Stage 3 (transcribed only): pick via discovery query
- Stage 2 (sign-detected ML only): one of the 81 CompVis tablets
- Stage 1 (just an image): pick via discovery query

**Story**: One screenshot per stage. Each shows the same metadata frame but increasing data depth.

---

## Scenario: performance test — heavy load

**For**: page-load performance under realistic conditions.

**Records**:
- Lemma: epsd2/ninda (top attestation — 109,427)
- Critical-cache top 53 (icount ≥ 10,000)

**Story**: Open a tablet with many tokens. Knowledge bar lookups should fan out fast (cache hit rate ≥ 85%). Lemma detail for ninda should load < 500 ms.

---

## Scenario: ML-vs-human disagreement

**For**: demonstrating the confidence + provenance UX for ML annotations.

**Records**:
- A tablet processed by BabyLemmatizer
- The same tablet (or a similar genre) with human ORACC lemmatization
- A specific token where they diverge

**Story**: User clicks the divergent token. Knowledge bar shows both lemma candidates, each with confidence + source. ML annotation is visibly secondary (lower confidence, source = `babylemmatizer-v2.1`).

---

## When this list gets stale

- A new feature ships and needs a demonstrative scenario → add it here
- A scenario relies on a record that's been deprecated → update or remove
- A scenario's records have been pinned as test fixtures → cross-link to the test

Update `modified:` on this file when scenarios change.
