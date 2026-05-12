-- ============================================================================
-- Migration 008a: Alter Existing Tables for Single Values Array
-- ============================================================================
-- Purpose: Update lexical_signs table to use single values array
--          instead of separate logographic_values/syllabic_values
--
-- Changes:
--   1. Add new 'values' column
--   2. Copy data from logographic_values (since both had same data)
--   3. Drop old columns
--   4. Update indexes
--   5. Add unique constraint for idempotency
--   6. Add value column to associations table
--
-- Date: 2026-02-22
-- ============================================================================

BEGIN;

-- Add new values column to lexical_signs
ALTER TABLE lexical_signs ADD COLUMN IF NOT EXISTS values TEXT[];

-- Copy data from logographic_values (they were duplicates anyway)
UPDATE lexical_signs SET values = logographic_values WHERE values IS NULL;

-- Drop old indexes
DROP INDEX IF EXISTS idx_lexical_signs_values_log;
DROP INDEX IF EXISTS idx_lexical_signs_values_syll;

-- Drop old columns
ALTER TABLE lexical_signs DROP COLUMN IF EXISTS logographic_values;
ALTER TABLE lexical_signs DROP COLUMN IF EXISTS syllabic_values;

-- Create new index for values
CREATE INDEX IF NOT EXISTS idx_lexical_signs_values ON lexical_signs USING GIN(values);

-- NOTE: Unique constraint will be added AFTER cleanup (see 15b_cleanup_duplicates.sql)
-- This is because duplicates must be removed before constraint can be applied

-- Update comment
COMMENT ON COLUMN lexical_signs.values IS 'All sign values/readings (logographic + syllabic mixed). Reading type determined at association level.';

-- Add value column to associations table (if not exists)
ALTER TABLE lexical_sign_lemma_associations ADD COLUMN IF NOT EXISTS value TEXT;

COMMENT ON COLUMN lexical_sign_lemma_associations.value IS 'Specific sign value used (preserves subscripts: du₃, aya₂)';

-- Verify changes
SELECT
    'lexical_signs' as table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'lexical_signs'
  AND column_name IN ('values', 'logographic_values', 'syllabic_values')
ORDER BY column_name;

SELECT
    'lexical_sign_lemma_associations' as table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'lexical_sign_lemma_associations'
  AND column_name = 'value';

-- Check unique constraint
SELECT
    conname as constraint_name,
    contype as constraint_type
FROM pg_constraint
WHERE conrelid = 'lexical_signs'::regclass
  AND contype = 'u';

COMMIT;

-- ============================================================================
-- Expected Results:
--   - lexical_signs.values column exists (TEXT[])
--   - lexical_signs.logographic_values column does NOT exist
--   - lexical_signs.syllabic_values column does NOT exist
--   - idx_lexical_signs_values index exists (GIN)
--   - lexical_signs_sign_name_source_key unique constraint exists
--   - lexical_sign_lemma_associations.value column exists (TEXT)
-- ============================================================================
