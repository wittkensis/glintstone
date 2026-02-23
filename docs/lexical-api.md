# Lexical API Documentation

Unified lexical resource API for exploring cuneiform dictionaries and sign lists.

## Overview

The lexical API provides functions for:
- Looking up lemmas by token form
- Retrieving senses and signs for lemmas
- Full chain retrieval (Sign → Lemmas → Senses)
- Token integration (form → lexical context)
- Search across lemmas and signs

## Architecture

### Three-Dimensional Lexical Model

```
DIMENSION 1: GLYPHS (Graphemic)
├─ Cuneiform signs (𒈗, 𒇽, 𒃲)
├─ Sign values (LUGAL, LU, GU4)
└─ lexical_signs table

DIMENSION 2: LEMMAS (Lexemic)
├─ Citation forms (lugal, šarru, du)
├─ Part of speech (N, V, AJ)
└─ lexical_lemmas table

DIMENSION 3: MEANINGS (Semantic)
├─ Semantic concepts
├─ Sense distinctions
└─ lexical_senses table
```

### Connective Tissue

- **Signs ↔ Lemmas**: `lexical_sign_lemma_associations` (many-to-many)
- **Lemmas → Senses**: `lexical_senses.lemma_id` (one-to-many, CASCADE)
- **Tokens → Lemmas**: Application-layer lookup (no FK)

## Data Sources

| Source | Lemmas | Senses | Languages | Projects |
|--------|--------|--------|-----------|----------|
| **ePSD2** | 15,940 | 71,820 | Sumerian | epsd2 |
| **ORACC** | 45,495 | 83,671 | sux, akk, elx, xhu, uga, qpn | dcclt, blms, etcsri, dccmt, hbtin, ribo, rinap, saao |
| **Total** | 61,435 | 155,491 | 6 languages | 9 projects |

## Basic Lookup Functions

### lookup_lemmas_by_form(form, language, source)

Find all lemmas matching a token form.

```python
from core.lexical import lookup_lemmas_by_form

# Find Sumerian lemmas
lemmas = lookup_lemmas_by_form("lugal", language="sux")
# Returns: [
#   {
#     "id": 123,
#     "citation_form": "lugal",
#     "guide_word": "king",
#     "pos": "N",
#     "language_code": "sux",
#     "source": "epsd2",
#     "attestation_count": 2006,
#     "sense_count": 20,
#     "sign_count": 1
#   }
# ]

# Find Akkadian lemmas from specific source
lemmas = lookup_lemmas_by_form("šarru", language="akk", source="oracc/saao")
```

**Parameters**:
- `form` (str): Citation form to search for
- `language` (str): Language code (sux, akk, elx, xhu, hit, uga)
- `source` (str, optional): Source filter (epsd2, oracc/dcclt, etc.)

**Returns**: List of lemma dicts with `sense_count` and `sign_count`

---

### get_lemma_senses(lemma_id)

Get all senses for a lemma (polysemy).

```python
from core.lexical import get_lemma_senses

senses = get_lemma_senses(123)
# Returns: [
#   {
#     "id": 456,
#     "lemma_id": 123,
#     "sense_number": 1,
#     "definition_parts": ["king", "ruler", "master"],
#     "translations": {"en": ["king"], "de": ["König"]},
#     "semantic_domain": "governance",
#     "source": "epsd2"
#   },
#   {
#     "sense_number": 2,
#     "definition_parts": ["owner"],
#     ...
#   }
# ]
```

**Parameters**:
- `lemma_id` (int): ID of the lemma

**Returns**: List of sense dicts ordered by `sense_number`

---

### get_signs_for_lemma(lemma_id)

Find all signs that can write a lemma.

```python
from core.lexical import get_signs_for_lemma

signs = get_signs_for_lemma(123)
# Returns: [
#   {
#     "id": 789,
#     "sign_name": "LUGAL",
#     "values": ["lugal", "šarru"],
#     "reading_type": "logographic",
#     "value": "lugal",
#     "frequency": 2006,
#     "source": "epsd2-sl"
#   }
# ]
```

**Parameters**:
- `lemma_id` (int): ID of the lemma

**Returns**: List of sign dicts with association metadata

**Note**: Only ePSD2 lemmas have sign associations. ORACC glossaries don't include sign mapping data.

---

### get_lemmas_for_sign(sign_id)

Find all lemmas that a sign can represent.

```python
from core.lexical import get_lemmas_for_sign

lemmas = get_lemmas_for_sign(789)
# Returns: [
#   {
#     "id": 123,
#     "citation_form": "lugal",
#     "guide_word": "king",
#     "pos": "N",
#     "reading_type": "logographic",
#     "value": "lugal",
#     "frequency": 2006
#   }
# ]
```

**Parameters**:
- `sign_id` (int): ID of the sign

**Returns**: List of lemma dicts with association metadata

---

### get_tablets_for_sign(sign_id, limit)

Get tablets where a sign appears (pre-computed).

```python
from core.lexical import get_tablets_for_sign

tablets = get_tablets_for_sign(789, limit=10)
# Returns: [
#   {"p_number": "P123456", "occurrence_count": 25},
#   {"p_number": "P234567", "occurrence_count": 12}
# ]
```

**Parameters**:
- `sign_id` (int): ID of the sign
- `limit` (int): Maximum tablets to return (default: 100)

**Returns**: List of dicts with `p_number` and `occurrence_count`

**Note**: Currently empty - will be populated by background job in future.

---

### get_tablets_for_lemma(lemma_id, limit)

Get tablets where a lemma appears (pre-computed).

```python
from core.lexical import get_tablets_for_lemma

tablets = get_tablets_for_lemma(123, limit=10)
```

**Parameters**:
- `lemma_id` (int): ID of the lemma
- `limit` (int): Maximum tablets to return (default: 100)

**Returns**: List of dicts with `p_number` and `occurrence_count`

**Note**: Currently empty - will be populated by background job in future.

---

## Full Chain Retrieval Functions

### get_sign_full_chain(sign_id)

Get complete chain: Sign → all Lemmas → all Senses for each Lemma.

```python
from core.lexical import get_sign_full_chain

result = get_sign_full_chain(789)
# Returns: {
#   "sign": {
#     "id": 789,
#     "sign_name": "LUGAL",
#     "values": ["lugal", "šarru"],
#     "source": "epsd2-sl"
#   },
#   "lemmas": [
#     {
#       "id": 123,
#       "citation_form": "lugal",
#       "guide_word": "king",
#       "pos": "N",
#       "reading_type": "logographic",
#       "value": "lugal",
#       "senses": [
#         {
#           "id": 456,
#           "sense_number": 1,
#           "definition_parts": ["king", "ruler"],
#           "translations": {"en": ["king"]}
#         }
#       ]
#     }
#   ],
#   "tablets": [
#     {"p_number": "P123456", "occurrence_count": 25}
#   ],
#   "total_occurrences": 2006
# }
```

**Parameters**:
- `sign_id` (int): ID of the sign

**Returns**: Dict with sign data, lemmas (with nested senses), and tablets

**Use Case**: Sign detail page showing all meanings and usage

---

### get_lemma_full_chain(lemma_id)

Get complete chain: Lemma → all Senses + all Signs.

```python
from core.lexical import get_lemma_full_chain

result = get_lemma_full_chain(123)
# Returns: {
#   "lemma": {
#     "id": 123,
#     "citation_form": "lugal",
#     "guide_word": "king",
#     "pos": "N",
#     "language_code": "sux",
#     "source": "epsd2",
#     "attestation_count": 2006
#   },
#   "senses": [
#     {
#       "id": 456,
#       "sense_number": 1,
#       "definition_parts": ["king", "ruler"],
#       "semantic_domain": "governance"
#     }
#   ],
#   "signs": [
#     {
#       "id": 789,
#       "sign_name": "LUGAL",
#       "value": "lugal",
#       "reading_type": "logographic"
#     }
#   ],
#   "tablets": [
#     {"p_number": "P123456", "occurrence_count": 25}
#   ],
#   "total_occurrences": 2006
# }
```

**Parameters**:
- `lemma_id` (int): ID of the lemma

**Returns**: Dict with lemma data, senses, signs, and tablets

**Use Case**: Lemma detail page showing all meanings and writing systems

---

### get_sense_full_chain(sense_id)

Get complete chain: Sense → Lemma → all Signs.

```python
from core.lexical import get_sense_full_chain

result = get_sense_full_chain(456)
# Returns: {
#   "sense": {
#     "id": 456,
#     "sense_number": 1,
#     "definition_parts": ["king", "ruler"],
#     "semantic_domain": "governance"
#   },
#   "lemma": {
#     "id": 123,
#     "citation_form": "lugal",
#     "guide_word": "king",
#     "pos": "N"
#   },
#   "signs": [
#     {
#       "id": 789,
#       "sign_name": "LUGAL",
#       "value": "lugal"
#     }
#   ]
# }
```

**Parameters**:
- `sense_id` (int): ID of the sense

**Returns**: Dict with sense, parent lemma, and signs

**Use Case**: Sense detail page with writing context

---

## Token Integration Functions

### get_token_lexical_context(token_form, language, source)

Get complete lexical context for a token.

```python
from core.lexical import get_token_lexical_context

result = get_token_lexical_context("lugal", language="sux")
# Returns: {
#   "token_form": "lugal",
#   "language": "sux",
#   "count": 9,
#   "lemmas": [
#     {
#       "id": 123,
#       "citation_form": "lugal",
#       "guide_word": "king",
#       "pos": "N",
#       "source": "epsd2",
#       "senses": [
#         {
#           "sense_number": 1,
#           "definition_parts": ["king", "ruler"]
#         }
#       ],
#       "signs": [
#         {
#           "sign_name": "LUGAL",
#           "value": "lugal"
#         }
#       ]
#     },
#     {
#       "citation_form": "lugal",
#       "guide_word": "king",
#       "source": "oracc/etcsri",
#       ...
#     }
#   ]
# }
```

**Parameters**:
- `token_form` (str): The token's form (e.g., "lugal", "šarru")
- `language` (str): Language code (sux, akk, etc.)
- `source` (str, optional): Source filter

**Returns**: Dict with token form, matching lemmas (with senses and signs), and count

**Use Case**: Token detail popup in tablet viewer showing all possible meanings

**Design**: No foreign key between tokens and lemmas - flexible lookup pattern allows ambiguity and multi-source matches.

---

## Search Functions

### search_lemmas(query, language, pos, source, limit)

Search lemmas by citation form or guide word.

```python
from core.lexical import search_lemmas

# General search
results = search_lemmas("king", limit=10)

# Language-filtered search
results = search_lemmas("king", language="sux", limit=10)

# POS-filtered search
results = search_lemmas("build", pos="V", limit=10)

# Source-filtered search
results = search_lemmas("water", source="epsd2", limit=10)
```

**Parameters**:
- `query` (str): Search string (ILIKE match on citation_form or guide_word)
- `language` (str, optional): Language filter (sux, akk, etc.)
- `pos` (str, optional): POS filter (N, V, AJ, etc.)
- `source` (str, optional): Source filter (epsd2, oracc/dcclt, etc.)
- `limit` (int): Maximum results to return (default: 50)

**Returns**: List of matching lemmas with `sense_count` and `sign_count`

---

### search_signs(query, language, limit)

Search signs by name or values.

```python
from core.lexical import search_signs

# Search by sign name
results = search_signs("DU", limit=10)

# Language-filtered search
results = search_signs("LUGAL", language="sux", limit=10)
```

**Parameters**:
- `query` (str): Search string (ILIKE match on sign_name or exact match in values array)
- `language` (str, optional): Language filter
- `limit` (int): Maximum results to return (default: 50)

**Returns**: List of matching signs with `lemma_count`

---

## Usage Examples

### Example 1: Token Detail Popup in Tablet Viewer

```python
from core.lexical import get_token_lexical_context

# User clicks on token "lugal" in tablet viewer
token_form = "lugal"
language = "sux"

context = get_token_lexical_context(token_form, language)

# Display in UI:
# "lugal" (Sumerian)
# 9 possible meanings from multiple sources:
#
# 1. lugal[king]N (ePSD2)
#    - king, ruler, master
#    - owner
#    Written: 𒈗 (LUGAL)
#
# 2. lugal[king]N (ORACC/ETCSRI)
#    - king
#    - owner
#
# 3. lugal[plant]N (ePSD2)
#    - a plant
```

### Example 2: Sign Detail Page

```python
from core.lexical import search_signs, get_sign_full_chain

# User searches for "LUGAL"
signs = search_signs("LUGAL")
sign_id = signs[0]["id"]

# Get full chain for detail page
result = get_sign_full_chain(sign_id)

# Display:
# Sign: LUGAL (𒈗)
# Values: lugal, šarru
# Source: ePSD2 Sign List
#
# Can represent:
# 1. lugal[king]N (logographic)
#    - king, ruler, master
#    - owner
#
# 2. lugal[plant]N (logographic)
#    - a plant
#
# Occurs in: 2,006 attestations across 892 tablets
```

### Example 3: Dictionary Search

```python
from core.lexical import search_lemmas

# User searches for "king"
results = search_lemmas("king", limit=20)

# Display results grouped by language:
# Sumerian (5 results):
#   - lugal[king]N (ePSD2) - 20 senses
#   - lugal[king]N (ORACC/ETCSRI) - 2 senses
#   - lugal[king]N (ORACC/DCCLT) - 4 senses
#
# Akkadian (8 results):
#   - šarru[king]N (ORACC/RINAP) - 1 sense
#   - šarru[king]N (ORACC/SAAO) - 9 senses
#   - šarrūtu[kingship]N (ORACC/RINAP) - 1 sense
```

### Example 4: Multi-Source Comparison

```python
from core.lexical import lookup_lemmas_by_form

# Compare "lugal" across sources
epsd2_lemmas = lookup_lemmas_by_form("lugal", language="sux", source="epsd2")
oracc_lemmas = lookup_lemmas_by_form("lugal", language="sux", source="oracc/dcclt")

# ePSD2: 20 senses (comprehensive)
# ORACC/DCCLT: 4 senses (lexical texts specific)
```

---

## Performance Considerations

### Pre-Computed Data

The following fields are pre-computed for performance:
- `lemmas.attestation_count` - Total occurrences in corpus
- `lemmas.tablet_count` - Number of distinct tablets
- `sign_lemma_associations.frequency` - Usage frequency
- `lexical_tablet_occurrences` - Tablet associations (to be populated)

**Update strategy**: Background job runs nightly to update counts from token data.

### Indexes

All tables have appropriate indexes:
- GIN indexes on array columns (values, language_codes, definition_parts)
- B-tree indexes on foreign keys (lemma_id, sign_id)
- Composite unique indexes (cf_gw_pos + source)

### Query Optimization

- Full chain queries use nested SELECT with json_agg (single query, no N+1)
- Lookups are case-insensitive (LOWER() or ILIKE)
- Results ordered by pre-computed attestation_count

---

## Source Attribution

All data includes source attribution:
- `source`: Short identifier (epsd2, epsd2-sl, oracc/dcclt)
- `source_citation`: Full academic citation
- `source_url`: Link to original resource

**Example**:
```python
lemma = lookup_lemmas_by_form("lugal", language="sux")[0]
print(lemma["source"])  # "epsd2"
print(lemma["source_citation"])  # "ePSD2: Electronic Pennsylvania Sumerian Dictionary"
print(lemma["source_url"])  # "http://oracc.org/epsd2"
```

---

## Dialect and Period Tracking

Lemmas track dialect and period information:

```python
lemma = lookup_lemmas_by_form("šarru", language="akk", source="oracc/saao")[0]
print(lemma["dialect"])  # "midass" (Middle Assyrian)
print(lemma["period"])  # None (ORACC doesn't always provide period)
print(lemma["region"])  # None
```

**Available dialects**:
- **Sumerian**: emesal, emegir
- **Akkadian**: earakk (Early Akkadian), oldbab (Old Babylonian), midbab (Middle Babylonian), stdbab (Standard Babylonian), neoass (Neo-Assyrian), neobab (Neo-Babylonian), ltebab (Late Babylonian), midass (Middle Assyrian), ltass (Late Assyrian), mbperi (Middle Babylonian Peripheral)

---

## Future Enhancements

### Tablet Occurrences (Background Job)

```python
# Nightly job to populate lexical_tablet_occurrences
def compute_tablet_occurrences():
    """
    Pre-compute tablet associations by joining through token_readings.

    For signs: Match via token_readings.grapheme
    For lemmas: Match via lemmatizations + token_readings.form
    """
    # Implementation TBD
```

### Confidence Scoring

```python
# Future: Add confidence scores for lemma matches
def get_token_lexical_context_with_confidence(token_form, language):
    """
    Return lemmas with confidence scores based on:
    - Exact match vs partial match
    - Frequency in corpus
    - Context (POS patterns, collocations)
    """
    # Implementation TBD
```

### Manual Curation

```python
# Future: Flag preferred lemma for specific tokens
def set_preferred_lemma(token_id, lemma_id):
    """Mark this lemma as preferred interpretation for this token."""
    # Implementation TBD
```

---

## Error Handling

All functions return empty lists/None on no results:

```python
# No lemmas found
lemmas = lookup_lemmas_by_form("xyz123", language="sux")
# Returns: []

# No sign found
result = get_sign_full_chain(999999)
# Returns: None
```

Exceptions are raised for:
- Database connection errors
- Invalid parameters (will raise PostgreSQL errors)

---

## Testing

Run the test suite to verify API functionality:

```bash
python3 source-data/import-tools/17_test_lexical_api.py
```

Test coverage:
- ✅ Lookup lemmas by form (Sumerian, Akkadian)
- ✅ Get senses for lemma
- ✅ Get signs for lemma (ePSD2 only)
- ✅ Get lemmas for sign
- ✅ Full chain retrieval (sign, lemma, sense)
- ✅ Token lexical context
- ✅ Search lemmas (general, filtered)
- ✅ Search signs

---

## Summary

The Lexical API provides a comprehensive interface for exploring cuneiform lexical resources across multiple dimensions:

- **61,435 lemmas** from ePSD2 and 8 ORACC projects
- **155,491 senses** with modular definitions
- **2,093 cuneiform signs** with values and associations
- **6 languages**: Sumerian, Akkadian, Elamite, Hurrian, Ugaritic, Proper Nouns
- **11 Akkadian dialects** tracked

**Key features**:
- Multi-source support (ePSD2, ORACC projects)
- Deduplication via composite keys
- Source attribution for academic credit
- Flexible lookup patterns (no rigid FK constraints)
- Full chain retrieval (Sign → Lemmas → Senses)
- Token integration for tablet viewer

**Design principles**:
- Linguistically coherent (3-dimensional model)
- Performance-optimized (pre-computed counts, GIN indexes)
- Future-ready (background jobs, confidence scoring, manual curation)
