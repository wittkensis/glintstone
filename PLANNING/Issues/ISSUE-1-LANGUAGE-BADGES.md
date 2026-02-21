# Issue 1: Language Badges - Implementation Summary

## Problem
Language badges showing "undetermined" instead of actual language data. Most tablets have language data but aren't displaying badges correctly.

## Root Cause Analysis

**Data discovered:**
- language_map table has 44 entries ✓
- 139,961 artifacts have "Sumerian" language
- 84,736 artifacts have "Akkadian" language
- BUT: 19 unmapped language variants exist due to semicolon vs comma separator issue

**Examples of unmapped variants:**
- "Sumerian; Akkadian" (2,844 tablets) - not in map (map has "Sumerian, Akkadian" with comma)
- "Akkadian; Aramaic" - not in map (map has "Akkadian, Aramaic")
- Multiple other semicolon-separated combinations

**Template macro issue:**
- `/app/templates/components/_macros.html` lines 4-9 has only 12 hardcoded languages
- Falls back to first 2 chars for unmapped languages
- Many CDLI variants not covered

## Solution Implemented

### 1. Added Migration for language_normalized Column
**File:** `/data-model/migrations/002_add_language_normalized.sql`

Follows the pattern of period_normalized and provenience_normalized.

**To run:**
```sql
ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS language_normalized TEXT;
CREATE INDEX IF NOT EXISTS idx_artifacts_language_normalized ON artifacts(language_normalized);
```

Note: Run this as database superuser if permission error occurs.

### 2. Modified Import Script
**File:** `/source-data/import-tools/05_import_artifacts.py`

**Changes:**
- Added `load_lookup_tables()` to return `lang_map` (line 88-106)
- Added `normalize_language()` function (line 121-145) that:
  - Handles semicolon→comma normalization
  - Looks up in language_map
  - Returns normalized full_name
- Updated main() to load lang_map (line 178)
- Updated record tuple to use `normalize_language(language_raw, lang_map)` (line 222)

### 3. Update Repository (TODO)
**File:** `/api/repositories/artifact_repo.py` line 56

Change:
```python
# FROM:
SELECT a.language
# TO:
SELECT COALESCE(a.language_normalized, a.language) as language
```

This uses normalized value if available, falls back to raw.

### 4. Expand Template Macro (TODO)
**File:** `/app/templates/components/_macros.html` lines 4-9

Current abbr_map has only 12 languages. Options:
1. Expand to cover all 44 language_map entries
2. Use a more intelligent fallback (first 2-3 chars of normalized name)
3. Create CSS classes for each language family and use color coding

## Next Steps

1. **Run migration** (as superuser if needed):
   ```bash
   cd /Volumes/Portable\ Storage/Glintstone
   python3 run_migration_002.py
   # OR as postgres user
   ```

2. **Update repository to use language_normalized**

3. **Expand template macro abbr_map** to cover all languages

4. **Reimport artifacts** with normalized language:
   ```bash
   cd source-data/import-tools
   python3 05_import_artifacts.py --reset
   ```

5. **Verify** language badges on:
   - P000001 (should show language badge based on data)
   - Sumerian tablets → "SU" badge
   - Akkadian tablets → "AK" badge
   - "Sumerian; Akkadian" tablets → Normalized to "Sumerian and Akkadian"

## Expected Results

After implementation:
- **139,961 Sumerian tablets** will show "SU" badge
- **84,736 Akkadian tablets** will show "AK" badge
- **2,844 Sumerian;Akkadian tablets** will show correct badge (normalized to "Sumerian and Akkadian")
- Unmapped variants reduced from 19 to 0

## Files Modified

- ✅ `/source-data/import-tools/05_import_artifacts.py` - Added language normalization
- ✅ `/data-model/migrations/002_add_language_normalized.sql` - Migration script
- ⏸️ `/api/repositories/artifact_repo.py` - Needs update to use language_normalized
- ⏸️ `/app/templates/components/_macros.html` - Needs expanded abbr_map

## Notes

- Keep raw `language` column for data provenance
- Use `language_normalized` for display/filtering
- Normalization handles both data quality (semicolons) and lookup (variants)
