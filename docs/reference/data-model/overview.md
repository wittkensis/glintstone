# Data Model Overview

Glintstone's schema is organized into five layers. The P-number is the universal join key. Everything connects through it.

## The five layers

| Layer | Key tables | Current scale |
|-------|-----------|---------------|
| **1. Artifacts** | `artifacts`, `surfaces`, `artifact_identifiers`, `artifact_composites`, `composites` | 353,283 artifacts |
| **2. Texts** | `text_lines`, `tokens`, `token_readings`, `translations` | 1.4M lines, 3.96M tokens |
| **3. Linguistic Analysis** | `lemmatizations`, `morphology`, `annotation_runs` | ~309k lemma tokens |
| **4. Lexical Resources** | `signs`, `sign_values`, `sign_variants`, `lexical_lemmas`, `lexical_senses`, `glossary_entries`, `glossary_forms`, `glossary_senses` | 3,367 signs, 61k lemmas, 155k senses |
| **5. Scholarly Context** | `scholars`, `publications`, `publication_authors`, `artifact_editions`, `scholarly_annotations`, `fragment_joins` | 20,490 scholars, 16,725 publications |

## The P-number

`P227657` is an example P-number. CDLI assigned it. Every system in the field uses P-numbers as the universal artifact identifier. In Glintstone, it is the primary key on the `artifacts` table and the foreign key in nearly every other table.

Think of the P-number as the DOI for tablets.

## Q-numbers for composites

Some tablets are individual copies of a larger literary work — the Epic of Gilgamesh has 73 known exemplar tablets. Q-numbers (e.g., `Q000039`) identify the abstract composite text. Individual tablets link to composites via `artifact_composites`. The `composites` table holds Q-number metadata.

## The annotation_run_id

Every row in every annotation table (lemmatizations, morphology, scholarly_annotations, translations) carries `annotation_run_id`. This is the attribution backbone. Each annotation run identifies the source, method, scholar, and timestamp. Nothing is silently overwritten — new data creates new runs.

## Layer pages

- [Artifacts](/docs/reference/data-model/artifacts-layer/) — Layer 1: the physical object
- [Texts](/docs/reference/data-model/texts-layer/) — Layer 2: transliteration and tokens
- [Linguistic Analysis](/docs/reference/data-model/linguistic/) — Layer 3: lemmatization and morphology
- [Lexical Resources](/docs/reference/data-model/lexical/) — Layer 4: signs and dictionaries
- [Scholarly Context](/docs/reference/data-model/scholarly/) — Layer 5: scholars, publications, editions
