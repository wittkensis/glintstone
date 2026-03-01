# ATF Viewer Options for Translation Facilitation

Three architectures for showing tablet text with translation layers. Each uses the same data (token_readings, lemmatizations, lexical_lemmas, lexical_senses, glossary_forms, artifacts) organized for different workflows.

## Real Data Used

- **P229547 line 40** (OB Sumerian-Akkadian bilingual): `lu₂ šà ḫul gig-ga ak = %a ša le-mu-ut-tam e-ep-šu`
- **P247823 line 13'** (Std Babylonian literary): `[...] ra-man-šú-nu ú-šaḫ-ḫa-zu nu-ul-la-a-tu₂`
- **KBo 50, 009 line 9** (Middle Hittite ritual): `u₄ ur-sag mar-tu# ib₂-ta-sa`

---

## Option A: Interlinear Stack (Philological)

Each layer is a horizontal row under the ATF line. Classic interlinear gloss format.

```
{P-number} · {publication} · {surface} {line}    {period}
ATF     token₁      token₂      token₃      ...
SIGN    {sign_name} {sign_name} {sign_name}
FUNC    {function}  {function}  {function}
LEMMA   {cf [gw]}   {cf [gw]}   {cf [gw]}
POS     {pos_label} {pos_label} {pos_label}
NORM    {norm_form} {norm_form} {norm_form}
GLOSS   {english}   {english}   {english}

LAYERS  ■/□/◧ per layer    [coverage bar]
```

- Toggle layers on/off via checkboxes
- Click token → dictionary detail in side panel
- `⚠` badge for competing lemmatizations
- Language coloring via CSS class from `lemmatizations.language`
- Coverage bar = fraction of tokens with data at each layer
- **Best for:** Teaching, line-by-line translation

---

## Option B: Token Column Grid (Analytical)

Each token is a column. Rows are layers. Spreadsheet-like.

```
         │ TOKEN n    │ TOKEN n+1  │ TOKEN n+2  │
─────────┼────────────┼────────────┼────────────┤
ATF      │ {reading}  │ {reading}  │ {reading}  │
SIGN     │ {name} {꩜} │ {name} {꩜} │ {name} {꩜} │
LEMMA    │ {cf [gw]}  │ {cf [gw]}  │ {cf [gw]}  │
         │ {alt₁}     │            │            │
GLOSS    │ {english}  │ {english}  │ {english}  │
att.     │ {count}    │ {count}    │ {count}    │
─────────┴────────────┴────────────┴────────────┤
COVERAGE  [======    ] {description}             │
```

- Competing lemma candidates shown as expandable sub-rows
- Bilingual lines: separate column groups per language zone
- Attestation counts per token for frequency context
- **Best for:** Research, data quality audit, disambiguation

---

## Option C: Annotation Ribbons (Reading-Oriented) — RECOMMENDED

ATF flows naturally left-to-right. Annotations appear as togglable colored ribbons below.

```
{P-number} · {publication}            {period}
{surface} {line}

  token₁     token₂     token₃     ═══  token₄     token₅
  {LANG_A} ─────────────────────    │    {LANG_B} ──────────

  ┌─ lemma ribbon ──────────────────────────────────┐
  │ {cf [gw]}   {cf [gw]}   {cf [gw]}   {cf [gw]}  │
  └─────────────────────────────────────────────────┘

  ┌─ gloss ribbon ──────────────────────────────────┐
  │ {english}   {english}   {english}   {english}   │
  └─────────────────────────────────────────────────┘

  [coverage bar]  {description}
```

- Ribbon toggles: Lemma / Norm / Gloss / Signs (checkboxes)
- Hover token → tooltip with full chain
- `═══` visual separator at language boundary (= %a tokens)
- `⚠` expands to show competing analyses inline
- Wraps naturally for long lines — best mobile behavior
- **Best for:** Reading, browsing, general scholarly use

---

## Comparison

| | A: Interlinear | B: Token Grid | C: Ribbons |
|---|---|---|---|
| Metaphor | Philological interlinear | Spreadsheet | Annotated reading |
| Best for | Teaching | Research/audit | Reading/browsing |
| Ambiguity handling | Inline ⚠ badges | Expandable rows | Branching under token |
| Bilingual lines | Side-by-side in row | Column groups | Language zone separator |
| Data density | Medium | High | Low (on-demand) |
| Long line behavior | Horizontal scroll | Horizontal scroll | Wraps |
| Mobile | Poor | Poor | Good |
| Implementation | Simple (stacked divs) | Medium (table/grid) | Medium (positioned ribbons) |

## Recommendation

**Option C (Ribbons) as default**, with **Option B (Grid) as "analysis mode" toggle** for deep investigation.

## Shared Implementation Notes

- Language CSS classes from `lemmatizations.language` (no schema changes)
- `=` and `%a` tokens detected as language boundaries (POS=L)
- Coverage bar: count populated layers / total layers per token
- Dictionary detail via existing API endpoints (click-through)
- Token data: JOIN `tokens → token_readings + lemmatizations → lexical_lemmas → lexical_senses`
- Period/provenience from `text_lines → artifacts`
