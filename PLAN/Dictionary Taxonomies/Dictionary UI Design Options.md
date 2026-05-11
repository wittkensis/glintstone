# Dictionary UI Design Options

Ideation reference for Signs, Lemmas, and Glosses detail pages, ATF viewer, and knowledge bar sidebar. Grounded in current schema reality and real corpus data.

---

## Terminology Alignment

The Lexicography Terminology report defines 5 layers. Current schema mapping:

| Report Layer | Definition | Schema Equivalent | Alignment |
|---|---|---|---|
| **L0: Sign** | Physical cuneiform impression | `lexical_signs` | Good. Missing: sign_type, period attestation range |
| **L1: Reading** | Phonological realization, language-scoped | No dedicated table. Split across `lexical_signs.values[]`, `sign_lemma_associations.reading_type`, `token_readings` | Gap. Readings should be first-class entities |
| **L2: Lemma** | Dictionary citation form | `lexical_lemmas` | Good. Missing: certainty flag, stem/derivation, root |
| **L3: Gloss** | Target-language translation label | `lexical_lemmas.guide_word` + `lexical_senses.definition_parts[]` | Rename "Meanings" to "Glosses" is correct |
| **L4: Attestation** | Specific textual instance | `lemmatizations` + `tokens` + `text_lines` | Good. Missing: context gloss, sentence type |

Key principles:
- "Gloss for finding, attestation for understanding"
- `lexical_senses` stores glosses, not senses (senses are irrecoverable for dead languages)
- The Glosses page is a proxy Concept browser (grouped by English guide_word)
- Reading is the biggest structural gap (scattered across 3 locations)

---

## Data Reality

| Table | Rows | Key fields | Gaps |
|---|---|---|---|
| `lexical_signs` | 2,965 | sign_name, unicode_char, values[] | shape_category, component_signs, periods[], regions[] empty |
| `lexical_lemmas` | 61,435 | citation_form, guide_word, pos, language_code, attestation_count | period, region, dialect empty |
| `lexical_senses` | 155,491 | definition_parts[], lemma_id, sense_number | semantic_domain, context_distribution empty |
| `sign_lemma_associations` | 2,972 | sign_id, lemma_id (all logographic) | No syllabic or determinative |
| `token_readings` | 948,574 | reading, sign_function (470k numeric, 467k syl, 12k logo) | -- |
| `lemmatizations` | 181,394 | citation_form, guide_word, pos, language (32k match lexical_lemmas) | -- |
| `glossary_entries` | 45,572 | headword, citation_form, guide_word, icount, pos, language | -- |
| `glossary_forms` | 205,532 | form, count per entry | -- |

**Critical join path:** `lemmatizations -> tokens -> text_lines -> artifacts` gives period/provenience for 2,200 tablets.

---

## Translation Layers -- Real Data Examples

### Example 1: Sumerian-Akkadian bilingual (P229547, OB lexical)

ATF: `lu2 sza3 hul gig-ga ak = %a sza le-mu-ut-tam e-ep-szu`

| Layer | lu2 | sza3 | hul | gig-ga | ak | Akk gloss |
|---|---|---|---|---|---|---|
| Sign | LU2 | SHA3 | HUL | GIG.GA | AK | (syllabic) |
| Reading | lu2 (syl) | sha3 (syl) | hul (syl) | gig-ga (syl) | ak (syl) | sha le-mu-ut-tam e-ep-shu |
| Lemma | lu [person] N sux | shag [heart] N sux | hulu [bad] V/i sux | gig [sick] V/i sux | ak [do] V/t sux | (unlemmatized) |
| Gloss | person, man | heart, inside | bad, evil | sick, pained | to do | -- |

- Sumerian side: full chain works. Akkadian side: readings present but NO lemmatization
- Multiple lexical_lemma matches per token (lu[person] in 6 sources) -- use highest attestation_count
- `=` and `%a` stored as regular tokens (POS=L), detectable as language boundaries

### Example 2: Pure Akkadian (P247823, Std Babylonian literary)

ATF: `[...] ra-man-szu2-nu u2-szah-ha-zu nu-ul-la-a-tu2`

| Layer | ra-man-shu2-nu | u2-shah-ha-zu | nu-ul-la-a-tu2 |
|---|---|---|---|
| Sign | (no token_readings) | (no token_readings) | (no token_readings) |
| Lemma | ramanu [self] N akk-x-stdbab | ahazu [take] V | nulliatu [malice] N |
| Norm | ramanshunu | ushahhazu | nullatu |
| Gloss | self | to incite (Sh-stem) | maliciousness |

- No sign-level data. Norm vs citation form distinction important for Akkadian

### Example 3: Hittite with Sumerograms (KBo 50,009, MH ritual)

ATF: `u4 ur-sag mar-tu# ib2-ta-sa`

| Layer | u4 | ur-sag | mar-tu# | ib2-ta-sa |
|---|---|---|---|---|
| Sign | U4 | UR.SAG | MAR.TU | IB2.TA.SA |
| Lemma | ud [day] OR nig [thing] | ursag [hero] OR tuku [acquire] OR usar [neighbor] | MAR.TU [westerner] | X (unlemmatized) |
| Gloss | day / thing | hero / acquire / neighbor | westerner | -- |

- ALL lemmatizations are Sumerian, not Hittite. This is a writing system reality, not a data gap
- 14,669 Hittite tablets, 167k tokens, but 0 Hittite-language lemmatizations

### Language Coverage

| Language | Lemmatizations | Dictionary link |
|---|---|---|
| Sumerian | 133,900 | Good (32k match lexical_lemmas) |
| Akkadian | 32,636 | Partial |
| Hittite | 8,864 (as Sumerograms) | Sumerogram-only |
| Hurrian | 1,202 | Minimal |
| Ugaritic | 528 | Minimal |

---

## Available Measurements Per Entity

### Sign

Available now (no schema changes):
- Glyph + metadata (unicode_char, sign_name, codepoint, source)
- Readings (values[] array)
- Linked lemmas via sign_lemma_associations (2,972, all logographic)
- Occurrence count from token_readings (72k matchable)
- Function breakdown: syllabographic / logographic / numeric / determinative
- Period distribution via token_readings -> tokens -> text_lines -> artifacts
- Provenience distribution (same join)
- Language distribution (same join -> lemmatizations.language)
- Simple vs compound heuristic (names containing x or . are compound)

Proposed measurements:
- Total corpus occurrences, tablet spread
- Function ratio (% syl / % logo / % num)
- Top periods, proveniences (bar charts)
- Polysemy (distinct lemmas this sign writes)
- Reading density (number of values vs corpus average)

### Lemma

Available now:
- Header: citation_form [guide_word] POS, language, source, attestation_count
- Glosses list: lexical_senses.definition_parts[] by sense_number
- Signs used via sign_lemma_associations
- Period/provenience distribution via lemmatizations join
- Dialect breakdown: lemmatizations.language grouped
- Orthographic forms: glossary_forms via glossary_entries (variant spellings with counts)
- Tablet count, cross-language equivalents (same guide_word)

Proposed measurements:
- Temporal profile (period bar chart with proper sort_order)
- Geographic spread, polysemy index, Zipf rank
- Hapax flag, comparative frequency ("Nth most common [POS] in [language]")
- Orthographic variation count

### Gloss

Available now:
- Header: guide_word, total attestations across all lemmas
- Lemmas by language with attestation bars
- Relative frequency, POS distribution, cross-language coverage

Proposed measurements:
- Language coverage ratio ("N of M languages")
- Attestation concentration (one lemma dominates or evenly distributed?)
- Temporal range (earliest to latest period)
- Related glosses (co-occurring guide_words)

---

## Detail Section Structure Options

Three approaches to organizing information *within* a detail page.

### Option 1: Metrics-Forward

Lead with quantitative measurements. Stats and distributions first, entities second. For researchers who want "how much? where? when?" before "what connects?"

**Section order (Sign):**
1. Stat cards: occurrences, tablets, lemmas, readings
2. Function ratio bar (logo/syl/det/num)
3. Period bars | Provenience bars (side by side)
4. Language distribution bars
5. Readings list
6. Linked lemmas with attestation bars

**Section order (Lemma):**
1. Stat cards: attestations, tablets, glosses, spellings
2. Zipf rank note
3. Period bars | Provenience bars (side by side)
4. Orthographic forms with frequency bars
5. Glosses numbered list
6. Signs used
7. Cross-language equivalents with attestation bars
8. Dialect breakdown bars

**Section order (Gloss):**
1. Stat cards: total att, lemmas, languages
2. Attestation share by language (bar)
3. Period range (timeline)
4. Lemmas grouped by language with attestation bars
5. Related glosses grid

### Option 2: Relationships-Forward

Lead with connected entities. The page is a navigation hub showing *what connects to this*. Measurements appear inline alongside relationships.

**Section order (Sign):**
1. "Writes These Words" -- lemmas grouped by language with attestation bars
2. Readings list
3. "Shares Glosses With" -- other signs writing same meanings
4. Usage Context box: function ratio + where/when (combined)

**Section order (Lemma):**
1. "Means" -- glosses list
2. "Written With" -- signs + orthographic forms with frequency bars
3. "Same Meaning In Other Languages" -- cross-language + dialect breakdown
4. "Appears In" -- period/provenience side-by-side + rank note

**Section order (Gloss):**
1. "Expressed By" -- lemmas grouped by language, each with glosses + sign info
2. "Written With Same Sign" -- logographic bridges across languages
3. Related glosses with overlap notes
4. Distribution bar (language share)

### Option 3: Layered Disclosure

Compact top block with essential identity + one key insight. Everything else behind expandable `>/<` sections. Scholar controls depth.

**Structure (all entities):**
1. Dense summary line (identity + key numbers + most notable fact)
2. One section open by default (most essential: Readings for signs, Glosses for lemmas, Lemmas for glosses)
3. All other sections collapsed: click to expand

**Sign example:**
```
U+12217 LUGAL -- OGSL -- 12,304 occ across 892 tablets
Primarily logographic (89%) -- 7 readings -- 18 linked words

> Readings (open by default)
  lugal, sharru, hasshu, LUGAL, lugal2, shar, sar

> Linked Words (18)
> Function Breakdown
> Periods & Proveniences
> Language Distribution
```

### Section Structure Comparison

| | 1: Metrics-Forward | 2: Relationships-Forward | 3: Layered Disclosure |
|---|---|---|---|
| First thing visible | Stat cards + bars | Connected entities | Dense summary sentence |
| Primary question | "How common? Where?" | "What connects?" | "What is this?" |
| Cognitive load | High (all visible) | Medium (natural groups) | Low (scholar controls) |
| Scroll length | Long | Medium-long | Short (collapsed) |
| Best for | Corpus researchers | Philologists | Mixed audiences |
| Section headers | Technical (CORPUS PROFILE) | Natural language (WRITES THESE WORDS) | Entity-type labels |

---

## ATF Viewer Options

Three architectures for showing tablet text with translation layers.

### Option A: Interlinear Stack (Philological)

Each layer is a horizontal row under the ATF line. Classic interlinear gloss format.

```
{P-number} . {publication} . {surface} {line}    {period}
ATF     token1      token2      token3      ...
SIGN    {sign_name} {sign_name} {sign_name}
FUNC    {function}  {function}  {function}
LEMMA   {cf [gw]}   {cf [gw]}   {cf [gw]}
POS     {pos_label} {pos_label} {pos_label}
NORM    {norm_form} {norm_form} {norm_form}
GLOSS   {english}   {english}   {english}

LAYERS  filled/empty/partial per layer    [coverage bar]
```

- Toggle layers on/off. Click token -> dictionary detail. Warning badge for competing lemmatizations
- Language coloring via CSS class from lemmatizations.language
- **Best for:** Teaching, line-by-line translation

### Option B: Token Column Grid (Analytical)

Each token is a column. Rows are layers. Spreadsheet-like.

```
         | TOKEN n    | TOKEN n+1  | TOKEN n+2  |
---------+------------+------------+------------|
ATF      | {reading}  | {reading}  | {reading}  |
SIGN     | {name}     | {name}     | {name}     |
LEMMA    | {cf [gw]}  | {cf [gw]}  | {cf [gw]}  |
         | {alt1}     |            |            |
GLOSS    | {english}  | {english}  | {english}  |
att.     | {count}    | {count}    | {count}    |
```

- Competing lemmas as expandable sub-rows. Attestation counts per token
- **Best for:** Research, data quality audit, disambiguation

### Option C: Annotation Ribbons (Reading-Oriented) -- RECOMMENDED

ATF flows naturally left-to-right. Togglable colored ribbons below.

```
{P-number} . {publication}            {period}
{surface} {line}

  token1     token2     token3     ===  token4     token5
  {LANG_A} ---------------------    |    {LANG_B} ----------

  [ lemma ribbon: {cf [gw]}   {cf [gw]}   {cf [gw]}   {cf [gw]} ]
  [ gloss ribbon: {english}   {english}   {english}   {english}  ]

  [coverage bar]  {description}
```

- Ribbon toggles: Lemma / Norm / Gloss / Signs. Hover token -> full chain tooltip
- Language boundary separator at = %a tokens. Wraps naturally
- **Best for:** Reading, browsing, general scholarly use

### ATF Viewer Comparison

| | A: Interlinear | B: Token Grid | C: Ribbons |
|---|---|---|---|
| Metaphor | Philological interlinear | Spreadsheet | Annotated reading |
| Best for | Teaching | Research/audit | Reading/browsing |
| Ambiguity | Inline badges | Expandable rows | Branching under token |
| Bilingual | Side-by-side in row | Column groups | Language zone separator |
| Data density | Medium | High | Low (on-demand) |
| Long lines | Horizontal scroll | Horizontal scroll | Wraps |
| Mobile | Poor | Poor | Good |

**Recommendation:** Option C as default, Option B as "analysis mode" toggle.

### Shared ATF Implementation Notes

- Language CSS classes from `lemmatizations.language` (no schema changes)
- `=` and `%a` tokens detected as language boundaries (POS=L)
- Coverage bar: populated layers / total layers per token
- Token data: `tokens -> token_readings + lemmatizations -> lexical_lemmas -> lexical_senses`
- Period/provenience from `text_lines -> artifacts`

---

## Knowledge Bar (Token Sidebar) Options

When a scholar clicks a token in the ATF viewer, the Knowledge Bar answers "What does this mean in this context?" Three approaches.

### Option 1: Contextual Stack

Narrative flow widening from specific to general: this instance -> dictionary entry -> corpus statistics -> tablet context. Scholar reads top-to-bottom and stops when they have enough.

**Sections:**

IN THIS TEXT
- Reading, Sign, Lemma, Sense, Language
- Line context with selected token highlighted
- If ambiguous: competing lemmatizations as radio list ranked by attestation count

IN THE DICTIONARY
- Full glosses list from lexical_senses (with "this instance uses sense N" marker)
- Attestation count + Zipf rank

IN THE CORPUS
- "How this reading is typically interpreted" (% breakdown of lemmatizations for this reading)
- Co-occurrence: words frequently appearing with this token on same line
- "On this tablet" summary: how many times this token appears, consistency of lemmatization

THIS TABLET
- P-number, publication, period, provenience, genre

**For ambiguous tokens (e.g., Hittite ur-sag):**
- Competing lemmatizations shown as radio-button list with attestation counts
- "In Hittite texts specifically" -- narrowed % breakdown
- "No Hittite reading available" notice when all lemmatizations are Sumerograms

**Character:** Scholarly annotation feel. Each section widens the lens. Long sidebar, requires scrolling.

### Option 2: Faceted Panels

Mini tabbed interface with 4 focused panels. Each answers one question. One screen per tab, no scrolling.

**Tabs:**

[Instance] -- "What is this token?"
- Reading, Sign, Lemma, Sense, Norm, Language
- Line context with gloss underline
- Tablet metadata
- If ambiguous: disambiguation selector that updates all other tabs

[Reading] -- "What sign is this?"
- Sign glyph + name + stats
- All readings of this sign
- Function breakdown (syl/logo/det)
- "This reading typically means" (% breakdown)

[Dictionary] -- "What does the dictionary say?"
- Full glosses list (with "this instance" marker)
- Signs used to write this lemma
- Top spellings with frequency bars
- Cross-language equivalents

[Corpus] -- "Where else does this appear?"
- Period distribution bars
- Provenience distribution bars
- Co-occurring words (same line)
- "On this tablet" summary

**For ambiguous tokens:**
- Instance tab gets disambiguation header
- Selecting a candidate updates all tabs

**Character:** Structured reference. Scholar navigates by question type. No scrolling within a tab.

### Option 3: Progressive Tooltip -> Drawer

Three levels of commitment. Most lookups end at Stage 1 or 2.

**Stage 1: Hover tooltip** (no click needed)
```
lu [person] N -- Sumerian
"person, man"
12,304 att. -- ePSD2
> More
```

For ambiguous tokens:
```
Warning: 3 candidates:
ursag [hero] N         72%
tuku [acquire] V/t     18%
usar [neighbor] N      10%
> More
```

**Stage 2: Click -> expanded tooltip**
- Full glosses list (with "this instance" marker)
- Sign info
- "This reading usually means" (% breakdown)
- Line context with gloss underline
- "Open >" link to full drawer

**Stage 3: "Open" -> full sidebar drawer**
- Everything from Option 1 (Contextual Stack) in a persistent sidebar
- Includes cross-language, corpus stats, co-occurrence, tablet info

**Character:** Graduated disclosure. Hover = instant gloss (most common need). Click = enough to resolve ambiguity. Open = full reference. Keeps reading flow intact.

### Knowledge Bar Comparison

| | 1: Contextual Stack | 2: Faceted Panels | 3: Progressive Tooltip |
|---|---|---|---|
| Entry point | Click -> full sidebar | Click -> full sidebar | Hover -> tooltip |
| Quick lookup speed | Slow (must scroll) | Medium (find tab) | Fast (hover = instant) |
| Ambiguity handling | Radio list in narrative | Radio list updates all tabs | % in tooltip, radio in drawer |
| Organization | By zoom level | By question type | By commitment level |
| Scrolling | Yes, long | No, one screen/tab | No (tooltip), yes (drawer) |
| Best for | Deep reading | Structured reference | Mixed scanning + deep dives |
| Implementation | Simple (one div) | Medium (tab state) | Higher (hover + click + drawer) |

---

## Semantic Category Proposal (deferred)

Top 30 guide_words by attestation suggest these natural groupings:

| Category | Examples | Rule |
|---|---|---|
| Numerals & Measurement | "1", "00", "unit" | POS = NU or MA |
| Kinship & Social | "son", "slave", "king" | Manual |
| Spatial & Geographic | "land", "place", "house" | Manual |
| Temporal | "day" | Manual |
| Divine & Religious | "god" | Manual |
| Body & Physical | "hand", "ring" | Manual |
| Actions & Processes | "do", "go" | POS = V, V/t, V/i |
| Grammar & Function | "of", "in", "to" | POS = PP, CNJ, DP, IP |
| Qualities | "great", "totality" | POS = AJ |
| Proper Names | "Assyria" | POS = GN, PN, DN, etc. |

~60% auto-assignable from POS. Top 500 need manual curation.

---

## Additional Ideas

### Cross-Entity Analytics
- Sign -> Lemma -> Gloss chains: visualize branching from one sign to many words to many meanings
- Compound family browser: link component signs, show how meaning combines
- Cognate network: same meaning across Sumerian/Akkadian/Hittite

### Corpus-Level
- Diachronic meaning shift (requires per-sense period data)
- Genre association (admin vs literary via artifact genre joins)
- Co-occurrence (words on same tablet or line)

---

## User Preferences Noted

- Full dedicated detail pages (not panel)
- Simple HTML/CSS bars for charts
- Semantic categories deferred
- "Meanings" renamed to "Glosses"

---

## Tablet Citation Display Options

Three approaches for presenting citation/metadata for a tablet. Using **P134010** (CM 26, 037) — an Ur III administrative tablet from Umma with 502 text lines, seal impression, physical dimensions, dated text, and full publication data.

### Available Citation Fields (P134010)

| Field | Value |
|-------|-------|
| CDLI P-number | P134010 |
| Designation | CM 26, 037 |
| Museum number | NBC 00419 |
| Material | clay |
| Object type | tablet |
| Dimensions | 38 × 38 × 15 mm |
| Seal | S000207 |
| Period | Ur III (ca. 2100–2000 BC) |
| Provenience | Umma (mod. Tell Jokha) |
| Genre | Administrative |
| Language | Sumerian |
| Primary publication | CM 26, 037 |
| Publication author | Sharlach, Tonia M. |
| Date of origin | (year/month/day in regnal dating) |
| ORACC projects | epsd2 |
| ATF source | cdlistaff |
| Surfaces | obverse, reverse |
| Text lines | 502 |
| Collection | Nies Babylonian Collection, Yale |

### Option 1: Bibliographic Card (Library Catalog Style)

Treats the tablet as a published artifact. Citation-first layout modeled on library catalog entries and CDLI's own record format. Groups data into labeled blocks: identification, physical description, textual content, provenance, bibliography.

```
┌─────────────────────────────────────────────────────────────┐
│  CM 26, 037                                    P134010      │
│  ═══════════                                                │
│                                                             │
│  IDENTIFICATION                                             │
│  Museum no.     NBC 00419                                   │
│  Collection     Nies Babylonian Collection, Yale            │
│  Seal           S000207                                     │
│                                                             │
│  PHYSICAL DESCRIPTION                                       │
│  Object         tablet · clay                               │
│  Dimensions     38 × 38 × 15 mm (W × H × T)               │
│  Surfaces       obverse · reverse                           │
│  Preservation   —                                           │
│                                                             │
│  TEXT                                                       │
│  Language        Sumerian                                   │
│  Lines           502                                        │
│  Genre           Administrative                             │
│  ATF source      cdlistaff                                  │
│  Translation     —                                          │
│                                                             │
│  PROVENANCE                                                 │
│  Provenience     Umma (mod. Tell Jokha)                     │
│  Period          Ur III (ca. 2100–2000 BC)                  │
│  Date            (regnal date if available)                  │
│                                                             │
│  BIBLIOGRAPHY                                               │
│  Primary pub.    CM 26, 037                                 │
│  Author          Sharlach, Tonia M.                         │
│  ORACC           epsd2                                      │
│  CDLI            https://cdli.ucla.edu/P134010              │
│                                                             │
│  ┌─────────────────────────────────────────────────┐        │
│  │  Cite as:                                       │        │
│  │  Sharlach, T.M. CM 26, 037. NBC 00419.         │        │
│  │  Nies Babylonian Collection, Yale.              │        │
│  │  CDLI P134010.                                  │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

**Pros:** Familiar to scholars, complete, machine-parsable sections, easy to scan for a specific field. Copyable citation block.
**Cons:** Verbose, lots of vertical space, many fields will be empty for sparse tablets. Static feel.

---

### Option 2: Compact Header + Metadata Chips (Dashboard Style)

Citation compressed into a dense header above the ATF viewer. Key facts as inline chips/badges. Secondary fields in a collapsible "More details" drawer. Optimizes for "get back to reading" — shows enough to orient, hides the rest.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  CM 26, 037                                                 │
│  NBC 00419 · Nies Babylonian Collection, Yale               │
│                                                             │
│  ┌──────────┐ ┌────────┐ ┌───────┐ ┌────────────────────┐  │
│  │ Ur III   │ │ Umma   │ │ Admin │ │ Sumerian           │  │
│  └──────────┘ └────────┘ └───────┘ └────────────────────┘  │
│                                                             │
│  502 lines · obv + rev · 38×38×15 mm · Seal S000207        │
│                                                             │
│  Pub: Sharlach, T.M.  ·  CDLI P134010  ·  ORACC: epsd2    │
│                                                             │
│  ▸ More details                                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  @obverse                                                   │
│  1'. [...]-nita2# szu                                       │
│  2'. [...] AN                                               │
│  ...                                                        │
└─────────────────────────────────────────────────────────────┘

Expanded "More details":
┌─────────────────────────────────────────────────────────────┐
│  ▾ More details                                             │
│                                                             │
│  Material        clay tablet                                │
│  Date            (regnal date)                              │
│  ATF source      cdlistaff                                  │
│  Translation     not available                              │
│  Preservation    —                                          │
│  CDLI entered    2006-02-07                                 │
│  CDLI updated    2020-02-12                                 │
│                                                             │
│  ┌──────────────────────────────────────────┐               │
│  │ 📋 Copy citation                         │               │
│  └──────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

**Pros:** Minimal vertical footprint, chips scannable at a glance, progressive disclosure keeps rare fields out of the way. Best when citation supports reading rather than being the primary focus.
**Cons:** Important fields may hide behind "More details." Chips can feel reductive for nuanced metadata (period names truncated, etc.).

---

### Option 3: Structured Sidebar (Reference Pane)

Citation data lives in a persistent sidebar column alongside the ATF viewer, not above it. Always visible while scrolling through text. Grouped into small labeled sections with a fixed-width layout. Similar to a museum placard or the metadata column in a digital archive viewer.

```
┌──────────────────────┬──────────────────────────────────────┐
│  TABLET               │  @obverse                           │
│                       │  1'. [...]-nita2# szu               │
│  CM 26, 037           │  2'. [...] AN                       │
│  P134010              │  3'. [x] masz2-gal                  │
│                       │  4'. [x] masz2-nita2                │
│  ────────────────     │  5'. ur-{d}lamma                    │
│  Museum               │  6'. 1(u) 3(disz) ud5 ...          │
│  NBC 00419            │  7'. a-ra2 1(disz)-kam              │
│  Nies Babylonian      │  8'. ...                            │
│  Coll., Yale          │  9'. ...                            │
│                       │  10'. ...                           │
│  ────────────────     │  ...                                │
│  Physical             │                                     │
│  tablet · clay        │  @reverse                           │
│  38 × 38 × 15 mm     │  1. ...                             │
│  obv · rev            │  2. ...                             │
│  Seal S000207         │  3. ...                             │
│                       │                                     │
│  ────────────────     │                                     │
│  Context              │                                     │
│  Ur III               │                                     │
│  Umma (Tell Jokha)    │                                     │
│  Administrative       │                                     │
│  Sumerian             │                                     │
│  (regnal date)        │                                     │
│                       │                                     │
│  ────────────────     │                                     │
│  Publication          │                                     │
│  CM 26, 037           │                                     │
│  Sharlach, T.M.       │                                     │
│                       │                                     │
│  ────────────────     │                                     │
│  Links                │                                     │
│  CDLI  ·  ORACC       │                                     │
│  epsd2                │                                     │
│                       │                                     │
│  ────────────────     │                                     │
│  Copy citation        │                                     │
└──────────────────────┴──────────────────────────────────────┘
```

**Pros:** Citation always visible during reading — no scrolling away from text. Natural for comparison (metadata on left, content on right). Mirrors physical museum experience (placard beside artifact). Good for printing.
**Cons:** Costs horizontal space permanently. On narrow screens, must collapse to a header or overlay. Sidebar can feel disconnected from the text it describes.

---

### Tablet Citation — Comparison

| | 1: Bibliographic Card | 2: Compact Header + Chips | 3: Structured Sidebar |
|---|---|---|---|
| Layout | Full-width block above text | Compressed header above text | Persistent column beside text |
| Vertical cost | High (15–25 lines) | Low (5–8 lines) | None (parallel) |
| Horizontal cost | None | None | ~220px sidebar |
| Always visible | No (scrolls away) | Partially (header stays) | Yes |
| Sparse tablets | Many empty rows | Chips just absent — clean | Short sidebar — clean |
| Rich tablets | Complete display | Overflow into drawer | Complete display |
| Mobile | Good | Best | Poor (needs collapse) |
| Scholar workflow | Reference lookup | Reading-focused | Side-by-side study |
| Copy citation | Block at bottom | Button in drawer | Button at bottom |

### Recommendation

**Option 2 (Compact Header + Chips) as default** for the ATF viewer, where the text is the focus. **Option 1 (Bibliographic Card)** for a dedicated tablet detail/catalog page if one exists. Option 3 is elegant for desktop but breaks on mobile and duplicates the Knowledge Bar's sidebar real estate.
