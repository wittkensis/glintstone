# Knowledge Bar (Token Sidebar) Options

When a scholar clicks a token in the ATF viewer, the Knowledge Bar answers "What does this mean in this context?" Three approaches.

---

## Option 1: Contextual Stack

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

---

## Option 2: Faceted Panels

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

---

## Option 3: Progressive Tooltip -> Drawer

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

---

## Comparison

| | 1: Contextual Stack | 2: Faceted Panels | 3: Progressive Tooltip |
|---|---|---|---|
| Entry point | Click -> full sidebar | Click -> full sidebar | Hover -> tooltip |
| Quick lookup speed | Slow (must scroll) | Medium (find tab) | Fast (hover = instant) |
| Ambiguity handling | Radio list in narrative | Radio list updates all tabs | % in tooltip, radio in drawer |
| Organization | By zoom level | By question type | By commitment level |
| Scrolling | Yes, long | No, one screen/tab | No (tooltip), yes (drawer) |
| Best for | Deep reading | Structured reference | Mixed scanning + deep dives |
| Implementation | Simple (one div) | Medium (tab state) | Higher (hover + click + drawer) |
