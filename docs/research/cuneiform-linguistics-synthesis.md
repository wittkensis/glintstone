---
question: "What do we collectively know about the four cuneiform languages, the script's evolution, the loanword network, and the state of decipherment — at the depth needed for schema design?"
created: 2026-05-11
modified: 2026-05-11
context: "Synthesized from three independent research outputs (Claude, Gemini, Grok) commissioned to answer the same comparative-typology question from different angles. The three originals approached it as: a multilingual-comparison tutorial (Claude), an academic-formal report with citations (Gemini), and a concise enumerated analysis with schema design ideas (Grok). This file extracts the converged consensus plus the additions each agent contributed, in a form usable by engineers and scholars alike. The shorter, schema-decision-focused version lives in .claude/skills/gs-expert-assyriology/comparative-typology.md."
status: active
audience: [scholars, engineers, claude]
owners: [eric]
related_issues: []
related_skills: [gs-expert-assyriology, gs-expert-data-model]
supersedes: ["PLAN/Linguistics Schema/v2/Phase 1/Linguistics Schema Research (Claude).md", "PLAN/Linguistics Schema/v2/Phase 1/Linguistics Schema Research (Gemini).md", "PLAN/Linguistics Schema/v2/Phase 1/Linguistics Schema Research (Grok).md"]
superseded_by: null
---

# Cuneiform linguistics — synthesis

A reference for scholars and engineers. Synthesized from three independent agent outputs that answered the same comparative-typology question from different angles. Read this when you want depth; the skill version (`gs-expert-assyriology/comparative-typology.md`) is the operational cheat sheet.

## 1. Frame: a script, not a language

Cuneiform was invented by Sumerian speakers in southern Mesopotamia around 3200 BCE, originally as proto-pictographic accounting tokens on clay. Over ~3,000 years it was adapted to record at least four genetically unrelated languages: Sumerian (isolate), Akkadian (East Semitic), Hittite (Indo-European, Anatolian branch), and Elamite (isolate). The script outlived its progenitor language: Sumerian died as a spoken language ~1800 BCE but persisted as a scholarly and liturgical medium until ~100 CE, much as Latin did in medieval Europe.

The analogy to Latin alphabet usage across English, Turkish, Vietnamese, and Swahili is apt: the script is shared, but the underlying linguistic machinery is radically different in each case. The script's polyvalency (one sign, many readings) is itself a record of this multilingualism — Sumerian readings, Akkadian readings, syllabic values, and logographic uses coexist within a single signary.

## 2. Sumerian — agglutinative isolate

### Morphology

Agglutinative. Morphemes attach in chains; the verbal template is roughly:

```
[modal] – [conjugation] – [ventive/ientive] – [dimensional] – [person] – STEM – [person] – [pronominal]
```

A Sumerian verb such as *mu-n-na-ab-sum* "he gave it to him" parses slot-by-slot:

- **mu-** — ventive (motion toward speaker / discourse anchor)
- **n-** — 3sg.IO dative
- **na-** — 3sg.human.IO allative
- **b-** — 3sg.neuter.DO
- **sum** — give (stem)

Noun phrases are head-first: `lugal kalam-ma-k` = "king-of-the-land", possessor follows possessed (analogous to Japanese `の` constructions).

### Alignment

**Ergative-absolutive**, the most consequential structural fact. The agent of a transitive verb takes the ergative marker `-e`; the patient of a transitive AND the subject of an intransitive are both absolutive (unmarked):

- *lugal-e e₂-Ø mu-n-du₃* — "the king(ERG) built the house(ABS)"
- *lugal-Ø dur₂-ru-na* — "the king(ABS) sat down"

The king is marked differently depending on whether he is doing something *to* something or simply existing/acting. This is structurally identical to ergative patterns in Basque, Inuit, and Yup'ik.

### Noun class

Personal vs impersonal (human/divine vs animals/objects). Plural marker `-ene` for personal class.

### Scholarly status

Strong but contested. Jagersma 2010 is the modern reference grammar; Zolyomi and Edzard offer alternative analyses of the prefix slot system. The disagreement is genuine and unresolved — multiple framework analyses can validly coexist for the same Sumerian text.

### Schema implication

Don't compress the verbal chain into a single morph string. Store slot-by-slot, or preserve the ORACC string and parse on render. The `morphology` table must support multiple competing parses keyed to `annotation_run_id`.

## 3. Akkadian — Semitic root-and-pattern

### Morphology

Triconsonantal roots with internal vowel ablaut and stem augments. The root `b-n-y` "build" surfaces as:

- *ibnī* — G-stem preterite "he built"
- *ibtanī* — Gtn iterative "he kept building"
- *ubnī* — Š causative "he had built"
- *bītum* — noun "house" derived from the same root
- *bāniyum* — agent noun "builder"

This is structurally identical to Arabic *b-n-y* → *banā* "he built", *binā'* "building", *mabnā* "structure", and to the Hebrew *b-n-h* → *banah*.

### Stems (binyanim)

G (basic), D (intensive), Š (causative), N (passive), plus t-infixed variants Gt, Gtn, Dt, etc. The system maps almost directly onto the Arabic Forms I–X. Akkadian scribes catalogued the stem system in bilingual paradigms.

### Alignment

**Nominative-accusative** (unlike Sumerian). Three cases: nominative `-um`, accusative `-am`, genitive `-im`. Case endings (and the case system itself) erode in Neo-Babylonian and Neo-Assyrian — paralleling the loss of case in spoken Arabic.

### Word order

Predominantly **SOV**, an adoption from Sumerian. Subordinate clauses are consistently verb-final. Some poetic registers show VSO tendencies.

### Construct state

Identical to Arabic *idāfa*: `bīt šarrim` "house of the king" = `house-CONSTRUCT king-GEN`, where the head noun is in the construct state (no case ending) and the dependent in the genitive.

### Dialects

A first-class schema dimension, not a footnote:

| Dialect | Period | Region | Notes |
|---|---|---|---|
| Old Akkadian | ~2500–1950 BCE | Akkad | Earliest stage |
| Old Babylonian | ~1950–1530 BCE | South | Literary classical standard |
| Old Assyrian | ~1950–1750 BCE | North | Trader colonies in Anatolia |
| Middle Babylonian | ~1530–1000 BCE | South | Kassite period |
| Middle Assyrian | ~1500–1000 BCE | North | Empire expansion |
| Neo-Babylonian | ~1000–600 BCE | South | Chaldean / Neo-Babylonian empire |
| Neo-Assyrian | ~1000–600 BCE | North | Empire administration |
| Late Babylonian | ~600 BCE – 100 CE | South | Last living phase |

Neo-Assyrian features vowel harmony, loss of case endings, and analytical constructions — these aren't dialect-accent differences but full grammatical drift. Track dialect on every lemma and every annotation.

## 4. Hittite — Indo-European with heterography

### Morphology

Fusional / inflecting, like German. Two genders (common and neuter — archaic IE without the masculine/feminine split). Extensive case system: nominative, accusative, genitive, dative-locative, ablative, instrumental, allative, vocative.

Two verb conjugations:
- *-mi* conjugation (the "normal" IE one)
- *-ḫi* conjugation (unique to Hittite; reflects a very archaic stative/perfect; cognate possibly to the IE perfect)

### Word order and Wackernagel's Position

**SOV**, similar to German subordinate clauses. The defining clause-level feature is **Wackernagel's Position**: enclitic particles (pronouns, reflexives, local particles) stack in a fixed order after the first stressed word of the clause. The introductory particle *nu* often serves as the anchor:

```
nu=ššan  LUGAL-uš  É.GAL=an   iyat
nu=PTC   king-NOM  palace=ACC build.3SG.PRET
"And the king built the palace."
```

The clitic chain `=ššan` attaches to *nu*, not to the verb.

### Heterography — three writing systems in one text

A single Hittite text routinely mixes:
- **Hittite** phonetic spellings (in italics in transliteration)
- **Sumerograms** — Sumerian words used as logograms for Hittite words (UPPERCASE: `LUGAL` for `ḫassuš` "king")
- **Akkadograms** — Akkadian words used as logograms (ITALIC UPPERCASE: `ANA` for "to", `ŠA` for "of")
- **Determinatives** — silent classifiers (`{d}`, `{m}`, `{ki}`)
- **Phonetic complements** — small syllabic signs attached to logograms to mark the underlying Hittite ending (`LUGAL-uš` = nominative singular *ḫassus*)

Example: `LUGAL-uš ANA DINGIR-LIM SISKUR iyazi`
- `LUGAL-uš` = Sumerogram + Hittite NOM ending → *ḫassuš* "the king"
- `ANA` = Akkadian preposition used logographically
- `DINGIR-LIM` = Sumerogram + Akkadogram complement → *šiwannī* "to the god"
- `SISKUR` = Sumerogram → some Hittite ritual term
- `iyazi` = Hittite verb "makes"

Only *iyazi* (and the Hittite endings on the logograms) is phonetically Hittite. This is **the rule, not the exception** in Hittite texts.

### Schema implication

Hittite is the language where the graphemic / linguistic split is widest. The schema's three-layer model (graphemic / linguistic / semantic) must be honored fully. `tokens.surface_form` (what was written) is separate from `lemmatizations.lemma_id` (what was meant) is separate from `glossary_senses` (the conceptual content). A token's surface might be Sumerian, its lemma Hittite, its sense English.

## 5. Elamite — agglutinative class system

### Morphology

Agglutinative. The defining feature is a pervasive **noun-class system** with three classes based on the relationship to the speech act:

- **Locutive** (1st person) — marked `-k`
- **Allocutive** (2nd person) — marked `-t`
- **Delocutive** (3rd person) — `-r` (animate sg), `-p` (animate pl), `-me` (inanimate)

### Suffixaufnahme

Adjectives and genitive modifiers take the class marker of their head noun. In `sunki-k GN-k` = "I, the king of GN", the locutive marker `-k` is doubled onto both the noun `sunki` "king" AND the city name, because the speaker (1st person) is the subject of the apposition.

This is analogous to Caucasian and Hurro-Urartian patterns but operates on a deeper class system.

### Periods

| Period | Range | Notes |
|---|---|---|
| Old Elamite | ~2600–1500 BCE | Very sparsely attested |
| Middle Elamite | ~1500–1000 BCE | Royal inscriptions; best-attested phase |
| Neo-Elamite | ~1000–550 BCE | Transitional |
| Achaemenid Elamite | ~550–330 BCE | Administrative language of the Persian Empire; Persepolis Fortification Archive; heavily Old-Persian-influenced, possibly a bureaucratic pidgin rather than natural speech |

### Scholarly status

Improving. Recent breakthroughs in **Linear Elamite** (a parallel non-cuneiform script, ~2000 BCE; François Desset et al.) are starting to back-fill Cuneiform Elamite understanding. The corpus is small, dependencies on Old Persian are heavy in the Achaemenid period, and many readings remain genuinely uncertain.

### Schema implication

Confidence scores aren't a nicety — they're load-bearing. The `morphology` table must support partial / uncertain readings. Class markers should be stored as a separate feature, not baked into the lemma form.

## 6. Polyvalency — the script-wide reality

A single cuneiform sign typically encodes:
- Multiple **logographic** readings (whole words)
- Multiple **syllabic** values (CV, VC, CVC sequences)
- Functions as a **determinative** (silent classifier)

And these vary by language, period, and context.

### Case study: AN (𒀭)

| Sign | Sumerian | Akkadian | Hittite | Elamite |
|---|---|---|---|---|
| **AN** | `an` "sky", `dingir` "god" | `šamû` "heaven", `ilu` "god", syllable `an` | divine determinative | syllable `an` |
| **KUR** (𒆳) | `kur` "mountain, foreign land" | `šadû` "mountain", `mātu` "land", syllables `kur`/`mad`/`šad` | "country / land" (with phonetic complement for case) | — |
| **UD** (𒌓) | `ud` "day, sun" | `ūmu` "day", syllables `ud`/`tam`/`tú`/`par`/`laḫ` | "day" | syllable `ut` |
| **DU** (𒁺) | `du` "go", `gub` "stand" | syllables `du`/`rá`/`gub` | "go" | syllable `du` |

This polyvalency drives the schema's separation between `tokens` (a particular wedge group on a tablet), `token_readings` (the candidate phonological realizations), and `lemmatizations` (the dictionary entries those readings can map to).

Compare to Chinese characters in Japanese (kanji + kana) or Arabic script in Persian: highly adaptable but polyvalent and context-dependent.

## 7. The loanword network

### Sumerian → Akkadian — the dominant direction

Estimated 20–30% of Akkadian vocabulary in administrative, religious, and technical domains. Examples:

| Sumerian | Akkadian | Meaning |
|---|---|---|
| `dubsar` (DUB.SAR) | `ṭupšarru` | scribe (lit. "tablet-writer") |
| `engar` | `ikkaru` | farmer |
| `nagar` | `naggāru` | carpenter |
| `é-gal` | `ekallu` | palace (lit. "great house") |
| `abzu` | `apsû` | abyss |
| `nam-tar` | `namtaru` | fate; fate demon |
| `gal` | `gallu` | "great" → "demon" (semantic shift in Akkadian) |
| `saĝĝa` | `šangû` | temple administrator |

The direction tells you something about cultural prestige: Sumerian was the "high culture" language, so technical and administrative vocabulary flowed up the prestige gradient.

### Akkadian as Late Bronze Age lingua franca

The Amarna Letters (14th c. BCE) document Akkadian as the diplomatic language of Egypt, Hatti, Babylon, Assyria, and their vassals. From this period:

- *ṭuppu* "tablet" → Hittite *tuppi-*, Elamite *tup-pi*
- *ḫazannu* "mayor / town leader" → Hittite *ḫazannu-*

But most "Akkadian influence" in Hittite is **logographic, not phonetic** — Hittite scribes wrote Akkadian words as logograms and pronounced them in Hittite.

### "Banana Language" substrate

Pre-Sumerian / pre-Akkadian personal names with reduplicated final syllables — `Bunene`, `Zababa`, `Inana` — suggest an unidentifiable substrate language possibly shared between Sumerian and Elamite. The hypothesis explains why certain etymologies are flatly unrecoverable.

### Wanderwörter

Some words appear across multiple languages without clear directionality. Examples include certain plant, animal, and technology names; some divine names; the root `ḫul/ḫūlu` "evil/bad" appears in Sumerian, Akkadian, and possibly Elamite forms. These may be areal Sprachbund features.

### Schema implication

An etymology / cognate layer is essential. A lemma entry should be able to link to cognates and loans across all four languages, with directionality (if known), semantic shift, and confidence level. Many etymologies are genuinely disputed; the model must not pretend otherwise.

## 8. Determinatives — silent classifiers

Determinatives are signs that classify but aren't pronounced. ATF transcription puts them in `{...}`:

| Determinative | Class | Example |
|---|---|---|
| `{d}` (DINGIR) | divine | `{d}UTU` = the god Shamash |
| `{m}` / `{lu2}` | male personal name | `{m}ŠARRU-KĪN` = Sargon |
| `{f}` / `{munus}` | female personal name | `{f}IŠTAR-...` |
| `{ki}` | place name (city) | `Nibru{ki}` = Nippur |
| `{kur}` | foreign land / mountain | `{kur}elam{ki}` = Elam |
| `{giš}` | wooden object | `{giš}gigir` "chariot" |
| `{kuš}` | leather | |
| `{na4}` | stone | |
| `{uruda}` | copper | |
| `{tug2}` | textile | |

Determinatives are crucial for **named-entity recognition** and **disambiguation**. A search for "place names containing X" is a query over determinative-tagged tokens. Schema-wise, they belong as metadata on a token, not as separate tokens.

## 9. Lexical lists, paradigms, and ancient scholarship

Cuneiform was preserved through millennia in part because the scribes built their own scholarly apparatus. Standardized lists like *Ea* and *Diri* provided four-column mappings:

1. Phonetic gloss of the Sumerian word
2. Sign form
3. Sign name
4. Akkadian translation

These are essentially the world's first dictionaries. They are also the foundation of every modern decipherment: bilingual Sumerian-Akkadian lexical lists are how Sumerian was deciphered (after Akkadian had been read by analogy with Hebrew and Arabic).

The *Edubba* ("House of Tablets"), the scribal school, drilled students for ~12 years on copying lexical lists and literary works. Scribes were a privileged elite, often more powerful than the illiterate monarchs they served.

## 10. Cuneiform's evolution

| Phase | Date | Characteristics |
|---|---|---|
| Proto-literate (Uruk IV) | ~3100–3000 BCE | Pictographs on tokens; accounting primarily |
| Archaic Sumerian | ~3000–2500 BCE | Rotated 90° (around 2800 BCE); wedge-shaped marks emerge |
| Sumero-Akkadian | ~2500–2000 BCE | Phoneticization via the rebus principle to accommodate Akkadian |
| Regional diversification | ~2000–1000 BCE | Divergent ductus (handwriting styles); Assyrian linear, Hittite Old-Babylonian-derived |
| Achaemenid Elamite | ~550–330 BCE | Reduced to ~131 signs, near-alphabetic, almost no polyvalency |
| Late survival | ~330 BCE – 100 CE | Astronomical and ritual texts in Babylonian |

Sign count over time: Uruk IV ~1,500 (purely logographic); Ur III ~600 (balanced logo-syllabic); Neo-Assyrian ~570-800 (standardized polyphony); Hittite ~375 (high Sumerogram density); Achaemenid Elamite ~131 (simplified).

## 11. Decipherment story

Cuneiform decipherment proceeded via **trilingual inscriptions**:

- **Bisitun inscription** (Old Persian + Elamite + Babylonian) — the Rosetta Stone equivalent for cuneiform. Old Persian was deciphered first (simpler script, known descendants). Akkadian came next via the Babylonian column. Elamite came last.
- **Boğazköy archives** — ~30,000 Hittite tablets discovered at the capital Hattusa; Bedřich Hrozný confirmed Hittite as Indo-European in 1915.
- **Sumerian-Akkadian bilinguals** — the lexical-list tradition let scholars work backward from Akkadian to Sumerian.

This history is why the schema has to treat bilingual / trilingual texts as first-class: they ARE the foundation of the field, not edge cases.

## 12. State of understanding (today)

- **Akkadian** — excellent. Von Soden's *GAG* is canonical; the corpus is huge. Challenges: dialect variation, damaged tablets.
- **Sumerian** — strong (Jagersma 2010), but the verbal prefix system has genuine open questions. Different analyses (Jagersma, Zolyomi, Edzard) coexist.
- **Hittite** — strong (Hoffner, Melchert). Challenges: clitic chain analysis at clause level; logogram-heavy texts hide Hittite phonology.
- **Elamite** — improving. Recent Linear Elamite decipherment (Desset and others) is beginning to back-fill cuneiform Elamite. Small corpus; Achaemenid Old Persian influence distorts.

## 13. What this means for Glintstone

Distilled implications for the schema and the parser:

1. **Multi-source provenance is structural.** Every linguistic claim is contestable. `annotation_run_id` carries who/when/what version.
2. **The graphemic / linguistic / semantic split is real.** Hittite forces it; the schema benefits from honoring it for every language.
3. **Polyvalency means tokens ≠ readings.** A token can have many candidate readings; readings can map to many lemmas; lemmas can have many senses.
4. **Slot-based morphology for Sumerian; root-pattern for Akkadian; inflecting for Hittite; class-based for Elamite.** The `morphology` table must support all four shapes.
5. **Dialect is a first-class dimension.** Especially for Akkadian.
6. **Determinatives are metadata.** Token-level, never independent words.
7. **Bilingual / trilingual texts are foundational, not edge cases.** Token-level language switching is normal.
8. **Confidence and disagreement are first-class data.** Especially for Elamite and for the contested parts of Sumerian morphology.
9. **The loanword / cognate / etymology layer needs to exist.** Sumerian → Akkadian alone is ~20–30% of administrative vocabulary.
10. **The Sumero-Akkadian lexical tradition is the field's foundation.** Lexical-list ingestion is part of the data model, not a side feature.

## References (live)

- Jagersma, A. H. *A Descriptive Grammar of Sumerian*. PhD diss., Leiden 2010.
- Huehnergard, J. *A Grammar of Akkadian*. 3rd ed. Eisenbrauns 2011.
- Hoffner, H. A. & H. C. Melchert. *A Grammar of the Hittite Language*. Eisenbrauns 2008.
- Stolper, M. W. "Elamite". In Woodard, R. D., ed. *The Cambridge Encyclopedia of the World's Ancient Languages*. CUP 2004.
- ETCSL — Electronic Text Corpus of Sumerian Literature. http://etcsl.orinst.ox.ac.uk
- ORACC — http://oracc.museum.upenn.edu
- ePSD2 — http://oracc.org/epsd2

## Provenance of this synthesis

This file is a consensus distillation from three independently-commissioned research outputs (Claude, Gemini, Grok) answering the same question — "What do the four cuneiform languages share, where do they differ, and what should our schema track?" Each angle contributed:

- The pedagogical multilingual-analogy framing (German → Hittite, Japanese → Sumerian, Arabic → Akkadian, Mandarin → cuneiform-as-script)
- The detailed comparative-typology tables and the "Sign-Topology Folding" framing
- The "AlphaFold for cuneiform" framing and the concise schema-action items

Where the three diverged: minor differences in transliteration conventions (handled by preferring the ATF / OGSL standard), and confidence on speculative Wanderwörter (this synthesis flags speculation explicitly).

The originals lived in `PLAN/Linguistics Schema/v2/Phase 1/` and are archived (committed to git history then removed) as part of the 2026-05-11 knowledge architecture overhaul.
