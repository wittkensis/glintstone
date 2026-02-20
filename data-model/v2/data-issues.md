# v2 Schema Data Issues & Resolutions

12 critical issues found by pressure-testing the v2 schema against the live Glintstone database (314 MB, 389,715 artifacts). Each issue would break or corrupt imports if not addressed.

**Related docs**: [glintstone-v2-schema.yaml](glintstone-v2-schema.yaml) (schema fixes), [data-quality.md](data-quality.md) (trust architecture), [import-pipeline-guide.md](import-pipeline-guide.md) (validation per step).

---

## Issue 1: Period String Chaos

**Severity:** High — breaks filtering, aggregation, and sorting.

46+ distinct period formats. Same period with/without date ranges, uncertainty markers.

| Format | Count | Example |
|--------|-------|---------|
| Canonical only | 194,556 | `Old Babylonian` |
| With date range | 73,211 | `Old Babylonian (ca. 1900-1600 BC)` |
| With uncertainty | 1,247 | `Neo-Babylonian (ca. 626-539 BC) ?` |

**Fix** (addressed in v2 schema): `period_normalized` column + `period_canon` lookup table.
- Regex strip `(ca. ...)` and `?` suffix
- Map to canonical via lookup
- Preserve raw in `period` column
- Schema ref: `artifacts.period_normalized`, `period_canon` table

---

## Issue 2: Language Field Multi-Values + Code Mismatch

**Severity:** High — breaks language filtering and ORACC cross-referencing.

- Multi-language artifacts: `Sumerian; Akkadian` (2,854), `Akkadian; Persian; Elamite` (138)
- CDLI uses English names, ORACC uses ISO codes (sux, akk, akk-x-stdbab)
- ORACC lemmas have `-949` suffixes (akk-949) = uncertain language attribution

**Fix** (addressed in v2 schema): `language_map` lookup table + `languages` JSON array column. `-949` suffix becomes `uncertain` flag on lemmatization.
- Schema ref: `artifacts.languages`, `language_map` table

---

## Issue 3: Genre Case Inconsistency

**Severity:** Medium — causes duplicate filter facets.

`Administrative` (194,556) vs `administrative` (725). Multi-genre: `Lexical; Mathematical` (109).

**Fix:** `genre_canon` lookup table normalizing to title-case. `genre` = primary, `genres` JSON array for multi-genre.

---

## Issue 4: 72% of Lemmas Are Unlemmatized Tokens

**Severity:** High — v2 must correctly separate identified words from damaged/unread tokens.

| Category | Count | % |
|----------|-------|---|
| Fully identified words | 86,659 | 28.1% |
| Damaged/unread tokens | 221,912 | 71.9% |
| Partially read names | 39 | 0.01% |

Top unidentified forms: `x` (38,833 completely illegible), `geš` (4,777 determinative for wood), `1(N01)` (4,678 archaic number tokens).

**Fix:** ALL 308k become `tokens`. Only 86,659 with cf != NULL and cf != 'X' get `lemmatizations`. Unidentified tokens exist at reading layer with damage info.

**Import rule** (addressed in v2 schema): `IF cf IS NOT NULL AND cf != '' AND cf != 'X' THEN token + lemmatization ELSE token only`
- Schema ref: `tokens` table (all 309k), `lemmatizations` table (86k with real identifications)

---

## Issue 5: Sign Annotations Use MZL Numbers, No Concordance

**Severity:** High — 11,070 sign bounding box annotations unresolvable to canonical sign system.

CompVis annotations use MZL integers (839, 748, 10). Database uses OGSL names (A, AN, |A.AN|). No mapping exists.

216 annotations have empty surface values.

**Fix:**
1. Auto-match MZL -> OGSL via Unicode bridge (eBL ebl.txt + OGSL)
2. Auto-match via shared reading values
3. Flag ~200-400 unresolved for manual curation
4. Store in `signs` table: new `mzl_number`, `abz_number` columns
5. Populate `sign_id` FK on sign_annotations via concordance
6. Empty surfaces -> `unknown`
- Schema ref: `signs.mzl_number`, `signs.abz_number`, `sign_annotations.sign_id`
- Status: Addressed in v2 schema; concordance.py implementation pending

---

## Issue 6: Provenience Normalization

**Severity:** Medium — breaks geographic aggregation and Pleiades linking.

Mixed formats: `Nippur (mod. Nuffar)`, `Sippar-Yahrurum (mod. Tell Abu Habbah) ?`, `uncertain (mod. Babylonia)`.

**Fix:** `provenience_canon` lookup table. `provenience_normalized` = ancient name only.

---

## Issue 7: P-Number Format Variation

**Severity:** Low — but will cause validation errors if uncaught.

Most: 7-char `P######` (P000001-P999999). Some exceed range: P1273754, P2757983.

**Fix:** p_number as TEXT. Validation regex: `P\d{6,7}`. Update zero-pad logic.

---

## Issue 8: ORACC Texts Without CDLI ATF (2,215 orphans)

**Severity:** Medium — these texts have lemmatization but no intermediate text structure.

ORACC has linguistic analysis for ~7,500 texts. 2,215 of these have no corresponding CDLI ATF.

Top orphans by lemma count: P507554 (4,266), Q000055 (2,633), P282465 (2,595).

Several are Q-numbers (composite texts) — scholarly reconstructions without a single physical ATF source.

**Fix:** Build `text_lines` from ORACC CDL data (which contains line structure). Set `source=oracc`. Create tokens from CDL nodes as normal.

---

## Issue 9: Empty glossary_senses (0 rows)

**Severity:** High — users cannot see the full range of word meanings.

`glossary_senses` table schema exists but has 0 rows. Data IS available in ORACC glossary JSON (5,271 Sumerian entries have senses).

Example: Sumerian word "a" has 9 senses — arm (86%), strap (6%), horn (1%), etc.

**Fix:** Parse `senses[]` array from every ORACC glossary entry. Each sense has: `mng` (meaning), `icount` (frequency), `pos`, `oid`, nested `forms[]`.

---

## Issue 10: Composite Multi-Value Fields

**Severity:** Medium — comma-separated cache fields are fragile and duplicate data.

Composites store derived metadata as comma-separated strings (`periods_cache`, `proveniences_cache`, `genres_cache`). Period names themselves contain commas.

**Fix:** Remove cache columns. Derive via SQL view from artifact_composites JOIN artifacts. Composites keep only: `q_number`, `designation`, `exemplar_count`.

---

## Issue 11: Translation Source Column Migration

**Severity:** Low — but must not lose source attribution.

All 5,597 translations have `source=cdli`. Replacing with `annotation_run_id` FK.

**Resolution: No data loss.** Create annotation_runs record for cdli:atf import. Every translation row gets `annotation_run_id` pointing to that record. Join to annotation_runs returns `source_name='cdli:atf'` with richer provenance (date, method, scope).

---

## Issue 12: Glossary Entry Dedup Across Projects

**Severity:** Medium — must preserve source attribution while avoiding confusion.

1,726 duplicate pairs across import methods. All share same guide_word and POS. Attestation counts and spelling variants differ.

Current `project` values (`extracted`, `json`) are import-method labels, not actual ORACC project names.

**Fix:**
1. Keep ALL entries from all projects
2. Correct `project` to actual ORACC project names (dcclt, saao, rinap, etc.)
3. UNIQUE(headword, language, project) constraint
4. For named_entities: dedup by headword+language, link back to ALL source entries
5. API includes source attribution per project
