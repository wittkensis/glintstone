# Citation Sourcing Pipeline

Import and link ALL known digitized Assyriology research citations into the Glintstone v2 schema.

**Prerequisite:** Full v2 schema migration must be complete before running import scripts.

## Provider Attribution

Every imported record links to an `annotation_run` with `source_name` identifying the data provider. Provider attribution MUST appear in any query response or UI that displays citation data.

## Data Sources

### Primary Sources

| Source | Volume | Access | Format | Provider Attribution | URL |
|--------|--------|--------|--------|---------------------|-----|
| CDLI API | 16,725+ pubs, 390k artifact links | REST, no auth | BibTeX/JSON/CSV | `CDLI - cdli.earth` | https://cdli.earth/docs/api |
| CDLI CSV | 83k pub_history, 20k citation rows | Local file | Freetext | `CDLI` | https://github.com/cdli-gh/data |
| ORACC | ~12 projects, ~10k artifact-edition links | Local JSON | Catalogue JSON | `ORACC/{project}` | https://oracc.museum.upenn.edu/ |
| eBL API | Fragment-level citations (CSL-JSON) | REST API | CSL-JSON | `eBL - Electronic Babylonian Literature` | https://www.ebl.lmu.de/ |

### Enrichment Sources

| Source | Volume | Access | Format | Provider Attribution | URL |
|--------|--------|--------|--------|---------------------|-----|
| OpenAlex | 184k+ Assyriology works (Topic T12307) | REST, no auth | JSON | `OpenAlex` | https://docs.openalex.org/ |
| Semantic Scholar | Citation graphs for known DOIs | REST, rate-limited | JSON | `Semantic Scholar` | https://api.semanticscholar.org/ |

### Scholar Directory Sources

| Source | Volume | Access | Format | Provider Attribution | URL |
|--------|--------|--------|--------|---------------------|-----|
| Who's Who in Cuneiform Studies | ~500-1000 scholars | Web page | HTML | `CDLI Wiki` | https://cdli.ox.ac.uk/wiki/doku.php?id=who_s_who_in_cuneiform_studies |
| Wikipedia Assyriologists | ~200 scholars | Web page | HTML | `Wikipedia` | https://en.wikipedia.org/wiki/List_of_Assyriologists |

### Pending/Manual Acquisition

| Source | Volume | Access | Format | Provider Attribution | URL |
|--------|--------|--------|--------|---------------------|-----|
| KeiBi | ~90,000 entries | **No API/dump** - web UI only | BibTeX export | `KeiBi - Keilschriftbibliographie` | https://vergil.uni-tuebingen.de/keibi/ |
| AfO Register | Annual bibliography | Subscription-gated | Web search | -- (deferred) | https://afo.orient.univie.ac.at/ |

**KeiBi acquisition:** No open API or data dump exists. Options: (a) contact Tuebingen project team for bulk BibTeX export, (b) manual per-volume export from web UI (~80 volumes). BibTeX is the export format.

## Scripts

| Script | Phase | Description |
|--------|-------|-------------|
| `01_cdli_publications.py` | 1A | Dynamic CDLI API fetch + import publications |
| `02_cdli_artifact_editions.py` | 1B+1C | API-first artifact-publication links + CSV fallback |
| `03_ebl_bibliography.py` | 2 | eBL API bibliography import with attribution |
| `04_oracc_editions.py` | 3 | ORACC project editions + scholar extraction |
| `05_cdli_csv_supplementary.py` | 4 | Parse citation, collation, join fields from CSV |
| `06_enrich_openalex.py` | 5 | DOI + ORCID backfill from OpenAlex |
| `07_import_keibi.py` | 6 | KeiBi BibTeX import (requires manual data acquisition) |
| `08_enrich_semantic_scholar.py` | 7 | Citation graph enrichment |
| `09_import_scholars_directory.py` | 8 | Who's Who + Wikipedia scholar import |
| `10_seed_supersessions.py` | 9 | Manual + algorithmic supersession chains |
| `11_cleanup_scholars.py` | 10 | Scholar deduplication, classification, and merge audit |
| `12_link_openalex_authors.py` | 11 | Parse OpenAlex author strings into scholar links |

## Shared Libraries

| Module | Purpose |
|--------|---------|
| `lib/checkpoint.py` | Checkpoint/resume, signal handling, progress reporting |
| `lib/name_normalizer.py` | Scholar name normalization and matching |
| `lib/publication_matcher.py` | Cross-source deduplication |
| `lib/bibtex_parser.py` | BibTeX parsing utilities |
| `lib/cdli_client.py` | Dynamic CDLI API client with local cache |
| `lib/ebl_client.py` | eBL API client with provider attribution |

## Running

```bash
# Full pipeline (phases run in dependency order)
./run_citation_import.sh

# Individual phases
python 01_cdli_publications.py [--reset]
python 02_cdli_artifact_editions.py [--reset]
# etc.

# Verification
python verify/verify_publications.py
python verify/verify_provider_attribution.py
```

## Data Freshness

Each import creates an `annotation_run` record with timestamp. Re-running a script checks cached data freshness and only re-fetches if stale.

Cache files stored in `_cache/`. Progress checkpoints in `_progress/`.

## Licenses

- **CDLI**: CC0 (public domain)
- **ORACC**: CC BY-SA 3.0 (per project)
- **eBL**: Check eBL terms of use
- **OpenAlex**: CC0 (public domain)
- **Semantic Scholar**: Check S2 API terms
- **KeiBi**: Check Tuebingen terms
- **Wikipedia**: CC BY-SA 4.0
