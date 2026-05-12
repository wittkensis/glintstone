---
question: "TODO: one sentence — what question does schema-pipeline-examples.md answer?"
created: 2026-05-11
modified: 2026-05-11
context: "TODO: why was this file created?"
status: draft
audience: [engineers]
owners: [eric]
related_issues: []
related_skills: []
supersedes: null
superseded_by: null
---

# Cuneiform Translation Pipeline: Worked Examples

## Part 1: "The King Built the Temple" — Four Languages, One Pipeline

This phrase is chosen because royal building inscriptions are the **single most common genre** across all four language traditions. Every king who built a temple wrote about it. The formulaic nature makes comparison tractable, but the linguistic differences are revealing.

---

### SUMERIAN

**Source**: Gudea Cylinder A, col. i, lines 1–2 (c. 2144–2124 BCE, Lagash)
**Genre**: Royal building inscription

#### Step 0: Physical Object
```
Object:     Clay cylinder, ~61 cm tall
Museum:     Louvre (AO 22126)
Condition:  Well preserved, minor surface damage
CDLI ID:    P232275
```

#### Step 1: Sign Identification (Graphemic Layer)
```
What a human or OCR system sees on the clay:
  𒂍 𒉣𒈾 𒀭𒊩𒌆𒄈𒋢 𒈬𒈾𒆕

These are wedge impressions. Each cluster is a sign or sign group.
```

#### Step 2: Transliteration (Reading Layer)
```
e₂   nin-ĝir₂-su-ka-ni   mu-na-du₃
```

**Reading decisions made here:**
| Sign | Sign Name | Reading Chosen | Alternatives Rejected | Why |
|------|-----------|---------------|----------------------|-----|
| 𒂍 | E₂ | e₂ | bid, bit₃ | Context: "house/temple" expected in building inscription |
| 𒉣 | NIN | nin | ereš | Compound: part of divine name |
| 𒈾 | NA | na | — | Syllabographic, unambiguous in this position |
| 𒀭 | AN/DINGIR | ᵈ (silent) | an, dingir | Determinative before divine name |
| 𒊩𒌆 | NIN₉? | (part of name) | — | Component of Ninĝirsu |
| 𒄈 | GIR₂ | ĝir₂ | — | Part of divine name compound |
| 𒋢 | SU | su | — | Part of divine name |
| 𒈬 | MU | mu | — | Verbal prefix (ventive) |
| 𒆕 | DU₃ | du₃ | du, gin, gub | Context: "build" in building inscription; NOT du "go" or gub "stand" |

**This last reading decision is critical.** The sign DU₃ is distinct from DU (which has readings *gin* "to go," *gub* "to stand," *túm* "to carry," *rá* "to go," and more). But an OCR system seeing the physical sign must distinguish them — and in some periods and hands, they look similar.

#### Step 3: Tokenization for BabyLemmatizer
```
Mode: 1 (indexed logo-syllabic — Sumerian preserves indices)

Raw:        e₂     nin-ĝir₂-su-ka-ni     mu-na-du₃
Tokenized:  e2     nin-ĝir2-su-ka-ni      mu-na-du3

Note: BabyLemmatizer mode 1 keeps the index numbers (e2, du3)
because they distinguish different Sumerian words.
```

#### Step 4: BabyLemmatizer Processing (Linguistic Layer)

**POS-tagger input/output:**
```
Source sequence: e 2 | n i n - ĝ i r 2 - s u - k a - n i | m u - n a - d u 3
Target: N | DN | V
```

**Lemmatizer input/output (with POS context):**
```
Source: e 2 [N_ctx]
Target: e [house]

Source: n i n - ĝ i r 2 - s u - k a - n i [DN_ctx]
Target: Ninĝirsu [1]   (divine name — not decomposed into lemma)

Source: m u - n a - d u 3 [V_ctx]
Target: du₃ [build]
```

#### Step 5: CoNLL-U Output
```
# text_id = P232275
# surface = cylinder_a
# line = i.1-2
# language = sux (Sumerian)
# genre = royal_inscription

ID  FORM                LEMMA       UPOS  XPOS  FEATS                           HEAD  DEPREL
1   e₂                  e           NOUN  N     Case=Abs                        3     obj
2   nin-ĝir₂-su-ka-ni  Ninĝirsu    PROPN DN    Case=Gen|Person[poss]=3|Num=Sg  1     nmod
3   mu-na-du₃           du₃         VERB  V     Person=3|Ventive=Yes            0     root
```

#### Step 6: Full Schema Record (for token #3: mu-na-du₃)
```json
{
  "token_id": "uuid-001",
  "position": {"text": "P232275", "surface": "cylinder_a", "line": "i.2", "word": 2},

  "graphemic_layer": {
    "sign_sequence": [
      {"sign_id": "MU",  "unicode": "U+1222C", "damage": "intact"},
      {"sign_id": "NA",  "unicode": "U+1223E", "damage": "intact"},
      {"sign_id": "DU₃", "unicode": "U+12085", "damage": "intact"}
    ]
  },

  "reading_layer": {
    "transliteration": "mu-na-du₃",
    "function_per_sign": ["syllabogram", "syllabogram", "logogram+syllabogram"],
    "source_language_per_sign": ["Sumerian", "Sumerian", "Sumerian"],
    "phonetic_reading": "munadu",
    "reading_confidence": 0.97,
    "alternative_readings": []
  },

  "linguistic_layer": {
    "target_language": "Sumerian",
    "lemma": "du₃",
    "oracc_signature": "du[build]V/t",
    "pos": {"upos": "VERB", "xpos": "V"},
    "morphological_analysis": {
      "type": "sumerian_verbal_chain",
      "template": {
        "modal_prefix": null,
        "conjugation_prefix": "mu-",
        "ventive": "mu-",
        "dimensional_prefix": "-na-",
        "stem": "du₃",
        "person_suffix": null
      },
      "person_agent": "3sg",
      "person_patient": "3sg.dative (na = 'for him/her')",
      "transitivity": "transitive",
      "aspect": "perfective"
    },
    "annotation_provenance": {
      "method": "BabyLemmatizer_v2.2",
      "model": "sumerian-lit",
      "confidence": 0.96,
      "human_review": "unreviewed"
    }
  },

  "semantic_layer": {
    "translation_en": "he built (it for him)",
    "semantic_domain": "construction",
    "parallel_texts": ["Gudea Statue B v.12", "Gudea Cyl B xiv.5"]
  }
}
```

#### Step 7: Human-Readable Translation
```
e₂        nin-ĝir₂-su-ka-ni     mu-na-du₃
temple     of-his-Ninĝirsu       he.built.for.him

"He built the temple of his (god) Ninĝirsu for him."
```

**Scholarly note**: The verbal prefix chain `mu-na-` is debated. `mu-` is typically analyzed as a "ventive" prefix (motion toward speaker/reference point), while `-na-` is a dative dimensional prefix ("for him"). Some grammarians (Jagersma) analyze `mu-` differently from others (Zólyomi, Edzard). Your schema records the analysis but should flag the theoretical framework used.

---

### AKKADIAN (Neo-Assyrian Dialect)

**Source**: Based on Esarhaddon's building inscriptions (c. 681–669 BCE)
**Genre**: Royal building inscription

#### Step 2: Transliteration
```
É.SAG.ÍL   ú-šak-lil
```

#### Reading Decisions
| Sign(s) | Reading | Function | Notes |
|---------|---------|----------|-------|
| É | *bīt-* | Sumerogram | = Akkadian *bītu* "house, temple" |
| SAG | *rēš-* | Sumerogram (part of compound) | = *rēštu* "foremost" |
| ÍL | — | Sumerogram (part of compound) | É.SAG.ÍL = Esagil, Marduk's temple in Babylon |
| ú | *ú* | Syllabogram | Verbal prefix |
| šak | *šak* | Syllabogram | |
| lil | *lil* | Syllabogram | |

**Key complication**: É.SAG.ÍL is written entirely in Sumerograms but is a **proper noun** (Esagil, the temple of Marduk). A naive system reading each logogram separately would get "house-head-lift" — the etymological components — but the actual meaning is a temple name. Your schema needs to handle **compound Sumerograms that form proper nouns**.

#### Step 3: Tokenization (BabyLemmatizer Mode 0)
```
Raw:        É.SAG.ÍL    ú-šak-lil
Tokenized:  É.SAG.ÍL    u š a k l i l

Logograms preserved as tokens; syllabic signs broken to characters.
Subscript numbers stripped (no ú₂ distinction needed for Akkadian).
```

#### Step 4: BabyLemmatizer Output
```
POS:    TN     V
Lemma:  Esagil šuklulu

(TN = Temple Name; šuklulu = "to complete" in the Š-stem)
```

#### Step 5: CoNLL-U
```
# text_id = Esarhaddon_prism_B
# language = akk-x-neoass
# genre = royal_inscription

ID  FORM        LEMMA     UPOS   XPOS  FEATS
1   É.SAG.ÍL    Esagil    PROPN  TN    _
2   ú-šak-lil   šuklulu   VERB   V     Stem=Š|Tense=Pret|Person=3|Gender=Masc|Number=Sg
```

#### Step 6: Full Schema Record (for token #2: ú-šak-lil)
```json
{
  "token_id": "uuid-002",

  "graphemic_layer": {
    "sign_sequence": [
      {"sign_id": "U₂", "unicode": "U+12311", "damage": "intact"},
      {"sign_id": "ŠAK", "unicode": "...", "damage": "intact"},
      {"sign_id": "LIL", "unicode": "...", "damage": "intact"}
    ]
  },

  "reading_layer": {
    "transliteration": "ú-šak-lil",
    "function_per_sign": ["syllabogram", "syllabogram", "syllabogram"],
    "source_language_per_sign": ["Akkadian", "Akkadian", "Akkadian"],
    "phonetic_reading": "ušaklil"
  },

  "linguistic_layer": {
    "target_language": "Akkadian",
    "dialect": "Neo-Assyrian",
    "lemma": "šuklulu",
    "oracc_signature": "šuklulu[complete]V",
    "pos": {"upos": "VERB", "xpos": "V"},
    "morphological_analysis": {
      "type": "akkadian_root_pattern",
      "root": "k-l-l",
      "stem": "Š",
      "pattern": "ušaklil (Š preterite 3ms)",
      "binyan_meaning": "causative: 'to cause to be complete' = 'to complete, finish'",
      "base_meaning_G": "kalālu = 'to be complete'",
      "person": "3ms",
      "tense": "preterite"
    },
    "annotation_provenance": {
      "method": "BabyLemmatizer_v2.2",
      "model": "neo-assyrian",
      "confidence": 0.94,
      "dictionary_confirmed": true
    }
  },

  "semantic_layer": {
    "translation_en": "he completed",
    "note": "Š-stem of KLL: 'to make complete' — standard verb in building inscriptions"
  }
}
```

#### Step 7: Translation
```
É.SAG.ÍL    ú-šak-lil
Esagil       he.completed

"He completed Esagil (the temple of Marduk)."
```

**Arabic parallel for your intuition**: The root k-l-l relates to Arabic k-m-l (كمل "to be complete"). The Š-stem (causative) functions like Arabic Form IV: أكمل *akmala* "he completed." The vowel pattern *u-a-CiC* in the Š preterite is regular.

---

### HITTITE

**Source**: Based on Hattušili III building inscription style (c. 1267–1237 BCE)
**Genre**: Royal building inscription

#### Step 2: Transliteration
```
nu   É.DINGIR-LIM   ar-ḫa   wa-aḫ-nu-nu-un
```

#### Reading Decisions — The Three-Language Problem
| Written | Source Language | Function | Read as (Hittite) | Notes |
|---------|---------------|----------|-------------------|-------|
| nu | Hittite | Hittite particle | *nu* | Clause-initial connective "and, then" |
| É | Sumerian | Sumerogram | *parn-* or *karimmn-* | "house" or "temple" — WHICH Hittite word? |
| DINGIR | Sumerian | Sumerogram | *siun-* | "god" — part of compound "house of god" = temple |
| -LIM | Akkadian | Akkadogram | (morphological indicator) | Akkadian *ilim* (gen. of *ilum* "god") — tells scribe this is the genitive form |
| ar-ḫa | Hittite | Syllabographic | *arḫa* | "away, completely" (preverb) |
| wa-aḫ-nu-nu-un | Hittite | Syllabographic | *waḫnunun* | "I turned (= renovated)" |

**Critical ambiguity**: É.DINGIR-LIM could be:
- *parn- šiunaš* "house of the god" (using native Hittite words)
- *karimmi-* "temple" (a different Hittite word entirely)
- We genuinely don't know what the scribe would have said aloud

This is the **Sumerogram/Akkadogram problem** at its most acute. The sign sequence tells us the MEANING ("god-house" = temple) but not the Hittite WORD.

#### Step 3: Tokenization
```
Mode: 0 (unindexed logo-syllabic for Hittite)

Raw:        nu    É.DINGIR-LIM    ar-ḫa    wa-aḫ-nu-nu-un
Tokenized:  nu    É.DINGIR-LIM    a r ḫ a  w a a ḫ n u n u u n

Sumerograms/Akkadograms preserved as unit tokens.
Syllabic Hittite broken to characters.
```

#### Step 4: Lemmatization
```
⚠️ NO PRETRAINED BABYLEMMATIZER MODEL EXISTS FOR HITTITE

Hypothetical output if one existed:
  POS:    CNJ    N          PREV   V
  Lemma:  nu     É.DINGIR   arḫa   waḫnu-

Actual current workflow: MANUAL annotation by Hittitologist
```

**This is a key gap.** Your pipeline must handle the case where automated lemmatization is unavailable. The schema records `method: "human"` in annotation_provenance.

#### Step 5: CoNLL-U (manually annotated)
```
# text_id = CTH_88_example
# language = hit (Hittite)
# genre = royal_inscription

ID  FORM               LEMMA          UPOS  XPOS  FEATS
1   nu                 nu             CCONJ CNJ   _
2   É.DINGIR-LIM       É.DINGIR       NOUN  N     Case=Acc|Number=Sing
3   ar-ḫa              arḫa           ADV   PREV  _
4   wa-aḫ-nu-nu-un     waḫnu-         VERB  V     Person=1|Number=Sg|Tense=Pret
```

#### Step 6: Full Schema Record (for token #2: É.DINGIR-LIM)
```json
{
  "token_id": "uuid-003",

  "graphemic_layer": {
    "sign_sequence": [
      {"sign_id": "E₂", "unicode": "U+1208D", "damage": "intact"},
      {"sign_id": "AN/DINGIR", "unicode": "U+1202D", "damage": "intact"},
      {"sign_id": "LIM", "unicode": "...", "damage": "intact"}
    ]
  },

  "reading_layer": {
    "transliteration": "É.DINGIR-LIM",
    "function_per_sign": ["Sumerogram", "Sumerogram", "Akkadogram"],
    "source_language_per_sign": ["Sumerian", "Sumerian", "Akkadian"],
    "phonetic_reading": "UNKNOWN — logographic writing hides Hittite pronunciation",
    "reading_confidence": 0.60,
    "alternative_readings": [
      {"reading": "parn šiunaš", "confidence": 0.35, "note": "if decomposed to Hittite words"},
      {"reading": "karimmi-", "confidence": 0.25, "note": "alternative Hittite word for temple"},
      {"reading": "OPAQUE", "confidence": 0.40, "note": "phonetic form genuinely unknown"}
    ]
  },

  "linguistic_layer": {
    "target_language": "Hittite",
    "lemma": "É.DINGIR",
    "lemma_note": "Sumerographic lemma — Hittite word uncertain",
    "pos": {"upos": "NOUN", "xpos": "N"},
    "morphological_analysis": {
      "type": "hittite_nominal",
      "case": "accusative",
      "number": "singular",
      "note": "Case inferred from syntax (direct object of waḫnu-), not from logographic spelling"
    },
    "annotation_provenance": {
      "method": "human",
      "annotator": "hittitologist",
      "confidence": 0.75,
      "model": null,
      "uncertainty_flags": ["logographic_opacity", "hittite_word_unknown"]
    }
  },

  "semantic_layer": {
    "translation_en": "the temple",
    "semantic_certainty": "high — meaning is clear from logograms",
    "phonetic_certainty": "low — Hittite pronunciation uncertain",
    "note": "Meaning certain; pronunciation uncertain. A common Hittite problem."
  }
}
```

#### Step 7: Translation
```
nu   É.DINGIR-LIM    ar-ḫa    wa-aḫ-nu-nu-un
and  temple(ACC)      compl.   I.renovated

"And I (completely) renovated the temple."
```

**German parallel**: The sentence structure maps well to German subordinate-clause order: "...und den Tempel renovierte ich." SOV with preverb *arḫa* functioning like German separable prefixes (um-bauen → "ich baute den Tempel um").

---

### ELAMITE

**Source**: Based on Šilhak-Inšušinak building inscription style (c. 1150–1120 BCE, Susa)
**Genre**: Royal building inscription

#### Step 2: Transliteration
```
ú  zi-ya-an   ku-ši-ik   hu-ut-ta-aš
```

#### Reading Decisions
| Sign | Reading | Function | Notes |
|------|---------|----------|-------|
| ú | *u* | Syllabogram | Conjunction "and/then" (or relative pronoun — debated) |
| zi-ya-an | *ziyan* | Syllabographic | "temple" (one of the best-attested Elamite nouns) |
| ku-ši-ik | *kušik* | Syllabographic | "I built/made" (or "he built" — person marking debated) |
| hu-ut-ta-aš | *huttaš* | Syllabographic | "I built/made" (alternative verb — wait, are BOTH verbs present? See below) |

**Elamite complication**: Middle Elamite inscriptions often use formulaic verbal pairs. The exact parsing of *kušik huttaš* is debated — is it two verbs ("I fashioned and built"), or a verb + auxiliary ("I caused to be built"), or something else? The morphological analysis of both forms is uncertain.

#### Step 3: Tokenization
```
Mode: 0 (unindexed logo-syllabic)

Raw:        ú    zi-ya-an    ku-ši-ik    hu-ut-ta-aš
Tokenized:  u    z i y a n   k u š i k   h u t t a š

Elamite is mostly syllabographic — no Sumerograms in this example.
Fewer sign-reading ambiguities than Akkadian, but the LANGUAGE is less understood.
```

#### Step 4: Lemmatization
```
⚠️ NO BABYLEMMATIZER MODEL FOR ELAMITE

Manual annotation only:
  POS:    REL?    N         V        V
  Lemma:  u       ziyan     kuši-    hutta-

Confidence: LOW on all morphological analysis
```

#### Step 5: CoNLL-U (manually annotated, high uncertainty)
```
# text_id = ME_SilhakInsusinak_01
# language = elx (Elamite)
# period = Middle Elamite
# genre = royal_inscription

ID  FORM          LEMMA    UPOS   XPOS   FEATS
1   ú             u        PRON?  REL?   _
2   zi-ya-an      ziyan    NOUN   N      Case=Acc?
3   ku-ši-ik      kuši-    VERB   V      Person=1?|Tense=Pret?
4   hu-ut-ta-aš   hutta-   VERB   V      Person=1?|Tense=Pret?|Causative?
```

Note the question marks — this is real uncertainty, not laziness. The FEATS are genuinely debated.

#### Step 6: Full Schema Record (for token #3: ku-ši-ik)
```json
{
  "token_id": "uuid-004",

  "graphemic_layer": {
    "sign_sequence": [
      {"sign_id": "KU", "unicode": "U+121AA", "damage": "intact"},
      {"sign_id": "ŠI", "unicode": "...", "damage": "intact"},
      {"sign_id": "IK", "unicode": "...", "damage": "intact"}
    ]
  },

  "reading_layer": {
    "transliteration": "ku-ši-ik",
    "function_per_sign": ["syllabogram", "syllabogram", "syllabogram"],
    "source_language_per_sign": ["Elamite", "Elamite", "Elamite"],
    "phonetic_reading": "kušik"
  },

  "linguistic_layer": {
    "target_language": "Elamite",
    "period": "Middle Elamite",
    "lemma": "kuši-",
    "lemma_certainty": "medium — attested in multiple inscriptions",
    "pos": {"upos": "VERB", "xpos": "V"},
    "morphological_analysis": {
      "type": "elamite_verbal",
      "stem": "kuši-",
      "suffix": "-k",
      "suffix_analysis": [
        {"interpretation": "1sg subject marker", "scholar": "Grillot-Susini 1987", "confidence": 0.4},
        {"interpretation": "3sg subject marker", "scholar": "Stolper (various)", "confidence": 0.3},
        {"interpretation": "perfective marker", "scholar": "Khačikjan 1998", "confidence": 0.2}
      ],
      "note": "Basic meaning 'to build/make' is agreed; person marking is debated"
    },
    "annotation_provenance": {
      "method": "human",
      "annotator": "elamitologist",
      "confidence": 0.55,
      "uncertainty_flags": [
        "morphology_debated",
        "person_marking_uncertain",
        "no_automated_tools_available"
      ]
    }
  },

  "semantic_layer": {
    "translation_en": "I/he built",
    "semantic_certainty": "medium — 'build/make' is likely, person is uncertain",
    "competing_translations": [
      {"translation": "I built", "probability": 0.5},
      {"translation": "he built", "probability": 0.3},
      {"translation": "was built", "probability": 0.2}
    ]
  }
}
```

#### Step 7: Translation
```
ú       zi-ya-an    ku-ši-ik    hu-ut-ta-aš
REL?    temple(ACC?) I/he.built  I/he.fashioned

"(The temple which?) I built (and) fashioned."
  — OR —
"I built and fashioned the temple."
  — OR —
"The temple was built and fashioned."
```

The range of possible translations illustrates why Elamite demands the highest uncertainty tolerance in your schema.

---

## Side-by-Side Summary: Same Phrase, Four Pipelines

| Pipeline Stage | Sumerian | Akkadian (NA) | Hittite | Elamite |
|---------------|----------|---------------|---------|---------|
| **Physical object** | Clay cylinder | Clay prism | Clay tablet | Clay tablet/brick |
| **Writing system** | Logo-syllabic | Logo-syllabic (heavy Sumerograms) | Tri-lingual (Sum+Akk+Hit signs) | Mostly syllabic |
| **Sign reading ambiguity** | HIGH (DU₃ vs DU vs GUB) | HIGH (logograms hide pronunciation) | VERY HIGH (3 languages in 1 text) | LOW (mostly syllabic) |
| **Language understanding** | Good (debated grammar) | Very good | Good | Poor |
| **BabyLemmatizer available?** | ✅ Yes (lit + admin models) | ✅ Yes (multiple dialect models) | ❌ No model exists | ❌ No model exists |
| **Tokenization mode** | 1 (indexed) | 0 (unindexed) | 0 (unindexed) | 0 (unindexed) |
| **Lemmatization confidence** | 93–96% automated | 94–96% automated | Manual only | Manual only |
| **Morphology confidence** | Medium (debated grammar) | High | High (when phonetic) | Low |
| **Translation confidence** | High for formulaic texts | High for formulaic texts | High for meaning, low for pronunciation | Medium meaning, low grammar |
| **Key pipeline challenge** | Verbal chain analysis | Sumerogram resolution | Logographic opacity (meaning clear, pronunciation unknown) | Everything is uncertain |

---

## Part 2: A Challenging Case Scholars Would Debate

### The Hittite Plague Prayer of Muršili II — Where Three Writing Systems Collide and Meaning Fractures

**Source**: CTH 378.II, "Second Plague Prayer of Muršili II" (c. 1318–1295 BCE)
**Genre**: Royal prayer/ritual text
**Why it's hard**: This text uses dense logographic writing, has damage, contains a passage where the interpretation hinges on whether a Sumerogram is read one way or another, and the theological implications of the translation are significant.

#### The Passage

A partially damaged line from the prayer. Muršili is asking the gods why they have sent plague upon Hatti. He references something his father Šuppiluliuma did that angered the gods.

**What's on the tablet (reconstructed transliteration):**
```
nu    A-BU-YA    ᵈUTU    ᵘʳᵘKÙ.BABBAR-aš    DINGIR^{MEŠ}-aš
SISKUR    SISKUR    ŠA    ᵘʳᵘKÙ.BABBAR    ar-ḫa    wa-ar-nu-ut
```

#### Layer-by-Layer Decoding

Let's unpack every token:

**Token 1: `nu`**
```
graphemic:  𒉡
reading:    nu
function:   Hittite particle
language:   Hittite (phonetic)
lemma:      nu (clause connector "and, then")
confidence: 0.99
debate:     None. This is unambiguous.
```

**Token 2: `A-BU-YA`**
```
graphemic:  𒀀-𒁍-𒅀
reading:    A-BU-YA
function:   Akkadogram + Hittite complement
language:   Akkadian logogram + Hittite possessive

Decoding:
  A-BU = Akkadian word abu "father" (Akkadogram)
  -YA  = Hittite possessive suffix? OR Akkadian 1sg possessive -ya?

  Read as Hittite: *attaš=miš* ("my father") — but we're GUESSING the Hittite
  OR the scribe simply wrote the Akkadian word *abūya* "my father"

lemma:      atta- (Hittite "father") or recorded as A-BU logographically
confidence: 0.85 — meaning certain, Hittite form uncertain
debate:     Minor. The possessive suffix convention is unclear.
```

**Token 3: `ᵈUTU`**
```
graphemic:  𒀭 𒌓
reading:    ᵈUTU
function:   Determinative (ᵈ) + Sumerogram (UTU)

Decoding:
  ᵈ = DINGIR sign as determinative (silent, marks divine name)
  UTU = Sumerian sun-god name, used logographically

  Read as Hittite: *ᴵštanu-* (the Hittite Sun God)
  OR: *ᵈUTU-ši* (the Sun Goddess of Arinna, chief deity of Hatti)

  ⚠️ THIS IS WHERE THE DEBATE BEGINS

  In Hittite religious texts, ᵈUTU can refer to:
  (a) The Sun God (masculine, celestial) — Hittite Ištanu
  (b) The Sun Goddess of Arinna (feminine, chief deity) — the supreme goddess of Hatti
  (c) The Sun God of Heaven — a distinct figure
  (d) "His/Her Majesty" — the king himself (royal title!)

  In THIS context (plague prayer, addressing gods about father's sins):
  - If ᵈUTU = "my father, His Majesty (the king)" → Muršili is saying his father the king...
  - If ᵈUTU = "the Sun God(dess)" → Muršili is saying the Sun Deity...

  The sign is identical in all cases. Only context disambiguates.

lemma:      ᵈUTU (recorded logographically; Hittite word depends on interpretation)
confidence: 0.50 — FOUR possible referents
debate:     MAJOR. See below.
```

**Token 4: `ᵘʳᵘKÙ.BABBAR-aš`**
```
graphemic:  𒌷 𒆬 𒌓 - 𒀸
reading:    ᵘʳᵘKÙ.BABBAR-aš
function:   Determinative (ᵘʳᵘ = city) + Sumerogram compound + Hittite complement

Decoding:
  ᵘʳᵘ = URU determinative (silent, marks city name)
  KÙ.BABBAR = literally "pure/silver" in Sumerian
  -aš = Hittite genitive singular ending

  ᵘʳᵘKÙ.BABBAR is a known Sumerogram for ḪATTUŠA (the Hittite capital)

  BUT WAIT: KÙ.BABBAR without the URU determinative means "silver"
  WITH the URU determinative it's a city name
  The determinative is CRITICAL for disambiguation here

  Read as Hittite: *Ḫattušaš* (genitive: "of Ḫattuša")

lemma:      Ḫattuša
pos:        PROPN (proper noun, place name)
confidence: 0.92 (URU determinative makes this fairly clear)
debate:     Minor — the identification of URU.KÙ.BABBAR = Ḫattuša is well established
```

**Token 5: `DINGIR^{MEŠ}-aš`**
```
graphemic:  𒀭 𒈨 - 𒀸
reading:    DINGIR^{MEŠ}-aš
function:   Sumerogram + Sumerogram (plural marker) + Hittite complement

Decoding:
  DINGIR = "god" (Sumerogram)
  MEŠ = Sumerian plural marker (used as pluralizer in Hittite writing)
  -aš = Hittite genitive plural? OR genitive singular?

  ⚠️ GRAMMATICAL DEBATE:
  In Hittite, genitive plural of "god" (*šiunaš*) and genitive singular
  look the same in some paradigms. The MEŠ should indicate plural, but:
  - Is this "of the gods" (genitive plural)?
  - Or is MEŠ a scribal convention for the collective "the gods" as a group?

  Read as Hittite: *šiunaš* (genitive, "of the god(s)")

lemma:      šiu- ("god")
confidence: 0.80
debate:     Moderate — number (singular vs. plural) affects meaning
```

**Tokens 6–7: `SISKUR SISKUR`**
```
graphemic:  𒁶 𒁶 (repeated)
reading:    SISKUR SISKUR
function:   Sumerogram (repeated for emphasis or plurality)

Decoding:
  SISKUR = Sumerian word for "offering, sacrifice"
  Repeated: could mean "offerings" (plural) or "offering-offering" (intensive)

  Read as Hittite: unknown — what Hittite word for "offering" would the scribe say?
  Perhaps *šipant-* ("libation, offering")? Or *malḫeššar* ("ritual")?

  ⚠️ LOGOGRAPHIC OPACITY: We know the MEANING but not the WORD

lemma:      SISKUR (left logographic)
confidence: 0.70 for meaning, 0.30 for Hittite word
debate:     Moderate — is this "offerings" or "ritual sacrifices" or "the offering ritual"?
```

**Token 8: `ŠA`**
```
graphemic:  𒊭
reading:    ŠA
function:   Akkadogram

Decoding:
  ŠA = Akkadian preposition *ša* "of, which, belonging to"
  Used logographically in Hittite for the genitive construction

  Read as Hittite: probably just a graphic convention, not a spoken word
  OR: corresponds to Hittite relative pronoun *kuiš*?

lemma:      ŠA (Akkadographic convention)
confidence: 0.85 for meaning
debate:     Minor — how to interpret the syntactic function
```

**Token 9: `ᵘʳᵘKÙ.BABBAR`** (same as token 4 but without the Hittite complement)
```
Same city name, Ḫattuša, but this time without case ending.
In Hittite it would be something like the nominative or bare stem.
```

**Tokens 10–11: `ar-ḫa wa-ar-nu-ut`**
```
graphemic:  𒅈-𒄩 𒉿-𒅈-𒉡-𒌑
reading:    ar-ḫa wa-ar-nu-ut
function:   Hittite phonetic (preverb + verb)

Decoding:
  ar-ḫa = *arḫa* "away, completely" (preverb)
  wa-ar-nu-ut = *warnut*

  ⚠️ MAJOR DEBATE: Which verb is this?

  OPTION A: *warnuut* from *warnā-* / *warnu-* "to burn (transitive)"
    → "burned away" the offerings
    Meaning: "My father burned/destroyed the offerings of the gods of Ḫattuša"
    Implication: Šuppiluliuma committed sacrilege by burning sacred offerings

  OPTION B: *warnut* from *warnu-* "to let burn (causative)"
    → "had (them) burned" — same verb but with slightly different agency
    Implication: He ordered the offerings destroyed

  OPTION C: Some scholars have read the sign differently as a form of
    *warriš-* "to help" or *warra-* "to wash"
    → "washed away" the offerings (purification context)
    Implication: He performed purification on the offerings — OPPOSITE meaning

The difference between "burned the offerings" and "purified the offerings"
is theologically enormous. Did Šuppiluliuma commit sacrilege or perform piety?
The plague — sent as divine punishment — makes sense under interpretation A,
but interpretation C would change our understanding of the entire prayer.

CURRENT SCHOLARLY CONSENSUS: Option A (*warnu-* "to burn") is favored by most
Hittitologists (Singer 2002, de Roos 2007), but the debate is not fully closed.

lemma:      warnu- (to burn) ← majority reading
            warra- (to wash) ← minority reading
confidence: 0.70 for warnu-, 0.15 for causative variant, 0.10 for warra-, 0.05 other
```

#### Full Schema Record — The Debated Verb

```json
{
  "token_id": "uuid-005",
  "position": {"text": "CTH_378.II", "line": "iii.14", "word": 6},

  "graphemic_layer": {
    "sign_sequence": [
      {"sign_id": "AR", "damage": "intact"},
      {"sign_id": "HA", "damage": "intact"},
      {"sign_id": "WA", "damage": "partial_top"},
      {"sign_id": "AR", "damage": "intact"},
      {"sign_id": "NU", "damage": "intact"},
      {"sign_id": "UT", "damage": "edge_damage"}
    ],
    "overall_condition": "mostly_legible",
    "condition_note": "WA sign has minor damage to upper wedges; UT sign near tablet edge with slight chipping"
  },

  "reading_layer": {
    "transliteration": "ar-ḫa wa-ar-nu-ut",
    "is_compound_expression": true,
    "components": [
      {
        "part": "ar-ḫa",
        "function": "preverb",
        "source_language": "Hittite",
        "reading_confidence": 0.95
      },
      {
        "part": "wa-ar-nu-ut",
        "function": "finite_verb",
        "source_language": "Hittite",
        "reading_confidence": 0.70,
        "alternative_readings": [
          {
            "reading": "wa-ar-nu-ut",
            "normalization": "warnut",
            "confidence": 0.75,
            "note": "Standard reading; WA sign slightly damaged but legible"
          },
          {
            "reading": "wa-ar-ri-eš",
            "normalization": "warriš",
            "confidence": 0.08,
            "note": "Requires different reading of NU and UT signs; unlikely given sign forms"
          }
        ]
      }
    ]
  },

  "linguistic_layer": {
    "target_language": "Hittite",
    "interpretations": [
      {
        "interpretation_id": "A",
        "label": "Majority reading (Singer 2002, de Roos 2007)",
        "lemma": "warnu-",
        "pos": "VERB",
        "morphological_analysis": {
          "stem": "warnu-",
          "meaning": "to burn (causative of war- 'to burn [intrans.]')",
          "conjugation": "-mi verb",
          "tense": "preterite",
          "person": "3sg",
          "voice": "active"
        },
        "preverb": "arḫa (completive: 'completely, away')",
        "combined_meaning": "he burned away / he completely burned",
        "confidence": 0.70,
        "supporting_evidence": [
          "arḫa warnu- is a well-attested phrasal verb meaning 'to burn completely'",
          "Context of divine punishment for sacrilege supports destructive meaning",
          "Parallel passages in other plague prayers reference destructive acts"
        ]
      },
      {
        "interpretation_id": "B",
        "label": "Causative nuance (Haas 1994)",
        "lemma": "warnu-",
        "pos": "VERB",
        "morphological_analysis": {
          "stem": "warnu-",
          "meaning": "to cause to burn / to have burned",
          "conjugation": "-mi verb",
          "tense": "preterite",
          "person": "3sg",
          "voice": "causative"
        },
        "preverb": "arḫa",
        "combined_meaning": "he had (someone) burn away",
        "confidence": 0.15,
        "supporting_evidence": [
          "Same verb, different shade of agency — king ordered, didn't personally burn",
          "Royal inscriptions often use causative constructions for delegated actions"
        ]
      },
      {
        "interpretation_id": "C",
        "label": "Minority reading (purification)",
        "lemma": "warra-",
        "pos": "VERB",
        "morphological_analysis": {
          "stem": "warra-",
          "meaning": "to wash, purify",
          "conjugation": "-mi verb (?)",
          "tense": "preterite",
          "person": "3sg"
        },
        "preverb": "arḫa",
        "combined_meaning": "he washed away / he purified",
        "confidence": 0.10,
        "supporting_evidence": [
          "arḫa warra- could mean 'to wash away' (purification)",
          "Would change theological reading entirely: piety instead of sacrilege",
          "Morphological form is difficult to reconcile with known paradigm of warra-"
        ],
        "counter_evidence": [
          "The -nu- infix is hard to explain if the root is warra-",
          "No clear parallel for arḫa warra- in this ritual context",
          "Broader narrative context strongly favors sacrilege interpretation"
        ]
      }
    ],

    "consensus": {
      "preferred_interpretation": "A",
      "consensus_strength": "moderate",
      "note": "Most scholars favor warnu- 'to burn' but the debate illustrates how logographic writing + minor damage can create genuine ambiguity with major semantic consequences"
    },

    "annotation_provenance": {
      "method": "human_scholarly_consensus",
      "sources": [
        "Singer, I. (2002). Hittite Prayers. SBL WAW 11.",
        "de Roos, J. (2007). Hittite Votive Texts. PIHANS 109.",
        "Haas, V. (1994). Geschichte der hethitischen Religion. HdO I/15."
      ]
    }
  },

  "semantic_layer": {
    "translation_options": [
      {"text": "he burned away (the offerings)", "interpretation": "A", "confidence": 0.70},
      {"text": "he had (the offerings) burned", "interpretation": "B", "confidence": 0.15},
      {"text": "he purified (the offerings)", "interpretation": "C", "confidence": 0.10}
    ],
    "theological_impact": "HIGH — determines whether Šuppiluliuma committed sacrilege or performed legitimate ritual, which in turn determines the logic of the entire plague prayer",
    "cross_references": [
      "CTH 378.I (First Plague Prayer) — parallel passage",
      "CTH 376 (Plague Prayer of Muršili, different version)",
      "CTH 381 (Prayer of Muwatalli II) — similar construction"
    ]
  }
}
```

#### The Full Passage Translated — Three Versions

**Interpretation A (majority: warnu- "to burn"):**
```
nu    A-BU-YA       ᵈUTU         ᵘʳᵘKÙ.BABBAR-aš    DINGIR-MEŠ-aš
and   my.father     His.Majesty   of.Ḫattuša          of.the.gods

SISKUR  SISKUR   ŠA   ᵘʳᵘKÙ.BABBAR   ar-ḫa  wa-ar-nu-ut
offerings        of    Ḫattuša         away   burned

"And my father, His Majesty, burned away the offerings of the gods of Ḫattuša."
```
→ Šuppiluliuma committed sacrilege → gods sent plague as punishment → prayer makes sense as atonement

**Interpretation C (minority: warra- "to wash"):**
```
"And my father, His Majesty, purified the offerings of the gods of Ḫattuša."
```
→ Šuppiluliuma performed correct ritual → why would gods punish this? → entire prayer logic changes

**The ᵈUTU ambiguity adds another layer:**

If ᵈUTU = "His Majesty" (royal title), the sentence is about the king.
If ᵈUTU = "the Sun God," the sentence is about the Sun God doing something to the offerings.
If ᵈUTU = "the Sun Goddess of Arinna" (chief deity), the theological implications shift again.

Most scholars read ᵈUTU here as the royal title "His Majesty" based on context, but the sign itself is identical in all cases.

---

## What This Example Reveals About Schema Requirements

### 1. Multiple interpretations must coexist as first-class entities
The schema can't store "the answer" — it must store **competing interpretations with metadata**:
- Who proposed each interpretation
- What evidence supports/contradicts each
- What the current consensus is (and how strong)
- What downstream effects each interpretation has (e.g., theological implications)

### 2. Confidence varies independently across layers
For `É.DINGIR-LIM`:
- **Graphemic confidence**: HIGH (signs clearly legible)
- **Semantic confidence**: HIGH (meaning "temple" is clear)
- **Phonetic confidence**: LOW (Hittite pronunciation unknown)
- **Morphological confidence**: MEDIUM (genitive case from -aš complement)

A single "confidence score" is insufficient. Your schema needs **per-layer confidence**.

### 3. Logographic opacity is systematically different from damage
When a sign is damaged, we're uncertain about WHAT IS WRITTEN.
When a Sumerogram is used in Hittite, we know what's written but are uncertain about WHAT WAS SAID.
These are fundamentally different types of uncertainty and your schema must distinguish them:

```
uncertainty_type:
  - "physical_damage"      → affects graphemic layer
  - "sign_ambiguity"       → affects reading layer (polyvalence)
  - "logographic_opacity"  → affects linguistic layer (known meaning, unknown pronunciation)
  - "grammatical_debate"   → affects morphological analysis
  - "semantic_debate"      → affects translation
  - "language_poorly_known" → affects everything (Elamite)
```

### 4. Cross-language sign identity ≠ linguistic identity
The sign DINGIR (𒀭) appears 3 times in our Hittite passage:
1. As a **determinative** before UTU (silent, marks divine name)
2. As a **Sumerogram** meaning "god(s)" in DINGIR^{MEŠ}
3. Conceptually, as part of É.DINGIR where it contributes meaning

Same sign. Three different functions. Different linguistic analyses each time. Your schema's sign-function-per-occurrence tracking is essential.

### 5. The pipeline breaks at different stages for different languages
```
                    Sumerian    Akkadian    Hittite     Elamite
                    ────────    ────────    ────────    ────────
Sign ID (OCR)       works       works       works       works
Reading assignment  hard        hard        very hard   easier
Tokenization        automated   automated   automated   automated
POS-tagging         automated   automated   MANUAL      MANUAL
Lemmatization       automated   automated   MANUAL      MANUAL
Morphology          debated     good        good*       debated
Translation         good**      good        good**      poor

*  when phonetically written; opaque for logograms
** for formulaic texts; harder for literary/ritual
```

Your pipeline architecture must gracefully degrade: when BabyLemmatizer has no model, the same schema fields are filled by human annotators, with `method: "human"` in provenance. The schema doesn't care who filled it — it cares that the data is there, with honest confidence scores.

---

## Part 3: How the Schema Connects the Four Languages

### Cross-Language Entity Map for "Temple"

Here's how your schema links the concept "temple" across all four languages:

```
CONCEPT: "temple" (sacred building)

┌─────────────────────────────────────────────────────┐
│ SIGN: É (𒂍)                                         │
│   Sign name: E₂                                     │
│   Unicode: U+1208D                                  │
│   Primary Sumerian reading: e₂ "house, temple"      │
│                                                      │
│   Used in:                                           │
│   ├── Sumerian: e₂ (logogram) → lemma "e" [house]  │
│   ├── Akkadian: É → read as bītu(m) [house/temple] │
│   ├── Hittite: É → read as per- [house] (opaque)   │
│   └── Elamite: (rarely used as logogram)            │
└──────────────────────────┬──────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ DICT ENTRY   │  │ DICT ENTRY   │  │ DICT ENTRY       │
│ Sumerian     │  │ Akkadian     │  │ Hittite          │
│              │  │              │  │                   │
│ lemma: e₂    │  │ lemma: bītu  │  │ lemma: per-/parn-│
│ GW: house    │  │ GW: house    │  │ GW: house        │
│ POS: N       │  │ POS: N       │  │ POS: N           │
│ root: —      │  │ root: b-y-t  │  │ IE root: *per-   │
│              │  │ Heb: בית     │  │ (cf. German      │
│ compounds:   │  │ Ar: بيت      │  │  Pforte? debated)│
│  e₂-gal      │  │              │  │                   │
│  "big house" │  │ compounds:   │  │ Also: karimmi-   │
│  = palace    │  │  bīt ili     │  │  "temple" (may be │
│              │  │  "god-house" │  │  the word behind  │
│  e₂-dingir   │  │  = temple    │  │  É.DINGIR)       │
│  "god-house" │  │              │  │                   │
│  = temple    │  │              │  │                   │
└──────┬───────┘  └──────┬───────┘  └────────┬──────────┘
       │                 │                    │
       │     ┌───────────┼────────────────────┘
       │     │           │
       ▼     ▼           ▼
┌──────────────────────────────────────────────────────┐
│ CROSS-LINGUISTIC LINK                                 │
│                                                       │
│  type: "logographic_equivalence"                     │
│  sign: É (E₂)                                        │
│  sumerian_word: e₂                                   │
│  akkadian_word: bītu(m)     ← Semitic, unrelated    │
│  hittite_word: per-/parn-   ← IE, unrelated          │
│  elamite_word: ziyan-       ← Isolate, unrelated     │
│                                                       │
│  linguistic_relationship: NONE                       │
│  graphemic_relationship: SHARED SIGN                  │
│  semantic_relationship: EQUIVALENT MEANING            │
│                                                       │
│  note: Four completely unrelated words from four      │
│  unrelated language families, connected ONLY by the   │
│  shared writing system convention of using É for      │
│  "house/temple"                                       │
└──────────────────────────────────────────────────────┘
```

### Cross-Language Entity Map for the Elamite outlier

```
CONCEPT: "temple" in Elamite

┌──────────────────────────────────────────────────────┐
│ DICT ENTRY: Elamite                                   │
│                                                       │
│ lemma: ziyan                                         │
│ GW: temple                                           │
│ POS: N                                               │
│ attestation: frequent in Middle Elamite inscriptions │
│ written: zi-ya-an (syllabographic, NO Sumerogram)    │
│                                                       │
│ etymology: unknown (language isolate)                │
│ related_forms:                                       │
│   - ziyan-kuk "tower/ziggurat" (?)                  │
│   - ziyanam "to build a temple" (?) (debated)       │
│                                                       │
│ logographic_equivalents: none commonly used          │
│   (Elamite scribes rarely used É for this word,     │
│    preferring syllabographic spelling)               │
│                                                       │
│ cross_linguistic_links:                              │
│   - NO linguistic relationship to Sumerian e₂       │
│   - NO linguistic relationship to Akkadian bītu     │
│   - Possible loan from an unknown substrate?         │
│   - Debated connection to Dravidian? (very uncertain)│
└──────────────────────────────────────────────────────┘
```

The Elamite case is revealing: unlike Hittite, which heavily used Sumerograms, Elamite scribes tended to spell things out syllabically. This means we **know the pronunciation** of Elamite words better than Hittite ones — but we understand Hittite **grammar** better because it's Indo-European and we have comparative evidence.

---

## Part 4: Tools & Data Required at Each Pipeline Stage

### Complete Tool Chain

```
STAGE 1: ACQUISITION
━━━━━━━━━━━━━━━━━━━━
Input:  Physical tablet
Tools:  - RTI (Reflectance Transformation Imaging) or structured light 3D scanning
        - CDLI image repository (photographs)
        - GigaMesh (3D mesh processing for cuneiform)
Output: Digital images / 3D models
Data:   CDLI catalog (museum numbers, provenance, dating)

STAGE 2: SIGN IDENTIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input:  Digital images
Tools:  - DeepScribe (CNN for sign detection, JHU/UCLA)
        - CuneiformOCR projects (various)
        - Human collation (remains gold standard)
Output: Sequence of identified sign IDs
Data:   - Sign lists (MZL, aBZL, HZL) as reference
        - Unicode cuneiform block for standardized encoding
        - Training data: CDLI annotated tablets

STAGE 3: TRANSLITERATION
━━━━━━━━━━━━━━━━━━━━━━━━
Input:  Sign sequences
Tools:  - Human Assyriologist (primary)
        - Sign-to-reading models (research stage)
Output: ATF transliteration files
Data:   - ORACC project conventions
        - Period/region-specific sign value tables
        - Genre-specific expectations (building inscription → expect É, LUGAL, etc.)
Format: ATF (ASCII Transliteration Format)

STAGE 4: TOKENIZATION & FORMATTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input:  ATF files
Tools:  - ATF-to-CoNLL-U converters (Pagé-Perron scripts; CDLI tools)
        - BabyLemmatizer's built-in preprocessing
        - txt2conllu.py (BabyLemmatizer utility)
Output: CoNLL-U files (blank LEMMA, UPOS, XPOS fields)
Data:   - Language detection (which tokenization mode?)
        - Period metadata (affects expected sign values)

STAGE 5: POS-TAGGING & LEMMATIZATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input:  CoNLL-U (unlemmatized)
Tools:
  FOR SUMERIAN:
    - BabyLemmatizer (sumerian-lit or sumerian-admin model)
    - ePSD2 (dictionary validation)
    - L2 lemmatizer (ORACC, dictionary-based)
  FOR AKKADIAN:
    - BabyLemmatizer (dialect-specific model: neo-assyrian, babylonian-1st, etc.)
    - CAD / CDA (dictionary validation)
    - L2 lemmatizer
    - Akkademia (CNN transliteration + segmentation)
  FOR HITTITE:
    - NO AUTOMATED LEMMATIZER — human annotation
    - CHD (Chicago Hittite Dictionary) for reference
    - HPM (Hethitologie Portal Mainz) for text parallels
  FOR ELAMITE:
    - NO AUTOMATED LEMMATIZER — human annotation
    - EW (Elamisches Wörterbuch, Hinz & Koch) — dated but only option
    - Persepolis Fortification Archive publications
Output: CoNLL-U (with LEMMA, UPOS, XPOS, FEATS filled)
Data:   - ORACC annotated corpora (training data for neural models)
        - Glossaries per language and project
        - Override lexicons (BabyLemmatizer post-correction)

STAGE 6: MORPHOLOGICAL ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input:  Lemmatized CoNLL-U
Tools:
  FOR AKKADIAN:
    - BabyFST (finite-state morphological analyzer, Sahala 2020)
    - Future: BabyLemmatizer planned morphology module
  FOR SUMERIAN:
    - Manual (grammar debated; no consensus analyzer)
    - PPCS parser (Penn Parsed Corpus of Sumerian, for syntax)
  FOR HITTITE:
    - Manual (IE morphology relatively well understood)
  FOR ELAMITE:
    - Manual (morphology actively debated)
Output: FEATS column populated; schema morphological_analysis field
Data:   - Language-specific morphological templates
        - Paradigm tables (verb conjugations, noun declensions)

STAGE 7: TRANSLATION
━━━━━━━━━━━━━━━━━━━━
Input:  Fully annotated text
Tools:
  - Human translator (primary for all languages)
  - Akkadian MT: Gutherz et al. 2023 (Akkadian → English, BLEU ~37)
  - Sumerian MT: Pagé-Perron et al. 2017 (research stage)
  - Hittite MT: none
  - Elamite MT: none
Output: Translation in modern language(s)
Data:   - Parallel corpora (bilingual texts, esp. Sum-Akk)
        - Published translations (scholarly editions)
        - Cultural/historical context databases

STAGE 8: SCHOLARLY REVIEW & PUBLICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input:  Full annotated, translated text
Tools:
  - Your pipeline's review interface
  - Standard philological publication workflow
Output: Published edition, annotations fed back into corpus
Data:   - Schema records with human_review status updated
        - Corrections fed back to model retraining
```

---

## Summary: What These Examples Prove About the Schema

1. **The schema MUST be layered.** No flat data model survives contact with Hittite trilingual writing or Elamite morphological uncertainty.

2. **Confidence is multidimensional.** A Hittite Sumerogram can have high semantic confidence and zero phonetic confidence simultaneously. The schema needs per-layer confidence, not a single number.

3. **Competing interpretations are data, not errors.** The *warnu-* vs. *warra-* debate isn't a bug — it's a feature. Your schema must hold both with metadata about scholarly provenance and evidence.

4. **The same sign means different things depending on language, function, and context.** É is a house in Sumerian, *bītu* in Akkadian, *per-/parn-* in Hittite, and rarely used in Elamite. The sign is the connection point; the languages diverge from there.

5. **Automation coverage varies dramatically.** BabyLemmatizer handles Sumerian and Akkadian well; Hittite and Elamite are manual. Your pipeline must support both seamlessly, with the same schema structure regardless of annotation source.

6. **The "AlphaFold moment" is at Stage 3→5.** The gap between sign identification and lemmatization is where the most human labor is spent and where AI could help most — but only if the schema provides clean training data linking images → signs → readings → lemmata → translations.
