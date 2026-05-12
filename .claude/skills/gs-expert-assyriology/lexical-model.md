---
question: "What's a sign vs reading vs lemma vs sense vs gloss, and how does Glintstone's three-dimensional lexical schema express the relationships?"
created: 2026-05-11
modified: 2026-05-11
context: "Consolidates content from PLAN/Dictionary Taxonomies/ (Lexicography Terminology.md, normalization-bridge.md, assyriological-typography.md) into a single skill file during the 2026-05-11 knowledge architecture overhaul. The terminology is what scholars use; the schema is how Glintstone stores it."
status: active
audience: [claude, engineers, scholars]
owners: [eric]
related_issues: []
related_skills: [gs-expert-assyriology, gs-expert-data-model]
supersedes: ["PLAN/Dictionary Taxonomies/Lexicography Terminology.md", "PLAN/Dictionary Taxonomies/normalization-bridge.md", "PLAN/Dictionary Taxonomies/assyriological-typography.md"]
superseded_by: null
---

# Lexical model — terminology + schema

## Vocabulary scholars use

| Term | Definition | Where it lives |
|---|---|---|
| **Sign** | A specific cuneiform impression. The raw graphemic unit. Polyvalent. | OGSL: 3,367 signs |
| **Reading** | The phonological realization of a sign in context. Logographic readings are lowercase Sumerian; Sumerograms in Akkadian are uppercase. | Transliteration layer (`tokens` + `token_readings`) |
| **Form** | An attested written spelling of a word, including all syllabic combinations. | `glossary_forms`, `lexical_forms` |
| **Normalization (norm)** | The reconstructed inflected word. Critical for Akkadian (syllabic writing); minimal for Sumerian (logographic). | `glossary_norms` (ORACC bridge) |
| **Lemma** | The dictionary citation form. Stable lexical unit abstracted from attestations. | `glossary_entries`, `lexical_lemmas` |
| **Gloss** | A short target-language label (e.g. "king", "house"). Provisional navigation aid, not a full definition. | `glossary_entries.guide_word` |
| **Sense** | A distinct conceptual meaning of a lemma. Polysemy lives here. | `glossary_senses`, `lexical_senses` |
| **Citation form (CF)** | The standardized headword used by CAD, ePSD, ORACC. | `glossary_entries.citation_form` |
| **Guide word (GW)** | The short English gloss. | `glossary_entries.guide_word` |
| **POS** | Part of speech (see [languages.md](languages.md) for ORACC codes). | `glossary_entries.pos` |

## The pipeline (sign → meaning)

```
Sign → Function → Reading → NORMALIZATION → Lemma → Morphology → Sense
```

- **Sign**: physical wedge group, e.g. `KA`.
- **Function**: is this sign acting as a logogram, a syllable, or a determinative?
- **Reading**: what phoneme/word does this sign realize here? `ka` (Sumerian "mouth") vs `pû` (Akkadian, written `KA`).
- **Normalization**: for Akkadian, reconstruct the inflected word from its syllabic spelling. `a-na ra-ma-ni-šu` → `ana ramānišu` "for himself".
- **Lemma**: dictionary entry. `ramānu` "self".
- **Morphology**: stem, TAM, agreement.
- **Sense**: which meaning of `ramānu` applies here?

## Three-dimensional lexical model

```
DIMENSION 1: GLYPHS (graphemic)
├─ Cuneiform signs (𒈗, 𒇽, 𒃲)
├─ Sign values (LUGAL, LU, GU₄)
└─ lexical_signs table

DIMENSION 2: LEMMAS (lexemic)
├─ Citation forms (lugal, šarru, du)
├─ Part of speech (N, V, AJ)
└─ lexical_lemmas table

DIMENSION 3: MEANINGS (semantic)
├─ Sense distinctions
├─ Polysemy
└─ lexical_senses table
```

Connectors between dimensions:

- **Signs ↔ Lemmas**: `lexical_sign_lemma_associations` (many-to-many)
- **Lemmas → Senses**: `lexical_senses.lemma_id` (one-to-many, CASCADE)
- **Tokens → Lemmas**: application-layer lookup (no FK — too lossy and dialect-dependent)

## Glossary schema (canonical tables)

```
glossary_entries
├── entry_id (PK): "project/id" — e.g. "epsd2/e02384"
├── citation_form (CF)
├── guide_word (GW)
├── pos
├── language: ISO 639-3 (akk, sux, xhu, hit, elx, uga)
├── dialect: e.g. "oldbab", "neoass" (Akkadian dialect chronology)
└── icount: corpus occurrences

glossary_forms (attested spellings)
├── entry_id (FK)
├── form
└── count

glossary_norms (Akkadian normalization bridge)
├── entry_id (FK)
├── norm: reconstructed inflected form
└── icount

glossary_senses (polysemy)
├── entry_id (FK)
├── sense_number
├── guide_word, definition
└── semantic_category

glossary_relationships
├── from_entry_id, to_entry_id
└── relationship_type: synonym | antonym | translation | cognate | etymology_source | compound_contains | see_also

semantic_fields (hierarchical)
├── id, name, parent_field_id
└── 12 seeded categories: Kinship, Royalty, Divine, Material Culture, Agriculture, Water, Animals, Numbers, Body Parts, Actions, Abstract, Geography
```

The **unified lexical** family (`lexical_signs`, `lexical_lemmas`, `lexical_senses`, `lexical_sign_lemma_assoc`, `lexical_tablet_occurrences`) is the cross-source model. Older `glossary_*` tables remain for source-specific data.

## Normalization bridge — Akkadian deep dive

Akkadian is written syllabically, so every token needs normalization to identify the word.

ORACC glossary JSON expresses this hierarchically:

```json
{
  "cf": "abāku",          // citation form (lemma)
  "gw": "lead away",      // guide word
  "pos": "V",
  "forms": [
    {"id": "x0014509.0", "n": "a-ba-ku", "icount": "1"}
  ],
  "norms": [
    {
      "id": "x0014509.1",
      "n": "abāku",
      "icount": "1",
      "ipct": "100",
      "forms": [
        {"n": "a-ba-ku", "ref": "x0014509.0", "icount": "1"}
      ]
    }
  ]
}
```

Per-token annotation lives in the ORACC CDL `f` object (see `gs-expert-integrations/sources.md`).

| Language | Normalization role | Why |
|---|---|---|
| Akkadian (all dialects) | **Critical** | Written syllabically; every token must be normalized to identify the word. |
| Sumerian | Minimal | Mostly logographic — one sign, one word. Norms exist but aren't load-bearing. |
| Hittite | N/A | Written with Sumerian/Akkadian logograms; lemmatization targets the logogram. |
| Hurrian, Ugaritic | Moderate | Some syllabic writing; norms exist where ORACC data does. |

## Typography conventions (what scholars see in print)

These conventions show up in ORACC output, ATF input, and our UI:

| Convention | Meaning |
|---|---|
| **lowercase italics** (*šarru*) | Akkadian transcription |
| **lowercase roman** (lugal) | Sumerian reading |
| **UPPERCASE** (LUGAL) | Sumerogram (Sumerian word as logogram in Akkadian/Hittite) |
| **{d}** before name | Divine determinative |
| **{f}** | Female determinative |
| **{ki}** | Place determinative |
| **subscript₂** | Disambiguation (mode 0) or distinct lexeme (mode 1) |
| **superscript** | Determinative in some fonts |
| **square brackets [...]** | Broken/restored |
| **half-brackets ⸢⸣** | Uncertain reading |

The web UI should respect these typographic distinctions when rendering glossed text.

## Cross-language search implications

- **Sumerograms**: `KA` in Akkadian = `pû` "mouth". Query `cad_logograms` to bridge.
- **Cognates**: Akkadian–Hebrew–Aramaic–Arabic etymology chains live in `glossary_relationships.relationship_type='cognate'`.
- **Variant spellings**: same lemma may have many attested forms; group via `glossary_forms`.

For the API surface that exercises this, see `gs-expert-data-model/lexical-api.md`.
