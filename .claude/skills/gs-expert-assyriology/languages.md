---
question: "How do the languages cuneiform records (Akkadian, Sumerian, Hittite, Elamite) actually work, and where do scholars disagree?"
created: 2026-05-11
modified: 2026-05-11
context: "Pulled from skills-disabled/assyriology/SKILL.md and the PLAN/Linguistics Schema research reports. The scholarly-debate notes matter: when the data model stores 'competing analyses', this is the linguistic reality it's tracking."
status: active
audience: [claude, engineers, scholars]
owners: [eric]
related_issues: []
related_skills: [gs-expert-assyriology, gs-expert-data-model]
supersedes: null
superseded_by: null
---

# Cuneiform languages — capsule reference

Four languages dominate the Glintstone corpus. Same script, very different grammars.

## The four

| Language | Type | Key features | Tokenization mode |
|---|---|---|---|
| **Akkadian** | Semitic (East Semitic) | Root-stem morphology, triconsonantal roots, dialect chronology (OA, OB, MB, SB, NA, NB, LB) | Mode 0 — strip subscripts |
| **Sumerian** | Language isolate | SOV, agglutinative, ergative-absolutive, slot-based verb chain | Mode 1 — preserve subscripts |
| **Elamite** | Language isolate (likely) | Agglutinative; corpus sparse | Mode 0 |
| **Hittite** | Indo-European (Anatolian) | Heavy use of Sumerian + Akkadian logograms — graphemic ≠ linguistic layer | Mode 0 |

Also present at smaller scale: **Hurrian**, **Urartian**, **Ugaritic**, **Eblaite**, **Old Persian**.

## Akkadian — root-stem-TAM system

- **Root**: usually triconsonantal (`b-n-y` "build", `š-a-l` "ask")
- **Stem**: G (basic), D (intensive), Š (causative), N (passive); each has -t- and -tn- iterative variants (Gt, Gtn, Gtt …)
- **TAM**: tense-aspect-mood — preterite, durative, perfect, stative, precative, …
- **Agreement**: person (1/2/3), gender (m/f), number (sg/du/pl)

Example: *ibnī* = `i-bn-ī` = (3rd person)-(b-n-y root)-(preterite singular) = "he built" (G-stem preterite).

**Dialects matter.** The same root behaves differently in Old Babylonian vs Neo-Assyrian. The `glossary_entries.dialect` column tracks this.

## Sumerian — slot-based verb chain

The Sumerian verb is a chain of slots:

```
[modal]-[conjugation]-[ventive]-[dimensional]-[person]-STEM-[ergative]-[pronominal]
```

Example: *mu-n-na-ab-sum* = "he gave it to him"

- `mu-` ventive
- `n-` 3sg.IO dative
- `na-` 3sg.human.IO allative
- `b-` 3sg.neuter.DO
- `sum` give (stem)

**Scholarly debate.** Jagersma, Zolyomi, and Edzard analyze the prefix slots differently. ORACC follows Jagersma. Glintstone stores both ORACC's analysis and (where present) alternatives, keyed to their `annotation_run`. This is not a bug; it reflects the field.

## Hittite — logogram-heavy

A Hittite text can contain:
- Hittite words written syllabically
- Sumerograms (Sumerian words used as shorthand for Hittite words, rendered in UPPERCASE in transliteration)
- Akkadograms (Akkadian words used as shorthand, often italicized or marked)
- Determinatives

Lemmatization for Hittite usually targets the underlying Hittite word, even when the surface is a Sumerogram. The schema supports this via the `cad_logograms` table linking Akkadian entries to Sumerian sign-forms.

## Elamite — sparse

Far less data than the others. Lemmatization coverage is thin. Handle gracefully (NULL is common).

## ORACC POS codes

| Code | Meaning | Code | Meaning |
|---|---|---|---|
| **N** | Noun | **V/i** | Intransitive verb |
| **V/t** | Transitive verb | **AJ** | Adjective |
| **DN** | Divine name | **PN** | Personal name |
| **GN** | Geographic name | **NU** | Number |

Extended: `SN` settlement, `WN` watercourse, `ON` object, `RN` royal name, `MN` month, `YN` year, `QN` qualification.

Full list: http://oracc.org/doc/help/editinginatf/primer/lexicaldata/

## Morphological lemmatization (BabyLemmatizer)

Glintstone integrates **BabyLemmatizer** (`ml/models/`), a neural sequence-to-sequence model (OpenNMT) that does POS-tagging + lemmatization.

- In-vocabulary accuracy: 94–96%
- Out-of-vocabulary: 68–84%
- Output: CoNLL-U format (`ID | FORM | LEMMA | UPOS | XPOS | FEATS | …`)
- Modes: 0 (Akkadian, Elamite, Hittite, Hurrian), 1 (Sumerian), 2 (Greek, Latin)
- Outputs are stored with a `babylemmatizer-vX.Y` annotation run — lower confidence than human annotation by convention.

## ORACC lemmatization format

```
inst="%sux:za-ba4-lu2=[sorrow//sorrow]N"
     ^^^^  ^^^^^^^^^  ^^^^^^  ^^^^^^ ^
     lang    form        CF     GW   POS
```

- `ref`: `P######.line.word` (1-indexed)
- `morph`: optional, language-specific morphology string

## Search implications

- "Find all forms of `banûm`" requires lemma-based search: surface forms (`ibnī`, `ibtanī`, `ubnī`, `nibnī`) all link to the same lemma.
- "Find every use of the sign `KA`" requires graphemic search across both Sumerian (`ka` "mouth") and Akkadian (`pû`, written `KA` as logogram) — query through `cad_logograms`.

For schema details, see [lexical-model.md](lexical-model.md) and `gs-expert-data-model/lexical-api.md`.
