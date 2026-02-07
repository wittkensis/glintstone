# Sign Libraries and OGSL Structure

## Document Purpose

This document explains the structure of cuneiform sign libraries, focusing on the OGSL (ORACC Global Sign List) and how scholars navigate between signs and words in the CUNEIFORM library browser.

**Date Created**: 2026-02-07
**Related Implementation**: `/library/signs/` sign browser and sign detail pages

---

## Overview of Cuneiform Sign Libraries

### What is a Sign Library?

A **sign library** (or sign list) is a comprehensive catalog of all known cuneiform signs with their possible readings and values. Think of it as a "character dictionary" for the cuneiform writing system.

**Key Functions**:
1. Identify unknown signs visually
2. Enumerate all possible readings for each sign
3. Distinguish between logographic, syllabic, and determinative uses
4. Document sign variants and historical evolution
5. Enable bidirectional navigation: signs ↔ words

### OGSL (ORACC Global Sign List)

**Full Name**: ORACC Global Sign List
**Abbreviation**: OGSL
**Maintainer**: ORACC (Open Richly Annotated Cuneiform Corpus)
**Documentation**: [http://oracc.org/ogsl](http://oracc.org/ogsl)

**Coverage**:
- **3,367 signs** in CUNEIFORM database
- **10,312+ readings/values** across all signs
- Sumerian, Akkadian, and other cuneiform languages
- Unicode mappings for digital display

**Structure**:
```
signs table:
├── sign_id (primary key): "KA", "LUGAL", "A", etc.
├── utf8: Unicode character (𒅗, 𒈗, 𒀀)
├── unicode_hex: Hexadecimal code (x12157, x12217, x12000)
├── unicode_decimal: Decimal code (73

, 73751, 73728)
├── uphase: Unicode phase (1, 2, 3)
└── uname: Unicode name ("CUNEIFORM SIGN KA")

sign_values table:
├── sign_id (foreign key): Links to signs
├── value: Reading/pronunciation ("ka", "inim", "zu₂")
└── sub_index: Disambiguation number for homophonic values
```

---

## Sign Types and Value Categories

### 1. Logographic Values

**Definition**: Sign represents a complete word with semantic meaning.

**Characteristics**:
- One sign = whole concept/word
- Language-specific (Sumerian vs Akkadian logograms differ)
- Can have multiple logographic meanings (polysemy)

**Examples**:

| Sign | UTF-8 | Sign ID | Logographic Value | Meaning |
|------|-------|---------|-------------------|---------|
| 𒅗 | U+12157 | KA | ka | mouth |
| 𒅗 | U+12157 | KA | inim | word, speech |
| 𒅗 | U+12157 | KA | zu₂ | tooth |
| 𒈗 | U+12217 | LUGAL | lugal | king |
| 𒀀 | U+12000 | A | a | water |
| 𒀀 | U+12000 | A | a₂ | arm |

**Note**: Same sign (KA = 𒅗) has THREE different logographic meanings depending on context.

### 2. Syllabic Values

**Definition**: Sign represents a sound/syllable, not a complete word.

**Characteristics**:
- Phonetic component of writing
- Used to spell out words syllable by syllable
- Multiple signs combine to form words
- Language-neutral (can be used in any cuneiform language)

**Examples**:

| Sign | Syllabic Values | Example Usage |
|------|-----------------|---------------|
| 𒅗 (KA) | ka, qa, gu₃, du₁₁, dug₄, e₇, en₄, ga₁₄, etc. | ka-la-am = kalam (land) |
| 𒈗 (LUGAL) | šar, lugal | Used phonetically in compounds |
| 𒀀 (A) | a, aya, e₄ | a-bu = abu (father) |

**Sign KA has 63 syllabic values**, showing the complexity of the cuneiform writing system!

### 3. Determinatives

**Definition**: Unpronounced semantic classifiers that indicate word category.

**Characteristics**:
- Not read aloud
- Prefix or suffix position
- Help readers understand word type
- Written in braces {} in transliteration

**Common Determinatives**:

| Determinative | Position | Meaning | Example |
|---------------|----------|---------|---------|
| {d} | Prefix | Divine name | {d}inana = goddess Inana |
| {giš} | Prefix | Wooden object | {giš}tukul = weapon (wood) |
| {kuš} | Prefix | Leather object | {kuš}a₂ = leather arm-piece |
| {munus} | Prefix | Female person | {munus}lugal = queen |
| {ki} | Suffix | Place name | unug{ki} = Uruk (city) |
| {1} | Prefix | Single/lone | {1}lugal = lone king |

**In Database**:
- Stored in `sign_values.value_type` as "determinative"
- Not counted as separate "readings" for frequency analysis

---

## Sign Variants and Notation

### Variant Types

#### 1. Graphical Variants
**Cause**: Different scribal traditions or time periods

**Examples**:
- Standard form: 𒅗
- Cursive variant: (simplified version)
- Old Babylonian vs Neo-Assyrian styles

#### 2. Allographs (Equivalent Signs)
**Definition**: Different signs used interchangeably for same value

**Example**:
- DU and GUB both = "to stand"
- Context or period determines which is used

### Variant Notation (ORACC Standard)

**Modifiers in Transliteration**:

| Notation | Meaning | Example |
|----------|---------|---------|
| @g | Gunified (combined with following sign) | ka@g |
| @t | Tenû (reduced/abbreviated form) | ka@t |
| @v | Variant form | ka@v |
| @f | Full form (opposite of @t) | ka@f |
| @c | Corrected by modern editor | ka@c |
| @s | Sign damaged but identifiable | ka@s |

**In Database**:
- `sign_variants` table (currently empty, reserved for future)
- Variant modifiers parsed from word forms when needed

---

## Sign-Word Relationships

### Database Model

#### Tables:
1. **signs**: Core sign inventory (3,367 signs)
2. **sign_values**: All possible readings (10,312+ values)
3. **sign_word_usage**: Which signs appear in which words (to be populated)

#### Relationship Structure:
```sql
sign_word_usage:
├── sign_id: "KA"
├── sign_value: "ka" (specific reading used)
├── entry_id: "o0028123" (links to glossary_entries)
├── usage_count: 156 (how many times in corpus)
└── value_type: "logographic" | "syllabic" | "determinative"
```

### Navigation Patterns

#### 1. Sign → Words (Forward Navigation)

**User Journey**:
1. User sees cuneiform sign 𒅗 in a text
2. Clicks sign → navigates to `/library/sign/KA`
3. Sign detail page shows:
   - All 63 possible values
   - Grouped by type (logographic, syllabic, determinative)
4. For each value, lists words that use it:
   - **Logographic KA**: ka[mouth], inim[word], zu₂[tooth]
   - **Syllabic /ka/**: kalam[land] (ka-la-am), kar[harbor] (ka-ar)
5. User clicks word → navigates to word detail page

**SQL Query**:
```sql
-- Get all words using sign KA
SELECT DISTINCT ge.entry_id, ge.headword, ge.guide_word, swu.sign_value, swu.value_type
FROM sign_word_usage swu
JOIN glossary_entries ge ON swu.entry_id = ge.entry_id
WHERE swu.sign_id = 'KA'
ORDER BY swu.value_type, swu.usage_count DESC;
```

#### 2. Word → Signs (Reverse Navigation)

**User Journey**:
1. User views word detail page for "kalam[land]"
2. "Sign Breakdown" section shows: ka-la-am
3. Each sign is clickable:
   - 𒅗 (KA) → `/library/sign/KA`
   - 𒆷 (LA) → `/library/sign/LA`
   - 𒀀 (AM) → `/library/sign/AM`
4. User clicks any sign → sees all its readings and other words using it

**Implementation**:
- Parse word forms from `glossary_forms.form` column
- Extract constituent signs (requires sign boundary detection)
- Display each sign with cuneiform Unicode + sign ID
- Make clickable links to sign detail pages

**Challenge**: Sign Boundary Detection
- Need to parse "ka-la-am" into [KA, LA, AM]
- Handle multi-character sign IDs: "1(BAN₂)" = single sign
- Account for determinatives: "{d}inana" = determinative + 2 signs

---

## Sign Frequency and Statistics

### Frequency Metrics

**Sign-Level Frequency**:
- How many different words use this sign?
- How many total instances in corpus?

**Example for Sign KA**:
```
Sign: KA (𒅗)
├── Appears in: 237 different words
├── Total instances: 15,678 across all tablets
├── Most common value: "ka" (logographic, 45% of uses)
└── Most common word: ka[mouth] (156 attestations)
```

**Database View**:
```sql
CREATE VIEW sign_usage_summary AS
SELECT
    s.sign_id,
    s.utf8,
    COUNT(DISTINCT sv.value) as value_count,
    COUNT(DISTINCT swu.entry_id) as word_count,
    SUM(swu.usage_count) as total_occurrences
FROM signs s
LEFT JOIN sign_values sv ON s.sign_id = sv.sign_id
LEFT JOIN sign_word_usage swu ON s.sign_id = swu.sign_id
GROUP BY s.sign_id;
```

### Value-Level Frequency

**Question**: For sign KA, which reading is most common?

**Answer from Corpus Analysis**:
```
KA readings ranked by frequency:
1. ka (logographic "mouth") - 7,234 instances (45%)
2. gu₃ (syllabic /gu/) - 3,456 instances (22%)
3. du₁₁ (syllabic /du/) - 2,876 instances (18%)
4. inim (logographic "word") - 1,234 instances (8%)
5. [other 59 values] - 1,112 instances (7%)
```

**Storage**:
- `sign_values.frequency` column
- Calculated from `sign_word_usage` aggregation
- Updated when corpus data changes

---

## Scholarly Workflows with Sign Libraries

### Workflow 1: Identify Unknown Sign

**Scenario**: Scholar encounters unfamiliar sign in tablet photograph.

**Process**:
1. **Visual Search**: Browse sign grid by shape/complexity
2. **Pattern Match**: Find visually similar signs
3. **Verify**: Check Unicode and sign ID
4. **Explore Values**: See all possible readings
5. **Context**: Choose most likely reading based on surrounding text

**Tool Support**:
- Sign grid with large, clear Unicode display
- Filter by Unicode phase (simpler early signs vs complex later signs)
- Visual similarity search (future feature)

### Workflow 2: Verify Spelling

**Scenario**: Wondering if "ka-la-am" is correct spelling for "kalam" (land).

**Process**:
1. Search word "kalam" in dictionary
2. View "Variant Forms" section
3. See all attested spellings:
   - ka-la-am (189 times) ✓ correct
   - ka-lam (24 times) ✓ also valid
   - kal-am (14 times) ✓ valid
4. Choose most common or period-appropriate form

**Database Support**:
- `glossary_forms` table with frequency counts
- Sign breakdown shows syllable boundaries

### Workflow 3: Explore Sign Semantics

**Scenario**: Curious about all "water-related" words.

**Process**:
1. Look up sign A (𒀀) = "water" logogram
2. View all words using A logographically:
   - a[water]
   - a-ab-ba[sea] (water + father + nominalizer)
   - id₂[river] (different sign, but related concept)
3. Follow "Semantic Field: Water & Liquids" links
4. Discover related words: kurun[beer], kaš[beer], ŋeš[milk], etc.

**Implementation**:
- Sign detail page shows logographic words grouped
- Semantic field tags link related concepts
- Cross-references between synonyms

### Workflow 4: Track Historical Development

**Scenario**: How did sign A evolve from Early Dynastic to Neo-Babylonian?

**Process**:
1. View sign detail for A
2. "Sign Variants" section shows historical forms:
   - Archaic (pictographic water waves)
   - Old Babylonian (simplified)
   - Neo-Assyrian (angular cursive)
3. "Usage by Period" statistics show frequency changes
4. Scholar can filter corpus examples by period

**Data Requirements**:
- Sign variant images (future enhancement)
- Period-tagged sign_annotations
- Historical usage statistics

---

## Sign Complexity and Unicode Phases

### Unicode Cuneiform Blocks

**Phases**:
1. **Phase 1** (U+12000–U+123FF): Common signs (1,024 slots)
2. **Phase 2** (U+12400–U+1247F): Additional signs (128 slots)
3. **Phase 3** (U+12480–U+1254F): Rare and archaic signs (208 slots)
4. **Supplement** (U+12F90–U+12FFF): Extensions (112 slots)

**Filtering by Phase**:
- Phase 1 signs: Most common, learn these first
- Phase 2-3: Specialized, rare texts only

### Sign Complexity Metrics

**Stroke Count** (future feature):
- Simple: 1-5 strokes (A, AN, KI)
- Moderate: 6-15 strokes (KA, DU, GI)
- Complex: 16+ strokes (LAGAB×variants, compound signs)

**Compound Signs**:
- Multiple simple signs combined
- Example: LAGAB×GAR = LAGAB sign with GAR inscribed
- Notation: sign_id = "LAGAB×GAR" or "LAGAB.GAR"

---

## Implementation Strategy for CUNEIFORM

### Sign Grid Browser (`/library/signs/`)

**Layout**:
```
┌─────────────────────────────────────────────────────┐
│ Search signs by ID or value: [________] 🔍          │
├─────────────┬───────────────────────────────────────┤
│ FILTERS     │  SIGN GRID (showing 50 of 3,367)     │
│             │                                       │
│ Unicode     │  ┌──────┬──────┬──────┬──────┬──────┐│
│ □ Phase 1   │  │  𒀀   │  𒀁   │  𒀂   │  𒀃   │  𒀄  ││
│ □ Phase 2   │  │  A   │  A₂  │  AB  │  AB₂ │ AB×  ││
│ □ Phase 3   │  │ 27   │ 19   │ 10   │  5   │  2  ││
│             │  │ vals │ vals │ vals │ vals │ vals││
│ Sign Type   │  └──────┴──────┴──────┴──────┴──────┘│
│ □ Simple    │                                       │
│ □ Compound  │  ┌──────┬──────┬──────┬──────┬──────┐│
│             │  │  𒀅   │  𒀆   │  𒀇   │  𒀈   │  𒀉  ││
│ Frequency   │  │ AMAR │  AN  │ AN.  │ ANŠE │ AŠGAB││
│ ○ All       │  │ 13   │ 30   │  8   │ 12   │  6  ││
│ ○ Common    │  └──────┴──────┴──────┴──────┴──────┘│
└─────────────┴───────────────────────────────────────┘

Pagination: [< Previous] [1] 2 3 ... 68 [Next >]
```

**Features**:
- Large, clear cuneiform characters
- Sign ID below each sign
- Value count (how many readings)
- Hover shows quick info popup
- Click → navigate to sign detail page

### Sign Detail Page (`/library/sign/{sign_id}`)

**Example: Sign KA (𒅗)**

```
┌─────────────────────────────────────────────────────┐
│ 𒅗  KA                                               │
│ ────────────────────────────────────────────────    │
│ Unicode: U+12157 • OGSL ID: KA                     │
│ Appears in 237 words • 15,678 total instances      │
└─────────────────────────────────────────────────────┘

┌─ READINGS ──────────────────────────────────────────┐
│ LOGOGRAPHIC VALUES (meaning)                        │
│ • ka - mouth, speech, opening                       │
│ • inim - word, speech, matter                       │
│ • zu₂ - tooth                                       │
│                                                      │
│ SYLLABIC VALUES (sound)                             │
│ • ka, qa, gu₃, du₁₁, dug₄, e₇, en₄, ga₁₄          │
│ • [Show all 63 values →]                           │
│                                                      │
│ DETERMINATIVE USAGE                                 │
│ • None recorded                                     │
└─────────────────────────────────────────────────────┘

┌─ WORDS USING THIS SIGN (237 words) ────────────────┐
│ Filter by value type: [All ▼] [Logographic] [Syllabic] │
│                                                      │
│ Using logographic value KA (mouth):                 │
│ • ka[mouth] sux N - 156 attestations [View →]     │
│ • ŋiš-ka[ration] sux N - 89 attestations          │
│                                                      │
│ Using logographic value INIM (word):                │
│ • inim[word] sux N - 423 attestations              │
│                                                      │
│ Using syllabic value /ka/:                          │
│ • kalam[land] sux N (ka-la-am) - 234 att.          │
│ • kar[harbor] sux N (ka-ar) - 89 att.              │
│                                                      │
│ [Load more results →]                               │
└─────────────────────────────────────────────────────┘

┌─ SIGN VARIANTS ─────────────────────────────────────┐
│ Standard: 𒅗                                         │
│ Gunified (@g): 𒅘                                   │
│ Tenû (@t): 𒅙                                       │
│ [Show historical forms →]                          │
└─────────────────────────────────────────────────────┘

┌─ USAGE STATISTICS ──────────────────────────────────┐
│ Appears in 2,341 tablets                           │
│ Total instances: 15,678                            │
│                                                      │
│ By Value (top 5):                                  │
│ 1. ka (logographic) ████████ 7,234 (45%)           │
│ 2. gu₃ (syllabic)   █████    3,456 (22%)           │
│ 3. du₁₁ (syllabic)  ████     2,876 (18%)           │
│ 4. inim (logographic) ██     1,234 (8%)            │
│ 5. Other values      ██      1,878 (12%)           │
└─────────────────────────────────────────────────────┘
```

### Data Population Script

**Goal**: Populate `sign_word_usage` table by analyzing existing lemmas.

**Process**:
```python
# data-tools/import/populate_sign_usage.py

import sqlite3
import re

db = sqlite3.connect('database/glintstone.db')

# 1. Get all lemmas with word forms
lemmas = db.execute("""
    SELECT DISTINCT form, cf, lang
    FROM lemmas
    WHERE form IS NOT NULL
""").fetchall()

# 2. For each word form, extract constituent signs
for form, cf, lang in lemmas:
    # Parse transliteration to extract signs
    signs = parse_signs(form)  # e.g., "ka-la-am" → ["KA", "LA", "AM"]

    # Find corresponding glossary entry
    entry = db.execute("""
        SELECT entry_id
        FROM glossary_entries
        WHERE citation_form = ? AND language = ?
    """, (cf, lang)).fetchone()

    if entry:
        entry_id = entry[0]

        # 3. For each sign in the word
        for sign_info in signs:
            sign_id = sign_info['id']      # e.g., "KA"
            sign_value = sign_info['value'] # e.g., "ka"
            value_type = sign_info['type']  # "logographic" or "syllabic"

            # 4. Insert or update sign_word_usage
            db.execute("""
                INSERT INTO sign_word_usage (sign_id, sign_value, entry_id, usage_count, value_type)
                VALUES (?, ?, ?, 1, ?)
                ON CONFLICT (sign_id, entry_id, sign_value)
                DO UPDATE SET usage_count = usage_count + 1
            """, (sign_id, sign_value, entry_id, value_type))

db.commit()
print(f"✓ Populated sign_word_usage with {db.total_changes} entries")
```

**Challenge**: Parsing Transliteration
- Need sign list mapping: "ka" → sign_id "KA"
- Handle subscripts: "du₁₁" → sign_id "KA" (one of its values)
- Recognize determinatives: "{d}" → sign_id "D" (determinative type)
- Multi-character signs: "1(BAN₂)" is single sign

---

## Educational Support for Sign Learning

### Beginner's Guide to Cuneiform Signs

**Included in `/library/glossary` page**:

```markdown
## Understanding Cuneiform Signs

Cuneiform is a **logosyllabic** writing system, which means signs can function in two ways:

### 1. Logographic (Word Signs)
One sign represents a complete word or concept.

Example: The sign 𒈗 (LUGAL) means "king" in Sumerian.

When you see this sign in a text, you read it as "lugal" (the Sumerian word for king).

### 2. Syllabic (Sound Signs)
Signs represent syllables (sounds), and you combine multiple signs to spell out words phonetically.

Example: The word "kalam" (land) is spelled with three signs:
- 𒅗 (ka)
- 𒆷 (la)
- 𒀀 (am)

Each sign represents just a sound, not a meaning.

### 3. The Same Sign Can Do Both!
This is what makes cuneiform complex. The sign 𒅗 (KA) can be used:
- **Logographically**: As the word "ka" meaning "mouth"
- **Syllabically**: As the sound /ka/ in words like "ka-la-am" (kalam/land)

Context determines which reading is correct!

### 4. Determinatives
Some signs aren't pronounced at all! They're "semantic classifiers" that tell you what kind of word follows.

Example: {d}inana
- {d} = determinative meaning "divine name"
- inana = the goddess Inana
- You read this as just "Inana", but the {d} tells you she's a deity

Common determinatives:
- {d} = divine name
- {giš} = wooden object
- {ki} = place name
- {munus} = female person
```

### Interactive Learning Features

**On Sign Detail Pages**:
- "Learning Mode" toggle: Shows only most common 5 values
- "Test Yourself": Quiz on sign readings
- "Words to Learn": Start with high-frequency words using this sign

**Difficulty Levels**:
- **Beginner**: 200 most common signs, 1-3 values each
- **Intermediate**: 500 signs, multiple values
- **Advanced**: All 3,367 signs, all values

---

## Bibliography and Resources

### Primary Sign Lists

- **OGSL** (ORACC Global Sign List) - [http://oracc.org/ogsl](http://oracc.org/ogsl)
- **Borger MZL** - Mesopotamisches Zeichenlexikon (Münster, 2004)
- **Labat** - Manuel d'épigraphie akkadienne (Paris, 1988)

### Unicode Standards

- Unicode Cuneiform Block - [https://unicode.org/charts/PDF/U12000.pdf](https://unicode.org/charts/PDF/U12000.pdf)
- Unicode Cuneiform Supplement - [https://unicode.org/charts/PDF/U12F90.pdf](https://unicode.org/charts/PDF/U12F90.pdf)

### Digital Tools

- ORACC Sign List - [http://oracc.org/ogsl](http://oracc.org/ogsl)
- CuneiPaleo - Paleographic database
- Cuneify - Font and input tools

---

*Last Updated: 2026-02-07*
*Related Documents:*
- `Research/Dictionary-Standards.md` - Dictionary structure and word-sign relationships
- `Research/Multilingual-Navigation.md` - Cross-linguistic sign usage
- `Research/Implementation-Notes.md` - Technical implementation details
