# Assyriological Typography Conventions

Reference for typographic rules used in cuneiform transliteration, normalization, and translation. Governs how text is displayed in the Glintstone knowledge bar and dictionary views.

---

## Three Layers of Representation

| Layer | Represents | Formatting | Example |
|---|---|---|---|
| **Transliteration** | Signs on the tablet | Case/punctuation rules below | *ṭu-up-šar-ru* or DUB.SAR |
| **Normalization** | Spoken word (phonological) | Italic, no hyphens or dots | *ṭupšarru* |
| **Translation** | Meaning in English | Roman, often in quotes | "scribe" |

Transliteration preserves sign information. Normalization preserves phonological form. Translation preserves meaning. Each layer loses information from the previous.

---

## Case Rules

| Convention | Meaning | Example |
|---|---|---|
| lowercase italic | Syllabic reading (Akkadian/Hittite) | *šar-ru-um* |
| lowercase roman | Syllabic reading (Sumerian) | lugal, dub-sar |
| UPPERCASE | Logogram / sign name | LUGAL, DUB.SAR |
| SMALL CAPS | Sumerogram in Akkadian text (print) | ʟᴜɢᴀʟ |
| italic SMALL CAPS | Akkadogram in Hittite text | distinguishes from Sumerograms |

**Core principle:** Capitals = sign identity. Lowercase = phonetic reading chosen by the editor.

---

## Punctuation Between Signs

| Symbol | Use | Example |
|---|---|---|
| `-` (hyphen) | Between syllables in one word | *ṭu-up-šar-ru* |
| `.` (period) | Between logograms in a compound | DUB.SAR, GIR₂.TAB |
| (space) | Between words | lugal kur-ra |

---

## Homophone Disambiguation

Different cuneiform signs can share the same phonetic value. Disambiguation uses subscript numbers or (in legacy systems) accents.

| Homophone | Modern (preferred) | Legacy | Notes |
|---|---|---|---|
| First | `u` | `u` | No marker needed |
| Second | `u₂` | `ú` (acute) | |
| Third | `u₃` | `ù` (grave) | |
| Fourth+ | `u₄`, `u₅`... | n/a | Subscript only |

ORACC recommends subscript notation. Glintstone data contains both conventions (see sign-name encoding divergence in normalization bridge docs).

---

## Determinatives (Semantic Classifiers)

Unpronounced signs that classify a word's category. Not read aloud.

| Determinative | ATF (digital) | Print | Classifies |
|---|---|---|---|
| deity | `{d}IŠKUR` | ᵈIŠKUR | divine name |
| place | `sip-par{ki}` | sipparᵏⁱ | geographic name |
| male person | `{m}Da-ri-uš` | ᵐDariuš | male personal name |
| female person | `{f}Pu-a-bi` | ᶠPuabi | female personal name |
| wood | `{ŋeš}TUKUL` | ᵍᵉˢTUKUL | wooden object |
| plural | `LUGAL{meš}` | LUGALᵐᵉˢ | plural marker |

ATF uses `{curly braces}`. Print uses superscript. Both positioned adjacent to the word with no space.

---

## Damage and Editorial Markers

| Notation | Meaning | Example |
|---|---|---|
| `x` | Completely illegible sign | `x x x` = three unreadable signs |
| `[...]` | Missing/broken, restored by editor | `[a-na]` = editorial restoration |
| `#` | Damaged but partially legible | `a#` |
| `?` | Uncertain reading | `a?` |
| `!` | Corrected by editor | `ki!(DI)` = reads *ki*, tablet shows DI |
| `*` | Collated (personally verified on tablet) | `a*` |
| `⸢ ⸣` | Half-brackets (print only) | Partially preserved signs |
| `...` | Lacuna of unknown length | Indeterminate missing signs |

ATF does not use half-brackets; `#` serves that role in digital encoding.

---

## Compound Grapheme Notation

| Notation | Meaning | Example |
|---|---|---|
| `\|KA×NUN\|` | Compound sign (sign within sign) | GDL encoding |

Pipe/vertical bar delimiters enclose compound graphemes in ATF/GDL (Grapheme Description Language). Used for signs that are physically composed of multiple sign elements.

---

## The cf[gw]POS Lemmatization Format

ORACC's standard signature format: **citation_form [guide_word] POS**

| Component | Role | Example |
|---|---|---|
| CF (citation form) | Dictionary headword | lugal, šarru, alāku |
| GW (guide word) | Disambiguating semantic label | [king], [go], [lead away] |
| POS (part of speech) | Grammatical category | N, V, AJ |

**Full examples:**
- `lugal [king] N` — Sumerian noun
- `šarru [king] N` — Akkadian noun
- `alāku [go] V` — Akkadian verb
- `abāku [lead away] V` vs `abāku [overturn] V` — same CF, different GW

The guide word is a quick disambiguator, not a full definition. Two lemmas sharing a citation form get different guide words.

---

## Font Conventions

| Context | Font | Notes |
|---|---|---|
| Transliteration body text | Serif with full Unicode | Must support š, ṣ, ṭ, ā, ē, ī, ū |
| Cuneiform glyphs | Noto Sans Cuneiform, Santakku, Assurbanipal | Specialized glyph fonts |
| ATF source / sign lists | Monospace | Columnar alignment matters |
| Web/UI display | Sans-serif acceptable | Must have Unicode coverage |

**Italic rules:**
- Mandatory for Akkadian/Hittite syllabic transliterations
- Sumerian uses roman (upright)
- Logograms are always roman uppercase
- Normalized forms are always italic

**Unicode is required.** Legacy ASCII conventions (`sz` for š, `s,` for ṣ) should not appear in display. ATF files should declare `#atf: use unicode`.

---

## Glintstone UI Implications

How these conventions map to stored data and display:

| Convention | Data source | Display rule |
|---|---|---|
| Readings (lowercase) | `token_readings.reading`, `lemmatizations` | Italic for Akkadian, roman for Sumerian |
| Sign names (UPPERCASE) | `lexical_signs` | Always uppercase roman |
| Norms (italic, no hyphens) | `lexical_norms.norm` | Always italic |
| cf[gw]POS headers | `lexical_lemmas` fields | Standard format in knowledge bar headers |
| Determinatives | ATF `{d}`, `{ki}`, etc. | Render as superscript in UI |
| Damage markers | `#`, `?`, `!` in ATF data | Visual treatment (color, half-brackets, or subtle styling) |

### Key display decisions for the knowledge bar

1. Use **italic** for Akkadian normalized forms and syllabic readings
2. Use **roman** for Sumerian readings
3. Use **uppercase** for sign names and logograms
4. Render determinatives as **superscript** (not curly braces)
5. Consider subtle styling for damaged signs (muted color, dotted underline) rather than raw `#` markers
