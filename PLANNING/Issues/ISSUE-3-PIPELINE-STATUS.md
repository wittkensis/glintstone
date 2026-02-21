# Issue 3: Pipeline Summary Status - Implementation Summary

## Problem
Pipeline summary badges not showing correct state for tablets. P000001 has 6 text lines but shows Reading=0.0 instead of Reading=1.0.

## Root Cause
The `pipeline_status` table exists and has 100% coverage (353,283 rows), but scores were calculated incorrectly during initial population.

**Current incorrect data:**
- P000001: Physical=0.3, Reading=0.0 (WRONG - should be Physical=0.0, Reading=1.0)
- Most tablets: Physical=0.3 regardless of actual image presence

**Actual data in database:**
- 101,402 artifacts have ATF text lines
- 1,687 artifacts have lemmatizations
- 2,492 artifacts have translations
- Only 1 artifact has images
- Only 1 artifact has sign annotations

## Solution Created

Created three approaches to recalculate scores:

### 1. Python Script with Batched Updates
**File:** `/source-data/import-tools/19_recalculate_pipeline_status.py`
- Processes in batches of 5,000 artifacts
- Shows progress reporting
- Uses subqueries for each batch
- **Issue:** Very slow due to complex subqueries on large dataset

### 2. Python Script with Temp Tables
**File:** `/source-data/import-tools/19_recalculate_pipeline_status_fast.py`
- Pre-computes counts in temporary tables
- Single UPDATE with LEFT JOINs
- **Issue:** Hangs on final UPDATE step (too many JOINs on 353k rows)

### 3. Direct SQL Approach (RECOMMENDED)
**File:** `/source-data/import-tools/recalc_pipeline_simple.sql`
- 5 separate UPDATE statements (one per pipeline stage)
- Uses `EXISTS` instead of `COUNT` for better performance
- Can be run directly with psql or via Python wrapper

## How to Run (Choose One)

### Option A: Direct SQL (Fastest)
```bash
cd /Volumes/Portable\ Storage/Glintstone/source-data/import-tools
PGPASSWORD=glintstone psql -h 127.0.0.1 -p 5432 -U glintstone -d glintstone -f recalc_pipeline_simple.sql
```

### Option B: Python Script
```bash
cd /Volumes/Portable\ Storage/Glintstone/source-data/import-tools
python3 19_recalculate_pipeline_status.py
```
Note: May take 30+ minutes due to dataset size

### Option C: Manual SQL in Sections
Run each UPDATE separately in a PostgreSQL client to monitor progress:
```sql
-- Step 1: Physical (images)
UPDATE pipeline_status ps
SET physical_complete = CASE WHEN EXISTS (
    SELECT 1 FROM surface_images si JOIN surfaces s ON si.surface_id = s.id
    WHERE s.p_number = ps.p_number LIMIT 1
) THEN 1.0 ELSE 0.0 END;

-- Step 2: Reading (ATF)
UPDATE pipeline_status ps
SET reading_complete = CASE WHEN EXISTS (
    SELECT 1 FROM text_lines WHERE p_number = ps.p_number LIMIT 1
) THEN 1.0 ELSE 0.0 END;

-- (Continue for graphemic, linguistic, semantic...)
```

## Expected Results After Recalculation

- **P000001**: Physical=0.0, Reading=1.0, Graphemic=0.0, Linguistic=0.0, Semantic=0.0
- **101,402 tablets**: reading_complete=1.0
- **1,687 tablets**: linguistic_complete=1.0
- **2,492 tablets**: semantic_complete=1.0

## Verification

After running recalculation, verify with:

```sql
-- Check P000001
SELECT * FROM pipeline_status WHERE p_number = 'P000001';

-- Check summary
SELECT
    SUM(CASE WHEN physical_complete > 0 THEN 1 ELSE 0 END) as with_images,
    SUM(CASE WHEN reading_complete > 0 THEN 1 ELSE 0 END) as with_atf,
    SUM(CASE WHEN linguistic_complete > 0 THEN 1 ELSE 0 END) as with_lemmas
FROM pipeline_status;
```

## Files Modified/Created

- ✅ `/source-data/import-tools/diagnose_pipeline_status.py` - Diagnostic tool
- ✅ `/source-data/import-tools/19_recalculate_pipeline_status.py` - Batched Python version
- ✅ `/source-data/import-tools/19_recalculate_pipeline_status_fast.py` - Temp table version
- ✅ `/source-data/import-tools/recalc_pipeline_simple.sql` - Direct SQL (recommended)

## Next Steps

1. Run one of the recalculation approaches above
2. Verify P000001 and sample tablets show correct scores
3. Test UI to confirm pipeline badges display correctly
4. Comment on GitHub issue #21 with completion status

## Notes for Future

- Consider creating a materialized view for pipeline_status that auto-updates
- Add triggers to update pipeline_status when related data (text_lines, etc.) changes
- Performance: The large UPDATE operations are slow due to dataset size - consider running during off-peak hours
