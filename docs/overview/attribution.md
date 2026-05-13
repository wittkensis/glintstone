# Attribution

Every record in Glintstone carries provenance tracing back to its source. This is structural, not a documentation convention.

## The annotation_run_id chain

Every annotation table in the database — lemmatizations, morphology, scholarly annotations, translations — carries an `annotation_run_id` column. Each run identifies:

- The source name (e.g., `oracc-epsd2`, `cdli-catalog`, `user-correction`)
- The method (e.g., `bulk-import`, `agent-hypothesis-correction`)
- The scholar ID, if the annotation is attributed to an individual
- A timestamp

This means you can always trace a lemmatization, a translation, or a correction back to exactly where it came from and when.

## Source licenses

| Source | License | Notes |
|--------|---------|-------|
| CDLI catalog and ATF | CC0 (public domain) | P-numbers, metadata, transliterations |
| ORACC projects (ePSD2, OGSL, etc.) | CC BY-SA 3.0 | Lemmatizations, glossaries, sign data |
| eBL | Research use | Varies by component; attribution required |

When displaying eBL-sourced data, "eBL — Electronic Babylonian Literature" must appear as a credit.

## How to cite Glintstone data

Glintstone is a federation layer, not an original data source. When citing data you find here, cite the upstream source. For CDLI data, use the CDLI P-number and the CDLI citation format. For ORACC lemmatizations, cite the ORACC project (e.g., ePSD2, ETCSRI). Glintstone does not claim credit for the underlying scholarship.

If you use the Glintstone API or MCP in a published workflow, a citation to glintstone.org with the date accessed is appropriate.

## Competing interpretations

Glintstone stores multiple interpretations of the same text without merging them. Two scholars who disagree on a lemmatization both get stored — as separate rows in the `lemmatizations` table, each with its own `annotation_run_id`.

The `is_consensus` flag marks interpretations that have been designated as the dominant scholarly reading. Interpretations without this flag are competing or provisional. The flag is set per annotation run, not globally — so a human expert's reading and BabyLemmatizer's reading for the same token can coexist, each correctly labeled.

This design reflects a basic fact about Assyriology: scholars genuinely disagree on grammar, readings, and interpretation. Silently deduplicating would erase that disagreement. Glintstone treats it as data.

## What "never silent overwrite" means

Glintstone has a hard rule: when new data arrives for an existing annotation, a new annotation run is created. The previous annotation is not deleted. This means the database is append-only for interpretive content. Historical states are recoverable. Nothing is silently overwritten.
