# Lexical Resources — Layer 4

Layer 4 is the dictionary: the canonical inventory of signs and the lexical database of lemmas and senses.

## Key tables

**Signs (from OGSL)**

- `signs` — 3,367 cuneiform signs. Fields: Unicode codepoint, canonical name, sign type (simple, compound, modified), GDL structural definition.
- `sign_values` — ~15,000 reading values for signs, with sub-indices. A single sign like KA can have readings: `ka`, `gu`, `dug`, `inim`, `zu`.
- `sign_variants` — Variant forms and glyph families.

**Lexical entries (from ePSD2 and ORACC glossaries)**

- `lexical_lemmas` — 61,435 dictionary headwords. Fields: citation form (`cf`), guide word (`gw`), part of speech (`pos`), language code, source (epsd2, ogsl, oracc), attestation count.
- `lexical_senses` — 155,491 meaning distinctions per lemma. One lemma can have multiple senses with different glosses and usage contexts.
- `glossary_entries` — ORACC glossary entries for specific projects.
- `glossary_forms` — Variant written forms attested in the corpus for a glossary entry.
- `glossary_senses` — Sense data from ORACC project glossaries.

## OGSL as sign authority

The ORACC Global Sign List is Glintstone's canonical sign inventory. OGSL assigns internal sign IDs that serve as the primary key in `signs`. MZL (Borger's Mesopotamisches Zeichenlexikon) numbers are mapped via Unicode codepoints for cross-reference with CompVis and other systems.

~200–400 CompVis MZL labels remain unresolved after automatic matching — these are sign annotations without a confirmed OGSL mapping.

## ePSD2 and ORACC glossaries

ePSD2 is the primary Sumerian lexicon (1.8 GB of dictionary data). It is imported as an ORACC project (`epsd2`) and provides comprehensive Sumerian entries with attestation counts. ORACC project glossaries (gloss-sux.json, gloss-akk.json, and others) provide lemma data for specific corpora.

The `lexical_lemmas` table merges entries across sources. Duplicate detection uses citation form + guide word + language code as the composite key.

## The normalization bridge

The path from a written form in ATF to a dictionary entry:

```
written_form (e.g., "lu₂-gal")
  → normalized_form (e.g., "lugal")
    → lexical_lemma (cf="lugal", gw="king", pos="N", lang="sux")
      → lexical_senses (gw="king", sense="ruler", ...)
```

This bridge is implemented as the `dictionary/lookup` API endpoint and powers the `interpret_token` MCP tool. Candidates are ranked by attestation frequency.

Subscript handling differs by language. In Sumerian, `du₃` ("to build") is a different word from `du` ("to go") — subscripts carry semantic content. In Akkadian, subscripts are sign disambiguation only — `du₃` normalizes to `du`.

## Language coverage

| Source | Languages covered |
|--------|------------------|
| ePSD2 | Sumerian (sux) |
| ORACC glossaries | sux, akk, akk-x-stdbab, akk-x-oldbab, qpn (proper nouns) |
| OGSL | Sign level only (language-agnostic) |

Elamite and Hittite lexical coverage is minimal.
