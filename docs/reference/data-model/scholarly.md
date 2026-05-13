# Scholarly Context — Layer 5

Layer 5 tracks the human infrastructure behind the corpus: the scholars who have studied these texts, the publications they have produced, and the editions connecting individual tablets to the literature.

## Key tables

**`scholars`** — 20,490 researcher records. Key fields:
- `name` — normalized full name
- `orcid` — ORCID identifier (where resolved via OpenAlex, ~10–20% coverage)
- `institution` — affiliation when known
- `merge_target_id` — null unless this record is a duplicate; points to the canonical record

**`publications`** — 16,725 academic publications. Key fields:
- `title`, `year`, `journal`
- `doi` — present for ~15–30% (via OpenAlex backfill)
- `bibtex_key` — CDLI bibliography key
- `source` — cdli-api, cdli-csv, ebl, openalexo

**`publication_authors`** — Junction table linking scholars to publications.

**`artifact_editions`** — Editions linking a tablet (P-number) to a publication. Tracks which publication contains the primary edition of a text.

**`scholarly_annotations`** — Free-text scholarly notes associated with an artifact, drawn from CDLI CSV collation fields. Confidence 0.3–0.7 depending on parse quality.

**`fragment_joins`** — Records of scholars proposing that two separate museum fragments belong to the same tablet. Drawn from CDLI CSV join fields.

## OpenAlex for DOI and ORCID backfill

Glintstone uses the OpenAlex API (CC0) to enrich publication and scholar records. For publications with DOIs, OpenAlex provides citation counts, journal metadata, and linked ORCID identifiers for authors. Topic T12307 ("Ancient Near East History") is the primary filter for cuneiform-relevant works.

## Scholar deduplication

The scholar database contains duplicates from different source representations of the same person — "J. Smith", "John Smith", "Smith, John" — especially across CDLI and eBL bibliography data. Deduplication uses `name_normalizer.py`, which provides:

- `parse_name()` — normalizes a raw name string to (last, first, initials)
- `parse_author_string()` — handles "Last, F.M." and "First Last" conventions
- `names_match()` — returns a 0.0–1.0 similarity score

When two records are merged, `scholar_merge_log` records the merge with the kept and removed scholar IDs, timestamp, and method. The `scholars.merge_target_id` column points to the canonical record for any removed duplicate. Foreign key references in `publication_authors` and `artifact_editions` are updated to point to the canonical record.

## Citation pipeline sources

| Source | What it provides | Confidence |
|--------|-----------------|------------|
| CDLI API | Primary publication links | 1.0 |
| CDLI CSV | Supplementary citations, fragment joins | 0.3–0.7 |
| eBL API | Fragment-level citations (CSL-JSON) | 1.0 |
| OpenAlex | DOI backfill, ORCID backfill | 0.8–0.9 |
| Semantic Scholar | Citation graphs for DOI-resolved publications | 0.9 |

Cross-source deduplication cascade: DOI exact match (1.0) > bibtex_key (0.95) > title+year (0.8) > short_title+volume+page (0.9). Records below 0.7 similarity are staged for manual review.
