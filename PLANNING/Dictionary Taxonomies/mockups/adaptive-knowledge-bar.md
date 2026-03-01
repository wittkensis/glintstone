# Adaptive Knowledge Bar — Token Translation Facilitator

Replaces the general dictionary browser with a focused translation assistant. When a scholar clicks a token, it shows exactly what's known and highlights what's missing, guiding the token toward the next translation layer.

## Design Principle

**"Show what you have. Name what you don't. Suggest the next step."**

The bar adapts its entire structure based on which pipeline layers are populated for the selected token. Instead of showing empty sections for missing data, it reshapes to foreground the most useful information for the token's current state.

---

## Full Translation Pipeline

```
Sign -> Function -> Reading -> Normalization -> Lemma -> Morphology -> Sense
 L0                   L1          (bridge)        L2                    L3
```

**Normalization** sits between Reading and Lemma. For Akkadian syllabic text, it is the critical bridge: without it, a sequence of syllable signs cannot be linked to a dictionary entry. For Sumerian logographic text, normalization is near-trivial (sign = word). The Knowledge Bar treats normalization as a pseudo-stage — visible when it matters (Akkadian), hidden when it doesn't (Sumerian logographic).

### Data sources per stage

| Stage | Primary table | Lookup bridge | Coverage |
|-------|--------------|--------------|----------|
| Sign | `token_readings` -> `lexical_signs` | sign_name match | 72k matched |
| Function | `token_readings.sign_function` | direct field | 948k tokens |
| Reading | ATF raw + `token_readings.reading` | direct | universal |
| **Normalization** | **`lexical_norm_forms` -> `lexical_norms`** | **written_form lookup** | **80k forms, 179k norms** |
| Lemma | `lemmatizations` -> `lexical_lemmas` | cf/gw/pos match | 32k matched |
| Sense/Gloss | `lexical_senses` | lemma_id FK | 155k senses |

### Two normalization paths

**Path A (CDL-annotated tokens):** Token already has `lemmatizations.norm` populated. Follow `norm_id` FK directly to `lexical_norms` -> `lexical_lemmas`. Fast, exact. Works for 5,441 Akkadian tokens.

**Path B (unlemmatized tokens):** Token has only a reading (written form) and no lemmatization. Look up `written_form` in `lexical_norm_forms` to get candidate norms and lemmas. Returns ranked candidates. Note: written-form lookup is sensitive to sign-name encoding conventions (acute accent vs subscript number — see below).

### Sign-name encoding divergence

ATF and ORACC glossaries use different conventions for the same cuneiform signs:

| Sign | ATF/CDL convention | Glossary convention |
|------|-------------------|-------------------|
| U₂ | `ú` (u-acute) | `u₂` (u + subscript) |
| ŠU₂ | `šú` (s-caron + u-acute) | `šu₂` (s-caron + subscript) |

Both are standard. Path B written-form lookup may miss tokens that use a different convention than the glossary. Path A (norm-text) is not affected because norms are language-level forms, not sign-level spellings.

---

## Pipeline States

A token can be at one of 6 states based on populated layers:

| State | Has | Missing | Frequency | Example |
|---|---|---|---|---|
| **S0: Raw** | ATF reading only | Sign, Norm, Lemma, Gloss | Rare (unprocessed) | Damaged/unclear tokens |
| **S1: Identified** | Reading + Sign match | Norm, Lemma, Gloss | Common for Hittite | `u₄` -> sign U₄ found, no lemma |
| **S1.5: Norm-matched** | Reading + Norm candidates (no lemmatization) | Lemma confirmation, Gloss | Akkadian unlemmatized | `a-ba-ku` -> norm `abaku` -> 2 candidate lemmas |
| **S2: Lemmatized** | Reading + Lemma (1 candidate) | Gloss may be sparse | Most Sumerian/Akkadian | `lu₂` -> lu [person] N |
| **S3: Ambiguous** | Reading + Multiple lemma candidates | Disambiguation needed | Hittite Sumerograms | `ur-sag` -> 3 candidates |
| **S4: Translated** | Reading + Lemma + Glosses + Norms | Nothing critical | Well-attested words | `lugal` -> sharru [king] -> "king, ruler" |

---

## S0: Raw Token (reading only, no sign match, no lemma)

The token exists in ATF but nothing links to it. The bar becomes a diagnostic tool.

```
+------------------------------------------+
|                                          |
|  ib₂-ta-sa                              |
|  ──────────                              |
|  No dictionary data                      |
|                                          |
|  READING                                 |
|  ib₂-ta-sa                              |
|  Line 9, KBo 50, 009                     |
|  Language: unknown                       |
|                                          |
|  ──────────────────────────              |
|                                          |
|  POSSIBLE SIGNS                          |
|  IB₂  TA  SA  (compound?)               |
|  No confirmed sign match                 |
|                                          |
|  ──────────────────────────              |
|                                          |
|  NORMALIZATION SEARCH                    |
|  No matches in norm-forms index          |
|                                          |
|  ──────────────────────────              |
|                                          |
|  ON THIS TABLET                          |
|  Appears 1x                             |
|  14,669 Hittite tablets in corpus        |
|  Period: Middle Hittite                  |
|  Prov: Hattusa                          |
|                                          |
|  ──────────────────────────              |
|                                          |
|  NEXT STEP                               |
|  Pipeline gap: Sign, Norm, Lemma, Gloss  |
|                                          |
|  Try:                                    |
|  > Search corpus for similar readings    |
|  > View other unidentified tokens on     |
|    this tablet (12 of 502 unresolved)    |
|  > Open ePSD2 search for "ib₂-ta-sa"    |
|                                          |
|  Future: Assign sign values and lemma    |
|                                          |
|  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄            |
|  Sign [ ] Read [*] Norm [ ] Lemma [ ]   |
|                                          |
+------------------------------------------+
```

**Key behavior:** The NORMALIZATION SEARCH section explicitly reports "no matches" — this is informative, not just empty. It tells the scholar that the written form doesn't appear in any ORACC glossary, narrowing the problem to either a rare/damaged token or an encoding gap.

---

## S1: Identified Token (sign matched, no lemma)

The sign is recognized but no lemmatization exists. The bar shows the sign's readings and, for Akkadian tokens, attempts a normalization lookup.

```
+------------------------------------------+
|                                          |
|  u₄                                     |
|  ──────────                              |
|  Sign identified · No lemmatization      |
|                                          |
|  SIGN                                    |
|  U₄  (glyph)                            |
|  Function: logographic (this token)      |
|                                          |
|  All readings of U₄:                     |
|  ud    "day, sun"        4,201 att.      |
|  u₄    "day, storm"      3,887 att.      |
|  tam    (syllabic)          42 att.      |
|  par₃   (syllabic)         18 att.      |
|                                          |
|  ──────────────────────────              |
|                                          |
|  LIKELY LEMMAS (from this reading)       |
|  When u₄ is lemmatized, it maps to:     |
|                                          |
|  ud [day] N/sux          62% (2,411)     |
|  ==============================          |
|  ud [sun] N/sux          23% (894)       |
|  ===========                             |
|  niŋ [thing] N/sux       8% (311)        |
|  ====                                    |
|  ud [storm] N/sux        7% (271)        |
|  ===                                     |
|                                          |
|  ──────────────────────────              |
|                                          |
|  CONTEXT CLUES                           |
|  Line: u₄ ur-sag mar-tu# ib₂-ta-sa     |
|  Period: Middle Hittite                  |
|  Genre: Ritual                           |
|  In Hittite rituals, u₄ usually = ud    |
|  [day] (78% of 342 instances)            |
|                                          |
|  ──────────────────────────              |
|                                          |
|  NEXT STEP                               |
|  Pipeline gap: Lemma                     |
|                                          |
|  Best candidate: ud [day] N              |
|  62% match · 2,411 att. in this reading  |
|  "day, time" -- 5 glosses in dictionary  |
|                                          |
|  > View full ud [day] entry              |
|  > Compare all 4 candidates side by side |
|                                          |
|  Future: Confirm lemma assignment        |
|                                          |
|  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄            |
|  Sign [*] Read [*] Norm [~] Lemma [ ]   |
|                                          |
+------------------------------------------+
```

**Key behavior:** For this Sumerian logographic token, normalization is near-trivial (reading ~= norm). The `[~]` in the pipeline indicator means "not applicable / implicit." The sign's readings ranked by corpus frequency become the primary disambiguation tool. No NORMALIZATION SEARCH section shown — it would add noise for a logographic token.

---

## S1.5: Norm-Matched Token (Akkadian, no lemmatization, but written form found in norms index)

**New state.** The token has no CDL lemmatization, but its written form matches entries in `lexical_norm_forms`. This is the normalization bridge doing its job — providing a path from syllabic spelling to candidate lemmas.

```
+------------------------------------------+
|                                          |
|  a-ba-ku                                 |
|  ──────────                              |
|  Not lemmatized · Norm candidates found  |
|                                          |
|  NORMALIZATION                           |
|  Written form: a-ba-ku                   |
|  Language zone: Akkadian                 |
|                                          |
|  Resolves to:                            |
|                                          |
|  (*) abāku [lead away] V                |
|      norm: abāku                         |
|      1 att. (dcclt) · 15 att. (lemma)    |
|      glosses: "leading away"             |
|                                          |
|  ( ) abāku [overturn] V                  |
|      norm: abāku                         |
|      3 att. (dcclt) · 8 att. (lemma)     |
|      glosses: "overturning"              |
|                                          |
|  ──────────────────────────              |
|                                          |
|  HOW THIS WAS FOUND                      |
|  a-ba-ku is attested 4x across           |
|  2 ORACC projects as a spelling of       |
|  the norm "abāku" (normalized form).     |
|  The norm links to 2 lemmas with         |
|  different meanings.                     |
|                                          |
|  ──────────────────────────              |
|                                          |
|  ON THIS TABLET                          |
|  Appears 1x                             |
|  Period: Standard Babylonian             |
|  Genre: Lexical                          |
|                                          |
|  ──────────────────────────              |
|                                          |
|  NEXT STEP                               |
|  Pipeline gap: Lemma confirmation        |
|                                          |
|  2 candidates found via normalization.   |
|  Context suggests: abāku [lead away] V   |
|  (lexical text, only 1 att. difference)  |
|                                          |
|  > View abāku [lead away] full entry     |
|  > View abāku [overturn] full entry      |
|  > Compare candidates side by side       |
|                                          |
|  Future: Confirm which lemma applies     |
|                                          |
|  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄            |
|  Sign [ ] Read [*] Norm [*] Lemma [ ]   |
|                                          |
+------------------------------------------+
```

**Key behavior:** Normalization is the hero section. The bar explicitly shows the bridge chain: written form -> norm -> lemma candidates. "HOW THIS WAS FOUND" explains the provenance — the scholar sees this is a statistical match from glossary data, not a confirmed CDL annotation. The pipeline indicator shows Norm [*] but Lemma [ ] — the norm was found, but no authoritative lemmatization exists.

### Polysemy variant (same written form, multiple lemma targets)

```
+------------------------------------------+
|                                          |
|  a-na                                    |
|  ──────────                              |
|  Not lemmatized · 3 candidates via norm  |
|                                          |
|  NORMALIZATION                           |
|  Written form: a-na                      |
|                                          |
|  (*) ana [to] PRP/akk                    |
|      8,514 att. across 5 sources         |
|      ====================================|
|      "to, for, towards"                  |
|                                          |
|  ( ) ana [what?] QP/sux                  |
|      25 att. across 2 sources            |
|      =                                   |
|      "what?"                             |
|                                          |
|  ( ) ana [the sign AN] N/akk             |
|      15 att. (dcclt)                     |
|      =                                   |
|      "the sign AN"                       |
|                                          |
|  ──────────────────────────              |
|                                          |
|  NOTE                                    |
|  Candidates span 2 languages             |
|  (Akkadian, Sumerian). Token's line      |
|  language can narrow this.               |
|                                          |
|  ──────────────────────────              |
|                                          |
|  NEXT STEP                               |
|  Pipeline gap: Lemma confirmation        |
|                                          |
|  Strongest candidate: ana [to] PRP       |
|  8,514 att. (340x more than next)        |
|  If this line is Akkadian, confidence    |
|  is very high.                           |
|                                          |
|  > View ana [to] full entry              |
|  > Filter by this tablet's language      |
|                                          |
|  Future: Confirm lemma assignment        |
|                                          |
|  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄            |
|  Sign [ ] Read [*] Norm [*] Lemma [ ]   |
|                                          |
+------------------------------------------+
```

**Key behavior:** Cross-language polysemy is flagged. The 3-order-of-magnitude frequency gap (8,514 vs 25 vs 15) makes the ranking unambiguous. The NOTE section alerts the scholar that language context can disambiguate — if this token is on an Akkadian line, the Sumerian candidate drops out.

---

## S2: Lemmatized Token (single candidate, glosses available)

The most common state. One clear lemma match. For Akkadian tokens with a norm, the normalization chain is visible but compact.

```
+------------------------------------------+
|                                          |
|  lu₂                                    |
|  ──────────                              |
|  lu [person] N · Sumerian                |
|  12,304 attestations · ePSD2             |
|                                          |
|  THIS INSTANCE                           |
|  Sense: "person, man"                    |
|  Sign: LU₂ (logographic)                |
|  Norm: lu₂                              |
|  Line 40: lu₂ šà ḫul gig-ga ak          |
|           ^^^                            |
|                                          |
|  ──────────────────────────              |
|                                          |
|  ALL GLOSSES                             |
|  1. person, man           <-- this one   |
|  2. human being                          |
|  3. someone, anyone                      |
|  4. slave, servant                       |
|  5. gentleman                            |
|                                          |
|  ──────────────────────────              |
|                                          |
|  QUICK STATS                             |
|  Rank #14 among Sumerian nouns           |
|  Appears on 4,891 tablets                |
|  Ur III ████████████░░ 68%               |
|  OB     ████░░░░░░░░░░ 19%               |
|  Other  ██░░░░░░░░░░░░ 13%               |
|                                          |
|  ──────────────────────────              |
|                                          |
|  CROSS-LANGUAGE                          |
|  Akkadian: awilum [man] N                |
|            amelu [person] N              |
|                                          |
|  ──────────────────────────              |
|                                          |
|  NEXT STEP                               |
|  Pipeline complete: Sign through Gloss   |
|                                          |
|  Refine:                                 |
|  > Which sense fits this context?        |
|    5 glosses -- "person" is sense 1      |
|  > View other lu₂ instances on this      |
|    tablet (appears 23x, all sense 1)     |
|  > View Akkadian equivalent: awilum      |
|                                          |
|  Open full entry >                       |
|                                          |
|  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄            |
|  Sign [*] Read [*] Norm [~] Lemma [*]   |
|  Gloss [*]                               |
|                                          |
+------------------------------------------+
```

**Key behavior:** For Sumerian logographic tokens, Norm is `[~]` (implicit). The norm line under THIS INSTANCE shows `lu₂` — identical to the reading, confirming this is logographic and normalization was trivial.

### Akkadian S2 variant (normalization chain visible)

```
+------------------------------------------+
|                                          |
|  ra-man-šú-nu                            |
|  ──────────                              |
|  ramānu [self] N · Std Babylonian        |
|  236 attestations                        |
|                                          |
|  THIS INSTANCE                           |
|  Sense: "self, own person"               |
|  Norm: ramānšunu (3mp possessive)        |
|  Line 13': ra-man-šú-nu ú-šah-ha-zu ... |
|             ^^^^^^^^^^^^                 |
|                                          |
|  ──────────────────────────              |
|                                          |
|  NORMALIZATION                           |
|  ra-man-šú-nu -> ramānšunu -> ramānu     |
|  (syllabic)     (normalized)  (lemma)    |
|                                          |
|  72 forms of ramānu attested:            |
|  ramānišu      48 att.                   |
|  ramānuš       22 att.                   |
|  ramānišunu    20 att.                   |
|  ramānšu       13 att.                   |
|  ramānšunu      1 att.  <-- this form    |
|  ...                                     |
|                                          |
|  ──────────────────────────              |
|                                          |
|  ALL GLOSSES                             |
|  1. self, own person      <-- this one   |
|  2. voluntary, of free will              |
|                                          |
|  ──────────────────────────              |
|                                          |
|  CROSS-LANGUAGE                          |
|  Sumerian: niŋ₂ [self] N                |
|                                          |
|  ──────────────────────────              |
|                                          |
|  NEXT STEP                               |
|  Pipeline complete: Reading through Gloss|
|                                          |
|  Refine:                                 |
|  > Rare spelling: ramānšunu has 1 att.   |
|    More common: ramānišu (48 att.)       |
|  > Which sense? "self, own person" vs    |
|    "voluntary, of free will"             |
|  > View other ramānu forms on this tablet|
|                                          |
|  Open full entry >                       |
|                                          |
|  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄            |
|  Sign [ ] Read [*] Norm [*] Lemma [*]   |
|  Gloss [*]                               |
|                                          |
+------------------------------------------+
```

**Key behavior:** The NORMALIZATION section is the distinguishing feature for Akkadian S2. It shows the full chain: written form -> normalized form -> lemma. Below that, the morphological breadth of the lemma — 72 distinct norms for ramānu, each a different inflected form. The current form's attestation count (1) is flagged to show this is a rare spelling. This section only appears when normalization data exists (Akkadian); it's hidden for Sumerian logographic tokens.

---

## S3: Ambiguous Token (multiple competing lemmatizations)

Multiple lemma candidates. For Hittite Sumerograms: no normalization data. For Akkadian: normalization can help disambiguate.

### Hittite variant (no normalization)

```
+------------------------------------------+
|                                          |
|  ur-sag                                  |
|  ──────────                              |
|  !! 3 candidates                         |
|  Sign: UR.SAG (logographic)              |
|                                          |
|  DISAMBIGUATION                          |
|                                          |
|  (*) ursaŋ [hero] N/sux                  |
|      "warrior, hero"                     |
|      4,102 att. · 72% for this reading   |
|      ================================    |
|      Ur III █████░ · OB ███░ · Other █░  |
|                                          |
|  ( ) tuku [acquire] V/t/sux              |
|      "to acquire, to get"               |
|      1,044 att. · 18% for this reading   |
|      =========                           |
|      Ur III ██░ · OB █████░ · Other ██░  |
|                                          |
|  ( ) usar [neighbor] N/sux               |
|      "neighbor, rival"                   |
|      579 att. · 10% for this reading     |
|      =====                               |
|                                          |
|  ──────────────────────────              |
|                                          |
|  CONTEXT WEIGHING                        |
|  Period: Middle Hittite                  |
|  Genre: Ritual                           |
|  In Hittite rituals:                     |
|    ursaŋ [hero]     84%  <-- strongest   |
|    tuku [acquire]   12%                  |
|    usar [neighbor]   4%                  |
|                                          |
|  Note: All candidates are Sumerian       |
|  logograms. No Hittite reading           |
|  available for this token.               |
|                                          |
|  ──────────────────────────              |
|                                          |
|  LINE CONTEXT                            |
|  u₄  ur-sag  mar-tu#  ib₂-ta-sa        |
|       ^^^^^^                             |
|  "day hero/warrior westerner ..."        |
|  (partial gloss of resolved tokens)      |
|                                          |
|  ──────────────────────────              |
|                                          |
|  NEXT STEP                               |
|  Pipeline gap: Lemma disambiguation      |
|                                          |
|  Strongest candidate: ursaŋ [hero] N     |
|  84% in Hittite rituals · 4,102 att.     |
|                                          |
|  > View ursaŋ [hero] full entry          |
|  > View all 3 candidates' glosses        |
|  > See other ur-sag instances on this    |
|    tablet (2 more, both lemmatized)      |
|                                          |
|  Future: Confirm lemma for this token    |
|                                          |
|  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄            |
|  Sign [*] Read [*] Norm [~] Lemma [?]   |
|                                          |
+------------------------------------------+
```

**Key behavior:** Norm is `[~]` (logographic, normalization implicit). Lemma is `[?]` (ambiguous). No NORMALIZATION section shown. Disambiguation relies entirely on corpus frequency and context weighing.

### Akkadian variant (normalization-assisted disambiguation)

```
+------------------------------------------+
|                                          |
|  e-hu-uz                                 |
|  ──────────                              |
|  !! 2 candidates via normalization       |
|  Language: Akkadian                      |
|                                          |
|  NORMALIZATION                           |
|  Written form: e-hu-uz                   |
|  Resolves to 2 norms:                    |
|                                          |
|  (*) ēhuz -> ahāzu [take] V             |
|      "to take, seize; learn"             |
|      7 att. for this norm (rinap)        |
|      ahāzu total: 236 att.              |
|      ================================    |
|                                          |
|  ( ) ehuz -> ehēzu [bright] V            |
|      "to be(come) bright, pure"          |
|      2 att. for this norm                |
|      ehēzu total: 14 att.               |
|      ====                                |
|                                          |
|  ──────────────────────────              |
|                                          |
|  CONTEXT WEIGHING                        |
|  Period: Neo-Assyrian                    |
|  Genre: Royal inscription               |
|  ahāzu appears 15x on this tablet       |
|  ehēzu appears 0x on this tablet        |
|                                          |
|  ──────────────────────────              |
|                                          |
|  LINE CONTEXT                            |
|  ... e-hu-uz GIŠ.TUKUL-šú ...           |
|      ^^^^^^^                             |
|  "he took his weapon"                    |
|  (partial gloss of resolved tokens)      |
|                                          |
|  ──────────────────────────              |
|                                          |
|  NEXT STEP                               |
|  Pipeline gap: Lemma disambiguation      |
|                                          |
|  Strongest candidate: ahāzu [take] V     |
|  7 att. for this norm · appears 15x on   |
|  this tablet · 0 uses of ehēzu here     |
|                                          |
|  > View ahāzu [take] full entry          |
|  > View ehēzu [bright] full entry        |
|  > Compare candidates side by side       |
|                                          |
|  Future: Confirm lemma for this token    |
|                                          |
|  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄            |
|  Sign [ ] Read [*] Norm [*] Lemma [?]   |
|                                          |
+------------------------------------------+
```

**Key behavior:** For Akkadian S3, the normalization bridge provides the disambiguation data. Each candidate shows norm -> lemma -> gloss. Context weighing uses tablet-level data (how many times each candidate appears elsewhere on this tablet) to suggest the strongest match. The written form `e-hu-uz` resolves to two different norms (`ēhuz` vs `ehuz`), each pointing to a different lemma.

---

## S4: Fully Translated Token (lemma + rich glosses + norms)

Everything populated. The bar becomes a compact reference card.

### Sumerian variant (logographic, normalization implicit)

```
+------------------------------------------+
|                                          |
|  lugal                                   |
|  ──────────                              |
|  lugal [king] N · Sumerian               |
|  "king, ruler, master, lord"             |
|  34,891 att. · Rank #3 noun              |
|                                          |
|  THIS INSTANCE                           |
|  Sense: "king" (sense 1)                |
|  Norm: lugal                             |
|  Sign: LUGAL (logographic)               |
|  (glyph)                                |
|                                          |
|  ──────────────────────────              |
|                                          |
|  GLOSSES                                 |
|  1. king                  <-- this one   |
|  2. ruler, sovereign                     |
|  3. master, owner                        |
|  4. lord (in personal names)             |
|  5. "big man" (lit.)                     |
|                                          |
|  ──────────────────────────              |
|                                          |
|  SPELLINGS (this tablet)                 |
|  lugal          47x                      |
|  lugal-e         8x                      |
|  lugal-la        3x                      |
|                                          |
|  ──────────────────────────              |
|                                          |
|  CROSS-LANGUAGE                          |
|  Akkadian: šarru [king] N  (28,441 att.) |
|  Also: belum [lord], malku [ruler]       |
|                                          |
|  ──────────────────────────              |
|                                          |
|  ON THIS TABLET                          |
|  Appears 58x (47 as lugal, 8+3 affixed) |
|  Always lemmatized as lugal [king]       |
|  Consistent across all 58 occurrences    |
|                                          |
|  ──────────────────────────              |
|                                          |
|  NEXT STEP                               |
|  Pipeline complete. Fully resolved.      |
|                                          |
|  Explore:                                |
|  > View full lugal [king] entry          |
|  > See Akkadian equivalent: šarru [king] |
|  > Browse all 58 occurrences on tablet   |
|  > View lugal across this corpus         |
|    (34,891 att. in 4,891 tablets)        |
|                                          |
|  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄            |
|  Sign [*] Read [*] Norm [~] Lemma [*]   |
|  Gloss [*]                               |
|                                          |
+------------------------------------------+
```

### Akkadian variant (normalization chain visible)

```
+------------------------------------------+
|                                          |
|  LUGAL                                   |
|  ──────────                              |
|  šarru [king] N · Akkadian               |
|  "king, ruler, sovereign"                |
|  28,441 att. · Rank #1 noun              |
|                                          |
|  THIS INSTANCE                           |
|  Sense: "king" (sense 1)                |
|  Norm: šar (construct state)             |
|  Sign: LUGAL (logographic Sumerogram)    |
|  (glyph)                                |
|                                          |
|  ──────────────────────────              |
|                                          |
|  NORMALIZATION                           |
|  LUGAL -> šar -> šarru                   |
|  (Sumerogram) (normalized) (lemma)       |
|                                          |
|  Top inflected forms:                    |
|  šar        2,927 att.                   |
|  šarru        553 att.  <-- nominative   |
|  šarrāni      549 att.  <-- plural       |
|  šarri        125 att.  <-- genitive     |
|  šarrū         95 att.                   |
|                                          |
|  Written as LUGAL in 5 ORACC projects    |
|                                          |
|  ──────────────────────────              |
|                                          |
|  GLOSSES                                 |
|  1. king                  <-- this one   |
|  2. ruler, sovereign                     |
|  3. master                               |
|                                          |
|  ──────────────────────────              |
|                                          |
|  CROSS-LANGUAGE                          |
|  Sumerian: lugal [king] N (34,891 att.)  |
|                                          |
|  ──────────────────────────              |
|                                          |
|  NEXT STEP                               |
|  Pipeline complete. Fully resolved.      |
|                                          |
|  Explore:                                |
|  > View full šarru [king] entry          |
|  > See Sumerian equivalent: lugal [king] |
|  > Browse all šarru norms (5 forms)      |
|  > View inflection: šar is construct     |
|    state -- see šarru (nom), šarri (gen) |
|                                          |
|  Open full entry >                       |
|                                          |
|  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄            |
|  Sign [*] Read [*] Norm [*] Lemma [*]   |
|  Gloss [*]                               |
|                                          |
+------------------------------------------+
```

**Key behavior:** LUGAL is a Sumerogram in Akkadian text — the sign itself is Sumerian, but it's read as the Akkadian word `šarru`. The NORMALIZATION section shows this cross-script chain: `LUGAL` (Sumerogram written form) -> `šar` (Akkadian construct-state norm) -> `šarru` (citation form). The inflected forms list gives morphological context. This section only appears in S4 when normalization data exists.

---

## Adaptive Structure Summary

| Section | S0 | S1 | S1.5 | S2 (sux) | S2 (akk) | S3 (hit) | S3 (akk) | S4 (sux) | S4 (akk) |
|---|---|---|---|---|---|---|---|---|---|
| **Header** | Reading | Reading + sign | Reading + "norm candidates" | cf [gw] POS | cf [gw] POS | "!! N candidates" | "!! N via norm" | cf + gloss + rank | cf + gloss + rank |
| **Sign** | Possible signs | Full sign info | -- | -- | -- | Sign name | -- | Compact | Compact |
| **Norm** | "No matches" | -- | **HERO: candidates** | -- | Chain + forms | -- | **HERO: candidates** | -- | Chain + forms |
| **Lemma/Gloss** | -- | Likely lemmas (%) | Gloss preview | Glosses | Glosses | Radio list | Radio list | Glosses | Glosses |
| **Context** | On this tablet | Context clues | How found | Quick stats | Quick stats | Context weighing | Context weighing | On this tablet | On this tablet |
| **Next Step** | Search/ePSD2 | Best candidate | Select candidate | Refine sense | Refine sense/norm | Pick candidate | Pick via norm | Explore/corpus | Explore/inflect |
| **Future tag** | Assign signs+lemma | Confirm lemma | Confirm lemma | -- | -- | Confirm lemma | Confirm lemma | -- | -- |
| **Pipeline** | `[ ] [*] [ ] [ ]` | `[*] [*] [~] [ ]` | `[ ] [*] [*] [ ]` | `[*] [*] [~] [*] [*]` | `[ ] [*] [*] [*] [*]` | `[*] [*] [~] [?]` | `[ ] [*] [*] [?]` | `[*] [*] [~] [*] [*]` | `[*] [*] [*] [*] [*]` |

Pipeline indicators: `[*]` populated, `[ ]` missing, `[~]` implicit/trivial, `[?]` ambiguous

---

## Next Step Philosophy

Every state has a NEXT STEP section at the bottom. The pattern:

1. **Name the gap** — "Pipeline gap: Lemma" or "Pipeline complete"
2. **Suggest the strongest candidate** — with evidence (attestation count, context %)
3. **Offer navigation** — links to full entries, side-by-side comparison, corpus views
4. **"Future:" tag** — for actions that will be available when annotation is enabled (e.g., "Confirm lemma assignment", "Assign sign values"). This prepares the UI for data entry without enabling it now.

### Transition paths

- **S0 -> S1:** Corpus search, ePSD2 lookup. Future: assign sign values.
- **S0 -> S1.5:** Check alternate encodings in norm-forms index.
- **S1 -> S2:** Best candidate by frequency + context. Future: confirm lemma.
- **S1.5 -> S2:** Select from norm-bridge candidates. Future: confirm lemma.
- **S2 -> S4:** Refine sense selection. View normalization chain (Akkadian).
- **S3 -> S2:** Pick candidate using context + frequency. Future: confirm lemma.
- **S4:** Explore: full entry, cross-language, corpus statistics, inflection.

## Coverage Indicator

All states show a pipeline status at the bottom:

```
  Sign [*]  Read [*]  Norm [*]  Lemma [*]  Gloss [*]
```

States: `[*]` populated, `[ ]` missing, `[~]` implicit, `[?]` ambiguous

For Sumerian logographic tokens, Norm always shows `[~]`. For Akkadian syllabic tokens, Norm shows `[*]` when normalization data exists or `[ ]` when it doesn't. This gives scholars an instant read on pipeline completeness without taking meaningful space.
