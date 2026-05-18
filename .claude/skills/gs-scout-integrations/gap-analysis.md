---
question: "Where does Glintstone have its biggest data gaps today — and which gaps would a new integration close?"
created: 2026-05-11
modified: 2026-05-18
context: "Created during the 2026-05-11 overhaul. The gaps come from the Data-Model-Data-Issues wiki page (https://github.com/wittkensis/glintstone/wiki/Data-Model-Data-Issues) and from the row counts in gs-orient-project. Update when significant ingestion lands."
status: active
audience: [claude, engineers]
owners: [eric]
related_issues: ["#17", "#18", "#19", "#22"]
related_skills: [gs-scout-integrations]
supersedes: null
superseded_by: null
---

# Coverage gaps (highest-impact integration targets)

Ranked by how much pain a fix would relieve. Verify against the [Data Issues wiki page](https://github.com/wittkensis/glintstone/wiki/Data-Model-Data-Issues) for the canonical list.

## Tier 1 — most impactful

### Lemmatization coverage

- **Current**: ~2% of 353k artifacts have lemmatization (~7,500 tablets)
- **Why it hurts**: ATF without lemmas can't be searched lexically, dictionary entries can't be ranked by attestation, knowledge bar has no anchor
- **What would close it**: a high-recall Akkadian lemmatizer, a Sumerian lemmatizer trained beyond the ORACC core projects, or per-corpus efforts to lemmatize specific genres

### Sign detection / OCR

- **Current**: ~81 tablets have computer-vision sign annotations (CompVis)
- **Why it hurts**: every other tablet starts from human transcription; "find me the KA sign on this image" doesn't exist
- **What would close it**: DETR-class models trained on broader sign classes, or models that produce bounding boxes + class predictions at scale

### MZL ↔ OGSL ↔ ABZ concordance

- **Current**: ~90% auto-matched via Unicode codepoints; 200-400 signs need manual curation
- **Why it hurts**: cross-source joins break for the missing signs; eBL annotations can't always link back to OGSL
- **What would close it**: focused human curation, or an LLM-assisted matching pass with human review

## Tier 2 — meaningful

### Sumerian outside ORACC

- **Current**: ePSD2 + ORACC lexical projects (dcclt, etcsri, etc.)
- **Why it hurts**: Sumerian texts outside these projects (e.g. early Sumerian literary corpora) aren't lemmatized
- **What would close it**: extending ingestion to ETCSL fully, or a new Sumerian lemmatizer

### Akkadian dialect coverage

- **Current**: 11 dialects tracked in `lexical_lemmas.dialect` (oldbab, midbab, stdbab, neoass, neobab, …)
- **Why it hurts**: dialect-specific spellings and morphology aren't always disambiguated
- **What would close it**: per-dialect glossaries (currently muddled by CBD's aggregation)

### Translations beyond English

- **Current**: 43.7k translations, mostly English; some German, Arabic, Persian
- **Why it hurts**: multilingual UI (#46) needs translation parity
- **What would close it**: nllb-style multilingual translation models, or sourced translations from European publications

### Composite-text reconstructions

- **Current**: 857 composite Q-numbers, 3,771 exemplar links
- **Why it hurts**: scholars work with reconstructed wholes; exemplar-only view is incomplete
- **What would close it**: ingesting reconstructed composite ATF from ORACC + manual curation of new joins

## Tier 3 — interesting but lower-leverage

### Hittite corpora

- **Current**: minimal coverage; logographic complexity makes lemmatization hard
- **Why it hurts**: a whole language family is essentially absent
- **What would close it**: dedicated Hittite annotation projects; HTSP / Hittite Online resources

### Elamite

- **Current**: handful of glossary entries
- **Why it hurts**: similar to Hittite; language isolate
- **What would close it**: targeted ingestion of Elamite corpora (e.g. Persepolis Fortification Archive)

### Image hosting / thumbnails (#16, #52)

- Not a content gap — an infra gap. Handle via `gs-expert-deployment`, not ingestion.

### Bibliography enrichment

- **Current**: 16.7k publications, partial DOI coverage
- **Why it hurts**: citation chains break without DOIs
- **What would close it**: OpenAlex + Semantic Scholar bulk enrichment (issue #20, partially done)

## When this file gets stale

Update when:

- A connector lands that significantly closes one of these gaps (move it down a tier or remove it)
- Row counts in `gs-orient-project/SKILL.md` shift the percentages
- A new gap emerges from data-issues.md

Bump `modified:` whenever the tier list changes.
