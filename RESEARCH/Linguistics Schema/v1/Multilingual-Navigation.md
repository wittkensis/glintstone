# Multilingual Navigation in Cuneiform Studies

## Document Purpose

This document explains cross-linguistic connections between Sumerian and Akkadian in cuneiform texts, and how the CUNEIFORM library browser enables navigation between language equivalents.

**Date Created**: 2026-02-07
**Related Implementation**: Cross-references in `/library/word/{entry_id}` and bilingual search

---

## Historical Context

### Language Coexistence in Mesopotamia

**Sumerian** (language isolate, non-Semitic):
- Spoken: ~3500 BCE - ~2000 BCE
- Written: Continued as scholarly/liturgical language until ~100 CE
- Status: Became "dead" language but remained prestigious

**Akkadian** (Semitic language):
- Spoken: ~2500 BCE - ~100 CE
- Dialects: Old Akkadian, Old Babylonian, Standard Babylonian, Neo-Assyrian, etc.
- Status: Living language throughout most periods

**Bilingual Period** (~2000-100 BCE):
- Sumerian used for religious, literary, and scholarly texts
- Akkadian used for daily administration and communication
- Scribes trained in both languages
- Extensive use of Sumerian logograms in Akkadian texts

---

## Bilingual Practice

### Sumerian Logograms in Akkadian Texts

**Common Pattern**: Akkadian texts written with Sumerian word signs.

**Example**:
```
Text: LUGAL-ru-um {d}INANA i-ra-am
├── LUGAL = Sumerian logogram for "king"
├── -ru-um = Akkadian phonetic spelling (nominative case)
├── {d}INANA = Sumerian divine name
└── i-ra-am = Akkadian verb "loves" (phonetic)

Reading: "šarrum Ištar īram" = "the king loves Ištar"
```

**Why Use Logograms?**:
1. **Efficiency**: One sign vs multiple syllables
2. **Prestige**: Sumerian retained scholarly status
3. **Disambiguation**: Clarifies which Akkadian word intended
4. **Tradition**: Established scribal conventions

### Ancient Lexical Lists

**Function**: Bilingual dictionaries for training scribes.

**Major Lists**:

1. **Ura = hubullu** ("interest-bearing loan")
   - 24 tablets, ~10,000 entries
   - Sumerian → Akkadian word pairs
   - Organized by semantic field
   - Format: Sumerian entry / Akkadian equivalent

2. **Aa = naqu** ("A = to cry out")
   - Sign list with Akkadian readings
   - Teaches cuneiform basics

3. **Proto-Ea** / **Ea**
   - Advanced sign list
   - Multiple Akkadian equivalents per sign

**Example Entry**:
```
[Ura = hubullu, Tablet 3]
e₂         = bītu       (house)
e₂-gal     = ēkallu     (palace, "big house")
e₂-kur     = ekurru     (temple, "mountain house")
```

**Digital Resource**: [DCCLT - Digital Corpus of Cuneiform Lexical Texts](https://oracc.museum.upenn.edu/dcclt/)

---

## Guide Words (English Glosses)

### Purpose

**Function**: English translation that disambiguates homonyms across languages.

**Format**: `word[guide_word]POS`

**Examples**:
- Sumerian: `lugal[king]N`
- Akkadian: `šarru[king]N`
- Guide word "king" identifies both as equivalents

### Role in Bilingual Navigation

**User Query**: "What's the Akkadian word for 'king'?"

**Navigation Path**:
1. Search guide word: "king"
2. Results show:
   - `lugal[king]N` (Sumerian)
   - `šarru[king]N` (Akkadian)
3. Click either word → see cross-reference to the other
4. "Related Words" section shows bilingual pair

**Database Implementation**:
```sql
-- Find Sumerian-Akkadian pairs via guide word matching
SELECT
    sux.entry_id as sux_entry,
    sux.headword as sux_word,
    akk.entry_id as akk_entry,
    akk.headword as akk_word,
    sux.guide_word as meaning
FROM glossary_entries sux
JOIN glossary_entries akk ON sux.guide_word = akk.guide_word
WHERE sux.language = 'sux'
  AND akk.language LIKE 'akk%'
  AND sux.pos = akk.pos
ORDER BY sux.icount DESC;
```

**Limitations**:
- Guide words not always exact translations
- Cultural concepts may lack one-to-one mapping
- Multiple Akkadian words may share same guide word

---

## Cross-Linguistic Relationships

### Relationship Types

**In `glossary_relationships` table**:

1. **Translation** (Sumerian ↔ Akkadian)
   ```sql
   from_entry_id: o0032435 (lugal[king] sux)
   to_entry_id:   a0015234 (šarru[king] akk)
   relationship_type: translation
   notes: "Standard Akkadian equivalent"
   ```

2. **Loan Word** (borrowed between languages)
   ```sql
   from_entry_id: s1234567 (Sumerian technical term)
   to_entry_id:   a2345678 (Akkadian borrowing)
   relationship_type: etymology_source
   notes: "Sumerian loanword in Akkadian"
   ```

3. **Cognate** (related within language family)
   ```sql
   from_entry_id: a1111111 (Akkadian word)
   to_entry_id:   a2222222 (Hebrew cognate)
   relationship_type: cognate
   notes: "Semitic root ŠRR"
   ```

### Example Implementation

**Word Detail Page for "lugal[king] sux"**:

```html
<section class="related-words">
    <h3>Bilingual Equivalents</h3>

    <div class="equiv-pair">
        <div class="equiv-sumerian">
            <span class="lang-badge">Sumerian</span>
            <strong>lugal</strong> [king]
        </div>
        <span class="equiv-arrow">⟷</span>
        <div class="equiv-akkadian">
            <span class="lang-badge">Akkadian</span>
            <a href="/library/word/a0015234"><strong>šarru</strong></a> [king]
        </div>
    </div>

    <p class="usage-note">
        In Akkadian texts, LUGAL is often used as a logogram
        for "šarru" rather than writing the word syllabically.
    </p>
</section>
```

---

## Semantic Equivalence vs Exact Translation

### Complex Cases

**1. Partial Overlap**

Example: **Sumerian e₂** vs **Akkadian bītu**
- Both mean "house"
- But semantic range differs:
  - Sumerian e₂: physical building, temple, household
  - Akkadian bītu: dwelling, household, family line, estate

**Display**:
```
Related Words:
→ bītu[house] akk (primary equivalent)
→ ekallu[palace] akk (for e₂-gal compounds)

Note: Semantic overlap ~80%. Context determines best equivalent.
```

**2. One-to-Many Mapping**

Example: Sumerian **dug₄** (to speak)
- Akkadian equivalents:
  - qabû (to say, speak)
  - dabābu (to speak, discuss)
  - zakāru (to speak, mention)

**Display**:
```
Akkadian Equivalents (context-dependent):
→ qabû[speak] akk (general speech)
→ dabābu[speak] akk (conversation, discussion)
→ zakāru[speak] akk (formal mention, invoke)
```

**3. Cultural Concepts**

Example: Sumerian **nam-lugal** (kingship)
- Abstract noun formed with nam- prefix
- Akkadian: šarrūtu (kingship)
- But conceptual frameworks differ (Sumerian divine kingship vs Akkadian royal ideology)

**Display**:
```
Translation: šarrūtu[kingship] akk
Cultural Note: Sumerian nam-lugal emphasizes divine
appointment, while Akkadian šarrūtu focuses on dynastic
succession. Not exact semantic equivalents.
```

---

## User Workflows

### Workflow 1: Find Foreign Language Equivalent

**Scenario**: User knows Sumerian "lugal", wants Akkadian equivalent.

**Path**:
1. Search "lugal" → word detail page
2. Scroll to "Related Words" section
3. See "Bilingual Equivalents: šarru[king] akk"
4. Click šarru → navigate to Akkadian word
5. Learn pronunciation, usage, compounds

### Workflow 2: English → Multiple Languages

**Scenario**: User searches English word "king".

**Path**:
1. Search "king" (guide word search)
2. Results show both:
   - lugal[king] sux
   - šarru[king] akk
3. Cards display side-by-side with language badges
4. User can explore either or both

**Search API Enhancement**:
```php
// api/library/search.php
if ($searchType === 'guide_word') {
    $results = [
        'sumerian' => findByGuideWord($query, 'sux'),
        'akkadian' => findByGuideWord($query, 'akk%'),
    ];

    // Group by meaning, show bilingual pairs
    $grouped = groupBilingualPairs($results);
}
```

### Workflow 3: Compound Word Analysis

**Scenario**: User encounters "e₂-gal" (palace).

**Path**:
1. Search "e₂-gal" → word detail
2. "Compound Analysis" section shows:
   - e₂ = house
   - gal = big
   - Literal: "big house"
   - Meaning: palace
3. "Akkadian Equivalent": ēkallu[palace]
4. Etymology note: Akkadian ēkallu borrowed from Sumerian e₂-gal

---

## Implementation Requirements

### Database Population

**Script**: `data-tools/import/populate_relationships.py`

**Goal**: Populate `glossary_relationships` with 100+ Sumerian ↔ Akkadian translation pairs.

**Method 1: Guide Word Matching**
```python
# Match by identical guide words and POS
matches = db.execute("""
    SELECT
        sux.entry_id,
        sux.headword,
        akk.entry_id,
        akk.headword,
        sux.guide_word
    FROM glossary_entries sux
    JOIN glossary_entries akk
      ON sux.guide_word = akk.guide_word
     AND sux.pos = akk.pos
    WHERE sux.language = 'sux'
      AND akk.language LIKE 'akk%'
      AND sux.icount > 50  -- Focus on common words
""")

for match in matches:
    insert_relationship(
        from_entry=match['sux_entry'],
        to_entry=match['akk_entry'],
        type='translation',
        confidence='inferred_guidword'
    )
```

**Method 2: DCCLT Lexical Lists**
```python
# Parse Ura = hubullu entries
# Format: sumerian_word / akkadian_equivalent
lexical_pairs = parse_dcclt_list('ura_hubullu.txt')

for pair in lexical_pairs:
    sux_entry = find_entry(pair['sumerian'], 'sux')
    akk_entry = find_entry(pair['akkadian'], 'akk')

    if sux_entry and akk_entry:
        insert_relationship(
            from_entry=sux_entry,
            to_entry=akk_entry,
            type='translation',
            confidence='attested_lexical_list',
            notes=f"Ura = hubullu {pair['tablet_ref']}"
        )
```

**Method 3: Manual Curation**
- Top 100 most common words
- Verified by Assyriologist
- Highest confidence relationships

### API Response Format

**Endpoint**: `/api/library/word-detail.php?entry_id=o0032435`

**Response Includes**:
```json
{
  "entry_id": "o0032435",
  "headword": "lugal",
  "guide_word": "king",
  "language": "sux",
  "related_words": {
    "translations": [
      {
        "entry_id": "a0015234",
        "headword": "šarru",
        "guide_word": "king",
        "language": "akk",
        "relationship": "translation",
        "confidence": "verified"
      }
    ],
    "synonyms": [
      {
        "entry_id": "o0025678",
        "headword": "en",
        "guide_word": "lord",
        "language": "sux"
      }
    ]
  }
}
```

---

## Educational Content

### For Learners: Understanding Bilingualism

**Included in `/library/glossary#bilingual`**:

```markdown
## Sumerian and Akkadian: Two Languages, One Writing System

### Historical Background
Imagine learning Latin in medieval Europe - it's a dead language,
but essential for scholarship. That's how Sumerian functioned in
ancient Mesopotamia from ~2000 BCE onward.

**Sumerian**:
- Originally spoken language (~3500-2000 BCE)
- Became scholarly "dead" language (like Latin)
- Used for religious texts, literature, and prestige

**Akkadian**:
- Living language throughout most periods
- Used for daily administration and communication
- Borrowed heavily from Sumerian vocabulary

### How to Use the Bilingual Dictionary

**1. Find Equivalents**
When viewing a Sumerian word, look for the "Bilingual
Equivalents" section to see the Akkadian translation.

**2. Understand Logograms**
Many Akkadian texts use Sumerian word-signs (logograms).
Example: LUGAL in an Akkadian text is read as "šarru" (king).

**3. Learn Both for Reading**
To read Akkadian texts, you often need to know Sumerian
logograms! This dictionary helps you navigate between them.
```

---

*Last Updated: 2026-02-07*
*Related Documents:*
- `Research/Dictionary-Standards.md` - Guide word standards and homonyms
- `Research/Sign-Libraries.md` - Sign usage across languages
- `Research/Implementation-Notes.md` - Technical cross-reference implementation
