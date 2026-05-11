# Real Data Examples from Database

## Overview

This document presents **3 compelling tablets** selected from the database to illustrate different data scenarios and guide UI design. Each example shows actual data structures with varying completion levels.

---

## Selection Criteria

| Example | P-Number | Characteristics | Why Selected |
|---------|----------|-----------------|--------------|
| 1 | P227657 | Full linguistic data, lexical text | Best-case scenario, rich translations |
| 2 | P247526 | Sumerian language, British Museum | Language variation, different period |
| 3 | P229672 | Joined fragment, Neo-Assyrian | Complex designation, composite linkage |

All examples have:
- ✅ **ATF text** (raw_atf populated)
- ✅ **Translations** (line-level English glosses)
- ⚠️ **Token data** (gdl_json only, token_readings empty)
- ❌ **Lemmatizations** (placeholder rows with 'None' values)

---

## Example 1: P227657 "KTT 188"

### Tablet Metadata

```json
{
  "p_number": "P227657",
  "designation": "KTT 188",
  "museum_no": "NMSR —",
  "excavation_no": "Bi.28/50:135,08",
  "object_type": "tag",
  "period": "Old Babylonian (ca. 1900-1600 BC)",
  "period_normalized": "Old Babylonian",
  "provenience": "Tuttul (mod. Tell Bi'a)",
  "genre": "Administrative",
  "subgenre": "OB Nippur Ura",
  "supergenre": "LEX",
  "language": "Akkadian",
  "primary_publication": "KTT 188",
  "collection": "National Museum of Syria, Raqqa, Syria",
  "oracc_projects": "[\"dcclt\", \"epsd2\"]"
}
```

### Pipeline Status

```json
{
  "physical_complete": 0.0,
  "graphemic_complete": 0.0,
  "reading_complete": 1.0,
  "linguistic_complete": 1.0,
  "semantic_complete": 1.0,
  "has_image": 0,
  "has_atf": 1,
  "has_lemmas": 1,
  "has_translation": 1,
  "has_sign_annotations": 0,
  "quality_score": 0.0
}
```

**Note:** `reading_complete = 1.0` is misleading - only ATF exists, not token readings.

### Text Lines (Sample: Lines 1-10)

| Line # | Surface | ATF | Translation |
|--------|---------|-----|-------------|
| 1 | NULL | `a` | water |
| 2 | NULL | `ninda` | bread |
| 3 | NULL | `kasz` | beer |
| 4 | NULL | `tu7` | soup |
| 5 | NULL | `[tu7] saga` | good quality soup |
| 6 | NULL | `tu7# gu2# gal` | soup made with broad beans |
| 7 | NULL | `tu7 gu2 tur` | lentil soup |
| 8 | NULL | `tu7 gu2 nig2-ar3-ra` | soup made with vetch |
| 9 | NULL | `tu7 SI#!? gu2 ASZ` | soup made with the flour of the ... pulse |
| 10 | NULL | `tu7 ar-za-na` | soup made with barley groats |

### Token Structure (Line 2: "ninda")

```json
{
  "line_id": 282193,
  "line_number": "2",
  "raw_atf": "ninda",
  "tokens": [
    {
      "id": 556573,
      "position": 0,
      "gdl_json": "{\"frag\": \"ninda\"}"
    }
  ],
  "token_readings": [],  // EMPTY
  "lemmatizations": [],  // EMPTY (or placeholder with 'None')
  "translation": "bread"
}
```

### Characteristics

- **Lexical Text:** Bilingual word list (Sumerian → Akkadian/English)
- **Simple Structure:** One word per line
- **Full Translations:** 259 of 265 lines have English glosses
- **Positional Matching:** Perfect 1:1 alignment between lines and translations
- **No Images:** `has_image = 0`
- **No Surface Data:** Surface type is NULL for all lines

### UI Implications

**Can Display:**
- ✅ Line-by-line ATF
- ✅ Parallel translation column
- ✅ Tablet metadata panel
- ✅ Pipeline status (with caveat about token_readings)

**Cannot Display (Yet):**
- ❌ Interactive word clicking (no token_readings)
- ❌ Lemmatization glosses (data not populated)
- ❌ Damage state highlighting (no damage metadata)

**Workaround:**
- Parse `gdl_json` client-side for basic word splitting
- Use ATF damage markers (`#`, `?`, `[]`) for visual indicators

---

## Example 2: P247526 "BM 103142"

### Tablet Metadata

```json
{
  "p_number": "P247526",
  "designation": "BM 103142",
  "museum_no": "BM 103142",
  "object_type": "tablet",
  "period": "Ur III (ca. 2100-2000 BC)",
  "period_normalized": "Ur III",
  "genre": "Administrative",
  "subgenre": "OB Ura",
  "supergenre": "LEX",
  "language": "Sumerian",
  "collection": "British Museum, London, UK",
  "oracc_projects": "[\"dcclt\", \"epsd2\"]"
}
```

### Pipeline Status

```json
{
  "physical_complete": 0.0,
  "graphemic_complete": 0.0,
  "reading_complete": 1.0,
  "linguistic_complete": 1.0,
  "semantic_complete": 1.0,
  "has_image": 0,
  "has_atf": 1,
  "has_lemmas": 1,
  "has_translation": 1
}
```

### Text Lines (Sample: Lines 1-10)

| Line # | Surface | ATF | Translation |
|--------|---------|-----|-------------|
| 1 | NULL | `[...]` | ... ... |
| 2 | NULL | `[...]` | ... ... |
| 3 | NULL | `[udu] ku5-ku5-ra2#` | crippled sheep |
| 4 | NULL | `udu# niga` | fattened sheep |
| 5 | NULL | `udu# niga saga` | good quality fattened sheep |
| 6 | NULL | `udu niga na-gada` | fattened sheep of the cowherd |
| 7 | NULL | `udu nita amasz` | breeder ram |
| 8 | NULL | `udu ur3-ra` | "roof" sheep |
| 9 | NULL | `udu si-im` | trimmed sheep |
| 10 | NULL | `udu masz2-da-ri-a` | sheep of the maszdaria payment |

### Token Structure (Line 5: "udu# niga saga")

```json
{
  "line_id": 282194,
  "line_number": "5",
  "raw_atf": "udu# niga saga",
  "tokens": [
    {
      "id": 556575,
      "position": 0,
      "gdl_json": "{\"frag\": \"udu\"}"
    },
    {
      "id": 556576,
      "position": 1,
      "gdl_json": "{\"frag\": \"niga\"}"
    },
    {
      "id": 556577,
      "position": 2,
      "gdl_json": "{\"frag\": \"saga\"}"
    }
  ],
  "translation": "good quality fattened sheep"
}
```

### Characteristics

- **Sumerian Language:** Different from P227657 (Akkadian)
- **Broken Lines:** Lines 1-2 are fully broken (`[...]`)
- **Compound Terms:** Multi-word lines (e.g., "udu niga saga")
- **Damage Markers:** `#` indicates damaged signs
- **Thematic Content:** Lexical list about sheep and animal products

### UI Implications

**Language-Specific Considerations:**
- Sumerian orthography differs from Akkadian
- Multi-word compounds should be treated as single semantic units
- Damage markers need visual distinction

**Broken Line Handling:**
- Lines 1-2: Display `[...]` with gray/italic styling
- Translation "... ..." indicates fully unknown content
- Don't show token breakdown for broken lines

---

## Example 3: P229672 "K 03254 + K 03779"

### Tablet Metadata

```json
{
  "p_number": "P229672",
  "designation": "K 03254 + K 03779",
  "museum_no": "BM —",
  "object_type": "tablet",
  "period": "Neo-Assyrian (ca. 911-612 BC)",
  "period_normalized": "Neo-Assyrian",
  "provenience": "Nineveh (mod. Kuyunjik)",
  "genre": null,
  "subgenre": "OB Nippur Diri",
  "supergenre": "LEX",
  "language": "Akkadian",
  "collection": "British Museum, London, UK",
  "oracc_projects": "[\"dcclt\", \"epsd2\"]"
}
```

### Composite Linkage

```json
{
  "p_number": "P229672",
  "q_number": "Q000057",
  "composite_designation": null,
  "line_ref": null
}
```

**Note:** This tablet is an exemplar of composite Q000057, but designation is not populated.

### Pipeline Status

```json
{
  "physical_complete": 0.0,
  "graphemic_complete": 0.0,
  "reading_complete": 1.0,
  "linguistic_complete": 1.0,
  "semantic_complete": 1.0,
  "has_image": 0,
  "has_atf": 1,
  "has_lemmas": 1,
  "has_translation": 1
}
```

### Text Lines (Sample: Lines 1-5)

| Line # | Surface | ATF | Translation |
|--------|---------|-----|-------------|
| 1 | NULL | `$ (single ruling between each Akkadian entry)` | (structural marker) |
| 2 | obverse | `$ beginning broken` | (structural marker) |
| 1 | obverse | `# diri ~ [($ blank space $)] = %a [...]-um#` | wide |
| 3 | obverse | `# diri ~ ($ blank space $) = %a sza-ba-bu-um` | to walk |
| 4 | obverse | `# diri ~ ($ blank space $) = %a na-ha-al-lum` | gorge |

### Token Structure (Line 3: Complex ATF)

```json
{
  "line_id": 282196,
  "line_number": "3",
  "surface_type": "obverse",
  "raw_atf": "# diri ~ ($ blank space $) = %a sza-ba-bu-um",
  "tokens": [
    {"id": 556578, "position": 0, "gdl_json": "{\"frag\": \"#\"}"},
    {"id": 556579, "position": 1, "gdl_json": "{\"frag\": \"diri\"}"},
    {"id": 556580, "position": 2, "gdl_json": "{\"frag\": \"~\"}"},
    {"id": 556581, "position": 3, "gdl_json": "{\"frag\": \"(\"}"},
    {"id": 556582, "position": 4, "gdl_json": "{\"frag\": \"$\"}"},
    {"id": 556583, "position": 5, "gdl_json": "{\"frag\": \"blank\"}"},
    {"id": 556584, "position": 6, "gdl_json": "{\"frag\": \"space\"}"},
    {"id": 556585, "position": 7, "gdl_json": "{\"frag\": \"$\"}"},
    {"id": 556586, "position": 8, "gdl_json": "{\"frag\": \")\"}"},
    {"id": 556587, "position": 9, "gdl_json": "{\"frag\": \"sza-ba-bu-um\"}"}
  ],
  "translation": "to walk"
}
```

**Complexity:** ATF includes:
- `#` - Comment/note marker
- `~` - Equivalence operator
- `($ blank space $)` - Structural notation (blank space in original)
- `=` - Equals sign (Sumerian = Akkadian)
- `%a` - Akkadian language switch

### Characteristics

- **Joined Fragment:** Designation "K 03254 + K 03779" indicates physical join
- **Composite Linkage:** Part of Q000057 (ideal composite text)
- **Complex ATF:** Includes structural markers, language switches, editorial notation
- **Surface Data:** Some lines have `surface_type = "obverse"`
- **Structural Lines:** Lines 1-2 are metadata (ruling, broken section markers)
- **Diri Sign List:** Specialized lexical genre (sign values and meanings)

### UI Implications

**Join Display:**
- Parse `+` in designation → "This tablet is a join of 2 fragments: K 03254, K 03779"
- Show join info in header or metadata panel

**Composite Badge:**
- "Exemplar of Q000057" badge with link to composite view
- Query `artifact_composites` table for linkage

**Complex ATF Rendering:**
- Structural markers (`$`) should be styled differently (gray, small font)
- Language switches (`%a`) need visual indicators
- Editorial notation (`#`) needs distinct styling

**Surface Tabs:**
- Some lines have surface data ("obverse"), others don't
- Group lines by surface when available
- Default to single view when surface data missing

---

## Data Retrieval Workflow (Using Example 1)

### Step 1: Fetch Tablet Metadata

**Request:**
```
GET /api/artifacts/P227657
```

**Response:**
```json
{
  "p_number": "P227657",
  "designation": "KTT 188",
  "period": "Old Babylonian (ca. 1900-1600 BC)",
  "language": "Akkadian",
  "genre": "Administrative",
  "pipeline_status": {
    "has_atf": 1,
    "has_translation": 1,
    "reading_complete": 1.0
  }
}
```

---

### Step 2: Fetch ATF Lines

**Request:**
```
GET /api/artifacts/P227657/atf
```

**Response:**
```json
{
  "p_number": "P227657",
  "total_lines": 265,
  "lines": [
    {
      "id": 282192,
      "line_number": "1",
      "surface_type": null,
      "raw_atf": "a",
      "is_ruling": false,
      "is_blank": false
    },
    {
      "id": 282193,
      "line_number": "2",
      "surface_type": null,
      "raw_atf": "ninda",
      "is_ruling": false,
      "is_blank": false
    }
  ]
}
```

---

### Step 3: Fetch Translations

**Request:**
```
GET /api/artifacts/P227657/translation
```

**Response:**
```json
{
  "p_number": "P227657",
  "total": 259,
  "translations": [
    {
      "id": 15275,
      "line_id": null,
      "translation": "water",
      "language": "en",
      "source": "cdli"
    },
    {
      "id": 15276,
      "line_id": null,
      "translation": "bread",
      "language": "en",
      "source": "cdli"
    }
  ]
}
```

**Matching:**
```javascript
// Positional matching
lines.forEach((line, i) => {
  line.translation = translations[i]?.translation || null;
});
```

---

### Step 4: Fetch Tokens (For Interactive Word Clicking)

**Request:**
```
GET /api/artifacts/P227657/lines/282193/tokens
```

**Response:**
```json
{
  "line_id": 282193,
  "line_number": "2",
  "tokens": [
    {
      "id": 556573,
      "position": 0,
      "gdl_json": "{\"frag\": \"ninda\"}"
    }
  ]
}
```

**Parse GDL:**
```javascript
const token = {
  id: 556573,
  position: 0,
  form: "ninda"  // Extract from gdl_json
};
```

---

### Step 5: Fetch Lemmatization (Currently Unavailable)

**Request (Future):**
```
GET /api/artifacts/P227657/tokens/556573/lemmas
```

**Expected Response:**
```json
{
  "token_id": 556573,
  "lemmatizations": [
    {
      "citation_form": "ninda[bread]",
      "guide_word": "bread",
      "pos": "N",
      "norm": "ninda",
      "entry_id": "o0027567"
    }
  ]
}
```

**Current State:** Returns empty or placeholder data.

---

### Step 6: Fetch Dictionary Entry (On Word Click)

**Request:**
```
GET /api/dictionary/o0027567
```

**Response:**
```json
{
  "entry_id": "o0027567",
  "headword": "ninda[bread]N",
  "citation_form": "ninda",
  "guide_word": "bread",
  "pos": "N",
  "language": "sux",
  "icount": 33019,
  "senses": [
    {
      "sense_number": 1,
      "guide_word": "bread",
      "definition": "flatbread made from barley or wheat flour"
    }
  ],
  "forms": [
    {"form": "NINDA", "count": 18234},
    {"form": "ninda", "count": 14785}
  ]
}
```

---

## UI Design Guidance

### Layout Hierarchy

```
┌────────────────────────────────────────────────┐
│ HEADER: Tablet Metadata                       │
│ P227657 | KTT 188 | Old Babylonian | Tuttul   │
│ [Pipeline Status] [Exemplar Badge]            │
├────────────────────────────────────────────────┤
│ SURFACE TABS                                   │
│ [Obverse] [Reverse] [Edge]                     │
├────────────────────────────────────────────────┤
│ LINE-BY-LINE VIEW                              │
│                                                │
│ 1.  a                                          │
│     water                                      │
│                                                │
│ 2.  ninda                                      │
│     bread                                      │
│                                                │
│ 3.  kasz                                       │
│     beer                                       │
│                                                │
├────────────────────────────────────────────────┤
│ SIDEBAR: Dictionary/Glossary                  │
│ (Opens on word click)                          │
└────────────────────────────────────────────────┘
```

### Interaction Flow

1. **Page Load:**
   - Fetch tablet metadata + pipeline status
   - Fetch ATF lines + translations in parallel
   - Match translations positionally
   - Render line-by-line view

2. **Line Click (Expand):**
   - Fetch tokens for clicked line
   - Parse gdl_json client-side
   - Display word-level breakdown
   - Highlight clickable words

3. **Word Click:**
   - Check critical cache for glossary entry
   - If not cached, fetch from API
   - Open dictionary sidebar
   - Show full entry (senses, forms, related words)

### Graceful Degradation

**Full Data Available (Future):**
```
Line 2: ninda
  Token: [ninda] (NINDA)
  Lemma: ninda[bread]N
  Gloss: "bread"
  Translation: bread
```

**Current Reality (Partial Data):**
```
Line 2: ninda
  (Token data pending)
  Translation: bread
```

**User-Friendly Message:**
```
"Word-level analysis is being processed.
View the full ATF line and translation now,
or check back later for detailed lemmatization."
```

---

## Conclusion

These 3 real examples illustrate:
- ✅ **What data exists** (ATF, translations, gdl_json)
- ❌ **What's missing** (token_readings, lemmatizations)
- ✅ **How to match translations** (positional)
- ✅ **How to handle complexity** (joins, composites, structural markers)

Use these examples to:
1. **Design the UI** with actual data structures
2. **Test API endpoints** with real P-numbers
3. **Validate assumptions** about data availability
4. **Build graceful fallbacks** for missing data

**Next Step:** Implement UI using these patterns, with awareness of current limitations and future enhancements.
