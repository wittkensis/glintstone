# Citation Sourcing Pipeline: Data Model Impact Summary

This document describes the citation sourcing pipeline built to populate the trust, citation, knowledge graph, and annotation infrastructure in the Glintstone v2 schema. Written for handoff to another agent reviewing the data model.

**Related docs**: [data-quality.md](data-quality.md) (trust architecture), [data-sources.md](data-sources.md) (all sources including citations), [ml-integration.md](ml-integration.md) (ML models as annotation sources using the same provenance system), [import-pipeline-guide.md](import-pipeline-guide.md) (this is step 18 of 19).

## What This Pipeline Does

Imports ALL known digitized Assyriology research citations from 9 external sources into the v2 schema. Goal: every artifact, translation, reading, and scholarly claim in Glintstone becomes citable with full provenance -- who said it, where it was published, what evidence supports it, and whether it's the current consensus.

## Prerequisite

The full v2 schema migration must complete before this pipeline runs. All target tables below are NEW in v2 (none exist in v1).

## External Data Sources

| Source | Records | Access | Provider Attribution String |
|--------|---------|--------|---------------------------|
| CDLI API (cdli.earth) | 16,725 pubs + 390k artifact-pub links | REST, no auth, CC0 | `CDLI - cdli.earth` |
| CDLI CSV (cdli_cat.csv) | 83k pub_history rows, 20k citations, 4k collations, 7k joins | Local file | `CDLI` |
| eBL API (ebl.lmu.de) | Fragment-level citations in CSL-JSON | REST, may need token | `eBL - Electronic Babylonian Literature` |
| ORACC projects | 12 projects, ~10k artifact-edition links | Local JSON exports | `ORACC/{project_name}` |
| OpenAlex | 5-20k Assyriology works | REST, no auth, CC0 | `OpenAlex` |
| KeiBi (Keilschriftbibliographie) | ~90,000 entries | No API -- manual BibTeX export | `KeiBi - Keilschriftbibliographie` |
| Semantic Scholar | Citation graphs for publications with DOIs | REST, rate-limited | `Semantic Scholar` |
| CDLI Who's Who + Wikipedia | ~500-1000 scholar records | Web scrape | `CDLI Wiki` / `Wikipedia` |

## v2 Tables Populated by This Pipeline

### Direct Targets (pipeline writes to these)

#### `scholars` (Trust layer)
- **Populated by**: CDLI publication author parsing, ORACC credits extraction, OpenAlex ORCID backfill, Who's Who/Wikipedia scrape
- **Fields filled**: `name`, `orcid` (via OpenAlex), `institution`, `active_since` (via Who's Who)
- **Estimated yield**: 2,000-5,000 unique scholars across all sources
- **Dedup key**: Normalized name (surname + initials, diacritics stripped, particles handled). ORCID is authoritative when available.

#### `annotation_runs` (Provenance)
- **Populated by**: Every import phase creates one or more annotation_run records
- **Fields filled**: `source_type` = "import", `source_name` = provider string (see table above), `method` = "api_fetch" or "import", `created_at`
- **Design rule**: Every record in every target table carries an `annotation_run_id` FK. This is how provider attribution propagates. The `source_name` on annotation_runs is the single source of truth for "where did this data come from?"

#### `publications` (Citation Resolution)
- **Populated by**: CDLI API (16,725), eBL API (varies), ORACC projects (12 digital editions), OpenAlex (5-20k), KeiBi (up to 90k)
- **Fields filled**: `bibtex_key` (UNIQUE), `doi` (UNIQUE, nullable), `title`, `short_title`, `publication_type`, `year`, `series_key`, `volume_in_series`, `authors`, `editors`, `publisher`, `place`, `url`, `oracc_project`, `supersedes_id`, `superseded_scope`
- **bibtex_key convention**: CDLI keys are canonical (e.g., `Frayne1990RIME4`). KeiBi keys prefixed with `keibi:`. ORACC projects prefixed with `oracc:`. eBL-sourced publications prefixed with `ebl:`. OpenAlex prefixed with `openalex:`.
- **Supersession chains**: ~50 manually curated publication-level supersessions (e.g., RIME 4 supersedes VAB 6). `supersedes_id` is a self-referential FK.
- **publication_type values used**: monograph, journal_article, chapter, digital_edition, conference_paper, thesis, other

#### `publication_authors` (Citation Resolution)
- **Populated by**: Author/editor parsing from every source that provides author data
- **Fields filled**: `publication_id` (FK), `scholar_id` (FK), `role` (author/editor/translator/contributor), `position` (author order)
- **Constraint**: UNIQUE(publication_id, scholar_id, role)
- **Relationship**: This is the structured bridge between publications and scholars. The `authors` TEXT column on publications is the semicolon-separated fallback.

#### `artifact_editions` (Citation Resolution / Edition Tracking)
- **Populated by**: CDLI API artifact-publication links (primary, ~470k), CDLI CSV publication_history parsing (fallback), ORACC catalogue membership (~10k), eBL fragment bibliography
- **Fields filled**: `p_number` (FK to artifacts), `publication_id` (FK), `reference_string`, `reference_normalized`, `page_start`, `plate_no`, `item_no`, `edition_type`, `is_current_edition`, `supersedes_id`, `confidence`, `note`
- **Import strategy**: CDLI API data is imported first (confidence 1.0). CSV data is imported only for artifacts NOT covered by the API (tiered confidence: 1.0/0.7/0.3 based on regex parse quality). Dedup on UNIQUE(p_number, publication_id, reference_string).
- **is_current_edition**: Set algorithmically in Phase 9 -- newest full_edition per artifact wins. At most 1 per artifact (verified by check script). Manually overridable via artifact_edition_decisions.
- **edition_type values used**: full_edition, hand_copy, photograph_only, catalog_entry, collation, translation_only, commentary
- **Per-artifact supersession**: `supersedes_id` chain separate from publication-level (more granular -- one publication may supersede another for some artifacts but not all)

#### `scholarly_annotations` (Annotation Ecosystem)
- **Populated by**: CDLI CSV `citation` field (20,928 rows)
- **Fields filled**: `artifact_id` (FK), `annotation_type` = "bibliography", `content` (raw citation text), `annotation_run_id`, `confidence`, `visibility` = "public"
- **Strict FK targeting**: Exactly one non-NULL target FK per row (artifact_id in this case). CHECK constraint enforces this.

#### `fragment_joins` (Annotation Ecosystem)
- **Populated by**: CDLI CSV `join_information` field (7,367 rows)
- **Fields filled**: `fragment_a`, `fragment_b` (both FK to artifacts), `join_type` = "uncertain", `annotation_run_id`, `confidence` = 0.6, `note`
- **Constraint**: UNIQUE(fragment_a, fragment_b). Ordering enforced (a < b alphabetically).

### Indirect Targets (pipeline enriches existing records)

#### `publications.doi`
- **Enriched by**: OpenAlex (Phase 5). Matches existing publications by normalized title + year, backfills DOI.

#### `scholars.orcid`
- **Enriched by**: OpenAlex (Phase 5). Matches existing scholars by normalized name, backfills ORCID from OpenAlex author records.

### Pipeline-Internal Table (not in v2 schema)

#### `_dedup_candidates`
- Staging table for cross-source publication duplicates below confidence threshold
- Schema: `pub_a_id`, `pub_b_id`, `match_method`, `confidence`, `resolved`, `resolution`
- Created by the pipeline; consumed by manual curation; can be dropped after review

## Tables NOT Directly Populated (but Structurally Enabled)

The following v2 tables are structurally ready to receive data from this pipeline's output but require additional import work beyond what this pipeline does:

| Table | What's missing | Why |
|-------|---------------|-----|
| `artifact_identifiers` | Seeded from artifacts.museum_no/excavation_no during v2 migration, not by this pipeline | Different migration scope |
| `artifact_identifier_evidence/decisions` | Awaits identifier disputes | No disputes at import time |
| `artifact_edition_evidence` | Awaits manual evidence attachment | Evidence is publication-level, not import-level |
| `artifact_edition_decisions` | Awaits editorial review | is_current_edition set algorithmically; decisions come from scholars |
| `named_entities` | Populated from glossary_entries, not from citations | Separate pipeline (glossary import) |
| `entity_mentions` | Populated from ORACC lemmatization corpus | Separate pipeline |
| `entity_relationships` | Semantic Scholar citation graphs stored here (Phase 7), but most relationships come from scholarly assertions | Partially populated |
| `authority_links` | Wikipedia Wikidata IDs could flow here but require entity_id mapping | Partially populated (scholar -> Wikidata deferred) |
| `discussion_posts/threads` | User-generated scholarly discourse | Not an import concern |

## Provider Attribution Architecture

Every record traces back to its data source through this chain:

```
any_record.annotation_run_id
  -> annotation_runs.source_name   (e.g., "CDLI - cdli.earth")
  -> annotation_runs.source_type   ("import")
  -> annotation_runs.method        ("api_fetch" or "import")
  -> annotation_runs.created_at    (import timestamp)
```

This is enforced by a verification script (`verify_provider_attribution.py`) that checks:
1. No publications without annotation_run_id
2. No annotation_runs without source_name
3. No artifact_editions without annotation_run_id
4. Distribution of records by provider

**eBL-specific requirement**: Any query response or UI display that includes eBL-sourced data must show "eBL - Electronic Babylonian Literature" attribution. This is not just a schema concern -- it's an application-layer requirement documented in the eBL import script and README.

## Deduplication Strategy

Cross-source matching uses a cascading key hierarchy:

1. **DOI exact** (confidence 1.0) -- globally unique
2. **bibtex_key exact within authority** (0.95) -- CDLI keys authoritative within CDLI scope
3. **title + year fuzzy** (0.8) -- normalized title (lowercase, no diacritics, no articles), Levenshtein ratio > 0.85, year exact match
4. **short_title + volume exact** (0.9) -- "RIME 4" matches regardless of full title
5. Below 0.7 -> `_dedup_candidates` staging table for manual review

## Scholar Name Resolution

Assyriological names have specific challenges (diacritics, particles, initial variants). The pipeline normalizes via:
- Strip diacritics (NFKD decomposition)
- Extract surname + initials, handling particles (von, de, al-)
- Create `normalized_key` = `{surname_lower}_{initials_lower}`

Resolution cascade: ORCID exact (1.0) -> name+institution (0.95) -> name+period overlap (0.85) -> surname+coauthor network (0.7) -> manual

## File Locations

Pipeline code: `data/v2-schema-tools/citations/`

```
01_cdli_publications.py         # CDLI API -> publications, scholars, publication_authors
02_cdli_artifact_editions.py    # CDLI API + CSV -> artifact_editions
03_ebl_bibliography.py          # eBL API -> publications, artifact_editions
04_oracc_editions.py            # ORACC JSON -> publications, artifact_editions, scholars
05_cdli_csv_supplementary.py    # CDLI CSV -> scholarly_annotations, artifact_editions, fragment_joins
06_enrich_openalex.py           # OpenAlex -> publications (new + DOI backfill), scholars (ORCID backfill)
07_import_keibi.py              # KeiBi BibTeX -> publications, scholars
08_enrich_semantic_scholar.py   # Semantic Scholar -> citation graph cache
09_import_scholars_directory.py # Web scrape -> scholars
10_seed_supersessions.py        # Manual + algorithmic -> publications.supersedes_id, artifact_editions.is_current_edition
lib/                            # Shared: checkpoint, name_normalizer, publication_matcher, bibtex_parser, cdli_client, ebl_client
verify/                         # verify_publications.py, verify_provider_attribution.py
run_citation_import.sh          # Orchestrator (runs all phases in dependency order)
```

## Execution Dependencies

```
Phase 1 (CDLI publications)
  |
  +-> Phase 1B+1C (artifact editions)     -- needs publication_ids
  +-> Phase 4 (CSV supplementary)          -- needs publication_ids
  +-> Phase 5 (OpenAlex enrichment)        -- enriches existing publications
  |     +-> Phase 7 (Semantic Scholar)     -- needs DOIs from OpenAlex
  +-> Phase 6 (KeiBi)                      -- dedup against existing
  +-> Phase 9 (supersessions)              -- needs all editions present

Phase 2 (eBL)           -- independent
Phase 3 (ORACC)         -- independent
Phase 8 (scholars dir)  -- independent
```

## Data Quality Indicators

| Metric | Expected Value |
|--------|---------------|
| Publications with bibtex_key | 100% (required) |
| Publications with DOI | 15-30% (after OpenAlex enrichment) |
| Scholars with ORCID | 10-20% (after OpenAlex enrichment) |
| Artifact editions from API (confidence 1.0) | ~60% of total |
| Artifact editions from CSV (confidence 0.3-0.7) | ~40% of total |
| Artifacts with at least 1 edition | 20-40% of 353k artifacts |
| Artifacts with is_current_edition set | subset of above |
| Dedup candidates pending manual review | 500-2000 |

## Open Questions for Data Model Review

1. **annotation_runs.method values**: The pipeline uses "api_fetch" and "import". Are these sufficient, or should we add "web_scrape" for scholar directories?

2. **publications.publication_type**: The v2 schema defines 9 values. The pipeline maps from CDLI (numeric entry_type_id), OpenAlex (CSL types), eBL (CSL types), and BibTeX (entry types). Some mappings are approximate. Should we add "digital_edition" handling for ORACC projects or is that covered?

3. **scholarly_annotations target FK**: The CSV citation import targets `artifact_id`. Should some citations instead target `line_id` or `composite_id` when the citation references a specific line or composite text?

4. **fragment_joins without join_groups**: The CSV import creates fragment_joins without join_group_id (the join_groups table is designed for manually curated multi-fragment reconstructions). Should we auto-create join_groups, or leave group assignment for later curation?

5. **eBL reference types**: eBL distinguishes EDITION, DISCUSSION, COPY, PHOTO, TRANSLATION, ARCHAEOLOGY, ACQUISITION, SEAL. These map to artifact_editions.edition_type but not perfectly (ARCHAEOLOGY and ACQUISITION have no direct v2 equivalent -- currently mapped to "catalog_entry"). Worth adding edition_type values?

6. **Supersession chain validation**: The pipeline sets `is_current_edition` algorithmically (newest full_edition wins). This could be wrong when a newer publication only partially supersedes an older one. The `artifact_edition_decisions` table exists for manual correction, but should the algorithm be more conservative (e.g., only set is_current_edition for CDLI API-sourced "primary" type links)?
