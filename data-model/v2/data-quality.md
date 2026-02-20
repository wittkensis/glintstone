# Data Quality and Academic Trust

Glintstone's data model is designed around a core principle: every claim about a cuneiform text -- its reading, lemmatization, translation, or identification -- should be traceable to the scholar, tool, or import process that produced it. This document describes how the schema enforces provenance, supports competing interpretations, and validates data integrity.

---

## Provenance Architecture

### annotation_runs: The Trust Backbone

Every record in the database carries an `annotation_run_id` foreign key linking it to an `annotation_runs` record. This single mechanism handles all provenance:

| Field | Purpose |
|-------|---------|
| `source_type` | human, model, hybrid, or import |
| `source_name` | Provider attribution string (e.g., "ORACC/dcclt", "BabyLemmatizer v2.2", "CDLI - cdli.earth") |
| `scholar_id` | FK to scholars table (NULL for ML/import runs) |
| `method` | How the annotation was produced: hand_copy, photograph, collation, autopsy, RTI, 3D_scan, ML_model, import |
| `publication_id` | Structured link to the publication where this annotation appeared |
| `created_at` | When the annotation was recorded |

This design means a single JOIN from any data row to `annotation_runs` answers: *who said this, when, how, and where was it published?*

### Provider Attribution

Each data source has a canonical attribution string stored in `annotation_runs.source_name`. These strings must appear in the UI when displaying source-specific data:

- `CDLI - cdli.earth`
- `ORACC/{project_name}` (e.g., ORACC/dcclt, ORACC/saao)
- `eBL - Electronic Babylonian Literature`
- `CompVis`
- `OpenAlex`
- `KeiBi - Keilschriftbibliographie`

Verification: `verify_provider_attribution.py` checks that no records exist without a valid `annotation_run_id` and that all provider strings match the canonical list.

### Scholar Records

The `scholars` table tracks individual contributors with:
- Normalized name (diacritics handled, particles like "von" and "de" standardized)
- ORCID persistent identifier (backfilled from OpenAlex where available)
- Expertise metadata: period specializations, language competencies
- Active-since year (from Who's Who in Cuneiform Studies)

Name deduplication uses cascading match: ORCID exact > surname+initials normalized > full name fuzzy. Ambiguous matches are flagged for manual review.

---

## Competing Interpretations

A single token position on a tablet may have multiple valid readings or lemmatizations proposed by different scholars or tools. The schema preserves all of them.

### Token Readings (Reading Layer)

`token_readings` stores multiple transliterations for the same `token_id`:

```
Token P000001, line 3, position 5:
  Reading A: form="du₃"    source=ORACC/dcclt    confidence=0.95  is_consensus=1
  Reading B: form="KAK"    source=BabyLemmatizer  confidence=0.72  is_consensus=0
```

The `is_consensus` flag marks the editorially chosen or highest-confidence reading. At most one reading per token carries this flag.

### Lemmatizations (Linguistic Layer)

`lemmatizations` stores multiple linguistic analyses for the same token:

```
Token P000001, line 3, position 5:
  Analysis A: cf="banû" gw="build" pos=V  source=ORACC/dcclt  confidence=0.95  is_consensus=1
  Analysis B: cf="banû" gw="build" pos=V  source=BabyLemmatizer  confidence=0.88  is_consensus=0
```

When sources agree, this strengthens confidence. When they disagree, the competing analyses are preserved for scholarly review.

### Decision Audit Trails

Three decision tables record how consensus was reached:

- `token_reading_decisions`
- `lemmatization_decisions`
- `translation_decisions`

Each decision records: who decided, the method (editorial, vote, algorithm, import_default), rationale, timestamp, and a `supersedes_id` chain linking to the previous decision. This creates an immutable audit trail -- decisions are never deleted, only superseded.

---

## Evidence System

Four evidence tables link annotations to their supporting material:

| Table | Links To | Evidence Types |
|-------|----------|----------------|
| `token_reading_evidence` | token_readings | photograph, hand_copy, collation, RTI, 3D_scan |
| `lemmatization_evidence` | lemmatizations | publication, glossary_match, parallel_text |
| `sign_annotation_evidence` | sign_annotations | photograph, 3D_scan, dataset_ground_truth |
| `translation_evidence` | translations | publication, parallel_text, personal_communication |

Each evidence row contains:
- `evidence_type`: What kind of evidence (catalog_entry, museum_record, publication, photograph, collation, autopsy, database_export, personal_communication)
- `evidence_ref`: URL, DOI, catalog page, or freetext citation
- `added_by`: FK to scholars table
- `note`: Contextual explanation

This enables questions like: *What evidence supports Reading A over Reading B for this token?*

---

## Citation Resolution

A three-tier system links artifacts to their publication history:

### Tier 1: Identity Concordance

`artifact_identifiers` maps every known identifier (museum number, excavation number, publication designation, project ID) to its P-number. Normalized for fast lookup.

### Tier 2: Publication Registry

`publications` stores structured bibliographic records with:
- BibTeX keys prefixed by authority (cdli:, oracc:, ebl:, openalex:, keibi:)
- Series membership (RIME, SAA, RINAP, VAB)
- Supersession chains: `supersedes_id` tracks when a newer publication replaces an older one

### Tier 3: Edition Bridge

`artifact_editions` links individual artifacts to publications with granular metadata:
- Edition type: full_edition, hand_copy, photograph_only, catalog_entry, collation, translation_only, commentary
- `is_current_edition`: Algorithmically set (newest full_edition wins), at most one per artifact, manually overridable via `artifact_edition_decisions`
- Per-artifact supersession (more granular than publication-level -- one publication may supersede another for some artifacts but not all)

### W3C Web Annotation Export

`scholarly_annotations` supports export to W3C Web Annotation Data Model format for interoperability with annotation federation tools. Each annotation carries strict FK targeting (exactly one non-NULL target FK per row, enforced by CHECK constraint).

---

## Import Validation

### Pressure Testing

12 critical data issues were identified by testing the schema against the live 314 MB database (389,715 artifacts). All are addressed in the v2 design. See [data-issues.md](data-issues.md) for the full catalog.

Key issues and their fixes:

| Issue | Severity | Fix |
|-------|----------|-----|
| Period string chaos (46+ formats) | High | `period_canon` lookup + `period_normalized` column |
| Language code mismatch (CDLI vs ORACC) | High | `language_map` lookup + `languages` JSON array |
| 72% of lemma rows are unlemmatized tokens | High | Separate tokens (all 309k) from lemmatizations (86k with real identifications) |
| Sign annotations use MZL, no OGSL concordance | High | Auto-match via Unicode bridge, flag ~200-400 unresolved |
| Empty glossary_senses table | High | Parse senses[] arrays from ORACC glossary JSON |
| Glossary entry dedup across projects | Medium | UNIQUE(headword, language, project), keep all with source attribution |

### Per-Import Validation

Every import step runs validation checks:
- **Row count**: Expected vs actual, warning if deviation > 5%
- **NULL audit**: Critical columns checked against threshold (e.g., p_number must be 0% NULL)
- **FK integrity**: All foreign keys verified post-import
- **annotation_run_id NOT NULL**: Enforced -- no orphan records allowed
- **Deduplication**: Cross-source duplicates caught by cascading match (DOI > bibtex_key > title+year > short_title+volume)

Imports below confidence threshold (0.7) are staged in `_dedup_candidates` for manual review rather than auto-merged.

### Checkpoint/Resume

The `ImportCheckpoint` class provides:
- SIGINT/SIGTERM signal handling with graceful state save
- Atomic state file writes (JSON in `_progress/` directory)
- Source checksums to detect upstream changes since last run
- Progress reporting: processed/inserted/updated/skipped/errors per step

---

## Completeness Transparency

Glintstone surfaces data gaps honestly rather than hiding them. Key coverage metrics:

- **Lemmatization**: Only ~2% of artifacts have ORACC linguistic annotation. The remaining 98% exist at the identity or text layer only.
- **Geographic coordinates**: ~3% of artifacts have Pleiades-linked coordinates (via ORACC geojson).
- **Physical dimensions**: Width/height available for ~18% of artifacts.
- **Images**: Coverage varies widely by collection. Many tablets have no published photographs.
- **Sign concordance**: ~200-400 MZL numbers remain unresolved to OGSL after auto-matching.

The `pipeline_status` table tracks 5-stage completeness (Image > OCR > ATF > Lemmas > Translation) per artifact, making gaps visible in every view.

---

## Trade-offs and Open Questions

### JSON vs. Normalized Tables for GDL

Sign-level Grapheme Description Language (GDL) data is stored as JSON on `tokens.gdl_json` rather than in a normalized `sign_instances` table. JSON is simpler to import and query for display. Normalized tables would enable queries like "find all tokens containing sign AN" but add significant complexity. Leaning JSON for v2.0 with the option to normalize later.

### Sumerian Morphology Framework

Sumerian verbal morphology is actively debated. The `morphology` table uses a slot-based model with columns for conjugation_prefix, dimensional_prefixes, stem_form, pronominal_suffix, aspect, and transitivity. Different scholarly frameworks (Jagersma, Zolyomi, Edzard) analyze these slots differently. The schema supports storing multiple morphological analyses as competing annotations via the same provenance mechanism used for lemmatizations.

### Metadata Conflicts Between Sources

CDLI and ORACC sometimes disagree on period, genre, or provenience for the same artifact. Resolution: CDLI is authoritative for identity fields. ORACC-specific enrichment (subgenre, supergenre, geographic coordinates) stored in separate columns. Both raw and normalized values preserved.

### CDLI Upstream Freeze

The CDLI bulk catalog export has not been updated since August 2022. New tablets added to CDLI after this date are not reflected in Glintstone. The API provides more recent data for some fields (publications, artifact-edition links) but not the full catalog.
