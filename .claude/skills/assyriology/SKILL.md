---
triggers: [akkadian, sumerian, atf, cuneiform, lemma, glossary, sign, cdli, oracc, ebl, assyriology]
description: ANE linguistics, ATF, cuneiform data sources, morphology
---

# Assyriology Domain Expert

Domain expertise for Ancient Near Eastern languages (Akkadian, Sumerian, Elamite, Hittite) and cuneiform text processing.

---

## Languages

| Language | Type | Key Features | Tokenization Mode |
|----------|------|--------------|-------------------|
| **Akkadian** | Semitic | Root-stem morphology, triconsonantal roots, dialects (OB, MB, SB, NA, NB) | Mode 0 (strip subscripts) |
| **Sumerian** | Isolate | SOV agglutinative, ergative-absolutive, slot-based verb chains | Mode 1 (preserve subscripts) |
| **Elamite** | Isolate | Agglutinative | Mode 0 |
| **Hittite** | Indo-European | Heavy logographic writing (graphemic ≠ linguistic layer) | Mode 0 |

**Tokenization**: Mode 0 strips subscripts (du₃ → du), Mode 1 preserves (du ≠ du₃ ≠ du₇)

---

## ATF Standards

### CDLI ATF (Basic)
```
&P123456               # Tablet ID
#atf: lang akk         # Language declaration
@obverse               # Surface marker
1. {d}30-EN            # Line: determinative + signs
$ ruling               # Physical damage/ruling
#tr.en: Sin is lord   # Translation
>>Q000123 1            # Composite text reference
```

**Line protocols**: `N.` (line number), `N'.` (uncertain line), `$` (state/damage), `#tr.XX:` (translation), `#note:` (comment), `>>Q######` (composite ref)

**Surface markers**: `@obverse`, `@reverse`, `@left`, `@right`, `@top`, `@bottom`, `@seal`, `@column N`

**Damage**: `[...]` (broken), `broken_text` (uncertain)

### eBL ATF (Extended)
Full EBNF grammar with additional notation:

| Notation | Meaning | Example |
|----------|---------|---------|
| `{d}`, `{f}`, `{ki}` | Determinatives (divine, female, place) | `{d}UTU` = Shamash |
| `\|A.B\|` | Compound sign | `\|A.AN\|` |
| `@g`, `@t`, `@s` | Sign modifiers (gunu, tenu, sheshig) | `A@g` |
| `⸢...⸣` | Uncertain reading | `⸢GIŠ⸣` |
| `[...]` | Broken/missing | `[x x]` |
| `◦` | No longer visible | `◦GIŠ◦` |
| `%akk`, `%sux`, `%n` | Language/normalization shift | `%n ša-ar-ru-um` |

**Reference**: eBL grammar at `source-data/sources/eBL/metadata/ebl-api/docs/ebl-atf.md`

### Surface Mapping (ATF → DB)

| ATF Marker | DB Canonical | ATF Aliases |
|------------|--------------|-------------|
| `@obverse` | `obverse` | `@o` |
| `@reverse` | `reverse` | `@r` |
| `@left` | `left_edge` | `@l.e.` |
| `@right` | `right_edge` | `@r.e.` |
| `@top` | `top_edge` | `@t.e.` |
| `@bottom` | `bottom_edge` | `@b.e.` |
| `@seal` | `seal` | - |

**Column structure**: `@column N` maps to `text_lines.column_number`, not `surfaces` table

---

## Data Sources

| Source | Content | Format | Key Fields |
|--------|---------|--------|------------|
| **CDLI** | 353k artifacts, ATF corpus | `cdli_cat.csv`, `cdliatf_unblocked.atf` | `p_number`, `language` (semicolon-delimited) |
| **ORACC** | Glossaries, lemmatized corpus | `gloss-{lang}.json`, `corpusjson/P######.json` | CBD 2.0: `cf[gw]POS`, `entry_id="project/id"` |
| **OGSL** | 3,367 cuneiform signs | `ogsl-sl.json` | `sign_id`, `values[]`, types: simple\|modified\|compound |
| **eBL** | Babylonian literature | Word schema JSON | `lemma[]`, `logograms[]`, `derivedFrom`, `WordOrigin` enum |
| **CAD** | Chicago Assyrian Dictionary | Extracted from scans | `cad_meanings` (polysemy), `cad_logograms` (Sumerograms) |

### ORACC Projects
**Active**: dcclt, epsd2, rinap, saao, blms, etcsri, cams. **Entry ID**: `"project/id"` (e.g., `"epsd2/e02384"`)

### OGSL Sign Types
- **Simple**: Basic sign (e.g., `A`, `KA`)
- **Modified**: With modifier (e.g., `A@g`, `KA@t`)
- **Compound**: Multi-sign grapheme (e.g., `|A.AN|`, `|A.EDIN.LAL|`)

**Value types**: logographic (word), syllabic (phoneme), determinative (classifier)

---

## Schema Architecture

### 5-Layer Model
1. **Physical**: `artifacts` → `surfaces` → `surface_images`
2. **Graphemic**: `signs`, `sign_values`, `sign_annotations` (computer vision)
3. **Reading**: `text_lines` → `tokens` → `token_readings` (competing transliterations)
4. **Linguistic**: `lemmatizations` → `morphology` (root, stem, tense, etc.)
5. **Semantic**: `glossary_entries` → `glossary_senses` → `glossary_relationships` → `semantic_fields`

**Key principle**: Separate physical object, graphemic signs, phonetic reading, linguistic analysis, semantic meaning into distinct layers with provenance tracking at each layer.

### Provenance Pattern
Every annotation carries `annotation_run_id` linking to:
- Source name (cdli-atf, oracc-corpus, babylemmatizer-v2.1, manual-scholar-xyz)
- Tool version + configuration
- Timestamp (started_at, completed_at)
- Quality metrics (confidence score)

**Competing interpretations**: Store multiple rows per token with different `annotation_run_id` values

### Glossary Schema
```
glossary_entries
├── entry_id (PK): "project/id"
├── citation_form: CF from CBD
├── guide_word: GW (English meaning)
├── pos: Part of speech code
├── language: ISO 639-3 (akk, sux, xhu, hit)
└── icount: Corpus occurrence count

glossary_forms (variants)
├── entry_id (FK)
├── form: Alternative spelling
└── count: Attestation frequency

glossary_senses (polysemy)
├── entry_id (FK)
├── sense_number: 1, 2, 3...
├── guide_word, definition
└── semantic_category

glossary_relationships
├── from_entry_id, to_entry_id
├── relationship_type: synonym|antonym|translation|cognate|etymology_source|compound_contains|see_also
└── confidence

semantic_fields (hierarchical)
├── id, name, parent_field_id
└── Categories: Kinship, Royalty, Divine, Material Culture, Agriculture, etc.
```

**Cross-language links**: `cad_logograms` connects Akkadian entries to Sumerian logographic spellings

---

## Morphology & Lemmatization

### BabyLemmatizer
Neural sequence-to-sequence (OpenNMT) performing POS-tagging + lemmatization

**Tokenization modes**:
- **Mode 0** (Akkadian, Elamite, Hittite, Hurrian): Strip subscripts, logo-syllabic
- **Mode 1** (Sumerian): Preserve subscripts (lexical contrast: du "go" ≠ du₃ "build")
- **Mode 2**: Character sequences (Greek, Latin)

**Output**: CoNLL-U format (`ID | FORM | LEMMA | UPOS | XPOS | FEATS | ...`)

**Accuracy**: 94-96% in-vocabulary, 68-84% out-of-vocabulary

### ORACC Lemmatization Format
```
inst="%sux:za-ba4-lu2=[sorrow//sorrow]N"
     ^^^^  ^^^^^^^^^  ^^^^^^  ^^^^^^ ^
     lang    form        CF     GW  POS
```

**Ref field**: `P123456.3.1` = textid.line.word (1-indexed)

**Morph field**: Optional morphology string (language-specific encoding)

### Akkadian Morphology
**Root-Stem-TAM system**:
- **Root**: Triconsonantal (e.g., b-n-y "build", š-a-l "ask")
- **Stem**: G (basic), D (intensive), Š (causative), N (passive), Gt/Gtn/Gtt (iterative)
- **TAM**: Tense-Aspect-Mood (preterite, durative, perfect, stative, precative, etc.)
- **Agreement**: Person (1/2/3), gender (m/f), number (sg/du/pl)

**Example**: *ibnī* = i-bn-ī (3-build-past.sg) = "he built" (G-stem preterite)

### Sumerian Morphology
**Slot-based verb chain**:
```
[modal]-[conjugation]-[ventive]-[dimensional]-[person]-STEM-[ergative]-[pronominal]
```

**Example**: *mu-n-na-ab-sum* = "he gave it to him"
- mu- (ventive)
- n- (3sg.IO dative)
- na- (3sg.human.IO allative)
- b- (3sg.neuter.DO)
- sum (give)

**Scholarly debate**: Jagersma vs Zolyomi vs Edzard frameworks differ on prefix slot analysis. ORACC follows Jagersma.

---

## ORACC POS Codes

| Code | Meaning | Code | Meaning |
|------|---------|------|---------|
| **N** | Noun | **V/i** | Intransitive verb |
| **V/t** | Transitive verb | **AJ** | Adjective |
| **DN** | Divine name | **PN** | Personal name |
| **GN** | Geographic name | **NU** | Number |

**Full list**: See http://oracc.org/doc/help/editinginatf/primer/lexicaldata/

**Extended codes**: SN (settlement), WN (watercourse), ON (object), RN (royal name), MN (month), YN (year), QN (qualification)

---

## Search Patterns

### Morphological Awareness
**Problem**: User searches "build" → should find *ibnī*, *ibtanī*, *ubnī*, *nibnī* (all b-n-y root)

**Solution**:
1. Lemmatization links surface forms → citation form (banûm)
2. Search expands to all attested forms via `glossary_forms` table
3. Morphology table enables root-based search

### Variant Handling
**Graphemic variants**: KU vs QU (same phoneme, different periods)
**Orthographic variants**: Plene vs defective (ma-li-i vs ma-li)

**Implementation**: `normalized_headword` field + `glossary_forms` with frequency counts

### Cross-Language Search
**Sumerograms**: KA in Akkadian text = pû "mouth"

**Implementation**:
- `cad_logograms` table: links Akkadian entries to Sumerian sign forms
- `sign_word_usage` table: links `signs` → `glossary_entries` with usage context

**Example query**: "Find all uses of KA sign as logogram" → returns both Sumerian *ka* "mouth" and Akkadian *pû* written KA

### Semantic Field Navigation
**Hierarchical**: `semantic_fields.parent_field_id` enables tree traversal

**12 seeded categories**:
1. Kinship & Family
2. Royalty & Authority
3. Divine & Religious
4. Material Culture
5. Agriculture & Food
6. Water & Liquids
7. Animals & Nature
8. Numbers & Mathematics
9. Body Parts
10. Actions & Verbs
11. Abstract Concepts
12. Geographic Features

**Query pattern**: "Find all kinship terms" → SELECT entries WHERE semantic_field_id IN (descendants of Kinship node)

---

## Integration with Other Skills

### When to Combine

**assyriology + code-architect**:
- Implementing ATF parsers, dictionary APIs, search endpoints
- **Division**: Assyriology provides domain rules (tokenization modes, ORACC format); code-architect provides REST patterns, error handling, testing

**assyriology + frontend-design**:
- Designing ATF viewers, sign renderers, glossary UIs
- **Division**: Assyriology provides notation rules (⸢...⸣, |A.B|, determinative styling); frontend-design provides Kenilworth tokens, typography, component patterns

**assyriology alone**:
- Pure domain questions (stem forms, data source structures, ATF syntax, linguistic analysis)

---

## References

**Local Schema Files**:
- Full schema: `data-model/v2/glintstone-v2-schema.yaml`
- Import pipeline: `data-model/v2/import-pipeline.yaml`
- ML integration: `data-model/v2/ml-integration.md`

**Source Schemas**:
- ORACC glossary: `data-model/source-schemas/oracc-glossary.yaml`
- OGSL signs: `data-model/source-schemas/ogsl-signlist.yaml`
- CDLI ATF: `data-model/source-schemas/cdli-atf.yaml`

**External Standards**:
- CDLI ATF: http://cdli.ox.ac.uk/wiki/doku.php?id=atf_structure
- ORACC CBD 2.0: http://oracc.org/doc/help/editinginatf/cbd/
- ORACC documentation: http://oracc.org/doc/
- OGSL: http://oracc.org/ogsl/

**eBL Grammar**: `source-data/sources/eBL/metadata/ebl-api/docs/ebl-atf.md` (full EBNF)
