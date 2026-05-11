# CRITICAL FINDINGS: Translation Pipeline Data Status

## Executive Summary

The Glintstone database contains **353,283 artifacts** with **1.4M text lines** and **3.9M tokens**, but the translation pipeline is **incomplete**. This document explains the current state and what's needed for the UI.

---

## Q1: Why Are Token Readings NULL? (CRITICAL)

### Answer: Import Pipeline Incomplete

**Root Cause:** Step 10 of the v2 import pipeline (`10_import_token_readings.py`) has **not been built**.

**Current State:**
- ✅ **tokens table:** 3,957,240 rows with `gdl_json` populated
- ❌ **token_readings table:** **0 rows** (completely empty)
- ❌ **lemmatizations table:** 65,906 rows but all fields are string `'None'`

**What Exists:**
```javascript
// tokens table (populated)
{
  "id": 556573,
  "line_id": 282193,
  "position": 0,
  "gdl_json": "{\"frag\": \"ki\"}"  // ✅ Raw ORACC GDL data
}
```

**What's Missing:**
```javascript
// token_readings table (EMPTY - 0 rows)
{
  "token_id": 556573,
  "form": "ki",                  // ❌ Not extracted
  "reading": "KI",                // ❌ Not extracted
  "sign_function": "logo",        // ❌ Not extracted
  "damage": "intact"              // ❌ Not extracted
}
```

### Technical Details

From `import-pipeline.yaml`:
```yaml
- step: 10
  name: Token readings
  status: not_built              # ← THE PROBLEM
  script: 10_import_token_readings.py
  description: >
    How each token is read (sign values assigned to graphemes).
    Parse GDL data from tokens.gdl_json and insert into token_readings.
```

**What Step 10 Should Do:**
1. Read `tokens.gdl_json` for all 3.9M tokens
2. Parse GDL structure to extract:
   - `form` (written form, e.g., "ninda")
   - `reading` (sign value, e.g., "NINDA")
   - `sign_function` (logogram/syllabogram/determinative)
   - `damage` (intact/damaged/missing)
3. Insert ~8M rows into `token_readings` (multiple readings per token possible)

**Pipeline Status Misleading:**
- `pipeline_status.reading_complete = 1.0` (100%)
- BUT this only means **ATF text exists**, not that token decomposition is done
- `reading_complete` should be renamed `atf_complete`

### Impact on UI

**Cannot Currently Display:**
- ❌ Interactive word-level highlighting
- ❌ Form vs. reading distinction (e.g., "ninda" vs "NINDA")
- ❌ Damage state per token (intact/damaged/missing)
- ❌ Sign function indicators (logogram badges)

**Can Display (Workarounds):**
- ✅ Raw ATF line text (`text_lines.raw_atf`)
- ✅ Full translations (positional matching)
- ✅ Parsed tokens (from `gdl_json` if needed)
- ✅ Line-level metadata (surface, ruling markers)

### Recommended Actions

**Short-term (Current UI):**
1. Display `text_lines.raw_atf` as plain text
2. Use positional translation matching (see Q2)
3. Parse `tokens.gdl_json` client-side if needed for basic word splitting
4. Add "Token readings pending" badge to pipeline status

**Long-term (Full Pipeline):**
1. Build Step 10 import script to populate `token_readings`
2. Build Step 11 import script to populate `lemmatizations` with real data
3. Update `pipeline_status` metrics to reflect actual completion
4. Add `/artifacts/{p_number}/tokens/{token_id}/readings` API endpoint

### Verification Queries

```sql
-- Confirm token_readings is empty
SELECT COUNT(*) FROM token_readings;
-- Result: 0

-- Confirm tokens have gdl_json
SELECT COUNT(*) FROM tokens WHERE gdl_json IS NOT NULL;
-- Result: 3,957,240

-- Check lemmatizations data quality
SELECT citation_form, guide_word, pos
FROM lemmatizations
WHERE citation_form != 'None'
LIMIT 10;
-- Result: 0 rows (all are string 'None')
```

---

## Impact on Translation Pipeline UI

### What Data IS Available

| Layer | Table | Status | Count | Quality |
|-------|-------|--------|-------|---------|
| Identity | `artifacts` | ✅ Complete | 353,283 | High |
| Physical | `text_lines` | ✅ Complete | 1,395,668 | High |
| Graphemic | `tokens` | ⚠️ Partial | 3,957,240 | GDL only |
| Reading | `token_readings` | ❌ Missing | 0 | N/A |
| Linguistic | `lemmatizations` | ❌ Placeholder | 65,906 | Unusable |
| Semantic | `translations` | ✅ Complete | 43,777 | High |
| Semantic | `glossary_entries` | ✅ Complete | 45,572 | High |

### Graceful Degradation Strategy

**Layer 1: ATF Display (Fully Functional)**
- Show raw ATF lines
- Surface tabs (obverse/reverse)
- Structural markers (rulings, blank lines)
- Parallel translation column

**Layer 2: Token Highlighting (Requires Client-Side Parse)**
- Parse `gdl_json` in JavaScript
- Basic word clickability
- Fallback to string splitting if GDL parse fails

**Layer 3: Lemmatization (Blocked)**
- Awaits Step 11 completion
- Show "Lemmatization pending" state
- Link to glossary for manual lookup

**Layer 4: Full Pipeline (Future)**
- All token readings
- Confidence indicators
- Competing interpretations
- Scholar annotations

---

## Next Steps

1. **Document current limitations** in UI with helpful messaging
2. **Build Step 10 import script** (priority: high, complexity: medium)
3. **Add API endpoints** for token readings when available
4. **Design progressive enhancement** UI that works now and improves later

---

## References

- Import pipeline spec: `/data-model/v2/import-pipeline.yaml`
- Database schema: Lines 479-520 (Step 10 definition)
- Investigation script: `/investigate_tokens.py` (generated during analysis)
- Schema verification: `/check_schema.py` (generated during analysis)
