# Artifacts — Layer 1

Layer 1 is the physical object: what it is, where it came from, what catalog records describe it.

## Key tables

**`artifacts`** — One row per cuneiform object. Key fields:

| Field | Notes |
|-------|-------|
| `p_number` | Primary key. CDLI universal identifier. |
| `designation` | Human-readable label (e.g., "CDLI Seals 001234") |
| `museum_number` | Museum accession number |
| `excavation_number` | Field excavation ID |
| `period` | Normalized period string (e.g., "Ur III (ca. 2112-2004 BC)") |
| `provenience` | Find site (e.g., "Nippur (mod. Nuffar)") |
| `genre` | Text genre (Administrative, Literary, Legal, etc.) |
| `language` | Primary language |
| `object_type` | Tablet, prism, cone, seal, etc. |
| `material` | Clay, stone, metal, etc. |
| `pipeline_stage` | One of: captured, recognized, transcribed, lemmatized, translated |
| `collection` | Holding institution |

**`surfaces`** — Named surfaces of the physical object: obverse, reverse, left/right/top/bottom edges, seal. One tablet can have multiple surfaces.

**`artifact_identifiers`** — Alternative identifiers for the same artifact: museum number, excavation number, primary publication. Multiple identifier types per artifact.

**`composites`** — Q-number composite texts (abstract literary works).

**`artifact_composites`** — Junction table linking P-numbers to Q-numbers.

## Where data comes from

Almost all Layer 1 data comes from the CDLI catalog (`cdli_cat.csv`), which provides 353,283 records with 64 metadata fields per artifact. CDLI is CC0 — public domain.

The CDLI bulk export was last updated in August 2022. Approximately 33,000 additional stub records exist for P-numbers present in the ATF file but absent from the catalog CSV — these have minimal metadata.

## Null rates

From a live database audit of the CDLI catalog:

| Field | Null rate |
|-------|-----------|
| museum_number | 9.2% |
| excavation_number | 68% |
| width / height | 82% |
| thickness | 91% |
| period | 1.8% |
| provenience | 3.1% |
| genre | 1.4% |
| language | 5.2% |

Expect NULLs. Physical measurement data is especially sparse.

## Canon tables

Raw source data uses inconsistent strings for period, provenience, language, and genre. Canon tables normalize these to consistent values used throughout the app:

- `period_canon` — maps period strings to canonical forms and groups (e.g., "Third Millennium")
- `provenience_canon` — maps raw provenience strings to short canonical names
- `language_map` — maps ISO-style language codes to display labels
- `genre_canon` — maps raw genre strings to canonical forms

The filter system operates on canonical values.

## The pipeline_stage column

`pipeline_stage` is a string enum on `artifacts` tracking the highest stage the artifact has reached: `captured`, `recognized`, `transcribed`, `lemmatized`, `translated`. It is set during ingestion and updated as new data arrives.
