---
question: "Read-side view: what does CDLI / ORACC / eBL / OGSL / ePSD2 each provide, in terms a domain expert would think about?"
created: 2026-05-11
modified: 2026-05-11
context: "The read-side cheat sheet for understanding what each source means linguistically. The write-side equivalent (how to ingest each) lives in gs-expert-integrations/sources.md."
status: active
audience: [claude, engineers, scholars]
owners: [eric]
related_issues: []
related_skills: [gs-expert-assyriology, gs-expert-integrations]
supersedes: null
superseded_by: null
---

# Read-side: what each source means

## CDLI — Cuneiform Digital Library Initiative

The catalog of record for cuneiform artifacts. Provides:

- **Identity**: P-number for every artifact (the universal join key)
- **Catalog metadata**: museum number, designation, period, provenience, genre, language
- **ATF transliterations**: ~135k texts (~4M tokens)
- **Translations**: ~43k English glosses
- **Composite text links**: P → Q mappings (exemplars of an abstract work)
- **Fragment joins**: when two physical pieces belong to one tablet (encoded in `designation` with `+`)
- **Publications bibliography**: 16.7k pubs with editorial chains
- **Scholar registry**: ATF editor and author attribution

License: CC0 (catalog, ATF) / CC BY-SA (scholar registry).

Coverage note: the bulk catalog dump has been frozen since August 2022.

## ORACC — Open Richly Annotated Cuneiform Corpus

The deepest linguistic annotation source. Project-based; each subproject is a focused corpus (e.g. `rinap` = Royal Inscriptions of the Neo-Assyrian Period).

Provides:

- **Lemmatization**: ~309k tokens linked to dictionary entries
- **Glossaries**: ~21k entries with citation forms, guide words, POS, dialect
- **Normalization**: reconstructed Akkadian inflected forms (critical for syllabic spelling)
- **Per-text credits**: who edited which text
- **Project metadata**: release dates, scope, languages

License: CC BY-SA 3.0.

Projects with data downloaded AND annotation run registered: dcclt, epsd2, rinap, saao, blms, etcsri, riao. Projects with data downloaded but no annotation run yet: hbtin, dccmt, ribo. Projects with annotation run registered but data status unclear: cams, rimanum. Credits/enrichment metadata only (no lemmas or glossary): etcsl, rime, amgg. The full ORACC project universe (~50+ projects) is at oracc.museum.upenn.edu/projectlist.html — most have not been downloaded.

## eBL — electronic Babylonian Library

Focused on Babylonian literary tradition (epics, hymns, omens). Provides:

- **Fragment-level data**: per-piece transliteration with extended ATF notation
- **Bibliography**: via live API (auth required)
- **MZL sign concordance**: bridges Mesopotamisches Zeichenlexikon numbers to OGSL
- **ML training data**: sign detection annotations, OCR training set

License: research use; ML datasets CC BY 4.0.

eBL ATF supports notation CDLI ATF doesn't (`⸢...⸣`, `◦`, `%n`, `|A.B|`). See [atf-format.md](atf-format.md#ebl-atf--extended-notation).

## ePSD2 — Electronic Pennsylvania Sumerian Dictionary

The primary Sumerian dictionary. Provides:

- **Lemma inventory**: ~15k Sumerian entries with citation forms
- **Senses**: ~71k sense distinctions
- **Sign-level glossary data**: links signs to lemma readings
- **Forms**: attested spellings per lemma

License: CC BY-SA 3.0.

Glintstone uses ePSD2 as the canonical Sumerian lexical base, augmented by ORACC project-specific glossaries for other languages.

## OGSL — Oracc Global Sign List

The canonical sign inventory. Provides:

- **Signs**: 3,367 graphemes
- **Reading values**: ~15k (syllabic + logographic + determinative)
- **Concordance**: Unicode codepoints, MZL numbers, ABZ numbers
- **Sign types**: simple / modified / compound

License: CC BY-SA 3.0.

When a sign has no Unicode mapping, this is a real data gap (~200-400 signs need manual curation per `data-issues.md`).

## CAD — Chicago Assyrian Dictionary

Reference dictionary for Akkadian. Currently extracted from scans; not yet a primary ingestion source. Provides:

- **Polysemy**: rich sense distinctions for Akkadian lemmas
- **Logogram cross-references**: Sumerogram-to-Akkadian bridges (the `cad_logograms` table)

## OpenAlex / Semantic Scholar

Citation enrichment, not primary linguistic data. Used to:

- Resolve DOIs for publications in CDLI's bibliography
- Tie scholars to ORCID identifiers for disambiguation
- Build a citation graph for "what cites this text"

## Pleiades

Geographic gazetteer for the ancient world. Resolves Glintstone's provenience strings ("Nippur (mod. Nuffar)") to stable geographic IDs and coordinates.

## What's missing (per data-issues.md)

- **Hittite** corpora at scale
- **Elamite** dictionaries
- **CAD** as primary ingestion (currently scan-extracted)
- **DeepScribe** vision pipeline integration (Persepolis Fortification Archive)
- **Larger sign concordance** — ~200-400 signs still need manual MZL/OGSL bridging
