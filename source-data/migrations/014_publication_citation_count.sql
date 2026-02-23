-- ============================================================================
-- Migration 014: Add citation count to publications
-- ============================================================================
-- Stores pre-fetched citation count from Semantic Scholar. Full citation graph
-- is fetched on-demand via API rather than stored locally.
--
-- Date: 2026-02-23
-- ============================================================================

ALTER TABLE publications ADD COLUMN IF NOT EXISTS cited_by_count INTEGER;

CREATE INDEX IF NOT EXISTS idx_publications_cited_by_count
    ON publications(cited_by_count DESC) WHERE cited_by_count IS NOT NULL;
