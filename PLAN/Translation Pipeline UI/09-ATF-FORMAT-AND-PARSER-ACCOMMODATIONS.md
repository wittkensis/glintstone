# ATF Format: Overview & The Muddy Realities

**Author**: Claude Code
**Date**: 2026-02-21
**Purpose**: Document ATF format variations, parser accommodations, and design decisions for the Glintstone import pipeline

---

## What is ATF?

**ASCII Transliteration Format (ATF)** is the standard format for encoding cuneiform texts in plain text. Developed by the CDLI and ORACC projects, it represents:
- Cuneiform signs in ASCII transliteration
- Tablet structure (surfaces, columns, lines)
- Damage, uncertainty, and editorial notes
- Translations (inline with original text)

**Purpose**: Bridge between physical tablets and digital analysis

---

## ATF Basic Structure

```atf
&P227657 = CDLI Ur III text
#atf: lang sux
@tablet
@obverse
1. 1(disz) gu4 niga
#tr.en: 1 ox, grain-fed,
2. 2(u) udu
#tr.en: 20 rams,
@reverse
1. ki ab-ba-sa6-ga-ta
#tr.en: from Abbasaga,
$ blank space
```

**Key elements**:
- `&P######` - Tablet identifier (CDLI P-number)
- `#atf: lang xxx` - Language code (sux=Sumerian, akk=Akkadian)
- `@surface` - Physical surface markers (obverse, reverse, edge, seal)
- `N.` - Numbered line (1., 2., 3.)
- `#tr.XX:` - Translation (XX=language code: en, de, es, etc.)
- `$` - Editorial note (damage, blank space, ruling)

---

## The Muddy Realities

ATF is a human-curated format spanning decades of scholarship across multiple projects and contributors. This creates **substantial variability**:

### 1. Surface Type Inconsistencies

**Canonical surfaces** (DB schema constraint):
- `obverse`, `reverse`, `left_edge`, `right_edge`, `top_edge`, `bottom_edge`, `seal`

**Actual ATF usage**:
- `@obverse`, `@reverse` ✅
- `@o`, `@r` (abbreviations) - mapped to canonical
- `@left`, `@right`, `@top`, `@bottom` - mapped to edges
- `@edge` (generic) - skipped (not in DB constraint)
- `@column N` - sub-structure, tracked in label but not as surface
- `@tablet`, `@object`, `@envelope`, `@prism`, `@cylinder`, `@brick`, `@cone`, `@bulla` - object types, not surfaces - ignored

**Parser accommodation**: `SURFACE_MAP` dictionary (07_parse_atf.py lines 53-76) maps variants to canonical forms or None (skip)

### 2. Line Numbering Formats

**Standard ATF** supports multiple line numbering conventions:

```atf
1. text                    # Simple integer
1'. text                   # Prime (damaged/interpolated)
1.a. text                  # Sub-line (administrative lists)
1.b1. text                 # Sub-line with counter
o 1. text                  # Surface prefix (old format)
o i 3. text                # Surface + column + line
```

**Current parser** (07_parse_atf.py line 85):
```python
RE_LINE = re.compile(r"^(\d+(?:\'|\.(?:[a-z](?:\d+)?))?\.)\s+(.+)$")
```

**Handles**:
- `1. text` ✅
- `12'. text` ✅ (prime notation)
- `1.a. text` ✅ (sub-line) **FIXED 2026-02-21**
- `1.a1. text` ✅ (sub-line + counter) **FIXED 2026-02-21**

**Parser fix (Feb 2026)**:
- Enhanced regex to capture sub-line notation
- Changed `text_lines.line_number` from INTEGER to TEXT
- Stores full line number strings: "1", "1'", "1.a", "3.b1"

### 3. Composite References

**Format**: `>>Q000000 location`

**Variations**:
```atf
>>Q000057 o 1    # Standard
>>Q057 1         # Non-zero-padded
>>Q57 obverse 1  # Mixed format
```

**Parser accommodation** (line 182):
```python
q_number = "Q" + m.group(1)[1:].zfill(6)  # normalize to Q000000
```

### 4. Translation Markers

**Standard**: `#tr.en: translation text`

**Variations**:
```atf
#tr.en: text                # English (most common)
#tr.de: text                # German
#tr.es: text                # Spanish
#tr.en.liter: text          # Literal translation (NOT parsed correctly)
#note: text                 # NOT a translation (ignored)
```

**Parser** (line 87):
```python
RE_TRANSLATION = re.compile(r"^#tr\.(\w+):\s+(.+)$")
```

**Handles**: `en`, `de`, `es`, `fr` etc. (single lang code)
**Doesn't handle**: `en.liter`, `de.lit` (compound codes) - partial language code captured

### 5. Editorial Notes ($-lines)

**Examples**:
```atf
$ blank space               # Physical blank on tablet
$ single ruling             # Horizontal line incised
$ double ruling             # Two horizontal lines
$ beginning broken          # Top of tablet damaged
$ rest broken               # Continuation damaged
$ reverse blank             # Entire reverse surface empty
$ seal impression           # Cylinder seal rolled on surface
```

**Parser accommodation** (lines 196-208):
- Ruling lines → `is_ruling = 1`
- Broken/blank → `is_blank = 1`
- All $-lines stored in text_lines to preserve sequence

### 6. Damage and Uncertainty Notation

**Sign-level markers** (within transliteration):
```atf
[broken]        # Square brackets = missing/restored
#damaged#       # Hash = damaged but recognizable
?uncertain?     # Question mark = uncertain reading
!collated!      # Exclamation = collation note
x               # Unknown sign
...             # Lacuna (gap)
```

**Current parser**: Stores raw ATF (no sign-level parsing in Step 7-9)
**Future**: Step 10 (token readings) extracts damage from gdl_json

### 7. Language Codes

**Expected**: ISO 639-2/3 codes
```atf
#atf: lang sux     # Sumerian
#atf: lang akk     # Akkadian
#atf: lang elx     # Elamite
```

**Reality**: Also sees:
- `sux-x-emesal` - Sumerian dialect
- `akk-x-oldbab` - Akkadian variant
- `qcu` - Cuneiform Akkadian (alternative code)
- `und` - Undetermined (parser default)

**Parser accommodation** (line 139):
```python
"lang": "und",  # Default if no #atf: lang found
```

### 8. Object Structure vs. Surface Structure

**ATF allows nested object structure**:
```atf
@tablet
  @obverse
  @reverse
@envelope
  @obverse
  @reverse
```

**DB schema**: Flat surface table (p_number, surface_type)
**Parser accommodation**: Tracks only leaf surfaces, ignores object containers

---

## Sub-Line Notation in Administrative Texts

**Why sub-lines exist**: Ancient administrative records often list items in condensed notation:

**ATF example** (P000735):
```atf
3. 2(barig) 1(ban2) sze gur lugal ,
3.a. a-kal dumu lugal-ezen ,
3.b. 2(barig) 1(ban2) ba-na-sa10
4. 1(ban2) sze gur lugal ,
4.a. geme2 dumu-zi-da ,
4.b. 1(ban2) ba-na-sa10
```

**Meaning**: Line 3 is a header, 3.a and 3.b are details. Line 4 is another header, 4.a and 4.b are details.

**Translation markers follow each sub-line**:
```atf
3. header
#tr.en: 2 barig 1 ban of royal grain,
3.a. detail 1
#tr.en: rations for the son of Lugal-ezen,
3.b. detail 2
#tr.en: 2 barig 1 ban was purchased.
```

**Previous parser behavior** (before Feb 2026): Skipped 3.a and 3.b, only created text_line for "3"
**Result**: 3 translations → 1 text_line (artificial many-to-one)

**Current behavior** (after fix): Creates separate text_lines for "3", "3.a", "3.b"
**Result**: 3 translations → 3 text_lines (proper 1:1 mapping)

---

## Accommodations in Current Parser (07_parse_atf.py)

| Issue | Accommodation | Line(s) |
|-------|---------------|---------|
| Surface variants | SURFACE_MAP dictionary | 53-76 |
| Unknown p_numbers | Skip if not in artifacts table | 239-241 |
| Missing lang | Default to 'und' | 139 |
| Non-canonical surfaces | Map to canonical or skip | 168-177 |
| Composite Q-number format | Normalize to Q000000 | 182 |
| Editorial $-lines | Store with is_ruling/is_blank flags | 196-208 |
| Column markers | Ignore @column, track in parent surface | 164-165 |
| Blank lines | Skip entirely | 125-126 |
| Comments | Skip lines starting with # (except #tr., #atf:) | 220-221 |
| Missing line numbers | Auto-increment counter as fallback | 215 |
| Token delimiters | Split on whitespace, remove commas | 96-106 |
| Composite references inline | Strip from line text | 103 |
| **Sub-line notation** | **Enhanced regex + TEXT column** | **85, 213-217** |

---

## Known Gaps

| Gap | Impact | Priority | Status |
|-----|--------|----------|--------|
| **Sub-line notation** | **Was: 9,652 unmatched translations** | **CRITICAL** | **✅ FIXED Feb 2026** |
| Surface prefix format (`o 1.`) | Unknown (not tested) | Medium | Open |
| Column-aware line parsing (`o i 3`) | Column info lost | Low | Open |
| Compound translation codes (`en.liter`) | Language code truncated | Low | Open |
| Sign-level damage parsing | Stored but not parsed | Future | Planned for Step 10 |
| Multi-tablet joins (`+` notation) | Not parsed | Low | Open |
| Seal impressions content | Stored as blank line | Low | Open |

---

## Translation Matching Enhancements (19_match_translation_lines.py)

### Unmatchable Pattern Detection

**Enhanced Feb 2026** to catch embedded ellipsis:

```python
UNMATCHABLE_PATTERNS = [
    # Catches any ellipsis - standalone, leading, embedded, or trailing
    # Examples: "...", "22 ... slaves", "... field", "word ... word"
    (r"(^\.{3,}|^\.{3,}\s+|\s\.{3,}\s|\s\.{3,}$)", "broken"),
    # ... other patterns
]
```

**Impact**: +607 translations correctly flagged as unmatchable

### Sub-Line Pattern Extraction

**Added Pattern 0** to handle sub-line notation in translation text:

```python
# Pattern 0: Sub-line notation "1.a. text", "2.b text"
(
    r"^([oro]|obv?|rev?|obverse|reverse|edge)?\s*(\d+)\.([a-z]\d?)\s*[.:]\s*(.+)$",
    lambda m: {
        "line_number": m.group(2) + "." + m.group(3),  # e.g., "1.a"
        "confidence": 0.7,
    },
),
```

**Impact**: Matches translations with sub-line notation after parser re-import

---

## Expected Improvements (After Full Re-Import)

| Metric | Before Parser Fix | After Parser Fix | Improvement |
|--------|-------------------|------------------|-------------|
| Total text_lines | ~1,400,000 | ~1,410,000-1,415,000 | +10,000-15,000 |
| Translation match rate | 65.8% | ~85-90% | +20-24% |
| Effective match rate | 74.9% | ~95% | +20% |
| Unmatched (truly unmatchable) | 9,652 | ~400 | -9,252 |

**Key Achievement**: Eliminates artificial many-to-one translation→line mappings by properly parsing sub-line structure

---

## References

- CDLI ATF Specification: https://cdli.mpiwg-berlin.mpg.de/articles/cdli-atf-primer
- ORACC ATF Documentation: http://oracc.museum.upenn.edu/doc/help/editinginatf/
- Parser Implementation: `source-data/import-tools/07_parse_atf.py`
- Translation Matching: `source-data/import-tools/19_match_translation_lines.py`

---

## Changelog

**2026-02-21**: Initial documentation
- Added comprehensive ATF format overview
- Documented all parser accommodations
- Recorded sub-line notation fix
- Added translation matching enhancements
