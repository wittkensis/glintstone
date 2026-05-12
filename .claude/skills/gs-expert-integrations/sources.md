---
question: "What are the per-source idiosyncrasies I'll hit when writing a connector against CDLI / ORACC / eBL / ePSD2 / OGSL / OpenAlex / Pleiades?"
created: 2026-05-11
modified: 2026-05-11
context: "Created during the 2026-05-11 knowledge architecture overhaul to capture per-source quirks that were previously scattered across import-tools READMEs and lived in tribal memory. Pulled together from the actual connector implementations in ingestion/connectors/."
status: active
audience: [claude, engineers]
owners: [eric]
related_issues: []
related_skills: [gs-expert-integrations, gs-scout-integrations]
supersedes: null
superseded_by: null
---

# Per-source quirks

Each upstream has its own conventions, freshness story, redirect behavior, license, and known pitfalls. Read the relevant section before writing or modifying a connector.

---

## CDLI — Cuneiform Digital Library Initiative

**Provides**: artifact catalog (~353k), ATF transliterations, translations, photographs, publication bibliography, scholar registry.

**License**: CC0 (catalog, ATF), CC BY-SA (scholar registry).

**Access**:
- Bulk catalog dump: `cdli_cat.csv` (semicolon-delimited; semicolons inside fields are escaped — use a CSV reader, not `split`)
- ATF dump: `cdliatf_unblocked.atf` (one big text file; `&Pnumber` line headers separate records)
- Live URLs: `cdli.earth/P######` — **issues lots of 302 redirects**. Follow them; don't treat as errors.
- Bulk catalog export has been **frozen since August 2022** — partial refreshes only

**Gotchas**:
- `language` field is semicolon-delimited (`sux;akk` = bilingual)
- `museum_no` formatting varies: `BM 099070`, `K. 01057`, `K 01057`, `K01057` — normalize before joins
- Designations may contain `+` for joined fragments (`K 03254 + K 03779`) — split when parsing
- P-numbers are zero-padded to 6 digits in IDs but not always in URLs
- ATF header `&P######` may be followed by ` = ` and a designation — parse defensively

**connectors**: `cdli_catalog.py`, `atf_parser.py`, `artifact_identifiers.py`, `scholars.py`

---

## ORACC — Open Richly Annotated Cuneiform Corpus

**Provides**: lemmatized texts (~7,500), glossaries (~21k entries), morphology, per-text credits, project metadata. Project-based: each subproject is a separate dataset.

**License**: CC BY-SA 3.0.

**Active subprojects ingested**: `dcclt`, `epsd2`, `rinap`, `saao`, `blms`, `etcsri`, `cams`, `dccmt`, `hbtin`, `ribo`. (Plus `amgg`, `riao`, `etcsl`, `ctij` discovered but partially ingested.)

**Access**:
- Per-project ZIP downloads at `oracc.museum.upenn.edu/<project>/json.zip`
- Files: `corpusjson/P######.json` (per-tablet CDL), `gloss-<lang>.json`, `<project>-portal.json`, `metadata.json`

**Gotchas**:
- CBD glossary format 2.0 uses keys like `cf` (citation form), `gw` (guide word), `pos`. Entries are keyed `"project/id"` (`"epsd2/e02384"`)
- Lemmatization `inst` field encodes lang + form + lemma + guide-word + POS: `"%sux:za-ba4-lu2=[sorrow//sorrow]N"`
- `ref` field format: `P######.line.word` (1-indexed)
- No central version number — each project has its own release cadence; track `metadata.json.released` per project
- The `etcsri` directory structure differs from the canonical layout; check for `etcsri/json/etcsri/corpusjson/` not `etcsri/corpusjson/`
- `xhu`, `uga`, `qpn` are smaller language codes in glossaries — keep them, don't filter

**connectors**: `oracc_lemmatizations.py`, `oracc_glossaries.py`, `oracc_lexical_glossaries.py`, `oracc_norms.py`, `oracc_enrichment.py`, `oracc_credits.py`

---

## eBL — electronic Babylonian Library

**Provides**: ML training data (sign detection, OCR), Babylonian Library fragments, lemmatized literature, bibliography (live API), MZL sign concordance.

**License**: research use; the OCR dataset (cuneiform_ocr_data) is CC BY 4.0.

**Access**:
- `cuneiform_ocr_data` GitHub repo for ML annotations and MZL concordance
- Live API at `ebl.lmu.de` for bibliography/fragments — **requires auth (Auth0)**
- ATF dialect is extended: full EBNF grammar at `source-data/sources/eBL/metadata/ebl-api/docs/ebl-atf.md`

**Gotchas**:
- eBL ATF supports more notation than CDLI ATF — `⸢...⸣` (uncertain), `◦` (no longer visible), `%n` (normalization shift), `|A.B|` (compound signs)
- MZL numbers are integers; OGSL uses string sign-ids — concordance table bridges them
- Some museum numbers in eBL are missing the prefix space (`BM099070` vs CDLI's `BM 099070`)

**connectors**: `ebl_sign_concordance.py` (more planned per data-issues.md)

---

## ePSD2 — Electronic Pennsylvania Sumerian Dictionary

**Provides**: Sumerian lexicon (~15k entries, ~71k senses), sign-level glossary data, lemma forms.

**License**: CC BY-SA 3.0.

**Access**: bulk JSON dump (~1.8 GB), no API.

**Gotchas**:
- Same CBD format as ORACC but with ePSD2-specific extensions
- Many entries link signs to lemmas via `sign_word_usage`-style cross-references — preserve these
- Sumerian subscripts are meaningful (`du₂` ≠ `du`); the connector must use tokenization mode 1 (see `gs-expert-assyriology/atf-format.md`)

**connector**: `epsd2.py`

---

## OGSL — Oracc Global Sign List

**Provides**: canonical sign inventory (3,367 signs, ~15k reading values, Unicode/MZL/ABZ concordance).

**License**: CC BY-SA 3.0.

**Access**: `ogsl-sl.json` from the OGSL repo.

**Gotchas**:
- Sign types: `simple` (`A`, `KA`), `modified` (`A@g`, `KA@t`), `compound` (`|A.AN|`, `|A.EDIN.LAL|`)
- Unicode mapping covers ~90% of signs; ~200-400 require manual MZL/ABZ curation
- Value types: `logographic`, `syllabic`, `determinative`

**connector**: `ogsl_signs.py`, `unicode_signs.py`

---

## OpenAlex

**Provides**: publication DOI enrichment, scholar ORCID identifiers, citation graph (via topics).

**License**: CC0.

**Access**: REST API.

**Gotchas**:
- The `concepts` API is **deprecated**. Use `topics`.
- Topic `T12307` = "Ancient Near East History" (~184k works)
- API has aggressive rate limits — back off on 429s
- Match by DOI when possible; ORCID is the second-best join key

---

## Pleiades

**Provides**: geographic coordinates for ancient places.

**License**: CC BY 3.0.

**Access**: bulk JSON/CSV.

**Gotchas**:
- Pleiades IDs are stable; names are not — always join on ID
- Provenience resolution requires ORACC GeoJSON to bridge ancient place names to Pleiades IDs

---

## Semantic Scholar

**Provides**: citation/reference graph keyed to DOIs.

**License**: free API (rate-limited).

**Gotchas**: same DOI-matching as OpenAlex; check both, dedupe.

---

## KeiBi

**Provides**: comprehensive Assyriology bibliography (~90k entries).

**License**: research use (no automated bulk download).

**Gotchas**: not currently ingested at scale; manual snapshots only.

---

## Hugging Face (model / dataset hub)

**Provides**: ML models and datasets — see `gs-scout-integrations/worked-examples.md` for current evaluations.

**Gotchas**:
- License varies per repo — always check `LICENSE` and `model card`
- Some repos drop without warning; mirror anything critical to `source-data/sources/`
- Model files can be huge (>10 GB); use `huggingface_hub` to stream rather than `wget`

---

## macOS SSL workaround

For any HTTPS endpoint, Python's `urllib`/`requests` can fail on macOS with SSL errors. Use `subprocess.run(["curl", "-fSsL", url], check=True, capture_output=True).stdout` instead. This applies to ALL connectors that fetch live URLs.

---

## When adding a new source

1. Add a new section to this file with the seven headings used above (Provides / License / Access / Gotchas / connector(s) / Macros / Live-API auth note if relevant).
2. Add the source's gotchas BEFORE writing the connector — most pain comes from misreading the dump format.
3. Add a fixture record to `gs-curator-artifacts/catalog.yaml` once the connector lands.
