# Cuneiform Languages: A Comparative Tutorial for Data Schema Design

## Preamble: What You're Actually Dealing With

Before anything else, understand this: **cuneiform is not a language. It's a writing system** — a technology that was adopted, adapted, and repurposed by speakers of radically different languages over roughly 3,000 years (c. 3400 BCE – 75 CE). The relationship between cuneiform and the languages that used it is analogous to the Latin alphabet being used for English, Turkish, Vietnamese, and Swahili. The script is shared; the underlying linguistic machinery is not.

The four languages you've named span:

| Language | Family | Type | Approx. Period | Primary Regions |
|----------|--------|------|-----------------|-----------------|
| **Sumerian** | Isolate (no known relatives) | Agglutinative, ergative-absolutive | c. 3500–2000 BCE (spoken); used as scholarly language until ~100 CE | Southern Mesopotamia (modern southern Iraq) |
| **Akkadian** (incl. Assyrian & Babylonian dialects) | Semitic (Afroasiatic) | Fusional, nominative-accusative | c. 2800–100 BCE | All of Mesopotamia, spreading to Syria, Anatolia, Egypt (diplomatic) |
| **Hittite** (Nesite) | Indo-European (Anatolian branch) | Fusional with agglutinative features | c. 1650–1178 BCE | Central Anatolia (modern Turkey) |
| **Elamite** | Isolate (debated connections to Dravidian) | Agglutinative | c. 2600–330 BCE | Southwestern Iran (Khuzestan, Fars) |

Your multilingual background is directly useful here:
- **German** → will help you with Hittite (both Indo-European; case systems, verb-final tendencies)
- **Japanese** → closest structural analogy to Sumerian (SOV, agglutinative, postpositions, topic-marking)
- **Arabic** → directly relevant to Akkadian (Semitic triconsonantal root system, case endings, verbal templates)
- **Mandarin** → useful for understanding logographic principles in the cuneiform sign system itself

---

## 1. Sentence Structures

### 1.1 Sumerian: The Japanese Analogy

Sumerian is **SOV** (Subject–Object–Verb) and **agglutinative**, meaning grammatical information is stacked onto words as a chain of affixes. If you speak Japanese, you are already close to the right mental model.

**Example:**
```
lugal-e     e₂-Ø      mu-n-du₃
king-ERG    house-ABS  VENT-3SG.A-build
"The king built the house."
```

Key structural features:
- **Ergative-absolutive alignment**: This is the single most important structural fact. Unlike nominative-accusative languages (English, Akkadian, Hittite), Sumerian treats the subject of a transitive verb differently from the subject of an intransitive verb. The *agent* of a transitive verb gets the ergative case marker **-e**, while the *patient* and intransitive subjects are unmarked (absolutive).
  - Think of it this way: "The king (ERG) built the house (ABS)" vs. "The king (ABS) sat down" — the king is marked differently depending on whether he's *doing something to something else* or just *existing/acting alone*.
- **Verbal chain**: The Sumerian verb is a complex of prefixes and suffixes encoding person, number, transitivity, tense/aspect, subordination, and more. The verbal template is roughly: `modal prefixes – conjugation prefix – ventive/ientive – dimensional prefixes – person markers – STEM – person suffixes`.
- **Postpositions**, not prepositions: `e₂-a` = "in the house" (house-LOC). Just like Japanese の, に, で, etc.
- **Noun chains (genitive)**: `lugal kalam-ma-k` = "king of the land" (king land-GEN). Possessor follows possessed, like Japanese の constructions.
- **No grammatical gender**.
- **Two noun classes**: human (sometimes called "animate") and non-human, which affect pronoun and verb agreement patterns.

**For your schema**: Sumerian morphology requires storing a rich set of prefix/suffix chains on the verb. Each verbal element occupies a specific "slot" in the template. Your data model needs to represent a **slot-based morphological template** for Sumerian verbs, not just "root + inflection."

### 1.2 Akkadian (Assyrian/Babylonian): The Arabic Analogy

Akkadian is **Semitic**, so your Arabic is directly applicable. It uses a **triconsonantal root system** where meaning is encoded in (usually) three consonants, and vowel patterns + affixes convey grammatical categories.

**Example:**
```
šarrum       bītam       ibnī
šarr-um      bīt-am      i-bni-Ø
king-NOM     house-ACC    3M.SG-build.PRET-Ø
"The king built the house."
```

Key structural features:
- **Word order**: Predominantly **SOV** in earlier periods, with **VSO** tendencies in certain clause types (like Arabic). Subordinate clauses are consistently verb-final.
- **Nominative-accusative alignment**: Unlike Sumerian. Subjects take nominative (-um), direct objects take accusative (-am), indirect objects/possessive take genitive (-im).
- **Root-and-pattern morphology**: The root *b-n-y* (to build) appears in:
  - *ibnī* (he built) — G-stem preterite
  - *ibtanī* (he kept building) — Gtn iterative
  - *ubnī* (he had (someone) build) — Š causative
  - *bītum* (house) — noun derived from same root
  - Compare Arabic: *b-n-y* → *banā* (he built), *binā'* (building), *mabnā* (structure)
- **Verbal stems (binyanim)**: G, D, Š, N, plus t-infixed variants (Gt, Dt, Št, etc.) — exactly analogous to Arabic Forms I–X.
- **Three cases**: nominative, accusative, genitive (lost in later periods — Neo-Assyrian/Neo-Babylonian drop mimation and case endings, paralleling the loss of case in spoken Arabic).
- **Two grammatical genders**: masculine and feminine.
- **Bound/construct state**: `bīt šarrim` = "house of the king" (house.CONST king.GEN). Identical to Arabic *idāfa*: بيت الملك.

**Dialects matter for your schema:**
- **Old Akkadian** (c. 2500–1950 BCE)
- **Old Babylonian** / **Old Assyrian** (c. 1950–1530 BCE) — OB is the "classical" literary standard
- **Middle Babylonian** / **Middle Assyrian** (c. 1530–1000 BCE)
- **Neo-Babylonian** / **Neo-Assyrian** (c. 1000–600 BCE)
- **Late Babylonian** (c. 600 BCE – 100 CE)

These aren't just accent differences — they involve significant phonological, morphological, and syntactic changes. Neo-Assyrian, for instance, has undergone vowel harmony, lost case endings, and developed analytical constructions. Your schema **must** capture dialect/period as a first-class dimension.

### 1.3 Hittite: The Indo-European Surprise

Hittite was the first known Indo-European language to be deciphered (by Bedřich Hrozný, 1915). Your German gives you an entry point.

**Example:**
```
LUGAL-uš    É-an         iyat
hassu-š     parn-an      iyat
king-NOM    house-ACC    make.3SG.PRET
"The king built the house."
```

Key structural features:
- **SOV word order** (like German subordinate clauses: "...dass der König das Haus baute").
- **Nominative-accusative alignment** with an **extensive case system**: nominative, accusative, genitive, dative-locative, ablative, instrumental, allative, vocative. Compare German's four cases, but more.
- **Two genders**: common and neuter (not masculine/feminine — archaic IE feature).
- **Verb conjugation**: Present/future and preterite; two conjugation classes (-mi and -ḫi verbs). The -ḫi conjugation is unique among IE languages and may reflect a very archaic stative/perfect.
- **Enclitic chain**: Hittite stacks enclitic particles after the first stressed word of a clause (Wackernagel's Law). This is similar to what you see in some analyses of Japanese particle chains, but operates at the clause level.
- **Heavy use of Sumerograms and Akkadograms**: This is crucial for your schema. Hittite scribes wrote many words using Sumerian logograms (LUGAL for "king" instead of the Hittite word *ḫassus*) or Akkadian logograms (sometimes with Hittite phonetic complements). A single Hittite text can contain three languages simultaneously at the sign level.

**Example of mixed writing:**
```
Written:  LUGAL-uš  A-NA  DINGIR-LIM  SISKUR  iyazi
Read as:  ḫassu-s   ... (to) siuni-    ... (offering) iyazi
Meaning:  "The king makes an offering to the god."
```
Where LUGAL = Sumerian logogram, A-NA = Akkadian preposition used as logogram, DINGIR = Sumerian determinative/logogram, SISKUR = Sumerian logogram, and only *-uš* and *iyazi* are phonetically Hittite.

**For your schema**: Any Hittite data model must handle **multilingual writing** as a core feature, not an edge case. A single "word" in a Hittite text may be a Sumerian logogram with a Hittite phonetic complement. You need to separate the *graphemic layer* (what's written) from the *linguistic layer* (what's spoken) from the *semantic layer* (what's meant).

### 1.4 Elamite: The Understudied Outlier

Elamite is the least understood of the four. It's a language isolate with possible (highly debated) distant connections to Dravidian languages.

**Example (Middle Elamite):**
```
sunki-k     hiya-n       hutta-h-š
king-AGENT  house-ACC?   make-3SG-3SG.OBJ
"The king built the house."
```

Key structural features:
- **SOV word order**.
- **Agglutinative** morphology, like Sumerian but with different mechanics.
- **Complex pronoun/agreement system**: Verbs agree with both subject and object, using suffix chains.
- **No grammatical gender** in the traditional sense, but a distinction between "divine/human" and "non-human" in some periods.
- **Three major periods** with significantly different grammar:
  - **Old Elamite** (c. 2600–1500 BCE) — very poorly attested
  - **Middle Elamite** (c. 1500–1000 BCE) — most substantial corpus (royal inscriptions)
  - **Neo-Elamite** (c. 1000–550 BCE) — transitional
  - **Achaemenid Elamite** (c. 550–330 BCE) — used as administrative language of the Persian Empire; most texts from Persepolis tablets
- Achaemenid Elamite is heavily influenced by Old Persian and may represent a bureaucratic pidgin rather than natural speech.

**For your schema**: Elamite poses a **data sparsity problem**. Your model must handle high uncertainty — many signs and words have debated or unknown meanings. Confidence scores on readings and translations are essential, not optional.

---

## 2. Shared Words (Loanwords and Wanderwörter)

### 2.1 Sumerian → Akkadian (massive borrowing in both directions)

This is the single most important lexical relationship in your dataset. Sumerian and Akkadian coexisted for over a millennium in southern Mesopotamia, producing intense mutual borrowing.

**Sumerian → Akkadian loans:**
| Sumerian | Akkadian | Meaning | Notes |
|----------|----------|---------|-------|
| *agar/agar₅* | *ugāru* | field, meadow | Agricultural terminology |
| *apin* | *epinnu* | plow | |
| *dubsar* (DUB.SAR) | *ṭupšarru* | scribe | Lit. "tablet-writer" |
| *engar* | *ikkaru* | farmer | |
| *gal* | *gallu* | great; demon | Semantic shift in Akkadian! |
| *ḫal* | *ḫallu* | crotch, upper thigh | |
| *kur* | *mātu* (not a loan, but KUR used logographically) | land, mountain | |
| *nam-tar* | *namtaru* | fate; a fate demon | |
| *saĝĝa* | *šangû* | temple administrator | |
| *šagan* | *šaknu* | governor | |
| *nagar* | *naggāru* | carpenter | |

**Akkadian → Sumerian loans (fewer but significant):**
| Akkadian | Sumerian borrowing | Meaning |
|----------|-------------------|---------|
| *māḫiru* | *maḫir* | market price, exchange rate |
| *damqum* | *damqi* | good, fine |

The directionality tells you something about cultural prestige: Sumerian was the "high culture" language, so technical, religious, and administrative vocabulary flowed from Sumerian to Akkadian. Akkadian commercial terms sometimes flowed back.

### 2.2 Akkadian as Lingua Franca → Hittite and Elamite

Akkadian served as the diplomatic *lingua franca* of the Late Bronze Age (c. 1400–1200 BCE). The Amarna Letters — correspondence between Egypt, Hatti, Babylon, Assyria, and vassal states — are written in Akkadian.

**Akkadian → Hittite loans:**
| Akkadian | Hittite | Meaning |
|----------|---------|---------|
| *ṭuppu* | *tuppi-* | tablet |
| *šarru* | (used logographically as LUGAL, not borrowed phonetically) | king |
| *ḫazannu* | *ḫazannu-* | mayor, town leader |

However, most "Akkadian influence" in Hittite is **logographic**, not phonetic. Hittite scribes wrote Akkadian words as logograms but pronounced them in Hittite.

**Akkadian → Elamite loans (Achaemenid period):**
| Akkadian | Elamite | Meaning |
|----------|---------|---------|
| *ṭuppu* | *tup-pi* | tablet |
| Various administrative terms | adapted with Elamite morphology | |

### 2.3 Substrate and Wanderwörter

Some words appear across multiple languages without clear borrowing direction — these may be areal features or from an unknown substrate:
- Words for certain local plants, animals, and technologies
- Some place names and divine names
- The word *ḫul* / *ḫūlu* (evil/bad) appears in forms across Sumerian, Akkadian, and possibly Elamite

**For your schema**: You need a **loanword/etymology layer** that tracks: source language, target language, directionality (if known), semantic shift, and confidence level. Many etymologies are disputed. A word entry should be able to link to cognates/loans across all four languages.

---

## 3. Shared Cuneiform Signs

This is where the real complexity for your data model lives.

### 3.1 The Sign as a Multivalent Entity

A cuneiform sign is **not** like an alphabetic letter. A single sign can function as:

1. **Logogram (word sign)**: The sign represents a whole word.
   - Example: 𒀭 (AN) = Sumerian *an* "sky, heaven" or *dingir* "god"

2. **Syllabogram (phonetic sign)**: The sign represents a syllable (CV, VC, CVC, or V).
   - Example: 𒀭 when used phonetically = the syllable *an*

3. **Determinative (semantic classifier)**: The sign is placed before or after a word to indicate its semantic category but is **not pronounced**.
   - Example: 𒀭 before a divine name = "the following is a god's name" (written ᵈ in transliteration)
   - Compare: Chinese/Japanese radicals (氵= water radical, but in cuneiform determinatives are full signs used as unpronounced classifiers)

4. **Phonetic complement**: A sign added to a logogram to help specify its reading.
   - Example: LUGAL-uš where -uš specifies the Hittite nominative ending, telling you to read it as *ḫassuš*

### 3.2 Polyvalence and Homophony: The Core Data Challenge

**Polyvalence** means one sign has multiple readings:

The sign 𒀭 (DINGIR/AN):
| Context | Reading | Language | Function |
|---------|---------|----------|----------|
| Sumerian word "sky" | *an* | Sumerian | logogram |
| Sumerian word "god" | *dingir* | Sumerian | logogram |
| Syllable /an/ | *an* | any language | syllabogram |
| Before a god's name | (silent) | any language | determinative |
| Akkadian word "god" | *ilu* | Akkadian | logogram (Sumerogram) |
| Hittite word "god" | *siu-* | Hittite | logogram (Sumerogram) |

So the sign 𒀭 before the name Marduk is:
- Written: ᵈMarduk  
- Function: determinative  
- Pronounced: nothing (it's a semantic tag)  
- But the *same sign* in `an-ki` = "heaven and earth" is pronounced *an*  
- And in an Akkadian religious text, used logographically = *ilum* "god"

**Homophony** means multiple signs share the same reading:

The syllable /du/ can be written with at least six different signs in Old Babylonian:
- DU (𒁺) — also reads *gin*, *gub*, *ĝen*, *rá*, *túm*, etc.
- DU₃ (𒆕) — also reads *dù*
- And others indexed DU₄, DU₅, etc.

These are distinguished in transliteration by subscript numbers (a convention, not ancient practice):
- du = sign X
- du₂ = sign Y  
- du₃ = sign Z

**For your schema**: This is your central modeling challenge. You need:
```
Sign (grapheme)
  ├── visual form (glyph variants by period/region)
  ├── sign name (modern conventional name, e.g., "AN")
  ├── readings[] (each a tuple of:)
  │     ├── phonetic value (e.g., "an", "dingir", "il")
  │     ├── language context (Sumerian, Akkadian, Hittite, Elamite)
  │     ├── function (logogram, syllabogram, determinative)
  │     ├── semantic domain (if logogram)
  │     ├── period/region validity
  │     └── frequency/attestation confidence
  └── relationships to other signs (sign evolution, similar forms)
```

### 3.3 Sign Evolution Across Periods

Cuneiform signs changed shape dramatically over time:

**Archaic → Classical → Neo-Assyrian trajectory:**

Stage 1: **Proto-cuneiform** (c. 3400–3000 BCE, Uruk) — pictographic. The sign for "head" looks like a head. Signs are drawn with a pointed stylus, producing curved lines.

Stage 2: **Early Dynastic** (c. 2900–2350 BCE) — signs rotated 90° counterclockwise (debated why — possibly scribal posture changed). Curved lines begin to be replaced by wedge impressions.

Stage 3: **Old Babylonian** (c. 2000–1600 BCE) — fully "cuneiformized." All strokes are wedge-shaped impressions made by a reed stylus (horizontal, vertical, diagonal wedges, and the Winkelhaken). This is the classical form most Assyriologists learn first.

Stage 4: **Middle Babylonian/Assyrian** (c. 1500–1000 BCE) — regional divergence accelerates. Babylonian signs become more cursive; Assyrian signs become more angular.

Stage 5: **Neo-Assyrian** (c. 1000–600 BCE) — highly angular, "clean" forms. This is what most people picture as "cuneiform." Library of Ashurbanipal texts use this script.

Stage 6: **Neo-/Late Babylonian** (c. 600–100 CE) — increasingly cursive and abbreviated. Late astronomical texts can be very difficult to read.

**The same sign in different periods can look completely different** — like comparing Roman capitals (A) to modern cursive handwriting (𝒶) to blackletter (𝔄). Your "AlphaFold for cuneiform" needs to handle this variation.

### 3.4 Regional Variants

Even within the same period, signs look different depending on where they were written:
- **Babylonian** vs. **Assyrian** sign forms diverge from ~1500 BCE onward
- **Peripheral cuneiform** (Hittite, Elamite, Ugarit, Amarna) has its own conventions
- **Hittite cuneiform** derives from Old Babylonian forms (imported ~1650 BCE) and then evolved independently — so Hittite signs often look archaic compared to contemporary Mesopotamian forms
- **Elamite cuneiform** similarly preserves older forms and adds its own innovations

**For your schema**: Sign form must be indexed by at minimum: **period**, **region**, **scribal tradition**. A sign ID should be a persistent, form-independent identifier (like Unicode code points for cuneiform — which exist! U+12000–U+1254F), with variant glyphs attached as period/region-specific renderings.

---

## 4. How Words and Signs Relate: The Encoding System

### 4.1 The Fundamental Distinction: Graphemic vs. Linguistic Analysis

This is the conceptual foundation for your entire pipeline:

**Layer 1: Physical** — Clay tablet, inscribed marks, physical damage
**Layer 2: Graphemic** — Identified sign sequences (what signs are present)
**Layer 3: Transliteration** — Assignment of readings to signs (choosing among polyvalent options)
**Layer 4: Normalization** — Reconstruction of the underlying word forms
**Layer 5: Translation** — Meaning in a target language

Each layer involves different types of uncertainty and different scholarly conventions.

**Example walkthrough — an Akkadian sentence:**

Physical tablet has these signs:
```
𒀭 𒀫 𒁺 𒌓 𒁍 𒋫 𒀀 𒈠
```

**Layer 2 (Sign identification):**
```
AN.MAR.DU — UD.BU.TA.A.MA
```

**Layer 3 (Transliteration):**
```
ᵈmar-duk  u₄-bu-ut-ta-a-ma
```
Here: ᵈ = determinative (AN sign, marking a divine name), mar-duk = phonetic spelling of Marduk, and the rest spells out a word syllabically.

Wait — but *is* that the correct reading? Maybe the UD sign here should be read as *šam* or *pir* or any of its other values. **This is where scholarly judgment and AI could help.**

**Layer 4 (Normalization):**
```
Marduk ... (grammatical analysis of the normalized Akkadian form)
```

**Layer 5 (Translation):**
```
"Marduk ... [did something]"
```

### 4.2 How Sumerian Uses Cuneiform

Sumerian is the language cuneiform was *designed for* (or rather, co-evolved with). The fit is tightest here.

**Writing strategies in Sumerian:**
- Many common words are written with single logograms: 𒈗 = LUGAL = *lugal* "king"
- Grammatical affixes are written with syllabographic signs: *lugal-e* written LUGAL-*e* (logogram + syllabogram for ergative case)
- Some words are written with compound logograms: DUB.SAR = "tablet-writer" = *dubsar* "scribe"
- Administrative texts tend to be heavily logographic; literary texts tend to be more syllabographic (because they care about exact pronunciation for poetic meter)

### 4.3 How Akkadian Uses Cuneiform

Akkadian adapted a system designed for a completely different language. This created inherent tensions:

- Sumerian has no consonant clusters; Akkadian has many. Solution: CVC signs were invented/repurposed.
- Sumerian distinguishes fewer consonants than Akkadian. Solution: some signs were assigned new phonetic values, but the system never fully captured Akkadian phonology. For example, Akkadian distinguishes emphatic consonants (ṭ, ṣ, q) that Sumerian lacked — these are imperfectly represented.
- **Sumerograms**: Akkadian scribes continued to use Sumerian logograms extensively. The sign LUGAL in an Akkadian text is read *šarrum* "king" — it's a logographic borrowing. This is directly analogous to Japanese using Chinese characters: 王 is read *ō* in Chinese but *ō/ōsama* in Japanese.

**Mixed writing example (Old Babylonian letter):**
```
a-na be-lí-ia  qí-bí-ma
a-na  LUGAL-ia  qí-bí-ma
"To my lord, speak:"
```
Both spellings are attested — the second uses LUGAL as a Sumerogram for *bēlī* "my lord."

### 4.4 How Hittite Uses Cuneiform

Hittite pushes the mixed-writing system to its extreme:

A typical Hittite text mixes:
1. **Hittite phonetic signs** (syllabograms reading Hittite)
2. **Sumerograms** (Sumerian logograms read as their Hittite equivalents)
3. **Akkadograms** (Akkadian words used as logograms, read as Hittite)
4. **Determinatives** (Sumerian semantic classifiers)
5. **Phonetic complements** (Hittite syllabic signs attached to logograms)

**Practical example:**
```
Written: nu  ᵈUTU-uš  LUGAL-i  EGIR-pa  me-mi-iš-ki-iz-zi
```

Breaking this down:
| Written | Source | Read as (Hittite) | Function |
|---------|--------|-------------------|----------|
| nu | Hittite | nu | Hittite particle "and, then" |
| ᵈ | Sumerian | (silent) | determinative: divine name follows |
| UTU | Sumerian | ᴵštanu- (Sun God) | Sumerogram |
| -uš | Hittite | -š | phonetic complement (nom. sg.) |
| LUGAL | Sumerian | ḫassui (dat.) | Sumerogram |
| -i | Hittite | -i | phonetic complement (dat. sg.) |
| EGIR | Sumerian | appan | Sumerogram "back, behind" |
| -pa | Hittite | -pa (postposition) | Hittite particle |
| me-mi-iš-ki-iz-zi | Hittite | memiskizzi | phonetic: "keeps speaking" |

**Full reading**: *nu Ištanuš ḫassui appan memiskizzi* — "And the Sun God keeps speaking to the king."

This is THREE languages in one sentence at the graphemic level, but ONE language (Hittite) at the linguistic level.

**For your schema**: You absolutely need a **layered annotation model**:
```
Token:
  graphemic_form: "LUGAL-i"
  sign_sequence: [LUGAL, I]
  sign_origins: [Sumerian_logogram, Hittite_syllabogram]
  functions: [logogram, phonetic_complement]
  target_language: Hittite
  phonetic_reading: "ḫassui"
  morphological_analysis: {stem: "ḫassus", case: "dative", number: "singular"}
  translation: "to the king"
```

### 4.5 How Elamite Uses Cuneiform

Elamite cuneiform is a reduced subset of the Mesopotamian sign repertoire:
- Primarily syllabographic (less logographic than Akkadian or Hittite)
- Some Sumerograms used, especially in royal inscriptions
- The Achaemenid Elamite syllabary is quite small (~130 signs) compared to the 600+ of Akkadian
- Some signs have Elamite-specific phonetic values not found in Mesopotamian usage

**This relative simplicity is a mixed blessing**: Fewer sign ambiguities, but less context for disambiguation, and the language itself is poorly understood.

---

## 5. Evolution of Cuneiform and Each Language

### 5.1 The Cuneiform Writing System: A Timeline

```
c. 3400 BCE  Proto-cuneiform (Uruk IV) — numerical/administrative tokens
             → NOT yet language-specific; may encode Sumerian or something else
c. 3200 BCE  Uruk III — signs become more standardized; likely Sumerian
c. 2900 BCE  Early Dynastic I — first clearly linguistic texts (Sumerian)
c. 2600 BCE  Early Dynastic IIIa — Fara and Abu Salabikh texts
             → First evidence of Akkadian personal names in cuneiform
             → Elamite may begin using linear script (not cuneiform yet)
c. 2350 BCE  Sargonic period — Akkadian becomes major written language
             → Elamite adapts cuneiform (alongside its own Linear Elamite script)
c. 2100 BCE  Ur III — Sumerian "golden age" of documentation
             → Massive administrative archives (estimated 100,000+ tablets)
c. 1900 BCE  Old Babylonian — classical cuneiform standardized
             → Old Assyrian trading colony texts (Kültepe/Kanesh, in Anatolia)
c. 1650 BCE  Hittites adopt cuneiform (from Babylonian tradition)
c. 1400 BCE  Cuneiform used internationally: Amarna Letters
             → Also used for Hurrian, Ugaritic (alphabetic cuneiform!)
c. 1200 BCE  Bronze Age Collapse — Hittite cuneiform ceases
c. 1000 BCE  Neo-Assyrian script standardization
c. 600 BCE   Neo-Babylonian developments
             → Achaemenid Elamite at Persepolis
             → Old Persian cuneiform invented (semi-alphabetic, very different)
c. 100 CE    Last known cuneiform texts (astronomical diaries, Babylon)
```

### 5.2 Sumerian Language Evolution

- **Archaic Sumerian** (pre-2600 BCE): Extremely difficult to analyze. Many texts may be lists or administrative records with minimal grammar visible.
- **Old Sumerian** (c. 2600–2350 BCE): Pre-Sargonic royal inscriptions (Lagash, etc.). Grammar is becoming clearer.
- **Neo-Sumerian** (c. 2100–2000 BCE, Ur III): Enormous administrative corpus. Highly standardized. This is the best-attested period for grammar.
- **Post-Sumerian** / **Old Babylonian literary Sumerian** (c. 2000–1600 BCE): Sumerian is likely dead as a spoken language by ~2000 BCE. It continues as a literary, religious, and scholarly language (think Latin in medieval Europe). Old Babylonian scribes copied and composed Sumerian texts, but their Sumerian shows Akkadian interference.
- **Late Sumerian** (post-1600 BCE through ~100 CE): Used in ritual, scholarly, and astronomical contexts. Increasingly fossilized.

**The "dead language problem"**: Most of our Sumerian literary texts were written by Akkadian speakers after Sumerian died as a spoken language. How much of the grammar in these texts reflects actual Sumerian vs. Akkadian-influenced "school Sumerian" is actively debated. This is a significant uncertainty in any NLP model.

### 5.3 Akkadian Language Evolution

- **Old Akkadian** (c. 2500–1950 BCE): Sargonic period. Shows features not found in later dialects. Not yet clearly differentiated into Assyrian and Babylonian.
- **Old Babylonian** (c. 1950–1530 BCE): The "Classical Arabic" of Akkadian — this is the standard taught first, the one with the fullest case system and most transparent morphology.
- **Old Assyrian** (contemporary with OB): Known primarily from the Kanesh trading archives. Distinctive phonology and vocabulary.
- **Middle Babylonian / Middle Assyrian** (c. 1530–1000 BCE): Case system weakening. MB used as international diplomatic language.
- **Neo-Assyrian** (c. 1000–600 BCE): Significant phonological changes. Vowel harmony. Loss of mimation. The language of Sargon II, Sennacherib, Ashurbanipal.
- **Neo-Babylonian / Late Babylonian** (c. 1000 BCE – 100 CE): Further morphological simplification. Last cuneiform texts are LB astronomical diaries.
- **Standard Babylonian**: An artificial literary dialect used across Mesopotamia for literary and scholarly texts from ~1500 BCE onward. Based on OB but with innovations. Used for the standard version of the *Epic of Gilgamesh*. Think of it as "Literary Akkadian" that doesn't correspond to any spoken dialect.

### 5.4 Hittite Language Evolution

- **Old Hittite** (c. 1650–1500 BCE): Earliest texts. Some archaic features. Often known only through later copies.
- **Middle Hittite** (c. 1500–1380 BCE): Transitional.
- **New/Neo-Hittite** (c. 1380–1178 BCE): Imperial period. Most texts come from the capital Hattusha (modern Boğazkale). Best attested.
- Hittite ceases to be written after the fall of the Hittite Empire (~1178 BCE). The Luwian and related languages continue in hieroglyphic Luwian script.

### 5.5 Elamite Language Evolution

- **Old Elamite** (c. 2600–1500 BCE): Poorly attested. Some texts in Linear Elamite script (still only partially deciphered) and some in cuneiform.
- **Middle Elamite** (c. 1500–1000 BCE): Most substantial corpus. Royal inscriptions from Susa and Chogha Zanbil. Best understood period.
- **Neo-Elamite** (c. 1000–550 BCE): Political decline. Fewer texts.
- **Achaemenid Elamite** (c. 550–330 BCE): Used in the Persepolis Fortification Archive and Treasury texts. Heavily influenced by Old Persian. ~15,000+ tablets.

---

## 6. Most Significant Similarities and Differences

### 6.1 Similarities (Beyond Cuneiform)

**Structural:**
- Three of four languages are **SOV**: Sumerian, Hittite, Elamite (Akkadian tends SOV too, especially in early periods). This may partly be an areal feature of the ancient Near East.
- Three of four are significantly **agglutinative**: Sumerian, Hittite (partially), Elamite. Akkadian is more fusional but still uses productive affixation.
- All four show **verb-agreement with subject** (and sometimes object).

**Cultural/scribal:**
- All four language traditions share the **Sumerian scholarly apparatus**: sign lists, lexical lists, bilingual texts. Mesopotamian scribal education was exported along with cuneiform.
- All four are attested primarily on **clay tablets** (some stone inscriptions, some metal).
- All four share significant **religious and cultural vocabulary** derived from the Sumerian/Akkadian tradition (names of gods, ritual terms, royal titles).

**Lexical:**
- The "international vocabulary" of cuneiform culture: words for tablet (*tup-/dup-*), scribe, temple, king, and various commodities appear (in borrowed or adapted form) across multiple traditions.

### 6.2 Differences (The Big Ones)

| Feature | Sumerian | Akkadian | Hittite | Elamite |
|---------|----------|----------|---------|---------|
| Language family | Isolate | Semitic | Indo-European | Isolate |
| Morphological type | Agglutinative | Fusional (root-and-pattern) | Fusional + agglutinative | Agglutinative |
| Case alignment | Ergative-absolutive | Nominative-accusative | Nominative-accusative | Debated (possibly neither cleanly) |
| Gender | None (human/non-human class) | Masculine/Feminine | Common/Neuter | None (human/non-human?) |
| Root system | No root-and-pattern | Triconsonantal root | IE roots (ablaut) | No root-and-pattern |
| Verb morphology | Prefix chain + stem + suffix chain (slot-based) | Root + pattern + affixes (templatic) | Stem + suffix (IE conjugation) | Stem + suffix chain |
| Writing density | Logographic + syllabographic | Mixed (many Sumerograms) | Heavily mixed (three-language writing) | Mostly syllabographic |
| Corpus size | ~100,000+ texts | ~500,000+ texts | ~30,000+ fragments | ~20,000+ texts |

**The most significant difference**: These languages have fundamentally different morphological architectures. Akkadian's root-and-pattern system (like Arabic) is radically different from Sumerian's slot-based agglutination (like Japanese). Any unified data schema must accommodate both without privileging one.

### 6.3 The "False Friend" Problem

Because all four use cuneiform, there's a constant danger of conflating graphemic similarity with linguistic similarity. 

The sign LUGAL appears in Sumerian, Akkadian, and Hittite texts — but:
- In Sumerian it's the word *lugal* (morphologically: lu₂ "man" + gal "big")
- In Akkadian it's read *šarru* (a native Semitic word from the root *š-r-r*)
- In Hittite it's read *ḫassus* (an Anatolian IE word)

**Same sign. Three different words from three different language families. Zero linguistic relationship.** This is analogous to the kanji 山 being read *shān* in Chinese and *yama/san* in Japanese — same grapheme, different linguistic items.

Your schema must enforce this separation.

---

## 7. Cultural Contexts

### 7.1 Sumerian: Temple and Palace

Sumerian civilization was centered on **city-states** (Ur, Uruk, Lagash, Nippur, Eridu) in southern Mesopotamia. Key cultural institutions:

- **The temple economy**: Many early texts are administrative records of temple institutions tracking land, labor, animals, and rations. The god owned the land; the temple administered it.
- **The scribal school (é-dub-ba-a, "tablet house")**: Formal education centered on copying sign lists, proverbs, literary texts. The curriculum is well-known from OB period.
- **Literary genres**: Myths (Enki and Ninhursag), hymns (temple hymns, royal hymns), laments (Lament for Ur), debates (Summer and Winter), proverbs, love poetry.
- **Lexical lists**: Organized collections of signs and words by category (professions, animals, wooden objects, etc.). These are foundational for your pipeline — they're essentially ancient sign dictionaries.

**Key corpus for your schema**: The **Ur III administrative archive** (~100,000 texts) is the single largest corpus of cuneiform texts and is highly formulaic — ideal for NLP training. The **Old Babylonian literary corpus** contains the core literary traditions.

### 7.2 Akkadian: Empire and Commerce

- **Old Akkadian (Sargonic)**: First empire — administrative and royal inscriptions.
- **Old Babylonian**: Code of Hammurabi. Extensive legal documents, letters, mathematical and astronomical texts, literature (Atrahasis, Gilgamesh).
- **Old Assyrian**: Trading colony archives at Kanesh — letters, contracts, legal disputes. Window into commercial life.
- **Neo-Assyrian**: Imperial administration, state correspondence, library texts (Ashurbanipal's library at Nineveh — the largest ancient cuneiform library).
- **Neo-/Late Babylonian**: Astronomical diaries, temple archives, mathematical astronomy. The last flourishing of cuneiform culture.

**Genre affects writing conventions**: Royal inscriptions use archaic/literary forms. Letters are more colloquial. Legal texts have formulaic language. Administrative texts are heavily abbreviated. Your NLP model needs genre awareness.

### 7.3 Hittite: Ritual and Diplomacy

The Hittite archive from **Hattusha (Boğazkale)** includes:
- **Treaties and diplomatic correspondence**: International treaties with Egypt (Treaty of Kadesh, earliest known peace treaty), vassal treaties.
- **Laws**: Hittite law code — notable for relatively mild penalties compared to Mesopotamian codes.
- **Ritual texts**: Extremely numerous. Rituals for purification, festivals, augury, and healing.
- **Mythological texts**: Hittite versions of Mesopotamian myths plus native Anatolian myths (Kumarbi cycle, Illuyanka myth).
- **Multilingual texts**: Hittite, Luwian, Palaic, Hattic, and Hurrian texts found in the same archive. Hattusha was a multilingual city.

**Critical for your pipeline**: The Boğazkale archive is **the** source for Hittite. Almost all Hittite cuneiform comes from this one site. This creates a sampling bias — we know Hittite as written in the capital by state scribes. Regional or colloquial variation is almost invisible.

### 7.4 Elamite: The Perennial Neighbor

Elam was Mesopotamia's eastern neighbor for three millennia:
- **Susa** was the primary center. Elamite culture oscillated between independence and Mesopotamian influence.
- **Middle Elamite period**: Greatest independence. Kings like Untash-Napirisha built Chogha Zanbil. Royal inscriptions are the main source.
- **Achaemenid period**: Elamite was one of three official languages of the Persian Empire (alongside Old Persian and Babylonian). The **Persepolis Fortification Archive** and **Persepolis Treasury tablets** are the largest Elamite corpus — but they represent bureaucratic language, heavily influenced by Persian, and may not reflect natural Elamite.

**The Elamite challenge**: We have no bilingual "Rosetta Stone" of the quality that exists for Akkadian-Sumerian. The decipherment of Elamite relies heavily on:
1. Comparison with Akkadian versions of multilingual inscriptions (especially Achaemenid royal inscriptions in Old Persian, Elamite, and Babylonian)
2. Internal analysis
3. Educated guesswork

Many Elamite words and grammatical features remain uncertain or debated.

---

## 8. State of Understanding and Challenges

### 8.1 Sumerian

**State**: Moderately well understood. Grammar is still actively debated.

**Key challenges**:
- **Phonology**: We don't know exactly how Sumerian sounded. The vowel system (usually reconstructed as a, e, i, u) is debated. Some scholars argue for fewer vowels. Consonant distinctions are uncertain (was there really a /ĝ/ distinct from /g/? what about the "unclear" series of consonants?).
- **Verbal system**: The Sumerian verbal chain is the most debated aspect of the grammar. The number of prefix "slots," their exact functions, and their interactions are subjects of active scholarly disagreement. Major competing grammatical frameworks exist (Thomsen, Edzard, Jagersma, Zólyomi, Attinger — each with somewhat different analyses).
- **Ergative system**: How consistently ergative was Sumerian? Were there splits based on tense, animacy, or other factors? Debated.
- **Dead language problem**: Most literary Sumerian was written by non-native speakers. Separating "real" Sumerian from Akkadicized school Sumerian is difficult.
- **Dialectology**: Evidence for an *eme-sal* dialect (possibly women's speech in literary contexts, or a separate sociolect/register) adds complexity.

**Available resources**:
- **ePSD2** (Electronic Pennsylvania Sumerian Dictionary): Main lexical resource
- **ETCSL** (Electronic Text Corpus of Sumerian Literature): ~400 literary compositions
- **CDLI** (Cuneiform Digital Library Initiative): Largest cuneiform database overall
- **ORACC** (Open Richly Annotated Cuneiform Corpus): Annotated text editions
- **BDTNS** (Database of Neo-Sumerian Texts): Ur III administrative texts

### 8.2 Akkadian

**State**: Well understood. This is the best-known cuneiform language by far.

**Key challenges**:
- **Dialectal variation**: The differences between OB, NA, NB, etc. are significant. An NLP model trained on OB texts will struggle with NA texts and vice versa.
- **Logographic writing**: Heavy use of Sumerograms means that the phonetic form of many words in many texts is unknown — we know the meaning but not how the scribe would have pronounced it.
- **Corpus bias**: Certain genres are overrepresented (administrative texts), others underrepresented (everyday speech). Literary "Standard Babylonian" is an artificial dialect that may never have been spoken.
- **Hapax legomena**: Many rare words occur only once or twice in the entire corpus, making meaning uncertain.

**Available resources**:
- **CAD** (Chicago Assyrian Dictionary): 21-volume monster. The standard reference. Now freely available online.
- **AHw** (Akkadisches Handwörterbuch, von Soden): German-language dictionary. More etymologically focused.
- **CDA** (Concise Dictionary of Akkadian): Accessible student reference.
- **ORACC/SAAo** (State Archives of Assyria online): Neo-Assyrian state correspondence
- **ARCHIBAB**: Old Babylonian texts online

### 8.3 Hittite

**State**: Well understood for an ancient language, but ongoing refinements.

**Key challenges**:
- **Sumerogram/Akkadogram problem**: Because so much of any Hittite text is written logographically, the actual Hittite vocabulary is smaller than it would be if texts were written phonetically. We don't know the Hittite words for many concepts because scribes always wrote them as Sumerograms.
- **Text condition**: Many Hattusha tablets are fragmentary. Joins (identifying that two fragments belong to the same tablet) are ongoing.
- **Single-site corpus**: Almost everything comes from Hattusha. We lack dialectal or regional data.
- **Scribal errors**: Hittite scribes made errors (this is true of all cuneiform traditions, but the consequences are significant when your corpus is smaller).
- **Phonology debates**: Exact pronunciation of many Hittite sounds is debated (the *ḫ* sounds, the status of *a* vs. *ā* when written with plene spelling, etc.).

**Available resources**:
- **CHD** (Chicago Hittite Dictionary): The standard reference (in progress for decades, nearing completion).
- **HED** (Hittite Etymological Dictionary, Puhvel): Etymological focus.
- **HPM** (Hethitologie Portal Mainz): Database of Hittite texts.
- **TITUS**: Text corpus including Hittite.
- **Konkordanz der hethitischen Keilschrifttafeln**: Catalog of published Hittite texts.

### 8.4 Elamite

**State**: Poorly understood. The least-known major cuneiform language.

**Key challenges**:
- **No related languages**: As an isolate, there's no comparative evidence to help reconstruct meaning or grammar.
- **No substantial bilingual corpus**: Unlike Akkadian-Sumerian (which has extensive bilinguals), Elamite-Akkadian bilinguals are limited to formulaic royal inscriptions.
- **Limited corpus**: Especially for Old and Neo-Elamite periods.
- **Achaemenid Elamite bias**: The largest corpus is administrative language from a specific context, possibly a pidginized form.
- **Competing grammars**: Scholars don't agree on basic morphological analysis. The case system, verbal agreement patterns, and syntax are all debated.
- **Linear Elamite**: The native Elamite script (used alongside and sometimes instead of cuneiform in early periods) was only recently partially deciphered (Desset, 2022). This is an active frontier.

**Available resources**:
- **EW** (Elamisches Wörterbuch, Hinz & Koch): The standard dictionary. Now quite dated.
- No equivalent to CAD or CHD in scope or modernity.
- Persepolis Fortification Archive publications (Hallock, etc.)
- Growing but still limited digital resources.

---

## 9. Additional Topics You Should Be Asking About

### 9.1 Transliteration Conventions

Your pipeline must handle the standard transliteration system used by Assyriologists:

- **Sumerian logograms** are written in CAPITALS or small caps: LUGAL, AN, E₂
- **Akkadian and Hittite** phonetic values are written in italics lowercase: *šar-ru-um*
- **Determinatives** are written as superscripts: ᵈ (divine), ᵐ (male person), ᶠ (female), ᵘʳᵘ (city), ᵏᵘʳ (land/mountain), ᵍⁱˢ (wood)
- **Sign index numbers**: du₃ means "the third sign with the reading /du/" — these are assigned by convention (mainly following Borger's sign list numbering)
- **Damage markers**: [...] = broken/missing; ⸢x⸣ = partially preserved sign; x = illegible sign
- **Uncertain readings**: sign? or sign! for questionable/corrected readings

**For your schema**: You need to encode:
- Sign-level annotations (damage state: complete, partial, broken, missing)
- Certainty levels on readings
- Scholarly provenance of readings (who assigned this reading and when)
- Cross-references to standard sign lists (Borger, MZL, aBZL, etc.)

### 9.2 Lexical Lists: Your Training Data Goldmine

The ancient Mesopotamians created their own dictionaries. These **lexical lists** are critical for any cuneiform AI:

- **Proto-Lu₂** / **Lu₂ = ša**: Lists of professions (Sumerian with Akkadian translations)
- **Proto-Ea** / **Ea = nâqu**: Sign lists with Sumerian readings and Akkadian translations
- **Proto-Ḫḫ** / **Ḫar-ra = ḫubullu**: Thematic word lists (24 tablets covering trees, wooden objects, reeds, pottery, hides, metals, animals, stones, plants, fish, birds, textiles, foods, drinks, etc.)
- **Malku = šarru**: Synonym lists
- **Nabnītu**: Grammatical text showing Sumerian verb forms with Akkadian translations
- **Syllabary texts (Sᵃ, Sᵇ)**: Sign lists organized by sign form

These lists are your Rosetta Stone equivalent — they provide explicit ancient mappings between signs, readings, and translations. They should be a primary data source for your schema.

### 9.3 Sign Lists and Modern Cataloging

Modern sign references your schema should cross-reference:

| Abbreviation | Full Name | Coverage |
|-------------|-----------|----------|
| **MZL** | Mesopotamisches Zeichenlexikon (Borger) | Comprehensive sign list, standard numbering |
| **aBZL** | Altbabylonische Zeichenliste (Mittermayer) | Old Babylonian sign forms |
| **ŠL** | Šumerisches Lexikon (Deimel) | Older Sumerian sign list |
| **HZL** | Hethitische Zeichenlexikon (Rüster & Neu) | Hittite cuneiform signs |
| **Unicode** | Unicode Standard (Cuneiform block) | U+12000–U+1254F, U+12480–U+12543 |

Your pipeline should map between these numbering systems. A sign entity in your database should have:
```
sign_id: internal UUID
unicode: U+12000 (if assigned)
borger_mzl: 13
hzl: 1 (if applicable to Hittite)
cdli_id: ... (CDLI sign identifier)
```

### 9.4 The AlphaFold Analogy: What Would This Actually Look Like?

You mentioned wanting to build an "AlphaFold for cuneiform signs." Let me unpack what the analogous problem structure would be:

**AlphaFold's problem**: Given a sequence of amino acids (1D), predict the 3D structure of the protein.

**Cuneiform's equivalent problems** (there are several):

**Problem 1: Sign Identification (OCR/HTR)**
- Input: Image of a tablet surface (2D/3D scan)
- Output: Sequence of identified signs
- Challenges: Damage, weathering, variant sign forms, overlapping wedges
- Existing work: DeepScribe (UCLA), CDLI CoNLL-U, various CNN/transformer approaches
- This is the most "AlphaFold-like" problem — a well-defined input-output mapping

**Problem 2: Reading Assignment (Disambiguation)**
- Input: Identified sign sequence + language context
- Output: Correct reading for each sign (resolving polyvalence)
- This is more like a **contextual language model problem** — given the sign DU in position N, which of its 15+ possible readings is correct?
- Context clues: surrounding signs, expected grammar, genre, period, region

**Problem 3: Translation**
- Input: Transliterated text in Language X
- Output: Translation in a modern language
- This is **machine translation** — but with extremely limited parallel corpora compared to modern MT
- The Sumerian-Akkadian bilingual corpus is the richest; Elamite is desperately thin

**Problem 4: Fragment Joining**
- Input: Multiple tablet fragments (physical shape + text content)
- Output: Which fragments belong together
- This is a **matching/reconstruction problem** — both physical (3D shape fitting) and textual (does the text continue coherently?)

**For your schema design**, the most important thing is to **keep these problems separate in your data model** while allowing them to interoperate. A unified pipeline would flow:

```
3D scan → Sign identification → Reading assignment → 
Morphological analysis → Syntactic parsing → Translation
         ↑                    ↑                ↑
   Sign list data      Grammar rules     Parallel texts
   Period/region        Lexical lists     Dictionaries
   Visual variants      Genre context     Cultural knowledge
```

### 9.5 Existing Digital Infrastructure You Should Build On

| Project | URL | What It Provides |
|---------|-----|-----------------|
| **CDLI** | cdli.mpiwg-berlin.mpg.de | Catalog and images of ~350,000 cuneiform objects |
| **ORACC** | oracc.museum.upenn.edu | Annotated text editions with lemmatization |
| **ePSD2** | oracc.museum.upenn.edu/epsd2 | Sumerian dictionary with attestations |
| **ETCSL** | etcsl.orinst.ox.ac.uk | Sumerian literary texts |
| **BDTNS** | bdtns.filol.csic.es | Neo-Sumerian administrative texts |
| **SEAL** | seal.huji.ac.il | Sources of Early Akkadian Literature |
| **SAAo** | oracc.museum.upenn.edu/saao | State Archives of Assyria |
| **Hethitologie Portal** | hethiter.net | Hittite text database |
| **DCCLT** | oracc.museum.upenn.edu/dcclt | Digital Corpus of Cuneiform Lexical Texts |
| **CCP** | ccp.yale.edu | Cuneiform Commentaries Project |
| **DeepScribe** | deepscribe.library.jhu.edu | ML for cuneiform sign identification |

**Data formats you'll encounter:**
- **ATF** (ASCII Transliteration Format): CDLI's standard. Line-by-line transliteration with metadata.
- **CoNLL-U**: Used in some ML projects for token-level annotation.
- **TEI XML**: Used by some European projects.
- **ORACC JSON**: ORACC's API output format.
- **Custom formats**: Many projects use bespoke schemas. Interoperability is a real problem.

### 9.6 What Your Schema Needs: A Sketch

Based on everything above, here's a conceptual data model:

```
TABLET (physical object)
  ├── id, museum_number, provenance, period, dimensions
  ├── physical_condition
  ├── images[] (photos, 3D scans)
  └── surfaces[] (obverse, reverse, edges)
        └── lines[]
              └── tokens[]

TOKEN (the unit linking all layers)
  ├── position (surface, line, position_in_line)
  ├── graphemic_layer
  │     ├── sign_sequence[] → SIGN entities
  │     ├── damage_state (intact, partial, broken, supplied)
  │     └── visual_form_image (crop from tablet image)
  ├── reading_layer
  │     ├── transliteration (e.g., "LUGAL-uš")
  │     ├── function_per_sign[] (logogram, syllabogram, determinative, complement)
  │     ├── source_language_per_sign[] (Sumerian, Akkadian, Hittite, Elamite)
  │     ├── phonetic_reading (e.g., "ḫassuš")
  │     ├── reading_confidence (0-1)
  │     └── alternative_readings[] (with confidence scores)
  ├── linguistic_layer
  │     ├── target_language (the language actually being expressed)
  │     ├── lemma → DICTIONARY_ENTRY
  │     ├── morphological_analysis (structured by language-specific grammar)
  │     │     ├── Sumerian: slot-based template
  │     │     ├── Akkadian: root + pattern + affixes
  │     │     ├── Hittite: stem + inflection
  │     │     └── Elamite: stem + suffix chain
  │     ├── part_of_speech
  │     └── syntactic_role
  └── semantic_layer
        ├── translation(s) in modern language(s)
        ├── semantic_domain
        └── cross-references to parallel texts

SIGN (abstract grapheme)
  ├── sign_id (internal)
  ├── unicode_codepoint
  ├── sign_name (e.g., "AN")
  ├── borger_mzl_number
  ├── readings[] → READING entities
  └── variant_forms[]
        ├── period, region, script_tradition
        └── glyph (image or vector)

READING
  ├── phonetic_value (e.g., "an", "dingir", "il")
  ├── function (logogram, syllabogram, determinative)
  ├── language_context (Sumerian, Akkadian, Hittite, Elamite, any)
  ├── semantic_value (if logogram)
  ├── period_range
  ├── frequency/attestation_count
  └── notes

DICTIONARY_ENTRY
  ├── lemma_form (citation form)
  ├── language
  ├── dialect/period
  ├── part_of_speech
  ├── meanings[]
  ├── etymology
  ├── cognates/loans[] → other DICTIONARY_ENTRY entities
  └── attestations[] → TOKEN entities
```

### 9.7 The Scholarly Workflow Your Pipeline Must Support

Assyriologists typically work through this process:
1. **Collation**: Examining the physical tablet (or high-quality photos/3D scans) to determine which signs are present.
2. **Transliteration**: Assigning readings to the identified signs.
3. **Normalization**: Reconstructing the underlying linguistic forms.
4. **Translation**: Rendering the text in a modern language.
5. **Commentary**: Discussing philological problems, parallel texts, historical context.

Steps 1–3 involve the most uncertainty and are where AI assistance would be most valuable. **But the human expert must remain in the loop** — cuneiform scholarship is full of cases where a single sign reading changes the interpretation of an entire text. Your pipeline should be designed to **augment** expert judgment, not replace it. Confidence scores, alternative readings, and transparent reasoning are essential.

### 9.8 Phonological Systems Compared

For completeness, here's how the phonological inventories compare (reconstructed):

**Sumerian (highly debated):**
- Consonants: b, d, g, ĝ, ḫ, k, l, m, n, p, r, s, š, t, z (+ debated sounds)
- Vowels: a, e, i, u (possibly with length distinctions)
- No known consonant clusters in native words
- Tone? Debated. Probably not, but we genuinely don't know.

**Akkadian:**
- Consonants: b, d, g, ḫ, k, l, m, n, p, q, r, s, ṣ, š, t, ṭ, w, y, z, ʾ (glottal stop)
- Vowels: a, e, i, u (all with length distinctions: ā, ē, ī, ū)
- Complex consonant clusters allowed (but imperfectly represented in cuneiform)
- Stress: probably penultimate if penult is heavy, else antepenultimate (debated)

**Hittite:**
- Consonants: b, d, g, ḫ, ḫḫ, k, l, m, n, p, r, s, š, t, w, y, z (+ debated fortis/lenis distinction)
- Vowels: a, e, i, u (length exists but the writing system doesn't consistently mark it)
- Consonant clusters allowed and significant (typical for IE)
- The cuneiform script is a poor fit for Hittite phonology in some respects

**Elamite:**
- Consonants: b/p, d/t, g/k, ḫ, l, m, n, r, s, š, z (simplified; exact inventory debated)
- Vowels: a, i, u (possibly e; vowel system debated)
- Relatively simple syllable structure

---

## 10. Practical Recommendations for Your Schema and Pipeline

### 10.1 Design Principles

1. **Language-agnostic sign layer**: The graphemic/sign layer should be independent of any specific language. A sign is a sign, regardless of what language it's being used for.

2. **Language-specific linguistic layers**: Morphological analysis must be language-specific. Don't try to force Sumerian agglutinative chains and Akkadian triconsonantal roots into the same morphological template. Use a **polymorphic design** — the morphological analysis structure varies by language.

3. **Period and region as first-class dimensions**: Not metadata, but core indexing fields. A sign reading that's valid in Old Babylonian may not exist in Neo-Assyrian.

4. **Uncertainty as a first-class data type**: Every reading, every translation, every morphological analysis should have a confidence score and provenance. Cuneiform scholarship is inherently probabilistic.

5. **Layered annotation**: Physical → Graphemic → Reading → Linguistic → Semantic. Each layer should be independently editable without destroying the others.

6. **Cross-linguistic linking**: Words should be linkable across languages (this Sumerian word was borrowed into Akkadian as X, which was used logographically in Hittite representing Hittite word Y).

7. **Versioning and scholarly attribution**: Multiple scholars may disagree on the reading of the same sign. Your schema should support competing interpretations with attribution, not force a single "correct" answer.

### 10.2 Where AI Can Help Most

**High confidence, high impact:**
- Sign identification from images (OCR/HTR for cuneiform)
- Reading disambiguation given context (language model approach)
- Pattern matching in administrative texts (highly formulaic)
- Fragment joining (both physical and textual matching)
- Identifying parallel texts across the corpus

**Medium confidence, high value:**
- Morphological analysis (especially for well-understood languages like Akkadian)
- Translation assistance for formulaic genres (royal inscriptions, administrative texts)
- Anomaly detection (finding unusual forms that may indicate new words or scribal errors)

**Low confidence, proceed with caution:**
- Elamite translation (insufficient training data)
- Novel Sumerian grammatical analysis (too much scholarly disagreement)
- Literary translation (requires cultural knowledge beyond what current models handle well)
- Interpreting damaged or ambiguous passages (the heart of scholarship — this is where human expertise is irreplaceable, and where AI errors would be most damaging)

### 10.3 A Note on Reproducibility and Trust

Given your interest in trust frameworks and provenance — this is directly applicable here. Your pipeline should:
- **Never present an AI reading as authoritative without flagging it as machine-generated**
- **Always provide the reasoning chain**: "I identified this as sign X because of visual features A, B, C; I assigned reading Y because of contextual features D, E, F"
- **Track provenance**: Was this reading assigned by a human expert, copied from a published edition, or generated by AI?
- **Support correction**: When a human expert disagrees with an AI reading, the correction should feed back into the model AND be tracked as a scholarly event

This is exactly the trust acquisition → growth → maintenance cycle you've been thinking about in your agentic design work, applied to a scholarly domain.

---

## Glossary of Key Terms

| Term | Definition |
|------|-----------|
| **Allograph** | A variant form of the same sign (different visual appearance, same sign identity) |
| **Determinative** | A sign used as an unpronounced semantic classifier |
| **Hapax legomenon** | A word attested only once in the entire corpus |
| **Logogram** | A sign used to represent a whole word |
| **Normalization** | Reconstructing the actual word form from a transliteration |
| **Phonetic complement** | A syllabographic sign added to a logogram to indicate its reading |
| **Polyvalence** | One sign having multiple possible readings |
| **Homophony** | Multiple signs sharing the same phonetic value |
| **Sumerogram** | A Sumerian logogram used in a non-Sumerian text |
| **Akkadogram** | An Akkadian word used logographically in a non-Akkadian text |
| **Syllabogram** | A sign used to represent a syllable |
| **Transliteration** | Converting cuneiform signs to roman-alphabet representation |
| **ATF** | ASCII Transliteration Format (CDLI standard) |

---

*Document prepared as a working reference for cuneiform data schema design. This represents a synthesis of current scholarly understanding as of mid-2025. For specific philological questions, always consult the primary literature and specialist colleagues.*
