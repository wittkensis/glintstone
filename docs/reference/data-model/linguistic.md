# Linguistic Analysis — Layer 3

Layer 3 is the interpretive layer: the assignment of dictionary entries and grammatical structure to individual tokens.

## Key tables

**`lemmatizations`** — One row per token-interpretation pair. Key fields:

| Field | Notes |
|-------|-------|
| `token_id` | Foreign key to tokens |
| `annotation_run_id` | Which run produced this interpretation |
| `cf` | Citation form (the canonical dictionary headword, e.g., "lugal") |
| `gw` | Guide word (English gloss, e.g., "king") |
| `pos` | Part of speech (N, V, AJ, AV, etc.) |
| `epos` | Effective part of speech in context |
| `lang` | Language code (sux, akk, akk-x-stdbab, etc.) |
| `sense` | Contextual sense, if assigned |
| `is_consensus` | Whether this is the dominant scholarly reading |
| `source_type` | "human" or "model" |
| `confidence` | Confidence score (0.0–1.0), set by model runs |

**`morphology`** — Grammatical decomposition: stem, prefixes, suffixes, case, tense, person, number. One row per lemmatization with morphological annotation.

**`annotation_runs`** — Every source that has contributed interpretive data to Glintstone. Key fields:
- `source_name` — e.g., `oracc-epsd2`, `baby-lemmatizer`, `user-correction`
- `method` — `bulk-import`, `model-inference`, `agent-hypothesis-correction`
- `scholar_id` — optional link to scholars table for individual-attributed work
- `source_type` — `human` or `model`
- `created_at` — timestamp

## How competing interpretations coexist

The `lemmatizations` table does not have a unique constraint on `(token_id)`. Multiple rows for the same token are expected and correct. Each represents a distinct interpretation from a distinct annotation run.

Example: ORACC's human-lemmatized reading and BabyLemmatizer's ML prediction for the same token both appear in the table, each with its own `annotation_run_id`, its own `confidence`, and its own `source_type`.

The `is_consensus` flag indicates which interpretation is considered authoritative. It is set per annotation run — the same token can have one consensus reading and one or more competing ones.

## The annotation_run_id chain

Every lemmatization traces back to a run. Every run traces back to a source. If you need to audit where a specific interpretation came from, follow: `lemmatizations.annotation_run_id → annotation_runs.source_name`.

This chain is also how corrections work: when a scholar submits a correction via `submit_correction`, a new annotation run is created with `method='agent-hypothesis-correction'`. The corrected token then has an additional row in `lemmatizations` from the new run.

## Coverage

Only ~7,500 texts (~2% of the catalog) have any lemmatization. All of this comes from ORACC human-annotated projects. BabyLemmatizer has been evaluated but its full-corpus run has not yet been executed. When it is, its output will be stored with `source_type='model'` and a confidence score.

## source_type and confidence

Human ORACC lemmatizations: `source_type='human'`, `confidence=1.0`.
BabyLemmatizer (when run): `source_type='model'`, `confidence` set per token based on model output (typically 0.68–0.96).
User corrections: `source_type='human'`, `confidence=1.0`, `method='agent-hypothesis-correction'`.
