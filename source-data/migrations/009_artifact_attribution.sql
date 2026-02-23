-- ============================================================================
-- Migration 009: Artifact Attribution Fields
-- ============================================================================
-- Add per-artifact scholarly attribution from CDLI CSV fields:
--   atf_source, translation_source, author, date_entered, db_source
--
-- These are 1:1 with the artifact row. No new tables needed.
--
-- Date: 2026-02-22
-- ============================================================================

ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS atf_source TEXT;
ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS translation_source TEXT;
ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS publication_author TEXT;
ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS cdli_date_entered TEXT;
ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS db_source TEXT;
