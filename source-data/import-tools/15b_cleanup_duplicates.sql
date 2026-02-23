-- ============================================================================
-- Cleanup Script: Remove Duplicate ePSD2 Data
-- ============================================================================
-- Purpose: Clean up duplicate sign entries and associations before re-import
--          with revised schema (single values array + case-insensitive matching)
--
-- What this does:
--   1. Deletes duplicate sign entries (8,372 → 2,093 unique)
--   2. Deletes existing sign-lemma associations (will be recreated)
--
-- Date: 2026-02-21
-- ============================================================================

BEGIN;

-- Count before cleanup
SELECT
    (SELECT COUNT(*) FROM lexical_signs WHERE source = 'epsd2-sl') as sign_count_before,
    (SELECT COUNT(*) FROM lexical_sign_lemma_associations WHERE source = 'epsd2-sl') as assoc_count_before;

-- Delete duplicate signs (keep lowest ID for each sign_name + source combination)
DELETE FROM lexical_signs a
USING lexical_signs b
WHERE a.id > b.id
  AND a.sign_name = b.sign_name
  AND a.source = b.source
  AND a.source = 'epsd2-sl';

-- Delete existing associations (will be recreated with new logic)
DELETE FROM lexical_sign_lemma_associations WHERE source = 'epsd2-sl';

-- Add unique constraint for idempotency (now that duplicates are removed)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'lexical_signs_sign_name_source_key'
    ) THEN
        ALTER TABLE lexical_signs ADD CONSTRAINT lexical_signs_sign_name_source_key UNIQUE (sign_name, source);
    END IF;
END
$$;

-- Count after cleanup
SELECT
    (SELECT COUNT(*) FROM lexical_signs WHERE source = 'epsd2-sl') as sign_count_after,
    (SELECT COUNT(*) FROM lexical_sign_lemma_associations WHERE source = 'epsd2-sl') as assoc_count_after;

-- Show remaining unique signs
SELECT
    COUNT(DISTINCT sign_name) as unique_sign_names,
    COUNT(*) as total_sign_records
FROM lexical_signs
WHERE source = 'epsd2-sl';

COMMIT;

-- ============================================================================
-- Expected Results:
--   - sign_count_before: 8,372
--   - sign_count_after: 2,093 (unique signs)
--   - assoc_count_before: 2,325
--   - assoc_count_after: 0 (will be recreated by import)
-- ============================================================================
