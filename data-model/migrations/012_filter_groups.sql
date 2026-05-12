-- ============================================================================
-- Migration 012: Period and Provenience Grouping for Filter UI
-- ============================================================================
-- Adds grouping columns to existing canon tables for hierarchical filter display.
-- Adds partial indexes on artifacts for fast cross-filter count queries.
-- ============================================================================

-- Period grouping: scholarly chronological categories
ALTER TABLE period_canon ADD COLUMN IF NOT EXISTS group_name TEXT;
ALTER TABLE period_canon ADD COLUMN IF NOT EXISTS sort_order INTEGER;

-- Provenience grouping: geographic macro-region / sub-region
ALTER TABLE provenience_canon ADD COLUMN IF NOT EXISTS region TEXT;
ALTER TABLE provenience_canon ADD COLUMN IF NOT EXISTS subregion TEXT;
ALTER TABLE provenience_canon ADD COLUMN IF NOT EXISTS sort_order INTEGER;

-- Canon table indexes for grouped filter queries
CREATE INDEX IF NOT EXISTS idx_period_canon_group
    ON period_canon (group_name, sort_order);
CREATE INDEX IF NOT EXISTS idx_provenience_canon_region
    ON provenience_canon (region, subregion, sort_order);

-- Partial indexes on artifacts for fast filter count queries
CREATE INDEX IF NOT EXISTS idx_artifacts_period_norm
    ON artifacts (period_normalized) WHERE period_normalized IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_artifacts_prov_norm
    ON artifacts (provenience_normalized) WHERE provenience_normalized IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_artifacts_genre
    ON artifacts (genre) WHERE genre IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_artifacts_lang_norm
    ON artifacts (language_normalized) WHERE language_normalized IS NOT NULL;
