---
question: "How do Sumerian, Akkadian, Hittite, and Elamite compare typologically — and what does that mean for the schema and the parser?"
created: 2026-05-11
modified: 2026-05-18
context: "Synthesized from PLAN/Linguistics Schema/v2/Phase 1/Linguistics Schema Research (Claude/Gemini/Grok).md during the 2026-05-11 overhaul. The three reports answered the same comparative-typology question from different angles; this file extracts the core takeaways most directly useful for schema and parser decisions. Long-form synthesis with citations lives on the Research-Cuneiform-Linguistics-Synthesis wiki page (https://github.com/wittkensis/glintstone/wiki/Research-Cuneiform-Linguistics-Synthesis)."
status: active
audience: [claude, engineers, scholars]
owners: [eric]
related_issues: []
related_skills: [gs-expert-assyriology, gs-expert-data-model]
supersedes: null
superseded_by: null
---

# Comparative typology — four languages, one script

Cuneiform is a writing system, not a language. The script was adopted, adapted, and repurposed by speakers of radically different languages over ~3,000 years. The four languages in Glintstone's corpus represent **three language families plus two isolates**.

## Big picture

| Feature | Sumerian | Akkadian | Hittite | Elamite |
|---|---|---|---|---|
| **Family** | Isolate | Semitic (Afroasiatic) | Indo-European (Anatolian) | Isolate |
| **Morphology** | Agglutinative | Fusional (root + pattern) | Inflecting (fusional) | Agglutinative |
| **Alignment** | Ergative-absolutive | Nominative-accusative | Nominative-accusative | Nom-acc with class system |
| **Word order** | SOV strict | SOV (Sumerian-influenced) | SOV | SOV |
| **Noun class** | Personal / impersonal | Masculine / feminine | Common / neuter | Locutive / allocutive / delocutive |
| **Period spoken** | ~3500–2000 BCE (literary to ~100 CE) | ~2800 BCE – ~100 CE | ~1650–1178 BCE | ~2600–330 BCE |

All four are **SOV** — that's an areal feature (Sprachbund), not a genetic one. The fact that unrelated languages converged on the same word order is itself informative: Akkadian probably adopted SOV from Sumerian during their millennium of contact.

## Schema implications by language

### Sumerian — slot-based verbal chain

The verb is built from a stem plus up to ~10 prefix slots and several suffix slots. The schema must represent a **slot-based morphological template**, not just `root + inflection`. Each slot encodes a specific category (modal, conjugation, ventive, dimensional, person, ergative marker, pronominal suffix).

Example: `mu-n-na-ab-sum` = "he gave it to him" parses as `mu-` (ventive) `n-` (3sg.IO dat) `na-` (3sg.human.IO all) `b-` (3sg.neut.DO) `sum` (give stem).

**Schema implication**: don't try to flatten the chain into a single `morph_string` column. Store the slot-fill as structured data (or carry the ORACC string verbatim and parse on render). The `morphology` table should support a flexible scheme.

**Scholarly debate**: Jagersma, Zolyomi, and Edzard disagree on which prefix occupies which slot. ORACC follows Jagersma; the schema's `annotation_run_id` model is exactly the mechanism for storing competing parses.

### Akkadian — root + pattern

Triconsonantal root with internal vowel patterns + stem augments encodes the grammar. The root `b-n-y` "build" appears as `ibnī` (G preterite "he built"), `ibtanī` (Gtn iterative), `ubnī` (Š causative "he had built"), `bītum` (noun "house" — same root).

**Schema implication**: `lexical_lemmas` should expose root + stem augment + pattern slot. Currently `glossary_entries.citation_form` is just the lemma string; richer morphology would unlock root-based search ("find all derivatives of b-n-y").

**Dialect is a first-class dimension**: Old Akkadian, Old / Middle / Neo / Late Babylonian, Old / Middle / Neo Assyrian have distinct grammars. Neo-Assyrian lost case endings; Late Babylonian is partly analytical. Track dialect on every lemma and every annotation, not just on the tablet.

### Hittite — heterography is the rule

A Hittite text routinely contains three languages at the graphemic layer:
- Hittite phonetic spellings
- Sumerograms (`LUGAL` for `ḫassuš` "king") — UPPERCASE in transliteration
- Akkadograms (`ANA` for "to" / "for") — *ITALICS-UPPERCASE*
- Sumerian determinatives (`{d}`, `{m}`, `{ki}`)
- Phonetic complements on logograms to mark the underlying Hittite ending

Example: `LUGAL-uš É.GAL=an iyat` — `LUGAL` (Sumerogram) `-uš` (Hittite nominative ending) ` É.GAL=an` (Sumerogram + clitic Hittite accusative) `iyat` (Hittite verb).

**Schema implication**: the graphemic layer is genuinely independent of the linguistic layer. A token's `surface_form` (what's written) and its `lemma_id` (what's meant) MUST be separate concerns. The schema already supports this via `tokens` + `lemmatizations`, but Hittite is the language where the gap is widest.

**Wackernagel's Position**: enclitic chains (pronouns, reflexive markers, local particles) cluster after the first stressed word of the clause. The intro particle `nu` is the typical anchor. If we ever parse Hittite syntax in earnest, this constraint needs to be expressible.

### Elamite — class system everywhere

The locutive / allocutive / delocutive distinction (1st / 2nd / 3rd person animate) suffuses the morphology. Plural and inanimate markers attach to nouns AND to their modifiers (Suffixaufnahme / suffix doubling).

Example: `sunki-k GN-k` = "I, the king of GN" — the `-k` locutive marker appears on BOTH the noun "king" AND on the city name, because the speaker (1st person) is the subject of the apposition.

**Schema implication**: Elamite morphological annotations should carry the class marker as a separate feature, not bake it into the lemma. The corpus is small and sparse — confidence scores matter more here than for Akkadian.

**Periods diverge significantly**: Old Elamite (sparse), Middle Elamite (royal inscriptions, best-attested), Neo-Elamite (transitional), Achaemenid Elamite (Persepolis Fortification Archive — heavily Old-Persian-influenced, possibly a bureaucratic pidgin rather than natural speech).

## Polyvalency — the script-wide reality

A single sign has multiple readings, multiple meanings, multiple functions. The classic teaching example is the AN sign (𒀭):

| Sign | Sumerian | Akkadian | Hittite | Elamite |
|---|---|---|---|---|
| **AN** (𒀭) | `an` "sky", `dingir` "god" | `šamû` "heaven", `ilu` "god", syllable `an` | divine determinative | `an` syllable |
| **KUR** (𒆳) | `kur` "mountain, foreign land" | `šadû` "mountain", `mātu` "land", syllables `kur` / `mad` / `šad` | "land" (with phonetic complement) | — |
| **UD** (𒌓) | `ud` "day, sun" | `ūmu` "day", syllables `ud` / `tam` / `tú` / `par` / `laḫ` | "day" | `ut` |

This is the schema's central data challenge. **Polyvalency is the reason `tokens` and `token_readings` are separate**: one cuneiform sign in a text can have multiple competing readings, each scoped to a language + period.

## Loanwords and the Sprachbund

Sumerian → Akkadian is the highest-volume direction. Technical, administrative, religious, scribal vocabulary flowed up the prestige gradient:

| Sumerian | Akkadian | Meaning |
|---|---|---|
| `dubsar` (DUB.SAR) | `ṭupšarru` | scribe (lit. "tablet-writer") |
| `engar` | `ikkaru` | farmer |
| `nagar` | `naggāru` | carpenter |
| `é-gal` | `ekallu` | palace (lit. "great house") |
| `abzu` | `apsû` | abyss |
| `gal` | `gallu` | "great" → "demon" (semantic shift!) |

Akkadian → Hittite/Elamite is mostly **logographic**, not phonetic — Hittite scribes wrote Akkadian words as logograms and pronounced them in Hittite.

The **"Banana Language" hypothesis** notes pre-Sumerian / pre-Akkadian names with reduplicated final syllables (Bunene, Zababa, Inana) — a substrate language we can't identify, possibly shared between Sumerian and Elamite. Useful for understanding *why* certain etymologies are unknowable.

## Determinatives — silent classifiers

Determinatives are signs that classify but aren't pronounced. They're encoded in ATF as `{...}`:

| Determinative | Class |
|---|---|
| `{d}` | divine name (DINGIR) |
| `{m}`, `{lu2}` | male personal name |
| `{f}`, `{munus}` | female personal name |
| `{ki}` | place name (city) |
| `{kur}` | foreign land / mountain |
| `{giš}` | wooden object |
| `{kuš}` | leather |
| `{na4}` | stone |
| `{uruda}` | copper |
| `{tug2}` | textile |

**Schema implication**: determinatives are metadata on a token, not separate tokens. They contribute to classification (named-entity recognition, semantic categorization) but never to phonological reconstruction.

## State of understanding

- **Akkadian** — best-understood. Von Soden's *GAG* is canonical. Largest corpus.
- **Sumerian** — strong (Jagersma 2010), but the verbal prefix system is genuinely contested.
- **Hittite** — strong (Hoffner / Melchert). Logogram-heavy texts hide some Hittite phonology behind Sumerograms.
- **Elamite** — improving. Recent breakthroughs in Linear Elamite (Desset and others) are starting to feed back into Cuneiform Elamite understanding. Small corpus, late Old-Persian influence distorts Achaemenid Elamite.

## Cross-cutting decipherment story

Cuneiform was deciphered via **trilingual inscriptions** — Bisitun (Old Persian + Elamite + Babylonian) was the Rosetta Stone equivalent. Hittite's IE-ness was confirmed via thousands of tablets from Boğazköy. Sumerian was deciphered AFTER Akkadian because the bilingual Sumerian-Akkadian lexical lists let scholars work backward.

This history matters for the schema: bilingual / trilingual texts are not edge cases — they're the foundation of the entire field. The data model has to treat them as first-class.

## Where this maps in the codebase

| Concept | Schema | Skill / code |
|---|---|---|
| Ergative vs accusative | `morphology` table (per-language conventions) | `gs-expert-data-model/query-patterns.md` |
| Root + pattern (Akkadian) | `glossary_entries.citation_form` (+ proposed `root`, `stem`) | `gs-expert-assyriology/lexical-model.md` |
| Heterography (Hittite) | `tokens.surface_form` vs `lemmatizations.lemma_id` | `gs-expert-assyriology/atf-format.md` |
| Class suffixes (Elamite) | `morphology` per-language features | — |
| Polyvalency | `tokens` → many `token_readings` | `gs-expert-data-model/lexical-api.md` |
| Determinatives | parsed from ATF, stored as token metadata | `gs-expert-assyriology/atf-format.md` |
| Dialect tracking | `lexical_lemmas.dialect`, per-annotation | `gs-expert-assyriology/languages.md` |
| Competing analyses | `annotation_run_id` on every row | `gs-orient-project/SKILL.md` |

## Where to read more

- Long-form synthesis with citations: [Cuneiform Linguistics Synthesis (wiki)](https://github.com/wittkensis/glintstone/wiki/Research-Cuneiform-Linguistics-Synthesis)
- The disagreement-tolerant schema design that flows from all of this: [`gs-expert-data-model/SKILL.md`](../gs-expert-data-model/SKILL.md)
