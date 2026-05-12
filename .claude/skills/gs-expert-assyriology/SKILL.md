---
name: gs-expert-assyriology
description: Ancient Near East linguistics domain expert — ATF format, language morphology, lexical schema, and data-source semantics. Use when the question is about meaning or structure of cuneiform data rather than code patterns.
metadata:
  question: "When am I working on a cuneiform / ANE-linguistics question, and what topic file should I open first?"
  created: 2026-05-11
  modified: 2026-05-11
  context: "Re-homed from .claude/skills-disabled/assyriology/SKILL.md and split into topic files during the 2026-05-11 knowledge architecture overhaul. The previous 300-line monoskill mixed ATF, morphology, sources, and lexical schema — split here for progressive disclosure."
  status: active
  audience: [claude, engineers, scholars]
  owners: [eric]
  related_issues: []
  related_skills: [gs-orient-project, gs-expert-data-model, gs-expert-integrations, gs-expert-ui]
  supersedes: ".claude/skills-disabled/assyriology/SKILL.md"
  superseded_by: null
  triggers: [akkadian, sumerian, hittite, elamite, atf, cuneiform, lemma, glossary, sign, cdli, oracc, ebl, ogsl, epsd2, assyriology, "ancient near east", babylonian, "p-number", determinative, sumerogram, lemmatization, transliteration, normalization]
---

# Glintstone — ANE / cuneiform domain

Domain expertise for cuneiform writing and the languages it records: Akkadian, Sumerian, Elamite, Hittite, and related corpora.

## When to load which topic file

| Question | File |
|---|---|
| "How do I parse this ATF line / what does `{d}` / `⸢...⸣` / `%n` mean?" | [atf-format.md](atf-format.md) |
| "How does Sumerian / Akkadian morphology work? Why does `du₃` differ from `du`? What POS codes does ORACC use?" | [languages.md](languages.md) |
| "What's a lemma vs a sense vs a sign? How is the glossary schema organized? Why are competing analyses kept?" | [lexical-model.md](lexical-model.md) |
| "What does CDLI / ORACC / eBL / OGSL / ePSD2 actually provide and how do its fields map?" | [data-sources.md](data-sources.md) |

## Five concepts that keep coming up

- **P-number** — CDLI artifact identifier (`P227657`). Universal join key. Composites use **Q-numbers**.
- **ATF** — ASCII Transliteration Format. The text representation of cuneiform. CDLI ATF (simple) and eBL ATF (extended) exist; both are valid.
- **Transliteration** — converting signs to Latin letters. *Not* translation.
- **Lemmatization** — linking a token to its dictionary entry. The ~2% bottleneck.
- **Polyvalency** — one sign, many readings. `KA` can be `ka`, `gu`, `dug`, `inim`, or `zu`.

## Five non-negotiables (these reflect the data, not preferences)

1. **Subscripts mean different things by language.** In Sumerian, `du₃` and `du` are different words. In Akkadian, subscripts only disambiguate signs. The tokenizer picks mode 0 vs mode 1 based on the ATF language header. See [atf-format.md](atf-format.md#tokenization-modes).
2. **Competing interpretations are stored.** Two scholars lemmatizing the same word differently both get rows, both keyed to their `annotation_run`. Never silently dedupe.
3. **Scholars genuinely disagree on Sumerian grammar.** Jagersma, Zolyomi, and Edzard analyze the verb chain differently. ORACC follows Jagersma; the schema allows others.
4. **Source attribution is structural.** Every annotation carries `annotation_run_id` → who, when, what version. This is a data-model requirement, not a nicety.
5. **Coverage is sparse.** ~35% have ATF, ~12% translations, ~2% lemmatization. Expect NULLs.

## Outbound references

- 5-minute primer: [docs/assyriology-101.md](../../../docs/assyriology-101.md)
- Long-form research: [docs/research/](../../../docs/research/) — ecosystem, translation history, curriculum structures, academic workflows
- Lexicography terminology source: pulled into [lexical-model.md](lexical-model.md) from `PLAN/Dictionary Taxonomies/Lexicography Terminology.md` (deprecated path)

## When to bring in another skill

- Encoding any of this into the database / schema → `gs-expert-data-model`
- Writing a connector to import a new linguistic resource → `gs-expert-integrations`
- Rendering glossed text or sign tooltips in the UI → `gs-expert-ui`
- "Find me a tablet that demonstrates [phenomenon]" → `gs-curator-artifacts`
