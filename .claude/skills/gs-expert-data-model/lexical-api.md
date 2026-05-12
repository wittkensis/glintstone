---
question: "How do I look up lemmas, signs, and senses through Glintstone's core.lexical API — the three-dimensional lexical model in code?"
created: 2026-02-22
modified: 2026-05-11
context: "Migrated from PLAN/lexical-api.md during the 2026-05-11 overhaul. The 3-dimensional model (signs / lemmas / senses) is the canonical post-unified-lexical schema; this file documents the application-layer helpers that traverse it."
status: active
audience: [claude, engineers]
owners: [eric]
related_issues: []
related_skills: [gs-expert-data-model, gs-expert-assyriology]
supersedes: "PLAN/lexical-api.md"
superseded_by: null
---

# Lexical API (core/lexical.py)

Unified lexical resource API for cuneiform dictionaries and sign lists. Wraps the three-dimensional lexical model (signs / lemmas / senses) with lookups, search, and chain-walking helpers.

## Three-dimensional model — recap

```
DIMENSION 1: GLYPHS (graphemic)        lexical_signs
DIMENSION 2: LEMMAS (lexemic)          lexical_lemmas
DIMENSION 3: MEANINGS (semantic)       lexical_senses
```

Connective tissue:

- Signs ↔ Lemmas: `lexical_sign_lemma_associations` (many-to-many)
- Lemmas → Senses: `lexical_senses.lemma_id` (one-to-many, CASCADE)
- Tokens → Lemmas: application-layer lookup (no FK)

## Data sources behind the model

| Source | Lemmas | Senses | Languages |
|---|---|---|---|
| ePSD2 | 15,940 | 71,820 | sux |
| ORACC (8 projects) | 45,495 | 83,671 | sux, akk, elx, xhu, uga, qpn |
| **Total** | **61,435** | **155,491** | 6 |

## Basic lookups

### `lookup_lemmas_by_form(form, language=None, source=None)`

Find lemmas matching a token form.

```python
from core.lexical import lookup_lemmas_by_form

# Sumerian
lemmas = lookup_lemmas_by_form("lugal", language="sux")
# [{
#   "id": 123, "citation_form": "lugal", "guide_word": "king",
#   "pos": "N", "language_code": "sux", "source": "epsd2",
#   "attestation_count": 2006, "sense_count": 20, "sign_count": 1
# }]

# Akkadian, scoped to ORACC SAAo glossary
lemmas = lookup_lemmas_by_form("šarru", language="akk", source="oracc/saao")
```

### `lookup_signs_by_value(value)`

```python
from core.lexical import lookup_signs_by_value

signs = lookup_signs_by_value("LUGAL")
# [{"id": 42, "name": "LUGAL", "unicode": "𒈗", "values": ["lugal", "šarru"]}]
```

### `lookup_senses_for_lemma(lemma_id)`

Returns ordered senses with definitions.

## Chain walking

### `signs_for_lemma(lemma_id)`

Returns signs that can write the lemma — useful for the dictionary UI's "shown as" section.

### `lemmas_for_sign(sign_id, reading_type=None)`

Inverse: which lemmas can a sign represent? Optional `reading_type` filters `logographic | syllabic | determinative`.

### `full_chain(token_form, language=None)`

The big one: given a token form, return everything needed to render a knowledge-bar:

```python
{
  "form": "lugal",
  "lemmas": [...],          # candidates
  "signs": [...],           # graphemic backing
  "senses_by_lemma": {...}, # nested
  "confidence": 0.92        # if a single best match emerged
}
```

## Search

### `search_lemmas(query, language=None, pos=None, limit=20)`

Prefix + fuzzy search across `citation_form` and `guide_word`. Used by the dictionary search bar.

### `search_signs(query, limit=20)`

Search across sign names, values, Unicode codepoints.

## REST endpoints (planned, partial)

| Endpoint | Status |
|---|---|
| `GET /api/signs/:id` | Built |
| `GET /api/lemmas/:id` | Built |
| `GET /api/senses/:id` | Built |
| `GET /api/tokens/:form/lexical` | Built |
| `GET /api/search/lemmas?query=X` | Built |
| `GET /api/search/signs?query=X` | Built |
| `GET /api/dictionary/critical-cache` | Planned (53-entry preload) |
| `GET /api/lemmas/:id/cognates` | Planned |

Caching strategy:

- **Tier 1** (in-memory Map): top 53 entries with `icount ≥ 10,000`
- **Tier 2** (localStorage, 7-day TTL): top 433 with `icount ≥ 1,000`
- **Tier 3** (session): everything else, fetched on demand

## Performance notes

- `lookup_lemmas_by_form` is fast (indexed on `citation_form`).
- `full_chain` runs 3–5 queries; cache aggressively in the UI.
- `lexical_tablet_occurrences` is pre-computed but currently 0 rows (see TODO in `gs-orient-project`); when populated, single-tablet attestation counts become a join, not a count.

## Schema bridges to other layers

- `lemmatizations.lemma_id` — links token-level annotations to canonical lemmas
- `cad_logograms` — bridges Akkadian lemmas to Sumerian sign-form spellings (Sumerogram resolution)
- `sign_word_usage` — per-tablet sign usage with reading-type and lemma link

For the underlying philosophy (sign vs reading vs lemma vs sense), see `gs-expert-assyriology/lexical-model.md`.
