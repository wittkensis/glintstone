# Roadmap

Glintstone is being built in close consultation with working Assyriologists. The goal is to earn its place in the scholarly workflow — and that takes iteration.

## Defining with Experts

The most important step before any feature is understanding how scholars actually work. We are seeking direct input from cuneiform specialists on annotation workflows, search needs, and the trust infrastructure required for scholarly editions to carry real weight.

Current status: exploratory conversations underway. If you are a working Assyriologist and want to shape this platform, [get in touch](mailto:eric.wittke@gmail.com).

## Translation Builder

A structured interface for composing line-by-line translations with full provenance tracking — linking every phrase to a lemma, a reading, and the scholar who proposed it. Competing translations coexist in the data model. The Translation Builder makes that visible and navigable.

Current status: multiple prototype iterations complete. Core data model designed.

## Glintstone API

A REST API providing programmatic access to artifact metadata, ATF transliterations, lemmatizations, translations, and lexical data. Designed to serve ML pipelines, other tools, and public integrations.

Current status: **live** at [api.glintstone.org](https://api.glintstone.org). See the [API Reference](/docs/reference/api/) for endpoint documentation.

## LLM Integration & ML Models

BabyLemmatizer for automated Sumerian POS tagging, DETR-based sign detection via DeepScribe and CompVis, and Akkademia for sign recognition. These models run as annotation pipelines with explicit source attribution — their output is stored as competing interpretations, not ground truth.

Current status: models evaluated, import pipeline designed, full-corpus runs not yet executed.

## Improved Search

Faceted search across 353k artifacts by period, provenience, genre, language, and pipeline stage. Full-text and semantic search over transliterations and lemmas.

Current status: basic filtering implemented. Hybrid semantic search live via the `/search` endpoint and MCP. Browser-facing semantic search in development.

## Sign Dictionary

Browsable lexicon of all cuneiform signs — values, readings, sign lists (OGSL), and their attestations in the corpus. Sumerian and Akkadian entries with senses and forms.

Current status: OGSL and ePSD2 data imported (3,367 signs, 61k lemmas, 155k senses). Browser UI in early development.

## Scholarly Contribution

The long-term goal: a platform where a scholar's annotations, corrections, and translations are attributed, discoverable, and citable. This requires significant scholarly input to get the trust infrastructure right.

Current status: annotation run schema designed. `submit_correction` MCP tool live. External contribution workflows not yet designed.

## Multilingual Support

Sumerian, Akkadian, and Elamite are the primary languages in the corpus, with smaller presences of Hittite, Hurrian, and others. The data model is language-aware; display support varies by script.
