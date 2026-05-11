# Normalization Bridge

## What is Normalization?

Normalization is the step in cuneiform translation where a syllabic written form becomes a recognizable word. It sits between Reading and Lemma in the translation pipeline:

```
Sign -> Function -> Reading -> NORMALIZATION -> Lemma -> Morphology -> Sense
```

**Example:** The Akkadian token `ra-man-šú-nu` (4 syllable signs) normalizes to `ramānšunu` (one inflected word), which is a form of the lemma `ramānu` "self" with a 3rd-person masculine plural possessive suffix.

## When Normalization Applies

| Language | Normalization role | Why |
|----------|-------------------|-----|
| **Akkadian** (all dialects) | **Critical** | Written syllabically. Every token needs normalization to identify the word. |
| **Sumerian** | Minimal | Mostly logographic (one sign = one word). Norms exist in ORACC data but are less linguistically essential. |
| **Hittite** | N/A | Written with Sumerian/Akkadian logograms. Lemmatizations are of the logograms, not Hittite words. |
| **Hurrian, Ugaritic** | Moderate | Some syllabic writing; norms available where ORACC data exists. |

## Source Data

### ORACC Glossary JSON Structure

Each glossary entry has a three-level hierarchy:

```
entry (lemma)
  |-- forms[]        (attested written spellings at entry level)
  |-- norms[]        (normalized forms)
        |-- forms[]  (written spellings linked to this specific norm)
```

Example from `gloss-akk-x-stdbab.json`:

```json
{
  "cf": "abāku", "gw": "lead away", "pos": "V",
  "forms": [{"id": "x0014509.0", "n": "a-ba-ku", "icount": "1"}],
  "norms": [{
    "id": "x0014509.1",
    "n": "abāku",
    "icount": "1",
    "ipct": "100",
    "forms": [{
      "n": "a-ba-ku",
      "ref": "x0014509.0",
      "icount": "1"
    }]
  }]
}
```

The `ref` field links norm-level forms back to entry-level forms by ID.

### ORACC CDL (per-token annotation)

The CDL JSON format provides per-token normalization in the `f` object:

```json
{
  "node": "l",
  "frag": "ra-man-šú-nu",
  "f": {
    "lang": "akk-x-stdbab",
    "form": "ra-man-šú-nu",
    "cf": "ramānu",
    "gw": "self",
    "pos": "N",
    "norm": "ramānšunu"
  }
}
```

This is imported by step 11 (`11_import_lemmatizations.py`) into the `lemmatizations.norm` TEXT column.

## Data Volume

| Source | Entries | Norms | Written forms |
|--------|---------|-------|---------------|
| All ORACC Akkadian glossaries | 39,588 | 109,837 | 149,333 |
| ORACC Sumerian glossaries | ~7,000 | ~7,000+ | TBD |
| `lemmatizations.norm` (CDL) | 181,394 total | 6,091 populated (3.4%) | -- |

### Coverage by Akkadian Dialect

| Dialect | Norms | Written forms | Primary source |
|---------|-------|---------------|----------------|
| Generic Akkadian (akk) | ~24,400 | ~36,300 | dcclt, saao, rinap |
| Neo-Assyrian (akk-x-neoass) | ~16,600 | ~25,600 | saao |
| Standard Babylonian (akk-x-stdbab) | ~8,700 | ~10,500 | dcclt, rinap |
| Neo-Babylonian (akk-x-neobab) | ~7,000 | ~9,300 | saao |
| Old Babylonian (akk-x-oldbab) | ~2,600 | ~2,800 | dcclt, rime |
| Middle Babylonian Peripheral (akk-x-mbperi) | ~1,200 | ~1,300 | dcclt |
| Late Babylonian (akk-x-ltebab) | ~1,600 | ~2,200 | rinap |

## Schema

### `lexical_norms`

Normalized forms linked to parent lemmas. One lemma has many norms (morphological variants).

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PK | |
| `norm` | TEXT NOT NULL | Normalized form (e.g., `ramānšunu`) |
| `lemma_id` | INT FK -> lexical_lemmas | Parent lemma |
| `attestation_count` | INT | From source icount |
| `attestation_pct` | SMALLINT | % of parent lemma's attestations |
| `source` | TEXT NOT NULL | e.g., `epsd2`, `oracc/dcclt` |
| `source_id` | TEXT | Original ORACC ID |

Unique constraint: `(norm, lemma_id, source)`

### `lexical_norm_forms`

Written/orthographic spellings per norm. One norm has many written forms.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PK | |
| `norm_id` | INT FK -> lexical_norms | Parent norm |
| `written_form` | TEXT NOT NULL | Actual spelling (e.g., `ra-man-šú-nu`) |
| `attestation_count` | INT | Times this spelling attested |
| `source` | TEXT NOT NULL | |

Unique constraint: `(norm_id, written_form, source)`

### `lemmatizations.norm_id`

Optional FK added to existing table. Links per-token annotations to the normalization bridge. Backfilled from the TEXT `norm` column after import.

## Query Patterns

### Written form -> candidate lemmas (Knowledge Bar S1/S3)

```sql
SELECT ln.norm, ln.attestation_count,
       ll.citation_form, ll.guide_word, ll.pos, ll.language_code
FROM lexical_norm_forms lnf
JOIN lexical_norms ln ON lnf.norm_id = ln.id
JOIN lexical_lemmas ll ON ln.lemma_id = ll.id
WHERE lnf.written_form = 'ra-man-šú-nu'
ORDER BY ln.attestation_count DESC;
```

### All spellings for a lemma (Knowledge Bar S4)

```sql
SELECT ln.norm, ln.attestation_count,
       lnf.written_form, lnf.attestation_count AS form_count
FROM lexical_norms ln
LEFT JOIN lexical_norm_forms lnf ON lnf.norm_id = ln.id
WHERE ln.lemma_id = 12345
ORDER BY ln.attestation_count DESC, lnf.attestation_count DESC;
```

## API Endpoints

- `GET /dictionary/lookup?form={written_form}&language={lang}` -- written form -> candidate lemmas
- `GET /dictionary/lemmas/{id}/norms` -- all norms + forms for a lemma

## Knowledge Bar Integration

The normalization bridge powers the adaptive Knowledge Bar's pipeline states:

| State | How normalization helps |
|-------|----------------------|
| **S0 (Raw)** | No normalization data. Bar shows sign decomposition heuristics. |
| **S1 (Identified)** | Sign known, no lemma. `lookup_by_written_form()` provides "likely lemmas" with % bars. |
| **S2 (Lemmatized)** | Single lemma resolved. `get_norms_for_lemma()` shows orthographic variants. |
| **S3 (Ambiguous)** | Multiple candidates. `lookup_by_written_form()` ranks them by attestation frequency, narrowable by period/genre. |
| **S4 (Translated)** | Full chain complete. `get_norms_for_lemma()` shows "spellings on this tablet" section. |

## Import Pipeline

- **Step 18** (`18_import_norms.py`): Primary import from all ORACC glossaries. Phase 1 imports norms/forms, Phase 2 backfills `lemmatizations.norm_id`.
- **Step 15** (`15_import_epsd2_unified.py`): Will be modified to also extract norms from ePSD2 Sumerian glossary (currently discards `norms[]`).
- **Step 16** (`16_import_oracc_glossaries.py`): Will be modified to also extract norms alongside lemmas/senses.

## Relationship to Existing Tables

The normalization bridge integrates with but does not replace existing tables:

- **`glossary_forms`** (205k rows): Legacy import from ePSD2/ORACC. Keyed to `glossary_entries.entry_id` (TEXT), not to `lexical_lemmas.id`. Contains similar written-form data but not linked to the unified lexical schema. Long-term candidate for deprecation.
- **`lemmatizations.norm`** (TEXT column): Per-token norm from ORACC CDL. Retained as-is; the new `norm_id` FK supplements it by linking to the normalization bridge for dictionary lookup.
