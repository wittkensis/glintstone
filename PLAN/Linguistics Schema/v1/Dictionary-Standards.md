# Academic Dictionary Standards for Ancient Near Eastern Languages

## Document Purpose

This document outlines the academic standards and best practices used by major cuneiform dictionaries, providing the foundation for the CUNEIFORM Library Browser implementation.

**Date Created**: 2026-02-07
**Related Implementation**: `/library/` dictionary browser and knowledge sidebar

---

## Overview of Major Dictionaries

### 1. Chicago Assyrian Dictionary (CAD)

**Full Title**: The Assyrian Dictionary of the Oriental Institute of the University of Chicago
**Abbreviation**: CAD
**Coverage**: Complete Akkadian language (all dialects and periods)
**Publication**: 1956-2010 (90 years of scholarship)
**Format**: 26 volumes, organized alphabetically
**Availability**:
- Free PDFs: [Oriental Institute](https://isac.uchicago.edu/research/publications/chicago-assyrian-dictionary)
- Searchable PDFs: [Internet Archive](https://archive.org/details/Assyrian_cad)
- Physical copies: ~$1,400 for complete set

**Structure**:
- Alphabetical organization by Akkadian headword
- Each entry includes:
  1. Etymology and cognates
  2. Meanings and semantic range
  3. Usage contexts with example attestations
  4. Derived forms and compounds
  5. Scholarly bibliography

**Example Entry Format**:
```
ŠARRU [𒊬] (šarrum, šarrū, šarri, šarrī)

    I. Etymology
       Semitic root ŠRR "to rule"
       Cognate with Hebrew śar "prince"

   II. Meanings
       1. king, monarch, sovereign
          a. Political/royal context
             "šarru rabû" - great king
             Citations: ARM 1 1:5, VAB 4 270:12
          b. Hereditary ruler
             Citations: ...

       2. military commander (Neo-Assyrian period)
          Citations: ...

  III. Compounds
       šarru-kīnu "legitimate king"
       šarru rabû "great king"

   IV. Derived Forms
       šarrūtu "kingship" (abstract noun)
       šarrānu "royal" (adjective)
```

**Key Principles**:
- Comprehensive attestations from cuneiform corpus
- Diachronic coverage (tracks meaning changes over time)
- Rich semantic analysis with contextual examples
- Cross-references to related words and forms
- Scholarly citations using standardized abbreviations

### 2. Electronic Pennsylvania Sumerian Dictionary (ePSD2)

**Full Title**: Electronic Pennsylvania Sumerian Dictionary
**Abbreviation**: ePSD2
**Coverage**: Sumerian language (all periods)
**Format**: Digital-native, part of ORACC infrastructure
**URL**: [http://oracc.museum.upenn.edu/epsd2/sux](http://oracc.museum.upenn.edu/epsd2/sux)
**Entries**: 15,944 dictionary entries

**Structure**:
- Uses ORACC CBD 2.0 (Corpus-Based Dictionary) format
- Each entry has permanent OID (ORACC ID): e.g., `o0023086`
- Organization:
  - **Headword**: Dictionary form (e.g., `lugal`)
  - **Citation Form (CF)**: Scholarly reference form
  - **Guide Word (GW)**: English meaning for disambiguation
  - **POS**: Part of speech code
  - **Forms**: Variant spellings with frequency counts
  - **Instances**: Links to corpus attestations

**CBD 2.0 Format**:
```
@entry lugal [king] N
@bases lugal
@form lugal 189
@form lugal-la 24
@form lugal-bi 14
@sense N 1. king; 2. master, lord
@end entry
```

**Key Features**:
- Corpus-driven (all entries linked to actual attestations)
- Frequency data (instance counts for each word and variant)
- Bilingual support (Sumerian with Akkadian equivalents)
- Integration with ORACC projects for contextual data

**Permanent URLs**:
- Entry format: `http://oracc2.museum.upenn.edu/epsd2/o0023086`
- Allows stable scholarly citations

### 3. ORACC Glossary Standards

**Organization**: Open Richly Annotated Cuneiform Corpus
**URL**: [https://oracc.museum.upenn.edu](https://oracc.museum.upenn.edu)
**Documentation**: [CBD 2.0 Specification](https://build-oracc.museum.upenn.edu/doc/Help/Glossaries/CBD2/index.html)

**Glossary Architecture**:

1. **Entry Structure**:
   - `@entry` tag with CF + GW + POS
   - `@form` tags link corpus instances to dictionary headwords
   - `@sense` tags for polysemy (multiple meanings)
   - `@bases` for lexical base forms

2. **Part of Speech (POS) System**:
   - Hierarchical categorization
   - 30+ POS codes covering:
     - **N** = Noun
     - **V**, **V/i**, **V/t** = Verb (intransitive, transitive)
     - **AJ** = Adjective
     - **AV** = Adverb
     - **DP** = Demonstrative Pronoun
     - **PP** = Personal Pronoun
     - **RP** = Relative Pronoun
     - **REL** = Relative
     - **MOD** = Modal
     - **PRP** = Preposition
     - **CNJ** = Conjunction
     - **DN** = Divine Name
     - **PN** = Personal Name
     - **RN** = Royal Name
     - **GN** = Geographic Name
     - **TN** = Temple Name
     - *(and more...)*

3. **Cross-Reference System**:
   - PSUs (Phrasal Semantic Units) for multi-word expressions
   - Super-glossaries: map files merging multiple glossaries
   - Equivalence links between Sumerian and Akkadian

4. **XCL Format** (Extended Corpus Linguistic Annotation):
   - Detailed linguistic markup
   - Morphological analysis
   - Syntactic relationships

**Best Practices from ORACC**:
- Unique identifiers for permanent references
- Frequency tracking (icount = instance count in corpus)
- Variant forms with usage statistics
- Project-specific glossaries that can be merged
- Consistent field naming (CF, GW, POS, lang)

---

## Handling Linguistic Complexity

### Homonyms (Same Spelling, Different Words)

**Challenge**: Multiple words with identical spelling but unrelated meanings.

**Academic Solution**:
- Numerical subscripts distinguish homonyms
- Each homonym gets unique entry ID

**Examples**:
- Sumerian **a₁** (water) vs **a₂** (arm) vs **a₃** (power)
- Akkadian **bītu** (house) vs **bītu** (daughter)

**Implementation in ePSD2**:
- Entry o0023086: `a[water]N`
- Entry o0035637: `a[arm]N`
- Entry o0035640: `a[power]N`

**Guide Word Strategy**:
- English meaning in brackets disambiguates
- Format: `headword[guide_word]POS`
- Example: `lugal[king]N` vs `lugal[owner]N`

### Polysemy (One Word, Multiple Related Meanings)

**Challenge**: Single word with multiple semantic senses.

**Academic Solution**:
- Numbered sense divisions within single entry
- Usage percentages when corpus data available
- Contextual examples for each sense

**Example (CAD-style)**:
```
BĪTU [𒂍] (bītum, bītī, bīti)

1. house, building (physical structure)
   a. residential dwelling (78% of attestations)
   b. temple (divine house) (15%)
   c. palace (royal house) (7%)

2. household (social unit)
   a. family members
   b. servants and dependents

3. estate, property (economic unit)
```

**Database Implementation**:
- `glossary_senses` table with sense_number, definition, usage_context
- Frequency percentage per sense if calculable
- Link to example lemmas for each sense

### Logographic vs Syllabic Readings

**Cuneiform Writing Systems**:

1. **Logographic**: Sign represents complete word
   - Sign KA (𒅗) = "mouth" in Sumerian
   - One sign, complete semantic unit

2. **Syllabic**: Signs represent sounds
   - ka-la-am = kalam "land"
   - Multiple signs spell out pronunciation

3. **Determinative**: Semantic classifier (unpronounced)
   - {d} before divine names: {d}inana = "goddess Inana"
   - {giš} before wooden objects
   - {munus} before female names

**Sign Values Table**:
- Sign KA has 63 different readings:
  - **Logographic**: ka (mouth), inim (word), zu₂ (tooth)
  - **Syllabic**: /ka/, /qa/, /gu₃/, /du₁₁/, /dug₄/, /e₇/, etc.

**Academic Practice**:
- Dictionary entries note which signs are used
- Sign lists (OGSL) enumerate all possible values
- Context determines which reading applies

### Variant Spellings Across Time Periods

**Causes of Variation**:
1. **Diachronic change**: Spelling conventions evolve over centuries
2. **Dialectal differences**: Geographic/cultural variation
3. **Scribal schools**: Different training traditions
4. **Grammatical context**: Suffixes and case markers
5. **Phonetic complements**: Extra signs clarify pronunciation

**Example Variants for "lugal" (king)**:
```
Form           Count   Period/Context
lugal          189     Standard form
lugal-la       24      With locative suffix
lugal-bi       14      With possessive suffix
lugal-ŋu₁₀      7      With 1st person possessive
{1}lugal        5      With numeral determinative (lone king)
```

**Academic Standard**:
- All variants map to single headword
- Frequency counts for each variant
- Period attribution when data available
- Notes on dialectal or grammatical differences

**Database Implementation**:
- `glossary_forms` table: entry_id, form, count, period (optional)
- Normalized lookup for search (strip subscripts, determinatives)
- Display variants with usage bars on word detail pages

### Cross-References and Relationships

**Types of Cross-References**:

1. **Synonyms** (same language, similar meaning)
   - Sumerian: `en[lord]` ↔ `lugal[king]` ↔ `nun[prince]`

2. **Antonyms** (opposite meaning)
   - Akkadian: `damqu[good]` ↔ `lemnu[bad]`

3. **Bilingual Equivalents** (translation)
   - Sumerian `lugal[king]` ↔ Akkadian `šarru[king]`

4. **Cognates** (related across dialects)
   - Old Babylonian `bītu` ↔ Standard Babylonian `bītu`

5. **Etymology** (word origin)
   - Akkadian `šarru` ← Semitic root *ŠRR "to rule"
   - Cognate with Hebrew *śar*, Arabic *šarr*

6. **Semantic Field** (conceptual domain)
   - "Royalty & Authority": lugal, en, nin, nam-lugal, e₂-gal

7. **Compound Contains**
   - `nam-lugal[kingship]` contains `lugal[king]`

8. **Derived Forms**
   - `šarrūtu[kingship]` derived from `šarru[king]`

**Database Implementation**:
- `glossary_relationships` table
- Fields: from_entry_id, to_entry_id, relationship_type, notes, confidence
- Relationship types: synonym, antonym, translation, cognate, etymology_source, semantic_field, compound_contains, see_also

---

## Citation and Attestation Standards

### Corpus Citations

**Format**: `COLLECTION VOLUME TABLET:LINE`

**Examples**:
- **ARM 1 1:5** = Archives Royales de Mari, volume 1, tablet 1, line 5
- **VAB 4 270:12** = Vorderasiatische Bibliothek, volume 4, tablet 270, line 12
- **CT 44 7:3** = Cuneiform Texts, volume 44, tablet 7, line 3

**Common Abbreviations**:
- **ARM** = Archives Royales de Mari
- **VAB** = Vorderasiatische Bibliothek
- **CT** = Cuneiform Texts from Babylonian Tablets
- **ABL** = Assyrian and Babylonian Letters
- **TCL** = Textes Cunéiformes du Louvre

**Modern Standard (CDLI)**:
- P-numbers: unique identifiers for each tablet
- **P123456** = specific tablet in CDLI database
- Line references: obv. i 3 (obverse, column 1, line 3)

### Attestation Display

**Scholarly Standard**:
- Show sample citations with context
- Include period, genre, provenience
- Link to full corpus when possible

**Example Display (word detail page)**:
```
Corpus Examples (234 attestations across 156 tablets)

P526829 • Old Babylonian Literary • Nippur
obv. i 3: lugal-e nam-mi-tar
         "the king decrees"
[View tablet →]

P234567 • Ur III Administrative • Ur
rev. ii 12: lugal kur-kur-ra
            "king of (all) lands"
[View tablet →]

[Show 10 more] [View all 234 →]
```

### Frequency Data (icount)

**Purpose**:
- Indicates word importance and textual coverage
- Helps learners prioritize common words
- Shows how well-attested a word is

**Range**:
- **1** = hapax legomenon (appears only once)
- **10-50** = rare word
- **50-200** = moderately common
- **200-500** = common
- **500+** = very common (high-frequency vocabulary)

**Display**:
- Show raw count: "234 occurrences"
- Show context: "234 attestations across 156 tablets"
- Use as sorting/filtering metric
- Visualize with frequency badges or bars

**Usage in Learning**:
- Students focus on high-frequency words first
- Researchers assess attestation reliability
- Lexicographers identify gaps in corpus coverage

---

## ORACC-Specific Standards

### Entry ID System

**Format**: `o` + 7-digit number (e.g., `o0023086`)

**Purpose**:
- Permanent, stable identifiers
- Support scholarly citations
- Enable cross-project references

**Benefits**:
- URLs never break: `http://oracc2.museum.upenn.edu/epsd2/o0023086`
- Database foreign keys remain valid
- API responses use stable IDs

### Language Codes

**Standard**: ISO 639-3 with ORACC extensions

**Major Codes**:
- **sux** = Sumerian (language isolate)
- **sux-x-emesal** = Emesal (Sumerian dialect)
- **akk** = Akkadian (umbrella term)
- **akk-x-stdbab** = Standard Babylonian
- **akk-x-oldbab** = Old Babylonian
- **akk-x-neoass** = Neo-Assyrian
- **akk-x-mbperi** = Middle Babylonian period
- **hit** = Hittite
- **uga** = Ugaritic
- **qpc** = Proto-Cuneiform
- **qpn** = Proper Nouns (generic)
- **elx** = Elamite
- **xhu** = Hurrian

**Hierarchical Structure**:
- Base language: `akk`
- Dialect: `akk-x-stdbab`
- Period: `akk-x-oldbab`

**Display**:
- Full labels: "Standard Babylonian Akkadian"
- Codes in parentheses: "Sumerian (sux)"
- Filter by language family or specific dialect

### Variant Form Tracking

**Format**:
```
@form lugal 189
@form lugal-la 24
@form lugal-bi 14
```

**Data Captured**:
- **Form**: Exact spelling with determinatives, subscripts
- **Count**: Number of attestations in corpus
- **Period** (optional): When variant was used
- **Dialect** (optional): Geographic/cultural context

**Normalized Forms**:
- For search: remove subscripts, determinatives
- `{d}inana₂` → search index: `inana`
- Allows flexible user queries

---

## Bibliography and References

### Primary Sources

- **Chicago Assyrian Dictionary (CAD)** - Oriental Institute, University of Chicago
  [https://isac.uchicago.edu/research/publications/chicago-assyrian-dictionary](https://isac.uchicago.edu/research/publications/chicago-assyrian-dictionary)

- **Electronic Pennsylvania Sumerian Dictionary (ePSD2)** - University of Pennsylvania
  [http://oracc.museum.upenn.edu/epsd2/sux](http://oracc.museum.upenn.edu/epsd2/sux)

- **ORACC Glossaries Documentation** - Build ORACC
  [https://build-oracc.museum.upenn.edu/doc/Help/Glossaries/CBD2/index.html](https://build-oracc.museum.upenn.edu/doc/Help/Glossaries/CBD2/index.html)

### Secondary Literature

- Tinney, S. "The Sumerian Lexicon: A Brief Overview" (CDLI)
- Fincke, J. C. "The Babylonian Texts of Nineveh" (Oxford, 2003)
- Borger, R. "Mesopotamisches Zeichenlexikon" (Münster, 2004)
- Civil, M. "Studies in the Lexicon of Sumerian" (ANES, various)

### Digital Tools Referenced

- ORACC (Open Richly Annotated Cuneiform Corpus)
- CDLI (Cuneiform Digital Library Initiative)
- eBL (Electronic Babylonian Library)
- DCCLT (Digital Corpus of Cuneiform Lexical Texts)

---

## Implementation Notes for CUNEIFORM Library

### Data Model Alignment

**Match ORACC Standards**:
- Use entry_id for permanent identifiers
- Store headword, citation_form, guide_word separately
- Include POS and language codes
- Track icount (frequency)
- Link variant forms with counts

**Database Tables**:
- `glossary_entries`: Core dictionary entries
- `glossary_forms`: Variant spellings
- `glossary_senses`: Polysemy support
- `glossary_relationships`: Cross-references
- `semantic_fields`: Conceptual domains

### Educational Layer

**Field Explanations** (for learners):
- **Headword**: "The standard dictionary form of the word"
- **Citation Form**: "How scholars reference this word in publications"
- **Guide Word**: "English meaning that helps identify which word this is"
- **POS**: "Part of speech - how the word functions grammatically"
- **icount**: "How often this word appears in the corpus"

**Glossary Page**:
- All POS codes explained with examples
- All language codes with historical context
- Grammar basics (SOV word order, case systems, etc.)
- Research conventions (citations, transliteration, etc.)

### CAD Integration Strategy

**Phase 1**: Basic linking (volume/page references)
**Phase 2**: Full digitization via Claude PDF extraction
**Phase 3**: Semantic enrichment and cross-linking

See `Research/Implementation-Notes.md` for detailed CAD workflow.

---

*Last Updated: 2026-02-07*
*Related Documents:*
- `Research/Sign-Libraries.md` - OGSL structure and sign-word relationships
- `Research/Multilingual-Navigation.md` - Bilingual practice and guide words
- `Research/Implementation-Notes.md` - Technical decisions and CAD plan
