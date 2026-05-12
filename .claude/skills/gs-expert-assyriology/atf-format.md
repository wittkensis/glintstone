---
question: "How do I read or parse ATF — what does each marker mean, what differs between CDLI ATF and eBL ATF, and which tokenization mode applies?"
created: 2026-05-11
modified: 2026-05-11
context: "Pulled from skills-disabled/assyriology/SKILL.md and refined during the 2026-05-11 knowledge architecture overhaul. The eBL ATF grammar reference is the authoritative file at source-data/sources/eBL/metadata/ebl-api/docs/ebl-atf.md."
status: active
audience: [claude, engineers, scholars]
owners: [eric]
related_issues: []
related_skills: [gs-expert-assyriology, gs-expert-integrations]
supersedes: null
superseded_by: null
---

# ATF — ASCII Transliteration Format

The digital notation scholars use to type cuneiform. Two dialects matter for Glintstone: **CDLI ATF** (simpler, in the bulk catalog) and **eBL ATF** (extended, with full EBNF).

## CDLI ATF — minimum viable shape

```
&P227657 = KTT 188
#atf: lang sux
@obverse
1. ninda
2. kasz
$ ruling
#tr.en: bread, beer
>>Q000123 1
```

Line protocols:

| Marker | Meaning |
|---|---|
| `&P######` | Tablet ID line (optionally `= designation`) |
| `#atf: lang XXX` | Language declaration (`sux`, `akk`, `hit`, `elx`) — drives tokenization mode |
| `@SURFACE` | Surface marker (see table below) |
| `N.` | Line number |
| `N'.` | Uncertain line number |
| `$` | State/damage note (often `$ ruling`, `$ broken`) |
| `#tr.XX:` | Translation line (XX = language code) |
| `#note:` | Editorial comment |
| `>>Q######` | Composite-text reference |

Surface markers and their canonical DB form:

| ATF | DB | Aliases |
|---|---|---|
| `@obverse` | `obverse` | `@o` |
| `@reverse` | `reverse` | `@r` |
| `@left` | `left_edge` | `@l.e.` |
| `@right` | `right_edge` | `@r.e.` |
| `@top` | `top_edge` | `@t.e.` |
| `@bottom` | `bottom_edge` | `@b.e.` |
| `@seal` | `seal` | — |

`@column N` → `text_lines.column_number`, not a row in `surfaces`.

Damage / uncertainty: `[...]` = broken, `[xx]` = guessed text, plain text = certain reading.

## eBL ATF — extended notation

Full EBNF lives at `source-data/sources/eBL/metadata/ebl-api/docs/ebl-atf.md`. Highlights:

| Notation | Meaning | Example |
|---|---|---|
| `{d}`, `{f}`, `{ki}` | Determinatives (divine, female, place) | `{d}UTU` = the god Shamash |
| `\|A.B\|` | Compound sign | `\|A.AN\|` |
| `@g`, `@t`, `@s` | Sign modifiers (gunu, tenu, sheshig) | `A@g` |
| `⸢...⸣` | Uncertain reading | `⸢GIŠ⸣` |
| `[...]` | Broken/missing | `[x x]` |
| `◦` | No longer visible | `◦GIŠ◦` |
| `%akk`, `%sux`, `%n` | Language or normalization shift | `%n ša-ar-ru-um` |

## Tokenization modes

The tokenizer in `ingestion/connectors/atf_parser.py` switches modes based on the `#atf: lang` header:

| Mode | Applies to | Behavior |
|---|---|---|
| **Mode 0** | Akkadian, Elamite, Hittite, Hurrian | Strip subscripts (`du₃` → `du`). Subscripts only disambiguate signs in these languages. |
| **Mode 1** | Sumerian | Preserve subscripts (`du`, `du₂`, `du₃` are distinct lexemes). |
| **Mode 2** | Greek, Latin (transcribed loans) | Character sequences as-is. |

Getting this wrong silently corrupts Sumerian lexical work — every `du₃` becomes indistinguishable from `du`.

## Sign tokenization rules

When parsing a line into tokens:

1. Split on whitespace.
2. Determinative-prefixed sequences (`{d}UTU`) are one token where the determinative is metadata.
3. Compound signs `|A.B|` are one token.
4. Modifiers (`@g`, `@t`) are attached to the preceding sign.
5. Damage brackets do not affect token boundaries — they're applied as state.

## Common parse failures

- `&P` headers without a trailing space before `=` (CDLI sometimes drops it)
- Missing `#atf: lang` — fall back to whatever the catalog row says; if neither, dead-letter the ATF
- `@column N` appearing before any surface marker (rare but valid; treat as continuing previous surface)
- Mixed language tablets — split by `%lang` shifts, not by surface

## References

- CDLI ATF wiki: http://cdli.ox.ac.uk/wiki/doku.php?id=atf_structure
- ORACC ATF primer: http://oracc.org/doc/help/editinginatf/primer/
- eBL ATF EBNF: `source-data/sources/eBL/metadata/ebl-api/docs/ebl-atf.md`
- current parser: `ingestion/connectors/atf_parser.py`
