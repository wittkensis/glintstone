# Dictionary Taxonomy Survey

## Overview

A multi-language cuneiform dictionary spanning **Sumerian, Akkadian, Hittite, and Elamite**, built from open-source data and delivered as an open API with an exploratory UI. The project is designed to serve scholars, students, and computational researchers, with support for competing scholarly interpretations and confidence scoring.

---

## Open Data Sources

### Sumerian

| Resource | Description | Format / Access |
|----------|-------------|-----------------|
| **ePSD2** (Penn) | Richest lemmatized Sumerian dictionary | JSON via ORACC API |
| **ETCSL** | Transliterated literary corpus with lemmatization | XML/HTML |
| **CDLI** | Catalog + transliterations for ~350k objects (ATF files) | Web API, bulk download |
| **ORACC project corpora** (DCCLT, Nisaba, etc.) | Individual project lemmatizations feeding ePSD2 | JSON via ORACC API |

### Akkadian

| Resource | Description | Format / Access |
|----------|-------------|-----------------|
| **ISAC/CAD** (Chicago Assyrian Dictionary) | 21-volume comprehensive dictionary, being digitized | Digitization in progress; format TBD |
| **CDA** (Black/George/Postgate) | Concise dictionary, widely used | Copyright-restricted |
| **ORACC Akkadian lemmatizations** | Scattered across projects (SAAo, RINAP, etc.) | JSON via ORACC API |
| **Korp/LMU Munich projects** | Some morphologically parsed corpora | Varies |

### Hittite

| Resource | Description | Format / Access |
|----------|-------------|-----------------|
| **CHD** (Chicago Hittite Dictionary) | Partially digitized | Digitization in progress |
| **HPM** (Hittite Parsed Morphology, Marquette) | Morphological decomposition data | Structured data |
| **Hethitologie Portal Mainz** | Catalog and some transliterations | Web |
| **TITUS** (Frankfurt) | Some digitized Hittite texts | Web |

### Elamite

| Resource | Description | Format / Access |
|----------|-------------|-----------------|
| **CDLI** | Some Elamite text catalog entries | Web API |
| **Persepolis Fortification Archive** (ISAC) | Elamite administrative text transliterations | Varies |
| **Tavernier / Desmet / Henkelman** | Key scholarly lexicon and prosopography work | Not well-digitized; extraction needed |

> ⚠️ Elamite is the thinnest layer by far. Significant manual curation will be required.

### Sign Lists & Paleography

| Resource | Description | Format / Access |
|----------|-------------|-----------------|
| **OGSL** (ORACC Global Sign List) | Best open sign list; sign names → readings → Unicode | JSON via ORACC |
| **MZL** (Borger) | Standard sign list; sign numbers widely referenced | Copyright-restricted (numbers are open) |
| **Labat** | Older sign list, numbering system still used | Copyright-restricted |
| **Unicode Cuneiform block** | U+12000–U+1254F + supplements | Standard |
| **CDLI Sign Image Project** | Photographs and drawings of sign variants by period | Images |

---

## Core Data Model

The dictionary is not three separate indexes but a **single knowledge graph** with three access layers. Five core entity types form the backbone:

### Entity Types

```
SIGN ←→ READING ←→ LEMMA ←→ CONCEPT
                      ↑
                INTERPRETATION
```

**SIGN (Grapheme)** — The physical cuneiform sign as written on a tablet.
- Canonical ID (Unicode codepoint + OGSL reference)
- Cross-references to Borger/MZL and Labat numbering
- Wedge component decomposition (for structural/fuzzy search)
- Period/region variants with optional SVG or image references

**READING (Value)** — A specific phonetic or logographic value a sign can carry.
- Value string, type (syllabic, logographic, determinative)
- Scoped by language(s), period(s), and script type
- Confidence score and source references

**LEMMA (Dictionary Entry)** — A word in a specific language.
- Citation form, guide word (English gloss), part of speech
- Root (for Semitic languages) or morphological structure
- Full morphological paradigm (declension/conjugation forms)
- Orthographic realizations: the sign sequences used to write this word, tagged by type (logographic, syllabic, mixed) and period
- Semantic domain links, attestation references, cross-linguistic equivalents

**CONCEPT (Semantic Node)** — A meaning that bridges across languages.
- Label and domain hierarchy (e.g., `SOCIAL_HIERARCHY.POLITICAL.RULER`)
- Links to all lemmas expressing this concept across all four languages
- Scholarly notes on semantic range and overlap

**INTERPRETATION** — A first-class entity for scholarly claims.
- Target (any entity: a reading, a lemma meaning, an etymology, a dating)
- Claim text, confidence score (0–1), basis type (consensus / revision / speculative)
- Source citations with full bibliographic references
- Supersession and contestation links to other interpretations

> This model makes disagreement visible rather than hidden, which is especially critical for Elamite and for contested Sumerian readings.

---

## Three Access Patterns (Taxonomy Layers)

Each access pattern is a lens into the same underlying graph, serving a different user need and workflow.

### 1. Sign Entry Point — "I see this on a tablet"

**User:** Epigrapher, student, tablet reader.

**Query flow:**
```
Visual form / sign name / wedge description / MZL number
  → SIGN
    → all READINGS (filtered by language, period)
      → all LEMMAS using this sign
        → attestations in context
```

**UI concept:** A sign browser with multiple input methods:
- Unicode character or sign name
- Borger/MZL or Labat number
- Wedge-component search ("two horizontals + one Winkelhaken")
- Visual period selector showing paleographic evolution
- Future: drawn input or image-based matching

**Result view:** Sign card showing visual history across periods, every known reading grouped by language, and links to every word written with that sign.

---

### 2. Concept Entry Point — "What's the word for X?"

**User:** Comparativist, cultural historian, translator.

**Query flow:**
```
English gloss / semantic domain browse
  → CONCEPT
    → LEMMAS across all four languages (side by side)
      → orthographic forms per lemma
        → SIGNS used, highlighting shared logograms
```

**UI concept:** A thematic explorer organized by semantic ontology:
- Browse or search a controlled vocabulary of ~500–800 conceptual domains
- Side-by-side view of how each language expresses a concept
- Visual highlighting of logographic bridges (e.g., 𒈗 LUGAL = "king" in all four languages, representing four unrelated spoken words)
- Related concept navigation

**Result view:** Comparative table with expandable entries per language, showing the sign-level convergence and divergence across writing traditions.

---

### 3. Lemma Entry Point — "I know this word, tell me everything"

**User:** Philologist, text editor, advanced student.

**Query flow:**
```
Transliteration / citation form / ORACC-style lemma
  → LEMMA
    → morphological paradigm
    → orthographic variants (logographic, syllabic, mixed)
    → semantic domains
    → attestations
    → cross-linguistic equivalents
```

**UI concept:** Traditional dictionary view, enhanced:
- Search by transliteration, normalized form, or ORACC lemma format (`lugal[king]N`)
- Full morphological paradigm display
- Orthographic realization as a first-class layer (not a footnote)
- Timeline of attestations by period
- Cross-language links with relationship types (equivalent, cognate, loan, calque)
- Interpretation panel showing competing scholarly readings with confidence and sources

**Result view:** Rich dictionary entry card with collapsible sections for morphology, spellings, attestations, and scholarly discussion.

---

## Paleographic Strategy

A layered approach, built progressively:

| Layer | Description | Priority |
|-------|-------------|----------|
| **Unicode + OGSL** | Canonical sign IDs with standard codepoints | **Baseline — build first** |
| **Component decomposition** | Wedge-stroke descriptions with positional encoding (from OGSL) for structural and fuzzy search | **Baseline — build first** |
| **Period/script-type tags** | Metadata tagging each sign variant by period (Ur III, OB, NA, NB/LB) and script type (monumental, cursive) | **Baseline — build first** |
| **SVG vector forms** | Vector drawings of sign variants per period, sourced from published paleographies and CDLI | **Phase 2 — progressive enhancement** |
| **Photographic references** | Links to CDLI tablet images showing sign in situ | **Phase 2 — progressive enhancement** |
| **Drawn/image input** | Visual sign lookup by sketch or photo upload | **Phase 3 — advanced feature** |

---

## API Architecture

### REST — Simple Lookups

```
GET  /signs/{id}                          → Sign with all readings
GET  /signs/{id}/readings?period=OB&lang=akk  → Filtered readings
GET  /lemmas/{id}                         → Full dictionary entry
GET  /lemmas?q=šarrum&lang=akk            → Search lemmas
GET  /concepts/{id}                       → Semantic node with linked lemmas
GET  /search?q=lugal                      → Cross-entity search
GET  /interpretations?target={lemma_id}   → Competing readings for an entry
```

### GraphQL — Complex Scholarly Queries

For traversals REST cannot express cleanly:

- "All Hittite words written logographically with Sumerian signs, in the RITUAL domain, with Akkadian equivalents"
- "All signs that have both a Sumerian logographic and an Akkadian syllabic reading, attested in OB period"
- "Lemmas with contested interpretations where confidence < 0.5"

### Linked Data (RDF/JSON-LD)

For interoperability with the broader digital humanities ecosystem:

- Link to **Wikidata** for entities (rulers, cities, deities)
- Link to **Pleiades** for ancient place names
- Link to **VIAF** for ancient authors and modern scholars
- Enable SPARQL queries for semantic web researchers

### Agent / MCP Integration

Structured JSON responses optimized for LLM consumption, enabling:
- Cuneiform translation agents that query the dictionary mid-workflow
- Automated lemmatization pipelines
- Research assistants that cross-reference interpretations

---

## UI Architecture — Exploratory Interface

### Primary Views

1. **Sign Browser** — Grid or list of signs with visual variants, filterable by period, component count, reading count. Click-through to full sign detail with all readings and linked words.

2. **Dictionary View** — Traditional alphabetical/lemma browsing per language, with powerful search (transliteration, normalized form, English gloss). Each entry is a rich card with morphology, spellings, attestations, and interpretations.

3. **Concept Explorer** — Visual/browsable semantic ontology. Select a domain, see all four languages side by side. Highlight logographic bridges and semantic drift across languages.

4. **Cross-Reference Graph** — Interactive visualization of relationships between signs, words, and concepts. Navigate the knowledge graph visually. Useful for exploring how a single sign connects to dozens of words across four languages.

5. **Interpretation Tracker** — Surface where competing scholarly readings are visible. Filter by confidence level, recency, or source. Enables the dictionary to function as a map of current knowledge rather than a single-authority reference.

### Search Paradigm

A unified search bar that routes intelligently:
- Detects Unicode cuneiform → routes to Sign view
- Detects transliteration patterns (hyphens, subscript numbers) → routes to Lemma view
- Detects plain English → routes to Concept view
- Detects MZL/Labat numbers → routes to Sign view
- Supports explicit filters: `lang:hit`, `period:OB`, `pos:V`, `confidence:>0.7`

---

## Open Questions

| Question | Impact |
|----------|--------|
| **Semantic ontology source:** Build from scratch? Adapt Louw-Nida domains? Use WordNet synset structure? | Defines the Concept layer; hardest piece with least precedent |
| **Collaboration model:** Open wiki-style editing or curated editorial process? | Shapes versioning, attribution, and trust architecture |
| **Language prioritization:** Build full 4-language architecture and populate unevenly, or start Sum+Akk? | Determines MVP scope and timeline |
| **Tech stack:** Graph DB (Neo4j, etc.) vs. relational + search (Postgres + Elasticsearch)? | Shapes API performance and query flexibility |
| **MVP definition:** Target scope for a demonstrable first milestone (e.g., 100 signs × 500 lemmas × 4 languages) | Critical for attracting collaborators and funding |
| **Nonprofit structure:** Timeline and relationship to this project | Affects licensing, governance, and partnership strategy |

---

## Recommended Next Steps

1. **Audit OGSL + ePSD2 data quality** — These are your most complete open foundations. Understand their schemas deeply before designing yours.
2. **Investigate ISAC/CAD digitization format** — The CAD data is the single highest-value Akkadian source. Determine what structured access is available or forthcoming.
3. **Define the semantic ontology approach** — This is the most novel and least precedented component. A small prototype (50 concepts, mapped across Sum + Akk) would validate the concept.
4. **Build a schema prototype** — Model 100 signs with full reading/lemma/concept links across all four languages in a graph or relational schema. Test the three access patterns against it.
5. **Design the interpretation data model** — Get this right early; retrofitting scholarly uncertainty is much harder than building it in from the start.